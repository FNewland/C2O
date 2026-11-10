"""Debris assessment of wave 3 (3.L8, owner L; created empty by step 0; PI addendum).

``DebrisAssessmentRow`` (``debris_assessments``): one run of the DRAMA/DAS-like assessment in the
tool: the inputs (mass, area, altitude, solar cycle, sail), orbital lifetime with and without the
disposal device, casualty risk, collision probability, compliance against the 5-year and 25-year
rules, and its acceptance (by whom, at which gate; accepted at SRR in the walkthrough).

Study-owned (``study_id``). Registered on ``models.Base`` (imported at the end of ``db/models.py``).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class DebrisAssessmentRow(Base):
    """A debris assessment and its acceptance (wave 3, 3.L8)."""
    __tablename__ = "debris_assessments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    inputs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    lifetime_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    lifetime_without_device_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    casualty_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    collision_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # per case, compliance lines
    status: Mapped[str] = mapped_column(String(16), default="draft")        # draft | submitted | accepted | superseded
    accepted_by: Mapped[str] = mapped_column(String(120), default="")
    accepted_gate: Mapped[str] = mapped_column(String(16), default="")
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
