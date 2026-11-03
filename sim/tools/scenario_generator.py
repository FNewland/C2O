#!/usr/bin/env python3
"""SMO Scenario Generator — interactive web UI.

Serves a form at http://localhost:8096 where the instructor describes failures
and timing; clicking Generate writes the YAML directly to
configs/eosat1/scenarios/ and returns the file path.

Usage:
    python tools/scenario_generator.py
    python tools/scenario_generator.py --port 8097
"""
import argparse
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from datetime import datetime

# The shared tool page frame (tools/tool_frame.py) sits next to this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from aiohttp import web
except ImportError:
    raise SystemExit("aiohttp not installed — run: pip install aiohttp")

# ── Failure catalogue ────────────────────────────────────────────────────────
#
# Derived from the simulator's declarative failure catalogue, which is built
# from each subsystem model's own FAILURE_SPECS table (declared next to its
# inject_failure() body). This file used to carry a hand-copied dict of
# subsystems -> failure names -> {label, extras}; it drifted every time a model
# changed, and its "extras" list understood only `wheel`, `face` and `axis`, so
# every other typed parameter (star tracker unit, EPS power line, memory
# segment, gyro axis, drift ppm, leak rate ...) was unreachable from this tool
# and the scenarios it generated silently used the model defaults.
#
# The form is now generated from the same ParamSpec objects the instructor
# console uses, so a new failure appears here automatically and with the right
# controls, ranges and engineering units.

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _pkg in ("smo-common", "smo-simulator"):
    _src = _REPO_ROOT / "packages" / _pkg / "src"
    if _src.exists() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from smo_simulator import failure_catalog as _failure_catalog  # noqa: E402

# {subsystem: {"label": str, "failures": {name: FailureSpec-as-dict}}}
SUBSYSTEMS = {
    entry["name"]: {
        "label": entry["label"],
        "failures": {f["name"]: f for f in entry["failures"]},
    }
    for entry in _failure_catalog.to_dict()["subsystems"]
}

# Meta keys of a generated inject event that belong to the failure MANAGER
# (severity/timing) rather than to the failure's own parameter spec.
_INJECT_META_KEYS = ("type", "subsystem", "failure", "magnitude", "onset",
                     "onset_duration_s", "timing_type", "time_offset_s",
                     "condition", "label", "params")

# Key telemetry parameters available for set_parameter events
PARAMS = [
    {"id": "0x0101", "name": "eps.bat_soc",       "desc": "Battery SoC (%)",           "unit": "%"},
    {"id": "0x0105", "name": "eps.bus_voltage",    "desc": "Bus voltage (V)",            "unit": "V"},
    {"id": "0x0107", "name": "eps.power_gen",      "desc": "Power generation (W)",       "unit": "W"},
    {"id": "0x0106", "name": "eps.power_cons",     "desc": "Power consumption (W)",      "unit": "W"},
    {"id": "0x0102", "name": "eps.bat_temp",       "desc": "Battery temperature (°C)",   "unit": "C"},
    {"id": "0x0208", "name": "aocs.rw2_speed",     "desc": "RW-2 speed (RPM)",           "unit": "RPM"},
    {"id": "0x0207", "name": "aocs.rw1_speed",     "desc": "RW-1 speed (RPM)",           "unit": "RPM"},
    {"id": "0x0209", "name": "aocs.rw3_speed",     "desc": "RW-3 speed (RPM)",           "unit": "RPM"},
    {"id": "0x020A", "name": "aocs.rw4_speed",     "desc": "RW-4 speed (RPM)",           "unit": "RPM"},
    {"id": "0x0407", "name": "tcs.temp_battery",   "desc": "Battery temperature TCS (°C)", "unit": "C"},
    {"id": "0x0406", "name": "tcs.temp_obc",       "desc": "OBC temperature (°C)",       "unit": "C"},
    {"id": "0x0408", "name": "tcs.temp_fpa",       "desc": "FPA temperature (°C)",       "unit": "C"},
    {"id": "0x0302", "name": "obdh.cpu_load",      "desc": "CPU load (%)",               "unit": "%"},
    {"id": "0x0502", "name": "ttc.rssi",            "desc": "RSSI (dBm)",                "unit": "dBm"},
    {"id": "0x0503", "name": "ttc.link_margin",    "desc": "Link margin (dB)",           "unit": "dB"},
]

DIFFICULTIES = ["BASIC", "INTERMEDIATE", "ADVANCED", "EXPERT"]
ONSETS = ["step", "gradual", "intermittent"]
FACES = ["px", "mx", "py", "my", "pz", "mz"]

