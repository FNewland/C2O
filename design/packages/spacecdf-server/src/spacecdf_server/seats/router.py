"""Seat API (redesign WP9). Mounted under ``/api``.

Catalogue and identity
    GET  /seats/catalogue                       seat definitions + team-size presets (EN/FR)
    GET  /seats/me                              who am I, instructor status, instructor mode
    POST /seats/instructor/claim | /release     laptop mode only (no instructor list configured)

Per study  (``/studies/{sid}/team``)
    GET  ""                                     seats, holders, states, freeze, timer, messages, me
    POST /preset      {team_size, optional}     Team leader / instructor (anyone while solo)
    POST /claim       {seats: [...]}            self-claim (all or nothing)
    POST /release     {seat}
    POST /request     {seat}                    "Request seat" from the holder (60 s)
    POST /answer      {seat, accept}            the holder answers
    POST /active      {seat}                    active-seat switch
    POST /heartbeat   {seat?}                   presence (every 30 s); returns the team view
    POST /hand        {raised}                  raise / lower hand
    POST /reassign    {seat, person_id, name}   instructor
    POST /lock        {seat, locked}            instructor
    GET  /pending     ?seat=&mine=&status=      review inbox / my proposals
    POST /pending/{id}/accept|reject|withdraw   {comment}
    GET  /ownership                             element id → owning seat
    GET/POST/DELETE /subscriptions              {seat, element_id, field}
    POST /subscriptions/seen                    {seat, element_id?, field?}
    POST /wanted {seat, key, note}; DELETE /wanted {key}; POST /wanted/provide {key, element_id, field}
    GET  /ledger                                wanted vs provided (Systems)
    GET  /next        ?seat=                    the seat's "Next" card
    GET  /events      ?limit=                   recent seat activity
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from . import config as cfg
from . import store
from .identity import instructor_emails, instructor_mode, person as person_of
from .service import (
    SeatCtx, answer_handover, claim, owner_of_element, reassign, release, request_handover,
    seat_ctx, set_lock, set_preset, switch_active, team_view, used_seats,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def broadcast_team(study_id: str, what: str = "team") -> None:
    from ..routers.ws import _broadcast_study
    try:
        await _broadcast_study(study_id, {"type": "team_changed", "what": what})
    except Exception:  # noqa: BLE001
        logger.debug("team broadcast failed", exc_info=True)


def _study_or_404(study_id: str):
    from ..routers.studies import get_study_store
    s = get_study_store().get(study_id)
    if s is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return s


async def _ctx(request: Request, study_id: str) -> SeatCtx:
    _study_or_404(study_id)
    return await seat_ctx(request, study_id)


# ─── catalogue / identity ────────────────────────────────────────────────────

@router.get("/seats/catalogue")
async def catalogue() -> dict:
    return cfg.public()


@router.get("/seats/me")
async def me(request: Request) -> dict:
    p = person_of(request)
    lap = await store.laptop_instructor()
    return {**p.public(), "instructor": await store.is_instructor(p),
            "instructor_status": await store.instructor_status(p),
            "instructor_mode": instructor_mode(),
            "instructors_configured": len(instructor_emails()),
            "laptop_instructor": ({"name": lap.get("name"), "since": lap.get("since")} if lap else None)}


@router.post("/seats/instructor/claim")
async def claim_instructor(request: Request) -> dict:
    p = person_of(request)
    if instructor_mode() == "list":
        raise HTTPException(409, {"code": "instructor_list", "message": "Instructors are set by SPACECDF_INSTRUCTORS on this server"})
    if p.anonymous:
        raise HTTPException(401, {"code": "anonymous", "message": "Enter a name first"})
    cls = await store.get_team(store.CLASS)
    cur = cls.get("instructor")
    if cur and cur.get("person_id") != p.id:
        raise HTTPException(409, {"code": "instructor_taken", "message": f"{cur.get('name')} is the instructor"})
    cls["instructor"] = {"person_id": p.id, "name": p.name, "since": store.now_iso()}
    await store.save_team(store.CLASS, cls)
    await store.log_event(store.CLASS, "instructor", p, "instructor_claim")
    return await me(request)


@router.post("/seats/instructor/release")
async def release_instructor(request: Request) -> dict:
    p = person_of(request)
    cls = await store.get_team(store.CLASS)
    if (cls.get("instructor") or {}).get("person_id") == p.id:
        cls["instructor"] = None
        await store.save_team(store.CLASS, cls)
        await store.log_event(store.CLASS, "instructor", p, "instructor_release")
    return await me(request)


# ─── team ────────────────────────────────────────────────────────────────────

@router.get("/studies/{study_id}/team")
async def get_team(study_id: str, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    return team_view(study_id, ctx.state, ctx)


class PresetBody(BaseModel):
    team_size: str | int | None = None
    optional: list[str] = Field(default_factory=list)


@router.post("/studies/{study_id}/team/preset")
async def post_preset(study_id: str, body: PresetBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    async with store.lock_for(study_id):
        await set_preset(ctx, None if body.team_size in (None, "", "solo", 0, "0") else str(body.team_size), body.optional)
    await broadcast_team(study_id)
    return team_view(study_id, ctx.state, await seat_ctx(request, study_id))


class SeatsBody(BaseModel):
    seats: list[str] = Field(default_factory=list)
    seat: str = ""


@router.post("/studies/{study_id}/team/claim")
async def post_claim(study_id: str, body: SeatsBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    seats = body.seats or ([body.seat] if body.seat else [])
    if not seats:
        raise HTTPException(400, "seats required")
    async with store.lock_for(study_id):
        await claim(ctx, seats)
    await broadcast_team(study_id)
    return team_view(study_id, ctx.state, await seat_ctx(request, study_id))


class SeatBody(BaseModel):
    seat: str


@router.post("/studies/{study_id}/team/release")
async def post_release(study_id: str, body: SeatBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    async with store.lock_for(study_id):
        await release(ctx, body.seat)
    await broadcast_team(study_id)
    return team_view(study_id, ctx.state, await seat_ctx(request, study_id))


@router.post("/studies/{study_id}/team/request")
async def post_request(study_id: str, body: SeatBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    async with store.lock_for(study_id):
        res = await request_handover(ctx, body.seat)
    await broadcast_team(study_id, "request")
    return {**res, "team": team_view(study_id, ctx.state, await seat_ctx(request, study_id))}


class AnswerBody(BaseModel):
    seat: str
    accept: bool


@router.post("/studies/{study_id}/team/answer")
async def post_answer(study_id: str, body: AnswerBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    async with store.lock_for(study_id):
        res = await answer_handover(ctx, body.seat, body.accept)
    await broadcast_team(study_id)
    return {**res, "team": team_view(study_id, ctx.state, await seat_ctx(request, study_id))}


@router.post("/studies/{study_id}/team/active")
async def post_active(study_id: str, body: SeatBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    await switch_active(ctx, body.seat)
    await broadcast_team(study_id, "active")
    return team_view(study_id, ctx.state, ctx)


class HeartbeatBody(BaseModel):
    seat: str = ""


@router.post("/studies/{study_id}/team/heartbeat")
async def post_heartbeat(study_id: str, body: HeartbeatBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    store.touch(study_id, ctx.person, active_seat=ctx.active)
    return team_view(study_id, ctx.state, ctx)


class HandBody(BaseModel):
    raised: bool = True
    note: str = Field("", max_length=200)


@router.post("/studies/{study_id}/team/hand")
async def post_hand(study_id: str, body: HandBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    if ctx.person.anonymous:
        raise HTTPException(401, "anonymous")
    hands = ctx.state.setdefault("hands", {})
    if body.raised:
        hands[ctx.person.id] = {"name": ctx.person.name, "seat": ctx.active, "at": store.now_iso(), "note": body.note}
    else:
        hands.pop(ctx.person.id, None)
    await store.save_team(study_id, ctx.state)
    await store.log_event(study_id, ctx.active or "", ctx.person, "hand_raise" if body.raised else "hand_lower",
                          detail={"note": body.note} if body.note else None)
    await broadcast_team(study_id, "hand")
    return team_view(study_id, ctx.state, ctx)


class ReassignBody(BaseModel):
    seat: str
    person_id: str | None = None
    name: str = ""


@router.post("/studies/{study_id}/team/reassign")
async def post_reassign(study_id: str, body: ReassignBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    async with store.lock_for(study_id):
        await reassign(ctx, body.seat, body.person_id, body.name)
    await broadcast_team(study_id)
    return team_view(study_id, ctx.state, ctx)


class LockBody(BaseModel):
    seat: str
    locked: bool = True


@router.post("/studies/{study_id}/team/lock")
async def post_lock(study_id: str, body: LockBody, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    await set_lock(ctx, body.seat, body.locked)
    await broadcast_team(study_id)
    return team_view(study_id, ctx.state, ctx)


@router.get("/studies/{study_id}/team/people")
async def team_people(study_id: str, request: Request) -> list[dict]:
    """Everyone seen in the study (presence + holders), for the instructor's reassign menu."""
    ctx = await _ctx(request, study_id)
    people: dict[str, dict] = {}
    for pid, d in store.presence(study_id).items():
        people[pid] = {"id": pid, "name": d.get("name", ""), "verified": d.get("verified", False),
                       "status": "active" if store.holder_status(study_id, {"person_id": pid}) == "active" else "idle"}
    for sid, hs in (ctx.state.get("holdings") or {}).items():
        for h in hs:
            people.setdefault(h["person_id"], {"id": h["person_id"], "name": h["name"], "verified": h.get("verified"),
                                               "status": store.holder_status(study_id, h)})
            people[h["person_id"]].setdefault("seats", []).append(sid)
    return sorted(people.values(), key=lambda p: p["name"].lower())


