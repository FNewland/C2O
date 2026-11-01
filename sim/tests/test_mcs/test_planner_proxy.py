"""Same-origin planner access from the MCS page (R3 A2).

The MCS used to hand the browser its INTERNAL planner address
(``http://127.0.0.1:9091``) through /api/client-config. On a laptop that is
cross-origin (CORS blocks it); behind the c2o.live load balancer the browser
cannot reach it at all (MCS is ops.c2o.live, the planner plan.c2o.live behind
IAP). The burn-plan confirmation and the classic ground-track map broke.

Now the page calls ``/planner/api/...`` on its own origin and the MCS server
forwards it to the planner — GET only, ``api/`` paths only.
"""
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.config.schemas import MCSDisplayConfig
from smo_mcs.server import MCSServer


def _server():
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}), \
         patch("smo_mcs.server.load_tc_catalog", return_value=[]):
        return MCSServer(config_dir="/tmp/fake_config", connect_host="localhost",
                         connect_port=9999, http_port=0)


def _mcs_app(srv):
    app = web.Application()
    app.router.add_get("/planner/{path:api/.+}", srv._handle_planner_proxy)
    app.router.add_get("/api/client-config", srv._handle_client_config)
    return app


@pytest.fixture
async def planner():
    seen = []

    async def schedule(request):
        seen.append(dict(request.query))
        return web.json_response({"schedule": [{"name": "orbit_manoeuvre"}]})

    async def post_only(request):
        seen.append("POST")
        return web.json_response({})

    app = web.Application()
    app.router.add_get("/api/schedule", schedule)
    app.router.add_post("/api/schedule", post_only)
    async with TestServer(app) as ts:
        yield ts, seen


async def test_get_is_forwarded_with_its_query(planner):
    ts, seen = planner
    srv = _server()
    srv._planner_api_base = str(ts.make_url("")).rstrip("/")
    async with TestClient(TestServer(_mcs_app(srv))) as c:
        r = await c.get("/planner/api/schedule?state=PLANNED")
        assert r.status == 200
        assert (await r.json())["schedule"][0]["name"] == "orbit_manoeuvre"
        assert r.headers["Content-Type"].startswith("application/json")
    assert seen == [{"state": "PLANNED"}]


async def test_proxy_is_read_only_and_api_only(planner):
    ts, seen = planner
    srv = _server()
    srv._planner_api_base = str(ts.make_url("")).rstrip("/")
    async with TestClient(TestServer(_mcs_app(srv))) as c:
        assert (await c.post("/planner/api/schedule", json={})).status == 405
        assert (await c.get("/planner/modern")).status == 404
        assert (await c.get("/planner/api/../wide")).status in (400, 404)
    assert "POST" not in seen


async def test_planner_down_is_a_502_with_a_reason():
    srv = _server()
    srv._planner_api_base = "http://127.0.0.1:9"        # nothing listens
    async with TestClient(TestServer(_mcs_app(srv))) as c:
        r = await c.get("/planner/api/time-source")
        assert r.status == 502
        assert (await r.json())["error"] == "planner unreachable"


async def test_client_config_hands_the_browser_the_same_origin_base(monkeypatch):
    monkeypatch.delenv("SMO_PLANNER_PUBLIC_URL", raising=False)
    srv = _server()
    async with TestClient(TestServer(_mcs_app(srv))) as c:
        cfg = await (await c.get("/api/client-config")).json()
    assert cfg["planner_url"] == "/planner"
    assert "127.0.0.1" not in cfg["planner_url"] and "9091" not in cfg["planner_url"]


async def test_public_url_override(monkeypatch):
    monkeypatch.setenv("SMO_PLANNER_PUBLIC_URL", "https://plan.c2o.live/")
    srv = _server()
    async with TestClient(TestServer(_mcs_app(srv))) as c:
        cfg = await (await c.get("/api/client-config")).json()
    assert cfg["planner_url"] == "https://plan.c2o.live"
