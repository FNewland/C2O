"""ORM tables of the Nov 2026 mode model (spacecdf_design_rules.md §5 D1, D7, D8).

* ``ModeTransitionRow`` — the mode machine's edges (MO-05): trigger and guard per transition,
  replacing guards parsed from mode description text.
* ``RuleProposalRow`` — a generic rule proposal (D1): one record per (rule, target) with its
  source, rationale, inputs hash and review status. Used here for FDIR monitor/action stubs
  (FD-01/02), heater proposals (EI-05 / rule 7) and risk-register proposals (FD-03 / RV-04).
* ``HeaterRow`` — a heater with thermostat set-points and a proposed power line (D8).

Registered on ``models.Base`` (models.py imports this module at its end).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModeTransitionRow(Base):
    """One transition of the spacecraft mode machine (rule MO-05)."""
    __tablename__ = "mode_transitions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    from_mode_id: Mapped[str] = mapped_column(String(64), index=True)
    to_mode_id: Mapped[str] = mapped_column(String(64), index=True)
    trigger: Mapped[str] = mapped_column(String(16), default="ground_tc")   # ground_tc|autonomous|timer|event
    guard_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)     # {param, op, value, unit, text}
    monitor_ref: Mapped[str] = mapped_column(String(64), default="")        # RuleProposalRow id of the monitor
    priority: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    origin: Mapped[str] = mapped_column(String(48), default="user")          # user | template | conops
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class RuleProposalRow(Base):
    """A value or entity proposed by a deterministic rule, kept with its review status.

    status: suggested | accepted | edited | rejected | stale. Rejected rows are kept so the
    same (rule_id, target_key) is never proposed again; a changed ``inputs_hash`` marks an
    accepted/edited row stale (rule 13) and silently refreshes a suggested one.
    """
    __tablename__ = "rule_proposals"
    __table_args__ = (UniqueConstraint("study_id", "rule_id", "target_key", name="uq_rule_proposal_target"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    rule_id: Mapped[str] = mapped_column(String(16), index=True)            # FD-01, FD-02, FD-03, RV-04, EI-05
    kind: Mapped[str] = mapped_column(String(24), index=True)               # monitor | action | heater | risk
    target_key: Mapped[str] = mapped_column(String(160))                    # stable key of what is proposed
    element_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    standard_ref: Mapped[str] = mapped_column(String(255), default="")
    c2o_default: Mapped[bool] = mapped_column(default=True)
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict)        # {en, fr}
    inputs_hash: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(String(16), default="suggested")
    owner_seat: Mapped[str] = mapped_column(String(40), default="")
    result_ref: Mapped[str] = mapped_column(String(64), default="")        # e.g. risk id / heater id once accepted
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class HeaterRow(Base):
    """A heater with thermostat set-points (D8; sim ``tcs.yaml heaters``)."""
    __tablename__ = "heaters"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    element_id: Mapped[str] = mapped_column(String(64), index=True)        # the unit (thermal node) heated
    heater_element_id: Mapped[str] = mapped_column(String(64), default="")  # the heater component, once created
    name: Mapped[str] = mapped_column(String(128), default="")
    power_w: Mapped[float] = mapped_column(default=0.0)
    on_c: Mapped[float] = mapped_column(default=0.0)
    off_c: Mapped[float] = mapped_column(default=5.0)
    control: Mapped[str] = mapped_column(String(16), default="auto")       # auto (thermostat) | manual
    line_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)     # proposed power line (electrical model)
    proposal_id: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
