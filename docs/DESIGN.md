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
| Vie percorribili | 1 433 tratti, 890 incroci, circa 86 km (nel centro storico 157 tratti, 9 km) |
| Vie decorative (cieche, non percorribili) | 240 tratti |
| Larghezza delle vie | da 3,4 m (vicoli) a 8 m; 37 tratti ristretti al minimo |
| Inversioni a goccia | 5 (la quinta in fondo alla strada del Bosco) |
| Edifici reali | 518 nel centro storico (dopo il ritaglio) e 2 038 in città (con il P.I.P. e il rifugio), nessuno sulla carreggiata |
| Archi sulle vie | 5 |
| Scalinate reali (solo decorative) | 7, 165 m |
| Edifici con altezza reale | 1 (Museo Santomasi, 3 piani); le altre sono stimate per zona |
| Area del diorama | tre zolle (`GEO.meta.zolle`): città 2,88 × 3,12 km (est −840…2040, nord −1140…1980), P.I.P. (est 2040…2760, nord 300…1260), Bosco (est 120…600, nord −1860…−1140); riquadro complessivo `GEO.meta.area` est −840…2760, nord −1860…1980 |
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

**Livelli di dettaglio** (blocco I). Ogni riquadro ha due versioni nella stessa mesh, una dopo
l'altra: le parti solo da vicino (terreno fine, vie con cordoli e marciapiedi, edifici con cortili
e torrini, finestre, torrini e cisterne del centro storico, alberi), quelle comuni (case del
centro storico, binari) e quelle solo da lontano. La versione lontana ha:
- il terreno a maglia doppia (10/30/60 m);
- vie con tratti fino a 24 m e slarghi a 6 spicchi (nel centro storico chianche senza cordoli);
- sagome degli edifici semplificate (scarto 1,2 m) senza cortili né torrini, e il castello senza merli;
- metà degli alberi, senza tronco.

`Tiles.updateLod` sceglie la versione con `setDrawRange`, quindi senza draw call in più. Passa a
quella lontana oltre 560 m dalla camera su PC (420 m sul telefono) e torna alla piena sotto 520 m
(380 m): è l'isteresi, così non ci sono sfarfallii. Da lontano il riquadro non fa ombra.

Come combaciano le due versioni:
- **bordi:** sui lati verso un vicino, i triangoli della versione lontana si dividono nei vertici
  della versione piena, così il bordo combacia qualunque versione mostri il vicino;
- **vie:** vicino alle vie la maglia larga prende la quota più bassa dei dintorni, e le vie
  lontane restano sopra il terreno lontano (ricerca per cella, `farCells`).

**Shader della città** (`cityMaterial`): colori per faccia come il resto del diorama, più un
attributo `aInfo` per vertice che dice il tipo di superficie. Finestre con le persiane per piano
e campata, negozi al piano terra, lamiera dei capannoni, marciapiedi, strisce, traversine e
rotaie costano zero triangoli; da lontano si sfumano nel colore medio. Le campate vengono dai
metri lungo il perimetro (`aInfo.w`), non dalle derivate: di sbieco sarebbero instabili.

**Quote.** Nel centro storico il terreno resta quello disegnato a mano; fuori, le quote
Copernicus smussate. Le vie seguono le pendenze reali e il terreno si spiana sotto vie e binari.

**Vie e terreno (blocco M1).** La maglia larga (15 m in città, 30 in campagna) non poteva seguire
le vie in trincea o in rilevato: un triangolo che scavalcava la via la copriva (il mezzo entrava
nella collina) o la lasciava sospesa. Ora:
- `MeshFit` (sezione 6e), prima di costruire i riquadri, controlla la maglia vera (gli stessi
  vertici di `_terrain`) ogni 3 m al centro, ai bordi e appena fuori da ogni via, e sui dischi
  degli incroci; poi sposta i vertici interni del minimo che serve, con proiezioni successive in
  cui vince «la via non va coperta». Gli scarti entrano in `Terrain.heightAt` interpolati sul
  triangolo, così case, alberi e dettagli restano appoggiati alla maglia;
- dove la maglia di partenza sbaglia di molto (vie in trincea o in rilevato oltre 2 m, vie vicine
  a quote diverse, curve e cambi di pendenza) il riquadro passa da vicino a **7,5 m**
  (`CONFIG.city.refine`); la versione lontana resta quella di prima (`t.cell0` × 2);
- dove nessun triangolo può seguire tutte le vie (incroci in forte pendenza) un **muretto di
  contenimento** scende dal bordo della via fin sotto il terreno (`Tiles._wall`);
- i **dischi degli incroci** hanno l'orlo alla quota delle vie che arrivano (`Tiles.discRim`) e il
  colore dell'asfalto (prima prendevano quello della mezzeria);
- le **vie decorative** non corrono più dentro le carreggiate (la pipeline toglie il tratto
  dentro, `deco_off_roads`, e restringe quelle troppo larghe accanto a una via) e partono dalla
  quota della via su cui si innestano.
Le misure si fanno con `tools/test/difetti.mjs` (vie sotto il terreno, sospese, dischi sfasati,
decorative sovrapposte). Il limite del 18% non cambia.

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

## 2c. Le strade per il Bosco e il P.I.P. (fase 3.4, blocco F)

**Zolle.** Il diorama non è più un rettangolo solo: è fatto di tre zolle (`ZOLLE` in
`tools/genera_dati.py`, `GEO.meta.zolle` nel diorama). La città, il P.I.P. a est e l'appendice
del Bosco a sud. Quote e uso del suolo coprono il riquadro che le contiene tutte
(`GEO.meta.area`); i buchi fuori dalle zolle si riempiono (`fill_masked`) ma non si disegnano.
`Tiles` tiene una griglia che vale `null` fuori dalle zolle, `World.inZolle(e, n, pad)` dice se
un punto è dentro, e il plinto è un blocco per zolla. La minimappa è trasparente fuori.

**P.I.P. - Zona Artigianale.** Vie reali a scala reale, con i capannoni. Solo l'etichetta.

**Tracciato reale compresso (regola in `CLAUDE.md`).** La strada del Bosco parte dal vero
tracciato Overture (`BOSCO_ROUTE`, 5 397 m), lo riduce in scala 0,125 (circa 760 m), lo
semplifica e lo ammorbidisce (`chaikin`). Si attacca alla città nel nodo reale (356, −1060), ha i
nodi `bosco:svolta` e `bosco:rifugio` e finisce con una goccia. Gli angoli restano quelli reali.
Il torrente si taglia prima dell'appendice.

**Bosco di querce.** Copertura `querce` (12): un cerchio di 95 m con una radura di 24 m attorno
al rifugio (8 × 6 m, alto 3,6 m). Nel diorama `COVER.QUERCE` colora il terreno e posa querce
procedurali (tronco e chioma tonda, densità 0,6) lontane dalla carreggiata. La scheda del Bosco
si apre entro 60 m dal centro; il rifugio ha solo l'etichetta (nessuna fonte).

### Il Bosco da vicino (fase 3.4, blocco L)

**Strada fino al vivaio.** `bosco_chain()` costruisce il tracciato a pezzi: fino a `QUERCUS_A`
compresso (0,125), poi a scala reale attraverso l'area Quercus fino all'incrocio `BOSCO_J`, poi
di nuovo compresso lungo la strada reale OSM (`VIVAIO_ROUTE`, 3 212 m) fino a `VIVAIO_REAL`, e a
scala reale fino all'incrocio con Contrada Annunziata, dove c'è la goccia. Ogni zona a scala
reale ha un'ancora (`ZONA_Q`, `ZONA_V`): un punto reale dentro la zona va nel diorama con
`bosco_map` (ancora + scarto reale); fuori dalle zone, a lato del vertice più vicino della strada
compressa. Tratti di strada: 950 m fino all'area Quercus, 674 m fino al vivaio (8,5 km reali).
Zolle: il Bosco si allarga a ovest (−120, 600, −1860, −1140) e si aggiunge `VIVAIO`
(−600, 360, −2340, −1860); 11 riquadri in più. Le quote lì sotto sono di un altro posto (la valle
a sud della città): si smussano molto e si dimezza il rilievo.

