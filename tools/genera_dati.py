#!/usr/bin/env python3
"""
Genera i dati geografici REALI di Gravina 3D e li incorpora in index.html.

Fonti: Overture Maps Foundation (release indicata in RELEASE), i cui temi
"transportation", "buildings", "base" e "places" derivano in gran parte da
OpenStreetMap; OpenStreetMap via Overpass API (luoghi con nome); Copernicus DEM
GLO-30 (quote). Licenze: ODbL (© OpenStreetMap contributors), CDLA-Permissive-2.0
e la licenza del Copernicus DEM (attribuzione dell'art. 6(b) in GEO.meta.quote).

Il diorama resta un file unico: i dati NON vengono caricati a runtime, ma
scritti come costante JavaScript (`GEO`) tra due marcatori dentro index.html.

Uso
    python3 -m venv .venv
    .venv/bin/pip install -r tools/requirements.txt
    .venv/bin/python tools/genera_dati.py              # scarica (se serve), elabora, aggiorna index.html
    .venv/bin/python tools/genera_dati.py --forza      # riscarica ignorando la cache
    .venv/bin/python tools/genera_dati.py --anteprima tools/anteprima.png   # disegna una mappa di controllo

Come funziona
    1. Download mirato: dei file GeoParquet di Overture (centinaia di GB) legge
       solo il footer e i "row group" che intersecano il riquadro di Gravina,
       tramite richieste HTTP Range. Pochi MB in tutto.
    2. Rete stradale: vie carrabili reali spezzate nei loro incroci reali
       (i "connector" di Overture). I vicoli ciechi vengono potati (2-core del
       grafo). Le vie cieche importanti (piazza del Duomo, Calata Grotte San
       Michele…) restano e ricevono un'inversione "a goccia" dentro lo slargo
       reale in fondo alla via, solo se c'è spazio tra gli edifici.
       Il ponte (Via giudice Montea, pedonale nella realtà) resta percorribile
       perché richiesto dal progetto: nei dati è marcato come "pedonale".
    3. Edifici: sagome reali semplificate, con cortili (fori) e classe.
    4. Morfologia: corso del Torrente La Gravina, falesie, mura, belvederi,
       scalinate reali (solo decorative), più il ciglio del canyon tracciato a
       mano su belvederi, mura e falesie.
    Altezze degli edifici: solo numero di piani e altezze di OpenStreetMap; le
    stime automatiche dalle immagini aeree (Microsoft ML Buildings) si scartano.
    5. Città intera (fase 3.4): zolla AREA a riquadri da TILE m, centro storico
       Z0 con il dettaglio pieno; vie cieche dei quartieri come vie decorative
       (GEO.deco, non percorribili); edifici della città in forma compatta con
       l'altezza stimata per tipo (GEO.city); quote Copernicus smussate (GEO.dem)
       e letto del torrente (GEO.riverY); uso del suolo (GEO.cover); binari
       (GEO.rails); luoghi OSM (GEO.pois); Castello Svevo con la sterrata.
    6. Strade fuori città (fase 3.4, blocco F): due appendici a riquadri interi
       attaccate alla zolla (GEO.meta.zolle). Il P.I.P. - Zona Artigianale a
       scala reale, con vie e capannoni reali; la strada per il Bosco Difesa
       Grande come TRACCIATO REALE COMPRESSO (eccezione dichiarata in CLAUDE.md):
       angoli di svolta reali, lunghezze ridotte a BOSCO_SCALA.
    7. Il Bosco da vicino (fase 3.4, blocco L): la strada compressa arriva all'area
       Quercus e prosegue fino al vivaio forestale; le due zone attorno restano a
       scala reale (edifici, campi, vasche e sentieri di OSM, GEO.bosco), i
       sentieri del bosco si percorrono a piedi, l'uso del suolo viene dal
       poligono OSM del Bosco Difesa Grande.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import re
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests
import pyarrow.parquet as pq
import shapely
from shapely.geometry import LineString, MultiPoint, Point, Polygon, box, mapping, shape
from shapely.strtree import STRtree

# ─────────────────────────────────────────────────────────────────────────────
# Configurazione
# ─────────────────────────────────────────────────────────────────────────────
RELEASE = 'release/2026-09-23.1'
BASE_URL = 'https://overturemaps-us-west-2.s3.amazonaws.com/'
CA_BUNDLE = None                      # es. '/percorso/ca.crt' se serve un proxy con CA propria
BBOX = (16.395, 16.455, 40.800, 40.840)   # lon min, lon max, lat min, lat max (la città intera)
ORIGIN = (40.8174, 16.4134)               # Cattedrale: origine del sistema locale (lat, lon)

# Zolla del diorama in metri locali (est min/max, nord min/max): 12 × 13 riquadri da 240 m.
# Contiene la città fino alla stazione, al cimitero, allo Sportland e al Castello Svevo.
TILE = 240
AREA = (-840, 2040, -1140, 1980)
AREA_ROADS = (-830, 2030, -1130, 1970)    # binari: devono stare tutti qui dentro
# Blocco F: appendici a riquadri interi, attaccate alla zolla.
PIP = (2040, 2760, 300, 1260)             # P.I.P. - Zona Artigianale, a scala reale (3 × 4 riquadri)
BOSCO = (-120, 600, -1860, -1140)         # strada compressa per il Bosco Difesa Grande e area Quercus (3 × 3 riquadri)
VIVAIO = (-840, 360, -2340, -1860)        # blocco L: strada fino al vivaio forestale; blocco M2: a ovest l'anello V2 (5 × 2 riquadri)
VIVAIO_SUD = (-600, -120, -2580, -2340)   # blocco M2: la vasca grande del vivaio (2 riquadri)
ZOLLE = (AREA, PIP, BOSCO, VIVAIO, VIVAIO_SUD)
BOSCHI = (BOSCO, VIVAIO, VIVAIO_SUD)      # zolle del bosco: paesaggio compresso
BOUND = (-840, 2760, -2580, 1980)         # rettangolo delle zolle: origine e griglie di GEO
ROAD_MARGIN = 10                          # le vie restano ad almeno 10 m dal bordo delle zolle
# Zona Z0, il centro storico: edifici, vie e terreno con il dettaglio pieno (fasi 2–3).
Z0 = (-340, 450, -320, 540)
ALT0 = 358                                # quota (m s.l.m.) dello zero del diorama: l'altopiano della Cattedrale

# Il Castello Svevo si raggiunge da una strada di servizio e da una sterrata reali, che con la
# strada vicinale a nord-est chiudono un anello: qui dentro diventano percorribili.
CASTLE_BOX = (560, 760, 1480, 1920)
DEM_FILE = 'dem/Copernicus_DSM_COG_10_N40_00_E016_00_DEM.tif'

THEMES = {                                # nome cache → tema/tipo Overture
    'segment': 'theme=transportation/type=segment',
    'connector': 'theme=transportation/type=connector',
    'building': 'theme=buildings/type=building',
    'water': 'theme=base/type=water',
    'infrastructure': 'theme=base/type=infrastructure',
    'land': 'theme=base/type=land',
    'land_use': 'theme=base/type=land_use',
    'place': 'theme=places/type=place',
}

DRIVABLE = {'secondary', 'tertiary', 'residential', 'living_street', 'pedestrian', 'unclassified'}
# Tratti a piedi (blocco G): solo nel centro storico, e solo quelli che chiudono un anello con le vie.
WALK = {'footway', 'steps'}
# Vie cieche da conservare (con inversione a goccia) perché portano a luoghi importanti.
KEEP_DEAD_ENDS = {'Piazza Benedetto XIII', 'Via Civita', 'Larghetto San Francesco', 'Via Matteotti'}
# Blocco M2: tratti a piedi reali scelti per id OSM (Overture dice da quale via OSM viene ogni pezzo),
# anche fuori dal centro storico. Entrano nella rete solo se chiudono un anello con altre vie reali.
WALK_OSM = {
    578892844, 682777030, 682776965,                                  # A · sentiero degli scavi di Botromagno
    1288066843, 1288066841, 1288066847, 1288066840, 1288066845,      # C · Pineta Parco Robinson
    1288066844, 1288066842, 1288066846,                              # D · Parco Robinson, vialetti a sud
    902676524,                                                       # E · Via Pietro Ianora (service, basolato)
    1288069906, 1288069907, 1288069908, 1288069909, 1288069910,      # F · scale e sottopassaggio della stazione
    1195312391, 1195312392, 1195312390, 1195312393, 1195312394,      # vialetti della Villa Comunale
    # blocco N5 (piano approvato dal committente il 14/10/2026): Capotenda, carrarecce e sentieri fino al guado
    682777028, 682777027,                                            # carrareccia da Via Madonna della Stella
    682777029, 682777031,                                            # sentiero che attraversa Capotenda; lungo la gola, dal belvedere
    578916724, 578916725, 578916726,                                 # carrarecce attorno alla vigna di Botromagno
    578916727, 578916728,                                            # giù verso il torrente, poi lungo il torrente fino al guado
}
# Villa Comunale e Piazza della Repubblica pedonali (decisione del committente del 01/10/2026, anche se OSM
# segna residential): Viale Orsini e Via Libertà, più le vie della rete dentro le due aree OSM.
PEDONALI_OSM = {76147726, 385225743, 385148840}
PEDONALI_AREE = (327411255, 385148839)        # Villa Comunale, Piazza della Repubblica (area pedonale OSM)
PEDONALI_NO = {'Corso Vittorio Emanuele'}     # resta carrabile
# Blocco N2 (piano approvato dal committente il 05/10/2026): nel Fondovito le vie che nella realtà non si fanno
# in auto per i dislivelli sono pedonali anche dove OSM segna residential. Su Street View l'auto di Google non è
# passata sulla Calata Grotte San Michele (solo foto a 360° di utenti); Via Civita resta carrabile.
PEDONALI_FONDOVITO = {76151641, 385174951, 1384781495, 600751157}    # Calata Grotte San Michele, tutta; blocco N5c: Via Giacomo Leopardi fino al cancello di Hortus; blocco 4.7: Larghetto San Francesco (w600751157)
# Il ponticello in fondo alla terrazza di San Michele delle Grotte (richiesta del committente, 05/10/2026): una
# passerella di pietra col parapetto che scavalca la testa del canalone e porta al promontorio delle mura (OSM
# w1512581512). Non è in OSM: punti scelti sul satellite e sulla foto da drone (solo come riferimento) tra la fine
# della terrazza OSM (w76152588) e l'inizio delle mura. Eccezione scritta in CLAUDE.md.
PONTICELLO = ('Ponticello di San Michele', [(-59.9, -176.4), (-64.5, -179.8), (-69.3, -183.2), (-73.5, -186.0)])
# Il guado di Capotenda (blocco N5, eccezione approvata dal committente il 14/10/2026, come il ponticello): i sassi
# piatti sul torrente (OSM w578916734, w578916735 con ford=stepping_stones) e i primi 9 m di w578916733 sull'altra
# sponda. Il segmento Overture che li contiene esce dalla zolla e la pipeline lo scarterebbe intero: qui i punti OSM,
# dal nodo db9552 (fine di w578916728) al greto, dove la figurina gira con la goccia (GOCCE_PIEDI).
GUADO = ('Guado di Capotenda', [(-575.3, 1284.6), (-565.8, 1286.4), (-556.9, 1288.0), (-554.2, 1291.0), (-550.5, 1294.2)])
# Tratti a piedi ciechi che finiscono in uno slargo reale: restano, e la figurina gira con la goccia (blocco N2,
# eccezione come le gocce del mezzo). Punto dove finiscono.
GOCCE_PIEDI = [
    (-73.5, -186.0),              # oltre il ponticello di San Michele, sul promontorio delle mura
    (-550.5, 1294.2),             # blocco N5: oltre il guado di Capotenda, sul greto dell'altra sponda (GUADO)
    (-4.5, 107.6),                # blocco N2b: il footway OSM w1195336380 («Calata S. Lucia») finisce davanti alla chiesa di Santa Lucia
    (1590, -572),                 # blocco N4: il giardino del Casino di Meninni finisce nella radura dietro il Casino (GIARDINO_MENINNI)
    (200.3, 242.2),               # blocco 4.7: Larghetto San Francesco (OSM w600751157), goccia davanti alla facciata della chiesa
]
# Raccordi a piedi attraverso un'area pedonale reale, tra due vertici del suo contorno (blocco N2, approvato il
# 05/10/2026 come le aree pedonali della Villa): nome, punti, superficie (SUPERFICI).
RACCORDI_PIEDI = [
    # i Gradoni San Giovanni Battista finiscono sul vertice (89.3, -126.6) dell'area pedonale di Piazza Pellicciari
    # (OSM w469108906, surface=concrete); Via Marconi tocca la stessa area nel vertice (103.2, -115.5)
    ('Piazza Giuseppe Pellicciari', [(89.3, -126.6), (103.2, -115.5)], 2),
]
# Blocco N2: vie cieche del centro storico che si disegnano (decorative, non percorribili) perché portano a un luogo
DECO_Z0 = {1384781495}                        # Via Giacomo Leopardi, fino al cancello di Hortus (Street View, ottobre 2025)
SOTTOPASSO_PIEDI = {1288069909}               # sottopassaggio pedonale della stazione (OSM level=-1, tra due scalinate)
# Percorso del ponte: pedonale nella realtà, percorribile nel diorama.
BRIDGE_ROUTE_NAME = 'Via giudice Montea'
BRIDGE_WEST_BOX = (-140, 40, 200, 420)    # sentieri attorno alla Madonna della Stella

# Ciglio del canyon, tracciato a mano (da sud a nord) su belvederi, mura del
# Piaggio, falesie e testate del ponte. Il torrente scorre tra i due cigli.
EAST_RIM = [(-150, -420), (-110, -300), (-95, -230), (-78, -186), (-60, -140), (-45, -70),
            (-30, 20), (-20, 100), (-8, 157), (14, 200), (26, 250), (30, 290), (58, 335),
            (78, 400), (84, 450), (62, 505), (0, 535), (-80, 562), (-150, 640)]
WEST_RIM = [(-240, -420), (-205, -300), (-182, -160), (-168, 20), (-156, 113), (-132, 150),
            (-124, 199), (-106, 249), (-84, 300), (-80, 350), (-62, 400), (-90, 428),
            (-150, 445), (-230, 530), (-260, 640)]

CACHE = Path(__file__).with_name('.cache')
ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / 'index.html'
MARK_START = '/* @@DATI-GEO-INIZIO@@'
MARK_END = '/* @@DATI-GEO-FINE@@ */'

# ─────────────────────────────────────────────────────────────────────────────
# Geografia
# ─────────────────────────────────────────────────────────────────────────────
M_LAT = 111132
M_LON = 111320 * math.cos(math.radians(ORIGIN[0]))


def to_local(lon: float, lat: float) -> tuple[float, float]:
    """(lon, lat) → (est, nord) in metri rispetto alla Cattedrale."""
    return ((lon - ORIGIN[1]) * M_LON, (lat - ORIGIN[0]) * M_LAT)


def local_geom(g):
    """Converte una geometria shapely da lon/lat a metri locali."""
    return shapely.transform(g, lambda xy: np.column_stack(((xy[:, 0] - ORIGIN[1]) * M_LON, (xy[:, 1] - ORIGIN[0]) * M_LAT)))


def inside(p, area) -> bool:
    return area[0] <= p[0] <= area[1] and area[2] <= p[1] <= area[3]


def zone_union(zones, margin=0.0):
    """Unione dei rettangoli `zones` (est min/max, nord min/max), ristretta di `margin` m."""
    g = shapely.union_all([box(z[0], z[2], z[1], z[3]) for z in zones])
    return g.buffer(-margin, join_style='mitre') if margin else g


def zone_mask(E, N, pad):
    """Punti della griglia (E, N) dentro una delle zolle, allargate di `pad` m."""
    EE, NN = np.meshgrid(E, N)
    m = np.zeros(EE.shape, bool)
    for z in ZOLLE:
        m |= (EE >= z[0] - pad) & (EE <= z[1] + pad) & (NN >= z[2] - pad) & (NN <= z[3] + pad)
    return m


# Città e P.I.P. prendono vie ed edifici reali; nell'appendice del bosco c'è solo la strada compressa.
CITY_ZONE = zone_union((AREA, PIP))
CITY_ROADS = zone_union((AREA, PIP), ROAD_MARGIN)
ALL_ROADS = zone_union(ZOLLE, ROAD_MARGIN)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Download mirato dei GeoParquet (HTTP Range)
# ─────────────────────────────────────────────────────────────────────────────
SESSION = requests.Session()
if CA_BUNDLE:
    SESSION.verify = CA_BUNDLE


def http_range(url: str, a: int, b: int) -> bytes:
    for attempt in range(4):
        try:
            r = SESSION.get(url, headers={'Range': f'bytes={a}-{b - 1}'}, timeout=180)
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


class RangeFile(io.RawIOBase):
    """File remoto in sola lettura per pyarrow: footer in un colpo, il resto a richiesta."""

    def __init__(self, key: str, size: int):
        self.url, self.size, self.pos = BASE_URL + key, size, 0
        flen = struct.unpack('<I', http_range(self.url, size - 8, size - 4))[0]
        self.tail_start = size - flen - 8
        self.tail = http_range(self.url, self.tail_start, size)

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def read(self, n=-1):
        n = self.size - self.pos if n < 0 else min(n, self.size - self.pos)
        if n <= 0:
            return b''
        if self.pos >= self.tail_start:
            d = self.tail[self.pos - self.tail_start:self.pos - self.tail_start + n]
        else:
            d = http_range(self.url, self.pos, self.pos + n)
        self.pos += len(d)
        return d

    def readinto(self, b):
        d = self.read(len(b))
        b[:len(d)] = d
        return len(d)


def list_keys(theme_type: str) -> list[tuple[str, int]]:
    prefix = f'{RELEASE}/{theme_type}/'
    keys, token = [], None
    while True:
        url = BASE_URL + f'?list-type=2&prefix={prefix}'
        if token:
            url += '&continuation-token=' + requests.utils.quote(token, safe='')
        xml = SESSION.get(url, timeout=60).text
        keys += list(zip(re.findall(r'<Key>([^<]+)</Key>', xml), map(int, re.findall(r'<Size>(\d+)</Size>', xml))))
        m = re.search(r'<NextContinuationToken>([^<]+)</NextContinuationToken>', xml)
        if not m:
            return [k for k in keys if k[0].endswith('.parquet')]
        token = m.group(1)


def row_groups_in_bbox(pf) -> list[int]:
    """Indici dei row group le cui statistiche sul bbox intersecano BBOX."""
    md, hits = pf.metadata, []
    for r in range(md.num_row_groups):
        rg, st = md.row_group(r), {}
        for i in range(rg.num_columns):
            c = rg.column(i)
            if c.path_in_schema.startswith('bbox.') and c.statistics is not None:
                st[c.path_in_schema] = (c.statistics.min, c.statistics.max)
        if (st['bbox.xmin'][0] <= BBOX[1] and st['bbox.xmax'][1] >= BBOX[0]
                and st['bbox.ymin'][0] <= BBOX[3] and st['bbox.ymax'][1] >= BBOX[2]):
            hits.append(r)
    return hits


def clean(v):
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items() if x not in (None, [], {})}
    if isinstance(v, list):
        return [clean(x) for x in v]
    return None if isinstance(v, bytes) else v


def download(name: str, theme_type: str, force: bool) -> list[dict]:
    CACHE.mkdir(exist_ok=True)
    out = CACHE / f'{name}.json'
    if out.exists() and not force:
        return json.loads(out.read_text())
    keys = list_keys(theme_type)

    def scan(k):
        f = RangeFile(*k)
        return k, f, row_groups_in_bbox(pq.ParquetFile(f))

    with ThreadPoolExecutor(24) as ex:
        scanned = [s for s in ex.map(scan, keys) if s[2]]
    feats = []
    for (key, size), f, rgs in scanned:
        pf = pq.ParquetFile(f)
        for rg in rgs:
            for row in pf.read_row_group(rg).to_pylist():
                b = row.pop('bbox')
                if b['xmin'] > BBOX[1] or b['xmax'] < BBOX[0] or b['ymin'] > BBOX[3] or b['ymax'] < BBOX[2]:
                    continue
                g = shapely.from_wkb(row.pop('geometry'))
                props = clean(row)
                props['geom'] = mapping(g)
                feats.append(props)
    out.write_text(json.dumps(feats, default=str))
    print(f'  {name}: {len(feats)} elementi')
    return feats


# ─────────────────────────────────────────────────────────────────────────────
# 2. Rete stradale reale
# ─────────────────────────────────────────────────────────────────────────────
def point_at(pts, t):
    """Punto a frazione t (0..1) della lunghezza di una polilinea, con l'indice del tratto."""
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + math.dist(a, b))
    target = t * L[-1]
    for i in range(len(pts) - 1):
        if L[i + 1] >= target:
            u = (target - L[i]) / ((L[i + 1] - L[i]) or 1)
            return i, (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)
    return len(pts) - 2, pts[-1]


def length(poly):
    return sum(math.dist(a, b) for a, b in zip(poly, poly[1:]))


def osm_ways(s):
    """Vie OSM da cui viene un segmento Overture: [(id, t0, t1)] lungo il segmento."""
    out = []
    for src in s.get('sources') or []:
        rid = src.get('record_id') or ''
        if rid.startswith('w'):
            a, b = src.get('between') or (0, 1)
            out.append((int(rid[1:].split('@')[0]), a, b))
    return out


def rail_lines(segments):
    """Binari (FAL e RFI) come linee in metri locali: servono a riconoscere i sottopassi."""
    return [LineString([to_local(*p) for p in s['geom']['coordinates']]) for s in segments
            if s.get('subtype') == 'rail' and s.get('class') in ('narrow_gauge', 'standard_gauge')]


def build_edges(segments, connectors):
    """Spezza i segmenti Overture nei loro connettori → archi tra incroci reali."""
    conn_pos = {c['id']: to_local(*c['geom']['coordinates']) for c in connectors}
    rails = STRtree(rail_lines(segments))
    edges = []
    for s in segments:
        cls, name = s.get('class'), (s.get('names') or {}).get('primary')
        if s.get('subtype') != 'road':
            continue
        pts = [to_local(*p) for p in s['geom']['coordinates']]
        ways = osm_ways(s)
        ids = {w for w, _, _ in ways}
        walk_osm = bool(ids & WALK_OSM)
        on_bridge_route = name == BRIDGE_ROUTE_NAME and cls != 'steps'
        near_bridge_west = cls in ('footway', 'path') and not walk_osm and any(
            BRIDGE_WEST_BOX[0] < p[0] < BRIDGE_WEST_BOX[1] and BRIDGE_WEST_BOX[2] < p[1] < BRIDGE_WEST_BOX[3] for p in pts)
        to_castle = (cls in ('track', 'service') and all(inside(p, CASTLE_BOX) for p in pts)) or (cls == 'service' and bool(ids & SERVIZIO_OSM))
        if to_castle:
            cls = 'track'
        # vie senza classe (per lo più traverse cieche dei quartieri nuovi): solo da guardare
        deco = cls == 'unknown'
        # marciapiedi, passaggi e scalinate del centro storico: si percorrono a piedi (blocco G);
        # dal blocco M2 anche i tratti reali scelti per id OSM (WALK_OSM), in tutta la città
        walk = (cls in WALK and not on_bridge_route and not near_bridge_west and all(inside(p, Z0) for p in pts)) or walk_osm
        if cls not in DRIVABLE and not on_bridge_route and not near_bridge_west and not to_castle and not deco and not walk:
            continue
        flags = s.get('road_flags') or []
        cuts = [(c['at'], c['connector_id']) for c in s.get('connectors', [])]
        spans = {'is_bridge': [], 'is_tunnel': []}
        for f in flags:
            for v in f.get('values', []):
                if v in spans:
                    between = f.get('between') or [0, 1]
                    k = len(spans[v])
                    spans[v].append(between)
                    # blocco M2: un nome per ogni galleria (prima le gallerie di un segmento finivano nello stesso nodo)
                    cuts += [(between[0], f'{v}-a{k}:{s["id"]}'), (between[1], f'{v}-b{k}:{s["id"]}')]
        cuts = sorted(set(cuts))
        # Blocco M2: le gallerie di un segmento che passa sotto i binari restano tutte (sono un sottopasso solo)
        under_rails = False
        for a, b in spans['is_tunnel']:
            i0, p0 = point_at(pts, a)
            i1, p1 = point_at(pts, b)
            line = LineString([p0] + pts[i0 + 1:i1 + 1] + [p1])
            under_rails |= any(rails.geometries[i].intersects(line) for i in rails.query(line))
        for (t0, c0), (t1, c1) in zip(cuts, cuts[1:]):
            if t1 - t0 < 1e-6:
                continue
            mid = (t0 + t1) / 2
            i0, p0 = point_at(pts, t0)
            i1, p1 = point_at(pts, t1)
            poly = [p0] + pts[i0 + 1:i1 + 1] + [p1]
            osm = {w for w, a, b in ways if a <= mid <= b} or ids
            tunnel = any(a <= mid <= b for a, b in spans['is_tunnel'])
            if tunnel and not under_rails:
                # Blocco M2: le gallerie sotto i binari (Corso Giuseppe di Vittorio, Via Falcone e Borsellino)
                # sono sottopassi veri: restano, con il flag `tunnel`; le altre gallerie non si vedono.
                continue
            edges.append({
                'a': c0, 'b': c1, 'poly': poly, 'cls': cls, 'name': name or next((WALK_NOMI[w] for w in osm if w in WALK_NOMI), None), 'osm': osm,
                'bridge': any(a <= mid <= b for a, b in spans['is_bridge']),
                'foot': cls not in DRIVABLE and not to_castle and not deco, 'deco': deco,
                'walk': walk and (cls in WALK or bool(osm & WALK_OSM)),
                'tunnel': tunnel or bool(osm & SOTTOPASSO_PIEDI),
            })
    # posizioni dei nodi: connettori reali o punti di taglio
    pos = dict(conn_pos)
    for e in edges:
        pos.setdefault(e['a'], e['poly'][0])
        pos.setdefault(e['b'], e['poly'][-1])
    return edges, pos


