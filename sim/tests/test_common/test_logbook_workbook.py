"""Ops workbook in the logbook (2026-11-02): live procedure checklists built
from the cards, structured forms, workbook-ordered export, hand-in header.

Franz: "I want the teams to really use them as work books… make the
checklists part of the log books". The checklist follows the CARD (what is
executed); the printed workbook sheet is kept as the reference and every
disagreement is listed.
"""
import importlib.util
import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.logbook import LogbookStore, WorksheetCatalog, register_logbook_routes
from smo_common.logbook.checklist import (ChecklistProvider, build_checklist, compare_sheet,
                                          parse_card, parse_check, runner_map,
                                          sheet_for_procedure)
from smo_common.logbook.export import build_document, export_filename, to_html, to_markdown
from smo_common.procedures import from_markdown

SIM = Path(__file__).resolve().parents[2]
CFG = SIM / "configs" / "eosat1"
NOW = datetime(2026, 11, 2, 23, 41, tzinfo=timezone.utc)
P = "op@example.org"


def _index():
    return yaml.safe_load((CFG / "procedures" / "procedure_index.yaml").read_text())["procedures"]


def _catalog():
    from smo_common.config.loader import load_tc_catalog
    cat = {}
    for c in load_tc_catalog(CFG):
        e = {"service": c.service, "subtype": c.subtype, "func_id": c.func_id}
        cat[c.name] = e
        for a in c.aliases or []:
            cat.setdefault(a, e)
    return cat


@pytest.fixture(scope="module")
def provider():
    cat = WorksheetCatalog(CFG / "worksheets")
    tc = _catalog()
    return ChecklistProvider(_index(), CFG / "procedures", CFG / "i18n" / "fr" / "procedures",
                             cat.sheets, lambda: tc)


# ── card parsing ────────────────────────────────────────────────────────

CARD = """# XYZ-001: Test Card
**Subsystem:** EPS

## Purpose
Nothing to do here.
**TC:** `NOT_A_STEP` (Service 8, Subtype 1)

## Procedure Steps

### Step 1 --- Read the Battery
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- EPS
**Verify:** `eps.bat_soc` (0x0101) > 50 % within 10 s
**Verify:** `aocs.mode` (0x020F) in {4, 8} (NOMINAL; 8 = ECLIPSE)
**Verify:** `aocs.rate_pitch` (0x0205) in range [0.043, 0.083] deg/s
**Verify:** `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106)
**Verify:** |`aocs.rate_roll`| (0x0204) < 0.05 deg/s
**GO/NO-GO:** If SoC < 50 %, stop.

### Step 2a — Poll
**Action:** Ask every position
for its call.
**GO/NO-GO Gate --- Flight Director Poll:**
- EPS: SoC > 50 % --- GO / NO-GO
- AOCS: NOMINAL --- GO / NO-GO
**Decision:** all GO to proceed.

### Reference Table
| a | b |

## Off-Nominal Handling
- nothing
"""


def test_parse_card_steps_checks_and_gates():
    c = parse_card(CARD)
    assert c["title"] == "XYZ-001: Test Card"
    assert [s["key"] for s in c["steps"]] == ["s1", "s2a"]     # the reference table is not a step
    s1, s2 = c["steps"]
    assert s1["n"] == "1" and s1["title"] == "Read the Battery"
    assert [t["cmd"] for t in s1["tcs"]] == ["HK_REQUEST(sid=1)"]
    soc, mode, pitch, gen, roll = s1["checks"]
    assert (soc["param"], soc["pid"], soc["op"], soc["value"], soc["num"]) == \
        ("eps.bat_soc", "0x0101", ">", "50 %", 50.0)
    assert mode["op"] == "in" and mode["set"] == ["4", "8"]
    assert (pitch["op"], pitch["lo"], pitch["hi"]) == ("in", 0.043, 0.083)
    assert gen["ref_param"] == "eps.power_cons" and gen["op"] == ">"
    assert (roll["param"], roll["op"], roll["num"]) == ("aocs.rate_roll", "<", 0.05)
    assert s1["gonogo"].startswith("If SoC")
    assert s2["n"] == "2a" and s2["actions"] == ["Ask every position for its call."]
    assert "• EPS: SoC > 50 % --- GO / NO-GO" in s2["gonogo"]
    assert "Decision: all GO" in s2["gonogo"]


