"""SpaceCDF — study-linked licensing documents (W5.04).

Every generator takes a ``StudyExport`` (``services.export_context.collect``) and returns one
*document model*::

    {"kind", "title", "authority", "standard", "study_id", "study_name", "generated", "lang",
     "sections": [{"number", "title", "rows": [{"label", "value", "source"}], "paragraphs": [...],
                   "table": {"columns": [...], "rows": [[...]]}}],
     "open_items": [...], "to_be_confirmed": [...], "key": {...}}

``source`` says where a value comes from: ``design`` (derived from the study), ``team`` (the
Licensing tab), ``input`` (a team input that is still missing: printed as
"[APPLICANT INPUT REQUIRED: ...]"), ``tbc`` (a fact to be confirmed before filing). A value the
design can derive is never printed as an applicant input. ``services/docx/regulatory.py`` renders
the model as Word; the route ``POST /api/exports/regulatory/{kind}/{study_id}`` serves both.

Kinds: ``rsssa``, ``ised-space``, ``ised-earth`` (one document per station), ``itu-api``,
``debris``, ``un-registration``, ``export-control``, ``status``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

INPUT = "[APPLICANT INPUT REQUIRED]"
KINDS = ("rsssa", "ised-space", "ised-earth", "itu-api", "debris", "un-registration", "export-control", "status")

TITLES = {
    "rsssa": ("RSSSA operating licence application", "Global Affairs Canada",
              "Remote Sensing Space Systems Act (S.C. 2005, c. 45) and Regulations (SOR/2007-66); GAC operating "
              "licence application guide"),
    "ised-space": ("ISED space station licence: technical brief", "Innovation, Science and Economic Development Canada",
                   "CPC-2-6-02 Issue 7 (April 2026), Licensing of space stations"),
    "ised-earth": ("ISED earth station licence application", "Innovation, Science and Economic Development Canada",
                   "CPC-2-6-01 (earth stations; procedure to be confirmed) and CPC-2-0-03 (antenna siting)"),
    "itu-api": ("ITU advance publication information (API)", "ISED, for submission to the ITU Radiocommunication Bureau",
                "ITU Radio Regulations Article 9 (No. 9.1, 9.21) and Appendix 4"),
    "debris": ("Space debris mitigation plan", "Innovation, Science and Economic Development Canada",
               "ISED decision on space debris mitigation (April 2026; number to be confirmed) and N2 space station "
               "licence conditions; ISO 24113:2023"),
    "un-registration": ("Registration of a space object (UN Registration Convention, Article IV)",
                        "Canada, for transmission to the UN Secretary-General (UNOOSA)",
                        "Convention on Registration of Objects Launched into Outer Space (1975), Article IV"),
    "export-control": ("Export-control summary", "Global Affairs Canada (Export Controls)",
                       "Export and Import Permits Act; Export Control List (Wassenaar categories 5, 6, 7, 9)"),
    "status": ("Licensing status and timeline", "Project", "Filing tracker of the Licensing tab"),
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _row(label: str, value: Any, source: str = "design", field: str = "") -> dict:
    empty = value is None or value == "" or value == [] or value == {}
    if empty and source == "team":
        return {"label": label, "value": f"{INPUT[:-1]}: {field or label}]", "source": "input"}
    if empty and source == "design":
        return {"label": label, "value": "not yet in the design model", "source": "open"}
    if isinstance(value, float):
        value = f"{value:g}"
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return {"label": label, "value": str(value), "source": source}


def _sec(number: str, title: str, rows: list[dict] | None = None, paragraphs: list[str] | None = None,
         table: dict | None = None) -> dict:
    return {"number": number, "title": title, "rows": rows or [], "paragraphs": paragraphs or [],
            "table": table}


def _doc(kind: str, sx, sections: list[dict], key: dict | None = None, title: str | None = None) -> dict:
    t, auth, std = TITLES[kind]
    lic = sx.licensing or {}
    opens = [f"{s['number']} {s['title']}: {r['label']}" for s in sections for r in s["rows"]
             if r["source"] in ("input", "open")]
    return {"kind": kind, "title": title or t, "authority": auth, "standard": std,
            "study_id": sx.study_id, "study_name": sx.study_name, "mission_name": _mission_name(sx),
            "generated": _now(), "lang": sx.lang, "sections": sections, "open_items": opens,
            "to_be_confirmed": [x["text"] for x in (lic.get("to_be_confirmed") or [])], "key": key or {}}


def _mission_name(sx) -> str:
    return (sx.mission.get("definition") or {}).get("name") or sx.study_name


def _defn(sx) -> dict:
    return sx.mission.get("definition") or {}


def _mass(sx) -> dict:
    return sx.rollup.get("mass") or {}


def _ff(sx) -> str:
    return sx.rollup.get("form_factor") or ""


def _dims(ff: str) -> str:
    sizes = {"1U": "10 x 10 x 11.35 cm", "1.5U": "10 x 10 x 17 cm", "2U": "10 x 10 x 22.7 cm",
             "3U": "10 x 10 x 34.05 cm", "6U": "10 x 22.6 x 34.05 cm", "12U": "22.6 x 22.6 x 34.05 cm"}
    return sizes.get(ff, "")


def _orbit_type(defn: dict, orb: dict) -> str:
    t = str((defn.get("orbit") or {}).get("orbit_type") or "")
    circ = "circular" if float(orb.get("eccentricity") or 0.0) < 0.001 else "elliptical"
    return f"sun-synchronous, {circ}" if t.lower() in ("sso", "sun-synchronous") else f"{t or 'LEO'}, {circ}"


def _launch(sx) -> dict:
    return (sx.licensing or {}).get("launch") or {}


def _assign_table(assignments: list[dict], side: str | None = None, station: str | None = None) -> dict:
    cols = ["Id", "Station", "Direction", "Centre (MHz)", "Bandwidth (kHz)", "Emission", "Power (W)",
            "Gain (dBi)", "Polarisation", "EIRP (dBW)", "PFD at 5 deg (dBW/m2/4 kHz)", "Service", "Footnotes",
            "Coordination"]
    rows = []
    for a in assignments:
        if side and a["side"] != side:
            continue
        if station and a["station"] != station:
            continue
        rows.append([a["id"], a["station"], a["direction"] + (" (fallback)" if a.get("fallback") else ""),
                     f"{a['centre_frequency_mhz']:g}", f"{a['necessary_bandwidth_khz']:g}", a["emission_designator"],
                     "" if a.get("tx_power_w") is None else f"{a['tx_power_w']:g}", f"{a['antenna_gain_dbi']:g}",
                     a["polarisation"], "" if a.get("eirp_dbw") is None else f"{a['eirp_dbw']:g}",
                     "" if a.get("pfd_5deg_dbw_m2_4khz") is None else f"{a['pfd_5deg_dbw_m2_4khz']:g}",
                     a["service"], ", ".join("RR " + f if f[0].isdigit() else f for f in a.get("footnotes") or []),
                     a["coordination"]])
    return {"columns": cols, "rows": rows}


def _disposal_rows(d: dict) -> list[dict]:
    sail = d.get("sail") or {}
    ws, wo = d.get("lifetime_with_sail_y") or {}, d.get("lifetime_without_sail_y") or {}
    rows = [
        _row("Disposal method", f"Drag sail ({sail.get('name')}), deployed at end of operational life"
             if sail else "Natural decay (no disposal device)"),
        _row("Deployed sail area", f"{sail.get('deployed_area_m2')} m2" if sail else "none"),
        _row("Effective (tumbling-averaged) drag area", f"{d.get('area_deployed_effective_m2')} m2 "
             f"(0.38 x deployed + 0.05 m2 bus)" if sail else f"{d.get('area_stowed_m2')} m2 (bus, tumbling)"),
        _row("Mass used for the decay", f"{d.get('mass_kg')} kg ({d.get('mass_basis')})"),
        _row("Start of decay (worst case)", f"{d.get('start_year')} (early unrecoverable failure; the independent "
             f"timer deploys the sail)"),
        _row("Post-mission lifetime with the sail (strong / nominal / weak cycle 26)",
             " / ".join(f"{ws[k]} y" for k in ("strong", "nominal", "weak") if k in ws) if ws else "n/a"),
        _row("Lifetime without the sail (strong / nominal / weak)",
             " / ".join(f"{wo[k]} y" for k in ("strong", "nominal", "weak") if k in wo)),
        _row("Lifetime without the sail, typical range (nominal and weak cycles)",
             f"{d.get('without_sail_range_y', ['?', '?'])[0]}-{d.get('without_sail_range_y', ['?', '?'])[1]} y"),
    ]
    if d.get("highest_start_altitude_5y_km"):
        h = d["highest_start_altitude_5y_km"]
        rows.append(_row("Highest start altitude for 5 years (weak / nominal cycle)",
                         f"{h.get('weak')} km / {h.get('nominal')} km"))
    if sail:
        rows += [
            _row("Deployment triggers", sail.get("trigger") or []),
            _row("Independent release circuits", sail.get("independent_circuits")),
            _row("Independent timer", f"{sail.get('independent_timer_days')} days without a ground contact"
                 if sail.get("independent_timer_days") else "none"),
            _row("Disposal (sail deployment) reliability", f"{d.get('disposal_reliability')} = mechanism "
                 f"{sail.get('mechanism_reliability')} x (1 - (1 - {sail.get('circuit_reliability')})^"
                 f"{sail.get('independent_circuits')}); to be demonstrated by deployment tests"),
        ]
    if d.get("cbe_case"):
        c = d["cbe_case"]
        rows.append(_row("Sensitivity: current best estimate mass", f"{c['mass_kg']} kg: with sail "
                         + " / ".join(f"{v} y" for v in (c.get("lifetime_with_sail_y") or {}).values())))
    return rows


def _checks_table(d: dict) -> dict:
    rows = []
    for c in d.get("checks") or []:
        ok = c.get("pass")
        rows.append([c["id"], c["rule"], f"{c['value']} {c.get('unit') or ''}".strip(),
                     f"{c['limit']} {c.get('unit') or ''}".strip(),
                     "PASS" if ok else ("FAIL" if ok is False else "OPEN"), c.get("basis", "")])
    return {"columns": ["Check", "ISED condition", "Value", "Limit", "Result", "Basis"], "rows": rows}


def _evidence_rows(d: dict) -> list[dict]:
    ev = d.get("evidence") or []
    if not ev:
        return [_row("DRAMA / DAS result", "not yet imported: run ESA DRAMA (OSCAR, ARES, MIDAS, SARA) or NASA "
                     "DAS for the operational and disposal phases and import the result in the Licensing tab",
                     "open")]
    out = []
    for e in ev:
        parts = [f"{k.replace('_', ' ')} {v}" for k, v in e.items() if k not in ("tool", "version") and v not in (None, "")]
        out.append(_row(f"{e.get('tool')} {e.get('version') or ''}".strip(), "; ".join(parts), "team"))
    return out


# ───────────────────────────────────────────────────────────────── RSSSA

def rsssa(sx) -> dict:
    lic, d = sx.licensing or {}, (sx.licensing or {}).get("disposal") or {}
    ap, cd, dp = lic.get("applicant") or {}, lic.get("cdpp") or {}, lic.get("data_policy") or {}
    defn, orb, mo = _defn(sx), lic.get("orbit") or {}, sx.mission.get("orbit") or {}
    sensor, ln = lic.get("sensor") or {}, _launch(sx)
    stations = lic.get("stations") or []
    m, ff = _mass(sx), _ff(sx)
    ops = defn.get("design_lifetime_years")
    st_table = {"columns": ["Station", "Latitude", "Longitude", "Elevation mask (deg)", "Role"],
                "rows": [[s["name"], f"{s['lat']:.2f}", f"{s['lon']:.2f}", f"{s.get('min_elevation_deg') or 10:g}",
                          "command and data (UHF)"] for s in stations]}
    dl = next((a for a in lic.get("assignments") or [] if a["id"] == "SS-TX-DL"), {})
    ul = next((a for a in lic.get("assignments") or [] if a["id"] == "SS-RX-UL"), {})
    secs = [
        _sec("1", "Applicant identification", [_row("Legal name", ap.get("legal_name"), "team", "legal name"),
                                                 _row("Address", ap.get("address"), "team", "address"),
                                                 _row("Country", ap.get("country") or "Canada", "team")]),
        _sec("2", "Contact person", [_row("Name", ap.get("contact_name"), "team", "contact name"),
                                     _row("E-mail", ap.get("contact_email"), "team", "contact e-mail"),
                                     _row("Telephone", ap.get("contact_phone"), "team", "telephone")]),
        _sec("3", "Canadian presence", [_row("Canadian entity", {True: "yes", False: "no"}.get(ap.get("canadian_entity"), ""),
                                             "team", "Canadian entity (yes/no)")]),
        _sec("4", "Ownership and control", [_row("Owners and control", lic.get("notes"), "team",
                                                 "owners holding 10 % or more, and control")]),
        _sec("5", "Officers and responsible persons", [_row("Security officer", ap.get("security_officer"), "team",
                                                            "security officer")]),
        _sec("6", "Security screening", [_row("Reliability status of personnel with system access",
                                              cd.get("personnel_security"), "team", "security screening plan")]),
        _sec("7", "Foreign ownership and agreements", [_row("Affiliates (see §31)",
                                                            f"{len(lic.get('affiliates') or [])} listed", "team")]),
        _sec("8", "Data distribution plan (summary)", [_row("Distribution", dp.get("distribution"), "team",
                                                            "data distribution plan")]),
        _sec("9", "System name and ITU identification", [
            _row("System name", _mission_name(sx)),
            _row("ITU satellite network name", lic.get("itu_network_name"), "team", "ITU network name"),
            _row("Number of satellites", defn.get("num_spacecraft") or 1)]),
        _sec("10", "Mission, instruments and launch", [
            _row("Mission", (sx.need or {}).get("problem_statement") or defn.get("mission_type")),
            _row("Instruments", [i["name"] for i in sensor.get("instruments") or []] or sensor.get("instrument_names")),
            _row("Design life", f"{ops} years" if ops else None),
            _row("Planned launch date", ln.get("date")),
            _row("Launch vehicle / deployer", ln.get("vehicle") or ln.get("deployer"), "team", "launch vehicle"),
            _row("Launch site", ln.get("site"), "team", "launch site"),
            _row("Launch provider", ln.get("provider"), "team", "launch provider")]),
        _sec("11", "Orbit", [
            _row("Orbit type", _orbit_type(defn, orb)),
            _row("Altitude", f"{orb.get('altitude_km')} km"),
            _row("Semi-major axis", f"{6378.137 + float(orb.get('altitude_km') or 0):.1f} km"),
            _row("Eccentricity", orb.get("eccentricity") if orb.get("eccentricity") is not None else 0.0),
            _row("Inclination", f"{orb.get('inclination_deg')} deg"),
            _row("Equator crossing time (local mean solar time)", orb.get("equator_crossing")),
            _row("Local time of the descending node (LTDN)", orb.get("ltdn")),
            _row("Local time of the ascending node (LTAN)", orb.get("ltan")),
            _row("Period", f"{mo.get('period_min')} min" if mo.get("period_min") else None),
            _row("RAAN, argument of perigee, anomaly, epoch", "set by the launch; reported after injection",
                 "tbc"),
            _row("Injection tolerances", "per launch provider interface control document", "tbc")]),
        _sec("12", "System disposal plan", _disposal_rows(d) + [
            _row("Casualty risk (uncontrolled re-entry)", f"{d.get('casualty_risk')} (all-aluminium CubeSat; DAS "
                 f"to confirm total demise)"),
            _row("Hazardous materials", "Li-ion battery (passivated at end of life); no propellant")] +
            _evidence_rows(d)),
        _sec("13", "Satellite description", [
            _row("Mass (current best estimate)", f"{m.get('cbe_kg'):.2f} kg" if m.get("cbe_kg") else None),
            _row("Mass with margins", f"{m.get('with_system_margin_kg'):.2f} kg" if m.get("with_system_margin_kg") else None),
            _row("Form factor", ff),
            _row("Dimensions (stowed)", _dims(ff)),
            _row("Sensor type", "passive optical imagers (two fixed cameras, no moving parts)"
                 if sensor.get("gsd_m") else None),
            _row("Ground sample distance (payload product, nadir)", f"{sensor.get('gsd_m')} m" if sensor.get("gsd_m") else None),
            *[_row(f"Native GSD: {i['name']}", f"{i['native_gsd_m']} m ({i['pixel_pitch_um']} um pixels, "
                   f"{i['focal_length_mm']} mm focal length)") for i in sensor.get("instruments") or []],
            _row("Swath", f"{sensor.get('swath_km')} km" if sensor.get("swath_km") else None),
            _row("Spectral bands", sensor.get("spectral_bands")),
            _row("Field of view", f"{sensor.get('fov_deg')} deg" if sensor.get("fov_deg") else None),
            _row("TT&C links", f"downlink {dl.get('centre_frequency_mhz')} MHz {dl.get('emission_designator')}; "
                 f"uplink {ul.get('centre_frequency_mhz')} MHz {ul.get('emission_designator')}" if dl else None),
            _row("Satellite drawing", "attach the stack/assembly drawing exported from the Stack tab", "tbc")]),
        _sec("14", "Command protection plan: overview", [_row("Command process", cd.get("command_process"), "team",
                                                              "command process")]),
        _sec("15", "Command facilities", [_row("Mission control facility", cd.get("command_facility"), "team",
                                               "command facility"),
                                          _row("Backup facility", cd.get("backup_facility"), "team", "backup facility")]),
        _sec("16", "Ground stations", [_row("Number of stations", len(stations))], table=st_table),
        _sec("17", "Uplink characteristics", [_row("Uplink", f"{ul.get('centre_frequency_mhz')} MHz, "
                                                   f"{ul.get('emission_designator')}, {ul.get('rate_bps')} bit/s, "
                                                   f"{ul.get('service')}" if ul else None)]),
        _sec("18", "Command encryption and authentication", [
            _row("Command encryption", cd.get("command_encryption"), "team", "command encryption"),
            _row("Command authentication", cd.get("command_authentication"), "team", "command authentication")]),
        _sec("19", "Key management", [_row("Key management", cd.get("key_management"), "team", "key management"),
                                      _row("Key custody", cd.get("key_custody"), "team", "key custody")]),
        _sec("20", "Command process and procedures", [_row("Procedures", cd.get("command_process"), "team",
                                                            "command procedures")]),
        _sec("21", "Personnel security (command)", [_row("Personnel security", cd.get("personnel_security"), "team",
                                                         "personnel security")]),
        _sec("22", "Data protection plan: overview", [_row("Data facility", cd.get("data_facility"), "team",
                                                           "data facility")]),
        _sec("23", "Data reception, processing and storage facilities", [
            _row("Receiving stations", ", ".join(s["name"] for s in stations)),
            _row("Processing and archive", cd.get("data_facility"), "team", "processing and archive facility")]),
        _sec("24", "Downlink characteristics and protection", [
            _row("Downlink", f"{dl.get('centre_frequency_mhz')} MHz, {dl.get('emission_designator')}, "
                 f"{dl.get('rate_bps')} bit/s, {dl.get('service')}" if dl else None),
            _row("Downlink encryption", cd.get("downlink_encryption"), "team", "downlink encryption")]),
        _sec("25", "Data storage", [_row("On-board store", (sx.data_budget or {}).get("stores") or
                                         "payload store (see the data budget)", "design")]),
        _sec("26", "Data access control", [_row("Network security", cd.get("network_security"), "team",
                                                "network security")]),
        _sec("27", "Data distribution and sensed-state access", [
            _row("Distribution", dp.get("distribution"), "team", "distribution"),
            _row("Sensed-state access", dp.get("sensed_state_access"), "team", "sensed-state access"),
            _row("Priority access", dp.get("priority_access"), "team", "priority access")]),
        _sec("28", "Data disposal plan", [_row("Data disposal", dp.get("disposal"), "team", "data disposal plan"),
                                          _row("Retention", dp.get("retention"), "team", "retention")]),
        _sec("29", "End-user licence agreement", [_row("EULA", dp.get("eula"), "team", "EULA")]),
        _sec("30", "Physical and network security of facilities", [
            _row("Physical security", cd.get("physical_security"), "team", "physical security"),
            _row("Network security", cd.get("network_security"), "team", "network security")]),
        _sec("31", "Affiliates", table={"columns": ["Name", "Relationship", "Country"],
                                        "rows": [[a.get("name", ""), a.get("relationship", ""), a.get("country", "")]
                                                 for a in lic.get("affiliates") or []]},
             rows=[] if lic.get("affiliates") else [_row("Affiliates", None, "team", "affiliates (or 'none')")]),
        _sec("32", "System participants", table={"columns": ["Name", "Role", "Country"],
                                                 "rows": [[p.get("name", ""), p.get("role", ""), p.get("country", "")]
                                                          for p in lic.get("participants") or []]},
             rows=[] if lic.get("participants") else [_row("Participants", None, "team", "system participants")]),
        _sec("Annex A", "Ground-segment documents", paragraphs=[
            "Attach: the PDR and CDR reports (within 45 days of each review), ground-station drawings and permits, "
            "the network plan and the ground equipment list (BOM export, ground segment lines)."]),
        _sec("Annex B", "Generated technical data", table=_assign_table(lic.get("assignments") or [])),
    ]
    key = {"gsd_m": sensor.get("gsd_m"), "ltdn": orb.get("ltdn"), "mass_kg": m.get("cbe_kg"), "form_factor": ff,
           "sections": 32}
    return _doc("rsssa", sx, secs, key)


# ───────────────────────────────────────────────────────────────── ISED

def ised_space(sx) -> dict:
    lic = sx.licensing or {}
    ap, orb, d = lic.get("applicant") or {}, lic.get("orbit") or {}, lic.get("disposal") or {}
    asg = lic.get("assignments") or []
    space = [a for a in asg if a["side"] == "space"]
    dl = next((a for a in asg if a["id"] == "SS-TX-DL"), {})
    link = (sx.links or {}).get("design_case") or {}
    secs = [
        _sec("1", "Applicant", [_row("Applicant", ap.get("legal_name"), "team", "legal name"),
                                _row("Contact", ap.get("contact_name"), "team", "contact"),
                                _row("Canadian control (notarised affidavit)", None, "team", "affidavit")]),
        _sec("2", "System overview", [_row("Space station", _mission_name(sx)),
                                      _row("Mission", (sx.need or {}).get("problem_statement")),
                                      _row("Form factor and mass", f"{_ff(sx)}, {(_mass(sx).get('cbe_kg') or 0):.2f} kg"),
                                      _row("Licence type requested", "developmental or space station licence "
                                           "(to be agreed in the pre-consultation)", "tbc")]),
        _sec("3", "Orbit", [_row("Altitude", f"{orb.get('altitude_km')} km"), _row("Inclination", f"{orb.get('inclination_deg')} deg"),
                            _row("Equator crossing", orb.get("equator_crossing")),
                            _row("Apogee", f"{d.get('apogee_km')} km (at or below 600 km: no propulsion required)")]),
        _sec("4", "Frequency assignments (space station)", table=_assign_table(space)),
        _sec("5", "Space station characteristics", [
            _row("Transmitter power", f"{dl.get('tx_power_w')} W"),
            _row("Antenna", dl.get("antenna")), _row("Antenna gain", f"{dl.get('antenna_gain_dbi')} dBi"),
            _row("Polarisation", dl.get("polarisation")), _row("EIRP", f"{dl.get('eirp_dbw')} dBW"),
            _row("PFD at 5 deg elevation", f"{dl.get('pfd_5deg_dbw_m2')} dBW/m2 "
                 f"({dl.get('pfd_5deg_dbw_m2_4khz')} dBW/m2 in 4 kHz)")]),
        _sec("6", "Earth stations served", [_row("Stations", ", ".join(s["name"] for s in lic.get("stations") or []))]),
        _sec("7", "Link budgets (Annex C)", [
            _row("Design case", f"{link.get('downlink_frequency_mhz')} MHz, {link.get('downlink_rate_bps')} bit/s, "
                 f"margin {link.get('margin_db')} dB" if link else None),
            _row("Per-station cases", f"{len((sx.links or {}).get('items') or [])} named link cases (W4.04), table below"
                 if (sx.links or {}).get("items") else None)], table=_link_cases_table(sx)),
        _sec("8", "Interference and sharing", paragraphs=[
            "401-402 MHz: primary space operation (space-to-Earth); the channel avoids 401.4-401.7 MHz used by NGSO "
            "data-collection systems (ITU-R SA.2045) and is shared with radiosondes (meteorological aids).",
            "449.75-450.25 MHz: RR 5.286 permits space operation (Earth-to-space) subject to agreement under RR "
            "No. 9.21; radiolocation is primary below 450 MHz and land mobile above (Canadian footnote C23).",
            "148-149.9 MHz (fallback only): space operation (Earth-to-space) under RR 5.218, agreement under RR No. 9.21."]),
        _sec("9", "ITU filing", [_row("Network name", lic.get("itu_network_name"), "team", "ITU network name"),
                                 _row("API status", _filing_status(lic, "itu_api"))]),
        _sec("10", "Space debris mitigation plan (summary)", _disposal_rows(d)[:6],
             table=_checks_table(d), paragraphs=["The full plan is the separate debris mitigation document."]),
        _sec("11", "Timetable", [_row("Planned launch", (lic.get("launch") or {}).get("date")),
                                 _row("Apply within 6 months of ISED sending the ITU filing", "planning rule"),
                                 _row("Service standard", "126 calendar days")]),
    ]
    return _doc("ised-space", sx, secs, {"service": dl.get("service"), "emission": dl.get("emission_designator")})


def _fmt(v: Any, unit: str = "", nd: int = 1) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        v = f"{round(float(v), nd):g}"
    return f"{v} {unit}".strip()


def _case_rows(prefix: str, c: dict | None) -> list[dict]:
    """The link case (W4.04) a station's assignment is based on, as document rows."""
    if not c:
        return [_row(f"{prefix} link case", "no named link case for this station: band defaults used", "tbc")]
    return [
        _row(f"{prefix} link case", f"{c.get('name')}" + (" (design case)" if c.get("is_design_case") else "")),
        _row(f"{prefix} elevation", _fmt(c.get("elevation_deg"), "deg", 0)),
        _row(f"{prefix} slant range", _fmt(c.get("slant_range_km"), "km", 0)),
        _row(f"{prefix} data rate", _fmt((c.get("data_rate_bps") or 0) / 1e3 or None, "kbit/s")
             + (f", {c['coding']}" if c.get("coding") else "") if c.get("data_rate_bps") else None),
        _row(f"{prefix} receiver G/T", _fmt(c.get("g_over_t_dbk"), "dB/K")
             + (f" (T_sys {c['system_noise_temp_k']:g} K)" if c.get("system_noise_temp_k") else "")
             if c.get("g_over_t_dbk") is not None else None),
        _row(f"{prefix} Eb/N0", _fmt(c.get("ebn0_db"), "dB")),
        _row(f"{prefix} margin", _fmt(c.get("margin_db"), "dB")),
    ]


