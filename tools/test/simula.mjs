/**
 * Prova di robustezza: un'ora di guida simulata con scelte casuali agli incroci.
 * Fallisce se il mezzo si blocca, se la rete ha vicoli ciechi, se qualche
 * edificio invade una carreggiata (le case non devono stare sulla strada)
 * o se ci sono errori.
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
  return { problemi: g.problems, monumenti: g.landmarks.length, casesullastrada: invasioni, simulazione: g.driver.simulate(3600, { step: 1 / 20 }) };
});
console.log(JSON.stringify(r, null, 2));
const ok = report(logs) && r.problemi.length === 0 && r.casesullastrada === 0;
await browser.close();
process.exit(ok ? 0 : 1);
