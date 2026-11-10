"""SpaceCDF — Data Budget Agent (Tier 1).

Computes data generation, storage requirements, and downlink capacity.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState


class DataAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "data"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return [
            "payload.0.data_rate_mbps", "payload.0.duty_cycle",
            "link.data_per_day_gb", "hk.per_day_gb", "data.compression_ratio",
            # wave 3 (3.H1): the study's data budget (services/data_budget.design_overlay)
            "data.science_on_channel_mb_per_day", "data.capacity_mb_per_day",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "data.generated_per_day_gb", "data.downlinked_per_day_gb",
            "data.storage_required_gb", "data.obdh_mass_kg", "data.obdh_cost_keur",
            "data.phase0_generated_per_day_gb", "data.phase0_delta_gb",
        ]

    def dependencies(self) -> list[str]:
        return ["link"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        # Data generated per day. Prefer the payload lead's explicit
        # data_volume_per_day_gb when provided (it carries instrument-level
        # truth — compression, scheduling, region-of-interest limits); only
        # fall back to a rate × duty × time estimate when absent.
        gen_per_day_gb = 0.0
        i = 0
        while True:
            explicit = state.get(f"payload.{i}.data_volume_per_day_gb")
            dr = state.get(f"payload.{i}.data_rate_mbps")
            if explicit is None and dr is None:
                break
            if explicit is not None and explicit > 0:
                gen_per_day_gb += explicit
            elif dr is not None:
                dc = state.get(f"payload.{i}.duty_cycle", 0.25) or 0.25
                # 2:1 compression assumption for raw-rate-derived estimates (or the study's ratio)
                cr = state.get("data.compression_ratio") or 2.0
                gen_per_day_gb += (dr / 8000) * dc * 86400 / max(float(cr), 1.0)
            i += 1

        # W3.03: housekeeping stored on board and the payload's compression ratio from the data
        # budget (services/data_budget.py) when the study gives them; the 2:1 default otherwise.
        hk_gb = state.get("hk.per_day_gb", 0) or 0
        gen_per_day_gb += hk_gb
        downlink_per_day = state.get("link.data_per_day_gb", 0) or 0

        # Wave 3 (3.H1, A1): one source per quantity. When the study's data budget is in the design
        # state, what goes down the link is the science product set after compression on the
        # channel plus the housekeeping, against the capacity of the union of the passes. The
        # per-payload sum above (frames acquired) stays as the labelled "Phase 0 estimate".
        phase0_gb = gen_per_day_gb
        sci_ch = state.get("data.science_on_channel_mb_per_day")
        study_budget = sci_ch is not None
        if study_budget:
            hk_st = state.get("data.hk_stored_mb_per_day", 0) or 0
            hk_rt = state.get("data.hk_realtime_mb_per_day", 0) or 0
            gen_per_day_gb = (float(sci_ch) + float(hk_st) + float(hk_rt)) / 1000.0
            cap_mb = state.get("data.capacity_mb_per_day")
            if cap_mb is not None:
                downlink_per_day = float(cap_mb) / 1000.0
            result.log(f"Data budget: {sci_ch:.2f} MB/day science on the channel + {hk_st + hk_rt:.2f} MB/day HK "
                       f"against {downlink_per_day * 1000:.2f} MB/day capacity (Phase 0 estimate {phase0_gb:.3f} GB/day)")

        # Storage = buffer for 2 days of data generation
        storage_gb = gen_per_day_gb * 2

        # OBDH mass estimate — strongly dependent on spacecraft class. Historic
        # CubeSat OBDH boards (GomSpace NanoMind, ISISpace iOBC) are 0.05-0.15 kg.
        # References: GomSpace NanoMind A3200 datasheet; ISIS iOBC datasheet.
        # spacecraft_class is a string requirement — must use get_requirement (state.get only returns numerics)
        sc_class = state.get_requirement("spacecraft_class", "small")
        class_factor = {
            "nano":     0.15,   # CubeSat single-board
            "micro":    0.35,
            "small":    1.2,
            "medium":   2.0,
            "large":    3.5,
            "flagship": 6.0,
        }.get(sc_class, 1.2)
        # Scale modestly with storage demand — doubles when storage > 100 GB.
        storage_factor = 1.0 + min(storage_gb / 100.0, 1.5)
        obdh_mass = class_factor * storage_factor

        result.add_param("data.generated_per_day_gb", "Data Generated/Day", round(gen_per_day_gb, 5), "GB")
        result.add_param("data.downlinked_per_day_gb", "Data Downlinked/Day", round(downlink_per_day, 5), "GB")
        result.add_param("data.phase0_generated_per_day_gb", "Data Generated/Day (Phase 0 estimate)", round(phase0_gb, 4), "GB")
        result.add_param("data.phase0_delta_gb", "Phase 0 estimate − study data budget", round(phase0_gb - gen_per_day_gb, 4), "GB")
        result.add_param("data.storage_required_gb", "Storage Required", round(storage_gb, 1), "GB")
        result.add_param("data.obdh_mass_kg", "OBDH Mass", round(obdh_mass, 2), "kg", margin_percent=10)
        result.add_param("data.obdh_cost_keur", "OBDH Cost", round(obdh_mass * 100, 0), "kEUR")

        if gen_per_day_gb > downlink_per_day > 0:
            deficit = gen_per_day_gb - downlink_per_day
            result.add_warning(
                f"Data deficit: generating {gen_per_day_gb * 1000:.1f} MB/day but only downlinking "
                f"{downlink_per_day * 1000:.1f} MB/day (deficit: {deficit * 1000:.1f} MB/day)"
            )

        # ---- Report-quality narrative & structured intermediates ----
        if study_budget:
            result.rationale = (
                f"Data architecture from the study's data budget: {gen_per_day_gb * 1000:.2f} MB/day to downlink "
                f"(science after compression on the channel and housekeeping) against {downlink_per_day * 1000:.2f} MB/day "
                f"of capacity from the union of the passes.  The Phase 0 estimate (payload volumes summed) is "
                f"{phase0_gb:.3f} GB/day; the difference is on-board selection (ROI products) and compression.  "
                f"OBDH mass {obdh_mass:.2f} kg from class factor × storage demand."
            )
        else:
            result.rationale = (
                f"Data architecture sized for {gen_per_day_gb:.1f} GB/day generated "
                f"({downlink_per_day:.1f} GB/day downlinked).  Onboard storage "
                f"{storage_gb:.1f} GB provides 2-orbit redundancy.  OBDH mass "
                f"{obdh_mass:.2f} kg from class factor × storage demand."
            )
        result.assumptions = [
            "2:1 lossless compression when payload data rate is used as input "
            "(explicit per-day volume overrides this).",
            "Storage = 2 × daily generation (operational buffer).",
            "OBDH mass scales with class baseline × (1 + storage/100 GB).",
        ]
        result.extras["data.summary"] = {
            "per_day_gb": gen_per_day_gb,
            "downlink_capacity_gb": downlink_per_day,
            "storage_required_gb": storage_gb,
            "compression_ratio": state.get("data.compression_ratio") or 2.0,
            "hk_per_day_gb": hk_gb,
            "obdh_mass_kg": obdh_mass,
            "source": "study data budget" if study_budget else "Phase 0 estimate",
            "phase0_generated_per_day_gb": phase0_gb,
            "science_raw_mb_per_day": state.get("data.science_raw_mb_per_day"),
            "science_delivered_mb_per_day": state.get("data.science_delivered_mb_per_day"),
        }

        result.confidence = 0.80
        return result
