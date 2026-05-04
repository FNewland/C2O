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
            # Performance
            {"id": "SR-PWR-001", "level": "system", "type": "performance", "text": "The EPS shall generate >=8W EOL from body-mounted solar cells"},
            {"id": "SR-PWR-002", "level": "system", "type": "performance", "text": "The EPS shall maintain positive power margin in all operational modes"},
            # Interface
            {"id": "IR-PWR-001", "level": "system", "type": "interface", "text": "The EPS shall provide regulated 3.3V +/-0.1V and 5.0V +/-0.25V buses to all subsystems via PC/104 connector"},
            {"id": "IR-PWR-002", "level": "system", "type": "interface", "text": "The EPS shall provide >=4 independently switched power lines with over-current protection"},
            {"id": "IR-PWR-003", "level": "system", "type": "interface", "text": "The EPS shall provide battery voltage telemetry via I2C to the OBC"},
            # Budget
            {"id": "BR-PWR-001", "level": "system", "type": "budget", "text": "The EPS total mass shall not exceed 0.75 kg including SA, battery, and board"},
            {"id": "BR-PWR-002", "level": "system", "type": "budget", "text": "The EPS recurring cost shall not exceed 20 kEUR"},
            # Functional
            {"id": "FR-PWR-001", "level": "system", "type": "functional", "text": "The EPS shall autonomously disconnect loads when battery voltage falls below safe threshold"},
            {"id": "FR-PWR-002", "level": "system", "type": "functional", "text": "The EPS shall support battery passivation (discharge to safe level) via ground command"},
            # Subsystem
            {"id": "SSR-PWR-001", "level": "subsystem", "type": "performance", "text": "The battery shall provide >=10 Wh capacity at 30% maximum DoD"},
            {"id": "SSR-PWR-002", "level": "subsystem", "type": "interface", "text": "The EPS board shall accept 4 solar panel inputs via standard connectors"},
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
            # Performance
            {"id": "SR-PWR-001", "level": "system", "type": "performance", "text": "The EPS shall generate >=20W EOL from deployable solar arrays"},
            {"id": "SR-PWR-002", "level": "system", "type": "performance", "text": "The EPS shall maintain positive power margin in all operational modes including eclipse"},
            # Interface
            {"id": "IR-PWR-001", "level": "system", "type": "interface", "text": "The EPS shall provide regulated 3.3V +/-0.1V and 5.0V +/-0.25V buses via PC/104"},
            {"id": "IR-PWR-002", "level": "system", "type": "interface", "text": "The EPS shall provide >=6 independently switched power lines"},
            {"id": "IR-PWR-003", "level": "system", "type": "interface", "text": "The SA deployment signal shall be provided by the OBC via dedicated GPIO"},
            {"id": "IR-PWR-004", "level": "system", "type": "interface", "text": "The SA deployment status shall be reported via deployment switch telemetry"},
            # Budget
            {"id": "BR-PWR-001", "level": "system", "type": "budget", "text": "The EPS total mass shall not exceed 1.1 kg including deployable SA, battery, and board"},
            # Functional
            {"id": "FR-PWR-001", "level": "system", "type": "functional", "text": "The SA deployment mechanism shall deploy within 30 minutes of separation"},
            {"id": "FR-PWR-002", "level": "system", "type": "functional", "text": "The EPS shall autonomously manage battery charge/discharge cycling"},
            {"id": "FR-PWR-003", "level": "system", "type": "functional", "text": "The EPS shall support battery passivation via ground command"},
            # Subsystem
            {"id": "SSR-PWR-001", "level": "subsystem", "type": "performance", "text": "The battery shall provide >=20 Wh at 30% maximum DoD"},
            {"id": "SSR-PWR-002", "level": "subsystem", "type": "interface", "text": "The deployment hinge shall provide >=180deg deployment with positive latch"},
            {"id": "SSR-PWR-003", "level": "subsystem", "type": "interface", "text": "The SA harness shall route through the hinge without exceeding bend radius limits"},
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
            # Performance
            {"id": "SR-AOCS-001", "level": "system", "type": "performance", "text": "The AOCS shall achieve <=0.1deg pointing accuracy (3-sigma) in imaging mode"},
            {"id": "SR-AOCS-002", "level": "system", "type": "performance", "text": "The AOCS shall achieve <=0.01deg/s pointing stability during imaging"},
            {"id": "SR-AOCS-003", "level": "system", "type": "performance", "text": "The AOCS shall complete a 30deg slew within 120 seconds"},
            # Functional
            {"id": "FR-AOCS-001", "level": "system", "type": "functional", "text": "The AOCS shall autonomously enter safe mode (sun-pointing) within 60s of anomaly detection"},
            {"id": "FR-AOCS-002", "level": "system", "type": "functional", "text": "The AOCS shall perform autonomous momentum dumping using magnetorquers"},
            {"id": "FR-AOCS-003", "level": "system", "type": "functional", "text": "The AOCS shall support nadir pointing, target tracking, and inertial hold modes"},
            # Interface
            {"id": "IR-AOCS-001", "level": "system", "type": "interface", "text": "The AOCS shall receive attitude commands from the OBC via I2C/SPI bus"},
            {"id": "IR-AOCS-002", "level": "system", "type": "interface", "text": "The AOCS shall provide attitude quaternion telemetry to the OBC at >=1 Hz"},
            {"id": "IR-AOCS-003", "level": "system", "type": "interface", "text": "The reaction wheels shall be powered via dedicated EPS switched lines"},
            {"id": "IR-AOCS-004", "level": "system", "type": "interface", "text": "The star tracker mounting shall maintain <=0.05deg alignment to payload axis"},
            # Budget
            {"id": "BR-AOCS-001", "level": "system", "type": "budget", "text": "The AOCS total mass shall not exceed 1.0 kg (4 RW + ST + 3 MTQ + sensors)"},
            {"id": "BR-AOCS-002", "level": "system", "type": "budget", "text": "The AOCS peak power shall not exceed 8W (all wheels + ST active)"},
            # Subsystem
            {"id": "SSR-AOCS-001", "level": "subsystem", "type": "performance", "text": "The star tracker shall provide <=10 arcsec attitude knowledge (3-sigma)"},
            {"id": "SSR-AOCS-002", "level": "subsystem", "type": "performance", "text": "Each reaction wheel shall provide >=5 mNm torque and >=20 mNms momentum"},
            {"id": "SSR-AOCS-003", "level": "subsystem", "type": "interface", "text": "The star tracker shall have >=20deg x 20deg FOV with exclusion zone handling"},
            {"id": "SSR-AOCS-004", "level": "subsystem", "type": "functional", "text": "The safe mode shall use sun sensors + magnetorquers only (no RW/ST dependency)"},
            {"id": "SSR-AOCS-005", "level": "subsystem", "type": "interface", "text": "The RW vibration isolators shall attenuate >=20 dB above 50 Hz"},
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
            # Performance
            {"id": "SR-TTC-001", "level": "system", "type": "performance", "text": "The TTC shall achieve >=4 Mbps downlink data rate at >=3 dB margin"},
            {"id": "SR-TTC-002", "level": "system", "type": "performance", "text": "The TTC shall close the link at minimum 10deg elevation angle"},
            # Interface
            {"id": "IR-TTC-001", "level": "system", "type": "interface", "text": "The TTC shall operate on S-band uplink (2025-2110 MHz) and downlink (2200-2290 MHz)"},
            {"id": "IR-TTC-002", "level": "system", "type": "interface", "text": "The TTC shall interface with the OBC via UART for TC reception and TM formatting"},
            {"id": "IR-TTC-003", "level": "system", "type": "interface", "text": "The TTC RF output shall be 50 ohm impedance via SMA connector to antenna"},
            {"id": "IR-TTC-004", "level": "system", "type": "interface", "text": "The TTC shall be powered via dedicated EPS switched line"},
            # Budget
            {"id": "BR-TTC-001", "level": "system", "type": "budget", "text": "The TTC total mass shall not exceed 0.3 kg (transponder + antenna + cable)"},
            {"id": "BR-TTC-002", "level": "system", "type": "budget", "text": "The TTC peak power shall not exceed 8W during transmission"},
            # Functional
            {"id": "FR-TTC-001", "level": "system", "type": "functional", "text": "The TTC shall support store-and-forward data delivery"},
            {"id": "FR-TTC-002", "level": "system", "type": "functional", "text": "The TTC shall transmit beacon telemetry at >=1 packet per 30 seconds in safe mode"},
            {"id": "FR-TTC-003", "level": "system", "type": "functional", "text": "The TTC shall support authenticated telecommand reception"},
            # Subsystem
            {"id": "SSR-TTC-001", "level": "subsystem", "type": "performance", "text": "The S-band transmitter shall provide >=2W RF output power"},
            {"id": "SSR-TTC-002", "level": "subsystem", "type": "interface", "text": "The S-band antenna shall provide >=4 dBi gain with hemispherical coverage"},
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

