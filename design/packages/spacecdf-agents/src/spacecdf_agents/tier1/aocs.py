"""SpaceCDF — AOCS Design Agent (Tier 1).

Computes attitude control system sizing based on pointing requirements
and disturbance environment.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.aocs import compute_aocs_design
from spacecdf_common.physics.heritage_mass import calibrate_mass


class AOCSAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "aocs"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return [
            "orbit.altitude_km", "orbit.period_s",
            "payload.0.pointing_deg",
            "mass.dry_mass_estimate_kg",
            "aocs.reaction_wheel.equipment_id",
            "aocs.star_tracker.equipment_id",
            "aocs.magnetorquer.equipment_id",
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
        return ["aocs.mass_kg", "aocs.power_w", "aocs.cost_keur"]

    def dependencies(self) -> list[str]:
        return ["orbit"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        alt = state.get("orbit.altitude_km", 500.0)
        period = state.get("orbit.period_s", 5700.0)
        sc_mass = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0

        # ConOps-driven: use tightest pointing mode if available
        conops = state.conops
        if conops and hasattr(conops, 'tightest_pointing_mode') and conops.tightest_pointing_mode:
            pointing_req = conops.tightest_pointing_mode.pointing_requirement_deg
            result.log(f"AOCS: using ConOps tightest pointing mode ({conops.tightest_pointing_mode.name}, {pointing_req} deg)")
        else:
            pointing_req = state.get("payload.0.pointing_deg", 0.1) or 0.1

        sc_class = state.get_requirement("spacecraft_class", "small")
        max_dim = {"nano": 0.3, "micro": 0.5, "small": 1.0, "medium": 2.0, "large": 3.0, "flagship": 5.0}
        dim = max_dim.get(sc_class, 1.0)

        # Determine central body for disturbance torques
        orbit_type = state.get_requirement("orbit.orbit_type")
        body = "earth"
        if orbit_type in ("lunar",):
            body = "moon"
        elif orbit_type in ("mars",):
            body = "mars"
        elif orbit_type in ("interplanetary",):
            body = "sun"  # Deep space: solar radiation pressure dominant, no gravity gradient

        # For deep space / interplanetary: use reference altitude for torque calc
        # SRP is dominant; gravity gradient and aero are negligible (correct)
        if orbit_type in ("interplanetary",) or alt == 0:
            effective_alt = 149597870.7  # 1 AU in km for heliocentric
            if orbit_type == "lunar":
                effective_alt = 100  # 100 km lunar orbit as reference
            result.log(f"Deep-space AOCS: using {body} body, alt={effective_alt:.0f} km for torques")
            aocs = compute_aocs_design(
                altitude_km=effective_alt,
                spacecraft_mass_kg=sc_mass,
                spacecraft_area_m2=dim * dim,
                max_dimension_m=dim,
                required_pointing_deg=pointing_req,
                orbit_period_s=period if period > 0 else 86400,
                body=body,
            )
        else:
            aocs = compute_aocs_design(
                altitude_km=alt,
                spacecraft_mass_kg=sc_mass,
                spacecraft_area_m2=dim * dim,
                max_dimension_m=dim,
                required_pointing_deg=pointing_req,
                orbit_period_s=period,
                body=body,
            )

        # --- KB override: AOCS component datasheet values (SPINE_SPEC §8) ---
        kb_rw = self._resolve_from_kb(state, "reaction_wheels", "aocs.reaction_wheel.equipment_id")
        kb_st = self._resolve_from_kb(state, "star_trackers", "aocs.star_tracker.equipment_id")
        kb_mtq = self._resolve_from_kb(state, "magnetorquers", "aocs.magnetorquer.equipment_id")
        kb_mass_total = 0.0
        kb_cost_total = 0.0
        kb_any = False
        if kb_rw:
            kb_any = True
            kb_mass_total += kb_rw.get("mass_kg", 0)
            kb_cost_total += kb_rw.get("cost_keur", 0)
            aocs.reaction_wheel_momentum_nms = kb_rw.get("momentum_nms", aocs.reaction_wheel_momentum_nms)
            result.log(f"KB reaction wheel: mass={kb_rw.get('mass_kg', 0):.2f} kg, momentum={aocs.reaction_wheel_momentum_nms:.3f} Nms")
        if kb_st:
            kb_any = True
            kb_mass_total += kb_st.get("mass_kg", 0)
            kb_cost_total += kb_st.get("cost_keur", 0)
            result.log(f"KB star tracker: mass={kb_st.get('mass_kg', 0):.2f} kg")
        if kb_mtq:
            kb_any = True
            kb_mass_total += kb_mtq.get("mass_kg", 0)
            kb_cost_total += kb_mtq.get("cost_keur", 0)
            result.log(f"KB magnetorquer: mass={kb_mtq.get('mass_kg', 0):.2f} kg, dipole={kb_mtq.get('dipole_am2', 0):.2f} Am²")
        if kb_any:
            aocs.aocs_mass_kg = kb_mass_total if kb_mass_total > 0 else aocs.aocs_mass_kg
            aocs.aocs_cost_keur = kb_cost_total if kb_cost_total > 0 else aocs.aocs_cost_keur

        dry_est = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        aocs_mass = calibrate_mass("aocs", aocs.aocs_mass_kg, dry_est, sc_class)
        result.add_param("aocs.mass_kg", "AOCS Mass", round(aocs_mass, 2), "kg", margin_percent=20)
        result.add_param("aocs.power_w", "AOCS Power", round(aocs.aocs_power_w, 1), "W")
        result.add_param("aocs.cost_keur", "AOCS Cost", round(aocs.aocs_cost_keur, 0), "kEUR")
        result.add_param("aocs.wheel_momentum_nms", "Wheel Momentum", round(aocs.reaction_wheel_momentum_nms, 3), "Nms")
        result.add_param("aocs.pointing_accuracy_deg", "Pointing Accuracy", aocs.pointing_accuracy_deg, "deg")
        result.add_param("aocs.torque_gravity_gradient_nm", "Gravity Gradient Torque", round(aocs.gravity_gradient_torque_nm, 6), "Nm")
        result.add_param("aocs.torque_solar_pressure_nm", "Solar Pressure Torque", round(aocs.solar_pressure_torque_nm, 6), "Nm")
        result.add_param("aocs.torque_aerodynamic_nm", "Aerodynamic Torque", round(aocs.aerodynamic_torque_nm, 6), "Nm")
        result.add_param("aocs.torque_magnetic_nm", "Magnetic Torque", round(aocs.magnetic_torque_nm, 6), "Nm")
        result.add_param("aocs.torque_total_nm", "Total Disturbance Torque", round(aocs.total_disturbance_torque_nm, 6), "Nm")

        result.warnings.extend(aocs.warnings)
        result.confidence = 0.80
        return result
