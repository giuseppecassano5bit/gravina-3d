/**
 * Misure di prestazioni, da lanciare prima e dopo ogni modifica pesante (piano della fase 3.4,
 * sezione 3): peso di index.html, tempo di costruzione, memoria JavaScript, triangoli e draw
 * call della scena e di ogni fotogramma, fps. Usa la GPU vera del computer (Chromium headless).
 *
 * Profili: "pc" (1280×720 a 2×) e "telefono" (390×844 a 3×, touch: profilo leggero).
 * Viste: partenza (vetrina sul ponte), centro (inseguimento in Piazza Benedetto XIII),
 * scacchi (inseguimento da Piazza Scacchi verso la città moderna), pausa (vista dall'alto),
 * panoramica (camera alta sopra la città), alta (camera 120 m sopra il centro storico, inclinata
 * verso la città: la vista della futura mongolfiera).
 * I riquadri lontani usano la versione semplificata (livelli di dettaglio, sezione 6e).
 *
 * Uso: node prestazioni.mjs [etichetta]   → tabella in console e shots/prestazioni-<etichetta>.json
 */
import fs from 'fs';
import zlib from 'zlib';
import path from 'path';
import { open, report, ROOT, SHOTS } from './common.mjs';

const label = process.argv[2] ?? 'misura';
const html = fs.readFileSync(path.join(ROOT, 'index.html'));
const file = { kb: Math.round(html.length / 1024), gzipKb: Math.round(zlib.gzipSync(html, { level: 9 }).length / 1024) };

/** Nella pagina: registra i "long task" (blocchi del thread principale oltre 50 ms). */
const init = () => {
  window.__lunghi = [];
  try { new PerformanceObserver((l) => window.__lunghi.push(...l.getEntries().map((e) => [e.startTime, e.duration]))).observe({ type: 'longtask', buffered: true }); } catch { /* non supportato */ }
};

const VIEWS = {
  partenza: null,
  centro: { at: [40, -12], heading: [1, 0] },
  scacchi: { at: [415, 0], heading: [1, 0] },
  pausa: { at: [415, 0], heading: [1, 0], pause: true },
  panoramica: { camera: [950, -750, 320], look: [350, 150, 0] },
  alta: { camera: [-60, -120, 120], look: [400, 300, 0], above: true },   // quota sopra il suolo
};

