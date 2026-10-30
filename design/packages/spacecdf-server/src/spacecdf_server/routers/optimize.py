"""SpaceCDF — Design optimiser API (Phase 5B).

Endpoints:
    GET    /api/optimize/config                        -- available objectives + default vars
    POST   /api/optimize/sessions/{session_id}         -- kick off a run (returns run_id)
    GET    /api/optimize/runs/{run_id}                 -- current run status + history
    GET    /api/optimize/runs                          -- list recent runs

Background tasks own the optimiser work; the caller polls or listens on the
session WS for `optimize.progress` events.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..db.engine import get_session_factory
from ..db.models import OptimizationRunRow
from ..services.optimizer import (
    DEFAULT_DESIGN_VARIABLES,
    OBJECTIVES,
    MultiObjectiveConfig,
    OptimizeConfig,
    OptimizeProgress,
    run_multi_objective,
    run_single_objective,
)
from ..services.session_manager import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory run cache — useful while a run is still executing (DB holds the
# final snapshot). run_id -> latest progress/history payload.
_run_cache: dict[int, dict] = {}


class OptimizeBody(BaseModel):
    objective: str = Field(default="", description="Objective key for single-objective, e.g. 'min_mass'")
    objectives: list[str] = Field(default_factory=list, description="Objective keys for multi-objective (2+)")
    variables: list[str] = Field(description="Parameter IDs to vary")
    bounds: list[list[float]] = Field(description="[[lo, hi], ...] parallel to variables")
    max_evals: int = 200
    algo: str = "differential_evolution"
    seed: int | None = 42
    # NSGA-II specific
    pop_size: int = 40
    n_generations: int = 30


@router.get("/config")
async def optimizer_config(
    mission_type: str | None = None,
    has_propulsion: bool = False,
    pointing_accuracy_deg: float = 1.0,
) -> dict:
    """Expose the objective + default-variable registry for the UI picker.

    If mission_type is provided, filters to only relevant objectives and variables.
    """
    from ..services.equipment_logic import filter_relevant_objectives, filter_relevant_variables

    if mission_type:
        relevant_obj_keys = set(filter_relevant_objectives(mission_type, has_propulsion))
        relevant_var_keys = set(filter_relevant_variables(mission_type, has_propulsion, pointing_accuracy_deg))
    else:
        relevant_obj_keys = set(OBJECTIVES.keys())
        relevant_var_keys = set(DEFAULT_DESIGN_VARIABLES.keys())

    return {
        "objectives": [
            {
                "key": s.key,
                "description": s.description,
                "parameter_id": s.parameter_id,
                "direction": s.direction,
                "relevant": s.key in relevant_obj_keys,
            }
            for s in OBJECTIVES.values()
        ],
        "default_variables": [
            {"id": vid, "lower": lo, "upper": hi, "relevant": vid in relevant_var_keys}
            for vid, (lo, hi) in DEFAULT_DESIGN_VARIABLES.items()
        ],
    }


async def _persist_new_run(
    session_id: str, study_id: str | None, body: OptimizeBody
) -> int:
    factory = get_session_factory()
    async with factory() as db:
        row = OptimizationRunRow(
            session_id=session_id,
            study_id=study_id,
            algo=body.algo,
            objective=body.objective,
            design_variables_json=list(body.variables),
            constraints_json=[],
            status="running",
            num_evals=0,
            best_x_json={},
            pareto_front_json=[],
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row.id


async def _update_run(run_id: int, **fields) -> None:
    factory = get_session_factory()
    async with factory() as db:
        row = await db.get(OptimizationRunRow, run_id)
        if row is None:
            return
        for k, v in fields.items():
            setattr(row, k, v)
        await db.commit()


async def _execute_run(
    run_id: int,
    session_id: str,
    body: OptimizeBody,
) -> None:
    """Background task — runs the optimiser and persists the outcome."""
    sm = get_session_manager()
    base_state = sm.get_session_state(session_id)
    if base_state is None:
        await _update_run(
            run_id,
            status="failed",
            error_message=f"Session {session_id} has no live state",
            finished_at=datetime.now(timezone.utc),
        )
        return

    from .ws import _broadcast  # local import to avoid import cycle at module load

    def progress_cb(prog: OptimizeProgress) -> None:
        payload = {
            "type": "optimize.progress",
            "run_id": prog.run_id,
            "evaluations": prog.evaluations,
            "max_evals": prog.max_evals,
            "fraction": prog.fraction,
            "best_y": prog.best_y,
            "best_x": prog.best_x,
        }
        _run_cache[run_id] = payload
        # Fire-and-forget broadcast from the optimiser's thread.
        try:
            loop = asyncio.get_event_loop_policy().get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(_broadcast(session_id, payload), loop)
        except Exception:
            pass

    is_multi = len(body.objectives) >= 2

    if is_multi:
        mo_config = MultiObjectiveConfig(
            variables=list(body.variables),
            bounds=[tuple(b) for b in body.bounds],
            objectives=list(body.objectives),
            pop_size=body.pop_size,
            n_generations=body.n_generations,
            seed=body.seed,
        )
        result = await run_multi_objective(
            run_id=run_id,
            session_id=session_id,
            base_state=base_state,
            config=mo_config,
            progress_cb=progress_cb,
        )
    else:
        config = OptimizeConfig(
            variables=list(body.variables),
            bounds=[tuple(b) for b in body.bounds],
            objective=body.objective,
            algo=body.algo,
            max_evals=body.max_evals,
            seed=body.seed,
        )
        result = await run_single_objective(
            run_id=run_id,
            session_id=session_id,
            base_state=base_state,
            config=config,
            progress_cb=progress_cb,
        )

    # Persist terminal state
    await _update_run(
        run_id,
        status=result.status,
        num_evals=result.num_evals,
        best_x_json=dict(result.best_x or {}),
        best_y=(float(result.best_y) if result.best_y is not None else None),
        pareto_front_json=result.pareto_front,
        duration_ms=float(result.duration_ms),
        error_message=result.error,
        finished_at=datetime.now(timezone.utc),
    )

    # Final WS event + cache update
    complete_payload = {
        "type": "optimize.complete",
        "run_id": run_id,
        "status": result.status,
        "best_x": result.best_x,
        "best_y": result.best_y,
        "num_evals": result.num_evals,
        "duration_ms": result.duration_ms,
        "pareto_front": result.pareto_front,
        "error": result.error,
    }
    _run_cache[run_id] = {**complete_payload, "history": result.history}
    try:
        await _broadcast(session_id, complete_payload)
    except Exception:
        pass


@router.post("/sessions/{session_id}")
async def kick_off_run(
    session_id: str,
    body: OptimizeBody,
    bg: BackgroundTasks,
) -> dict:
    """Start a new optimiser run; returns the run_id immediately."""
    sm = get_session_manager()
    sess = sm.get_session(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    is_multi = len(body.objectives) >= 2
    if is_multi:
        for obj in body.objectives:
            if obj not in OBJECTIVES:
                raise HTTPException(status_code=400, detail=f"Unknown objective {obj}")
    else:
        if not body.objective:
            raise HTTPException(status_code=400, detail="Must provide 'objective' for single-objective or 'objectives' (2+) for Pareto")
        if body.objective not in OBJECTIVES:
            raise HTTPException(status_code=400, detail=f"Unknown objective {body.objective}")
    if len(body.variables) != len(body.bounds):
        raise HTTPException(status_code=400, detail="variables and bounds must be same length")
    for var in body.variables:
        if "." not in var:
            raise HTTPException(status_code=400, detail=f"Invalid variable id: {var}")

    study_id = getattr(sess, "study_id", None)
    run_id = await _persist_new_run(session_id, study_id, body)
    bg.add_task(_execute_run, run_id, session_id, body)

    return {
        "run_id": run_id,
        "session_id": session_id,
        "objective": body.objective,
        "variables": body.variables,
        "max_evals": body.max_evals,
        "status": "queued",
    }


@router.get("/runs/{run_id}")
async def get_run(run_id: int) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        row = await db.get(OptimizationRunRow, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        payload = {
            "id": row.id,
            "session_id": row.session_id,
            "study_id": row.study_id,
            "algo": row.algo,
            "objective": row.objective,
            "variables": list(row.design_variables_json or []),
            "status": row.status,
            "num_evals": row.num_evals,
            "best_x": dict(row.best_x_json or {}),
            "best_y": row.best_y,
            "pareto_front": list(row.pareto_front_json or []),
            "duration_ms": row.duration_ms,
            "error": row.error_message,
            "created_at": (row.created_at or datetime.now(timezone.utc)).isoformat(),
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        }
        # Splice in any live progress from the cache
        cached = _run_cache.get(run_id)
        if cached:
            payload["latest_event"] = cached
        return payload


@router.get("/runs")
async def list_runs(limit: int = 20) -> list[dict]:
    factory = get_session_factory()
    async with factory() as db:
        stmt = (
            select(OptimizationRunRow)
            .order_by(OptimizationRunRow.created_at.desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": r.id,
                "session_id": r.session_id,
                "objective": r.objective,
                "status": r.status,
                "num_evals": r.num_evals,
                "best_y": r.best_y,
                "duration_ms": r.duration_ms,
                "created_at": (r.created_at or datetime.now(timezone.utc)).isoformat(),
            }
            for r in rows
        ]


class SensitivityRequest(BaseModel):
    """Request for Morris screening sensitivity analysis."""
    variables: list[str]
    bounds: list[tuple[float, float]]
    objective: str = "min_mass"
    num_trajectories: int = 10
    levels: int = 4


@router.post("/sensitivity/{session_id}")
async def run_sensitivity(session_id: str, req: SensitivityRequest) -> dict:
    """Run Morris screening sensitivity analysis.

    Returns the elementary effects (mean and std) for each variable,
    indicating which variables have the most influence on the objective.
    """
    import numpy as np
    from ..services.optimizer import OBJECTIVES
    from ..services.evaluator import CandidateEvaluator
    from spacecdf_common.agents.base import DesignState

    if req.objective not in OBJECTIVES:
        raise HTTPException(400, f"Unknown objective: {req.objective}")

    obj_spec = OBJECTIVES[req.objective]
    n_vars = len(req.variables)
    if n_vars == 0:
        raise HTTPException(400, "Need at least one variable")

    bounds = np.array(req.bounds)
    evaluator = CandidateEvaluator()
    base_state = DesignState()

    # Morris method: generate trajectories
    results_per_var: dict[str, list[float]] = {v: [] for v in req.variables}

    for _ in range(req.num_trajectories):
        # Random base point in [0,1]^n, quantised to `levels` grid
        x_base = np.random.randint(0, req.levels, size=n_vars) / (req.levels - 1)

        # Evaluate base point
        overrides_base = {
            req.variables[j]: float(bounds[j, 0] + x_base[j] * (bounds[j, 1] - bounds[j, 0]))
            for j in range(n_vars)
        }
        res_base = await evaluator.evaluate(base_state, overrides_base)
        y_base = res_base.parameters.get(obj_spec.parameter_id, 0.0)

        # Perturb each variable one at a time
        delta = 1.0 / (req.levels - 1)
        for j in range(n_vars):
            x_pert = x_base.copy()
            x_pert[j] = min(1.0, x_pert[j] + delta)
            overrides_pert = {
                req.variables[k]: float(bounds[k, 0] + x_pert[k] * (bounds[k, 1] - bounds[k, 0]))
                for k in range(n_vars)
            }
            res_pert = await evaluator.evaluate(base_state, overrides_pert)
            y_pert = res_pert.parameters.get(obj_spec.parameter_id, 0.0)

            # Elementary effect
            ee = (y_pert - y_base) / (delta * (bounds[j, 1] - bounds[j, 0]))
            results_per_var[req.variables[j]].append(ee)

    # Compute Morris indices: mu* (mean of absolute EE) and sigma (std of EE)
    sensitivity = []
    for v in req.variables:
        ees = results_per_var[v]
        if ees:
            mu_star = float(np.mean(np.abs(ees)))
            sigma = float(np.std(ees))
        else:
            mu_star, sigma = 0.0, 0.0
        sensitivity.append({
            "variable": v,
            "mu_star": round(mu_star, 4),
            "sigma": round(sigma, 4),
            "classification": "important" if mu_star > 0.1 else "negligible",
        })

    # Sort by importance
    sensitivity.sort(key=lambda s: s["mu_star"], reverse=True)

    return {
        "objective": req.objective,
        "num_trajectories": req.num_trajectories,
        "total_evals": req.num_trajectories * (n_vars + 1),
        "sensitivity": sensitivity,
    }
