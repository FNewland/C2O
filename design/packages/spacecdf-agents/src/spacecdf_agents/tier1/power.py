"""SpaceCDF — Power Design Agent (Tier 1).

Computes power budget, solar array sizing, and battery sizing.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.physics.heritage_mass import calibrate_mass, estimate_sa_power_needed
from spacecdf_common.physics.power import compute_power_budget


class PowerAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "power"

    @property
    def tier(self) -> int:
        return 1

    def input_parameters(self) -> list[str]:
        return [
            "orbit.eclipse_fraction", "orbit.sunlight_fraction", "orbit.period_s",
            "payload.0.power_w", "payload.0.duty_cycle",
            "thermal.heater_power_w",
            "mission.duration_years",
            "power.battery.equipment_id",
            "power.solar_array.cell_equipment_id",
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
            "power.sa_area_m2", "power.sa_power_bol_w", "power.sa_power_eol_w",
            "power.sa_mass_kg", "power.battery_capacity_wh", "power.battery_mass_kg",
            "power.total_sunlight_w", "power.total_eclipse_w",
            "power.eps_mass_kg", "power.eps_cost_keur",
        ]

    def dependencies(self) -> list[str]:
        return ["orbit"]  # Needs eclipse fraction from orbit agent

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)

        eclipse_frac = state.get("orbit.eclipse_fraction", 0.35)
        sunlight_frac = state.get("orbit.sunlight_fraction", 0.65)
        period_s = state.get("orbit.period_s", 5700.0)
        mission_years = state.get("mission.duration_years", 3.0)

        # --- ConOps-driven power budget (if modes are defined) ---
        conops = state.conops
        has_modes = conops and hasattr(conops, 'modes') and len(conops.modes) > 0

        if has_modes:
            # Use ConOps modes for physically-driven sizing
            worst_sun = conops.worst_case_power_mode
            worst_eclipse = conops.worst_case_eclipse_mode

            # Sunlight demand = worst-case sunlight mode power
            payload_power = worst_sun.payload_power_w if worst_sun else 0
            platform_power_sun = worst_sun.platform_power_w if worst_sun else 30
            heater_power = worst_eclipse.heater_power_w if worst_eclipse else 10

            # Platform power from mode definition (more accurate than summing agent outputs)
            platform_power = platform_power_sun
            payload_duty = worst_sun.duty_cycle_percent / 100 if worst_sun else 0.25

            result.log(f"ConOps-driven: worst sunlight mode = {worst_sun.name if worst_sun else '?'} ({worst_sun.power_w if worst_sun else 0}W)")
            result.log(f"ConOps-driven: worst eclipse mode = {worst_eclipse.name if worst_eclipse else '?'} ({worst_eclipse.power_w if worst_eclipse else 0}W)")
        else:
            # Fallback: estimate from payload specs + subsystem agents (original logic)
            payload_power = 0.0
            payload_duty = 0.25
            i = 0
            while True:
                pp = state.get(f"payload.{i}.power_w")
                if pp is None:
                    break
                payload_power += pp
                pd = state.get(f"payload.{i}.duty_cycle", 0.25)
                payload_duty = max(payload_duty, pd)
                i += 1

            heater_power = state.get("thermal.heater_power_w", 10.0) or 10.0
            aocs_power = state.get("aocs.power_w") or 0
            ttc_power = state.get("link.ttc_power_w") or 0
            obdh_power = state.get("data.obc_power_w") or 0

            # Scale default platform power by spacecraft class when agents haven't computed yet
            sc_class_pwr = state.get_requirement("spacecraft_class", "nano")
            if aocs_power == 0 and ttc_power == 0:
                # Use class-appropriate defaults (not medium-sat defaults)
                if sc_class_pwr in ("nano",):
                    aocs_power, ttc_power, obdh_power = 2.0, 3.0, 2.0  # ~7W platform for 3U
                elif sc_class_pwr in ("micro",):
                    aocs_power, ttc_power, obdh_power = 5.0, 8.0, 5.0  # ~18W platform
                else:
                    aocs_power, ttc_power, obdh_power = 15.0, 20.0, 10.0

            platform_power = aocs_power + ttc_power + obdh_power

        # Determine cell efficiency by spacecraft class
        sc_class = state.get_requirement("spacecraft_class", "small")
        if sc_class in ("nano", "micro"):
            cell_eff = 0.295  # Triple-junction GaAs
            sa_specific = 80.0  # Body-mounted
        elif sc_class in ("small",):
            cell_eff = 0.30
            sa_specific = 100.0  # Deployable
        else:
            cell_eff = 0.32
            sa_specific = 130.0  # High-efficiency deployable

        # --- KB override: solar cell datasheet values (SPINE_SPEC §8) ---
        kb_cell = self._resolve_from_kb(state, "solar_cells", "power.solar_array.cell_equipment_id")
        if kb_cell:
            cell_eff = kb_cell.get("efficiency_pct", cell_eff * 100) / 100.0
            sa_specific = 1000.0 / kb_cell.get("mass_kg_per_m2", 1000.0 / sa_specific) if kb_cell.get("mass_kg_per_m2") else sa_specific
            result.log(f"KB solar cell: efficiency={cell_eff*100:.1f}%, specific_power={sa_specific:.0f} W/kg")

        pb = compute_power_budget(
            eclipse_fraction=eclipse_frac,
            sunlight_fraction=sunlight_frac,
            orbit_period_s=period_s,
            mission_duration_years=mission_years,
            platform_power_w=platform_power,
            payload_power_w=payload_power,
            payload_duty_cycle=payload_duty,
            heater_power_eclipse_w=heater_power,
            cell_efficiency=cell_eff,
            sa_specific_power_w_kg=sa_specific,
        )

        # --- KB override: battery datasheet values (SPINE_SPEC §8) ---
        kb_battery = self._resolve_from_kb(state, "batteries", "power.battery.equipment_id")
        if kb_battery:
            pb.battery_mass_kg = kb_battery.get("mass_kg", pb.battery_mass_kg)
            result.log(f"KB battery: mass={pb.battery_mass_kg:.2f} kg")

        result.add_param("power.sa_area_m2", "Solar Array Area", round(pb.sa_area_m2, 3), "m²")
        result.add_param("power.sa_power_bol_w", "SA Power BOL", round(pb.sa_power_bol_w, 1), "W")
        result.add_param("power.sa_power_eol_w", "SA Power EOL", round(pb.sa_power_eol_w, 1), "W")
        result.add_param("power.sa_mass_kg", "Solar Array Mass", round(pb.sa_mass_kg, 2), "kg")
        result.add_param("power.battery_capacity_wh", "Battery Capacity", round(pb.battery_capacity_wh, 1), "Wh")
        result.add_param("power.battery_mass_kg", "Battery Mass", round(pb.battery_mass_kg, 2), "kg")
        result.add_param("power.battery_dod_pct", "Battery DOD", round(pb.battery_dod_percent, 1), "%")
        if pb.battery_dod_percent > 30:
            result.warnings.append(f"Battery DOD {pb.battery_dod_percent:.0f}% exceeds 30% design limit — reduce eclipse load or increase battery capacity")
        result.add_param("power.total_sunlight_w", "Total Power (Sunlight)", round(pb.total_power_sunlight_w, 1), "W")
        result.add_param("power.total_eclipse_w", "Total Power (Eclipse)", round(pb.total_power_eclipse_w, 1), "W")
        dry_est = state.get("mass.dry_mass_estimate_kg", 100.0) or 100.0
        eps_mass = calibrate_mass("eps", pb.eps_mass_kg, dry_est, sc_class)
        result.add_param("power.eps_mass_kg", "EPS Total Mass", round(eps_mass, 2), "kg", margin_percent=20)
        result.add_param("power.eps_cost_keur", "EPS Cost", round(pb.eps_cost_keur, 0), "kEUR")

        # Note: duty-cycle SA override removed — compute_power_budget now uses
        # peak power (p_peak) for SA sizing, which is correct for all classes.
        # The old override used hardcoded class power tables that ignored actual
        # payload specifications, capping SA at ~10W for nano class regardless
        # of the real payload power requirement.

        result.warnings.extend(pb.warnings)

        # ---- Report-quality narrative & structured intermediates ----
        result.rationale = (
            f"Electrical power system sized for a worst-case sunlight load of "
            f"{pb.total_power_sunlight_w:.1f} W and worst-case eclipse load of "
            f"{pb.total_power_eclipse_w:.1f} W.  Solar array delivers "
            f"{pb.sa_power_bol_w:.1f} W BoL / {pb.sa_power_eol_w:.1f} W EoL "
            f"after {mission_years:.1f} yr of degradation, covering "
            f"{pb.sa_area_m2:.3f} m² of {cell_eff*100:.1f}%-efficient cells.  "
            f"Battery capacity {pb.battery_capacity_wh:.1f} Wh chosen for "
            f"{pb.battery_dod_percent:.1f}% depth-of-discharge over the "
            f"eclipse duration."
        )
        result.assumptions = [
            f"Solar cell efficiency {cell_eff*100:.1f}% (class-appropriate "
            f"triple-junction GaAs / KB-resolved cell).",
            f"Specific power {sa_specific:.0f} W/kg.",
            f"Worst-case mode selected from ConOps."
            if has_modes else "Mode profile estimated from payload duty cycles.",
            f"Heater allocation {heater_power:.1f} W during eclipse.",
            "Battery DoD limit 30% (ECSS Li-ion practice).",
        ]
        # Build mode-by-mode breakdown
        modes_extras = []
        if has_modes:
            for m in conops.modes:
                modes_extras.append({
                    "name": m.name,
                    "duty_cycle": float(getattr(m, "duty_cycle_percent", 0)) / 100,
                    "power_w": float(getattr(m, "power_w", 0)),
                    "platform_w": float(getattr(m, "platform_power_w", 0)),
                    "payload_w": float(getattr(m, "payload_power_w", 0)),
                    "heater_w": float(getattr(m, "heater_power_w", 0)),
                })
        result.extras["power.modes"] = modes_extras
        result.extras["power.battery"] = {
            "capacity_wh": pb.battery_capacity_wh,
            "dod_percent": pb.battery_dod_percent,
            "mass_kg": pb.battery_mass_kg,
            "chemistry": kb_battery.get("chemistry") if kb_battery else "Li-ion (assumed)",
        }
        result.extras["power.solar_array"] = {
            "area_m2": pb.sa_area_m2,
            "bol_w": pb.sa_power_bol_w,
            "eol_w": pb.sa_power_eol_w,
            "efficiency_pct": cell_eff * 100,
            "specific_power_w_kg": sa_specific,
        }
        result.extras["power.profile"] = {
            "sunlit_load_w": pb.total_power_sunlight_w,
            "eclipse_load_w": pb.total_power_eclipse_w,
            "period_min": period_s / 60.0 if period_s else 95.0,
            "eclipse_fraction": eclipse_frac,
            "sa_eol_w": pb.sa_power_eol_w,
        }

        result.confidence = 0.85
        return result
