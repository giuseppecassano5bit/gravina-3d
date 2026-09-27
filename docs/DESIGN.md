# Gravina 3D: documento di progetto

Diorama interattivo low-poly del centro storico di Gravina in Puglia.
Un unico file HTML (`index.html`), tutto procedurale e costruito con Three.js.
Progetto open source realizzato per **Nunzia Food, Eccellenze Pugliesi**.

---

## 1. Visione

Una "Google Earth in miniatura" al tramonto: una zolla di tufo sospesa nel cielo dorato,
tagliata dalla gravina, attraversata dal Ponte Acquedotto. Un'Audi RS Q8 low-poly
percorre da sola le vie reali del centro storico; il visitatore sceglie a ogni incrocio
quale strada esplorare. Lungo il percorso compaiono schede brevi sui monumenti.

Principi guida:

| Principio | Scelta concreta |
|---|---|
| Riconoscibilità più che realismo | Ogni monumento è ridotto alla sua silhouette essenziale: archi del ponte, facciata e campanile del Duomo, grotte nel tufo. |
| Topologia fedele | I punti chiave sono ancorati a coordinate GPS reali convertite in metri. Le vie minori sono interpolate in modo plausibile. |
| Zero collisioni, 60 fps | Il veicolo segue una rete di spline precalcolata: niente fisica, niente raycast per frame. |
| Faccette nette | Tutti i materiali usano `flatShading: true`, con colori per faccia e nessuna texture caricata. |

---

## 2. Sistema di coordinate

* **Origine**: Cattedrale di Santa Maria Assunta (40.8174 N, 16.4134 E).
* **Unità**: 1 unità Three.js = 1 metro.
* **Assi**: `x` = Est, `y` = quota, `z` = −Nord (in Three.js la camera guarda verso −z, quindi il Nord è "avanti").
* **Conversione** (equirettangolare locale, errore < 0,1% su 1 km):

```
est   = (lon − lon0) · 111 320 · cos(lat0)   ≈ (lon − 16.4134) · 84 248 m
nord  = (lat − lat0) · 111 132                ≈ (lat − 40.8174) · 111 132 m
```

### Ancore verificate (fonti pubbliche)

| Luogo | Lat | Lon | Est (m) | Nord (m) |
|---|---|---|---|---|
| Cattedrale (origine) | 40.8174 | 16.4134 | 0 | 0 |
| Ponte Acquedotto (centro) | 40.820115 | 16.412897 | −42 | +302 |
| Chiesa rupestre Madonna della Stella | 40.81989 | 16.41234 | −89 | +277 |
| Chiesa del Purgatorio (P.zza Notar Domenico) | 40.817360 | 16.414903 | +127 | −4 |
| Piazza della Repubblica (Palazzo Orsini) | 40.81725 | 16.41692 | +297 | −17 |
| Corso Vittorio Emanuele | 40.816502 | 16.4159 | +211 | −100 |

Fatti geografici usati per il modello:

* Il centro storico sta sul **bordo orientale** della gravina; a ovest si alza la collina di **Botromagno** (parco archeologico).
* Il Ponte Acquedotto è lungo **90 m**, largo **5,5 m** e alto **37 m**. Collega la città alla chiesa rupestre della Madonna della Stella, sul versante opposto.
* I rioni medievali **Piaggio** e **Fondovico** sono scavati nel tufo lungo il canyon, sotto la Cattedrale.
* **San Michele delle Grotte** si trova in fondo a Calata Grotte San Michele, nel rione Fondovico, sul ciglio della gravina.

> **Accuratezza.** Le ancore qui sopra sono reali. Il tracciato delle vie *tra* le ancore
> è stilizzato. L'insegna di Nunzia Food è posta in Piazza della Repubblica come punto
> di partenza scenografico: se il negozio ha un indirizzo diverso, basta spostare
> `START` in `index.html`.

---

## 3. Rete stradale (spline codificate)

La rete è un **grafo non orientato**: i **nodi** sono gli incroci e le piazze, gli **archi** sono le vie.
Ogni arco è una `CatmullRomCurve3` (centripeta, senza "overshoot") che passa per i nodi
estremi e per i punti intermedi indicati. La curva viene campionata ogni ~1 m in un
`Float32Array`: la posizione a una certa distanza si legge così in O(1).

### Nodi

| ID | Nome | Est, Nord (m) | Quota |
|---|---|---|---|
| `REP` | Piazza della Repubblica (partenza, Nunzia Food) | 297, −17 | terreno |
| `NOT` | Piazza Notar Domenico (Purgatorio) | 127, −20 | terreno |
| `DUO` | Piazza Benedetto XIII (Cattedrale) | 42, −12 | terreno |
| `PIA` | Belvedere del Piaggio | −115, −100 | terreno |
| `COR` | Corso Vittorio Emanuele | 211, −110 | terreno |
| `PEL` | Piazza Pellicciari | 60, 85 | terreno |
| `SMG` | San Michele delle Grotte | −40, 160 | terreno |
| `PTE` | Ponte, testata est | 2, 290 | −10 |
| `PTO` | Ponte, testata ovest (verso la Madonna della Stella) | −86, 314 | −10 |
| `BOT` | Belvedere di Botromagno | −165, 335 | terreno |

