#!/usr/bin/env python3
"""Baut aus den GS1-GDSN-Schemas eine einzige XSD für die CatalogueItemNotification (CIN).

Ergebnis: Lobster/CatalogueItemNotification_flat.xsd und Lobster/namespaces.csv
mit den TradeItem-Modulen aus der Modulliste Lobster/modules.txt (Storck).
Die Fassung mit allen GS1-Modulen liegt auf dem Branch "alle-module".

- Alle import/include (SBDH, SharedCommon, GdsnCommon, TradeItem, alle *Module.xsd)
  werden in eine Datei ohne targetNamespace aufgelöst.
- Die Substitution Group gdsn_common:document wird durch das konkrete
  Element catalogueItemNotification ersetzt.
- Das generische xsd:any in tradeItemInformation/extension und
  componentInformation/extension wird durch die TradeItem-Module ersetzt
  (TradeItemModulesExtensionType, jedes Modul optional, alphabetisch);
  übernommen werden nur die Module der Modulliste (mit --all alle).
- Alle Element-Referenzen werden zu lokalen Elementen aufgelöst, sodass
  catalogueItemNotificationMessage das einzige globale Element ist.
- Nicht erreichbare Typen werden entfernt.
- Gleichnamige Typen aus unterschiedlichen Namespaces werden, falls sie sich
  unterscheiden, mit Präfix umbenannt; identische werden zusammengeführt.

Aufruf (aus dem Repo-Root):
    python3 tools/build_cin_flat_xsd.py                       # Module aus Lobster/modules.txt
    python3 tools/build_cin_flat_xsd.py --modules <liste> --out-dir <ordner>
    python3 tools/build_cin_flat_xsd.py --all --out-dir <ordner>   # alle GS1-Module

Modulliste: ein Modul-Element pro Zeile (z. B. allergenInformationModule),
Leerzeilen und Kommentare (#) werden ignoriert. Unbekannte oder doppelte
Einträge brechen den Build mit Fehlermeldung ab.
"""
import argparse
import difflib
import copy
import glob
import os
import sys

from lxml import etree

XS = "http://www.w3.org/2001/XMLSchema"
NS = {"xsd": XS}
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(ROOT_DIR, "Schemas")
LOBSTER_DIR = os.path.join(ROOT_DIR, "Lobster")
MODULE_LIST = os.path.join(LOBSTER_DIR, "modules.txt")
OUT_NAME = "CatalogueItemNotification_flat.xsd"
NS_NAME = "namespaces.csv"
SBDH_NS = "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader"

CIN_NS = "urn:gs1:gdsn:catalogue_item_notification:xsd:3"
GDSN_COMMON_NS = "urn:gs1:gdsn:gdsn_common:xsd:3"
SHARED_NS = "urn:gs1:shared:shared_common:xsd:3"
TRADE_ITEM_NS = "urn:gs1:gdsn:trade_item:xsd:3"

ROOT_ELEMENT = "catalogueItemNotificationMessage"
MODULE_EXT_TYPE = "TradeItemModulesExtensionType"
# complexTypes, deren <extension> die TradeItem-Module aufnimmt
MODULE_EXT_OWNERS = {(TRADE_ITEM_NS, "TradeItemInformationType"), (TRADE_ITEM_NS, "ComponentInformationType")}

QNAME_ATTRS = {"type": "type", "base": "type", "itemType": "type", "ref": None, "substitutionGroup": "element"}
COMPONENT_SPACE = {
    "complexType": "type",
    "simpleType": "type",
    "element": "element",
    "attribute": "attribute",
    "group": "group",
    "attributeGroup": "attributeGroup",
}


def local(el):
    return etree.QName(el).localname


def resolve_qname(el, value):
    """QName-String im Kontext von el -> (namespace, localname); ohne Präfix gilt der Default-Namespace (SBDH)."""
    if ":" in value:
        prefix, name = value.split(":", 1)
        return el.nsmap[prefix], name
    return el.nsmap.get(None), value


def ref_space(el, attr):
    """Symbol-Space, auf den ein QName-Attribut verweist."""
    if attr != "ref":
        return QNAME_ATTRS[attr]
    return {"element": "element", "attribute": "attribute", "group": "group", "attributeGroup": "attributeGroup"}[local(el)]