@pytest.mark.parametrize("text,want", [
    ("`obdh.mode` (0x0300) = 0 (NOMINAL) within 10 s", {"param": "obdh.mode", "op": "==", "value": "0"}),
    ("`ttc.link_status == 2` (timeout 15 s)", {"param": "ttc.link_status", "op": "==", "value": "2"}),
    ("TT&C page (ground): `ttc.rssi` (0x0502) > -126 dBm", {"param": "ttc.rssi", "op": ">", "num": -126.0}),
    ("`eps.power_gen` (0x0107) reported", {"param": "eps.power_gen", "pid": "0x0107"}),
    ("All 6 HK packets received within 30 s", {}),
])
def test_parse_check(text, want):
    got = parse_check(text)
    for k, v in want.items():
        assert got.get(k) == v, (text, got)
    if not want:
        assert "param" not in got and "op" not in got


def test_runner_map_matches_the_runner_for_every_runnable_card():
    """Per-section extraction equals the runner's whole-card extraction, so
    runner step i maps to the right checklist step."""
    cat = _catalog()
    n = 0
    for e in _index():
        if (e.get("runnable") or {}).get("kind") != "markdown":
            continue
        md = (CFG / "procedures" / e["file"]).read_text(encoding="utf-8")
        full = from_markdown(md, cat)
        rm = runner_map(md, cat)
        assert len(rm) == len(full), e["id"]
        keys = {s["key"] for s in parse_card(md)["steps"]}
        assert {k for k in rm if k} <= keys, e["id"]
        assert rm and rm[0], e["id"]
        n += 1
    assert n >= 3


def test_every_indexed_card_builds_or_is_cleanly_absent(provider):
    for e in _index():
        for lang in ("en", "fr"):
            cl = provider(e["id"], lang)
            if cl is None:
                continue
            assert cl["procedure"] == e["id"] and cl["steps"], e["id"]
            assert all(s["key"] and s["title"] for s in cl["steps"]), e["id"]
            assert "`" not in json.dumps(cl["steps"]), e["id"]     # plain text, no markup


def test_nom001_checklist_follows_the_card_with_the_printed_sheet_beside(provider):
    cl = provider("NOM-001", "en")
    assert cl["sheet_id"] == "WB-5.4-N001" and not cl["runnable"]
    assert [s["n"] for s in cl["steps"]] == ["1", "2", "3", "4", "5", "6", "7"]   # the CARD's steps
    s4 = cl["steps"][3]
    assert s4["title"] == "Establish TTC Link" and s4["tcs"] == ["TTC_SWITCH_PRIMARY"]
    assert any(c.get("param") == "ttc.link_status" and c["op"] == "==" for c in s4["checks"])
    assert any(r["n"] == "3" for r in s4["ref"])        # printed row 3 is about link lock
    assert cl["steps"][6]["gonogo"]                     # the FD poll is a GO/NO-GO gate
    assert [q["text"] for q in cl["extra"]] == ["Off-nominal items observed"]
    kinds = {m["kind"] for m in cl["mismatches"]}
    assert {"count", "row_unmatched", "step_unprinted"} <= kinds
    count = next(m for m in cl["mismatches"] if m["kind"] == "count")
    assert (count["n_sheet"], count["n_card"]) == (10, 7)


def test_french_checklist_uses_the_french_card_and_keeps_english_parsing(provider):
    fr = provider("NOM-001", "fr")
    en = provider("NOM-001", "en")
    assert fr["steps"][0]["title"] == "Vérifier l'état de l'OBC"
    assert "sous 10\u00a0s" in fr["steps"][0]["checks"][0]["text"]
    assert fr["steps"][0]["checks"][0]["param"] == en["steps"][0]["checks"][0]["param"]
    assert fr["steps"][6]["gonogo"]                      # « Jalon GO/NO-GO » is the gate too
    assert fr["sheet_title"].startswith("NOM-001 Ouverture de passage")


def test_runnable_card_carries_its_runner_map(provider):
    cl = provider("NOM-008", "en")
    assert cl["runnable"] and len(cl["runner_map"]) > len(cl["steps"])
    assert cl["sheet_id"] == "PROC-NOM-008"              # no printed sheet for this card


