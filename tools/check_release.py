#!/usr/bin/env python3
"""Vergleicht ein neues GS1-GDSN-Release-ZIP mit den Schemas im Repo.

Aufruf (aus dem Repo-Root):
    python3 tools/check_release.py <Release.zip>            # nur prüfen, Bericht schreiben
    python3 tools/check_release.py <Release.zip> --apply    # prüfen und Release ins Repo übernehmen

Das ZIP ist das BMS-Paket von GS1 (enthält das *Implementers_Packet*.zip); ein
Implementers Packet direkt geht auch.

Ergebnis: Bericht unter reports/release_check_<alt>_to_<neu>.md mit
- neuen, entfernten und geänderten XSD-Dateien,
- je Datei den geänderten Typen/Elementen inkl. Details
  (Codelisten-Werte, Kind-Elemente, Kardinalitäten, Datentypen),
- der Entscheidung, ob die flache CIN-XSD (Lobster/) neu erzeugt werden muss.
  Maßgeblich sind nur Komponenten, die von der CatalogueItemNotification inkl.
  SBDH und den Modulen aus Lobster/modules.txt (Storck) erreichbar sind.
  Module der Liste, die es im neuen Release nicht mehr gibt, werden als FEHLER
  gemeldet, neue GS1-Module als Hinweis (Kandidaten für die Liste).

Mit --apply werden Schemas/, Instance File/, HTML Sample/, TableOfContents.txt und
docs/ durch das neue Release ersetzt. Ist die CIN betroffen, werden
tools/build_cin_flat_xsd.py und tests/check_cin_flat.py ausgeführt.
"""
import copy
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

from lxml import etree

XS = "http://www.w3.org/2001/XMLSchema"
NS = {"xsd": XS}
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(ROOT_DIR, "Schemas")
CIN_FILE = "gs1/gdsn/CatalogueItemNotification.xsd"
CIN_NS = "urn:gs1:gdsn:catalogue_item_notification:xsd:3"
CIN_ROOTS = ["catalogueItemNotificationMessage", "catalogueItemNotification"]
QNAME_ATTRS = ("type", "base", "itemType", "ref", "substitutionGroup")
SPACE = {"complexType": "type", "simpleType": "type", "element": "element", "attribute": "attribute",
         "group": "group", "attributeGroup": "attributeGroup"}


def local(el):
    return etree.QName(el).localname


def resolve(el, value):
    if ":" in value:
        prefix, name = value.split(":", 1)
        return el.nsmap[prefix], name
    return el.nsmap.get(None), value


def ref_space(el, attr):
    if attr in ("type", "base", "itemType"):
        return "type"
    if attr == "substitutionGroup":
        return "element"
    return SPACE[local(el)]


# ---------------------------------------------------------------- Laden


def extract_release(zip_path, work):
    """Entpackt das Release (auch verschachtelt) und liefert das Paket-Verzeichnis mit Schemas/."""
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(os.path.join(work, "outer"))
    outer = os.path.join(work, "outer")
    if glob.glob(os.path.join(outer, "**", "Schemas"), recursive=True):
        return outer, None
    inner_zips = glob.glob(os.path.join(outer, "**", "*Implementers_Packet*.zip"), recursive=True)
    if len(inner_zips) != 1:
        sys.exit("Kein (eindeutiges) Implementers_Packet*.zip im Release gefunden")
    inner = os.path.join(work, "inner")
    with zipfile.ZipFile(inner_zips[0]) as z:
        z.extractall(inner)
    return inner, outer


def find_schema_dir(pkg):
    dirs = glob.glob(os.path.join(pkg, "**", "Schemas"), recursive=True)
    if len(dirs) != 1:
        sys.exit("Kein (eindeutiger) Schemas-Ordner im Release gefunden")
    return dirs[0]


def load(schema_dir):
    """Liest alle XSDs: files {relpfad: root}, comps {(space, ns, name): (relpfad, element)}."""
    files, comps = {}, {}
    for path in sorted(glob.glob(os.path.join(schema_dir, "**", "*.xsd"), recursive=True)):
        rel = os.path.relpath(path, schema_dir).replace(os.sep, "/")
        root = etree.parse(path).getroot()
        files[rel] = root
        ns = root.get("targetNamespace")
        for c in root:
            if isinstance(c.tag, str) and local(c) in SPACE:
                comps.setdefault((SPACE[local(c)], ns, c.get("name")), (rel, c))
    return files, comps


# ---------------------------------------------------------------- Vergleich


