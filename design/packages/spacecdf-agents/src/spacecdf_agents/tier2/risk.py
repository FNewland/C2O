"""SpaceCDF — Risk Assessment Agent (Tier 2).

Rule-based risk identification and scoring using a standard
risk matrix (likelihood x consequence).
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_agents.exporters.docs.agent_extras import risk_entry


class RiskAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "risk"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return [
            "systems.health_score",
            "mass.dry_mass_kg", "cost.total_meur",
        ]

    def output_parameters(self) -> list[str]:
        return ["risk.total_risks", "risk.high_risks", "risk.risk_score"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)
        risks = []

        # Check for low-TRL components
        for pid, param in state.parameters.items():
            if param.trl is not None and param.trl <= 5:
                risks.append({
                    "id": f"TRL-{pid}",
                    "description": f"{param.name} at TRL {param.trl}",
                    "likelihood": 3,
                    "consequence": 3,
                    "category": "technical",
                    "mitigation": f"Develop {param.name} to TRL 6+ before PDR; carry backup at TRL 7+",
                })

        # Single-string-of-pearls risks
        health = state.get("systems.health_score", 100) or 100
        if health < 60:
            risks.append({
                "id": "SYS-001",
                "description": "Multiple budget margins tight — design fragile",
                "likelihood": 4,
                "consequence": 4,
                "category": "programmatic",
                "mitigation": "Review requirements; consider relaxing secondary requirements",
            })

        # Schedule risk for complex missions
        sc_class = state.get("mission.spacecraft_class", "small")
        if isinstance(sc_class, str) and sc_class in ("large", "flagship"):
            risks.append({
                "id": "PROG-001",
                "description": "Large mission schedule risk — integration complexity",
                "likelihood": 4,
                "consequence": 3,
                "category": "programmatic",
                "mitigation": "Plan for 6-month schedule margin; early long-lead procurement",
            })

        high_risks = sum(1 for r in risks if r["likelihood"] * r["consequence"] >= 12)
        total_score = sum(r["likelihood"] * r["consequence"] for r in risks)

        result.add_param("risk.total_risks", "Total Risks", len(risks), "")
        result.add_param("risk.high_risks", "High Risks", high_risks, "")
        result.add_param("risk.risk_score", "Risk Score", total_score, "")

        for r in risks:
            severity = "HIGH" if r["likelihood"] * r["consequence"] >= 12 else "MEDIUM"
            result.add_warning(f"[{severity}] {r['description']}")
            result.add_recommendation(f"Mitigation for {r['id']}: {r['mitigation']}")

        # ---- Report-quality narrative & structured intermediates ----
        result.rationale = (
            f"Identified {len(risks)} risks ({high_risks} high-rated, "
            f"aggregate score {total_score}).  Risks scored on a 5×5 "
            f"likelihood × severity matrix per ECSS-M-ST-80C; mitigation "
            f"actions are tracked in the Risk Management Plan."
        )
        result.assumptions = [
            "Likelihood/severity scaled 1–5 per ECSS-M-ST-80C.",
            "Score ≥12 → red, 8–11 → amber, <8 → green.",
            "Technical risks anchored to TRL ≤5 components from the design state.",
        ]
        result.extras["risk.register"] = [
            risk_entry(id=r["id"], name=r["description"],
                       likelihood=r["likelihood"], severity=r["consequence"],
                       mitigation=r.get("mitigation", ""),
                       owner=r.get("category", "system"))
            for r in risks
        ]

        result.confidence = 0.70
        return result
