"""Cost pricing of wave 3 (3.A7, owner A; created empty by step 0; PI addendum).

``CostItemRow`` (``cost_items``): one priced line of the study cost model at MDR/PRR: labour
(person-months × rate), test campaigns (facility days × rate), hardware, reserve (percent of the
base), launch (zero when provided), other. ``services/cost_engine.py`` totals them; MDR-EC-08 and
PRR-EC-11 judge the total (R wires them).

Study-owned (``study_id``). Registered on ``models.Base`` (imported at the end of ``db/models.py``).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


#: cost categories (3.A7)
COST_CATEGORIES = ("labour", "test_campaign", "hardware", "software", "facilities", "launch", "operations",
                   "reserve", "other")


class CostItemRow(Base):
    """A priced line of the cost model (wave 3, 3.A7)."""
    __tablename__ = "cost_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    category: Mapped[str] = mapped_column(String(16), default="other")      # COST_CATEGORIES
    name: Mapped[str] = mapped_column(String(200), default="")
    name_fr: Mapped[str] = mapped_column(String(200), default="")
    wbs_code: Mapped[str] = mapped_column(String(24), default="")
    element_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)    # person-months, facility days, units
    unit: Mapped[str] = mapped_column(String(24), default="")
    unit_cost_keur: Mapped[float | None] = mapped_column(Float, nullable=True)
    percent_of_base: Mapped[float | None] = mapped_column(Float, nullable=True)   # reserve lines
    total_keur: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(160), default="")            # reference class, quote, KB
    basis: Mapped[str] = mapped_column(Text, default="")
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
