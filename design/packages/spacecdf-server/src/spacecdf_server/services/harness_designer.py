"""SpaceCDF — CubeSat Harness Designer.

Given selected components and their declared interfaces, generates the
signal-level wiring plan: which bus protocol connects which components,
connector assignments, cable routing, harness mass estimate, and EMC
compatibility check.

Stage 3 of the CubeSat full lifecycle capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Standard CubeSat bus protocols with physical characteristics
BUS_SPECS: dict[str, dict[str, Any]] = {
    "I2C": {
        "type": "serial_bus", "topology": "multi-drop", "max_devices": 127,
        "data_rate_bps": 400_000, "voltage_v": 3.3,
        "wire_count": 4, "wires": ["SDA", "SCL", "VCC", "GND"],
        "connector": "Hirose DF13 or PC/104 stack",
        "cable_mass_per_m_g": 8, "max_length_m": 0.5,
    },
    "SPI": {
        "type": "serial_bus", "topology": "star", "max_devices": 8,
        "data_rate_bps": 10_000_000, "voltage_v": 3.3,
        "wire_count": 6, "wires": ["MOSI", "MISO", "SCK", "CS", "VCC", "GND"],
        "connector": "Hirose DF13",
        "cable_mass_per_m_g": 10, "max_length_m": 0.3,
    },
    "CAN": {
        "type": "field_bus", "topology": "bus", "max_devices": 32,
        "data_rate_bps": 1_000_000, "voltage_v": 3.3,
        "wire_count": 4, "wires": ["CANH", "CANL", "VCC", "GND"],
        "connector": "Micro-D or PC/104 stack",
        "cable_mass_per_m_g": 8, "max_length_m": 1.0,
    },
    "UART": {
        "type": "serial_point", "topology": "point-to-point", "max_devices": 2,
        "data_rate_bps": 115_200, "voltage_v": 3.3,
        "wire_count": 4, "wires": ["TX", "RX", "VCC", "GND"],
        "connector": "Hirose DF13",
        "cable_mass_per_m_g": 8, "max_length_m": 0.5,
    },
    "RS422": {
        "type": "serial_differential", "topology": "point-to-point", "max_devices": 2,
        "data_rate_bps": 10_000_000, "voltage_v": 5.0,
        "wire_count": 6, "wires": ["TX+", "TX-", "RX+", "RX-", "VCC", "GND"],
        "connector": "Micro-D 9-pin",
        "cable_mass_per_m_g": 12, "max_length_m": 1.0,
    },
    "SpaceWire": {
        "type": "network", "topology": "point-to-point", "max_devices": 2,
        "data_rate_bps": 200_000_000, "voltage_v": 3.3,
        "wire_count": 10, "wires": ["D+", "D-", "S+", "S-", "VCC", "GND", "TimeCd+", "TimeCd-", "Shield", "Shield"],
        "connector": "Micro-D 9-pin",
        "cable_mass_per_m_g": 18, "max_length_m": 1.0,
    },
    "LVDS": {
        "type": "serial_differential", "topology": "point-to-point", "max_devices": 2,
        "data_rate_bps": 655_000_000, "voltage_v": 3.3,
        "wire_count": 4, "wires": ["D+", "D-", "CLK+", "CLK-"],
        "connector": "Micro-D or board-to-board",
        "cable_mass_per_m_g": 10, "max_length_m": 0.3,
    },
    "PC/104": {
        "type": "stack_bus", "topology": "stack", "max_devices": 12,
        "data_rate_bps": 0,  # carries multiple protocols
        "voltage_v": [3.3, 5.0, 12.0],
        "wire_count": 104, "wires": ["104-pin stack connector"],
        "connector": "PC/104 104-pin",
        "cable_mass_per_m_g": 0, "max_length_m": 0,  # no cable — direct stack
    },
}


@dataclass
class WireConnection:
    """A single wire/signal connection between two components."""
    signal_name: str
    protocol: str
    from_component: str
    to_component: str
    connector_type: str
    cable_length_m: float
    cable_mass_g: float


@dataclass
class InterfaceLink:
    """A logical link between two components using a specific protocol."""
    protocol: str
    component_a: str
    component_b: str
    purpose: str
    wires: list[WireConnection] = field(default_factory=list)
    is_pc104_stack: bool = False
    emc_compatible: bool = True
    emc_note: str = ""


@dataclass
class HarnessDesign:
    """Complete harness design for a CubeSat."""
    links: list[InterfaceLink] = field(default_factory=list)
    total_mass_g: float = 0.0
    total_wire_count: int = 0
    total_connections: int = 0
    pc104_stack_count: int = 0
    external_cable_count: int = 0
    emc_warnings: list[str] = field(default_factory=list)
    icd_entries: list[dict[str, Any]] = field(default_factory=list)


def design_harness(
    selected_components: dict[str, dict[str, Any]],
    form_factor: str = "3U",
) -> HarnessDesign:
    """Generate a harness design from selected CubeSat components.

    Determines which bus protocols connect which components, estimates
    cable lengths and masses, and checks EMC compatibility.
    """
    harness = HarnessDesign()

    # Extract all components with their interfaces
    comp_interfaces: dict[str, list[str]] = {}
    for category, comp in selected_components.items():
        name = comp.get("name", category)
        interfaces = comp.get("interfaces", [])
        comp_interfaces[name] = interfaces

    # Determine the primary data bus
    # Priority: CAN (robust, multi-drop) > I2C (simple) > SPI (fast, point-to-point)
    all_interfaces = set()
    for ifaces in comp_interfaces.values():
        all_interfaces.update(ifaces)

    primary_bus = "I2C"  # Default
    if "CAN" in all_interfaces:
        can_count = sum(1 for ifaces in comp_interfaces.values() if "CAN" in ifaces)
        if can_count >= 3:
            primary_bus = "CAN"
    if "SpaceWire" in all_interfaces:
        sw_count = sum(1 for ifaces in comp_interfaces.values() if "SpaceWire" in ifaces)
        if sw_count >= 2:
            primary_bus = "SpaceWire"

    # Estimate cable lengths based on form factor
    stack_height_mm = {"1U": 80, "3U": 250, "6U": 250, "12U": 250}.get(form_factor, 250)
    avg_cable_m = stack_height_mm / 1000 * 0.5  # Average half the stack height

    # Generate links
    obc_name = None
    eps_name = None
    for cat, comp in selected_components.items():
        if cat == "obcs":
            obc_name = comp.get("name", "OBC")
        elif cat == "eps_boards":
            eps_name = comp.get("name", "EPS")

    if not obc_name:
        obc_name = "OBC"
    if not eps_name:
        eps_name = "EPS"

    # Power distribution: EPS → every component
    for cat, comp in selected_components.items():
        if cat == "eps_boards":
            continue
        name = comp.get("name", cat)
        link = InterfaceLink(
            protocol="Power",
            component_a=eps_name,
            component_b=name,
            purpose=f"Power supply to {name}",
        )
        if "PC/104" in comp.get("interfaces", []):
            link.is_pc104_stack = True
            link.wires = []  # Via stack connector
        else:
            cable_m = avg_cable_m
            mass_g = cable_m * 12  # Power cables heavier
            link.wires = [
                WireConnection("VCC", "Power", eps_name, name, "Molex Pico-Blade", cable_m, mass_g / 2),
                WireConnection("GND", "Power", eps_name, name, "Molex Pico-Blade", cable_m, mass_g / 2),
            ]
            harness.total_mass_g += mass_g
        harness.links.append(link)

    # Data bus: OBC → each component that shares a protocol
    for cat, comp in selected_components.items():
        if cat in ("obcs", "eps_boards", "cubesat_structures", "deployers"):
            continue
        name = comp.get("name", cat)
        comp_ifaces = comp.get("interfaces", [])

        # Find shared protocol with OBC
        obc_ifaces = selected_components.get("obcs", {}).get("interfaces", [])
        shared = [p for p in [primary_bus, "I2C", "SPI", "UART", "CAN"] if p in comp_ifaces and p in obc_ifaces]

        if not shared:
            shared = [p for p in comp_ifaces if p in obc_ifaces]

        protocol = shared[0] if shared else primary_bus

        link = InterfaceLink(
            protocol=protocol,
            component_a=obc_name,
            component_b=name,
            purpose=f"Data/command: {obc_name} ↔ {name}",
        )

        bus_spec = BUS_SPECS.get(protocol, BUS_SPECS["I2C"])

        if protocol == "PC/104" or ("PC/104" in comp_ifaces and "PC/104" in obc_ifaces):
            link.is_pc104_stack = True
            link.protocol = f"{protocol} via PC/104 stack"
            harness.pc104_stack_count += 1
        else:
            cable_m = avg_cable_m
            mass_g = cable_m * bus_spec.get("cable_mass_per_m_g", 8)
            wire_count = bus_spec.get("wire_count", 4)
            for wire_name in bus_spec.get("wires", [])[:wire_count]:
                link.wires.append(WireConnection(
                    wire_name, protocol, obc_name, name,
                    bus_spec.get("connector", "Hirose DF13"),
                    cable_m, mass_g / wire_count,
                ))
            harness.total_mass_g += mass_g
            harness.external_cable_count += 1
            harness.total_wire_count += wire_count

        harness.links.append(link)
        harness.total_connections += 1

    # EMC check: does the TX frequency interfere with any sensitive detector?
    tx_freqs = []
    sensitive_detectors = []
    for cat, comp in selected_components.items():
        perf = comp.get("performance", {})
        freq = perf.get("frequency_mhz")
        if freq and cat in ("transponders",):
            tx_freqs.append((comp.get("name", cat), freq))
        if cat in ("star_trackers", "sun_sensors"):
            sensitive_detectors.append(comp.get("name", cat))

    for tx_name, freq in tx_freqs:
        for det_name in sensitive_detectors:
            if freq > 1000:  # S-band and above near optical detectors
                harness.emc_warnings.append(
                    f"EMC: {tx_name} ({freq} MHz) may interfere with {det_name} — "
                    f"ensure physical separation or RF shielding"
                )

    # Generate ICD entries
    for link in harness.links:
        if link.is_pc104_stack:
            continue
        harness.icd_entries.append({
            "interface_id": f"ICD-{link.component_a[:3]}-{link.component_b[:3]}",
            "component_a": link.component_a,
            "component_b": link.component_b,
            "protocol": link.protocol,
            "purpose": link.purpose,
            "connector_a": link.wires[0].connector_type if link.wires else "PC/104",
            "connector_b": link.wires[0].connector_type if link.wires else "PC/104",
            "wire_count": len(link.wires),
            "cable_length_m": link.wires[0].cable_length_m if link.wires else 0,
            "signals": [w.signal_name for w in link.wires],
        })

    return harness


def harness_summary(harness: HarnessDesign) -> dict[str, Any]:
    """Generate a summary report from a harness design."""
    return {
        "total_links": len(harness.links),
        "pc104_stack_connections": harness.pc104_stack_count,
        "external_cables": harness.external_cable_count,
        "total_wires": harness.total_wire_count,
        "harness_mass_g": round(harness.total_mass_g, 1),
        "harness_mass_kg": round(harness.total_mass_g / 1000, 3),
        "emc_warnings": harness.emc_warnings,
        "icd_count": len(harness.icd_entries),
        "icds": harness.icd_entries,
    }
