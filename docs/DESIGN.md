# Gravina 3D: documento di progetto

Diorama interattivo low-poly del centro storico di Gravina in Puglia, costruito sulle
**vie, gli edifici e il torrente reali**. È un unico file HTML (`index.html`) con Three.js:
tutta la geometria è procedurale, i dati geografici sono incorporati come costante.

Progetto open source realizzato per **Nunzia Food, Eccellenze Pugliesi**.

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
| Riconoscibilità | I monumenti hanno forme dedicate: Cattedrale con campanile, lesene e rosone, chiese con portale e campanile a vela, portale del Purgatorio, ponte ad archi su due ordini. |
| Vie libere | Nessun edificio sulla carreggiata: il mezzo non attraversa mai le case. Dove una casa scavalca davvero la via c'è un arco. |
| Zero collisioni, 60 fps | Il mezzo segue spline precalcolate sulla rete reale: niente fisica. |
| Anche su telefono | Interfaccia touch, pannelli che si adattano a verticale e orizzontale, risoluzione adattiva. |

---

## 2. Dati reali

### Fonte

**Overture Maps Foundation**, release `2026-09-23.1`. I temi usati (vie, incroci, edifici,
acque, infrastrutture, uso del suolo, luoghi) derivano in gran parte da **OpenStreetMap**
(© OpenStreetMap contributors, licenza ODbL 1.0). Alcuni luoghi hanno licenza CDLA-Permissive-2.0.

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
   `level` (i corpi sopraelevati hanno `level = 1`).
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
4. **Morfologia.** Corso del Torrente La Gravina, falesie, mura, belvederi, aree pedonali e verdi, luoghi d'interesse.
5. **Ciglio del canyon.** È tracciato a mano, una volta sola, su belvederi, mura del Fondovico,
   falesie e testate del ponte (costanti `EAST_RIM` e `WEST_RIM`).
6. **Scrittura.** La costante `GEO` viene scritta tra i marcatori `@@DATI-GEO-INIZIO@@` e
   `@@DATI-GEO-FINE@@` di `index.html` (circa 150 KB).

### Numeri attuali

| Voce | Valore |
|---|---|
| Vie percorribili | 157 tratti, 111 incroci, circa 9 km |
| Larghezza delle vie | da 3,4 m (vicoli) a 8 m; 37 tratti ristretti al minimo |
| Inversioni a goccia | 4 |
| Edifici reali | 532 (dopo il ritaglio), nessuno sulla carreggiata |
| Archi sulle vie | 5 |
| Area del diorama | 780 × 860 m (est −340…440, nord −320…540) |

### Sistema di coordinate

* **Origine**: la Cattedrale (40.8174 N, 16.4134 E); 1 unità = 1 metro.
* **Assi Three.js**: `x` = Est, `y` = quota, `z` = −Nord.
* **Conversione**: `est = (lon − 16.4134) · 111 320 · cos(40.8174°)`, `nord = (lat − 40.8174) · 111 132`.

---

## 3. Il canyon (topologia della gravina)

* **Asse**: è il corso reale del Torrente La Gravina, orientato verso nord. Così la sponda destra è sempre quella della città e la sinistra quella di Botromagno.
* Per ogni punto si calcola la posizione relativa `t` tra il torrente (0) e il ciglio (1). Da `t` si ricava il profilo della sponda.

| Sponda | Profilo |
|---|---|
| Città (est) | fondo a −38 m, poi **falesia** fino a −20 m (fino a t = 0,32), poi i **gradoni** dei rioni fino al ciglio a 0 m: Piaggio a nord della Cattedrale, Fondovico a sud |
| Botromagno (ovest) | fondo, poi **parete ripida** a tre salti fino a −8 m, poi un ripiano fino a −3 m, poi l'altopiano che sale verso la collina di Botromagno |

