"""Systems-engineering V tables of wave 3 (owner S; created empty by step 0).

* ``SeMoeRow`` (``se_moes``, 3.S3): a measure of effectiveness: measure, threshold, the objectives
  and needs it serves, who defines it (``placeholder`` = still to co-define).
* ``SeValidationActivityRow`` (``se_validation_activities``, 3.S5): a validation activity (V1 …):
  objectives, needs, MOEs, method, environment, stage, performer (a stakeholder id), acceptance,
  evidence and status.
* ``SeNeedValidationRow`` (``se_need_validation``, 3.S5): how one stakeholder need is validated.
* ``SeAssumptionRow`` (``se_assumptions``, 3.S6): an assumption (ASM-…): statement, what it
  affects, the evidence that would replace it, owner seat, due gate and status.

Stakeholders themselves stay in ``MissionNeed`` (``C/models/mission_need.py``, 3.S3).
Every table is study-owned (``study_id``), so the project file carries it. Registered on
``models.Base`` (imported at the end of ``db/models.py``). Prefer ``data_json`` to new columns.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class SeMoeRow(Base):
    """A measure of effectiveness (wave 3, 3.S3)."""
    __tablename__ = "se_moes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24), default="")               # MOE-01
    name: Mapped[str] = mapped_column(String(200), default="")
    name_fr: Mapped[str] = mapped_column(String(200), default="")
    measure: Mapped[str] = mapped_column(Text, default="")
    threshold: Mapped[str] = mapped_column(Text, default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(String(32), default="")
    objectives_json: Mapped[list | None] = mapped_column(JSON, nullable=True)   # ["O1", "O3"]
    needs_json: Mapped[list | None] = mapped_column(JSON, nullable=True)        # ["SN-02"]
    defined_by: Mapped[str] = mapped_column(String(120), default="")       # stakeholder id or seat
    placeholder: Mapped[bool] = mapped_column(Boolean, default=False)      # still to co-define
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class SeValidationActivityRow(Base):
    """A validation activity on the right side of the V (wave 3, 3.S5)."""
    __tablename__ = "se_validation_activities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24), default="")               # V1 … V7
    title: Mapped[str] = mapped_column(String(240), default="")
    title_fr: Mapped[str] = mapped_column(String(240), default="")
    objectives_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    needs_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    moes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    requirement_codes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    method: Mapped[str] = mapped_column(String(64), default="")
    environment: Mapped[str] = mapped_column(Text, default="")
    stage: Mapped[str] = mapped_column(String(16), default="")              # PRR … IOV, ORR, CRR, phase_e
    performer: Mapped[str] = mapped_column(String(120), default="")         # stakeholder id (SH-…)
    acceptance: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="planned")      # proposed planned done failed
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class SeNeedValidationRow(Base):
    """How one stakeholder need is validated (wave 3, 3.S5)."""
    __tablename__ = "se_need_validation"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    need_code: Mapped[str] = mapped_column(String(24), default="")          # SN-01
    activity_codes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)   # ["V1"]
    method: Mapped[str] = mapped_column(String(64), default="")
    criterion: Mapped[str] = mapped_column(Text, default="")
    stage: Mapped[str] = mapped_column(String(16), default="")
    status: Mapped[str] = mapped_column(String(16), default="planned")
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class SeAssumptionRow(Base):
    """An assumption of the design, to be replaced by evidence (wave 3, 3.S6)."""
    __tablename__ = "se_assumptions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24), default="")               # ASM-01
    statement: Mapped[str] = mapped_column(Text, default="")
    affects_json: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{kind, ref}] element/field/requirement/budget
    replace_with: Mapped[str] = mapped_column(Text, default="")             # the evidence that would replace it
    owner_seat: Mapped[str] = mapped_column(String(48), default="")
    due_gate: Mapped[str] = mapped_column(String(16), default="")
    status: Mapped[str] = mapped_column(String(16), default="open")         # open confirmed replaced retired
    source: Mapped[str] = mapped_column(String(200), default="")            # budgets.yaml path, requirement code …
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
