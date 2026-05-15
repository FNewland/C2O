"""SpaceCDF — Thermal Design Agent (Tier 1).

Computes thermal balance, radiator sizing, and heater power requirements.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.heritage_mass import calibrate_mass
from spacecdf_common.physics.thermal import compute_thermal_balance, spacecraft_surface_area
from spacecdf_agents.exporters.docs.agent_extras import thermal_node


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
        dry_mass = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0

        # ConOps-driven: use worst-case hot mode power for radiator sizing
        conops = state.conops
        if conops and hasattr(conops, 'worst_case_power_mode') and conops.worst_case_power_mode:
            internal_power = conops.worst_case_power_mode.power_w
            result.log(f"Thermal: using ConOps hot case ({conops.worst_case_power_mode.name}, {internal_power}W)")
        else:
            internal_power = state.get("power.total_sunlight_w", 50.0) or 50.0

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
        if tb.tcs_heater_power_w > 20:
            result.warnings.append(f"Heater power {tb.tcs_heater_power_w:.0f} W exceeds 20 W — consider MLI improvements or passive thermal design")
        tcs_mass = calibrate_mass("tcs", tcs_mass, dry_mass, sc_class)
        result.add_param("thermal.tcs_mass_kg", "TCS Total Mass", round(tcs_mass, 2), "kg", margin_percent=20)
        result.add_param("thermal.tcs_cost_keur", "TCS Cost", round(tcs_mass * 15, 0), "kEUR")

        result.warnings.extend(tb.warnings)

        # ---- Report-quality narrative & structured intermediates ----
        result.rationale = (
            f"Thermal control sized for a hot-case internal dissipation of "
            f"{internal_power:.1f} W on a {sc_area:.2f} m² external surface "
            f"({form}).  The radiator area is {tb.radiator_area_m2:.3f} m² "
            f"(ε=0.85, α=0.15) and rejects to space at T_max=50 °C.  In the "
            f"cold case (eclipse, 30 % standby load) heaters supply "
            f"{tb.tcs_heater_power_w:.1f} W to hold the platform above T_min=-20 °C."
        )
        result.assumptions = [
            "Stefan–Boltzmann steady-state energy balance, no transient analysis.",
            "Solar flux 1361 W/m², Earth IR 237 W/m², albedo 0.30.",
            "Radiator: ε=0.85, α=0.15 (white paint / OSR).",
            "MLI effective emissivity 0.01 (15-layer blanket).",
            "Platform allowable range −20 °C to +50 °C; payload limits set separately.",
        ]
        result.extras["thermal.nodes"] = [
            thermal_node("Spacecraft bus", hot_c=tb.hot_case_temp_c,
                         cold_c=tb.cold_case_temp_c, limit_hot_c=50, limit_cold_c=-20),
            thermal_node("Battery", hot_c=tb.hot_case_temp_c - 5,
                         cold_c=max(2.0, tb.cold_case_temp_c + 10),
                         limit_hot_c=35, limit_cold_c=0),
            thermal_node("Payload optics", hot_c=tb.hot_case_temp_c - 10,
                         cold_c=tb.cold_case_temp_c, limit_hot_c=40, limit_cold_c=-30),
            thermal_node("OBDH/avionics", hot_c=tb.hot_case_temp_c - 3,
                         cold_c=tb.cold_case_temp_c + 5, limit_hot_c=70, limit_cold_c=-40),
        ]
        result.extras["thermal.surfaces"] = [
            {"surface": "Radiator (OSR)", "alpha": 0.15, "epsilon": 0.85,
             "area_m2": round(tb.radiator_area_m2, 3)},
            {"surface": "MLI (15-layer)", "alpha": 0.10, "epsilon": 0.01,
             "area_m2": round(max(0, tb.mli_area_m2), 3)},
        ]
        result.extras["thermal.heater"] = {
            "eclipse_power_w": tb.tcs_heater_power_w,
            "margin_factor": 1.5,
            "control": "Thermostatic, redundant heater string.",
        }

        result.confidence = 0.75  # Thermal is approximate at this stage
        return result
