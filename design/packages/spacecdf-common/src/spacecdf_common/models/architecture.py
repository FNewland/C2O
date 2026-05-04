"""SpaceCDF -- System & Subsystem Architecture Model.

Defines architecture options per subsystem, with mass/power/cost impacts,
derived requirements, and block diagram data.

Per NASA SEH Process 4 (Design Solution Definition) and ECSS-E-ST-10C SS5.4:
architecture selection defines system boundaries, identifies interfaces, and
enables decomposition of requirements to lower levels.

References:
  - NASA SEH SS4.4 (Process 4: Design Solution Definition)
  - ECSS-E-ST-10C Rev.1 SS5.4 (System design)
  - SMAD4 Ch.10-11 (Subsystem design)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ArchitectureOption:
    """A selectable architecture option for a subsystem."""
    id: str
    subsystem: str
    name: str
    description: str
    mass_kg_typical: float
    power_w_typical: float
    cost_keur_typical: float
    trl: int
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    pointing_deg: float | None = None  # For AOCS options
    data_rate_mbps: float | None = None  # For TTC options
    derived_requirements: list[dict[str, str]] = field(default_factory=list)
    # Block diagram: list of blocks and connections
    blocks: list[dict[str, str]] = field(default_factory=list)
    connections: list[dict[str, str]] = field(default_factory=list)


@dataclass
class SelectedArchitecture:
    """The chosen architecture for each subsystem."""
    selections: dict[str, str] = field(default_factory=dict)  # subsystem -> option_id
    derived_requirements: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Architecture Options Catalogue
# ---------------------------------------------------------------------------

EPS_OPTIONS = [
    ArchitectureOption(
        id="eps-body-single", subsystem="eps",
        name="Body-mounted SA + single battery",
        description="Simplest configuration. Solar cells on body panels, single Li-ion battery pack, basic EPS board.",
        mass_kg_typical=0.6, power_w_typical=8.0, cost_keur_typical=15, trl=9,
        pros=["Simplest design", "No deployment risk", "Lowest cost", "Flight proven"],
        cons=["Limited power (7-12W for 3U)", "No redundancy", "Eclipse survival constrained"],
        derived_requirements=[
            {"id": "SR-PWR-001", "level": "system", "text": "The EPS shall generate >=8W EOL from body-mounted solar cells"},
            {"id": "SR-PWR-002", "level": "system", "text": "The EPS shall provide regulated 3.3V and 5.0V buses"},
            {"id": "SSR-PWR-001", "level": "subsystem", "text": "The battery shall provide >=10 Wh at 30% maximum DoD"},
        ],
        blocks=[
            {"id": "sa", "name": "Body-Mounted SA", "type": "source"},
            {"id": "eps", "name": "EPS Board (MPPT)", "type": "processor"},
            {"id": "bat", "name": "Li-Ion Battery", "type": "storage"},
            {"id": "bus", "name": "Power Bus (3.3/5V)", "type": "distribution"},
        ],
        connections=[
            {"from": "sa", "to": "eps", "label": "Raw solar"},
            {"from": "eps", "to": "bat", "label": "Charge"},
            {"from": "bat", "to": "eps", "label": "Discharge"},
            {"from": "eps", "to": "bus", "label": "Regulated"},
        ],
    ),
    ArchitectureOption(
        id="eps-deploy-single", subsystem="eps",
        name="Deployable SA + single battery",
        description="Deployable solar panels for higher power. Single battery. Deployment mechanism required.",
        mass_kg_typical=0.9, power_w_typical=20.0, cost_keur_typical=25, trl=8,
        pros=["Higher power (15-30W)", "Enables more payload duty cycle", "Well-proven on CubeSats"],
        cons=["Deployment risk", "More complex", "Higher mass", "Mechanism testing needed"],
        derived_requirements=[
            {"id": "SR-PWR-001", "level": "system", "text": "The EPS shall generate >=20W EOL from deployable solar arrays"},
            {"id": "SR-PWR-002", "level": "system", "text": "The EPS shall provide regulated 3.3V and 5.0V buses"},
            {"id": "SR-PWR-003", "level": "system", "text": "The SA deployment mechanism shall deploy within 30 minutes of separation"},
            {"id": "SSR-PWR-001", "level": "subsystem", "text": "The battery shall provide >=20 Wh at 30% maximum DoD"},
            {"id": "SSR-PWR-002", "level": "subsystem", "text": "The deployment hinge shall provide >=180deg deployment angle"},
        ],
        blocks=[
            {"id": "sa", "name": "Deployable SA Panels", "type": "source"},
            {"id": "hinge", "name": "Deployment Hinge", "type": "mechanism"},
            {"id": "eps", "name": "EPS Board (MPPT)", "type": "processor"},
            {"id": "bat", "name": "Li-Ion Battery", "type": "storage"},
            {"id": "bus", "name": "Power Bus (3.3/5V)", "type": "distribution"},
        ],
        connections=[
            {"from": "sa", "to": "hinge", "label": "Deployed by"},
            {"from": "sa", "to": "eps", "label": "Raw solar"},
            {"from": "eps", "to": "bat", "label": "Charge"},
            {"from": "eps", "to": "bus", "label": "Regulated"},
        ],
    ),
    ArchitectureOption(
        id="eps-deploy-redundant", subsystem="eps",
        name="Deployable SA + redundant battery",
        description="Highest reliability. Dual battery packs with cross-strapping. Deployable SA.",
        mass_kg_typical=1.3, power_w_typical=25.0, cost_keur_typical=40, trl=8,
        pros=["High reliability", "Battery redundancy", "Higher power"],
        cons=["Highest mass", "Most complex", "Highest cost", "Two battery charging circuits"],
        derived_requirements=[
            {"id": "SR-PWR-001", "level": "system", "text": "The EPS shall generate >=25W EOL from deployable solar arrays"},
            {"id": "SR-PWR-002", "level": "system", "text": "The EPS shall provide redundant battery packs with autonomous switchover"},
            {"id": "SR-PWR-003", "level": "system", "text": "The EPS shall survive single battery pack failure"},
        ],
        blocks=[
            {"id": "sa", "name": "Deployable SA", "type": "source"},
            {"id": "eps", "name": "EPS Board (MPPT)", "type": "processor"},
            {"id": "bat1", "name": "Battery Pack A", "type": "storage"},
            {"id": "bat2", "name": "Battery Pack B", "type": "storage"},
            {"id": "sw", "name": "Switchover Logic", "type": "processor"},
            {"id": "bus", "name": "Power Bus", "type": "distribution"},
        ],
        connections=[
            {"from": "sa", "to": "eps", "label": "Raw solar"},
            {"from": "eps", "to": "bat1", "label": "Charge A"},
            {"from": "eps", "to": "bat2", "label": "Charge B"},
            {"from": "bat1", "to": "sw", "label": ""},
            {"from": "bat2", "to": "sw", "label": ""},
            {"from": "sw", "to": "bus", "label": "Selected"},
        ],
    ),
]

AOCS_OPTIONS = [
    ArchitectureOption(
        id="aocs-passive", subsystem="aocs",
        name="Passive magnetic stabilisation",
        description="Permanent magnet aligns with Earth's field. No active control. Simplest possible.",
        mass_kg_typical=0.05, power_w_typical=0.0, cost_keur_typical=2, trl=9,
        pointing_deg=10.0,
        pros=["No power", "No software", "No failure modes", "Lowest mass"],
        cons=["~10deg pointing only", "Cannot point at targets", "Libration oscillations"],
        derived_requirements=[
            {"id": "SR-AOCS-001", "level": "system", "text": "The AOCS shall maintain alignment within 10deg of local magnetic field"},
        ],
        blocks=[{"id": "mag", "name": "Permanent Magnet", "type": "actuator"}, {"id": "hyst", "name": "Hysteresis Rods", "type": "damper"}],
        connections=[],
    ),
    ArchitectureOption(
        id="aocs-mtq", subsystem="aocs",
        name="Magnetorquer-only (3-axis)",
        description="Active magnetic control using 3-axis magnetorquers. Coarse pointing. No reaction wheels.",
        mass_kg_typical=0.1, power_w_typical=1.0, cost_keur_typical=8, trl=9,
        pointing_deg=3.0,
        pros=["Simple", "Low mass", "No moving parts", "Low cost"],
        cons=["2-5deg pointing", "Cannot hold constant attitude", "Depends on magnetic field"],
        derived_requirements=[
            {"id": "SR-AOCS-001", "level": "system", "text": "The AOCS shall achieve <=3deg pointing accuracy using magnetorquers"},
            {"id": "SR-AOCS-002", "level": "system", "text": "The AOCS shall provide B-dot detumbling within 5 orbits"},
            {"id": "SSR-AOCS-001", "level": "subsystem", "text": "Each magnetorquer shall provide >=0.2 Am2 dipole moment"},
        ],
        blocks=[
            {"id": "ss", "name": "Sun Sensors (x2)", "type": "sensor"},
            {"id": "mag", "name": "Magnetometer", "type": "sensor"},
            {"id": "obc", "name": "ADCS Algorithm", "type": "processor"},
            {"id": "mtq", "name": "Magnetorquers (x3)", "type": "actuator"},
        ],
        connections=[
            {"from": "ss", "to": "obc", "label": "Sun vector"},
            {"from": "mag", "to": "obc", "label": "B-field"},
            {"from": "obc", "to": "mtq", "label": "Dipole cmd"},
        ],
    ),
    ArchitectureOption(
        id="aocs-3wheel", subsystem="aocs",
        name="3 reaction wheels + magnetorquers",
        description="Medium pointing. 3-axis RW control with MTQ for momentum dumping. No star tracker.",
        mass_kg_typical=0.5, power_w_typical=3.0, cost_keur_typical=35, trl=9,
        pointing_deg=0.5,
        pros=["Moderate pointing (<1deg)", "Proven on many CubeSats", "Moderate cost"],
        cons=["No redundancy (3 wheels)", "Wheel vibration affects payload", "No star tracker = limited accuracy"],
        derived_requirements=[
            {"id": "SR-AOCS-001", "level": "system", "text": "The AOCS shall achieve <=0.5deg pointing accuracy"},
            {"id": "SR-AOCS-002", "level": "system", "text": "The AOCS shall dump accumulated momentum using magnetorquers"},
            {"id": "SSR-AOCS-001", "level": "subsystem", "text": "Each reaction wheel shall provide >=2 mNm torque and >=10 mNms momentum"},
        ],
        blocks=[
            {"id": "ss", "name": "Sun Sensors (x2)", "type": "sensor"},
            {"id": "mag", "name": "Magnetometer", "type": "sensor"},
            {"id": "obc", "name": "ADCS Algorithm", "type": "processor"},
            {"id": "rw", "name": "Reaction Wheels (x3)", "type": "actuator"},
            {"id": "mtq", "name": "Magnetorquers (x3)", "type": "actuator"},
        ],
        connections=[
            {"from": "ss", "to": "obc", "label": "Sun vector"},
            {"from": "mag", "to": "obc", "label": "B-field"},
            {"from": "obc", "to": "rw", "label": "Torque cmd"},
            {"from": "obc", "to": "mtq", "label": "Dump cmd"},
        ],
    ),
    ArchitectureOption(
        id="aocs-fine", subsystem="aocs",
        name="4 RW + star tracker + magnetorquers",
        description="Fine pointing. Redundant 4-wheel config (3+1). Star tracker for arcsec-level attitude knowledge.",
        mass_kg_typical=0.8, power_w_typical=5.0, cost_keur_typical=55, trl=9,
        pointing_deg=0.05,
        pros=["Fine pointing (<0.1deg)", "4th wheel redundancy", "Star tracker accuracy"],
        cons=["Higher mass", "Higher cost", "Star tracker FOV exclusion zones", "Wheel vibration"],
        derived_requirements=[
            {"id": "SR-AOCS-001", "level": "system", "text": "The AOCS shall achieve <=0.1deg pointing accuracy in imaging mode"},
            {"id": "SR-AOCS-002", "level": "system", "text": "The AOCS shall autonomously enter safe mode (sun-pointing) on anomaly"},
            {"id": "SR-AOCS-003", "level": "system", "text": "The AOCS shall provide 3+1 redundant reaction wheel configuration"},
            {"id": "SSR-AOCS-001", "level": "subsystem", "text": "The star tracker shall provide <=10 arcsec attitude knowledge (3-sigma)"},
            {"id": "SSR-AOCS-002", "level": "subsystem", "text": "Each reaction wheel shall provide >=5 mNm torque"},
            {"id": "SSR-AOCS-003", "level": "subsystem", "text": "The safe mode shall use sun sensors + magnetorquers only"},
        ],
        blocks=[
            {"id": "st", "name": "Star Tracker", "type": "sensor"},
            {"id": "ss", "name": "Sun Sensors (x2)", "type": "sensor"},
            {"id": "gyro", "name": "Gyroscope", "type": "sensor"},
            {"id": "mag", "name": "Magnetometer", "type": "sensor"},
            {"id": "obc", "name": "ADCS Algorithm", "type": "processor"},
            {"id": "rw", "name": "Reaction Wheels (x4)", "type": "actuator"},
            {"id": "mtq", "name": "Magnetorquers (x3)", "type": "actuator"},
        ],
        connections=[
            {"from": "st", "to": "obc", "label": "Attitude quaternion"},
            {"from": "ss", "to": "obc", "label": "Sun vector (safe)"},
            {"from": "gyro", "to": "obc", "label": "Angular rate"},
            {"from": "mag", "to": "obc", "label": "B-field"},
            {"from": "obc", "to": "rw", "label": "Torque cmd"},
            {"from": "obc", "to": "mtq", "label": "Dump cmd"},
        ],
    ),
]

TTC_OPTIONS = [
    ArchitectureOption(
        id="ttc-uhf-amateur", subsystem="ttc",
        name="UHF amateur only",
        description="Single UHF transceiver on amateur band. Low rate. IARU coordination required.",
        mass_kg_typical=0.1, power_w_typical=2.0, cost_keur_typical=10, trl=9,
        data_rate_mbps=0.01,
        pros=["Free licensing", "Simplest", "Lowest cost", "Community support (SatNOGS)"],
        cons=["<=19.2 kbps", "No encryption", "Open data required", "No commercial use"],
        derived_requirements=[
            {"id": "SR-TTC-001", "level": "system", "text": "The TTC shall provide command uplink and telemetry downlink on UHF amateur band"},
            {"id": "SR-TTC-002", "level": "system", "text": "The TTC shall provide >=3 dB link margin at 10deg elevation"},
            {"id": "SSR-TTC-001", "level": "subsystem", "text": "The UHF transceiver shall operate at 435-438 MHz with >=0.5W RF output"},
        ],
        blocks=[
            {"id": "rx", "name": "UHF Receiver", "type": "receiver"},
            {"id": "tx", "name": "UHF Transmitter", "type": "transmitter"},
            {"id": "ant", "name": "UHF Antenna", "type": "antenna"},
            {"id": "obc", "name": "TM/TC Handler", "type": "processor"},
        ],
        connections=[
            {"from": "ant", "to": "rx", "label": "TC uplink"},
            {"from": "tx", "to": "ant", "label": "TM downlink"},
            {"from": "rx", "to": "obc", "label": "Commands"},
            {"from": "obc", "to": "tx", "label": "Telemetry"},
        ],
    ),
    ArchitectureOption(
        id="ttc-sband", subsystem="ttc",
        name="S-band (TTC + moderate data)",
        description="Single S-band for both TTC and payload data. Commercial licence required.",
        mass_kg_typical=0.2, power_w_typical=6.0, cost_keur_typical=25, trl=9,
        data_rate_mbps=4.0,
        pros=["Moderate data rate (1-10 Mbps)", "Single band", "Moderate cost"],
        cons=["Commercial licence needed", "ITU filing required", "Higher power than UHF"],
        derived_requirements=[
            {"id": "SR-TTC-001", "level": "system", "text": "The TTC shall provide S-band uplink (2025-2110 MHz) and downlink (2200-2290 MHz)"},
            {"id": "SR-TTC-002", "level": "system", "text": "The TTC shall achieve >=4 Mbps downlink data rate"},
            {"id": "SR-TTC-003", "level": "system", "text": "The TTC shall provide >=3 dB link margin at 10deg elevation"},
        ],
        blocks=[
            {"id": "rx", "name": "S-band Receiver", "type": "receiver"},
            {"id": "tx", "name": "S-band Transmitter", "type": "transmitter"},
            {"id": "dip", "name": "Diplexer", "type": "filter"},
            {"id": "ant", "name": "S-band Patch Antenna", "type": "antenna"},
            {"id": "obc", "name": "TM/TC + Data Handler", "type": "processor"},
        ],
        connections=[
            {"from": "ant", "to": "dip", "label": "RF"},
            {"from": "dip", "to": "rx", "label": "Uplink"},
            {"from": "tx", "to": "dip", "label": "Downlink"},
            {"from": "rx", "to": "obc", "label": "Commands"},
            {"from": "obc", "to": "tx", "label": "TM + Data"},
        ],
    ),
    ArchitectureOption(
        id="ttc-dual-uhf-xband", subsystem="ttc",
        name="UHF TTC + X-band payload downlink",
        description="Dual-band: UHF for commanding, X-band for high-rate payload data.",
        mass_kg_typical=0.5, power_w_typical=12.0, cost_keur_typical=60, trl=8,
        data_rate_mbps=200.0,
        pros=["Very high data rate (50-400 Mbps)", "UHF backup for commands", "Professional"],
        cons=["Dual RF chains", "X-band needs pointing", "Higher mass/power/cost", "Complex licensing"],
        derived_requirements=[
            {"id": "SR-TTC-001", "level": "system", "text": "The TTC shall provide UHF command uplink and beacon downlink"},
            {"id": "SR-TTC-002", "level": "system", "text": "The TTC shall provide X-band payload downlink at >=50 Mbps"},
            {"id": "SR-TTC-003", "level": "system", "text": "Both links shall provide >=3 dB margin at 10deg elevation"},
            {"id": "SSR-TTC-001", "level": "subsystem", "text": "The X-band transmitter shall provide >=2W RF output at 8025-8400 MHz"},
            {"id": "SSR-TTC-002", "level": "subsystem", "text": "The X-band antenna shall provide >=10 dBi gain"},
        ],
        blocks=[
            {"id": "uhf_rx", "name": "UHF Receiver", "type": "receiver"},
            {"id": "uhf_tx", "name": "UHF Beacon TX", "type": "transmitter"},
            {"id": "uhf_ant", "name": "UHF Antenna", "type": "antenna"},
            {"id": "x_tx", "name": "X-band Transmitter", "type": "transmitter"},
            {"id": "x_ant", "name": "X-band Antenna", "type": "antenna"},
            {"id": "obc", "name": "Data Handler", "type": "processor"},
        ],
        connections=[
            {"from": "uhf_ant", "to": "uhf_rx", "label": "TC"},
            {"from": "uhf_tx", "to": "uhf_ant", "label": "Beacon"},
            {"from": "obc", "to": "x_tx", "label": "Payload data"},
            {"from": "x_tx", "to": "x_ant", "label": "X-band DL"},
            {"from": "uhf_rx", "to": "obc", "label": "Commands"},
        ],
    ),
]

# Complete catalogue indexed by subsystem
ARCHITECTURE_CATALOGUE: dict[str, list[ArchitectureOption]] = {
    "eps": EPS_OPTIONS,
    "aocs": AOCS_OPTIONS,
    "ttc": TTC_OPTIONS,
}


def get_options(subsystem: str) -> list[ArchitectureOption]:
    """Get available architecture options for a subsystem."""
    return ARCHITECTURE_CATALOGUE.get(subsystem, [])


def select_architecture(subsystem: str, option_id: str) -> dict[str, Any]:
    """Select an architecture and return derived requirements + block diagram."""
    options = ARCHITECTURE_CATALOGUE.get(subsystem, [])
    selected = next((o for o in options if o.id == option_id), None)
    if not selected:
        return {"error": f"Unknown option: {option_id}"}

    return {
        "subsystem": subsystem,
        "option_id": option_id,
        "option_name": selected.name,
        "description": selected.description,
        "mass_kg": selected.mass_kg_typical,
        "power_w": selected.power_w_typical,
        "cost_keur": selected.cost_keur_typical,
        "trl": selected.trl,
        "derived_requirements": selected.derived_requirements,
        "blocks": [{"id": b["id"], "name": b["name"], "type": b["type"]} for b in selected.blocks],
        "connections": selected.connections,
    }


def get_all_subsystems() -> list[str]:
    """Return all subsystems with architecture options."""
    return list(ARCHITECTURE_CATALOGUE.keys())
