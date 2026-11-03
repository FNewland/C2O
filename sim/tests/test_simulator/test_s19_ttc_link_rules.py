"""S19 ea 4001 / 4003 fire on what the spacecraft can really observe.

Author ruling (2026-11-01, RULINGS.md "Plan decisions"): the two TTC autonomy
rules used to trigger on S12 violations of 0x0503 link margin and 0x050C BER.
Both are ground-receiver quantities (``visibility: ground_derived``); the
spacecraft has no S12 monitor on either, so neither rule could ever fire.

They are now retriggered on on-board observables:

* ea 4001 — event 0x0513 UPLINK_LOCK_DROPOUT (carrier lock lost and regained
  within 60 s, i.e. a fade mid-pass) -> TTC_SET_TX_POWER level 2 (HIGH);
* ea 4003 — event 0x0514 CMD_LOSS_TIMEOUT (no telecommand accepted for
  ttc.yaml ``cmd_loss_switch_timeout_s`` = 24 h, timer 0x053D) ->
  TTC_SWITCH_OTHER (FDIR TTC-01). Since 2026-11-02 the switch goes both
  ways: the timer re-arms after each expiry and toggles to whichever unit is
  not selected, so a dead REDUNDANT unit is switched away from too.

These tests fly the real engine end to end: model -> S5 event -> S19 -> S8.
"""
import os
from pathlib import Path

import pytest
import yaml

from smo_simulator.engine import SimulationEngine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


def _yaml(rel):
    return yaml.safe_load((CONFIG_DIR / rel).read_text(encoding="utf-8"))


def _rule(ea_id):
    return next(r for r in _yaml("monitoring/s19_rules.yaml")["s19_rules"]
                if r["ea_id"] == ea_id)


def _event_ids():
    return {int(e["id"]) for e in _yaml("events/event_catalog.yaml")["events"]}


# ── static shape ────────────────────────────────────────────────────────

def test_4001_is_uplink_dropout_to_tx_power_high():
    rule = _rule(4001)
    assert rule["trigger"] == {"kind": "event", "id": 0x0513}
    assert rule["action_func_id"] == 68            # TTC_SET_TX_POWER
    assert list(rule["action_data"]) == [2]        # level 2 = HIGH (5 W)
    assert 0x0513 in _event_ids()


def test_4003_is_cmd_loss_timer_to_switch_other():
    rule = _rule(4003)
    assert rule["trigger"] == {"kind": "event", "id": 0x0514}
    assert rule["action_func_id"] == 99            # TTC_SWITCH_OTHER
    assert not rule.get("action_data")             # the command takes no args
    assert 0x0514 in _event_ids()


def test_neither_rule_watches_a_ground_derived_parameter():
    params = {int(p["id"]): p for p in
              _yaml("telemetry/parameters.yaml")["parameters"]}
    for ea in (4001, 4003):
        trig = _rule(ea)["trigger"]
        if trig["kind"] == "param":
            assert params[int(trig["id"])].get("visibility", "real") == "real"


def test_cmd_loss_timer_parameter_is_catalogued_and_real():
    params = {int(p["id"]): p for p in
              _yaml("telemetry/parameters.yaml")["parameters"]}
    p = params[0x053D]
    assert p["name"] == "ttc.time_since_last_tc"
    assert p.get("visibility", "real") == "real"
    assert _yaml("subsystems/ttc.yaml")["cmd_loss_switch_timeout_s"] == 86400


# ── real engine ─────────────────────────────────────────────────────────

@pytest.fixture
def engine(tmp_path):
    os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(CONFIG_DIR)
    eng._spacecraft_phase = 6
    eng.subsystems["obdh"]._state.sw_image = 1     # application
    eng.subsystems["obdh"]._state.mode = 0
    fired = []
    dispatch = eng._dispatcher._s19_dispatch

    def spy(ea_id, func_id, action_data=b""):
        fired.append((ea_id, func_id, bytes(action_data)))
        return dispatch(ea_id, func_id, action_data)

    eng._dispatcher._s19_dispatch = spy
    eng._fired = fired
    return eng


def _tick_until(eng, pred, limit):
    for _ in range(limit):
        eng._tick_once(1.0)
        if pred():
            return True
    return False


