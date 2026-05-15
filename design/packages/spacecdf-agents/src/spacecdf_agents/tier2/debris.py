"""SpaceCDF — Debris Compliance Agent (Tier 2).

Assesses space debris mitigation compliance per ECSS-U-AS-10C Rev.2,
ISO 24113:2023, and NASA-STD-8719.14.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.debris import compute_debris_compliance


class DebrisComplianceAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "debris"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return [
            "orbit.altitude_km", "orbit.inclination_deg",
            "mass.dry_mass_kg", "propulsion.type",
            "orbit.delta_v_total_ms", "mission.duration_years",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "debris.lifetime_years", "debris.compliant_25yr",
            "debris.compliant_5yr", "debris.casualty_risk",
            "debris.casualty_compliant", "debris.passivation_score",
            "debris.collision_avoidance_dv_per_year_ms",
            "debris.compliance_score", "debris.deorbit_method",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit", "mass", "propulsion"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        alt = state.get("orbit.altitude_km", 500.0)
        inc = state.get("orbit.inclination_deg", 97.4) or 97.4
        dry_mass = state.get("mass.dry_mass_kg", 10.0) or 10.0
        mission_years = state.get("mission.duration_years", 3.0) or 3.0

        prop_type = state.get("propulsion.type")
        if hasattr(prop_type, "value"):
            prop_type = prop_type.value
        prop_type = str(prop_type) if prop_type else "none"
        has_propulsion = prop_type not in ("none", "", "None")

        # Available ΔV for deorbit (remaining after mission ΔV)
        orbit_type = state.get_requirement("orbit.orbit_type")
        if orbit_type in ("lunar", "mars", "interplanetary", "lagrange"):
            # Deep-space: not in Earth orbit, debris rules don't apply same way
            available_dv = 0.0
        else:
            deorbit_dv = state.get("orbit.delta_v_deorbit_ms", 0) or 0
            available_dv = deorbit_dv  # Allocated for deorbit

        dc = compute_debris_compliance(
            altitude_km=alt,
            inclination_deg=inc,
            dry_mass_kg=dry_mass,
            has_propulsion=has_propulsion,
            propulsion_type=prop_type,
            available_delta_v_ms=available_dv,
            has_battery=True,
            has_pressurised_tanks=has_propulsion,
            mission_duration_years=mission_years,
        )

        result.add_param("debris.lifetime_years", "Orbital Lifetime",
                         round(dc.lifetime_years, 1), "years")
        result.add_param("debris.compliant_25yr", "25-Year Rule Compliant",
                         1.0 if dc.compliant_25yr else 0.0, "")
        result.add_param("debris.compliant_5yr", "5-Year Rule Compliant",
                         1.0 if dc.compliant_5yr else 0.0, "")
        result.add_param("debris.casualty_risk", "Casualty Risk (Ec)",
                         dc.casualty_risk, "")
        result.add_param("debris.casualty_compliant", "Casualty Risk Compliant",
                         1.0 if dc.casualty_compliant else 0.0, "")
        result.add_param("debris.passivation_score", "Passivation Score",
                         round(dc.passivation_score, 2), "")
        result.add_param("debris.collision_avoidance_dv_per_year_ms", "Collision Avoidance ΔV/yr",
                         round(dc.collision_avoidance_dv_per_year_ms, 1), "m/s")
        result.add_param("debris.compliance_score", "Debris Compliance Score",
                         round(dc.debris_compliance_score, 0), "")
        result.add_param("debris.deorbit_method", "Deorbit Method",
                         dc.deorbit_method, "")

        result.warnings.extend(dc.warnings)

        # ---- Report-quality narrative & structured intermediates ----
        result.rationale = (
            f"Post-mission disposal: orbital lifetime {dc.lifetime_years:.1f} yr "
            f"with deorbit method '{dc.deorbit_method}'.  Casualty risk Ec="
            f"{dc.casualty_risk:.2e} ({'compliant' if dc.casualty_compliant else 'non-compliant'} "
            f"against 1e-4 threshold).  Passivation score {dc.passivation_score:.2f} "
            f"covers stored-energy depletion of battery and propellant tanks "
            f"per ISO 24113.  25-yr rule "
            f"{'satisfied' if dc.compliant_25yr else 'NOT satisfied'}; "
            f"5-yr rule {'satisfied' if dc.compliant_5yr else 'NOT satisfied'}."
        )
        result.assumptions = [
            "Atmospheric drag lifetime per NRLMSISE-00 / JR-1971 (mean solar flux).",
            "Casualty risk per NASA-STD-8719.14 demise model.",
            "Passivation score weighted by battery + propellant tank stored energy.",
            "Collision-avoidance ΔV budget assumed ~1 m/s per year in LEO.",
        ]
        result.extras["debris.compliance"] = {
            "lifetime_years": dc.lifetime_years,
            "compliant_25yr": bool(dc.compliant_25yr),
            "compliant_5yr": bool(dc.compliant_5yr),
            "casualty_risk": dc.casualty_risk,
            "casualty_compliant": bool(dc.casualty_compliant),
            "passivation_score": dc.passivation_score,
            "compliance_score": dc.debris_compliance_score,
            "method": dc.deorbit_method,
            "collision_avoidance_dv_per_year_ms": dc.collision_avoidance_dv_per_year_ms,
        }

        result.confidence = 0.75
        return result
