# CIN-Schema für Lobster_data

`CatalogueItemNotification_flat.xsd` ist die GDSN-Nachricht **CatalogueItemNotification 3.1.37** als **eine einzige XSD-Datei**, inkl. **StandardBusinessDocumentHeader** und **aller 76 TradeItem-Module**. Erzeugt mit `python3 tools/build_cin_flat_xsd.py` aus `Schemas/`.

## Was gegenüber den Original-Schemas geändert ist

| Original | Flache Datei |
|---|---|
| ~90 Dateien mit `xsd:import`/`xsd:include`, 80+ Namespaces | eine Datei, **kein** `targetNamespace` |
| `tradeItemInformation/extension` und `componentInformation/extension` = `xsd:any` | `TradeItemModulesExtensionType`: alle 76 Module als optionale Elemente, alphabetisch sortiert |
| `documentCommand/document` (abstrakt, Substitution Group) | konkret `catalogueItemNotification` |
| SBDH `ScopeInformation` (abstrakt, Substitution Group) | `xsd:choice` aus `CorrelationInformation` / `BusinessService` |
| SBDH-Gruppe `ScopeAttributes` | direkt eingesetzt |
| globale Element-Referenzen (`ref=`) | lokale Elemente; einziges globales Element ist `catalogueItemNotificationMessage` |
| `String500Type`/`String5000Type` doppelt (SharedCommon/GdsnCommon) | identisch, daher einmal |
| nicht von der CIN genutzte Typen | entfernt |

Unverändert bleiben Elementnamen, Reihenfolgen, Kardinalitäten, Datentypen, Codelisten und Dokumentation (`xsd:annotation`). Nur `documentReference/extension` (`DocumentReferenceType`) bleibt generisch (`xsd:any`).

## Wichtig für die Ausgabe an den Datenpool: Namespaces

Weil die Datei keinen Namespace hat, erzeugt Lobster die Nachricht zunächst **ohne Namespaces**. Der Datenpool erwartet aber an folgenden Elementen einen Namespace (alle anderen Elemente sind auch im Original **ohne** Namespace):

1. `catalogueItemNotificationMessage` (Root) → `urn:gs1:gdsn:catalogue_item_notification:xsd:3`
2. `StandardBusinessDocumentHeader` **und alle Unterelemente** → `http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader`
3. `catalogueItemNotification` → `urn:gs1:gdsn:catalogue_item_notification:xsd:3`
4. das jeweilige **Modul-Element** unter `extension` (z. B. `nutritionalInformationModule` → `urn:gs1:gdsn:nutritional_information:xsd:3`); die Elemente **innerhalb** eines Moduls sind wieder ohne Namespace

Die vollständige Liste mit üblichem Präfix steht in `namespaces.csv`. Diese Namespaces müssen in Lobster bei der Ausgabe gesetzt werden.

## Weitere Hinweise

- **Reihenfolge der Module:** Im Original ist sie beliebig (`xsd:any`), hier ist sie alphabetisch. Für die Ausgabe ist jede Reihenfolge GDSN-konform.
- **Rekursion:** `catalogueItemChildItemLink/catalogueItem` enthält wieder einen kompletten `tradeItem` (Hierarchie). Das ist schon im Original so.
- **Prüfung:** `python3 tests/check_cin_flat.py` validiert die GS1-Beispiel-CIN ohne Namespaces gegen die flache Datei und prüft, dass sie nach dem Setzen der Namespaces aus `namespaces.csv` wieder gegen das Original-Schema gültig ist.
