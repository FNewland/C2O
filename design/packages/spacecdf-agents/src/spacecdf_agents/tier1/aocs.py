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
        ]

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

        # For deep space / interplanetary: disturbance torques are minimal
        # (no atmosphere, no magnetic field, gravity gradient negligible)
        # Use a simplified AOCS model: just actuators for pointing
        if orbit_type in ("interplanetary",) or alt == 0:
            # Deep space CubeSat AOCS: reference MarCO (BCT XACT, 2.19 kg for 14 kg SC)
            # Fraction: ~15% for fine pointing, ~5% for coarse
            if pointing_req <= 0.5:
                aocs_mass_estimate = max(0.8, sc_mass * 0.15)  # Fine: RW + ST
            else:
                aocs_mass_estimate = max(0.3, sc_mass * 0.05)  # Coarse: just sun sensors

            from spacecdf_common.physics.aocs import AOCSDesignResult
            aocs = AOCSDesignResult()
            aocs.aocs_mass_kg = aocs_mass_estimate
            aocs.aocs_power_w = aocs_mass_estimate * 3  # ~3 W/kg for AOCS
            aocs.aocs_cost_keur = aocs_mass_estimate * 30
            aocs.pointing_accuracy_deg = pointing_req
            result.log(f"Deep-space AOCS: simplified model, {aocs_mass_estimate:.1f} kg")
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

        dry_est = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        aocs_mass = calibrate_mass("aocs", aocs.aocs_mass_kg, dry_est, sc_class)
        result.add_param("aocs.mass_kg", "AOCS Mass", round(aocs_mass, 2), "kg", margin_percent=20)
        result.add_param("aocs.power_w", "AOCS Power", round(aocs.aocs_power_w, 1), "W")
        result.add_param("aocs.cost_keur", "AOCS Cost", round(aocs.aocs_cost_keur, 0), "kEUR")
        result.add_param("aocs.wheel_momentum_nms", "Wheel Momentum", round(aocs.reaction_wheel_momentum_nms, 3), "Nms")
        result.add_param("aocs.pointing_accuracy_deg", "Pointing Accuracy", aocs.pointing_accuracy_deg, "deg")

        result.warnings.extend(aocs.warnings)
        result.confidence = 0.80
        return result