async function measure(profile) {
  const t0 = Date.now();
  const { browser, page, logs } = await open(profile === 'telefono' ? { mobile: true, dpr: 3, gpu: true, init } : { dpr: 2, gpu: true, init });
  const openMs = Date.now() - t0;
  // Costruzione: segni di tempo messi da index.html (se ci sono), altrimenti il momento in cui "Parti" si abilita.
  const build = await page.evaluate(async () => {
    const mark = (n) => performance.getEntriesByName(n)[0]?.startTime ?? null;
    const t = performance.now();
    for (let k = 0; k < 600 && mark('gravina:pronto') !== null && mark('gravina:completo') === null; k++) await new Promise((r) => setTimeout(r, 50));
    return { pronto: mark('gravina:pronto') ?? t, completo: mark('gravina:completo') ?? mark('gravina:pronto') ?? t, inizio: mark('gravina:inizio') };
  });
  const gpuName = await page.evaluate(() => {
    const gl = window.gravina.renderer.getContext(), ext = gl.getExtension('WEBGL_debug_renderer_info');
    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  });

  // Triangoli di tutta la scena, per strato (figli diretti della scena).
  const scene = await page.evaluate(() => {
    const g = window.gravina, layers = {};
    let total = 0, meshes = 0;
    const tris = (o) => {
      if (!o.isMesh || !o.geometry) return 0;
      const geo = o.geometry, n = (geo.index ? geo.index.count : geo.attributes.position.count) / 3;
      return n * (o.isInstancedMesh ? o.count : 1);
    };
    for (const child of g.scene.children) {
      let t = 0;
      child.traverse((o) => { if (o.visible) { const k = tris(o); if (k) { t += k; meshes++; } } });
      if (!t) continue;
      const name = child.name || child.type;
      layers[name] = (layers[name] ?? 0) + t;
      total += t;
    }
    return { total: Math.round(total), meshes, layers: Object.fromEntries(Object.entries(layers).map(([k, v]) => [k, Math.round(v)]).sort((a, b) => b[1] - a[1])), tiles: { ...g.Tiles.stats } };
  });

  const views = {};
  await page.click('#btn-start');
  for (const [name, v] of Object.entries(VIEWS)) {
    await page.evaluate((v) => {
      const g = window.gravina;
      if (g.phase === 'pause') g.resume();
      if (!v) return;
      if (v.at) { g.placeAt(v.at[0], v.at[1], v.heading); g.driver.start(); g.rig.snap(g.driver); g.advance(1.5); }
      if (v.pause) g.pause();
      if (v.camera) {
        g.rig.mode = 'free';
        const y = v.camera[2] + (v.above ? g.Terrain.heightAt(v.camera[0], v.camera[1]) : 0);
        const ly = v.look[2] + (v.above ? g.Terrain.heightAt(v.look[0], v.look[1]) : 0);
        g.camera.position.set(v.camera[0], y, -v.camera[1]);
        g.camera.lookAt(v.look[0], ly, -v.look[1]);
      }
    }, v);
    // fps reali (la pagina disegna da sola con la GPU), poi triangoli e draw call del fotogramma più pesante.
    const r = await page.evaluate(async () => {
      const g = window.gravina, info = g.renderer.info.render, R = g.renderer;
      await new Promise((res) => setTimeout(res, 1500));
      // tempo di CPU di ogni renderer.render() (culling, stato, draw call): la GPU non ha un tetto a 60 fps
      const render = R.render, cpu = [];
      R.render = function (...a) { const t = performance.now(); render.apply(this, a); cpu.push(performance.now() - t); };
      let frames = 0, worst = 0, last = performance.now();
      const t0 = last;
      let tri = 0, calls = 0;
      await new Promise((res) => {
        const tick = () => {
          const now = performance.now();
          worst = Math.max(worst, now - last); last = now; frames++;
          tri = Math.max(tri, info.triangles); calls = Math.max(calls, info.calls);
          if (now - t0 < 3000) requestAnimationFrame(tick); else res();
        };
        requestAnimationFrame(tick);
      });
      R.render = render;
      cpu.sort((a, b) => a - b);
      return { fps: Math.round(frames / ((last - t0) / 1000)), peggiore: Math.round(worst), cpuMs: +cpu[Math.floor(cpu.length / 2)].toFixed(2), triangoli: tri, draw: calls };
    });
    views[name] = r;
  }
  const memory = await page.evaluate(() => Math.round((performance.memory?.usedJSHeapSize ?? 0) / 1048576));
  const longTasks = await page.evaluate(() => (window.__lunghi ?? []).map(([s, d]) => [Math.round(s), Math.round(d)]));
  const ok = report(logs);
  await browser.close();
  return { profile, gpu: gpuName, openMs, build: Object.fromEntries(Object.entries(build).map(([k, v]) => [k, v === null ? null : Math.round(v)])), memoryMb: memory, scene, views, longTasks: longTasks.filter(([s]) => s > build.pronto).sort((a, b) => b[1] - a[1]).slice(0, 5), ok };
}

const out = { label, date: new Date().toISOString(), file, profiles: [] };
for (const p of ['pc', 'telefono']) out.profiles.push(await measure(p));

console.log(`\nPrestazioni · ${label} · index.html ${file.kb} KB (${file.gzipKb} KB compresso)`);
for (const p of out.profiles) {
  console.log(`\n[${p.profile}] ${p.gpu}`);
  console.log(`  pronto (Parti) ${p.build.pronto} ms dall'apertura (${p.build.pronto - p.build.inizio} ms di costruzione) · completo ${p.build.completo} ms · memoria JS ${p.memoryMb} MB · triangoli nella scena ${p.scene.total} (${p.scene.meshes} mesh)`);
  console.log(`  strati: ${Object.entries(p.scene.layers).map(([k, v]) => `${k} ${Math.round(v / 1000)}k`).join(', ')}`);
  if (p.scene.tiles) console.log(`  nei riquadri: ${Object.entries(p.scene.tiles).map(([k, v]) => `${k} ${Math.round(v / 1000)}k`).join(', ')}`);
  for (const [v, r] of Object.entries(p.views)) console.log(`  ${v.padEnd(11)} ${String(r.fps).padStart(3)} fps (fotogramma peggiore ${r.peggiore} ms, CPU ${r.cpuMs} ms) · ${String(r.triangoli).padStart(7)} triangoli · ${r.draw} draw call`);
  if (p.longTasks.length) console.log(`  blocchi dopo "Parti" (inizio ms, durata ms): ${p.longTasks.map(([s, d]) => `${s}+${d}`).join(' ')}`);
}
fs.writeFileSync(path.join(SHOTS, `prestazioni-${label}.json`), JSON.stringify(out, null, 2));
process.exit(out.profiles.every((p) => p.ok) ? 0 : 1);
