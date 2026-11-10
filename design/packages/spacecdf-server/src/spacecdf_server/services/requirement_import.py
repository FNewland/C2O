"""Bulk requirement import (W2.04, W2.09): a native YAML / JSON / CSV baseline into one study.

``POST /api/studies/{sid}/requirements/import`` (routers/relations.py) calls :func:`import_requirements`.

Input
-----
* The requirements-baseline YAML of the teaching missions (``requirements`` rows with ``id``,
  ``level``/``tool_level``, ``type``, ``text``, ``rationale``, ``parents``, ``objectives``,
  ``verification_method``, ``verification_phase``, ``owner_seat``, ``subsystem``, ``priority``,
  ``category``, ``source``, ``status``, ``threshold {op, value, unit}``, ``interface``, ``verifies``,
  ``open_item``; v2 adds ``function``, ``allocation`` (code lists), ``budget_ref``,
  ``verification_level``, ``verification_model``, ``verification_event``, ``acceptance``,
  ``open_item_note``), plus its ``stakeholder_needs`` (level ``stakeholder``) and ``objectives``
  (mission-level ``OBJ-*`` rows whose parents are the needs);
* the same as JSON, or a plain list of rows;
* CSV with one row per requirement and the same column names (lists such as ``parents`` are
  separated by ``;``, ``|`` or ``,``; ``threshold_op`` / ``threshold_value`` / ``threshold_unit``).

Parents are referenced **by code** (rows of the file, or live rows already in the study).

Behaviour
---------
* **Upsert by (study, code)**: a code the study already holds is updated in place (its id is
  kept); a new code gets the id ``"<study id>:<code>"`` (or ``REQ-<hex>`` when that is longer than
  32 characters or taken). Codes of another study are never touched.
* **All or nothing**: any row error (unknown level, operator, method, stage or priority, a parent
  code that does not exist, a duplicate code in the file) stops the import; nothing is written and
  the error report lists every problem. ``dry_run`` returns the same report and the planned
  changes without writing.
* **Relations**: further parents become ``derives`` relations, further objectives ``traces``
  relations to entity kind ``objective``, ``verifies`` lists ``verifies`` relations. They are made
  exact for every imported row (a parent removed from the file is unlinked).
* **Allocation by name** (W2.09): ``subsystem`` (or ``element``) is matched to an element of the
  study by name (case-insensitive), then by the aliases in :func:`resolve_element`
  (``Science Segment`` = the user segment, ``Harness``, ``Operations`` …), then by a unique name
  prefix; ``element_map`` in the request overrides.
* **Owner seats**: ``owner_seat`` → ``responsible_position``. PI rule: a requirement allocated to
  a disposal device (drag sail, deorbit timer) is owned by the Propulsion seat
  (``propulsion_engineer``), whatever the file says.
* **No automatic proposals**: no element or interface route runs, and the interface-requirement
  generator is held off while the rows are written, so the import adds no ``IR-*`` rows.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import re
import time
from typing import Any
from uuid import uuid4

import yaml

from spacecdf_common.models.requirement import (
    LEVELS, PRIORITIES, THRESHOLD_OPS, VERIFICATION_LEVELS, VERIFICATION_METHODS, VERIFICATION_STAGES,
    normalise_method,
)

logger = logging.getLogger(__name__)

#: Fields the import manages; a row only changes the fields it carries.
MANAGED = ("level", "text", "rationale", "req_type", "category", "element_id", "parent_id",
           "derived_from_requirement_id", "objective_id", "verification_method", "verification_methods",
           "verification_phase", "verification_level", "responsible_position", "priority", "source_ref",
           "status", "threshold_op", "threshold_value", "threshold_unit", "open_item", "ir_json",
           # wave 3, step 0 (v2 baseline)
           "acceptance", "verification_model", "verification_event", "budget_ref", "open_item_note",
           "function_codes", "allocation_codes")

#: v2 fields with no value on stakeholder-need and objective rows.
V2_EMPTY = {"acceptance": None, "verification_model": None, "verification_event": None, "budget_ref": None,
            "open_item_note": None, "function_codes": [], "allocation_codes": []}

OBJECTIVE_PRIORITY = {"primary": 1, "secondary": 2, "constraint": 1, "tertiary": 3}
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SPLIT = re.compile(r"[;|,]\s*")
PROPULSION_SEAT = "propulsion_engineer"


class ImportError_(ValueError):
    """The document cannot be read at all (not YAML/JSON/CSV, no rows)."""


# ═══════════════════════════════════════════════════════════════════════
# Parsing
# ═══════════════════════════════════════════════════════════════════════

def parse_document(content: Any, fmt: str | None = None) -> dict:
    """``content``: a dict / list (already parsed) or text in ``fmt`` (yaml | json | csv;
    guessed when None). Returns ``{"requirements": [...], "objectives": [...],
    "stakeholder_needs": [...]}``."""
    if isinstance(content, (bytes, bytearray)):
        content = content.decode("utf-8-sig")
    if isinstance(content, str):
        text = content
        f = (fmt or "").lower()
        if not f:
            first = text.lstrip()[:1]
            head = text.lstrip().split("\n", 1)[0]
            f = "json" if first in "[{" else ("csv" if head.count(",") >= 2 and ":" not in head else "yaml")
        if f == "csv":
            rows = [dict(r) for r in csv.DictReader(io.StringIO(text))]
            content = {"requirements": rows}
        elif f == "json":
            content = json.loads(text)
        elif f in ("yaml", "yml"):
            content = yaml.safe_load(text)
        else:
            raise ImportError_(f"unknown format {fmt!r}: yaml, json or csv")
    if isinstance(content, list):
        content = {"requirements": content}
    if not isinstance(content, dict):
        raise ImportError_("the document holds no requirement list")
    reqs = content.get("requirements")
    if not isinstance(reqs, list):
        raise ImportError_("the document has no 'requirements' list")
    return {"requirements": reqs, "objectives": list(content.get("objectives") or []),
            "stakeholder_needs": list(content.get("stakeholder_needs") or [])}


def _list(v: Any) -> list[str]:
    if v is None or v == "":
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in _SPLIT.split(str(v)) if x.strip()]


def _blank(v: Any) -> Any:
    return None if v is None or (isinstance(v, str) and v.strip() == "") else v


def _bool(v: Any) -> bool | None:
    v = _blank(v)
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "y", "oui")


def threshold_fields(th: dict | None) -> tuple[str | None, Any, str | None]:
    """(op, value, unit) in the tool's model: a date becomes ``before``/``after``, a pair or a
    ``{min, max}`` becomes ``in_range``."""
    th = th or {}
    op, value, unit = _blank(th.get("op")), _blank(th.get("value")), _blank(th.get("unit"))
    if op is None and value is None:
        return None, None, unit
    if isinstance(value, (list, tuple)) and len(value) == 2:
        value, op = {"min": value[0], "max": value[1]}, "in_range"
    if isinstance(value, dict) and ("min" in value or "max" in value):
        op = "in_range"
    is_date = (str(unit or "").lower() == "date") or (isinstance(value, str) and bool(_DATE.match(value.strip())))
    if is_date and op in ("<=", "<", "before"):
        op = "before"
    elif is_date and op in (">=", ">", "after"):
        op = "after"
    if hasattr(value, "isoformat"):
        value = value.isoformat()
    if str(unit or "").lower() == "date":
        unit = None
    return op, value, unit


def normalise_row(r: dict) -> dict:
    """One file row → the tool's field names (values not yet validated)."""
    g = lambda *ks: next((r[k] for k in ks if k in r and _blank(r[k]) is not None), None)  # noqa: E731
    th = r.get("threshold") if isinstance(r.get("threshold"), dict) else {
        "op": g("threshold_op"), "value": g("threshold_value"), "unit": g("threshold_unit")}
    op, value, unit = threshold_fields(th)
    level = g("level")
    if level not in LEVELS:
        level = g("tool_level") or level
    methods = _list(g("verification_methods")) or _list(g("verification_method"))
    iface = r.get("interface") if isinstance(r.get("interface"), dict) else None
    if iface is None and g("icd_ref", "endpoints"):
        iface = {"icd_ref": g("icd_ref"), "endpoints": _list(g("endpoints"))}
    out = {
        "code": str(g("id", "code") or "").strip(),
        "level": level,
        "text": g("text") or "",
        "rationale": g("rationale"),
        "req_type": g("type", "req_type"),
        "category": g("category"),
        "element_name": g("subsystem", "element", "allocated_to"),
        "parents": _list(g("parents", "parent", "parent_codes")),
        "objectives": _list(g("objectives", "objective_ids", "objective")),
        "verifies": _list(g("verifies")),
        "verification_methods": methods,
        "verification_phase": g("verification_phase", "verification_stage", "stage"),
        "verification_level": g("verification_level"),
        "responsible_position": g("owner_seat", "responsible_position", "owner"),
        "priority": g("priority"),
        "source_ref": g("source", "source_ref"),
        "status": g("status") or "draft",
        "threshold_op": op, "threshold_value": value, "threshold_unit": unit,
        "open_item": _bool(r.get("open_item")),
        "interface": iface,
        # wave 3, step 0: v2 fields (``function`` and ``allocation`` are code lists)
        "acceptance": g("acceptance"),
        "verification_model": g("verification_model"),
        "verification_event": g("verification_event"),
        "budget_ref": g("budget_ref"),
        "open_item_note": g("open_item_note"),
        "function_codes": _list(g("function", "functions", "function_codes")),
        "allocation_codes": _list(g("allocation", "allocation_codes")),
    }
    return out


