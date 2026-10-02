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

Als Referenz setzt `python3 tools/add_gdsn_namespaces.py <flat.xml> <gdsn.xml>` genau diese Namespaces in einer Nachricht ohne Namespaces. Damit lässt sich eine Lobster-Ausgabe prüfen oder umwandeln.

## Beispielnachricht

`examples/` enthält eine vollständige Beispiel-CIN (fiktive Daten, Präfix 4012345):

| Datei | Inhalt |
|---|---|
| `examples/CIN_Beispiel_flat.xml` | wie Lobster sie gegen die flache XSD erzeugt (ohne Namespaces) |
| `examples/CIN_Beispiel_gdsn.xml` | dieselbe Nachricht GDSN-konform mit Namespaces (erzeugt mit `tools/add_gdsn_namespaces.py`) |

Inhalt: Karton `CASE` (GTIN 14012345000013) mit 6 × Bio-Apfelsaft 1 l `BASE_UNIT_OR_EACH` (GTIN 04012345000016), Zielmarkt Deutschland (276), Texte auf Deutsch. Die Verbrauchereinheit hängt über `catalogueItemChildItemLink` unter dem Karton.

| Ebene | Module |
|---|---|
| Karton | deliveryPurchasingInformation, packagingInformation, tradeItemDescription, tradeItemHierarchy, tradeItemMeasurements |
| Flasche | allergenInformation, foodAndBeverageIngredient, nutritionalInformation, packagingInformation, packagingMarking, placeOfItemActivity, tradeItemDescription, tradeItemLifespan, tradeItemMeasurements |

Die Codewerte (z. B. GPC-Brick, Verpackungs- und Nährstoffcodes) sind nach bestem Wissen gewählt, werden vom Schema aber nicht geprüft (offene Codelisten). Vor produktiver Nutzung gegen die aktuellen GS1-Codelisten und die Validierungsregeln des Datenpools prüfen.

## Weitere Hinweise

- **Reihenfolge der Module:** Im Original ist sie beliebig (`xsd:any`), hier ist sie alphabetisch. Für die Ausgabe ist jede Reihenfolge GDSN-konform.
- **Rekursion:** `catalogueItemChildItemLink/catalogueItem` enthält wieder einen kompletten `tradeItem` (Hierarchie). Das ist schon im Original so.
- **Prüfung:** `python3 tests/check_cin_flat.py` validiert die GS1-Beispiel-CIN ohne Namespaces gegen die flache Datei und prüft, dass sie nach dem Setzen der Namespaces aus `namespaces.csv` wieder gegen das Original-Schema gültig ist. Dasselbe gilt für `examples/CIN_Beispiel_flat.xml`; außerdem prüft der Test, dass `examples/CIN_Beispiel_gdsn.xml` aktuell ist.
