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


async def _interface_requirements(study_id: str | None) -> list[dict]:
    """Requirements of level ``interface`` (design rules IF-01), not retired."""
    if not study_id:
        return []
    from .requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    return [r for r in _requirements.values() if r.get("study_id") == study_id
            and r.get("level") == "interface" and r.get("status") != "retired"]


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
    risks: list[dict] = []

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
            from .exports.docx import conops_dict
            conops = conops_dict(study)
            mission_phases = list(conops.get("phases") or [])

        # W1.09f: the requirement store, the risk register, the ConOps and the ground stations of
        # the study, through the export collector (study.requirements is the mission definition,
        # not a list, so the old read always gave 0 requirements).
        from ..services.export_context import collect
        try:
            sx = await collect(study_id, sections=("elements", "requirements", "risks", "modes"))
        except LookupError:
            sx = None
        if sx is not None:
            names = {e.get("id"): e for e in (sx.elements or {}).get("items") or []}
            for r in (sx.requirements or {}).get("items") or []:
                el = names.get(r.get("element_id")) or {}
                requirements.append({
                    "id": r.get("code") or r.get("id"), "text": r.get("text") or "",
                    "domain": el.get("subsystem_domain") or r.get("req_type") or "",
                    "level": r.get("level") or "system", "category": r.get("req_type") or "",
                    "verification_method": r.get("verification_method") or "",
                    "threshold": r.get("threshold_value"), "operator": r.get("threshold_op") or "",
                    "unit": r.get("unit") or "", "objective_id": r.get("objective_id") or "",
                    "rationale": r.get("rationale") or "", "allocated_to": el.get("name") or "",
                })
            risks = list((sx.risks or {}).get("items") or [])
            elements = list((sx.elements or {}).get("items") or [])
            interfaces = list((sx.elements or {}).get("interfaces") or [])
            for e in elements:
                perf = e.get("performance") if isinstance(e.get("performance"), dict) else {}
                if e.get("subsystem_domain") == "ground" and (perf.get("lat") is not None or perf.get("latitude") is not None):
                    ground_stations.append({"name": e.get("name"), "latitude": perf.get("lat", perf.get("latitude")),
                                            "longitude": perf.get("lon", perf.get("longitude")),
                                            "bands": perf.get("bands") or [], "antenna_m": perf.get("antenna_m")})
            equipment = [e for e in elements if e.get("element_type") == "component"]
            # the Modes tab (the team's mode set) wins over the auto-generated ConOps modes
            mset = sx.modes or {}
            if mset.get("modes"):
                pw = {m.get("mode_id"): m for m in ((mset.get("energy") or {}).get("modes") or [])}
                conops = {**conops, "modes": [
                    {"name": m.get("name"), "mode_type": m.get("kind") or "", "description": m.get("description") or "",
                     "power_w": (pw.get(m.get("id")) or {}).get("power_cbe_w"), "pointing": m.get("pointing"),
                     "duty_cycle_percent": round(float(m.get("orbit_fraction") or 0) * 100, 1),
                     "sunlit_only": bool(m.get("sunlit_only"))} for m in mset["modes"]]}
            conops.setdefault("ground_stations", ground_stations)

    # Generate based on type — pass all available data (generators use **kwargs)
    _, gen_fn = DID_TYPES[did_type]
    common = dict(study_name=study_name, phase_id=phase_id)

    if did_type == "mrd":
        return gen_fn(**common, mission_need=mission_need, requirements=requirements)
    elif did_type == "ts":
        return gen_fn(**common, requirements=requirements, design_params=design_params,
                       mission_phases=mission_phases, interfaces=interfaces)
    elif did_type == "ird":
        return gen_fn(**common, interfaces=interfaces, elements=elements,
                      interface_requirements=await _interface_requirements(study_id))
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
                # F6: the model's interfaces and interface requirements, not estimates
                "model_interfaces": [i for i in interfaces if i.get("status") == "accepted"],
                "interface_requirements": await _interface_requirements(study_id),
            }
            return gen_semp_full(study_data=study_data, semp_answers={})
        except Exception:
            return gen_fn(**common)
    elif did_type == "rmp":
        return gen_fn(**common, risks=risks, parameters=design_params)
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
    """Shared by the GET and POST gate-evaluate routes: one *canonical* gate (MDR, PRR, SRR,
    PDR; ``mcr`` = MDR) evaluated from the stored study only.

    Nov 2026 (WP0): the POST body is ignored. Before, the client's ``mission_need`` and
    ``parameters`` took precedence over the stored study, and the V&V panel sent the empty
    legacy store, so the MDR always failed "Problem statement is empty" (walkthrough top
    problem 2). The profile-aware checklist is GET /api/studies/{id}/rules/gates/{gate}.
    """
    from ..services.gate_evaluator import evaluate_gate, resolve_phase
    from .gates import gate_inputs

    if resolve_phase(phase_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown review gate: {phase_id}")

    try:
        ctx = await gate_inputs(study_id)
    except HTTPException:
        ctx = {"study": None, "elements": [], "interfaces": [], "requirements": [], "params": {},
               "function_count": 0, "risks": []}
    study = ctx["study"]
    reqs_model = getattr(study, "requirements", None) if study else None
    params = dict(ctx["params"])
    elements = ctx["elements"]
    params["_elements"] = elements
    params["_element_count"] = len(elements)
    params["_component_count"] = len([e for e in elements if e.get("element_type") == "component"])
    params["_frozen_count"] = len([e for e in elements if e.get("frozen")])

    result = evaluate_gate(
        phase_id=phase_id,
        mission_need=getattr(study, "mission_need", None) if study else None,
        design_params=params,
        target_mass_kg=getattr(reqs_model, "target_mass_kg", None) if reqs_model else None,
        target_cost_meur=getattr(reqs_model, "target_cost_meur", None) if reqs_model else None,
        reliability_target=getattr(reqs_model, "reliability_target", None) if reqs_model else None,
        requirements=ctx["requirements"],
        elements=elements,
        interfaces=ctx["interfaces"],
        mission=reqs_model,
        function_count=ctx.get("function_count"),
        risks=ctx.get("risks"),
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
    """Kept for old clients: same as GET (the body is ignored; server state only)."""
    return await _evaluate_gate_for_study(study_id, phase_id, body)
