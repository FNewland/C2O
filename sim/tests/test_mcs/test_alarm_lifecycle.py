"""Franz (operating the deployed system, 2026-11):

1. "Do alarms automatically disappear when the alarm state is gone (whether
   acknowledged or not)? I seem to have some AOCS alarms that do not
   correspond with my current state."
2. "When I dump the alarm store, this should not regenerate all the alarms in
   the alarm window — they need to be analyzed offline with the delayed
   telemetry analysis tool. None of the delayed telemetry should appear in
   the live window."

Root causes these tests pin down:

* A played-back (S15 dump) packet was byte-identical to a real-time one and
  arrived on the same stream, so the MCS processed it as live: every stored
  S12 TM(12,9) and S5 alarm event raised a fresh alarm, and every stored HK
  packet overwrote live values with old ones (and re-ran the ground limit
  check on them). Played-back TM now travels on virtual channel 1 and the MCS
  keeps it out of every live path.
* Alarms had no return-to-normal for S12 (TM(12,10) was ignored) and the S5
  mirror of every S12 violation (0x9xxx) raised a second, point-event alarm
  that nothing could clear. The journal now follows the ISA-18.2 states.
"""
from __future__ import annotations

import asyncio
import struct
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smo_common.config.loader import load_hk_structures
from smo_common.config.schemas import MCSDisplayConfig
from smo_common.protocol.ecss_packet import build_tm_packet, decommutate_packet
from smo_common.protocol.framing import (
    VC_PLAYBACK, VcPacket, deframe_sync, frame_packet, is_playback,
    read_framed_packet, tag_vc, vcid_of,
)
from smo_mcs import alarm_state as A
from smo_mcs.server import MCSServer

REPO = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO / "configs" / "eosat1"
sys.path.insert(0, str(REPO / "tools"))


# ── helpers ─────────────────────────────────────────────────────────────

def _server() -> MCSServer:
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}):
        srv = MCSServer(config_dir=str(CONFIG_DIR), connect_host="localhost",
                        connect_port=9999, http_port=0)
    srv._archive.close()
    srv._archive = MagicMock()
    srv._archive.store_alarm.return_value = 1
    return srv


def _ws(srv):
    ws = MagicMock()
    ws.send_str = AsyncMock()
    srv._ws_clients = [(ws, None)]
    return ws


def _sent(ws, kind):
    import json
    out = []
    for c in ws.send_str.call_args_list:
        m = json.loads(c.args[0])
        if m.get("type") == kind:
            out.append(m)
    return out


def _s12(param_id, value, *, entered, mon_id, low, high, cuc=800_000_000):
    data = struct.pack(">HfHBBff", param_id, value, mon_id, 0, 3, low, high)
    return build_tm_packet(apid=1, service=12, subtype=9 if entered else 10,
                           data=data, cuc_time=cuc)


def _s12_defs(rows, cuc=800_000_000):
    body = struct.pack(">H", len(rows))
    for mon_id, pid, ctype, enabled, lo, hi in rows:
        body += struct.pack(">HHBBff", mon_id, pid, ctype, 1 if enabled else 0, lo, hi)
    return build_tm_packet(apid=1, service=12, subtype=13, data=body, cuc_time=cuc)


def _s5(event_id, severity, text="x", cuc=800_000_000):
    aux = text.encode()
    data = struct.pack(">HBI", event_id, severity, cuc) + bytes([len(aux)]) + aux
    return build_tm_packet(apid=1, service=5, subtype=severity, data=data,
                           cuc_time=cuc)


def _hk_for(pid: int, value: float, cuc=800_000_000) -> bytes:
    for hk in load_hk_structures(CONFIG_DIR):
        if any(p.param_id == pid for p in hk.parameters):
            out = struct.pack(">H", hk.sid)
            for p in hk.parameters:
                eng = value if p.param_id == pid else 0.0
                if p.pack_format in ("f", "d"):
                    out += struct.pack(">" + p.pack_format, float(eng))
                    continue
                raw = int(round(eng * p.scale))
                size = struct.calcsize(">" + p.pack_format)
                signed = p.pack_format.islower()
                bits = size * 8
                lo = -(1 << (bits - 1)) if signed else 0
                hi = (1 << (bits - 1)) - 1 if signed else (1 << bits) - 1
                out += struct.pack(">" + p.pack_format, max(lo, min(hi, raw)))
            return build_tm_packet(apid=1, service=3, subtype=25, data=out,
                                   cuc_time=cuc)
    raise AssertionError(f"0x{pid:04X} in no HK SID")


