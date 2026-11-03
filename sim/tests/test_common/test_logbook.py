"""Participant logbook: store, fold, purge, export, identity, limits, routes.

docs/plan_2026-11/LOGBOOK_SPEC.md is the contract (SpaceCDF implements the
same file format and HTTP API in FastAPI, so these tests pin both).
"""
from __future__ import annotations

import json
import os
import stat
import threading
import time
from datetime import datetime, timedelta, timezone

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.logbook import (LogbookError, LogbookStore, WorksheetCatalog,
                                identify, register_logbook_routes)
from smo_common.logbook.export import export_filename, to_html, to_json, to_markdown
from smo_common.logbook.identity import COOKIE, IAP_HEADER, cookie_header
from smo_common.logbook.store import file_name, iso

P = "alice@example.org"
NOW = datetime(2026, 11, 2, 23, 41, 7, 123000, tzinfo=timezone.utc)


def _add(store, text="went GO", kind="decision", tool="mcs", **kw):
    return store.add(P, {"kind": kind, "text": text, "tool": tool, **kw})


@pytest.fixture
def store(tmp_path):
    return LogbookStore(tmp_path / "logbook", retention_h=48, max_age_h=168)


# ── storage format ─────────────────────────────────────────────────────

def test_file_per_person_named_by_hash_with_private_modes(store):
    _add(store)
    path = store.path_for(P)
    assert path.name == file_name(P) and len(path.stem) == 32
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.dir.stat().st_mode) == 0o700
    rec = json.loads(path.read_text().splitlines()[0])
    assert rec["v"] == 1 and rec["op"] == "add" and rec["tool"] == "mcs"
    assert rec["ts"].endswith("Z") and len(rec["ts"]) == len("2026-11-02T23:41:07.123Z")


def test_iso_format():
    assert iso(NOW) == "2026-11-02T23:41:07.123Z"


def test_edits_and_deletes_are_appended_and_folded(store):
    a = _add(store, "first")
    b = _add(store, "second", kind="thought")
    store.edit(P, a["id"], {"text": "first, revised"})
    store.delete(P, b["id"])
    lines = store.path_for(P).read_text().splitlines()
    assert [json.loads(x)["op"] for x in lines] == ["add", "add", "edit", "delete"]
    entries = store.entries(P)
    assert [e["text"] for e in entries] == ["first, revised"]
    assert entries[0]["edited"] is True


def test_entries_are_newest_first(store):
    for i in range(3):
        _add(store, f"n{i}")
        time.sleep(0.002)
    assert [e["text"] for e in store.entries(P)] == ["n2", "n1", "n0"]


def test_context_is_whitelisted_and_clipped(store):
    e = _add(store, context={"page": "eps", "procedure": "CTG-001", "alarm_id": 42,
                             "evil": "x", "param": "y" * 500})
    assert e["context"] == {"page": "eps", "procedure": "CTG-001", "alarm_id": 42,
                            "param": "y" * 200}


def test_torn_line_is_skipped(store):
    _add(store, "ok")
    with open(store.path_for(P), "a") as f:
        f.write('{"v":1,"id":"x","op":"add","te')
    assert [e["text"] for e in store.entries(P)] == ["ok"]


# ── validation and limits ──────────────────────────────────────────────

@pytest.mark.parametrize("body,status", [
    ({"kind": "rant", "text": "x", "tool": "mcs"}, 400),
    ({"kind": "decision", "text": "x", "tool": "nope"}, 400),
    ({"kind": "decision", "text": "   ", "tool": "mcs"}, 400),
    ({"kind": "decision", "text": 5, "tool": "mcs"}, 400),
    ({"kind": "worksheet", "text": "x", "tool": "mcs"}, 400),
])
def test_bad_entries_rejected(store, body, status):
    with pytest.raises(LogbookError) as ei:
        store.add(P, body)
    assert ei.value.status == status


def test_text_limit_is_413(store):
    _add(store, "x" * 8000)
    with pytest.raises(LogbookError) as ei:
        _add(store, "x" * 8001)
    assert ei.value.status == 413