# ─── pending changes (ruling 5) ──────────────────────────────────────────────

@router.get("/studies/{study_id}/team/pending")
async def list_pending(study_id: str, request: Request, seat: str | None = None, mine: bool = False,
                       status: str | None = "pending") -> list[dict]:
    ctx = await _ctx(request, study_id)
    rows = await store.list_pending(study_id, None if status in ("", "all") else status)
    if seat:
        rows = [r for r in rows if r["owner_seat"] == seat]
    if mine:
        rows = [r for r in rows if r["by_person"] == ctx.person.id]
    return rows


class ReviewBody(BaseModel):
    comment: str = Field("", max_length=2000)


async def _review(study_id: str, pc_id: str, request: Request, action: str, comment: str) -> dict:
    from .changes import apply_pending, change_fields
    ctx = await _ctx(request, study_id)
    async with store.lock_for(study_id):
        pc = await store.get_pending(pc_id)
        if pc is None or pc["study_id"] != study_id:
            raise HTTPException(404, "Pending change not found")
        if pc["status"] != "pending":
            raise HTTPException(409, {"code": "already_reviewed", "message": f"Already {pc['status']}"})
        if action == "withdraw":
            if pc["by_person"] != ctx.person.id:
                raise HTTPException(403, {"code": "not_author", "message": "Only the author withdraws a proposal"})
            seat = pc["by_seat"]
        else:
            if not (ctx.holds(pc["owner_seat"]) or ctx.instructor):
                raise HTTPException(403, {"code": "not_owner",
                                          "message": f"Only {cfg.label(pc['owner_seat'])['en']} reviews this change",
                                          "owner_seat": pc["owner_seat"]})
            seat = pc["owner_seat"] if ctx.holds(pc["owner_seat"]) else "instructor"
        applied = None
        if action == "accept":
            applied = await apply_pending(pc)
        status = {"accept": "accepted", "reject": "rejected", "withdraw": "withdrawn"}[action]
        pc = await store.close_pending(pc_id, status, ctx.person, seat, comment)
        await store.log_event(study_id, seat, ctx.person, action, pc.get("element_name") or pc.get("element_id", ""), {
            "pending_id": pc_id, "element_id": pc.get("element_id"), "fields": change_fields(pc.get("new") or {}),
            "param_keys": pc.get("param_keys"), "by_person": pc.get("by_person"), "by_name": pc.get("by_name"),
            "by_seat": pc.get("by_seat"), "new": pc.get("new"), "old": pc.get("old"), "comment": comment})
    await broadcast_team(study_id, "pending")
    return {**pc, "applied": applied}


