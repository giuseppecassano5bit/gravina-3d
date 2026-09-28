/**
 * Immagine di anteprima per i social e i motori di ricerca: og-image.jpg (1200×630, JPEG ≤ 150 KB)
 * nella radice del progetto, citata dai meta og:image e twitter:image di index.html.
 * Inquadratura del diorama senza interfaccia, con una targa in marmo come quelle del centro storico.
 *
 * Uso: node anteprima.mjs                → rigenera ../../og-image.jpg
 *      node anteprima.mjs prova e n y te tn ty [altre sei cifre…]
 *        → prove di inquadratura in shots/anteprima-<n>.png (quote come in vista.mjs: "t+3" = 3 m sopra il terreno)
 */
import fs from 'fs';
import path from 'path';
import { open, report, ROOT, SHOTS } from './common.mjs';

/** Inquadratura scelta: camera (est, nord, quota) e punto guardato. */
const POSA = ['-30', '440', 't+42', '15', '240', 't-5'];
const W = 1200, H = 630, TETTO = 150 * 1024;

const [cmd, ...nums] = process.argv.slice(2);
const prova = cmd === 'prova';
const pose = [];
if (prova) for (let i = 0; i + 5 < nums.length; i += 6) pose.push(nums.slice(i, i + 6));
else pose.push(POSA);

const { browser, page, logs } = await open({ w: W, h: H });
// Per la targa servono i caratteri veri: qui si lasciano passare i Google Fonts (serve la rete).
await page.unroute('https://fonts.googleapis.com/**');
await page.unroute('https://fonts.gstatic.com/**');
await page.addStyleTag({ url: 'https://fonts.googleapis.com/css2?family=Marcellus+SC&family=Barlow+Semi+Condensed:wght@600&display=block' });
await page.evaluate(() => Promise.all([document.fonts.load('50px "Marcellus SC"'), document.fonts.load('600 19px "Barlow Semi Condensed"')]));
await page.evaluate(() => {
  for (const s of ['#hud', '.labels', '.start', '.debug']) document.querySelector(s)?.setAttribute('hidden', '');
});

const inquadra = (v) => page.evaluate((v) => {
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

if (prova) {
  for (const [k, v] of pose.entries()) {
    await inquadra(v);
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${SHOTS}/anteprima-${k}.png` });
    console.log(`shots/anteprima-${k}.png`, v.join(' '));
  }
} else {
  await inquadra(POSA);
  // Targa in marmo (stessi colori e caratteri della targa stradale del diorama).
  await page.evaluate(() => {
    const t = document.createElement('div');
    t.innerHTML = '<b>Gravina in Puglia</b><span>Il centro storico in 3D</span>';
    Object.assign(t.style, {
      position: 'fixed', left: '48px', bottom: '44px', display: 'grid', gap: '6px',
      padding: '16px 30px 18px', color: '#2C2620', background: '#F4EEE2', borderRadius: '4px',
      boxShadow: 'inset 0 0 0 5px #F4EEE2, inset 0 0 0 7px #7A6F60, 0 18px 40px rgba(0,0,0,0.35)',
    });
    Object.assign(t.querySelector('b').style, { font: '400 50px/1.05 "Marcellus SC", Georgia, serif', letterSpacing: '0.05em' });
    Object.assign(t.querySelector('span').style, {
      font: '600 19px/1.2 "Barlow Semi Condensed", "Arial Narrow", sans-serif', letterSpacing: '0.18em', textTransform: 'uppercase', color: '#6B5F50',
    });
    document.body.append(t);
  });
  await page.waitForTimeout(500);
  const out = path.join(ROOT, 'og-image.jpg');
  let quality = 86, bytes = Infinity;
  while (quality >= 50) {
    await page.screenshot({ path: out, type: 'jpeg', quality });
    bytes = fs.statSync(out).size;
    if (bytes <= TETTO) break;
    quality -= 6;
  }
  console.log(`og-image.jpg · ${W}×${H} · qualità ${quality} · ${(bytes / 1024).toFixed(0)} KB`);
  if (bytes > TETTO) { console.log('✗ oltre 150 KB'); process.exitCode = 1; }
}
if (!report(logs)) process.exitCode = 1;
await browser.close();
