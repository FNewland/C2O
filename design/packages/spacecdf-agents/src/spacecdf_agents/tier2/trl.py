"""SpaceCDF — TRL Innovation Agent (Tier 2).

Identifies technology innovation opportunities for each subsystem.
Proposes low-TRL alternatives alongside proven baselines, following
the project philosophy of testing new tech with every mission.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.models.parameter import TRLAssessment


# Innovation opportunities database — maps subsystems to potential innovations
INNOVATION_DB = {
    "eps": [
        {
            "baseline": "Triple-junction GaAs (Azur Space 3G30C)",
            "baseline_trl": 9,
            "innovation": "Perovskite-silicon tandem solar cells",
            "innovation_trl": 5,
            "benefit": "40% higher efficiency, lower manufacturing cost",
            "risk": "Radiation degradation not fully characterised",
            "mass_reduction": 0.15,
            "cost_reduction": 0.10,
        },
        {
            "baseline": "Li-ion battery (SAFT VES16)",
            "baseline_trl": 9,
            "innovation": "Solid-state lithium battery",
            "innovation_trl": 4,
            "benefit": "2x energy density, no thermal runaway risk",
            "risk": "Limited cycle life data in space environment",
            "mass_reduction": 0.30,
            "cost_reduction": -0.20,  # More expensive
        },
    ],
    "aocs": [
        {
            "baseline": "Reaction wheels + star tracker",
            "baseline_trl": 9,
            "innovation": "MEMS gyroscope + AI-based attitude determination",
            "innovation_trl": 5,
            "benefit": "50% mass reduction, lower power",
            "risk": "AI algorithms not space-qualified",
            "mass_reduction": 0.40,
            "cost_reduction": 0.30,
        },
    ],
    "ttc": [
        {
            "baseline": "X-band transponder (conventional)",
            "baseline_trl": 9,
            "innovation": "Optical inter-satellite link (OISL) terminal",
            "innovation_trl": 6,
            "benefit": "100x data rate, no frequency coordination",
            "risk": "Pointing requirements challenging for small sats",
            "mass_reduction": -0.20,  # Heavier
            "cost_reduction": -0.50,  # More expensive
        },
    ],
    "propulsion": [
        {
            "baseline": "Monoprop hydrazine",
            "baseline_trl": 9,
            "innovation": "Water electrolysis green propulsion",
            "innovation_trl": 5,
            "benefit": "Non-toxic, ITAR-free, simpler ground handling",
            "risk": "Lower ISP, larger tanks",
            "mass_reduction": -0.10,
            "cost_reduction": 0.40,
        },
        {
            "baseline": "Hall-effect thruster",
            "baseline_trl": 8,
            "innovation": "Electrospray (ionic liquid) thruster",
            "innovation_trl": 6,
            "benefit": "Ultra-precise thrust, no moving parts",
            "risk": "Limited total impulse for large dV",
            "mass_reduction": 0.20,
            "cost_reduction": 0.10,
        },
    ],
    "structure": [
        {
            "baseline": "Aluminium honeycomb panels",
            "baseline_trl": 9,
            "innovation": "3D-printed titanium lattice structure",
            "innovation_trl": 6,
            "benefit": "30% mass reduction, integrated thermal paths",
            "risk": "Qualification for flight loads ongoing",
            "mass_reduction": 0.30,
            "cost_reduction": -0.30,
        },
    ],
    "thermal": [
        {
            "baseline": "MLI + radiator panels",
            "baseline_trl": 9,
            "innovation": "Phase-change material thermal buffer",
            "innovation_trl": 5,
            "benefit": "Eliminates heater power during eclipse",
            "risk": "Mass penalty, limited thermal cycling data",
            "mass_reduction": -0.20,
            "cost_reduction": 0.15,
        },
    ],
    "obdh": [
        {
            "baseline": "RAD750 / GR740 radiation-hardened processor",
            "baseline_trl": 9,
            "innovation": "COTS RISC-V with radiation-tolerant design",
            "innovation_trl": 5,
            "benefit": "10x compute performance, 1/10th cost",
            "risk": "SEE mitigation needs flight validation",
            "mass_reduction": 0.10,
            "cost_reduction": 0.70,
        },
    ],
}


class TRLAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "trl"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return [
            "power.eps_mass_kg", "aocs.mass_kg", "thermal.tcs_mass_kg",
            "link.ttc_mass_kg", "structure.mass_kg", "propulsion.total_mass_kg",
        ]

    def output_parameters(self) -> list[str]:
        return ["trl.innovation_count", "trl.recommended_innovations"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        assessments = []
        top_innovations = []

        mass_params = {
            "eps": state.get("power.eps_mass_kg", 5) or 5,
            "aocs": state.get("aocs.mass_kg", 5) or 5,
            "ttc": state.get("link.ttc_mass_kg", 2) or 2,
            "thermal": state.get("thermal.tcs_mass_kg", 2) or 2,
            "structure": state.get("structure.mass_kg", 10) or 10,
            "propulsion": state.get("propulsion.total_mass_kg", 5) or 5,
            "obdh": state.get("data.obdh_mass_kg", 2) or 2,
        }

        for subsys, innovations in INNOVATION_DB.items():
            mass = mass_params.get(subsys, 5)
            for innov in innovations:
                trl_a = TRLAssessment(
                    subsystem=subsys,
                    baseline_component=innov["baseline"],
                    baseline_trl=innov["baseline_trl"],
                    baseline_mass_kg=mass,
                    innovation_component=innov["innovation"],
                    innovation_trl=innov["innovation_trl"],
                    innovation_mass_kg=mass * (1 - innov["mass_reduction"]),
                    innovation_benefit=innov["benefit"],
                    innovation_risk=innov["risk"],
                )

                score = trl_a.innovation_benefit_score
                if score > 0.05:
                    trl_a.recommendation = "carry_both"
                    top_innovations.append((score, subsys, innov))
                else:
                    trl_a.recommendation = "baseline"

                assessments.append(trl_a)

        # Sort by benefit score and recommend top 2
        top_innovations.sort(reverse=True)
        recommended = top_innovations[:2]

        result.trl_assessments = assessments
        result.add_param("trl.innovation_count", "Innovation Opportunities", len(top_innovations), "")

        rec_names = []
        for score, subsys, innov in recommended:
            rec_names.append(f"{subsys}: {innov['innovation']}")
            result.add_recommendation(
                f"[INNOVATION] {subsys.upper()}: Consider {innov['innovation']} (TRL {innov['innovation_trl']}) "
                f"as tech demo alongside baseline {innov['baseline']}. "
                f"Benefit: {innov['benefit']}. Risk: {innov['risk']}"
            )

        result.add_param("trl.recommended_innovations", "Recommended Innovations",
                         "; ".join(rec_names) if rec_names else "None", "")

        result.confidence = 0.70
        return result
