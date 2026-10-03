# CIN-Schema für Lobster_data

`CatalogueItemNotification_flat.xsd` ist die GDSN-Nachricht **CatalogueItemNotification 3.1.37** als **eine einzige XSD-Datei**, inkl. **StandardBusinessDocumentHeader** und der **28 TradeItem-Module, die Storck benötigt** (Liste: `modules.txt`). Erzeugt mit `python3 tools/build_cin_flat_xsd.py` aus `Schemas/`.

Die Fassung mit **allen 76 GS1-Modulen** liegt auf dem Branch **`alle-module`**. Sie lässt sich hier jederzeit mit `python3 tools/build_cin_flat_xsd.py --all --out-dir <ordner>` erzeugen.

| Datei | Inhalt |
|---|---|
| `modules.txt` | **Modulliste (Storck)** – ein Modul-Element pro Zeile, Kommentare mit `#`; Grundlage für Build und Vollständigkeitsprüfung |
| `CatalogueItemNotification_flat.xsd` | flache CIN-XSD mit genau diesen Modulen |
| `namespaces.csv` | Elemente, die in der GDSN-Nachricht einen Namespace brauchen |

## Modulliste ändern

1. `modules.txt` bearbeiten. Namen wie im GDSN-Schema, z. B. `batteryInformationModule`; alle verfügbaren Module stehen auf dem Branch `alle-module` in `Lobster/namespaces.csv`.
2. Neu erzeugen: `python3 tools/build_cin_flat_xsd.py` – unbekannte oder doppelte Einträge brechen mit Fehlermeldung ab, bei Tippfehlern mit Vorschlag (`unbekannt: allergenInformationModul (gemeint: allergenInformationModule?)`).
3. Prüfen: `python3 tests/check_cin_flat.py`, dann committen.

## Vollständigkeitsprüfung

`python3 tests/check_cin_flat.py` prüft:

- die Liste enthält nur Module, die es im aktuellen GS1-Release gibt, und keine doppelten,
- XSD und `namespaces.csv` sind aktuell (passen zur Liste und zu `Schemas/`),
- die XSD enthält **genau** die Module der Liste (meldet fehlende und überzählige),
- die GS1-Beispiel-CIN, reduziert auf die gelisteten Module und ohne Namespaces, ist gegen die flache XSD gültig und mit Namespaces aus `namespaces.csv` wieder gegen das Original-Schema,
- ein nicht gelistetes Modul wird von der flachen XSD abgelehnt.

## Was gegenüber den Original-Schemas geändert ist

| Original | Flache Datei |
|---|---|
| ~90 Dateien mit `xsd:import`/`xsd:include`, 80+ Namespaces | eine Datei, **kein** `targetNamespace` |
| `tradeItemInformation/extension` und `componentInformation/extension` = `xsd:any` | `TradeItemModulesExtensionType`: die Module aus `modules.txt` als optionale Elemente, alphabetisch sortiert; andere Module sind nicht erlaubt |
| `documentCommand/document` (abstrakt, Substitution Group) | konkret `catalogueItemNotification` |
| SBDH `ScopeInformation` (abstrakt, Substitution Group) | `xsd:choice` aus `CorrelationInformation` / `BusinessService` |
| SBDH-Gruppe `ScopeAttributes` | direkt eingesetzt |
| globale Element-Referenzen (`ref=`) | lokale Elemente; einziges globales Element ist `catalogueItemNotificationMessage` |
| `String500Type`/`String5000Type` doppelt (SharedCommon/GdsnCommon) | identisch, daher einmal |
| nicht genutzte Typen (andere Nachrichten, nicht gelistete Module) | entfernt (443 statt 963 Typen) |

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
- **Nicht gelistete Module:** Liefert ein Datenpool ein Modul, das nicht in `modules.txt` steht, ist die Nachricht gegen diese XSD ungültig. Dann das Modul in die Liste aufnehmen und neu erzeugen.
