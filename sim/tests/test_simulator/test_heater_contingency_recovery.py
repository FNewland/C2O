"""A forced-cold zone recovers once its heater LINE is powered (P1).

Walkthrough finding P1 (2026-11-02): heater lines 5/6/8 are OFF after
commissioning, so every `HEATER_*_ON` in EMG-001/002/003 was refused S1.8
"EPS power line N is OFF", and with the battery line dark the battery drifted
into the red in nominal operations.

Franz: "in a contingency situation can we switch them on, if we force the
temperature cold?" Pinned here, on the full engine:

* the instructor `cold_soak` failure really cools a heated zone (a physical
  sink offset, not a sensor offset), so the thermostat sees it;
* with the line dark `HEATER_BATTERY(on=1)` is refused, exactly as the cards
  used to hit it;
* `EPS_POWER_ON(line_index=5)` first, then the heater: the battery climbs back
  through the thermostat band; the same for the OBC (line 6);
* with line 5 left ON in AUTO (the new post-commissioning state, COM-002) the
  thermostat alone holds a cold-soaked battery above its +5 C ON setpoint —
  no ground action at all.
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
    eng._spacecraft_phase = 6
    eng.subsystems["obdh"]._state.sw_image = 1
    eng.subsystems["obdh"]._state.mode = 0
    eps = eng.subsystems["eps"]
    eps._state.power_lines["htr_bat"] = False
    eps._state.power_lines["htr_obc"] = False
    return eng


def _run(eng, seconds, dt=10.0):
    for _ in range(int(seconds / dt)):
        eng._tick_once(dt)


def _s8(eng, *data):
    return eng._dispatcher._handle_s8(1, bytes(data))


def test_cold_soak_is_physical_not_a_sensor_offset(engine):
    tcs = engine.subsystems["tcs"]
    _run(engine, 60)
    t0 = tcs._state.temp_battery
    # Through the instructor's failure manager, as the console injects it.
    engine._failure_manager.inject("tcs", "cold_soak", zone="battery",
                                   offset_c=-25.0)
    _run(engine, 60)
    assert tcs._state.temp_battery < t0 - 15.0
    assert "battery" not in tcs._state.sensor_drift


def test_battery_heater_refused_until_its_line_is_powered_then_recovers(engine):
    tcs = engine.subsystems["tcs"]
    _run(engine, 30)
    tcs.inject_failure("cold_soak", zone="battery", offset_c=-25.0)
    _run(engine, 600)
    cold = tcs._state.temp_battery
    assert cold < 5.0, f"cold soak did not make the battery cold ({cold:.1f} C)"

    # The old card: heater ON with line 5 dark -> refused, nothing heats.
    _s8(engine, 40, 1)
    _run(engine, 20)
    assert tcs._state.htr_battery is False
    assert int(engine.params.get(0x0115, 0)) == 0

    # The new card: EPS_POWER_ON(line_index=5) first, check, then the heater.
    _s8(engine, 19, 5)
    _run(engine, 20)
    assert int(engine.params.get(0x0115, 0)) == 1
    _s8(engine, 40, 1)
    _run(engine, 20)
    assert tcs._state.htr_battery is True
    _run(engine, 3600)
    assert tcs._state.temp_battery > cold + 8.0, (
        f"battery did not recover: {cold:.1f} -> {tcs._state.temp_battery:.1f} C")


def test_obc_heater_same_story_on_line_6(engine):
    tcs = engine.subsystems["tcs"]
    _run(engine, 30)
    # The 4 W OBC heater has ~4.5 K of authority (UA = 800 J/K / 900 s), so
    # it can only claw back a few kelvin: that is the physics, not a bug.
    tcs.inject_failure("cold_soak", zone="obc", offset_c=-10.0)
    _run(engine, 2700)
    cold = tcs._state.temp_obc
    _s8(engine, 41, 1)
    _run(engine, 10)
    assert tcs._state.htr_obc is False
    _s8(engine, 19, 6)
    _run(engine, 20)
    _s8(engine, 41, 1)
    _run(engine, 20)
    assert tcs._state.htr_obc is True
    _run(engine, 2700)
    assert tcs._state.temp_obc > cold + 2.5


def test_line_on_in_auto_holds_the_battery_without_ground_action(engine):
    """The post-commissioning state (COM-002 exit): lines 5/6 ON, heaters in
    AUTO. A cold soak the heater has authority over never takes the battery
    below its thermostat band."""
    tcs = engine.subsystems["tcs"]
    _s8(engine, 19, 5)
    _s8(engine, 45, 0)                       # HEATER_AUTO_MODE(circuit=0)
    _run(engine, 30)
    tcs.inject_failure("cold_soak", zone="battery", offset_c=-15.0)
    tcs._state.temp_battery = 3.0            # start below the ON setpoint
    _run(engine, 4 * 3600)
    assert tcs._state.htr_battery_manual is False
    assert tcs._state.temp_battery > 4.0, (
        f"thermostat lost the battery: {tcs._state.temp_battery:.1f} C")
