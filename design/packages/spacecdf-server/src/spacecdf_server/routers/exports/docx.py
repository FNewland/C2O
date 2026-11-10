"""SpaceCDF export family: docx.

Word documents from services/docx (MRD, ConOps, VP, TS, IRD, SEMP, RMP, test plan, regulatory and review stubs).
Routes (prefix /api/exports): POST /docx/{doc_type}

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ._common import _read_orbit_params

router = APIRouter()

# --- Word Document Generation ---

@router.post("/docx/{doc_type}")
async def generate_docx(doc_type: str, study_id: str | None = None):
    """Generate an editable Word (.docx) document.

    Available types: mrd, conops, vp
    Returns a downloadable .docx file.
    """
    from ...services.docx import DOCX_GENERATORS
    from ..studies import get_study_store

    if doc_type not in DOCX_GENERATORS:
        raise HTTPException(400, f"Unknown doc type: {doc_type}. Available: {list(DOCX_GENERATORS.keys())}")

    name, gen_fn = DOCX_GENERATORS[doc_type]

    # Get study data if available
    study_name = "Unnamed Mission"
    mission_need: dict = {}
    requirements: list = []
    conops: dict = {}
    orbit_params: dict = {}
    elements: list = []
    interfaces: list = []

    if study_id:
        store = get_study_store()
        study = store.get(study_id)
        if study:
            study_name = study.name

            # ── Full mission_need dict ──
            if hasattr(study, 'mission_need') and study.mission_need:
                mn = study.mission_need
                mission_need = {
                    "problem_statement": getattr(mn, "problem_statement", ""),
                    "operational_context": getattr(mn, "operational_context", ""),
                    "selection_rationale": getattr(mn, "selection_rationale", ""),
                    "conops_summary": getattr(mn, "conops_summary", ""),
                    "objectives": [
                        {
                            "id": getattr(o, "id", ""),
                            "text": o.text,
                            "priority": o.priority.value if hasattr(o.priority, "value") else str(o.priority),
                            "type": o.type.value if hasattr(o.type, "value") else str(getattr(o, "type", "")),
                            "measurable_criterion": getattr(o, "measurable_criterion", ""),
                            "status": getattr(o, "status", "proposed"),
                        }
                        for o in getattr(mn, "objectives", [])
                    ],
                    "stakeholders": [
                        {
                            "name": s.name,
                            "role": s.role.value if hasattr(s.role, "value") else str(getattr(s, "role", "")),
                            "needs": getattr(s, "needs", []),
                            "priority": getattr(s, "priority", "primary"),
                        }
                        for s in getattr(mn, "stakeholders", [])
                    ],
                    "alternatives": [
                        {
                            "id": getattr(a, "id", ""),
                            "name": a.name,
                            "type": a.type.value if hasattr(a.type, "value") else str(getattr(a, "type", "")),
                            "description": getattr(a, "description", ""),
                            "pros": getattr(a, "pros", []),
                            "cons": getattr(a, "cons", []),
                            "feasibility_score": getattr(a, "feasibility_score", 0.0),
                            "decision": a.decision.value if hasattr(a.decision, "value") else str(getattr(a, "decision", "")),
                        }
                        for a in getattr(mn, "alternatives_considered", [])
                    ],
                    "selected_alternative_id": getattr(mn, "selected_alternative_id", None),
                }

            # ── Requirements from the requirements store ──
            try:
                from ..requirements import _requirements
                requirements = [
                    r for r in _requirements.values()
                    if r.get("study_id") == study_id and r.get("status") != "retired"
                ]
            except Exception:
                pass

            # ── Orbit parameters ──
            orbit_params = _read_orbit_params(study)

            # ── Computed orbit values ──
            try:
                from spacecdf_common.physics.orbit import compute_orbit_params
                op = compute_orbit_params(
                    altitude_km=orbit_params["altitude_km"],
                    inclination_deg=orbit_params["inclination_deg"],
                    eccentricity=orbit_params.get("eccentricity", 0.0),
                )
                orbit_params.update({
                    "period_min": round(op.period_min, 2),
                    "velocity_ms": round(op.velocity_ms, 1),
                    "eclipse_fraction": round(op.eclipse_fraction, 3),
                    "eclipse_duration_min": round(getattr(op, "eclipse_duration_min", 0), 2),
                    "orbits_per_day": round(op.orbits_per_day, 1),
                })
            except Exception:
                pass

            # ── ConOps from study ──
            if hasattr(study, 'conops') and study.conops:
                cop = study.conops
                conops = {
                    "phases": [
                        {
                            "name": p.name, "phase_type": p.phase_type.value if hasattr(p.phase_type, "value") else str(p.phase_type),
                            "duration_days": p.duration_days, "description": p.description,
                            "entry_criteria": getattr(p, "entry_criteria", ""),
                            "exit_criteria": getattr(p, "exit_criteria", ""),
                        }
                        for p in getattr(cop, "phases", [])
                    ],
                    "modes": [
                        {
                            "name": m.name, "mode_type": m.mode_type.value if hasattr(m.mode_type, "value") else str(m.mode_type),
                            "description": getattr(m, "description", ""),
                            "power_w": m.power_w, "payload_active": m.payload_active,
                            "data_rate_mbps": m.data_rate_mbps,
                            "pointing_requirement_deg": m.pointing_requirement_deg,
                            "nadir_pointing": m.nadir_pointing,
                            "duty_cycle_percent": m.duty_cycle_percent,
                            "is_critical": m.is_critical,
                        }
                        for m in getattr(cop, "modes", [])
                    ],
                    "ground_stations": [
                        {
                            "name": gs.name,
                            "type": gs.type.value if hasattr(gs.type, "value") else str(gs.type),
                            "latitude_deg": gs.latitude_deg, "longitude_deg": gs.longitude_deg,
                            "antenna_diameter_m": gs.antenna_diameter_m,
                            "frequency_bands": gs.frequency_bands,
                            "contact_time_per_day_min": gs.contact_time_per_day_min,
                        }
                        for gs in getattr(cop, "ground_stations", [])
                    ],
                    "data_pipeline": [
                        {
                            "name": dp.name, "location": dp.location,
                            "description": dp.description, "latency": dp.latency,
                            "data_level": dp.data_level,
                        }
                        for dp in getattr(cop, "data_pipeline", [])
                    ],
                    "autonomy_level": getattr(cop, "autonomy_level", ""),
                    "operations_concept": getattr(cop, "operations_concept", ""),
                    "summary": getattr(cop, "summary", ""),
                }

            # ── Elements from the element store ──
            try:
                from ..elements import _elements, _interfaces
                elements = [
                    e for e in _elements.values()
                    if e.get("study_id") == study_id and not e.get("deleted_at")
                ]
                interfaces = [
                    i for i in _interfaces.values()
                    if not i.get("deleted_at") and i.get("status") != "rejected" and (
                        i.get("study_id") == study_id
                        or i.get("source_element_id") in {e.get("id") for e in elements}
                        or i.get("target_element_id") in {e.get("id") for e in elements}
                    )
                ]
            except Exception:
                pass

    # Build a universal data dict for generators that take (study_name, data)
    data = {
        "mission_need": mission_need,
        "requirements": requirements,
        "orbit": orbit_params,
        "conops": conops,
        "elements": elements,
        "interfaces": interfaces,
    }

    # SEMP / IRD: the same diagram models the Diagrams view draws (services/diagrams)
    if study_id and doc_type in ("semp", "ird"):
        try:
            from ...services import diagrams as dg
            ddata = await dg.load(study_id)
            data["diagrams"] = [dg.build(k, ddata) for k in dg.DOCUMENT_SETS[doc_type]]
        except Exception:  # noqa: BLE001 — the document still renders without figures
            import logging
            logging.getLogger(__name__).warning("diagrams for %s export failed", doc_type, exc_info=True)

    # Generate the document
    kwargs: dict = {"study_name": study_name}
    if doc_type in ("mrd",):
        kwargs["mission_need"] = mission_need
        kwargs["requirements"] = requirements
        kwargs["orbit"] = orbit_params
        kwargs["elements"] = elements
    elif doc_type in ("conops",):
        kwargs["mission_need"] = mission_need
        kwargs["conops"] = conops
        kwargs["orbit"] = orbit_params
        kwargs["elements"] = elements
    elif doc_type in ("vp",):
        kwargs["requirements"] = requirements
    elif doc_type in ("ts", "ird", "semp", "rmp", "testplan",
                      "itu_api", "iaru", "rsssa", "export", "copuos", "eol",
                      "srr", "pdr", "cdr"):
        kwargs["data"] = data

    docx_bytes = gen_fn(**kwargs)

    filename = f"SpaceCDF_{name.replace(' ', '_')}_{study_name.replace(' ', '_')}.docx"
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
