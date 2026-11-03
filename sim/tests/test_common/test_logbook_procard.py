"""The procedure card as the working surface (2026-11-03).

Franz: "The procedure cards should help the user to go to the workbook to
mark steps as done or not, capture values, and capture decisions (the
procedure cards become part of the logbook as they get filled in)."

The MCS card view (smo_common/ui/procard.js) writes the SAME check records
as the logbook's Workbook tab. These tests pin the server half:

* the checklist carries the card's Prerequisites items (``prereqs``),
  French text only when the twin lists the same items;
* the store keeps ``check.part = "pre"`` and the ``run`` context key of a
  decision recorded from the card;
* the export prints the filled card: prerequisites first, then the steps,
  and the card's decisions under its run (not again in the log);
* ``GET /api/logbook/checklist`` serves the prerequisites.

The browser half (record shape, one source of truth, card keys) is in
test_procard_js.py.
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.logbook import LogbookStore, WorksheetCatalog, register_logbook_routes
from smo_common.logbook.checklist import ChecklistProvider, build_checklist, parse_prereqs
from smo_common.logbook.export import build_document, to_html, to_markdown

from .test_logbook_workbook import CFG, _catalog, _index

NOW = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
P = "op@example.org"

CARD = """# XYZ-002: Card With Prerequisites
**Subsystem:** TT&C

## Purpose
Test.

## Prerequisites
- [ ] COM-001 through COM-003 completed
- [ ] Bidirectional S-band link active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [x] OBC in the APPLICATION image (`obdh.sw_image` 0x0311 = 1). Booting the
      application lifts the PA inhibit.
- not a checkbox item
  - [ ] an indented item is continuation text, not an item

## Procedure Steps

### Step 1 — Deploy the antenna
**TC:** `TTC_DEPLOY_ANTENNA` (Service 8, Subtype 1, func_id 69)
**Verify:** `ttc.antenna_deployed == 1` (0x0520, timeout 30 s)
**GO/NO-GO:** antenna deployed
"""

CARD_FR = """# XYZ-002 : Carte avec prérequis

## Prérequis
- [ ] COM-001 à COM-003 terminées
- [ ] Liaison bidirectionnelle active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] OBC sur l'image APPLICATION (`obdh.sw_image` 0x0311 = 1)

## Déroulement

