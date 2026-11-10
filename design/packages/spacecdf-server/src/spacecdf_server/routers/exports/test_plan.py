"""SpaceCDF export family: test_plan.

Test plan (json/docx/xlsx).
Routes (prefix /api/exports): POST /test-plan/{study_id}

W1.09j: the launcher comes from the mission definition (``launch_vehicle``) or from the launch
segment elements; with no launcher named the levels are a labelled generic envelope (they used
to default silently to one specific launcher). Wave 2: the levels are
``services.ait.environment_levels`` (W8a: protoflight, GEVS spectra, the launcher's quasi-static
loads when named, the launch provider's ICD when the launch is provided).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from ..studies import get_study_store

router = APIRouter()

#: launchers with an envelope in spacecdf_common.physics.structures.launch_loads
KNOWN_LAUNCHERS = ("electron", "falcon_9", "falcon_heavy", "vega_c", "ariane_6", "pslv", "soyuz", "h3", "sls",
                   "starship", "new_glenn", "long_march_5")
#: quasi-static envelope used when no launcher is identified (C2O default; labelled as such)
GENERIC_QSL = (6.0, 2.0)


def _match_launcher(text: str) -> str | None:
    t = (text or "").lower().replace("-", " ").replace("_", " ")
    for lv in KNOWN_LAUNCHERS:
        if lv.replace("_", " ") in t:
            return lv
    return None


def identify_launcher(study, elements: list[dict]) -> tuple[str | None, str, str]:
    """(envelope key or None, label, source) of the study's launcher: ``mission.launch_vehicle``,
    then the launch segment elements, then the study notes."""
    req = getattr(study, "requirements", None) if study is not None else None
    lv = getattr(req, "launch_vehicle", None) if req is not None else None
    if lv:
        return _match_launcher(str(lv)), str(lv), "mission.launch_vehicle"
    ids = {e.get("id"): e for e in elements}

    def in_launch(e: dict) -> bool:
        cur, n = e, 0
        while cur is not None and n < 50:
            if cur.get("segment") == "launch":
                return True
            cur, n = ids.get(cur.get("parent_id")), n + 1
        return False

    launch = [e for e in elements if e.get("element_type") != "segment" and in_launch(e)]
    for e in launch:
        perf = e.get("performance") if isinstance(e.get("performance"), dict) else {}
        text = " ".join(str(x) for x in (perf.get("launch_vehicle"), e.get("name"), e.get("description")) if x)
        key = _match_launcher(text)
        if key:
            return key, str(perf.get("launch_vehicle") or e.get("name")), "launch segment element"
    if launch:
        return None, f"{launch[0].get('name')} (launcher not named)", "launch segment element"
    notes = getattr(study, "notes", "") if study is not None else ""
    key = _match_launcher(notes or "")
    if key:
        return key, key, "study notes"
    return None, "not selected", "none"

@router.post("/test-plan/{study_id}")
async def export_test_plan(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx, xlsx"),
) -> JSONResponse:
    """Generate AIT/AIV test plan from requirements."""
    from ...services.branding import get_branding
    from ...routers.requirements import _requirements
    from ..elements import _elements, _interfaces

    # Read study
    studies = get_study_store()
    study = studies.get(study_id)

    reqs = [r for r in _requirements.values() if r.get("study_id") == study_id and r.get("status") != "retired"]
    test_reqs = [r for r in reqs if r.get("verification_method") == "T"]
    analysis_reqs = [r for r in reqs if r.get("verification_method") == "A"]
    inspection_reqs = [r for r in reqs if r.get("verification_method") == "I"]

    # Read elements for component-level tests
    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    by_id = {e.get("id"): e for e in elements}

    def _segment(e: dict) -> str | None:   # components inherit the segment of their ancestors
        cur, n = e, 0
        while cur is not None and n < 50:
            if cur.get("segment"):
                return cur["segment"]
            cur, n = by_id.get(cur.get("parent_id")), n + 1
        return None

    space_components = [e for e in elements if e.get("element_type") == "component" and _segment(e) == "space"]

    # Read interfaces for integration test matrix
    study_interfaces = [
        i for i in _interfaces.values()
        if not i.get("deleted_at") and i.get("status") != "rejected" and (
            i.get("study_id") == study_id or
            i.get("source_element_id") in {e.get("id") for e in elements} or
            i.get("target_element_id") in {e.get("id") for e in elements}
        )
    ]

    # Build element ID -> name lookup
    element_names = {e.get("id"): e.get("name", "Unknown") for e in elements}

    test_cases = []
    for i, r in enumerate(test_reqs):
        test_cases.append({
            "test_id": f"TC-{i+1:03d}",
            "requirement_code": r.get("code", r["id"]),
            "requirement_text": r.get("text", ""),
            "level": r.get("level", "system"),
            "test_description": f"Verify: {r.get('text', '')}",
            "pass_criteria": f"Requirement {r.get('code', '')} is satisfied",
            "test_type": "Functional",
            "status": "planned",
        })

    # Component-level unit tests (one per component)
    unit_tests = []
    for j, comp in enumerate(space_components):
        unit_tests.append({
            "test_id": f"UT-{j+1:03d}",
            "component": comp["name"],
            "subsystem": comp.get("subsystem_domain", ""),
            "test_description": f"Functional verification of {comp['name']}",
            "pass_criteria": f"{comp['name']} operates within specified parameters",
            "checks": [],
        })
        # Add specific checks based on component properties
        if comp.get("mass_kg"):
            unit_tests[-1]["checks"].append(f"Mass verification: {comp['mass_kg']} kg +/- 5%")
        if comp.get("power_avg_w"):
            unit_tests[-1]["checks"].append(f"Power draw: {comp['power_avg_w']} W nominal")
        perf = comp.get("performance") or {}
        if perf.get("data_rate_mbps"):
            unit_tests[-1]["checks"].append(f"Data rate: {perf['data_rate_mbps']} Mbps")
        if perf.get("pointing_accuracy_deg"):
            unit_tests[-1]["checks"].append(f"Pointing accuracy: {perf['pointing_accuracy_deg']} deg")

    # Integration test matrix from interfaces
    integration_tests = []
    for k, iface in enumerate(study_interfaces):
        src_name = element_names.get(iface.get("source_element_id"), iface.get("source_name", "Unknown"))
        tgt_name = element_names.get(iface.get("target_element_id"), iface.get("target_name", "Unknown"))
        iface_type = iface.get("interface_type", iface.get("type", "data"))
        integration_tests.append({
            "test_id": f"IT-{k+1:03d}",
            "source": src_name,
            "target": tgt_name,
            "interface_type": iface_type,
            "test_description": f"Verify {iface_type} interface between {src_name} and {tgt_name}",
            "pass_criteria": f"Data/power/signal flows correctly between {src_name} and {tgt_name}",
        })

    # Environmental test profile: services.ait.environment_levels (W8a) from the launch segment
    env_profile: dict = {}
    try:
        from ...services.ait import _launch_provided, environment_levels
        lv_key, lv_label, lv_source = identify_launcher(study, elements)
        try:
            provided = await _launch_provided(study_id)
        except Exception:  # noqa: BLE001
            provided = False
        env = environment_levels(study, elements, launch_provided=provided)
        qs, sine, rnd, tv = (env.get(k) or {} for k in ("quasi_static", "sine", "random", "tvac"))
        env_profile = {
            "launch_vehicle": lv_label,
            "launch_vehicle_source": lv_source,
            "levels_source": env.get("level_source"),
            "philosophy": env.get("philosophy"),
            "quasi_static_loads": {"axial_g": qs.get("axial_g"), "lateral_g": qs.get("lateral_g"),
                                   **({"note": qs["note"]} if qs.get("note") else {})},
            "random_vibration": {"level_grms": rnd.get("grms"),
                                 "frequency_range_hz": " - ".join(str(x) for x in rnd.get("range_hz") or []),
                                 "duration_s": rnd.get("duration_s_per_axis"), "axes": rnd.get("axes"),
                                 "note": rnd.get("note")},
            "sine_vibration": {"level_g": sine.get("level_g"),
                               "frequency_range_hz": " - ".join(str(x) for x in sine.get("range_hz") or []),
                               "sweep_rate_oct_min": sine.get("sweep_oct_per_min"), "axes": sine.get("axes"),
                               "note": sine.get("note")},
            "thermal_vacuum": {"cycles": tv.get("cycles"), "pressure_mbar": tv.get("pressure_hpa"),
                               "margin_c": tv.get("margin_c"), "note": tv.get("note")},
        }
    except Exception:  # noqa: BLE001
        import logging
        logging.getLogger(__name__).warning("environment levels unavailable for %s", study_id, exc_info=True)
        env_profile = {"note": "Environmental levels unavailable: to be taken from the launch provider"}

    b = get_branding()
    data = {
        "document": "AIT/AIV Test Plan",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "summary": {
            "total_requirements": len(reqs),
            "test_requirements": len(test_reqs),
            "analysis_requirements": len(analysis_reqs),
            "inspection_requirements": len(inspection_reqs),
            "total_components": len(space_components),
            "total_interfaces": len(study_interfaces),
            "unit_tests": len(unit_tests),
            "integration_tests": len(integration_tests),
        },
        "test_cases": test_cases,
        "unit_tests": unit_tests,
        "integration_tests": integration_tests,
        "environmental_profile": env_profile,
        "test_phases": [
            {"phase": "Unit Test", "description": "Individual component functional verification"},
            {"phase": "Integration Test", "description": "Subsystem-level interface and performance verification"},
            {"phase": "System Test", "description": "Full spacecraft functional and environmental testing"},
            {"phase": "Acceptance Test", "description": "Final verification before launch campaign"},
        ],
    }

    if fmt.lower() == "docx":
        from ...services.branding import create_branded_docx
        doc = create_branded_docx("AIT/AIV Test Plan", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Summary", level=1)
        doc.add_paragraph(f"Total requirements: {len(reqs)}")
        doc.add_paragraph(f"Test (T): {len(test_reqs)}  |  Analysis (A): {len(analysis_reqs)}  |  Inspection (I): {len(inspection_reqs)}")
        doc.add_paragraph(f"Components: {len(space_components)}  |  Interfaces: {len(study_interfaces)}")
        doc.add_paragraph(f"Unit tests: {len(unit_tests)}  |  Integration tests: {len(integration_tests)}")

        doc.add_heading("2. Requirement-Level Test Cases", level=1)
        if test_cases:
            t = doc.add_table(rows=1, cols=6, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Test ID"
            t.rows[0].cells[1].text = "Req Code"
            t.rows[0].cells[2].text = "Level"
            t.rows[0].cells[3].text = "Description"
            t.rows[0].cells[4].text = "Pass Criteria"
            t.rows[0].cells[5].text = "Status"
            for tc in test_cases:
                row = t.add_row()
                row.cells[0].text = tc["test_id"]
                row.cells[1].text = tc["requirement_code"]
                row.cells[2].text = tc["level"]
                row.cells[3].text = tc["test_description"]
                row.cells[4].text = tc["pass_criteria"]
                row.cells[5].text = tc["status"]
        else:
            doc.add_paragraph("No test-verified requirements defined.")

        doc.add_heading("3. Unit Tests (per Component)", level=1)
        if unit_tests:
            for ut in unit_tests:
                doc.add_heading(f"{ut['test_id']}: {ut['component']}", level=2)
                doc.add_paragraph(f"Subsystem: {ut['subsystem']}")
                doc.add_paragraph(f"Description: {ut['test_description']}")
                doc.add_paragraph(f"Pass criteria: {ut['pass_criteria']}")
                if ut["checks"]:
                    doc.add_paragraph("Specific checks:")
                    for chk in ut["checks"]:
                        doc.add_paragraph(chk, style="List Bullet")
        else:
            doc.add_paragraph("No space segment components defined for unit testing.")

        doc.add_heading("4. Integration Test Matrix", level=1)
        if integration_tests:
            t = doc.add_table(rows=1, cols=5, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Test ID"
            t.rows[0].cells[1].text = "Source"
            t.rows[0].cells[2].text = "Target"
            t.rows[0].cells[3].text = "Interface Type"
            t.rows[0].cells[4].text = "Description"
            for it in integration_tests:
                row = t.add_row()
                row.cells[0].text = it["test_id"]
                row.cells[1].text = it["source"]
                row.cells[2].text = it["target"]
                row.cells[3].text = it["interface_type"]
                row.cells[4].text = it["test_description"]
        else:
            doc.add_paragraph("No interfaces defined for integration testing.")

        doc.add_heading("5. Environmental Test Profile", level=1)
        if env_profile.get("note"):
            doc.add_paragraph(env_profile["note"])
        if env_profile.get("launch_vehicle"):
            doc.add_paragraph(f"Launch vehicle: {env_profile['launch_vehicle']} "
                              f"(from {env_profile.get('launch_vehicle_source', 'the study')})")
            if env_profile.get("levels_source"):
                doc.add_paragraph(f"Levels: {env_profile['levels_source']}")

        if env_profile.get("philosophy"):
            doc.add_paragraph(f"Test philosophy: {env_profile['philosophy']}")

        def _v(v, unit=""):
            return "from the launch provider" if v in (None, "") else f"{v} {unit}".strip()

        qsl = env_profile.get("quasi_static_loads", {})
        if qsl:
            doc.add_heading("Quasi-Static Loads", level=2)
            doc.add_paragraph(f"Axial: {_v(qsl.get('axial_g'), 'g')}")
            doc.add_paragraph(f"Lateral: {_v(qsl.get('lateral_g'), 'g')}")
            if qsl.get("note"):
                doc.add_paragraph(str(qsl["note"]))

        rv = env_profile.get("random_vibration")
        if rv:
            doc.add_heading("Random Vibration", level=2)
            doc.add_paragraph(f"Level: {_v(rv.get('level_grms'), 'grms')}")
            doc.add_paragraph(f"Frequency range: {_v(rv.get('frequency_range_hz'), 'Hz')}")
            doc.add_paragraph(f"Duration: {_v(rv.get('duration_s'), 's')} per axis, {rv.get('axes') or 3} axes")
            if rv.get("note"):
                doc.add_paragraph(str(rv["note"]))

        sv = env_profile.get("sine_vibration")
        if sv:
            doc.add_heading("Sine Vibration", level=2)
            doc.add_paragraph(f"Level: {_v(sv.get('level_g'), 'g')}, {_v(sv.get('frequency_range_hz'), 'Hz')}")
            doc.add_paragraph(f"Sweep rate: {_v(sv.get('sweep_rate_oct_min'), 'oct/min')}")
            if sv.get("note"):
                doc.add_paragraph(str(sv["note"]))

        tvac = env_profile.get("thermal_vacuum")
        if tvac:
            doc.add_heading("Thermal Vacuum", level=2)
            t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Parameter"
            t.rows[0].cells[1].text = "Value"
            for label, key, unit in [
                ("Cycles", "cycles", ""),
                ("Pressure", "pressure_mbar", "mbar"),
                ("Margin on the predicted extremes", "margin_c", "C"),
                ("Note", "note", ""),
            ]:
                if tvac.get(key) not in (None, ""):
                    row = t.add_row()
                    row.cells[0].text = label
                    row.cells[1].text = f"{tvac[key]} {unit}".strip()

        doc.add_heading("6. Test Phases", level=1)
        for phase in data["test_phases"]:
            doc.add_paragraph(f"{phase['phase']}: {phase['description']}", style="List Bullet")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="Test_Plan_{study_id}.docx"'},
        )

    if fmt.lower() == "xlsx":
        from ...services.branding import create_branded_xlsx
        wb = create_branded_xlsx(f"AIT/AIV Test Plan — Study {study_id}")
        if wb is None:
            raise HTTPException(status_code=500, detail="openpyxl not available")

        ws = wb.create_sheet("Test Cases")
        headers = ["Test ID", "Req Code", "Req Text", "Level", "Description", "Pass Criteria", "Type", "Status"]
        ws.append(headers)
        from openpyxl.styles import Font as XlFont
        for cell in ws[1]:
            cell.font = XlFont(bold=True)
        for tc in test_cases:
            ws.append([
                tc["test_id"], tc["requirement_code"], tc["requirement_text"],
                tc["level"], tc["test_description"], tc["pass_criteria"],
                tc["test_type"], tc["status"],
            ])
        for col in ws.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

        # Unit tests sheet
        ws_ut = wb.create_sheet("Unit Tests")
        ws_ut.append(["Test ID", "Component", "Subsystem", "Description", "Pass Criteria", "Checks"])
        for cell in ws_ut[1]:
            cell.font = XlFont(bold=True)
        for ut in unit_tests:
            ws_ut.append([
                ut["test_id"], ut["component"], ut["subsystem"],
                ut["test_description"], ut["pass_criteria"],
                "; ".join(ut["checks"]),
            ])
        for col in ws_ut.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=10)
            ws_ut.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

        # Integration tests sheet
        ws_it = wb.create_sheet("Integration Tests")
        ws_it.append(["Test ID", "Source", "Target", "Interface Type", "Description", "Pass Criteria"])
        for cell in ws_it[1]:
            cell.font = XlFont(bold=True)
        for it in integration_tests:
            ws_it.append([
                it["test_id"], it["source"], it["target"],
                it["interface_type"], it["test_description"], it["pass_criteria"],
            ])
        for col in ws_it.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=10)
            ws_it.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

        ws2 = wb.create_sheet("Summary")
        ws2.append(["Metric", "Count"])
        ws2.append(["Total requirements", len(reqs)])
        ws2.append(["Test (T)", len(test_reqs)])
        ws2.append(["Analysis (A)", len(analysis_reqs)])
        ws2.append(["Inspection (I)", len(inspection_reqs)])
        ws2.append(["Components", len(space_components)])
        ws2.append(["Interfaces", len(study_interfaces)])
        ws2.append(["Unit tests", len(unit_tests)])
        ws2.append(["Integration tests", len(integration_tests)])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="Test_Plan_{study_id}.xlsx"'},
        )

    return JSONResponse(content=data)
