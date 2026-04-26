"""SpaceCDF — Mass Budget Agent (Tier 1).

Aggregates mass from all subsystem agents and tracks the system mass budget.
This agent runs last in Tier 1 to capture all subsystem masses.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


class MassAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "mass"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return [
            "payload.0.mass_kg",
            "power.eps_mass_kg", "thermal.tcs_mass_kg",
            "link.ttc_mass_kg", "aocs.mass_kg",
            "structure.mass_kg", "propulsion.total_mass_kg",
            "data.obdh_mass_kg",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "mass.payload_kg", "mass.platform_kg",
            "mass.dry_mass_kg", "mass.propellant_kg",
            "mass.wet_mass_kg", "mass.dry_mass_estimate_kg",
        ]

    def dependencies(self) -> list[str]:
        return ["power", "thermal", "link", "aocs", "structure", "propulsion", "data"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        # Sum payload masses
        payload_mass = 0.0
        i = 0
        while True:
            pm = state.get(f"payload.{i}.mass_kg")
            if pm is None:
                break
            payload_mass += pm
            i += 1

        # Sum subsystem masses
        eps_mass = state.get("power.eps_mass_kg", 0) or 0
        tcs_mass = state.get("thermal.tcs_mass_kg", 0) or 0
        ttc_mass = state.get("link.ttc_mass_kg", 0) or 0
        aocs_mass = state.get("aocs.mass_kg", 0) or 0
        struct_mass = state.get("structure.mass_kg", 0) or 0
        # Prefer data agent's class-aware OBDH estimate over a hard-coded value.
        obdh_mass = state.get("data.obdh_mass_kg")
        if obdh_mass is None:
            # Class-aware fallback if data agent hasn't converged yet
            sc_class = state.get_requirement("spacecraft_class", "small")
            obdh_mass = {
                "nano": 0.2, "micro": 0.5, "small": 1.5,
                "medium": 2.5, "large": 4.0, "flagship": 6.5,
            }.get(sc_class, 1.5)

        platform_mass = eps_mass + tcs_mass + ttc_mass + aocs_mass + struct_mass + obdh_mass
        dry_mass = payload_mass + platform_mass

        # Propellant
        prop_mass = state.get("propulsion.propellant_mass_kg", 0) or 0
        prop_system = state.get("propulsion.total_mass_kg", 0) or 0
        dry_mass += prop_system - prop_mass  # Add dry propulsion hardware

        wet_mass = dry_mass + prop_mass

        result.add_param("mass.payload_kg", "Payload Mass", round(payload_mass, 2), "kg",
                         margin_percent=10)
        result.add_param("mass.platform_kg", "Platform Mass", round(platform_mass, 2), "kg",
                         margin_percent=20)
        result.add_param("mass.dry_mass_kg", "Dry Mass", round(dry_mass, 2), "kg",
                         margin_percent=20)
        result.add_param("mass.propellant_kg", "Propellant Mass", round(prop_mass, 2), "kg",
                         margin_percent=5)
        result.add_param("mass.wet_mass_kg", "Wet Mass (Launch)", round(wet_mass, 2), "kg",
                         margin_percent=20)
        # Estimate for upstream agents (structure, thermal) that need it before convergence
        result.add_param("mass.dry_mass_estimate_kg", "Dry Mass Estimate", round(dry_mass, 2), "kg",
                         confidence=0.7)

        result.confidence = 0.80
        return result
