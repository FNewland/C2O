"""SpaceCDF — Design Execution API.

Runs the design convergence loop and returns results.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator, ConvergenceConfig

from .studies import get_study_store

router = APIRouter()


class DesignRunRequest(BaseModel):
    """Request to run the design loop."""
    max_iterations: int = 50
    convergence_threshold: float = 0.001


class DesignRunResponse(BaseModel):
    """Response from a design loop execution."""
    converged: bool
    iterations: int
    total_time_s: float
    parameters: dict
    budgets: dict
    warnings: list[str]
    recommendations: list[str]
    conflicts: list[dict] = []


@router.post("/{study_id}/run")
async def run_design_loop(study_id: str, request: DesignRunRequest | None = None) -> DesignRunResponse:
    """Execute the design convergence loop for a study."""
    studies = get_study_store()
    study = studies.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    config = ConvergenceConfig(
        max_iterations=request.max_iterations if request else 50,
        convergence_threshold=request.convergence_threshold if request else 0.001,
    )

    orchestrator = DesignLoopOrchestrator(config=config)
    orchestrator.initialise_agents()

    loop_result = await orchestrator.run(study.requirements)

    # Update study with results
    study.iterations = loop_result.iterations

    # Serialise parameters
    params = {}
    if loop_result.final_state:
        for pid, p in loop_result.final_state.parameters.items():
            params[pid] = {
                "value": p.value,
                "unit": p.unit,
                "confidence": p.confidence,
                "margin_percent": p.margin_percent,
                "source": p.source.value,
                "domain": p.domain,
            }

    # Serialise budgets
    budgets = {}
    for btype, budget in loop_result.budgets.items():
        budgets[btype] = {
            "total_nominal": budget.total_nominal,
            "total_with_margin": budget.total_with_margin,
            "allocation": budget.allocation,
            "margin_percent": budget.margin_percent,
            "status": budget.status.value,
            "lines": [line.model_dump() for line in budget.lines],
        }

    return DesignRunResponse(
        converged=loop_result.converged,
        iterations=len(loop_result.iterations),
        total_time_s=round(loop_result.total_time_s, 3),
        parameters=params,
        budgets=budgets,
        warnings=loop_result.all_warnings,
        recommendations=loop_result.all_recommendations,
        conflicts=[c.model_dump() if hasattr(c, 'model_dump') else c for c in loop_result.conflicts],
    )


@router.post("/quick-design")
async def quick_design(requirements: MissionRequirements) -> DesignRunResponse:
    """One-shot design: create study + run loop in a single call."""
    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    loop_result = await orchestrator.run(requirements)

    params = {}
    if loop_result.final_state:
        for pid, p in loop_result.final_state.parameters.items():
            params[pid] = {
                "value": p.value,
                "unit": p.unit,
                "confidence": p.confidence,
                "margin_percent": p.margin_percent,
                "source": p.source.value,
                "domain": p.domain,
            }

    budgets = {}
    for btype, budget in loop_result.budgets.items():
        budgets[btype] = {
            "total_nominal": budget.total_nominal,
            "total_with_margin": budget.total_with_margin,
            "allocation": budget.allocation,
            "margin_percent": budget.margin_percent,
            "status": budget.status.value,
            "lines": [line.model_dump() for line in budget.lines],
        }

    return DesignRunResponse(
        converged=loop_result.converged,
        iterations=len(loop_result.iterations),
        total_time_s=round(loop_result.total_time_s, 3),
        parameters=params,
        budgets=budgets,
        warnings=loop_result.all_warnings,
        recommendations=loop_result.all_recommendations,
        conflicts=[c.model_dump() if hasattr(c, 'model_dump') else c for c in loop_result.conflicts],
    )
