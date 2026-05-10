"""SpaceCDF — ECSS DID (Document Item Description) Generator.

Generates document templates for all major ECSS deliverables.
Each document is populated from the live design state, requirements,
ConOps, and functional decomposition.

References:
  - ECSS-E-ST-10C Annex A — MRD
  - ECSS-E-ST-10-06C — Technical Specification
  - ECSS-E-ST-10-02C — VP / VCD (existing in compliance_generator)
  - ECSS-E-ST-10-24C — IRD
  - ECSS-M-ST-80C — RMP
  - NASA SEH Appendix J — SEMP
  - NASA SEH Appendix S — ConOps
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_table_row(*cols: str) -> str:
    """Format a pipe-separated table row."""
    return "| " + " | ".join(str(c) for c in cols) + " |"


def _fmt_table_header(*cols: str) -> str:
    """Format a table header with separator line."""
    header = _fmt_table_row(*cols)
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    return f"{header}\n{sep}"


def _safe(val: Any, fallback: str = "TBD") -> str:
    """Return stringified val or fallback."""
    if val is None or val == "":
        return fallback
    return str(val)


def _radiation_note(alt_km: float | None) -> str:
    """Rough radiation environment note from altitude."""
    if alt_km is None:
        return "TBD — orbit altitude not yet specified."
    a = float(alt_km)
    if a < 600:
        return f"LEO ({a:.0f} km) — benign radiation environment, minor trapped proton exposure at SAA."
    if a < 1500:
        return f"LEO ({a:.0f} km) — moderate trapped proton and electron flux; Van Allen inner belt fringe at higher altitudes."
    if a < 6000:
        return f"MEO ({a:.0f} km) — high radiation environment within Van Allen belts; significant total ionising dose."
    if a < 40000:
        return f"MEO/GEO ({a:.0f} km) — substantial trapped electron flux and solar particle exposure."
    return f"HEO/deep-space ({a:.0f} km) — high galactic cosmic-ray and solar-particle exposure."


def _thermal_range(alt_km: float | None) -> str:
    """Rough thermal range from orbit altitude (very approximate)."""
    if alt_km is None:
        return "TBD"
    a = float(alt_km)
    if a < 600:
        return "Hot case ~+80 °C (sun-facing), cold case ~ -100 °C (eclipse). Eclipse duration ~36 min for typical LEO."
    if a < 2000:
        return "Hot case ~+90 °C (sun-facing), cold case ~ -120 °C (eclipse). Eclipse durations vary with altitude."
    return "Hot case ~+100 °C (sun-facing), cold case ~ -180 °C (deep shadow). Eclipse conditions orbit-dependent."


# ---------------------------------------------------------------------------
# MRD — Mission Requirements Document
# ---------------------------------------------------------------------------

def generate_mrd(
    *,
    study_name: str,
    mission_need: dict[str, Any],
    requirements: list[dict[str, Any]],
    phase_id: str = "phase_a",
) -> dict[str, Any]:
    """Mission Requirements Document — ECSS-E-ST-10C Annex A."""
    mn = mission_need or {}
    objectives = mn.get("objectives", [])
    stakeholders = mn.get("stakeholders", [])
    operational_context = mn.get("operational_context", {})

    # ---- Group requirements by domain ----
    by_domain: dict[str, list[dict]] = {}
    for r in requirements:
        d = r.get("domain", "systems")
        by_domain.setdefault(d, []).append(r)

    # ---- Group requirements by level ----
    by_level: dict[str, list[dict]] = {}
    for r in requirements:
        lvl = r.get("level", "mission")
        by_level.setdefault(lvl, []).append(r)

    # ---- Section 2.2: objectives table ----
    obj_header = _fmt_table_header("No.", "ID", "Objective", "Priority", "Measurable Criterion", "Type")
    obj_rows = []
    for idx, o in enumerate(objectives, 1):
        obj_rows.append(_fmt_table_row(
            str(idx),
            _safe(o.get("id"), f"OBJ-{idx:03d}"),
            _safe(o.get("text")),
            _safe(o.get("priority", "primary")).upper(),
            _safe(o.get("measurable_criterion")),
            _safe(o.get("type", "performance")),
        ))
    obj_table = f"{obj_header}\n" + "\n".join(obj_rows) if obj_rows else "No objectives defined yet."

    # ---- Section 3: requirements grouped by domain AND level ----
    req_subsections: list[dict] = []
    sub_idx = 1
    for domain, reqs in sorted(by_domain.items()):
        # sub-group by level within each domain
        domain_by_level: dict[str, list[dict]] = {}
        for r in reqs:
            lvl = r.get("level", "mission")
            domain_by_level.setdefault(lvl, []).append(r)

        level_blocks: list[str] = []
        for level in ("mission", "system", "subsystem"):
            lvl_reqs = domain_by_level.get(level, [])
            if not lvl_reqs:
                continue
            hdr = _fmt_table_header("ID", "Requirement", "Threshold", "Op", "Unit", "Verification")
            rows = []
            for r in lvl_reqs:
                rows.append(_fmt_table_row(
                    _safe(r.get("id")),
                    _safe(r.get("text")),
                    _safe(r.get("threshold")),
                    _safe(r.get("operator"), ""),
                    _safe(r.get("unit"), ""),
                    _safe(r.get("verification_method")),
                ))
            level_blocks.append(f"**{level.title()}-level requirements:**\n\n{hdr}\n" + "\n".join(rows))

        content = "\n\n".join(level_blocks) if level_blocks else "No requirements in this domain."
        req_subsections.append({
            "number": f"3.{sub_idx}",
            "title": f"{domain.replace('_', ' ').title()} Requirements",
            "content": content,
        })
        sub_idx += 1

    # ---- Section 5: Operational Requirements ----
    if operational_context:
        if isinstance(operational_context, dict):
            op_lines = []
            for key, val in operational_context.items():
                op_lines.append(f"- **{key.replace('_', ' ').title()}**: {val}")
            op_content = "\n".join(op_lines)
        else:
            op_content = str(operational_context)
    else:
        op_content = "Operational context not yet defined. To be populated with ground-segment concept, data latency, autonomy level, and operations cadence."

    # ---- Section 7: Traceability matrix ----
    trace_rows: list[str] = []
    obj_id_map = {o.get("id", f"OBJ-{i+1:03d}"): o.get("text", "") for i, o in enumerate(objectives)}
    for r in requirements:
        obj_ref = r.get("objective_id") or r.get("parent_id") or ""
        if obj_ref:
            obj_text_short = obj_id_map.get(obj_ref, obj_ref)[:60]
            trace_rows.append(_fmt_table_row(
                _safe(r.get("id")),
                _safe(r.get("text", ""))[:60],
                obj_ref,
                obj_text_short,
            ))
    if trace_rows:
        trace_header = _fmt_table_header("Req ID", "Requirement (excerpt)", "Objective ID", "Objective (excerpt)")
        trace_content = f"{trace_header}\n" + "\n".join(trace_rows)
    else:
        trace_content = "No explicit requirement-to-objective traceability links defined yet. Populate the `objective_id` field on requirements to enable this matrix."

    # ---- Section 6: Environment placeholder ----
    orbit_type = mn.get("orbit_type") or mn.get("orbit", {}).get("type", "TBD")
    env_content = (
        f"Orbit type: {orbit_type}.\n\n"
        "Environmental requirements (radiation, thermal, debris, atomic oxygen) "
        "shall be derived from the orbit analysis and specified per ECSS-E-ST-10-04C. "
        "See Technical Specification for detailed environmental design loads."
    )

    return {
        "document": "Mission Requirements Document (MRD)",
        "standard": "ECSS-E-ST-10C Annex A",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {
                "number": "1", "title": "Introduction",
                "subsections": [
                    {"number": "1.1", "title": "Purpose", "content": f"This document defines the mission-level requirements for the {study_name} mission."},
                    {"number": "1.2", "title": "Scope", "content": "Covers all mission-level requirements derived from stakeholder needs and mission objectives."},
                    {"number": "1.3", "title": "Applicable Documents", "content": "ECSS-E-ST-10C Rev.1, ECSS-M-ST-10C Rev.1"},
                    {"number": "1.4", "title": "Reference Documents", "content": ""},
                ],
            },
            {
                "number": "2", "title": "Mission Overview",
                "subsections": [
                    {"number": "2.1", "title": "Problem Statement", "content": mn.get("problem_statement", "TBD")},
                    {"number": "2.2", "title": "Mission Objectives", "content": obj_table},
                    {"number": "2.3", "title": "Stakeholders",
                     "content": "\n".join(f"- {s.get('name', '')}: {s.get('role', '')}" for s in stakeholders) or "TBD"},
                    {"number": "2.4", "title": "Mission Success Criteria",
                     "content": "\n".join(f"- {o.get('measurable_criterion', 'TBD')}" for o in objectives if o.get("measurable_criterion")) or "TBD"},
                ],
            },
            {
                "number": "3", "title": "Mission Requirements",
                "subsections": req_subsections if req_subsections else [
                    {"number": "3.1", "title": "TBD", "content": "Requirements not yet defined."},
                ],
            },
            {
                "number": "4", "title": "Constraints",
                "subsections": [
                    {"number": "4.1", "title": "Programmatic Constraints", "content": "TBD — budget, schedule, launch date"},
                    {"number": "4.2", "title": "Technical Constraints", "content": "TBD — orbit, mass, interfaces"},
                    {"number": "4.3", "title": "Regulatory Constraints", "content": "Space debris mitigation per ECSS-U-AS-10C Rev.2, ITU frequency coordination"},
                ],
            },
            {
                "number": "5", "title": "Operational Requirements",
                "subsections": [
                    {"number": "5.1", "title": "Operational Context", "content": op_content},
                ],
            },
            {
                "number": "6", "title": "Environment Requirements",
                "subsections": [
                    {"number": "6.1", "title": "Environment Summary", "content": env_content},
                ],
            },
            {
                "number": "7", "title": "Traceability",
                "subsections": [
                    {"number": "7.1", "title": "Requirements-to-Objectives Traceability Matrix", "content": trace_content},
                ],
            },
        ],
        "total_requirements": len(requirements),
        "requirements_by_domain": {d: len(r) for d, r in by_domain.items()},
        "requirements_by_level": {l: len(r) for l, r in by_level.items()},
    }


# ---------------------------------------------------------------------------
# Technical Specification
# ---------------------------------------------------------------------------

def generate_technical_specification(
    *,
    study_name: str,
    requirements: list[dict[str, Any]],
    design_params: dict[str, Any],
    phase_id: str = "phase_a",
    mission_phases: list[dict[str, Any]] | None = None,
    interfaces: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Technical Specification — ECSS-E-ST-10-06C."""
    phases = mission_phases or []
    ifc_list = interfaces or []

    # ---- Section 2: Life Profile ----
    if phases:
        lp_header = _fmt_table_header("Phase", "Duration", "Description")
        lp_rows = []
        for p in phases:
            dur = p.get("duration_days") or p.get("duration", "TBD")
            lp_rows.append(_fmt_table_row(
                _safe(p.get("name")),
                f"{dur} days" if dur != "TBD" else "TBD",
                _safe(p.get("description"), ""),
            ))
        life_profile_content = f"{lp_header}\n" + "\n".join(lp_rows)
    else:
        life_profile_content = (
            "Mission life profile phases to be defined. Typically includes:\n"
            "- Launch and Early Operations (LEOP)\n"
            "- Commissioning\n"
            "- Nominal Operations\n"
            "- Extended Operations (if applicable)\n"
            "- Disposal"
        )

    # ---- Section 3.1: ALL performance requirements ----
    perf_reqs = [r for r in requirements if r.get("category") == "performance"]
    all_reqs_with_threshold = [r for r in requirements if r.get("threshold") is not None]
    display_reqs = perf_reqs if perf_reqs else all_reqs_with_threshold

    if display_reqs:
        pr_header = _fmt_table_header("ID", "Requirement", "Threshold", "Operator", "Unit")
        pr_rows = []
        for r in display_reqs:
            pr_rows.append(_fmt_table_row(
                _safe(r.get("id")),
                _safe(r.get("text")),
                _safe(r.get("threshold")),
                _safe(r.get("operator"), ""),
                _safe(r.get("unit"), ""),
            ))
        perf_content = f"{pr_header}\n" + "\n".join(pr_rows)
    else:
        perf_content = "See MRD for mission-level performance requirements."

    # ---- Section 3.3: Environment from orbit parameters ----
    alt = design_params.get("mission_analysis.orbit_altitude_km") or design_params.get("orbit_altitude_km")
    inc = design_params.get("mission_analysis.inclination_deg") or design_params.get("inclination_deg")

    env_lines = []
    if alt is not None:
        env_lines.append(f"**Orbit altitude**: {alt} km")
    if inc is not None:
        env_lines.append(f"**Inclination**: {inc}°")
    env_lines.append(f"\n**Radiation environment**: {_radiation_note(alt)}")
    env_lines.append(f"\n**Thermal environment**: {_thermal_range(alt)}")
    env_content = "\n".join(env_lines) if (alt or inc) else "Per ECSS-E-ST-10-04C. Orbit parameters not yet specified."

    # ---- Section 4: Budget tables ----
    def _budget_row(label: str, key: str, unit: str, margin_key: str | None = None) -> str:
        val = design_params.get(key)
        margin = design_params.get(margin_key) if margin_key else None
        return _fmt_table_row(
            label,
            _safe(val),
            unit,
            f"{margin}%" if margin is not None else "TBD",
        )

    budget_header = _fmt_table_header("Parameter", "Value", "Unit", "Margin")
    budget_rows = [
        _budget_row("Dry mass", "systems.dry_mass_kg", "kg", "systems.mass_margin_percent"),
        _budget_row("Wet mass", "systems.wet_mass_kg", "kg", None),
        _budget_row("Total power (orbit avg)", "systems.total_power_w", "W", "systems.power_margin_percent"),
        _budget_row("Peak power", "systems.peak_power_w", "W", None),
        _budget_row("Downlink data rate", "comms.downlink_data_rate_kbps", "kbps", None),
        _budget_row("Link margin", "comms.link_margin_db", "dB", None),
        _budget_row("Total delta-V", "propulsion.total_dv_ms", "m/s", "propulsion.dv_margin_percent"),
        _budget_row("Pointing accuracy", "aocs.pointing_accuracy_deg", "deg", None),
    ]
    budget_content = f"{budget_header}\n" + "\n".join(budget_rows)

    # Interface summary
    if ifc_list:
        ifc_summary = f"Total interfaces defined: {len(ifc_list)}. See IRD for details."
    else:
        ifc_summary = "Interface definition pending. See IRD."

    return {
        "document": "Technical Specification (TS)",
        "standard": "ECSS-E-ST-10-06C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {
                "number": "1", "title": "Introduction",
                "subsections": [
                    {"number": "1.1", "title": "Purpose", "content": f"Technical specification for {study_name}."},
                    {"number": "1.2", "title": "Scope", "content": "System-level technical requirements and design constraints."},
                ],
            },
            {
                "number": "2", "title": "System Description",
                "subsections": [
                    {"number": "2.1", "title": "System Architecture", "content": "See ConOps document for mission architecture."},
                    {"number": "2.2", "title": "Functional Description", "content": "See Functional Decomposition."},
                    {"number": "2.3", "title": "Life Profile", "content": life_profile_content},
                ],
            },
            {
                "number": "3", "title": "Technical Requirements",
                "subsections": [
                    {"number": "3.1", "title": "Performance Requirements", "content": perf_content},
                    {"number": "3.2", "title": "Interface Requirements", "content": "See IRD"},
                    {"number": "3.3", "title": "Environmental Requirements", "content": env_content},
                    {"number": "3.4", "title": "Design Constraints", "content": "TBD"},
                ],
            },
            {
                "number": "4", "title": "Design Budgets",
                "subsections": [
                    {"number": "4.1", "title": "System Budgets", "content": budget_content},
                    {"number": "4.2", "title": "Interface Summary", "content": ifc_summary},
                ],
            },
        ],
        "total_requirements": len(requirements),
    }


