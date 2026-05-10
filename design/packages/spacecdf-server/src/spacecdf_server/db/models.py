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
    study_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("studies.id"), nullable=True, index=True
    )  # SCDF-141: index for study-level snapshot queries
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
    # SCDF-141: FK to the last change_event that produced this snapshot
    last_change_event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("change_events.id"), nullable=True, index=True
    )

    session: Mapped["SessionRow"] = relationship(back_populates="snapshots")
    last_change_event: Mapped["ChangeEventRow | None"] = relationship(
        foreign_keys=[last_change_event_id]
    )


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


# SCDF-110: New tables for reactive spine
class ChangeEventRow(Base):
    """Typed envelope for all design mutations (SPINE_SPEC §2.4)."""
    __tablename__ = "change_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("sessions.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64))  # ChangeKind enum value
    actor_id: Mapped[str] = mapped_column(String(64))
    actor_label: Mapped[str] = mapped_column(String(100), default="")
    target_id: Mapped[str] = mapped_column(String(255), index=True)
    target_kind: Mapped[str] = mapped_column(String(32))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, default="")
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)


class RequirementRow(Base):
    """Requirement hierarchy (SPINE_SPEC §6.1)."""
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("requirements.id"), nullable=True, index=True)
    level: Mapped[str] = mapped_column(String(16))  # mission / system / subsystem
    code: Mapped[str] = mapped_column(String(32))  # e.g. "MR-001", "SR-PWR-002"
    text: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    threshold_param_path: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    threshold_op: Mapped[str | None] = mapped_column(String(16), nullable=True)  # <= >= == in_range exists
    threshold_value: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded
    verification_method: Mapped[str | None] = mapped_column(String(8), nullable=True)  # A T I R D
    verification_phase: Mapped[str | None] = mapped_column(String(8), nullable=True)  # PDR CDR QR AR
    responsible_position: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft approved violated verified retired
    derived_from_requirement_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    study: Mapped["StudyRow"] = relationship(foreign_keys=[study_id])
    parent: Mapped["RequirementRow | None"] = relationship(
        remote_side="RequirementRow.id", foreign_keys=[parent_id]
    )


class OptimizationRunRow(Base):
    """Phase 5B — one optimiser run."""

    __tablename__ = "optimization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    study_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    # SCDF-141: FK to the initial snapshot for this optimization run
    initial_snapshot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("design_states.id"), nullable=True, index=True
    )
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

    initial_snapshot: Mapped["DesignStateSnapshotRow | None"] = relationship(
        foreign_keys=[initial_snapshot_id]
    )  # SCDF-141


class ExportRow(Base):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("sessions.id"))
    kind: Mapped[str] = mapped_column(String(32))
    path: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ═══════════════════════════════════════════════════════════════════════
# MODEL-CENTRIC DESIGN ELEMENTS (new architecture — 2026-05-06)
# Every block in a diagram is a rich object carrying mass, power, cost,
# interfaces, size, work packages, risks. Views are projections.
# ═══════════════════════════════════════════════════════════════════════

class DesignElementRow(Base):
    """Core entity: any physical, logical, or operational item in the design."""
    __tablename__ = "design_elements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("design_elements.id"), nullable=True, index=True)

    # Identity
    name: Mapped[str] = mapped_column(String(255))
    element_type: Mapped[str] = mapped_column(String(32), index=True)
    # element_type values: mission, segment, system, subsystem, component, software, mode, logical
    subsystem_domain: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    # subsystem_domain values: power, aocs, ttc, thermal, structure, propulsion, obc, payload, ground
    description: Mapped[str] = mapped_column(Text, default="")
    segment: Mapped[str] = mapped_column(String(16), default="space")
    # segment values: space, ground, operations

    # Physical properties
    mass_kg: Mapped[float | None] = mapped_column(nullable=True)
    power_avg_w: Mapped[float | None] = mapped_column(nullable=True)
    power_peak_w: Mapped[float | None] = mapped_column(nullable=True)
    volume_cm3: Mapped[float | None] = mapped_column(nullable=True)
    dimensions_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Financial
    cost_nre_keur: Mapped[float | None] = mapped_column(nullable=True)
    cost_recurring_keur: Mapped[float | None] = mapped_column(nullable=True)
    work_package_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Maturity & provenance
    trl: Mapped[int | None] = mapped_column(nullable=True)
    heritage_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    part_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    kb_component_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Quantity & redundancy
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    redundancy_type: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Domain-specific performance (flexible JSON)
    performance_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Budget & margins
    margin_percent: Mapped[float] = mapped_column(default=20.0)
    verification_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Ownership in concurrent design
    owner_position: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Scope & freeze flags
    in_scope: Mapped[bool] = mapped_column(default=True)
    frozen: Mapped[bool] = mapped_column(default=False)

    # Diagram layout (for @xyflow/react persistence)
    diagram_x: Mapped[float | None] = mapped_column(nullable=True)
    diagram_y: Mapped[float | None] = mapped_column(nullable=True)
    diagram_collapsed: Mapped[bool] = mapped_column(default=False)

    # Optimistic locking
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ElementInterfaceRow(Base):
    """Typed connection between two design elements."""
    __tablename__ = "element_interfaces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)

    name: Mapped[str] = mapped_column(String(255), default="")
    interface_type: Mapped[str] = mapped_column(String(32))
    # interface_type values: electrical, data, rf, mechanical, thermal, optical
    direction: Mapped[str] = mapped_column(String(16), default="bidirectional")

    from_element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)
    to_element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)

    # Type-specific properties (voltage, current, data rate, frequency, connector, protocol)
    properties_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="defined")
    criticality: Mapped[str] = mapped_column(String(16), default="standard")
    diagram_label: Mapped[str] = mapped_column(String(128), default="")

    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ModeElementRow(Base):
    """Which elements are active in each operational mode, with power/duty overrides."""
    __tablename__ = "mode_elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)
    element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)

    is_active: Mapped[bool] = mapped_column(default=True)
    power_w_in_mode: Mapped[float | None] = mapped_column(nullable=True)
    duty_cycle_percent: Mapped[float] = mapped_column(default=100.0)
    notes: Mapped[str] = mapped_column(Text, default="")


class BudgetAllocationRow(Base):
    """Budget envelope/bucket allocation at each level of the hierarchy."""
    __tablename__ = "budget_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)

    budget_type: Mapped[str] = mapped_column(String(32))
    # budget_type values: mass, power, cost, data, delta_v, volume
    allocation_value: Mapped[float] = mapped_column()
    unit: Mapped[str] = mapped_column(String(16), default="")
    source: Mapped[str] = mapped_column(String(64), default="manual")
    # source values: requirement, derived, manual
    rationale: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ElementBaselineRow(Base):
    """Frozen snapshot of an element at a review gate (SRR, PDR, CDR)."""
    __tablename__ = "element_baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    baseline_name: Mapped[str] = mapped_column(String(128))
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"))

    snapshot_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
