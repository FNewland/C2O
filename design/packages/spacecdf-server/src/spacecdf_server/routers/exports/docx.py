"""SpaceCDF export family: docx.

Word documents from services/docx (MRD, ConOps, VP, TS, IRD, SEMP, RMP, test plan, licensing
documents and review stubs).
Routes (prefix /api/exports): POST /docx/{doc_type}

Since W1.09 (a, b) the requirements, verification items and risks come from the study
collector (``services.export_context``): every requirement, sorted by level then code, with its
code, type, threshold, parent and allocation; ``IR-*`` rows generated from links go to the IRD,
not the TS/VP; the RMP receives the risk register sorted by likelihood x consequence.
``docx_document`` builds the bytes; the review packs (``packs.py``) call it too.

Wave 2: with a study, ``STUDY_DOCS`` are built from the collector: the MRD
(``mrd_kwargs_from_export``), the ConOps (``routers.conops``), the verification plan (W8a,
``generate_verification_plan_docx``), the TS (W4.06) and the IRD (W4.07); ``rsssa``, ``itu_api``,
``copuos``, ``eol`` and ``export`` render the study-linked licensing documents of
``services.licensing_docs`` (W5.04). ``iaru`` and the review stubs keep the legacy path.
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ._common import _read_orbit_params

router = APIRouter()

# --- Word Document Generation ---

@router.post("/docx/{doc_type}")
async def generate_docx(doc_type: str, study_id: str | None = None,
                        lang: str = Query(default="en", description="Document language: en or fr (the TS, IRD, "
                                          "VP, ConOps and licensing documents; the others stay English until W9)")):
    """Generate an editable Word (.docx) document.

    Types: the keys of ``services.docx.DOCX_GENERATORS`` (mrd, conops, vp, ts, ird, semp, rmp,
    testplan, the licensing documents and the srr/pdr/cdr review stubs). With a study, the MRD,
    ConOps, VP, TS, IRD and the licensing documents (rsssa, itu_api, copuos, eol, export) are built
    from the study collector (``STUDY_DOCS``). Returns a downloadable .docx file.
    """
    from ...services.docx import DOCX_GENERATORS
    if doc_type not in DOCX_GENERATORS:
        raise HTTPException(400, f"Unknown doc type: {doc_type}. Available: {list(DOCX_GENERATORS.keys())}")
    filename, docx_bytes = await docx_document(doc_type, study_id, lang=lang)
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


#: collector sections the Word families read
_SECTIONS = ("need", "mission", "elements", "requirements", "verification", "risks")


def requirement_rows_for_docs(sx_requirements: list[dict], elements: list[dict]) -> list[dict]:
    """Requirement dicts for the Word generators: the stored row plus ``parent_code`` and
    ``allocated_to`` (element name). Order as collected (level, then code)."""
    codes = {r.get("id"): (r.get("code") or r.get("id")) for r in sx_requirements}
    names = {e.get("id"): e.get("name") for e in elements}
    out = []
    for r in sx_requirements:
        parent = r.get("parent_id") or r.get("derived_from_requirement_id")
        out.append({**r, "parent_code": codes.get(parent, parent or ""),
                    "allocated_to": names.get(r.get("element_id"), "") if r.get("element_id") else ""})
    return out


#: registry key -> licensing document kind of ``services.licensing_docs`` (W5.04)
LICENSING_KINDS = {"rsssa": "rsssa", "itu_api": "itu-api", "copuos": "un-registration", "eol": "debris",
                   "export": "export-control"}
#: documents built from the study collector when a study is given: type -> sections they read
STUDY_DOCS: dict[str, tuple[str, ...]] = {
    "mrd": ("need", "mission", "requirements", "elements", "stakeholders", "validation"),
    "conops": (),                       # routers.conops collects its own sections
    "vp": ("mission", "requirements", "ait", "schedule"),
    "ts": ("need", "mission", "elements", "requirements", "ait"),
    "ird": ("mission", "elements", "requirements", "links", "electrical"),
    **{k: () for k in LICENSING_KINDS},  # services.licensing_docs.SECTIONS_NEEDED
    "semp": (),                         # wave 3 (3.X3): every section (collected in full)
}


async def study_document(doc_type: str, study_id: str, *, sx=None, lang: str = "en") -> bytes:
    """.docx bytes of a document in ``STUDY_DOCS``, built from ``sx`` (collected here when None or
    when it lacks the sections the document reads)."""
    from ...services.export_context import collect
    lang = "fr" if str(lang or "").lower().startswith("fr") else "en"

    async def need(sections):
        if sx is not None:
            return sx
        return await collect(study_id, lang=lang, sections=list(sections))

    if doc_type == "conops":
        from ...services.docx.conops import generate_conops_from_view
        from ..conops import conops_view
        return generate_conops_from_view(await conops_view(study_id, lang=lang, sx=sx), lang=lang)
    if doc_type == "semp":
        from ...services.docx.semp import generate_semp_from_export
        s = sx if sx is not None else await collect(study_id, lang=lang)
        figs = []
        try:
            from ...services import diagrams as dg
            ddata = await dg.load(study_id)
            figs = [dg.build(k, ddata, **o) for k, o in dg.expand(dg.DOCUMENT_SETS["semp"], ddata)]
        except Exception:  # noqa: BLE001 — the plan still renders without figures
            import logging
            logging.getLogger(__name__).warning("diagrams for the SEMP failed", exc_info=True)
        return generate_semp_from_export(s, lang, figs)
    if doc_type in LICENSING_KINDS:
        from ...services import licensing_docs as ld
        from ...services.docx.regulatory import render_regulatory_docx
        model = ld.GENERATORS[LICENSING_KINDS[doc_type]](await need(ld.SECTIONS_NEEDED))
        return render_regulatory_docx(model[0] if isinstance(model, list) else model)
    s = await need(STUDY_DOCS[doc_type])
    if doc_type == "mrd":
        from ...services.docx.mrd import generate_mrd_docx, mrd_kwargs_from_export
        return generate_mrd_docx(**mrd_kwargs_from_export(s))
    if doc_type == "vp":
        from ...services.docx.vp import generate_verification_plan_docx
        return generate_verification_plan_docx(s, lang)
    if doc_type == "ts":
        from ...services.docx.ts import generate_ts_from_export
        return generate_ts_from_export(s, lang)
    if doc_type == "ird":
        from ...services.docx.ird import generate_ird_from_export
        diagrams = []
        try:
            from ...services import diagrams as dg
            ddata = await dg.load(study_id)
            diagrams = [dg.build(k, ddata, **o) for k, o in dg.expand(dg.DOCUMENT_SETS["ird"], ddata)]
        except Exception:  # noqa: BLE001 — the document still renders without figures
            import logging
            logging.getLogger(__name__).warning("diagrams for the IRD failed", exc_info=True)
        return generate_ird_from_export(s, lang, diagrams=diagrams)
    raise KeyError(doc_type)


async def docx_document(doc_type: str, study_id: str | None, *, sx=None, lang: str = "en") -> tuple[str, bytes]:
    """(file name, .docx bytes) of one Word family for a study. ``sx`` is a ``StudyExport``
    already collected (the packs pass theirs); otherwise the needed sections are collected."""
    from ...services.docx import DOCX_GENERATORS
    from ..studies import get_study_store

    if doc_type not in DOCX_GENERATORS:
        raise KeyError(doc_type)
    name, gen_fn = DOCX_GENERATORS[doc_type]
    if study_id and doc_type in STUDY_DOCS and get_study_store().get(study_id) is not None:
        study_name = get_study_store().get(study_id).name or "study"
        data = await study_document(doc_type, study_id, sx=sx, lang=lang)
        return f"SpaceCDF_{name.replace(' ', '_')}_{study_name.replace(' ', '_')}.docx", data

    # Get study data if available
    study_name = "Unnamed Mission"
    mission_need: dict = {}
    requirements: list = []
    risks: list = []
    verification: list = []
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

            # ── Requirements, verification items and risks from the study collector ──
            if sx is None:
                from ...services.export_context import collect
                try:
                    sx = await collect(study_id, sections=_SECTIONS)
                except LookupError:
                    sx = None
            if sx is not None:
                requirements = requirement_rows_for_docs((sx.requirements or {}).get("items") or [],
                                                         (sx.elements or {}).get("items") or [])
                risks = list((sx.risks or {}).get("items") or [])
                verification = list((sx.verification or {}).get("items") or [])

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
            conops = conops_dict(study)

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
    # TS / VP / review stubs carry the team's requirements; IR-* rows generated from the links
    # belong to the IRD (W1.09a).
    team_reqs = [r for r in requirements if not r.get("generated_interface")]
    data = {
        "mission_need": mission_need,
        "requirements": team_reqs,
        "interface_requirements": [r for r in requirements if r.get("generated_interface")
                                   or r.get("level") == "interface"],
        "risks": risks,
        "verification": verification,
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
            data["diagrams"] = [dg.build(k, ddata, **o) for k, o in dg.expand(dg.DOCUMENT_SETS[doc_type], ddata)]
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
        kwargs["requirements"] = team_reqs
        kwargs["verification_items"] = verification
    elif doc_type in ("ts", "ird", "semp", "rmp", "testplan",
                      "itu_api", "iaru", "rsssa", "export", "copuos", "eol",
                      "srr", "pdr", "cdr"):
        kwargs["data"] = data

    docx_bytes = gen_fn(**kwargs)

    filename = f"SpaceCDF_{name.replace(' ', '_')}_{study_name.replace(' ', '_')}.docx"
    return filename, docx_bytes


def conops_dict(study) -> dict:
    """``study.conops`` (the auto-generated ConOps) as plain data ({} when the study has none).
    Shared with the DID route (routers/ecss.py)."""
    conops: dict = {}
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
    return conops