def _link_cases_table(sx) -> dict | None:
    items = (sx.links or {}).get("items") or []
    if not items:
        return None
    rows = []
    for c in items:
        r = c.get("results") or {}
        m = c.get("margin_db") if c.get("margin_db") is not None else r.get("margin_db")
        rows.append([c.get("name") or c.get("id"), c.get("direction"), c.get("station") or "",
                     f"{c.get('elevation_deg') or 0:g}", f"{(c.get('data_rate_bps') or 0) / 1e3:g}",
                     f"{c.get('tx_power_w') or 0:g}", "" if r.get("eirp_dbw") is None else f"{r['eirp_dbw']:g}",
                     "" if r.get("g_over_t_dbk") is None else f"{r['g_over_t_dbk']:g}",
                     "" if m is None else f"{round(m, 1):g}", "yes" if c.get("is_design_case") else ""])
    return {"columns": ["Case", "Direction", "Station", "Elevation (deg)", "Rate (kbit/s)", "Power (W)", "EIRP (dBW)",
                        "G/T (dB/K)", "Margin (dB)", "Design case"], "rows": rows}


def ised_earth(sx) -> list[dict]:
    """One ISED earth-station application per ground station. Transmit power, antenna gain and line
    loss come from the station's link case (W4.04) unless the Licensing tab overrides them for the
    assignment (``assignment_overrides``)."""
    lic = sx.licensing or {}
    asg = lic.get("assignments") or []
    ap = lic.get("applicant") or {}
    docs = []
    for st in lic.get("stations") or []:
        mine = [a for a in asg if a["station"] == st["name"]]
        tx = next((a for a in mine if a["transmits"]), {})
        rx = next((a for a in mine if not a["transmits"]), {})
        height = tx.get("antenna_height_m") or rx.get("antenna_height_m")
        basis = {"link case": "from the link case", "licensing record": "from the Licensing tab (override)",
                 "design": "band default"}
        secs = [
            _sec("1", "Applicant", [_row("Applicant", ap.get("legal_name"), "team", "legal name"),
                                    _row("Contact", ap.get("contact_name"), "team", "contact"),
                                    _row("Address", ap.get("address"), "team", "address")]),
            _sec("2", "Site", [_row("Station", st["name"]), _row("Latitude", f"{st['lat']:.4f}"),
                               _row("Longitude", f"{st['lon']:.4f}"),
                               _row("Antenna height above ground", _fmt(height, "m"), "team", "antenna height"),
                               _row("Minimum elevation", f"{st.get('min_elevation_deg') or 10:g} deg"),
                               _row("Antenna siting consultation (CPC-2-0-03)", "exemption to be confirmed", "tbc")]),
            _sec("3", "Frequency assignments (earth station)", table=_assign_table(mine)),
            _sec("4", "Transmitter", [_row("Power", f"{tx.get('tx_power_w'):g} W (at most)" if tx.get("tx_power_w") else None),
                                      _row("Antenna", tx.get("antenna")),
                                      _row("Gain", _fmt(tx.get("antenna_gain_dbi"), "dBi")),
                                      _row("Line loss", _fmt(tx.get("line_loss_db"), "dB")),
                                      _row("EIRP", _fmt(tx.get("eirp_dbw"), "dBW")),
                                      _row("Basis", basis.get(tx.get("basis"), tx.get("basis")))]),
            _sec("5", "Receiver", [_row("Antenna", rx.get("antenna")),
                                   _row("Gain", _fmt(rx.get("antenna_gain_dbi"), "dBi")),
                                   _row("System noise temperature", _fmt(rx.get("system_noise_temp_k"), "K", 0)),
                                   _row("Basis", basis.get(rx.get("basis"), rx.get("basis")))]),
            _sec("6", "Link budgets (W4.04 link cases)",
                 _case_rows("Uplink", tx.get("link_case")) + _case_rows("Downlink", rx.get("link_case"))),
            _sec("7", "Sharing", paragraphs=["Uplink at 449.75-450.25 MHz: protect land-mobile users above 450 MHz "
                                             "(C23) and radiolocation below; transmit only above the elevation mask "
                                             "and while the satellite is in view."]),
        ]
        dlc = rx.get("link_case") or {}
        docs.append(_doc("ised-earth", sx, secs,
                         {"station": st["name"], "tx_power_w": tx.get("tx_power_w"), "eirp_dbw": tx.get("eirp_dbw"),
                          "uplink_case": (tx.get("link_case") or {}).get("name"), "downlink_case": dlc.get("name"),
                          "downlink_margin_db": dlc.get("margin_db")},
                         title=f"ISED earth station licence application: {st['name']}"))
    return docs


