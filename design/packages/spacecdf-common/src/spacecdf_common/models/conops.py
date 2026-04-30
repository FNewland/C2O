"""SpaceCDF — Concept of Operations (ConOps) structured model.

Replaces the single conops_summary text field with a structured model
that captures mission phases, operational modes, ground segment
architecture, and data flow. Each operational mode carries resource
profiles (power, thermal, data, pointing) that drive multi-mode
subsystem sizing.

Aligned with:
  - NASA SEH Appendix S: ConOps Annotated Outline
  - ECSS-E-ST-70C: Ground systems and operations
  - NASA SEH §4.1: Stakeholder Expectations Definition
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Operational Mode
# ---------------------------------------------------------------------------

class ModeType(str, Enum):
    """Standard spacecraft operational modes."""
    LAUNCH = "launch"
    SAFE = "safe"
    COMMISSIONING = "commissioning"
    NOMINAL_SCIENCE = "nominal_science"
    DOWNLINK = "downlink"
    SLEW = "slew"
    ECLIPSE = "eclipse"
    ORBIT_MAINTENANCE = "orbit_maintenance"
    DEORBIT = "deorbit"
    STANDBY = "standby"
    PEAK_SCIENCE = "peak_science"
    CALIBRATION = "calibration"
    CUSTOM = "custom"


class OperationalMode(BaseModel):
    """A spacecraft operational mode with resource profiles.

    The set of modes drives multi-mode sizing: battery is sized for
    worst-case eclipse mode, SA for worst-case sunlight mode, thermal
    for hot/cold case modes, data storage for gap between generation
    and downlink.
    """
    id: str = ""
    name: str = ""
    mode_type: ModeType = ModeType.NOMINAL_SCIENCE
    description: str = ""

    # Resource profiles for this mode
    power_w: float = Field(default=0.0, description="Total power consumption in this mode")
    payload_active: bool = Field(default=False, description="Is the payload operating?")
    payload_power_w: float = 0.0
    platform_power_w: float = 0.0
    heater_power_w: float = 0.0

    # Thermal profile
    internal_dissipation_w: float = 0.0
    sun_illuminated: bool = True

    # Data profile
    data_rate_mbps: float = 0.0
    data_generation_gb_per_hour: float = 0.0
    data_downlink_active: bool = False

    # Pointing profile
    pointing_requirement_deg: float = Field(default=5.0, description="Pointing accuracy needed in this mode")
    slew_rate_deg_s: float = 0.0
    nadir_pointing: bool = True

    # Timing
    duty_cycle_percent: float = Field(default=100.0, description="Fraction of orbit spent in this mode")
    typical_duration_s: float = 0.0
    occurs_per_orbit: float = Field(default=1.0, description="How many times per orbit this mode occurs")

    # Constraints
    is_critical: bool = Field(default=False, description="Failure in this mode = mission loss")
    requires_ground_contact: bool = False
    autonomous: bool = True


# ---------------------------------------------------------------------------
# Mission Phase
# ---------------------------------------------------------------------------

class MissionPhaseType(str, Enum):
    LEOP = "leop"                    # Launch and Early Orbit Phase
    COMMISSIONING = "commissioning"
    TRANSFER = "transfer"            # Orbit transfer / cruise
    NOMINAL = "nominal"              # Primary mission operations
    EXTENDED = "extended"            # Extended mission
    DISPOSAL = "disposal"            # End-of-life / deorbit


class MissionPhase(BaseModel):
    """A phase of the mission life cycle with associated modes."""
    id: str = ""
    name: str = ""
    phase_type: MissionPhaseType = MissionPhaseType.NOMINAL
    description: str = ""
    duration_days: float = 0.0
    modes: list[str] = Field(default_factory=list, description="Mode IDs active during this phase")
    primary_mode: str = Field(default="", description="The dominant mode during this phase")
    entry_criteria: str = ""
    exit_criteria: str = ""


# ---------------------------------------------------------------------------
# Ground Segment
# ---------------------------------------------------------------------------

class GroundStationType(str, Enum):
    DEDICATED = "dedicated"           # Owned / reserved ground station
    COMMERCIAL = "commercial"         # KSAT, AWS, Leaf Space
    DSN = "dsn"                       # NASA Deep Space Network
    ESTRACK = "estrack"               # ESA tracking network
    UNIVERSITY = "university"
    AMATEUR = "amateur"


class GroundStation(BaseModel):
    """A ground station in the mission ground segment."""
    name: str = ""
    type: GroundStationType = GroundStationType.COMMERCIAL
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    antenna_diameter_m: float = 13.0
    frequency_bands: list[str] = Field(default_factory=lambda: ["S", "X"])
    contact_time_per_day_min: float = 0.0
    cost_per_pass_eur: float = 0.0


class DataPipelineStep(BaseModel):
    """A step in the data processing pipeline from instrument to end user."""
    name: str = ""
    location: str = Field(default="ground", description="onboard / ground / cloud")
    description: str = ""
    latency: str = Field(default="", description="e.g. 'near-real-time', '< 3 hours', '< 24 hours'")
    output_format: str = ""
    data_level: str = Field(default="", description="L0 / L1A / L1B / L2 / L3")


# ---------------------------------------------------------------------------
# Full ConOps
# ---------------------------------------------------------------------------

class ConceptOfOperations(BaseModel):
    """Structured Concept of Operations per NASA SEH Appendix S.

    Captures HOW the mission will be operated — mission phases,
    spacecraft modes, ground segment, data flow, and operator roles.
    Each element feeds directly into subsystem sizing.
    """
    # Mission timeline
    phases: list[MissionPhase] = Field(default_factory=list)

    # Spacecraft modes (referenced by phases)
    modes: list[OperationalMode] = Field(default_factory=list)

    # Ground segment
    ground_stations: list[GroundStation] = Field(default_factory=list)
    mission_control_centre: str = ""
    ground_segment_description: str = ""

    # Data pipeline
    data_pipeline: list[DataPipelineStep] = Field(default_factory=list)
    data_distribution_policy: str = Field(default="", description="Open data? Licensed? Latency SLA?")

    # Operator roles
    operator_roles: list[str] = Field(default_factory=list,
        description="e.g. Flight Director, Spacecraft Controller, Payload Operator, Ground Segment Operator")
    operations_concept: str = Field(default="", description="Shift pattern, autonomy level, on-call vs 24/7")

    # Autonomy
    autonomy_level: str = Field(default="ground_controlled",
        description="ground_controlled / supervised_autonomy / full_autonomy")
    onboard_decision_making: list[str] = Field(default_factory=list,
        description="What decisions does the spacecraft make autonomously?")

    # Summary (the old text field, kept for backward compatibility)
    summary: str = ""

    def get_mode(self, mode_id: str) -> OperationalMode | None:
        for m in self.modes:
            if m.id == mode_id:
                return m
        return None

    @property
    def worst_case_power_mode(self) -> OperationalMode | None:
        """Mode with highest total power demand — drives SA sizing."""
        if not self.modes:
            return None
        return max(self.modes, key=lambda m: m.power_w)

    @property
    def worst_case_eclipse_mode(self) -> OperationalMode | None:
        """Mode with highest power during eclipse — drives battery sizing."""
        eclipse_modes = [m for m in self.modes if not m.sun_illuminated or m.mode_type == ModeType.ECLIPSE]
        if not eclipse_modes:
            # Use safe mode as proxy (always survives eclipse)
            safe = [m for m in self.modes if m.mode_type == ModeType.SAFE]
            return safe[0] if safe else None
        return max(eclipse_modes, key=lambda m: m.power_w)

    @property
    def peak_data_mode(self) -> OperationalMode | None:
        """Mode with highest data generation — drives storage sizing."""
        if not self.modes:
            return None
        return max(self.modes, key=lambda m: m.data_rate_mbps)

    @property
    def tightest_pointing_mode(self) -> OperationalMode | None:
        """Mode with tightest pointing requirement — drives AOCS sizing."""
        pointing_modes = [m for m in self.modes if m.pointing_requirement_deg > 0]
        if not pointing_modes:
            return None
        return min(pointing_modes, key=lambda m: m.pointing_requirement_deg)
