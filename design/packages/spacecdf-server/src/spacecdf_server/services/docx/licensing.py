"""SpaceCDF Word document family: licensing pack document (W5.04 / W5.06).

``pack_docx(sx, *, gate, lang)`` is the review-pack hook ``hook:licensing``
(``documents/Licensing_status.docx``): the filing tracker with its start-by dates, then one
summary row per study-linked licensing document (``services/licensing_docs.py``) with the inputs
it still needs and the facts to be confirmed. The full documents come from
``POST /api/exports/regulatory/{kind}/{study_id}``. Owner: agent L.
"""
from __future__ import annotations

from typing import Any


def licensing_summary_model(sx: Any) -> dict:
    """The status document model extended with a section per licensing document."""
    from .. import licensing_docs as ld
    model = ld.status(sx)
    rows = []
    for kind in ld.KINDS:
        if kind == "status":
            continue
        try:
            out = ld.GENERATORS[kind](sx)
        except Exception as exc:  # noqa: BLE001 — one broken generator must not break the pack
            rows.append([ld.TITLES[kind][0], ld.TITLES[kind][1], "error", f"{type(exc).__name__}: {exc}"])
            continue
        docs = out if isinstance(out, list) else [out]
        opens = sorted({o for d in docs for o in d.get("open_items") or []})
        rows.append([ld.TITLES[kind][0] + (f" (x{len(docs)})" if len(docs) > 1 else ""), ld.TITLES[kind][1],
                     str(len(opens)), "; ".join(o.split(": ", 1)[-1] for o in opens[:8]) + (" ..." if len(opens) > 8 else "")])
    model["sections"].append(ld._sec("2", "Documents generated from the study", table={
        "columns": ["Document", "Authority", "Open inputs", "Inputs still needed"], "rows": rows},
        paragraphs=["Each document is generated from the study with POST /api/exports/regulatory/{kind}/{study}; "
                    "the inputs still needed are entered in the Licensing tab."]))
    d = (sx.licensing or {}).get("disposal") or {}
    ws = d.get("lifetime_with_sail_y") or {}
    if ws:
        model["sections"].append(ld._sec("3", "Disposal (debris mitigation plan)", [
            ld._row("Lifetime with the sail (strong / nominal / weak cycle)",
                    f"{ws.get('strong')} / {ws.get('nominal')} / {ws.get('weak')} y"),
            ld._row("Disposal reliability", d.get("disposal_reliability")),
            ld._row("ISED conditions met", "yes" if d.get("compliant") else "no")]))
    model["title"] = "Spectrum and licensing: status and documents"
    return model


def pack_docx(sx: Any, *, gate: str, lang: str) -> bytes | None:
    from .regulatory import render_regulatory_docx
    if not (sx.licensing or {}).get("filings"):
        return None
    return render_regulatory_docx(licensing_summary_model(sx))
