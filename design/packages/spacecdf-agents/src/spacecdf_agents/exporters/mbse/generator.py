"""ECSS-E-TM-10-25A-style MBSE JSON export.

Schema overview (loosely aligned with ECSS-E-TM-10-25A Annex A data model):

{
    "schema":       "spacecdf.mbse.v1",
    "ecss_profile": "ECSS-E-TM-10-25A-like",
    "generated":    "<iso timestamp>",

    "site_directory": {
        "name": "SpaceCDF",
        "version": "0.1.0"
    },

    "engineering_model": {
        "id":    "<study id>",
        "name":  "<study name>",
        "phase": "<phase_0|phase_a|phase_b1>",
        "iid":   "urn:spacecdf:study:<id>",

        "reference_data_library": {
            "units":            [ { "id": "kg", "name": "kilogram" }, ... ],
            "parameter_types":  [ { "id": "mass", "name": "Mass", "unit": "kg" }, ... ],
            "categories":       [ "EPS", "AOCS", "TCS", "TTC", "Propulsion",
                                  "Structures", "OBDH", "Payload", "Orbit" ]
        },

        "blocks": [
            { "id":          "<domain>",
              "name":        "<Domain Name>",
              "kind":        "subsystem",
              "owner":       "<position_id>",
              "contains":    [ <block_ids> ],
              "parameters":  [ <parameter_ids> ] }
        ],

        "parameters": [
            { "id":         "power.total_sunlight_w",
              "name":       "<human name>",
              "value":      123.4,
              "unit":       "W",
              "domain":     "power",
              "source":     "computed",
              "confidence": 0.8,
              "margin_percent": 20.0,
              "owning_block": "power",
              "satisfies":  [ "REQ-PWR-001" ] }
        ],

        "requirements": [
            { "id":     "REQ-PWR-001",
              "text":   "The EPS shall ...",
              "rationale": "...",
              "verification_method": "analysis",
              "parameter_ids": [ "power.total_sunlight_w" ],
              "owning_block": "power" }
        ],

        "applicable_standards": [ "ECSS-E-ST-10C Rev.1", ... ],
        "trace_links": [
            { "source": "requirements/REQ-PWR-001",
              "target": "parameters/power.total_sunlight_w",
              "kind":   "satisfies" }
        ]
    }
}

This is consumable by any downstream SysML importer and is diff-friendly for
version control. Clause references (when cited in rationale / text) use the
ECSS ID format surfaced by the fine-grained ECSS reference skills.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "spacecdf.mbse.v1"
ECSS_PROFILE = "ECSS-E-TM-10-25A-like"


# Canonical subsystem/domain → human name + kind
_DOMAIN_META: dict[str, dict[str, str]] = {
    "orbit":       {"name": "Orbit",              "kind": "system"},
    "payload":     {"name": "Payload",            "kind": "subsystem"},
    "power":       {"name": "Electrical Power",   "kind": "subsystem"},
    "aocs":        {"name": "AOCS",               "kind": "subsystem"},
    "thermal":     {"name": "Thermal Control",    "kind": "subsystem"},
    "link":        {"name": "Communications",     "kind": "subsystem"},
    "ttc":         {"name": "TTC",                "kind": "subsystem"},
    "propulsion":  {"name": "Propulsion",         "kind": "subsystem"},
    "structures":  {"name": "Structures",         "kind": "subsystem"},
    "obdh":        {"name": "On-Board Data Handling", "kind": "subsystem"},
    "data":        {"name": "Data Budget",        "kind": "aggregate"},
    "mass":        {"name": "Mass Budget",        "kind": "aggregate"},
    "cost":        {"name": "Cost",               "kind": "aggregate"},
    "risk":        {"name": "Risk",               "kind": "aggregate"},
    "trl":         {"name": "Technology Readiness", "kind": "aggregate"},
    "systems":     {"name": "System",             "kind": "system"},
    "mission":     {"name": "Mission",            "kind": "system"},
}

# Engineering-domain → responsible CDF position
_DOMAIN_POSITION: dict[str, str] = {
    "orbit": "mission_analyst",
    "payload": "payload_lead",
    "power": "power_engineer",
    "aocs": "aocs_engineer",
    "thermal": "thermal_engineer",
    "link": "comms_engineer",
    "ttc": "comms_engineer",
    "propulsion": "propulsion_engineer",
    "structures": "structures_engineer",
    "cost": "cost_engineer",
}


def _extract_unit_library(parameters: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build a unique unit list for the reference data library."""
    units: dict[str, dict[str, str]] = {}
    common = {
        "kg": "kilogram", "g": "gram", "W": "watt", "Wh": "watt-hour",
        "V": "volt", "A": "ampere", "km": "kilometre", "m": "metre",
        "s": "second", "deg": "degree", "deg/s": "degree per second",
        "K": "kelvin", "°C": "celsius", "dB": "decibel", "dBi": "decibel isotropic",
        "bps": "bit per second", "Mbps": "megabit per second",
        "GB": "gigabyte", "GB/day": "gigabyte per day",
        "m/s": "metre per second", "MEUR": "million euro", "keur": "thousand euro",
        "years": "year", "%": "percent", "N": "newton", "Ns": "newton-second",
        "Nm": "newton-metre", "Nms": "newton-metre-second",
    }
    for p in parameters:
        u = p.get("unit", "")
        if not u:
            continue
        if u not in units:
            units[u] = {"id": u, "name": common.get(u, u)}
    return sorted(units.values(), key=lambda d: d["id"])


