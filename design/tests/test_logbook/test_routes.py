"""/api/logbook routes: identity, CRUD, export, worksheets (LOGBOOK_SPEC.md §1, §3)."""
from __future__ import annotations

import json
import re

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from spacecdf_server.logbook import router as lb_router

IAP = {"X-Goog-Authenticated-User-Email": "accounts.google.com:Alice@C2O.live"}


@pytest.fixture()
async def client(lbdir):
    app = FastAPI()
    app.include_router(lb_router, prefix="/api/logbook")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _entry(**kw):
    return {"kind": "decision", "text": "Accept the EPS–OBC power link", "tool": "design",
            "context": {"study_id": "s1", "study_name": "AuroraSat", "tab": "interfaces", "level": 2}, **kw}


async def test_iap_identity_no_cookie(client):
    r = await client.get("/api/logbook", headers=IAP)
    assert r.status_code == 200
    body = r.json()
    assert body["person"] == {"id_label": "alice@c2o.live", "local": False}
    assert body["entries"] == [] and body["count"] == 0
    assert body["retention_h"] == 48 and body["max_age_h"] == 168
    assert body["expires_at"] is None and body["last_write"] is None
    assert "c2o_lb" not in r.headers.get("set-cookie", "")


async def test_local_cookie_is_issued_and_reused(client):
    r = await client.get("/api/logbook")
    cookie = r.headers["set-cookie"]
    assert re.match(r'c2o_lb="?local:[0-9a-f]{32}"?;', cookie), cookie
    low = cookie.lower()
    assert "httponly" in low and "samesite=lax" in low and "path=/" in low and "max-age=2592000" in low
    assert r.json()["person"] == {"id_label": "this browser", "local": True}
    assert (await client.get("/api/logbook?lang=fr")).json()["person"]["id_label"] == "ce navigateur"
    # the client kept the cookie: the same person writes and reads
    await client.post("/api/logbook/entries", json=_entry())
    assert (await client.get("/api/logbook")).json()["count"] == 1


async def test_iap_wins_over_cookie(client, lbdir):
    await client.post("/api/logbook/entries", json=_entry(text="as this browser"))
    r = await client.get("/api/logbook", headers=IAP)
    assert r.json()["count"] == 0


async def test_crud_round_trip(client):
    r = await client.post("/api/logbook/entries", json=_entry(), headers=IAP)
    assert r.status_code == 201
    e = r.json()
    assert e["tool"] == "design" and e["kind"] == "decision" and not e["edited"]
    r = await client.patch(f"/api/logbook/entries/{e['id']}", json={"text": "Reject it instead"}, headers=IAP)
    assert r.status_code == 200 and r.json()["text"] == "Reject it instead" and r.json()["edited"]
    body = (await client.get("/api/logbook", headers=IAP)).json()
    assert body["count"] == 1 and body["unsaved"] == 1
    assert body["expires_at"] and body["last_write"]
    r = await client.delete(f"/api/logbook/entries/{e['id']}", headers=IAP)
    assert r.json() == {"ok": True}
    assert (await client.get("/api/logbook", headers=IAP)).json()["count"] == 0
    assert (await client.delete(f"/api/logbook/entries/{e['id']}", headers=IAP)).status_code == 404


async def test_filters(client):
    await client.post("/api/logbook/entries", json=_entry(), headers=IAP)
    await client.post("/api/logbook/entries", json=_entry(tool="mcs", text="from the MCS"), headers=IAP)
    body = (await client.get("/api/logbook?tool=mcs", headers=IAP)).json()
    assert len(body["entries"]) == 1 and body["entries"][0]["tool"] == "mcs"
    assert body["count"] == 2, "count is every live entry (as smo-common); filters narrow entries"
    body = (await client.get("/api/logbook?since=2099-01-01T00:00:00Z", headers=IAP)).json()
    assert body["entries"] == []


async def test_errors_are_json(client):
    r = await client.post("/api/logbook/entries", json={"kind": "x", "text": "y", "tool": "design"})
    assert r.status_code == 400 and "kind" in r.json()["detail"]
    r = await client.post("/api/logbook/entries", json=_entry(text="z" * 8001))
    assert r.status_code == 413
    r = await client.patch("/api/logbook/entries/nope", json={"text": "x"})
    assert r.status_code == 404


async def test_export_md_marks_download(client):
    await client.post("/api/logbook/entries", json=_entry(), headers=IAP)
    r = await client.get("/api/logbook/export?format=md&lang=en", headers=IAP)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert re.match(r'attachment; filename="c2o-logbook-\d{8}-\d{4}\.md"', r.headers["content-disposition"])
    assert "# C2O logbook" in r.text and "alice@c2o.live" in r.text
    assert "Accept the EPS–OBC power link" in r.text and "Deleted from the C2O server on" in r.text
    body = (await client.get("/api/logbook", headers=IAP)).json()
    assert body["last_download"] and body["unsaved"] == 0