### Archi

| Da ↔ A | Nome sulla targa | Note |
|---|---|---|
| REP ↔ NOT | Centro storico | |
| NOT ↔ DUO | Centro storico | arrivo in piazza del Duomo |
| DUO ↔ PIA | Rione Piaggio | scende verso il ciglio |
| PIA ↔ COR | Corso Vittorio Emanuele | |
| COR ↔ REP | Via della Libertà | collega il Corso a Piazza della Repubblica |
| DUO ↔ PEL | Rione Fondovico | |
| NOT ↔ PEL | Centro storico | |
| PIA ↔ SMG | Belvedere sulla Gravina | inquadratura panoramica sul canyon |
| PEL ↔ SMG | Calata Grotte San Michele | |
| SMG ↔ PTE | Rione Fondovico | rampa che scende al ponte, panoramica |
| PEL ↔ PTE | Rione Fondovico | |
| PTE ↔ PTO | **Ponte Acquedotto** | inquadratura cinematografica dall'interno del canyon |
| PTO ↔ BOT | Via Madonna della Stella | anello di ritorno |
| BOT ↔ PTO | Parco archeologico di Botromagno | anello di ritorno |

```
                    BOT ──── PTO ═══ Ponte ═══ PTE
                     ╰───────╯              ╱     ╲
                                         SMG ──── PEL
                                          │      ╱   ╲
                                          │   DUO ─── NOT ─── REP ★ Nunzia Food
                                          │  ╱                      │
                                          PIA ──── Corso ──── COR ───╯
```

### Garanzia "nessun vicolo cieco"

1. Il veicolo **non fa mai inversione**: arrivato a un nodo, può prendere qualunque arco tranne quello da cui arriva.
2. Ogni nodo ha **grado ≥ 2**. Quindi esiste sempre almeno un'uscita e il giro può continuare all'infinito.
3. Oltre il ponte la rete si chiude con un **anello** (PTO → BOT → PTO): si può tornare indietro senza inversioni.
4. `TrackNetwork.validate()` verifica i punti 1 e 2 all'avvio e segnala in console qualunque violazione.

---

## 4. La gravina (topologia del canyon)

* **Asse del canyon**: spline di 10 punti da SSO a NNE. Passa sotto il ponte, dove la tangente è perpendicolare all'asse del ponte.
* **Profilo trasversale** in funzione della distanza `d` dall'asse:
  * fondo (`d < 10 m`): quota −44 m, letto del torrente e macchia verde;
  * pareti (`10 m < d < ~48 m`): 5 **gradoni** di tufo, cioè cenge piatte seguite da salti ripidi. Evocano la stratificazione della roccia e le grotte;
  * sponda est (città): scende a terrazze da 0 m a −6 m verso il ciglio (Piaggio e Fondovico);
  * sponda ovest (Botromagno): parte da −9 m al ciglio e sale dolcemente verso la collina.
* **Adattamento alle strade**: il terreno viene "spianato" sotto ogni via, con un raccordo morbido di 12 m, così le strade poggiano sempre sulla roccia. Il ponte è escluso, perché deve restare sospeso sul vuoto.
* **Effetto diorama**: la zolla è ritagliata in un rettangolo con pareti laterali a strati di tufo, come un plastico da museo.

---

## 5. Estetica "tufo" in flat shading

* Il terreno è una griglia di 5 m con i vertici **leggermente sfalsati** (jitter deterministico): i triangoli risultano irregolari, come in una scultura sfaccettata.
* La geometria non è indicizzata e ha **un colore per faccia** (vertex color identico sui 3 vertici). La scelta dipende da:
  * pendenza (normale): roccia sulle pareti, terra sui piani;
  * quota: bande alternate di tufo sulle pareti, come strati sedimentari;
  * sponda: tufo chiaro in città, campi dorati e ulivi a Botromagno.
* Ogni faccia ha una piccola variazione casuale di luminosità (±4%), per un effetto "pietra viva".
* Palette del tufo: `#E8D2A0` chiaro, `#D4B577`, `#C4A265`, `#B08D58` in ombra; macchia `#7F8A4A`.
* Tutti i materiali sono `MeshStandardMaterial({ flatShading: true })`. Le luci sono calde e radenti (fase 4).

---

## 6. Audi RS Q8 low-poly

Quote reali: lunghezza 5,01 m, larghezza 2,00 m, altezza 1,69 m, passo 3,00 m, cerchi 22–23".

Il modello usa solo **box deformati** (esaedri a 8 vertici), **cilindri** e **tori**:

