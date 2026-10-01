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
VIVAIO = (-600, 360, -2340, -1860)        # blocco L: strada fino al vivaio forestale (4 × 2 riquadri)
ZOLLE = (AREA, PIP, BOSCO, VIVAIO)
BOUND = (-840, 2760, -2340, 1980)         # rettangolo delle zolle: origine e griglie di GEO
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
KEEP_DEAD_ENDS = {'Piazza Benedetto XIII', 'Via Civita', 'Calata Grotte San Michele',
                  'Larghetto San Francesco', 'Via Matteotti'}
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


def build_edges(segments, connectors):
    """Spezza i segmenti Overture nei loro connettori → archi tra incroci reali."""
    conn_pos = {c['id']: to_local(*c['geom']['coordinates']) for c in connectors}
    edges = []
    for s in segments:
        cls, name = s.get('class'), (s.get('names') or {}).get('primary')
        if s.get('subtype') != 'road':
            continue
        pts = [to_local(*p) for p in s['geom']['coordinates']]
        on_bridge_route = name == BRIDGE_ROUTE_NAME and cls != 'steps'
        near_bridge_west = cls in ('footway', 'path') and any(
            BRIDGE_WEST_BOX[0] < p[0] < BRIDGE_WEST_BOX[1] and BRIDGE_WEST_BOX[2] < p[1] < BRIDGE_WEST_BOX[3] for p in pts)
        to_castle = cls in ('track', 'service') and all(inside(p, CASTLE_BOX) for p in pts)
        if to_castle:
            cls = 'track'
        # vie senza classe (per lo più traverse cieche dei quartieri nuovi): solo da guardare
        deco = cls == 'unknown'
        # marciapiedi, passaggi e scalinate del centro storico: si percorrono a piedi (blocco G)
        walk = cls in WALK and not on_bridge_route and not near_bridge_west and all(inside(p, Z0) for p in pts)
        if cls not in DRIVABLE and not on_bridge_route and not near_bridge_west and not to_castle and not deco and not walk:
            continue
        flags = s.get('road_flags') or []
        cuts = [(c['at'], c['connector_id']) for c in s.get('connectors', [])]
        spans = {'is_bridge': [], 'is_tunnel': []}
        for f in flags:
            for v in f.get('values', []):
                if v in spans:
                    between = f.get('between') or [0, 1]
                    spans[v].append(between)
                    cuts += [(between[0], f'{v}-a:{s["id"]}'), (between[1], f'{v}-b:{s["id"]}')]
        cuts = sorted(set(cuts))
        for (t0, c0), (t1, c1) in zip(cuts, cuts[1:]):
            if t1 - t0 < 1e-6:
                continue
            mid = (t0 + t1) / 2
            if any(a <= mid <= b for a, b in spans['is_tunnel']):
                continue                                   # le gallerie non si vedono: escluse
            i0, p0 = point_at(pts, t0)
            i1, p1 = point_at(pts, t1)
            poly = [p0] + pts[i0 + 1:i1 + 1] + [p1]
            edges.append({
                'a': c0, 'b': c1, 'poly': poly, 'cls': cls, 'name': name,
                'bridge': any(a <= mid <= b for a, b in spans['is_bridge']),
                'foot': cls not in DRIVABLE and not to_castle and not deco, 'deco': deco, 'walk': walk,
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


def add_turnarounds(core, extra, pos, buildings_tree, buildings, prune=True):
    """
    Aggiunge le vie cieche selezionate. A ogni foglia prova a inserire
    un'inversione a goccia che non tocchi gli edifici; se non c'è spazio,
    pota l'ultimo tratto e riprova sulla nuova foglia (con prune=False la lascia com'è).
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
            if leaf not in tried:
                tried.add(leaf)
                for r in (6.0, 5.0, 4.2):
                    for ang in (0, 25, -25, 50, -50, 75, -75):
                        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                        f = ((dx * c - dy * s) / dl, (dx * s + dy * c) / dl)
                        q, right, left = teardrop(pos[leaf], f, r)
                        shape_ = LineString(right + left[1:]).buffer(2.3)
                        if not area.contains(shape_):
                            continue
                        hit = any(buildings[i].buffer(-0.3).intersects(shape_) for i in buildings_tree.query(shape_))
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
                base = {'cls': e['cls'], 'name': e['name'], 'bridge': False, 'foot': e['foot'], 'turn': True}
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
                    or (e1['cls'] == 'track') != (e2['cls'] == 'track'):
                continue
            p1 = e1['poly'] if e1['b'] == n else e1['poly'][::-1]
            a1 = e1['a'] if e1['b'] == n else e1['b']
            p2 = e2['poly'] if e2['a'] == n else e2['poly'][::-1]
            b2 = e2['b'] if e2['a'] == n else e2['a']
            if a1 == b2:
                continue                                 # eviterebbe un anello su sé stesso
            merged = {**e1, 'a': a1, 'b': b2, 'poly': p1 + p2[1:],
                      'cls': e1['cls'] if length(p1) >= length(p2) else e2['cls']}
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
ZONA_V = (-3390, -2955, -7728, -7290)     # vivaio, Base Scout, area pic-nic, a scala reale
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


def bosco_ways(elements, anchors, pos):
    """Via di servizio e sentieri dell'area Quercus (OSM): tratti tra i nodi condivisi, a scala reale."""
    K = lambda g: (round(g['lon'], 7), round(g['lat'], 7))
    ways = {el['id']: el for el in elements if el.get('type') == 'way' and el['id'] in QUERCUS_SENTIERI | {QUERCUS_SERVIZIO}}
    count = collections.Counter(K(g) for w in ways.values() for g in w['geometry'])
    jkey = K(ways[QUERCUS_SERVIZIO]['geometry'][0])           # il primo punto della via di servizio è l'incrocio
    count[jkey] += 1
    names, out = {}, []
    base = {'bridge': False, 'deco': False, 'name': None}
    for wid, w in ways.items():
        g = w['geometry']
        cur = [g[0]]
        for pt in g[1:]:
            cur.append(pt)
            if count[K(pt)] > 1 or pt is g[-1]:
                ends = (K(cur[0]), K(cur[-1]))
                if all(count[k] > 1 for k in ends) and ends[0] != ends[1]:
                    ids = []
                    for k, gp in zip(ends, (cur[0], cur[-1])):
                        nid = 'bosco:quercus' if k == jkey else names.setdefault(k, f'bosco:q{len(names)}')
                        pos.setdefault(nid, bosco_map(to_local(gp['lon'], gp['lat']), anchors))
                        ids.append(nid)
                    poly = [bosco_map(to_local(q['lon'], q['lat']), anchors) for q in cur]
                    poly[0], poly[-1] = pos[ids[0]], pos[ids[1]]
                    path = wid != QUERCUS_SERVIZIO
                    out.append({**base, 'a': ids[0], 'b': ids[1], 'poly': poly, 'cls': 'path' if path else 'unclassified',
                                'foot': path, 'walk': path})
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
    # Contrada Annunziata oltre l'incrocio del vivaio (OSM w252747446): si vede, non si percorre.
    deco = []
    for el in elements:
        if el.get('type') == 'way' and el['id'] == 252747446:
            real_pts = [to_local(g['lon'], g['lat']) for g in el['geometry']]
            keep = [bosco_map(q, anchors) for q in real_pts if inside(q, (ZONA_V[0] + 15, ZONA_V[1], ZONA_V[2] + 15, ZONA_V[3]))]
            if len(keep) > 1:
                deco.append({**base, 'a': None, 'b': None, 'poly': keep, 'cls': 'unclassified', 'name': None})
    return ([{**base, 'a': start, 'b': 'bosco:svolta', 'poly': a, 'cls': 'secondary', 'name': BOSCO_PROVINCIALE},
             {**base, 'a': 'bosco:svolta', 'b': 'bosco:quercus', 'poly': b, 'cls': 'tertiary', 'name': None},
             {**base, 'a': 'bosco:quercus', 'b': 'bosco:vivaio', 'poly': c, 'cls': 'tertiary', 'name': None}] + paths, deco)


def build_network(data, buildings, bosco_osm):
    """
    Rete percorribile (2-core del grafo, più le vie cieche del centro storico con la goccia)
    e vie decorative: le vie cieche reali della città moderna, visibili ma non percorribili.
    """
    edges, pos = build_edges(data['segment'], data['connector'])
    edges = [e for e in edges if e['a'] != e['b'] and shapely.contains_xy(CITY_ROADS, *np.array(e['poly']).T).all()]
    edges, pos = merge_close_nodes(edges, pos)
    drivable = [e for e in edges if not e['deco'] and not e.get('walk')]
    # Marciapiedi, passaggi e scalinate del centro storico (blocco G) contano per gli anelli: una via
    # carrabile resta se chiude un anello anche passando a piedi.
    walk = [e for e in edges if e.get('walk')]
    core = two_core(drivable + walk)
    extra = [e for t in dead_end_trees(drivable, core)
             if any(x['name'] in KEEP_DEAD_ENDS for x in t) and all(inside(midpoint(x['poly']), Z0) for x in t) for e in t]
    bosco_edges, bosco_deco = bosco_road(core, pos, bosco_osm)
    extra += bosco_edges
    tree = STRtree(buildings)
    net, loops = add_turnarounds(core, extra, pos, tree, buildings)
    # Dove una via carrabile continua solo a piedi, la goccia lascia scegliere: si scende o si torna
    # indietro. Se la goccia non ci sta, la via resta e in fondo si prosegue per forza a piedi.
    drive, more = add_turnarounds([e for e in net if not e.get('walk')], [], pos, tree, buildings, prune=False)
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
    deco = [e for e in edges if id(e) not in used and not e['foot'] and not e['bridge'] and not inside(midpoint(e['poly']), Z0)]
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
KIND = {'house': 0, 'church': 1, 'cathedral': 2, 'shed': 3, 'apartments': 4, 'public': 5, 'rurale': 6}


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


def build_buildings(raw):
    area = CITY_ZONE
    out = []
    for b in raw:
        if b.get('is_underground'):
            continue
        g = local_geom(shape(b['geom'])).intersection(area)
        polys = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
        for p in polys:
            if p.is_empty:
                continue
            # centro storico a 0,3 m (come nelle fasi 2–3), città moderna a 0,5 m
            p = p.simplify(0.3 if inside(p.centroid.coords[0], Z0) else 0.5, preserve_topology=True)
            if p.is_empty or p.area < 8:
                continue
            out.append({'poly': p, 'kind': building_kind(b.get('class')), 'cls': b.get('class'),
                        'name': (b.get('names') or {}).get('primary'), 'height': reliable_height(b),
                        'level': b.get('level') or 0})
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
        return TURN_WIDTH
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
    rl = rl.difference(box(BOSCO[0] - 80, VIVAIO[2] - 80, BOSCO[1] + 80, BOSCO[3]))
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
        if l.get('class') not in ('pedestrian', 'plaza', 'park', 'grass', 'garden'):
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
         'cimitero': 7, 'sport': 8, 'piazza': 9, 'macchia': 10, 'cava': 11, 'querce': 12, 'bruciato': 13, 'fitto': 14, 'roccia': 15}
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
    for z in (BOSCO, VIVAIO):
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


def land_cover(data, buildings, bosco_osm, rock=None):
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
    e superficie. Palazzine da 2 a 6 piani nei quartieri, capannoni da 7 a 9 m, case di
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
        floors = 4 + int(seed * 2.99)
    return floors * 3.3 + 0.6


CITY_KIND = {'house': 0, 'church': 1, 'shed': 3, 'apartments': 4, 'public': 5, 'industry': 6, 'castle': 7, 'school': 8, 'villa': 9, 'padiglione': 10, 'tribuna': 11}


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
    ('Scuola primaria Santomasi', (387, 596), 2),               # Overture, Corso Aldo Moro
]
CHURCHES = [
    ('Chiesa Gesù Buon Pastore', (1055, -176)),                 # OSM w328013129 (edificio senza nome)
    ('SS. Crocifisso e San Sebastiano', (442, -571)),           # OSM r6148330 e Overture
    ('Santuario Madonna delle Grazie', (658, 826)),             # Overture, Via Madonna della Grazia
    ('Santi Pietro e Paolo', (1080, 1140)),                     # Overture (Via Luigi Longo), edificio OSM w411139942
]
MENINNI = ('Casino di Meninni', (1572, -536))                   # sul Guardialto, sopra la SP201 (Via Guardialto)
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
    inner = shapely.union_all([box(z[0] + 6, z[2] + 6, z[1] - 6, z[3] - 6) for z in (BOSCO, VIVAIO)])
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
    clear_v = Point(*feats['picnic']).buffer(40).union(Point(*feats['scritta'][:2]).buffer(24))   # area pic-nic: prato senza alberi dei riquadri
    paths_d = [LineString(e['poly']) for e in bosco_ways(elements, anchors, {}) if e['walk']]
    near_path = shapely.union_all([p.buffer(42) for p in paths_d]) if paths_d else None
    burned = [box(x0, y0, x1, y1) for x0, x1, y0, y1 in BOSCO_BRUCIATO]
    counts = collections.Counter()
    for j, n in enumerate(N):
        for i, e in enumerate(E):
            if not (inside((e, n), BOSCO) or inside((e, n), VIVAIO)):
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
    b = pick(MENINNI[1])
    if b:
        b['name'], b['kind'], b['height'] = MENINNI[0], CITY_KIND['villa'], 9.5
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
    print(f'  binari: {len(rails)} tratti, {sum(r["line"].length for r in rails) / 1000:.1f} km')
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
        return ((1 if e['bridge'] else 0) | (2 if e['foot'] else 0) | (4 if e.get('turn') else 0)
                | (8 if e['cls'] in ('track', 'path') else 0) | (16 if e.get('urban') else 0) | (32 if e.get('walk') else 0))
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
        'bosco': extra['bosco'],
        'botromagno': extra['botromagno'],
        'sport': extra['sport'],
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
    # Blocco L: edifici reali attorno all'area Quercus e al vivaio (al posto della capanna generica)
    bosco_osm = overpass_bosco()
    buildings += bosco_buildings(bosco_osm)
    print('3. Rete stradale')
    edges, deco, pos = build_network(data, [b['poly'] for b in buildings], bosco_osm)
    buildings, arches = free_roads(edges + deco, pos, buildings)
    deco = deco_off_roads(edges, deco)
    print('4. Morfologia, quote reali, uso del suolo')
    feats = build_features(data)
    at, ground, light, _, _ = ground_model(dem_at, buildings)
    rims = extend_rims(feats['river'], at)
    buildings, bot = botromagno(overpass_cached('rovine', ROVINE_OVERPASS), feats['river'], rims[1], buildings)
    cover = land_cover(data, buildings, bosco_osm, bot['rock'])
    old = [b for b in buildings if inside(b['poly'].centroid.coords[0], Z0)]
    city = city_buildings([b for b in buildings if not inside(b['poly'].centroid.coords[0], Z0)], cover)
    print(f'  edifici: {len(old)} nel centro storico, {len(city)} nella città')
    versante(old, bot)
    city, sport = stadio_fiera(overpass_cached('stadio_fiera', STADIO_FIERA_OVERPASS), city)
    name_places(old, city)
    extra = {
        'ground': ground, 'cover': cover, 'rails': build_rails(data), 'pois': city_pois(osm),
        'riverY': river_bed(feats['river'], lambda e, n: at(e, n)), 'rims': rims,
        'rioni': rioni_profile(at), 'bosco': bosco_features(bosco_osm),
        'sport': sport,
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
