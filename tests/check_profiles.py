#!/usr/bin/env python3
"""Vollständigkeitsprüfung der Modul-Profile (z. B. Lobster/storck/modules.txt).

Für jedes Profil Lobster/<profil>/modules.txt wird geprüft:
1. Die Modulliste ist gültig (nur bekannte Module, keine doppelten Einträge).
2. Die XSD im Profilordner enthält genau die Module der Liste – nicht mehr, nicht weniger.
3. XSD und namespaces.csv sind aktuell (identisch mit einem frischen Build aus Liste und Schemas/).
4. Die GS1-Beispiel-CIN, reduziert auf die Module des Profils, ist gegen die Profil-XSD gültig
   und nach Setzen der Namespaces aus namespaces.csv auch gegen das Original-Schema.
5. Ein Modul, das nicht im Profil steht, wird von der Profil-XSD abgelehnt.

Aufruf (aus dem Repo-Root): python3 tests/check_profiles.py
"""
import copy
import glob
import os
import shutil
import subprocess
import sys
import tempfile

from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_cin_flat_xsd import read_module_list  # noqa: E402

SAMPLE = os.path.join(ROOT, "Instance File", "CatalogueItemNotification.xml")
ORIG = os.path.join(ROOT, "Schemas", "gs1", "gdsn", "CatalogueItemNotification.xsd")
BUILD = os.path.join(ROOT, "tools", "build_cin_flat_xsd.py")
XS = "{http://www.w3.org/2001/XMLSchema}"

orig_schema = etree.XMLSchema(etree.parse(ORIG))


def strip_namespaces(doc):
    for el in doc.iter():
        if isinstance(el.tag, str):
            el.tag = etree.QName(el).localname
    etree.cleanup_namespaces(doc)
    return doc


def add_namespaces(doc, ns_file):
    with open(ns_file, encoding="utf-8") as f:
        ns_of = {line.split(";")[0]: line.strip().split(";")[3] for line in list(f)[1:]}
    root = doc.getroot()
    root.tag = "{%s}%s" % (ns_of[root.tag], root.tag)
    for el in root.iter("StandardBusinessDocumentHeader"):
        for d in el.iter():
            d.tag = "{%s}%s" % (ns_of["StandardBusinessDocumentHeader"], d.tag)
    for el in root.iter("catalogueItemNotification"):
        el.tag = "{%s}%s" % (ns_of[el.tag], el.tag)
    for ext in root.iter("extension"):
        for m in ext:
            m.tag = "{%s}%s" % (ns_of[m.tag], m.tag)
    return doc


def check_profile(list_file):
    pdir = os.path.dirname(list_file)
    name = os.path.basename(pdir)
    xsd_file = os.path.join(pdir, "CatalogueItemNotification_flat_%s.xsd" % name)
    ns_file = os.path.join(pdir, "namespaces.csv")
    print("== Profil %s (%s)" % (name, os.path.relpath(list_file, ROOT)))

    # 1. + 3. Frischer Build in ein temporäres Verzeichnis (bricht bei ungültiger Liste ab)
    with tempfile.TemporaryDirectory() as tmp:
        tdir = os.path.join(tmp, name)
        os.makedirs(tdir)
        shutil.copy(list_file, tdir)
        r = subprocess.run([sys.executable, BUILD, "--profile", os.path.join(tdir, "modules.txt")],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(r.stderr or r.stdout)
        for f in (xsd_file, ns_file):
            fresh = os.path.join(tdir, os.path.basename(f))
            if not os.path.exists(f) or open(f, "rb").read() != open(fresh, "rb").read():
                sys.exit("%s ist nicht aktuell – neu erzeugen mit:\n  python3 tools/build_cin_flat_xsd.py --profile %s"
                         % (os.path.relpath(f, ROOT), os.path.relpath(list_file, ROOT)))
    print("  Liste gültig, XSD und namespaces.csv aktuell")

    # 2. Module in der XSD == Module in der Liste
    wanted = read_module_list(list_file)
    flat = etree.parse(xsd_file)
    (ext_type,) = flat.xpath("//xsd:complexType[@name='TradeItemModulesExtensionType']", namespaces={"xsd": XS[1:-1]})
    order = [e.get("name") for e in ext_type.iter(XS + "element")]
    missing, extra = sorted(set(wanted) - set(order)), sorted(set(order) - set(wanted))
    if missing or extra:
        sys.exit("  Module fehlen in der XSD: %s\n  Module zu viel in der XSD: %s" % (missing, extra))
    print("  XSD enthält genau die %d Module der Liste" % len(order))

    # 4. GS1-Beispiel auf die Profil-Module reduzieren und validieren
    schema = etree.XMLSchema(flat)
    doc = strip_namespaces(etree.parse(SAMPLE))
    removed = []
    for ext in doc.iter("extension"):
        kept = [m for m in ext if m.tag in order]
        removed += [m for m in ext if m.tag not in order]
        ext[:] = sorted(kept, key=lambda m: order.index(m.tag))
    if not schema.validate(doc):
        sys.exit("  GS1-Beispiel ungültig gegen Profil-XSD:\n" + "\n".join(str(e) for e in schema.error_log))
    print("  GS1-Beispiel (ohne %s) gegen Profil-XSD: gültig"
          % (", ".join(sorted({m.tag for m in removed})) or "Entfernungen"))
    orig_schema.assertValid(add_namespaces(copy.deepcopy(doc), ns_file))
    print("  mit Namespaces aus namespaces.csv gegen Original-Schema: gültig")

    # 5. Ein nicht gelistetes Modul muss abgelehnt werden
    if removed:
        ext = next(doc.iter("extension"))
        ext.append(removed[0])
        if schema.validate(doc):
            sys.exit("  Modul %s ist nicht im Profil, wurde aber akzeptiert" % removed[0].tag)
        print("  nicht gelistetes Modul %s wird abgelehnt" % removed[0].tag)


profiles = sorted(glob.glob(os.path.join(ROOT, "Lobster", "*", "modules.txt")))
if not profiles:
    sys.exit("Keine Profile (Lobster/*/modules.txt) gefunden")
for p in profiles:
    check_profile(p)
print("Alle %d Profil(e) in Ordnung" % len(profiles))
