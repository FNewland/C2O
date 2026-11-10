"""SpaceCDF — the change-control flow of a change proposal (wave 3, 3.D7; PI addendum: ECP-01
and ECP-02 decided on camera). Owner D.

The proposals themselves (ECP-01, ECP-02, CR-V2 …) are agent L's ``change_proposals``. This
module runs the flow around one proposal, kept in ``change_approvals`` (one row per affected
seat, one row for the board)::

    not_started ──start──▶ in_review ──every affected seat agrees──▶ agreed ──decide approve──▶ approved
                              │   ▲                                      │                          (baseline update)
                              │   └──── a seat changes its answer ───────┘
                              └── a seat objects ──▶ objected ──decide reject──▶ rejected

* **start**: the impact preview (agent L's ``POST /impact/preview``; the study's key numbers when
  the preview is not available) and the affected seats: the owners of the affected requirements'
  elements, the seats the preview names, the seat of the source trade, and Systems.
* **agree**: each affected seat agrees or objects, with a note (a seat study checks that the
  person holds that seat, or is the Team leader or the instructor).
* **decide**: the board (Team leader or instructor) approves, only once every affected seat
  agreed, or rejects. Approval sets the proposal ``accepted``, applies the requirement edits it
  carries, and saves a new configuration baseline revision (``gate_baselines``, gate
  ``chg:<code>``) of the kind of the last gate passed (mission, functional, allocated, product);
  the board row keeps its id as ``baseline_ref``.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

SEAT_DECISIONS = ("agree", "object")
BOARD_DECISIONS = ("approve", "reject")
#: requirement fields a change may set on approval
APPLY_FIELDS = ("text", "threshold_value", "threshold_op", "threshold_unit", "acceptance", "rationale", "status",
                "verification_method", "open_item_note")
_CODE = re.compile(r"\b[A-Z]{2,5}(?:-[A-Z0-9]{1,6}){1,3}\b")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(v: Any) -> str | None:
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


class ChangeControlError(ValueError):
    def __init__(self, status: int, code: str, message: str, **extra: Any):
        super().__init__(message)
        self.status, self.code, self.extra = status, code, extra


# ─── records ─────────────────────────────────────────────────────────────

async def _proposal(study_id: str, change_id: str):
    """The change proposal by id or code (ECP-01)."""
    from sqlalchemy import select

    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeProposalRow
    async with get_session_factory()() as s:
        row = await s.get(ChangeProposalRow, change_id)
        if row is None or row.study_id != study_id:
            row = (await s.execute(select(ChangeProposalRow).where(ChangeProposalRow.study_id == study_id,
                                                                   ChangeProposalRow.code == change_id))).scalars().first()
        if row is None:
            raise ChangeControlError(404, "not_found", f"Change {change_id} not found")
        return _proposal_dict(row)


def _proposal_dict(r: Any) -> dict[str, Any]:
    return {"id": r.id, "code": r.code, "kind": r.kind, "title": r.title, "change_class": r.change_class,
            "description": r.description, "impact": dict(r.impact_json or {}) if isinstance(r.impact_json, dict)
            else r.impact_json, "affected_codes": list(r.affected_codes_json or []),
            "affected_requirement_ids": list(r.affected_requirement_ids_json or []), "source_trade": r.source_trade,
            "status": r.status, "decision_gate": r.decision_gate, "decided_by": r.decided_by,
            "data": dict(r.data_json or {})}


async def _approvals(study_id: str, change_id: str) -> list[Any]:
    from sqlalchemy import select

    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeApprovalRow
    async with get_session_factory()() as s:
        return list((await s.execute(select(ChangeApprovalRow).where(
            ChangeApprovalRow.study_id == study_id, ChangeApprovalRow.change_id == change_id)
            .order_by(ChangeApprovalRow.order))).scalars().all())


def _approval_dict(r: Any) -> dict[str, Any]:
    return {"id": r.id, "kind": r.kind, "seat": r.seat, "decision": r.decision, "by": r.by, "at": _iso(r.at),
            "note": r.note, "baseline_ref": r.baseline_ref, "data": dict(r.data_json or {})}


def flow_state(proposal: dict[str, Any], rows: list[Any]) -> str:
    seats = [r for r in rows if r.kind == "seat"]
    board = next((r for r in rows if r.kind == "board"), None)
    if board is not None and board.decision == "approve":
        return "approved"
    if board is not None and board.decision == "reject":
        return "rejected"
    if not seats and board is None:
        st = str(proposal.get("status") or "").lower()
        return {"accepted": "approved", "approved": "approved", "rejected": "rejected"}.get(st, "not_started")
    if any(r.decision == "object" for r in seats):
        return "objected"
    if seats and all(r.decision == "agree" for r in seats):
        return "agreed"
    return "in_review"


async def view(study_id: str, change_id: str) -> dict[str, Any]:
    """The flow of one change: the proposal, the impact it saw, each affected seat's answer, the
    board decision and the baseline it produced."""
    p = await _proposal(study_id, change_id)
    rows = await _approvals(study_id, p["id"])
    board = next((r for r in rows if r.kind == "board"), None)
    seats = [_approval_dict(r) for r in rows if r.kind == "seat"]
    impact = next((r.impact_json for r in rows if r.kind == "board" and r.impact_json), None)
    state = flow_state(p, rows)
    return {"study_id": study_id, "change": p, "state": state, "impact": impact or {},
            "seats": seats, "pending_seats": [s["seat"] for s in seats if s["decision"] == "pending"],
            "objecting_seats": [s["seat"] for s in seats if s["decision"] == "object"],
            "board": _approval_dict(board) if board is not None else None,
            "baseline_ref": board.baseline_ref if board is not None else "",
            "can_decide": state in ("agreed", "objected", "in_review")}


async def list_all(study_id: str) -> list[dict[str, Any]]:
    """The flow of every change proposal of the study (export section)."""
    from .gate_evidence import changes
    out = []
    for c in await changes(study_id):
        try:
            out.append(await view(study_id, c["id"]))
        except ChangeControlError:
            continue
    return out


# ─── affected seats and the impact preview ───────────────────────────────

async def affected_seats(study_id: str, p: dict[str, Any], preview: dict[str, Any] | None) -> list[str]:
    """Owners of the affected requirements' elements, the seats the preview names, the source
    trade's seat and Systems (always), in seat order."""
    from ..seats import config as seats_cfg
    seats: list[str] = []
    codes = set(p.get("affected_codes") or [])
    for c in p.get("affected_codes") or []:
        codes.update(_CODE.findall(str(c)))
    try:
        from ..routers.requirements import _ensure_loaded, _requirements
        await _ensure_loaded()
        els = {e.get("id"): e for e in (await _study_elements(study_id))}
        for r in _requirements.values():
            if r.get("study_id") != study_id or r.get("id") not in set(p.get("affected_requirement_ids") or []) \
                    and r.get("code") not in codes:
                continue
            el = els.get(r.get("element_id"))
            seat = seats_cfg.element_owner_seat(el, els) if el else None
            if seat:
                seats.append(seat)
    except Exception:  # noqa: BLE001 — requirements unavailable: the preview and Systems decide
        logger.debug("affected seats: requirements unavailable for %s", study_id, exc_info=True)
    for s in (preview or {}).get("seats") or (preview or {}).get("affected_seats") or []:
        sid = s.get("seat") if isinstance(s, dict) else s
        if sid:
            seats.append(str(sid))
    trade_seat = await _trade_seat(study_id, p.get("source_trade") or "")
    if trade_seat:
        seats.append(trade_seat)
    seats.append("systems_engineer")
    order = seats_cfg.seat_ids()
    uniq = [s for s in dict.fromkeys(seats) if s in order and seats_cfg.kind(s) not in ("observer", "instructor")]
    return sorted(uniq, key=lambda s: order.index(s))