@router.post("/studies/{study_id}/team/pending/{pc_id}/accept")
async def accept_pending(study_id: str, pc_id: str, body: ReviewBody, request: Request) -> dict:
    return await _review(study_id, pc_id, request, "accept", body.comment)


@router.post("/studies/{study_id}/team/pending/{pc_id}/reject")
async def reject_pending(study_id: str, pc_id: str, body: ReviewBody, request: Request) -> dict:
    if not body.comment.strip():
        raise HTTPException(400, {"code": "comment_required", "message": "Say why the change is rejected"})
    return await _review(study_id, pc_id, request, "reject", body.comment)


@router.post("/studies/{study_id}/team/pending/{pc_id}/withdraw")
async def withdraw_pending(study_id: str, pc_id: str, body: ReviewBody, request: Request) -> dict:
    return await _review(study_id, pc_id, request, "withdraw", body.comment)


# ─── ownership, subscriptions, wanted-vs-provided ────────────────────────────

def _study_elements(study_id: str) -> dict[str, dict]:
    from ..routers import elements as el_router
    return {k: v for k, v in el_router._elements.items()
            if v.get("study_id") == study_id and not v.get("deleted_at")}


def field_value(el: dict[str, Any] | None, field: str) -> Any:
    if el is None:
        return None
    if field.startswith("performance."):
        return (el.get("performance") or {}).get(field.split(".", 1)[1])
    return el.get(field)