**Area Quercus** (ex area ristoro «Marcuccio», in OSM «Rifugio Bosco Difesa Grande»): ristorante
col tetto rosso (w411141350), i tre campi OSM (tennis al centro, calcetto ai lati, con le righe, le
porte o la rete e la recinzione a giorno), la tribunetta, i tavoli nella radura, il parcheggio
«Terra Rossa» sterrato a lato della strada. Maneggio e giochi tolti nel blocco M1: il committente
ha detto che non ci sono, e dove stava il maneggio torna il bosco.
**Vivaio forestale**: edifici OSM (il lungo col tetto in coppi), vasche con l'acqua verde, aiuole in
file. **Base Scout** nel grande campo a nord della strada. **Area pic-nic** davanti al vivaio:
spiazzo di ghiaia che segue il terreno, staccionate a due traverse (in basso e in alto), scaletta
col corrimano, la **scritta «SIC DIFESA GRANDE»** (lettere a blocchi 5 × 7, alte 1,7 m, inclinate
sul pendio e rivolte alla strada, con la foglia) e, sul prato, vialetti bordati di travetti,
tavoli, querce giovani coi tutori, pini, cipressi e un lampione.

**Uso del suolo** (`bosco_cover`): ogni cella delle zolle del bosco torna al punto reale
(`bosco_real`) e diventa querce (12) se sta nei poligoni OSM del Bosco Difesa Grande o del Bosco di
Gravina, campo altrimenti; `bruciato` (13) dove il satellite mostra gli alberi morti; `fitto` (14)
entro 42 m dai sentieri; prato (`sport`) nelle radure dell'area Quercus e del pic-nic; `cava` per
il parcheggio. Nei riquadri le querce hanno densità 0,42, le querce morte sono tronchi grigi.

**A piedi nel bosco.** I sentieri OSM attorno all'area Quercus (`QUERCUS_SENTIERI`) con la via di
servizio w647001048: 524 m a scala reale, flag 32 e 8 («Sentiero nel bosco»). Il mezzo aspetta alla
via di servizio, come nel centro storico.

**Bosco fitto** (sezione 6f, `Forest`): nelle celle `fitto`, su una griglia sfalsata di 3,1 m
(4,3 sul telefono), querce di tre età con chioma a quattro volumi, querce morte vicino alle zone
bruciate, arbusti, tronchi caduti, sassi e foglie a terra di cinque colori. Sei `InstancedMesh`
(una draw call ciascuna, solo in vista), ombre delle querce solo su PC (le macchie di luce).
Gli alberi tra la camera e la figura si abbassano in 0,3 s e tornano quando la vista è libera.
Nel bosco la nebbia si avvicina (foschia) e la targa dice «Bosco Difesa Grande».

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
  terreno scende dolcemente verso il ciglio. Sotto il ciglio i gradoni partono da quella quota, e
  dove il rione scende molto la falesia si abbassa. Cattedrale, Piazza Benedetto XIII e testata del
  ponte restano fuori.
* **Quote reali come guida** (blocco G, `GEO.rioni`). Quanto scende il rione, e da quale distanza
  dal ciglio, lo misura la pipeline sulle quote Copernicus ogni 15 m lungo il ciglio est
  (`rioni_profile`): l'altopiano a 220–300 m dal ciglio contro la quota a 45 m dal ciglio, più
  metà della pendenza che resta. I 45 m vicino al ciglio non si usano: a 30 m di maglia, e dopo lo
  smusso, il canyon "sbava" dentro le case e la discesa verrebbe esagerata (30–40 m). Per lo
  stesso motivo se ne usa il 45% (`RIONI_SCALA`): Piaggio fino a 17 m (prima 8 m), Fondovico circa
  12 m come prima, con la forma presa dai dati (più profondo a sud e a metà Piaggio). Nel diorama
  `rioneDrop` allunga larghezza e dissolvenza quando il rione scende di più (11 e 7,5 volte la
  profondità), così le vie restano entro le pendenze di prima: massimo 19% vicino alla testata del
  ponte. Restano disegnati a mano: linee dei cigli, fondo, falesia, gradoni e sponda di Botromagno.
* **Salite e discese vere** (blocco N1, `GEO.centro`, `Guida` nella sezione 4). L'altopiano lato città
  segue le quote Copernicus: la pipeline prende il DSM grezzo su una griglia a 10 m attorno al terreno
  disegnato a mano, il percentile 20% su 90 m dei soli pixel a più di 120 m dal ciglio est (vicino al
  ciglio la cella da 30 m prende dentro il canyon: con i pixel a più di 25 m la Cattedrale veniva −13,8 m,
  con 120 m −0,3), la sfocatura dei soli valori noti (35 m, noti oltre 150 m dal ciglio), il prolungamento
  **piatto lungo la normale** fino al ciglio, lo smusso finale (20 m); in GEO una griglia a 20 m con le quote a
  0,1 m (circa 3 KB compressi) e la guida sul ciglio ogni 10 m di nord. Vicino al ciglio una discesa morbida
  porta alla quota del ciglio di prima, rioni compresi, o alla guida se è più bassa (a sud del Fondovito: lì
  il ciglio scende fino a −15 m, e i gradoni scendono con lui). Senza esagerazione (×1, scelta del
  committente; ×1,5 di riserva in `CONFIG.terrain.relief`). Quote nei punti noti: Cattedrale −0,4,
  Purgatorio +0,5, Piazza della Repubblica +4,3, Porta San Michele +4,9, San Francesco +10, Pellicciari −0,1.
  Vie del mezzo nel centro storico (14,1 km) per pendenza, prima → dopo: entro il 2% dall'84% al 36%,
  2–4% dal 6 al 31%, 4–6% dal 3,5 al 17%, 6–9% dal 2,8 al 7%, 9–13% dall'1,5 al 4,6%, 13–18% dall'1,9 al 4,2%,
  oltre il 18% niente. Per restarci c'è un **limitatore sulle quote degli incroci** (`#limitNodes`): sul grafo
  delle vie del mezzo, se la salita media tra due incroci supera l'85% del 18%, le due quote si avvicinano
  (le testate del ponte restano ferme); poi il terreno si adatta alle vie.
* **Il pendio vero del Fondovico** (blocco N2, `PENDIO` e `pendioFondovico` nella sezione 4). Fino al blocco N1 dove sta
  San Michele delle Grotte c'era un pianoro a −6 m, più alto del cancello (−12): a sud di nord −110 la discesa del rione
  sfumava e restava la guida. Ora, da nord −212 a −118 e fino a 72 m dal ciglio, il prato scende dalla Calata San Giovanni
  Battista (−9 m) alla terrazza, che sta 2 m sotto il cancello (la scalinata della foto a 360°) e scende dolce da −14 a
  −16,5 m; accanto il prato verde a cuneo, poi la parete di roccia che risale di 6 m in 12 m e la macchia; oltre il parapetto
  la scarpata verso il canalone dei cipressi; sotto il ponticello la testa del canalone, 5,5 m più giù. Non alza mai il
  terreno; il ciglio si abbassa col prato e i gradoni scendono con lui. Le quote Copernicus (terrazza −18, chiesa −21)
  confermano la discesa ma vicino al ciglio «sbavano» nel canyon. Lungo la terrazza il raccordo del terreno coi sentieri è
  corto (2,5 m invece di 9), e sotto il ponticello il terreno non si appiana. Vie del mezzo, Piazzetta e Via San Vito
  Vecchio restano fuori; abitazioni rupestri invariate (21).
* Il canyon e i rioni sono disegnati a mano solo dentro `CONFIG.terrain.proc` (est −360…460,
  nord −380…600); fuori ci sono le quote reali Copernicus, con il letto del torrente inciso nella
  valle (`Ravine.bed`). Tra i due, una sfumatura di 110 m (`Terrain.procWeight`), di 220 m a sud
  (`bandSouth`, blocco D), dove le quote reali stanno 15–30 m sotto l'altopiano del centro.
* **Gradino a sud della città, corretto nel blocco D.** Il ciglio est prolungato dalla pipeline
  cominciava con lo stesso punto ripetuto tre volte: il tratto lungo zero, senza verso, faceva
  credere al terreno che tutta la fascia a sud-est di quel punto stesse dentro il canyon. Lungo
  il confine della fascia (circa nord −390…−430, da Via Goito a Via Tripoli) c'era un salto di
  15–18 m che le vie salivano quasi in verticale (fino al 1 600% su 5 m). `Polyline2D` ora scarta i
  punti ripetuti, e `extend_rims` non li scrive più.
