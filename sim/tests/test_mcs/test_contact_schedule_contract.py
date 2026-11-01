"""Client/server contract for /api/displays/contact-schedule (R3 A1).

The server answers ``{"next_passes": [...], "current_contact_status": ...}``
but the modern console read ``d.passes || d.contacts || d.schedule``, so the
"What's next?" card and the Overview pass table said "no pass schedule"
forever while the timeline above them showed passes. Field-name drift between
a client and its own server is invisible until a screen is blank, so pin it:

* every ``d.<field>`` the console reads in ``loadContactSchedule`` is a key
  of the real handler's response;
* every ``c.<field>`` / ``cur.<field>`` / ``next.<field>`` the pass consumers
  (``updateNextCard``, ``renderPassTable``) read is a key of a served pass.
"""
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.config.schemas import MCSDisplayConfig
from smo_mcs.server import MCSServer

REPO = Path(__file__).resolve().parents[2]
MCS_JS = REPO / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js"


def _fn_body(js: str, name: str) -> str:
    m = re.search(r"(?:async\s+)?function\s+" + name + r"\s*\([^)]*\)\s*\{", js)
    assert m, f"{name} not found in mcs.js"
    depth, i = 0, m.end() - 1
    while i < len(js):
        if js[i] == "{":
            depth += 1
        elif js[i] == "}":
            depth -= 1
            if depth == 0:
                # comments may quote the old field names; only code counts
                return re.sub(r"//[^\n]*|/\*.*?\*/", "", js[m.end():i], flags=re.S)
        i += 1
    raise AssertionError(f"unterminated {name}")


def _server():
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}), \
         patch("smo_mcs.server.load_tc_catalog", return_value=[]):
        return MCSServer(config_dir="/tmp/fake_config", connect_host="localhost",
                         connect_port=9999, http_port=0)


@pytest.fixture
async def served():
    srv = _server()
    now = srv.sim_now_ts()
    srv._planner_api_base = "http://127.0.0.1:9"     # unreachable: no network
    srv._contact_scheduler.update_passes([MCSServer._normalize_contact({
        "aos": now + 600, "los": now + 1200, "gs_name": "Troll",
        "max_elevation_deg": 42.0})])
    app = web.Application()
    app.router.add_get("/api/displays/contact-schedule", srv._handle_contact_schedule)
    async with TestClient(TestServer(app)) as client:
        r = await client.get("/api/displays/contact-schedule")
        assert r.status == 200
        yield await r.json()


async def test_client_reads_the_list_field_the_server_sends(served):
    body = _fn_body(MCS_JS.read_text(encoding="utf-8"), "loadContactSchedule")
    read = set(re.findall(r"\bd\.(\w+)", body))
    assert read, "loadContactSchedule reads no field of the response"
    missing = read - set(served)
    assert not missing, (
        f"the console reads {sorted(missing)} but the server sends {sorted(served)}")
    assert served["next_passes"], "fixture pass not served"


async def test_pass_fields_read_by_the_console_are_served(served):
    js = MCS_JS.read_text(encoding="utf-8")
    pass_keys = set(served["next_passes"][0])
    read = set()
    for fn in ("updateNextCard", "renderPassTable"):
        read |= set(re.findall(r"\b(?:c|cur|next)\.(\w+)", _fn_body(js, fn)))
    assert {"aos_time", "los_time"} <= read
    missing = read - pass_keys
    assert not missing, (
        f"pass fields {sorted(missing)} are read by the console but not served "
        f"(a pass has {sorted(pass_keys)})")
