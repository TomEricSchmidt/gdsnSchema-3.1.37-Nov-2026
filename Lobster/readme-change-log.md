# Change-Log Lobster-Mapping

Änderungen an newPIM-Entität und Mappings, die das CIN-Mapping auf `CatalogueItemNotification_flat.xsd` betreffen. Neueste Einträge oben ergänzen.

| Nr. | Änderung | Bereich | Stand |
|---|---|---|---|
| 1 | Datentyp `date` → `date-time` für GDSN Startdatum, GDSN gültig ab, GDSN gültig bis | Entität `newpimsdm`, Mapping SAP → newPIM | umgesetzt (07.10.2026) |
| 2 | Neues Feld `tradeItemUnitDescriptorCode` | Entität `newpimsdm`, Mapping SAP → newPIM | umgesetzt (09.10.2026) |
| 3 | `tradeItemContactInformation`: Inverkehrbringer immer aus `CONTACT_AD`; `tradeItemContact-gln#7` nicht mehr gefüllt | CIN-Mapping | umgesetzt (09.10.2026) |

## 1. Datentyp von `date` auf `date-time` umgestellt

Betroffene Felder in der Entität `newpimsdm`, Gruppe `gdsnDaten` (DEV- und LIVE-System):

| Feld | Bezeichnung | vorher | jetzt |
|---|---|---|---|
| `gdsnStartDate` | GDSN Startdatum | `format: date` | `format: date-time` |
| `gdsnValidStart` | GDSN gültig ab | `format: date` | `format: date-time` |
| `gdsnValidEnd` | GDSN gültig bis | ohne `format` | `format: date-time` |

- Im Mapping von SAP an newPIM (`000-P1-MATMAS-ERP_to_newPIM-SDM`) wird die Uhrzeit fix angehängt.
- Das CIN-Mapping übernimmt die Werte 1:1 als `xsd:dateTime`; das bisherige `concat` entfällt.
- Hintergrund: `readme-mapping.md`, Punkt 2.

## 2. Neues Feld `tradeItemUnitDescriptorCode`

- Neues Feld in der newPIM-Entität für den GDSN-Code der Hierarchieebene (`BASE_UNIT_OR_EACH`, `CASE`, `PALLET` …).
- Im Mapping von SAP an newPIM wird entschieden, welcher Code in das Feld kommt (bisher im CIN-Mapping aus ZZMEE ermittelt).
- Das CIN-Mapping übernimmt den Wert 1:1 nach `tradeItem/tradeItemUnitDescriptorCode`.
- Hintergrund: `readme-mapping.md`, Punkt 3.

## 3. `tradeItemContactInformation`: Inverkehrbringer

- Für den Inverkehrbringer wird jetzt immer der Kontakt mit `ISPECFLD-2 = CONTACT_AD` verwendet.
- Das Feld `tradeItemContact-gln#7` wird nicht mehr gefüllt.
- Ziel in der CIN: `tradeItem/tradeItemContactInformation`.
