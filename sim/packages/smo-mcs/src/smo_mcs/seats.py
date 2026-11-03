"""Console seat registry: who holds which MCS desk (redesign WP10).

Decision 6 (docs/plan_2026-11/REDESIGN_DECISIONS.md): seat authority lives in
the MCS on the ground, and no identity crosses the space link. Decision 4:
self-claim plus instructor override, with an instructor lock.

The registry is pure state (no HTTP, no I/O): ``seats_http.py`` maps requests
onto it and the MCS asks it, for every command, which positions a person
holds. Times: ``clock`` is wall time (presence and timeouts are real-time
concerns); ``sim_clock`` stamps events so they line up with telemetry and the
instructor timeline.

Model (redesign s5 "Data model sketch", ops half)::

    Person      person_id = IAP email | "local:<browser id>", display name,
                verified (IAP JWT checked), instructor
    Connection  one browser tab or screen: conn_id, label ("screen 2"),
                view = one position | a tile of held positions | the wall,
                active position, last heartbeat
    Holding     position -> one holder (exclusive desks) plus, when the
                instructor ticks "pair" for that desk, a read-only shadow or a
                second commander
    Request     "Request desk" from its holder, answered within 60 s
    SeatEvent   every transfer and presence change (audit and assessment)

Presence: a holder is *active* while one of their screens has sent a
heartbeat in the last 3 min, *idle* after that, and the desk is *reclaimable*
by someone else after 5 min. Data stays with the desk, not the person.
"""
from __future__ import annotations

import itertools
import re
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

IDLE_S = 180.0
RECLAIM_S = 300.0
REQUEST_TIMEOUT_S = 60.0
#: A connection that has been silent this long is forgotten (its screen chip
#: disappears from the board); the person and their desks are kept.
CONN_FORGET_S = 15 * 60.0
MAX_CONNS_PER_PERSON = 8
MAX_PERSONS = 400
PAIR_MODES = ("shadow", "second")
VIEW_KINDS = ("position", "tile", "wall")
_CONN_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class SeatError(Exception):
    """A refused seat operation. ``code`` is the machine word, ``status``
    the HTTP status the route returns, ``params`` fill the message."""

    def __init__(self, code: str, msg: str, status: int = 409, **params):
        super().__init__(msg)
        self.code, self.status, self.params = code, status, params


@dataclass
class Person:
    person_id: str
    display_name: str
    verified: bool
    instructor: bool = False
    first_seen: float = 0.0
    last_seen: float = 0.0


@dataclass
class Connection:
    conn_id: str
    person_id: str
    label: str
    view: dict = field(default_factory=lambda: {"kind": "position", "positions": []})
    active_position: str = ""
    last_heartbeat: float = 0.0
    created: float = 0.0


@dataclass
class Holding:
    position: str
    person_id: str
    since: float
    since_sim: float
    assigned_by: str            # self | instructor | handover | rotate | reclaim
    role: str = "holder"        # holder | shadow | second


@dataclass
class SeatRequest:
    position: str
    from_person: str
    to_person: str
    created: float
    expires: float


