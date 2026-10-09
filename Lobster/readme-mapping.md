# Mapping-Hinweise und -Fragen

Offene Punkte und Entscheidungen zum Lobster-Mapping auf `CatalogueItemNotification_flat.xsd`.

| Nr. | Thema | Status |
|---|---|---|
| 1 | `isReload` aus MSGFN oder INITIAL_LOAD | offen |
| 2 | Datum ohne Uhrzeit (`gdsnValidEnd`, `tradeItemSynchronisationDates`), CIN braucht `dateTime` | erledigt: Entität in DEV und LIVE umgestellt, Mapping 000-P1 angepasst |
| 3 | `tradeItemUnitDescriptorCode` aus ZZMEE: Ermittlung in die SAP-Schnittstelle verlagern | erledigt: neues Feld in der Entität, Ermittlung im Mapping SAP → newPIM |

## 1. `isReload`: MSGFN oder INITIAL_LOAD?

**Frage:** `isReload` wird im alten Mapping aus der MSGFN gefüllt. Wäre es nicht besser, das Feld INITIAL_LOAD dafür zu benutzen? Soll der Datentyp von INITIAL_LOAD auf boolean umgestellt werden?

**Kontext:**

- Ziel: `catalogueItemNotificationMessage/transaction/documentCommand/catalogueItemNotification/isReload`, **Pflichtfeld**, Datentyp `xsd:boolean` (zulässig: `true`/`false` bzw. `1`/`0`).
- In newPIM ist `initialLoad` in der Entität `newpimlisting` bereits als `boolean` angelegt („Kennzeichen für Erstladung“) und wird im Workflow „newPIM-Listung – CIP senden“ übergeben.

**Entscheidung:** offen

## 2. Datum ohne Uhrzeit: `gdsnValidEnd` und `tradeItemSynchronisationDates`

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

### Ergänzung: auch `tradeItemSynchronisationDates` betroffen

Das Problem mit der fehlenden Uhrzeit tritt in der CIN auch in der Attributgruppe `tradeItem/tradeItemSynchronisationDates` auf. Alle Elemente dort sind `xsd:dateTime`:

| Element | Pflicht |
|---|---|
| `lastChangeDateTime` | ja |
| `cancelledDateTime` | nein |
| `communityVisibilityDateTime` | nein |
| `discontinuedDateTime` | nein |
| `effectiveDateTime` | nein |
| `publicationDateTime` | nein |
| `udidFirstPublicationDateTime` | nein |

**Bevorzugte Lösung (Favorit):** Die Quellfelder in newPIM um die Uhrzeit erweitern, und zwar bereits beim Import aus dem ERP. Die Erweiterung wird im Mapping vom MATMAS-IDoc in die newPIM-Entität eingebaut. Dann liefert newPIM fertige `dateTime`-Werte, und das CIN-Mapping kann 1:1 übernehmen – ohne `concat` in jedem Ausgangsmapping.

Dafür nötig:

1. **newPIM-Entität `newpimsdm`:** Datentyp der betroffenen Datumsfelder auf `format: date-time` umstellen (u. a. `gdsnDaten.gdsnValidEnd`; die Quellfelder für `tradeItemSynchronisationDates` noch zuordnen).
2. **Lobster-Mapping `000-P1-MATMAS-ERP_to_newPIM-SDM`:** die Datumsfelder aus dem MATMAS-IDoc als `dateTime` mit Uhrzeit (und Zeitzone) in die Entität schreiben.

Zu klären:

- Liefert das MATMAS-IDoc zu den Datumsfeldern eine Uhrzeit mit? Falls nicht, wird die Uhrzeit im Mapping `000-P1-MATMAS-ERP_to_newPIM-SDM` festgelegt – dann aber zentral an einer Stelle statt in jedem Ausgangsmapping.
- Welche Uhrzeit und Zeitzone gelten je Feld (z. B. „gültig bis“ = Ende des Tages)?
- Bestandsdaten in newPIM: einmalig migrieren oder per Neuimport aus dem ERP aktualisieren?
- Welche weiteren Mappings lesen die umgestellten Felder und müssen angepasst werden?

**Entscheidung:** Uhrzeit bereits beim MATMAS-Import ergänzen (Favorit umgesetzt, siehe unten).

### Umsetzung (Stand 07.10.2026)