def _run(srv, raw: bytes, *, stored=False):
    asyncio.run(srv._process_tm(decommutate_packet(raw), stored=stored))


def _limited_pid():
    from smo_common.config.loader import load_limits
    hk_pids = {p.param_id for hk in load_hk_structures(CONFIG_DIR)
               for p in hk.parameters}
    for lim in load_limits(CONFIG_DIR):
        if lim.param_id in hk_pids and lim.red_high is not None \
                and lim.yellow_high is not None and lim.yellow_low is not None:
            return lim
    raise AssertionError("no limited HK parameter with a full band")


# ── A. virtual-channel tag on the TCP framing ───────────────────────────

def test_vc0_records_are_byte_identical_to_the_old_framing():
    pkt = bytes(range(20))
    assert frame_packet(pkt) == struct.pack(">H", 20) + pkt


def test_playback_tag_round_trips_through_framing_and_relays():
    pkt = tag_vc(bytes(range(20)), VC_PLAYBACK)
    assert isinstance(pkt, VcPacket) and is_playback(pkt)
    wire = frame_packet(pkt) + frame_packet(b"\x01" * 9)
    buf = bytearray(wire)
    out = deframe_sync(buf)
    assert [vcid_of(p) for p in out] == [1, 0]
    assert bytes(out[0]) == bytes(range(20)) and not buf
    # A relay that does frame_packet(read_framed_packet(...)) keeps the tag.
    async def relay():
        r = asyncio.StreamReader()
        r.feed_data(wire)
        r.feed_eof()
        a = await read_framed_packet(r)
        b = await read_framed_packet(r)
        return frame_packet(a) + frame_packet(b)
    assert asyncio.run(relay()) == wire


def test_smo_link_split_records_forwards_tagged_records_intact():
    from smo_link import protocol as P
    wire = frame_packet(tag_vc(b"\xAB" * 30, 1)) + frame_packet(b"\xCD" * 7)
    recs = P.split_records(bytearray(wire))
    assert b"".join(recs) == wire and len(recs) == 2


def test_rfsim_frames_keep_vc0_and_vc1_streams_apart():
    """Interleaved VC0/VC1 frames: per-VC reassembly, VC1 packets tagged."""
    pytest.importorskip("smo_rfsim")
    from smo_rfsim.ccsds.tm_frame import TMFrameParser
    from smo_rfsim.ccsds.virtual_channel import VCMultiplexer
    mux = VCMultiplexer(frame_length=128, fecf_present=False)
    rt = [_s5(0x0200 + i, 1, "rt" * 20) for i in range(6)]
    pb = [_s5(0x0300 + i, 4, "pb" * 20) for i in range(6)]
    for a, b in zip(rt, pb):
        mux.add_packet(a, vcid=0)
        mux.add_packet(tag_vc(b, 1), vcid=1)
    frames = []
    while mux.has_data():
        frames.append(mux.get_next_frame())
    frames += mux.flush_all()
    # interleave frames from both VCs
    v0 = [f for f in frames if f.header.vcid == 0]
    v1 = [f for f in frames if f.header.vcid == 1]
    order = [f for pair in zip(v0, v1) for f in pair] + v0[len(v1):] + v1[len(v0):]
    parser = TMFrameParser(frame_length=128, fecf_present=False)
    got = []
    for f in order:
        got += parser.extract_packets(f)
    assert sorted(bytes(p) for p in got if not is_playback(p)) == sorted(rt)
    assert sorted(bytes(p) for p in got if is_playback(p)) == sorted(pb)


# ── A. the simulator puts dump packets on VC1 and the MCS keeps them out ──