@router.get("/studies/{study_id}/team/ownership")
async def ownership(study_id: str, request: Request) -> dict:
    ctx = await _ctx(request, study_id)
    from ..routers import elements as el_router
    els = _study_elements(study_id)
    out = {}
    for eid, el in els.items():
        o = owner_of_element(ctx.state, el, el_router._elements) if ctx.enabled else \
            cfg.element_owner_seat(el, el_router._elements)
        out[eid] = o
    return {"enabled": ctx.enabled, "owners": out}


class SubBody(BaseModel):
    seat: str
    element_id: str | None = None
    field: str | None = None


def _sub_key(element_id: str, field: str) -> str:
    return f"{element_id}|{field}"


@router.get("/studies/{study_id}/team/subscriptions")
async def list_subscriptions(study_id: str, request: Request, seat: str) -> list[dict]:
    return subs_view(await _ctx(request, study_id), seat)


def subs_view(ctx: SeatCtx, seat: str) -> list[dict]:
    from ..routers import elements as el_router
    subs = (ctx.state.get("subscriptions") or {}).get(seat) or {}
    out = []
    for key, seen in subs.items():
        eid, field = key.split("|", 1)
        el = el_router._elements.get(eid)
        val = field_value(el, field)
        owner = owner_of_element(ctx.state, el, el_router._elements) if el else None
        out.append({"element_id": eid, "element_name": (el or {}).get("name", "?"), "field": field,
                    "param_key": f"{cfg.owner_prefix(owner) if owner else 'unowned'}.{field}",
                    "owner_seat": owner, "owner_label": cfg.label(owner) if owner else None,
                    "value": val, "seen_value": seen.get("value"), "seen_at": seen.get("at"),
                    "changed": el is not None and val != seen.get("value"), "missing": el is None})
    return out


