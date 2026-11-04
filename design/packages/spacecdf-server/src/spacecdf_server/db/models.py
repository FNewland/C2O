"""SQLAlchemy ORM models for SpaceCDF persistence."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
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
    element_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("design_elements.id"), nullable=True, index=True
    )
    derived_from_requirement_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # SCDF-160: objective trace (MissionNeed.objectives[].id) — read by the traceability tree
    objective_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # SCDF-160 §1.4: identity in external tools (Capella Requirements VP / ReqIF)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    external_ids_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Interface requirement (level "interface", design rules IF-01..IF-05):
    # {origin, template_id, interface_id, inputs_hash, review, edited, proposed_text, values, endpoints}
    ir_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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
    # SCDF-160 §1.3: Arcadia layer. 'PA' for physical items, 'LA' where
    # element_type='logical'. Realizations (RealizationRow) link LA<->PA.
    layer: Mapped[str] = mapped_column(String(4), default="PA")

    # Physical properties
    mass_kg: Mapped[float | None] = mapped_column(nullable=True)
    power_avg_w: Mapped[float | None] = mapped_column(nullable=True)
    power_peak_w: Mapped[float | None] = mapped_column(nullable=True)
    volume_cm3: Mapped[float | None] = mapped_column(nullable=True)
    dimensions_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    position_json: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [x,y,z] m, body frame (SCDF-176)
    # Nov 2026 (F4): the KB facts copied on selection (services/kb_copy.kb_element_fields):
    # category, form_factor, interfaces, operating_temp_c, dimensions_mm, kb_hash, stale flag.
    kb_spec_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

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
    # interface_type: canonical values of spacecdf_common.models.interface_types.InterfaceType
    # (power, data, rf, mechanical, thermal, timing, optical, fluid, electrical_signal);
    # old spellings (electrical, propulsion, ...) are migrated at start-up (db/migrate.py).
    subtype: Mapped[str | None] = mapped_column(String(32), nullable=True)
    direction: Mapped[str] = mapped_column(String(16), default="bidirectional")
    # Provenance (Nov 2026): "user" | "import" | "rule:<rule_id>" (interface_rules.yaml)
    origin: Mapped[str] = mapped_column(String(64), default="user")
    # {"en": ..., "fr": ...} — why the rule proposed this link
    rationale_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    standard_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    from_element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)
    to_element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)

    # Type-specific properties (voltage, current, data rate, frequency, connector, protocol)
    properties_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # SCDF-160 §1.2: list of exchange_items.id flowing over this interface
    exchange_item_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # "suggested" (rule baseline, not yet reviewed) | "accepted" | "rejected"
    # (rejected links are kept so the proposer never re-proposes them).
    status: Mapped[str] = mapped_column(String(32), default="accepted")
    criticality: Mapped[str] = mapped_column(String(16), default="standard")
    diagram_label: Mapped[str] = mapped_column(String(128), default="")
    # Bilateral agreement (design rules IF-05): {provider_seat, consumer_seat,
    # provider: {by, seat, at} | None, consumer: {...} | None, inputs_hash}
    agreement_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

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
    # Nov 2026 mode model (D7, rules MO-01 / EB-02 / EB-03 / EB-05; services/mode_model.py)
    power_state: Mapped[str | None] = mapped_column(String(16), nullable=True)    # off|standby|nominal|peak
    data_rate_bps: Mapped[float | None] = mapped_column(nullable=True)            # data produced in the mode
    dissipation_w: Mapped[float | None] = mapped_column(nullable=True)            # override; None = derived
    origin: Mapped[str] = mapped_column(String(48), default="user")               # user | rule:MO-01
    status: Mapped[str] = mapped_column(String(16), default="accepted")           # suggested|accepted|edited|rejected|stale
    source_ref: Mapped[str] = mapped_column(String(255), default="")              # KB power_modes_w | C2O default ...
    inputs_hash: Mapped[str] = mapped_column(String(32), default="")


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


# ═══════════════════════════════════════════════════════════════════════
# SCDF-160 ARCADIA SPINE (design: docs/_review/designs/SCDF-160-arcadia-spine.md)
# Functions, ports, allocations, functional exchanges, realizations,
# exchange items, typed requirement relations, typed parameters.
# ═══════════════════════════════════════════════════════════════════════

class FunctionRow(Base):
    """Persisted, allocatable function (Arcadia `fa`). §1.1"""
    __tablename__ = "functions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    parent_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("functions.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    layer: Mapped[str] = mapped_column(String(4), default="SA", index=True)  # OA|SA|LA|PA
    function_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0)
    is_leaf: Mapped[bool] = mapped_column(Boolean, default=False)
    position_responsible: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    external_ids_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class FunctionPortRow(Base):
    """Input/output port of a function. §1.1"""
    __tablename__ = "function_ports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    function_id: Mapped[str] = mapped_column(String(64), ForeignKey("functions.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    direction: Mapped[str] = mapped_column(String(4), default="out")  # in|out
    exchange_item_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class FunctionAllocationRow(Base):
    """Function -> element allocation, unique per (function, layer). §1.1"""
    __tablename__ = "function_allocations"
    __table_args__ = (
        UniqueConstraint("function_id", "layer", name="uq_function_allocation_function_layer"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    function_id: Mapped[str] = mapped_column(String(64), ForeignKey("functions.id"), index=True)
    element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)
    layer: Mapped[str] = mapped_column(String(4), default="SA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class FunctionalExchangeRow(Base):
    """Flow between two function ports, optionally realised by an element interface. §1.1"""
    __tablename__ = "functional_exchanges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    from_port_id: Mapped[str] = mapped_column(String(64), ForeignKey("function_ports.id"), index=True)
    to_port_id: Mapped[str] = mapped_column(String(64), ForeignKey("function_ports.id"), index=True)
    exchange_item_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    realized_by_interface_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("element_interfaces.id"), nullable=True, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class RealizationRow(Base):
    """Cross-layer realization link (SA->LA->PA functions, LA->PA elements). §1.1"""
    __tablename__ = "realizations"
    __table_args__ = (
        UniqueConstraint(
            "source_kind", "source_id", "target_kind", "target_id",
            name="uq_realization_source_target",
        ),
        Index("ix_realizations_source", "source_kind", "source_id"),
        Index("ix_realizations_target", "target_kind", "target_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    source_kind: Mapped[str] = mapped_column(String(16))  # function|element
    source_id: Mapped[str] = mapped_column(String(64))
    target_kind: Mapped[str] = mapped_column(String(16))
    target_id: Mapped[str] = mapped_column(String(64))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ExchangeItemRow(Base):
    """What flows over an interface (Arcadia `information` -> ICD line). §1.2"""
    __tablename__ = "exchange_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(16), default="data", index=True)
    # kind values: data, power, rf, thermal, mechanical, optical, fluid
    properties_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    external_ids_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class RequirementRelationRow(Base):
    """Typed relation (Capella Requirements VP / ReqIF SPEC-RELATION). §1.4"""
    __tablename__ = "requirement_relations"
    __table_args__ = (
        UniqueConstraint(
            "kind", "source_kind", "source_id", "target_kind", "target_id",
            name="uq_requirement_relation",
        ),
        Index("ix_requirement_relations_source", "source_kind", "source_id"),
        Index("ix_requirement_relations_target", "target_kind", "target_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)
    # kind values: satisfies, verifies, refines, derives, traces, allocates
    source_kind: Mapped[str] = mapped_column(String(16))
    # source/target kind values: requirement, element, function, interface, parameter, test
    source_id: Mapped[str] = mapped_column(String(64))
    target_kind: Mapped[str] = mapped_column(String(16))
    target_id: Mapped[str] = mapped_column(String(64))
    rationale: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ParameterDefinitionRow(Base):
    """Global parameter definition (10-25 ParameterType + quantity kind + unit). §1.5"""
    __tablename__ = "parameter_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    quantity_kind: Mapped[str] = mapped_column(String(32), default="")
    unit: Mapped[str] = mapped_column(String(16), default="")
    scale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    is_well_known: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ElementParameterRow(Base):
    """Typed parameter value on an element (10-25 ParameterValueSet). §1.5"""
    __tablename__ = "element_parameters"
    __table_args__ = (
        UniqueConstraint(
            "element_id", "definition_id", "iteration",
            name="uq_element_parameter_element_definition_iteration",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    element_id: Mapped[str] = mapped_column(String(64), ForeignKey("design_elements.id"), index=True)
    definition_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("parameter_definitions.id"), index=True
    )
    owner_domain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    manual_value: Mapped[float | None] = mapped_column(nullable=True)
    computed_value: Mapped[float | None] = mapped_column(nullable=True)
    reference_value: Mapped[float | None] = mapped_column(nullable=True)
    value_switch: Mapped[str] = mapped_column(String(16), default="computed")  # manual|computed|reference
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    formula_kind: Mapped[str | None] = mapped_column(String(8), nullable=True)  # ref|calc|None
    option_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, default=1)
    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# ── SCDF-170 §1.2: analysis runs + conflicts ──────────────────────────

class AnalysisRunRow(Base):
    """One execution of an engineering analysis (design loop, simulation, ...).

    ``inputs_hash`` is ``analysis_context.context_hash`` over the context
    subset the analysis declares it reads; the API reports the run as *stale*
    when it no longer matches the live context. ``series_ref`` points at the
    JSON file under ``<SPACECDF_DATA_DIR>/analysis/<run_id>.json`` that holds
    the bulky time-series / full parameter set; ``summary_json`` is the small
    part the UI shows on the card.
    """
    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("ix_analysis_runs_study_analysis", "study_id", "analysis"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    option_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    analysis: Mapped[str] = mapped_column(String(64), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="running")  # running|ok|failed
    inputs_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    series_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AnalysisConflictRow(Base):
    """A conflict raised by an analysis run (SCDF-170 §1.2).

    Unresolved conflicts of the same (study, option, analysis) are replaced on
    every publish; resolved ones are kept for history (``resolved_at`` set).
    """
    __tablename__ = "analysis_conflicts"
    __table_args__ = (
        Index("ix_analysis_conflicts_study_analysis", "study_id", "analysis"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    option_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    analysis: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="major")  # critical|major|minor|warning|info
    code: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    element_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    requirement_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OptionRow(Base):
    """Design option / variant (ECSS-E-TM-10-25 Option). Parameter overrides may be option-scoped (SCDF-172)."""
    __tablename__ = "options"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    is_baseline: Mapped[bool] = mapped_column(default=False)
    branched_from_option_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class VerificationItemRow(Base):
    """Per-requirement verification planning item (SCDF-175, ECSS-E-ST-10-02C)."""
    __tablename__ = "verification_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), ForeignKey("studies.id"), index=True)
    requirement_id: Mapped[str] = mapped_column(String(32), index=True)
    method: Mapped[str | None] = mapped_column(String(8), nullable=True)      # A T I R D
    level: Mapped[str | None] = mapped_column(String(16), nullable=True)      # unit subsystem system segment
    phase: Mapped[str | None] = mapped_column(String(8), nullable=True)       # PDR CDR QR AR
    facility: Mapped[str | None] = mapped_column(String(128), nullable=True)
    procedure_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acceptance_criterion: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="planned")        # planned in_progress passed failed waived
    evidence_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    edited_by_user: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class GateBaselineRow(Base):
    """Baseline snapshot saved when a review gate passes (WP6, Nov 2026).

    One row per pass: the study's mission need and requirements model, its element
    tree, interfaces, requirements, risk register, the gate evaluation and the products
    the gate baselines (configs/gate_profiles.yaml) — frozen as JSON.
    """

    __tablename__ = "gate_baselines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    gate: Mapped[str] = mapped_column(String(32))
    profile: Mapped[str] = mapped_column(String(32), default="")
    created_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)


# ─── SpaceCDF seats (redesign WP9, Nov 2026) ───────────────────────────────────

class StudyTeamRow(Base):
    """A study's seats: preset, holdings, locks, freeze, timer, messages, sign-offs and
    subscriptions as one JSON document (small; changes on claims, not on edits).
    ``study_id = "__class__"`` holds the class-wide state (broadcasts, laptop instructor)."""

    __tablename__ = "study_teams"

    study_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class SeatEventRow(Base):
    """Audit and assessment trail: every claim, handover, edit, proposal, review and
    instructor intervention, with the person AND the seat (append-only)."""

    __tablename__ = "seat_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    seat_id: Mapped[str] = mapped_column(String(40), default="")
    person_id: Mapped[str] = mapped_column(String(255), default="")
    person_name: Mapped[str] = mapped_column(String(255), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    action: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(String(255), default="")
    detail_json: Mapped[dict] = mapped_column(JSON, default=dict)


class PendingChangeRow(Base):
    """An edit of a parameter owned by another seat, waiting for the owning seat
    (REDESIGN_DECISIONS.md ruling 5). Until accepted the owner's value stands."""

    __tablename__ = "pending_changes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(32), index=True)
    owner_seat: Mapped[str] = mapped_column(String(40), index=True)
    kind: Mapped[str] = mapped_column(String(32))            # element_fields | element_param | element_param_delete
    element_id: Mapped[str] = mapped_column(String(64), default="")
    element_name: Mapped[str] = mapped_column(String(255), default="")
    param_keys: Mapped[list] = mapped_column(JSON, default=list)
    old_json: Mapped[dict] = mapped_column(JSON, default=dict)
    new_json: Mapped[dict] = mapped_column(JSON, default=dict)
    option_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    by_person: Mapped[str] = mapped_column(String(255), default="")
    by_name: Mapped[str] = mapped_column(String(255), default="")
    by_seat: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(16), default="pending")   # pending accepted rejected withdrawn
    reviewed_by: Mapped[str] = mapped_column(String(255), default="")
    reviewed_name: Mapped[str] = mapped_column(String(255), default="")
    reviewed_seat: Mapped[str] = mapped_column(String(40), default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    comment: Mapped[str] = mapped_column(Text, default="")


class StackLayoutRow(Base):
    """The CubeSat stack layout of a study (design rules §4, D9; routers/stack.py).

    ``approved_json`` is the layout the Structures seat approved (its positions are in
    every element's ``position_json``); ``proposal_json`` an open proposal (auto-placement
    ``rule:STACK-AUTO`` or a user edit) waiting for Structures (ruling 5). Each holds a
    layout spec (columns, layers, faces, locks) plus who/when; placements are derived."""

    __tablename__ = "stack_layouts"

    study_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    form_factor: Mapped[str] = mapped_column(String(16), default="")
    approved_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    proposal_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# Nov 2026 mode model tables (mode transitions, rule proposals, heaters) live in their own
# module; importing it here registers them on ``Base.metadata`` for create_all.
from . import models_modes  # noqa: E402,F401

# Electrical and data-handling tables (power rails, lines, buses, nodes, ports) live in their
# own module; importing it registers them on Base.metadata for create_all.
from . import electrical_models as _electrical_models  # noqa: E402,F401

# CDR design model (TM/TC database, FDIR, AOCS modes, TT&C ladder, line states, operations):
# one generic table, registered on Base.metadata for create_all.
from . import cdr_models as _cdr_models  # noqa: E402,F401
