"""Ruling Q4 (2026-10-30): body +Z = zenith, -Z = nadir.

The imager boresight and the radiator are on -Z; the +Z face carries the
body-mounted cells (eps.yaml: mz has no cells), the zenith star tracker and
the GPS antenna. +X stays along-track (the -X thruster still burns prograde)
and the wing / SADA axis Y stays on the orbit normal.

Phase C had used the standard LVLH frame (z = nadir) as the nominal body
attitude, so these tests pin the convention at every layer that depends on
it: the reference attitude, the published nadir and sun vectors, the star
tracker mounts, the target-tracking frame, the EPS +Z cells and the power
budget tool's closed-form sun vector.
"""
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs" / "eosat1"
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from smo_common import attitude as att  # noqa: E402
from smo_simulator.models.aocs_basic import (  # noqa: E402
    AOCSBasicModel, MODE_NOMINAL, _ST_BORESIGHTS, nominal_body_dcm,
)
from smo_simulator.models.eps_basic import EPSBasicModel  # noqa: E402

import power_budget  # noqa: E402  (tools/power_budget.py)


def _orbit():
    return SimpleNamespace(
        in_eclipse=False, solar_beta_deg=-25.0, lat_deg=45.0, lon_deg=10.0,
        alt_km=513.0, vel_x=0.0, vel_y=7.5, vel_z=0.0, in_contact=False)


def _settled_nominal(ticks=1200):
    m = AOCSBasicModel()
    m.configure({})
    o = _orbit()
    p = {}
    m.handle_command({"command": "st_power", "unit": 1, "on": True})
    m.handle_command({"command": "set_mode", "mode": MODE_NOMINAL})
    for _ in range(ticks):
        m.tick(1.0, o, p)
    return m, o, p


class TestNominalBodyDcm:
    R = np.array([6891.0e3, 0.0, 0.0])
    V = np.array([0.0, -0.98, 7.54]) * 1e3      # ~97.4 deg inclination

    def test_minus_z_is_nadir_plus_z_is_zenith(self):
        C = nominal_body_dcm(self.R, self.V)
        nadir = -self.R / np.linalg.norm(self.R)
        assert np.allclose(C @ nadir, [0.0, 0.0, -1.0], atol=1e-12)
        assert np.allclose(C.T @ np.array([0.0, 0.0, 1.0]), -nadir,
                           atol=1e-12)

    def test_x_is_velocity_and_y_is_orbit_normal(self):
        C = nominal_body_dcm(self.R, self.V)
        v_hat = self.V / np.linalg.norm(self.V)
        h = np.cross(self.R, self.V)
        h_hat = h / np.linalg.norm(h)
        assert float(np.dot(C.T @ [1.0, 0.0, 0.0], v_hat)) > 0.9999
        assert np.allclose(C.T @ np.array([0.0, 1.0, 0.0]), h_hat,
                           atol=1e-12)

    def test_is_a_proper_rotation(self):
        C = nominal_body_dcm(self.R, self.V)
        assert np.allclose(C @ C.T, np.eye(3), atol=1e-12)
        assert np.linalg.det(C) == pytest.approx(1.0)

    def test_is_lvlh_turned_180_about_x(self):
        C = nominal_body_dcm(self.R, self.V)
        L = att.lvlh_dcm(self.R, self.V)
        assert np.allclose(C, np.diag([1.0, -1.0, -1.0]) @ L, atol=1e-12)


class TestNominalAttitudeInTheModel:
    """The closed-loop model, not just the helper, flies -Z at nadir."""

    def test_published_nadir_vector_is_minus_z(self):
        m, o, p = _settled_nominal()
        nadir_b = np.array([p[0x02B0], p[0x02B1], p[0x02B2]])
        assert nadir_b[2] < -0.999, nadir_b

    def test_reference_attitude_points_minus_z_at_nadir(self):
        m, o, p = _settled_nominal(ticks=10)
        q_ref, _ = m._compute_reference(m._state, MODE_NOMINAL)
        C = att.quat_to_dcm(q_ref)
        r = m._env['r_m']
        assert float((C @ (-r / np.linalg.norm(r)))[2]) == pytest.approx(
            -1.0, abs=1e-9)

    def test_published_sun_vector_y_is_sin_beta(self):
        """+Y = +orbit normal, so sun_body_y = sin(beta) in NOMINAL (the
        97.39 deg SSO keeps beta negative: the sun is on the -Y side)."""
        m, o, p = _settled_nominal()
        sun_y = p[0x02B4]
        h = np.cross(m._env['r_m'], m._env['v_ms'])
        beta = math.asin(float(np.dot(h / np.linalg.norm(h),
                                      m._env['sun_hat'])))
        assert sun_y == pytest.approx(math.sin(beta), abs=2e-3)


