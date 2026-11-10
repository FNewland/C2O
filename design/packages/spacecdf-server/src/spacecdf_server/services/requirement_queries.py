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
