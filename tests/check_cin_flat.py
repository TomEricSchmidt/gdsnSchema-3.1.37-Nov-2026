#!/usr/bin/env python3
"""Prüft Lobster/CatalogueItemNotification_flat.xsd inkl. Vollständigkeit gegen Lobster/modules.txt.

1. Die Modulliste ist gültig (nur bekannte Module, keine doppelten Einträge).
2. XSD und namespaces.csv sind aktuell (identisch mit einem frischen Build aus Liste und Schemas/).
3. Die XSD enthält genau die Module der Liste – nicht mehr, nicht weniger.
4. Die GS1-Beispiel-CIN ist gegen das Original-Schema gültig; reduziert auf die gelisteten
   Module und ohne Namespaces (so wie Lobster sie erzeugt) gegen die flache XSD; und nach
   Setzen der Namespaces aus namespaces.csv wieder gegen das Original-Schema.
5. Ein Modul, das nicht in der Liste steht, wird von der flachen XSD abgelehnt.

Aufruf (aus dem Repo-Root): python3 tests/check_cin_flat.py
"""
import copy
import os
import subprocess
import sys
import tempfile

from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_cin_flat_xsd import read_module_list  # noqa: E402

SAMPLE = os.path.join(ROOT, "Instance File", "CatalogueItemNotification.xml")
ORIG = os.path.join(ROOT, "Schemas", "gs1", "gdsn", "CatalogueItemNotification.xsd")
LOBSTER = os.path.join(ROOT, "Lobster")
MODULE_LIST = os.path.join(LOBSTER, "modules.txt")
FLAT = os.path.join(LOBSTER, "CatalogueItemNotification_flat.xsd")
NS_FILE = os.path.join(LOBSTER, "namespaces.csv")
BUILD = os.path.join(ROOT, "tools", "build_cin_flat_xsd.py")
XS = "{http://www.w3.org/2001/XMLSchema}"


def fail(msg):
    sys.exit("FEHLER: " + msg)


# 1. + 2. Frischer Build in ein temporäres Verzeichnis (bricht bei ungültiger Liste ab)
with tempfile.TemporaryDirectory() as tmp:
    r = subprocess.run([sys.executable, BUILD, "--modules", MODULE_LIST, "--out-dir", tmp], capture_output=True, text=True)
    if r.returncode:
        fail(r.stderr or r.stdout)
    for f in (FLAT, NS_FILE):
        if open(f, "rb").read() != open(os.path.join(tmp, os.path.basename(f)), "rb").read():
            fail("%s ist nicht aktuell – neu erzeugen mit: python3 tools/build_cin_flat_xsd.py" % os.path.relpath(f, ROOT))
print("Modulliste gültig, XSD und namespaces.csv aktuell")

# 3. Module in der XSD == Module in der Liste
wanted = read_module_list(MODULE_LIST)
flat = etree.parse(FLAT)
(ext_type,) = flat.xpath("//xsd:complexType[@name='TradeItemModulesExtensionType']", namespaces={"xsd": XS[1:-1]})
order = [e.get("name") for e in ext_type.iter(XS + "element")]
missing, extra = sorted(set(wanted) - set(order)), sorted(set(order) - set(wanted))
if missing or extra:
    fail("Module fehlen in der XSD: %s / Module zu viel in der XSD: %s" % (missing, extra))
print("XSD enthält genau die %d Module aus Lobster/modules.txt" % len(order))

# 4. GS1-Beispiel: Original gültig, dann ohne Namespaces und auf die Liste reduziert gegen die flache XSD
orig_schema = etree.XMLSchema(etree.parse(ORIG))
doc = etree.parse(SAMPLE)
orig_schema.assertValid(doc)
print("Original-Beispiel gegen Original-Schema: gültig")

for el in doc.iter():
    if isinstance(el.tag, str):
        el.tag = etree.QName(el).localname
etree.cleanup_namespaces(doc)
removed = []
for ext in doc.iter("extension"):
    removed += [m for m in ext if m.tag not in order]
    ext[:] = sorted((m for m in ext if m.tag in order), key=lambda m: order.index(m.tag))

schema = etree.XMLSchema(flat)
if not schema.validate(doc):
    fail("Beispiel ungültig gegen flache XSD:\n" + "\n".join(str(e) for e in schema.error_log))
print("Beispiel ohne Namespaces gegen flache XSD: gültig%s"
      % (" (nicht gelistete Module entfernt: %s)" % ", ".join(sorted({m.tag for m in removed})) if removed else ""))

with open(NS_FILE, encoding="utf-8") as f:
    ns_of = {line.split(";")[0]: line.strip().split(";")[3] for line in list(f)[1:]}
gdsn = copy.deepcopy(doc)
root = gdsn.getroot()
root.tag = "{%s}%s" % (ns_of[root.tag], root.tag)
for el in root.iter("StandardBusinessDocumentHeader"):
    for d in el.iter():
        d.tag = "{%s}%s" % (ns_of["StandardBusinessDocumentHeader"], d.tag)
for el in root.iter("catalogueItemNotification"):
    el.tag = "{%s}%s" % (ns_of[el.tag], el.tag)
for ext in root.iter("extension"):
    for m in ext:
        m.tag = "{%s}%s" % (ns_of[m.tag], m.tag)
orig_schema.assertValid(gdsn)
print("Nach Setzen der Namespaces aus namespaces.csv gegen Original-Schema: gültig")

# 5. Ein nicht gelistetes Modul muss abgelehnt werden
if removed:
    next(doc.iter("extension")).append(removed[0])
    if schema.validate(doc):
        fail("Modul %s steht nicht in der Liste, wurde aber akzeptiert" % removed[0].tag)
    print("Nicht gelistetes Modul %s wird abgelehnt" % removed[0].tag)
