"""FPA/imager limits apply only while the payload or its cooler is on.

Franz's ruling of 2026-11-03 (docs/plan_2026-11/REDESIGN_DECISIONS.md,
OBC_THERMAL_ANALYSIS.md §8.5 item 1): with the payload OFF in a long survival
the uncooled imager follows its isolated radiator to -23...-27 C, which raised
the FPA yellow and, in the cold season, the red, on board and on the ground.
The S12 FPA monitors now carry a PUS-C validity condition on 0x0426
`tcs.fpa_limits_valid`, and mcs/limits.yaml the same `valid_when`.
"""
import os
from pathlib import Path

import pytest
import yaml

from smo_simulator.engine import SimulationEngine
from smo_simulator.monitoring_loader import load_s12_definitions

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"
FPA_PIDS = (0x0408, 0x0601)


@pytest.fixture
def engine(tmp_path):
    os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(CONFIG_DIR)
    eng._spacecraft_phase = 6
    eng.subsystems["obdh"]._state.sw_image = 1
    eng.subsystems["obdh"]._state.mode = 0
    return eng


def test_every_fpa_monitor_carries_the_validity_condition():
    defs = [d for d in load_s12_definitions(CONFIG_DIR).values()
            if d["param_id"] in FPA_PIDS]
    assert len(defs) == 3
    for d in defs:
        assert d["validity_param"] == 0x0426, d
        assert d["validity_mask"] == 1 and d["validity_value"] == 1


def test_ground_limits_carry_the_same_condition():
    rows = yaml.safe_load((CONFIG_DIR / "mcs" / "limits.yaml").read_text())["limits"]
    by = {r["param_id"]: r for r in rows}
    for pid in (0x0408, 0x0601, 0x0617):
        vw = by[pid].get("valid_when")
        assert vw == {"param_id": 0x0426, "mask": 1, "value": 1}, pid


def test_validity_flag_follows_payload_and_cooler(engine):
    p = engine.params
    eps = engine.subsystems["eps"]
    tcs = engine.subsystems["tcs"]
    engine._tick_once(1.0)
    assert p[0x0426] == 0                       # payload OFF, cooler off
    eps._state.power_lines["payload"] = True
    engine.subsystems["payload"].handle_command({"command": "set_mode", "mode": 1})
    for _ in range(2):
        engine._tick_once(1.0)
    assert p[0x0426] == 1                       # payload powered
    engine.subsystems["payload"].handle_command({"command": "set_mode", "mode": 0})
    eps._state.power_lines["fpa_cooler"] = True
    tcs._state.cooler_fpa = True
    for _ in range(2):
        engine._tick_once(1.0)
    assert p[0x0426] == 1                       # cooler running alone


def _entered(engine):
    out = []
    orig = engine._emit_s12_transition

    def spy(violation, entered=True):
        if entered:
            out.append(violation["param_id"])
        return orig(violation, entered=entered)
    engine._emit_s12_transition = spy
    return out


def test_cold_unpowered_imager_raises_no_fpa_monitor(engine):
    """Survival: payload and cooler off, imager at -27 C."""
    entered = _entered(engine)
    tcs = engine.subsystems["tcs"]
    for _ in range(5):
        tcs._state.temp_fpa = -27.0
        engine.subsystems["payload"]._state.fpa_temp = -27.5
        engine._tick_once(1.0)
    assert engine.params[0x0426] == 0
    assert engine.params[0x0408] < -25.5
    assert not [pid for pid in entered if pid in FPA_PIDS], entered


def test_cold_fpa_with_the_payload_on_is_still_reported(engine):
    """The same temperature with the payload powered is a real anomaly."""
    entered = _entered(engine)
    eps = engine.subsystems["eps"]
    eps._state.power_lines["payload"] = True
    engine.subsystems["payload"].handle_command({"command": "set_mode", "mode": 1})
    tcs = engine.subsystems["tcs"]
    for _ in range(5):
        tcs._state.temp_fpa = -27.0
        engine._tick_once(1.0)
    assert engine.params[0x0426] == 1
    assert 0x0408 in entered


def test_payload_events_follow_the_same_rule():
    """FPA_UNDERTEMP needs a powered or regulated detector; FPA_OVERTEMP
    needs cooled operation (the cooler is off in STANDBY, so the FPA warms
    through -3 C after every imaging session)."""
    import queue
    from types import SimpleNamespace
    from smo_simulator.models.payload_basic import PayloadBasicModel
    m = PayloadBasicModel()
    m.configure({})
    q = queue.Queue()
    m._engine = SimpleNamespace(_model_event_queue=q)
    orbit = SimpleNamespace(in_eclipse=False, lat_deg=0.0, lon_deg=0.0,
                            alt_km=513.0, solar_beta_deg=-30.0)

    def crossing(mode, cooler, t_prev, t_now):
        s = m._state
        s.mode, s.cooler_active = mode, cooler
        s.prev_fpa_temp, s.fpa_temp = t_prev, t_now
        while not q.empty():
            q.get_nowait()
        m.tick(1.0, orbit, {0x0408: t_now})
        out = []
        while not q.empty():
            out.append(q.get_nowait()["event_id"])
        return out

    assert 0x0604 not in crossing(1, False, -4.0, -2.0)   # STANDBY warm-up
    assert 0x0604 in crossing(2, False, -4.0, -2.0)       # IMAGING, cooler lost
    assert 0x0605 not in crossing(0, False, -20.0, -25.0)  # unpowered imager
    assert 0x0605 in crossing(1, False, -20.0, -25.0)      # powered detector
