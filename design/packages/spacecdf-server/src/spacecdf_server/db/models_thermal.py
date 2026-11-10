"""Thermal nodal model of wave 3 (3.A6; owner A after the step-0 rebalance, see W0_SEAMS §9;
created empty by step 0; PI addendum).

* ``ThermalNodeRow`` (``thermal_nodes``): a node (6–10 for the teaching model): element,
  thermal capacitance, area, absorptivity / emissivity, internal dissipation per case, operating
  and survival limits (KB), heater power.
* ``ThermalCouplingRow`` (``thermal_couplings``): a conductive or radiative coupling between two
  nodes (or a node and space).
* ``ThermalCaseRow`` (``thermal_cases``): a design case (hot / cold): β, eclipse, attitude, mode
  dissipation, environment; the solved node temperatures and the margins (design, acceptance,
  qualification per ECSS-E-ST-31C) in ``results_json``. H's ``services/orbit_season.py`` (3.H4)
  proposes the β / eclipse of the hot and cold cases.

Study-owned (``study_id``). Registered on ``models.Base`` (imported at the end of ``db/models.py``).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class ThermalNodeRow(Base):
    """A node of the thermal model (wave 3, 3.A6)."""
    __tablename__ = "thermal_nodes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24), default="")               # N01 …
    name: Mapped[str] = mapped_column(String(160), default="")
    element_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(16), default="diffusion")      # diffusion | boundary (space)
    capacitance_j_k: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    absorptivity: Mapped[float | None] = mapped_column(Float, nullable=True)
    emissivity: Mapped[float | None] = mapped_column(Float, nullable=True)
    dissipation_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # {case or mode: W}
    op_min_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    op_max_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    survival_min_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    survival_max_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    limits_source: Mapped[str] = mapped_column(String(120), default="")     # kb:<id> | datasheet | assumption
    heater_w: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ThermalCouplingRow(Base):
    """A conductive or radiative coupling (wave 3, 3.A6)."""
    __tablename__ = "thermal_couplings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    node_a: Mapped[str] = mapped_column(String(32), default="")             # node id
    node_b: Mapped[str] = mapped_column(String(32), default="")             # node id, or "space"
    kind: Mapped[str] = mapped_column(String(16), default="conductive")     # conductive | radiative
    value: Mapped[float | None] = mapped_column(Float, nullable=True)       # W/K, or m² for radiative (GR)
    source: Mapped[str] = mapped_column(String(120), default="")
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ThermalCaseRow(Base):
    """A hot or cold design case and its solution (wave 3, 3.A6)."""
    __tablename__ = "thermal_cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(24), default="")               # HOT-OP, COLD-SURV …
    kind: Mapped[str] = mapped_column(String(16), default="hot")            # hot | cold
    beta_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    eclipse_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    mode_key: Mapped[str] = mapped_column(String(48), default="")
    environment_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # solar, albedo, IR, EOL optics
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)       # {node: {t_c, margin_design_c …}}
    status: Mapped[str] = mapped_column(String(16), default="proposed")     # proposed accepted solved
    source: Mapped[str] = mapped_column(String(120), default="")            # orbit_season (H) | user
    data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="user")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
