# Cosa resta da fare

Stato al 1° ottobre 2026: fase 3 approvata e online, blocchi A, C, D, E, F, G, I e L della fase 3.4 uniti.
Aggiornare questo file a ogni fase.

**Fase 3.4 (Gravina oltre il centro storico) in corso**: piano, dati, budget, rischi e divisione
del lavoro su due chat in [`PIANO_FASE_3_4.md`](PIANO_FASE_3_4.md).

### Fase 3.4, seconda parte (decisioni del 30/09/2026)

Ordine: I → D → E → L → M1 → M2 → M3 → N, dettagli e decisioni nella sezione 7 del piano.

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
      (in OSM non ce l'ha: nel diorama «Strada nel bosco»); la chiesa di Santi Pietro e Paolo
      (nome da Overture).
- [ ] **Prestazioni**: se dopo i blocchi M e N il diorama resta pesante, il committente pensa a
      un'impostazione che carichi il mondo solo attorno alla visuale; in città non si riduce niente,
      al massimo in periferia dove dall'auto non si vede (01/10/2026).
- [ ] Telefono in orizzontale, partenza sul ponte: il contatore di debug segna 74 draw call (tetto 70),
      uguale su `main` prima di E e L (`node foto.mjs orizzontale`). In verticale il massimo è 48.
      Da guardare nel blocco N con i ritocchi dell'orizzontale.
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
- [ ] **M2 · percorsi a piedi, zone pedonali e suoni del bosco** (`fase-3-4-m2-a-piedi`): anello V2
      del vivaio e Base Scout, sentiero degli scavi, Parco Robinson, Via Ianora, scale della stazione,
      Villa Comunale e Piazza della Repubblica pedonali, Fiera e strada dello stadio; suoni del bosco
      senza pioggia (uccelli, cicale, gufo, cinghiale, lupi lontani). Richieste aggiunte dal
      committente il 01/10/2026: sottopassaggi dove le vie incrociano i binari, Pineta e Parco
      Robinson costruiti (cancelli, giostre, area pedonale), strada del Casino di Meninni
      percorribile con un percorso a piedi dentro, il fischietto «cola cola» nel suo punto.
- [ ] **M3 · mezzi realistici e mongolfiera** (`fase-3-4-m3-mezzi-mongolfiera`): auto per sezioni
      con guidatore, stop e frecce senza draw call in più; mongolfiera come quinto mezzo, giro fisso
      da Botromagno sopra il centro storico, prima e terza persona.
- [ ] **N · cartolina, giro guidato e ritocchi** (`fase-3-4-n-cartolina-giro`).
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

- [ ] Golden hour: luci, nebbia e ombre nette; un leggero bloom solo se regge i 60 fps.
- [x] Musica procedurale Web Audio: la radio ambient del blocco G.
- [x] Camera: giro automatico e camera libera nel blocco G.
- [ ] Prestazioni su telefono: livelli di dettaglio per le finestre, misura su un telefono vero.
- [ ] Interfaccia: restyling con le skill di design, accessibilità, inglese opzionale.
- [ ] Licenza del codice (per esempio MIT) e file `LICENSE`.

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
- [ ] **Altre chiese** (Santa Teresa, Santa Sofia, San Nicola, Addolorata): portale generico,
      perché su Street View i vicoli stretti non mostrano bene le facciate. Servono foto.

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
- [ ] Dopo il teletrasporto la camera a volte parte troppo vicina a un tetto (screenshot
      `30-teletrasporto`): controllare l'altezza iniziale in `rig.snap`.
- [ ] In verticale le schede lunghe (Cattedrale, Santa Sofia, circa 330 caratteri) occupano
      molto schermo: accorciarle o renderle scorrevoli.
- [ ] Vetrina, campo lungo: sui telefoni il mezzo è piccolo. Le pose si tarano in
      `CONFIG.camera.showroom` con `node vetrina.mjs "[…]" "[…]"`.
- [ ] Prestazioni con la città intera (blocco C, `node prestazioni.mjs`): 543 000 triangoli in
      scena, al massimo 334 000 per fotogramma su PC e 242 000 sul telefono, 69 e 54 draw call.
      Misurare su un telefono di fascia media.

**Progetto**
- [ ] I marchi dei mezzi (Fiat, Audi, Lamborghini, John Deere) vanno verificati prima di un uso
      commerciale o promozionale.
