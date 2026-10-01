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
with open(os.path.join(ROOT, "Lobster", "namespaces.csv"), encoding="utf-8") as f:
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
etree.XMLSchema(etree.parse(ORIG)).assertValid(doc)
print("Nach Setzen der Namespaces aus namespaces.csv gegen Original-Schema: gültig")
