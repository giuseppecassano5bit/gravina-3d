# Fase 3.4 · Gravina oltre il centro storico: piano di lavoro

Stato al 28 settembre 2026. Il piano è stato preparato prima di scrivere codice. Richiesta
originale: `riferimenti/PROMPT_FASE_3_4.md` (cartella locale, fuori da git).
Obiettivo: ogni gravinese che apre il progetto deve riconoscere subito che è una copia di
Gravina fatta bene.

Le regole di `CLAUDE.md` valgono sempre. Le eccezioni decise in questa fase vanno scritte
anche lì (vedi la sezione 9).

---

## 1. Cosa è emerso dalle verifiche

Coordinate in metri locali `[est, nord]` rispetto alla Cattedrale, come in `GEO`.

**Porta di San Michele (Piazza Arcangelo Scacchi).** La porta non esiste più.
- Era la Porta San Tommaso, poi Regia, dedicata a San Michele dopo il 1799.
- Stava sulle mura, demolite tra il 1861 e il 1890.
- In OSM la piazza (w469109640, [415, 13]) ha `old_name` "Via Estramurale; Porta Regia; Porta San Tommaso".
- Oggi resta il nome del luogo. Resta anche la nicchia con la statua lignea di San Michele del
  1799, restaurata e ricollocata il 28/11/2020, all'imbocco del centro storico.
- Nella foto 1 di `riferimenti/`, la nicchia è sul palazzo rosa, a destra del vicolo.
- Da lì parte Via Santa Cecilia: è carrabile in OSM (`residential`) e già percorribile nel
  diorama, dal nodo [415.9, −0.8], larga 3,4 m.
- Della forma dell'arco non c'è una fonte: De Marino (1608) dice solo "bellissima con ponte".

**Monumento nella foto 1 (dietro l'ulivo).** Non è il monumento ai caduti.
- Sul blocco di pietra si legge "CANIO MUSACCHIO": è il busto in bronzo del sindacalista.
- In OSM c'è un busto a [430, 30] (w411138256), probabilmente questo: da verificare.
- La piazza ha anche un busto in pietra di Arcangelo Scacchi (Giardini storici della Puglia),
  con posizione da verificare.

**Monumento ai caduti della prima guerra mondiale.**
- È al centro della Villa Comunale: OSM w411137249, [288, −92], Wikidata Q136344179.
- Il gruppo in bronzo è di Angelo Galli, il basamento di Angelo Amodio. Il bronzo è quello dei
  cannoni austriaci.
- Le figure: l'Italia turrita a cavallo con bandiera e scudo, tre soldati (bersagliere, fante,
  soldato con la spada), una donna e un uomo con la catena spezzata.
- Iscrizione "GRAVINA AI SUOI CADUTI NELLA GUERRA 1915-1918", con 317 nomi.
- **Data discordante**: 4 novembre 1922 per GravinaLife, 1934 per Giardini storici della Puglia.
  Va risolta con una terza fonte prima di scriverla.

**Fondovito = Fondovico.** Sono lo stesso rione, scritto in due modi.
- Il nome viene dal culto di San Vito, a cui era dedicata l'odierna Sant'Agostino.
- Nel diorama c'è già, come "Rione Fondovico".
- Da aggiungere: il Complesso rupestre delle Sette Camere (OSM n6365472958, [−190, −134]) e la
  Piazzetta Fondovico [−18, −121].

**Casino Meninni.**
- Le fonti (FAI, GravinaLife) parlano del "Casino dei Meninni" sul colle del Guardialto, con un
  giardino di pini d'Aleppo e una cappella di famiglia.
- In OSM non ha nome. Lo Sportland è w1158532121, a [1478, −825], sul colle di sud-est
  (circa 434 m secondo il DEM).
- Le "case rosa" non sono nei dati: serve l'indicazione del committente.

**"La caccia".** In OSM c'è un piccolo parco "La Caccia" (w831715191, [720, 534]) vicino a
Largo Cappuccini. Cosa intende il committente va chiesto.

**Zona industriale.**
- In OSM c'è il P.I.P. - Zona Artigianale: 92 ettari di capannoni reali, centro circa [2709, 778].
- Sta a circa 1 km dal centro e circa 500 m dal bordo della città.
- Lì c'è anche l'ITT - IPSIA G. Galilei (l'ITC/ITT Bachelet, [2617, 681]).
- Se è questa la zona industriale, la strada si può tenere a scala reale.

**Bosco Difesa Grande.**
- Rifugio a [−782, −5673], 5,7 km a sud.
- Tracciato reale di circa 6 km: provinciale Matera–Gravina verso sud, poi la strada verso la
  Selva. Da comprimere in 500–800 m.

**Quote reali (Copernicus GLO-30).** Centro storico 360 m, Piazza Scacchi 366, città a nord-est
fino a circa 400, colle del Castello Svevo 435, colle dello Sportland/Guardialto 434, zona P.I.P.
406, cimitero 321.
- Il modello è un DSM: include tetti e alberi e ha maglie di 30 m.
- Il canyon ne esce solo accennato, quindi resta disegnato a mano. Le quote reali servono per la
  città moderna e le colline.

**Copertura OSM.** Nell'area della città ci sono circa 3 800 edifici OSM (conteggio Overpass
del 28/09/2026), più 257 stime Microsoft. I quartieri moderni sono mappati bene: la mappa di
controllo si rigenera con lo script di esplorazione.

---

## 2. Prototipo della pipeline sulla città

