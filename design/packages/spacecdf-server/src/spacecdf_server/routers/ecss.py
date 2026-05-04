"""SpaceCDF — ECSS compliance API.

Exposes the ECSS review-gate deliverable expectations to the frontend so
that the Compliance Panel can show, for a given study phase, which DRDs
are expected at the next review gate and which SpaceCDF currently covers.

Reference sources (via ~/.claude/skills/ecss-standards/):
  - ECSS-E-ST-10C Rev.1 Annex A (Table A-1, informative)
  - ECSS-M-ST-10C Rev.1 (project phase / review-gate structure)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..services.ecss_gates import compliance_summary, list_phases
from ..services.did_generator import list_available_dids, DID_TYPES
from ..services.ecss_margin_enforcer import enforce_ecss_margins
from .studies import get_study_store

router = APIRouter()


@router.get("/phases")
async def get_phases() -> list[str]:
    """Return the list of configured phase ids (phase_0, phase_a, ...)."""
    return list_phases()


@router.get("/compliance/{phase_id}")
async def get_phase_compliance(phase_id: str) -> dict:
    """Return the expected DRDs + SpaceCDF coverage for a given phase."""
    summary = compliance_summary(phase_id)
    if not summary.get("found"):
        raise HTTPException(status_code=404, detail=f"Unknown phase: {phase_id}")
    return summary


@router.get("/margins/{study_id}")
async def check_margins(study_id: str) -> dict:
    """Enforce ECSS margin philosophy against current design state.

    Checks mass, power, link, thermal, and ΔV margins against the
    phase-appropriate ECSS policy values.
    """
    from .engineering import _get_design_state

    _, params_dict, _ = await _get_design_state(study_id=study_id)

    store = get_study_store()
    study = store.get(study_id)
    phase_id = "phase_a"
    if study:
        phase_id = study.phase.value if hasattr(study.phase, "value") else str(study.phase)

    report = enforce_ecss_margins(params_dict, phase_id)

    return {
        "study_id": study_id,
        "phase": report.phase,
        "compliant": report.compliant,
        "critical_count": report.critical_count,
        "major_count": report.major_count,
        "total_checks": len(report.checks),
        "checks": [
            {
                "domain": c.domain,
                "standard": c.standard,
                "parameter": c.parameter,
                "required_margin": c.required_margin,
                "actual_margin": round(c.actual_margin, 2),
                "unit": c.unit,
                "severity": c.severity,
                "message": c.message,
            }
            for c in report.checks
        ],
        "violations": [
            {
                "domain": v.domain,
                "standard": v.standard,
                "parameter": v.parameter,
                "required_margin": v.required_margin,
                "actual_margin": round(v.actual_margin, 2),
                "unit": v.unit,
                "severity": v.severity,
                "message": v.message,
            }
            for v in report.violations
        ],
    }


@router.get("/compliance/by-study/{study_id}")
async def get_study_compliance(study_id: str) -> dict:
    """Return DRD compliance for the phase of the named study.

    Convenience endpoint — the frontend doesn't need to know the study's
    current phase; it just asks "what does this study owe at its next gate?"
    """
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    # StudyPhase is a str Enum, so .value is the config key (phase_0, phase_a, phase_b1)
    phase_id = study.phase.value if hasattr(study.phase, "value") else str(study.phase)
    summary = compliance_summary(phase_id)
    summary["study_id"] = study_id
    summary["study_name"] = study.name
    return summary


@router.get("/dids")
async def get_available_dids() -> list[dict]:
    """List all available DID (Document Item Description) templates."""
    return list_available_dids()


@router.post("/dids/{did_type}/generate")
async def generate_did(did_type: str, study_id: str | None = None) -> dict:
    """Generate an ECSS DID document from the current study state."""
    if did_type not in DID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown DID type: {did_type}. Available: {list(DID_TYPES.keys())}",
        )

    store = get_study_store()
    study = None
    study_name = "Unnamed Mission"
    phase_id = "phase_a"
    mission_need: dict = {}
    requirements: list[dict] = []
    design_params: dict = {}
    interfaces: list[dict] = []
    conops: dict = {}

    if study_id:
        study = store.get(study_id)
        if study:
            study_name = study.name
            phase_id = study.phase.value if hasattr(study.phase, "value") else str(study.phase)
            if hasattr(study, "mission_need") and study.mission_need:
                mn = study.mission_need
                mission_need = {
                    "problem_statement": getattr(mn, "problem_statement", ""),
                    "objectives": [{"text": o.text, "priority": o.priority, "measurable_criterion": getattr(o, "measurable_criterion", "")} for o in getattr(mn, "objectives", [])],
                    "stakeholders": [{"name": s.name, "role": getattr(s, "role", "")} for s in getattr(mn, "stakeholders", [])],
                }
            requirements = [
                {"id": r.id, "text": r.text, "domain": r.domain, "category": getattr(r, "category", ""), "verification_method": r.verification_method.value}
                for r in getattr(study, "requirements", [])
            ]

    # Generate based on type
    _, gen_fn = DID_TYPES[did_type]

    if did_type == "mrd":
        return gen_fn(study_name=study_name, mission_need=mission_need, requirements=requirements, phase_id=phase_id)
    elif did_type == "ts":
        return gen_fn(study_name=study_name, requirements=requirements, design_params=design_params, phase_id=phase_id)
    elif did_type == "ird":
        return gen_fn(study_name=study_name, interfaces=interfaces, phase_id=phase_id)
    elif did_type == "semp":
        return gen_fn(study_name=study_name, phase_id=phase_id)
    elif did_type == "rmp":
        return gen_fn(study_name=study_name, phase_id=phase_id)
    elif did_type == "conops":
        return gen_fn(study_name=study_name, mission_need=mission_need, conops=conops, phase_id=phase_id)
    elif did_type == "test_plan":
        return gen_fn(study_name=study_name, requirements=requirements, phase_id=phase_id)
    else:
        raise HTTPException(status_code=400, detail=f"Generator not implemented for {did_type}")
