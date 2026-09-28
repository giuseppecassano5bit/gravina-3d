# Gravina 3D: documento di progetto

Diorama interattivo low-poly del centro storico di Gravina in Puglia, costruito sulle
**vie, gli edifici e il torrente reali**. È un unico file HTML (`index.html`) con Three.js:
tutta la geometria è procedurale, i dati geografici sono incorporati come costante.

Progetto open source di **Giuseppe Cassano** ([github.com/giuseppecassano5bit](https://github.com/giuseppecassano5bit)).

---

## 1. Visione

Una "Google Earth in miniatura" al tramonto. Una zolla di tufo sospesa nel cielo dorato,
tagliata dalla gravina e attraversata dal Ponte Acquedotto. Appena si apre, il mezzo
aspetta accanto al ponte: il visitatore sceglie tra **Fiat Panda 4x4 del 1999, Audi RS6
Avant, Lamborghini Huracán e trattore John Deere**, poi il mezzo percorre da solo le vie
reali del centro storico e a ogni incrocio reale il visitatore sceglie dove andare. Può
fermarsi quando vuole: in pausa cambia mezzo o si teletrasporta toccando un luogo sulla
mappa. Lungo il percorso compaiono schede brevi sui monumenti.

| Principio | Scelta concreta |
|---|---|
| Fedeltà ai luoghi | Vie, incroci e sagome degli edifici vengono dai dati reali (OpenStreetMap via Overture Maps). |
| Stile a blocchi | Ogni edificio reale è un blocco estruso di tufo o intonaco, con finestre, persiane, terrazze o tetti in coppi. |
| Riconoscibilità | I monumenti hanno forme dedicate, verificate sulle fonti: Cattedrale con facciata tripartita, rosone a 24 raggi e campanile a cipolla, portale del Purgatorio con orsi e torri, chiese rupestri scavate, ponte ad archi su due ordini. |
| Vie libere | Nessun edificio sulla carreggiata: il mezzo non attraversa mai le case. Dove una casa scavalca davvero la via c'è un arco. |
| Zero collisioni, 60 fps | Il mezzo segue spline precalcolate sulla rete reale: niente fisica. |
| Anche su telefono | Interfaccia touch, pannelli che si adattano a verticale e orizzontale, risoluzione adattiva. |

---

## 2. Dati reali

### Fonte

**Overture Maps Foundation**, release `2026-09-23.1`. I temi usati (vie, incroci, edifici,
acque, infrastrutture, uso del suolo, luoghi) derivano in gran parte da **OpenStreetMap**
(© OpenStreetMap contributors, licenza ODbL 1.0). Alcuni luoghi hanno licenza CDLA-Permissive-2.0.

Dalla fase 3.4 servono anche:
* **OpenStreetMap via Overpass API** (stessa licenza ODbL): monumenti, chiese, stazioni, parchi e
  la sagoma del Castello Svevo, che Overture non ha tutti. Una query piccola, messa in cache in
  `tools/.cache/overpass.json`.
* **Copernicus DEM GLO-30** (tessera N40 E016): le quote del terreno fuori dal centro storico.
  Licenza libera con l'attribuzione dell'art. 6(b) sempre visibile (schermata iniziale, mappa
  della pausa, credito breve sotto la minimappa) e la clausola dell'art. 6(c) nel README.

### Pipeline (`tools/genera_dati.py`)

1. **Download mirato.** I file GeoParquet di Overture pesano centinaia di GB. Lo script legge
   solo il footer di ogni file (con richieste HTTP Range) e scarica soltanto i *row group* che
   intersecano il riquadro di Gravina: pochi MB in tutto. La cache finisce in `tools/.cache/`.
2. **Rete stradale.**
   - Considera le vie carrabili: secondarie, terziarie, residenziali, zone residenziali, pedonali, non classificate.
   - Le spezza nei loro **incroci reali**, cioè i *connector* di Overture.
   - Esclude le gallerie e taglia tutto ciò che esce dal diorama.
   - Pota i vicoli ciechi (2-core del grafo) e tiene la componente connessa principale.
   - Conserva alcune vie cieche importanti (Piazza Benedetto XIII, Via Civita, Calata Grotte San Michele, Larghetto San Francesco, Via Matteotti). In fondo a ciascuna aggiunge un'**inversione a goccia** dentro lo slargo reale, solo se c'è spazio tra gli edifici.
   - Il **Ponte Acquedotto** fa parte di Via giudice Montea, che nella realtà è pedonale: resta percorribile per scelta di progetto, ed è marcato "pedonale" nei dati e sulla targa.
3. **Edifici.** Sagome reali semplificate a 0,3 m, con cortili (fori), classe, nome e
   `level` (i corpi sopraelevati hanno `level = 1`). L'altezza si prende solo se è affidabile:
   numero di piani o altezza di OpenStreetMap. Le altezze stimate dalle immagini aeree
   (Microsoft ML Buildings, 35 edifici nell'area) si scartano perché nel centro storico sono
   spesso assurde (1,5-2,5 m per un condominio).
3b. **Vie libere dagli edifici** (`free_roads`). Le mezzerie OSM non stanno sempre al centro
   dei vicoli e le carreggiate avevano una larghezza fissa per classe: alcune facciate finivano
   sulla strada e il mezzo sembrava attraversare le case. Ora lo script:
   - **ricentra** ogni via tra le facciate (spostamento massimo 1,6 m, estremi fermi sugli incroci);
   - la **restringe** nei vicoli stretti: 20° percentile dello spazio tra le facciate, meno 0,35 m
     per lato, mai sotto 3,4 m (ci passa il trattore) né sopra la larghezza della classe;
   - **ritaglia** le sagome lungo carreggiata e slarghi, con 0,35 m di margine, e scarta le schegge.
     Il ritaglio usa la stessa curva Catmull-Rom centripeta che disegna `index.html`, non la
     polilinea: tra punti radi la curva se ne allontana anche di un metro;
   - trasforma in **archi** i corpi sopraelevati (`level = 1`) che la via attraversa per al
     massimo 14 m, come L'Arc D' Bench. La larghezza di ogni via viaggia con i dati.
4. **Morfologia.** Corso del Torrente La Gravina, falesie, mura, belvederi, aree pedonali e verdi, luoghi d'interesse,
   e le 7 **scalinate reali** (`highway=steps`, 165 m in tutto: Via giudice Montea, Gradoni San Giovanni Battista…).
5. **Ciglio del canyon.** È tracciato a mano, una volta sola, su belvederi, mura del Fondovico,
   falesie e testate del ponte (costanti `EAST_RIM` e `WEST_RIM`).
6. **Scrittura.** La costante `GEO` viene scritta tra i marcatori `@@DATI-GEO-INIZIO@@` e
   `@@DATI-GEO-FINE@@` di `index.html` (circa 420 KB, 170 KB compressi).
7. **Città intera (fase 3.4).** Tutto gira in circa 18 s con i dati in cache.
   - Zolla `AREA` di 2,88 × 3,12 km, divisa in 12 × 13 riquadri da 240 m (`TILE`); il centro
     storico è la zona `Z0` (est −340…450, nord −320…540).
   - Vie: stesse classi del centro storico; il 2-core toglie le vie cieche dei quartieri, che
     restano in `GEO.deco` come **vie decorative non percorribili** (disegnate, mai nella rete).
     Le vie con le facciate vicine sono "urbane" (flag 16, con i marciapiedi).
   - **Castello Svevo**: dentro `CASTLE_BOX` la strada di servizio, la sterrata e la vicinale
     reali chiudono un anello e diventano percorribili (la sterrata ha il flag 8).
   - Edifici della città in `GEO.city`, codificati in modo compatto (interi variabili, 0,25 m):
     tipo e altezza stimata per tipo e superficie (palazzine da 2 a 6 piani, capannoni 7–9 m,
     case di campagna 1–2 piani). Le altezze Microsoft si scartano anche qui: sono troppo basse.
   - Quote: il DSM Copernicus comprende tetti e alberi. In città si prende un percentile basso
     su 90 m e si smussa molto, in campagna poco; il letto del torrente è il minimo di traverso,
     sempre in discesa (`GEO.riverY`). Griglia `GEO.dem` ogni 30 m, in quarti di metro; `ALT0`
     (358 m s.l.m., l'altopiano della Cattedrale) è lo zero del diorama.
   - I cigli del canyon, tracciati a mano nel centro storico, proseguono a nord e a sud guidati
     dal DSM.
   - Uso del suolo `GEO.cover` ogni 15 m (città, piazze, parchi, sport, bosco, macchia, uliveti,
     industria, cimitero, cave, campi), compresso a sequenze: colora il terreno e sceglie gli alberi.
   - Binari FAL e RFI (`GEO.rails`, con i ponti) e luoghi con nome (`GEO.pois`, solo etichette).

### Numeri attuali

| Voce | Valore |
|---|---|
| Vie percorribili | 1 390 tratti, 861 incroci, circa 80 km (nel centro storico 157 tratti, 9 km) |
| Vie decorative (cieche, non percorribili) | 238 tratti, 21,6 km |
| Larghezza delle vie | da 3,4 m (vicoli) a 8 m; 37 tratti ristretti al minimo |
| Inversioni a goccia | 4 |
| Edifici reali | 518 nel centro storico (dopo il ritaglio) e 1 828 in città, nessuno sulla carreggiata |
| Archi sulle vie | 5 |
| Scalinate reali (solo decorative) | 7, 165 m |
| Edifici con altezza reale | 1 (Museo Santomasi, 3 piani); le altre sono stimate per zona |
| Area del diorama | 2,88 × 3,12 km (est −840…2040, nord −1140…1980), 12 × 13 riquadri da 240 m |
| Centro storico (zona Z0) | 790 × 860 m (est −340…450, nord −320…540) |
| Quote e uso del suolo | griglia di 97 × 105 quote ogni 30 m; 192 × 208 celle ogni 15 m |
| Binari e luoghi OSM | 25 tratti di binario (FAL e RFI); 54 luoghi con nome |

### Sistema di coordinate

* **Origine**: la Cattedrale (40.8174 N, 16.4134 E); 1 unità = 1 metro.
* **Assi Three.js**: `x` = Est, `y` = quota, `z` = −Nord.
* **Conversione**: `est = (lon − 16.4134) · 111 320 · cos(40.8174°)`, `nord = (lat − 40.8174) · 111 132`.

---

## 2b. La città intera (fase 3.4, blocco C)

**Zone di dettaglio**

| Zona | Dove | Edifici | Vie | Terreno |
|---|---|---|---|---|
| **Z0** | centro storico, fino a Piazza Scacchi e alla Villa Comunale | come nelle fasi 2–3: finestre vere, coppi, torrini, monumenti su misura | chianche con cordoli, archi, vicoli ristretti | maglia da 5 m, canyon e rioni a mano |
| **Z1** | città moderna | prismi sulla sagoma reale, tetti a terrazza, finestre e negozi **disegnati dallo shader** | asfalto, marciapiedi e strisce disegnati dallo shader, campionamento adattivo (2–8 m) | maglia da 15 m, quote reali |
| **Z2** | campagna attorno | case di campagna e capannoni | come Z1, sterrati in terra battuta | maglia da 30 m, ulivi e macchia radi |

**Riquadri** (sezione 6e, `Tiles`). La zolla è divisa in riquadri da 240 m e ogni riquadro è
**una mesh sola**: terreno, vie, edifici, binari, alberi e fianco della zolla. Così il frustum
culling scarta quello che non si vede, anche nel passaggio delle ombre, e le draw call restano
poche. Anche vie, case, finestre, torrini, cisterne e alberi del centro storico entrano nel loro
riquadro: si preparano prima con `Tiles.builderAt(e, n, strato)` e il riquadro li accoda quando
si chiude (`_begin` fa il terreno, `_finish` il resto). Tra maglie diverse i vertici di confine
seguono la maglia più larga: niente fessure. Le finestre coperte dalla casa accanto (muri in
comune) non si posano.

**Shader della città** (`cityMaterial`): colori per faccia come il resto del diorama, più un
attributo `aInfo` per vertice che dice il tipo di superficie. Finestre con le persiane per piano
e campata, negozi al piano terra, lamiera dei capannoni, marciapiedi, strisce, traversine e
rotaie costano zero triangoli; da lontano si sfumano nel colore medio. Le campate vengono dai
metri lungo il perimetro (`aInfo.w`), non dalle derivate: di sbieco sarebbero instabili.

**Quote.** Nel centro storico il terreno resta quello disegnato a mano; fuori, le quote
Copernicus smussate. Le vie seguono le pendenze reali e il terreno si spiana sotto vie e binari.

**Costruzione progressiva.** I riquadri del centro storico si costruiscono subito (il pulsante
Parti si abilita), gli altri pochi per fotogramma (7 ms), dal più vicino al mezzo; dopo un
teletrasporto quelli entro 420 m si costruiscono al volo. La nebbia chiude la vista tra 420 e
1 100 m, la camera finisce a 1 250 m.

**Profilo leggero** (telefoni e tablet): alberi dimezzati, anche nel centro storico; niente
torrini sulle palazzine; ombre solo dai riquadri del centro storico.

**Mappe** (sezioni 10–10b). La minimappa è vettoriale: disegna in memoria un quadro di 700 m
attorno al mezzo con una griglia spaziale, e lo ridisegna quando il mezzo si allontana. La mappa
della pausa si apre sul mezzo (circa 900 m di città), con zoom (rotella, pizzico, + e −),
trascinamento e il pulsante **Centro storico**. L'elenco dei luoghi è diviso per gruppi.

---

## 3. Il canyon (topologia della gravina)

* **Asse**: è il corso reale del Torrente La Gravina, orientato verso nord. Così la sponda destra è sempre quella della città e la sinistra quella di Botromagno.
* Per ogni punto si calcola la posizione relativa `t` tra il torrente (0) e il ciglio (1). Da `t` si ricava il profilo della sponda.

| Sponda | Profilo |
|---|---|
| Città (est) | fondo a −38 m, poi **falesia** fino a −20 m (fino a t = 0,32), poi i **gradoni** dei rioni fino al ciglio a 0 m: Piaggio a nord della Cattedrale, Fondovico a sud |
| Botromagno (ovest) | fondo, poi **parete ripida** a tre salti fino a −8 m, poi un ripiano fino a −3 m, poi l'altopiano che sale verso la collina di Botromagno |

* Il fondo è a −38 m: il ponte (a quota 0 sulla testata est) risulta alto circa 37 m, come quello vero.
* **Discesa dei rioni** (costante `RIONI`). Nei dati le case fitte del Piaggio e del Fondovico stanno
  oltre il ciglio tracciato a mano, cioè sull'altopiano; nella realtà i rioni scendono verso la
  gravina (la Calata Grotte San Michele scende dal Fondovico; da Piazza Pellicciari una scalinata
  attraversa il rione fino a San Michele). Così, lungo il tratto di ciglio di ogni rione, il
  terreno scende dolcemente verso il ciglio: 8 m nel Piaggio (a partire da 80 m dal ciglio),
  12 m nel Fondovico (da 170 m, cioè da Piazza Pellicciari). Sotto il ciglio i gradoni partono da
  quella quota. Cattedrale, Piazza Benedetto XIII e testata del ponte restano fuori; le vie nuove
  in pendenza arrivano al 14%.
* Il canyon e i rioni sono disegnati a mano solo dentro `CONFIG.terrain.proc` (est −360…460,
  nord −380…600); fuori ci sono le quote reali Copernicus, con il letto del torrente inciso nella
  valle (`Ravine.bed`). Tra i due, una sfumatura di 110 m (`Terrain.procWeight`).
* Il terreno viene **spianato sotto le strade** (con raccordi di 9 m), tranne sotto il ponte.
* Le **grotte** sono bocche ad arco sulle pareti lato città. Aggiungono l'effetto "città di pietra scavata".

---

## 4. Edifici e monumenti

| Elemento | Resa |
|---|---|
| Case | Sagoma reale estrusa. Nei rioni Piaggio e Fondovico: 1–2 piani, **a gradoni** (la sagoma è tagliata in strisce di circa 3,5 m parallele al ciglio, ognuna alta quanto serve sopra il suo terreno; i tetti fanno da terrazza e sui salti si aprono porte e finestre). Nel centro storico: 2–3 piani (3,3 m per piano), toni di tufo e calce. Nei quartieri moderni: 3–5 piani e intonaci chiari. |
| Tetti | Terrazze piane con torrini, cisterne e comignoli; i piccoli corpi rettangolari hanno spesso un **tetto a capanna in coppi**. Le falde sono **ritagliate sulla sagoma reale** (divise lungo il colmo e triangolate): nessun tetto sporge sulla strada. |
| Archi | Volume di tufo con volta a tutto sesto sopra la carreggiata, ghiera in pietra chiara e finestrella sulle due fronti. |
| Finestre e porte | Pannelli istanziati lungo ogni facciata, piano per piano: persiane marroni o verdi, portoni al piano terra (fino a 32 000 istanze, una sola draw call). |
| Chiese | Pietra di tufo, tetto a capanna, **campanile a vela** sul colmo; sul lato che guarda la via un **portale** con stipiti, architrave, timpano, gradino e **oculo**. |
| Chiesa del Purgatorio | Portale sul lato corto a sud, su Piazza Notar Domenico (dove i dati segnano la chiesa). Ai lati della porta due **pilastri di tre torri sovrapposte**, sempre più strette e rigonfie al centro (lo stemma dei Frangipane della Tolfa), che **poggiano sugli orsi** degli Orsini; sulla trabeazione il **timpano spezzato** con i **due scheletri distesi**; al centro lo **stemma Orsini** e sotto il **drappo di pietra con l'epigrafe** (fonte FAI). |
| Cattedrale | Sagoma reale orientata est-ovest. La sporgenza a nord della sagoma non sposta più l'asse. Navate laterali sulla sagoma e navata centrale rialzata con le finestre alte. **Facciata ovest tripartita da due lesene**, con **tre portali** (il centrale più grande e incompiuto, i laterali con lunetta e un **oculo** sopra), il **rosone a 24 raggi** con l'Assunta al centro, la cornice di coronamento e la croce. **Fianco sud**: portale dorico con due colonne, architrave e timpano, il rilievo della Madonna col Bambino tra San Pietro e San Paolo, e un **secondo rosone accanto al campanile**. **Campanile** a filo del fianco sud (nei dati non è un edificio a sé): quattro ordini decrescenti separati da cornici, bifore cieche, cella con arcate e balaustra, **cupola a cipolla** del 1698 con la croce di ferro. **Cappellone del Santissimo** a due piani sulla sporgenza nord. Niente abside esterna: la sagoma reale finisce piatta a est, contro un altro edificio. |
| San Michele delle Grotte | Fuori terra non c'è un edificio: la sagoma dei dati diventa lo **sperone di tufo a strati** in cui è scavata la chiesa, con l'ingresso laterale alto e stretto, le bocche delle grotte e il **corridoio panoramico** con il parapetto verso la gravina. |
| Madonna della Stella | Chiesetta **imbiancata** con la facciata a capanna rivolta alla gravina, **campanile a vela in mattoni** sul vertice, **corpo basso con tetto a una falda** e finestra, la **roccia** alle spalle in cui è scavata la chiesa vera. |
| Palazzi | Palazzo Ducale Orsini e Museo Pomarici Santomasi: **cornicione**, fascia marcapiano e **portale in bugnato**. |
| Ponte Acquedotto | Prospetto estruso con **archi su due ordini**: 4 grandi arcate sul canyon più una fila di archetti sotto l'impalcato, circa 25 archi come l'originale. **Lesene** sui piloni, **due cornici** marcapiano, parapetti, larghezza reale 5,5 m. |
| Fontana della Stella | Muro con nicchia ad arco, cornice, vasca con l'acqua, accanto alla testata est del ponte e fuori dalla strada (forma stilizzata). |
| Belvederi | Parapetti in ferro sul ciglio, nei tre belvederi dei dati, solo dove non c'è la strada. |
| Scalinate | Le 7 scalinate reali: gradini di tufo con alzate da 16 cm che seguono il terreno e parapetti bassi. Si guardano soltanto e si fermano prima delle vie. |
| Abitazioni rupestri | 20 grotte chiuse da una fronte in muratura (tufo o calce) con porta e finestrella, sui salti dei gradoni lato città, lontano da vie ed edifici. Le fonti ne contano circa ottanta sui pendii. |
| Lanterne | Lanterne a muro accese, ogni ~16 m nelle vie entro 70 m dai monumenti (circa 100). |
| Regola | Nessun dettaglio sulla carreggiata: la prova `npm run simula` controlla che nessun vertice di portali, campanile, scalinate, lanterne e parapetti stia sopra una via tra 0,3 e 3,2 m d'altezza (`dettaglisullastrada` vuoto). Nei vicoli i dettagli sporgono al massimo 0,3 m. |
| Mura | I tratti reali di mura urbane diventano muri di tufo. |
| Alberi | Pini e lecci nei giardini reali (Villa Comunale), ulivi verso Botromagno, macchia nel canyon. |

Monumenti con scheda (solo fatti verificati): Cattedrale, la Gravina (belvedere), Chiesa del
Purgatorio, Palazzo Ducale Orsini, Museo Pomarici Santomasi, Santa Lucia (Piaggio), Gravina
Sotterranea, Piazza Pellicciari, Sant'Agostino, San Michele delle Grotte (Fondovico), Ponte
Acquedotto, Fontana della Stella, Madonna della Stella, Botromagno, e dalla fase 3 San
Francesco, Santa Sofia, Santa Cecilia, Santa Teresa e Chiesa del Gesù. L'Addolorata e le piazze
hanno solo l'etichetta (per l'Addolorata non ci sono fonti affidabili).

Non verificato, e quindi non modellato: il campanile di San Francesco (le fonti dicono tre
ordini e circa 40 m, ma la sua posizione non si ricava dai dati) e la posizione esatta del
campanile della Cattedrale lungo il fianco sud (è nella metà verso est). Una fonte (Wikivoyage)
parla di una "facciata a due ordini con oculi ovali": non è chiaro a quale chiesa si riferisca,
e le fonti principali descrivono la facciata della Cattedrale come tripartita.

---

## 5. I mezzi

Quattro mezzi a scelta, costruiti solo da primitive (esaedri deformati, cilindri, profili
estrusi) con quote reali. Nessun logo. La parte bassa della carrozzeria è divisa in tre blocchi
con **passaruota a trapezio**, così le ruote si vedono. Le anteriori sterzano, tutte rotolano;
la scocca beccheggia, rolla e vibra (anche da ferma, a motore acceso).

| Mezzo | Quote | Tratti riconoscibili | Ritmo |
|---|---|---|---|
| Fiat Panda 4x4 (1999) | 3,38 × 1,49 × 1,48 m, passo 2,16 m | due volumi squadrati, protezioni in plastica grezza, barre sul tetto, fari rettangolari, cerchi in lamiera | 0,9 |
| Audi RS6 Avant (C8) | 5,00 × 1,95 × 1,46 m, passo 2,93 m | familiare bassa, passaruota bombati, grande calandra nera, fascia luminosa posteriore, scarichi ovali, pinze rosse, grigio opaco | 1,1 |
| Lamborghini Huracán | 4,46 × 1,93 × 1,17 m, passo 2,62 m | cuneo, abitacolo avanzato, fari a Y, prese d'aria laterali, cofano motore a lamelle, quattro scarichi, arancione | 1,2 |
| Trattore John Deere | 4,6 × 2,35 × 3,0 m, ruote posteriori da 1,76 m | cofano lungo verde, cabina a quattro montanti, parafanghi a settore, ruote gialle con tasselli a spina di pesce, marmitta verticale con sbuffi di fumo | 0,62 |

Il ritmo moltiplica le velocità di `CONFIG.drive`. Ogni mezzo è costruito una sola volta e poi
riusato: il cambio è istantaneo.

---

## 6. Movimento, incroci e cartelli

* Il mezzo segue la spline della via: crociera 8,5 m/s, 5,5 m/s vicino agli incroci, 6 m/s sul ponte, 4,5 m/s nelle inversioni, tutto moltiplicato per il ritmo del mezzo.
* **Partenza**: 12 m prima della testata est del Ponte Acquedotto, sulla via che vi arriva (Via Fontana la Stella), accanto alla Fontana della Stella e rivolti verso il ponte. Il primo tratto attraversa il ponte.
* **Pausa**: il mezzo frena a 7 m/s² fino a fermarsi; il menu (riprendi, cambia mezzo, mappa e luoghi) compare solo in pausa. Il viaggio va in pausa da solo se la pagina viene nascosta.
* **Teletrasporto** (solo in pausa): dissolvenza, il mezzo va sulla via più vicina al luogo, 12 m prima, e il viaggio riprende da lì con la scheda del monumento. Per il ponte si torna al punto di partenza.
* A 38 m dall'incrocio si calcolano le uscite (tutte tranne l'inversione) ordinate da sinistra a destra con l'**angolo di svolta reale**. La più dritta è preselezionata.
* **Cartelli marroni**:
  - in grande il nome reale della via;
  - per i vicoli senza nome, "Vicolo per" seguito dalla via in cui sboccano;
  - sotto, il prossimo monumento lungo quella via ("verso Chiesa del Purgatorio"), oppure il rione.
* **Targa in marmo**: via corrente più rione (Centro storico, Rione Piaggio, Rione Fondovico anche sulla discesa verso il ciglio, Madonna della Stella · Botromagno), e "percorso pedonale" dove serve.
* Le quote delle strade sono smussate (media mobile di ±6 m), così i gradoni del terreno non si sentono sotto le ruote.

---

## 7. Camera

* **Vetrina** all'apertura, a due tempi (`CONFIG.camera.showroom`): per 9 s la camera ondeggia piano attorno al tre quarti posteriore del mezzo fermo, dal lato più aperto, e guarda la strada davanti; poi un volo a gru di 3,5 s porta a un **campo lungo dal canyon**, a sud del ponte, con le arcate su due ordini e il mezzo sulla testata; dopo 10 s si torna al primo piano. Scegliendo un mezzo si torna subito al primo piano. Pose diverse per schermi orizzontali e verticali, calcolate rispetto all'asse del ponte.
* **Inseguimento dall'alto** (18 m sopra il mezzo, 12 m dietro; un po' più alto per il trattore): si vede la strada tra i tetti, come in un plastico.
* **Tetti**: se un tetto si mette tra la camera e il mezzo, o la camera finisce a ridosso di un tetto, la camera sale (fino a 22 m in più) e si avvicina in pianta. Usa una griglia dei tetti (celle da 10 m) con la quota di ogni edificio e arco.
* **Pausa**: vista dall'alto che gira piano sopra il mezzo.
* **Pannelli**: l'inquadratura si sposta (view offset) nella parte di schermo libera dal pannello iniziale o dal menu di pausa.
* **Ponte**: la camera entra nel canyon, 80 m a monte lungo il torrente, all'altezza dell'impalcato.
* **Ciglio**: sulle vie che corrono lungo il ciglio (Via giudice Montea, Via Fontana la Stella, il sentiero ovest) fa una ripresa "da drone" di tre quarti dall'alto verso il canyon, con 25 s di pausa tra una e l'altra.

---

## 7b. Schermata iniziale, crediti e ricerca su Google

* **Credito**: uno solo, «Un progetto di Giuseppe Cassano», in fondo alla schermata iniziale,
  accanto al pulsante **Il progetto**; nella mappa non ci sono crediti né marchi.
* **Pannello «Il progetto»**: un `<dialog>` nativo (Esc chiude, il fuoco resta dentro e torna al
  pulsante), foglio di marmo con la testata marrone dei cartelli turistici. Dice cos'è il
  diorama, cosa si vede, come si usa, da dove vengono dati e fonti, crediti e licenze. È testo
  vero nel DOM, quindi lo leggono anche i motori di ricerca, e ha uno script suo: si apre anche
  se il diorama non parte. Su telefono occupa tutto lo schermo.
* **Finestre basse** (portatili a 720–880 px d'altezza): la schermata iniziale si compatta
  (titolo, spaziature) perché credito e attribuzione ODbL restino dentro lo schermo.
* **Metadati** nel `<head>`: titolo e descrizione con «Gravina in Puglia», «centro storico» e
  «3D», autore, canonical, Open Graph e Twitter card con `og-image.jpg`, `theme-color`, icona SVG
  in linea (il Ponte Acquedotto al tramonto), JSON-LD con `WebSite`, `CreativeWork` (basato su
  OpenStreetMap, ODbL, e Overture Maps), `Place` Gravina in Puglia (Wikipedia, Wikidata Q51829) e
  `Person` Giuseppe Cassano.
* **File separati** (eccezione al file unico: il diorama non li usa):
  - `og-image.jpg`, 1200×630, generata dal diorama con `npm run anteprima` (`tools/test/anteprima.mjs`);
  - `sitemap.xml`, da inviare da Google Search Console.
  - Niente `robots.txt`: su GitHub Pages il sito sta in `/gravina-3d/`, mentre i motori di
    ricerca leggono solo `https://giuseppecassano5bit.github.io/robots.txt`, alla radice del
    dominio, che questo repository non controlla. Senza `robots.txt` tutto è già indicizzabile.

---

## 8. Prestazioni

Misure con `tools/test/prestazioni.mjs` (Mac M4, GPU vera, Chromium headless), nelle viste
partenza, centro, Piazza Scacchi, pausa e panoramica sulla città (il caso peggiore).
"Per fotogramma" è il massimo tra le viste, senza il passaggio delle ombre.

| Voce | Fase 3 (solo centro storico) | Fase 3.4, città intera | Tetto |
|---|---|---|---|
| `index.html` | 390 KB (124 KB compressi) | 737 KB (268 KB compressi) | ≤ 900 KB (≤ 280) |
| Costruzione fino a "Parti" | 282 ms | circa 510 ms | ≤ 1,5 s |
| Città completa (in sottofondo) | — | circa 900 ms | — |
| Triangoli nella scena | 267 000 | 543 000 (telefono 483 000) | ≤ 650 000 |
| Triangoli per fotogramma, PC | 267 000 | 334 000 | ≤ 400 000 |
| Triangoli per fotogramma, telefono | 267 000 | 242 000 | ≤ 250 000 |
| Draw call, PC / telefono | 39 / 38 | 69 / 53 | ≤ 90 / ≤ 70 |

| Voce | Valore |
|---|---|
| Aggiornamento per frame | O(1) sulla spline; minimappa copiata da un quadro pre-disegnato; 8 + 16 controlli sulla griglia dei tetti per la camera |
| Ombre | riquadro di 180 m che segue il mezzo, agganciato ai texel (niente sfarfallio); i riquadri lontani non entrano nel passaggio delle ombre |
| Telefoni e tablet | niente MSAA su schermi densi, mappa d'ombra 1024 e ombre non sfumate, risoluzione che segue gli fps (da 0,9 a 2×), profilo leggero (sezione 2b) |

---

## 9. Stato e prossimi passi

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ |
| 2 | Base: rete, auto, incroci, camera, interfaccia | ✅ |
| 2b | **Dati reali**: vie e incroci reali, edifici reali, torrente e cigli reali, ponte ad archi | ✅ |
| 2c | **Vie libere e mezzi**: nessuna casa sulla strada, archi reali, quattro mezzi, partenza dal ponte, pausa con cambio mezzo e teletrasporto, camera che scavalca i tetti, dettagli dei monumenti, versione mobile | ✅ |
| 3 | **Architettura e fedeltà**: Cattedrale e Purgatorio sulle fonti, San Michele e Madonna della Stella scavate nella roccia, rioni a gradoni in discesa con scalinate reali e abitazioni rupestri, altezze affidabili o stimate per zona, schede di altre cinque chiese, vetrina con il campo lungo sulle arcate | ✅ in revisione |
| 3.4 C | **Città intera**: zolla di 2,9 × 3,1 km a riquadri, 80 km di vie, 1 828 edifici della città, quote Copernicus, binari, Castello Svevo, mappe vettoriali con zoom | 🔄 in revisione |
| 4 | Rifinitura: musica procedurale (Web Audio, 40%, muto), transizioni di camera, prove su telefoni reali | ⏳ |

### Da decidere insieme (fase 3, punto 6)

**Percorsi pedonali e scalinate.** Nei dati ci sono 20 tratti di marciapiede o passaggio
pedonale (1,7 km), 7 scalinate (165 m) e 8 sentieri (3,2 km). Aggiungendo marciapiedi e
scalinate alla rete, sempre senza vicoli ciechi, si passa da 157 a 178 tratti e da 8,96 a
9,83 km, con circa 1 km pedonale in più (i sentieri non aggiungono anelli). Tre strade possibili:
1. lasciarli decorativi, come oggi le scalinate;
2. percorrerli col mezzo, come già il ponte (ma una Huracán giù per una scalinata stona);
3. un tratto **a piedi**: sui tratti pedonali il mezzo si ferma all'imbocco e prosegue una
   figurina low-poly, che al tratto carrabile successivo ritrova il mezzo. Più lavoro, ma è
   fedele e mostra i rioni dal loro punto di vista.

**Allargare il diorama.** *Fatto nella fase 3.4 (blocco C): la zolla ora contiene la città
intera.* Prima era 780 × 860 m. Appena fuori restano il Museo Civico (30 m a
est), la Chiesa di San Domenico (90 m a est), la Pineta comunale (a nord) e, più lontano, il
Santuario della Madonna delle Grazie con la facciata a stemma (circa 360 m a nord-est). Con 100 m
in più per lato l'area cresce di oltre il 50%: più edifici e triangoli, da misurare sui telefoni.

**Quote reali.** *Nella fase 3.4 (blocco C) le quote Copernicus disegnano la città e la
campagna; per ciglio, gradoni e rioni del centro storico resta da fare (blocco G).* Il modello di
elevazione Copernicus GLO-30 (30 m, licenza libera con
attribuzione) è raggiungibile dal bucket S3 pubblico. Si potrebbe usare nello script per tarare
ciglio, gradoni e discesa dei rioni, oggi tracciati a mano, e scrivere le quote in `GEO`. A
30 m il canyon è appena accennato: servirebbe come guida, non come terreno diretto.

Il prompt per continuare il lavoro in una nuova chat è in [`PROMPT_NUOVA_CHAT.md`](PROMPT_NUOVA_CHAT.md).
