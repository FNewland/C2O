"""SpaceCDF — Orbit Design Agent (Tier 1).

Computes orbital parameters, eclipse fractions, contact windows,
and delta-V budgets from mission requirements.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.orbit import (
    compute_orbit_params,
    delta_v_deorbit,
    delta_v_station_keeping,
    estimate_contact_time_per_day,
    sso_inclination,
)


class OrbitAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "orbit"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return ["orbit.altitude_km", "orbit.inclination_deg"]

    def output_parameters(self) -> list[str]:
        return [
            "orbit.period_s", "orbit.period_min", "orbit.velocity_ms",
            "orbit.eclipse_fraction", "orbit.sunlight_fraction",
            "orbit.eclipse_duration_min", "orbit.sunlight_duration_min",
            "orbit.orbits_per_day", "orbit.raan_drift_deg_day",
            "orbit.footprint_radius_km", "orbit.contact_time_per_day_s",
            "orbit.delta_v_sk_ms", "orbit.delta_v_deorbit_ms", "orbit.delta_v_total_ms",
        ]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        alt = state.get("orbit.altitude_km", 500.0)
        inc = state.get("orbit.inclination_deg")
        orbit_type = state.get_requirement("orbit.orbit_type")
        mission_years = state.get("mission.duration_years", 3.0)

        # Auto-compute SSO inclination if needed
        if orbit_type == "sso" and (inc is None or inc == 0):
            inc = sso_inclination(alt)
            result.log(f"Computed SSO inclination: {inc:.2f} deg for {alt:.0f} km")
        elif inc is None:
            inc = 97.4  # Default SSO

        # Compute orbital parameters
        params = compute_orbit_params(alt, inc)

        result.add_param("orbit.period_s", "Orbital Period", params.period_s, "s",
                         rationale=f"Kepler period at {alt:.0f} km altitude")
        result.add_param("orbit.period_min", "Orbital Period", params.period_min, "min")
        result.add_param("orbit.velocity_ms", "Orbital Velocity", params.velocity_ms, "m/s")
        result.add_param("orbit.eclipse_fraction", "Eclipse Fraction", params.eclipse_fraction, "",
                         rationale="Cylindrical shadow model")
        result.add_param("orbit.sunlight_fraction", "Sunlight Fraction", params.sunlight_fraction, "")
        result.add_param("orbit.eclipse_duration_min", "Eclipse Duration", params.eclipse_duration_min, "min")
        result.add_param("orbit.sunlight_duration_min", "Sunlight Duration", params.sunlight_duration_min, "min")
        result.add_param("orbit.orbits_per_day", "Orbits per Day", params.orbits_per_day, "")
        result.add_param("orbit.raan_drift_deg_day", "RAAN Drift", params.raan_drift_deg_day, "deg/day")
        result.add_param("orbit.footprint_radius_km", "Footprint Radius", params.footprint_radius_km, "km")

        # Contact time estimate
        gs_lat = state.get_requirement("ground_stations")
        gs_latitude = 78.0  # Default: Svalbard-like high latitude station
        contact_s = estimate_contact_time_per_day(alt, gs_latitude, inc)
        result.add_param("orbit.contact_time_per_day_s", "Contact Time/Day", contact_s, "s",
                         rationale=f"Estimated for GS at {gs_latitude:.0f}° lat")

        # Delta-V budget
        # For non-Earth orbits, use insertion delta-V from requirements
        dv_insertion = state.get_requirement("orbit.delta_v_insertion_ms") or 0.0
        dv_maintenance_req = state.get_requirement("orbit.delta_v_maintenance_ms") or 0.0

        if orbit_type in ("lunar", "interplanetary", "lagrange", "mars"):
            # Non-Earth orbits: use requirement-specified delta-V, no atmospheric drag
            dv_sk = dv_maintenance_req
            dv_deorbit = 0.0
            dv_total = dv_insertion + dv_sk
            result.log(f"Non-Earth orbit: using requirement-specified dV (insertion={dv_insertion:.0f}, maintenance={dv_sk:.0f} m/s)")
        else:
            dv_sk = delta_v_station_keeping(alt, mission_years)
            dv_deorbit = delta_v_deorbit(alt) if state.get_requirement("orbit.deorbit_required") != False else 0.0
            dv_total = dv_sk + dv_deorbit

        result.add_param("orbit.delta_v_sk_ms", "Station-keeping ΔV", dv_sk, "m/s",
                         rationale=f"Drag makeup over {mission_years:.0f} years")
        result.add_param("orbit.delta_v_deorbit_ms", "Deorbit ΔV", dv_deorbit, "m/s")
        result.add_param("orbit.delta_v_total_ms", "Total ΔV", dv_total, "m/s", margin_percent=10)

        result.confidence = 0.95
        return result
