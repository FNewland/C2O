"""SpaceCDF — Link Budget Design Agent (Tier 1).

Computes communication link budgets, antenna sizing, and data throughput.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.link_budget import compute_link_budget


class LinkAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "link"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return [
            "orbit.altitude_km",
            "orbit.contact_time_per_day_s",
            "data.generated_per_day_gb",
            "payload.0.data_rate_mbps",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "link.downlink_margin_db", "link.downlink_rate_bps",
            "link.data_per_day_gb", "link.ttc_mass_kg",
            "link.ttc_power_w", "link.ttc_cost_keur",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        alt = state.get("orbit.altitude_km", 500.0)
        contact_s = state.get("orbit.contact_time_per_day_s", 1200.0) or 1200.0

        sc_class = state.get_requirement("spacecraft_class", "small")
        payload_data_rate_mbps = state.get("payload.0.data_rate_mbps", 0) or 0
        # Band selection driven by class + data-rate need
        if sc_class == "nano" and payload_data_rate_mbps < 1:
            freq_ghz, tx_power, gs_diam, tx_gain = 0.4, 1.0, 13.0, 2.0   # UHF simple nanosat
        elif sc_class in ("nano", "micro"):
            freq_ghz, tx_power, gs_diam, tx_gain = 8.2, 2.0, 13.0, 6.0   # X-band nanosat
        elif sc_class == "small":
            freq_ghz, tx_power, gs_diam, tx_gain = 8.2, 5.0, 13.0, 10.0  # X-band smallsat
        elif sc_class == "medium":
            freq_ghz, tx_power, gs_diam, tx_gain = 8.2, 10.0, 13.0, 15.0
        else:
            freq_ghz, tx_power, gs_diam, tx_gain = 26.0, 15.0, 13.0, 20.0  # Ka-band

        # Required operational rate = payload data / contact time (with 20 % margin headroom)
        generated_gb_per_day = state.get("data.generated_per_day_gb", 0) or 0
        if generated_gb_per_day > 0 and contact_s > 0:
            required_rate_bps = (generated_gb_per_day * 8 * 1e9) / contact_s
            # Size with 20% headroom so we don't run at exactly 0 dB
            required_rate_bps *= 1.2
        else:
            required_rate_bps = payload_data_rate_mbps * 1e6 if payload_data_rate_mbps > 0 else 0

        lb = compute_link_budget(
            altitude_km=alt,
            tx_power_w=tx_power,
            tx_antenna_gain_dbi=tx_gain,
            frequency_ghz=freq_ghz,
            gs_antenna_diameter_m=gs_diam,
            contact_time_per_day_s=contact_s,
            required_data_rate_bps=required_rate_bps,
            # Clear-sky design point by default — caller can override for worst-case
            rain_rate_mm_hr=0.0,
        )

        result.add_param("link.downlink_margin_db", "Downlink Margin", round(lb.downlink_margin_db, 1), "dB")
        result.add_param("link.downlink_rate_bps", "Downlink Data Rate", round(lb.downlink_data_rate_bps, 0), "bps")
        result.add_param("link.data_per_day_gb", "Data Downlinked/Day", round(lb.data_downlinked_per_day_gb, 2), "GB")
        result.add_param("link.ttc_mass_kg", "TTC Mass", round(lb.ttc_mass_kg, 2), "kg", margin_percent=10)
        result.add_param("link.ttc_power_w", "TTC Power", round(lb.ttc_power_w, 1), "W")
        result.add_param("link.ttc_cost_keur", "TTC Cost", round(lb.ttc_cost_keur, 0), "kEUR")

        result.warnings.extend(lb.warnings)
        result.confidence = 0.85
        return result
