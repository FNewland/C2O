"""SpaceCDF — Cost Estimation Agent (Tier 2).

Rule-based parametric cost estimation using heritage CER data.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


# Cost Estimating Relationships (CER) — kEUR per kg by subsystem
# Based on SSCM and heritage data, inflation-adjusted to 2025
CER_KEUR_PER_KG = {
    "eps": 80,
    "aocs": 120,
    "tcs": 15,
    "ttc": 100,
    "obdh": 150,
    "structure": 8,
    "propulsion": 50,
    "payload": 200,
}

# Non-recurring engineering as fraction of hardware cost
NRE_FRACTION = {
    "nano": 0.50,    # CubeSat — high NRE relative to hardware
    "micro": 0.60,
    "small": 0.80,
    "medium": 1.00,
    "large": 1.20,
    "flagship": 1.50,
}

# Operations cost per year (kEUR)
OPS_COST_PER_YEAR = {
    "nano": 200,
    "micro": 500,
    "small": 1500,
    "medium": 5000,
    "large": 15000,
    "flagship": 50000,
}


class CostAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "cost"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return [
            "mass.dry_mass_kg", "mass.payload_kg",
            "power.eps_mass_kg", "aocs.mass_kg", "thermal.tcs_mass_kg",
            "link.ttc_mass_kg", "structure.mass_kg", "propulsion.total_mass_kg",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "cost.hardware_keur", "cost.nre_keur", "cost.launch_keur",
            "cost.operations_keur", "cost.total_keur", "cost.total_meur",
        ]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        sc_class = state.get("mission.spacecraft_class", "small")
        if not isinstance(sc_class, str):
            sc_class = "small"
        mission_years = state.get("mission.duration_years", 3.0) or 3.0

        # Hardware cost by subsystem
        hw_cost = 0.0
        subsystems = {
            "eps": state.get("power.eps_mass_kg", 0) or 0,
            "aocs": state.get("aocs.mass_kg", 0) or 0,
            "tcs": state.get("thermal.tcs_mass_kg", 0) or 0,
            "ttc": state.get("link.ttc_mass_kg", 0) or 0,
            "structure": state.get("structure.mass_kg", 0) or 0,
            "propulsion": state.get("propulsion.total_mass_kg", 0) or 0,
            "payload": state.get("mass.payload_kg", 0) or 0,
        }

        for subsys, mass in subsystems.items():
            cer = CER_KEUR_PER_KG.get(subsys, 50)
            hw_cost += mass * cer

        # OBDH
        obdh_mass = state.get("data.obdh_mass_kg", 2.0) or 2.0
        hw_cost += obdh_mass * CER_KEUR_PER_KG.get("obdh", 150)

        # AIT (Assembly, Integration, Test) — typically 10-15% of hardware
        ait_cost = hw_cost * 0.12

        # NRE
        nre_fraction = NRE_FRACTION.get(sc_class, 1.0)
        nre_cost = hw_cost * nre_fraction

        # Launch cost estimate
        wet_mass = state.get("mass.wet_mass_kg", 100.0) or 100.0
        if wet_mass < 50:
            launch_cost = 1000  # Rideshare ~1 MEUR
        elif wet_mass < 300:
            launch_cost = 3000  # Dedicated smallsat launcher
        elif wet_mass < 2000:
            launch_cost = 10000  # Rideshare on Falcon 9
        elif wet_mass < 5000:
            launch_cost = 30000  # Dedicated medium launcher
        else:
            launch_cost = 80000  # Large launcher

        # Operations
        ops_per_year = OPS_COST_PER_YEAR.get(sc_class, 1500)
        ops_cost = ops_per_year * mission_years

        total = hw_cost + ait_cost + nre_cost + launch_cost + ops_cost

        result.add_param("cost.hardware_keur", "Hardware Cost", round(hw_cost, 0), "kEUR")
        result.add_param("cost.nre_keur", "NRE Cost", round(nre_cost, 0), "kEUR")
        result.add_param("cost.launch_keur", "Launch Cost", round(launch_cost, 0), "kEUR")
        result.add_param("cost.operations_keur", "Operations Cost", round(ops_cost, 0), "kEUR")
        result.add_param("cost.total_keur", "Total Cost", round(total, 0), "kEUR")
        result.add_param("cost.total_meur", "Total Cost", round(total / 1000, 1), "MEUR")

        result.log(f"Cost breakdown: HW={hw_cost:.0f} + AIT={ait_cost:.0f} + NRE={nre_cost:.0f} + Launch={launch_cost:.0f} + Ops={ops_cost:.0f} = {total:.0f} kEUR")

        target = state.get_requirement("target_cost_meur")
        if target and total / 1000 > target:
            result.add_warning(f"Cost estimate {total/1000:.1f} MEUR exceeds target {target:.1f} MEUR")

        result.confidence = 0.60  # Parametric cost estimates have high uncertainty
        return result
