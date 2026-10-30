"""SpaceCDF — Ground Segment Configurator.

Generates ground system configuration from the design:
- Mission Control System config (COSMOS/OpenMCT/Yamcs format)
- Pass prediction from orbit + station network
- Operations timeline from ConOps phases
- Commissioning sequence
- Frequency coordination documentation

Stage 5 of CubeSat full lifecycle capability.
"""
from __future__ import annotations

import math
from typing import Any


def generate_mcs_config(
    parameters: dict[str, Any],
    modes: list[dict] | None = None,
    spacecraft_name: str = "SC1",
    framework: str = "cosmos",
) -> dict[str, str]:
    """Generate Mission Control System configuration files.

    Supports COSMOS (Ball Aerospace), OpenMCT (NASA), and Yamcs formats.
    """
    modes = modes or []

    # Telemetry point database
    tm_points: list[dict] = []
    for pid, param in sorted(parameters.items()):
        unit = ""
        if hasattr(param, "unit"):
            unit = param.unit
        elif isinstance(param, dict):
            unit = param.get("unit", "")
        domain = pid.split(".")[0] if "." in pid else ""
        tm_points.append({
            "id": pid,
            "name": pid.replace(".", "_"),
            "domain": domain,
            "unit": unit,
            "type": "FLOAT32",
        })

    if framework == "cosmos":
        return _generate_cosmos_config(tm_points, modes, spacecraft_name)
    elif framework == "yamcs":
        return _generate_yamcs_config(tm_points, modes, spacecraft_name)
    else:
        return _generate_openmct_config(tm_points, modes, spacecraft_name)


def _generate_cosmos_config(
    tm_points: list[dict], modes: list[dict], sc_name: str
) -> dict[str, str]:
    """Generate COSMOS (Ball Aerospace / OpenC3) configuration."""

    # Target definition
    target_txt = f"""# {sc_name} Target Definition
# Auto-generated from SpaceCDF design

REQUIRE_UTILITY 'openc3/utilities/simulated_target'

TARGET {sc_name.upper()} {sc_name.upper()}
"""

    # Telemetry definition
    tm_lines = [f"TELEMETRY {sc_name.upper()} HEALTH BIG_ENDIAN"]
    tm_lines.append("  APPEND_ID_ITEM APID 16 UINT 0x0100")
    tm_lines.append("  APPEND_ITEM TIMESTAMP 32 UINT")
    tm_lines.append("    UNITS seconds s")

    for pt in tm_points[:50]:  # Limit to first 50 for readability
        tm_lines.append(f"  APPEND_ITEM {pt['name'].upper()} 32 FLOAT")
        if pt['unit']:
            tm_lines.append(f"    UNITS {pt['unit']} {pt['unit']}")

    # Command definitions
    cmd_lines = [f"COMMAND {sc_name.upper()} MODE_CHANGE BIG_ENDIAN"]
    cmd_lines.append('  APPEND_PARAMETER TARGET_MODE 8 UINT 0 255 0')
    for i, mode in enumerate(modes):
        cmd_lines.append(f'    STATE {mode.get("id", f"MODE_{i}").upper()} {i}')
    cmd_lines.append('  APPEND_PARAMETER CONFIRM 8 UINT 0 1 0')
    cmd_lines.append('')
    cmd_lines.append(f"COMMAND {sc_name.upper()} SAFE_MODE BIG_ENDIAN")
    cmd_lines.append('  APPEND_PARAMETER REASON 160 STRING "operator_command"')

    return {
        f"cosmos/{sc_name}/target.txt": target_txt,
        f"cosmos/{sc_name}/cmd_tlm/tlm.txt": "\n".join(tm_lines),
        f"cosmos/{sc_name}/cmd_tlm/cmd.txt": "\n".join(cmd_lines),
    }


def _generate_yamcs_config(
    tm_points: list[dict], modes: list[dict], sc_name: str
) -> dict[str, str]:
    """Generate Yamcs XTCE telemetry/telecommand database."""

    xtce = f"""<?xml version="1.0" encoding="UTF-8"?>
<SpaceSystem name="{sc_name}" xmlns="http://www.omg.org/spec/XTCE/20180204">
  <TelemetryMetaData>
    <ParameterSet>
"""
    for pt in tm_points:
        xtce += f'      <Parameter name="{pt["name"]}" parameterTypeRef="float32_t">\n'
        if pt["unit"]:
            xtce += f'        <UnitSet><Unit>{pt["unit"]}</Unit></UnitSet>\n'
        xtce += f'      </Parameter>\n'

    xtce += """    </ParameterSet>
  </TelemetryMetaData>
  <CommandMetaData>
    <MetaCommandSet>
      <MetaCommand name="MODE_CHANGE">
        <ArgumentList>
          <Argument name="target_mode" argumentTypeRef="uint8_t"/>
        </ArgumentList>
      </MetaCommand>
      <MetaCommand name="SAFE_MODE"/>
    </MetaCommandSet>
  </CommandMetaData>
</SpaceSystem>
"""
    return {f"yamcs/{sc_name}.xml": xtce}


