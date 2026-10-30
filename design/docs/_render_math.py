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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CACHE_DIR = Path(__file__).parent / "assets" / "figures" / "_math"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Body text in the PDF is 10.5pt Calibri.  Math is rendered in Computer
# Modern which is visually slightly tighter; we pick sizes that read at the
# *same* x-height as the surrounding prose.
# Bump when the output of an unchanged expression changes, to invalidate the cache.
RENDER_VERSION = 3

INLINE_FONTSIZE = 11.0    # pt — single line, sits on the baseline of body text
DISPLAY_FONTSIZE = 12.5    # pt — display equations stand off, but not overpowering

plt.rcParams.update({
    "mathtext.fontset": "cm",          # Computer Modern — the textbook standard
    "mathtext.default": "rm",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "savefig.transparent": True,
})


# ---- Rewrites: LaTeX that matplotlib mathtext does not understand --------
#
# mathtext covers most textbook maths but not every LaTeX/amsmath macro.
# Simple synonyms are rewritten here; constructs with no mathtext equivalent
# (amsmath matrices, \underbrace, ...) fall through to the LaTeX backend.

_REWRITES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\\ge(?![A-Za-z])"), r"\\geq"),
    (re.compile(r"\\le(?![A-Za-z])"), r"\\leq"),
    (re.compile(r"\\ne(?![A-Za-z])"), r"\\neq"),
    (re.compile(r"\\[td]frac(?![A-Za-z])"), r"\\frac"),
    # \big( \Big[ \bigl\{ ... — mathtext has no fixed-size delimiters;
    # the plain delimiter reads correctly at body size.
    (re.compile(r"\\[Bb]igg?[lrm]?(?![A-Za-z])\s*"), ""),
    # Non-breaking / narrow spaces typed into the source (French "5 °C").
    (re.compile("[\u00a0\u202f]"), r"\\ "),
    # Computer Modern has no U+00B0; mathtext falls back to an "fl" glyph.
    (re.compile("°"), r"^\\circ"),
]


def normalise(expr: str) -> str:
    """Rewrite *expr* into the dialect matplotlib mathtext accepts."""
    expr = " ".join(expr.split())          # display maths may span lines
    for pat, rep in _REWRITES:
        expr = pat.sub(rep, expr)
    return expr


_PARSER = None


def mathtext_ok(expr: str) -> tuple[bool, str]:
    """Return (True, "") when mathtext can typeset *expr* (already normalised)."""
    global _PARSER
    if _PARSER is None:
        from matplotlib.mathtext import MathTextParser
        _PARSER = MathTextParser("path")
    try:
        _PARSER.parse(f"${expr}$", 72)
        return True, ""
    except Exception as exc:                # pyparsing / ValueError
        return False, str(exc).splitlines()[0][:120]


# ---- LaTeX backend (pdflatex + pdftocairo) for what mathtext cannot do -----

_TEX = r"""\documentclass[border=0.5pt]{standalone}
\usepackage{fix-cm}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,xcolor}
\definecolor{ink}{HTML}{2D2D2C}
%% Upright Latin letters, matching mathtext.default = "rm" used for the rest
%% of the book (Greek stays italic in both).
\makeatletter
\def\rm@letters#1#2{\@tempcnta=#1\relax
  \loop\mathcode\@tempcnta=\numexpr"7000+\@tempcnta\relax
  \advance\@tempcnta\@ne\ifnum\@tempcnta<#2\repeat}
\AtBeginDocument{\rm@letters{65}{91}\rm@letters{97}{123}}
\makeatother
\begin{document}
\fontsize{%(size)s}{%(lead)s}\selectfont\color{ink}$%(style)s %(expr)s$
\end{document}
"""


def latex_available() -> bool:
    return bool(shutil.which("pdflatex") and shutil.which("pdftocairo"))


