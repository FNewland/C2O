"""SpaceCDF — Compliance artefact API (Phase 5C).

Endpoints:
    GET  /api/compliance/{study_id}                — full compliance package (VP + TM + gate)
    GET  /api/compliance/{study_id}/verification    — Verification Plan only
    GET  /api/compliance/{study_id}/tailoring        — Tailoring Matrix only
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .studies import get_study_store
from .exports import _run_design_for_study
from ..services.compliance_generator import (
    generate_compliance_package,
    generate_tailoring_matrix,
    generate_verification_plan,
)
from spacecdf_common.models.requirements import generate_requirements, verify_requirements

router = APIRouter()


def _study_metadata(study_id: str) -> tuple:
    """Retrieve study + resolve phase, applicable ECSS, and active domains."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    phase_id = study.phase.value if hasattr(study.phase, "value") else str(study.phase)

    # Pull applicable ECSS from template when the study was seeded from one
    applicable_ecss: list[str] = []
    notes = getattr(study, "notes", "") or ""
    if "Seeded from template:" in notes:
        tmpl_id = notes.split("Seeded from template:")[1].strip().split()[0]
        try:
            from ..services.template_library import get_template
            tmpl = get_template(tmpl_id)
            if tmpl:
                applicable_ecss = list(tmpl.applicable_ecss)
        except Exception:
            pass

    return study, phase_id, applicable_ecss


@router.get("/{study_id}")
async def get_compliance_package(study_id: str) -> dict:
    """Generate full compliance package: VP + Tailoring Matrix + gate summary."""
    study, phase_id, applicable_ecss = _study_metadata(study_id)
    state, requirements, _ = await _run_design_for_study(study_id)

    # Detect active domains from converged parameters
    domains_active = list({
        pid.split(".")[0] for pid in state.parameters if "." in pid
    })

    return generate_compliance_package(
        study_name=study.name,
        phase_id=phase_id,
        mission_req_dict=study.requirements.model_dump(),
        state_params=state.parameters,
        applicable_ecss=applicable_ecss,
        domains_active=domains_active,
    )


@router.get("/{study_id}/verification")
async def get_verification_plan(study_id: str) -> dict:
    """Generate the Verification Plan for this study."""
    study, phase_id, _ = _study_metadata(study_id)
    state, requirements_obj, _ = await _run_design_for_study(study_id)

    reqs = generate_requirements(study.requirements.model_dump())
    verifications = verify_requirements(reqs, state.parameters)

    return generate_verification_plan(
        requirements=reqs,
        verifications=verifications,
        phase_id=phase_id,
        study_name=study.name,
    )


@router.get("/{study_id}/tailoring")
async def get_tailoring_matrix(study_id: str) -> dict:
    """Generate the ECSS Tailoring Matrix for this study."""
    study, phase_id, applicable_ecss = _study_metadata(study_id)
    state, _, _ = await _run_design_for_study(study_id)

    domains_active = list({
        pid.split(".")[0] for pid in state.parameters if "." in pid
    })

    return generate_tailoring_matrix(
        applicable_ecss=applicable_ecss,
        phase_id=phase_id,
        domains_active=domains_active,
        study_name=study.name,
    )