class TestStarTrackerMounting:

    def test_neither_tracker_sees_the_earth_in_nominal(self):
        """Over a full orbit of nadir pointing, both boresights stay well
        above the Earth's limb (angular radius ~67.8 deg at 513 km)."""
        rho = math.degrees(math.asin(6378.137 / (6378.137 + 513.0)))
        r0 = 6891.0e3
        v0 = 7.6e3
        for k in range(36):
            th = 2 * math.pi * k / 36
            r = r0 * np.array([math.cos(th), math.sin(th), 0.0])
            v = v0 * np.array([-math.sin(th), math.cos(th), 0.0])
            C = nominal_body_dcm(r, v)
            nadir_b = C @ (-r / r0)
            for unit, b in _ST_BORESIGHTS.items():
                c = max(-1.0, min(1.0, float(np.dot(nadir_b, b))))
                ang = math.degrees(math.acos(c))
                assert ang > rho + 30.0, (unit, ang)

    def test_nominal_sun_outside_exclusion_cones(self):
        """With beta in the 97.39 deg SSO's yearly band (about -21 to
        -31 deg) the sun stays outside both 15 deg exclusion cones."""
        m = AOCSBasicModel()
        m.configure({})
        for beta in (-17.0, -20.0, -25.0, -31.5):
            for k in range(72):
                sun = power_budget.sun_body_nominal(beta, 5.0 * k)
                for unit, b in _ST_BORESIGHTS.items():
                    assert not m._check_st_blinding(sun, b), (beta, k, unit)


class TestTargetTrackFrame:

    def test_imager_minus_z_points_at_the_target(self):
        m, o, p = _settled_nominal(ticks=10)
        s = m._state
        r = m._env['r_m']
        # Target on the sub-satellite meridian: whatever lat/lon is used,
        # the reference must put the -Z boresight on the line of sight.
        lon = o.lon_deg
        r_hat = r / np.linalg.norm(r)
        lat = math.degrees(math.asin(float(r_hat[2])))
        m.handle_command({"command": "set_target_geo", "lat": lat,
                          "lon": lon, "alt_m": 0.0})
        s.pointing_frame = 2
        q_ref, _ = m._compute_reference(s, MODE_NOMINAL)
        C = att.quat_to_dcm(q_ref)
        boresight_eci = C.T @ np.array([0.0, 0.0, -1.0])
        # The target is on the visible Earth: the boresight is close to nadir
        assert float(np.dot(boresight_eci, -r_hat)) > 0.99
        assert float(np.dot(C.T @ np.array([0.0, 0.0, 1.0]), r_hat)) > 0.99


def _eps():
    cfg = yaml.safe_load((CONFIG_DIR / "subsystems" / "eps.yaml").read_text())
    cfg["simulation"] = yaml.safe_load(
        (CONFIG_DIR / "simulation.yaml").read_text())["eps"]
    m = EPSBasicModel()
    m.configure(cfg)
    m.rng.seed(20261030)
    m._state.wing_py_deployed = True
    m._state.wing_my_deployed = True
    return m


class TestEpsZenithCells:

    def test_body_sun_vector_matches_the_model_frame(self):
        r = np.array([7.0e6, 0.0, 0.0])
        v = np.array([0.0, 7.5e3, 0.0])     # h = +z
        for beta in (0.0, -25.0, 32.3):
            for phase in (0.0, 37.0, 214.0):
                b, ph = math.radians(beta), math.radians(phase)
                sun = np.array([math.cos(b) * math.cos(ph),
                                math.cos(b) * math.sin(ph), math.sin(b)])
                truth = nominal_body_dcm(r, v) @ sun
                got = power_budget.sun_body_nominal(beta, phase)
                assert got == pytest.approx(tuple(truth), abs=1e-12)

    def test_plus_z_cells_lit_at_orbit_noon_minus_z_has_none(self):
        """At orbit noon (phase 0) the sun is near the zenith: the +Z face
        is lit and generates; -Z (nadir: imager + radiator) has no cells."""
        m = _eps()
        orbit = SimpleNamespace(solar_beta_deg=-25.0, in_eclipse=False)
        sx, sy, sz = power_budget.sun_body_nominal(-25.0, 0.0)
        assert sz > 0.9
        m.tick(1.0, orbit, {0x02B3: sx, 0x02B4: sy, 0x02B5: sz})
        cur = m._state.sa_panel_currents
        assert cur["pz"] > 0.0
        assert cur["mz"] == 0.0