def _render_latex(expr: str, *, display: bool, fontsize: float, out: Path) -> bool:
    """Typeset *expr* with real LaTeX and write a pt-sized SVG to *out*."""
    if not latex_available():
        return False
    src = _TEX % {
        "size": fontsize, "lead": round(fontsize * 1.2, 2),
        "style": r"\displaystyle" if display else r"\textstyle",
        "expr": expr.replace("°", r"^\circ"),
    }
    with tempfile.TemporaryDirectory(prefix="rmath_") as tmp:
        t = Path(tmp)
        (t / "m.tex").write_text(src, encoding="utf-8")
        r = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "m.tex"],
            cwd=t, capture_output=True, timeout=60)
        if r.returncode != 0 or not (t / "m.pdf").exists():
            return False
        r = subprocess.run(["pdftocairo", "-svg", "m.pdf", "m.svg"],
                           cwd=t, capture_output=True, timeout=60)
        if r.returncode != 0:
            return False
        svg = (t / "m.svg").read_text(encoding="utf-8")
    # pdftocairo writes unitless width/height in PDF points; unitless means
    # CSS px to WeasyPrint, so make the unit explicit (as matplotlib does).
    svg = re.sub(r'(<svg[^>]*?\bwidth=")([0-9.]+)(")', r"\g<1>\g<2>pt\g<3>", svg, count=1)
    svg = re.sub(r'(<svg[^>]*?\bheight=")([0-9.]+)(")', r"\g<1>\g<2>pt\g<3>", svg, count=1)
    out.write_text(svg, encoding="utf-8")
    return True


# ---- Pure-matplotlib fallback for amsmath constructs (no TeX needed) -------
#
# Used only when mathtext rejects an expression and no LaTeX is installed:
#   \underbrace{X}_{T} / \overbrace{X}^{T}  ->  \underset{T}{X} / \overset{T}{X}
#   \begin{bmatrix|pmatrix|vmatrix|Bmatrix|matrix} ... \end{...}
#        -> laid out cell by cell, delimiters drawn as lines.

_MATRIX_ENV = re.compile(
    r"\\begin\{([bpvBV]?matrix)\}(.*?)\\end\{\1\}", re.S)
_BRACE_CMD = re.compile(r"\\(under|over)brace\s*(?=\{)")


def _group(s: str, i: int) -> int:
    """Index just past the balanced {...} group starting at s[i] == '{'."""
    depth = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == "\\":
            continue
        if c == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif c == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return j + 1
    raise ValueError("unbalanced braces")


def _rewrite_braces(expr: str) -> str:
    """\\underbrace{X}_{T} -> \\underset{T}{X} (and over/^ likewise)."""
    while True:
        m = _BRACE_CMD.search(expr)
        if not m:
            return expr
        kind = m.group(1)
        a = m.end()
        b = _group(expr, a)
        body = expr[a:b]
        rest = expr[b:]
        lab = ""
        mm = re.match(r"\s*([_^])\s*", rest)
        if mm and mm.group(1) == ("_" if kind == "under" else "^"):
            k = mm.end()
            if rest[k:k + 1] == "{":
                e = _group(rest, k)
                lab, rest = rest[k:e], rest[e:]
            else:
                lab, rest = "{" + rest[k:k + 1] + "}", rest[k + 1:]
        cmd = r"\underset" if kind == "under" else r"\overset"
        expr = expr[:m.start()] + (f"{cmd}{lab}{body}" if lab else body) + rest


def _fallback_segments(expr: str):
    """Split into [('t', mathtext) | ('m', env, rows)] or None if unusable."""
    try:
        expr = _rewrite_braces(normalise(expr))
    except ValueError:
        return None
    segs, pos = [], 0
    for m in _MATRIX_ENV.finditer(expr):
        if expr[pos:m.start()].strip():
            segs.append(("t", expr[pos:m.start()]))
        rows = [[c.strip() for c in r.split("&")]
                for r in re.split(r"\\\\", m.group(2)) if r.strip()]
        segs.append(("m", m.group(1), rows))
        pos = m.end()
    if expr[pos:].strip():
        segs.append(("t", expr[pos:]))
    for s in segs:
        cells = [s[1]] if s[0] == "t" else [c or "{}" for r in s[2] for c in r]
        if not all(mathtext_ok(c)[0] for c in cells):
            return None
    return segs