def test_entry_count_limit_is_413_with_download_hint(tmp_path):
    s = LogbookStore(tmp_path, max_entries=3)
    for i in range(3):
        s.add(P, {"kind": "thought", "text": str(i), "tool": "mcs"})
    with pytest.raises(LogbookError) as ei:
        s.add(P, {"kind": "thought", "text": "4", "tool": "mcs"})
    assert ei.value.status == 413 and "Download" in str(ei.value)


def test_edit_and_delete_unknown_entry_404(store):
    for fn in (lambda: store.edit(P, "nope", {"text": "x"}), lambda: store.delete(P, "nope")):
        with pytest.raises(LogbookError) as ei:
            fn()
        assert ei.value.status == 404
    _add(store)
    with pytest.raises(LogbookError):
        store.edit(P, "nope", {"text": "x"})


def test_edit_churn_is_compacted(tmp_path, monkeypatch):
    import smo_common.logbook.store as st
    monkeypatch.setattr(st, "COMPACT_SLACK", 10)
    s = LogbookStore(tmp_path)
    e = s.add(P, {"kind": "thought", "text": "v0", "tool": "mcs"})
    for i in range(30):
        s.edit(P, e["id"], {"text": f"v{i + 1}"})
    assert len(s.path_for(P).read_text().splitlines()) < 15
    assert s.entries(P)[0]["text"] == "v30"


def test_concurrent_writers_lose_nothing(store):
    def w(n):
        for i in range(20):
            store.add(P, {"kind": "thought", "text": f"{n}-{i}", "tool": "mcs"})
    ts = [threading.Thread(target=w, args=(n,)) for n in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(store.entries(P)) == 80


# ── summary, downloads, retention ──────────────────────────────────────

def test_summary_expires_48h_after_last_write_and_counts_unsaved(store):
    a = _add(store)
    s = store.summary(P)
    lw = datetime.fromisoformat(s["last_write"].replace("Z", "+00:00"))
    ex = datetime.fromisoformat(s["expires_at"].replace("Z", "+00:00"))
    assert ex - lw == timedelta(hours=48)
    assert s["count"] == 1 and s["unsaved"] == 1 and s["last_download"] is None
    mtime = store.path_for(P).stat().st_mtime
    time.sleep(0.02)
    store.mark_downloaded(P, "md")
    s2 = store.summary(P)
    assert s2["unsaved"] == 0 and s2["last_download"]
    assert s2["expires_at"] == s["expires_at"]                     # not a write
    assert store.path_for(P).stat().st_mtime == pytest.approx(mtime)
    store.edit(P, a["id"], {"text": "changed"})
    assert store.summary(P)["unsaved"] == 1


def test_summary_filters(store):
    _add(store, "a", tool="mcs")
    _add(store, "b", tool="orbit")
    assert [e["text"] for e in store.summary(P, tool="orbit")["entries"]] == ["b"]
    assert store.summary(P, tool="orbit")["count"] == 2


def test_empty_logbook_summary(store):
    s = store.summary("nobody@example.org")
    assert s["count"] == 0 and s["expires_at"] is None and s["entries"] == []


def test_purge_deletes_idle_files_and_is_idempotent(store):
    _add(store)
    path = store.path_for(P)
    old = time.time() - 49 * 3600
    os.utime(path, (old, old))
    assert store.purge()["files_deleted"] == 1
    assert not path.exists()
    assert store.purge() == {"files_deleted": 0, "entries_dropped": 0, "files_kept": 0}


def test_purge_keeps_active_file_and_drops_entries_over_max_age(store):
    old_ts = datetime.now(timezone.utc) - timedelta(days=8)
    store.add(P, {"kind": "thought", "text": "ancient", "tool": "mcs"}, now=old_ts)
    store.mark_downloaded(P, "md", now=old_ts)
    _add(store, "recent")
    mtime = store.path_for(P).stat().st_mtime
    stats = store.purge()
    assert stats["entries_dropped"] == 1 and stats["files_kept"] == 1
    assert [e["text"] for e in store.entries(P)] == ["recent"]
    assert store.summary(P)["last_download"] is None
    assert store.path_for(P).stat().st_mtime == pytest.approx(mtime)
    assert store.purge()["entries_dropped"] == 0


def test_purge_with_no_directory(tmp_path):
    assert LogbookStore(tmp_path / "absent").purge()["files_kept"] == 0


def test_writer_survives_a_concurrent_delete(store):
    _add(store, "one")
    assert store.delete_all(P) is True
    assert store.delete_all(P) is False
    _add(store, "two")
    assert [e["text"] for e in store.entries(P)] == ["two"]


def test_retention_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SMO_LOGBOOK_RETENTION_H", "12")
    monkeypatch.setenv("SMO_LOGBOOK_MAX_AGE_H", "24")
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(tmp_path / "x"))
    s = LogbookStore()
    assert (s.retention_h, s.max_age_h, s.dir) == (12, 24, tmp_path / "x")