def need_rows(needs: list[dict]) -> list[dict]:
    out = []
    for n in needs:
        out.append({
            "code": str(n.get("id") or n.get("code") or "").strip(), "level": "stakeholder",
            "text": n.get("need") or n.get("text") or "", "rationale": n.get("role"),
            "req_type": None, "category": "stakeholder", "element_name": None, "parents": [],
            "objectives": [], "verifies": [], "verification_methods": [], "verification_phase": None,
            "verification_level": None, "responsible_position": None, "priority": None,
            "source_ref": n.get("stakeholder"), "status": n.get("status") or "draft",
            "threshold_op": None, "threshold_value": None, "threshold_unit": None, "open_item": None,
            "interface": None, **V2_EMPTY,
        })
    return out


def objective_rows(objectives: list[dict], need_codes: set[str]) -> list[dict]:
    out = []
    for o in objectives:
        oid = str(o.get("id") or "").strip()
        text = str(o.get("text") or "").strip()
        out.append({
            "code": str(o.get("code") or f"OBJ-{oid}").strip(), "level": "mission",
            "text": f"The mission shall {text[:1].lower()}{text[1:]}" if text else "",
            "rationale": o.get("measure") or o.get("measurable_criterion"),
            "req_type": "functional", "category": "objective", "element_name": o.get("subsystem"),
            "parents": [n for n in _list(o.get("needs")) if n in need_codes], "objectives": [oid],
            # an objective is closed out by review (R) of the evidence of the requirements below it:
            # in orbit for a mission objective, at acceptance for a programmatic constraint (QR-EC-01
            # asks every row for a method and a close-out stage); the document's own values win
            "verifies": [], "verification_methods": _list(o.get("verification_method")) or ["R"],
            "verification_phase": o.get("verification_phase")
            or ("AR" if str(o.get("priority") or "").lower() == "constraint" else "IOV"), "verification_level": None,
            "responsible_position": o.get("owner_seat") or "customer",
            "priority": OBJECTIVE_PRIORITY.get(str(o.get("priority") or "").lower(), _blank(o.get("priority"))),
            "source_ref": o.get("source"), "status": o.get("status") or "draft",
            "threshold_op": None, "threshold_value": None, "threshold_unit": None, "open_item": None,
            "interface": None, **V2_EMPTY,
        })
    return out