# ── Cascade knowledge base (derived from fault_propagation.yaml + subsystem models) ──
# Maps (subsystem, failure) → list of cascade effects with timing and severity
CASCADE_MAP = {
    # EPS failures
    ("eps", "solar_panel_loss"): [
        {"to": "eps",     "effect": "Bus voltage drops → undervoltage alarm",         "delay_s": 5,   "severity": "warning"},
        {"to": "eps",     "effect": "Battery begins discharging (SoC declining)",      "delay_s": 10,  "severity": "warning"},
        {"to": "tcs",     "effect": "Heaters shed to reduce load (temp drops)",        "delay_s": 60,  "severity": "warning"},
        {"to": "aocs",    "effect": "AOCS enters safe mode if bus < 22 V",             "delay_s": 120, "severity": "critical"},
        {"to": "payload", "effect": "Payload powered off at load-shed stage 2",        "delay_s": 180, "severity": "critical"},
        {"to": "obdh",    "effect": "Watchdog reset risk if SoC < 10%",               "delay_s": 600, "severity": "critical"},
    ],
    ("eps", "solar_array_total_loss"): [
        {"to": "eps",     "effect": "Bus voltage collapses immediately",               "delay_s": 1,   "severity": "critical"},
        {"to": "eps",     "effect": "Battery only — survival time ~90 min",            "delay_s": 2,   "severity": "critical"},
        {"to": "tcs",     "effect": "All non-essential heaters shed",                  "delay_s": 5,   "severity": "warning"},
        {"to": "aocs",    "effect": "AOCS safe mode within seconds",                   "delay_s": 5,   "severity": "critical"},
        {"to": "payload", "effect": "Payload powered off immediately",                 "delay_s": 2,   "severity": "critical"},
        {"to": "ttc",     "effect": "TX power reduced to preserve battery",            "delay_s": 10,  "severity": "warning"},
        {"to": "obdh",    "effect": "OBC enters contingency boot sequence",            "delay_s": 30,  "severity": "critical"},
    ],
    ("eps", "bat_cell"): [
        {"to": "eps",     "effect": "Reduced capacity → SoC drops faster",            "delay_s": 5,   "severity": "warning"},
        {"to": "eps",     "effect": "Battery overtemp risk during charge",             "delay_s": 30,  "severity": "warning"},
        {"to": "tcs",     "effect": "Battery heater may activate abnormally",          "delay_s": 60,  "severity": "info"},
        {"to": "aocs",    "effect": "Safe mode if SoC drops below threshold",          "delay_s": 300, "severity": "critical"},
    ],
    ("eps", "undervoltage"): [
        {"to": "aocs",    "effect": "AOCS enters safe mode (< 22 V threshold)",        "delay_s": 5,   "severity": "critical"},
        {"to": "payload", "effect": "Payload powered off",                             "delay_s": 2,   "severity": "critical"},
        {"to": "tcs",     "effect": "Non-essential heaters disabled",                  "delay_s": 1,   "severity": "warning"},
        {"to": "ttc",     "effect": "TX power reduced",                                "delay_s": 3,   "severity": "warning"},
    ],
    ("eps", "bus_short"): [
        {"to": "eps",     "effect": "Overcurrent trip — affected bus powered off",     "delay_s": 0,   "severity": "critical"},
        {"to": "aocs",    "effect": "AOCS power loss if on shorted bus",               "delay_s": 1,   "severity": "critical"},
        {"to": "obdh",    "effect": "Possible OBC reset if OBC bus affected",          "delay_s": 1,   "severity": "critical"},
    ],
    ("eps", "overcurrent"): [
        {"to": "eps",     "effect": "Overcurrent protection trips affected line",       "delay_s": 0,   "severity": "critical"},
        {"to": "aocs",    "effect": "Attitude control loss if AOCS line tripped",      "delay_s": 1,   "severity": "critical"},
        {"to": "payload", "effect": "Payload offline if payload line tripped",         "delay_s": 1,   "severity": "warning"},
    ],
    # AOCS failures
    ("aocs", "rw_bearing"): [
        {"to": "aocs",    "effect": "RW friction increases → speed runaway risk",      "delay_s": 30,  "severity": "warning"},
        {"to": "aocs",    "effect": "Attitude pointing error grows (desaturation fails)","delay_s": 120,"severity": "warning"},
        {"to": "aocs",    "effect": "Safe mode entry if RW exceeds 6000 RPM",          "delay_s": 300, "severity": "critical"},
        {"to": "payload", "effect": "Imaging quality degrades, then halts",            "delay_s": 120, "severity": "warning"},
        {"to": "eps",     "effect": "RW current draw spikes (motor fighting bearing)", "delay_s": 30,  "severity": "info"},
        {"to": "tcs",     "effect": "RW thermal output rises",                         "delay_s": 60,  "severity": "info"},
    ],
    ("aocs", "rw_seizure"): [
        {"to": "aocs",    "effect": "Immediate attitude disturbance torque",           "delay_s": 0,   "severity": "critical"},
        {"to": "aocs",    "effect": "Safe mode entry if 3-axis control lost",          "delay_s": 5,   "severity": "critical"},
        {"to": "payload", "effect": "Payload halted — attitude unstable",              "delay_s": 5,   "severity": "critical"},
        {"to": "eps",     "effect": "AOCS power spike then drop (wheel off)",          "delay_s": 2,   "severity": "warning"},
    ],
    ("aocs", "gyro_bias"): [
        {"to": "aocs",    "effect": "Attitude estimate drifts — pointing error grows", "delay_s": 60,  "severity": "warning"},
        {"to": "aocs",    "effect": "Star tracker needed for recovery; if blinded → safe mode","delay_s": 300,"severity": "critical"},
        {"to": "payload", "effect": "Imaging off-target progressively",               "delay_s": 120, "severity": "warning"},
    ],
    ("aocs", "st_failure"): [
        {"to": "aocs",    "effect": "Attitude estimation degrades to gyro-only",       "delay_s": 1,   "severity": "warning"},
        {"to": "aocs",    "effect": "Safe mode if gyro drift exceeds limit",           "delay_s": 300, "severity": "critical"},
        {"to": "payload", "effect": "Fine pointing lost",                              "delay_s": 60,  "severity": "warning"},
    ],
    ("aocs", "st_blind"): [
        {"to": "aocs",    "effect": "Fine attitude reference lost",                    "delay_s": 1,   "severity": "warning"},
        {"to": "aocs",    "effect": "Coarse sun-safe mode after gyro timeout",         "delay_s": 120, "severity": "critical"},
        {"to": "payload", "effect": "Imaging halted",                                  "delay_s": 5,   "severity": "warning"},
    ],
    ("aocs", "multi_wheel_failure"): [
        {"to": "aocs",    "effect": "3-axis attitude control lost immediately",         "delay_s": 1,   "severity": "critical"},
        {"to": "aocs",    "effect": "Sun-safe tumble mode — magnetorquers only",       "delay_s": 5,   "severity": "critical"},
        {"to": "payload", "effect": "Payload powered off",                             "delay_s": 2,   "severity": "critical"},
        {"to": "eps",     "effect": "Power draw drops (wheels off), but SA may lose sun pointing","delay_s": 10,"severity": "warning"},
        {"to": "ttc",     "effect": "Link margin degrades if antenna off-pointing",    "delay_s": 30,  "severity": "warning"},
    ],
    # TCS failures
    ("tcs", "cooler_failure"): [
        {"to": "tcs",     "effect": "FPA temperature rises (imaging sensor heats up)", "delay_s": 60,  "severity": "warning"},
        {"to": "payload", "effect": "Payload imaging degraded → halted above threshold","delay_s": 180,"severity": "critical"},
        {"to": "eps",     "effect": "FPA cooler power line freed (minor power saving)", "delay_s": 5,  "severity": "info"},
    ],
    ("tcs", "heater_failure"): [
        {"to": "tcs",     "effect": "Zone temperature drops below setpoint",           "delay_s": 120, "severity": "warning"},
        {"to": "eps",     "effect": "Battery temp may fall below -5°C safe limit",     "delay_s": 300, "severity": "critical"},
        {"to": "obdh",    "effect": "OBC performance degrades below -20°C",            "delay_s": 600, "severity": "warning"},
    ],
    ("tcs", "heater_stuck_on"): [
        {"to": "tcs",     "effect": "Zone temperature climbs above setpoint",          "delay_s": 60,  "severity": "warning"},
        {"to": "eps",     "effect": "Heater line drawing excess current",              "delay_s": 10,  "severity": "warning"},
        {"to": "tcs",     "effect": "Battery overtemp risk → charge rate cut",         "delay_s": 300, "severity": "critical"},
    ],
    ("tcs", "obc_thermal"): [
        {"to": "obdh",    "effect": "CPU throttling → increased latency",              "delay_s": 30,  "severity": "warning"},
        {"to": "obdh",    "effect": "Possible OBC reset above 85°C",                  "delay_s": 120, "severity": "critical"},
        {"to": "aocs",    "effect": "AOCS commanding delayed during OBC slowdown",     "delay_s": 30,  "severity": "info"},
    ],
    # TTC failures
    ("ttc", "uplink_loss"): [
        {"to": "ttc",     "effect": "No TC reception — ground cannot command",         "delay_s": 0,   "severity": "critical"},
        {"to": "obdh",    "effect": "FDIR may escalate if no uplink within timeout",   "delay_s": 300, "severity": "warning"},
        {"to": "aocs",    "effect": "No manual override possible during anomaly",      "delay_s": 0,   "severity": "warning"},
    ],
    ("ttc", "primary_failure"): [
        {"to": "ttc",     "effect": "Switchover to redundant transponder attempted",   "delay_s": 2,   "severity": "warning"},
        {"to": "ttc",     "effect": "Link outage during switchover (~10 s)",           "delay_s": 2,   "severity": "warning"},
        {"to": "obdh",    "effect": "TC loss triggers FDIR uplink-loss watchdog",      "delay_s": 5,   "severity": "warning"},
    ],
    ("ttc", "pa_overheat"): [
        {"to": "ttc",     "effect": "TX power auto-reduced to protect PA",             "delay_s": 1,   "severity": "warning"},
        {"to": "ttc",     "effect": "Downlink data rate reduced",                      "delay_s": 5,   "severity": "warning"},
        {"to": "ttc",     "effect": "PA shutdown if temp > 90°C → full link loss",     "delay_s": 60,  "severity": "critical"},
        {"to": "tcs",     "effect": "Transponder compartment heat rises",              "delay_s": 30,  "severity": "info"},
    ],
    ("ttc", "high_ber"): [
        {"to": "ttc",     "effect": "TC frame error rate rises — commands may be lost", "delay_s": 0,  "severity": "warning"},
        {"to": "obdh",    "effect": "TC rejection count increases",                    "delay_s": 5,   "severity": "info"},
    ],
    # OBDH failures
    ("obdh", "watchdog_reset"): [
        {"to": "obdh",    "effect": "OBC reboots → ~30 s blackout",                   "delay_s": 0,   "severity": "critical"},
        {"to": "aocs",    "effect": "AOCS enters safe mode during OBC reboot",         "delay_s": 2,   "severity": "critical"},
        {"to": "payload", "effect": "Payload safed during OBC reboot",                 "delay_s": 1,   "severity": "warning"},
        {"to": "ttc",     "effect": "TM stream interrupted during reboot",             "delay_s": 0,   "severity": "warning"},
        {"to": "obdh",    "effect": "Boots into BOOTLOADER (phase 3) — manual recovery needed","delay_s": 30,"severity": "critical"},
    ],
    ("obdh", "bus_failure"): [
        {"to": "aocs",    "effect": "AOCS commanding via CAN lost → safe mode",        "delay_s": 2,   "severity": "critical"},
        {"to": "payload", "effect": "Payload cannot be commanded → powered off",       "delay_s": 1,   "severity": "critical"},
        {"to": "eps",     "effect": "EPS enters contingency power profile",            "delay_s": 3,   "severity": "warning"},
        {"to": "ttc",     "effect": "TTC in standby awaiting comms restoration",       "delay_s": 1,   "severity": "warning"},
        {"to": "tcs",     "effect": "Heater commanding lost",                          "delay_s": 2,   "severity": "warning"},
    ],
    ("obdh", "obc_crash"): [
        {"to": "obdh",    "effect": "Full OBC crash → watchdog trips within 5 s",     "delay_s": 5,   "severity": "critical"},
        {"to": "aocs",    "effect": "AOCS autonomous safe mode",                       "delay_s": 5,   "severity": "critical"},
        {"to": "payload", "effect": "Payload loses power",                             "delay_s": 5,   "severity": "critical"},
        {"to": "ttc",     "effect": "TM drops — ground sees loss of signal",           "delay_s": 5,   "severity": "critical"},
    ],
    ("obdh", "memory_errors"): [
        {"to": "obdh",    "effect": "Correctable SEU events → scrubber load increases","delay_s": 10,  "severity": "info"},
        {"to": "obdh",    "effect": "Uncorrectable errors may trigger safe mode reboot","delay_s": 300,"severity": "warning"},
        {"to": "aocs",    "effect": "AOCS commanding reliability reduced",             "delay_s": 30,  "severity": "info"},
    ],
    ("obdh", "cpu_spike"): [
        {"to": "obdh",    "effect": "TC processing delayed — commands queued",         "delay_s": 0,   "severity": "warning"},
        {"to": "aocs",    "effect": "AOCS update rate drops if OBC overloaded",        "delay_s": 5,   "severity": "info"},
        {"to": "ttc",     "effect": "TM packetisation may lag",                        "delay_s": 5,   "severity": "info"},
    ],
}

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
# SMO_SCENARIO_DIR redirects saved scenarios (the cloud deployment points it
# at a persistent volume that the simulator also loads, via
# SMO_EXTRA_SCENARIO_DIR); default: the built-in scenario folder.
SCENARIO_DIR = Path(os.environ.get("SMO_SCENARIO_DIR")
                    or REPO_ROOT / "configs" / "eosat1" / "scenarios")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def generate_yaml(data: dict) -> tuple[str, str]:
    """Build YAML text from the form data dict. Returns (yaml_text, filename)."""
    name = data.get("name", "Custom Scenario").strip() or "Custom Scenario"
    difficulty = data.get("difficulty", "BASIC")
    duration = int(data.get("duration_s", 1800))
    briefing = data.get("briefing", "").strip()
    events_raw = data.get("events", [])

    lines = []
    lines.append(f'name: "{name}"')
    lines.append(f"difficulty: {difficulty}")
    lines.append(f"duration_s: {duration}")
    if briefing:
        lines.append("briefing: |")
        for bl in textwrap.wrap(briefing, 72):
            lines.append(f"  {bl}")
    lines.append("")
    lines.append("events:")
    lines.append("")

    for ev in events_raw:
        ev_type = ev.get("type", "inject")

        if ev_type == "inject":
            subsys = ev.get("subsystem", "")
            failure = ev.get("failure", "")
            magnitude = float(ev.get("magnitude", 1.0))
            onset = ev.get("onset", "step")
            onset_dur = ev.get("onset_duration_s", "")
            # Typed parameters, whatever the failure's spec declares. This
            # used to be a hard-coded (wheel, face, axis) triple, so every
            # other unit selector silently fell back to the model default.
            spec = (SUBSYSTEMS.get(subsys, {}).get("failures", {})
                    .get(failure, {}))
            typed = {p["name"]: ev.get(p["name"])
                     for p in (spec.get("params") or [])
                     if ev.get(p["name"]) not in (None, "", [])}
            timing_type = ev.get("timing_type", "time")
            time_offset = ev.get("time_offset_s", 0)
            condition = ev.get("condition", "").strip()
            label = ev.get("label", "").strip()

            if label:
                lines.append(f"  # {label}")
            if timing_type == "condition" and condition:
                lines.append(f'  - condition: "{condition}"')
            else:
                lines.append(f"  - time_offset_s: {int(time_offset)}")
            lines.append(f"    action: inject")
            lines.append(f"    params:")
            lines.append(f"      subsystem: {subsys}")
            lines.append(f"      failure: {failure}")
            lines.append(f"      magnitude: {magnitude}")
            lines.append(f"      onset: {onset}")
            if onset == "gradual" and onset_dur:
                lines.append(f"      onset_duration_s: {int(onset_dur)}")
            for pname, pvalue in typed.items():
                if isinstance(pvalue, (list, tuple)):
                    rendered = "[" + ", ".join(json.dumps(v) for v in pvalue) + "]"
                else:
                    rendered = json.dumps(pvalue)
                lines.append(f"      {pname}: {rendered}")
            lines.append("")

        elif ev_type == "set_parameter":
            param_id = ev.get("param_id", "")
            value = ev.get("value", 0)
            param_name = ev.get("param_name", param_id)
            time_offset = ev.get("time_offset_s", 0)
            label = ev.get("label", "").strip()

            if label:
                lines.append(f"  # {label}")
            else:
                lines.append(f"  # Force {param_name} = {value}")
            lines.append(f"  - time_offset_s: {int(time_offset)}")
            lines.append(f"    action: set_parameter")
            lines.append(f"    params:")
            lines.append(f"      param_id: {param_id}  # {param_name}")
            lines.append(f"      value: {value}")
            lines.append("")

    # expected_responses
    responses = data.get("expected_responses", [])
    if responses:
        lines.append("expected_responses:")
        for r in responses:
            cat = r.get("category", "recover")
            desc = r.get("description", "").strip()
            if desc:
                lines.append(f"  - category: {cat}")
                lines.append(f"    description: >")
                for dl in textwrap.wrap(desc, 70):
                    lines.append(f"      {dl}")
        lines.append("")

    yaml_text = "\n".join(lines)
    filename = _slug(name) + ".yaml"
    return yaml_text, filename


