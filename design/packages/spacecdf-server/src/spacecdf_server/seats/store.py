"""Seat state: per-study team documents, presence, the audit trail and pending changes.

Write-through: the in-memory dicts are the read path; every change is mirrored to the DB
(``study_teams``, ``seat_events``, ``pending_changes``). DB failures are logged and the
server keeps working in memory (same rule as the other repositories).
Presence (heartbeats) is memory only: after a restart every holder shows Idle until their
browser's next heartbeat (≤ 30 s).
"""
from __future__ import annotations

import asyncio
import copy
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from ..db.engine import get_session_factory
from ..db.models import PendingChangeRow, SeatEventRow, StudyTeamRow
from . import config as cfg
from .identity import Person, instructor_emails

logger = logging.getLogger(__name__)

CLASS = "__class__"

_team: dict[str, dict[str, Any]] = {}
_loaded: set[str] = set()
_locks: dict[str, asyncio.Lock] = {}
# study_id → person_id → {name, verified, last, active_seat, last_action, last_action_at}
_presence: dict[str, dict[str, dict[str, Any]]] = {}
# in-memory mirror of events (used when the DB is down, and for fast "changed" markers)
_events_mem: list[dict[str, Any]] = []
_pending_mem: dict[str, dict[str, Any]] = {}
_START = time.time()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse(ts: str | None) -> float:
    if not ts:
        return 0.0
    try:
        return datetime.fromisoformat(ts).timestamp()
    except ValueError:
        return 0.0


def default_state() -> dict[str, Any]:
    return {"enabled": False, "preset": None, "optional": [], "groups": [], "holdings": {},
            "locked": {}, "requests": {}, "hands": {}, "frozen": None, "timer": None,
            "messages": [], "signoffs": {}, "subscriptions": {}, "wanted": {}, "active": {}}


def lock_for(study_id: str) -> asyncio.Lock:
    lk = _locks.get(study_id)
    if lk is None:
        lk = _locks[study_id] = asyncio.Lock()
    return lk


def reset_memory() -> None:
    """Tests: forget everything held in memory (the DB fixture is per test)."""
    _team.clear()
    _loaded.clear()
    _locks.clear()
    _presence.clear()
    _events_mem.clear()
    _pending_mem.clear()


async def get_team(study_id: str) -> dict[str, Any]:
    if study_id in _team:
        return _team[study_id]
    state = default_state()
    if study_id not in _loaded:
        try:
            async with get_session_factory()() as s:
                row = await s.get(StudyTeamRow, study_id)
                if row is not None and isinstance(row.state_json, dict):
                    state.update(copy.deepcopy(row.state_json))
        except Exception:  # noqa: BLE001
            logger.debug("team state not loaded for %s", study_id, exc_info=True)
        _loaded.add(study_id)
    _team[study_id] = state
    return state


def peek_team(study_id: str) -> dict[str, Any] | None:
    """The cached team document, without touching the DB (middleware fast path)."""
    return _team.get(study_id)


async def save_team(study_id: str, state: dict[str, Any]) -> None:
    _team[study_id] = state
    try:
        async with get_session_factory()() as s:
            row = await s.get(StudyTeamRow, study_id)
            doc = copy.deepcopy(state)
            if row is None:
                s.add(StudyTeamRow(study_id=study_id, state_json=doc))
            else:
                row.state_json = doc
            await s.commit()
    except Exception:  # noqa: BLE001
        logger.warning("team state not persisted for %s", study_id, exc_info=True)


async def drop_team(study_id: str) -> None:
    _team.pop(study_id, None)
    _presence.pop(study_id, None)
    try:
        async with get_session_factory()() as s:
            row = await s.get(StudyTeamRow, study_id)
            if row is not None:
                await s.delete(row)
                await s.commit()
    except Exception:  # noqa: BLE001
        logger.debug("team row not deleted for %s", study_id, exc_info=True)


async def known_team_ids() -> list[str]:
    ids = set(k for k in _team if k != CLASS)
    try:
        async with get_session_factory()() as s:
            for (sid,) in (await s.execute(select(StudyTeamRow.study_id))).all():
                if sid != CLASS:
                    ids.add(sid)
    except Exception:  # noqa: BLE001
        pass
    return sorted(ids)


# ─── instructor ──────────────────────────────────────────────────────────────

