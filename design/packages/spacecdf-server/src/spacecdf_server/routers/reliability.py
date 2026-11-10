"""Reliability analysis and FMEA/FMECA worksheet (wave 3, 3.A5; PI addendum). Owner A.

Tables ``reliability_blocks`` and ``fmea_rows`` (``db/models_reliability.py``); the service is
``services/reliability_model.py``. PDR-EC-05 (wired by R) reads ``reliability_model.evidence``.

    GET   /studies/{id}/reliability            blocks, result over the mission-success horizon, FMEA
    POST  /studies/{id}/reliability/run        propose the blocks the study lacks, compute R(t)
    PATCH /studies/{id}/reliability/blocks/{b} edit a block (rate, source, k of n, duty)
    GET   /studies/{id}/reliability/evidence   what PDR-EC-05 reads
    GET   /studies/{id}/fmea                   the worksheet
    POST  /studies/{id}/fmea                   a row of the team's own
    POST  /studies/{id}/fmea/propose           failure modes per unit, linked to FDIR and risks
    PATCH /studies/{id}/fmea/{row}             edit a row (criticality recomputed)
    DELETE /studies/{id}/fmea/{row}
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..db.models_reliability import FmeaRow, ReliabilityBlockRow
from ..services import reliability_model as rm
from ..services import study_rows as sr
from .studies import get_study_store

router = APIRouter()


def _study_or_404(study_id: str):
    s = get_study_store().get(study_id)
    if s is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return s


@router.get("/studies/{study_id}/reliability")
async def get_reliability(study_id: str) -> dict:
    _study_or_404(study_id)
    return await rm.get(study_id)


@router.post("/studies/{study_id}/reliability/run")
async def run_reliability(study_id: str, replace: bool = False) -> dict:
    _study_or_404(study_id)
    out = await rm.run(study_id, replace=replace)
    return {**(await rm.get(study_id)), "result": out["result"]}


@router.put("/studies/{study_id}/reliability/horizon")
async def put_reliability_horizon(study_id: str, body: dict[str, Any]) -> dict:
    """The mission-success horizon (``success_horizon_months``, e.g. 12 for MIS-LIF-02) and,
    optionally, the reliability target it applies to. ``{"success_horizon_months": null}`` clears
    it (the design life is then used)."""
    from ..db.study_repo import db_save_study
    study = _study_or_404(study_id)
    req = study.requirements
    if "success_horizon_months" in body:
        v = body.get("success_horizon_months")
        if v is not None:
            try:
                v = float(v)
            except (TypeError, ValueError):
                raise HTTPException(422, "success_horizon_months must be a number of months")
            if not 0 < v <= 600:
                raise HTTPException(422, "success_horizon_months must be within 0-600 months")
        req.success_horizon_months = v
    if body.get("reliability_target") is not None:
        t = float(body["reliability_target"])
        if not 0 < t <= 1:
            raise HTTPException(422, "reliability_target must be within 0-1")
        req.reliability_target = t
    await db_save_study(study)
    return {"study_id": study_id, "success_horizon_months": req.success_horizon_months,
            "reliability_target": req.reliability_target, "horizon": rm.horizon(study)}


@router.get("/studies/{study_id}/reliability/evidence")
async def reliability_evidence(study_id: str) -> dict:
    _study_or_404(study_id)
    return await rm.evidence(study_id)


_BLOCK_FIELDS = ("name", "subsystem", "arrangement", "k", "n", "failure_rate_fit", "rate_source", "duty_cycle",
                 "parent_block")


@router.patch("/studies/{study_id}/reliability/blocks/{block_id}")
async def update_block(study_id: str, block_id: str, body: dict[str, Any]) -> dict:
    _study_or_404(study_id)
    b = await sr.get_row(ReliabilityBlockRow, block_id)
    if b is None or b.get("study_id") != study_id:
        raise HTTPException(404, "block not found")
    f = {k: body[k] for k in _BLOCK_FIELDS if k in body}
    if "failure_rate_fit" in f and "rate_source" not in f:
        f["rate_source"] = "user"
    data = dict(b.get("data_json") or {})
    for k in ("one_shot", "mission_success"):
        if k in body:
            data[k] = body[k]
    f["data_json"] = data
    f["origin"] = "user"
    await sr.update_row(ReliabilityBlockRow, block_id, f)
    await rm.run(study_id)
    return await sr.get_row(ReliabilityBlockRow, block_id)


@router.get("/studies/{study_id}/fmea")
async def list_fmea(study_id: str) -> dict:
    _study_or_404(study_id)
    d = await rm.get(study_id)
    return {"study_id": study_id, "items": d["fmea"], "counts": d["counts"], "critical_threshold": rm.CRITICAL}


@router.post("/studies/{study_id}/fmea")
async def create_fmea_row(study_id: str, body: dict[str, Any]) -> dict:
    _study_or_404(study_id)
    return await rm.create_fmea(study_id, body)


@router.post("/studies/{study_id}/fmea/propose")
async def propose_fmea(study_id: str, replace: bool = False) -> dict:
    _study_or_404(study_id)
    return await rm.propose_fmea(study_id, replace=replace)


@router.patch("/studies/{study_id}/fmea/{row_id}")
async def update_fmea_row(study_id: str, row_id: str, body: dict[str, Any]) -> dict:
    _study_or_404(study_id)
    row = await sr.get_row(FmeaRow, row_id)
    if row is None or row.get("study_id") != study_id:
        raise HTTPException(404, "FMEA row not found")
    return await rm.update_fmea(row, body)


@router.delete("/studies/{study_id}/fmea/{row_id}")
async def delete_fmea_row(study_id: str, row_id: str) -> dict:
    _study_or_404(study_id)
    n = await sr.delete_rows(FmeaRow, study_id, ids=[row_id])
    if not n:
        raise HTTPException(404, "FMEA row not found")
    return {"deleted": row_id}
