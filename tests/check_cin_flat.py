#!/usr/bin/env python3
"""Prüft Lobster/CatalogueItemNotification_flat.xsd gegen die GS1-Beispiel-CIN.

Die Beispielnachricht wird ohne Namespaces umgeschrieben (so wie Lobster sie gegen das
flache Schema erzeugt), die Module in /extension in Schema-Reihenfolge sortiert und dann validiert.
Zusätzlich wird die Original-Nachricht gegen das Original-Schema validiert.
Aufruf (aus dem Repo-Root): python3 tests/check_cin_flat.py
"""
import os
import sys

from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "Instance File", "CatalogueItemNotification.xml")
FLAT = os.path.join(ROOT, "Lobster", "CatalogueItemNotification_flat.xsd")
ORIG = os.path.join(ROOT, "Schemas", "gs1", "gdsn", "CatalogueItemNotification.xsd")
XS = "{http://www.w3.org/2001/XMLSchema}"

doc = etree.parse(SAMPLE)
etree.XMLSchema(etree.parse(ORIG)).assertValid(doc)
print("Original-Beispiel gegen Original-Schema: gültig")

for el in doc.iter():
    if isinstance(el.tag, str):
        el.tag = etree.QName(el).localname
etree.cleanup_namespaces(doc)

flat = etree.parse(FLAT)
(ext_type,) = flat.xpath("//xsd:complexType[@name='TradeItemModulesExtensionType']", namespaces={"xsd": XS[1:-1]})
order = [e.get("name") for e in ext_type.iter(XS + "element")]
modules = 0
for ext in doc.iter("extension"):
    children = sorted(ext, key=lambda c: order.index(c.tag))
    modules += len(children)
    ext[:] = children

schema = etree.XMLSchema(flat)
if not schema.validate(doc):
    for e in schema.error_log:
        print(e)
    sys.exit(1)
print("Beispiel ohne Namespaces gegen flaches Schema: gültig (%d Module)" % modules)

# Namespaces laut Lobster/namespaces.csv wieder setzen -> muss gegen das Original-Schema gültig sein
sys.path.insert(0, os.path.join(ROOT, "tools"))
from add_gdsn_namespaces import add_namespaces  # noqa: E402

orig_schema = etree.XMLSchema(etree.parse(ORIG))
orig_schema.assertValid(add_namespaces(doc))
print("Nach Setzen der Namespaces aus namespaces.csv gegen Original-Schema: gültig")

# Beispielnachricht Lobster/examples: flach gültig, mit Namespaces gültig, GDSN-Fassung aktuell
example = os.path.join(ROOT, "Lobster", "examples", "CIN_Beispiel_flat.xml")
example_gdsn = os.path.join(ROOT, "Lobster", "examples", "CIN_Beispiel_gdsn.xml")
ex = etree.parse(example)
schema.assertValid(ex)
gdsn = add_namespaces(ex)
orig_schema.assertValid(gdsn)
if etree.tostring(gdsn, method="c14n") != etree.tostring(etree.parse(example_gdsn), method="c14n"):
    sys.exit("CIN_Beispiel_gdsn.xml ist nicht aktuell: python3 tools/add_gdsn_namespaces.py "
             "Lobster/examples/CIN_Beispiel_flat.xml Lobster/examples/CIN_Beispiel_gdsn.xml")
print("Lobster/examples/CIN_Beispiel_flat.xml: gültig (flach und mit Namespaces gegen Original)")
