# Cosa resta da fare

Stato al 27 settembre 2026, dopo la fase 3 (in revisione). Aggiornare questo file a ogni fase.

## Fatto finora

| Fase | Contenuto | Stato |
|---|---|---|
| 1–2 | Documento di progetto, rete stradale, mezzo, incroci, camera, interfaccia | ✅ |
| 2b | Dati reali: vie, incroci, edifici, torrente, ponte ad archi | ✅ |
| 2c | Vie libere dalle case, archi reali, quattro mezzi, pausa, teletrasporto, versione mobile | ✅ |
| 3 | Cattedrale e Purgatorio sulle fonti, chiese rupestri, rioni a gradoni con scalinate e abitazioni rupestri, altezze, cinque schede nuove, vetrina sulle arcate | ✅ in revisione |

## 1. Subito

- [ ] **Attivare GitHub Pages** (una volta sola): Settings → Pages → Deploy from a branch →
      `main` / `(root)` → Save. Oggi il repository non ha Pages attivo, quindi
      https://giuseppecassano5bit.github.io/gravina-3d/ non risponde ancora.
- [ ] **Provare su un telefono vero** (fps, leggibilità delle schede, tocchi sui cartelli) e
      annotare cosa non va.
- [ ] **Approvare la fase 3** (o chiedere correzioni).

## 2. Decisioni aperte (fase 3, punto 6): dettagli in `docs/DESIGN.md`, "Da decidere insieme"

- [ ] **Percorsi pedonali e scalinate**: restano decorativi, si percorrono col mezzo, oppure
      un tratto **a piedi** con una figurina (consigliato). Con marciapiedi e scalinate la rete
      passa da 157 a 178 tratti (+0,9 km, circa 1 km pedonale).
- [ ] **Allargare il diorama** (oggi 780 × 860 m): subito fuori ci sono il Museo Civico, San
      Domenico, la Pineta comunale; più lontano la Madonna delle Grazie con la facciata a stemma.
- [ ] **Quote reali** dal modello di elevazione Copernicus GLO-30 per tarare ciglio, gradoni e
      discesa dei rioni (oggi disegnati a mano e stilizzati).

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
- [ ] Prestazioni: circa 265 000 triangoli (prima della fase 3 circa 245 000); le draw call
      vanno da 15 a 45 secondo la vista. Misurare su un telefono di fascia media.

**Progetto**
- [ ] I marchi dei mezzi (Fiat, Audi, Lamborghini, John Deere) vanno verificati prima di un uso
      commerciale o promozionale.
