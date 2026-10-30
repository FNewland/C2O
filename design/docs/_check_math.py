#!/usr/bin/env python3
"""List every maths fragment in the course books / OER textbook (EN + FR)
and say whether docs/_render_math.py can typeset it.

    python3 docs/_check_math.py            # current renderer
    python3 docs/_check_math.py --legacy   # the pre-U1 behaviour, for comparison
    python3 docs/_check_math.py --all      # also print every OK fragment
    python3 docs/_check_math.py --render   # actually render the LaTeX-backend
                                           # fragments (proves pdflatex works)

Exit status is the number of failing fragments (capped at 100), so it can
gate a build.  Statuses: ``mathtext`` (matplotlib), ``latex`` (pdflatex +
pdftocairo fallback), ``FAIL`` (red placeholder in the PDF).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _render_math as R  # noqa: E402

WORK = HERE.parents[1]          # .../work  (cdf/docs -> cdf -> work)
SOURCES = [
    "drive_course/*.md",
    "drive_mirror/fr/*.md",
    "cdf/docs/oer/chapters/*.md",
    "cdf/docs/oer/fr/chapters/*.md",
    "cdf/docs/orbit_north/week3/*.md",
    "cdf/docs/orbit_north/week3/fr/*.md",
]

# --- the renderer as it was before U1 (regex pairing + raw mathtext) --------
_LEG_INLINE = re.compile(r"(?<![\\$])\$(?!\s)([^\n$]+?)\$(?![0-9])")


def legacy_fragments(text: str):
    out = []
    text = R._DISPLAY.sub(lambda m: out.append((m.group(1).strip(), True)) or "\0", text)
    _LEG_INLINE.sub(lambda m: out.append((m.group(1).strip(), False)) or "\0", text)
    return out


def legacy_status(expr: str) -> str:
    ok, _ = R.mathtext_ok(expr.replace("°", r"^\circ"))
    return "mathtext" if ok else "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()

    seen: dict[tuple[str, bool], set[str]] = {}
    for pat in SOURCES:
        for f in sorted(WORK.glob(pat)):
            text = f.read_text(encoding="utf-8")
            frags = legacy_fragments(text) if a.legacy else R.iter_fragments(text)
            for expr, disp in frags:
                seen.setdefault((expr, disp), set()).add(str(f.relative_to(WORK)))

    counts = {"mathtext": 0, "latex": 0, "FAIL": 0}
    for (expr, disp), files in seen.items():
        if a.legacy:
            st = legacy_status(expr)
        else:
            st = R.backend_for(expr).replace("fail", "FAIL")
            if st == "latex" and a.render:
                p = R._render(expr, display=disp)
                st = "latex" if p.name.startswith("m_") else "FAIL"
        counts[st] += 1
        if a.all or st != "mathtext":
            why = "" if st != "FAIL" else "  -- " + R.mathtext_ok(R.normalise(expr))[1]
            print(f"{st:8s} {'D' if disp else 'I'} {expr!r}{why}")
            print(f"           in: {', '.join(sorted(files))}")
    print(f"\n{'legacy' if a.legacy else 'current'} renderer: {len(seen)} unique "
          f"fragments -- mathtext {counts['mathtext']}, latex {counts['latex']}, "
          f"FAIL {counts['FAIL']}")
    return min(counts["FAIL"], 100)


if __name__ == "__main__":
    sys.exit(main())