In der newPIM-Entität `newpimsdm`, Gruppe `gdsnDaten`, wurden die drei Felder auf `date-time` umgestellt – **im DEV- und im LIVE-System**:

```json
"gdsnStartDate": {
  "type": "string",
  "format": "date-time"
},
"gdsnValidStart": {
  "type": "string",
  "format": "date-time"
},
"gdsnValidEnd": {
  "type": "string",
  "format": "date-time"
}
```

| Feld | vorher | jetzt |
|---|---|---|
| `gdsnDaten.gdsnStartDate` | `format: date` | `format: date-time` |
| `gdsnDaten.gdsnValidStart` („GDSN gültig ab“) | `format: date` | `format: date-time` |
| `gdsnDaten.gdsnValidEnd` („GDSN gültig bis“) | ohne `format` | `format: date-time` |

- **Mapping `000-P1-MATMAS-ERP_to_newPIM-SDM`:** von Sergej angepasst – die Felder werden jetzt als `dateTime` mit Uhrzeit befüllt.
- Das CIN-Mapping kann die Werte jetzt 1:1 übernehmen; das `concat` im Ausgangsmapping entfällt.
- **Status: erledigt.**
- Das newPIM-Backup-Repo (`entity_configs/newpimsdm.json`) zeigt die neuen Datentypen erst nach dem nächsten Export-Import.

## 3. `tradeItemUnitDescriptorCode`: Ermittlung aus ZZMEE

**Frage:** Der Code wird im alten Mapping durch Abfrage des Quellfeldes ZZMEE im Bereich „Allgemeine Daten“ ausgewertet und so der GDSN-Code ermittelt. Wäre es nicht sinnvoller, diese Ermittlung in der SAP-Schnittstelle zu machen und in der Entität ein neues Feld dafür einzufügen?

**Kontext:**

- Ziel: `tradeItem/tradeItemUnitDescriptorCode` (Hierarchieebene des Artikels). Im Schema optional und als offene Codeliste (`GS1CodeType`) definiert – die XSD prüft die Werte also **nicht**; ungültige Codes fallen erst beim Datenpool auf. In der GDSN-Praxis wird das Feld je Hierarchieebene erwartet (mit dem Datenpool bestätigen).
- GS1-Codewerte: `BASE_UNIT_OR_EACH`, `PACK_OR_INNER_PACK`, `CASE`, `DISPLAY_SHIPPER`, `PALLET`, `MIXED_MODULE`, `TRANSPORT_LOAD`.
- In den newPIM-Entitäten gibt es derzeit kein Feld für den Code und kein Feld ZZMEE.

**Vorschlag (Favorit):** Den GDSN-Code bereits beim Import aus SAP ermitteln und in einem neuen Feld der Entität ablegen (z. B. in `newpimsdm`, Gruppe `gdsnDaten`), als `enum` mit den GS1-Codewerten. Das CIN-Mapping übernimmt den Wert dann 1:1.

| Vorteil | |
|---|---|
| Logik an einer Stelle | Zuordnung ZZMEE → GDSN-Code nicht mehr in jedem Ausgangsmapping |
| Sichtbar und prüfbar | Code ist in newPIM sichtbar und kann dort kontrolliert oder korrigiert werden |
| Gültige Werte | `enum` in der Entität verhindert ungültige Codes, die die XSD nicht abfängt |

Zu klären:

- Wo genau wird ermittelt: direkt in SAP (IDoc liefert den Code mit) oder im Lobster-Mapping `000-P1-MATMAS-ERP_to_newPIM-SDM`?
- Zuordnungstabelle ZZMEE → GDSN-Code aus dem alten Mapping übernehmen und hier dokumentieren.
- Name und Ort des neuen Felds in der Entität; Befüllung der Bestandsdaten.

**Entscheidung:** Ermittlung beim Import, neues Feld in der Entität (Favorit umgesetzt).

### Umsetzung (Stand 09.10.2026)

- Neues Feld `tradeItemUnitDescriptorCode` in der newPIM-Entität.
- Im Mapping von SAP an newPIM wird entschieden, welcher Code in das Feld kommt; die Auswertung von ZZMEE im CIN-Mapping entfällt.
- Das CIN-Mapping übernimmt den Wert 1:1 nach `tradeItem/tradeItemUnitDescriptorCode`.
- Siehe auch `readme-change-log.md`, Eintrag 2.
- **Status: erledigt.**