THERMAL_OPTIONS = [
    ArchitectureOption(
        id="tcs-passive-coatings", subsystem="thermal",
        name="Passive only (surface coatings)",
        description="Thermal control through surface finishes only. No heaters, no MLI. Suitable for low-power LEO missions.",
        mass_kg_typical=0.01, power_w_typical=0.0, cost_keur_typical=2, trl=9,
        pros=["Zero power", "Zero mass", "No failure modes", "Simplest possible"],
        cons=["No cold case protection", "Limited to benign orbits", "No active temperature control"],
        derived_requirements=[
            {"id": "SR-TCS-001", "level": "system", "text": "All external surfaces shall have thermal coatings selected for equilibrium temperature within component limits"},
        ],
        blocks=[{"id": "coat", "name": "Surface Coatings (alpha/epsilon)", "type": "passive"}],
        connections=[],
    ),
    ArchitectureOption(
        id="tcs-passive-heaters", subsystem="thermal",
        name="Passive + heaters",
        description="Surface coatings plus thermostatically controlled heaters for eclipse cold case. Standard CubeSat approach.",
        mass_kg_typical=0.05, power_w_typical=2.0, cost_keur_typical=5, trl=9,
        pros=["Eclipse protection", "Simple control", "Low mass", "Well proven"],
        cons=["Heater power from battery during eclipse", "Limited hot case control"],
        derived_requirements=[
            {"id": "SR-TCS-001", "level": "system", "text": "The TCS shall maintain all components within operating range [-20C, +50C]"},
            {"id": "SR-TCS-002", "level": "system", "text": "The TCS shall provide survival heating during eclipse"},
            {"id": "SSR-TCS-001", "level": "subsystem", "text": "Eclipse heater power shall not exceed 3W total"},
        ],
        blocks=[
            {"id": "coat", "name": "Surface Coatings", "type": "passive"},
            {"id": "htr", "name": "Kapton Heaters", "type": "active"},
            {"id": "therm", "name": "Thermistors", "type": "sensor"},
            {"id": "ctrl", "name": "Thermostat Control", "type": "processor"},
        ],
        connections=[
            {"from": "therm", "to": "ctrl", "label": "Temperature"},
            {"from": "ctrl", "to": "htr", "label": "On/Off"},
        ],
    ),
    ArchitectureOption(
        id="tcs-active-mli", subsystem="thermal",
        name="Passive + heaters + MLI",
        description="Full passive thermal control with MLI blankets for insulation. For missions with larger thermal excursions.",
        mass_kg_typical=0.15, power_w_typical=3.0, cost_keur_typical=8, trl=9,
        pros=["Good insulation", "Reduces heater power need", "Protects sensitive components"],
        cons=["MLI mass", "Installation complexity", "Outgassing concerns"],
        derived_requirements=[
            {"id": "SR-TCS-001", "level": "system", "text": "The TCS shall maintain all components within operating range [-20C, +50C]"},
            {"id": "SR-TCS-002", "level": "system", "text": "The TCS shall provide MLI insulation on spacecraft surfaces not used as radiators"},
            {"id": "SSR-TCS-001", "level": "subsystem", "text": "MLI effective emittance shall be <=0.02"},
        ],
        blocks=[
            {"id": "mli", "name": "MLI Blankets", "type": "passive"},
            {"id": "rad", "name": "Radiator Surface", "type": "passive"},
            {"id": "htr", "name": "Heaters", "type": "active"},
            {"id": "therm", "name": "Thermistors", "type": "sensor"},
        ],
        connections=[
            {"from": "therm", "to": "htr", "label": "Control"},
        ],
    ),
]

