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

Se Playwright non trova Chromium, installalo con `npx playwright install chromium`
oppure indica un eseguibile con `CHROMIUM_PATH=/percorso/chrome`.

Le prove aprono `index.html?debug` in Chromium senza finestra (WebGL via SwiftShader):
gli fps misurati lì sono molto più bassi di quelli di un vero dispositivo.