# ═══════════════════════════════════════════════════════════════════════
# Element and seat mapping
# ═══════════════════════════════════════════════════════════════════════

_ALIASES = {
    "science segment": ("segment", ("user", "science")),
    "user segment": ("segment", ("user", "science")),
    "user/science segment": ("segment", ("user", "science")),
    "operations": ("segment", ("operations",)),
    "operations segment": ("segment", ("operations",)),
    "space segment": ("segment", ("space",)),
    "ground segment": ("segment", ("ground",)),
    "launch segment": ("segment", ("launch",)),
}


def resolve_element(name: str | None, elements: list[dict], element_map: dict[str, str] | None = None) -> str | None:
    """Element id for a requirement's ``subsystem`` name (see the module doc)."""
    if not name:
        return None
    if element_map and name in element_map:
        return element_map[name] or None
    key = name.strip().casefold()
    live = [e for e in elements if not e.get("deleted_at")]
    exact = [e for e in live if (e.get("name") or "").strip().casefold() == key]
    if exact:
        # the highest one in the tree wins (a subsystem over a component of the same name)
        order = {"mission": 0, "segment": 1, "system": 2, "subsystem": 3}
        return sorted(exact, key=lambda e: order.get(e.get("element_type") or "", 9))[0]["id"]
    alias = _ALIASES.get(key)
    if alias:
        etype, segs = alias
        hit = [e for e in live if e.get("element_type") == etype and (e.get("segment") or "") in segs]
        if len(hit) == 1:
            return hit[0]["id"]
    if key == "harness":
        hit = [e for e in live if e.get("element_type") == "subsystem" and "harness" in (e.get("name") or "").casefold()]
        if len(hit) == 1:
            return hit[0]["id"]
    pref = [e for e in live if (e.get("name") or "").casefold().startswith(key)
            and e.get("element_type") in ("segment", "system", "subsystem")]
    if len(pref) == 1:
        return pref[0]["id"]
    return None


