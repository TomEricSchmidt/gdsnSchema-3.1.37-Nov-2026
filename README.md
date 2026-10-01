# GS1 GDSN Schemas 3.1.37 – Catalogue Item Sync

Entpackter Inhalt von `BMS_Package_GDSN_Catalogue_Item_Sync_July2026.zip` (Original liegt weiterhin im Repo-Root).

| Ordner/Datei | Inhalt |
|---|---|
| `Schemas/gs1/gdsn/` | GDSN-Nachrichten-XSDs (u. a. `CatalogueItemNotification.xsd`), `TradeItem.xsd`, `GdsnCommon.xsd` und alle TradeItem-Module |
| `Schemas/gs1/shared/` | `SharedCommon.xsd` |
| `Schemas/sbdh/` | Standard Business Document Header (SBDH) |
| `Instance File/` | Beispiel-XML-Instanzen je Nachricht |
| `HTML Sample/` | HTML-Darstellung der Beispiel-Instanzen |
| `TableOfContents.txt` | Inhaltsverzeichnis des Implementers Packet (inkl. Schema-Versionen) |
| `Lobster/` | **CIN als eine XSD-Datei für Lobster_data** inkl. SBDH und aller Module, siehe `Lobster/README.md` |
| `tools/`, `tests/` | Skript zum Erzeugen der flachen XSD und Prüfung gegen die Beispiel-CIN |
| `docs/` | BMS-Dokument (PDF), ReadMe und Inhaltsverzeichnis des Gesamtpakets |

Die Ordnerstruktur unter `Schemas/` ist unverändert, damit die relativen `schemaLocation`-Pfade der `xsd:import`/`xsd:include` funktionieren.

Prüfung: `Instance File/CatalogueItemNotification.xml` validiert mit `xmllint` gegen `Schemas/gs1/gdsn/CatalogueItemNotification.xsd`.
