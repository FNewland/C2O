"""SpaceCDF export family: packs.

Review data packs (SRR/PDR/CDR zip and Markdown) built by spacecdf_agents.exporters.docs.
Routes (prefix /api/exports): POST /docs/{study_id}

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from . import _common

router = APIRouter()

@router.post("/docs/{study_id}")
async def export_design_document(
    study_id: str,
    review: str = Query(default="srr", description="Review type: srr, pdr, cdr"),
    fmt: str = Query(default="zip", description="Output format: zip (default) or markdown"),
    lang: str = Query(default="en", description="Document language: en (default) or fr. "
                      "Selects templates/fr/ for the Markdown when present; Word/Excel stay English for now."),
):
    """Generate a design review document from a design study.

    When ``fmt=zip`` (default) streams a zip archive containing Markdown,
    Word, and Excel artefacts. When ``fmt=markdown``, returns the Markdown
    body as JSON for backwards compatibility.

    ``lang`` (i18n packet C0) only picks per-language Jinja templates; no
    French templates exist yet, so output is English either way.
    TODO(i18n C2/K3): add templates/fr/*.md.j2 and a lang-aware
    docx/xlsx generator; then thread ``lang`` through the other export
    routes (docx, launch-icd, rsssa, deorbit, thermal-report, test-plan).
    """
    state, requirements, result = await _common._run_design_for_study(study_id)

    from spacecdf_agents.exporters.docs.generator import DocumentGenerator
    generator = DocumentGenerator()
    review_lower = (review or "srr").lower()
    if review_lower not in ("srr", "pdr", "cdr"):
        review_lower = "srr"

    if fmt.lower() == "markdown":
        doc = generator.generate(state, requirements, result, review_type=review_lower, lang=lang)
        return JSONResponse(content={
            "review_type": review_lower,
            "document_markdown": doc,
            "sections": doc.count("\n## "),
        })

    zip_bytes = generator.generate_bundle(
        state, requirements, result,
        review_type=review_lower,
        study_name=study_id,
        lang=lang,
    )
    filename = f"{review_lower}_export.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