def merge_close_nodes(edges, pos, tol=0.8):
    """Unisce nodi a meno di `tol` metri (connettori duplicati, tagli coincidenti)."""
    parent = {n: n for n in pos}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    items = list(pos.items())
    tree = STRtree([Point(p) for _, p in items])
    for i, (n, p) in enumerate(items):
        for j in tree.query(Point(p).buffer(tol)):
            if j != i and math.dist(p, items[j][1]) <= tol:
                parent[find(items[j][0])] = find(n)
    out = []
    for e in edges:
        a, b = find(e['a']), find(e['b'])
        if a == b and length(e['poly']) < 2:
            continue
        out.append({**e, 'a': a, 'b': b})
    return out, {find(n): p for n, p in pos.items()}


def degrees(edges):
    d = collections.Counter()
    for e in edges:
        d[e['a']] += 1
        d[e['b']] += 1
    return d


def two_core(edges):
    """Pota iterativamente i nodi di grado 1: restano solo vie senza vicoli ciechi."""
    while True:
        d = degrees(edges)
        kept = [e for e in edges if d[e['a']] >= 2 and d[e['b']] >= 2]
        if len(kept) == len(edges):
            return kept
        edges = kept


def teardrop(leaf, direction, r):
    """Inversione a goccia davanti al nodo cieco: due semiarchi foglia→Q e Q→foglia."""
    fx, fy = direction
    nx, ny = -fy, fx
    P = lambda a, b: (leaf[0] + fx * a * r + nx * b * r, leaf[1] + fy * a * r + ny * b * r)
    q = P(2.4, 0)
    return q, [leaf, P(0.9, -0.85), P(1.9, -0.75), q], [q, P(1.9, 0.75), P(0.9, 0.85), leaf]


def add_turnarounds(core, extra, pos, buildings_tree, buildings, prune=True, walls=(), ostacoli=()):
    """
    Aggiunge le vie cieche selezionate. A ogni foglia prova a inserire
    un'inversione a goccia che non tocchi gli edifici; se non c'è spazio,
    pota l'ultimo tratto e riprova sulla nuova foglia (con prune=False la lascia com'è).
    `walls` vale solo per le gocce della figurina, `ostacoli` per tutte (blocco N4: il muro di cinta del Casino di Meninni).
    """
    edges = core + extra
    loops = 0
    tried = set()
    area = ALL_ROADS
    while True:
        d = degrees(edges)
        leaves = [n for n, k in d.items() if k == 1 and (prune or n not in tried)]
        if not leaves:
            return edges, loops
        for leaf in leaves:
            e = next(x for x in edges if leaf in (x['a'], x['b']))
            poly = e['poly'] if e['b'] == leaf else e['poly'][::-1]
            tail = next((p for p in reversed(poly[:-1]) if math.dist(p, poly[-1]) > 1.5), poly[0])
            dx, dy = poly[-1][0] - tail[0], poly[-1][1] - tail[1]
            dl = math.hypot(dx, dy) or 1
            placed = None
            walk = bool(e.get('walk'))                  # blocco N2: la goccia della figurina è piccola
            if leaf not in tried:
                tried.add(leaf)
                for r in ((2.4, 2.0, 1.7) if walk else (6.0, 5.0, 4.2)):
                    for ang in (0, 25, -25, 50, -50, 75, -75):
                        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                        f = ((dx * c - dy * s) / dl, (dx * s + dy * c) / dl)
                        q, right, left = teardrop(pos[leaf], f, r)
                        shape_ = LineString(right + left[1:]).buffer(1.1 if walk else 2.3)
                        if not area.contains(shape_):
                            continue
                        hit = any(buildings[i].buffer(-0.3).intersects(shape_) for i in buildings_tree.query(shape_))
                        hit = hit or (walk and any(w.intersects(shape_) for w in walls))   # blocco N2: la figurina non gira nelle mura
                        hit = hit or any(w.intersects(shape_) for w in ostacoli)
                        if not hit:
                            placed = (q, right, left)
                            break
                    if placed:
                        break
            if placed or not prune:
                if not placed:
                    break
                q, right, left = placed
                qid = f'inv:{leaf}'
                pos[qid] = q
                base = {'cls': e['cls'], 'name': e['name'], 'bridge': False, 'foot': e['foot'], 'turn': True, 'walk': walk,
                        'surf': (e.get('surf') or {}) if walk else {}}
                edges.append({**base, 'a': leaf, 'b': qid, 'poly': right})
                edges.append({**base, 'a': qid, 'b': leaf, 'poly': left})
                loops += 1
            else:
                edges = [x for x in edges if x is not e]
            break                                   # ricalcola i gradi dopo ogni modifica


def dead_end_trees(all_edges, core):
    """Rami potati attaccati al nucleo, raggruppati ad albero."""
    core_ids = {id(e) for e in core}
    core_nodes = {e['a'] for e in core} | {e['b'] for e in core}
    pruned = [e for e in all_edges if id(e) not in core_ids]
    adj = collections.defaultdict(list)
    for e in pruned:
        adj[e['a']].append(e)
        adj[e['b']].append(e)
    seen, trees = set(), []
    for e in pruned:
        if id(e) in seen:
            continue
        stack, tree = [e], []
        while stack:
            x = stack.pop()
            if id(x) in seen:
                continue
            seen.add(id(x))
            tree.append(x)
            for n in (x['a'], x['b']):
                if n not in core_nodes:
                    stack += [y for y in adj[n] if id(y) not in seen]
        if any(x['a'] in core_nodes or x['b'] in core_nodes for x in tree):
            trees.append(tree)
    return trees


def largest_component(edges):
    adj = collections.defaultdict(list)
    for e in edges:
        adj[e['a']].append(e['b'])
        adj[e['b']].append(e['a'])
    best, seen = set(), set()
    for n in adj:
        if n in seen:
            continue
        comp, stack = set(), [n]
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            stack += adj[x]
        seen |= comp
        if len(comp) > len(best):
            best = comp
    return [e for e in edges if e['a'] in best]


def merge_chains(edges):
    """Unisce i tratti consecutivi della stessa via separati da nodi di grado 2."""
    changed = True
    while changed:
        changed = False
        d = degrees(edges)
        inc = collections.defaultdict(list)
        for e in edges:
            inc[e['a']].append(e)
            inc[e['b']].append(e)
        for n, k in d.items():
            if k != 2:
                continue
            e1, e2 = inc[n]
            if e1 is e2 or e1['name'] != e2['name'] or e1['bridge'] or e2['bridge'] \
                    or e1['foot'] != e2['foot'] or e1.get('walk') != e2.get('walk') or e1.get('turn') or e2.get('turn') \
                    or e1.get('tunnel') != e2.get('tunnel') \
                    or (e1['cls'] == 'track') != (e2['cls'] == 'track'):
                continue
            p1 = e1['poly'] if e1['b'] == n else e1['poly'][::-1]
            a1 = e1['a'] if e1['b'] == n else e1['b']
            p2 = e2['poly'] if e2['a'] == n else e2['poly'][::-1]
            b2 = e2['b'] if e2['a'] == n else e2['a']
            if a1 == b2:
                continue                                 # eviterebbe un anello su sé stesso
            surf = dict(e1.get('surf') or {})
            for k, v in (e2.get('surf') or {}).items():
                surf[k] = surf.get(k, 0) + v
            merged = {**e1, 'a': a1, 'b': b2, 'poly': p1 + p2[1:],
                      'cls': e1['cls'] if length(p1) >= length(p2) else e2['cls'], 'surf': surf}
            edges = [x for x in edges if x is not e1 and x is not e2] + [merged]
            changed = True
            break
    return edges


def midpoint(poly):
    return point_at(poly, 0.5)[1]


# Strada per il Bosco Difesa Grande: tracciato reale dal bordo sud della città al rifugio
# (Overture Maps, fuori dalla zolla: provinciale Matera–Gravina fino alla svolta, poi la strada
# senza nome verso il bosco e l'ultimo tratto fino al rifugio), circa 5,6 km in metri locali.
BOSCO_ROUTE = [(413, -1151), (469, -1240), (501, -1291), (667, -1516), (723, -1579), (786, -1700),
               (790, -1716), (789, -2013), (773, -2066), (491, -2881),
               (450, -2900), (422, -2926), (400, -2972), (414, -3139), (468, -3340), (499, -3511), (519, -3784),
               (191, -4130), (167, -4149), (84, -4268), (-106, -4866), (-214, -5287), (-269, -5428),
               (-441, -5485), (-614, -5592), (-750, -5701), (-785, -5732), (-773, -5662)]
BOSCO_TURN = 9                            # indice della svolta: fin qui è la provinciale
BOSCO_START = (356, -1060)                # incrocio della provinciale con Via Fosse Ardeatine (in città)
BOSCO_SCALA = 0.125                       # 5,6 km → 0,7 km: angoli reali, lunghezze accorciate
BOSCO_PROVINCIALE = 'Strada provinciale Matera Gravina'


def chaikin(pts, rounds=2):
    """Smussa gli spigoli di una polilinea (estremi fermi): curve morbide, direzioni invariate."""
    for _ in range(rounds):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        pts = out[:1] + out[2:-1] + [pts[-1]]
    return pts


# Blocco L (decisioni del 30/09/2026): dall'area Quercus la strada reale asfaltata (OSM w107709083,
# w1068957585, w1068957584, w252747452; su Google la SP158) scende per 3,2 km fino all'incrocio con
# Contrada Annunziata davanti al vivaio forestale. Si comprime con la stessa regola; le zone attorno
# all'area Quercus e al vivaio restano a scala reale (ZONA_Q, ZONA_V: rettangoli in metri reali).
QUERCUS_A = 24                            # da questo punto di BOSCO_ROUTE la strada è a scala reale (area Quercus)
BOSCO_J = (-785.2, -5732.3)               # incrocio sotto l'area Quercus (OSM): di qui la via di servizio e la strada del vivaio
VIVAIO_ROUTE = [BOSCO_J, (-949, -5872), (-979, -5887), (-1001, -5894), (-1059, -5906), (-1092, -5905), (-1118, -5900),
                (-1145, -5895), (-1181, -5909), (-1337, -6048), (-1357, -6062), (-1407, -6093), (-1571, -6189), (-1605, -6212),
                (-1653, -6269), (-1740, -6413), (-1798, -6497), (-1839, -6532), (-1880, -6558), (-1920, -6596), (-1999, -6700),
                (-2021, -6718), (-2166, -6814), (-2194, -6843), (-2255, -6932), (-2268, -6948), (-2333, -7009), (-2428, -7089),
                (-2499, -7163), (-2548, -7228), (-2628, -7339), (-2687, -7396), (-2752, -7429), (-2826, -7452), (-2869, -7456),
                (-2964, -7443), (-2988, -7446), (-3008, -7458), (-3029, -7487), (-3076, -7561), (-3102, -7569), (-3123, -7563),
                (-3143, -7562), (-3160, -7571), (-3192, -7570), (-3198, -7575), (-3209.5, -7590.7)]
VIVAIO_REAL = 35                          # da (-2964, -7443) la strada è di nuovo a scala reale (zona del vivaio)
ZONA_Q = (-960, -610, -5770, -5470)       # area Quercus, a scala reale
ZONA_V = (-3470, -2955, -7800, -7290)     # vivaio, Base Scout, area pic-nic, a scala reale (blocco M2: con l'anello V2 e la vasca grande)
# Sentieri reali attorno all'area Quercus (OSM highway=path) che chiudono anelli con la via di servizio
# w647001048: circa 490 m a scala reale, lontano dalla strada del vivaio (anello nord).
QUERCUS_SERVIZIO = 647001048
QUERCUS_SENTIERI = {647001042, 647001043, 647001044, 647001046, 647001047, 759847416, 773874702}
BOSCO_BRUCIATO = [(-950, -825, -5665, -5540), (-745, -612, -5760, -5662)]   # alberi morti grigi (satellite, solo riferimento visivo)
# Punti senza dati OSM (solo riferimento visivo dal satellite e indicazioni del committente), in metri reali.
BOSCO_PUNTI = {
    'picnic': (-3108, -7507),                 # area pic-nic davanti al vivaio, a nord della strada (committente)
    'scritta': (-3136, -7539, 21.6),          # «SIC DIFESA GRANDE» sul pendio, rivolta alla strada: centro e direzione del testo
    'aiuole': (-3060, -7690),                 # aiuole del vivaio in file, a sud-est degli edifici
}
# Dove il blocco L metteva il maneggio (che non c'è): serve solo a lasciare il parcheggio com'era.
MANEGGIO_EX = (-749, -5643)
BOSCO_OVERPASS = """[out:json][timeout:160];
(way["highway"](40.740,16.365,40.775,16.420);way["building"](40.740,16.365,40.775,16.420);
 way["leisure"](40.740,16.365,40.775,16.420);way["amenity"](40.740,16.365,40.775,16.420);
 way["landuse"~"reservoir|basin"](40.740,16.365,40.775,16.420);
 way["natural"="wood"](40.735,16.36,40.785,16.425););out tags geom;"""


def overpass_cached(name, query):
    """Query Overpass piccola con la sua cache (tools/.cache/<name>.json): così overpass.json non si riscarica."""
    out = CACHE / f'{name}.json'
    if not out.exists():
        for url in (OVERPASS_URL, 'https://overpass.private.coffee/api/interpreter'):
            try:
                r = SESSION.post(url, data={'data': query}, timeout=200,
                                 headers={'User-Agent': 'gravina-3d (github.com/giuseppecassano5bit/gravina-3d)', 'Accept': 'application/json'})
                r.raise_for_status()
                r.json()
                out.write_text(r.text)
                break
            except (requests.RequestException, ValueError):
                time.sleep(5)
    return json.loads(out.read_text())['elements']


def overpass_bosco():
    """Dati OSM del Bosco Difesa Grande (sentieri, edifici, campi, vasche, poligono del bosco), in cache."""
    return overpass_cached('bosco', BOSCO_OVERPASS)


def bosco_chain():
    """
    Tracciato compresso: ogni tratto reale si accorcia di BOSCO_SCALA mantenendo la direzione (gli
    angoli restano quelli reali); i tratti nelle zone Quercus e vivaio restano a scala reale.
    Restituisce (provinciale, svolta→Quercus, Quercus→vivaio, ancore) in metri del diorama; le ancore
    dicono dove cade nel diorama il punto reale da cui parte ogni zona a scala reale.
    """
    o = BOSCO_ROUTE[0]
    sc = lambda q: (o[0] + (q[0] - o[0]) * BOSCO_SCALA, o[1] + (q[1] - o[1]) * BOSCO_SCALA)
    a = chaikin([BOSCO_START] + [sc(q) for q in LineString(BOSCO_ROUTE[:BOSCO_TURN + 1]).simplify(30).coords])

    def walk(start_d, pieces):
        pts, d = [start_d], start_d
        for real, scale in pieces:
            seg = [d]
            q = list(LineString(real).simplify(30 if scale < 1 else 1).coords)
            for p0, p1 in zip(q, q[1:]):
                d = (d[0] + (p1[0] - p0[0]) * scale, d[1] + (p1[1] - p0[1]) * scale)
                seg.append(d)
            pts += (chaikin(seg) if scale < 1 else seg)[1:]
        return pts
    route = BOSCO_ROUTE[:QUERCUS_A + 2] + [BOSCO_J]
    A = route[QUERCUS_A]
    b = walk(a[-1], [(route[BOSCO_TURN:QUERCUS_A + 1], BOSCO_SCALA), (route[QUERCUS_A:], 1)])
    dA = (b[-1][0] - (BOSCO_J[0] - A[0]), b[-1][1] - (BOSCO_J[1] - A[1]))
    R = VIVAIO_ROUTE[VIVAIO_REAL]
    c = walk(b[-1], [(VIVAIO_ROUTE[:VIVAIO_REAL + 1], BOSCO_SCALA), (VIVAIO_ROUTE[VIVAIO_REAL:], 1)])
    dR = (c[-1][0] - (VIVAIO_ROUTE[-1][0] - R[0]), c[-1][1] - (VIVAIO_ROUTE[-1][1] - R[1]))
    return a, b, c, {'Q': (A, dA), 'V': (R, dR), 'J': b[-1]}


def bosco_map(p, anchors, ref=None):
    """
    Punto reale → diorama: a scala reale nelle zone Quercus e vivaio, altrimenti a lato del tracciato
    compresso (per una sagoma intera si passa `ref`, il suo centro: tutti i punti usano lo stesso vertice).
    """
    ref = ref or p
    for key, zone in (('Q', ZONA_Q), ('V', ZONA_V)):
        if inside(ref, zone):
            (A, dA) = anchors[key]
            return (dA[0] + p[0] - A[0], dA[1] + p[1] - A[1])
    # a lato della strada compressa: il vertice reale più vicino, più lo scarto reale
    (J, dJ) = BOSCO_J, anchors['J']
    q = min(VIVAIO_ROUTE[:VIVAIO_REAL + 1], key=lambda v: math.dist(v, ref))
    return (dJ[0] + (q[0] - J[0]) * BOSCO_SCALA + p[0] - q[0], dJ[1] + (q[1] - J[1]) * BOSCO_SCALA + p[1] - q[1])


def bosco_real(d, anchors, route_d, route_r):
    """Diorama → punto reale (per l'uso del suolo): nelle zone a scala reale esatto, altrimenti a lato del tracciato."""
    for key, zone in (('Q', ZONA_Q), ('V', ZONA_V)):
        A, dA = anchors[key]
        r = (A[0] + d[0] - dA[0], A[1] + d[1] - dA[1])
        if inside(r, zone):
            return r
    k = int(np.argmin(np.hypot(route_d[:, 0] - d[0], route_d[:, 1] - d[1])))
    return (route_r[k][0] + d[0] - route_d[k][0], route_r[k][1] + d[1] - route_d[k][1])


def bosco_site():
    """Fondo della strada del vivaio: (punto finale, direzione)."""
    c = bosco_chain()[2]
    (x0, y0), (x1, y1) = c[-2], c[-1]
    l = math.hypot(x1 - x0, y1 - y0) or 1
    return (x1, y1), ((x1 - x0) / l, (y1 - y0) / l)


# Blocco M2: anello V2 attorno al vivaio (691 m, tutte vie OSM reali), dalla goccia di Contrada Annunziata.
VIVAIO_ANELLO = {252747455, 621213285, 409090222, 647001064, 146025991, 621213286}


def bosco_ways(elements, anchors, pos, ids=None, junction=None, jid='bosco:quercus', drive=QUERCUS_SERVIZIO, prefix='q'):
    """
    Tratti tra i nodi condivisi di vie OSM attorno all'area Quercus (via di servizio e sentieri) o al vivaio
    (anello V2), a scala reale. `junction` è il punto reale dell'incrocio con la strada, che diventa il nodo `jid`.
    """
    K = lambda g: (round(g['lon'], 7), round(g['lat'], 7))
    ids = ids or QUERCUS_SENTIERI | {QUERCUS_SERVIZIO}
    ways = {el['id']: el for el in elements if el.get('type') == 'way' and el['id'] in ids}
    count = collections.Counter(K(g) for w in ways.values() for g in w['geometry'])
    if junction is None:
        jkey = K(ways[QUERCUS_SERVIZIO]['geometry'][0])       # il primo punto della via di servizio è l'incrocio
    else:
        jkey = min((K(g) for w in ways.values() for g in w['geometry']), key=lambda k: math.dist(to_local(*k), junction))
    count[jkey] += 1
    names, out = {}, []
    base = {'bridge': False, 'deco': False, 'name': None, 'osm': set(), 'tunnel': False}
    for wid, w in ways.items():
        g = w['geometry']
        cur = [g[0]]
        for pt in g[1:]:
            cur.append(pt)
            if count[K(pt)] > 1 or pt is g[-1]:
                ends = (K(cur[0]), K(cur[-1]))
                if all(count[k] > 1 for k in ends) and ends[0] != ends[1]:
                    nids = []
                    for k, gp in zip(ends, (cur[0], cur[-1])):
                        nid = jid if k == jkey else names.setdefault(k, f'bosco:{prefix}{len(names)}')
                        pos.setdefault(nid, bosco_map(to_local(gp['lon'], gp['lat']), anchors))
                        nids.append(nid)
                    poly = [bosco_map(to_local(q['lon'], q['lat']), anchors) for q in cur]
                    poly[0], poly[-1] = pos[nids[0]], pos[nids[1]]
                    path = wid != drive
                    out.append({**base, 'a': nids[0], 'b': nids[1], 'poly': poly, 'cls': 'path' if path else 'unclassified',
                                'foot': path, 'walk': path, 'osm': {wid}})
                cur = [pt]
    return out


def bosco_road(core, pos, elements):
    """Archi della strada compressa (fino al vivaio), più via di servizio e sentieri dell'area Quercus."""
    nodes = {n for e in core for n in (e['a'], e['b'])}
    start = min(nodes, key=lambda n: math.dist(pos[n], BOSCO_START))
    if math.dist(pos[start], BOSCO_START) > 3:
        print('  ATTENZIONE: incrocio di partenza della strada del bosco non trovato')
        return [], []
    a, b, c, anchors = bosco_chain()
    a[0] = pos[start]
    pos['bosco:svolta'], pos['bosco:quercus'], pos['bosco:vivaio'] = a[-1], b[-1], c[-1]
    base = {'bridge': False, 'foot': False, 'deco': False}
    real = length(BOSCO_ROUTE[:QUERCUS_A + 2]) + length(VIVAIO_ROUTE)
    print(f'  strada del bosco: {length(a) + length(b) + length(c):.0f} m (tracciato reale {real:.0f} m, scala {BOSCO_SCALA}; '
          f'fino all\'area Quercus {length(a) + length(b):.0f} m, poi {length(c):.0f} m fino al vivaio)')
    paths = bosco_ways(elements, anchors, pos)
    print(f'  area Quercus: via di servizio {sum(length(e["poly"]) for e in paths if not e["walk"]):.0f} m, '
          f'sentieri {sum(length(e["poly"]) for e in paths if e["walk"]):.0f} m a scala reale')
    # Blocco M2: anello V2 del vivaio dalla goccia, e il sentiero della Base Scout (eccezione approvata)
    ring = bosco_ways(elements, anchors, pos, VIVAIO_ANELLO, VIVAIO_ROUTE[-1], 'bosco:vivaio', None, 'v')
    print(f'  vivaio: anello V2 {sum(length(e["poly"]) for e in ring):.0f} m a scala reale')
    paths += ring
    # Contrada Annunziata oltre l'incrocio del vivaio (OSM w252747446): si vede, non si percorre.
    deco = []
    for el in elements:
        if el.get('type') == 'way' and el['id'] == 252747446:
            real_pts = [to_local(g['lon'], g['lat']) for g in el['geometry']]
            keep = [bosco_map(q, anchors) for q in real_pts if inside(q, (ZONA_V[0] + 15, ZONA_V[1], ZONA_V[2] + 15, ZONA_V[3]))]
            if len(keep) > 1:
                deco.append({**base, 'a': None, 'b': None, 'poly': keep, 'cls': 'unclassified', 'name': None})
    base = {**base, 'osm': set(), 'tunnel': False, 'walk': False}
    road = [{**base, 'a': start, 'b': 'bosco:svolta', 'poly': a, 'cls': 'secondary', 'name': BOSCO_PROVINCIALE},
            {**base, 'a': 'bosco:svolta', 'b': 'bosco:quercus', 'poly': b, 'cls': 'tertiary', 'name': None},
            {**base, 'a': 'bosco:quercus', 'b': 'bosco:vivaio', 'poly': c, 'cls': 'tertiary', 'name': None, 'vivaio': True}]
    for name, where, parts in PERCORSI:
        if where == 'vivaio':
            mapped = [[bosco_map(q, anchors) for q in part] for part in parts]
            scout = walk_paths(name, mapped, road, pos, host=lambda e: e.get('vivaio'))
            print(f'  {name}: {sum(length(e["poly"]) for e in scout):.0f} m')
            paths += scout
    return road + paths, deco


# ─────────────────────────────────────────────────────────────────────────────
# Blocco M2 · a piedi, zone pedonali, vie cieche fino ai luoghi
# ─────────────────────────────────────────────────────────────────────────────
M2_ZONE = {'robinson': '40.82154,16.41186,40.82469,16.41660', 'villa': '40.81587,16.41506,40.81758,16.41850',
           'meninni': '40.81092,16.42978,40.81416,16.43453', 'stazione': '40.82451,16.41779,40.82613,16.41969',
           'colacola': '40.81776,16.43477,40.81902,16.43714', 'fiera': '40.82550,16.41031,40.82712,16.41482'}
def osm_m2():
    """Dati OSM delle zone del blocco M2 (parchi, Villa, Casino di Meninni, stazione, Fiera, ponti dei binari), in cache."""
    bb = OVERPASS_BBOX
    return overpass_cached('m2', f"""[out:json][timeout:160];
({''.join(f'nwr({b});' for b in M2_ZONE.values())}
 way["railway"]["bridge"]({bb});way["highway"]["tunnel"]({bb});way["highway"]["layer"~"^-"]({bb});
 node["railway"~"level_crossing|crossing"]({bb});way["railway"~"platform"]({bb});
);out tags geom;""")


def osm_polygon(elements, wid):
    for el in elements:
        if el.get('type') == 'way' and el['id'] == wid and el.get('geometry'):
            return Polygon([to_local(g['lon'], g['lat']) for g in el['geometry']]).buffer(0)
    return None


