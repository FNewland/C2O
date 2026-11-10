"""Change proposals and the open-item register of wave 3 (created empty by step 0).

Shared file, one class per owner (W0_SEAMS §9): each agent edits only its own class.

* ``ChangeProposalRow`` (``change_proposals``) — **owner L** (3.L4): an engineering change
  proposal or change request (ECP-01, CR-V2 …) with class, impact, affected requirement codes,
  source trade, status and decision gate.
* ``ChangeApprovalRow`` (``change_approvals``) — **owner D** (3.D7, PI addendum): the change-control
  flow of a change proposal: one row per affected seat (agree / object), the board decision and
  the new baseline it produced.
* ``OpenItemRow`` (``open_items``) — **owner D** (3.D4): one entry of the open-item register that
  joins RIDs, actions, conditional decisions, PI and seat decisions and change proposals, with the
  gate it blocks.

Every table is study-owned (``study_id``), so the project file carries it. Registered on
``models.Base`` (imported at the end of ``db/models.py``). Prefer ``data_json`` to new columns.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


# ─── owner L (3.L4) ───────────────────────────────────────────────────────

class ChangeProposalRow(Base):
    """An engineering change proposal (ECP) or change request (CR) (wave 3, 3.L4)."""
    __tablename__ = "change_proposals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24), default="")               # ECP-01, CR-V2
    kind: Mapped[str] = mapped_column(String(8), default="ecp")             # ecp | cr
    title: Mapped[str] = mapped_column(String(240), default="")
    change_class: Mapped[str] = mapped_column(String(16), default="")       # class I / II (ECSS-M-ST-40C)
    description: Mapped[str] = mapped_column(Text, default="")
    impact_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # {mass_kg, power_w, cost, schedule …}
    affected_codes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)       # requirement codes
    affected_requirement_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)  # resolved ids
    source_trade: Mapped[str] = mapped_column(String(24), default="")       # T-A01 …
    status: Mapped[str] = mapped_column(String(16), default="proposed")     # proposed accepted rejected closed
    decision_gate: Mapped[str] = mapped_column(String(16), default="")
    decided_by: Mapped[str] = mapped_column(String(120), default="")
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# ─── owner D (3.D4) ───────────────────────────────────────────────────────

class OpenItemRow(Base):
    """One entry of the open-item register (wave 3, 3.D4)."""
    __tablename__ = "open_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(32), default="")               # D-PI-01, D-PAY-01 …
    kind: Mapped[str] = mapped_column(String(24), default="decision")       # rid action conditional_decision pi_decision seat_decision change
    title: Mapped[str] = mapped_column(String(240), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    owner_seat: Mapped[str] = mapped_column(String(48), default="")
    status: Mapped[str] = mapped_column(String(16), default="open")         # open closed
    blocks_gate: Mapped[str] = mapped_column(String(16), default="")
    due: Mapped[str] = mapped_column(String(10), default="")                # YYYY-MM-DD
    condition: Mapped[str] = mapped_column(Text, default="")                # conditional decision
    fallback: Mapped[str] = mapped_column(Text, default="")
    resolution: Mapped[str] = mapped_column(Text, default="")
    source_ref: Mapped[str] = mapped_column(String(64), default="")         # trade id, RID id, ECP code …
    links_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)    # {risks: [], requirements: [] …}
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# ─── owner D (3.D7, PI addendum: change control on camera) ─────────────────

class ChangeApprovalRow(Base):
    """One step of the change-control flow of a change proposal (wave 3, 3.D7)."""
    __tablename__ = "change_approvals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    change_id: Mapped[str] = mapped_column(String(32), default="", index=True)   # change_proposals.id
    kind: Mapped[str] = mapped_column(String(16), default="seat")           # seat (affected seat) | board (decision)
    seat: Mapped[str] = mapped_column(String(48), default="")
    decision: Mapped[str] = mapped_column(String(16), default="pending")    # pending agree object approve reject
    by: Mapped[str] = mapped_column(String(120), default="")
    at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    impact_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # the impact preview it saw (L, 3.L6)
    baseline_ref: Mapped[str] = mapped_column(String(64), default="")       # gate baseline the decision produced
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