def is_disposal_device(el: dict | None, elements: dict[str, dict] | None = None) -> bool:
    """A drag sail, deorbit device or its disposal subsystem (PI rule: the Propulsion seat owns it)."""
    if not el:
        return False
    name = (el.get("name") or "").casefold()
    perf = el.get("performance") or el.get("performance_json") or {}
    cat = str((perf or {}).get("category") or el.get("category") or "").casefold()
    kb = str(el.get("kb_component_id") or "").casefold()
    dom = str(el.get("subsystem_domain") or "").casefold()
    return (kb.startswith("deorb") or cat in ("deorbit_device", "drag_sail") or dom in ("deorbit", "disposal")
            or "drag sail" in name or "deorbit" in name or name.startswith("disposal"))


def owner_seat_for(element_id: str | None, elements: dict[str, dict], given: str | None) -> str | None:
    """The owner seat of a requirement: the file's seat, except the PI rule for disposal devices."""
    el = elements.get(element_id or "")
    if el is not None:
        cur, seen = el, set()
        while cur is not None and cur.get("id") not in seen:
            seen.add(cur.get("id"))
            if is_disposal_device(cur, elements):
                return PROPULSION_SEAT
            if cur.get("element_type") in ("subsystem", "system", "segment", "mission"):
                break
            cur = elements.get(cur.get("parent_id") or "")
    return given


# ═══════════════════════════════════════════════════════════════════════
# Import
# ═══════════════════════════════════════════════════════════════════════

def _err(errors: list, i: int, code: str, field: str, msg: str) -> None:
    errors.append({"row": i, "code": code, "field": field, "message": msg})