def _filing_status(lic: dict, fid: str) -> str:
    f = next((x for x in lic.get("filings") or [] if x["id"] == fid), None)
    if not f:
        return "not started"
    return f["status"].replace("_", " ") + (f" ({f['submitted']})" if f.get("submitted") else "")


# ───────────────────────────────────────────────────────────────── ITU

def itu_api(sx) -> dict:
    lic = sx.licensing or {}
    orb, d = lic.get("orbit") or {}, lic.get("disposal") or {}
    mo = sx.mission.get("orbit") or {}
    asg = [a for a in lic.get("assignments") or [] if not a.get("fallback")]
    services = sorted({a["service"] for a in asg if a["side"] == "space"})
    secs = [
        _sec("A", "Notifying administration and network", [
            _row("Notifying administration", "CAN"), _row("Satellite network name", lic.get("itu_network_name"),
                                                          "team", "network name"),
            _row("Service(s)", "; ".join(services)), _row("Number of satellites", 1),
            _row("Date of bringing into use", (lic.get("launch") or {}).get("date")),
            _row("Operator", (lic.get("applicant") or {}).get("legal_name"), "team", "operator")]),
        _sec("B", "Orbital characteristics (non-geostationary)", [
            _row("Apogee", f"{d.get('apogee_km') or orb.get('altitude_km')} km"),
            _row("Perigee", f"{orb.get('altitude_km')} km"), _row("Inclination", f"{orb.get('inclination_deg')} deg"),
            _row("Period", f"{mo.get('period_min')} min" if mo.get("period_min") else None),
            _row("Number of orbital planes", 1), _row("Satellites per plane", 1)]),
        _sec("C", "Frequency assignments", table=_assign_table(asg)),
        _sec("D", "Coordination", paragraphs=[
            "Downlink 401-402 MHz: advance publication (RR No. 9.1), comments within four months (RR No. 9.3), then "
            "notification (Article 11) within seven years.",
            "Uplink 449.75-450.25 MHz: agreement sought under RR No. 9.21 (RR 5.286).",
            "The Resolution 32 short-duration route does not apply to a band subject to RR No. 9.21."]),
    ]
    return _doc("itu-api", sx, secs, {"services": services})


