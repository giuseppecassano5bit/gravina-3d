# Gravina 3D: documento di progetto

Diorama interattivo low-poly del centro storico di Gravina in Puglia, costruito sulle
**vie, gli edifici e il torrente reali**. È un unico file HTML (`index.html`) con Three.js:
tutta la geometria è procedurale, i dati geografici sono incorporati come costante.

Progetto open source realizzato per **Nunzia Food, Eccellenze Pugliesi**.

---

## 1. Visione

Una "Google Earth in miniatura" al tramonto. Una zolla di tufo sospesa nel cielo dorato,
tagliata dalla gravina e attraversata dal Ponte Acquedotto. Una **Ferrari rossa low-poly**
percorre da sola le vie reali del centro storico; a ogni incrocio reale il visitatore
sceglie dove andare. Lungo il percorso compaiono schede brevi sui monumenti.

| Principio | Scelta concreta |
|---|---|
| Fedeltà ai luoghi | Vie, incroci e sagome degli edifici vengono dai dati reali (OpenStreetMap via Overture Maps). |
| Stile a blocchi | Ogni edificio reale è un blocco estruso di tufo o intonaco, con finestre, persiane, terrazze o tetti in coppi. |
| Riconoscibilità | I monumenti hanno forme dedicate: Cattedrale con campanile, chiese con tetto a capanna e campanile a vela, ponte ad archi su due ordini. |
| Zero collisioni, 60 fps | L'auto segue spline precalcolate sulla rete reale: niente fisica. |

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
3. **Edifici.** Sagome reali semplificate a 0,3 m, con cortili (fori), classe e nome.
4. **Morfologia.** Corso del Torrente La Gravina, falesie, mura, belvederi, aree pedonali e verdi, luoghi d'interesse.
5. **Ciglio del canyon.** È tracciato a mano, una volta sola, su belvederi, mura del Fondovico,
   falesie e testate del ponte (costanti `EAST_RIM` e `WEST_RIM`).
6. **Scrittura.** La costante `GEO` viene scritta tra i marcatori `@@DATI-GEO-INIZIO@@` e
   `@@DATI-GEO-FINE@@` di `index.html` (circa 115 KB).

### Numeri attuali

