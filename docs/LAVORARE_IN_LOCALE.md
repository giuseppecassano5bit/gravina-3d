# Lavorare a Gravina 3D sul proprio computer

Guida per portare il progetto dal cloud al PC e continuare con Claude Code in locale.
Tutto il lavoro è su GitHub (`giuseppecassano5bit/gravina-3d`, branch `main`): sul PC basta
clonarlo. Le regole del progetto sono in `CLAUDE.md`, che Claude Code legge da solo.

## 1. Cosa installare (una volta sola)

| Programma | A cosa serve | Dove si prende |
|---|---|---|
| **Git** | scaricare il progetto e salvare le modifiche su GitHub | https://git-scm.com (su Windows installa anche Git Credential Manager, già incluso) |
| **Node.js 20 o più recente** (LTS) | le prove automatiche e il server locale | https://nodejs.org |
| **Python 3.11 o più recente** | solo per rigenerare i dati di OpenStreetMap (raramente) | https://www.python.org (su Windows spunta "Add python.exe to PATH") |
| **Claude Code** | Claude che lavora sul progetto | istruzioni aggiornate: https://code.claude.com/docs · con Node già installato: `npm install -g @anthropic-ai/claude-code` |
| **GitHub CLI** (facoltativo) | aprire e unire le pull request dal terminale | https://cli.github.com, poi `gh auth login` |

Serve anche un browser moderno (Chrome, Edge, Firefox, Safari).

## 2. Scaricare il progetto

Apri un terminale (su Windows: PowerShell o Git Bash) nella cartella dove vuoi il progetto:

```bash
git clone https://github.com/giuseppecassano5bit/gravina-3d.git
cd gravina-3d
```

La prima volta che fai `git push`, Git chiede di accedere a GitHub (si apre il browser).

## 3. Preparare le prove automatiche

```bash
cd tools/test
npm install
npx playwright install chromium    # scarica il Chromium per le prove (circa 150 MB)
npm run simula                     # deve finire con "Nessun errore in console."
npm run interazioni                # 11 controlli con ✓
cd ../..
```

Le prove usano un WebGL software (SwiftShader): gli fps che misurano sono più bassi di quelli
veri. Lancia una prova alla volta, non in parallelo.

## 4. Vedere il diorama sul PC (e sul telefono di casa)

```bash
npx serve .
```

Apri l'indirizzo che compare (di solito http://localhost:3000). Per provarlo sul telefono
collegato alla **stessa rete Wi-Fi**, usa l'indirizzo "Network" che `serve` stampa
(per esempio http://192.168.1.20:3000). Con `?debug` in fondo all'indirizzo compaiono fps,
triangoli e l'oggetto `window.gravina` nella console.

## 5. Rigenerare i dati (solo se serve)

Serve Internet: lo script scarica pochi MB dal bucket pubblico di Overture Maps.

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/genera_dati.py --anteprima tools/anteprima.png

# Windows (PowerShell)
py -m venv .venv
.venv\Scripts\pip install -r tools\requirements.txt
.venv\Scripts\python tools\genera_dati.py --anteprima tools\anteprima.png
```

Con la stessa release di Overture (`RELEASE` nello script) i dati escono identici.

## 6. Lavorare con Claude Code

1. Apri il terminale **nella cartella `gravina-3d`** e avvia `claude` (oppure apri la cartella
   dall'app desktop di Claude o dall'estensione di VS Code).
2. Incolla il prompt del lavoro da fare. I prompt si preparano di volta in volta e stanno
   nella cartella locale `riferimenti/`, fuori da git.
3. Claude legge `CLAUDE.md` e `docs/DA_FARE.md` e parte dal punto indicato nel prompt.

In locale Claude chiede il permesso prima di eseguire comandi o modificare file: puoi
approvare una volta per tutte i comandi che si ripetono (per esempio `npm run simula`).

## 7. Mettere online le modifiche

Il sito pubblico è GitHub Pages dal branch `main`:
**https://giuseppecassano5bit.github.io/gravina-3d/**

- Ogni push su `main` aggiorna il sito in 1–2 minuti.
- Il flusso consigliato: branch → commit → prove verdi → pull request → unione su `main`.
  Con GitHub CLI: `gh pr create --base main` e poi `gh pr merge --merge`.
- **Attivazione di GitHub Pages (una volta sola, se il sito non risponde):** su GitHub apri il
  repository → **Settings** → **Pages** → in *Build and deployment* scegli **Deploy from a
  branch**, branch **main**, cartella **/ (root)** → **Save**. Dopo un paio di minuti in cima
  alla pagina compare l'indirizzo del sito.

## 8. Differenze rispetto al cloud

- In locale non c'è il proxy del cloud: i siti delle fonti (Wikipedia, GravinaOggi…) si
  leggono direttamente, e le verifiche storiche sono più semplici.
- Non servono `CHROMIUM_PATH` né `REQUESTS_CA_BUNDLE`: erano accorgimenti del cloud.
- Gli strumenti del cloud per GitHub (pull request, controlli) in locale si sostituiscono con
  GitHub CLI (`gh`) o con il sito di GitHub.