async def instructor_status(p: Person) -> str | None:
    """``listed`` | ``claimed`` (laptop instructor) | None."""
    emails = instructor_emails()
    if emails:
        return "listed" if (p.verified and p.email in emails) else None
    cls = await get_team(CLASS)
    claimed = (cls.get("instructor") or {}).get("person_id")
    return "claimed" if claimed and claimed == p.id else None


async def is_instructor(p: Person) -> bool:
    return (await instructor_status(p)) is not None


async def laptop_instructor() -> dict[str, Any] | None:
    return (await get_team(CLASS)).get("instructor")


# ─── presence ────────────────────────────────────────────────────────────────

def touch(study_id: str, p: Person, active_seat: str | None = None, action: str | None = None) -> None:
    if p.anonymous:
        return
    d = _presence.setdefault(study_id, {}).setdefault(p.id, {"name": p.name, "verified": p.verified})
    d["name"] = p.name or d.get("name", "")
    d["verified"] = p.verified
    d["last"] = time.time()
    if active_seat is not None:
        d["active_seat"] = active_seat
    if action:
        d["last_action"] = action
        d["last_action_at"] = now_iso()


def presence(study_id: str) -> dict[str, dict[str, Any]]:
    return _presence.get(study_id, {})


def last_seen(study_id: str, person_id: str, fallback_iso: str | None = None) -> float:
    d = _presence.get(study_id, {}).get(person_id)
    if d and d.get("last"):
        return float(d["last"])
    # Never seen in this process: count from the claim or from the server start.
    return max(_parse(fallback_iso), _START)


def holder_status(study_id: str, holding: dict[str, Any], now: float | None = None) -> str:
    """``active`` | ``idle`` | ``reclaimable`` for one holding."""
    t = cfg.timing()
    now = now or time.time()
    age = now - last_seen(study_id, holding["person_id"], holding.get("since"))
    if age >= t["idle_after_s"] + t["reclaimable_after_s"]:
        return "reclaimable"
    if age >= t["idle_after_s"]:
        return "idle"
    return "active"


# ─── events ──────────────────────────────────────────────────────────────────

async def log_event(study_id: str, seat_id: str, p: Person | None, action: str, target: str = "",
                    detail: dict[str, Any] | None = None) -> dict[str, Any]:
    ev = {"ts": now_iso(), "study_id": study_id, "seat_id": seat_id or "",
          "person_id": p.id if p else "", "person_name": p.name if p else "",
          "verified": bool(p and p.verified), "action": action, "target": target or "",
          "detail": detail or {}}
    _events_mem.append(ev)
    if len(_events_mem) > 20000:
        del _events_mem[:5000]
    try:
        async with get_session_factory()() as s:
            s.add(SeatEventRow(ts=datetime.fromisoformat(ev["ts"]).replace(tzinfo=None), study_id=study_id,
                               seat_id=ev["seat_id"], person_id=ev["person_id"], person_name=ev["person_name"],
                               verified=ev["verified"], action=action, target=ev["target"], detail_json=ev["detail"]))
            await s.commit()
    except Exception:  # noqa: BLE001
        logger.debug("seat event not persisted", exc_info=True)
    if p and study_id != CLASS:
        touch(study_id, p, action=action)
    return ev


def _ev_from_row(r: SeatEventRow) -> dict[str, Any]:
    ts = r.ts.replace(tzinfo=timezone.utc).isoformat() if r.ts and r.ts.tzinfo is None else (r.ts.isoformat() if r.ts else "")
    return {"ts": ts, "study_id": r.study_id, "seat_id": r.seat_id, "person_id": r.person_id,
            "person_name": r.person_name, "verified": bool(r.verified), "action": r.action,
            "target": r.target, "detail": r.detail_json or {}}


async def list_events(study_id: str | None = None, since: str | None = None, limit: int = 50000) -> list[dict[str, Any]]:
    try:
        async with get_session_factory()() as s:
            q = select(SeatEventRow).order_by(SeatEventRow.id)
            if study_id:
                q = q.where(SeatEventRow.study_id == study_id)
            rows = (await s.execute(q.limit(limit))).scalars().all()
            out = [_ev_from_row(r) for r in rows]
    except Exception:  # noqa: BLE001
        out = [e for e in _events_mem if not study_id or e["study_id"] == study_id]
    if since:
        cut = _parse(since)
        out = [e for e in out if _parse(e["ts"]) > cut]
    return out


