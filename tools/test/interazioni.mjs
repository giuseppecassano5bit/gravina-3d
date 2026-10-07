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
// (dal blocco N2 la Calata Grotte San Michele è pedonale: si parte da Via Marconi verso nord, dove il passaggio
// pedonale sale alla Calata e da lì al vicolo carrabile)
await page.evaluate(() => { const g = window.gravina; g.placeAt(103, -100, [0, 1]); g.rig.snap(g.driver); });
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
// la rotella cambia la distanza, la camera resta libera finché non si preme «Segui il mezzo» (blocco M1),
// che la riporta subito dietro; con la camera libera il clic sui cartelli sceglie ancora la via; M accende la musica.
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
await advance(6);
c = await cam();
check('dopo 6 s la camera resta libera, col pulsante «Segui il mezzo»', c.free && c.button);
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
// il cartello si guarda quando la scelta si apre (dopo l'incrocio il prossimo può non essere ancora aperto)
let opened = null, t = 0, signShown = false;
for (; t < 40 && !opened; t += 0.1) { const x = await drv(); if (x.open) { opened = x; signShown = await page.isVisible('.sign'); } else await advance(0.1); }
let told = 0;
if (opened) { const e0 = opened.edge; for (; told < 20 && (await drv()).edge === e0; told += 0.1) await advance(0.1); }
check('all’incrocio il cartello si apre prima e c’è tempo per scegliere', !!opened && opened.rem > 45 && told > 3.5 && signShown,
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

// Bosco (blocco L): dalla pausa si va all'area Quercus con la sua scheda, la targa dice «Bosco Difesa
// Grande»; l'interruttore «Suoni del bosco» nella pausa si spegne e si riaccende.
await page.keyboard.press('p');
await page.click('.poi >> text=Area Quercus');
await page.waitForTimeout(900);
await advance(1);
const wood = await page.evaluate(() => ({ phase: window.gravina.phase, card: document.getElementById('card')?.textContent ?? '', plate: document.getElementById('plaque-dest').textContent }));
check('dall’elenco si va all’area Quercus, con la scheda e la targa del bosco', wood.phase === 'drive' && /Quercus/.test(wood.card) && /Bosco Difesa Grande/.test(wood.plate), wood.plate);
await page.keyboard.press('p');
await page.click('#btn-forest-sound');
const off = await page.evaluate(() => [window.gravina.ForestSound.on, document.getElementById('btn-forest-sound').getAttribute('aria-checked')]);
await page.click('#btn-forest-sound');
const onAgain = await page.evaluate(() => window.gravina.ForestSound.on);
check('l’interruttore «Suoni del bosco» si spegne e si riaccende', off[0] === false && off[1] === 'false' && onAgain);
await page.keyboard.press('Escape');

// Blocco M2: tre giri a piedi nuovi. Una guida nella pagina sceglie le uscite come farebbe un visitatore:
// `loop` prende i tratti a piedi non ancora fatti e poi torna al mezzo; `to` va verso un tratto preciso.
await page.evaluate(() => {
  window.__guide = (mode, target, seconds) => {
    const g = window.gravina, d = g.driver, N = g.network;
    const far = (o) => (o.dir > 0 ? o.edge.b : o.edge.a);
    /** Distanza a piedi o in auto da ogni nodo ai nodi di partenza (Dijkstra semplice: circa mille nodi). */
    const dijkstra = (srcs) => {
      const dist = new Map(srcs.map((n) => [n, 0])), done = new Set();
      for (;;) {
        let best = null;
        for (const [n, v] of dist) if (!done.has(n) && (!best || v < dist.get(best))) best = n;
        if (!best) return dist;
        done.add(best);
        for (const e of best.edges) {
          const o = e.a === best ? e.b : e.a, v = dist.get(best) + e.length;
          if (v < (dist.get(o) ?? Infinity)) dist.set(o, v);
        }
      }
    };
    const goal = target && N.edges.find((e) => e.id === target);
    const toGoal = goal && dijkstra([goal.a, goal.b]);
    const visits = new Map(), names = new Set(), cards = new Set(), card = document.getElementById('card');
    let last = null, lastEdge = null, foot = false, walked = 0, odo = d.odometer, back = false;
    for (let t = 0; t < seconds; t += 0.1) {
      if (d.edge !== lastEdge) { lastEdge = d.edge; visits.set(d.edge, (visits.get(d.edge) ?? 0) + 1); if (d.onFoot) names.add(d.edge.name); }
      if (card.classList.contains('is-visible')) cards.add(document.getElementById('card-title').textContent);   // blocco N2: schede apparse
      const dec = d.decision;
      if (dec && dec !== last && dec.options.length > 1) {
        last = dec;
        const opts = dec.options;
        let pick = -1;
        if (mode === 'to') {
          const cost = (o) => (o.edge === goal ? 0 : o.edge.length + (toGoal.get(far(o)) ?? Infinity));
          pick = opts.reduce((b, o, i) => (cost(o) < cost(opts[b]) ? i : b), 0);
        } else {
          pick = opts.findIndex((o) => o.edge.walk && !visits.has(o.edge));
          if (pick < 0 && d.onFoot) pick = opts.findIndex((o) => !o.edge.walk && !o.edge.turn);       // al mezzo
          if (pick < 0 && d.car) {
            const toCar = dijkstra([d.car.edge.a, d.car.edge.b]);
            const cost = (o) => o.edge.length + (toCar.get(far(o)) ?? Infinity) + (visits.get(o.edge) ?? 0) * 50;
            pick = opts.reduce((b, o, i) => (cost(o) < cost(opts[b]) ? i : b), 0);
          }
        }
        if (pick >= 0) d.choose(pick);
      }
      if (mode === 'to' && (d.sitting || (d.edge === goal && d.onFoot && !goal.soste))) break;
      if (d.onFoot) { foot = true; walked += d.odometer - odo; }
      odo = d.odometer;
      if (mode === 'loop' && foot && !d.onFoot && d.speed > 1) { back = true; break; }
      g.advance(0.1, 1 / 30);
    }
    return { back, walked: Math.round(walked), names: [...names], cards: [...cards], street: d.edge.name, onFoot: d.onFoot, sitting: !!d.sitting, speed: d.speed };
  };
});
const guide = (mode, target, seconds) => page.evaluate(([m, t, s]) => window.__guide(m, t, s), [mode, target, seconds]);

// Vivaio: dalla strada del vivaio alla goccia di Contrada Annunziata, «a piedi», anello V2 e ritorno al mezzo.
await page.evaluate(() => { const g = window.gravina; g.placeAt(-300, -2185, [-1, 0], 0); g.rig.snap(g.driver); });
const vivSign = await until(() => page.isVisible('.sign:has-text("a piedi")'), 40);
if (vivSign) await page.click('.sign:has-text("a piedi")');
let w = await guide('loop', null, 900);
check('vivaio: «a piedi» alla goccia, anello V2 e ritorno al mezzo', vivSign && w.back && w.walked > 600 && w.names.includes('Sentiero nel bosco'),
  `${w.walked} m a piedi su ${w.names.join(', ')} · ${w.street}`);

// Sentiero degli scavi (A): da Via giudice Montea, vicino alla Madonna della Stella.
await page.evaluate(() => { const g = window.gravina; g.placeAt(-60, 240, [-1, 0.6], 25); g.rig.snap(g.driver); g.driver.decision = null; });
// il tratto del sentiero più vicino a [−172, 402] (gli id dei tratti cambiano quando si rigenera GEO)
const nearEdge = (name, at) => page.evaluate(([nm, p]) => {
  const mid = (e) => { const k = Math.floor(e.count / 2) * 3; return Math.hypot(e.samples[k] - p[0], -e.samples[k + 2] - p[1]); };
  return window.gravina.network.edges.filter((e) => e.name === nm && !e.turn).sort((x, y) => mid(x) - mid(y))[0]?.id;
}, [name, at]);
w = await guide('to', await nearEdge('Sentiero degli scavi', [-172, 402]), 60);
const scaviStart = await foot();
w = await guide('loop', null, 1500);
check('sentiero degli scavi (A) a piedi, poi di nuovo al mezzo', scaviStart.onFoot && w.back && w.names.includes('Sentiero degli scavi') && w.walked > 500,
  `${w.walked} m a piedi su ${w.names.join(', ')} · ${w.street}`);

// Villa Comunale: a piedi fino alla panchina davanti al Monumento ai Caduti; la figurina si siede, c'è la
// scheda, dopo circa 5 s il pulsante «Esci dalla piazzetta · torna al mezzo», che riporta al mezzo.
await page.evaluate(() => { const g = window.gravina; g.placeAt(330, -95, [-1, -0.3], 0); g.rig.snap(g.driver); g.driver.decision = null; });
const sostaEdge = await page.evaluate(() => window.gravina.network.edges.find((e) => e.soste)?.id);
w = await guide('to', sostaEdge, 300);
const bench = await page.evaluate(() => ({ card: document.getElementById('card').classList.contains('is-visible'), title: document.getElementById('card-title').textContent, btn: !document.getElementById('btn-bench').hidden, car: window.gravina.driver.car?.edge.name }));
check('Villa: la figurina si siede sulla panchina, con la scheda dei Caduti', w.sitting && bench.card && /Caduti/.test(bench.title) && !bench.btn, bench.title);
await advance(5.5);
const benchBtn = await page.isVisible('#btn-bench');
check('dopo circa 5 s compare «Esci dalla piazzetta · torna al mezzo»', benchBtn && /torna al mezzo/i.test(await page.textContent('#btn-bench')));
if (benchBtn) await page.click('#btn-bench');
// la via si legge appena finita la dissolvenza: se il mezzo era su un tratto corto (per esempio un vicolo), dopo
// pochi secondi è già sulla via dopo
await page.waitForFunction(() => !window.gravina.driver.sitting, null, { timeout: 15000 }).catch(() => {});
const backAt = await page.evaluate(() => window.gravina.driver.edge?.name);
await page.waitForTimeout(600);
await advance(2);
f = await foot();
// (la Villa non ha ingressi a piedi su Corso Vittorio Emanuele: il mezzo aspetta dove si è scesi, qui vicino a Piazza Pellicciari)
check('il pulsante riporta al mezzo, dove era parcheggiato, e si riparte', !f.onFoot && !f.figure && f.speed > 0.5 && backAt === bench.car && await page.isHidden('#btn-bench'), `${backAt}, poi ${f.street}`);

// Blocco N2: dal vicolo sopra Via Marconi giù per la Calata Grotte San Michele, tutta a piedi, fino alla terrazza: al
// portico si apre la scheda di San Michele delle Grotte, il ponticello porta alla goccia della figurina sul promontorio.
// Poi su per la Calata San Giovanni Battista e i Gradoni fino a Piazza Pellicciari, dove il mezzo aspetta.
const fv = await page.evaluate(() => {
  const N = window.gravina.network.edges;
  return { ponte: N.find((e) => e.span)?.id, goccia: N.find((e) => e.walk && e.turn && Math.hypot(e.a.e + 73.5, e.a.n + 186) < 3)?.id,
    raccordo: N.find((e) => e.walk && e.name === 'Piazza Giuseppe Pellicciari')?.id };
});
await page.evaluate(() => { const g = window.gravina; g.placeAt(117, -16, [0.25, -1], 0); g.rig.snap(g.driver); g.driver.decision = null; });
w = await guide('to', fv.ponte, 400);
const smCar = await page.evaluate(() => window.gravina.driver.car?.edge.name);
check('Fondovito: giù per la Calata a piedi fino al ponticello, con la scheda di San Michele delle Grotte',
  w.onFoot && w.names.includes('Calata Grotte San Michele') && w.cards.includes('San Michele delle Grotte'), `${w.names.join(', ')} · schede ${w.cards.join(', ')} · il mezzo su ${smCar}`);
w = await guide('to', fv.goccia, 120);
check('oltre il ponticello la figurina gira nella goccia sul promontorio', w.onFoot && !!fv.goccia, `${w.street}`);
w = await guide('to', fv.raccordo, 600);
check('poi su per la Calata San Giovanni Battista e i Gradoni', w.onFoot && w.names.includes('Gradoni San Giovanni Battista') && w.names.includes('Calata San Giovanni Battista'), w.names.join(', '));
w = await guide('loop', null, 200);
check('a Piazza Pellicciari il mezzo aspetta e si riparte', w.back && !w.onFoot && w.speed > 0.5, w.street);

// Blocco N2b: da Via Calderoni a piedi per il passaggio fino alla chiesa di Santa Lucia (OSM w1195336380): si apre la
// scheda, davanti alla chiesa la figurina gira nella goccia, poi si torna al mezzo.
const sl = await page.evaluate(() => {
  const N = window.gravina.network.edges, end = (e) => Math.hypot(e.b.e + 4.5, e.b.n - 107.6) < 3 || Math.hypot(e.a.e + 4.5, e.a.n - 107.6) < 3;
  return { passo: N.find((e) => e.walk && !e.turn && end(e))?.id, goccia: N.find((e) => e.walk && e.turn && end(e))?.id };
});
await page.evaluate(() => { const g = window.gravina; g.placeAt(110, 74, [-1, 0.1], 0); g.rig.snap(g.driver); g.driver.decision = null; });
w = await guide('to', sl.passo, 200);
check('Santa Lucia: da Via Calderoni la figurina scende a piedi sul passaggio', !!sl.passo && w.onFoot && w.street === 'Passaggio pedonale', w.street);
w = await guide('to', sl.goccia, 200);
check('davanti alla chiesa la figurina gira nella goccia, con la scheda di Santa Lucia', !!sl.goccia && w.onFoot && w.cards.includes('Santa Lucia'), `${w.street} · schede ${w.cards.join(', ')}`);
w = await guide('loop', null, 300);
check('poi si torna per il passaggio e si ritrova il mezzo', w.back && !w.onFoot && w.speed > 0.5, w.street);

// Blocco N2b: dalla ringhiera della Cattedrale (belvedere OSM n3348673132) il ponte si vede. Prima del blocco una casa a
// tre piani (in OSM un rudere) lo nascondeva a 16 m: tre raggi dall'occhio (1,6 m) all'impalcato, nessun ostacolo.
const vistaPonte = await page.evaluate(() => {
  const g = window.gravina, T = g.THREE, meshes = [];
  g.scene.traverse((o) => { if (o.isMesh && o.name.startsWith('riquadro')) meshes.push(o); });
  const deck = new T.Box3().setFromObject(g.scene.getObjectByName('ponte-acquedotto')).max.y - 0.3, eye = new T.Vector3(-26.9, g.Terrain.heightAt(-26.9, 19) + 1.6, -19);
  let hits = 0;
  for (const dx of [-12, 0, 12]) {
    const to = new T.Vector3(-24 + dx, deck, -297), dir = to.clone().sub(eye), dist = dir.length();
    hits += new T.Raycaster(eye, dir.normalize(), 0.1, dist - 4).intersectObjects(meshes, false).length;
  }
  return { hits, deck: +deck.toFixed(1), tiles: meshes.length };
});
check('dalla ringhiera della Cattedrale il ponte si vede (nessuna casa sulla linea d’occhio)', vistaPonte.tiles > 20 && vistaPonte.hits === 0, `${vistaPonte.hits} ostacoli, impalcato a ${vistaPonte.deck} m, ${vistaPonte.tiles} riquadri`);

// Vie cieche reali con la goccia (blocco M2): dall'elenco dei luoghi si arriva in auto e si riparte.
for (const [name, at] of [['Casino di Meninni', [1572, -536]], ['Monumento alla Cola Cola', [1893, 102]], ['Fiera di San Giorgio', [-53, 948]]]) {
  await page.keyboard.press('p');
  await page.click(`.poi >> text=${name}`);
  // con SwiftShader, a fine giro, costruire i riquadri del luogo può richiedere qualche secondo
  await page.waitForFunction(() => window.gravina.phase === 'drive', null, { timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(300);
  await until(() => page.evaluate((n) => document.getElementById('card-title').textContent === n, name), 4);
  const a = await page.evaluate(() => { const d = window.gravina.driver; return { phase: window.gravina.phase, odo: d.odometer, onFoot: d.onFoot, e: d.position.x, n: -d.position.z, title: document.getElementById('card-title').textContent }; });
  await advance(60);
  const b = await page.evaluate(() => window.gravina.driver.odometer);
  const dist = Math.hypot(a.e - at[0], a.n - at[1]);
  check(`dall’elenco si arriva in auto a ${name} e si riparte dalla goccia`, a.phase === 'drive' && !a.onFoot && dist < 120 && b - a.odo > 200 && a.title === name,
    `a ${dist.toFixed(0)} m, ${(b - a.odo).toFixed(0)} m in 60 s${a.phase === 'drive' && a.title === name ? '' : `, ${a.phase}, scheda «${a.title}»`}`);
}

await page.reload();
await page.waitForFunction(() => !document.getElementById('btn-start').disabled, null, { timeout: 120000 });
const kept = await page.evaluate(() => document.querySelector('#start-picker .vcard.is-selected')?.dataset.id);
check('alla riapertura resta il mezzo scelto', kept === 'deere', kept);

// Blocco M3: la mongolfiera, quinto mezzo. Decollo da Botromagno, volo, scheda, prima e terza persona,
// pausa, teletrasporto (sul giro e lontano), cambio mezzo e fine del giro con l'auto che riparte dal decollo.
const bal = () => page.evaluate(() => {
  const g = window.gravina, f = g.flight, p = f.position;
  return { mode: g.mode, phase: g.phase, s: f.s, h: p.y - g.Terrain.heightAt(p.x, -p.z), view: g.rig.view, pace: g.driver.pace, e: p.x, n: -p.z,
    title: document.getElementById('card-title').textContent, street: g.driver.edge.name, speed: g.driver.speed, btn: !document.getElementById('btn-view').hidden };
});
const realUntil = async (test, n) => { for (let k = 0; k < n; k++) { if (await test()) return true; await advance(1); await page.waitForTimeout(120); } return test(); };
await page.click('#start-picker .vcard[data-id="balloon"]');
let b = await bal();
check('nella schermata iniziale si sceglie la mongolfiera, a terra a Botromagno', b.mode === 'balloon' && b.h < 1 && Math.hypot(b.e + 379, b.n - 685) < 2);
await page.click('#btn-start');
await page.waitForTimeout(1700);
await advance(20);
b = await bal();
check('decollo: la mongolfiera sale e avanza sul giro', b.phase === 'drive' && b.s > 30 && b.h > 15 && b.btn, `${b.s.toFixed(0)} m del giro, ${b.h.toFixed(0)} m dal suolo`);
const card1 = await until(async () => /Necropoli|Botromagno/.test((await bal()).title), 120, 1);
check('passando sopra la necropoli si apre la scheda', card1, (await bal()).title);
await page.click('#btn-view');
await advance(0.5);
b = await bal();
const eye = await page.evaluate(() => { const g = window.gravina; return g.camera.position.y - g.flight.position.y; });
check('il pulsante passa alla vista dalla cesta', b.view === 'in' && Math.abs(eye - 1.75) < 0.6 && /Vista esterna/.test(await page.textContent('#btn-view')), `occhi a ${eye.toFixed(2)} m`);
await page.click('#btn-view');
await advance(1);
check('…e torna alla vista esterna', (await bal()).view === 'out');
await page.keyboard.press('p');
await advance(3);
const s0 = (await bal()).s;
await advance(2);
b = await bal();
check('in pausa la mongolfiera resta sospesa', b.phase === 'pause' && Math.abs(b.s - s0) < 1.5);
await page.click('.poi >> text=Porta San Michele');
await page.waitForTimeout(900);
await advance(1);
b = await bal();
check('teletrasporto in mongolfiera: al punto del giro più vicino', b.mode === 'balloon' && b.phase === 'drive' && Math.hypot(b.e - 398, b.n + 25) < 120, `a ${Math.hypot(b.e - 398, b.n + 25).toFixed(0)} m`);
await page.keyboard.press('p');
await page.click('.poi >> text=Area Quercus');
await page.waitForTimeout(900);
await advance(1);
b = await bal();
check('i luoghi lontani dal giro si raggiungono con l’ultima auto', b.mode === 'car' && b.phase === 'drive' && /bosco/i.test(b.street) && b.speed > 0, b.street);
await page.evaluate(() => { const g = window.gravina; g.placeAt(300, 0, [1, 0]); g.rig.snap(g.driver); });
await page.keyboard.press('p');
await page.click('#pause-picker .vcard[data-id="balloon"]');
b = await bal();
check('dalla pausa la mongolfiera compare in volo sul giro', b.mode === 'balloon' && b.h > 40, `${b.h.toFixed(0)} m dal suolo`);
await page.click('#pause-picker .vcard[data-id="rs6"]');
await page.keyboard.press('Escape');
await advance(2);
b = await bal();
check('tornando a un’auto si riparte dalla via più vicina', b.mode === 'car' && b.speed > 1, b.street);
await page.keyboard.press('p');
await page.click('#pause-picker .vcard[data-id="balloon"]');
await page.keyboard.press('Escape');
await page.evaluate(() => { const g = window.gravina; g.flight.place(g.Volo.L - 80, true); });
const landed = await realUntil(async () => (await bal()).mode === 'car', 60);
await page.waitForTimeout(800);
await advance(3);
b = await bal();
const dTake = await page.evaluate(() => { const p = window.gravina.driver.position; return Math.hypot(p.x + 379, -p.z - 685); });
check('fine del giro: atterra al decollo e si riparte con l’ultima auto', landed && b.mode === 'car' && b.pace === 1.1 && b.speed > 0.5 && dTake < 500, `${b.street}, a ${dTake.toFixed(0)} m dal decollo`);

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