def _in_pass(eng):
    eng._override_passes = True
    eng.params[0x05FF] = 1


def test_mid_pass_uplink_dropout_fires_4001_and_boosts_tx(engine):
    ttc = engine.subsystems["ttc"]
    _in_pass(engine)
    assert _tick_until(engine, lambda: ttc._state.carrier_lock, 60), \
        "carrier lock never acquired with the pass override on"
    assert ttc._pa_nominal_power_w == pytest.approx(2.0)

    # A fade: lock drops for a few seconds, then comes back in the same pass.
    ttc.inject_failure("uplink_loss")
    _tick_until(engine, lambda: False, 5)
    assert not ttc._state.carrier_lock
    assert not any(f[0] == 4001 for f in engine._fired), \
        "the loss alone must not fire: LOS looks exactly the same on board"
    ttc.clear_failure("uplink_loss")
    assert _tick_until(engine, lambda: any(f[0] == 4001 for f in engine._fired),
                       30), engine._fired

    assert (4001, 68, b"\x02") in engine._fired
    assert ttc._pa_nominal_power_w == pytest.approx(5.0), \
        "TX power must latch at HIGH (5 W)"


def test_normal_los_does_not_fire_4001(engine):
    ttc = engine.subsystems["ttc"]
    _in_pass(engine)
    assert _tick_until(engine, lambda: ttc._state.carrier_lock, 60)
    engine._override_passes = False
    engine.params[0x05FF] = 0
    # Out of contact for longer than the dropout window, then a new pass.
    window = int(ttc.UPLINK_DROPOUT_WINDOW_S) + 30
    orbit_in_contact = lambda: False
    _tick_until(engine, orbit_in_contact, window)
    _in_pass(engine)
    _tick_until(engine, lambda: ttc._state.carrier_lock, 60)
    assert not any(f[0] == 4001 for f in engine._fired), engine._fired
    assert ttc._pa_nominal_power_w == pytest.approx(2.0)


def test_cmd_loss_timer_runs_and_resets_on_accepted_tc(engine):
    ttc = engine.subsystems["ttc"]
    obdh = engine.subsystems["obdh"]
    _tick_until(engine, lambda: False, 5)
    t0 = engine.params[0x053D]
    assert t0 >= 4.0
    obdh.record_tc_accepted()
    _tick_until(engine, lambda: False, 2)
    assert engine.params[0x053D] <= 2.0, \
        "an accepted TC must restart the command-loss timer"
    assert ttc._state.time_since_last_tc_s <= 2.0


def _fires(eng):
    return sum(1 for f in eng._fired if f[0] == 4003)


def test_24h_without_a_tc_fires_4003_and_switches_transponder(engine):
    ttc = engine.subsystems["ttc"]
    assert ttc._state.mode == 0                    # primary
    # Fast-forward the on-board timer to just short of 24 h.
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    assert _tick_until(engine, lambda: _fires(engine) > 0, 10), engine._fired
    assert (4003, 99, b"") in engine._fired
    assert ttc._state.mode == 1, "FDIR TTC-01 must select the redundant XPDR"
    # One firing per expiry: the timer keeps running but the rule does not
    # re-fire every tick.
    n = _fires(engine)
    _tick_until(engine, lambda: False, 5)
    assert _fires(engine) == n == 1


def test_primary_dead_switches_to_redundant_after_24h(engine):
    """Franz 2026-11-02, case 1: the selected PRIMARY dies; nobody can
    command; 24 h after the last accepted TC the spacecraft is on the
    redundant unit and the link is back."""
    ttc = engine.subsystems["ttc"]
    _in_pass(engine)
    ttc.inject_failure("primary_failure", 1.0)
    _tick_until(engine, lambda: False, 2)
    assert not ttc.selected_transponder_alive()
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    assert _tick_until(engine, lambda: ttc._state.mode == 1, 10)
    assert ttc.selected_transponder_alive()
    assert _fires(engine) == 1


