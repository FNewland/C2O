"""Negotiation records of wave 3 (3.H6, owner H; created empty by step 0).

``NegotiationRecordRow`` (``negotiation_records``) records what the seats must agree: the issue,
the coupled parameters (``key_numbers`` keys with their live values), the seats, the options with
their computed effects, the agreed values, one sign-off per seat (the IF-05 pattern), the reopen
trigger and the links to requirements, risks, trades, RIDs and change proposals.

Study-owned (``study_id``), so the project file carries it. Registered on ``models.Base``
(imported at the end of ``db/models.py``). Prefer ``data_json`` to new columns.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class NegotiationRecordRow(Base):
    """A negotiation between seats and what they agreed (wave 3, 3.H6)."""
    __tablename__ = "negotiation_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(16), default="")               # N1, N3, N7 …
    issue: Mapped[str] = mapped_column(Text, default="")
    issue_fr: Mapped[str] = mapped_column(Text, default="")
    parameters_json: Mapped[list | None] = mapped_column(JSON, nullable=True)   # key_numbers keys
    seats_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    options_json: Mapped[list | None] = mapped_column(JSON, nullable=True)      # [{label, values, effects}]
    agreed_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)       # {key: value}
    signoffs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)     # {seat: {by, at}}
    reopen_trigger: Mapped[str] = mapped_column(Text, default="")
    links_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)        # {requirements, risks, trades, rids, changes}
    status: Mapped[str] = mapped_column(String(16), default="proposed")     # proposed agreed reopened
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
