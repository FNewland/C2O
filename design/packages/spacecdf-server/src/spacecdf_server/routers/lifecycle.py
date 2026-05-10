"""SpaceCDF — Lifecycle Services API.

Endpoints for all specialist services: harness design, ground segment,
test procedures, launch planning, BOM generation, fit-gap analysis,
ground segment trade study, and engineering budgets.

These connect the previously-orphaned utility services to the frontend.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .studies import get_study_store
from .exports import _run_design_for_study
from ..services.harness_designer import design_harness, harness_summary
from ..services.ground_configurator import generate_mcs_config, generate_pass_predictions, generate_ops_timeline
from ..services.test_generator import generate_test_procedures, generate_environmental_test_specs
from ..services.launch_planner import check_launch_compatibility, generate_campaign_timeline, generate_regulatory_checklist
from ..services.bom_generator import generate_bom, generate_bom_from_elements, bom_to_csv, bom_to_svg_table
from ..services.fit_gap_analysis import analyze_component_fit, analyze_category
from ..services.ground_segment_trade import compute_ground_segment_trade
from ..services.orbit_trade import compute_orbit_trade
from ..services.class_advisor import advise_mission_class
from ..services.traceability import trace_budget_to_need
from ..services.session_guidance import recommend_next_session
from ..services.mission_trade import compute_mission_trade
from ..services.example_missions import list_example_missions, get_example_mission

router = APIRouter()


# --- Example Missions ---

@router.get("/example-missions")
async def list_examples() -> dict:
    """Return a summary list of pre-loaded example missions."""
    return {"missions": list_example_missions()}


@router.get("/example-missions/{mission_id}")
async def get_example(mission_id: str) -> dict:
    """Return full mission data for a pre-loaded example."""
    mission = get_example_mission(mission_id)
    if not mission:
        raise HTTPException(404, f"Example mission '{mission_id}' not found")
    return mission


# --- Harness Design ---

class HarnessRequest(BaseModel):
    selected_components: dict[str, dict[str, Any]]
    form_factor: str = "3U"

@router.post("/harness")
async def design_harness_endpoint(req: HarnessRequest) -> dict:
    """Generate harness design from selected components."""
    harness = design_harness(req.selected_components, req.form_factor)
    return harness_summary(harness)


# --- Ground Segment ---

@router.get("/ground/trade/{study_id}")
async def ground_segment_trade_endpoint(study_id: str) -> dict:
    """Compute ground segment architecture trade for a study."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")
    return compute_ground_segment_trade(
        orbit_altitude_km=study.requirements.orbit.altitude_km,
        orbit_inclination_deg=study.requirements.orbit.inclination_deg,
        data_volume_gb_per_day=study.requirements.payloads[0].data_volume_per_day_gb if study.requirements.payloads else 1.0,
        spacecraft_class=study.requirements.spacecraft_class,
        orbit_type=study.requirements.orbit.orbit_type.value if hasattr(study.requirements.orbit.orbit_type, 'value') else str(study.requirements.orbit.orbit_type),
    )

@router.get("/ground/mcs/{study_id}")
async def mcs_config_endpoint(study_id: str, framework: str = Query(default="cosmos")) -> dict:
    """Generate Mission Control System configuration."""
    state, _, _ = await _run_design_for_study(study_id)
    return generate_mcs_config(state.parameters, framework=framework)

@router.get("/ground/passes/{study_id}")
async def pass_predictions_endpoint(study_id: str) -> dict:
    """Generate pass predictions for the study's orbit and ground stations."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")
    stations = [{"name": gs, "latitude_deg": 78.0} for gs in study.requirements.ground_stations]
    return generate_pass_predictions(
        study.requirements.orbit.altitude_km,
        study.requirements.orbit.inclination_deg,
        stations,
    )

@router.get("/ground/timeline/{study_id}")
async def ops_timeline_endpoint(study_id: str) -> dict:
    """Generate operations timeline."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")
    return generate_ops_timeline(study.requirements.design_lifetime_years)


# --- Test Procedures ---

@router.get("/test/procedures/{study_id}")
async def test_procedures_endpoint(study_id: str) -> dict:
    """Generate test procedures from study requirements."""
    from spacecdf_common.models.requirements import generate_requirements
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")
    reqs = generate_requirements(study.requirements.model_dump())
    procs = generate_test_procedures([r.model_dump() for r in reqs])
    return {"study_id": study_id, "procedures": [p.model_dump() for p in procs], "count": len(procs)}