STRUCTURE_OPTIONS = [
    ArchitectureOption(
        id="str-3u", subsystem="structure",
        name="3U CubeSat (10x10x34 cm)",
        description="Standard 3U frame per CDS Rev 14.1. 3000 cm3 internal volume. 6 kg mass limit.",
        mass_kg_typical=0.35, power_w_typical=0.0, cost_keur_typical=8, trl=9,
        pros=["Most common form factor", "Widest deployer compatibility", "Lowest cost"],
        cons=["Limited volume (3000 cm3)", "6 kg mass limit", "Tight for complex missions"],
        derived_requirements=[
            # Performance
            {"id": "SR-STR-001", "level": "system", "type": "performance", "text": "The structure shall survive qualification launch loads with MoS >=0 (quasi-static, random, shock)"},
            {"id": "SR-STR-002", "level": "system", "type": "performance", "text": "The first natural frequency shall be >=40 Hz in all axes"},
            # Interface
            {"id": "IR-STR-001", "level": "system", "type": "interface", "text": "The spacecraft shall comply with CDS Rev 14.1 for 3U form factor (100x100x340.5 mm)"},
            {"id": "IR-STR-002", "level": "system", "type": "interface", "text": "The PC/104 stack shall accommodate all avionics boards within 250 mm stack height"},
            {"id": "IR-STR-003", "level": "system", "type": "interface", "text": "All subsystem mounting shall use M3 fasteners with specified torque values"},
            # Budget
            {"id": "BR-STR-001", "level": "system", "type": "budget", "text": "The total spacecraft mass shall not exceed 6 kg (CDS 3U limit)"},
            {"id": "BR-STR-002", "level": "system", "type": "budget", "text": "The structure mass shall not exceed 0.5 kg including frame, fasteners, and brackets"},
            {"id": "BR-STR-003", "level": "system", "type": "budget", "text": "Internal volume utilisation shall not exceed 85% of 3000 cm3"},
            # Functional
            {"id": "FR-STR-001", "level": "system", "type": "functional", "text": "The structure shall provide 3 independent deployment inhibits (2 switches + 1 RBF pin)"},
            {"id": "FR-STR-002", "level": "system", "type": "functional", "text": "The CG shall remain within 2 cm of geometric centre in all axes"},
            # Subsystem
            {"id": "SSR-STR-001", "level": "subsystem", "type": "interface", "text": "CDS rail dimensions shall be 8.5x8.5 mm +/-0.1 mm hard anodised aluminium"},
            {"id": "SSR-STR-002", "level": "subsystem", "type": "interface", "text": "Deployment switches shall be provided on +X and -X rail faces per deployer ICD"},
            {"id": "SSR-STR-003", "level": "subsystem", "type": "functional", "text": "RBF pin shall deactivate all power when inserted and be accessible for pre-launch removal"},
        ],
        blocks=[
            {"id": "frame", "name": "3U Frame + Rails", "type": "structure"},
            {"id": "stack", "name": "PC/104 Stack", "type": "integration"},
            {"id": "sw", "name": "Deploy Switches", "type": "mechanism"},
            {"id": "rbf", "name": "RBF Pin", "type": "mechanism"},
        ],
        connections=[],
    ),
    ArchitectureOption(
        id="str-6u", subsystem="structure",
        name="6U CubeSat (10x22.6x34 cm)",
        description="Standard 6U frame. 6000 cm3 internal volume. 12 kg mass limit. More room for payload.",
        mass_kg_typical=0.70, power_w_typical=0.0, cost_keur_typical=10, trl=9,
        pros=["Double the volume of 3U", "12 kg mass limit", "Room for larger payloads"],
        cons=["Fewer deployer options", "Higher launch cost", "Larger thermal surface"],
        derived_requirements=[
            {"id": "SR-STR-001", "level": "system", "text": "The spacecraft shall comply with CDS Rev 14.1 for 6U form factor"},
            {"id": "SR-STR-002", "level": "system", "text": "The structure shall survive qualification launch loads with MoS >=0"},
            {"id": "SR-STR-003", "level": "system", "text": "Total mass shall not exceed 12 kg"},
        ],
        blocks=[
            {"id": "frame", "name": "6U Frame + Rails", "type": "structure"},
            {"id": "stack", "name": "PC/104 Stack (2-wide)", "type": "integration"},
            {"id": "pl_bay", "name": "Payload Bay", "type": "structure"},
            {"id": "sw", "name": "Deploy Switches", "type": "mechanism"},
        ],
        connections=[],
    ),
    ArchitectureOption(
        id="str-12u", subsystem="structure",
        name="12U CubeSat (22.6x22.6x34 cm)",
        description="Large CubeSat. 12000 cm3. 24 kg. Enables complex missions (SAR, propulsion, deep space).",
        mass_kg_typical=1.20, power_w_typical=0.0, cost_keur_typical=15, trl=8,
        pros=["Large volume for complex payloads", "24 kg allows propulsion", "Room for redundancy"],
        cons=["Higher cost", "Fewer launch options", "Thermal management more complex"],
        derived_requirements=[
            {"id": "SR-STR-001", "level": "system", "text": "The spacecraft shall comply with CDS Rev 14.1 for 12U form factor"},
            {"id": "SR-STR-002", "level": "system", "text": "Total mass shall not exceed 24 kg"},
        ],
        blocks=[
            {"id": "frame", "name": "12U Frame", "type": "structure"},
            {"id": "stack", "name": "Avionics Stack", "type": "integration"},
            {"id": "pl_bay", "name": "Payload Bay", "type": "structure"},
            {"id": "prop_bay", "name": "Propulsion Bay", "type": "structure"},
        ],
        connections=[],
    ),
]

