"""Electrical and data-handling design elements (design rules §2.1, §2.4, §5 D4–D6).

Power rails, PCDU/EPS power lines (switches), data buses, bus nodes (addresses) and
element ports. Every row can be proposed by a rule (``origin = "rule:<RULE-ID>"``,
``status = "suggested"``) and then accepted, edited or rejected, like the interface
proposals: a suggested row counts in the checks until it is rejected, a rejected row is
kept so the same proposal is never made again, and a row the user edited is never
overwritten by the rules (``edited``); when the facts a rule used change
(``inputs_hash``) an accepted row is marked ``review = "stale"`` for its owner seat.

The tables are created by ``Base.metadata.create_all`` (imported at the end of
``db/models.py``); columns added later are picked up by ``db/migrate.py``.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, _utcnow


class _ProposalMixin:
    """Provenance and review fields shared by every proposable electrical row."""

    # "suggested" (rule baseline, counts until rejected) | "accepted" | "rejected"
    status: Mapped[str] = mapped_column(String(16), default="accepted")
    # "user" | "rule:<RULE-ID>" (configs/electrical_rules.yaml)
    origin: Mapped[str] = mapped_column(String(64), default="user")
    rationale_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # {en, fr}
    standard_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # hash of the facts the rule used; a change marks an accepted row "stale"
    inputs_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    edited: Mapped[bool] = mapped_column(Boolean, default=False)
    review: Mapped[str | None] = mapped_column(String(16), nullable=True)      # None | "stale"
    # what the rule would set now, kept for the owner when the row is accepted/edited ("stale")
    proposed_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class PowerRailRow(_ProposalMixin, Base):
    """A voltage rail offered by an EPS/PCDU (regulated converter output or the
    unregulated battery bus)."""

    __tablename__ = "power_rails"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    eps_element_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    voltage_v: Mapped[float] = mapped_column(Float)
    regulated: Mapped[bool] = mapped_column(Boolean, default=True)
    # converter rating (A); None = unknown (capacity check not evaluated)
    max_current_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    v_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    v_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class PowerLineRow(_ProposalMixin, Base):
    """A PCDU/EPS output line (switch / LCL) and the loads on it."""

    __tablename__ = "power_lines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    eps_element_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    rail_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    line_no: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(128), default="")
    # True: commandable switch (S8 EPS_POWER_ON/OFF); False: always-on line
    switchable: Mapped[bool] = mapped_column(Boolean, default=True)
    # LCL trip current (A)
    lcl_limit_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    # line state after separation (deployment switches released, before boot) and at OBC boot
    default_on_separation: Mapped[bool] = mapped_column(Boolean, default=False)
    default_on_boot: Mapped[bool] = mapped_column(Boolean, default=False)
    # inhibit identifiers that open this line (e.g. "deployment_switch", "rbf", "rf_tx_timer")
    inhibits_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    load_element_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class DataBusRow(_ProposalMixin, Base):
    """A data bus segment (CAN, I2C, SPI, UART, RS-485, SpaceWire …)."""

    __tablename__ = "data_buses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    protocol: Mapped[str] = mapped_column(String(32))
    segment: Mapped[str] = mapped_column(String(16), default="A")
    bit_rate_bps: Mapped[float | None] = mapped_column(Float, nullable=True)
    # "none" | "cold" | "hot": this segment is duplicated (nominal + redundant harness)
    redundancy: Mapped[str] = mapped_column(String(16), default="none")
    redundant_with_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    master_element_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    max_devices: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class BusNodeRow(_ProposalMixin, Base):
    """An element on a bus, with its address (unique per bus segment)."""

    __tablename__ = "bus_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    bus_id: Mapped[str] = mapped_column(String(64), index=True)
    element_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16), default="node")     # master | node
    address: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_rate_bps: Mapped[float | None] = mapped_column(Float, nullable=True)
    # the data link that implies this node (None for a node added by hand)
    interface_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ElementPortRow(_ProposalMixin, Base):
    """A port on an element; interfaces bind ports (``interface_ids_json``)."""

    __tablename__ = "element_ports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    element_id: Mapped[str] = mapped_column(String(64), index=True)
    # power_in | power_out | data | rf | mechanical | thermal | signal | optical | fluid | timing
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(128), default="")
    connector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    properties_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interface_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    line_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bus_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
