"""Both S-band transponders failed => the link is cut, override or not.

Walkthrough finding S4 (2026-11-02): with ``ttc primary_failure`` and
``redundant_failure`` injected and the instructor pass override on,
``ttc.link_status`` read 0 yet telecommands still executed and their S1.8
replies ("Primary XPDR failed") arrived on the downlink, so EMG-004 and
CTG-003 could not be practised as a real loss of communication.

Franz's ruling: "Unless overridden, this should cut the link (and maybe even
if overridden?)". The pass override stands in for "a station is in view"; it
cannot resurrect a radio. A real spacecraft has no override for dead
transponders, so with BOTH units dead:

* no uplinked TC is executed (the OBC's accepted-TC counter does not move);
* no TM leaves the spacecraft — no HK, no event, no S1 reply, and no UHF
  beacon either: the model takes the spacecraft out of contact as soon as
  the selected transponder is dead, so the beacon (which needs a contact)
  goes quiet too. Franz asked for exactly that ("cut the link").

Recovery is the failure clearing (instructor clear, or a transient's
duration running out); the link comes straight back.
"""
import os
from pathlib import Path

import pytest

from smo_common.protocol.ecss_packet import build_tc_packet, decommutate_packet
from smo_simulator.engine import SimulationEngine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


@pytest.fixture
def engine(tmp_path):
    os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(CONFIG_DIR)
    eng._spacecraft_phase = 6
    eng.subsystems["obdh"]._state.sw_image = 1     # application
    eng.subsystems["obdh"]._state.mode = 0
    # The transmitter line is hot (post-LEOP state), so the only thing that
    # can cut the link in these tests is the transponders themselves.
    eng.subsystems["eps"]._state.power_lines["ttc_tx"] = True
    # The instructor pass override: the worst case for the gate, because it
    # used to open both directions regardless of the radios.
    eng._override_passes = True
    eng.params[0x05FF] = 1
    return eng


def _tick(eng, n):
    for _ in range(n):
        eng._tick_once(1.0)


def _drain(eng):
    out = []
    while not eng.tm_queue.empty():
        out.append(eng.tm_queue.get_nowait())
    return out


def _services(pkts):
    """(service, subtype, sid-or-None) of every downlinked packet."""
    res = []
    for raw in pkts:
        p = decommutate_packet(raw)
        if p is None or p.secondary is None:
            continue
        sid = None
        if p.secondary.service == 3 and p.secondary.subtype == 25 and p.data:
            sid = int.from_bytes(p.data[:2], "big") if len(p.data) >= 2 else p.data[0]
        res.append((p.secondary.service, p.secondary.subtype, sid))
    return res


def _ping(seq):
    return build_tc_packet(apid=100, service=17, subtype=1, seq_count=seq)


def _tc_accepted(eng):
    return int(eng.params.get(0x0305, 0))


def test_link_works_before_the_failure(engine):
    _tick(engine, 30)
    assert engine.downlink_active and engine.uplink_active
    before = _tc_accepted(engine)
    _drain(engine)
    engine.tc_queue.put_nowait(_ping(1))
    _tick(engine, 3)
    assert _tc_accepted(engine) > before
    assert any(s == 1 for s, _, _ in _services(_drain(engine))), \
        "the ping's S1 verification must arrive while the radios work"


def test_both_transponders_failed_cuts_tc_and_tm_even_with_override(engine):
    ttc = engine.subsystems["ttc"]
    _tick(engine, 30)
    ttc.inject_failure("primary_failure", 1.0)
    ttc.inject_failure("redundant_failure", 1.0)
    _tick(engine, 5)
    _drain(engine)                                  # anything already radiated

    assert not engine.uplink_active
    assert not engine.downlink_active
    before = _tc_accepted(engine)

    # Commands the walkthrough saw "execute": a ping and both switch commands.
    engine.tc_queue.put_nowait(_ping(2))
    engine.tc_queue.put_nowait(build_tc_packet(apid=100, service=8, subtype=1,
                                               data=bytes([63]), seq_count=3))
    engine.tc_queue.put_nowait(build_tc_packet(apid=100, service=8, subtype=1,
                                               data=bytes([64]), seq_count=4))
    _tick(engine, 120)

    assert _tc_accepted(engine) == before, "a TC executed with no receiver"
    seen = _services(_drain(engine))
    assert seen == [], f"TM leaked with both transponders dead: {seen[:10]}"
    assert not engine.params.get(0x0527), "the beacon still reports active"


def test_clearing_the_failure_restores_the_link(engine):
    ttc = engine.subsystems["ttc"]
    _tick(engine, 30)
    ttc.inject_failure("primary_failure", 1.0)
    ttc.inject_failure("redundant_failure", 1.0)
    _tick(engine, 10)
    assert not engine.uplink_active
    ttc.clear_failure("primary_failure")
    _tick(engine, 30)
    assert engine.uplink_active and engine.downlink_active
    before = _tc_accepted(engine)
    _drain(engine)
    engine.tc_queue.put_nowait(_ping(5))
    _tick(engine, 3)
    assert _tc_accepted(engine) > before


def test_selected_unit_failed_override_still_reaches_the_standby_receiver(engine):
    """One unit dead: the override can still command the switch blind (the
    standby receiver is hot), but the dead selected unit radiates nothing
    until the switch is made."""
    ttc = engine.subsystems["ttc"]
    _tick(engine, 30)
    ttc.inject_failure("primary_failure", 1.0)
    _tick(engine, 5)
    _drain(engine)
    assert engine.uplink_active
    assert not engine.downlink_active
    engine.tc_queue.put_nowait(build_tc_packet(apid=100, service=8, subtype=1,
                                               data=bytes([64]), seq_count=6))
    _tick(engine, 30)
    assert ttc._state.mode == 1
    assert engine.downlink_active


def test_command_loss_timer_is_the_only_onboard_recovery(engine):
    """EMG-004 Step 5 / CTG-003 Step 6: the on-board autonomy is FDIR TTC-01
    — every 24 h without an accepted TC raises 0x0514 and S19 ea 4003 toggles
    to the other transponder. With the selected unit dead that brings the
    link back; with BOTH dead the toggle changes nothing and the link stays
    cut."""
    ttc = engine.subsystems["ttc"]
    _tick(engine, 30)
    ttc.inject_failure("primary_failure", 1.0)
    _tick(engine, 2)
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    _tick(engine, 10)
    assert ttc._state.mode == 1, "TTC-01 did not switch to the redundant unit"
    _tick(engine, 30)
    assert engine.downlink_active and engine.uplink_active

    # Second episode: the redundant unit dies too. The timer fires again and
    # toggles (blindly) back to the dead primary; nothing radiates.
    ttc.inject_failure("redundant_failure", 1.0)
    ttc._state._cmd_loss_fires = 0
    ttc._state.time_since_last_tc_s = 86400.0 - 3.0
    _tick(engine, 10)
    assert ttc._state.mode == 0, "the toggle is blind: it goes back anyway"
    _drain(engine)
    _tick(engine, 30)
    assert not engine.uplink_active and not engine.downlink_active
    assert _services(_drain(engine)) == []
