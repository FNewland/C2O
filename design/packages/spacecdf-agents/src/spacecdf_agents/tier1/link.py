"""SpaceCDF — Link Budget Design Agent (Tier 1).

Computes communication link budgets, antenna sizing, and data throughput.
"""
from __future__ import annotations

import math

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.heritage_mass import calibrate_mass
from spacecdf_common.physics.link_budget import compute_link_budget
from spacecdf_agents.exporters.docs.agent_extras import link_waterfall


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
            # wave 3 (3.H1): the design case and the loop's own estimate beside it
            "link.frequency_ghz", "link.phase0_payload_margin_db", "link.phase0_data_per_day_gb",
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

        # --- Mission definition override (Nov 2026): the link the team chose ---
        # ``requirements.link`` (mission editor / link-budget tool "Apply to Design") beats the
        # class defaults and the KB datasheet values above.
        link_req = state.get_requirement("link") or {}
        if isinstance(link_req, dict) and not is_deep_space:
            def _pos(key: str) -> float | None:
                v = link_req.get(key)
                return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 else None
            if _pos("downlink_frequency_mhz"):
                freq_ghz = _pos("downlink_frequency_mhz") / 1000.0
            if _pos("tx_power_w"):
                tx_power = _pos("tx_power_w")
            if link_req.get("tx_antenna_gain_dbi") is not None:
                tx_gain = float(link_req["tx_antenna_gain_dbi"])
            if link_req.get("rx_antenna_gain_dbi") is not None:
                # G = eta (pi D / lambda)^2, eta = 0.55 (compute_link_budget's assumption)
                lam = 0.299792458 / freq_ghz
                g_lin = 10 ** (float(link_req["rx_antenna_gain_dbi"]) / 10.0)
                gs_diam = max(0.1, lam / math.pi * math.sqrt(g_lin / 0.55))
            if _pos("downlink_rate_bps"):
                required_rate_bps = _pos("downlink_rate_bps")
            result.log(f"Mission link: {freq_ghz * 1000:.1f} MHz, {tx_power:.1f} W, {tx_gain:.1f} dBi, "
                       f"{required_rate_bps:.0f} bit/s")

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
        phase0_margin = payload_margin

        # Wave 3 (3.H1, A1): the study's design link case (link-budget tool → "Apply to design",
        # ``requirements.link.margin_db``) is the margin of record; with one radio for TT&C and
        # payload data (a UHF CubeSat) the TT&C channel is the same link. The parametric value
        # stays beside it as the "Phase 0 estimate".
        design_case = None
        if isinstance(link_req, dict) and not is_deep_space:
            m = link_req.get("margin_db")
            if isinstance(m, (int, float)) and not isinstance(m, bool):
                design_case = float(m)
        if design_case is not None:
            payload_margin = design_case
            if freq_ghz < 1.0:
                ttc_margin = design_case
                um = link_req.get("uplink_margin_db")
                uplink_margin = float(um) if isinstance(um, (int, float)) and not isinstance(um, bool) else uplink_margin
            result.log(f"Design link case: {design_case:+.2f} dB (Phase 0 estimate {phase0_margin:+.2f} dB)")

        result.add_param("link.downlink_margin_db", "Downlink Margin (worst)", round(min(ttc_margin, payload_margin), 1), "dB")
        result.add_param("link.ttc_margin_db", "TTC Margin", round(ttc_margin, 1), "dB")
        result.add_param("link.payload_margin_db", "Payload DL Margin", round(payload_margin, 1), "dB")
        result.add_param("link.uplink_margin_db", "Uplink Margin", round(uplink_margin, 1), "dB")
        result.add_param("link.downlink_rate_bps", "Downlink Data Rate", round(lb.downlink_data_rate_bps, 0), "bps")
        # W3.03: when the study designs its link framing (TM/TC → link_framing: RS coding, transfer frame,
        # SDLS), the daily volume uses that frame efficiency instead of the generic 10 % protocol overhead.
        per_day_gb = lb.data_downlinked_per_day_gb
        frame_eff = state.get("link.frame_efficiency")
        if frame_eff and 0 < frame_eff <= 1:
            per_day_gb = per_day_gb / 0.9 * float(frame_eff)
        phase0_per_day = per_day_gb
        cap_mb = state.get("data.capacity_mb_per_day")
        if cap_mb is not None:      # wave 3: the data budget's capacity (union, framing, acquisition, availability)
            per_day_gb = float(cap_mb) / 1000.0
        result.add_param("link.data_per_day_gb", "Data Downlinked/Day", round(per_day_gb, 5), "GB")
        result.add_param("link.frequency_ghz", "Downlink Frequency", round(freq_ghz, 4), "GHz")
        result.add_param("link.phase0_payload_margin_db", "Payload DL Margin (Phase 0 estimate)", round(phase0_margin, 1), "dB")
        result.add_param("link.phase0_data_per_day_gb", "Data Downlinked/Day (Phase 0 estimate)", round(phase0_per_day, 4), "GB")
        dry_est = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        ttc_mass = calibrate_mass("ttc", lb.ttc_mass_kg, dry_est, sc_class)
        result.add_param("link.ttc_mass_kg", "TTC Mass", round(ttc_mass, 2), "kg", margin_percent=10)
        result.add_param("link.ttc_power_w", "TTC Power", round(lb.ttc_power_w, 1), "W")
        result.add_param("link.ttc_cost_keur", "TTC Cost", round(lb.ttc_cost_keur, 0), "kEUR")

        result.warnings.extend(lb.warnings)

        # ---- Report-quality narrative & structured intermediates ----
        result.rationale = (
            f"Communications architecture is a dual link: an always-on "
            f"{'UHF' if sc_class == 'nano' else 'S-band'} TT&C channel for command and "
            f"housekeeping (margin {ttc_margin:.1f} dB) and a higher-rate "
            f"{lb.band} payload downlink at {freq_ghz:.1f} GHz "
            f"(margin {payload_margin:.1f} dB).  EIRP is "
            f"{lb.downlink_eirp_dbw:.1f} dBW; free-space loss is "
            f"{lb.free_space_loss_db:.1f} dB at the worst-case slant range of "
            f"{lb.slant_range_km:.0f} km."
        )
        if design_case is not None:
            result.rationale = (
                f"Link margin of record from the study's design link case: {design_case:+.1f} dB at "
                f"{freq_ghz * 1000:.1f} MHz, {tx_power:.1f} W ({link_req.get('source') or 'link-budget tool'}).  "
                f"The parametric Phase 0 estimate is {phase0_margin:+.1f} dB; the difference is the station, "
                f"the noise temperature and the losses the team entered term by term.  Daily volume "
                f"{per_day_gb * 1000:.2f} MB/day from the union of the passes."
            )
        result.assumptions = [
            f"{lb.elevation_deg:.0f}° minimum elevation; ITU-R P.676/P.618 atmospheric model.",
            f"GS antenna {gs_diam:.1f} m, efficiency 0.55, system noise temperature 200 K.",
            f"Modulation coding rate 0.5, protocol overhead 10%, implementation loss 2 dB.",
            f"Required Eb/N0 10 dB for BER 10⁻⁶ at the assumed modulation.",
        ]

        # GS antenna gain (recomputed for the waterfall display)
        wavelength_m = 299792458.0 / (freq_ghz * 1e9)
        gs_gain_dbi = 10 * math.log10(
            0.55 * (math.pi * gs_diam / wavelength_m) ** 2
        )
        rb_db = 10 * math.log10(max(lb.downlink_data_rate_bps, 1))

        result.extras["link.waterfall"] = link_waterfall(
            ("Tx power (dBW)", 10 * math.log10(max(tx_power, 1e-6))),
            ("Tx antenna gain", tx_gain),
            ("Tx line loss", -1.0),
            ("Free-space loss", -lb.free_space_loss_db),
            ("Atmospheric gas", -lb.atmos_gas_loss_db),
            ("Rain", -lb.atmos_rain_loss_db),
            ("Polarisation", -lb.polarisation_loss_db),
            ("Pointing", -lb.pointing_loss_db),
            ("GS antenna gain", gs_gain_dbi),
            ("Boltzmann (k)", -(-228.6)),  # +228.6
            ("System noise T", -10 * math.log10(200)),
            ("Data rate", -rb_db),
            ("Required Eb/N0", -10.0),
            ("Implementation loss", -2.0),
        )
        result.extras["link.summary"] = {
            "band": lb.band,
            "frequency_ghz": lb.frequency_ghz,
            "tx_power_w": tx_power,
            "tx_antenna_gain_dbi": tx_gain,
            "gs_antenna_diameter_m": gs_diam,
            "gs_antenna_gain_dbi": gs_gain_dbi,
            "slant_range_km": lb.slant_range_km,
            "data_rate_bps": lb.downlink_data_rate_bps,
            "data_per_day_gb": lb.data_downlinked_per_day_gb,
            "downlink_margin_db": payload_margin,
            "ttc_margin_db": ttc_margin,
            "uplink_margin_db": uplink_margin,
            "is_deep_space": is_deep_space,
            "source": "design link case" if design_case is not None else "Phase 0 estimate",
            "phase0_payload_margin_db": phase0_margin,
            "phase0_data_per_day_gb": phase0_per_day,
        }

        result.confidence = 0.85
        return result