def canonical(el, with_docs):
    """Definition mit aufgelösten QNames; optional ohne Dokumentation."""
    e = copy.deepcopy(el)
    for src, d in zip(el.iter(), e.iter()):
        if not isinstance(d.tag, str):
            continue
        for a in QNAME_ATTRS:
            if d.get(a):
                d.set(a, "{%s}%s" % resolve(src, d.get(a)))
        if d.get("memberTypes"):
            d.set("memberTypes", " ".join("{%s}%s" % resolve(src, v) for v in d.get("memberTypes").split()))
    if not with_docs:
        for d in e.xpath(".//xsd:annotation", namespaces=NS):
            d.getparent().remove(d)
    for d in e.iter():
        if isinstance(d.tag, str) and d.text is not None and not d.text.strip():
            d.text = None
        d.tail = None
    return etree.tostring(e, method="c14n")


def short(qname_value):
    return qname_value.split(":", 1)[-1] if qname_value else qname_value


def signature(el):
    """Vergleichbare Merkmale eines Typs/Elements für die Detailauflistung."""
    sig = {"enum": [], "children": {}, "attrs": {}, "base": None, "type": short(el.get("type"))}
    for d in el.iter():
        if not isinstance(d.tag, str):
            continue
        n = local(d)
        if n == "enumeration":
            sig["enum"].append(d.get("value"))
        elif n in ("restriction", "extension"):
            sig["base"] = sig["base"] or short(d.get("base"))
        elif n in ("minLength", "maxLength", "length", "pattern", "totalDigits", "fractionDigits",
                   "minInclusive", "maxInclusive", "minExclusive", "maxExclusive"):
            sig["attrs"]["facet " + n] = d.get("value")
        elif n == "element" and d is not el:
            key = d.get("name") or short(d.get("ref"))
            sig["children"][key] = "%s [%s..%s]" % (
                short(d.get("type") or d.get("ref")) or "(inline)",
                d.get("minOccurs", "1"),
                {"unbounded": "n"}.get(d.get("maxOccurs", "1"), d.get("maxOccurs", "1")),
            )
        elif n == "attribute":
            sig["attrs"]["@" + d.get("name", short(d.get("ref") or ""))] = "%s (%s)" % (
                short(d.get("type")), d.get("use", "optional"))
    return sig


def details(old, new):
    so, sn = signature(old), signature(new)
    out = []
    if so["type"] != sn["type"]:
        out.append("Typ: `%s` → `%s`" % (so["type"], sn["type"]))
    if so["base"] != sn["base"]:
        out.append("Basistyp: `%s` → `%s`" % (so["base"], sn["base"]))
    added = [v for v in sn["enum"] if v not in so["enum"]]
    removed = [v for v in so["enum"] if v not in sn["enum"]]
    if added:
        out.append("Codewerte neu: " + ", ".join("`%s`" % v for v in added))
    if removed:
        out.append("Codewerte entfernt: " + ", ".join("`%s`" % v for v in removed))
    for k in sn["children"]:
        if k not in so["children"]:
            out.append("Element neu: `%s` %s" % (k, sn["children"][k]))
        elif so["children"][k] != sn["children"][k]:
            out.append("Element geändert: `%s` %s → %s" % (k, so["children"][k], sn["children"][k]))
    for k in so["children"]:
        if k not in sn["children"]:
            out.append("Element entfernt: `%s` %s" % (k, so["children"][k]))
    if list(so["children"]) != list(sn["children"]) and set(so["children"]) == set(sn["children"]):
        out.append("Reihenfolge der Elemente geändert")
    for k in sorted(set(so["attrs"]) | set(sn["attrs"])):
        if so["attrs"].get(k) != sn["attrs"].get(k):
            out.append("%s: `%s` → `%s`" % (k, so["attrs"].get(k), sn["attrs"].get(k)))
    return out or ["Strukturänderung (siehe Diff der Datei)"]


# ---------------------------------------------------------------- CIN-Relevanz


def module_elements(comps, rel):
    """Namen der globalen Elemente einer Modul-Datei."""
    return [k[2] for k, (r, el) in comps.items() if r == rel and k[0] == "element"]


def load_module_list():
    """Module der flachen CIN-XSD aus Lobster/modules.txt"""
    sys.path.insert(0, os.path.join(ROOT_DIR, "tools"))
    from build_cin_flat_xsd import read_module_list
    return read_module_list(os.path.join(ROOT_DIR, "Lobster", "modules.txt"))