# Nomi dei tratti a piedi senza nome in OSM (per targa e cartelli)
WALK_NOMI = {578892844: 'Sentiero degli scavi', 682777030: 'Sentiero degli scavi', 682776965: 'Sentiero degli scavi',
             1288066843: 'Pineta Parco Robinson', 1288066841: 'Pineta Parco Robinson', 1288066847: 'Pineta Parco Robinson',
             1288066840: 'Pineta Parco Robinson', 1288066845: 'Pineta Parco Robinson', 1288066844: 'Parco Robinson',
             1288066842: 'Parco Robinson', 1288066846: 'Parco Robinson', 1288069906: 'Scale della stazione',
             1288069907: 'Scale della stazione', 1288069908: 'Scale della stazione', 1288069910: 'Scale della stazione',
             1288069909: 'Sottopassaggio della stazione', 1195312391: 'Villa Comunale', 1195312392: 'Villa Comunale',
             1195312390: 'Villa Comunale', 1195312393: 'Villa Comunale', 1195312394: 'Villa Comunale',
             # blocco N5: in OSM non hanno nome
             682777028: 'Sentiero di Capotenda', 682777027: 'Sentiero di Capotenda', 682777029: 'Sentiero di Capotenda',
             682777031: 'Sentiero di Capotenda', 578916724: 'Sentiero di Capotenda', 578916725: 'Sentiero di Capotenda',
             578916726: 'Sentiero di Capotenda', 578916727: 'Sentiero di Capotenda', 578916728: 'Sentiero di Capotenda',
             # blocco 4.7
             600751157: 'Larghetto San Francesco'}


def luoghi_m2(elements):
    """
    GEO.m2: sagome e punti OSM dei luoghi del blocco M2 (Pineta e Parco Robinson, Monumento ai Caduti con le
    panchine della Villa, monumento alla Cola Cola), in metri locali.
    """
    ways = {el['id']: el for el in elements if el.get('type') == 'way' and el.get('geometry')}
    nodes = {el['id']: el for el in elements if el.get('type') == 'node'}
    ring = lambda w: flat([to_local(g['lon'], g['lat']) for g in ways[w]['geometry'][:-1]]) if w in ways else []
    pt = lambda n: [round(v, 1) for v in to_local(nodes[n]['lon'], nodes[n]['lat'])] if n in nodes else None
    villa = osm_polygon(elements, 327411255)
    benches = []
    for el in nodes.values():
        t = el.get('tags') or {}
        e, n = to_local(el['lon'], el['lat'])
        if t.get('amenity') == 'bench' and villa is not None and villa.buffer(2).contains(Point(e, n)):
            benches.append([round(e, 1), round(n, 1), 1 if t.get('backrest') == 'yes' else 0])
    out = {
        'robinson': ring(473031981),                     # Pineta Parco Robinson (leisure=park, pini)
        'giochi': pt(5659135030),                         # leisure=playground
        'busto': ring(411137974),                         # historic=memorial, bust, al centro dei vialetti
        'fontanella': pt(5659135226),                     # amenity=drinking_water
        'belvederi': [p for p in (pt(11945189869), pt(11945189969)) if p],
        'riparo': pt(5659135225),                         # amenity=shelter, «Observation»
        'caduti': ring(411137249),                        # Monumento ai Caduti (Q136344179)
        'panchine': sorted(benches),                      # panchine OSM della Villa Comunale
        'fontane': [p for p in (pt(4630401137), pt(4630401138)) if p],   # «Fontanone gemello»
        'colacola': ring(411137509),                      # historic=memorial: monumento alla Cola Cola (Via Bari)
    }
    if not luoghi_m2.detto:
        luoghi_m2.detto = True
        print(f'  luoghi del blocco M2: {len(benches)} panchine nella Villa, '
              + ', '.join(k for k, v in out.items() if not v) + (' mancanti' if not all(out.values()) else 'tutto trovato'))
    return out


luoghi_m2.detto = False


# Vie cieche reali che diventano percorribili fino a un punto, con l'inversione a goccia (committente,
# 01/10/2026, come la strada del Bosco): id OSM della via, punto dove finisce, perché.
VIE_CIECHE = [
    (946720266, (-140, 1044)),      # strada della Fiera fino al parcheggio dello stadio (w1340515588): la goccia resta fuori dalla recinzione
    (28355376, (1912, 126)),        # Via Bari fino al monumento alla Cola Cola (OSM w411137509)
    (1158532123, (1559, -816)),     # blocco N5b: via Guardialto Alto fino al piazzale dei campi di Sportland (vedi SERVIZIO_OSM)
]
# Blocco N5b (piano approvato dal committente il 14/10/2026, risposta «1b»; eccezione scritta in CLAUDE.md): la SP201 torna
# percorribile oltre lo sterrato del Casino di Meninni fino al bivio di via Guardialto Alto (OSM w1158532123, highway=service),
# e questa fino al piazzale sterrato davanti ai campi di Sportland, fuori dal recinto del centro sportivo (OSM w1158532121) e
# dal cancello della pizzeria (Street View ottobre 2025, satellite). In OSM via Guardialto Alto è cieca: niente anello, la goccia
# del mezzo sta nel piazzale. Le `service` non entrano nella rete: questa sì, per id, come sterrato (il resto resta decorativo).
SERVIZIO_OSM = {1158532123}
# Blocco N4 (piano approvato dal committente il 14/10/2026, eccezione scritta in CLAUDE.md): la strada del Casino di
# Meninni. Non è in OSM: uno sterrato di circa 20 m che lascia la SP201 (Via Guardialto, OSM w1068971736) ed entra nello
# spiazzo di terra battuta davanti al cancello, dove si parcheggia (Street View ottobre 2025 da [1432, -462] e
# [1448, -489], solo come riferimento). Finisce con la goccia del mezzo, girata verso nord-est lungo lo spiazzo e lontana
# dal muro di cinta; la goccia di prima, in mezzo alla SP201 a [1520, -612], non c'è più e oltre l'incrocio la SP201 torna
# decorativa. Superficie: terra (SUPERFICI).
STRADA_MENINNI = ('Ingresso del Casino di Meninni', [(1434, -468), (1444, -467), (1451, -463)], 4)
# Il giardino a piedi (sostituisce il percorso del blocco M2, attaccato alla SP201 in due punti): dal fondo dello
# sterrato, il cancello, su per i pini d'Aleppo fino a una decina di metri dal fronte nord-ovest del Casino, poi in curva
# larga attorno al lato sud-ovest (a 5–7 m dalle torrette d'angolo) e dietro, fino alla goccia della figurina nella radura
# dello spazio piano dei cipressi (FAI; radura sul satellite). Niente svolte strette.
GIARDINO_MENINNI = ('Giardino del Casino di Meninni', [(1451, -463), (1467, -474), (1484, -486), (1500, -495), (1516, -503),
                                                      (1532, -511), (1545.5, -519.7), (1551.4, -528.0), (1550.6, -535.0),
                                                      (1548.7, -541.0), (1554.6, -550.0), (1562.9, -558.6), (1571.0, -561.9),
                                                      (1578.7, -565.6), (1590, -572)])
# Muro di cinta del Casino (satellite e Street View di ottobre 2025, indicativo come il ponticello di San Michele): lungo
# la SP201 a circa 15 m dall'asse, poi su a nord-est fino all'angolo nord, giù a sud-est fino ai due corpi bassi
# (OSM w411137117, w411137478) e oltre, dove il satellite lo mostra tra la pineta e l'uliveto. A sud non si vede.
MURO_MENINNI = [
    [(1540, -620), (1486.5, -533.7), (1462, -487), (1494, -397), (1572, -473)],
    [(1606, -494), (1614, -499)],
    [(1628, -503), (1656, -517), (1687, -541), (1716, -572)],
]
CANCELLO_MENINNI = (1467, -474)       # tra due pilastri, sul muro nord-ovest (Street View: «un pilastro, forse il varco»)
# Percorsi a piedi senza dati OSM (eccezioni approvate dal committente il 01/10/2026): si disegnano solo
# perché chiudono un anello con vie reali. Punti scelti sul satellite (solo come riferimento) tra gli
# edifici reali. Ogni percorso è un elenco di tratti: un estremo in comune tra due tratti è un incrocio,
# un estremo usato una volta sola si attacca alla via più vicina.
PERCORSI = [
    # Fiera di San Giorgio: due tratti dal cancello OSM n8763525337 alla strada (entrata e uscita), il viale
    # a ovest del padiglione grande e un giro nel piazzale tra i padiglioni.
    ('Fiera di San Giorgio', 'city', [
        [(-80, 1039), (-75, 1022)], [(-75, 1022), (-67, 1037)],
        [(-75, 1022), (-84, 1010), (-88, 992), (-84, 978), (-70, 969)],
        [(-70, 969), (-45, 968), (-20, 963), (-19, 945), (-22, 930)], [(-22, 930), (-45, 929), (-70, 934), (-70, 969)]]),
    # Base Scout Gravina 1: dalla strada del vivaio su per il prato fino alla base, attorno, e giù per
    # l'area pic-nic (coordinate reali, zona del vivaio a scala reale).
    ('Sentiero della Base Scout', 'vivaio', [
        [(-2990, -7447), (-3012, -7420), (-3045, -7386), (-3080, -7352), (-3097, -7334), (-3106, -7313), (-3127, -7311),
         (-3140, -7330), (-3133, -7352), (-3110, -7385), (-3092, -7430), (-3085, -7480), (-3080, -7530), (-3076, -7561)]]),
]
# Blocco N5c (richiesta del committente del 14/10/2026): il percorso a piedi nel giardino di Hortus.
# Dal cancello su Via Giacomo Leopardi sale tra i terrazzamenti di tufo fino alla panchina panoramica
# affacciata sul Fondovico e sulla gravina, poi fa il giro della terrazza alta e riscende verso il cancello.
GIARDINO_HORTUS = (
    'Giardino di Hortus',
    [
        [(-26.0, -248.0), (-29.0, -245.0), (-33.0, -241.0), (-36.5, -235.0), (-37.5, -228.0), (-35.0, -227.0)],
        [(-35.0, -227.0), (-31.0, -230.0), (-28.0, -237.0), (-26.0, -248.0)],
    ]
)


def split_edge(edges, pos, pt, ok=lambda e: True, near=3.0):
    """
    Taglia la via (tra quelle che soddisfano `ok`) più vicina a `pt` nel suo punto più vicino e restituisce
    l'id del nodo: quello vecchio se il taglio cade a meno di `near` m da un estremo.
    """
    P = Point(pt)
    best = min((e for e in edges if ok(e)), key=lambda e: LineString(e['poly']).distance(P))
    line = LineString(best['poly'])
    d = line.project(P)
    if d < near:
        return best['a']
    if line.length - d < near:
        return best['b']
    q = line.interpolate(d)
    nid = f'taglio:{q.x:.1f},{q.y:.1f}'
    pos[nid] = (q.x, q.y)
    run, k = 0.0, 0
    pts = best['poly']
    while k < len(pts) - 2 and run + math.dist(pts[k], pts[k + 1]) < d:
        run += math.dist(pts[k], pts[k + 1])
        k += 1
    first = {**best, 'b': nid, 'poly': pts[:k + 1] + [(q.x, q.y)]}
    second = {**best, 'a': nid, 'poly': [(q.x, q.y)] + pts[k + 1:]}
    edges[edges.index(best):edges.index(best) + 1] = [first, second]
    return nid


def branch_to(tree, core_nodes, target):
    """Archi dell'albero cieco che portano dal nucleo al nodo `target` (ricerca in ampiezza)."""
    adj = collections.defaultdict(list)
    for e in tree:
        adj[e['a']].append(e)
        adj[e['b']].append(e)
    prev, queue = {target: None}, [target]
    while queue:
        n = queue.pop(0)
        if n in core_nodes:
            out = []
            while prev[n] is not None:
                e = prev[n]
                out.append(e)
                n = e['a'] if e['b'] == n else e['b']
            return out
        for e in adj[n]:
            m = e['b'] if e['a'] == n else e['a']
            if m not in prev:
                prev[m] = e
                queue.append(m)
    return []


def walk_paths(name, parts, edges, pos, host=lambda e: not e['deco'] and not e.get('walk'), cls='path'):
    """Percorso a piedi da un elenco di tratti (PERCORSI): incroci interni e attacchi alle vie."""
    ends = collections.Counter(p for part in parts for p in (part[0], part[-1]))
    node = {}
    for p, k in ends.items():
        if k > 1:
            node[p] = f'piedi:{name}:{p[0]:.0f},{p[1]:.0f}'
            pos[node[p]] = p
        else:
            node[p] = split_edge(edges, pos, p, host)
    base = {'cls': cls, 'name': name, 'bridge': False, 'foot': True, 'deco': False, 'walk': True, 'osm': set(), 'tunnel': False}
    out = []
    for part in parts:
        a, b = node[part[0]], node[part[-1]]
        out.append({**base, 'a': a, 'b': b, 'poly': [pos[a]] + list(part[1:-1]) + [pos[b]]})
    return out


SUPERFICI = {'sett': 1, 'paving_stones': 1, 'asphalt': 2, 'concrete': 2, 'paved': 2, 'unhewn_cobblestone': 3, 'cobblestone': 3,
             'ground': 4, 'dirt': 4, 'rock': 4, 'gravel': 4, 'compacted': 4, 'fine_gravel': 4}
PIAZZA_DUOMO = 385146363     # Piazza Benedetto XIII (area pedonale OSM, sett): sul satellite lastre chiare con file più scure a rombi
PIAZZA_DUOMO_VIA = 76156682  # la via che la attraversa (paving_stones): stesso disegno a rombi
ROMBI = 5


def superfici():
    """
    Blocco N1: superficie OSM delle vie del centro storico (sett, paving_stones, asphalt…) per id della via,
    più la sagoma di Piazza Benedetto XIII. Query Overpass piccola, in cache (tools/.cache/superfici.json).
    Codici: 1 lastre (chianche), 2 asfalto, 3 ciottoli, 4 terra, 5 lastre a rombi (Piazza Benedetto XIII).
    """
    m = 30
    bb = (f'{ORIGIN[0] + (Z0[2] - m) / M_LAT:.6f},{ORIGIN[1] + (Z0[0] - m) / M_LON:.6f},'
          f'{ORIGIN[0] + (Z0[3] + m) / M_LAT:.6f},{ORIGIN[1] + (Z0[1] + m) / M_LON:.6f}')
    q = (f'[out:json][timeout:120];way["highway"]["surface"]({bb});out tags;'
         f'(way({PIAZZA_DUOMO});way["landuse"~"grass|flowerbed"]({bb});way["leisure"="garden"]({bb}););out geom tags;')
    els = overpass_cached('superfici', q)
    codes = {el['id']: SUPERFICI[el['tags']['surface']] for el in els if el['tags'].get('surface') in SUPERFICI}
    for w in (PIAZZA_DUOMO, PIAZZA_DUOMO_VIA):
        if w in codes:
            codes[w] = ROMBI
    piazza = next((Polygon([to_local(p['lon'], p['lat']) for p in el['geometry']]) for el in els
                   if el['id'] == PIAZZA_DUOMO and 'geometry' in el), None)
    return codes, piazza


def build_network(data, buildings, bosco_osm):
    """
    Rete percorribile (2-core del grafo, più le vie cieche del centro storico con la goccia)
    e vie decorative: le vie cieche reali della città moderna, visibili ma non percorribili.
    """
    edges, pos = build_edges(data['segment'], data['connector'])
    edges = [e for e in edges if e['a'] != e['b'] and shapely.contains_xy(CITY_ROADS, *np.array(e['poly']).T).all()]
    # Blocco N1: superficie OSM (metri per codice: le vie unite da merge_chains tengono la più lunga)
    codes, _ = superfici()
    for e in edges:
        code = next((codes[w] for w in sorted(e['osm']) if w in codes), 0)
        e['surf'] = {code: length(e['poly'])} if code else {}
        if e['osm'] & SERVIZIO_OSM:
            e['surf'] = {4: length(e['poly'])}         # blocco N5b: via Guardialto Alto è uno sterrato chiaro
    edges, pos = merge_close_nodes(edges, pos)
    # Blocco M2: Villa Comunale e Piazza della Repubblica pedonali (decisione del committente)
    m2 = osm_m2()
    areas = [a.buffer(1.0) for a in (osm_polygon(m2, w) for w in PEDONALI_AREE) if a is not None]
    for e in edges:
        if e['deco'] or e.get('walk') or e['cls'] not in DRIVABLE or e['name'] in PEDONALI_NO:
            continue
        if e['osm'] & (PEDONALI_OSM | PEDONALI_FONDOVITO) or any(a.contains(Point(midpoint(e['poly']))) for a in areas):
            e['walk'] = True
            print(f'  pedonale: {e["name"] or "via senza nome"} ({length(e["poly"]):.0f} m)')
    # Blocco N2: raccordi a piedi attraverso le aree pedonali reali (Gradoni → Piazza Pellicciari)
    for name, pts, code in RACCORDI_PIEDI:
        ends = [min(pos, key=lambda n, p=p: math.dist(pos[n], p)) for p in (pts[0], pts[-1])]
        if any(math.dist(pos[n], p) > 1.5 for n, p in zip(ends, (pts[0], pts[-1]))):
            sys.exit(f'raccordo {name}: gli estremi non cadono su due nodi della rete')
        a, b = ends
        edges.append({'a': a, 'b': b, 'poly': [pos[a]] + list(pts[1:-1]) + [pos[b]], 'cls': 'footway', 'name': name, 'osm': set(),
                      'bridge': False, 'foot': True, 'deco': False, 'walk': True, 'tunnel': False, 'surf': {code: math.dist(pos[a], pos[b])}})
        print(f'  raccordo a piedi: {name} ({math.dist(pos[a], pos[b]):.0f} m)')
    # Blocco N2: il ponticello di San Michele, dalla fine della terrazza (nodo OSM) a un nodo nuovo sul promontorio
    name, pts = PONTICELLO
    a = min(pos, key=lambda n: math.dist(pos[n], pts[0]))
    if math.dist(pos[a], pts[0]) > 1.5:
        sys.exit(f'{name}: la terrazza non finisce dove dovrebbe')
    b = f'piedi:{name}'
    pos[b] = pts[-1]
    edges.append({'a': a, 'b': b, 'poly': [pos[a]] + list(pts[1:]), 'cls': 'footway', 'name': name, 'osm': set(), 'bridge': False,
                  'foot': True, 'deco': False, 'walk': True, 'tunnel': False, 'surf': {1: length(pts)}})
    print(f'  {name}: {length(pts):.0f} m a piedi')
    # Blocco N5: il guado di Capotenda, dal nodo db9552 in fondo al sentiero lungo il torrente al greto dell'altra sponda
    name, pts = GUADO
    a = min(pos, key=lambda n: math.dist(pos[n], pts[0]))
    if math.dist(pos[a], pts[0]) > 1.5:
        sys.exit(f'{name}: il sentiero lungo il torrente non finisce dove dovrebbe')
    b = f'piedi:{name}'
    pos[b] = pts[-1]
    edges.append({'a': a, 'b': b, 'poly': [pos[a]] + list(pts[1:]), 'cls': 'path', 'name': name, 'osm': {578916734, 578916735},
                  'bridge': False, 'foot': True, 'deco': False, 'walk': True, 'tunnel': False,
                  'surf': {4: length(pts)}})
    print(f'  {name}: {length(pts):.0f} m a piedi')
    # Blocco N5c: il giardino di Hortus a piedi (anello che parte e torna al cancello su Via Leopardi)
    hname, hparts = GIARDINO_HORTUS
    gate_pt = hparts[0][0]
    gate_node = split_edge(edges, pos, gate_pt, lambda e: 1384781495 in e['osm'] and not e['deco'])
    high_pt = hparts[0][-1]
    high_node = f'piedi:{hname}:alto'
    pos[high_node] = high_pt
    edges.append({'a': gate_node, 'b': high_node, 'poly': [pos[gate_node]] + list(hparts[0][1:-1]) + [high_pt],
                  'cls': 'path', 'name': hname, 'osm': set(), 'bridge': False, 'foot': True, 'deco': False,
                  'walk': True, 'tunnel': False, 'surf': {4: length(hparts[0])}})
    edges.append({'a': high_node, 'b': gate_node, 'poly': [high_pt] + list(hparts[1][1:-1]) + [pos[gate_node]],
                  'cls': 'path', 'name': hname, 'osm': set(), 'bridge': False, 'foot': True, 'deco': False,
                  'walk': True, 'tunnel': False, 'surf': {4: length(hparts[1])}})
    print(f'  {hname}: {length(hparts[0]) + length(hparts[1]):.0f} m di anello a piedi')
    # Vie cieche che portano a un luogo (VIE_CIECHE): si tagliano nel punto d'arrivo, dove andrà la goccia.
    ends = [split_edge(edges, pos, pt, lambda e, w=wid: w in e['osm'] and not e['deco'] and not e.get('walk')) for wid, pt in VIE_CIECHE]
    # Blocco N4: lo sterrato del Casino di Meninni lascia la SP201 in un incrocio nuovo e finisce nello spiazzo, da dove
    # il giardino si fa a piedi (GIARDINO_MENINNI, con la goccia della figurina in GOCCE_PIEDI).
    sname, pts, code = STRADA_MENINNI
    a = split_edge(edges, pos, pts[0], lambda e: 1068971736 in e['osm'] and not e['deco'] and not e.get('walk'))
    b = f'piedi:{sname}'
    pos[b] = pts[-1]
    edges.append({'a': a, 'b': b, 'poly': [pos[a]] + list(pts[1:]), 'cls': 'track', 'name': sname, 'osm': set(), 'bridge': False,
                  'foot': False, 'deco': False, 'walk': False, 'tunnel': False, 'surf': {code: length(pts)}})
    ends.append(b)
    gname, gpts = GIARDINO_MENINNI
    if math.dist(gpts[0], pts[-1]) > 0.1:
        sys.exit(f'{gname}: non parte dal fondo di {sname}')
    c = f'piedi:{gname}'
    pos[c] = gpts[-1]
    edges.append({'a': b, 'b': c, 'poly': list(gpts), 'cls': 'path', 'name': gname, 'osm': set(), 'bridge': False,
                  'foot': True, 'deco': False, 'walk': True, 'tunnel': False, 'surf': {code: length(gpts)}})
    print(f'  {sname}: {length(pts):.0f} m di sterrato; {gname}: {length(gpts):.0f} m a piedi')
    # Percorsi a piedi senza dati OSM in città (eccezioni approvate: Fiera, Casino di Meninni)
    for name, where, parts in PERCORSI:
        if where == 'city':
            new = walk_paths(name, parts, edges, pos, cls='footway' if 'Fiera' in name else 'path')   # la Fiera è asfaltata
            print(f'  {name}: {sum(length(e["poly"]) for e in new):.0f} m a piedi')
            edges += new
    drivable = [e for e in edges if not e['deco'] and not e.get('walk')]
    # Marciapiedi, passaggi e scalinate del centro storico (blocco G) contano per gli anelli: una via
    # carrabile resta se chiude un anello anche passando a piedi.
    walk = [e for e in edges if e.get('walk')]
    core = two_core(drivable + walk)
    core_nodes = {n for e in core for n in (e['a'], e['b'])}
    trees = dead_end_trees(drivable, core)
    extra = [e for t in trees
             if any(x['name'] in KEEP_DEAD_ENDS for x in t) and all(inside(midpoint(x['poly']), Z0) for x in t) for e in t]
    for nome, end in zip([f'w{wid}' for wid, _ in VIE_CIECHE] + [sname], ends):
        tree = next((t for t in trees if any(end in (x['a'], x['b']) for x in t)), [])
        branch = branch_to(tree, core_nodes, end) if end not in core_nodes else []
        print(f'  via cieca {nome} fino a {pos[end][0]:.0f}, {pos[end][1]:.0f}: {sum(length(e["poly"]) for e in branch):.0f} m in più')
        extra += [e for e in branch if e not in extra]
    # Blocco N2: tratti a piedi ciechi fino a uno slargo reale (GOCCE_PIEDI), con la goccia della figurina
    wtrees = dead_end_trees(walk, core)
    # Blocco N4: il giardino del Casino di Meninni parte dal fondo di una via cieca percorribile, non dal nucleo
    ancore = core + [e for e in extra if not e.get('walk')]
    wtrees2, nodi2 = dead_end_trees(walk, ancore), {n for e in ancore for n in (e['a'], e['b'])}
    for pt in GOCCE_PIEDI:
        end = min({n for e in walk for n in (e['a'], e['b'])}, key=lambda n: math.dist(pos[n], pt))
        tree = next((t for t in wtrees if any(end in (x['a'], x['b']) for x in t)), [])
        branch = branch_to(tree, core_nodes, end)
        if not branch:
            tree = next((t for t in wtrees2 if any(end in (x['a'], x['b']) for x in t)), [])
            branch = branch_to(tree, nodi2, end)
        print(f'  a piedi fino a {pos[end][0]:.0f}, {pos[end][1]:.0f}: {sum(length(e["poly"]) for e in branch):.0f} m con la goccia')
        extra += [e for e in branch if e not in extra]
    bosco_edges, bosco_deco = bosco_road(core, pos, bosco_osm)
    extra += bosco_edges
    tree = STRtree(buildings)
    # blocco N2: le mura reali del centro storico (nel diorama muri spessi 1,6 m) per le gocce della figurina
    walls = [local_geom(shape(i['geom'])).buffer(0.8) for i in data['infrastructure'] if i.get('class') == 'city_wall']
    walls = [w for w in walls if inside(w.centroid.coords[0], Z0)]
    muro = [LineString(m).buffer(1.0) for m in MURO_MENINNI]       # blocco N4: niente gocce nel muro di cinta
    net, loops = add_turnarounds(core, extra, pos, tree, buildings, walls=walls, ostacoli=muro)
    # Dove una via carrabile continua solo a piedi, la goccia lascia scegliere: si scende o si torna
    # indietro. Se la goccia non ci sta, la via resta e in fondo si prosegue per forza a piedi.
    drive, more = add_turnarounds([e for e in net if not e.get('walk')], [], pos, tree, buildings, prune=False, ostacoli=muro)
    net = two_core(drive + [e for e in net if e.get('walk')])
    net = largest_component(net)
    loops += more
    for n, k in degrees([e for e in net if not e.get('walk')]).items():
        if k == 1:
            e = next(x for x in net if n in (x['a'], x['b']) and not x.get('walk'))
            print(f'  in fondo a {e["name"] or "una via senza nome"} ({pos[n][0]:.0f}, {pos[n][1]:.0f}) si prosegue solo a piedi')
    ped = [e for e in net if e.get('walk')]
    print(f'  a piedi: {len(ped)} tratti su {len(walk)} ({sum(length(e["poly"]) for e in ped):.0f} m), '
          f'di cui scalinate {sum(e["cls"] == "steps" for e in ped)} ({sum(length(e["poly"]) for e in ped if e["cls"] == "steps"):.0f} m)')
    used = {id(e) for e in net}
    net = merge_chains(net)
    # Decorative: tutto ciò che resta fuori dalla rete, nella città moderna (il centro storico resta com'era).
    deco = [e for e in edges if id(e) not in used and not e['foot'] and not e['bridge'] and not e.get('tunnel') and not e.get('walk')
            and (not inside(midpoint(e['poly']), Z0) or e['osm'] & DECO_Z0)]
    deco = merge_chains(deco) + bosco_deco
    for e in net + deco:                              # geometria più leggera
        if not e.get('turn'):
            e['poly'] = list(LineString(e['poly']).simplify(0.35).coords)
    deco = [e for e in deco if length(e['poly']) >= 12]
    print(f'  rete: {len(net)} vie, {len(degrees(net))} incroci, '
          f'{sum(length(e["poly"]) for e in net) / 1000:.2f} km, {loops} inversioni a goccia; '
          f'{len(deco)} vie decorative ({sum(length(e["poly"]) for e in deco) / 1000:.2f} km)')
    return net, deco, pos


