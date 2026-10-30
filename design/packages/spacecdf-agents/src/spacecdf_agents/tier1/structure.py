"""SpaceCDF — Structure Design Agent (Tier 1).

Estimates structural mass using parametric heritage correlations.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.structures import estimate_structure_mass


class StructureAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "structure"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return ["mass.dry_mass_estimate_kg", "mission.spacecraft_class"]

    def output_parameters(self) -> list[str]:
        return ["structure.mass_kg", "structure.cost_keur"]

    def dependencies(self) -> list[str]:
        return []  # No strict dependency — uses estimate

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        dry_mass = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        sc_class = state.get_requirement("spacecraft_class", "small")

        struct = estimate_structure_mass(
            spacecraft_dry_mass_kg=dry_mass,
            spacecraft_class=sc_class,
        )

        result.add_param("structure.mass_kg", "Structure Mass", round(struct.structure_mass_kg, 2), "kg",
                         margin_percent=20)
        result.add_param("structure.cost_keur", "Structure Cost", round(struct.structure_cost_keur, 0), "kEUR")
        result.add_param("structure.fraction", "Structure Fraction", round(struct.structure_fraction, 3), "")

        result.confidence = 0.70  # Parametric estimates
        return result