# ── HTML ─────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title data-i18n>Scenario generator</title>
__FRAME_HEAD__
<style>
/* Scenario generator. Left: the form, one hairline section per concern.
   Right: the scenario as a picture (events against the duration, with the
   cascade the model predicts), then the YAML it will save, then Save. */
.sg-wrap{ display:grid; grid-template-columns:minmax(0,1fr) 440px; gap:var(--sp-4); align-items:start; }
.sg-side{ position:sticky; top:64px; display:flex; flex-direction:column; gap:var(--sp-4);
  max-height:calc(100vh - 80px); }
.sg-meta{ display:grid; grid-template-columns:minmax(0,1fr) 180px 140px; gap:var(--sp-3) var(--sp-4); padding:var(--sp-3) var(--sp-4) var(--sp-4); }
.sg-meta .full{ grid-column:1 / -1; }
textarea.ds-input{ min-height:72px; padding:var(--sp-2); font-family:var(--sans); resize:vertical; line-height:var(--lh-text); }
.sg-ev{ border-top:1px solid var(--line); padding:var(--sp-3) var(--sp-4) var(--sp-4); }
.sg-ev:first-child{ border-top:0; }
.sg-ev-h{ display:flex; align-items:center; gap:var(--sp-2); margin-bottom:var(--sp-3); }
.sg-ev-h .t{ font-family:var(--mono); font-size:var(--fs-label); color:var(--tx2); min-width:9ch; }
.sg-ev-h .k{ font-weight:600; color:var(--tx); }
.sg-ev-h .ds-btn{ margin-left:auto; }
.sg-grid{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:var(--sp-3) var(--sp-3); align-items:end; }
.sg-grid .w2{ grid-column:span 2; }
.sg-grid .w4{ grid-column:1 / -1; }
.sg-grid .ds-field[hidden]{ display:none; }
.sg-effect{ grid-column:1 / -1; font-size:var(--fs-label); color:var(--tx3); }
.sg-add{ display:flex; gap:var(--sp-2); padding:var(--sp-3) var(--sp-4); border-top:1px solid var(--line); }
.sg-resp{ display:grid; grid-template-columns:150px minmax(0,1fr) auto; gap:var(--sp-2) var(--sp-3); align-items:start;
  padding:var(--sp-2) var(--sp-4); border-top:1px solid var(--line); }
