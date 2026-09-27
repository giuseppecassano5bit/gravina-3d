/**
 * Inquadrature libere per controllare i dettagli (sviluppo).
 * Uso: node vista.mjs nome est nord quota guardaEst guardaNord guardaQuota [altre sei cifre per più viste…]
 * Le quote sono assolute; con "t+3" la quota è relativa al terreno in quel punto.
 * Gli screenshot finiscono in tools/test/shots/vista-<nome>-<n>.png
 */
import { open, report, SHOTS } from './common.mjs';

const [name, ...nums] = process.argv.slice(2);
const views = [];
for (let i = 0; i + 5 < nums.length; i += 6) views.push(nums.slice(i, i + 6));
const { browser, page, logs } = await open({ w: 1280, h: 720 });
await page.evaluate(() => {
  document.getElementById('hud').hidden = true;
  document.querySelector('.labels').hidden = true;
  document.querySelector('.start')?.setAttribute('hidden', '');
  const d = document.querySelector('.debug'); if (d) d.hidden = true;
});
for (const [k, v] of views.entries()) {
  await page.evaluate((v) => {
    const g = window.gravina;
    const q = (s, e, n) => (String(s).startsWith('t') ? g.Terrain.heightAt(e, n) + Number(String(s).slice(1) || 0) : Number(s));
    const [e, n, y, te, tn, ty] = v;
    g.rig.mode = 'free';
    g.rig.setFrame(0, 0, true);
    g.camera.clearViewOffset();
    g.camera.position.set(+e, q(y, +e, +n), -n);
    g.camera.lookAt(+te, q(ty, +te, +tn), -tn);
    g.advance(0.05);
  }, v);
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${SHOTS}/vista-${name}-${k}.png` });
}
report(logs);
await browser.close();
