"""Ground segment closure routes (SCDF-174, design SCDF-170 §2.2).

    POST   /api/studies/{study_id}/analyses/ground_segment/run?option_id=
           start_run -> build_context -> run_ground_segment -> ResultsSink.publish
           -> finish_run -> refresh_inputs_hash; returns
           {run_id, summary, parameters, conflicts, warnings, stale: false}
    GET    /api/studies/{study_id}/analyses/ground_segment?option_id=
           last run (+ ``stale``, ``summary``) and its unresolved conflicts
    GET    /api/studies/{study_id}/ground-stations
           {selected: [...station elements + KB props...], catalogue: [...KB stations...]}
    POST   /api/studies/{study_id}/ground-stations {kb_station_id, min_elevation_deg?}
           persists the selection as a ``segment='ground'`` component element
           (``kb_component_id`` = station id, station props in ``performance``)
           under the study's ground-segment element (created when missing)
    DELETE /api/studies/{study_id}/ground-stations/{element_id}
           soft-deletes the station element (through ``routers.elements``)

The station endpoints go through ``routers.elements.create_element`` /
``delete_element`` so the write-through cache, DB and WebSocket broadcasts
stay the single path. ``analysis_started`` / ``analysis_completed`` are
broadcast by ``start_run`` / ``ResultsSink.publish``; a failed run broadcasts
``analysis_completed`` with ``status='failed'`` from here.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import analysis_repo
from ..services import analysis_results
from ..services.analysis_context import build_context, context_hash
from ..services.analysis_results import ResultsSink, finish_run, input_keys_for, refresh_inputs_hash, start_run
from ..services.ground_closure import ANALYSIS, run_ground_segment
from . import elements as elements_router
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)
router = APIRouter()

STATION_PROPS = ("lat", "lon", "alt_m", "bands", "antenna_m", "g_over_t_db_k", "eirp_dbw", "min_elevation_deg", "operator")


class StationAdd(BaseModel):
    kb_station_id: str
    min_elevation_deg: float | None = None


def _kb_stations() -> list[dict]:
    try:
        from spacecdf_kb.loader import KnowledgeBase
        return KnowledgeBase().ground_stations
    except Exception:
        logger.warning("KB ground stations unavailable", exc_info=True)
        return []


def _study_elements(study_id: str) -> list[dict]:
    return [e for e in elements_router._elements.values()
            if e.get("study_id") == study_id and not e.get("deleted_at")]


def _station_elements(study_id: str) -> list[dict]:
    return [e for e in _study_elements(study_id)
            if e.get("segment") == "ground" and e.get("kb_component_id") and e.get("element_type") in ("system", "component")]


def _serialise(el: dict, catalogue: dict[str, dict]) -> dict:
    kb = catalogue.get(el.get("kb_component_id") or "", {})
    perf = el.get("performance_json") or el.get("performance") or {}
    props = {k: (perf.get(k) if perf.get(k) is not None else kb.get(k)) for k in STATION_PROPS}
    return {"element_id": el["id"], "kb_station_id": el.get("kb_component_id"), "name": el.get("name"),
            "parent_id": el.get("parent_id"), "version": el.get("version"), **props, "in_catalogue": bool(kb)}


async def _ensure_ground_segment(study_id: str) -> dict:
    els = _study_elements(study_id)
    for e in els:
        if e.get("element_type") == "segment" and e.get("segment") == "ground":
            return e
    root = next((e for e in els if e.get("element_type") == "mission"), None)
    if root is None:
        ids = {e["id"] for e in els}
        root = next((e for e in els if not e.get("parent_id") or e["parent_id"] not in ids), None)
    body = elements_router.ElementCreate(name="Ground Segment", element_type="segment", segment="ground",
                                         parent_id=root["id"] if root else None, subsystem_domain="ground",
                                         description="Ground segment (created by the ground-station picker)")
    return await elements_router.create_element(body, study_id=study_id)


def _placeholder_station(study_id: str, segment_id: str) -> dict | None:
    """The default tree's "Ground Station" system: no KB station, nothing under it."""
    els = _study_elements(study_id)
    has_kids = {e.get("parent_id") for e in els}
    for e in els:
        if (e.get("parent_id") == segment_id and e.get("element_type") == "system" and not e.get("kb_component_id")
                and e["id"] not in has_kids and str(e.get("name") or "") in ("Ground Station", "DSN Ground Station")):
            return e
    return None


@router.get("/studies/{study_id}/ground-stations")
async def list_ground_stations(study_id: str) -> dict:
    catalogue = _kb_stations()
    by_id = {s.get("id"): s for s in catalogue}
    selected = [_serialise(e, by_id) for e in _station_elements(study_id)]
    chosen = {s["kb_station_id"] for s in selected}
    return {"study_id": study_id, "selected": selected,
            "catalogue": [{**s, "selected": s.get("id") in chosen} for s in catalogue]}


