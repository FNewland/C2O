"""Wave 1, agent D (decide, mission and ConOps) acceptance on the Northern Fire and Ice fixture.

W1.04 link-budget presets from the study and the seat guard; W1.06 mission-need editor fields
and the MRD; W6 multiple trade studies; W4.04 named link cases; W4.08 gate review record; W7.01
editable phases; W7.02 ConOps built from the study; the Propulsion seat for a disposal device.
Every number is checked against NUMBERS.yaml / trades.yaml, never retyped.
"""
from __future__ import annotations

import io

import pytest
from docx import Document

from tests.fixtures.nfi import load, seed_nfi
from tests.fixtures.nfi.seed import MDR_RIDS, TRADE_CHOICE


def _text(blob: bytes) -> str:
    d = Document(io.BytesIO(blob))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.extend(c.text for c in row.cells)
    return "\n".join(parts)


@pytest.fixture()
async def s3(client):
    return await seed_nfi(client, "S3")


# ─── W6 trade studies ────────────────────────────────────────────────────────

async def test_every_trade_is_kept_with_its_weights_links_and_decision(client, s3):
    data = load("trades")
    items = (await client.get(f"/api/studies/{s3.study_id}/trades")).json()["items"]
    assert [i["id"] for i in items] == [t["id"] for t in data["trades"]]
    st = (await client.get(f"/api/studies/{s3.study_id}")).json()
    records = {r["id"]: r for r in st["decision_records"]}
    for it, t in zip(items, data["trades"]):
        exp = data["pairwise_inputs"][t["id"]]
        ev = it["evaluation"]
        for c, w in exp["weights_from_pairwise"].items():
            assert ev["weights"][c] == pytest.approx(w, abs=1e-4), (t["id"], c)
        tot = {x["option"]: x["weighted"] for x in ev["totals"]}
        for o, v in exp["totals_with_these_weights"].items():
            assert tot[o] == pytest.approx(v, abs=1e-4), (t["id"], o)
        assert it["state"]["comparisons"] and it["state"]["weights_mode"] == "pairwise"
        assert it["state"]["status"] == "decided"
        assert it["state"]["decision"]["selected"] == t["options"][TRADE_CHOICE[t["id"]]]
        links = it["state"]["links"]
        assert links["decision_record"] == t["decision_record"]
        assert links["requirements"] and all(c in s3.requirements for c in links["requirements"])
        assert links["elements"], t["id"]
        rec = records[t["decision_record"]]
        assert rec["selected_alternative_id"] == it["state"]["decision"]["selected"]
        assert rec["related_requirement_ids"] == links["requirements"]
        assert len(ev["sensitivity"]) == len(t["criteria"])
    # the rows that cite a trade are linked to it
    t07 = next(i for i in items if i["id"] == "T-07")
    assert "OBD-SEC-01" in t07["state"]["links"]["requirements"]
    # every trade is in the decisions section and the trade-off report
    sx = (await client.get(f"/api/studies/{s3.study_id}/export-context?sections=trades,decisions")).json()
    assert sx["trades"]["counts"] == {"total": len(data["trades"]), "decided": len(data["trades"])}
    r = await client.post(f"/api/studies/{s3.study_id}/trades/report")
    assert r.status_code == 200
    text = _text(r.content)
    for t in data["trades"]:
        assert t["id"] in text and t["decision_record"] in text
    assert "35 %" in text and "+0.55" in text     # T-01 weight and the 1610 nm total


async def test_trade_edit_conflict_and_legacy_pugh(client, study_obj):
    sid = study_obj.id
    # the old single Pugh record of the Decide tab is T-01
    r = await client.put(f"/api/studies/{sid}/trades/pugh", json={"state": {
        "criteria": [{"id": "c1", "name": "Mass", "weight": 3}], "options": ["A", "B"], "datum": "A",
        "scores": {"B": {"c1": 1}}}})
    assert r.status_code == 200 and r.json()["id"] == "T-01"
    items = (await client.get(f"/api/studies/{sid}/trades")).json()["items"]
    assert [i["id"] for i in items] == ["T-01"] and items[0]["state"]["scores"] == {"B": {"Mass": 1.0}}
    # a second trade; a stale save is refused; a decision keeps the trade
    new = (await client.post(f"/api/studies/{sid}/trades", json={"state": {
        "title": "Battery", "criteria": ["Mass", "Energy"], "options": ["X", "Y"],
        "comparisons": {"Mass|Energy": 1}, "scores": {"Y": {"Mass": 1, "Energy": -2}},
        "thresholds": {"Energy": -1}}})).json()
    assert new["id"] == "T-02"
    ev = new["evaluation"]
    assert ev["weights"] == {"Mass": 1.0, "Energy": 0.0}      # pairwise row sums (pairwise.ts)
    assert ev["totals"][1]["below_threshold"] == ["Energy"] and ev["winner"] == "X"
    ok = await client.put(f"/api/studies/{sid}/trades/T-02", json={"state": {"title": "Battery pack"}, "version": 1})
    assert ok.status_code == 200 and ok.json()["state"]["criteria"] == ["Mass", "Energy"]
    stale = await client.put(f"/api/studies/{sid}/trades/T-02", json={"state": {"title": "x"}, "version": 1})
    assert stale.status_code == 409
    d = await client.post(f"/api/studies/{sid}/trades/T-02/decision", json={"selected": "Y", "rationale": "capacity"})
    assert d.status_code == 200 and d.json()["decision_record"]["id"] == "D-T-02"
    assert (await client.post(f"/api/studies/{sid}/trades/T-02/decision", json={"selected": "Z"})).status_code == 422
    assert len((await client.get(f"/api/studies/{sid}/trades")).json()["items"]) == 2


