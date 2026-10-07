# Gravina 3D

Diorama 3D interattivo in stile low-poly del centro storico di **Gravina in Puglia**,
costruito sulle **vie, gli edifici e il torrente reali**.
Progetto open source di **Giuseppe Cassano** ([github.com/giuseppecassano5bit](https://github.com/giuseppecassano5bit)).

Appena si apre, il mezzo aspetta accanto al **Ponte Acquedotto**. Scegli con che cosa
girare: **Fiat Panda 4x4 del 1999**, **Audi RS6 Avant**, **Lamborghini Huracán**,
**trattore John Deere** o **mongolfiera**. Le auto percorrono da sole le vie reali del centro storico, e a
ogni incrocio reale scegli tu quale via prendere. Nel centro storico alcuni cartelli portano
**a piedi** su passaggi e scalinate reali: il mezzo si ferma, prosegue una figurina, e il mezzo
la aspetta al tratto carrabile successivo. La camera gira da sola attorno al mezzo, e puoi
girarla anche tu trascinando; una radio suona brani ambient originali, generati dal diorama.
In mongolfiera si decolla da Botromagno per un giro di sette minuti sopra la necropoli, il Ponte
Acquedotto e il centro storico, con la vista esterna o dalla cesta.
Puoi fermarti quando vuoi: dal menu di pausa cambi mezzo oppure tocchi un luogo sulla mappa e
ti teletrasporti lì.
Tutto sta in **un unico file HTML**: la geometria è procedurale e i dati geografici sono
incorporati nel file, senza modelli, texture o GeoJSON caricati a runtime.

## Come si apre

Apri `index.html` in un browser moderno (Chrome, Edge, Firefox o Safari recenti), anche su
telefono o tablet. Serve una connessione a Internet: Three.js e i font vengono caricati da CDN.

In alternativa puoi avviare un piccolo server locale:

```bash
npx serve .
```

### Pubblicarlo online (GitHub Pages)

Il repository è pubblico, quindi il diorama può avere un indirizzo raggiungibile da qualsiasi
dispositivo, gratis:

1. porta il lavoro sul branch `main` (unisci la pull request del branch di lavoro);
2. su GitHub apri **Settings → Pages**;
3. in **Build and deployment** scegli **Deploy from a branch**, branch `main`, cartella `/ (root)`, e salva.

Dopo un paio di minuti il diorama è su `https://giuseppecassano5bit.github.io/gravina-3d/`.
Non serve nessun passaggio di compilazione: `index.html` è già il sito (il file `.nojekyll`
dice a GitHub di pubblicarlo così com'è). Da lì in poi ogni push su `main` aggiorna il sito.

### Ricerca su Google e anteprime nei social

`index.html` ha già titolo e descrizione per i motori di ricerca, i meta Open Graph e Twitter
per le anteprime (l'immagine è `og-image.jpg`) e i dati strutturati JSON-LD (sito, opera,
luogo e autore). Il pannello **Il progetto** della schermata iniziale è testo vero, leggibile
anche dai motori di ricerca.

Fatto il 28 settembre 2026: la proprietà è verificata e la sitemap inviata. I passi, se mai
servisse ripeterli (per esempio con un altro account):

1. apri [Google Search Console](https://search.google.com/search-console) e aggiungi una
   proprietà di tipo **Prefisso URL**: `https://giuseppecassano5bit.github.io/gravina-3d/`;
2. come metodo di verifica scegli **Tag HTML** e copia il `<meta name="google-site-verification" …>`
   nel `<head>` di `index.html`, poi porta la modifica su `main`;
3. quando il sito è aggiornato premi **Verifica**;
4. in **Sitemap** invia `sitemap.xml`.

Due file stanno fuori da `index.html` perché servono solo a social e motori di ricerca:
`og-image.jpg` (1200×630, si rigenera con `npm run anteprima` in `tools/test`) e `sitemap.xml`
(aggiornare `lastmod` quando il sito cambia molto). Non c'è `robots.txt`: su GitHub Pages il
sito sta in `/gravina-3d/` e i motori di ricerca leggono solo quello alla radice del dominio
(`giuseppecassano5bit.github.io/robots.txt`); senza, tutto è già indicizzabile.

### Lavorare in locale con Claude Code

Tutto per continuare sul proprio computer è nel repository:

* [`CLAUDE.md`](CLAUDE.md): regole e vincoli del progetto, letti da Claude Code all'avvio;
* [`docs/LAVORARE_IN_LOCALE.md`](docs/LAVORARE_IN_LOCALE.md): cosa installare, prove, server locale, pubblicazione;
* [`docs/DA_FARE.md`](docs/DA_FARE.md): cosa resta da fare e le decisioni aperte.

## Comandi

| Azione | Desktop | Mobile |
|---|---|---|
| Scegliere il mezzo | clic su una scheda | tocca una scheda |
| Partire | pulsante **Parti** | tocca **Parti** |
| Scegliere la via all'incrocio | <kbd>←</kbd> <kbd>→</kbd> (oppure <kbd>A</kbd> <kbd>D</kbd>) | tocca un cartello marrone (in verticale anche le frecce ai lati) |
| Tornare alla via più dritta | <kbd>↑</kbd> (oppure <kbd>W</kbd>) | tocca il cartello con la freccia dritta |
| Fermarsi (pausa) | <kbd>P</kbd>, <kbd>Spazio</kbd> o il pulsante **Pausa** | tocca **⏸** o la minimappa |
| Ripartire | <kbd>P</kbd>, <kbd>Spazio</kbd>, <kbd>Esc</kbd> o **Riprendi** | tocca **Riprendi** |
| Cambiare mezzo | nel menu di pausa | nel menu di pausa |
| Teletrasportarsi | in pausa: clic su un luogo della mappa e **Vai qui**, su un'etichetta del diorama o su un nome dell'elenco | gli stessi, al tocco |
| Andare a piedi | scegli un cartello col pedone («a piedi») | tocca un cartello col pedone |
| Girare la camera | trascina col mouse; rotella per avvicinarsi o allontanarsi; **Segui il mezzo** per tornare dietro | trascina con un dito; due dita per lo zoom |
| Musica | <kbd>M</kbd> o il pulsante **Musica**; poi brano successivo e volume | tocca **♪** |

Il mezzo avanza da solo. Se non scegli, agli incroci prosegue sulla via più dritta.
Il menu di pausa compare solo a mezzo fermo; se cambi app o scheda il viaggio va in pausa da
solo. Il browser ricorda l'ultimo mezzo scelto.

### I mezzi

Dal blocco M3 le auto sono **realistiche nello stile**: carrozzeria per sezioni con i passaruota,
vetri trasparenti con l'abitacolo e il guidatore seduto, ruote con la spalla e i cerchi di ogni
modello, fari al tramonto, **stop** quando rallentano e **frecce** prima delle svolte.

| Mezzo | Carattere nel diorama |
|---|---|
| Fiat Panda 4x4 (1999) | rossa, squadrata, con protezioni in plastica, barre sul tetto e cerchi in lamiera; passo tranquillo |
| Audi RS6 Avant | familiare grigia con parafanghi allargati, cerchi a dieci razze e pinze rosse; brillante |
| Lamborghini Huracán | arancione, a cuneo, con i fari a Y e le pinze gialle; la più svelta (sempre a passo da centro storico) |
| Trattore John Deere | verde e giallo, ruote tassellate e sbuffi di fumo; il più lento, e la camera sale un po' |
| Mongolfiera | pallone a spicchi nei colori del diorama con una fascia blu, cesta di vimini, fiamma e soffio del bruciatore; vola su un **giro fisso** di 2,7 km da Botromagno, sempre almeno 30 m sopra tetti e monumenti, e non segue le vie (un'eccezione come il Ponte Acquedotto). Il pulsante **Vista dalla cesta / Vista esterna** passa dalla prima alla terza persona. Alla fine del giro si riparte con l'ultima auto dalla via più vicina al decollo; i luoghi lontani dal giro (il bosco, il P.I.P., il Castello, il Casino di Meninni) si raggiungono scendendo e prendendo l'auto |

## Com'è fatto

Il file `index.html` è diviso in sezioni numerate e commentate:

| # | Sezione | Contenuto |
|---|---|---|
| 0 | Configurazione | tutti i parametri (velocità, frenata, camera, sole…) |
| 1 | Utilità | matematica, rumore procedurale, geometria piana |
| 2 | Geografia | conversione da latitudine/longitudine a metri |
| 3 | Dati | blocco `GEO` generato (vie, incroci, edifici, torrente…) e monumenti curati |
| 4 | Gravina e terreno | canyon sul corso reale del torrente, falesie, gradoni e discesa dei rioni Piaggio e Fondovico (`RIONI`) |
| 5 | Rete stradale | vie reali come spline, uscite agli incroci, cartelli, controlli |
| 6 | Mondo | terreno, strade, Ponte Acquedotto ad archi, edifici reali con le case a gradoni dei rioni, archi sulle vie, Cattedrale, chiese rupestri, grotte, abitazioni rupestri, alberi |
| 6e | Città a riquadri | la zolla in riquadri da 240 m (una mesh ciascuno): terreno a 5/15/30 m (7,5 m da vicino lungo le vie difficili), vie ed edifici della città, binari, alberi, fianco della zolla; finestre e marciapiedi disegnati dallo shader; da lontano una versione semplificata nella stessa mesh (livelli di dettaglio, blocco I); la maglia adattata alle vie (`MeshFit`, blocco M1) |
| 6d | Dettagli | portali delle chiese, portale del Purgatorio, palazzi, Fontana della Stella, scalinate, belvederi, lanterne; dal blocco M1 le rovine e le tombe di Botromagno, lo stadio e la Fiera |
| 7 | Mezzi | Panda 4x4, RS6, Huracán e trattore per sezioni (`Shop.loft`), con abitacolo, guidatore, luci da uniform e 4 mesh per mezzo; mappa d'ambiente al tramonto solo per i mezzi |
| 7c | Mongolfiera | pallone a 14 spicchi, cesta, funi, bruciatore con la fiamma, pilota e visitatore (circa 2 400 triangoli) |
| 7 | Figurina | il visitatore a piedi (`Walker`), circa 200 triangoli in una mesh |
| 8 | Conducente | movimento automatico, incroci, pausa con frenata, tratti a piedi (sosta all'imbocco, mezzo che aspetta all'uscita), sosta in panchina alla Villa |
| 8b | Volo | il giro della mongolfiera (`Volo`, `Flight`): curva chiusa, quota sopra tetti e monumenti, decollo e atterraggio |
| 9 | Camera | vetrina a due tempi (primo piano e campo lungo sulle arcate), inseguimento che scavalca i tetti nei vicoli, giro automatico attorno al mezzo, camera libera, panoramiche, vista dall'alto in pausa; in mongolfiera giro largo attorno al pallone e vista dalla cesta |
| 10–11 | Interfaccia | minimappa vettoriale, mappa della pausa con zoom e trascinamento, luoghi per gruppi, scelta del mezzo, targa, cartelli, schede, teletrasporto |
| 11b | Radio | sei brani ambient generati con Web Audio, senza file audio |
| 11c–11d | Suoni | suoni del bosco (uccelli, grilli, cicale, allocco, picchio, cinghiale, lupi lontani) e soffio del bruciatore della mongolfiera, generati con Web Audio |
| 12–13 | Scena e avvio | cielo al tramonto, luci, ombre agganciate ai texel, qualità adattiva, ciclo principale |

Il documento di progetto completo è in [`docs/DESIGN.md`](docs/DESIGN.md); cosa resta da fare
è in [`docs/DA_FARE.md`](docs/DA_FARE.md).

## Dati geografici

Vie, incroci, sagome degli edifici, corso del torrente, mura e luoghi d'interesse vengono da
**[Overture Maps](https://overturemaps.org)** (release 2026-09-23.1), che li deriva in gran
parte da **[OpenStreetMap](https://www.openstreetmap.org/copyright)**.

Dalla fase 3.4 la zolla contiene **la città intera** (2,9 × 3,1 km, dal cimitero alla stazione,
dallo Sportland al Castello Svevo):

* **87 km di vie percorribili** (1 461 tratti, 908 incroci) e 240 vie cieche reali disegnate ma
  non percorribili; la sterrata del Castello Svevo si percorre;
* **percorsi a piedi** nel centro storico (blocco G): 19 tratti reali di marciapiede, passaggio
  pedonale o scalinata (584 m), solo dove si collegano ad altre vie; le 5 scalinate che nei dati
  finiscono nel vuoto si guardano soltanto;
* **due appendici** (blocco F): la zona artigianale **P.I.P.**, a est, con le sue vie a scala
  reale, e il **Bosco Difesa Grande**, a sud (blocco L: area Quercus, vivaio forestale, Base
  Scout, area pic-nic con la scritta «SIC DIFESA GRANDE», 524 m di sentieri reali a piedi, bosco
  dal poligono OSM del Bosco Difesa Grande e suoni del bosco generati dal codice);
* **scuole, chiese e luoghi della città** (blocco E): 16 scuole sull'edificio reale, le chiese
  della città con portale e croce, il Casino di Meninni, le case rosa, schede per Fiera di San
  Giorgio, stadio, stazione FAL e Casino; le vie del mezzo stanno entro il 18% in tutta la città;
* **2 045 edifici della città** (più i 518 del centro storico) con l'altezza stimata per tipo e superficie (le stime Microsoft
  sono troppo basse e si scartano);
* **quote reali** dal modello di elevazione **Copernicus DEM GLO-30**, smussate (il DSM comprende
  tetti e alberi). Nel centro storico il canyon, i cigli e i gradoni restano disegnati a mano; le
  quote reali fanno da **guida** per la discesa dei rioni Piaggio e Fondovico verso la gravina
  (`GEO.rioni`, una misura ogni 15 m lungo il ciglio). A 30 m di maglia il canyon è sfocato e
  "sbava" dentro le case, quindi se ne usa meno della metà: il Piaggio scende fino a 17 m, il
  Fondovico circa 12 m. Nel centro storico le vie del mezzo non superano il 18% (blocco D,
  `CONFIG.road.maxGrade`); a sud l'altopiano del centro si raccorda alle quote reali in 220 m.
  Dal blocco N1 anche **l'altopiano del centro storico segue le quote vere** (`GEO.centro`): dal DSM
  grezzo si prende un percentile basso dei soli pixel a più di 120 m dal ciglio (via i tetti e il
  canyon sfocato), lo si smussa e lo si prolunga piatto fino al ciglio. Senza esagerazione: la
  Cattedrale resta a quota 0, Piazza della Repubblica sta 4 m più su, San Francesco 10 m; le vie del
  mezzo in piano (entro il 2%) passano dall'84% al 36% della lunghezza, e nessuna supera il 18%;
* uso del suolo, binari FAL e RFI e luoghi con nome da OpenStreetMap, letti con l'**Overpass
  API** (monumenti, chiese, stazioni, parchi). Query piccole a parte, ognuna con la sua cache in
  `tools/.cache/`: il Bosco (`bosco.json`), le rovine e gli scavi di Botromagno (`rovine.json`),
  lo stadio e la Fiera (`stadio_fiera.json`).

**A piedi.** Il mezzo percorre solo vie reali. Marciapiedi, passaggi pedonali e scalinate del
centro storico si percorrono **a piedi**, con una figurina: il mezzo si ferma all'imbocco e la
aspetta al tratto carrabile successivo. Nella realtà ci arriverebbe per altre vie: nel diorama
compare lì, fuori dall'inquadratura. In fondo a Via giudice Montea (verso la scalinata), Via
Civita e Via Matteotti non c'è spazio per l'inversione a goccia: lì si prosegue per forza a piedi.
Nel Fondovito (blocco N2) la Calata Grotte San Michele, che nella realtà non si fa in auto, è tutta
pedonale anche se OSM la segna `residential`; dalla terrazza di San Michele un ponticello (non in OSM:
satellite e foto da drone) porta a una goccia per la figurina sul promontorio delle mura, e dai Gradoni
San Giovanni Battista un raccordo di 18 m attraversa l'area pedonale di Piazza Pellicciari fino a Via
Marconi.

**Tracciato reale compresso.** Il Bosco Difesa Grande è a circa 6 km dalla città: la strada che
ci porta segue il tracciato reale (la provinciale Matera–Gravina, poi la strada verso il bosco,
circa 5,3 km secondo Overture Maps) **ridotto in scala a circa 950 m** fino all'area Quercus.
Dal blocco L prosegue con la stessa regola fino al vivaio forestale, all'incrocio con Contrada
Annunziata: 3,2 km di strada reale (OSM) diventano 674 m, e in fondo c'è l'inversione a goccia.
Gli angoli di svolta restano quelli reali, si accorciano solo le lunghezze. Le zone attorno
all'area Quercus e al vivaio restano **a scala reale** (edifici, campi, vasche e sentieri di OSM),
e i sentieri del bosco non si comprimono. È un'eccezione come il Ponte Acquedotto: nessun'altra
via è compressa, e la strada del P.I.P. resta a scala reale. La scheda del Bosco lo dice al
visitatore. Il parcheggio «Terra Rossa», 700 m più giù lungo la strada, resta a lato della strada
compressa, ritagliato fuori dall'area dei campi.

**Acceleratore.** Sul computer, tenendo premuto **Shift** il mezzo va 1,8 volte più veloce; agli
incroci rallenta da solo e il cartello compare prima. Sul telefono non c'è, per non rischiare
rallentamenti.

Per rigenerarli (per esempio dopo aver migliorato la mappa di Gravina su OpenStreetMap):

```bash
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/genera_dati.py --anteprima tools/anteprima.png
```

Lo script scarica solo i pochi MB che riguardano Gravina (la prima volta, con la città intera
e la tessera Copernicus di 39 MB, servono una decina di minuti; poi circa 18 s dalla cache in
`tools/.cache/`), costruisce la rete stradale senza vicoli ciechi e riscrive il blocco `GEO`
dentro `index.html`. Le scelte (vie cieche da
conservare, ciglio del canyon, area del diorama) sono costanti commentate in cima allo script.

Oltre alle vie esporta le **scalinate reali** (in OpenStreetMap `highway=steps`: la scalinata
di Via giudice Montea, i Gradoni San Giovanni Battista e altre cinque), che nel diorama sono
gradini di tufo da guardare e non si percorrono.

**Altezze degli edifici.** In OpenStreetMap mancano quasi sempre: nell'area del diorama il
numero di piani c'è solo per il Museo Santomasi (3 piani). Overture aggiunge le altezze stimate
dalle immagini aeree (Microsoft ML Buildings) per 35 edifici, ma nel centro storico sono spesso
assurde (1,5-2,5 m per un condominio): lo script le scarta. Le altezze mancanti le stima il
diorama per zona: uno o due piani nei rioni Piaggio e Fondovico, due o tre nel centro storico,
tre-cinque nei quartieri moderni.

Lo script **libera anche le vie dagli edifici**: ricentra ogni via tra le facciate, la
restringe nei vicoli stretti (mai sotto 3,4 m), ritaglia le sagome lungo la carreggiata e
trasforma in **archi** i corpi sopraelevati reali che scavalcano una via (in OpenStreetMap
hanno `level = 1`, come L'Arc D' Bench). Risultato attuale: nessun edificio sulla
carreggiata (la prova `npm run simula` lo verifica sulla geometria disegnata), 5 archi, lo 0,6%
della superficie costruita ritagliato.

Non servono strumenti di scraping: i dati arrivano dal bucket pubblico di Overture Maps e le
notizie storiche da fonti pubbliche citate qui sotto.

## Personalizzare

* **Punto di partenza**: costante `START` in `index.html` (metri prima della testata est del ponte, oggi 12).
* **Vetrina**: `CONFIG.camera.showroom` (durate del primo piano e del campo lungo, pose del campo lungo).
* **Rioni**: costante `RIONI` (tratto di ciglio, larghezza e profondità della discesa verso la gravina).
* **Mezzi**: array `VEHICLES` (nome, colore, ritmo `pace`, sagoma per i menu) e le funzioni in `VehicleFactory`.
* **Velocità e frenata**: `CONFIG.drive`.
* **Camera**: `CONFIG.camera` (altezza, distanza, quanto può salire sopra i tetti).
* **Monumenti e schede**: array `LANDMARKS`.
* **Vie**: si modificano in OpenStreetMap o nello script di generazione, non a mano nel blocco `GEO`.

## Strumenti per sviluppatori

Aggiungi `?debug` all'indirizzo (per esempio `index.html?debug`) per vedere fps, triangoli e
posizione sulla rete, e per avere in console l'oggetto `window.gravina`. Esempi:

```js
gravina.driver.simulate(3600)          // un'ora di guida con scelte casuali: verifica che il mezzo non si blocchi mai
gravina.advance(5)                     // fa avanzare la simulazione di 5 secondi senza disegnare
gravina.placeAt(60, 310, [-1, -0.5])   // mette il mezzo sulla via più vicina a (est, nord), diretto verso ovest
gravina.useVehicle('deere')            // cambia mezzo: panda, rs6, huracan, deere, balloon
gravina.pause(); gravina.goTo('duomo') // pausa e teletrasporto verso un monumento (id di LANDMARKS)
```

Prove automatiche con Playwright: vedi [`tools/test/README.md`](tools/test/README.md). Le misure di
prestazioni (triangoli, draw call, tempi di costruzione, memoria) si prendono con
`node prestazioni.mjs` in `tools/test`, con la GPU vera; i difetti delle vie nei riquadri (vie
sotto il terreno o sospese, dischi sfasati, decorative sovrapposte) con `node difetti.mjs`.

## Stato del progetto

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ |
| 2 | Base: rete stradale, auto, incroci, camera, interfaccia | ✅ |
| 2b | Dati reali: vie e incroci reali, edifici, torrente e cigli, ponte ad archi | ✅ |
| 2c | Vie libere dagli edifici e archi reali; quattro mezzi a scelta; partenza dal ponte; pausa con cambio mezzo, mappa e teletrasporto; camera che scavalca i tetti; dettagli dei monumenti; versione mobile | ✅ |
| 3 | Architettura e fedeltà: Cattedrale e Purgatorio sulle fonti, chiese rupestri scavate, rioni a gradoni con scalinate e abitazioni rupestri, altezze per zona, schede di altre cinque chiese, vetrina sulle arcate | ✅ in revisione |
| 3.4 | Gravina oltre il centro storico: città intera (C), strade per il Bosco e il P.I.P. (F), percorsi a piedi, quote reali del centro storico, camera attorno al mezzo e radio ambient (G), spazio sul telefono (I), centro storico (D), luoghi della città, scuole e chiese (E), il Bosco da vicino (L) e acceleratore su PC; Botromagno, strade, stadio e Fiera (M1); percorsi a piedi, zone pedonali, sottopassi, parchi, Monumento ai Caduti, Cola Cola e suoni del bosco (M2); auto realistiche nello stile e mongolfiera (M3) | ⏳ |
| 4 | Rifinitura: luci, prove su telefoni reali, restyling | ⏳ |

## Crediti, licenze e marchi

* **Autore**: Giuseppe Cassano ([github.com/giuseppecassano5bit](https://github.com/giuseppecassano5bit)).

* **Dati cartografici** (blocco `GEO` in `index.html`): © OpenStreetMap contributors, disponibili
  sotto [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/). Sono un
  database derivato e restano sotto ODbL; l'attribuzione è visibile nella pagina.
* **Musica**: i sei brani della radio sono composizioni originali generate dal codice (Web Audio),
  senza campioni né brani di terzi.
* **Quote del terreno** della città e della campagna (`GEO.dem`), e la discesa dei rioni del centro
  storico (`GEO.rioni`): modello di elevazione
  Copernicus DEM GLO-30, distribuito gratuitamente con la
  [licenza del Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).
  L'attribuzione richiesta dall'art. 6(b) è sempre visibile nella pagina (schermata iniziale,
  mappa della pausa e, in breve, sotto la minimappa):
  "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space
  GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved".
  Come chiede l'art. 6(c): "The organisations in charge of the Copernicus programme by law or
  by delegation do not incur any liability for any use of the Copernicus WorldDEM-30".
* **Codice**: la licenza è ancora da scegliere (per esempio MIT).
* **Librerie e caratteri**: [Three.js](https://threejs.org) (MIT) da CDN; Marcellus SC, Barlow e
  Barlow Semi Condensed (SIL Open Font License) da Google Fonts.
* **Fiat** e **Panda**, **Audi** e **RS6**, **Lamborghini** e **Huracán**, **John Deere** (e i
  suoi colori verde e giallo) sono marchi dei rispettivi proprietari. I mezzi del diorama sono
  interpretazioni stilizzate non ufficiali e non riproducono loghi. Prima di un uso commerciale
  o promozionale, verificate i diritti.

## Fonti

Notizie storiche e posizioni dei monumenti da fonti pubbliche, tra cui:

* Ponte Acquedotto: [Wikipedia (EN)](https://en.wikipedia.org/wiki/Ponte_Madonna_della_Stella), [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/il-ponte-acquedotto-settecentesco-orsiniano-della-madonna-della-stella/), [Viaggiamo.it](https://www.viaggiamo.it/ponte-acquedotto-di-gravina-di-puglia-la-storia/)
* Cattedrale: [Wikipedia](https://it.wikipedia.org/wiki/Concattedrale_di_Santa_Maria_Assunta_(Gravina_in_Puglia)), [Wikipedia (EN)](https://en.wikipedia.org/wiki/Gravina_Cathedral), [Carta dei Beni Culturali della Regione Puglia](https://www.cartapulia.it/en/esplora-la-carta/-/rcp/ricercaCartapulia_INSTANCE_1yi8w0oVRO9u/dettaglio/5990) (orientamento, facciata tripartita con tre portali e rosone a 24 raggi, campanile sul profilo sud, cappellone), [Museo Capitolare, campanile](https://www.museocapitolaregravina.it/campanile-cattedrale/) (quattro ordini, cipollone del 1698), [Visit Puglia](https://www.visit-puglia.it/at/11/luogosacro/786/it/Cattedrale-di-Santa-Maria-Assunta-Gravina-in-Puglia-(Bari)) (portale sud e secondo rosone attiguo al campanile; blocco D: campanile in fondo a est del fianco sud, contro la Curia, e rosone subito a ovest, verificati su Street View e sulle [foto di Piazza Benedetto XIII](https://commons.wikimedia.org/wiki/File:Piazza_Benedetto_XIII_-_Duomo.jpg) di Wikimedia Commons), [Catalogo generale dei Beni Culturali](https://catalogo.beniculturali.it/detail/ArchitecturalOrLandscapeHeritage/1600180859), [GCatholic](https://gcatholic.org/churches/italy/1312.htm), [GravinaOggi, struttura architettonica](https://www.gravinaoggi.it/_la_struttura_architettonica.html)
* Chiesa del Purgatorio: [FAI, portale](https://fondoambiente.it/luoghi/portale-chiesa-purgatorio) (pilastri a torri sovrapposte sugli orsi, timpano spezzato con gli scheletri, stemma ed epigrafe), [Wikipedia](https://it.wikipedia.org/wiki/Chiesa_di_Santa_Maria_del_Suffragio_(Gravina_in_Puglia)), [GravinaOggi](https://www.gravinaoggi.it/chiesa-ducale-santa-maria-del-suffragio--o-purgatorio-.html), [Wikidata](https://www.wikidata.org/wiki/Q55163985)
* Rioni Piaggio e Fondovico (sulla targa «Fondovito», scelta del committente; il nome viene dal culto di San Vito, [GravinaOggi](https://www.gravinaoggi.it/rione_fondovito.html)): [Stanze Orsini](https://www.stanzeorsini.it/rioni-piaggio-e-fondovico/), [FAI](https://fondoambiente.it/luoghi/rioni-piaggio-e-fondovico?ldc=), [GravinaOggi](https://www.gravinaoggi.it/i-rioni-storici-piaggio-e-fondovito-a-gravina.html) (scalinate di tufo, circa ottanta ambienti scavati)
* Madonna della Stella: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/santuario-rupestre-madonna-della-stella/) (esterno imbiancato, campanile a vela in mattoni, corpo basso a una falda), [Museo Capitolare](https://www.museocapitolaregravina.it/madonna-della-stella/), [Il Tacco di Bacco](https://iltaccodibacco.it/puglia/guida/7825/)
* San Michele delle Grotte: [Museo Capitolare](https://www.museocapitolaregravina.it/san-michele-delle-grotte/) (cinque navate e 14 pilastri, il vestibolo di caverne naturali, il Cristo Pantocratore, l'altare con la statua di San Michele nella navata centrale, teschi e ossa in una grotta accanto attribuiti dall'iscrizione ai gravinesi uccisi dai Saraceni nel 999), [Wikipedia](https://it.wikipedia.org/wiki/Chiesa_rupestre_di_San_Michele) (14 pilastri, cinque navate, il Pantocratore, l'incursione del 999), [Showcaves](https://www.showcaves.com/english/it/caves/SanMicheleGravina.html) (in fondo a Calata Grotte San Michele; grotta naturale allargata a portico con grandi pilastri monolitici; scala di tufo che sale; cinque navate e 14 pilastri), [Italy for Movies](https://www.italyformovies.com/location/detail/17491/crypt-of-st-michael-grotta-di-san-michele-gravina-in-puglia) (cinque navate e 14 pilastri, il Pantocratore, l'ossario e il 999, «la prima cattedrale»), [FAI, Rioni Piaggio e Fondovico](https://fondoambiente.it/luoghi/rioni-piaggio-e-fondovico) (la prima cattedrale di Gravina), [Happy Rentals](https://happy.rentals/blog/234-gravina-in-puglia-an-extraordinary-date-with-history) (l'ossario e il 999). Blocco N2, solo come riferimento visivo: terrazza, parapetto curvo coi faretti, cipressi, prato e parete di roccia dalle foto a 360° del 2016 su Google (Sergio Paolilli Treonze) e dalle foto su Wikimedia Commons (`riferimenti/foto_n/elenco-sm.tsv`); il portico che guarda il paese e il campanile della Cattedrale dalla [foto di Tiziana Gagliardi](https://commons.wikimedia.org/wiki/File:Gravina_in_Puglia_-_Rione_Fondovico_-_2023-09-17_20-01-26_001.JPG); il ponticello sul canalone in fondo alla terrazza dal satellite e dalla foto a 360° da drone del 2019 su Google (Marek Szczepanski). Posizioni da OSM: cancello n898359849, terrazza w76152588, «San Michele» n898361350, mura w1512581512
* Rione Fondovico (blocco N2): Calata Grotte San Michele pedonale perché su Street View l'auto di Google non ci è passata (solo foto a 360° di utenti); Piazzetta Fondovico (OSM w385177566) con le quattro strisce di prato, i muretti e i vialetti di mattoni dal satellite e da una foto a 360° del 2017; la macchia del Fondovico (w385177569) con gli orti a terrazze dal satellite, solo come riferimento visivo
* Hortus (blocco N2): su Google è un parco in Via Giacomo Leopardi 5; l'arco col cancello decorato, il pilastro col cartello «hortus» e il cancello piccolo da Street View (ottobre 2025), il giardino a terrazze dal satellite, solo come riferimento visivo. Nessuna notizia verificata: solo l'etichetta
* San Francesco: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/la-monumentale-chiesa-di-san-francesco-nella-sua-evoluzione-storica/), [GravinaOggi, il campanile](https://www.gravinaoggi.it/il_campanile_di_san_francesco.html); posizione e forma del campanile (all'angolo nord della facciata, quattro ordini, cupolina) e facciata col rosone da Street View (Larghetto San Francesco, luglio 2022), solo come riferimento visivo
* Santa Sofia: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/gravina-santa-sofia-tomba-di-angela-castriota-skanderbeg/), [Columbia University, Spanish Italy and the Iberian Americas](https://siia.mcah.columbia.edu/object/tomb-angela-castriota-skanderbeg-s-sofia-gravina)
* Santa Cecilia: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/chiesa-santa-cecilia-nel-centro-storico/), [GravinaOggi](https://www.gravinaoggi.it/chiesa-di-santa-cecilia.html); la lunetta sopra la porta da Street View (Via Salvatore Fighera)
* Santa Teresa: [GravinaOggi, il monastero](https://www.gravinaoggi.it/monastero-di-santa-teresa-a-gravina-in-puglia.html), [GravinaOggi, il SS. Nome di Gesù](https://www.gravinaoggi.it/la_chiesa_del_ss_nome_di_gesu.html) (l'antica parrocchia di San Matteo)
* Chiesa del Gesù: [GravinaOggi](https://www.gravinaoggi.it/la_chiesa_del_ss_nome_di_gesu.html), [Carta dei Beni Culturali della Regione Puglia](https://cartapulia.it/dettaglio?id=127705); facciata bianca con il timpano e tre oculi dalla [foto su Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Chiesa_del_Ges%C3%B9_(Gravina_in_Puglia).jpg). Sant'Agostino: i vasi agli angoli della facciata dalla [foto su Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Gravina_in_Puglia_-_chiesa_di_Sant%27Agostino_-_2026-09-29_18-31-36_001.jpg)
* San Nicola: [Chiese italiane (CEI)](https://chieseitaliane.chiesacattolica.it/chieseitaliane/AccessoEsterno.do?mode=guest&type=auto&code=57156) (Santi Nicola e Cecilia: preesistenze del IX–X secolo, demolizione del 1410, completamento nel Seicento, facciata del 1704), [GravinaLife, confraternita della SS. Annunziata](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/confraternita-della-santissima-annunziata-di-gravina-in-puglia-1555/) (eretta «molto probabilmente nel 1555 nella chiesa di San Nicola»)
* Addolorata e Annunziata: OSM, Overture e Google mettono i due nomi sulla stessa sagoma, in Via Borgo. Il [catalogo dei Beni Culturali](https://catalogo.beniculturali.it/detail/ArchitecturalOrLandscapeHeritage/1600181066) ha l'Addolorata in «Via Borgo Vecchio», [GravinaOggi](https://www.gravinaoggi.it/la_chiesa_sconsacrata_della_ss_annunziata_.html) la SS. Annunziata, sconsacrata, nella «vecchia via Borgo»: nessuna fonte dice che siano la stessa chiesa, quindi resta solo l'etichetta «Addolorata»
* Porta San Michele: [GravinaLife, le antiche porte fortificate](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/le-antiche-porte-fortificate-di-gravina/) (Giuseppe Massari, 6/8/2020: porta San Tommaso, poi Regia, dedicata a San Michele dopo il 1799), [Algramà](https://www.algrama.it/algramanews/riposta-nella-nicchia-la-statua-di-san-michele-del-1799-gravina-fu-salva-dalle-orde-del-cardinale-ruffo/) (29/11/2020: la statua lignea del 1799 torna nella nicchia di Piazza Scacchi il 28/11/2020), [MurgiaTime](https://www.murgiatime.it/murgia/index.php?option=com_content&view=article&id=13901:il-san-michele-della-porta-1799-2020&catid=89:gravina-storia&Itemid=541); in OSM la piazza (w469109640) ha i vecchi nomi «Porta Regia» e «Porta San Tommaso». Nicchia all'angolo del palazzo rosa sull'imbocco di Via Matteotti, colori e balconi da Street View (ottobre 2025), solo come riferimento visivo
* Piazza Scacchi: busto in bronzo di Canio Musacchio, «primo sindacalista meridionale» secondo la sua lapide (letta su Street View), [GravinaLife, 6/5/2023](https://www.gravinalife.it/notizie/imbrattato-il-monumento-a-canio-musacchio/); busto in pietra di Arcangelo Scacchi «nella piazza prospiciente la sua casa natia», [GravinaOggi](https://www.gravinaoggi.it/arcangelo_scacchi_1810-1893.html), date di nascita e morte da [Wikipedia](https://en.wikipedia.org/wiki/Arcangelo_Scacchi). Posizione del busto di Scacchi dal basamento in OSM (w411138256); aiuole, ulivo, sedute e pannelli da Street View
* Quattro Fontane: le due lapidi fotografate su Wikimedia Commons ([Le Quattro Fontane](https://commons.wikimedia.org/wiki/File:Le_Quattro_Fontane_(Gravina_in_Puglia).jpg), [iscrizione del 1927](https://commons.wikimedia.org/wiki/File:Iscrizione_nelle_Quattro_Fontane.jpg)): regnando Ferdinando IV si decise nel MDCCLXXVIIII (1779) di portare l'acqua del Pozzo Pateo in questa fontana, costruita con denaro pubblico (sindaco Giuseppe Palmieri, architetto Gaetano De Tomasio) e restaurata nel MDCCCLVIIII (1859, sindaco Raffaele Pignatelli); il 31/12/1927 arrivò l'acqua del Sele. [Wikipedia](https://it.wikipedia.org/wiki/Gravina_in_Puglia) scrive 1778, la data 1859 di OSM (`start_date`) è quella del restauro: nella scheda c'è la data della lapide. Sagoma da OSM (w411137158)
* Bastione medievale: [Wikipedia](https://it.wikipedia.org/wiki/Gravina_in_Puglia) («ultimo pezzo dell'antica cinta muraria, collega il quartiere di Sant'Andrea al ponte acquedotto»); posizione da OSM (n13159769942)
* Monumento ai Caduti (blocco M2): [Pietre della memoria](https://www.pietredellamemoria.it/pietre/monumento-ai-caduti-della-grande-guerra-gravina-in-puglia-ba/) (gruppo in bronzo di Angelo Galli, fuso nel bronzo dei cannoni austriaci: l'Italia che impugna il vessillo sul cavallo, i soldati nello scatto che precede la carica, un prigioniero con le catene recise ai polsi; basamento di marmo bianco coi nomi dei caduti per anno; incompiuto nel retro perché l'artista non ricevette tutto il dovuto), [Giardini storici della Puglia, Gravina](https://www.giardinidellapuglia.it/i-giardini/bari/gravina-in-puglia/) (realizzato nel 1934 al centro della Villa; dado con tre gradini e lastre di marmo coi nomi; Angelo Galli), [GravinaOggi](https://www.gravinaoggi.it/monumento_ai_caduti_della_grande_guerra_1915-1918.html) (Angelo Galli, 1870–1933, di Viggiù). Posizione e sagoma da OSM w411137249 (Wikidata Q136344179), panchine e fontane della Villa da OSM; forma delle figure stilizzata dalle foto.
* Monumento alla Cola Cola (blocco M2): [Rolling Mamas](https://www.rollingmamas.com/la-cola-cola-di-gravina-in-puglia/) (fischietto bitonale di terracotta, corpo bianco calce con strisce rosse, gialle, verdi e blu; tradizione di metà Ottocento; la famiglia Loglisci; casa museo in Piazza Benedetto XIII 24), [Provincia Mon Amour](https://www.provinciamonamour.it/casa-museo-della-cola-cola/) (la scultura gigantesca in vetroresina all'ingresso della città), [GravinaLife, 12/04/2010](https://www.gravinalife.it/notizie/addio-cola-cola/) (la statua fu realizzata nel 2005). Posizione da OSM w411137509 (`historic=memorial`, Via Bari), confermata da Google Maps («Monumento alla Cola-Cola», solo riferimento visivo). Forma stilizzata dalle foto dei fischietti (Wikimedia Commons, Casa Museo della Cola Cola).
* Sottopassi (blocco M2): gallerie OSM sotto i binari (`tunnel=yes`, `layer=-1`) di Corso Giuseppe di Vittorio e di Via Falcone e Borsellino, il sottopassaggio pedonale della stazione (w1288069909, `level=-1`), i ponti dei binari a Via Spinazzola (OSM w125059307 e w125061479); muri e impalcato da Street View, solo come riferimento visivo.
* Botromagno e Necropoli del Padre Eterno: [Stanze Orsini, 17/08/2016](https://www.stanzeorsini.it/sito-archeologico-botromagno-petra-magna/) (il sito Padre Eterno, ai piedi del colle Petra Magna, si estende per 1 400 m lungo il bordo ovest della gravina, a pochi passi dalla chiesa-grotta affrescata Padre Eterno; tombe scavate nella roccia non prima del VII secolo a.C., sei in serie monumentali in un recinto funerario; il 2/9/1988 una tomba del IV secolo a.C. con 46 pezzi di corredo; buche per i pali delle capanne del IX–VIII secolo a.C.; cisterne, canalizzazioni e fornaci; tracce della cinta muraria della fine del IV secolo a.C.; Sidion, poi Silvium stazione sulla via Appia), [GravinaOggi, il Parco Archeologico di Botromagno](https://www.gravinaoggi.it/il-parco-archeologico-di-botromagno-a-gravina-in-puglia.html) (oltre 400 ettari; sepolture a fossa dalla fine del VII alla fine del IV secolo a.C. nell'area Padre Eterno; fornaci per vasi e laterizi; monete con la leggenda «Sidinon»; il nome di Sidion, centro apulo, sopravvive in Silvium; tombe a semicamera intonacate e dipinte del V secolo a.C.), [Museo Capitolare, complesso rupestre della Madonna della Stella](https://www.museocapitolaregravina.it/madonna-della-stella-traduzioni/complesso-roccioso-di-madonna-della-stella/) (sei grotte sul margine calcareo, «nella zona della necropoli che va sotto il nome di area del Padre Eterno»). Rovine dalle sagome OSM `building=ruins`, area degli scavi da OSM w484764621 (Wikidata Q111644781), punto «Padre Eterno» da OSM n4491972089 (solo l'etichetta: con ogni probabilità è la chiesa-grotta, ma non è verificato). Forme di muri, tombe e buche stilizzate; il Madonna della Stella Resort a un piano col porticato da una foto sferica su Google Maps, solo come riferimento visivo
* Sette Camere: [Wikipedia](https://it.wikipedia.org/wiki/Gravina_in_Puglia) (scavo artificiale in un banco di tufo, presumibilmente negli ultimi secoli dell'Alto Medioevo), [foto su Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Grotte_delle_sette_camere.jpg) (la fila di grotte sulla parete); posizione da OSM (n6365472958). Piazzetta Fondovico: prato in OSM (w385177566), solo l'etichetta (le strisce e i muretti dal blocco N2, vedi sopra)
* Bosco Difesa Grande: [Wikipedia](https://it.wikipedia.org/wiki/Bosco_Difesa_Grande) (6 km a sud della città; sito Natura 2000 IT9120008 di 5 268 ettari, zona speciale di conservazione dal 2015 con il D.M. 10/07/2015; 1 890 ettari di bosco; roverella, cerro e farnetto), [SISEF](https://www.sisef.org/2025/07/04/incendio-e-rinascita-del-bosco-difesa-grande-gravina-in-puglia/) (incendi del 12/08/2017, oltre 1 200 ettari, e del 28/07/2021, 936 ettari), [Overture Maps](https://overturemaps.org) (lunghezza del tracciato reale: 5 397 m)
* Area Quercus (in OSM il parco «Rifugio Bosco Difesa Grande», w477739267; ristorante n11092432410, campi w1195121473/5/6, tribunetta w1195121474, parcheggio «Terra Rossa» w477738793): [GravinaLife, 14/06/2021](https://www.gravinalife.it/notizie/area-ristoro-marcuccio-assegnata-nuova-gestione/) (l'area ristoro «Marcuccio» a una nuova gestione, con due campi da calcetto, uno da tennis e l'area pic-nic), [GravinaLife, 29/06/2024](https://www.gravinalife.it/notizie/quercus-una-nuova-era-di-sport-divertimento-e-gastronomia/) (struttura rinnovata: campi da calcio e tennis, zona giochi, ristorante e pizzeria, escursioni nel bosco e gite a cavallo), [GravinaLife, 13/06/2026](https://www.gravinalife.it/notizie/presentazione-football-camp-2026-e-inaugurazione-quercus) (i «campetti dell'area Quercus»). In OSM i tre campi sono segnati da tennis: dal satellite il centrale (w1195121475) è quello da tennis, gli altri due da calcetto come dice GravinaLife. Tavoli: posizione indicativa dal satellite, solo come riferimento visivo; maneggio e giochi tolti nel blocco M1 (il committente: non ci sono)
* Vivaio forestale e Centro visite «San Nicola la Macchia»: [Il Tacco di Bacco](https://iltaccodibacco.it/gravina-in-puglia/centro-visite-bosco-difesa-grande) (nel cuore del SIC Bosco Difesa Grande, indirizzo «Vivaio Forestale», attività educative, didattiche e divulgative per scuole, famiglie e turisti). Su Google Maps risulta «chiuso temporaneamente»: la scheda non dice che sia aperto. Edifici (w411142982, w411144227, w411147963) e vasche (w411138897, w411139081) da OSM; la vasca grande w411138854 resta fuori dalla zolla
* Base Scout «Base Scout Gravina 1»: edificio OSM w411148672, solo l'etichetta. Area pic-nic e scritta «SIC DIFESA GRANDE»: non sono in OSM; posizione indicata dal committente, forme (staccionate, scaletta, vialetti, tavoli, alberi, lampione, lettere bianche con la foglia) da Street View (giugno 2022), solo come riferimento visivo
* Sentieri dell'area Quercus: OSM `highway=path` w647001042, w647001043, w647001044, w647001046, w647001047, w759847416, w773874702, con la via di servizio w647001048; bosco dai poligoni OSM «Bosco Difesa Grande» (w330074271) e «Bosco di Gravina» (w330074290); zone di alberi bruciati dal satellite
* Scuole (blocco E): posizioni e nomi da OSM (w411138848, w411138849, r6148449, w1384764963, n12091003369, n12039009818, n12039071161, edificio «Edificio Scolastico S.G. Bosco») e Overture Maps (licei G. Tarantino, Benedetto XIII, Don Saverio Valerio, Tommaso Fiore, Savio-Fiore, Soranno, Santomasi); l'edificio è la sagoma reale che contiene il punto. Solo le etichette. Chiese della città senza nome in OSM (Gesù Buon Pastore, SS. Crocifisso e San Sebastiano, Madonna delle Grazie, Santi Pietro e Paolo): nome da OSM o Overture, solo l'etichetta; portale e croce generici, campanili non verificati e quindi non disegnati
* Casino di Meninni: [FAI, I Luoghi del Cuore](https://fondoambiente.it/luoghi/casino-dei-meninni) (palazzo storico che dalla collina del Guardialto sovrasta la città, giardino con altissimi pini d'Aleppo, cappella di famiglia tra i cipressi, luogo fatiscente; nei Luoghi del Cuore dal 2012 al 2022), [GravinaLife, 11/02/2026](https://www.gravinalife.it/notizie/casino-di-meninni-interrogazione-del-consigliere-conca) (fabbricati storici abbandonati). Edificio su Via Guardialto indicato dal committente (sagoma OSM, [1572, −536]). Case rosa tra Via Guardialto e Via Guardialto Piccolo: indicazione del committente, solo l'etichetta
* Fiera di San Giorgio: [Stanze Orsini](https://www.stanzeorsini.it/la-fiera-san-giorgio-gravina-puglia/) (esisteva già prima del 1294, quando Carlo d'Angiò la ripristinò, secondo un documento del Registro Angioino; ad aprile, per San Giorgio; in origine sui terreni della chiesa di San Giorgio dei Cavalieri di Malta, oggi nel Parco Fiere dell'ex linificio in via Spinazzola); area da OSM «Zona Fiera San Giorgio» (w478401751), cancello OSM n8763525337, padiglioni OSM (Padiglione Tobia Granieri w411148871, w411147010, w411147074, w411147873); recinzione (muretto con la rete), botteghino e portoni da Street View (aprile 2025), solo come riferimento visivo
* Stadio Stefano Vicino: [Wikipedia, FBC Gravina](https://it.wikipedia.org/wiki/FBC_Gravina) (via Fazzatoia, circa 4 000 posti, intitolato nel 2015 a Stefano Vicino, erba sintetica dal 2015, lavori 2024–2025 con la copertura della tribuna ovest); campo, gradinate, torri faro e muro di cinta dalle sagome OSM (stadio w478401752, campo w927885291, tribune w411149113 e w411146463) e dal satellite, solo come riferimento visivo
* Stazione FAL: [Wikipedia](https://it.wikipedia.org/wiki/Stazione_di_Gravina_in_Puglia_(FAL)) (aperta nel 1915, linea Bari–Altamura–Potenza delle Ferrovie Appulo Lucane, interscambio con la stazione RFI)
* Zona artigianale P.I.P.: solo l'etichetta (nessuna scheda)
* Centro storico vero (blocco N1). **Salite e discese**: quote Copernicus (sopra). **Strade**: la superficie
  di ogni via da OSM (`surface`: `sett` e `paving_stones` lastre, `asphalt` asfalto, `unhewn_cobblestone`
  ciottoli), letta con l'Overpass API (`tools/.cache/superfici.json`); Piazza Benedetto XIII dalla sagoma OSM
  dell'area pedonale (w385146363), il disegno a rombi dal satellite e da Street View (ottobre 2025). **Facciate**
  (zoccolo, portoni con la cornice, balconi su mensole con la ringhiera e i vasi, pluviali): da Street View in
  Via Abbrazzo D'Ales, Via San Giovanni Evangelista, Via Vittorio Veneto, Via Donato Cristiani (2025) e vicino a
  Piazza della Repubblica (maggio 2025), solo come riferimento visivo; balconi, porte e vasi sono distribuiti dal
  codice, non uno per uno. **Fontanine** dell'Acquedotto Pugliese nei sei punti OSM `amenity=drinking_water`
  (n3724586269, n9679370615, n11094034285, n11094147078, n11187757150, n11999538354), forma dalla
  [foto su Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Drinking_fountain_in_Calata_Grotte_San_Michele,_Gravina_in_Puglia,_Italia_Apr_19,_2025_04-49-56_PM.jpg)
  in Calata Grotte San Michele e da Street View in Piazza della Repubblica: lo stesso modello in tutti e sei.
  **Belvedere «la porticina»** del Piaggio: tre panchine di marmo senza schienale e un paletto di pietra da OSM
  (n11094118739–42), la ringhiera sui pilastri da una foto sferica del luglio 2017. **Statua di Benedetto XIII**:
  sagoma OSM w411137523 (Wikidata Q136345080), piedistallo, gradini e recinto di catene da Street View (ottobre
  2025), figura stilizzata. **Alberelli davanti alla Cattedrale**: indicazione del committente, aiuola e cinque
  alberi potati dal satellite e da Street View (ottobre 2025), col lampione a palo. **Piazza della Repubblica**:
  aiuola rialzata con due ulivi, cubi di pietra, fioriere tonde e lampione a due bracci da Street View (maggio
  2025); l'aiuola non è in OSM, la posizione viene dal satellite; fioriere grigie lungo Via Libertà. **Via
  Fontana la Stella**: tre alberi sul lato nord verso il ponte (Street View, ottobre 2025). **Via Vittorio
  Veneto**: lampioni a palo neri e paletti di pietra agli incroci (Street View, ottobre 2025). In OSM nel centro
  storico non ci sono alberi né lampioni: ci sono solo quelli visti
* Geografia generale: [Wikipedia, Gravina in Puglia](https://en.wikipedia.org/wiki/Gravina_in_Puglia)

Dati geografici della città intera (fase 3.4):

* Vie, edifici, uso del suolo, acque e binari: [Overture Maps](https://overturemaps.org) 2026-09-23.1, derivato da [OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL)
* Luoghi con nome (monumenti, chiese, stazioni, parchi, impianti sportivi): [OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL), letti con l'[Overpass API](https://overpass-api.de) e messi in cache da `tools/genera_dati.py`
* Quote del terreno: [Copernicus DEM GLO-30](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM), tessera N40 E016 dal [registro Open Data di AWS](https://registry.opendata.aws/copernicus-dem/)
