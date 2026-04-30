"""SpaceCDF — Power Design Agent (Tier 1).

Computes power budget, solar array sizing, and battery sizing.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.heritage_mass import calibrate_mass
from spacecdf_common.physics.power import compute_power_budget


class PowerAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "power"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return [
            "orbit.eclipse_fraction", "orbit.sunlight_fraction", "orbit.period_s",
            "payload.0.power_w", "payload.0.duty_cycle",
            "thermal.heater_power_w",
            "mission.duration_years",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "power.sa_area_m2", "power.sa_power_bol_w", "power.sa_power_eol_w",
            "power.sa_mass_kg", "power.battery_capacity_wh", "power.battery_mass_kg",
            "power.total_sunlight_w", "power.total_eclipse_w",
            "power.eps_mass_kg", "power.eps_cost_keur",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit"]  # Needs eclipse fraction from orbit agent

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        eclipse_frac = state.get("orbit.eclipse_fraction", 0.35)
        sunlight_frac = state.get("orbit.sunlight_fraction", 0.65)
        period_s = state.get("orbit.period_s", 5700.0)
        mission_years = state.get("mission.duration_years", 3.0)

        # --- ConOps-driven power budget (if modes are defined) ---
        conops = state.conops
        has_modes = conops and hasattr(conops, 'modes') and len(conops.modes) > 0

        if has_modes:
            # Use ConOps modes for physically-driven sizing
            worst_sun = conops.worst_case_power_mode
            worst_eclipse = conops.worst_case_eclipse_mode

            # Sunlight demand = worst-case sunlight mode power
            payload_power = worst_sun.payload_power_w if worst_sun else 0
            platform_power_sun = worst_sun.platform_power_w if worst_sun else 30
            heater_power = worst_eclipse.heater_power_w if worst_eclipse else 10

            # Platform power from mode definition (more accurate than summing agent outputs)
            platform_power = platform_power_sun
            payload_duty = worst_sun.duty_cycle_percent / 100 if worst_sun else 0.25

            result.log(f"ConOps-driven: worst sunlight mode = {worst_sun.name if worst_sun else '?'} ({worst_sun.power_w if worst_sun else 0}W)")
            result.log(f"ConOps-driven: worst eclipse mode = {worst_eclipse.name if worst_eclipse else '?'} ({worst_eclipse.power_w if worst_eclipse else 0}W)")
        else:
            # Fallback: estimate from payload specs + subsystem agents (original logic)
            payload_power = 0.0
            payload_duty = 0.25
            i = 0
            while True:
                pp = state.get(f"payload.{i}.power_w")
                if pp is None:
                    break
                payload_power += pp
                pd = state.get(f"payload.{i}.duty_cycle", 0.25)
                payload_duty = max(payload_duty, pd)
                i += 1

            heater_power = state.get("thermal.heater_power_w", 10.0) or 10.0
            aocs_power = state.get("aocs.power_w", 15.0) or 15.0
            ttc_power = state.get("link.ttc_power_w", 20.0) or 20.0
            obdh_power = 10.0
            platform_power = aocs_power + ttc_power + obdh_power

        # Determine cell efficiency by spacecraft class
        sc_class = state.get_requirement("spacecraft_class", "small")
        if sc_class in ("nano", "micro"):
            cell_eff = 0.295  # Triple-junction GaAs
            sa_specific = 80.0  # Body-mounted
        elif sc_class in ("small",):
            cell_eff = 0.30
            sa_specific = 100.0  # Deployable
        else:
            cell_eff = 0.32
            sa_specific = 130.0  # High-efficiency deployable

        pb = compute_power_budget(
            eclipse_fraction=eclipse_frac,
            sunlight_fraction=sunlight_frac,
            orbit_period_s=period_s,
            mission_duration_years=mission_years,
            platform_power_w=platform_power,
            payload_power_w=payload_power,
            payload_duty_cycle=payload_duty,
            heater_power_eclipse_w=heater_power,
            cell_efficiency=cell_eff,
            sa_specific_power_w_kg=sa_specific,
        )

        result.add_param("power.sa_area_m2", "Solar Array Area", round(pb.sa_area_m2, 3), "m²")
        result.add_param("power.sa_power_bol_w", "SA Power BOL", round(pb.sa_power_bol_w, 1), "W")
        result.add_param("power.sa_power_eol_w", "SA Power EOL", round(pb.sa_power_eol_w, 1), "W")
        result.add_param("power.sa_mass_kg", "Solar Array Mass", round(pb.sa_mass_kg, 2), "kg")
        result.add_param("power.battery_capacity_wh", "Battery Capacity", round(pb.battery_capacity_wh, 1), "Wh")
        result.add_param("power.battery_mass_kg", "Battery Mass", round(pb.battery_mass_kg, 2), "kg")
        result.add_param("power.total_sunlight_w", "Total Power (Sunlight)", round(pb.total_power_sunlight_w, 1), "W")
        result.add_param("power.total_eclipse_w", "Total Power (Eclipse)", round(pb.total_power_eclipse_w, 1), "W")
        dry_est = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        eps_mass = calibrate_mass("eps", pb.eps_mass_kg, dry_est, sc_class)
        result.add_param("power.eps_mass_kg", "EPS Total Mass", round(eps_mass, 2), "kg", margin_percent=20)
        result.add_param("power.eps_cost_keur", "EPS Cost", round(pb.eps_cost_keur, 0), "kEUR")

        result.warnings.extend(pb.warnings)
        result.confidence = 0.85
        return result
