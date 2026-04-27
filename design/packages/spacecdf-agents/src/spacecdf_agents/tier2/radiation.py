"""SpaceCDF — Radiation Environment Agent (Tier 2)."""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.radiation import estimate_radiation


class RadiationAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "radiation"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return ["orbit.altitude_km", "orbit.inclination_deg", "mass.dry_mass_kg", "mission.duration_years"]

    def output_parameters(self) -> list[str]:
        return [
            "radiation.tid_mission_krad", "radiation.tid_per_year_krad",
            "radiation.environment", "radiation.electronics_class",
            "radiation.shielding_mass_kg", "radiation.see_rate_per_day",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit", "mass"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        alt = state.get("orbit.altitude_km", 500.0)
        inc = state.get("orbit.inclination_deg", 97.4) or 97.4
        dry_mass = state.get("mass.dry_mass_kg", 100.0) or 100.0
        mission_years = state.get("mission.duration_years", 3.0) or 3.0

        orbit_type = state.get_requirement("orbit.orbit_type")
        body = "moon" if orbit_type == "lunar" else ("mars" if orbit_type == "mars" else "earth")

        rad = estimate_radiation(
            altitude_km=alt, inclination_deg=inc,
            mission_duration_years=mission_years,
            shielding_mm_al=1.0, body=body, dry_mass_kg=dry_mass,
        )

        result.add_param("radiation.tid_mission_krad", "Total Mission Dose", round(rad.tid_mission_krad, 1), "krad")
        result.add_param("radiation.tid_per_year_krad", "Annual Dose Rate", round(rad.tid_krad_per_year, 1), "krad/yr")
        result.add_param("radiation.environment", "Radiation Environment", rad.environment, "")
        result.add_param("radiation.electronics_class", "Electronics Class Required", rad.electronics_class, "")
        result.add_param("radiation.shielding_mass_kg", "Shielding Mass", round(rad.shielding_mass_kg, 2), "kg")
        result.add_param("radiation.see_rate_per_day", "SEE Rate (relative)", round(rad.see_rate_per_day, 2), "/day")

        result.warnings.extend(rad.warnings)
        result.confidence = 0.65
        return result
