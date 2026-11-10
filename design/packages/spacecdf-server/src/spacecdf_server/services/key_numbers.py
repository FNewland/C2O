"""The study's key numbers, one flat dictionary every negotiation and preview quotes (wave 3).

Owner: A for step 0, **L after step 0** (3.L6 impact preview). H (negotiation records, 3.H6)
and S read it; a new key is added by L on request (W0_SEAMS §9).

    from spacecdf_server.services.key_numbers import key_numbers
    kn = await key_numbers(study_id)        # {key: {value, unit, source, owner_seat}}
    kn["mass.with_system_margin_kg"]["value"]

Keys are stable dotted names; ``value`` is None when the study cannot give it yet (no equipment,
no modes, no stations). ``source`` names the service the figure comes from, ``owner_seat`` the
seat that answers for it. Pure read: it never writes. Filled from the one roll-up
(``services/rollup.py``), the Modes energy balance (``services/mode_model.py``), the data budget
(``services/data_budget.py``) and the disposal analysis (``services/licensing.py``).

Two entry points share one code path:

* ``key_numbers(study_id)`` — the stored study;
* ``numbers_from_context(ctx, rows)`` — the same figures from an ``AnalysisContext`` the caller may
  have changed in memory (the dry run of the impact preview, ``services/impact_preview.py``).
  Nothing is written: the context is a copy and every service used is a pure function of it.

Wave 3 (3.L6) keys beyond step 0: the operational mode shares (downlink share stored and proposed
from the union contact time, 3.H3's rule), the Communications orbit-average load (the Systems
seat's allocation line), the worst depth of discharge, contacts per station, windows and longest
gap, the design link margin and the disposal lifetimes with and without the sail.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

#: key -> (unit, owner seat, roll-up path)
ROLLUP_KEYS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "mass.cbe_kg": ("kg", "systems_engineer", ("mass", "cbe_kg")),
    "mass.with_maturity_kg": ("kg", "systems_engineer", ("mass", "with_maturity_kg")),
    "mass.with_system_margin_kg": ("kg", "systems_engineer", ("mass", "with_system_margin_kg")),
    "mass.system_margin_percent": ("%", "systems_engineer", ("mass", "system_margin_percent")),
    "mass.limit_kg": ("kg", "systems_engineer", ("mass", "limit_kg")),
    "power.orbit_average_w": ("W", "power_engineer", ("power", "orbit_average_w")),
    "power.orbit_average_with_maturity_w": ("W", "power_engineer", ("power", "orbit_average_with_maturity_w")),
    "power.orbit_average_with_margin_w": ("W", "power_engineer", ("power", "orbit_average_with_margin_w")),
    "power.system_margin_percent": ("%", "power_engineer", ("power", "system_margin_percent")),
}

#: key -> (unit, owner seat, data-budget daily figure)
DATA_KEYS: dict[str, tuple[str, str, str]] = {
    "data.capacity_mb_per_day": ("MB/day", "comms_engineer", "capacity_mb_per_day"),
    "data.demand_mb_per_day": ("MB/day", "comms_engineer", "demand_mb_per_day"),
    "data.margin_pct": ("%", "comms_engineer", "margin_pct"),
    "data.science_delivered_mb_per_day": ("MB/day", "payload_lead", "science_delivered_mb_per_day"),
    "contacts.union_min_per_day": ("min/day", "mission_analyst", "union_min_per_day"),
}

#: wave 3 (3.L6): key -> (unit, owner seat, source); filled by ``numbers_from_context``
EXTRA_KEYS: dict[str, tuple[str, str, str]] = {
    "modes.downlink_share_pct": ("%", "power_engineer", "modes"),
    "modes.downlink_share_proposed_pct": ("%", "mission_analyst", "data_budget"),
    "modes.imaging_share_pct": ("%", "power_engineer", "modes"),
    "power.comms_orbit_average_w": ("W", "systems_engineer", "modes"),
    "energy.worst_dod_percent": ("%", "power_engineer", "modes.energy"),
    "energy.operational_balance_wh": ("Wh/orbit", "power_engineer", "modes.energy"),
    "contacts.windows_per_day": ("1/day", "mission_analyst", "data_budget"),
    "contacts.longest_gap_h": ("h", "mission_analyst", "data_budget"),
    "contacts.stations": ("", "mission_analyst", "data_budget"),
    "link.design_margin_db": ("dB", "comms_engineer", "link_cases"),
    "disposal.lifetime_with_sail_worst_y": ("y", "propulsion_engineer", "disposal"),
    "disposal.lifetime_without_sail_worst_y": ("y", "propulsion_engineer", "disposal"),
    "disposal.compliant": ("", "propulsion_engineer", "disposal"),
}

DAY_MIN = 1440.0


def _dig(d: Any, path: tuple[str, ...]) -> Any:
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _entry(value: Any, unit: str, source: str, seat: str) -> dict[str, Any]:
    return {"value": value, "unit": unit, "source": source, "owner_seat": seat}


def _slug(s: Any) -> str:
    s = re.sub(r"^\s*(gs|ground station)\s+", "", str(s or ""), flags=re.I)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "station"


# ───────────────────────────────────────────────────────────── one code path

def _gate_of(ctx, gate: str | None) -> str | None:
    if gate is not None:
        return gate
    try:
        from ..routers.gates import study_margin_gate
        return study_margin_gate(ctx.study)
    except Exception:  # noqa: BLE001
        return None


def energy(ctx, gate: str | None) -> dict[str, Any] | None:
    """The Modes energy balance of a context (as ``GET /modes/energy``); None without modes."""
    from . import mode_model as mm
    from .margin_policy import system_margin_percent
    from ..routers.modes import _element_modes, _power_sources
    modes = _element_modes(ctx)
    if not modes:
        return None
    sa, _sa_src, bat, _bat_src = _power_sources(ctx)
    return mm.energy_balance(modes, ctx.elements, period_s=ctx.orbit.get("period_s") or 5700.0,
                             eclipse_fraction=ctx.orbit.get("eclipse_fraction"), sa_power_eol_w=sa,
                             battery_wh=bat, system_margin_percent=system_margin_percent(gate, "power"),
                             battery_efficiency=None, max_dod_percent=ctx.power.get("battery_dod_percent"))


def _orbit_average(res: dict | None) -> tuple[float | None, float | None]:
    """(nominal, with maturity) orbit-average load of the operational mix (``rollup._orbit_average``)."""
    if not res:
        return None, None
    ops = res.get("operational_orbit") or {}
    mix = [(m.get("mode_id"), float(m.get("orbit_fraction") or 0)) for m in ops.get("modes") or []]
    tot = sum(f for _, f in mix)
    if not mix or tot <= 0:
        return None, None
    rows = {r.get("mode_id"): r for r in res.get("modes") or []}

    def avg(key: str) -> float:
        w = 0.0
        for mid, f in mix:
            r = rows.get(mid) or {}
            v = r.get(key) if r.get(key) is not None else r.get("power_cbe_w")
            w += float(v or 0.0) * f
        return w / tot
    return avg("power_cbe_w"), avg("power_with_maturity_w")


def _comms_ids(ctx) -> set[str]:
    """Element ids of the Communications (TT&C) subtree of the space segment."""
    by_parent: dict[str, list[dict]] = {}
    for e in ctx.elements:
        by_parent.setdefault(e.get("parent_id") or "", []).append(e)
    roots = [e for e in ctx.elements if e.get("element_type") == "subsystem"
             and (e.get("subsystem_domain") or "") in ("ttc", "comms", "communications")]
    out: set[str] = set()
    stack = list(roots)
    while stack:
        e = stack.pop()
        out.add(e["id"])
        stack.extend(by_parent.get(e["id"], []))
    out |= {e["id"] for e in ctx.elements if e.get("element_type") == "component"
            and (e.get("subsystem_domain") or "") in ("ttc", "comms", "communications")}
    return out


def mode_shares(ctx) -> dict[str, Any]:
    """Operational mix shares by kind and the Communications orbit-average load (CBE)."""
    from .mode_model import in_operational_mix
    from ..routers.modes import _element_modes
    modes = [m for m in _element_modes(ctx) if in_operational_mix(m)]
    tot = sum(float(m.orbit_fraction or 0) for m in modes)
    if tot <= 0:
        return {"downlink": None, "imaging": None, "comms_w": None}
    comms = _comms_ids(ctx)
    share: dict[str, float] = {}
    comms_w = 0.0
    for m in modes:
        f = float(m.orbit_fraction or 0) / tot
        share[m.kind or "custom"] = share.get(m.kind or "custom", 0.0) + f
        comms_w += f * sum(float(r.get("power_w") or 0) * float(r.get("duty") if r.get("duty") is not None else 1.0)
                           for r in m.members if r.get("element_id") in comms)
    return {"downlink": share.get("downlink"), "imaging": share.get("imaging"), "comms_w": comms_w}


def _rollup(ctx, gate: str | None, oa: float | None, oa_mat: float | None) -> dict:
    from .rollup import rollup_elements
    study = ctx.study
    params: dict[str, Any] = {}
    target = None
    if study is not None:
        its = getattr(study, "iterations", None) or []
        if its:
            params.update(getattr(its[-1], "parameter_snapshot", None) or {})
        req = getattr(study, "requirements", None)
        target = getattr(req, "target_mass_kg", None) if req is not None else None
    els = [e for e in ctx.elements if not e.get("deleted_at")]
    return rollup_elements(els, gate=gate, params=params, orbit_average_w=oa, orbit_average_with_maturity_w=oa_mat,
                           orbit_average_source="modes.energy" if oa is not None else None, target_mass_kg=target,
                           study_id=ctx.study_id,
                           margin_policy=getattr(study, "margin_policy", None) if study is not None else None).as_dict()


def _design_margin(ctx) -> float | None:
    for c in ctx.link_cases or []:
        if c.get("direction") == "downlink" and c.get("is_design_case"):
            m = c.get("margin_db")
            if m is None:
                m = (c.get("results") or {}).get("margin_db")
            return round(float(m), 2) if isinstance(m, (int, float)) else None
    return None


def _disposal(ctx, ru: dict) -> dict:
    from .licensing import disposal_analysis
    return disposal_analysis(ctx.study, ctx.elements, ru, None)


async def numbers_from_context(ctx, rows: list[dict] | None, *, gate: str | None = None, data: bool = True,
                               disposal: bool = True, days: float = 30.0, step_s: float = 10.0) -> dict[str, dict[str, Any]]:
    """Every key number from an ``AnalysisContext`` and the CDR rows (pure: never writes).

    ``data=False`` skips the contact prediction and data budget (the slow part); ``disposal=False``
    the decay runs."""
    out: dict[str, dict[str, Any]] = {}
    g = _gate_of(ctx, gate)
    try:
        res = energy(ctx, g)
    except Exception:  # noqa: BLE001 — no rule config / no modes
        logger.debug("key_numbers: energy failed", exc_info=True)
        res = None
    oa, oa_mat = _orbit_average(res)
    try:
        ru = _rollup(ctx, g, oa, oa_mat)
    except Exception:  # noqa: BLE001
        logger.debug("key_numbers: roll-up failed", exc_info=True)
        ru = {}
    for key, (unit, seat, path) in ROLLUP_KEYS.items():
        out[key] = _entry(_dig(ru, path), unit, "rollup", seat)
    lim, wsm = out["mass.limit_kg"]["value"], out["mass.with_system_margin_kg"]["value"]
    out["mass.margin_to_limit_kg"] = _entry(round(lim - wsm, 3) if lim is not None and wsm is not None else None,
                                            "kg", "rollup", "systems_engineer")
    extra: dict[str, Any] = {}
    try:
        sh = mode_shares(ctx)
        extra["modes.downlink_share_pct"] = round(100 * sh["downlink"], 2) if sh["downlink"] is not None else None
        extra["modes.imaging_share_pct"] = round(100 * sh["imaging"], 2) if sh["imaging"] is not None else None
        extra["power.comms_orbit_average_w"] = round(sh["comms_w"], 3) if sh["comms_w"] is not None else None
    except Exception:  # noqa: BLE001
        logger.debug("key_numbers: mode shares failed", exc_info=True)
    if res:
        dods = [r.get("dod_percent") for r in res.get("modes") or [] if r.get("dod_percent") is not None]
        ops = res.get("operational_orbit") or {}
        extra["energy.worst_dod_percent"] = max([*dods, ops.get("dod_percent") or 0.0]) if dods else ops.get("dod_percent")
        extra["energy.operational_balance_wh"] = ops.get("balance_wh")
    extra["link.design_margin_db"] = _design_margin(ctx)
    daily: dict[str, Any] = {}
    if data:
        try:
            from .data_budget import from_context
            from .export_context.sections.data_budget import daily_figures
            b = from_context(ctx, rows or [], include_degraded=False, gate=g, days=days, step_s=step_s)
            daily = daily_figures(b)
            ct = b.get("contacts") or {}
            extra["contacts.windows_per_day"] = ct.get("windows_per_day")
            gap = (ct.get("union") or {}).get("longest_gap_h")
            extra["contacts.longest_gap_h"] = round(float(gap), 2) if isinstance(gap, (int, float)) else None
            stations = [r for r in ((b.get("network") or {}).get("stations") or []) if r.get("status") != "excluded"]
            extra["contacts.stations"] = sorted(str(r.get("name")) for r in stations)
            for r in stations:
                out[f"contacts.station.{_slug(r.get('name'))}_min_per_day"] = _entry(
                    r.get("contact_min_per_day"), "min/day", "data_budget", "mission_analyst")
        except Exception:  # noqa: BLE001 — no modes / stations yet
            logger.debug("key_numbers: data budget failed", exc_info=True)
    for key, (unit, seat, fld) in DATA_KEYS.items():
        out[key] = _entry(daily.get(fld), unit, "data_budget", seat)
    u = daily.get("union_min_per_day")
    extra["modes.downlink_share_proposed_pct"] = round(100 * float(u) / DAY_MIN, 2) if isinstance(u, (int, float)) else None
    if disposal and ctx.study is not None:
        try:
            d = _disposal(ctx, ru)
            ws, wo = d.get("lifetime_with_sail_y") or {}, d.get("lifetime_without_sail_y") or {}
            extra["disposal.lifetime_with_sail_worst_y"] = max(ws.values()) if ws else None
            extra["disposal.lifetime_without_sail_worst_y"] = max(wo.values()) if wo else None
            extra["disposal.compliant"] = d.get("compliant")
        except Exception:  # noqa: BLE001
            logger.debug("key_numbers: disposal failed", exc_info=True)
    for key, (unit, seat, src) in EXTRA_KEYS.items():
        out[key] = _entry(extra.get(key), unit, src, seat)
    return out


async def key_numbers(study_id: str, *, gate: str | None = None, data: bool = True,
                      disposal: bool = True) -> dict[str, dict[str, Any]]:
    """The study's key numbers (see the module doc). Never raises for a missing model."""
    from .analysis_context import build_context
    try:
        ctx = await build_context(study_id)
    except Exception:  # noqa: BLE001 — no study: every key is None
        logger.debug("key_numbers: context failed for %s", study_id, exc_info=True)
        ctx = None
    rows: list[dict] = []
    if data:
        try:
            from ..db import cdr_repo
            rows = await cdr_repo.list_rows(study_id)
        except Exception:  # noqa: BLE001
            rows = []
    if ctx is None:
        out = {k: _entry(None, u, "rollup", s) for k, (u, s, _p) in ROLLUP_KEYS.items()}
        out["mass.margin_to_limit_kg"] = _entry(None, "kg", "rollup", "systems_engineer")
        out.update({k: _entry(None, u, "data_budget", s) for k, (u, s, _f) in DATA_KEYS.items()})
        out.update({k: _entry(None, u, src, s) for k, (u, s, src) in EXTRA_KEYS.items()})
        return out
    return await numbers_from_context(ctx, rows, gate=gate, data=data, disposal=disposal)


__all__ = ["DATA_KEYS", "EXTRA_KEYS", "ROLLUP_KEYS", "energy", "key_numbers", "mode_shares", "numbers_from_context"]
