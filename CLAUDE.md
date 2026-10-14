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
  Fiera di San Giorgio e fino alla Base Scout non sono in OSM (`PERCORSI` in `genera_dati.py`) e si
  disegnano solo perché chiudono un anello con vie reali; Villa Comunale e Piazza della Repubblica sono
  pedonali anche dove OSM segna `residential`; due vie cieche reali si percorrono fino al luogo, con la
  goccia (`VIE_CIECHE`): la strada della Fiera fino al parcheggio dello stadio, Via Bari fino alla Cola Cola.
- **Casino di Meninni (blocco N4, piano approvato dal committente il 14/10/2026)**: lo sterrato «Ingresso del
  Casino di Meninni» (`STRADA_MENINNI`, 18 m, non in OSM: punti scelti su satellite e Street View) lascia la SP201
  e finisce con la goccia del mezzo nello spiazzo davanti al cancello; la goccia di prima in mezzo alla SP201 non
  c'è più e oltre l'incrocio la SP201 è decorativa. Il giardino a piedi (`GIARDINO_MENINNI`, non in OSM) va dal
  fondo dello sterrato per il cancello attorno al Casino fino alla goccia della figurina nella radura dietro
  (`GOCCE_PIEDI`). Il muro di cinta (`MURO_MENINNI`) è indicativo (satellite e Street View) e tiene lontane le gocce;
  la cappella di famiglia non si vede in nessuna foto: è semplice, nel posto proposto col piano. Corvi e vento
  generati dal codice, con l'interruttore dei suoni del bosco.
- **Sottopassi** (blocco M2): dove OSM segna una galleria sotto i binari la via scende in trincea
  (`Sottopassi`, rampe entro il 18%) e i binari, se serve, salgono di poco; il terreno si ritaglia.
- **Eccezioni del Fondovito (blocco N2, piano approvato dal committente il 05/10/2026)**:
  - le vie che nella realtà non si fanno in auto per i dislivelli sono **pedonali anche dove OSM segna
    `residential`** (`PEDONALI_FONDOVITO`: la Calata Grotte San Michele), come Villa e Piazza della Repubblica;
    regole: nessun vicolo cieco per il mezzo, il mezzo aspetta all'uscita (blocco G);
  - un tratto a piedi può finire con la **goccia della figurina in uno slargo reale** (`GOCCE_PIEDI`), come le
    gocce del mezzo: oggi sul promontorio oltre il ponticello di San Michele;
  - il **raccordo di 18 m attraverso l'area pedonale di Piazza Pellicciari** (OSM w469108906, `RACCORDI_PIEDI`)
    dai Gradoni San Giovanni Battista a Via Marconi, come le aree pedonali della Villa;
  - il **ponticello di San Michele** (`PONTICELLO`) non è in OSM: si vede sul satellite e nella foto da drone
    del 2019 in fondo alla terrazza, sopra la testa del canalone; si percorre a piedi, in piano, e sotto scende
    il filo d'acqua (`Cascata`, richiesta del committente);
- **Hortus a piedi (blocco N5c, piano approvato dal committente il 14/10/2026)**: Via Giacomo Leopardi
  (OSM w1384781495, 65 m) è pedonale fino al cancello di Hortus (`PEDONALI_FONDOVITO`) e oltre il cancello è decorativa;
  il giardino a piedi (`GIARDINO_HORTUS`, 53 m, non in OSM) entra dal cancellino, compie un anello tra i terrazzamenti
  di tufo toccando la panchina panoramica (con la sosta, la scheda e il pulsante «Riprendi il percorso») e si richiude
  al cancello per tornare al mezzo che aspetta su Via San Vito Vecchio.
