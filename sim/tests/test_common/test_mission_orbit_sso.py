"""Ruling Q2b (2026-10-30, amended): EOSAT-1 flies a TRUE sun-synchronous orbit.

The shipped TLE (configs/eosat1/orbit.yaml) has inclination 97.39 deg -- the
exact SSO value for its 15.24 rev/day mean motion under SGP4's own secular
J2/J4 node rate (the interim 97.45 deg, computed from altitude, ran 0.0078
deg/day fast and drifted LTAN ~0.4 h in two years) -- RAAN
120 deg at the 2026-08-20T12:00Z epoch and 15.24 rev/day (mean altitude
~513 km, LTAN ~10:00). The previous 98.0 deg precessed the node at ~1.07
deg/day against the Sun's 0.9856 deg/day and walked LTAN by ~2 h a year.

These tests pin the physics, not just the number: the TLE must be valid, the
declared summaries must agree with it, and SGP4 must give a nodal rate close
to the Sun's so LTAN stays near 10:00 over the two-year active phase.
"""
import math
from pathlib import Path

import numpy as np
import pytest
import yaml
from sgp4.api import Satrec, WGS72

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"
SUN_RATE_DEG_DAY = 360.0 / 365.2422          # 0.9856 deg/day


def _orbit():
    return yaml.safe_load((CONFIG_DIR / "orbit.yaml").read_text("utf-8"))


def _checksum(line: str) -> int:
    return sum(int(c) if c.isdigit() else (1 if c == "-" else 0)
               for c in line[:68]) % 10


def _sat():
    o = _orbit()
    return Satrec.twoline2rv(o["tle_line1"], o["tle_line2"], WGS72)


class TestTle:

    def test_lines_are_69_chars_with_valid_checksums(self):
        o = _orbit()
        for key in ("tle_line1", "tle_line2"):
            line = o[key]
            assert len(line) == 69, key
            assert int(line[68]) == _checksum(line), key

    def test_inclination_is_97_39(self):
        o = _orbit()
        assert float(o["tle_line2"][8:16]) == pytest.approx(97.39)
        assert math.degrees(_sat().inclo) == pytest.approx(97.39, abs=1e-6)

    def test_raan_and_mean_motion_unchanged(self):
        line2 = _orbit()["tle_line2"]
        assert float(line2[17:25]) == pytest.approx(120.0)
        assert float(line2[52:63]) == pytest.approx(15.24)

    def test_declared_summaries_match_the_tle(self):
        o = _orbit()
        m = yaml.safe_load((CONFIG_DIR / "mission.yaml").read_text("utf-8"))
        assert o["inclination_deg"] == pytest.approx(97.39)
        assert m["orbit"]["inclination_deg"] == pytest.approx(97.39)


class TestSunSynchronous:

    def test_sgp4_nodal_rate_close_to_the_sun(self):
        """SGP4's secular node rate matches 0.9856 deg/day to 0.05 % (the old
        98.0 deg orbit was 8 % fast, the interim 97.45 deg 0.8 % fast)."""
        rate = math.degrees(_sat().nodedot) * 1440.0
        assert rate == pytest.approx(SUN_RATE_DEG_DAY, rel=5e-4), rate

    def test_inclination_is_the_exact_sso_value_for_the_mean_motion(self):
        """Solve SGP4's secular node rate for the inclination that equals the
        Sun's rate at this mean motion; the TLE carries it to 2 decimals."""
        line1, line2 = _orbit()["tle_line1"], _orbit()["tle_line2"]

        def rate(inc):
            l2 = line2[:8] + f"{inc:8.4f}" + line2[16:]
            return math.degrees(Satrec.twoline2rv(line1, l2, WGS72).nodedot) * 1440.0

        lo, hi = 96.0, 99.0
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if rate(mid) < SUN_RATE_DEG_DAY else (lo, mid)
        assert round(mid, 2) == pytest.approx(97.39), mid

    def test_ltan_stays_near_10h_over_two_years(self):
        """Measured LTAN (orbit-averaged RAAN against the mean sun) starts at
        ~10:05 and drifts under 5 minutes in two years (97.45 deg: ~0.4 h)."""
        sat = _sat()
        jd0 = sat.jdsatepoch + sat.jdsatepochF
        period_d = 1.0 / 15.24

        def ltan_h(jd):
            raans = []
            for k in range(40):
                _, r, v = sat.sgp4(jd + k * period_d / 40, 0.0)
                h = np.cross(r, v)
                n = np.cross([0.0, 0.0, 1.0], h)
                raans.append(math.atan2(n[1], n[0]))
            raan = math.degrees(float(np.mean(np.unwrap(raans)))) % 360.0
            d = jd - 2451545.0
            mean_sun = (280.460 + 0.9856474 * d) % 360.0
            return ((raan - mean_sun) / 15.0 + 12.0) % 24.0

        start = ltan_h(jd0)
        end = ltan_h(jd0 + 730.0)
        assert 9.75 < start < 10.25, start
        drift_h = (end - start + 12.0) % 24.0 - 12.0
        assert abs(drift_h) < 5.0 / 60.0, drift_h
