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
        return [
            "orbit.delta_v_total_ms", "mass.dry_mass_estimate_kg",
            "propulsion.thruster.equipment_id",
            "propulsion.tank.equipment_id",
        ]

    def _resolve_from_kb(self, state: DesignState, category: str, param_path: str) -> dict | None:
        """Look up a KB component by equipment_id (SPINE_SPEC §8)."""
        eq_id = state.get(param_path)
        if eq_id and hasattr(state, 'kb') and state.kb is not None:
            component = state.kb.get_component(category, eq_id)
            if component:
                return component.__dict__
        return None

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

        # Check if mission actually needs propulsion
        # For CubeSats at low altitude, natural decay handles deorbit
        sc_class = state.get_requirement("spacecraft_class", "nano")
        alt = state.get("orbit.altitude_km", 500) or 500
        has_explicit_propulsion = state.get_requirement("has_propulsion", False)
        propulsion_type = state.get_requirement("propulsion_type", "none")

        # Skip propulsion if: nano/micro class, low LEO, no explicit propulsion requirement
        needs_propulsion = has_explicit_propulsion or propulsion_type not in ("none", None, "")
        if not needs_propulsion and sc_class in ("nano", "micro") and alt < 700:
            dv = 0  # Natural decay sufficient, no propulsion mass

        if dv < 1.0:
            result.add_param("propulsion.total_mass_kg", "Propulsion System Mass", 0.0, "kg")
            result.add_param("propulsion.propellant_mass_kg", "Propellant Mass", 0.0, "kg")
            result.add_param("propulsion.type", "Propulsion Type", "none", "")
            result.add_param("propulsion.isp_s", "Specific Impulse", 0.0, "s")
            result.add_param("propulsion.cost_keur", "Propulsion Cost", 0.0, "kEUR")
            result.add_param("propulsion.delta_v_total_ms", "Total Delta-V", 0.0, "m/s")
            result.add_param("propulsion.total_impulse_ns", "Total Impulse", 0.0, "Ns")
            result.log("No delta-V required — propulsion system not needed")
            result.confidence = 0.95
            return result

        prop = compute_propulsion_budget(
            delta_v_ms=dv,
            dry_mass_kg=dry_mass,
            available_power_w=available_power,
        )

        # --- KB override: thruster datasheet values (SPINE_SPEC §8) ---
        kb_thruster = self._resolve_from_kb(state, "thrusters", "propulsion.thruster.equipment_id")
        if kb_thruster:
            prop.isp_s = kb_thruster.get("isp_sec", prop.isp_s)
            thruster_mass = kb_thruster.get("mass_kg", 0)
            thruster_cost = kb_thruster.get("cost_keur", 0)
            if thruster_mass:
                prop.total_propulsion_mass_kg = thruster_mass + prop.propellant_mass_kg
            if thruster_cost:
                prop.propulsion_cost_keur = thruster_cost
            # Recompute propellant mass with KB Isp (Tsiolkovsky)
            import math
            if prop.isp_s > 0:
                g0 = 9.80665
                mass_ratio = math.exp(dv / (prop.isp_s * g0))
                prop.propellant_mass_kg = dry_mass * (mass_ratio - 1)
                prop.total_propulsion_mass_kg = (thruster_mass or (prop.total_propulsion_mass_kg - prop.propellant_mass_kg)) + prop.propellant_mass_kg
            result.log(f"KB thruster: Isp={prop.isp_s:.0f} s, mass={thruster_mass:.2f} kg")

        # --- KB override: tank datasheet values (SPINE_SPEC §8) ---
        kb_tank = self._resolve_from_kb(state, "tanks", "propulsion.tank.equipment_id")
        if kb_tank:
            tank_mass = kb_tank.get("mass_empty_kg", 0)
            tank_cost = kb_tank.get("cost_keur", 0)
            if tank_mass:
                prop.total_propulsion_mass_kg += tank_mass
            if tank_cost:
                prop.propulsion_cost_keur += tank_cost
            result.log(f"KB tank: empty_mass={tank_mass:.2f} kg, capacity={kb_tank.get('capacity_liters', 0):.1f} L")

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
