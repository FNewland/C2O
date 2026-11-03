"""Thermal network (2026-11) — docs/plan_2026-11/THERMAL_MODEL.md.

Unit tests of smo_simulator.models.thermal_network and of its wiring into
TCSBasicModel:

  * energy conservation in an adiabatic network (no surfaces): the stored
    energy changes by exactly the dissipated energy, and a closed network
    with no input keeps its energy while equalising;
  * steady state against a hand calculation (two-node radiator, and the
    flat-plate Earth view factor's closed forms and continuity);
  * eclipse cooling: the same spacecraft is colder in umbra than in sun;
  * dissipation coupling: what EPS bills a line heats the node it feeds,
    so switching a load off cools the spacecraft;
  * heater recovery: a cold-soaked zone is recovered by its heater;
  * stability at the maximum time acceleration (engine speed.max).
"""
import math
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = REPO_ROOT / "configs" / "eosat1"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from smo_simulator.models import thermal_network as tn  # noqa: E402
from smo_simulator.models.tcs_basic import TCSBasicModel  # noqa: E402

SIGMA = tn.SIGMA


def _two_node(g=0.5, surfaces=()):
    spec = {"nodes": [{"name": "a", "capacitance_j_per_k": 400.0, "initial_c": 40.0},
                      {"name": "b", "capacitance_j_per_k": 900.0, "initial_c": -10.0}],
            "conductors": [{"a": "a", "b": "b", "g_w_per_k": g}],
            "radiative": [{"a": "a", "b": "b", "ea_m2": 0.02}],
            "surfaces": list(surfaces)}
    net, init = tn.build_network(spec)
    return net, tn.NetworkSolver(net, init)


class TestConservation:
    def test_closed_network_conserves_energy_while_equalising(self):
        net, sol = _two_node()
        e0 = sol.energy_j()
        for _ in range(500):
            sol.step(60.0, [0.0, 0.0], [0.0, 0.0], [0.0, 0.0])
        assert sol.energy_j() == pytest.approx(e0, rel=1e-12)
        # ...and equalised at the capacity-weighted mean
        t_mean = (400 * 40.0 + 900 * -10.0) / 1300.0
        assert sol.temp_c("a") == pytest.approx(t_mean, abs=0.01)
        assert sol.temp_c("b") == pytest.approx(t_mean, abs=0.01)

    def test_adiabatic_dissipation_goes_entirely_into_storage(self):
        net, sol = _two_node()
        e0 = sol.energy_j()
        p = [7.0, 3.0]
        for _ in range(100):
            sol.step(30.0, [0.0, 0.0], [0.0, 0.0], p)
        assert sol.energy_j() - e0 == pytest.approx(10.0 * 3000.0, rel=1e-9)

    def test_radiated_energy_closes_the_balance(self):
        surf = [{"node": "a", "normal": [1, 0, 0], "area_m2": 0.05,
                 "alpha": 0.5, "epsilon": 0.8}]
        net, sol = _two_node(surfaces=surf)
        e0 = sol.energy_j()
        q_abs, p = [12.0, 0.0], [0.0, 4.0]
        ea = [0.8 * 0.05, 0.0]
        rad = sum(sol.step(20.0, q_abs, ea, p) for _ in range(300))
        assert sol.energy_j() - e0 == pytest.approx(16.0 * 6000.0 - rad, rel=1e-9)


