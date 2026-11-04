"""CDR design model rows (Nov 2026, phase 2): TM/TC database, FDIR, AOCS modes and gains,
TT&C rate ladder, power-line states per mode, operations organisation.

One table, one row per database entry: ``kind`` names the collection (``parameters``,
``hk``, ``commands``, ``events``, ``monitors``, ``event_actions`` …, see
``services/cdr_model.KINDS``), ``key`` its natural key inside the study (parameter id,
SID, function name …) and ``data_json`` the entry itself. The proposal life cycle is the
electrical one (``electrical_models._ProposalMixin``): a rule row starts ``suggested`` and
counts until rejected; a rejected row is kept so it is never proposed again; an edited row
is never overwritten and turns ``review = "stale"`` when the rule's facts move.

``origin`` is ``user``, ``rule:<RULE-ID>`` or ``import:eosat1`` (the read-only reference
database imported from ``sim/configs/eosat1``).
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .electrical_models import _ProposalMixin
from .models import Base


class CdrRow(_ProposalMixin, Base):
    __tablename__ = "cdr_rows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)
    key: Mapped[str] = mapped_column(String(96), default="")
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    owner_seat: Mapped[str] = mapped_column(String(40), default="")
