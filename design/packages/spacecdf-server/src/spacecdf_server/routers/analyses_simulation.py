"""Mission simulation closure routes (SCDF-173, design SCDF-170 §2.1).

    POST /api/studies/{study_id}/analyses/mission_simulation/run?option_id=&n_orbits=
         start_run -> build_context -> run_mission_simulation -> ResultsSink.publish
         -> finish_run -> refresh_inputs_hash; returns
         {run_id, summary, parameters, conflicts, warnings, stale: false}
    GET  /api/studies/{study_id}/analyses/mission_simulation?option_id=
         last run (+ ``stale``, ``summary``) and its unresolved conflicts
    GET  /api/analyses/runs/{run_id}/series
         the stored series JSON (t_s, mode, soc_pct, p_gen_w, p_load_w, data_buffer_gb, temp_c)

``analysis_started`` is broadcast by ``start_run`` and ``analysis_completed``
by ``ResultsSink.publish`` (both via ``routers._arcadia_events``); a failed
run broadcasts ``analysis_completed`` with ``status='failed'`` from here.

Note: ``analyses_common`` registers ``GET /studies/{id}/analyses/{analysis}``
before this router, so the plain GET is served by that generic route (same
run dict with ``stale``); the handler here is kept for direct mounting and
adds the conflicts.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from ..db import analysis_repo
from ..services import analysis_results
from ..services.analysis_context import build_context, context_hash
from ..services.analysis_results import ResultsSink, finish_run, input_keys_for, load_series, refresh_inputs_hash, start_run
from ..services.mission_simulation import ANALYSIS, run_mission_simulation
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/studies/{study_id}/analyses/mission_simulation/run")
async def run_simulation(study_id: str, option_id: str | None = Query(None),
                         n_orbits: int = Query(15, ge=1, le=200)) -> dict:
    ctx = await build_context(study_id, option_id=option_id)
    if not ctx.elements:
        raise HTTPException(400, f"Study {study_id} has no design elements to simulate")
    run_id = await start_run(study_id, ANALYSIS, context_hash(ctx, input_keys_for(ANALYSIS)), option_id)
    try:
        out = await run_mission_simulation(ctx, n_orbits=n_orbits)
        pub = await ResultsSink().publish(study_id, ANALYSIS, parameters=out.parameters, conflicts=out.conflicts,
                                          notes=out.warnings, option_id=option_id, run_id=run_id, ctx=ctx)
        summary = {**out.summary, "parameters_written": len(pub.written), "shadowed": [s["name"] for s in pub.shadowed],
                   "conflicts": len(pub.conflicts)}
        run = await finish_run(run_id, "ok", summary=summary, series=out.series)
        await refresh_inputs_hash(run_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("mission simulation failed for %s", study_id)
        await finish_run(run_id, "failed", summary={"error": str(exc)})
        await broadcast_mutation(study_id, "analysis_completed", "analysis", ANALYSIS,
                                 {"run_id": run_id, "option_id": option_id, "status": "failed", "error": str(exc)})
        raise HTTPException(500, f"Mission simulation failed: {exc}") from exc
    return {
        "run_id": run_id, "analysis": ANALYSIS, "option_id": option_id, "status": run["status"],
        "summary": summary,
        "parameters": [{"name": w["name"], "value": w["value"], "element_id": w["element_id"]} for w in pub.written],
        "shadowed": [{"name": s["name"], "value": s["value"], "element_id": s["element_id"]} for s in pub.shadowed],
        "conflicts": pub.conflicts, "warnings": out.warnings, "stale": False,
    }


@router.get("/studies/{study_id}/analyses/mission_simulation")
async def get_simulation(study_id: str, option_id: str | None = Query(None)) -> dict:
    run = await analysis_results.get_last_run(study_id, ANALYSIS, option_id=option_id)
    if run is None:
        raise HTTPException(404, f"No {ANALYSIS} run for study {study_id}")
    run["conflicts"] = await analysis_repo.list_conflicts(study_id, option_id=option_id, analysis=ANALYSIS)
    return run


@router.get("/analyses/runs/{run_id}/series")
async def get_run_series(run_id: str) -> dict:
    run = await analysis_repo.get_run(run_id)
    if run is None:
        raise HTTPException(404, f"Run {run_id} not found")
    series = load_series(run.get("series_ref"))
    if series is None:
        raise HTTPException(404, f"Run {run_id} has no stored series")
    return {"run_id": run_id, "analysis": run["analysis"], "series": series}
