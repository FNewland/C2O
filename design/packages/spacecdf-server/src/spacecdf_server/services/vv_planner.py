"""V&V Plan Generator — requirement-to-test protocol mapping (SCDF-241/242).

Per ECSS-E-ST-10-02C. Maps each requirement to a verification method,
test level, test phase, and (optionally) facility assignment.

Generates a verification plan document structure with:
- Verification matrix (requirement → method → phase → evidence)
- Test programme sequence
- Facility allocation recommendations
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerificationEntry:
    """One row in the verification matrix."""
    requirement_id: str
    requirement_text: str
    method: str  # A (analysis), T (test), I (inspection), R (review), D (demonstration)
    level: str  # unit, subsystem, system, acceptance, qualification
    phase: str  # PDR, CDR, QR, AR
    facility: str | None = None  # e.g., "TVAC chamber", "vibration table"
    status: str = "planned"  # planned, scheduled, passed, failed, waived
    evidence: str | None = None


@dataclass
class TestProtocol:
    """A specific test procedure."""
    id: str
    name: str
    environment: str  # thermal, vibration, EMC, functional, deployment
    level: str  # qualification, acceptance, protoflight
    requirements_covered: list[str] = field(default_factory=list)
    duration_hours: float = 4.0
    facility_type: str = "clean_room"
    pass_criteria: str = ""


@dataclass
class VVPlanResult:
    """Full V&V plan output."""
    verification_matrix: list[VerificationEntry] = field(default_factory=list)
    test_protocols: list[TestProtocol] = field(default_factory=list)
    test_sequence: list[str] = field(default_factory=list)
    facility_summary: dict[str, int] = field(default_factory=dict)  # facility_type → count of tests
    coverage_pct: float = 0.0
    warnings: list[str] = field(default_factory=list)


# Standard test environments per ECSS-E-ST-10-03C
STANDARD_TESTS = [
    TestProtocol(id="T-001", name="Incoming Inspection", environment="visual", level="acceptance", duration_hours=2, facility_type="clean_room", pass_criteria="No visible damage, all connectors seated"),
    TestProtocol(id="T-002", name="Functional Test (Baseline)", environment="functional", level="acceptance", duration_hours=8, facility_type="clean_room", pass_criteria="All subsystems nominal per test procedure"),
    TestProtocol(id="T-003", name="Sine Vibration", environment="vibration", level="qualification", duration_hours=4, facility_type="shaker_table", pass_criteria="No resonance shift >5%, no anomalies"),
    TestProtocol(id="T-004", name="Random Vibration", environment="vibration", level="qualification", duration_hours=4, facility_type="shaker_table", pass_criteria="RMS within spec, no loose hardware"),
    TestProtocol(id="T-005", name="Thermal Vacuum", environment="thermal", level="qualification", duration_hours=48, facility_type="tvac_chamber", pass_criteria="All temps within range, functional OK at extremes"),
    TestProtocol(id="T-006", name="Thermal Cycling", environment="thermal", level="acceptance", duration_hours=24, facility_type="thermal_chamber", pass_criteria="8 cycles, functional baseline maintained"),
    TestProtocol(id="T-007", name="EMC/EMI", environment="emc", level="qualification", duration_hours=8, facility_type="anechoic_chamber", pass_criteria="Emissions within ECSS-E-ST-20-07C limits"),
    TestProtocol(id="T-008", name="Deployment Test", environment="deployment", level="qualification", duration_hours=4, facility_type="deployment_rig", pass_criteria="100+ successful actuations"),
    TestProtocol(id="T-009", name="Mass Properties", environment="mechanical", level="acceptance", duration_hours=2, facility_type="balance_fixture", pass_criteria="CoM within allocation"),
    TestProtocol(id="T-010", name="Final Functional Test", environment="functional", level="acceptance", duration_hours=8, facility_type="clean_room", pass_criteria="Identical to baseline; no degradation"),
]

# Standard test sequence per ECSS
STANDARD_SEQUENCE = [
    "T-001", "T-002", "T-003", "T-004", "T-002",  # Vibe → re-test
    "T-005", "T-002", "T-007", "T-008", "T-009", "T-010",  # TVAC → EMC → deploy → final
]

# Method assignment heuristics
METHOD_RULES: dict[str, str] = {
    "mass": "T",  # Mass requirements → test (weigh it)
    "power": "T",  # Power → test (measure it)
    "link": "A",  # Link margin → analysis (link budget)
    "pointing": "T",  # Pointing → test (measure on ADCS test bench)
    "thermal": "A",  # Thermal → analysis (model) + test confirmation
    "cost": "A",  # Cost → analysis (accounting)
    "systems": "A",  # System-level → analysis
    "structure": "T",  # Structural → test (vibration)
    "propulsion": "T",  # Propulsion → test (leak, functional)
}


def generate_vv_plan(
    requirements: list[dict[str, Any]],
    spacecraft_class: str = "nano",
) -> VVPlanResult:
    """Generate a V&V plan from accepted requirements.

    Args:
        requirements: List of requirements with id, text, domain, verification_method.
        spacecraft_class: nano/micro/small — affects test levels.

    Returns:
        VVPlanResult with verification matrix, test protocols, and sequence.
    """
    result = VVPlanResult()

    # Build verification matrix
    for req in requirements:
        domain = req.get("domain", "systems")
        method = req.get("verification_method") or METHOD_RULES.get(domain, "A")
        level = "system" if req.get("level") == "mission" else "subsystem"
        phase = "CDR" if method == "T" else "PDR"

        entry = VerificationEntry(
            requirement_id=req.get("id", ""),
            requirement_text=req.get("text", "")[:100],
            method=method.upper()[0] if method else "A",
            level=level,
            phase=phase,
            facility=_assign_facility(method, domain),
        )
        result.verification_matrix.append(entry)

    # Assign test protocols
    result.test_protocols = list(STANDARD_TESTS)
    result.test_sequence = list(STANDARD_SEQUENCE)

    # Map requirements to test protocols
    for entry in result.verification_matrix:
        if entry.method == "T":
            # Find matching test protocol
            for proto in result.test_protocols:
                if _method_matches_protocol(entry, proto):
                    proto.requirements_covered.append(entry.requirement_id)
                    break

    # Facility summary
    for proto in result.test_protocols:
        ft = proto.facility_type
        result.facility_summary[ft] = result.facility_summary.get(ft, 0) + 1

    # Coverage
    total_reqs = len(requirements)
    covered = len([e for e in result.verification_matrix if e.method in ("T", "A", "I", "D")])
    result.coverage_pct = (covered / total_reqs * 100) if total_reqs > 0 else 0

    # Warnings
    untested = [e for e in result.verification_matrix if e.method not in ("T", "A", "I", "D", "R")]
    if untested:
        result.warnings.append(f"{len(untested)} requirements have no assigned verification method")

    return result


def _assign_facility(method: str, domain: str) -> str | None:
    """Assign a facility based on verification method and domain."""
    if method.upper().startswith("T"):
        facility_map = {
            "structure": "shaker_table",
            "thermal": "tvac_chamber",
            "power": "clean_room",
            "link": "anechoic_chamber",
            "pointing": "aocs_test_bench",
            "propulsion": "propulsion_lab",
        }
        return facility_map.get(domain, "clean_room")
    return None


def _method_matches_protocol(entry: VerificationEntry, proto: TestProtocol) -> bool:
    """Check if a verification entry matches a test protocol."""
    domain_to_env = {
        "structure": "vibration",
        "thermal": "thermal",
        "power": "functional",
        "link": "emc",
        "pointing": "functional",
    }
    # Simple matching by domain → environment
    return domain_to_env.get(entry.requirement_id.split("-")[1].lower() if "-" in entry.requirement_id else "", "") == proto.environment
