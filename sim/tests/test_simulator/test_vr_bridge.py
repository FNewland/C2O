"""VR visualisation bridge — smo-vr/1 (docs/VR_INTERFACE_ICD.md).

Covers the frame builder against a real engine (frame conventions, deployment
mapping), the return-line parser and health classification, the TCP and
WebSocket transports end to end, the instructor /api/vr route and badge, the
server's config precedence, and — because every VR team develops against the
stand-alone stub — that tools/vr_stub/vr_stub.py emits the SAME message shape,
parses status lines the same way, and that the shipped sample files are not
stale.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from smo_common import attitude as att
from smo_simulator import vr_bridge as vb

ROOT = Path(__file__).resolve().parents[2]
STUB_DIR = ROOT / "tools" / "vr_stub"


def _load_stub():
    spec = importlib.util.spec_from_file_location("vr_stub",
                                                  STUB_DIR / "vr_stub.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


stub = _load_stub()


@pytest.fixture(scope="module")
def engine():
    from smo_simulator.engine import SimulationEngine
    e = SimulationEngine(str(ROOT / "configs" / "eosat1"))
    for _ in range(3):
        e._tick_once(1.0)
    e._publish_snapshot()
    return e


def _shape(d):
    """Recursive key structure of a frame (values' types for leaves)."""
    if isinstance(d, dict):
        return {k: _shape(v) for k, v in d.items()}
    if isinstance(d, list):
        return ("list", len(d))
    if isinstance(d, bool):
        return "bool"
    if isinstance(d, (int, float)):
        return "num"
    return type(d).__name__


def _rot(q, v):
    return att.quat_to_dcm(np.asarray(q, float)).T @ np.asarray(v, float)


# ── frame builder ────────────────────────────────────────────────────────

class TestFrameBuilder:

    def test_published_and_json_serialisable(self, engine):
        body = engine.get_vr_state()
        assert body is not None
        json.dumps(body)
        assert body["tick"] == engine._tick_count
        for key in ("orbit", "attitude", "sun", "earth", "deploy", "mission"):
            assert key in body

    def test_unit_vectors_and_frame_consistency(self, engine):
        b = vb.build_vr_state(engine)
        for v in (b["sun"]["dir_eci"], b["sun"]["dir_body"],
                  b["earth"]["dir_body"]):
            assert np.linalg.norm(v) == pytest.approx(1.0, abs=1e-5)
        q = b["attitude"]["q_body_to_eci"]
        assert np.linalg.norm(q) == pytest.approx(1.0, abs=1e-6)
        # dir_body rotated back into ECI must be dir_eci
        assert np.allclose(_rot(q, b["sun"]["dir_body"]), b["sun"]["dir_eci"],
                           atol=1e-5)
        pos = np.asarray(b["orbit"]["pos_eci_km"])
        assert np.allclose(_rot(q, b["earth"]["dir_body"]),
                           -pos / np.linalg.norm(pos), atol=1e-5)
        assert b["earth"]["radius_km"] == pytest.approx(6371.0)

    def test_quaternion_is_body_to_eci_nadir(self, engine):
        """ICD §6 check: in nadir pointing, body +Z rotated by q points
        straight down, +X along velocity, and earth.dir_body = +Z."""
        o = engine.orbit.state
        s = engine.subsystems["aocs"]._state
        saved = list(s.q_true)
        try:
            s.q_true = [float(x) for x in att.dcm_to_quat(
                att.lvlh_dcm(o.pos_eci, o.vel_eci))]
            b = vb.build_vr_state(engine)
        finally:
            s.q_true = saved
        q = b["attitude"]["q_body_to_eci"]
        nadir = -np.asarray(o.pos_eci) / np.linalg.norm(o.pos_eci)
        assert np.dot(_rot(q, [0, 0, 1]), nadir) > 0.9999
        assert np.dot(_rot(q, [1, 0, 0]),
                      np.asarray(o.vel_eci) / np.linalg.norm(o.vel_eci)) > 0.99
        assert np.allclose(b["earth"]["dir_body"], [0, 0, 1], atol=1e-4)

    def test_gmst_matches_propagator_longitude(self, engine):
        """Rotating the ECI position by -gmst must reproduce lon_deg."""
        b = vb.build_vr_state(engine)
        g = math.radians(b["earth"]["gmst_deg"])
        x, y, _ = b["orbit"]["pos_eci_km"]
        lon = math.degrees(math.atan2(-math.sin(g) * x + math.cos(g) * y,
                                      math.cos(g) * x + math.sin(g) * y))
        assert lon == pytest.approx(b["orbit"]["lon_deg"], abs=0.05)

    def test_wing_deployment_mapping(self, engine):
        es = engine.subsystems["eps"]._state
        saved = (es.wing_py_deployed, es.wing_py_deploying,
                 es.wing_my_deployed, es.wing_my_deploying,
                 es.wing_deploy_timer)
        try:
            es.wing_py_deployed, es.wing_py_deploying = False, True
            es.wing_my_deployed, es.wing_my_deploying = True, False
            es.wing_deploy_timer = 0.25 * engine.subsystems[
                "eps"]._wing_deploy_time_s
            d = vb.build_vr_state(engine)["deploy"]
        finally:
            (es.wing_py_deployed, es.wing_py_deploying, es.wing_my_deployed,
             es.wing_my_deploying, es.wing_deploy_timer) = saved
        assert d["wing_py"] == {"state": "DEPLOYING", "fraction": 0.75}
        assert d["wing_my"] == {"state": "DEPLOYED", "fraction": 1.0}

    @pytest.mark.parametrize("truth,sensor,state", [
        (False, 1, "STOWED"), (True, 2, "DEPLOYED"), (False, 3, "JAMMED"),
        (True, 3, "DEPLOYED"), (False, 0, "STOWED")])
    def test_antenna_mapping(self, engine, truth, sensor, state):
        ts = engine.subsystems["ttc"]._state
        saved = (ts.antenna_deployed, ts.antenna_deployment_sensor)
        try:
            ts.antenna_deployed, ts.antenna_deployment_sensor = truth, sensor
            a = vb.build_vr_state(engine)["deploy"]["antenna"]
        finally:
            ts.antenna_deployed, ts.antenna_deployment_sensor = saved
        assert a["state"] == state and a["deployed"] is truth

    def test_state_summary_carries_vr_link(self, engine):
        engine.vr_link = {"enabled": True, "n_clients": 0,
                          "overall": "NO_CLIENTS", "clients": []}
        try:
            assert engine._build_state_summary()["vr_link"]["overall"] \
                == "NO_CLIENTS"
        finally:
            engine.vr_link = None


# ── return line ──────────────────────────────────────────────────────────

PARSE_CASES = [
    ('{"type":"status","status_word":15}', True),
    ('{"type":"status","status_word":15,"state":"ok","team":"T1",'
     '"fps":72,"seq_ack":9,"text":"hi","extra":1}', True),
    ('{"type":"status","status_word":65536}', False),
    ('{"type":"status","status_word":-1}', False),
    ('{"type":"status","status_word":"15"}', False),
    ('{"type":"status","status_word":true}', False),
    ('{"type":"status","status_word":15,"state":"FINE"}', False),
    ('{"type":"ping"}', False),
    ('[1,2]', False),
    ('not json', False),
    ('   ', False),
    (b'\xff\xfe', False),
]


@pytest.mark.parametrize("text,ok", PARSE_CASES)
def test_parse_client_message(text, ok):
    msg, err = vb.parse_client_message(text)
    assert (msg is not None) is ok and (err is None) is ok


@pytest.mark.parametrize("text,ok", PARSE_CASES)
def test_stub_parser_agrees_with_simulator(text, ok):
    assert stub.parse_client_message(text) == vb.parse_client_message(text)


class TestHealth:

    def _mon(self):
        mon = vb.VRLinkMonitor(8100, 8101)
        return mon, mon.register("tcp", "x")

    def test_no_reply_is_not_a_fault(self):
        mon, c = self._mon()
        assert mon.summary()["overall"] == "NO_REPLY"

    @pytest.mark.parametrize("line,health", [
        ('{"type":"status","status_word":15}', "OK"),
        ('{"type":"status","status_word":255,"state":"OK"}', "OK"),
        ('{"type":"status","status_word":7}', "DEGRADED"),
        ('{"type":"status","status_word":15,"state":"WARN"}', "DEGRADED"),
        ('{"type":"status","status_word":15,"state":"ERROR"}', "ERROR"),
    ])
    def test_classification(self, line, health):
        mon, c = self._mon()
        assert mon.on_text(c, line) is None
        s = mon.summary()
        assert s["clients"][0]["health"] == health and s["overall"] == health

    def test_silent_after_timeout(self, monkeypatch):
        mon, c = self._mon()
        mon.on_text(c, '{"type":"status","status_word":15}')
        c.last_rx -= vb.SILENT_AFTER_S + 1
        assert mon.summary()["overall"] == "SILENT"

    def test_bad_line_counted_not_fatal(self):
        mon, c = self._mon()
        assert mon.on_text(c, "garbage")
        row = mon.summary()["clients"][0]
        assert row["rx_errors"] == 1 and row["health"] == "NO_REPLY"

    def test_worst_client_wins(self):
        mon = vb.VRLinkMonitor()
        a, b = mon.register("tcp", "a"), mon.register("ws", "b")
        mon.on_text(a, '{"type":"status","status_word":15}')
        mon.on_text(b, '{"type":"status","status_word":1}')
        assert mon.summary()["overall"] == "DEGRADED"
        mon.unregister(b)
        assert mon.summary()["overall"] == "OK"


# ── transports end to end ────────────────────────────────────────────────

def test_tcp_and_websocket_round_trip(engine):
    async def run():
        import aiohttp
        summaries = []
        bridge = vb.VRBridge(engine.get_vr_state, host="127.0.0.1",
                             tcp_port=0, ws_port=0, max_rate_hz=20,
                             on_summary=summaries.append)
        await bridge.start()
        try:
            r, w = await asyncio.open_connection("127.0.0.1", bridge.tcp_port)
            hello = json.loads(await asyncio.wait_for(r.readline(), 5))
            assert hello["type"] == "hello" and hello["schema"] == vb.SCHEMA
            st = json.loads(await asyncio.wait_for(r.readline(), 5))
            assert st["type"] == "state" and st["seq"] >= 1
            w.write(b"garbage\n")
            w.write((json.dumps({"type": "status", "team": "TCP1",
                                 "status_word": 15, "seq_ack": st["seq"]})
                     + "\n").encode())
            await w.drain()
            async with aiohttp.ClientSession() as s:
                async with s.ws_connect(
                        f"http://127.0.0.1:{bridge.ws_port}/vr") as ws:
                    m = json.loads((await ws.receive(timeout=5)).data)
                    assert m["type"] == "hello"
                    await ws.send_str(json.dumps(
                        {"type": "status", "team": "WS1", "status_word": 3}))
                    engine._tick_once(1.0)
                    engine._publish_snapshot()
                    seen = 0
                    while seen < 2:
                        m = json.loads((await ws.receive(timeout=5)).data)
                        assert m["type"] == "state"
                        seen += 1
                    await asyncio.sleep(0.2)
                    summ = bridge.monitor.summary()
            teams = {c["team"]: c for c in summ["clients"]}
            assert teams["TCP1"]["health"] == "OK"
            assert teams["TCP1"]["rx_errors"] == 1
            assert teams["WS1"]["health"] == "DEGRADED"
            assert summ["overall"] == "DEGRADED"
            assert summaries and summaries[-1]["enabled"] is True
            w.close()
        finally:
            await bridge.stop()
    asyncio.run(run())


def test_frames_repeat_as_keepalive_when_frozen():
    body = {"tick": 5, "sim_time": "x"}

    async def run():
        bridge = vb.VRBridge(lambda: body, host="127.0.0.1", tcp_port=0,
                             ws_port=None, max_rate_hz=20)
        await bridge.start()
        try:
            r, w = await asyncio.open_connection("127.0.0.1", bridge.tcp_port)
            await r.readline()                  # hello
            first = json.loads(await asyncio.wait_for(r.readline(), 3))
            nxt = json.loads(await asyncio.wait_for(r.readline(), 3))
            assert nxt["tick"] == first["tick"] == 5
            assert nxt["seq"] == first["seq"] + 1
            w.close()
        finally:
            await bridge.stop()
    asyncio.run(run())


# ── wiring ───────────────────────────────────────────────────────────────

class TestWiring:

    def test_config_precedence(self):
        from smo_simulator.server import resolve_vr_config, build_parser
        net = SimpleNamespace(vr_enabled=True, vr_tcp_port=8100,
                              vr_ws_port=8101, vr_max_rate_hz=10.0)
        args = build_parser().parse_args([])
        assert resolve_vr_config(args, net, env={}) == {
            "tcp_port": 8100, "ws_port": 8101, "max_rate_hz": 10.0}
        assert resolve_vr_config(args, net, env={"SMO_VR_PORT": "9100"})[
            "tcp_port"] == 9100
        args = build_parser().parse_args(["--vr-port", "7100"])
        assert resolve_vr_config(args, net, env={"SMO_VR_PORT": "9100"})[
            "tcp_port"] == 7100
        assert resolve_vr_config(args, net, env={"SMO_VR": "0"}) is None
        assert resolve_vr_config(build_parser().parse_args(["--no-vr"]),
                                 net, env={}) is None
        net.vr_enabled = False
        assert resolve_vr_config(build_parser().parse_args([]), net,
                                 env={}) is None

    def test_mission_config_declares_ports(self):
        from smo_common.config.loader import load_mission_config
        n = load_mission_config(ROOT / "configs" / "eosat1").network
        assert (n.vr_tcp_port, n.vr_ws_port) == (8100, 8101)

    def test_instructor_api_vr(self, engine):
        from aiohttp.test_utils import TestClient, TestServer
        from smo_simulator.instructor.app import create_instructor_app

        async def run():
            app = create_instructor_app(engine)
            async with TestClient(TestServer(app)) as client:
                resp = await client.get("/api/vr")
                assert resp.status == 200
                data = await resp.json()
                assert data["link"] == {"enabled": False}
                assert data["frame"]["orbit"]["pos_eci_km"]
        asyncio.run(run())

    def test_instructor_badge_is_wired(self):
        static = ROOT / "packages/smo-simulator/src/smo_simulator/instructor/static/modern"
        assert 'id="vr-badge"' in (static / "index.html").read_text("utf-8")
        js = (static / "instructor.js").read_text("utf-8")
        assert "renderVrBadge(state.vr_link)" in js


# ── the stub every team develops against ─────────────────────────────────

class TestStubParity:

    def test_state_shape_matches_simulator(self, engine):
        sim = vb.build_vr_state(engine)
        st = stub.Story("once").body(1000.0, 1000)
        assert _shape(st) == _shape(sim)

    def test_hello_matches_simulator(self):
        a = vb.build_hello("x", 10.0, 8100, 8101)
        b = stub.build_hello("x", 10.0, 8100, 8101)
        assert a == b

    def test_constants_match(self):
        assert stub.SCHEMA == vb.SCHEMA
        assert stub.STATUS_BITS == vb.STATUS_BITS
        assert stub.HEALTHY_MASK == vb.HEALTHY_MASK
        assert stub.DEFAULT_TCP_PORT == vb.DEFAULT_TCP_PORT
        assert stub.DEFAULT_WS_PORT == vb.DEFAULT_WS_PORT

    def test_stub_enums_are_simulator_enums(self):
        story = stub.Story("once")
        for t in range(0, int(stub.PERIOD_S), 50):
            b = story.body(float(t), t)
            assert b["attitude"]["aocs_mode"] in vb.AOCS_MODE_NAMES.values()
            assert b["attitude"]["pointing"] in vb.POINTING_NAMES.values()
            assert b["mission"]["phase"] in vb.PHASE_NAMES
            assert b["mission"]["sc_mode"] in vb.SC_MODE_NAMES.values()
            assert b["deploy"]["antenna"]["state"] in (
                "STOWED", "DEPLOYED", "JAMMED")

    def test_stub_nadir_convention(self):
        b = stub.Story("once").body(2500.0, 2500)
        pos = np.asarray(b["orbit"]["pos_eci_km"])
        z = _rot(b["attitude"]["q_body_to_eci"], [0, 0, 1])
        assert np.dot(z, -pos / np.linalg.norm(pos)) > 0.9999
        assert np.allclose(b["earth"]["dir_body"], [0, 0, 1], atol=1e-4)
        assert np.allclose(_rot(b["attitude"]["q_body_to_eci"],
                                b["sun"]["dir_body"]), b["sun"]["dir_eci"],
                           atol=1e-5)

    def test_stub_orbit_tracks_simulator(self, engine):
        from datetime import timedelta
        from smo_simulator.engine import SimulationEngine
        e = SimulationEngine(str(ROOT / "configs" / "eosat1"))
        t0 = e._sim_time
        for t in (0.0, 1500.0, 3000.0):
            o = e.orbit.propagate_to(t0 + timedelta(seconds=t))
            b = stub.Story("once").body(t, int(t))
            d = np.linalg.norm(np.asarray(o.pos_eci) - b["orbit"]["pos_eci_km"])
            assert d < 60.0, f"t={t}: stub {d:.1f} km from the simulator"
            assert b["sun"]["in_eclipse"] == bool(o.in_eclipse)
            assert b["earth"]["gmst_deg"] == pytest.approx(
                vb.gmst_deg_at(o.utc), abs=1e-3)

    def test_sample_files_are_current(self, tmp_path):
        nd, cs = stub.write_sample(str(tmp_path))
        for name, fresh in (("sample_vr_frames.ndjson", nd),
                            ("sample_vr_frames.csv", cs)):
            shipped = (STUB_DIR / name).read_text("utf-8")
            assert Path(fresh).read_text("utf-8") == shipped, (
                f"{name} is stale — run: python3 tools/vr_stub/vr_stub.py "
                f"--write-sample tools/vr_stub")

    def test_sample_story_covers_every_state(self):
        lines = (STUB_DIR / "sample_vr_frames.ndjson").read_text(
            "utf-8").splitlines()
        assert json.loads(lines[0])["type"] == "hello"
        frames = [json.loads(x) for x in lines[1:]]
        wings = {f["deploy"]["wing_py"]["state"] for f in frames}
        assert wings == {"STOWED", "DEPLOYING", "DEPLOYED"}
        assert {f["deploy"]["antenna"]["state"] for f in frames} == {
            "STOWED", "DEPLOYED"}
        assert {f["sun"]["in_eclipse"] for f in frames} == {True, False}
        assert {f["mission"]["in_contact"] for f in frames} == {True, False}
        assert [f["seq"] for f in frames] == list(range(1, len(frames) + 1))