def _render_fallback(expr: str, *, fontsize: float, out: Path) -> bool:
    segs = _fallback_segments(expr)
    if segs is None:
        return False
    ink = "#2d2d2c"
    W, H = 12.0, 4.0                               # scratch canvas, inches
    fig = plt.figure(figsize=(W, H))
    try:
        r = fig.canvas.get_renderer()
        dpi = fig.dpi
        # Positions are worked out in inches and placed in figure fractions
        # (dpi_scale_trans does not survive savefig's dpi change for SVG).
        tr = fig.transFigure
        pt = fontsize / 72.0                       # 1 em in inches

        def _put(tex, x, y):
            t = fig.text(x / W, y / H, f"${tex}$", fontsize=fontsize,
                         color=ink, transform=tr, va="baseline", ha="left")
            bb = t.get_window_extent(r)
            return t, bb.width / dpi, (bb.y1 / dpi - y), (y - bb.y0 / dpi)

        x, base = 0.2, 2.0                         # inches; baseline of line
        for s in segs:
            if s[0] == "t":
                _, w, _, _ = _put(s[1], x, base)
                x += w + 0.15 * pt
                continue
            env, rows = s[1], s[2]
            ncol = max(len(rw) for rw in rows)
            rows = [rw + [""] * (ncol - len(rw)) for rw in rows]
            # measure every cell
            meas = [[_put(c or "{}", 0, 0) for c in rw] for rw in rows]
            for rw in meas:
                for t, *_ in rw:
                    t.remove()
            colw = [max(meas[i][j][1] for i in range(len(rows)))
                    for j in range(ncol)]
            asc = [max(m[2] for m in rw) for rw in meas]
            desc = [max(m[3] for m in rw) for rw in meas]
            gap_r, gap_c = 0.35 * pt, 0.9 * pt
            height = sum(asc) + sum(desc) + gap_r * (len(rows) - 1)
            axis = base + 0.25 * pt                # math axis above baseline
            top = axis + height / 2
            delim = {"bmatrix": "[]", "pmatrix": "()", "vmatrix": "||",
                     "Vmatrix": "‖‖", "Bmatrix": "{}"}.get(env, "")
            pad = 0.25 * pt
            x0 = x + (pad if delim else 0)
            y = top
            for i, rw in enumerate(rows):
                y -= asc[i]
                cx = x0 + pad
                for j, c in enumerate(rw):
                    t, w, _, _ = _put(c or "{}", cx + (colw[j] - meas[i][j][1]) / 2, y)
                    cx += colw[j] + gap_c
                y -= desc[i] + gap_r
            inner = sum(colw) + gap_c * (ncol - 1) + 2 * pad
            yb, yt = top - height - 0.1 * pt, top + 0.1 * pt
            xl, xr = x0, x0 + inner
            lw = max(0.6, fontsize / 16)
            def _line(xs, ys):
                import numpy as np
                xs = np.asarray(xs, float) / W
                ys = np.asarray(ys, float) / H
                fig.add_artist(plt.Line2D(xs, ys, transform=tr, color=ink,
                                          lw=lw, solid_capstyle="butt"))
            arm = 0.3 * pt
            if delim == "[]":
                _line([xl + arm, xl, xl, xl + arm], [yt, yt, yb, yb])
                _line([xr - arm, xr, xr, xr - arm], [yt, yt, yb, yb])
            elif delim in ("||", "‖‖"):
                for off in ((0,) if delim == "||" else (0, 0.12 * pt)):
                    _line([xl + off] * 2, [yb, yt]); _line([xr - off] * 2, [yb, yt])
            elif delim in ("()", "{}"):
                import numpy as np
                th = np.linspace(-1, 1, 40)
                ym, hh = (yt + yb) / 2, (yt - yb) / 2
                bulge = 0.3 * pt
                _line(xl + bulge * th ** 2, ym + hh * th)
                _line(xr - bulge * th ** 2, ym + hh * th)
            x = xr + (pad if delim else 0) + 0.15 * pt
        fig.savefig(out, format="svg")
    finally:
        plt.close(fig)
    return True


def backend_for(expr: str) -> str:
    """'mathtext', 'latex', 'fallback' or 'fail' — the backend _render() uses."""
    norm = normalise(expr)
    if mathtext_ok(norm)[0]:
        return "mathtext"
    if latex_available():
        return "latex"
    return "fallback" if _fallback_segments(expr) is not None else "fail"


# Stacked limits need more leading than mathtext gives a second line.
_BIG_OP = re.compile(r"\\(sum|prod|int|oint|coprod|bigcup|bigcap)(?![A-Za-z])")


