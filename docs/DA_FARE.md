# Cosa resta da fare

Stato al 16 ottobre 2026: fase 3 approvata e online, fase 3.4 completata e unita su `main` con tutti i blocchi da A a N8 (PR #30, commit `caceef6`). **Fase 4 · Rifinitura in corso**, completati il **Blocco 4.1 · Golden hour** (branch `fase-4-1-golden-hour`, PR #31), il **Blocco 4.2 · Sponde del Ponte, stabilità mezzi, rumore motori e boost Shift** (branch `fase-4-2-ponte-motori-stabilita`, PR #32 in bozza) il **Blocco 4.3 · Via giudice Montea (salita, parapetto e case pericolanti), campi sportivi, Seminario Vescovile e posizioni reali cinema** (branch `fase-4-3-montea-cinema-campi`, PR #33), tutti uniti su `main`. **Blocco 4.4 · Camera dopo il teletrasporto, schede sul telefono, accessibilità, licenza, testate del ponte, motori e velocità massime** (branch `fase-4-4-camera-schede-rifinitura`, PR #34), tutti uniti su `main`. **Blocco 4.5 · La guida** (acceleratore sul telefono e dritto agli incroci, niente tremolio, vie lunghe dritte; branch `fase-4-5-guida`, PR #35) fatto, in attesa del sì del committente. Poi i blocchi 4.6 e 4.7.
Aggiornare questo file a ogni fase.

**Fase 3.4 (Gravina oltre il centro storico) completata**: piano, dati, budget, rischi e divisione
del lavoro su due chat in [`PIANO_FASE_3_4.md`](PIANO_FASE_3_4.md).

### Fase 3.4, seconda parte (decisioni del 30/09/2026)

Ordine: I → D → E → L → M1 → M2 → M3 → N1 → N2 → N2b → N3 → N4 → N4b → N5 → N5b → N5c → N6 → N7 → N8, dettagli e decisioni nella sezione 7 del piano.

- [x] **I · spazio sul telefono** (`fase-3-4-i-prestazioni`, PR #13, unita il 30/09/2026):
      due livelli di dettaglio per riquadro nella stessa mesh (terreno a maglia doppia, vie rade,
      sagome semplificate, metà degli alberi; finestre e torrini solo da vicino), con isteresi e
      senza draw call in più. Fotogramma peggiore da 243 500 a 164 700 triangoli sul telefono e da
      335 400 a 235 500 su PC; «Pronto» circa 640 ms. Vista «alta» in `prestazioni.mjs`.
- [x] **D · centro storico** (`fase-3-4-d-centro-storico`, PR #14, unita il 30/09/2026):
      Porta San Michele (nicchia con San Michele all'imbocco di Via Matteotti, facciate dei due
      palazzi d'angolo), Piazza Scacchi (busti di Musacchio e Scacchi, ulivo, aiuole e sedute),
      Quattro Fontane (dalle lapidi: 1779, restauro 1859), campanile e facciata di San Francesco,
      campanile della Cattedrale in fondo a est, lunetta di Santa Cecilia, facciata del Gesù, vasi
      di Sant'Agostino, grotte delle Sette Camere; schede nuove (Porta San Michele, Piazza Scacchi,
      Quattro Fontane, San Nicola, Bastione, Sette Camere), Piazzetta Fondovico e «Fondovito» sulla
      targa. Vie del mezzo nel centro storico entro il 18%; tolto il gradino di 15–18 m a sud della
      città. 264 KB compressi (+9), telefono 175 300 triangoli, PC 246 000, draw call invariate.
- [x] **Peso**: il 30/09/2026 il committente ha alzato il tetto da 280 a **360 KB compressi**
      (≤ 1,2 MB non compressi). Dopo il blocco D restano circa 96 KB per E, L, M e N.
      Il 03/10/2026 lo ha alzato ancora, da 360 a **450 KB compressi**: dopo M3 (337 KB) restano
      circa 113 KB per i blocchi N. I tetti di triangoli e draw call non cambiano.
- [x] **E + L insieme** (`fase-3-4-e-l-luoghi-bosco`, PR #15, unita il 01/10/2026), più
      l'**acceleratore solo su PC** (Shift tenuto premuto, ×1,8; sul telefono no, decisione del
      committente del 30/09/2026): agli incroci il cartello si apre prima e il mezzo torna alla
      crociera. 60 fps e fotogramma peggiore come senza, subito dopo Parti e dopo un teletrasporto.
- [x] **E · luoghi della città, scuole e chiese**: 16 scuole sull'edificio reale (Liceo
      G. Tarantino scientifico e linguistico, ITT Bachelet · IPSIA G. Galilei al P.I.P., come chiesto,
      più le altre con la sagoma), con pennoni, pensilina, campo da gioco e recinzione; chiese della
      città con portale, oculo e croce (niente campanili: nessuna foto verificata); Casino di Meninni
      (scheda FAI), case rosa, La Caccia, Largo Cappuccini e gli altri luoghi; schede nuove per Fiera
      di San Giorgio, stadio Stefano Vicino, stazione FAL. Vie del mezzo entro il 18% in tutta la
      città (raccordo del terreno a nord e a est da 110 a 230 m): da 27 vie oltre il 20% a una.
- [x] **L · il Bosco da vicino**: strada compressa fino al vivaio (674 m per 3,2 km reali), zone
      dell'area Quercus e del vivaio a scala reale, area Quercus (ristorante, campi, tribunetta,
      maneggio, giochi, tavoli, parcheggio; scheda), vivaio con vasche e aiuole (scheda senza dire
      che il centro visite è aperto), Base Scout, area pic-nic con la scritta «SIC DIFESA GRANDE»,
      524 m di sentieri reali a piedi, bosco fitto istanziato che si apre tra camera e figurina,
      foschia, suoni del bosco solo dentro il bosco (interruttore nella pausa).
- [x] Area Quercus: maneggio e giochi non ci sono (committente, 01/10/2026), tolti nel blocco M1;
      i tavoli restano.
- [ ] Da verificare con il committente: il nome della strada del bosco
      (in OSM non ce l'ha: nel diorama «Strada nel bosco»). La chiesa di Santi Pietro e Paolo: il nome ora è sulla chiesa a
      cono (blocco N3, risposta del committente).
- [ ] **Prestazioni**: se dopo i blocchi M e N il diorama resta pesante, il committente pensa a
      un'impostazione che carichi il mondo solo attorno alla visuale; in città non si riduce niente,
      al massimo in periferia dove dall'auto non si vede (01/10/2026).
- [x] Telefono in orizzontale, partenza sul ponte: il contatore di debug segnava 74 draw call (tetto 70).
      Con i mezzi del blocco M3 (4 mesh invece di più di 20) sono 57 (`node foto.mjs orizzontale`).
- [ ] La vasca grande del vivaio (w411138854) è fuori dalla zolla del vivaio: allargarla di un
      riquadro verso sud, se si vuole.
- [x] **M1 · Botromagno, strade, stadio e Fiera** (`fase-3-4-m1-botromagno-strade`, PR #16, unita il
      01/10/2026):
      - Botromagno: 46 rovine OSM sul lato di Botromagno (non solo a ovest del ciglio: tre stavano
        nella scarpata e diventavano torri) a muri a secco con brecce, recinto funerario con sei
        tombe, tombe a fossa, a semicamera e a camera col dromos, buche dei pali, suolo di roccia;
        resort e versante a un piano coi coppi; scheda «Necropoli del Padre Eterno», etichette
        «Scavi archeologici di Botromagno» e «Padre Eterno»;
      - vie (difetti 1–6 e 8, `node difetti.mjs` sulle vie del mezzo): sotto il terreno da 283 a 0,
        sospese da 1 001 a pochissime, dischi sfasati da 237 a 0, decorative sovrapposte da 5 a 0;
        maglia vicina a 7,5 m dove serviva (in città non si toglie niente: decisione del committente);
      - stadio su terrapieno con campo, gradinate, tribuna ovest coperta, torri faro e muro di cinta;
        Fiera con recinzione, cancello, botteghino e portoni;
      - area Quercus senza maneggio e giochi; camera libera senza ritorno automatico.
- [x] **M2 · percorsi a piedi, zone pedonali e suoni del bosco** (`fase-3-4-m2-a-piedi`, PR #17,
      unita il 02/10/2026 con l'approvazione anticipata del committente):
      - a piedi, tratti reali per id OSM: sentiero degli scavi (A, 1,5 km), Pineta e Parco Robinson
        (C, D), Via Pietro Ianora (E), scale e sottopassaggio della stazione (F), vialetti della Villa;
        nel vivaio l'anello V2 (692 m) e il sentiero della Base Scout; percorsi approvati nella Fiera e
        nel giardino del Casino di Meninni. Rete: da 1 473 a 1 539 tratti, da 89,2 a 94,3 km; a piedi da
        21 a 53 tratti (da 1,1 a 5,2 km);
      - Villa Comunale e Piazza della Repubblica pedonali; strada della Fiera fino al parcheggio dello
        stadio, Via Guardialto fino al Casino di Meninni e Via Bari fino alla Cola Cola con la goccia;
      - **sottopassi** (richiesta del committente): Corso Giuseppe di Vittorio, Via Falcone e Borsellino e
        il sottopassaggio pedonale della stazione in trincea coi muri e l'impalcato; viadotti dei binari
        a Via Spinazzola con le pile;
      - **Pineta e Parco Robinson** costruiti: pini a ombrello, prato, cancellata coi cancelli, area giochi
        (altalene, scivolo, giostra, dondoli, altalena a bilico), busto, panchine, lampioni, fontanella;
      - **Monumento ai Caduti** rifatto dalle fonti, con la **sosta in panchina** (scheda e pulsante «Esci
        dalla piazzetta · torna al mezzo»); panchine e Fontanoni gemelli della Villa;
      - **monumento alla Cola Cola** su Via Bari, nel punto OSM, con la scheda;
      - vasca grande del vivaio (zolle allargate); suoni del bosco senza pioggia, intonati con la radio.
- [x] **Resto di M2**, fatto insieme a M3 il 02/10/2026:
      - `interazioni.mjs`: giri a piedi nel vivaio (V2, 738 m), sul sentiero degli scavi (A, 643 m) e nella
        Villa con la sosta in panchina e il pulsante; Fiera, Casino di Meninni e Cola Cola dall'elenco dei
        luoghi, con la goccia;
      - `node difetti.mjs` prima e dopo M2 (`shots/difetti-prima-m2.json`, `difetti-dopo-m2.json`): «sotto»
        da 0 a 31, quasi tutti nelle trincee dei sottopassi (l'impalcato sopra la galleria) e 3 sui vialetti
        del Parco Robinson, a vista a posto; «galleggia» da 16 a 20, «spezzate» da 44 a 58 (curve dei
        sentieri nuovi);
      - screenshot su telefono in verticale e in orizzontale, pulsante della panchina sul telefono;
      - **gradini** nel sottopassaggio pedonale della stazione (alzate da 16 cm dove la rampa supera il 12%);
      - `DESIGN.md`: sottopassi, Pineta e Parco Robinson, Villa e sosta in panchina, Cola Cola, suoni del bosco.
- [ ] **Street View** (resto di M2): ingresso dello stadio (visto sul satellite: va bene), paletti agli
      ingressi della Villa, foto della Cola Cola. Il 02/10/2026 Street View non si caricava (pannello nero).
- [x] **M3 · mezzi realistici e mongolfiera** (`fase-3-4-m3-mezzi-mongolfiera`, PR #18, unita il
      03/10/2026; approvati anche i suoni del bosco e il soffio del bruciatore):
      - auto per sezioni (anelli di 15 punti, passaruota, parafanghi), vetri trasparenti, abitacolo col
        guidatore seduto, ruote per modello; fari con l'alone, stop in frenata, frecce prima della svolta;
        4 mesh per mezzo invece di più di 20; mappa d'ambiente al tramonto solo per i mezzi;
      - mongolfiera: giro di 2,7 km in 7 minuti da Botromagno, sempre 30 m sopra tetti e monumenti,
        vista esterna e dalla cesta, cambio mezzo, pausa, teletrasporto, fine del giro con l'auto;
      - sul telefono i mezzi sono tessere su una riga (il pannello iniziale si abbassa, «Parti» resta in
        vista anche in orizzontale); vetrina rifatta: campo lungo sul ponte da sud-ovest (prima la collina
        della sponda est copriva il ponte), in verticale un campo medio sul mezzo;
      - misure (`shots/prestazioni-dopo-m3.txt`): draw call da 71 a 56 su PC e da 50 a 35 sul telefono;
        triangoli al massimo 283 600 su PC (mongolfiera) e 183 200 sul telefono; 337 KB compressi;
        memoria JS 174 MB su PC (tetto 150, era 179) e 157 sul telefono.
- [ ] Ritocchi dei mezzi: i fari della Huracán sporgono un poco dal muso.
- [ ] Sul telefono, nella sosta in panchina, la scheda lunga dei Caduti copre il monumento: accorciarla
      o renderla richiudibile (vedi anche «schede lunghe» più giù).
- [x] **N1 · centro storico vero** (`fase-3-4-n1-centro-storico`, PR #19, unita il 05/10/2026 con
      l'approvazione del committente; piano approvato il 03/10/2026):
      - **salite e discese** sulle quote reali senza esagerazione (`GEO.centro`, `Guida`): vie del mezzo
        entro il 2% dall'84% al 36% della lunghezza, nessuna oltre il 18% (limitatore sulle quote degli
        incroci); Cattedrale 0, Piazza della Repubblica +4,3, San Francesco +10; canyon, cigli e gradoni
        a mano (a sud del Fondovito il ciglio scende fino a −15 m e i gradoni con lui);
      - effetti: camera a 30° in pendenza; case con lo zoccolo in conci, marcapiano, cornicione e
        pluviali dallo shader; gradoni anche fuori dai rioni; finestre in file orizzontali e 899 porte coi
        gradini; 247 m di muretti e ringhiere dove la via si stacca dal terreno;
      - **strade** secondo la superficie OSM (lastre, asfalto, ciottoli), Piazza Benedetto XIII a rombi,
        tombini radi;
      - **facciate**: cornici, davanzali, persiane a stecche, portoni a riquadri con le lunette (shader),
        2 287 balconi con ringhiera e 3 834 vasi istanziati, solo entro 180 m (metà sul telefono);
      - **arredo**: 6 fontanine dell'Acquedotto Pugliese, panchine e paletto della «porticina», aiuola con
        cinque alberelli davanti al Vescovado, statua di Benedetto XIII (non c'era), Piazza della
        Repubblica (aiuola con due ulivi, cubi, fioriere, lampione a due bracci), alberi in Via Fontana la
        Stella, lampioni e paletti in Via Vittorio Veneto;
      - misure: 356 KB compressi (+19), triangoli al massimo 323 700 su PC («alta») e 217 900 sul telefono
        («centro»), draw call 59 e 38, «Pronto» 1,24 e 1,22 s, memoria JS 174 e 156 MB (invariata);
        `difetti.mjs`: nessun difetto nuovo («galleggia» da 20 a 12).
- [ ] Dopo N1, da valutare col committente: l'esagerazione ×1,5 delle quote (di riserva); nei vicoli
      stretti la camera resta alta per non finire dietro i tetti, e lì la pendenza si vede soprattutto
      da zoccoli, gradini e gradoni.
- [x] **N2 · Fondovito, San Michele delle Grotte e Hortus** (`fase-3-4-n2-fondovito`, PR #20, piano approvato il
      05/10/2026; unita il 07/10/2026 con l'approvazione anticipata del committente):
      - **a piedi**: Calata Grotte San Michele tutta pedonale (via le due gocce del mezzo), Gradoni San Giovanni Battista
        col raccordo di 18 m nell'area pedonale di Piazza Pellicciari, terrazza di San Michele e **ponticello** (non in
        OSM: satellite e foto da drone) con la goccia della figurina sul promontorio delle mura. Mezzo da 89,43 a 89,13 km,
        a piedi da 5,2 a 5,6 km; il mezzo aspetta su Via Marconi, Via Civita o Piazza Pellicciari;
      - **il pendio vero**: dove c'era il pianoro (−6 m, più alto del cancello) il prato scende dalla Calata San Giovanni
        Battista (−9) alla terrazza (−14…−16,5), col prato verde, la parete di roccia, la scarpata dei cipressi e la testa
        del canalone sotto il ponticello; terrazza dal 21% al 5% di pendenza massima; abitazioni rupestri invariate (21);
      - **San Michele nel posto giusto**: terrazza lastricata col parapetto a conci, i faretti e i cipressi, cancello col
        cartello, portico nella rupe coi pilastri monolitici, la cancellata, la scala di tufo e l'ossario dietro la grata;
        ponticello ad arco con la **cascata** animata fino al torrente; scheda spostata sul portico, coi fatti verificati
        (cinque navate, 14 pilastri, Pantocratore, statua, prima cattedrale, ossario e 999); la vecchia sagoma w411139697 è
        una chiesetta di un piano;
      - **rione**: Piazzetta Fondovico a quattro strisce coi muretti e i vialetti di mattoni, macchia del Fondovico con gli
        orti a terrazze, i cespugli e gli alberi; mura del promontorio basse; **Hortus** in Via Leopardi (arco, cancello col
        cartello, giardino a terrazze; solo l'etichetta);
      - misure: 370 KB compressi (+14), triangoli al massimo 327 600 su PC («alta») e 217 900 sul telefono («centro»,
        invariato), draw call 59 e 38, «Pronto» 1,24 e 1,23 s, memoria JS invariata (oscilla tra 157 e 186 MB);
        `difetti.mjs` uguale a N1, `simula` e `interazioni` verdi (59 controlli).
- [ ] Da N2, se il committente vuole: dentro la chiesa (la figurina che sale nella prima navata: la camera finirebbe
      nella roccia, per ora si vede dal portico); case del rione con scale esterne e archi (sm-05, sm-12: in N2b coi
      livelli veri); i sentieri a tornanti coi muri bianchi nella macchia (non in OSM, solo da guardare).
- [ ] Domande aperte di N2 (in attesa di risposta): la sagoma w411139697 è la chiesa di San Bartolomeo? San Demetrio
      (nessun edificio nei dati, Google a [−44, −180]) va aggiunta?
- [x] **N2b · livelli veri delle case, belvedere della Cattedrale e Santa Lucia** (`fase-3-4-n2b-livelli`, PR #21, piano
      approvato il 07/10/2026; unita il 09/10/2026 con l'approvazione del committente):
      - **ruderi**: i 28 `building=ruins` OSM del centro storico (17 nel Piaggio, 7 nel Fondovico, 4 altrove) sono ruderi
        urbani (`KIND['rudere']`, `Buildings.ruin`): muri di tufo crollati a pezzi, senza tetto, con le brecce; quelli nel cono
        di 12° dalla ringhiera verso il ponte restano a 0,6 m;
      - **la ringhiera della Cattedrale**: prima una casa a tre piani (un rudere in OSM) copriva il ponte a 16 m; ora si vede
        (prova di tre raggi in `interazioni.mjs`, controllo negativo sul diorama di prima: 3 raggi su 3 bloccati);
      - **piani veri**: tabella `LIVELLI` in `genera_dati.py` con 81 case rilevate su Street View (punto nella sagoma, id OSM,
        piani, via e data; «almeno N» dove la cima non si vede, 49 case su 81). Rispetto alla regola di prima: 39 più alte,
        39 uguali, 3 più basse; il Piaggio da 1 piano a 3–4 (Via Calderoni, San Basilio). Il Fondovico non ha Street View
        (solo foto a 360° di notte o interne) e resta con la regola;
      - **Santa Lucia a piedi**: footway OSM w1195336380 da Via Calderoni alla chiesa, goccia della figurina davanti alla porta,
        scheda lungo il passaggio (`interazioni.mjs`: giù a piedi, scheda, goccia, ritorno al mezzo);
      - misure: 371 KB compressi (+1), triangoli al massimo 334 700 su PC («alta») e 225 800 sul telefono («centro»), draw
        call 59 e 38, «Pronto» 1,31 e 1,24 s, memoria JS 187 e 159 MB; `difetti.mjs` come prima, `simula` verde, `interazioni`
        63 controlli verdi.
- [ ] Da N2b, se il committente vuole: i piani delle altre ~280 case (98 oltre il centro, il Fondovico dalle foto a 360°
      di giorno, il resto del centro) con altre uscite su Street View; le scale esterne e gli archi delle case del Fondovico
      (sm-05, sm-12); l'anello di Santa Lucia con «Via Santa Lucia» (w1512581502) se si trova un collegamento; le vie
      w1512581499–501 («Via Piaggio»), in Overture ma vie cieche del centro storico, non disegnate; la posizione della scheda
      «Santa Lucia» ([15, 109]) accanto alla chiesa OSM ([3,9; 123,4]).
- [x] **N3 · facciate di chiese e scuole** (`fase-3-4-n3-facciate`, PR #22, piano approvato il 09/10/2026; lavoro del
      12–13/10/2026, unita su `main` il 13/10/2026 con l'approvazione anticipata; screenshot ancora da vedere):
      - un costruttore (`Details.facciata`) e una tabella (`FACCIATE`): Santa Sofia (su Via Santa Sofia, non sul vicolo),
        Santa Teresa, **San Nicola** a due ordini sulla piazzetta (la navata era un corridoio vuoto: in pipeline è l'area OSM
        del luogo di culto), Addolorata (chiesa e non più casa), **Santa Lucia** (la cappella imbiancata davanti alla roccia
        della foto di Arditogi: le nicchie sono nella roccia dietro), Madonna delle Grazie con l'aquila (sulla chiesa vera:
        il nome era su un altro edificio), Gesù Buon Pastore, Santi Pietro e Paolo col tetto a otto falde (il nome era su una
        pensilina), Spirito Santo con la vela (prima era una casa), Mater Ecclesiae col campanile e il tamburo, il convento
        del Crocifisso, **San Domenico** (trovato: foto di un utente su Google Maps);
      - conci e bugnato dallo shader (`SURF.CONCI`), finestre a nastro delle scuole (`SURF.SCUOLA`), tabella `SCUOLE` con colori,
        recinzioni, scale antincendio, tettoia; Benedetto XIII e San Giovanni Bosco scuole; tre scuole in un palazzo: etichetta;
      - misure: 388 KB compressi (+17), triangoli al massimo 341 200 su PC («alta», +6 400) e 230 700 sul telefono («centro»,
        +4 900: più dei 3 000 stimati, sotto il tetto di 250 000), draw call invariate, «Pronto» 1,25 e 1,30 s.
- [ ] Da N3, se il committente vuole: la palestra del Bachelet (il volume cieco grigio della foto; non l'ho modellato), le
      scuole senza foto utile (Padre Pio, Giovanni Paolo II, Tommaso Fiore, Santomasi: servono foto), la torre e il tamburo di
      Mater Ecclesiae più fedeli (solo da Street View sul fianco), il convento della Madonna delle Grazie con le finestre, la
      statua della Madonna davanti a San Domenico; sul telefono i dettagli più fini delle facciate solo da molto vicino, se
      servono triangoli.
- [x] **N4 · Casino di Meninni** (`fase-3-4-n4-meninni-villette`, PR #23, piano approvato il 14/10/2026, unita il 14/10/2026):
      - **rete**: lo sterrato «Ingresso del Casino di Meninni» (18 m, non in OSM) lascia la SP201 e finisce con la goccia nello
        spiazzo davanti al cancello; via la goccia in mezzo alla SP201 (oltre l'incrocio è decorativa); il giardino a piedi dal
        cancello attorno al Casino fino alla goccia della figurina nella radura dietro (sostituisce il percorso del blocco M2).
        Rete da 1 548 a 1 549 tratti, da 94,52 a 94,28 km, da 12 a 13 gocce; a piedi da 95 a 97 tratti, da 5,68 a 5,59 km;
      - **il rudere** com'è (Street View, satellite, FAI): due piani senza tetto, finestre vuote con le cornici e il timpanetto,
        lesene, cornicione crollato a tratti, quattro torrette tonde con la cupoletta, stanze scoperchiate, corpo più alto al
        centro, scala coi muretti a L; terreno spianato in locale; i due corpi bassi sul muro da OSM come ruderi;
      - **attorno**: muro di cinta di conci bianchi a gradoni coi blocchi mancanti, cancello aperto, pini d'Aleppo fitti,
        cipressi, albero secco, rovi, cappella di famiglia (nessuna foto: semplice), suolo scuro dentro il recinto;
      - **corvi** (una draw call, solo vicino) e **vento** con l'ululato e i gracchi, con l'interruttore dei suoni del bosco;
      - scheda («rudere senza tetto», «tanto fatiscente quanto mistico», FAI), teletrasporto sullo sterrato (`via` del luogo);
      - prove: `interazioni.mjs` arriva sullo sterrato e fa il giardino a piedi fino alla goccia e ritorno; vista «meninni» in
        `prestazioni.mjs`; `difetti.mjs` come dopo N2b (sotto 31, galleggia 12, spezzate 58);
      - misure (`shots/prestazioni-dopo-n4.txt`): 400 KB compressi (+12), triangoli invariati nelle viste di oggi (PC «alta»
        341 200, telefono «centro» 230 700), vista «meninni» 67 100 su PC e 43 300 sul telefono, draw call al massimo 59 e 38;
        «Pronto» 1,45 s su PC e 1,42 sul telefono (erano 1,25 e 1,30: da rimisurare; se resta così, costruire il Casino
        dopo «Parti»); memoria JS 187 e 181 MB (oscilla).
- [x] **N4b · villette del triangolo Via Quasimodo – Via Montale – Via Carlo Betocchi** (`fase-3-4-n4b-villette`, PR #24,
      unita il 14/10/2026 con l'approvazione anticipata del committente; prompt `riferimenti/PROMPT_BLOCCHI_N4b_N6.md`, piano già approvato il 14/10/2026):
      - 16 sagome col centro nel triangolo diventano «villette» (tipo 13 della città); **livelli contati su Street View** (maggio e
        ottobre 2025, 13 punti di ripresa) nella tabella `LIVELLI` estesa alla città: da 3 a 5 livelli (prima da 2 a 6), sul lato alto;
      - **unità** della schiera (tabella `VILLETTE`, satellite del 14/10/2026: 8 m in Via Palazzeschi, 6 m sotto Piazza Digiesi), ognuna col
        suo intonaco, il tetto alla sua quota e i suoi piani; shader `SURF.VILLETTA` (zoccolo, persiane o tapparelle, porte-finestre,
        garage, pluviali, parapetto) e `SURF.RINGHIERA`; circa 250 balconi; terrazze col parapetto vero, torrini, pannelli, un attico;
        **coppi** col colmo di traverso su 730, 746, 745, 723 e sul capo sud-ovest di 865;
      - **giardinetti** (prato, muretto con la ringhiera, cancello tra i pilastri, siepe, palme e alberelli: circa 115) e le quattro
        **piazzette** OSM con cedri, pini, siepi e panchine;
      - Casino di Meninni e villette preparati dopo «Parti» (`Tiles.later`): «Pronto» 1,36 s su PC e 1,29 sul telefono (erano 1,45 e 1,42);
      - nel README il refuso di OSM («Via Carlo Bertocchi», il poeta è Carlo Betocchi): nel diorama resta il nome OSM.
- [ ] Villette, ritocchi possibili: i piani unità per unità dove la schiera mescola villette e palazzine (oggi una riga per sagoma più
      le eccezioni della tabella `VILLETTE`), la trama dei coppi (oggi tinta unita, come i tetti del centro storico).
- [ ] Casino di Meninni, ritocchi possibili: il muro di cinta a est e a sud (il satellite non lo mostra), i muretti a secco e i
      pali col filo spinato dello spiazzo (Street View), una foschia leggera vicino al rudere se il committente la vuole.
- [x] **N5 · Capotenda e vigna di Botromagno** (`fase-3-4-n5-capotenda-vigne`, PR #25; piano approvato il 14/10/2026, unita il
      14/10/2026 con l'approvazione del committente):
      - **a piedi**: carrarecce e sentieri OSM di Capotenda (9 vie, «Sentiero di Capotenda»), tre anelli col sentiero degli scavi; il
        **guado** (eccezione approvata, `GUADO`): la figurina passa su 8 sassi sopra l'acqua e gira con la goccia sul greto dell'altra
        sponda; il mezzo prende 393 m in più di Via Madonna della Stella, con la goccia all'imbocco della carrareccia. Rete da 1 549 a
        1 569 tratti, da 94,28 a 96,77 km, gocce da 13 a 14; a piedi da 97 a 114 tratti, da 5,59 a 7,70 km;
      - **la gola** incisa tra il belvedere e il guado (`GOLA`, `Gola`): letto 7,5 m più giù, pareti di calcare chiaro a strati entro
        18 m, sette laghetti nel letto (posizioni indicative), cengia per i sentieri vicini, maglia vicina a 7,5 m;
      - **Capotenda** (`Capotenda` in sezione 6d, dopo «Parti»): passerella di legno a zig-zag col corrimano (è il sentiero OSM, satellite
        a zoom 20), bancata delle cave di salnitro con le bocche e due grate, grotta del Padre Eterno nella parete, muretti a secco e la
        rovina, cespugli sulle pareti; scheda «Capotenda» (testo approvato) e luogo nell'elenco («La gravina e il paesaggio»);
      - **vigna di Botromagno**: classe `vigna` (16) dell'uso del suolo, 18 200 m², filari a spalliera nord-sud ogni 2,5 m da vicino;
      - misure (`shots/prestazioni-dopo-n5.txt`): 420 KB compressi (+9 invece dei 4 stimati), triangoli PC «alta» 342 100, telefono
        «centro» 232 300, vista «capotenda» 26 500 / 22 500, draw call invariate, «Pronto» 1,35 s; `interazioni` 70 controlli verdi.
- [x] **Peso** (decisione del committente del 14/10/2026, dopo N5): «se sforiamo non succede nulla, dobbiamo far venire il lavoro fatto
      bene». Il tetto di 450 KB compressi resta un riferimento, non un vincolo: prima viene la qualità; si dice comunque quanto pesa ogni
      blocco.
- [ ] Capotenda, ritocchi possibili: il belvedere «Patre Eterno» su Via Madonna della Stella (oggi niente), la casetta bianca sul pianoro
      (satellite), le canne attorno al laghetto grande (tolte per il peso), la posizione vera delle cave e dei laghetti con altre foto.
- [x] **N5b · uliveti, Casino Scacchi e Sportland** (`fase-3-4-n5b-uliveti-scacchi`, PR #26; piano approvato il 14/10/2026 con le risposte
      «1b, nessuna scritta né cartellone a Sportland ma zona riconoscibile»; unito su `main` il 14/10/2026):
      - **uliveti a filari**: otto campi (`ULIVETI`, classe 17 «filari», `GEO.uliveti`, `Tiles._olives`), ulivi ogni 7 m, da lontano metà senza tronco;
      - **Casino Scacchi** (rudere OSM w411138777, oggetto `Scacchi`): due piani senza tetto con la cima crollata, portale, finestre murate,
        corpo basso; cappella con la vela e l'edera; terrazzamenti a muretti a secco con mandorli e ulivi; macchia nel fossato; solo l'etichetta;
      - **Sportland**: piani veri degli edifici (pizzeria a due piani, tettoie, palestra), campi da calcetto e tennis con righe, porte, rete,
        recinzioni alte e torri faro, cancello con l'arco senza scritta, piazzale sterrato; nessuna etichetta;
      - **strada**: la SP201 di nuovo percorribile fino al bivio di via Guardialto Alto (OSM w1158532123) e questa fino al piazzale dei campi,
        con la goccia (eccezione in CLAUDE.md); rete da 1 569 a 1 573 tratti, da 96,77 a 97,25 km, 15 gocce; pendenza massima 16,5%;
      - **richieste nuove durante il blocco**: niente ulivi nel prato tra Via Madonna della Stella e la gravina (`PRATO_STELLA`): stanno
        dall'altra parte della strada (uliveto n. 8, verso Contrada Botromagno); la roccia della gravina **grigio-bianca** con la macchia
        a chiazze (`PALETTE.strata`, `Tiles._banks`), sotto lo stadio e lungo tutto il torrente;
      - `Plane.dbl`: i poligoni scritti a mano con numeri interi rallentavano `Plane.contains` per tutti («Pronto» +150 ms);
      - misure: 430 KB compressi (+10); triangoli PC «alta» 341 600, telefono «centro» 232 100 (invariati); viste nuove «sportland» 45 300 /
        39 500 e «salsa» 133 600 / 160 400; draw call invariate; «Pronto» 1,46 s su PC e 1,36 sul telefono (prima 1,34 e 1,31 nella stessa sessione: in gran parte la compilazione degli shader, che oscilla); `difetti.mjs` come prima.
- [ ] Da N5b, ritocchi possibili: dove guarda davvero la facciata del Casino Scacchi (scelta: sud-est), la sagoma vera del corpo alto
      (OSM è stretta e lunga), il manufatto tondo di Sportland (w411140007), il colore dello sterrato di via Guardialto Alto.
- [x] **N5c · Hortus a piedi** (`fase-3-4-n5c-hortus`, PR #27 in bozza, 15/10/2026): Via Giacomo Leopardi pedonale fino al cancello di Hortus (OSM w1384781495) e anello nel giardino a terrazze (53 m, terra battuta). Cancello aperto per l'accesso pedonale, panchina panoramica in legno e ferro sulla terrazza alta affacciata sul Fondovico e la rupe di San Michele con sosta (`action: 'stand'`), apertura automatica della scheda e comparsa del pulsante «Riprendi il percorso» che al clic fa rialzare la figurina completando l'anello e tornando all'auto su Via San Vito Vecchio. Scheda descrittiva verificata e inclusione in «Piazze e giardini». Prove verdi: `simula` (20,14 km simulati, carreggiate e dettagli liberi), `interazioni` (77 controlli), `difetti` invariato; foglio prima/dopo `riferimenti/foto_n5c/n5c-prima-dopo.jpg`.
- [x] **N6 · mezzi nuovi** (`fase-3-4-n6-mezzi`, PR #28, 15/10/2026): sostituiti i 4 mezzi terrestri originali con i modelli richiesti:
      - **Fiat Panda del 2013** (terza serie "Squircle", 3,65 × 1,64 × 1,55 m, passo 2,30 m): fari alti arrotondati, DRL a sfera, fascione laterale a squircle, terza luce laterale, barre longitudinali sul tetto e colore Rosso Pastello Fiat (`#c4261d`);
      - **Audi RS Q8** (SUV coupé sportivo, 5,01 × 2,00 × 1,70 m, passo 2,99 m): mascherina Singleframe ottagonale RS a nido d'ape nero, fari Matrix LED affilati, parafanghi "quattro blisters" allargati, cerchi enormi da 23", fascia LED posteriore a tutta larghezza e doppio terminale di scarico ovale RS;
      - **Ferrari Monza SP2** (Icona series barchetta biposto aperta senza parabrezza, 4,66 × 1,99 × 1,15 m, passo 2,72 m): Virtual Wind Shield aerodinamico davanti al pilota, spina centrale divisoria, carenature twin buttress / gobbe aerodinamiche posteriori, fari a lama LED, striscia continua a LED posteriore, estrattore in carbonio con 4 scarichi tondi, interni in cuoio e finitura Rosso Corsa metallizzato (`#c81e24`);
      - **John Deere serie 8R coi contropesi anteriori** (410 CV, 6,65 × 2,55 × 3,45 m, passo 3,05 m): castello zavorre a valigetta in ghisa frontale sporgente a sbalzo con gancio, ruote posteriori giganti da 2,16 m con cerchi gialli zavorrati, cofano lungo verde/giallo John Deere, cabina panoramica CommandView IV a 4 montanti con doppi lampeggianti e scarico verticale con sbuffi di fumo procedurale;
      - la mongolfiera (quinto mezzo volante) resta invariata;
      - vincolo delle 4 mesh consolidato (`opaqueMaterial`, `haloMaterial`), zero draw call aggiuntive, compatibilità id preservata (`panda`, `rs6`, `huracan`, `deere` + alias `rsq8`, `monza`);
      - prove verdi: `npm run simula` (0 problemi, 0 case sulla strada), `npm run interazioni` (77 controlli), `node difetti.mjs` invariato;
      - screenshot completi e foglio comparativo salvato in `riferimenti/foto_n6/n6-prima-dopo.jpg`.
- [x] **N7 · cinema, teatri e luoghi della cultura** (`fase-3-4-n7-cultura`, PR #29, 15/10/2026):
      - **modellazione prospetti** in `Details.luoghiCultura(tops)` (strato `dettagli` dei riquadri urbani, zero draw call aggiuntive):
        1. *Cinema Teatro Mastrogiacomo* (Piazza Scacchi 16, edificio 306): prospetto in intonaco salmone chiaro, basamento e marcapiano in tufo, portale con stipiti e architrave profilati, insegna stilizzata a sbalzo con fascia oro e bacheche locandine a giorno;
        2. *Cinema Teatro Centrone* (Via Alcide De Gasperi 14, edificio 239): maestoso fronte tardo-liberty su Via De Gasperi, portale monumentale con colonne doriche scanalate e basamenti, balconata superiore con colonnine in tufo, grande rosone radiale ornamentale a 16 razze, due avancorpi laterali con coronamenti sagomati, mensole e insegna dorata;
        3. *Teatro Vida* (Via Giardini 72, edificio 494): ingresso moderno al civico 72 con vetrata scura e profili in ferro, insegna stilizzata rossa incorniciata, bacheca locandina illuminata a giorno e lanterna a muro a braccio;
        4. *Fondazione Museo Pomarici Santomasi* (Via Museo 20, palazzo seicentesco): portale monumentale bugnato ad arco a tutto sesto, stemma nobiliare in chiave di volta, balconata nobile con ringhiera in ferro battuto e lapide dedicatoria;
        5. *Gravina Sotterranea* (Rione Piaggio / Via Meucci, edificio 267): accesso agli ipogei ad arco in tufo, portale con cancello in ferro a barre verticali e lanterna antica a braccio con alone caldo;
        6. *Biblioteca Capitolare Finia* (Piazza Benedetto XIII, edificio 121): portale monumentale in pietra d'onore con colonne binate doriche, trabeazione con timpano triangolare spezzato e targa scolpita;
      - **schede POI verificate in `LANDMARKS`**: coordinate reali, vicinanza stradale verificata per il teletrasporto dal menu di pausa, cenni storici accurati;
      - **gruppo tematico in `POI_GROUPS`**: aggiunto `Cinema, teatri e cultura` con tutti e 6 i luoghi;
      - prove verdi: `npm run simula` (0 problemi, 0 case sulla strada, dettagli liberi), `npm run interazioni` (77 controlli), `node difetti.mjs` invariato;
      - screenshot ortogonali ad alta definizione e foglio d'insieme in `riferimenti/foto_n7/n7-luoghi-cultura.jpg`.
- [x] **N8 · cartolina, giro guidato e ritocchi** (`fase-3-4-n8-cartolina-giro`, 15/10/2026):
      - **Cartolina da Gravina in Puglia**: cattura WebGL ad alta risoluzione con cornice color tufo/pergamena calda (`#f4eee2`), filetto dorato (`#cca84a`), passepartout interno, titolo in caratteri serif «GRAVINA IN PUGLIA», sottotitolo con il luogo corrente dinamico (monumento o via), credito «Un progetto di Giuseppe Cassano», link al sito e attribuzioni OSM/Copernicus; supporto Web Share API su dispositivi mobili e download immediato PNG su PC; pulsante dedicato nell'HUD (`#btn-postcard`), scorciatoia da tastiera (tasto `C`) e notifica toast elegante (`Cartolina scattata!`, `Cartolina salvata!`);
      - **Giro guidato dei monumenti (14 tappe)**: sequenza logica tra centro storico, rioni rupestri, luoghi di cultura e archeologia (Ponte Acquedotto, Bastione medievale, San Michele delle Grotte, Gravina Sotterranea, Cattedrale, Chiesa del Purgatorio, Palazzo Orsini, Cinema Teatro Mastrogiacomo, Monumento ai Caduti, Cinema Teatro Centrone, Santa Lucia, Hortus, Botromagno, Madonna della Stella); attivazione da schermata iniziale (`#btn-tour-start`) e da menu di pausa (`#btn-pause-tour`); navigazione automatica con selezione intelligente della via ottimale a ogni bivio; banner HUD dedicato in alto con avanzamento (`Tappa X/14: [Nome] (a [D] m)`), pulsanti `Prossima` ed `Esci dal giro` (e tasto Esc); rallentamento dolce all'arrivo alla tappa (2,5 m/s) e apertura automatica della scheda;
      - **Camera post-teletrasporto (`Rig.snap`)**: azzeramento completo delle variabili di stato (`lift = 0`, `slope = 0`, `sitMix = 0`) ed esecuzione di due passate di convergenza `update(0, driver)` in modo che `#roofLift` e arretramento convergano istantaneamente, eliminando qualsiasi vicinanza ai tetti;
      - **Schede descrittive e panchina**: impostato `max-height: min(280px, 46dvh)` e scroll verticale con scrollbar sottile; aggiunta classe `.card--bench` per non occludere il monumento o il panorama durante le soste in panchina; scheda del Monumento ai Caduti sintetizzata a 50 parole;
      - **Misure e prove**: `index.html` 440 KB compresso (sotto il limite di 450 KB), 60 fps costanti su PC e mobile, 0 draw call aggiuntive, 0 errori in console; prove `npm run simula` (0 problemi, 0 case sulla strada), `npm run interazioni` (tutti i controlli verdi) e `node difetti.mjs` invariati; foglio fotografico in `riferimenti/foto_n8/n8-cartolina-giro.jpg`.
- Versione in inglese: non ora.

### Fase 3.4, blocco G · percorsi a piedi, quote reali, camera e radio (PR #12, unita il 30/09/2026) ✅

Richiesto il 28/09/2026. Oltre al blocco G del piano, il committente ha chiesto una camera che si
muove attorno al mezzo (il blocco B) e una radio. Le canzoni di Non-Stop-Pop FM (GTA V) sono
commerciali e protette: il committente ha scelto musica ambient originale, generata dal codice.

- [x] Piano e risposte del committente: scalinate cieche decorative, musica ambient «alla
      Minecraft», camera automatica e manuale, correzione della camera della pausa.
- [x] Dati del centro storico (nodi, vie, vie decorative, edifici) con il `CODEC`, senza
      perdite: da 277 a 240 KB compressi, ed è il margine che paga tutto il resto.
- [x] **Percorsi a piedi**: 19 tratti reali (584 m), di cui 2 scalinate (70 m); +7 anelli nel
      centro storico. Rete: 1 461 tratti, 908 incroci, 87,20 km. Le altre 5 scalinate finiscono
      nel vuoto nei dati (a 8–19 m dalla via più vicina) e restano decorative.
- [x] Il mezzo si ferma a 3,2 m dall'imbocco, scende una figurina (circa 200 triangoli, una mesh),
      il mezzo aspetta al tratto carrabile d'uscita (si sposta fuori dall'inquadratura). Targa,
      cartelli «a piedi» / «al mezzo», minimappa tratteggiata, camera più bassa.
- [x] In fondo a Via giudice Montea (verso la scalinata), Via Civita e Via Matteotti la goccia non
      ci sta: si prosegue per forza a piedi. Alla testata del ponte il ponte ha la precedenza.
- [x] **Quote reali** come guida per la discesa dei rioni (`GEO.rioni`): Piaggio fino a 17 m
      (prima 8), Fondovico circa 12 m come prima, pendenze delle vie come prima (massimo 19%).
      Scalinata di Via giudice Montea da 4 a 32 gradini. Canyon e cigli restano a mano.
- [x] **Camera**: giro automatico attorno al mezzo (tre quarti, fianco, davanti; dietro prima
      degli incroci) e camera libera (trascinamento, rotella, pizzico, «Segui il mezzo», ritorno
      dopo 4 s). In pausa si gira e si zooma; la camera della pausa non entra più nei tetti.
- [x] **Radio**: sei brani ambient originali generati con Web Audio (pianoforte, celesta, flauto,
      tappeto e riverbero), pulsante Musica, tasto M, brano successivo, volume.
- [ ] Provare su un telefono vero: tocchi della camera libera, musica con lo schermo bloccato.
- [ ] Figurina: se piace, variare vestiti e cappello a ogni discesa.

### Fase 3.4, blocco A · crediti e ricerca su Google (PR #7, unita il 28/09/2026) ✅

- [x] Unico credito Giuseppe Cassano; nessun riferimento allo sponsor precedente nei file.
- [x] Metadati (titolo, descrizione, canonical, Open Graph, Twitter card, JSON-LD, icona).
- [x] Pannello «Il progetto» con testo vero e `<noscript>` più ricco.
- [x] `og-image.jpg` generata dal diorama (`npm run anteprima`) e `sitemap.xml`.
- [x] Schermata iniziale compattata: a 1280×720 credito e attribuzione ODbL uscivano dallo schermo.
- [x] Proprietà creata in Google Search Console (prefisso URL) e `<meta name="google-site-verification">`
      nel `<head>`: non va tolto, altrimenti la verifica decade.
- [x] Search Console (28/09/2026): proprietà verificata con il tag HTML, `sitemap.xml` inviata,
      indicizzazione della pagina richiesta (è in coda di scansione prioritaria).
- [ ] **Ricontrollare la sitemap tra qualche giorno** (Search Console → Sitemap). Subito dopo
      l'invio risultava «Impossibile recuperare», senza nessuna lettura: è normale per una
      proprietà appena creata, e il file è valido (200, `application/xml`). Se resta così, reinviarla.
- [x] Descrizione del repository su GitHub aggiornata, con il link al sito nel riquadro About.

### Fase 3.4, blocco C · la città intera (PR #8, unita il 28/09/2026) ✅

- [x] Pipeline: zolla di 2,9 × 3,1 km (12 × 13 riquadri da 240 m), 80 km di vie percorribili
      (1 390 tratti, 861 incroci) più 238 vie cieche decorative, 1 828 edifici della città,
      quote Copernicus GLO-30 smussate, uso del suolo, binari FAL e RFI, luoghi OSM via Overpass.
- [x] Castello Svevo dentro il diorama, con la sterrata reale percorribile (risposta 7 del
      committente). La zona industriale è il P.I.P. (risposta 3): strada nel blocco F.
- [x] Riquadri con terreno a 5/15/30 m, una mesh per riquadro; finestre, marciapiedi e binari
      disegnati dallo shader; costruzione in sottofondo; nebbia a 1,1 km.
- [x] Anche vie, case, finestre, torrini e alberi del centro storico nei riquadri: sul telefono
      il fotogramma peggiore è sceso da 296 000 a 242 000 triangoli (tetto 250 000).
- [x] Minimappa e mappa della pausa vettoriali, con zoom e trascinamento; luoghi per gruppi.
- [x] Attribuzione Copernicus (art. 6(b)) nella schermata iniziale, sotto e sopra la mappa della
      pausa e, in breve, sotto la minimappa; art. 6(c) nel README.
- [x] Prove: `simula` verde anche con gli alberi del centro storico controllati; `interazioni`
      verde; `prestazioni.mjs` con i triangoli per strato dei riquadri.
- [x] **Camera della pausa in città**: l'orbita (24 m sopra il mezzo) sfiorava o entrava nei tetti
      delle palazzine. Corretta nel blocco G (`#aerialPose` usa `#roofLift`).
- [ ] **Schermata iniziale in orizzontale sul telefono**: il pannello sfora di circa 50 px e la
      riga delle quote Copernicus si vede solo scorrendo (chat interfaccia).
- [ ] Provare la città su un telefono vero (fps, tempo di costruzione, calore).
- [x] Dopo l'unione: blocco F (strade per il Bosco Difesa Grande e il P.I.P.), unito.

### Fase 3.4, blocco F · strade per il Bosco Difesa Grande e il P.I.P. (PR #10, unita il 28/09/2026) ✅

- [x] Regola del **tracciato reale compresso** in `CLAUDE.md` (eccezione come il Ponte Acquedotto).
- [x] Tre zolle (città, P.I.P., Bosco) in `GEO.meta.zolle`; plinto, riquadri e minimappa per zolla.
- [x] Strada del Bosco: tracciato reale Overture di 5 397 m ridotto a circa 760 m, angoli reali,
      goccia in fondo. Rete: 1 433 tratti, 890 incroci, 86,26 km, 5 gocce.
- [x] Bosco di querce procedurale con radura e rifugio; P.I.P. a scala reale con i capannoni.
- [x] Scheda del Bosco sulle fonti (Wikipedia, SISEF, Overture). P.I.P. e rifugio: solo etichetta.
- [x] Prove: guida fino alla goccia e ritorno con la scheda che si apre; `simula` e `interazioni`
      verdi; budget rispettato (telefono 241 000 triangoli e 53 draw call al massimo, PC 334 000 e
      69; 277 KB compressi).
- [x] **Rifugio**: è l'area Quercus, con la scheda (blocco L).
- [x] Prossimo: blocco G (percorsi a piedi e quote reali del centro storico): fatto, con la
      camera libera del blocco B.
- [ ] Blocchi D (revisione del centro storico) ed E (nuovi luoghi): non ancora iniziati.

## Fatto finora

| Fase | Contenuto | Stato |
|---|---|---|
| 1–2 | Documento di progetto, rete stradale, mezzo, incroci, camera, interfaccia | ✅ |
| 2b | Dati reali: vie, incroci, edifici, torrente, ponte ad archi | ✅ |
| 2c | Vie libere dalle case, archi reali, quattro mezzi, pausa, teletrasporto, versione mobile | ✅ |
| 3 | Cattedrale e Purgatorio sulle fonti, chiese rupestri, rioni a gradoni con scalinate e abitazioni rupestri, altezze, cinque schede nuove, vetrina sulle arcate | ✅ approvata il 28/09/2026 |

## 1. Subito

- [x] **GitHub Pages attivo** da `main` / `(root)`:
      https://giuseppecassano5bit.github.io/gravina-3d/ risponde.
- [ ] **Provare su un telefono vero** (fps, leggibilità delle schede, tocchi sui cartelli) e
      annotare cosa non va.
- [x] **Fase 3 approvata** (28 settembre 2026).

## 2. Decisioni aperte (fase 3, punto 6): dettagli in `docs/DESIGN.md`, "Da decidere insieme"

- [x] **Percorsi pedonali e scalinate**: a piedi con una figurina (fase 3.4, blocco G).
- [x] **Allargare il diorama**: fatto nella fase 3.4, blocco C (la città intera).
- [x] **Quote reali** per la discesa dei rioni del centro storico: fatto come guida nel blocco G
      (il canyon e i cigli restano disegnati a mano).

## 3. Fase 4 · Rifinitura (dal piano originale)

- [x] **4.1 · Golden hour** (`fase-4-1-golden-hour`, PR #31): atmosfera Golden hour murgiana al calar del sole; cielo equirettangolare con gradiente crepuscolare profondo (cobalto, indaco, rosa, ambra, oro), alone solare morbido ad ampia diffusione radiale e disco luminoso; luce solare radente calda ambrata (`#ffa958`, intensità 3.15, azimut 248°, elevazione 11.5°), luce emisferica coordinata cielo/tufo (`#ffd5b2`/`#563e2f`, intensità 0.58), nebbia volumetrica all'orizzonte perfettamente intonata (`#e2a16d`); mappa d'ambiente riflessi mezzi (`VehicleFactory.setEnv`) arricchita; ACES Filmic Tone Mapping calibrato (esposizione 1.08) e ombre morbide senza acne (`normalBias: 0.45`); 60 fps costanti su PC e mobile, 0 draw call in più, peso invariato (440 KB compressi), prove `simula` (0 problemi, 0 case sulla strada) e `interazioni` (82/82) tutte verdi; foglio comparativo in `riferimenti/foto_4_1/4_1-prima-dopo.jpg`.
- [x] **4.2 · Sponde del Ponte, stabilità mezzi, rumore motori e boost Shift** (`fase-4-2-ponte-motori-stabilita`, PR #32 unita il 16/10/2026):
      - **Ponte Acquedotto e le due sponde fedelissime alla realtà**: studio approfondito da Google Maps e Street View; sponda ovest (versante opposto alla partenza del mezzo) con spalla monumentale in conci di tufo e pietra ancorata allo sperone roccioso naturale sotto l'arcata, eliminati i parapetti troncati nel vuoto con pilastrini terminali squadrati e modanati alle testate, muretto di contenimento e protezione continuo lungo il ciglio della gravina sulla rampa lastricata verso Madonna della Stella e Botromagno, balze rocciose e macchia mediterranea; sponda est (testata lato città / Fontana la Stella) con innesti a ventaglio di Via Fontana la Stella e Via giudice Montea, parapetti con pilastrini e Fontana della Stella rifinita con nicchia, modanatura e vasca integrata al muretto del belvedere;
      - **Stabilità di marcia dei veicoli**: eliminazione di ondeggiamenti, rollio e beccheggio eccessivo lungo i campioni delle vie in `Driver` e `VehicleFactory`; anticipo di pendenza allargato (`pitchLookahead` a ±3,6 m) con smorzamento esponenziale morbido `damp(4.2, dt)`; filtro passa-basso di rollio del 2° ordine su `this.roll` (`damp(3.5, dt)`), calibrazione delle vibrazioni del telaio per una marcia solida, piantata e realistica;
      - **Rumore reale procedurale per ogni mezzo (`EngineAudio`)**: Web Audio procedurale specifico per ciascun veicolo in base a velocità, accelerazione e regime (V12 aspirato Ferrari Monza SP2, V8 biturbo Audi RS Q8 con sibilo compressore, 4 cilindri Fire Fiat Panda, diesel John Deere serie 8R con minimo scandito e fischio turbo, coordinamento bruciatore mongolfiera); pulsante e selettore volume motore nell'HUD (`#btn-engine`, `#engine-vol`, persistenza `localStorage`);
      - **Acceleratore potenziato su PC (Shift Boost)**: incremento del moltiplicatore `CONFIG.drive.boost` a `2.75` con transizione `boostRate: 2.0` per rendere i tratti lunghi periferici scorrevoli.
- [x] **4.3 · Via giudice Montea (salita, parapetto e case pericolanti), campi sportivi, Seminario Vescovile e posizioni cinema** (`fase-4-3-montea-cinema-campi`, PR #33 unita il 16/10/2026):
      - **Posizioni reali Cinema Centrone e Cinema Mastrogiacomo**: Centrone posizionato in Via Alcide De Gasperi 14 (`[416.7, -49.0]`) con facciata liberty in tufo e bugnato; Mastrogiacomo sulla cortina nord-est di Piazza Arcangelo Scacchi 16 (`[347.8, 49.3]`) con intonaco rosato, lesene in pietra e bacheche locandine in ferro battuto;
      - **Seminario Vescovile in Piazza Benedetto XIII (civico 25)**: portale monumentale bugnato in tufo, stemma vescovile scolpito in chiave di volta con nappe pastorali, fasce marcapiano modanate, portone ligneo massiccio, finestre e balcone centrale con ringhiera in ferro battuto e targa commemorativa in marmo; aggiunto a `LANDMARKS` e al gruppo POI «Chiese e conventi»;
      - **Campi da calcio e calcetto procedurali della città (senza etichette né schede)**: Campetto parrocchiale SS. Crocifisso "Giuseppe Dipalma" in erba sintetica bicolore, righe, porte da calcetto con rete, recinzione alta e piloni faro; Campetto parrocchiale San Domenico con manto verde smeraldo e porte; campetti oratoriali; esclusione alberi generici dall'interno dei campi da gioco (`Details.insidePitch`);
      - **Via giudice Montea (dal ponte alla città)**: eliminata la buca anomala del DSM Copernicus, salita continua e dolce dal Ponte Acquedotto (`y = -4,62 m` a n = 287) al Bastione medievale (`y = -1,98 m` a n = 196) e verso Via Calderoni e la città; muretto continuo di parapetto in conci di tufo e copertine sagomate sul ciglio della gravina; cortina di case storiche a 2 piani; case a pericolo crollo reali puntellate con robuste travi inclinate in legno e acciaio, tiranti metallici passanti a croce/X, lesioni diagonali a gradini sui conci di tufo, finestre/varchi sbarrati con assi di legno e transenne stradali di sicurezza a bande bianco-rosse con cartelli gialli "Pericolo Crollo"; linea d'occhio panoramica dal belvedere Cattedrale al ponte 100% pulita (0 ostacoli);
      - Verifiche verdi: `npm run simula` (0 problemi, 0 case sulla strada, `dettaglisullastrada: {}`, 0 errori) e `npm run interazioni` (83/83 controlli superati con successo).
- [x] **4.4 · Camera dopo il teletrasporto, schede sul telefono, accessibilità e licenza** (`fase-4-4-camera-schede-rifinitura`, PR #34 unita il 16/10/2026 con l'approvazione del committente, che ha ascoltato i motori):
      - **camera** (`Rig.snap`): tra cinque direzioni attorno al mezzo sceglie la più libera e resta sopra i tetti entro 20 m
        per 2,5 s, poi scende piano; sui 42 luoghi con la scheda quelli che partivano a ridosso di un tetto da 16 a 0;
      - **schede** sul telefono in verticale: al massimo un terzo dello schermo, scorrevoli col fondo che sfuma; nascoste,
        non prendono più i tocchi sulla scena;
      - **accessibilità dell'HUD**: `aria-pressed` con nome fisso, `aria-keyshortcuts`, gruppi e regioni, cursori del volume
        con la percentuale; con il fuoco su un cursore le frecce lo spostano (prima sterzavano);
      - **licenza MIT** nel file `LICENSE`;
      - **Ponte Acquedotto, testate** (richiesta del committente): i pilastrini d'angolo e i muretti a ventaglio di est
        stavano dentro la carreggiata di Via giudice Montea e Via Fontana la Stella, il raccordo ovest chiudeva Via giudice
        Montea; ora muretti e pilastrini solo fuori dalla carreggiata, e `simula` controlla anche il ponte (prima escluso);
      - **rumore dei motori rifatto** (richiesta del committente: «fastidioso e ridicolo»): modello a scoppi per cilindro
        sui dati veri dei motori, tubi di scarico, silenziatore, aspirazione, turbo e cambio con le marce, senza registrazioni
        (sono di terzi); prova `node motori.mjs` coi file audio da ascoltare in `tools/test/shots/`;
      - prove: `npm run simula` verde (0 problemi, 0 case e 0 dettagli sulla strada) e `npm run interazioni` 83/83 dopo
        ogni compito.
- [x] Terza richiesta del committente (16/10/2026): **velocità massime per mezzo** (Deere 50, Panda 80, Audi e Ferrari 180)
      con l'accelerazione vera, **limiti per tipo di strada** (scelta del committente), frenata prima degli incroci, cambio
      che a velocità costante mette la marcia lunga, trattore più cattivo sotto sforzo; prova `node velocita.mjs`.
- [x] Rumore dei motori approvato dal committente («perfetto ottimo lavoro mi piace», 16/10/2026) dopo tre giri di ascolto.
- [x] **Prestazioni dopo il blocco 4.4** (blocco 4.5, `shots/prestazioni-dopo-4-4.json`): tutto nei tetti (PC 352 400
      triangoli e 59 draw call al massimo, telefono 232 300 e 35; 60 fps in tutte le viste). Corsa a 180 km/h verso il Bosco
      (Ferrari, 30 s, motore acceso o spento): 60 fps, il 99% dei fotogrammi sotto i 19 ms, nessun blocco lungo (i riquadri sono
      già tutti costruiti a 2,5 s dall'apertura). Motore: 20–27 µs per blocco audio da 128 campioni (circa 1% del filo audio sul
      Mac; su un telefono medio 5–10%).

### Blocco 4.5 · La guida (branch `fase-4-5-guida`, PR #35 in bozza; piano approvato il 16/10/2026)
- [x] **Niente tremolio sull'asfalto** («movimenti parkinsoniani»): la scocca trema solo al minimo, sobbalzi solo su pietre,
      ciottoli e sterrati (`ROUGH`); a velocità alta sterzo e beccheggio guardano più avanti. Sull'asfalto beccheggio da 0,49 a
      0,015 mrad per fotogramma², sobbalzo da 1,7 mm a 0; sulle pietre come prima.
- [x] **Con l'acceleratore si tira dritto agli incroci** (decisione del committente): la via carrabile più dritta, rallentando
      solo per la svolta (`Driver.cornerSpeed`); una scelta a mano si rispetta. La frenata ora segue la curva (arrivava 15 km/h lunga).
- [x] **Acceleratore sul telefono**: casella nella schermata iniziale e interruttore nella pausa («almeno 6 GB di memoria; per
      l'esperienza migliore usa un computer»), pulsante «Accelera» da tenere premuto. Regola aggiornata in `CLAUDE.md`.
- [x] **Vie lunghe dritte** (Via Tripoli, Via Alcide De Gasperi): `Raddrizza`, vedi `DESIGN.md` § 6. Le residenziali restano
      come nei dati (case sul filo della via).
- [x] Prove: `simula` verde, `interazioni` 86/86 (nuove: Shift tira dritto, pulsante «Accelera» sul telefono), `velocita` verde
      (svolte entro la velocità della curva), `difetti` invariati o migliori; prestazioni `shots/prestazioni-dopo-4-5.json`
      (60 fps, stessi triangoli e draw call; «Pronto» +0,19 s su PC e +0,26 s sul telefono, di cui 91 ms per `Raddrizza`).
- [ ] Prossimi: **Blocco 4.6** (altezze degli edifici, sponda opposta del ponte, suoni del bosco con animali veri) e **Blocco 4.7**
      (restyling, inglese, schermo intero, schede in orizzontale, schermata iniziale in orizzontale).
- [ ] Da decidere con il committente: un pulsante per lo **schermo intero** (non c'è; su iPhone Safari non funziona fuori dai video).
- [x] Musica procedurale Web Audio: la radio ambient del blocco G.
- [x] Camera: giro automatico e camera libera nel blocco G.
- [ ] Prestazioni su telefono: livelli di dettaglio per le finestre, misura su un telefono vero.
- [ ] Interfaccia: restyling con le skill di design, inglese opzionale (accessibilità dell'HUD fatta nel blocco 4.4).
- [x] Licenza del codice: MIT, file `LICENSE` (© 2026 Giuseppe Cassano; blocco 4.4). I dati di `GEO` restano ODbL e Copernicus.

## 4. Da sistemare o verificare (emerso finora)

**Fedeltà**
- [x] Campanile di **San Francesco**: modellato nel blocco D, all'angolo nord della facciata (Street View).
- [x] **Campanile della Cattedrale** in fondo a est del fianco sud e secondo rosone a ovest (blocco D, Street View e foto).
- [ ] **Addolorata e Annunziata**: stessa sagoma in Via Borgo per OSM, Overture e Google; il
      catalogo dei Beni Culturali ha l'Addolorata in «Via Borgo Vecchio», GravinaOggi l'Annunziata
      sconsacrata nella «vecchia via Borgo». Nessuna fonte dice che siano la stessa chiesa: resta
      l'etichetta. Se il committente lo sa, si può decidere il nome.
- [x] Schede rilette sulle fonti per i luoghi nuovi del blocco D. Le schede della fase 3 restano
      quelle con le fonti nel README.
- [x] **Abitazioni rupestri**: restano 20 sui gradoni (né dati né fonti le collocano una per una);
      nel blocco D le grotte fitte delle Sette Camere, dove la posizione c'è (OSM e foto).
- [x] **Altre chiese** (Santa Teresa, Santa Sofia, San Nicola, Addolorata): rifatte nel blocco N3 dalle foto (Street View,
      Commons, foto di utenti su Google Maps).

**Terreno e percorso**
- [x] Le scalinate reali avevano pochi gradini perché le quote erano stilizzate: con le quote
      reali (blocco G) quella di Via giudice Montea ne ha 32 invece di 4.
- [x] Pendenze (blocco D): nel centro storico le vie del mezzo stanno entro il 18%
      (`CONFIG.road.maxGrade`, Via Fontana la Stella dal 21%). Il sentiero verso Botromagno e la
      scalinata di Via giudice Montea sono tratti a piedi e restano ripidi.
- [x] Gradino di 15–18 m a sud della città (da Via Goito a Via Tripoli): punti ripetuti nel ciglio
      est, corretto nel blocco D.
- [x] Fuori dal centro storico, a nord, alcune vie erano ripide (Via Savoia, Via Giardini, Corso
      Aldo Moro, 29–37%): era il raccordo del terreno, allargato nel blocco E. Resta Via Goito (22%).

**Camera e interfaccia**
- [x] Dopo il teletrasporto la camera a volte partiva troppo vicina a un tetto: dal blocco 4.4 `rig.snap`
      sceglie la direzione più libera e tiene la camera sopra i tetti entro 20 m per 2,5 s (16 luoghi su 42
      a ridosso di un tetto, ora nessuno).
- [x] In verticale le schede lunghe (Cattedrale, Santa Sofia, circa 330 caratteri) occupavano
      molto schermo: dal blocco 4.4 al massimo un terzo dello schermo (da 280 a 248 px a 390 × 844), testo
      che scala con la larghezza, scorrimento col fondo che sfuma finché c'è altro testo; mentre si legge
      la scheda resta. Da nascosta non prende più i tocchi sulla scena (prima restava trasparente sopra).
- [ ] In orizzontale sul telefono il testo delle schede resta tagliato a tre righe: se si vuole, scorrevole
      come in verticale.
- [x] Vetrina, campo lungo: sui telefoni il mezzo era piccolo. Rifatte nel blocco M3: in verticale un
      campo medio sul mezzo vicino alla Fontana della Stella (`CONFIG.camera.showroom`, `node vetrina.mjs`).
- [ ] Prestazioni con la città intera (blocco C, `node prestazioni.mjs`): 543 000 triangoli in
      scena, al massimo 334 000 per fotogramma su PC e 242 000 sul telefono, 69 e 54 draw call.
      Misurare su un telefono di fascia media.

**Progetto**
- [ ] I marchi dei mezzi (Fiat, Audi, Lamborghini, John Deere) vanno verificati prima di un uso
      commerciale o promozionale.
