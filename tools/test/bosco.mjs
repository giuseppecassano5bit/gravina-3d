/**
 * Suoni del bosco (blocco 4.6): resi senza altoparlanti (OfflineAudioContext) e salvati da ascoltare in
 *  - shots/bosco-passeggiata.wav: 90 s di bosco come dal vivo (i versi rari più fitti, così si sentono tutti);
 *  - shots/bosco-versi.wav: ogni specie una volta, in fila (l'elenco coi secondi lo stampa qui sotto);
 *  - shots/passi.wav: i passi della figurina su pietra e su terra, camminando e di corsa.
 * Controlla anche che non ci siano valori anomali né saturazione (picco e rms dal vivo; nel file il volume è alzato).
 * Uso: node bosco.mjs
 */
import fs from 'fs';
import { open, report, SHOTS } from './common.mjs';

const { browser, page, logs } = await open({ w: 800, h: 600 });
let ok = true;
for (const [mode, seconds] of [['passeggiata', 90], ['versi', 66], ['passi', 0]]) {
  const r = await page.evaluate(async ([mode, seconds]) => {
    const { left, right, sr, log } = mode === 'passi' ? await window.gravina.Passi.render() : await window.gravina.ForestSound.render(seconds, mode);
    let peak = 0, sum = 0, bad = 0;
    for (const ch of [left, right]) for (const v of ch) { if (!Number.isFinite(v)) bad++; else { peak = Math.max(peak, Math.abs(v)); sum += v * v; } }
    // nel file il volume si alza fino a un picco di 0,7, per ascoltarlo comodamente (dal vivo resta com'è)
    const gain = peak > 0 ? 0.7 / peak : 1, pcm = new Int16Array(left.length * 2);
    for (let i = 0; i < left.length; i++) for (const [k, v] of [[0, left[i]], [1, right[i]]]) pcm[i * 2 + k] = Number.isFinite(v) ? Math.round(v * gain * 32767) : 0;
    let bin = '';
    const u8 = new Uint8Array(pcm.buffer);
    for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode(...u8.subarray(i, i + 0x8000));
    return { sr, peak, rms: Math.sqrt(sum / (left.length * 2)), bad, log, data: btoa(bin) };
  }, [mode, seconds]);
  const pcm = Buffer.from(r.data, 'base64'), h = Buffer.alloc(44);
  h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length, 4); h.write('WAVE', 8); h.write('fmt ', 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22); h.writeUInt32LE(r.sr, 24);
  h.writeUInt32LE(r.sr * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length, 40);
  const file = mode === 'passi' ? 'passi.wav' : `bosco-${mode}.wav`;
  fs.writeFileSync(`${SHOTS}/${file}`, Buffer.concat([h, pcm]));
  const good = r.bad === 0 && r.peak < 0.98 && r.rms > 0.0005;
  ok &&= good;
  console.log(`${good ? '✓' : '✗'} ${mode}: picco ${r.peak.toFixed(2)}, rms ${(20 * Math.log10(r.rms)).toFixed(1)} dB${r.bad ? `, ${r.bad} valori anomali` : ''} · shots/${file}`);
  console.log('   ' + r.log.map(([t, k]) => `${t}s ${k}`).join(' · '));
}
ok = report(logs) && ok;
await browser.close();
process.exit(ok ? 0 : 1);
