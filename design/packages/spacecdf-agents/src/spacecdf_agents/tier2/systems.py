"""SpaceCDF — Systems Engineering Agent (Tier 2).

Rule-based system-level assessment: budget status, interface checks,
requirement verification, and design recommendations.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


class SystemsAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "systems"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return [
            "mass.dry_mass_kg", "mass.wet_mass_kg",
            "power.sa_power_eol_w", "power.total_sunlight_w",
            "data.generated_per_day_gb", "data.downlinked_per_day_gb",
            "link.downlink_margin_db",
        ]

    def output_parameters(self) -> list[str]:
        return ["systems.health_score", "systems.mass_margin_percent", "systems.power_margin_percent"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)
        score = 100.0

        # Mass margin check
        dry_mass = state.get("mass.dry_mass_kg", 0) or 0
        target_mass = state.get_requirement("target_mass_kg")
        if target_mass and dry_mass > 0:
            mass_margin = (target_mass - dry_mass * 1.2) / target_mass * 100
            result.add_param("systems.mass_margin_percent", "Mass Margin", round(mass_margin, 1), "%")
            if mass_margin < 0:
                result.add_warning(f"Mass budget EXCEEDED: dry mass {dry_mass:.1f}kg with 20% margin exceeds {target_mass:.0f}kg allocation")
                score -= 25
            elif mass_margin < 10:
                result.add_warning(f"Mass margin tight: {mass_margin:.1f}%")
                score -= 10

        # Power margin check
        sa_power = state.get("power.sa_power_eol_w", 0) or 0
        power_demand = state.get("power.total_sunlight_w", 0) or 0
        if sa_power > 0 and power_demand > 0:
            power_margin = (sa_power - power_demand) / sa_power * 100
            result.add_param("systems.power_margin_percent", "Power Margin", round(power_margin, 1), "%")
            if power_margin < 10:
                result.add_warning(f"Power margin tight: {power_margin:.1f}%")
                score -= 15

        # Data budget check
        gen = state.get("data.generated_per_day_gb", 0) or 0
        downlink = state.get("data.downlinked_per_day_gb", 0) or 0
        if gen > 0 and downlink > 0 and gen > downlink:
            result.add_warning(f"Data deficit: {gen:.1f} GB/day generated vs {downlink:.1f} GB/day downlinked")
            score -= 15
            result.add_recommendation("Consider higher data rate downlink (Ka-band) or onboard data compression/selection")

        # Link margin check
        link_margin = state.get("link.downlink_margin_db", 0) or 0
        if 0 < link_margin < 3:
            result.add_warning(f"Link margin {link_margin:.1f}dB below 3dB minimum")
            score -= 10

        result.add_param("systems.health_score", "Design Health Score", round(max(0, score), 0), "")
        result.confidence = 0.90
        return result