### Étape 1 — Déployer l'antenne
**TC:** `TTC_DEPLOY_ANTENNA` (Service 8, Subtype 1, func_id 69)
**Verify:** `ttc.antenna_deployed == 1` (0x0520, timeout 30 s)
**GO/NO-GO:** antenne déployée
"""


def test_parse_prereqs_items_and_continuations():
    pre = parse_prereqs(CARD)
    assert [p["key"] for p in pre] == ["p1", "p2", "p3"]
    assert pre[2]["text"].endswith("Booting the application lifts the PA inhibit.")
    # the Procedure Steps section and its bullets are not prerequisites
    assert all("antenna" not in p["text"] for p in pre)
    assert parse_prereqs(CARD_FR)[0]["text"] == "COM-001 à COM-003 terminées"


def test_checklist_carries_prereqs_with_checks_and_french():
    en = build_checklist("XYZ-002", CARD)
    assert [p["n"] for p in en["prereqs"]] == ["P1", "P2", "P3"]
    assert "checks" not in en["prereqs"][0]
    c = en["prereqs"][1]["checks"][0]
    assert (c["param"], c["pid"], c["op"], c["value"]) == ("ttc.link_status", "0x0501", "==", "2")
    assert en["prereqs"][1]["text"].startswith("Bidirectional S-band link active")   # markup removed
    fr = build_checklist("XYZ-002", CARD, card_md_fr=CARD_FR, lang="fr")
    assert fr["prereqs"][0]["text"] == "COM-001 à COM-003 terminées"
    # a French twin that lists other items is not used (the English stands)
    short = CARD_FR.replace("- [ ] COM-001 à COM-003 terminées\n", "")
    assert build_checklist("XYZ-002", CARD, card_md_fr=short, lang="fr")["prereqs"][0]["text"] \
        == "COM-001 through COM-003 completed"


def test_every_card_lists_the_same_prerequisites_in_french():
    """The card view numbers P1, P2… in the language shown: the twin must
    list as many items, or the French checklist falls back to English."""
    odd = []
    for e in _index():
        if not e.get("file"):
            continue
        en_p = CFG / "procedures" / e["file"]
        fr_p = CFG / "i18n" / "fr" / "procedures" / e["file"]
        if not en_p.is_file() or not fr_p.is_file():
            continue
        a = len(parse_prereqs(en_p.read_text(encoding="utf-8")))
        b = len(parse_prereqs(fr_p.read_text(encoding="utf-8")))
        if a != b:
            odd.append(f"{e['id']}: {a} EN vs {b} FR")
    assert not odd, odd


def test_real_card_prereqs_served_by_the_provider():
    cat = WorksheetCatalog(CFG / "worksheets")
    tc = _catalog()
    prov = ChecklistProvider(_index(), CFG / "procedures", CFG / "i18n" / "fr" / "procedures",
                             cat.sheets, lambda: tc)
    cl = prov("COM-006", "en")
    assert len(cl["prereqs"]) == 7
    assert cl["prereqs"][5]["checks"][0]["param"] == "ttc.link_status"


# ── store and export ─────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    return LogbookStore(tmp_path / "lb", retention_h=48, max_age_h=168)


def _rec(store, key, result, *, part=None, order=0, step="", values=None, note=""):
    check = {"procedure": "COM-006", "step": step, "key": key, "order": order, "title": f"title {key}",
             "run": "1", "result": result, "source": "operator", "position": "ttc", "note": note,
             "values": values or []}
    if part:
        check["part"] = part
    return store.add(P, {"kind": "worksheet", "tool": "mcs", "text": f"{key} — {result}",
                         "context": {"procedure": "COM-006", "step": step or key},
                         "worksheet": {"id": "WB-5.6-C006", "q": key, "instance": "1",
                                       "checked": result not in ("open", "fail", "skip", "nogo")},
                         "check": check})


def test_store_keeps_prereq_part_and_card_run_context(store):
    e = _rec(store, "p2", "done", part="pre", order=1, step="P2")
    assert e["check"]["part"] == "pre" and e["check"]["step"] == "P2"
    bad = _rec(store, "s1", "pass", part="bogus", step="1")
    assert "part" not in bad["check"]
    d = store.add(P, {"kind": "decision", "tool": "mcs", "text": "Hold Step 2a.",
                      "context": {"procedure": "COM-006", "step": "1", "run": "1", "nope": 1}})
    assert d["context"] == {"procedure": "COM-006", "step": "1", "run": "1"}


def _filled_card(store):
    # recorded out of order, as an operator works: step, prerequisite, step
    _rec(store, "s1", "nogo", order=1, step="1", note="margin 4.2 dB",
         values=[{"param": "ttc.link_margin", "expect": "ttc.link_margin > 6.0 dB", "value": "4.20", "units": "dB",
                  "ok": False}])
    _rec(store, "p1", "done", part="pre", order=0, step="P1")
    _rec(store, "s0", "go", order=0, step="0")
    store.add(P, {"kind": "decision", "tool": "mcs", "text": "COM-006 · Step 1\nDecision: hold Step 2a",
                  "context": {"procedure": "COM-006", "step": "1", "run": "1"}})
    store.add(P, {"kind": "decision", "tool": "mcs", "text": "Unrelated decision.",
                  "context": {"procedure": "CTG-001"}})
    return store.summary(P)


def test_export_prints_the_filled_card(store):
    summary = _filled_card(store)
    doc = build_document(summary, P, now=NOW)
    run = doc["sheets"][0]["runs"][0]
    assert [e["check"]["key"] for e in run["rows"]] == ["p1", "s0", "s1"]    # prerequisites first
    assert [e["text"] for e in run["decisions"]] == ["COM-006 · Step 1\nDecision: hold Step 2a"]
    log_texts = [e["text"] for _, es in doc["log"] for e in es]
    assert log_texts == ["Unrelated decision."]            # the card's decision is not printed twice
    md = to_markdown(summary, P, now=NOW)
    assert md.index("| P1 |") < md.index("| 0 |") < md.index("| 1 |")
    assert "**Decisions recorded on this card**" in md and "Decision: hold Step 2a" in md
    assert "4.20 dB ✗" in md and "**NO-GO**" in md
    fr = to_markdown(summary, P, now=NOW, lang="fr")
    assert "Décisions consignées sur cette carte" in fr
    html = to_html(summary, P, now=NOW)
    assert "<h4>Decisions recorded on this card</h4>" in html
    # one sheet only ("This sheet"): the card's decisions stay with it
    one = build_document(summary, P, now=NOW, sheet="WB-5.6-C006")
    assert one["sheets"][0]["runs"][0]["decisions"] and not one["log"]


# ── HTTP ─────────────────────────────────────────────────────────────────

H = {"X-Goog-Authenticated-User-Email": "accounts.google.com:op@example.org"}


async def test_checklist_route_serves_prereqs(tmp_path):
    tc = _catalog()

    def factory(catalog):
        return ChecklistProvider(_index(), CFG / "procedures", CFG / "i18n" / "fr" / "procedures",
                                 catalog.sheets, lambda: tc)
    factory.wants_catalog = True
    app = web.Application()
    register_logbook_routes(app, tool="mcs", store_dir=tmp_path / "lb",
                            worksheets_dir=CFG / "worksheets", checklists=factory)
    c = TestClient(TestServer(app))
    await c.start_server()
    try:
        r = await c.get("/api/logbook/checklist?procedure=COM-006&lang=fr", headers=H)
        j = await r.json()
        assert r.status == 200 and [p["key"] for p in j["prereqs"]] == [f"p{i}" for i in range(1, 8)]
        assert j["prereqs"][1]["text"] == "OBC en mode NOMINAL"
        # a prerequisite tick posted the way the card posts it round-trips
        body = {"kind": "worksheet", "tool": "mcs", "lang": "fr", "text": "Prérequis P6 — faite",
                "context": {"procedure": "COM-006", "step": "P6", "page": "proc"},
                "worksheet": {"id": j["sheet_id"], "q": "p6", "instance": "1", "checked": True},
                "check": {"procedure": "COM-006", "step": "P6", "key": "p6", "order": 5, "run": "1",
                          "result": "done", "part": "pre", "source": "operator",
                          "values": [{"param": "ttc.link_status", "pid": "0x0501",
                                      "expect": "ttc.link_status = 2", "value": "2", "ok": True}]}}
        r = await c.post("/api/logbook/entries", json=body, headers=H)
        e = await r.json()
        assert r.status in (200, 201) and e["check"]["part"] == "pre" and e["check"]["values"][0]["ok"] is True
        md = await (await c.get("/api/logbook/export?format=md&copy=1&lang=fr", headers=H)).text()
        assert "| P6 |" in md and "faite" in md
    finally:
        await c.close()


async def test_doc_viewer_cards_are_working_copies_too(tmp_path, monkeypatch):
    """The documentation viewer renders the procedure cards, so it mounts the
    same working copy (no live TM there: no capture) and serves the card's
    checklist; a manual page stays a plain document."""
    import importlib.util
    import sys
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(tmp_path / "lb"))
    tools = Path(__file__).resolve().parents[2] / "tools"
    spec = importlib.util.spec_from_file_location("_pc_doc_viewer", tools / "doc_viewer.py")
    dv = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = dv
    spec.loader.exec_module(dv)
    c = TestClient(TestServer(dv.create_app(CFG)))
    await c.start_server()
    try:
        t = await (await c.get("/doc/procedures/commissioning/ttc_link_verification.md?lang=fr")).text()
        assert 'data-procedure="COM-006"' in t and "/static/shared/procard.js" in t
        assert 'levels: { step: "H3", section: "H2" }, live: false' in t
        t = await (await c.get("/doc/manual/00_mission_overview.md")).text()
        assert "<article lang=\"en\">" in t and 'import { mountProcCard }' not in t
        r = await c.get("/api/logbook/checklist?procedure=COM-006&lang=en", headers=H)
        assert r.status == 200 and len((await r.json())["prereqs"]) == 7
    finally:
        await c.close()