# ── identity ───────────────────────────────────────────────────────────

def test_iap_identity_strips_prefix_and_lowercases():
    i = identify({IAP_HEADER: "accounts.google.com:Alice@Example.ORG"}, {})
    assert (i.person_id, i.local, i.new_cookie, i.label) == (P, False, None, P)


def test_local_identity_uses_or_mints_the_cookie():
    fresh = identify({}, {})
    assert fresh.local and fresh.new_cookie == fresh.person_id
    assert fresh.person_id.startswith("local:") and len(fresh.person_id) == 6 + 32
    again = identify({}, {COOKIE: fresh.person_id})
    assert again.person_id == fresh.person_id and again.new_cookie is None
    assert again.label == "this browser"
    forged = identify({}, {COOKIE: "local:../../etc"})
    assert forged.person_id != "local:../../etc" and forged.new_cookie


def test_cookie_attributes():
    h = cookie_header("local:" + "0" * 32)
    for part in ("Path=/", "Max-Age=2592000", "SameSite=Lax", "HttpOnly"):
        assert part in h
    assert "Secure" in cookie_header("local:" + "0" * 32, secure=True)


# ── export ─────────────────────────────────────────────────────────────

def _summary(store):
    _add(store, "Went GO for load shed", context={"procedure": "CTG-001", "page": "eps"},
         sim_ts="2026-03-10T04:18:22Z")
    _add(store, "Bus at 24.6 V", kind="observation", tool="delayed_tm")
    store.add(P, {"kind": "worksheet", "text": "I would not have shed the cooler first.",
                  "tool": "mcs", "worksheet": {"id": "WB-5.5-DB", "q": "q1", "checked": True}})
    return store.summary(P)


def test_markdown_export(store):
    s = _summary(store)
    md = to_markdown(s, P, lookup=WorksheetCatalog().question, now=NOW)
    assert md.startswith("# C2O logbook")
    assert f"- Person: {P}" in md and "- Entries: 3" in md
    assert "Mission control, Delayed TM" in md
    # ops workbook (2026-11): worksheets first, then the chronological log
    assert md.index("## Workbook") < md.index("## Log")
    assert "Mission control · Decision" in md and "Delayed TM · Observation" in md
    assert "procedure CTG-001" in md and "sim time 2026-03-10T04:18:22Z" in md
    assert "### WB-5.5-DB — Day 3 Post-Shift Debrief Reflection" in md
    assert "What is one decision you took during the shift" in md
    assert "[x] I would not have shed" in md
    assert "Deleted from the C2O server on" in md.splitlines()[-1]


def test_markdown_export_in_french_for_this_browser(store):
    s = _summary(store)
    md = to_markdown(s, "this browser", lang="fr", lookup=WorksheetCatalog().question, now=NOW)
    assert "# Journal de bord C2O" in md and "Personne\u00a0: ce navigateur" in md
    assert "Contrôle de mission" in md and "Supprimé du serveur C2O le" in md
    assert "Quelle décision avez-vous prise" in md


def test_html_export_is_self_contained_and_escaped(store):
    _add(store, "<script>alert(1)</script>")
    s = store.summary(P)
    h = to_html(s, P, now=NOW)
    assert h.startswith("<!DOCTYPE html>") and "@page" in h
    assert "<script>" not in h and "&lt;script&gt;" in h
    assert "src=" not in h and "http" not in h.replace("http-equiv", "")
    assert "Deleted from the C2O server on" in h


def test_json_export(store):
    s = _summary(store)
    doc = json.loads(to_json(s, P, lookup=WorksheetCatalog().question, now=NOW))
    assert doc["count"] == 3 and doc["person"] == P
    ws = [e for e in doc["entries"] if e["kind"] == "worksheet"][0]
    assert ws["worksheet"]["q_text"].startswith("What is one decision")