async def _study_elements(study_id: str) -> list[dict[str, Any]]:
    from ..routers.elements import _elements
    return [e for e in _elements.values() if e.get("study_id") == study_id]


async def _trade_seat(study_id: str, source: str) -> str:
    m = re.search(r"T-[A-Z]?\d{2}", source or "")
    if not m:
        return ""
    from ..routers.studies import get_study_store
    from .trades import normalise_records
    study = get_study_store().get(study_id)
    rec = normalise_records(getattr(study, "trade_records", None)).get(m.group(0)) if study else None
    return str(((rec or {}).get("state") or {}).get("seat") or "")


async def impact_preview(study_id: str, p: dict[str, Any]) -> dict[str, Any]:
    """Agent L's impact preview of the change (``POST /impact/preview``, dry run), else the
    study's key numbers as they stand (``source: key_numbers``) with the impact the proposal states."""
    body = {"kind": "change_proposal", "change_id": p["id"], "code": p["code"], "impact": p.get("impact"),
            "affected_codes": p.get("affected_codes"), "change": p.get("data", {}).get("proposed") or {}}
    try:
        from ..routers.impact import impact_preview as route
        res = await route(study_id, body)
        if isinstance(res, dict) and res.get("status") != "not_implemented":
            return {"source": "impact_preview", **res}
    except Exception as exc:  # noqa: BLE001 — L's preview not landed (501) or failed
        logger.debug("impact preview unavailable for %s: %s", study_id, exc)
    try:
        from .key_numbers import key_numbers
        kn = await key_numbers(study_id)
    except Exception:  # noqa: BLE001
        kn = {}
    return {"source": "key_numbers", "stated_impact": p.get("impact"),
            "key_numbers": {k: v for k, v in kn.items() if (v or {}).get("value") is not None}, "deltas": {}}


