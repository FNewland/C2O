"""Seat rules: claiming, handover, the active seat, and who may write what.

REDESIGN_DECISIONS.md ruling 4: self-claim + instructor override, with an instructor lock.
Ruling 5: editing a parameter owned by another seat warns first; if the editor continues the
edit becomes a pending change the owning seat accepts or rejects; until then the owner's value
stands. Team leader and Instructor follow the same rule unless they hold the owning seat.

A study without seats (``enabled: false``: created solo, or before WP9) keeps the old open
behaviour so a single laptop user and the existing API clients work unchanged.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request

from . import config as cfg
from . import store
from .identity import Person, confirmed_review, person as person_of, requested_seat


@dataclass
class SeatCtx:
    study_id: str
    person: Person
    state: dict[str, Any]
    held: list[str] = field(default_factory=list)
    active: str | None = None
    instructor: bool = False

    @property
    def enabled(self) -> bool:
        return bool(self.state.get("enabled"))

    @property
    def active_kind(self) -> str:
        return cfg.kind(self.active) if self.active else ""

    def holds(self, seat_id: str | None) -> bool:
        return bool(seat_id) and seat_id in self.held


def used_seats(state: dict[str, Any]) -> list[str]:
    return cfg.study_seats(state.get("groups") or [])


def held_by(state: dict[str, Any], person_id: str) -> list[str]:
    order = used_seats(state)
    held = [sid for sid, hs in (state.get("holdings") or {}).items()
            if any(h["person_id"] == person_id for h in hs)]
    return sorted(held, key=lambda s: order.index(s) if s in order else 99)


def pick_active(state: dict[str, Any], person_id: str, held: list[str], wanted: str | None) -> str | None:
    if wanted and wanted in held:
        return wanted
    stored = (state.get("active") or {}).get(person_id)
    if stored in held:
        return stored
    editing = [s for s in held if cfg.kind(s) in cfg.EDITING_KINDS]
    return (editing or held or [None])[0]


async def seat_ctx(request: Request | None, study_id: str, p: Person | None = None) -> SeatCtx:
    p = p or (person_of(request) if request is not None else Person("anon", "", False))
    state = await store.get_team(study_id)
    held = held_by(state, p.id) if not p.anonymous else []
    active = pick_active(state, p.id, held, requested_seat(request) if request is not None else None)
    return SeatCtx(study_id=study_id, person=p, state=state, held=held, active=active,
                   instructor=await store.is_instructor(p))


def _http(status: int, code: str, message: str, **extra: Any) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message, **extra})


# ─── views of the team document ──────────────────────────────────────────────

def prune_requests(state: dict[str, Any]) -> bool:
    now = time.time()
    reqs = state.get("requests") or {}
    gone = [sid for sid, r in reqs.items() if r.get("expires", 0) < now]
    for sid in gone:
        reqs.pop(sid, None)
    return bool(gone)


def seat_view(study_id: str, state: dict[str, Any], seat_id: str) -> dict[str, Any]:
    hs = (state.get("holdings") or {}).get(seat_id) or []
    pres = store.presence(study_id)
    holders = []
    for h in hs:
        st = store.holder_status(study_id, h)
        pd = pres.get(h["person_id"]) or {}
        holders.append({**h, "status": st, "active_seat": pd.get("active_seat"),
                        "last_action": pd.get("last_action"), "last_action_at": pd.get("last_action_at"),
                        "hand": bool((state.get("hands") or {}).get(h["person_id"]))})
    locked = (state.get("locked") or {}).get(seat_id)
    if locked:
        st = "locked"
    elif not holders:
        st = "free"
    elif cfg.is_exclusive(seat_id) and holders[0]["status"] != "active":
        st = "idle"
    else:
        st = "held"
    req = (state.get("requests") or {}).get(seat_id)
    return {"id": seat_id, "label": cfg.label(seat_id), "kind": cfg.kind(seat_id),
            "exclusive": cfg.is_exclusive(seat_id), "state": st, "holders": holders,
            "reclaimable": bool(holders) and cfg.is_exclusive(seat_id) and holders[0]["status"] == "reclaimable",
            "locked": locked, "request": req}


def team_view(study_id: str, state: dict[str, Any], ctx: SeatCtx | None = None) -> dict[str, Any]:
    prune_requests(state)
    groups = state.get("groups") or []
    out: dict[str, Any] = {
        "study_id": study_id, "enabled": bool(state.get("enabled")), "preset": state.get("preset"),
        "optional": list(state.get("optional") or []), "groups": groups,
        "seats": [seat_view(study_id, state, sid) for sid in used_seats(state)] if state.get("enabled") else [],
        "frozen": state.get("frozen"), "timer": state.get("timer"),
        "messages": list(state.get("messages") or [])[-20:],
        "hands": state.get("hands") or {}, "signoffs": state.get("signoffs") or {},
    }
    if ctx is not None:
        out["me"] = {**ctx.person.public(), "held": ctx.held, "active": ctx.active,
                     "instructor": ctx.instructor,
                     "requests_to_me": [{"seat": sid, **r} for sid, r in (state.get("requests") or {}).items()
                                        if sid in ctx.held],
                     "my_requests": [{"seat": sid, **r} for sid, r in (state.get("requests") or {}).items()
                                     if r.get("person_id") == ctx.person.id]}
    return out


# ─── claiming and handover ───────────────────────────────────────────────────

def _holding(p: Person, assigned_by: str) -> dict[str, Any]:
    return {"person_id": p.id, "name": p.name, "verified": p.verified, "since": store.now_iso(),
            "assigned_by": assigned_by}


def _require_enabled(ctx: SeatCtx) -> None:
    if not ctx.enabled:
        raise _http(409, "no_seats", "This study has no seats (solo study). Choose a team size first.")


def _require_seat(ctx: SeatCtx, seat_id: str) -> None:
    if seat_id not in used_seats(ctx.state):
        raise _http(404, "unknown_seat", f"Seat {seat_id} is not used in this study")


async def claim(ctx: SeatCtx, seat_ids: list[str]) -> list[str]:
    """Self-claim Free seats (all or nothing). An exclusive seat held by someone active refuses."""
    _require_enabled(ctx)
    if ctx.person.anonymous:
        raise _http(401, "anonymous", "Sign in or enter a name first")
    hold = ctx.state.setdefault("holdings", {})
    reclaimed: list[tuple[str, dict]] = []
    for sid in seat_ids:
        _require_seat(ctx, sid)
        if (ctx.state.get("locked") or {}).get(sid) and not ctx.instructor:
            raise _http(423, "seat_locked", f"{cfg.label(sid)['en']} is locked by the instructor", seat=sid)
        hs = hold.get(sid) or []
        if any(h["person_id"] == ctx.person.id for h in hs):
            continue
        if cfg.is_exclusive(sid) and hs:
            if store.holder_status(ctx.study_id, hs[0]) != "reclaimable":
                raise _http(409, "seat_held", f"{cfg.label(sid)['en']} is held by {hs[0]['name']}",
                            seat=sid, holder=hs[0]["name"])
            reclaimed.append((sid, hs[0]))
    for sid in seat_ids:
        hs = hold.setdefault(sid, [])
        if any(h["person_id"] == ctx.person.id for h in hs):
            continue
        if cfg.is_exclusive(sid):
            hs.clear()
        hs.append(_holding(ctx.person, "self"))
        (ctx.state.get("requests") or {}).pop(sid, None)
    await store.save_team(ctx.study_id, ctx.state)
    for sid in seat_ids:
        prev = next((h for s, h in reclaimed if s == sid), None)
        if prev:
            await store.log_event(ctx.study_id, sid, ctx.person, "reclaim", sid,
                                  {"from_person": prev["person_id"], "from_name": prev["name"]})
        else:
            await store.log_event(ctx.study_id, sid, ctx.person, "claim", sid)
    return held_by(ctx.state, ctx.person.id)


async def release(ctx: SeatCtx, seat_id: str) -> None:
    _require_enabled(ctx)
    if (ctx.state.get("locked") or {}).get(seat_id) and not ctx.instructor:
        raise _http(423, "seat_locked", "The instructor locked this seat")
    hs = (ctx.state.get("holdings") or {}).get(seat_id) or []
    left = [h for h in hs if h["person_id"] != ctx.person.id]
    if len(left) == len(hs):
        raise _http(409, "not_holder", "You do not hold this seat")
    ctx.state["holdings"][seat_id] = left
    await store.save_team(ctx.study_id, ctx.state)
    await store.log_event(ctx.study_id, seat_id, ctx.person, "release", seat_id)


async def request_handover(ctx: SeatCtx, seat_id: str) -> dict[str, Any]:
    """"Request seat" from its holder; the holder has ``handover_timeout_s`` (60 s) to answer.
    A reclaimable seat is simply claimed."""
    _require_enabled(ctx)
    _require_seat(ctx, seat_id)
    if ctx.person.anonymous:
        raise _http(401, "anonymous", "Sign in or enter a name first")
    if (ctx.state.get("locked") or {}).get(seat_id):
        raise _http(423, "seat_locked", "The instructor locked this seat")
    hs = (ctx.state.get("holdings") or {}).get(seat_id) or []
    if not hs or not cfg.is_exclusive(seat_id) or store.holder_status(ctx.study_id, hs[0]) == "reclaimable":
        await claim(ctx, [seat_id])
        return {"claimed": True}
    if hs[0]["person_id"] == ctx.person.id:
        raise _http(409, "already_holder", "You already hold this seat")
    prune_requests(ctx.state)
    t = cfg.timing()["handover_timeout_s"]
    req = {"person_id": ctx.person.id, "name": ctx.person.name, "verified": ctx.person.verified,
           "at": store.now_iso(), "expires": time.time() + t, "timeout_s": t}
    ctx.state.setdefault("requests", {})[seat_id] = req
    await store.save_team(ctx.study_id, ctx.state)
    await store.log_event(ctx.study_id, seat_id, ctx.person, "handover_request", seat_id,
                          {"holder": hs[0]["person_id"], "holder_name": hs[0]["name"]})
    return {"claimed": False, "request": req}


async def answer_handover(ctx: SeatCtx, seat_id: str, accept: bool) -> dict[str, Any]:
    _require_enabled(ctx)
    prune_requests(ctx.state)
    req = (ctx.state.get("requests") or {}).get(seat_id)
    if not req:
        raise _http(404, "no_request", "No open request for this seat (it may have timed out)")
    if not ctx.holds(seat_id) and not ctx.instructor:
        raise _http(403, "not_holder", "Only the holder answers a seat request")
    ctx.state["requests"].pop(seat_id, None)
    new = Person(req["person_id"], req.get("name", ""), bool(req.get("verified")))
    if accept:
        ctx.state.setdefault("holdings", {})[seat_id] = [_holding(new, "handover")]
    await store.save_team(ctx.study_id, ctx.state)
    await store.log_event(ctx.study_id, seat_id, ctx.person, "handover_accept" if accept else "handover_decline",
                          seat_id, {"to_person": new.id, "to_name": new.name})
    return {"accepted": accept, "to": new.public()}


async def reassign(ctx: SeatCtx, seat_id: str, person_id: str | None, name: str = "") -> None:
    """Instructor override: move the seat without asking (person_id None/"" frees it)."""
    _require_enabled(ctx)
    _require_seat(ctx, seat_id)
    if not ctx.instructor:
        raise _http(403, "instructor_only", "Only the instructor reassigns seats")
    hs = ctx.state.setdefault("holdings", {}).setdefault(seat_id, [])
    prev = [dict(h) for h in hs]
    if person_id:
        pres = store.presence(ctx.study_id).get(person_id) or {}
        known = next((h for s in (ctx.state.get("holdings") or {}).values() for h in s
                      if h["person_id"] == person_id), None)
        nm = name or pres.get("name") or (known or {}).get("name") or person_id
        ver = bool(pres.get("verified", (known or {}).get("verified", person_id.startswith("iap:"))))
        new = {"person_id": person_id, "name": nm, "verified": ver, "since": store.now_iso(),
               "assigned_by": "instructor"}
        if cfg.is_exclusive(seat_id):
            hs[:] = [new]
        elif not any(h["person_id"] == person_id for h in hs):
            hs.append(new)
    else:
        hs.clear()
    (ctx.state.get("requests") or {}).pop(seat_id, None)
    await store.save_team(ctx.study_id, ctx.state)
    await store.log_event(ctx.study_id, seat_id, ctx.person, "reassign", seat_id,
                          {"from": [h["person_id"] for h in prev], "from_names": [h["name"] for h in prev],
                           "to_person": person_id or "", "to_name": name})


async def set_lock(ctx: SeatCtx, seat_id: str, locked: bool) -> None:
    _require_enabled(ctx)
    _require_seat(ctx, seat_id)
    if not ctx.instructor:
        raise _http(403, "instructor_only", "Only the instructor locks seats")
    lk = ctx.state.setdefault("locked", {})
    if locked:
        lk[seat_id] = {"by": ctx.person.name, "at": store.now_iso()}
    else:
        lk.pop(seat_id, None)
    await store.save_team(ctx.study_id, ctx.state)
    await store.log_event(ctx.study_id, seat_id, ctx.person, "lock" if locked else "unlock", seat_id)


async def switch_active(ctx: SeatCtx, seat_id: str) -> None:
    if seat_id not in ctx.held:
        raise _http(409, "not_holder", "You can only switch to a seat you hold")
    ctx.state.setdefault("active", {})[ctx.person.id] = seat_id
    ctx.active = seat_id
    store.touch(ctx.study_id, ctx.person, active_seat=seat_id)
    await store.save_team(ctx.study_id, ctx.state)
    await store.log_event(ctx.study_id, seat_id, ctx.person, "switch", seat_id)


async def set_preset(ctx: SeatCtx, preset: str | None, optional: list[str] | None) -> None:
    """Choose the team size (instructor or Team leader; anyone while the study has no seats)."""
    if ctx.enabled and not (ctx.instructor or ctx.holds("team_leader")):
        raise _http(403, "lead_only", "Only the Team leader or the instructor changes the team size")
    apply_preset(ctx.state, preset, optional)
    await store.save_team(ctx.study_id, ctx.state)
    await store.log_event(ctx.study_id, "team_leader" if ctx.holds("team_leader") else "", ctx.person, "preset",
                          str(preset or "solo"), {"optional": list(ctx.state.get("optional") or [])})


def apply_preset(state: dict[str, Any], preset: str | None, optional: list[str] | None) -> None:
    pid = cfg.preset_for_size(preset)
    if pid is None:
        state["enabled"] = False
        state["preset"] = None
        state["groups"] = []
        return
    opt = [s for s in (optional or []) if (cfg.seat(s) or {}).get("optional")]
    groups = cfg.groups_for(pid, opt)
    state["enabled"] = True
    state["preset"] = pid
    state["optional"] = opt
    state["groups"] = groups
    used = set(cfg.study_seats(groups))
    for sid in list((state.get("holdings") or {}).keys()):
        if sid not in used:
            state["holdings"].pop(sid, None)


# ─── write permissions ───────────────────────────────────────────────────────

def owner_of_element(state: dict[str, Any], element: dict[str, Any], elements: dict[str, dict]) -> str | None:
    return cfg.resolve_in_study(cfg.element_owner_seat(element, elements), used_seats(state))


def param_keys(owner_seat: str | None, fields: list[str]) -> list[str]:
    prefix = cfg.owner_prefix(owner_seat) if owner_seat else "unowned"
    return [f"{prefix}.{f}" for f in fields]


async def element_edit_decision(request: Request, element: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Who may change ``fields`` of ``element`` (ruling 5).

    Returns ``{"mode": "open"|"direct"|"pending", "ctx", "owner"}``; raises the 403/409/423 the
    route returns. ``pending`` is only returned when the request carries the confirmation
    header; without it the editor first gets 409 ``owned_by_other_seat`` (the warning).
    """
    from ..routers import elements as el_router
    ctx = await seat_ctx(request, element["study_id"])
    if not ctx.enabled:
        return {"mode": "open", "ctx": ctx, "owner": None}
    owned = [f for f in fields if f not in cfg.layout_fields()]
    owner = owner_of_element(ctx.state, element, el_router._elements)
    if not owned:
        return {"mode": "direct", "ctx": ctx, "owner": owner}
    if owner is None or ctx.holds(owner):
        return {"mode": "direct", "ctx": ctx, "owner": owner}
    if not (ctx.instructor or ctx.active_kind in cfg.EDITING_KINDS):
        raise _http(403, "read_only_seat", "Your seat cannot edit design parameters")
    holder = ((ctx.state.get("holdings") or {}).get(owner) or [{}])[0].get("name", "")
    if not confirmed_review(request):
        raise _http(409, "owned_by_other_seat",
                    f"Owned by {cfg.label(owner)['en']} — your change goes to them for review",
                    owner_seat=owner, owner_label=cfg.label(owner), owner_holder=holder,
                    fields=owned, param_keys=param_keys(owner, owned), element_name=element.get("name", ""))
    return {"mode": "pending", "ctx": ctx, "owner": owner}


