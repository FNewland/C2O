"""SpaceCDF — Deterministic Parameter ID Allocator for SMO export.

Allocates hex parameter IDs in the SMO convention:
  0x0100-0x01FF: EPS
  0x0200-0x02FF: AOCS
  0x0300-0x03FF: OBDH
  0x0400-0x04FF: TCS
  0x0500-0x05FF: TTC
  0x0600-0x06FF: Payload

Allocation is deterministic: same DesignState always produces
the same IDs (parameters sorted by ID before allocation).
"""
from __future__ import annotations

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.parameter import ParameterValue

# SpaceCDF domain → SMO subsystem mapping
DOMAIN_TO_SUBSYSTEM = {
    "power": "eps",
    "aocs": "aocs",
    "data": "obdh",
    "thermal": "tcs",
    "link": "ttc",
    "payload": "payload",
    "orbit": "orbital",
    "propulsion": "propulsion",
    "structure": "structure",
    "mass": "eps",  # mass params go into EPS for budget tracking
    "systems": "obdh",
    "cost": "obdh",
    "risk": "obdh",
    "trl": "obdh",
    "mission": "obdh",
    "conflicts": "obdh",
}

# SMO subsystem → hex base
SUBSYSTEM_BASE = {
    "eps": 0x0100,
    "aocs": 0x0200,
    "obdh": 0x0300,
    "tcs": 0x0400,
    "ttc": 0x0500,
    "payload": 0x0600,
    "orbital": 0x0000,
    "propulsion": 0x0700,
    "structure": 0x0800,
}

# Base parameter set — always allocated for each subsystem, in this order
BASE_PARAMS = {
    "eps": [
        ("bat_voltage", "V"), ("bat_soc", "%"), ("bat_temp", "C"),
        ("bus_voltage", "V"), ("power_cons", "W"), ("power_gen", "W"),
        ("eclipse_flag", ""), ("bat_current", "A"),
        ("sa_a_current", "A"), ("sa_b_current", "A"),
    ],
    "aocs": [
        ("att_q1", ""), ("att_q2", ""), ("att_q3", ""), ("att_q4", ""),
        ("rate_roll", "deg/s"), ("rate_pitch", "deg/s"), ("rate_yaw", "deg/s"),
        ("rw1_speed", "RPM"), ("rw2_speed", "RPM"), ("rw3_speed", "RPM"), ("rw4_speed", "RPM"),
        ("aocs_mode", ""), ("att_error", "deg"),
    ],
    "obdh": [
        ("obc_mode", ""), ("cpu_load", "%"), ("mem_used", "%"),
        ("uptime_s", "s"), ("reboot_count", ""),
    ],
    "tcs": [
        ("temp_panel_px", "C"), ("temp_panel_mx", "C"),
        ("temp_panel_py", "C"), ("temp_panel_my", "C"),
        ("temp_panel_pz", "C"), ("temp_panel_mz", "C"),
        ("temp_obc", "C"), ("temp_battery", "C"), ("temp_fpa", "C"),
        ("htr_battery", ""), ("htr_obc", ""),
    ],
    "ttc": [
        ("ttc_mode", ""), ("link_status", ""), ("rssi", "dBm"),
        ("link_margin", "dB"), ("tm_data_rate", "bps"),
        ("xpdr_temp", "C"),
    ],
    "payload": [
        ("pli_mode", ""), ("fpa_temp", "C"), ("cooler_pwr", "W"),
        ("store_used", "%"), ("image_count", ""), ("data_rate", "Mbps"),
    ],
}


class ParamIDAllocator:
    """Allocates deterministic hex parameter IDs for SMO export."""

    def __init__(self):
        self._counters: dict[str, int] = {}
        self._allocations: dict[str, int] = {}  # param_name -> hex_id
        self._param_defs: list[dict] = []  # Full parameter definitions for parameters.yaml

        # Allocate base parameters first
        for subsys, params in BASE_PARAMS.items():
            base = SUBSYSTEM_BASE.get(subsys, 0x0000)
            for i, (name, unit) in enumerate(params):
                hex_id = base + i
                full_name = f"{subsys}.{name}"
                self._allocations[full_name] = hex_id
                self._param_defs.append({
                    "id": hex_id,
                    "name": full_name,
                    "subsystem": subsys,
                    "units": unit,
                    "description": name.replace("_", " ").title(),
                })
            self._counters[subsys] = base + len(params)

    def allocate(self, spacecdf_param_id: str, domain: str, unit: str = "", description: str = "") -> int:
        """Allocate a hex ID for a SpaceCDF parameter."""
        subsys = DOMAIN_TO_SUBSYSTEM.get(domain, "obdh")
        smo_name = f"{subsys}.{spacecdf_param_id.replace('.', '_')}"

        # Check if already allocated
        if smo_name in self._allocations:
            return self._allocations[smo_name]

        # Allocate next ID in subsystem range
        base = SUBSYSTEM_BASE.get(subsys, 0x0300)
        counter = self._counters.get(subsys, base)
        hex_id = counter
        self._counters[subsys] = counter + 1

        self._allocations[smo_name] = hex_id
        self._param_defs.append({
            "id": hex_id,
            "name": smo_name,
            "subsystem": subsys,
            "units": unit,
            "description": description or smo_name,
        })
        return hex_id

    def allocate_from_state(self, state: DesignState) -> dict[str, int]:
        """Allocate IDs for all parameters in the design state."""
        # Sort for determinism
        for param_id in sorted(state.parameters.keys()):
            p = state.parameters[param_id]
            if isinstance(p.value, (int, float)):  # Only numeric params become telemetry
                self.allocate(param_id, p.domain, p.unit, p.name)
        return dict(self._allocations)

    @property
    def param_defs(self) -> list[dict]:
        """Get parameter definitions for parameters.yaml."""
        return sorted(self._param_defs, key=lambda d: d["id"])

    def get_subsystem_params(self, subsystem: str) -> dict[str, int]:
        """Get param_ids dict for a subsystem config (e.g. eps.yaml param_ids)."""
        prefix = f"{subsystem}."
        return {
            name.replace(prefix, ""): hex_id
            for name, hex_id in self._allocations.items()
            if name.startswith(prefix)
        }