# ───────────────────────────────────────────────────────────────── debris

def _assessment(sx) -> dict | None:
    sec = getattr(sx, "debris", None) or {}
    return sec.get("assessment") if isinstance(sec, dict) else None


def _casualty_rows(d: dict, a: dict | None) -> list[dict]:
    """Section 6: the in-tool DAS-like screening when the team has run it, else the old basis."""
    cas = (a or {}).get("casualty") or {}
    if not cas:
        return [_row("Casualty expectation", d.get("casualty_risk")),
                _row("Basis", "small all-aluminium CubeSat expected to demise fully; run the debris assessment in "
                     "the tool, then confirm with DAS or DRAMA SARA", "tbc")]
    surv = [f for f in cas.get("fragments") or [] if f.get("counted")]
    return [_row("Casualty expectation", f"{cas.get('casualty_expectation'):.1e} (1 in {cas.get('one_in'):,})"
                 if cas.get("one_in") else "0 (every fragment below 15 J)"),
            _row("Limit", "1:10 000 (1e-4)"),
            _row("Debris casualty area", f"{cas.get('dca_m2')} m2"),
            _row("Surviving fragments counted", ", ".join(f"{f['pieces']} x {f['material']} ({f['component']})" for f in surv)
                 or "none"),
            _row("Method", cas.get("method") + "; confirm with DAS or DRAMA SARA", "tbc")]


