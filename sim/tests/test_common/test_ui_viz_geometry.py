"""Spacecraft geometry for the pictorial displays (configs/eosat1/geometry.yaml).

The 3D attitude view (shared/ui-viz/attitude3d.js) draws EOSAT-1 from this
file, and SpaceCDF will write the same shape for a design. The file copies
numbers owned elsewhere, so these tests pin each copy to its owner: the
config files (via validate_geometry's cross-check) and the simulator's own
constants (star-tracker boresights and exclusion, the wing normal law, the
thrust axis). They also pin the MCS route GET /api/geometry.
"""
from __future__ import annotations

import copy
import math
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.config.geometry import (
    GeometryError, SCHEMA, load_geometry, validate_geometry,
)

REPO = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO / "configs" / "eosat1"


@pytest.fixture(scope="module")
def geo():
    return load_geometry(CONFIG_DIR)


def test_eosat1_geometry_loads_and_validates(geo):
    assert geo["schema"] == SCHEMA
    assert geo["spacecraft"] == "EOSAT-1"
    assert validate_geometry(geo, CONFIG_DIR) == []


def test_quaternion_convention_matches_smo_common_attitude(geo):
    """The views print this convention; smo_common.attitude defines it."""
    import numpy as np
    from smo_common import attitude as att
    assert geo["quaternion"] == {"order": "xyzw", "maps": "eci_to_body"}
    # scalar last: identity is [0, 0, 0, 1] and maps ECI -> body unchanged.
    assert np.allclose(att.quat_to_dcm([0, 0, 0, 1]), np.eye(3))
    # eci_to_body: +90 deg about Z (q = [0,0,s,s]) takes ECI +X to body -Y.
    s = math.sqrt(0.5)
    assert np.allclose(att.quat_to_dcm([0, 0, s, s]) @ [1, 0, 0], [0, -1, 0])


def test_bus_is_the_6u_envelope_from_eps_yaml(geo):
    # eps.yaml: 6U CDS envelope 100 x 226 x 366 mm; +-X faces 366x226 etc.
    assert geo["bus"]["size_m"] == pytest.approx([0.100, 0.226, 0.366])


def test_star_trackers_match_the_simulator(geo):
    from smo_simulator.models import aocs_basic
    st = {s["id"]: s["boresight"] for s in geo["star_trackers"]}
    assert st["st1"] == pytest.approx(list(aocs_basic._ST_BORESIGHTS[1]))
    assert st["st2"] == pytest.approx(list(aocs_basic._ST_BORESIGHTS[2]), abs=1e-6)
    assert geo["star_tracker_sun_exclusion_deg"] == aocs_basic._ST_EXCLUSION_DEG


def test_wing_normal_law_matches_eps_model(geo):
    """n(a) = cos a * normal_at_0deg + sin a * normal_at_90deg == _wing_normal."""
    from smo_simulator.models.eps_basic import EPSBasicModel
    eps = EPSBasicModel()
    eps.configure(yaml.safe_load((CONFIG_DIR / "subsystems" / "eps.yaml").read_text()))
    d = geo["array_drive"]
    for deg in (-135, -30, 0, 45, 90, 170):
        a = math.radians(deg)
        want = eps._wing_normal(a)
        got = [math.cos(a) * n0 + math.sin(a) * n9
               for n0, n9 in zip(d["normal_at_0deg"], d["normal_at_90deg"])]
        assert got == pytest.approx(list(want), abs=1e-9), deg


def test_thruster_axis_matches_prop_yaml(geo):
    prop = yaml.safe_load((CONFIG_DIR / "subsystems" / "prop.yaml").read_text())
    assert geo["thrusters"][0]["thrust_axis"] == pytest.approx(prop["thrust_axis"])


