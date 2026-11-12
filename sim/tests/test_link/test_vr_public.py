"""The GSG's public VR port (VR_INTERFACE_ICD): /vr and /vr/power over the space link,
/vr/requests relayed to the MCS on the ground, nothing else, no sign-in or Origin needed."""
from __future__ import annotations

import json

import aiohttp
import pytest
from aiohttp import WSMsgType, web

from smo_link.httpproxy import route_allowed

from .harness import Stack, wait_for

pytestmark = pytest.mark.timeout(60)


@pytest.fixture
async def mcs():
    """A stand-in MCS: /vr/requests answers a hello and echoes, and records the peer."""
    seen = {}

    async def requests(r):
        seen["xff"] = r.headers.get("X-Forwarded-For")
        ws = web.WebSocketResponse()
        await ws.prepare(r)
        await ws.send_str('{"type":"hello","channel":"requests"}')
        async for m in ws:
            if m.type == WSMsgType.TEXT:
                await ws.send_str(json.dumps({"type": "request_ack", "echo": json.loads(m.data)}))
        return ws
    app = web.Application()
    app.router.add_get("/vr/requests", requests)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}", seen
    await runner.cleanup()


@pytest.fixture
async def stack(tmp_path, mcs):
    s = await Stack(tmp_path, vr_port=0, vr_bind="127.0.0.1", mcs_url=mcs[0]).start()
    await wait_for(lambda: s.gw.bound(), msg="link bound")
    yield s
    await s.stop()


def test_vr_streams_are_on_the_allowlist_as_websockets_only():
    assert route_allowed("GET", "/vr", websocket=True)
    assert route_allowed("GET", "/vr/power", websocket=True)
    assert not route_allowed("GET", "/vr/requests", websocket=True)   # never crosses the link
    assert not route_allowed("GET", "/vr")                            # not a plain GET


async def test_streams_cross_the_link_without_origin_or_host_checks(stack):
    base = f"ws://127.0.0.1:{stack.gw.ports['vr']}"
    async with aiohttp.ClientSession() as http:
        for path, channel in (("/vr", None), ("/vr/power", "power")):
            async with http.ws_connect(base + path, headers={"Origin": "https://elsewhere.example",
                                                             "Host": "ops.c2o.live"}) as ws:
                hello = json.loads((await ws.receive(timeout=5)).data)
                assert hello["schema"] == "smo-vr/1" and hello.get("channel") == channel
                assert json.loads((await ws.receive(timeout=5)).data)["type"] == "state"
                await ws.send_str('{"type":"status","team":"T1","status_word":15}')
                await wait_for(lambda: any("T1" in m for m in stack.sim.ws_inbound),
                               msg="status line reached the simulator")


async def test_nothing_else_is_served_on_the_vr_port(stack):
    base = f"http://127.0.0.1:{stack.gw.ports['vr']}"
    async with aiohttp.ClientSession() as http:
        for path in ("/", "/ws", "/api/command", "/api/vr", "/vr/../ws"):
            r = await http.get(base + path)
            assert r.status == 404, path
        assert (await http.get(base + "/vr")).status == 404           # a WebSocket only
        assert (await http.get(base + "/vr/healthz")).status == 200   # the load balancer's check


async def test_requests_are_relayed_to_the_mcs_on_the_ground(stack, mcs):
    base = f"ws://127.0.0.1:{stack.gw.ports['vr']}"
    async with aiohttp.ClientSession() as http:
        async with http.ws_connect(base + "/vr/requests",
                                   headers={"X-Forwarded-For": "198.51.100.4"}) as ws:
            assert json.loads((await ws.receive(timeout=5)).data)["channel"] == "requests"
            await ws.send_str('{"type":"request","request":"deploy_antenna"}')
            ack = json.loads((await ws.receive(timeout=5)).data)
            assert ack["echo"]["request"] == "deploy_antenna"
    assert mcs[1]["xff"] == "198.51.100.4"