* Il fondo è a −38 m: il ponte (a quota 0 sulla testata est) risulta alto circa 37 m, come quello vero.
* Il terreno viene **spianato sotto le strade** (con raccordi di 9 m), tranne sotto il ponte.
* Le **grotte** sono bocche ad arco sulle pareti lato città. Aggiungono l'effetto "città di pietra scavata".

---

## 4. Edifici e monumenti

| Elemento | Resa |
|---|---|
| Case | Sagoma reale estrusa. Nel centro storico: 2–3 piani (3,3 m per piano), toni di tufo e calce. Nei quartieri moderni: 3–5 piani e intonaci chiari. |
| Tetti | Terrazze piane con torrini, cisterne e comignoli; i piccoli corpi rettangolari hanno spesso un **tetto a capanna in coppi**. Le falde sono **ritagliate sulla sagoma reale** (divise lungo il colmo e triangolate): nessun tetto sporge sulla strada. |
| Archi | Volume di tufo con volta a tutto sesto sopra la carreggiata, ghiera in pietra chiara e finestrella sulle due fronti. |
| Finestre e porte | Pannelli istanziati lungo ogni facciata, piano per piano: persiane marroni o verdi, portoni al piano terra (fino a 32 000 istanze, una sola draw call). |
| Chiese | Pietra di tufo, tetto a capanna, **campanile a vela** sul colmo; sul lato che guarda la via un **portale** con stipiti, architrave, timpano, gradino e **oculo**. |
| Chiesa del Purgatorio | Portale con **timpano spezzato**, i **due scheletri distesi** e, ai lati su piedistalli, gli **orsi degli Orsini** (come nella scheda, fonte FAI). |
| Cattedrale | Sagoma reale, navata centrale rialzata con tetto a capanna, **facciata ovest con rosone** (ghiera e raggi) e croce, abside a est, **campanile sul fianco sud**, **lesene** lungo i fianchi, **portale sud con due colonne** verso Piazza Benedetto XIII. |
| Palazzi | Palazzo Ducale Orsini e Museo Pomarici Santomasi: **cornicione**, fascia marcapiano e **portale in bugnato**. |
| Ponte Acquedotto | Prospetto estruso con **archi su due ordini**: 4 grandi arcate sul canyon più una fila di archetti sotto l'impalcato, circa 25 archi come l'originale. **Lesene** sui piloni, **due cornici** marcapiano, parapetti, larghezza reale 5,5 m. |
| Fontana della Stella | Muro con nicchia ad arco, cornice, vasca con l'acqua, accanto alla testata est del ponte e fuori dalla strada (forma stilizzata). |
| Belvederi | Parapetti in ferro sul ciglio, nei tre belvederi dei dati. |
| Lanterne | Lanterne a muro accese, ogni ~16 m nelle vie entro 70 m dai monumenti (circa 100). |
| Regola | Nessun dettaglio sporge più di 0,3 m dal muro verso la strada. |
| Mura | I tratti reali di mura urbane diventano muri di tufo. |
| Alberi | Pini e lecci nei giardini reali (Villa Comunale), ulivi verso Botromagno, macchia nel canyon. |

Monumenti con scheda (solo fatti verificati): Cattedrale, la Gravina (belvedere), Chiesa del
Purgatorio, Palazzo Ducale Orsini, Museo Pomarici Santomasi, Santa Lucia (Piaggio), Gravina
Sotterranea, Piazza Pellicciari, Sant'Agostino, San Michele delle Grotte (Fondovico), Ponte
Acquedotto, Fontana della Stella, Madonna della Stella, Botromagno. Altre chiese e piazze
hanno solo l'etichetta.

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
* **Partenza**: 26 m prima della testata est del Ponte Acquedotto, sulla via che vi arriva (Via Fontana la Stella), rivolti verso il ponte. Il primo tratto attraversa il ponte.
* **Pausa**: il mezzo frena a 7 m/s² fino a fermarsi; il menu (riprendi, cambia mezzo, mappa e luoghi) compare solo in pausa. Il viaggio va in pausa da solo se la pagina viene nascosta.
* **Teletrasporto** (solo in pausa): dissolvenza, il mezzo va sulla via più vicina al luogo, 12 m prima, e il viaggio riprende da lì con la scheda del monumento. Per il ponte si torna al punto di partenza.
* A 38 m dall'incrocio si calcolano le uscite (tutte tranne l'inversione) ordinate da sinistra a destra con l'**angolo di svolta reale**. La più dritta è preselezionata.
* **Cartelli marroni**:
  - in grande il nome reale della via;
  - per i vicoli senza nome, "Vicolo per" seguito dalla via in cui sboccano;
  - sotto, il prossimo monumento lungo quella via ("verso Chiesa del Purgatorio"), oppure il rione.
