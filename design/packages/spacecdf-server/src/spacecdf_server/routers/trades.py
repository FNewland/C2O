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

Wave 3 (3.D3, 3.D4):

* ``GET    /studies/{sid}/trades/summary``         trades by review gate and level, and the protocol's
                                                   trade deliverable per gate (PI ruling)
* ``POST   /studies/{sid}/trades/from-tool``       "Record as trade" from the orbit or ground tools: a
                                                   draft system-level trade with the tool's candidates
* ``PUT    /studies/{sid}/trades/{tid}/condition`` the condition, due date, fallback and linked risks
                                                   of a conditional decision
* the decision body takes ``condition``, ``due``, ``fallback`` and ``risks``; a PUT that changes the
  weights after scoring keeps them but sets ``post_hoc_weights`` and logs the change.
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


@router.get("/studies/{study_id}/trades/summary")
async def trades_summary(study_id: str) -> dict:
    """Trades by gate and level, plus the trade deliverable of each gate that asks one."""
    recs = _records(_study(study_id))
    out = tr.gate_summary(recs)
    out["deliverables"] = {g: tr.trade_deliverable(recs, g) for g in tr.GATE_TRADE_LEVELS}
    return {"study_id": study_id, **out}


class FromToolBody(BaseModel):
    tool: str = Field("orbit", max_length=24)          # orbit | ground | other
    title: str = Field("", max_length=300)
    gate: str = Field("", max_length=8)
    level: str = Field("", max_length=24)
    seat: str = Field("", max_length=40)
    options: list[dict[str, Any]] = Field(default_factory=list, max_length=tr.MAX_OPTIONS)   # {id, label, metrics{}}
    criteria: list[dict[str, Any]] = Field(default_factory=list, max_length=tr.MAX_CRITERIA)  # {name, weight, source, scale}
    datum: str = ""
    id: str | None = None


#: default gate, level and seat of a trade recorded from a tool (PI ruling: orbit at MDR)
TOOL_DEFAULTS = {"orbit": ("mdr", "mission", "mission_analyst"), "ground": ("srr", "system", "comms_engineer"),
                 "other": ("", "system", "systems_engineer")}


@router.post("/studies/{study_id}/trades/from-tool")
async def trade_from_tool(study_id: str, body: FromToolBody) -> dict:
    """"Record as trade": the candidates the orbit or ground tool compared become a draft
    absolute-scale trade (options with their labels and metrics as evidence, criteria from the
    metrics unless given). The team then writes the scales, sources and weights before scoring."""
    study = _study(study_id)
    recs = _records(study)
    if len(recs) >= MAX_TRADES:
        raise HTTPException(413, "Too many trades in this study")
    if len(body.options) < 2:
        raise HTTPException(422, "A trade needs at least two candidates")
    g0, l0, s0 = TOOL_DEFAULTS.get(body.tool, TOOL_DEFAULTS["other"])
    opts = [str(o.get("id") or chr(65 + i))[:24] for i, o in enumerate(body.options)]
    labels = {k: str(o.get("label") or o.get("name") or k)[:400] for k, o in zip(opts, body.options)}
    metrics: list[str] = []
    for o in body.options:
        for m in (o.get("metrics") or {}):
            if m not in metrics:
                metrics.append(str(m)[:200])
    crit = body.criteria or [{"name": m} for m in metrics[: tr.MAX_CRITERIA]]
    n = max(len(crit), 1)
    crit = [{**c, "weight": c.get("weight", round(1 / n, 4))} for c in crit]
    evidence = {str(c.get("name")): "; ".join(f"{k}: {(o.get('metrics') or {}).get(c.get('name'))}" for k, o in zip(opts, body.options)
                                             if (o.get("metrics") or {}).get(c.get("name")) is not None)
                for c in crit}
    tid = tr.resolve_id((body.id or "").strip()) or _next_level_id(recs, body.level or l0)
    if tid in recs:
        raise HTTPException(409, {"code": "exists", "message": f"Trade {tid} exists"})
    state = tr.clean_state({"title": body.title or f"{body.tool.capitalize()} candidates", "seat": body.seat or s0,
                            "level": body.level or l0, "gate": body.gate or g0, "method": "absolute_scale",
                            "options": opts, "option_labels": labels, "datum": body.datum if body.datum in opts else opts[0],
                            "criteria": crit, "weights_mode": "direct",
                            "evidence_by_criterion": {k: v for k, v in evidence.items() if v},
                            "note": f"Recorded from the {body.tool} tool"}, tid)
    recs[tid] = {"state": state, "version": 1}
    study.trade_records = recs
    await _save(study, f"trade:{tid}")
    return _public(tid, recs[tid])


