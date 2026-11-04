"""Ground orbit products the workbook reads off the screens (worksheet screen
audit, 2026-11-04).

* OrbitPropagator.eclipse_window — the MCS EPS page's "Next eclipse"
  (duration) and "This eclipse";
* Orbit tools: the elements of the mission TLE (RAAN was 90° off), the GPS
  ECEF state converted to inertial before the elements are taken (the
  inclination was 3.5° off), LTAN, TCA in the pass list, the eclipse list.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
import yaml

SIM = Path(__file__).resolve().parents[2]
if str(SIM / "tools") not in sys.path:
    sys.path.insert(0, str(SIM / "tools"))

from smo_common.orbit.propagator import OrbitPropagator  # noqa: E402

ORBIT = yaml.safe_load((SIM / "configs" / "eosat1" / "orbit.yaml").read_text())
T0 = datetime(2026, 8, 20, 12, 4, tzinfo=timezone.utc)


def _prop(t):
    p = OrbitPropagator(ORBIT["tle_line1"], ORBIT["tle_line2"])
    p.reset(t)
    return p


def test_eclipse_window_sunlit_and_in_eclipse():
    w = _prop(T0).eclipse_window()
    assert w["in_eclipse"] is False
    assert 0 < w["entry_s"] < w["exit_s"]
    # EOSAT-1's eclipses run 33.2–35.2 min over the year (manual 07 §3)
    assert 33.0 * 60 <= w["duration_s"] <= 35.5 * 60
    mid = T0 + timedelta(seconds=w["entry_s"] + w["duration_s"] / 2)
    w2 = _prop(mid).eclipse_window()
    assert w2["in_eclipse"] is True
    assert w2["entry_s"] < 0 < w2["exit_s"]
    assert abs(w2["duration_s"] - w["duration_s"]) < 5.0
    # the edges agree with the next-transition scan to its 60 s step
    tr = _prop(T0).next_eclipse_transition()
    assert abs(tr["time_to_eclipse_entry_s"] - w["entry_s"]) <= 60.0


def test_eclipse_window_mutates_nothing():
    p = _prop(T0)
    before = (p.state.lat_deg, p.state.in_eclipse, p._current_utc)
    p.eclipse_window()
    assert (p.state.lat_deg, p.state.in_eclipse, p._current_utc) == before


def test_orbit_tools_elements_of_the_mission_tle():
    import orbit_tools as ot
    r, v = ot.TleToStateConverter.propagate(ORBIT["tle_line1"], ORBIT["tle_line2"], T0)
    e = ot.OrbitAnalyzer.compute_orbital_elements(r, v)
    assert e["i_deg"] == pytest.approx(97.39, abs=0.05)
    assert e["raan_deg"] == pytest.approx(120.0, abs=0.5)        # TLE RAAN 120°
    # argument of latitude: AOP + true anomaly is the angle from the node to r
    h = np.cross(r, v)
    n = np.cross([0.0, 0.0, 1.0], h)
    u = np.degrees(np.arctan2(np.dot(np.cross(n, r), h) / np.linalg.norm(h), np.dot(n, r))) % 360
    assert (e["aop_deg"] + e["ta_deg"]) % 360 == pytest.approx(u, abs=0.01)
    assert ot.ltan_hours(T0, e["raan_deg"]) == pytest.approx(10.0, abs=0.25)                     # LTAN ~10:00 (manual 00 §3)


def test_orbit_tools_gps_ecef_state_gives_the_inertial_elements():
    """A GPS fix is Earth-fixed (velocity relative to the rotating Earth):
    the elements must be taken after ECEF→ECI with the rotation term."""
    import orbit_tools as ot
    r, v = ot.TleToStateConverter.propagate(ORBIT["tle_line1"], ORBIT["tle_line2"], T0)
    g = ot._gmst_at(T0, np.array([0.0]))[0]
    r_e = ot.EciEcefConverter.eci_to_ecef(r, g)
    v_e = ot.EciEcefConverter.eci_to_ecef(v, g) - np.cross([0.0, 0.0, ot._OMEGA_EARTH], r_e)
    ri, vi = ot.ecef_state_to_eci(r_e, v_e, T0)
    e = ot.OrbitAnalyzer.compute_orbital_elements(ri, vi)
    ref = ot.OrbitAnalyzer.compute_orbital_elements(r, v)
    assert e["i_deg"] == pytest.approx(ref["i_deg"], abs=0.02)
    assert e["raan_deg"] == pytest.approx(ref["raan_deg"], abs=0.1)
    assert e["period_min"] == pytest.approx(ref["period_min"], abs=0.05)
    # what the page did before: several degrees off
    bad = ot.OrbitAnalyzer.compute_orbital_elements(r_e, v_e)
    assert abs(bad["i_deg"] - ref["i_deg"]) > 1.0


def test_orbit_tools_passes_carry_tca_and_eclipses_the_longest():
    import orbit_tools as ot
    geo = ot.orbit_geometry(T0, tle=(ORBIT["tle_line1"], ORBIT["tle_line2"]))
    assert geo["passes"]
    for p in geo["passes"]:
        assert p["aos_s"] <= p["tca_s"] <= p["los_s"]
    ecl = geo["eclipses"]
    assert len(ecl) >= 14                     # ~15 orbits in 24 h
    whole = [e for e in ecl if not e["truncated"]]
    longest = [e for e in ecl if e.get("longest")]
    assert len(longest) == 1 and longest[0]["duration_s"] == max(e["duration_s"] for e in whole)
    for e in whole:
        assert 32 * 60 <= e["duration_s"] <= 36 * 60
