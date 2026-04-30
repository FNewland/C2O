"""SpaceCDF — Interface requirements and subsystem interface matrix.

Implements NASA SEH Process 12 (Interface Management). This is the single
biggest source of real CDF conflicts — every subsystem boundary is a
potential interface problem.

Captures:
  - Interface requirements (mechanical, electrical, thermal, data)
  - Subsystem-to-subsystem interface matrix
  - Interface conflicts (e.g. SA mounting vs star tracker FOV)
  - External interfaces (launch vehicle, ground segment)

Aligned with:
  - NASA SEH §6.3: Interface Management
  - NASA SEH Appendix L: IRD Outline
  - ECSS-E-ST-10-24C Rev.1: Interface management
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InterfaceType(str, Enum):
    MECHANICAL = "mechanical"         # Mounting, alignment, deployment
    ELECTRICAL = "electrical"         # Power bus, grounding, harness
    THERMAL = "thermal"               # Heat paths, radiator/heater interfaces
    DATA = "data"                     # Data bus, telemetry, commands
    RF = "rf"                         # RF interference, antenna FOV
    OPTICAL = "optical"               # FOV blockage, stray light, contamination
    PROPULSION = "propulsion"         # Plume impingement, tank pressurisation
    SOFTWARE = "software"             # Command/data interfaces, mode transitions


class InterfaceStatus(str, Enum):
    IDENTIFIED = "identified"         # Known to exist
    DEFINED = "defined"               # Requirements written
    AGREED = "agreed"                 # Both sides agreed
    VERIFIED = "verified"             # Tested/analysed
    CONFLICT = "conflict"             # Active conflict


class InterfaceRequirement(BaseModel):
    """A specific requirement at a subsystem interface.

    e.g. "The EPS shall provide 28V ± 2V regulated power to the AOCS via
    connector J5" or "The SA panel shall not occlude the star tracker FOV
    by more than 5°."
    """
    id: str = ""
    text: str = ""
    interface_type: InterfaceType = InterfaceType.ELECTRICAL
    subsystem_a: str = Field(description="Provider / source subsystem")
    subsystem_b: str = Field(description="Consumer / sink subsystem")
    parameter_value: str = Field(default="", description="e.g. '28V ± 2V', '< 5° occultation'")
    status: InterfaceStatus = InterfaceStatus.IDENTIFIED
    owner: str = Field(default="", description="Position responsible for this interface")
    notes: str = ""
    conflict_with: str | None = Field(default=None, description="ID of conflicting interface requirement")


class SubsystemInterface(BaseModel):
    """An interface between two subsystems, potentially with multiple
    requirement types (mechanical + electrical + thermal).
    """
    subsystem_a: str
    subsystem_b: str
    interface_types: list[InterfaceType] = Field(default_factory=list)
    requirements: list[InterfaceRequirement] = Field(default_factory=list)
    status: InterfaceStatus = InterfaceStatus.IDENTIFIED
    description: str = ""
    criticality: str = Field(default="standard", description="critical / standard / non-critical")


class ExternalInterface(BaseModel):
    """An interface with an external system (launch vehicle, ground segment,
    other spacecraft, etc.)."""
    id: str = ""
    external_system: str = Field(description="e.g. 'Falcon 9 payload adapter', 'KSAT Svalbard', 'Copernicus data hub'")
    interface_types: list[InterfaceType] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list, description="Key interface requirements (text)")
    icd_reference: str = Field(default="", description="ICD document reference if available")
    status: InterfaceStatus = InterfaceStatus.IDENTIFIED


class InterfaceConflict(BaseModel):
    """A detected conflict at a subsystem interface.

    These are the spatial/thermal/electrical conflicts that parametric
    models can't detect — they require knowledge of physical layout,
    FOV geometry, thermal paths, and harness routing.
    """
    id: str = ""
    title: str = ""
    description: str = ""
    interface_type: InterfaceType = InterfaceType.MECHANICAL
    subsystem_a: str = ""
    subsystem_b: str = ""
    severity: str = Field(default="major", description="critical / major / minor")
    resolution: str = ""
    resolved: bool = False


# ---------------------------------------------------------------------------
# Interface Matrix
# ---------------------------------------------------------------------------

# Standard subsystem pairs that always have interfaces
_STANDARD_INTERFACES: list[dict[str, Any]] = [
    # EPS interfaces with everything
    {"a": "power", "b": "aocs", "types": ["electrical"], "desc": "Power bus to AOCS electronics + reaction wheels"},
    {"a": "power", "b": "link", "types": ["electrical"], "desc": "Power bus to TTC transponder + PA"},
    {"a": "power", "b": "thermal", "types": ["electrical", "thermal"], "desc": "Power bus to heaters; SA thermal coupling"},
    {"a": "power", "b": "data", "types": ["electrical"], "desc": "Power bus to OBC"},
    {"a": "power", "b": "payload", "types": ["electrical"], "desc": "Power bus to payload; peak power switching"},
    {"a": "power", "b": "propulsion", "types": ["electrical"], "desc": "Power bus to valve drivers / EP PPU"},
    # Structure interfaces
    {"a": "structure", "b": "power", "types": ["mechanical", "thermal"], "desc": "SA mounting; panel thermal path"},
    {"a": "structure", "b": "aocs", "types": ["mechanical"], "desc": "RW + ST mounting alignment; vibration isolation"},
    {"a": "structure", "b": "thermal", "types": ["mechanical", "thermal"], "desc": "Radiator mounting; heat pipe routing"},
    {"a": "structure", "b": "propulsion", "types": ["mechanical"], "desc": "Tank mounting; thrust vector alignment"},
    {"a": "structure", "b": "payload", "types": ["mechanical", "optical"], "desc": "Payload mounting; alignment stability; FOV clearance"},
    # Data bus
    {"a": "data", "b": "aocs", "types": ["data"], "desc": "Attitude data for payload pointing; mode commands"},
    {"a": "data", "b": "link", "types": ["data"], "desc": "Telemetry stream; telecommand routing"},
    {"a": "data", "b": "payload", "types": ["data"], "desc": "Science data acquisition; instrument commanding"},
    # Thermal
    {"a": "thermal", "b": "payload", "types": ["thermal"], "desc": "Payload thermal control; detector cooling"},
    {"a": "thermal", "b": "propulsion", "types": ["thermal"], "desc": "Propellant tank heating; catalyst bed temperature"},
    # RF
    {"a": "link", "b": "payload", "types": ["rf"], "desc": "RF interference; antenna pattern vs payload FOV"},
    {"a": "link", "b": "aocs", "types": ["rf", "optical"], "desc": "Antenna deployment vs star tracker FOV"},
    # Propulsion
    {"a": "propulsion", "b": "aocs", "types": ["mechanical"], "desc": "Thruster alignment; plume impingement on SA/sensors"},
]

# Common interface conflicts that should be checked
_COMMON_CONFLICTS: list[dict[str, str]] = [
    {"title": "Solar array vs star tracker FOV",
     "desc": "Deployable SA panels may occlude star tracker field of view in certain orientations",
     "a": "power", "b": "aocs", "type": "optical", "severity": "major"},
    {"title": "Thruster plume impingement on solar array",
     "desc": "RCS thruster exhaust may deposit contaminants on SA cells or cause thermal loads",
     "a": "propulsion", "b": "power", "type": "propulsion", "severity": "major"},
    {"title": "Antenna deployment vs payload FOV",
     "desc": "High-gain antenna or deployable boom may obstruct payload instrument field of view",
     "a": "link", "b": "payload", "type": "optical", "severity": "major"},
    {"title": "Reaction wheel vibration vs payload stability",
     "desc": "Micro-vibrations from reaction wheels may degrade optical payload image quality",
     "a": "aocs", "b": "payload", "type": "mechanical", "severity": "critical"},
    {"title": "Power bus voltage compatibility",
     "desc": "Subsystem input voltage range must be compatible with EPS regulated bus output",
     "a": "power", "b": "data", "type": "electrical", "severity": "critical"},
    {"title": "Radiator area vs SA area competition",
     "desc": "Both radiators and solar arrays need external surface area; they compete for panel real estate",
     "a": "thermal", "b": "power", "type": "mechanical", "severity": "major"},
    {"title": "EMC: TX interference with payload",
     "desc": "S/X-band transmission may cause electromagnetic interference with sensitive payload detectors",
     "a": "link", "b": "payload", "type": "rf", "severity": "major"},
]


class InterfaceMatrix(BaseModel):
    """The complete set of interfaces for the mission.

    Auto-populated from the standard interface set, then refined by
    engineers. The matrix exposes:
    - Which subsystem pairs have interfaces (and of what type)
    - Where interface requirements are missing
    - Where interface conflicts exist
    """
    subsystem_interfaces: list[SubsystemInterface] = Field(default_factory=list)
    external_interfaces: list[ExternalInterface] = Field(default_factory=list)
    conflicts: list[InterfaceConflict] = Field(default_factory=list)

    @property
    def total_interfaces(self) -> int:
        return len(self.subsystem_interfaces) + len(self.external_interfaces)

    @property
    def undefined_count(self) -> int:
        return sum(1 for si in self.subsystem_interfaces if si.status == InterfaceStatus.IDENTIFIED)

    @property
    def conflict_count(self) -> int:
        return len([c for c in self.conflicts if not c.resolved])

    def get_interface(self, sub_a: str, sub_b: str) -> SubsystemInterface | None:
        for si in self.subsystem_interfaces:
            if (si.subsystem_a == sub_a and si.subsystem_b == sub_b) or \
               (si.subsystem_a == sub_b and si.subsystem_b == sub_a):
                return si
        return None

    def completeness_report(self) -> dict[str, Any]:
        total = len(self.subsystem_interfaces)
        defined = sum(1 for si in self.subsystem_interfaces if si.status.value in ("defined", "agreed", "verified"))
        conflicts = self.conflict_count
        return {
            "total_interfaces": total,
            "defined": defined,
            "undefined": total - defined,
            "completeness_percent": (defined / max(total, 1)) * 100,
            "active_conflicts": conflicts,
            "external_interfaces": len(self.external_interfaces),
        }


def generate_standard_interface_matrix() -> InterfaceMatrix:
    """Generate the standard interface matrix for a typical spacecraft.

    Pre-populates all standard subsystem-to-subsystem interfaces
    and flags common conflict areas.
    """
    matrix = InterfaceMatrix()

    for si in _STANDARD_INTERFACES:
        matrix.subsystem_interfaces.append(SubsystemInterface(
            subsystem_a=si["a"],
            subsystem_b=si["b"],
            interface_types=[InterfaceType(t) for t in si["types"]],
            description=si["desc"],
            status=InterfaceStatus.IDENTIFIED,
        ))

    for cc in _COMMON_CONFLICTS:
        matrix.conflicts.append(InterfaceConflict(
            id=f"IC-{cc['title'][:20].replace(' ', '-').lower()}",
            title=cc["title"],
            description=cc["desc"],
            interface_type=InterfaceType(cc["type"]),
            subsystem_a=cc["a"],
            subsystem_b=cc["b"],
            severity=cc["severity"],
        ))

    # Standard external interfaces
    matrix.external_interfaces.extend([
        ExternalInterface(
            id="EI-LV", external_system="Launch vehicle",
            interface_types=[InterfaceType.MECHANICAL, InterfaceType.ELECTRICAL],
            requirements=["Payload adapter mechanical interface", "Separation system", "Umbilical connector"],
        ),
        ExternalInterface(
            id="EI-GS", external_system="Ground segment",
            interface_types=[InterfaceType.DATA, InterfaceType.RF],
            requirements=["TTC link protocol (CCSDS)", "Frequency coordination", "Data delivery interface"],
        ),
    ])

    return matrix
