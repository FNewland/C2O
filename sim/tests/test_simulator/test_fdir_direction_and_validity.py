"""FDIR fixes of 2026-11-03 (docs/plan_2026-11/OBC_THERMAL_ANALYSIS.md §3.3).

1. S19 ea 3003 "OBC overtemp -> OBC SAFE" fired on the LOW limit of the S12
   monitor on 0x0406 too, so every OBC cold soak safed the OBC. Param rules
   are now armed on one side (`trigger.limit`); the cold crossing is still
   reported to the ground (TM(12,9) + S5 0x9406).
2. The battery-cold FDIR response sent HEATER ON (manual), bypassing the
   thermostat for good. It now returns the heater to thermostat control, and
   the battery-overtemp response hands the heater back to the thermostat when
   it releases (`on_clear`).
3. S19 ea 1004/1005 "solar array degraded" fired at every eclipse entry. They
   now watch string-yield monitors that are only checked while the string is
   lit (PUS-C validity) with a 30-check repetition; a genuine array failure in
   sunlight still fires them.
"""
import os
from pathlib import Path

import pytest
import yaml

from smo_simulator.engine import SimulationEngine
from smo_simulator.monitoring_loader import (
    TRIGGER_KIND_PARAM, load_s12_definitions, load_s19_rules,
)

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


@pytest.fixture
def engine(tmp_path):
    os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(CONFIG_DIR)
    eng._spacecraft_phase = 6
    eng.subsystems["obdh"]._state.sw_image = 1     # application
    eng.subsystems["obdh"]._state.mode = 0         # NOMINAL
    return eng


def _spy_s19(engine):
    fired = []
    dispatch = engine._dispatcher._s19_dispatch

    def spy(ea_id, func_id, action_data=b""):
        fired.append(ea_id)
        return dispatch(ea_id, func_id, action_data)

    engine._dispatcher._s19_dispatch = spy
    return fired


def _spy_s12_entries(engine):
    entered = []
    orig = engine._emit_s12_transition

    def spy(violation, entered_flag=None, **kw):
        flag = kw.get("entered", entered_flag)
        if flag:
            entered.append((violation["param_id"], violation.get("limit")))
        return orig(violation, entered=flag)

    engine._emit_s12_transition = spy
    return entered


# ── 1. OBC cold soak must not safe the OBC ─────────────────────────────

def test_one_sided_rules_are_armed_on_the_high_limit():
    rules = load_s19_rules(CONFIG_DIR)
    for ea_id in (3001, 3002, 3003, 4002, 6002):
        assert rules[ea_id]["trigger_kind"] == TRIGGER_KIND_PARAM
        assert rules[ea_id]["trigger_limit"] == "high", ea_id


def test_obc_cold_soak_does_not_fire_3003_or_safe_the_obc(engine):
    obdh = engine.subsystems["obdh"]
    tcs = engine.subsystems["tcs"]
    fired = _spy_s19(engine)
    entered = _spy_s12_entries(engine)

    # Reported OBC temperature 80 C below truth: under any plausible S12 low
    # limit on 0x0406 (the limits themselves are owned by the TCS work).
    tcs.inject_failure("sensor_drift", -80.0, zone="obc")
    for _ in range(20):
        engine._tick_once(1.0)

    assert engine.params[0x0406] < -40.0
    assert (0x0406, "low") in entered, "cold OBC must still be reported (TM(12,9))"
    assert 3003 not in fired, fired
    assert obdh._state.mode == 0, "a cold OBC must not be put in SAFE"


def test_obc_overtemp_still_fires_3003(engine):
    fired = _spy_s19(engine)
    engine.subsystems["tcs"].inject_failure("sensor_drift", 80.0, zone="obc")
    for _ in range(10):
        engine._tick_once(1.0)
    assert 3003 in fired
    assert engine.subsystems["obdh"]._state.mode == 1


def test_cold_battery_does_not_switch_the_transmitter_off(engine):
    """Same bug class: ea 3002 (battery OVERtemp -> TX off) also fired on
    the -10 C low limit of the 0x0407 monitor."""
    fired = _spy_s19(engine)
    engine.subsystems["tcs"].inject_failure("sensor_drift", -40.0, zone="battery")
    for _ in range(10):
        engine._tick_once(1.0)
    assert engine.params[0x0407] < -10.0
    assert 3002 not in fired, fired


def test_untagged_limit_is_still_two_sided():
    """`trigger.limit` omitted = either side (wheel overspeed is ±)."""
    rules = load_s19_rules(CONFIG_DIR)
    assert rules[2005]["trigger_limit"] == "any"


# ── 2. Battery-cold response leaves the heater under its thermostat ───

def test_battery_cold_fdir_returns_heater_to_thermostat(engine):
    tcs = engine.subsystems["tcs"]
    eps = engine.subsystems["eps"]
    eps._state.power_lines["htr_bat"] = True
    # Heater left in MANUAL OFF (by the ground, or an earlier overtemp).
    assert tcs.handle_command({"command": "heater", "circuit": "battery",
                               "on": False})["success"]
    assert tcs._state.htr_battery_manual

    # Battery reads well below the +1 C FDIR threshold.
    tcs.inject_failure("sensor_drift", -30.0, zone="battery")
    for _ in range(5):
        engine._tick_once(1.0)
    assert engine._fdir_triggered.get("tcs.temp_battery_heater_auto_battery")
    assert not tcs._state.htr_battery_manual, "FDIR must hand back to the thermostat"

    # Condition clears: the heater stays in AUTO — nothing latched manual.
    tcs.inject_failure("sensor_drift", 0.0, zone="battery")
    for _ in range(5):
        engine._tick_once(1.0)
    assert not engine._fdir_triggered.get("tcs.temp_battery_heater_auto_battery")
    assert not tcs._state.htr_battery_manual


