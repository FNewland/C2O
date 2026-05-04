"""SpaceCDF — Requirement Engine.

Generates SMART requirements that say WHAT not HOW, validates them,
supports the suggest-then-approve pattern, and checks for non-compliance.

Requirement types per ECSS-E-ST-10C / NASA SEH:
  - Mission: WHAT the system must achieve (from objectives)
    "The system shall provide 10m GSD multispectral imagery"
  - System: WHAT with measurable threshold (from functions)
    "The communication link shall close with ≥ 3 dB margin"
  - Subsystem: WHAT allocated to a subsystem (from system reqs)
    "The EPS shall provide positive power margin in all operating modes"
  - Interface: HOW — pinned down tightly (from interface matrix)
    "The EPS shall provide 28V ± 2V regulated power via PC/104 connector"

SMART validation:
  S — Specific (not vague)
  M — Measurable (has a threshold value)
  A — Achievable (within the class performance envelope)
  R — Relevant (traces to an objective)
  T — Traceable (has objective_id and function_id)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SMARTCheck:
    """Result of SMART validation for a single requirement."""
    requirement_id: str
    specific: bool = False
    measurable: bool = False
    achievable: bool = False
    relevant: bool = False
    traceable: bool = False
    issues: list[str] = field(default_factory=list)
    is_smart: bool = False
    is_how_not_what: bool = False  # Flags if req describes HOW instead of WHAT


@dataclass
class SuggestedRequirement:
    """A requirement suggested by the tool, pending user approval."""
    id: str
    text: str
    req_type: str            # mission / system / subsystem / interface
    domain: str
    threshold: float = 0
    operator: str = ">="
    unit: str = ""
    verification_method: str = "analysis"
    objective_id: str = ""
    function_id: str = ""
    rationale: str = ""
    status: str = "suggested"  # suggested / accepted / edited / rejected


# Words that indicate a requirement describes HOW rather than WHAT
_HOW_INDICATORS = [
    "shall operate at",
    "shall use",
    "shall be located",
    "shall orbit at",
    "shall fly",
    "shall be built",
    "shall employ",
    "shall be made of",
    "shall be manufactured",
    "shall be deployed from",
    "shall launch on",
]

# Words that indicate a WHAT requirement (good)
_WHAT_INDICATORS = [
    "shall provide",
    "shall achieve",
    "shall support",
    "shall maintain",
    "shall withstand",
    "shall survive",
    "shall enable",
    "shall allow",
    "shall detect",
    "shall measure",
    "shall transmit",
    "shall receive",
    "shall store",
    "shall process",
    "shall protect",
]


def generate_smart_requirements(
    objectives: list[dict[str, Any]],
    mission_requirements_dict: dict[str, Any],
    functions: list[dict[str, Any]] | None = None,
) -> list[SuggestedRequirement]:
    """Generate SMART requirements from objectives and functions.

    Unlike the old generate_requirements() which worked from orbit/payload
    specs (describing HOW), this generates from objectives (describing WHAT).
    """
    suggestions: list[SuggestedRequirement] = []
    counter = 0
    functions = functions or []

    # === Mission-level requirements (from objectives) ===
    for obj in objectives:
        obj_id = obj.get("id", "")
        obj_text = obj.get("text", "")
        criterion = obj.get("measurable_criterion", "")
        priority = obj.get("priority", "primary")

        if not obj_text:
            continue

        counter += 1
        # Generate a WHAT requirement from each objective
        req_text = _objective_to_requirement(obj_text, criterion)

        suggestions.append(SuggestedRequirement(
            id=f"REQ-MIS-{counter:03d}",
            text=req_text,
            req_type="mission",
            domain="systems",
            threshold=_extract_threshold(criterion),
            operator=_extract_operator(criterion),
            unit=_extract_unit(criterion),
            verification_method="analysis",
            objective_id=obj_id,
            rationale=f"Derived from {priority} objective: {obj_text}",
        ))

    # === System-level requirements (from mission req constraints) ===
    mr = mission_requirements_dict

    # Lifetime — this is a WHAT
    if mr.get("design_lifetime_years"):
        counter += 1
        suggestions.append(SuggestedRequirement(
            id=f"REQ-SYS-{counter:03d}",
            text=f"The system shall have a design lifetime of at least {mr['design_lifetime_years']} years",
            req_type="system", domain="systems",
            threshold=mr["design_lifetime_years"], operator=">=", unit="years",
            verification_method="analysis",
            rationale="From mission lifetime requirement",
        ))

    # Mass constraint (if target set) — this is a WHAT (performance boundary)
    if mr.get("target_mass_kg"):
        counter += 1
        suggestions.append(SuggestedRequirement(
            id=f"REQ-SYS-{counter:03d}",
            text=f"The total spacecraft launch mass shall not exceed {mr['target_mass_kg']} kg",
            req_type="system", domain="mass",
            threshold=mr["target_mass_kg"], operator="<=", unit="kg",
            verification_method="test",
            rationale="From mass allocation constraint",
        ))

    # Cost constraint
    if mr.get("target_cost_meur"):
        counter += 1
        suggestions.append(SuggestedRequirement(
            id=f"REQ-SYS-{counter:03d}",
            text=f"The total mission cost shall not exceed {mr['target_cost_meur']} MEUR",
            req_type="system", domain="cost",
            threshold=mr["target_cost_meur"], operator="<=", unit="MEUR",
            verification_method="analysis",
            rationale="From programmatic cost ceiling",
        ))

    # === Subsystem-level requirements (from functions) ===
    for func in functions:
        if not func.get("performance_criteria"):
            continue
        func_id = func.get("id", "")
        domain = func.get("allocated_to", "")
        for criterion in func.get("performance_criteria", []):
            counter += 1
            suggestions.append(SuggestedRequirement(
                id=f"REQ-{domain.upper()[:3] or 'SUB'}-{counter:03d}",
                text=f"The {domain or 'system'} shall {criterion}",
                req_type="subsystem", domain=domain,
                threshold=_extract_threshold(criterion),
                operator=_extract_operator(criterion),
                unit=_extract_unit(criterion),
                verification_method="analysis" if "margin" in criterion.lower() or "accuracy" in criterion.lower() else "test",
                function_id=func_id,
                objective_id=func.get("objective_ids", [""])[0] if func.get("objective_ids") else "",
                rationale=f"Derived from function: {func.get('name', '')}",
            ))

    # === Standard requirements every mission needs ===
    standard_reqs = [
        ("The communication link shall close with at least 3 dB margin at minimum elevation", "link", 3.0, ">=", "dB", "analysis"),
        ("The EPS shall provide positive power margin in all operating modes including eclipse", "power", 0, ">=", "W", "analysis"),
        ("The system shall comply with space debris mitigation requirements per applicable regulations", "systems", 0, ">=", "", "analysis"),
    ]
    for text, domain, threshold, op, unit, method in standard_reqs:
        counter += 1
        suggestions.append(SuggestedRequirement(
            id=f"REQ-STD-{counter:03d}",
            text=text, req_type="system", domain=domain,
            threshold=threshold, operator=op, unit=unit,
            verification_method=method,
            rationale="Standard requirement for all space missions",
        ))

    # Deorbit requirement (if applicable)
    orbit = mr.get("orbit", {})
    if orbit.get("deorbit_required", True) and orbit.get("orbit_type") not in ("lunar", "interplanetary"):
        counter += 1
        suggestions.append(SuggestedRequirement(
            id=f"REQ-STD-{counter:03d}",
            text="The system shall be capable of disposal within 25 years of end-of-mission per space debris mitigation guidelines",
            req_type="system", domain="propulsion",
            threshold=25, operator="<=", unit="years",
            verification_method="analysis",
            rationale="ECSS-U-AS-10C / ITU / national regulations",
        ))

    return suggestions


def validate_smart(req: dict[str, Any]) -> SMARTCheck:
    """Validate a requirement against SMART criteria.

    S — Specific: not vague, uses "shall"
    M — Measurable: has a threshold value or clear pass/fail criterion
    A — Achievable: (simplified — check if threshold is within reason)
    R — Relevant: traces to an objective
    T — Traceable: has objective_id
    """
    check = SMARTCheck(requirement_id=req.get("id", ""))
    text = req.get("text", "")
    issues: list[str] = []

    # Specific
    if "shall" in text.lower() and len(text) > 20:
        check.specific = True
    else:
        issues.append("Not specific: requirement should use 'shall' and be detailed")

    # Measurable
    threshold = req.get("threshold")
    if threshold is not None and (isinstance(threshold, (int, float)) and threshold != 0):
        check.measurable = True
    elif req.get("operator") and req.get("unit"):
        check.measurable = True
    else:
        issues.append("Not measurable: add a threshold value with operator and unit")

    # Achievable (simplified — just check it's not obviously impossible)
    check.achievable = True  # Would need class envelope check in production

    # Relevant
    if req.get("objective_id") or req.get("rationale"):
        check.relevant = True
    else:
        issues.append("Not relevant: should trace to an objective or have a rationale")

    # Traceable
    if req.get("objective_id") or req.get("function_id") or req.get("mission_need_id"):
        check.traceable = True
    else:
        issues.append("Not traceable: should link to an objective or function")

    # Check HOW vs WHAT
    text_lower = text.lower()
    req_type = req.get("req_type", "system")
    if req_type != "interface":  # Interface reqs ARE allowed to be specific HOW
        for indicator in _HOW_INDICATORS:
            if indicator in text_lower:
                check.is_how_not_what = True
                issues.append(f"Describes HOW not WHAT: '{indicator}' — rephrase to describe the capability needed, not the implementation")
                break

    check.issues = issues
    check.is_smart = check.specific and check.measurable and check.relevant and check.traceable and not check.is_how_not_what

    return check


def check_non_compliance(
    requirement: dict[str, Any],
    achieved_value: float | None,
    margin_percent: float | None,
) -> dict[str, Any]:
    """Check if a requirement is non-compliant and generate resolution options."""
    threshold = requirement.get("threshold", 0)
    operator = requirement.get("operator", ">=")
    req_id = requirement.get("id", "")
    domain = requirement.get("domain", "")

    is_compliant = True
    if margin_percent is not None and margin_percent < 0:
        is_compliant = False
    elif achieved_value is not None and threshold:
        if operator == ">=" and achieved_value < threshold:
            is_compliant = False
        elif operator == "<=" and achieved_value > threshold:
            is_compliant = False

    if is_compliant:
        return {"requirement_id": req_id, "compliant": True, "options": []}

    # Generate resolution options
    options = [
        {
            "id": "change_design",
            "label": "Change design to meet requirement",
            "description": f"Modify the {domain} subsystem design to achieve {operator} {threshold} {requirement.get('unit', '')}",
            "effort": "medium",
            "needs_approval": False,
        },
        {
            "id": "relax_requirement",
            "label": "Relax the requirement threshold",
            "description": f"Change threshold from {threshold} to a value the design can meet. Requires stakeholder approval if this is a mission-level requirement.",
            "effort": "low",
            "needs_approval": True,
        },
        {
            "id": "accept_risk",
            "label": "Accept as design risk",
            "description": "Document the non-compliance, assess the impact, and accept the risk at programme level.",
            "effort": "low",
            "needs_approval": True,
        },
        {
            "id": "escalate",
            "label": "Escalate to systems engineer",
            "description": "This non-compliance may have cross-domain implications. Escalate for trade study.",
            "effort": "high",
            "needs_approval": False,
        },
    ]

    return {
        "requirement_id": req_id,
        "requirement_text": requirement.get("text", ""),
        "compliant": False,
        "achieved_value": achieved_value,
        "threshold": threshold,
        "operator": operator,
        "margin_percent": margin_percent,
        "options": options,
    }


def _objective_to_requirement(obj_text: str, criterion: str) -> str:
    """Convert an objective statement into a WHAT requirement."""
    # If criterion has measurable value, incorporate it
    if criterion:
        return f"The system shall {obj_text.lower().rstrip('.')} ({criterion})"
    return f"The system shall {obj_text.lower().rstrip('.')}"


def _extract_threshold(text: str) -> float:
    """Extract numeric threshold from criterion text."""
    import re
    match = re.search(r'[<>=]+\s*([\d.]+)', text)
    if match:
        return float(match.group(1))
    match = re.search(r'([\d.]+)\s*[a-zA-Z]', text)
    if match:
        return float(match.group(1))
    return 0.0


def _extract_operator(text: str) -> str:
    import re
    match = re.search(r'([<>]=?|=)', text)
    return match.group(1) if match else ">="


def _extract_unit(text: str) -> str:
    import re
    match = re.search(r'[\d.]+\s*([a-zA-Z/%°]+)', text)
    return match.group(1) if match else ""