# ─────────────────────────────────────────────────────────────────────────────
# 3. Edifici
# ─────────────────────────────────────────────────────────────────────────────
KIND = {'house': 0, 'church': 1, 'cathedral': 2, 'shed': 3, 'apartments': 4, 'public': 5, 'rurale': 6, 'rudere': 7}


def building_kind(cls):
    if cls in ('church', 'chapel'):
        return KIND['church']
    if cls == 'cathedral':
        return KIND['cathedral']
    if cls in ('roof', 'shed', 'garage', 'garages', 'carport'):
        return KIND['shed']
    if cls in ('apartments', 'commercial', 'office', 'retail', 'hotel'):
        return KIND['apartments']
    if cls in ('school', 'library', 'post_office', 'civic', 'government', 'public', 'hospital', 'university'):
        return KIND['public']
    return KIND['house']


def reliable_height(b):
    """
    Altezza affidabile in metri, oppure None.
    Si usano il numero di piani e l'altezza di OpenStreetMap. Le altezze stimate
    dalle immagini aeree (Microsoft ML Buildings) nel centro storico sono spesso
    assurde (1,5-2,5 m per un condominio) e si scartano: le stima il diorama per zona.
    """
    if b.get('num_floors'):
        return b['num_floors'] * 3.3 + 0.6
    if not b.get('height'):
        return None
    srcs = b.get('sources') or []
    src = next((x for x in srcs if x.get('property') == '/properties/height'), None) \
        or next((x for x in srcs if not x.get('property')), None)
    return b['height'] if src and src.get('dataset') == 'OpenStreetMap' else None


def osm_id(b):
    """Id della way OpenStreetMap da cui viene un edificio di Overture (il record_id dice «w411140601@1»), o None."""
    for s in b.get('sources') or []:
        r = s.get('record_id') or ''
        if r.startswith('w') and r[1:].split('@')[0].isdigit():
            return int(r[1:].split('@')[0])
    return None


def build_buildings(raw):
    area = CITY_ZONE
    out = []
    for b in raw:
        if b.get('is_underground'):
            continue
        g = local_geom(shape(b['geom'])).intersection(area)
        polys = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
        osm = osm_id(b)
        for p in polys:
            if p.is_empty:
                continue
            # centro storico a 0,3 m (come nelle fasi 2–3), città moderna a 0,5 m
            p = p.simplify(0.3 if inside(p.centroid.coords[0], Z0) else 0.5, preserve_topology=True)
            if p.is_empty or p.area < 8:
                continue
            b_name = (b.get('names') or {}).get('primary')
            b_kind = building_kind(b.get('class'))
            # Blocco 4.7: in Via Santa Cecilia non c'è alcuna chiesa, l'edificio è una casa normale
            if osm == 411148976 or b_name == 'Chiesa di Santa Cecilia':
                b_name = None
                b_kind = KIND['house']
            out.append({'poly': p, 'kind': b_kind, 'cls': b.get('class'),
                        'name': b_name, 'height': reliable_height(b),
                        'level': b.get('level') or 0, 'osm': osm})
    print(f'  edifici: {len(out)}')
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 3b. Vie libere dagli edifici
#     Le mezzerie OSM non stanno sempre al centro dei vicoli e le carreggiate
#     del diorama hanno una larghezza fissa per classe: così alcune facciate
#     finivano sulla strada e il mezzo sembrava attraversare le case.
#     Qui (1) si ricentra la via tra le facciate, (2) la si restringe dove il
#     vicolo è stretto, (3) si ritagliano le sagome lungo la carreggiata e
#     (4) i corpi sopraelevati attraversati dalla via diventano archi.
# ─────────────────────────────────────────────────────────────────────────────
CLASS_WIDTH = {0: 8.0, 1: 7.0, 2: 4.6, 3: 4.2, 4: 4.5, 5: 3.2, 6: 3.6}   # = CONFIG.road.widths in index.html
# Città moderna (Z1): nelle vie urbane la larghezza comprende i marciapiedi, che index.html
# disegna sui bordi del nastro; le vie di campagna hanno solo la carreggiata.
URBAN_WIDTH = {0: 14.0, 1: 12.0, 2: 10.0, 3: 8.0, 4: 7.0, 5: 3.2, 6: 3.6}
RURAL_WIDTH = {0: 7.5, 1: 7.0, 2: 6.0, 3: 5.0, 4: 5.0, 5: 3.2, 6: 3.6}
URBAN_RAY = 11.0          # m: nella città moderna le facciate si cercano più lontano
BRIDGE_WIDTH, TURN_WIDTH = 5.5, 3.6
WALK_WIDTH, WALK_MIN = 2.4, 1.6   # m: i tratti a piedi sono stretti come i vicoli, e non ritagliano le case
MIN_WIDTH = 3.4           # m: il mezzo più largo (il trattore, circa 2,4 m) passa con margine
FACADE_GAP = 0.35         # m liberi tra il bordo della carreggiata e le facciate
MAX_SHIFT = 1.6           # m: spostamento massimo della mezzeria verso il centro del vicolo
RAY = 7.0                 # m: fin dove si cercano le facciate ai lati della via
ARCH_MAX_DEPTH = 14.0     # m: un corpo sopraelevato più profondo non è un arco, e viene tagliato


def centripetal_curve(pts, step=1.0):
    """
    La stessa curva che disegna index.html (THREE.CatmullRomCurve3 'centripetal',
    aperta, con i punti fantasma estrapolati agli estremi), campionata ogni ~step m.
    Il ritaglio degli edifici va fatto su questa, non sulla polilinea: tra punti
    radi la curva si allontana dalla spezzata anche di un metro.
    """
    P = [tuple(map(float, q)) for q in pts]
    n = len(P)
    if n < 3:
        return P
    out = []
    for i in range(n - 1):
        p1, p2 = P[i], P[i + 1]
        p0 = P[i - 1] if i > 0 else (2 * p1[0] - p2[0], 2 * p1[1] - p2[1])
        p3 = P[i + 2] if i + 2 < n else (2 * p2[0] - p1[0], 2 * p2[1] - p1[1])
        dt1 = math.dist(p1, p2) ** 0.5 or 1.0
        dt0 = math.dist(p0, p1) ** 0.5 or dt1
        dt2 = math.dist(p2, p3) ** 0.5 or dt1
        coef = []
        for k in (0, 1):
            x0, x1, x2, x3 = p0[k], p1[k], p2[k], p3[k]
            t1 = ((x1 - x0) / dt0 - (x2 - x0) / (dt0 + dt1) + (x2 - x1) / dt1) * dt1
            t2 = ((x2 - x1) / dt1 - (x3 - x1) / (dt1 + dt2) + (x3 - x2) / dt2) * dt1
            coef.append((x1, t1, -3 * x1 + 3 * x2 - 2 * t1 - t2, 2 * x1 - 2 * x2 + t1 + t2))
        m = max(1, math.ceil(math.dist(p1, p2) / step))
        for j in range(m):
            t = j / m
            out.append(tuple(c0 + c1 * t + c2 * t * t + c3 * t ** 3 for c0, c1, c2, c3 in coef))
    out.append(P[-1])
    return out


def _normal(line, s):
    """Punto e normale sinistra della polilinea alla progressiva s."""
    a, b = line.interpolate(max(0.0, s - 0.6)), line.interpolate(min(line.length, s + 0.6))
    tx, ty = b.x - a.x, b.y - a.y
    tl = math.hypot(tx, ty) or 1
    return line.interpolate(s), (-ty / tl, tx / tl)


def _side_clearance(p, n, tree, polys, ray_len=RAY):
    """Distanze dalle facciate a sinistra e a destra di p (None se p è dentro un edificio)."""
    out = []
    for sgn in (1, -1):
        ray = LineString([(p.x, p.y), (p.x + sgn * n[0] * ray_len, p.y + sgn * n[1] * ray_len)])
        best = ray_len
        for i in tree.query(ray):
            g = polys[i]
            if g.contains(p):
                return None
            hit = ray.intersection(g)
            if not hit.is_empty:
                best = min(best, p.distance(hit))
        out.append(best)
    return out


def in_z0(e):
    return inside(midpoint(e['poly']), Z0)


def full_width(e):
    """Larghezza piena della via, prima di restringerla tra le facciate."""
    code = CLASS_CODE.get(e['cls'], 2)
    if e.get('walk'):
        return WALK_WIDTH
    if in_z0(e):
        return CLASS_WIDTH[code]
    return (URBAN_WIDTH if e.get('urban') else RURAL_WIDTH)[code]


def is_urban(e, tree, polys):
    """Via di città (facciate vicine su almeno un lato per buona parte del percorso)."""
    line = LineString(e['poly'])
    ss = np.arange(2.0, max(2.5, line.length - 2), 6.0)
    near = 0
    for s in ss:
        p, n = _normal(line, s)
        d = _side_clearance(p, n, tree, polys, URBAN_RAY)
        near += d is None or min(d) < URBAN_RAY
    return near >= 0.35 * len(ss)


def recenter(e, tree, polys):
    """Sposta la mezzeria verso il centro del vicolo (estremi fermi sugli incroci)."""
    line = LineString(e['poly'])
    L = line.length
    if L < 12:
        return e['poly']
    count = max(2, int(L / 1.5))
    ss = [L * k / count for k in range(count + 1)]
    shifts, normals, points = [], [], []
    half = full_width(e) / 2
    ray = RAY if in_z0(e) else URBAN_RAY
    for s in ss:
        p, n = _normal(line, s)
        points.append(p)
        normals.append(n)
        d = _side_clearance(p, n, tree, polys, ray)
        if d is None or min(d) >= half + FACADE_GAP or min(d) >= ray:
            shifts.append(0.0)                       # nessuna facciata troppo vicina
        else:
            shifts.append(max(-MAX_SHIFT, min(MAX_SHIFT, (d[0] - d[1]) / 2)))
    k = 3                                            # media mobile: niente zig-zag
    smooth = [sum(shifts[max(0, i - k):i + k + 1]) / len(shifts[max(0, i - k):i + k + 1]) for i in range(len(shifts))]
    out = []
    for s, p, n, sh in zip(ss, points, normals, smooth):
        w = min(1.0, s / 8.0, (L - s) / 8.0)         # raccordo di 8 m verso gli incroci
        w = w * w * (3 - 2 * w)
        out.append((p.x + n[0] * sh * w, p.y + n[1] * sh * w))
    out[0], out[-1] = e['poly'][0], e['poly'][-1]
    return list(LineString(out).simplify(0.25).coords)


def fit_width(e, tree, polys):
    """Larghezza della carreggiata: quella della classe, ristretta nei vicoli stretti."""
    if e['bridge']:
        return BRIDGE_WIDTH
    if e.get('turn'):
        return WALK_MIN + 0.4 if e.get('walk') else TURN_WIDTH
    full = full_width(e)
    ray = RAY if in_z0(e) else URBAN_RAY
    line = LineString(centripetal_curve(e['poly']))
    gaps = []
    for s in np.arange(2.5, line.length - 2.5, 1.0 if in_z0(e) else 2.0):  # lontano dagli spigoli degli incroci
        p, n = _normal(line, s)
        d = _side_clearance(p, n, tree, polys, ray)
        if d is not None and max(d) < ray:
            gaps.append(d[0] + d[1])
    if not gaps:
        return full
    return round(max(WALK_MIN if e.get('walk') else MIN_WIDTH, min(full, float(np.quantile(gaps, 0.2)) - 2 * FACADE_GAP)), 1)


def free_roads(edges, pos, buildings):
    """Ricentra e dimensiona le vie (anche le decorative), ritaglia gli edifici, ricava gli archi."""
    ground = [b['poly'] for b in buildings if not b['level']]
    tree = STRtree(ground)
    for e in edges:
        e['urban'] = not in_z0(e) and not e['bridge'] and not e.get('turn') and is_urban(e, tree, ground)
    for e in edges:
        if not e['bridge'] and not e.get('turn'):
            e['poly'] = recenter(e, tree, ground)
    for e in edges:
        e['width'] = fit_width(e, tree, ground)

    # Carreggiate + margine, più gli slarghi agli incroci con 3+ vie (come in index.html).
    curves = {id(e): LineString(centripetal_curve(e['poly'])) for e in edges}
    parts = [curves[id(e)].buffer(e['width'] / 2 + FACADE_GAP, quad_segs=6) for e in edges]
    inc = collections.defaultdict(list)
    for e in edges:
        inc[e['a']].append(e['width'])
        inc[e['b']].append(e['width'])
    for n, ws in inc.items():
        if len(ws) >= 3:
            parts.append(Point(pos[n]).buffer(max(ws) / 2 + 0.3 + FACADE_GAP, quad_segs=6))
    corridor = shapely.union_all(parts)
    centerlines = [(curves[id(e)], e) for e in edges if not e['bridge'] and not e.get('turn')]

    out, arches, cut_area, whole_area = [], [], 0.0, 0.0
    for b in buildings:
        poly = b['poly']
        whole_area += poly.area
        if not poly.intersects(corridor):
            out.append(b)
            continue
        # Corpo sopraelevato attraversato dalla mezzeria: è un arco sulla via (solo nel centro storico).
        if b['level'] and inside(poly.centroid.coords[0], Z0):
            for line, e in centerlines:
                span = line.intersection(poly)
                if not span.is_empty and span.length > 0.5 and span.length <= ARCH_MAX_DEPTH:
                    piece = poly.intersection(line.buffer(e['width'] / 2 + FACADE_GAP + 0.6, cap_style='flat'))
                    piece = max(getattr(piece, 'geoms', [piece]), key=lambda g: g.area)
                    if piece.geom_type == 'Polygon' and piece.area > 2:
                        arches.append({'poly': piece.simplify(0.2), 'name': b['name'], 'width': e['width']})
        rest = poly.difference(corridor)
        cut_area += poly.area - rest.area
        pieces = [g for g in getattr(rest, 'geoms', [rest]) if g.geom_type == 'Polygon']
        # scarta schegge troppo piccole o troppo sottili per essere case; la semplificazione
        # alleggerisce i bordi tagliati e il secondo taglio li riporta fuori dalla strada
        pieces = [g for g in pieces if g.area >= 6 and not g.buffer(-0.7).is_empty]
        pieces = [max(getattr(h, 'geoms', [h]), key=lambda x: x.area)
                  for h in (g.simplify(0.25, preserve_topology=True).difference(corridor) for g in pieces)]
        pieces = [g for g in pieces if g.geom_type == 'Polygon' and g.area >= 6]
        pieces.sort(key=lambda g: -g.area)
        for i, g in enumerate(pieces):
            if b['kind'] == KIND['cathedral'] and i:
                continue                             # la Cattedrale resta un corpo unico
            main = i == 0
            out.append({**b, 'poly': g, 'name': b['name'] if main else None,
                        'kind': b['kind'] if main or b['kind'] not in (KIND['church'], KIND['cathedral']) else KIND['house']})
    print(f'  vie libere: {len(arches)} archi, {cut_area:.0f} m² di edifici ritagliati '
          f'({100 * cut_area / whole_area:.1f}% della superficie), {len(out)} edifici')
    return out, arches


def deco_off_roads(edges, deco):
    """
    Blocco M1: le vie decorative non corrono dentro la carreggiata di una via percorribile. Nei dati
    alcune (doppioni o corsie di servizio) le stanno sopra o a un metro, a un'altra quota: si vedeva
    un nastro doppio, e il terreno non poteva seguire tutte e due. Il tratto dentro la carreggiata
    (meno mezzo metro dal bordo) si toglie; i pezzi che restano, se lunghi almeno 12 m, rimangono.
    """
    curves = [LineString(centripetal_curve(e['poly'])) for e in edges if not e['bridge']]
    widths = [e['width'] for e in edges if not e['bridge']]
    lanes = shapely.union_all([c.buffer(max(0.5, w / 2 - 0.5), quad_segs=4) for c, w in zip(curves, widths)])
    roads = shapely.union_all([c.buffer(w / 2, quad_segs=4) for c, w in zip(curves, widths)])
    out, dropped, cut, removed, narrow = [], 0, 0, 0.0, 0
    for d in deco:
        line = LineString(d['poly'])
        inside_len = line.intersection(lanes).length
        if inside_len < 6:
            out.append(d)
            continue
        rest = line.difference(lanes)
        parts = [g for g in getattr(rest, 'geoms', [rest]) if g.geom_type == 'LineString' and g.length >= 12]
        removed += line.length - sum(g.length for g in parts)
        if not parts:
            dropped += 1
            continue
        cut += 1
        out += [{**d, 'poly': list(g.coords)} for g in parts]
    # Accanto a una via vera (lontano dagli innesti, 12 m da ogni capo) la decorativa si restringe
    # quanto basta perché il suo nastro non copra quello della via.
    for d in out:
        line = LineString(d['poly'])
        if line.length < 30:
            continue
        gap = min(roads.boundary.distance(line.interpolate(s)) for s in np.arange(12, line.length - 12, 2.0))
        if gap < d['width'] / 2 - 0.2 and not roads.contains(line.interpolate(line.length / 2)):
            d['width'] = round(max(3.2, 2 * gap - 0.4), 1)
            narrow += 1
    print(f'  vie decorative dentro le carreggiate: {dropped} tolte, {cut} accorciate ({removed:.0f} m in meno), {narrow} ristrette')
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 4. Idrografia, morfologia, luoghi
# ─────────────────────────────────────────────────────────────────────────────
def build_features(data):
    big = (AREA[0] - 200, AREA[1] + 200, AREA[2] - 200, AREA[3] + 200)
    river = next(w for w in data['water'] if (w.get('names') or {}).get('primary') == 'Torrente La Gravina')
    rl = LineString([to_local(*p) for p in river['geom']['coordinates']])
    rl = rl.intersection(box(big[0], big[2], big[1], big[3]))
    # l'appendice del bosco è un paesaggio compresso: il torrente reale si ferma 80 m prima
    rl = rl.difference(box(BOSCO[0] - 80, VIVAIO_SUD[2] - 80, BOSCO[1] + 80, BOSCO[3]))
    rl = max(getattr(rl, 'geoms', [rl]), key=lambda g: g.length).simplify(1.0)

    cliffs = [LineString([to_local(*p) for p in l['geom']['coordinates']])
              for l in data['land'] if l.get('class') == 'cliff' and l['geom']['type'] == 'LineString']
    cliffs = [c for c in cliffs if inside(c.centroid.coords[0], Z0)]

    walls, views, bridges = [], [], []
    for i in data['infrastructure']:
        g = local_geom(shape(i['geom']))
        if not inside(g.centroid.coords[0], Z0):
            continue
        name = (i.get('names') or {}).get('primary')
        if i.get('class') == 'city_wall':
            walls.append(g)
        elif i.get('class') == 'viewpoint':
            views.append((g, name))
        elif i.get('class') == 'bridge' and g.geom_type == 'LineString' and not name:
            bridges.append(g)

    areas = []
    for l in data['land_use']:
        # blocco N2: anche i prati incolti (meadow): nel centro storico la macchia del Fondovico (OSM w385177569)
        if l.get('class') not in ('pedestrian', 'plaza', 'park', 'grass', 'garden', 'meadow'):
            continue
        g = local_geom(shape(l['geom']))
        if g.geom_type == 'Polygon' and inside(g.centroid.coords[0], Z0):
            areas.append((l.get('class'), g.simplify(0.5)))

    # Scalinate reali (OSM highway=steps): nel diorama sono gradini di tufo da guardare, non vie.
    steps = []
    for sg in data['segment']:
        if sg.get('class') != 'steps' or sg['geom']['type'] != 'LineString':
            continue
        line = LineString([to_local(*p) for p in sg['geom']['coordinates']]).intersection(box(Z0[0], Z0[2], Z0[1], Z0[3]))
        if line.geom_type == 'LineString' and line.length > 4:
            steps.append(((sg.get('names') or {}).get('primary'), line))

    places = []
    keep = ('christian_place_of_worship', 'museum', 'historic_site', 'public_plaza', 'library', 'bridge', 'park', 'land_feature')
    for p in data['place']:
        cat = p.get('basic_category')
        e, n = to_local(*p['geom']['coordinates'])
        if cat in keep and inside((e, n), Z0) and (p.get('confidence') or 0) >= 0.6:
            places.append((e, n, (p.get('names') or {}).get('primary'), cat))
    return {'river': rl, 'cliffs': cliffs, 'walls': walls, 'views': views,
            'bridges': bridges, 'areas': areas, 'places': places, 'steps': steps}


# ─────────────────────────────────────────────────────────────────────────────
# 4b. Città moderna: quote reali, uso del suolo, altezze stimate, ferrovie, luoghi
# ─────────────────────────────────────────────────────────────────────────────
DEM_STEP = 30             # m: passo della griglia delle quote in GEO
COVER_STEP = 15           # m: passo della griglia dell'uso del suolo in GEO
COVER = {'campagna': 0, 'citta': 1, 'parco': 2, 'bosco': 3, 'campo': 4, 'uliveto': 5, 'industria': 6,
         'cimitero': 7, 'sport': 8, 'piazza': 9, 'macchia': 10, 'cava': 11, 'querce': 12, 'bruciato': 13, 'fitto': 14, 'roccia': 15,
         'vigna': 16, 'filari': 17}
# Blocco N5: la vigna di Botromagno (indicazione del committente del 03/10/2026: «a Botromagno vicino a Padre Eterno c'è la
# vigna di Botromagno»; piano approvato il 14/10/2026). Sul satellite a zoom 20 filari nord-sud a spalliera, ogni 2,4 m. Il
# contorno viene dagli elementi OSM: Via Madonna della Stella a sud-ovest, le carrarecce w578916725–726 a est (i vertici qui
# sotto sono loro punti), il bordo della zolla a ovest e nord 1 078 (dove finiscono i filari). Si tolgono le carreggiate.
VIGNA = [(-764, 891), (-835, 958), (-835, 1078), (-668, 1078), (-678.1, 1045.2), (-696.6, 1016.7), (-714.5, 997.7), (-729.1, 946.2)]
VIGNA_BORDI = {'Via Madonna della Stella': 8, 578916725: 6, 578916726: 6}     # metri tolti attorno alle vie
# Blocco N5b: gli uliveti a filari (approvati dal committente il 14/10/2026 coi numeri del piano di N5; il n. 1 è la vigna).
# Contorni indicativi dal satellite di Google (zoom 17–19, solo come riferimento visivo; le immagini sono spostate di 8–12 m
# rispetto a OSM), tranne il n. 3 che è l'uliveto OSM w1152762647. Si tolgono le carreggiate (ULIVETI_BORDO m dall'asse di ogni
# via) e quello che esce dalla zolla. `angolo`: direzione dei filari in gradi da est verso nord; ulivi ogni ULIVETI_PASSO m.
ULIVETI = [
    (2, [(1700, -409), (1748, -439), (1715, -547), (1667, -532)], 75,
     'a est del muro di cinta del Casino di Meninni (indicazione del committente in N4), striscia tra i muretti'),
    (3, [(1047.3, -1026.6), (1070.1, -1016.3), (1112.2, -984.1), (1116.7, -980.2), (1111.3, -974.8), (1105.5, -971.4), (1074.2, -961.8),
         (1029.3, -937.1), (986.3, -908.7), (949.9, -952.9), (1027.0, -1016.1), (1038.0, -1022.8)], -27, 'uliveto OSM w1152762647'),
    (4, [(944, -632), (1139, -644), (1160, -700), (1150, -760), (1150, -890), (1075, -940), (990, -895), (944, -874), (979, -780),
         (932, -721)], 50, 'Contrada Salsa, a ovest e a sud del Casino Scacchi (i terrazzamenti attorno al Casino sono a parte)'),
    (5, [(-487, -668), (-433, -680), (-385, -716), (-382, -758), (-415, -812), (-469, -794), (-490, -758), (-490, -704)], -38,
     'Terrasanta, tra la via curva e la scarpata del torrente'),
    (6, [(563, 1797), (602, 1800), (596, 1710), (560, 1710)], 90, 'accanto al Castello Svevo, lungo la carrareccia a sud'),
    (7, [(-188, -1010), (-149, -995), (-92, -1028), (-107, -1112), (-122, -1133), (-197, -1040)], -58,
     'Contrada Cozzarolo, il recinto murato a ovest'),
    # richiesta del committente del 14/10/2026: gli ulivi della Madonna della Stella stanno dall'altra parte della strada, tra
    # Contrada Botromagno e Via Madonna della Stella (satellite: uliveto a filari a sud della contrada, a ovest del fossato)
    (8, [(-503, 150), (-389, 255), (-362, 243), (-344, 162), (-329, 0), (-551, 0), (-551, 108)], 43,
     'tra Contrada Botromagno e Via Madonna della Stella, a ovest del fossato'),
]
ULIVETI_PASSO = 7.0
ULIVETI_BORDO = 5.0
OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
OVERPASS_BBOX = '40.79,16.39,40.85,16.46'
OVERPASS_QUERY = f"""[out:json][timeout:160];
(nwr["historic"]({OVERPASS_BBOX});
 nwr["amenity"="place_of_worship"]({OVERPASS_BBOX});
 nwr["railway"="station"]({OVERPASS_BBOX});
 nwr["leisure"~"park|stadium|sports_centre"]({OVERPASS_BBOX});
);out tags center;
way(76156899);out geom;
"""


