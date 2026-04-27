"""SpaceCDF — Volume Budget Agent (Tier 2).

Estimates subsystem volumes and checks against bus envelope.
Flags volume overflows as conflicts.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


# Typical subsystem density (kg/litre) for volume estimation
_DENSITY: dict[str, float] = {
    "eps":        1.5,   # Batteries are dense; SA are not (but external)
    "aocs":       2.0,   # Reaction wheels, gyros
    "ttc":        1.8,   # Transponder + antenna feed
    "obdh":       1.2,   # Electronics boards
    "tcs":        0.8,   # MLI + radiators (low density)
    "propulsion": 1.0,   # Tanks dominate (low fill density)
    "structure":  0.0,   # Structure IS the bus envelope — not counted
    "payload":    1.5,   # Generic instrument
}

# Bus volume envelope by spacecraft class (litres)
_BUS_VOLUME: dict[str, float] = {
    "nano":     6.0,      # 3U = 3000 cm³ usable ≈ 3 L; 6U = 6 L
    "micro":    80.0,     # ~80×80×80 cm cube interior
    "small":    400.0,    # ~1m cube
    "medium":   2000.0,
    "large":    8000.0,
    "flagship": 30000.0,
}


class VolumeAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "volume"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return [
            "power.eps_mass_kg", "aocs.mass_kg", "link.ttc_mass_kg",
            "data.obdh_mass_kg", "thermal.tcs_mass_kg",
            "propulsion.total_mass_kg", "mass.payload_kg",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "volume.total_litres", "volume.bus_envelope_litres",
            "volume.utilisation_percent", "volume.margin_litres",
        ]

    def dependencies(self) -> list[str]:
        return ["power", "aocs", "link", "data", "thermal", "propulsion", "mass"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)
        sc_class = state.get_requirement("spacecraft_class", "small")

        # Estimate volume from mass × density
        subsystems = {
            "eps":        state.get("power.eps_mass_kg", 0) or 0,
            "aocs":       state.get("aocs.mass_kg", 0) or 0,
            "ttc":        state.get("link.ttc_mass_kg", 0) or 0,
            "obdh":       state.get("data.obdh_mass_kg", 0) or 0,
            "tcs":        state.get("thermal.tcs_mass_kg", 0) or 0,
            "propulsion": state.get("propulsion.total_mass_kg", 0) or 0,
            "payload":    state.get("mass.payload_kg", 0) or 0,
        }

        total_vol = 0.0
        for sub, mass in subsystems.items():
            density = _DENSITY.get(sub, 1.5)
            if density > 0 and mass > 0:
                total_vol += mass / density

        bus_vol = _BUS_VOLUME.get(sc_class, 400.0)
        utilisation = (total_vol / bus_vol * 100) if bus_vol > 0 else 0
        margin = bus_vol - total_vol

        result.add_param("volume.total_litres", "Total Equipment Volume", round(total_vol, 1), "L")
        result.add_param("volume.bus_envelope_litres", "Bus Envelope", round(bus_vol, 0), "L")
        result.add_param("volume.utilisation_percent", "Volume Utilisation", round(utilisation, 1), "%")
        result.add_param("volume.margin_litres", "Volume Margin", round(margin, 1), "L")

        if utilisation > 90:
            result.add_warning(f"Volume utilisation {utilisation:.0f}% — bus is nearly full")
        if margin < 0:
            result.add_warning(f"Volume OVERFLOW: {-margin:.1f} L over bus envelope — need larger bus or volume reduction")

        result.confidence = 0.60
        return result