# ─── the flow ────────────────────────────────────────────────────────────

async def start(study_id: str, change_id: str, *, seats: list[str] | None = None, by: str = "") -> dict[str, Any]:
    """Open the review of a change: the impact preview and one pending row per affected seat
    (``seats`` adds to the computed ones). Restarting keeps the answers of seats still affected."""
    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeApprovalRow
    p = await _proposal(study_id, change_id)
    rows = await _approvals(study_id, p["id"])
    if flow_state(p, rows) in ("approved", "rejected"):
        raise ChangeControlError(409, "decided", f"{p['code'] or p['id']} is already decided")
    prev = await impact_preview(study_id, p)
    names = await affected_seats(study_id, p, prev)
    for s in seats or []:
        if s not in names:
            names.append(s)
    now = _now()
    async with get_session_factory()() as s:
        have = {r.seat: r for r in rows if r.kind == "seat"}
        for r in rows:
            if r.kind == "seat" and r.seat not in names:
                await s.delete(await s.get(ChangeApprovalRow, r.id))
        for i, seat in enumerate(names):
            if seat in have:
                row = await s.get(ChangeApprovalRow, have[seat].id)
                row.order = i
                continue
            s.add(ChangeApprovalRow(id=uuid4().hex[:16], study_id=study_id, change_id=p["id"], kind="seat", seat=seat,
                                    decision="pending", order=i))
        board = next((r for r in rows if r.kind == "board"), None)
        if board is None:
            s.add(ChangeApprovalRow(id=uuid4().hex[:16], study_id=study_id, change_id=p["id"], kind="board",
                                    seat="team_leader", decision="pending", impact_json=prev, order=999,
                                    data_json={"started_by": by, "started_at": now.isoformat()}))
        else:
            row = await s.get(ChangeApprovalRow, board.id)
            row.impact_json = prev
            row.data_json = {**dict(row.data_json or {}), "restarted_by": by, "restarted_at": now.isoformat()}
        await s.commit()
    return await view(study_id, p["id"])


async def agree(study_id: str, change_id: str, seat: str, decision: str, note: str = "", by: str = "") -> dict[str, Any]:
    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeApprovalRow
    if decision not in SEAT_DECISIONS:
        raise ChangeControlError(422, "bad_decision", f"decision must be one of {', '.join(SEAT_DECISIONS)}")
    p = await _proposal(study_id, change_id)
    rows = await _approvals(study_id, p["id"])
    st = flow_state(p, rows)
    if st == "not_started":
        raise ChangeControlError(409, "not_started", "Start the change review first")
    if st in ("approved", "rejected"):
        raise ChangeControlError(409, "decided", f"{p['code'] or p['id']} is already decided")
    row = next((r for r in rows if r.kind == "seat" and r.seat == seat), None)
    if row is None:
        raise ChangeControlError(409, "not_affected", f"{seat} is not an affected seat of {p['code'] or p['id']}",
                                 seats=[r.seat for r in rows if r.kind == "seat"])
    if decision == "object" and not note.strip():
        raise ChangeControlError(422, "note_required", "An objection needs a reason")
    async with get_session_factory()() as s:
        r = await s.get(ChangeApprovalRow, row.id)
        r.decision, r.note, r.by, r.at = decision, note.strip()[:4000], by[:120], _now()
        await s.commit()
    return await view(study_id, p["id"])


