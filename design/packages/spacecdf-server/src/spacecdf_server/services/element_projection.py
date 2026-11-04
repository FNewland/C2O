"""Element Projection Service — bridges the element tree and flat DesignState.

Forward projection: element tree → flat parameter dict (for agents)
Reverse merge: agent results → update element tree

The mapping registry defines how element properties map to parameter paths.

SCDF-170: ``sum`` aggregates count *leaf* elements only (an element with
live children contributes through its children, never in addition to them),
so a subsystem that carries a rolled-up ``mass_kg`` column (N1) is not
double-counted. ``contributing_elements`` / ``reverse_map`` expose the
registry both ways for ``services.analysis_context`` (which flat paths an
element override touches) and ``services.analysis_results`` (which element
parameter an agent output lands on).
"""
from __future__ import annotations

from typing import Any


# ─── Mapping Registry ───
# Maps flat parameter paths to (element selector, property extraction)
# element selector: how to find the element in the tree
# property: which field to read/write

DOMAIN_SUBSYSTEM_MAP = {
    "power": "eps",
    "aocs": "aocs",
    "link": "ttc",
    "thermal": "thermal",
    "structure": "structure",
    "propulsion": "propulsion",
    "data": "obc",
    "payload": "payload",
}

# Forward projection rules: element tree property → flat parameter path
PROPERTY_TO_PARAM = {
    # Subsystem mass aggregates
    "power.eps_mass_kg": ("power", "mass_kg", "sum"),
    "aocs.mass_kg": ("aocs", "mass_kg", "sum"),
    "link.ttc_mass_kg": ("ttc", "mass_kg", "sum"),
    "thermal.tcs_mass_kg": ("thermal", "mass_kg", "sum"),
    "structure.mass_kg": ("structure", "mass_kg", "sum"),
    "propulsion.total_mass_kg": ("propulsion", "mass_kg", "sum"),
    "data.obdh_mass_kg": ("obc", "mass_kg", "sum"),

    # Subsystem power aggregates
    "aocs.power_w": ("aocs", "power_avg_w", "sum"),
    "link.ttc_power_w": ("ttc", "power_avg_w", "sum"),

    # Subsystem cost aggregates
    "power.eps_cost_keur": ("power", "cost_recurring_keur", "sum"),
    "aocs.cost_keur": ("aocs", "cost_recurring_keur", "sum"),
    "link.ttc_cost_keur": ("ttc", "cost_recurring_keur", "sum"),

    # Component-level performance (first match in domain)
    "power.battery_capacity_wh": ("power", "performance.capacity_wh", "first"),
    "power.battery_mass_kg": ("power", "performance.battery_mass_kg", "first"),
    "aocs.wheel_momentum_nms": ("aocs", "performance.momentum_nms", "first"),
    "aocs.pointing_accuracy_deg": ("aocs", "performance.pointing_accuracy_deg", "first"),
}


def _sum_members(live: list[dict], prop: str, overrides: set[tuple[str, str]] | None) -> list[dict]:
    """Elements that count towards a ``sum`` of ``prop``: leaves, plus any
    element whose ``(id, prop)`` is in ``overrides`` — an overridden roll-up
    replaces its subtree (its descendants are excluded for that property)."""
    by_id = {e["id"]: e for e in live}
    children: dict[str, list[str]] = {}
    for e in live:
        if e.get("parent_id"):
            children.setdefault(e["parent_id"], []).append(e["id"])
    overridden = {eid for eid, p in (overrides or ()) if p == prop and eid in by_id}

    def _under_override(eid: str) -> bool:
        pid = by_id[eid].get("parent_id")
        while pid and pid in by_id:
            if pid in overridden:
                return True
            pid = by_id[pid].get("parent_id")
        return False

    return [e for e in live
            if (e["id"] in overridden or not children.get(e["id"])) and not _under_override(e["id"])]


