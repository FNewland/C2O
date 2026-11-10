"""ORM table of the gate review record: RIDs and actions (W4.08, Nov 2026).

``ReviewItemRow`` — one review item discrepancy (RID) or action raised at a review gate: number,
gate, kind, the seat that raised it, description, owner seat, due date, status and the closure
evidence. The review's chair note and go / no-go decision live with the gate state
(``study.gate_states[gate]["review"]``, routers/gates.py).

Registered on ``models.Base`` (models.py imports this module at its end); study-owned, so the
project file carries it.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReviewItemRow(Base):
    """A RID or an action of a review gate (W4.08)."""
    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    gate: Mapped[str] = mapped_column(String(16), index=True)                # profile gate id (mdr, prr ... frr)
    number: Mapped[str] = mapped_column(String(32), default="")              # RID-MDR-01 / ACT-MDR-01
    kind: Mapped[str] = mapped_column(String(8), default="rid")              # rid | action
    criterion_id: Mapped[str] = mapped_column(String(40), default="")        # gate criterion it is about, if any
    raised_by_seat: Mapped[str] = mapped_column(String(40), default="")
    raised_by: Mapped[str] = mapped_column(String(160), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(8), default="minor")       # major | minor
    owner_seat: Mapped[str] = mapped_column(String(40), default="")
    due_date: Mapped[str] = mapped_column(String(10), default="")           # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String(12), default="open")          # open | in_work | closed | rejected
    closure_evidence: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