Area provata: `AREA = (-800, 2100, -1150, 1250)`, cioè 2,9 × 2,4 km, circa 10 volte quella di
oggi. Contiene stadio, fiera, stazioni, pineta, cimitero, San Sebastiano, liceo, Sportland,
Spirito Santo. Fuori restano il Castello Svevo [574, 1811] e il P.I.P.

| Voce | Oggi | Prototipo città |
|---|---|---|
| Edifici | 532 | 2 038 (21 279 vertici) |
| Tratti di via / incroci | 157 / 111 | 1 350 / 835 |
| Km di vie percorribili | 9 | 75 |
| Blocco `GEO` | 153 KB (50 KB compresso) | 477 KB (157 KB compresso) |
| `free_roads` | pochi s | 7,6 s |

Classi di via nella rete di prova: residential 1 178, tertiary 77, secondary 65,
unclassified 15, living_street 6, pedestrian 5.
Escluse: trunk (tangenziale, SS96), service, track.

---

## 3. Budget di prestazioni

Misure di oggi (branch `main`) su Mac M4, 1280×720 a 2×, GPU vera, browser integrato:

| Voce | Oggi | Tetto dopo il blocco C |
|---|---|---|
| `index.html` | 399 KB (127 KB compresso) | ≤ 900 KB (≤ 280 KB compresso); dal 30/09/2026 ≤ 1,2 MB (≤ 360 KB compresso), dal 03/10/2026 **≤ 450 KB compressi**, deciso dal committente |
| Triangoli nella scena | 267 000 (terreno 72k, finestre 50k, edifici 44k, alberi 35k, strade 32k, dettagli 15k) | ≤ 650 000 |
| Triangoli per fotogramma | 266 000 | ≤ 400 000 su PC, ≤ 250 000 su telefono |
| Draw call | 37–38 | ≤ 90 su PC, ≤ 70 su telefono |
| Costruzione | circa 1 s | centro storico ≤ 1,5 s (si può partire), il resto in sottofondo |
| fps | 60 (limite del vsync) | 60 su PC, ≥ 45 su telefono medio con risoluzione adattiva |
| Memoria JS | 61 MB | ≤ 150 MB |

Da aggiungere `tools/test/prestazioni.mjs`: triangoli, draw call, tempo di costruzione, memoria e
peso del file, nelle viste centro, città e pausa. Va lanciato prima e dopo, e i numeri vanno
riportati nella PR.

Gli fps di un telefono vero li misura il committente. Con il browser integrato nascosto,
`requestAnimationFrame` è rallentato: il tempo di costruzione si misura con Playwright.

---

## 4. Zone e livelli di dettaglio

| Zona | Area | Edifici | Vie | Terreno |
|---|---|---|---|---|
| **Z0 centro storico** | l'area di oggi, allargata fino a Piazza Scacchi e Villa Comunale | come oggi: finestre istanziate, coppi, torrini, monumenti su misura | come oggi (1 m, cordoli, archi, vicoli ristretti) | maglia da 5 m, canyon e rioni procedurali |
| **Z1 città moderna** | resto del centro abitato | blocchi sulla sagoma reale, altezza da OSM o per tipo (palazzine 3–6 piani, capannoni 7–9 m); **finestre disegnate dallo shader** (`onBeforeCompile`, a costo zero in triangoli); pochi torrini istanziati | campionamento adattivo (2–8 m), marciapiedi semplici; vie cieche reali visibili ma non percorribili | maglia da 15 m, quote reali smussate |
| **Z2 bordi e strade F** | fascia esterna, strade compresse, zone del bosco e industriale | capannoni e masserie come blocchi | tracciato compresso (F) | maglia da 30 m, ulivi e macchia radi |

Rendering:
- Riquadri da 250 m: una mesh per riquadro e per strato (terreno, strade, edifici), così il
  frustum culling lavora.
- La nebbia finisce a circa 1,1 km, `camera.far` a circa 1,6 km.
- Le ombre riguardano solo i riquadri vicini: il riquadro d'ombra da 180 m resta.
- Costruzione progressiva: prima il centro storico (il pulsante Parti si abilita), poi i riquadri
  della città, pochi per fotogramma, durante la vetrina.
- Sui dispositivi touch c'è un profilo leggero: meno alberi, niente torrini in Z1, ombre solo in Z0.

Mappe:
- Minimappa vettoriale per finestra, con griglia spaziale. La tela di oggi a 2 px/m sarebbe di
  5 800 × 4 800 px, troppo per un telefono.
- Mappa della pausa con zoom (rotella/pizzico) e trascinamento, più un pulsante "centro storico".
- Elenco dei luoghi diviso per categorie.

---

## 5. Dati da scaricare

1. **Overture Maps 2026-09-23.1** (`tools/genera_dati.py`).
   - Città: `BBOX = (16.395, 16.455, 40.800, 40.840)`, temi segment, connector, building, water,
     infrastructure, land, land_use.
   - Area ampia, per i tracciati del Bosco: `(16.30, 16.52, 40.72, 40.88)`, temi segment,
     connector, place, land_use.
   - Circa 30 MB. La prima volta servono circa 13 minuti.
   - **Già in cache** nella cartella di lavoro della chat "città" (sezione 9).
2. **OpenStreetMap via Overpass API**, con query piccola e messa in cache: monumenti
   (`historic=*`), chiese con Wikidata, stazioni, parchi. Overture non li ha tutti: per esempio
   manca il monumento ai caduti. Stessa licenza ODbL.
   - Overpass rifiuta le richieste senza User-Agent o senza `Accept: application/json`.