def test_export_filename():
    assert export_filename("md", NOW) == "c2o-logbook-20261102-2341.md"
    assert export_filename("html", NOW) == "c2o-logbook-20261102-2341.html"


# ── worksheets ─────────────────────────────────────────────────────────

def test_worksheet_matching():
    c = WorksheetCatalog()
    ids = [w["id"] for w in c.match("mcs", {"procedure": "NOM-001"})]
    assert ids[0] == "WB-5.4-N001"
    assert "WB-5.5-L001" not in ids                  # other procedures' sheets
    assert "WB-5.5-DB" in ids                        # general for the MCS
    assert [w["id"] for w in c.match("mcs", {"procedure": "LEOP-003"})][0] == "WB-5.5-L003"
    assert [w["id"] for w in c.match("mcs", {"procedure": "COM-002"})][0] == "WB-5.6-C002"
    assert [w["id"] for w in c.match("mcs", {"procedure": "CTG-003"})][0] == "WB-5.4-C003"
    assert [w["id"] for w in c.match("instructor", {"scenario": "first_contact",
                                                    "phase": "prep"})] == ["WB-5.5-PB"]
    deb = [w["id"] for w in c.match("instructor", {"phase": "debrief"})]
    assert "WB-5.5-DB" in deb and "WB-5.5-GO" in deb
    at = c.match("delayed_tm", {"anomaly": True})
    assert at[0]["id"] == "WB-5.5-AT" and at[0]["match"] == "context"


def test_worksheet_localisation():
    w = WorksheetCatalog().match("mcs", {"procedure": "NOM-001"}, lang="fr")[0]
    assert w["title"].startswith("NOM-001 Ouverture de passage")
    assert w["questions"][0]["kind"] == "check"
    assert w["questions"][0]["text"].startswith("1. Segment sol")


# ── HTTP routes ────────────────────────────────────────────────────────

async def _client(tmp_path, tool="mcs"):
    app = web.Application()
    register_logbook_routes(app, tool=tool, store_dir=tmp_path / "lb", purge_interval_s=3600)
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


async def test_routes_round_trip_with_iap_identity(tmp_path):
    c = await _client(tmp_path)
    H = {IAP_HEADER: "accounts.google.com:" + P}
    try:
        r = await c.get("/api/logbook", headers=H)
        j = await r.json()
        assert r.status == 200 and j["count"] == 0
        assert j["person"] == {"id_label": P, "local": False}
        assert j["retention_h"] == 48 and j["max_age_h"] == 168
        assert "Set-Cookie" not in r.headers and r.headers["Cache-Control"] == "no-store"

        r = await c.post("/api/logbook/entries", headers=H, json={
            "kind": "decision", "text": "GO", "context": {"page": "eps"}})
        e = await r.json()
        assert r.status == 201 and e["tool"] == "mcs" and e["context"] == {"page": "eps"}

        r = await c.post("/api/logbook/entries", headers=H, json={
            "kind": "worksheet", "text": "nominal", "worksheet": {"id": "WB-5.5-DB", "q": "q2"}})
        w = await r.json()
        assert w["worksheet"]["title"] == "Day 3 Post-Shift Debrief Reflection"
        assert w["worksheet"]["q_text"].startswith("What is one decision that surprised")

        r = await c.patch(f"/api/logbook/entries/{e['id']}", headers=H, json={"text": "NO-GO"})
        assert (await r.json())["text"] == "NO-GO"
        r = await c.delete(f"/api/logbook/entries/{w['id']}", headers=H)
        assert await r.json() == {"ok": True}

        j = await (await c.get("/api/logbook", headers=H)).json()
        assert j["count"] == 1 and j["unsaved"] == 1 and j["expires_at"]

        r = await c.get("/api/logbook/export?format=md&lang=en", headers=H)
        assert r.status == 200 and r.content_type == "text/markdown"
        cd = r.headers["Content-Disposition"]
        assert cd.startswith('attachment; filename="c2o-logbook-') and cd.endswith('.md"')
        assert "NO-GO" in await r.text()
        j = await (await c.get("/api/logbook", headers=H)).json()
        assert j["unsaved"] == 0 and j["last_download"]

        r = await c.get("/api/logbook/export?format=html&lang=fr", headers=H)
        assert r.content_type == "text/html" and "Journal de bord C2O" in await r.text()
        r = await c.get("/api/logbook/export?format=pdf", headers=H)
        assert r.status == 400

        r = await c.get("/api/logbook/worksheets?context=" + json.dumps({"procedure": "NOM-001"}),
                        headers=H)
        j = await r.json()
        assert j["tool"] == "mcs" and j["worksheets"][0]["id"] == "WB-5.4-N001"

        r = await c.delete("/api/logbook", headers=H)
        assert (await r.json())["deleted"] is True
        assert (await (await c.get("/api/logbook", headers=H)).json())["count"] == 0
    finally:
        await c.close()


