"""SpaceCDF — Link Budget Design Agent (Tier 1).

Computes communication link budgets, antenna sizing, and data throughput.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.heritage_mass import calibrate_mass
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
            "link.transponder.equipment_id",
            "link.antenna.equipment_id",
        ]

    def _resolve_from_kb(self, state: DesignState, category: str, param_path: str) -> dict | None:
        """Look up a KB component by equipment_id (SPINE_SPEC §8)."""
        eq_id = state.get(param_path)
        if eq_id and hasattr(state, 'kb') and state.kb is not None:
            component = state.kb.get_component(category, eq_id)
            if component:
                return component.__dict__
        return None

    def output_parameters(self) -> list[str]:
        return [
            "link.downlink_margin_db", "link.downlink_rate_bps",
            "link.data_per_day_gb", "link.ttc_mass_kg",
            "link.ttc_power_w", "link.ttc_cost_keur",
            "link.ttc_margin_db", "link.payload_margin_db",
            "link.uplink_margin_db",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        alt = state.get("orbit.altitude_km", 500.0)
        contact_s = state.get("orbit.contact_time_per_day_s", 1200.0) or 1200.0
        orbit_type = state.get_requirement("orbit.orbit_type")

        # Deep-space missions: slant range is Earth-body distance, not orbital altitude.
        # Override altitude_km so the link budget uses the correct free-space loss.
        _DEEP_SPACE_DISTANCE_KM = {
            "lunar": 384_400.0,
            "mars": 225_000_000.0,        # mean opposition
            "lagrange": 1_500_000.0,       # L2
            "interplanetary": 225_000_000.0,
        }
        is_deep_space = orbit_type in _DEEP_SPACE_DISTANCE_KM
        link_altitude_km = _DEEP_SPACE_DISTANCE_KM.get(orbit_type, alt) if is_deep_space else alt

        # Deep-space missions also get DSN-class ground station and longer contact
        if is_deep_space:
            contact_s = max(contact_s, 8 * 3600)  # 8-hour DSN pass minimum

        sc_class = state.get_requirement("spacecraft_class", "small")
        payload_data_rate_mbps = state.get("payload.0.data_rate_mbps", 0) or 0
        # Band selection driven by class + data-rate need + deep space
        if is_deep_space:
            # Deep-space: X-band with high-gain antenna + DSN 34m or 70m
            freq_ghz, tx_power, gs_diam, tx_gain = 8.4, 15.0, 34.0, 30.0
        elif sc_class == "nano" and payload_data_rate_mbps < 1:
            freq_ghz, tx_power, gs_diam, tx_gain = 0.4, 1.0, 13.0, 2.0   # UHF simple nanosat
        elif sc_class == "nano":
            freq_ghz, tx_power, gs_diam, tx_gain = 8.2, 2.0, 13.0, 6.0   # X-band nanosat
        elif sc_class == "micro":
            freq_ghz, tx_power, gs_diam, tx_gain = 8.2, 8.0, 13.0, 10.0  # X-band microsat (e.g. PROBA-V)
        elif sc_class == "small":
            freq_ghz, tx_power, gs_diam, tx_gain = 8.2, 5.0, 13.0, 10.0  # X-band smallsat
        elif sc_class == "medium":
            freq_ghz, tx_power, gs_diam, tx_gain = 8.2, 10.0, 13.0, 15.0
        else:
            freq_ghz, tx_power, gs_diam, tx_gain = 26.0, 15.0, 13.0, 20.0  # Ka-band

        # --- KB override: transponder datasheet values (SPINE_SPEC §8) ---
        kb_transponder = self._resolve_from_kb(state, "transponders", "link.transponder.equipment_id")
        if kb_transponder:
            tx_power = kb_transponder.get("power_tx_w", tx_power)
            result.log(f"KB transponder: tx_power={tx_power:.1f} W")

        # --- KB override: antenna datasheet values (SPINE_SPEC §8) ---
        kb_antenna = self._resolve_from_kb(state, "antennas", "link.antenna.equipment_id")
        if kb_antenna:
            tx_gain = kb_antenna.get("gain_dbi", tx_gain)
            result.log(f"KB antenna: gain={tx_gain:.1f} dBi")

        # Required operational rate = payload data / contact time (with 20 % margin headroom)
        generated_gb_per_day = state.get("data.generated_per_day_gb", 0) or 0
        if generated_gb_per_day > 0 and contact_s > 0:
            required_rate_bps = (generated_gb_per_day * 8 * 1e9) / contact_s
            # Size with 20% headroom so we don't run at exactly 0 dB
            required_rate_bps *= 1.2
        else:
            required_rate_bps = payload_data_rate_mbps * 1e6 if payload_data_rate_mbps > 0 else 0

        lb = compute_link_budget(
            altitude_km=link_altitude_km,
            tx_power_w=tx_power,
            tx_antenna_gain_dbi=tx_gain,
            frequency_ghz=freq_ghz,
            gs_antenna_diameter_m=gs_diam,
            contact_time_per_day_s=contact_s,
            required_data_rate_bps=required_rate_bps,
            # Deep-space: no atmospheric rain (direct-to-Earth); LEO: clear-sky default
            rain_rate_mm_hr=0.0,
        )

        # --- KB override: mass/cost from datasheet (SPINE_SPEC §8) ---
        if kb_transponder:
            lb.ttc_mass_kg = kb_transponder.get("mass_kg", lb.ttc_mass_kg)
            lb.ttc_cost_keur = kb_transponder.get("cost_keur", lb.ttc_cost_keur)
            result.log(f"KB transponder: mass={lb.ttc_mass_kg:.2f} kg, cost={lb.ttc_cost_keur:.0f} kEUR")
        if kb_antenna:
            # Antenna mass additive to transponder mass
            antenna_mass = kb_antenna.get("mass_kg", 0)
            if antenna_mass:
                lb.ttc_mass_kg += antenna_mass
                result.log(f"KB antenna: added {antenna_mass:.2f} kg to TTC mass")
            antenna_cost = kb_antenna.get("cost_keur", 0)
            if antenna_cost:
                lb.ttc_cost_keur += antenna_cost

        # --- Dual-link model: separate TTC + payload downlink ---
        # TTC link (commanding + housekeeping): always present, low rate, reliable
        if not is_deep_space:
            ttc_freq = 0.4 if sc_class == "nano" else 2.2  # UHF for nano, S-band otherwise
            ttc_power = 1.0 if sc_class == "nano" else 5.0
            ttc_gain_db = 2.0 if sc_class == "nano" else 6.0
            ttc_gs_diam = 13.0
            ttc_lb = compute_link_budget(
                altitude_km=link_altitude_km, tx_power_w=ttc_power,
                tx_antenna_gain_dbi=ttc_gain_db, frequency_ghz=ttc_freq,
                gs_antenna_diameter_m=ttc_gs_diam, contact_time_per_day_s=contact_s,
                required_data_rate_bps=16000,
            )
            ttc_margin = ttc_lb.downlink_margin_db
            # Uplink: ground station transmits to spacecraft (typically 10+ dB margin)
            uplink_margin = ttc_margin + 10  # GS has much higher EIRP
        else:
            ttc_margin = lb.downlink_margin_db
            uplink_margin = ttc_margin + 5  # DSN uplink advantage

        # Payload downlink is the main link budget (already computed as `lb`)
        payload_margin = lb.downlink_margin_db

        result.add_param("link.downlink_margin_db", "Downlink Margin (worst)", round(min(ttc_margin, payload_margin), 1), "dB")
        result.add_param("link.ttc_margin_db", "TTC Margin", round(ttc_margin, 1), "dB")
        result.add_param("link.payload_margin_db", "Payload DL Margin", round(payload_margin, 1), "dB")
        result.add_param("link.uplink_margin_db", "Uplink Margin", round(uplink_margin, 1), "dB")
        result.add_param("link.downlink_rate_bps", "Downlink Data Rate", round(lb.downlink_data_rate_bps, 0), "bps")
        result.add_param("link.data_per_day_gb", "Data Downlinked/Day", round(lb.data_downlinked_per_day_gb, 2), "GB")
        dry_est = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        ttc_mass = calibrate_mass("ttc", lb.ttc_mass_kg, dry_est, sc_class)
        result.add_param("link.ttc_mass_kg", "TTC Mass", round(ttc_mass, 2), "kg", margin_percent=10)
        result.add_param("link.ttc_power_w", "TTC Power", round(lb.ttc_power_w, 1), "W")
        result.add_param("link.ttc_cost_keur", "TTC Cost", round(lb.ttc_cost_keur, 0), "kEUR")

        result.warnings.extend(lb.warnings)
        result.confidence = 0.85
        return result
