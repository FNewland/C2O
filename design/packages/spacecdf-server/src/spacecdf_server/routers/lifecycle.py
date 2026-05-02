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
from ..services.bom_generator import generate_bom
from ..services.fit_gap_analysis import analyze_component_fit, analyze_category
from ..services.ground_segment_trade import compute_ground_segment_trade
from ..services.orbit_trade import compute_orbit_trade
from ..services.class_advisor import advise_mission_class
from ..services.traceability import trace_budget_to_need
from ..services.session_guidance import recommend_next_session

router = APIRouter()


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
    """Generate Bill of Materials from selected components."""
    return generate_bom(req.selected_components, req.form_factor)


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

@router.post("/orbit-trade")
async def orbit_trade_custom(req: OrbitTradeRequest) -> dict:
    """Compute orbit trade with custom parameters."""
    return compute_orbit_trade(
        target_gsd_m=req.target_gsd_m, target_revisit_days=req.target_revisit_days,
        target_latitude_band=tuple(req.target_latitude_band[:2]),
        aperture_m=req.aperture_m, max_mass_kg=req.max_mass_kg,
        max_cost_meur=req.max_cost_meur, min_lifetime_years=req.min_lifetime_years,
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