def _build_blocks(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group parameters by domain and emit a SysML-like block per domain."""
    domains: dict[str, list[str]] = {}
    for p in parameters:
        d = p.get("domain") or p.get("id", "").split(".")[0]
        domains.setdefault(d, []).append(p["id"])

    blocks: list[dict[str, Any]] = []
    # A root Spacecraft block composes all subsystem blocks
    root_contains: list[str] = []
    for d in sorted(domains.keys()):
        meta = _DOMAIN_META.get(d, {"name": d.title(), "kind": "subsystem"})
        block = {
            "id": d,
            "name": meta["name"],
            "kind": meta["kind"],
            "owner": _DOMAIN_POSITION.get(d),
            "contains": [],
            "parameters": sorted(domains[d]),
        }
        blocks.append(block)
        if meta["kind"] in ("subsystem", "aggregate"):
            root_contains.append(d)

    # Prepend the root Spacecraft block
    blocks.insert(0, {
        "id": "Spacecraft",
        "name": "Spacecraft",
        "kind": "block",
        "owner": "systems_engineer",
        "contains": sorted(root_contains),
        "parameters": [],
    })
    return blocks


def _build_trace_links(
    parameters: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Emit satisfies / derivedFrom links between requirements and parameters."""
    out: list[dict[str, str]] = []
    for r in requirements:
        for pid in r.get("parameter_ids", []) or []:
            out.append({
                "source": f"requirements/{r['id']}",
                "target": f"parameters/{pid}",
                "kind": "satisfies",
            })
    # Hierarchical requirement links
    for r in requirements:
        parent = r.get("parent_id")
        if parent:
            out.append({
                "source": f"requirements/{r['id']}",
                "target": f"requirements/{parent}",
                "kind": "derivedFrom",
            })
    return out


def _normalise_parameters(state_parameters: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert the design state parameter dict into a stable list form."""
    out: list[dict[str, Any]] = []
    for pid in sorted(state_parameters.keys()):
        p = state_parameters[pid]
        # Allow dict or ParameterValue-like objects
        get = p.get if isinstance(p, dict) else lambda k, d=None: getattr(p, k, d)
        source = get("source")
        if hasattr(source, "value"):
            source = source.value
        out.append({
            "id": pid,
            "name": get("name", pid),
            "value": get("value"),
            "unit": get("unit", ""),
            "domain": get("domain", pid.split(".")[0] if "." in pid else ""),
            "source": source or "unknown",
            "confidence": get("confidence", 0.8),
            "margin_percent": get("margin_percent", 20.0),
            "owning_block": get("domain", pid.split(".")[0] if "." in pid else ""),
            "equipment_id": get("equipment_id"),
            "rationale": get("rationale", ""),
        })
    return out


def _normalise_requirements(requirements: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in requirements or []:
        get = r.get if isinstance(r, dict) else lambda k, d=None: getattr(r, k, d)
        vm = get("verification_method", "analysis")
        if hasattr(vm, "value"):
            vm = vm.value
        out.append({
            "id": get("id"),
            "text": get("text"),
            "rationale": get("rationale", ""),
            "verification_method": vm or "analysis",
            "parameter_ids": list(get("parameter_ids", []) or []),
            "owning_block": get("domain", ""),
            "threshold": get("threshold"),
            "threshold_max": get("threshold_max"),
            "operator": get("operator", ""),
            "unit": get("unit", ""),
            "margin_policy_percent": get("margin_policy_percent", 20.0),
            "parent_id": get("parent_id"),
        })
    return out


# --- Public entry point ----------------------------------------------------

def generate_mbse_export(
    *,
    study_id: str,
    study_name: str,
    phase: str,
    parameters: dict[str, Any],
    requirements: list[Any] | None = None,
    applicable_standards: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Generate the ECSS-E-TM-10-25A-style JSON export.

    Args:
        study_id:    The Study id (used in the engineering model IID).
        study_name:  Human-friendly name.
        phase:       ECSS phase (phase_0 / phase_a / phase_b1 / ...).
        parameters:  Dict of {param_id: ParameterValue-like} from DesignState.
        requirements: Optional list of Requirement-like objects (may be dicts
            or Pydantic models).
        applicable_standards: ECSS standard IDs the study is designed against.
        notes:       Free-text study notes.

    Returns:
        A dict ready to be json.dumps'd and handed to a SysML importer.
    """
    params_list = _normalise_parameters(parameters or {})
    reqs_list = _normalise_requirements(requirements or [])
    blocks = _build_blocks(params_list)
    trace = _build_trace_links(params_list, reqs_list)

    # Wire satisfies onto parameter entries too for convenience
    sat_map: dict[str, list[str]] = {}
    for link in trace:
        if link["kind"] == "satisfies":
            req_id = link["source"].split("/", 1)[1]
            param_id = link["target"].split("/", 1)[1]
            sat_map.setdefault(param_id, []).append(req_id)
    for p in params_list:
        p["satisfies"] = sat_map.get(p["id"], [])

    return {
        "schema": SCHEMA_VERSION,
        "ecss_profile": ECSS_PROFILE,
        "generated": datetime.now(timezone.utc).isoformat(),
        "site_directory": {
            "name": "SpaceCDF",
            "version": "0.1.0",
        },
        "engineering_model": {
            "id": study_id,
            "name": study_name,
            "phase": phase,
            "iid": f"urn:spacecdf:study:{study_id}",
            "reference_data_library": {
                "units": _extract_unit_library(params_list),
                "categories": sorted({p["domain"] for p in params_list if p["domain"]}),
            },
            "blocks": blocks,
            "parameters": params_list,
            "requirements": reqs_list,
            "applicable_standards": sorted(applicable_standards or []),
            "trace_links": trace,
            "notes": notes,
            "counts": {
                "parameters": len(params_list),
                "requirements": len(reqs_list),
                "blocks": len(blocks),
                "trace_links": len(trace),
            },
        },
    }