def test_simulator_dump_goes_down_on_vc1_and_file_still_analysable(tmp_path, monkeypatch):
    from smo_simulator.engine import SimulationEngine
    from smo_simulator.tm_storage import OnboardTMStorage
    from tm_report import PassAnalysis, load_catalogs, read_dump
    monkeypatch.setenv("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    eng = SimulationEngine(CONFIG_DIR, speed=1.0)
    eng._tm_storage = OnboardTMStorage()
    stored = [_s12(0x0218, 9.0, entered=True, mon_id=7, low=-5, high=5),
              _s5(0x0210, 4, "AOCS rate high"),
              _s12(0x0218, 1.0, entered=False, mon_id=7, low=-5, high=5)]
    for p in stored:
        assert eng._tm_storage.store_packet_direct(4, p)
    while not eng.tm_queue.empty():
        eng.tm_queue.get_nowait()
    monkeypatch.setattr(type(eng), "downlink_active", property(lambda s: True))
    assert eng.queue_dump(4) == 3
    eng._tick_dump_emission(1000.0)
    out = []
    while not eng.tm_queue.empty():
        out.append(eng.tm_queue.get_nowait())
    assert [bytes(p) for p in out] == stored
    assert all(vcid_of(p) == VC_PLAYBACK for p in out)
    # ... and survive the sim server's framing to the ground.
    rx = deframe_sync(bytearray(b"".join(frame_packet(p) for p in out)))
    assert all(is_playback(p) for p in rx)

    # The delayed-TM tool still sees and analyses every dumped packet.
    files = list((tmp_path / "dumps").glob("dump_sid04_*.bin"))
    assert len(files) == 1
    params_by_id, _hk, hk_plist = load_catalogs()
    pa = PassAnalysis()
    for raw in read_dump(files[0]):
        pa.ingest_packet(raw, params_by_id, hk_plist)
    assert [t.get("mon_id") for t in pa.s12_transitions] == [7, 7]
    assert any(e.get("event_id") == 0x0210 for e in pa.events)


def test_dumped_alarm_store_raises_no_live_alarm_and_touches_nothing_live():
    srv = _server()
    ws = _ws(srv)
    lim = _limited_pid()
    pid = lim.param_id
    srv._param_cache[pid] = {"value": 1.234, "last_update_ts": 1.0, "sid": 1}
    before_fdir = srv._fdir_model.journal()
    for raw in (_s12(0x0218, 9.0, entered=True, mon_id=7, low=-5, high=5),
                _s5(0x0210, 4, "AOCS rate high"),
                _s5(0x9218, 3, "mirror"),
                _hk_for(pid, lim.red_high + abs(lim.red_high) + 10.0)):
        _run(srv, raw, stored=True)
    assert list(srv._alarm_journal) == []
    assert srv._param_cache[pid]["value"] == 1.234          # live value kept
    assert srv._tm_processor.limit_statuses().get(pid, "nominal") == "nominal"
    assert _sent(ws, "tm") == [] and _sent(ws, "alarm") == []
    assert srv.tm_packets_received == 0
    assert srv.tm_stored_packets_received == 4
    assert srv._fdir_model.journal() == before_fdir
    # S5 events from the dump are archived at their on-board time.
    assert srv._archive.store_event.call_count == 2
    kw = srv._archive.store_event.call_args.kwargs
    assert kw["obc_cuc"] is not None


def test_the_same_packets_in_real_time_do_raise():
    srv = _server()
    _ws(srv)
    _run(srv, _s12(0x0218, 9.0, entered=True, mon_id=7, low=-5, high=5))
    _run(srv, _s5(0x0210, 4, "AOCS rate high"))
    assert {a["source"] for a in srv._alarm_journal} == {"S12", "S5"}


# ── B. alarm lifecycle (ISA-18.2) ───────────────────────────────────────

def test_state_machine_all_transitions():
    a = A.init({"source": "S12"}, ts=0.0)
    assert a["state"] == A.UNACK_ACTIVE and A.is_live(a)
    A.acknowledge(a, ts=1.0)
    assert a["state"] == A.ACK_ACTIVE and A.is_live(a)
    A.return_to_normal(a, ts=2.0, reason="r")
    assert a["state"] == A.ACK_RTN and not A.is_live(a)

    b = A.init({"source": "LIMIT"}, ts=0.0)
    A.return_to_normal(b, ts=1.0, reason="r")
    assert b["state"] == A.UNACK_RTN and A.is_live(b) and b["rtn"]
    assert not b["acknowledged"]                 # RTN never implies ack
    A.acknowledge(b, ts=2.0)
    assert b["state"] == A.ACK_RTN and not A.is_live(b)

    e = A.init({"source": "S5"}, ts=0.0)          # point event
    assert e["state"] == A.UNACK_ACTIVE and e["point_event"]
    A.acknowledge(e, ts=1.0)
    assert e["state"] == A.ACK_RTN


def test_s12_back_to_limits_clears_and_ack_removes():
    srv = _server()
    ws = _ws(srv)
    _run(srv, _s12(0x0218, 9.0, entered=True, mon_id=7, low=-5, high=5))
    (al,) = srv.live_alarms()
    assert al["state"] == A.UNACK_ACTIVE
    _run(srv, _s12(0x0218, 1.0, entered=False, mon_id=7, low=-5, high=5))
    assert al["state"] == A.UNACK_RTN and al in srv.live_alarms()
    assert _sent(ws, "alarm_cleared")[-1]["alarms"][0]["state"] == A.UNACK_RTN
    asyncio.run(srv._acknowledge_alarm(al["id"]))
    assert srv.live_alarms() == [] and al in srv._alarm_journal


def test_acknowledged_s12_alarm_leaves_the_list_on_rtn():
    srv = _server()
    _ws(srv)
    _run(srv, _s12(0x0218, 9.0, entered=True, mon_id=7, low=-5, high=5))
    (al,) = srv.live_alarms()
    asyncio.run(srv._acknowledge_alarm(al["id"]))
    assert al["state"] == A.ACK_ACTIVE and srv.live_alarms() == [al]
    _run(srv, _s12(0x0218, 1.0, entered=False, mon_id=7, low=-5, high=5))
    assert srv.live_alarms() == []


def test_s12_mirror_events_raise_no_second_alarm():
    srv = _server()
    _ws(srv)
    _run(srv, _s12(0x0218, 9.0, entered=True, mon_id=7, low=-5, high=5))
    _run(srv, _s5(0x9218, 3, "mirror of the S12 violation"))
    assert [a["source"] for a in srv._alarm_journal] == ["S12"]


def test_s5_event_stays_until_acknowledged_then_goes():
    srv = _server()
    _ws(srv)
    _run(srv, _s5(0x0210, 4, "AOCS rate high"))
    (al,) = srv.live_alarms()
    assert al["state"] == A.UNACK_ACTIVE and al["point_event"]
    asyncio.run(srv._acknowledge_alarm(al["id"]))
    assert srv.live_alarms() == []


def test_ground_limit_rtn_is_not_auto_acknowledged():
    srv = _server()
    _ws(srv)
    lim = _limited_pid()
    tag = f"0x{lim.param_id:04X}"
    mine = lambda lst: [a for a in lst if a["source"] == "LIMIT" and a["parameter"] == tag]
    _run(srv, _hk_for(lim.param_id, lim.red_high + abs(lim.red_high) + 10.0))
    act = mine(srv.live_alarms())
    assert act and all(a["state"] == A.UNACK_ACTIVE for a in act)
    mid = (lim.yellow_low + lim.yellow_high) / 2.0
    _run(srv, _hk_for(lim.param_id, mid))
    lim_alarms = mine(srv._alarm_journal)
    assert all(a["state"] == A.UNACK_RTN for a in lim_alarms)
    assert all(not a["acknowledged"] for a in lim_alarms)
    for a in lim_alarms:
        asyncio.run(srv._acknowledge_alarm(a["id"]))
    assert not mine(srv.live_alarms())


def test_limit_escalation_supersedes_the_lower_band():
    srv = _server()
    _ws(srv)
    lim = _limited_pid()
    yel = (lim.yellow_high + lim.red_high) / 2.0
    _run(srv, _hk_for(lim.param_id, yel))
    _run(srv, _hk_for(lim.param_id, lim.red_high + abs(lim.red_high) + 10.0))
    active = [a for a in srv._alarm_journal
              if a["source"] == "LIMIT" and A.is_active(a)
              and a["parameter"] == f"0x{lim.param_id:04X}"]
    assert len(active) == 1 and active[0]["limit_status"].startswith("red")


def test_disabled_or_deleted_monitor_clears_its_alarm():
    srv = _server()
    _ws(srv)
    _run(srv, _s12(0x0218, 9.0, entered=True, mon_id=7, low=-5, high=5))
    _run(srv, _s12(0x0105, 9.0, entered=True, mon_id=8, low=20, high=100))
    _run(srv, _s12_defs([(7, 0x0218, 0, False, -5, 5)]))   # 7 disabled, 8 gone
    reasons = {a["mon_id"]: a.get("rtn_reason") for a in srv._alarm_journal}
    assert "disabled" in reasons[7] and "deleted" in reasons[8]


def test_reconcile_after_reconnect_or_reset_clears_missed_rtn():
    """The on-board monitor cleared while the MCS was not listening (or the
    sim was reset, which re-arms monitors without any TM(12,10))."""
    srv = _server()
    _ws(srv)
    pid = 0x0105
    _run(srv, _s12(pid, 9.0, entered=True, mon_id=8, low=20, high=100))
    (al,) = srv.live_alarms()
    # No reconcile window: a value back in band is not enough on its own
    # (the on-board check may have a persistence count we cannot see).
    _run(srv, _hk_for(pid, 50.0))
    assert A.is_active(al)
    srv._arm_alarm_reconcile("TM reconnect")
    _run(srv, _hk_for(pid, 50.0))
    assert al["state"] == A.UNACK_RTN
    assert "TM reconnect" in al["rtn_reason"]


def test_sim_clock_discontinuity_arms_the_reconcile():
    from datetime import datetime, timedelta, timezone
    srv = _server()
    srv._ground_epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
    import time as _t
    srv._ground_start_wall = _t.time()
    srv._alarm_reconcile = None
    srv._detect_sim_time_jump(srv._ground_epoch + timedelta(days=3))
    assert srv._alarm_reconcile and "discontinuity" in srv._alarm_reconcile["reason"]


def test_api_alarms_serves_the_live_list_and_history_on_request():
    from aiohttp.test_utils import TestClient, TestServer
    srv = _server()
    _ws(srv)
    _run(srv, _s5(0x0210, 4, "AOCS rate high"))
    _run(srv, _s5(0x0211, 4, "AOCS other"))
    first = srv.live_alarms()[-1]
    asyncio.run(srv._acknowledge_alarm(first["id"]))

    async def go():
        from aiohttp import web
        app = web.Application()
        app.router.add_get("/api/alarms", srv._handle_alarms_get)
        async with TestClient(TestServer(app)) as c:
            live = await (await c.get("/api/alarms")).json()
            hist = await (await c.get("/api/alarms?all=1")).json()
            return live, hist
    live, hist = asyncio.run(go())
    assert len(live["alarms"]) == 1 and len(hist["alarms"]) == 2


def test_new_pass_reconciles_an_rtn_sent_during_los():
    """The TM(12,10) for an excursion that ended out of coverage is in the
    on-board store, and stored TM never clears a live alarm — the first
    real-time packets of the next pass must reconcile it on value."""
    srv = _server()
    _ws(srv)
    pid = 0x0105
    _run(srv, _s12(pid, 9.0, entered=True, mon_id=8, low=20, high=100))
    (al,) = srv.live_alarms()
    srv._alarm_reconcile = None
    srv._last_rt_rx_ts = srv.sim_now_ts() - 5400.0          # LOS: 90 min
    # The dump of that TM(12,10) changes nothing ...
    _run(srv, _s12(pid, 50.0, entered=False, mon_id=8, low=20, high=100),
         stored=True)
    assert A.is_active(al)
    # ... the first real-time HK of the pass does.
    _run(srv, _hk_for(pid, 50.0))
    assert al["state"] == A.UNACK_RTN and "new pass" in al["rtn_reason"]