.sg-tl{ padding:var(--sp-2) var(--sp-4) var(--sp-3); }
.sg-tl .ln{ stroke:var(--line); }
.sg-tl .inj{ fill:var(--val); }
.sg-tl .set{ fill:none; stroke:var(--val); stroke-width:1.5; }
.sg-tl .cw{ fill:var(--bg); stroke:var(--warn); stroke-width:1.5; }
.sg-tl .cc{ fill:var(--alarm); }
.sg-tl .ci{ fill:var(--tx3); }
.sg-tl .lab{ fill:var(--tx2) !important; font-family:var(--sans) !important; }
.sg-tl .end{ stroke:var(--tx3); stroke-dasharray:2 2; }
.sg-yaml{ flex:1 1 auto; min-height:0; display:flex; flex-direction:column; }
.sg-yaml pre{ flex:1 1 auto; overflow:auto; margin:0; padding:var(--sp-3) var(--sp-4); font-family:var(--mono);
  font-size:var(--fs-label); line-height:1.5; color:var(--tx2); background:var(--bg); white-space:pre; min-height:120px; max-height:42vh; }
.sg-act{ display:flex; gap:var(--sp-2); align-items:center; padding:var(--sp-3) var(--sp-4); border-top:1px solid var(--line); flex-wrap:wrap; }
.sg-act .ds-meta{ flex:1 0 100%; }
.sg-list-empty{ padding:var(--sp-4); color:var(--tx3); }
@media (max-width:1100px){
  .sg-wrap{ grid-template-columns:minmax(0,1fr); }
  .sg-side{ position:static; max-height:none; }
}
@media (max-width:720px){
  .sg-meta{ grid-template-columns:1fr 1fr; } .sg-meta .grow{ grid-column:1 / -1; }
  .sg-grid{ grid-template-columns:1fr 1fr; } .sg-grid .w2{ grid-column:1 / -1; }
  .sg-resp{ grid-template-columns:1fr auto; } .sg-resp textarea{ grid-column:1 / -1; }
}
</style>
</head>
<body>
<a class="ds-skip" href="#main" data-i18n>Skip to content</a>
__FRAME_BAR__
<main id="main" class="tf-main sg-wrap">
<div class="ds-stack" style="gap:var(--sp-4)">
  <section class="ds-panel" aria-labelledby="meta-h">
    <div class="ds-panel-h"><span id="meta-h" data-i18n>Scenario</span></div>
    <div class="sg-meta">
      <div class="ds-field grow" id="f-sc-name">
        <label for="sc-name" data-i18n>Scenario name</label>
        <input class="ds-input text" id="sc-name" type="text" placeholder="e.g. Battery thermal runaway" data-i18n-placeholder>
      </div>
      <div class="ds-field">
        <label for="sc-diff" data-i18n>Difficulty</label>
        <select class="ds-select" id="sc-diff"><option>BASIC</option><option>INTERMEDIATE</option><option selected>ADVANCED</option><option>EXPERT</option></select>
      </div>
      <div class="ds-field" id="f-sc-dur">
        <label for="sc-dur" data-i18n>Duration (s)</label>
        <span class="ds-input-wrap"><input class="ds-input" id="sc-dur" inputmode="numeric" value="1800"><span class="u">s</span></span>
      </div>
      <div class="ds-field full">
        <label for="sc-brief" data-i18n>Instructor briefing (not shown to operators)</label>
        <textarea class="ds-input" id="sc-brief" data-i18n-placeholder placeholder="Describe the scenario narrative and what operators must achieve…"></textarea>
      </div>
    </div>
  </section>

  <section class="ds-panel" aria-labelledby="ev-h">
    <div class="ds-panel-h"><span id="ev-h" data-i18n>Failure events and parameter overrides</span><span class="r" id="ev-count"></span></div>
    <div id="events-list"></div>
    <div class="sg-add">
      <button type="button" class="ds-btn" id="add-inject" data-i18n>Add failure</button>
      <button type="button" class="ds-btn" id="add-set" data-i18n>Add parameter override</button>
    </div>
  </section>

  <section class="ds-panel" aria-labelledby="resp-h">
    <div class="ds-panel-h"><span id="resp-h" data-i18n>Expected operator responses</span><span class="r" data-i18n>optional, used for scoring</span></div>
    <div id="resp-list"></div>
    <div class="sg-add"><button type="button" class="ds-btn" id="add-resp" data-i18n>Add response</button></div>
  </section>
