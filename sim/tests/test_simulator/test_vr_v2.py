"""smo-vr/2: the VR channels again, in the spacecraft's own body axes (VR_INTERFACE_ICD §6c).

smo-vr/1 stays exactly as issued (+Z nadir). smo-vr/2 is the same data with +Z zenith,
+Y orbit normal, as in the operations manual; these tests hold it to the simulator's own
attitude, wings and faces, and check every place that serves or relays it.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import numpy as np
import pytest

from smo_common import attitude as att
from smo_simulator import vr_bridge as vb

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def engine():
    from smo_simulator.engine import SimulationEngine
    e = SimulationEngine(str(ROOT / "configs" / "eosat1"))
    for _ in range(3):
        e._tick_once(1.0)
    e._publish_snapshot()
    return e


def _rot(q, v):
    """v_eci = q (x) v_body (x) q*, q = [x, y, z, w]."""
    return att.quat_to_dcm(np.asarray(q, float)).T @ np.asarray(v, float)


def test_v2_is_the_simulators_own_body_frame(engine):
    aocs = engine.subsystems["aocs"]._state
    eps = engine.subsystems["eps"]._state
    saved = (list(aocs.q_true), list(aocs.omega_true), eps.wing_py_deployed, eps.wing_my_deployed)
    q_sim = np.array([0.1, -0.4, 0.3, 0.86])
    q_sim /= np.linalg.norm(q_sim)
    try:
        aocs.q_true = [float(x) for x in q_sim]
        aocs.omega_true = [0.01, -0.02, 0.03]
        eps.wing_py_deployed, eps.wing_my_deployed = True, False      # the SPACECRAFT's +Y wing
        v1 = vb.build_vr_state(engine)
        v2 = vb.to_spacecraft_axes(v1)
    finally:
        aocs.q_true, aocs.omega_true, eps.wing_py_deployed, eps.wing_my_deployed = saved
    o = engine.orbit.state
    C = att.quat_to_dcm(q_sim)                                     # ECI -> simulator body
    sun = np.asarray(o.sun_eci, float) / np.linalg.norm(o.sun_eci)
    nadir = -np.asarray(o.pos_eci, float) / np.linalg.norm(o.pos_eci)
    assert np.allclose(v2["sun"]["dir_body"], C @ sun, atol=1e-5)
    assert np.allclose(v2["earth"]["dir_body"], C @ nadir, atol=1e-5)
    assert np.allclose(v2["attitude"]["rate_body_deg_s"], np.degrees([0.01, -0.02, 0.03]), atol=1e-3)
    # the quaternion turns spacecraft-axis vectors into ECI exactly as the simulator's does
    for v in ([1, 0, 0], [0, 1, 0], [0, 0, 1]):
        assert np.allclose(_rot(v2["attitude"]["q_body_to_eci"], v), _rot(q_sim, v), atol=1e-5)
    assert np.allclose(_rot(v2["attitude"]["q_body_to_eci"], v2["sun"]["dir_body"]), sun, atol=1e-5)
    assert v2["deploy"]["wing_py"]["state"] == "DEPLOYED" and v2["deploy"]["wing_my"]["state"] == "STOWED"
    assert v1["deploy"]["wing_my"]["state"] == "DEPLOYED"        # smo-vr/1 is unchanged
    assert v2["orbit"] == v1["orbit"] and v2["mission"] == v1["mission"]


def test_v2_power_faces_and_wings_are_the_simulators(engine):
    s = engine.subsystems["eps"]._state
    v2 = vb.to_spacecraft_axes(engine.get_vr_power_state())["power"]
    for face in ("px", "mx", "py", "my", "pz", "mz"):
        body = s.sa_panel_currents[face] - s.sa_wing_currents.get(face, 0.0)
        assert v2["body_faces"][face]["current_a"] == pytest.approx(max(0.0, body), abs=1e-3)
    assert v2["wings"]["wing_py"]["current_a"] == pytest.approx(s.sa_wing_currents["py"], abs=1e-3)
    assert v2["wings"]["wing_py"]["deployed"] == bool(s.wing_py_deployed)
    assert v2["net_w"] == pytest.approx(v2["generated_w"] - v2["consumed_w"], abs=0.02)


def test_turning_twice_gives_back_smo_vr_1(engine):
    v1 = engine.get_vr_power_state()
    back = vb.to_spacecraft_axes(vb.to_spacecraft_axes(v1))
    q1, qb = np.asarray(v1["attitude"]["q_body_to_eci"]), np.asarray(back["attitude"]["q_body_to_eci"])
    assert np.allclose(q1, qb, atol=1e-9) or np.allclose(q1, -qb, atol=1e-9)
    for k in ("sun", "earth", "deploy", "power", "orbit", "mission"):
        assert back[k] == v1[k]


def test_v2_hello_names_the_spacecraft_axes():
    h = vb.build_hello("smo-simulator", 10.0, 8106, 8107, "state", vb.SCHEMA_V2)
    assert h["schema"] == "smo-vr/2" and h["channel"] == "state"
    assert h["spacecraft"]["body_axes"]["+Z"].startswith("zenith")
    assert "DO NOT USE" in h["spacecraft"]["sada"]["note"]
    h1 = vb.build_hello("smo-simulator", 10.0, 8100, 8101)
    assert "channel" not in h1 and h1["spacecraft"]["body_axes"]["+Z"].startswith("nadir")
    hp = vb.build_hello("smo-simulator", 10.0, 8108, 8109, "power", vb.SCHEMA_V2)
    assert "spacecraft body axes" in hp["power_fields"]


def test_v2_bridges_stream_and_are_told_apart(engine):
    async def run():
        import aiohttp
        summaries: dict = {}
        v1 = vb.VRBridge(engine.get_vr_state, host="127.0.0.1", tcp_port=None, ws_port=0,
                         on_summary=lambda s: summaries.__setitem__("state", s))
        v2 = vb.VRBridge(engine.get_vr_power_state, host="127.0.0.1", tcp_port=0, ws_port=0,
                         channel="power", schema=vb.SCHEMA_V2,
                         on_summary=lambda s: summaries.__setitem__("power2", s))
        await v1.start(); await v2.start()
        try:
            r, w = await asyncio.open_connection("127.0.0.1", v2.tcp_port)
            hello = json.loads(await asyncio.wait_for(r.readline(), 5))
            assert hello["schema"] == "smo-vr/2" and hello["channel"] == "power"
            m = json.loads(await asyncio.wait_for(r.readline(), 5))
            assert m["schema"] == "smo-vr/2" and "power" in m
            expect = vb.to_spacecraft_axes(engine.get_vr_power_state())
            assert m["attitude"] == expect["attitude"] and m["deploy"] == expect["deploy"]
            async with aiohttp.ClientSession() as s:
                async with s.ws_connect(f"http://127.0.0.1:{v2.ws_port}/vr2") as ws:
                    assert json.loads((await ws.receive(timeout=5)).data)["schema"] == "smo-vr/2"
                    await asyncio.sleep(1.2)
            merged = vb.merge_summaries(summaries)
            assert merged["power2_tcp_port"] == v2.tcp_port
            assert summaries["power2"]["schema"] == "smo-vr/2"
            assert {c["channel"] for c in summaries["power2"]["clients"]} <= {"power2"}
            w.close()
        finally:
            await v1.stop(); await v2.stop()
    asyncio.run(run())


def test_v2_is_mounted_on_the_http_port(engine):
    from aiohttp.test_utils import TestClient, TestServer
    from smo_simulator.instructor.app import create_instructor_app

    async def run():
        app = create_instructor_app(engine)
        b = vb.VRBridge(engine.get_vr_state, host="127.0.0.1", tcp_port=None, ws_port=None,
                        schema=vb.SCHEMA_V2)
        await b.start()
        app["vr_bridges"]["state2"] = b
        try:
            async with TestClient(TestServer(app)) as client:
                assert (await client.get("/vr2/power")).status == 503     # power2 not running
                async with client.ws_connect("/vr2") as ws:
                    assert json.loads((await ws.receive(timeout=5)).data)["schema"] == "smo-vr/2"
        finally:
            await b.stop()
    asyncio.run(run())


def test_the_link_lets_vr2_through():
    from smo_link import httpproxy
    assert {"/vr2", "/vr2/power"} <= httpproxy.VR_WS_EXACT
    assert httpproxy.route_allowed("GET", "/vr2", websocket=True)
    assert httpproxy.route_allowed("GET", "/vr2/power", websocket=True)
    assert not httpproxy.route_allowed("POST", "/vr2", websocket=False)


def test_v2_ports_are_configured():
    import yaml
    net = yaml.safe_load((ROOT / "configs" / "eosat1" / "mission.yaml").read_text("utf-8"))["network"]
    assert [net[k] for k in ("vr2_tcp_port", "vr2_ws_port", "vr2_power_tcp_port",
                             "vr2_power_ws_port")] == [8106, 8107, 8108, 8109]
    setup = (ROOT.parent / "deploy" / "gcp" / "setup.sh").read_text("utf-8")
    assert "- /vr2\n" in setup and "- /vr2/power\n" in setup


def test_the_stub_turns_frames_exactly_as_the_simulator_does(engine):
    import importlib.util
    spec = importlib.util.spec_from_file_location("vr_stub", ROOT / "tools" / "vr_stub" / "vr_stub.py")
    stub = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stub)
    body = engine.get_vr_power_state()
    assert stub.to_spacecraft_axes(body) == vb.to_spacecraft_axes(body)
    assert stub.SPACECRAFT_GEOMETRY_V2 == vb.SPACECRAFT_GEOMETRY_V2
    assert stub.build_hello("x", 10, 1, 2, "power", stub.SCHEMA_V2)["power_fields"] == \
        vb.build_hello("x", 10, 1, 2, "power", vb.SCHEMA_V2)["power_fields"]
    sample = (ROOT / "tools" / "vr_stub" / "sample_vr2_power.ndjson").read_text("utf-8").splitlines()
    hello, first = json.loads(sample[0]), json.loads(sample[1])
    assert hello["schema"] == first["schema"] == "smo-vr/2"
    pos = np.asarray(first["orbit"]["pos_eci_km"])
    assert np.allclose(_rot(first["attitude"]["q_body_to_eci"], first["earth"]["dir_body"]),
                       -pos / np.linalg.norm(pos), atol=1e-4)


def test_a_class_of_headsets_connects_at_once(engine):
    """40 headsets (20 TCP, 20 WebSocket) connect in the same instant; every one gets the
    hello and fresh frames, and the instructor summary lists them all."""
    async def run():
        import aiohttp
        b = vb.VRBridge(engine.get_vr_state, host="127.0.0.1", tcp_port=0, ws_port=0,
                        max_rate_hz=5.0)
        await b.start()
        try:
            async def tcp_headset(i):
                r, w = await asyncio.open_connection("127.0.0.1", b.tcp_port)
                hello = json.loads(await asyncio.wait_for(r.readline(), 5))
                frames = [json.loads(await asyncio.wait_for(r.readline(), 5)) for _ in range(3)]
                w.write((json.dumps({"type": "status", "team": f"T{i}", "status_word": 15}) + "\n").encode())
                await w.drain()
                return hello, frames, w

            async def ws_headset(session, i):
                ws = await session.ws_connect(f"http://127.0.0.1:{b.ws_port}/vr")
                hello = json.loads((await ws.receive(timeout=5)).data)
                frames = [json.loads((await ws.receive(timeout=5)).data) for _ in range(3)]
                return hello, frames, ws

            async with aiohttp.ClientSession() as session:
                results = await asyncio.gather(*[tcp_headset(i) for i in range(20)],
                                               *[ws_headset(session, i) for i in range(20)])
                for hello, frames, _ in results:
                    assert hello["type"] == "hello" and all(f["type"] == "state" for f in frames)
                await asyncio.sleep(1.2)
                summary = b.monitor.summary()
                assert summary["n_clients"] == 40
                assert len({c["id"] for c in summary["clients"]}) == 40
                for _, _, conn in results:
                    if hasattr(conn, "close") and not hasattr(conn, "send_str"):
                        conn.close()
                    else:
                        await conn.close()
        finally:
            await b.stop()
    asyncio.run(run())