def _validate(i: int, row: dict, errors: list) -> None:
    code = row["code"]
    if not code:
        _err(errors, i, code, "id", "missing code")
    elif len(code) > 32:
        _err(errors, i, code, "id", "code longer than 32 characters")
    if row["level"] not in LEVELS:
        _err(errors, i, code, "level", f"level {row['level']!r} is not one of {list(LEVELS)}")
    if not str(row["text"] or "").strip():
        _err(errors, i, code, "text", "empty text")
    if row["threshold_op"] is not None and row["threshold_op"] not in THRESHOLD_OPS:
        _err(errors, i, code, "threshold", f"operator {row['threshold_op']!r} is not one of {list(THRESHOLD_OPS)}")
    ms = []
    for m in row["verification_methods"]:
        nm = normalise_method(m)
        if nm not in VERIFICATION_METHODS:
            _err(errors, i, code, "verification_method", f"method {m!r} is not one of {list(VERIFICATION_METHODS)} (D = T)")
        elif nm not in ms:
            ms.append(nm)
    row["verification_methods"] = ms
    st = _blank(row["verification_phase"])
    if st is not None:
        st = str(st).strip().upper()
        if st not in VERIFICATION_STAGES:
            _err(errors, i, code, "verification_phase", f"stage {st!r} is not one of {list(VERIFICATION_STAGES)}")
    row["verification_phase"] = st
    if row["verification_level"] is not None and row["verification_level"] not in VERIFICATION_LEVELS:
        _err(errors, i, code, "verification_level", f"{row['verification_level']!r} is not one of {list(VERIFICATION_LEVELS)}")
    p = _blank(row["priority"])
    if p is not None:
        try:
            p = int(p)
        except (TypeError, ValueError):
            p = -1
        if p not in PRIORITIES:
            _err(errors, i, code, "priority", f"priority {row['priority']!r} is not one of {list(PRIORITIES)}")
    row["priority"] = p


def _same(field: str, a: Any, b: Any) -> bool:
    from ..db.requirement_repo import normalise_threshold_value as n
    if field == "threshold_value":
        a, b = n(a), n(b)
    a = None if a in ("", [], {}) else a
    b = None if b in ("", [], {}) else b
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