| Voce | Valore |
|---|---|
| Vie percorribili | 157 tratti, 111 incroci, circa 9 km |
| Inversioni a goccia | 4 |
| Edifici reali | 539 |
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
| Tetti | Terrazze piane con torrini, cisterne e comignoli; i piccoli corpi rettangolari hanno spesso un **tetto a capanna in coppi**. |
| Finestre e porte | Pannelli istanziati lungo ogni facciata, piano per piano: persiane marroni o verdi, portoni al piano terra (fino a 32 000 istanze, una sola draw call). |
| Chiese | Pietra di tufo, tetto a capanna, **campanile a vela** sul lato corto. |
| Cattedrale | Sagoma reale, navata centrale rialzata con tetto a capanna, **facciata ovest con rosone**, abside a est, **campanile sul fianco sud** (dove si apre l'ingresso principale, verso Piazza Benedetto XIII). |
| Ponte Acquedotto | Prospetto estruso con **archi su due ordini**: 4 grandi arcate sul canyon più una fila di archetti sotto l'impalcato, circa 25 archi come l'originale. Parapetti, larghezza reale 5,5 m. |
| Mura | I tratti reali di mura urbane diventano muri di tufo. |
| Alberi | Pini e lecci nei giardini reali (Villa Comunale), ulivi verso Botromagno, macchia nel canyon. |

Monumenti con scheda (solo fatti verificati): Cattedrale, la Gravina (belvedere), Chiesa del
Purgatorio, Palazzo Ducale Orsini, Museo Pomarici Santomasi, Santa Lucia (Piaggio), Gravina
Sotterranea, Piazza Pellicciari, Sant'Agostino, San Michele delle Grotte (Fondovico), Ponte
Acquedotto, Fontana della Stella, Madonna della Stella, Botromagno. Altre chiese e piazze
hanno solo l'etichetta.

---

## 5. Ferrari low-poly (ispirata a LaFerrari)

Quote reali: 4,70 × 1,99 × 1,12 m, passo 2,65 m, cerchi da 19" davanti e 20" dietro.
Colore **Rosso Corsa**. Il modello non riproduce loghi o marchi.

| Parte | Primitiva |
|---|---|
| Pianale | esaedro a cuneo, bassissimo davanti |
| Muso | esaedro ribassato tra due **parafanghi a pinna** |
| Abitacolo | esaedro a goccia in vetro scuro, tetto in tinta |
| Fianchi posteriori | esaedri muscolosi sopra le ruote dietro; grandi prese d'aria nere |
| Cofano motore | esaedro in carbonio che scende verso la coda |
| Coda | alettone, diffusore, **quattro fanali tondi**, tre scarichi centrali |
| Ruote | cilindri a 14 lati, 5 razze; le anteriori sterzano |

---

## 6. Movimento, incroci e cartelli

* L'auto segue la spline della via: crociera 8,5 m/s, 5,5 m/s vicino agli incroci, 6 m/s sul ponte, 4,5 m/s nelle inversioni.
* A 38 m dall'incrocio si calcolano le uscite (tutte tranne l'inversione) ordinate da sinistra a destra con l'**angolo di svolta reale**. La più dritta è preselezionata.
* **Cartelli marroni**:
  - in grande il nome reale della via;
  - per i vicoli senza nome, "Vicolo per" seguito dalla via in cui sboccano;
  - sotto, il prossimo monumento lungo quella via ("verso Chiesa del Purgatorio"), oppure il rione.
* **Targa in marmo**: via corrente più rione (Centro storico, Rione Piaggio, Rione Fondovico, Madonna della Stella · Botromagno), e "percorso pedonale" dove serve.
* Le quote delle strade sono smussate (media mobile di ±6 m), così i gradoni del terreno non si sentono sotto le ruote.

---

## 7. Camera

* **Orbita** d'attesa sopra tutto il diorama.
* **Inseguimento dall'alto** (16 m sopra l'auto, 14 m dietro): si vede la strada tra i tetti, come in un plastico.
* **Ponte**: la camera entra nel canyon, 80 m a monte lungo il torrente, all'altezza dell'impalcato.
* **Ciglio**: sulle vie che corrono lungo il ciglio (Via giudice Montea, Via Fontana la Stella, il sentiero ovest) fa una ripresa "da drone" di tre quarti dall'alto verso il canyon, con 25 s di pausa tra una e l'altra.

---

## 8. Prestazioni

| Voce | Valore |
|---|---|
| Triangoli totali | circa 225 000 (terreno 70k, edifici, 25k finestre istanziate) |
| Draw call | circa 30 |
| Costruzione della scena | circa 1 s su un PC recente |
| Aggiornamento per frame | O(1) sulla spline; minimappa copiata da un canvas pre-disegnato |

---

## 9. Stato e prossimi passi

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ |
| 2 | Base: rete, auto, incroci, camera, interfaccia | ✅ |
| 2b | **Dati reali**: vie e incroci reali, 539 edifici reali, torrente e cigli reali, Ferrari, ponte ad archi | ✅ in revisione |
| 3 | Architettura: facciate più ricche per i monumenti, San Michele e Madonna della Stella scavate nella roccia, portali, dettagli dei rioni | ⏳ |
| 4 | Rifinitura: luce dorata, ombre, musica procedurale (Web Audio, 40%, muto), transizioni di camera, prestazioni su mobile | ⏳ |

Il prompt per continuare il lavoro in una nuova chat è in [`PROMPT_NUOVA_CHAT.md`](PROMPT_NUOVA_CHAT.md).
