#!/usr/bin/env python3
"""Setzt in einer CIN ohne Namespaces (gemäß Lobster/CatalogueItemNotification_flat.xsd)
die GDSN-Namespaces laut Lobster/namespaces.csv, sodass sie gegen die Original-Schemas gültig ist.

Qualifiziert werden: das Root-Element, der StandardBusinessDocumentHeader inkl. aller
Unterelemente, catalogueItemNotification und die Modul-Elemente direkt unter extension.
Alle übrigen Elemente bleiben ohne Namespace (wie im Original-Schema).

Aufruf (aus dem Repo-Root):
    python3 tools/add_gdsn_namespaces.py <eingabe_flat.xml> <ausgabe_gdsn.xml>
"""
import copy
import os
import sys

from lxml import etree

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS_FILE = os.path.join(ROOT_DIR, "Lobster", "namespaces.csv")


def load_namespaces():
    """element -> (praefix, namespace)"""
    with open(NS_FILE, encoding="utf-8") as f:
        rows = [line.rstrip("\n").split(";") for line in f][1:]
    return {r[0]: (r[2], r[3]) for r in rows}


def add_namespaces(doc):
    ns_of = load_namespaces()

    def qualify(el, key=None):
        el.tag = "{%s}%s" % (ns_of[key or el.tag][1], el.tag)

    root = doc.getroot()
    sbdh = [d for el in root.iter("StandardBusinessDocumentHeader") for d in el.iter() if isinstance(d.tag, str)]
    cin = list(root.iter("catalogueItemNotification"))
    modules = [m for ext in root.iter("extension") for m in ext if isinstance(m.tag, str)]
    qualify(root)
    for d in sbdh:
        qualify(d, "StandardBusinessDocumentHeader")
    for el in cin + modules:
        qualify(el)

    # Präfixe aus namespaces.csv am Root deklarieren (nur die tatsächlich verwendeten)
    used = {etree.QName(e).namespace for e in [root] + sbdh + cin + modules}
    nsmap = {p: ns for p, ns in ns_of.values() if ns in used}
    new_root = etree.Element(root.tag, nsmap=nsmap, attrib=root.attrib)
    new_root.text = root.text
    new_root[:] = list(root)
    before = [copy.deepcopy(n) for n in root.itersiblings(preceding=True)]  # z. B. Kommentare
    doc._setroot(new_root)
    for n in reversed(before):
        new_root.addprevious(n)
    return doc


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    doc = etree.parse(sys.argv[1], etree.XMLParser(remove_blank_text=False))
    add_namespaces(doc)
    doc.write(sys.argv[2], xml_declaration=True, encoding="UTF-8")
    print("Geschrieben:", sys.argv[2])


if __name__ == "__main__":
    main()
