"""AIT tables of work package W8a: model philosophy and the test matrix.

* ``AitModelRow`` — one development or flight model of the study (breadboard, engineering
  model, qualification model, protoflight model, flight model …), with the month it is due
  (counted from the project start, see ``models_schedule.ProjectSettingsRow``), its level and
  its purpose. The set of rows plus ``philosophy`` (protoflight, prototype, hybrid) is the
  model philosophy of ECSS-E-ST-10-02C §5.2.5 / ECSS-E-HB-10-02A.
* ``AitTestRow`` — one line of the test matrix: test × models × level, with the source of its
  level (the launch provider's user guide, ECSS-E-ST-10-03C, GEVS …), the facility, the
  environment levels and the requirements it verifies (codes).

Both tables are study-owned (``study_id``), so the project file carries them. Rows proposed by
``services/ait.py`` carry ``origin = "proposed"``; a row the user changed is ``origin = "user"``
and is never overwritten by a later proposal.
Registered on ``models.Base`` (imported at the end of ``db/models.py``).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class AitModelRow(Base):
    """A development or flight model in the model philosophy (W8a)."""
    __tablename__ = "ait_models"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(16))            # BB | EM | STM | QM | PFM | FM | FS
    name: Mapped[str] = mapped_column(String(128), default="")
    name_fr: Mapped[str] = mapped_column(String(128), default="")
    philosophy: Mapped[str] = mapped_column(String(24), default="protoflight")   # protoflight | prototype | hybrid
    level: Mapped[str] = mapped_column(String(16), default="system")   # unit | subsystem | system
    due_month: Mapped[int | None] = mapped_column(Integer, nullable=True)   # months after project start
    purpose: Mapped[str] = mapped_column(Text, default="")
    purpose_fr: Mapped[str] = mapped_column(Text, default="")
    build_standard: Mapped[str] = mapped_column(String(64), default="")   # e.g. "COTS boards, lab harness"
    status: Mapped[str] = mapped_column(String(16), default="planned")   # planned | built | tested | retired
    origin: Mapped[str] = mapped_column(String(16), default="user")      # proposed | user
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class AitTestRow(Base):
    """One test of the AIT test matrix (W8a): test × models × level."""
    __tablename__ = "ait_tests"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24))             # T-ENV-01 …
    name: Mapped[str] = mapped_column(String(160), default="")
    name_fr: Mapped[str] = mapped_column(String(160), default="")
    # environmental | functional | performance | emc | deployment | end_to_end | mission | physical
    category: Mapped[str] = mapped_column(String(24), default="functional")
    models_json: Mapped[list | None] = mapped_column(JSON, nullable=True)       # model codes, e.g. ["EM", "PFM"]
    level: Mapped[str] = mapped_column(String(16), default="system")           # unit | subsystem | system
    level_source: Mapped[str] = mapped_column(String(160), default="")        # where the test level comes from
    facility: Mapped[str] = mapped_column(String(160), default="")
    environment_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # levels, durations, cycles …
    requirement_codes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)   # codes it verifies
    stage: Mapped[str] = mapped_column(String(8), default="QR")                # PDR CDR QR AR IOV
    status: Mapped[str] = mapped_column(String(16), default="planned")        # planned | done | waived
    notes: Mapped[str] = mapped_column(Text, default="")
    origin: Mapped[str] = mapped_column(String(16), default="user")            # proposed | user
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
