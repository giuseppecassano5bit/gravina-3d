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

Per interfaccia e design usa le skill di design, soprattutto `frontend-design` e `ui-ux-pro-max`
(poi design, design-system, brand, ui-styling, banner-design, slides). Non sono nel repository:
sono installate sul Mac del committente in `~/.claude/skills/`. Se non risultano caricate (per
esempio in una sessione nel cloud), dillo prima di procedere.

I prompt delle chat e le foto di riferimento stanno in `riferimenti/`, nella cartella locale:
è fuori da git e non va caricata su GitHub.

## Dove sono le cose

| File | Contenuto |
|---|---|
| `index.html` | tutto il diorama: CSS, HTML e JS in sezioni numerate 0–13 |
| `index.html`, sezione 3 | la costante `GEO` è **generata**: non modificarla a mano. Il diorama è fatto di tre zolle (città, P.I.P., Bosco) in `GEO.meta.zolle` |
| `tools/genera_dati.py` | pipeline dei dati reali (Overture Maps, OSM via Overpass, quote Copernicus → `GEO` dentro `index.html`) |
| `tools/test/` | prove Playwright: `simula` (anche il giro della mongolfiera), `interazioni`, `foto`, `prestazioni` (GPU vera: triangoli, draw call, tempi; dal blocco M3 anche la vista «mongolfiera», il punto più pesante del giro), `difetti` (vie sotto il terreno o sospese, dischi, decorative sovrapposte), più `vista`, `valuta`, `vetrina` per lo sviluppo e `anteprima` per `og-image.jpg` |
| `og-image.jpg`, `sitemap.xml` | anteprima per i social (1200×630) e mappa del sito per Google: file separati, il diorama non li usa |
| `docs/DESIGN.md` | documento di progetto aggiornato, con le decisioni aperte |
| `docs/DA_FARE.md` | **resoconto di cosa resta da fare**: leggilo a inizio lavoro |
| `docs/LAVORARE_IN_LOCALE.md` | installazione sul PC e flusso di lavoro |
| `README.md` | panoramica, comandi, dati, licenze e **fonti** delle schede |

## Vincoli non negoziabili

- Output finale: **un unico file HTML** copiabile, con CSS e JS inclusi (Three.js da CDN).
  Eccezione (approvata il 28/09/2026): `og-image.jpg` e `sitemap.xml` servono solo a social e
  motori di ricerca; il diorama funziona anche senza. Niente `robots.txt`: in `/gravina-3d/` i motori non lo leggono.
- Stile a blocchi, low-poly, materiali con `flatShading: true`, tutto procedurale. Nessun
  modello, texture o GeoJSON caricato a runtime: i dati reali restano nella costante `GEO`.
- Con il mezzo si percorrono **solo vie reali** che si incrociano con altre vie reali. Non
  inventare vie. Eccezioni ammesse: il Ponte Acquedotto (pedonale nella realtà) e le
  inversioni a goccia negli slarghi reali.
- **Tracciato reale compresso** (eccezione come il Ponte Acquedotto, fase 3.4 blocchi F e L): la
  strada per il Bosco Difesa Grande segue il tracciato reale (provinciale Matera–Gravina, poi
  la strada verso il bosco, circa 5,3 km) ridotto in scala (`BOSCO_SCALA`) fino all'area Quercus,
  e prosegue con la stessa regola fino al vivaio forestale (3,2 km reali, circa 670 m). Gli angoli
  di svolta restano quelli reali, le lunghezze si accorciano. Le zone attorno all'area Quercus e
  al vivaio restano a scala reale (`ZONA_Q`, `ZONA_V`), e i sentieri del bosco non si comprimono.
  Nessun'altra via si comprime: la strada del P.I.P. - Zona Artigianale resta a scala reale.
- **A piedi nel bosco** (blocco L): i sentieri reali OSM attorno all'area Quercus
  (`QUERCUS_SENTIERI` in `genera_dati.py`) si percorrono con la figurina, come nel centro storico.
- **Acceleratore** (blocco E): solo su PC, Shift tenuto premuto (`CONFIG.drive.boost`). Sul
  telefono non c'è, per non rischiare rallentamenti (decisione del committente).
