"""Instructor class board and interventions (redesign WP9). Mounted under ``/api/instructor``;
every route needs an instructor (``SPACECDF_INSTRUCTORS`` / ``SMO_INSTRUCTORS``, or the laptop
instructor).

    GET  /board                          rows = studies, columns = seats; holder, presence,
                                         raised hands, gate state, needs-attention reasons
    POST /broadcast        {text}        message to every study
    POST /timer            {minutes, label}   timer on every study (0 clears)
    POST /studies/{sid}/message  {text}
    POST /studies/{sid}/timer    {minutes, label}
    POST /studies/{sid}/freeze   {frozen}
    POST /studies/{sid}/inject   {text, requirement_id?}   customer requirement change
    GET  /studies/{sid}/gate-items                         manual / hybrid items of the current gate
    POST /studies/{sid}/signoff  {criterion_id, signed, note}
    POST /studies/{sid}/hands/clear
    GET  /timeline  ?study_id=&format=csv|md&lang=en|fr    post-session export
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from . import config as cfg
from . import export as export_mod
from . import store
from .router import broadcast_team
from .service import require_instructor, seat_view, used_seats

logger = logging.getLogger(__name__)
router = APIRouter()

_gate_cache: dict[str, tuple[float, dict]] = {}
GATE_CACHE_S = 10.0


def _studies() -> dict[str, Any]:
    from ..routers.studies import get_study_store
    return get_study_store()


def _study_or_404(study_id: str):
    s = _studies().get(study_id)
    if s is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return s


async def _gate_summary(study_id: str) -> dict[str, Any]:
    hit = _gate_cache.get(study_id)
    if hit and time.time() - hit[0] < GATE_CACHE_S:
        return hit[1]
    from ..routers import gates as gates_router
    out: dict[str, Any] = {"gate": None}
    try:
        study = _studies()[study_id]
        profile = gates_router.study_profile(study)
        cur = gates_router.current_gate(profile, study)
        if cur is None:
            out = {"gate": "done", "state": "passed"}
        else:
            ev = await gates_router.evaluate_study_gate(study_id, cur["id"])
            must = [c for c in ev["criteria"] if c["priority"] == "must_pass"]
            failed = [c for c in must if c["status"] == "fail"]
            out = {"gate": cur["id"], "short": cur.get("short", cur["id"].upper()), "state": ev["state"],
                   "must_pass": len(must), "must_pass_met": ev["summary"]["must_pass_met"],
                   "failed": [{"id": c["id"], "question": c["question"], "owner_seat": c.get("owner_seat")}
                              for c in failed],
                   "manual_open": sum(1 for c in ev["criteria"]
                                      if c.get("mode") in ("manual", "hybrid") and c["status"] != "pass")}
    except Exception:  # noqa: BLE001
        logger.debug("board: gate summary failed for %s", study_id, exc_info=True)
    _gate_cache[study_id] = (time.time(), out)
    return out


def invalidate_gate_cache(study_id: str | None = None) -> None:
    if study_id:
        _gate_cache.pop(study_id, None)
    else:
        _gate_cache.clear()


@router.get("/board")
async def board(request: Request) -> dict:
    await require_instructor(request)
    rows = []
    for sid, study in list(_studies().items()):
        state = await store.get_team(sid)
        seats = [seat_view(sid, state, s) for s in used_seats(state)] if state.get("enabled") else []
        gate = await _gate_summary(sid)
        pending = await store.list_pending(sid)
        hands = state.get("hands") or {}
        idle = [s["id"] for s in seats if s["exclusive"] and s["state"] == "idle"]
        free = [s["id"] for s in seats if s["exclusive"] and s["state"] == "free"]
        reasons = []
        if gate.get("failed"):
            reasons.append("failed_must_pass")
        if idle:
            reasons.append("idle_seat")
        if hands:
            reasons.append("raised_hand")
        people = store.presence(sid)
        online = sum(1 for pid in people if store.holder_status(sid, {"person_id": pid}) == "active")
        rows.append({"study_id": sid, "name": study.name, "enabled": bool(state.get("enabled")),
                     "preset": state.get("preset"), "seats": seats, "gate": gate, "hands": hands,
                     "frozen": state.get("frozen"), "timer": state.get("timer"), "pending": len(pending),
                     "online": online, "idle_seats": idle, "free_seats": free,
                     "needs_attention": reasons})
    cls = await store.get_team(store.CLASS)
    return {"rows": rows, "seat_columns": [s["id"] for s in cfg.seats() if s["kind"] in ("lead", "systems", "domain")],
            "labels": {s["id"]: s["label"] for s in cfg.seats()},
            "broadcasts": list(cls.get("messages") or [])[-10:], "timer": cls.get("timer"),
            "now": store.now_iso()}


class TextBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


def _message(p, text: str, scope: str, kind: str = "message") -> dict:
    return {"id": uuid.uuid4().hex[:10], "at": store.now_iso(), "from": p.name, "text": text,
            "scope": scope, "kind": kind}


async def _post(study_id: str, msg: dict, p, action: str) -> None:
    state = await store.get_team(study_id)
    msgs = state.setdefault("messages", [])
    msgs.append(msg)
    del msgs[:-50]
    await store.save_team(study_id, state)
    await store.log_event(study_id, "instructor", p, action, msg["kind"], {"text": msg["text"]})
    await broadcast_team(study_id, "message")


@router.post("/broadcast")
async def broadcast(body: TextBody, request: Request) -> dict:
    p = await require_instructor(request)
    msg = _message(p, body.text, "all")
    cls = await store.get_team(store.CLASS)
    cls.setdefault("messages", []).append(msg)
    await store.save_team(store.CLASS, cls)
    for sid in list(_studies()):
        await _post(sid, dict(msg), p, "broadcast")
    return msg


@router.post("/studies/{study_id}/message")
async def team_message(study_id: str, body: TextBody, request: Request) -> dict:
    p = await require_instructor(request)
    _study_or_404(study_id)
    msg = _message(p, body.text, "team")
    await _post(study_id, msg, p, "message")
    return msg


class TimerBody(BaseModel):
    minutes: float = Field(..., ge=0, le=600)
    label: str = Field("", max_length=120)


def _timer(p, body: TimerBody) -> dict | None:
    if body.minutes <= 0:
        return None
    return {"ends_at": time.time() + body.minutes * 60, "minutes": body.minutes, "label": body.label,
            "set_by": p.name, "set_at": store.now_iso()}


async def _set_timer(study_id: str, timer: dict | None, p) -> None:
    state = await store.get_team(study_id)
    state["timer"] = timer
    await store.save_team(study_id, state)
    await store.log_event(study_id, "instructor", p, "timer", (timer or {}).get("label", ""),
                          {"minutes": (timer or {}).get("minutes", 0)})
    await broadcast_team(study_id, "timer")


@router.post("/timer")
async def timer_all(body: TimerBody, request: Request) -> dict:
    p = await require_instructor(request)
    t = _timer(p, body)
    cls = await store.get_team(store.CLASS)
    cls["timer"] = t
    await store.save_team(store.CLASS, cls)
    for sid in list(_studies()):
        await _set_timer(sid, t, p)
    return {"timer": t}


@router.post("/studies/{study_id}/timer")
async def timer_team(study_id: str, body: TimerBody, request: Request) -> dict:
    p = await require_instructor(request)
    _study_or_404(study_id)
    t = _timer(p, body)
    await _set_timer(study_id, t, p)
    return {"timer": t}


class FreezeBody(BaseModel):
    frozen: bool = True


@router.post("/studies/{study_id}/freeze")
async def freeze(study_id: str, body: FreezeBody, request: Request) -> dict:
    p = await require_instructor(request)
    _study_or_404(study_id)
    state = await store.get_team(study_id)
    state["frozen"] = {"by": p.name, "at": store.now_iso()} if body.frozen else None
    await store.save_team(study_id, state)
    await store.log_event(study_id, "instructor", p, "freeze" if body.frozen else "unfreeze")
    await broadcast_team(study_id, "freeze")
    return {"frozen": state["frozen"]}


class InjectBody(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)
    requirement_id: str | None = None
    rationale: str = Field("", max_length=1000)


@router.post("/studies/{study_id}/inject")
async def inject(study_id: str, body: InjectBody, request: Request) -> dict:
    """A customer requirement change: a new mission requirement, or new text for an existing
    mission requirement; the team gets a message and the change is logged."""
    p = await require_instructor(request)
    _study_or_404(study_id)
    from ..routers import requirements as req_router
    await req_router._ensure_loaded()
    if body.requirement_id:
        cur = req_router._requirements.get(body.requirement_id)
        if not cur or cur.get("study_id") != study_id:
            raise HTTPException(404, "Requirement not found")
        old = cur.get("text")
        req = await req_router.update_requirement(body.requirement_id, {
            "text": body.text, "status": "draft",
            "rationale": body.rationale or cur.get("rationale") or "Customer change (instructor inject)"})
        detail = {"requirement_id": req["id"], "old": old, "new": body.text}
    else:
        n = 1 + sum(1 for r in req_router._requirements.values()
                    if r.get("study_id") == study_id and str(r.get("code", "")).startswith("CUST-"))
        req = await req_router.create_requirement({
            "study_id": study_id, "level": "mission", "code": f"CUST-{n:03d}", "text": body.text,
            "rationale": body.rationale or "Customer change (instructor inject)", "status": "draft",
            "responsible_position": "team_leader"})
        detail = {"requirement_id": req["id"], "new": body.text}
    msg = _message(p, body.text, "team", kind="inject")
    msg["requirement_id"] = req["id"]
    msg["code"] = req.get("code")
    state = await store.get_team(study_id)
    state.setdefault("messages", []).append(msg)
    await store.save_team(study_id, state)
    await store.log_event(study_id, "customer", p, "inject", req.get("code") or req["id"], detail)
    await broadcast_team(study_id, "inject")
    from ..routers.ws import _broadcast_study
    try:
        await _broadcast_study(study_id, {"type": "requirement_updated", "requirement": req})
    except Exception:  # noqa: BLE001
        pass
    return {"requirement": req, "message": msg}


@router.get("/studies/{study_id}/gate-items")
async def gate_items(study_id: str, request: Request) -> dict:
    await require_instructor(request)
    study = _study_or_404(study_id)
    from ..routers import gates as gates_router
    profile = gates_router.study_profile(study)
    cur = gates_router.current_gate(profile, study)
    if cur is None:
        return {"gate": None, "items": []}
    ev = await gates_router.evaluate_study_gate(study_id, cur["id"])
    items = [{k: c.get(k) for k in ("id", "question", "mode", "status", "priority", "owner_seat", "evidence_found",
                                    "evidence_required", "signoff")}
             for c in ev["criteria"] if c.get("mode") in ("manual", "hybrid")]
    return {"gate": cur["id"], "short": cur.get("short"), "state": ev["state"], "items": items}


class SignoffBody(BaseModel):
    criterion_id: str
    signed: bool = True
    note: str = Field("", max_length=500)


@router.post("/studies/{study_id}/signoff")
async def signoff(study_id: str, body: SignoffBody, request: Request) -> dict:
    p = await require_instructor(request)
    _study_or_404(study_id)
    state = await store.get_team(study_id)
    so = state.setdefault("signoffs", {})
    if body.signed:
        so[body.criterion_id] = {"by": p.name, "person_id": p.id, "at": store.now_iso(), "note": body.note}
    else:
        so.pop(body.criterion_id, None)
    await store.save_team(study_id, state)
    await store.log_event(study_id, "instructor", p, "signoff" if body.signed else "signoff_withdrawn",
                          body.criterion_id, {"note": body.note})
    invalidate_gate_cache(study_id)
    await broadcast_team(study_id, "signoff")
    return await gate_items(study_id, request)


@router.post("/studies/{study_id}/hands/clear")
async def clear_hands(study_id: str, request: Request) -> dict:
    p = await require_instructor(request)
    state = await store.get_team(study_id)
    state["hands"] = {}
    await store.save_team(study_id, state)
    await store.log_event(study_id, "instructor", p, "hands_clear")
    await broadcast_team(study_id, "hand")
    return {"hands": {}}


@router.get("/timeline")
async def timeline(request: Request, study_id: str | None = None, format: str = Query("csv", pattern="^(csv|md)$"),
                   lang: str = "en"):
    await require_instructor(request)
    events = [e for e in await store.list_events(study_id) if e["study_id"] != store.CLASS]
    names = {sid: s.name for sid, s in _studies().items()}
    stamp = store.now_iso()[:19].replace(":", "")
    base = f"spacecdf_timeline_{study_id or 'all'}_{stamp}"
    if format == "md":
        body = export_mod.to_markdown(events, names, lang, generated=store.now_iso()[:19] + "Z")
        return PlainTextResponse(body, media_type="text/markdown; charset=utf-8",
                                 headers={"Content-Disposition": f'attachment; filename="{base}.md"'})
    body = export_mod.to_csv(events, names, lang)
    return PlainTextResponse("﻿" + body, media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{base}.csv"'})