3. **Copernicus GLO-30**, tessera N40 E016 (39 MB):
   `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N40_00_E016_00_DEM/Copernicus_DSM_COG_10_N40_00_E016_00_DEM.tif`.
   - Si legge con `tifffile` + `imagecodecs`: pixel di 1″, angolo in alto a sinistra 41 N 16 E.
   - Attribuzione obbligatoria e sempre visibile: la formula esatta va copiata dalla licenza
     ufficiale del Copernicus DEM (ESA), non scritta a memoria.
4. **Wikidata e fonti web**, per identificare le chiese senza nome e per le schede.

---

## 6. Rischi

1. **Telefoni di fascia media.** È il rischio più grosso. Si affronta con zone, riquadri,
   finestre nello shader, profilo leggero, risoluzione adattiva (già presente) e costruzione
   progressiva.
2. **Caricamento.** `GEO` triplica. Gli edifici Z1 vanno codificati in modo compatto
   (coordinate a 0,5 m, differenze); GitHub Pages comprime da solo.
3. **Terreno.**
   - Il canyon procedurale (cigli `EAST_RIM`/`WEST_RIM`) esiste solo nel centro: a nord e a sud
     va esteso, guidato dal DEM.
   - Il raccordo tra Z0 procedurale e Z1 da DEM va sfumato.
   - Il DSM include tetti e alberi, quindi va smussato (almeno 90 m).
   - Le vie seguiranno pendenze reali.
4. **Rete.**
   - Il 2-core toglie molte vie cieche reali dei quartieri: vanno disegnate come non
     percorribili, con la goccia dove c'è spazio.
   - Niente statali e svincoli a più livelli.
5. **Prove.**
   - In `simula.mjs` il controllo `casesullastrada` confronta ogni punto di via con ogni
     edificio: con la città diventa lentissimo, serve una griglia spaziale.
   - Con SwiftShader le prove saranno più lente: alzare i timeout.
6. **Fedeltà.** Molte chiese non hanno nome in OSM. Dove i fatti non sono verificabili si mette
   solo l'etichetta, senza scheda.
7. **Camera libera.**
   - Distinguere il tocco breve dal trascinamento (soglia di circa 6 px).
   - Non rompere il sollevamento sopra i tetti né le panoramiche: mentre la camera è libera, le
     panoramiche si sospendono.
8. **Lavoro in parallelo.** `index.html` è un file solo: le due chat devono toccare sezioni
   diverse e sincronizzarsi con `main` prima di ogni unione (sezione 9).

---

## 7. I blocchi

Ogni blocco ha il suo branch e una PR in bozza aperta subito. Push dopo ogni commit. Alla fine:
`npm run simula` e `npm run interazioni` verdi (una prova alla volta), screenshot guardati
(desktop, telefono in verticale e in orizzontale), stop per il feedback. Con l'approvazione:
`gh pr ready`, `gh pr merge`, controllo del sito.

### A · Crediti e ricerca su Google (`fase-3-4-a-crediti-seo`)
- Togliere ogni riferimento allo sponsor precedente: schermata iniziale, meta description,
  commento di testa di `index.html`, README, DESIGN, CLAUDE.md, il prompt per la nuova chat e
  ogni altro file (un `grep -ri` sul nome non deve trovare nulla).
- Unico credito: **Giuseppe Cassano** (github.com/giuseppecassano5bit), nella schermata iniziale
  e come autore nei metadati.
- Metadati:
  - `title` e `description` descrittivi (Gravina in Puglia, diorama 3D, centro storico,
    Giuseppe Cassano);
  - `meta author`, canonical `https://giuseppecassano5bit.github.io/gravina-3d/`;
  - Open Graph (`og:title`, `og:description`, `og:image` 1200×630, `og:url`, `og:type`,
    `og:locale it_IT`, `og:site_name`) e Twitter card `summary_large_image`;
  - `theme-color` e un'icona SVG in linea.
- JSON-LD con `@graph`: `WebSite`, `CreativeWork` con `about` → `Place` Gravina in Puglia
  (coordinate, `sameAs` Wikipedia e Wikidata), `author` → `Person` Giuseppe Cassano, licenze.
- Anteprima: un'immagine generata dal diorama con Playwright (1200×630, JPEG ≤ 150 KB), salvata
  nel repository (per esempio `og-image.jpg`).
- Testo leggibile dai motori di ricerca:
  - un pannello "Il progetto" apribile dalla schermata iniziale, con testo vero nel DOM e non
    nascosto con trucchi: cos'è, cosa si vede, come si usa, crediti, licenze, fonti;
  - un `<noscript>` più ricco.
- `sitemap.xml`. Il `robots.txt` è stato tolto durante il lavoro: in `/gravina-3d/` i motori di
  ricerca non lo leggono (vale solo quello alla radice del dominio).
- Chiedere il codice di verifica di Google Search Console e inserirlo come
  `<meta name="google-site-verification" …>`. Dopo l'unione, il committente invia la sitemap
  dalla console.
- Eccezione da far confermare e scrivere in CLAUDE.md: anteprima, sitemap e robots sono file
  separati che il diorama non usa.

### B · Camera libera durante la guida (`fase-3-4-b-camera-libera`)
- In `CameraRig` (sezione 9) c'è un'orbita attorno al mezzo in movimento: angolo orizzontale,
  inclinazione tra 10° e 80° circa, distanza tra 8 e 70 m circa. Il bersaglio segue il mezzo.
  Niente camera sotto il terreno o dentro i tetti (`Buildings.roofAt`).
