"""Schedule-lite tables of work package W11a: project settings, milestones, work packages.

* ``ProjectSettingsRow`` — one row per study: project start, reporting currency (EUR or CAD,
  with the exchange rate used), "launch provided by the agency" (removes the launch cost) and
  the cost-estimate options.
* ``MilestoneRow`` — a dated milestone: a review gate of the study's gate profile, the extra
  ECSS reviews (QR, AR), the Flight Readiness Review, model deliveries and launch.
* ``WorkPackageRow`` — one work package of the WBS (ECSS-M-ST-10C §5.4), optionally tied to a
  product-tree element (``element_id``); elements may also name their work package through the
  existing ``design_elements.work_package_id`` column (the WBS code).

Every table is study-owned (``study_id``), so the project file carries it. Proposed rows have
``origin = "proposed"``; rows the user changed are ``origin = "user"`` and a new proposal keeps them.
Registered on ``models.Base`` (imported at the end of ``db/models.py``).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class ProjectSettingsRow(Base):
    """Project-level settings used by the schedule and the cost estimate (one per study)."""
    __tablename__ = "project_settings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True, unique=True)
    start_date: Mapped[str] = mapped_column(String(10), default="")      # "YYYY-MM" or "YYYY-MM-DD"
    currency: Mapped[str] = mapped_column(String(3), default="EUR")      # EUR | CAD
    eur_to_cad: Mapped[float] = mapped_column(Float, default=1.6129)     # 1 CAD = 0.62 EUR (KB rate)
    launch_provided: Mapped[bool] = mapped_column(Boolean, default=False)   # launch provided by the agency
    launch_cost_keur: Mapped[float | None] = mapped_column(Float, nullable=True)   # when bought
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class MilestoneRow(Base):
    """A dated project milestone (W11a)."""
    __tablename__ = "schedule_milestones"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24))                 # MDR, PRR, …, QR, AR, FRR, LAUNCH, BB …
    kind: Mapped[str] = mapped_column(String(16), default="review")   # review | model | launch | other
    gate_id: Mapped[str] = mapped_column(String(32), default="")      # profile gate id when kind = review
    name: Mapped[str] = mapped_column(String(160), default="")
    name_fr: Mapped[str] = mapped_column(String(160), default="")
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)  # months after project start
    date: Mapped[str] = mapped_column(String(10), default="")        # "YYYY-MM" (derived or set)
    status: Mapped[str] = mapped_column(String(16), default="planned")   # planned | held | passed
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class WorkPackageRow(Base):
    """One work package of the work breakdown structure (W11a)."""
    __tablename__ = "work_packages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24))                  # WBS code, e.g. "4.3"
    parent_code: Mapped[str] = mapped_column(String(24), default="")
    name: Mapped[str] = mapped_column(String(160), default="")
    name_fr: Mapped[str] = mapped_column(String(160), default="")
    element_id: Mapped[str | None] = mapped_column(String(64), nullable=True)   # product-tree node
    owner_seat: Mapped[str] = mapped_column(String(48), default="")
    start_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deliverables_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
