"""SEMP / ECSS diagram models (design rules §3). Mounted under ``/api``.

    GET /studies/{sid}/diagrams                 catalogue: every diagram, the gates that expect it,
                                                its gap count and completeness (?gate=pdr filters to the
                                                diagrams the gate of the study's profile expects)
    GET /studies/{sid}/diagrams/{kind}          the diagram model (nodes, edges, groups, legend,
                                                provenance per item, gaps, table alternative)
                                                ?level=system|unit &focus=<subsystem id> &types=power,data
                                                &view=functions (the functional N²); trade_matrix: focus=<trade id>
    GET /studies/{sid}/diagrams/{kind}/svg      the same model drawn as SVG (?lang=fr, ?download=1)
    GET /studies/{sid}/diagrams/{kind}/png      … as PNG (the image the docx exports embed)
    GET /studies/{sid}/diagrams-document.docx   every diagram with its gaps and data table (?set=semp|ird|se|all)

Read-only: the diagrams never change the model. The React view and the docx exporters draw
the same model, so the screen and the documents show the same picture.
"""
from __future__ import annotations


from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from ..services import diagrams as dg

router = APIRouter()


async def _data(study_id: str) -> dg.DiagramData:
    from .studies import get_study_store
    d = await dg.load(study_id)
    if get_study_store().get(study_id) is None and not d.elements:
        raise HTTPException(404, f"Study {study_id} not found")
    return d


def _covers(study, gate: str) -> list[str]:
    """Canonical gates a profile gate covers (pdr → [srr, pdr] in the ESA IOD profile)."""
    try:
        from ..services import gate_profiles as gp
        from .gates import study_profile
        if study is not None:
            for pg in study_profile(study).get("gates") or []:
                if pg["id"] == gate:
                    return list(pg.get("covers") or [gate])
        canon = (gp.load().get("legacy_gate_ids") or {}).get(gate, gate)
        return [canon]
    except Exception:  # noqa: BLE001
        return [gate]


@router.get("/studies/{study_id}/diagrams")
async def diagram_catalogue(study_id: str, gate: str | None = Query(None)) -> dict:
    d = await _data(study_id)
    covers = _covers(d.study, gate) if gate else None
    return {"study_id": study_id, "gate": gate, "covers": covers, "groups": dg.GROUPS,
            "diagrams": dg.catalogue(d, covers), "warnings": d.warnings}


def _kind_or_404(kind: str) -> None:
    if kind not in dg.KINDS or dg.KINDS[kind]["fn"] is None:
        raise HTTPException(404, f"Unknown diagram {kind!r}; one of {[k for k, v in dg.KINDS.items() if v['fn']]}")


@router.get("/studies/{study_id}/diagrams/{kind}")
async def diagram_model(study_id: str, kind: str, level: str | None = Query(None), focus: str | None = Query(None),
                        types: str | None = Query(None), view: str | None = Query(None)) -> dict:
    _kind_or_404(kind)
    d = await _data(study_id)
    return dg.build(kind, d, level=level, focus=focus, types=types, view=view)


@router.get("/studies/{study_id}/diagrams/{kind}/svg")
async def diagram_svg(study_id: str, kind: str, lang: str = Query("en"), level: str | None = Query(None),
                      focus: str | None = Query(None), types: str | None = Query(None),
                      download: bool = Query(False), view: str | None = Query(None)) -> Response:
    from ..services.diagrams.render import to_svg
    _kind_or_404(kind)
    d = await _data(study_id)
    svg = to_svg(dg.build(kind, d, level=level, focus=focus, types=types, view=view), lang=lang)
    headers = {"Content-Disposition": f'attachment; filename="{kind}_{study_id}.svg"'} if download else {}
    return Response(svg, media_type="image/svg+xml", headers=headers)


@router.get("/studies/{study_id}/diagrams/{kind}/png")
async def diagram_png(study_id: str, kind: str, lang: str = Query("en"), level: str | None = Query(None),
                      focus: str | None = Query(None), types: str | None = Query(None),
                      download: bool = Query(False), view: str | None = Query(None)) -> Response:
    from ..services.diagrams.render import to_png
    _kind_or_404(kind)
    d = await _data(study_id)
    png = to_png(dg.build(kind, d, level=level, focus=focus, types=types, view=view), lang=lang)
    headers = {"Content-Disposition": f'attachment; filename="{kind}_{study_id}.png"'} if download else {}
    return Response(png, media_type="image/png", headers=headers)


@router.get("/studies/{study_id}/diagrams-document.docx")
async def diagram_document(study_id: str, set: str = Query("all", pattern="^(semp|ird|se|all)$"),
                           lang: str = Query("en")) -> Response:
    from ..services.diagrams.render import diagrams_docx
    d = await _data(study_id)
    name = getattr(d.study, "name", None) or study_id
    data = diagrams_docx(d, dg.DOCUMENT_SETS[set], study_name=name, lang=lang)
    return Response(content=data,
                             media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             headers={"Content-Disposition": f'attachment; filename="SpaceCDF_Diagrams_{set}_{study_id}.docx"'})
