# Istruzioni per gli agenti (Antigravity, Gemini, Codex e simili)

Le regole del progetto sono in [`CLAUDE.md`](CLAUDE.md): valgono per ogni agente, non solo per Claude. Leggilo per intero
prima di cominciare. In breve: rispondi in italiano; un solo file `index.html`; `GEO` si cambia solo da `tools/genera_dati.py`;
lavora su un branch, commit piccoli in italiano e push dopo ogni commit; mai force push, mai unione su `main` senza
l'approvazione del committente e le prove verdi (`npm run simula`, `npm run interazioni` in `tools/test`).

Lo stato del lavoro e i prompt dei blocchi sono nella cartella locale `riferimenti/` (fuori da git): parti da
`riferimenti/STATO_LAVORO.md` e `riferimenti/PROMPT_ANTIGRAVITY.md`, e aggiorna `STATO_LAVORO.md` quando ti fermi.
