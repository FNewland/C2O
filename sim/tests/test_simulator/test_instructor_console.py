"""Instructor console redesign (docs/plan_2026-11/INSTRUCTOR_CONSOLE_DESIGN.md).

Covers the server half of the design:
  * divergence classification (truth / spacecraft / ground, cause precedence);
  * the fault menu by control-loop element (every catalogue failure placed);
  * the ground view computed from the simulator's own downlinked TM;
  * the one timeline: injects, focus hints, scheduled injects (delay, AOS,
    telecommand triggers), cancel, marks, auto snapshot, new segment on a
    breakpoint load, fault swimlane latencies;
  * the /api/instructor/* routes and the command validation;
  * the server-side guard: no instructor data in /api/state or on /ws, and
    the space-link proxy allowlists the new routes as read-only;
  * the focus state machine and timeline helpers (node, when installed).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from smo_simulator.engine import SimulationEngine
from smo_simulator.instructor import divergence as dv
from smo_simulator.instructor import taxonomy as tx

REPO = Path(__file__).resolve().parents[2]
MODERN = REPO / "packages/smo-simulator/src/smo_simulator/instructor/static/modern"
NODE = shutil.which("node")


def _engine(tmp_path=None, monkeypatch=None):
    if monkeypatch is not None and tmp_path is not None:
        # a manual save would write here (auto snapshots: conftest tmp dir)
        monkeypatch.setattr(SimulationEngine, "_BREAKPOINT_DIR", tmp_path / "bp")
    e = SimulationEngine(REPO / "configs" / "eosat1", speed=1.0)
    return e


def _nominal(e, link=True, sids=range(1, 8)):
    ok, why = e.submit_instructor_cmd_sync({"type": "set_phase", "phase": 6})
    assert ok, why
    if link:
        e._handle_instructor_cmd({"type": "override_passes", "enabled": True})
    for s in sids:
        e.set_hk_enabled(s, True)


def _ticks(e, n, dt=1.0):
    for _ in range(n):
        e._tick_once(dt)


def _items(e, **match):
    out = e.instructor_rec.timeline_since(0, limit=10000)["items"]
    return [i for i in out if all(i.get(k) == v for k, v in match.items())]


# ── 1. classification (pure) ────────────────────────────────────────────────


class TestClassify:
    def test_agreement_is_ok(self):
        c = dv.classify(10.0, 10.05, 10.04, threshold=1.0, ground_age_s=2)
        assert c["state"] == "ok" and c["cause"] is None and c["causes"] == []

    def test_injected_indication_fault(self):
        c = dv.classify(15.0, 23.0, 23.0, threshold=1.0, ground_age_s=1, injected=True)
        assert c["state"] == "diverged" and c["cause"] == "injected"
        assert c["onboard_err"] == pytest.approx(8.0)

    def test_estimator_error_without_inject(self):
        c = dv.classify(0.0, 0.4, 0.4, threshold=0.1, ground_age_s=1, estimate=True)
        assert c["cause"] == "estimator"

    def test_delay_when_ground_is_behind(self):
        c = dv.classify(50.0, 50.0, 60.0, threshold=1.0, ground_age_s=300,
                        delay_reason="no downlink (out of contact or transmitter off)")
        assert c["cause"] == "delay" and c["late"] is True
        assert c["reason"].startswith("no downlink")

    def test_never_received_is_delay(self):
        c = dv.classify(1.0, 1.0, None, threshold=0.5)
        assert c["state"] == "diverged" and c["cause"] == "delay"
        assert c["reason"] == "never received on the ground"

    def test_precedence_injected_then_estimator_then_delay(self):
        c = dv.classify(15.0, 23.0, 30.0, threshold=1.0, injected=True)
        assert c["causes"] == ["injected", "delay"] and c["cause"] == "injected"
        c = dv.classify(15.0, 23.0, 30.0, threshold=1.0)
        assert c["causes"] == ["estimator", "delay"] and c["cause"] == "estimator"

    def test_small_injected_lie_still_flagged(self):
        # gradual onset: the lie is below threshold but it is the instructor's
        c = dv.classify(15.0, 15.4, 15.4, threshold=1.0, injected=True)
        assert c["cause"] == "injected" and c["state"] == "diverged"

    def test_enum_pairs(self):
        assert dv.classify(0, 0, 0, threshold=0, enum=True)["state"] == "ok"
        c = dv.classify(0, 0, 1, threshold=0, enum=True)
        assert c["cause"] == "delay"

    def test_no_truth_is_nodata(self):
        assert dv.classify(None, 1.0, 1.0, threshold=1.0)["state"] == "nodata"

    def test_angular_wrap(self):
        c = dv.classify(179.5, -179.5, -179.5, threshold=2.0, angular=True)
        assert c["state"] == "ok" and c["onboard_err"] == pytest.approx(1.0)


# ── 2. fault menu by control-loop element ───────────────────────────────────


def test_every_failure_has_a_control_loop_element():
    from smo_simulator import failure_catalog
    missing = [(s, f) for s, fs in failure_catalog.catalog().items() for f in fs
               if (s, f) not in tx.ELEMENT_OF]
    assert not missing, f"add these to taxonomy.ELEMENT_OF: {missing}"
    assert set(tx.ELEMENT_OF.values()) <= set(tx.ELEMENT_IDS)


def test_fault_menu_groups_the_whole_catalogue():
    from smo_simulator import failure_catalog
    menu = tx.fault_menu()
    assert [e["id"] for e in menu["elements"]] == list(tx.ELEMENT_IDS)
    placed = {(f["subsystem"], f["name"]) for e in menu["elements"] for f in e["failures"]}
    every = {(s, f) for s, fs in failure_catalog.catalog().items() for f in fs}
    assert placed == every
    obs = next(e for e in menu["elements"] if e["id"] == "observer")
    assert all(f["inject_class"] == "indication" for f in obs["failures"])
    assert {"tcs", "aocs", "obdh"} <= {f["subsystem"] for f in obs["failures"]}


def test_indication_faults_focus_the_divergence_view():
    assert tx.view_for("tcs", "sensor_drift") == "divergence"
    assert tx.view_for("eps", "bus_short") == "power"
    assert tx.inject_class("aocs", "rw_seizure") == "physical"


# ── 3. ground view + divergence on a live engine ───────────────────────────


@pytest.fixture(scope="module")
def drift_engine():
    e = _engine()
    _nominal(e)
    _ticks(e, 5)
    ok, why = e.submit_instructor_cmd_sync({
        "type": "failure_inject", "subsystem": "tcs", "failure": "sensor_drift",
        "magnitude": 8.0, "zone": "obc", "snapshot_before": True})
    assert ok, why
    _ticks(e, 130)
    e.instructor_rec.maybe_build_views(force=True)
    return e


def _row(e, pid):
    views = e.instructor_rec.published()
    return next(r for r in views["divergence"]["rows"] if r["id"] == pid)


def test_ground_view_comes_from_downlinked_hk(drift_engine):
    e = drift_engine
    g = e.instructor_rec.ground.values()
    assert e.instructor_rec.ground.packets > 0
    # EPS SID 1 every second: the ground's SoC is the packed, scaled value
    assert abs(g[0x0101]["v"] - e.params[0x0101]) < 0.05
    assert g[0x0101]["via"] == "rt"


def test_sensor_drift_is_classified_injected(drift_engine):
    r = _row(drift_engine, "tcs.obc")
    assert r["injected"] is True and r["cause"] == "injected"
    assert r["onboard"] - r["truth"] == pytest.approx(8.0, abs=0.5)
    # the ground got the lying value too (SID 3 every 60 s)
    assert r["ground"] == pytest.approx(r["onboard"], abs=0.5)


def test_other_zones_agree(drift_engine):
    assert _row(drift_engine, "tcs.battery")["cause"] is None


def test_auto_snapshot_before_inject(drift_engine):
    autos = [r["name"] for r in drift_engine._auto_snapshots.list()]
    assert any("before tcs/sensor_drift" in n for n in autos)
    # the manual store is untouched
    assert not any(s.get("auto") for s in drift_engine._breakpoints.values())


def test_inject_on_timeline_with_focus_hint(drift_engine):
    inj = _items(drift_engine, lane="fault", kind="inject")
    assert inj and inj[-1]["focus"]["view"] == "divergence"
    assert inj[-1]["focus"]["reason"] == "inject fired"
    assert "zone=obc" in inj[-1]["text"]
    div = _items(drift_engine, lane="fault", kind="diverge")
    assert any(i["ref"] == "tcs.obc" for i in div)


def test_overview_tiles_carry_inject_and_divergence(drift_engine):
    tiles = {t["id"]: t for t in drift_engine.instructor_rec.published()["overview"]["tiles"]}
    assert set(tiles) >= {"eps", "aocs", "tcs", "obdh", "ttc", "payload", "prop"}
    assert tiles["tcs"]["injected"] == 1 and tiles["tcs"]["div_injected"] >= 1


def test_delay_without_downlink():
    e = _engine()
    _nominal(e, link=False)
    _ticks(e, 10)
    e.instructor_rec.maybe_build_views(force=True)
    r = _row(e, "eps.soc")
    if not e.downlink_active:
        assert r["cause"] == "delay"
        assert r["reason_t"]["key"] in ("no downlink (out of contact or transmitter off)",
                                       "never received on the ground") or r["reason"]


def test_clock_offset_is_an_estimator_gap_not_observable_on_ground():
    e = _engine()
    _ticks(e, 3)
    e.instructor_rec.maybe_build_views(force=True)
    r = _row(e, "obdh.clock")
    assert r["ground_kind"] == "none"
    assert r["cause"] == "estimator"      # OBC clock never set at boot


def test_truth_views_shape(drift_engine):
    v = drift_engine.instructor_rec.published()
    th = v["thermal"]
    assert th["available"] and len(th["nodes"]) >= 16
    obc = next(n for n in th["nodes"] if n["id"] == "obc")
    assert obc["sensor_offset"] == pytest.approx(8.0)
    assert any(l["kind"] == "cond" for l in th["links"])
    assert v["attitude"]["available"] and len(v["attitude"]["q_true"]) == 4
    chain = {c["id"]: c for c in v["orbit"]["chain"]}
    assert chain["geometry"]["ok"] and set(chain) >= {"geometry", "line", "pa", "radio"}
    assert v["storage"]["stores"] and "transitions" in v["obc"]


# ── 4. scheduler, marks, segments ──────────────────────────────────────────


def test_delay_schedule_fires_once_with_snapshot(tmp_path, monkeypatch):
    e = _engine(tmp_path, monkeypatch)
    _nominal(e)
    _ticks(e, 2)
    ok, why = e.submit_instructor_cmd_sync({
        "type": "failure_schedule", "trigger": {"kind": "delay", "delay_s": 5},
        "injects": [{"subsystem": "eps", "failure": "solar_array_partial", "magnitude": 0.5, "array": "A"},
                    {"subsystem": "tcs", "failure": "heater_failure", "circuit": "battery"}]})
    assert ok, why
    pend = e.instructor_rec.pending()
    assert pend and pend[0]["source"] == "instructor" and pend[0]["ts"] is not None
    _ticks(e, 3)
    assert not e._failure_manager.active_failures()
    _ticks(e, 4)
    subs = {f["subsystem"] for f in e._failure_manager.active_failures()}
    assert subs == {"eps", "tcs"}, "a batch fires together"
    assert not e.instructor_rec.schedule_list()
    assert len(_items(e, kind="sched_fire")) == 1
    assert any("eps/solar_array_partial+tcs/heater_failure" in r["name"]
               for r in e._auto_snapshots.list())


def test_aos_trigger_and_cancel():
    e = _engine()
    _nominal(e, link=False)
    _ticks(e, 3)
    ok, _ = e.submit_instructor_cmd_sync({"type": "failure_schedule", "trigger": {"kind": "aos"},
        "injects": [{"subsystem": "ttc", "failure": "high_ber", "offset": 3}], "snapshot_before": False})
    assert ok
    ok, _ = e.submit_instructor_cmd_sync({"type": "failure_schedule", "trigger": {"kind": "los"},
        "injects": [{"subsystem": "ttc", "failure": "high_ber", "offset": 3}]})
    sid = e.instructor_rec.schedule_list()[-1]["id"]
    ok, why = e.submit_instructor_cmd_sync({"type": "schedule_cancel", "schedule_id": sid})
    assert ok, why
    ok, why = e.submit_instructor_cmd_sync({"type": "schedule_cancel", "schedule_id": sid})
    assert not ok and "no pending" in why
    assert len(e.instructor_rec.schedule_list()) == 1
    # the pass override makes the downlink come up: an AOS edge
    e._handle_instructor_cmd({"type": "override_passes", "enabled": True})
    _ticks(e, 4)
    assert _items(e, kind="aos"), "AOS on the link lane"
    assert any(f["failure"] == "high_ber" for f in e._failure_manager.active_failures())


def test_tc_trigger_fires_on_the_next_matching_telecommand():
    from smo_common.protocol.ecss_packet import build_tc_packet
    e = _engine()
    _nominal(e)
    _ticks(e, 3)
    ok, _ = e.submit_instructor_cmd_sync({"type": "failure_schedule",
        "trigger": {"kind": "tc", "service": 17, "subtype": 1},
        "injects": [{"subsystem": "obdh", "failure": "cpu_spike", "load": 90}], "snapshot_before": False})
    assert ok
    e.tc_queue.put(build_tc_packet(1, 3, 27, b"\x00\x01", 5))
    _ticks(e, 2)
    assert not e._failure_manager.active_failures()
    e.tc_queue.put(build_tc_packet(1, 17, 1, b"", 6))
    _ticks(e, 2)
    assert any(f["failure"] == "cpu_spike" for f in e._failure_manager.active_failures())
    rx = _items(e, kind="tc_rx")
    assert any("S17.1" in i["text"] for i in rx)
    assert _items(e, kind="tc_acc"), "S1 verification on the TC lane"


def test_schedule_validation_errors():
    e = _engine()
    rec = e.instructor_rec
    assert rec.schedule({"injects": []})[0] is False
    assert rec.schedule({"injects": [{"subsystem": "eps", "failure": "x"}] * 9})[0] is False
    assert rec.schedule({"injects": [{"subsystem": "eps", "failure": "bus_short"}],
                         "trigger": {"kind": "sometime"}})[0] is False
    assert rec.schedule({"injects": [{"subsystem": "eps", "failure": "bus_short"}],
                         "trigger": {"kind": "delay", "delay_s": -1}})[0] is False
    assert rec.schedule({"injects": [{"subsystem": "eps", "failure": "bus_short"}],
                         "trigger": {"kind": "tc"}})[0] is False


def test_marks():
    e = _engine()
    ok, _ = e.submit_instructor_cmd_sync({"type": "timeline_mark", "kind": "bookmark", "text": "  look   here "})
    assert ok
    ok, why = e.submit_instructor_cmd_sync({"type": "timeline_mark", "kind": "anomaly",
                                            "disposition": "restart", "text": "glitch"})
    assert ok, why
    ok, why = e.submit_instructor_cmd_sync({"type": "timeline_mark", "kind": "anomaly", "disposition": "maybe"})
    assert not ok
    ok, why = e.submit_instructor_cmd_sync({"type": "timeline_mark", "kind": "shout"})
    assert not ok
    marks = _items(e, lane="instr")
    assert [m["text"] for m in marks if m["kind"] in ("bookmark", "anomaly")] == [
        "Bookmark: look here", "Sim anomaly (restart from snapshot): glitch"]


def test_breakpoint_load_starts_a_new_segment(tmp_path, monkeypatch):
    e = _engine(tmp_path, monkeypatch)
    _ticks(e, 2)
    ok, why = e.submit_instructor_cmd_sync({"type": "save_breakpoint", "name": "a"})
    assert ok, why
    _ticks(e, 2)
    seg0 = e.instructor_rec.segment
    ok, why = e.submit_instructor_cmd_sync({"type": "load_breakpoint", "name": "a"})
    assert ok, why
    assert e.instructor_rec.segment == seg0 + 1
    assert _items(e, kind="load_breakpoint")[0]["seg"] == seg0 + 1


def test_fault_swimlane_symptom_ground_and_response():
    from smo_common.protocol.ecss_packet import build_tc_packet
    e = _engine()
    _nominal(e)
    _ticks(e, 5)
    ok, why = e.submit_instructor_cmd_sync({"type": "failure_inject", "subsystem": "eps",
                                            "failure": "undervoltage", "magnitude": 8})
    assert ok, why

    def lane():
        return next(f for f in e.instructor_rec.fault_lanes() if f["failure"] == "undervoltage")
    for _ in range(60):
        _ticks(e, 1)
        if lane()["ground_ts"] is not None:
            break
    f = lane()
    assert f["element"] == "process"
    assert f["symptom_ts"] is not None and f["ground_ts"] is not None
    assert f["response_ts"] is None
    _ticks(e, 3)
    e.tc_queue.put(build_tc_packet(1, 17, 1, b"", 9))
    _ticks(e, 2)
    f = lane()
    assert f["response_ts"] is not None and f["latency"]["to_response_s"] >= 3
    assert f["latency"]["to_symptom_s"] >= 0 and f["latency"]["to_ground_s"] >= 0
    ok, _ = e.submit_instructor_cmd_sync({"type": "failure_clear_all"})
    _ticks(e, 2)
    assert lane()["cleared_ts"] is not None and _items(e, lane="fault", kind="clear")


def test_scenario_events_are_pending_ahead_of_now():
    e = _engine()
    se = e._scenario_engine
    name = next(s["name"] for s in se.list_scenarios() if s["name"] == "Solar Array Degradation")
    ok, why = e.submit_instructor_cmd_sync({"type": "start_scenario", "scenario": name})
    assert ok, why
    _ticks(e, 2)
    pend = e.instructor_rec.pending()
    now = e.instructor_rec.now_ts()
    inj = [p for p in pend if p["source"] == "scenario" and "solar_array_partial" in p["text"]]
    assert inj and inj[0]["ts"] > now
    assert any(p["id"] == "scn_end" for p in pend)
    assert _items(e, kind="scn_start")


# ── 5. HTTP routes ─────────────────────────────────────────────────────────


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    from aiohttp.test_utils import TestClient, TestServer
    from smo_simulator.instructor.app import create_instructor_app
    e = _engine(tmp_path, monkeypatch)
    _ticks(e, 3)
    return e, (lambda: TestClient(TestServer(create_instructor_app(e, ui_mode="modern"))))


@pytest.mark.asyncio
async def test_instructor_routes(app_client):
    e, mk = app_client
    client = mk()
    await client.start_server()
    try:
        r = await client.get("/api/instructor/views")
        assert r.status == 200 and r.headers["Cache-Control"] == "no-store"
        v = await r.json()
        assert {"overview", "divergence", "thermal", "attitude", "orbit", "obc", "storage",
                "power", "schedule"} <= set(v)
        r = await client.get("/api/instructor/timeline?since=0")
        tl = await r.json()
        assert tl["lanes"][-1] == "voice" and "voice" in tl["unavailable_lanes"]
        last = tl["seq"]
        r = await client.get(f"/api/instructor/timeline?since={last}")
        assert (await r.json())["items"] == []
        assert (await client.get("/api/instructor/timeline?since=x")).status == 400
        menu = await (await client.get("/api/instructor/fault-menu")).json()
        assert len(menu["elements"]) == 8
        h = await (await client.get("/api/instructor/history")).json()
        assert "samples" in h
        d = await (await client.get("/api/instructor/debrief")).json()
        assert {"segment", "faults", "items", "scenario"} <= set(d)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_schedule_command_validation_over_http(app_client):
    e, mk = app_client
    client = mk()
    await client.start_server()
    try:
        bad = {"type": "failure_schedule", "trigger": {"kind": "delay", "delay_s": 10},
               "injects": [{"subsystem": "aocs", "failure": "rw_seizure", "wheel": 9}]}
        r = await client.post("/api/command", json=bad)
        body = await r.json()
        assert r.status == 400 and "injects[0]" in body["message"]
        good = {"type": "failure_schedule", "trigger": {"kind": "delay", "delay_s": 10},
                "injects": [{"subsystem": "aocs", "failure": "rw_seizure", "wheel": 1}]}
        r = await client.post("/api/command", json=good)
        assert r.status == 200, await r.text()
        assert e.instructor_rec.schedule_list()
        r = await client.post("/api/command", json={"type": "schedule_cancel", "schedule_id": "nope"})
        assert r.status == 400
        # snapshot_before / label are meta keys, not failure parameters
        r = await client.post("/api/command", json={"type": "failure_inject", "subsystem": "tcs",
            "failure": "sensor_drift", "magnitude": 2, "zone": "battery", "snapshot_before": True})
        assert r.status == 200, await r.text()
        bps = await (await client.get("/api/breakpoints")).json()
        assert all("auto" in b for b in bps)
    finally:
        await client.close()


# ── 6. server-side guard ───────────────────────────────────────────────────

#: Instructor-only content that must never reach the ground (the state
#: summary crosses the space link and feeds /ws, rfsim and the planner).
DENY = ("divergence", "timeline", "truth", "clock_truth", "instructor", "fault_menu",
        "swimlane", "q_true", "omega_true", "sensor_drift", "injects", "snapshot_before")


def _keys(obj, out=None):
    out = set() if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(str(k))
            _keys(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _keys(v, out)
    return out


def test_state_feed_carries_no_instructor_data(drift_engine):
    keys = _keys({k: v for k, v in drift_engine.get_state_summary().items() if k != "params"})
    leaked = [k for k in keys if any(d in k for d in DENY)]
    assert not leaked, f"instructor data in /api/state: {leaked}"


def test_link_proxy_allowlists_new_routes_read_only():
    from smo_link import httpproxy as hp
    for path in ("/api/instructor/views", "/api/instructor/timeline",
                 "/api/instructor/fault-menu", "/api/instructor/history",
                 "/api/instructor/debrief"):
        assert path in hp.READ_EXACT, path
        assert path not in hp.COMMAND_EXACT


def test_instructor_routes_not_mounted_on_ground_servers():
    for server in ("packages/smo-mcs/src/smo_mcs/server.py",
                   "packages/smo-planner/src/smo_planner/server.py"):
        assert "/api/instructor/" not in (REPO / server).read_text()


def test_page_never_sends_truth_on_the_websocket():
    js = (MODERN / "instructor.js").read_text()
    assert ".send(" not in js
    # the truth feeds are polled, never subscribed on /ws
    for path in ("/api/instructor/views", "/api/instructor/timeline"):
        assert path in js


# ── 7. page structure (the design's fixed elements) ────────────────────────


def test_page_structure():
    html = (MODERN / "index.html").read_text()
    for el in ('id="overview"', 'id="focus"', 'id="focus-reason"', 'id="btn-focus-back"',
               'id="btn-focus-pin"', 'id="focus-auto"', 'id="timeline-panel"', 'id="rail"',
               'id="elements"', 'id="fail-trigger"', 'id="fail-snapshot"', 'id="inject-review"',
               'id="btn-add-batch"', 'id="schedule-list"', 'id="view-debrief"', 'id="view-prep"',
               "INSTRUCTOR · TRUTH"):
        assert el in html, el


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_focus_state_machine_and_timeline_helpers():
    r = subprocess.run([NODE, str(Path(__file__).parent / "js" / "test_instructor_focus.mjs"), str(MODERN)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("ok ")
