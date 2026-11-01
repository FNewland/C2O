"""MCS HTTP delivery (R3 audit A8): gzip + cache headers via the shared
smo_common.web.http policy, the same one the planner and instructor use.

Over c2o.live every console reload used to cost 1-2 MB: no compression and
`no-cache` on everything. Pinned here:
  - the MCS server wires apply_http_policy (not a private middleware);
  - the modern index is served with content-hash ?v= stamps and no-cache;
  - a stamped asset is immutable and a large JS file is gzipped;
  - an unstamped own asset still revalidates (no-cache), vendor gets max-age.
"""
import re
from pathlib import Path
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.config.schemas import MCSDisplayConfig
from smo_common.web.http import IMMUTABLE, apply_http_policy
from smo_mcs.server import MCSServer

REPO = Path(__file__).resolve().parents[2]
SERVER = REPO / "packages/smo-mcs/src/smo_mcs/server.py"
STATIC = REPO / "packages/smo-mcs/src/smo_mcs/static"


def _server():
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}), \
         patch("smo_mcs.server.load_tc_catalog", return_value=[]):
        return MCSServer(config_dir="/tmp/fake_config", connect_host="localhost",
                         connect_port=9999, http_port=0)


def _app(srv):
    import smo_common
    app = web.Application()
    apply_http_policy(app, revalidate_prefixes=("/static/",),
                      max_age_prefixes={"/static/vendor/": 86400})
    srv._http_app = app
    srv._ui_mode = "modern"
    app.router.add_get("/", srv._handle_index)
    app.router.add_static("/static/shared/", Path(smo_common.__file__).parent / "ui")
    app.router.add_static("/static/", STATIC)
    return app


def test_server_uses_the_shared_policy():
    src = SERVER.read_text(encoding="utf-8")
    assert "apply_http_policy(app" in src
    assert "_no_cache_own_assets" not in src


async def test_index_is_stamped_and_assets_are_gzipped_and_immutable():
    srv = _server()
    async with TestClient(TestServer(_app(srv))) as c:
        r = await c.get("/")
        assert r.status == 200
        assert r.headers["Cache-Control"] == "no-cache"
        html = await r.text()
        m = re.search(r'src="(/static/modern/mcs\.js\?v=[0-9a-f]+)"', html)
        assert m, "mcs.js is not stamped with its content hash"
        js = await c.get(m.group(1), headers={"Accept-Encoding": "gzip"})
        assert js.status == 200
        assert js.headers.get("Content-Encoding") == "gzip"
        assert js.headers["Cache-Control"] == IMMUTABLE
        plain = await c.get("/static/shared/state.js")
        assert plain.headers["Cache-Control"] == "no-cache"
