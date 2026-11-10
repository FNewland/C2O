"""SpaceCDF export family: regulatory (W5.04).

Routes (prefix /api/exports):

* ``POST /regulatory/{kind}/{study_id}?fmt=json|docx&lang=en|fr&station=`` — one study-linked
  licensing document: ``rsssa``, ``ised-space``, ``ised-earth`` (one per station: JSON
  ``{"documents": [...]}``, docx: a zip of one .docx per station, or one station with ``station=``),
  ``itu-api``, ``debris``, ``un-registration``, ``export-control``, ``status``.

The documents take their data from ``services.export_context.collect`` (the ``licensing`` section
from ``services/licensing.py``) and their mass and form factor from ``services.rollup``. Owner:
agent L (design/docs/dev/W0_SEAMS.md).
"""
from __future__ import annotations

import io
import re
import zipfile

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()

_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:60] or "doc"


@router.post("/regulatory/{kind}/{study_id}")
async def export_regulatory(
    kind: str,
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
    lang: str = Query(default="en", description="Document language (en; fr headings follow W9)"),
    station: str | None = Query(default=None, description="ised-earth: one station by name"),
):
    """Generate a study-linked licensing document (W5.04)."""
    from ...services import licensing_docs as ld
    from ...services.docx.regulatory import render_regulatory_docx

    if kind not in ld.KINDS:
        raise HTTPException(400, f"Unknown regulatory document {kind!r}. Available: {list(ld.KINDS)}")
    if fmt.lower() not in ("json", "docx"):
        raise HTTPException(422, "fmt must be json or docx")
    try:
        out = await ld.build(kind, study_id, lang=lang)
    except LookupError:
        raise HTTPException(404, f"Study {study_id} not found") from None
    docs = out if isinstance(out, list) else [out]
    if station is not None:
        docs = [d for d in docs if (d.get("key") or {}).get("station") == station]
        if not docs:
            raise HTTPException(404, f"No station {station!r} in study {study_id}")
    if fmt.lower() == "json":
        return JSONResponse(content={"kind": kind, "documents": docs} if isinstance(out, list) and station is None
                            else docs[0])
    if len(docs) == 1:
        d = docs[0]
        name = f"{_slug(kind)}_{_slug(d.get('mission_name') or study_id)}" + (
            f"_{_slug(d['key']['station'])}" if (d.get("key") or {}).get("station") else "")
        return StreamingResponse(io.BytesIO(render_regulatory_docx(d)), media_type=_DOCX,
                                 headers={"Content-Disposition": f'attachment; filename="{name}.docx"'})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for d in docs:
            z.writestr(f"{_slug(kind)}_{_slug((d.get('key') or {}).get('station') or d['title'])}.docx",
                       render_regulatory_docx(d))
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{_slug(kind)}_{study_id}.zip"'})