def _assessment_rows(a: dict | None) -> list[dict]:
    if not a:
        return [_row("Assessment", None, "team", "run the debris assessment (Licensing tab, Disposal)")]
    lt = a.get("lifetime") or {}
    acc = a.get("status") == "accepted"
    return [_row("Assessment version", f"v{a.get('version')} ({a.get('created_at') or ''})".strip()),
            _row("Lifetime with the device, worst cycle", f"{lt.get('worst_with_device_y')} y"
                 if lt.get("worst_with_device_y") is not None else None),
            _row("Lifetime without the device, worst cycle", f"{lt.get('worst_without_device_y')} y"
                 if lt.get("worst_without_device_y") is not None else None),
            _row("Collision probability (>= 10 cm, operational life)", (a.get("collision") or {}).get("operational_large")),
            _row("Casualty expectation", (a.get("casualty") or {}).get("casualty_expectation")),
            _row("Every check met", "yes" if a.get("compliant") else "no"),
            _row("Accepted", f"at {str(a.get('accepted_gate') or '').upper()} by {a.get('accepted_by')} "
                 f"({a.get('accepted_at') or ''})" if acc else None, "team", "acceptance at a review"),
            *([_row("Deviation", a.get("deviation"))] if a.get("deviation") else [])]


def debris(sx) -> dict:
    lic = sx.licensing or {}
    d = lic.get("disposal") or {}
    a = _assessment(sx)
    rules = d.get("rules") or {}
    secs = [
        _sec("1", "Mission and orbit", [_row("Space station", _mission_name(sx)),
                                        _row("Orbit", f"{d.get('altitude_km')} km circular, apogee {d.get('apogee_km')} km"),
                                        _row("Operational life", f"{d.get('operations_years')} years from {d.get('launch_date')}")]),
        _sec("2", "Applicable conditions", paragraphs=[
            f"{rules.get('decision', 'ISED decision on space debris mitigation (April 2026)')}; {rules.get('conditions', '')}.",
            "Disposal within 5 years of the end of operational life (which includes an unrecoverable anomaly); "
            "disposal probability at least 90 % (99 % encouraged); collision probability below 0.001 with objects of "
            "10 cm or more and below 0.01 with smaller objects over the operational life; active propulsion when the "
            "apogee is above 600 km; trackable (smallest dimension at least 10 cm, deployables excluded); orbital "
            "environment assessed within 30 km of the orbit; SSA registration with 24/7 contact."]),
        _sec("3", "Compliance summary", table=_checks_table(d)),
        _sec("4", "Disposal method and lifetime", _disposal_rows(d),
             table={"columns": ["Case", "Cycle 26", "Start", "Area (m2)", "Lifetime (y)"],
                    "rows": [[r["case"].replace("_", " "), r["scenario"], f"{r['start_year']}", f"{r['area_m2']}",
                              f"{r['lifetime_years']}"] for r in d.get("scenarios") or []]}),
        _sec("5", "Collision probability", [
            _row("Operational life, objects >= 10 cm", d.get("collision_probability_large")),
            _row("Operational life, objects < 10 cm", d.get("collision_probability_small")),
            _row("Disposal phase with the sail, objects >= 10 cm", d.get("collision_probability_disposal_large")),
            _row("Method", "screening flux by altitude (catalogue spatial density x 10 km/s); replace with DRAMA ARES "
                 "or DAS", "tbc")]),
        _sec("6", "Re-entry casualty risk", _casualty_rows(d, a)),
        _sec("7", "Passivation", paragraphs=[
            "At end of life: deploy the sail, switch off both transmitters permanently, discharge the battery and "
            "open the solar-array charge path. No propellant or pressurised system on board."]),
        _sec("8", "Trackability and SSA", [
            _row("Smallest dimension", f"{d.get('smallest_dimension_cm')} cm" if d.get("smallest_dimension_cm") else None),
            _row("SSA registration and 24/7 contact", (lic.get("applicant") or {}).get("contact_name"), "team",
                 "24/7 operations contact"),
            _row("Conjunction assessment", "screening by a conjunction service; no manoeuvre capability (no "
                 "propulsion): the operator informs the other operator and the SSA service", "design"),
            _row("Orbital environment within 30 km", "to be assessed with the launch provider's injection orbit "
                 "and the catalogue (DRAMA or a commercial service)", "tbc")]),
        _sec("9", "Evidence (DRAMA / DAS)", _evidence_rows(d)),
        _sec("10", "Debris assessment in the tool and its acceptance", _assessment_rows(a)),
    ]
    ws = d.get("lifetime_with_sail_y") or {}
    return _doc("debris", sx, secs, {"lifetime_nominal_y": ws.get("nominal"), "lifetime_weak_y": ws.get("weak"),
                                     "reliability": d.get("disposal_reliability"),
                                     "pc_large": d.get("collision_probability_large"), "compliant": d.get("compliant")})