* **Pendenze** (blocco D). Le vie del mezzo nel centro storico (zona Z0) non superano il 18%
  (`CONFIG.road.maxGrade`): le quote di ogni tratto passano da un limitatore con gli incroci fermi,
  solo dove la salita media tra i due incroci lo permette. Via Fontana la Stella scende dal 21% al
  18%. Restano ripidi i tratti a piedi (sentiero verso Botromagno, scalinata di Via giudice Montea)
  e, fuori dal centro storico, alcune vie dei quartieri a nord sulle quote reali (Via Savoia,
  Via Giardini, Corso Aldo Moro: 29–37%).
* Il terreno viene **spianato sotto le strade** (con raccordi di 9 m), tranne sotto il ponte.
* Le **grotte** sono bocche ad arco sulle pareti lato città. Aggiungono l'effetto "città di pietra scavata".
  Di fronte al Fondovito, sulla parete di Botromagno, le **Sette Camere** (OSM n6365472958): fino a
  36 bocche fitte entro 40 m, come nella foto del complesso (blocco D).

---

## 4. Edifici e monumenti

| Elemento | Resa |
|---|---|
| Case del centro storico (blocco N1) | Prisma sulla sagoma senza la faccia di sotto; nei muri la quota del suolo per vertice (`SURF.OLD`): lo shader disegna lo **zoccolo** in conci squadrati che segue la strada, con la cimasa, il **marcapiano** ai piani (contati dal tetto), il **cornicione** con l'ombra e qualche **pluviale** all'angolo, a costo zero in triangoli. Le case con più di 2,5 m di dislivello scendono **a gradoni** nel verso della pendenza, come nei rioni. Le file delle finestre sono orizzontali; la porta sta alla quota della strada davanti alla sua colonna, coi **gradini** (alzate uguali, pedate da 30 cm) se la soglia è più alta e c'è posto fuori dalla carreggiata, altrimenti è una finestra; sotto un piano terra molto rialzato, una porta a filo strada. |
| Finestre, portoni e balconi (blocco N1) | Il pannello di ogni finestra si allarga per la **cornice di pietra** e il **davanzale**; lo shader (`SURF.WIN`) ci disegna le persiane a stecche a due ante (o i vetri scuri col telaio), i **portoni** in legno a riquadri con la battuta e, su un portone su tre circa, la **lunetta** ad arco (fuori dall'arco il pannello sparisce). Circa una finestra alta su otto è una porta-finestra col **balcone**: lastra di pietra su due mensole e **ringhiera** di ferro con le sbarre, il corrimano e una fascia di riccioli disegnati dallo shader con l'alpha test; ogni tanto un balcone lungo su due finestre, con più vasi. **Vasi** di terracotta coi fiori anche accanto a qualche porta. Tre InstancedMesh (lastre, ringhiere, vasi), solo entro 180 m dalla camera (`CONFIG.buildings.near`, celle da 60 m) e sul telefono la metà; mai sotto i 3,4 m sopra la carreggiata. |
| Piani veri e ruderi (blocco N2b) | Fino a N1 i piani li sceglieva il diorama per zona (`Buildings.height`: rioni 1–2, centro 2–3, oltre 3–5, a caso). Ora la pipeline ha la tabella **`LIVELLI`** (`tools/genera_dati.py`): per ogni casa rilevata un punto nella sagoma, l'id OSM se c'è, i piani e la fonte, **contati su Street View** (via e data della foto): 81 case nelle vie attorno a Via Calderoni, Via San Giovanni Evangelista, Via Santa Sofia, Piazza Benedetto XIII, Via Matteotti, Via Ingannamorte, Via Corrado, Via Vittorio Veneto e Via Fontana la Stella. Dove la cima della facciata esce dall'inquadratura il numero è «almeno N»: l'altezza va in GEO come 100 m + il minimo e `Buildings.height` prende il più alto tra il minimo e la regola. Dove non c'è una riga (e in tutto il Fondovico, dove Street View ha solo foto a 360° di notte o interne) resta la regola. Il DSM Copernicus a 30 m non distingue 2 da 3 piani (il «suolo» del DSM è fatto dai tetti stessi: scarto mediano 1,9 m nel centro), serve solo come conferma. I **28 `building=ruins` OSM** del centro storico (17 nel Piaggio, 7 nel Fondovico, 4 altrove) sono `KIND['rudere']` (7): sul contorno reale muri di tufo e calce a pezzi di 1–2 m (`Buildings.ruin`), alti da pochi decimetri a 4,5 m, con le brecce dove sono crollati, senza tetto né finestre, fondo di terra; nel cono di vista di 12° dalla ringhiera della Cattedrale (OSM n3348673132) verso il ponte i ruderi restano a 0,6 m. Nello strato «edifici» dei riquadri, quindi anche da lontano. |
| Case | Sagoma reale estrusa. Nei rioni Piaggio e Fondovico: 1–2 piani, **a gradoni** (la sagoma è tagliata in strisce di circa 3,5 m parallele al ciglio, ognuna alta quanto serve sopra il suo terreno; i tetti fanno da terrazza e sui salti si aprono porte e finestre). Nel centro storico: 2–3 piani (3,3 m per piano), toni di tufo e calce. Nei quartieri moderni: 3–5 piani e intonaci chiari. |
| Tetti | Terrazze piane con torrini, cisterne e comignoli; i piccoli corpi rettangolari hanno spesso un **tetto a capanna in coppi**. Le falde sono **ritagliate sulla sagoma reale** (divise lungo il colmo e triangolate): nessun tetto sporge sulla strada. |
| Archi | Volume di tufo con volta a tutto sesto sopra la carreggiata, ghiera in pietra chiara e finestrella sulle due fronti. |
| Finestre e porte | Pannelli istanziati lungo ogni facciata, piano per piano: persiane marroni o verdi, portoni al piano terra (fino a 32 000 istanze, una sola draw call). |
| Chiese | Pietra di tufo, tetto a capanna, **campanile a vela** sul colmo; sul lato che guarda la via un **portale** con stipiti, architrave, timpano, gradino e **oculo**. Blocco D, dalle foto: Santa Cecilia con la **lunetta** con la grata sopra la porta, Sant'Agostino con i **vasi di pietra** agli angoli della facciata, la Chiesa del Gesù (nei dati è una casa) con la **facciata bianca**, il timpano e **tre oculi**. |
| San Francesco | Facciata sul Larghetto con **rosone**, cornice marcapiano e due porte laterali con un **oculo** sopra. **Campanile** (1766, circa 40 m) all'angolo nord della facciata, tra la chiesa e il convento, un poco avanti: base con le lesene d'angolo, due ordini con finestra ad arco e balaustra, cella con quattro arcate, cupolina con lanterna e croce (Street View, blocco D). |
| Porta San Michele e Piazza Scacchi | All'imbocco di Via Matteotti le **facciate dipinte** dei due palazzi d'angolo (rosa con due balconi lunghi e giallo), con persiane verdi e botteghe; nell'angolo del palazzo rosa, al primo piano, la **nicchia** con **San Michele** (ali, spada, drago). A sud, sotto un **ulivo** in un'aiuola rotonda, il **busto in bronzo di Canio Musacchio** sul blocco con la lapide e il muretto curvo; a nord il **busto in pietra di Arcangelo Scacchi** su un alto piedistallo, con le catene (basamento da OSM). Lungo Via Garibaldi un'**aiuola rialzata** con gli alberi e le **sedute di pietra**; fioriere tonde e i due pannelli con la pianta della città. Tutto nello strato dei dettagli dei riquadri: si vede solo da vicino. |
| Quattro Fontane | Blocco di pietra dalla sagoma OSM (circa 2,6 × 2,3 m) con una lapide per lato sotto il coronamento curvo, pinnacoli agli angoli, sui lati lunghi i **due serpenti marini** e la vasca. Nel diorama l'incrocio passa più vicino che nella realtà: la fontana si sposta di quel poco che serve per stare fuori dalla carreggiata. |
| Chiesa del Purgatorio | Portale sul lato corto a sud, su Piazza Notar Domenico (dove i dati segnano la chiesa). Ai lati della porta due **pilastri di tre torri sovrapposte**, sempre più strette e rigonfie al centro (lo stemma dei Frangipane della Tolfa), che **poggiano sugli orsi** degli Orsini; sulla trabeazione il **timpano spezzato** con i **due scheletri distesi**; al centro lo **stemma Orsini** e sotto il **drappo di pietra con l'epigrafe** (fonte FAI). |
| Cattedrale | Sagoma reale orientata est-ovest (blocco D: campanile in fondo a est del fianco sud, contro la Curia, e secondo rosone subito a ovest, come su Street View). La sporgenza a nord della sagoma non sposta più l'asse. Navate laterali sulla sagoma e navata centrale rialzata con le finestre alte. **Facciata ovest tripartita da due lesene**, con **tre portali** (il centrale più grande e incompiuto, i laterali con lunetta e un **oculo** sopra), il **rosone a 24 raggi** con l'Assunta al centro, la cornice di coronamento e la croce. **Fianco sud**: portale dorico con due colonne, architrave e timpano, il rilievo della Madonna col Bambino tra San Pietro e San Paolo, e un **secondo rosone accanto al campanile**. **Campanile** a filo del fianco sud (nei dati non è un edificio a sé): quattro ordini decrescenti separati da cornici, bifore cieche, cella con arcate e balaustra, **cupola a cipolla** del 1698 con la croce di ferro. **Cappellone del Santissimo** a due piani sulla sporgenza nord. Niente abside esterna: la sagoma reale finisce piatta a est, contro un altro edificio. |
| San Michele delle Grotte (blocco N2) | Nel posto vero, in fondo alla terrazza (fino al blocco N1 era uno sperone sulla sagoma OSM w411139697, ora una chiesetta di un piano). Oltre il **cancello** coi pilastri e il cartello marrone, la **terrazza lastricata** (circa 4,4 m) scende dolce lungo la rupe: verso la gravina il **parapetto di conci di tufo** con la copertina chiara, curvo dove gira, coi **faretti** incassati; verso il prato un cordolo basso; sotto il parapetto **cipressi** e lecci. Accanto, il **prato verde** a cuneo e la **parete di roccia**. In fondo, nella **rupe a strati** (massi e cespugli in cima), il **portico**: grotta allargata coi due **pilastri monolitici** chiari, la cancellata di ferro, dentro la **scala di tufo** che sale verso il passaggio stretto e, dietro la grata, l'**ossario** coi teschi. Dalla fine della terrazza il **ponticello** ad arco (non in OSM: satellite e foto da drone) scavalca la testa del canalone, dove scende il **filo d'acqua** animato fino al torrente (`Cascata`); oltre, sul promontorio, la goccia della figurina e le mura (w1512581512). Tutto nello strato dei dettagli; la scheda sta sul portico. |
| Santa Lucia (blocco N2b) | Il footway OSM **w1195336380** («Calata S. Lucia» su Google, 60 m, 14% di pendenza media) scende da Via Michelangelo Calderoni (nodo OSM [48,6; 85,8]) alla chiesa **w411139356** («Ipogeo Santa Lucia» su Google): tratto a piedi cieco che finisce con la **goccia della figurina** nello slargo davanti alla chiesa (`GOCCE_PIEDI`, eccezione scritta in `CLAUDE.md`); la scheda «Santa Lucia» si apre lungo il passaggio. Via Calderoni resta una sola via fino al nodo, poi si divide. L'anello con «Via Santa Lucia» (w1512581502) non c'è: 9 m senza collegamento in OSM e nessuna foto. |
| Madonna della Stella | Chiesetta **imbiancata** con la facciata a capanna rivolta alla gravina, **campanile a vela in mattoni** sul vertice, **corpo basso con tetto a una falda** e finestra, la **roccia** alle spalle in cui è scavata la chiesa vera. |
| Palazzi | Palazzo Ducale Orsini e Museo Pomarici Santomasi: **cornicione**, fascia marcapiano e **portale in bugnato**. |
| Ponte Acquedotto | Prospetto estruso con **archi su due ordini**: 4 grandi arcate sul canyon più una fila di archetti sotto l'impalcato, circa 25 archi come l'originale. **Lesene** sui piloni, **due cornici** marcapiano, parapetti, larghezza reale 5,5 m. |
| Fontana della Stella | Muro con nicchia ad arco, cornice, vasca con l'acqua, accanto alla testata est del ponte e fuori dalla strada (forma stilizzata). |
| Belvederi | Parapetti in ferro sul ciglio, nei tre belvederi dei dati, solo dove non c'è la strada. |
| Scalinate | Le 7 scalinate reali: gradini di tufo con alzate da 16 cm che seguono il terreno e parapetti bassi, e si fermano prima delle vie. Due si percorrono a piedi (blocco G): quella di Via giudice Montea (32 gradini) e quella tra Via Lettieri e Via Fontana la Stella. Le altre cinque nei dati finiscono nel vuoto e si guardano soltanto. |
| Abitazioni rupestri | 20 grotte chiuse da una fronte in muratura (tufo o calce) con porta e finestrella, sui salti dei gradoni lato città, lontano da vie ed edifici. Le fonti ne contano circa ottanta sui pendii, ma né i dati né le fonti le collocano una per una: nel blocco D si aggiungono solo le grotte delle Sette Camere, dove la posizione c'è. |
| Lanterne | Lanterne a muro accese, ogni ~16 m nelle vie entro 70 m dai monumenti (circa 100). |
| Scuole (blocco E) | 16 scuole sull'edificio reale (OSM o Overture): muri ocra o mattone con le finestre dello shader, tetto grigio chiaro; all'ingresso pensilina e due pennoni con le bandiere (Italia, Europa), un campo da gioco in resina coi canestri sul lato più libero e la recinzione verde attorno, col cancello. Solo da vicino. |
| Chiese della città (blocco E) | Pietra col tetto a capanna, portale con timpano e oculo sul lato della via e croce in cima; senza foto verificate niente campanili. |
| Casino di Meninni e case rosa (blocco E) | Il Casino in pietra col tetto in coppi, i pini d'Aleppo nel giardino verso la città e i cipressi dietro (FAI); le case rosa tra Via Guardialto e Via Guardialto Piccolo in intonaco rosa. |
| Strade del centro storico (blocco N1) | Secondo la superficie OSM (`edge.surface`, bit 128–512 dei flag): **lastre** squadrate (chianche) a file di traverso sfalsate coi giunti per `sett` e `paving_stones`, **asfalto**, **ciottoli** per `unhewn_cobblestone`, terra battuta; Piazza Benedetto XIII (strada e area pedonale OSM) a **lastre chiare in diagonale con le file più scure a rombi**, come sul satellite. Tutto dallo shader, anche nella versione lontana dei riquadri; qualche **tombino** a metà via, niente canaletta centrale. |
| Muretti e ringhiere (blocco N1) | Dove una via del mezzo corre più di 1 m sotto il terreno accanto, un muro di contenimento in conci (fino a 2,2 m); dove corre più di 1 m sopra, un muretto basso con la ringhiera di ferro. Fuori dalle case, dal canyon e dagli incroci: circa 250 m. |
| Arredo del centro storico (blocco N1) | Le **6 fontanine dell'Acquedotto Pugliese** nei punti OSM (colonnina di ghisa con cupoletta e pomello, fascia della scritta, rubinetto d'ottone, pulsante, coppa tonda, vasca quadra di pietra con la griglia); al belvedere «la porticina» del Piaggio tre **panchine di marmo** e un **paletto** di pietra, la ringhiera sui pilastri; davanti alla Cattedrale, sul lato sud di Piazza Benedetto XIII, l'**aiuola con cinque alberelli** potati e il bordo di siepe, col lampione; la **statua di Benedetto XIII** benedicente sul piedistallo, coi gradini e il recinto di catene; in **Piazza della Repubblica** l'aiuola rialzata con due ulivi, i cubi di pietra, le fioriere tonde e il lampione a due bracci, e lungo Via Libertà le fioriere grigie; tre alberi in fondo a Via Fontana la Stella; in Via Vittorio Veneto i **lampioni a palo** neri e i **paletti** di pietra agli incroci. Dove nel diorama la via passa più vicina che nella realtà, l'oggetto si sposta di quel poco che serve. |
| Regola | Nessun dettaglio sulla carreggiata: la prova `npm run simula` controlla che nessun vertice di portali, campanile, scalinate, lanterne e parapetti stia sopra una via tra 0,3 e 3,2 m d'altezza (`dettaglisullastrada` vuoto). Nei vicoli i dettagli sporgono al massimo 0,3 m. |
| Mura | I tratti reali di mura urbane diventano muri di tufo che seguono il terreno, a pezzi di 2 m con la copertina: nei dati c'è solo quello del promontorio di San Michele (w1512581512), basso (1,8 m) come sul satellite. |
| Rione Fondovico (blocco N2) | **Piazzetta Fondovico**: quattro strisce nel prato OSM coi muretti bianchi e i vialetti di mattoni tra l'una e l'altra; **macchia del Fondovico** (OSM w385177569, colore di macchia e, alla quota della terrazza, prato verde) con i muretti a secco degli orti lungo le curve di livello, a pezzi coi varchi, cespugli e qualche albero. **Hortus** in Via Leopardi (decorativa): l'arco col cancello decorato, il pilastro col cartello e il cancello piccolo, i vecchi muri di conci, il giardino a terrazze con le aiuole e gli alberi; solo l'etichetta. |
| Alberi | Pini e lecci nei giardini reali (Villa Comunale), ulivi verso Botromagno, macchia nel canyon. |
| Botromagno (blocco M1) | Le sagome OSM `building=ruins` dal lato di Botromagno (46) sono **rovine**: muri a secco di blocchi irregolari di calcare e tufo sul contorno reale, alti 0,3–1,2 m con brecce e tratti crollati, fondo di terra, conci caduti, erba secca e cespugli. Nell'area degli scavi (OSM w484764621) il **recinto funerario con sei tombe in serie**, tombe a fossa (alcune con la lastra spostata), a semicamera e a camera col dromos (gradini scavati verso l'apertura nel banco), **buche per i pali** delle capanne in anelli; suolo di **roccia** (calcare con crepe, massi ed erba secca) lungo il ciglio ovest e negli scavi. Gli edifici veri del versante (il Madonna della Stella Resort e i suoi corpi) a un piano, muri chiari e coppi. Le rovine sul lato della città restano case. |
| Stadio «Stefano Vicino» (blocco M1) | Su un terrapieno piano alla quota del campo (le quote a 30 m lo davano in pendenza di 15 m: lo stadio sta sul ciglio della gravina). Campo in erba sintetica con strisce, righe e porte; **gradinata est** sulla sagoma OSM della tribuna, **tribuna ovest coperta** (la copertura è dei lavori 2024–2025), curva sud e settore nord in cemento con le file di seggiolini, quattro **torri faro**, **muro di cinta** sul contorno OSM con gli ingressi verso le vie (verso la gravina fa da muro di sostegno). |
| Pineta e Parco Robinson (blocco M2) | Pini d'Aleppo a ombrello (tronco alto, chioma larga e piatta) sul prato; cancellata sui lati verso le vie con i cancelli dove entrano i vialetti reali; area giochi sul punto OSM (altalene, scivolo, giostra girevole, dondoli a molla, altalena a bilico) col fondo antitrauma e lo steccato; il busto al centro dei vialetti, panchine e lampioni, la fontanella, i tavoli del pic-nic e i parapetti ai belvederi (OSM w473031981). |
| Villa Comunale e Monumento ai Caduti (blocco M2) | Il monumento rifatto dalle foto e dalle fonti: tre gradini, il dado di marmo bianco con le lapidi dei nomi e il gruppo in bronzo di Angelo Galli (1934), l'Italia a cavallo col vessillo, due soldati alla carica e il prigioniero con le catene spezzate; scheda con la **sosta in panchina** (sezione 6b). Le panchine OSM (di marmo attorno al monumento, di legno coi braccioli di ferro lungo i viali) e i due «Fontanoni gemelli». Villa e Piazza della Repubblica sono pedonali. |
| Monumento alla Cola Cola (blocco M2) | All'ingresso della città su Via Bari, nel punto OSM (w411137509): una grande cola cola, il fischietto di terracotta di Gravina, su un basamento di pietra; corpo bianco calce con le strisce rosse, gialle, verdi e blu, base a campana, becco, cresta e coda alzata; con la scheda; Via Bari ci arriva come via cieca reale con la goccia. |
| Fiera di San Giorgio (blocco M1) | Recinzione di muretto basso in cemento con la rete metallica, cancello tra due pilastri sul punto OSM e **botteghino** giallo accanto (Street View, aprile 2025); i quattro padiglioni OSM sono capannoni chiari con i **portoni** grandi bordati di giallo. |

