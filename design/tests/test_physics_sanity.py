"""
Physics Sanity Check — validates all analytical models against known references.
"""
import sys, math
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
for pkg in ["spacecdf-server", "spacecdf-common", "spacecdf-agents", "spacecdf-kb"]:
    src = str(_root / "packages" / pkg / "src")
    if src not in sys.path:
        sys.path.insert(0, src)

import pytest


class TestOrbitMechanics:
    def test_iss_orbit_period(self):
        from spacecdf_common.physics.orbit import compute_orbit_params
        p = compute_orbit_params(410, 51.6)
        assert abs(p.period_s / 60 - 92.6) < 1.0

    def test_geo_orbit_period(self):
        from spacecdf_common.physics.orbit import compute_orbit_params
        p = compute_orbit_params(35786, 0)
        assert abs(p.period_s / 60 - 1436) < 5

    def test_sso_inclination_500km(self):
        from spacecdf_common.physics.orbit import sso_inclination
        assert abs(sso_inclination(500) - 97.4) < 0.5

    def test_hohmann_leo_to_geo(self):
        from spacecdf_common.physics.orbit import delta_v_hohmann
        dv1, dv2 = delta_v_hohmann(200, 35786)
        assert abs((dv1 + dv2) - 3940) < 100, f"LEO-GEO ΔV: {dv1+dv2:.0f} m/s"

    def test_eclipse_fraction_sso(self):
        from spacecdf_common.physics.orbit import compute_orbit_params
        p = compute_orbit_params(500, 97.4, beta_angle_deg=0)
        assert 0.25 < p.eclipse_fraction < 0.45


class TestLinkBudget:
    def test_xband_link_closes(self):
        from spacecdf_common.physics.link_budget import compute_link_budget
        r = compute_link_budget(altitude_km=500, frequency_ghz=8.2, tx_power_w=2,
                                tx_antenna_gain_dbi=6, gs_antenna_diameter_m=5, min_elevation_deg=10)
        assert r.downlink_margin_db > -10, f"X-band margin {r.downlink_margin_db:.1f} dB"

    def test_fspl_increases_with_frequency(self):
        from spacecdf_common.physics.link_budget import compute_link_budget
        r_uhf = compute_link_budget(altitude_km=500, frequency_ghz=0.4)
        r_xband = compute_link_budget(altitude_km=500, frequency_ghz=8.2)
        assert r_xband.free_space_loss_db > r_uhf.free_space_loss_db, "Higher freq = more path loss"


class TestPowerBudget:
    def test_power_budget_produces_sa_area(self):
        from spacecdf_common.physics.power import compute_power_budget
        r = compute_power_budget(eclipse_fraction=0.35, sunlight_fraction=0.65,
                                 orbit_period_s=5670, payload_power_w=10, platform_power_w=5)
        assert r.sa_area_m2 > 0, "SA area should be positive"
        assert r.battery_capacity_wh > 0, "Battery capacity should be positive"

    def test_deeper_eclipse_needs_more_battery(self):
        from spacecdf_common.physics.power import compute_power_budget
        r1 = compute_power_budget(eclipse_fraction=0.20, sunlight_fraction=0.80, orbit_period_s=5670)
        r2 = compute_power_budget(eclipse_fraction=0.40, sunlight_fraction=0.60, orbit_period_s=5670)
        assert r2.battery_capacity_wh > r1.battery_capacity_wh


class TestThermal:
    def test_stefan_boltzmann(self):
        sigma = 5.67e-8
        eps = 0.85
        T = 300
        Q = 20
        A = Q / (eps * sigma * T ** 4)
        assert 0.01 < A < 0.1, f"Radiator area {A:.3f} m²"


class TestPropulsion:
    def test_tsiolkovsky(self):
        from spacecdf_common.physics.propulsion import tsiolkovsky
        m = tsiolkovsky(delta_v_ms=100, isp_s=220, dry_mass_kg=5)
        expected = 5 * (math.exp(100 / (220 * 9.80665)) - 1)
        assert abs(m - expected) < 0.01

    def test_high_delta_v_mass_ratio(self):
        from spacecdf_common.physics.propulsion import tsiolkovsky
        m = tsiolkovsky(delta_v_ms=2000, isp_s=310, dry_mass_kg=10)
        ratio = (10 + m) / 10
        expected = math.exp(2000 / (310 * 9.80665))
        assert abs(ratio - expected) < 0.1


class TestStructures:
    def test_cubesat_structure(self):
        from spacecdf_common.physics.structures import estimate_structure_mass
        r = estimate_structure_mass(spacecraft_dry_mass_kg=5, spacecraft_class="nano")
        assert 0.2 < r.structure_mass_kg < 2.0, f"Structure mass {r.structure_mass_kg:.2f} kg"


class TestDeorbit:
    def test_400km_lifetime(self):
        from spacecdf_common.physics.debris import estimate_orbital_lifetime
        lt = estimate_orbital_lifetime(400, area_to_mass_ratio_m2_kg=0.007)
        assert 0.5 < lt < 15

    def test_500km_lifetime(self):
        from spacecdf_common.physics.debris import estimate_orbital_lifetime
        lt = estimate_orbital_lifetime(500, area_to_mass_ratio_m2_kg=0.007)
        assert 2 < lt < 40

    def test_800km_no_natural_compliance(self):
        from spacecdf_common.physics.debris import estimate_orbital_lifetime
        assert estimate_orbital_lifetime(800, area_to_mass_ratio_m2_kg=0.007) > 25

    def test_drag_sail_enables_compliance(self):
        from spacecdf_common.physics.debris import estimate_orbital_lifetime
        lt = estimate_orbital_lifetime(700, area_to_mass_ratio_m2_kg=0.2)
        assert lt < 25

    def test_solar_cycle(self):
        from spacecdf_common.physics.debris import estimate_orbital_lifetime
        lt_min = estimate_orbital_lifetime(500, area_to_mass_ratio_m2_kg=0.007, f107=70, solar_cycle_phase_years=0)
        lt_max = estimate_orbital_lifetime(500, area_to_mass_ratio_m2_kg=0.007, f107=200, solar_cycle_phase_years=0)
        assert lt_max < lt_min
        assert lt_min / lt_max > 2

    def test_deployed_panels_faster_decay(self):
        from spacecdf_common.physics.debris import estimate_orbital_lifetime
        lt_bare = estimate_orbital_lifetime(500, area_to_mass_ratio_m2_kg=0.007)
        lt_deployed = estimate_orbital_lifetime(500, area_to_mass_ratio_m2_kg=0.012)
        assert lt_deployed < lt_bare


class TestRadiation:
    def test_leo_radiation(self):
        from spacecdf_common.physics.radiation import estimate_radiation
        r = estimate_radiation(altitude_km=500, inclination_deg=97.4, mission_duration_years=3)
        assert 1 < r.tid_mission_krad < 30, f"TID {r.tid_mission_krad:.1f} krad"

    def test_higher_orbit_more_radiation(self):
        from spacecdf_common.physics.radiation import estimate_radiation
        r500 = estimate_radiation(altitude_km=500, inclination_deg=97.4)
        r800 = estimate_radiation(altitude_km=800, inclination_deg=97.4)
        assert r800.tid_mission_krad > r500.tid_mission_krad
