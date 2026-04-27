"""SpaceCDF — Community & Societal Impact Agent (Tier 2).

Assesses mission impact across stakeholder engagement, open science,
educational value, international collaboration, and capacity building.
Designed for C4 (Community-Centred Challenge Collaboratory) integration.

This agent produces qualitative and quantitative metrics that help
design teams think beyond purely technical optimisation.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


class CommunityImpactAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "community"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return ["mission.duration_years", "mass.dry_mass_kg", "cost.total_meur"]

    def output_parameters(self) -> list[str]:
        return [
            "community.stakeholder_count",
            "community.open_data_score",
            "community.educational_value",
            "community.collaboration_index",
            "community.capacity_building_score",
            "community.societal_impact_score",
            "community.explainability_score",
        ]

    def dependencies(self) -> list[str]:
        return ["cost", "mass"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        mission_type = state.get_requirement("mission_type") or "technology_demo"
        if hasattr(mission_type, "value"):
            mission_type = mission_type.value
        mission_type = str(mission_type)

        sc_class = state.get_requirement("spacecraft_class", "small")
        cost_meur = state.get("cost.total_meur", 10.0) or 10.0
        num_payloads = 0
        i = 0
        while state.get(f"payload.{i}.mass_kg") is not None:
            num_payloads += 1
            i += 1

        # --- Stakeholder mapping ---
        # Base stakeholders: design team, funding agency, launch provider
        stakeholders = 3
        # Science missions add science community
        if mission_type in ("earth_observation", "science_planetary", "science_heliophysics",
                            "science_astrophysics", "lunar"):
            stakeholders += 3  # PI team, co-Is, data users
        # EO adds downstream data users (agriculture, climate, disaster response)
        if mission_type == "earth_observation":
            stakeholders += 4  # Copernicus-like downstream
        # Tech demo adds industry partners
        if mission_type == "technology_demo":
            stakeholders += 2
        # Scale with cost (larger missions = more stakeholders)
        if cost_meur > 50:
            stakeholders += 3
        elif cost_meur > 10:
            stakeholders += 1

        # --- Open data score (0-100) ---
        # Assumes open data unless mission is explicitly commercial
        open_data = 70.0  # Default: most publicly-funded missions release data
        if mission_type == "earth_observation":
            open_data = 90.0  # Copernicus/Landsat tradition
        elif mission_type in ("science_planetary", "science_astrophysics", "lunar"):
            open_data = 85.0  # NASA/ESA science data policies
        elif mission_type == "communications":
            open_data = 20.0  # Commercial
        elif mission_type == "technology_demo":
            open_data = 60.0  # Published results but not continuous data

        # --- Educational value (0-100) ---
        educational = 40.0  # Base: all missions have some educational value
        if sc_class == "nano":
            educational += 30.0  # CubeSats are inherently educational
        if mission_type == "technology_demo":
            educational += 20.0
        if cost_meur < 10:
            educational += 10.0  # Accessible cost for university missions
        educational = min(100, educational)

        # --- Collaboration index (0-100) ---
        # Number of instruments × geographic spread × mission complexity
        collab = 30.0 + num_payloads * 10.0
        if cost_meur > 50:
            collab += 20.0  # Big missions → international consortia
        collab = min(100, collab)

        # --- Capacity building (0-100) ---
        # Higher for missions that build local capability
        capacity = 30.0
        if sc_class in ("nano", "micro"):
            capacity += 25.0  # Small sats build national capability
        if mission_type == "technology_demo":
            capacity += 20.0  # Explicit TRL advancement
        if cost_meur < 20:
            capacity += 10.0  # Affordable for developing space nations
        capacity = min(100, capacity)

        # --- Explainability score (0-100) ---
        # How well can the design decisions be explained to non-specialists?
        # SpaceCDF provides rationale chains — this scores their completeness
        params_with_rationale = 0
        total_params = 0
        for pid, p in state.parameters.items():
            total_params += 1
            if hasattr(p, "rationale") and p.rationale:
                params_with_rationale += 1
        explainability = (params_with_rationale / max(total_params, 1)) * 80 + 20

        # --- Composite societal impact score ---
        societal = (
            open_data * 0.25 +
            educational * 0.20 +
            collab * 0.15 +
            capacity * 0.20 +
            explainability * 0.20
        )

        result.add_param("community.stakeholder_count", "Stakeholder Groups", stakeholders, "")
        result.add_param("community.open_data_score", "Open Data Score", round(open_data, 0), "")
        result.add_param("community.educational_value", "Educational Value", round(educational, 0), "")
        result.add_param("community.collaboration_index", "Collaboration Index", round(collab, 0), "")
        result.add_param("community.capacity_building_score", "Capacity Building", round(capacity, 0), "")
        result.add_param("community.societal_impact_score", "Societal Impact Score", round(societal, 0), "")
        result.add_param("community.explainability_score", "Design Explainability", round(explainability, 0), "")

        result.confidence = 0.50  # Qualitative assessment
        return result