def last_edit_ts(study_id: str, element_id: str, field: str) -> str | None:
    """When the value of (element, field) last changed through SpaceCDF (memory trail)."""
    for ev in reversed(_events_mem):
        if ev["study_id"] != study_id or ev["action"] not in ("edit", "accept"):
            continue
        d = ev.get("detail") or {}
        if d.get("element_id") == element_id and field in (d.get("fields") or []):
            return ev["ts"]
    return None


# ─── pending changes ─────────────────────────────────────────────────────────

_PC_COLS = ("id", "study_id", "owner_seat", "kind", "element_id", "element_name", "param_keys",
            "option_id", "by_person", "by_name", "by_seat", "status", "reviewed_by", "reviewed_name",
            "reviewed_seat", "comment")


def _pc_from_row(r: PendingChangeRow) -> dict[str, Any]:
    d = {k: getattr(r, k) for k in _PC_COLS}
    d["old"] = r.old_json or {}
    d["new"] = r.new_json or {}
    d["created_at"] = r.created_at.replace(tzinfo=timezone.utc).isoformat() if r.created_at else None
    d["reviewed_at"] = r.reviewed_at.replace(tzinfo=timezone.utc).isoformat() if r.reviewed_at else None
    return d


async def add_pending(pc: dict[str, Any]) -> dict[str, Any]:
    pc = {"id": uuid.uuid4().hex[:16], "status": "pending", "reviewed_by": "", "reviewed_name": "",
          "reviewed_seat": "", "comment": "", "created_at": now_iso(), "reviewed_at": None, **pc}
    _pending_mem[pc["id"]] = pc
    try:
        async with get_session_factory()() as s:
            s.add(PendingChangeRow(
                id=pc["id"], study_id=pc["study_id"], owner_seat=pc["owner_seat"], kind=pc["kind"],
                element_id=pc.get("element_id") or "", element_name=pc.get("element_name") or "",
                param_keys=list(pc.get("param_keys") or []), old_json=pc.get("old") or {},
                new_json=pc.get("new") or {}, option_id=pc.get("option_id"),
                by_person=pc["by_person"], by_name=pc["by_name"], by_seat=pc["by_seat"]))
            await s.commit()
    except Exception:  # noqa: BLE001
        logger.debug("pending change not persisted", exc_info=True)
    return pc


async def list_pending(study_id: str, status: str | None = "pending") -> list[dict[str, Any]]:
    try:
        async with get_session_factory()() as s:
            q = select(PendingChangeRow).where(PendingChangeRow.study_id == study_id)
            if status:
                q = q.where(PendingChangeRow.status == status)
            rows = (await s.execute(q.order_by(PendingChangeRow.created_at))).scalars().all()
            out = [_pc_from_row(r) for r in rows]
            for pc in out:
                _pending_mem.setdefault(pc["id"], pc)
            return out
    except Exception:  # noqa: BLE001
        return [p for p in _pending_mem.values()
                if p["study_id"] == study_id and (not status or p["status"] == status)]


async def get_pending(pc_id: str) -> dict[str, Any] | None:
    try:
        async with get_session_factory()() as s:
            r = await s.get(PendingChangeRow, pc_id)
            if r is not None:
                return _pc_from_row(r)
    except Exception:  # noqa: BLE001
        pass
    return _pending_mem.get(pc_id)


async def close_pending(pc_id: str, status: str, p: Person, seat_id: str, comment: str) -> dict[str, Any] | None:
    at = datetime.now(timezone.utc)
    pc = _pending_mem.get(pc_id) or await get_pending(pc_id)
    if pc is None:
        return None
    pc.update(status=status, reviewed_by=p.id, reviewed_name=p.name, reviewed_seat=seat_id,
              comment=comment, reviewed_at=at.isoformat())
    _pending_mem[pc_id] = pc
    try:
        async with get_session_factory()() as s:
            r = await s.get(PendingChangeRow, pc_id)
            if r is not None:
                r.status, r.reviewed_by, r.reviewed_name = status, p.id, p.name
                r.reviewed_seat, r.comment, r.reviewed_at = seat_id, comment, at.replace(tzinfo=None)
                await s.commit()
    except Exception:  # noqa: BLE001
        logger.debug("pending change review not persisted", exc_info=True)
    return pc
