"""Console seats over HTTP: identity, command authority and the seat board.

Three modes (``SMO_SEATS``):

``iap``    cloud (the default when the ground env says so, see
           ``smo_common.web.identity.cloud_deployment``). The person is the
           IAP account. ``X-Goog-IAP-JWT-Assertion`` is verified against
           Google's keys and ``SMO_IAP_AUDIENCES`` (``SMO_IAP_VERIFY=0`` falls
           back to trusting the plain email header, logged loudly, and every
           person is then marked unverified).
``local``  a laptop or classroom LAN without IAP: the person is this browser
           (the ``c2o_lb`` cookie the logbook already uses) with a typed
           name, always marked "unverified". Instructor = a browser on the
           MCS host itself (loopback).
``off``    the default without IAP: no registry enforcement. Positions are
           self-asserted as before, every command is logged "unverified",
           and unknown positions are still refused.

In ``iap`` and ``local`` the position of every command comes from the
registry: a request may name a position only to switch among the desks the
person holds; anything else is refused (403). Instructor-only actions check
the account against ``SMO_INSTRUCTORS`` on the server.

Ground activity summary
-----------------------
:class:`GroundActivity` is the identity-free feed for the instructor console
timeline (alarm acknowledgements, procedure steps, GO/NO-GO, voice talk,
desk staffing). Items are built from a fixed set of keys; no person id,
name, email, screen or connection id is ever put in one (a test asserts it).
It is served at ``/api/seats/activity`` on the ground: the GSG answers
``/api/seats*`` locally (it forwards them to the MCS on the ground VM and
never over the space link), so the instructor console at sim.<domain> reads
it without anything crossing the link.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from aiohttp import web

from .seats import SeatError, SeatRegistry, conn_public

logger = logging.getLogger(__name__)

MODES = ("off", "local", "iap")
SCREEN_HEADER = "X-SMO-Screen"
_NO_STORE = {"Cache-Control": "no-store"}
_LOOPBACK = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}


def _truthy(v) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "yes", "on")


def mode_from_env(env: Optional[Mapping[str, str]] = None) -> str:
    env = os.environ if env is None else env
    m = str(env.get("SMO_SEATS", "") or "").strip().lower()
    if m in MODES:
        return m
    if m:
        logger.warning("SMO_SEATS=%r is not one of %s", m, MODES)
    from smo_common.web.identity import cloud_deployment
    return "iap" if cloud_deployment(env) else "off"


class SeatHttpError(Exception):
    def __init__(self, status: int, code: str, message: str, **params):
        super().__init__(message)
        self.status, self.code, self.message, self.params = status, code, message, params

    def response(self) -> web.Response:
        return web.json_response({"status": "denied" if self.status == 403 else "error",
                                  "error": self.message.format(**self.params),
                                  "message": self.message.format(**self.params),
                                  "code": self.code, "params": self.params},
                                 status=self.status, headers=_NO_STORE)


@dataclass(frozen=True)
class Identity:
    person_id: str
    name: str             # "" = a local browser that has not typed a name yet
    verified: bool
    instructor: bool
    new_cookie: Optional[str] = None


@dataclass(frozen=True)
class Actor:
    """Who sends a command, as the server decided it."""
    position: str
    person_id: str = ""
    name: str = ""
    screen: str = ""
    conn_id: str = ""
    verified: bool = False
    enforced: bool = False
    instructor: bool = False

    def log_fields(self) -> dict:
        """Command-log fields. ``person`` is empty when nobody is known
        (seats off and no typed name); ``verified`` is False unless the IAP
        assertion was checked."""
        return {"person": self.name, "screen": self.screen,
                "verified": bool(self.verified)}


# ── Anonymous ground activity ─────────────────────────────────────────────

#: The only keys an activity item may carry. Nothing here names a person.
ITEM_KEYS = frozenset({"seq", "ts", "ts_end", "lane", "kind", "position", "ref", "alarm_id",
                       "subsystem", "severity", "procedure", "step", "step_text", "result",
                       "response", "label", "loop", "state", "outcome"})
LANES = ("alarm", "proc", "voice", "crew")


class GroundActivity:
    """What the team did on the ground, by position only."""

    def __init__(self, sim_clock: Callable[[], float], maxlen: int = 4000):
        self._sim = sim_clock
        self.items: deque = deque(maxlen=maxlen)
        self._seq = 0
        self.talking: dict[tuple, float] = {}
        self.staffing: dict[str, dict] = {}

    def add(self, lane: str, kind: str, position: str, **fields) -> dict:
        self._seq += 1
        it = {"seq": self._seq, "ts": float(fields.pop("ts", None) or self._sim()),
              "lane": lane, "kind": kind, "position": str(position or "")}
        for k, v in fields.items():
            if k in ITEM_KEYS and v is not None:
                it[k] = v
        self.items.append(it)
        return it

    def alarm_ack(self, position: str, alarm: Mapping) -> None:
        self.add("alarm", "g_ack", position, alarm_id=alarm.get("id"),
                 subsystem=str(alarm.get("subsystem") or ""),
                 severity=alarm.get("severity"),
                 label=str(alarm.get("name") or alarm.get("parameter") or "")[:120],
                 ref=str(alarm.get("parameter") or "")[:40] or None)

    def proc_step(self, position: str, procedure: str, step: int, step_text: str,
                  result: str) -> None:
        self.add("proc", "g_step", position, procedure=procedure, step=int(step),
                 step_text=str(step_text or "")[:120], result=result)

    def proc_event(self, position: str, procedure: str, outcome: str) -> None:
        self.add("proc", "g_proc", position, procedure=procedure, outcome=outcome)

    def gonogo(self, kind: str, position: str, *, label: str = "", response: str = "",
               outcome: str = "") -> None:
        self.add("proc", kind, position, label=label[:80], response=response or None,
                 outcome=outcome or None)

    def talk(self, position: str, loop: str, on: bool) -> Optional[dict]:
        key = (position, loop)
        now = float(self._sim())
        if on:
            self.talking.setdefault(key, now)
            return None
        start = self.talking.pop(key, None)
        if start is None:
            return None
        return self.add("voice", "talk", position, loop=loop, ts=start, ts_end=max(start, now))

    def crew(self, position: str, state: str) -> None:
        prev = self.staffing.get(position, {}).get("state")
        if prev == state:
            return
        now = float(self._sim())
        self.staffing[position] = {"state": state, "since": now}
        self.add("crew", "seat", position, state=state, ts=now)

    def summary(self, since: int, positions: list[dict]) -> dict:
        items = [dict(i) for i in self.items if i["seq"] > since]
        now = float(self._sim())
        return {"schema": "c2o.ground-activity/1", "seq": self._seq, "now_sim": now,
                "positions": positions,
                "talking": [{"position": p, "loop": lp, "since": t}
                            for (p, lp), t in sorted(self.talking.items())],
                "items": items}


# ── The service ───────────────────────────────────────────────────────────

class SeatService:
    """Identity + registry + activity for one MCS."""

    def __init__(self, positions: list[str], *, sim_clock: Callable[[], float],
                 env: Optional[Mapping[str, str]] = None, mode: Optional[str] = None,
                 verifier=None, clock: Callable[[], float] = time.time,
                 labels: Optional[Mapping[str, str]] = None):
        env = dict(os.environ if env is None else env)
        self.env = env
        self.mode = mode or mode_from_env(env)
        self.positions = list(positions)
        #: {position: {"label": English label}} for pages that cannot read
        #: the MCS's /api/positions (the instructor console via the GSG).
        self.positions_meta = {p: {"label": str((labels or {}).get(p) or p)} for p in self.positions}
        self.registry = SeatRegistry(self.positions, clock=clock, sim_clock=sim_clock)
        self.activity = GroundActivity(sim_clock)
        from smo_common.web.identity import instructor_emails
        self.instructors = instructor_emails(env)
        self.verify_jwt = self.mode == "iap" and str(env.get("SMO_IAP_VERIFY", "1")).strip() != "0"
        self.verifier = verifier
        if self.verify_jwt and self.verifier is None:
            from smo_common.web.iap_jwt import IapVerifier
            self.verifier = IapVerifier.from_env(env)
        self._seen_events = 0
        if self.mode == "iap":
            if not self.verify_jwt:
                logger.warning("SEATS: IAP JWT verification is OFF (SMO_IAP_VERIFY=0): the plain "
                               "email header is trusted and every person is marked unverified")
            elif not getattr(self.verifier, "audiences", None):
                logger.error("SEATS: SMO_IAP_AUDIENCES is empty: every request will be refused "
                             "until the IAP audiences are configured (deploy/gcp README)")
        if not self.instructors and self.mode == "iap":
            logger.warning("SEATS: SMO_INSTRUCTORS is empty: nobody can use the instructor board")
        logger.info("Console seats: mode=%s, %d positions", self.mode, len(self.positions))

    @property
    def enforced(self) -> bool:
        return self.mode in ("local", "iap")

    # ── identity ────────────────────────────────────────────────────────
    async def identify(self, request: web.Request, *, typed_name: str = "") -> Optional[Identity]:
        """The person behind a request, or None (local: no name yet).
        Raises SeatHttpError(401) when IAP identity is required and absent
        or does not verify."""
        if self.mode == "iap":
            from smo_common.web.identity import iap_user
            header_email = iap_user(request.headers)
            if self.verify_jwt:
                from smo_common.web.iap_jwt import IAP_JWT_HEADER, IapJwtError
                token = request.headers.get(IAP_JWT_HEADER, "")
                if not token:
                    raise SeatHttpError(401, "sign-in", "Sign-in required (IAP identity missing)")
                try:
                    claims = await self.verifier.verify(token)
                except IapJwtError as e:
                    logger.warning("IAP assertion refused: %s", e.code)
                    raise SeatHttpError(401, "iap-" + e.code,
                                        "Sign-in could not be verified ({why})", why=e.code) from None
                email = claims["email"]
                if header_email and header_email != email:
                    raise SeatHttpError(401, "iap-mismatch", "IAP headers disagree")
                verified = True
            else:
                if not header_email:
                    raise SeatHttpError(401, "sign-in", "Sign-in required (IAP identity missing)")
                email, verified = header_email, False
            p = self.registry.persons.get(email)
            name = (p.display_name if p else "") or email
            return Identity(email, name, verified, email in self.instructors)
        from smo_common.logbook.identity import identify as cookie_identity
        ci = cookie_identity({}, request.cookies)          # local: never trust a header
        person_id = ci.person_id
        p = self.registry.persons.get(person_id)
        name = clean_name(typed_name) or (p.display_name if p else "")
        instructor = self._local_instructor(request)
        if not name:
            return Identity(person_id, "", False, instructor, ci.new_cookie)
        return Identity(person_id, name, False, instructor, ci.new_cookie)

    def _local_instructor(self, request: web.Request) -> bool:
        if self.mode == "off":
            from smo_common.web.identity import is_instructor
            return is_instructor(request.headers, self.env)
        return (request.remote or "") in _LOOPBACK

    async def person(self, request: web.Request, *, typed_name: str = "",
                     require: bool = True) -> Optional[Identity]:
        ident = await self.identify(request, typed_name=typed_name)
        if ident is None or not ident.name:
            if require:
                raise SeatHttpError(401, "name", "Type your name first")
            return ident
        self.registry.touch_person(ident.person_id, ident.name, verified=ident.verified,
                                   instructor=ident.instructor)
        return ident

    async def instructor(self, request: web.Request) -> Identity:
        if self.mode == "off":
            if not self._local_instructor(request):
                raise SeatHttpError(403, "instructor", "Only an instructor may do this")
            ident = Identity("local:instructor", "Instructor", False, True)
            self.registry.touch_person(ident.person_id, ident.name, verified=False, instructor=True)
            return ident
        ident = await self.person(request, require=self.mode != "local")
        if self.mode == "local" and (ident is None or not ident.name):
            if not self._local_instructor(request):
                raise SeatHttpError(403, "instructor", "Only an instructor may do this")
            ident = await self.person(request, typed_name="Instructor")
        if not ident.instructor:
            raise SeatHttpError(403, "instructor", "Only an instructor may do this")
        return ident

    # ── command authority ───────────────────────────────────────────────
    async def actor_for(self, request: web.Request, requested: Any = "") -> Actor:
        """The position a command is sent from, decided on the server."""
        requested = str(requested or "").strip()
        conn_id = screen_id(request)
        if not self.enforced:
            pos = requested or "flight_director"
            if self.positions and pos not in self.positions:
                raise SeatHttpError(403, "unknown-position", "Unknown position {position}",
                                    position=pos[:40])
            soft = None
            try:
                soft = await self.identify(request)
            except Exception:  # noqa: BLE001 -- seats off: identity is best effort
                soft = None
            conn = self.registry.conns.get(conn_id)
            name = ""
            if soft is not None:
                p = self.registry.persons.get(soft.person_id)
                name = p.display_name if p else ""
            return Actor(pos, soft.person_id if soft else "", name,
                         conn.label if conn else "", conn_id if conn else "", False, False,
                         bool(soft and soft.instructor))
        ident = await self.person(request)
        pid = ident.person_id
        held = self.registry.command_positions(pid)
        conn = self.registry.conns.get(conn_id)
        if conn is not None and conn.person_id != pid:
            conn = None
        if requested:
            if requested not in self.positions:
                raise SeatHttpError(403, "unknown-position", "Unknown position {position}",
                                    position=requested[:40])
            if requested not in held:
                raise SeatHttpError(403, "not-holder",
                                    "You do not hold the {position} desk", position=requested,
                                    held=held)
            pos = requested
        else:
            pos = conn.active_position if conn is not None and conn.active_position in held \
                else (held[0] if held else "")
            if not pos:
                raise SeatHttpError(403, "no-desk", "Claim a desk before commanding")
        return Actor(pos, pid, ident.name, conn.label if conn else "",
                     conn.conn_id if conn else "", ident.verified, True, ident.instructor)

    def may_act_for(self, person_id: str, position: str) -> bool:
        return (not self.enforced) or position in self.registry.command_positions(person_id)

    # ── activity feed (anonymous) ───────────────────────────────────────
    def crew_positions(self) -> list[dict]:
        out = []
        for pos in self.positions:
            st = self.registry.seat_state(pos) if self.enforced else "unknown"
            out.append({"id": pos, "state": st, "locked": self.registry.is_locked(pos),
                        "pair": self.registry.pair_mode.get(pos)})
        return out

    def tick(self) -> None:
        """Presence edges and the staffing lane (call every few seconds)."""
        self.registry.tick()
        if self.enforced:
            for pos in self.positions:
                self.activity.crew(pos, self.registry.seat_state(pos))

    def activity_summary(self, since: int = 0) -> dict:
        return self.activity.summary(since, self.crew_positions())

    # ── views ───────────────────────────────────────────────────────────
    def me(self, ident: Optional[Identity], conn=None) -> dict:
        if ident is None:
            return {"needs_name": True}
        pid = ident.person_id
        return {"name": ident.name, "verified": ident.verified, "instructor": ident.instructor,
                "needs_name": not ident.name,
                "positions": self.registry.positions_of(pid),
                "command_positions": self.registry.command_positions(pid),
                "view_positions": self.registry.view_positions(pid),
                "requests": [{"position": r.position,
                              "from": self.registry.public_person(r.from_person)["name"],
                              "expires_in_s": max(0, round(r.expires - self.registry._now()))}
                             for r in self.registry.requests_for(pid)],
                "outgoing": [{"position": r.position,
                              "expires_in_s": max(0, round(r.expires - self.registry._now()))}
                             for r in self.registry.requests.values() if r.from_person == pid],
                "screen": conn_public(conn) if conn is not None else None,
                "screens": [conn_public(c) for c in self.registry.conns.values()
                            if c.person_id == pid]}

    def participant_board(self) -> dict:
        b = self.registry.board(for_instructor=False)
        for col in b["positions"]:
            if col["holder"]:
                col["holder"] = {k: col["holder"][k] for k in ("name", "verified", "presence")}
            col["pairs"] = [{"name": x["name"], "role": x["role"]} for x in col["pairs"]]
            if col["request"]:
                col["request"] = {"pending": True}
        return b


def screen_id(request) -> str:
    """The ``X-SMO-Screen`` connection id of a request ("" if none)."""
    try:
        raw = request.headers.get(SCREEN_HEADER)
    except Exception:  # noqa: BLE001
        return ""
    return raw.strip()[:64] if isinstance(raw, str) else ""


def clean_name(raw) -> str:
    from .voice import clean_name as _c
    return _c(raw)


# ── Routes ────────────────────────────────────────────────────────────────

def register_seat_routes(app: web.Application, svc: SeatService, *,
                         static_dir=None, default_lang: str = "en") -> None:
    """Mount /seats (board page) and /api/seats* on the MCS."""
    from pathlib import Path
    static_dir = Path(static_dir) if static_dir else Path(__file__).parent / "static" / "modern"
    page = static_dir / "seats.html"
    reg = svc.registry

    def ok(payload: dict, *, cookie: Optional[str] = None, request=None) -> web.Response:
        r = web.json_response(payload, headers=_NO_STORE)
        if cookie:
            from smo_common.logbook.identity import cookie_header
            secure = bool(request is not None and request.secure)
            r.headers["Set-Cookie"] = cookie_header(cookie, secure=secure)
        return r

    async def body_of(request) -> dict:
        if request.content_type != "application/json":
            raise SeatHttpError(415, "json", "Send application/json")
        if (request.content_length or 0) > 8192:
            raise SeatHttpError(413, "too-large", "Request too large")
        try:
            b = await request.json()
        except ValueError:
            raise SeatHttpError(400, "json", "Body is not JSON") from None
        if not isinstance(b, dict):
            raise SeatHttpError(400, "json", "Body must be an object")
        return b

    def guard(fn):
        async def h(request):
            try:
                return await fn(request)
            except SeatHttpError as e:
                return e.response()
            except SeatError as e:
                return SeatHttpError(e.status, e.code, str(e), **e.params).response()
        h.__name__ = fn.__name__
        return h

    def need_enforced():
        if not svc.enforced:
            raise SeatHttpError(409, "seats-off",
                                "Console seats are off (SMO_SEATS=off): positions are chosen freely")

    async def seats_page(request):
        if not page.is_file():
            raise web.HTTPNotFound(text="seat board not installed")
        from smo_common.web.http import stamp_asset_versions
        html = page.read_text(encoding="utf-8")
        if default_lang and default_lang != "en":
            from smo_common.i18n import inject_default_lang
            html = inject_default_lang(html, default_lang)
        return web.Response(text=stamp_asset_versions(html, app), content_type="text/html",
                            headers={"Cache-Control": "no-cache"})

    @guard
    async def get_seats(request):
        ident = None
        cookie = None
        if svc.enforced:
            try:
                ident = await svc.person(request, require=False)
            except SeatHttpError as e:
                if e.status != 401:
                    raise
            cookie = ident.new_cookie if ident else None
        conn = reg.conns.get(screen_id(request))
        if conn is not None and ident is not None and conn.person_id != ident.person_id:
            conn = None
        return ok({"mode": svc.mode, "enforced": svc.enforced,
                   "me": svc.me(ident, conn) if ident is not None else {"needs_name": svc.mode == "local",
                                                                        "signed_in": False},
                   "board": svc.participant_board(),
                   "positions": svc.positions, "positions_meta": svc.positions_meta},
                  cookie=cookie, request=request)

    @guard
    async def connect(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request, typed_name=str(b.get("name") or ""), require=False)
        if ident is None or not ident.name:
            return ok({"mode": svc.mode, "enforced": True, "me": {"needs_name": True}},
                      cookie=ident.new_cookie if ident else None, request=request)
        c = reg.connect(ident.person_id, str(b.get("conn_id") or "") or None,
                        str(b.get("label") or "") or None)
        return ok({"mode": svc.mode, "enforced": True, "conn_id": c.conn_id,
                   "me": svc.me(ident, c), "board": svc.participant_board()},
                  cookie=ident.new_cookie, request=request)

    @guard
    async def heartbeat(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request)
        c = reg.heartbeat(str(b.get("conn_id") or ""), ident.person_id,
                          str(b.get("position") or "") or None)
        return ok({"conn_id": c.conn_id, "me": svc.me(ident, c),
                   "board": svc.participant_board()})

    @guard
    async def disconnect(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request)
        reg.disconnect(str(b.get("conn_id") or ""), ident.person_id)
        return ok({"status": "ok"})

    def _pos(b) -> str:
        return str(b.get("position") or "").strip()[:40]

    @guard
    async def claim(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request)
        reg.claim(ident.person_id, _pos(b))
        return ok({"status": "claimed", "me": svc.me(ident), "board": svc.participant_board()})

    @guard
    async def release(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request)
        reg.release(ident.person_id, _pos(b))
        return ok({"status": "released", "me": svc.me(ident), "board": svc.participant_board()})

    @guard
    async def request_seat(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request)
        res = reg.request(ident.person_id, _pos(b))
        return ok(dict(res, me=svc.me(ident), board=svc.participant_board()))

    @guard
    async def answer(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request)
        res = reg.answer(ident.person_id, _pos(b), bool(b.get("accept")))
        return ok(dict(res, me=svc.me(ident), board=svc.participant_board()))

    @guard
    async def screen(request):
        b = await body_of(request)
        need_enforced()
        ident = await svc.person(request)
        cid = str(b.get("conn_id") or "")
        if "label" in b:
            reg.rename_screen(cid, str(b.get("label") or ""), ident.person_id)
        v = b.get("view")
        if isinstance(v, dict):
            reg.set_view(cid, str(v.get("kind") or ""), [str(x) for x in (v.get("positions") or [])
                                                         if isinstance(x, str)], ident.person_id)
        c = reg.conns.get(cid)
        return ok({"status": "ok", "screen": conn_public(c) if c else None})

    @guard
    async def talk(request):
        """The voice panel reports push-to-talk edges: position + loop only
        reach the activity feed. The position must be one the person may
        use (the token was minted for it)."""
        b = await body_of(request)
        loop = str(b.get("loop") or "").strip()[:32]
        if not loop:
            raise SeatHttpError(400, "loop", "loop required")
        pos = str(b.get("position") or "").strip()[:40]
        from .voice import ROLE_POSITIONS
        if pos in ROLE_POSITIONS:
            await svc.instructor(request)
        else:
            actor = await svc.actor_for(request, pos)
            pos = actor.position
        svc.activity.talk(pos, loop, bool(b.get("on")))
        return ok({"status": "ok"})

    # instructor
    @guard
    async def board(request):
        await svc.instructor(request)
        reg.expire_requests()
        b = reg.board(for_instructor=True)
        b.update({"mode": svc.mode, "enforced": svc.enforced})
        return ok(b)

    @guard
    async def assign(request):
        b = await body_of(request)
        need_enforced()
        ins = await svc.instructor(request)
        person = b.get("person")
        reg.assign(ins.person_id, _pos(b), str(person) if person else None)
        return ok({"status": "ok"})

    @guard
    async def bench(request):
        b = await body_of(request)
        need_enforced()
        ins = await svc.instructor(request)
        freed = reg.bench(ins.person_id, str(b.get("person") or ""))
        return ok({"status": "ok", "freed": freed})

    @guard
    async def vacate(request):
        b = await body_of(request)
        need_enforced()
        ins = await svc.instructor(request)
        reg.vacate(ins.person_id, _pos(b))
        return ok({"status": "ok"})

    @guard
    async def lock(request):
        b = await body_of(request)
        need_enforced()
        ins = await svc.instructor(request)
        reg.lock(ins.person_id, bool(b.get("on")), _pos(b) or None)
        return ok({"status": "ok", "locked": reg.locked_board})

    @guard
    async def rotate(request):
        await body_of(request)
        need_enforced()
        ins = await svc.instructor(request)
        moved = reg.rotate(ins.person_id)
        return ok({"status": "ok", "moved": len(moved)})

    @guard
    async def pair(request):
        b = await body_of(request)
        need_enforced()
        ins = await svc.instructor(request)
        if b.get("person"):
            reg.pair(ins.person_id, _pos(b), str(b["person"]))
        else:
            mode = b.get("mode")
            reg.set_pair_mode(ins.person_id, _pos(b), str(mode) if mode else None)
        return ok({"status": "ok"})

    @guard
    async def events(request):
        """The transfer log WITH names: assessment data, ground only."""
        await svc.instructor(request)
        rows = []
        for e in reg.events:
            rows.append(dict(e, person=reg.public_person(e["person_id"])["name"]
                             if e.get("person_id") else "",
                             by_name=reg.public_person(e["by"])["name"] if e.get("by") else ""))
        if request.query.get("format") == "csv":
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["seq", "ts_sim", "action", "position", "person", "by"])
            for r in rows:
                w.writerow([r["seq"], r["ts_sim"], r["action"], r["position"], r["person"],
                            r["by_name"]])
            return web.Response(text=buf.getvalue(), content_type="text/csv",
                                headers={**_NO_STORE, "Content-Disposition":
                                         'attachment; filename="seat_events.csv"'})
        return ok({"events": rows})

    @guard
    async def activity(request):
        """Identity-free ground activity for the instructor timeline."""
        await svc.instructor(request)
        try:
            since = int(request.query.get("since", "0") or 0)
        except ValueError:
            since = 0
        return ok(svc.activity_summary(since))

    app.router.add_get("/seats", seats_page)
    app.router.add_get("/api/seats", get_seats)
    app.router.add_post("/api/seats/connect", connect)
    app.router.add_post("/api/seats/heartbeat", heartbeat)
    app.router.add_post("/api/seats/disconnect", disconnect)
    app.router.add_post("/api/seats/claim", claim)
    app.router.add_post("/api/seats/release", release)
    app.router.add_post("/api/seats/request", request_seat)
    app.router.add_post("/api/seats/answer", answer)
    app.router.add_post("/api/seats/screen", screen)
    app.router.add_post("/api/seats/talk", talk)
    app.router.add_get("/api/seats/board", board)
    app.router.add_post("/api/seats/assign", assign)
    app.router.add_post("/api/seats/bench", bench)
    app.router.add_post("/api/seats/vacate", vacate)
    app.router.add_post("/api/seats/lock", lock)
    app.router.add_post("/api/seats/rotate", rotate)
    app.router.add_post("/api/seats/pair", pair)
    app.router.add_get("/api/seats/events", events)
    app.router.add_get("/api/seats/activity", activity)


def summary_has_identity(summary: Any, secrets_: list[str]) -> list[str]:
    """Which of ``secrets_`` (emails, names, ids) occur in ``summary``
    (test helper, also usable as a runtime self-check)."""
    blob = json.dumps(summary, sort_keys=True).lower()
    return [s for s in secrets_ if s and s.lower() in blob]
