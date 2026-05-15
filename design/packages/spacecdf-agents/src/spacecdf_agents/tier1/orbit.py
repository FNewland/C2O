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
from spacecdf_agents.exporters.docs.agent_extras import delta_v_breakdown


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

        # Determine central body from orbit type
        body = "earth"
        if orbit_type in ("lunar",):
            body = "moon"
        elif orbit_type in ("mars",):
            body = "mars"

        # Auto-compute SSO inclination if needed (Earth only)
        if orbit_type == "sso" and (inc is None or inc == 0):
            inc = sso_inclination(alt)
            result.log(f"Computed SSO inclination: {inc:.2f} deg for {alt:.0f} km")
        elif inc is None:
            inc = 97.4  # Default SSO

        # Compute orbital parameters
        params = compute_orbit_params(alt, inc, body=body)

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

        # ---- Report-quality narrative & structured intermediates ----
        # Flatten any enum representation to a clean uppercase token
        _ot = getattr(orbit_type, "value", orbit_type)
        _ot = str(_ot).split(".")[-1].upper().replace("_", " ")
        result.rationale = (
            f"Orbit chosen as {_ot} at {alt:.0f} km altitude "
            f"and inclination {inc:.2f}°.  The Keplerian period is {params.period_min:.1f} min "
            f"({params.orbits_per_day:.1f} orbits / day) with an eclipse fraction of "
            f"{params.eclipse_fraction:.2f} (cylindrical shadow).  A high-latitude ground "
            f"station near {gs_latitude:.0f}° provides ≈{contact_s/60:.1f} min of contact / day."
        )
        result.add_assumption(f"Cylindrical Earth-shadow eclipse model (no penumbra).")
        result.add_assumption(f"Ground-station latitude assumed {gs_latitude:.0f}° (Svalbard-class).")
        if orbit_type in ("lunar", "interplanetary", "lagrange", "mars"):
            result.add_assumption(
                "Atmospheric drag neglected — non-Earth-orbit / deep-space regime; "
                "station-keeping ΔV taken from mission requirements."
            )
        else:
            result.add_assumption(
                f"Station-keeping ΔV from JR-1971 drag model over {mission_years:.0f}-yr life."
            )

        result.extras["orbit.delta_v_breakdown"] = delta_v_breakdown(
            ("Insertion", dv_insertion,
             "From launch vehicle injection accuracy / orbital manoeuvres."),
            ("Station-keeping", dv_sk,
             f"Drag makeup over {mission_years:.0f} yr design life."),
            ("Collision avoidance",
             1.0 * (mission_years or 1.0) if body == "earth" else 0.0,
             "Allowance of ~1 m/s per year for collision-avoidance burns."),
            ("Deorbit / EOL", dv_deorbit,
             "Lower perigee for ≤25-yr re-entry (IADC compliance)."),
        )
        result.extras["orbit.contact_window"] = {
            "per_day_s": contact_s,
            "ground_station_latitude_deg": gs_latitude,
            "footprint_radius_km": params.footprint_radius_km,
        }
        result.extras["orbit.geometry"] = {
            "altitude_km": alt,
            "inclination_deg": inc,
            "orbit_type": str(orbit_type).upper(),
            "eclipse_fraction": params.eclipse_fraction,
            "central_body": body,
        }

        result.confidence = 0.95
        return result
