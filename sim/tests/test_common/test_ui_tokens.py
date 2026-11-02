"""C2O design tokens (shared/ui-tokens) and the shared design-system CSS.

The tokens JSON is the single source of truth; build.py writes the token
block of smo_common/ui/design-system.css and SpaceCDF's tokens.css/tokens.ts.
These tests keep the outputs from drifting, keep SpaceCDF's variable names
stable (its components are built on them), and keep the hand-written CSS
free of literal colours and of the old font stack.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TOKENS_DIR = REPO / "shared" / "ui-tokens"
BUILD = TOKENS_DIR / "build.py"
UI = REPO / "sim/packages/smo-common/src/smo_common/ui"
DS_CSS = UI / "design-system.css"
CDF_CSS = REPO / "design/frontend/src/theme/tokens.css"
CDF_TS = REPO / "design/frontend/src/theme/tokens.ts"


def _build_module():
    sys.dont_write_bytecode = True          # keep shared/ui-tokens free of __pycache__
    spec = importlib.util.spec_from_file_location("c2o_tokens_build", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generated_outputs_are_up_to_date():
    """`build.py --check` fails when someone edits a hex by hand (or edits
    the JSON and forgets to rebuild), and when a contrast floor is missed."""
    r = subprocess.run([sys.executable, str(BUILD), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_both_themes_define_the_same_tokens():
    t = json.loads((TOKENS_DIR / "c2o.tokens.json").read_text(encoding="utf-8"))

    def leaves(node, path=""):
        out = set()
        for k, v in node.items():
            if k.startswith("$"):
                continue
            p = f"{path}.{k}" if path else k
            if isinstance(v, dict) and "$value" in v:
                out.add(p)
            elif isinstance(v, dict):
                out |= leaves(v, p)
        return out

    dark, light = leaves(t["theme"]["dark"]), leaves(t["theme"]["light"])
    assert dark == light, dark ^ light
    # every mapped output name points at a real token
    b = _build_module()
    for target in ("console", "cdf"):
        m = t["$extensions"]["org.c2o.outputs"][target]
        for path in m["theme"]:
            b.get(t["theme"]["dark"], path)
        for path in m["scale"]:
            b.get(t, path)


def test_type_scale_and_geometry_follow_the_brief():
    t = json.loads((TOKENS_DIR / "c2o.tokens.json").read_text(encoding="utf-8"))
    assert [t["size"][k]["$value"] for k in ("label", "body", "value", "title")] == \
        ["12px", "13px", "15px", "20px"]
    assert [t["space"][k]["$value"] for k in "123456"] == \
        ["4px", "8px", "12px", "16px", "24px", "32px"]
    radii = [int(t["radius"][k]["$value"][:-2]) for k in ("sm", "md", "lg")]
    assert radii == [2, 3, 4]
    assert t["motion"]["duration"]["$value"] == "140ms"
    assert t["font"]["sans"]["$value"][0] == "IBM Plex Sans"
    assert t["font"]["mono"]["$value"][0] == "IBM Plex Mono"


def test_contrast_check_catches_a_failing_token():
    b = _build_module()
    t = b.load()
    _, fails = b.contrast_report(t)
    assert fails == []
    bad = copy.deepcopy(t)
    bad["theme"]["dark"]["text"]["tertiary"]["$value"] = "#6A7480"   # ~4:1 on the panel
    _, fails = b.contrast_report(bad)
    assert any("text.tertiary" in f for f in fails), fails


# SpaceCDF's tokens.css/tokens.ts as of 2026-11-01: worker E builds on these
# names. Generated files may ADD names, never drop one.
CDF_CSS_NAMES = """
--font-sans --font-mono --fs-label --fs-body --fs-value --fs-title --lh-text --lh-value
--sp-1 --sp-2 --sp-3 --sp-4 --sp-5 --sp-6 --radius --radius-sm --motion
--surface-0 --surface-1 --surface-2 --surface-3 --line --line-strong --text-value --text
--text-2 --text-3 --text-disabled --interactive --interactive-wash --on-fill
--status-caution --status-caution-wash --status-alarm --status-alarm-wash --status-ok
--status-ok-wash --status-shelved --status-stale --brand --cat-1 --cat-2 --cat-3 --cat-4
--cat-5 --cat-6 --cat-7 --cat-8 --focus-ring --overlay --bg-primary --bg-secondary
--bg-card --border --text-primary --text-secondary --accent --success --warning --danger --info
""".split()
CDF_TS_KEYS = """surface0 surface1 surface2 surface3 line lineStrong textValue text text2 text3
textDisabled interactive interactiveWash onFill caution cautionWash alarm alarmWash ok okWash
brand""".split()


def test_spacecdf_names_are_kept():
    css = CDF_CSS.read_text(encoding="utf-8")
    defined = set(re.findall(r"(--[\w-]+)\s*:", css))
    assert not (set(CDF_CSS_NAMES) - defined), set(CDF_CSS_NAMES) - defined
    assert "[data-theme='dark']" in css and "@import '@fontsource/ibm-plex-sans/400.css'" in css
    ts = CDF_TS.read_text(encoding="utf-8")
    c_block = ts[ts.index("export const c = {"):]
    c_block = c_block[:c_block.index("} as const")]
    keys = set(re.findall(r"^\s*(\w+):", c_block, re.M))
    assert not (set(CDF_TS_KEYS) - keys), set(CDF_TS_KEYS) - keys
    for name in ("export const fs", "export const font", "export function tint",
                 "export const SUBSYSTEM", "export function subsystemStyle"):
        assert name in ts


def _hand_written_css() -> str:
    css = DS_CSS.read_text(encoding="utf-8")
    head_end = css.index("*/") + 2                       # the header comment
    a, b = css.index("/* tokens:begin */"), css.index("/* tokens:end */")
    return css[head_end:a] + css[b:]


def test_console_css_uses_tokens_not_literal_colours():
    body = re.sub(r"/\*.*?\*/", "", _hand_written_css(), flags=re.S)
    hexes = re.findall(r"#[0-9A-Fa-f]{3,8}\b", body)
    assert not hexes, f"literal colours outside the generated token block: {hexes[:5]}"
    assert not re.search(r"rgba?\(", body), "literal rgb() colours outside the token block"


def test_console_css_type_floor_and_fonts():
    css = DS_CSS.read_text(encoding="utf-8")
    body = re.sub(r"/\*.*?\*/", "", _hand_written_css(), flags=re.S)
    sizes = [float(x) for x in re.findall(r"font-size:\s*([\d.]+)px", body)]
    assert sizes and min(sizes) >= 12, "type floor is 12 px"
    assert "Inter" not in re.sub(r"/\*.*?\*/", "", css, flags=re.S), "old font stack is back"
    # every self-hosted font the CSS points at ships with the package, with its licence
    urls = re.findall(r"url\((fonts/[^)]+)\)", css)
    assert len(urls) >= 14
    for u in urls:
        assert (UI / u).is_file(), u
    assert (UI / "fonts" / "OFL.txt").read_text(encoding="utf-8").count("SIL OPEN FONT LICENSE") >= 1
    # IBM Plex Mono ships 400/500 only: never ask the browser to fake a bold
    for rule in re.findall(r"\{[^}]*var\(--mono\)[^}]*\}", body):
        w = re.search(r"font-weight:\s*(\d+)", rule)
        assert not w or int(w.group(1)) <= 500, rule


def test_state_vocabulary_is_styled():
    css = DS_CSS.read_text(encoding="utf-8")
    for sel in (".is-disabled", '[aria-disabled="true"]', ".is-armed", ".is-active",
                ".is-stale", ".is-nodata", ".is-caution", ".is-alarm", ".ds-age",
                ".ds-nodata", ".ds-tip", ".ds-gauge", ".ds-tabs", ".ds-disclosure",
                ".ds-field", ".ds-readout"):
        assert sel in css, sel
    # the superseded "em-dash on a hatch" stale rule is gone
    assert ".ds-stale{ background:var(--hatch)" not in css
    # disabled controls: not-allowed cursor; blink only for unacked P1, off under reduced motion
    assert "cursor:not-allowed" in css
    assert ".ds-alarm-row.p1.unacked .pri{ animation" in css
    assert "prefers-reduced-motion:reduce" in css


def test_gallery_is_self_contained():
    html = (UI / "gallery.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/static/shared/design-system.css">' in html
    # offline: no CDN, no remote fonts
    assert not re.search(r"""(src|href)=["']https?://""", html)
    for mod in re.findall(r'from "(/static/shared/[\w.-]+\.js)"', html):
        assert (UI / mod.rsplit("/", 1)[1]).is_file(), mod
