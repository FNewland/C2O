"""Allocation requirements kept in step with the allocation ledger (wave 3, 3.R3; rule AR-01).

"Whenever a budget is allocated to an element, a requirement states the allocation, and vice
versa" (the IF-01 pattern applied to budgets).

* **Covered.** A ledger line (``allocation_ledger``, 3.A2) is *covered* by the requirement whose
  ``budget_ref`` names the same budget and element (``mass.allocations.PAY`` for the PAY mass
  line; the line's own ``budget_ref`` or ``requirement_code`` when it carries one), or whose
  ``threshold_param_path`` checks that element's figure. The v2 baseline already holds one row per
  allocation, so it gets no new row.
* **Proposed.** A line with a non-zero value and no covering row gets a draft row
  ``AR-<BUDGET>-<ELEM>`` (origin ``rule:AR-01``), allocated to the element, with the ledger value
  as its threshold and, as parent, the system budget row of that budget (``SYS-BUD-*`` whose
  ``budget_ref`` is ``<budget>.closure``, else the system row whose text holds most of the trace
  words). A nil allocation (0 W on the structure) needs no requirement.
* **Stale.** When a line's value no longer equals the covering row's threshold, the row is marked
  ``external_ids.allocation_sync = {state: "stale", proposed_value, ledger_value, row_value,
  line_id, at}`` and the change is logged (seat event ``allocation_changed``). The owner accepts
  (the threshold takes the ledger value) or dismisses it.
* **Retired.** A covering row whose line was deleted is marked ``state: "retired"`` ("allocation
  retired"); the owner retires the row or keeps it.

:func:`sync` is idempotent; A's ledger routes call it after each change (hand-off), and
``POST /studies/{sid}/requirements/allocation-sync`` runs it on demand.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

ORIGIN = "rule:AR-01"
#: ledger budget type -> (budget_ref family, quantity words EN, FR, unit, path template)
BUDGETS: dict[str, dict[str, Any]] = {
    "mass": {"ref": "mass.allocations.{code}", "abbr": "MASS", "unit": "kg",
             "en": "mass, current best estimate plus maturity margin,", "fr": "masse, estimation actuelle plus marge de maturité,",
             "path": "rollup.mass.{code}.with_maturity_kg", "closure": "mass.closure", "words": ("mass", "allocation")},
    "power_avg": {"ref": "power.allocations.{code}", "abbr": "PWR", "unit": "W",
                  "en": "orbit-average power, including maturity margin,", "fr": "puissance moyenne orbitale, marge de maturité comprise,",
                  "path": "rollup.power.{code}.orbit_average_with_maturity_w", "closure": "power.closure",
                  "words": ("power", "allocation", "orbit-average")},
    "power_peak": {"ref": "power.peak_allocations.{code}", "abbr": "PPK", "unit": "W",
                   "en": "peak power", "fr": "puissance de crête", "path": "modes.peak.{code}.power_w",
                   "closure": "power.closure", "words": ("power", "peak")},
    "power_mode": {"ref": "power.mode_allocations.{code}.{mode}", "abbr": "PMD", "unit": "W",
                   "en": "power in the {mode} mode", "fr": "puissance en mode {mode}", "path": "modes.{mode}.{code}.power_w",
                   "closure": "power.closure", "words": ("power", "mode")},
    "data": {"ref": "data.allocations.{mode}", "abbr": "DAT", "unit": "MB/day",
             "en": "daily data volume", "fr": "volume de données quotidien", "path": None,
             "closure": "data", "words": ("data", "volume")},
}


def _num(v: Any) -> float | None:
    from ..db.requirement_repo import normalise_threshold_value
    v = normalise_threshold_value(v)
    try:
        v = json.loads(v) if isinstance(v, str) else v
        return float(v) if v is not None and not isinstance(v, bool) else None
    except (TypeError, ValueError):
        return None


def line_ref(line: dict, code: str | None) -> str | None:
    """The ``budget_ref`` a ledger line stands for (``mass.allocations.EPS``)."""
    b = BUDGETS.get(line.get("budget_type") or "")
    if b is None or not code:
        return None
    mode = line.get("mode_key") or ""
    if "{mode}" in b["ref"] and not mode:
        return None
    return b["ref"].format(code=code, mode=mode)


async def _ledger(study_id: str) -> list[dict]:
    from sqlalchemy import select
    from ..db._arcadia_common import get_session_factory
    from ..db.models_alloc import AllocationLedgerRow
    async with get_session_factory()() as s:
        rows = (await s.execute(select(AllocationLedgerRow).where(AllocationLedgerRow.study_id == study_id)
                                .order_by(AllocationLedgerRow.order))).scalars().all()
    return [{c.name: getattr(r, c.name) for c in AllocationLedgerRow.__table__.columns} for r in rows]


def _covering(line: dict, ref: str | None, reqs: list[dict], code: str | None) -> dict | None:
    by_code = {r.get("code"): r for r in reqs}
    if line.get("requirement_code") and line["requirement_code"] in by_code:
        return by_code[line["requirement_code"]]
    if line.get("requirement_id"):
        hit = next((r for r in reqs if r["id"] == line["requirement_id"]), None)
        if hit:
            return hit
    refs = {x for x in (ref, line.get("budget_ref")) if x}
    hits = [r for r in reqs if r.get("budget_ref") in refs and r.get("threshold_op") in ("<=", "<")]
    if hits:
        return sorted(hits, key=lambda r: r.get("code") or "")[0]
    b = BUDGETS.get(line.get("budget_type") or "")
    if b and b.get("path") and code:
        path = b["path"].format(code=code, mode=line.get("mode_key") or "")
        hits = [r for r in reqs if r.get("threshold_param_path") == path]
        if hits:
            return sorted(hits, key=lambda r: r.get("code") or "")[0]
    return None


def _parent(btype: str, reqs: list[dict]) -> dict | None:
    b = BUDGETS[btype]
    sys_rows = [r for r in reqs if r.get("level") == "system"]
    hit = [r for r in sys_rows if r.get("budget_ref") == b["closure"]]
    if hit:
        return hit[0]
    def score(r: dict) -> int:
        t = (r.get("text") or "").lower()
        return sum(1 for w in b["words"] if re.search(rf"\b{re.escape(w)}\b", t))
    best = sorted(sys_rows, key=lambda r: (-score(r), r.get("code") or ""))
    return best[0] if best and score(best[0]) else None


async def status(study_id: str) -> dict[str, Any]:
    """Per ledger line: its covering requirement and the sync state (read-only)."""
    from ..routers.requirements import ensure_requirements_loaded, study_requirements
    from .requirement_queries import _study_elements_list, element_code_map
    await ensure_requirements_loaded()
    reqs = study_requirements(study_id)
    elements = _study_elements_list(study_id)
    codes = await element_code_map(study_id, elements)
    code_of = {eid: c for c, eid in codes.items()}
    lines = await _ledger(study_id)
    out = []
    covered_ids: set[str] = set()
    for ln in lines:
        if ln.get("line_kind") != "allocation":
            continue
        code = ln.get("element_code") or code_of.get(ln.get("element_id") or "")
        ref = line_ref(ln, code)
        cov = _covering(ln, ref, reqs, code)
        row_value = _num(cov.get("threshold_value")) if cov else None
        state = "covered" if cov else ("nil" if not ln.get("value") else "uncovered")
        if cov:
            covered_ids.add(cov["id"])
            if ln.get("value") is not None and row_value is not None and abs(float(ln["value"]) - row_value) > 1e-9:
                state = "stale"
        out.append({"line_id": ln["id"], "budget_type": ln.get("budget_type"), "element_code": code,
                    "mode_key": ln.get("mode_key"), "value": ln.get("value"), "unit": ln.get("unit"),
                    "status": ln.get("status"), "budget_ref": ref, "requirement_id": cov["id"] if cov else None,
                    "requirement_code": cov.get("code") if cov else None, "row_value": row_value, "state": state})
    # rows whose allocation line is gone: a line of the same budget exists for other elements
    types_present = {ln.get("budget_type") for ln in lines if ln.get("line_kind") == "allocation"}
    retired = []
    for r in reqs:
        ref = str(r.get("budget_ref") or "")
        for btype, b in BUDGETS.items():
            if btype not in types_present or "{mode}" in b["ref"]:
                continue
            prefix = b["ref"].split("{code}")[0]
            if ref.startswith(prefix) and ref[len(prefix):].isalnum() and r["id"] not in covered_ids \
                    and r.get("status") != "retired":
                retired.append({"requirement_id": r["id"], "requirement_code": r.get("code"), "budget_ref": ref})
    return {"study_id": study_id, "lines": out, "retired": retired,
            "counts": {"lines": len(out), "covered": sum(1 for x in out if x["state"] in ("covered", "stale")),
                       "uncovered": sum(1 for x in out if x["state"] == "uncovered"),
                       "stale": sum(1 for x in out if x["state"] == "stale"),
                       "nil": sum(1 for x in out if x["state"] == "nil"), "retired": len(retired)}}


def _next_code(abbr: str, code: str, taken: set[str]) -> str:
    base = f"AR-{abbr}-{code}"
    if base not in taken:
        return base
    i = 2
    while f"{base}-{i}" in taken:
        i += 1
    return f"{base}-{i}"


async def sync(study_id: str, *, create: bool = True) -> dict[str, Any]:
    """Apply AR-01 (see the module doc). Returns ``{created[], stale[], retired[], cleared[]}``."""
    from ..db.requirement_repo import db_create_requirement, db_update_requirement
    from ..routers.requirements import _requirements, study_requirements
    from .requirement_queries import _study_elements_list, element_code_map
    st = await status(study_id)
    reqs = study_requirements(study_id)
    els = {e["id"]: e for e in _study_elements_list(study_id)}
    codes = await element_code_map(study_id, list(els.values()))
    now = datetime.now(timezone.utc).isoformat()
    created, stale, retired, cleared = [], [], [], []
    taken = {r.get("code") for r in reqs}
    marked: set[str] = set()
    for ln in st["lines"]:
        rid = ln["requirement_id"]
        if ln["state"] == "uncovered" and create:
            b = BUDGETS.get(ln["budget_type"] or "")
            eid = codes.get(ln["element_code"] or "")
            if b is None or eid is None:
                continue
            el = els.get(eid) or {}
            mode = ln.get("mode_key") or ""
            parent = _parent(ln["budget_type"], reqs)
            code = _next_code(b["abbr"], ln["element_code"], taken)
            taken.add(code)
            val = float(ln["value"])
            qty_en, qty_fr = b["en"].format(mode=mode), b["fr"].format(mode=mode)
            name = el.get("name") or ln["element_code"]
            rid_new = f"{study_id}:{code}"
            if len(rid_new) > 32 or rid_new in _requirements:
                from uuid import uuid4
                rid_new = f"REQ-{uuid4().hex[:12]}"
            req = {
                "id": rid_new,
                "study_id": study_id, "code": code, "level": "subsystem", "req_type": "performance",
                "category": "budgets", "status": "draft",
                "text": f"The {name} {qty_en} shall not exceed its allocation of {val:g} {ln.get('unit') or b['unit']}.",
                "rationale": f"Allocation ledger line ({ln['budget_type']}, {ln['element_code']}); rule AR-01.",
                "element_id": eid, "parent_id": parent["id"] if parent else None,
                "derived_from_requirement_id": parent["id"] if parent else None,
                "threshold_op": "<=", "threshold_value": json.dumps(val), "threshold_unit": ln.get("unit") or b["unit"],
                "threshold_param_path": b["path"].format(code=ln["element_code"], mode=mode) if b.get("path") else None,
                "verification_method": "A", "verification_methods": ["A"], "verification_phase": "PDR",
                "budget_ref": ln["budget_ref"], "allocation_codes": [ln["element_code"]],
                "responsible_position": None,
                "external_ids": {"origin": ORIGIN, "ledger_line": ln["line_id"],
                                 "text_fr": f"La {qty_fr} de {name} ne doit pas dépasser son allocation de "
                                            f"{str(f'{val:g}').replace('.', ',')} {ln.get('unit') or b['unit']}."},
            }
            from .interface_requirements import owner_seat
            req["responsible_position"] = owner_seat(el, els)
            _requirements[req["id"]] = req
            await db_create_requirement(req)
            created.append(code)
        elif ln["state"] == "stale" and rid:
            req = _requirements.get(rid)
            if req is None:
                continue
            ext = dict(req.get("external_ids") or {})
            cur = ext.get("allocation_sync") or {}
            marked.add(rid)
            if (cur.get("state") == "stale" and cur.get("proposed_value") == ln["value"]) or \
                    (cur.get("state") == "stale_dismissed" and cur.get("dismissed_value") == ln["value"]):
                continue
            log = list(cur.get("log") or [])[-19:]
            log.append({"at": now, "event": "allocation_changed", "from": ln["row_value"], "to": ln["value"],
                        "line_id": ln["line_id"]})
            ext["allocation_sync"] = {"state": "stale", "proposed_value": ln["value"], "row_value": ln["row_value"],
                                      "ledger_value": ln["value"], "line_id": ln["line_id"], "at": now, "log": log}
            req["external_ids"] = ext
            await db_update_requirement(rid, req)
            stale.append(req.get("code"))
            await _log(study_id, "allocation_changed", req.get("code") or rid,
                       {"requirement_id": rid, "from": ln["row_value"], "to": ln["value"], "line_id": ln["line_id"]})
        elif rid:
            marked.add(rid)
    for x in st["retired"]:
        req = _requirements.get(x["requirement_id"])
        if req is None:
            continue
        marked.add(req["id"])
        ext = dict(req.get("external_ids") or {})
        if (ext.get("allocation_sync") or {}).get("state") == "retired":
            continue
        log = list((ext.get("allocation_sync") or {}).get("log") or [])[-19:]
        log.append({"at": now, "event": "allocation_retired"})
        ext["allocation_sync"] = {"state": "retired", "at": now, "log": log}
        req["external_ids"] = ext
        await db_update_requirement(req["id"], req)
        retired.append(req.get("code"))
        await _log(study_id, "allocation_retired", req.get("code") or req["id"], {"requirement_id": req["id"]})
    # a flag whose cause went away (the line changed back, or came back) is cleared
    for r in reqs:
        ext = r.get("external_ids") or {}
        if ext.get("allocation_sync", {}).get("state") in ("stale", "retired") and r["id"] not in marked:
            ext = dict(ext)
            ext["allocation_sync"] = {**ext["allocation_sync"], "state": "in_step", "at": now}
            r["external_ids"] = ext
            await db_update_requirement(r["id"], r)
            cleared.append(r.get("code"))
    if created or stale or retired or cleared:
        from ..routers._arcadia_events import broadcast_mutation
        await broadcast_mutation(study_id, "allocation_requirements_synced", "study", study_id,
                                 {"created": created, "stale": stale, "retired": retired})
    return {"study_id": study_id, "created": created, "stale": stale, "retired": retired, "cleared": cleared,
            "counts": st["counts"]}


async def ledger_changed(study_id: str, line: dict | None = None, old_value: Any = None, *,
                         create: bool = True) -> dict[str, Any]:
    """The one entry point A's ledger calls after a change (create, value edit, propose, import,
    agree, delete): AR-01 applied to the whole study (``line`` / ``old_value`` are informative;
    :func:`sync` reads the ledger itself). Never raises: a failed sync is logged."""
    try:
        return await sync(study_id, create=create)
    except Exception:  # noqa: BLE001 — the ledger edit stands; the sync can be run on demand
        logger.warning("allocation requirement sync failed for %s", study_id, exc_info=True)
        return {"study_id": study_id, "created": [], "stale": [], "retired": [], "cleared": [], "error": True}


async def resolve(req: dict, action: str) -> dict:
    """The owner's answer to a flag: ``accept`` (the threshold takes the ledger value; a retired
    row is retired) or ``dismiss`` (the row is kept as it is)."""
    from ..db.requirement_repo import db_update_requirement
    ext = dict(req.get("external_ids") or {})
    flag = dict(ext.get("allocation_sync") or {})
    if flag.get("state") not in ("stale", "retired"):
        raise ValueError("the requirement has no allocation flag")
    now = datetime.now(timezone.utc).isoformat()
    log = list(flag.get("log") or [])[-19:]
    if action == "accept" and flag["state"] == "stale":
        req["threshold_value"] = json.dumps(flag["proposed_value"])
        log.append({"at": now, "event": "accepted", "value": flag["proposed_value"]})
    elif action == "accept":
        req["status"] = "retired"
        log.append({"at": now, "event": "retired"})
    elif action == "dismiss":
        log.append({"at": now, "event": "dismissed"})
    else:
        raise ValueError("action must be accept or dismiss")
    ext["allocation_sync"] = {"state": "in_step" if action == "accept" else f"{flag['state']}_dismissed",
                              "at": now, "log": log, **({"dismissed_value": flag.get("proposed_value")}
                                                       if action == "dismiss" else {})}
    req["external_ids"] = ext
    await db_update_requirement(req["id"], req)
    await _log(req["study_id"], f"allocation_{action}", req.get("code") or req["id"], {"requirement_id": req["id"]})
    return req


async def _log(study_id: str, action: str, target: str, detail: dict) -> None:
    try:
        from ..seats import store
        await store.log_event(study_id, "systems_engineer", None, action, target, detail)
    except Exception:  # noqa: BLE001 — the event log is best effort
        logger.debug("allocation event not logged", exc_info=True)


__all__ = ["BUDGETS", "line_ref", "resolve", "status", "sync"]
