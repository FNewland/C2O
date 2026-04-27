"""SpaceCDF — Reliability Model Agent (Tier 2).

FMECA-lite: per-subsystem failure rates from heritage data, series/parallel
reliability model, single-point failure identification, and redundancy
recommendations.

References:
  - ECSS-Q-ST-30-02C — FMECA
  - MIL-HDBK-217F — Reliability prediction of electronic equipment
  - Wertz, SMAD4 §19.1 — Reliability and quality assurance
"""
from __future__ import annotations

import math

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


# Heritage failure rates (failures per 10^6 hours) by subsystem
# Source: SMAD4 Table 19-5, MIL-HDBK-217F, industry heritage data
_FAILURE_RATES: dict[str, float] = {
    "eps":        2.5,    # Power system (SA + battery + PCDU)
    "aocs":       3.0,    # AOCS (wheels + sensors + electronics)
    "ttc":        1.5,    # Communications
    "obdh":       2.0,    # On-board computer
    "tcs":        0.5,    # Thermal (mostly passive — low failure rate)
    "propulsion": 4.0,    # Propulsion (valves, thrusters)
    "structure":  0.1,    # Structure (very low — no moving parts)
    "payload":    3.0,    # Instrument (generic)
}

# Redundancy effectiveness: reduces failure rate by this factor
_REDUNDANCY_FACTOR = 0.15  # ~85% reduction for hot redundant pair


class ReliabilityAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "reliability"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return ["mission.duration_years"]

    def output_parameters(self) -> list[str]:
        return [
            "reliability.mission_reliability",
            "reliability.weakest_subsystem",
            "reliability.single_point_failures",
            "reliability.mtbf_hours",
        ]

    def dependencies(self) -> list[str]:
        return ["mass"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        mission_years = state.get("mission.duration_years", 3.0) or 3.0
        mission_hours = mission_years * 365.25 * 24

        reliability_target = state.get_requirement("reliability_target") or 0.9

        # Compute per-subsystem reliability: R = exp(-λt)
        subsystem_reliabilities: dict[str, float] = {}
        single_point_failures: list[str] = []
        weakest = ("", 1.0)

        for sub, failure_rate in _FAILURE_RATES.items():
            # Check if subsystem has any mass (i.e., exists in design)
            mass_param = {
                "eps": "power.eps_mass_kg", "aocs": "aocs.mass_kg",
                "ttc": "link.ttc_mass_kg", "obdh": "data.obdh_mass_kg",
                "tcs": "thermal.tcs_mass_kg", "propulsion": "propulsion.total_mass_kg",
                "structure": "structure.mass_kg", "payload": "mass.payload_kg",
            }.get(sub)

            mass = state.get(mass_param, 0) if mass_param else 0
            if not mass or mass <= 0:
                subsystem_reliabilities[sub] = 1.0
                continue

            lambda_per_hour = failure_rate / 1e6
            r_sub = math.exp(-lambda_per_hour * mission_hours)
            subsystem_reliabilities[sub] = r_sub

            if r_sub < weakest[1]:
                weakest = (sub, r_sub)

            # Single-point failure: if subsystem reliability < 0.95 and no redundancy
            # (We don't model redundancy explicitly yet — flag everything below threshold)
            if r_sub < 0.95:
                single_point_failures.append(f"{sub} (R={r_sub:.3f})")

        # System reliability (series model — all must work)
        system_reliability = 1.0
        for r in subsystem_reliabilities.values():
            system_reliability *= r

        # MTBF
        total_lambda = sum(fr / 1e6 for fr in _FAILURE_RATES.values())
        mtbf_hours = 1.0 / total_lambda if total_lambda > 0 else float("inf")

        result.add_param("reliability.mission_reliability", "Mission Reliability",
                         round(system_reliability, 4), "")
        result.add_param("reliability.weakest_subsystem", "Weakest Subsystem",
                         weakest[0] if weakest[0] else "none", "")
        result.add_param("reliability.single_point_failures", "Single-Point Failures",
                         len(single_point_failures), "")
        result.add_param("reliability.mtbf_hours", "System MTBF",
                         round(mtbf_hours, 0), "hours")

        if system_reliability < reliability_target:
            result.add_warning(
                f"Mission reliability {system_reliability:.3f} < target {reliability_target:.2f}; "
                f"weakest: {weakest[0]} (R={weakest[1]:.3f}). Consider redundancy."
            )
        if single_point_failures:
            result.add_warning(f"Single-point failures: {', '.join(single_point_failures)}")

        result.confidence = 0.60
        return result