def test_compare_sheet_reports_each_kind_of_disagreement():
    card = parse_card("""# X
### Step 1 --- Ping
**TC:** `CONNECTION_TEST` (Service 17, Subtype 1)
### Step 2 --- Battery
**Verify:** `eps.bat_soc` (0x0101) > 50 %
### Step 3 --- Never printed
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1)
""")
    sheet = {"id": "WB-T", "questions": [
        {"id": "q1", "step": "1", "text": {"en": "1. Check battery eps.bat_soc"}},
        {"id": "q2", "step": "2", "text": {"en": "2. Send CONNECTION_TEST and SET_TIME"}},
        {"id": "q3", "step": "3", "text": {"en": "3. Log the pass in the shift log"}},
        {"id": "q4", "text": {"en": "Notes"}}]}
    out = compare_sheet(card, sheet)
    kinds = [m["kind"] for m in out["mismatches"]]
    assert "order" in kinds                       # row 2 is card step 1, after row 1 = step 2
    assert any(m["kind"] == "command" and m["names"] == ["SET_TIME"] for m in out["mismatches"])
    assert any(m["kind"] == "row_unmatched" and m["row"] == "3" for m in out["mismatches"])
    assert any(m["kind"] == "step_unprinted" and m["step"] == "3" for m in out["mismatches"])
    assert [r["n"] for r in out["rows"]["s2"]] == ["1"] and [r["n"] for r in out["rows"]["s1"]] == ["2"]


def test_sheet_for_procedure_prefers_the_step_sheet():
    sheets = WorksheetCatalog(CFG / "worksheets").sheets()
    assert sheet_for_procedure(sheets, "COM-012")["id"] == "WB-5.6-C012"   # not WB-5.6-FL
    assert sheet_for_procedure(sheets, "NOM-002") is None


def test_checklist_for_a_card_without_a_sheet():
    cl = build_checklist("ZZZ-1", CARD, name="Test")
    assert cl["sheet_id"] == "PROC-ZZZ-1" and cl["mismatches"] == [] and cl["extra"] == []


# ── generated worksheets: what the workbook UI relies on ────────────────

def test_generated_sheets_mark_steps_forms_and_prefill():
    c = WorksheetCatalog(CFG / "worksheets")
    n001 = c.get("WB-5.4-N001")
    assert [q.get("step") for q in n001["questions"][:10]] == [str(i) for i in range(1, 11)]
    assert "step" not in n001["questions"][10]
    at = c.get("WB-5.5-AT")
    assert at["form"] == "anomaly" and at["instances"] is True
    assert {q.get("prefill") for q in at["questions"]} >= {"ticket_id", "param_value", "procedure"}
    assert not any("copy" in str(q.get("section", "")).lower() for q in at["questions"])
    go = c.get("WB-5.5-GO")
    assert any(q["text"]["en"] == "Notes for debrief" and q.get("prefill") == "gonogo"
               for q in go["questions"])          # a "**Label:** ____" field is no longer dropped
    assert c.get("WB-5.6-HO")["form"] == "handover" and c.get("WB-5.6-DB")["form"] == "debrief"
    loc = WorksheetCatalog.localise(at, "fr")
    assert loc["form"] == "anomaly" and loc["questions"][0]["prefill"] == "ticket_id"


def test_all_sheets_in_workbook_order_with_match():
    c = WorksheetCatalog(CFG / "worksheets")
    allm = c.all_for("mcs", {"procedure": "NOM-001"})
    ids = [w["id"] for w in allm]
    assert ids.index("WB-5.4-N001") < ids.index("WB-5.5-AT") < ids.index("WB-A-CTG-001")
    assert next(w for w in allm if w["id"] == "WB-5.4-N001")["match"] == "procedure"
    assert next(w for w in allm if w["id"] == "WB-5.5-L001").get("match") is None
    assert c.order("WB-5.0") == 0 and c.order("nope") is None


# ── store: the optional check / form payloads ──────────────────────────

@pytest.fixture
def store(tmp_path):
    return LogbookStore(tmp_path / "lb", retention_h=48, max_age_h=168)


def _tick(store, key="s3", result="pass", run="1", **kw):
    body = {"kind": "worksheet", "tool": "mcs", "text": f"Step {key[1:]} — {result}",
            "context": {"procedure": "NOM-001", "position": "ttc"}, "sim_ts": "2026-03-10T04:18:22Z",
            "worksheet": {"id": "WB-5.4-N001", "q": key, "title": "NOM-001", "q_text": "Step 3 — Link",
                          "checked": result == "pass", "instance": run},
            "check": {"procedure": "NOM-001", "step": key[1:], "key": key, "order": int(key[1:]) - 1,
                      "title": "Establish TTC Link", "run": run, "result": result, "source": "operator",
                      "position": "ttc", "sim_ts": "2026-03-10T04:18:22Z", "note": "",
                      "values": [{"param": "ttc.link_status", "pid": "0x0501", "expect": "ttc.link_status = 2",
                                  "value": "2", "ok": True, "bogus": 1}],
                      "evil": "<script>"}}
    body["check"].update(kw)
    return store.add(P, body)