@router.get("/test/environmental/{study_id}")
async def environmental_specs_endpoint(study_id: str, launch_vehicle: str = Query(default="falcon_9")) -> dict:
    """Generate environmental test specifications."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)
    specs = generate_environmental_test_specs(launch_vehicle, study.requirements.target_mass_kg or 5.0)
    return {"specs": [s.model_dump() for s in specs]}


# --- Launch Planning ---

@router.get("/launch/compatibility/{study_id}")
async def launch_compatibility_endpoint(study_id: str) -> dict:
    """Check launch vehicle compatibility for a study."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)
    mass = study.requirements.target_mass_kg or 5.0
    form_map = {"nano": 3, "micro": 6, "small": 12}
    volume_u = form_map.get(study.requirements.spacecraft_class, 6)
    return check_launch_compatibility(
        mass, volume_u,
        str(study.requirements.orbit.orbit_type.value if hasattr(study.requirements.orbit.orbit_type, 'value') else study.requirements.orbit.orbit_type),
        study.requirements.orbit.altitude_km,
        study.requirements.orbit.inclination_deg,
    )

@router.get("/launch/campaign/{study_id}")
async def launch_campaign_endpoint(study_id: str) -> dict:
    """Generate launch campaign timeline."""
    return {"timeline": generate_campaign_timeline()}

@router.get("/launch/regulatory/{study_id}")
async def regulatory_checklist_endpoint(study_id: str, country: str = Query(default="UK")) -> dict:
    """Generate regulatory filing checklist."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)
    freq = 437.0  # Default UHF
    return {"checklist": generate_regulatory_checklist(
        study.requirements.orbit.altitude_km, freq,
        study.requirements.target_mass_kg or 5.0, country,
    )}


# --- BOM ---

class BOMRequest(BaseModel):
    selected_components: dict[str, dict[str, Any]]
    form_factor: str = "3U"

@router.post("/bom")
async def bom_endpoint(req: BOMRequest) -> dict:
    """Generate Bill of Materials from selected components (legacy)."""
    return generate_bom(req.selected_components, req.form_factor)


@router.get("/bom/{study_id}")
async def bom_from_elements_endpoint(
    study_id: str,
    fmt: str = Query("json", description="Output format: json, csv, svg"),
) -> Any:
    """Generate BOM from the element tree for a study."""
    from ..routers.elements import _elements
    from fastapi.responses import PlainTextResponse

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    if not elements:
        raise HTTPException(404, f"No elements found for study {study_id}")

    # Get study name
    store = get_study_store()
    study = store.get(study_id)
    study_name = study.requirements.name if study else "SpaceCDF Mission"

    # Get SEMP answers if available (from request body or study)
    bom = generate_bom_from_elements(elements, study_name=study_name)

    if fmt == "csv":
        csv_content = bom_to_csv(bom)
        return PlainTextResponse(csv_content, media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename=bom-{study_id[:8]}.csv"})
    elif fmt == "svg":
        svg_content = bom_to_svg_table(bom)
        return PlainTextResponse(svg_content, media_type="image/svg+xml")

    return bom


# --- Engineering Budgets ---

@router.get("/budgets/{study_id}")
async def engineering_budgets_endpoint(study_id: str) -> dict:
    """Compute engineering budgets with requirement roll-up for a study."""
    from spacecdf_common.models.budgets import compute_engineering_budgets, check_requirement_impact
    state, _, _ = await _run_design_for_study(study_id)
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)

    conops_modes = []
    if study.conops and study.conops.modes:
        conops_modes = [m.model_dump() for m in study.conops.modes]

    budgets = compute_engineering_budgets(
        parameters=state.parameters,
        mission_requirements=study.requirements.model_dump(),
        conops_modes=conops_modes,
        spacecraft_class=study.requirements.spacecraft_class,
    )

    impacts = check_requirement_impact(budgets)

    return {
        "study_id": study_id,
        "budgets": {
            name: {
                "name": b.name, "unit": b.unit,
                "total_actual": round(b.total_actual, 3),
                "total_allocation": round(b.total_allocation, 3),
                "margin_percent": round(b.margin_percent, 1),
                "status": b.status.value,
                "mission_requirement_at_risk": b.mission_requirement_at_risk,
                "mission_requirement_id": b.mission_requirement_id,
                "lines": [{"subsystem": l.subsystem, "actual": round(l.actual, 4), "allocation": round(l.allocation, 4), "unit": l.unit} for l in b.lines],
            }
            for name, b in budgets.items()
        },
        "requirement_impacts": impacts,
    }


# --- Orbit Trade ---

@router.get("/orbit-trade/{study_id}")
async def orbit_trade_endpoint(study_id: str) -> dict:
    """Compute orbit trade study from study objectives."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)
    # Extract parameters from objectives or requirements
    gsd = 10.0
    revisit = 3.0
    aperture = 0.15
    if study.requirements.payloads:
        pl = study.requirements.payloads[0]
        gsd = getattr(pl, 'gsd_m', 10.0) or 10.0  # Default 10m if not specified
        aperture = 0.15  # Default 15cm aperture
    return compute_orbit_trade(
        target_gsd_m=gsd, target_revisit_days=revisit, aperture_m=aperture,
        max_mass_kg=study.requirements.target_mass_kg or 12,
        max_cost_meur=study.requirements.target_cost_meur or 10,
        min_lifetime_years=study.requirements.design_lifetime_years,
    )