class SeatRegistry:
    def __init__(self, positions: Iterable[str], *,
                 clock: Callable[[], float] = time.time,
                 sim_clock: Optional[Callable[[], float]] = None,
                 idle_s: float = IDLE_S, reclaim_s: float = RECLAIM_S,
                 request_timeout_s: float = REQUEST_TIMEOUT_S):
        self.positions: list[str] = [str(p) for p in positions]
        self._known = set(self.positions)
        self._clock = clock
        self._sim = sim_clock or clock
        self.idle_s, self.reclaim_s, self.request_timeout_s = idle_s, reclaim_s, request_timeout_s
        self.persons: dict[str, Person] = {}
        self.conns: dict[str, Connection] = {}
        self.holders: dict[str, Holding] = {}
        self.pairs: dict[str, list[Holding]] = {}
        self.pair_mode: dict[str, str] = {}
        self.locked_board = False
        self.locked_positions: set[str] = set()
        self.requests: dict[str, SeatRequest] = {}
        self.events: deque = deque(maxlen=5000)
        self._seq = itertools.count(1)
        self.version = 0
        #: last presence state per position, for idle/active edge events
        self._presence: dict[str, str] = {}

    # ── helpers ─────────────────────────────────────────────────────────
    def _now(self) -> float:
        return float(self._clock())

    def _event(self, action: str, position: str = "", person_id: str = "",
               by: str = "", **detail) -> dict:
        ev = {"seq": next(self._seq), "ts": self._now(), "ts_sim": float(self._sim()),
              "action": action, "position": position, "person_id": person_id,
              "by": by, **detail}
        self.events.append(ev)
        self.version += 1
        return ev

    def known(self, position: str) -> bool:
        return position in self._known

    def _need_position(self, position: str) -> None:
        if position not in self._known:
            raise SeatError("unknown-position", "Unknown position {position}", 404,
                            position=str(position)[:40])

    def _need_person(self, person_id: str) -> Person:
        p = self.persons.get(person_id)
        if p is None:
            raise SeatError("unknown-person", "Unknown participant", 404)
        return p

    def _need_instructor(self, by: str) -> None:
        p = self.persons.get(by)
        if p is None or not p.instructor:
            raise SeatError("instructor", "Only an instructor may do this", 403)

    # ── persons and connections ─────────────────────────────────────────
    def touch_person(self, person_id: str, display_name: str, *, verified: bool,
                     instructor: bool) -> Person:
        now = self._now()
        p = self.persons.get(person_id)
        if p is None:
            if len(self.persons) >= MAX_PERSONS:
                self._forget_stale_persons()
            if len(self.persons) >= MAX_PERSONS:
                raise SeatError("full", "Too many participants", 503)
            p = Person(person_id, display_name, verified, instructor, now, now)
            self.persons[person_id] = p
            self.version += 1
        else:
            if display_name and p.display_name != display_name:
                p.display_name = display_name
                self.version += 1
            if p.verified != verified or p.instructor != instructor:
                p.verified, p.instructor = verified, instructor
                self.version += 1
            p.last_seen = now
        return p

    def _forget_stale_persons(self) -> None:
        now = self._now()
        held = {h.person_id for h in self.holders.values()} | {
            h.person_id for hs in self.pairs.values() for h in hs}
        for pid, p in list(self.persons.items()):
            if pid not in held and now - p.last_seen > CONN_FORGET_S and \
                    not any(c.person_id == pid for c in self.conns.values()):
                del self.persons[pid]

    def connect(self, person_id: str, conn_id: Optional[str] = None,
                label: Optional[str] = None) -> Connection:
        self._need_person(person_id)
        now = self._now()
        if conn_id and conn_id in self.conns:
            c = self.conns[conn_id]
            if c.person_id != person_id:
                conn_id = None              # a tab id is never shared between people
            else:
                c.last_heartbeat = now
                if label:
                    c.label = clean_label(label) or c.label
                return c
        if not conn_id or not _CONN_RE.match(conn_id):
            conn_id = secrets.token_urlsafe(12)
        mine = sorted((c for c in self.conns.values() if c.person_id == person_id),
                      key=lambda c: c.last_heartbeat)
        while len(mine) >= MAX_CONNS_PER_PERSON:
            del self.conns[mine.pop(0).conn_id]
        used = {c.label for c in mine}
        n = 1
        while f"screen {n}" in used:
            n += 1
        c = Connection(conn_id, person_id, clean_label(label) or f"screen {n}",
                       last_heartbeat=now, created=now)
        held = self.positions_of(person_id)
        if held:
            c.active_position = held[0]
            c.view = {"kind": "position", "positions": [held[0]]}
        self.conns[conn_id] = c
        self.version += 1
        return c

    def heartbeat(self, conn_id: str, person_id: str,
                  active_position: Optional[str] = None) -> Connection:
        c = self.conns.get(conn_id)
        if c is None or c.person_id != person_id:
            raise SeatError("unknown-connection", "Unknown screen: reconnect", 404)
        c.last_heartbeat = self._now()
        p = self.persons.get(person_id)
        if p is not None:
            p.last_seen = c.last_heartbeat
        if active_position and active_position != c.active_position and \
                active_position in self.command_positions(person_id):
            c.active_position = active_position
            self.version += 1
        return c

    def disconnect(self, conn_id: str, person_id: str) -> None:
        c = self.conns.get(conn_id)
        if c is not None and c.person_id == person_id:
            del self.conns[conn_id]
            self.version += 1

    def rename_screen(self, conn_id: str, label: str, by: str) -> Connection:
        c = self.conns.get(conn_id)
        if c is None:
            raise SeatError("unknown-connection", "Unknown screen", 404)
        if c.person_id != by:
            self._need_instructor(by)
        c.label = clean_label(label) or c.label
        self.version += 1
        return c

    def set_view(self, conn_id: str, kind: str, positions: Iterable[str], by: str) -> Connection:
        """One screen shows one position, a tile of positions its owner
        holds, or the wall. Set by the screen's owner or an instructor."""
        c = self.conns.get(conn_id)
        if c is None:
            raise SeatError("unknown-connection", "Unknown screen", 404)
        if c.person_id != by:
            self._need_instructor(by)
        if kind not in VIEW_KINDS:
            raise SeatError("view", "View must be position, tile or wall", 400)
        pos = [p for p in positions if p in self._known]
        if kind == "position":
            pos = pos[:1]
            if not pos:
                raise SeatError("view", "Choose a position for this screen", 400)
        elif kind == "tile":
            pos = pos or self.positions_of(c.person_id)
        else:
            pos = []
        c.view = {"kind": kind, "positions": pos}
        if kind == "position" and pos[0] in self.command_positions(c.person_id):
            c.active_position = pos[0]
        self._event("view", pos[0] if pos else "", c.person_id, by, screen=c.label, view=kind)
        return c

    # ── who holds what ──────────────────────────────────────────────────
    def holder_of(self, position: str) -> Optional[str]:
        h = self.holders.get(position)
        return h.person_id if h else None

    def positions_of(self, person_id: str) -> list[str]:
        return [p for p in self.positions
                if (self.holders.get(p) and self.holders[p].person_id == person_id)]

    def command_positions(self, person_id: str) -> list[str]:
        """Positions this person may command from: desks they hold, plus
        desks where the instructor made them second commander."""
        out = self.positions_of(person_id)
        for p in self.positions:
            for h in self.pairs.get(p, []):
                if h.person_id == person_id and h.role == "second" and p not in out:
                    out.append(p)
        return out

    def view_positions(self, person_id: str) -> list[str]:
        out = self.command_positions(person_id)
        for p in self.positions:
            for h in self.pairs.get(p, []):
                if h.person_id == person_id and p not in out:
                    out.append(p)
        return out

    def last_heartbeat(self, person_id: str) -> Optional[float]:
        beats = [c.last_heartbeat for c in self.conns.values() if c.person_id == person_id]
        if beats:
            return max(beats)
        p = self.persons.get(person_id)
        return p.last_seen if p else None

    def presence(self, person_id: str) -> str:
        """active | idle | away (reclaimable)."""
        hb = self.last_heartbeat(person_id)
        if hb is None:
            return "away"
        age = self._now() - hb
        if age < self.idle_s:
            return "active"
        return "idle" if age < self.reclaim_s else "away"

    def seat_state(self, position: str) -> str:
        """vacant | staffed | idle | reclaimable (+ locked is separate)."""
        h = self.holders.get(position)
        if h is None:
            return "vacant"
        pr = self.presence(h.person_id)
        return {"active": "staffed", "idle": "idle", "away": "reclaimable"}[pr]

    def is_locked(self, position: str) -> bool:
        return self.locked_board or position in self.locked_positions

    # ── participant actions ─────────────────────────────────────────────
    def claim(self, person_id: str, position: str) -> Holding:
        self._need_person(person_id)
        self._need_position(position)
        if self.is_locked(position):
            raise SeatError("locked", "The instructor has locked the desks", 423)
        cur = self.holders.get(position)
        if cur is not None and cur.person_id == person_id:
            return cur
        action = "claim"
        if cur is not None:
            if self.seat_state(position) != "reclaimable":
                raise SeatError("held", "{position} is held: request it from its holder", 409,
                                position=position)
            action = "reclaim"
        h = Holding(position, person_id, self._now(), float(self._sim()),
                    "reclaim" if action == "reclaim" else "self")
        self.holders[position] = h
        self._drop_pair_entry(position, person_id)
        self.requests.pop(position, None)
        self._event(action, position, person_id, person_id,
                    **({"from_person": cur.person_id} if cur else {}))
        self._point_screens(person_id)
        return h

    def release(self, person_id: str, position: str) -> None:
        self._need_position(position)
        h = self.holders.get(position)
        if h is None or h.person_id != person_id:
            raise SeatError("not-holder", "You do not hold {position}", 409, position=position)
        if self.is_locked(position):
            raise SeatError("locked", "The instructor has locked the desks", 423)
        del self.holders[position]
        self.requests.pop(position, None)
        self._event("release", position, person_id, person_id)
        self._point_screens(person_id)

    def request(self, person_id: str, position: str) -> dict:
        """Ask the holder for the desk; a free desk is simply claimed."""
        self._need_person(person_id)
        self._need_position(position)
        if self.is_locked(position):
            raise SeatError("locked", "The instructor has locked the desks", 423)
        h = self.holders.get(position)
        if h is None or self.seat_state(position) == "reclaimable":
            self.claim(person_id, position)
            return {"status": "claimed"}
        if h.person_id == person_id:
            return {"status": "held"}
        self.expire_requests()
        old = self.requests.get(position)
        if old is not None and old.from_person != person_id:
            raise SeatError("request-pending", "Someone else already asked for {position}", 409,
                            position=position)
        now = self._now()
        self.requests[position] = SeatRequest(position, person_id, h.person_id, now,
                                              now + self.request_timeout_s)
        self._event("request", position, person_id, person_id, to_person=h.person_id)
        return {"status": "requested", "expires_in_s": self.request_timeout_s}

    def answer(self, person_id: str, position: str, accept: bool) -> dict:
        self.expire_requests()
        r = self.requests.get(position)
        h = self.holders.get(position)
        if r is None or h is None or h.person_id != person_id or r.to_person != person_id:
            raise SeatError("no-request", "No pending request for {position}", 404, position=position)
        del self.requests[position]
        if not accept:
            self._event("request_declined", position, r.from_person, person_id)
            return {"status": "declined"}
        self.holders[position] = Holding(position, r.from_person, self._now(), float(self._sim()),
                                         "handover")
        self._drop_pair_entry(position, r.from_person)
        self._event("handover", position, r.from_person, person_id, from_person=person_id)
        self._point_screens(person_id)
        self._point_screens(r.from_person)
        return {"status": "handed-over"}

    def expire_requests(self) -> None:
        now = self._now()
        for pos, r in list(self.requests.items()):
            if now >= r.expires:
                del self.requests[pos]
                self._event("request_expired", pos, r.from_person, "", to_person=r.to_person)

    def requests_for(self, person_id: str) -> list[SeatRequest]:
        self.expire_requests()
        return [r for r in self.requests.values() if r.to_person == person_id]

    # ── instructor actions ──────────────────────────────────────────────
    def assign(self, by: str, position: str, person_id: Optional[str]) -> None:
        """Put ``person_id`` on ``position`` without asking (None = vacate).
        The previous holder goes back to the bench."""
        self._need_instructor(by)
        self._need_position(position)
        if person_id is None:
            return self.vacate(by, position)
        self._need_person(person_id)
        cur = self.holders.get(position)
        if cur is not None and cur.person_id == person_id:
            return
        self.holders[position] = Holding(position, person_id, self._now(), float(self._sim()),
                                         "instructor")
        self._drop_pair_entry(position, person_id)
        self.requests.pop(position, None)
        self._event("assign", position, person_id, by,
                    **({"from_person": cur.person_id} if cur else {}))
        self._point_screens(person_id)
        if cur is not None:
            self._point_screens(cur.person_id)

    def bench(self, by: str, person_id: str) -> list[str]:
        """Take every desk (and pair place) from one person: "sick member"."""
        self._need_instructor(by)
        self._need_person(person_id)
        freed = []
        for pos in list(self.positions):
            h = self.holders.get(pos)
            if h and h.person_id == person_id:
                del self.holders[pos]
                self.requests.pop(pos, None)
                freed.append(pos)
                self._event("vacate", pos, person_id, by)
            self._drop_pair_entry(pos, person_id)
        self._point_screens(person_id)
        return freed

    def vacate(self, by: str, position: str) -> None:
        self._need_instructor(by)
        self._need_position(position)
        h = self.holders.pop(position, None)
        self.requests.pop(position, None)
        if h is not None:
            self._event("vacate", position, h.person_id, by)
            self._point_screens(h.person_id)

    def lock(self, by: str, on: bool, position: Optional[str] = None) -> None:
        self._need_instructor(by)
        if position:
            self._need_position(position)
            if on:
                self.locked_positions.add(position)
            else:
                self.locked_positions.discard(position)
        else:
            self.locked_board = bool(on)
        self._event("lock" if on else "unlock", position or "", "", by)

    def rotate(self, by: str) -> dict:
        """Everyone moves one desk along (positions.yaml order); vacancies
        move too, so the same set of desks stays staffed in a full team."""
        self._need_instructor(by)
        n = len(self.positions)
        if n < 2:
            return {}
        old = {p: self.holders.get(p) for p in self.positions}
        moved = {}
        now, sim = self._now(), float(self._sim())
        for i, p in enumerate(self.positions):
            src = old[self.positions[(i - 1) % n]]
            if src is None:
                self.holders.pop(p, None)
            else:
                self.holders[p] = Holding(p, src.person_id, now, sim, "rotate")
                moved[p] = src.person_id
        self.requests.clear()
        self.pairs.clear()
        self._event("rotate", "", "", by, moves=len(moved))
        for pid in {h.person_id for h in old.values() if h}:
            self._point_screens(pid)
        return moved

    def set_pair_mode(self, by: str, position: str, mode: Optional[str]) -> None:
        """Allow a second person at a desk: ``shadow`` (read-only) or
        ``second`` (a second commander, for training). None removes it."""
        self._need_instructor(by)
        self._need_position(position)
        if mode is not None and mode not in PAIR_MODES:
            raise SeatError("pair", "Pair must be shadow or second", 400)
        if mode is None:
            self.pair_mode.pop(position, None)
            for h in self.pairs.pop(position, []):
                self._event("unpair", position, h.person_id, by)
        else:
            self.pair_mode[position] = mode
            for h in self.pairs.get(position, []):
                h.role = mode
        self._event("pair_mode", position, "", by, mode=mode or "off")

    def pair(self, by: str, position: str, person_id: str) -> None:
        self._need_instructor(by)
        self._need_position(position)
        self._need_person(person_id)
        mode = self.pair_mode.get(position)
        if mode is None:
            raise SeatError("pair-off", "Tick pair on {position} first", 409, position=position)
        if self.holder_of(position) == person_id:
            return
        lst = self.pairs.setdefault(position, [])
        if any(h.person_id == person_id for h in lst):
            return
        lst.append(Holding(position, person_id, self._now(), float(self._sim()), "instructor", mode))
        self._event("pair", position, person_id, by, role=mode)
        self._point_screens(person_id)

    def _drop_pair_entry(self, position: str, person_id: str) -> None:
        lst = self.pairs.get(position)
        if lst:
            self.pairs[position] = [h for h in lst if h.person_id != person_id]

    def _point_screens(self, person_id: str) -> None:
        """Keep each screen's view and active position inside what its
        owner may now see and command."""
        cmd = self.command_positions(person_id)
        see = self.view_positions(person_id)
        for c in self.conns.values():
            if c.person_id != person_id:
                continue
            if c.active_position not in cmd:
                c.active_position = cmd[0] if cmd else ""
            v = c.view
            if v.get("kind") == "position":
                pos = [p for p in v.get("positions", []) if p in see] or (cmd[:1] or see[:1])
                c.view = {"kind": "position", "positions": pos}
            elif v.get("kind") == "tile":
                c.view = {"kind": "tile", "positions": [p for p in v.get("positions", []) if p in see] or see}
        self.version += 1

    # ── presence edges ──────────────────────────────────────────────────
    def tick(self) -> list[dict]:
        """Expire requests, forget long-silent screens and emit idle/active
        edge events per desk. Call every few seconds."""
        self.expire_requests()
        now = self._now()
        for cid, c in list(self.conns.items()):
            if now - c.last_heartbeat > CONN_FORGET_S:
                del self.conns[cid]
                self.version += 1
        out = []
        for pos in self.positions:
            st = self.seat_state(pos)
            prev = self._presence.get(pos)
            if prev is not None and st != prev and prev != "vacant" and st != "vacant":
                h = self.holders.get(pos)
                out.append(self._event({"staffed": "active", "idle": "idle",
                                        "reclaimable": "away"}[st], pos,
                                       h.person_id if h else ""))
            self._presence[pos] = st
        return out

    # ── views of the state ──────────────────────────────────────────────
    def public_person(self, person_id: str) -> dict:
        p = self.persons.get(person_id)
        if p is None:
            return {"id": person_id, "name": "?", "verified": False}
        return {"id": p.person_id, "name": p.display_name, "verified": p.verified,
                "instructor": p.instructor, "presence": self.presence(p.person_id)}

    def board(self, *, for_instructor: bool) -> dict:
        """The board. Participants see who holds each desk; instructors also
        see every participant's screens and the bench."""
        self.expire_requests()
        cols = []
        for pos in self.positions:
            h = self.holders.get(pos)
            col = {"position": pos, "state": self.seat_state(pos),
                   "locked": self.is_locked(pos),
                   "holder": self.public_person(h.person_id) if h else None,
                   "since_sim": h.since_sim if h else None,
                   "assigned_by": h.assigned_by if h else None,
                   "pair_mode": self.pair_mode.get(pos),
                   "pairs": [dict(self.public_person(x.person_id), role=x.role)
                             for x in self.pairs.get(pos, [])],
                   "request": None}
            r = self.requests.get(pos)
            if r is not None:
                col["request"] = {"from": self.public_person(r.from_person),
                                  "expires_in_s": max(0.0, round(r.expires - self._now(), 1))}
            cols.append(col)
        out = {"positions": cols, "locked": self.locked_board, "version": self.version,
               "idle_s": self.idle_s, "reclaim_s": self.reclaim_s}
        if for_instructor:
            people = []
            for pid, p in self.persons.items():
                screens = [conn_public(c) for c in self.conns.values() if c.person_id == pid]
                held = self.positions_of(pid)
                paired = [pos for pos in self.positions
                          if any(h.person_id == pid for h in self.pairs.get(pos, []))]
                if not screens and not held and not paired:
                    continue
                people.append(dict(self.public_person(pid), screens=screens,
                                   positions=held, paired=paired,
                                   bench=not held and not paired))
            people.sort(key=lambda x: (not x["instructor"], x["name"].lower()))
            out["people"] = people
            out["events"] = list(self.events)[-60:]
        return out


def conn_public(c: Connection) -> dict:
    return {"conn_id": c.conn_id, "label": c.label, "view": dict(c.view),
            "active_position": c.active_position}


def clean_label(raw) -> str:
    s = " ".join(str(raw or "").split())
    s = "".join(ch for ch in s if ch.isprintable())
    return s[:32]