def test_check_payload_is_cleaned_folded_and_edited(store):
    e = _tick(store)
    assert e["check"]["result"] == "pass" and e["check"]["values"][0] == {
        "param": "ttc.link_status", "pid": "0x0501", "expect": "ttc.link_status = 2", "value": "2", "ok": True}
    assert "evil" not in e["check"] and e["worksheet"]["instance"] == "1"
    store.edit(P, e["id"], {"text": "Step 3 — NO-GO", "checked": False,
                            "check": {"result": "nogo", "note": "margin 1.2 dB"}})
    f = store.entries(P)[0]
    assert f["check"]["result"] == "nogo" and f["check"]["note"] == "margin 1.2 dB"
    assert f["check"]["values"][0]["value"] == "2"            # merged, not replaced
    assert f["worksheet"]["checked"] is False and f["edited"]


def test_bad_check_values_are_dropped(store):
    e = _tick(store, result="maybe", source="robot", order=True)
    assert "result" not in e["check"] and "source" not in e["check"] and "order" not in e["check"]
    plain = store.add(P, {"kind": "decision", "tool": "mcs", "text": "x", "check": {"result": "pass"}})
    assert "check" not in plain                   # only worksheet entries carry payloads


def test_form_payload_round_trip_and_compaction(store, monkeypatch):
    import smo_common.logbook.store as st
    body = {"kind": "worksheet", "tool": "mcs", "text": "WB-5.5-AT — AT-1\nOutcome: recovered",
            "worksheet": {"id": "WB-5.5-AT", "q": "form", "instance": "AT-1"},
            "form": {"instance": "AT-1", "fields": [
                {"q": "q4", "value": "eps.bat_soc = 17 %", "prefilled": True},
                {"q": "q11", "value": "recovered"}, {"value": "no q"}, {"q": "q99"}],
                "info": [{"label": "From alarm", "value": "eps.bat_soc"}, {"nolabel": 1}]}}
    e = store.add(P, body)
    assert [f["q"] for f in e["form"]["fields"]] == ["q4", "q11"]
    assert e["form"]["info"] == [{"label": "From alarm", "value": "eps.bat_soc"}]
    store.edit(P, e["id"], {"text": "edited", "form": {"instance": "AT-1", "fields": [{"q": "q11", "value": "safe"}]}})
    assert store.entries(P)[0]["form"]["fields"] == [{"q": "q11", "value": "safe"}]   # saved whole
    monkeypatch.setattr(st, "COMPACT_SLACK", 1)
    _tick(store)
    _tick(store, key="s4")
    store.edit(P, e["id"], {"text": "again"})
    es = {x["worksheet"]["id"] + x["worksheet"]["q"]: x for x in store.entries(P)}
    assert es["WB-5.5-ATform"]["form"]["fields"] == [{"q": "q11", "value": "safe"}]
    assert es["WB-5.4-N001s4"]["check"]["key"] == "s4"


# ── export ──────────────────────────────────────────────────────────────

def _workbook(store):
    _tick(store, key="s4", result="pass")
    _tick(store, key="s3", result="nogo", note="margin 1.2 dB")
    _tick(store, key="s5", result="skip")
    store.add(P, {"kind": "worksheet", "tool": "mcs", "text": "AT", "context": {"position": "eps"},
                  "worksheet": {"id": "WB-5.5-AT", "q": "form", "instance": "AT-0820-7"},
                  "form": {"instance": "AT-0820-7", "info": [{"label": "From alarm", "value": "eps.bat_soc"}],
                           "fields": [{"q": "q4", "value": "eps.bat_soc = 17 % | limit 25", "prefilled": True},
                                      {"q": "q11", "value": "recovered"}]}})
    store.add(P, {"kind": "decision", "tool": "mcs", "text": "Shed the payload first.",
                  "context": {"procedure": "CTG-001"}})
    store.add(P, {"kind": "worksheet", "tool": "mcs", "text": "Too slow on the callout.",
                  "worksheet": {"id": "WB-5.5-DB", "q": "q3"}})
    return store.summary(P)