# ---------------------------------------------------------------------------
# IRD — Interface Requirements Document
# ---------------------------------------------------------------------------

def generate_ird(
    *,
    study_name: str,
    interfaces: list[dict[str, Any]],
    phase_id: str = "phase_b",
    elements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Interface Requirements Document — ECSS-E-ST-10-24C.

    Accepts actual interface data from the element tree. The ``interfaces``
    list should contain dicts with keys matching the ElementInterface model:
      - from_element_id / from_element / from
      - to_element_id / to_element / to
      - interface_type / types
      - name / description / diagram_label
      - properties (dict)
      - direction
      - status

    The ``elements`` list provides the design-element context so that
    element names and subsystem_domain values can be resolved from IDs.
    """
    elem_list = elements or []

    # Build element lookup by id — support both "id" key and nested structures
    elem_map: dict[str, dict] = {}
    for e in elem_list:
        eid = e.get("id", "")
        if eid:
            elem_map[eid] = e

    # ---- Section 2: Interface details ----
    ifc_subsections: list[dict] = []
    subsystem_pairs: dict[tuple[str, str], list[str]] = {}  # for N² matrix

    # ---- Interface statistics by type ----
    type_counts: dict[str, int] = {}

    for i, ifc in enumerate(interfaces[:40]):
        # Resolve element IDs — support multiple key naming conventions
        from_id = ifc.get("from_element_id") or ifc.get("from_element") or ifc.get("from", "")
        to_id = ifc.get("to_element_id") or ifc.get("to_element") or ifc.get("to", "")
        from_elem = elem_map.get(from_id, {})
        to_elem = elem_map.get(to_id, {})

        # Resolve human-readable names from the element tree
        from_name = (
            from_elem.get("name")
            or ifc.get("from_element_name")
            or (ifc.get("subsystems", ["?", "?"])[0] if ifc.get("subsystems") else None)
            or from_id
            or "?"
        )
        to_name = (
            to_elem.get("name")
            or ifc.get("to_element_name")
            or (ifc.get("subsystems", ["?", "?"])[1] if ifc.get("subsystems") else None)
            or to_id
            or "?"
        )
        from_domain = from_elem.get("subsystem_domain") or ifc.get("from_subsystem_domain") or from_name
        to_domain = to_elem.get("subsystem_domain") or ifc.get("to_subsystem_domain") or to_name

        ifc_type = ifc.get("interface_type") or ", ".join(ifc.get("types", []))
        props = ifc.get("properties") or ifc.get("properties_json") or {}
        props_str = ", ".join(f"{k}: {v}" for k, v in props.items()) if props else ""
        desc = ifc.get("description") or ifc.get("name") or ifc.get("diagram_label") or ""
        direction = ifc.get("direction", "bidirectional")
        status = ifc.get("status", "defined")

        # Count by type
        for t in (ifc_type.split(", ") if ifc_type else ["unspecified"]):
            type_counts[t.strip()] = type_counts.get(t.strip(), 0) + 1

        content_parts = [f"**Interface type**: {ifc_type or 'TBD'}"]
        content_parts.append(f"**Direction**: {direction}")
        content_parts.append(f"**Status**: {status}")
        if desc:
            content_parts.append(f"**Description**: {desc}")
        if props_str:
            content_parts.append(f"**Properties**: {props_str}")
        # Include element context if resolved
        if from_elem.get("element_type"):
            content_parts.append(f"**From element type**: {from_elem['element_type']} ({from_domain})")
        if to_elem.get("element_type"):
            content_parts.append(f"**To element type**: {to_elem['element_type']} ({to_domain})")

        ifc_subsections.append({
            "number": f"2.{i + 1}",
            "title": f"{from_name} \u2194 {to_name}",
            "content": "\n".join(content_parts),
        })

        # Accumulate for N² matrix
        pair = tuple(sorted([str(from_domain), str(to_domain)]))
        subsystem_pairs.setdefault(pair, []).append(ifc_type or "unspecified")

    if not ifc_subsections:
        ifc_subsections = [{"number": "2.1", "title": "TBD", "content": "Interface matrix not yet populated."}]

    # ---- N² matrix summary ----
    if subsystem_pairs:
        n2_header = _fmt_table_header("Subsystem A", "Subsystem B", "Interface Types", "Count")
        n2_rows = []
        for (a, b), types in sorted(subsystem_pairs.items()):
            unique_types = sorted(set(t for t in types if t))
            n2_rows.append(_fmt_table_row(a, b, ", ".join(unique_types) or "TBD", str(len(types))))
        n2_content = f"{n2_header}\n" + "\n".join(n2_rows)
    else:
        n2_content = "N² matrix will be populated once interfaces are defined."

    return {
        "document": "Interface Requirements Document (IRD)",
        "standard": "ECSS-E-ST-10-24C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {
                "number": "1", "title": "Introduction",
                "subsections": [
                    {"number": "1.1", "title": "Purpose", "content": f"Defines all internal and external interfaces for {study_name}."},
                    {"number": "1.2", "title": "Interface Categories", "content": "Mechanical, Electrical, Thermal, Data, RF, Optical"},
                ],
            },
            {
                "number": "2", "title": "Internal Interfaces (Subsystem-to-Subsystem)",
                "subsections": ifc_subsections,
            },
            {
                "number": "3", "title": "External Interfaces",
                "subsections": [
                    {"number": "3.1", "title": "Launch Vehicle Interface", "content": "Per launch adapter ICD. Mechanical, electrical separation connector."},
                    {"number": "3.2", "title": "Ground Segment Interface", "content": "RF link (TM/TC), data products interface."},
                ],
            },
            {
                "number": "4", "title": "N² Interface Matrix Summary",
                "subsections": [
                    {"number": "4.1", "title": "Subsystem Pair Summary", "content": n2_content},
                ],
            },
            {
                "number": "5", "title": "Interface Conflicts & Resolution",
                "subsections": [
                    {"number": "5.1", "title": "Identified Conflicts",
                     "content": "\n".join(f"- {ifc.get('conflict_title', '')}" for ifc in interfaces if ifc.get('has_conflict')) or "No conflicts identified."},
                ],
            },
        ],
        "total_interfaces": len(interfaces),
        "unique_subsystem_pairs": len(subsystem_pairs),
        "interfaces_by_type": type_counts,
        "total_elements": len(elem_list),
    }


# ---------------------------------------------------------------------------
# SEMP — Systems Engineering Management Plan (stub — replaced by semp_generator)
# ---------------------------------------------------------------------------

def generate_semp(
    *,
    study_name: str,
    phase_id: str = "phase_a",
) -> dict[str, Any]:
    """Systems Engineering Management Plan — NASA SEH Appendix J / ECSS-M-ST-10C."""
    return {
        "document": "Systems Engineering Management Plan (SEMP)",
        "standard": "NASA SEH Appendix J / ECSS-M-ST-10C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Defines the SE approach for {study_name}."},
                {"number": "1.2", "title": "Scope", "content": "Covers all 17 SE processes per NPR 7123.1."},
            ]},
            {"number": "2", "title": "SE Process Application", "subsections": [
                {"number": "2.1", "title": "System Design (Processes 1-4)", "content": "Stakeholder expectations, requirements definition, logical decomposition, design solution."},
                {"number": "2.2", "title": "Product Realisation (Processes 5-9)", "content": "Implementation, integration, verification, validation, transition."},
                {"number": "2.3", "title": "Technical Management (Processes 10-17)", "content": "Planning, requirements management, interface management, risk, CM, data, assessment, decision analysis."},
            ]},
            {"number": "3", "title": "Organisation & Roles", "subsections": [
                {"number": "3.1", "title": "Concurrent Design Team", "content": "Systems Engineer, Power, AOCS, Thermal, Comms, Propulsion, Structures, Payload, Cost, Mission Analyst."},
            ]},
            {"number": "4", "title": "Reviews & Milestones", "subsections": [
                {"number": "4.1", "title": "Review Schedule", "content": "MCR → SRR → PDR → CDR → TRR → FRR per ECSS-M-ST-10C / NASA life cycle."},
                {"number": "4.2", "title": "Exit Criteria", "content": "Per SpaceCDF gate review framework."},
            ]},
            {"number": "5", "title": "Risk Management", "subsections": [
                {"number": "5.1", "title": "Risk Process", "content": "Per ECSS-M-ST-80C / NPR 8000.4."},
            ]},
            {"number": "6", "title": "Technical Performance Measures", "subsections": [
                {"number": "6.1", "title": "TPMs", "content": "Mass margin, power margin, pointing accuracy, link margin, cost margin."},
            ]},
        ],
    }


# ---------------------------------------------------------------------------
# RMP — Risk Management Plan
# ---------------------------------------------------------------------------

def generate_rmp(
    *,
    study_name: str,
    risks: list[dict[str, Any]] | None = None,
    phase_id: str = "phase_a",
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Risk Management Plan — ECSS-M-ST-80C."""
    risk_items = list(risks or [])
    params = parameters or {}

    def _pval(key: str) -> float | None:
        """Extract numeric value from parameter (handles both raw numbers and {value:X} dicts)."""
        v = params.get(key)
        if v is None:
            return None
        if isinstance(v, dict):
            v = v.get("value")
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    # ---- Auto-detect risks from budget margins ----
    auto_risks: list[dict[str, Any]] = []

    mass_margin = _pval("systems.mass_margin_percent")
    if mass_margin is not None and mass_margin < 10:
        auto_risks.append({
            "title": "Insufficient Mass Margin",
            "id": "RSK-AUTO-MASS",
            "likelihood": 3,
            "consequence": 4,
            "description": f"Current mass margin is {mass_margin}% which is below the 10% threshold recommended for this phase. Risk of exceeding launch vehicle capacity or requiring de-scope.",
            "mitigation": "Review subsystem mass allocations, identify mass-saving options, consider lighter materials or component alternatives.",
            "source": "auto-detected",
        })

    power_margin = _pval("systems.power_margin_percent")
    if power_margin is not None and power_margin < 10:
        auto_risks.append({
            "title": "Insufficient Power Margin",
            "id": "RSK-AUTO-PWR",
            "likelihood": 3,
            "consequence": 3,
            "description": f"Current power margin is {power_margin}% which is below 10%. Risk of power-negative conditions.",
            "mitigation": "Review duty cycles, consider larger solar array, reduce payload power, or add battery capacity.",
            "source": "auto-detected",
        })

    link_margin = _pval("comms.link_margin_db")
    if link_margin is not None and link_margin < 3:
        auto_risks.append({
            "title": "Low Link Margin",
            "id": "RSK-AUTO-LINK",
            "likelihood": 2,
            "consequence": 3,
            "description": f"Link margin is {link_margin} dB, below the 3 dB design target. Risk of communication dropouts or reduced data throughput.",
            "mitigation": "Increase antenna gain, reduce data rate, increase transmitter power, or optimise ground station selection.",
            "source": "auto-detected",
        })

    # Check for low-TRL equipment
    for key, val in params.items():
        if key.endswith(".trl") or key.endswith("_trl"):
            try:
                trl_val = int(val)
                if trl_val < 6:
                    component = key.rsplit(".", 1)[0] if "." in key else key.replace("_trl", "")
                    auto_risks.append({
                        "title": f"Low TRL Component: {component}",
                        "id": f"RSK-AUTO-TRL-{component.upper().replace('.', '-')}",
                        "likelihood": 3,
                        "consequence": 3,
                        "description": f"Component '{component}' has TRL {trl_val} (< 6). Technology maturation risk may impact schedule and cost.",
                        "mitigation": "Develop technology maturation plan, identify alternative COTS components, plan breadboard/engineering model testing.",
                        "source": "auto-detected",
                    })
            except (ValueError, TypeError):
                pass

    pointing_accuracy = params.get("aocs.pointing_accuracy_deg")
    pointing_required = params.get("aocs.pointing_required_deg")
    if pointing_accuracy is not None and pointing_required is not None:
        try:
            margin = float(pointing_accuracy) - float(pointing_required)
            if margin < 0.01 and float(pointing_required) > 0:
                auto_risks.append({
                    "title": "Tight Pointing Budget",
                    "id": "RSK-AUTO-POINT",
                    "likelihood": 2,
                    "consequence": 3,
                    "description": f"Pointing accuracy ({pointing_accuracy}°) is very close to requirement ({pointing_required}°). Minimal margin for disturbance rejection.",
                    "mitigation": "Review pointing error budget contributors, consider higher-performance actuators or improved sensor suite.",
                    "source": "auto-detected",
                })
        except (ValueError, TypeError):
            pass

    # Merge auto-detected with user-supplied (user-supplied take precedence)
    existing_titles = {r.get("title", "").lower() for r in risk_items}
    for ar in auto_risks:
        if ar["title"].lower() not in existing_titles:
            risk_items.append(ar)

    # ---- Risk counts by severity ----
    critical_count = sum(1 for r in risk_items if r.get("likelihood", 0) * r.get("consequence", 0) >= 15)
    major_count = sum(1 for r in risk_items if 8 <= r.get("likelihood", 0) * r.get("consequence", 0) < 15)

    # ---- Risk register subsections ----
    risk_subsections: list[dict] = []
    for i, r in enumerate(risk_items):
        lik = r.get("likelihood", "TBD")
        con = r.get("consequence", "TBD")
        try:
            score = int(lik) * int(con)
            score_str = f" (Score: {score})"
        except (ValueError, TypeError):
            score_str = ""

        content_parts = [
            f"**ID**: {r.get('id', f'RSK-{i+1:03d}')}",
            f"**Likelihood**: {lik}/5, **Consequence**: {con}/5{score_str}",
            f"**Description**: {r.get('description', 'TBD')}",
        ]
        if r.get("mitigation"):
            content_parts.append(f"**Mitigation**: {r['mitigation']}")
        if r.get("source") == "auto-detected":
            content_parts.append("*[Auto-detected from design parameters]*")

        risk_subsections.append({
            "number": f"3.{i + 1}",
            "title": r.get("title", f"Risk {i + 1}"),
            "content": "\n".join(content_parts),
        })

    if not risk_subsections:
        risk_subsections = [{"number": "3.1", "title": "TBD", "content": "Risk register to be populated during Phase A."}]

    return {
        "document": "Risk Management Plan (RMP)",
        "standard": "ECSS-M-ST-80C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Risk management approach for {study_name}."},
            ]},
            {"number": "2", "title": "Risk Process", "subsections": [
                {"number": "2.1", "title": "Identification", "content": "Risk identification via design analysis, trade studies, heritage review, and automated margin monitoring from SpaceCDF design parameters."},
                {"number": "2.2", "title": "Assessment", "content": f"5x5 likelihood x consequence matrix per ECSS-M-ST-80C.\n\nMatrix dimensions: 5 likelihood levels (1=Remote to 5=Very High) x 5 consequence levels (1=Negligible to 5=Catastrophic).\n\nCurrent register: {len(risk_items)} risks identified ({critical_count} critical, {major_count} major)."},
                {"number": "2.3", "title": "Mitigation", "content": "Accept / Mitigate / Transfer / Avoid."},
                {"number": "2.4", "title": "Monitoring", "content": "Risk review at each design review gate. Auto-detected risks are refreshed from live design parameters."},
            ]},
            {"number": "3", "title": "Risk Register", "subsections": risk_subsections},
        ],
        "total_risks": len(risk_items),
        "auto_detected_risks": len(auto_risks),
        "critical_risks": critical_count,
        "major_risks": major_count,
    }