# ───────────────────────────────────────────────────────────────── UN registration

def un_registration(sx) -> dict:
    lic = sx.licensing or {}
    orb, ln = lic.get("orbit") or {}, _launch(sx)
    mo = sx.mission.get("orbit") or {}
    alt = orb.get("altitude_km")
    secs = [_sec("IV", "Article IV information", [
        _row("(a) Name of launching State(s)", "Canada (and the State of the launch site, see (c))", "tbc"),
        _row("(b) Designator or registration number", "COSPAR designator assigned after launch", "tbc"),
        _row("(c) Date and territory or location of launch", f"{ln.get('date') or 'TBD'}; {ln.get('site') or ''}".strip("; "),
             "team" if ln.get("site") else "tbc"),
        _row("(d)(i) Nodal period", f"{mo.get('period_min')} min" if mo.get("period_min") else None),
        _row("(d)(ii) Inclination", f"{orb.get('inclination_deg')} deg"),
        _row("(d)(iii) Apogee", f"{alt} km"), _row("(d)(iv) Perigee", f"{alt} km"),
        _row("(e) General function", "Earth observation: monitoring of northern wildfires and river and lake ice "
             "(education and science)" if "fire" in _mission_name(sx).lower() else
             (sx.need or {}).get("problem_statement") or "Earth observation"),
        _row("Owner/operator", (lic.get("applicant") or {}).get("legal_name"), "team", "owner/operator")])]
    return _doc("un-registration", sx, secs)