def test_markdown_reads_like_a_completed_workbook(store):
    cat = WorksheetCatalog(CFG / "worksheets")
    md = to_markdown(_workbook(store), P, lookup=cat.question, order=cat.order, now=NOW,
                     header={"team": "Borealis", "scenario": "first_contact", "session": "Day 3 pass 1"})
    for line in ("- Team: Borealis", "- Position: ", "- Scenario: first_contact",
                 "- Session: Day 3 pass 1"):
        assert line in md
    wb, log = md.index("## Workbook"), md.index("## Log")
    n001, at, db = (md.index("### WB-5.4-N001"), md.index("### WB-5.5-AT"), md.index("### WB-5.5-DB"))
    assert wb < n001 < at < db < log                      # printed workbook order, then the log
    assert "| # | Step | Check (expected) | Observed | Time (UTC · sim) | By | Result | Note |" in md
    rows = [ln for ln in md.splitlines() if ln.startswith("| 3 |") or ln.startswith("| 4 |")]
    assert rows[0].startswith("| 3 |") and "**NO-GO**" in rows[0] and "margin 1.2 dB" in rows[0]
    assert "04:18:22" in rows[0] and "ttc, operator" in rows[0] and "ttc.link_status = 2" in rows[0]
    assert "_Deviations: 3 NO-GO: margin 1.2 dB; 5 SKIPPED_" in md
    assert "**AT-0820-7**" in md and "| Triggering parameter and value | eps.bat_soc = 17 % \\| limit 25 ¹ |" in md
    assert "¹ _prefilled from the console_" in md
    assert "Which voice callout did you most struggle" in md
    assert "Mission control · Decision" in md[log:] and "Shed the payload first." in md[log:]


def test_markdown_in_french(store):
    cat = WorksheetCatalog(CFG / "worksheets")
    md = to_markdown(_workbook(store), "this browser", lang="fr", lookup=cat.question,
                     order=cat.order, now=NOW, header={"team": "Austral"})
    assert "- Équipe : Austral" in md and "## Cahier d’exercices" in md and "## Journal" in md
    assert "| nº | Étape |" in md and "**NO-GO**" in md and "SAUTÉE" in md
    assert "Paramètre déclencheur et valeur" in md


def test_html_export_tables_and_escaping(store):
    s = _workbook(store)
    store.add(P, {"kind": "worksheet", "tool": "mcs", "text": "<b>x</b>",
                  "worksheet": {"id": "WB-5.5-AT", "q": "form"},
                  "form": {"fields": [{"q": "q12", "value": "<script>alert(1)</script>"}]}})
    h = to_html(store.summary(P), P, now=NOW, header={"team": "<Borealis>"})
    assert "<table class='cl'>" in h and "<th>Observed</th>" in h and "class=dev" in h
    assert "<script>" not in h and "&lt;script&gt;" in h and "&lt;Borealis&gt;" in h
    assert h.index("WB-5.4-N001") < h.index("WB-5.5-AT")
    assert len(s["entries"]) == 6


def test_one_sheet_only(store):
    s = _workbook(store)
    doc = build_document(s, P, sheet="WB-5.5-AT", now=NOW)
    assert [x["id"] for x in doc["sheets"]] == ["WB-5.5-AT"] and doc["log"] == []
    md = to_markdown(s, P, sheet="WB-5.5-AT", now=NOW)
    assert "_Worksheet WB-5.5-AT only_" in md and "WB-5.4-N001" not in md
    assert export_filename("md", NOW, "WB-5.5-AT") == "c2o-logbook-WB-5.5-AT-20261102-2341.md"


def test_old_records_still_export(store):
    store.add(P, {"kind": "worksheet", "tool": "mcs", "text": "Done", "worksheet":
                  {"id": "WB-5.4-N001", "q": "q3", "checked": True}})
    md = to_markdown(store.summary(P), P, lookup=WorksheetCatalog(CFG / "worksheets").question, now=NOW)
    assert "3. TT&C: At AOS, verify link lock acquired" in md and "[x] Done" in md


# ── the SpaceCDF twin reads the same file safely ───────────────────────

TWIN = SIM.parent / "design" / "packages" / "spacecdf-server" / "src" / "spacecdf_server" / "logbook"


def _load_twin():
    pkg = types.ModuleType("_twin_lb")
    pkg.__path__ = [str(TWIN)]
    sys.modules["_twin_lb"] = pkg
    mods = {}
    for name in ("store", "export"):
        spec = importlib.util.spec_from_file_location(f"_twin_lb.{name}", TWIN / f"{name}.py")
        m = importlib.util.module_from_spec(spec)
        sys.modules[f"_twin_lb.{name}"] = m
        spec.loader.exec_module(m)
        mods[name] = m
    return mods


