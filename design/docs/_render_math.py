#!/usr/bin/env python3
"""Render every LaTeX math fragment in a Markdown document to an SVG and
replace the fragment with an <img> tag.

Why SVG (not PNG)?
    Inline math sits on the body line.  PNGs need either an explicit
    height attribute (which crushes tall expressions like fractions and
    square roots) or a fixed DPI that does not match the printed point
    size.  SVG carries its own intrinsic dimensions in PostScript points,
    so WeasyPrint can place each image at exactly the right size: simple
    variables stay short, fractions get the height they need.

Display math becomes a centred block; inline math becomes a baseline-
aligned glyph.  SVGs are cached under ``docs/assets/figures/_math/`` by
hash so successive builds are fast.

Usage:
    python3 docs/_render_math.py <src.md> <out.md>
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CACHE_DIR = Path(__file__).parent / "assets" / "figures" / "_math"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Body text in the PDF is 10.5pt Calibri.  Math is rendered in Computer
# Modern which is visually slightly tighter; we pick sizes that read at the
# *same* x-height as the surrounding prose.
INLINE_FONTSIZE = 11.0    # pt — single line, sits on the baseline of body text
DISPLAY_FONTSIZE = 12.5    # pt — display equations stand off, but not overpowering

plt.rcParams.update({
    "mathtext.fontset": "cm",          # Computer Modern — the textbook standard
    "mathtext.default": "rm",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "savefig.transparent": True,
})


def _render(expr: str, *, display: bool) -> Path:
    """Render a math expression to a cached transparent SVG."""
    fontsize = DISPLAY_FONTSIZE if display else INLINE_FONTSIZE
    key = hashlib.sha1(
        f"svg::{display}::{fontsize}::{expr}".encode("utf-8")
    ).hexdigest()[:16]
    out = CACHE_DIR / f"m_{key}.svg"
    if out.exists():
        return out

    fig = plt.figure(figsize=(0.01, 0.01))
    try:
        fig.text(0.0, 0.0, f"${expr}$", fontsize=fontsize, color="#2d2d2c")
        fig.savefig(out, format="svg")
    except Exception:
        # Failed to parse — emit a red monospace placeholder so the document
        # still builds and the failure is visible to the editor.
        plt.close(fig)
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0.0, 0.0, expr, fontsize=fontsize, color="#8f001a",
                 family="monospace")
        fig.savefig(out, format="svg")
    finally:
        plt.close(fig)
    return out


# ---- Markdown scanning -----------------------------------------------------

_DISPLAY = re.compile(r"\$\$([^$]+?)\$\$", re.S)
_INLINE = re.compile(
    r"(?<![\\$])\$(?!\s)([^\n$]+?)\$(?![0-9])"
)


def _img_tag(path: Path, *, display: bool, alt: str) -> str:
    # base_url=docs/course/ for the rendering pipeline, so '../assets/...'
    # resolves to docs/assets/...
    rel = "../assets/figures/_math/" + path.name
    cls = "math-display" if display else "math-inline"
    style = (
        "display:block;margin:8pt auto;"
        if display else
        "display:inline;vertical-align:middle;"
    )
    alt_esc = alt.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<img src="{rel}" alt="{alt_esc}" class="{cls}" style="{style}"/>'


def transform(text: str) -> tuple[str, int, int]:
    n_display = n_inline = 0

    def _disp(m: re.Match) -> str:
        nonlocal n_display
        expr = m.group(1).strip()
        path = _render(expr, display=True)
        n_display += 1
        return "\n\n" + _img_tag(path, display=True, alt=expr) + "\n\n"

    text = _DISPLAY.sub(_disp, text)

    def _inl(m: re.Match) -> str:
        nonlocal n_inline
        expr = m.group(1).strip()
        path = _render(expr, display=False)
        n_inline += 1
        return _img_tag(path, display=False, alt=expr)

    text = _INLINE.sub(_inl, text)

    return text, n_display, n_inline


def main(argv):
    if len(argv) != 3:
        print("Usage: render_math.py <in.md> <out.md>", file=sys.stderr)
        return 1
    src = Path(argv[1]); dst = Path(argv[2])
    if not src.exists():
        print(f"Missing source: {src}", file=sys.stderr)
        return 1
    text = src.read_text()
    new, n_d, n_i = transform(text)
    dst.write_text(new)
    print(f"  math rendered: {n_d} display + {n_i} inline ({src.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
