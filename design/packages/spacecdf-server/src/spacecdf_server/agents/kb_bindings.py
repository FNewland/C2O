"""KB-aware agent bindings registry — SPINE_SPEC §8.

Single source of truth for which agents consult the KB for which
equipment types. Replaces the scattered SELECTION_EFFECTS map.

Maps: agent_name -> [(category, param_path, *attr_names), ...]

When an engineer selects a component via EquipmentBrowser, the relevant
agent uses datasheet values from KB instead of heritage scaling.
"""
from __future__ import annotations

KB_BINDINGS: dict[str, list[tuple[str, str, ...]]] = {
    "power": [
        ("batteries", "power.battery.equipment_id", "nominal_voltage_v", "mass_kg", "cost_keur"),
        ("solar_cells", "power.solar_array.cell_equipment_id", "efficiency_pct", "mass_kg_per_m2", "cost_keur_per_m2"),
    ],
    "link": [
        ("transponders", "link.transponder.equipment_id", "power_tx_w", "mass_kg", "cost_keur"),
        ("antennas", "link.antenna.equipment_id", "gain_dbi", "mass_kg", "cost_keur"),
    ],
    "aocs": [
        ("reaction_wheels", "aocs.reaction_wheel.equipment_id", "momentum_nms", "mass_kg", "cost_keur"),
        ("star_trackers", "aocs.star_tracker.equipment_id", "fov_deg", "mass_kg", "cost_keur"),
        ("magnetorquers", "aocs.magnetorquer.equipment_id", "dipole_am2", "mass_kg", "cost_keur"),
    ],
    "propulsion": [
        ("thrusters", "propulsion.thruster.equipment_id", "thrust_n", "isp_sec", "mass_kg", "cost_keur"),
        ("tanks", "propulsion.tank.equipment_id", "capacity_liters", "mass_empty_kg", "cost_keur"),
    ],
    "data": [
        ("storage", "data.storage.equipment_id", "capacity_gb", "mass_kg", "cost_keur"),
    ],
    "thermal": [
        ("heaters", "thermal.heater.equipment_id", "power_w", "mass_kg", "cost_keur"),
    ],
}


def get_bindings(agent_name: str) -> list[tuple[str, str, ...]]:
    """Return [(category, param_path, *attr_names), ...] for agent."""
    return KB_BINDINGS.get(agent_name, [])


def get_param_path(agent_name: str, category: str) -> str | None:
    """Return the equipment_id param path for (agent, category)."""
    for entry in get_bindings(agent_name):
        if entry[0] == category:
            return entry[1]
    return None


def get_all_categories() -> dict[str, str]:
    """Return {category: agent_name} for all bindings."""
    result = {}
    for agent_name, entries in KB_BINDINGS.items():
        for entry in entries:
            result[entry[0]] = agent_name
    return result
