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
    return { back, walked: Math.round(walked), names: [...names], cards: [...cards], street: d.edge.name, onFoot: d.onFoot, sitting: !!d.sitting, speed: d.speed,
      ids: [...visits.keys()].map((e) => e.id) };
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
const sostaEdge = await page.evaluate(() => window.gravina.network.edges.find((e) => e.soste?.some((s) => s.sosta.lm === 'caduti'))?.id);
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

// Blocco N4: dallo sterrato del Casino di Meninni a piedi per il cancello e il giardino dei pini, attorno al Casino fino
// alla goccia della figurina nella radura dietro (con la scheda), poi di nuovo al mezzo che aspetta nello spiazzo.
const mg = await page.evaluate(() => {
  const N = window.gravina.network.edges, end = (e) => Math.hypot(e.b.e - 1590, e.b.n + 572) < 3 || Math.hypot(e.a.e - 1590, e.a.n + 572) < 3;
  return N.find((e) => e.walk && e.turn && end(e))?.id;
});
await page.evaluate(() => { const g = window.gravina; g.placeAt(1437, -468, [1, 0.1], 0); g.rig.snap(g.driver); g.driver.decision = null; });
w = await guide('to', mg, 400);
check('Casino di Meninni: dallo spiazzo a piedi per il cancello e il giardino fino alla goccia dietro il Casino, con la scheda',
  !!mg && w.onFoot && w.names.includes('Giardino del Casino di Meninni') && w.cards.includes('Casino di Meninni'), `${w.street} · schede ${w.cards.join(', ')}`);
w = await guide('loop', null, 400);
check('poi si torna al mezzo nello spiazzo e si riparte', w.back && !w.onFoot && w.speed > 0.5, w.street);

// Blocco N5b: in auto sulla SP201 oltre lo sterrato del Casino di Meninni, giù fino al bivio e su via Guardialto Alto fino al
// piazzale dei campi di Sportland: il mezzo gira nella goccia (fuori dal recinto) e torna indietro sulla SP201.
const sp = await page.evaluate(() => {
  const N = window.gravina.network.edges, near = (x) => Math.hypot(x.e - 1548, x.n + 825) < 6 || Math.hypot(x.e - 1559, x.n + 816) < 6;
  return N.find((e) => e.turn && !e.walk && /Guardialto Alto/.test(e.name ?? '') && (near(e.a) || near(e.b)))?.id;
});
await page.evaluate(() => { const g = window.gravina; g.placeAt(1480, -548, [0.55, -0.83], 0); g.rig.snap(g.driver); g.driver.decision = null; });
w = await guide('to', sp, 120);
const spBack = await page.evaluate(() => { const d = window.gravina.driver; return { name: d.edge.name, n: -d.position.z }; });
check('Sportland: in auto sulla SP201 fino al piazzale dei campi, si gira nella goccia e si torna indietro',
  !!sp && w.ids.includes(sp) && !w.onFoot && w.speed > 0.5, `goccia ${sp} ${w.ids.includes(sp) ? 'fatta' : 'mancata'} · ${spBack.name} a nord ${spBack.n.toFixed(0)}`);
await page.keyboard.press('p');
check('nell’elenco dei luoghi c’è il Casino Scacchi (solo l’etichetta)', await page.isVisible('.poi >> text=Casino Scacchi'), '');
await page.keyboard.press('Escape');

// Blocco N5: dall'elenco dei luoghi a Capotenda (su Via Madonna della Stella, verso la goccia), poi a piedi sul sentiero del
// pianoro (la scheda), giù fino al guado: sui sassi sopra l'acqua e alla goccia della figurina sull'altra sponda; poi al mezzo.
await page.keyboard.press('p');
await page.click('.poi >> text=Capotenda');
await page.waitForFunction(() => window.gravina.phase === 'drive', null, { timeout: 20000 }).catch(() => {});
const cp = await page.evaluate(() => { const d = window.gravina.driver; return { phase: window.gravina.phase, e: d.position.x, n: -d.position.z, street: d.edge.name }; });
check('dall’elenco si arriva a Capotenda su Via Madonna della Stella', cp.phase === 'drive' && cp.street === 'Via Madonna della Stella' && Math.hypot(cp.e + 737, cp.n - 862) < 60,
  `${cp.street} a [${cp.e.toFixed(0)}, ${cp.n.toFixed(0)}]`);