class TestSteadyState:
    def test_radiator_node_matches_hand_calculation(self):
        """One node, P = 10 W into a 0.1 m2 eps 0.8 radiator, behind a
        0.5 W/K link: T_rad^4 = P / (eps A sigma); T_int = T_rad + P/G."""
        spec = {"nodes": [{"name": "rad", "capacitance_j_per_k": 200.0, "initial_c": 0.0},
                          {"name": "box", "capacitance_j_per_k": 300.0, "initial_c": 0.0}],
                "conductors": [{"a": "rad", "b": "box", "g_w_per_k": 0.5}],
                "surfaces": [{"node": "rad", "normal": [0, 0, 1], "area_m2": 0.1,
                              "alpha": 0.2, "epsilon": 0.8}]}
        net, init = tn.build_network(spec)
        sol = tn.NetworkSolver(net, init)
        ea = [0.08, 0.0]
        for _ in range(3000):
            sol.step(30.0, [0.0, 0.0], ea, [0.0, 10.0])
        t_rad = (10.0 / (0.08 * SIGMA)) ** 0.25 - 273.15
        assert sol.temp_c("rad") == pytest.approx(t_rad, abs=0.05)
        assert sol.temp_c("box") == pytest.approx(t_rad + 10.0 / 0.5, abs=0.05)

    @pytest.mark.parametrize("alt_km", [400.0, 513.0, 800.0])
    def test_view_factor_closed_forms_and_continuity(self, alt_km):
        H = (6378.137 + alt_km) / 6378.137
        # nadir-facing plate sees (R/(R+h))^2; zenith-facing sees nothing
        assert tn.plate_earth_view_factor(1.0, H) == pytest.approx(1.0 / H ** 2)
        assert tn.plate_earth_view_factor(-1.0, H) == 0.0
        rho = math.asin(1.0 / H)
        for edge in (0.5 * math.pi - rho, 0.5 * math.pi + rho):
            lo = tn.plate_earth_view_factor(math.cos(edge - 1e-6), H)
            hi = tn.plate_earth_view_factor(math.cos(edge + 1e-6), H)
            assert lo == pytest.approx(hi, abs=1e-4)
        # monotone in the angle
        vals = [tn.plate_earth_view_factor(math.cos(math.radians(a)), H)
                for a in range(0, 181, 5)]
        assert all(x >= y - 1e-12 for x, y in zip(vals, vals[1:]))

    def test_orientation_average_matches_the_sphere_value(self):
        """Mean over random orientations of the plate view factor equals
        (1 - cos rho) / 2 (0.311 at 513 km, OBC_THERMAL_ANALYSIS §4.4)."""
        H = (6378.137 + 513.0) / 6378.137
        n = 20000
        # uniform on the sphere: cos(theta) uniform in [-1, 1]
        mean = sum(tn.plate_earth_view_factor(-1.0 + 2.0 * (i + 0.5) / n, H)
                   for i in range(n)) / n
        assert mean == pytest.approx(tn.tumbling_earth_view_factor(H), rel=2e-3)
        assert tn.tumbling_earth_view_factor(H) == pytest.approx(0.311, abs=0.002)

    def test_unknown_keys_and_nodes_are_rejected(self):
        with pytest.raises(ValueError, match="unknown key"):
            tn.build_network({"nodes": [{"name": "a", "capacitance_j_per_k": 1,
                                         "colour": "red"}]})
        with pytest.raises(ValueError, match="unknown node"):
            tn.build_network({"nodes": [{"name": "a", "capacitance_j_per_k": 1}],
                              "conductors": [{"a": "a", "b": "zz", "g_w_per_k": 1}]})


# ── TCS wiring ─────────────────────────────────────────────────────────────

class _Orbit:
    def __init__(self, eclipse=False):
        self.in_eclipse = eclipse
        self.solar_beta_deg = -30.0


def _tcs():
    cfg = yaml.safe_load((CONFIG_DIR / "subsystems" / "tcs.yaml").read_text())
    sim = yaml.safe_load((CONFIG_DIR / "simulation.yaml").read_text())
    cfg["simulation"] = sim["tcs"]
    m = TCSBasicModel()
    m.configure(cfg)
    return m


def _params(load_w=None, bus_v=28.0):
    """EPS-like parameters: per-line currents for the given line powers."""
    load_w = load_w or {}
    ids = TCSBasicModel._LINE_CURRENT_IDS
    p = {0x0105: bus_v}
    for line, pid in ids.items():
        p[pid] = load_w.get(line, 0.0) / bus_v
    p[0x0106] = sum(load_w.values())
    p[0x0109] = 0.0
    return p


ORBIT_S, ECL_FRAC = 5670.0, 0.36


def _run(m, seconds, params, orbit, dt=10.0, t0=0.0, eclipse_cycle=False):
    for i in range(int(seconds / dt)):
        if eclipse_cycle:
            orbit.in_eclipse = ((t0 + i * dt) % ORBIT_S) > (1 - ECL_FRAC) * ORBIT_S
        m.tick(dt, orbit, params)


