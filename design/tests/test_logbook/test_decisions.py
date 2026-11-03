"""Decision records: store, API, prefill, export, and the shared file format."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from spacecdf_server.logbook import router as lb_router
from spacecdf_server.logbook.store import LogbookError, compacted, fold

IAP = {"X-Goog-Authenticated-User-Email": "accounts.google.com:bob@c2o.live"}
REPO = Path(__file__).resolve().parents[3]

ORBIT = {
    "decision_id": "D-2.3-ORBIT",
    "options": [
        {"name": "SSO 500 km", "values": {"GSD (m)": 4.1, "Lifetime (yr)": 4}, "score": 0.82},
        {"name": "SSO 550 km", "values": {"GSD (m)": 4.5, "Lifetime (yr)": 9}, "score": 0.85, "chosen": True},
        {"name": "ISS 410 km", "score": 0.41},
    ],
    "criteria": [{"name": "GSD", "weight": 0.4, "direction": "lower"}, {"name": "Lifetime", "weight": 0.6}],
    "choice": "SSO 550 km, 97.6°",
    "rationale": "Meets the 5 m GSD with margin and decays in under 25 years.",
    "evidence": [{"label": "Altitude", "before": 500, "after": 550, "unit": "km"}],
    "consequences": "Needs a deorbit plan check at PDR.",
    "margin_impact": "Mass margin unchanged.",
    "capture": "decide:orbit-trade",
}


@pytest.fixture()
async def client(lbdir):
    app = FastAPI()
    app.include_router(lb_router, prefix="/api/logbook")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _post(record, study="s1", **kw):
    return {"kind": "decision", "tool": "design", "text": "-", "record": record,
            "context": {"study_id": study, "tab": "decide", "level": 0}, **kw}


async def test_record_entry_is_self_describing(client):
    r = await client.post("/api/logbook/entries", headers=IAP, json=_post(ORBIT))
    assert r.status_code == 201, r.text
    e = r.json()
    rec = e["record"]
    # catalogue facts filled in by the server
    assert rec["question"].startswith("Which orbit family") and rec["gate"] == "prr"
    assert rec["seat"] == "mission_analyst" and rec["part"] == "LW-2.3/B"
    assert rec["part_title"] == "Part B: Orbit Trade Matrix"
    # the workbook part, as worksheet answers carry it
    assert e["worksheet"] == {"id": "LW-2.3", "q": "B", "section": "decision",
                              "title": "Orbit Selection and Mission Architecture", "q_text": "Part B: Orbit Trade Matrix"}
    assert e["context"]["decision_id"] == "D-2.3-ORBIT" and e["context"]["study_id"] == "s1"
    # text is a complete plain rendering (what every export, ops included, prints)
    t = e["text"]
    for bit in ("Decision D-2.3-ORBIT — Which orbit family", "Choice: SSO 550 km, 97.6°",
                "- SSO 550 km [chosen] (GSD (m) 4.5, Lifetime (yr) 9, score 85%)",
                "Criteria and weights: GSD (weight 0.4, lower is better); Lifetime (weight 0.6)",
                "Rationale: Meets the 5 m GSD", "- Altitude: 500\u00a0km → 550\u00a0km",
                "Consequences and risks: Needs a deorbit", "Margin impact: Mass margin unchanged.",
                "Workbook LW-2.3/B · Gate PRR · Owner Mission analysis & ops"):
        assert bit in t, (bit, t)


async def test_french_record_text(client):
    r = await client.post("/api/logbook/entries", headers=IAP, json=_post(ORBIT, lang="fr"))
    t = r.json()["text"]
    assert "Décision D-2.3-ORBIT — Quelle famille d’orbite" in t
    assert "Choix retenu : SSO 550 km" in t and "[retenue]" in t and "Justification :" in t
    assert r.json()["worksheet"]["q_text"].startswith("Partie B")


async def test_record_needs_choice_or_rationale(client):
    r = await client.post("/api/logbook/entries", headers=IAP,
                          json=_post({"decision_id": "D-2.3-ORBIT", "options": ORBIT["options"]}))
    assert r.status_code == 400 and "choice or the rationale" in r.json()["detail"]


async def test_record_validation_limits(client):
    bad = await client.post("/api/logbook/entries", headers=IAP, json=_post({"decision_id": "", "choice": "x"}))
    assert bad.status_code == 400
    big = {**ORBIT, "options": [{"name": "o" * 200, "summary": "s" * 500, "values": {f"k{i}": "v" * 200 for i in range(12)}}
                                for _ in range(20)]}
    r = await client.post("/api/logbook/entries", headers=IAP, json=_post(big))
    assert r.status_code == 413
    odd = await client.post("/api/logbook/entries", headers=IAP, json=_post(
        {"decision_id": "D-2.3-ORBIT", "choice": "x", "options": [{"name": "a", "score": float("nan") if False else "high"},
                                                                     {"no": "name"}], "evil": {"x": 1}}))
    assert odd.status_code == 201
    rec = odd.json()["record"]
    assert rec["options"] == [{"name": "a"}] and "evil" not in rec


def test_store_refuses_a_record_on_other_kinds(store):
    with pytest.raises(LogbookError):
        store.add("p", {"kind": "thought", "tool": "design", "text": "x", "record": {"decision_id": "D-2.3-ORBIT"}})


async def test_status_per_study_and_due_by_gate(client):
    await client.post("/api/logbook/entries", headers=IAP, json=_post(ORBIT, study="s1"))
    await client.post("/api/logbook/entries", headers=IAP, json=_post(
        {"decision_id": "D-1.4-SPACE", "choice": "Dedicated CubeSat"}, study=None, context={"step": "wizard:alternatives"}))
    await client.post("/api/logbook/entries", headers=IAP, json=_post(
        {"decision_id": "D-2.4-MASS", "choice": "x"}, study="other"))
    body = (await client.get("/api/logbook/decisions?study_id=s1&gate=srr", headers=IAP)).json()
    status = {d["id"]: d["status"] for d in body["decisions"]}
    assert status["D-2.3-ORBIT"] == "recorded"
    assert status["D-1.4-SPACE"] == "recorded", "wizard decisions (no study yet) count for the study"
    assert status["D-2.4-MASS"] == "open", "another study's record does not count"
    due = body["due"]
    assert due["gate"] == "srr" and "D-2.3-ORBIT" in due["recorded"] and "D-2.4-MASS" in due["open"]
    assert not any(d.startswith("D-3.1-ARRAY") for d in due["open"]), "PDR decisions are not due at SRR"
    mcr = (await client.get("/api/logbook/decisions?study_id=s1&gate=mcr&lang=fr", headers=IAP)).json()
    assert mcr["due"]["gate"] == "mdr" and mcr["gates"][0]["label"].startswith("MDR — revue")
    orbit = next(d for d in body["decisions"] if d["id"] == "D-2.3-ORBIT")
    assert orbit["part_title"] == "Part B: Orbit Trade Matrix" and orbit["seat_label"] == "Mission analysis & ops"
    assert len(orbit["entries"]) == 1
    # another person sees nothing of Bob's (private, ruling L1)
    other = (await client.get("/api/logbook/decisions?study_id=s1")).json()
    assert all(d["status"] == "open" for d in other["decisions"])


async def test_edit_replaces_the_record_and_rerenders(client):
    e = (await client.post("/api/logbook/entries", headers=IAP, json=_post(ORBIT))).json()
    r = await client.patch(f"/api/logbook/entries/{e['id']}", headers=IAP,
                           json={"text": "-", "record": {**ORBIT, "choice": "SSO 600 km", "options": []}})
    assert r.status_code == 200, r.text
    e2 = r.json()
    assert e2["record"]["choice"] == "SSO 600 km" and "options" not in e2["record"]
    assert "Choice: SSO 600 km" in e2["text"] and e2["edited"]
    # a record cannot be grafted onto a thought
    t = (await client.post("/api/logbook/entries", headers=IAP,
                           json={"kind": "thought", "tool": "design", "text": "hm"})).json()
    bad = await client.patch(f"/api/logbook/entries/{t['id']}", headers=IAP, json={"text": "x", "record": ORBIT})
    assert bad.status_code == 400


def test_fold_and_compaction_keep_the_record():
    recs = [{"v": 1, "id": "a", "op": "add", "ts": "2026-11-02T10:00:00.000Z", "tool": "design", "kind": "decision",
             "text": "t", "context": {"decision_id": "D-2.3-ORBIT"}, "record": {"v": 1, "decision_id": "D-2.3-ORBIT", "choice": "A"}},
            {"v": 1, "id": "a", "op": "edit", "ts": "2026-11-02T10:05:00.000Z", "text": "t2",
             "record": {"v": 1, "decision_id": "D-2.3-ORBIT", "choice": "B"}}]
    assert fold(recs).entries["a"]["record"]["choice"] == "B"
    again = fold(compacted(recs)).entries["a"]
    assert again["record"]["choice"] == "B" and again["text"] == "t2" and again["edited"]


def _smo_store():
    path = REPO / "sim" / "packages" / "smo-common" / "src" / "smo_common" / "logbook" / "store.py"
    if not path.exists():
        pytest.skip("smo-common not in this checkout")
    spec = importlib.util.spec_from_file_location("_smo_lb_store", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses look the module up
    spec.loader.exec_module(mod)
    return mod


async def test_the_ops_implementation_reads_a_decision_record(client, lbdir):
    """smo-common folds our file: it ignores `record`, keeps the full text, the
    decision id in context and the workbook part, so its export prints it all."""
    await client.post("/api/logbook/entries", headers=IAP, json=_post(ORBIT))
    smo = _smo_store()
    (f,) = list(Path(lbdir).glob("*.jsonl"))
    recs = [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines()]
    folded = smo.LogbookStore.fold(recs)
    (e,) = folded.entries
    assert e["kind"] == "decision" and e.get("record")   # ops keeps it (compaction-safe)
    assert "Choice: SSO 550 km" in e["text"] and "Rationale:" in e["text"]
    assert e["context"]["decision_id"] == "D-2.3-ORBIT"
    assert e["worksheet"]["id"] == "LW-2.3"
    # and its compaction keeps what our status needs
    kept = smo.LogbookStore.fold(smo.LogbookStore._compacted(smo.LogbookStore, recs)).entries[0]
    assert kept["context"]["decision_id"] == "D-2.3-ORBIT"
    # our side still knows the decision is recorded from context alone
    from spacecdf_server.logbook.decisions import recorded
    assert "D-2.3-ORBIT" in recorded([{**kept, "kind": "decision"}], "s1")


# ─── Export ───────────────────────────────────────────────────────────────

async def _book(client):
    await client.post("/api/logbook/entries", headers=IAP, json=_post(ORBIT))
    await client.post("/api/logbook/entries", headers=IAP, json={
        "kind": "worksheet", "tool": "design", "text": "Top three: SSO 500, 550, ISS",
        "worksheet": {"id": "LW-2.3", "q": "B"}, "context": {"study_id": "s1"}})
    await client.post("/api/logbook/entries", headers=IAP, json={
        "kind": "thought", "tool": "design", "text": "Ask the instructor about the drag model", "context": {"study_id": "s1"}})
    await client.post("/api/logbook/entries", headers=IAP, json={
        "kind": "observation", "tool": "mcs", "text": "Battery at 71 %"})


async def test_markdown_export_reads_like_the_workbook(client):
    await _book(client)
    md = (await client.get("/api/logbook/export?format=md&study_id=s1", headers=IAP)).text
    wb, open_, log = md.index("## Workbook"), md.index("## Open decisions"), md.index("## Log")
    assert wb < open_ < log
    sheet = md.index("### Worksheet 2.3 · Orbit Selection and Mission Architecture")
    part = md.index("#### Part B: Orbit Trade Matrix")
    block = md.index("##### Decision D-2.3-ORBIT · Which orbit family, altitude and inclination?")
    assert wb < sheet < part < block < md.index("**Worksheet answers**") < md.index("Top three") < open_
    assert "| **SSO 550 km** | GSD (m) 4.5, Lifetime (yr) 9 | 85 % | chosen |" in md
    assert "**Choice:** SSO 550 km, 97.6°" in md and "- Altitude: 500\u00a0km → 550\u00a0km" in md
    assert "_owner Mission analysis & ops · by PRR · recorded" in md
    # part B's other decision (constellation) is listed as still open under the part
    assert md.index("_Not recorded yet_") < md.index("**D-2.3-CONSTELLATION**") < open_
    # open decisions by gate, with owner seat and workbook place
    tail = md[open_:log]
    assert "### MDR — Mission Definition Review" in tail and "**D-1.4-SPACE**" in tail
    assert "D-2.3-ORBIT" not in tail
    # the free log: chronological, every tool; the decision is not repeated there
    assert "Ask the instructor" in md[log:] and "Battery at 71 %" in md[log:] and "D-2.3-ORBIT" not in md[log:]
    assert "| **Decisions** | 1 recorded" in md


async def test_html_export_has_the_record_table(client):
    await _book(client)
    html = (await client.get("/api/logbook/export?format=html&lang=fr", headers=IAP)).text
    assert '<section class="dr">' in html and '<table class="opts">' in html and "<tr class=chosen>" in html
    assert "Cahier d’exercices" in html and "Fiche 2.3" in html and "Décisions ouvertes" in html
    assert "<script" not in html and "https://" not in html


async def test_one_worksheet_export_does_not_count_as_download(client):
    await _book(client)
    r = await client.get("/api/logbook/export?format=md&worksheet=LW-2.3&study_id=s1&inline=1", headers=IAP)
    assert r.status_code == 200 and r.headers["content-disposition"].startswith("inline;")
    assert "c2o-LW-2.3-" in r.headers["content-disposition"]
    md = r.text
    assert md.startswith("# Worksheet 2.3 · Orbit Selection and Mission Architecture")
    assert "#### Decision D-2.3-ORBIT" in md and "Top three" in md
    assert "Ask the instructor" not in md and "Battery" not in md, "one worksheet: no free log"
    # every part with something in it, in order; the open debris decision sits under part C
    assert md.index("### Part B") < md.index("### Part C: Debris Compliance") < md.index("**D-2.3-DEBRIS**")
    summary = (await client.get("/api/logbook", headers=IAP)).json()
    assert summary["last_download"] is None and summary["unsaved"] == 4
    bad = await client.get("/api/logbook/export?format=md&worksheet=../etc", headers=IAP)
    assert bad.status_code == 400


async def test_json_export_carries_records_and_open_decisions(client):
    await _book(client)
    doc = (await client.get("/api/logbook/export?format=json&study_id=s1", headers=IAP)).json()
    recs = [e for e in doc["entries"] if e.get("record")]
    assert recs and recs[0]["record"]["decision_id"] == "D-2.3-ORBIT"
    assert any(d["id"] == "D-1.4-SPACE" for d in doc["open_decisions"])


# ─── Prefill ──────────────────────────────────────────────────────────────

async def test_prefill_unknown_and_empty(client):
    assert (await client.get("/api/logbook/decisions/D-NOPE/prefill")).status_code == 404
    r = (await client.get("/api/logbook/decisions/D-2.4-MASS/prefill?study_id=none")).json()
    assert r["decision_id"] == "D-2.4-MASS" and r["sources"] == []


async def test_prefill_reads_the_study(client, monkeypatch):
    from spacecdf_common.models.study import MissionRequirements, Study
    from spacecdf_server.routers import elements as el_router
    from spacecdf_server.routers import studies as st_router

    study = Study(id="s9", name="AuroraSat", requirements=MissionRequirements(name="AuroraSat", target_mass_kg=6))
    study.mission_need.problem_statement = "Farmers lack weekly crop-stress maps."
    monkeypatch.setitem(st_router._studies, "s9", study)
    els = {
        "m": {"id": "m", "study_id": "s9", "name": "AuroraSat", "element_type": "mission", "parent_id": None,
              "segment": "space", "quantity": 1, "margin_percent": 20},
        "sc": {"id": "sc", "study_id": "s9", "name": "SC-1", "element_type": "system", "parent_id": "m",
               "segment": "space", "quantity": 1, "margin_percent": 20,
               "performance": {"orbit_altitude_km": 550, "orbit_inclination_deg": 97.6, "orbit_type": "sso"}},
        "rw": {"id": "rw", "study_id": "s9", "name": "RW-400", "element_type": "component", "parent_id": "sc",
               "segment": "space", "subsystem_domain": "aocs", "mass_kg": 0.4, "power_avg_w": 1.5, "trl": 9,
               "quantity": 1, "margin_percent": 10, "manufacturer": "Acme"},
    }
    for k, v in els.items():
        monkeypatch.setitem(el_router._elements, k, v)

    problem = (await client.get("/api/logbook/decisions/D-1.4-PROBLEM/prefill?study_id=s9")).json()
    assert problem["choice"] == "Farmers lack weekly crop-stress maps." and problem["sources"] == ["mission_need"]

    orbit = (await client.get("/api/logbook/decisions/D-2.3-ORBIT/prefill?study_id=s9")).json()
    assert orbit["choice"] == "SSO 550 km, 97.6°"
    labels = {e["label"]: e for e in orbit["evidence"]}
    assert labels["Altitude"]["value"] == 550 and labels["Altitude"]["unit"] == "km"
    assert "selected_orbit" in orbit["sources"] and "study_requirements" in orbit["sources"]

    mass = (await client.get("/api/logbook/decisions/D-2.4-MASS/prefill?study_id=s9&lang=fr")).json()
    ev = {e["label"]: e["value"] for e in mass["evidence"]}
    assert ev["Masse : nominal"] == pytest.approx(0.4)
    assert "aucune allocation" in mass["margin_impact"]

    equip = (await client.get("/api/logbook/decisions/D-3.4-EQUIPMENT/prefill?study_id=s9")).json()
    assert equip["options"][0]["name"] == "RW-400" and equip["options"][0]["chosen"] is True
    assert equip["options"][0]["values"]["TRL"] == 9