def cin_reachable(files, comps, modules=None):
    """Alle Komponenten, die die flache CIN-XSD enthält (CIN + SBDH + alle bzw. die angegebenen Module)."""
    heads = {}
    for (space, ns, name), (rel, el) in comps.items():
        if space == "element" and el.get("substitutionGroup"):
            hns, hname = resolve(el, el.get("substitutionGroup"))
            if hns == ns:  # z. B. SBDH ScopeInformation; gdsn_common:document -> nur die CIN selbst
                heads.setdefault(("element", hns, hname), []).append(("element", ns, name))
    todo = [("element", CIN_NS, n) for n in CIN_ROOTS]
    todo += [k for k, (rel, el) in comps.items() if k[0] == "element" and rel.endswith("Module.xsd")
             and (modules is None or k[2] in modules)]
    seen = set()
    while todo:
        key = todo.pop()
        if key in seen or key not in comps:
            continue
        seen.add(key)
        todo += heads.get(key, [])
        el = comps[key][1]
        for d in el.iter():
            if not isinstance(d.tag, str):
                continue
            for a in QNAME_ATTRS:
                if d.get(a) and a != "substitutionGroup":
                    rns, rname = resolve(d, d.get(a))
                    if rns != XS:
                        todo.append((ref_space(d, a), rns, rname))
            for v in (d.get("memberTypes") or "").split():
                rns, rname = resolve(d, v)
                if rns != XS:
                    todo.append(("type", rns, rname))
    return seen


# ---------------------------------------------------------------- Bericht


def compare(old_dir, new_dir):
    old_files, old_comps = load(old_dir)
    new_files, new_comps = load(new_dir)
    modules = load_module_list()
    reach = cin_reachable(old_files, old_comps, modules) | cin_reachable(new_files, new_comps, modules)
    new_modules = sorted(name for (sp, ns, name), (rel, el) in new_comps.items()
                         if sp == "element" and rel.endswith("Module.xsd"))
    old_v = old_files[CIN_FILE].get("version") if CIN_FILE in old_files else "?"
    new_v = new_files[CIN_FILE].get("version") if CIN_FILE in new_files else "?"

    lines = ["# GDSN-Release-Prüfung %s → %s" % (old_v, new_v), ""]
    cin_reasons, doc_only_cin, hints = [], [], []
    errors = ["Modul `%s` aus Lobster/modules.txt gibt es im neuen Release nicht mehr – Liste anpassen" % m
              for m in modules if m not in new_modules]

    added_files = sorted(set(new_files) - set(old_files))
    removed_files = sorted(set(old_files) - set(new_files))
    for f in added_files:
        if f.endswith("Module.xsd"):
            hints += ["neues GS1-Modul `%s` (nicht in Lobster/modules.txt)" % m for m in module_elements(new_comps, f)]

    per_file = {}
    for key in sorted(set(old_comps) | set(new_comps), key=lambda k: (k[0], k[2])):
        o, n = old_comps.get(key), new_comps.get(key)
        rel = (n or o)[0]
        cin = key in reach
        if o and not n:
            entry = ("entfernt", [], cin)
        elif n and not o:
            entry = ("neu", [], cin)
        elif canonical(o[1], False) != canonical(n[1], False):
            entry = ("geändert", details(o[1], n[1]), cin)
        elif canonical(o[1], True) != canonical(n[1], True):
            entry = ("nur Dokumentation", [], cin)
        else:
            continue
        per_file.setdefault(rel, []).append((key, entry))
        if rel in added_files or rel in removed_files:
            continue  # als neue/entfernte Datei bereits gemeldet
        if cin and entry[0] == "nur Dokumentation":
            doc_only_cin.append(key[2])
        elif cin:
            cin_reasons.append("`%s` %s (%s)" % (key[2], entry[0], rel))

    common = set(old_files) & set(new_files)
    changed_files = [f for f in per_file if f in common]
    unchanged = sorted(f for f in common if f not in per_file)
    version_only = [f for f in unchanged if old_files[f].get("version") != new_files[f].get("version")]

    # Entscheidung
    if errors:
        verdict = "**FEHLER – Lobster/modules.txt anpassen**, danach neu erzeugen"
    elif cin_reasons:
        verdict = "**JA – neue flache CIN-XSD erzeugen** (%d inhaltliche Änderung(en) im CIN-Umfang)" % len(cin_reasons)
    elif doc_only_cin:
        verdict = "**OPTIONAL** – im CIN-Umfang nur Dokumentationsänderungen (%d); die Struktur bleibt gleich" % len(doc_only_cin)
    else:
        verdict = "**NEIN** – keine Änderungen im CIN-Umfang"
    lines += ["## Ergebnis", "",
              "CIN-Umfang: CIN, SBDH und die %d Module aus `Lobster/modules.txt`." % len(modules), "",
              "Neue flache CIN-XSD erforderlich: " + verdict, ""]
    if errors or cin_reasons:
        lines += ["Gründe:", ""] + ["- " + r for r in errors + cin_reasons] + [""]
    if hints:
        lines += ["Hinweise:", ""] + ["- " + h for h in hints] + [""]

    lines += ["## Übersicht", "",
              "| | Anzahl |", "|---|---|",
              "| Neue XSD-Dateien | %d |" % len(added_files),
              "| Entfernte XSD-Dateien | %d |" % len(removed_files),
              "| Geänderte XSD-Dateien | %d |" % len(changed_files),
              "| Unveränderte XSD-Dateien | %d |" % len(unchanged),
              "| davon nur Versionsnummer geändert | %d |" % len(version_only), ""]
    if added_files:
        lines += ["### Neue Dateien", ""] + ["- `%s`" % f for f in added_files] + [""]
    if removed_files:
        lines += ["### Entfernte Dateien", ""] + ["- `%s`" % f for f in removed_files] + [""]

    lines += ["## Änderungen je Datei", "",
              "Spalte *CIN*: ✔ = Teil der flachen CIN-XSD (CIN, SBDH, Module aus Lobster/modules.txt).", ""]
    for rel in sorted(per_file):
        ov = old_files.get(rel, etree.Element("x")).get("version")
        nv = new_files.get(rel, etree.Element("x")).get("version")
        if rel in added_files:
            title = " (neue Datei)"
        elif rel in removed_files:
            title = " (entfernte Datei)"
        else:
            title = " (Version %s → %s)" % (ov, nv) if ov != nv else ""
        lines += ["### `%s`%s" % (rel, title), "",
                  "| Komponente | Art | Änderung | CIN | Details |", "|---|---|---|---|---|"]
        for (space, ns, name), (what, det, cin) in per_file[rel]:
            lines.append("| `%s` | %s | %s | %s | %s |" % (
                name, space, what, "✔" if cin else "", "<br>".join(det)))
        lines.append("")
    if not per_file and not added_files and not removed_files:
        lines += ["Keine inhaltlichen Unterschiede in den XSD-Dateien.", ""]
    return "\n".join(lines), bool(errors or cin_reasons), old_v, new_v


