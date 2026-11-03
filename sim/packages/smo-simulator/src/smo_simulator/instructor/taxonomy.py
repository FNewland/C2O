"""Instructor fault menu: the failure catalogue organised by control-loop element.

The Ames SimSup practice for LADEE and NuSTAR (Owens & Crocker, NTRS
20150021505) sorted injects by where they sit in the control loop. The
instructor console uses the same structure for its fault menu instead of a
flat list per subsystem (the F-14 console's ten-page malfunction list was the
cautionary case), and the structure is also what the debrief explains.

Every failure in ``failure_catalog`` must have an entry here; a test fails
when a model adds a failure without one, so the menu can never silently drop
a failure.

``inject_class`` separates the two kinds the nuclear simulator standard keeps
apart: a *physical* fault changes the spacecraft; an *indication* fault makes
a sensor, an estimate or a clock lie while the truth is unchanged. Only an
indication fault is a cause of truth-versus-telemetry divergence.
"""
from __future__ import annotations

from typing import Any

#: Control-loop elements, in loop order (menu order). English text is the
#: i18n key the console translates.
ELEMENTS: tuple[dict[str, str], ...] = (
    {"id": "control_input", "label": "Control input",
     "hint": "Commands cannot reach the spacecraft or arrive wrong"},
    {"id": "controller", "label": "Controller",
     "hint": "On-board software, computer and control laws"},
    {"id": "actuator", "label": "Actuator",
     "hint": "Wheels, torquers, heaters, switches, valves, drives"},
    {"id": "process", "label": "Process",
     "hint": "The physical plant: arrays, battery, bus, tanks, zones"},
    {"id": "process_input", "label": "Process input",
     "hint": "Outside the spacecraft: ground station and RF path"},
    {"id": "disturbance", "label": "Disturbance",
     "hint": "Upsets and unplanned heat: SEU, memory errors, heat leaks"},
    {"id": "observer", "label": "Observer (sensor)",
     "hint": "Sensors, estimates and clocks lie; the truth is unchanged"},
    {"id": "data", "label": "Data path and products",
     "hint": "Buses, transponders, mass memory and image products"},
)
ELEMENT_IDS = tuple(e["id"] for e in ELEMENTS)

#: (subsystem, failure) -> control-loop element.
ELEMENT_OF: dict[tuple[str, str], str] = {
    # EPS
    ("eps", "solar_array_partial"): "process",
    ("eps", "solar_panel_loss"): "process",
    ("eps", "solar_array_total_loss"): "process",
    ("eps", "bat_cell"): "process",
    ("eps", "bus_short"): "process",
    ("eps", "overcurrent"): "actuator",
    ("eps", "undervoltage"): "process",
    ("eps", "overvoltage"): "controller",
    ("eps", "sada_stuck"): "actuator",
    # AOCS
    ("aocs", "rw_bearing"): "actuator",
    ("aocs", "rw_seizure"): "actuator",
    ("aocs", "multi_wheel_failure"): "actuator",
    ("aocs", "gyro_bias"): "observer",
    ("aocs", "st_blind"): "observer",
    ("aocs", "st_failure"): "observer",
    ("aocs", "css_failure"): "observer",
    ("aocs", "css_head_fail"): "observer",
    ("aocs", "mag_failure"): "observer",
    ("aocs", "mtq_failure"): "actuator",
    ("aocs", "gain_corruption"): "controller",
    # TCS
    ("tcs", "heater_failure"): "actuator",
    ("tcs", "heater_stuck_on"): "actuator",
    ("tcs", "heater_open_circuit"): "actuator",
    ("tcs", "cooler_failure"): "actuator",
    ("tcs", "obc_thermal"): "disturbance",
    ("tcs", "sensor_drift"): "observer",
    ("tcs", "cold_soak"): "disturbance",
    ("tcs", "temp_anomaly"): "process",
    # OBDH
    ("obdh", "watchdog_reset"): "controller",
    ("obdh", "obc_crash"): "controller",
    ("obdh", "memory_errors"): "disturbance",
    ("obdh", "memory_corruption"): "disturbance",
    ("obdh", "memory_segment_fail"): "data",
    ("obdh", "cpu_spike"): "controller",
    ("obdh", "bus_failure"): "data",
    ("obdh", "boot_image_corrupt"): "controller",
    ("obdh", "stuck_in_bootloader"): "controller",
    ("obdh", "clock_drift"): "observer",
    # TT&C
    ("ttc", "primary_failure"): "data",
    ("ttc", "redundant_failure"): "data",
    ("ttc", "high_ber"): "data",
    ("ttc", "pa_overheat"): "data",
    ("ttc", "uplink_loss"): "control_input",
    ("ttc", "receiver_degrade"): "control_input",
    ("ttc", "antenna_deploy_failed"): "actuator",
    ("ttc", "gs_lna_degradation"): "process_input",
    ("ttc", "gs_antenna_mispoint"): "process_input",
    ("ttc", "gs_feed_loss"): "process_input",
    ("ttc", "gs_rfi_interference"): "process_input",
    ("ttc", "gs_hpa_degradation"): "process_input",
    ("ttc", "gs_ref_osc_drift"): "process_input",
    ("ttc", "gs_tracking_loss"): "process_input",
    # Payload
    ("payload", "cooler_failure"): "actuator",
    ("payload", "fpa_degraded"): "data",
    ("payload", "image_corrupt"): "data",
    ("payload", "memory_segment_fail"): "data",
    ("payload", "ccd_line_dropout"): "data",
    # Propulsion
    ("prop", "leak"): "process",
    ("prop", "latch_stuck_open"): "actuator",
    ("prop", "thrust_degraded"): "actuator",
    ("prop", "tank_overpressure"): "process",
}