# ---------------------------------------------------------------------------
# ConOps — Concept of Operations
# ---------------------------------------------------------------------------

def generate_conops_document(
    *,
    study_name: str,
    mission_need: dict[str, Any],
    conops: dict[str, Any] | None = None,
    phase_id: str = "phase_a",
    ground_stations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Concept of Operations Document — NASA SEH Appendix S."""
    mn = mission_need or {}
    ops = conops or {}
    phases = ops.get("phases", [])
    modes = ops.get("modes", [])
    gs_list = ground_stations or []

    # ---- Section 2.2: Ground Segment with stations ----
    if gs_list:
        gs_header = _fmt_table_header("Station", "Latitude", "Longitude", "Bands")
        gs_rows = []
        for gs in gs_list:
            bands = gs.get("bands", [])
            bands_str = ", ".join(bands) if isinstance(bands, list) else _safe(bands)
            gs_rows.append(_fmt_table_row(
                _safe(gs.get("name")),
                _safe(gs.get("latitude")),
                _safe(gs.get("longitude")),
                bands_str,
            ))
        gs_content = f"Ground station network:\n\n{gs_header}\n" + "\n".join(gs_rows)
    else:
        gs_content = "Ground station(s) + MCC + data processing. Station network to be defined."

    # ---- Section 4: Operational modes as proper table ----
    if modes:
        mode_subsections: list[dict] = []
        for i, m in enumerate(modes):
            mode_header = _fmt_table_header("Attribute", "Value")
            mode_rows = [
                _fmt_table_row("Mode Name", _safe(m.get("name"))),
                _fmt_table_row("Description", _safe(m.get("description"))),
                _fmt_table_row("Pointing", _safe(m.get("pointing"))),
                _fmt_table_row("Active Subsystems", ", ".join(m.get("subsystems_active", [])) or "TBD"),
                _fmt_table_row("Data Flow", _safe(m.get("dataflow"))),
                _fmt_table_row("Power Mode", _safe(m.get("power_mode"))),
                _fmt_table_row("Data Handling", _safe(m.get("data_handling"))),
            ]
            mode_content = f"{mode_header}\n" + "\n".join(mode_rows)
            mode_subsections.append({
                "number": f"4.{i + 1}",
                "title": m.get("name", f"Mode {i + 1}"),
                "content": mode_content,
            })
    else:
        mode_subsections = [{"number": "4.1", "title": "TBD", "content": "Operational modes to be defined."}]

    return {
        "document": "Concept of Operations (ConOps)",
        "standard": "NASA SEH Appendix S",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Describes how {study_name} will be operated to meet mission objectives."},
                {"number": "1.2", "title": "Mission Overview", "content": mn.get("problem_statement", "TBD")},
            ]},
            {"number": "2", "title": "Mission Architecture", "subsections": [
                {"number": "2.1", "title": "Space Segment", "content": "Spacecraft + payload."},
                {"number": "2.2", "title": "Ground Segment", "content": gs_content},
                {"number": "2.3", "title": "User Segment", "content": "Data products and services to end users."},
            ]},
            {"number": "3", "title": "Mission Phases", "subsections": [
                {"number": f"3.{i+1}", "title": p.get("name", f"Phase {i+1}"),
                 "content": f"Duration: {p.get('duration_days', 'TBD')} days. {p.get('description', '')}"}
                for i, p in enumerate(phases)
            ] if phases else [
                {"number": "3.1", "title": "LEOP", "content": "TBD"},
                {"number": "3.2", "title": "Commissioning", "content": "TBD"},
                {"number": "3.3", "title": "Nominal Operations", "content": "TBD"},
                {"number": "3.4", "title": "Disposal", "content": "TBD"},
            ]},
            {"number": "4", "title": "Operational Modes", "subsections": mode_subsections},
            {"number": "5", "title": "Data Flow", "subsections": [
                {"number": "5.1", "title": "Data Pipeline", "content": "Instrument → Onboard Storage → Downlink → Ground Processing → Archive → User."},
            ]},
        ],
        "total_phases": len(phases),
        "total_modes": len(modes),
        "ground_stations": len(gs_list),
    }


# ---------------------------------------------------------------------------
# Test Plan
# ---------------------------------------------------------------------------

def generate_test_plan(
    *,
    study_name: str,
    requirements: list[dict[str, Any]],
    phase_id: str = "phase_c",
    equipment: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Test Plan — ECSS-E-ST-10-03C."""
    test_reqs = [r for r in requirements if r.get("verification_method") == "test"]
    equip_list = equipment or []

    # ---- Section 1.2: Model philosophy from mean TRL ----
    trl_values = []
    for eq in equip_list:
        trl = eq.get("trl")
        if trl is not None:
            try:
                trl_values.append(int(trl))
            except (ValueError, TypeError):
                pass

    if trl_values:
        mean_trl = sum(trl_values) / len(trl_values)
        if mean_trl > 8:
            model_approach = "Proto-Flight Model (PFM)"
            model_text = (
                f"Mean equipment TRL is {mean_trl:.1f} (based on {len(trl_values)} items). "
                f"High heritage maturity supports a **Proto-Flight Model (PFM)** approach. "
                "The flight unit will undergo proto-flight qualification testing at qualification levels "
                "but with acceptance durations per ECSS-E-ST-10-03C."
            )
        else:
            model_approach = "Qualification Model + Flight Model (QM+FM)"
            model_text = (
                f"Mean equipment TRL is {mean_trl:.1f} (based on {len(trl_values)} items). "
                f"Mixed maturity requires a **Qualification Model + Flight Model (QM+FM)** approach. "
                "A dedicated QM will undergo full qualification testing; the FM will be tested at acceptance levels. "
                "Components with TRL < 6 require additional breadboard/engineering model testing."
            )
        # List low-TRL items
        low_trl = [eq for eq in equip_list if eq.get("trl") is not None and int(eq.get("trl", 9)) < 6]
        if low_trl:
            model_text += "\n\n**Low-TRL items requiring technology maturation testing:**\n"
            for eq in low_trl:
                model_text += f"- {eq.get('name', 'Unknown')} (TRL {eq.get('trl')}, {eq.get('subsystem_domain', 'TBD')})\n"
    else:
        model_approach = "TBD"
        model_text = "Proto-flight approach for CubeSats; model philosophy for larger missions. Equipment TRL data not yet available to determine approach."

    # ---- Section 4: Test requirements table ----
    if test_reqs:
        tr_header = _fmt_table_header("ID", "Requirement", "Test Type", "Pass Criteria")
        tr_rows = []
        for r in test_reqs[:30]:
            # Infer test type
            text_lower = (r.get("text", "") + r.get("domain", "")).lower()
            if any(kw in text_lower for kw in ("thermal", "vibration", "shock", "radiation", "emc", "vacuum")):
                test_type = "Environmental"
            else:
                test_type = "Functional"

            threshold = r.get("threshold")
            operator = r.get("operator", "")
            unit = r.get("unit", "")
            if threshold is not None:
                pass_criteria = f"{operator} {threshold} {unit}".strip()
            else:
                pass_criteria = "Per requirement text"

            tr_rows.append(_fmt_table_row(
                _safe(r.get("id")),
                _safe(r.get("text", ""))[:80],
                test_type,
                pass_criteria,
            ))
        test_matrix_content = f"{tr_header}\n" + "\n".join(tr_rows)
    else:
        test_matrix_content = "No requirements with verification_method='test' identified yet. Test requirements to be derived from VP."

    return {
        "document": "Test Plan",
        "standard": "ECSS-E-ST-10-03C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Test plan for {study_name} verification."},
                {"number": "1.2", "title": "Model Philosophy", "content": model_text},
            ]},
            {"number": "2", "title": "Environmental Testing", "subsections": [
                {"number": "2.1", "title": "Vibration", "content": "Sine, random, shock per launch vehicle ICD."},
                {"number": "2.2", "title": "Thermal Vacuum", "content": "Qualification range +/-10 deg C beyond operating. 4 cycles minimum."},
                {"number": "2.3", "title": "EMC", "content": "Per ECSS-E-ST-20-07C. Radiated emissions, susceptibility, conducted."},
            ]},
            {"number": "3", "title": "Functional Testing", "subsections": [
                {"number": "3.1", "title": "Subsystem Tests", "content": "Individual subsystem functional verification before integration."},
                {"number": "3.2", "title": "System-Level Tests", "content": "End-to-end data chain, mode transitions, FDIR."},
            ]},
            {"number": "4", "title": "Test Requirements Matrix", "subsections": [
                {"number": "4.1", "title": "Test Requirements", "content": test_matrix_content},
            ]},
        ],
        "test_requirement_count": len(test_reqs),
        "model_approach": model_approach,
        "equipment_count": len(equip_list),
    }


# ---------------------------------------------------------------------------
# Map of all available DID types
# ---------------------------------------------------------------------------

DID_TYPES = {
    "mrd": ("Mission Requirements Document", generate_mrd),
    "ts": ("Technical Specification", generate_technical_specification),
    "ird": ("Interface Requirements Document", generate_ird),
    "semp": ("SE Management Plan", generate_semp),
    "rmp": ("Risk Management Plan", generate_rmp),
    "conops": ("Concept of Operations", generate_conops_document),
    "test_plan": ("Test Plan", generate_test_plan),
}


def list_available_dids() -> list[dict[str, str]]:
    """List all available DID types."""
    return [{"id": k, "name": v[0]} for k, v in DID_TYPES.items()]
