"""Threshold ↔ computed value binding (wave 3, 3.R2; automation A2).

A requirement's threshold is *checked against* a figure the tool computes when its
``threshold_param_path`` names one. This module

* lists the figures a threshold can be bound to (:data:`CATALOGUE`: the budget figures of
  ``gate_evaluator.BUDGET_PARAMS``, the per-subsystem roll-up, the allocation closure, the
  per-mode power, the data budget and the design parameters), with their unit;
* **proposes** a binding for each row from its ``budget_ref`` (v2: ``mass.allocations.PAY``,
  ``power.mode_allocations.COM.downlink`` …), its threshold unit and, failing those, keywords of
  its text (:func:`propose`); a proposal is only made when the units agree;
* computes the **values** of the catalogue for a study (:func:`values`), so the compliance
  tracker (``ComplianceTracker.evaluate_single``) and the gate criteria (SRR-EC-03, PDR-EC-01)
  evaluate the bound rows;
* **accepts** a proposal (or a path picked by hand) per row: ``threshold_param_path`` is set and
  ``external_ids["binding"]`` records ``{path, source, accepted_at, by}``.

Paths
-----
``budget.*``                          gate_evaluator figures (dry mass, margins, data, link)
``rollup.mass.<CODE>.with_maturity_kg``   subsystem CBE with its units' maturity margins
``rollup.power.<CODE>.orbit_average_with_maturity_w``  subsystem share of the operational
                                      orbit average, with the units' power maturity margins
``modes.<kind>.<CODE>.power_w``      subsystem power (nominal, duty-averaged) in the modes of
                                      one kind (``imaging``, ``downlink``, ``disposal``; ``peak`` =
                                      the highest of every mode). A per-mode allocation carries its
                                      own headroom over the mode matrix, so it is checked against
                                      the nominal figure (v2 ``budgets.yaml`` ``mode_allocations``)
``alloc.mass.sum_with_margin_kg`` / ``alloc.power.sum_with_margin_w``  Σ of the subsystem
                                      allocations × (1 + system margin): the agreed allocation
                                      ledger lines, else the allocation requirements' thresholds
``data.*``                            the data budget's daily figures
``power.sa_power_eol_w``              design-loop parameter (array power at end of life)
``power.battery_dod_operational_pct`` depth of discharge of the operational orbit (Modes energy
                                      balance)

``<CODE>`` is the v2 element code of the subsystem (PAY, EPS, AOCS, COM, OBC, THM, STR, DIS, HAR;
``services.requirement_queries.element_code_map``).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SUBSYSTEM_CODES = ("PAY", "EPS", "AOCS", "COM", "OBC", "THM", "STR", "DIS", "HAR")
MODE_KINDS = ("imaging", "downlink", "disposal", "peak")
#: v2 ``budget_ref`` mode keys → the tool's mode kind
MODE_ALIASES = {"eol": "disposal", "sail": "disposal", "disposal": "disposal", "imaging": "imaging",
                "acquisition": "imaging", "downlink": "downlink", "nominal": "nominal"}


def _lbl(en: str, fr: str) -> dict[str, str]:
    return {"en": en, "fr": fr}


def _catalogue() -> dict[str, dict[str, Any]]:
    cat: dict[str, dict[str, Any]] = {
        "budget.mass_total_dry_kg": {"unit": "kg", "label": _lbl("Dry mass (roll-up, with harness)", "Masse sèche (bilan, avec harnais)")},
        "budget.mass_with_system_margin_kg": {"unit": "kg", "label": _lbl("Mass with system margin", "Masse avec marge système")},
        "budget.mass_system_margin_available_percent": {"unit": "%", "label": _lbl("System mass margin the limit leaves", "Marge système de masse laissée par la limite")},
        "budget.power_margin_eol_percent": {"unit": "%", "label": _lbl("End-of-life power margin", "Marge de puissance en fin de vie")},
        "budget.data_margin_percent": {"unit": "%", "label": _lbl("Daily data-volume margin", "Marge de volume de données quotidien")},
        "budget.link_margin_design_case_db": {"unit": "dB", "label": _lbl("Link margin, design case", "Marge de liaison, cas de dimensionnement")},
        "alloc.mass.sum_with_margin_kg": {"unit": "kg", "label": _lbl("Σ mass allocations × (1 + system margin)", "Σ allocations de masse × (1 + marge système)")},
        "alloc.power.sum_with_margin_w": {"unit": "W", "label": _lbl("Σ power allocations × (1 + system margin)", "Σ allocations de puissance × (1 + marge système)")},
        "power.sa_power_eol_w": {"unit": "W", "label": _lbl("Array power at end of life (orbit average)", "Puissance des panneaux en fin de vie (moyenne orbitale)")},
        "power.battery_dod_operational_pct": {"unit": "%", "label": _lbl("Battery depth of discharge, operational orbit", "Profondeur de décharge de la batterie, orbite opérationnelle")},
        "data.science_delivered_mb_per_day": {"unit": "MB/day", "label": _lbl("Science delivered per day", "Données scientifiques livrées par jour")},
        "data.stored_hk_mb_per_day": {"unit": "MB/day", "label": _lbl("Stored housekeeping per day", "Télémesure de servitude stockée par jour")},
        "data.realtime_hk_mb_per_day": {"unit": "MB/day", "label": _lbl("Real-time housekeeping per day", "Télémesure de servitude temps réel par jour")},
        "data.capacity_mb_per_day": {"unit": "MB/day", "label": _lbl("Downlink capacity per day", "Capacité de liaison descendante par jour")},
    }
    for c in SUBSYSTEM_CODES:
        cat[f"rollup.mass.{c}.with_maturity_kg"] = {
            "unit": "kg", "label": _lbl(f"{c} mass with maturity margins", f"Masse {c} avec marges de maturité")}
        cat[f"rollup.power.{c}.orbit_average_with_maturity_w"] = {
            "unit": "W", "label": _lbl(f"{c} orbit-average power with maturity margins",
                                       f"Puissance moyenne orbitale {c} avec marges de maturité")}
        for k, (en, fr) in {"imaging": ("imaging mode", "mode imagerie"), "downlink": ("downlink mode", "mode transmission"),
                            "disposal": ("disposal mode", "mode de retrait"), "peak": ("highest mode", "mode le plus élevé")}.items():
            cat[f"modes.{k}.{c}.power_w"] = {
                "unit": "W", "label": _lbl(f"{c} power in the {en} (nominal)", f"Puissance {c} en {fr} (nominale)")}
    for p, v in cat.items():
        v["path"] = p
        v["family"] = p.split(".", 1)[0]
    return cat


CATALOGUE: dict[str, dict[str, Any]] = _catalogue()

# ─────────────────────────────────────────────────────────────── proposals

_UNIT_KIND = (("kg", ("kg",)), ("W", ("w", "watt")), ("dB", ("db",)), ("%", ("%", "percent")),
              ("MB/day", ("mb/day", "mb per day")))


def unit_kind(unit: str | None) -> str | None:
    """``kg`` | ``W`` | ``dB`` | ``%`` | ``MB/day`` from a threshold unit (first word wins:
    ``% system mass margin`` → ``%``, ``W orbit average EOL`` → ``W``); None otherwise."""
    u = str(unit or "").strip().lower()
    if not u:
        return None
    head = u.split()[0]
    if u.startswith("mb/day") or u.startswith("mb per day"):
        return "MB/day"
    for kind, keys in _UNIT_KIND:
        if head in keys:
            return kind
    return None


#: (budget_ref pattern, threshold unit kind, path template)
_RULES: tuple[tuple[str, str | None, str], ...] = (
    (r"^mass\.allocations\.(\w+)$", "kg", "rollup.mass.{0}.with_maturity_kg"),
    (r"^power\.allocations\.(\w+)$", "W", "rollup.power.{0}.orbit_average_with_maturity_w"),
    (r"^power\.mode_allocations\.(\w+)\.(\w+)$", "W", "modes.{1}.{0}.power_w"),
    (r"^power\.peak_allocations\.(\w+)$", "W", "modes.peak.{0}.power_w"),
    (r"^mass\.closure$", "kg", "alloc.mass.sum_with_margin_kg"),
    (r"^power\.closure$", "W", "alloc.power.sum_with_margin_w"),
    (r"^power\.generation$", "W", "power.sa_power_eol_w"),
    (r"^power\.eclipse$", "%", "power.battery_dod_operational_pct"),
    (r"^mass\.totals$", "kg", "budget.mass_total_dry_kg"),
    (r"^mass\.totals$", "%", "budget.mass_system_margin_available_percent"),
    (r"^power\.totals$", "%", "budget.power_margin_eol_percent"),
    (r"^data$", "%", "budget.data_margin_percent"),
    (r"^link$", "dB", "budget.link_margin_design_case_db"),
    (r"^data\.allocations\.science$", "MB/day", "data.science_delivered_mb_per_day"),
    (r"^data\.allocations\.stored_hk$", "MB/day", "data.stored_hk_mb_per_day"),
    (r"^data\.allocations\.realtime_hk$", "MB/day", "data.realtime_hk_mb_per_day"),
)

#: keyword fallback for rows without ``budget_ref`` (a student's own row): (unit kind, words, path)
_WORDS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("kg", ("mass",), "rollup.mass.{sub}.with_maturity_kg"),
    ("W", ("orbit-average", "orbit average"), "rollup.power.{sub}.orbit_average_with_maturity_w"),
    ("dB", ("link", "margin"), "budget.link_margin_design_case_db"),
)


def _mode_key(k: str) -> str | None:
    return MODE_ALIASES.get(k.lower())


def propose(req: dict, sub_code: str | None = None) -> dict | None:
    """The binding proposal of one requirement: ``{path, reason, unit}`` or None.

    ``sub_code``: the v2 code of the subsystem the row is allocated to (keyword fallback only)."""
    if not req.get("threshold_op") or req.get("threshold_op") in ("exists", "in_range", "range", "before", "after"):
        return None
    kind = unit_kind(req.get("threshold_unit"))
    ref = str(req.get("budget_ref") or "").strip()
    if ref:
        for pat, ukind, tpl in _RULES:
            m = re.match(pat, ref)
            if not m or (ukind and kind and ukind != kind) or (ukind and not kind):
                continue
            groups = list(m.groups())
            if tpl.startswith("modes.") and len(groups) == 2:
                mk = _mode_key(groups[1])
                if mk is None:
                    continue
                groups[1] = mk
            if any(g in SUBSYSTEM_CODES for g in groups) or not groups or tpl.startswith("modes.peak"):
                path = tpl.format(*groups)
            else:
                continue
            if path in CATALOGUE:
                return {"path": path, "reason": "budget_ref", "budget_ref": ref, "unit": CATALOGUE[path]["unit"]}
        return None
    text = f" {(req.get('text') or '').lower()} "
    for ukind, words, tpl in _WORDS:
        if kind != ukind or not all(w in text for w in words[:1]):
            continue
        if "{sub}" in tpl:
            if not sub_code or sub_code not in SUBSYSTEM_CODES:
                continue
            path = tpl.format(sub=sub_code)
        else:
            path = tpl
        if path in CATALOGUE:
            return {"path": path, "reason": "keywords", "budget_ref": None, "unit": CATALOGUE[path]["unit"]}
    return None


# ─────────────────────────────────────────────────────────────── values

def _subsystem_codes(elements: list[dict], codes: dict[str, str]) -> dict[str, str]:
    """element id → the v2 code of its subsystem (walking up the tree)."""
    by_id = {e["id"]: e for e in elements}
    sub_code = {eid: c for c, eid in codes.items() if c in SUBSYSTEM_CODES}
    out: dict[str, str] = {}
    for e in elements:
        cur, n = e, 0
        while cur is not None and n < 30:
            if cur["id"] in sub_code:
                out[e["id"]] = sub_code[cur["id"]]
                break
            cur, n = by_id.get(cur.get("parent_id") or ""), n + 1
    return out


async def _ledger_sums(study_id: str) -> dict[str, Any]:
    """Σ of the allocation-ledger lines per budget type (agreed and all), from the table A
    fills (3.A2); empty when no line exists yet."""
    out: dict[str, Any] = {}
    try:
        from sqlalchemy import select
        from ..db._arcadia_common import get_session_factory
        from ..db.models_alloc import AllocationLedgerRow
        async with get_session_factory()() as s:
            rows = (await s.execute(select(AllocationLedgerRow).where(AllocationLedgerRow.study_id == study_id))).scalars().all()
        for r in rows:
            if r.line_kind != "allocation" or r.value is None:
                continue
            t = r.budget_type
            out.setdefault(t, {"all": 0.0, "agreed": 0.0, "lines": 0, "agreed_lines": 0})
            out[t]["all"] += float(r.value)
            out[t]["lines"] += 1
            if r.status == "agreed":
                out[t]["agreed"] += float(r.value)
                out[t]["agreed_lines"] += 1
    except Exception:  # noqa: BLE001 — no ledger table yet
        logger.debug("no allocation ledger for %s", study_id, exc_info=True)
    return out


def _allocation_rows(reqs: list[dict], prefix: str) -> dict[str, float]:
    """Subsystem code → the allocation stated by its allocation requirement
    (``budget_ref = <prefix>.<CODE>``, operator ``<=``)."""
    from ..db.requirement_repo import normalise_threshold_value
    out: dict[str, float] = {}
    for r in reqs:
        ref = str(r.get("budget_ref") or "")
        if not ref.startswith(prefix + ".") or r.get("threshold_op") != "<=":
            continue
        code = ref[len(prefix) + 1:]
        if code not in SUBSYSTEM_CODES:
            continue
        v = normalise_threshold_value(r.get("threshold_value"))
        try:
            import json
            v = float(json.loads(v) if isinstance(v, str) else v)
        except (TypeError, ValueError):
            continue
        out[code] = v
    return out


async def values(study_id: str, *, gate: str | None = None) -> dict[str, float]:
    """The catalogue figures the study can give now (path → number). Never raises."""
    from ..routers.requirements import ensure_requirements_loaded, study_requirements
    from . import rollup as rollup_mod
    from .requirement_queries import _study_elements_list, element_code_map
    out: dict[str, float] = {}
    elements = _study_elements_list(study_id)
    codes = await element_code_map(study_id, elements)
    subs = _subsystem_codes(elements, codes)
    try:
        ru = (await rollup_mod.compute(study_id, gate=gate)).as_dict()
    except Exception:  # noqa: BLE001
        ru = {}
    mass = ru.get("mass") or {}
    per: dict[str, float] = {}
    for u in mass.get("units") or []:
        c = subs.get(u.get("element_id") or "")
        if c and isinstance(u.get("with_margin"), (int, float)):
            per[c] = per.get(c, 0.0) + float(u["with_margin"])
    for c, v in per.items():
        out[f"rollup.mass.{c}.with_maturity_kg"] = round(v, 4)
    if mass.get("total_dry_kg") is not None:
        out["budget.mass_total_dry_kg"] = float(mass["total_dry_kg"])
    if mass.get("with_system_margin_kg") is not None:
        out["budget.mass_with_system_margin_kg"] = float(mass["with_system_margin_kg"])
    lim, wm = mass.get("limit_kg"), mass.get("with_maturity_kg")
    if lim and wm:
        out["budget.mass_system_margin_available_percent"] = round(100.0 * (float(lim) - float(wm)) / float(wm), 2)
    sys_mass = float(mass.get("system_margin_percent") or 0.0)
    sys_power = float((ru.get("power") or {}).get("system_margin_percent") or sys_mass)

    # per-subsystem power: the operational-orbit mix and the modes of each kind
    try:
        await _mode_values(study_id, subs, out)
    except Exception:  # noqa: BLE001 — no modes yet
        logger.debug("no mode power for %s", study_id, exc_info=True)

    # design-loop and gate figures (array EOL power, DoD, data and link margins)
    try:
        from ..routers.gates import design_params
        from ..routers.studies import get_study_store
        dp = await design_params(study_id, get_study_store().get(study_id))
    except Exception:  # noqa: BLE001
        dp = {}
    for k in ("power.sa_power_eol_w",):
        v = dp.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = float(v)
    avg = (ru.get("power") or {}).get("orbit_average_w")
    if avg and out.get("power.sa_power_eol_w") is not None:
        out["budget.power_margin_eol_percent"] = round(100.0 * (out["power.sa_power_eol_w"] - float(avg)) / float(avg), 2)
    try:
        from .key_numbers import key_numbers
        kn = await key_numbers(study_id, gate=gate)
        for src, dst in (("data.science_delivered_mb_per_day", "data.science_delivered_mb_per_day"),
                         ("data.capacity_mb_per_day", "data.capacity_mb_per_day"),
                         ("data.margin_pct", "budget.data_margin_percent")):
            v = (kn.get(src) or {}).get("value")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[dst] = float(v)
        from .data_budget import for_study
        from .export_context.sections.data_budget import daily_figures
        daily = daily_figures(await for_study(study_id, gate=gate))
        for src, dst in (("stored_hk_mb_per_day", "data.stored_hk_mb_per_day"),
                         ("rt_hk_mb_per_day", "data.realtime_hk_mb_per_day")):
            v = daily.get(src)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[dst] = float(v)
    except Exception:  # noqa: BLE001 — no modes / stations
        logger.debug("no data figures for %s", study_id, exc_info=True)
    link = dp.get("link.downlink_margin_db")
    try:
        from ..routers.studies import get_study_store
        st = get_study_store().get(study_id)
        lk = getattr(getattr(st, "requirements", None), "link", None) if st else None
        lm = (lk.get("margin_db") if isinstance(lk, dict) else getattr(lk, "margin_db", None)) if lk else None
        if isinstance(lm, (int, float)) and not isinstance(lm, bool):
            link = lm
    except Exception:  # noqa: BLE001
        pass
    if isinstance(link, (int, float)) and not isinstance(link, bool):
        out["budget.link_margin_design_case_db"] = float(link)

    # allocation closure: the ledger lines (agreed, else proposed), else the allocation rows
    await ensure_requirements_loaded()
    reqs = study_requirements(study_id)
    led = await _ledger_sums(study_id)
    for btype, prefix, key, sysm in (("mass", "mass.allocations", "alloc.mass.sum_with_margin_kg", sys_mass),
                                     ("power_avg", "power.allocations", "alloc.power.sum_with_margin_w", sys_power)):
        lines = led.get(btype) or {}
        total = lines.get("all") if lines.get("lines") else None
        if total is None:
            rows = _allocation_rows(reqs, prefix)
            total = sum(rows.values()) if rows else None
        if total is not None:
            out[key] = round(total * (1 + sysm / 100.0), 4)
    return out


async def _mode_values(study_id: str, subs: dict[str, str], out: dict[str, float]) -> None:
    from ..routers.modes import _ctx, _element_modes
    from .mode_model import _attr, _maturity_pct, in_operational_mix
    ctx = await _ctx(study_id)
    modes = _element_modes(ctx)
    by_id = {e["id"]: e for e in ctx.elements}

    def per_sub(mode: Any, with_maturity: bool = True) -> dict[str, float]:
        acc: dict[str, float] = {}
        for mem in _attr(mode, "members") or []:
            e = by_id.get(mem.get("element_id"))
            c = subs.get(mem.get("element_id") or "")
            if e is None or c is None:
                continue
            duty = mem.get("duty") if mem.get("duty") is not None else 1.0
            p = float(mem.get("power_w") or 0.0) * float(duty)
            acc[c] = acc.get(c, 0.0) + p * ((1 + _maturity_pct(e) / 100) if with_maturity else 1.0)
        return acc

    mix = [(m, float(_attr(m, "orbit_fraction") or 0.0)) for m in modes if in_operational_mix(m)]
    tot = sum(f for _, f in mix)
    if tot > 0:
        avg: dict[str, float] = {}
        for m, f in mix:
            for c, p in per_sub(m).items():
                avg[c] = avg.get(c, 0.0) + p * f / tot
        for c, v in avg.items():
            out[f"rollup.power.{c}.orbit_average_with_maturity_w"] = round(v, 4)
    for m in modes:
        kind = str(_attr(m, "kind") or "")
        for c, p in per_sub(m, with_maturity=False).items():
            for k in ([kind] if kind in MODE_KINDS else []) + ["peak"]:
                key = f"modes.{k}.{c}.power_w"
                out[key] = round(max(out.get(key, 0.0), p), 4)
    try:
        from ..routers.modes import mode_energy
        res = await mode_energy(study_id, gate=None)
        dod = ((res.get("operational_orbit") or {}).get("dod_percent"))
        if isinstance(dod, (int, float)) and not isinstance(dod, bool):
            out["power.battery_dod_operational_pct"] = float(dod)
    except Exception:  # noqa: BLE001 — no battery or modes
        logger.debug("no depth of discharge for %s", study_id, exc_info=True)


# ─────────────────────────────────────────────────────────────── rows, accept

async def binding_rows(study_id: str, *, with_values: bool = True) -> dict[str, Any]:
    """Every requirement with a numeric threshold: its current binding, the proposal and, when
    bound, the compliance tracker's verdict. ``{catalogue, rows, counts}``."""
    from ..routers.requirements import ensure_requirements_loaded, study_requirements
    from .compliance_tracker import ComplianceTracker
    from .requirement_queries import _study_elements_list, element_code_map
    await ensure_requirements_loaded()
    reqs = [r for r in study_requirements(study_id) if r.get("level") != "stakeholder"]
    elements = _study_elements_list(study_id)
    codes = await element_code_map(study_id, elements)
    subs = _subsystem_codes(elements, codes)
    vals = await values(study_id) if with_values else {}
    tracker = ComplianceTracker()
    rows = []
    for r in reqs:
        if not r.get("threshold_op") or r.get("threshold_value") in (None, ""):
            continue
        sub = subs.get(r.get("element_id") or "")
        prop = propose(r, sub)
        cur = r.get("threshold_param_path")
        if not prop and not cur and not r.get("budget_ref"):
            continue
        row = {"requirement_id": r["id"], "code": r.get("code"), "budget_ref": r.get("budget_ref"),
               "threshold_op": r.get("threshold_op"), "threshold_value": r.get("threshold_value"),
               "threshold_unit": r.get("threshold_unit"), "current_path": cur,
               "binding": (r.get("external_ids") or {}).get("binding"),
               "proposal": prop, "accepted": bool(cur and prop and cur == prop["path"]),
               "status": None, "achieved": None, "margin_pct": None}
        if cur and with_values:
            res = tracker.evaluate_single(r, vals)
            row.update(status=res.status, achieved=res.achieved_value, margin_pct=res.margin_pct)
        rows.append(row)
    rows.sort(key=lambda x: str(x["code"] or ""))
    cat = [{**v, "value": vals.get(p)} for p, v in CATALOGUE.items()]
    return {"study_id": study_id, "catalogue": cat, "rows": rows, "values": vals,
            "counts": {"budget_ref": sum(1 for x in rows if x["budget_ref"]),
                       "proposed": sum(1 for x in rows if x["proposal"]),
                       "bound": sum(1 for x in rows if x["current_path"]),
                       "accepted": sum(1 for x in rows if x["accepted"]),
                       "pass": sum(1 for x in rows if x["status"] == "pass"),
                       "fail": sum(1 for x in rows if x["status"] == "fail"),
                       "untestable": sum(1 for x in rows if x["status"] == "untestable")}}