@pytest.mark.skipif(not TWIN.is_dir(), reason="design/ (SpaceCDF) not in this checkout")
def test_spacecdf_twin_folds_and_renders_the_new_records(store):
    _workbook(store)
    path = store.path_for(P)
    recs = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
    assert any("check" in r for r in recs) and any("form" in r for r in recs)
    twin = _load_twin()
    folded = twin["store"].fold(recs)
    entries = list(folded.entries.values())
    assert len(entries) == 6
    for fn in (twin["export"].render_markdown, twin["export"].render_html, twin["export"].render_json):
        out = fn(entries=entries, person_label=P, exported_at=NOW, expires_at=None,
                 retention_h=48.0, lang="en")
        # each record's readable summary is shown, grouped under its worksheet
        assert "Step 3 — nogo" in out and "WB-5.4-N001" in out and "Shed the payload first." in out
    sys.modules.pop("_twin_lb.store", None)
    sys.modules.pop("_twin_lb.export", None)
    sys.modules.pop("_twin_lb", None)


# ── HTTP: checklist, export header, one sheet, copy, all sheets ────────

async def _client(tmp_path, checklists=None):
    app = web.Application()
    register_logbook_routes(app, tool="mcs", store_dir=tmp_path / "lb",
                            worksheets_dir=CFG / "worksheets", checklists=checklists)
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


H = {"X-Goog-Authenticated-User-Email": "accounts.google.com:op@example.org"}


async def test_checklist_route(tmp_path):
    tc = _catalog()

    def factory(catalog):
        return ChecklistProvider(_index(), CFG / "procedures", CFG / "i18n" / "fr" / "procedures",
                                 catalog.sheets, lambda: tc)
    factory.wants_catalog = True
    c = await _client(tmp_path, factory)
    try:
        r = await c.get("/api/logbook/checklist?procedure=NOM-001&lang=fr", headers=H)
        assert r.status == 200
        j = await r.json()
        assert j["sheet_id"] == "WB-5.4-N001" and j["lang"] == "fr" and len(j["steps"]) == 7
        assert (await c.get("/api/logbook/checklist?procedure=NOPE-1", headers=H)).status == 404
        assert (await c.get("/api/logbook/checklist", headers=H)).status == 404
    finally:
        await c.close()


async def test_no_checklists_in_a_tool_without_procedures(tmp_path):
    c = await _client(tmp_path)
    try:
        assert (await c.get("/api/logbook/checklist?procedure=NOM-001", headers=H)).status == 404
    finally:
        await c.close()


async def test_export_header_sheet_and_copy(tmp_path):
    c = await _client(tmp_path)
    try:
        r = await c.post("/api/logbook/entries", headers=H, json={
            "kind": "worksheet", "text": "AT", "worksheet": {"id": "WB-5.5-AT", "q": "form", "instance": "AT-1"},
            "form": {"instance": "AT-1", "fields": [{"q": "q11", "value": "recovered"}]}})
        assert r.status == 201 and (await r.json())["form"]["instance"] == "AT-1"
        await c.post("/api/logbook/entries", headers=H, json={"kind": "thought", "text": "free note"})
        r = await c.get("/api/logbook/export?format=md&copy=1&team=Borealis&position=ttc", headers=H)
        md = await r.text()
        assert r.headers["Content-Disposition"].startswith("inline;")
        assert "- Team: Borealis" in md and "- Position: ttc" in md and "free note" in md
        j = await (await c.get("/api/logbook", headers=H)).json()
        assert j["last_download"] is None and j["unsaved"] == 2      # a copy is not a download
        r = await c.get("/api/logbook/export?format=html&sheet=WB-5.5-AT", headers=H)
        h = await r.text()
        assert "c2o-logbook-WB-5.5-AT-" in r.headers["Content-Disposition"]
        assert "recovered" in h and "free note" not in h
        j = await (await c.get("/api/logbook", headers=H)).json()
        assert j["last_download"] is not None
        r = await c.get("/api/logbook/worksheets?all=1&context=" + json.dumps({"procedure": "NOM-001"}),
                        headers=H)
        ws = (await r.json())["worksheets"]
        assert ws[0]["id"] == "WB-5.4-N001" and any(w["id"] == "WB-A-CTG-020" for w in ws)
        assert next(w for w in ws if w["id"] == "WB-5.5-AT")["form"] == "anomaly"
    finally:
        await c.close()
