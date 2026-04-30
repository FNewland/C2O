"""SpaceCDF — Study, Mission, and Spacecraft data models.

Defines the hierarchy: Study → Mission → SpaceSegment → Spacecraft → Subsystem.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .mission_need import MissionNeed


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
    data_volume_per_day_gb: float = 10.0
    pointing_accuracy_deg: float = 0.1
    pointing_stability_deg_s: float = 0.01
    temperature_range_c: list[float] = Field(default_factory=lambda: [-20.0, 40.0])
    fov_deg: float = 5.0
    duty_cycle_percent: float = 25.0
    description: str = ""


class MissionRequirements(BaseModel):
    """Top-level mission requirements that drive the design."""

    name: str = "New Mission"
    mission_type: MissionType = MissionType.EARTH_OBSERVATION
    orbit: OrbitRequirements = Field(default_factory=OrbitRequirements)
    payloads: list[PayloadRequirements] = Field(default_factory=lambda: [PayloadRequirements()])
    design_lifetime_years: float = 3.0
    reliability_target: float = 0.9
    target_cost_meur: float | None = None
    target_mass_kg: float | None = None
    spacecraft_class: str = Field(default="small", description="nano/micro/small/medium/large/flagship")
    num_spacecraft: int = 1
    launch_date_target: str | None = None
    ground_stations: list[str] = Field(default_factory=lambda: ["KSAT Svalbard"])
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
    requirements: MissionRequirements = Field(default_factory=MissionRequirements)
    spacecraft: SpacecraftDesign = Field(default_factory=SpacecraftDesign)
    iterations: list[DesignIteration] = Field(default_factory=list)
    team: list[str] = Field(default_factory=list)
    notes: str = ""
