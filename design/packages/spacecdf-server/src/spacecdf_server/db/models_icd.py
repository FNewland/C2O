"""ICD issue control of wave 3 (3.R6, owner R; created empty by step 0; PI addendum).

``IcdIssueRow`` (``icd_issues``): one issue of one interface control document (or one interface
agreement): issue letter and revision, state (draft → issue_a → baselined), the two owning seats
(provider and consumer) and the sign-off of each. The SRR and PDR criteria (PDR-EC-02, R) read
the latest issue of each ICD. Earlier issues are kept (history).

Study-owned (``study_id``), so the project file carries it. Registered on ``models.Base``
(imported at the end of ``db/models.py``). Prefer ``data_json`` to new columns.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


#: issue states (3.R6)
ICD_STATES = ("draft", "issue_a", "issue_b", "baselined", "superseded")


class IcdIssueRow(Base):
    """One issue of an ICD with its two-seat sign-off (wave 3, 3.R6)."""
    __tablename__ = "icd_issues"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    icd_ref: Mapped[str] = mapped_column(String(48), default="")            # ICD-DEP-01, the requirement's icd_ref
    interface_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)   # element interface
    title: Mapped[str] = mapped_column(String(240), default="")
    issue: Mapped[str] = mapped_column(String(8), default="")               # "", A, B …
    revision: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(16), default="draft")         # ICD_STATES
    provider_seat: Mapped[str] = mapped_column(String(48), default="")
    consumer_seat: Mapped[str] = mapped_column(String(48), default="")
    signoffs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # {seat: {by, at, issue, revision}}
    requirement_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    change_note: Mapped[str] = mapped_column(Text, default="")
    history_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