async def test_routes_local_cookie_identity_and_privacy(tmp_path):
    c = await _client(tmp_path, tool="delayed_tm")
    try:
        r = await c.get("/api/logbook")
        sc = r.headers["Set-Cookie"]
        assert sc.startswith(COOKIE + "=local:") and "HttpOnly" in sc
        assert (await r.json())["person"] == {"id_label": "this browser", "local": True}
        cookie = sc.split(";", 1)[0].split("=", 1)[1]
        c.session.cookie_jar.clear()          # send cookies explicitly below
        mine = {"Cookie": f"{COOKIE}={cookie}"}
        r = await c.post("/api/logbook/entries", headers=mine,
                         json={"kind": "observation", "text": "secret"})
        e = await r.json()
        assert e["tool"] == "delayed_tm"
        # another browser sees nothing and cannot touch the entry
        other = {"Cookie": f"{COOKIE}=local:{'f' * 32}"}
        assert (await (await c.get("/api/logbook", headers=other)).json())["count"] == 0
        r = await c.patch(f"/api/logbook/entries/{e['id']}", headers=other, json={"text": "x"})
        assert r.status == 404
        r = await c.delete(f"/api/logbook/entries/{e['id']}", headers=other)
        assert r.status == 404
        assert (await (await c.get("/api/logbook", headers=mine)).json())["count"] == 1
    finally:
        await c.close()


async def test_routes_reject_bad_bodies(tmp_path):
    c = await _client(tmp_path)
    try:
        r = await c.post("/api/logbook/entries", data="not json",
                         headers={"Content-Type": "application/json"})
        assert r.status == 400
        r = await c.post("/api/logbook/entries", json=[1, 2])
        assert r.status == 400
        r = await c.post("/api/logbook/entries", json={"kind": "thought", "text": "x" * 9000})
        assert r.status == 413
        r = await c.post("/api/logbook/entries", data=b"{" + b" " * 70000 + b"}",
                         headers={"Content-Type": "application/json"})
        assert r.status == 413
        r = await c.post("/api/logbook/entries", data='{"kind":"thought","text":"csrf"}',
                         headers={"Content-Type": "text/plain"})
        assert r.status == 415                   # no cross-site form posts
        r = await c.get("/api/logbook/worksheets?context=%7Bbad")
        assert r.status == 200
    finally:
        await c.close()


def test_register_rejects_unknown_tool():
    with pytest.raises(ValueError):
        register_logbook_routes(web.Application(), tool="spacecraft")


async def test_purge_task_runs_at_startup(tmp_path):
    lb = tmp_path / "lb"
    s = LogbookStore(lb)
    s.add(P, {"kind": "thought", "text": "old", "tool": "mcs"})
    old = time.time() - 72 * 3600
    os.utime(s.path_for(P), (old, old))
    c = await _client(tmp_path)
    try:
        for _ in range(50):
            if not s.path_for(P).exists():
                break
            await __import__("asyncio").sleep(0.02)
        assert not s.path_for(P).exists()
    finally:
        await c.close()


def test_shared_group_mode(tmp_path, monkeypatch):
    """Ground VM: SMO (uid 10001) and SpaceCDF (uid 10002 + smo group) share
    the store, so SMO_LOGBOOK_SHARED_GROUP=1 gives 0660 files in 02770."""
    monkeypatch.setenv("SMO_LOGBOOK_SHARED_GROUP", "1")
    s = LogbookStore(tmp_path / "lb")
    s.add(P, {"kind": "thought", "text": "x", "tool": "mcs"})
    assert stat.S_IMODE(s.path_for(P).stat().st_mode) == 0o660
    assert stat.S_IMODE(s.dir.stat().st_mode) == 0o2770


