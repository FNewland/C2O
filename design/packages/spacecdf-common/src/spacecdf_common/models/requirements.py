"""SpaceCDF — Requirement Verification data models.

Formal traceability: Mission Requirement → System Requirement →
Design Parameter → Component Specification.

Supports auto-generation of requirements from MissionRequirements,
evaluation against design state, and worst-case analysis.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    PERFORMANCE = "performance"
    CONSTRAINT = "constraint"
    FUNCTIONAL = "functional"
    INTERFACE = "interface"
    ENVIRONMENTAL = "environmental"


class VerificationMethod(str, Enum):
    ANALYSIS = "analysis"
    TEST = "test"
    INSPECTION = "inspection"
    REVIEW = "review"
    DEMONSTRATION = "demonstration"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"           # Margin >= policy
    MARGINAL = "marginal"             # 0% <= margin < policy
    NON_COMPLIANT = "non_compliant"   # Margin < 0%
    NOT_VERIFIED = "not_verified"     # No data yet


class Requirement(BaseModel):
    """A formal design requirement with traceability to design parameters."""

    id: str = Field(description="Unique ID, e.g. 'REQ-PWR-001'")
    text: str = Field(description="Requirement statement in 'shall' form")
    req_type: RequirementType = RequirementType.PERFORMANCE
    parent_id: str | None = Field(default=None, description="Parent requirement ID for flow-down")
    source: str = Field(default="mission", description="Where this requirement comes from")
    verification_method: VerificationMethod = VerificationMethod.ANALYSIS
    parameter_ids: list[str] = Field(default_factory=list, description="Design parameters that satisfy this")
    threshold: float = Field(description="Threshold value for compliance")
    threshold_max: float | None = Field(default=None, description="Upper bound for range requirements")
    operator: str = Field(default="<=", description="Comparison: >=, <=, ==, range")
    unit: str = Field(default="")
    margin_policy_percent: float = Field(default=20.0, description="Required margin (20% Phase 0, 10% Phase B)")
    domain: str = Field(default="", description="Engineering domain this requirement belongs to")
    position: str = Field(default="", description="Position responsible for verification")
    rationale: str = Field(default="", description="Why this requirement exists")
    # System-V traceability — links to MissionNeed hierarchy
    mission_need_id: str | None = Field(default=None, description="Traces to the mission need this derives from")
    objective_id: str | None = Field(default=None, description="Traces to the objective this implements")


class RequirementVerification(BaseModel):
    """Verification result for a single requirement against the current design."""

    requirement_id: str
    requirement_text: str
    achieved_value: float | None = None
    margin_percent: float | None = None
    status: ComplianceStatus = ComplianceStatus.NOT_VERIFIED
    worst_case_value: float | None = None
    worst_case_margin_percent: float | None = None
    worst_case_status: ComplianceStatus | None = None
    component_limit: float | None = Field(default=None, description="Operating limit from selected equipment")
    component_limit_margin_percent: float | None = None
    notes: str = ""


class ComplianceMatrix(BaseModel):
    """Full compliance matrix for a design study."""

    requirements: list[Requirement] = Field(default_factory=list)
    verifications: list[RequirementVerification] = Field(default_factory=list)

    @property
    def total_requirements(self) -> int:
        return len(self.requirements)

    @property
    def compliant_count(self) -> int:
        return sum(1 for v in self.verifications if v.status == ComplianceStatus.COMPLIANT)

    @property
    def marginal_count(self) -> int:
        return sum(1 for v in self.verifications if v.status == ComplianceStatus.MARGINAL)

    @property
    def non_compliant_count(self) -> int:
        return sum(1 for v in self.verifications if v.status == ComplianceStatus.NON_COMPLIANT)

    @property
    def compliance_percent(self) -> float:
        verified = [v for v in self.verifications if v.status != ComplianceStatus.NOT_VERIFIED]
        if not verified:
            return 0.0
        return (self.compliant_count / len(verified)) * 100


# --- Auto-generation from MissionRequirements ---

def generate_requirements(mission_req: dict) -> list[Requirement]:
    """Auto-generate formal requirements from MissionRequirements fields.

    Maps mission-level parameters to 'shall' statements with thresholds.
    """
    reqs: list[Requirement] = []
    req_counter = {"SYS": 0, "ORB": 0, "PWR": 0, "AOCS": 0, "TCS": 0, "TTC": 0, "DATA": 0, "PROP": 0, "PL": 0}

    def _next_id(prefix: str) -> str:
        req_counter[prefix] = req_counter.get(prefix, 0) + 1
        return f"REQ-{prefix}-{req_counter[prefix]:03d}"

    # Orbit requirements
    orbit = mission_req.get("orbit", {})
    if orbit.get("altitude_km"):
        reqs.append(Requirement(
            id=_next_id("ORB"),
            text=f"The spacecraft shall operate at an orbital altitude of {orbit['altitude_km']} km",
            req_type=RequirementType.PERFORMANCE,
            parameter_ids=["orbit.altitude_km"],
            threshold=orbit["altitude_km"],
            operator="==",
            unit="km",
            domain="orbit",
            position="mission_analyst",
            margin_policy_percent=2.0,  # Orbit altitude has tight tolerance
        ))

    if orbit.get("mission_duration_years"):
        reqs.append(Requirement(
            id=_next_id("SYS"),
            text=f"The spacecraft shall have a design lifetime of at least {orbit['mission_duration_years']} years",
            req_type=RequirementType.CONSTRAINT,
            parameter_ids=["mission.duration_years"],
            threshold=orbit["mission_duration_years"],
            operator=">=",
            unit="years",
            domain="systems",
            position="systems_engineer",
        ))

    # Mass requirement
    if mission_req.get("target_mass_kg"):
        reqs.append(Requirement(
            id=_next_id("SYS"),
            text=f"The spacecraft wet mass shall not exceed {mission_req['target_mass_kg']} kg",
            req_type=RequirementType.CONSTRAINT,
            parameter_ids=["mass.wet_mass_kg"],
            threshold=mission_req["target_mass_kg"],
            operator="<=",
            unit="kg",
            domain="mass",
            position="systems_engineer",
        ))

    # Cost requirement
    if mission_req.get("target_cost_meur"):
        reqs.append(Requirement(
            id=_next_id("SYS"),
            text=f"The total mission cost shall not exceed {mission_req['target_cost_meur']} MEUR",
            req_type=RequirementType.CONSTRAINT,
            parameter_ids=["cost.total_meur"],
            threshold=mission_req["target_cost_meur"],
            operator="<=",
            unit="MEUR",
            domain="cost",
            position="cost_engineer",
        ))

    # Payload requirements
    for i, payload in enumerate(mission_req.get("payloads", [])):
        pl_name = payload.get("name", f"Payload {i}")

        if payload.get("pointing_accuracy_deg"):
            reqs.append(Requirement(
                id=_next_id("AOCS"),
                text=f"The spacecraft shall provide pointing accuracy of {payload['pointing_accuracy_deg']}° or better for {pl_name}",
                req_type=RequirementType.PERFORMANCE,
                parameter_ids=["aocs.pointing_accuracy_deg"],
                threshold=payload["pointing_accuracy_deg"],
                operator="<=",
                unit="deg",
                domain="aocs",
                position="aocs_engineer",
            ))

        if payload.get("data_rate_mbps"):
            reqs.append(Requirement(
                id=_next_id("DATA"),
                text=f"The communication system shall support downlink of {pl_name} data at {payload['data_rate_mbps']} Mbps or equivalent daily volume",
                req_type=RequirementType.PERFORMANCE,
                parameter_ids=["data.generated_per_day_gb", "data.downlinked_per_day_gb"],
                threshold=0,  # Checked as data_downlinked >= data_generated
                operator=">=",
                unit="GB/day",
                domain="data",
                position="comms_engineer",
                rationale="Payload data must be fully downlinked within 24 hours",
            ))

    # Power requirements
    reqs.append(Requirement(
        id=_next_id("PWR"),
        text="The EPS shall provide positive power margin in all operating modes including eclipse",
        req_type=RequirementType.PERFORMANCE,
        parameter_ids=["power.sa_power_eol_w", "power.total_sunlight_w"],
        threshold=0,
        operator=">=",
        unit="W",
        domain="power",
        position="power_engineer",
        rationale="SA EOL power must exceed total demand with margin",
    ))

    # Link budget requirement
    reqs.append(Requirement(
        id=_next_id("TTC"),
        text="The communication link shall close with at least 3 dB margin at minimum elevation",
        req_type=RequirementType.PERFORMANCE,
        parameter_ids=["link.downlink_margin_db"],
        threshold=3.0,
        operator=">=",
        unit="dB",
        domain="link",
        position="comms_engineer",
    ))

    # Deorbit requirement
    if orbit.get("deorbit_required", True):
        reqs.append(Requirement(
            id=_next_id("SYS"),
            text="The spacecraft shall be capable of deorbiting within 25 years of end-of-mission per space debris mitigation guidelines",
            req_type=RequirementType.CONSTRAINT,
            parameter_ids=["orbit.delta_v_deorbit_ms"],
            threshold=0,
            operator=">=",
            unit="m/s",
            domain="propulsion",
            position="propulsion_engineer",
        ))

    return reqs


def verify_requirements(
    requirements: list[Requirement],
    state_params: dict[str, Any],
    margin_policy_override: float | None = None,
) -> list[RequirementVerification]:
    """Evaluate each requirement against the current design state."""
    verifications = []

    for req in requirements:
        verification = RequirementVerification(
            requirement_id=req.id,
            requirement_text=req.text,
        )

        policy = margin_policy_override or req.margin_policy_percent

        # Get achieved values
        values = []
        for pid in req.parameter_ids:
            p = state_params.get(pid)
            if p is not None:
                val = p.value if hasattr(p, "value") else (p.get("value") if isinstance(p, dict) else p)
                if isinstance(val, (int, float)):
                    values.append(val)

        if not values:
            verification.status = ComplianceStatus.NOT_VERIFIED
            verification.notes = "No parameter data available"
            verifications.append(verification)
            continue

        achieved = values[0]  # Primary parameter
        verification.achieved_value = achieved

        # Special case: data budget (check generated <= downlinked)
        if len(values) >= 2 and req.operator == ">=" and req.domain == "data":
            generated = values[0]
            downlinked = values[1]
            if generated > 0:
                margin = ((downlinked - generated) / generated) * 100
                verification.margin_percent = margin
            else:
                margin = 100
                verification.margin_percent = margin
        elif req.operator == "<=":
            if req.threshold > 0:
                margin = ((req.threshold - achieved) / req.threshold) * 100
            else:
                margin = 100 if achieved <= 0 else -100
            verification.margin_percent = margin
        elif req.operator == ">=":
            if req.threshold > 0:
                margin = ((achieved - req.threshold) / req.threshold) * 100
            else:
                margin = 100 if achieved >= 0 else -100
            verification.margin_percent = margin
        elif req.operator == "==":
            if req.threshold > 0:
                margin = 100 - abs((achieved - req.threshold) / req.threshold) * 100
            else:
                margin = 100 if achieved == 0 else 0
            verification.margin_percent = margin
        else:
            verification.margin_percent = 0

        # Determine compliance status
        if verification.margin_percent is not None:
            if verification.margin_percent >= policy:
                verification.status = ComplianceStatus.COMPLIANT
            elif verification.margin_percent >= 0:
                verification.status = ComplianceStatus.MARGINAL
            else:
                verification.status = ComplianceStatus.NON_COMPLIANT

        verifications.append(verification)

    return verifications
