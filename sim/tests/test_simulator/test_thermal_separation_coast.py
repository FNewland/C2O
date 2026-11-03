"""The thermal network runs between separation and first boot (2026-11-03).

Franz's ruling: TCS was not ticked in spacecraft phases 0-1, so the spacecraft
did not cool (or warm) between separation and OBC boot. The network now ticks
in those phases with no electrical dissipation and no heater (separation
switches open), and the bus-powered phases follow as before.
"""
import os
from pathlib import Path

import pytest

from smo_simulator.engine import SimulationEngine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


@pytest.fixture
def engine(tmp_path):
    os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(CONFIG_DIR)
    eng.configure_separation_state()          # phase 1, everything at +20 C
    return eng


def test_network_ticks_during_the_separation_timer(engine):
    tcs = engine.subsystems["tcs"]
    assert engine._spacecraft_phase == 1
    before = {n: tcs.node_temperature(n) for n in ("structure", "payload", "panel_pz")}
    for _ in range(60):
        engine._tick_once(10.0)
    assert engine._spacecraft_phase == 1        # 600 s of the 1800 s timer
    after = {n: tcs.node_temperature(n) for n in before}
    assert any(abs(after[n] - before[n]) > 0.5 for n in before), (before, after)


def test_nothing_is_powered_before_the_timer_expires(engine):
    tcs = engine.subsystems["tcs"]
    eps = engine.subsystems["eps"]
    eps._state.power_lines["htr_bat"] = True    # even a line left ON
    tcs._state.temp_battery = -5.0              # well below the thermostat
    engine._tick_once(10.0)
    assert tcs._state.htr_battery is False
    power, _ = tcs._electrical_inputs(engine.params, {})
    assert all(abs(w) < 1e-9 for w in power), power


def test_obc_dissipates_once_the_bootloader_runs(engine):
    tcs = engine.subsystems["tcs"]
    engine._sep_timer = 5.0
    for _ in range(3):
        engine._tick_once(10.0)
    assert engine._spacecraft_phase >= 2
    idx = tcs._net.index["obc"]
    assert tcs._last_inputs["power"][idx] > 1.0