def _generate_openmct_config(
    tm_points: list[dict], modes: list[dict], sc_name: str
) -> dict[str, str]:
    """Generate OpenMCT dictionary JSON."""
    import json

    dictionary = {
        "name": sc_name,
        "key": sc_name.lower(),
        "measurements": [
            {
                "key": pt["id"],
                "name": pt["name"],
                "units": pt["unit"],
                "type": "float",
                "source": pt["domain"],
            }
            for pt in tm_points
        ],
    }

    return {
        f"openmct/{sc_name}_dictionary.json": json.dumps(dictionary, indent=2),
    }


def generate_pass_predictions(
    orbit_altitude_km: float,
    orbit_inclination_deg: float,
    stations: list[dict[str, Any]],
    days: int = 7,
) -> dict[str, Any]:
    """Generate pass prediction summary for the station network.

    Simplified geometric model — in production, use SGP4 + TLE.
    """
    from spacecdf_common.physics.orbit import estimate_contact_time_per_day

    period_s = 2 * math.pi * math.sqrt(((6371 + orbit_altitude_km) * 1000)**3 / 3.986004418e14)
    orbits_per_day = 86400 / period_s

    station_passes: list[dict] = []
    total_contact_min = 0

    for stn in stations:
        lat = stn.get("latitude_deg", 78)
        name = stn.get("name", "Unknown")
        contact_s = estimate_contact_time_per_day(
            orbit_altitude_km, lat, orbit_inclination_deg
        )
        passes_per_day = contact_s / max(period_s * 0.05, 1)  # Avg pass ~5% of orbit
        avg_pass_min = (contact_s / max(passes_per_day, 1)) / 60

        station_passes.append({
            "station": name,
            "latitude_deg": lat,
            "passes_per_day": round(passes_per_day, 1),
            "avg_pass_duration_min": round(avg_pass_min, 1),
            "total_contact_min_per_day": round(contact_s / 60, 1),
            "total_contact_min_7day": round(contact_s / 60 * 7, 0),
        })
        total_contact_min += contact_s / 60

    return {
        "orbit": {
            "altitude_km": orbit_altitude_km,
            "inclination_deg": orbit_inclination_deg,
            "period_min": round(period_s / 60, 1),
            "orbits_per_day": round(orbits_per_day, 1),
        },
        "stations": station_passes,
        "total_contact_min_per_day": round(total_contact_min, 1),
        "prediction_days": days,
    }


def generate_ops_timeline(
    mission_duration_years: float,
    modes: list[dict] | None = None,
) -> dict[str, Any]:
    """Generate an operations timeline from mission duration and ConOps phases."""
    modes = modes or []

    phases = [
        {
            "name": "Launch & Early Orbit Phase (LEOP)",
            "duration_days": 3,
            "description": "Initial acquisition, solar array deployment, first ground contact",
            "primary_mode": "safe",
            "activities": [
                "Separation from launch vehicle",
                "Solar array deployment confirmation",
                "First ground station pass — beacon acquisition",
                "Initial attitude determination",
                "EPS checkout — battery voltage and solar array current",
                "OBC health check — memory, processor, storage",
            ],
        },
        {
            "name": "Commissioning Phase",
            "duration_days": 30,
            "description": "Subsystem-by-subsystem checkout and calibration",
            "primary_mode": "nominal_science",
            "activities": [
                "AOCS commissioning — attitude modes, pointing accuracy verification",
                "Comms commissioning — link budget verification, data rate testing",
                "Payload commissioning — first light, focus check, calibration",
                "Propulsion commissioning (if applicable) — thruster firing test",
                "Thermal characterisation — compare predictions to telemetry",
                "Full functional test — all modes exercised",
                "Declare operational readiness",
            ],
        },
        {
            "name": "Nominal Operations",
            "duration_days": int(mission_duration_years * 365 * 0.8),
            "description": "Primary mission operations — science data collection and downlink",
            "primary_mode": "nominal_science",
            "activities": [
                "Daily science data acquisition per ConOps timeline",
                "Regular ground station contacts for TM/TC and data downlink",
                "Periodic orbit maintenance manoeuvres (if propulsion available)",
                "Monthly housekeeping trend analysis",
                "Quarterly calibration campaign",
                "Software updates as needed",
            ],
        },
        {
            "name": "Extended Operations (if approved)",
            "duration_days": int(mission_duration_years * 365 * 0.2),
            "description": "Continued operations with potentially degraded performance",
            "primary_mode": "nominal_science",
            "activities": [
                "Reduced operations cadence",
                "Focus on high-value targets",
                "Monitor degradation trends (SA, battery, reaction wheels)",
                "Plan for end-of-life disposal",
            ],
        },
        {
            "name": "End of Life & Disposal",
            "duration_days": 14,
            "description": "Passivation and deorbit (or graveyard orbit raise)",
            "primary_mode": "safe",
            "activities": [
                "Final data downlink",
                "Deorbit burn / drag augmentation deployment",
                "Battery discharge to safe level",
                "RF transmitter shutdown",
                "Reaction wheel spin-down",
                "Final telemetry beacon",
                "Mission complete declaration",
            ],
        },
    ]

    return {
        "mission_duration_years": mission_duration_years,
        "total_phases": len(phases),
        "phases": phases,
    }
