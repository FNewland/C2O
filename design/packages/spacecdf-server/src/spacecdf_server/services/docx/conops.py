"""SpaceCDF Word document family: conops. Concept of Operations (ConOps).

Moved verbatim from services/docx_generator.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for ownership.
"""
from __future__ import annotations

import io
from typing import Any

from docx import Document

from ._common import (
    _add_cover_page,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _render_bullet,
    _render_rich_content,
    _setup_margins,
    _setup_styles,
)


def generate_conops_docx(
    study_name: str = "",
    mission_need: dict[str, Any] | None = None,
    conops: dict[str, Any] | None = None,
    orbit: dict[str, Any] | None = None,
    elements: list[dict[str, Any]] | None = None,
) -> bytes:
    """Generate Concept of Operations document as .docx bytes."""
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    mn = mission_need or {}
    ops = conops or {}
    orb = orbit or {}
    elems = elements or []

    _add_cover_page(doc, "Concept of Operations", "NASA SEH Appendix S", study_name)
    _add_toc_placeholder(doc)
    _add_footer(doc, study_name)

    # ── Section 1: Mission Overview ──
    _add_section(doc, "1", "Mission Overview")
    _add_section(doc, "1.1", "Purpose",
                 f"This document describes the concept of operations for the {study_name} "
                 f"mission, defining how the system will be operated throughout its "
                 f"lifecycle to meet mission objectives.")
    problem = mn.get("problem_statement", "")
    sel_rationale = mn.get("selection_rationale", "")
    overview_parts = []
    if problem:
        overview_parts.append(problem)
    if sel_rationale:
        overview_parts.append(f"\n\n**Selected Concept:** {sel_rationale}")
    _add_section(doc, "1.2", "Mission Description",
                 "\n".join(overview_parts) if overview_parts else "[To be defined]")
    op_context = mn.get("operational_context", "")
    if op_context:
        _add_section(doc, "1.3", "Operational Context", op_context)

    # ── Section 2: Orbital Parameters ──
    _add_section(doc, "2", "Orbital Parameters")
    if orb:
        orbit_rows = [
            ["Orbit Type", str(orb.get("orbit_type", "TBD"))],
            ["Altitude", f"{orb.get('altitude_km', 'TBD')} km"],
            ["Inclination", f"{orb.get('inclination_deg', 'TBD')} deg"],
            ["Eccentricity", str(orb.get("eccentricity", "0.0"))],
        ]
        if orb.get("period_min"):
            orbit_rows.append(["Orbital Period", f"{orb['period_min']} min"])
        if orb.get("orbits_per_day"):
            orbit_rows.append(["Orbits per Day", f"{orb['orbits_per_day']}"])
        if orb.get("eclipse_fraction"):
            orbit_rows.append(["Eclipse Fraction", f"{orb['eclipse_fraction']}"])
        if orb.get("eclipse_duration_min"):
            orbit_rows.append(["Eclipse Duration", f"{orb['eclipse_duration_min']} min"])
        if orb.get("velocity_ms"):
            orbit_rows.append(["Orbital Velocity", f"{orb['velocity_ms']} m/s"])
        if orb.get("design_lifetime_years"):
            orbit_rows.append(["Design Lifetime", f"{orb['design_lifetime_years']} years"])
        _add_table(doc, ["Parameter", "Value"], orbit_rows)
    else:
        doc.add_paragraph("[Orbit parameters to be defined]")

    # ── Section 3: Mission Phases ──
    _add_section(doc, "3", "Mission Phases")
    phases = ops.get("phases", [])
    if phases:
        _add_table(doc,
                   ["Phase", "Type", "Duration (days)", "Description"],
                   [
                       [
                           p.get("name", ""),
                           p.get("phase_type", ""),
                           str(p.get("duration_days", "")),
                           p.get("description", ""),
                       ]
                       for p in phases
                   ])
        # Add entry/exit criteria if available
        for p in phases:
            entry = p.get("entry_criteria", "")
            exit_c = p.get("exit_criteria", "")
            if entry or exit_c:
                _add_section(doc, f"3.{phases.index(p)+1}", p.get("name", "Phase"),
                             f"**Entry criteria:** {entry or 'TBD'}\n\n**Exit criteria:** {exit_c or 'TBD'}")
    else:
        _add_table(doc,
                   ["Phase", "Duration", "Description"],
                   [
                       ["LEOP", "3 days", "Launch and Early Orbit Phase: initial contact, detumble, solar array deployment"],
                       ["Commissioning", "30 days", "Platform and payload checkout, calibration, orbit verification"],
                       ["Nominal Operations", "Mission lifetime", "Science/service operations at full capability"],
                       ["Extended Operations", "TBD", "Reduced operations if consumables/orbit allow"],
                       ["Disposal", "TBD", "Passivation and deorbit per debris mitigation requirements"],
                   ])

    # ── Section 4: Operational Modes ──
    _add_section(doc, "4", "Operational Modes")
    modes = ops.get("modes", [])
    if modes:
        _add_table(doc,
                   ["Mode", "Type", "Power (W)", "Payload Active", "Data Rate (Mbps)",
                    "Pointing (deg)", "Duty Cycle (%)"],
                   [
                       [
                           m.get("name", ""),
                           m.get("mode_type", ""),
                           f"{m.get('power_w', 0):.1f}" if m.get("power_w") else "",
                           "Yes" if m.get("payload_active") else "No",
                           f"{m.get('data_rate_mbps', 0):.1f}" if m.get("data_rate_mbps") else "",
                           f"{m.get('pointing_requirement_deg', '')}" if m.get("pointing_requirement_deg") else "",
                           f"{m.get('duty_cycle_percent', '')}" if m.get("duty_cycle_percent") else "",
                       ]
                       for m in modes
                   ])
        # Mode descriptions
        for m in modes:
            desc = m.get("description", "")
            if desc:
                _render_bullet(doc, f"- **{m.get('name', '')}:** {desc}")
    else:
        _add_table(doc,
                   ["Mode", "Description", "Key Subsystems"],
                   [
                       ["Safe Mode", "Minimum power, sun-pointing, waiting for ground contact", "EPS, AOCS (coarse), TTC (beacon)"],
                       ["Nominal / Science", "Full payload operation, nadir-pointing", "All subsystems active"],
                       ["Downlink", "High-rate data downlink to ground station", "TTC (high power), OBC, AOCS"],
                       ["Eclipse", "Battery-powered, payload may be inactive", "EPS (battery), Thermal (heaters)"],
                   ])

    # ── Section 5: Ground Station Network ──
    _add_section(doc, "5", "Ground Station Network")
    gs_list = ops.get("ground_stations", [])
    # Also check elements for ground segment
    gs_elements = [e for e in elems if e.get("segment") == "ground"
                   and (e.get("performance") or {}).get("latitude")]
    if gs_list:
        _add_table(doc,
                   ["Station", "Type", "Latitude", "Longitude", "Antenna (m)",
                    "Bands", "Contact (min/day)"],
                   [
                       [
                           gs.get("name", ""),
                           gs.get("type", ""),
                           f"{gs.get('latitude_deg', ''):.1f}" if gs.get("latitude_deg") else "",
                           f"{gs.get('longitude_deg', ''):.1f}" if gs.get("longitude_deg") else "",
                           f"{gs.get('antenna_diameter_m', '')}" if gs.get("antenna_diameter_m") else "",
                           ", ".join(gs.get("frequency_bands", [])),
                           f"{gs.get('contact_time_per_day_min', '')}" if gs.get("contact_time_per_day_min") else "",
                       ]
                       for gs in gs_list
                   ])
    elif gs_elements:
        _add_table(doc,
                   ["Station", "Latitude", "Longitude", "Bands"],
                   [
                       [
                           e.get("name", ""),
                           str((e.get("performance") or {}).get("latitude", "")),
                           str((e.get("performance") or {}).get("longitude", "")),
                           ", ".join((e.get("performance") or {}).get("bands", [])),
                       ]
                       for e in gs_elements
                   ])
    else:
        doc.add_paragraph("[Ground station network to be defined]")

    # Operations concept
    ops_concept = ops.get("operations_concept", "")
    autonomy = ops.get("autonomy_level", "")
    if ops_concept or autonomy:
        _add_section(doc, "5.1", "Operations Concept")
        if ops_concept:
            _render_rich_content(doc, ops_concept)
        if autonomy:
            doc.add_paragraph(f"Autonomy level: {autonomy}")

    # ── Section 6: Data Flow ──
    _add_section(doc, "6", "Data Flow")
    pipeline = ops.get("data_pipeline", [])
    if pipeline:
        _add_table(doc,
                   ["Step", "Location", "Description", "Latency", "Data Level"],
                   [
                       [
                           dp.get("name", ""),
                           dp.get("location", ""),
                           dp.get("description", ""),
                           dp.get("latency", ""),
                           dp.get("data_level", ""),
                       ]
                       for dp in pipeline
                   ])
    else:
        _add_section(doc, "6.1", "Data Pipeline",
                     "- Instrument acquisition (onboard)\n"
                     "- Onboard storage (mass memory)\n"
                     "- Downlink via TTC subsystem to ground station\n"
                     "- Ground processing (L0 to L1/L2 products)\n"
                     "- Archive and distribution to end users")

    # Data rates from modes
    data_modes = [m for m in modes if m.get("data_rate_mbps", 0) > 0]
    if data_modes:
        _add_section(doc, "6.2", "Data Generation Rates")
        _add_table(doc,
                   ["Mode", "Data Rate (Mbps)"],
                   [
                       [m.get("name", ""), f"{m['data_rate_mbps']:.1f}"]
                       for m in data_modes
                   ])

    # ── Section 7: Anomaly Response ──
    _add_section(doc, "7", "Anomaly Response")
    _add_table(doc,
               ["Contingency", "Trigger", "Response", "Recovery"],
               [
                   ["Loss of attitude", "Attitude error exceeds threshold",
                    "Autonomous transition to Safe Mode, sun-pointing", "Ground diagnosis, mode recovery command"],
                   ["Power anomaly", "Battery SoC below safe threshold",
                    "Load shedding, payload shutdown", "Ground analysis, gradual load restoration"],
                   ["Communication loss", "Missed scheduled ground contact",
                    "Autonomous safe mode after timeout", "Next ground pass recovery attempt"],
                   ["Thermal exceedance", "Temperature sensor out of range",
                    "Heater activation or payload duty cycle reduction", "Ground thermal analysis, ops adjustment"],
                   ["Payload anomaly", "Payload health check failure",
                    "Payload power-off, continue platform operations", "Diagnostic data downlink, reconfiguration"],
               ])

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
