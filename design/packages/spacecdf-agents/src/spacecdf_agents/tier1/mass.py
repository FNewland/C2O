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

        # Heritage calibration is now applied in each subsystem agent via
        # calibrate_mass(), so no platform-level floor is needed here.
        platform_mass = platform_mass_raw

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

        # ---- Report-quality narrative & structured intermediates ----
        dry_margin = 20.0
        result.rationale = (
            f"System mass rollup: payload {payload_mass:.2f} kg, platform "
            f"{platform_mass:.2f} kg (EPS {eps_mass:.2f}, TCS {tcs_mass:.2f}, "
            f"TT&C {ttc_mass:.2f}, AOCS {aocs_mass:.2f}, structure {struct_mass:.2f}, "
            f"OBDH {obdh_mass:.2f}), propulsion dry hardware {prop_dry_hw:.2f} kg, "
            f"yielding a dry mass of {dry_mass:.2f} kg and a wet (launch) mass "
            f"of {wet_mass:.2f} kg with {prop_mass:.2f} kg of propellant.  "
            f"ECSS Phase-A margin policy applied: payload 10%, platform 20%, "
            f"propellant 5%."
        )
        result.assumptions = [
            "Per-subsystem masses come from each Tier-1 agent with heritage calibration.",
            "OBDH mass set by class-aware default if data agent has not yet sized.",
            "Propulsion dry hardware = total propulsion mass − propellant mass.",
            "ECSS-E-ST-10-02 / SMAD Phase A margins applied per subsystem.",
        ]
        result.extras["mass.rollup"] = [
            {"subsystem": "Payload", "nominal_kg": payload_mass, "margin_percent": 10,
             "with_margin_kg": payload_mass * 1.10},
            {"subsystem": "EPS", "nominal_kg": eps_mass, "margin_percent": 20,
             "with_margin_kg": eps_mass * 1.20},
            {"subsystem": "AOCS", "nominal_kg": aocs_mass, "margin_percent": 20,
             "with_margin_kg": aocs_mass * 1.20},
            {"subsystem": "TT&C", "nominal_kg": ttc_mass, "margin_percent": 10,
             "with_margin_kg": ttc_mass * 1.10},
            {"subsystem": "OBDH", "nominal_kg": obdh_mass, "margin_percent": 20,
             "with_margin_kg": obdh_mass * 1.20},
            {"subsystem": "Thermal", "nominal_kg": tcs_mass, "margin_percent": 20,
             "with_margin_kg": tcs_mass * 1.20},
            {"subsystem": "Structure", "nominal_kg": struct_mass, "margin_percent": 20,
             "with_margin_kg": struct_mass * 1.20},
            {"subsystem": "Propulsion (dry)", "nominal_kg": prop_dry_hw,
             "margin_percent": 10, "with_margin_kg": prop_dry_hw * 1.10},
            {"subsystem": "Propellant", "nominal_kg": prop_mass,
             "margin_percent": 5, "with_margin_kg": prop_mass * 1.05},
        ]

        result.confidence = 0.80
        return result