const gu = await page.evaluate(() => {
  const g = window.gravina, N = g.network.edges, end = (e) => Math.hypot(e.b.e + 550.5, e.b.n - 1294.2) < 3 || Math.hypot(e.a.e + 550.5, e.a.n - 1294.2) < 3;
  const passo = N.find((e) => e.wet), water = g.Ravine.bed(...g.GOLA.guado).y + 0.35;
  const S = passo?.samples, sopra = !!passo && [...passo.wet].every((k, i) => !k || S[i * 3 + 1] > water + 0.1);
  return { passo: passo?.id, goccia: N.find((e) => e.walk && e.turn && end(e))?.id, sopra, sassi: g.Capotenda.count.sassi };
});
const cw1 = await guide('to', await nearEdge('Sentiero di Capotenda', [-660, 880]), 400);
const cw2 = await guide('to', gu.goccia, 600);
check('Capotenda: a piedi sul sentiero del pianoro, con la scheda', cw1.onFoot && [...cw1.cards, ...cw2.cards].includes('Capotenda'), `${cw1.street} · schede ${[...cw1.cards, ...cw2.cards].join(', ')}`);
check('giù fino al guado: sui sassi sopra l’acqua e alla goccia della figurina sull’altra sponda', !!gu.goccia && cw2.onFoot && cw2.names.includes('Guado di Capotenda') && gu.sopra && gu.sassi >= 6,
  `${cw2.names.join(', ')} · ${gu.sassi} sassi${gu.sopra ? '' : ', il sentiero va sott’acqua'}`);
const carEdge = await page.evaluate(() => window.gravina.driver.car?.edge.id);
const cw3 = await guide('to', carEdge, 600);             // si ferma appena la figurina arriva sulla via del mezzo
await advance(6);
const cafter = await foot();
check('poi si risale per i sentieri e si ritrova il mezzo', cw3.onFoot && !cafter.onFoot && cafter.speed > 0.5, `${cafter.street}, ${cafter.speed.toFixed(1)} m/s`);

// Blocco N5c: dall'elenco dei luoghi a Hortus (arriva su Via San Vito Vecchio all'imbocco di Via Leopardi),
// poi a piedi per Via Leopardi e nel giardino di Hortus fino alla panchina panoramica: si siede, si apre
// la scheda, il pulsante «Riprendi il percorso» fa rialzare la figurina, che completa l'anello e torna al mezzo.
await page.keyboard.press('p');
await page.click('.poi >> text=Hortus');
await page.waitForFunction(() => window.gravina.phase === 'drive', null, { timeout: 20000 }).catch(() => {});
const hPlace = await page.evaluate(() => {
  const d = window.gravina.driver;
  return { phase: window.gravina.phase, e: d.position.x, n: -d.position.z, street: d.edge.name };
});
check('dall’elenco si arriva a Hortus su Via San Vito Vecchio', hPlace.phase === 'drive' && hPlace.street === 'Via San Vito Vecchio' && Math.hypot(hPlace.e - 27, hPlace.n + 245) < 30,
  `${hPlace.street} a [${hPlace.e.toFixed(0)}, ${hPlace.n.toFixed(0)}]`);

const hortusBenchEdge = await page.evaluate(() => {
  const e = window.gravina.network.edges.find((x) => x.soste?.some((s) => s.sosta.lm === 'hortus'));
  return e?.id;
});
const hw1 = await guide('to', hortusBenchEdge, 400);
const hbench = await page.evaluate(() => ({
  card: document.getElementById('card').classList.contains('is-visible'),
  title: document.getElementById('card-title').textContent,
  btn: !document.getElementById('btn-bench').hidden,
  sitting: !!window.gravina.driver.sitting,
  car: window.gravina.driver.car?.edge.name,
}));
check('Hortus: a piedi nel giardino e sulla panchina panoramica con la scheda', hw1.sitting && hbench.sitting && hbench.card && /Hortus/i.test(hbench.title),
  `${hbench.title} · seduti: ${hbench.sitting}`);

await advance(5.5);
const hbenchBtn = await page.isVisible('#btn-bench');
const hbenchText = hbenchBtn ? await page.textContent('#btn-bench') : '';
check('dopo circa 5 s compare «Riprendi il percorso»', hbenchBtn && /riprendi il percorso/i.test(hbenchText), hbenchText.trim());

if (hbenchBtn) await page.click('#btn-bench');
await page.waitForTimeout(300);
const hStood = await page.evaluate(() => !window.gravina.driver.sitting && window.gravina.driver.onFoot);
check('il pulsante fa rialzare la figurina e prosegue a piedi', hStood);

const hCarEdge = await page.evaluate(() => window.gravina.driver.car?.edge.id);
const hw2 = await guide('to', hCarEdge, 500);
await advance(6);
const hafter = await foot();
check('completa l’anello nel giardino e risale sul mezzo su Via San Vito Vecchio', hw2.onFoot && !hafter.onFoot && hafter.speed > 0.5,
  `${hafter.street}, ${hafter.speed.toFixed(1)} m/s`);


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

