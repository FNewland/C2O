"""SpaceCDF — Engineering API Router.

Endpoints for equipment selection, requirement verification, sensitivity
analysis, trade studies, and cost estimation. These are the Phase 3
interactive CDF capabilities.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator

from .studies import get_study_store

router = APIRouter()


# --- Helper: run design and get state ---

async def _get_design_state(study_id: str | None = None, requirements: MissionRequirements | None = None):
    """Run design loop and return (state, loop_result, requirements)."""
    if study_id:
        studies = get_study_store()
        study = studies.get(study_id)
        if not study:
            raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
        requirements = study.requirements

    if not requirements:
        raise HTTPException(status_code=400, detail="Either study_id or requirements must be provided")

    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    result = await orchestrator.run(requirements)
    return result.final_state, result, requirements


# --- Equipment Search ---

class EquipmentSearchResponse(BaseModel):
    domain: str
    categories: dict  # {category: [ComponentMatch...]}


@router.get("/equipment/{domain}/search")
async def search_equipment(domain: str, study_id: str | None = None) -> dict:
    """Search KB for equipment compatible with the current design for a given domain.

    Returns ranked components by fit_score, with compatibility notes.
    """
    from ..services.equipment import search_compatible_equipment, DOMAIN_TO_CATEGORIES
    from spacecdf_common.config.loader import load_yaml

    if domain not in DOMAIN_TO_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {domain}. Available: {list(DOMAIN_TO_CATEGORIES.keys())}")

    # Get design state
    state = None
    if study_id:
        state, _, _ = await _get_design_state(study_id=study_id)

    # Load KB components
    kb_data_dir = Path(__file__).resolve().parents[4] / "spacecdf-kb" / "src" / "spacecdf_kb" / "data"
    if not kb_data_dir.exists():
        # Fallback search
        kb_data_dir = Path(__file__).resolve()
        while kb_data_dir != kb_data_dir.parent:
            candidate = kb_data_dir / "packages" / "spacecdf-kb" / "src" / "spacecdf_kb" / "data"
            if candidate.exists():
                kb_data_dir = candidate
                break
            kb_data_dir = kb_data_dir.parent

    kb_components: dict[str, list] = {}
    components_dir = kb_data_dir / "components"
    if components_dir.is_dir():
        for cat in DOMAIN_TO_CATEGORIES[domain]:
            yaml_path = components_dir / f"{cat}.yaml"
            if yaml_path.exists():
                data = load_yaml(yaml_path)
                kb_components[cat] = data.get("components", data.get("items", []))

    if state:
        results = search_compatible_equipment(domain, state, kb_components)
        return {
            "domain": domain,
            "categories": {
                cat: [{"component": m.component, "fit_score": round(m.fit_score, 3), "notes": m.notes}
                      for m in matches]
                for cat, matches in results.items()
            }
        }
    else:
        # No design state — just return all components
        return {
            "domain": domain,
            "categories": {cat: comps for cat, comps in kb_components.items()}
        }


# --- Requirement Verification ---

@router.get("/verification")
async def get_compliance_matrix(
    study_id: str | None = None,
    worst_case: str = Query(default="nominal", description="nominal | eol | hot | cold"),
) -> dict:
    """Build compliance matrix from auto-generated requirements vs design state.

    Supports worst-case analysis modes:
    - nominal: as-designed values
    - eol: end-of-life degradation applied (SA, battery, pointing)
    - hot: hot-case thermal derating
    - cold: cold-case thermal derating
    """
    from ..services.verification import build_compliance_matrix

    state, _, _ = await _get_design_state(study_id=study_id)
    if not state:
        raise HTTPException(status_code=400, detail="No design state available")

    matrix = build_compliance_matrix(state, worst_case=worst_case)

    return {
        "worst_case_mode": worst_case,
        "total_requirements": matrix.total_requirements,
        "compliant": matrix.compliant_count,
        "marginal": matrix.marginal_count,
        "non_compliant": matrix.non_compliant_count,
        "compliance_percent": round(matrix.compliance_percent, 1),
        "requirements": [r.model_dump() for r in matrix.requirements],
        "verifications": [v.model_dump() for v in matrix.verifications],
    }


# --- NASA-Aligned Cost Estimation ---

@router.get("/cost")
async def get_cost_estimate(study_id: str | None = None) -> dict:
    """Run NASA CEH-aligned cost estimation with WBS structure.

    Returns:
    - WBS-structured cost breakdown (NPR 7120.5 Level 2)
    - DDT&E vs recurring split
    - Phase distribution (A/B/CD/E)
    - Cost confidence intervals (P50/P70/P80) via Monte Carlo
    - Learning curve analysis for constellations
    """
    from ..services.cost_engine import estimate_cost

    state, _, _ = await _get_design_state(study_id=study_id)
    if not state:
        raise HTTPException(status_code=400, detail="No design state available")

    est = estimate_cost(state)

    return {
        "model_used": est.model_used,
        "wbs": [
            {"wbs_id": w.wbs_id, "name": w.name, "ddte_keur": w.ddte_keur,
             "recurring_keur": w.recurring_keur, "total_keur": w.total_keur,
             "cost_drivers": w.cost_drivers, "notes": w.notes}
            for w in est.wbs
        ],
        "totals": {
            "spacecraft_ddte_keur": round(est.spacecraft_ddte_keur, 0),
            "spacecraft_recurring_keur": round(est.spacecraft_recurring_keur, 0),
            "payload_keur": round(est.payload_keur, 0),
            "pm_se_sma_keur": round(est.pm_se_sma_keur, 0),
            "launch_keur": round(est.launch_keur, 0),
            "ground_keur": round(est.ground_keur, 0),
            "operations_keur": round(est.operations_keur, 0),
            "total_lcc_keur": round(est.total_lcc_keur, 0),
            "total_lcc_meur": round(est.total_lcc_keur / 1000, 1),
        },
        "phases": {
            "phase_a_keur": round(est.phase_a_keur, 0),
            "phase_b_keur": round(est.phase_b_keur, 0),
            "phase_cd_keur": round(est.phase_cd_keur, 0),
            "phase_e_keur": round(est.phase_e_keur, 0),
        },
        "risk": {
            "p50_keur": round(est.p50_keur, 0),
            "p70_keur": round(est.p70_keur, 0),
            "p80_keur": round(est.p80_keur, 0),
            "p90_keur": round(est.p90_keur, 0),
            "p50_meur": round(est.p50_keur / 1000, 1),
            "p70_meur": round(est.p70_keur / 1000, 1),
            "p80_meur": round(est.p80_keur / 1000, 1),
            "p90_meur": round(est.p90_keur / 1000, 1),
            "mean_keur": round(est.cost_mean_keur, 0),
            "std_keur": round(est.cost_std_keur, 0),
            "cost_hist": est.cost_hist,
            "cost_hist_bin_edges": est.cost_hist_bin_edges,
        },
        "constellation": {
            "num_units": est.num_units,
            "learning_rate": est.learning_rate,
            "fleet_total_keur": round(est.fleet_total_keur, 0) if est.fleet_total_keur > 0 else None,
        },
        "warnings": est.warnings,
    }


# --- Sensitivity Analysis ---

class SensitivityRequest(BaseModel):
    sweep_param: str = "orbit.altitude_km"
    sweep_min: float = 300
    sweep_max: float = 700
    num_points: int = 10


@router.post("/analysis/sensitivity")
async def run_sensitivity_analysis(
    req: SensitivityRequest,
    study_id: str | None = None,
) -> dict:
    """Sweep one parameter across a range and show impact on all budgets.

    Each point runs a full convergence (~5ms), so 20 points completes in ~100ms.
    """
    from ..services.analysis import run_sensitivity

    _, _, requirements = await _get_design_state(study_id=study_id)

    step = (req.sweep_max - req.sweep_min) / max(req.num_points - 1, 1)
    sweep_range = [req.sweep_min + i * step for i in range(req.num_points)]

    result = await run_sensitivity(requirements, req.sweep_param, sweep_range)

    return {
        "sweep_param": result.sweep_param,
        "total_time_ms": round(result.total_time_ms, 1),
        "points": [
            {
                "sweep_value": p.sweep_value,
                "converged": p.converged,
                "budgets": p.budgets,
                "key_params": p.key_params,
            }
            for p in result.points
        ],
    }


# --- Equipment Trade Study ---


class TradeStudyRequest(BaseModel):
    domain: str
    category: str


@router.post("/analysis/trade-study")
async def run_trade_study(
    req: TradeStudyRequest,
    study_id: str | None = None,
) -> dict:
    """Run an equipment trade study: for each KB component in the chosen
    category, evaluate the system-level budget impact.
    """
    from ..services.equipment import DOMAIN_TO_CATEGORIES
    from ..services.analysis import run_equipment_trade_study
    from spacecdf_common.config.loader import load_yaml

    if req.domain not in DOMAIN_TO_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown domain: {req.domain}. Available: {list(DOMAIN_TO_CATEGORIES.keys())}",
        )
    if req.category not in DOMAIN_TO_CATEGORIES[req.domain]:
        raise HTTPException(
            status_code=400,
            detail=f"Category {req.category} not valid for domain {req.domain}",
        )

    _, _, requirements = await _get_design_state(study_id=study_id)

    # Load KB components for this category
    kb_data_dir = Path(__file__).resolve().parents[4] / "spacecdf-kb" / "src" / "spacecdf_kb" / "data"
    if not kb_data_dir.exists():
        p = Path(__file__).resolve()
        while p != p.parent:
            candidate = p / "packages" / "spacecdf-kb" / "src" / "spacecdf_kb" / "data"
            if candidate.exists():
                kb_data_dir = candidate
                break
            p = p.parent

    yaml_path = kb_data_dir / "components" / f"{req.category}.yaml"
    components: list[dict] = []
    if yaml_path.exists():
        data = load_yaml(yaml_path)
        components = data.get("components", data.get("items", []))

    result = await run_equipment_trade_study(requirements, req.domain, req.category, components)

    return {
        "domain": result.domain,
        "category": result.category,
        "total_time_ms": round(result.total_time_ms, 1),
        "rows": [
            {
                "component_id": r.component_id,
                "component_name": r.component_name,
                "manufacturer": r.manufacturer,
                "trl": r.trl,
                "mass_kg": r.mass_kg,
                "power_w": r.power_w,
                "cost_keur": r.cost_keur,
                "heritage": r.heritage,
                "system_mass_kg": round(r.system_mass_kg, 2),
                "system_cost_meur": round(r.system_cost_meur, 2),
                "mass_margin_percent": round(r.mass_margin_percent, 1),
                "power_margin_percent": round(r.power_margin_percent, 1),
                "fit_score": r.fit_score,
            }
            for r in result.rows
        ],
    }


# --- EOL Degradation Curves ---

@router.get("/analysis/eol-curves")
async def get_eol_curves(study_id: str | None = None) -> dict:
    """Compute end-of-life degradation curves for key parameters."""
    from ..services.analysis import compute_eol_curves

    state, _, _ = await _get_design_state(study_id=study_id)
    mission_years = state.get("mission.duration_years", 3.0) or 3.0

    result = compute_eol_curves(state, mission_years)

    return {
        "mission_years": result.mission_years,
        "curves": [
            {
                "year": p.year,
                "sa_power_w": round(p.sa_power_w, 1),
                "battery_capacity_wh": round(p.battery_capacity_wh, 1),
                "pointing_deg": round(p.pointing_deg, 4),
                "link_margin_db": round(p.link_margin_db, 1),
            }
            for p in result.points
        ],
    }
