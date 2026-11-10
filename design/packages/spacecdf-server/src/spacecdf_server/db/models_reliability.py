"""Reliability analysis and FMEA/FMECA worksheet of wave 3 (3.A5, owner A; created empty by
step 0; PI addendum).

* ``ReliabilityBlockRow`` (``reliability_blocks``): one block of the reliability block diagram:
  element, failure rate (FIT or per hour) and its source (KB, heritage, handbook), redundancy
  (k-of-n), duty cycle, and the block's reliability over the mission-success horizon.
* ``FmeaRow`` (``fmea_rows``): one line of the FMEA/FMECA worksheet per subsystem: item, failure
  mode, cause, local / system effect, severity, probability, criticality, detection, the FDIR
  reaction (CDR model) and the linked risks. PDR-EC-05 (R wires it) reads both.

Study-owned (``study_id``). Registered on ``models.Base`` (imported at the end of
``db/models.py``). The legacy catalogue FMECA (``routers/fmeca.py``) stays as a proposer.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class ReliabilityBlockRow(Base):
    """One block of the reliability block diagram (wave 3, 3.A5)."""
    __tablename__ = "reliability_blocks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    element_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    subsystem: Mapped[str] = mapped_column(String(48), default="")
    parent_block: Mapped[str] = mapped_column(String(32), default="")        # series / parallel grouping
    arrangement: Mapped[str] = mapped_column(String(16), default="series")   # series | parallel | k_of_n
    k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_rate_fit: Mapped[float | None] = mapped_column(Float, nullable=True)   # failures per 1e9 h
    rate_source: Mapped[str] = mapped_column(String(120), default="")        # kb:<id> | heritage | handbook | assumption
    duty_cycle: Mapped[float | None] = mapped_column(Float, nullable=True)
    reliability: Mapped[float | None] = mapped_column(Float, nullable=True)  # over the horizon (computed)
    horizon_months: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class FmeaRow(Base):
    """One line of the FMEA/FMECA worksheet (wave 3, 3.A5)."""
    __tablename__ = "fmea_rows"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24), default="")               # FM-EPS-01
    element_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    subsystem: Mapped[str] = mapped_column(String(48), default="")
    item: Mapped[str] = mapped_column(String(200), default="")
    function: Mapped[str] = mapped_column(String(200), default="")
    failure_mode: Mapped[str] = mapped_column(Text, default="")
    cause: Mapped[str] = mapped_column(Text, default="")
    local_effect: Mapped[str] = mapped_column(Text, default="")
    system_effect: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)     # 1..4 (ECSS-Q-ST-30-02C)
    probability: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1..5
    criticality: Mapped[int | None] = mapped_column(Integer, nullable=True)  # severity × probability
    detection: Mapped[str] = mapped_column(Text, default="")
    fdir_ref: Mapped[str] = mapped_column(String(64), default="")           # CDR FDIR row / OBCP
    mitigation: Mapped[str] = mapped_column(Text, default="")
    risk_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    single_point: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="open")
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