def schema_files():
    files = [
        "gs1/gdsn/CatalogueItemNotification.xsd",
        "gs1/gdsn/GdsnCommon.xsd",
        "gs1/shared/SharedCommon.xsd",
        "gs1/gdsn/TradeItem.xsd",
    ]
    files += sorted(os.path.relpath(f, SCHEMA_DIR) for f in glob.glob(os.path.join(SCHEMA_DIR, "sbdh", "*.xsd")))
    modules = sorted(os.path.relpath(f, SCHEMA_DIR) for f in glob.glob(os.path.join(SCHEMA_DIR, "gs1", "gdsn", "*Module.xsd")))
    return files + modules, modules


def read_module_list(path):
    """Modulliste lesen: ein Element-Name pro Zeile, # leitet Kommentare ein."""
    names = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            name = line.split("#", 1)[0].strip()
            if name:
                names.append(name)
    return names


def check_module_list(names, available, path):
    """Abbruch bei unbekannten oder doppelten Modulen, mit Vorschlägen."""
    errors = []
    for name in sorted({n for n in names if names.count(n) > 1}):
        errors.append("doppelt: %s" % name)
    for name in names:
        if name not in available:
            hint = difflib.get_close_matches(name, available, n=1)
            errors.append("unbekannt: %s%s" % (name, " (gemeint: %s?)" % hint[0] if hint else ""))
    if errors:
        sys.exit("Modulliste %s ist fehlerhaft:\n  " % path + "\n  ".join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--modules", default=MODULE_LIST, help="Modulliste (Standard: Lobster/modules.txt)")
    parser.add_argument("--all", action="store_true", help="alle GS1-Module statt der Modulliste (nur mit --out-dir)")
    parser.add_argument("--out-dir", default=LOBSTER_DIR, help="Zielordner (Standard: Lobster/)")
    args = parser.parse_args()
    if args.all and os.path.abspath(args.out_dir) == LOBSTER_DIR:
        sys.exit("--all überschreibt sonst die Storck-XSD in Lobster/ – bitte --out-dir angeben")
    out_file = os.path.join(args.out_dir, OUT_NAME)
    ns_file = os.path.join(args.out_dir, NS_NAME)
    source = "alle Module" if args.all else os.path.relpath(os.path.abspath(args.modules), ROOT_DIR)

    files, module_files = schema_files()

    # 1. Alle globalen Komponenten einsammeln: (space, ns, name) -> Element
    comps = {}
    module_elements = []  # (ns, name)
    version = etree.parse(os.path.join(SCHEMA_DIR, files[0])).getroot().get("version")
    for rel in files:
        root = etree.parse(os.path.join(SCHEMA_DIR, rel)).getroot()
        ns = root.get("targetNamespace")
        for c in root:
            if not isinstance(c.tag, str) or local(c) not in COMPONENT_SPACE:
                continue
            key = (COMPONENT_SPACE[local(c)], ns, c.get("name"))
            if key in comps:
                continue  # SBDH-Includes können doppelt geladen werden
            comps[key] = c
            if rel in module_files and local(c) == "element":
                module_elements.append((ns, c.get("name")))
    if len(module_elements) != len(module_files):
        sys.exit("Erwartet genau ein globales Element pro Modul")
    if not args.all:
        wanted = read_module_list(args.modules)
        check_module_list(wanted, [name for ns, name in module_elements], args.modules)
        module_elements = [(ns, name) for ns, name in module_elements if name in wanted]

    # 2. Neue (namespace-freie) Namen vergeben, Konflikte auflösen
    def canonical(el):
        """Definition mit aufgelösten QNames, um Duplikate zu erkennen."""
        e = copy.deepcopy(el)
        for src, d in zip(el.iter(), e.iter()):
            if not isinstance(d.tag, str):
                continue
            for a in list(d.attrib):
                if a in QNAME_ATTRS:
                    d.set(a, "{%s}%s" % resolve_qname(src, d.get(a)))
        for d in e.xpath(".//xsd:annotation", namespaces=NS):
            d.getparent().remove(d)
        return etree.tostring(e, method="c14n")

    by_name = {}
    for space, ns, name in comps:
        by_name.setdefault((space, name), []).append(ns)
    newname = {}
    for (space, name), nss in by_name.items():
        if len(nss) == 1:
            newname[(space, nss[0], name)] = name
            continue
        defs = {canonical(comps[(space, ns, name)]) for ns in nss}
        if len(defs) == 1:
            for ns in nss:
                newname[(space, ns, name)] = name
            print("Zusammengeführt (identisch):", name)
        else:
            for ns in nss:
                prefix = ns.split(":")[-3] if ns.startswith("urn:") else "sbdh"
                newname[(space, ns, name)] = name if ns == SHARED_NS else "%s_%s" % (prefix, name)
            print("Umbenannt (unterschiedlich):", name, "->", [newname[(space, ns, name)] for ns in nss])

    def rename(space, ns, name):
        if ns == XS:
            return "xsd:" + name
        return newname[(space, ns, name)]

    # 3. Komponenten kopieren und QNames umschreiben
    out = {}
    for (space, ns, name), el in comps.items():
        # QNames gegen das Original auflösen: deepcopy behält nur benutzte Namespace-Deklarationen
        e = copy.deepcopy(el)
        for src, d in zip(el.iter(), e.iter()):
            if not isinstance(d.tag, str):
                continue
            for a in list(d.attrib):
                if a in QNAME_ATTRS:
                    rns, rname = resolve_qname(src, d.get(a))
                    d.set(a, rename(ref_space(d, a), rns, rname))
                elif a == "memberTypes":
                    d.set(a, " ".join(rename("type", *resolve_qname(src, v)) for v in d.get(a).split()))
        e.set("name", newname[(space, ns, name)])
        out[(space, newname[(space, ns, name)])] = (ns, e)

    # 4. Substitution Groups einsammeln (abstraktes Kopf-Element -> konkrete Elemente).
    #    gdsn_common:document -> catalogueItemNotification (nur die CIN ist geladen),
    #    sbdh:ScopeInformation -> CorrelationInformation | BusinessService
    subst = {}
    for (space, name), (ns, e) in out.items():
        if space == "element" and e.get("substitutionGroup"):
            subst.setdefault(e.get("substitutionGroup"), []).append(name)

    # 5. Modul-Extension-Typ anlegen und in die Owner-Typen einhängen
    ext = etree.Element("{%s}complexType" % XS, name=MODULE_EXT_TYPE, nsmap=NS)
    ann = etree.SubElement(etree.SubElement(ext, "{%s}annotation" % XS), "{%s}documentation" % XS)
    ann.text = "Ersetzt shared_common:ExtensionType (xsd:any). Enthält %s GDSN TradeItem-Module %s." % (
        "alle" if args.all else "die %d Module aus %s" % (len(module_elements), source), version)
    seq = etree.SubElement(ext, "{%s}sequence" % XS)
    for ns, name in sorted(module_elements, key=lambda x: x[1].lower()):
        etree.SubElement(seq, "{%s}element" % XS, ref=newname[("element", ns, name)], minOccurs="0")
    out[("type", MODULE_EXT_TYPE)] = (SHARED_NS, ext)
    for ns, owner in MODULE_EXT_OWNERS:
        t = out[("type", owner)][1]
        (ext_el,) = t.xpath(".//xsd:element[@name='extension']", namespaces=NS)
        ext_el.set("type", MODULE_EXT_TYPE)

    # 6. Gruppen und Element-Referenzen in lokale Deklarationen auflösen
    def occurs(src, dst):
        for a in ("minOccurs", "maxOccurs"):
            if src.get(a) is not None:
                dst.set(a, src.get(a))

    def inline_refs(node):
        for gr in node.xpath(".//xsd:group[@ref]", namespaces=NS):
            model = copy.deepcopy(next(c for c in out[("group", gr.get("ref"))][1] if local(c) != "annotation"))
            occurs(gr, model)
            gr.getparent().replace(gr, model)
        for r in node.xpath(".//xsd:element[@ref]", namespaces=NS):
            g = out[("element", r.get("ref"))][1]
            if g.get("abstract") == "true":
                members = sorted(subst.get(r.get("ref"), []))
                if len(members) == 1:
                    r.set("ref", members[0])
                    g = out[("element", members[0])][1]
                else:
                    choice = etree.Element("{%s}choice" % XS)
                    occurs(r, choice)
                    for m in members:
                        etree.SubElement(choice, "{%s}element" % XS, ref=m)
                    r.getparent().replace(r, choice)
                    inline_refs(choice)
                    continue
            r.set("name", g.get("name"))
            del r.attrib["ref"]
            for a, v in g.attrib.items():
                if a not in ("name", "abstract", "substitutionGroup"):
                    r.set(a, v)
            for child in g:
                r.append(copy.deepcopy(child))
            inline_refs(r)

    for (space, name), (ns, e) in out.items():
        if space == "type":
            inline_refs(e)
    root_el = out[("element", ROOT_ELEMENT)][1]
    inline_refs(root_el)

    # 7. Nur vom Root erreichbare Typen behalten
    types = {name: e for (space, name), (ns, e) in out.items() if space == "type"}
    keep, todo = set(), [root_el]
    while todo:
        node = todo.pop()
        for d in node.iter():
            if not isinstance(d.tag, str):
                continue
            refs = [d.get(a) for a in ("type", "base", "itemType") if d.get(a)]
            refs += (d.get("memberTypes") or "").split()
            for t in refs:
                if t in types and t not in keep:
                    keep.add(t)
                    todo.append(types[t])
    if any(space not in ("type", "element", "group") for space, _ in out):
        sys.exit("Unerwartete globale Komponente (attribute/group) – Skript erweitern")

    # 8. Ausgabe
    schema = etree.Element(
        "{%s}schema" % XS,
        nsmap=NS,
        attributeFormDefault="unqualified",
        elementFormDefault="unqualified",
        version=version,
    )
    doc = etree.SubElement(etree.SubElement(schema, "{%s}annotation" % XS), "{%s}documentation" % XS)
    doc.text = (
        "GS1 GDSN CatalogueItemNotification %s inkl. StandardBusinessDocumentHeader und %s, " % (
            version, "aller TradeItem-Module" if args.all
            else "der %d TradeItem-Module aus %s" % (len(module_elements), source))
        + "zu einer Datei ohne targetNamespace zusammengeführt (tools/build_cin_flat_xsd.py). "
        + "Namespace-qualifizierte Elemente der Original-Nachricht siehe Lobster/README.md."
    )
    schema.append(root_el)
    for name in sorted(keep, key=str.lower):
        schema.append(types[name])
    for d in schema.iter():
        if isinstance(d.tag, str):
            d.tag = "{%s}%s" % (XS, local(d))
    etree.cleanup_namespaces(schema, top_nsmap=NS)
    etree.indent(schema, space="    ")

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    etree.ElementTree(schema).write(out_file, xml_declaration=True, encoding="UTF-8", pretty_print=True)

    # 9. Namespace-Tabelle: welche Elemente in der echten GDSN-Nachricht qualifiziert sind
    def prefix(ns):
        return "sh" if ns == SBDH_NS else ns.split(":")[-3]

    rows = [
        ("catalogueItemNotificationMessage", "/catalogueItemNotificationMessage", prefix(CIN_NS), CIN_NS),
        ("StandardBusinessDocumentHeader", "/catalogueItemNotificationMessage/StandardBusinessDocumentHeader (inkl. aller Unterelemente)", "sh", SBDH_NS),
        ("catalogueItemNotification", "/catalogueItemNotificationMessage/transaction/documentCommand/catalogueItemNotification", prefix(CIN_NS), CIN_NS),
    ]
    for ns, name in sorted(module_elements, key=lambda x: x[1].lower()):
        rows.append((name, ".../tradeItemInformation/extension/%s und .../componentInformation/extension/%s" % (name, name), prefix(ns), ns))
    with open(ns_file, "w", encoding="utf-8") as f:
        f.write("element;pfad;praefix;namespace\n")
        for r in rows:
            f.write(";".join(r) + "\n")

    print("Geschrieben:", os.path.relpath(out_file, ROOT_DIR), "-", len(keep), "Typen,", len(module_elements), "Module")


if __name__ == "__main__":
    main()
