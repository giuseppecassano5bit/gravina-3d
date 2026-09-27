# Prove automatiche

```bash
cd tools/test
npm install
npm run simula          # un'ora di guida simulata: nessun blocco, nessun vicolo cieco, nessun errore
npm run interazioni     # come un visitatore: mezzo, partenza, pausa, minimappa, teletrasporto, cambio mezzo
npm run foto            # screenshot delle scene principali in tools/test/shots/
node foto.mjs mobile        # le stesse scene su un telefono in verticale
node foto.mjs orizzontale   # e in orizzontale
```

`simula` controlla anche che nessun dettaglio 3D (portali, campanile, scalinate, lanterne,
parapetti…) stia sulla carreggiata all'altezza del mezzo: la voce `dettaglisullastrada` deve
restare vuota.

Due strumenti per lo sviluppo:

```bash
# inquadrature libere: nome, poi gruppi di sei numeri (camera est nord quota, punto guardato est nord quota);
# "t+3" vuol dire 3 m sopra il terreno in quel punto. Escono in shots/vista-<nome>-<n>.png
node vista.mjs duomo -26 -4 t+3 -12 -3.5 t+11
# valuta un'espressione nella pagina, con g = window.gravina
node valuta.mjs "g.Terrain.heightAt(0, 0)"
# vetrina: primo piano e campo lungo sul ponte in desktop, telefono verticale e orizzontale;
# i numeri facoltativi provano altre pose del campo lungo (CONFIG.camera.showroom)
node vetrina.mjs "[26,56,3,8]" "[18,82,8,6]"
```

Se Playwright non trova Chromium, installalo con `npx playwright install chromium`
oppure indica un eseguibile con `CHROMIUM_PATH=/percorso/chrome`.

Le prove aprono `index.html?debug` in Chromium senza finestra (WebGL via SwiftShader):
gli fps misurati lì sono molto più bassi di quelli di un vero dispositivo.
