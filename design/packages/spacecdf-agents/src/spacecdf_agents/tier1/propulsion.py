"""SpaceCDF — Propulsion Design Agent (Tier 1).

Sizes the propulsion system based on the delta-V budget.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.propulsion import compute_propulsion_budget


class PropulsionAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "propulsion"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return ["orbit.delta_v_total_ms", "mass.dry_mass_estimate_kg"]

    def output_parameters(self) -> list[str]:
        return [
            "propulsion.total_mass_kg", "propulsion.propellant_mass_kg",
            "propulsion.type", "propulsion.isp_s", "propulsion.cost_keur",
            "propulsion.delta_v_total_ms", "propulsion.total_impulse_ns",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        dv = state.get("orbit.delta_v_total_ms", 0) or 0
        dry_mass = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        available_power = state.get("power.sa_power_eol_w", 100.0) or 100.0

        prop = compute_propulsion_budget(
            delta_v_ms=dv,
            dry_mass_kg=dry_mass,
            available_power_w=available_power,
        )

        result.add_param("propulsion.total_mass_kg", "Propulsion System Mass",
                         round(prop.total_propulsion_mass_kg, 2), "kg", margin_percent=10)
        result.add_param("propulsion.propellant_mass_kg", "Propellant Mass",
                         round(prop.propellant_mass_kg, 2), "kg", margin_percent=5)
        result.add_param("propulsion.type", "Propulsion Type", prop.propulsion_type, "")
        result.add_param("propulsion.isp_s", "Specific Impulse", prop.isp_s, "s")
        result.add_param("propulsion.cost_keur", "Propulsion Cost",
                         round(prop.propulsion_cost_keur, 0), "kEUR")
        result.add_param("propulsion.delta_v_total_ms", "Total Delta-V",
                         round(prop.total_delta_v_ms, 1), "m/s")
        # Total impulse: propellant_mass * Isp * g0
        total_impulse = prop.propellant_mass_kg * prop.isp_s * 9.80665 if prop.isp_s > 0 else 0.0
        result.add_param("propulsion.total_impulse_ns", "Total Impulse",
                         round(total_impulse, 1), "Ns")

        result.warnings.extend(prop.warnings)
        result.confidence = 0.80
        return result
