/**
 * Valuta un'espressione JavaScript nella pagina (sviluppo), con `g` = window.gravina.
 * Uso: node valuta.mjs "g.Terrain.heightAt(0, 0)"
 */
import { open, report } from './common.mjs';

const { browser, page, logs } = await open();
const out = await page.evaluate((src) => {
  const g = window.gravina;
  const r = new Function('g', `return (${src});`)(g);
  return JSON.stringify(r, (k, v) => (typeof v === 'number' ? Math.round(v * 100) / 100 : v), 1);
}, process.argv[2]);
console.log(out);
report(logs);
await browser.close();
