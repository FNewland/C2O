"""SpaceCDF — Thermal Design Agent (Tier 1).

Computes thermal balance, radiator sizing, and heater power requirements.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.thermal import compute_thermal_balance, spacecraft_surface_area


class ThermalAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "thermal"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return [
            "orbit.eclipse_fraction",
            "mass.dry_mass_estimate_kg",
            "power.total_sunlight_w",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "thermal.radiator_area_m2", "thermal.radiator_mass_kg",
            "thermal.heater_power_w", "thermal.tcs_mass_kg", "thermal.tcs_cost_keur",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit", "power"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        eclipse_frac = state.get("orbit.eclipse_fraction", 0.35)
        internal_power = state.get("power.total_sunlight_w", 50.0) or 50.0
        dry_mass = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0

        sc_class = state.get_requirement("spacecraft_class", "small")
        form = "cubesat" if sc_class in ("nano", "micro") else "box"
        sc_area = spacecraft_surface_area(dry_mass, form)

        tb = compute_thermal_balance(
            internal_power_w=internal_power,
            spacecraft_area_m2=sc_area,
            eclipse_fraction=eclipse_frac,
        )

        # Class-aware TCS mass override. The physics function's baseline +0.5kg
        # for heaters/thermistors + full-MLI wrap is reasonable for 100+ kg sats
        # but 5-10× heavy for CubeSats where thermal control is mostly passive:
        # small MLI patches (50-100g) + heaters/thermistors (50-100g), no dedicated
        # radiator. References: ISISpace CubeSat thermal guide; GomSpace product docs.
        tcs_mass = tb.tcs_mass_kg
        radiator_mass = tb.radiator_mass_kg
        if sc_class == "nano":
            radiator_mass = 0.0          # Bus structure radiates
            tcs_mass = max(0.15, 0.05 * dry_mass)  # 5% of dry mass, min 150g
        elif sc_class == "micro":
            tcs_mass = max(0.5, 0.04 * dry_mass)

        result.add_param("thermal.radiator_area_m2", "Radiator Area", round(tb.radiator_area_m2, 3), "m²")
        result.add_param("thermal.radiator_mass_kg", "Radiator Mass", round(radiator_mass, 2), "kg")
        result.add_param("thermal.heater_power_w", "Eclipse Heater Power", round(tb.tcs_heater_power_w, 1), "W")
        result.add_param("thermal.tcs_mass_kg", "TCS Total Mass", round(tcs_mass, 2), "kg", margin_percent=20)
        result.add_param("thermal.tcs_cost_keur", "TCS Cost", round(tcs_mass * 15, 0), "kEUR")

        result.warnings.extend(tb.warnings)
        result.confidence = 0.75  # Thermal is approximate at this stage
        return result