@router.post("/studies/{study_id}/ground-stations")
async def add_ground_station(study_id: str, body: StationAdd) -> dict:
    catalogue = _kb_stations()
    kb = next((s for s in catalogue if s.get("id") == body.kb_station_id or s.get("name") == body.kb_station_id), None)
    if kb is None:
        raise HTTPException(404, f"Ground station {body.kb_station_id!r} not in the catalogue")
    if any(e.get("kb_component_id") == kb.get("id") for e in _station_elements(study_id)):
        raise HTTPException(409, f"Ground station {kb.get('id')} is already selected")
    segment = await _ensure_ground_segment(study_id)
    perf = {k: kb.get(k) for k in STATION_PROPS if kb.get(k) is not None}
    if body.min_elevation_deg is not None:
        perf["min_elevation_deg"] = body.min_elevation_deg
    # A ground station is a level-2 element of the ground segment (ECSS product tree,
    # services/product_tree.py); the default tree's empty "Ground Station" placeholder is
    # taken over by the first station picked.
    placeholder = _placeholder_station(study_id, segment["id"])
    if placeholder is not None:
        upd = {"name": str(kb.get("name") or kb.get("id")), "kb_component_id": str(kb.get("id")),
               "subsystem_domain": "ground", "manufacturer": kb.get("operator"),
               "description": str(kb.get("notes") or ""),
               "performance": {**(placeholder.get("performance") or {}), **perf}}
        placeholder["subsystem_domain"] = "ground"
        el = await elements_router.apply_element_update(placeholder, {k: v for k, v in upd.items() if v is not None})
        await broadcast_mutation(study_id, "ground_station_added", "element", el["id"],
                                 {"kb_station_id": kb.get("id"), "analysis": ANALYSIS})
        return _serialise(el, {kb.get("id"): kb})
    create = elements_router.ElementCreate(
        name=str(kb.get("name") or kb.get("id")), element_type="system", parent_id=segment["id"],
        subsystem_domain="ground", segment="ground", kb_component_id=str(kb.get("id")),
        manufacturer=kb.get("operator"), description=str(kb.get("notes") or ""), performance=perf,
    )
    el = await elements_router.create_element(create, study_id=study_id)
    await broadcast_mutation(study_id, "ground_station_added", "element", el["id"],
                             {"kb_station_id": kb.get("id"), "analysis": ANALYSIS})
    return _serialise(el, {kb.get("id"): kb})


@router.delete("/studies/{study_id}/ground-stations/{element_id}")
async def remove_ground_station(study_id: str, element_id: str) -> dict:
    el = elements_router._elements.get(element_id)
    if el is None or el.get("study_id") != study_id or el.get("deleted_at"):
        raise HTTPException(404, f"Ground station element {element_id} not found in study {study_id}")
    if el.get("segment") != "ground":
        raise HTTPException(400, f"Element {element_id} is not a ground-segment element")
    res = await elements_router.delete_element(element_id)
    await broadcast_mutation(study_id, "ground_station_removed", "element", element_id,
                             {"kb_station_id": el.get("kb_component_id"), "analysis": ANALYSIS})
    return {**res, "kb_station_id": el.get("kb_component_id")}


@router.post("/studies/{study_id}/analyses/ground_segment/run")
async def run_ground(study_id: str, option_id: str | None = Query(None)) -> dict:
    ctx = await build_context(study_id, option_id=option_id)
    if not ctx.elements:
        raise HTTPException(400, f"Study {study_id} has no design elements")
    run_id = await start_run(study_id, ANALYSIS, context_hash(ctx, input_keys_for(ANALYSIS)), option_id)
    try:
        out = await run_ground_segment(ctx)
        pub = await ResultsSink().publish(study_id, ANALYSIS, parameters=out.parameters, conflicts=out.conflicts,
                                          notes=out.warnings, option_id=option_id, run_id=run_id, ctx=ctx)
        summary = {**out.summary, "parameters_written": len(pub.written), "shadowed": [s["name"] for s in pub.shadowed],
                   "conflicts": len(pub.conflicts)}
        run = await finish_run(run_id, "ok", summary=summary, series=out.series)
        await refresh_inputs_hash(run_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("ground segment closure failed for %s", study_id)
        await finish_run(run_id, "failed", summary={"error": str(exc)})
        await broadcast_mutation(study_id, "analysis_completed", "analysis", ANALYSIS,
                                 {"run_id": run_id, "option_id": option_id, "status": "failed", "error": str(exc)})
        raise HTTPException(500, f"Ground segment closure failed: {exc}") from exc
    return {
        "run_id": run_id, "analysis": ANALYSIS, "option_id": option_id, "status": run["status"],
        "summary": summary,
        "parameters": [{"name": w["name"], "value": w["value"], "element_id": w["element_id"]} for w in pub.written],
        "shadowed": [{"name": s["name"], "value": s["value"], "element_id": s["element_id"]} for s in pub.shadowed],
        "conflicts": pub.conflicts, "warnings": out.warnings, "stale": False,
    }


@router.get("/studies/{study_id}/analyses/ground_segment")
async def get_ground(study_id: str, option_id: str | None = Query(None)) -> dict:
    run = await analysis_results.get_last_run(study_id, ANALYSIS, option_id=option_id)
    if run is None:
        raise HTTPException(404, f"No {ANALYSIS} run for study {study_id}")
    run["conflicts"] = await analysis_repo.list_conflicts(study_id, option_id=option_id, analysis=ANALYSIS)
    return run
