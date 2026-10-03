# CIN-Schema für Lobster_data – Profil Storck

`CatalogueItemNotification_flat_storck.xsd` ist die flache CIN-XSD (GDSN 3.1.37, inkl. StandardBusinessDocumentHeader) mit **nur den TradeItem-Modulen, die Storck benötigt**. Aufbau, Namespace-Regeln und Hinweise sind identisch mit der vollständigen Fassung, siehe `../README.md`.

| Datei | Inhalt |
|---|---|
| `modules.txt` | **Modulliste** – ein Modul-Element pro Zeile, Kommentare mit `#`. Quelle für Build und Vollständigkeitsprüfung. |
| `CatalogueItemNotification_flat_storck.xsd` | flache CIN-XSD mit den 28 Modulen der Liste (443 statt 963 Typen) |
| `namespaces.csv` | Elemente, die in der GDSN-Nachricht einen Namespace brauchen (für die Profil-Module) |

Die Module stehen unter `tradeItemInformation/extension` und `componentInformation/extension`, jeweils optional und alphabetisch sortiert.

## Modul hinzufügen oder entfernen

1. `modules.txt` bearbeiten (Namen wie im GDSN-Schema, z. B. `batteryInformationModule`; die vollständige Liste steht in `../namespaces.csv`).
2. XSD neu erzeugen:
   ```
   python3 tools/build_cin_flat_xsd.py --profile Lobster/storck/modules.txt
   ```
   Unbekannte oder doppelte Einträge brechen mit einer Fehlermeldung ab, bei Tippfehlern mit Vorschlag (`unbekannt: allergenInformationModul (gemeint: allergenInformationModule?)`).
3. Prüfen und committen:
   ```
   python3 tests/check_profiles.py
   ```

## Vollständigkeitsprüfung

`python3 tests/check_profiles.py` prüft für jedes Profil `Lobster/<profil>/modules.txt`:

- die Liste enthält nur Module, die es im aktuellen GS1-Release gibt, und keine doppelten,
- die XSD enthält **genau** die Module der Liste (meldet fehlende und überzählige),
- XSD und `namespaces.csv` sind aktuell (passen zur Liste und zu `Schemas/`),
- die GS1-Beispiel-CIN, reduziert auf die Profil-Module, ist gegen die Profil-XSD gültig und mit Namespaces auch gegen das Original-Schema,
- ein nicht gelistetes Modul wird von der Profil-XSD abgelehnt.

## Neues GDSN-Release

`tools/check_release.py` bewertet jedes Profil zusätzlich einzeln (siehe `README.md` im Repo-Root):

- **JA**: Änderungen an Typen, die die Profil-Module (oder CIN/SBDH) nutzen → neu erzeugen
- **OPTIONAL** / **NEIN**: nur Dokumentation bzw. keine Änderung im Profil-Umfang
- **FEHLER**: ein Modul der Liste gibt es im neuen Release nicht mehr → `modules.txt` anpassen
- neue GS1-Module werden als Hinweis gelistet (Kandidaten für die Liste)

Mit `--apply` werden betroffene Profile automatisch neu erzeugt und geprüft.
