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
        sc_class = state.get_requirement("spacecraft_class", "small")
        eps_mass = state.get("power.eps_mass_kg", 0) or 0
        tcs_mass = state.get("thermal.tcs_mass_kg", 0) or 0
        ttc_mass = state.get("link.ttc_mass_kg", 0) or 0
        aocs_mass = state.get("aocs.mass_kg", 0) or 0
        struct_mass = state.get("structure.mass_kg", 0) or 0
        # Prefer data agent's class-aware OBDH estimate over a hard-coded value.
        obdh_mass = state.get("data.obdh_mass_kg")
        if obdh_mass is None:
            obdh_mass = {
                "nano": 0.2, "micro": 0.5, "small": 1.5,
                "medium": 2.5, "large": 4.0, "flagship": 6.5,
            }.get(sc_class, 1.5)

        platform_mass_raw = eps_mass + tcs_mass + ttc_mass + aocs_mass + struct_mass + obdh_mass

        # Propellant and dry propulsion hardware
        prop_mass = state.get("propulsion.propellant_mass_kg", 0) or 0
        prop_system = state.get("propulsion.total_mass_kg", 0) or 0
        prop_dry_hw = prop_system - prop_mass  # Dry propulsion hardware (tanks, engine, feed)

        # Platform mass floor: empirical minimum based on heritage data.
        # Parametric models underestimate harness, brackets, connectors, MLI,
        # separation system, and integration overhead for micro+ class.
        # Sources: SMAD4 Table 10-8, ESA CDF heritage, SSTL platform data.
        #
        # The floor represents the minimum plausible platform mass for a
        # spacecraft of this class, independent of what the subsystem models
        # compute. It accounts for the "missing mass" that parametric sizing
        # systematically omits.
        _PLATFORM_FLOOR: dict[str, float] = {
            "nano":     0.0,   # CubeSats: COTS boards, no missing overhead
            "micro":    35.0,  # PROBA-class: harness+PCDU+brackets+sep ~35 kg min
            "small":    55.0,  # 100-500 kg class: ~55 kg platform minimum
            "medium":  120.0,  # 500-2000 kg: ~120 kg
            "large":   250.0,  # 2000+ kg
            "flagship": 500.0,
        }
        platform_floor = _PLATFORM_FLOOR.get(sc_class, 0.0)
        platform_mass = max(platform_mass_raw, platform_floor)

        dry_mass = payload_mass + platform_mass + prop_dry_hw
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
