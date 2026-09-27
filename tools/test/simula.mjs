/**
 * Prova di robustezza: un'ora di guida simulata con scelte casuali agli incroci.
 * Fallisce se il mezzo si blocca, se la rete ha vicoli ciechi, se qualche
 * edificio invade una carreggiata (le case non devono stare sulla strada)
 * se un dettaglio 3D (portali, campanile, scalinate, lanterne…) sta sulla
 * carreggiata all'altezza del mezzo, o se ci sono errori.
 */
import { open, report } from './common.mjs';

const { browser, page, logs } = await open();
const r = await page.evaluate(() => {
  const g = window.gravina;
  // Bordi e mezzeria di ogni via, ogni 2 m: nessuna sagoma di edificio deve contenerli.
  const polys = g.GEO.buildings.map(([, , , rings]) => g.DATA.pairs(rings[0]));
  const boxes = polys.map((p) => g.Plane.bbox(p));
  let invasioni = 0;
  for (const edge of g.network.edges) {
    const S = edge.samples, half = edge.width / 2 - 0.05;
    for (let i = 1; i < edge.count; i += 2) {
      let te = S[i * 3 + 3] - S[i * 3 - 3], tn = -(S[i * 3 + 5] - S[i * 3 - 1]);
      const l = Math.hypot(te, tn) || 1;
      te /= l; tn /= l;
      for (const k of [-half, 0, half]) {
        const e = S[i * 3] - tn * k, n = -S[i * 3 + 2] + te * k;
        if (polys.some((p, j) => e > boxes[j][0] && e < boxes[j][1] && n > boxes[j][2] && n < boxes[j][3] && g.Plane.contains(p, e, n))) invasioni++;
      }
    }
  }
  // Dettagli 3D (portali, campanile, scalinate, lanterne, archi…): nessun vertice nello spazio
  // del mezzo, cioè sopra la carreggiata tra 0,3 e 3,2 m d'altezza.
  const C = 4, grid = new Map();
  for (const edge of g.network.edges) {
    if (edge.bridge) continue;
    const S = edge.samples;
    for (let i = 0; i <= edge.count; i++) {
      const e = S[i * 3], n = -S[i * 3 + 2], k = Math.floor(e / C) * 10007 + Math.floor(n / C);
      (grid.get(k) ?? grid.set(k, []).get(k)).push([e, n, S[i * 3 + 1], edge.width / 2 - 0.2]);
    }
  }
  const onRoad = (e, n, y) => {
    const ci = Math.floor(e / C), cj = Math.floor(n / C);
    for (let i = ci - 1; i <= ci + 1; i++) for (let j = cj - 1; j <= cj + 1; j++) {
      for (const [se, sn, sy, h] of grid.get(i * 10007 + j) ?? []) if (y > sy + 0.3 && y < sy + 3.2 && Math.hypot(se - e, sn - n) < h) return true;
    }
    return false;
  };
  const skip = new Set(['terreno', 'strade', 'ponte-acquedotto', 'alberi', 'panda-4x4', 'audi-rs6', 'lamborghini-huracan', 'trattore-john-deere']);
  const esclusa = (o) => { for (let x = o; x; x = x.parent) if (skip.has(x.name) || x.userData?.vehicle) return true; return false; };
  const dettagli = {};
  const v = new g.THREE.Vector3(), m = new g.THREE.Matrix4();
  g.scene.updateMatrixWorld(true);
  g.scene.traverse((o) => {
    if (!o.isMesh || esclusa(o)) return;
    const P = o.geometry.attributes.position, count = o.isInstancedMesh ? o.count : 1;
    for (let k = 0; k < count; k++) {
      if (o.isInstancedMesh) { o.getMatrixAt(k, m); m.premultiply(o.matrixWorld); } else m.copy(o.matrixWorld);
      for (let i = 0; i < P.count; i++) {
        v.fromBufferAttribute(P, i).applyMatrix4(m);
        if (onRoad(v.x, -v.z, v.y)) {
          const key = `${o.name || o.parent?.name || '?'} vicino a ${Math.round(v.x / 5) * 5} ${Math.round(-v.z / 5) * 5}`;
          dettagli[key] = (dettagli[key] ?? 0) + 1;
        }
      }
    }
  });
  return { problemi: g.problems, monumenti: g.landmarks.length, casesullastrada: invasioni, dettaglisullastrada: dettagli, simulazione: g.driver.simulate(3600, { step: 1 / 20 }) };
});
console.log(JSON.stringify(r, null, 2));
const ok = report(logs) && r.problemi.length === 0 && r.casesullastrada === 0 && Object.keys(r.dettaglisullastrada).length === 0;
await browser.close();
process.exit(ok ? 0 : 1);
