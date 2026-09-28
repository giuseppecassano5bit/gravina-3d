/**
 * Prova delle interazioni come le fa un visitatore: credito e pannello «Il progetto», scelta del mezzo, partenza,
 * pausa e ripresa da tastiera, minimappa, teletrasporto da etichetta 3D e da
 * elenco, cambio mezzo in pausa, pausa automatica a scheda nascosta, mezzo
 * ricordato alla riapertura, percorsi a piedi (sosta all'imbocco, figurina, pausa, ripartenza,
 * teletrasporto). Fallisce alla prima attesa non rispettata.
 */
import { open } from './common.mjs';

const { browser, page, logs } = await open();
const state = () => page.evaluate(() => ({ phase: window.gravina.phase, speed: window.gravina.driver.speed, street: window.gravina.driver.edge.name }));
const advance = (s) => page.evaluate((s) => window.gravina.advance(s), s);
let failures = 0;
const check = (label, ok, info = '') => {
  console.log(`${ok ? '✓' : '✗'} ${label}${info ? ` · ${info}` : ''}`);
  if (!ok) failures++;
};

const credit = await page.textContent('.credit__name');
check('nella schermata iniziale c’è il credito', credit.trim() === 'Giuseppe Cassano', credit.trim());
await page.click('#btn-about');
check('«Il progetto» apre il pannello', await page.isVisible('#about') && await page.evaluate(() => document.activeElement.id === 'about-close'));
await page.keyboard.press('Escape');
check('Esc chiude il pannello e il fuoco torna al pulsante', !(await page.isVisible('#about')) && await page.evaluate(() => document.activeElement.id === 'btn-about'));

await page.click('#start-picker .vcard[data-id="rs6"]');
await page.click('#btn-start');
await page.evaluate(() => window.gravina.driver.start());
await advance(4);
let s = await state();
check('si parte dalla via del ponte e si attraversa', s.phase === 'drive' && s.speed > 3, s.street);

await page.keyboard.press('p');
await advance(2);
s = await state();
check('P mette in pausa e il mezzo si ferma', s.phase === 'pause' && s.speed === 0 && await page.isVisible('#pause-sheet'));

await page.keyboard.press('Escape');
await advance(2);
s = await state();
check('Esc riprende il viaggio', s.phase === 'drive' && s.speed > 1 && !(await page.isVisible('#pause-sheet')));

await page.click('#minimap-btn');
check('la minimappa apre la pausa', (await state()).phase === 'pause');

const label = await page.evaluate(() => {
  const el = [...document.querySelectorAll('.pin-label')].find((e) => e.style.display !== 'none' && getComputedStyle(e).pointerEvents === 'auto');
  const r = el?.getBoundingClientRect();
  return el ? { name: el.textContent, x: r.x + r.width / 2, y: r.y + r.height / 2 } : null;
});
check('in pausa le etichette sono cliccabili', !!label, label?.name);
if (label) {
  await page.mouse.click(label.x, label.y);
  await page.waitForTimeout(900);
  await advance(1);
  s = await state();
  check('il clic su un’etichetta teletrasporta e si riparte', s.phase === 'drive' && s.speed > 0, s.street);
}

await page.keyboard.press('p');
await page.click('#pause-picker .vcard[data-id="deere"]');
const pace = await page.evaluate(() => window.gravina.driver.pace);
check('in pausa si cambia mezzo', pace === 0.62, `ritmo ${pace}`);

await page.click('.poi >> text=Cattedrale di Santa Maria Assunta');
await page.waitForTimeout(900);
await advance(1);
s = await state();
check('dall’elenco si va alla Cattedrale', s.phase === 'drive' && s.street === 'Piazza Benedetto XIII', s.street);

await page.evaluate(() => { Object.defineProperty(document, 'hidden', { value: true, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); });
check('scheda nascosta: pausa automatica', (await state()).phase === 'pause');

// A piedi (blocco G): il mezzo si ferma all'imbocco del tratto pedonale, la figurina lo percorre
// e al tratto carrabile ritrova il mezzo, che riparte. Pausa e teletrasporto funzionano anche a piedi.
const foot = () => page.evaluate(() => {
  const d = window.gravina.driver;
  return { onFoot: d.onFoot, walk: d.edge.walk, speed: d.speed, remaining: d.remaining, car: d.car && [d.car.pos.x, d.car.pos.z], street: d.edge.name,
    figure: window.gravina.scene.getObjectByName('figurina')?.visible, plate: document.getElementById('plaque-dest').textContent, phase: window.gravina.phase };
});
const until = async (test, seconds, dt = 0.25) => {
  for (let t = 0; t < seconds; t += dt) { if (await test()) return true; await advance(dt); }
  return test();
};
await page.keyboard.press('Escape');
await page.evaluate(() => { const g = window.gravina; g.placeAt(60, -40, [-1, 0]); g.rig.snap(g.driver); });
const sign = await until(() => page.isVisible('.sign:has-text("a piedi")'), 20);
check('agli incroci c’è il cartello «a piedi»', sign);
if (sign) await page.click('.sign:has-text("a piedi")');
await until(async () => (await foot()).onFoot, 20);
let f = await foot();
check('il mezzo si ferma all’imbocco e scende la figurina', f.onFoot && f.figure && f.speed === 0 && Math.abs(f.remaining - 3.2) < 0.6, `${f.street}, ${f.remaining.toFixed(1)} m dall’imbocco`);
const parked = f.car;
await advance(4);
f = await foot();
check('la figurina percorre il tratto pedonale, il mezzo resta fermo', f.onFoot && f.walk && f.speed > 2 && f.car[0] === parked[0] && /percorso pedonale/.test(f.plate), `${f.street} · ${f.plate}`);
await page.keyboard.press('p');
await advance(1.5);
f = await foot();
check('P mette in pausa anche a piedi', f.phase === 'pause' && f.speed === 0 && f.onFoot);
await page.keyboard.press('Escape');
const back = await until(async () => { const x = await foot(); return !x.onFoot && !x.walk; }, 90, 0.5);
await advance(2);
f = await foot();
check('al tratto carrabile si ritrova il mezzo e si riparte', back && !f.onFoot && !f.figure && f.speed > 1, f.street);
await page.evaluate(() => { const g = window.gravina; g.placeAt(230, -20, [1, 0]); g.rig.snap(g.driver); });
await until(async () => (await foot()).onFoot, 20);
await page.keyboard.press('p');
await page.evaluate(() => window.gravina.goTo('duomo'));
await page.waitForTimeout(900);
await advance(1);
f = await foot();
check('il teletrasporto da piedi riporta sul mezzo', f.phase === 'drive' && !f.onFoot && !f.figure && f.speed > 0, f.street);

await page.reload();
await page.waitForFunction(() => !document.getElementById('btn-start').disabled, null, { timeout: 120000 });
const kept = await page.evaluate(() => document.querySelector('#start-picker .vcard.is-selected')?.dataset.id);
check('alla riapertura resta il mezzo scelto', kept === 'deere', kept);

const errors = logs.filter((l) => /error/i.test(l));
check('nessun errore in console', errors.length === 0, errors.join(' | '));
await browser.close();
process.exit(failures ? 1 : 0);
