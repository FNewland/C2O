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
            "link.data_per_day_gb",
        ]

    def output_parameters(self) -> list[str]:
        return [
            "data.generated_per_day_gb", "data.downlinked_per_day_gb",
            "data.storage_required_gb", "data.obdh_mass_kg", "data.obdh_cost_keur",
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
                # 2:1 compression assumption for raw-rate-derived estimates
                gen_per_day_gb += (dr / 8000) * dc * 86400 * 0.5
            i += 1

        downlink_per_day = state.get("link.data_per_day_gb", 0) or 0

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

        result.add_param("data.generated_per_day_gb", "Data Generated/Day", round(gen_per_day_gb, 2), "GB")
        result.add_param("data.downlinked_per_day_gb", "Data Downlinked/Day", round(downlink_per_day, 2), "GB")
        result.add_param("data.storage_required_gb", "Storage Required", round(storage_gb, 1), "GB")
        result.add_param("data.obdh_mass_kg", "OBDH Mass", round(obdh_mass, 2), "kg", margin_percent=10)
        result.add_param("data.obdh_cost_keur", "OBDH Cost", round(obdh_mass * 100, 0), "kEUR")

        if gen_per_day_gb > downlink_per_day > 0:
            deficit = gen_per_day_gb - downlink_per_day
            result.add_warning(
                f"Data deficit: generating {gen_per_day_gb:.1f} GB/day but only downlinking "
                f"{downlink_per_day:.1f} GB/day (deficit: {deficit:.1f} GB/day)"
            )

        result.confidence = 0.80
        return result