# ─── W4.04 link cases, W1.04 presets ─────────────────────────────────────────

async def test_link_cases_reproduce_the_numbers_and_set_the_design_case(client):
    n = load("NUMBERS")
    s = await seed_nfi(client, "S2")
    res = (await client.get(f"/api/studies/{s.study_id}/link-budgets")).json()
    cases = {c["name"]: c for c in res["items"]}
    assert len(cases) == 8
    m = n["links"]["downlink_margin_db_10deg_rs"]
    assert cases["DL Ottawa 1 W urban (700 K)"]["margin_db"] == pytest.approx(m["urban_700K_1W"], abs=0.15)
    for site in ("Yellowknife", "Iqaluit", "Inuvik"):
        assert cases[f"DL {site} 1 W rural (300 K)"]["margin_db"] == pytest.approx(m["rural_300K_1W"], abs=0.15)
    assert cases["DL Ottawa 2 W urban (700 K)"]["margin_db"] == pytest.approx(m["urban_700K_2W"], abs=0.15)
    assert cases["DL Ottawa 1 W urban uncoded"]["margin_db"] == pytest.approx(m["uncoded_urban_1W"], abs=0.15)
    up = n["links"]["uplink_margin_db_10deg_9k6"]
    assert cases["UL 25 W, spacecraft 600 K"]["margin_db"] == pytest.approx(up["25W_600K"], abs=0.15)
    assert cases["UL 25 W, spacecraft 1500 K"]["margin_db"] == pytest.approx(up["25W_1500K"], abs=0.15)
    dl = cases["DL Ottawa 1 W urban (700 K)"]["results"]
    assert dl["slant_range_km"] == pytest.approx(n["links"]["slant_range_km"]["el_10deg"], abs=1)
    assert dl["fspl_db"] == pytest.approx(n["links"]["fspl_db"]["at_401p5MHz_10deg"], abs=0.1)
    assert dl["ebn0_db"] == pytest.approx(n["links"]["downlink_ebn0_db_10deg"]["1W_700K"], abs=0.15)
    # the design cases are applied to requirements.link (what the analyses read)
    link = res["design_case"]
    assert link["downlink_frequency_mhz"] == 401.5 and link["band"] == "UHF"
    assert link["downlink_rate_bps"] == n["links"]["downlink"]["rate_kbps"] * 1000
    assert link["uplink_frequency_mhz"] == 450.0 and link["uplink_rate_bps"] == n["links"]["uplink"]["rate_kbps"] * 1000
    assert sum(1 for c in res["items"] if c["is_design_case"]) == 2
    # W1.04: the tool opens on the study's link; the uplink is not the S-band preset
    assert res["start"]["downlink"]["frequency_mhz"] == 401.5
    assert res["start"]["uplink"]["frequency_mhz"] == 450.0 and res["start"]["uplink"]["data_rate_bps"] == 9600.0
    # the export collector carries the cases (master budget, ISED brief)
    sx = (await client.get(f"/api/studies/{s.study_id}/export-context?sections=links")).json()["links"]
    assert len(sx["items"]) == 8 and len(sx["by_direction"]["uplink"]) == 2