@router.post("/studies/{study_id}/team/subscriptions")
async def add_subscription(study_id: str, body: SubBody, request: Request) -> list[dict]:
    ctx = await _ctx(request, study_id)
    if body.seat not in ctx.held:
        raise HTTPException(403, {"code": "not_holder", "message": "Subscribe from a seat you hold"})
    from ..routers import elements as el_router
    el = el_router._elements.get(body.element_id or "")
    if el is None or el.get("study_id") != study_id or not body.field:
        raise HTTPException(404, "Element or field not found")
    subs = ctx.state.setdefault("subscriptions", {}).setdefault(body.seat, {})
    subs[_sub_key(el["id"], body.field)] = {"value": field_value(el, body.field), "at": store.now_iso()}
    await store.save_team(study_id, ctx.state)
    await store.log_event(study_id, body.seat, ctx.person, "subscribe", f"{el.get('name')}.{body.field}",
                          {"element_id": el["id"], "field": body.field})
    return await list_subscriptions(study_id, request, body.seat)


@router.delete("/studies/{study_id}/team/subscriptions")
async def delete_subscription(study_id: str, request: Request, seat: str, element_id: str, field: str) -> list[dict]:
    ctx = await _ctx(request, study_id)
    if seat not in ctx.held:
        raise HTTPException(403, {"code": "not_holder", "message": "Not your seat"})
    ((ctx.state.get("subscriptions") or {}).get(seat) or {}).pop(_sub_key(element_id, field), None)
    await store.save_team(study_id, ctx.state)
    await store.log_event(study_id, seat, ctx.person, "unsubscribe", field, {"element_id": element_id, "field": field})
    return await list_subscriptions(study_id, request, seat)


@router.post("/studies/{study_id}/team/subscriptions/seen")
async def mark_seen(study_id: str, body: SubBody, request: Request) -> list[dict]:
    ctx = await _ctx(request, study_id)
    if body.seat not in ctx.held:
        raise HTTPException(403, {"code": "not_holder", "message": "Not your seat"})
    from ..routers import elements as el_router
    subs = (ctx.state.get("subscriptions") or {}).get(body.seat) or {}
    for key in list(subs):
        eid, field = key.split("|", 1)
        if body.element_id and (eid != body.element_id or (body.field and field != body.field)):
            continue
        subs[key] = {"value": field_value(el_router._elements.get(eid), field), "at": store.now_iso()}
    await store.save_team(study_id, ctx.state)
    return await list_subscriptions(study_id, request, body.seat)


class WantedBody(BaseModel):
    seat: str
    key: str = Field(..., min_length=3, max_length=120)
    note: str = Field("", max_length=500)


@router.post("/studies/{study_id}/team/wanted")
async def add_wanted(study_id: str, body: WantedBody, request: Request) -> dict:
    """ICEMaker "Parameters wanted": a seat asks for a parameter nobody provides yet."""
    ctx = await _ctx(request, study_id)
    if body.seat not in ctx.held:
        raise HTTPException(403, {"code": "not_holder", "message": "Ask from a seat you hold"})
    key = body.key.strip()
    w = ctx.state.setdefault("wanted", {}).setdefault(key, {"by": [], "at": store.now_iso(), "note": body.note})
    if body.seat not in w["by"]:
        w["by"].append(body.seat)
    await store.save_team(study_id, ctx.state)
    await store.log_event(study_id, body.seat, ctx.person, "want", key, {"note": body.note})
    await broadcast_team(study_id, "ledger")
    return await ledger(study_id, request)


