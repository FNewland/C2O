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
        # worked by hand is a normal answer, not an HTTP error (the browser
        # logs every 4xx as a failed request)
        assert r.status == 200
        j = await r.json()
        assert j["runnable"] is False and j["manual"] is True and j["procedure_id"] == "NOM-001"
        assert "checklist" in j["reason"]
        r = await c.post("/api/procedure/load", json={"path": "nominal/no_such_card.md"})
        assert r.status == 404
        r = await c.post("/api/procedure/load", json={
            "source": "ops", "path": "nominal/clock_sync.md", "step_by_step": True})
        assert r.status == 200, await r.text()
        assert (await r.json())["runnable"] is True
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
        assert cl["steps"][0]["title"] and cl["mismatches"]
        r = await c.get("/api/logbook/checklist?procedure=CTG-018", headers=H)
        assert r.status == 404                     # retired card: no steps, no checklist
    finally:
        await c.close()


def test_console_feeds_the_workbook():
    js = MCS_JS.read_text(encoding="utf-8")
    # runner progress -> checklist ticks; Start / a manual card open the checklist
    assert "r.json.runnable === false" in js and "r.json.manual" not in js
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


# ── activity-type cards (NOM-002/003/004/009): runner_step_map.yaml ──────

def _step_maps():
    import yaml
    return (yaml.safe_load((CONFIG_DIR / "mcs" / "runner_step_map.yaml")
                           .read_text(encoding="utf-8")) or {})["procedures"]


def test_every_activity_type_card_has_a_step_map_that_fits_runner_and_card(server):
    from smo_common.logbook.checklist import parse_card
    maps = _step_maps()
    linked = {e["id"]: e for e in server._procedure_index
              if isinstance(e.get("runnable"), dict) and e["runnable"].get("kind") == "activity_type"}
    assert {"NOM-002", "NOM-003", "NOM-004", "NOM-009"} <= set(linked)
    assert set(maps) == set(linked), "every activity-type card is mapped, and only those"
    for pid, e in linked.items():
        m = maps[pid]
        assert m["activity_type"] == e["runnable"]["ref"], pid
        # one entry per step the RUNNER loads (the activity's command sequence)
        runner = server._indexed_procedure(pid)
        assert len(m["steps"]) == len(runner["steps"]), pid
        card = parse_card((CONFIG_DIR / "procedures" / e["file"]).read_text(encoding="utf-8"))
        keys = [s["key"] for s in card["steps"]]
        mapped = [k for k in m["steps"] if k is not None]
        assert mapped and set(mapped) <= set(keys), (pid, set(mapped) - set(keys))
        for k, note in (m.get("notes") or {}).items():
            assert k in mapped, (pid, k)
            assert note["en"].strip() and note["fr"].strip(), (pid, k)


async def test_activity_type_card_checklist_carries_the_map_and_notes(server, tmp_path):
    c = await _client(server, tmp_path)
    try:
        for pid in ("NOM-002", "NOM-003", "NOM-004", "NOM-009"):
            r = await c.post("/api/procedure/load", json={"procedure_id": pid, "step_by_step": True})
            assert r.status == 200, await r.text()
            st = await (await c.get("/api/procedure/status")).json()
            assert st["procedure_ref"] == pid
            cl = await (await c.get(f"/api/logbook/checklist?procedure={pid}&lang=fr", headers=H)).json()
            assert cl["runnable"], pid
            assert len(cl["runner_map"]) == st["total_steps"] == len(st["step_results"]), pid
            assert cl["runner_map"] == _step_maps()[pid]["steps"]
            assert cl["runner_notes"] and all(" " in v for v in cl["runner_notes"].values())
        # the notes follow the language
        en = await (await c.get("/api/logbook/checklist?procedure=NOM-003&lang=en", headers=H)).json()
        assert en["runner_notes"]["s4"].startswith("Runner:")
        assert cl["runner_notes"]["s1"].startswith("Exécuteur")      # NOM-009, French
    finally:
        await c.close()


def test_runner_results_tick_the_card_steps_of_an_activity_type_card(server, tmp_path):
    """The real runner step list of imaging_pass, folded through the map by
    the browser's own code (smo_common/ui/checklist.js runnerResults)."""
    import json
    import shutil
    import subprocess
    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        pytest.skip("node not installed")
    ui = REPO / "packages/smo-common/src/smo_common/ui"
    (tmp_path / "checklist.mjs").write_text((ui / "checklist.js").read_text(encoding="utf-8"))
    m = _step_maps()["NOM-002"]["steps"]
    n = len(server._indexed_procedure("NOM-002")["steps"])
    P, Q, F = 2, 0, 3          # PASSED, PENDING, FAILED
    cases = [[P] * 6 + [Q] * (n - 6), [P] * n, [P] * 10 + [F] + [Q] * (n - 11)]
    (tmp_path / "run.mjs").write_text(
        'import * as C from "./checklist.mjs";\n'
        f"const m = {json.dumps(m)}; const cases = {json.dumps(cases)};\n"
        "console.log(JSON.stringify(cases.map((c) => C.runnerResults(m, "
        "c.map((r, i) => ({index: i, result: r})), [\"s1\", \"s2\", \"s3\"]))));\n")
    p = subprocess.run([node, str(tmp_path / "run.mjs")], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    early, done, failed = json.loads(p.stdout)
    assert early == {"s2": "go"}            # s1 still waits on runner steps 6-9
    assert done == {"s1": "go", "s2": "go", "s4": "pass", "s5": "pass", "s6": "pass"}
    assert failed["s4"] == "fail"


def test_workbook_carries_the_runner_note_with_the_tick():
    js = (REPO / "packages/smo-common/src/smo_common/ui/workbook.js").read_text(encoding="utf-8")
    assert "runnerNote: (W.cl.runner_notes || {})[key]" in js
    assert "|| opts.runnerNote" in js