# ---------------------------------------------------------------- Übernahme


def apply_release(pkg, outer):
    """Ersetzt die Release-Inhalte im Repo durch die des neuen Pakets."""
    for name in ("Schemas", "Instance File", "HTML Sample"):
        src = glob.glob(os.path.join(pkg, "**", name), recursive=True)
        dst = os.path.join(ROOT_DIR, name)
        if src:
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src[0], dst)
    toc = glob.glob(os.path.join(pkg, "**", "TableOfContents.txt"), recursive=True)
    if toc:
        shutil.copy(toc[0], os.path.join(ROOT_DIR, "TableOfContents.txt"))
    if outer:
        docs = os.path.join(ROOT_DIR, "docs")
        shutil.rmtree(docs, ignore_errors=True)
        os.makedirs(docs)
        for f in os.listdir(outer):
            p = os.path.join(outer, f)
            if os.path.isfile(p) and not f.lower().endswith(".zip"):
                shutil.copy(p, os.path.join(docs, "TableOfContents_Package.txt" if f == "TableOfContents.txt" else f))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    with tempfile.TemporaryDirectory() as work:
        pkg, outer = extract_release(args[0], work)
        report, cin_affected, old_v, new_v = compare(SCHEMA_DIR, find_schema_dir(pkg))
        os.makedirs(os.path.join(ROOT_DIR, "reports"), exist_ok=True)
        out = os.path.join(ROOT_DIR, "reports", "release_check_%s_to_%s.md" % (old_v, new_v))
        with open(out, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(report.split("## Übersicht")[0].strip())
        print("\nBericht:", os.path.relpath(out, ROOT_DIR))

        if "--apply" in sys.argv:
            apply_release(pkg, outer)
            print("Release %s übernommen (Schemas/, Instance File/, HTML Sample/, TableOfContents.txt, docs/)." % new_v)
            if cin_affected:
                for script in ("tools/build_cin_flat_xsd.py", "tests/check_cin_flat.py"):
                    if subprocess.run([sys.executable, os.path.join(ROOT_DIR, script)]).returncode:
                        sys.exit("\nFEHLER in %s – Release ist übernommen, die flache CIN-XSD muss geprüft werden "
                                 "(bei fehlenden Modulen Lobster/modules.txt anpassen)." % script)
            else:
                print("CIN nicht betroffen – flache CIN-XSD bleibt unverändert.")


if __name__ == "__main__":
    main()
