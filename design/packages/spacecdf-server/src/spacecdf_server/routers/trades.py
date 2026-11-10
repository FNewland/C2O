"""SpaceCDF — trade studies of a study (W6.01/W6.03, Nov 2026).

Mounted under ``/api`` (included by routers/gates.py, which owned the single Pugh record before):

* ``GET    /studies/{sid}/trades``                 every trade with its evaluation
* ``POST   /studies/{sid}/trades``                 new trade ({"state": {...}}; id T-nn unless given)
* ``POST   /studies/{sid}/trades/import``          trades in the ``trades.yaml`` format (+ ``pairwise_inputs``)
* ``POST   /studies/{sid}/trades/report``          the trade-off report (.docx, ``?lang=en|fr``)
* ``GET    /studies/{sid}/trades/{tid}``           one trade: ``{id, state, version, evaluation}``
* ``PUT    /studies/{sid}/trades/{tid}``           save ``{"state", "version"}`` (409 when stale); top-level
                                                   keys the body leaves out are kept (links, decision)
* ``DELETE /studies/{sid}/trades/{tid}``
* ``POST   /studies/{sid}/trades/{tid}/decision``  ``{"selected", "rationale", "seat"}``: records the
                                                   decision on the trade (which is kept) and writes the
                                                   study decision record (``study.decision_records``)

``pugh`` (the old single record, the Decide tab before Nov 2026) is an alias of ``T-01``.
"""
from __future__ import annotations

import io
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services import trades as tr

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_TRADES = 60
MAX_STATE_BYTES = 200_000


def _study(study_id: str):
    from .gates import _study_or_404
    return _study_or_404(study_id)


async def _save(study, kind: str) -> None:
    from .gates import _broadcast, _save as save_study
    await save_study(study)
    await _broadcast(study.id, "study_records_changed", {"kind": kind})


def _records(study) -> dict[str, dict[str, Any]]:
    return tr.normalise_records(getattr(study, "trade_records", None))


def _public(tid: str, rec: dict[str, Any]) -> dict[str, Any]:
    state = rec.get("state") or tr.clean_state({}, tid)
    return {"id": tid, "state": state, "version": int(rec.get("version") or 0), "evaluation": tr.evaluate(state)}


@router.get("/studies/{study_id}/trades")
async def list_trades(study_id: str) -> dict:
    recs = _records(_study(study_id))
    items = [_public(k, v) for k, v in recs.items()]
    return {"study_id": study_id, "count": len(items), "items": items}


class TradeCreate(BaseModel):
    state: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None


@router.post("/studies/{study_id}/trades")
async def create_trade(study_id: str, body: TradeCreate) -> dict:
    study = _study(study_id)
    recs = _records(study)
    if len(recs) >= MAX_TRADES:
        raise HTTPException(413, "Too many trades in this study")
    tid = (body.id or body.state.get("id") or "").strip() or tr.next_id(recs)
    tid = tr.resolve_id(tid)
    if not tr.ID_RE.match(tid):
        raise HTTPException(422, f"Bad trade id: {tid!r}")
    if tid in recs:
        raise HTTPException(409, {"code": "exists", "message": f"Trade {tid} exists"})
    _check_size(body.state)
    recs[tid] = {"state": tr.clean_state(body.state, tid), "version": 1}
    study.trade_records = recs
    await _save(study, f"trade:{tid}")
    return _public(tid, recs[tid])


class TradeImport(BaseModel):
    trades: list[dict[str, Any]] = Field(default_factory=list, max_length=MAX_TRADES)
    pairwise_inputs: dict[str, Any] = Field(default_factory=dict)
    replace: bool = False      # replace trades with the same id (else they are skipped)


@router.post("/studies/{study_id}/trades/import")
async def import_trades(study_id: str, body: TradeImport) -> dict:
    """Trades in the teaching-baseline file format (``trades.yaml``). Each keeps its id, its
    weights (from the pairwise inputs when given) and its links."""
    study = _study(study_id)
    recs = _records(study)
    added, replaced, skipped = [], [], []
    for t in body.trades:
        if not isinstance(t, dict) or not t.get("id"):
            continue
        tid = tr.resolve_id(str(t["id"]).strip())
        if not tr.ID_RE.match(tid):
            skipped.append(tid)
            continue
        if tid in recs and not body.replace:
            skipped.append(tid)
            continue
        state = tr.from_file_trade({**t, "id": tid}, (body.pairwise_inputs or {}).get(tid))
        (replaced if tid in recs else added).append(tid)
        recs[tid] = {"state": state, "version": int((recs.get(tid) or {}).get("version") or 0) + 1}
    if len(recs) > MAX_TRADES:
        raise HTTPException(413, "Too many trades in this study")
    if added or replaced:
        study.trade_records = recs
        await _save(study, "trades")
    return {"added": added, "replaced": replaced, "skipped": skipped,
            "items": [_public(k, recs[k]) for k in (*added, *replaced)]}


