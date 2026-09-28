/**
 * Apre index.html in Chromium headless per le prove.
 * - Three.js viene servito da node_modules (niente rete necessaria per il CDN).
 * - I Google Fonts vengono ignorati (restano i font di ripiego).
 * - WebGL gira via SwiftShader: più lento di una GPU vera, ma affidabile.
 * Con `gpu: true` usa la GPU vera del computer (per misurare gli fps).
 * Percorso di Chromium personalizzabile con la variabile CHROMIUM_PATH.
 */
import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, '../..');
const THREE_DIR = path.join(HERE, 'node_modules/three');
export const SHOTS = path.join(HERE, 'shots');
fs.mkdirSync(SHOTS, { recursive: true });

export async function open({ w = 1280, h = 720, mobile = false, landscape = false, gpu = false, dpr, init } = {}) {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || undefined,
    channel: gpu ? 'chromium' : undefined,   // il Chromium completo: la "headless shell" non usa la GPU
    args: gpu ? ['--ignore-gpu-blocklist', '--enable-precise-memory-info']
      : ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  const phone = landscape ? { width: 844, height: 390 } : { width: 390, height: 844 };
  const ctx = await browser.newContext(mobile
    ? { viewport: phone, deviceScaleFactor: dpr ?? 2, hasTouch: true, isMobile: true }
    : { viewport: { width: w, height: h }, deviceScaleFactor: dpr ?? 1 });
  const page = await ctx.newPage();
  if (init) await page.addInitScript(init);
  const logs = [];
  page.on('console', (m) => logs.push(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}\n${e.stack}`));
  await page.route('https://cdn.jsdelivr.net/npm/three@0.170.0/**', (r) =>
    r.fulfill({ path: path.join(THREE_DIR, r.request().url().split('three@0.170.0/')[1]), contentType: 'application/javascript' }));
  await page.route('https://fonts.googleapis.com/**', (r) => r.fulfill({ body: '', contentType: 'text/css' }));
  await page.route('https://fonts.gstatic.com/**', (r) => r.abort());
  await page.route('http://local/**', (r) => r.fulfill({ path: path.join(ROOT, new URL(r.request().url()).pathname) }));
  await page.goto('http://local/index.html?debug');
  await page.waitForFunction(() => !document.getElementById('btn-start').disabled
    || /Impossibile/.test(document.getElementById('status').textContent), null, { timeout: 120000 });
  return { browser, page, logs };
}

/** Stampa gli errori della pagina (ignorando gli avvisi innocui). */
export function report(logs) {
  const bad = logs.filter((l) => /error|pageerror|\[warning\].*Rete|Monumenti/i.test(l));
  console.log(bad.length ? bad.join('\n') : 'Nessun errore in console.');
  return bad.length === 0;
}
