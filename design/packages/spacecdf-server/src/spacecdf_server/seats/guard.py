"""Server-side write guard for studies that use seats (WP9).

One middleware in front of every ``/api`` write (POST/PUT/PATCH/DELETE) that names a study
(path ``/studies/{id}``, ``/design/{id}``, ``?study_id=``, an element / interface /
requirement id, or ``"study_id"`` in the JSON body). For a study with seats:

* the instructor may always write (Line Manager + Team Leader rights; ownership still applies
  to parameters, see ``service.element_edit_decision``);
* a frozen study refuses writes (423 ``study_frozen``);
* a person with no seat, or whose active seat is Observer, may not write (403);
* the Customer may only write *mission-level* requirements (403 ``customer_requirements_only``).

Parameter ownership, element deletion, gate decisions and study deletion are checked in the
routes themselves (``service``). Seat, instructor, logbook and identity routes are exempt.
Studies without seats are not touched.

Required seats (PI decision, Nov 2026): a study that needs a disposal device (a drag sail or
another deorbit device in its product tree, or ``disposal_method`` drag_sail / propulsive) or any
ΔV gets the optional **Propulsion** seat, which owns the disposal function (the drag sail). The
guard adds it to the team (``ensure_required_seats``) before any write to the study and when the
team is read, so the seat card is there to claim even when the preset or the wizard left it out.
Apply from the Comms & OBDH seat (link budget → ``PATCH /studies/{id}/mission``) is an ordinary
write: it is never turned into a pending change for the Team leader (W1.04).
"""
from __future__ import annotations

import json
import re
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import config as cfg
from . import store
from .service import seat_ctx

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_EXEMPT = (
    re.compile(r"^/api/studies/[^/]+/team(/|$)"),
    re.compile(r"^/api/instructor(/|$)"),
    re.compile(r"^/api/seats(/|$)"),
    re.compile(r"^/api/logbook(/|$)"),
    re.compile(r"^/api/whoami$"),
    re.compile(r"^/api/studies/?$"),                       # create a study
    re.compile(r"^/api/studies/[^/]+/?$"),                 # delete: instructor check in the route
)
_STUDY_PATH = re.compile(r"^/api/(?:studies|design)/([^/?]+)")
_ELEMENT_PATH = re.compile(r"^/api/elements/([^/?]+)")
_IFACE_PATH = re.compile(r"^/api/interfaces/([^/?]+)")
_REQ_PATH = re.compile(r"^/api/requirements/([^/?]+)")
_REQ_ROUTE = re.compile(r"^/api/requirements(/|$)")
_TEAM_READ = re.compile(r"^/api/studies/([^/]+)/team/?$")


# ─── required seats (PI decision: Propulsion owns disposal) ───────────────────

def required_optional_seats(study: Any, elements: list[dict[str, Any]]) -> list[str]:
    """Optional seats a study must have: Propulsion when it needs ΔV or a disposal device."""
    need: list[str] = []
    req = getattr(study, "requirements", None)
    orbit = getattr(req, "orbit", None)
    dv = 0.0
    try:
        dv = float(getattr(orbit, "delta_v_insertion_ms", 0) or 0) + float(getattr(orbit, "delta_v_maintenance_ms", 0) or 0)
    except (TypeError, ValueError):
        dv = 0.0
    method = str(getattr(req, "disposal_method", "") or "").lower()
    device = method in ("drag_sail", "propulsive") or any(
        cfg.is_disposal_device(e) or str(e.get("subsystem_domain") or "").lower() in ("propulsion", "prop")
        for e in elements if not e.get("deleted_at"))
    if dv > 0 or device:
        need.append("propulsion_engineer")
    return need


async def ensure_required_seats(study_id: str) -> list[str]:
    """Add the required optional seats to a seat study's team; returns the seats added."""
    state = store.peek_team(study_id)
    if state is None:
        state = await store.get_team(study_id)
    if not state.get("enabled") or not state.get("preset"):
        return []
    from ..routers.elements import _elements
    from ..routers.studies import get_study_store
    study = get_study_store().get(study_id)
    if study is None:
        return []
    els = [e for e in _elements.values() if e.get("study_id") == study_id]
    used = set(cfg.study_seats(state.get("groups") or []))
    missing = [s for s in required_optional_seats(study, els) if s not in used]
    if not missing:
        return []
    optional = [*list(state.get("optional") or []), *missing]
    state["optional"] = optional
    state["groups"] = cfg.groups_for(state["preset"], optional)
    await store.save_team(study_id, state)
    await store.log_event(study_id, "", None, "seat_required", ", ".join(missing),
                          {"reason": "disposal device or delta-V (PI decision: Propulsion owns disposal)"})
    return missing


