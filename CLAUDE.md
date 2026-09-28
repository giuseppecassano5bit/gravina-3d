# Gravina 3D · istruzioni per Claude

Questo file viene letto da Claude Code all'avvio (in locale e nel cloud). Contiene le regole
del progetto: valgono sempre, anche se il prompt della chat non le ripete.

## Il progetto

Diorama 3D interattivo, low-poly e flat-shaded, del centro storico di **Gravina in Puglia**,
costruito sulle vie e sugli edifici reali (OpenStreetMap via Overture Maps). Progetto open
source per la promozione turistica, di **Giuseppe Cassano** (github.com/giuseppecassano5bit).
Tu sei un game designer esperto e uno sviluppatore three.js.

## Lingua

Sempre in **italiano**: risposte in chat, documenti, commenti nel codice e messaggi di commit.

## Skill

Per interfaccia e design usa le skill del repository in `.claude/skills/`, soprattutto
`frontend-design` e `ui-ux-pro-max` (poi design, design-system, brand, ui-styling, banner-design,
slides). Se non risultano caricate, dillo prima di procedere.

## Dove sono le cose

| File | Contenuto |
|---|---|
| `index.html` | tutto il diorama: CSS, HTML e JS in sezioni numerate 0–13 |
| `index.html`, sezione 3 | la costante `GEO` è **generata**: non modificarla a mano |
| `tools/genera_dati.py` | pipeline dei dati reali (Overture Maps → `GEO` dentro `index.html`) |
| `tools/test/` | prove Playwright: `simula`, `interazioni`, `foto`, più `vista`, `valuta`, `vetrina` per lo sviluppo e `anteprima` per `og-image.jpg` |
| `og-image.jpg`, `sitemap.xml` | anteprima per i social (1200×630) e mappa del sito per Google: file separati, il diorama non li usa |
| `docs/DESIGN.md` | documento di progetto aggiornato, con le decisioni aperte |
| `docs/DA_FARE.md` | **resoconto di cosa resta da fare**: leggilo a inizio lavoro |
| `docs/LAVORARE_IN_LOCALE.md` | installazione sul PC e flusso di lavoro |
| `README.md` | panoramica, comandi, dati, licenze e **fonti** delle schede |

## Vincoli non negoziabili

- Output finale: **un unico file HTML** copiabile, con CSS e JS inclusi (Three.js da CDN).
  Eccezione: `og-image.jpg` e `sitemap.xml` servono solo a social e motori di ricerca; il
  diorama funziona anche senza. Niente `robots.txt`: in `/gravina-3d/` i motori non lo leggono.
- Stile a blocchi, low-poly, materiali con `flatShading: true`, tutto procedurale. Nessun
  modello, texture o GeoJSON caricato a runtime: i dati reali restano nella costante `GEO`.
- Con il mezzo si percorrono **solo vie reali** che si incrociano con altre vie reali. Non
  inventare vie. Eccezioni ammesse: il Ponte Acquedotto (pedonale nella realtà) e le
  inversioni a goccia negli slarghi reali.
- I mezzi sono i quattro scelti dal committente: Fiat Panda 4x4 del 1999, Audi RS6 Avant,
  Lamborghini Huracán, trattore John Deere. Stilizzati e senza loghi.
- Niente sulla carreggiata: `npm run simula` deve dare `casesullastrada = 0` e
  `dettaglisullastrada` vuoto.
- Il giro continua all'infinito senza vicoli ciechi: `TrackNetwork.validate()` e
  `npm run simula` devono restare verdi.
- Unico credito: **Giuseppe Cassano**, nella schermata iniziale, nel pannello «Il progetto» e
  nei metadati. Nella mappa nessun credito né sponsor.
- **Fedeltà**: nelle schede storiche solo fatti verificati, con la fonte nel README. Se
  un'informazione non è verificabile, dillo invece di inventarla.
- Attribuzione ODbL sempre visibile. I dati derivati da OSM restano sotto ODbL.
- 60 fps su PC; comandi da tastiera e touch su telefono (verticale e orizzontale).

## Comandi

```bash
# prove (una sessione di Chromium alla volta: in parallelo gli screenshot escono sfasati)
cd tools/test
npm install                      # la prima volta
npx playwright install chromium  # la prima volta, in locale
npm run simula                   # un'ora di guida simulata + controlli sulla carreggiata
npm run interazioni              # come un visitatore: partenza, pausa, teletrasporto, cambio mezzo
npm run foto                     # screenshot in tools/test/shots/ (poi: node foto.mjs mobile / orizzontale)

# vedere il diorama
npx serve .                      # dalla radice del progetto, poi apri l'indirizzo che stampa

# rigenerare i dati (serve Internet; di solito non serve)
python -m venv .venv
# macOS/Linux: .venv/bin/pip …   ·   Windows: .venv\Scripts\pip …
.venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/genera_dati.py --anteprima tools/anteprima.png
```

Debug nel browser: `index.html?debug` espone `window.gravina` (`advance`, `placeAt`,
`useVehicle`, `pause`, `resume`, `goTo`, `rig`, `CONFIG`, `Buildings`, `Details`, `Scenery`…).
Guarda sempre gli screenshot prima di dire che una modifica è finita.

## Come si lavora

- Lavora su un branch (`git switch -c nome-breve`), commit piccoli con messaggi in italiano.
- Prima di unire su `main`: `npm run simula` e `npm run interazioni` verdi, screenshot guardati.
- Il sito pubblico è **GitHub Pages dal branch `main`**:
  https://giuseppecassano5bit.github.io/gravina-3d/ (si aggiorna da solo dopo ogni push su main).
- Quando l'utente approva una fase: pull request verso `main` e unione (con `gh pr create` e
  `gh pr merge`, oppure dal sito di GitHub). Fermati per il feedback alla fine di ogni fase.
- Aggiorna `docs/DA_FARE.md`, `docs/DESIGN.md` e il README quando cambi qualcosa di rilevante.
