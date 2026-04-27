"""SpaceCDF — Sustainability Score Agent (Tier 2).

Computes a composite sustainability score aligned with ESA's Space
Sustainability Rating (SSR) framework. Considers debris compliance,
orbit selection, passivation capability, trackability, and collision
avoidance readiness.

Reference: ESA Space Sustainability Rating (2023), World Economic Forum.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


class SustainabilityAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "sustainability"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return [
            "orbit.altitude_km", "mass.dry_mass_kg",
            "debris.compliance_score", "debris.compliant_5yr",
            "debris.passivation_score", "debris.collision_avoidance_dv_per_year_ms",
            "propulsion.type", "mission.duration_years",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "sustainability.score", "sustainability.grade",
            "sustainability.orbit_responsibility",
            "sustainability.eol_readiness",
            "sustainability.trackability",
            "sustainability.collision_preparedness",
            "sustainability.mission_index",
        ]

    def dependencies(self) -> list[str]:
        return ["debris", "propulsion", "orbit"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        alt = state.get("orbit.altitude_km", 500.0)
        dry_mass = state.get("mass.dry_mass_kg", 10.0) or 10.0
        mission_years = state.get("mission.duration_years", 3.0) or 3.0

        debris_score = state.get("debris.compliance_score", 50.0) or 50.0
        compliant_5yr = state.get("debris.compliant_5yr", 0.0)
        passivation = state.get("debris.passivation_score", 0.5) or 0.5
        ca_dv = state.get("debris.collision_avoidance_dv_per_year_ms", 0.0) or 0.0

        prop_type = state.get("propulsion.type")
        prop_str = str(prop_type) if prop_type else "none"
        has_propulsion = prop_str not in ("none", "", "None")

        # --- Orbit Responsibility (0-25) ---
        # Prefer orbits with natural decay; penalise congested altitudes
        if alt < 400:
            orbit_resp = 25.0  # Quick natural decay
        elif alt < 600:
            orbit_resp = 20.0  # Moderate lifetime
        elif alt < 800:
            orbit_resp = 12.0  # Peak debris zone
        elif alt < 1000:
            orbit_resp = 8.0   # Long lifetime, congested
        else:
            orbit_resp = 5.0   # Very long lifetime
        if compliant_5yr:
            orbit_resp = min(25, orbit_resp + 5)

        # --- End-of-Life Readiness (0-25) ---
        eol_readiness = 0.0
        if has_propulsion:
            eol_readiness += 15.0  # Can perform controlled deorbit
        if passivation >= 0.8:
            eol_readiness += 10.0
        elif passivation >= 0.5:
            eol_readiness += 5.0

        # --- Trackability (0-20) ---
        # Larger objects are easier to track; active tracking aids help
        if dry_mass > 100:
            trackability = 18.0  # Easily tracked by SSA networks
        elif dry_mass > 10:
            trackability = 14.0
        elif dry_mass > 1:
            trackability = 8.0   # CubeSats harder to track
        else:
            trackability = 4.0
        # Bonus for active tracking capability (GPS + transponder)
        trackability = min(20, trackability + 2)

        # --- Collision Preparedness (0-15) ---
        if has_propulsion and ca_dv > 0:
            collision_prep = min(15, 5 + ca_dv * 2)
        elif has_propulsion:
            collision_prep = 8.0
        else:
            collision_prep = 2.0

        # --- Mission Index (0-15) ---
        # Reward efficient use of orbital slot: shorter mission = less exposure
        if mission_years <= 1:
            mission_idx = 15.0
        elif mission_years <= 3:
            mission_idx = 12.0
        elif mission_years <= 7:
            mission_idx = 8.0
        else:
            mission_idx = 5.0

        total = orbit_resp + eol_readiness + collision_prep + trackability + mission_idx
        total = min(100, max(0, total))

        # Grade
        if total >= 85:
            grade = "A"
        elif total >= 70:
            grade = "B"
        elif total >= 55:
            grade = "C"
        elif total >= 40:
            grade = "D"
        else:
            grade = "F"

        result.add_param("sustainability.score", "Sustainability Score", round(total, 0), "")
        result.add_param("sustainability.grade", "Sustainability Grade", grade, "")
        result.add_param("sustainability.orbit_responsibility", "Orbit Responsibility", round(orbit_resp, 0), "")
        result.add_param("sustainability.eol_readiness", "EOL Readiness", round(eol_readiness, 0), "")
        result.add_param("sustainability.trackability", "Trackability", round(trackability, 0), "")
        result.add_param("sustainability.collision_preparedness", "Collision Preparedness", round(collision_prep, 0), "")
        result.add_param("sustainability.mission_index", "Mission Efficiency Index", round(mission_idx, 0), "")

        if total < 55:
            result.add_warning(f"Sustainability score {total:.0f}/100 (grade {grade}) — review debris mitigation strategy")

        result.confidence = 0.70
        return result
