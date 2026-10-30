"""SpaceCDF — Conventions for ``AgentResult.extras`` keys.

This module defines the schema of structured intermediates that each agent
may publish on :attr:`AgentResult.extras`.  The DOCX exporter consults these
keys when rendering per-domain chapters and figures.

Every key is optional — the exporter falls back to summary tables if a key
is missing.  Use the helper builders below from inside agents so the schema
stays consistent.

Conventions (key → shape):

    "orbit.delta_v_breakdown"     list[{"name": str, "value_ms": float, "rationale": str}]
    "orbit.disturbance_torques"    list[{"source": str, "value_nm": float}]
    "orbit.contact_window"         dict {"per_day_s": float, "ground_station": str,
                                         "max_elevation_deg": float}
    "link.waterfall"               list[{"label": str, "delta_db": float}]
    "link.assumptions"             list[str]
    "power.modes"                  list[{"name": str, "duty_cycle": float,
                                          "power_w": float, "load_components": [...]}]
    "power.battery"                dict {"dod_percent": float, "cycles": int,
                                         "capacity_wh": float, "chemistry": str}
    "thermal.nodes"                list[{"name": str, "hot_c": float, "cold_c": float,
                                         "limit_hot_c": float, "limit_cold_c": float}]
    "thermal.surfaces"             list[{"surface": str, "alpha": float, "epsilon": float}]
    "aocs.disturbance_breakdown"   list[{"source": str, "torque_nm": float}]
    "aocs.pointing_budget"         list[{"contributor": str, "value_arcsec": float}]
    "propulsion.tsiolkovsky"       dict {"delta_v_ms": float, "isp_s": float,
                                         "m0_kg": float, "mf_kg": float,
                                         "propellant_kg": float}
    "propulsion.thruster"          dict {"name": str, "thrust_n": float, "type": str,
                                         "isp_s": float, "duty_cycle": float}
    "mass.rollup"                  list[{"subsystem": str, "nominal_kg": float,
                                         "margin_percent": float}]
    "data.summary"                 dict {"per_day_gb": float, "downlink_capacity_gb": float,
                                          "storage_required_gb": float,
                                          "compression_ratio": float}
    "reliability.fmeca"            list[{"item": str, "failure_mode": str,
                                          "cause": str, "effect": str,
                                          "severity": int, "occurrence": int,
                                          "detection": int, "rpn": int,
                                          "mitigation": str}]
    "reliability.failure_rates"    list[{"subsystem": str, "lambda_per_hour": float,
                                          "redundancy": str}]
    "cost.wbs"                     list[{"wbs_id": str, "name": str,
                                          "ddte_keur": float, "recurring_keur": float,
                                          "total_keur": float}]
    "risk.register"                list[{"id": str, "name": str, "likelihood": int,
                                          "severity": int, "score": int,
                                          "mitigation": str, "owner": str}]
    "debris.compliance"            dict {"lifetime_years": float,
                                          "casualty_risk": float,
                                          "passivation_score": float,
                                          "method": str}
    "radiation.tid"                dict {"krad_per_year": float, "shielding_mm_al": float,
                                          "margin_factor": float}
"""
from __future__ import annotations

from typing import Any


def delta_v_breakdown(*items: tuple[str, float, str]) -> list[dict[str, Any]]:
    """Build a delta-V breakdown list.  Each item: (name, value_ms, rationale)."""
    return [{"name": n, "value_ms": float(v or 0), "rationale": r}
            for (n, v, r) in items if v]


def link_waterfall(*items: tuple[str, float]) -> list[dict[str, Any]]:
    """Build a link budget waterfall list.  Each item: (label, delta_db)."""
    return [{"label": l, "delta_db": float(v)} for (l, v) in items]


def thermal_node(name: str, *, hot_c: float, cold_c: float,
                 limit_hot_c: float | None = None,
                 limit_cold_c: float | None = None) -> dict[str, Any]:
    out = {"name": name, "hot_c": float(hot_c), "cold_c": float(cold_c)}
    if limit_hot_c is not None:
        out["limit_hot_c"] = float(limit_hot_c)
    if limit_cold_c is not None:
        out["limit_cold_c"] = float(limit_cold_c)
    return out


def fmeca_row(*, item: str, failure_mode: str, cause: str, effect: str,
              severity: int, occurrence: int, detection: int,
              mitigation: str = "") -> dict[str, Any]:
    return {
        "item": item, "failure_mode": failure_mode,
        "cause": cause, "effect": effect,
        "severity": int(severity), "occurrence": int(occurrence),
        "detection": int(detection),
        "rpn": int(severity) * int(occurrence) * int(detection),
        "mitigation": mitigation,
    }


def risk_entry(*, id: str, name: str, likelihood: int, severity: int,
               mitigation: str = "", owner: str = "") -> dict[str, Any]:
    return {
        "id": id, "name": name,
        "likelihood": int(likelihood), "severity": int(severity),
        "score": int(likelihood) * int(severity),
        "mitigation": mitigation, "owner": owner,
    }