def test_drive_angle_and_wing_bits_name_real_telemetry(geo):
    params = yaml.safe_load((CONFIG_DIR / "telemetry" / "parameters.yaml").read_text())
    by_name = {p["name"]: p for p in params["parameters"]}
    assert geo["array_drive"]["angle_param"] in by_name
    assert "bit0=+Y" in by_name["eps.wing_status"]["description"]
    bits = {w["face"]: w["deployed_bit"] for w in geo["wings"]}
    assert bits == {"py": 0, "my": 1}


# ── validator negatives ──────────────────────────────────────────────

def _broken(geo, mutate):
    g = copy.deepcopy(geo)
    mutate(g)
    return validate_geometry(g)


@pytest.mark.parametrize("mutate, fragment", [
    (lambda g: g.update(colour="red"), "unknown key 'colour'"),
    (lambda g: g.update(schema="c2o.geometry/0"), "schema"),
    (lambda g: g["bus"].update(size_m=[0.1, -0.2, 0.3]), "bus.size_m"),
    (lambda g: g["payload"].update(boresight=[0, 0, -2]), "payload"),
    (lambda g: g["body_panels"][0].update(normal=[0, 1, 0]), "not the px face normal"),
    (lambda g: g["wings"][0].update(cell_area_m2=9.0), "exceeds the panel area"),
    (lambda g: g["array_drive"].update(normal_at_90deg=[1, 0, 0]), "orthogonal"),
    (lambda g: g["star_trackers"][1].update(id="st1"), "duplicate id"),
    (lambda g: g.update(star_tracker_earth_exclusion_deg=200), "earth_exclusion"),
    (lambda g: g["thrusters"][0].pop("thrust_axis"), "missing thrust_axis"),
])
def test_validator_reports_each_problem(geo, mutate, fragment):
    probs = _broken(geo, mutate)
    assert any(fragment in p for p in probs), probs


def test_stack_builder_extension_is_optional_and_checked(geo):
    """SpaceCDF's stack builder adds frame / internal / mass_properties (additive)."""
    assert validate_geometry(geo, CONFIG_DIR) == []          # the file without them stays valid
    g = copy.deepcopy(geo)
    g["frame"] = {"origin": "envelope centre", "axes": "+Z zenith"}
    g["internal"] = [{"id": "obc", "name": "OBC", "mount": "pc104_board", "column": 0, "slot": 2,
                      "face": None, "box_m": [0.0, -0.056, 0.01, 0.096, 0.09, 0.015], "mass_kg": 0.06},
                     {"id": "patch", "face": "mz", "box_m": [0.0, 0.05, -0.18, 0.098, 0.098, 0.005]}]
    g["mass_properties"] = {"mass_kg": 11.2, "cog_m": [0.001, -0.004, 0.006]}
    assert validate_geometry(g) == []
    bad = copy.deepcopy(g)
    bad["internal"][0]["box_m"] = [0, 0, 0, -0.1, 0.1, 0.1]
    bad["internal"][1]["face"] = "top"
    bad["mass_properties"] = {"mass_kg": 3}
    probs = validate_geometry(bad)
    assert any("internal[0].box_m" in p for p in probs), probs
    assert any("internal.patch.face" in p for p in probs), probs
    assert any("mass_properties" in p for p in probs), probs


def test_cross_check_catches_a_drifted_copy(geo, tmp_path):
    cfg = tmp_path / "cfg"
    (cfg / "subsystems").mkdir(parents=True)
    (cfg / "planning").mkdir()
    shutil.copy(CONFIG_DIR / "subsystems" / "eps.yaml", cfg / "subsystems" / "eps.yaml")
    shutil.copy(CONFIG_DIR / "planning" / "planner.yaml", cfg / "planning" / "planner.yaml")
    g = copy.deepcopy(geo)
    g["body_panels"][0]["cell_area_m2"] = 0.061
    g["payload"]["fov_deg"] = 30.0
    g["array_drive"].update(axis=[0, 0, 1], normal_at_90deg=[0, 1, 0])
    probs = validate_geometry(g, cfg)
    assert any("solar_panels.px_area_m2" in p for p in probs)
    assert any("imaging.fov_deg" in p for p in probs)
    assert any("sada_axis" in p for p in probs)