def project_elements_to_params(elements: list[dict],
                               overrides: set[tuple[str, str]] | None = None) -> dict[str, float]:
    """Convert element tree (flat list) to parameter dict for agents.

    Args:
        elements: list of design element dicts (with subsystem_domain, mass_kg, etc.)
        overrides: ``{(element_id, property)}`` whose value is a user override /
            formula result; such an element replaces its subtree in ``sum``
            aggregates (see ``_sum_members``).

    Returns:
        Flat parameter dict like {"power.eps_mass_kg": 1.3, "aocs.mass_kg": 0.87, ...}
    """
    params: dict[str, float] = {}
    live = [e for e in elements if not e.get("deleted_at")]

    for param_path, (domain, prop, agg_type) in PROPERTY_TO_PARAM.items():
        # Find matching elements; ``sum`` aggregates use leaves only (no double count)
        matching = [e for e in live if e.get("subsystem_domain") == domain]
        if agg_type == "sum":
            member_ids = {e["id"] for e in _sum_members(live, prop, overrides)}
            matching = [e for e in matching if e["id"] in member_ids]

        if not matching:
            continue

        if "." in prop and prop.startswith("performance"):
            # Performance JSON lookup
            perf_key = prop.split(".", 1)[1]
            if agg_type == "first":
                for e in matching:
                    perf = e.get("performance_json") or e.get("performance") or {}
                    if perf_key in perf:
                        params[param_path] = perf[perf_key]
                        break
            elif agg_type == "sum":
                total = 0
                for e in matching:
                    perf = e.get("performance_json") or e.get("performance") or {}
                    val = perf.get(perf_key, 0) or 0
                    total += val * (e.get("quantity", 1))
                if total > 0:
                    params[param_path] = total
        else:
            # Direct property lookup
            if agg_type == "sum":
                total = sum((e.get(prop, 0) or 0) * (e.get("quantity", 1)) for e in matching)
                if total > 0:
                    params[param_path] = total
            elif agg_type == "first":
                for e in matching:
                    val = e.get(prop)
                    if val is not None:
                        params[param_path] = val
                        break

    # Also compute total mass: every physical leaf (components, plus subsystems
    # that carry a mass but no equipment yet) in the space segment.
    mass_member_ids = {e["id"] for e in _sum_members(live, "mass_kg", overrides)}
    all_physical = [
        e for e in live
        if e.get("element_type") in ("component", "subsystem")
        and e["id"] in mass_member_ids
        and (e.get("segment") or "space") == "space"
    ]
    total_mass = sum((e.get("mass_kg", 0) or 0) * (e.get("quantity", 1)) for e in all_physical)
    if total_mass > 0:
        params["mass.dry_mass_kg"] = total_mass

    return params


def contributing_elements(elements: list[dict],
                          overrides: set[tuple[str, str]] | None = None) -> dict[str, list[tuple[str, str]]]:
    """``{param_path: [(element_id, property_name), ...]}`` — which element
    properties feed each registry path under the same rules as
    :func:`project_elements_to_params` (leaves / overridden roll-ups for
    ``sum``; every matching element for ``first`` since any of them may be
    picked). ``performance.<key>`` properties are reported as ``performance.<key>``.
    """
    live = [e for e in elements if not e.get("deleted_at")]
    out: dict[str, list[tuple[str, str]]] = {}
    for param_path, (domain, prop, agg_type) in PROPERTY_TO_PARAM.items():
        matching = [e for e in live if e.get("subsystem_domain") == domain]
        if agg_type == "sum":
            member_ids = {e["id"] for e in _sum_members(live, prop, overrides)}
            matching = [e for e in matching if e["id"] in member_ids]
        if matching:
            out[param_path] = [(e["id"], prop) for e in matching]
    return out


def reverse_map(param_path: str, elements: list[dict]) -> tuple[dict, str] | None:
    """Registry path -> ``(subsystem element, parameter name)`` it writes back to.

    Only paths in ``PROPERTY_TO_PARAM`` resolve; the target is the
    ``subsystem`` element of the path's domain (``performance.<key>`` maps
    to parameter name ``<key>``). ``None`` when the path is unknown or the
    study has no such subsystem.
    """
    entry = PROPERTY_TO_PARAM.get(param_path)
    if entry is None:
        return None
    domain, prop, _ = entry
    for e in elements:
        if (e.get("element_type") == "subsystem" and e.get("subsystem_domain") == domain
                and not e.get("deleted_at")):
            name = prop.split(".", 1)[1] if prop.startswith("performance.") else prop
            return e, name
    return None


def merge_agent_params_to_elements(
    elements: list[dict],
    agent_params: dict[str, Any],
) -> list[str]:
    """Merge agent-computed parameters back into element properties.

    Only updates elements that don't have user-set values (sticky check).
    Returns list of element IDs that were modified.

    Note: This is conservative — only writes aggregates back to subsystem elements,
    not individual components. Components are only modified by explicit user selection.
    """
    modified_ids: list[str] = []

    # Reverse mapping: for each parameter, find the target subsystem element
    for param_path, value in agent_params.items():
        if not isinstance(value, (int, float)):
            continue

        # Parse domain from param path
        parts = param_path.split(".")
        if len(parts) < 2:
            continue
        domain = parts[0]

        # Find the subsystem-level element for this domain
        target_domain = DOMAIN_SUBSYSTEM_MAP.get(domain)
        if not target_domain:
            continue

        # Find the subsystem element (element_type == "subsystem" and matching domain)
        subsystem_el = None
        for e in elements:
            if (e.get("element_type") == "subsystem" and
                e.get("subsystem_domain") == target_domain and
                not e.get("deleted_at")):
                subsystem_el = e
                break

        if not subsystem_el:
            continue

        # Map specific agent params back to element properties
        prop = parts[1] if len(parts) == 2 else ".".join(parts[1:])

        if "mass" in prop and "kg" in prop:
            if subsystem_el.get("mass_kg") is None:  # Don't overwrite user-set values
                subsystem_el["mass_kg"] = value
                modified_ids.append(subsystem_el["id"])
        elif "power" in prop and "_w" in prop:
            if subsystem_el.get("power_avg_w") is None:
                subsystem_el["power_avg_w"] = value
                modified_ids.append(subsystem_el["id"])
        elif "cost" in prop and "keur" in prop:
            if subsystem_el.get("cost_recurring_keur") is None:
                subsystem_el["cost_recurring_keur"] = value
                modified_ids.append(subsystem_el["id"])

    return list(set(modified_ids))


