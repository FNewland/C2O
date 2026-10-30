"""S19 ea 3003 `tcs_obc_overtemp_safe_mode` puts the OBC into SAFE.

Author ruling (2026-10-30, RULINGS.md §B "Simulator bug fix"): the rule used to
dispatch S8 func 40 (HEATER_BATTERY) with no argument bytes, so an OBC
overtemperature drove the battery heater (or was refused) instead of
commanding OBC_SET_MODE(1). These tests fly the real engine: an injected OBC
overtemperature trips the S12 monitor on 0x0406, ea 3003 fires, the OBC ends
in mode 1 (SAFE) and the battery heater is untouched.
"""
import os
from pathlib import Path

import pytest
import yaml

from smo_simulator.engine import SimulationEngine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


def _rule(ea_id):
    rules = yaml.safe_load(
        (CONFIG_DIR / "monitoring" / "s19_rules.yaml").read_text(encoding="utf-8"))
    return next(r for r in rules["s19_rules"] if r["ea_id"] == ea_id)


def test_rule_3003_is_obc_set_mode_safe():
    rule = _rule(3003)
    assert rule["action_func_id"] == 50            # OBC_SET_MODE
    assert list(rule["action_data"]) == [1]        # mode 1 = SAFE


def test_rule_5004_cpu_overload_is_obc_set_mode_safe():
    rule = _rule(5004)
    assert rule["action_func_id"] == 50
    assert list(rule["action_data"]) == [1]


@pytest.fixture
def engine(tmp_path):
    os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(CONFIG_DIR)
    eng._spacecraft_phase = 6
    eng.subsystems["obdh"]._state.sw_image = 1     # application, not bootloader
    eng.subsystems["obdh"]._state.mode = 0         # NOMINAL
    return eng


def test_injected_obc_overtemp_fires_3003_and_safes_the_obc(engine):
    obdh = engine.subsystems["obdh"]
    tcs = engine.subsystems["tcs"]
    eps = engine.subsystems["eps"]

    htr_before = tcs._state.htr_battery
    line_before = eps._state.power_lines.get("htr_bat")

    fired = []
    dispatch = engine._dispatcher._s19_dispatch

    def spy(ea_id, func_id, action_data=b""):
        fired.append((ea_id, func_id, bytes(action_data)))
        return dispatch(ea_id, func_id, action_data)

    engine._dispatcher._s19_dispatch = spy

    # Reported OBC temperature driven 80 °C over truth: well past the 60 °C
    # S12 red limit on 0x0406 the rule is triggered by.
    tcs.inject_failure("sensor_drift", 80.0, zone="obc")
    for _ in range(10):
        engine._tick_once(1.0)
        if any(f[0] == 3003 for f in fired):
            break

    assert engine.params.get(0x0406, 0) > 60.0
    assert (3003, 50, b"\x01") in fired, fired
    assert obdh._state.mode == 1, "OBC must end in SAFE (mode 1)"
    assert tcs._state.htr_battery == htr_before, "battery heater must not change"
    assert eps._state.power_lines.get("htr_bat") == line_before
