# Gravina 3D

Diorama 3D interattivo in stile low-poly del centro storico di **Gravina in Puglia**,
costruito sulle **vie, gli edifici e il torrente reali**.
Progetto open source di **Giuseppe Cassano** ([github.com/giuseppecassano5bit](https://github.com/giuseppecassano5bit)).

Appena si apre, il mezzo aspetta accanto al **Ponte Acquedotto**. Scegli con che cosa
girare: **Fiat Panda 4x4 del 1999**, **Audi RS6 Avant**, **Lamborghini Huracán** o
**trattore John Deere**. Poi il mezzo percorre da solo le vie reali del centro storico, e a
ogni incrocio reale scegli tu quale via prendere. Puoi fermarti quando vuoi: dal menu di
pausa cambi mezzo oppure tocchi un luogo sulla mappa e ti teletrasporti lì.
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
* [`docs/PROMPT_NUOVA_CHAT.md`](docs/PROMPT_NUOVA_CHAT.md): il prompt da incollare nella nuova chat;
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

Il mezzo avanza da solo. Se non scegli, agli incroci prosegue sulla via più dritta.
Il menu di pausa compare solo a mezzo fermo; se cambi app o scheda il viaggio va in pausa da
solo. Il browser ricorda l'ultimo mezzo scelto.

### I mezzi

| Mezzo | Carattere nel diorama |
|---|---|
| Fiat Panda 4x4 (1999) | rossa, squadrata, con protezioni in plastica e barre sul tetto; passo tranquillo |
| Audi RS6 Avant | familiare grigia con passaruota bombati e pinze rosse; brillante |
| Lamborghini Huracán | arancione, a cuneo, con i fari a Y; la più svelta (sempre a passo da centro storico) |
| Trattore John Deere | verde e giallo, ruote tassellate e sbuffi di fumo; il più lento, e la camera sale un po' |

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
| 6d | Dettagli | portali delle chiese, portale del Purgatorio, palazzi, Fontana della Stella, scalinate, belvederi, lanterne |
| 7 | Mezzi | Panda 4x4, RS6, Huracán e trattore, costruiti solo da primitive |
| 8 | Conducente | movimento automatico, incroci, pausa con frenata |
| 9 | Camera | vetrina a due tempi (primo piano e campo lungo sulle arcate), inseguimento che scavalca i tetti nei vicoli, panoramiche, vista dall'alto in pausa |
| 10–11 | Interfaccia | minimappa, mappa della pausa, scelta del mezzo, targa, cartelli, schede, teletrasporto |
| 12–13 | Scena e avvio | cielo al tramonto, luci, ombre agganciate ai texel, qualità adattiva, ciclo principale |

Il documento di progetto completo è in [`docs/DESIGN.md`](docs/DESIGN.md); cosa resta da fare
è in [`docs/DA_FARE.md`](docs/DA_FARE.md).

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
gravina.useVehicle('deere')            // cambia mezzo: panda, rs6, huracan, deere
gravina.pause(); gravina.goTo('duomo') // pausa e teletrasporto verso un monumento (id di LANDMARKS)
```

Prove automatiche con Playwright: vedi [`tools/test/README.md`](tools/test/README.md).

## Stato del progetto

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | Documento di progetto | ✅ |
| 2 | Base: rete stradale, auto, incroci, camera, interfaccia | ✅ |
| 2b | Dati reali: vie e incroci reali, edifici, torrente e cigli, ponte ad archi | ✅ |
| 2c | Vie libere dagli edifici e archi reali; quattro mezzi a scelta; partenza dal ponte; pausa con cambio mezzo, mappa e teletrasporto; camera che scavalca i tetti; dettagli dei monumenti; versione mobile | ✅ |
| 3 | Architettura e fedeltà: Cattedrale e Purgatorio sulle fonti, chiese rupestri scavate, rioni a gradoni con scalinate e abitazioni rupestri, altezze per zona, schede di altre cinque chiese, vetrina sulle arcate | ✅ in revisione |
| 4 | Rifinitura: musica procedurale, transizioni di camera, prove su telefoni reali | ⏳ |

## Crediti, licenze e marchi

* **Autore**: Giuseppe Cassano ([github.com/giuseppecassano5bit](https://github.com/giuseppecassano5bit)).

* **Dati cartografici** (blocco `GEO` in `index.html`): © OpenStreetMap contributors, disponibili
  sotto [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/). Sono un
  database derivato e restano sotto ODbL; l'attribuzione è visibile nella pagina.
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
* Cattedrale: [Wikipedia](https://it.wikipedia.org/wiki/Concattedrale_di_Santa_Maria_Assunta_(Gravina_in_Puglia)), [Wikipedia (EN)](https://en.wikipedia.org/wiki/Gravina_Cathedral), [Carta dei Beni Culturali della Regione Puglia](https://www.cartapulia.it/en/esplora-la-carta/-/rcp/ricercaCartapulia_INSTANCE_1yi8w0oVRO9u/dettaglio/5990) (orientamento, facciata tripartita con tre portali e rosone a 24 raggi, campanile sul profilo sud, cappellone), [Museo Capitolare, campanile](https://www.museocapitolaregravina.it/campanile-cattedrale/) (quattro ordini, cipollone del 1698), [Visit Puglia](https://www.visit-puglia.it/at/11/luogosacro/786/it/Cattedrale-di-Santa-Maria-Assunta-Gravina-in-Puglia-(Bari)) (portale sud e secondo rosone attiguo al campanile), [Catalogo generale dei Beni Culturali](https://catalogo.beniculturali.it/detail/ArchitecturalOrLandscapeHeritage/1600180859), [GCatholic](https://gcatholic.org/churches/italy/1312.htm), [GravinaOggi, struttura architettonica](https://www.gravinaoggi.it/_la_struttura_architettonica.html)
* Chiesa del Purgatorio: [FAI, portale](https://fondoambiente.it/luoghi/portale-chiesa-purgatorio) (pilastri a torri sovrapposte sugli orsi, timpano spezzato con gli scheletri, stemma ed epigrafe), [Wikipedia](https://it.wikipedia.org/wiki/Chiesa_di_Santa_Maria_del_Suffragio_(Gravina_in_Puglia)), [GravinaOggi](https://www.gravinaoggi.it/chiesa-ducale-santa-maria-del-suffragio--o-purgatorio-.html), [Wikidata](https://www.wikidata.org/wiki/Q55163985)
* Rioni Piaggio e Fondovico: [Stanze Orsini](https://www.stanzeorsini.it/rioni-piaggio-e-fondovico/), [FAI](https://fondoambiente.it/luoghi/rioni-piaggio-e-fondovico?ldc=), [GravinaOggi](https://www.gravinaoggi.it/i-rioni-storici-piaggio-e-fondovito-a-gravina.html) (scalinate di tufo, circa ottanta ambienti scavati)
* Madonna della Stella: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/santuario-rupestre-madonna-della-stella/) (esterno imbiancato, campanile a vela in mattoni, corpo basso a una falda), [Museo Capitolare](https://www.museocapitolaregravina.it/madonna-della-stella/), [Il Tacco di Bacco](https://iltaccodibacco.it/puglia/guida/7825/)
* San Michele delle Grotte: [Museo Capitolare](https://www.museocapitolaregravina.it/san-michele-delle-grotte/), [Wikipedia](https://it.wikipedia.org/wiki/Chiesa_rupestre_di_San_Michele), [Showcaves](https://www.showcaves.com/english/it/caves/SanMicheleGravina.html)
* San Francesco: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/la-monumentale-chiesa-di-san-francesco-nella-sua-evoluzione-storica/), [GravinaOggi, il campanile](https://www.gravinaoggi.it/il_campanile_di_san_francesco.html)
* Santa Sofia: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/gravina-santa-sofia-tomba-di-angela-castriota-skanderbeg/), [Columbia University, Spanish Italy and the Iberian Americas](https://siia.mcah.columbia.edu/object/tomb-angela-castriota-skanderbeg-s-sofia-gravina)
* Santa Cecilia: [GravinaLife](https://www.gravinalife.it/rubriche/passeggiando-con-la-storia-1/chiesa-santa-cecilia-nel-centro-storico/), [GravinaOggi](https://www.gravinaoggi.it/chiesa-di-santa-cecilia.html)
* Santa Teresa: [GravinaOggi, il monastero](https://www.gravinaoggi.it/monastero-di-santa-teresa-a-gravina-in-puglia.html), [GravinaOggi, il SS. Nome di Gesù](https://www.gravinaoggi.it/la_chiesa_del_ss_nome_di_gesu.html) (l'antica parrocchia di San Matteo)
* Chiesa del Gesù: [GravinaOggi](https://www.gravinaoggi.it/la_chiesa_del_ss_nome_di_gesu.html), [Carta dei Beni Culturali della Regione Puglia](https://cartapulia.it/dettaglio?id=127705)
* Addolorata: nessuna fonte affidabile trovata (nei dati il punto d'interesse vicino si chiama "Chiesa dell'Annunziata"), quindi solo l'etichetta
* Geografia generale: [Wikipedia, Gravina in Puglia](https://en.wikipedia.org/wiki/Gravina_in_Puglia)
