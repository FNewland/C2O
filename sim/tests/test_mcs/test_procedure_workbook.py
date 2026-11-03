"""MCS side of the ops workbook (2026-11-02): an ops card picked in the
procedure panel either runs (runnable card) or is worked by hand from its
live checklist; the checklist served by the MCS lines up with what the
runner executes; the console feeds the checklist and the forms."""
from pathlib import Path
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.config.schemas import MCSDisplayConfig
from smo_common.logbook import register_logbook_routes
from smo_mcs.server import MCSServer

REPO = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO / "configs" / "eosat1"
MCS_JS = REPO / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js"
H = {"X-Goog-Authenticated-User-Email": "accounts.google.com:fd@example.org"}


@pytest.fixture
def server(tmp_path):
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value={}):
        s = MCSServer(config_dir=str(CONFIG_DIR), connect_host="localhost",
                      connect_port=9999, http_port=0)
    # every parameter a runnable card checks is "known" (no live spacecraft)
    s._tlm_vocabulary = lambda: None
    return s


async def _client(server, tmp_path):
    app = web.Application()
    register_logbook_routes(app, tool="mcs", store_dir=tmp_path / "lb",
                            worksheets_dir=CONFIG_DIR / "worksheets",
                            checklists=server._checklist_provider)
    app.router.add_post("/api/procedure/load", server._handle_proc_load)
    app.router.add_get("/api/procedure/status", server._handle_proc_status)
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


async def test_ops_card_by_path_runs_or_is_worked_by_hand(server, tmp_path):
    c = await _client(server, tmp_path)
    try:
        r = await c.post("/api/procedure/load", json={
            "source": "ops", "id": "nominal/startup.md", "path": "nominal/startup.md"})
        assert r.status == 409
        j = await r.json()
        assert j["manual"] is True and j["procedure_id"] == "NOM-001"
        r = await c.post("/api/procedure/load", json={"path": "nominal/no_such_card.md"})
        assert r.status == 404
        r = await c.post("/api/procedure/load", json={
            "source": "ops", "path": "nominal/clock_sync.md", "step_by_step": True})
        assert r.status == 200, await r.text()
        st = await (await c.get("/api/procedure/status")).json()
        assert st["state"] == "LOADED" and st["procedure_ref"] == "NOM-008"
        assert isinstance(st["loaded_at"], float)          # one load = one checklist run
        # the checklist's runner map has one entry per step the runner loaded
        cl = await (await c.get("/api/logbook/checklist?procedure=NOM-008", headers=H)).json()
        assert cl["runnable"] and len(cl["runner_map"]) == st["total_steps"]
        assert cl["runner_map"][0] == cl["steps"][0]["key"]
    finally:
        await c.close()


async def test_checklist_for_a_manual_card(server, tmp_path):
    c = await _client(server, tmp_path)
    try:
        cl = await (await c.get("/api/logbook/checklist?procedure=LEOP-001&lang=fr", headers=H)).json()
        assert cl["sheet_id"] == "WB-5.5-L001" and not cl["runnable"] and "runner_map" not in cl
        assert cl["steps"][0]["title"]
        assert cl["mismatches"] == []              # the printed sheet follows the card
        r = await c.get("/api/logbook/checklist?procedure=CTG-018", headers=H)
        assert r.status == 404                     # retired card: no steps, no checklist
    finally:
        await c.close()


def test_console_feeds_the_workbook():
    js = MCS_JS.read_text(encoding="utf-8")
    # runner progress -> checklist ticks; Start / a manual card open the checklist
    assert "LB.onRunner({ ...st, procedure_id: lbProcedureId() })" in js
    assert js.count("LB.openChecklist(") >= 3
    # the stepper reads the runner's real status fields
    assert "st.step_results" in js and "st.procedure_name" in js
    # alarms file an anomaly ticket; forms are prefilled from the console
    assert 'data-act="ticket"' in js and 'LB.openForm("anomaly"' in js
    assert "readParam: lbReadParam, prefill: lbPrefill, info: lbInfo" in js
    for key in ("ticket_id", "param_value", "fdir_rule", "procedure_state", "params_top3",
                "next_pass", "gonogo_open", "gonogo"):
        assert f'case "{key}"' in js, key