async def test_uhf_presets_and_case_edit(client, study_obj):
    pre = (await client.get("/api/link-budgets/presets")).json()["bands"]
    assert pre["UHF"]["uplink"]["frequency_mhz"] == 450.0 and pre["UHF"]["uplink"]["data_rate_bps"] == 9600.0
    assert pre["UHF"]["downlink"]["frequency_mhz"] == 401.5 and pre["UHF"]["downlink"]["rx_antenna_gain_dbi"] == 15.0
    assert pre["S"]["uplink"]["frequency_mhz"] == 2050.0
    sid = study_obj.id
    r = await client.patch(f"/api/studies/{sid}/mission", json={"link": {"band": "UHF", "downlink_frequency_mhz": 401.5}})
    assert r.status_code == 200
    start = (await client.get(f"/api/studies/{sid}/link-budgets")).json()["start"]
    assert start["uplink"]["frequency_mhz"] == 450.0 and start["uplink"]["band"] == "UHF"
    c = (await client.post(f"/api/studies/{sid}/link-budgets", json={"direction": "uplink", "station": "GS"})).json()
    assert c["frequency_mhz"] == 450.0 and c["margin_db"] is not None
    c2 = (await client.patch(f"/api/studies/{sid}/link-budgets/{c['id']}", json={"tx_power_w": 50})).json()
    assert c2["margin_db"] == pytest.approx(c["margin_db"] + 3.01, abs=0.02)
    assert (await client.delete(f"/api/studies/{sid}/link-budgets/{c['id']}")).status_code == 200


# ─── seats: Comms Apply, Propulsion for the disposal device ─────────────────

INSTRUCTOR = "prof@c2o.live"


def _iap(email: str, name: str) -> dict:
    return {"X-Goog-Authenticated-User-Email": f"accounts.google.com:{email}", "X-C2O-Name": name}


@pytest.fixture()
def _seats(monkeypatch):
    from spacecdf_server.seats import store
    from spacecdf_server.seats.instructor import invalidate_gate_cache
    monkeypatch.setenv("SPACECDF_INSTRUCTORS", INSTRUCTOR)
    monkeypatch.delenv("SMO_INSTRUCTORS", raising=False)
    store.reset_memory()
    invalidate_gate_cache()
    yield
    store.reset_memory()


async def test_propulsion_seat_owns_the_sail_and_comms_apply_is_direct(client, _seats):
    s = await seed_nfi(client, "S2")
    sid = s.study_id
    prof, comms = _iap(INSTRUCTOR, "Prof"), _iap("comms@c2o.live", "Comms")
    r = await client.post(f"/api/studies/{sid}/team/preset", json={"team_size": "9"}, headers=prof)
    assert r.status_code == 200
    team = (await client.get(f"/api/studies/{sid}/team", headers=prof)).json()
    seats = {x["id"] for x in team["seats"]}
    assert "propulsion_engineer" in seats, "a study with a drag sail and no delta-V needs the Propulsion seat"
    owners = (await client.get(f"/api/studies/{sid}/team/ownership", headers=prof)).json()["owners"]
    sail = next(e for n, e in s.elements.items() if "drag sail" in n.lower() and e["element_type"] == "component")
    assert owners[sail["id"]] == "propulsion_engineer"
    r = await client.post(f"/api/studies/{sid}/team/claim", json={"seats": ["comms_engineer"]}, headers=comms)
    assert r.status_code == 200
    r = await client.patch(f"/api/studies/{sid}/mission", headers=comms,
                           json={"link": {"uplink_frequency_mhz": 450.0, "uplink_rate_bps": 9600, "source": "link_budget_tool"}})
    assert r.status_code == 200 and "pending_change" not in r.json()
    assert r.json()["requirements"]["link"]["uplink_frequency_mhz"] == 450.0
    pend = (await client.get(f"/api/studies/{sid}/team/pending", headers=prof)).json()
    assert not (pend.get("items") if isinstance(pend, dict) else pend)


# ─── W1.06 mission need and MRD, W4.08 review record, profile with FRR ──────

async def test_mission_need_fields_close_mdr_ec_06_and_reach_the_mrd(client):
    s = await seed_nfi(client, "S0")
    st = (await client.get(f"/api/studies/{s.study_id}")).json()
    need = st["mission_need"]
    assert need["conops_summary"] and len(need["success_criteria"]) >= 3
    assert any(a["type"] != "space_dedicated" for a in need["alternatives_considered"])
    g = (await client.get(f"/api/studies/{s.study_id}/rules/gates/mdr")).json()
    by = {c["id"]: c for c in g["criteria"]}
    assert by["MDR-EC-06"]["status"] == "pass" and by["MDR-EC-04"]["status"] == "pass"
    from spacecdf_server.services.docx.mrd import generate_mrd_docx, mrd_kwargs_from_export
    from spacecdf_server.services.export_context import collect
    sx = await collect(s.study_id, sections=["need", "mission", "requirements"])
    text = _text(generate_mrd_docx(**mrd_kwargs_from_export(sx)))
    n = load("NUMBERS")["disposal"]["rules"]
    assert need["conops_summary"][:60] in text
    assert all(c[:50] in text for c in need["success_criteria"])
    assert f"Apogee ≤ {n['apogee_without_propulsion_max_km']} km" in text
    assert f"≤ {n['disposal_max_y']} years" in text and f"≥ {n['probability_min']}" in text
    assert f"< {n['collision_probability_max']}" in text