Monumenti con scheda (solo fatti verificati): Cattedrale, la Gravina (belvedere), Chiesa del
Purgatorio, Palazzo Ducale Orsini, Museo Pomarici Santomasi, Santa Lucia (Piaggio), Gravina
Sotterranea, Piazza Pellicciari, Sant'Agostino, San Michele delle Grotte (Fondovico), Ponte
Acquedotto, Fontana della Stella, Madonna della Stella, Botromagno, e dalla fase 3 San
Francesco, Santa Sofia, Santa Cecilia, Santa Teresa e Chiesa del Gesù, e dal blocco D Porta San
Michele, Piazza Scacchi, Quattro Fontane, San Nicola, Bastione medievale e Sette Camere, e dal blocco
M1 la Necropoli del Padre Eterno (con le etichette «Scavi archeologici di Botromagno» e «Padre
Eterno», senza scheda: è con ogni probabilità la chiesa-grotta, ma non è verificato). L'Addolorata
e le altre piazze (con la Piazzetta Fondovico) hanno solo l'etichetta: Addolorata e Annunziata sono
sulla stessa sagoma, ma nessuna fonte dice che siano la stessa chiesa.

Il campanile di San Francesco e la posizione del campanile della Cattedrale sono stati verificati
su Street View nel blocco D. Una fonte (Wikivoyage)
parla di una "facciata a due ordini con oculi ovali": non è chiaro a quale chiesa si riferisca,
e le fonti principali descrivono la facciata della Cattedrale come tripartita.