def overpass():
    """Luoghi di OpenStreetMap che Overture non ha (monumenti, stazioni…), più la sagoma del Castello Svevo. In cache."""
    out = CACHE / 'overpass.json'
    if out.exists():
        return json.loads(out.read_text())['elements']
    r = SESSION.post(OVERPASS_URL, data={'data': OVERPASS_QUERY}, timeout=200,
                     headers={'User-Agent': 'gravina-3d (github.com/giuseppecassano5bit/gravina-3d)', 'Accept': 'application/json'})
    r.raise_for_status()
    out.write_text(r.text)
    return r.json()['elements']


def load_dem():
    """Tessera Copernicus GLO-30 (DSM, pixel di 1″): restituisce il campionamento bilineare in metri locali."""
    import tifffile
    with tifffile.TiffFile(CACHE / DEM_FILE) as tf:
        page = tf.pages[0]
        z = page.asarray().astype(np.float64)
        sx, sy = page.tags['ModelPixelScaleTag'].value[:2]
        lon0, lat0 = page.tags['ModelTiepointTag'].value[3:5]

    def at(e, n):
        lat = ORIGIN[0] + np.asarray(n, float) / M_LAT
        lon = ORIGIN[1] + np.asarray(e, float) / M_LON
        r, c = (lat0 - lat) / sy - 0.5, (lon - lon0) / sx - 0.5      # centri dei pixel (PixelIsArea)
        r0, c0 = np.floor(r).astype(int), np.floor(c).astype(int)
        fr, fc = r - r0, c - c0
        return (z[r0, c0] * (1 - fr) * (1 - fc) + z[r0, c0 + 1] * (1 - fr) * fc
                + z[r0 + 1, c0] * fr * (1 - fc) + z[r0 + 1, c0 + 1] * fr * fc)
    return at


def blur(a, sigma):
    """Sfocatura gaussiana separabile (sigma in celle), bordi replicati."""
    r = max(1, int(3 * sigma + 0.5))
    x = np.arange(-r, r + 1)
    k = np.exp(-x * x / (2 * sigma * sigma))
    k /= k.sum()
    b = np.pad(a, ((r, r), (0, 0)), mode='edge')
    b = sum(k[i] * b[i:i + a.shape[0]] for i in range(2 * r + 1))
    b = np.pad(b, ((0, 0), (r, r)), mode='edge')
    return sum(k[i] * b[:, i:i + a.shape[1]] for i in range(2 * r + 1))


def low_percentile(a, size, q):
    """Percentile basso su una finestra quadrata di `size` celle: toglie tetti e alberi dal DSM."""
    from numpy.lib.stride_tricks import sliding_window_view
    h = size // 2
    w = sliding_window_view(np.pad(a, h, mode='edge'), (size, size))
    return np.percentile(w, q, axis=(2, 3))


def building_density(buildings, E, N, sigma):
    """Frazione di suolo coperta da edifici attorno a ogni punto della griglia (E, N)."""
    step = E[1] - E[0]
    acc = np.zeros((len(N), len(E)))
    for b in buildings:
        c = b['poly'].centroid
        i, j = int(round((c.x - E[0]) / step)), int(round((c.y - N[0]) / step))
        if 0 <= i < len(E) and 0 <= j < len(N):
            acc[j, i] += b['poly'].area
    return blur(acc / (step * step), sigma / step)