- **A piedi** (blocco G): marciapiedi, passaggi e scalinate reali del centro storico (flag 32,
  `WALK` in `genera_dati.py`) si percorrono con la figurina, solo se chiudono un anello con altre
  vie reali. Il mezzo si ferma all'imbocco e aspetta al tratto carrabile d'uscita (eccezione: ci
  compare, fuori dall'inquadratura). Le scalinate che nei dati finiscono nel vuoto restano
  decorative: non si inventano raccordi.
- Nel centro storico le quote Copernicus fanno solo da **guida**: per la discesa dei rioni
  (`GEO.rioni`) e, dal blocco N1, per l'altopiano (`GEO.centro`, `Guida` nella sezione 4, senza
  esagerazione: `CONFIG.terrain.relief` = 1). Canyon, cigli, falesia e gradoni restano disegnati a
  mano; le vie del mezzo stanno entro il 18% (`CONFIG.road.maxGrade`, blocco D; dal blocco E in tutta
  la città; dal blocco N1 c'è anche il limitatore sulle quote degli incroci, `#limitNodes`).
- **Musica**: solo brani originali generati dal codice (sezione 11b). Niente canzoni o campioni di
  terzi, anche se richiesti: sono protetti e pesano più dell'intero diorama.
- **Eccezioni approvate dal committente il 01/10/2026 (blocco M2)**: i percorsi a piedi dentro la
  Fiera di San Giorgio, nel giardino del Casino di Meninni e fino alla Base Scout non sono in OSM
  (`PERCORSI` in `genera_dati.py`) e si disegnano solo perché chiudono un anello con vie reali;
  Villa Comunale e Piazza della Repubblica sono pedonali anche dove OSM segna `residential`; tre vie
  cieche reali si percorrono fino al luogo, con la goccia (`VIE_CIECHE`): la strada della Fiera fino
  al parcheggio dello stadio, Via Guardialto fino al Casino di Meninni, Via Bari fino alla Cola Cola.
- **Sottopassi** (blocco M2): dove OSM segna una galleria sotto i binari la via scende in trincea
  (`Sottopassi`, rampe entro il 18%) e i binari, se serve, salgono di poco; il terreno si ritaglia.
- Le vie cieche reali della città (`GEO.deco`) si disegnano ma **non si percorrono**. La
  sterrata reale del Castello Svevo è percorribile: con la strada di servizio e la vicinale
  chiude un anello (flag 8, `CASTLE_BOX` in `genera_dati.py`).
- I mezzi sono i **cinque** scelti dal committente: Fiat Panda 4x4 del 1999, Audi RS6 Avant,
  Lamborghini Huracán, trattore John Deere e, dal blocco M3, la mongolfiera. Le auto sono
  **realistiche nello stile** (carrozzeria per sezioni, abitacolo col guidatore, luci da uniform,
  4 mesh per mezzo), sempre low-poly e senza loghi.
- **Mongolfiera** (blocco M3): è un'eccezione come il Ponte Acquedotto. Vola su un **giro fisso**
  (`CONFIG.balloon`, sezione 8b) e non segue le vie; resta almeno 30 m sopra tetti, monumenti e
  terreno e dentro la zolla della città. Alla fine del giro si riparte con l'ultima auto dalla via
  percorribile più vicina al decollo.
- Niente sulla carreggiata, nemmeno sui tratti a piedi: `npm run simula` deve dare
  `casesullastrada = 0` e `dettaglisullastrada` vuoto.
- Il giro continua all'infinito senza vicoli ciechi: `TrackNetwork.validate()` e
  `npm run simula` devono restare verdi.
- Unico credito: **Giuseppe Cassano**, nella schermata iniziale, nel pannello «Il progetto» e
  nei metadati. Nella mappa nessun credito né sponsor.
- **Fedeltà**: nelle schede storiche solo fatti verificati, con la fonte nel README. Se
  un'informazione non è verificabile, dillo invece di inventarla.
- Attribuzione ODbL sempre visibile. I dati derivati da OSM restano sotto ODbL.
- Attribuzione delle quote Copernicus sempre visibile, con il testo esatto dell'art. 6(b)
  della licenza WorldDEM-30 (`GEO.meta.quote`): schermata iniziale, mappa della pausa e, in
  breve, sotto la minimappa.
- Budget (piano della fase 3.4, sezione 3): per fotogramma al massimo 400 000 triangoli su PC e
  250 000 sul telefono, 90 e 70 draw call. Si misura con `node prestazioni.mjs`. I riquadri hanno
  due livelli di dettaglio nella stessa mesh (sezione 6e, `Tiles.updateLod`): quello che si
  aggiunge ai riquadri va anche nella versione lontana, semplificato, o solo in quella piena.
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
node prestazioni.mjs dopo        # triangoli, draw call, tempi e memoria con la GPU vera (PC e telefono)
node difetti.mjs                 # difetti delle vie nei riquadri (GRAVINA_HTML=copia.html per un'altra versione)

# vedere il diorama
npx serve .                      # dalla radice del progetto, poi apri l'indirizzo che stampa

# rigenerare i dati (serve Internet; di solito non serve)
python -m venv .venv
# macOS/Linux: .venv/bin/pip …   ·   Windows: .venv\Scripts\pip …
.venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/genera_dati.py --anteprima tools/anteprima.png
```

Debug nel browser: `index.html?debug` espone `window.gravina` (`advance`, `placeAt`,
`useVehicle`, `pause`, `resume`, `goTo`, `rig`, `driver`, `Radio`, `CONFIG`, `Buildings`, `Details`,
`Scenery`…). A piedi: `driver.onFoot`, `driver.car` (dove aspetta il mezzo); camera libera:
`rig.drag(dx, dy)`, `rig.zoom(f)`, `rig.follow()`.
Guarda sempre gli screenshot prima di dire che una modifica è finita.

## Come si lavora

- Lavora su un branch (`git switch -c nome-breve`), commit piccoli con messaggi in italiano.
- Prima di unire su `main`: `npm run simula` e `npm run interazioni` verdi, screenshot guardati.
- Il sito pubblico è **GitHub Pages dal branch `main`**:
  https://giuseppecassano5bit.github.io/gravina-3d/ (si aggiorna da solo dopo ogni push su main).
- Quando l'utente approva una fase: pull request verso `main` e unione (con `gh pr create` e
  `gh pr merge`, oppure dal sito di GitHub). Fermati per il feedback alla fine di ogni fase.
- Aggiorna `docs/DA_FARE.md`, `docs/DESIGN.md` e il README quando cambi qualcosa di rilevante.