def seed_elements_from_design_result(
    study_id: str,
    result_params: dict[str, Any],
    mission_type: str = "earth_observation",
    spacecraft_class: str = "nano",
) -> list[dict]:
    """Create initial element tree from a design result.

    Called after first `runDesign()` to bootstrap the element tree.
    Creates: mission → segments → systems → subsystems with agent-computed values.
    """
    from uuid import uuid4

    elements = []

    def _el(name, etype, parent_id=None, domain=None, segment="space", **kwargs):
        el_id = uuid4().hex
        el = {
            "id": el_id, "study_id": study_id, "parent_id": parent_id,
            "name": name, "element_type": etype, "subsystem_domain": domain,
            "segment": segment, "description": "", "quantity": 1,
            "margin_percent": 20.0, "version": 1, "deleted_at": None,
            **kwargs,
        }
        elements.append(el)
        return el_id

    # Mission root
    mission_id = _el(f"{mission_type.replace('_', ' ').title()} Mission", "mission")

    # Segments
    space_id = _el("Space Segment", "segment", mission_id, segment="space")
    ground_id = _el("Ground Segment", "segment", mission_id, segment="ground")
    ops_id = _el("Operations", "segment", mission_id, segment="operations")

    # Space segment → the spacecraft (level 2); platform subsystems and the payload are
    # level-3 subsystems of it (ECSS product tree, services/product_tree.py)
    platform_id = _el("Spacecraft", "system", space_id)
    payload_id = _el("Payload", "subsystem", platform_id, domain="payload")

    # Subsystems under platform
    get = lambda k: result_params.get(k, {}).get("value") if isinstance(result_params.get(k), dict) else result_params.get(k)

    subsystems = [
        ("EPS", "power", get("power.eps_mass_kg"), get("power.total_sunlight_w"), 50, 30),
        ("AOCS", "aocs", get("aocs.mass_kg"), get("aocs.power_w"), 230, 30),
        ("TTC", "ttc", get("link.ttc_mass_kg"), get("link.ttc_power_w"), 410, 30),
        ("OBC/Data Handling", "obc", get("data.obdh_mass_kg"), None, 50, 160),
        ("Thermal Control", "thermal", get("thermal.tcs_mass_kg"), get("thermal.heater_power_w"), 230, 160),
        ("Structure", "structure", get("structure.mass_kg"), None, 410, 160),
        ("Propulsion", "propulsion", get("propulsion.total_mass_kg"), None, 590, 160),
    ]

    subsystem_ids = {}
    for name, domain, mass, power, dx, dy in subsystems:
        sid = _el(name, "subsystem", platform_id, domain=domain,
                  mass_kg=mass, power_avg_w=power, diagram_x=dx, diagram_y=dy)
        subsystem_ids[domain] = sid

    # Payload element with position
    _el("Imager/Sensor", "component", payload_id, domain="payload",
        mass_kg=get("payload.mass_kg"), power_avg_w=get("payload.0.power_w"),
        diagram_x=590, diagram_y=30)

    # Standard interfaces between subsystems
    interfaces = []
    def _iface(from_domain, to_domain, itype, label):
        from_id = subsystem_ids.get(from_domain)
        to_id = subsystem_ids.get(to_domain)
        if from_id and to_id:
            iface_id = uuid4().hex
            interfaces.append({
                "id": iface_id, "study_id": study_id,
                "name": label, "interface_type": itype,
                "direction": "bidirectional",
                "from_element_id": from_id, "to_element_id": to_id,
                "properties_json": None, "status": "defined",
                "criticality": "standard", "diagram_label": label,
                "version": 1, "deleted_at": None,
            })

    _iface("power", "obc", "electrical", "Power Bus")
    _iface("power", "aocs", "electrical", "Power")
    _iface("power", "ttc", "electrical", "Power")
    _iface("power", "thermal", "electrical", "Heater Power")
    _iface("obc", "aocs", "data", "ADCS Commands")
    _iface("obc", "ttc", "data", "TM/TC Packets")
    _iface("obc", "payload", "data", "Payload Data")
    _iface("aocs", "payload", "data", "Pointing Info")
    _iface("ttc", "obc", "rf", "Uplink TC")

    # Ground segment
    gs_id = _el("Ground Station Network", "system", ground_id, segment="ground", diagram_x=100, diagram_y=30)
    mcc_id = _el("Mission Control Centre", "system", ground_id, segment="ground", diagram_x=350, diagram_y=30)
    _el("Data Processing", "system", ground_id, segment="ground", diagram_x=350, diagram_y=160)

    # Operations modes
    _el("LEOP", "mode", ops_id, segment="operations")
    _el("Nominal Operations", "mode", ops_id, segment="operations")
    _el("Safe Mode", "mode", ops_id, segment="operations")

    return elements, interfaces