@router.delete("/studies/{study_id}/team/wanted")
async def delete_wanted(study_id: str, request: Request, key: str) -> dict:
    ctx = await _ctx(request, study_id)
    if not (ctx.held or ctx.instructor):
        raise HTTPException(403, {"code": "no_seat", "message": "Claim a seat first"})
    (ctx.state.get("wanted") or {}).pop(key, None)
    await store.save_team(study_id, ctx.state)
    await store.log_event(study_id, ctx.active or "", ctx.person, "unwant", key)
    return await ledger(study_id, request)


class ProvideBody(BaseModel):
    key: str
    element_id: str
    field: str


@router.post("/studies/{study_id}/team/wanted/provide")
async def provide_wanted(study_id: str, body: ProvideBody, request: Request) -> dict:
    """The owning seat points a wanted parameter at the element field that provides it; the
    seats that asked for it are subscribed to that field."""
    ctx = await _ctx(request, study_id)
    from ..routers import elements as el_router
    el = el_router._elements.get(body.element_id)
    w = (ctx.state.get("wanted") or {}).get(body.key)
    if el is None or w is None:
        raise HTTPException(404, "Wanted parameter or element not found")
    owner = owner_of_element(ctx.state, el, el_router._elements)
    if not (ctx.holds(owner) or ctx.holds("systems_engineer") or ctx.instructor):
        raise HTTPException(403, {"code": "not_owner", "message": "The owning seat or Systems provides a parameter"})
    w["provided"] = {"element_id": el["id"], "field": body.field, "by": ctx.person.name, "at": store.now_iso()}
    for seat in w.get("by") or []:
        ctx.state.setdefault("subscriptions", {}).setdefault(seat, {})[_sub_key(el["id"], body.field)] = \
            {"value": None, "at": store.now_iso()}
    await store.save_team(study_id, ctx.state)
    await store.log_event(study_id, owner or ctx.active or "", ctx.person, "provide", body.key,
                          {"element_id": el["id"], "field": body.field})
    await broadcast_team(study_id, "ledger")
    return await ledger(study_id, request)


@router.get("/studies/{study_id}/team/ledger")
async def ledger(study_id: str, request: Request) -> dict:
    """Wanted vs provided: every subscribed or requested parameter, who wants it, who owns
    it and whether a value exists. ``unowned`` = no seat of this study holds the owner."""
    ctx = await _ctx(request, study_id)
    from ..routers import elements as el_router
    holdings = ctx.state.get("holdings") or {}
    rows: dict[str, dict] = {}

    def owner_info(owner: str | None) -> dict:
        hs = holdings.get(owner or "") or []
        return {"owner_seat": owner, "owner_label": cfg.label(owner) if owner else None,
                "owner_holder": hs[0]["name"] if hs else None}

    for seat, subs in (ctx.state.get("subscriptions") or {}).items():
        for key in subs:
            eid, field = key.split("|", 1)
            el = el_router._elements.get(eid)
            owner = owner_of_element(ctx.state, el, el_router._elements) if el else None
            pk = f"{cfg.owner_prefix(owner) if owner else 'unowned'}.{field}"
            row = rows.setdefault(f"{eid}|{field}", {
                "key": pk, "element_id": eid, "element_name": (el or {}).get("name"), "field": field,
                "value": field_value(el, field), "wanted_by": [], "source": "subscription", **owner_info(owner)})
            if seat not in row["wanted_by"]:
                row["wanted_by"].append(seat)
    for key, w in (ctx.state.get("wanted") or {}).items():
        prov = w.get("provided") or {}
        el = el_router._elements.get(prov.get("element_id", "")) if prov else None
        owner = owner_of_element(ctx.state, el, el_router._elements) if el else \
            cfg.resolve_in_study(cfg.seat_for_param_key(key), used_seats(ctx.state))
        rows[f"wanted|{key}"] = {"key": key, "element_id": prov.get("element_id"), "element_name": (el or {}).get("name"),
                                 "field": prov.get("field"), "value": field_value(el, prov.get("field", "")) if el else None,
                                 "wanted_by": list(w.get("by") or []), "note": w.get("note", ""),
                                 "source": "wanted", **owner_info(owner)}
    out = []
    for r in rows.values():
        if not r["owner_seat"] or not r["owner_holder"]:
            r["status"] = "unowned"
        elif r["value"] in (None, "", 0) and r["source"] == "subscription":
            r["status"] = "no_value"
        elif r["source"] == "wanted" and not r.get("element_id"):
            r["status"] = "requested"
        else:
            r["status"] = "provided"
        out.append(r)
    order = {"unowned": 0, "requested": 1, "no_value": 2, "provided": 3}
    out.sort(key=lambda r: (order[r["status"]], r["key"]))
    return {"rows": out, "counts": {k: sum(1 for r in out if r["status"] == k) for k in order}}