async def bind(req: dict, path: str | None, *, source: str, by: str | None = None) -> dict:
    """Set (or clear, ``path=None``) the row's ``threshold_param_path`` and record the binding."""
    from ..db.requirement_repo import db_update_requirement
    ext = dict(req.get("external_ids") or {})
    if path:
        ext["binding"] = {"path": path, "source": source, "by": by or "",
                          "accepted_at": datetime.now(timezone.utc).isoformat()}
    else:
        ext.pop("binding", None)
    req["threshold_param_path"] = path or None
    req["external_ids"] = ext or None
    await db_update_requirement(req["id"], req)
    return req


async def accept(study_id: str, requirement_ids: list[str] | None = None, *, by: str | None = None) -> dict:
    """Accept the proposals of ``requirement_ids`` (every proposed row when None). A row bound
    by hand to another path keeps it unless it is named explicitly."""
    from ..routers.requirements import _requirements
    data = await binding_rows(study_id, with_values=False)
    wanted = set(requirement_ids or [])
    done: list[str] = []
    for row in data["rows"]:
        prop = row["proposal"]
        if not prop or row["accepted"]:
            continue
        if wanted and row["requirement_id"] not in wanted:
            continue
        if not wanted and (prop.get("reason") != "budget_ref" or (
                row["current_path"] and row["current_path"] != prop["path"]
                and (row.get("binding") or {}).get("source") == "manual")):
            continue          # a keyword guess or a hand-made binding is only taken when named
        req = _requirements.get(row["requirement_id"])
        if req is None:
            continue
        await bind(req, prop["path"], source="proposal", by=by)
        done.append(row["code"])
    if done:
        from ..routers._arcadia_events import broadcast_mutation
        await broadcast_mutation(study_id, "requirements_bound", "study", study_id, {"codes": done})
    return {"study_id": study_id, "accepted": len(done), "codes": done}


__all__ = ["CATALOGUE", "accept", "bind", "binding_rows", "propose", "unit_kind", "values"]
