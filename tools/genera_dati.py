#!/usr/bin/env python3
"""
Genera i dati geografici REALI di Gravina 3D e li incorpora in index.html.

Fonte: Overture Maps Foundation (release indicata in RELEASE), i cui temi
"transportation", "buildings", "base" e "places" derivano in gran parte da
OpenStreetMap. Licenze: ODbL (© OpenStreetMap contributors) e CDLA-Permissive-2.0.

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
from shapely.geometry import LineString, Point, Polygon, box, mapping, shape
from shapely.strtree import STRtree

# ─────────────────────────────────────────────────────────────────────────────
# Configurazione
# ─────────────────────────────────────────────────────────────────────────────
RELEASE = 'release/2026-09-23.1'
BASE_URL = 'https://overturemaps-us-west-2.s3.amazonaws.com/'
CA_BUNDLE = None                      # es. '/percorso/ca.crt' se serve un proxy con CA propria
BBOX = (16.398, 16.432, 40.806, 40.830)   # lon min, lon max, lat min, lat max
ORIGIN = (40.8174, 16.4134)               # Cattedrale: origine del sistema locale (lat, lon)

AREA = (-340, 440, -320, 540)             # diorama in metri locali: est min/max, nord min/max
AREA_ROADS = (-330, 430, -310, 530)       # le vie devono stare tutte qui dentro

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
        if cls not in DRIVABLE and not on_bridge_route and not near_bridge_west:
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
                'foot': cls not in DRIVABLE,
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


def add_turnarounds(core, extra, pos, buildings_tree, buildings):
    """
    Aggiunge le vie cieche selezionate. A ogni foglia prova a inserire
    un'inversione a goccia che non tocchi gli edifici; se non c'è spazio,
    pota l'ultimo tratto e riprova sulla nuova foglia.
    """
    edges = core + extra
    loops = 0
    tried = set()
    area = box(AREA_ROADS[0], AREA_ROADS[2], AREA_ROADS[1], AREA_ROADS[3])
    while True:
        d = degrees(edges)
        leaves = [n for n, k in d.items() if k == 1]
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
            if placed:
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
                    or e1['foot'] != e2['foot'] or e1.get('turn') or e2.get('turn'):
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


def build_network(data, buildings):
    edges, pos = build_edges(data['segment'], data['connector'])
    edges = [e for e in edges if all(inside(p, AREA_ROADS) for p in e['poly']) and e['a'] != e['b']]
    edges, pos = merge_close_nodes(edges, pos)
    core = two_core(edges)
    extra = [e for t in dead_end_trees(edges, core) if any(x['name'] in KEEP_DEAD_ENDS for x in t) for e in t]
    tree = STRtree(buildings)
    edges, loops = add_turnarounds(core, extra, pos, tree, buildings)
    edges = two_core(edges)
    edges = largest_component(edges)
    edges = merge_chains(edges)
    for e in edges:                                   # geometria più leggera
        if not e.get('turn'):
            e['poly'] = list(LineString(e['poly']).simplify(0.35).coords)
    print(f'  rete: {len(edges)} vie, {len(degrees(edges))} incroci, '
          f'{sum(length(e["poly"]) for e in edges) / 1000:.2f} km, {loops} inversioni a goccia')
    return edges, pos


# ─────────────────────────────────────────────────────────────────────────────
# 3. Edifici
# ─────────────────────────────────────────────────────────────────────────────
KIND = {'house': 0, 'church': 1, 'cathedral': 2, 'shed': 3, 'apartments': 4, 'public': 5}


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
    area = box(AREA[0], AREA[2], AREA[1], AREA[3])
    out = []
    for b in raw:
        if b.get('is_underground'):
            continue
        g = local_geom(shape(b['geom'])).intersection(area)
        polys = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
        for p in polys:
            p = p.simplify(0.3, preserve_topology=True)
            if p.is_empty or p.area < 8:
                continue
            out.append({'poly': p, 'kind': building_kind(b.get('class')),
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
CLASS_WIDTH = {0: 8.0, 1: 7.0, 2: 4.6, 3: 4.2, 4: 4.5, 5: 3.2}   # = CONFIG.road.widths in index.html
BRIDGE_WIDTH, TURN_WIDTH = 5.5, 3.6
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


def _side_clearance(p, n, tree, polys):
    """Distanze dalle facciate a sinistra e a destra di p (None se p è dentro un edificio)."""
    out = []
    for sgn in (1, -1):
        ray = LineString([(p.x, p.y), (p.x + sgn * n[0] * RAY, p.y + sgn * n[1] * RAY)])
        best = RAY
        for i in tree.query(ray):
            g = polys[i]
            if g.contains(p):
                return None
            hit = ray.intersection(g)
            if not hit.is_empty:
                best = min(best, p.distance(hit))
        out.append(best)
    return out


def recenter(e, tree, polys):
    """Sposta la mezzeria verso il centro del vicolo (estremi fermi sugli incroci)."""
    line = LineString(e['poly'])
    L = line.length
    if L < 12:
        return e['poly']
    count = max(2, int(L / 1.5))
    ss = [L * k / count for k in range(count + 1)]
    shifts, normals, points = [], [], []
    half = CLASS_WIDTH[CLASS_CODE.get(e['cls'], 2)] / 2
    for s in ss:
        p, n = _normal(line, s)
        points.append(p)
        normals.append(n)
        d = _side_clearance(p, n, tree, polys)
        if d is None or min(d) >= half + FACADE_GAP or min(d) >= RAY:
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
    full = CLASS_WIDTH[CLASS_CODE.get(e['cls'], 2)]
    line = LineString(centripetal_curve(e['poly']))
    gaps = []
    for s in np.arange(2.5, line.length - 2.5, 1.0):  # lontano dagli spigoli degli incroci
        p, n = _normal(line, s)
        d = _side_clearance(p, n, tree, polys)
        if d is not None and max(d) < RAY:
            gaps.append(d[0] + d[1])
    if not gaps:
        return full
    return round(max(MIN_WIDTH, min(full, float(np.quantile(gaps, 0.2)) - 2 * FACADE_GAP)), 1)


def free_roads(edges, pos, buildings):
    """Ricentra e dimensiona le vie, ritaglia gli edifici, ricava gli archi."""
    ground = [b['poly'] for b in buildings if not b['level']]
    tree = STRtree(ground)
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
        # Corpo sopraelevato attraversato dalla mezzeria: è un arco sulla via.
        if b['level']:
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


# ─────────────────────────────────────────────────────────────────────────────
# 4. Idrografia, morfologia, luoghi
# ─────────────────────────────────────────────────────────────────────────────
def build_features(data):
    big = (AREA[0] - 200, AREA[1] + 200, AREA[2] - 200, AREA[3] + 200)
    river = next(w for w in data['water'] if (w.get('names') or {}).get('primary') == 'Torrente La Gravina')
    rl = LineString([to_local(*p) for p in river['geom']['coordinates']])
    rl = rl.intersection(box(big[0], big[2], big[1], big[3]))
    rl = max(getattr(rl, 'geoms', [rl]), key=lambda g: g.length).simplify(1.0)

    cliffs = [LineString([to_local(*p) for p in l['geom']['coordinates']])
              for l in data['land'] if l.get('class') == 'cliff' and l['geom']['type'] == 'LineString']
    cliffs = [c for c in cliffs if inside(c.centroid.coords[0], AREA)]

    walls, views, bridges = [], [], []
    for i in data['infrastructure']:
        g = local_geom(shape(i['geom']))
        if not inside(g.centroid.coords[0], AREA):
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
        if g.geom_type == 'Polygon' and inside(g.centroid.coords[0], AREA):
            areas.append((l.get('class'), g.simplify(0.5)))

    # Scalinate reali (OSM highway=steps): nel diorama sono gradini di tufo da guardare, non vie.
    steps = []
    for sg in data['segment']:
        if sg.get('class') != 'steps' or sg['geom']['type'] != 'LineString':
            continue
        line = LineString([to_local(*p) for p in sg['geom']['coordinates']]).intersection(box(AREA[0], AREA[2], AREA[1], AREA[3]))
        if line.geom_type == 'LineString' and line.length > 4:
            steps.append(((sg.get('names') or {}).get('primary'), line))

    places = []
    keep = ('christian_place_of_worship', 'museum', 'historic_site', 'public_plaza', 'library', 'bridge', 'park', 'land_feature')
    for p in data['place']:
        cat = p.get('basic_category')
        e, n = to_local(*p['geom']['coordinates'])
        if cat in keep and inside((e, n), AREA) and (p.get('confidence') or 0) >= 0.6:
            places.append((e, n, (p.get('names') or {}).get('primary'), cat))
    return {'river': rl, 'cliffs': cliffs, 'walls': walls, 'views': views,
            'bridges': bridges, 'areas': areas, 'places': places, 'steps': steps}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Scrittura del blocco dati in index.html
# ─────────────────────────────────────────────────────────────────────────────
CLASS_CODE = {'secondary': 0, 'tertiary': 1, 'residential': 2, 'unclassified': 2, 'living_street': 3,
              'pedestrian': 4, 'footway': 5, 'path': 5, 'steps': 5}


def flat(coords):
    return [round(v, 1) for p in coords for v in p]


def encode(edges, pos, buildings, arches, feats):
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
    E = []
    for e in edges:
        flags = (1 if e['bridge'] else 0) | (2 if e['foot'] else 0) | (4 if e.get('turn') else 0)
        poly = list(e['poly'])
        poly[0], poly[-1] = pos[e['a']], pos[e['b']]        # estremi esattamente sui nodi
        E.append([node_ids[e['a']], node_ids[e['b']], CLASS_CODE.get(e['cls'], 2), nid(e['name']), flags, flat(poly), e['width']])
    B = []
    for b in buildings:
        rings = [flat(b['poly'].exterior.coords[:-1])] + [flat(r.coords[:-1]) for r in b['poly'].interiors]
        B.append([b['kind'], nid(b['name']), round(b['height'] or 0, 1), rings])
    geo = {
        'meta': {
            'fonte': f'Overture Maps Foundation {RELEASE.split("/")[-1]} · © OpenStreetMap contributors (ODbL)',
            'origine': list(ORIGIN), 'area': list(AREA),
        },
        'names': names,
        'nodes': flat(nodes),
        'edges': E,
        'buildings': B,
        'arches': [[nid(a['name']), a['width'], flat(a['poly'].exterior.coords[:-1])] for a in arches],
        'river': flat(feats['river'].coords),
        'cliffs': [flat(c.coords) for c in feats['cliffs']],
        'walls': [flat(w.coords) for w in feats['walls'] if w.geom_type == 'LineString'],
        'views': [[round(g.centroid.x, 1), round(g.centroid.y, 1), nid(n)] for g, n in feats['views']],
        'bridges': [flat(b.coords) for b in feats['bridges']],
        'areas': [[c, flat(g.exterior.coords[:-1])] for c, g in feats['areas']],
        'places': [[round(e, 1), round(n, 1), nid(nm), c] for e, n, nm, c in feats['places'] if nm],
        'steps': [[nid(nm), flat(g.coords)] for nm, g in feats['steps']],
        'rims': {'east': flat(EAST_RIM), 'west': flat(WEST_RIM)},
    }
    lines = ['const GEO = {']
    for k, v in geo.items():
        if k in ('edges', 'buildings', 'arches', 'places', 'areas', 'cliffs', 'walls', 'views', 'bridges', 'steps'):
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


def preview(path, edges, buildings, arches, feats):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 13), dpi=80)
    for b in buildings:
        x, y = b['poly'].exterior.xy
        ax.fill(x, y, color='#b0452a' if b['kind'] in (1, 2) else '#dccaa0', lw=0)
    for e in edges:
        road = LineString(e['poly']).buffer(e['width'] / 2)
        x, y = road.exterior.xy
        ax.fill(x, y, color='#e8a23a' if e['bridge'] else '#8fb8a8' if e['foot'] or e.get('turn') else '#8a93a6', lw=0, alpha=0.8)
        x, y = zip(*e['poly'])
        ax.plot(x, y, color='#135', lw=0.4)
    for a in arches:
        x, y = a['poly'].exterior.xy
        ax.fill(x, y, color='#7a2ea0', lw=0)
    for _, g in feats['steps']:
        ax.plot(*g.xy, color='#6a3a1c', lw=2.5)
    x, y = feats['river'].xy
    ax.plot(x, y, color='#2a7fd4', lw=2)
    for rim, c in ((EAST_RIM, 'r'), (WEST_RIM, 'm')):
        ax.plot(*zip(*rim), c + '--', lw=1)
    ax.set_xlim(AREA[0], AREA[1]); ax.set_ylim(AREA[2], AREA[3]); ax.set_aspect('equal')
    plt.tight_layout(); plt.savefig(path)
    print(f'  anteprima: {path}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--forza', action='store_true', help='riscarica i dati ignorando la cache')
    ap.add_argument('--anteprima', metavar='PNG', help='salva una mappa di controllo (richiede matplotlib)')
    args = ap.parse_args()
    print('1. Download (Overture Maps)')
    data = {name: download(name, tt, args.forza) for name, tt in THEMES.items()}
    print('2. Edifici')
    buildings = build_buildings(data['building'])
    print('3. Rete stradale')
    edges, pos = build_network(data, [b['poly'] for b in buildings])
    buildings, arches = free_roads(edges, pos, buildings)
    print('4. Morfologia')
    feats = build_features(data)
    print('5. Scrittura')
    write_html(encode(edges, pos, buildings, arches, feats))
    if args.anteprima:
        preview(args.anteprima, edges, buildings, arches, feats)


if __name__ == '__main__':
    sys.exit(main())
