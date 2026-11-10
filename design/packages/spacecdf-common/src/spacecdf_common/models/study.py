"""SpaceCDF — Study, Mission, and Spacecraft data models.

Defines the hierarchy: Study → Mission → SpaceSegment → Spacecraft → Subsystem.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .mission_need import MissionNeed
from .conops import ConceptOfOperations
from .functions import FunctionalDecomposition
from .interfaces import InterfaceMatrix
from .conflicts import DecisionRecord


class StudyPhase(str, Enum):
    PHASE_0 = "phase_0"       # Mission analysis / feasibility
    PHASE_A = "phase_a"       # Feasibility / concept
    PHASE_B1 = "phase_b1"     # Preliminary definition


class MissionType(str, Enum):
    EARTH_OBSERVATION = "earth_observation"
    COMMUNICATIONS = "communications"
    NAVIGATION = "navigation"
    SCIENCE_PLANETARY = "science_planetary"
    SCIENCE_HELIOPHYSICS = "science_heliophysics"
    SCIENCE_ASTROPHYSICS = "science_astrophysics"
    TECHNOLOGY_DEMO = "technology_demo"
    HUMAN_SPACEFLIGHT = "human_spaceflight"
    LUNAR = "lunar"
    MARS = "mars"
    DEEP_SPACE = "deep_space"


class OrbitType(str, Enum):
    LEO = "leo"
    SSO = "sso"
    MEO = "meo"
    GEO = "geo"
    GTO = "gto"
    HEO = "heo"
    LUNAR = "lunar"
    INTERPLANETARY = "interplanetary"
    LAGRANGE = "lagrange"


class OrbitRequirements(BaseModel):
    """Orbit definition for the mission."""

    orbit_type: OrbitType = OrbitType.SSO
    altitude_km: float = 500.0
    inclination_deg: float = 97.4
    eccentricity: float = 0.0
    raan_deg: float | None = None
    ltan: str | None = Field(default=None, description="Local Time of Ascending Node, e.g. '10:30'")
    repeat_cycle_days: int | None = None
    delta_v_insertion_ms: float = 0.0
    delta_v_maintenance_ms: float = 0.0
    mission_duration_years: float = 3.0
    deorbit_required: bool = True


class PayloadRequirements(BaseModel):
    """Science/payload instrument requirements."""

    name: str = "Payload"
    type: str = Field(default="optical_imager", description="Instrument type category")
    mass_kg: float = 5.0
    power_w: float = 30.0
    power_peak_w: float = 50.0
    data_rate_mbps: float = 100.0
    data_volume_per_day_gb: float = 0.0  # 0 = compute from data_rate_mbps × duty_cycle
    pointing_accuracy_deg: float = 0.1
    pointing_stability_deg_s: float = 0.01
    temperature_range_c: list[float] = Field(default_factory=lambda: [-20.0, 40.0])
    fov_deg: float = 5.0
    duty_cycle_percent: float = 25.0
    description: str = ""
    # Nov 2026 (mission definition editor): imaging parameters a team states up front.
    # Optional: None / [] = not stated (analyses fall back to their defaults).
    gsd_m: float | None = Field(default=None, description="Ground sample distance at nadir (m)")
    swath_km: float | None = Field(default=None, description="Swath width at nadir (km)")
    wavelengths_nm: list[float] = Field(default_factory=list, description="Band centre wavelengths (nm)")
    data_per_image_mb: float | None = Field(default=None, description="Data volume of one acquisition (MB)")


class LinkRequirements(BaseModel):
    """Communication link chosen for the mission (Nov 2026).

    Written by the mission definition editor and by the link-budget tool's "Apply to
    Design"; read by the design loop's link agent and the ground / mission-simulation
    closures in preference to their class defaults. Every field is optional.
    """

    band: str | None = Field(default=None, description="UHF, VHF, S, X, Ka ...")
    downlink_frequency_mhz: float | None = None
    uplink_frequency_mhz: float | None = None
    downlink_rate_bps: float | None = None
    uplink_rate_bps: float | None = None
    tx_power_w: float | None = None
    tx_antenna_gain_dbi: float | None = None
    tx_losses_db: float | None = None
    rx_antenna_gain_dbi: float | None = Field(default=None, description="Ground station antenna gain (downlink)")
    system_noise_temp_k: float | None = None
    slant_range_km: float | None = None
    required_ebn0_db: float | None = None
    margin_db: float | None = Field(default=None, description="Margin the link-budget tool computed")
    source: str | None = Field(default=None, description="mission_editor | link_budget_tool | ...")

    def is_set(self) -> bool:
        return any(v is not None for k, v in self.model_dump().items() if k not in ("source", "margin_db"))


class MissionRequirements(BaseModel):
    """Top-level mission requirements that drive the design."""

    name: str = "New Mission"
    mission_type: MissionType = MissionType.EARTH_OBSERVATION
    orbit: OrbitRequirements = Field(default_factory=OrbitRequirements)
    payloads: list[PayloadRequirements] = Field(default_factory=lambda: [PayloadRequirements()])
    design_lifetime_years: float = 3.0
    reliability_target: float = 0.9
    # wave 3 (3.A1): the mission-success horizon the reliability target applies to (months of
    # operations after commissioning, e.g. 12 for MIS-LIF-02), kept apart from the design life
    success_horizon_months: float | None = None
    target_cost_meur: float | None = None
    target_mass_kg: float | None = None
    spacecraft_class: str = Field(default="small", description="nano/micro/small/medium/large/flagship")
    num_spacecraft: int = 1
    launch_date_target: str | None = None
    ground_stations: list[str] = Field(default_factory=lambda: ["KSAT Svalbard"])
    # Nov 2026 (mission definition editor)
    link: LinkRequirements = Field(default_factory=LinkRequirements)
    launch_vehicle: str | None = Field(default=None, description="Launch / deployer choice, free text")
    disposal_method: str | None = Field(default=None, description="natural_decay | drag_sail | propulsive | ...")
    constraints: dict[str, Any] = Field(default_factory=dict, description="Additional mission-specific constraints")


class SubsystemDesign(BaseModel):
    """Design state for one spacecraft subsystem."""

    name: str
    domain: str
    mass_kg: float = 0.0
    mass_margin_percent: float = 20.0
    power_w: float = 0.0
    power_peak_w: float = 0.0
    cost_keur: float = 0.0
    trl: int = 9
    equipment: list[dict[str, Any]] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class SpacecraftDesign(BaseModel):
    """Complete spacecraft design state."""

    name: str = "SC-1"
    subsystems: dict[str, SubsystemDesign] = Field(default_factory=dict)
    dry_mass_kg: float = 0.0
    wet_mass_kg: float = 0.0
    total_power_w: float = 0.0
    total_cost_meur: float = 0.0


class DesignIteration(BaseModel):
    """Record of one convergence iteration."""

    iteration: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    max_parameter_delta: float = Field(description="Largest parameter change in this iteration")
    converged: bool = False
    budgets_closed: bool = False
    warnings: list[str] = Field(default_factory=list)
    parameter_snapshot: dict[str, float] = Field(default_factory=dict)


class Study(BaseModel):
    """Top-level study container — one CDF study session."""

    id: str = ""
    name: str = "New Study"
    phase: StudyPhase = StudyPhase.PHASE_0
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mission_need: MissionNeed = Field(default_factory=MissionNeed)
    conops: ConceptOfOperations = Field(default_factory=ConceptOfOperations)
    functional_decomposition: FunctionalDecomposition = Field(default_factory=FunctionalDecomposition)
    interface_matrix: InterfaceMatrix = Field(default_factory=InterfaceMatrix)
    decision_records: list[DecisionRecord] = Field(default_factory=list)
    requirements: MissionRequirements = Field(default_factory=MissionRequirements)
    spacecraft: SpacecraftDesign = Field(default_factory=SpacecraftDesign)
    iterations: list[DesignIteration] = Field(default_factory=list)
    team: list[str] = Field(default_factory=list)
    notes: str = ""
    # Nov 2026 (WP6): review gates. ``gate_profile`` is an id of configs/gate_profiles.yaml
    # (full_ecss, esa_iod, c2o_3gate, nasa); "" = the configured default. ``gate_states``:
    # profile gate id → {state, history[], baselines[]} (services/gate_reviews.py).
    gate_profile: str = ""
    gate_states: dict[str, dict[str, Any]] = Field(default_factory=dict)
    # Nov 2026 (WP0): team records that lived in each browser's localStorage, now per study.
    risk_register: list[dict[str, Any]] = Field(default_factory=list)
    trade_records: dict[str, dict[str, Any]] = Field(default_factory=dict)
    # Wave 3, step 0: the study's own margin choices on top of configs/margin_policy.yaml,
    # e.g. {"study_override": {"percent": 20, "through_gate": "pdr", "resources": ["mass", "power"],
    # "rationale": "..."}} (services/rollup.py applies it; the ladder is still quoted beside it).
    margin_policy: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _migrate_gate_names(cls, data: Any) -> Any:
        """Studies saved before Nov 2026 call the Phase 0 gate "MCR" (now MDR, ruling 3)."""
        if isinstance(data, dict) and isinstance(data.get("gate_states"), dict):
            states = dict(data["gate_states"])
            if "mcr" in states or "MCR" in states:
                old = states.pop("mcr", None) or states.pop("MCR", None)
                states.setdefault("mdr", old)
            for st in states.values():
                if isinstance(st, dict):
                    for h in st.get("history") or []:
                        if isinstance(h, dict) and str(h.get("gate", "")).lower() == "mcr":
                            h["gate"] = "mdr"
            data = {**data, "gate_states": states}
        return data