- Input con Pointer Events sulla tela:
  - mouse: trascinamento per girare, rotella per lo zoom;
  - touch: un dito ruota, due dita pizzicano per lo zoom;
  - soglia di circa 6 px prima di considerarlo un trascinamento.
- Dopo circa 4 s senza input, la camera rientra dolcemente dietro al mezzo (circa 1,5 s).
- Pulsante **"Segui il mezzo"**: compare solo con la camera libera e riporta subito dietro al
  mezzo. Si disegna con le skill di design.
- Durante l'orbita le panoramiche automatiche (ponte, ciglio) si sospendono.
- In pausa si può girare attorno al mezzo; poi riprende il giro lento dall'alto.
- Non rompere: scelte agli incroci (frecce e tocchi), tocchi su cartelli ed etichette, pausa,
  teletrasporto.
- Prove in `interazioni.mjs`:
  - il trascinamento cambia la vista e il mezzo continua ad avanzare;
  - la rotella cambia la distanza;
  - dopo circa 4,5 s la camera torna dietro al mezzo;
  - "Segui il mezzo" riporta subito dietro;
  - con la camera libera il clic su un cartello sceglie ancora la via;
  - P e il teletrasporto funzionano;
  - touch con uno e due dita su telefono (CDP `Input.dispatchTouchEvent`).

### C · Città intera (`fase-3-4-c-citta`)
Pipeline (`tools/genera_dati.py`):
- `AREA` della città (sezione 2) e zona Z0 come poligono.
- Classi di via come nel prototipo. Vie cieche reali esportate come decorative; ferrovie FAL e
  RFI come linee decorative.
- Edifici Z1 semplificati a circa 0,5 m, codifica compatta, altezze da OSM (`num_floors`,
  `height` OSM) o per tipo.
- Quote Copernicus smussate in una griglia (per esempio 30 m, in decimetri interi) dentro `GEO`,
  solo per Z1 e Z2. La discesa del Z0 resta procedurale. Richiede l'approvazione del committente:
  vedi le domande.
- Estensione dei cigli del canyon a nord e a sud, guidata dal DEM.
- Luoghi da Overpass, in cache.
- `GEO` resta **generata**, mai scritta a mano.

Diorama:
- terreno a riquadri con maglie di 5, 15 e 30 m, bordo e basamento attorno alla nuova zolla;
- edifici Z1 veloci (array tipizzati, niente `ExtrudeGeometry`) con le finestre nello shader;
- strade a riquadri con campionamento adattivo;
- alberi dei parchi reali, a partire dalla Pineta;
- costruzione progressiva, nebbia e `far`;
- minimappa vettoriale, mappa della pausa con zoom, elenco dei luoghi per categorie;
- targa: "Gravina in Puglia" fuori dal centro storico. Se non ci sono fonti sui nomi dei
  quartieri moderni, niente nomi inventati.

Prove e misure:
- `simula.mjs` con griglia spaziale;
- `TrackNetwork.validate()` e `simula` verdi, `casesullastrada = 0`, `dettaglisullastrada` vuoto;
- `prestazioni.mjs` prima e dopo, con la tabella nella PR.

### D · Revisione del centro storico (`fase-3-4-d-centro-storico`, dopo C)
- Rilettura di vie, edifici e schede sulle pagine intere: Wikipedia, GravinaOggi, Stanze Orsini,
  Algramà, GravinaLife.
- Porta San Michele: modellare l'imbocco com'è oggi (vedi le domande): i due palazzi d'angolo, la
  nicchia con la statua di San Michele, luogo d'interesse con scheda. Via Santa Cecilia resta
  percorribile.
- Piazza Scacchi: aiuole curve, sedute in pietra, ulivo, busto di Canio Musacchio, busto di
  Arcangelo Scacchi (se la posizione è verificabile).
- Fondovito: il nome scelto dal committente sulla targa, le Sette Camere, la Piazzetta Fondovico.
- Altri ritocchi:
  - Quattro Fontane (1859): OSM w411137158, [123, −26];
  - Bastione medievale: OSM n13159769942, [35, 290], l'ultimo sperone delle mura;
  - Chiesa di San Nicola: OSM w385174930, [277, 62], Wikidata Q55163990;
  - Addolorata e Annunziata; campanile di San Francesco.

### E · Nuovi luoghi di interesse (`fase-3-4-e-luoghi`, dopo C)
Posizione sempre dai dati. Scheda solo con fatti verificati e fonte nel README; altrimenti
solo l'etichetta, e lo si dice.

