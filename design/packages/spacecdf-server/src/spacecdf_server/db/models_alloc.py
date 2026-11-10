"""Allocation ledger of wave 3 (3.A2, owner A; created empty by step 0).

``AllocationLedgerRow`` (``allocation_ledger``) is one agreed (or proposed, or disputed) budget
allocation to one element: the mass, average / peak / per-mode power, data, pointing,
registration or timing share an element owner signs up to. The Systems reserve is a line of its
own (``element_code = "SYS"``, ``line_kind = "reserve"``). ``BudgetAllocationRow`` stays the cache
the Budget tab already reads; the ledger is the record with the owner's sign-off and history.

Every table is study-owned (``study_id``), so the project file carries it. Registered on
``models.Base`` (imported at the end of ``db/models.py``). Prefer the ``data_json`` field to a new
column for anything the 3.A2 work finds it needs.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow

#: budget types of a ledger line (3.A2)
LEDGER_BUDGET_TYPES = ("mass", "power_avg", "power_peak", "power_mode", "data", "pointing", "registration", "timing")
#: line states (3.A2): an owner agrees or disputes a proposed line
LEDGER_STATUSES = ("proposed", "agreed", "disputed")


class AllocationLedgerRow(Base):
    """One budget allocation line with its owner's sign-off (wave 3, 3.A2)."""
    __tablename__ = "allocation_ledger"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    element_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)   # product-tree node
    element_code: Mapped[str] = mapped_column(String(16), default="")       # v2 element id: PAY, EPS ... SYS
    line_kind: Mapped[str] = mapped_column(String(16), default="allocation")   # allocation | reserve
    budget_type: Mapped[str] = mapped_column(String(16), default="mass")      # LEDGER_BUDGET_TYPES
    mode_key: Mapped[str] = mapped_column(String(48), default="")           # power_mode lines: the mode
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(16), default="")
    cbe: Mapped[float | None] = mapped_column(Float, nullable=True)         # current best estimate behind it
    margined: Mapped[float | None] = mapped_column(Float, nullable=True)    # CBE with maturity
    requirement_id: Mapped[str | None] = mapped_column(String(32), nullable=True)   # covering requirement
    requirement_code: Mapped[str] = mapped_column(String(32), default="")
    budget_ref: Mapped[str] = mapped_column(String(128), default="")        # budgets.yaml path
    owner_seat: Mapped[str] = mapped_column(String(48), default="")
    status: Mapped[str] = mapped_column(String(16), default="proposed")     # LEDGER_STATUSES
    agreed_by: Mapped[str] = mapped_column(String(120), default="")
    agreed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    history_json: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{at, by, field, old, new, why}]
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")         # user | proposed | import
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