---

## 5. I mezzi

Cinque mezzi a scelta (blocco M3): quattro auto **realistiche nello stile** e la mongolfiera.
Nessun logo, nessun modello caricato: tutto è costruito dal codice (sezione 7, `VehicleFactory`).

| Mezzo | Quote | Tratti riconoscibili | Ritmo | Triangoli |
|---|---|---|---|---|
| Fiat Panda 4x4 (1999) | 3,38 × 1,49 × 1,48 m, passo 2,16 m | due volumi squadrati, protezioni in plastica grezza, barre sul tetto, fari rettangolari, cerchi in lamiera con le asole | 0,9 | 3 900 |
| Audi RS6 Avant (C8) | 5,00 × 1,95 × 1,46 m, passo 2,93 m | familiare bassa, parafanghi allargati, grande calandra nera, fascia luminosa posteriore, scarichi ovali, cerchi a dieci razze con pinze rosse, grigio | 1,1 | 4 400 |
| Lamborghini Huracán | 4,46 × 1,93 × 1,17 m, passo 2,62 m | cuneo, abitacolo avanzato, fari a Y, prese d'aria laterali, cofano motore a lamelle, quattro scarichi, cerchi a Y con pinze gialle, arancione | 1,2 | 4 400 |
| Trattore John Deere | 4,6 × 2,35 × 3,0 m, ruote posteriori da 1,76 m | cofano lungo verde, cabina a quattro montanti, parafanghi a settore, ruote gialle con tasselli a spina di pesce, marmitta con gli sbuffi di fumo | 0,62 | 5 500 |
| Mongolfiera | alta circa 23 m con la cesta | pallone a 14 spicchi nei colori del diorama (terracotta, ocra, crema) con una fascia blu, cesta di vimini, funi, bruciatore con la fiamma, pilota e visitatore | — | 2 400 |

**Carrozzeria per sezioni** (`Shop.loft`): una serie di anelli di 15 punti lungo il mezzo, dal
paraurti al baule, con le **arcate dei passaruota** ritagliate e, per RS6 e Huracán, i parafanghi
allargati. **Vetri a filo** trasparenti: si vedono l'abitacolo con sedili, cruscotto e volante e il
**guidatore seduto** (`Walker.figure()`, la figurina del blocco G in posa seduta, coi colori per
nome); parcheggiato, senza guidatore. **Ruote** con la spalla della gomma e il cerchio di ogni
modello; rotolano e sterzano nello shader (`uSpin`, `uSteer`). Sospensioni: la scocca beccheggia,
rolla e vibra un po' di più sul basolato del centro storico e sugli sterrati.

