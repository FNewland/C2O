"""ORM table of the Licensing tab (W5.03).

``LicensingRow`` holds, per study, the licensing inputs that cannot be derived from the design
(applicant, contacts, system participants and affiliates, the command and data protection plan,
data policy and EULA, launch provider and site, frequency-assignment overrides, the disposal
device's reliability figures, imported DRAMA/DAS results) and the filing tracker. Everything the
design already knows (orbit, mass, sensor, links, stations, disposal lifetime) is derived at export
time by ``services/licensing.py`` and is not stored here.

The table is study-owned (``study_id`` is the key), so the project file carries it. It is
registered on ``models.Base`` by the import at the end of ``models.py``.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LicensingRow(Base):
    """The licensing record of one study (one row per study)."""
    __tablename__ = "licensing_records"

    study_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    data_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[str] = mapped_column(String(64), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
