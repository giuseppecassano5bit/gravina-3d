# Gravina 3D

Diorama 3D interattivo in stile low-poly del centro storico di **Gravina in Puglia**.
Progetto open source realizzato per **Nunzia Food, Eccellenze Pugliesi**.

Un'Audi RS Q8 low-poly percorre da sola le vie del centro storico, dalla Cattedrale al
Ponte Acquedotto, lungo il ciglio della gravina. Tu scegli a ogni incrocio quale strada
esplorare. Tutto è generato proceduralmente in **un unico file HTML**, senza modelli,
texture o dati esterni.

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
| 1 | Utilità | matematica, rumore procedurale, eventi |
| 2 | Geografia | conversione da latitudine/longitudine a metri |
| 3 | Dati della mappa | ancore GPS reali, nodi, vie, monumenti |
| 4 | Gravina e terreno | asse del canyon, profilo a gradoni, adattamento alle strade |
| 5 | Rete stradale | spline Catmull-Rom, uscite agli incroci, controlli di integrità |
| 6 | Costruzione del mondo | terreno flat-shaded, strade, piazze, ponte, segnaposti |
| 7 | Audi RS Q8 | veicolo costruito solo da primitive |
| 8 | Conducente | movimento automatico e logica degli incroci |
| 9 | Camera | orbita, inseguimento e panoramiche su gravina e ponte |
| 10–11 | Interfaccia | minimappa, targa stradale, cartelli, schede dei monumenti |
| 12–13 | Scena e avvio | cielo al tramonto, luci, ombre, ciclo principale |

Il documento di progetto completo è in [`docs/DESIGN.md`](docs/DESIGN.md).

### Personalizzare

* **Punto di partenza (vetrina Nunzia Food)**: costante `START` e scheda `nunzia` in `LANDMARKS`.
* **Colore dell'auto**: `CONFIG.car.color`.
* **Velocità e ritmo**: `CONFIG.drive`.
* **Nuove vie**: aggiungi un oggetto in `EDGES` (e, se serve, un nodo in `NODES`). All'avvio `TrackNetwork.validate()` segnala in console eventuali vicoli ciechi o vie che finiscono nel canyon.

### Strumenti per sviluppatori

Aggiungi `?debug` all'indirizzo (per esempio `index.html?debug`) per vedere fps, triangoli e
posizione sulla rete, e per avere in console l'oggetto `window.gravina`. Esempi:

```js
gravina.driver.simulate(1800)   // 30 minuti di guida con scelte casuali: verifica che l'auto non si blocchi mai
gravina.advance(5)              // fa avanzare la simulazione di 5 secondi senza disegnare
```

## Stato del progetto

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ |
| 2 | Base: rete stradale, auto, incroci, camera, interfaccia, terreno con la gravina | ✅ in revisione |
| 3 | Architettura: Ponte Acquedotto ad archi, Cattedrale, chiese rupestri, case in tufo, vetrina Nunzia Food | ⏳ |
| 4 | Rifinitura: luce dorata, ombre, musica procedurale, prestazioni | ⏳ |

## Fonti

Coordinate e notizie storiche provengono da fonti pubbliche, tra cui:

* Ponte Acquedotto: [Wikipedia (EN)](https://en.wikipedia.org/wiki/Ponte_Madonna_della_Stella), [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/il-ponte-acquedotto-settecentesco-orsiniano-della-madonna-della-stella/), [Viaggiamo.it](https://www.viaggiamo.it/ponte-acquedotto-di-gravina-di-puglia-la-storia/)
* Cattedrale: [Wikipedia](https://it.wikipedia.org/wiki/Cattedrale_di_Gravina_in_Puglia), [GCatholic](https://gcatholic.org/churches/italy/1312.htm)
* Chiesa del Purgatorio: [FAI, portale](https://fondoambiente.it/luoghi/portale-chiesa-purgatorio), [Wikidata](https://www.wikidata.org/wiki/Q55163985)
* Madonna della Stella: [Il Tacco di Bacco](https://iltaccodibacco.it/puglia/guida/7825/)
* San Michele delle Grotte: [Showcaves](https://www.showcaves.com/english/it/caves/SanMicheleGravina.html)
* Geografia generale: [Wikipedia, Gravina in Puglia](https://en.wikipedia.org/wiki/Gravina_in_Puglia)

Le ancore GPS sono reali; il tracciato delle vie tra un'ancora e l'altra è stilizzato.