| Luogo | Dati | Fonti già trovate | Note |
|---|---|---|---|
| Monumento ai caduti | OSM w411137249 [288, −92] | GravinaLife, GravinaOggi, Giardini storici | data 1922/1934 da risolvere |
| Fiera di San Giorgio | OSM "Zona Fiera San Giorgio" w478401751 [−53, 948], 3 ha | Stanze Orsini, GravinaOggi, fierasangiorgiogravina.it | diploma di Carlo II d'Angiò del 1294; Largo Cappuccini nel 1928; ex linificio nel 1977 |
| Stadio comunale "Stefano Vicino" | OSM w478401752 [−155, 861] | Wikipedia (FBC Gravina), GravinaLife | circa 4 000 posti, intitolato nel 2015, via Fazzatoia |
| Cimitero comunale | OSM w307087141 [−35, −655], 5,9 ha, Wikidata Q111560335 | da cercare | |
| Chiese del centro abitato | San Domenico r6148327 [556, −70]; San Nicola w385174930; Spirito Santo w1152762610 [1733, 152]; Gesù Buon Pastore w328013129 [1055, −176]; Mater Ecclesiae e San Matteo w411139947 [586, 334]; SS. Crocifisso e convento di San Sebastiano r6148330 [442, −571]; santuario Madonna delle Grazie (luogo Overture [658, 826]) | Wikidata dove c'è | chiese senza nome in OSM: w411139537 [355, 499], w411139821 [525, 907], w411139942 [1055, 1141], w411147519 [1317, 325], w411148157 [357, 382], r6148328 [721, 613]; cappelle w411146139 [62, 1060], w411144859 [−22, 1749]; evangeliche w411139371 [360, −217] e w411148880 [521, −577] |
| Pineta comunale e Parco Robinson | OSM w473031981 [29, 631], 5 ha | GravinaOggi (parco_robinson) | |
| Altri parchi e spazi verdi | Villa Comunale, Parco San Sebastiano [457, −515], Parco dell'Aquila [545, 964], Parco San Felice [746, 607], Largo Cappuccini [659, 650], piazzette del quartiere San Sebastiano | | solo etichette |
| Casino Meninni | non nominato in OSM | FAI, GravinaLife | edificio da far indicare al committente |
| La caccia | parco "La Caccia" [720, 534]? | | da chiedere |
| Stazione ferroviaria | FAL n1389951622 [381, 951] (1915); RFI n3804297063 [465, 865] | Wikipedia | le due stazioni sono vicine |
| Liceo scientifico G. Tarantino | luogo Overture [762, −471] | | solo punto, senza scheda |
| ITC/ITT Bachelet | land_use "ITT - IPSIA G. Galilei" [2617, 681] (zona P.I.P.) | | solo punto; se il P.I.P. resta fuori, va chiarito |

Vie e piazze riconoscibili da proporre al committente:
- Corsi e viali: Corso Vittorio Emanuele, Corso Aldo Moro, Corso Canio Musacchio, Corso Giuseppe
  Di Vittorio, Viale Regina Margherita, Viale dei Pini, Viale Orsini.
- Vie: Via Bari, Via Spinazzola, Via Guardialto, Via San Sebastiano, Via Tripoli,
  Via Falcone e Borsellino, Via Alcide De Gasperi, Via Garibaldi, Via Federico Meninni,
  Via Fazzatoia.
- Piazze e larghi: Piazza Cavour, Piazza Plebiscito, Piazza Bruno Buozzi, Largo Cappuccini,
  Piazza Immacolata (la Madonnina, OSM w411136133), Piazza Padre Pio, Largo Caduti del
  15 Luglio 1948, Piazza Nino Rota.
- Altri: Castello Svevo (OSM w76156899, [574, 1811], 1231, Wikidata Q3662626), fuori dall'area.

### F · Strade verso il Bosco Difesa Grande e la zona industriale (`fase-3-4-f-strade`, dopo C)
- Strada per il Bosco:
  - tracciato reale compresso in 500–800 m: gli angoli di svolta restano, le lunghezze si
    accorciano lungo il percorso;
  - attaccata al bordo sud della città;
  - finisce in una piccola zona del bosco: querce, radura, rifugio, giro a goccia;
  - scheda con fonti verificate.
- Zona industriale: se è il P.I.P., strada reale a scala reale e piccola zolla con i capannoni
  reali. Altrimenti, stessa tecnica del Bosco.
- La regola "tracciato reale compresso" è un'eccezione come il Ponte Acquedotto: va scritta in
  CLAUDE.md, DESIGN e README.
- Nessun vicolo cieco: `validate()` e `simula` verdi.

### G · Percorsi a piedi e quote reali del centro storico (`fase-3-4-g-pedoni-quote`, se c'è margine)
- Marciapiedi, scalinate e passaggi pedonali percorsi da una figurina low-poly (circa 200
  triangoli). Il mezzo si ferma all'imbocco e si ritrova al tratto carrabile successivo.
  Nessun vicolo cieco.
- Quote Copernicus come guida per ciglio, gradoni e discesa dei rioni (`RIONI`), senza perdere
  il canyon disegnato a mano.
- Da fare solo se non peggiora la fluidità (misura con `prestazioni.mjs`).

### H · Documenti (a ogni blocco)
`docs/DA_FARE.md` (stato, cosa resta), `docs/DESIGN.md`, README (fonti, eccezioni, crediti,
licenze), `CLAUDE.md` (nuove regole ed eccezioni).

### Seconda parte (decisioni del committente del 30/09/2026)

Ordine: **I → D → E → L → M → N** (M diviso in M1, M2, M3 il 01/10/2026; N in N1, N2, N3 il 03/10/2026), un blocco alla volta, ognuno col suo branch e la sua PR.
Decisioni già prese:
1. **Area Quercus** = l'ex area ristoro «Marcuccio»; in OSM «Rifugio Bosco Difesa Grande»
   (w477739267), dove oggi finisce la strada del Bosco.
2. **Vivaio forestale**: la strada compressa si allunga fino al vivaio con la stessa regola
   (angoli reali, lunghezze per `BOSCO_SCALA`). Si vedono anche la Base Scout, l'area pic-nic
   davanti al vivaio e la scritta «SIC DIFESA GRANDE» sul prato.
3. **Auto realistiche nello stile del diorama**: low-poly, `flatShading`, procedurali, senza
   loghi, ma non più fatte a blocchi.
