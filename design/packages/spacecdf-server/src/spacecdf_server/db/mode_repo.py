"""Async repository for the Nov 2026 mode model: mode members (extended ``mode_elements``),
mode transitions, rule proposals and heaters.

The mode × element matrix lives in ``mode_elements`` (the analysis context already reads it);
writes here also drop any matching entry from the legacy in-memory list in
``routers/elements._mode_elements`` so the database row is what the analyses see.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select

from .engine import get_session_factory
from .models import ModeElementRow
from .models_modes import HeaterRow, ModeTransitionRow, RuleProposalRow

logger = logging.getLogger(__name__)

MEMBER_FIELDS = ("is_active", "power_w_in_mode", "duty_cycle_percent", "notes", "power_state", "data_rate_bps",
                 "dissipation_w", "origin", "status", "source_ref", "inputs_hash")
PROPOSAL_STATUSES = ("suggested", "accepted", "edited", "rejected", "stale")


def _member_dict(r: ModeElementRow) -> dict[str, Any]:
    return {"mode_id": r.mode_id, "element_id": r.element_id, "is_active": bool(r.is_active),
            "power_w_in_mode": r.power_w_in_mode, "duty_cycle_percent": r.duty_cycle_percent, "notes": r.notes or "",
            "power_state": r.power_state, "data_rate_bps": r.data_rate_bps, "dissipation_w": r.dissipation_w,
            "origin": r.origin or "user", "status": r.status or "accepted", "source_ref": r.source_ref or "",
            "inputs_hash": r.inputs_hash or ""}


def _forget_memory(mode_id: str, element_id: str | None = None) -> None:
    try:
        from ..routers import elements as el_router
        el_router._mode_elements[:] = [m for m in el_router._mode_elements
                                       if not (m.get("mode_id") == mode_id and (element_id is None or m.get("element_id") == element_id))]
    except Exception:  # pragma: no cover
        pass


# ───────────────────────────────────────────────────────────── members

async def list_members(mode_ids: list[str]) -> list[dict]:
    if not mode_ids:
        return []
    async with get_session_factory()() as s:
        res = await s.execute(select(ModeElementRow).where(ModeElementRow.mode_id.in_(mode_ids)))
        rows = [_member_dict(r) for r in res.scalars()]
    # legacy in-memory entries (POST /elements/{mode}/activate) not yet in the table
    try:
        from ..routers import elements as el_router
        seen = {(r["mode_id"], r["element_id"]) for r in rows}
        for m in el_router._mode_elements:
            if m.get("mode_id") in mode_ids and (m["mode_id"], m["element_id"]) not in seen:
                rows.append({**{k: None for k in MEMBER_FIELDS}, "origin": "user", "status": "accepted",
                             "duty_cycle_percent": 100.0, **m})
    except Exception:  # pragma: no cover
        pass
    return rows


async def upsert_member(mode_id: str, element_id: str, fields: dict[str, Any]) -> dict:
    async with get_session_factory()() as s:
        res = await s.execute(select(ModeElementRow).where(ModeElementRow.mode_id == mode_id,
                                                           ModeElementRow.element_id == element_id))
        row = res.scalars().first()
        if row is None:
            row = ModeElementRow(mode_id=mode_id, element_id=element_id, is_active=True, duty_cycle_percent=100.0,
                                 notes="", origin="user", status="accepted", source_ref="", inputs_hash="")
            s.add(row)
        for k, v in fields.items():
            if k in MEMBER_FIELDS:
                setattr(row, k, v)
        await s.commit()
        out = _member_dict(row)
    _forget_memory(mode_id, element_id)
    return out


async def delete_members(mode_id: str) -> None:
    async with get_session_factory()() as s:
        await s.execute(delete(ModeElementRow).where(ModeElementRow.mode_id == mode_id))
        await s.commit()
    _forget_memory(mode_id)


# ───────────────────────────────────────────────────────────── transitions

def _transition_dict(r: ModeTransitionRow) -> dict[str, Any]:
    return {"id": r.id, "study_id": r.study_id, "from_mode_id": r.from_mode_id, "to_mode_id": r.to_mode_id,
            "trigger": r.trigger, "guard": r.guard_json or {}, "monitor_ref": r.monitor_ref or "",
            "priority": r.priority or 0, "description": r.description or "", "origin": r.origin or "user"}


async def list_transitions(study_id: str) -> list[dict]:
    async with get_session_factory()() as s:
        res = await s.execute(select(ModeTransitionRow).where(ModeTransitionRow.study_id == study_id)
                              .order_by(ModeTransitionRow.created_at))
        return [_transition_dict(r) for r in res.scalars()]


async def create_transition(study_id: str, t: dict[str, Any]) -> dict:
    row = ModeTransitionRow(id=uuid4().hex, study_id=study_id, from_mode_id=t["from_mode_id"], to_mode_id=t["to_mode_id"],
                            trigger=t.get("trigger") or "ground_tc", guard_json=t.get("guard") or {},
                            monitor_ref=t.get("monitor_ref") or "", priority=int(t.get("priority") or 0),
                            description=t.get("description") or "", origin=t.get("origin") or "user")
    async with get_session_factory()() as s:
        s.add(row)
        await s.commit()
        return _transition_dict(row)


async def update_transition(tid: str, fields: dict[str, Any]) -> dict | None:
    async with get_session_factory()() as s:
        row = await s.get(ModeTransitionRow, tid)
        if row is None:
            return None
        for k, v in fields.items():
            if k == "guard":
                row.guard_json = v or {}
            elif k in ("from_mode_id", "to_mode_id", "trigger", "monitor_ref", "description"):
                setattr(row, k, v or "")
            elif k == "priority":
                row.priority = int(v or 0)
        await s.commit()
        return _transition_dict(row)


async def delete_transition(tid: str) -> bool:
    async with get_session_factory()() as s:
        row = await s.get(ModeTransitionRow, tid)
        if row is None:
            return False
        await s.delete(row)
        await s.commit()
        return True


async def delete_transitions_of_mode(study_id: str, mode_id: str) -> None:
    async with get_session_factory()() as s:
        await s.execute(delete(ModeTransitionRow).where(
            ModeTransitionRow.study_id == study_id,
            (ModeTransitionRow.from_mode_id == mode_id) | (ModeTransitionRow.to_mode_id == mode_id)))
        await s.commit()


# ───────────────────────────────────────────────────────────── proposals

def _proposal_dict(r: RuleProposalRow) -> dict[str, Any]:
    return {"id": r.id, "study_id": r.study_id, "rule_id": r.rule_id, "kind": r.kind, "target_key": r.target_key,
            "element_id": r.element_id or "", "payload": r.payload_json or {}, "standard_ref": r.standard_ref or "",
            "c2o_default": bool(r.c2o_default), "rationale": r.rationale_json or {}, "inputs_hash": r.inputs_hash or "",
            "status": r.status, "owner_seat": r.owner_seat or "", "result_ref": r.result_ref or "",
            "updated_at": r.updated_at.isoformat() if r.updated_at else None}


async def list_proposals(study_id: str, kind: str | None = None) -> list[dict]:
    async with get_session_factory()() as s:
        q = select(RuleProposalRow).where(RuleProposalRow.study_id == study_id)
        if kind:
            q = q.where(RuleProposalRow.kind == kind)
        res = await s.execute(q.order_by(RuleProposalRow.rule_id, RuleProposalRow.target_key))
        return [_proposal_dict(r) for r in res.scalars()]


async def upsert_proposals(study_id: str, proposals: list[dict], *, rule_ids: set[str] | None = None) -> dict[str, int]:
    """Store rule output with the proposal life cycle (spacecdf_design_rules.md §1.1).

    new → suggested; suggested + changed inputs → refreshed silently; accepted/edited + changed
    inputs → stale; rejected → kept, never re-proposed. Suggested rows of ``rule_ids`` that the
    rules no longer produce are deleted (their cause is gone).
    """
    counts = {"new": 0, "refreshed": 0, "stale": 0, "kept": 0, "withdrawn": 0}
    keys = {(p["rule_id"], p["target_key"]) for p in proposals}
    async with get_session_factory()() as s:
        res = await s.execute(select(RuleProposalRow).where(RuleProposalRow.study_id == study_id))
        existing = {(r.rule_id, r.target_key): r for r in res.scalars()}
        for p in proposals:
            r = existing.get((p["rule_id"], p["target_key"]))
            if r is None:
                s.add(RuleProposalRow(
                    id=uuid4().hex, study_id=study_id, rule_id=p["rule_id"], kind=p["kind"], target_key=p["target_key"],
                    element_id=p.get("element_id") or "", payload_json=p.get("payload") or {},
                    standard_ref=p.get("standard_ref") or "", c2o_default=bool(p.get("c2o_default", True)),
                    rationale_json=p.get("rationale") or {}, inputs_hash=p.get("inputs_hash") or "",
                    status="suggested", owner_seat=p.get("owner_seat") or ""))
                counts["new"] += 1
            elif r.inputs_hash == (p.get("inputs_hash") or "") or r.status == "rejected":
                counts["kept"] += 1
            elif r.status == "suggested":
                r.payload_json, r.rationale_json, r.inputs_hash = p.get("payload") or {}, p.get("rationale") or {}, p.get("inputs_hash") or ""
                r.standard_ref = p.get("standard_ref") or r.standard_ref
                counts["refreshed"] += 1
            else:
                if r.status != "stale":
                    r.status = "stale"
                    counts["stale"] += 1
                r.rationale_json = {**(r.rationale_json or {}), "stale_since": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if rule_ids:
            for (rid, tk), r in existing.items():
                if rid in rule_ids and (rid, tk) not in keys and r.status == "suggested":
                    await s.delete(r)
                    counts["withdrawn"] += 1
        await s.commit()
    return counts


async def set_proposal_status(pid: str, status: str, *, result_ref: str | None = None,
                              payload: dict | None = None) -> dict | None:
    async with get_session_factory()() as s:
        r = await s.get(RuleProposalRow, pid)
        if r is None:
            return None
        r.status = status
        if result_ref is not None:
            r.result_ref = result_ref
        if payload is not None:
            r.payload_json = payload
        await s.commit()
        return _proposal_dict(r)


async def get_proposal(pid: str) -> dict | None:
    async with get_session_factory()() as s:
        r = await s.get(RuleProposalRow, pid)
        return _proposal_dict(r) if r else None


# ───────────────────────────────────────────────────────────── heaters

def _heater_dict(r: HeaterRow) -> dict[str, Any]:
    return {"id": r.id, "study_id": r.study_id, "element_id": r.element_id, "heater_element_id": r.heater_element_id,
            "name": r.name, "power_w": r.power_w, "on_c": r.on_c, "off_c": r.off_c, "control": r.control,
            "line": r.line_json or {}, "proposal_id": r.proposal_id}


async def create_heater(study_id: str, h: dict[str, Any]) -> dict:
    row = HeaterRow(id=uuid4().hex, study_id=study_id, element_id=h["element_id"],
                    heater_element_id=h.get("heater_element_id") or "", name=h.get("name") or "",
                    power_w=float(h.get("power_w") or 0), on_c=float(h.get("on_c") or 0), off_c=float(h.get("off_c") or 5),
                    control=h.get("control") or "auto", line_json=h.get("line") or {}, proposal_id=h.get("proposal_id") or "")
    async with get_session_factory()() as s:
        s.add(row)
        await s.commit()
        return _heater_dict(row)


async def list_heaters(study_id: str) -> list[dict]:
    async with get_session_factory()() as s:
        res = await s.execute(select(HeaterRow).where(HeaterRow.study_id == study_id))
        return [_heater_dict(r) for r in res.scalars()]
