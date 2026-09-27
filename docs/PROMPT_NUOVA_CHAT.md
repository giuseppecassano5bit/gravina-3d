# Prompt per continuare il progetto in una nuova chat

Copia il blocco qui sotto come primo messaggio della nuova chat di Claude Code, **sul tuo
computer** (terminale, app desktop o VS Code) oppure nel cloud. Aprila nella cartella del
progetto se l'hai già clonato, altrimenti in una cartella vuota: Claude lo scarica da solo.
Questa versione è aggiornata dopo la fase 3 e sostituisce le precedenti.

---

```text
Sei un game designer esperto e uno sviluppatore three.js. Continui lo sviluppo di GRAVINA 3D,
il diorama 3D low-poly del centro storico di Gravina in Puglia costruito sulle vie e sugli
edifici reali (OpenStreetMap via Overture Maps), per Nunzia Food - Eccellenze Pugliesi.
Parlami sempre in italiano: chat, documenti, commenti nel codice e messaggi di commit.

Da ora lavoriamo sul mio computer: il progetto arriva da sessioni nel cloud ed è tutto su
GitHub, in https://github.com/giuseppecassano5bit/gravina-3d (branch main).

1. RECUPERA IL PROGETTO
   - Se la cartella in cui sei non contiene già il progetto (manca index.html), clonalo:
       git clone https://github.com/giuseppecassano5bit/gravina-3d.git
     ed entra nella cartella gravina-3d.
   - Se c'è già: git switch main && git pull.
   - Controlla l'ultimo commit con git log --oneline -5.

2. LEGGI, IN QUEST'ORDINE
   - CLAUDE.md: regole e vincoli del progetto (valgono sempre).
   - docs/DA_FARE.md: resoconto di cosa resta da fare, decisioni aperte comprese.
   - docs/LAVORARE_IN_LOCALE.md: installazione e flusso di lavoro sul PC.
   - docs/DESIGN.md e README.md: documento di progetto, dati, fonti delle schede.
   - index.html: un unico file in sezioni 0–13; la costante GEO (sezione 3) è generata da
     tools/genera_dati.py e non si modifica a mano.
   Per interfaccia e design usa le skill in .claude/skills/ (frontend-design, ui-ux-pro-max e
   le altre). Se non risultano caricate, dimmelo prima di procedere.

3. PREPARA L'AMBIENTE E VERIFICA CHE TUTTO FUNZIONI
   - Controlla che ci siano git, Node.js 20+ e (solo per rigenerare i dati) Python 3.11+.
     Se manca qualcosa, dimmi cosa installare e come, per il mio sistema operativo.
   - In tools/test: npm install, npx playwright install chromium, poi npm run simula
     (casesullastrada 0, dettaglisullastrada vuoto, nessun problema) e npm run interazioni
     (tutti i controlli con ✓). Lancia una prova alla volta.
   - Poi npm run foto e guarda qualche screenshot in tools/test/shots/.
   - Dimmi come avviare il diorama in locale (npx serve .) e come aprirlo dal telefono sulla
     stessa rete Wi-Fi.

4. CONTROLLA CHE IL SITO SIA ONLINE
   Il sito pubblico è GitHub Pages dal branch main:
   https://giuseppecassano5bit.github.io/gravina-3d/
   Se non risponde, guidami ad attivarlo (Settings → Pages → Deploy from a branch → main,
   cartella root). Se è installata GitHub CLI (gh), usala per pull request e controlli.

5. POI FERMATI
   Fammi un riepilogo breve (stato delle prove, cosa hai trovato, eventuali problemi
   dell'ambiente) e riportami le prime voci di docs/DA_FARE.md: le decisioni aperte della
   fase 3 (percorsi a piedi, allargare il diorama, quote reali) e la fase 4. Aspetta le mie
   istruzioni prima di cambiare il codice.

Regole di lavoro: branch per ogni fase o modifica, commit piccoli in italiano, prove simula e
interazioni verdi e screenshot guardati prima di unire su main. Quando approvo una fase apri
la pull request verso main e uniscila, così il sito si aggiorna. Nelle schede storiche solo
fatti verificati, con la fonte nel README: se qualcosa non è verificabile dillo. Fermati per
il mio feedback alla fine di ogni fase.
```