| Parte | Primitiva | Dettaglio riconoscibile |
|---|---|---|
| Corpo inferiore | esaedro a cuneo | frontale inclinato, coda alta da SUV |
| Cofano | esaedro inclinato | sale verso il parabrezza |
| Abitacolo | esaedro rastremato (vetro scuro) | linea del tetto **coupé** che scende verso la coda |
| Montante C | esaedri sottili in tinta | spezza il vetro laterale |
| Calandra Singleframe | cilindro a **8 lati** scalato | l'ottagono tipico di Audi |
| Logo | 4 tori low-poly intrecciati | i "quattro anelli" |
| Fari | barre sottili emissive | sguardo affilato |
| Passaruota | esaedri "blister" sopra le ruote | parafanghi allargati quattro |
| Posteriore | barra luminosa rossa a tutta larghezza | firma luminosa RS Q8 |
| Scarichi | 2 cilindri ovali | terminali ovali RS |
| Ruote | cilindri a 14 lati + 5 razze | ruotano con la velocità; le anteriori sterzano |

Gerarchia: `auto` (posizione e imbardata) → `scocca` (beccheggio, rollio, molleggio) + `ruote`.
Colore predefinito: un **blu metallizzato** ispirato al Blu Navarra, complementare al giallo del tufo. Si cambia in `CONFIG.car.color`.

---

## 7. Movimento e incroci

Stato del conducente: `{ arco, verso (+1/−1), s (metri percorsi sull'arco), velocità }`.

1. **Avanzamento**: `s += v·dt`. La velocità tende in modo esponenziale al valore obiettivo: crociera 10 m/s, 6 m/s vicino agli incroci con scelta, 6,5 m/s sul ponte.
2. **Apertura della scelta**: a 55 m dal nodo si calcolano le uscite possibili, escluso l'arco di provenienza. Per ciascuna si misura l'**angolo di svolta** con segno (prodotto vettoriale tra la tangente d'arrivo e quella d'uscita). Le uscite vengono ordinate da sinistra a destra.
3. **Scelta predefinita**: l'uscita più dritta. `←`/`→` spostano la selezione, `↑` torna alla più dritta.
4. **Attraversamento del nodo**: il resto di `s` passa al nuovo arco, quindi il moto resta continuo.
5. **Orientamento**: l'imbardata segue un punto 4 m avanti. Se quel punto cade oltre il nodo, si usa l'uscita selezionata, così l'auto "anticipa" la curva appena scegli. Beccheggio dalla pendenza, rollio dalla velocità d'imbardata.

---

## 8. Camera cinematografica

* **Inseguimento**: dietro e sopra l'auto (13 m indietro, 7,5 m su), con molle critiche su posizione e imbardata.
* **Panoramica gravina**: sulle vie di ciglio la camera sale alle spalle dell'auto, come un drone, e guarda avanti verso il vuoto: l'auto in primo piano, il canyon e il torrente accanto. Scatta a intermittenza, con un tempo di riposo di 25 s.
* **Ponte**: la camera entra nel canyon, 80 m a monte lungo il suo asse, poco sopra l'impalcato. Inquadra il ponte di profilo, l'auto che lo attraversa e il vuoto sotto.
* **Attrazione**: prima della partenza la camera orbita lenta attorno al diorama.
* La camera non scende mai sotto il terreno (controllo sulla quota).

---

## 9. Interfaccia e audio

* **Schermata iniziale**: titolo inciso nel tufo, coordinate reali, pulsante **"Visita Gravina"** e crediti Nunzia Food.
* **Targa stradale** in marmo in alto a sinistra: nome della via o del rione corrente.
* **Cartelli turistici marroni** agli incroci, come la segnaletica italiana: freccia orientata come la svolta reale e destinazione. Su mobile si toccano direttamente, con frecce grandi ai lati.
* **Minimappa** con il Nord in alto: rete, gravina, monumenti e auto.
* **Schede monumento** (stile didascalia museale) quando l'auto passa vicino a un luogo.
* **Musica** (fase 4): Web Audio procedurale con accordi pad, arpeggi pizzicati e riverbero generato. Entra in dissolvenza; volume predefinito 40%, pulsante muto e cursore.

---

## 10. Budget prestazioni (60 fps)

| Voce | Budget |
|---|---|
| Terreno | ~72k triangoli, 1 draw call |
| Strade e piazze | 1 geometria unita |
| Edifici (fase 3) | `InstancedMesh`, poche draw call |
| Ombre | 1 luce direzionale, mappa 2048, frustum stretto che segue l'auto |
| Aggiornamento per frame | O(1) sulla spline, nessuna allocazione nel ciclo principale |
| Pixel ratio | massimo 2 (1,5 su dispositivi touch) |

---

## 11. Piano di lavoro

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ questo file |
| 2 | Base: rete stradale, Audi RS Q8, movimento, incroci, camera, UI di base, terreno col canyon | ✅ **in revisione** |
| 3 | Architettura: Ponte Acquedotto ad archi, Cattedrale e campanile, Purgatorio, San Michele, Madonna della Stella, case in tufo, vetrina Nunzia Food | ⏳ |
| 4 | Rifinitura: golden hour, ombre nette, riflessi, musica, transizioni di camera, ottimizzazioni | ⏳ |
