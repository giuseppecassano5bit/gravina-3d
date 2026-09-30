/**
 * Prova delle interazioni come le fa un visitatore: credito e pannello «Il progetto», scelta del mezzo, partenza,
 * pausa e ripresa da tastiera, minimappa, teletrasporto da etichetta 3D e da
 * elenco, cambio mezzo in pausa, pausa automatica a scheda nascosta, mezzo
 * ricordato alla riapertura, percorsi a piedi (sosta all'imbocco, figurina, pausa, ripartenza,
 * teletrasporto), camera libera, acceleratore (solo su PC) e radio. Fallisce alla prima attesa non rispettata.
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

// Camera libera (blocco B) e radio: il trascinamento gira la vista e il mezzo continua ad avanzare,
// la rotella cambia la distanza, dopo 4,5 s la camera torna dietro, «Segui il mezzo» la riporta
// subito, con la camera libera il clic sui cartelli sceglie ancora la via; M accende la musica.
const cam = () => page.evaluate(() => { const g = window.gravina;
  return { free: g.rig.free, button: !document.getElementById('btn-follow').hidden, dist: g.camera.position.distanceTo(g.driver.position), speed: g.driver.speed, odo: g.driver.odometer }; });
await page.evaluate(() => { const g = window.gravina; g.placeAt(300, 0, [1, 0]); g.rig.snap(g.driver); });
await advance(2);
const before = await cam();
await page.mouse.move(640, 420); await page.mouse.down(); await page.mouse.move(700, 400, { steps: 4 }); await page.mouse.move(860, 360, { steps: 8 }); await page.mouse.up();
await advance(0.5);
let c = await cam();
check('il trascinamento gira la camera e il mezzo avanza', c.free && c.button && c.speed > 1 && c.odo > before.odo);
const near = c.dist;
await page.mouse.wheel(0, 500);
await advance(0.6);
c = await cam();
check('la rotella allontana la camera', c.dist > near + 2, `${near.toFixed(0)} → ${c.dist.toFixed(0)} m`);
await advance(4.5);
c = await cam();
check('dopo 4,5 s la camera torna dietro al mezzo', !c.free && !c.button);
await page.mouse.move(640, 420); await page.mouse.down(); await page.mouse.move(520, 440, { steps: 10 }); await page.mouse.up();
await advance(0.2);
const freeSign = await until(() => page.isVisible('.sign:not([aria-checked="true"])'), 20);
if (freeSign) {
  const want = await page.evaluate(() => [...document.querySelectorAll('.sign')].findIndex((b) => b.getAttribute('aria-checked') !== 'true'));
  await page.click(`.sign >> nth=${want}`);
  const chosen = await page.evaluate(() => window.gravina.driver.decision?.selected);
  check('con la camera libera il clic su un cartello sceglie la via', chosen === want && (await cam()).free);
}
await page.click('#btn-follow');
await advance(0.3);
check('«Segui il mezzo» riporta subito dietro', !(await cam()).free && await page.isHidden('#btn-follow'));
// Acceleratore (blocco E, solo su PC): con Shift tenuto il mezzo va più veloce e lasciando torna al
// suo passo; all'incrocio con scelta il cartello si apre prima e il tempo per scegliere non si accorcia.
const drv = () => page.evaluate(() => { const d = window.gravina.driver; return { v: d.speed, open: !!d.decision && d.decision.options.length > 1, rem: d.remaining, edge: d.edge.id, cruise: window.gravina.CONFIG.drive.cruiseSpeed * d.pace }; });
await page.evaluate(() => { const g = window.gravina; g.placeAt(760, -120, [1, 0]); g.rig.snap(g.driver); g.driver.decision = null; });
await advance(4);
const calm = await drv();
await page.keyboard.down('Shift');
let top = 0;                                                     // la velocità più alta in 5 s (tra un incrocio e l'altro)
for (let k = 0; k < 25; k++) { await advance(0.2); top = Math.max(top, (await drv()).v); }
check('con Shift tenuto il mezzo accelera', top > calm.cruise * 1.4, `crociera ${calm.cruise.toFixed(1)} m/s, con Shift fino a ${top.toFixed(1)} m/s`);
let opened = null, t = 0;
for (; t < 40 && !opened; t += 0.1) { const x = await drv(); if (x.open) opened = x; else await advance(0.1); }
let told = 0;
if (opened) { const e0 = opened.edge; for (; told < 20 && (await drv()).edge === e0; told += 0.1) await advance(0.1); }
check('all’incrocio il cartello si apre prima e c’è tempo per scegliere', !!opened && opened.rem > 45 && told > 3.5 && await page.isVisible('.sign'),
  opened ? `cartello a ${opened.rem.toFixed(0)} m, ${told.toFixed(1)} s per scegliere` : 'nessun incrocio');
await page.keyboard.up('Shift');
await advance(4);
const calmAgain = await drv();
check('lasciando Shift torna alla velocità normale', calmAgain.v < calm.cruise * 1.1, `${calmAgain.v.toFixed(1)} m/s`);

await page.keyboard.press('m');
await page.waitForTimeout(300);
const radio = await page.evaluate(() => ({ on: window.gravina.Radio.on, label: document.getElementById('radio-label').textContent, pressed: document.getElementById('btn-radio').getAttribute('aria-pressed') }));
check('M accende la radio e il pulsante mostra il brano', radio.on && radio.pressed === 'true' && radio.label !== 'Musica', radio.label);
await page.click('#btn-next');
const second = await page.textContent('#radio-label');
check('«Brano successivo» cambia brano', second !== radio.label, second);
await page.click('#btn-radio');
check('il pulsante spegne la musica', !(await page.evaluate(() => window.gravina.Radio.on)));

await page.reload();
await page.waitForFunction(() => !document.getElementById('btn-start').disabled, null, { timeout: 120000 });
const kept = await page.evaluate(() => document.querySelector('#start-picker .vcard.is-selected')?.dataset.id);
check('alla riapertura resta il mezzo scelto', kept === 'deere', kept);

const errors = logs.filter((l) => /error/i.test(l));
check('nessun errore in console', errors.length === 0, errors.join(' | '));
await browser.close();

// Telefono: un dito gira la camera, due dita la avvicinano o allontanano (tocchi veri via CDP).
{
  const { browser, page } = await open({ mobile: true });
  await page.click('#btn-start');
  await page.evaluate(() => { const g = window.gravina; g.driver.start(); g.placeAt(300, 0, [1, 0]); g.rig.snap(g.driver); g.advance(2); });
  const cdp = await page.context().newCDPSession(page);
  const touch = (type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts.map(([x, y], id) => ({ x, y, id })) });
  const view = () => page.evaluate(() => { const g = window.gravina; g.advance(0.3); return { free: g.rig.free, dist: g.camera.position.distanceTo(g.driver.position) }; });
  await touch('touchStart', [[195, 520]]);
  for (let k = 1; k <= 8; k++) await touch('touchMove', [[195 + k * 12, 520 - k * 4]]);
  await touch('touchEnd', []);
  const one = await view();
  check('telefono: un dito gira la camera', one.free);
  await touch('touchStart', [[150, 500], [240, 500]]);
  for (let k = 1; k <= 8; k++) await touch('touchMove', [[150 + k * 5, 500], [240 - k * 5, 500]]);
  await touch('touchEnd', []);
  const two = await view();
  check('telefono: due dita allontanano la camera', two.dist > one.dist + 1, `${one.dist.toFixed(0)} → ${two.dist.toFixed(0)} m`);
  await page.keyboard.down('Shift');
  check('telefono: niente acceleratore', !(await page.evaluate(() => window.gravina.driver.boosting)));
  await browser.close();
}
process.exit(failures ? 1 : 0);
