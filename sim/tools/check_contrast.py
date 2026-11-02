#!/usr/bin/env python3
"""WCAG 2.2 contrast validator for the C2O design-system palette.

Run:  python tools/check_contrast.py            (from sim/, or anywhere)
      python tools/check_contrast.py --tokens path/to/c2o.tokens.json

The colours are read from the one source of truth,
``shared/ui-tokens/c2o.tokens.json`` (the same file that generates the token
block of ``smo_common/ui/design-system.css``); nothing is hard-coded here.
Which tokens are text, which are graphics, which surfaces count and the
floors all come from the JSON's ``$extensions["org.c2o.contrast"]`` block:

  dark   text >= 7:1 (AAA) on surface.0 and surface.1, graphics >= 3:1
  light  text >= 4.5:1 (AA) on surface.0 and surface.1, graphics >= 3:1
  disabled ink is reported for information only (the 40 % treatment never
  carries information on its own: the reason text does).

The table is printed per theme with each token's console CSS variable name
(``--tx3`` ...) beside its token path, and the ratio on every surface.
Exit status 1 if any floor is missed, so it can gate CI. The maths is the
same as ``shared/ui-tokens/build.py`` (which writes the table into the
design-system.css header).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TOKENS = REPO_ROOT / "shared" / "ui-tokens" / "c2o.tokens.json"


def lum(hexstr: str) -> float:
    """Relative luminance (WCAG 2.2) of ``#RRGGBB``."""
    h = hexstr.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a: str, b: str) -> float:
    la, lb = lum(a), lum(b)
    lo, hi = min(la, lb), max(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def load_tokens(path: Path = DEFAULT_TOKENS) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def token_hex(tree: dict, dotted: str) -> str:
    node = tree
    for part in dotted.split("."):
        node = node[part]
    return node["$value"]


def css_names(tokens: dict) -> dict[str, str]:
    """token path -> first console CSS variable (``text.tertiary`` -> ``--tx3``)."""
    m = (tokens.get("$extensions", {}).get("org.c2o.outputs", {})
         .get("console", {}).get("theme", {}))
    out = {}
    for path, names in m.items():
        if isinstance(names, dict):
            names = [names.get("css", "")]
        if names:
            out[path] = names[0]
    return out


def table(tokens: dict, theme: str) -> tuple[list[str], bool]:
    """(printed lines, all floors met) for one theme."""
    spec = tokens["$extensions"]["org.c2o.contrast"][theme]
    tree = tokens["theme"][theme]
    names = css_names(tokens)
    surfaces = [(p, token_hex(tree, p)) for p in spec["surfaces"]]
    primary = spec.get("primary", 2)
    floor = float(spec["textFloor"])
    lines = [f"\n{theme.upper()}  (text floor {floor:g}:1 on "
             f"{' and '.join(names.get(p, p) for p, _ in surfaces[:primary])}; "
             f"graphics floor 3:1)"]
    hdr = "  {:8} {:18} {:9} floor " + " ".join(
        f"{names.get(p, p):>6}" for p, _ in surfaces)
    lines.append(hdr.format("token", "path", "hex"))
    ok = True
    for group, fl in (("text", floor), ("graphics", 3.0), ("disabled", None)):
        for p in spec.get(group, []):
            hx = token_hex(tree, p)
            rr = [ratio(hx, sv) for _, sv in surfaces]
            checked = rr[:primary]
            if fl is None:
                verdict = "info (40 % treatment)"
                shown = "  -- "
            else:
                good = all(x >= fl for x in checked)
                ok &= good
                verdict = ("PASS" if group == "text" else "PASS graphics") if good else "FAIL"
                shown = f"{fl:>4.1f} "
            lines.append("  {:8} {:18} {:9} {} ".format(names.get(p, "?"), p, hx, shown)
                         + " ".join(f"{x:6.2f}" for x in rr) + f"  {verdict}")
    c = tokens["$extensions"]["org.c2o.contrast"]
    for fg, bg in c.get("onFill", []):
        r = ratio(token_hex(tree, fg), token_hex(tree, bg))
        good = r >= floor
        ok &= good
        lines.append(f"  {names.get(fg, fg)} on {names.get(bg, bg)}: {r:.2f}  "
                     f"{'PASS' if good else 'FAIL'}")
    for fg, bg, fl in c.get("pairs", []):
        r = ratio(token_hex(tree, fg), token_hex(tree, bg))
        good = r >= fl
        ok &= good
        lines.append(f"  {names.get(fg, fg)} on {names.get(bg, bg)}: {r:.2f}  "
                     f"{'PASS' if good else 'FAIL'} (graphics, floor {fl:g})")
    return lines, ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS,
                    help="token file (default: shared/ui-tokens/c2o.tokens.json)")
    a = ap.parse_args(argv)
    tokens = load_tokens(a.tokens)
    ok = True
    for theme in ("dark", "light"):
        lines, good = table(tokens, theme)
        ok &= good
        print("\n".join(lines))
    try:
        src = Path(a.tokens).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        src = str(a.tokens)
    print(f"\nsource: {src}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