def test_redundant_selected_and_dead_switches_back_to_primary(engine):
    """Franz 2026-11-02, case 2: the switch must go both ways. With the
    REDUNDANT unit selected and dead, the old rule (func 64, switch to
    redundant) could never recover the link; the toggle returns to the
    primary 24 h after the last accepted TC."""
    ttc = engine.subsystems["ttc"]
    _in_pass(engine)
    ttc._state.mode = 1
    ttc.inject_failure("redundant_failure", 1.0)
    _tick_until(engine, lambda: False, 2)
    assert not ttc.selected_transponder_alive()
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    assert _tick_until(engine, lambda: ttc._state.mode == 0, 10)
    assert ttc.selected_transponder_alive()
    assert (4003, 99, b"") in engine._fired


def test_timer_rearms_and_toggles_again_every_24h(engine):
    """Re-arming: no TC after the first switch -> another toggle at 48 h, and
    so on. The autonomous switch itself is not an accepted TC, so it does not
    reset the timer, which keeps counting from the last accepted TC."""
    ttc = engine.subsystems["ttc"]
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    assert _tick_until(engine, lambda: ttc._state.mode == 1, 10)
    t1 = ttc._state.time_since_last_tc_s
    assert t1 >= 86400.0, "the autonomous switch must not reset the timer"
    ttc._state.time_since_last_tc_s = 2 * 86400.0 - 3.0
    assert _tick_until(engine, lambda: ttc._state.mode == 0, 10)
    assert _fires(engine) == 2
    ttc._state.time_since_last_tc_s = 3 * 86400.0 - 3.0
    assert _tick_until(engine, lambda: ttc._state.mode == 1, 10)
    assert _fires(engine) == 3


def test_both_dead_keeps_toggling_harmlessly(engine):
    """Both units dead: the on-board timer cannot tell a deaf receiver from a
    quiet ground, so it keeps toggling every 24 h. Nothing else changes, and
    the moment a unit recovers the toggle will eventually land on it."""
    ttc = engine.subsystems["ttc"]
    ttc.inject_failure("primary_failure", 1.0)
    ttc.inject_failure("redundant_failure", 1.0)
    for k in range(1, 4):
        ttc._state.time_since_last_tc_s = k * 86400.0 - 3.0
        assert _tick_until(engine, lambda: _fires(engine) == k, 10)
        assert ttc._state.mode == k % 2
        assert not ttc.any_transponder_alive()


def test_accepted_tc_resets_the_timer_and_the_toggle_count(engine):
    """Any accepted TC restarts the on-board timer: an expiry that was 3 s
    away is pushed back a full 24 h, and the next loss episode starts from
    the first expiry again."""
    ttc = engine.subsystems["ttc"]
    obdh = engine.subsystems["obdh"]
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    assert _tick_until(engine, lambda: _fires(engine) == 1, 10)
    assert ttc._state.mode == 1
    # Ground gets a TC in (on the redundant unit), 3 s before the 48 h toggle.
    ttc._state.time_since_last_tc_s = 2 * 86400.0 - 3.0
    obdh.record_tc_accepted()
    _tick_until(engine, lambda: False, 10)
    assert ttc._state.time_since_last_tc_s <= 10.0
    assert _fires(engine) == 1 and ttc._state.mode == 1, \
        "an accepted TC must cancel the pending toggle"
    assert ttc._state._cmd_loss_fires == 0
    # A new episode: the first expiry is again at 24 h after that TC.
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    assert _tick_until(engine, lambda: ttc._state.mode == 0, 10)
    assert _fires(engine) == 2


def test_switch_other_is_ground_commandable_and_blind(engine):
    """TTC_SWITCH_OTHER (func 99) is in the catalogue; it toggles even onto
    a unit the simulator knows is failed (the OBC cannot know: cold
    redundancy), unlike the named 63/64 selections."""
    ttc = engine.subsystems["ttc"]
    cat = _yaml("commands/tc_catalog.yaml")["commands"]
    entry = next(c for c in cat if c["name"] == "TTC_SWITCH_OTHER")
    assert (entry["service"], entry["subtype"], entry["func_id"]) == (8, 1, 99)
    ttc.inject_failure("redundant_failure", 1.0)
    engine._dispatcher._s19_dispatch(0, 99, b"")
    assert ttc._state.mode == 1
    engine._dispatcher._s19_dispatch(0, 99, b"")
    assert ttc._state.mode == 0
