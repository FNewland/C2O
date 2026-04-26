"""SQLAlchemy ORM models for SpaceCDF persistence."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class StudyRow(Base):
    __tablename__ = "studies"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)

    sessions: Mapped[list["SessionRow"]] = relationship(back_populates="study")


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"))
    name: Mapped[str] = mapped_column(String(255), default="")
    state: Mapped[str] = mapped_column(String(32), default="active")
    owner_label: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    study: Mapped["StudyRow"] = relationship(back_populates="sessions")
    edits: Mapped[list["ParameterEditRow"]] = relationship(back_populates="session")
    snapshots: Mapped[list["DesignStateSnapshotRow"]] = relationship(
        back_populates="session"
    )


class DesignStateSnapshotRow(Base):
    __tablename__ = "design_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("sessions.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=0)
    state_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, index=True
    )
    # Phase 5B additive columns (nullable / with defaults so create_all picks
    # them up without migration on SQLite; Postgres users should run the
    # short migration note in docs).
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    label: Mapped[str] = mapped_column(String(32), default="auto")
    parent_snapshot_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags_json: Mapped[list] = mapped_column(JSON, default=list)

    session: Mapped["SessionRow"] = relationship(back_populates="snapshots")


class ParameterEditRow(Base):
    __tablename__ = "parameter_edits"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("sessions.id"), index=True
    )
    position_id: Mapped[str] = mapped_column(String(64))
    param_path: Mapped[str] = mapped_column(String(255), index=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32))
    actor_label: Mapped[str] = mapped_column(String(100), default="")
    edit_type: Mapped[str] = mapped_column(String(32), default="override")
    equipment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, index=True
    )

    session: Mapped["SessionRow"] = relationship(back_populates="edits")


class OptimizationRunRow(Base):
    """Phase 5B — one optimiser run."""

    __tablename__ = "optimization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    study_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    algo: Mapped[str] = mapped_column(String(32), default="differential_evolution")
    objective: Mapped[str] = mapped_column(String(64))  # min_mass / min_cost / max_link_margin
    design_variables_json: Mapped[list] = mapped_column(JSON, default=list)
    constraints_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending / running / done / failed
    num_evals: Mapped[int] = mapped_column(Integer, default=0)
    best_x_json: Mapped[dict] = mapped_column(JSON, default=dict)
    best_y: Mapped[float | None] = mapped_column(nullable=True)
    pareto_front_json: Mapped[list] = mapped_column(JSON, default=list)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ExportRow(Base):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("sessions.id"))
    kind: Mapped[str] = mapped_column(String(32))
    path: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
