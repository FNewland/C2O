"""Allocation ledger with owner sign-off (wave 3, 3.A2; SE-05, negotiation #2, N7).

Systems proposes a budget allocation to each element; the element's owner seat agrees it (or
disputes it with a reason). The ledger keeps the value, the covering requirement, the owner, the
state, who agreed and when, a version and the history of every change. The Systems reserve is a
line of its own (``line_kind = "reserve"``): what is left between the sum of the allocations with
the system margin and the limit (mass), the end-of-life generation (power) or the daily downlink
capacity (data).

``BudgetAllocationRow`` (the Budget tab's allocation cache) stays as it is: the ledger is the
signed record, not a second budget.

Public API::

    await import_budgets(study_id, budgets, agree=True, by="seed")   # budgets.yaml shape
    await propose(study_id)                                           # from the roll-up
    await list_lines(study_id) -> {"items", "reserve", "closure", "counts"}
    await status(study_id) -> {...}          # what readiness and PDR-EC-07 (R) read
    await apply_ledger_change(pc)            # a pending change accepted by the owner seat

Allocation requirements (rule AR-01, agent R, ``services/allocation_requirements.py``): every
value change calls ``allocation_requirements.ledger_changed(study_id, line, old_value)`` when that
module exists; until then the ledger marks its covering requirement ``stale`` with the proposed
value in ``data_json.requirement_sync``.
"""
from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any

from ..db.models_alloc import LEDGER_BUDGET_TYPES, LEDGER_STATUSES, AllocationLedgerRow as Row
from . import study_rows as sr

logger = logging.getLogger(__name__)

#: v2 element codes -> the product-tree domain of the element that carries the allocation
CODE_DOMAIN: dict[str, str] = {
    "PAY": "payload", "EPS": "power", "AOCS": "aocs", "COM": "ttc", "OBC": "obc", "THM": "thermal",
    "STR": "structure", "DIS": "propulsion", "HAR": "harness",
}
#: requirement-code prefix -> element code (registration / timing contributors, pointing)
PREFIX_CODE: dict[str, str] = {
    "PAY": "PAY", "EPS": "EPS", "ADC": "AOCS", "GNS": "AOCS", "COM": "COM", "OBD": "OBC", "THM": "THM",
    "STR": "STR", "DIS": "DIS", "HAR": "HAR", "SEG": "SYS", "SYS": "SYS", "IF": "SYS", "MIS": "SYS",
}
#: the seat that answers for an element code when the baseline does not name one
CODE_SEAT: dict[str, str] = {
    "PAY": "payload_lead", "EPS": "power_engineer", "AOCS": "aocs_engineer", "COM": "comms_engineer",
    "OBC": "comms_engineer", "THM": "thermal_engineer", "STR": "structures_engineer",
    "DIS": "propulsion_engineer", "HAR": "systems_engineer", "SYS": "systems_engineer", "SC": "systems_engineer",
}
#: share of the daily downlink capacity that can be allocated (station availability, as in the
#: ground closure)
DATA_AVAILABILITY = 0.9
UNITS = {"mass": "kg", "power_avg": "W", "power_peak": "W", "power_mode": "W", "data": "MB/day",
         "pointing": "deg", "registration": "px", "timing": "ms"}
