// Cerca difetti visibili delle vie nei riquadri (fuori dal centro storico): vie sotto il terreno,
// vie che galleggiano, dischi degli incroci sfasati, curve spezzate, vie decorative sovrapposte.
// Uso: node difetti.mjs shots/difetti.json   (con GRAVINA_HTML=percorso/copia.html un'altra versione)
// Scritto nel piano dei blocchi M; blocco M1: una via «galleggia» solo se sotto il suo bordo non c'è
// né terreno né un'altra via o il disco di un incrocio (agli incroci il bordo sta sul disco), e il
// disco si confronta con il suo orlo (Tiles.discRim) dove c'è.
import { open } from './common.mjs';
import fs from 'fs';
const { browser, page } = await open({ gpu: true });
const out = await page.evaluate(() => {
  const g = window.gravina, T = g.Tiles, net = g.network;
  g.buildAll();
  for (const t of T.list) if (t.mesh) T._setLod(t, false);
  // griglia di triangoli per riquadro (celle da 4 m)
  const C = 4;
  for (const t of T.list) {
    if (!t.mesh) continue;
    const geo = t.mesh.geometry, P = geo.attributes.position.array, I = geo.attributes.aInfo.array;
    const [a, b] = t.lod.near, cells = new Map();
    for (let f = a; f < b; f++) {
      const p = f * 9;
      const x0 = Math.min(P[p], P[p + 3], P[p + 6]), x1 = Math.max(P[p], P[p + 3], P[p + 6]);
      const n0 = Math.min(-P[p + 2], -P[p + 5], -P[p + 8]), n1 = Math.max(-P[p + 2], -P[p + 5], -P[p + 8]);
      if (x1 - x0 > 80 || n1 - n0 > 80) continue;
      for (let i = Math.floor(x0 / C); i <= Math.floor(x1 / C); i++) for (let j = Math.floor(n0 / C); j <= Math.floor(n1 / C); j++) {
        const k = i * 100003 + j; (cells.get(k) ?? cells.set(k, []).get(k)).push(f);
      }
    }
    t._cells = cells; t._P = P; t._I = I;
  }
  const hits = (e, n) => {
    const t = T.at(e, n); if (!t?._cells) return [];
    const list = t._cells.get(Math.floor(e / C) * 100003 + Math.floor(n / C)) ?? [], P = t._P, out = [];
    const x = e, z = -n;
    for (const f of list) {
      const p = f * 9, ax = P[p], az = P[p + 2], bx = P[p + 3], bz = P[p + 5], cx = P[p + 6], cz = P[p + 8];
      const d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
      if (Math.abs(d) < 1e-9) continue;
      const l1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d, l2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d, l3 = 1 - l1 - l2;
      if (l1 < -1e-4 || l2 < -1e-4 || l3 < -1e-4) continue;
      // normale verticale?
      const ux = bx - ax, uy = P[p + 4] - P[p + 1], uz = bz - az, wx = cx - ax, wy = P[p + 7] - P[p + 1], wz = cz - az;
      const ny = uz * wx - ux * wz, nl = Math.hypot(uy * wz - uz * wy, ny, ux * wy - uy * wx) || 1;
      out.push({ y: l1 * P[p + 1] + l2 * P[p + 4] + l3 * P[p + 7], type: Math.round(t._I[f * 12]), up: Math.abs(ny) / nl });
    }
    return out;
  };
  const lift = g.CONFIG.city.roadLift;
  const R = { sotto: [], galleggia: [], dischi: [], spezzate: [], sovrapposte: [], scarpate: [] };
  const all = [...net.edges.map((e) => [e, false]), ...net.deco.map((e) => [e, true])];
  for (const [edge, deco] of all) {
    if (edge.bridge) continue;
    const S = edge.samples, half = edge.width / 2, st = Math.max(1, Math.round(4 / edge.step));
    for (let i = st; i < edge.count; i += st) {
      const e = S[i * 3], n = -S[i * 3 + 2], y = S[i * 3 + 1];
      if (T.inZ0(e, n)) continue;
      const yr = y + lift;
      const i0 = (i - 1) * 3, i1 = (i + 1) * 3;
      let te = S[i1] - S[i0], tn = -(S[i1 + 2] - S[i0 + 2]); const l = Math.hypot(te, tn) || 1; te /= l; tn /= l;
      const occ = g.Buildings.occupied?.(e, n);
      // 1. terreno sopra la via (al centro)
      const ground = hits(e, n).filter((h) => h.type === 0 && h.up > 0.3);
      const top = Math.max(-1e9, ...ground.map((h) => h.y));
      if (!occ && top > yr + 0.12) R.sotto.push({ e: +e.toFixed(1), n: +n.toFixed(1), d: +(top - yr).toFixed(2), via: edge.name, deco });
      // 2. ai lati: galleggia (terreno sotto il bordo) o scarpata (terreno sopra)
      for (const sg of [1, -1]) {
        const se = e + tn * (half + 0.4) * sg, sn = n - te * (half + 0.4) * sg;
        const gs = hits(se, sn).filter((h) => h.type <= 3 && h.up > 0.3);
        if (!gs.length) continue;
        const ys = Math.max(...gs.filter((h) => h.type === 0 || h.y < yr + 0.3).map((h) => h.y));
        // un muretto di contenimento sotto il bordo (Tiles._wall, blocco M1) chiude il vuoto
        const wall = (T.at(se, sn)?.walls ?? []).concat(T.at(e, n)?.walls ?? []).some(([a0, b0, a1, b1, bottom]) => {
          const dx = a1 - a0, dy = b1 - b0, u = Math.max(0, Math.min(1, ((se - a0) * dx + (sn - b0) * dy) / (dx * dx + dy * dy || 1)));
          return Math.hypot(a0 + dx * u - se, b0 + dy * u - sn) < 0.8 && bottom <= ys + 0.3;
        });
        if (yr - ys > 0.7 && !wall) R.galleggia.push({ e: +e.toFixed(1), n: +n.toFixed(1), d: +(yr - ys).toFixed(2), via: edge.name, deco });
        // scarpata: terreno a 6 m dal bordo molto più alto o basso (pendenza > 100%)
        const fe = e + tn * (half + 5) * sg, fn = n - te * (half + 5) * sg;
        const gf = hits(fe, fn).filter((h) => h.type === 0 && h.up > 0.2);
        if (gf.length) { const yf = Math.max(...gf.map((h) => h.y)); if (Math.abs(yf - yr) > 5) R.scarpate.push({ e: +e.toFixed(1), n: +n.toFixed(1), d: +(yf - yr).toFixed(1), via: edge.name, deco }); }
      }
      // 3. curve spezzate
      if (!edge.turn && i >= 2 * st && i + st <= edge.count) {
        const j0 = (i - st) * 3, j1 = (i + st) * 3;
        const a0 = Math.atan2(-(S[i * 3 + 2] - S[j0 + 2]), S[i * 3] - S[j0]), a1 = Math.atan2(-(S[j1 + 2] - S[i * 3 + 2]), S[j1] - S[i * 3]);
        let da = Math.abs(a1 - a0); if (da > Math.PI) da = 2 * Math.PI - da;
        if (da > 0.7) R.spezzate.push({ e: +e.toFixed(1), n: +n.toFixed(1), d: +(da * 57.3).toFixed(0), via: edge.name, deco });
      }
    }
  }
  // 4. dischi degli incroci: quota della via a r dal centro rispetto al disco
  for (const node of net.nodes) {
    if (!node.edges.length || T.inZ0(node.e, node.n)) continue;
    const r = node.plaza || Math.max(...node.edges.map((x) => x.width)) / 2 + 0.2;
    let worst = 0;
    const rim = T.discRim?.(node);
    for (const edge of node.edges) {
      const fromA = edge.a === node, k = Math.min(edge.count, Math.round(r / edge.step)), idx = (fromA ? k : edge.count - k) * 3;
      let disc = node.y;
      if (rim) {
        const a = Math.atan2(edge.samples[idx + 2] - node.pos.z, edge.samples[idx] - node.pos.x), f = (((a / (2 * Math.PI)) % 1) + 1) % 1 * rim.spokes, q = Math.floor(f);
        disc = rim.ys[q] + (rim.ys[q + 1] - rim.ys[q]) * (f - q);
      }
      worst = Math.max(worst, Math.abs(edge.samples[idx + 1] - disc));
    }
    if (worst > 0.3) R.dischi.push({ e: +node.e.toFixed(1), n: +node.n.toFixed(1), d: +worst.toFixed(2), via: node.edges.map((x) => x.name).join(' / ') });
  }
  // 5. vie decorative sovrapposte alle vie percorribili (lontano dagli incroci)
  for (const d of net.deco) {
    const S = d.samples;
    for (let i = 0; i <= d.count; i += Math.max(1, Math.round(4 / d.step))) {
      const e = S[i * 3], n = -S[i * 3 + 2];
      const near = net.nearest(e, n);
      if (!near) continue;
      const k = near.i ?? Math.round(near.s / near.edge.step);
      const ee = near.edge.samples[k * 3], nn = -near.edge.samples[k * 3 + 2];
      const dist = Math.hypot(ee - e, nn - n), lim = (d.width + near.edge.width) / 2 - 0.6;
      const nodeNear = [near.edge.a, near.edge.b].some((x) => Math.hypot(x.e - e, x.n - n) < 14) || [0, d.count].some((q) => Math.hypot(S[q * 3] - e, -S[q * 3 + 2] - n) < 12);
      if (dist < lim && !nodeNear) R.sovrapposte.push({ e: +e.toFixed(1), n: +n.toFixed(1), d: +dist.toFixed(1), dy: +(S[i * 3 + 1] - near.edge.samples[k * 3 + 1]).toFixed(2), via: d.name + ' / ' + near.edge.name });
    }
  }
  return R;
});
fs.writeFileSync(process.argv[2] ?? 'shots/difetti.json', JSON.stringify(out));
for (const [k, v] of Object.entries(out)) console.log(k.padEnd(12), 'vie del mezzo', String(v.filter((x) => !x.deco).length).padStart(5), '· decorative', v.filter((x) => x.deco).length);
await browser.close();