def test_battery_cold_response_never_forces_manual_on(engine):
    rules = engine._fdir_rules
    cold = [r for r in rules if r.parameter == "tcs.temp_battery"
            and r.condition.strip().startswith("<")]
    assert cold and all(r.action == "heater_auto_battery" for r in cold)
    assert not any(r.action == "heater_on_battery" for r in rules)


def test_battery_overtemp_response_releases_to_thermostat(engine):
    tcs = engine.subsystems["tcs"]
    engine.subsystems["eps"]._state.power_lines["htr_bat"] = True
    tcs.inject_failure("sensor_drift", 45.0, zone="battery")
    for _ in range(5):
        engine._tick_once(1.0)
    assert engine.params[0x0407] > 42.0
    assert tcs._state.htr_battery_manual and not tcs._state.htr_battery

    tcs.inject_failure("sensor_drift", 0.0, zone="battery")
    for _ in range(5):
        engine._tick_once(1.0)
    assert not tcs._state.htr_battery_manual, \
        "on_clear must return the heater to thermostat control"


# ── 3. Solar-array-degraded rules: sunlit only ─────────────────────────

def test_sa_rules_watch_lit_only_yield_monitors():
    rules = load_s19_rules(CONFIG_DIR)
    defs = load_s12_definitions(CONFIG_DIR)
    for ea_id, pid, bit in ((1004, 0x014C, 0x1), (1005, 0x014D, 0x2)):
        r = rules[ea_id]
        assert (r["trigger_kind"], r["event_type"], r["trigger_limit"]) == \
            (TRIGGER_KIND_PARAM, pid, "low")
        assert r["action_func_id"] == 20 and r["action_data"] == [3]
        mons = [d for d in defs.values() if d["param_id"] == pid]
        assert len(mons) == 1
        m = mons[0]
        assert m["validity_param"] == 0x014E
        assert m["validity_mask"] == bit and m["validity_value"] == bit
        assert m["repetition"] >= 10
    # Nothing watches the raw string currents any more.
    assert not [d for d in defs.values() if d["param_id"] in (0x0103, 0x0104)]


def _run_until(engine, pred, limit_s):
    for _ in range(int(limit_s)):
        engine._tick_once(1.0)
        if pred():
            return True
    return False


def test_eclipse_does_not_fire_1004_1005(engine):
    fired = _spy_s19(engine)
    # Sun -> eclipse -> sun: run through the first eclipse into sunlight.
    assert _run_until(engine, lambda: engine.params.get(0x0108) == 1, 6000)
    assert _run_until(engine, lambda: engine.params.get(0x0108) == 0, 3000)
    for _ in range(120):
        engine._tick_once(1.0)
    assert not {1004, 1005} & set(fired), fired
    # The monitors really were checked in sunlight (validity bit set).
    assert int(engine.params.get(0x014E, 0)) != 0


def test_injected_array_degradation_in_sun_fires_1004(engine):
    fired = _spy_s19(engine)
    eps = engine.subsystems["eps"]
    assert _run_until(engine, lambda: int(engine.params.get(0x014E, 0)) & 1
                      and engine.params.get(0x0108) == 0, 6000)
    eps._state.power_lines["payload"] = True
    eps.inject_failure("solar_array_partial", 0.6, array="A")
    assert _run_until(engine, lambda: 1004 in fired, 120), \
        "string A at 40 % yield in sunlight must trip ea 1004"
    assert 1005 not in fired
    assert engine.params[0x014C] < 70.0
    assert eps._state.power_lines["payload"] is False, "load shed: payload line OFF"


def test_s12_validity_and_repetition_unit(engine):
    """Dispatcher-level: unchecked while invalid, reports only after N."""
    d = engine._dispatcher
    d._s12_definitions = {0x7F00: {
        'mon_id': 0x7F00, 'param_id': 0x0F70, 'check_type': 0,
        'low_limit': 10.0, 'high_limit': 20.0, 'enabled': True,
        'last_value': None, 'severity': 'WARNING', 'name': 't',
        'description': '', 'repetition': 3, 'rep_count': 0,
        'validity_param': 0x0F71, 'validity_mask': 0x1, 'validity_value': 0x1,
    }}
    engine.params[0x0F70] = 0.0
    engine.params[0x0F71] = 0
    assert d.check_monitoring() == []            # invalid -> unchecked
    engine.params[0x0F71] = 1
    assert d.check_monitoring() == []            # 1st out-of-limit check
    assert d.check_monitoring() == []            # 2nd
    v = d.check_monitoring()                     # 3rd -> reported
    assert len(v) == 1 and v[0]["limit"] == "low"
    engine.params[0x0F70] = 15.0
    assert d.check_monitoring() == []
    engine.params[0x0F70] = 25.0
    assert d.check_monitoring() == [] and d.check_monitoring() == []
    assert d.check_monitoring()[0]["limit"] == "high"