async def import_requirements(study_id: str, doc: Any, *, fmt: str | None = None, dry_run: bool = False,
                              element_map: dict[str, str] | None = None, include_needs: bool = True,
                              include_objectives: bool = True) -> dict:
    """Import a baseline into ``study_id``. Returns the report (see the module doc). Raises
    ``ImportError_`` when the document cannot be read."""
    from ..db.relation_repo import sync_relations
    from ..db.requirement_repo import (
        db_create_requirements, db_update_requirements, normalise_threshold_value,
    )
    from ..routers import elements as el_router
    from ..routers import requirements as rr
    from . import interface_requirements as irs

    t0 = time.perf_counter()
    await rr.ensure_requirements_loaded()
    parsed = parse_document(doc, fmt)
    needs = need_rows(parsed["stakeholder_needs"]) if include_needs else []
    objs = objective_rows(parsed["objectives"], {n["code"] for n in needs}) if include_objectives else []
    rows = needs + objs + [normalise_row(r) for r in parsed["requirements"] if isinstance(r, dict)]

    errors: list[dict] = []
    warnings: list[str] = []
    seen: dict[str, int] = {}
    for i, row in enumerate(rows):
        _validate(i, row, errors)
        if row["code"] in seen:
            _err(errors, i, row["code"], "id", f"duplicate code (also row {seen[row['code']]})")
        seen.setdefault(row["code"], i)

    existing = {r["code"]: r for r in rr.study_requirements(study_id) if r.get("code")}
    file_codes = set(seen)
    elements = [e for e in el_router._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    els_by_id = {e["id"]: e for e in elements}

    # ids: existing rows keep theirs, new rows get "<study>:<code>"
    ids: dict[str, str] = {c: r["id"] for c, r in existing.items()}
    taken = set(rr._requirements)
    for row in rows:
        c = row["code"]
        if c in ids or not c:
            continue
        cand = f"{study_id}:{c}"
        if len(cand) > 32 or cand in taken:
            cand = f"REQ-{uuid4().hex[:12]}"
        ids[c] = cand
        taken.add(cand)

    for i, row in enumerate(rows):
        for p in row["parents"]:
            if p not in file_codes and p not in existing:
                _err(errors, i, row["code"], "parents", f"parent {p!r} is not in the file or the study")
            elif p == row["code"]:
                _err(errors, i, row["code"], "parents", "a requirement cannot be its own parent")
        for v in row["verifies"]:
            if v not in file_codes and v not in existing:
                _err(errors, i, row["code"], "verifies", f"verified requirement {v!r} is not in the file or the study")

    # build the target state
    planned: list[tuple[dict, dict | None]] = []      # (new state, current or None)
    unallocated: list[str] = []
    seat_overrides: list[str] = []
    wanted_rel: list[dict] = []
    owned: set[tuple[str, str, str]] = set()
    by_level: dict[str, int] = {}
    for row in rows:
        c = row["code"]
        if not c:
            continue
        rid = ids[c]
        cur = existing.get(c)
        eid = resolve_element(row["element_name"], elements, element_map)
        if row["element_name"] and not eid:
            unallocated.append(c)
        seat = owner_seat_for(eid, els_by_id, row["responsible_position"])
        if seat != row["responsible_position"]:
            seat_overrides.append(c)
        parents = [ids[p] for p in row["parents"] if p in ids]
        objectives = row["objectives"]
        ms = row["verification_methods"]
        ir = dict((cur or {}).get("ir_json") or {})
        if row["interface"]:
            ir.update({"origin": ir.get("origin") or "import", "icd_ref": row["interface"].get("icd_ref"),
                       "endpoint_names": _list(row["interface"].get("endpoints"))})
        new = {
            "id": rid, "study_id": study_id, "code": c, "level": row["level"], "text": str(row["text"]).strip(),
            "rationale": _blank(row["rationale"]), "req_type": _blank(row["req_type"]),
            "category": _blank(row["category"]), "element_id": eid,
            "parent_id": parents[0] if parents else None,
            "derived_from_requirement_id": parents[0] if parents else None,
            "objective_id": objectives[0] if objectives else None,
            "verification_method": ms[0] if ms else None, "verification_methods": ms or None,
            "verification_phase": row["verification_phase"], "verification_level": _blank(row["verification_level"]),
            "responsible_position": _blank(seat), "priority": row["priority"],
            "source_ref": _blank(row["source_ref"]), "status": row["status"] or "draft",
            "threshold_op": row["threshold_op"], "threshold_value": normalise_threshold_value(row["threshold_value"]),
            "threshold_unit": _blank(row["threshold_unit"]), "open_item": row["open_item"],
            "ir_json": ir or None,
            "acceptance": _blank(row["acceptance"]), "verification_model": _blank(row["verification_model"]),
            "verification_event": _blank(row["verification_event"]), "budget_ref": _blank(row["budget_ref"]),
            "open_item_note": _blank(row["open_item_note"]),
            "function_codes": list(row["function_codes"]) or None,
            "allocation_codes": list(row["allocation_codes"]) or None,
        }
        if new["status"] == "retired":
            new["status"] = "draft"
        planned.append((new, cur))
        by_level[new["level"]] = by_level.get(new["level"], 0) + 1
        for p in parents[1:]:
            wanted_rel.append({"kind": "derives", "source_kind": "requirement", "source_id": rid,
                               "target_kind": "requirement", "target_id": p, "rationale": "import: further parent"})
        for o in objectives[1:]:
            wanted_rel.append({"kind": "traces", "source_kind": "requirement", "source_id": rid,
                               "target_kind": "objective", "target_id": o, "rationale": "import: further objective"})
        for v in row["verifies"]:
            if v in ids:
                wanted_rel.append({"kind": "verifies", "source_kind": "requirement", "source_id": rid,
                                   "target_kind": "requirement", "target_id": ids[v], "rationale": "import"})
        owned |= {("derives", rid, "requirement"), ("traces", rid, "objective"), ("verifies", rid, "requirement")}

    to_create = [n for n, cur in planned if cur is None]
    to_update = []
    for n, cur in planned:
        if cur is None:
            continue
        diff = [k for k in MANAGED if not _same(k, n.get(k), cur.get(k))]
        if diff:
            to_update.append((n, cur, diff))

    report: dict[str, Any] = {
        "study_id": study_id, "dry_run": dry_run, "ok": not errors, "rows": len(rows),
        "created": len(to_create), "updated": len(to_update),
        "unchanged": len(planned) - len(to_create) - len(to_update),
        "relations_created": 0, "relations_removed": 0,
        "by_level": by_level, "errors": errors, "warnings": warnings,
        "unallocated": unallocated, "owner_seat_overrides": seat_overrides,
        "changes": [{"code": n["code"], "fields": d} for n, _, d in to_update][:500],
        "id_map": {c: ids[c] for c in seen if c in ids},
    }
    if unallocated:
        warnings.append(f"{len(unallocated)} row(s) name an element the study does not have: "
                        + ", ".join(unallocated[:12]) + (" …" if len(unallocated) > 12 else ""))
    if errors or dry_run:
        report["seconds"] = round(time.perf_counter() - t0, 3)
        return report

    # write: parents first (self-referencing foreign key), one transaction each
    order = {n["id"]: n for n in to_create}
    done: set[str] = set()
    ordered: list[dict] = []

    def visit(n: dict, depth: int = 0) -> None:
        if n["id"] in done or depth > 64:
            return
        p = n.get("parent_id")
        if p in order:
            visit(order[p], depth + 1)
        done.add(n["id"])
        ordered.append(n)

    for n in to_create:
        visit(n)
    token = irs._busy.set(True)          # no interface-requirement proposals during the import
    try:
        await db_create_requirements(ordered)
        for n in ordered:
            rr._requirements[n["id"]] = n
        await db_update_requirements([{**cur, **n} for n, cur, _ in to_update])
        for n, cur, _ in to_update:
            cur.update(n)
        rc, rm = await sync_relations(study_id, wanted_rel, owned)
    finally:
        irs._busy.reset(token)
    report["relations_created"], report["relations_removed"] = rc, rm
    report["seconds"] = round(time.perf_counter() - t0, 3)
    from ..routers._arcadia_events import broadcast_mutation
    await broadcast_mutation(study_id, "requirements_imported", "study", study_id,
                             {k: report[k] for k in ("created", "updated", "unchanged")})
    return report


def coverage(study_id: str, reqs: list[dict], extra_parents: dict[str, list[str]],
             extra_objectives: dict[str, list[str]], objective_ids: list[str]) -> dict[str, dict]:
    """Objective coverage (W2.03): per objective, the rows that name it (``objective_id`` or a
    ``traces`` relation) and the rows whose parent chain reaches one of those."""
    by_id = {r["id"]: r for r in reqs}
    children: dict[str, list[str]] = {}
    for r in reqs:
        first = r.get("parent_id") or r.get("derived_from_requirement_id")
        for p in ([first] if first else []) + extra_parents.get(r["id"], []):
            if p in by_id:
                children.setdefault(p, []).append(r["id"])
    out: dict[str, dict] = {}
    for oid in objective_ids:
        direct = {r["id"] for r in reqs
                  if r.get("objective_id") == oid or oid in extra_objectives.get(r["id"], [])}
        reach: set[str] = set()
        stack = [rid for rid in direct]
        while stack:
            rid = stack.pop()
            for c in children.get(rid, []):
                if c not in reach and c not in direct:
                    reach.add(c)
                    stack.append(c)
        out[oid] = {"direct": len(direct), "reached": len(direct | reach)}
    return out
