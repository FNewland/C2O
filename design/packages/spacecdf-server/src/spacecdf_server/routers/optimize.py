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
    OptimizeConfig,
    OptimizeProgress,
    run_single_objective,
)
from ..services.session_manager import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory run cache — useful while a run is still executing (DB holds the
# final snapshot). run_id -> latest progress/history payload.
_run_cache: dict[int, dict] = {}


class OptimizeBody(BaseModel):
    objective: str = Field(description="Objective key, e.g. 'min_mass' or 'min_cost'")
    variables: list[str] = Field(description="Parameter IDs to vary")
    bounds: list[list[float]] = Field(description="[[lo, hi], ...] parallel to variables")
    max_evals: int = 200
    algo: str = "differential_evolution"
    seed: int | None = 42


@router.get("/config")
async def optimizer_config() -> dict:
    """Expose the objective + default-variable registry for the UI picker."""
    return {
        "objectives": [
            {
                "key": s.key,
                "description": s.description,
                "parameter_id": s.parameter_id,
                "direction": s.direction,
            }
            for s in OBJECTIVES.values()
        ],
        "default_variables": [
            {"id": vid, "lower": lo, "upper": hi}
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
        duration_ms=float(result.duration_ms),
        error_message=result.error,
        finished_at=datetime.now(timezone.utc),
    )

    # Final WS event + cache update
    _run_cache[run_id] = {
        "type": "optimize.complete",
        "run_id": run_id,
        "status": result.status,
        "best_x": result.best_x,
        "best_y": result.best_y,
        "num_evals": result.num_evals,
        "duration_ms": result.duration_ms,
        "history": result.history,
        "error": result.error,
    }
    try:
        await _broadcast(session_id, {
            "type": "optimize.complete",
            "run_id": run_id,
            "status": result.status,
            "best_x": result.best_x,
            "best_y": result.best_y,
            "num_evals": result.num_evals,
            "duration_ms": result.duration_ms,
        })
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
