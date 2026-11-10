"""Requirement, interface and exchange-item queries for documents (wave 2, agent R).

The technical specification (TS, W4.06) and the interface requirements document (IRD, W4.07)
read the requirement store through these functions, so every document counts and groups the
same rows. Every function is read-only. See ``docs/dev/REQUIREMENT_COUNTS.md`` for what the
store holds for the Northern Fire and Ice mission and why.

``await requirement_counts(study_id)``
    How many live requirements of each kind the study holds: ``stakeholder`` needs (SN-*),
    ``objective`` rows (OBJ-*), ``generated_interface`` rows (IR-*, rule IF-01) and ``user``
    rows (everything else, e.g. the 216 baseline rows), plus ``by_level`` and the totals a
    document should quote: ``specification`` (all but the needs) and ``all``.

``await ts_rows(study_id, include_generated=True)``
    One flat dict per requirement of the specification scope (every live requirement but the
    stakeholder needs), ordered by TS group, level and code. Fields: ``code, level, group,
    type, category, text, text_fr, rationale, unit, threshold, stage, methods, parents
    (codes), objectives, allocation, allocation_path, owner, priority, source, status,
    open_item, generated, tbd``. ``group`` is one of :data:`TS_GROUPS`.

``ts_group(row)``
    The TS group of one requirement dict (pure).

``await ird_dataset(study_id)``
    Everything the IRD/ICD tables need, from data: accepted interfaces with their end points,
    boundary subsystems, properties, power line (LCL, rail), bus node (bus, protocol, address,
    rate), exchange items and the interface requirements that cover them; the interface
    requirements with their template, origin, covered links, exchange items and parent; the
    exchange items with their interfaces and requirements; the segment interfaces; the
    suggestions (templates with too few known values) and the PDR-EC-02 status.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

#: technical specification groups (ECSS-E-ST-10-06C §8 requirement types, folded to the seven
#: groups of plan item W4.06), in document order
TS_GROUPS = ("functional", "performance", "interface", "environmental", "operational",
             "product_assurance", "regulatory")
TS_GROUP_LABELS = {
    "functional": {"en": "Functional requirements", "fr": "Exigences fonctionnelles"},
    "performance": {"en": "Performance requirements", "fr": "Exigences de performance"},
    "interface": {"en": "Interface requirements", "fr": "Exigences d’interface"},
    "environmental": {"en": "Environmental requirements", "fr": "Exigences d’environnement"},
    "operational": {"en": "Operational requirements", "fr": "Exigences opérationnelles"},
    "product_assurance": {"en": "Product assurance requirements", "fr": "Exigences d’assurance produit"},
    "regulatory": {"en": "Regulatory requirements", "fr": "Exigences réglementaires"},
}
_ENV_CATEGORIES = {"environment", "emc", "cleanliness", "launch", "lifetime"}
_OPS_CATEGORIES = {"operations", "modes_fdir", "ground_segment", "user_segment", "security"}
_PA_CATEGORIES = {"verification", "reliability", "safety"}
_ENV_WORDS = ("withstand", "radiation", "total ionising dose", "total ionizing dose", "vibration",
              "thermal vacuum", "launch environment", "environments")
_TBD = re.compile(r"\b(TBD|TBC)\b")
_LEVEL_ORDER = ("stakeholder", "mission", "segment", "system", "subsystem", "interface")
_OPS = {">=": "≥", "<=": "≤", ">": ">", "<": "<", "==": "=", "=": "="}


def is_generated(r: dict) -> bool:
    """An interface requirement made by rule IF-01 from an accepted link (code IR-*)."""
    return (r.get("ir_json") or {}).get("origin") == "rule:IF-01" or str(r.get("code") or "").startswith("IR-")


def is_objective(r: dict) -> bool:
    return r.get("category") == "objective" or str(r.get("code") or "").startswith("OBJ-")


def kind_of(r: dict) -> str:
    """``stakeholder`` | ``objective`` | ``generated_interface`` | ``user``."""
    if r.get("level") == "stakeholder":
        return "stakeholder"
    if is_objective(r):
        return "objective"
    if is_generated(r):
        return "generated_interface"
    return "user"


def ts_group(r: dict) -> str:
    """The TS group of a requirement: interface rows first, then regulatory, environmental,
    operational and product-assurance categories, then the requirement type (functional or
    performance; a process requirement is product assurance)."""
    cat = str(r.get("category") or "").lower()
    rtype = str(r.get("req_type") or r.get("type") or "").lower()
    text = f" {(r.get('text') or '').lower()} "
    if r.get("level") == "interface" or rtype == "interface" or cat == "interface":
        return "interface"
    if rtype == "regulatory" or cat == "regulatory":
        return "regulatory"
    if cat in _ENV_CATEGORIES or (rtype == "performance" and any(w in text for w in _ENV_WORDS)):
        return "environmental"
    if cat in _OPS_CATEGORIES:
        return "operational"
    if cat in _PA_CATEGORIES or rtype == "process":
        return "product_assurance"
    if rtype == "functional" or is_objective(r):
        return "functional"
    return "performance"


def threshold_text(r: dict) -> str:
    """``≥ 3 independent inhibits (TBC)``, ``between 10 and 20 °C``, ``before 2028-06-30``; ``""``."""
    op, val, unit = r.get("threshold_op"), r.get("threshold_value"), r.get("threshold_unit") or ""
    if not op or val in (None, ""):
        return ""
    if isinstance(val, str):
        try:
            from .requirement_engine import _decode_threshold
            val = _decode_threshold(val)
        except Exception:  # noqa: BLE001
            pass
    if op == "in_range" and isinstance(val, (list, tuple)) and len(val) == 2:
        return f"between {val[0]} and {val[1]} {unit}".strip()
    if op in ("before", "after"):
        return f"{op} {val}"
    if isinstance(val, float) and val.is_integer():
        val = int(val)
    return f"{_OPS.get(op, op)} {val} {unit}".strip()


async def _live(study_id: str) -> list[dict]:
    from ..routers.requirements import _requirements, ensure_requirements_loaded, with_lists
    try:
        await ensure_requirements_loaded()
    except Exception:  # noqa: BLE001 — DB unavailable: use what is cached
        pass
    rows = [dict(r) for r in _requirements.values()
            if r.get("study_id") == study_id and r.get("status") != "retired"]
    return await with_lists(study_id, rows)


def _sort_key(r: dict) -> tuple:
    lvl = str(r.get("level") or "")
    return (_LEVEL_ORDER.index(lvl) if lvl in _LEVEL_ORDER else len(_LEVEL_ORDER), str(r.get("code") or "~"),
            str(r.get("id") or ""))


def counts_of(rows: list[dict]) -> dict[str, Any]:
    """Pure: the counts of :func:`requirement_counts` for live requirement dicts."""
    kinds = {"stakeholder": 0, "objective": 0, "generated_interface": 0, "user": 0}
    by_level: dict[str, int] = {}
    by_group: dict[str, int] = {g: 0 for g in TS_GROUPS}
    for r in rows:
        kinds[kind_of(r)] += 1
        lvl = str(r.get("level") or "")
        by_level[lvl] = by_level.get(lvl, 0) + 1
        if r.get("level") != "stakeholder":
            by_group[ts_group(r)] += 1
    return {**kinds, "by_level": by_level, "by_ts_group": by_group,
            "specification": len(rows) - kinds["stakeholder"],
            "specification_without_generated": len(rows) - kinds["stakeholder"] - kinds["generated_interface"],
            "all": len(rows)}


async def requirement_counts(study_id: str) -> dict[str, Any]:
    return counts_of(await _live(study_id))


def _element_path(eid: str | None, els: dict[str, dict]) -> str:
    out, seen, cur = [], set(), els.get(eid or "")
    while cur is not None and cur.get("id") not in seen:
        seen.add(cur["id"])
        if cur.get("element_type") != "mission":
            out.append(cur.get("name") or "")
        cur = els.get(cur.get("parent_id") or "")
    return " / ".join(reversed(out))


def _study_elements(study_id: str) -> dict[str, dict]:
    from ..routers import elements as el
    return {e["id"]: e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")}


async def ts_rows(study_id: str, include_generated: bool = True) -> list[dict]:
    rows = [r for r in await _live(study_id) if r.get("level") != "stakeholder"
            and (include_generated or not is_generated(r))]
    els = _study_elements(study_id)
    code_of = {r["id"]: r.get("code") or r["id"] for r in rows}
    try:
        from ..routers.requirements import _requirements
        code_of.update({k: v.get("code") or k for k, v in _requirements.items() if v.get("study_id") == study_id})
    except Exception:  # noqa: BLE001
        pass
    out = []
    for r in sorted(rows, key=_sort_key):
        ir = r.get("ir_json") or {}
        methods = list(r.get("verification_methods") or ([r["verification_method"]] if r.get("verification_method") else []))
        el = els.get(r.get("element_id") or "")
        text = r.get("text") or ""
        out.append({
            "id": r["id"], "code": r.get("code") or r["id"], "level": r.get("level"), "group": ts_group(r),
            "type": r.get("req_type"), "category": r.get("category"), "text": text,
            "text_fr": (ir.get("text_i18n") or {}).get("fr"), "rationale": r.get("rationale") or "",
            "unit": r.get("threshold_unit") or "", "threshold": threshold_text(r),
            "stage": r.get("verification_phase") or "", "methods": methods,
            "parents": [code_of.get(p, p) for p in r.get("parent_ids") or []],
            "objectives": list(r.get("objective_ids") or []),
            "allocation": (el or {}).get("name") or "", "allocation_path": _element_path(r.get("element_id"), els),
            "owner": r.get("responsible_position") or "", "priority": r.get("priority"),
            "source": r.get("source_ref") or "", "status": r.get("status"), "open_item": r.get("open_item"),
            "generated": is_generated(r), "tbd": bool(_TBD.search(text)),
        })
    order = {g: i for i, g in enumerate(TS_GROUPS)}
    out.sort(key=lambda x: order[x["group"]])          # stable: level and code order kept per group
    return out


# ─────────────────────────────────────────────────────────────────────────── IRD / ICD


def _segment_of(el: dict | None, els: dict[str, dict]) -> str | None:
    seen, cur = set(), el
    while cur is not None and cur.get("id") not in seen:
        seen.add(cur["id"])
        if cur.get("element_type") == "segment":
            return cur["id"]
        cur = els.get(cur.get("parent_id") or "")
    return None


async def ird_dataset(study_id: str) -> dict[str, Any]:
    from ..db import exchange_item_repo as xrepo
    from ..db.relation_repo import list_relations_by_study
    from . import interface_requirements as irs

    reqs = await _live(study_id)
    elements, interfaces, _ctx, rows = await irs._study_state(study_id)
    els = {e["id"]: e for e in elements}
    live_ifaces = [i for i in interfaces if i.get("status") == "accepted" and not i.get("deleted_at")
                   and i.get("from_element_id") in els and i.get("to_element_id") in els]
    plan = irs.coverage_plan(live_ifaces, els, reqs)
    try:
        items = {x["id"]: x for x in await xrepo.list_exchange_items_by_study(study_id)}
    except Exception:  # noqa: BLE001
        logger.exception("exchange items unavailable for %s", study_id)
        items = {}
    try:
        rels = await list_relations_by_study(study_id, kind="allocates")
    except Exception:  # noqa: BLE001
        rels = []
    by_id = {r["id"]: r for r in reqs}
    code = lambda rid: (by_id.get(rid) or {}).get("code") or rid  # noqa: E731
    # requirement ↔ exchange item and requirement ↔ interface, from the relations and ir_json
    x_reqs: dict[str, set[str]] = {}
    i_reqs: dict[str, set[str]] = {}
    for rel in rels:
        if rel.get("source_kind") != "requirement" or rel.get("source_id") not in by_id:
            continue
        if rel.get("target_kind") == "exchange_item":
            x_reqs.setdefault(rel["target_id"], set()).add(rel["source_id"])
        elif rel.get("target_kind") == "interface":
            i_reqs.setdefault(rel["target_id"], set()).add(rel["source_id"])
    ir_rows = [r for r in reqs if r.get("level") == "interface"]
    for r in ir_rows:
        ir = r.get("ir_json") or {}
        for iid in {ir.get("interface_id"), *(ir.get("interface_ids") or []), *(ir.get("covers_interface_ids") or [])}:
            if iid:
                i_reqs.setdefault(iid, set()).add(r["id"])
        for xid in ir.get("exchange_item_ids") or []:
            x_reqs.setdefault(xid, set()).add(r["id"])

    buses = {b["id"]: b for b in rows.get("buses", []) if b.get("status") != "rejected" and not b.get("deleted_at")}
    rails = {b["id"]: b for b in rows.get("rails", []) if b.get("status") != "rejected" and not b.get("deleted_at")}

    def end(eid: str) -> dict:
        e = els[eid]
        b = els.get(irs._boundary(e, els) or "") or e
        seg = els.get(_segment_of(e, els) or "")
        return {"id": eid, "name": e.get("name") or "", "element_type": e.get("element_type"),
                "boundary": b.get("name") or "", "boundary_id": b.get("id"), "segment": (seg or {}).get("name") or ""}

    out_ifaces = []
    x_ifaces: dict[str, list[str]] = {}
    for i in sorted(live_ifaces, key=lambda i: (i.get("type") or i.get("interface_type") or "", i.get("name") or "", i["id"])):
        t = i.get("type") or i.get("interface_type")
        f, to = end(i["from_element_id"]), end(i["to_element_id"])
        row: dict[str, Any] = {
            "id": i["id"], "name": i.get("name") or "", "type": t, "subtype": i.get("subtype"),
            "direction": i.get("direction"), "origin": i.get("origin"), "from": f, "to": to,
            "segment_interface": bool(f["segment"] and to["segment"] and f["segment"] != to["segment"])
            or (f["element_type"] == "segment" and to["element_type"] == "segment"),
            "properties": dict(i.get("properties") or {}),
            "line": None, "node": None, "exchange_items": [], "requirements": [], "covered_by": None,
        }
        if t == "power":
            ln = irs._line_for(i, rows)
            if ln:
                rail = rails.get(ln.get("rail_id") or "") or {}
                row["line"] = {"line_no": ln.get("line_no"), "name": ln.get("name") or "", "lcl_limit_a": ln.get("lcl_limit_a"),
                               "switchable": ln.get("switchable"), "inhibits": list(ln.get("inhibits") or []),
                               "rail": rail.get("name") or "", "rail_voltage_v": rail.get("voltage_v"),
                               "eps": (els.get(ln.get("eps_element_id") or "") or {}).get("name") or ""}
        if t == "data":
            node, bus = irs._node_for(i, rows)
            if node and bus:
                row["node"] = {"bus": bus.get("name") or "", "protocol": bus.get("protocol"),
                               "address": (f"0x{int(node['address']):02X}" if node.get("address") is not None else None),
                               "rate_bps": node.get("data_rate_bps") or bus.get("bit_rate_bps"),
                               "master": (els.get(bus.get("master_element_id") or "") or {}).get("name") or ""}
        for xid in list(i.get("exchange_item_ids_json") or i.get("exchange_item_ids") or []):
            if xid in items:
                row["exchange_items"].append(xid)
                x_ifaces.setdefault(xid, []).append(i["id"])
        row["requirements"] = sorted(code(rid) for rid in i_reqs.get(i["id"], set()))
        why = plan.get(i["id"])
        if why:
            ref = why[1]
            row["covered_by"] = {"reason": why[0],
                                 "ref": (els.get(ref) or {}).get("name") if why[0] == "internal"
                                 else code(ref) if why[0] == "requirement" else ref}
        out_ifaces.append(row)

    out_reqs = []
    for r in sorted(ir_rows, key=_sort_key):
        ir = r.get("ir_json") or {}
        out_reqs.append({
            "id": r["id"], "code": r.get("code") or r["id"], "text": r.get("text") or "",
            "text_fr": (ir.get("text_i18n") or {}).get("fr"),
            "origin": "rule" if is_generated(r) else (ir.get("origin") or "user"),
            "template_id": ir.get("template_id"), "icd_ref": ir.get("icd_ref"),
            "interface_ids": [x for x in dict.fromkeys([ir.get("interface_id"), *(ir.get("interface_ids") or [])]) if x],
            "covers_interface_ids": list(ir.get("covers_interface_ids") or []),
            "exchange_items": list(ir.get("exchange_item_ids") or []),
            "parents": [code(p) for p in r.get("parent_ids") or []],
            "allocation": (els.get(r.get("element_id") or "") or {}).get("name") or "",
            "method": r.get("verification_method"), "stage": r.get("verification_phase"),
            "status": r.get("status"), "review": ir.get("review"), "missing": list(ir.get("missing") or []),
            "tbd": bool(_TBD.search(r.get("text") or "")),
        })
    out_items = []
    for xid, x in sorted(items.items(), key=lambda kv: (kv[1].get("name") or "", kv[0])):
        out_items.append({"id": xid, "name": x.get("name") or "", "kind": x.get("kind"),
                          "description": x.get("description") or "",
                          "properties": dict(x.get("properties") or x.get("properties_json") or {}),
                          "interfaces": sorted(x_ifaces.get(xid, [])),
                          "requirements": sorted(code(rid) for rid in x_reqs.get(xid, set()))})
    try:
        sugg = await irs.compute_suggestions(study_id)
    except Exception:  # noqa: BLE001
        sugg = []
    status = irs.ird_status(live_ifaces, reqs)
    return {
        "interfaces": out_ifaces,
        "segment_interfaces": [i["id"] for i in out_ifaces if i["segment_interface"]],
        "requirements": out_reqs,
        "exchange_items": out_items,
        "suggestions": sugg,
        "status": {k: v for k, v in status.items() if k != "rows"},
        "counts": {"interfaces": len(out_ifaces), "with_requirements": sum(1 for i in out_ifaces if i["requirements"]),
                   "covered": sum(1 for i in out_ifaces if i["covered_by"]),
                   "interface_requirements": len(out_reqs),
                   "generated": sum(1 for r in out_reqs if r["origin"] == "rule"),
                   "exchange_items": len(out_items), "suggestions": len(sugg)},
    }


# ═══════════════════════════════════════════════════════════════════════
# Wave 3 (3.R1): element codes, function ↔ requirement links and coverage
# ═══════════════════════════════════════════════════════════════════════

#: v2 element codes (functions.yaml ``elements``) → how to find the tool element: (element
#: types, segments, name words). The import's ``element_map`` wins; the function import stores
#: the map it used on each function, so later lookups (ICD seats, coverage) reuse it.
ELEMENT_CODES: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
    "MIS": (("mission",), (), ()),
    "SSEG": (("segment",), ("space",), ()),
    "GSEG": (("segment",), ("ground",), ()),
    "LSEG": (("segment",), ("launch",), ()),
    "USEG": (("segment",), ("user", "science"), ()),
    "SCI": (("segment",), ("user", "science"), ()),
    "SCT": (("segment",), ("user", "science"), ()),
    "OPS": (("segment",), ("operations",), ()),
    "GS": (("segment",), ("ground",), ()),
    "SC": (("system",), ("space",), ()),
    "MCC": (("system",), ("ground",), ("mission control",)),
    "PAY": (("subsystem",), (), ("payload",)),
    "EPS": (("subsystem",), (), ("eps", "power")),
    "AOCS": (("subsystem",), (), ("aocs", "adcs", "attitude")),
    "COM": (("subsystem",), (), ("communication", "ttc", "tt&c")),
    "OBC": (("subsystem",), (), ("on-board computer", "obc", "data handling")),
    "THM": (("subsystem",), (), ("thermal",)),
    "STR": (("subsystem",), (), ("structure",)),
    "DIS": (("subsystem",), (), ("disposal", "drag sail", "deorbit")),
    "HAR": (("subsystem",), (), ("harness",)),
}


def resolve_element_code(code: str, elements: list[dict], element_map: dict[str, str] | None = None) -> str | None:
    """The tool element id of a v2 element code (``PAY``, ``SSEG`` …); None when unknown."""
    if not code:
        return None
    if element_map and element_map.get(code):
        return element_map[code]
    live = [e for e in elements if not e.get("deleted_at")]
    if any(e.get("id") == code for e in live):
        return code
    rule = ELEMENT_CODES.get(code.upper())
    if rule is None:
        hit = [e for e in live if (e.get("name") or "").strip().casefold() == code.casefold()]
        return hit[0]["id"] if len(hit) == 1 else None
    types, segs, words = rule
    cands = [e for e in live if e.get("element_type") in types
             and (not segs or (e.get("segment") or "") in segs)]
    if words:
        named = [e for e in cands if any((e.get("name") or "").casefold().startswith(w) for w in words)]
        if not named:
            named = [e for e in cands if any(w in (e.get("name") or "").casefold() for w in words)]
        cands = named
    if code.upper() == "SC" and len(cands) > 1:
        cands = [e for e in cands if any(c.get("parent_id") == e["id"] and c.get("element_type") == "subsystem"
                                         for c in live)] or cands
    return cands[0]["id"] if cands else None


async def element_code_map(study_id: str, elements: list[dict] | None = None) -> dict[str, str]:
    """Element code → element id for the study: the map the function import stored, completed by
    :func:`resolve_element_code` for every code in :data:`ELEMENT_CODES`."""
    from ..db import function_repo
    if elements is None:
        elements = _study_elements_list(study_id)
    out: dict[str, str] = {}
    try:
        for f in await function_repo.list_functions_by_study(study_id):
            ext = f.get("external_ids") or {}
            for c, e in zip(ext.get("allocation_codes") or [], ext.get("allocation") or []):
                if c and e:
                    out.setdefault(c, e)
    except Exception:  # noqa: BLE001 — no function table: resolve by name only
        logger.debug("no stored element codes for %s", study_id, exc_info=True)
    ids = {e["id"] for e in elements}
    out = {c: e for c, e in out.items() if e in ids}
    for c in ELEMENT_CODES:
        if c not in out:
            eid = resolve_element_code(c, elements)
            if eid:
                out[c] = eid
    return out


def _study_elements_list(study_id: str) -> list[dict]:
    from ..routers import elements as el
    return [e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


async def link_function_requirements(study_id: str) -> dict[str, int]:
    """``function_codes`` of the requirements become ``satisfies`` relations function →
    requirement (3.R1). The links of every row that carries codes are made exact; rows without
    codes keep the links a user drew. Codes no function has are reported."""
    from ..db import function_repo
    from ..db.relation_repo import sync_incoming
    from ..routers.requirements import ensure_requirements_loaded, study_requirements
    await ensure_requirements_loaded()
    by_code = {f.get("external_id"): f["id"] for f in await function_repo.list_functions_by_study(study_id)
               if f.get("external_id")}
    wanted: set[tuple[str, str]] = set()
    managed: set[str] = set()
    unknown: set[str] = set()
    for r in study_requirements(study_id):
        codes = r.get("function_codes") or []
        if not codes or not by_code:
            continue
        managed.add(r["id"])
        for c in codes:
            fid = by_code.get(c)
            if fid:
                wanted.add((fid, r["id"]))
            else:
                unknown.add(c)
    created, removed = await sync_incoming(study_id, "satisfies", "function", "requirement", wanted, managed,
                                           rationale="function_codes")
    return {"links": len(wanted), "created": created, "removed": removed, "rows": len(managed),
            "unknown_codes": sorted(unknown)}


async def set_requirement_functions(study_id: str, req: dict, function_ids: list[str]) -> dict:
    """The Requirements table's function picker: the functions (or processes) that satisfy
    ``req`` become exactly ``function_ids``; ``function_codes`` follows (the codes of the
    functions that have one)."""
    from ..db import function_repo
    from ..db.relation_repo import sync_incoming
    fns = {f["id"]: f for f in await function_repo.list_functions_by_study(study_id)}
    bad = [f for f in function_ids if f not in fns]
    if bad:
        raise ValueError(f"unknown function(s): {', '.join(bad)}")
    await sync_incoming(study_id, "satisfies", "function", "requirement",
                        {(f, req["id"]) for f in function_ids}, {req["id"]}, rationale="picker")
    codes = [fns[f].get("external_id") or fns[f].get("name") for f in function_ids]
    return {"function_ids": list(function_ids), "function_codes": [c for c in codes if c]}


def _is_spec_row(r: dict) -> bool:
    """A requirement row the function coverage counts: not a stakeholder need, an objective row
    or an interface row generated by rule IF-01 from a link (it traces to its interface)."""
    return (r.get("level") != "stakeholder" and not is_objective(r) and not is_generated(r)
            and r.get("status") != "retired")


async def function_coverage(study_id: str) -> dict[str, Any]:
    """Function ↔ requirement coverage (3.R1, SRR-EC-12, PRR-EC-03).

    Returns ``{functions, processes, leaves, leaves_allocated, leaves_without_requirement[],
    leaves_unallocated[], requirements, requirements_with_function, requirements_without_function[],
    allocation_warnings[], subsystems_without_requirement[], by_depth}``. A requirement counts as
    covered by a function when a ``satisfies`` relation links them (either direction); its
    allocation (``allocation_codes``, else ``element_id``) should sit under, or above, an element
    one of its functions (or their leaves) is allocated to, else a warning."""
    from ..db import function_repo
    from ..db.relation_repo import list_relations_by_study
    from ..routers.requirements import ensure_requirements_loaded, study_requirements
    await ensure_requirements_loaded()
    fns = await function_repo.list_functions_by_study(study_id)
    allocs = await function_repo.list_allocations_by_study(study_id)
    rels = await list_relations_by_study(study_id, kind="satisfies")
    els = {e["id"]: e for e in _study_elements_list(study_id)}
    codes = await element_code_map(study_id, list(els.values()))
    reqs = [r for r in study_requirements(study_id) if _is_spec_row(r)]
    req_ids = {r["id"] for r in reqs}
    fn_by = {f["id"]: f for f in fns}

    children: dict[str, list[str]] = {}
    for f in fns:
        if f.get("parent_id") in fn_by:
            children.setdefault(f["parent_id"], []).append(f["id"])
    procs = [f for f in fns if f.get("function_type") == "process"]
    funcs = [f for f in fns if f.get("function_type") != "process"]
    leaves = [f for f in funcs if f["id"] not in children]
    alloc_of: dict[str, set[str]] = {}
    for a in allocs:
        if a.get("element_id"):
            alloc_of.setdefault(a["function_id"], set()).add(a["element_id"])

    def under(fid: str, seen: set | None = None) -> set[str]:
        seen = seen if seen is not None else set()
        if fid in seen:
            return set()
        seen.add(fid)
        out = set(alloc_of.get(fid, set()))
        for c in children.get(fid, []):
            out |= under(c, seen)
        return out

    fn_reqs: dict[str, set[str]] = {}
    req_fns: dict[str, set[str]] = {}
    for rel in rels:
        if rel.get("source_kind") == "function" and rel.get("target_kind") == "requirement":
            f, r = rel["source_id"], rel["target_id"]
        elif rel.get("source_kind") == "requirement" and rel.get("target_kind") == "function":
            f, r = rel["target_id"], rel["source_id"]
        else:
            continue
        if f in fn_by and r in req_ids:
            fn_reqs.setdefault(f, set()).add(r)
            req_fns.setdefault(r, set()).add(f)

    def lineage(eid: str) -> set[str]:
        out, cur, n = set(), els.get(eid), 0
        while cur is not None and n < 30:
            out.add(cur["id"])
            cur, n = els.get(cur.get("parent_id") or ""), n + 1
        return out

    code_of = {f["id"]: f.get("external_id") or f.get("name") for f in fns}
    req_code = {r["id"]: r.get("code") or r["id"] for r in reqs}
    warnings = []
    for r in reqs:
        fs = req_fns.get(r["id"], set())
        if not fs:
            continue
        mine = {codes.get(c) for c in (r.get("allocation_codes") or [])} - {None}
        if not mine and r.get("element_id"):
            mine = {r["element_id"]}
        theirs: set[str] = set()
        for f in fs:
            theirs |= under(f)
        if not theirs:
            continue
        near: set[str] = set()
        for e in theirs:
            near |= lineage(e)                     # the function's elements and their parents
        odd = [e for e in mine if e not in near and not (lineage(e) & theirs)]
        if odd:
            warnings.append({"code": req_code[r["id"]], "requirement_id": r["id"],
                             "elements": sorted((els.get(e) or {}).get("name") or e for e in odd),
                             "functions": sorted(code_of[f] for f in fs)})
    subs = [e for e in els.values() if e.get("element_type") == "subsystem" and (e.get("segment") or "space") == "space"
            and e.get("in_scope") is not False]
    with_req: set[str] = set()
    for r in reqs:
        if r.get("element_id"):
            with_req.add(r["element_id"])
        for c in r.get("allocation_codes") or []:
            if codes.get(c):
                with_req.add(codes[c])
    depth: dict[int, int] = {}
    for f in funcs:
        depth[int(f.get("level") or 0)] = depth.get(int(f.get("level") or 0), 0) + 1
    return {
        "study_id": study_id,
        "functions": len(funcs), "processes": len(procs), "by_depth": {str(k): v for k, v in sorted(depth.items())},
        "leaves": len(leaves),
        "leaves_allocated": sum(1 for f in leaves if alloc_of.get(f["id"])),
        "leaves_unallocated": [code_of[f["id"]] for f in leaves if not alloc_of.get(f["id"])],
        "leaves_without_requirement": [code_of[f["id"]] for f in leaves if not fn_reqs.get(f["id"])],
        "requirements": len(reqs),
        "requirements_with_function": sum(1 for r in reqs if req_fns.get(r["id"])),
        "requirements_without_function": sorted(req_code[r["id"]] for r in reqs if not req_fns.get(r["id"])),
        "allocation_warnings": warnings,
        "subsystems": len(subs),
        "subsystems_without_requirement": sorted(e.get("name") or e["id"] for e in subs if e["id"] not in with_req),
        "per_function": {code_of[f]: sorted(req_code[r] for r in rs) for f, rs in fn_reqs.items()},
    }