PROPULSION_OPTIONS = [
    ArchitectureOption(
        id="prop-none", subsystem="propulsion",
        name="No propulsion",
        description="No propulsion system. Natural orbital decay for deorbit. Suitable for alt <500 km.",
        mass_kg_typical=0.0, power_w_typical=0.0, cost_keur_typical=0, trl=9,
        pros=["Zero mass", "Zero cost", "Zero complexity", "No propellant safety concerns"],
        cons=["No orbit maintenance", "No collision avoidance", "Must rely on natural decay"],
        derived_requirements=[
            {"id": "SR-PROP-001", "level": "system", "text": "The spacecraft shall deorbit naturally within 5 years of end of mission (FCC rule)"},
        ],
        blocks=[],
        connections=[],
    ),
    ArchitectureOption(
        id="prop-drag-sail", subsystem="propulsion",
        name="Drag augmentation sail",
        description="Deployable drag sail for accelerated deorbit. No active manoeuvring capability.",
        mass_kg_typical=0.3, power_w_typical=0.0, cost_keur_typical=15, trl=7,
        pros=["Low mass", "No propellant", "Passive after deployment", "Addresses FCC 5yr rule"],
        cons=["No orbit maintenance", "No collision avoidance", "Deployment risk", "Changes ballistic coefficient"],
        derived_requirements=[
            {"id": "SR-PROP-001", "level": "system", "text": "The drag sail shall reduce post-mission orbital lifetime to <=5 years"},
            {"id": "SSR-PROP-001", "level": "subsystem", "text": "The sail shall deploy to >=1 m2 effective area"},
        ],
        blocks=[
            {"id": "sail", "name": "Drag Sail (stowed)", "type": "mechanism"},
            {"id": "deploy", "name": "Deployment Mechanism", "type": "mechanism"},
        ],
        connections=[{"from": "deploy", "to": "sail", "label": "Deploy cmd"}],
    ),
    ArchitectureOption(
        id="prop-cold-gas", subsystem="propulsion",
        name="Cold gas propulsion",
        description="Simplest active propulsion. Stored gas (N2 or R-236FA) expelled through thrusters.",
        mass_kg_typical=0.7, power_w_typical=1.0, cost_keur_typical=30, trl=9,
        pros=["Simple", "Safe propellant", "Fast response", "Proven on CubeSats"],
        cons=["Low Isp (40-80s)", "Limited delta-V (10-30 m/s)", "Tank volume"],
        derived_requirements=[
            {"id": "SR-PROP-001", "level": "system", "text": "The propulsion system shall provide >=20 m/s total delta-V"},
            {"id": "SR-PROP-002", "level": "system", "text": "The propulsion system shall be passivatable at end of life"},
            {"id": "SSR-PROP-001", "level": "subsystem", "text": "Propellant tank shall withstand 1.5x MEOP"},
        ],
        blocks=[
            {"id": "tank", "name": "Propellant Tank", "type": "storage"},
            {"id": "valve", "name": "Isolation Valve", "type": "mechanism"},
            {"id": "thr", "name": "Thrusters (x4-8)", "type": "actuator"},
            {"id": "ctrl", "name": "Thrust Controller", "type": "processor"},
        ],
        connections=[
            {"from": "tank", "to": "valve", "label": "Propellant"},
            {"from": "valve", "to": "thr", "label": "Gas flow"},
            {"from": "ctrl", "to": "valve", "label": "Open/Close"},
        ],
    ),
    ArchitectureOption(
        id="prop-electric", subsystem="propulsion",
        name="Electric propulsion (electrospray/Hall)",
        description="High-Isp electric propulsion. Electrospray or miniature Hall-effect thruster.",
        mass_kg_typical=1.0, power_w_typical=20.0, cost_keur_typical=80, trl=7,
        pros=["High Isp (500-1500s)", "Large delta-V (50-200 m/s)", "Compact propellant"],
        cons=["High power demand", "Low thrust (slow manoeuvres)", "Higher cost", "Lower TRL"],
        derived_requirements=[
            {"id": "SR-PROP-001", "level": "system", "text": "The propulsion system shall provide >=100 m/s total delta-V"},
            {"id": "SR-PROP-002", "level": "system", "text": "The EPS shall provide >=20W dedicated propulsion power"},
            {"id": "SSR-PROP-001", "level": "subsystem", "text": "The thruster shall provide >=500s specific impulse"},
        ],
        blocks=[
            {"id": "ppu", "name": "Power Processing Unit", "type": "processor"},
            {"id": "tank", "name": "Propellant Reservoir", "type": "storage"},
            {"id": "thr", "name": "Electric Thruster", "type": "actuator"},
            {"id": "ctrl", "name": "Thrust Controller", "type": "processor"},
        ],
        connections=[
            {"from": "ppu", "to": "thr", "label": "High voltage"},
            {"from": "tank", "to": "thr", "label": "Propellant"},
            {"from": "ctrl", "to": "ppu", "label": "Command"},
        ],
    ),
]