def test_missing_file_raises_with_the_path(tmp_path):
    with pytest.raises(GeometryError) as e:
        load_geometry(tmp_path)
    assert "geometry.yaml not found" in e.value.problems[0]


# ── MCS route ────────────────────────────────────────────────────────

def _server(config_dir):
    from smo_common.config.schemas import MCSDisplayConfig
    from smo_mcs.server import MCSServer
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}):
        srv = MCSServer(config_dir=str(CONFIG_DIR), connect_host="localhost",
                        connect_port=9999, http_port=0)
    srv.config_dir = Path(config_dir)
    srv._running = False
    return srv


async def _get(srv, path="/api/geometry"):
    app = web.Application()
    app.router.add_get("/api/geometry", srv._handle_geometry)
    cli = TestClient(TestServer(app))
    await cli.start_server()
    try:
        res = await cli.get(path)
        return res.status, await res.json()
    finally:
        await cli.close()


@pytest.mark.asyncio
async def test_mcs_serves_geometry(geo):
    status, body = await _get(_server(CONFIG_DIR))
    assert status == 200
    assert body["geometry"] == geo


@pytest.mark.asyncio
async def test_mcs_geometry_missing_is_503_not_a_default(tmp_path):
    status, body = await _get(_server(tmp_path))
    assert status == 503
    assert body["error"] == "geometry unavailable"
    assert body["problems"]


def test_mcs_route_is_registered_read_only():
    src = (REPO / "packages" / "smo-mcs" / "src" / "smo_mcs" / "server.py").read_text()
    assert 'add_get("/api/geometry", self._handle_geometry)' in src
    assert 'add_post("/api/geometry"' not in src


# ── the JS views' pure geometry (node) ───────────────────────────────

VIZ = REPO.parent / "shared" / "ui-viz"
JS_TEST = Path(__file__).resolve().parent / "js" / "test_geometry_views.mjs"


def _reference() -> dict:
    """Frame maths from the simulator's own module, for the JS to match."""
    import numpy as np
    from smo_common import attitude as att
    from smo_simulator.models.aocs_basic import nominal_body_dcm
    r = [4200.0, -3100.0, 4300.0]                      # km, arbitrary LEO-ish
    v = [-2.1, 4.9, 5.6]                               # km/s
    q = list(att.quat_normalize([0.1, -0.3, 0.2, 0.9]))
    q_nom = list(att.dcm_to_quat(nominal_body_dcm(np.array(r), np.array(v))))
    return {"q": q, "C": att.quat_to_dcm(q).tolist(), "r": r, "v": v,
            "L": att.lvlh_dcm(r, v).tolist(), "qNominal": q_nom}


def test_geometry_views_js_against_smo_common_attitude():
    import json
    import shutil as sh
    import subprocess
    node = sh.which("node")
    if not node:
        pytest.skip("node not installed")
    out = subprocess.run([node, str(JS_TEST), str(VIZ), json.dumps(_reference())],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    assert out.stdout.startswith("ok "), out.stdout


def test_shared_basemap_is_the_planner_basemap():
    """land110m.js carries the planner wall display's Natural Earth data verbatim."""
    import re
    shared = (VIZ / "land110m.js").read_text()
    planner = (REPO / "packages" / "smo-planner" / "src" / "smo_planner" / "static"
               / "modern" / "wide-basemap.js").read_text()
    body = lambda s: re.sub(r"\s+", "", s[s.index("export const LAND"):])  # noqa: E731
    assert body(shared) == body(planner)


def test_vendored_three_is_pinned_with_its_licence():
    d = VIZ / "vendor" / "three"
    js = (d / "three.module.min.js").read_text()
    assert 'const t="170"' in js[:400], "three.js r170 expected (pinned)"
    assert "MIT License" in (d / "LICENSE").read_text()
    for name in ("attitude3d.js",):
        assert './vendor/three/three.module.min.js"' in (VIZ / name).read_text()
