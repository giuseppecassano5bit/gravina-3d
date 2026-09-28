# Cosa resta da fare

Stato al 28 settembre 2026: fase 3 approvata e online. Aggiornare questo file a ogni fase.

**Fase 3.4 (Gravina oltre il centro storico) in corso**: piano, dati, budget, rischi e divisione
del lavoro su due chat in [`PIANO_FASE_3_4.md`](PIANO_FASE_3_4.md).

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

### Fase 3.4, blocco C · la città intera (PR #8, in revisione) 🔄

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
- [ ] **Camera della pausa in città**: l'orbita (24 m sopra il mezzo) sfiora o entra nei tetti
      delle palazzine. Correzione di una riga proposta nella PR (sezione 9, chat interfaccia).
- [ ] **Schermata iniziale in orizzontale sul telefono**: il pannello sfora di circa 50 px e la
      riga delle quote Copernicus si vede solo scorrendo (chat interfaccia).
- [ ] Provare la città su un telefono vero (fps, tempo di costruzione, calore).
- [ ] Dopo l'unione: blocco F (strade per il Bosco Difesa Grande e il P.I.P.) e, se c'è margine,
      blocco G (percorsi a piedi e quote reali del centro storico).

### Fase 3.4, blocco F · strade per il Bosco Difesa Grande e il P.I.P. (PR #10, in revisione) 🔄

- [x] Regola del **tracciato reale compresso** in `CLAUDE.md` (eccezione come il Ponte Acquedotto).
- [x] Tre zolle (città, P.I.P., Bosco) in `GEO.meta.zolle`; plinto, riquadri e minimappa per zolla.
- [x] Strada del Bosco: tracciato reale Overture di 5 397 m ridotto a circa 760 m, angoli reali,
      goccia in fondo. Rete: 1 433 tratti, 890 incroci, 86,26 km, 5 gocce.
- [x] Bosco di querce procedurale con radura e rifugio; P.I.P. a scala reale con i capannoni.
- [x] Scheda del Bosco sulle fonti (Wikipedia, SISEF, Overture). P.I.P. e rifugio: solo etichetta.
- [x] Prove: guida fino alla goccia e ritorno con la scheda che si apre; `simula` e `interazioni`
      verdi; budget rispettato (telefono 241 000 triangoli e 53 draw call al massimo, PC 334 000 e
      69; 277 KB compressi).
- [ ] **Rifugio**: se si trovano fonti affidabili, dargli una scheda.
- [ ] Dopo l'unione, se c'è margine: blocco G (percorsi a piedi e quote reali del centro storico).

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

- [ ] **Percorsi pedonali e scalinate**: restano decorativi, si percorrono col mezzo, oppure
      un tratto **a piedi** con una figurina (consigliato). Con marciapiedi e scalinate la rete
      passa da 157 a 178 tratti (+0,9 km, circa 1 km pedonale).
- [x] **Allargare il diorama**: fatto nella fase 3.4, blocco C (la città intera).
- [ ] **Quote reali** dal modello di elevazione Copernicus GLO-30 per tarare ciglio, gradoni e
      discesa dei rioni (oggi disegnati a mano e stilizzati): la città le usa già dal blocco C,
      il centro storico nel blocco G.

## 3. Fase 4 · Rifinitura (dal piano originale)

- [ ] Golden hour: luci, nebbia e ombre nette; un leggero bloom solo se regge i 60 fps.
- [ ] Musica procedurale Web Audio, elegante e mediterranea (pad, arpeggi pizzicati, riverbero
      generato), dissolvenza in entrata, pulsante muto e volume al 40%.
- [ ] Camera: transizioni più cinematografiche e un pulsante per cambiare vista.
- [ ] Prestazioni su telefono: livelli di dettaglio per le finestre, misura su un telefono vero.
- [ ] Interfaccia: restyling con le skill di design, accessibilità, inglese opzionale.
- [ ] Licenza del codice (per esempio MIT) e file `LICENSE`.

## 4. Da sistemare o verificare (emerso finora)

**Fedeltà**
- [ ] Campanile di **San Francesco** (tre ordini, circa 40 m): non modellato perché dai dati non
      si ricava dove sia. Serve una foto o una pianta.
- [ ] Posizione esatta del **campanile della Cattedrale** lungo il fianco sud (oggi nella metà
      verso est, a filo del muro) e del secondo rosone: verificare su foto.
- [ ] **Addolorata**: nessuna fonte affidabile; nei dati c'è anche una "Chiesa dell'Annunziata"
      nello stesso punto. Capire se sono la stessa chiesa.
- [ ] In locale si leggono direttamente Wikipedia, GravinaOggi, Stanze Orsini e Algramà: vale la
      pena rileggere le schede della fase 3 sulle pagine intere (nel cloud erano bloccate).
- [ ] Le **abitazioni rupestri** sono 20, le fonti ne contano circa ottanta.

**Terreno e percorso**
- [ ] Le scalinate reali hanno pochi gradini perché le quote sono stilizzate (si risolve con le
      quote reali, punto 2).
- [ ] Pendenze ripide già presenti prima della fase 3: sentiero ovest verso Botromagno (59%),
      Via giudice Montea lato ovest (29%), Via Fontana la Stella (20%). Guardare come si comporta
      il mezzo e, se serve, smussare di più le quote su quei tratti.

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
