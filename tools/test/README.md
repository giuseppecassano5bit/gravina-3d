# Prove automatiche

```bash
cd tools/test
npm install
npm run simula          # un'ora di guida simulata: nessun blocco, nessun vicolo cieco, nessun errore
npm run foto            # screenshot delle scene principali in tools/test/shots/
node foto.mjs mobile    # le stesse scene su uno schermo da telefono
```

Se Playwright non trova Chromium, installalo con `npx playwright install chromium`
oppure indica un eseguibile con `CHROMIUM_PATH=/percorso/chrome`.