async def element_delete_allowed(request: Request, element: dict[str, Any]) -> SeatCtx:
    from ..routers import elements as el_router
    ctx = await seat_ctx(request, element["study_id"])
    if not ctx.enabled or ctx.instructor:
        return ctx
    owner = owner_of_element(ctx.state, element, el_router._elements)
    if ctx.holds(owner) or ctx.holds("team_leader") or ctx.holds("systems_engineer"):
        return ctx
    raise _http(403, "delete_not_allowed",
                f"Only {cfg.label(owner)['en'] if owner else 'the owning seat'}, the Team leader, Systems "
                f"or the instructor delete this element", owner_seat=owner)


async def require_gate_role(request: Request, study_id: str) -> SeatCtx:
    """Gate review actions and the gate profile: Team leader or instructor."""
    ctx = await seat_ctx(request, study_id)
    if not ctx.enabled or ctx.instructor or ctx.holds("team_leader"):
        return ctx
    raise _http(403, "lead_only", "Only the Team leader or the instructor records gate decisions")


async def require_study_delete(request: Request) -> None:
    """Only the instructor deletes studies (open on a laptop until someone is instructor)."""
    from .identity import instructor_emails
    p = person_of(request)
    if await store.is_instructor(p):
        return
    if not instructor_emails() and not await store.laptop_instructor():
        return  # laptop, nobody has claimed the instructor role: single-user mode
    raise _http(403, "instructor_only", "Only the instructor deletes studies")


async def require_instructor(request: Request) -> Person:
    p = person_of(request)
    if not await store.is_instructor(p):
        raise _http(403, "instructor_only", "Instructor only")
    return p