4. **Mongolfiera**: quinto mezzo, giro fisso sopra la città (eccezione come il Ponte Acquedotto).
5. **In più**: pulsante «Cartolina», suoni del bosco (solo nel bosco), giro guidato dei monumenti.
6. **Versione in inglese**: non ora.
7. **Scuole**: il committente sceglie dall'elenco trovato nei dati quali rifinire.
8. **Area Quercus e vivaio** con tono neutro, senza pubblicità; nella mappa nessun credito né sponsor.

### I · Spazio sul telefono (`fase-3-4-i-prestazioni`)
- Obiettivo: fotogramma peggiore ≤ 200 000 triangoli sul telefono e ≤ 300 000 su PC, draw call
  non oltre quelle di oggi, nessuna differenza visibile vicino alla camera, «Pronto» ≤ 1,5 s.
- Ogni riquadro ha due livelli nella stessa mesh (`setDrawRange`, zero draw call in più): da
  lontano terreno a maglia doppia, edifici semplificati senza torrini e dettagli del tetto, vie
  più rade, metà degli alberi; cambio con isteresi oltre la nebbia vicina.
- Vista «alta» in `prestazioni.mjs` (camera a circa 120 m sopra il centro storico): è la vista
  della futura mongolfiera.

### L · Il Bosco da vicino (`fase-3-4-l-bosco`)
- **Area Quercus** al posto della capanna generica: ristorante (n11092432410), campetti
  (w1195121473/5/6, da verificare tennis o calcetto), tribunetta (w1195121474), area pic-nic,
  giochi, maneggio, parcheggio «Terra Rossa» (w477738793). Scheda neutra sulle fonti GravinaLife
  (2021, 2024, 2026).
- **Strada fino al vivaio**: circa 3,2 km reali verso sud-ovest fino a Contrada Annunziata,
  compressi a circa 400 m con `BOSCO_SCALA`, goccia in fondo; la zolla del Bosco si allarga.
  Area Quercus e vivaio restano a scala reale.
- **Vivaio forestale** con il Centro visite «San Nicola la Macchia» (edifici w411142982,
  w411144227, w411147963; vasche w411138854, w411138897, w411139081): etichetta, scheda solo se
  le fonti reggono (senza dire che il centro visite è aperto).
- **Base Scout Gravina 1** (w411148672), **area pic-nic** (posizione indicata dal committente)
  e **scritta «SIC DIFESA GRANDE»** in lettere bianche sul pendio, un'unica mesh.
- **Giro a piedi** su un anello reale di sentieri (`highway=path`) di 400–800 m, a scala reale.
- **Bosco che sembri vero** vicino al sentiero (querce di età diverse, sottobosco, luce), con
  `InstancedMesh` e livelli di dettaglio; alberi sfumati tra camera e figurina.
- **Suoni del bosco** con Web Audio, solo nella zolla del Bosco. Vista «bosco a piedi» nelle misure.
- Google Maps e Street View solo come riferimento visivo.

### M1, M2, M3 (al posto del blocco M; decisioni del committente del 01/10/2026)
Il blocco M si divide in tre, ognuno col suo branch e la sua PR.

#### M1 · Botromagno, strade, stadio e Fiera (`fase-3-4-m1-botromagno-strade`)
- **Botromagno**: le 40 sagome OSM `building=ruins` a ovest del ciglio diventano rovine
  realistiche (muri a secco bassi con brecce, conci caduti, tombe scavate nella roccia, buche per i
  pali delle capanne), suolo `roccia` lungo il ciglio ovest e negli scavi; il Madonna della Stella
  Resort e gli altri edifici del versante a uno o due piani coi coppi. Scheda nuova «Necropoli del
  Padre Eterno», etichette «Scavi archeologici di Botromagno» e «Padre Eterno» (senza scheda).
- **Strade**: difetti 1–6 e 8 del foglio del piano (dischi chiari agli incroci, dischi piatti in
  salita, vie sotto il terreno o sospese, decorative sopra le vie vere), anche fuori dalla gravina
  tra la Madonna della Stella e la strada del cimitero e lungo la strada del bosco. Il 7 (incrocio
  a V) resta: è così nei dati.
- **Stadio** che sembri uno stadio (campo, gradinate, tribuna coperta, muro di cinta) e **Fiera di
  San Giorgio** con le recinzioni e i padiglioni da fiera.
