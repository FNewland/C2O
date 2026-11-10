"""SpaceCDF export family: deorbit.

Deorbit / end-of-life compliance report (json/docx).
Routes (prefix /api/exports): POST /deorbit/{study_id}

W1.09c / W5.02 (agent L): the report runs the disposal analysis of ``services/licensing.py``
(calibrated decay model with the drag sail, solar-cycle scenarios from the launch date, the ISED
conditions) instead of importing functions that never existed (EG D1), and lists "Vent
propellant" only when the spacecraft carries propellant (EG D13). Mass and form factor come from
the one roll-up (W0.3).
"""
from __future__ import annotations

import io
import re

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()


def _has_propellant(elements: list[dict]) -> bool:
    """True when a space element holds propellant or pressurant (a drag sail in the propulsion
    domain does not, EG D13)."""
    for e in elements:
        if (e.get("segment") or "space") != "space":
            continue
        p = e.get("performance") or {}
        prop = str(p.get("propellant_type") or "").lower()
        if prop and prop not in ("none", "n/a", "-"):
            return True
        if (p.get("isp_s") or 0) > 0 or (p.get("propellant_mass_kg") or 0) > 0:
            return True
        if e.get("element_type") == "component" and re.search(
                r"thruster|propellant|tank|engine|resistojet|cold gas", str(e.get("name") or ""), re.I):
            return True
    return False


def passivation_checklist(elements: list[dict], has_sail: bool) -> list[dict]:
    space = [e for e in elements if (e.get("segment") or "space") == "space"]
    names = " ".join(str(e.get("name") or "").lower() for e in space)
    doms = {e.get("subsystem_domain") for e in space}
    out = []
    if has_sail:
        out.append({"item": "Deploy the drag sail",
                    "description": "Deploy by command at end of operations; the independent timer or the "
                                   "under-voltage trigger deploys it if the satellite falls silent",
                    "standard": "ISED debris mitigation conditions (disposal within 5 years)"})
    if doms & {"eps", "power"} or "battery" in names:
        out.append({"item": "Discharge batteries", "standard": "ISO 24113 Cl. 6.2.3.1",
                    "description": "Discharge batteries to a safe level and open the charge path"})
    if _has_propellant(space):
        out.append({"item": "Vent propellant", "standard": "ISO 24113 Cl. 6.2.3.2",
                    "description": "Deplete or vent remaining propellant and pressurant"})
    if doms & {"ttc", "comms", "communications"} or re.search(r"radio|transmitter|transceiver", names):
        out.append({"item": "Disable transmitter", "standard": "ITU Radio Regulations Art. 22",
                    "description": "Permanently disable the RF transmitters"})
    if "wheel" in names:
        out.append({"item": "Spin down momentum wheels", "standard": "ISO 24113 Cl. 6.2.3.3",
                    "description": "De-spin reaction/momentum wheels"})
    out.append({"item": "Isolate solar arrays", "standard": "ISO 24113 Cl. 6.2.3.1",
                "description": "Open the solar array circuit to prevent battery charging"})
    return out