OBC_OPTIONS = [
    ArchitectureOption(
        id="obc-single", subsystem="obc",
        name="Single OBC (no redundancy)",
        description="Single flight computer. Standard for most CubeSats. Watchdog timer for recovery.",
        mass_kg_typical=0.08, power_w_typical=1.5, cost_keur_typical=10, trl=9,
        pros=["Low mass", "Low power", "Simple", "Sufficient for most missions"],
        cons=["Single point of failure", "No redundancy", "Relies on watchdog for recovery"],
        derived_requirements=[
            {"id": "SR-OBC-001", "level": "system", "text": "The OBC shall provide autonomous FDIR with watchdog timer recovery"},
            {"id": "SR-OBC-002", "level": "system", "text": "The OBC shall support time-tagged command execution"},
            {"id": "SSR-OBC-001", "level": "subsystem", "text": "The OBC shall provide >=4 GB non-volatile storage"},
        ],
        blocks=[
            {"id": "cpu", "name": "Processor (ARM/LEON)", "type": "processor"},
            {"id": "mem", "name": "NVM Storage", "type": "storage"},
            {"id": "wd", "name": "Watchdog Timer", "type": "processor"},
            {"id": "if", "name": "I2C/SPI/UART/CAN", "type": "interface"},
        ],
        connections=[
            {"from": "cpu", "to": "mem", "label": "Data"},
            {"from": "wd", "to": "cpu", "label": "Reset"},
            {"from": "cpu", "to": "if", "label": "Bus"},
        ],
    ),
    ArchitectureOption(
        id="obc-redundant", subsystem="obc",
        name="Redundant OBC (cold standby)",
        description="Primary + backup OBC. Automatic switchover on primary failure.",
        mass_kg_typical=0.16, power_w_typical=2.0, cost_keur_typical=20, trl=8,
        pros=["Fault tolerance", "Higher mission reliability", "Automatic failover"],
        cons=["Double mass", "Higher cost", "Switchover logic complexity"],
        derived_requirements=[
            {"id": "SR-OBC-001", "level": "system", "text": "The C&DH shall provide redundant processing with automatic failover"},
            {"id": "SR-OBC-002", "level": "system", "text": "The backup OBC shall maintain mission-critical state synchronisation"},
            {"id": "SSR-OBC-001", "level": "subsystem", "text": "Failover shall complete within 60 seconds of primary failure detection"},
        ],
        blocks=[
            {"id": "obc_a", "name": "OBC Primary", "type": "processor"},
            {"id": "obc_b", "name": "OBC Backup", "type": "processor"},
            {"id": "sw", "name": "Switchover Logic", "type": "processor"},
            {"id": "mem", "name": "Shared NVM", "type": "storage"},
        ],
        connections=[
            {"from": "obc_a", "to": "sw", "label": "Heartbeat"},
            {"from": "obc_b", "to": "sw", "label": "Ready"},
            {"from": "sw", "to": "mem", "label": "State sync"},
        ],
    ),
]

