"""Optional diagram rendering (SCDF-160 Phase 2c, best effort).

The vendored template carries no Sirius diagrams and the
``capellambse-context-diagrams`` extension is not a dependency, so on a plain
install :func:`render_context_svgs` returns ``{}``.  When the extension is
installed (``pip install capellambse-context-diagrams``) the context diagrams
of the layer root components and every exported component are rendered to
SVG; any failure is swallowed and reported in the ``warnings`` list.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["render_context_svgs", "context_diagrams_available"]


def context_diagrams_available() -> bool:
    try:
        import capellambse_context_diagrams  # noqa: F401
    except Exception:
        return False
    return True


def render_context_svgs(model, *, max_diagrams: int = 20,
                        warnings: list[str] | None = None) -> dict[str, str]:
    """Return ``{diagram_name: svg_text}`` for whatever renders headless here."""
    out: dict[str, str] = {}
    warnings = warnings if warnings is not None else []

    # 1. Diagrams already stored in the .aird (none in the empty template).
    try:
        for diag in list(model.diagrams)[:max_diagrams]:
            try:
                out[diag.name] = str(diag.as_svg)
            except Exception as exc:
                warnings.append(f"diagram {diag.name!r} not rendered: {exc}")
    except Exception as exc:
        warnings.append(f"listing diagrams failed: {exc}")

    # 2. Context diagrams via the optional extension.
    if not context_diagrams_available():
        warnings.append("capellambse-context-diagrams not installed; no context diagrams rendered")
        return out
    candidates: list[Any] = []
    try:
        for layer in (model.la, model.pa):
            candidates.append(layer.root_component)
            candidates.extend(list(layer.all_components)[:max_diagrams])
    except Exception as exc:
        warnings.append(f"collecting components failed: {exc}")
    for obj in candidates[:max_diagrams]:
        try:
            diag = obj.context_diagram
            out[f"context:{obj.name}"] = str(diag.as_svg)
        except Exception as exc:
            warnings.append(f"context diagram for {getattr(obj, 'name', obj)!r} not rendered: {exc}")
    return out
