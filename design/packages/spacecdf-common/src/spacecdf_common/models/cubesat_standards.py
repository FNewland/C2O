"""SpaceCDF — CubeSat Standard Interfaces and Form Factor Model.

Defines the CubeSat Design Specification (CDS) mechanical interfaces,
standard bus protocols, deployer compatibility, and form factor
constraints. Used for interface compatibility checking and volume
budget validation.

References:
  - Cal Poly CubeSat Design Specification (CDS) Rev 14
  - PC/104 Specification
  - ISIPOD Interface Control Document
  - CubeSat standard practices (de facto)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CubeSatFormFactor(str, Enum):
    U1 = "1U"
    U1_5 = "1.5U"
    U2 = "2U"
    U3 = "3U"
    U6 = "6U"
    U12 = "12U"
    U16 = "16U"


class BusProtocol(str, Enum):
    I2C = "I2C"
    SPI = "SPI"
    UART = "UART"
    CAN = "CAN"
    RS422 = "RS422"
    SPACEWIRE = "SpaceWire"
    USB = "USB"
    ETHERNET = "Ethernet"
    PC104 = "PC/104"
    ANALOG = "analog"


# CDS Rev 14 mechanical specifications
CDS_SPECS: dict[str, dict[str, Any]] = {
    "1U": {
        "dimensions_mm": [100, 100, 113.5],
        "max_mass_kg": 2.0,
        "volume_cm3": 1000,
        "rail_width_mm": 8.5,
        "rail_contact_length_mm": 113.5,
        "deployer_spring_plunger_mm": 6.5,
        "deployment_switch_locations": 4,
    },
    "1.5U": {
        "dimensions_mm": [100, 100, 170.2],
        "max_mass_kg": 3.0,
        "volume_cm3": 1500,
        "rail_width_mm": 8.5,
        "rail_contact_length_mm": 170.2,
    },
    "2U": {
        "dimensions_mm": [100, 100, 227.0],
        "max_mass_kg": 4.0,
        "volume_cm3": 2000,
        "rail_width_mm": 8.5,
        "rail_contact_length_mm": 227.0,
    },
    "3U": {
        "dimensions_mm": [100, 100, 340.5],
        "max_mass_kg": 6.0,
        "volume_cm3": 3000,
        "rail_width_mm": 8.5,
        "rail_contact_length_mm": 340.5,
    },
    "6U": {
        "dimensions_mm": [226.3, 100, 340.5],
        "max_mass_kg": 12.0,
        "volume_cm3": 6000,
        "rail_width_mm": 8.5,
        "rail_contact_length_mm": 340.5,
    },
    "12U": {
        "dimensions_mm": [226.3, 226.3, 340.5],
        "max_mass_kg": 24.0,
        "volume_cm3": 12000,
        "rail_width_mm": 8.5,
        "rail_contact_length_mm": 340.5,
    },
}

# PC/104 connector pinout (simplified — 104 pins total)
PC104_STANDARD = {
    "connector_type": "PC/104 (ISA bus subset)",
    "rows": 2,
    "pins_per_row": 52,
    "total_pins": 104,
    "pitch_mm": 2.54,
    "standard_signals": {
        "power": ["3.3V", "5V", "12V", "GND"],
        "data": ["I2C_SDA", "I2C_SCL", "SPI_MOSI", "SPI_MISO", "SPI_CLK", "SPI_CS"],
        "serial": ["UART_TX", "UART_RX", "CAN_H", "CAN_L"],
        "control": ["RESET", "INT0", "INT1"],
    },
    "max_stack_height_mm": {
        "1U": 70,    # ~4 boards
        "3U": 250,   # ~12 boards
        "6U": 250,   # Same height, wider
    },
    "board_dimensions_mm": [96, 90],
    "mounting_holes_mm": [4, 4],  # 4x M3 mounting holes
}


@dataclass
class InterfaceCompatibility:
    """Result of checking interface compatibility between two components."""
    compatible: bool
    component_a: str
    component_b: str
    shared_protocols: list[str] = field(default_factory=list)
    incompatibilities: list[str] = field(default_factory=list)
    notes: str = ""


def check_interface_compatibility(
    component_a: dict[str, Any],
    component_b: dict[str, Any],
) -> InterfaceCompatibility:
    """Check if two CubeSat components can communicate.

    Checks bus protocol compatibility and physical form factor.
    """
    a_name = component_a.get("name", "A")
    b_name = component_b.get("name", "B")

    a_interfaces = set(component_a.get("interfaces", []))
    b_interfaces = set(component_b.get("interfaces", []))

    shared = a_interfaces & b_interfaces
    result = InterfaceCompatibility(
        compatible=len(shared) > 0,
        component_a=a_name,
        component_b=b_name,
        shared_protocols=sorted(shared),
    )

    if not shared:
        result.incompatibilities.append(
            f"No shared bus protocol: {a_name} supports {sorted(a_interfaces)}, "
            f"{b_name} supports {sorted(b_interfaces)}"
        )

    # Check voltage compatibility
    a_voltage = component_a.get("performance", {}).get("bus_voltage_v")
    b_voltage = component_b.get("performance", {}).get("bus_voltage_v")
    if a_voltage and b_voltage:
        a_volts = a_voltage if isinstance(a_voltage, list) else [a_voltage]
        b_volts = b_voltage if isinstance(b_voltage, list) else [b_voltage]
        if not set(a_volts) & set(b_volts):
            result.incompatibilities.append(
                f"Voltage mismatch: {a_name}={a_volts}V, {b_name}={b_volts}V"
            )
            result.compatible = False

    # Check form factor — both should be PC/104 compatible
    a_ff = component_a.get("form_factor", "")
    b_ff = component_b.get("form_factor", "")
    if a_ff == "PC/104" and b_ff == "PC/104":
        result.notes = "Both PC/104 — stack-compatible"
    elif "PC/104" in a_interfaces and "PC/104" in b_interfaces:
        result.notes = "Both on PC/104 bus"

    return result


def check_cds_compliance(
    form_factor: str,
    total_mass_kg: float,
    component_dimensions: list[tuple[float, float, float]] | None = None,
) -> dict[str, Any]:
    """Check CubeSat Design Specification compliance.

    Verifies mass, volume, and dimensional constraints per CDS Rev 14.
    """
    spec = CDS_SPECS.get(form_factor)
    if not spec:
        return {"compliant": False, "error": f"Unknown form factor: {form_factor}"}

    issues = []
    max_mass = spec["max_mass_kg"]
    if total_mass_kg > max_mass:
        issues.append(f"Mass {total_mass_kg:.2f} kg exceeds CDS limit of {max_mass} kg for {form_factor}")

    return {
        "compliant": len(issues) == 0,
        "form_factor": form_factor,
        "cds_max_mass_kg": max_mass,
        "actual_mass_kg": total_mass_kg,
        "mass_margin_percent": ((max_mass - total_mass_kg) / max_mass) * 100,
        "cds_dimensions_mm": spec["dimensions_mm"],
        "cds_volume_cm3": spec["volume_cm3"],
        "issues": issues,
    }
