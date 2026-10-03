# Mapping-Hinweise und -Fragen

Offene Punkte und Entscheidungen zum Lobster-Mapping auf `CatalogueItemNotification_flat.xsd`.

| Nr. | Thema | Status |
|---|---|---|
| 1 | `isReload` aus MSGFN oder INITIAL_LOAD | offen |

## 1. `isReload`: MSGFN oder INITIAL_LOAD?

**Frage:** `isReload` wird im alten Mapping aus der MSGFN gefüllt. Wäre es nicht besser, das Feld INITIAL_LOAD dafür zu benutzen? Soll der Datentyp von INITIAL_LOAD auf boolean umgestellt werden?

**Kontext:**

- Ziel: `catalogueItemNotificationMessage/transaction/documentCommand/catalogueItemNotification/isReload`, **Pflichtfeld**, Datentyp `xsd:boolean` (zulässig: `true`/`false` bzw. `1`/`0`).
- In newPIM ist `initialLoad` in der Entität `newpimlisting` bereits als `boolean` angelegt („Kennzeichen für Erstladung“) und wird im Workflow „newPIM-Listung – CIP senden“ übergeben.

**Entscheidung:** offen