@router.post("/studies/{study_id}/trades/report")
async def trades_report(study_id: str, lang: str = Query("en")) -> StreamingResponse:
    """The trade-off report (gate product ``trade_reports``) as a Word document."""
    study = _study(study_id)
    from ..services.docx.trades import generate_trades_docx
    from ..services.export_context import collect
    sx = await collect(study_id, lang=lang, sections=["need", "mission", "requirements", "risks", "trades",
                                                     "decisions"])
    data = generate_trades_docx(sx, lang=lang)
    name = (study.name or "study").replace(" ", "_")
    return StreamingResponse(io.BytesIO(data),
                             media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             headers={"Content-Disposition": f'attachment; filename="SpaceCDF_Trade_reports_{name}.docx"'})


@router.get("/studies/{study_id}/trades/{trade_id}")
async def get_trade(study_id: str, trade_id: str) -> dict:
    tid = tr.resolve_id(trade_id)
    recs = _records(_study(study_id))
    if tid not in recs:
        if trade_id == tr.LEGACY_KEY:      # the old Decide tab expects an empty record
            return {"id": tid, "state": None, "version": 0, "evaluation": None}
        raise HTTPException(404, f"Unknown trade: {trade_id}")
    return _public(tid, recs[tid])


class TradeBody(BaseModel):
    state: dict[str, Any]
    version: int | None = None   # the version the client edited; None = overwrite


def _check_size(state: dict[str, Any]) -> None:
    if len(json.dumps(state, default=str)) > MAX_STATE_BYTES:
        raise HTTPException(413, "Trade record too large")


@router.put("/studies/{study_id}/trades/{trade_id}")
async def put_trade(study_id: str, trade_id: str, body: TradeBody) -> dict:
    tid = tr.resolve_id(trade_id)
    if not tr.ID_RE.match(tid):
        raise HTTPException(422, f"Bad trade id: {trade_id!r}")
    study = _study(study_id)
    recs = _records(study)
    cur = recs.get(tid) or {"version": 0, "state": {}}
    if body.version is not None and body.version != int(cur.get("version") or 0):
        raise HTTPException(409, {"code": "stale", "current": _public(tid, cur) if cur.get("state") else cur})
    _check_size(body.state)
    if tid not in recs and len(recs) >= MAX_TRADES:
        raise HTTPException(413, "Too many trades in this study")
    merged = {**(cur.get("state") or {}), **body.state}
    recs[tid] = {"state": tr.clean_state(merged, tid), "version": int(cur.get("version") or 0) + 1}
    study.trade_records = recs
    await _save(study, f"trade:{tid}")
    return _public(tid, recs[tid])


@router.delete("/studies/{study_id}/trades/{trade_id}")
async def delete_trade(study_id: str, trade_id: str) -> dict:
    tid = tr.resolve_id(trade_id)
    study = _study(study_id)
    recs = _records(study)
    if tid not in recs:
        raise HTTPException(404, f"Unknown trade: {trade_id}")
    recs.pop(tid)
    study.trade_records = recs
    await _save(study, f"trade:{tid}")
    return {"deleted": tid}


class DecisionBody(BaseModel):
    selected: str
    rationale: str = Field("", max_length=4000)
    seat: str = Field("", max_length=40)


@router.post("/studies/{study_id}/trades/{trade_id}/decision")
async def record_trade_decision(study_id: str, trade_id: str, body: DecisionBody) -> dict:
    """Record the decision of a trade: the trade is kept (status ``decided``) and the study's
    decision record is written (or replaced) under the trade's decision-record id."""
    tid = tr.resolve_id(trade_id)
    study = _study(study_id)
    recs = _records(study)
    if tid not in recs:
        raise HTTPException(404, f"Unknown trade: {trade_id}")
    try:
        state = tr.decide(recs[tid]["state"], body.selected, body.rationale, body.seat or recs[tid]["state"].get("seat", ""))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    recs[tid] = {"state": state, "version": int(recs[tid].get("version") or 0) + 1}
    study.trade_records = recs
    record = tr.upsert_decision_record(study, state)
    await _save(study, f"trade:{tid}")
    return {**_public(tid, recs[tid]), "decision_record": record}
