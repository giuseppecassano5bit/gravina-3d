/**
 * Velocità massime (blocco 4.4): ogni mezzo, con l'acceleratore tenuto premuto, sulla strada fuori città più
 * lunga e in centro storico. Stampa la velocità massima raggiunta, il limite della via, i tempi e controlla
 * che agli incroci con la scelta il mezzo arrivi lento (sotto i 25 km/h) e che non superi mai il limite.
 * Uso: node velocita.mjs
 */
import { open, report } from './common.mjs';

const { browser, page, logs } = await open({ w: 800, h: 600 });
await page.click('#btn-start');
await page.evaluate(() => window.gravina.advance(2));
let ok = true;
for (const id of ['panda', 'rs6', 'huracan', 'deere']) {
  for (const where of ['fuori città', 'centro storico']) {
    const r = await page.evaluate(([id, where]) => {
      const g = window.gravina, d = g.driver, N = g.network;
      g.useVehicle(id);
      // la via fuori città più lunga, oppure Via Vittorio Veneto nel centro storico
      const edge = where === 'fuori città'
        ? N.edges.filter((e) => !e.urban && !e.walk && !e.turn && !e.bridge && !e.dirt && e.cls <= 1).sort((a, b) => b.length - a.length)[0]
        : N.edges.filter((e) => !e.walk && !e.turn && !e.bridge && d.constructor.limit(e) < 31 / 3.6).sort((a, b) => b.length - a.length)[0];
      d.place(edge, 1, 0);
      d.running = true; d.speed = 0; d.boosting = true;
      let vmax = 0, t100 = null, over = 0, fastJunction = 0, t = 0;
      const dt = 1 / 30;
      for (; t < 40; t += dt) {
        const before = d.decision?.options.length > 1 ? d.decision : null;
        g.advance(dt);
        const v = d.speed * 3.6;
        vmax = Math.max(vmax, v);
        if (t100 === null && v >= Math.min(100, d.top * 3.6 - 1)) t100 = +t.toFixed(1);
        // mai oltre il limite della via in cui si trova (né oltre la massima del mezzo); la crociera vale sempre
        const lim = Math.max(Math.min(d.top, d.constructor.limit(d.edge)), g.CONFIG.drive.cruiseSpeed * d.pace) * 3.6;
        if (!d.edge.turn && v > lim + 3) over++;
        if (before && d.decision !== before && v > 25) fastJunction++;   // passato l'incrocio troppo forte
        if (d.decision?.options.length > 1) d.decision.selected = 0;
      }
      d.boosting = false;
      return { via: edge.name, lunga: Math.round(edge.length), vmax: Math.round(vmax), top: Math.round(d.top * 3.6), t100, over, fastJunction };
    }, [id, where]);
    const good = r.over === 0 && r.fastJunction === 0;
    ok &&= good;
    console.log(`${good ? '✓' : '✗'} ${id.padEnd(8)} ${where.padEnd(15)} ${r.via} (${r.lunga} m): massima raggiunta ${r.vmax} km/h su ${r.top}${r.t100 !== null ? `, a ${Math.min(100, r.top)} km/h in ${r.t100} s` : ''}${r.over ? `, ${r.over} volte oltre` : ''}${r.fastJunction ? `, ${r.fastJunction} incroci troppo forte` : ''}`);
  }
}
ok = report(logs) && ok;
await browser.close();
process.exit(ok ? 0 : 1);
