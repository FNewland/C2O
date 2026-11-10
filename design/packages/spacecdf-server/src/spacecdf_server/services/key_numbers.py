"""The study's key numbers, one flat dictionary every negotiation and preview quotes (wave 3).

Owner: A for step 0, **L after step 0** (3.L6 impact preview). H (negotiation records, 3.H6)
and S read it; a new key is added by L on request (W0_SEAMS §9).

    from spacecdf_server.services.key_numbers import key_numbers
    kn = await key_numbers(study_id)        # {key: {value, unit, source, owner_seat}}
    kn["mass.with_system_margin_kg"]["value"]

Keys are stable dotted names; ``value`` is None when the study cannot give it yet (no equipment,
no modes, no stations). ``source`` names the service the figure comes from, ``owner_seat`` the
seat that answers for it. Pure read: it never writes. Filled from the one roll-up
(``services/rollup.py``) and the data budget (``services/data_budget.py``).

TODO(L, 3.L6): energy (worst-case depth of discharge), contacts per station, disposal lifetime,
link margin of the design case; the dry-run variant used by the impact preview.
"""
from __future__ import annotations

import logging
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


def _dig(d: Any, path: tuple[str, ...]) -> Any:
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _entry(value: Any, unit: str, source: str, seat: str) -> dict[str, Any]:
    return {"value": value, "unit": unit, "source": source, "owner_seat": seat}


async def key_numbers(study_id: str, *, gate: str | None = None) -> dict[str, dict[str, Any]]:
    """The study's key numbers (see the module doc). Never raises for a missing model."""
    from . import rollup
    out: dict[str, dict[str, Any]] = {}
    try:
        ru = (await rollup.compute(study_id, gate=gate)).as_dict()
    except Exception:  # noqa: BLE001 — no study / no elements: every roll-up key is None
        logger.debug("key_numbers: roll-up failed for %s", study_id, exc_info=True)
        ru = {}
    for key, (unit, seat, path) in ROLLUP_KEYS.items():
        out[key] = _entry(_dig(ru, path), unit, "rollup", seat)
    lim, wsm = out["mass.limit_kg"]["value"], out["mass.with_system_margin_kg"]["value"]
    out["mass.margin_to_limit_kg"] = _entry(round(lim - wsm, 3) if lim is not None and wsm is not None else None,
                                            "kg", "rollup", "systems_engineer")
    daily: dict[str, Any] = {}
    try:
        from .data_budget import for_study
        from .export_context.sections.data_budget import daily_figures
        daily = daily_figures(await for_study(study_id, gate=gate))
    except Exception:  # noqa: BLE001 — no modes / stations yet
        logger.debug("key_numbers: data budget failed for %s", study_id, exc_info=True)
    for key, (unit, seat, fld) in DATA_KEYS.items():
        out[key] = _entry(daily.get(fld), unit, "data_budget", seat)
    return out


__all__ = ["DATA_KEYS", "ROLLUP_KEYS", "key_numbers"]
