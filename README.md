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
| `tools/`, `tests/` | Skripte zum Erzeugen der flachen XSD, zur Prüfung gegen die Beispiel-CIN und zum Vergleich neuer Releases |
| `reports/` | Prüfberichte neuer Releases (`tools/check_release.py`) |
| `docs/` | BMS-Dokument (PDF), ReadMe und Inhaltsverzeichnis des Gesamtpakets |

Die Ordnerstruktur unter `Schemas/` ist unverändert, damit die relativen `schemaLocation`-Pfade der `xsd:import`/`xsd:include` funktionieren.

Prüfung: `Instance File/CatalogueItemNotification.xml` validiert mit `xmllint` gegen `Schemas/gs1/gdsn/CatalogueItemNotification.xsd`.

## Neues GDSN-Release einspielen

Wenn GS1 ein neues Release der GDSN-Nachrichten (Catalogue Item Sync) veröffentlicht:

1. **Release-ZIP ins Repo legen.** Das BMS-Paket von GS1 (z. B. `BMS_Package_GDSN_Catalogue_Item_Sync_<Monat><Jahr>.zip`) unverändert in den Repo-Root hochladen. Das darin enthaltene `*Implementers_Packet*.zip` muss nicht vorher entpackt werden.
2. **Änderungen prüfen** (ändert noch nichts im Repo):
   ```
   python3 tools/check_release.py <neues-Release>.zip
   ```
   Das Skript entpackt das Release in ein temporäres Verzeichnis, vergleicht jede XSD-Datei mit `Schemas/` und schreibt den Bericht `reports/release_check_<alt>_to_<neu>.md`. Darin stehen:
   - neue, entfernte und geänderte XSD-Dateien (Dateien, bei denen sich nur die Versionsnummer geändert hat, werden nur gezählt),
   - je Datei die geänderten Typen und Elemente mit Details: neue/entfernte Codewerte, neue/entfernte/geänderte Kind-Elemente inkl. Datentyp und Kardinalität, geänderte Basistypen und Facetten (Länge, Pattern …) sowie reine Dokumentationsänderungen,
   - Spalte **CIN** ✔ für alles, was in der flachen CIN-XSD steckt (CIN, SBDH, alle Module); Änderungen an anderen Nachrichten (z. B. CatalogueItemConfirmation) werden gelistet, sind aber für die CIN nicht relevant,
   - die **Entscheidung**, ob eine neue flache CIN-XSD nötig ist:
     - **JA**: inhaltliche Änderung im CIN-Umfang oder ein neues/entferntes Modul. Die Gründe werden aufgelistet.
     - **OPTIONAL**: im CIN-Umfang haben sich nur Dokumentationstexte geändert, die Struktur in Lobster bleibt gleich.
     - **NEIN**: keine Änderung im CIN-Umfang.
3. **Release übernehmen:**
   ```
   python3 tools/check_release.py <neues-Release>.zip --apply
   ```
   Das ersetzt `Schemas/`, `Instance File/`, `HTML Sample/`, `TableOfContents.txt` und `docs/` durch das neue Release. Ist die CIN betroffen, werden automatisch `tools/build_cin_flat_xsd.py` (neue `Lobster/CatalogueItemNotification_flat.xsd` und `Lobster/namespaces.csv`) und `tests/check_cin_flat.py` (Prüfung gegen die neue Beispiel-CIN) ausgeführt.
4. **Committen:** neues Release-ZIP, übernommene Dateien, die neue flache XSD und den Bericht unter `reports/`. Das alte Release-ZIP kann gelöscht werden; es bleibt über die Git-Historie erreichbar.
5. **In Lobster:** Bei **JA** die neue `Lobster/CatalogueItemNotification_flat.xsd` in Lobster_data einlesen und die betroffenen Mappings anhand der CIN-Zeilen im Bericht anpassen.

Voraussetzung: Python 3 mit `lxml` (`pip install lxml`).
