"""wall.c2o.live (tools/wall.py): the planner's wall page, public and read-only.

The server is the allowlist, so these tests pin it: the page and its feeds work, every
other planner route is refused, writes are refused, cross-service answers are cut down to
what the page reads, queries are rebuilt, and a room of viewers costs one upstream fetch.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

SIM = Path(__file__).resolve().parents[2]
ROOT = SIM.parent


def _load():
    spec = importlib.util.spec_from_file_location("_tw_wall", SIM / "tools" / "wall.py")
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = mod          # dataclasses look their module up while defining
    spec.loader.exec_module(mod)
    return mod


wall = _load()


def _upstream(calls: list):
    """A fake planner + MCS + radio on one app; records every path it is asked for."""
    async def h(request):
        calls.append(request.path_qs)
        p = request.path
        if p == "/wide":
            return web.Response(text="<!DOCTYPE html><title>wall</title>", content_type="text/html")
        if p == "/api/config/planner":
            return web.json_response({"planner_config": {"horizons": {"timeline_hours": 24},
                                                         "services": {"mcs_url": "http://10.0.0.1:9090"}},
                                      "budget_sources": {"secret": "x"}})
        if p == "/api/state":
            return web.json_response({"derived": {"pass_fit": "ok"}, "params": {"0x0300": 1},
                                      "operators": ["someone@c2o.live"]})
        if p == "/api/pass-rollups":
            return web.json_response({"rollups": [{"n": i} for i in range(9)], "active": None,
                                      "debug": "x"})
        if p.startswith("/static/"):
            return web.Response(body=b"// js", content_type="text/javascript")
        if p.startswith("/api/"):
            return web.json_response({"path": p})
        return web.Response(status=404)
    app = web.Application()
    app.router.add_route("*", "/{t:.*}", h)
    return app


def _with_wall(fn):
    async def run():
        calls: list = []
        up = TestServer(_upstream(calls))
        await up.start_server()
        base = f"http://127.0.0.1:{up.port}"
        app = wall.build_app(wall.Upstreams(planner=base, mcs=base, radio=base))
        async with TestClient(TestServer(app)) as c:
            await fn(c, calls)
        await up.close()
    asyncio.run(run())


def test_the_page_and_every_feed_it_polls_work():
    async def body(c, calls):
        r = await c.get("/")
        assert r.status == 200 and "wall" in await r.text()
        assert "frame-ancestors" in r.headers["Content-Security-Policy"]
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        for p in wall.PLANNER_FEEDS:
            r = await c.get(p)
            assert r.status == 200 and (await r.json())["path"] == p
            assert r.headers["Access-Control-Allow-Origin"] == "*"
        for p in ("/static/modern/wide.js", "/static/shared/i18n.js", "/static/shared/design-system.css",
                  "/static/shared/fonts/ibm-plex-sans-latin-400-normal.woff2",
                  "/static/shared/i18n/fr.db.json", "/static/modern/i18n/fr.json"):
            assert (await c.get(p)).status == 200, p
    _with_wall(body)


def test_everything_else_is_refused():
    async def body(c, calls):
        for p in ("/api/activities", "/api/schedule/clear", "/api/upload", "/api/config/alignment",
                  "/static/modern/planner.js", "/static/index.html", "/static/vendor/x.js",
                  "/static/shared/../../server.py", "/static//shared/i18n.js", "/mcs/api/tc",
                  "/rf/api/x", "/admin", "/api/schedule/1"):
            assert (await c.get(p)).status == 404, p
        for m in ("POST", "PUT", "DELETE", "PATCH"):
            assert (await c.request(m, "/api/schedule")).status == 405
        assert not any("activities" in x or "clear" in x for x in calls)
    _with_wall(body)


def test_cross_service_answers_are_cut_down_and_addresses_rewritten():
    async def body(c, calls):
        cfg = await (await c.get("/api/config/planner")).json()
        assert set(cfg) == {"planner_config"}                      # budget sources dropped
        assert cfg["planner_config"]["services"] == {"mcs_url": "/mcs", "rfsim_url": "/rf"}
        assert await (await c.get("/mcs/api/state")).json() == {"derived": {"pass_fit": "ok"}}
        rf = await (await c.get("/rf/api/pass-rollups?limit=999")).json()
        assert set(rf) == {"rollups", "active"} and len(rf["rollups"]) == 5
        assert "/api/pass-rollups?limit=5" in calls
    _with_wall(body)


def test_queries_are_rebuilt_not_passed_through():
    async def body(c, calls):
        await c.get("/api/ground-track?duration_hours=99999&step_s=0.001&evil=1")
        await c.get("/api/ground-track?duration_hours=nan")
        await c.get("/api/schedule?x=1")
        await c.get("/?lang=fr&ui=classic")
        await c.get("/?lang=../../x")
        track = [x for x in calls if x.startswith("/api/ground-track")]
        assert track == ["/api/ground-track?duration_hours=48&step_s=120",
                         "/api/ground-track?duration_hours=24&step_s=120"]
        assert "/api/schedule" in calls and not any("x=1" in x for x in calls)
        assert "/wide?ui=modern&lang=fr" in calls and "/wide?ui=modern" in calls
        assert not any("evil" in x or ".." in x for x in calls)
    _with_wall(body)


def test_a_room_of_viewers_costs_one_upstream_fetch():
    async def body(c, calls):
        rs = await asyncio.gather(*[c.get("/api/spacecraft-state") for _ in range(40)])
        assert all(r.status == 200 for r in rs)
        assert calls.count("/api/spacecraft-state") == 1
    _with_wall(body)


def test_a_dead_planner_is_retried_quickly():
    async def run():
        t = [0.0]
        app = wall.build_app(wall.Upstreams(planner="http://127.0.0.1:9", mcs=None, radio=None),
                             clock=lambda: t[0])
        async with TestClient(TestServer(app)) as c:
            assert (await c.get("/api/schedule")).status == 502
            e = app["wall"]._cache["/api/schedule"]
            t[0] += 2.1
            assert t[0] - e.at >= wall.PLANNER_FEEDS["/api/schedule"]      # expired: retried
    asyncio.run(run())


def test_the_deployment_carries_the_wall_without_sign_in():
    common = (ROOT / "deploy" / "gcp" / "common.sh").read_text()
    assert re.search(r"^wall\s+wall\s+8099\s+ground\s+public\b", common, re.M)
    setup = (ROOT / "deploy" / "gcp" / "setup.sh").read_text()
    assert "tcp:8099" in setup and 'tool_public_be' in setup and '[ "$5" = public ] && return 0' in setup
    compose = (SIM / "docker" / "compose.yaml").read_text()
    assert '"tools/wall.py"' in compose and ":8099:8099" in compose
    assert "tools/wall.py" in (SIM / "start.sh").read_text()