</div>

<aside class="sg-side">
  <section class="ds-panel" aria-labelledby="tl-h">
    <div class="ds-panel-h"><span id="tl-h" data-i18n>Scenario timeline</span><span class="r" id="tl-meta"></span></div>
    <div class="sg-tl" id="timeline"></div>
  </section>
  <section class="ds-panel sg-yaml" aria-labelledby="y-h">
    <div class="ds-panel-h"><span id="y-h" data-i18n>Generated YAML</span><span class="r" id="y-file"></span></div>
    <pre id="yaml-out" tabindex="0" aria-labelledby="y-h"></pre>
    <div class="sg-act">
      <button type="button" class="ds-btn primary" id="save-btn" data-i18n>Save scenario</button>
      <button type="button" class="ds-btn" id="copy-btn" data-i18n>Copy YAML</button>
      <span class="ds-meta" id="save-note" role="status" aria-live="polite"></span>
    </div>
    <div id="banner"></div>
  </section>
</aside>
</main>
__FRAME_SCRIPT__
<script type="module">
import { renderBanner, renderButton, setDisabled, setEnabled, glyph, esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
const T = (s, v) => I18n.tText(s, v);
const $ = (id) => document.getElementById(id);
const SUBSYSTEMS = """ + json.dumps(SUBSYSTEMS) + r""";
const PARAMS = """ + json.dumps(PARAMS) + r""";
const CASCADE = __CASCADE_JSON__;

let evId = 0, saved = null, lastYaml = "", lastErr = {}, exists = false, previewTimer = null;

/* ── building blocks ── */
const field = (id, label, control, cls = "") => `<div class="ds-field ${cls}" id="f-${id}"><label for="${id}">${esc(label)}</label>${control}</div>`;
const num = (id, val, unit, attrs = "") => `<span class="ds-input-wrap"><input class="ds-input" id="${id}" inputmode="decimal" value="${esc(val)}"${attrs}>${unit ? `<span class="u">${esc(unit)}</span>` : ""}</span>`;
const sel = (id, opts, attrs = "") => `<select class="ds-select" id="${id}"${attrs}>${opts}</select>`;
const opt = (v, l, on) => `<option value="${esc(v)}"${on ? " selected" : ""}>${esc(l)}</option>`;

function addInject() {
  const id = ++evId;
  const div = document.createElement("div");
  div.className = "sg-ev"; div.id = `ev-${id}`; div.dataset.type = "inject";
  div.innerHTML = `
    <div class="sg-ev-h"><span class="t" id="ev-${id}-tag"></span><span class="k">${esc(T("Failure injection"))}</span>
      ${renderButton({ label: T("Remove"), kind: "ghost", size: "sm", attrs: `data-remove="ev-${id}" aria-label="${esc(T("Remove event"))}"` })}</div>
    <div class="sg-grid">
      ${field(`ev-${id}-timing`, T("Timing"), sel(`ev-${id}-timing`, opt("time", T("At time (s)")) + opt("condition", T("Condition"))))}
      ${field(`ev-${id}-time`, T("Time offset (s)"), num(`ev-${id}-time`, 0, "s"))}
      ${field(`ev-${id}-cond`, T("Condition (e.g. 257 < 60)"), `<input class="ds-input" id="ev-${id}-cond" placeholder="257 < 60">`, "w2").replace('class="ds-field w2"', 'class="ds-field w2" hidden')}
      ${field(`ev-${id}-sub`, T("Subsystem"), sel(`ev-${id}-sub`, Object.entries(SUBSYSTEMS).map(([k, v]) => opt(k, v.label)).join("")), "w2")}
      ${field(`ev-${id}-fail`, T("Failure"), sel(`ev-${id}-fail`, ""), "w2")}
      ${field(`ev-${id}-mag`, T("Magnitude (0–1)"), num(`ev-${id}-mag`, "1.0", ""))}
      ${field(`ev-${id}-onset`, T("Onset"), sel(`ev-${id}-onset`, ["step", "gradual", "intermittent"].map((o) => opt(o, o)).join("")))}
      <div class="sg-grid w4" id="ev-${id}-extras" style="padding:0"></div>
      <p class="sg-effect" id="ev-${id}-effect"></p>
      ${field(`ev-${id}-label`, T("Label / comment (optional)"), `<input class="ds-input text" id="ev-${id}-label" placeholder="${esc(T("e.g. SA-2B impact at T+0"))}">`, "w4")}
    </div>`;
  $("events-list").appendChild(div);
  updateFailures(id);
  changed();
}
function addSetParam() {
  const id = ++evId;
  const div = document.createElement("div");
  div.className = "sg-ev"; div.id = `ev-${id}`; div.dataset.type = "set_parameter";
  div.innerHTML = `
    <div class="sg-ev-h"><span class="t" id="ev-${id}-tag"></span><span class="k">${esc(T("Set parameter"))}</span>
      ${renderButton({ label: T("Remove"), kind: "ghost", size: "sm", attrs: `data-remove="ev-${id}" aria-label="${esc(T("Remove event"))}"` })}</div>
    <div class="sg-grid">
      ${field(`ev-${id}-time`, T("Time offset (s)"), num(`ev-${id}-time`, 0, "s"))}
      ${field(`ev-${id}-param`, T("Parameter"), sel(`ev-${id}-param`, PARAMS.map((p) => `<option value="${esc(p.id)}" data-name="${esc(p.name)}" data-unit="${esc(p.unit || "")}">${esc(p.desc)} (${esc(p.id)})</option>`).join("")), "w2")}
      ${field(`ev-${id}-value`, T("Value"), num(`ev-${id}-value`, 0, PARAMS[0] ? PARAMS[0].unit : ""))}
      ${field(`ev-${id}-label`, T("Label / comment (optional)"), `<input class="ds-input text" id="ev-${id}-label" placeholder="${esc(T("e.g. Force bus voltage low"))}">`, "w4")}
    </div>`;
  $("events-list").appendChild(div);
  changed();
}
function addResponse() {
  const id = ++evId;
  const div = document.createElement("div");
  div.className = "sg-resp"; div.id = `resp-${id}`;
  div.innerHTML = `<select class="ds-select" aria-label="${esc(T("Response category"))}">${["detect", "isolate", "recover", "verify"].map((c) => opt(c, c)).join("")}</select>` +
    `<textarea class="ds-input" aria-label="${esc(T("Expected response"))}" placeholder="${esc(T("Describe what the operator should do…"))}"></textarea>` +
    renderButton({ label: T("Remove"), kind: "ghost", size: "sm", attrs: `data-remove="resp-${id}" aria-label="${esc(T("Remove response"))}"` });
  $("resp-list").appendChild(div);
  changed();
}

function updateFailures(id) {
  const sub = $(`ev-${id}-sub`).value;
  $(`ev-${id}-fail`).innerHTML = Object.entries(SUBSYSTEMS[sub]?.failures || {}).map(([k, v]) => opt(k, v.label)).join("");
  updateExtras(id);
}
// Typed parameter controls straight from the failure's ParamSpec list.
function updateExtras(id) {
  const sub = $(`ev-${id}-sub`).value, fail = $(`ev-${id}-fail`).value, onset = $(`ev-${id}-onset`).value;
  const spec = SUBSYSTEMS[sub]?.failures?.[fail];
  let html = "";
  for (const p of (spec?.params || [])) {
    const cid = `ev-${id}-p-${p.name}`, label = (p.label || p.name);
    if (p.type === "bool") {
      html += field(cid, label, sel(cid, opt("true", T("Yes"), !!p.default) + opt("false", T("No"), !p.default), ` data-param="${esc(p.name)}"`));
    } else if (p.type === "enum") {
      const values = p.values || [], labels = p.value_labels || values.map(String);
      const defs = Array.isArray(p.default) ? p.default.map(String) : (p.default == null ? [] : [String(p.default)]);
      html += field(cid, label, sel(cid, values.map((v, i) => opt(v, labels[i], defs.includes(String(v)))).join(""),
        ` data-param="${esc(p.name)}" data-multi="${p.multi ? "1" : ""}"${p.multi ? ' multiple size="4"' : ""}`));
    } else {
      const lim = [p.min, p.max];
      html += field(cid, label, num(cid, p.default ?? "", p.unit || "",
        ` data-param="${esc(p.name)}" data-ptype="${esc(p.type)}" data-min="${lim[0] ?? ""}" data-max="${lim[1] ?? ""}"`));
    }
  }
  if (onset === "gradual") html += field(`ev-${id}-onset-dur`, T("Onset duration (s)"), num(`ev-${id}-onset-dur`, 60, "s"));
  $(`ev-${id}-extras`).innerHTML = html;
  $(`ev-${id}-effect`).textContent = spec && spec.effect ? spec.effect : "";
}
function collectExtras(id) {
  const out = {};
  document.querySelectorAll(`#ev-${id}-extras [data-param]`).forEach((el) => {
    const name = el.dataset.param;
    if (el.dataset.multi) {
      const vals = Array.from(el.selectedOptions).map((o) => { const n = Number(o.value); return Number.isFinite(n) && o.value.trim() !== "" ? n : o.value; });
      if (vals.length) out[name] = vals; return;
    }
    const raw = (el.value ?? "").toString().trim();
    if (raw === "") return;
    if (raw === "true" || raw === "false") { out[name] = raw === "true"; return; }
    const n = Number(raw); out[name] = Number.isFinite(n) ? n : raw;
  });
  return out;
}

function collectData() {
  const events = [];
  document.querySelectorAll("#events-list .sg-ev").forEach((card) => {
    const id = card.id.replace("ev-", "");
    if (card.dataset.type === "inject") {
      events.push({
        type: "inject", timing_type: $(`ev-${id}-timing`).value,
        time_offset_s: parseInt($(`ev-${id}-time`).value) || 0,
        condition: ($(`ev-${id}-cond`).value || "").trim(),
        subsystem: $(`ev-${id}-sub`).value, failure: $(`ev-${id}-fail`).value,
        magnitude: parseFloat($(`ev-${id}-mag`).value) || 1.0, onset: $(`ev-${id}-onset`).value,
        onset_duration_s: $(`ev-${id}-onset-dur`) ? $(`ev-${id}-onset-dur`).value : "",
        ...collectExtras(id), label: ($(`ev-${id}-label`).value || "").trim(),
      });
    } else {
      const s = $(`ev-${id}-param`), o = s.options[s.selectedIndex];
      events.push({ type: "set_parameter", time_offset_s: parseInt($(`ev-${id}-time`).value) || 0,
        param_id: s.value, param_name: o ? o.dataset.name : s.value,
        value: parseFloat($(`ev-${id}-value`).value) || 0, label: ($(`ev-${id}-label`).value || "").trim() });
    }
  });
  const expected_responses = [];
  document.querySelectorAll("#resp-list .sg-resp").forEach((row) => {
    const d = row.querySelector("textarea").value.trim();
    if (d) expected_responses.push({ category: row.querySelector("select").value, description: d });
  });
  return { name: $("sc-name").value.trim() || "Custom Scenario", difficulty: $("sc-diff").value,
    duration_s: parseInt($("sc-dur").value) || 1800, briefing: $("sc-brief").value.trim(), events, expected_responses };
}

/* ── validation: errors block saving; cautions are shown, never block ── */
// Field messages appear once a field has been visited (or Save was tried):
// an untouched form is not an error, the Save button's reason says what is missing.
const touched = new Set();
let showAll = false;
function setErr(id, msg, kind = "err") {
  if (msg && !showAll && !touched.has(id)) msg = "";
  const f = $("f-" + id), inp = $(id);
  if (!f || !inp) return;
  f.classList.toggle("is-invalid", kind === "err" && !!msg);
  f.querySelectorAll(".err,.hint.sg-c").forEach((e) => e.remove());
  if (msg) {
    const e = document.createElement("span");
    e.id = id + "-msg";
    if (kind === "err") { e.className = "err"; e.innerHTML = glyph("alarm-up") + esc(msg); inp.setAttribute("aria-invalid", "true"); }
    else { e.className = "hint sg-c"; e.style.color = "var(--warn)"; e.innerHTML = glyph("warn-up") + " " + esc(msg); inp.removeAttribute("aria-invalid"); }
    f.appendChild(e); inp.setAttribute("aria-describedby", e.id);
  } else { inp.removeAttribute("aria-invalid"); inp.removeAttribute("aria-describedby"); }
}
function validate() {
  const errs = [], dur = Number($("sc-dur").value);
  const bad = (id, msg) => { setErr(id, msg); errs.push(msg); };
  if (!$("sc-name").value.trim()) bad("sc-name", T("Name the scenario: the file name comes from it."));
  else setErr("sc-name", "");
  if (!Number.isInteger(dur) || dur < 60) bad("sc-dur", T("At least 60 s, whole seconds."));
  else setErr("sc-dur", "");
  const cards = document.querySelectorAll("#events-list .sg-ev");
  cards.forEach((card) => {
    const id = card.id.replace("ev-", "");
    const timed = card.dataset.type !== "inject" || $(`ev-${id}-timing`).value === "time";
    if (timed) {
      const t = Number($(`ev-${id}-time`).value);
      if (!Number.isFinite(t) || t < 0) bad(`ev-${id}-time`, T("A time of 0 s or later."));
      else setErr(`ev-${id}-time`, t > dur ? T("After the end of the scenario ({{d}} s).", { d: dur }) : "", "caution");
    } else {
      const c = ($(`ev-${id}-cond`).value || "").trim();
      if (!/^\d+\s*(<=|>=|==|!=|<|>)\s*-?\d+(\.\d+)?$/.test(c)) bad(`ev-${id}-cond`, T("Write it as: decimal parameter ID, operator, value (257 < 60)."));
      else setErr(`ev-${id}-cond`, "");
    }
    if (card.dataset.type === "inject") {
      const m = Number($(`ev-${id}-mag`).value);
      if (!(m >= 0 && m <= 1)) bad(`ev-${id}-mag`, T("Between 0 and 1.")); else setErr(`ev-${id}-mag`, "");
      card.querySelectorAll("[data-ptype]").forEach((el) => {
        const v = el.value.trim(); if (v === "") return setErr(el.id, "");
        const n = Number(v), lo = el.dataset.min, hi = el.dataset.max;
        if (!Number.isFinite(n) || (lo !== "" && n < +lo) || (hi !== "" && n > +hi) || (el.dataset.ptype === "int" && !Number.isInteger(n)))
          bad(el.id, lo !== "" && hi !== "" ? T("Between {{a}} and {{b}}.", { a: lo, b: hi }) : T("Enter a number."));
        else setErr(el.id, "");
      });
    } else {
      const v = Number($(`ev-${id}-value`).value);
      if (!Number.isFinite(v) || $(`ev-${id}-value`).value.trim() === "") bad(`ev-${id}-value`, T("Enter a number.")); else setErr(`ev-${id}-value`, "");
    }
    const tag = $(`ev-${id}-tag`);
    if (tag) tag.textContent = timed ? `T+${$(`ev-${id}-time`).value || 0} s` : T("on condition");
  });
  if (!cards.length) errs.push(T("Add at least one failure or parameter override."));
  $("ev-count").textContent = cards.length ? T("{{n}} event(s)", { n: cards.length }) : "";
  if (!cards.length && !$("events-list").querySelector(".sg-list-empty"))
    $("events-list").innerHTML = `<p class="sg-list-empty">${esc(T("No events yet. A scenario needs at least one failure or parameter override."))}</p>`;
  if (cards.length) { const e = $("events-list").querySelector(".sg-list-empty"); if (e) e.remove(); }
  if (!$("resp-list").children.length) $("resp-list").innerHTML = `<p class="sg-list-empty">${esc(T("No expected responses. Add them to score the class."))}</p>`;
  else if ($("resp-list").children.length > 1) { const e = $("resp-list").querySelector(".sg-list-empty"); if (e) e.remove(); }
  const sb = $("save-btn");
  if (errs.length) setDisabled(sb, errs.length === 1 ? errs[0] : T("{{n}} problems to fix first. The first: {{e}}", { n: errs.length, e: errs[0] }));
  else setEnabled(sb);
  return !errs.length;
}

/* ── saved / not saved ── */
function paintSaveState() {
  const st = $("tf-status");
  const cur = JSON.stringify(collectData());
  if (!saved) st.innerHTML = `<span class="ds-chip is-stale">${esc(T("Not saved"))}</span>`;
  else if (saved.data !== cur) st.innerHTML = `<span class="ds-chip is-caution">${glyph("warn-up")}${esc(T("Changed since saved"))}</span>`;
  else st.innerHTML = `<span class="ds-chip ok">${glyph("ack")}${esc(T("Saved"))}</span>`;
  const note = $("save-note");
  note.textContent = saved && saved.data === cur ? T("Saved to {{path}} at {{t}}", { path: saved.path, t: saved.time })
    : exists ? T("A scenario file with this name exists: saving replaces it.") : "";
  note.style.color = !(saved && saved.data === cur) && exists ? "var(--warn)" : "";
}

/* ── live preview: the YAML that Save would write ── */
async function preview() {
  try {
    const r = await fetch("generate", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...collectData(), save: false }) });
    const j = await r.json();
    if (j.ok) { lastYaml = j.yaml; $("yaml-out").textContent = j.yaml; $("y-file").textContent = j.filename; exists = !!j.exists; }
    else $("banner").innerHTML = renderBanner("alarm", j.error || T("Unknown error"));
  } catch (e) { $("banner").innerHTML = renderBanner("alarm", String(e)); }
  paintSaveState();
}
function changed() {
  validate(); drawTimeline(); paintSaveState();
  clearTimeout(previewTimer); previewTimer = setTimeout(preview, 250);
}
async function save() {
  showAll = true;
  if (!validate()) return;
  const sb = $("save-btn"), label = sb.textContent;
  sb.classList.add("is-active"); sb.innerHTML = `<span class="ds-run" aria-hidden="true"></span>${esc(T("Saving…"))}`;
  $("banner").innerHTML = "";
  try {
    const data = collectData();
    const r = await fetch("generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, save: true }) });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || T("Unknown error"));
    saved = { data: JSON.stringify(data), path: j.path, time: new Date().toTimeString().slice(0, 5) };
    lastYaml = j.yaml; $("yaml-out").textContent = j.yaml; exists = true;
  } catch (e) {
    $("banner").innerHTML = renderBanner("alarm", T("Not saved: {{msg}}", { msg: e.message }), { role: "alert" });
  } finally {
    sb.classList.remove("is-active"); sb.textContent = label;
    paintSaveState();
  }
}

/* ── the picture: events and predicted cascade against the duration ── */
const SUBS = ["eps", "aocs", "tcs", "obdh", "ttc", "payload", "prop"];
function drawTimeline() {
  const host = $("timeline"), data = collectData(), dur = Math.max(60, data.duration_s);
  const W = Math.max(280, host.clientWidth - 32), L = 64, R = 10, laneH = 22, top = 6;
  const used = new Set();
  const items = [];
  data.events.forEach((e) => {
    const t = e.type === "inject" && e.timing_type === "condition" ? null : e.time_offset_s;
    const sub = e.type === "inject" ? e.subsystem : (e.param_name || "").split(".")[0];
    items.push({ t, sub, kind: e.type === "inject" ? "inj" : "set", tip: e.type === "inject" ? `${e.subsystem}: ${e.failure}` : `${e.param_name} = ${e.value}` });
    if (e.type === "inject") for (const c of (CASCADE[`${e.subsystem}::${e.failure}`] || []))
      items.push({ t: t == null ? null : t + (c.delay_s || 0), sub: c.to, kind: c.severity === "critical" ? "cc" : c.severity === "warning" ? "cw" : "ci", tip: c.effect });
  });
  items.forEach((i) => used.add(i.sub));
  const lanes = SUBS.filter((s) => used.has(s)).concat([...used].filter((s) => !SUBS.includes(s)));
  if (!lanes.length) { host.innerHTML = `<p class="ds-meta" style="padding:var(--sp-3) 0">${esc(T("Add an event to see it on the timeline."))}</p>`; $("tl-meta").textContent = ""; return; }
  const maxT = Math.max(dur, ...items.filter((i) => i.t != null).map((i) => i.t));
  const X = (t) => L + (t / maxT) * (W - L - R);
  const H = top + lanes.length * laneH + 22;
  let s = `<svg class="tf-plot" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-labelledby="tl-h tl-desc">` +
    `<desc id="tl-desc">${esc(T("Events and the cascade the model predicts, one lane per subsystem, over the scenario duration."))}</desc>`;
  const step = [60, 120, 300, 600, 900, 1800, 3600, 7200].find((x) => maxT / x <= 6) || 7200;
  for (let t = 0; t <= maxT; t += step) s += `<line class="grid" x1="${X(t)}" y1="${top}" x2="${X(t)}" y2="${H - 18}"/><text x="${X(t)}" y="${H - 4}" text-anchor="${t ? "middle" : "start"}">${t >= 60 ? (t / 60) + " min" : t + " s"}</text>`;
  if (maxT > dur) s += `<line class="end" x1="${X(dur)}" y1="${top}" x2="${X(dur)}" y2="${H - 18}"><title>${esc(T("End of the scenario"))}</title></line>`;
  lanes.forEach((ln, i) => {
    const y = top + i * laneH + laneH / 2;
    s += `<line class="ln" x1="${L}" y1="${y + laneH / 2}" x2="${W - R}" y2="${y + laneH / 2}"/><text class="lab" x="0" y="${y + 4}">${esc(ln.toUpperCase())}</text>`;
    for (const it of items.filter((q) => q.sub === ln)) {
      const x = it.t == null ? W - R - 4 : X(it.t), tip = `<title>${esc((it.t == null ? T("on condition") : `T+${it.t} s`) + " · " + it.tip)}</title>`;
      s += it.kind === "inj" ? `<rect class="inj" x="${x - 4}" y="${y - 6}" width="8" height="12" rx="1">${tip}</rect>`
        : it.kind === "set" ? `<rect class="set" x="${x - 4}" y="${y - 5}" width="8" height="10" rx="1">${tip}</rect>`
        : `<path class="${it.kind}" d="M${x} ${y - 6}L${x + 6} ${y + 5}L${x - 6} ${y + 5}Z">${tip}</path>`;
    }
  });
  s += `</svg>`;
  host.innerHTML = s +
    `<div class="ds-row ds-meta" style="margin-top:var(--sp-2);gap:var(--sp-1) var(--sp-4)">` +
    `<span><svg width="10" height="12" aria-hidden="true"><rect class="inj" x="1" y="0" width="8" height="12" style="fill:var(--val)"/></svg> ${esc(T("Failure"))}</span>` +
    `<span><svg width="10" height="12" aria-hidden="true"><rect x="1" y="1" width="8" height="10" style="fill:none;stroke:var(--val);stroke-width:1.5"/></svg> ${esc(T("Override"))}</span>` +
    `<span><svg width="12" height="12" aria-hidden="true"><path d="M6 0L12 11L0 11Z" style="fill:var(--bg);stroke:var(--warn);stroke-width:1.5"/></svg> ${esc(T("Predicted warning"))}</span>` +
    `<span><svg width="12" height="12" aria-hidden="true"><path d="M6 0L12 11L0 11Z" style="fill:var(--alarm)"/></svg> ${esc(T("Predicted critical"))}</span></div>`;
  $("tl-meta").textContent = T("{{d}} min", { d: (dur / 60).toFixed(0) });
}

/* ── wiring ── */
$("add-inject").addEventListener("click", addInject);
$("add-set").addEventListener("click", addSetParam);
$("add-resp").addEventListener("click", addResponse);
$("save-btn").addEventListener("click", save);
$("copy-btn").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(lastYaml); $("save-note").textContent = T("YAML copied."); } catch (e) { /* no clipboard */ }
});
document.addEventListener("click", (ev) => {
  const b = ev.target.closest("[data-remove]");
  if (b) { $(b.dataset.remove)?.remove(); changed(); }
});
$("main").addEventListener("change", (ev) => {
  const m = /^ev-(\d+)-(sub|fail|onset|timing|param)$/.exec(ev.target.id || "");
  if (m) {
    const id = m[1];
    if (m[2] === "sub") updateFailures(id);
    if (m[2] === "fail" || m[2] === "onset") updateExtras(id);
    if (m[2] === "timing") {
      const cond = ev.target.value === "condition";
      $(`f-ev-${id}-time`).hidden = cond; $(`f-ev-${id}-cond`).hidden = !cond;
    }
    if (m[2] === "param") {
      const o = ev.target.options[ev.target.selectedIndex], u = $(`f-ev-${id}-value`).querySelector(".u");
      if (u) u.textContent = o.dataset.unit || "";
    }
  }
  changed();
});
$("main").addEventListener("input", changed);
$("main").addEventListener("focusout", (ev) => { if (ev.target.id) { touched.add(ev.target.id); validate(); } });
window.addEventListener("beforeunload", (ev) => {
  if ((saved && saved.data !== JSON.stringify(collectData())) || (!saved && document.querySelector("#events-list .sg-ev"))) { ev.preventDefault(); ev.returnValue = ""; }
});
new ResizeObserver(drawTimeline).observe($("timeline"));
const rerender = () => { changed(); document.getElementById("tf-meta").textContent = T("Saves to the scenario library"); };
window.addEventListener("smo:i18nready", rerender);
window.addEventListener("smo:langchange", rerender);
rerender();
</script>
</body>
</html>
"""


# ── aiohttp handlers ──────────────────────────────────────────────────────────

async def handle_index(request):
    from smo_common.web.http import tool_html_response
    import tool_frame          # shared page frame: TOOL_HEAD + title bar
    cascade_json = json.dumps({f"{k[0]}::{k[1]}": v for k, v in CASCADE_MAP.items()})
    page = (HTML.replace("__CASCADE_JSON__", cascade_json.replace("</", "<\\/"))
            .replace("__FRAME_HEAD__", tool_frame.head())
            .replace("__FRAME_BAR__", tool_frame.bar('<span data-i18n>Scenario generator</span>'))
            .replace("__FRAME_SCRIPT__", tool_frame.SCRIPT))
    return tool_html_response(page, request.app)


async def handle_generate(request):
    try:
        data = await request.json()
    except Exception as e:
        return web.json_response({"ok": False, "error": f"Bad JSON: {e}"})

    try:
        yaml_text, filename = generate_yaml(data)
    except Exception as e:
        return web.json_response({"ok": False, "error": f"YAML generation failed: {e}"})

    save = data.get("save", False)
    saved_path = ""
    # Saving writes configs/<mission>/scenarios/<slug>.yaml and REPLACES a
    # file of the same name; the page warns before that happens.
    exists = (SCENARIO_DIR / filename).is_file()
    if save:
        try:
            SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
            out_path = SCENARIO_DIR / filename
            out_path.write_text(yaml_text)
            from smo_common.web.http import relative_display_path
            saved_path = relative_display_path(out_path, REPO_ROOT)
        except Exception as e:
            # Never send the absolute server path to the page (R3 audit A9).
            msg = str(e).replace(str(REPO_ROOT) + os.sep, "").replace(str(REPO_ROOT), ".")
            return web.json_response({"ok": False, "error": f"Could not write file: {msg}"})

    return web.json_response({"ok": True, "yaml": yaml_text, "path": saved_path,
                              "filename": filename, "exists": exists})


def main():
    parser = argparse.ArgumentParser(description="SMO Scenario Generator")
    parser.add_argument("--port", type=int, default=8096)
    parser.add_argument("--host", default="localhost")
    args = parser.parse_args()

    # Shared HTTP policy + design system / language runtime (R3 A8, §8).
    from smo_common.web.http import setup_tool_app
    app = setup_tool_app(web.Application())
    app.router.add_get("/", handle_index)
    app.router.add_post("/generate", handle_generate)

    print(f"SMO Scenario Generator → http://{args.host}:{args.port}")
    web.run_app(app, host=args.host, port=args.port, print=lambda *_: None)


if __name__ == "__main__":
    main()