class OrbitTradeRequest(BaseModel):
    target_gsd_m: float = 10.0
    target_revisit_days: float = 3.0
    target_latitude_band: list[float] = [-30.0, 30.0]
    aperture_m: float = 0.15
    max_mass_kg: float = 12.0
    max_cost_meur: float = 10.0
    min_lifetime_years: float = 2.0
    mission_type: str = "earth_observation"

@router.post("/orbit-trade")
async def orbit_trade_custom(req: OrbitTradeRequest) -> dict:
    """Compute orbit trade with custom parameters."""
    return compute_orbit_trade(
        target_gsd_m=req.target_gsd_m, target_revisit_days=req.target_revisit_days,
        target_latitude_band=tuple(req.target_latitude_band[:2]),
        aperture_m=req.aperture_m, max_mass_kg=req.max_mass_kg,
        max_cost_meur=req.max_cost_meur, min_lifetime_years=req.min_lifetime_years,
        mission_type=req.mission_type,
    )


# --- Mission Class Advisor ---

class ClassAdvisorRequest(BaseModel):
    target_gsd_m: float | None = None
    target_revisit_days: float | None = None
    target_lifetime_years: float | None = None
    max_budget_meur: float | None = None
    max_schedule_months: int | None = None
    target_pointing_deg: float | None = None
    target_data_rate_mbps: float | None = None

@router.post("/class-advisor")
async def class_advisor_endpoint(req: ClassAdvisorRequest) -> dict:
    """Advise which spacecraft class fits the mission objectives."""
    return advise_mission_class(
        target_gsd_m=req.target_gsd_m, target_revisit_days=req.target_revisit_days,
        target_lifetime_years=req.target_lifetime_years, max_budget_meur=req.max_budget_meur,
        max_schedule_months=req.max_schedule_months, target_pointing_deg=req.target_pointing_deg,
        target_data_rate_mbps=req.target_data_rate_mbps,
    )

