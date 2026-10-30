"""Physics closure routes (SCDF-176, design SCDF-170 §2.4) + the study-driven
FMECA routes of SCDF-177 (defined in ``routers.fmeca.study_router`` and
mounted here so they live under ``/api/studies/...``).

    POST  /api/studies/{study_id}/analyses/physics/run?option_id=
          start_run -> build_context -> run_physics -> ResultsSink.publish
          -> finish_run -> refresh_inputs_hash; returns
          {run_id, summary, parameters, conflicts, warnings, stale: false}
    GET   /api/studies/{study_id}/analyses/physics?option_id=
          last run (+ ``stale``) and its unresolved conflicts
    GET   /api/studies/{study_id}/analyses/physics/placement?option_id=
          the current placement (positions, auto-placed ids, envelope) without running
    PATCH /api/elements/{element_id}/position   {x, y, z} | null
          write-through position_json on the element (bumps the version,
          persists, broadcasts ``element_updated``); the physics run goes stale
    POST  /api/studies/{study_id}/analyses/fmeca/run?option_id=   (SCDF-177)
    GET   /api/studies/{study_id}/analyses/fmeca?option_id=

Series of a run: ``GET /api/analyses/runs/{run_id}/series`` (analyses_simulation).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import analysis_repo
from ..db.element_repo import db_update_element
from ..services import analysis_results
from ..services.analysis_context import build_context, context_hash
from ..services.analysis_results import ResultsSink, finish_run, input_keys_for, refresh_inputs_hash, start_run
from ..services.physics_closure import ANALYSIS, place_elements, run_physics
from . import elements as elements_router
from ._arcadia_events import broadcast_mutation
from .fmeca import study_router as fmeca_study_router

logger = logging.getLogger(__name__)
router = APIRouter()
router.include_router(fmeca_study_router)


class PositionBody(BaseModel):
    x: float | None = None
    y: float | None = None
    z: float | None = None


@router.post("/studies/{study_id}/analyses/physics/run")
async def run_physics_closure(study_id: str, option_id: str | None = Query(None)) -> dict:
    ctx = await build_context(study_id, option_id=option_id)
    if not ctx.elements:
        raise HTTPException(400, f"Study {study_id} has no design elements")
    run_id = await start_run(study_id, ANALYSIS, context_hash(ctx, input_keys_for(ANALYSIS)), option_id)
    try:
        out = await run_physics(ctx)
        pub = await ResultsSink().publish(study_id, ANALYSIS, parameters=out.parameters, conflicts=out.conflicts,
                                          notes=out.warnings, option_id=option_id, run_id=run_id, ctx=ctx)
        summary = {**out.summary, "parameters_written": len(pub.written), "shadowed": [s["name"] for s in pub.shadowed],
                   "conflicts": len(pub.conflicts)}
        run = await finish_run(run_id, "ok", summary=summary, series=out.series)
        await refresh_inputs_hash(run_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("physics closure failed for %s", study_id)
        await finish_run(run_id, "failed", summary={"error": str(exc)})
        await broadcast_mutation(study_id, "analysis_completed", "analysis", ANALYSIS,
                                 {"run_id": run_id, "option_id": option_id, "status": "failed", "error": str(exc)})
        raise HTTPException(500, f"Physics closure failed: {exc}") from exc
    return {
        "run_id": run_id, "analysis": ANALYSIS, "option_id": option_id, "status": run["status"],
        "summary": summary,
        "parameters": [{"name": w["name"], "value": w["value"], "element_id": w["element_id"]} for w in pub.written],
        "shadowed": [{"name": s["name"], "value": s["value"], "element_id": s["element_id"]} for s in pub.shadowed],
        "conflicts": pub.conflicts, "warnings": out.warnings, "stale": False,
    }


@router.get("/studies/{study_id}/analyses/physics/placement")
async def get_placement(study_id: str, option_id: str | None = Query(None)) -> dict:
    ctx = await build_context(study_id, option_id=option_id)
    pl = place_elements(ctx)
    return {
        "study_id": study_id, "envelope_m": list(pl.envelope_m), "envelope_source": pl.envelope_source,
        "envelope_element_id": pl.envelope_element_id, "auto_placed": pl.auto_placed, "warnings": pl.warnings,
        "items": [{"element_id": it.element_id, "name": it.name, "element_type": it.element_type, "domain": it.domain,
                   "mass_kg": it.mass_kg, "dims_m": list(it.dims_m), "position_m": it.position_m, "source": it.source,
                   "quantity": it.quantity} for it in pl.items],
    }


@router.get("/studies/{study_id}/analyses/physics")
async def get_physics(study_id: str, option_id: str | None = Query(None)) -> dict:
    run = await analysis_results.get_last_run(study_id, ANALYSIS, option_id=option_id)
    if run is None:
        raise HTTPException(404, f"No {ANALYSIS} run for study {study_id}")
    run["conflicts"] = await analysis_repo.list_conflicts(study_id, option_id=option_id, analysis=ANALYSIS)
    return run


@router.patch("/elements/{element_id}/position")
async def set_element_position(element_id: str, body: PositionBody | None = None) -> dict:
    """Set (or clear, with an empty body / all-null) the body-frame position of an element."""
    el = elements_router._elements.get(element_id)
    if not el or el.get("deleted_at"):
        raise HTTPException(404, f"Element {element_id} not found")
    if body is None or (body.x is None and body.y is None and body.z is None):
        el["position_json"] = None
    else:
        cur = el.get("position_json") if isinstance(el.get("position_json"), list) and len(el["position_json"]) == 3 else [0.0, 0.0, 0.0]
        el["position_json"] = [float(body.x if body.x is not None else cur[0]),
                               float(body.y if body.y is not None else cur[1]),
                               float(body.z if body.z is not None else cur[2])]
    el["version"] = int(el.get("version") or 0) + 1
    await db_update_element(element_id, el)
    try:
        from .ws import _broadcast_study
        await _broadcast_study(el["study_id"], {"type": "element_updated", "element": el})
    except Exception:  # pragma: no cover - defensive
        logger.debug("broadcast failed", exc_info=True)
    return el