**Quattro mesh per mezzo** (prima più di 20): carrozzeria, ruote, vetri e aloni dei fari (il
trattore ha in più il fumo, una `InstancedMesh`). Colore, metallo, ruvidità e «gruppo di luce» sono
attributi dei vertici (`aMat`), non materiali diversi: le draw call della scena calano di 15 su PC e
sul telefono (`prestazioni.mjs`, blocco M3).

**Luci da uniform** (`uHead`, `uBrake`, `uBlinkL`, `uBlinkR`, `uDriver`, logica in `carLights`,
sezione 13): fari accesi al tramonto con un **alone finto** che si spegne di taglio e la pozza di
luce sull'asfalto; **stop** quando il mezzo rallenta (anche prima degli incroci, con l'acceleratore)
e da fermo; **frecce** prima della svolta, quando l'angolo supera 0,4 rad; parcheggiato tutto spento.

**Riflessi**: una mappa d'ambiente al tramonto generata dal codice (`VehicleFactory.setEnv`) vale
solo per i mezzi; il resto della scena usa `scene.environment` come prima.

**Mongolfiera** (sezione 7c, `VehicleFactory.register('balloon')`): pallone a 14 spicchi (tre
colonne per spicchio), fascia blu, cesta di vimini con le funi, bruciatore con la **fiamma a tratti**
(gruppo di luce 7) e il suo **soffio** generato con Web Audio (`Burner`, sezione 11d), il pilota e la
figurina, un dondolio leggero. È un'eccezione come il Ponte Acquedotto: **vola su un giro fisso e non
segue le vie** (sezione 6c).

Il ritmo moltiplica le velocità di `CONFIG.drive`. Ogni mezzo è costruito una sola volta e poi
riusato: il cambio è istantaneo. Nei menu le sagome (`icon`) sono ricavate dalle sezioni delle
carrozzerie. Sul telefono il menu ha cinque tessere su una riga, sagoma sopra e nome breve sotto
(il nome intero resta per i lettori di schermo); su PC schede su due colonne e la mongolfiera su una
riga intera.

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
* Alla testata est del ponte il **ponte ha la precedenza** sulla scelta "più dritta".
* **Acceleratore** (blocco E, solo su PC): tenendo premuto **Shift** la crociera si moltiplica per
  1,8 (`CONFIG.drive.boost`), con una salita e una discesa morbide (`boostRate`). Agli incroci il
  cartello si apre prima, in proporzione alla velocità (38 m × velocità / crociera, circa 68 m), e
  quando la scelta è aperta il mezzo torna alla crociera: il tempo per scegliere resta quello di
  sempre. Non vale a piedi, in pausa, nelle gocce e prima di un tratto a piedi. Sul telefono non
  c'è: il committente ha preferito non rischiare rallentamenti. Misure: vista «accelerata» di
  `prestazioni.mjs` subito dopo Parti (60 fps, fotogramma peggiore come senza acceleratore).