@router.get("/class-advisor/{study_id}")
async def class_advisor_from_study(study_id: str) -> dict:
    """Advise mission class from a study's requirements."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)
    pointing = min((p.pointing_accuracy_deg for p in study.requirements.payloads), default=None)
    data_rate = max((p.data_rate_mbps for p in study.requirements.payloads), default=None)
    return advise_mission_class(
        target_lifetime_years=study.requirements.design_lifetime_years,
        max_budget_meur=study.requirements.target_cost_meur,
        target_pointing_deg=pointing, target_data_rate_mbps=data_rate,
    )


# --- Traceability ---

@router.get("/traceability/{study_id}/{budget_name}")
async def traceability_endpoint(study_id: str, budget_name: str) -> dict:
    """Trace a budget to stakeholder impact."""
    from spacecdf_common.models.budgets import compute_engineering_budgets
    from spacecdf_common.models.requirements import generate_requirements
    state, _, _ = await _run_design_for_study(study_id)
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)

    budgets = compute_engineering_budgets(state.parameters, study.requirements.model_dump(),
        spacecraft_class=study.requirements.spacecraft_class)
    budget = budgets.get(budget_name)
    if not budget:
        raise HTTPException(404, f"Budget {budget_name} not found")

    reqs = generate_requirements(study.requirements.model_dump())
    funcs = [f.model_dump() for f in study.functional_decomposition.functions] if study.functional_decomposition else []
    objs = [o.model_dump() for o in study.mission_need.objectives] if study.mission_need else []
    shs = [s.model_dump() for s in study.mission_need.stakeholders] if study.mission_need else []

    report = trace_budget_to_need(
        budget_name=budget_name, budget_status=budget.status.value,
        budget_margin_percent=budget.margin_percent,
        parameters=state.parameters,
        requirements=[r.model_dump() for r in reqs],
        functions=funcs, objectives=objs, stakeholders=shs,
    )
    return {
        "trigger": report.trigger,
        "severity": report.severity,
        "chain": [{"level": l.level, "id": l.id, "text": l.text, "status": l.status} for l in report.chain],
        "recovery_options": [{"description": o.description, "subsystem": o.subsystem, "impact": o.impact,
                              "feasibility": o.feasibility, "trade_off": o.trade_off} for o in report.recovery_options],
        "stakeholder_impact": report.stakeholder_impact,
    }


# --- Session Guidance ---

@router.get("/session-guidance/{study_id}")
async def session_guidance_endpoint(study_id: str) -> dict:
    """Recommend what session to run next based on study maturity."""
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)
    return recommend_next_session({
        "mission_need": study.mission_need.model_dump() if study.mission_need else {},
        "has_design_result": False,  # Would check design state in production
        "components_selected": 0,
        "orbit_decided": study.requirements.orbit.altitude_km != 500,  # Default = not decided
    })


# --- Mission Trade (Space vs Non-Space) ---

class MissionTradeRequest(BaseModel):
    target_gsd_m: float = 10.0
    target_revisit_days: float = 3.0
    target_coverage: str = "regional"
    target_latency_hours: float = 24.0
    target_bands: list[str] | None = None
    require_data_ownership: bool = False
    require_scheduling_control: bool = False
    max_annual_budget_keur: float = 500.0
    mission_type: str = "earth_observation"
    num_spacecraft: int = 1

@router.post("/mission-trade")
async def mission_trade_endpoint(req: MissionTradeRequest) -> dict:
    """Compute space vs non-space mission trade analysis.

    Should be called BEFORE committing to building a satellite.
    Returns scored alternatives filtered by mission_type — comms missions
    don't see optical EO satellites, etc. Constellation option included
    when num_spacecraft > 1 or coverage is global.
    """
    return compute_mission_trade(
        target_gsd_m=req.target_gsd_m,
        target_revisit_days=req.target_revisit_days,
        target_coverage=req.target_coverage,
        target_latency_hours=req.target_latency_hours,
        target_bands=req.target_bands,
        require_data_ownership=req.require_data_ownership,
        require_scheduling_control=req.require_scheduling_control,
        max_annual_budget_keur=req.max_annual_budget_keur,
        mission_type=req.mission_type,
        num_spacecraft=req.num_spacecraft,
    )


# --- Currency ---

@router.get("/currencies")
async def list_currencies_endpoint() -> dict:
    """List available currencies with exchange rates and volatility."""
    from ..services.currency import list_currencies, EXCHANGE_RATES
    return {"currencies": list_currencies(), "base": "EUR"}

@router.get("/currency/convert")
async def convert_currency(
    amount_eur: float = Query(...),
    target: str = Query(default="USD"),
    programme_years: float = Query(default=0),
) -> dict:
    """Convert EUR amount to target currency with optional risk band."""
    from ..services.currency import convert_cost
    result = convert_cost(amount_eur, target, programme_years)
    return {
        "original_eur": result.original_eur,
        "converted": result.converted,
        "currency": result.currency,
        "rate": result.rate,
        "risk_low": result.risk_low,
        "risk_high": result.risk_high,
        "risk_band_percent": result.risk_band_percent,
        "programme_years": result.programme_years,
    }


# --- Custom Equipment Import ---

class CustomComponentRequest(BaseModel):
    component: dict[str, Any]
    category: str

@router.post("/equipment/import")
async def import_custom_component(req: CustomComponentRequest) -> dict:
    """Import a user-defined component into the in-memory KB.

    Validates required fields, adds to the KB for the current session.
    """
    comp = req.component
    required = ["id", "name", "mass_kg"]
    missing = [f for f in required if f not in comp]
    if missing:
        raise HTTPException(400, f"Missing required fields: {missing}")

    # Add to the KB (in-memory for this session)
    # In production, persist to YAML file in packages/spacecdf-kb/data/components/
    comp["category"] = req.category
    comp["source"] = "user_import"

    return {
        "imported": True,
        "component_id": comp.get("id"),
        "component_name": comp.get("name"),
        "category": req.category,
        "note": "Component added to in-memory KB for this session. Restart will clear it.",
    }


# --- Requirement Engine ---

@router.get("/requirements/generate/{study_id}")
async def generate_requirements_endpoint(study_id: str) -> dict:
    """Generate SMART requirements from study objectives and functions.

    Returns suggested requirements for user approval (suggest-then-approve).
    Each requirement has Accept / Edit / Reject status.
    """
    from ..services.requirement_engine import generate_smart_requirements
    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404)

    objectives = [o.model_dump() for o in study.mission_need.objectives] if study.mission_need.objectives else []
    functions = [f.model_dump() for f in study.functional_decomposition.functions] if study.functional_decomposition.functions else []

    suggestions = generate_smart_requirements(
        objectives=objectives,
        mission_requirements_dict=study.requirements.model_dump(),
        functions=functions,
    )

    return {
        "study_id": study_id,
        "suggestions": [
            {
                "id": s.id, "text": s.text, "req_type": s.req_type,
                "domain": s.domain, "threshold": s.threshold,
                "operator": s.operator, "unit": s.unit,
                "verification_method": s.verification_method,
                "objective_id": s.objective_id, "function_id": s.function_id,
                "rationale": s.rationale, "status": s.status,
            }
            for s in suggestions
        ],
        "count": len(suggestions),
    }


@router.post("/requirements/generate")
async def generate_requirements_from_data(body: dict[str, Any]) -> dict:
    """Generate SMART requirements from posted objectives (no study needed)."""
    from ..services.requirement_engine import generate_smart_requirements

    objectives = body.get("objectives", [])
    mission_reqs = {
        "mission_type": body.get("mission_type", "earth_observation"),
        "spacecraft_class": body.get("spacecraft_class", "nano"),
        "orbit": body.get("orbit", {}),
        "payloads": body.get("payloads", []),
        "name": body.get("name", "Mission"),
    }

    suggestions = generate_smart_requirements(
        objectives=objectives,
        mission_requirements_dict=mission_reqs,
        functions=[],
    )

    return {
        "suggestions": [
            {
                "id": s.id, "text": s.text, "req_type": s.req_type,
                "domain": s.domain, "threshold": s.threshold,
                "operator": s.operator, "unit": s.unit,
                "verification_method": s.verification_method,
                "objective_id": s.objective_id, "function_id": s.function_id,
                "rationale": s.rationale, "status": s.status,
            }
            for s in suggestions
        ],
        "count": len(suggestions),
    }


@router.post("/requirements/validate")
async def validate_requirement_endpoint(requirement: dict[str, Any]) -> dict:
    """Validate a single requirement against SMART criteria."""
    from ..services.requirement_engine import validate_smart
    check = validate_smart(requirement)
    return {
        "requirement_id": check.requirement_id,
        "is_smart": check.is_smart,
        "specific": check.specific,
        "measurable": check.measurable,
        "achievable": check.achievable,
        "relevant": check.relevant,
        "traceable": check.traceable,
        "is_how_not_what": check.is_how_not_what,
        "issues": check.issues,
    }


@router.post("/requirements/check-compliance")
async def check_compliance_endpoint(body: dict[str, Any]) -> dict:
    """Check non-compliance and get resolution options."""
    from ..services.requirement_engine import check_non_compliance
    return check_non_compliance(
        requirement=body.get("requirement", {}),
        achieved_value=body.get("achieved_value"),
        margin_percent=body.get("margin_percent"),
    )


@router.post("/requirements/split")
async def split_requirement_endpoint(requirement: dict[str, Any]) -> dict:
    """Split a compound requirement into atomic statements."""
    from ..services.requirement_engine import split_compound_requirement
    results = split_compound_requirement(requirement)
    return {"original_id": requirement.get("id", ""), "split": results, "was_split": len(results) > 1}


# --- Consistency Checking ---

@router.get("/consistency/{study_id}")
async def run_consistency_check_endpoint(study_id: str) -> dict:
    """Run full consistency check on a study.

    Validates requirements traceability, function coverage, interface
    completeness, budget margins, ConOps coverage, and equipment compatibility.
    """
    from ..services.consistency_engine import run_consistency_check

    store = get_study_store()
    study = store.get(study_id)
    if not study:
        raise HTTPException(404, detail=f"Study {study_id} not found")

    # Extract data from study
    mn = {}
    if study.mission_need:
        mn = {
            "problem_statement": getattr(study.mission_need, "problem_statement", ""),
            "objectives": [{"text": o.text, "priority": o.priority, "measurable_criterion": getattr(o, "measurable_criterion", "")}
                           for o in getattr(study.mission_need, "objectives", [])],
        }

    reqs = [{"id": r.id, "text": r.text, "domain": r.domain,
             "objective_id": getattr(r, "objective_id", None),
             "function_id": getattr(r, "function_id", None)}
            for r in getattr(study, "requirements", []) if hasattr(study, "requirements")]

    funcs = []
    if hasattr(study, "functional_decomposition") and study.functional_decomposition:
        funcs = [{"id": f.id, "name": f.name, "parent_function_id": f.parent_function_id,
                  "allocated_to": f.allocated_to, "derived_requirement_ids": f.derived_requirement_ids}
                 for f in getattr(study.functional_decomposition, "functions", [])]

    phase_id = study.phase.value if hasattr(study.phase, "value") else str(study.phase)

    report = run_consistency_check(
        mission_need=mn,
        requirements=reqs,
        functions=funcs,
        phase_id=phase_id,
    )

    return {
        "study_id": study_id,
        "checked_at": report.checked_at,
        "total_checks": report.total_checks,
        "pass_count": report.pass_count,
        "fail_count": report.fail_count,
        "health_score": round(report.health_score, 1),
        "critical_count": report.critical_count,
        "major_count": report.major_count,
        "issues": [
            {
                "id": i.id,
                "severity": i.severity,
                "category": i.category,
                "title": i.title,
                "description": i.description,
                "affected_items": i.affected_items,
                "suggested_fix": i.suggested_fix,
            }
            for i in report.issues
        ],
    }


# --- Spectrum & Licensing ---

@router.get("/spectrum/bands")
async def get_spectrum_bands(
    mission_type: str = "earth_observation",
    license_type: str = "commercial",
    data_rate_mbps: float = 10.0,
) -> dict:
    """Get available frequency bands filtered by mission type and license."""
    from ..services.spectrum import get_bands_for_mission
    bands = get_bands_for_mission(mission_type, license_type, data_rate_mbps)
    return {"bands": bands, "count": len(bands)}


@router.post("/spectrum/itu-api-template")
async def generate_itu_template(body: dict[str, Any]) -> dict:
    """Generate ITU Advance Publication Information filing template."""
    from ..services.spectrum import generate_itu_api_template
    return generate_itu_api_template(**body)


@router.post("/spectrum/iaru-template")
async def generate_iaru_template(body: dict[str, Any]) -> dict:
    """Generate IARU amateur satellite coordination request template."""
    from ..services.spectrum import generate_iaru_coordination_template
    return generate_iaru_coordination_template(**body)


# --- Regulatory Paperwork ---

@router.post("/regulatory/rsssa")
async def generate_rsssa(body: dict[str, Any]) -> dict:
    """Generate Canadian RSSSA filing template."""
    from ..services.regulatory import generate_rsssa_template
    return generate_rsssa_template(**body)


@router.post("/regulatory/export-assessment")
async def generate_export(body: dict[str, Any]) -> dict:
    """Generate export control classification assessment."""
    from ..services.regulatory import generate_export_assessment
    return generate_export_assessment(**body)


@router.post("/regulatory/copuos-registration")
async def generate_copuos(body: dict[str, Any]) -> dict:
    """Generate UN COPUOS registration template."""
    from ..services.regulatory import generate_copuos_registration
    return generate_copuos_registration(**body)


@router.post("/regulatory/eol-report")
async def generate_eol(body: dict[str, Any]) -> dict:
    """Generate end-of-life / debris compliance analysis report."""
    from ..services.regulatory import generate_eol_report
    return generate_eol_report(**body)


@router.post("/regulatory/itu-api-filing")
async def generate_itu_filing(body: dict[str, Any]) -> dict:
    """Generate ITU API filing template (Appendix 4) with auto-computed fields."""
    from ..services.regulatory import generate_itu_api_filing
    return generate_itu_api_filing(**body)


# --- Tabular Trade Studies ---

@router.get("/trade-templates")
async def get_trade_templates() -> dict:
    """Get pre-built trade study templates."""
    from ..services.tabular_trade import get_trade_templates
    return {"templates": get_trade_templates()}


@router.post("/trade-study")
async def run_trade_study(body: dict[str, Any]) -> dict:
    """Run a tabular trade study with criteria, weightings, and options."""
    from ..services.tabular_trade import run_tabular_trade

    result = run_tabular_trade(
        name=body.get("name", "Trade Study"),
        criteria=body.get("criteria", []),
        options=body.get("options", []),
    )

    return {
        "name": result.name,
        "recommendation": result.recommendation,
        "criteria": [{"id": c.id, "name": c.name, "weight": c.weight, "direction": c.direction, "unit": c.unit, "category": c.category} for c in result.criteria],
        "results": [
            {
                "rank": r.rank,
                "option_id": r.option_id,
                "option_name": r.option_name,
                "total_score": r.total_score,
                "all_thresholds_met": r.all_thresholds_met,
                "normalised_scores": r.normalised_scores,
                "weighted_scores": r.weighted_scores,
                "threshold_pass": r.threshold_pass,
            }
            for r in result.results
        ],
        "sensitivity": result.sensitivity,
    }


# --- Constellation Design ---

@router.post("/constellation/design")
async def design_constellation(body: dict[str, Any]) -> dict:
    """Design Walker delta constellation for coverage targets."""
    from spacecdf_common.physics.constellation import design_walker_constellation, compute_coverage, compute_constellation_budget

    candidates = design_walker_constellation(
        coverage_target_percent=body.get("coverage_target_percent", 95),
        max_revisit_hours=body.get("max_revisit_hours", 6),
        altitude_km=body.get("altitude_km", 500),
        inclination_deg=body.get("inclination_deg", 97.4),
    )

    results = []
    for design in candidates:
        cov = compute_coverage(design)
        budget = compute_constellation_budget(
            design.total_satellites,
            per_satellite_mass_kg=body.get("per_satellite_mass_kg", 5),
            per_satellite_cost_meur=body.get("per_satellite_cost_meur", 0.5),
        )
        results.append({
            "total_satellites": design.total_satellites,
            "num_planes": design.num_planes,
            "sats_per_plane": design.sats_per_plane,
            "walker_notation": f"{design.total_satellites}/{design.num_planes}/{design.phasing_parameter}",
            "coverage_percent": cov.coverage_percent,
            "max_revisit_hours": cov.max_revisit_hours,
            "mean_revisit_hours": cov.mean_revisit_hours,
            "total_mass_kg": budget.total_mass_kg,
            "total_cost_meur": budget.total_cost_meur,
            "launch_cost_meur": budget.launch_cost_meur,
            "spares": budget.spare_satellites,
            "learning_curve": budget.learning_curve_factor,
        })

    return {"candidates": results, "count": len(results)}


# --- Beyond-LEO Orbits ---

@router.get("/beyond-leo/orbits")
async def list_beyond_leo_orbits() -> dict:
    """List available beyond-LEO orbit options with environment data."""
    from spacecdf_common.physics.beyond_leo import BEYOND_LEO_ORBITS
    return {
        "orbits": [
            {
                "name": o.name,
                "type": o.orbit_type,
                "altitude_km": o.altitude_km,
                "perigee_km": o.perigee_km,
                "inclination_deg": o.inclination_deg,
                "period_hours": o.period_hours,
                "radiation_krad_per_year": o.radiation_dose_krad_per_year,
                "eclipse_fraction": o.eclipse_fraction,
                "solar_flux_w_m2": o.solar_flux_w_m2,
                "max_range_km": o.max_range_km,
            }
            for o in BEYOND_LEO_ORBITS
        ],
    }


@router.post("/beyond-leo/transfer")
async def compute_transfer(body: dict[str, Any]) -> dict:
    """Compute transfer orbit delta-V from LEO to target orbit."""
    from spacecdf_common.physics.beyond_leo import BEYOND_LEO_ORBITS, compute_transfer_delta_v

    target_name = body.get("target_orbit", "GEO (35786 km)")
    from_alt = body.get("from_altitude_km", 500)

    target = next((o for o in BEYOND_LEO_ORBITS if o.name == target_name), None)
    if not target:
        return {"error": f"Unknown orbit: {target_name}"}

    transfer = compute_transfer_delta_v(from_alt, target)
    return {
        "target": target_name,
        "delta_v_ms": transfer.delta_v_ms,
        "transfer_time_days": transfer.transfer_time_days,
        "transfer_type": transfer.type,
    }


@router.post("/beyond-leo/dsn-link")
async def dsn_link_budget(body: dict[str, Any]) -> dict:
    """Compute deep-space link budget for DSN communication."""
    from spacecdf_common.physics.beyond_leo import compute_dsn_link_budget
    return compute_dsn_link_budget(**body)


# --- Constraint Propagation ---

@router.post("/constraints/analyze")
async def analyze_constraints(body: dict[str, Any]) -> dict:
    """Analyze constraint violations with root causes, impacts, and resolutions."""
    from ..services.constraint_propagation import analyze_violations
    violations = analyze_violations(
        design_params=body.get("design_params", {}),
        constraints=body.get("constraints", {}),
    )
    return {
        "violations": [
            {
                "id": v.constraint.id, "name": v.constraint.name,
                "budget": v.constraint.budget_type, "parameter": v.constraint.parameter_id,
                "current": v.constraint.current_value, "limit": v.constraint.limit_value,
                "margin_pct": round(v.constraint.margin_pct, 1),
                "root_causes": v.root_causes,
                "downstream_impacts": [{"target": i.target_param, "budget": i.target_budget, "desc": i.description} for i in v.downstream_impacts],
                "resolutions": [{"id": r.id, "desc": r.description, "param": r.parameter_to_change, "dir": r.direction, "trade_off": r.trade_off} for r in v.resolutions],
            }
            for v in violations
        ],
        "total_violations": len(violations),
    }

@router.get("/constraints/interconnections")
async def get_interconnections() -> dict:
    """Return the full design point interconnection map (50+ connections)."""
    from ..services.constraint_propagation import get_interconnection_map
    conns = get_interconnection_map()
    return {"connections": conns, "total": len(conns)}


@router.post("/constraints/circular-deps")
async def check_circular_dependencies(body: dict[str, Any]) -> dict:
    """Detect circular dependencies for a given resolution path."""
    from ..services.constraint_propagation import detect_circular_dependencies
    cycles = detect_circular_dependencies(
        starting_param=body.get("starting_param", ""),
        resolution_param=body.get("resolution_param", ""),
    )
    return {"cycles": cycles, "has_cycles": len(cycles) > 0}


# --- System Architecture ---

@router.get("/architecture/subsystems")
async def list_architecture_subsystems() -> dict:
    """List all subsystems that have architecture options."""
    from spacecdf_common.models.architecture import get_all_subsystems
    return {"subsystems": get_all_subsystems()}


@router.get("/architecture/options/{subsystem}")
async def get_architecture_options(subsystem: str) -> dict:
    """Get available architecture options for a subsystem."""
    from spacecdf_common.models.architecture import get_options
    options = get_options(subsystem)
    return {
        "subsystem": subsystem,
        "options": [
            {
                "id": o.id, "name": o.name, "description": o.description,
                "mass_kg": o.mass_kg_typical, "power_w": o.power_w_typical,
                "cost_keur": o.cost_keur_typical, "trl": o.trl,
                "pointing_deg": o.pointing_deg, "data_rate_mbps": o.data_rate_mbps,
                "pros": o.pros, "cons": o.cons,
                "num_derived_requirements": len(o.derived_requirements),
            }
            for o in options
        ],
    }


@router.post("/architecture/select")
async def select_architecture_option(body: dict[str, Any]) -> dict:
    """Select an architecture option and get derived requirements + block diagram."""
    from spacecdf_common.models.architecture import select_architecture
    return select_architecture(body.get("subsystem", ""), body.get("option_id", ""))


# --- Parametric Model Data (user-editable) ---

@router.get("/parametric-data")
async def get_parametric_data() -> dict:
    """Return all parametric model data for user viewing and editing.

    Exposes mass fractions, cost fractions, power duty cycles, and SA power
    tables. Users can override any value via the design parameters.
    """
    from spacecdf_common.physics.heritage_mass import get_all_parametric_data
    return get_all_parametric_data()


@router.post("/duty-cycles")
async def estimate_duty_cycles_endpoint(body: dict[str, Any]) -> dict:
    """Estimate power duty cycles for a mission configuration.

    Returns per-mode power draw, duty cycle %, orbit-average power,
    and recommended SA power generation.
    """
    from spacecdf_common.physics.heritage_mass import estimate_duty_cycles, estimate_sa_power_needed

    modes = estimate_duty_cycles(
        spacecraft_class=body.get("spacecraft_class", "nano"),
        mission_type=body.get("mission_type", "earth_observation"),
        comms_band=body.get("comms_band", "S"),
        eclipse_fraction=body.get("eclipse_fraction", 0.35),
    )

    sa_needed = estimate_sa_power_needed(
        spacecraft_class=body.get("spacecraft_class", "nano"),
        mission_type=body.get("mission_type", "earth_observation"),
        comms_band=body.get("comms_band", "S"),
        eclipse_fraction=body.get("eclipse_fraction", 0.35),
    )

    total_avg = sum(m["orbit_avg_w"] for m in modes)

    return {
        "modes": modes,
        "orbit_average_power_w": round(total_avg, 1),
        "sa_power_needed_w": sa_needed,
        "notes": "SA power accounts for duty cycling — not all modes run simultaneously. "
                 "This is typically 30-50% lower than summing all subsystem peak powers.",
    }
