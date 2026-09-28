/**
 * Screenshot delle scene principali in tools/test/shots/:
 * vetrina dei quattro mezzi vicino al ponte e campo lungo sulle arcate, pannello «Il progetto», partenza sul ponte, incrocio,
 * menu di pausa, teletrasporto, un arco sulla via e il centro.
 * Con "mobile" usa un telefono in verticale, con "orizzontale" un telefono in orizzontale.
 */
import { open, report, SHOTS } from './common.mjs';

const mode = process.argv[2];
const device = mode === 'mobile' ? { mobile: true } : mode === 'orizzontale' ? { mobile: true, landscape: true } : {};
const pre = mode === 'mobile' ? 'mobile' : mode === 'orizzontale' ? 'orizz' : 'desktop';
const { browser, page, logs } = await open(device);
const run = (fn, arg) => page.evaluate(fn, arg);
const shot = async (name, wait = 900) => {
  await page.waitForTimeout(wait);
  await page.screenshot({ path: `${SHOTS}/${pre}-${name}.png` });
  console.log(name, '·', await run(() => `${window.gravina.phase} · ${window.gravina.driver.edge.name}`));
};

// Vetrina: i quattro mezzi fermi vicino al ponte.
for (const [i, id] of ['panda', 'rs6', 'huracan', 'deere'].entries()) {
  await page.click(`#start-picker .vcard[data-id="${id}"]`);
  await run(() => window.gravina.advance(2.5));
  await shot(`0${i}-vetrina-${id}`, 700);
}
// Vetrina, secondo tempo: il campo lungo sul Ponte Acquedotto con le arcate.
await run(() => window.gravina.advance(14));
await shot('04-vetrina-ponte', 700);
// Il pannello «Il progetto», aperto dalla schermata iniziale.
await page.click('#btn-about');
await shot('05-progetto', 600);
await page.keyboard.press('Escape');
await page.click('#start-picker .vcard[data-id="huracan"]');

// Partenza: si attraversa il ponte.
await page.click('#btn-start');
await run(() => { const g = window.gravina; g.driver.start(); g.advance(9); });
await shot('10-ponte', 1500);

// Pausa con il menu (e la mappa).
await run(() => { const g = window.gravina; g.advance(6); g.pause(); g.advance(3); });
await shot('20-pausa');
await page.click('#pause-picker .vcard[data-id="deere"]');
await run(() => window.gravina.advance(1));
await shot('21-pausa-trattore', 300);

// Mappa: si sceglie un luogo e si va.
const box = await page.locator('#bigmap').boundingBox();
if (box) {
  await page.locator('#bigmap').scrollIntoViewIfNeeded();
  // la mappa si apre sul mezzo, con lo zoom: il punto sulla tela lo dà la mappa stessa (pixel del dispositivo)
  const pos = await run(() => {
    const g = window.gravina, lm = g.landmarks.find((l) => l.id === 'purgatorio');
    const [x, y] = g.pauseMap.xy(...lm.at);
    return { x: x / g.pauseMap.dpr, y: y / g.pauseMap.dpr };
  });
  await page.locator('#bigmap').click({ position: pos });
  await shot('22-mappa-scelta', 400);
  await page.click('#map-go');
  await run(() => window.gravina.advance(0.1));
  await page.waitForTimeout(1200);
  await run(() => window.gravina.advance(4));
  await shot('30-teletrasporto', 300);
}

// Un arco sulla via (L'Arc D' Bench) e il centro storico.
await run(() => { const g = window.gravina; g.rig.vista.cooldown = 99; g.placeAt(313, 112, [0, -1], 0); g.driver.running = true; g.driver.speed = 6; g.rig.snap(g.driver); g.advance(1); });
await shot('40-arco');
await run(() => { const g = window.gravina; g.useVehicle('panda'); g.placeAt(160, -12, [1, 0]); g.driver.speed = 8; g.rig.snap(g.driver); g.advance(3); });
await shot('50-centro');

// Dettagli dei monumenti: camera libera sulla via più vicina, rivolta al monumento.
if (mode !== 'mobile' && mode !== 'orizzontale') {
  await page.evaluate(() => { document.getElementById('hud').hidden = true; document.querySelector('.labels').hidden = true; });
  // [luogo, distanza, altezza della camera]; per il ponte una vista dal canyon.
  const views = [['purgatorio', 16, 13], ['duomo', 42, 26], ['fontana', 16, 7], ['sanmichele', 38, 18], ['ponte', 0, 0], ['orsini', 26, 20]];
  for (const [k, [id, dist, height]] of views.entries()) {
    await run(([id, dist, height]) => {
      const g = window.gravina, lm = g.landmarks.find((l) => l.id === id);
      g.rig.mode = 'free';
      if (id === 'ponte') {
        g.camera.position.set(-5, -8, -225);
        g.camera.lookAt(-24, -12, -297);
      } else if (id === 'purgatorio') {
        const b = g.DATA.building('Santa Maria del Suffragio');
        const fe = g.Details.frontEdge(g.DATA.pairs(b[3][0]), 5, g.DATA.locate('Chiesa del Purgatorio'));
        const y = g.Terrain.heightAt(fe.M[0] + fe.n[0] * 2, fe.M[1] + fe.n[1] * 2);
        g.camera.position.set(fe.M[0] + fe.n[0] * 11 + fe.n[1] * 3, y + 5, -(fe.M[1] + fe.n[1] * 11 - fe.n[0] * 3));
        g.camera.lookAt(fe.M[0], y + 4, -fe.M[1]);
      } else {
        const near = g.network.closestSample(lm.at[0], lm.at[1]);
        const S = near.edge.samples, i = near.i;
        const de = S[i * 3] - lm.at[0], dn = -S[i * 3 + 2] - lm.at[1], l = Math.hypot(de, dn) || 1;
        const y = g.Terrain.heightAt(lm.at[0], lm.at[1]);
        g.camera.position.set(lm.at[0] + (de / l) * dist, y + height, -(lm.at[1] + (dn / l) * dist));
        g.camera.lookAt(lm.at[0], y + 5, -lm.at[1]);
      }
      g.advance(0.1);
    }, [id, dist, height]);
    await shot(`6${k}-dettaglio-${id}`, 500);
  }
}
report(logs);
await browser.close();
