"""SpaceCDF — Compliance artefact generator (Phase 5C).

Auto-generates ECSS deliverables that were previously tagged ``planned`` in
ecss_review_gates.yaml:

  - **Verification Plan (VP)** — ECSS-E-ST-10-02C Rev.1 Annex A
    Maps each requirement to verification method, responsible position,
    success criterion, and verification phase.

  - **ECSS Tailoring Matrix** — ECSS-S-ST-00-02C
    Lists every ECSS standard applicable to the study's archetype/phase and
    states applicability (full / partial / tailored out) with rationale.

Both artefacts are produced from the live design state, review-gate config,
and template metadata. Outputs are plain dicts suitable for JSON response
or serialisation to Markdown/YAML files under .compliance/.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from spacecdf_common.models.requirements import (
    Requirement,
    RequirementVerification,
    VerificationMethod,
    generate_requirements,
    verify_requirements,
)

from .ecss_gates import compliance_summary, get_phase_gate, list_phases

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ECSS standard catalogue — minimal set for tailoring matrix
# ---------------------------------------------------------------------------

# Each entry: (standard_id, title, domains, default_applicability)
# domains: engineering domains where this standard is relevant
_ECSS_CATALOGUE: list[tuple[str, str, list[str], str]] = [
    ("ECSS-E-ST-10C Rev.1",     "Space engineering — System engineering general requirements",   ["systems"],               "full"),
    ("ECSS-E-ST-10-02C Rev.1",  "Space engineering — Verification",                             ["systems"],               "full"),
    ("ECSS-E-ST-10-06C",        "Space engineering — Technical requirements specification",      ["systems"],               "full"),
    ("ECSS-E-ST-10-24C Rev.1",  "Space engineering — Interface management",                     ["systems"],               "partial"),
    ("ECSS-M-ST-10C Rev.1",     "Space project management — Project planning and implementation",["systems"],               "full"),
    ("ECSS-M-ST-40C Rev.1",     "Space project management — Configuration and information management", ["systems"],         "partial"),
    ("ECSS-M-ST-60C",           "Space project management — Cost and schedule management",       ["cost"],                  "partial"),
    ("ECSS-M-ST-80C",           "Space project management — Risk management",                    ["risk"],                  "full"),
    ("ECSS-E-ST-20C",           "Space engineering — Electrical and electronic",                 ["power"],                 "full"),
    ("ECSS-E-ST-31C",           "Space engineering — Thermal control general requirements",      ["thermal"],               "full"),
    ("ECSS-E-ST-32C Rev.1",     "Space engineering — Structural general requirements",           ["structures"],            "full"),
    ("ECSS-E-ST-33-01C Rev.1",  "Space engineering — Mechanisms",                                ["structures"],            "partial"),
    ("ECSS-E-ST-35C Rev.1",     "Space engineering — Propulsion general requirements",           ["propulsion"],            "partial"),
    ("ECSS-E-ST-50-05C Rev.2",  "Space engineering — Radio frequency and modulation",            ["link", "ttc"],           "full"),
    ("ECSS-E-ST-60-10C",        "Space engineering — Control engineering",                       ["aocs"],                  "full"),
    ("ECSS-E-ST-70-01C",        "Space engineering — On-board control procedures",               ["obdh"],                  "partial"),
    ("ECSS-E-ST-70C",           "Space engineering — Ground systems and operations",             ["mission"],               "partial"),
    ("ECSS-Q-ST-30-02C",        "Space product assurance — Failure modes, effects and criticality analysis (FMECA)", ["systems"], "partial"),
    ("ECSS-U-AS-10C Rev.2",     "Space sustainability — Space debris mitigation",                ["propulsion", "orbit"],   "full"),
    ("ECSS-E-TM-10-25A",        "Space engineering — Engineering design model data exchange",    ["systems"],               "partial"),
    ("ECSS-S-ST-00-01C Rev.2",  "ECSS system — Glossary of terms",                              ["systems"],               "full"),
]


# ---------------------------------------------------------------------------
# Verification Plan generator
# ---------------------------------------------------------------------------

def generate_verification_plan(
    *,
    requirements: list[Requirement],
    verifications: list[RequirementVerification],
    phase_id: str,
    study_name: str = "",
) -> dict[str, Any]:
    """Generate a Verification Plan document structure.

    Returns a dict with metadata + a list of verification items, each mapping a
    requirement to its verification approach.
    """
    ver_by_req = {v.requirement_id: v for v in verifications}

    gate = get_phase_gate(phase_id)
    gate_name = gate["gate_name"] if gate else phase_id

    items: list[dict[str, Any]] = []
    for req in requirements:
        v = ver_by_req.get(req.id)
        items.append({
            "requirement_id": req.id,
            "requirement_text": req.text,
            "domain": req.domain,
            "responsible_position": req.position or "systems_engineer",
            "verification_method": req.verification_method.value,
            "success_criterion": _derive_success_criterion(req),
            "verification_phase": _verification_phase(req, phase_id),
            "current_status": v.status.value if v else "not_verified",
            "current_margin_percent": round(v.margin_percent, 1) if v and v.margin_percent is not None else None,
            "notes": "",
        })

    return {
        "document": "Verification Plan",
        "standard": "ECSS-E-ST-10-02C Rev.1 Annex A",
        "study_name": study_name,
        "phase": phase_id,
        "gate": gate_name,
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_requirements": len(requirements),
        "items": items,
    }


def _derive_success_criterion(req: Requirement) -> str:
    """Auto-generate a success criterion string from requirement fields."""
    op_map = {"<=": "shall not exceed", ">=": "shall be at least", "==": "shall equal"}
    op_text = op_map.get(req.operator, f"shall satisfy {req.operator}")

    if req.threshold_max is not None:
        return f"Measured value shall be between {req.threshold} and {req.threshold_max} {req.unit}".strip()

    if req.threshold == 0 and req.operator == ">=":
        return "Positive margin shall be demonstrated"

    return f"Measured value {op_text} {req.threshold} {req.unit} with {req.margin_policy_percent}% margin".strip()


def _verification_phase(req: Requirement, current_phase: str) -> str:
    """Suggest when verification should occur based on method and current phase."""
    if req.verification_method == VerificationMethod.ANALYSIS:
        return current_phase
    if req.verification_method == VerificationMethod.TEST:
        return "phase_c"
    if req.verification_method == VerificationMethod.REVIEW:
        return current_phase
    if req.verification_method == VerificationMethod.INSPECTION:
        return "phase_d"
    return "phase_c"


# ---------------------------------------------------------------------------
# Tailoring Matrix generator
# ---------------------------------------------------------------------------

def generate_tailoring_matrix(
    *,
    applicable_ecss: list[str] | None = None,
    phase_id: str,
    domains_active: list[str] | None = None,
    study_name: str = "",
) -> dict[str, Any]:
    """Generate an ECSS Tailoring Matrix.

    For each standard in the catalogue, determines applicability based on:
    - Whether the standard is in the study's applicable_ecss list
    - Whether the standard's engineering domain is active in the design
    - The current project phase
    """
    applicable_set = set(applicable_ecss or [])
    active_domains = set(domains_active or [])

    entries: list[dict[str, Any]] = []
    for std_id, title, domains, default_app in _ECSS_CATALOGUE:
        # Determine applicability
        domain_relevant = not active_domains or bool(set(domains) & active_domains)
        explicitly_listed = std_id in applicable_set

        if explicitly_listed:
            applicability = "full"
            rationale = "Explicitly listed in study applicable standards"
        elif domain_relevant and default_app == "full":
            applicability = "full"
            rationale = f"Standard covers active domain(s): {', '.join(set(domains) & active_domains) if active_domains else ', '.join(domains)}"
        elif domain_relevant and default_app == "partial":
            applicability = "partial"
            rationale = f"Partially applicable to active domain(s): {', '.join(set(domains) & active_domains) if active_domains else ', '.join(domains)}"
        else:
            applicability = "tailored_out"
            rationale = f"Domain(s) {', '.join(domains)} not active in this design"

        entries.append({
            "standard_id": std_id,
            "title": title,
            "domains": domains,
            "applicability": applicability,
            "rationale": rationale,
            "tailoring_notes": "",
        })

    counts = {
        "full": sum(1 for e in entries if e["applicability"] == "full"),
        "partial": sum(1 for e in entries if e["applicability"] == "partial"),
        "tailored_out": sum(1 for e in entries if e["applicability"] == "tailored_out"),
    }

    return {
        "document": "ECSS Tailoring Matrix",
        "standard": "ECSS-S-ST-00-02C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_standards": len(entries),
        "counts": counts,
        "entries": entries,
    }


# ---------------------------------------------------------------------------
# Combined compliance package
# ---------------------------------------------------------------------------

def generate_compliance_package(
    *,
    study_name: str,
    phase_id: str,
    mission_req_dict: dict[str, Any],
    state_params: dict[str, Any],
    applicable_ecss: list[str] | None = None,
    domains_active: list[str] | None = None,
) -> dict[str, Any]:
    """Generate the full compliance package: VP + Tailoring Matrix + gate summary.

    This is the main entry point called by the compliance router.
    """
    # Generate requirements and verify them
    requirements = generate_requirements(mission_req_dict)
    verifications = verify_requirements(requirements, state_params)

    vp = generate_verification_plan(
        requirements=requirements,
        verifications=verifications,
        phase_id=phase_id,
        study_name=study_name,
    )

    tm = generate_tailoring_matrix(
        applicable_ecss=applicable_ecss,
        phase_id=phase_id,
        domains_active=domains_active,
        study_name=study_name,
    )

    gate_summary = compliance_summary(phase_id)

    return {
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "verification_plan": vp,
        "tailoring_matrix": tm,
        "gate_summary": gate_summary,
    }
