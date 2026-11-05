"""The workbook's pure checklist helpers (smo_common/ui/checklist.js) under
node: judging a captured value, turning runner progress into step ticks,
runs, progress and deviations. Plus the panel contract of workbook.js."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parents[2] / "packages" / "smo-common" / "src" / "smo_common" / "ui"
NODE = shutil.which("node") or shutil.which("nodejs")
needs_node = pytest.mark.skipif(not NODE, reason="node not installed")


def run(snippet: str, tmp_path: Path):
    (tmp_path / "checklist.mjs").write_text((UI / "checklist.js").read_text(encoding="utf-8"))
    (tmp_path / "run.mjs").write_text(
        'import * as C from "./checklist.mjs";\n'
        f"const out = (() => {{ {snippet} }})();\nconsole.log(JSON.stringify(out));\n")
    p = subprocess.run([NODE, str(tmp_path / "run.mjs")], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


@needs_node
def test_eval_check(tmp_path):
    out = run("""
      const soc = {op: ">", value: "50 %", num: 50};
      const mode = {op: "in", set: ["4", "8"]};
      const pitch = {op: "in", lo: 0.043, hi: 0.083};
      const eq = {op: "==", value: "0", num: 0};
      const word = {op: "==", value: "NOMINAL"};
      const ref = {op: ">", value: "eps.power_cons", ref_param: "eps.power_cons"};
      return [C.evalCheck(soc, 90.1), C.evalCheck(soc, "17.0"), C.evalCheck(mode, 8), C.evalCheck(mode, 5),
              C.evalCheck(pitch, 0.063), C.evalCheck(pitch, 0), C.evalCheck(eq, 0.004), C.evalCheck(eq, 1),
              C.evalCheck(word, "nominal"), C.evalCheck(ref, 3), C.evalCheck(soc, null), C.evalCheck({}, 3)];
    """, tmp_path)
    assert out == [True, False, True, False, True, False, True, False, True, None, None, None]


@needs_node
def test_parse_inline_check(tmp_path):
    out = run("""
      return [C.parseInlineCheck("OBC application SW running (obdh.sw_image 0x0311 = 1)"),
              C.parseInlineCheck("EPS confirms SoC ~90 % (eps.bat_soc 0x0101); only obc"),
              C.parseInlineCheck("Position assignments confirmed and posted")];
    """, tmp_path)
    assert out[0] == {"param": "obdh.sw_image", "pid": "0x0311", "op": "==", "value": "1", "num": 1}
    assert out[1] == {"param": "eps.bat_soc", "pid": "0x0101"}
    assert out[2] is None


@needs_node
def test_runner_results(tmp_path):
    # runner StepResult: 0 PENDING 1 RUNNING 2 PASSED 3 FAILED 4 SKIPPED 5 TIMEOUT
    out = run("""
      const map = ["s1", "s1", "s2", "s3", "s3", null, "s4"];
      const r = (xs) => xs.map((x, i) => ({index: i, result: x}));
      return [
        C.runnerResults(map, r([2, 2, 2, 2, 1, 0, 0]), ["s2"]),   // s3 still running
        C.runnerResults(map, r([2, 2, 2, 2, 5, 0, 0]), ["s2"]),   // timeout fails s3 at once
        C.runnerResults(map, r([2, 4, 3, 0, 0, 0, 0]), ["s2"]),   // skip in s1, gate s2 failed
        C.runnerResults(map, r([2, 2, 2, 2, 2, 2, 2]), []),
        C.runnerResults(null, [], [])];
    """, tmp_path)
    assert out[0] == {"s1": "pass", "s2": "go"}
    assert out[1] == {"s1": "pass", "s2": "go", "s3": "fail"}
    assert out[2] == {"s1": "skip", "s2": "nogo"}
    assert out[3] == {"s1": "pass", "s2": "pass", "s3": "pass", "s4": "pass"}
    assert out[4] == {}


@needs_node
def test_runs_ticks_and_progress(tmp_path):
    out = run("""
      const mk = (key, run, result, ts, extra = {}) => ({id: key + run + ts, kind: "worksheet", ts,
        worksheet: {id: "WB-5.4-N001", q: key, instance: run, checked: result === "pass"},
        check: {key, run, result, ...extra}});
      const es = [mk("s1", "1", "pass", "2026-11-02T10:00:00.000Z"),
                  mk("s2", "1", "nogo", "2026-11-02T10:01:00.000Z"),
                  mk("s1", "2", "pass", "2026-11-02T11:00:00.000Z"),
                  mk("s3", "2", "skip", "2026-11-02T11:02:00.000Z"),
                  {...mk("s3", "2", "pass", "2026-11-02T11:01:00.000Z"), id: "older"},
                  {kind: "decision", ts: "2026-11-02T11:03:00.000Z"}];
      const steps = [{key: "s1"}, {key: "s2"}, {key: "s3"}];
      const t2 = C.ticksFor(es, "WB-5.4-N001", "2");
      return [C.runIds(es, "WB-5.4-N001"), C.nextRunId(es, "WB-5.4-N001"), C.nextRunId(es, "OTHER"),
              Object.keys(t2).sort(), t2.s3.check.result,
              C.progress(steps, C.ticksFor(es, "WB-5.4-N001", "1")), C.progress(steps, t2),
              C.isDeviation("nogo"), C.isDeviation("go")];
    """, tmp_path)
    assert out[0] == ["1", "2"] and out[1] == "3" and out[2] == "1"
    assert out[3] == ["s1", "s3"] and out[4] == "skip"           # the newest tick wins
    assert out[5] == {"done": 2, "total": 3, "deviations": 1}
    assert out[6] == {"done": 2, "total": 3, "deviations": 1}
    assert out[7] is True and out[8] is False


def test_workbook_module_contract():
    js = (UI / "workbook.js").read_text(encoding="utf-8")
    assert "export function createWorkbook" in js
    assert 'from "/static/shared/checklist.js"' in js
    assert "localStorage" not in js and "sessionStorage" not in js   # the text lives on the server
    for api in ('"/checklist?procedure=', "/worksheets?all=1", '"/entries"'):
        assert api.strip('"') in js
    lb = (UI / "logbook.js").read_text(encoding="utf-8")
    for name in ("export function openChecklist", "export async function openForm",
                 "export function onRunner", "copy=1", "c2o.lb.team"):
        assert name in lb
    # no hard-coded colours in the panel CSS; workbook rules are present
    css = (UI / "logbook.css").read_text(encoding="utf-8")
    assert ".wb-st" in css and not re.search(r"#[0-9a-fA-F]{3,8}\b", css)


def test_every_workbook_string_is_translated():
    fr = json.loads((UI / "i18n" / "fr.json").read_text(encoding="utf-8"))
    js = (UI / "workbook.js").read_text(encoding="utf-8")
    keys = set(re.findall(r'\bt(?:Text)?\("((?:[^"\\]|\\.)+)"', js))
    assert len(keys) > 40
    missing = [k for k in keys if not (fr.get(k) or fr.get(k + "_one"))]
    assert not missing, missing


def test_tools_without_checklists_work_step_sheets_row_by_row():
    """Only the MCS serves /api/logbook/checklist. In the radio view and the
    orbit tools a confirm-each-step sheet (WB-5.5-L001, WB-5.5-L003…) used to
    call it (404 in the console) and show nothing; it now opens as the
    printed sheet with its step rows."""
    wb = (UI / "workbook.js").read_text(encoding="utf-8")
    assert 'host.tool === "mcs" && w && (w.questions || []).some((q) => q.step)' in wb
    assert 'const isList = host.tool === "mcs" &&' in wb
    assert '!q.step || host.tool !== "mcs"' in wb
    assert "Pick a sheet below. Everything you fill in is saved to your logbook." in wb
    lb = (UI / "logbook.js").read_text(encoding="utf-8")
    assert 'S.tool === "mcs"' in lb


def test_overlay_panel_stays_clear_of_header_and_scrollbar():
    lb = (UI / "logbook.js").read_text(encoding="utf-8")
    assert "function placeOverlay()" in lb and 'window.addEventListener("scroll", placeOverlay' in lb
    css = (UI / "logbook.css").read_text(encoding="utf-8")
    assert "width:440px; max-width:100%;" in css and "max-width:100vw" not in css


def test_checklist_follows_the_runner_to_its_new_run():
    """Browser finding (NOM-009, one step): the runner finished before
    Start's checklist fetch returned, the fetch then reset the view to the
    previous run and the console had stopped polling, so the ticks went to
    run 2 while run 1 was shown. The fetch now re-applies the runner's last
    status."""
    wb = (UI / "workbook.js").read_text(encoding="utf-8")
    i = wb.index('W.run = runs.length ? runs[runs.length - 1] : "1";')
    tail = wb[i:i + 900]
    assert 'W.runnerKey = ""; W.runnerSeen.clear();' in tail and "onRunner(last)" in tail
    assert "W.lastRunner = st;" in wb
    # notes wrap (a runner note or a long deviation is readable)
    assert '<textarea id="wb-nt-' in wb


def test_open_form_waits_for_the_sheet_load_in_flight():
    """alarm › Ticket on a logbook never opened before: opening the panel starts
    the sheet load, and openForm("anomaly") must wait for that load instead of
    finding an empty sheet list (2026-11-05, found filming V-OPS-03)."""
    src = (UI / "workbook.js").read_text(encoding="utf-8")
    body = src[src.index("async function loadSheets"):src.index("function currentProc")]
    assert "W.sheetsP" in body and "await W.sheetsP" in body