def _render(expr: str, *, display: bool) -> Path:
    """Render a math expression to a cached transparent SVG."""
    fontsize = DISPLAY_FONTSIZE if display else INLINE_FONTSIZE
    norm = normalise(expr)
    ok, _ = mathtext_ok(norm)
    backend = "mathtext" if ok else "latex"
    legacy = expr.replace("°", r"^\circ")
    if ok and norm == legacy:
        # Unchanged by the U1 rewrites: keep the pre-U1 cache key so the
        # committed SVG cache stays valid.
        seed = f"svg::{display}::{fontsize}::{legacy}"
    else:
        seed = (f"svg::{RENDER_VERSION}::{backend}::{display}::{fontsize}::"
                f"{expr if display else norm}")
    key = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    out = CACHE_DIR / f"m_{key}.svg"
    if out.exists():
        return out

    if ok:
        # A display equation the author broke over several source lines
        # ("x = a + b \n  = 42") keeps its breaks, provided each line is
        # valid on its own; otherwise it is set as one line.
        text, kw = f"${norm}$", {}
        lines = [normalise(ln) for ln in expr.strip().split("\n") if ln.strip()]
        if (display and len(lines) > 1 and not _BIG_OP.search(norm)
                and all(mathtext_ok(ln)[0] for ln in lines)):
            text = "\n".join(f"${ln}$" for ln in lines)
            kw = {"multialignment": "left", "linespacing": 1.6}
        fig = plt.figure(figsize=(0.01, 0.01))
        try:
            fig.text(0.0, 0.0, text, fontsize=fontsize, color="#2d2d2c", **kw)
            fig.savefig(out, format="svg")
        finally:
            plt.close(fig)
        return out

    if _render_latex(" ".join(expr.split()), display=display,
                     fontsize=fontsize, out=out):
        return out

    # No TeX on this machine: lay the amsmath construct out with mathtext.
    # Cached under its own key so a later TeX-equipped build upgrades it.
    fb = CACHE_DIR / ("m_" + hashlib.sha1(
        (seed + "::fallback").encode("utf-8")).hexdigest()[:16] + ".svg")
    if fb.exists() or _render_fallback(expr, fontsize=fontsize, out=fb):
        return fb

    # Neither backend could typeset it — emit a red monospace placeholder so
    # the document still builds and the failure is visible to the editor.
    # It is written under an "e_" name and never served from the cache, so
    # the next build retries once the source (or this renderer) is fixed.
    print(f"  math FAILED: {expr!r}", file=sys.stderr)
    out = CACHE_DIR / f"e_{key}.svg"
    fig = plt.figure(figsize=(0.01, 0.01))
    try:
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
# "$\pm$5 °C": a lone macro whose closing "$" is followed by a digit.  The
# currency guard "(?![0-9])" above would otherwise pair the *second* "$"
# with the next one ("$5 °C, Acceptance $") and set prose as maths.
_MACRO_DIGIT = re.compile(r"(?<![\\$])\$(\\[A-Za-z]+)\$(?=[0-9])")
# Fill-in-the-blank formulas written as several fragments around a "_____"
# blank, e.g. "$2\pi\sqrt{$ _____ $^3/\mu}$": each piece alone has
# unbalanced braces.  Glue them back into one expression with a math blank.
_SPLIT_BLANK = re.compile(
    r"(?<![\\$])\$(?!\s)([^\n$]+?)\$([ \t]*_{3,}[ \t]*)\$([^\n$]+?)\$")
_BLANK = r"\,\underline{\qquad}\,"


def _brace_depth(s: str) -> int:
    s = s.replace(r"\{", "").replace(r"\}", "")
    return s.count("{") - s.count("}")


def _join_split_blanks(text: str) -> str:
    def _join(m: re.Match) -> str:
        a, b = m.group(1), m.group(3)
        if _brace_depth(a) > 0 and _brace_depth(a) + _brace_depth(b) == 0:
            return "$" + a + _BLANK + b + "$"
        return m.group(0)
    return _SPLIT_BLANK.sub(_join, text)


def iter_fragments(text: str):
    """Yield (expr, display) for every fragment transform() would render,
    in the same order and with the same pairing rules."""
    out: list[tuple[str, bool]] = []
    transform(text, _collect=out)
    return out


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


def transform(text: str, _collect: list | None = None) -> tuple[str, int, int]:
    n_display = n_inline = 0

    def _emit(expr: str, display: bool) -> str:
        if _collect is not None:
            _collect.append((expr, display))
            return "\x00MATH\x00"            # keep later passes from re-pairing
        path = _render(expr, display=display)
        return _img_tag(path, display=display, alt=expr)

    def _disp(m: re.Match) -> str:
        nonlocal n_display
        expr = m.group(1).strip()
        n_display += 1
        return "\n\n" + _emit(expr, True) + "\n\n"

    text = _DISPLAY.sub(_disp, text)

    def _inl(m: re.Match) -> str:
        nonlocal n_inline
        expr = m.group(1).strip()
        n_inline += 1
        return _emit(expr, False)

    text = _join_split_blanks(text)
    text = _MACRO_DIGIT.sub(_inl, text)
    text = _INLINE.sub(_inl, text)
    # A literal currency "\$" in prose is not a math delimiter; unescape it
    # now that every math fragment has been replaced (Python-Markdown does
    # not treat "\$" as an escape).
    text = text.replace("\\$", "$")

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
