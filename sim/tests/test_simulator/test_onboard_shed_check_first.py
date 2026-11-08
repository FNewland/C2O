"""The model behaviour the load-shed cards now rely on (P3, 2026-11-02).

Franz: "if the spacecraft does not shed, the ground should — but check the
spacecraft first". The rewritten cards (CTG-001, CTG-005, CTG-013, CTG-023,
EMG-001, EMG-002) branch on the `eps.pl_*` line states because:

* the EPS sheds on its own, one line each time the bus falls to that line's
  level (2026-11 ruling: payload 28.4, fpa_cooler 27.8, ttc_tx 27.2,
  aocs_wheels 26.5, prop 26.1 V — CTG-001's own branch levels), and publishes
  each line's state (SID 1, 1 Hz) and the shed stage 0x0134;
* a ground shed of a line already open is refused at acceptance (S1.2/0x0004
  "power line ... is OFF"), so the old cards' shed steps could never pass;
* the AOCS collapses to OFF when its line opens and does not restart by
  itself; after EPS_POWER_ON(7) its mode commands are accepted again — which
  is why recovery re-powers the line before AOCS_SET_MODE.
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
    eps = eng.subsystems["eps"]._state
    for ln in ("payload", "fpa_cooler", "ttc_tx", "aocs_wheels"):
        eps.power_lines[ln] = True
    eng.subsystems["aocs"]._state.mode = 3
    for _ in range(3):
        eng._tick_once(1.0)
    return eng


def _shed(engine, soc=62.0):
    # BPX 8S-1P curve: one dead cell (-3.7 V). From 62 % SoC the bus sits near
    # 26.3 V: below the wheels' 26.5 V level (a deep shed, every line open) but
    # above prop / AOCS-safe (26.1 V) and the cascade (25.9 V).
    engine.subsystems["eps"]._state.bat_soc_pct = soc
    engine.subsystems["eps"].inject_failure("bat_cell", 1.0)   # -3.7 V
    for _ in range(10):
        engine._tick_once(1.0)


def test_onboard_shedder_opens_the_lines_and_says_so(engine):
    assert int(engine.params[0x0113]) == 1
    _shed(engine)
    assert engine.params[0x0105] < 26.5
    for pid in (0x0113, 0x0114, 0x0112, 0x0117):      # payload..aocs_wheels
        assert int(engine.params[pid]) == 0, f"0x{pid:04X} not shed"
    assert int(engine.params[0x0134]) >= 3


def test_onboard_shedder_is_tiered(engine):
    """Just under the 28.4 V flag only the payload goes; the rest wait for their level."""
    _shed(engine, soc=80.0)                               # bus ~28.0 V
    assert 27.8 < engine.params[0x0105] < 28.4
    assert int(engine.params[0x0113]) == 0                # payload shed
    for pid in (0x0112, 0x0117):                          # ttc_tx, aocs_wheels kept
        assert int(engine.params[pid]) == 1, f"0x{pid:04X} shed above its level"


def test_ground_shed_of_an_open_line_is_refused(engine):
    _shed(engine)
    gate = engine._dispatcher.check_power_state
    ok, why = gate(8, 1, bytes([26, 0]))               # PAYLOAD_SET_MODE(0)
    assert not ok and "payload" in why and "OFF" in why
    ok, why = gate(8, 1, bytes([67]))                  # TTC_PA_OFF
    assert not ok and "ttc_tx" in why


def test_aocs_needs_its_line_back_before_any_mode_command(engine):
    _shed(engine)
    aocs = engine.subsystems["aocs"]._state
    assert aocs.mode == 0, "AOCS did not collapse to OFF with its line open"
    gate = engine._dispatcher.check_power_state
    ok, _ = gate(8, 1, bytes([0, 2]))                  # AOCS_SET_MODE(2)
    assert not ok
    engine.subsystems["eps"].clear_failure("bat_cell")
    engine._dispatcher._handle_s8(1, bytes([19, 7]))   # EPS_POWER_ON(7)
    for _ in range(3):
        engine._tick_once(1.0)
    assert int(engine.params[0x0117]) == 1
    assert aocs.mode == 0, "the AOCS must not restart by itself"
    ok, why = gate(8, 1, bytes([0, 2]))
    assert ok, why
