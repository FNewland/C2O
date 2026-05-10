"""SpaceCDF — Cost Estimation Agent (Tier 2).

Rule-based parametric cost estimation using heritage CER data.

SCDF-144: This agent's CERs are the canonical source of truth for cost estimation.
The cost_engine.py service delegates to these same CERs for API-driven cost queries.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


# Cost Estimating Relationships — kEUR per kg by subsystem
# TWO models: CubeSat (COTS-anchored) and larger (SSCM-based)

# CubeSat COTS pricing (kEUR per subsystem, NOT per kg)
# Based on vendor pricing: GomSpace, ISIS, NanoAvionics, Endurosat
CUBESAT_SUBSYSTEM_COST_KEUR = {
    "eps": 15,        # NanoPower P31u + BP4 + panels: ~€10-20k
    "aocs": 40,       # Fine: RW(4×€8k) + ST(€15k) + MTQ(€5k) = ~€50k; Coarse: MTQ only ~€8k
    "aocs_coarse": 8,
    "tcs": 3,         # Passive: heaters + MLI ~€2-5k
    "ttc": 20,        # UHF transceiver €10-15k + antenna €2-5k
    "ttc_xband": 50,  # X-band transmitter €30-50k + antenna €10-15k
    "obdh": 10,       # NanoMind/SatBus OBC ~€5-15k
    "structure": 8,   # COTS frame €5-10k
    "propulsion": 60, # Cold gas €20-40k; Electric €50-100k
    "payload": 50,    # Highly variable: €10k (AIS) to €200k+ (custom imager)
    "harness": 5,     # Harness + connectors €3-8k
}

# Larger spacecraft CER — kEUR per kg (SSCM-based, inflation-adjusted 2025)
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
    "nano": 0.30,     # CubeSat — lower NRE (COTS reduces custom work)
    "micro": 0.50,
    "small": 0.80,
    "medium": 1.00,
    "large": 1.20,
    "flagship": 1.50,
}

# Operations cost per year (kEUR)
OPS_COST_PER_YEAR = {
    "nano": 100,      # CubeSat ops: mostly automated, ~€50-150k/yr
    "micro": 300,
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

        # Use get_requirement for string values (state.get only returns numerics)
        sc_class = state.get_requirement("spacecraft_class", "small")
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

        # CubeSat/small COTS: use flat pricing for small spacecraft
        dry_mass = state.get("mass.dry_mass_kg", 0) or 0
        use_cots = sc_class in ("nano", "micro") or (sc_class == "small" and dry_mass < 50)
        if use_cots:
            for subsys, mass in subsystems.items():
                if mass > 0:
                    hw_cost += CUBESAT_SUBSYSTEM_COST_KEUR.get(subsys, 20)
            hw_cost += CUBESAT_SUBSYSTEM_COST_KEUR.get("obdh", 10)
            hw_cost += CUBESAT_SUBSYSTEM_COST_KEUR.get("harness", 5)
        else:
            for subsys, mass in subsystems.items():
                cer = CER_KEUR_PER_KG.get(subsys, 50)
                hw_cost += mass * cer
            obdh_mass = state.get("data.obdh_mass_kg", 2.0) or 2.0
            hw_cost += obdh_mass * CER_KEUR_PER_KG.get("obdh", 150)

        # AIT (Assembly, Integration, Test) — typically 10-15% of hardware
        ait_cost = hw_cost * 0.12

        # NRE
        nre_fraction = NRE_FRACTION.get(sc_class, 1.0)
        nre_cost = hw_cost * nre_fraction

        # Launch cost estimate
        wet_mass = state.get("mass.wet_mass_kg", 100.0) or 100.0
        if wet_mass < 10:
            launch_cost = 200   # CubeSat rideshare: $200-350k (€150-250k)
        elif wet_mass < 50:
            launch_cost = 350   # Larger CubeSat rideshare
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
