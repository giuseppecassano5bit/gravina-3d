# Gravina 3D

Diorama 3D interattivo in stile low-poly del centro storico di **Gravina in Puglia**,
costruito sulle **vie, gli edifici e il torrente reali**.
Progetto open source realizzato per **Nunzia Food, Eccellenze Pugliesi**.

Una Ferrari rossa low-poly percorre da sola le vie reali del centro storico: da Piazza
Benedetto XIII alla Chiesa del Purgatorio, giù per i rioni Piaggio e Fondovico, fino al
Ponte Acquedotto e oltre la gravina. A ogni incrocio reale scegli tu quale via prendere.
Tutto sta in **un unico file HTML**: la geometria è procedurale e i dati geografici sono
incorporati nel file, senza modelli, texture o GeoJSON caricati a runtime.

## Come si apre

Apri `index.html` in un browser moderno (Chrome, Edge, Firefox o Safari recenti).
Serve una connessione a Internet: Three.js e i font vengono caricati da CDN.

In alternativa puoi avviare un piccolo server locale:

```bash
npx serve .
```

## Comandi

| Azione | Desktop | Mobile |
|---|---|---|
| Partire | pulsante **Visita Gravina** | tocca **Visita Gravina** |
| Scegliere la via all'incrocio | <kbd>←</kbd> <kbd>→</kbd> (oppure <kbd>A</kbd> <kbd>D</kbd>) | tocca un cartello marrone o le frecce ai lati |
| Tornare alla via più dritta | <kbd>↑</kbd> (oppure <kbd>W</kbd>) | tocca il cartello con la freccia dritta |

L'auto avanza da sola. Se non scegli, agli incroci prosegue sulla via più dritta.

## Com'è fatto

Il file `index.html` è diviso in sezioni numerate e commentate:

| # | Sezione | Contenuto |
|---|---|---|
| 0 | Configurazione | tutti i parametri (velocità, camera, sole, colore dell'auto…) |
| 1 | Utilità | matematica, rumore procedurale, geometria piana |
| 2 | Geografia | conversione da latitudine/longitudine a metri |
| 3 | Dati | blocco `GEO` generato (vie, incroci, edifici, torrente…) e monumenti curati |
| 4 | Gravina e terreno | canyon sul corso reale del torrente, falesie e gradoni dei rioni |
| 5 | Rete stradale | vie reali come spline, uscite agli incroci, cartelli, controlli |
| 6 | Mondo | terreno, strade, Ponte Acquedotto ad archi, edifici reali, Cattedrale, grotte, alberi |
| 7 | Ferrari | veicolo costruito solo da primitive |
| 8 | Conducente | movimento automatico e logica degli incroci |
| 9 | Camera | orbita, inseguimento dall'alto, panoramiche su gravina e ponte |
| 10–11 | Interfaccia | minimappa, targa stradale, cartelli, schede dei monumenti |
| 12–13 | Scena e avvio | cielo al tramonto, luci, ombre, ciclo principale |

Il documento di progetto completo è in [`docs/DESIGN.md`](docs/DESIGN.md).

## Dati geografici

Vie, incroci, sagome degli edifici, corso del torrente, mura e luoghi d'interesse vengono da
**[Overture Maps](https://overturemaps.org)** (release 2026-09-23.1), che li deriva in gran
parte da **[OpenStreetMap](https://www.openstreetmap.org/copyright)**.

Per rigenerarli (per esempio dopo aver migliorato la mappa di Gravina su OpenStreetMap):

```bash
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/genera_dati.py --anteprima tools/anteprima.png
```

Lo script scarica solo i pochi MB che riguardano Gravina, costruisce la rete stradale senza
vicoli ciechi e riscrive il blocco `GEO` dentro `index.html`. Le scelte (vie cieche da
conservare, ciglio del canyon, area del diorama) sono costanti commentate in cima allo script.

## Personalizzare

* **Punto di partenza**: costante `START` in `index.html`.
* **Colore dell'auto**: `CONFIG.car.color`.
* **Velocità e ritmo**: `CONFIG.drive`.
* **Monumenti e schede**: array `LANDMARKS`.
* **Vie**: si modificano in OpenStreetMap o nello script di generazione, non a mano nel blocco `GEO`.

## Strumenti per sviluppatori

Aggiungi `?debug` all'indirizzo (per esempio `index.html?debug`) per vedere fps, triangoli e
posizione sulla rete, e per avere in console l'oggetto `window.gravina`. Esempi:

```js
gravina.driver.simulate(3600)          // un'ora di guida con scelte casuali: verifica che l'auto non si blocchi mai
gravina.advance(5)                     // fa avanzare la simulazione di 5 secondi senza disegnare
gravina.placeAt(60, 310, [-1, -0.5])   // mette l'auto sulla via più vicina a (est, nord), diretta verso ovest
```

## Stato del progetto

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ |
| 2 | Base: rete stradale, auto, incroci, camera, interfaccia | ✅ |
| 2b | Dati reali: vie e incroci reali, 539 edifici, torrente e cigli, Ferrari, ponte ad archi | ✅ in revisione |
| 3 | Architettura: facciate più ricche dei monumenti, chiese rupestri scavate nella roccia | ⏳ |
| 4 | Rifinitura: luce dorata, ombre, musica procedurale, prestazioni su mobile | ⏳ |

## Licenze e marchi

* **Dati cartografici** (blocco `GEO` in `index.html`): © OpenStreetMap contributors, disponibili
  sotto [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/). Sono un
  database derivato e restano sotto ODbL; l'attribuzione è visibile nella pagina.
* **Codice**: la licenza è ancora da scegliere (per esempio MIT).
* **Ferrari** e **LaFerrari** sono marchi di Ferrari S.p.A. Il modello nel diorama è
  un'interpretazione stilizzata non ufficiale e non riproduce loghi. Prima di un uso commerciale
  o promozionale, verificate i diritti.

## Fonti

Notizie storiche e posizioni dei monumenti da fonti pubbliche, tra cui:

* Ponte Acquedotto: [Wikipedia (EN)](https://en.wikipedia.org/wiki/Ponte_Madonna_della_Stella), [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/il-ponte-acquedotto-settecentesco-orsiniano-della-madonna-della-stella/), [Viaggiamo.it](https://www.viaggiamo.it/ponte-acquedotto-di-gravina-di-puglia-la-storia/)
* Cattedrale: [Wikipedia](https://it.wikipedia.org/wiki/Concattedrale_di_Santa_Maria_Assunta_(Gravina_in_Puglia)), [GCatholic](https://gcatholic.org/churches/italy/1312.htm), [GravinaOggi, struttura architettonica](https://www.gravinaoggi.it/_la_struttura_architettonica.html)
* Chiesa del Purgatorio: [FAI, portale](https://fondoambiente.it/luoghi/portale-chiesa-purgatorio), [Wikidata](https://www.wikidata.org/wiki/Q55163985)
* Rioni Piaggio e Fondovico: [Stanze Orsini](https://www.stanzeorsini.it/rioni-piaggio-e-fondovico/), [FAI](https://fondoambiente.it/luoghi/rioni-piaggio-e-fondovico?ldc=)
* Madonna della Stella: [Il Tacco di Bacco](https://iltaccodibacco.it/puglia/guida/7825/)
* San Michele delle Grotte: [Showcaves](https://www.showcaves.com/english/it/caves/SanMicheleGravina.html)
* Geografia generale: [Wikipedia, Gravina in Puglia](https://en.wikipedia.org/wiki/Gravina_in_Puglia)