class TestTCSWiring:
    NOMINAL = {"obc": 6.0, "ttc_rx": 1.5, "aocs_wheels": 9.0, "payload": 2.4}

    def test_eclipse_cools_the_spacecraft(self):
        sun, ecl = _tcs(), _tcs()
        _run(sun, 6 * 3600, _params(self.NOMINAL), _Orbit(False))
        _run(ecl, 6 * 3600, _params(self.NOMINAL), _Orbit(True))
        for node in ("structure", "obc", "panel_px", "payload"):
            assert ecl.node_temperature(node) < sun.node_temperature(node) - 10.0, node

    def test_dissipation_heats_the_node_that_draws_it(self):
        """Load shed really cools: dropping the AOCS + payload lines (11.4 W)
        cools the AOCS node and the structure; the OBC (still powered) cools
        only by following the structure."""
        on, off = _tcs(), _tcs()
        _run(on, 8 * 3600, _params(self.NOMINAL), _Orbit(False))
        _run(off, 8 * 3600, _params({"obc": 6.0, "ttc_rx": 1.5}), _Orbit(False))
        d_struct = on.node_temperature("structure") - off.node_temperature("structure")
        d_aocs = on.node_temperature("aocs") - off.node_temperature("aocs")
        d_obc = on.node_temperature("obc") - off.node_temperature("obc")
        assert d_struct > 5.0
        assert d_aocs > d_struct + 5.0          # 9 W through its 1 W/K mount
        assert d_obc == pytest.approx(d_struct, abs=1.5)

    def test_obc_self_heating_matches_its_mount_conductance(self):
        """Hand check: the OBC node sits P_obc / (G + 4 eps A sigma T^3)
        above the structure in steady state (3 W across 0.6 W/K + its
        internal radiation)."""
        m = _tcs()
        _run(m, 10 * 3600, _params(self.NOMINAL), _Orbit(False))
        t_s = m.node_temperature("structure") + 273.15
        t_o = m.node_temperature("obc") + 273.15
        g_rad = 4.0 * 0.01 * SIGMA * ((t_s + t_o) / 2.0) ** 3
        assert (t_o - t_s) == pytest.approx(3.0 / (0.6 + g_rad), rel=0.03)

    def test_heater_recovers_a_cold_soak(self):
        m = _tcs()
        p = _params(self.NOMINAL)
        orbit = _Orbit(False)
        _run(m, 6 * 3600, p, orbit, eclipse_cycle=True)
        m.inject_failure("cold_soak", zone="battery")
        assert m._state.cold_soak["battery"] == m._soak_default["battery"]
        _run(m, 4 * 3600, p, orbit, eclipse_cycle=True)   # line 5 dark
        cold = m.node_temperature("battery")
        p[0x0115] = 1                           # heater line ON (thermostat)
        _run(m, 4 * 3600, p, orbit, eclipse_cycle=True)
        warm = m.node_temperature("battery")
        assert cold < 0.0
        assert warm > cold + 15.0
        assert warm >= m._state.htr_battery_setpoint_on_c - 1.0

    def test_open_circuit_heater_bills_but_does_not_heat(self):
        a, b = _tcs(), _tcs()
        for m in (a, b):
            m._state.htr_obc_manual = True
            m._state.htr_obc = True
        b.inject_failure("heater_open_circuit", circuit="obc")
        p = _params(self.NOMINAL)
        p[0x0116] = 1
        _run(a, 3 * 3600, dict(p), _Orbit(False))
        _run(b, 3 * 3600, dict(p), _Orbit(False))
        assert a.node_temperature("obc") > b.node_temperature("obc") + 4.0

    def test_published_parameters_follow_the_network(self):
        m = _tcs()
        p = _params(self.NOMINAL)
        _run(m, 3600, p, _Orbit(False))
        assert p[0x0406] == pytest.approx(m.node_temperature("obc"), abs=0.5)
        assert p[0x0407] == pytest.approx(m.node_temperature("battery"), abs=0.5)
        assert p[0x0400] == pytest.approx(m.node_temperature("panel_px"), abs=0.5)


class TestStability:
    def test_large_steps_are_substepped_and_agree_with_small_steps(self):
        fine, coarse = _tcs(), _tcs()
        p1, p2 = _params(TestTCSWiring.NOMINAL), _params(TestTCSWiring.NOMINAL)
        _run(fine, 4 * 3600, p1, _Orbit(False), dt=1.0)
        _run(coarse, 4 * 3600, p2, _Orbit(False), dt=600.0)
        assert coarse._solver.last_substeps > 1
        for node in ("structure", "obc", "battery", "panel_px", "wing_py"):
            assert coarse.node_temperature(node) == pytest.approx(
                fine.node_temperature(node), abs=0.3), node

    def test_engine_at_maximum_time_acceleration(self):
        """speed.max (1000x) at 1 Hz: dt_sim = 1000 s per outer tick, which
        the engine cuts into ceil(1000 / dt_max_s) sub-steps (capped at
        max_substeps). Nothing may blow up or oscillate, and the temperatures
        must stay physical."""
        import logging
        import os
        import tempfile
        os.environ.setdefault("SMO_DUMP_DIR", tempfile.mkdtemp())
        logging.disable(logging.WARNING)
        try:
            from smo_simulator.engine import SimulationEngine
            fast = SimulationEngine(CONFIG_DIR)
            ref = SimulationEngine(CONFIG_DIR)
            speed = float(fast._speed_max)
            n_outer = int(2 * 5670 / speed) + 1
            for eng in (fast, ref):
                eng._spacecraft_phase = 6
            for _ in range(n_outer):
                fast._tick_once(speed)         # 1 s of wall time at speed.max
            for _ in range(int(n_outer * speed / 10.0)):
                ref._tick_once(10.0)           # the same sim time at 10x
            tf, tr = fast.subsystems["tcs"], ref.subsystems["tcs"]
            for name in tf._net.names:
                t = tf.node_temperature(name)
                assert -120.0 < t < 150.0, (name, t)
                assert t == pytest.approx(tr.node_temperature(name), abs=1.0), name
        finally:
            logging.disable(logging.NOTSET)
