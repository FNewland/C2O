"""SpaceCDF — Design-Review DOCX Generator (uOttawa SpaceCDF course style).

Produces a rich, DID-structured Word document for SRR / PDR / CDR design
reviews.  Page furniture matches the SpaceCDF Facilitator's Book:

    • uOttawa garnet cover banner + slab title
    • running header with crimson rule
    • bilingual footer ("Page X of / de Y", uOttawa SEDTI)
    • Word-native ToC, acronyms, applicable/reference docs
    • numbered DID body sections
    • embedded figures (orbit, ground-track, link waterfall, power profile,
      thermal nodes, architecture diagram, compliance heatmap, risk matrix,
      cost P-curve and WBS bar)
    • per-domain chapter pulling agent.rationale + agent.assumptions +
      agent.extras + agent.parameters into a professional narrative

The renderer is data-defensive: missing sections fall back to "[Pending]"
or are skipped, so the document still produces with partial agent data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import theme, figures
from .theme import _shade, _set_cell_text  # internal helpers re-exported for cells


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_docx(context: dict[str, Any], review_type: str, output_path: Path) -> None:
    """Generate the design review .docx.

    Args:
        context: As returned by ``generator.build_context``.
        review_type: ``srr`` | ``pdr`` | ``cdr``.
        output_path: Destination for the .docx file.
    """
    theme.reset_counters()
    review_type = (review_type or "srr").lower()
    review_title = {
        "srr": "System Requirements Review",
        "pdr": "Preliminary Design Review",
        "cdr": "Critical Design Review",
    }.get(review_type, review_type.upper())

    document_code = context.get("document_code", f"SCDF-{review_type.upper()}-001")
    mission = context.get("mission_name", "Mission")
    study = context.get("study_name", mission)
    issue = context.get("issue", "1.0")
    date = context.get("date", "")

    doc = theme.new_document()

    # ---- Cover ---------------------------------------------------------
    theme.add_cover_page(
        doc,
        title=f"{review_type.upper()} — {mission}",
        subtitle=review_title,
        document_code=document_code,
        study_name=study,
        issue=issue,
        date=date,
        classification=context.get("classification", "Internal"),
        cohort="SpaceCDF",
        publisher=context.get("publisher", ""),
    )

    # ---- Page furniture (applies to all sections) ----------------------
    theme.add_page_furniture(
        doc,
        running_title=f"SpaceCDF — {review_type.upper()} — {mission}",
        document_code=document_code,
        footer_left=f"{document_code} · {study}",
        footer_right="uOttawa SEDTI",
    )

    # ---- Document information & change record -------------------------
    theme.add_doc_info_table(
        doc,
        document_code=document_code,
        title=f"{review_title} — {mission}",
        study_name=study,
        issue=issue,
        date=date,
        prepared_by="SpaceCDF AI Concurrent Design Facility",
        classification=context.get("classification", "Internal"),
        applies_to=mission,
    )
    theme.add_change_record(doc, [
        {"issue": issue, "date": date, "by": "SpaceCDF",
         "summary": f"Initial {review_type.upper()} issue generated from converged design loop."}
    ])
    theme.add_aig_acknowledgement(doc)
    theme.add_acronyms_table(doc, context.get("acronyms") or {})
    theme.add_reference_list(doc, context.get("applicable_documents") or [],
                             heading="Applicable Documents")
    theme.add_reference_list(doc, context.get("reference_documents") or [],
                             heading="Reference Documents")
    theme.add_toc(doc)

    # ---- 1. Scope ------------------------------------------------------
    _section_scope(doc, context, review_title, review_type)

    # ---- 2. Mission overview ------------------------------------------
    _section_mission_overview(doc, context)

    # ---- 3. Concept of operations & orbit -----------------------------
    _section_orbit_conops(doc, context)

    # ---- 4. System architecture ---------------------------------------
    _section_architecture(doc, context)

    # ---- 5. Per-subsystem chapters ------------------------------------
    _section_payload(doc, context)
    _section_power(doc, context)
    _section_thermal(doc, context)
    _section_aocs(doc, context)
    _section_propulsion(doc, context)
    _section_comms(doc, context)
    _section_data(doc, context)
    _section_structure(doc, context)

    # ---- 6. Budgets ----------------------------------------------------
    _section_budgets(doc, context)

    # ---- 7. Equipment list --------------------------------------------
    _section_equipment(doc, context)

    # ---- 8. Compliance & verification ---------------------------------
    _section_compliance(doc, context)
    _section_trl(doc, context)

    # ---- 9. Reliability & FMECA ---------------------------------------
    _section_reliability(doc, context)

    # ---- 10. Risk register --------------------------------------------
    _section_risk(doc, context)

    # ---- 11. Debris compliance ----------------------------------------
    _section_debris(doc, context)

    # ---- 12. Cost & schedule ------------------------------------------
    _section_cost(doc, context)

    # ---- 13. Design convergence ---------------------------------------
    _section_convergence(doc, context)

    # ---- 14. Conclusions & recommendations ----------------------------
    _section_conclusions(doc, context, review_type)

    doc.save(str(output_path))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agent(context: dict[str, Any], domain: str) -> dict[str, Any]:
    return (context.get("agents") or {}).get(domain) or {}


def _para(doc, text: str) -> None:
    if text:
        doc.add_paragraph(text)


def _bullets(doc, items: list[str]) -> None:
    for item in items or []:
        if item:
            doc.add_paragraph(item, style="List Bullet")


def _rationale_block(doc, agent_dict: dict[str, Any], default_text: str = "") -> None:
    """Render rationale + assumptions for an agent."""
    rationale = agent_dict.get("rationale") or default_text
    if rationale:
        doc.add_heading("Rationale", level=3)
        doc.add_paragraph(rationale)
    assumptions = agent_dict.get("assumptions") or []
    if assumptions:
        doc.add_heading("Assumptions", level=3)
        _bullets(doc, assumptions)
    warnings = agent_dict.get("warnings") or []
    if warnings:
        doc.add_heading("Warnings & open issues", level=3)
        _bullets(doc, warnings)


def _params_table(doc, agent_dict: dict[str, Any], *, exclude_prefixes: tuple[str, ...] = ()) -> None:
    params = agent_dict.get("parameters") or {}
    rows = []
    for pid, p in sorted(params.items()):
        if any(pid.startswith(pre) for pre in exclude_prefixes):
            continue
        val = p.get("value")
        if isinstance(val, float):
            val_s = f"{val:.3g}"
        else:
            val_s = str(val)
        rows.append([p.get("name") or pid, val_s, p.get("unit", ""), f"{p.get('margin_percent', 0):.0f}%"])
    if not rows:
        return
    theme.styled_table(
        doc,
        headers=["Parameter", "Value", "Unit", "Margin"],
        rows=rows,
        col_widths_cm=[7.5, 3.5, 2.5, 3.0],
    )


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _section_scope(doc, context, review_title: str, review_type: str) -> None:
    theme.bookmarked_heading(doc, "1. Scope", level=1, bookmark="sec_scope")
    doc.add_heading("1.1 Purpose", level=2)
    doc.add_paragraph(
        f"This document is the {review_title} for the {context.get('mission_name','mission')}.  "
        f"It captures the converged engineering baseline produced by the SpaceCDF "
        f"AI Concurrent Design Facility and provides the evidence required for the "
        f"{review_type.upper()} review gate per ECSS-M-ST-10C Rev.1."
    )
    doc.add_heading("1.2 Applicability", level=2)
    doc.add_paragraph(
        "The contents are applicable to all engineering disciplines, project "
        "management, product assurance and operations.  Subsystem-level data "
        "items inherit applicability from the parent applicable documents listed "
        "above."
    )
    doc.add_heading("1.3 Conventions", level=2)
    doc.add_paragraph(
        "All units are SI unless otherwise stated.  Margins are quoted relative "
        "to the nominal value (i.e. with-margin = nominal × (1 + margin%)).  "
        "Status colours follow the SpaceCDF / ECSS convention: green = "
        "compliant, amber = marginal, red = non-compliant or exceeded."
    )


def _section_mission_overview(doc, context) -> None:
    theme.bookmarked_heading(doc, "2. Mission Overview", level=1, bookmark="sec_mission")
    doc.add_paragraph(
        f"Mission '{context.get('mission_name')}' is a "
        f"{context.get('mission_type','')} mission carried out by "
        f"{context.get('num_spacecraft',1)} {context.get('spacecraft_class','')}-class "
        f"spacecraft over a design life of "
        f"{context.get('design_lifetime_years','—')} years.  "
        f"Top-level mission targets are "
        f"{context.get('target_mass_kg','—')} kg launch mass and "
        f"{context.get('target_cost_meur','—')} MEUR total programme cost."
    )

    # Top-level summary table
    rows = [
        ["Mission name", context.get("mission_name", "")],
        ["Mission type", context.get("mission_type", "")],
        ["Spacecraft class", context.get("spacecraft_class", "")],
        ["Number of spacecraft", context.get("num_spacecraft", 1)],
        ["Design lifetime (yr)", context.get("design_lifetime_years", "—")],
        ["Reliability target", context.get("reliability_target", "—")],
        ["Cost target (MEUR)", context.get("target_cost_meur", "—")],
        ["Mass target (kg)", context.get("target_mass_kg", "—")],
        ["Ground stations", ", ".join(context.get("ground_stations", []) or []) or "—"],
    ]
    theme.styled_table(doc, headers=["Mission attribute", "Value"], rows=rows,
                       col_widths_cm=[6.0, 11.0])
    theme.add_table_caption(doc, "Top-level mission descriptor.")

    payloads = context.get("payloads") or []
    if payloads:
        doc.add_heading("2.1 Payload complement", level=2)
        rows = [[pl["name"], pl["type"], f"{pl['mass_kg']:.2f}",
                 f"{pl['power_w']:.1f}", f"{pl['data_rate_mbps']:.1f}",
                 f"{pl.get('pointing_accuracy_deg', 0):.3f}",
                 f"{pl.get('duty_cycle_percent', 0):.0f}%"]
                for pl in payloads]
        theme.styled_table(
            doc,
            headers=["Name", "Type", "Mass (kg)", "Power (W)", "Rate (Mbps)",
                     "Pointing (°)", "Duty"],
            rows=rows,
            col_widths_cm=[3.2, 3.0, 2.0, 2.0, 2.4, 2.4, 1.8],
        )
        theme.add_table_caption(doc, "Payload complement.")


def _section_orbit_conops(doc, context) -> None:
    theme.bookmarked_heading(doc, "3. Concept of Operations & Orbit", level=1, bookmark="sec_conops")
    orbit = context.get("orbit") or {}
    orbit_agent = _agent(context, "orbit")

    rows = [
        ["Orbit type", str(orbit.get("orbit_type", "")).upper().replace("_", " ")],
        ["Altitude (km)", f"{orbit.get('altitude_km', 0):.0f}"],
        ["Inclination (deg)", f"{orbit.get('inclination_deg', 0):.2f}"],
        ["Period (min)", f"{orbit.get('period_min', 0):.1f}"],
        ["Orbits per day", f"{orbit.get('orbits_per_day', 0):.2f}"],
        ["Velocity (m/s)", f"{orbit.get('velocity_ms', 0):.1f}"],
        ["Eclipse fraction", f"{orbit.get('eclipse_fraction', 0):.3f}"],
        ["Footprint radius (km)", f"{orbit.get('footprint_radius_km', 0):.0f}"],
        ["Contact time / day (s)", f"{orbit.get('contact_time_per_day_s', 0):.0f}"],
        ["Mission duration (yr)", f"{orbit.get('mission_duration_years', 0):.1f}"],
    ]
    theme.styled_table(doc, headers=["Parameter", "Value"], rows=rows,
                       col_widths_cm=[6.0, 11.0])
    theme.add_table_caption(doc, "Orbital parameters.")

    # Figures
    try:
        theme.add_figure(
            doc,
            figures.orbit_geometry(
                altitude_km=orbit.get("altitude_km", 500),
                eclipse_fraction=orbit.get("eclipse_fraction", 0.35),
                inclination_deg=orbit.get("inclination_deg", 97.4),
                orbit_type=str(orbit.get("orbit_type", "LEO")).upper(),
            ),
            caption=f"{str(orbit.get('orbit_type','LEO')).upper()} orbit geometry with shaded eclipse arc.",
        )
    except Exception:
        pass
    try:
        theme.add_figure(
            doc,
            figures.ground_track(
                altitude_km=orbit.get("altitude_km", 500),
                inclination_deg=orbit.get("inclination_deg", 97.4),
                orbits=3,
            ),
            caption="Indicative ground track over three consecutive orbits.",
        )
    except Exception:
        pass

    # Rationale + assumptions + ΔV breakdown
    _rationale_block(doc, orbit_agent)

    dv_breakdown = (orbit_agent.get("extras") or {}).get("orbit.delta_v_breakdown") or []
    if dv_breakdown:
        doc.add_heading("3.1 ΔV breakdown", level=2)
        rows = [[item["name"], f"{item['value_ms']:.1f}", item.get("rationale", "")]
                for item in dv_breakdown if item.get("value_ms")]
        theme.styled_table(
            doc, headers=["Component", "ΔV (m/s)", "Rationale"],
            rows=rows, col_widths_cm=[4.0, 2.5, 10.5],
        )
        theme.add_table_caption(doc, "ΔV budget breakdown.")


def _section_architecture(doc, context) -> None:
    theme.bookmarked_heading(doc, "4. System Architecture", level=1, bookmark="sec_arch")
    doc.add_paragraph(
        "The spacecraft system architecture follows the canonical CubeSat-class "
        "topology with a payload routing data through the OBDH to the TT&C "
        "subsystem, while the EPS distributes regulated power to all platform "
        "subsystems.  AOCS drives propulsion (when fitted) and the thermal "
        "subsystem couples conductively to the structure."
    )
    try:
        theme.add_figure(doc, figures.subsystem_block_diagram(),
                         caption="Spacecraft system architecture — block diagram.")
    except Exception:
        pass


def _section_payload(doc, context) -> None:
    theme.bookmarked_heading(doc, "5. Payload", level=1, bookmark="sec_payload")
    payloads = context.get("payloads") or []
    if not payloads:
        doc.add_paragraph("No payload defined.")
        return
    for i, pl in enumerate(payloads, 1):
        doc.add_heading(f"5.{i} {pl['name']}", level=2)
        doc.add_paragraph(pl.get("description") or "[Description pending.]")
        rows = [
            ["Type", pl.get("type", "")],
            ["Mass (kg)", f"{pl['mass_kg']:.2f}"],
            ["Power, mean (W)", f"{pl['power_w']:.1f}"],
            ["Power, peak (W)", f"{pl.get('power_peak_w', pl['power_w']):.1f}"],
            ["Data rate (Mbps)", f"{pl['data_rate_mbps']:.2f}"],
            ["Data volume / day (GB)", f"{pl.get('data_volume_per_day_gb', 0):.2f}"],
            ["Pointing accuracy (°)", f"{pl.get('pointing_accuracy_deg', 0):.3f}"],
            ["Duty cycle (%)", f"{pl.get('duty_cycle_percent', 0):.0f}"],
        ]
        theme.styled_table(doc, headers=["Attribute", "Value"], rows=rows,
                           col_widths_cm=[6.0, 11.0])


def _section_power(doc, context) -> None:
    theme.bookmarked_heading(doc, "6. Electrical Power Subsystem", level=1, bookmark="sec_eps")
    agent = _agent(context, "power")
    _rationale_block(doc, agent)
    _params_table(doc, agent)

    # Figures
    extras = agent.get("extras") or {}
    profile = extras.get("power.profile")
    if profile:
        try:
            theme.add_figure(
                doc,
                figures.power_timeline(
                    period_min=profile.get("period_min", 95),
                    eclipse_fraction=profile.get("eclipse_fraction", 0.35),
                    sunlit_load_w=profile.get("sunlit_load_w", 25),
                    eclipse_load_w=profile.get("eclipse_load_w", 18),
                    sa_eol_w=profile.get("sa_eol_w"),
                ),
                caption="Orbit-averaged power profile (sunlit / eclipse, SA EoL line).",
            )
        except Exception:
            pass

    modes = extras.get("power.modes") or []
    if modes:
        doc.add_heading("6.1 Operational power modes", level=2)
        rows = [[m.get("name"),
                 f"{m.get('duty_cycle', 0)*100:.0f}%",
                 f"{m.get('power_w', 0):.1f}",
                 f"{m.get('platform_w', 0):.1f}",
                 f"{m.get('payload_w', 0):.1f}",
                 f"{m.get('heater_w', 0):.1f}"] for m in modes]
        theme.styled_table(
            doc,
            headers=["Mode", "Duty", "Total (W)", "Platform (W)", "Payload (W)", "Heater (W)"],
            rows=rows,
            col_widths_cm=[4.5, 1.8, 2.4, 2.7, 2.7, 2.4],
        )

    battery = extras.get("power.battery")
    if battery:
        doc.add_heading("6.2 Battery", level=2)
        rows = [
            ["Capacity (Wh)", f"{battery.get('capacity_wh', 0):.1f}"],
            ["Depth of discharge (%)", f"{battery.get('dod_percent', 0):.1f}"],
            ["Mass (kg)", f"{battery.get('mass_kg', 0):.2f}"],
            ["Chemistry", battery.get("chemistry", "")],
        ]
        theme.styled_table(doc, headers=["Parameter", "Value"], rows=rows,
                           col_widths_cm=[6.0, 11.0])


def _section_thermal(doc, context) -> None:
    theme.bookmarked_heading(doc, "7. Thermal Control Subsystem", level=1, bookmark="sec_tcs")
    agent = _agent(context, "thermal")
    _rationale_block(doc, agent)
    _params_table(doc, agent)

    extras = agent.get("extras") or {}
    nodes = extras.get("thermal.nodes") or []
    if nodes:
        try:
            theme.add_figure(doc, figures.thermal_node_bars(nodes),
                             caption="Hot and cold case temperatures across the principal thermal nodes.")
        except Exception:
            pass
        rows = [[n.get("name"),
                 f"{n.get('cold_c', 0):.1f}", f"{n.get('hot_c', 0):.1f}",
                 f"{n.get('limit_cold_c', '—')}", f"{n.get('limit_hot_c', '—')}"]
                for n in nodes]
        theme.styled_table(
            doc,
            headers=["Node", "Cold (°C)", "Hot (°C)", "Min limit", "Max limit"],
            rows=rows, col_widths_cm=[5.0, 2.5, 2.5, 2.5, 2.5],
        )

    surfaces = extras.get("thermal.surfaces") or []
    if surfaces:
        doc.add_heading("7.1 Surface treatments", level=2)
        rows = [[s.get("surface"),
                 f"{s.get('alpha', 0):.2f}",
                 f"{s.get('epsilon', 0):.2f}",
                 f"{s.get('area_m2', 0):.3f}"]
                for s in surfaces]
        theme.styled_table(doc, headers=["Surface", "α", "ε", "Area (m²)"],
                           rows=rows, col_widths_cm=[6.0, 2.5, 2.5, 4.0])


def _section_aocs(doc, context) -> None:
    theme.bookmarked_heading(doc, "8. AOCS", level=1, bookmark="sec_aocs")
    agent = _agent(context, "aocs")
    _rationale_block(doc, agent)
    _params_table(doc, agent)

    extras = agent.get("extras") or {}
    db = extras.get("aocs.disturbance_breakdown") or []
    if db:
        doc.add_heading("8.1 Disturbance torque budget", level=2)
        rows = [[item.get("source"), f"{item.get('torque_nm', 0):.2e}"] for item in db]
        theme.styled_table(doc, headers=["Source", "Torque (Nm)"], rows=rows,
                           col_widths_cm=[8.5, 8.5])

    pb = extras.get("aocs.pointing_budget") or []
    if pb:
        doc.add_heading("8.2 Pointing error budget", level=2)
        rows = [[item.get("contributor"), f"{item.get('value_arcsec', 0):.1f}"] for item in pb]
        theme.styled_table(doc, headers=["Contributor", "1σ (arcsec)"], rows=rows,
                           col_widths_cm=[10.0, 7.0])


def _section_propulsion(doc, context) -> None:
    theme.bookmarked_heading(doc, "9. Propulsion", level=1, bookmark="sec_prop")
    agent = _agent(context, "propulsion")
    _rationale_block(doc, agent)
    _params_table(doc, agent)

    ts = (agent.get("extras") or {}).get("propulsion.tsiolkovsky")
    if ts and ts.get("delta_v_ms"):
        doc.add_heading("9.1 Tsiolkovsky budget", level=2)
        rows = [
            ["ΔV (m/s)", f"{ts.get('delta_v_ms', 0):.1f}"],
            ["Isp (s)", f"{ts.get('isp_s', 0):.0f}"],
            ["Mass ratio m₀/m_f", f"{ts.get('mass_ratio', 1):.3f}"],
            ["Initial mass m₀ (kg)", f"{ts.get('m0_kg', 0):.2f}"],
            ["Final mass m_f (kg)", f"{ts.get('mf_kg', 0):.2f}"],
            ["Propellant (kg)", f"{ts.get('propellant_kg', 0):.2f}"],
        ]
        theme.styled_table(doc, headers=["Parameter", "Value"], rows=rows,
                           col_widths_cm=[6.0, 11.0])


def _section_comms(doc, context) -> None:
    theme.bookmarked_heading(doc, "10. Telemetry, Tracking & Command", level=1, bookmark="sec_ttc")
    agent = _agent(context, "link")
    _rationale_block(doc, agent)
    _params_table(doc, agent)

    extras = agent.get("extras") or {}
    waterfall = extras.get("link.waterfall") or []
    if waterfall:
        try:
            theme.add_figure(
                doc,
                figures.link_budget_waterfall(
                    [(w["label"], w["delta_db"]) for w in waterfall],
                    title="Payload downlink — link budget waterfall",
                ),
                caption="Payload downlink link budget waterfall (positive = gain, negative = loss).",
            )
        except Exception:
            pass
        rows = [[w["label"], f"{w['delta_db']:+.2f}"] for w in waterfall]
        theme.styled_table(doc, headers=["Term", "Δ (dB)"], rows=rows,
                           col_widths_cm=[10.0, 7.0])

    summary = extras.get("link.summary")
    if summary:
        doc.add_heading("10.1 Link summary", level=2)
        rows = [
            ["Band", summary.get("band", "")],
            ["Frequency (GHz)", f"{summary.get('frequency_ghz', 0):.3f}"],
            ["S/C Tx power (W)", f"{summary.get('tx_power_w', 0):.1f}"],
            ["S/C antenna gain (dBi)", f"{summary.get('tx_antenna_gain_dbi', 0):.1f}"],
            ["GS antenna Ø (m)", f"{summary.get('gs_antenna_diameter_m', 0):.2f}"],
            ["GS antenna gain (dBi)", f"{summary.get('gs_antenna_gain_dbi', 0):.1f}"],
            ["Slant range (km)", f"{summary.get('slant_range_km', 0):.0f}"],
            ["User data rate (bps)", f"{summary.get('data_rate_bps', 0):,.0f}"],
            ["Data downlinked / day (GB)", f"{summary.get('data_per_day_gb', 0):.2f}"],
            ["Downlink margin (dB)", f"{summary.get('downlink_margin_db', 0):.1f}"],
            ["TT&C margin (dB)", f"{summary.get('ttc_margin_db', 0):.1f}"],
            ["Uplink margin (dB)", f"{summary.get('uplink_margin_db', 0):.1f}"],
        ]
        theme.styled_table(doc, headers=["Parameter", "Value"], rows=rows,
                           col_widths_cm=[6.0, 11.0])


def _section_data(doc, context) -> None:
    theme.bookmarked_heading(doc, "11. Data Handling", level=1, bookmark="sec_data")
    agent = _agent(context, "data")
    _rationale_block(doc, agent)
    _params_table(doc, agent)


def _section_structure(doc, context) -> None:
    theme.bookmarked_heading(doc, "12. Structure & Mechanisms", level=1, bookmark="sec_struct")
    agent = _agent(context, "structure")
    _rationale_block(doc, agent, default_text=(
        "Structure mass is taken from the heritage class-fraction database with "
        "Phase-A margin of 20%.  Detailed FEM, modal analysis, and mechanism "
        "qualification are deferred to PDR/CDR."
    ))
    _params_table(doc, agent)


def _section_budgets(doc, context) -> None:
    theme.bookmarked_heading(doc, "13. System Budgets", level=1, bookmark="sec_budgets")
    budgets = context.get("budgets") or {}

    if budgets:
        try:
            theme.add_figure(
                doc,
                figures.budget_stacked_bar(budgets,
                                           title="Subsystem share of each budget"),
                caption="Normalised share of each system budget by subsystem.",
            )
        except Exception:
            pass

    for btype, label, unit_hint in (
        ("mass", "13.1 Mass budget", "kg"),
        ("power", "13.2 Power budget", "W"),
        ("data", "13.3 Data budget", "GB"),
        ("cost", "13.4 Cost budget", "kEUR"),
        ("delta_v", "13.5 ΔV budget", "m/s"),
    ):
        b = budgets.get(btype)
        if not b:
            continue
        doc.add_heading(label, level=2)
        unit = b.get("unit", unit_hint)
        try:
            theme.add_figure(
                doc,
                figures.budget_donut(b.get("lines", []), title=btype.title(),
                                     unit=unit,
                                     total_nominal=b.get("total_nominal"),
                                     total_with_margin=b.get("total_with_margin"),
                                     allocation=b.get("allocation")),
                caption=f"{btype.title()} budget contributions and total ({unit}).",
            )
        except Exception:
            pass
        _budget_table(doc, b, unit)


def _budget_table(doc, budget: dict, unit: str) -> None:
    lines = budget.get("lines") or []
    if not lines:
        doc.add_paragraph(f"No {unit} budget lines available.")
        return
    rows = []
    for l in lines:
        nom = float(l.get("nominal_value", 0) or 0)
        margin = float(l.get("margin_percent", 0) or 0)
        with_m = nom * (1 + margin / 100)
        rows.append([
            l.get("subsystem", ""),
            l.get("equipment", ""),
            f"{nom:.3g}",
            f"{margin:.0f}",
            f"{with_m:.3g}",
        ])
    # Total row
    rows.append([
        "TOTAL", "",
        f"{float(budget.get('total_nominal', 0) or 0):.3g}",
        f"{float(budget.get('margin_percent', 0) or 0):.0f}",
        f"{float(budget.get('total_with_margin', 0) or 0):.3g}",
    ])
    theme.styled_table(
        doc,
        headers=["Subsystem", "Equipment", f"Nominal ({unit})", "Margin (%)", f"With margin ({unit})"],
        rows=rows,
        col_widths_cm=[3.5, 5.0, 3.0, 2.0, 3.5],
    )
    status = str(budget.get("status", "")).lower().replace(" ", "_")
    # Strip "BUDGETSTATUS." prefix when status comes through as Enum repr
    if "." in status:
        status = status.split(".", 1)[1]
    allocation = budget.get("allocation")
    mp = budget.get("margin_percent", 0) or 0
    if allocation is not None:
        p = doc.add_paragraph()
        # Show kEUR allocations as MEUR for readability
        disp_unit = unit
        disp_alloc = allocation
        if unit.lower() == "keur" and allocation >= 1000:
            disp_alloc = allocation / 1000
            disp_unit = "MEUR"
        run = p.add_run(
            f"Allocation: {disp_alloc:.2f} {disp_unit} — margin {mp:.1f}% — status {status.upper() or '—'}"
        )
        run.bold = True


def _section_equipment(doc, context) -> None:
    theme.bookmarked_heading(doc, "14. Equipment List", level=1, bookmark="sec_eq")
    equipment = context.get("equipment") or []
    if not equipment:
        doc.add_paragraph("No KB-selected equipment recorded in the design state.")
        return
    rows = [[eq.get("domain", ""), eq.get("parameter_id", ""),
             eq.get("equipment_name", ""), eq.get("heritage", ""),
             eq.get("trl", "—")] for eq in equipment]
    theme.styled_table(
        doc,
        headers=["Domain", "Parameter", "Equipment", "Heritage", "TRL"],
        rows=rows,
        col_widths_cm=[2.5, 3.5, 5.0, 4.0, 2.0],
    )


def _section_compliance(doc, context) -> None:
    theme.bookmarked_heading(doc, "15. Compliance & Verification", level=1, bookmark="sec_comp")
    compliance = context.get("compliance") or {}
    verifs = compliance.get("verifications") or []
    if verifs:
        try:
            theme.add_figure(doc, figures.compliance_heatmap(verifs),
                             caption="Compliance status across all requirements.")
        except Exception:
            pass
        rows = []
        for v in verifs:
            av = v.get("achieved_value")
            mp = v.get("margin_percent")
            rows.append([
                v.get("requirement_id", ""),
                v.get("requirement_text", "")[:90],
                f"{av:.2f}" if isinstance(av, (int, float)) else "—",
                f"{mp:.1f}" if isinstance(mp, (int, float)) else "—",
                str(v.get("status", "")).lower(),
            ])
        theme.styled_table(
            doc,
            headers=["Req ID", "Description", "Achieved", "Margin %", "Status"],
            rows=rows, col_widths_cm=[2.0, 8.0, 2.5, 2.0, 2.5],
            status_col_index=4,
        )
        p = doc.add_paragraph()
        p.add_run(
            f"Total {compliance.get('total_requirements', 0)} requirements: "
            f"{compliance.get('compliant', 0)} compliant · "
            f"{compliance.get('marginal', 0)} marginal · "
            f"{compliance.get('non_compliant', 0)} non-compliant "
            f"({compliance.get('compliance_percent', 0):.1f}%)."
        ).bold = True
    else:
        doc.add_paragraph("No compliance matrix available — verification deferred to PDR.")


def _section_trl(doc, context) -> None:
    theme.bookmarked_heading(doc, "16. Technology Readiness", level=1, bookmark="sec_trl")
    trl_list = context.get("trl_assessments") or []
    if not trl_list:
        doc.add_paragraph("TRL assessment pending — equipment selection in progress.")
        return
    rows = []
    for trl in trl_list:
        innov = trl.get("innovation_component")
        rows.append([
            trl.get("subsystem", ""),
            f"{trl.get('baseline_component','')} ({trl.get('baseline_trl','')})",
            f"{innov} ({trl.get('innovation_trl','')})" if innov else "—",
            trl.get("recommendation", ""),
        ])
    theme.styled_table(
        doc,
        headers=["Subsystem", "Baseline (TRL)", "Innovation (TRL)", "Recommendation"],
        rows=rows, col_widths_cm=[3.0, 4.5, 4.5, 5.0],
    )


def _section_reliability(doc, context) -> None:
    theme.bookmarked_heading(doc, "17. Reliability & FMECA", level=1, bookmark="sec_rel")
    agent = _agent(context, "reliability")
    _rationale_block(doc, agent)

    rates = (agent.get("extras") or {}).get("reliability.failure_rates") or []
    if rates:
        doc.add_heading("17.1 Per-subsystem failure rates", level=2)
        rows = [[r.get("subsystem"), f"{r.get('lambda_per_hour', 0):.2e}",
                 f"{r.get('reliability', 0):.4f}", r.get("redundancy", "")]
                for r in rates]
        theme.styled_table(doc,
                           headers=["Subsystem", "λ (1/h)", "R(mission)", "Redundancy"],
                           rows=rows, col_widths_cm=[3.5, 3.5, 3.5, 6.5])

    fmeca = (agent.get("extras") or {}).get("reliability.fmeca") or []
    if fmeca:
        doc.add_heading("17.2 FMECA (top items)", level=2)
        rows = [[f.get("item"), f.get("failure_mode"), f.get("effect"),
                 f.get("severity"), f.get("occurrence"), f.get("detection"),
                 f.get("rpn"), f.get("mitigation", "")[:60]]
                for f in sorted(fmeca, key=lambda x: -x.get("rpn", 0))[:10]]
        theme.styled_table(
            doc,
            headers=["Item", "Failure mode", "Effect", "S", "O", "D", "RPN", "Mitigation"],
            rows=rows,
            col_widths_cm=[1.8, 3.2, 3.0, 1.0, 1.0, 1.0, 1.0, 5.0],
        )


def _section_risk(doc, context) -> None:
    theme.bookmarked_heading(doc, "18. Risk Register", level=1, bookmark="sec_risk")
    risks = context.get("risk_register") or []
    try:
        theme.add_figure(doc, figures.risk_matrix(risks),
                         caption="5×5 risk index map (ECSS-M-ST-80C).")
    except Exception:
        pass
    if not risks:
        doc.add_paragraph("Risk register pending — no risks identified at this stage.")
        return
    rows = [[r.get("id"), r.get("name", "")[:60],
             r.get("likelihood"), r.get("severity"), r.get("score"),
             r.get("mitigation", "")[:80], r.get("owner", "")]
            for r in risks]
    theme.styled_table(
        doc,
        headers=["ID", "Risk", "L", "S", "Score", "Mitigation", "Owner"],
        rows=rows,
        col_widths_cm=[1.8, 4.5, 1.0, 1.0, 1.2, 5.0, 2.5],
    )


def _section_debris(doc, context) -> None:
    theme.bookmarked_heading(doc, "19. Space Debris Compliance", level=1, bookmark="sec_debris")
    agent = _agent(context, "debris")
    _rationale_block(doc, agent)
    extras = agent.get("extras") or {}
    comp = extras.get("debris.compliance")
    if comp:
        rows = [
            ["Orbital lifetime (yr)", f"{comp.get('lifetime_years', 0):.1f}"],
            ["25-yr rule (IADC)", "Compliant" if comp.get("compliant_25yr") else "NON-compliant"],
            ["5-yr rule (FCC)", "Compliant" if comp.get("compliant_5yr") else "NON-compliant"],
            ["Casualty risk Ec", f"{comp.get('casualty_risk', 0):.2e}"],
            ["Casualty risk compliance", "Compliant" if comp.get("casualty_compliant") else "NON-compliant"],
            ["Passivation score", f"{comp.get('passivation_score', 0):.2f}"],
            ["Compliance score (0–100)", f"{comp.get('compliance_score', 0):.0f}"],
            ["Deorbit method", comp.get("method", "")],
            ["CA ΔV per year (m/s)", f"{comp.get('collision_avoidance_dv_per_year_ms', 0):.1f}"],
        ]
        theme.styled_table(doc, headers=["Parameter", "Value"], rows=rows,
                           col_widths_cm=[6.0, 11.0])


def _section_cost(doc, context) -> None:
    theme.bookmarked_heading(doc, "20. Cost & Schedule", level=1, bookmark="sec_cost")
    agent = _agent(context, "cost")
    _rationale_block(doc, agent)
    cost = context.get("cost") or {}
    if cost:
        try:
            theme.add_figure(doc, figures.cost_pcurve(cost),
                             caption="Cost estimate at P50/P70/P80/P90 confidence levels.")
        except Exception:
            pass
        if cost.get("wbs"):
            try:
                theme.add_figure(doc, figures.cost_wbs_bar(cost["wbs"]),
                                 caption="Cost breakdown by WBS element (DDT&E + recurring).")
            except Exception:
                pass
            rows = [[w.get("wbs_id"), w.get("name"),
                     f"{w.get('ddte_keur', 0)/1000:.2f}",
                     f"{w.get('recurring_keur', 0)/1000:.2f}",
                     f"{w.get('total_keur', 0)/1000:.2f}"]
                    for w in cost["wbs"]]
            theme.styled_table(
                doc,
                headers=["WBS", "Element", "DDT&E (MEUR)", "Recurring (MEUR)", "Total (MEUR)"],
                rows=rows, col_widths_cm=[1.8, 5.0, 3.4, 3.4, 3.4],
            )


def _section_convergence(doc, context) -> None:
    theme.bookmarked_heading(doc, "21. Design Loop Convergence", level=1, bookmark="sec_conv")
    conv = context.get("convergence") or {}
    rows = [
        ["Converged", "Yes" if conv.get("converged") else "No"],
        ["Iterations", str(conv.get("iterations", "—"))],
        ["Wall-clock time (s)", f"{conv.get('time_s', 0):.2f}"],
    ]
    theme.styled_table(doc, headers=["Metric", "Value"], rows=rows,
                       col_widths_cm=[6.0, 11.0])


def _section_conclusions(doc, context, review_type: str) -> None:
    theme.bookmarked_heading(doc, "22. Conclusions & Recommendations", level=1,
                             bookmark="sec_concl")
    doc.add_paragraph(
        f"The {review_type.upper()} baseline is now established.  Key engineering "
        f"observations follow."
    )
    warnings = context.get("warnings") or []
    recs = context.get("recommendations") or []
    if warnings:
        doc.add_heading("22.1 Open warnings", level=2)
        _bullets(doc, warnings)
    if recs:
        doc.add_heading("22.2 Recommendations", level=2)
        _bullets(doc, recs)
    if not warnings and not recs:
        doc.add_paragraph("No open warnings or recommendations recorded.")

    doc.add_heading("22.3 Next steps", level=2)
    next_steps = {
        "srr": [
            "Lock the Mission Requirements Document and Concept of Operations.",
            "Prepare the system architecture trade space for the PDR.",
            "Mature low-TRL components and update the technology development plan.",
        ],
        "pdr": [
            "Freeze the preliminary design and equipment selection.",
            "Initiate engineering model build and breadboard activities.",
            "Finalise the Verification Plan and Test Programme.",
        ],
        "cdr": [
            "Initiate qualification model build and AIT activities.",
            "Finalise the flight model assembly procedures.",
            "Confirm launch service interface and ground segment readiness.",
        ],
    }
    _bullets(doc, next_steps.get(review_type, []))