def _deny(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"detail": {"code": code, "message": message}}, status_code=status)


async def _body_json(request: Request) -> dict[str, Any]:
    if "json" not in (request.headers.get("content-type") or ""):
        return {}
    try:
        raw = await request.body()
        if not raw or len(raw) > 2_000_000:
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


async def study_of(request: Request, body: dict[str, Any]) -> str | None:
    path = request.url.path
    m = _STUDY_PATH.match(path)
    if m and m.group(1) not in ("", "local"):
        return m.group(1)
    q = request.query_params.get("study_id")
    if q:
        return q
    from ..routers import elements as el_router
    m = _ELEMENT_PATH.match(path)
    if m and m.group(1) in el_router._elements:
        return el_router._elements[m.group(1)].get("study_id")
    m = _IFACE_PATH.match(path)
    if m and m.group(1) in el_router._interfaces:
        return el_router._interfaces[m.group(1)].get("study_id")
    m = _REQ_PATH.match(path)
    if m:
        from ..routers import requirements as req_router
        r = req_router._requirements.get(m.group(1))
        if r:
            return r.get("study_id")
    sid = body.get("study_id")
    return sid if isinstance(sid, str) and sid else None


def _customer_may(request: Request, body: dict[str, Any]) -> bool:
    path = request.url.path
    if not _REQ_ROUTE.match(path):
        return False
    m = _REQ_PATH.match(path)
    if m and m.group(1) not in ("", "tree", "verify"):
        from ..routers import requirements as req_router
        r = req_router._requirements.get(m.group(1)) or {}
        if path.rstrip("/").endswith("/derive"):
            return False
        return r.get("level") == "mission"
    return (body.get("level") or "system") == "mission"


async def _ensure(sid: str) -> None:
    try:
        await ensure_required_seats(sid)
    except Exception:  # noqa: BLE001 — never block a request on this
        import logging
        logging.getLogger(__name__).debug("required seats not checked for %s", sid, exc_info=True)


class SeatGuard(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.method == "GET":
            m = _TEAM_READ.match(path)
            if m:
                await _ensure(m.group(1))
            return await call_next(request)
        if request.method not in WRITE_METHODS or not path.startswith("/api/"):
            return await call_next(request)
        if any(rx.match(path) for rx in _EXEMPT):
            m = _STUDY_PATH.match(path)
            if m and "/team" in path:
                await _ensure(m.group(1))
            return await call_next(request)
        body = await _body_json(request) if request.method in ("POST", "PUT", "PATCH") else {}
        sid = await study_of(request, body)
        if not sid:
            return await call_next(request)
        await _ensure(sid)
        state = store.peek_team(sid)
        if state is None:
            state = await store.get_team(sid)
        if not state.get("enabled"):
            return await call_next(request)
        ctx = await seat_ctx(request, sid)
        if ctx.instructor:
            return await self._logged(request, call_next, sid, ctx)
        if state.get("frozen"):
            return _deny(423, "study_frozen", "The instructor froze this study")
        if not ctx.held:
            return _deny(403, "no_seat", "Claim a seat to edit this study")
        kind = ctx.active_kind
        if kind == "observer":
            return _deny(403, "observer_read_only", "Observers have read-only access")
        if kind == "customer" and not _customer_may(request, body):
            return _deny(403, "customer_requirements_only", "The Customer writes mission requirements only")
        if kind not in (*cfg.EDITING_KINDS, "customer"):
            return _deny(403, "read_only_seat", "This seat cannot edit")
        store.touch(sid, ctx.person, active_seat=ctx.active)
        return await self._logged(request, call_next, sid, ctx)

    @staticmethod
    async def _logged(request: Request, call_next, sid: str, ctx):
        """Every write in a seat study records person and seat. Routes that log a richer event
        (element edits, proposals, gate actions) set ``request.state.seat_logged``."""
        response = await call_next(request)
        if response.status_code < 400 and not getattr(request.state, "seat_logged", False):
            q = request.url.query
            await store.log_event(sid, ctx.active or ("instructor" if ctx.instructor else ""), ctx.person, "write",
                                  f"{request.method} {request.url.path}" + (f"?{q}" if q else ""),
                                  {"status": response.status_code})
        return response