async def decide(study_id: str, change_id: str, decision: str, *, note: str = "", by: str = "",
                 apply: list[dict[str, Any]] | None = None, study: Any = None) -> dict[str, Any]:
    """The board's decision. ``approve`` needs every affected seat's agreement; it sets the
    proposal ``accepted``, applies the requirement edits (``apply``, or the proposal's
    ``data.apply``) and saves the new baseline revision. ``reject`` sets it ``rejected``."""
    from ..db.engine import get_session_factory
    from ..db.models_changes import ChangeApprovalRow, ChangeProposalRow
    if decision not in BOARD_DECISIONS:
        raise ChangeControlError(422, "bad_decision", f"decision must be one of {', '.join(BOARD_DECISIONS)}")
    p = await _proposal(study_id, change_id)
    rows = await _approvals(study_id, p["id"])
    st = flow_state(p, rows)
    if st == "not_started":
        raise ChangeControlError(409, "not_started", "Start the change review first")
    if st in ("approved", "rejected"):
        raise ChangeControlError(409, "decided", f"{p['code'] or p['id']} is already decided")
    if decision == "approve" and st != "agreed":
        pend = [r.seat for r in rows if r.kind == "seat" and r.decision != "agree"]
        raise ChangeControlError(409, "seats_pending", "Every affected seat must agree before approval: "
                                 + ", ".join(pend), seats=pend)
    applied: list[dict[str, Any]] = []
    baseline: dict[str, Any] = {}
    now = _now()
    if decision == "approve":
        applied = await _apply(study_id, apply if apply is not None else list(p["data"].get("apply") or []))
        baseline = await _baseline(study_id, p, by, applied, study)
    async with get_session_factory()() as s:
        board = next((r for r in rows if r.kind == "board"), None)
        if board is None:
            b = ChangeApprovalRow(id=uuid4().hex[:16], study_id=study_id, change_id=p["id"], kind="board",
                                  seat="team_leader", order=999)
            s.add(b)
        else:
            b = await s.get(ChangeApprovalRow, board.id)
        b.decision, b.note, b.by, b.at = decision, note.strip()[:4000], by[:120], now
        b.baseline_ref = baseline.get("id") or ""
        b.data_json = {**dict(b.data_json or {}), "applied": applied, "baseline": baseline}
        cp = await s.get(ChangeProposalRow, p["id"])
        cp.status = "accepted" if decision == "approve" else "rejected"
        cp.decided_by = (by or "board")[:120]
        cp.data_json = {**dict(cp.data_json or {}), "decided_at": now.isoformat(), "decision_note": note.strip()[:4000],
                        **({"baseline_ref": baseline.get("id")} if baseline.get("id") else {})}
        await s.commit()
    return await view(study_id, p["id"])


async def _apply(study_id: str, edits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Requirement edits of an approved change: ``[{code, field: value …}]`` (fields in
    ``APPLY_FIELDS``). Unknown codes are reported, not raised."""
    if not edits:
        return []
    from ..routers.requirements import _ensure_loaded, _requirements, update_requirement
    await _ensure_loaded()
    by_code = {r.get("code"): r for r in _requirements.values() if r.get("study_id") == study_id and r.get("code")}
    out = []
    for e in edits:
        if not isinstance(e, dict):
            continue
        code = str(e.get("code") or "")
        r = by_code.get(code)
        patch = {k: v for k, v in e.items() if k in APPLY_FIELDS}
        if r is None or not patch:
            out.append({"code": code, "applied": False, "reason": "unknown requirement" if r is None else "no field"})
            continue
        before = {k: r.get(k) for k in patch}
        await update_requirement(r["id"], patch)
        out.append({"code": code, "applied": True, "before": before, "after": patch})
    return out


async def _baseline(study_id: str, p: dict[str, Any], by: str, applied: list[dict[str, Any]], study: Any) -> dict[str, Any]:
    """A new revision of the configuration baseline: the kind of the last gate passed, the
    requirements, elements and risks as they stand after the change."""
    from ..db.gate_baseline_repo import list_baselines, save_baseline
    from ..routers.gates import gate_inputs, study_profile
    from . import gate_profiles as gp
    from .gate_reviews import baseline_kind
    try:
        ctx = await gate_inputs(study_id)
        study = study or ctx["study"]
        profile = study_profile(study)
        passed = [g for g in profile.get("gates") or [] if ((study.gate_states or {}).get(g["id"]) or {}).get("state") == "passed"]
        kind = baseline_kind(passed[-1], gp.load()) if passed else "mission"
        rev = 1 + sum(1 for b in await list_baselines(study_id) if str(b["gate"]).startswith("chg:"))
        code = p.get("code") or p["id"]
        snapshot = {"profile": profile["id"], "gate": f"chg:{code}", "kind": kind, "revision": rev, "change": code,
                    "after_gate": passed[-1]["id"] if passed else None,
                    "mission_need": study.mission_need.model_dump(mode="json"),
                    "requirements_model": study.requirements.model_dump(mode="json"),
                    "elements": ctx["elements"], "interfaces": ctx["interfaces"], "requirements": ctx["requirements"],
                    "risk_register": list(study.risk_register or []), "applied": applied, "criteria": [], "products": [],
                    "rids": [], "trades": {}, "review": {}}
        summary = {"kind": kind, "revision": rev, "change": code, "applied": len([a for a in applied if a.get("applied")]),
                   "elements": len(ctx["elements"]), "requirements": len(ctx["requirements"])}
        row = await save_baseline(study_id, f"chg:{code}"[:32], profile["id"], by or "board", summary, snapshot)
        return {"id": row["id"], "at": row["created_at"], "kind": kind, "revision": rev,
                "label": f"{kind} baseline rev. {rev} ({code})"}
    except Exception:  # noqa: BLE001 — the decision stands even if the snapshot fails
        logger.exception("change baseline not saved for %s/%s", study_id, p.get("code"))
        return {"id": None, "error": "baseline snapshot not saved"}


__all__ = ["BOARD_DECISIONS", "ChangeControlError", "SEAT_DECISIONS", "agree", "decide", "list_all", "start", "view"]
