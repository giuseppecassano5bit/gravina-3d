/**
 * Prova di robustezza: un'ora di guida simulata con scelte casuali agli incroci.
 * Fallisce se l'auto si blocca, se la rete ha vicoli ciechi o se ci sono errori.
 */
import { open, report } from './common.mjs';

const { browser, page, logs } = await open();
const r = await page.evaluate(() => {
  const g = window.gravina;
  return { problemi: g.problems, monumenti: g.landmarks.length, simulazione: g.driver.simulate(3600, { step: 1 / 20 }) };
});
console.log(JSON.stringify(r, null, 2));
const ok = report(logs) && r.problemi.length === 0;
await browser.close();
process.exit(ok ? 0 : 1);