# ── the shared panel and where it is mounted ───────────────────────────

from pathlib import Path as _P  # noqa: E402

_SIM = _P(__file__).resolve().parents[2]
_UI = _SIM / "packages" / "smo-common" / "src" / "smo_common" / "ui"


def test_panel_module_contract():
    js = (_UI / "logbook.js").read_text(encoding="utf-8")
    for name in ("export function mountLogbook", "export function logThis",
                 "export function renderLogThis", "export async function endSession"):
        assert name in js
    assert "localStorage" not in js          # the text lives on the server only
    assert "sessionStorage" in js            # an unsent draft may stay in the tab
    assert '"/api/logbook"' in js
    assert "beforeunload" in js
    css = (_UI / "logbook.css").read_text(encoding="utf-8")
    import re
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css), "tokens only, no hex colours"


@pytest.mark.parametrize("path,needle", [
    ("packages/smo-mcs/src/smo_mcs/static/modern/mcs.js", 'mountLogbook({ tool: "mcs"'),
    ("packages/smo-mcs/src/smo_mcs/server.py", 'register_logbook_routes(app, tool="mcs"'),
    ("tools/delayed_tm_viewer.py", 'logbook="delayed_tm"'),
    ("tools/delayed_tm_viewer.py", 'register_logbook_routes(app, tool="delayed_tm"'),
    ("tools/orbit_tools.py", 'logbook="orbit"'),
    ("tools/doc_viewer.py", 'logbook="docs"'),
    ("tools/portal.py", 'logbook="portal"'),
    ("packages/smo-rfsim/src/smo_rfsim/static/modern/index.html", 'tool: "radio"'),
    ("packages/smo-rfsim/src/smo_rfsim/radio/web_ui.py", 'tool="radio"'),
    ("packages/smo-simulator/src/smo_simulator/instructor/static/modern/instructor.js",
     'mountLogbook({ tool: "instructor"'),
    ("packages/smo-simulator/src/smo_simulator/instructor/app.py", 'tool="instructor"'),
    ("packages/smo-link/src/smo_link/gateway.py", 'tool="instructor"'),
])
def test_every_tool_mounts_the_logbook(path, needle):
    assert needle in (_SIM / path).read_text(encoding="utf-8"), path


def test_mcs_log_this_beside_decisions():
    js = (_SIM / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js").read_text(encoding="utf-8")
    html = (_SIM / "packages/smo-mcs/src/smo_mcs/static/modern/index.html").read_text(encoding="utf-8")
    assert js.count("renderLogThis(") >= 4     # send, procedure controls, alarm row, GO/NO-GO
    assert 'id="gonogo-logthis"' in html and 'id="lb-slot"' in html
    assert "LB.endSession({ reason: \"stopped\" })" in js


def test_compaction_keeps_spacecdf_decision_record(tmp_path):
    """SpaceCDF writes a structured ``record`` into the shared file; the ops
    store must carry it through fold and compaction (shared format, §8)."""
    from smo_common.logbook.store import LogbookStore
    st = LogbookStore(tmp_path)
    rec = {"question": "Orbit?", "choice": "SSO 525 km", "options": [{"name": "SSO 525 km"}]}
    recs = [
        {"v": 1, "id": "d1", "op": "add", "ts": "2026-11-02T10:00:00.000Z", "tool": "design",
         "kind": "decision", "text": "Orbit: SSO 525 km", "context": {"decision_id": "D-ORBIT"},
         "record": rec, "lang": "en"},
        {"v": 1, "id": "d1", "op": "edit", "ts": "2026-11-02T10:05:00.000Z",
         "text": "Orbit: SSO 530 km", "record": {**rec, "choice": "SSO 530 km"}},
    ]
    out = st._compacted(recs)
    folded = st.fold(out).entries
    assert folded[0]["record"]["choice"] == "SSO 530 km"
    assert folded[0]["text"] == "Orbit: SSO 530 km"