async def test_export_html_and_json(client):
    await client.post("/api/logbook/entries", json=_entry(text="<script>x</script>"), headers=IAP)
    r = await client.get("/api/logbook/export?format=html&lang=fr", headers=IAP)
    assert r.headers["content-type"].startswith("text/html")
    assert '<html lang="fr">' in r.text and "Journal de bord C2O" in r.text
    assert "<script>" not in r.text and "&lt;script&gt;" in r.text
    assert "@page" in r.text
    r = await client.get("/api/logbook/export?format=json", headers=IAP)
    data = json.loads(r.text)
    assert data["count"] == 1 and data["person"] == "alice@c2o.live"
    assert (await client.get("/api/logbook/export?format=pdf", headers=IAP)).status_code == 400


async def test_delete_now(client):
    await client.post("/api/logbook/entries", json=_entry(), headers=IAP)
    assert (await client.delete("/api/logbook", headers=IAP)).json() == {"ok": True, "deleted": True}
    assert (await client.get("/api/logbook", headers=IAP)).json()["count"] == 0


async def test_worksheets_for_context(client):
    ctx = json.dumps({"tab": "interfaces", "level": 2})
    r = await client.get(f"/api/logbook/worksheets?tool=design&lang=en&context={ctx}", headers=IAP)
    body = r.json()
    ids = [w["id"] for w in body["worksheets"]]
    assert "LW-2.4" in ids and all(w["match"] for w in body["worksheets"])
    assert "LW-5.3" not in ids
    ws = next(w for w in body["worksheets"] if w["id"] == "LW-2.4")
    assert ws["title"] == "Mission Architecture – Segments, Interfaces, and Budgets"
    assert ws["questions"][0]["id"] == "A" and ws["answered"] == {}

    await client.post("/api/logbook/entries", headers=IAP, json={
        "kind": "worksheet", "tool": "design", "text": "Dry mass 3.4 kg",
        "worksheet": {"id": "LW-2.4", "q": "A"}, "lang": "en"})
    r = await client.get(f"/api/logbook/worksheets?lang=fr&all=1&context={ctx}", headers=IAP)
    sheets = {w["id"]: w for w in r.json()["worksheets"]}
    assert len(sheets) == 20 and sheets["LW-5.3"]["match"] is False
    assert sheets["LW-2.4"]["answered"]["A"]
    assert sheets["LW-2.4"]["title"].startswith("Architecture")


async def test_gate_context_matches_review_worksheets(client):
    ctx = json.dumps({"tab": "vv", "level": 4, "gate": "pdr"})
    ids = [w["id"] for w in (await client.get(f"/api/logbook/worksheets?context={ctx}")).json()["worksheets"]]
    assert {"LW-4.2", "LW-4.4", "LW-5.4"} <= set(ids)
    assert ids.index("LW-4.2") < ids.index("LW-1.3"), "gate match ranks above a tab-only match"


async def test_worksheet_export_prints_question_text(client):
    await client.post("/api/logbook/entries", headers=IAP, json={
        "kind": "worksheet", "tool": "design", "text": "We pick SSO 550 km.",
        "worksheet": {"id": "LW-2.3", "q": "B"}})
    md = (await client.get("/api/logbook/export?format=md", headers=IAP)).text
    assert "LW-2.3" in md and "Part B: Orbit Trade Matrix" in md and "We pick SSO 550 km." in md


def test_main_app_mounts_the_logbook():
    from spacecdf_server.app import app
    paths = set(app.openapi()["paths"])
    for p in ("/api/logbook", "/api/logbook/entries", "/api/logbook/entries/{entry_id}",
              "/api/logbook/export", "/api/logbook/worksheets"):
        assert p in paths, p


async def test_worksheet_answer_carries_its_question_text(client, lbdir):
    """Like smo-common: title and q_text are stored so any tool's export prints them."""
    r = await client.post("/api/logbook/entries", headers=IAP, json={
        "kind": "worksheet", "tool": "design", "text": "x", "lang": "fr",
        "worksheet": {"id": "LW-2.3", "q": "B"}})
    ws = r.json()["worksheet"]
    assert ws["q_text"].startswith("Partie B") and ws["title"]
    r = await client.patch(f"/api/logbook/entries/{r.json()['id']}", headers=IAP, json={"text": "y", "checked": True})
    assert r.json()["worksheet"]["checked"] is True and r.json()["worksheet"]["q_text"].startswith("Partie B")
