"""SpaceCDF — Equipment Selection Service.

Matches KB components to design needs, ranks by compatibility,
and applies selections with property cascade into the design state.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.parameter import ParameterSource, ParameterValue

logger = logging.getLogger(__name__)

# Map SpaceCDF domains to KB component categories
DOMAIN_TO_CATEGORIES = {
    "power": ["batteries", "solar_cells", "solar_panels", "eps_boards"],
    "aocs": ["reaction_wheels", "star_trackers", "sun_sensors", "magnetorquers"],
    "link": ["transponders", "antennas", "gps_receivers"],
    "propulsion": ["thrusters"],
    "structure": ["cubesat_structures", "deployers", "mechanical_hardware"],
    "data": ["obcs"],
    "thermal": ["thermal_hardware"],
    "integration": ["harnesses"],
    # Ground segment equipment
    "ground_rf": ["ground_antennas", "ground_rf", "ground_baseband"],
    "ground_ops": ["ground_software", "ground_timing"],
}

# Map SpaceCDF domains to the key sizing parameter and unit
DOMAIN_SIZING_PARAMS = {
    "power": [
        ("batteries", "power.battery_capacity_wh", "performance.capacity_wh", "Wh"),
        ("solar_cells", "power.sa_power_eol_w", "performance.efficiency", None),
        ("solar_panels", "power.sa_power_eol_w", "performance.power_w", "W"),
        ("eps_boards", "power.eps_mass_kg", "mass_kg", "kg"),
    ],
    "aocs": [
        ("reaction_wheels", "aocs.wheel_momentum_nms", "performance.momentum_nms", "Nms"),
        ("star_trackers", "aocs.pointing_accuracy_deg", "performance.accuracy_arcsec", "arcsec"),
        ("sun_sensors", "aocs.mass_kg", "mass_kg", "kg"),
        ("magnetorquers", "aocs.mass_kg", "performance.dipole_am2", "Am2"),
    ],
    "link": [
        ("transponders", "link.downlink_rate_bps", "performance.max_data_rate_bps", "bps"),
        ("antennas", "link.ttc_mass_kg", "mass_kg", "kg"),
        ("gps_receivers", "aocs.mass_kg", "mass_kg", "kg"),
    ],
    "propulsion": [
        ("thrusters", "propulsion.isp_s", "performance.isp_s", "s"),
    ],
    "structure": [
        ("cubesat_structures", "structure.mass_kg", "mass_kg", "kg"),
        ("deployers", "structure.mass_kg", "mass_kg", "kg"),
    ],
    "data": [
        ("obcs", "data.obc_mass_kg", "mass_kg", "kg"),
    ],
}


@dataclass
class ComponentMatch:
    """A KB component matched against design requirements."""
    component: dict[str, Any]
    fit_score: float = 0.0  # 0-1, higher is better
    notes: list[str] = field(default_factory=list)
    category: str = ""


def search_compatible_equipment(
    domain: str,
    state: DesignState,
    kb_components: dict[str, list[dict]],
) -> dict[str, list[ComponentMatch]]:
    """Search KB for components compatible with current design needs.

    Returns {category: [ComponentMatch, ...]} ranked by fit_score.
    """
    categories = DOMAIN_TO_CATEGORIES.get(domain, [])
    results: dict[str, list[ComponentMatch]] = {}

    for category in categories:
        components = kb_components.get(category, [])
        matches = []

        for comp in components:
            match = _score_component(comp, domain, category, state)
            if match.fit_score > 0.01:  # Low threshold to show all components
                matches.append(match)

        matches.sort(key=lambda m: m.fit_score, reverse=True)
        results[category] = matches

    return results


def _score_component(
    comp: dict, domain: str, category: str, state: DesignState
) -> ComponentMatch:
    """Score a single component against design requirements."""
    match = ComponentMatch(component=comp, category=category)
    scores: list[float] = []

    # Basic scoring: does the component exist and have data
    mass = comp.get("mass_kg", 0)
    trl = comp.get("trl", 5)

    # TRL score — higher TRL is better for baseline, but we also value innovation
    trl_score = min(trl / 9.0, 1.0)
    scores.append(trl_score * 0.3)

    # Mass score — lighter is better (normalise against design estimate)
    domain_mass = state.get(f"{domain}.mass_kg") or state.get(f"power.eps_mass_kg") or 5.0
    if isinstance(domain_mass, (int, float)) and domain_mass > 0:
        mass_ratio = mass / domain_mass
        mass_score = max(0, 1.0 - abs(mass_ratio - 0.5))  # Best when component is ~50% of subsystem
        scores.append(mass_score * 0.2)

    # Performance match — category-specific
    sizing_params = DOMAIN_SIZING_PARAMS.get(domain, [])
    for cat, design_param, comp_param, unit in sizing_params:
        if cat != category:
            continue
        design_value = state.get(design_param)
        if design_value is None or not isinstance(design_value, (int, float)):
            continue

        # Navigate nested component performance dict
        comp_value = comp
        for key in comp_param.split("."):
            if isinstance(comp_value, dict):
                comp_value = comp_value.get(key)
            else:
                comp_value = None
                break

        if comp_value is not None and isinstance(comp_value, (int, float)) and design_value > 0:
            ratio = comp_value / design_value
            if ratio >= 1.0:
                perf_score = min(1.0, 1.0 / ratio)  # Exact match = 1.0, over-spec penalised slightly
                match.notes.append(f"Performance: {comp_value} {unit or ''} meets requirement of {design_value:.1f}")
            else:
                perf_score = ratio * 0.5  # Under-spec penalised heavily
                match.notes.append(f"Performance: {comp_value} {unit or ''} BELOW requirement of {design_value:.1f}")
            scores.append(perf_score * 0.5)

    # Heritage bonus
    heritage = comp.get("heritage_missions", [])
    if heritage:
        scores.append(0.1)
        match.notes.append(f"Heritage: {', '.join(heritage[:3])}")

    match.fit_score = sum(scores) / max(len(scores), 1)
    return match


def apply_equipment_selection(
    component: dict[str, Any],
    domain: str,
    category: str,
    state: DesignState,
    position_id: str,
    role: str = "primary",
    quantity: int = 1,
) -> set[str]:
    """Apply a component selection to the design state.

    Sets the relevant parameters with source=KB_COMPONENT so they
    persist through re-convergence (sticky parameters).

    Returns the set of changed parameter IDs.
    """
    changed = set()
    comp_id = component.get("id", "unknown")
    comp_name = component.get("name", "Unknown")
    mass = component.get("mass_kg", 0) * quantity
    power = component.get("power_w", 0) * quantity
    cost = component.get("cost_keur") or 0
    trl = component.get("trl", 5)

    # Map category to parameter prefix
    param_prefix = f"{domain}"

    # Set mass parameter
    mass_param_id = f"{param_prefix}.{category}_mass_kg"
    state._parameters[mass_param_id] = ParameterValue(
        id=mass_param_id,
        name=f"{comp_name} Mass",
        value=mass,
        unit="kg",
        domain=domain,
        source=ParameterSource.KB_COMPONENT,
        confidence=0.95,
        margin_percent=5.0,  # Known component, lower margin
        trl=trl,
        heritage=", ".join(component.get("heritage_missions", [])[:2]),
        equipment_id=comp_id,
        equipment_name=comp_name,
        override_by=position_id,
        updated_by=f"position:{position_id}",
        rationale=f"Selected {comp_name} from {component.get('manufacturer', 'unknown')}",
    )
    changed.add(mass_param_id)

    # Also update the domain-level mass if this is the primary mass driver
    domain_mass_id = f"{domain}.mass_kg" if domain != "power" else "power.eps_mass_kg"
    existing = state.get_param(domain_mass_id)
    if existing and not existing.source.is_sticky:
        # Don't override if another selection already set this
        pass

    logger.info(
        "Equipment selected: %s (%s) for %s by %s — mass=%.2f kg, TRL=%d",
        comp_name, comp_id, domain, position_id, mass, trl,
    )

    return changed
