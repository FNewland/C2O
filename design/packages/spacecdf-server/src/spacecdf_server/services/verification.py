"""SpaceCDF — Requirement Verification Service.

Auto-generates requirements from mission definition, evaluates against
design state, and performs worst-case analysis with EOL degradation.
"""
from __future__ import annotations

from typing import Any

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.requirements import (
    ComplianceMatrix,
    ComplianceStatus,
    Requirement,
    RequirementVerification,
    generate_requirements,
    verify_requirements,
)


# Worst-case degradation multipliers
WORST_CASE_EOL = {
    "power.sa_power_eol_w": lambda v, years: v * (1 - 0.025) ** years,  # 2.5%/yr degradation
    "power.battery_capacity_wh": lambda v, years: v * 0.80,  # 20% capacity loss at EOL
    "aocs.pointing_accuracy_deg": lambda v, years: v * 1.20,  # 20% degradation
    "link.downlink_margin_db": lambda v, years: v - 1.0,  # 1 dB rain/atmosphere margin
}

WORST_CASE_HOT = {
    "power.sa_power_eol_w": lambda v: v * 0.92,  # Hot case solar efficiency loss
    "thermal.tcs_mass_kg": lambda v: v * 1.15,    # Need more thermal hardware
}

WORST_CASE_COLD = {
    "power.battery_capacity_wh": lambda v: v * 0.85,  # Cold battery derating
    "thermal.heater_power_w": lambda v: v * 1.5,       # More heater power needed
}


def build_compliance_matrix(
    state: DesignState,
    worst_case: str = "nominal",
) -> ComplianceMatrix:
    """Build a full compliance matrix from the design state.

    Args:
        state: Current design state with parameters
        worst_case: "nominal", "eol", "hot", or "cold"
    """
    # Auto-generate requirements from mission definition
    requirements = generate_requirements(state.requirements)

    # Get parameter values (apply worst-case if requested)
    params = dict(state.parameters)
    mission_years = state.get("mission.duration_years", 3.0) or 3.0

    if worst_case == "eol":
        params = _apply_degradation(params, WORST_CASE_EOL, mission_years)
    elif worst_case == "hot":
        params = _apply_degradation(params, WORST_CASE_HOT)
    elif worst_case == "cold":
        params = _apply_degradation(params, WORST_CASE_COLD)

    # Verify
    verifications = verify_requirements(requirements, params)

    return ComplianceMatrix(
        requirements=requirements,
        verifications=verifications,
    )


def _apply_degradation(
    params: dict[str, Any],
    degradation_map: dict,
    years: float = 3.0,
) -> dict[str, Any]:
    """Apply worst-case degradation factors to parameter values."""
    result = dict(params)
    for param_id, func in degradation_map.items():
        p = result.get(param_id)
        if p is None:
            continue
        val = p.value if hasattr(p, "value") else (p.get("value") if isinstance(p, dict) else p)
        if not isinstance(val, (int, float)):
            continue

        # Apply degradation function
        import inspect
        sig = inspect.signature(func)
        if len(sig.parameters) == 2:
            new_val = func(val, years)
        else:
            new_val = func(val)

        # Create modified parameter copy
        if hasattr(p, "model_copy"):
            new_p = p.model_copy(update={"value": new_val})
        elif isinstance(p, dict):
            new_p = {**p, "value": new_val}
        else:
            continue
        result[param_id] = new_p

    return result
