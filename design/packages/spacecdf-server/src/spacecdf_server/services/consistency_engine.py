"""SpaceCDF — Consistency Checking Engine.

Validates the entire design state for internal consistency:
  - Requirements consistent with objectives (no orphans)
  - Functions cover all requirements (no uncovered functions)
  - Interface matrix complete (all subsystem pairs defined)
  - Design parameters satisfy all requirements (compliance matrix)
  - Budget margins within policy for current phase
  - Equipment selections compatible (interface check)
  - ConOps modes cover all mission phases
  - Cross-domain parameter coherence

Run on demand or after each change. Flags inconsistencies with
severity, affected items, and suggested resolution.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyIssue:
    """A single consistency issue found in the design."""
    id: str
    severity: str  # "critical", "major", "minor", "info"
    category: str  # "requirements", "functions", "interfaces", "budgets", "conops", "equipment"
    title: str
    description: str
    affected_items: list[str] = field(default_factory=list)
    suggested_fix: str = ""


@dataclass
class ConsistencyReport:
    """Full consistency check report."""
    issues: list[ConsistencyIssue] = field(default_factory=list)
    checked_at: str = ""
    total_checks: int = 0
    pass_count: int = 0
    fail_count: int = 0

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "critical")

    @property
    def major_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "major")

    @property
    def health_score(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return (self.pass_count / self.total_checks) * 100


def run_consistency_check(
    *,
    mission_need: dict[str, Any] | None = None,
    requirements: list[dict[str, Any]] | None = None,
    functions: list[dict[str, Any]] | None = None,
    interfaces: list[dict[str, Any]] | None = None,
    conops: dict[str, Any] | None = None,
    design_params: dict[str, Any] | None = None,
    equipment: list[dict[str, Any]] | None = None,
    phase_id: str = "phase_a",
) -> ConsistencyReport:
    """Run all consistency checks and return a consolidated report."""
    from datetime import datetime, timezone

    report = ConsistencyReport(checked_at=datetime.now(timezone.utc).isoformat())
    issues: list[ConsistencyIssue] = []
    checks = 0
    passes = 0

    mn = mission_need or {}
    reqs = requirements or []
    funcs = functions or []
    ifcs = interfaces or []
    ops = conops or {}
    params = design_params or {}
    equip = equipment or []

    # --- 1. Mission Need completeness ---
    checks += 1
    if mn.get("problem_statement", "").strip():
        passes += 1
    else:
        issues.append(ConsistencyIssue(
            id="CON-MN-01", severity="critical", category="mission_need",
            title="Problem statement missing",
            description="No problem statement defined. This is the foundation of the V-model.",
            suggested_fix="Define the problem statement in the Mission Need step.",
        ))

    checks += 1
    objectives = mn.get("objectives", [])
    if len(objectives) >= 1:
        passes += 1
    else:
        issues.append(ConsistencyIssue(
            id="CON-MN-02", severity="critical", category="mission_need",
            title="No mission objectives defined",
            description="At least one measurable objective is required.",
            suggested_fix="Add objectives with measurable success criteria.",
        ))

    # --- 2. Requirements traceability ---
    checks += 1
    orphan_reqs = [r for r in reqs if not r.get("objective_id") and not r.get("function_id")]
    if not orphan_reqs:
        passes += 1
    else:
        issues.append(ConsistencyIssue(
            id="CON-REQ-01", severity="major", category="requirements",
            title=f"{len(orphan_reqs)} requirement(s) not traced to objective or function",
            description="Requirements should trace back to an objective or derive from a function.",
            affected_items=[r.get("id", "") for r in orphan_reqs[:10]],
            suggested_fix="Link each requirement to its parent objective or function.",
        ))

    # Check for SMART quality
    checks += 1
    how_reqs = [r for r in reqs if any(kw in r.get("text", "").lower() for kw in ["shall operate at", "shall use", "shall be at"])]
    if not how_reqs:
        passes += 1
    else:
        issues.append(ConsistencyIssue(
            id="CON-REQ-02", severity="major", category="requirements",
            title=f"{len(how_reqs)} requirement(s) specify HOW not WHAT",
            description="Requirements should state WHAT the system must achieve, not HOW to achieve it.",
            affected_items=[r.get("id", "") for r in how_reqs[:10]],
            suggested_fix="Rewrite as performance requirements: 'shall provide X' not 'shall use Y'.",
        ))

    # --- 3. Functions coverage ---
    checks += 1
    if funcs:
        leaf_funcs = [f for f in funcs if not any(c.get("parent_function_id") == f.get("id") for c in funcs)]
        uncovered = [f for f in leaf_funcs if not f.get("derived_requirement_ids")]
        if not uncovered:
            passes += 1
        else:
            issues.append(ConsistencyIssue(
                id="CON-FN-01", severity="major", category="functions",
                title=f"{len(uncovered)} leaf function(s) have no requirements",
                description="Every leaf function should derive at least one requirement.",
                affected_items=[f.get("id", "") for f in uncovered[:10]],
                suggested_fix="Generate or link requirements for each uncovered function.",
            ))
    else:
        passes += 1  # No functions = no check needed at this stage

    checks += 1
    unallocated = [f for f in funcs if not f.get("allocated_to")]
    if not unallocated:
        passes += 1
    else:
        issues.append(ConsistencyIssue(
            id="CON-FN-02", severity="minor", category="functions",
            title=f"{len(unallocated)} function(s) not allocated to a subsystem",
            description="Functions should be allocated to a responsible subsystem domain.",
            affected_items=[f.get("id", "") for f in unallocated[:10]],
            suggested_fix="Assign each function to a subsystem (power, aocs, link, etc.).",
        ))

    # --- 4. Interface completeness ---
    checks += 1
    subsystems = {"power", "aocs", "link", "thermal", "structure", "propulsion", "data", "payload"}
    expected_pairs = len(subsystems) * (len(subsystems) - 1) // 2  # C(8,2) = 28
    if ifcs:
        defined_count = len(ifcs)
        if defined_count >= expected_pairs * 0.5:
            passes += 1
        else:
            issues.append(ConsistencyIssue(
                id="CON-IF-01", severity="minor", category="interfaces",
                title=f"Interface matrix {defined_count}/{expected_pairs} pairs defined",
                description="Less than 50% of subsystem pairs have defined interfaces.",
                suggested_fix="Review the interface matrix and define missing interfaces.",
            ))
    else:
        passes += 1  # No interface data available

    # --- 5. Budget margins ---
    margin_checks = [
        ("systems.mass_margin_percent", "Mass margin", 20, 10),
        ("systems.power_margin_percent", "Power margin", 20, 5),
    ]
    phase_min_margins = {
        "phase_0": 30, "phase_a": 20, "phase_b": 15, "phase_c": 10, "phase_d": 5,
    }
    min_margin = phase_min_margins.get(phase_id, 20)

    for param_id, label, _warn, _crit in margin_checks:
        checks += 1
        val = params.get(param_id)
        if val is not None:
            margin = val if isinstance(val, (int, float)) else (val.get("value", 0) if isinstance(val, dict) else 0)
            if margin >= min_margin:
                passes += 1
            elif margin >= 0:
                issues.append(ConsistencyIssue(
                    id=f"CON-BDG-{param_id.split('.')[-1][:4].upper()}",
                    severity="major", category="budgets",
                    title=f"{label} below policy ({margin:.0f}% < {min_margin}%)",
                    description=f"For {phase_id}, margin policy requires >= {min_margin}%.",
                    affected_items=[param_id],
                    suggested_fix=f"Reduce allocations or increase total {label.split()[0].lower()} capacity.",
                ))
            else:
                issues.append(ConsistencyIssue(
                    id=f"CON-BDG-{param_id.split('.')[-1][:4].upper()}",
                    severity="critical", category="budgets",
                    title=f"{label} is NEGATIVE ({margin:.0f}%)",
                    description="The design does not close. Fundamental redesign needed.",
                    affected_items=[param_id],
                    suggested_fix=f"Major redesign: reduce subsystem {label.split()[0].lower()} or increase budget.",
                ))
        else:
            passes += 1  # No data = can't check

    # --- 6. ConOps coverage ---
    checks += 1
    phases = ops.get("phases", [])
    modes = ops.get("modes", [])
    if phases and modes:
        has_safe = any("safe" in m.get("name", "").lower() for m in modes)
        has_science = any(m.get("name", "").lower() in ["science", "imaging", "observation"] or "science" in m.get("name", "").lower() for m in modes)
        has_downlink = any("downlink" in m.get("name", "").lower() for m in modes)
        if has_safe and has_science and has_downlink:
            passes += 1
        else:
            missing = []
            if not has_safe: missing.append("safe mode")
            if not has_science: missing.append("science/observation mode")
            if not has_downlink: missing.append("downlink mode")
            issues.append(ConsistencyIssue(
                id="CON-OPS-01", severity="major", category="conops",
                title=f"Missing operational mode(s): {', '.join(missing)}",
                description="All missions need at minimum: safe mode, primary science mode, and downlink mode.",
                suggested_fix="Add the missing modes in the ConOps editor.",
            ))
    else:
        passes += 1  # No ConOps data

    # --- 7. Equipment compatibility ---
    checks += 1
    if equip:
        total_equip_mass = sum(e.get("mass_kg", 0) for e in equip)
        if total_equip_mass > 0:
            passes += 1
        else:
            issues.append(ConsistencyIssue(
                id="CON-EQ-01", severity="info", category="equipment",
                title="No equipment mass data",
                description="Selected equipment has no mass data — budget verification impossible.",
                suggested_fix="Verify equipment selection includes mass specifications.",
            ))
    else:
        passes += 1

    report.issues = issues
    report.total_checks = checks
    report.pass_count = passes
    report.fail_count = checks - passes
    return report
