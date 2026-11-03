"""Shared pictorial displays (shared/ui-viz).

The modules in shared/ui-viz/ are the single source; sync.py copies them to
smo_common/ui/viz/ (served at /static/shared/viz/) and to SpaceCDF's
design/frontend/src/viz/. These tests keep the copies in step, run the
derive.js unit tests under Node, cross-check its quaternion algebra against
smo_common/attitude.py (the simulator's own conventions), and hold the
modules to the design-system rules (tokens only, framework-free, EN/FR).
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
VIZ = REPO / "shared" / "ui-viz"
SYNC = VIZ / "sync.py"
SERVED = REPO / "sim/packages/smo-common/src/smo_common/ui/viz"
FR_SHARED = REPO / "sim/packages/smo-common/src/smo_common/ui/i18n/fr.json"
MCS_MODERN = REPO / "sim/packages/smo-mcs/src/smo_mcs/static/modern"
DERIVE_TESTS = Path(__file__).parent / "js" / "test_derive.mjs"
# The modules this suite owns the rules for (the 3D/map modules have their own tests).
V1_MODULES = ["common.js", "derive.js", "powerflow.js", "overview.js", "attitude2d.js"]
NODE = shutil.which("node")


def _sync_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("c2o_viz_sync", SYNC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generated_copies_are_in_sync():
    """`sync.py --check` fails on a hand edit of a copy or a forgotten sync."""
    r = subprocess.run([sys.executable, str(SYNC), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_sync_ships_modules_not_tooling():
    shipped = _sync_module().shipped()
    for name in V1_MODULES:
        assert name in shipped, name
    assert "sync.py" not in shipped and "README.md" not in shipped
    assert "GENERATED.txt" in shipped


@pytest.mark.parametrize("name", V1_MODULES)
def test_modules_use_tokens_only(name):
    """Pictures use tokens: no literal colour in the module source."""
    src = (VIZ / name).read_text(encoding="utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", src), "hex colour literal"
    assert not re.search(r"\brgba?\(", src), "rgb() colour literal"


@pytest.mark.parametrize("name", V1_MODULES)
def test_modules_are_framework_free_and_relative(name):
    """Importable unchanged by the vanilla consoles and by SpaceCDF (Vite)."""
    src = (VIZ / name).read_text(encoding="utf-8")
    for spec in re.findall(r'^\s*import[^;]*?from\s+"([^"]+)"', src, re.M):
        assert spec.startswith("./"), f"{name} imports {spec}"


@pytest.mark.parametrize("name", ["powerflow.js", "overview.js", "attitude2d.js"])
def test_views_follow_the_mount_contract(name):
    src = (VIZ / name).read_text(encoding="utf-8")
    assert re.search(r"export function mount\(el, opts = \{\}\)", src)
    assert "update" in src and "destroy" in src
    # text alternative: a values table toggle and an SVG title/summary
    assert "mountFrame(" in src and "valuesTable(" in src


def test_reduced_motion_is_honoured():
    src = (VIZ / "powerflow.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion:reduce" in src and "reducedMotion()" in src


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_derive_unit_tests_pass():
    r = subprocess.run([NODE, str(DERIVE_TESTS), str(VIZ / "derive.js")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("ok ")


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_quaternion_algebra_matches_the_simulator(tmp_path):
    """derive.js and smo_common.attitude agree on product, DCM and angle."""
    import numpy as np
    from smo_common import attitude as att

    rng = np.random.default_rng(7)
    cases = []
    for _ in range(6):
        a = att.quat_normalize(rng.normal(size=4))
        b = att.quat_normalize(rng.normal(size=4))
        cases.append({"a": a.tolist(), "b": b.tolist()})
    snippet = tmp_path / "q.mjs"
    snippet.write_text(
        "import { pathToFileURL } from 'node:url';\n"
        f"const D = await import(pathToFileURL({json.dumps(str(VIZ / 'derive.js'))}).href);\n"
        f"const cases = {json.dumps(cases)};\n"
        "console.log(JSON.stringify(cases.map(({a, b}) => ({ mul: D.quatMul(a, b), dcm: D.quatToDcm(a),"
        " ang: D.attitudeAngleDeg(a, b) }))));\n", encoding="utf-8")
    r = subprocess.run([NODE, str(snippet)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    got = json.loads(r.stdout)
    for c, g in zip(cases, got):
        np.testing.assert_allclose(g["mul"], att.quat_mult(c["a"], c["b"]), atol=1e-12)
        np.testing.assert_allclose(g["dcm"], att.quat_to_dcm(c["a"]), atol=1e-12)
        assert math.isclose(g["ang"], att.quat_angle_deg(c["a"], c["b"]), abs_tol=1e-6)


def _t_keys(src: str) -> set[str]:
    keys = set(re.findall(r'\bt\(\s*"((?:\\.|[^"\\])*)"', src))
    m = re.search(r"DYNAMIC_KEYS = \[(.*?)\];", src, re.S)
    if m:
        keys |= set(re.findall(r'"((?:\\.|[^"\\])*)"', m.group(1)))
    return {k.encode().decode("unicode_escape") if "\\" in k else k for k in keys}


def test_every_view_string_has_french():
    fr = json.loads(FR_SHARED.read_text(encoding="utf-8"))
    missing = []
    for name in V1_MODULES:
        for k in _t_keys((VIZ / name).read_text(encoding="utf-8")):
            if not fr.get(k):
                missing.append(f"{name}: {k}")
    assert not missing, missing


def test_mcs_mounts_the_views_with_a_fallback():
    """The MCS loads pictorial.js lazily (the console keeps its schematics if
    the shared modules are absent) and leaves the 3D slot for attitude3d."""
    mcs = (MCS_MODERN / "mcs.js").read_text(encoding="utf-8")
    pic = (MCS_MODERN / "pictorial.js").read_text(encoding="utf-8")
    assert 'import("/static/modern/pictorial.js")' in mcs
    assert 'id="att3d"' in mcs and 'id="aocs-att2d"' in mcs and 'id="eps-flow"' in mcs
    assert 'id="ovr-power"' in mcs
    for mod in ("derive.js", "powerflow.js", "overview.js", "attitude2d.js", "attitude3d.js"):
        assert mod in pic
    assert '"/static/shared/viz/"' in pic
    # instructor-only parameters never feed an operator picture
    import yaml
    params = yaml.safe_load((REPO / "sim/configs/eosat1/telemetry/parameters.yaml").read_text())
    instr = {f"0x{int(str(p['id']), 0):04X}" for p in params["parameters"]
             if p.get("visibility") == "instructor"}
    used = set()
    for name in V1_MODULES:
        used |= set(re.findall(r'"(0x[0-9A-F]{4})"', (VIZ / name).read_text(encoding="utf-8")))
    used |= set(re.findall(r'"(0x[0-9A-F]{4})"', pic))
    assert not (used & instr), sorted(used & instr)


def test_served_copy_is_reachable_by_the_shared_mount():
    """/static/shared/ serves smo_common/ui/, so viz/ lands at /static/shared/viz/."""
    for name in V1_MODULES:
        assert (SERVED / name).is_file(), name


def test_overview_deployables_come_from_downlinked_tm_only():
    """Franz (2026-11-03): antenna and wings stowed or deployed, panels in
    sunlight or not — "if telemetry is available for this". Every parameter
    deriveDeployment() reads is a real (not ground-derived, not instructor)
    parameter carried by a housekeeping SID, so the picture shows what the
    spacecraft says and never simulator truth."""
    import yaml
    src = (VIZ / "derive.js").read_text(encoding="utf-8")
    i = src.index("export function deriveDeployment")
    body = src[src.index("/* ── 9. Deployables"):src.index("export function deriveAll")]
    used = set(re.findall(r'"(0x[0-9A-F]{4})"', body))
    assert {"0x0536", "0x0520", "0x0144", "0x0146", "0x0147", "0x0108", "0x014E",
            "0x012B", "0x0130"} <= used
    cfg = REPO / "sim/configs/eosat1/telemetry"
    params = {int(str(p["id"]), 0): p for p in yaml.safe_load((cfg / "parameters.yaml").read_text())["parameters"]}
    in_sid = {int(str(x["param_id"]), 0) for s in yaml.safe_load((cfg / "hk_structures.yaml").read_text())["structures"]
              for x in s["parameters"]}
    for h in used:
        n = int(h, 16)
        assert params[n].get("visibility", "real") == "real", h
        assert n in in_sid, f"{h} is in no HK SID"
    # the overview is fed the model, and draws stowed / deployed and the key
    assert i > 0 and "deploy: m.deploy" in (MCS_MODERN / "pictorial.js").read_text(encoding="utf-8")
    ov = (VIZ / "overview.js").read_text(encoding="utf-8")
    for s in ("function wingSvg", "function antennaSvg", "function solarHtml", '"antenna stowed"',
              '"sunlit: delivering current"', '"no data: not downlinked"'):
        assert s in ov, s