TYPE_LABEL = {
    "mass": {"en": "Mass", "fr": "Masse"},
    "power_avg": {"en": "Orbit-average power", "fr": "Puissance moyenne sur l’orbite"},
    "power_peak": {"en": "Peak power", "fr": "Puissance de crête"},
    "power_mode": {"en": "Power in a mode", "fr": "Puissance dans un mode"},
    "data": {"en": "Data volume", "fr": "Volume de données"},
    "pointing": {"en": "Pointing", "fr": "Pointage"},
    "registration": {"en": "Registration", "fr": "Recalage"},
    "timing": {"en": "Timing", "fr": "Datation"},
}
#: pointing allocations of budgets.yaml: (key, value field, unit, label)
POINTING_LINES = (
    ("control", "ape_deg_3sigma", "deg", "Absolute pointing error (3σ)"),
    ("knowledge", "deg_3sigma", "deg", "Attitude knowledge (3σ)"),
    ("alignment", "deg_3sigma", "deg", "Payload-to-sensor alignment (3σ)"),
    ("stability_day", "deg_s_3sigma", "deg/s", "Rate stability, day imaging (3σ)"),
    ("stability_night", "deg_s_3sigma", "deg/s", "Rate stability, night imaging (3σ)"),
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _code_of_requirement(req_code: str) -> str:
    head = (req_code or "").split("-")[0].upper()
    return PREFIX_CODE.get(head, "SYS")


# ───────────────────────────────────────────────────────── lookups (elements, requirements)

def _study_elements(study_id: str) -> list[dict]:
    from ..routers.elements import _elements
    return [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


def element_for_code(study_id: str, code: str, elements: list[dict] | None = None) -> str | None:
    """The element an allocation line belongs to: the subsystem of that domain, else the spacecraft."""
    els = elements if elements is not None else _study_elements(study_id)
    dom = CODE_DOMAIN.get(code)
    if dom:
        for e in els:
            if e.get("element_type") == "subsystem" and (e.get("subsystem_domain") or "") == dom:
                return e["id"]
    for e in els:
        if e.get("element_type") == "system" and (e.get("segment") or "space") == "space":
            return e["id"]
    return None


async def _requirements_by_code(study_id: str) -> dict[str, dict]:
    try:
        from ..routers.requirements import _requirements, ensure_requirements_loaded
        try:
            await ensure_requirements_loaded()
        except Exception:  # noqa: BLE001
            pass
        return {str(r.get("code") or ""): r for r in _requirements.values()
                if r.get("study_id") == study_id and r.get("code") and r.get("status") != "retired"}
    except Exception:  # noqa: BLE001
        return {}


# ───────────────────────────────────────────────────────── import from budgets.yaml

def lines_from_budgets(b: dict[str, Any]) -> list[dict[str, Any]]:
    """Every allocation of a ``budgets.yaml`` document as ledger lines (no ids, no element)."""
    trace = {}
    for t in b.get("traceability") or []:
        trace.setdefault(str(t.get("budget_ref") or ""), t)
    out: list[dict[str, Any]] = []

    def add(**kw: Any) -> None:
        kw.setdefault("unit", UNITS.get(kw["budget_type"], ""))
        kw.setdefault("line_kind", "allocation")
        ref = kw.get("budget_ref") or ""
        t = trace.get(ref) or {}
        kw.setdefault("requirement_code", t.get("requirement") or "")
        seat = kw.get("owner_seat") or t.get("owner_seat") or CODE_SEAT.get(kw.get("element_code") or "", "systems_engineer")
        kw["owner_seat"] = seat
        kw["order"] = len(out)
        out.append(kw)

    mass = b.get("mass") or {}
    subs = mass.get("subsystems") or {}
    for code, v in (mass.get("allocations") or {}).items():
        s = subs.get(code) or {}
        add(budget_type="mass", element_code=code, value=_num(v), cbe=_num(s.get("cbe_kg")),
            margined=_num(s.get("margined_kg")), requirement_code=s.get("requirement") or "",
            owner_seat=s.get("owner_seat"), rationale=s.get("rationale") or "", budget_ref=f"mass.allocations.{code}")
    power = b.get("power") or {}
    psubs = power.get("subsystems") or {}
    for code, v in (power.get("allocations") or {}).items():
        s = psubs.get(code) or {}
        add(budget_type="power_avg", element_code=code, value=_num(v), cbe=_num(s.get("orbit_average_w")),
            margined=_num(s.get("margined_w")), requirement_code=s.get("requirement") or "",
            owner_seat=s.get("owner_seat"), rationale=s.get("rationale") or "", budget_ref=f"power.allocations.{code}")
    for code, v in (power.get("peak_allocations") or {}).items():
        for key, w in (v or {}).items():
            if key.endswith("_w") and _num(w) is not None:
                add(budget_type="power_peak", element_code=code, value=_num(w), mode_key=key[:-2],
                    requirement_code=(v or {}).get("requirement") or "", budget_ref=f"power.peak_allocations.{code}")
    for code, modes in (power.get("mode_allocations") or {}).items():
        for mode, v in (modes or {}).items():
            add(budget_type="power_mode", element_code=code, mode_key=mode, value=_num((v or {}).get("w")),
                cbe=_num((v or {}).get("matrix_w")), requirement_code=(v or {}).get("requirement") or "",
                budget_ref=f"power.mode_allocations.{code}.{mode}",
                data_json={k: x for k, x in (v or {}).items() if k not in ("w", "requirement", "matrix_w")} or None)
    data = b.get("data") or {}
    for key, v in (data.get("allocations") or {}).items():
        req = (v or {}).get("requirement") or ""
        add(budget_type="data", element_code=_code_of_requirement(req) if key != "science" else "PAY", mode_key=key,
            value=_num((v or {}).get("mb_per_day")), cbe=_num((v or {}).get("cbe_mb_per_day") or (v or {}).get("product_mb_per_day")),
            requirement_code=req, owner_seat=(v or {}).get("owner_seat"), budget_ref=f"data.allocations.{key}",
            data_json={k: x for k, x in (v or {}).items() if k not in ("mb_per_day", "requirement", "owner_seat")} or None)
    pnt = b.get("pointing") or {}
    for key, field, unit, label in POINTING_LINES:
        v = pnt.get(key) or {}
        if _num(v.get(field)) is None:
            continue
        add(budget_type="pointing", element_code="AOCS", mode_key=key, value=_num(v.get(field)), unit=unit,
            requirement_code=v.get("requirement") or "", owner_seat="aocs_engineer", rationale=label,
            budget_ref=f"pointing.{key}")
    reg = b.get("registration") or {}
    for i, c in enumerate(reg.get("allocations") or []):
        req = str(c.get("requirement") or "").split("/")[0].strip()
        code = _code_of_requirement(req)
        add(budget_type="registration", element_code=code, mode_key=f"c{i + 1}", value=_num(c.get("px_rms")),
            unit="px", requirement_code=req, owner_seat=CODE_SEAT.get(code), rationale=str(c.get("contributor") or ""),
            budget_ref=f"registration.allocations[{i}]")
    tim = b.get("timing") or {}
    for i, c in enumerate(tim.get("contributors") or []):
        req = str(c.get("requirement") or "").split("(")[0].split("/")[0].strip()
        code = _code_of_requirement(req)
        add(budget_type="timing", element_code=code, mode_key=f"c{i + 1}", value=_num(c.get("ms")), unit="ms",
            requirement_code=req, owner_seat=CODE_SEAT.get(code), rationale=str(c.get("contributor") or ""),
            budget_ref=f"timing.contributors[{i}]")
    return out


async def import_budgets(study_id: str, budgets: dict[str, Any], *, agree: bool = False, replace: bool = True,
                         by: str = "") -> dict[str, Any]:
    """Every allocation of ``budgets`` (the ``budgets.yaml`` shape) in one call; ``agree`` records
    each line as agreed by its owner seat (the seed's S2; the walkthrough films the agreement)."""
    lines = lines_from_budgets(budgets or {})
    if replace:
        await sr.delete_rows(Row, study_id)
    els = _study_elements(study_id)
    reqs = await _requirements_by_code(study_id)
    now = _now()
    rows = []
    for ln in lines:
        r = reqs.get(ln.get("requirement_code") or "")
        row = {**ln, "element_id": element_for_code(study_id, ln.get("element_code") or "", els),
               "requirement_id": r.get("id") if r else None, "origin": "import", "version": 1,
               "history_json": [{"at": now.isoformat(), "by": by or "import", "field": "created", "old": None,
                                 "new": ln.get("value"), "why": "imported from the budget baseline"}]}
        if agree:
            row.update(status="agreed", agreed_by=f"{ln['owner_seat']}" + (f" ({by})" if by else ""), agreed_at=now)
        rows.append(row)
    await sr.insert_rows(Row, study_id, rows, prefix="al")
    await refresh_reserves(study_id, budgets=budgets)
    return {"imported": len(rows), **(await list_lines(study_id))}


async def propose(study_id: str, *, gate: str | None = None) -> dict[str, Any]:
    """Mass and orbit-average power lines per space subsystem from the roll-up (CBE with maturity,
    rounded up to the next 10 g / 0.1 W): the starting point Systems offers the seats."""
    from . import rollup
    ru = await rollup.compute(study_id, gate=gate)
    els = {e["id"]: e for e in _study_elements(study_id)}

    def sub_of(eid: str) -> dict | None:
        seen = set()
        e = els.get(eid)
        while e is not None and e["id"] not in seen:
            seen.add(e["id"])
            if e.get("element_type") == "subsystem":
                return e
            e = els.get(e.get("parent_id") or "")
        return None

    code_of = {v: k for k, v in CODE_DOMAIN.items()}
    # integration: the power line is the subsystem's ORBIT-AVERAGE share of the operational mode
    # mix with its maturity margin (the same figure the bound PWR rows check, R 3.R2), not the
    # units' ON power; the ON power is the fallback while the study has no operational mix
    oa: dict[str, float] = {}
    try:
        from .threshold_binding import values as binding_values
        for k, v in (await binding_values(study_id) or {}).items():
            m = re.match(r"^rollup\.power\.(\w+)\.orbit_average_with_maturity_w$", k)
            if m and isinstance(v, (int, float)):
                oa[m.group(1)] = float(v)
    except Exception:  # noqa: BLE001 — no modes: the ON power below
        logger.debug("no orbit-average shares for %s", study_id, exc_info=True)
    agg: dict[tuple[str, str], dict[str, float]] = {}
    for kind, units in (("mass", ru.mass.units), ("power_avg", [] if oa else ru.power.units)):
        for u in units or []:
            sub = sub_of(u.get("element_id") or "")
            if sub is None or (sub.get("segment") or "space") != "space":
                continue
            a = agg.setdefault((kind, sub["id"]), {"cbe": 0.0, "margined": 0.0})
            a["cbe"] += float(u.get("cbe") or 0.0)
            a["margined"] += float(u.get("with_margin") or 0.0)
    space_subs = [e for e in els.values() if e.get("element_type") == "subsystem"
                  and (e.get("segment") or "space") == "space" and e.get("in_scope", True) is not False
                  and code_of.get(e.get("subsystem_domain") or "") not in (None, "HAR")]
    if oa:
        for sub in space_subs:
            v = oa.get(code_of.get(sub.get("subsystem_domain") or "") or "")
            agg[("power_avg", sub["id"])] = {"cbe": None, "margined": float(v or 0.0)}   # type: ignore[dict-item]
    # a subsystem with a mass line and no power gets a nil power line (0 W: no requirement needed)
    for sub in space_subs:
        if ("mass", sub["id"]) in agg:
            agg.setdefault(("power_avg", sub["id"]), {"cbe": 0.0, "margined": 0.0})
    have = {(r["budget_type"], r.get("element_id")) for r in await sr.list_rows(Row, study_id)}
    rows = []
    for (kind, sid_), a in sorted(agg.items(), key=lambda kv: (kv[0][0], els[kv[0][1]].get("name", ""))):
        if (kind, sid_) in have or (a["margined"] <= 0 and kind != "power_avg"):
            continue
        sub = els[sid_]
        code = code_of.get(sub.get("subsystem_domain") or "", (sub.get("subsystem_domain") or "SC").upper()[:6])
        step = 0.01 if kind == "mass" else 0.1
        value = math.ceil(a["margined"] / step - 1e-9) * step
        from ..seats import config as seat_cfg
        rows.append({"budget_type": kind, "element_code": code, "element_id": sid_, "value": round(value, 3),
                     "unit": UNITS[kind], "cbe": round(a["cbe"], 4) if a["cbe"] is not None else None,
                     "margined": round(a["margined"], 4),
                     "owner_seat": seat_cfg.seat_for_domain(sub.get("subsystem_domain")) or CODE_SEAT.get(code, "systems_engineer"),
                     "status": "proposed", "origin": "proposed",
                     "rationale": ("Orbit-average share of the operational mix with maturity margin, rounded up (Modes)"
                                   if kind == "power_avg" and oa else "CBE with maturity margin, rounded up (roll-up)"),
                     "order": 100 + len(rows),
                     "history_json": [{"at": _now().isoformat(), "by": "roll-up", "field": "created", "old": None,
                                       "new": round(value, 3), "why": "proposed from the roll-up"}]})
    await sr.insert_rows(Row, study_id, rows, prefix="al")
    await refresh_reserves(study_id)
    return {"proposed": len(rows), **(await list_lines(study_id))}


# ───────────────────────────────────────────────────────── reserves and closure

async def _limits(study_id: str, budgets: dict | None = None, *, data_capacity: bool = False,
                  stored: list[dict] | None = None) -> dict[str, Any]:
    """Mass limit and system margin (roll-up), EOL generation (parts), daily capacity (data budget;
    computed only when ``data_capacity``, else the figure the data reserve line stored)."""
    out: dict[str, Any] = {"mass_limit_kg": None, "mass_margin_pct": None, "power_margin_pct": None,
                           "eol_generation_w": None, "data_capacity_mb_per_day": None,
                           "data_allocatable_mb_per_day": None}
    try:
        from . import rollup
        ru = await rollup.compute(study_id)
        out.update(mass_limit_kg=ru.mass.limit_kg, mass_margin_pct=ru.mass.system_margin_percent,
                   power_margin_pct=ru.power.system_margin_percent)
    except Exception:  # noqa: BLE001
        logger.debug("ledger: roll-up unavailable", exc_info=True)
    try:
        from .analysis_context import power_sources_from
        out["eol_generation_w"] = power_sources_from(_study_elements(study_id))[0]
    except Exception:  # noqa: BLE001
        logger.debug("ledger: power sources unavailable", exc_info=True)
    for r in stored or []:
        if r.get("line_kind") == "reserve" and r.get("budget_type") == "data":
            out["data_capacity_mb_per_day"] = (r.get("data_json") or {}).get("capacity")
            out["data_allocatable_mb_per_day"] = (r.get("data_json") or {}).get("limit")
    if budgets:   # the import's own figures win where the study has none yet
        m, p, d = budgets.get("mass") or {}, budgets.get("power") or {}, budgets.get("data") or {}
        out["mass_limit_kg"] = out["mass_limit_kg"] or _num(m.get("limit_kg"))
        out["mass_margin_pct"] = out["mass_margin_pct"] or _num(m.get("system_margin_pct"))
        out["eol_generation_w"] = out["eol_generation_w"] or _num((p.get("generation") or {}).get("eol_orbit_average_w"))
        out["data_capacity_mb_per_day"] = _num(d.get("capacity_mb_per_day")) or out["data_capacity_mb_per_day"]
        out["data_allocatable_mb_per_day"] = _num(d.get("allocatable_90pct_mb_per_day")) or out["data_allocatable_mb_per_day"]
    if out["data_capacity_mb_per_day"] is None and data_capacity:
        try:
            from .key_numbers import key_numbers
            out["data_capacity_mb_per_day"] = (await key_numbers(study_id)).get("data.capacity_mb_per_day", {}).get("value")
        except Exception:  # noqa: BLE001
            pass
    if out["data_allocatable_mb_per_day"] is None and _num(out["data_capacity_mb_per_day"]) is not None:
        # the 90 % station availability the ground closure applies (data allocations are made
        # against what is allocatable, not the raw capacity)
        out["data_allocatable_mb_per_day"] = round(float(out["data_capacity_mb_per_day"]) * DATA_AVAILABILITY, 3)
    return out


def closure(lines: list[dict], lim: dict[str, Any]) -> dict[str, Any]:
    """Σ allocations × (1 + system margin) against the limit, per resource."""
    out: dict[str, Any] = {}
    alloc = [ln for ln in lines if ln.get("line_kind") != "reserve"]
    for kind, limit_key, margin_key, unit in (("mass", "mass_limit_kg", "mass_margin_pct", "kg"),
                                               ("power_avg", "eol_generation_w", "power_margin_pct", "W"),
                                               ("data", "data_allocatable_mb_per_day", None, "MB/day")):
        vals = [float(ln["value"]) for ln in alloc if ln.get("budget_type") == kind and _num(ln.get("value")) is not None]
        if not vals:
            continue
        total = round(sum(vals), 4)
        pct = float(lim.get(margin_key) or 0.0) if margin_key else 0.0
        with_m = round(total * (1 + pct / 100), 4)
        limit = lim.get(limit_key)
        out[kind] = {"lines": len(vals), "sum": total, "system_margin_percent": pct, "with_system_margin": with_m,
                     "limit": limit, "unit": unit,
                     "reserve": round(limit - with_m, 4) if limit is not None else None,
                     "closes": (with_m <= limit) if limit is not None else None}
    return out


async def refresh_reserves(study_id: str, budgets: dict | None = None) -> list[dict]:
    """(Re)write the Systems reserve lines from the current allocations and limits."""
    lines = await sr.list_rows(Row, study_id)
    lim = await _limits(study_id, budgets, data_capacity=True, stored=lines)
    cl = closure(lines, lim)
    res_rows = {r["budget_type"]: r for r in lines if r.get("line_kind") == "reserve"}
    out = []
    for kind, c in cl.items():
        if c.get("reserve") is None:
            continue
        data = {"limit": c["limit"], "sum_allocations": c["sum"], "with_system_margin": c["with_system_margin"],
                "system_margin_percent": c["system_margin_percent"]}
        if kind == "data":
            data["capacity"] = lim.get("data_capacity_mb_per_day")
        if kind in res_rows:
            r = await sr.update_row(Row, res_rows[kind]["id"], {"value": c["reserve"], "data_json": data})
        else:
            r = (await sr.insert_rows(Row, study_id, [{
                "budget_type": kind, "line_kind": "reserve", "element_code": "SYS", "value": c["reserve"],
                "unit": c["unit"], "owner_seat": "systems_engineer", "status": "agreed", "agreed_by": "systems_engineer",
                "agreed_at": _now(), "origin": "proposed", "order": 900 + len(out), "data_json": data,
                "rationale": "Systems reserve: limit minus the allocations with the system margin"}], prefix="al"))[0]
        out.append(r)
    return out


async def list_lines(study_id: str) -> dict[str, Any]:
    lines = await sr.list_rows(Row, study_id)
    lim = await _limits(study_id, stored=lines)
    items = [ln for ln in lines if ln.get("line_kind") != "reserve"]
    reserve = {ln["budget_type"]: {"value": ln.get("value"), "unit": ln.get("unit"), "id": ln["id"],
                                   **(ln.get("data_json") or {})}
               for ln in lines if ln.get("line_kind") == "reserve"}
    counts: dict[str, Any] = {"lines": len(items), "by_type": {}, "by_status": {s: 0 for s in LEDGER_STATUSES}}
    for ln in items:
        counts["by_type"][ln["budget_type"]] = counts["by_type"].get(ln["budget_type"], 0) + 1
        counts["by_status"][ln.get("status") or "proposed"] = counts["by_status"].get(ln.get("status") or "proposed", 0) + 1
    for ln in lines:
        ln["type_label"] = TYPE_LABEL.get(ln["budget_type"], {"en": ln["budget_type"], "fr": ln["budget_type"]})
    return {"study_id": study_id, "items": items, "reserve": reserve, "closure": closure(lines, lim), "counts": counts,
            "limits": lim}


async def status(study_id: str, *, budget_types: tuple[str, ...] = ("mass", "power_avg")) -> dict[str, Any]:
    """Evidence for readiness and PDR-EC-07 (wired by R): mass and power lines agreed for every
    space subsystem, closure within the limit, every line covered by a requirement."""
    led = await list_lines(study_id)
    items = [ln for ln in led["items"] if ln["budget_type"] in budget_types]
    not_agreed = [ln for ln in items if ln.get("status") != "agreed"]
    uncovered = [ln for ln in items if not (ln.get("requirement_id") or ln.get("requirement_code"))
                 and (_num(ln.get("value")) or 0.0) > 0]
    have = {(ln["budget_type"], ln.get("element_code")) for ln in items}
    subs = [e for e in _study_elements(study_id) if e.get("element_type") == "subsystem"
            and (e.get("segment") or "space") == "space" and e.get("in_scope", True) is not False]
    code_of = {v: k for k, v in CODE_DOMAIN.items()}
    missing = []
    for e in subs:
        code = code_of.get(e.get("subsystem_domain") or "")
        if not code or code == "HAR":
            continue
        for bt in budget_types:
            if (bt, code) not in have:
                missing.append({"element_code": code, "element": e.get("name"), "budget_type": bt})
    closes = {k: v.get("closes") for k, v in led["closure"].items() if k in budget_types}
    ok = bool(items) and not not_agreed and not uncovered and not missing and all(c is not False for c in closes.values())
    return {"study_id": study_id, "ok": ok, "lines": len(items), "agreed": len(items) - len(not_agreed),
            "not_agreed": [{"id": ln["id"], "element_code": ln.get("element_code"), "budget_type": ln["budget_type"],
                            "owner_seat": ln.get("owner_seat"), "status": ln.get("status")} for ln in not_agreed],
            "uncovered": [ln["id"] for ln in uncovered], "missing": missing, "closure": led["closure"],
            "closes": closes}


# ───────────────────────────────────────────────────────── edits, agreement, dispute

EDITABLE = ("value", "unit", "rationale", "owner_seat", "requirement_code", "requirement_id", "mode_key",
            "element_id", "element_code", "budget_type", "cbe", "margined", "budget_ref")


def _hist(line: dict, by: str, field: str, old: Any, new: Any, why: str = "") -> list[dict]:
    h = list(line.get("history_json") or [])
    h.append({"at": _now().isoformat(), "by": by, "field": field, "old": old, "new": new, "why": why})
    return h[-200:]


async def create_line(study_id: str, body: dict[str, Any], by: str = "") -> dict[str, Any]:
    bt = body.get("budget_type") or "mass"
    if bt not in LEDGER_BUDGET_TYPES:
        raise ValueError(f"budget_type must be one of {LEDGER_BUDGET_TYPES}")
    code = body.get("element_code") or ""
    data = {k: body[k] for k in EDITABLE if k in body}
    data.setdefault("unit", UNITS.get(bt, ""))
    data.setdefault("owner_seat", CODE_SEAT.get(code, "systems_engineer"))
    if not data.get("element_id") and code:
        data["element_id"] = element_for_code(study_id, code)
    if data.get("requirement_code") and not data.get("requirement_id"):
        r = (await _requirements_by_code(study_id)).get(data["requirement_code"])
        data["requirement_id"] = r["id"] if r else None
    data.update(status="proposed", origin="user", version=1,
                history_json=[{"at": _now().isoformat(), "by": by, "field": "created", "old": None,
                               "new": data.get("value"), "why": body.get("why") or ""}])
    row = (await sr.insert_rows(Row, study_id, [data], prefix="al"))[0]
    await refresh_reserves(study_id)
    return row


async def update_line(line: dict, fields: dict[str, Any], *, by: str = "", by_owner: bool = False,
                      why: str = "") -> dict[str, Any]:
    """Apply an edit. A changed value bumps the version; the line goes back to ``proposed`` unless
    its owner made the change (then it stays agreed, by the owner)."""
    upd: dict[str, Any] = {}
    hist = list(line.get("history_json") or [])
    for k in EDITABLE:
        if k in fields and fields[k] != line.get(k):
            upd[k] = fields[k]
            hist = _hist({"history_json": hist}, by, k, line.get(k), fields[k], why)
    if not upd:
        return line
    value_changed = "value" in upd
    if value_changed:
        upd["version"] = int(line.get("version") or 1) + 1
        if by_owner:
            upd.update(status="agreed", agreed_by=by or line.get("owner_seat") or "", agreed_at=_now())
        else:
            upd.update(status="proposed", agreed_by="", agreed_at=None)
    if "requirement_code" in upd and "requirement_id" not in upd:
        r = (await _requirements_by_code(line["study_id"])).get(upd["requirement_code"] or "")
        upd["requirement_id"] = r["id"] if r else None
    upd["history_json"] = hist
    row = await sr.update_row(Row, line["id"], upd)
    if value_changed and row is not None:
        row = await _sync_requirement(row, line.get("value"))
        await refresh_reserves(line["study_id"])
    return row or line


async def _sync_requirement(line: dict, old_value: Any) -> dict:
    """Keep the covering requirement in step with a changed allocation (rule AR-01, agent R)."""
    try:
        from . import allocation_requirements as ar   # 3.R3 (agent R)
        hook = getattr(ar, "ledger_changed", None)
        if hook is not None:
            await hook(line["study_id"], line, old_value)
            return await sr.get_row(Row, line["id"]) or line
    except ImportError:
        pass
    except Exception:  # noqa: BLE001
        logger.warning("allocation requirement sync failed", exc_info=True)
    data = dict(line.get("data_json") or {})
    if line.get("requirement_id") or line.get("requirement_code"):
        data["requirement_sync"] = {"status": "stale", "requirement_id": line.get("requirement_id"),
                                    "requirement_code": line.get("requirement_code"),
                                    "old_value": old_value, "proposed_value": line.get("value"),
                                    "unit": line.get("unit"), "at": _now().isoformat()}
    else:
        data["requirement_sync"] = {"status": "missing", "proposed_code": proposed_requirement_code(line),
                                    "proposed_value": line.get("value"), "unit": line.get("unit")}
    return await sr.update_row(Row, line["id"], {"data_json": data}) or line


def proposed_requirement_code(line: dict) -> str:
    """AR-<budget>-<ELEM> (rule AR-01) for a line no requirement covers."""
    short = {"mass": "MAS", "power_avg": "PWR", "power_peak": "PPK", "power_mode": "PMD", "data": "DAT",
             "pointing": "PNT", "registration": "REG", "timing": "TIM"}
    return f"AR-{short.get(line.get('budget_type') or '', 'BUD')}-{line.get('element_code') or 'SC'}"


async def agree(line: dict, by: str) -> dict:
    row = await sr.update_row(Row, line["id"], {
        "status": "agreed", "agreed_by": by, "agreed_at": _now(),
        "history_json": _hist(line, by, "status", line.get("status"), "agreed")})
    return row or line


async def dispute(line: dict, by: str, reason: str) -> dict:
    data = dict(line.get("data_json") or {})
    data["dispute"] = {"by": by, "reason": reason, "at": _now().isoformat()}
    row = await sr.update_row(Row, line["id"], {
        "status": "disputed", "agreed_by": "", "agreed_at": None, "data_json": data,
        "history_json": _hist(line, by, "status", line.get("status"), "disputed", reason)})
    return row or line


async def apply_ledger_change(pc: dict[str, Any]) -> dict[str, Any]:
    """A pending change on a ledger line, accepted by the owner seat (``seats/changes.apply_pending``
    calls this for ``kind == "allocation_ledger"``). The owner's acceptance is its agreement."""
    new = dict(pc.get("new") or {})
    new.pop("_entity", None)
    line_id = new.pop("_id", None)
    line = await sr.get_row(Row, line_id) if line_id else None
    if line is None:
        from fastapi import HTTPException
        raise HTTPException(409, {"code": "ledger_line_gone", "message": "The allocation line no longer exists"})
    why = str(new.pop("why", "") or "")
    by = f"{pc.get('owner_seat') or ''} (accepted change from {pc.get('by_seat') or 'another seat'})"
    return await update_line(line, new, by=by, by_owner=True, why=why)