async def test_profile_has_frr_and_mdr_review_record(client, s3, monkeypatch):
    sid = s3.study_id
    ov = (await client.get(f"/api/studies/{sid}/gates")).json()
    assert [g["short"] for g in ov["gates"]] == ["MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR"]
    rids = (await client.get(f"/api/studies/{sid}/rids?gate=mdr")).json()["items"]
    assert len(rids) == len(MDR_RIDS) == 3 and {r["number"] for r in rids} == {"RID-MDR-01", "ACT-MDR-01", "ACT-MDR-02"}
    # FRR is not ready: the MDR actions are open and the board evidence is missing (named)
    frr = (await client.get(f"/api/studies/{sid}/rules/gates/frr")).json()
    by = {c["id"]: c for c in frr["criteria"]}
    assert frr["ready"] is False and by["FRR-RR-01"]["status"] == "fail" and "ACT-MDR-01" in by["FRR-RR-01"]["evidence_found"]
    assert by["FRR-RR-03"]["status"] == "manual" and "Licences" in by["FRR-RR-03"]["evidence_found"]
    # pass MDR (the seed lacks a design-loop run, so readiness is forced as in test_project_file)
    from spacecdf_server.routers import gates as gates_router
    real = gates_router._evaluate
    monkeypatch.setattr(gates_router, "_evaluate", lambda ctx, pg: {**real(ctx, pg), "ready": True})
    for gate in ("mdr", "prr"):
        for action in ("start", "pass"):
            assert (await client.post(f"/api/studies/{sid}/gates/{gate}/review", json={"action": action})).status_code == 200
        if gate == "mdr":
            await client.patch(f"/api/studies/{sid}/mission", json={"mission_need": {"conops_summary": "changed"}})
    monkeypatch.setattr(gates_router, "_evaluate", real)
    diff = (await client.get(f"/api/studies/{sid}/gate-baselines/diff?gate=prr")).json()
    assert diff["a"]["gate"] == "mdr" and "conops_summary" in diff["changes"]["mission_need"]
    r = await client.post(f"/api/studies/{sid}/gates/mdr/report")
    assert r.status_code == 200
    text = _text(r.content)
    assert "GO with actions" in text and all(x["number"] in text for x in rids)
    assert "MDR-EC-06" in text and "MDR-EC-01" in text
    # closing every earlier RID clears FRR-RR-01
    for x in rids:
        assert (await client.patch(f"/api/studies/{sid}/rids/{x['id']}", json={"status": "closed",
                                                                               "closure_evidence": "done"})).status_code == 200
    frr = (await client.get(f"/api/studies/{sid}/rules/gates/frr")).json()
    assert next(c for c in frr["criteria"] if c["id"] == "FRR-RR-01")["status"] == "pass"


# ─── W7 ConOps phases and document ───────────────────────────────────────────

async def test_conops_from_the_modes_tab(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    md = load("modes")
    view = (await client.get(f"/api/studies/{sid}/conops")).json()
    flight = [p for p in md["phases"] if not p[0].lower().startswith("pre-")]
    assert [p["name"] for p in view["phases"]] == [p[0] for p in flight]
    assert view["phases"][0]["duration_days"] == 7 and view["phases_edited"] is True
    assert sum(p["duration_days"] for p in view["phases"][:3]) == 90       # payload commissioning ends on day 90
    assert len(view["modes"]) == len(md["modes"])
    assert len(view["transitions"]) >= len(md["transitions_added"])
    assert view["data_flow"]["status"] == "open" and view["data_flow"]["downlink_rate_bps"] == 38400
    assert view["flight_rules"] and view["flight_rules"][0]["id"] == "FR-01"
    # W7.01: a mission-definition change that regenerates the auto ConOps keeps the phases
    r = await client.patch(f"/api/studies/{sid}/mission", json={"design_lifetime_years": 3.5})
    assert r.status_code == 200
    again = (await client.get(f"/api/studies/{sid}/conops/phases")).json()
    assert [p["name"] for p in again["phases"]] == [p["name"] for p in view["phases"]]
    r = await client.post(f"/api/studies/{sid}/conops/document")
    assert r.status_code == 200
    text = _text(r.content)
    for m in view["modes"]:
        assert m["name"] in text
    for bad in ("Safe Mode 19.0 W", "Downlink 30.0 W", "Nominal 876"):
        assert bad not in text
    assert "FR-01" in text and "Open item" in text and "Sail deploy" in text
    assert "MIS-DIS-01" in text                                               # EOL operations cite the disposal rows
    fr = _text((await client.post(f"/api/studies/{sid}/conops/document?lang=fr")).content)
    assert "Phases de la mission" in fr and "Règles de vol" in fr