# ─── the seat's "Next" card ──────────────────────────────────────────────────

async def next_for_seat(study_id: str, ctx: SeatCtx, seat: str) -> dict[str, Any]:
    """First failing must-pass gate item owned by the seat → proposals awaiting the seat →
    changed subscriptions → the seat's first unstarted step → nothing."""
    from ..routers import gates as gates_router
    gate_ev = None
    try:
        study = _study_or_404(study_id)
        profile = gates_router.study_profile(study)
        cur = gates_router.current_gate(profile, study)
        if cur:
            gate_ev = await gates_router.evaluate_study_gate(study_id, cur["id"])
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        logger.debug("next: gate evaluation failed", exc_info=True)
    mine = [c for c in (gate_ev or {}).get("criteria", []) if c.get("owner_seat") == seat]
    gate_short = ((gate_ev or {}).get("gate") or {}).get("short")
    fail = next((c for c in mine if c["priority"] == "must_pass" and c["status"] == "fail"), None)
    if fail:
        return {"kind": "gate_item", "gate": gate_short, "criterion_id": fail["id"], "question": fail["question"],
                "fix": fail.get("fix"), "step": fail.get("step"), "step_label": fail.get("step_label"),
                "evidence": fail.get("evidence_found")}
    pend = [p for p in await store.list_pending(study_id) if p["owner_seat"] == seat]
    if pend:
        return {"kind": "proposals", "count": len(pend), "first": {"element_name": pend[0]["element_name"],
                                                                    "by_name": pend[0]["by_name"],
                                                                    "by_seat": pend[0]["by_seat"],
                                                                    "fields": list((pend[0].get("new") or {}).keys())}}
    subs = subs_view(ctx, seat) if seat in ctx.held else []
    changed = [s for s in subs if s["changed"]]
    if changed:
        return {"kind": "subscriptions", "count": len(changed),
                "first": {"element_name": changed[0]["element_name"], "field": changed[0]["field"],
                          "owner_seat": changed[0]["owner_seat"]}}
    unstarted = next((c for c in mine if c["status"] == "not_evaluated"), None)
    if unstarted:
        return {"kind": "step", "gate": gate_short, "criterion_id": unstarted["id"], "question": unstarted["question"],
                "fix": unstarted.get("fix"), "step": unstarted.get("step"), "step_label": unstarted.get("step_label")}
    return {"kind": "none", "gate": gate_short}



@router.get("/studies/{study_id}/team/next")
async def next_card(study_id: str, request: Request, seat: str | None = None) -> dict:
    ctx = await _ctx(request, study_id)
    seat = seat or ctx.active
    if not seat:
        return {"kind": "no_seat"}
    return {"seat": seat, **(await next_for_seat(study_id, ctx, seat))}


@router.get("/studies/{study_id}/team/events")
async def recent_events(study_id: str, request: Request, limit: int = Query(50, ge=1, le=500)) -> list[dict]:
    await _ctx(request, study_id)
    evs = await store.list_events(study_id)
    return evs[-limit:][::-1]
