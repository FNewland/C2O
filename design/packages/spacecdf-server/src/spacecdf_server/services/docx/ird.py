"""SpaceCDF Word document family: ird. Interface requirements document (IRD).

W1.09a: the interface tables come from the study; nothing is hard-coded.

W4.07 (ECSS-E-ST-10-24C, without pin-outs): the IRD is built from the study's data only:

* segment interfaces: the link cases (band, frequency, rate, modulation, coding, margin per
  station and direction), the interfaces between segments, and the launch segment (deployer);
* space segment interfaces: the power rails and the power lines (LCL, switch, inhibits, loads),
  the data buses and their nodes (address, rate), then every other interface by type (data,
  timing, signals, RF, mechanical, thermal) with its exchange items;
* the interface control documents (exchange items) with the interfaces that carry them and the
  requirements linked to them (the requirement <-> ICD links of W2.07);
* the interface requirements (imported ``IF-*`` rows and the ``IR-*`` rows generated from the
  links) with their parents, ICD and covered interfaces, and the interfaces no requirement covers.

``generate_ird_from_export(sx, lang, diagrams=...)`` is the generator (sections ``elements``,
``requirements``, ``links``, ``electrical``); ``generate_ird_docx(study_name, data)`` is the legacy
entry of ``/docx/ird`` without a study. See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import (
    _add_cover_page,
    _add_diagrams,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _compact_table,
    _orient,
    _setup_margins,
    _setup_styles,
)
from .ts import _methods, _num, launch_lines, requirement_rows, threshold_text

TYPE_ORDER = ("power", "data", "timing", "electrical_signal", "rf", "mechanical", "thermal", "optical", "fluid")
TYPE_TITLES = {
    "power": {"en": "Power interfaces", "fr": "Interfaces de puissance"},
    "data": {"en": "Data interfaces", "fr": "Interfaces de données"},
    "timing": {"en": "Timing interfaces", "fr": "Interfaces de synchronisation"},
    "electrical_signal": {"en": "Electrical signal interfaces", "fr": "Interfaces de signaux électriques"},
    "rf": {"en": "RF interfaces", "fr": "Interfaces RF"},
    "mechanical": {"en": "Mechanical interfaces", "fr": "Interfaces mécaniques"},
    "thermal": {"en": "Thermal interfaces", "fr": "Interfaces thermiques"},
    "optical": {"en": "Optical interfaces", "fr": "Interfaces optiques"},
    "fluid": {"en": "Fluid interfaces", "fr": "Interfaces fluides"},
}

_TXT = {
    "title": {"en": "Interface Requirements Document", "fr": "Document des exigences d’interface"},
    "intro": {"en": "Introduction", "fr": "Introduction"},
    "purpose": {"en": "This document states the interfaces of the {name} system between its segments and between "
                      "the units of the space segment, and the requirements on them. Every table is drawn from the "
                      "study (links, link cases, electrical and data architecture, exchange items, requirements). "
                      "Connector pin-outs are given in the interface control documents at CDR.",
                "fr": "Ce document énonce les interfaces du système {name} entre ses segments et entre les unités du "
                      "segment spatial, et les exigences qui s’y appliquent. Chaque tableau est tiré de l’étude "
                      "(liaisons, cas de bilan de liaison, architecture électrique et de données, éléments "
                      "d’échange, exigences). Les brochages des connecteurs sont donnés dans les documents de "
                      "contrôle d’interface à la CDR."},
    "docs": {"en": "Applicable and reference documents", "fr": "Documents applicables et de référence"},
    "overview": {"en": "Interface overview", "fr": "Vue d’ensemble des interfaces"},
    "segments": {"en": "Segment interfaces", "fr": "Interfaces entre segments"},
    "rf": {"en": "Space to ground radio links", "fr": "Liaisons radio espace-sol"},
    "design_case": {"en": "Link design case: {txt}.", "fr": "Cas de dimensionnement de la liaison : {txt}."},
    "no_links": {"en": "No link-budget case is recorded yet (Link budget tab).",
                 "fr": "Aucun cas de bilan de liaison n’est encore enregistré (onglet Bilan de liaison)."},
    "launch": {"en": "Space to launch interface", "fr": "Interface espace-lanceur"},
    "no_launch": {"en": "No launch segment element is recorded yet.",
                  "fr": "Aucun élément du segment lancement n’est encore enregistré."},
    "seg_ifs": {"en": "Interfaces between segments", "fr": "Interfaces entre segments"},
    "none_seg": {"en": "No interface between segments is recorded in the study yet.",
                 "fr": "Aucune interface entre segments n’est encore enregistrée dans l’étude."},
    "internal": {"en": "Space segment interfaces", "fr": "Interfaces du segment spatial"},
    "rails": {"en": "Power rails", "fr": "Rails d’alimentation"},
    "lines": {"en": "Power lines (switches and current limiters)", "fr": "Lignes d’alimentation (commutateurs et limiteurs)"},
    "buses": {"en": "Data buses", "fr": "Bus de données"},
    "nodes": {"en": "Bus nodes and addresses", "fr": "Nœuds de bus et adresses"},
    "no_elec": {"en": "The electrical and data architecture is not proposed yet (Electrical tab).",
                "fr": "L’architecture électrique et de données n’est pas encore proposée (onglet Électrique)."},
    "none_sub": {"en": "No interface inside the space segment is recorded in the study yet.",
                 "fr": "Aucune interface interne au segment spatial n’est encore enregistrée dans l’étude."},
    "icds": {"en": "Interface control documents and their requirements",
             "fr": "Documents de contrôle d’interface et leurs exigences"},
    "icds_txt": {"en": "Each exchange item is one interface control document (ICD) row: the interfaces that carry it "
                       "and the interface requirements linked to it.",
                 "fr": "Chaque élément d’échange est une ligne de document de contrôle d’interface (ICD) : les "
                       "interfaces qui le portent et les exigences d’interface qui y sont liées."},
    "no_icds": {"en": "No exchange item is recorded yet.", "fr": "Aucun élément d’échange n’est encore enregistré."},
    "irs": {"en": "Interface requirements", "fr": "Exigences d’interface"},
    "no_irs": {"en": "No interface requirement is recorded in the study yet.",
               "fr": "Aucune exigence d’interface n’est encore enregistrée dans l’étude."},
    "coverage": {"en": "Coverage", "fr": "Couverture"},
    "cov_txt": {"en": "{c} of {n} interfaces are covered by at least one interface requirement; {u} are not:",
                "fr": "{c} des {n} interfaces sont couvertes par au moins une exigence d’interface ; {u} ne le sont pas :"},
    "physical": {"en": "Physical interfaces", "fr": "Interfaces physiques"},
    "ports": {"en": "{n} ports are defined on the units ({kinds}). Connector types and pin-outs are defined in the "
                    "ICDs at CDR.",
              "fr": "{n} ports sont définis sur les unités ({kinds}). Les types de connecteurs et les brochages sont "
                    "définis dans les ICD à la CDR."},
    "diagrams": {"en": "Interface diagrams", "fr": "Diagrammes d’interface"},
    "diag_txt": {"en": "Drawn from the design model (the same figures as the SpaceCDF Diagrams view); each figure lists "
                       "what the model still lacks for it.",
                 "fr": "Tirés du modèle de conception (les mêmes figures que la vue Diagrammes de SpaceCDF) ; chaque "
                       "figure indique ce qui manque encore au modèle."},
}


def _props(p: Any) -> str:
    if not isinstance(p, dict):
        return ""
    return "; ".join(f"{k}: {_num(v)}" for k, v in p.items() if v not in (None, "", [], {}) and not isinstance(v, (dict, list)))


def _ir_interface_ids(r: dict) -> list[str]:
    ir = r.get("ir_json") or {}
    ids = [ir.get("interface_id"), *(ir.get("interface_ids") or []), *(ir.get("covers_interface_ids") or [])]
    return [i for i in dict.fromkeys(ids) if i]


def build_ird(name: str, *, elements: list[dict], interfaces: list[dict], irs: list[dict], links: dict | None = None,
              electrical: dict | None = None, data: dict | None = None, lang: str = "en") -> bytes:
    lang = "fr" if str(lang or "").lower().startswith("fr") else "en"

    def T(key: str, **kw: Any) -> str:
        return _TXT[key][lang].format(**kw)

    en = lang == "en"
    els = {e.get("id"): e for e in elements if e.get("id")}
    links = links or {}
    elec = electrical or {}
    xis = {x["id"]: x for x in elec.get("exchange_items") or [] if x.get("id")}

    def seg(eid):
        cur, n = els.get(eid) or {}, 0
        while cur and not cur.get("segment") and cur.get("parent_id") in els and n < 50:
            cur, n = els[cur["parent_id"]], n + 1
        return (cur or {}).get("segment") or ""

    def ends(i):
        return (i.get("from_element_id") or i.get("source_element_id"), i.get("to_element_id") or i.get("target_element_id"))

    def ename(eid):
        return (els.get(eid) or {}).get("name") or eid or ""

    def icd_names(i):
        ids = i.get("exchange_item_ids_json") or i.get("exchange_item_ids") or []
        return [xis[x]["name"] for x in ids if x in xis]

    def if_row(i):
        a, b = ends(i)
        return [i.get("name") or "", ename(a), ename(b), i.get("subtype") or "", i.get("direction") or "",
                i.get("status") or "", _props(i.get("properties")), icd_names(i)]

    if_headers = (["Interface", "From", "To", "Subtype", "Direction", "Status", "Properties", "ICD"] if en else
                  ["Interface", "De", "Vers", "Sous-type", "Sens", "Statut", "Propriétés", "ICD"])
    if_widths = [5.0, 3.4, 3.4, 1.8, 1.8, 1.6, 3.6, 3.0]
    ifs = sorted(interfaces, key=lambda i: (str(i.get("interface_type") or i.get("type") or ""), str(i.get("name") or "")))
    seg_ifs = [i for i in ifs if seg(ends(i)[0]) != seg(ends(i)[1])]
    sub_ifs = [i for i in ifs if i not in seg_ifs]

    irs = sorted(irs, key=lambda r: str(r.get("code") or ""))
    covered: dict[str, list[str]] = {}
    for r in irs:
        for iid in _ir_interface_ids(r):
            covered.setdefault(iid, []).append(r.get("code") or r.get("id"))
    req_by_xi: dict[str, list[str]] = {}
    for r in irs:
        for x in (r.get("ir_json") or {}).get("exchange_item_ids") or []:
            req_by_xi.setdefault(x, []).append(r.get("code") or r.get("id"))

    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    _add_cover_page(doc, T("title"), "ECSS-E-ST-10-24C", name)
    _add_toc_placeholder(doc)
    _add_footer(doc, name, "IRD")

    _add_section(doc, "1", T("intro"), T("purpose", name=name))
    _add_section(doc, "2", T("docs"))
    for d in ("ECSS-E-ST-10-24C — Interface management", "ECSS-E-ST-50C — Communications",
              "ECSS-E-ST-20C — Electrical and electronic", "CCSDS 131.0-B / 132.0-B — TM synchronisation and space data link",
              "CubeSat Design Specification rev. 14.1"):
        doc.add_paragraph(d, style="List Bullet")

    # 3 overview
    _add_section(doc, "3", T("overview"))
    types = [t for t in TYPE_ORDER if any((i.get("interface_type") or i.get("type")) == t for i in ifs)]
    types += sorted({str(i.get("interface_type") or i.get("type") or "") for i in ifs} - set(types))
    if ifs:
        _add_table(doc, ["Type", "Interfaces", "Between segments" if en else "Entre segments",
                         "Covered by a requirement" if en else "Couvertes par une exigence"],
                   [[t or "—", str(sum(1 for i in ifs if (i.get("interface_type") or i.get("type") or "") == t)),
                     str(sum(1 for i in seg_ifs if (i.get("interface_type") or i.get("type") or "") == t)),
                     str(sum(1 for i in ifs if (i.get("interface_type") or i.get("type") or "") == t and i.get("id") in covered))]
                    for t in types]
                   + [["Total", str(len(ifs)), str(len(seg_ifs)), str(sum(1 for i in ifs if i.get("id") in covered))]])

    # 4 segment interfaces
    _orient(doc, landscape=True)
    _add_section(doc, "4", T("segments"))
    _add_section(doc, "4.1", T("rf"))
    dc = {k: v for k, v in (links.get("design_case") or {}).items() if v not in (None, "", [], {})}
    if dc:
        keys = ("band", "downlink_frequency_mhz", "uplink_frequency_mhz", "downlink_rate_bps", "uplink_rate_bps",
                "tx_power_w", "margin_db", "source")
        doc.add_paragraph(T("design_case", txt="; ".join(f"{k.replace('_', ' ')} {_num(dc[k])}" for k in keys if k in dc)))
    cases = links.get("items") or []
    if cases:
        _compact_table(doc, ["Case" if en else "Cas", "Direction", "Band" if en else "Bande", "Frequency (MHz)" if en else "Fréquence (MHz)",
                             "Rate (bit/s)" if en else "Débit (bit/s)", "Modulation", "Coding" if en else "Codage",
                             "Station", "TX power (W)" if en else "Puissance TX (W)", "Elevation (deg)" if en else "Élévation (deg)",
                             "Margin (dB)" if en else "Marge (dB)"],
                       [[c.get("name") or c.get("id"), c.get("direction"), c.get("band"), c.get("frequency_mhz"),
                         c.get("data_rate_bps") or c.get("rate_bps"), c.get("modulation"), c.get("coding"), c.get("station"),
                         c.get("tx_power_w"), c.get("elevation_deg"),
                         c.get("margin_db") if c.get("margin_db") is not None else (c.get("results") or {}).get("margin_db")]
                        for c in cases],
                       widths_cm=[4.6, 1.6, 1.2, 1.8, 1.8, 2.4, 3.0, 2.0, 1.6, 1.6, 1.4])
    else:
        doc.add_paragraph(T("no_links"))
    rf_seg = [i for i in seg_ifs if (i.get("interface_type") or i.get("type")) == "rf"]
    if rf_seg:
        _compact_table(doc, if_headers, [if_row(i) for i in rf_seg], widths_cm=if_widths)
    _add_section(doc, "4.2", T("launch"))
    ll = launch_lines(elements)
    for x in ll:
        doc.add_paragraph(x, style="List Bullet")
    if not ll:
        doc.add_paragraph(T("no_launch"))
    launch_ifs = [i for i in seg_ifs if "launch" in (seg(ends(i)[0]), seg(ends(i)[1]))]
    if launch_ifs:
        _compact_table(doc, if_headers, [if_row(i) for i in launch_ifs], widths_cm=if_widths)
    _add_section(doc, "4.3", T("seg_ifs"))
    other = [i for i in seg_ifs if i not in rf_seg and i not in launch_ifs]
    if other:
        _compact_table(doc, if_headers, [if_row(i) for i in other], widths_cm=if_widths)
    elif not seg_ifs:
        doc.add_paragraph(T("none_seg"))

    # 5 space segment interfaces: power, data, then every other type
    _add_section(doc, "5", T("internal"))
    rails, lines, buses, nodes = (elec.get(k) or [] for k in ("rails", "lines", "buses", "nodes"))
    n = 1
    _add_section(doc, f"5.{n}", T("rails"))
    if rails:
        _compact_table(doc, ["Rail", "Voltage (V)" if en else "Tension (V)", "Regulated" if en else "Régulé",
                             "Range (V)" if en else "Plage (V)", "Max current (A)" if en else "Courant max (A)",
                             "Source" if en else "Source", "Notes"],
                       [[r.get("name"), r.get("voltage_v"), r.get("regulated"),
                         f"{_num(r['v_min'])} to {_num(r['v_max'])}" if r.get("v_min") is not None and r.get("v_max") is not None else "",
                         r.get("max_current_a"), r.get("eps") or "", r.get("notes") or ""] for r in rails],
                       widths_cm=[3.0, 2.0, 2.0, 2.4, 2.4, 6.0, 5.0])
    else:
        doc.add_paragraph(T("no_elec"))
    if lines:
        _add_section(doc, f"5.{n}.1", T("lines"))
        _compact_table(doc, ["No.", "Line" if en else "Ligne", "Rail", "LCL (A)", "Switchable" if en else "Commutable",
                             "On at separation" if en else "Active à la séparation", "On at boot" if en else "Active au démarrage",
                             "Inhibits" if en else "Inhibitions", "Loads" if en else "Charges"],
                       [[ln.get("line_no"), ln.get("name"), ln.get("rail"), ln.get("lcl_limit_a"), ln.get("switchable"),
                         ln.get("default_on_separation"), ln.get("default_on_boot"), ln.get("inhibits") or [],
                         ln.get("loads") or []] for ln in lines],
                       widths_cm=[1.0, 5.0, 1.6, 1.4, 1.8, 2.0, 2.0, 3.4, 5.2])
    n += 1
    _add_section(doc, f"5.{n}", T("buses"))
    if buses:
        _compact_table(doc, ["Bus", "Protocol" if en else "Protocole", "Bit rate (bit/s)" if en else "Débit (bit/s)",
                             "Master" if en else "Maître", "Redundancy" if en else "Redondance",
                             "Max devices" if en else "Appareils max", "Notes"],
                       [[b.get("name"), b.get("protocol"), b.get("bit_rate_bps"), b.get("master") or "", b.get("redundancy"),
                         b.get("max_devices"), b.get("notes") or ""] for b in buses],
                       widths_cm=[5.0, 3.0, 2.4, 5.0, 2.0, 1.8, 3.6])
        if nodes:
            _add_section(doc, f"5.{n}.1", T("nodes"))
            _compact_table(doc, ["Bus", "Unit" if en else "Unité", "Role" if en else "Rôle", "Address" if en else "Adresse",
                                 "Data rate (bit/s)" if en else "Débit (bit/s)"],
                           [[nd.get("bus"), nd.get("element"), nd.get("role"),
                             f"{nd['address']} (0x{int(nd['address']):02X})" if isinstance(nd.get("address"), int) else nd.get("address"),
                             nd.get("data_rate_bps")] for nd in nodes],
                           widths_cm=[5.0, 8.0, 2.0, 3.0, 3.0])
    else:
        doc.add_paragraph(T("no_elec"))
    if not sub_ifs:
        doc.add_paragraph(T("none_sub"))
    for t in types:
        rows = [i for i in sub_ifs if (i.get("interface_type") or i.get("type") or "") == t]
        if not rows:
            continue
        n += 1
        _add_section(doc, f"5.{n}", f"{TYPE_TITLES.get(t, {}).get(lang) or (t or '—').capitalize()} ({len(rows)})")
        _compact_table(doc, if_headers, [if_row(i) for i in rows], widths_cm=if_widths)

    # 6 ICDs (exchange items) with the requirements linked to them
    _add_section(doc, "6", T("icds"), T("icds_txt"))
    ifname = {i.get("id"): i.get("name") for i in interfaces}
    if xis:
        _compact_table(doc, ["ICD", "Kind" if en else "Nature", "Interfaces", "Requirements" if en else "Exigences",
                             "Properties" if en else "Propriétés"],
                       [[x.get("name"), x.get("kind"),
                         f"{len(x.get('interface_ids') or [])}: " + "; ".join(ifname.get(i, i) for i in (x.get("interface_ids") or [])[:6])
                         + (" …" if len(x.get("interface_ids") or []) > 6 else ""),
                         req_by_xi.get(x["id"], []), _props(x.get("properties"))] for x in xis.values()],
                       widths_cm=[4.6, 1.8, 10.0, 3.4, 4.0])
    else:
        doc.add_paragraph(T("no_icds"))

    # 7 interface requirements
    _add_section(doc, "7", f"{T('irs')} ({len(irs)})")
    if irs:
        _compact_table(doc, ["Code", "Requirement" if en else "Exigence", "Threshold" if en else "Seuil",
                             "Method" if en else "Méthode", "Parents" if en else "Mères", "ICD",
                             "Interfaces", "Allocated to" if en else "Allouée à", "Rationale / source" if en else "Justification / source"],
                       [[r.get("code") or r.get("id", ""), r.get("text") or "", threshold_text(r), _methods(r),
                         r.get("parent_codes") or r.get("parent_code") or "",
                         (r.get("ir_json") or {}).get("icd_ref") or [xis[x]["name"] for x in (r.get("ir_json") or {}).get("exchange_item_ids") or [] if x in xis],
                         "; ".join(ifname.get(i, i) for i in _ir_interface_ids(r)[:3]) + (" …" if len(_ir_interface_ids(r)) > 3 else ""),
                         r.get("allocated_to") or "",
                         " — ".join(x for x in (r.get("rationale"), r.get("source_ref")) if x)] for r in irs],
                       widths_cm=[2.2, 6.0, 1.6, 1.0, 2.0, 2.4, 4.6, 2.4, 3.6])
    else:
        doc.add_paragraph(T("no_irs"))
    _add_section(doc, "8", T("coverage"))
    uncovered = [i for i in ifs if i.get("id") not in covered]
    doc.add_paragraph(T("cov_txt", c=len(ifs) - len(uncovered), n=len(ifs), u=len(uncovered)))
    if uncovered:
        _compact_table(doc, ["Interface", "Type", "Subtype" if en else "Sous-type", "Status" if en else "Statut"],
                       [[i.get("name"), i.get("interface_type") or i.get("type"), i.get("subtype"), i.get("status")]
                        for i in uncovered], widths_cm=[14.0, 3.0, 3.4, 3.0])
    _orient(doc, landscape=False)

    _add_section(doc, "9", T("physical"))
    ports = elec.get("ports") or {}
    if ports.get("total"):
        doc.add_paragraph(T("ports", n=ports["total"], kinds=", ".join(f"{k} {v}" for k, v in sorted((ports.get("by_kind") or {}).items()))))
    else:
        doc.add_paragraph("Connector types and pin-outs are defined in the ICDs at CDR." if en else
                          "Les types de connecteurs et les brochages sont définis dans les ICD à la CDR.")

    _add_diagrams(doc, "10", T("diagrams"), data or {}, T("diag_txt"))

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generate_ird_from_export(sx: Any, lang: str = "en", diagrams: list | None = None) -> bytes:
    """The IRD of a collected study (``export_context.StudyExport``)."""
    elements = (getattr(sx, "elements", None) or {}).get("items") or []
    interfaces = (getattr(sx, "elements", None) or {}).get("interfaces") or []
    reqs = requirement_rows((getattr(sx, "requirements", None) or {}).get("items") or [], elements)
    irs = [r for r in reqs if r.get("level") == "interface" or r.get("generated_interface")]
    return build_ird(getattr(sx, "study_name", "") or "", elements=elements, interfaces=interfaces, irs=irs,
                     links=getattr(sx, "links", None) or {}, electrical=getattr(sx, "electrical", None) or {},
                     data={"diagrams": diagrams or []}, lang=lang)


def generate_ird_docx(study_name: str, data: dict[str, Any]) -> bytes:
    """Legacy entry (``/docx/ird`` without a study): the ``data`` dict of the docx route."""
    irs = [{**r, "parent_codes": r.get("parent_codes") or ([r["parent_code"]] if r.get("parent_code") else [])}
           for r in data.get("interface_requirements") or []]
    return build_ird(study_name, elements=data.get("elements") or [], interfaces=data.get("interfaces") or [],
                     irs=irs, data=data)