- **Area Quercus**: via il maneggio e i giochi (il maneggio non c'è).
- **Camera**: niente ritorno automatico dopo 4 s; torna dietro solo con «Segui il mezzo».

#### M2 · Percorsi a piedi, zone pedonali e suoni del bosco (`fase-3-4-m2-a-piedi`)
- Vivaio: zolla allargata a sud (vasca grande), anello reale V2 e sentiero fino alla Base Scout.
- Città: sentiero degli scavi (A), Parco Robinson (C, D), Via Pietro Ianora (E), scale della
  stazione (F), vialetti della Villa Comunale; Villa e Piazza della Repubblica pedonali.
- Fiera: percorso a piedi tra i padiglioni e strada fino all'ingresso dello stadio.
- Eccezioni approvate: il percorso nella Fiera e quello della Base Scout (non in OSM) solo se
  chiudono un anello; Villa e Piazza della Repubblica pedonali anche dove OSM segna `residential`.
- Suoni del bosco senza fruscio di pioggia: uccelli intonati con la radio, cicale e grilli, gufo,
  picchio, di rado cinghiale e lupi lontani; passi morbidi solo a piedi.

#### M3 · Mezzi realistici e mongolfiera (`fase-3-4-m3-mezzi-mongolfiera`)
- Auto realistiche nello stile (carrozzerie per sezioni, abitacolo col guidatore, stop, frecce,
  fari al tramonto), senza draw call in più; acceleratore valido anche con le auto nuove.
- **Mongolfiera**, quinto mezzo: giro fisso di circa 2,7 km (7 minuti) dal prato degli scavi di
  Botromagno sopra il centro storico, quota 60–150 m e mai meno di 30 m sopra tetti e terreno;
  pulsante prima/terza persona; a fine giro l'ultima auto riparte da dove è decollata.
- Prove: giro campionato ogni 5 m in `simula.mjs`, decollo, scheda, cambio mezzo e fine del giro
  in `interazioni.mjs`, vista «mongolfiera» nel punto peggiore del giro.

### N1, N2, N3 (al posto del blocco N; decisioni del committente del 03/10/2026)
Il blocco N si divide in tre, ognuno col suo branch, il suo piano breve e la sua PR. Il tetto del
peso sale a 450 KB compressi (sezione 3); triangoli e draw call restano quelli di prima.

#### N1 · Centro storico vero (`fase-3-4-n1-centro-storico`)
- **Salite e discese vere** (scelta del committente fra due proposte): il terreno del centro storico
  segue le quote reali Copernicus **come guida** (smussate, senza le celle vicine al ciglio, corrette
  per i tetti e ancorate a ciglio, ponte, scalinate e rioni) invece dell'altopiano quasi piatto;
  vie del mezzo entro il 18%; canyon, cigli, falesia, gradoni e discesa dei rioni restano a mano.
- Effetti che fanno sentire la pendenza: camera più bassa in salita e in discesa, case con lo
  zoccolo a valle e i gradini alle porte, muretti e ringhiere dove la via si stacca dal terreno.
- **Strade**: chianche, asfalto e ciottoli disegnati dallo shader secondo la superficie OSM; tombini.
- **Edifici**: balconi con ringhiere, portoni in legno, davanzali, cornicioni, pluviali, comignoli,
  vasi di fiori; istanziati e solo nella versione vicina dei riquadri.
- **Arredo**: le 6 fontanine e le 3 panchine OSM, alberelli e fioriere solo dove le foto li mostrano.

#### N2 · Facciate di chiese e scuole (`fase-3-4-n2-facciate`)
- Santa Teresa, Santa Sofia, San Nicola, Addolorata (e Santa Lucia, se serve) rifatte sulle foto;
  ritocchi alle chiese già rifatte dove le foto mostrano differenze; chiese della città coi campanili
  se si vedono. Ogni elemento deve vedersi in una foto, altrimenti resta semplice.
- Scuole più riconoscibili: ingresso coi gradini, finestre a nastro, scale antincendio, palestra,
  cancello; la scritta col nome solo se si vede su Street View, generata dal codice.

#### N3 · Cartolina, giro guidato e ritocchi (`fase-3-4-n3-cartolina-giro`)
- **Cartolina**: immagine ad alta risoluzione con cornice (Gravina in Puglia, luogo, indirizzo del
  sito, attribuzioni OSM e Copernicus in breve), Web Share sul telefono; credito deciso dal committente.
- **Giro guidato dei monumenti**: il mezzo sceglie le vie, anche i tratti a piedi; «Prossima
  tappa», scheda a ogni tappa, «Esci dal giro». Prova sulle prime tre tappe in `interazioni.mjs`.
- **Ritocchi**: camera dopo il teletrasporto (`rig.snap`), schede lunghe in verticale (anche quella
  dei Caduti in panchina), schermata iniziale in orizzontale sul telefono, Street View rimasto da M2,
  memoria JS su PC (prima le strutture dati, senza toccare la città).

---

## 8. Domande aperte per il committente

| # | Domanda | Serve a |
|---|---|---|
| 1 | Codice di verifica di Google Search Console | A |
| 2 | "La caccia": cosa si intende? C'è un parco "La Caccia" vicino a Largo Cappuccini | E |
| 3 | La zona industriale è il P.I.P. (Zona Artigianale)? Se sì, strada a scala reale | C, F |
| 4 | Porta San Michele: modellarla com'è oggi (imbocco di Via Santa Cecilia con nicchia e statua), senza ricostruire l'arco perduto? | D |
| 5 | Fondovito o Fondovico sulla targa? | D |
| 6 | Casino Meninni e "case rosa": quale edificio o quale via? | E |
| 7 | Castello Svevo dentro il diorama, con la sua via reale? | C |
| 8 | Quote Copernicus già nel blocco C per la città moderna? (consigliato: costano solo dati) | C |
| 9 | Anteprima social, sitemap e robots come file separati: eccezione al "file unico"? | A |

---

## 9. Lavoro in parallelo su due chat

*Concluso il 28/09/2026: le due cartelle parallele sono state chiuse e si lavora di nuovo
nella cartella principale, un blocco alla volta. La sezione resta come promemoria.*

**Cartelle di lavoro** (git worktree dello stesso repository; la cartella principale
`progetto gravina 3d` resta su `main` e non ci si lavora):

| Chat | Cartella | Blocchi, in ordine |
|---|---|---|
| **Interfaccia e fonti** | `~/Desktop/gravina-3d-interfaccia` | A → B → ricerca delle fonti per D ed E (`docs/SCHEDE_FASE_3_4.md`) → D ed E dopo che C è su `main` |
| **Città** | `~/Desktop/gravina-3d-citta` | C → F → G |

**Chi tocca cosa in `index.html`**, per ridurre i conflitti:
- Interfaccia: `<head>`, schermata iniziale e CSS relativo, sezione 9 (camera), pulsanti
  dell'HUD, `LANDMARKS` (testi), sezione 6d dopo C. Nei test: `interazioni.mjs`, `foto.mjs`.
- Città: `genera_dati.py`, `GEO`, sezioni 4–6c, 10–10b (mappe), 12–13 (scena, qualità, avvio).
  Nei test: `simula.mjs`, `prestazioni.mjs`.
- `CONFIG`: ognuna aggiunge solo le sue chiavi.
- Documenti: ognuna aggiorna solo le righe e le sezioni del suo blocco.

**Unione su `main`** (solo con l'approvazione del committente):
- Prima di chiedere l'unione: `git fetch origin && git merge origin/main`, risolvere i
  conflitti, rilanciare le prove.
- Ordine previsto: A, B, poi C. D ed E partono da un `main` che contiene già C.

**Prove Playwright: una sola alla volta su tutto il Mac.** Si usa un lucchetto condiviso:

```bash
cd tools/test
find /tmp -maxdepth 1 -name gravina3d-prove.lock -mmin +30 -exec rmdir {} \; 2>/dev/null
until mkdir /tmp/gravina3d-prove.lock 2>/dev/null; do sleep 10; done
npm run simula; rmdir /tmp/gravina3d-prove.lock
```

Stesso schema per `npm run interazioni`, `node foto.mjs …` e le altre prove.

**Server di anteprima**: porta 3001 per l'interfaccia, 3002 per la città (la 3000 è già
occupata). In ogni cartella c'è un `.claude/launch.json` locale.

**Ambiente** (già preparato nelle due cartelle, fuori da git):
- `tools/test/node_modules` e `.venv` sono collegamenti a quelli della cartella principale.
  Non reinstallare Playwright: con Node 26 `npx playwright install` si blocca, e Chromium è già
  nella cache.
- Nella cartella "città", `tools/.cache/` contiene già:
  - i dati Overture della città (BBOX `(16.395, 16.455, 40.800, 40.840)`: impostare quel BBOX in
    `genera_dati.py` per riusarli);
  - `ampia/` con segment, connector, place e land_use dell'area ampia;
  - `dem/` con la tessera Copernicus;
  - `esplora/` con gli script di prova (`prova_rete.py`, `scarica.py`) e le mappe di controllo.
- Le foto di Street View restano solo in `~/Desktop/progetto gravina 3d/riferimenti/`: non vanno
  caricate su GitHub.

---

## Fonti usate per il piano

- Porta San Michele: [GravinaLife, porte fortificate](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/le-antiche-porte-fortificate-di-gravina/), [MurgiaTime](https://www.murgiatime.it/murgia/index.php?option=com_content&view=article&id=13901:il-san-michele-della-porta-1799-2020&catid=89:gravina-storia&Itemid=541), [Algramà](https://www.algrama.it/algramanews/riposta-nella-nicchia-la-statua-di-san-michele-del-1799-gravina-fu-salva-dalle-orde-del-cardinale-ruffo/), [Giardini storici della Puglia](https://www.giardinidellapuglia.it/i-giardini/bari/gravina-in-puglia/)
- Busto di Canio Musacchio: [GravinaLife](https://www.gravinalife.it/notizie/imbrattato-il-monumento-a-canio-musacchio/), [MurgiaTime](https://www.murgiatime.it/murgia/index.php?option=com_content&view=article&id=17912:vernice-sul-busto-di-canio-musacchio-un-offesa-alla-citta&catid=73:gravina-cronaca&Itemid=571)
- Monumento ai caduti: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/il-monumento-ai-caduti-tra-storia-leggenda-e-poesia/), [GravinaOggi](https://www.gravinaoggi.it/monumento_ai_caduti_della_grande_guerra_1915-1918.html), [Pietre della Memoria](https://www.pietredellamemoria.it/pietre/monumento-ai-caduti-della-grande-guerra-gravina-in-puglia-ba/), [Centenario 1914-1918](http://luoghi.centenario1914-1918.it/it/monumento/monumento-ai-caduti-della-prima-guerra-mondiale-4082)
- Fondovito/Fondovico: [GravinaOggi, rione Fondovito](https://www.gravinaoggi.it/rione_fondovito.html), [Stanze Orsini](https://www.stanzeorsini.it/rioni-piaggio-e-fondovico/), [FAI](https://fondoambiente.it/luoghi/rioni-piaggio-e-fondovico)
- Casino dei Meninni: [FAI](https://fondoambiente.it/luoghi/casino-dei-meninni), [GravinaLife](https://www.gravinalife.it/notizie/casino-di-meninni-interrogazione-del-consigliere-conca)
- Fiera di San Giorgio: [Stanze Orsini](https://www.stanzeorsini.it/la-fiera-san-giorgio-gravina-puglia/), [GravinaOggi](https://www.gravinaoggi.it/la_fiera_di_gravina_ieri.html), [sito della Fiera](https://fierasangiorgiogravina.it/)
- Stadio: [Wikipedia, FBC Gravina](https://it.wikipedia.org/wiki/FBC_Gravina), [GravinaLife](https://www.gravinalife.it/notizie/lavori-di-completamento-dello-stadio-vicino/)
- Stazioni: [Wikipedia, stazione FAL](https://it.wikipedia.org/wiki/Stazione_di_Gravina_in_Puglia_(FAL)), [Wikidata RFI Q3969752](https://www.wikidata.org/wiki/Q3969752)
- Parco Robinson: [GravinaOggi](https://www.gravinaoggi.it/parco_robinson.html)
