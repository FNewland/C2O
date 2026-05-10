"""SpaceCDF — Design Execution API.

Runs the design convergence loop and returns results.
Now accepts full V-model input: requirements + mission_need → auto-generates
ConOps modes that are passed to DesignState so agents use them.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator, ConvergenceConfig

from .studies import get_study_store, _generate_default_conops

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

    loop_result = await orchestrator.run(study.requirements, conops=study.conops)

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


class QuickDesignRequest(BaseModel):
    """Accepts requirements + optional mission_need for full V-model flow."""
    requirements: MissionRequirements | None = None
    mission_need: dict[str, Any] | None = None
    # User-set parameter overrides — injected as sticky values so agents don't overwrite
    parameter_overrides: dict[str, Any] | None = None
    # Backward compat: if sent as flat MissionRequirements, parse at validation
    name: str | None = None
    mission_type: str | None = None


@router.post("/quick-design")
async def quick_design(body: QuickDesignRequest | MissionRequirements) -> DesignRunResponse:
    """One-shot design: create study + run loop in a single call.

    Accepts either {requirements, mission_need} or flat MissionRequirements
    for backward compatibility. When mission_need is provided, auto-generates
    ConOps modes that drive multi-mode power/thermal/AOCS sizing.
    """
    # Parse input — handle both new format and legacy flat requirements
    if isinstance(body, MissionRequirements):
        requirements = body
        conops = _generate_default_conops(requirements)
    elif body.requirements:
        requirements = body.requirements
        conops = _generate_default_conops(requirements)
    else:
        # Legacy: body might be flat MissionRequirements fields
        requirements = MissionRequirements(**body.model_dump(exclude_none=True))
        conops = _generate_default_conops(requirements)

    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    loop_result = await orchestrator.run(requirements, conops=conops)

    # Apply user parameter overrides as sticky values (POSITION_OVERRIDE)
    overrides = getattr(body, 'parameter_overrides', None) or {}
    if overrides and loop_result.final_state:
        from spacecdf_common.models.parameter import ParameterSource, ParameterValue
        for param_id, value in overrides.items():
            # Skip non-scalar values (dicts, lists) — only float/str/bool are valid
            if isinstance(value, (dict, list)):
                continue
            try:
                existing = loop_result.final_state.get_param(param_id)
                loop_result.final_state._parameters[param_id] = ParameterValue(
                    id=param_id,
                    name=existing.name if existing else param_id,
                    value=value,
                    unit=existing.unit if existing else "",
                    domain=existing.domain if existing else param_id.split(".")[0],
                    source=ParameterSource.POSITION_OVERRIDE,
                    confidence=1.0,
                )
            except Exception:
                continue  # Skip any value that can't be coerced

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