GROUND_OPTIONS = [
    ArchitectureOption(
        id="gnd-own-station", subsystem="ground",
        name="Own ground station",
        description="University or organisation-owned antenna. Full control but limited passes.",
        mass_kg_typical=0.0, power_w_typical=0.0, cost_keur_typical=50, trl=9,
        pros=["Full control", "No per-pass fees", "Educational value", "Available 24/7"],
        cons=["Single location = limited contacts", "Maintenance burden", "Weather dependent"],
        derived_requirements=[
            {"id": "SR-GND-001", "level": "system", "text": "The ground station shall provide >=2 passes per day at >=10deg elevation"},
            {"id": "SR-GND-002", "level": "system", "text": "The ground station shall support the selected TTC frequency bands"},
        ],
        blocks=[
            {"id": "ant", "name": "Tracking Antenna", "type": "antenna"},
            {"id": "fe", "name": "RF Front-End", "type": "receiver"},
            {"id": "mcs", "name": "Mission Control SW", "type": "processor"},
            {"id": "db", "name": "Data Archive", "type": "storage"},
        ],
        connections=[
            {"from": "ant", "to": "fe", "label": "RF"},
            {"from": "fe", "to": "mcs", "label": "TM/TC"},
            {"from": "mcs", "to": "db", "label": "Archive"},
        ],
    ),
    ArchitectureOption(
        id="gnd-ksat", subsystem="ground",
        name="KSAT commercial network",
        description="Kongsberg Satellite Services global network. Professional, high availability, per-pass pricing.",
        mass_kg_typical=0.0, power_w_typical=0.0, cost_keur_typical=200, trl=9,
        pros=["Global coverage", "High availability (>99%)", "Professional operations", "Multi-band support"],
        cons=["High cost (per-pass fees)", "Scheduling required", "Shared infrastructure"],
        derived_requirements=[
            # Performance
            {"id": "SR-GND-001", "level": "system", "type": "performance", "text": "The ground network shall provide >=6 passes per day with global coverage"},
            {"id": "SR-GND-002", "level": "system", "type": "performance", "text": "The ground network shall provide >=99% service availability"},
            {"id": "SR-GND-003", "level": "system", "type": "performance", "text": "The data processing pipeline shall deliver L2 products within 24h of acquisition"},
            # Interface
            {"id": "IR-GND-001", "level": "system", "type": "interface", "text": "The ground station RF shall be compatible with selected spacecraft TTC bands"},
            {"id": "IR-GND-002", "level": "system", "type": "interface", "text": "The MCS shall provide CCSDS-compatible TM/TC processing"},
            {"id": "IR-GND-003", "level": "system", "type": "interface", "text": "The data archive shall provide API access for end users"},
            # Budget
            {"id": "BR-GND-001", "level": "system", "type": "budget", "text": "Ground segment annual operating cost shall not exceed 200 kEUR"},
            # Functional
            {"id": "FR-GND-001", "level": "system", "type": "functional", "text": "The MCS shall support automated pass scheduling and execution"},
            {"id": "FR-GND-002", "level": "system", "type": "functional", "text": "The MCS shall support manual commanding for contingency operations"},
            {"id": "FR-GND-003", "level": "system", "type": "functional", "text": "The ground segment shall perform conjunction screening and collision avoidance analysis"},
        ],
        blocks=[
            {"id": "net", "name": "KSAT Network (20+ stations)", "type": "network"},
            {"id": "scc", "name": "Satellite Control Centre", "type": "processor"},
            {"id": "pipe", "name": "Data Pipeline", "type": "processor"},
            {"id": "api", "name": "User API/Portal", "type": "interface"},
        ],
        connections=[
            {"from": "net", "to": "scc", "label": "TM/TC"},
            {"from": "scc", "to": "pipe", "label": "Data"},
            {"from": "pipe", "to": "api", "label": "Products"},
        ],
    ),
    ArchitectureOption(
        id="gnd-satnogs", subsystem="ground",
        name="SatNOGS community network",
        description="Open-source global ground station network. Free for amateur missions. Community operated.",
        mass_kg_typical=0.0, power_w_typical=0.0, cost_keur_typical=5, trl=8,
        pros=["Free/very low cost", "Global volunteer network", "Open source", "Good for educational missions"],
        cons=["No guaranteed availability", "Volunteer-dependent", "UHF/VHF only typically", "No SLA"],
        derived_requirements=[
            {"id": "SR-GND-001", "level": "system", "text": "The ground segment shall utilise SatNOGS network for UHF telemetry reception"},
            {"id": "SR-GND-002", "level": "system", "text": "The spacecraft shall transmit AX.25 compatible telemetry for community reception"},
        ],
        blocks=[
            {"id": "net", "name": "SatNOGS Network (global)", "type": "network"},
            {"id": "db", "name": "SatNOGS DB", "type": "storage"},
            {"id": "own", "name": "Own Command Station", "type": "processor"},
        ],
        connections=[
            {"from": "net", "to": "db", "label": "TM observations"},
            {"from": "own", "to": "net", "label": "TC (own station only)"},
        ],
    ),
]

# Complete catalogue indexed by subsystem
ARCHITECTURE_CATALOGUE: dict[str, list[ArchitectureOption]] = {
    "eps": EPS_OPTIONS,
    "aocs": AOCS_OPTIONS,
    "ttc": TTC_OPTIONS,
    "thermal": THERMAL_OPTIONS,
    "structure": STRUCTURE_OPTIONS,
    "propulsion": PROPULSION_OPTIONS,
    "obc": OBC_OPTIONS,
    "ground": GROUND_OPTIONS,
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