* **Pendenze**: dal blocco E il limite del 18% vale per tutte le vie del mezzo; il raccordo tra il
  terreno disegnato del centro storico e le quote reali è largo 230 m anche a nord e a est
  (prima 110 m: lì c'erano vie al 29–37%). Resta sopra il 20% solo un tratto di Via Goito (22%).

### 6b. A piedi (fase 3.4, blocco G)

* **Rete**: marciapiedi, passaggi e scalinate del centro storico (`WALK` in `genera_dati.py`,
  flag 32) entrano nella rete solo se chiudono un anello con le vie: 19 tratti reali, 584 m, di cui
  2 scalinate (70 m); 7 anelli in più. Larghi 1,6–2,4 m: non ritagliano le case come una via.
* **Gocce**: dove una via carrabile continua solo a piedi, la goccia lascia scegliere se scendere o
  tornare indietro. In fondo a Via giudice Montea (verso la scalinata), Via Civita e Via Matteotti
  la goccia non ci sta: lì si prosegue per forza a piedi. `validate()` controlla che ogni gruppo di
  tratti pedonali arrivi a una via carrabile.
* **Scendere**: quando l'uscita scelta è a piedi, il mezzo frena e si ferma a 3,2 m dall'imbocco;
  la figurina scende accanto alla portiera (0,9 s) e cammina a 2,6 m/s (più svelta del passo vero,
  1,4 m/s, per non annoiare). Sulle scalinate segue i gradini.
* **Risalire**: appena si sceglie un'uscita carrabile, il mezzo va ad aspettare lì, 3,2 m dopo
  l'incrocio e girato nel verso giusto (nella realtà ci arriverebbe per altre vie). Si sposta solo
  quando il parcheggio di prima è fuori dall'inquadratura, o quando la figurina è a meno di 16 m.
* **Figurina** (`Walker`): un visitatore stilizzato con cappello di paglia e zaino, circa 200
  triangoli in una mesh sola, un po' più grande del vero (×1,2). Gambe e braccia oscillano
  spostando i vertici attorno ad anca e spalla.
* **Interfaccia**: cartelli con il pedone e "a piedi · …" (o "al mezzo · …" per tornare); targa
  "percorso pedonale" col pittogramma; nella minimappa i tratti pedonali sono tratteggiati, la
  figurina è un pallino con la direzione e il mezzo parcheggiato una freccia più piccola.
* Pausa, teletrasporto (la figurina risale) e cambio mezzo funzionano anche a piedi.
* **Tratti a piedi del blocco M2**: sentiero degli scavi (A, 1,5 km), Pineta e Parco Robinson,
  Via Pietro Ianora, scale e sottopassaggio della stazione, vialetti della Villa Comunale; nel vivaio
  l'anello V2 (692 m) e il sentiero della Base Scout; i percorsi approvati nella Fiera e nel giardino
  del Casino di Meninni. In tutto 53 tratti, 5,2 km a piedi.
* **Fondovito a piedi** (blocco N2): la Calata Grotte San Michele è tutta pedonale (`PEDONALI_FONDOVITO`: su Street View
  l'auto di Google non ci è passata) e spariscono le due gocce del mezzo; i Gradoni San Giovanni Battista arrivano a Via
  Marconi con un raccordo di 18 m nell'area pedonale di Piazza Pellicciari (`RACCORDI_PIEDI`); la terrazza di San Michele
  prosegue sul ponticello (`PONTICELLO`, in piano come il ponte) fino alla **goccia della figurina** sul promontorio
  (`GOCCE_PIEDI`: piccola, raggio 1,7–2,4 m, lontana da case e mura). Il mezzo aspetta su Via Marconi, Via Civita o Piazza
  Pellicciari. Rete: mezzo da 89,43 a 89,13 km; a piedi da 53 a 68 tratti, da 5,2 a 5,6 km.
* **Santa Lucia a piedi** (blocco N2b): il footway OSM w1195336380 (60 m, «Passaggio pedonale» nel diorama) scende da
  Via Michelangelo Calderoni (il nodo [48,6; 85,8] è ora un incrocio: Via Calderoni passa da una via sola a due) alla chiesa
  w411139356, dove finisce con la **goccia della figurina** (`GOCCE_PIEDI`, punto [−4,5; 107,6]); la scheda «Santa Lucia» si
  apre lungo il passaggio. Rete: da 1 544 a 1 548 tratti, da 94,44 a 94,52 km; a piedi da 92 a 95 tratti, da 5,61 a 5,68 km;
  gocce da 11 a 12 (contati dalla pipeline).
* **Sosta in panchina** (blocco M2, `Soste`, sezione 7b del codice): nella piazzetta del Monumento ai
  Caduti la figurina si siede sulla panchina reale (OSM) più vicina al percorso e guarda il
  monumento; la scheda resta aperta e dopo circa 5 s compare il pulsante **Esci dalla piazzetta ·
  torna al mezzo**, che con una dissolvenza riporta al mezzo **dove era parcheggiato**. La Villa non
  ha ingressi a piedi su Corso Vittorio Emanuele: il mezzo aspetta dove si è scesi (Piazza
  Pellicciari o uno dei vicoli d'ingresso). Sul telefono il pulsante sta in basso, a tutta larghezza.

### 6c. La mongolfiera (blocco M3)

* **Giro fisso** (`CONFIG.balloon`, `Volo` e `Flight`, sezione 8b): curva chiusa (Catmull-Rom
  centripeta) sui 13 punti del piano: decollo sul prato degli scavi di Botromagno, Necropoli, Madonna
  della Stella e Ponte Acquedotto, Piaggio, San Francesco, Porta San Michele, Piazza della Repubblica,
  Purgatorio, Cattedrale, Fondovito, Sette Camere, il resort e il ciglio ovest. **2 725 m in 7
  minuti**, a 6,5 m/s, più piano al decollo e all'atterraggio.
* **Quota**: 63–131 m dal suolo; sale da sola per restare **almeno 30 m sopra** tetti, cime dei
  monumenti (anche il campanile della Cattedrale) e terreno entro 40 m, con salite dolci; fuori da
  questa regola solo il decollo e l'atterraggio. Sempre dentro la zolla della città, lontano dal bosco
  (`forestAmount` = 0 su tutto il giro). `simula.mjs` lo controlla ogni 5 m.
* **Schede** quando passa sopra un luogo (raggio di almeno 45 m); le etichette senza scheda (scuole,
  chiese della città, luoghi minori) si vedono solo entro 150 m. **Targa**: «In mongolfiera», il rione
  sotto la cesta e i metri dal suolo. Minimappa e mappa della pausa mostrano il giro tratteggiato.
* **Cambio mezzo**: dalla schermata iniziale si decolla da Botromagno; dalla pausa la mongolfiera
  compare in volo nel punto del giro più vicino; tornando a un'auto si riparte dalla via percorribile
  più vicina. L'acceleratore non fa niente in mongolfiera.
* **Teletrasporto**: al punto del giro più vicino al luogo se è entro 300 m; altrimenti, e per i luoghi
  del bosco, il P.I.P., il Castello Svevo e il Casino di Meninni, si scende e ci si va con l'ultima auto.
* **Fine del giro**: atterra al decollo e si riparte con l'ultima auto dalla via percorribile più
  vicina (Via Madonna della Stella, a 139 m), come ha chiesto il committente.

### 6d. Sottopassi (blocco M2)

Dove OSM segna una galleria sotto i binari (Corso Giuseppe di Vittorio, Via Falcone e Borsellino, il
sottopassaggio pedonale della stazione) la via scende in **trincea** (`Sottopassi`, sezione 5 del
codice): dall'incrocio di prima a quello di dopo la quota cala con le rampe (16,5%, entro il 18%)
fino alla profondità della galleria. Il terreno si ritaglia, ai lati ci sono i muri di contenimento
col parapetto e sopra la galleria l'**impalcato** alla quota dei binari; i binari salgono di poco se
sotto restano meno di 3,8 m liberi. Nel sottopassaggio pedonale della stazione, dove la rampa supera
il 12%, ci sono i **gradini** (alzate da 16 cm, `Tiles._steps`, solo nella versione vicina dei
riquadri). A Via Spinazzola i binari passano su un viadotto con le pile.

---

## 7. Camera

* **Vetrina** all'apertura, a due tempi (`CONFIG.camera.showroom`): per 9 s la camera ondeggia piano attorno al tre quarti posteriore del mezzo fermo, dal lato più aperto, e guarda la strada davanti; poi un volo a gru di 3,5 s porta a un **campo lungo dal canyon**, a sud-ovest del ponte, con le arcate su due ordini; dopo 10 s si torna al primo piano. Scegliendo un mezzo si torna subito al primo piano. Pose diverse per schermi orizzontali e verticali, calcolate rispetto all'asse del ponte. Nel blocco M3 le pose sono state rifatte: quelle di prima stavano dietro la collina della sponda est, che copriva quasi tutto il ponte; in verticale, dove il ponte non ci sta insieme al mezzo, c'è un **campo medio** sul mezzo che arriva alla testata accanto alla Fontana della Stella. Sul telefono in orizzontale il primo piano guarda meno avanti, così il mezzo resta nella parte libera dal pannello.
* **Mongolfiera** (blocco M3, `rig.balloon()`, `CONFIG.camera.balloon`): **vista esterna**, un giro
  largo e lento attorno al pallone (52 m, 14° dall'alto, 0,45 giri al minuto), con la camera libera
  (trascinando e con la rotella, 26–160 m) che resta dov'è fino a **Segui il mezzo**; **vista dalla
  cesta**, occhi a 1,75 m, si guarda avanti e un po' in basso, col dondolio, e trascinando ci si guarda
  attorno (la figurina sparisce). Il pulsante **Vista dalla cesta / Vista esterna** (`#btn-view`)
  passa dalla prima alla terza persona e viceversa, senza timer. In vetrina il pallone si guarda dal
  prato, a ovest, verso il centro storico (in verticale più da lontano, perché ci stia tutto sopra il
  pannello). In pausa la vista dall'alto è più larga.
* **Inseguimento dall'alto** (18 m sopra il mezzo, 12 m dietro; un po' più alto per il trattore): si vede la strada tra i tetti, come in un plastico.
* **In salita e in discesa** (blocco N1): se la pendenza media dei prossimi 25 m supera il 4%
  (`driver.gradeAhead`), la camera scende verso 30° d'inclinazione (`CONFIG.camera.slopeElev`) e si
  allontana del 15%, e il giro automatico preferisce tre quarti e fianco (`auto.slopeShots`), da dove la
  pendenza si vede. Nei vicoli stretti resta il sollevamento sopra i tetti, che lì vince.
* **Tetti**: se un tetto si mette tra la camera e il mezzo, o la camera finisce a ridosso di un tetto, la camera sale (fino a 22 m in più) e si avvicina in pianta. Usa una griglia dei tetti (celle da 10 m) con la quota di ogni edificio e arco.
* **Giro automatico** (blocco G, `CONFIG.camera.auto`): mentre il mezzo avanza la camera passa
  piano da un'inquadratura all'altra attorno al mezzo: dietro, tre quarti a sinistra, fianco destro,
  tre quarti davanti, tre quarti a destra, con 3–7 s per inquadratura. Negli ultimi 22 m prima di un
  incrocio con scelta torna dietro, per vedere dove si va; si ferma durante le panoramiche.
* **Camera libera** (blocco B, fatto nel blocco G): trascinando col mouse o con un dito si gira
  attorno al mezzo (inclinazione 10–80°), con la rotella o due dita si cambia la distanza (8–70 m).
  Sotto i 6 px è un tocco. Dal blocco M1 la camera resta dov'è finché non si preme **Segui il
  mezzo** (visibile solo con la camera libera, anche sul telefono), che la riporta dietro in circa
  1,5 s: niente ritorno automatico. Tetti e terreno valgono anche qui; le panoramiche si sospendono.
* **A piedi**: più bassa e vicina (6,5 m dietro, 4,6 m sopra), sale al massimo di 15 m sui tetti.
* **Pausa**: vista dall'alto che gira piano sopra il mezzo; si gira trascinando e si zooma. Non
  entra più nei tetti delle palazzine (stesso `#roofLift` dell'inseguimento).
* **Pannelli**: l'inquadratura si sposta (view offset) nella parte di schermo libera dal pannello iniziale o dal menu di pausa.
* **Ponte**: la camera entra nel canyon, 80 m a monte lungo il torrente, all'altezza dell'impalcato.
* **Ciglio**: sulle vie che corrono lungo il ciglio (Via giudice Montea, Via Fontana la Stella, il sentiero ovest) fa una ripresa "da drone" di tre quarti dall'alto verso il canyon, con 25 s di pausa tra una e l'altra.

### 7a. Radio (fase 3.4, blocco G)

Il committente aveva chiesto le canzoni di Non-Stop-Pop FM (la radio di GTA V): sono brani
commerciali protetti, e un solo MP3 pesa più di tutto il diorama. Ha scelto musica **ambient
rilassante, alla Minecraft**, generata dal codice (sezione 11b, `Radio`), senza file:

* sei brani originali con titoli di Gravina (Tufo, Chianche, Botromagno, Fondovico, Acquedotto,
  Piaggio), ciascuno con tonalità, passo (50–62 battiti al minuto), timbro e accordi suoi;
* pianoforte, celesta o flauto a sintesi (oscillatori con attacco breve e coda lunga), basso
  lento a ogni cambio d'accordo, tappeto morbido, riverbero da una coda di rumore generata;
* note rade scelte da un generatore con seme: ogni brano torna uguale; respiri ogni otto battute
  e un finale che sfuma; 32 battute a brano (2–3 minuti), poi il successivo;
* pulsante **Musica** sotto Pausa (spenta all'avvio: i browser non permettono la musica prima di
  un gesto), tasto **M**, brano successivo e volume (sul telefono bastano i tasti del volume).
  Se era accesa, si riaccende premendo Parti. Tace quando la scheda è nascosta.

**Suoni del bosco** (blocco L, rifatti nel blocco M2; sezione 11c, `ForestSound`): generati con Web
Audio, senza file. Il fruscio e il vento a banda larga sembravano pioggia: al loro posto un soffio
basso e lento a raffiche rare; **uccelli melodici** intonati sulla scala pentatonica del brano della
radio (merlo, pettirosso, capinera, fringuello, tortora, un cuculo lontano); **grilli** al tramonto e
qualche coro morbido di **cicale**; ogni tanto un **allocco** e il **picchio** che tamburella, di rado il
grugnito lontano di un **cinghiale** e, molto di rado, un **ululato di lupo** lontano e melodico.
Passi morbidi solo a piedi. Partono solo **dentro il bosco vero**: `forestAmount` conta le celle di
querce in un raggio di 25 m, con 3 s di dissolvenza; uscendo si spengono e il contesto audio si
sospende. Nel bosco la radio, se accesa, scende al 35%. Si spengono dalla pausa con l'interruttore
**Suoni del bosco** (ricordato nel browser). In debug si ascoltano uno per uno con
`gravina.ForestSound.play('owl')` (`'wolf'`, `'bird'`, …).

**Soffio del bruciatore** (blocco M3, sezione 11d, `Burner`): rumore filtrato, generato dal codice,
che sale e scende con la fiamma della mongolfiera.

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
partenza, centro, Piazza Scacchi, pausa, panoramica sulla città, alta (120 m sopra il centro
storico, verso la città), teletrasporto, bosco a piedi e, dal blocco M3, «mongolfiera» (il punto
più pesante del giro, guardando verso la città).
"Per fotogramma" è il massimo tra le viste, senza il passaggio delle ombre.

| Voce | Fase 3 (solo centro storico) | Fase 3.4, città intera | Dopo il blocco G | Dopo il blocco I | Dopo il blocco D | Dopo il blocco M1 | Dopo il blocco M3 (con M2) | Tetto |
|---|---|---|---|---|---|---|---|---|
| `index.html` | 390 KB (124 KB compressi) | 737 KB (269 KB compressi) | 593 KB (251 KB compressi) | 604 KB (255 KB compressi) | 634 KB (264 KB compressi) | 742 KB (298 KB compressi) | 866 KB (337 KB compressi) | ≤ 1,2 MB (≤ 360 compressi; prima 900 KB e 280, alzato dal committente il 30/09/2026) |
| Costruzione fino a "Parti" | 282 ms | circa 500 ms | circa 520 ms | circa 640 ms (telefono 620) | circa 770 ms (telefono 680) | circa 1 075 ms (telefono 990) | circa 1 130 ms (telefono 1 075) | ≤ 1,5 s |
| Memoria JavaScript | 41 MB | circa 100 MB | 112 MB (telefono 91) | 116 MB (telefono 129) | 117 MB (telefono 104) | 170 MB senza pulizia, 148 MB dopo la garbage collection (telefono 149) | 174 MB (telefono 157); prima di M3 179 e 161 | ≤ 150 MB |
| Città completa (in sottofondo) | — | circa 900 ms | circa 900 ms | circa 1 100 ms | circa 1 230 ms | circa 1 870 ms | circa 2 150 ms | — |
| Triangoli nella scena | 267 000 | 543 000 (telefono 483 000) | 571 000 (telefono 505 000) | 572 000 + 138 000 della versione lontana, mai disegnate insieme (telefono 505 000 + 116 000) | 580 000 + 138 000 (telefono 514 000 + 116 000) | 978 000 + 166 000, con il bosco fitto del blocco L e il terreno a 7,5 m lungo le vie (telefono 825 000 + 134 000) | 1 333 000 tra le due versioni, con i luoghi di M2 e i mezzi nuovi (telefono 1 085 000) | ≤ 650 000 (tetto del blocco C) |
| Triangoli per fotogramma, PC | 267 000 | 334 000 | 335 000 | 235 500 (alta) | 246 000 (alta) | 249 000 (alta) | 283 600 (mongolfiera; alta 271 700) | ≤ 400 000 (obiettivo del blocco I: 300 000) |
| Triangoli per fotogramma, telefono | 267 000 | 242 000 | 243 500 | 164 700 (centro) | 175 300 (centro) | 176 600 (centro) | 183 200 (centro) | ≤ 250 000 (obiettivo del blocco I: 200 000) |
| Draw call, PC / telefono | 39 / 38 | 69 / 54 | 69 / 48 | 68 / 48 | 68 / 48 | 71 / 48 | 56 / 35 (prima di M3 71 / 50): 4 mesh per mezzo invece di più di 20 | ≤ 90 / ≤ 70 |

Nel blocco G il peso è sceso nonostante figurina, camera e radio: nodi, vie, vie decorative ed
edifici del centro storico ora usano il `CODEC` (a 0,1 m, senza perdite), da 90 a 55 KB compressi.

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
| 3 | **Architettura e fedeltà**: Cattedrale e Purgatorio sulle fonti, San Michele e Madonna della Stella scavate nella roccia, rioni a gradoni in discesa con scalinate reali e abitazioni rupestri, altezze affidabili o stimate per zona, schede di altre cinque chiese, vetrina con il campo lungo sulle arcate | ✅ approvata il 28/09/2026 |
| 3.4 C | **Città intera**: zolla di 2,9 × 3,1 km a riquadri, 80 km di vie, 1 828 edifici della città, quote Copernicus, binari, Castello Svevo, mappe vettoriali con zoom | ✅ (PR #8) |
| 3.4 F | **Strade per il Bosco Difesa Grande e il P.I.P.**: tre zolle, tracciato reale compresso, bosco di querce | ✅ (PR #10) |
| 3.4 G | **Percorsi a piedi e quote reali del centro storico**, con la camera attorno al mezzo (blocco B) e la radio ambient | ✅ (PR #12) |
| 3.4 I | **Spazio sul telefono**: due livelli di dettaglio per riquadro, vista «alta» nelle misure | ✅ (PR #13) |
| 3.4 D | **Centro storico**: Porta San Michele, Piazza Scacchi, Quattro Fontane, campanili, vie entro il 18% | ✅ (PR #14) |
| 3.4 E + L | **Luoghi della città, scuole e chiese; il Bosco da vicino**, acceleratore su PC | ✅ (PR #15) |
| 3.4 M1 | **Botromagno, strade, stadio e Fiera** | ✅ (PR #16) |
| 3.4 M2 | **Percorsi a piedi, zone pedonali, sottopassi, parchi, suoni del bosco** | ✅ (PR #17) |
| 3.4 M3 | **Mezzi realistici e mongolfiera**, con il resto di M2 | ⏳ (PR #18) |
| 3.4 N | Cartolina, giro guidato e ritocchi | da fare |
| 4 | Rifinitura: luci, prove su telefoni reali, restyling | ⏳ |

### Da decidere insieme (fase 3, punto 6)

**Percorsi pedonali e scalinate.** *Fatto nella fase 3.4 (blocco G), con la figurina a piedi
(sezione 6b). Sui dati di oggi entrano 19 tratti (584 m) e 2 scalinate su 7: le altre finiscono
nel vuoto.* La stima qui sotto era fatta sul diorama piccolo. Nei dati ci sono 20 tratti di marciapiede o passaggio
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
campagna; nel blocco G guidano la discesa dei rioni del centro storico (sezione 3).* Il modello di
elevazione Copernicus GLO-30 (30 m, licenza libera con
attribuzione) è raggiungibile dal bucket S3 pubblico. Si potrebbe usare nello script per tarare
ciglio, gradoni e discesa dei rioni, oggi tracciati a mano, e scrivere le quote in `GEO`. A
30 m il canyon è appena accennato: servirebbe come guida, non come terreno diretto.
