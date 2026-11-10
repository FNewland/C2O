"""SpaceCDF Word document family: conops. Concept of Operations (ConOps).

* ``generate_conops_from_view(view, lang)`` (W7.02, Nov 2026): the ConOps built from the study:
  the Modes tab (modes, transitions with guards, power by mode, sunlit-only flags), the edited
  mission phases, the ConOps summary and success criteria, the contacts and the data flow (an
  open item until the data budget exists: ``routers/conops.data_flow_section``), a typical day,
  the flight rules and contingencies of the CDR model and the end-of-life operations. ``view`` is
  ``routers.conops.conops_view``; EN or FR headings.
* ``generate_conops_docx`` — the legacy generator of ``/exports/docx/conops`` (auto ConOps model),
  moved verbatim from services/docx_generator.py in W0.1.

See design/docs/dev/W0_SEAMS.md for ownership (agent D).
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


# ═══════════════════════════════════════════════════════════════════════════
# W7.02: the ConOps built from the study
# ═══════════════════════════════════════════════════════════════════════════

_T = {
    "en": {
        "title": "Concept of Operations", "std": "NASA SEH Appendix S / ECSS-E-ST-70C",
        "s1": "Mission overview", "s1_1": "ConOps summary", "s1_2": "Success criteria",
        "s2": "Orbit", "s3": "Mission phases", "s4": "Spacecraft modes", "s4_1": "Mode transitions",
        "s4_2": "Power by mode", "s5": "Ground segment and contacts", "s6": "Data flow and downlink allocation",
        "s7": "A typical day", "s8": "Flight rules", "s9": "Contingencies", "s10": "End-of-life operations",
        "param": "Parameter", "value": "Value", "phase": "Phase", "type": "Type", "dur": "Duration (days)",
        "entry": "Entry criteria", "exit": "Exit criteria", "modes": "Modes", "mode": "Mode", "kind": "Kind",
        "pointing": "Pointing", "sunlit": "Sunlit only", "share": "Share of orbit (%)", "initial": "Initial",
        "from": "From", "to": "To", "trigger": "Trigger", "guard": "Guard",
        "cbe": "CBE (W)", "total": "With margins (W)", "dod": "Depth of discharge (%)", "status": "Energy check",
        "yes": "yes", "no": "no", "none": "None recorded.", "station": "Ground station",
        "rule": "Rule", "text": "Text", "ref": "Reference", "name": "Name", "action": "Action", "level": "Level",
        "min_day": "Minutes per day", "per_day": "Orbits per day", "period": "Orbital period (min)",
        "eclipse": "Longest eclipse (min)", "open_item": "Open item",
        "df_open": "The data volumes and the per-pass downlink allocation come from the data budget "
                   "({wp}, owner {owner}), which is not in the study yet. This section lists them once it is.",
        "contacts_open": "Contact statistics per station come from the contact analysis (W4.05), not in the study yet.",
        "dl_rate": "Downlink rate (bit/s)", "ul_rate": "Uplink rate (bit/s)",
        "safe_entry": "Safe mode entry", "safe_exit": "Safe mode exit", "method": "Disposal method",
        "req": "Requirement", "phases_auto": "These phases are the tool's defaults: edit them in the ConOps phases editor.",
        "td_intro": "Share of each operational mode in a day of nominal operations (from the Modes tab).",
        "op_orbit": "Operational orbit",
    },
    "fr": {
        "title": "Concept d’opérations", "std": "NASA SEH annexe S / ECSS-E-ST-70C",
        "s1": "Présentation de la mission", "s1_1": "Résumé du concept d’opérations", "s1_2": "Critères de succès",
        "s2": "Orbite", "s3": "Phases de la mission", "s4": "Modes du satellite", "s4_1": "Transitions de mode",
        "s4_2": "Puissance par mode", "s5": "Segment sol et contacts", "s6": "Flux de données et allocation de la liaison descendante",
        "s7": "Une journée type", "s8": "Règles de vol", "s9": "Contingences", "s10": "Opérations de fin de vie",
        "param": "Paramètre", "value": "Valeur", "phase": "Phase", "type": "Type", "dur": "Durée (jours)",
        "entry": "Critères d’entrée", "exit": "Critères de sortie", "modes": "Modes", "mode": "Mode", "kind": "Nature",
        "pointing": "Pointage", "sunlit": "Au soleil seulement", "share": "Part de l’orbite (%)", "initial": "Initial",
        "from": "De", "to": "Vers", "trigger": "Déclencheur", "guard": "Garde",
        "cbe": "MEC (W)", "total": "Avec marges (W)", "dod": "Profondeur de décharge (%)", "status": "Bilan d’énergie",
        "yes": "oui", "no": "non", "none": "Aucun élément enregistré.", "station": "Station sol",
        "rule": "Règle", "text": "Texte", "ref": "Référence", "name": "Nom", "action": "Action", "level": "Niveau",
        "min_day": "Minutes par jour", "per_day": "Orbites par jour", "period": "Période orbitale (min)",
        "eclipse": "Éclipse la plus longue (min)", "open_item": "Point ouvert",
        "df_open": "Les volumes de données et l’allocation de la liaison descendante par passage viennent du bilan "
                   "de données ({wp}, responsable {owner}), qui n’est pas encore dans l’étude. Cette section les "
                   "donnera dès qu’il y sera.",
        "contacts_open": "Les statistiques de contact par station viennent de l’analyse des contacts (W4.05), "
                         "pas encore dans l’étude.",
        "dl_rate": "Débit descendant (bit/s)", "ul_rate": "Débit montant (bit/s)",
        "safe_entry": "Entrée en mode survie", "safe_exit": "Sortie du mode survie", "method": "Méthode de retrait",
        "req": "Exigence", "phases_auto": "Ces phases sont celles proposées par l’outil : modifiez-les dans l’éditeur des phases.",
        "td_intro": "Part de chaque mode opérationnel dans une journée d’opérations nominales (onglet Modes).",
        "op_orbit": "Orbite opérationnelle",
    },
}


def _fmt(v: Any, nd: int = 2) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.{nd}f}".rstrip("0").rstrip(".") if nd else f"{v:.0f}"
    return str(v)


def generate_conops_from_view(view: dict[str, Any], lang: str = "en") -> bytes:
    """The ConOps document from ``routers.conops.conops_view`` (see the module docstring)."""
    t = _T.get(lang, _T["en"])
    doc = Document()
    _setup_styles(doc)
    _setup_margins(doc)
    name = view.get("study_name") or ""
    _add_cover_page(doc, t["title"], t["std"], name)
    _add_toc_placeholder(doc)
    _add_footer(doc, name)

    _add_section(doc, "1", t["s1"])
    _add_section(doc, "1.1", t["s1_1"], view.get("summary") or t["none"])
    _add_section(doc, "1.2", t["s1_2"])
    crit = [c for c in view.get("success_criteria") or [] if str(c).strip()]
    if crit:
        for c in crit:
            _render_bullet(doc, f"- {c}")
    else:
        doc.add_paragraph(t["none"])

    _add_section(doc, "2", t["s2"])
    orb = view.get("orbit") or {}
    rows = [[k, _fmt(orb.get(k))] for k in ("orbit_type", "altitude_km", "inclination_deg", "ltan",
                                              "period_min", "eclipse_min", "orbits_per_day") if orb.get(k) is not None]
    if rows:
        _add_table(doc, [t["param"], t["value"]], rows)

    _add_section(doc, "3", t["s3"])
    phases = view.get("phases") or []
    if not view.get("phases_edited"):
        doc.add_paragraph(t["phases_auto"])
    if phases:
        _add_table(doc, [t["phase"], t["type"], t["dur"], t["modes"]],
                   [[p.get("name", ""), p.get("phase_type", ""), _fmt(p.get("duration_days"), 0),
                     ", ".join(p.get("modes") or [])] for p in phases])
        for i, p in enumerate(phases, 1):
            _add_section(doc, f"3.{i}", p.get("name") or t["phase"],
                         "\n\n".join(x for x in (
                             p.get("description") or "",
                             f"**{t['entry']}:** {p.get('entry_criteria') or '—'}",
                             f"**{t['exit']}:** {p.get('exit_criteria') or '—'}") if x))

    _add_section(doc, "4", t["s4"])
    modes = view.get("modes") or []
    if modes:
        _add_table(doc, [t["mode"], t["kind"], t["phase"], t["pointing"], t["sunlit"], t["share"], t["initial"]],
                   [[m.get("name", ""), m.get("kind", ""), m.get("phase") or "", m.get("pointing") or "",
                     t["yes"] if m.get("sunlit_only") else t["no"],
                     _fmt(round(100 * float(m.get("orbit_fraction") or 0), 1), 1),
                     t["yes"] if m.get("initial") else ""] for m in modes])
        for m in modes:
            if m.get("description"):
                _render_bullet(doc, f"- **{m.get('name', '')}:** {m['description']}")
    else:
        doc.add_paragraph(t["none"])
    _add_section(doc, "4.1", t["s4_1"])
    tr = view.get("transitions") or []
    if tr:
        _add_table(doc, [t["from"], t["to"], t["trigger"], t["guard"]],
                   [[x.get("from", ""), x.get("to", ""), x.get("trigger", ""), x.get("guard") or x.get("description") or ""]
                    for x in tr])
    else:
        doc.add_paragraph(t["none"])
    _add_section(doc, "4.2", t["s4_2"])
    if modes:
        _add_table(doc, [t["mode"], t["cbe"], t["total"], t["dod"], t["status"]],
                   [[m.get("name", ""), _fmt(m.get("power_cbe_w")), _fmt(m.get("power_total_w")),
                     _fmt(m.get("dod_percent"), 1), m.get("energy_status") or ""] for m in modes])
    op = view.get("operational_orbit")
    if isinstance(op, dict) and op:
        _add_table(doc, [t["op_orbit"], t["value"]],
                   [[k, _fmt(v)] for k, v in op.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)])

    _add_section(doc, "5", t["s5"])
    link = view.get("link") or {}
    gs = view.get("ground_stations") or []
    if gs:
        _add_table(doc, [t["station"]], [[g] for g in gs])
    lrows = [[t["dl_rate"], _fmt(link.get("downlink_rate_bps"), 0)], [t["ul_rate"], _fmt(link.get("uplink_rate_bps"), 0)]]
    _add_table(doc, [t["param"], t["value"]], lrows)
    contacts = (view.get("typical_day") or {}).get("contacts")
    if contacts:
        st = contacts.get("stations") or []
        if st:
            keys = [k for k in ("name", "min_per_day", "passes_per_day", "mean_pass_min", "max_pass_min") if k in st[0]]
            _add_table(doc, keys, [[_fmt(s.get(k)) for k in keys] for s in st])
        un = contacts.get("union") or {}
        if un:
            _add_table(doc, [t["param"], t["value"]], [[k, _fmt(v)] for k, v in un.items() if not isinstance(v, (dict, list))])
    else:
        doc.add_paragraph(f"{t['open_item']}: {t['contacts_open']}")

    _add_section(doc, "6", t["s6"])
    df = view.get("data_flow") or {}
    if df.get("status") != "ready":
        doc.add_paragraph(f"{t['open_item']}: " + t["df_open"].format(wp=df.get("work_package", "W3.02"),
                                                                      owner=df.get("owner", "H")))
    else:
        daily = df.get("daily") or {}
        if daily:
            _add_table(doc, [t["param"], t["value"]], [[k, _fmt(v)] for k, v in daily.items()
                                                       if not isinstance(v, (dict, list))])
        for c in df.get("cases") or []:
            if isinstance(c, dict):
                _render_bullet(doc, "- " + ", ".join(f"{k}: {_fmt(v)}" for k, v in c.items()
                                                      if not isinstance(v, (dict, list))))

    _add_section(doc, "7", t["s7"], t["td_intro"])
    td = view.get("typical_day") or {}
    _add_table(doc, [t["param"], t["value"]], [[t["period"], _fmt(td.get("period_min"))],
                                               [t["per_day"], _fmt(td.get("orbits_per_day"))],
                                               [t["eclipse"], _fmt(td.get("eclipse_min"), 1)]])
    if td.get("mode_minutes"):
        _add_table(doc, [t["mode"], t["share"], t["min_day"]],
                   [[m["mode"], _fmt(m["share_pct"], 1), _fmt(m["min_per_day"], 1)] for m in td["mode_minutes"]])

    _add_section(doc, "8", t["s8"])
    fr = view.get("flight_rules") or []
    if fr:
        _add_table(doc, [t["rule"], t["text"], t["ref"]], [[r["id"], r["text"], r.get("ref") or ""] for r in fr])
    else:
        doc.add_paragraph(t["none"])

    _add_section(doc, "9", t["s9"])
    sm = view.get("safe_mode")
    if sm:
        entries = ", ".join(str(e.get("ref") or e) if isinstance(e, dict) else str(e) for e in sm.get("entry") or [])
        _add_table(doc, [t["param"], t["value"]], [[t["safe_entry"], entries or "—"], [t["safe_exit"], sm.get("exit") or "—"]])
    cont = view.get("contingencies") or []
    if cont:
        _add_table(doc, [t["name"], t["trigger"], t["action"], t["level"]],
                   [[c.get("name") or "", c.get("trigger") or "", c.get("action") or "", _fmt(c.get("level"))] for c in cont])
    elif not sm:
        doc.add_paragraph(t["none"])

    _add_section(doc, "10", t["s10"])
    eol = view.get("eol") or {}
    ph = eol.get("phase") or {}
    if ph:
        _render_rich_content(doc, "\n\n".join(x for x in (
            f"**{ph.get('name', '')}** ({_fmt(ph.get('duration_days'), 0)} d)", ph.get("description") or "",
            f"**{t['entry']}:** {ph.get('entry_criteria') or '—'}",
            f"**{t['exit']}:** {ph.get('exit_criteria') or '—'}") if x))
    rows = []
    if eol.get("disposal_method"):
        rows.append([t["method"], str(eol["disposal_method"])])
    for k, v in (eol.get("constraints") or {}).items():
        rows.append([k, _fmt(v)])
    for m in eol.get("modes") or []:
        rows.append([t["mode"], f"{m.get('name')} ({_fmt(m.get('power_cbe_w'))} W)"])
    if rows:
        _add_table(doc, [t["param"], t["value"]], rows)
    if eol.get("requirements"):
        _add_table(doc, [t["req"], t["text"]], [[r.get("code") or "", r.get("text") or ""] for r in eol["requirements"]])

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
