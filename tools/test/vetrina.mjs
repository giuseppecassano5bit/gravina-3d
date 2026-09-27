/**
 * Vetrina (sviluppo): fotografa il primo piano e il campo lungo sul ponte nei tre formati.
 * Uso: node vetrina.mjs ['[lato,indietro,alto,guarda]' orizzontale] ['[…]' verticale]
 *      → shots/vetrina-<formato>-{vicino,ponte}.png  (i numeri sostituiscono CONFIG.camera.showroom)
 */
import { open, report, SHOTS } from './common.mjs';

for (const [name, opts] of [['desktop', {}], ['mobile', { mobile: true }], ['orizz', { mobile: true, landscape: true }]]) {
  const { browser, page, logs } = await open(opts);
  await page.evaluate(([l, p]) => {
    const S = window.gravina.CONFIG.camera.showroom;
    if (l) S.landscape = JSON.parse(l);
    if (p) S.portrait = JSON.parse(p);
  }, process.argv.slice(2, 4));
  await page.evaluate(() => window.gravina.advance(2.5));
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${SHOTS}/vetrina-${name}-vicino.png` });
  await page.evaluate(() => window.gravina.advance(14));
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${SHOTS}/vetrina-${name}-ponte.png` });
  if (!report(logs)) process.exitCode = 1;
  await browser.close();
}
