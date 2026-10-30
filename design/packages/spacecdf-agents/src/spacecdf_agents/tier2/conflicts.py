"""SpaceCDF — Cross-Domain Conflict Detection Agent (Tier 2).

Examines the converged design state and identifies clashes between
engineering domains. Each conflict names the two positions involved
and suggests resolutions with responsible party.

Eight detection rules covering the most common inter-domain tensions
in spacecraft design.
"""
from __future__ import annotations

from spacecdf_common.agents.base import AgentResult, DesignAgent, DesignState
from spacecdf_common.models.conflicts import (
    ConflictResolution,
    ConflictSeverity,
    CrossDomainConflict,
)
from spacecdf_common.physics.thermal import spacecraft_surface_area


class ConflictDetectionAgent(DesignAgent):

    @property
    def domain(self) -> str:
        return "conflicts"

    @property
    def tier(self) -> int:
        return 2

    def input_parameters(self) -> list[str]:
        return []  # Reads everything — runs after all other agents

    def output_parameters(self) -> list[str]:
        return ["conflicts.count", "conflicts.critical", "conflicts.major"]

    async def execute(self, state: DesignState) -> AgentResult:
        result = AgentResult(domain=self.domain)
        conflicts: list[CrossDomainConflict] = []

        # --- Rule 1: Data Rate vs Downlink Capacity ---
        gen_gb = state.get("data.generated_per_day_gb", 0) or 0
        dl_gb = state.get("data.downlinked_per_day_gb", 0) or 0
        if gen_gb > 0 and dl_gb > 0 and gen_gb > dl_gb * 1.1:
            deficit_pct = ((gen_gb - dl_gb) / gen_gb) * 100
            severity = ConflictSeverity.MAJOR if deficit_pct > 50 else ConflictSeverity.MINOR
            conflicts.append(CrossDomainConflict(
                id="CONF-DATA-001",
                severity=severity,
                title="Data Rate vs Downlink Capacity",
                description=(
                    f"Payload generates {gen_gb:.1f} GB/day but comms can only downlink "
                    f"{dl_gb:.1f} GB/day — {deficit_pct:.0f}% data deficit. "
                    f"Either reduce payload data rate, increase downlink capacity, or add onboard selection/compression."
                ),
                domain_a="data", domain_b="link",
                position_a="payload_lead", position_b="comms_engineer",
                param_a="data.generated_per_day_gb", param_b="link.data_per_day_gb",
                value_a_str=f"{gen_gb:.1f} GB/day", value_b_str=f"{dl_gb:.1f} GB/day",
                resolutions=[
                    ConflictResolution(
                        description="Reduce payload duty cycle or apply onboard data selection",
                        position_responsible="payload_lead",
                        parameter_to_change="payload.0.duty_cycle",
                        suggested_direction="decrease",
                        estimated_impact=f"Reducing duty cycle to {(dl_gb/gen_gb)*100:.0f}% would close the gap",
                    ),
                    ConflictResolution(
                        description="Upgrade to Ka-band or add ground station passes",
                        position_responsible="comms_engineer",
                        parameter_to_change="link.downlink_rate_bps",
                        suggested_direction="increase",
                        estimated_impact="Ka-band at 26 GHz could provide 10x data rate improvement",
                    ),
                    ConflictResolution(
                        description="Add onboard compression (2-4x typical for imaging payloads)",
                        position_responsible="payload_lead",
                        parameter_to_change="data.generated_per_day_gb",
                        suggested_direction="decrease",
                        estimated_impact="Compression ratio of 3:1 would reduce effective data to "
                                         f"{gen_gb/3:.1f} GB/day",
                    ),
                ],
            ))

        # --- Rule 2: Pointing vs AOCS Mass ---
        pointing_req = state.get("payload.0.pointing_deg", 1.0) or 1.0
        aocs_mass = state.get("aocs.mass_kg", 0) or 0
        dry_mass = state.get("mass.dry_mass_kg", 0) or 0
        if pointing_req < 0.05 and dry_mass > 0 and aocs_mass / dry_mass > 0.20:
            conflicts.append(CrossDomainConflict(
                id="CONF-AOCS-001",
                severity=ConflictSeverity.MAJOR,
                title="Fine Pointing vs AOCS Mass",
                description=(
                    f"Payload requires {pointing_req}° pointing accuracy, driving AOCS mass to "
                    f"{aocs_mass:.1f} kg ({aocs_mass/dry_mass*100:.0f}% of dry mass). "
                    f"Consider relaxing pointing or using lighter AOCS technology."
                ),
                domain_a="payload", domain_b="aocs",
                position_a="payload_lead", position_b="aocs_engineer",
                param_a="payload.0.pointing_deg", param_b="aocs.mass_kg",
                value_a_str=f"{pointing_req}°", value_b_str=f"{aocs_mass:.1f} kg",
                resolutions=[
                    ConflictResolution(
                        description="Relax pointing requirement if science allows",
                        position_responsible="payload_lead",
                        parameter_to_change="payload.0.pointing_deg",
                        suggested_direction="increase",
                    ),
                    ConflictResolution(
                        description="Use MEMS gyros + AI attitude determination (lower mass, TRL 5)",
                        position_responsible="aocs_engineer",
                        parameter_to_change="aocs.mass_kg",
                        suggested_direction="decrease",
                        estimated_impact="Could reduce AOCS mass by 40-50%",
                    ),
                ],
            ))

        # --- Rule 3: Eclipse Power vs Battery ---
        eclipse_power = state.get("power.total_eclipse_w", 0) or 0
        eclipse_min = state.get("orbit.eclipse_duration_min", 0) or 0
        battery_wh = state.get("power.battery_capacity_wh", 0) or 0
        if eclipse_power > 0 and eclipse_min > 0 and battery_wh > 0:
            eclipse_energy_wh = eclipse_power * (eclipse_min / 60.0)
            dod = eclipse_energy_wh / battery_wh if battery_wh > 0 else 0
            if dod > 0.40:
                severity = ConflictSeverity.CRITICAL if dod > 0.80 else ConflictSeverity.MAJOR
                conflicts.append(CrossDomainConflict(
                    id="CONF-PWR-001",
                    severity=severity,
                    title="Eclipse Power Demand vs Battery Capacity",
                    description=(
                        f"Eclipse loads of {eclipse_power:.0f}W for {eclipse_min:.0f} min require "
                        f"{eclipse_energy_wh:.0f} Wh, giving {dod*100:.0f}% DOD on a "
                        f"{battery_wh:.0f} Wh battery. Maximum recommended DOD is 30-40%."
                    ),
                    domain_a="thermal", domain_b="power",
                    position_a="thermal_engineer", position_b="power_engineer",
                    param_a="thermal.heater_power_w", param_b="power.battery_capacity_wh",
                    value_a_str=f"{eclipse_power:.0f}W eclipse load",
                    value_b_str=f"{battery_wh:.0f} Wh battery",
                    resolutions=[
                        ConflictResolution(
                            description="Reduce eclipse heater power (accept wider temp range or add MLI)",
                            position_responsible="thermal_engineer",
                            parameter_to_change="thermal.heater_power_w",
                            suggested_direction="decrease",
                        ),
                        ConflictResolution(
                            description="Increase battery capacity (mass/cost impact)",
                            position_responsible="power_engineer",
                            parameter_to_change="power.battery_capacity_wh",
                            suggested_direction="increase",
                        ),
                    ],
                ))

        # --- Rule 4: Propulsion Mass vs Total Mass ---
        prop_mass = state.get("propulsion.total_mass_kg", 0) or 0
        if dry_mass > 0 and prop_mass > 0 and prop_mass / dry_mass > 0.30:
            conflicts.append(CrossDomainConflict(
                id="CONF-PROP-001",
                severity=ConflictSeverity.MAJOR,
                title="Propulsion Mass Dominates Spacecraft",
                description=(
                    f"Propulsion system at {prop_mass:.1f} kg is {prop_mass/dry_mass*100:.0f}% of "
                    f"dry mass ({dry_mass:.0f} kg). Consider higher-ISP propulsion or reduced delta-V."
                ),
                domain_a="propulsion", domain_b="mass",
                position_a="propulsion_engineer", position_b="systems_engineer",
                param_a="propulsion.total_mass_kg", param_b="mass.dry_mass_kg",
                value_a_str=f"{prop_mass:.1f} kg", value_b_str=f"{dry_mass:.0f} kg total",
                resolutions=[
                    ConflictResolution(
                        description="Switch to electric propulsion (higher ISP, less propellant)",
                        position_responsible="propulsion_engineer",
                        parameter_to_change="propulsion.type",
                        suggested_direction="replace",
                        estimated_impact="Electric propulsion reduces propellant mass by 5-10x but needs more power and time",
                    ),
                    ConflictResolution(
                        description="Reduce delta-V requirement (accept orbit degradation or shorter lifetime)",
                        position_responsible="systems_engineer",
                        parameter_to_change="orbit.delta_v_total_ms",
                        suggested_direction="decrease",
                    ),
                ],
            ))

        # --- Rule 5: Solar Array Area vs Spacecraft Volume ---
        sa_area = state.get("power.sa_area_m2", 0) or 0
        sc_class = state.get("mission.spacecraft_class", "small")
        if isinstance(sc_class, str) and sc_class in ("nano", "micro") and sa_area > 0:
            body_area = spacecraft_surface_area(dry_mass if dry_mass > 0 else 10, "cubesat")
            if sa_area > body_area * 0.6:
                conflicts.append(CrossDomainConflict(
                    id="CONF-SA-001",
                    severity=ConflictSeverity.MINOR,
                    title="Solar Array Exceeds Body-Mount Area",
                    description=(
                        f"SA area {sa_area:.2f} m² exceeds 60% of body area {body_area:.2f} m² — "
                        f"deployable panels required, adding mass and complexity."
                    ),
                    domain_a="power", domain_b="structure",
                    position_a="power_engineer", position_b="structures_engineer",
                    param_a="power.sa_area_m2", param_b="structure.mass_kg",
                    value_a_str=f"{sa_area:.2f} m²", value_b_str=f"{body_area:.2f} m² body",
                    resolutions=[
                        ConflictResolution(
                            description="Use higher-efficiency solar cells to reduce area",
                            position_responsible="power_engineer",
                            parameter_to_change="power.sa_area_m2",
                            suggested_direction="decrease",
                        ),
                        ConflictResolution(
                            description="Accept deployable panels (add mechanisms mass + risk)",
                            position_responsible="structures_engineer",
                            parameter_to_change="structure.mass_kg",
                            suggested_direction="accept",
                        ),
                    ],
                ))

        # --- Rule 6: Link Margin vs Power Budget ---
        link_margin = state.get("link.downlink_margin_db", 0) or 0
        ttc_power = state.get("link.ttc_power_w", 0) or 0
        sa_power_eol = state.get("power.sa_power_eol_w", 0) or 0
        if link_margin < 3.0 and sa_power_eol > 0:
            pwr_pct = (ttc_power / sa_power_eol * 100) if sa_power_eol > 0 else 0
            conflicts.append(CrossDomainConflict(
                id="CONF-LINK-001",
                severity=ConflictSeverity.MAJOR,
                title="Link Margin Below Minimum",
                description=(
                    f"Downlink margin is {link_margin:.1f} dB (minimum 3 dB). "
                    f"Increasing TX power would help but TTC already uses {pwr_pct:.0f}% of SA power."
                ),
                domain_a="link", domain_b="power",
                position_a="comms_engineer", position_b="power_engineer",
                param_a="link.downlink_margin_db", param_b="power.sa_power_eol_w",
                value_a_str=f"{link_margin:.1f} dB", value_b_str=f"{sa_power_eol:.0f}W available",
                resolutions=[
                    ConflictResolution(
                        description="Use higher-gain spacecraft antenna",
                        position_responsible="comms_engineer",
                        parameter_to_change="link.downlink_margin_db",
                        suggested_direction="increase",
                    ),
                    ConflictResolution(
                        description="Use larger ground station antenna",
                        position_responsible="comms_engineer",
                        parameter_to_change="link.downlink_margin_db",
                        suggested_direction="increase",
                        estimated_impact="Moving from 13m to 15m dish adds ~1.2 dB",
                    ),
                    ConflictResolution(
                        description="Accept lower data rate (reduces required Eb/N0)",
                        position_responsible="comms_engineer",
                        parameter_to_change="link.downlink_rate_bps",
                        suggested_direction="decrease",
                    ),
                ],
            ))

        # --- Rule 7: Thermal Rejection vs Surface Area ---
        radiator_area = state.get("thermal.radiator_area_m2", 0) or 0
        if dry_mass > 0 and radiator_area > 0:
            form = "cubesat" if isinstance(sc_class, str) and sc_class in ("nano", "micro") else "box"
            total_area = spacecraft_surface_area(dry_mass, form)
            if radiator_area > total_area * 0.5:
                conflicts.append(CrossDomainConflict(
                    id="CONF-THERM-001",
                    severity=ConflictSeverity.MAJOR,
                    title="Radiator Area vs Available Surface",
                    description=(
                        f"Required radiator area {radiator_area:.2f} m² exceeds 50% of total "
                        f"spacecraft surface {total_area:.2f} m². Configuration conflict."
                    ),
                    domain_a="thermal", domain_b="structure",
                    position_a="thermal_engineer", position_b="structures_engineer",
                    param_a="thermal.radiator_area_m2", param_b="structure.mass_kg",
                    value_a_str=f"{radiator_area:.2f} m²", value_b_str=f"{total_area:.2f} m² total",
                    resolutions=[
                        ConflictResolution(
                            description="Reduce internal power dissipation",
                            position_responsible="systems_engineer",
                            parameter_to_change="power.total_sunlight_w",
                            suggested_direction="decrease",
                        ),
                        ConflictResolution(
                            description="Use deployable radiator panels",
                            position_responsible="thermal_engineer",
                            parameter_to_change="thermal.radiator_area_m2",
                            suggested_direction="accept",
                        ),
                    ],
                ))

        # --- Rule 8: Cost vs TRL Risk ---
        total_cost_meur = state.get("cost.total_meur", 0) or 0
        target_cost = state.get_requirement("target_cost_meur")
        # Count low-TRL parameters
        low_trl_count = sum(
            1 for p in state.parameters.values()
            if p.trl is not None and p.trl <= 5
        )
        if target_cost and total_cost_meur > target_cost * 0.9 and low_trl_count > 0:
            conflicts.append(CrossDomainConflict(
                id="CONF-COST-001",
                severity=ConflictSeverity.MINOR,
                title="Tight Budget with Low-TRL Technology Risk",
                description=(
                    f"Cost estimate {total_cost_meur:.1f} MEUR is at {total_cost_meur/target_cost*100:.0f}% "
                    f"of target {target_cost:.1f} MEUR, with {low_trl_count} low-TRL component(s). "
                    f"Technology maturation costs may push budget over."
                ),
                domain_a="cost", domain_b="trl",
                position_a="cost_engineer", position_b="systems_engineer",
                param_a="cost.total_meur", param_b="trl.innovation_count",
                value_a_str=f"{total_cost_meur:.1f} MEUR", value_b_str=f"{low_trl_count} low-TRL items",
                resolutions=[
                    ConflictResolution(
                        description="Use proven (TRL 7+) alternatives to reduce development risk/cost",
                        position_responsible="systems_engineer",
                        parameter_to_change="trl.recommended_innovations",
                        suggested_direction="decrease",
                    ),
                    ConflictResolution(
                        description="Increase cost budget to accommodate technology maturation",
                        position_responsible="cost_engineer",
                        parameter_to_change="cost.total_meur",
                        suggested_direction="accept",
                    ),
                ],
            ))

        # --- Store results ---
        n_crit = sum(1 for c in conflicts if c.severity == ConflictSeverity.CRITICAL)
        n_major = sum(1 for c in conflicts if c.severity == ConflictSeverity.MAJOR)

        result.add_param("conflicts.count", "Total Conflicts", len(conflicts), "")
        result.add_param("conflicts.critical", "Critical Conflicts", n_crit, "")
        result.add_param("conflicts.major", "Major Conflicts", n_major, "")

        # Store conflicts in computation_log as serialised data for the orchestrator to extract
        for c in conflicts:
            severity_str = c.severity.value.upper()
            result.add_warning(
                f"[{severity_str} CONFLICT] {c.title}: {c.description}"
            )
            for r in c.resolutions:
                result.add_recommendation(
                    f"[{c.id}] {r.position_responsible}: {r.description}"
                )

        # Attach conflicts data to result for orchestrator to extract
        result._conflicts = conflicts  # type: ignore[attr-defined]

        result.confidence = 0.90
        return result