def _next_level_id(recs: dict[str, Any], level: str) -> str:
    """T-Mnn (mission), T-Snn (system), T-Ann (architecture), else T-nn."""
    import re
    prefix = {"mission": "T-M", "system": "T-S", "architecture": "T-A"}.get(level)
    if not prefix:
        return tr.next_id(recs)
    n = max([int(m.group(1)) for k in recs for m in [re.match(rf"^{prefix}(\d+)$", k)] if m] or [0])
    return f"{prefix}{n + 1:02d}"


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
    old = cur.get("state") or {}
    merged = {**old, **body.state}
    # wave 3 (3.D3): weights lock at the first score; a later change is kept and flagged
    if old.get("weights_locked_at") and tr.weights_changed(old, tr.clean_state(merged, tid)):
        from datetime import datetime, timezone
        merged["post_hoc_weights"] = True
        merged["weight_history"] = [*(old.get("weight_history") or []),
                                    {"at": datetime.now(timezone.utc).isoformat(), "from": tr.weights_of(old),
                                     "to": tr.weights_of(tr.clean_state(merged, tid))}]
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
    # wave 3 (3.D4): a conditional decision stays in the open-item register until met
    condition: str = Field("", max_length=4000)
    due: str = Field("", max_length=10)
    fallback: str = Field("", max_length=4000)
    risks: list[str] = Field(default_factory=list, max_length=50)
    blocks_gate: str = Field("", max_length=8)


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
        state = tr.decide(recs[tid]["state"], body.selected, body.rationale, body.seat or recs[tid]["state"].get("seat", ""),
                          condition=body.condition, due=body.due, fallback=body.fallback, risks=body.risks,
                          blocks_gate=body.blocks_gate)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    recs[tid] = {"state": state, "version": int(recs[tid].get("version") or 0) + 1}
    study.trade_records = recs
    record = tr.upsert_decision_record(study, state)
    await _save(study, f"trade:{tid}")
    return {**_public(tid, recs[tid]), "decision_record": record}


class ConditionBody(BaseModel):
    condition: str = Field("", max_length=4000)
    due: str = Field("", max_length=10)
    fallback: str = Field("", max_length=4000)
    risks: list[str] = Field(default_factory=list, max_length=50)
    blocks_gate: str = Field("", max_length=8)
    met: bool = False            # the condition is met: the decision is no longer conditional
    note: str = Field("", max_length=2000)


@router.put("/studies/{study_id}/trades/{trade_id}/condition")
async def put_trade_condition(study_id: str, trade_id: str, body: ConditionBody) -> dict:
    """Set (or clear, with ``met``) the condition of a decided trade (3.D4)."""
    from datetime import datetime, timezone
    tid = tr.resolve_id(trade_id)
    study = _study(study_id)
    recs = _records(study)
    if tid not in recs:
        raise HTTPException(404, f"Unknown trade: {trade_id}")
    st = dict(recs[tid]["state"])
    dec = {k: v for k, v in dict(st.get("decision") or {}).items()
           if k not in ("condition", "due", "fallback", "risks", "blocks_gate")}
    if body.met:
        old = dict(st.get("decision") or {})
        if old.get("condition"):
            dec["condition_met"] = {"condition": old["condition"], "at": datetime.now(timezone.utc).isoformat(),
                                    "note": body.note[:2000]}
    else:
        dec.update(tr.conditional(body.condition, body.due, body.fallback, body.risks, body.blocks_gate))
    st["decision"] = dec
    recs[tid] = {"state": tr.clean_state(st, tid), "version": int(recs[tid].get("version") or 0) + 1}
    study.trade_records = recs
    await _save(study, f"trade:{tid}")
    return _public(tid, recs[tid])
