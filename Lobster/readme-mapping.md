# Mapping-Hinweise und -Fragen

Offene Punkte und Entscheidungen zum Lobster-Mapping auf `CatalogueItemNotification_flat.xsd`.

| Nr. | Thema | Status |
|---|---|---|
| 1 | `isReload` aus MSGFN oder INITIAL_LOAD | offen |
| 2 | `gdsnValidEnd`: Datum ohne Uhrzeit, CIN braucht `dateTime` | offen |

## 1. `isReload`: MSGFN oder INITIAL_LOAD?

**Frage:** `isReload` wird im alten Mapping aus der MSGFN gefüllt. Wäre es nicht besser, das Feld INITIAL_LOAD dafür zu benutzen? Soll der Datentyp von INITIAL_LOAD auf boolean umgestellt werden?

**Kontext:**

- Ziel: `catalogueItemNotificationMessage/transaction/documentCommand/catalogueItemNotification/isReload`, **Pflichtfeld**, Datentyp `xsd:boolean` (zulässig: `true`/`false` bzw. `1`/`0`).
- In newPIM ist `initialLoad` in der Entität `newpimlisting` bereits als `boolean` angelegt („Kennzeichen für Erstladung“) und wird im Workflow „newPIM-Listung – CIP senden“ übergeben.

**Entscheidung:** offen

## 2. `gdsnValidEnd`: Datum ohne Uhrzeit

**Frage:** `gdsnValidEnd` enthält nur ein Datum, in der CIN-Nachricht wird hier aber auch eine Uhrzeit benötigt. Im alten Mapping wurde die Uhrzeit per `concat` angefügt. Gesucht ist eine bessere Lösung; eventuell muss die newPIM-Entität angepasst werden.

**Kontext:**

- Datums-/Zeitfelder der CIN sind `xsd:dateTime`, also `JJJJ-MM-TTThh:mm:ss`, optional mit Zeitzone (z. B. `2026-12-31T23:59:59+01:00`). Ein reines Datum (`2026-12-31`) ist ungültig.
- In newPIM (`newpimsdm`) ist `gdsnDaten.gdsnValidEnd` („GDSN gültig bis“) ein `string` **ohne** `format`, während `gdsnDaten.gdsnValidStart` („GDSN gültig ab“) `format: date` hat. In `newpimlisting` gibt es bereits Felder mit `format: date-time`.
- Das CIN-Zielelement von `gdsnValidEnd` ist hier noch nicht dokumentiert (bitte ergänzen).

**Lösungsansätze:**

| Ansatz | Vorteil | Nachteil |
|---|---|---|
| A) Datum in newPIM behalten, in Lobster per Datumsfunktion in `dateTime` umwandeln (feste Uhrzeit, z. B. `23:59:59` für „gültig bis“, `00:00:00` für „gültig ab“, mit Zeitzone) | keine Änderung an Entität und Daten; Datum wird beim Umwandeln geprüft statt blind verkettet | Uhrzeit ist im Mapping fest verdrahtet |
| B) `gdsnValidEnd` auf `format: date-time` umstellen | Uhrzeit kommt direkt aus newPIM, Mapping 1:1 | Bestandsdaten migrieren; Pflege einer Uhrzeit ist fachlich meist nicht nötig |
| C) Zusätzlich: `gdsnValidEnd` mindestens `format: date` geben (wie `gdsnValidStart`) | ungültige Eingaben werden in newPIM abgefangen | ändert allein noch nichts an der Uhrzeit |

Mögliche Empfehlung: **A + C**. Zu klären ist dabei, welche Uhrzeit und Zeitzone der Datenpool für „gültig bis“ erwartet.

**Entscheidung:** offen