# ───────────────────────────────────────────────────────────────── export control

def export_control(sx) -> dict:
    """Per-part classification from ``bom_generator.export_control_of`` (W5.05: the element's
    ``performance.export_control``, the KB part's default, then the InGaAs / crypto / GNSS rules), and
    the flags of ``bom_generator.export_assessment_flags`` as the actions."""
    from .bom_generator import export_assessment_flags, export_control_of
    els = [e for e in (sx.elements or {}).get("items") or [] if not e.get("deleted_at")]
    by_id = {e.get("id"): e for e in els}
    items = []
    for e in els:
        if (e.get("segment") or "space") != "space" or e.get("element_type") != "component":
            continue
        ec = export_control_of(e, by_id.get(e.get("parent_id")))
        if not (ec["controlled"] or [r for r in ec["rules"] if r != "EC-US-ORIGIN"] or ec["eccn"]):
            continue
        basis = ", ".join(r.replace("EC-", "") for r in ec["rules"]) or "export-control data"
        items.append([str(e.get("name") or ""), ec["eccn"] or "to classify", ec["origin"] or "",
                      ec["permit"] or "", basis])
    flags = export_assessment_flags([e for e in els if (e.get("segment") or "space") == "space"])
    secs = [
        _sec("1", "Controlled items (by part)", table={"columns": ["Item", "Classification", "Origin", "Permit",
                                                                   "Rule"], "rows": items}),
        _sec("2", "Flags", table={"columns": ["Flag", "Severity", "Parts", "Basis", "Action"],
                                  "rows": [[f["flag"], f["severity"], f["parameter"], f["detail"], f["action"]]
                                           for f in flags]}),
        _sec("3", "Spacecraft", [_row("Complete spacecraft", "Export Control List Group 2/9 spacecraft item (to be "
                                      "confirmed); a permit is needed to export to a foreign launch site", "tbc")]),
        _sec("4", "Actions", paragraphs=[
            "Ask the SWIR camera vendor for its ECCN and the export authorisation it ships under before ordering the "
            "engineering model; re-export of the camera or of the satellite needs a Canadian export permit.",
            "Record the ECCN, origin and permit on each BOM line (Element Properties, export control)."]),
    ]
    return _doc("export-control", sx, secs, {"items": len(items), "flags": [f["flag"] for f in flags]})


