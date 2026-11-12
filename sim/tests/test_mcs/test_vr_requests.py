"""VR command requests: headsets propose, only the Flight Director decides (VR_INTERFACE_ICD §7a)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_mcs import vr_requests as vq
from smo_mcs.server import MCSServer, vr_request_ports

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _desk(**kw):
    seen, log = [], []
    clock = _Clock()
    desk = vq.VRRequestDesk(tcp_port=None, ws_port=None, on_change=seen.append,
                            log=log.append, clock=clock, **kw)
    return desk, seen, log, clock


def _client(desk, cid_peer="10.0.0.5:4000"):
    out = []

    async def send(line):
        out.append(json.loads(line))
    return desk._register("tcp", cid_peer, send), out


def test_requests_map_to_the_spacecraft_commands_in_its_own_axes():
    # smo-vr/1 +Y is the spacecraft's -Y: wing 1 in EPS_DEPLOY_WING (0=+Y, 1=-Y, 2=both)
    assert vq.REQUESTS["deploy_wing_py"]["args"] == {"wing": 1}
    assert vq.REQUESTS["deploy_wing_my"]["args"] == {"wing": 0}
    assert vq.REQUESTS["deploy_both_wings"]["args"] == {"wing": 2}
    assert vq.REQUESTS["deploy_antenna"]["command"] == "TTC_DEPLOY_ANTENNA"
    cat = (CONFIG_DIR / "commands" / "tc_catalog.yaml").read_text("utf-8")
    for spec in vq.REQUESTS.values():
        assert f"name: {spec['command']}" in cat


def test_a_request_is_held_until_the_flight_director_decides():
    async def run():
        desk, seen, log, clock = _desk()
        c, out = _client(desk)
        await desk.on_text(c, json.dumps({"type": "request", "request": "deploy_antenna",
                                          "team": "T07", "text": "show the dipole"}))
        assert out[-1] == {"type": "request_ack", "schema": "smo-vr/1", "id": "R1",
                           "request": "deploy_antenna", "state": "PENDING"}
        props = desk.proposals()
        assert props[0]["state"] == "PENDING" and props[0]["team"] == "T07"
        assert props[0]["command"] == "TTC_DEPLOY_ANTENNA" and seen
        assert "R1" in log[-1] and "T07" in log[-1]
        p = await desk.decide("R1", "sent", position="flight_director", tc_seq=42)
        assert p["state"] == "SENT" and p["tc_seq"] == 42
        assert out[-1]["type"] == "request_update" and out[-1]["state"] == "SENT"
        with pytest.raises(ValueError):
            await desk.decide("R1", "declined", position="flight_director")
        with pytest.raises(KeyError):
            await desk.decide("R9", "sent", position="flight_director")
    asyncio.run(run())


def test_bad_duplicate_and_too_fast_requests():
    async def run():
        desk, seen, log, clock = _desk()
        c, out = _client(desk)
        await desk.on_text(c, "not json")
        assert out[-1]["type"] == "request_rejected"
        await desk.on_text(c, json.dumps({"type": "request", "request": "fire_thrusters"}))
        assert out[-1]["type"] == "request_rejected" and "deploy_antenna" in out[-1]["reason"]
        await desk.on_text(c, json.dumps({"type": "request", "request": "deploy_wing_py", "team": "T1"}))
        assert out[-1]["state"] == "PENDING"
        await desk.on_text(c, json.dumps({"type": "request", "request": "deploy_wing_my", "team": "T1"}))
        assert out[-1]["type"] == "request_rejected" and "every" in out[-1]["reason"]   # rate
        clock.t += 3
        await desk.on_text(c, json.dumps({"type": "request", "request": "deploy_wing_py", "team": "T1"}))
        assert out[-1]["duplicate"] is True and out[-1]["id"] == "R1"
        await desk.on_text(c, json.dumps({"type": "status", "team": "T1", "status_word": 15}))
        await desk.on_text(c, json.dumps({"type": "withdraw", "id": "R1"}))
        assert out[-1]["state"] == "WITHDRAWN"
        assert len(desk.proposals()) == 1
    asyncio.run(run())


def test_unanswered_requests_expire_and_the_team_is_told():
    async def run():
        desk, seen, log, clock = _desk()
        c, out = _client(desk)
        await desk.on_text(c, json.dumps({"type": "request", "request": "deploy_both_wings"}))
        clock.t += vq.EXPIRE_S + 1
        assert await desk.expire() == 1
        assert out[-1]["state"] == "EXPIRED"
        assert desk.proposals()[0]["state"] == "EXPIRED"
    asyncio.run(run())


def test_ports_follow_env_then_mission_config():
    class Net:
        vr_enabled = True
        vr_request_tcp_port = 8104
        vr_request_ws_port = 8105
    assert vr_request_ports(Net(), env={}) == (8104, 8105)
    assert vr_request_ports(Net(), env={"SMO_VR_REQUEST_PORT": "off"}) == (None, 8105)
    assert vr_request_ports(Net(), env={"SMO_VR": "0"}) == (None, None)


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("SMO_TM_ARCHIVE", str(tmp_path / "a.db"))
    return MCSServer(config_dir=str(CONFIG_DIR), http_port=0)


@pytest.mark.asyncio
async def test_headset_websocket_and_flight_director_decision(server):
    sent = []
    server._vr_desk = vq.VRRequestDesk(tcp_port=None, ws_port=None,
                                       on_change=server._broadcast_vr_requests,
                                       log=lambda t: server._console_log("note", t, position="vr"))
    orig = server._broadcast_vr_requests

    async def spy(props):
        sent.append(props)
        await orig(props)
    server._vr_desk._on_change = spy
    app = web.Application()
    app.router.add_get("/vr/requests", server._vr_desk.handle_ws)
    app.router.add_get("/api/vr-requests", server._handle_vr_requests_get)
    app.router.add_post("/api/vr-requests/{pid}/decide", server._handle_vr_requests_decide)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        async with client.ws_connect("/vr/requests") as ws:
            hello = json.loads((await ws.receive(timeout=5)).data)
            assert hello["channel"] == "requests" and "deploy_antenna" in hello["requests"]
            await ws.send_str(json.dumps({"type": "request", "request": "deploy_antenna", "team": "T3"}))
            ack = json.loads((await ws.receive(timeout=5)).data)
            assert ack["id"] == "R1" and ack["state"] == "PENDING"
            listing = await (await client.get("/api/vr-requests")).json()
            assert listing["requests"][0]["id"] == "R1" and listing["summary"]["pending"] == 1
            r = await client.post("/api/vr-requests/R1/decide",
                                  json={"position": "eps_tcs", "decision": "sent"})
            assert r.status == 403                     # only the Flight Director decides
            r = await client.post("/api/vr-requests/R1/decide",
                                  json={"position": "flight_director", "decision": "declined",
                                        "note": "not in contact"})
            assert r.status == 200 and (await r.json())["state"] == "DECLINED"
            upd = json.loads((await ws.receive(timeout=5)).data)
            assert upd == {"type": "request_update", "schema": "smo-vr/1", "id": "R1",
                           "request": "deploy_antenna", "team": "T3", "state": "DECLINED",
                           "note": "not in contact", "tc_seq": None}
        assert sent and sent[-1][0]["state"] == "DECLINED"
        rows = [r for r in server._archive.query_console_log() if "VR request R1" in r["text"]]
        assert len(rows) >= 2
    finally:
        await client.close()


def test_the_console_wires_the_drawer_tab():
    static = Path(__file__).resolve().parents[2] / "packages/smo-mcs/src/smo_mcs/static/modern"
    html = (static / "index.html").read_text("utf-8")
    js = (static / "mcs.js").read_text("utf-8")
    assert 'data-bd="vr"' in html and 'id="bdp-vr"' in html
    assert "vr_requests: (m) => handleVrRequests(m)" in js
    # sending goes through the console's one transport (history, authority) and arm-through
    body = js[js.index("async function vrRequestSend"):js.index("async function vrRequestDecline")]
    assert "sendPus(" in body and "needsArm(cmd)" in body and "commandAuthority(" in body
