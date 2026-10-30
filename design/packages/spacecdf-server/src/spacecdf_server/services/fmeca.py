"""SpaceCDF — FMECA Service (SCDF-231/232/233).

Failure Modes, Effects, and Criticality Analysis for spacecraft subsystems.
Provides a default CubeSat failure catalogue, RPN computation, redundancy
suggestions, and effect propagation through subsystem graphs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class FailureMode:
    """A single failure mode entry in the FMECA table."""
    id: str
    component: str
    mode: str
    cause: str
    local_effect: str
    system_effect: str
    severity: int       # 1-5 (5 = catastrophic)
    occurrence: int     # 1-5 (5 = frequent)
    detection: int      # 1-5 (5 = undetectable)
    rpn: int = 0        # Risk Priority Number = severity * occurrence * detection
    mitigation: str = ""

    def __post_init__(self) -> None:
        if self.rpn == 0:
            self.rpn = self.severity * self.occurrence * self.detection


@dataclass
class FMECAResult:
    """Summary result of an FMECA analysis."""
    failure_modes: list[FailureMode]
    total_rpn: int = 0
    critical_count: int = 0
    top_risks: list[FailureMode] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.total_rpn == 0 and self.failure_modes:
            self.total_rpn = sum(fm.rpn for fm in self.failure_modes)
        if self.critical_count == 0 and self.failure_modes:
            self.critical_count = sum(
                1 for fm in self.failure_modes if fm.severity >= 4
            )
        if not self.top_risks and self.failure_modes:
            self.top_risks = sorted(
                self.failure_modes, key=lambda fm: fm.rpn, reverse=True
            )[:5]


# ---------------------------------------------------------------------------
# Default CubeSat Failure Mode Catalogue
# ---------------------------------------------------------------------------

_CUBESAT_CATALOGUE: list[FailureMode] = [
    # EPS
    FailureMode(
        id="EPS-001",
        component="EPS",
        mode="Battery cell internal short",
        cause="Manufacturing defect or radiation damage",
        local_effect="Cell voltage drop, thermal runaway risk",
        system_effect="Loss of power bus, mission loss",
        severity=5, occurrence=2, detection=3,
        mitigation="Cell-level fusing, thermal monitoring, redundant battery string",
    ),
    FailureMode(
        id="EPS-002",
        component="EPS",
        mode="Solar array deployment failure",
        cause="Mechanism cold-welding, harness snag",
        local_effect="Reduced power generation",
        system_effect="Degraded mission capability or loss",
        severity=4, occurrence=2, detection=4,
        mitigation="Redundant deployment actuators, ground testing in thermal-vac",
    ),
    # AOCS
    FailureMode(
        id="AOCS-001",
        component="AOCS",
        mode="Reaction wheel bearing failure",
        cause="Lubricant degradation, contamination",
        local_effect="Wheel speed instability or seizure",
        system_effect="Degraded pointing, possible loss of fine pointing",
        severity=3, occurrence=2, detection=2,
        mitigation="Redundant wheel (4th wheel), bearing heaters, speed monitoring",
    ),
    FailureMode(
        id="AOCS-002",
        component="AOCS",
        mode="Star tracker temporary blinding",
        cause="Sun/Earth/Moon in FOV",
        local_effect="Attitude determination gap",
        system_effect="Temporary loss of fine pointing",
        severity=2, occurrence=3, detection=1,
        mitigation="Baffle design, exclusion angle SW, gyro propagation during gaps",
    ),
    # TTC
    FailureMode(
        id="TTC-001",
        component="TTC",
        mode="Transponder failure",
        cause="Component degradation, radiation SEE",
        local_effect="Loss of uplink/downlink",
        system_effect="Loss of mission (no commanding)",
        severity=5, occurrence=1, detection=4,
        mitigation="Redundant transponder (cold spare), watchdog timer reset",
    ),
    FailureMode(
        id="TTC-002",
        component="TTC",
        mode="Antenna deployment failure",
        cause="Release mechanism malfunction",
        local_effect="Reduced RF gain",
        system_effect="Degraded link margin, potential loss of comm",
        severity=4, occurrence=2, detection=3,
        mitigation="Redundant release mechanism, low-gain backup antenna",
    ),
    # OBC
    FailureMode(
        id="OBC-001",
        component="OBC",
        mode="SEU-induced latchup",
        cause="Heavy ion or proton interaction",
        local_effect="Processor halt or anomalous state",
        system_effect="Temporary loss of control, safe mode entry",
        severity=3, occurrence=3, detection=2,
        mitigation="Latchup protection circuits, watchdog reset, EDAC memory",
    ),
    FailureMode(
        id="OBC-002",
        component="OBC",
        mode="Firmware corruption",
        cause="Radiation bit-flips in flash, failed upload",
        local_effect="Software crash or erroneous behaviour",
        system_effect="Loss of nominal ops, safe mode",
        severity=4, occurrence=2, detection=3,
        mitigation="Dual-bank firmware, CRC validation, bootloader fallback",
    ),
    # Thermal
    FailureMode(
        id="THM-001",
        component="Thermal",
        mode="Heater stuck-on",
        cause="Relay failure, SW command error",
        local_effect="Overheating of component",
        system_effect="Component damage, power drain",
        severity=3, occurrence=2, detection=2,
        mitigation="Thermostat backup, over-temperature SW limit, fuse",
    ),
    FailureMode(
        id="THM-002",
        component="Thermal",
        mode="Radiator surface degradation",
        cause="Atomic oxygen erosion, contamination",
        local_effect="Reduced thermal rejection",
        system_effect="Gradual temperature rise, shortened lifetime",
        severity=2, occurrence=3, detection=3,
        mitigation="Protected coatings, margin in thermal design, heater duty monitoring",
    ),
    # Structure
    FailureMode(
        id="STR-001",
        component="Structure",
        mode="Deployment mechanism jam",
        cause="Thermal distortion, debris, cold-welding",
        local_effect="Appendage not deployed",
        system_effect="Mission capability loss (payload/SA/antenna)",
        severity=4, occurrence=2, detection=4,
        mitigation="Redundant actuators, thermal soak testing, in-orbit bakeout",
    ),
]


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def get_failure_catalogue(
    spacecraft_class: str = "cubesat",
    subsystems: list[str] | None = None,
) -> list[FailureMode]:
    """Return failure mode catalogue filtered by spacecraft class and subsystems.

    Parameters
    ----------
    spacecraft_class : str
        Spacecraft class (currently only 'cubesat' has a built-in catalogue).
    subsystems : list[str] or None
        If provided, filter to only these subsystem components.

    Returns
    -------
    list[FailureMode]
    """
    if spacecraft_class.lower() in ("cubesat", "smallsat", "microsat"):
        catalogue = list(_CUBESAT_CATALOGUE)
    else:
        # Return full catalogue for unknown classes (extensible later)
        catalogue = list(_CUBESAT_CATALOGUE)

    if subsystems:
        # Normalize subsystem names for matching
        normalized = [s.upper() for s in subsystems]
        catalogue = [
            fm for fm in catalogue
            if fm.component.upper() in normalized
        ]

    return catalogue


def compute_rpn(failure_modes: list[FailureMode]) -> list[FailureMode]:
    """Recompute RPN for each failure mode and return sorted by RPN descending.

    Parameters
    ----------
    failure_modes : list[FailureMode]
        Input failure modes (RPN will be recalculated).

    Returns
    -------
    list[FailureMode]
        Same list with updated RPN values, sorted highest first.
    """
    for fm in failure_modes:
        fm.rpn = fm.severity * fm.occurrence * fm.detection
    return sorted(failure_modes, key=lambda fm: fm.rpn, reverse=True)


def analyze_redundancy(
    failure_modes: list[FailureMode],
    design_state: dict[str, Any] | None = None,
    rpn_threshold: int = 20,
) -> list[dict[str, Any]]:
    """Suggest redundancy improvements for high-RPN failure modes.

    Parameters
    ----------
    failure_modes : list[FailureMode]
        Analysed failure modes.
    design_state : dict or None
        Current design state (for checking existing redundancy).
    rpn_threshold : int
        Minimum RPN to trigger redundancy recommendation.

    Returns
    -------
    list[dict]
        Redundancy recommendations with rationale.
    """
    recommendations: list[dict[str, Any]] = []

    # Existing redundancy info from design state
    existing_redundancy: set[str] = set()
    if design_state and "redundancy" in design_state:
        existing_redundancy = set(design_state["redundancy"])

    for fm in failure_modes:
        if fm.rpn < rpn_threshold:
            continue

        # Skip if already has redundancy in design
        if fm.component.lower() in existing_redundancy:
            continue

        # Determine recommendation based on failure type
        rec: dict[str, Any] = {
            "failure_mode_id": fm.id,
            "component": fm.component,
            "current_rpn": fm.rpn,
            "recommendation": "",
            "expected_rpn_reduction": 0,
        }

        if fm.severity >= 4:
            rec["recommendation"] = (
                f"Add cold/hot redundancy for {fm.component} — "
                f"failure mode '{fm.mode}' has catastrophic/critical severity."
            )
            rec["expected_rpn_reduction"] = int(fm.rpn * 0.5)
        elif fm.occurrence >= 3:
            rec["recommendation"] = (
                f"Improve screening/derating for {fm.component} — "
                f"failure mode '{fm.mode}' has elevated occurrence."
            )
            rec["expected_rpn_reduction"] = int(fm.rpn * 0.3)
        else:
            rec["recommendation"] = (
                f"Enhance detection/monitoring for {fm.component} — "
                f"failure mode '{fm.mode}' is difficult to detect."
            )
            rec["expected_rpn_reduction"] = int(fm.rpn * 0.25)

        recommendations.append(rec)

    return recommendations


def propagate_effects(
    failure_mode: FailureMode,
    subsystem_graph: dict[str, list[str]] | None = None,
) -> list[dict[str, str]]:
    """Trace effect propagation from local to system level.

    Parameters
    ----------
    failure_mode : FailureMode
        The failure mode to propagate.
    subsystem_graph : dict or None
        Adjacency list of subsystem dependencies.
        E.g. {"EPS": ["OBC", "AOCS", "TTC", "Thermal", "Payload"]}

    Returns
    -------
    list[dict]
        Chain of effects from component to system level.
    """
    if subsystem_graph is None:
        # Default CubeSat dependency graph
        subsystem_graph = {
            "EPS": ["OBC", "AOCS", "TTC", "Thermal", "Payload"],
            "OBC": ["AOCS", "TTC", "Payload"],
            "AOCS": ["Payload"],
            "TTC": [],
            "Thermal": [],
            "Payload": [],
            "Structure": ["EPS", "AOCS", "TTC", "Payload"],
        }

    chain: list[dict[str, str]] = []

    # Level 0: local effect
    chain.append({
        "level": "local",
        "subsystem": failure_mode.component,
        "effect": failure_mode.local_effect,
    })

    # Level 1: direct dependents
    component_key = failure_mode.component
    dependents = subsystem_graph.get(component_key, [])

    for dep in dependents:
        chain.append({
            "level": "subsystem",
            "subsystem": dep,
            "effect": f"Degraded/lost {dep} function due to {component_key} failure",
        })

    # Level 2: system effect
    chain.append({
        "level": "system",
        "subsystem": "Mission",
        "effect": failure_mode.system_effect,
    })

    return chain


def run_fmeca(
    spacecraft_class: str = "cubesat",
    subsystems: list[str] | None = None,
    design_state: dict[str, Any] | None = None,
) -> FMECAResult:
    """Run a complete FMECA analysis.

    Parameters
    ----------
    spacecraft_class : str
        Spacecraft class for catalogue selection.
    subsystems : list[str] or None
        Subsystems to include (None = all).
    design_state : dict or None
        Current design state for redundancy analysis.

    Returns
    -------
    FMECAResult
    """
    catalogue = get_failure_catalogue(spacecraft_class, subsystems)
    ranked = compute_rpn(catalogue)

    return FMECAResult(
        failure_modes=ranked,
        total_rpn=sum(fm.rpn for fm in ranked),
        critical_count=sum(1 for fm in ranked if fm.severity >= 4),
        top_risks=ranked[:5],
    )
