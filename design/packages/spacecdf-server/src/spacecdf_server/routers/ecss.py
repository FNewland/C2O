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

    params_dict, _, _ = await _get_design_state(study_id=study_id)

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
    elements: list[dict] = []
    mission_phases: list[dict] = []
    ground_stations: list[dict] = []
    equipment: list[dict] = []

    if study_id:
        study = store.get(study_id)
        if study:
            study_name = study.name
            phase_id = study.phase.value if hasattr(study.phase, "value") else str(study.phase)
            if hasattr(study, "mission_need") and study.mission_need:
                mn = study.mission_need
                mission_need = {
                    "problem_statement": getattr(mn, "problem_statement", ""),
                    "operational_context": getattr(mn, "operational_context", ""),
                    "objectives": [{"id": getattr(o, "id", ""), "text": o.text, "priority": o.priority, "type": getattr(o, "type", ""), "measurable_criterion": getattr(o, "measurable_criterion", "")} for o in getattr(mn, "objectives", [])],
                    "stakeholders": [{"name": s.name, "role": getattr(s, "role", ""), "needs": getattr(s, "needs", [])} for s in getattr(mn, "stakeholders", [])],
                }
            requirements = [
                {"id": r.id, "text": r.text, "domain": r.domain, "level": getattr(r, "level", "system"),
                 "category": getattr(r, "category", ""), "verification_method": r.verification_method.value,
                 "threshold": getattr(r, "threshold", None), "operator": getattr(r, "operator", ""),
                 "unit": getattr(r, "unit", ""), "objective_id": getattr(r, "objective_id", "")}
                for r in getattr(study, "requirements", [])
            ]

        # Load element tree and interfaces for this study
        from .elements import _elements, _interfaces
        elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
        interfaces = [i for i in _interfaces.values() if i.get("study_id") == study_id
                      and not i.get("deleted_at") and i.get("status") != "rejected"]
        equipment = [e for e in elements if e.get("element_type") == "component"]

    # Generate based on type — pass all available data (generators use **kwargs)
    _, gen_fn = DID_TYPES[did_type]
    common = dict(study_name=study_name, phase_id=phase_id)

    if did_type == "mrd":
        return gen_fn(**common, mission_need=mission_need, requirements=requirements)
    elif did_type == "ts":
        return gen_fn(**common, requirements=requirements, design_params=design_params,
                       mission_phases=mission_phases, interfaces=interfaces)
    elif did_type == "ird":
        return gen_fn(**common, interfaces=interfaces, elements=elements)
    elif did_type == "semp":
        # Use the enriched SEMP generator if available
        try:
            from ..services.semp_generator import generate_semp as gen_semp_full
            # Build study_data from available info
            study_data: dict = {
                "requirements": {"name": study_name},
                "mission_need": mission_need,
                "generated_requirements": requirements,
                "parameters": design_params,
            }
            return gen_semp_full(study_data=study_data, semp_answers={})
        except Exception:
            return gen_fn(**common)
    elif did_type == "rmp":
        return gen_fn(**common, parameters=design_params)
    elif did_type == "conops":
        return gen_fn(**common, mission_need=mission_need, conops=conops,
                       ground_stations=ground_stations)
    elif did_type == "test_plan":
        return gen_fn(**common, requirements=requirements, equipment=equipment)
    else:
        raise HTTPException(status_code=400, detail=f"Generator not implemented for {did_type}")


@router.get("/gates")
async def list_review_gates() -> list[dict]:
    """Review gates configured in ``configs/gate_exit_criteria.yaml``."""
    from ..services.gate_evaluator import list_gate_options
    return list_gate_options()


async def _evaluate_gate_for_study(study_id: str, phase_id: str, body: dict | None = None) -> dict:
    """Shared by the GET and POST gate-evaluate routes.

    ``phase_id`` is a phase id (``phase_b1``) or a gate name (``pdr``).
    ``body`` (POST only) may carry the client's current ``mission_need`` and
    ``parameters`` ({id: number | {value: number}}); they take precedence over
    the stored study, so the gate reflects what the user is looking at.
    """
    from ..services.gate_evaluator import evaluate_gate, resolve_phase
    from .elements import _elements, _interfaces
    from .requirements import _requirements, ensure_requirements_loaded

    if resolve_phase(phase_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown review gate: {phase_id}")

    body = body or {}
    study = get_study_store().get(study_id)

    mission_need = body.get("mission_need")
    target_mass = target_cost = rel_target = None
    params: dict = {}
    if study:
        if mission_need is None:
            mission_need = getattr(study, "mission_need", None)
        reqs_model = getattr(study, "requirements", None)
        if reqs_model is not None:
            target_mass = getattr(reqs_model, "target_mass_kg", None)
            target_cost = getattr(reqs_model, "target_cost_meur", None)
            rel_target = getattr(reqs_model, "reliability_target", None)
        iterations = getattr(study, "iterations", None) or []
        if iterations:
            params.update(iterations[-1].parameter_snapshot or {})
    if isinstance(body.get("parameters"), dict):
        params.update(body["parameters"])

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    params["_elements"] = elements
    params["_element_count"] = len(elements)
    params["_component_count"] = len([e for e in elements if e.get("element_type") == "component"])
    params["_frozen_count"] = len([e for e in elements if e.get("frozen")])

    try:
        await ensure_requirements_loaded()
    except Exception:  # noqa: BLE001 — DB unavailable: evaluate with what is cached
        pass
    reqs = [r for r in _requirements.values() if r.get("study_id") == study_id]

    result = evaluate_gate(
        phase_id=phase_id,
        mission_need=mission_need,
        design_params=params,
        target_mass_kg=target_mass,
        target_cost_meur=target_cost,
        reliability_target=rel_target,
        requirements=reqs,
        elements=elements,
        interfaces=[i for i in _interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")],
    )
    result["study_id"] = study_id
    result["study_found"] = study is not None
    return result


@router.get("/gate-evaluate/{study_id}/{phase_id}")
async def evaluate_gate_endpoint(study_id: str, phase_id: str) -> dict:
    """Evaluate review gate exit criteria for a stored study."""
    return await _evaluate_gate_for_study(study_id, phase_id)


@router.post("/gate-evaluate/{study_id}/{phase_id}")
async def evaluate_gate_with_state(study_id: str, phase_id: str, body: dict | None = None) -> dict:
    """Evaluate review gate exit criteria using the client's current state."""
    return await _evaluate_gate_for_study(study_id, phase_id, body)