- **Mezzi nuovi (blocco N6, decisione del committente del 14/10/2026)**:
  Sostituiti i 4 mezzi terrestri originali con i modelli richiesti:
  1. Fiat Panda del 2013 (terza serie "Squircle", 3,65 × 1,64 × 1,55 m, passo 2,30 m, fari alti e terza luce sagomata);
  2. Audi RS Q8 (SUV coupé sportivo, 5,01 × 2,00 × 1,70 m, Singleframe RS a nido d'ape, cerchi 23", doppio scarico ovale);
  3. Ferrari Monza SP2 (barchetta biposto aperta senza parabrezza, 4,66 × 1,99 × 1,15 m, Virtual Wind Shield, twin buttresses, fascia continua LED a tutta larghezza e 4 scarichi);
  4. Trattore John Deere serie 8R coi contropesi anteriori (6,65 × 2,55 × 3,45 m, castello zavorre in ghisa a sbalzo, ruote posteriori giganti da 2,16 m, cabina CommandView IV e fumo alto).
  La mongolfiera (quinto mezzo volante introdotto nel blocco M3) resta invariata.
- **Eccezione di Santa Lucia (blocco N2b, piano approvato dal committente il 07/10/2026)**: il footway OSM w1195336380
  («Calata S. Lucia» su Google, 60 m da Via Michelangelo Calderoni alla chiesa) si percorre a piedi e finisce con la
  **goccia della figurina** nello slargo davanti alla chiesa (`GOCCE_PIEDI`), come il ponticello di San Michele. L'anello con
  w1512581502 («Via Santa Lucia») non si fa: tra la fine del sentiero e la via ci sono 9 m senza collegamento in OSM.
- **Ruderi e piani del centro storico (blocco N2b)**: i `building=ruins` OSM del centro storico sono ruderi (`KIND['rudere']`,
  muri crollati a pezzi, senza tetto; nel cono di vista dalla ringhiera della Cattedrale verso il ponte restano bassi, così il ponte
  si vede) e i piani delle case vengono dalla tabella `LIVELLI` di `genera_dati.py` (rilevati su Street View, con via e data;
  «almeno N» dove la cima non si vede); dove non c'è una riga vale la regola di `Buildings.height`.
- **Guado di Capotenda (blocco N5, piano approvato dal committente il 14/10/2026)**: i sentieri e le carrarecce OSM di Capotenda
  (`WALK_OSM`) si percorrono a piedi fino al guado, e la figurina passa sui sassi (OSM w578916734–35, `ford=stepping_stones`, più i
  primi 9 m di w578916733) fino alla **goccia della figurina** sul greto dell'altra sponda (`GOCCE_PIEDI`), come il ponticello di San
  Michele: il tratto esce dalla zolla in Overture e i suoi punti OSM sono nella costante `GUADO`. Nel terreno la gola stretta tra il
  belvedere e il guado (`GOLA` e `Gola`, sezione 4) è incisa a mano sulle quote reali (non alza mai il terreno; vicino ai sentieri
  lascia la cengia); la vigna di Botromagno è la classe `vigna` (16) dell'uso del suolo.
- **SP201 fino a Sportland (blocco N5b, piano approvato dal committente il 14/10/2026)**: la SP201 torna percorribile oltre lo
  sterrato del Casino di Meninni fino al bivio di via Guardialto Alto (OSM w1158532123, `highway=service`: entra nella rete per id,
  `SERVIZIO_OSM`), e questa fino al piazzale sterrato davanti ai campi di Sportland, con la goccia del mezzo (`VIE_CIECHE`), fuori dal
  recinto del centro sportivo: in OSM è cieca, nessun anello. A Sportland niente scritte, insegne, cartelloni né etichetta (decisione
  del committente: niente pubblicità), ma la zona riconoscibile (campi, reti, torri faro, cancello con l'arco). Il Casino Scacchi (rudere
  OSM w411138777, oggetto `Scacchi`) si guarda soltanto: nessuna strada, solo l'etichetta. Gli uliveti a filari stanno in `ULIVETI`
  (contorni indicativi dal satellite, tranne l'uliveto OSM w1152762647); il prato tra Via Madonna della Stella e la gravina è senza
  alberi (`PRATO_STELLA`).
- **Villette del Liceo Tarantino (blocco N4b, piano approvato dal committente il 14/10/2026)**: tutto il triangolo Via Montale – Via
  Quasimodo – Via Bertocchi (in OSM «Bertocchi» è un refuso di Betocchi: nel diorama resta il nome OSM, segnalato nel README) è di tipo
  «villetta» (`CITY_KIND` 13, oggetto `Villette` in sezione 6d); i livelli stanno nelle righe della città di `LIVELLI` (3 m per piano
  più il parapetto, contati sul lato alto, niente «almeno»), unità e tetti (coppi, pannelli, attico) nella tabella `VILLETTE`.
- **Facciate di chiese e scuole (blocco N3)**: tabelle `FACCIATE` e `SCUOLE` (sezione 6d), un solo costruttore
  (`Details.facciata`); solo gli elementi visti in una foto (fonti nel README), nessuna scritta coi nomi, campanili solo dove
  si vedono. In pipeline: la navata di San Nicola è l'area OSM del luogo di culto (`CHIESE_AREE`), l'Addolorata è una chiesa
  (`CHIESE_OSM`), i nomi di Madonna delle Grazie, Santi Pietro e Paolo e Spirito Santo stanno sulle chiese vere (`CHURCHES`).
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