* **Targa in marmo**: via corrente più rione (Centro storico, Rione Piaggio, Rione Fondovico, Madonna della Stella · Botromagno), e "percorso pedonale" dove serve.
* Le quote delle strade sono smussate (media mobile di ±6 m), così i gradoni del terreno non si sentono sotto le ruote.

---

## 7. Camera

* **Vetrina** all'apertura: la camera ondeggia piano attorno al tre quarti posteriore del mezzo fermo, dal lato più aperto (verso la gravina), e guarda la strada davanti.
* **Inseguimento dall'alto** (18 m sopra il mezzo, 12 m dietro; un po' più alto per il trattore): si vede la strada tra i tetti, come in un plastico.
* **Tetti**: se un tetto si mette tra la camera e il mezzo, o la camera finisce a ridosso di un tetto, la camera sale (fino a 22 m in più) e si avvicina in pianta. Usa una griglia dei tetti (celle da 10 m) con la quota di ogni edificio e arco.
* **Pausa**: vista dall'alto che gira piano sopra il mezzo.
* **Pannelli**: l'inquadratura si sposta (view offset) nella parte di schermo libera dal pannello iniziale o dal menu di pausa.
* **Ponte**: la camera entra nel canyon, 80 m a monte lungo il torrente, all'altezza dell'impalcato.
* **Ciglio**: sulle vie che corrono lungo il ciglio (Via giudice Montea, Via Fontana la Stella, il sentiero ovest) fa una ripresa "da drone" di tre quarti dall'alto verso il canyon, con 25 s di pausa tra una e l'altra.

---

## 8. Prestazioni

| Voce | Valore |
|---|---|
| Triangoli totali | circa 237 000 (terreno 70k, edifici, 25k finestre istanziate, dettagli) |
| Draw call | circa 37 |
| Costruzione della scena | circa 1 s su un PC recente |
| Aggiornamento per frame | O(1) sulla spline; minimappa copiata da un canvas pre-disegnato; 8 + 16 controlli sulla griglia dei tetti per la camera |
| Ombre | riquadro di 180 m che segue il mezzo, agganciato ai texel (niente sfarfallio) |
| Telefoni e tablet | niente MSAA su schermi densi, mappa d'ombra 1024 e ombre non sfumate, risoluzione che segue gli fps (da 0,9 a 2×) |

---

## 9. Stato e prossimi passi

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ |
| 2 | Base: rete, auto, incroci, camera, interfaccia | ✅ |
| 2b | **Dati reali**: vie e incroci reali, edifici reali, torrente e cigli reali, ponte ad archi | ✅ |
| 2c | **Vie libere e mezzi**: nessuna casa sulla strada, archi reali, quattro mezzi, partenza dal ponte, pausa con cambio mezzo e teletrasporto, camera che scavalca i tetti, dettagli dei monumenti, versione mobile | ✅ in revisione |
| 3 | Architettura: altre facciate dei monumenti, San Michele e Madonna della Stella scavate nella roccia, dettagli dei rioni | ⏳ |
| 4 | Rifinitura: musica procedurale (Web Audio, 40%, muto), transizioni di camera, prove su telefoni reali | ⏳ |

Il prompt per continuare il lavoro in una nuova chat è in [`PROMPT_NUOVA_CHAT.md`](PROMPT_NUOVA_CHAT.md).
