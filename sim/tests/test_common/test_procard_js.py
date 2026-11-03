"""The procedure card as the working surface: the browser half (2026-11-03).

smo_common/ui/procard.js turns the rendered card into the working copy
(Done / Failed / Skip or GO / NO-GO / Skip per step, Capture values, a note,
Record decision; Prerequisites checkboxes). It writes through the Workbook's
own tick() (workbook.js), so the card and the logbook's Workbook tab are one
source of truth. Pinned here under node:

* the card keys the browser derives from the rendered headings are the keys
  the server's checklist uses (every card, EN and FR);
* the records a card control writes: a prerequisite tick (check.part "pre",
  step "P1"), a capture on an open step, a GO that keeps the captured
  values, a note, a re-tick that PATCHes the same entry; every change
  notifies the card (subscribe) before the server answers;
* the module contract and its French.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from smo_common.logbook.checklist import _H3, parse_card

SIM = Path(__file__).resolve().parents[2]
UI = SIM / "packages" / "smo-common" / "src" / "smo_common" / "ui"
CFG = SIM / "configs" / "eosat1"
MCS_JS = SIM / "packages" / "smo-mcs" / "src" / "smo_mcs" / "static" / "modern" / "mcs.js"
NODE = shutil.which("node") or shutil.which("nodejs")
needs_node = pytest.mark.skipif(not NODE, reason="node not installed")

_SHARED = re.compile(r"""(["'])/static/shared/([\w.-]+)\.js(\?[^"']*)?\1""")


def _stage(tmp_path: Path) -> None:
    """Every shared UI module as ./<name>.mjs with its imports rewritten."""
    for f in UI.glob("*.js"):
        src = _SHARED.sub(r'"./\2.mjs"', f.read_text(encoding="utf-8"))
        (tmp_path / (f.stem + ".mjs")).write_text(src, encoding="utf-8")


PRELUDE = """
globalThis.window = globalThis;
globalThis.document = { documentElement: { lang: "en", setAttribute() {}, getAttribute() { return null; } },
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
  createElement: () => ({ style: {}, setAttribute() {}, appendChild() {} }),
  head: { appendChild() {} }, body: { appendChild() {} } };
globalThis.localStorage = { getItem: () => null, setItem() {} };
"""


def run(snippet: str, tmp_path: Path):
    _stage(tmp_path)
    (tmp_path / "run.mjs").write_text(
        PRELUDE + "const out = await (async () => { " + snippet + " })();\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    p = subprocess.run([NODE, str(tmp_path / "run.mjs")], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout.strip().splitlines()[-1])


def _cards():
    for base in (CFG / "procedures", CFG / "i18n" / "fr" / "procedures"):
        for f in sorted(base.rglob("*.md")):
            yield f


@needs_node
def test_browser_card_keys_match_the_server_checklist(tmp_path):
    """procard.js keys each rendered ### heading with checklist.js
    cardStepKeys(); the server keys the same headings with parse_card. A
    mismatch would put a step's controls on the wrong step."""
    cases = []
    for f in _cards():
        md = f.read_text(encoding="utf-8")
        lines = md.splitlines()
        heads = [(i + 1, _H3.match(ln.rstrip()).group(1)) for i, ln in enumerate(lines)
                 if _H3.match(ln.rstrip())]
        steps = {s["line"]: s["key"] for s in parse_card(md)["steps"]}
        if heads:
            cases.append({"file": str(f.relative_to(CFG)), "heads": [h for _, h in heads],
                          "want": [steps.get(ln) for ln, _ in heads]})
    assert len(cases) > 100
    out = run("const C = await import('./checklist.mjs');\n"
              f"const cases = {json.dumps(cases)};\n"
              "return cases.map((c) => ({ file: c.file, got: C.cardStepKeys(c.heads), want: c.want }));",
              tmp_path)
    bad = [c["file"] for c in out
           if any(w is not None and w != g for g, w in zip(c["got"], c["want"]))]
    assert not bad, bad


@needs_node
def test_prerequisite_helpers(tmp_path):
    out = run("""
      const C = await import('./checklist.mjs');
      return [C.isPrereqHeading("Prerequisites"), C.isPrereqHeading("Prérequis"),
              C.isPrereqHeading("Procedure Steps"), C.prereqItem("[ ] OBC in NOMINAL mode"),
              C.prereqItem("[x] done already"), C.prereqItem("no box here")];
    """, tmp_path)
    assert out == [True, True, False, "OBC in NOMINAL mode", "done already", None]


CHECKLIST = {
    "procedure": "COM-006", "name": "TTC Link Verification", "title": "COM-006", "lang": "en",
    "sheet_id": "WB-5.6-C006", "sheet_title": "COM-006 (confirm each step)", "runnable": True,
    "steps": [
        {"key": "s0", "n": "0", "title": "Configure the S-Band Chain", "tcs": ["TTC_PA_ON"],
         "checks": [{"text": "PA on", "param": "ttc.pa_on", "pid": "0x0516", "op": "==", "value": "1", "num": 1}],
         "gonogo": "S-band chain configured", "actions": [], "ref": []},
        {"key": "s1", "n": "1", "title": "Baseline", "tcs": [], "checks": [], "gonogo": "", "actions": ["Record"],
         "ref": []},
    ],
    "prereqs": [
        {"key": "p1", "n": "P1", "text": "COM-001 through COM-003 completed"},
        {"key": "p2", "n": "P2", "text": "S-band link active", "checks": [
            {"text": "link", "param": "ttc.link_status", "pid": "0x0501", "op": "==", "value": "2", "num": 2}]},
    ],
    "extra": [], "mismatches": [], "runner_map": ["s0", "s1"],
}


@needs_node
def test_card_controls_write_the_workbook_records(tmp_path):
    out = run(f"""
      const {{ createWorkbook }} = await import('./workbook.mjs');
      const calls = [], entries = [];
      let notes = 0, n = 0;
      const live = {{ "ttc.pa_on": {{ raw: 1, text: "on (1)", units: "", nodata: false, stale: false }},
                     "ttc.link_status": {{ raw: 2, text: "2", units: "", nodata: false, stale: false }} }};
      const host = {{
        tool: "mcs", API: "/api/logbook",
        async api(method, path, body) {{
          calls.push({{ method, path, body }});
          if (path.startsWith("/checklist")) return {json.dumps(CHECKLIST)};
          if (method === "POST") {{ n += 1; return {{ id: "e" + n, ...body, ts: "2026-11-03T12:00:0" + n + ".000Z" }}; }}
          return {{ id: path.split("/").pop(), ...body }};
        }},
        entries: () => entries, refresh: async () => null, refreshSoon() {{}}, announce() {{}},
        fmtTime: () => "", cleanContext: (c) => ({{ page: c.page, position: c.position }}),
        exportQuery: () => "", copyMarkdown() {{}}, afterDownload() {{}}, onCount() {{}},
        context: () => ({{ page: "proc", position: "ttc", procedure: "COM-006", sim_ts: "2026-08-20T12:00:00Z" }}),
        readParam: (name) => live[name] || {{ nodata: true }},
      }};
      const wb = createWorkbook(host);
      wb.subscribe(() => {{ notes += 1; }});
      const cl = await wb.useCard("COM-006");
      const st0 = wb.cardState();
      // a prerequisite ticked on the card
      await wb.tick("p2", "done");
      const pre = calls.filter((c) => c.method === "POST")[0].body;
      // capture on an open step, then GO: the captured values are kept
      const before = notes;
      const pCap = wb.tick("s0", "capture", {{ note: "first try" }});
      const optimistic = wb.cardState().ticks.s0.check;
      const notified = notes > before;
      await pCap;
      live["ttc.pa_on"] = {{ raw: 0, text: "off (0)", units: "", nodata: false, stale: false }};
      await wb.tick("s0", "go", {{ note: "GO given by FD" }});
      const posts = calls.filter((c) => c.method === "POST").map((c) => c.body);
      const patches = calls.filter((c) => c.method === "PATCH");
      // a plain step with no checks
      await wb.tick("s1", "fail", {{ note: "margin low" }});
      return {{
        loaded: !!cl, prereqs: st0.prereqs, progress: st0.progress, pre,
        optimistic: {{ result: optimistic.result, values: optimistic.values }}, notified,
        capture: posts[1], patch: patches[0],
        fail: calls.filter((c) => c.method === "POST").map((c) => c.body)[2],
        checklistCall: calls[0].path,
      }};
    """, tmp_path)
    assert out["loaded"] and out["prereqs"] == {"done": 0, "total": 2}
    assert out["progress"] == {"done": 0, "total": 2, "deviations": 0}
    assert out["checklistCall"].startswith("/checklist?procedure=COM-006")
    pre = out["pre"]
    assert pre["kind"] == "worksheet" and pre["worksheet"]["id"] == "WB-5.6-C006"
    assert pre["worksheet"]["q"] == "p2" and pre["worksheet"]["instance"] == "1"
    assert pre["worksheet"]["checked"] is True
    c = pre["check"]
    assert (c["part"], c["step"], c["key"], c["order"], c["result"], c["run"]) == ("pre", "P2", "p2", 1, "done", "1")
    assert c["values"][0]["param"] == "ttc.link_status" and c["values"][0]["ok"] is True
    assert pre["context"]["procedure"] == "COM-006" and pre["context"]["step"] == "P2"
    assert pre["sim_ts"] == "2026-08-20T12:00:00Z" and pre["text"].startswith("Prerequisite P2 · S-band link active")
    # optimistic: the card sees the capture before the server answers
    assert out["notified"] and out["optimistic"]["result"] == "open"
    assert out["optimistic"]["values"][0]["value"] == "on (1)"
    cap = out["capture"]["check"]
    assert cap["result"] == "open" and cap["note"] == "first try" and "part" not in cap
    assert cap["values"] == [{"param": "ttc.pa_on", "expect": "ttc.pa_on = 1", "pid": "0x0516",
                              "value": "on (1)", "ok": True}]
    assert out["capture"]["worksheet"]["checked"] is False
    # GO on the same step PATCHes the same entry and keeps the captured value
    patch = out["patch"]
    assert patch["path"] == "/entries/e2"
    assert patch["body"]["check"]["result"] == "go" and patch["body"]["checked"] is True
    assert patch["body"]["check"]["values"][0]["value"] == "on (1)"     # not the later "off (0)"
    assert patch["body"]["check"]["note"] == "GO given by FD"
    assert patch["body"]["check"]["gonogo"] == "S-band chain configured"
    fail = out["fail"]["check"]
    assert fail["result"] == "fail" and fail["values"] == [] and fail["note"] == "margin low"
    assert out["fail"]["worksheet"]["checked"] is False


def test_procard_module_contract():
    js = (UI / "procard.js").read_text(encoding="utf-8")
    assert "export function mountProcCard" in js and "export function markCard" in js
    # one source of truth: everything goes through the Workbook's records
    for api in ("wb.tick(", '"capture"', "wb.subscribe(", "wb.useCard(", "wb.cardState()",
                "lb.logThis(", "lb.openChecklist(", 'kind: "decision"'):
        assert api in js, api
    assert "fetch(" not in js and "localStorage" not in js and "sessionStorage" not in js
    assert 'from "/static/shared/checklist.js"' in js
    # keyboard: native buttons, Enter saves the note, Shift+Enter is a new line
    assert '<button type="button"' in js and 'ev.key === "Enter" && !ev.shiftKey' in js
    lb = (UI / "logbook.js").read_text(encoding="utf-8")
    assert "workbook: S.wb" in lb and "S.wb.onData();" in lb
    css = (UI / "logbook.css").read_text(encoding="utf-8")
    assert ".pc-ctl" in css and ".pc-bar" in css and not re.search(r"#[0-9a-fA-F]{3,8}\b", css)


def test_every_procard_string_is_translated():
    fr = json.loads((UI / "i18n" / "fr.json").read_text(encoding="utf-8"))
    keys = set()
    for name in ("procard.js", "workbook.js"):
        keys |= set(re.findall(r'\bt(?:Text)?\("((?:[^"\\]|\\.)+)"', (UI / name).read_text(encoding="utf-8")))
    missing = [k for k in keys if not (fr.get(k) or fr.get(k + "_one"))]
    assert not missing, missing


def test_mcs_procedure_page_mounts_the_card():
    js = MCS_JS.read_text(encoding="utf-8")
    assert 'import { mountProcCard } from "/static/shared/procard.js";' in js
    i = js.index("async function mountProcDocCard(path)")
    body = js[i:i + 900]
    assert 'levels: { step: "H4", section: "H3" }' in body and "lb: LB" in body
    assert "procCard.destroy()" in js
    # the card spans the page (not the narrow left column)
    assert 'id="proc-doc"' in js and 'data-i18n="Procedure card"' in js


@needs_node
def test_mcs_renders_card_items_and_tag_lines_whole(tmp_path):
    """The card view needs each Prerequisites item whole (its wrapped lines
    folded in) and each **TC:** / **Verify:** line on a line of its own."""
    harness = SIM / "tests" / "test_mcs" / "js" / "modern_harness.js"
    md = ("## Prerequisites\n- [ ] OBC in the APPLICATION image (`obdh.sw_image` 0x0311 = 1). Booting\n"
          "      the application lifts the PA inhibit\n- [ ] Second item\n\n"
          "### Step 0 — Configure\n**TC:** `TTC_PA_ON`\n**Verify:** `ttc.pa_on == 1`\n\nNext paragraph.\n")
    f = tmp_path / "snippet.js"
    f.write_text(f"return T.renderMarkdown({json.dumps(md)});", encoding="utf-8")
    p = subprocess.run([NODE, str(harness), str(SIM), str(f)], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    html = json.loads(p.stdout)
    assert "<li>[ ] OBC in the APPLICATION image (<code>obdh.sw_image</code> 0x0311 = 1). Booting " \
           "the application lifts the PA inhibit</li>" in html
    assert "<li>[ ] Second item</li>" in html
    assert "<code>TTC_PA_ON</code><br>\n<b>Verify:</b>" in html
    assert "<br><br>Next paragraph." in html