#: What each fault degrades (Rasmussen's abstraction hierarchy, read
#: bottom-up: component -> generalised function -> mission objective). Drawn
#: as the causal chain in the fault view. Keyed by subsystem; a failure may
#: override it in FUNCTION_OF_FAILURE.
FUNCTION_OF_SUBSYSTEM: dict[str, tuple[str, str]] = {
    "eps": ("Energy balance", "Keep the spacecraft powered"),
    "aocs": ("Pointing and momentum", "Image the target; keep arrays on the sun"),
    "tcs": ("Thermal balance", "Keep units inside their temperature limits"),
    "obdh": ("Command, data and autonomy", "Keep the spacecraft safe and commandable"),
    "ttc": ("Communication with the ground", "Downlink data and accept commands"),
    "payload": ("Image acquisition", "Deliver usable images"),
    "prop": ("Orbit control", "Keep the orbit and avoid collisions"),
}
FUNCTION_OF_FAILURE: dict[tuple[str, str], tuple[str, str]] = {
    ("obdh", "clock_drift"): ("Time knowledge", "Time-tag data and run schedules on time"),
    ("ttc", "uplink_loss"): ("Command reception", "Accept commands from the ground"),
    ("ttc", "receiver_degrade"): ("Command reception", "Accept commands from the ground"),
    ("eps", "sada_stuck"): ("Array pointing", "Keep the spacecraft powered"),
    ("tcs", "cooler_failure"): ("Focal-plane cooling", "Deliver usable images"),
    ("payload", "cooler_failure"): ("Focal-plane cooling", "Deliver usable images"),
}

#: Which view of the instructor console shows a subsystem's truth best.
VIEW_OF_SUBSYSTEM: dict[str, str] = {
    "eps": "power", "aocs": "attitude", "tcs": "thermal", "obdh": "obc",
    "ttc": "orbit", "payload": "storage", "prop": "power",
}


def element_of(subsystem: str, failure: str) -> str:
    """Control-loop element of a failure ("process" if unclassified)."""
    return ELEMENT_OF.get((subsystem, failure), "process")


def inject_class(subsystem: str, failure: str) -> str:
    """``indication`` (a sensor/estimate/clock lie) or ``physical``."""
    return "indication" if element_of(subsystem, failure) == "observer" else "physical"


def function_of(subsystem: str, failure: str) -> tuple[str, str]:
    return FUNCTION_OF_FAILURE.get(
        (subsystem, failure),
        FUNCTION_OF_SUBSYSTEM.get(subsystem, ("Spacecraft function", "Mission")))


def view_for(subsystem: str, failure: str = "") -> str:
    """Focus-pane view an inject of this failure should bring up."""
    if failure and inject_class(subsystem, failure) == "indication":
        return "divergence"
    return VIEW_OF_SUBSYSTEM.get(subsystem, "overview")


def fault_menu() -> dict[str, Any]:
    """The failure catalogue grouped by control-loop element.

    ``{"elements": [{id, label, hint, failures: [{subsystem, name, label,
    effect, inject_class, function, objective}]}]}`` — the parameter specs
    themselves stay in GET /api/failure-catalog (one source of truth for the
    form); this only adds the grouping and the causal-chain text.
    """
    from smo_simulator import failure_catalog

    groups: dict[str, list[dict[str, Any]]] = {e: [] for e in ELEMENT_IDS}
    for sub, failures in failure_catalog.catalog().items():
        for name, spec in failures.items():
            fn, obj = function_of(sub, name)
            groups[element_of(sub, name)].append({
                "subsystem": sub, "name": name, "label": spec.label,
                "effect": spec.effect, "reversible": spec.reversible,
                "inject_class": inject_class(sub, name),
                "function": fn, "objective": obj,
                "view": view_for(sub, name),
            })
    out = []
    for e in ELEMENTS:
        items = sorted(groups[e["id"]], key=lambda f: (f["subsystem"], f["label"]))
        out.append({**e, "failures": items})
    return {"elements": out}
