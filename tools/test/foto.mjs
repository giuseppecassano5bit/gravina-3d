/**
 * Screenshot delle scene principali in tools/test/shots/:
 * schermata iniziale, partenza, incrocio, ponte, ciglio, centro. Con "mobile" usa un telefono.
 */
import { open, report, SHOTS } from './common.mjs';

const mobile = process.argv[2] === 'mobile';
const pre = mobile ? 'mobile' : 'desktop';
const { browser, page, logs } = await open(mobile ? { mobile: true } : {});
const shot = async (name) => {
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${SHOTS}/${pre}-${name}.png` });
  console.log(name, await page.evaluate(() => window.gravina.driver.edge.name));
};
const run = (fn, arg) => page.evaluate(fn, arg);

await shot('00-inizio');
await page.click('#btn-start');
await run(() => { window.gravina.driver.start(); window.gravina.advance(6); });
await shot('10-partenza');
await run(() => { const g = window.gravina; for (let i = 0; i < 900 && !(g.driver.decision?.options.length > 1 && g.driver.remaining < 25); i++) g.advance(1 / 30); });
await shot('11-incrocio');
await run(() => {
  const g = window.gravina;
  g.placeAt(60, 310, [-1, -0.5]); g.driver.running = true; g.driver.speed = 7; g.rig.snap(g.driver);
  for (let i = 0; i < 1200 && !g.driver.decision?.options.some((o) => o.edge.bridge); i++) g.advance(1 / 30);
  const d = g.driver.decision; if (d) g.driver.choose(d.options.findIndex((o) => o.edge.bridge));
  for (let i = 0; i < 1200 && !g.driver.edge.bridge; i++) g.advance(1 / 30);
  g.advance(6);
});
await shot('20-ponte');
await run(() => { const g = window.gravina; g.rig.vista.cooldown = 0; g.placeAt(100, 333, [-1, -0.3]); g.driver.running = true; g.driver.speed = 8; g.rig.snap(g.driver); g.advance(6); });
await shot('30-ciglio');
await run(() => { const g = window.gravina; g.rig.vista.cooldown = 99; g.placeAt(160, -12, [1, 0]); g.driver.running = true; g.driver.speed = 8; g.rig.snap(g.driver); g.advance(3); });
await shot('40-centro');
report(logs);
await browser.close();
