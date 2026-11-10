"""SpaceCDF export family: test_plan.

Test plan (json/docx/xlsx).
Routes (prefix /api/exports): POST /test-plan/{study_id}

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from ..studies import get_study_store

router = APIRouter()

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
    space_components = [e for e in elements if e.get("segment") == "space" and e.get("element_type") == "component"]

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

    # Environmental test profile from launch vehicle
    env_profile: dict = {}
    try:
        from spacecdf_common.physics.structures import launch_loads
        # Try to detect launch vehicle from study notes or elements
        launch_vehicle = "falcon_9"  # default
        if study:
            notes = getattr(study, "notes", "") or ""
            for lv in ["electron", "falcon_9", "falcon_heavy", "vega_c", "ariane_6",
                        "pslv", "soyuz", "h3", "sls", "starship", "new_glenn", "long_march_5"]:
                if lv.replace("_", " ") in notes.lower() or lv in notes.lower():
                    launch_vehicle = lv
                    break

        axial_g, lateral_g = launch_loads(launch_vehicle)
        env_profile = {
            "launch_vehicle": launch_vehicle,
            "quasi_static_loads": {
                "axial_g": axial_g,
                "lateral_g": lateral_g,
            },
            "random_vibration": {
                "level_grms": round(axial_g * 2.35, 1),  # Typical qualification = ~2.35x QSL
                "frequency_range_hz": "20 - 2000",
                "duration_s": 120,
            },
            "sine_vibration": {
                "axial_g": round(axial_g * 1.25, 1),
                "lateral_g": round(lateral_g * 1.25, 1),
                "sweep_rate_oct_min": 2,
                "frequency_range_hz": "5 - 100",
            },
            "shock": {
                "srs_g_at_1000hz": 1500,
                "srs_g_at_3000hz": 3000,
            },
            "thermal_vacuum": {
                "hot_survival_c": 60,
                "cold_survival_c": -40,
                "hot_operational_c": 50,
                "cold_operational_c": -20,
                "cycles": 4,
                "pressure_mbar": 1e-5,
            },
        }
    except Exception:
        env_profile = {
            "note": "Launch loads module not available — using generic profile",
            "quasi_static_loads": {"axial_g": 6.0, "lateral_g": 2.0},
            "thermal_vacuum": {
                "hot_survival_c": 60, "cold_survival_c": -40,
                "hot_operational_c": 50, "cold_operational_c": -20,
                "cycles": 4,
            },
        }

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
            doc.add_paragraph(f"Launch vehicle: {env_profile['launch_vehicle']}")

        qsl = env_profile.get("quasi_static_loads", {})
        if qsl:
            doc.add_heading("Quasi-Static Loads", level=2)
            doc.add_paragraph(f"Axial: {qsl.get('axial_g', 'TBD')} g")
            doc.add_paragraph(f"Lateral: {qsl.get('lateral_g', 'TBD')} g")

        rv = env_profile.get("random_vibration")
        if rv:
            doc.add_heading("Random Vibration", level=2)
            doc.add_paragraph(f"Level: {rv.get('level_grms', 'TBD')} grms")
            doc.add_paragraph(f"Frequency range: {rv.get('frequency_range_hz', 'TBD')}")
            doc.add_paragraph(f"Duration: {rv.get('duration_s', 'TBD')} s per axis")

        sv = env_profile.get("sine_vibration")
        if sv:
            doc.add_heading("Sine Vibration", level=2)
            doc.add_paragraph(f"Axial: {sv.get('axial_g', 'TBD')} g")
            doc.add_paragraph(f"Lateral: {sv.get('lateral_g', 'TBD')} g")
            doc.add_paragraph(f"Sweep rate: {sv.get('sweep_rate_oct_min', 'TBD')} oct/min")

        shock = env_profile.get("shock")
        if shock:
            doc.add_heading("Shock (SRS)", level=2)
            doc.add_paragraph(f"SRS @ 1000 Hz: {shock.get('srs_g_at_1000hz', 'TBD')} g")
            doc.add_paragraph(f"SRS @ 3000 Hz: {shock.get('srs_g_at_3000hz', 'TBD')} g")

        tvac = env_profile.get("thermal_vacuum")
        if tvac:
            doc.add_heading("Thermal Vacuum", level=2)
            t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Parameter"
            t.rows[0].cells[1].text = "Value"
            for label, key, unit in [
                ("Hot survival", "hot_survival_c", "C"),
                ("Cold survival", "cold_survival_c", "C"),
                ("Hot operational", "hot_operational_c", "C"),
                ("Cold operational", "cold_operational_c", "C"),
                ("Cycles", "cycles", ""),
                ("Pressure", "pressure_mbar", "mbar"),
            ]:
                if key in tvac:
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
