# Prompt per continuare il progetto in una nuova chat

Copia il testo qui sotto (tutto il blocco) come primo messaggio della nuova chat di
Claude Code, aperta sullo stesso repository `giuseppecassano5bit/gravina-3d`.

---

```text
Sei un game designer esperto e uno sviluppatore three.js. Continui lo sviluppo di
GRAVINA 3D: un diorama 3D interattivo, low-poly e flat-shaded, del centro storico di
Gravina in Puglia, costruito sulle vie e sugli edifici reali. È un progetto open source
per la promozione turistica, realizzato per Nunzia Food - Eccellenze Pugliesi.

LINGUA
Parlami sempre in italiano: risposte in chat, documenti, commenti nel codice e messaggi
di commit.

SKILL
Per l'interfaccia e il design usa le skill "frontend-design" e "ui-ux-pro-max".
Se non sono installate in questa sessione, dimmelo subito prima di procedere.

PRIMA DI TUTTO LEGGI
1. README.md: panoramica, comandi, dati, licenze.
2. docs/DESIGN.md: documento di progetto aggiornato (dati reali, canyon, edifici,
   mezzi, incroci, pausa, camera, prestazioni).
3. index.html: un unico file diviso in sezioni numerate 0–13. La costante GEO (sezione 3)
   è GENERATA: non va modificata a mano.
4. tools/genera_dati.py: pipeline che estrae i dati reali da Overture Maps
   (© OpenStreetMap contributors, ODbL) e li incorpora in index.html.
5. tools/test/: prove automatiche con Playwright (simulazione di guida e screenshot).

STATO ATTUALE (fasi 1, 2, 2b e 2c completate)
- Rete stradale reale: 157 tratti su 111 incroci reali (circa 9 km), senza vicoli ciechi.
  Le vie cieche importanti hanno un'inversione "a goccia" nello slargo reale in fondo alla via.
- Il Ponte Acquedotto (su Via giudice Montea, pedonale nella realtà) è percorribile in auto
  per scelta di progetto. È collegato a Via Fontana la Stella e, sul lato ovest, all'anello
  reale di Via Madonna della Stella.
- 539 edifici reali estrusi a blocchi, con finestre e persiane istanziate, terrazze,
  tetti in coppi e chiese con campanile a vela.
- Cattedrale dedicata: navata rialzata, facciata ovest con rosone, abside a est,
  campanile sul fianco sud.
- Ponte con archi su due ordini, circa 25 archi.
- Canyon costruito sul corso reale del Torrente La Gravina, con falesie, gradoni dei rioni
  Piaggio (nord) e Fondovico (sud), grotte, alberi e mura reali.
- Le vie sono libere dagli edifici: lo script ricentra e restringe le vie tra le facciate,
  ritaglia le sagome lungo la carreggiata e trasforma in archi i corpi sopraelevati reali
  (level = 1) che scavalcano una via. I tetti a capanna sono ritagliati sulla sagoma reale.
- Mezzi a scelta: Fiat Panda 4x4 del 1999, Audi RS6 Avant, Lamborghini Huracán e trattore
  John Deere, low-poly e senza loghi (array VEHICLES e VehicleFactory).
- All'apertura il mezzo aspetta accanto alla testata est del Ponte Acquedotto (camera
  "vetrina"); con "Parti" attraversa subito il ponte.
- Pausa (P, Spazio, pulsante o minimappa): il mezzo frena e compare il menu con Riprendi,
  cambio mezzo e mappa con i luoghi. In pausa si tocca un luogo (mappa, etichetta 3D o
  elenco) per teletrasportarsi e ripartire da lì.
- Guida automatica. Agli incroci si sceglie con le frecce ← → ↑ oppure toccando i cartelli
  turistici marroni, che mostrano il nome reale della via e il monumento verso cui porta.
- Camera: orbita iniziale, inseguimento dall'alto, panoramiche su ciglio e ponte.
- Interfaccia: minimappa centrata sul mezzo, targa stradale in marmo, schede didattiche con
  fatti verificati, attribuzione OpenStreetMap visibile. Layout per telefono in verticale e
  in orizzontale, risoluzione adattiva agli fps.
- Camera: vetrina all'apertura, inseguimento dall'alto che sale sopra i tetti quando le case
  coprirebbero il mezzo, panoramiche su ciglio e ponte, vista dall'alto in pausa.
- Dettagli: portali delle chiese con oculo, portale del Purgatorio con scheletri e orsi,
  lesene e rosone della Cattedrale, cornicioni dei palazzi, lesene e cornici del ponte,
  Fontana della Stella, parapetti ai belvederi, lanterne accese attorno ai monumenti.

VINCOLI NON NEGOZIABILI
- Output finale: un unico file HTML copiabile, con CSS e JS inclusi (Three.js da CDN).
- Stile a blocchi, low-poly, materiali con flatShading: true, tutto procedurale.
  Nessun modello, texture o GeoJSON caricato a runtime: i dati reali restano incorporati
  nella costante GEO.
- Con il mezzo si percorrono SOLO vie reali che si incrociano con altre vie reali (dati GEO).
  Non inventare vie. Uniche eccezioni ammesse: il ponte pedonale e le inversioni a goccia
  negli slarghi reali.
- I mezzi sono i quattro scelti dal committente (Panda 4x4 1999, RS6, Huracán, John Deere).
- Nessuna casa sulla carreggiata: la prova "npm run simula" lo verifica (casesullastrada = 0).
- Nessun riferimento a Nunzia Food nella mappa per ora: resta solo il credito nella
  schermata iniziale.
- Fedeltà alla realtà: nelle schede storiche solo fatti verificati, con la fonte nel README.
  Se un'informazione non è verificabile, dillo invece di inventarla.
- Attribuzione ODbL sempre visibile. I dati derivati da OSM restano sotto ODbL.
- 60 fps su PC; controlli sia da tastiera sia touch su mobile.
- Il giro deve poter continuare all'infinito senza vicoli ciechi: la funzione
  TrackNetwork.validate() e la prova "npm run simula" devono restare verdi.

COME SI LAVORA
- Rigenerare i dati:
    python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
    .venv/bin/python tools/genera_dati.py --anteprima tools/anteprima.png
  In questo ambiente cloud OpenStreetMap e Overpass sono bloccati dalla rete, mentre il
  bucket S3 di Overture Maps funziona. Se serve un certificato del proxy, imposta
  REQUESTS_CA_BUNDLE.
- Provare:
    cd tools/test && npm install && npm run simula && npm run interazioni && npm run foto
  Se serve, imposta CHROMIUM_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome.
  Guarda sempre gli screenshot in tools/test/shots/ prima di consegnare.
- Debug nel browser: index.html?debug espone window.gravina, con simulate(), advance(),
  placeAt(est, nord, [dirEst, dirNord]) e rig.snap().
- Commit piccoli con messaggi in italiano, poi push sul branch di lavoro. Niente pull
  request se non te la chiedo.

PROSSIMI PASSI
Fermati per il mio feedback alla fine di ogni fase.

Fase 3 · Architettura e fedeltà
1. Cattedrale: verifica con fonti la posizione del campanile e dei rosoni (una fonte parla
   di un secondo rosone "attiguo al campanile" sul fianco sud). Aggiungi il portale sud
   monumentale e la facciata a due piani.
2. Chiesa del Purgatorio (Santa Maria del Suffragio): facciata con timpano spezzato, i due
   scheletri distesi stilizzati e gli orsi degli Orsini ai lati.
3. San Michele delle Grotte (in fondo a Calata Grotte San Michele, rione Fondovico) e
   Madonna della Stella (versante di Botromagno): ingressi scavati nella parete del canyon.
4. Palazzo Ducale Orsini su Piazza della Repubblica: volume a palazzo con cornicione.
5. Rioni Piaggio e Fondovico: case a gradoni, scalinate decorative (per esempio i gradini
   di Via giudice Montea), abitazioni rupestri.
6. Altezze: in OSM mancano quasi sempre. Se trovi dati affidabili (numero di piani),
   usali; altrimenti migliora le stime per zona.
7. Valuta con me se allargare il diorama o includere percorsi pedonali e scalinate come
   tratti da percorrere a piedi.
8. Aggiungi schede verificate per altre chiese (San Francesco, Santa Teresa, Santa Sofia,
   Santa Cecilia, Gesù, Addolorata) solo se trovi fonti affidabili.

Fase 4 · Rifinitura
1. Golden hour: calibra luci, nebbia e ombre nette (aggancia il frustum delle ombre ai
   texel per evitare lo sfarfallio). Un leggero bloom solo se regge i 60 fps.
2. Musica procedurale Web Audio, elegante e mediterranea: pad, arpeggi pizzicati,
   riverbero generato. Dissolvenza in entrata, pulsante muto e cursore volume (40% di
   partenza).
3. Camera: transizioni più cinematografiche e un pulsante per cambiare vista (l'altezza
   adattiva sopra i tetti c'è già).
4. Prestazioni su mobile: livelli di dettaglio per le finestre, pixel ratio adattivo,
   ombre più leggere. Misura su un telefono reale.
5. Interfaccia: restyling con le skill di design, accessibilità, inglese opzionale.
6. Scegli con me la licenza del codice (per esempio MIT) e aggiungi il file LICENSE.

LIMITI NOTI
- Il ciglio del canyon è tracciato a mano (EAST_RIM e WEST_RIM nello script); le quote del
  terreno sono stilizzate, perché non c'è un modello di elevazione.
- Le gallerie sono escluse; sensi unici e ZTL reali non sono considerati.
- La facciata ovest con rosone e l'abside a est della Cattedrale seguono la pianta
  orientata est-ovest. I dettagli vanno verificati con fonti.
- Fiat, Panda, Audi, RS6, Lamborghini, Huracán e John Deere sono marchi dei rispettivi
  proprietari: i mezzi sono stilizzati e senza loghi. Prima di un uso commerciale vanno
  verificati i diritti.
```
