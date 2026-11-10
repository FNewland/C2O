"""ORM table of the named link-budget cases (W4.04, Nov 2026).

``LinkBudgetRow`` — one named link case of a study: direction (downlink / uplink), band, ground
station, elevation, rate tier, coding, transmitter power, gains, losses, system noise
temperature, required Eb/N0 and the computed margin. The study's *design case* stays in
``study.requirements.link`` (what the analyses read); a case marked ``is_design_case`` is the one
that was last applied to it (``POST /studies/{id}/link-budgets/{case}/apply``).

Registered on ``models.Base`` (models.py imports this module at its end); study-owned, so the
project file carries it.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LinkBudgetRow(Base):
    """A named link-budget case (W4.04)."""
    __tablename__ = "link_budgets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(160), default="")
    direction: Mapped[str] = mapped_column(String(8), default="downlink")     # downlink | uplink
    band: Mapped[str] = mapped_column(String(8), default="")                  # UHF | VHF | S | X ...
    station: Mapped[str] = mapped_column(String(160), default="")             # ground-station name
    elevation_deg: Mapped[float] = mapped_column(Float, default=10.0)
    rate_tier: Mapped[str] = mapped_column(String(40), default="")            # e.g. "high 38.4 kbit/s"
    data_rate_bps: Mapped[float] = mapped_column(Float, default=9600.0)
    modulation: Mapped[str] = mapped_column(String(64), default="")
    coding: Mapped[str] = mapped_column(String(64), default="")
    frequency_mhz: Mapped[float] = mapped_column(Float, default=0.0)
    tx_power_w: Mapped[float] = mapped_column(Float, default=1.0)
    tx_antenna_gain_dbi: Mapped[float] = mapped_column(Float, default=0.0)
    tx_losses_db: Mapped[float] = mapped_column(Float, default=0.0)
    slant_range_km: Mapped[float] = mapped_column(Float, default=0.0)          # 0 = from altitude and elevation
    polarisation_loss_db: Mapped[float] = mapped_column(Float, default=0.0)
    atmospheric_loss_db: Mapped[float] = mapped_column(Float, default=0.0)
    pointing_loss_db: Mapped[float] = mapped_column(Float, default=0.0)
    other_losses_db: Mapped[float] = mapped_column(Float, default=0.0)
    rx_antenna_gain_dbi: Mapped[float] = mapped_column(Float, default=0.0)
    rx_losses_db: Mapped[float] = mapped_column(Float, default=0.0)
    system_noise_temp_k: Mapped[float] = mapped_column(Float, default=290.0)
    required_ebn0_db: Mapped[float] = mapped_column(Float, default=0.0)
    implementation_loss_db: Mapped[float] = mapped_column(Float, default=0.0)
    margin_db: Mapped[float | None] = mapped_column(Float, nullable=True)     # computed on every save
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)    # the cascade (EIRP, FSPL, G/T ...)
    is_design_case: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(64), default="user")          # user | link_budget_tool | seed
    notes: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
