/**
 * Rumore dei motori (blocco 4.4): per ogni mezzo una guida simulata (minimo, partenza, crociera, a tavoletta fino alla velocità massima,
 * acceleratore, rilascio, frenata, minimo) resa senza altoparlanti (OfflineAudioContext) e salvata in
 * shots/motore-<mezzo>.wav da ascoltare. Controlla anche che non ci siano valori anomali né saturazione,
 * e stampa giri, marce e carico lungo la prova.
 * Uso: node motori.mjs [mezzo…]
 */
import fs from 'fs';
import path from 'path';
import { open, report, SHOTS, ROOT } from './common.mjs';

const ids = process.argv.slice(2).length ? process.argv.slice(2) : ['panda', 'rs6', 'huracan', 'deere'];
const { browser, page, logs } = await open({ w: 800, h: 600 });
// l'AudioWorklet vuole una pagina sicura (https o localhost): la stessa pagina servita come https://local
await page.route('https://local/**', (r) => r.fulfill({ path: path.join(ROOT, new URL(r.request().url()).pathname) }));
await page.goto(`https://local/${process.env.GRAVINA_HTML ?? 'index.html'}?debug`);
await page.waitForFunction(() => window.gravina?.EngineAudio, null, { timeout: 120000 });
let ok = true;
for (const id of ids) {
  const r = await page.evaluate(async (id) => {
    const { left, right, sr, log } = await window.gravina.EngineAudio.render(id);
    let peak = 0, sum = 0, bad = 0;
    const pcm = new Int16Array(left.length * 2);
    for (let i = 0; i < left.length; i++) {
      for (const [k, v] of [[0, left[i]], [1, right[i]]]) {
        if (!Number.isFinite(v)) { bad++; continue; }
        peak = Math.max(peak, Math.abs(v)); sum += v * v;
        pcm[i * 2 + k] = Math.max(-32767, Math.min(32767, Math.round(v * 32767)));
      }
    }
    let bin = '';
    const u8 = new Uint8Array(pcm.buffer);
    for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode(...u8.subarray(i, i + 0x8000));
    return { sr, peak, rms: Math.sqrt(sum / (left.length * 2)), bad, log, data: btoa(bin) };
  }, id);
  const pcm = Buffer.from(r.data, 'base64'), h = Buffer.alloc(44);
  h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length, 4); h.write('WAVE', 8); h.write('fmt ', 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22); h.writeUInt32LE(r.sr, 24);
  h.writeUInt32LE(r.sr * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length, 40);
  fs.writeFileSync(`${SHOTS}/motore-${id}.wav`, Buffer.concat([h, pcm]));
  const good = r.bad === 0 && r.peak < 0.98 && r.rms > 0.005;
  ok &&= good;
  console.log(`${good ? '✓' : '✗'} ${id}: picco ${r.peak.toFixed(2)}, rms ${(20 * Math.log10(r.rms)).toFixed(1)} dB${r.bad ? `, ${r.bad} valori anomali` : ''} · shots/motore-${id}.wav`);
  console.log('   [s, km/h, giri, marcia, carico]', r.log.map((x) => x.join(' ')).join(' | '));
}
// Dal vivo: si parte, il mezzo va, il motore gira (worklet caricato, giri e marce che cambiano)
await page.waitForFunction(() => !document.getElementById('btn-start').disabled, null, { timeout: 120000 });
await page.click('#start-picker .vcard[data-id="rs6"]');
await page.click('#btn-start');
const seen = [];
for (let k = 0; k < 14; k++) { await page.waitForTimeout(700); seen.push(await page.evaluate(() => { const g = window.gravina, st = g.EngineAudio.state; return st && { ...st, kmh: Math.round(g.driver.speed * 3.6) }; })); }
const live = seen.filter(Boolean), giri = live.map((x) => x.rpm);
const vivo = live.length > 4 && Math.max(...giri) > Math.min(...giri) + 200;
ok &&= vivo;
console.log(`${vivo ? '✓' : '✗'} dal vivo (Audi RS Q8): ${live.map((x) => `${x.kmh} km/h ${x.rpm} giri (${x.gear}ª)`).join(' · ')}`);
ok = report(logs) && ok;
await browser.close();
process.exit(ok ? 0 : 1);