def ground_model(dem_at, buildings):
    """
    Quote del terreno dal DSM Copernicus. Il DSM comprende tetti e alberi: in città si
    prende un percentile basso su 90 m e si smussa molto (35 m), in campagna e nel canyon
    si smussa poco (15 m), così la valle del torrente resta incisa.
    Restituisce la funzione di quota fine (10 m) e la griglia di GEO (DEM_STEP m).
    """
    f, M = 10, 180
    E = np.arange(BOUND[0] - M, BOUND[1] + M + 1, f, dtype=float)
    N = np.arange(BOUND[2] - M, BOUND[3] + M + 1, f, dtype=float)
    EE, NN = np.meshgrid(E, N)
    Z = dem_at(EE, NN)
    U = np.clip((building_density(buildings, E, N, 45) - 0.06) / 0.14, 0, 1)
    A = blur(Z, 1.5)
    B = blur(low_percentile(Z, 9, 20), 3.5)
    G = A * (1 - U) + B * U
    # Zolle del bosco (blocco L): il paesaggio è compresso e le quote reali lì sotto sono di un altro posto
    # (la valle a sud della città). Colline dolci: quote molto smussate, rilievo dimezzato attorno alla media.
    Wb = np.zeros_like(G)
    for z in BOSCHI:
        Wb = np.maximum(Wb, ((EE > z[0] - 60) & (EE < z[1] + 60) & (NN > z[2] - 60) & (NN < z[3] + (0 if z is BOSCO else 60))).astype(float))
    Wb = np.clip(blur(Wb, 5), 0, 1) * (NN < BOSCO[3] - 120)
    if Wb.any():
        S = blur(G, 10)
        mean = float((S * Wb).sum() / Wb.sum())
        G = G * (1 - Wb) + (mean + (S - mean) * 0.5) * Wb
    k = DEM_STEP // f
    grid = G[M // f::k, M // f::k][:(BOUND[3] - BOUND[2]) // DEM_STEP + 1, :(BOUND[1] - BOUND[0]) // DEM_STEP + 1].copy()
    ge = BOUND[0] + DEM_STEP * np.arange(grid.shape[1])
    gn = BOUND[2] + DEM_STEP * np.arange(grid.shape[0])
    active = zone_mask(ge, gn, DEM_STEP)
    fill_masked(grid, active)

    def at(e, n):
        x, y = (np.asarray(e) - E[0]) / f, (np.asarray(n) - N[0]) / f
        i, j = np.clip(np.floor(x).astype(int), 0, len(E) - 2), np.clip(np.floor(y).astype(int), 0, len(N) - 2)
        fx, fy = x - i, y - j
        return (G[j, i] * (1 - fx) * (1 - fy) + G[j, i + 1] * fx * (1 - fy) + G[j + 1, i] * (1 - fx) * fy + G[j + 1, i + 1] * fx * fy)
    print(f'  quote: griglia {grid.shape[1]} × {grid.shape[0]} ogni {DEM_STEP} m, da {grid.min():.0f} a {grid.max():.0f} m s.l.m.')
    return at, grid, A, E, N


def river_bed(river, dem_light):
    """Quota del letto del torrente in ogni vertice (m s.l.m.): minimo del DSM di traverso, smussato, sempre in discesa."""
    pts = list(river.coords)
    ys = []
    for i, (e, n) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        offs = np.arange(-20, 21, 5.0)
        ys.append(float(np.min(dem_light(e - ty / l * offs, n + tx / l * offs))))
    s = np.concatenate([[0], np.cumsum([math.dist(p, q) for p, q in zip(pts, pts[1:])])])
    ys = np.array(ys)
    sm = np.array([np.sum(ys * np.exp(-((s - x) / 60) ** 2)) / np.sum(np.exp(-((s - x) / 60) ** 2)) for x in s])
    return np.minimum.accumulate(sm)                  # il torrente scorre da nord verso sud


def fill_masked(grid, active):
    """
    Fuori dalle zolle i valori non servono: ognuno copia il vicino a sinistra (o la riga sopra),
    così le differenze e le serie di GEO diventano zeri e il blocco compresso quasi non cresce.
    """
    for j in range(grid.shape[0]):
        idx = np.flatnonzero(active[j])
        if not len(idx):
            grid[j] = grid[j - 1] if j else grid[j]
            continue
        grid[j, :idx[0]] = grid[j, idx[0]]
        for i in range(idx[0] + 1, grid.shape[1]):
            if not active[j, i]:
                grid[j, i] = grid[j, i - 1]


def raster(polys, E, N):
    """Maschera dei punti della griglia (E, N) dentro i poligoni."""
    m = np.zeros((len(N), len(E)), bool)
    for p in polys:
        x0, y0, x1, y1 = p.bounds
        i0, i1 = np.searchsorted(E, x0), np.searchsorted(E, x1)
        j0, j1 = np.searchsorted(N, y0), np.searchsorted(N, y1)
        if i1 > i0 and j1 > j0:
            xx, yy = np.meshgrid(E[i0:i1], N[j0:j1])
            m[j0:j1, i0:i1] |= shapely.contains_xy(p, xx, yy)
    return m


def vigna_botromagno(segments):
    """Blocco N5: il poligono della vigna di Botromagno (VIGNA meno le carreggiate di VIGNA_BORDI)."""
    lines = []
    for sg in segments:
        if sg.get('subtype') != 'road':
            continue
        ids = {w for w, _, _ in osm_ways(sg)}
        m = VIGNA_BORDI.get((sg.get('names') or {}).get('primary')) or max((VIGNA_BORDI.get(w, 0) for w in ids), default=0)
        if m:
            lines.append(LineString([to_local(*p) for p in sg['geom']['coordinates']]).buffer(m))
    poly = Polygon(VIGNA).difference(shapely.union_all(lines))
    poly = max(getattr(poly, 'geoms', [poly]), key=lambda g: g.area).simplify(0.5)
    print(f'  vigna di Botromagno: {poly.area:.0f} m²')
    return poly


def uliveti(segments):
    """Blocco N5b: i poligoni degli uliveti a filari (ULIVETI meno le carreggiate, dentro la zolla): [(n, poligono, angolo)]."""
    roads = [LineString([to_local(*p) for p in sg['geom']['coordinates']]).buffer(ULIVETI_BORDO) for sg in segments
             if sg.get('subtype') == 'road' and sg.get('class') not in ('footway', 'path', 'steps', 'pedestrian')]
    roads = shapely.union_all([r for r in roads if r.intersects(box(*BOUND[::2], *BOUND[1::2]))])
    zone = CITY_ZONE.buffer(-3)
    out = []
    for k, ring, ang, _ in ULIVETI:
        poly = Polygon(ring).difference(roads).intersection(zone)
        poly = max(getattr(poly, 'geoms', [poly]), key=lambda g: g.area).simplify(0.5)
        out.append((k, poly, ang))
    print('  uliveti a filari: ' + ', '.join(f'n. {k} {p.area:.0f} m²' for k, p, _ in out))
    return out


def land_cover(data, buildings, bosco_osm, rock=None, vigna=None, filari=()):
    """
    Uso del suolo su una griglia di COVER_STEP m (centri delle celle): colori del terreno e alberi nella città moderna.
    `rock`: la roccia di Botromagno (blocco M1), lungo il ciglio ovest e negli scavi.
    """
    s = COVER_STEP
    E = np.arange(BOUND[0] + s / 2, BOUND[1], s, dtype=float)
    N = np.arange(BOUND[2] + s / 2, BOUND[3], s, dtype=float)
    grid = np.zeros((len(N), len(E)), np.uint8)
    polys = collections.defaultdict(list)
    lu = {'farmland': 'campo', 'meadow': 'campo', 'orchard': 'uliveto', 'residential': 'citta', 'industrial': 'industria',
          'commercial': 'industria', 'cemetery': 'cimitero', 'park': 'parco', 'grass': 'parco', 'garden': 'parco',
          'pitch': 'sport', 'stadium': 'sport', 'pedestrian': 'piazza', 'plaza': 'piazza', 'quarry': 'cava'}
    for l in data['land_use']:
        kind = lu.get(l.get('class'))
        if kind:
            g = local_geom(shape(l['geom']))
            polys[kind] += [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon']
    for l in data['land']:
        kind = {'forest': 'bosco', 'wood': 'bosco', 'heath': 'macchia', 'scrub': 'macchia'}.get(l.get('class'))
        if kind and l['geom']['type'] in ('Polygon', 'MultiPolygon'):
            g = local_geom(shape(l['geom']))
            polys[kind] += [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon']
    dense = building_density(buildings, E, N, 30) > 0.12
    for kind in ('campo', 'uliveto', 'macchia', 'citta', 'industria', 'cava', 'bosco', 'parco', 'cimitero', 'sport', 'piazza'):
        m = raster(polys[kind], E, N)
        if kind == 'citta':
            m = dense                                    # la città è dove ci sono le case, non tutto il poligono "residenziale"
        grid[m] = COVER[kind]
    bosco_cover(grid, E, N, bosco_osm)
    if vigna is not None:
        grid[raster([vigna], E, N)] = COVER['vigna']   # blocco N5: la vigna di Botromagno
    if filari:
        grid[raster([p for _, p, _ in filari], E, N)] = COVER['filari']   # blocco N5b: gli uliveti a filari (niente ulivi a caso)
    # Blocco M2: la Pineta Parco Robinson (OSM w473031981, «parco con giochi, panchine, pini») è una pineta;
    # prato senza alberi attorno ai giochi e al busto al centro dei vialetti.
    m2 = osm_m2()
    pineta = osm_polygon(m2, 473031981)
    if pineta is not None:
        grid[raster([pineta], E, N)] = COVER['bosco']
        lu = luoghi_m2(m2)
        lawn = [Point(*lu['giochi']).buffer(13)] if lu['giochi'] else []
        if lu['busto']:
            lawn.append(Polygon(list(zip(lu['busto'][::2], lu['busto'][1::2]))).centroid.buffer(9))
        grid[raster(lawn, E, N)] = COVER['sport']
    if rock is not None and not rock.is_empty:
        grid[raster([g for g in getattr(rock, 'geoms', [rock]) if g.geom_type == 'Polygon'], E, N)] = COVER['roccia']
    fill_masked(grid, zone_mask(E, N, s))
    print('  uso del suolo:', ', '.join(f'{k} {100 * np.mean(grid == v):.0f}%' for k, v in COVER.items() if np.any(grid == v)))
    return grid


HEIGHT_CLASS = {'roof': 3.2, 'shed': 3.0, 'garage': 3.0, 'garages': 3.0, 'carport': 2.8, 'greenhouse': 3.0, 'grandstand': 8.0}


def city_height(b, dense, industrial):
    """
    Altezza (m) di un edificio della città moderna. OpenStreetMap non ha quasi mai i piani,
    e le stime di Microsoft sono troppo basse (6-7 m per un condominio): si stima per tipo
    e superficie. Palazzine da 2 a 5 piani nei quartieri, capannoni da 7 a 9 m, case di
    campagna da 1 a 2 piani.
    """
    if b['height']:
        return b['height']
    cls, area = b['cls'], b['poly'].area
    c = b['poly'].centroid
    seed = (math.sin(c.x * 12.9898 + c.y * 78.233) * 43758.5453) % 1
    if cls in HEIGHT_CLASS:
        return HEIGHT_CLASS[cls]
    if b['kind'] == KIND['church']:
        return 11 + seed * 4
    if cls in ('industrial', 'warehouse') or (industrial and area > 300):
        return 7 + seed * 2
    if b['kind'] == KIND['public']:
        return 3.3 * 3 + 0.6
    if not dense:
        floors = 1 if area < 150 or seed < 0.5 else 2
    elif area < 60:
        floors = 1
    elif area < 150:
        floors = 2 + (seed > 0.5)
    elif area < 400:
        floors = 3 + int(seed * 2.99)
    else:
        # blocco 4.6: in OSM gli isolati grandi sono spesso una sagoma sola, e su Street View (Via Tripoli, Via De Gasperi)
        # stanno in media su quattro livelli: da 4–6 a 3–5
        floors = 3 + int(seed * 2.99)
    return floors * 3.3 + 0.6


CITY_KIND = {'house': 0, 'church': 1, 'shed': 3, 'apartments': 4, 'public': 5, 'industry': 6, 'castle': 7, 'school': 8, 'villa': 9, 'padiglione': 10, 'tribuna': 11,
             'rudere': 12, 'villetta': 13}


def city_buildings(buildings, cover):
    """Edifici fuori dal centro storico, con tipo e altezza stimata."""
    s = COVER_STEP
    out = []
    for b in buildings:
        c = b['poly'].centroid
        i, j = int((c.x - BOUND[0]) / s), int((c.y - BOUND[2]) / s)
        code = cover[min(j, cover.shape[0] - 1), min(i, cover.shape[1] - 1)]
        dense = code in (COVER['citta'], COVER['industria'], COVER['parco'], COVER['piazza'], COVER['sport'])
        h = city_height(b, dense, code == COVER['industria'])
        kind = b['kind']
        if b['cls'] in ('industrial', 'warehouse') or (code == COVER['industria'] and b['poly'].area > 300):
            kind = CITY_KIND['industry']
        out.append({**b, 'height': h, 'kind': kind})
    return out


# Blocco E (risposte del committente del 30/09/2026): scuole, chiese senza nome in OSM, Casino di
# Meninni e «case rosa». La posizione viene da OSM o Overture (id nei commenti); l'edificio è la
# sagoma reale che contiene il punto (o la più vicina entro 6 m). Nessun contorno da Google.
SCHOOLS = [
    ('Liceo scientifico G. Tarantino', (762, -471), 3),         # Overture, Via Salvatore Quasimodo
    ('Liceo linguistico G. Tarantino', (661, 102), 3),          # Overture, Via Gorizia
    ('ITT Bachelet · IPSIA G. Galilei', (2628, 687), 2),        # OSM w1384764963 (area), w1384764964, nel P.I.P.
    ('Scuola primaria Padre Pio', (1117, -216), 2),             # OSM w411138848, Via Guardialto
    ('Scuola media Don E. Montemurro', (648, -323), 3),         # OSM w411138849, Via Tripoli
    ('Circolo didattico San Giovanni Bosco', (320, -139), 3),   # OSM r6148449, Corso Vittorio Emanuele
    ('Edificio scolastico S.G. Bosco', (910, -21), 3),          # OSM, nome dell'edificio
    ('Scuola secondaria N. Ingannamorte', (730, 418), 3),       # OSM n12091003369, Via Francesco Baracca
    ('Scuola dell\'infanzia Papa Giovanni Paolo II', (1212, -187), 1),   # OSM n12039009818
    ('Scuola dell\'infanzia Alla Fine dell\'Arcobaleno', (1368, 124), 1),   # OSM n12039071161
    ('Scuola secondaria Benedetto XIII', (284, -44), 3),        # Overture, Via Libertà
    ('Scuola primaria Don Saverio Valerio', (313, -766), 2),    # Overture, Via Sandro Pertini
    ('Scuola primaria Tommaso Fiore', (837, 351), 2),           # Overture, Via Fratelli Cervi
    ('Circolo didattico Savio-Fiore', (545, 1052), 2),          # Overture, Via Fratelli Cervi
    ('Scuola primaria Michele Soranno', (1748, 266), 2),        # Overture, Via Michele Soranno
    ('Scuola primaria Santomasi', (345, 335), 2),               # blocco 4.7: Corso Aldo Moro 6
]
CHURCHES = [
    ('Chiesa Gesù Buon Pastore', (1055, -176)),                 # OSM w328013129 (edificio senza nome)
    ('SS. Crocifisso e San Sebastiano', (442, -571)),           # OSM r6148330 e Overture
    # Blocco N3: il punto di Overture (658, 826) cadeva su un altro edificio (OSM r6148494); la chiesa è OSM w411139821
    # su Via Madonna della Grazia (satellite, Street View maggio 2025: la facciata con l'aquila accanto al convento)
    ('Santuario Madonna delle Grazie', (525, 907)),
    # Blocco N3: il punto di Overture (1080, 1140, Via Luigi Longo) cadeva sulla pensilina w411146608 (74 m²): il nome va
    # sulla chiesa grande col tetto a cono, OSM w411139942 (Street View, aprile 2025)
    ('Santi Pietro e Paolo', (1056, 1142)),
    ('Chiesa Dello Spirito Santo', (1734, 151)),                # blocco N3: OSM w1152762610 (building=yes), era una casa
]
MENINNI = ('Casino di Meninni', (1572, -536))                   # sul Guardialto, sopra la SP201 (Via Guardialto)
# Blocco N4: il Casino (OSM w411138340, abandoned:building=yes) è un rudere senza tetto di due piani (Street View di ottobre
# 2025: finestre vuote da cui si vede il cielo; satellite: i muri delle stanze dentro); muri alti circa 10 m. Anche i due
# corpi bassi sul muro di cinta (w411137117, w411137478, abandoned:building=yes) sono senza tetto sul satellite: ruderi bassi.
MENINNI_ALTO = 10.5
MENINNI_OSM = 411138340
MENINNI_CORPI = {411137117: 3.6, 411137478: 3.2}       # non sono in Overture (in OSM hanno solo abandoned:building): da Overpass
MENINNI_OVERPASS = '[out:json][timeout:60];way(id:411138340,411137117,411137478);out tags geom;'


def meninni_ruderi(city):
    """Blocco N4: il Casino di Meninni sulla sagoma OSM e i due corpi bassi abbandonati sul muro di cinta, come ruderi."""
    els = overpass_cached('meninni', MENINNI_OVERPASS)
    geo = {el['id']: Polygon([to_local(g['lon'], g['lat']) for g in el['geometry']]).buffer(0)
           for el in els if el.get('type') == 'way' and el.get('geometry')}
    b = next((x for x in city if x['name'] == MENINNI[0]), None)
    if b is not None and MENINNI_OSM in geo:
        print(f'  Casino di Meninni: sagoma OSM w{MENINNI_OSM} ({geo[MENINNI_OSM].area:.0f} m², Overture {b["poly"].area:.0f} m²)')
        b['poly'] = geo[MENINNI_OSM].simplify(0.3)
    for wid, h in MENINNI_CORPI.items():
        if wid in geo:
            city.append({'poly': geo[wid].simplify(0.3), 'kind': CITY_KIND['rudere'], 'cls': 'abandoned', 'name': None, 'height': h,
                         'level': 0, 'osm': wid})
            print(f'  rudere sul muro di cinta del Casino di Meninni: w{wid} ({geo[wid].area:.0f} m²)')



# ─────────────────────────────────────────────────────────────────────────────
# Blocco N5b · Casino Scacchi e Sportland (piano approvato dal committente il 14/10/2026)
#   Casino Scacchi («Vecchia Domus Storica (Casino Scacchi)» su Google, in Contrada Salsa): il rudere OSM w411138777 (due
#   piani senza tetto, foto di utenti su Google dell'aprile 2026) e la cappella con la vela w411137455 (in OSM anche lei
#   `building=ruins`). Tutti e due diventano «ruderi» (tipo 12): li disegna l'oggetto Scacchi del diorama. Nessuna strada.
#   Sportland, di fronte al Casino di Meninni: centro sportivo OSM w1158532121 coi campi, la pizzeria nell'edificio grande
#   w411139162 e le tettoie. Overture dava palazzi di 14–17 m: piani da Street View (ottobre 2025) e satellite. Niente
#   scritte né insegne (decisione del committente): i campi, le reti e le torri faro li disegna l'oggetto Sportland.
# ─────────────────────────────────────────────────────────────────────────────
SCACCHI = ('Casino Scacchi', 411138777, 9.5)       # nome, sagoma OSM, altezza dei muri più alti (m)
SCACCHI_CAPPELLA = (411137455, 5.2)
# Sportland: (id OSM, tipo, altezza in m). Tipi della città: 0 casa, 3 tettoia, 6 capannone.
SPORTLAND_EDIFICI = {
    411139162: (0, 7.0),      # la pizzeria: due piani col tetto piano (Street View dalla SP201)
    411139646: (3, 3.4),      # corpo lungo e basso lungo il lato ovest, tetti grigi
    411148081: (0, 3.6),      # casetta a un piano a nord
    411140007: (0, 3.4),      # corpo basso a sud della pizzeria
    411142991: (3, 3.0),
    411145026: (6, 7.5),      # palestra coperta (building=sport, covered=yes): tetto bianco
}
SPORTLAND_OSM = 1158532121
SPORTLAND_OVERPASS = '[out:json][timeout:60];(way(1158532121);way(1158532124);way(1158532125);way(1158532126);way(1158532127););out tags geom;'


def casino_scacchi(city):
    """Blocco N5b: il Casino Scacchi e la cappella diventano ruderi (tipo 12); restituisce GEO.scacchi coi due anelli."""
    out = {}
    for b in city:
        if b.get('osm') == SCACCHI[1]:
            b.update(name=SCACCHI[0], kind=CITY_KIND['rudere'], height=SCACCHI[2])
            out['casino'] = flat(b['poly'].exterior.coords[:-1])
        elif b.get('osm') == SCACCHI_CAPPELLA[0]:
            b.update(name=None, kind=CITY_KIND['rudere'], height=SCACCHI_CAPPELLA[1])
            out['cappella'] = flat(b['poly'].exterior.coords[:-1])
    print(f'  Casino Scacchi: ' + ', '.join(out) + (' trovati' if len(out) == 2 else ' (manca qualcosa)'))
    return out


def sportland(city):
    """Blocco N5b: piani veri degli edifici di Sportland; restituisce GEO.sportland (recinto e campi da OSM)."""
    n = 0
    for b in city:
        if b.get('osm') in SPORTLAND_EDIFICI:
            b['kind'], b['height'] = SPORTLAND_EDIFICI[b['osm']]
            n += 1
    els = overpass_cached('sportland', SPORTLAND_OVERPASS)
    ring = lambda el: flat([to_local(g['lon'], g['lat']) for g in el['geometry']][:-1])
    out = {'recinto': [], 'campi': []}
    for el in els:
        if el.get('type') != 'way' or not el.get('geometry'):
            continue
        t = el.get('tags') or {}
        if el['id'] == SPORTLAND_OSM:
            out['recinto'] = ring(el)
        elif t.get('leisure') == 'pitch':
            out['campi'].append([{'soccer': 1, 'tennis': 2}.get(t.get('sport'), 0)] + ring(el))
    print(f'  Sportland: {n} edifici coi piani veri, {len(out["campi"])} campi')
    return out

# ─────────────────────────────────────────────────────────────────────────────
# Blocco N4b · villette del Liceo Tarantino (piano approvato dal committente il 14/10/2026: «tutto il triangolo formato
#   da Via Quasimodo, Via Montale e Via Carlo Betocchi»). Gli edifici col centro nel triangolo diventano «villette»
#   (CITY_KIND['villetta']): schiere di villette e palazzine di 3–5 livelli (Street View, maggio e ottobre 2025), divise
#   dal diorama in unità larghe `unita` metri lungo il lato lungo, coi tetti in coppi dove il satellite li mostra
#   (Google, visto il 14/10/2026: solo come riferimento visivo) e gli altri piani col parapetto. Le tettoie restano tettoie.
#   I piani stanno nella tabella LIVELLI (righe della città); qui le unità diverse e i tetti.
#   Vertici del triangolo sulle vie OSM: Via Eugenio Montale w107709045, Via Salvatore Quasimodo w1384775301, Via Carlo
#   Bertocchi w1384781475 (il poeta è Carlo Betocchi: in OSM il nome ha un refuso, nel diorama resta quello di OSM).
# ─────────────────────────────────────────────────────────────────────────────
VILLETTE_TRI = [(554.2, -346.8), (674.0, -348.9), (741.2, -351.0), (749.7, -352.8), (756.3, -355.3), (787.7, -385.4), (794.5, -392.0),
                (804.4, -403.5), (805.5, -407.6), (804.4, -410.6), (801.9, -413.4), (736.9, -457.8), (708.8, -477.0), (659.2, -509.7),
                (638.6, -484.1), (619.0, -459.9), (598.1, -434.0), (576.7, -405.4), (565.4, -390.3), (539.8, -356.1)]
VILLETTA_PIANO, VILLETTA_PARAPETTO = 3.0, 1.0      # m per piano e parapetto delle terrazze (altezza = piani × 3 + 1)
# Unità e tetti: (id OSM, punto nella sagoma, larghezza delle unità in m, [(est, nord, piani o None, tetto), …], fonte).
# Il punto sceglie l'unità che lo contiene; `piani` (se c'è) vale per quell'unità invece della riga di LIVELLI;
# tetto: 'coppi' (a falde col colmo di traverso), 'pannelli' (terrazza coi pannelli solari), 'attico' (corpo arretrato).
VILLETTE = [
    (411141192, (632.3, -366.0), 8.0, [(662, -369, None, 'pannelli')],
     'Via Eugenio Montale e Via A. Palazzeschi: nove villette a schiera larghe 8–9 m, terrazze piane, pannelli sull\'ultima a est'),
    (411149110, (646.3, -434.1), 6.0, [(627, -435, 4, None), (633, -434, None, 'coppi'), (639, -434, None, 'coppi'),
                                       (645, -434, None, 'coppi'), (650, -434, None, 'coppi'), (656, -434, None, 'coppi'),
                                       (665, -440, 4, None)],
     'Piazza Domenico Digiesi e Piazza Concordia: villette coi tetti in coppi rossi, palazzine di 4 livelli ai capi'),
    (411149180, (731.5, -373.1), 8.0, [(721, -367, None, 'coppi'), (730, -368, None, 'coppi'), (752, -375, 4, None)],
     'Via Eugenio Montale e Piazza della Solidarietà: due villette coi coppi a ovest, palazzina di 4 livelli a est'),
    (411148086, (691.4, -367.1), 12.0, [(691.4, -367.1, None, 'coppi')], 'Via Eugenio Montale: tetto a padiglione in coppi'),
    (411142683, (665.0, -484.0), 8.0, [(657, -484, None, 'coppi'), (664, -480, None, 'coppi')],
     'Via Salvatore Quasimodo e Via Cesare Pavese: coppi nella parte centrale, terrazze ai capi'),
    (411142787, (772.5, -410.8), 9.0, [(754, -420, None, 'coppi')], 'Via C. Rebora: coppi sul capo sud-ovest'),
    (411148126, (604.2, -405.4), 9.0, [(610, -400, None, 'pannelli'), (603, -409, None, 'pannelli')],
     'Via Vincenzo Cardarelli: terrazze coi pannelli solari'),
    (411144730, (668.2, -447.4), 10.0, [(668, -450, None, 'pannelli'), (668.2, -447.4, None, 'attico')],
     'Via Giuseppe Ungaretti: attico arretrato e pannelli solari'),
]
VILLETTE_PIAZZE = (831718825, 831718823, 831718822, 831718824)   # Piazza Concordia, della Solidarietà, Domenico Digiesi, Cooperazione
VILLETTE_OVERPASS = '[out:json][timeout:60];way(id:831718825,831718823,831718822,831718824);out tags geom;'


def villette(city):
    """Blocco N4b: gli edifici col centro nel triangolo delle villette diventano villette (le tettoie no)."""
    tri, n = Polygon(VILLETTE_TRI), 0
    for b in city:
        if b['kind'] in (CITY_KIND['house'], CITY_KIND['apartments']) and not b['name'] and tri.contains(b['poly'].centroid):
            b['kind'] = CITY_KIND['villetta']
            n += 1
    print(f'  villette del triangolo Via Montale – Via Quasimodo – Via Bertocchi: {n} edifici')


def villette_dati(city):
    """GEO.villette: unità e tetti delle villette (indice in GEO.city) e le quattro piazzette OSM del triangolo."""
    case = []
    for osm, pt, unita, unita_diverse, fonte in VILLETTE:
        p = Point(pt)
        k = next((i for i, b in enumerate(city) if b['poly'].contains(p)), None)
        if k is None or city[k].get('osm') != osm or city[k]['kind'] != CITY_KIND['villetta']:
            sys.exit(f'VILLETTE: in {pt} non c\'è la villetta w{osm} [{fonte}]')
        righe = []
        for e, nn, piani, tetto in unita_diverse:
            if not city[k]['poly'].contains(Point(e, nn)):
                sys.exit(f'VILLETTE: il punto ({e}, {nn}) è fuori dalla sagoma w{osm} [{fonte}]')
            code = {None: 0, 'coppi': 1, 'pannelli': 2, 'attico': 4}[tetto]
            righe.append([e, nn, round(piani * VILLETTA_PIANO + VILLETTA_PARAPETTO, 1) if piani else 0, code])
        case.append([k, unita, righe])
    els = overpass_cached('villette', VILLETTE_OVERPASS)
    piazze = [flat([to_local(g['lon'], g['lat']) for g in el['geometry']][:-1]) for el in els
              if el.get('type') == 'way' and el['id'] in VILLETTE_PIAZZE and el.get('geometry')]
    print(f'  villette: {len(case)} con le unità o i tetti dalla tabella, {len(piazze)} piazzette')
    return {'case': case, 'piazze': piazze}

# Blocco N3: chiese la cui navata vera in OSM è l'area del luogo di culto (senza `building`) accanto alla sagoma
# dell'edificio. San Nicola: la sagoma w411139790 è solo la parte a nord; la navata è l'area w385174930 («Chiesa San
# Nicola»), e la facciata del 1704 guarda la piazzetta in fondo a Via Cassese (Street View, ottobre 2025). Senza
# l'unione nel diorama c'era un corridoio vuoto al posto della navata.
CHIESE_AREE = {411139790: 385174930}
# Blocco N3: chiese OSM (amenity=place_of_worship, building=yes) che Overture dà come case: l'Addolorata in Via Borgo
# (Google la chiama «Chiesa dell'Annunziata»; facciata nelle foto di utenti su Google Maps, 2018 e 2022)
CHIESE_OSM = {411138843}
CHIESE_AREE_OVERPASS = '[out:json][timeout:60];(way(385174930););out tags geom;'


def chiese_aree(buildings):
    """Unisce alle sagome delle chiese l'area OSM del luogo di culto che ne è la navata (CHIESE_AREE)."""
    aree = {el['id']: Polygon([to_local(g['lon'], g['lat']) for g in el['geometry']]).buffer(0)
            for el in overpass_cached('chiese_aree', CHIESE_AREE_OVERPASS) if el.get('type') == 'way' and el.get('geometry')}
    for b in buildings:
        area = aree.get(CHIESE_AREE.get(b.get('osm')))
        if area is None:
            continue
        u = b['poly'].union(area.buffer(0.05)).buffer(-0.05)
        if u.geom_type == 'Polygon':
            b['poly'] = u.simplify(0.3, preserve_topology=True)
            print(f"  chiesa w{b['osm']} unita all'area del luogo di culto: {b['poly'].area:.0f} m²")
    return buildings


def taglio_torri_4_8a(buildings):
    """Blocco 4.8a · Separazione delle due torri isolate da 8 piani (Corso Aldo Moro 8 e Via Matteotti 18)
    e della Scuola primaria Santomasi (Corso Aldo Moro 6) dai rispettivi isolati monolitici OSM/Overture.
    Elimina la finta chiesa w411148157 unendola alla torre di Corso Aldo Moro."""
    # 1. Corso Aldo Moro: isolato w/r6148683 (civici 6–14) + finta chiesa w411148157
    b_rel = next((b for b in buildings if b['poly'].area > 4000 and 350 < b['poly'].centroid.x < 380), None)
    b_ch = next((b for b in buildings if b.get('osm') == 411148157), None)
    if b_rel and b_ch:
        buildings = [b for b in buildings if b is not b_rel and b is not b_ch]
        isolato = b_rel['poly'].union(b_ch['poly'])
        # Taglio della torre (civico 8): ricalca i vertici fino al passaggio cortilizio
        cut_torre = Polygon([
            (300, 355),
            (375.1, 355),
            (375.1, 391.35),
            (371.67, 392.82),
            (352.91, 396.59),
            (300, 396.59),
        ])
        box_scuola = box(300, 300, 420, 355)
        p_scuola = isolato.intersection(box_scuola)
        p_torre = isolato.intersection(cut_torre)
        p_nord = isolato.difference(box_scuola).difference(cut_torre)
        buildings.append({'poly': p_scuola, 'kind': KIND['public'], 'cls': 'school', 'name': 'Scuola primaria Santomasi', 'height': None, 'level': 0, 'osm': None})
        buildings.append({'poly': p_torre, 'kind': KIND['apartments'], 'cls': 'apartments', 'name': None, 'height': None, 'level': 0, 'osm': None})
        buildings.append({'poly': p_nord, 'kind': KIND['apartments'], 'cls': 'apartments', 'name': None, 'height': None, 'level': 0, 'osm': None})
        print(f'  blocco 4.8a: isolato Corso Aldo Moro tagliato in 3 edifici (scuola {p_scuola.area:.0f} m², torre {p_torre.area:.0f} m², cortina nord {p_nord.area:.0f} m²)')

    # 2. Via Matteotti: isolato r6148644 (civici 14–18)
    p_mat_pt = Point(241.4, -7.2)
    b_mat = next((b for b in buildings if b['poly'].contains(p_mat_pt)), None)
    if b_mat:
        buildings = [b for b in buildings if b is not b_mat]
        box_torre_mat = box(200, -30, 252, 20)
        p_torre_mat = b_mat['poly'].intersection(box_torre_mat)
        p_est_mat = b_mat['poly'].difference(box_torre_mat)
        buildings.append({'poly': p_torre_mat, 'kind': KIND['apartments'], 'cls': 'apartments', 'name': None, 'height': None, 'level': 0, 'osm': None})
        buildings.append({'poly': p_est_mat, 'kind': KIND['apartments'], 'cls': 'apartments', 'name': None, 'height': None, 'level': 0, 'osm': None})
        print(f'  blocco 4.8a: isolato Via Matteotti tagliato in 2 edifici (torre {p_torre_mat.area:.0f} m², palazzina est {p_est_mat.area:.0f} m²)')

    return buildings


CASE_ROSA = 'Case rosa'
# Tra Via Guardialto (SP201) e Via Guardialto Piccolo, dove si separano (indicazione del committente)
CASE_ROSA_ZONE = [(1142, -177), (1301, -295), (1470, -500), (1360, -250), (1323, -193), (1146, -155)]


# Edifici OSM delle zone a scala reale del bosco: nome, tipo (9 = tetto a capanna in coppi) e altezza.
BOSCO_EDIFICI = {411141350: ('Area Quercus', 9, 4.6),           # ristorante (amenity=restaurant n11092432410), tetto rosso
                 411142982: ('Vivaio forestale', 9, 4.8),       # edificio lungo col tetto di coppi (satellite)
                 411148672: ('Base Scout Gravina 1', 9, 3.8)}


def bosco_buildings(elements):
    """Edifici OSM attorno all'area Quercus e al vivaio, portati nel diorama (zone a scala reale)."""
    anchors = bosco_chain()[3]
    out = []
    for el in elements:
        t = el.get('tags') or {}
        if el.get('type') != 'way' or 'building' not in t or not el.get('geometry'):
            continue
        real = [to_local(g['lon'], g['lat']) for g in el['geometry']]
        c = Polygon(real).centroid
        if not (inside((c.x, c.y), ZONA_Q) or inside((c.x, c.y), ZONA_V)):
            continue
        poly = Polygon([bosco_map(q, anchors, (c.x, c.y)) for q in real]).buffer(0).simplify(0.3)
        name, kind, h = BOSCO_EDIFICI.get(el['id'], (None, KIND['shed'] if t['building'] in ('shed', 'roof') else KIND['house'], 3.4))
        out.append({'poly': poly, 'kind': kind, 'cls': t['building'], 'name': name, 'height': h, 'level': 0})
    print(f'  bosco: {len(out)} edifici OSM attorno all\'area Quercus e al vivaio')
    return out


def bosco_features(elements):
    """Campi, tribuna, parcheggio, vasche (OSM) e punti senza dati (BOSCO_PUNTI), in metri del diorama: GEO.bosco."""
    anchors = bosco_chain()[3]
    m = lambda q: bosco_map(q, anchors)
    geo = {el['id']: [to_local(g['lon'], g['lat']) for g in el['geometry']] for el in elements if el.get('type') == 'way' and el.get('geometry')}

    def ring(wid):
        c = Polygon(geo[wid]).centroid.coords[0]
        return flat([bosco_map(q, anchors, c) for q in geo[wid][:-1]])
    inner = shapely.union_all([box(z[0], z[2], z[1], z[3]) for z in BOSCHI]).buffer(-6, join_style='mitre')
    fits = lambda f: inner.contains(Polygon(list(zip(f[::2], f[1::2]))))
    # tre campi: in OSM tutti «tennis»; secondo GravinaLife (2021) due da calcetto e uno da tennis,
    # e dal satellite quello da tennis (verde, con le righe) è il centrale, w1195121475.
    out = {'campi': [[0 if w == 1195121475 else 1, ring(w)] for w in (1195121473, 1195121475, 1195121476)],
           'tribuna': ring(1195121474), 'parcheggio': ring(477738793), 'vasche': [f for f in (ring(w) for w in (411138854, 411138897, 411139081)) if fits(f)]}
    # Il parcheggio «Terra Rossa» è 700 m più giù lungo la strada: col tracciato compresso finirebbe sui
    # campi. Resta a lato della strada, ritagliato fuori dall'area dei campi. (Blocco M1: il maneggio
    # non c'è, lo ha detto il committente il 01/10/2026; il parcheggio resta com'era.)
    busy = MultiPoint([p for _, f in out['campi'] for p in zip(f[::2], f[1::2])]).convex_hull.buffer(8).union(Point(*m(MANEGGIO_EX)).buffer(32))
    park = Polygon(list(zip(out['parcheggio'][::2], out['parcheggio'][1::2]))).buffer(0).difference(busy)
    park = max(getattr(park, 'geoms', [park]), key=lambda g: g.area)
    out['parcheggio'] = flat(park.simplify(0.5).exterior.coords[:-1])
    out['picnic'] = [round(v, 1) for v in m(BOSCO_PUNTI['picnic'])]
    e, n, ang = BOSCO_PUNTI['scritta']
    out['scritta'] = [*map(lambda v: round(v, 1), m((e, n))), ang]
    out['aiuole'] = [round(v, 1) for v in m(BOSCO_PUNTI['aiuole'])]
    out['quercus'] = [round(v, 1) for v in m((-780, -5657))]    # parco «Rifugio Bosco Difesa Grande» (OSM w477739267)
    return out


def bosco_cover(grid, E, N, elements):
    """
    Uso del suolo nelle zolle del bosco: querce dove il punto reale corrispondente sta nel poligono OSM
    del Bosco Difesa Grande (w330074271) o del Bosco di Gravina (w330074290), campi altrove; alberi
    bruciati dove li mostra il satellite; radure attorno all'area Quercus e al vivaio; lungo i sentieri
    «fitto» (niente alberi dei riquadri: lì c'è il bosco istanziato del diorama).
    """
    a, b, c, anchors = bosco_chain()
    woods = [Polygon([to_local(g['lon'], g['lat']) for g in el['geometry']]).buffer(0)
             for el in elements if el.get('type') == 'way' and el['id'] in (330074271, 330074290)]
    wood = shapely.union_all(woods) if woods else None
    route_d, route_r = [], []
    o = BOSCO_ROUTE[0]
    for q in BOSCO_ROUTE[:QUERCUS_A + 1]:                     # provinciale e strada compressa: vertici reali e nel diorama
        route_r.append(q); route_d.append((o[0] + (q[0] - o[0]) * BOSCO_SCALA, o[1] + (q[1] - o[1]) * BOSCO_SCALA))
    for q in VIVAIO_ROUTE[:VIVAIO_REAL + 1]:
        route_r.append(q); route_d.append(bosco_map(q, anchors) if inside(q, ZONA_Q) else
                                          (anchors['J'][0] + (q[0] - BOSCO_J[0]) * BOSCO_SCALA, anchors['J'][1] + (q[1] - BOSCO_J[1]) * BOSCO_SCALA))
    route_d = np.array(route_d)
    anc = {'Q': anchors['Q'], 'V': anchors['V']}
    feats = bosco_features(elements)
    clear_q = MultiPoint([tuple(p) for f in [feats['tribuna'], *[r for _, r in feats['campi']]] for p in zip(f[::2], f[1::2])]).convex_hull.buffer(14)
    clear_q = clear_q.union(Point(*feats['quercus']).buffer(24))
    park = Polygon(list(zip(feats['parcheggio'][::2], feats['parcheggio'][1::2])))
    # blocco M2: niente alberi nelle vasche del vivaio (e un poco attorno)
    clear_q = clear_q.union(shapely.union_all([Polygon(list(zip(f[::2], f[1::2]))).buffer(6) for f in feats['vasche']]))
    clear_v = Point(*feats['picnic']).buffer(40).union(Point(*feats['scritta'][:2]).buffer(24))   # area pic-nic: prato senza alberi dei riquadri
    paths_d = [LineString(e['poly']) for e in bosco_ways(elements, anchors, {}) + bosco_ways(
        elements, anchors, {}, VIVAIO_ANELLO, VIVAIO_ROUTE[-1], 'bosco:vivaio', None, 'v') if e['walk']]
    near_path = shapely.union_all([p.buffer(42) for p in paths_d]) if paths_d else None
    burned = [box(x0, y0, x1, y1) for x0, x1, y0, y1 in BOSCO_BRUCIATO]
    counts = collections.Counter()
    for j, n in enumerate(N):
        for i, e in enumerate(E):
            if not any(inside((e, n), z) for z in BOSCHI):
                continue
            r = bosco_real((e, n), anc, route_d, route_r)
            pt = Point(r)
            code = COVER['querce'] if wood is not None and wood.contains(pt) else COVER['campo']
            if code == COVER['querce'] and any(bx.contains(pt) for bx in burned):
                code = COVER['bruciato']
            d = Point(e, n)
            if code != COVER['campo'] and near_path is not None and near_path.contains(d):
                code = COVER['fitto']
            if clear_q.contains(d) or park.contains(d) or clear_v.contains(d):
                code = COVER['cava'] if park.contains(d) else COVER['sport']      # radure (prato) e parcheggio sterrato
            grid[j, i] = code
            counts[code] += 1
    inv = {v: k for k, v in COVER.items()}
    print('  bosco, uso del suolo:', ', '.join(f'{inv[k]} {v}' for k, v in counts.most_common()))


# ─────────────────────────────────────────────────────────────────────────────
# Blocco M1 · il versante di Botromagno
#   In OSM, a ovest del ciglio, ci sono le sagome building=ruins degli scavi: Overture le passa
#   senza classe e il diorama le faceva diventare case e torri. Diventano rovine (GEO.botromagno),
#   con l'area degli scavi (w484764621) e un suolo di roccia lungo il ciglio. Le rovine dal lato
#   della città (i rioni) restano case come prima. Gli edifici veri del versante (il resort
#   Madonna della Stella e i suoi corpi) restano a uno o due piani, con i coppi.
# ─────────────────────────────────────────────────────────────────────────────
ROVINE_OVERPASS = """[out:json][timeout:120];
(way["building"="ruins"](40.79,16.39,40.85,16.46);way(484764621););out tags geom;"""
SCAVI = 484764621                          # «Scavi archeologici di Botromagno» (historic=archaeological_site, Q111644781)
ROCCIA_N = (250, 720)                      # tratto del ciglio ovest col suolo di roccia: dalla Madonna della Stella agli scavi
ROCCIA_LARGA = 30                          # m oltre il ciglio


def west_side(river):
    """
    Il lato di Botromagno: tutto ciò che sta a ovest del torrente. Il piano diceva «a ovest del ciglio
    ovest», ma tre rovine OSM stanno nella scarpata sotto il ciglio, dal lato di Botromagno, e il
    diorama le faceva diventare torri sottili: vale tutta la sponda (scelta più fedele ai dati).
    """
    pts = list(river.coords)
    if pts[0][1] > pts[-1][1]:
        pts = pts[::-1]
    return Polygon(pts + [(BOUND[0] - 50, pts[-1][1] + 50), (BOUND[0] - 50, pts[0][1] - 50)]).buffer(0)


def botromagno(elements, river, west_rim, buildings):
    """Rovine sul lato di Botromagno (tolte da Overture), area degli scavi e fascia di roccia: GEO.botromagno."""
    side = west_side(river)
    ruins = []
    scavi = None
    for el in elements:
        if el.get('type') != 'way' or not el.get('geometry'):
            continue
        p = Polygon([to_local(g['lon'], g['lat']) for g in el['geometry']]).buffer(0)
        if el['id'] == SCAVI:
            scavi = p
        elif (el.get('tags') or {}).get('building') == 'ruins' and side.contains(p.centroid) and CITY_ZONE.contains(p.centroid):
            ruins.append(p.simplify(0.15))
    tree = STRtree(ruins)
    keep, gone = [], 0
    for b in buildings:
        hit = [ruins[i] for i in tree.query(b['poly'])]
        if any(b['poly'].intersection(r).area > 0.5 * min(b['poly'].area, r.area) for r in hit):
            gone += 1
            continue
        keep.append(b)
    rim = LineString(west_rim)
    part = [p for p in west_rim if ROCCIA_N[0] <= p[1] <= ROCCIA_N[1]]
    band = LineString(part).buffer(ROCCIA_LARGA, single_sided=True) if len(part) > 1 else Polygon()
    if band.intersection(side).area < 0.5 * band.area:     # il lato giusto è quello di Botromagno
        band = LineString(part).buffer(-ROCCIA_LARGA, single_sided=True)
    rock = band.union(scavi) if scavi is not None else band
    print(f'  Botromagno: {len(ruins)} rovine dal lato di Botromagno ({gone} edifici di Overture tolti), '
          f'area degli scavi {scavi.area if scavi is not None else 0:.0f} m², roccia {rock.area:.0f} m²')
    return keep, {'ruins': ruins, 'scavi': scavi, 'rock': rock, 'side': side, 'rim': rim}


def versante(old, bot):
    """Edifici del centro storico sul versante di Botromagno: un piano, muri chiari e coppi (KIND rurale)."""
    count = 0
    for b in old:
        c = b['poly'].centroid
        if not bot['side'].contains(c) or b['kind'] in (KIND['church'], KIND['cathedral']) or b['name']:
            continue
        b['kind'] = KIND['rurale']
        b['height'] = 4.6 if b['poly'].area > 300 else 3.9    # il resort è a un piano, coi soffitti alti (foto sferica su Google Maps)
        count += 1
    print(f'  versante di Botromagno: {count} edifici a un piano')


# ─────────────────────────────────────────────────────────────────────────────
# Blocco N2b · ruderi urbani e piani veri delle case del centro storico
#   Fino a N2b i `building=ruins` OSM sul lato della città restavano case di 1–5 piani, e i piani li decideva il
#   diorama a caso. Ora i ruderi sono un tipo a sé (KIND['rudere']: muri crollati, senza tetto; `height` è l'altezza
#   dei muri più alti rimasti in piedi) e i piani delle case vengono da una tabella con la fonte, rilevata su
#   Street View (solo come riferimento visivo: la sagoma resta quella di OSM e Overture). Dove non c'è una riga
#   resta la regola di Buildings.height in index.html.
# ─────────────────────────────────────────────────────────────────────────────
RUDERI_ALTEZZA = 4.5           # m: i muri più alti rimasti in piedi (due piani al massimo, come nella foto a 360° «Chiesa Rupestre di San Basilio», lug 2022)
RUDERI_BASSI = 0.6             # m: nel cono di vista dalla ringhiera della Cattedrale verso il ponte i ruderi sono bassi
VISTA_PONTE = ((-27.4, 19.0), (-24.0, 297.0), 12.0)   # belvedere OSM n3348673132, testata del ponte, mezzo angolo in gradi
FLOOR_H = 3.3                  # m per piano (CONFIG.buildings.floorHeight), più 0,6 m di parapetto: come reliable_height()


def ruderi(old, elements):
    """Gli edifici del centro storico che OSM segna `building=ruins` (id nel record_id di Overture) diventano ruderi."""
    ids = {el['id'] for el in elements if el.get('type') == 'way' and (el.get('tags') or {}).get('building') == 'ruins'}
    (e0, n0), (e1, n1), half = VISTA_PONTE
    az = math.atan2(e1 - e0, n1 - n0)
    cono = Polygon([(e0, n0)] + [(e0 + math.sin(az + s * math.radians(half)) * 160, n0 + math.cos(az + s * math.radians(half)) * 160) for s in (-1, 1)])
    count = low = 0
    for b in old:
        if b.get('osm') not in ids:
            continue
        b['kind'] = KIND['rudere']
        b['name'] = None
        bassi = cono.intersects(b['poly'])
        b['height'] = RUDERI_BASSI if bassi else RUDERI_ALTEZZA
        count += 1
        low += bassi
    print(f'  ruderi urbani: {count} (di cui {low} bassi nel cono di vista verso il ponte)')


# Piani verificati: (fonte, [(id OSM o None, est, nord, piani), ...]). Il punto (est, nord) sta dentro la sagoma
# dell'edificio (serve dove Overture non ha l'id OSM); l'id, se c'è, controlla che sia lo stesso edificio.
# Piani contati come livelli (piano terra compreso); un numero negativo vuol dire «almeno» (la cima della facciata
# esce dall'inquadratura). Le righe si aggiungono man mano che si guardano le vie.
LIVELLI = [
    # @@LIVELLI-INIZIO@@
    ('Street View, Via San Giovanni Evangelista 11 e 16, Via Donato Cristiani 8, Via Santa Sofia 19 e 45 (apr–ott 2025)', [
        (None, 74.5, 291.7, 3),
        (None, 86.4, 262.8, -3),
        (None, 69.7, 208.0, -3),
        (None, 33.8, 203.7, -3),
        (411142139, 44.4, 191.5, 3),
        (411147101, 57.8, 184.0, -3),
        (None, 116.4, 173.4, -3),
        (None, 143.0, 181.9, -3),
        (None, 174.4, 243.8, -3),
        (None, 142.4, 269.3, 3),
        (None, 154.5, 293.0, 2),
    ]),
    ('Street View, Via Michelangelo Calderoni 24–28 (ott 2025) e foto a 360° «Chiesa Rupestre di San Basilio» (lug 2022)', [
        (411149194, 34.8, 97.1, 3),
        (411139348, 28.4, 88.6, 2),
        (411139299, 40.1, 76.3, 2),
        (411146635, 45.4, 82.6, 1),
        (411139933, 60.2, 61.7, 3),
    ]),
    ('Street View, Via Michelangelo Calderoni 4–16 e 36 (ott 2025)', [
        (None, 68.3, 106.7, 4),
        (None, 19.5, 122.3, 3),
        (None, 108.3, 96.5, 3),
        (411139231, 91.7, 71.8, 3),
        (411139681, 128.7, 54.3, 3),
        (None, 167.6, 91.8, 4),
    ]),
    ("Street View, Via Civita 16, Piazza Benedetto XIII 13, Via Abbrazzo D'Ales 22 e 23, Via Matteotti 3 e 15 (mag–ott 2025; Via D'Ales 23: ago 2012)", [
        (411147393, 122.9, 45.0, -3),
        (411140001, 123.7, 30.5, -3),
        (385177560, 2.7, -38.1, 3),
        (385177548, 0.4, -29.8, -3),
        (385174937, -5.6, -23.3, -3),
        (385174945, 60.7, 4.0, 3),
        (385174946, 76.5, 1.9, 3),
        (385225790, 187.2, -27.0, -3),
        (385225787, 162.2, -20.8, -3),
        (385225788, 170.5, -20.6, -3),
        (385225786, 198.7, -3.6, 4),
        (385225782, 163.9, -3.6, -3),
        (385225781, 148.3, 25.3, -3),
        (None, 189.3, 85.5, -3),
    ]),
    ('Street View, Piazza Benedetto XIII 32, Via Guglielmo Marconi 21 (ott 2025)', [
        (None, 95.5, 5.8, 3),
        (385174942, 92.8, -26.6, -3),
        (385225807, 104.4, -84.0, -3),
    ]),
    ('Street View, Piazza Giuseppe Pellicciari 20 (ott 2025)', [
        (385177554, 80.1, -89.1, 4),
        (385225811, 103.4, -101.1, -3),
        (385177553, 84.9, -114.6, 3),
    ]),
    ("Street View, Viale Orsini 17, Via Angelo Raffaele Corrado 28 e 47, Via Nunzio Ingannamorte 14, Via Libertà 9, Via Pasquale Cassese 2, piazzetta all'incrocio con Via Matteotti (apr–ott 2025)", [
        (385225794, 162.2, -116.4, -3),
        (385225817, 145.3, -105.4, -3),
        (385225800, 175.6, -87.5, -3),
        (None, 150.4, -70.9, -3),
        (411140043, 244.0, -64.9, 3),
        (385177550, 271.3, -68.8, 3),
        (385225744, 223.2, -92.8, 2),
        (385225750, 299.7, -54.5, -4),
        (385402859, 292.6, 13.6, -3),
        (385225778, 240.0, 18.9, -4),
        (385402860, 285.6, 11.3, -4),
        (385402865, 274.9, 21.1, 3),
        (385402876, 202.4, 36.7, -3),
        (385402897, 192.6, 34.8, -3),
    ]),
    ('Street View, Via Nunzio Ingannamorte 3 e 14, Via Matteotti 18, Via Angelo Raffaele Corrado 3 e 25 (mag–ott 2025)', [
        (385225774, 181.4, -49.0, -3),
        (385225796, 199.4, -56.2, 3),
        (None, 236.9, -7.3, -4),
        (385177578, 230.5, -41.7, -3),
        (385177576, 213.9, -31.9, -3),
        (385402905, 203.5, -35.3, -4),
        (385225772, 194.9, -49.3, -3),
        (385225791, 185.6, -39.8, -3),
        (385402898, 193.6, 27.4, -3),
        (385402883, 205.5, 31.3, -3),
        (385402887, 205.2, 21.4, -3),
        (385402901, 196.0, 15.8, -3),
        (385225776, 218.9, 8.9, 3),
        (385225777, 223.8, 9.5, 3),
        (385225775, 214.3, 8.4, 3),
    ]),
    ('Street View, Via Fontana la Stella 31, Via Vittorio Veneto 18, Via Giacomo Lupi 24 (2008), Via San Nicola 16, Via Pasquale Cassese 6 (ott 2025)', [
        (385402870, 268.9, 32.1, 2),
        (385402881, 235.3, 31.0, -3),
        (385402869, 258.6, 33.5, -3),
        (385402864, 285.3, 37.7, -4),
        (385402853, 277.6, 49.4, -3),
        (None, 302.9, 87.1, -4),
        (411148511, 306.3, 119.3, 4),
        (None, 178.2, 167.7, -3),
        (411148009, 273.9, 201.7, -3),
        (None, 214.9, 317.2, -5),
    ]),
    ('Street View, Via Alcide De Gasperi 16 e 47, Corso Vittorio Emanuele 10 e 32, Corso Aldo Moro 8, Viale Orsini 69 (mag–ott 2025; blocco 4.6)', [
        (None, 371.8, -290.4, 3),          # angolo Via Firenze: palazzo dell'Ottocento a due piani alti (circa 10 m)
        (None, 388.6, -194.0, 3),          # palazzi col portale a due piani alti e tre
        (None, 266.2, -131.4, 6),          # palazzina bianca coi portici (OSM w411143607)
        (None, 366.8, -92.9, 3),           # la scuola: due piani alti sul seminterrato
        (None, 336.6, 342.4, 3),           # palazzo signorile a due piani alti, accanto alla casa rossa
        (None, 296.0, -65.0, 7),           # Viale Orsini 69, angolo Via Libertà: palazzina moderna di sette livelli
    ]),
    # @@LIVELLI-FINE@@
    # Blocco N4b: le villette del triangolo Via Montale – Via Quasimodo – Via Bertocchi (edifici della città). I livelli si
    # contano sul lato più alto della sagoma (in città il tetto sta a gMax + altezza, Tiles.placeBuildings): sul lato basso
    # si vede un livello in più, come nelle foto. Niente «almeno» per la città.
    ('Street View, Via Eugenio Montale 1–42 e «56 Via Tripoli» (ott 2025), Via A. Palazzeschi (mag 2025)', [
        (411141192, 632.3, -366.0, 3),     # nove villette a schiera: piano rialzato e due piani (quattro livelli su Via Palazzeschi)
        (411147880, 567.9, -370.2, 4),
        (411148086, 691.4, -367.1, 4),
        (411149180, 731.5, -373.1, 3),     # villette su Via Montale, quattro livelli su Piazza della Solidarietà
    ]),
    ('Street View, Piazza della Solidarietà e Via A. Palazzeschi 14–22 (mag 2025), Via Vincenzo Cardarelli 7 (mag 2025)', [
        (411146000, 765.6, -388.6, 3),
        (411148126, 604.2, -405.4, 4),
    ]),
    ('Street View, Via C. Rebora 12 (mag 2025), Via Salvatore Quasimodo 8–46 (ott 2025)', [
        (411142787, 772.5, -410.8, 3),     # quattro livelli su Via Quasimodo, più in basso
        (411148772, 739.0, -433.8, 3),
        (411142683, 665.0, -484.0, 4),
    ]),
    ('Street View, Via Giuseppe Ungaretti 1–6 e Via Gozzano 5–21 (mag e ott 2025), Via Umberto Saba 11 (mag 2025)', [
        (411149050, 714.2, -455.0, 4),
        (411148556, 692.5, -404.8, 4),
        (411144730, 668.2, -447.4, 4),
    ]),
    ('Street View, Piazza Domenico Digiesi 17, Piazza Concordia 13, Via Cesare Pavese 2, Via Vincenzo Cardarelli 18 (mag 2025)', [
        (411149110, 646.3, -434.1, 3),     # villette coi balconi verdi; ai capi palazzine di 4 livelli (VILLETTE)
        (411140288, 690.1, -466.6, 3),
        (411146069, 614.0, -442.1, 5),
        (411148728, 620.2, -434.2, 4),
    ]),
    # Blocco 4.6: isolati della città sulle vie principali (in OSM un isolato è spesso una sagoma sola): i livelli della
    # facciata sulla via, contati su Street View; dove l'isolato mescola case basse e palazzine conta la facciata più lunga.
    ('Street View, Via Tripoli 14–109 (ott 2025; blocco 4.6)', [
        (None, 358.2, -463.2, 4),
        (None, 398.7, -456.8, 5),          # Via Tripoli 3: palazzina gialla di cinque livelli
        (None, 581.0, -316.4, 4),          # Via Tripoli 56, angolo: palazzina bianca di quattro livelli
        (None, 648.4, -273.4, 5),          # Via Tripoli 83: palazzine moderne
        (None, 684.8, -248.4, 5),          # Via Tripoli 91
        (None, 427.1, -417.9, 3),          # case vecchie a tre livelli (dietro, una palazzina di cinque)
        (None, 458.0, -419.4, 3),          # Via Tripoli 29, angolo
        (None, 462.0, -393.4, 3),          # Via Tripoli 54: case in tufo di due e tre livelli
        (None, 509.9, -386.3, 4),          # Via Tripoli 33, angolo Via Trieste
        (None, 742.6, -208.7, 4),
        (None, 800.5, -170.8, 4),          # Via Tripoli 109
        (None, 828.0, -143.1, 3),          # Via Tripoli 80, angolo Via Tagliamento
        (None, 846.8, -151.5, 4),          # Via Tripoli 80, angolo opposto
    ]),
    ('Street View, Via Alcide De Gasperi 87–133 (ott 2025; blocco 4.6)', [
        (None, 267.1, -666.8, 2),          # Via De Gasperi 133: casa a due livelli
        (None, 302.3, -576.6, 3),          # Via De Gasperi 111: case in tufo a tre livelli
        (None, 311.0, -538.4, 3),
        (None, 333.3, -538.5, 4),
        (None, 335.1, -407.7, 3),          # Via De Gasperi 87: case in tufo a tre livelli
        (None, 346.9, -418.9, 2),          # di fronte: casa in tufo a due livelli
    ]),
    ('Street View e satellite, Corso Aldo Moro 1–14, Via Matteotti 14–18, Piazza Scacchi (ott 2025; blocco 4.8a)', [
        (None, 355.0, 375.0, 8),          # Corso Aldo Moro 8: torre residenziale di 8 livelli (taglio dell'isolato)
        (None, 345.0, 335.0, 2),          # Corso Aldo Moro 6: Scuola primaria Santomasi (2 livelli scolastici)
        (None, 380.0, 410.0, 4),          # Corso Aldo Moro 10–14: cortina residenziale a 4 livelli
        (None, 375.0, 290.0, 4),          # Corso Aldo Moro 2–4 e Via Giardini: palazzina a 4 livelli
        (None, 391.6, 453.5, 3),          # Corso Aldo Moro (Palazzo Gramegna-Spada / Teatro Vida): 3 livelli
        (None, 241.4, -7.2, 8),           # Via Matteotti 18: torre residenziale di 8 livelli (taglio dell'isolato)
        (None, 265.0, -7.0, 3),           # Via Matteotti 14–16: palazzina residenziale a 3 livelli
        (None, 414.2, 327.0, 3),          # Corso Aldo Moro 1–3 / Piazza Scacchi est: palazzina a 3 livelli
    ]),
]


def livelli(old, city):
    """Altezza delle case dai piani verificati (LIVELLI): 3,3 m per piano più 0,6 m di parapetto; per le villette della
    città (blocco N4b) 3 m per piano più il parapetto della terrazza."""
    every = old + city
    tree = STRtree([b['poly'] for b in every])
    done, in_city = collections.Counter(), {id(b) for b in city}
    for fonte, righe in LIVELLI:
        for osm, e, n, piani in righe:
            p = Point(e, n)
            hit = [i for i in tree.query(p) if every[i]['poly'].contains(p)]
            if not hit:
                sys.exit(f'LIVELLI: nessun edificio in ({e}, {n}) [{fonte}]')
            b = every[hit[0]]
            if osm and b.get('osm') != osm:
                sys.exit(f'LIVELLI: in ({e}, {n}) c\'è w{b.get("osm")} invece di w{osm} [{fonte}]')
            if id(b) in in_city:
                if b['kind'] not in (CITY_KIND['house'], CITY_KIND['apartments'], CITY_KIND['villetta']) or piani <= 0:
                    sys.exit(f'LIVELLI: in ({e}, {n}) l\'edificio della città non è una casa (tipo {b["kind"]}) o i piani sono «almeno» [{fonte}]')
                villa = b['kind'] == CITY_KIND['villetta']
                b['height'] = round(piani * (VILLETTA_PIANO if villa else FLOOR_H) + (VILLETTA_PARAPETTO if villa else 0.6), 1)
                done['città'] += 1
                continue
            if b['kind'] not in (KIND['house'], KIND['apartments'], KIND['public']):       # blocco 4.6/4.8a: anche condomini e scuole
                sys.exit(f'LIVELLI: in ({e}, {n}) l\'edificio non è una casa o scuola (tipo {b["kind"]}) [{fonte}]')
            # piani negativi = «almeno»: la cima non si vede in foto; l'altezza si codifica come 100 m + il minimo
            # e il diorama prende il più alto tra il minimo e la regola (Buildings.height)
            b['height'] = round(abs(piani) * FLOOR_H + 0.6, 1) + (100 if piani < 0 else 0)
            done['centro'] += 1
    print(f'  piani verificati: {done["centro"]} case di {len(old)} edifici del centro storico, {done["città"]} edifici della città')


# ─────────────────────────────────────────────────────────────────────────────
# Blocco M1 · stadio «Stefano Vicino» e Fiera di San Giorgio
#   Le tribune OSM (building=grandstand) diventavano palazzine con le finestre: restano come sagome
#   (tipo «tribuna», per la camera e gli alberi) ma il diorama disegna campo, gradinate, tribuna
#   coperta, torri faro e muro di cinta dalle sagome OSM (GEO.sport). I padiglioni della Fiera
#   diventano capannoni da fiera.
# ─────────────────────────────────────────────────────────────────────────────
STADIO_FIERA_OVERPASS = """[out:json][timeout:120];
(way(478401752);way(927885291);way(411149113);way(411146463);way(478401751);node(8763525337);
 way(411148871);way(411147010);way(411147074);way(411147873););out tags geom;"""
STADIO, CAMPO, TRIBUNA_EST, ANELLO, FIERA = 478401752, 927885291, 411149113, 411146463, 478401751
CANCELLO_FIERA = 8763525337
PADIGLIONI = (411148871, 411147010, 411147074, 411147873)   # il primo è il Padiglione Tobia Granieri


def stadio_fiera(elements, city):
    """Segna le tribune e i padiglioni della Fiera e prepara GEO.sport."""
    geo, gate = {}, None
    for el in elements:
        if el.get('type') == 'way' and el.get('geometry'):
            geo[el['id']] = Polygon([to_local(g['lon'], g['lat']) for g in el['geometry']]).buffer(0)
        elif el.get('type') == 'node' and el['id'] == CANCELLO_FIERA:
            gate = [round(v, 1) for v in to_local(el['lon'], el['lat'])]
    over = lambda b, p: b['poly'].intersection(p).area > 0.5 * min(b['poly'].area, p.area)
    stands = [geo[i] for i in (TRIBUNA_EST, ANELLO) if i in geo]
    gone, pav = 0, 0
    for b in city:
        if any(over(b, p) for p in stands):
            b['kind'], b['height'] = CITY_KIND['tribuna'], 6.0
            gone += 1
        elif any(i in geo and over(b, geo[i]) for i in PADIGLIONI):
            b['kind'], b['height'] = CITY_KIND['padiglione'], 8.5
            pav += 1
    ring = lambda i: flat(geo[i].exterior.coords[:-1]) if i in geo else []
    print(f'  stadio e Fiera: {gone} tribune (diventano gradinate), {pav} padiglioni')
    return city, {'stadio': ring(STADIO), 'campo': ring(CAMPO), 'tribuna': ring(TRIBUNA_EST), 'anello': ring(ANELLO),
                  'fiera': ring(FIERA), 'cancello': gate}


def name_places(old, city):
    """Dà nome e tipo agli edifici delle scuole, delle chiese senza nome, del Casino e delle case rosa."""
    every = old + city
    tree = STRtree([b['poly'] for b in every])

    def pick(pt):
        p = Point(pt)
        near = [every[i] for i in tree.query(p.buffer(6))]
        near = [b for b in near if b['poly'].distance(p) <= 6]
        return min(near, key=lambda b: (b['poly'].distance(p), -b['poly'].area), default=None)

    in_city = {id(b) for b in city}
    found = 0
    for name, pt, floors in SCHOOLS:
        b = pick(pt)
        if not b:
            print(f'  ATTENZIONE: edificio della scuola non trovato: {name}')
            continue
        b['name'] = name
        b['kind'] = CITY_KIND['school'] if id(b) in in_city else KIND['public']
        b['height'] = floors * 3.4 + 0.8                      # piani alti 3,4 m, più il parapetto
        found += 1
    for name, pt in CHURCHES:
        b = pick(pt)
        if b:
            b['name'], b['kind'] = name, CITY_KIND['church']
            b['height'] = 12.0
    for b in every:
        if b.get('osm') in CHIESE_OSM:
            b['kind'] = KIND['church']
    b = pick(MENINNI[1])
    if b:
        b['name'], b['kind'], b['height'] = MENINNI[0], CITY_KIND['rudere'], MENINNI_ALTO
    zone = Polygon(CASE_ROSA_ZONE)
    rosa = [b for b in city if b['kind'] != CITY_KIND['school'] and b['poly'].area > 300 and zone.contains(b['poly'].centroid) and not b['name']]
    for b in rosa:
        b['name'] = CASE_ROSA
    print(f'  scuole: {found} su {len(SCHOOLS)}; case rosa: {len(rosa)} edifici')


def castle_outline(elements):
    """Sagoma del Castello Svevo (OSM w76156899, rovine del 1231) in metri locali."""
    for el in elements:
        if el.get('type') == 'way' and el.get('id') == 76156899 and el.get('geometry'):
            p = Polygon([to_local(g['lon'], g['lat']) for g in el['geometry']])
            return p.simplify(0.5, preserve_topology=True) if p.is_valid else p.buffer(0)
    return None


POI_KIND = [('castle', 'castello'), ('railway', 'stazione'), ('place_of_worship', 'chiesa'), ('stadium', 'sport'),
            ('sports_centre', 'sport'), ('park', 'parco'), ('memorial', 'memoria'), ('monument', 'monumento'),
            ('archaeological_site', 'archeologia'), ('ruins', 'storico'), ('fort', 'storico'), ('building', 'storico')]


def city_pois(elements):
    """Luoghi con nome da OpenStreetMap (via Overpass) nella zolla: solo etichette possibili, niente schede."""
    out = []
    for el in elements:
        t = el.get('tags') or {}
        c = el.get('center') or ({'lat': el['lat'], 'lon': el['lon']} if 'lat' in el else None)
        if not t.get('name') or not c:
            continue
        # Blocco 4.7: in Via Santa Cecilia non c'è alcuna chiesa di Santa Cecilia
        if el.get('id') == 411148976 or t.get('name') == 'Chiesa di Santa Cecilia':
            continue
        e, n = to_local(c['lon'], c['lat'])
        if not CITY_ZONE.contains(Point(e, n)):
            continue
        vals = {t.get('historic'), t.get('amenity'), t.get('leisure'), 'railway' if t.get('railway') == 'station' else None}
        kind = next((k for key, k in POI_KIND if key in vals), None)
        if kind:
            out.append((round(e, 1), round(n, 1), t['name'], kind, f"{el['type'][0]}{el['id']}", t.get('wikidata')))
    print(f'  luoghi da OpenStreetMap: {len(out)}')
    return sorted(out, key=lambda x: (x[3], x[2]))


def build_rails(data):
    """Binari reali (FAL a scartamento ridotto, RFI a scartamento ordinario): linee da guardare, senza gallerie."""
    rails = []
    clip = box(AREA_ROADS[0], AREA_ROADS[2], AREA_ROADS[1], AREA_ROADS[3])
    for sg in data['segment']:
        if sg.get('subtype') != 'rail' or sg.get('class') not in ('narrow_gauge', 'standard_gauge'):
            continue
        pts = [to_local(*p) for p in sg['geom']['coordinates']]
        cuts, spans = [0.0, 1.0], {'is_bridge': [], 'is_tunnel': []}
        for fl in sg.get('rail_flags') or []:
            for v in fl.get('values', []):
                if v in spans:
                    between = fl.get('between') or [0, 1]
                    spans[v].append(between)
                    cuts += between
        cuts = sorted(set(cuts))
        for t0, t1 in zip(cuts, cuts[1:]):
            mid = (t0 + t1) / 2
            if t1 - t0 < 1e-6 or any(a <= mid <= b for a, b in spans['is_tunnel']):
                continue
            i0, p0 = point_at(pts, t0)
            i1, p1 = point_at(pts, t1)
            line = LineString([p0] + pts[i0 + 1:i1 + 1] + [p1]).intersection(clip)
            for g in getattr(line, 'geoms', [line]):
                if g.geom_type == 'LineString' and g.length > 3:
                    bridge = any(a <= mid <= b for a, b in spans['is_bridge'])
                    rails.append({'gauge': 0 if sg['class'] == 'narrow_gauge' else 1, 'bridge': bridge, 'line': g.simplify(0.5)})
    # Blocco M2: i ponti dei binari come in OSM (Overture a Via Spinazzola chiude il ponte RFI 18 m prima,
    # proprio sopra la via): i tratti dentro un ponte OSM diventano ponte.
    osm_bridges = [LineString([to_local(g['lon'], g['lat']) for g in el['geometry']]) for el in osm_m2()
                   if el.get('type') == 'way' and (el.get('tags') or {}).get('railway') and (el.get('tags') or {}).get('bridge')]
    if osm_bridges:
        zone = shapely.union_all([b.buffer(2.5, cap_style='flat') for b in osm_bridges])
        out = []
        for r in rails:
            if r['bridge'] or not r['line'].intersects(zone):
                out.append(r)
                continue
            for part, bridge in ((r['line'].intersection(zone), True), (r['line'].difference(zone), False)):
                part = shapely.line_merge(part) if part.geom_type == 'MultiLineString' else part
                for g in getattr(part, 'geoms', [part]):
                    if g.geom_type == 'LineString' and g.length > 3:
                        out.append({**r, 'bridge': bridge, 'line': g})
        rails = out
    print(f'  binari: {len(rails)} tratti, {sum(r["line"].length for r in rails) / 1000:.1f} km, '
          f'ponti {sum(r["line"].length for r in rails if r["bridge"]):.0f} m')
    return rails


def extend_rims(river, dem_light):
    """
    Cigli del canyon: quelli tracciati a mano nel centro, prolungati a nord e a sud lungo il
    torrente finché il DSM mostra una valle incisa (almeno 12 m sotto le sponde). Servono alle
    panoramiche e alla targa; il terreno fuori dal centro storico viene direttamente dal DSM.
    """
    pts = list(river.coords)
    L = river.length

    def rim_offsets(s):
        p, a, b = river.interpolate(s), river.interpolate(max(0, s - 15)), river.interpolate(min(L, s + 15))
        tx, ty = b.x - a.x, b.y - a.y
        l = math.hypot(tx, ty) or 1
        nx, ny = -ty / l, tx / l                      # sinistra del verso di percorrenza (nord → sud: est)
        out = []
        for sgn in (1, -1):
            offs = np.arange(0, 260, 5.0)
            h = dem_light(p.x + sgn * nx * offs, p.y + sgn * ny * offs)
            floor, bank = h[:5].min(), np.percentile(h[24:], 70)
            if bank - floor < 12:
                return None
            k = int(np.argmax(h >= floor + 0.8 * (bank - floor)))
            out.append((p.x + sgn * nx * offs[k], p.y + sgn * ny * offs[k]))
        return out

    east, west = list(EAST_RIM), list(WEST_RIM)
    # a nord (a monte) si parte dall'ultimo punto dei cigli a mano e si risale; a sud si scende
    for towards, rim_e, rim_w in (('nord', east, west), ('sud', east, west)):
        anchor = rim_e[-1] if towards == 'nord' else rim_e[0]
        s0 = river.project(Point(anchor))
        step = -30 if towards == 'nord' else 30         # il torrente va da nord a sud
        added_e, added_w = [], []
        s = s0 + step * 2
        while 0 < s < L:
            r = rim_offsets(s)
            if not r:
                break
            (ea, eb) = r
            added_e.append(ea)
            added_w.append(eb)
            s += step
        added_e, added_w = smooth_line(added_e), smooth_line(added_w)
        if towards == 'nord':
            east += added_e
            west += added_w
        else:
            east[:0] = added_e[::-1]
            west[:0] = added_w[::-1]
    # niente punti ripetuti (tratti lunghi zero): il diorama non saprebbe da che parte sta il canyon
    east = [p for i, p in enumerate(east) if i == 0 or math.dist(p, east[i - 1]) > 1e-6]
    west = [p for i, p in enumerate(west) if i == 0 or math.dist(p, west[i - 1]) > 1e-6]
    print(f'  cigli del canyon: {len(EAST_RIM)} → {len(east)} punti a est, {len(WEST_RIM)} → {len(west)} a ovest')
    return east, west


RIONI_N = (-240, 300, 15)   # m: tratto del ciglio est in cui si misura la discesa dei rioni, e passo
RIONI_SCALA = 0.45         # le quote a 30 m esagerano la discesa vicino al ciglio (il canyon sfocato), e il canyon del
                           # diorama resta quello disegnato a mano: se ne usa meno della metà


def rioni_profile(ground_at):
    """
    Discesa dei rioni verso la gravina, dalle quote Copernicus (blocco G). Lungo il ciglio est
    disegnato a mano, ogni 15 m, si confronta l'altopiano (220–300 m dentro l'abitato) con la quota
    a 45 m dal ciglio, più metà della pendenza che resta fino al ciglio: i 45 m più vicini sono
    sporcati dal canyon, che a 30 m di maglia e dopo lo smusso "sbava" dentro le case. `da` è la
    distanza dal ciglio a cui comincia la discesa. Il diorama la usa come guida in rioneDrop.
    """
    def rim_e(n):
        for (e0, n0), (e1, n1) in zip(EAST_RIM, EAST_RIM[1:]):
            if min(n0, n1) <= n <= max(n0, n1):
                return e0 + (n - n0) / ((n1 - n0) or 1) * (e1 - e0)
    S = np.arange(0, 301, 5)
    depth, width = [], []
    for n in range(RIONI_N[0], RIONI_N[1] + 1, RIONI_N[2]):
        e = rim_e(n)
        H = np.array([float(ground_at(e + s, n)) for s in S])
        plateau, h45, h80 = H[S >= 220].max(), H[S == 45][0], H[S == 80][0]
        d = plateau - h45 + (h80 - h45) / 35 * 45 * 0.5
        depth.append(round(max(0.0, d) * RIONI_SCALA, 1))
        width.append(int(S[np.argmax(H >= plateau - 0.1 * (plateau - h45))]))
    print(f'  discesa dei rioni (quote reali × {RIONI_SCALA}): da {min(depth):.0f} a {max(depth):.0f} m, a partire da {min(width)}–{max(width)} m dal ciglio')
    return {'n0': RIONI_N[0], 'passo': RIONI_N[2], 'd': depth, 'w': width}


CENTRO = (-590, 690, -600, 830)   # m: CONFIG.terrain.proc del diorama più la sfumatura (230 m, 220 a sud)
CENTRO_PASSO = 20                 # m: passo della griglia della guida in GEO.centro
CENTRO_LONTANO = 120              # m dal ciglio est: più vicino la cella da 30 m del DSM prende dentro il canyon
CENTRO_NOTO = 150                 # m dal ciglio est: da qui la guida è nota, più vicino si prolunga piatta


def _masked_blur(a, known, sigma):
    """Sfocatura gaussiana dei soli valori noti (sigma in celle): media pesata, i buchi non contano."""
    w = known & np.isfinite(a)
    num, den = blur(np.where(w, a, 0.0), sigma), blur(w.astype(float), sigma)
    return num / np.maximum(den, 1e-9), den


def _masked_percentile(a, mask, half, q, least=8):
    """Percentile q su una finestra (2·half+1)² dei soli pixel della maschera; NaN dove ce ne sono meno di `least`."""
    from numpy.lib.stride_tricks import sliding_window_view
    size = 2 * half + 1
    A = sliding_window_view(np.pad(np.where(mask, a, np.nan), half, constant_values=np.nan), (size, size))
    cnt = np.isfinite(A).sum(axis=(2, 3))
    import warnings
    with warnings.catch_warnings(), np.errstate(all='ignore'):
        warnings.simplefilter('ignore', RuntimeWarning)               # finestre tutte vuote: diventano NaN
        out = np.nanpercentile(A.reshape(*A.shape[:2], -1), q, axis=2)
    return np.where(cnt >= least, out, np.nan)


def _rim_frame(rim, E, N):
    """Distanza con segno dal ciglio est (+ verso la città), punto del ciglio più vicino e normale verso la città."""
    P = np.asarray(rim, float)
    best = np.full(E.shape, np.inf)
    out = {k: np.zeros(E.shape) for k in ('re', 'rn', 'ue', 'un', 'cross')}
    for (e0, n0), (e1, n1) in zip(P, P[1:]):
        dx, dn = e1 - e0, n1 - n0
        L2 = dx * dx + dn * dn
        if L2 < 1e-9:
            continue
        t = np.clip(((E - e0) * dx + (N - n0) * dn) / L2, 0, 1)
        qe, qn = e0 + dx * t, n0 + dn * t
        d2 = (E - qe) ** 2 + (N - qn) ** 2
        k = d2 < best
        best[k] = d2[k]
        l = math.sqrt(L2)
        for key, v in (('re', qe), ('rn', qn), ('ue', np.full(E.shape, dn / l)), ('un', np.full(E.shape, -dx / l)),
                       ('cross', dx * (N - n0) - dn * (E - e0))):
            out[key][k] = v[k]
    # la normale (dn, −dx) del verso sud → nord guarda a est, cioè verso la città (cross < 0 oltre il ciglio)
    S = np.sqrt(best) * np.where(out['cross'] < 0, 1, -1)
    return S, out


def centro_guide(dem_at, east_rim):
    """
    Guida delle quote del centro storico (blocco N1): la quota vera del suolo dal DSM Copernicus grezzo,
    senza tetti, sulla zona del terreno disegnato a mano. Il diorama la usa per l'altopiano lato città;
    canyon, cigli, falesia, gradoni e discesa dei rioni restano disegnati a mano.
    - griglia a 10 m; percentile 20% su 90 m dei soli pixel a più di 120 m dal ciglio est (vicino al
      ciglio la cella da 30 m prende dentro il canyon: la Cattedrale verrebbe −14 m invece di −0,3);
    - sfocatura dei soli valori noti (35 m), noti solo oltre 150 m dal ciglio;
    - verso il ciglio (e oltre) la guida si prolunga piatta lungo la normale al ciglio;
    - smusso finale (20 m), griglia di GEO a 20 m con quote a 0,1 m;
    - `tr`: la guida sul ciglio est ogni 10 m di nord (il ciglio est è una funzione del nord).
    """
    st = 10
    E = np.arange(CENTRO[0], CENTRO[1] + 1, st, dtype=float)
    N = np.arange(CENTRO[2], CENTRO[3] + 1, st, dtype=float)
    EE, NN = np.meshgrid(E, N)
    Z = dem_at(EE, NN) - ALT0
    S, R = _rim_frame(east_rim, EE, NN)
    P = _masked_percentile(Z, S > CENTRO_LONTANO, 4, 20)
    B, _ = _masked_blur(P, np.isfinite(P) & (S > CENTRO_NOTO), 3.5)
    known = (S > CENTRO_NOTO) & np.isfinite(P)
    # prolungamento piatto: il valore a 160 m dal ciglio, lungo la normale verso la città
    reach = CENTRO_NOTO + 10
    te, tn = R['re'] + R['ue'] * reach, R['rn'] + R['un'] * reach
    x, y = np.clip((te - E[0]) / st, 0, len(E) - 1.001), np.clip((tn - N[0]) / st, 0, len(N) - 1.001)
    i, j = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - i, y - j
    Bk = np.where(known, B, np.nan)
    ext = (Bk[j, i] * (1 - fx) * (1 - fy) + Bk[j, i + 1] * fx * (1 - fy) + Bk[j + 1, i] * (1 - fx) * fy + Bk[j + 1, i + 1] * fx * fy)
    U = np.where(known, B, ext)
    # dove anche il punto lungo la normale non è noto (agli angoli), una media dei vicini noti
    F, _ = _masked_blur(U, np.isfinite(U), 5.0)
    U = np.where(np.isfinite(U), U, F)
    T = blur(U, 2.0)
    k = CENTRO_PASSO // st
    G = T[::k, ::k]
    q = np.round(G * 10).astype(int)
    dati = []
    for row in q:
        dati += [int(row[0])] + [int(v) for v in np.diff(row)]
    # guida sul ciglio est ogni 10 m di nord
    rim = np.asarray(east_rim, float)
    ns = np.arange(CENTRO[2], CENTRO[3] + 1, 10.0)
    tr = []
    for n in ns:
        kk = int(np.clip(np.searchsorted(rim[:, 1], n), 1, len(rim) - 1))
        (e0, n0), (e1, n1) = rim[kk - 1], rim[kk]
        f = float(np.clip((n - n0) / ((n1 - n0) or 1), 0, 1))
        e = e0 + f * (e1 - e0)
        xx, yy = np.clip((e - E[0]) / st, 0, len(E) - 1.001), np.clip((n - N[0]) / st, 0, len(N) - 1.001)
        ii, jj = int(xx), int(yy)
        ax, ay = xx - ii, yy - jj
        tr.append(round(float(T[jj, ii] * (1 - ax) * (1 - ay) + T[jj, ii + 1] * ax * (1 - ay) + T[jj + 1, ii] * (1 - ax) * ay + T[jj + 1, ii + 1] * ax * ay), 1))
    at = lambda e, n: float(T[int(round((n - N[0]) / st)), int(round((e - E[0]) / st))])
    print(f'  guida del centro storico: griglia {G.shape[1]} × {G.shape[0]} ogni {CENTRO_PASSO} m, da {G.min():.1f} a {G.max():.1f} m; '
          f'Cattedrale {at(10, 10):.1f}, Piazza della Repubblica {at(320, 0):.1f}, San Francesco {at(230, 220):.1f}')
    _, piazza = superfici()
    return {'e0': CENTRO[0], 'n0': CENTRO[2], 'passo': CENTRO_PASSO, 'nx': G.shape[1], 'ny': G.shape[0], 'q': 0.1,
            'dati': varint(dati), 'tr0': CENTRO[2], 'tr': tr,
            'piazza': flat(piazza.simplify(0.3).exterior.coords[:-1]) if piazza is not None else []}


def smooth_line(pts, k=2):
    """Media mobile su una polilinea (estremi compresi)."""
    return [tuple(np.mean(pts[max(0, i - k):i + k + 1], axis=0)) for i in range(len(pts))] if len(pts) > 2 else pts


# ─────────────────────────────────────────────────────────────────────────────
# 5. Scrittura del blocco dati in index.html
# ─────────────────────────────────────────────────────────────────────────────
CLASS_CODE = {'secondary': 0, 'tertiary': 1, 'residential': 2, 'unclassified': 2, 'living_street': 3,
              'pedestrian': 4, 'footway': 5, 'path': 5, 'steps': 5, 'track': 6, 'unknown': 2}


COPERNICUS = ('produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 '
              'provided under COPERNICUS by the European Union and ESA; all rights reserved')
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'


def flat(coords, digits=1):
    return [round(v, digits) for p in coords for v in p]


def varint(values):
    """
    Interi con segno → stringa compatta: ogni carattere porta 5 bit del valore (a zigzag)
    più un bit che dice se il numero continua. Decodificata da CODEC in index.html.
    """
    out = []
    for v in values:
        z = v * 2 if v >= 0 else -v * 2 - 1
        while True:
            c, z = z & 31, z >> 5
            out.append(ALPHABET[c | (32 if z else 0)])
            if not z:
                break
    return ''.join(out)


def ring_ints(coords, q):
    """Anello a passo q (m), dall'angolo sud-ovest della zolla: primo punto assoluto, poi differenze."""
    pts = [(round((x - BOUND[0]) / q), round((y - BOUND[2]) / q)) for x, y in coords]
    pts = [p for i, p in enumerate(pts) if p != pts[i - 1]] if len(pts) > 1 else pts
    out = [len(pts), *pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out += [x1 - x0, y1 - y0]
    return out


def dm_ints(flat_coords):
    """Linea piatta a 0,1 m → interi: numero di punti, primo punto in dm, poi differenze. Senza perdite."""
    q = [round(v * 10) for v in flat_coords]
    return [len(q) // 2, *q[:2], *(q[k] - q[k - 2] for k in range(2, len(q)))]


def encode(edges, deco, pos, buildings, city, arches, feats, extra):
    names, name_idx = [], {}

    def nid(s):
        if not s:
            return -1
        if s not in name_idx:
            name_idx[s] = len(names)
            names.append(s)
        return name_idx[s]

    node_ids = {}
    nodes = []
    for e in edges:
        for n in (e['a'], e['b']):
            if n not in node_ids:
                node_ids[n] = len(nodes)
                nodes.append(pos[n])

    def flags(e):
        surf = e.get('surf') or {}
        code = max(surf, key=surf.get) if surf else 0          # blocco N1: superficie OSM (bit 128, 256, 512)
        return ((1 if e['bridge'] else 0) | (2 if e['foot'] else 0) | (4 if e.get('turn') else 0)
                | (8 if e['cls'] in ('track', 'path') else 0) | (16 if e.get('urban') else 0) | (32 if e.get('walk') else 0)
                | (64 if e.get('tunnel') else 0) | (code << 7))
    # Vie, vie decorative ed edifici del centro storico in forma compatta (CODEC), a 0,1 m come prima:
    # index.html li riporta alle righe di sempre in DATA.unpack().
    E = []
    for e in edges:
        poly = list(e['poly'])
        poly[0], poly[-1] = pos[e['a']], pos[e['b']]        # estremi esattamente sui nodi
        E += [node_ids[e['a']], node_ids[e['b']], CLASS_CODE.get(e['cls'], 2), nid(e['name']), flags(e),
              round(e['width'] * 10), *dm_ints(flat(poly))]
    D = []
    for e in deco:
        D += [CLASS_CODE.get(e['cls'], 2), nid(e['name']), flags(e), round(e['width'] * 10), *dm_ints(flat(e['poly']))]
    B = []
    for b in buildings:
        rings = [flat(b['poly'].exterior.coords[:-1])] + [flat(r.coords[:-1]) for r in b['poly'].interiors]
        B += [b['kind'], nid(b['name']), round((b['height'] or 0) * 10), len(rings)]
        for r in rings:
            B += dm_ints(r)
    # Edifici della città moderna: tipo, nome, altezza in dm, anelli a passo di 0,25 m.
    C = []
    for b in city:
        rings = [b['poly'].exterior] + list(b['poly'].interiors)
        C += [b['kind'], nid(b['name']) + 1, round(b['height'] * 10), len(rings)]
        for r in rings:
            C += ring_ints(r.coords[:-1], 0.25)
    g = extra['ground']
    q = np.round((g - ALT0) / 0.25).astype(int)               # quote a passo di 0,25 m
    dem = []
    for row in q:
        dem += [int(row[0])] + [int(v) for v in np.diff(row)]
    cov, runs = extra['cover'].ravel(), []
    k = 0
    while k < len(cov):
        j = k
        while j < len(cov) and cov[j] == cov[k]:
            j += 1
        runs += [int(cov[k]), j - k]
        k = j
    geo = {
        'meta': {
            'fonte': f'Overture Maps Foundation {RELEASE.split("/")[-1]} · © OpenStreetMap contributors (ODbL)',
            'quote': COPERNICUS,
            'origine': list(ORIGIN), 'area': list(BOUND), 'zolle': [list(z) for z in ZOLLE], 'z0': list(Z0), 'riquadro': TILE, 'quota0': ALT0,
        },
        'names': names,
        'nodes': varint(dm_ints(flat(nodes))),
        'edges': varint(E),
        'deco': varint(D),
        'buildings': varint(B),
        'city': varint(C),
        'dem': {'passo': DEM_STEP, 'nx': g.shape[1], 'ny': g.shape[0], 'q': 0.25, 'dati': varint(dem)},
        'cover': {'passo': COVER_STEP, 'nx': extra['cover'].shape[1], 'ny': extra['cover'].shape[0], 'dati': varint(runs)},
        'arches': [[nid(a['name']), a['width'], flat(a['poly'].exterior.coords[:-1])] for a in arches],
        'river': flat(feats['river'].coords),
        'riverY': [round(float(y) - ALT0, 1) for y in extra['riverY']],
        'rails': [[r['gauge'], int(r['bridge']), flat(r['line'].coords, 0)] for r in extra['rails']],
        'cliffs': [flat(c.coords) for c in feats['cliffs']],
        'walls': [flat(w.coords) for w in feats['walls'] if w.geom_type == 'LineString'],
        'views': [[round(g.centroid.x, 1), round(g.centroid.y, 1), nid(n)] for g, n in feats['views']],
        'bridges': [flat(b.coords) for b in feats['bridges']],
        'areas': [[c, flat(g.exterior.coords[:-1])] for c, g in feats['areas']],
        'places': [[round(e, 1), round(n, 1), nid(nm), c] for e, n, nm, c in feats['places'] if nm],
        'pois': [[e, n, nid(nm), kind, osm, wd or ''] for e, n, nm, kind, osm, wd in extra['pois']],
        'steps': [[nid(nm), flat(g.coords)] for nm, g in feats['steps']],
        'rims': {'east': flat(extra['rims'][0]), 'west': flat(extra['rims'][1])},
        'rioni': extra['rioni'],
        'centro': extra['centro'],
        'bosco': extra['bosco'],
        'botromagno': extra['botromagno'],
        'sport': extra['sport'],
        'm2': extra['m2'],
        'meninni': extra['meninni'],
        'villette': extra['villette'],
        'capotenda': extra['capotenda'],
        'uliveti': extra['uliveti'],
        'scacchi': extra['scacchi'],
        'sportland': extra['sportland'],
    }
    lines = ['const GEO = {']
    for k, v in geo.items():
        if k in ('arches', 'places', 'pois', 'areas', 'cliffs', 'walls', 'views', 'bridges', 'steps', 'rails'):
            lines.append(f'  {k}: [')
            lines += [f'    {json.dumps(x, ensure_ascii=False, separators=(",", ":"))},' for x in v]
            lines.append('  ],')
        else:
            lines.append(f'  {k}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))},')
    lines.append('};')
    return '\n'.join(lines)


def write_html(block: str):
    html = HTML.read_text()
    a = html.index(MARK_START)
    b = html.index(MARK_END)
    head = html[:a] + MARK_START + ' generato da tools/genera_dati.py: non modificare a mano */\n'
    HTML.write_text(head + block + '\n' + html[b:])
    print(f'  index.html aggiornato ({len(block) / 1024:.0f} KB di dati)')


def preview(path, edges, deco, buildings, city, arches, feats, extra):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    W, H = BOUND[1] - BOUND[0], BOUND[3] - BOUND[2]
    fig, ax = plt.subplots(figsize=(W / 150, H / 150), dpi=90)
    tones = ['#f2ead8', '#e4dccb', '#b8d08a', '#7fa65a', '#eadca0', '#c9cf8f', '#d8d0d8', '#c8c0b0', '#9fd08a', '#efe2c8', '#c8c89a', '#c0b0a0', '#5f7f45']
    ax.imshow(extra['cover'], origin='lower', extent=(BOUND[0], BOUND[1], BOUND[2], BOUND[3]), cmap=ListedColormap(tones), vmin=0, vmax=12, interpolation='nearest')
    g = extra['ground']
    ax.contour(np.linspace(BOUND[0], BOUND[1], g.shape[1]), np.linspace(BOUND[2], BOUND[3], g.shape[0]), g, levels=np.arange(250, 460, 5), colors='#8a7a60', linewidths=0.3)
    for b in buildings + city:
        x, y = b['poly'].exterior.xy
        ax.fill(x, y, color='#b0452a' if b['kind'] in (1, 2, 7) else '#dccaa0' if b in buildings else '#c8b48a', lw=0)
    for e in deco:
        x, y = zip(*e['poly'])
        ax.plot(x, y, color='#9a9a9a', lw=e['width'] * 0.25, alpha=0.8)
    for e in edges:
        x, y = zip(*e['poly'])
        c = '#e8a23a' if e['bridge'] else '#6a8a3a' if e['cls'] == 'track' else '#8fb8a8' if e['foot'] or e.get('turn') else '#3a4a6a' if e.get('urban') else '#6a5a8a'
        ax.plot(x, y, color=c, lw=e['width'] * 0.25)
    for r in extra['rails']:
        ax.plot(*r['line'].xy, color='#222', lw=1.2, ls='--' if r['bridge'] else '-')
    for a in arches:
        x, y = a['poly'].exterior.xy
        ax.fill(x, y, color='#7a2ea0', lw=0)
    x, y = feats['river'].xy
    ax.plot(x, y, color='#2a7fd4', lw=2)
    for rim, c in ((extra['rims'][0], 'r'), (extra['rims'][1], 'm')):
        ax.plot(*zip(*rim), c + '--', lw=1)
    for z, st in ((Z0, 'k:'), *((z, 'k-') for z in ZOLLE)):
        ax.plot([z[0], z[1], z[1], z[0], z[0]], [z[2], z[2], z[3], z[3], z[2]], st, lw=1)
    for e, n, nm, kind, *_ in extra['pois']:
        ax.plot(e, n, 'k.', ms=3)
        ax.text(e + 6, n + 6, nm, fontsize=4)
    ax.set_xlim(BOUND[0], BOUND[1]); ax.set_ylim(BOUND[2], BOUND[3]); ax.set_aspect('equal')
    plt.tight_layout(); plt.savefig(path)
    print(f'  anteprima: {path}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--forza', action='store_true', help='riscarica i dati ignorando la cache')
    ap.add_argument('--anteprima', metavar='PNG', help='salva una mappa di controllo (richiede matplotlib)')
    args = ap.parse_args()
    t0 = time.time()
    print('1. Download (Overture Maps, OpenStreetMap via Overpass, Copernicus GLO-30)')
    data = {name: download(name, tt, args.forza) for name, tt in THEMES.items()}
    osm = overpass()
    dem_at = load_dem()
    print('2. Edifici')
    buildings = build_buildings(data['building'])
    castle = castle_outline(osm)
    if castle is not None:
        # la relazione OSM building=castle (r6148325) arriva da Overture come un edificio anonimo con la stessa sagoma
        buildings = [b for b in buildings if b['poly'].intersection(castle).area < 0.3 * b['poly'].area]
        buildings.append({'poly': castle, 'kind': CITY_KIND['castle'], 'cls': 'castle', 'name': 'Castello Svevo', 'height': 8.0, 'level': 0})
    buildings = chiese_aree(buildings)          # blocco N3: la navata di San Nicola
    # Blocco L: edifici reali attorno all'area Quercus e al vivaio (al posto della capanna generica)
    bosco_osm = overpass_bosco()
    buildings += bosco_buildings(bosco_osm)
    buildings = taglio_torri_4_8a(buildings)    # Blocco 4.8a: torri isolate e scuola di Corso Aldo Moro e Via Matteotti
    print('3. Rete stradale')
    edges, deco, pos = build_network(data, [b['poly'] for b in buildings], bosco_osm)
    buildings, arches = free_roads(edges + deco, pos, buildings)
    deco = deco_off_roads(edges, deco)
    print('4. Morfologia, quote reali, uso del suolo')
    feats = build_features(data)
    at, ground, light, _, _ = ground_model(dem_at, buildings)
    rims = extend_rims(feats['river'], at)
    rovine = overpass_cached('rovine', ROVINE_OVERPASS)
    buildings, bot = botromagno(rovine, feats['river'], rims[1], buildings)
    vigna = vigna_botromagno(data['segment'])
    filari = uliveti(data['segment'])
    cover = land_cover(data, buildings, bosco_osm, bot['rock'], vigna, filari)
    old = [b for b in buildings if inside(b['poly'].centroid.coords[0], Z0)]
    city = city_buildings([b for b in buildings if not inside(b['poly'].centroid.coords[0], Z0)], cover)
    print(f'  edifici: {len(old)} nel centro storico, {len(city)} nella città')
    versante(old, bot)
    ruderi(old, rovine)
    villette(city)                              # blocco N4b: prima dei piani, che per le villette sono da 3 m
    livelli(old, city)
    city, sport = stadio_fiera(overpass_cached('stadio_fiera', STADIO_FIERA_OVERPASS), city)
    name_places(old, city)
    meninni_ruderi(city)
    scacchi = casino_scacchi(city)
    sport_n5b = sportland(city)
    extra = {
        'ground': ground, 'cover': cover, 'rails': build_rails(data), 'pois': city_pois(osm),
        'riverY': river_bed(feats['river'], lambda e, n: at(e, n)), 'rims': rims,
        'rioni': rioni_profile(at), 'centro': centro_guide(dem_at, rims[0]), 'bosco': bosco_features(bosco_osm),
        'sport': sport, 'm2': luoghi_m2(osm_m2()),
        'meninni': {'muro': [flat(m) for m in MURO_MENINNI], 'cancello': list(CANCELLO_MENINNI)},
        'villette': villette_dati(city),
        'capotenda': {'vigna': flat(vigna.exterior.coords[:-1])},
        'uliveti': [[ang] + flat(p.exterior.coords[:-1]) for _, p, ang in filari],
        'scacchi': scacchi, 'sportland': sport_n5b,
        'botromagno': {'rovine': [flat(r.exterior.coords[:-1]) for r in bot['ruins']],
                       'scavi': flat(bot['scavi'].simplify(0.5).exterior.coords[:-1]) if bot['scavi'] is not None else []},
    }
    print('5. Scrittura')
    write_html(encode(edges, deco, pos, old, city, arches, feats, extra))
    print(f'  fatto in {time.time() - t0:.0f} s')
    if args.anteprima:
        preview(args.anteprima, edges, deco, old, city, arches, feats, extra)


if __name__ == '__main__':
    sys.exit(main())