# ───────────────────────────────────────────────────────────────── status

def status(sx) -> dict:
    lic = sx.licensing or {}
    rows = [[f["title"], f["authority"], f.get("start_by", ""), f["status"].replace("_", " "), f.get("submitted", ""),
             f.get("received", ""), f.get("granted", ""), f.get("conditions", "")] for f in lic.get("filings") or []]
    secs = [_sec("1", "Filings", table={"columns": ["Filing", "Authority", "Start by", "Status", "Submitted",
                                                    "Received", "Granted", "Conditions"], "rows": rows})]
    return _doc("status", sx, secs, {"filings": len(rows)})


GENERATORS = {"rsssa": rsssa, "ised-space": ised_space, "ised-earth": ised_earth, "itu-api": itu_api,
              "debris": debris, "un-registration": un_registration, "export-control": export_control,
              "status": status}

SECTIONS_NEEDED = ["need", "mission", "elements", "rollup", "links", "data_budget", "contacts", "licensing", "debris"]


async def build(kind: str, study_id: str, *, lang: str = "en", gate: str | None = None) -> dict | list[dict]:
    """The document model(s) of ``kind`` for a study (``ised-earth`` gives a list)."""
    from .export_context import collect
    if kind not in GENERATORS:
        raise KeyError(kind)
    sx = await collect(study_id, gate=gate, lang=lang, sections=SECTIONS_NEEDED)
    return GENERATORS[kind](sx)