@router.post("/deorbit/{study_id}")
async def export_deorbit(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate the deorbit analysis and debris compliance report (ISED conditions, drag sail)."""
    from ...services.branding import get_branding
    from ...services.export_context import collect

    try:
        sx = await collect(study_id, sections=["mission", "elements", "rollup", "licensing"])
    except LookupError:
        raise HTTPException(404, f"Study {study_id} not found") from None
    elements = (sx.elements or {}).get("items") or []
    mass = (sx.rollup or {}).get("mass") or {}
    total_mass = float(mass.get("cbe_kg") or 0.0)
    form_factor = sx.rollup.get("form_factor") or "Custom"
    d = (sx.licensing or {}).get("disposal") or {}
    altitude_km = float(((sx.mission.get("definition") or {}).get("orbit") or {}).get("altitude_km") or 500.0)
    sail = d.get("sail") or None
    ws, wo = d.get("lifetime_with_sail_y") or {}, d.get("lifetime_without_sail_y") or {}

    lifetime_scenarios = []
    for r in d.get("scenarios") or []:
        lifetime_scenarios.append({
            "scenario": f"{r['scenario'].title()} cycle 26, {r['case'].replace('_', ' ')}",
            "case": r["case"], "solar": r["scenario"], "start_year": r["start_year"], "area_m2": r["area_m2"],
            "lifetime_years": r["lifetime_years"],
            "compliant_5yr": r["lifetime_years"] <= 5.0, "compliant_25yr": r["lifetime_years"] <= 25.0})
    worst = max(ws.values()) if ws else (max(wo.values()) if wo else None)
    checks = {c["id"]: c for c in d.get("checks") or []}
    analysis = {
        "post_mission_lifetime_years_worst": worst,
        "lifetime_with_sail_years": ws, "lifetime_without_sail_years": wo,
        "without_sail_range_years": d.get("without_sail_range_y"),
        "disposal_reliability": d.get("disposal_reliability"),
        "collision_probability_large": d.get("collision_probability_large"),
        "collision_probability_small": d.get("collision_probability_small"),
        "casualty_risk": d.get("casualty_risk"),
        "mass_used_kg": d.get("mass_kg"), "mass_basis": d.get("mass_basis"),
        "model": d.get("model"), "evidence": d.get("evidence") or [],
    }
    passivation = passivation_checklist(elements, bool(sail))
    compliance_summary = {
        "ised_5yr": (checks.get("ISED-DM-01") or {}).get("pass"),
        "ised_reliability_90pct": (checks.get("ISED-DM-02") or {}).get("pass"),
        "ised_collision_large": (checks.get("ISED-DM-03") or {}).get("pass"),
        "ised_collision_small": (checks.get("ISED-DM-04") or {}).get("pass"),
        "ised_apogee_600km": (checks.get("ISED-DM-05") or {}).get("pass"),
        "ised_trackable": (checks.get("ISED-DM-06") or {}).get("pass"),
        "iadc_25yr": worst is not None and worst <= 25.0,
        "casualty_risk_compliant": (d.get("casualty_risk") or 0) < 1e-4,
        "passivation_items_count": len(passivation),
        "compliant": d.get("compliant"),
    }

    b = get_branding()
    data = {
        "document": "Deorbit Analysis & Debris Compliance Report",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "spacecraft": {"total_mass_kg": round(total_mass, 2), "altitude_km": altitude_km, "form_factor": form_factor,
                       "cross_section_m2": d.get("area_stowed_m2"),
                       "drag_sail": sail and {"name": sail.get("name"), "deployed_area_m2": sail.get("deployed_area_m2"),
                                              "effective_area_m2": d.get("area_deployed_effective_m2"),
                                              "independent_circuits": sail.get("independent_circuits"),
                                              "trigger": sail.get("trigger")}},
        "analysis": analysis,
        "lifetime_scenarios": lifetime_scenarios,
        "ised_checks": d.get("checks") or [],
        "passivation_checklist": passivation,
        "compliance_summary": compliance_summary,
        "standards": {
            "ised": (d.get("rules") or {}).get("decision", "ISED decision on space debris mitigation (April 2026)"),
            "ised_conditions": (d.get("rules") or {}).get("conditions", ""),
            "iso_24113": "ISO 24113:2023 — Space debris mitigation requirements",
            "iadc_25yr": "IADC guideline (25 years; superseded for Canadian licences by the ISED 5-year rule)",
        },
        "notes": d.get("notes") or [],
        "error": d.get("error"),
    }

    if fmt.lower() == "docx":
        from ...services.branding import create_branded_docx
        doc = create_branded_docx("Deorbit Analysis & Debris Compliance Report", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        def table(cols: list[str], rows: list[list]) -> None:
            t = doc.add_table(rows=1, cols=len(cols), style="Light List Accent 1")
            for i, c in enumerate(cols):
                t.rows[0].cells[i].text = c
            for r in rows:
                cells = t.add_row().cells
                for i, v in enumerate(r):
                    cells[i].text = "" if v is None else str(v)

        doc.add_heading("1. Spacecraft Parameters", level=1)
        doc.add_paragraph(f"Total mass (current best estimate): {round(total_mass, 2)} kg; mass used for the "
                          f"decay: {d.get('mass_kg')} kg ({d.get('mass_basis')})")
        doc.add_paragraph(f"Orbit altitude: {altitude_km} km; apogee {d.get('apogee_km')} km")
        doc.add_paragraph(f"Form factor: {form_factor}; tumbling area without the sail {d.get('area_stowed_m2')} m²")
        if sail:
            doc.add_paragraph(f"Drag sail: {sail.get('name')}, {sail.get('deployed_area_m2')} m² deployed, "
                              f"effective {d.get('area_deployed_effective_m2')} m²; triggers: "
                              f"{', '.join(sail.get('trigger') or [])}; {sail.get('independent_circuits')} "
                              f"independent release circuit(s)")
        doc.add_heading("2. Lifetime Analysis — Solar-Cycle Scenarios", level=1)
        if ws:
            doc.add_paragraph(f"With the sail (from {d.get('start_year')}): " +
                              ", ".join(f"{k} {v} y" for k, v in ws.items()))
        doc.add_paragraph("Without the sail: " + ", ".join(f"{k} {v} y" for k, v in wo.items()) +
                          f" (typical range {d.get('without_sail_range_y')} y)")
        table(["Scenario", "Start", "Area (m²)", "Lifetime (y)", "5-year rule"],
              [[s["scenario"], s["start_year"], s["area_m2"], s["lifetime_years"],
                "PASS" if s["compliant_5yr"] else "FAIL"] for s in lifetime_scenarios])
        doc.add_heading("3. ISED Debris Mitigation Conditions", level=1)
        table(["Check", "Condition", "Value", "Limit", "Result"],
              [[c["id"], c["rule"], c["value"], c["limit"],
                "PASS" if c["pass"] else ("FAIL" if c["pass"] is False else "OPEN")] for c in d.get("checks") or []])
        doc.add_heading("4. Passivation Checklist", level=1)
        table(["Action", "Description", "Standard"], [[p["item"], p["description"], p["standard"]] for p in passivation])
        doc.add_heading("5. Evidence and Model", level=1)
        doc.add_paragraph(f"Model: {d.get('model')}")
        for ev in d.get("evidence") or []:
            doc.add_paragraph(f"{ev.get('tool')} {ev.get('version') or ''}: lifetime {ev.get('lifetime_years')} y, "
                              f"Pc {ev.get('collision_probability')}, casualty {ev.get('casualty_risk')}",
                              style="List Bullet")
        if not d.get("evidence"):
            doc.add_paragraph("No DRAMA/DAS result imported yet (Licensing tab).")
        for n in d.get("notes") or []:
            doc.add_paragraph(n, style="List Bullet")
        doc.add_heading("6. Applicable Standards", level=1)
        for std in data["standards"].values():
            if std:
                doc.add_paragraph(std, style="List Bullet")
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="Deorbit_Report_{study_id}.docx"'},
        )

    return JSONResponse(content=data)