// Blocco N4b: le villette del triangolo Via Montale – Via Quasimodo – Via Bertocchi (tipo 13 della città) coi livelli da Street
// View (da 3 a 5: 3 m per piano più 1 m di parapetto), le unità della schiera, i coppi, i balconi e i giardinetti (preparati dopo
// «Parti», col primo riquadro che li tocca: a questo punto della prova i riquadri della città sono tutti costruiti).
const villette = await page.evaluate(() => {
  const g = window.gravina, V = g.DATA.city().filter((b) => b.kind === 13), units = V.flatMap((b) => b.vil?.units ?? []).filter(Boolean);
  const built = g.Tiles.list.filter((t) => t.e0 < 830 && t.e1 > 520 && t.n0 < -320 && t.n1 > -540).every((t) => t.built);
  return { n: V.length, hMin: Math.min(...V.map((b) => b.height)), hMax: Math.max(...V.map((b) => b.height)), units: units.length,
    coppi: units.filter((u) => u.coppi).length, built, ...g.Villette.count };
});
check('le villette del Liceo Tarantino: livelli da Street View, unità, coppi, balconi e giardinetti', villette.n === 16 && villette.hMin >= 10 && villette.hMax <= 16
  && villette.units >= 50 && villette.coppi >= 8 && villette.built && villette.balconi > 100 && villette.giardini > 50,
  `${villette.n} sagome, ${villette.hMin}–${villette.hMax} m, ${villette.units} unità (${villette.coppi} coi coppi), ${villette.balconi} balconi, ${villette.giardini} giardinetti`);

// Vie cieche reali con la goccia (blocco M2): dall'elenco dei luoghi si arriva in auto e si riparte.
// Blocco N4: il Casino di Meninni si raggiunge con lo sterrato nuovo, fino allo spiazzo davanti al cancello (circa 140 m dal Casino).
for (const [name, at] of [['Casino di Meninni', [1451, -463]], ['Monumento alla Cola Cola', [1893, 102]], ['Fiera di San Giorgio', [-53, 948]]]) {
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

// Blocco N8: Cartolina e Giro guidato dei monumenti
await page.evaluate(() => { const g = window.gravina; g.placeAt(300, 0, [1, 0]); g.rig.snap(g.driver); document.activeElement?.blur?.(); });
await page.waitForTimeout(300);

// 1. Cartolina: tasto C e notifica toast
await page.keyboard.press('c');
const toastEl = await page.waitForSelector('#toast.is-visible', { timeout: 4000 });
const toastText = (await toastEl?.textContent()) || '';
check('il tasto C scatta la cartolina e mostra il toast', !!toastEl && /cartolina/i.test(toastText), toastText);

// 2. Giro guidato dei monumenti: 14 tappe, HUD dedicato, salto ed uscita
const stopsCount = await page.evaluate(() => window.gravina.TOUR_STOPS?.length);
check('il giro guidato ha 14 tappe definite', stopsCount === 14, `${stopsCount} tappe`);

await page.keyboard.press('p');
await page.click('#btn-pause-tour');
await page.waitForTimeout(400);
let tourState = await page.evaluate(() => {
  const d = window.gravina.driver;
  const h = document.getElementById('tour-hud');
  const info = document.getElementById('tour-hud-info');
  return {
    active: d.tour?.active,
    index: d.tour?.index,
    hudVisible: h && !h.hidden,
    hudInfo: info?.textContent,
  };
});
check('il giro guidato si avvia dalla pausa col banner HUD', tourState.active && tourState.hudVisible && /Tappa 1\/14/i.test(tourState.hudInfo), tourState.hudInfo);

await page.click('#btn-tour-skip');
await page.waitForTimeout(300);
tourState = await page.evaluate(() => {
  const d = window.gravina.driver;
  const info = document.getElementById('tour-hud-info');
  return { active: d.tour?.active, index: d.tour?.index, hudInfo: info?.textContent };
});
check('il pulsante «Salta tappa» avanza alla tappa 2', tourState.active && tourState.index === 1 && /Tappa 2\/14/i.test(tourState.hudInfo), tourState.hudInfo);

await page.click('#btn-tour-exit');
await page.waitForTimeout(300);
tourState = await page.evaluate(() => {
  const d = window.gravina.driver;
  const h = document.getElementById('tour-hud');
  return { active: !!d.tour?.active, hudVisible: h && !h.hidden };
});
check('il pulsante «Esci dal giro» interrompe il tour e chiude l’HUD', !tourState.active && !tourState.hudVisible);

// Blocco 4.2: audio procedurale motore
const engineCheck = await page.evaluate(async () => {
  const g = window.gravina;
  const initOn = g.EngineAudio.enabled;
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'v' }));
  const offWithV = !g.EngineAudio.enabled;
  const btn = document.getElementById('btn-engine');
  btn.click();
  const onWithBtn = g.EngineAudio.enabled;
  const slider = document.getElementById('engine-vol');
  slider.value = '0.4';
  slider.dispatchEvent(new Event('input'));
  const volOk = Math.abs(g.EngineAudio.volume - 0.4) < 0.01;
  return { initOn, offWithV, onWithBtn, volOk };
});
check('motore: tasto V spegne, pulsante HUD riaccende e volume regolabile', engineCheck.initOn && engineCheck.offWithV && engineCheck.onWithBtn && engineCheck.volOk);

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
