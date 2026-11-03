"""WP0 (Nov 2026) — the 12 broken basics found by the BorealWatch-1 walkthrough.

One regression test per defect that the backend can see (the frontend-only ones are in
tests/test_frontend_logic.py). Numbers follow the WP0 list of the redesign (§6).
"""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element

# What the mission wizard posts after the Nov 2026 fix: every ranked alternative under
# ``alternatives_considered``, ``type`` = the mission-trade category.
TRADE_ALTERNATIVES = [
    {"id": n, "name": n, "type": cat, "description": "", "decision": "rejected"}
    for n, cat in [("Planet SuperDove", "commercial_tasking"), ("Sentinel-2", "existing_satellite"),
                   ("Landsat 9", "existing_satellite"), ("Aerial patrol", "aerial"),
                   ("Lookout towers", "ground"), ("New dedicated CubeSat", "new_satellite")]
]
TRADE_ALTERNATIVES[-1]["decision"] = "selected"

WIZARD_NEED = {
    "problem_statement": "Wildfires in the boreal forest are detected too late.",
    "operational_context": "48–62° N, fire season May–September.",
    "stakeholders": [{"id": "1", "name": "CIFFC", "role": "user", "needs": ["early alerts"],
                      "constraints": [], "priority": "high"}],
    "objectives": [{"id": "1", "text": "Detect active fires", "priority": "primary", "type": "performance",
                    "measurable_criterion": "Alert within 30 min of overpass", "status": "draft"}],
    "alternatives_considered": TRADE_ALTERNATIVES,
    "selected_alternative_id": "New dedicated CubeSat",
    "selection_rationale": "Thermal band and latency no existing service provides.",
    "conops_summary": "",
}
WIZARD_REQUIREMENTS = {
    "name": "BorealWatch-1", "mission_type": "earth_observation", "spacecraft_class": "nano",
    "orbit": {"orbit_type": "sso", "altitude_km": 500, "inclination_deg": 97.4, "mission_duration_years": 3},
    "payloads": [{"name": "Payload", "mass_kg": 1, "power_w": 10, "data_rate_mbps": 10,
                  "pointing_accuracy_deg": 1, "duty_cycle_percent": 25}],
    "design_lifetime_years": 3, "target_mass_kg": 6, "target_cost_meur": 2,
    "ground_stations": ["KSAT Svalbard"],
}


async def _wizard_study(client) -> str:
    r = await client.post("/api/studies/", json={"requirements": WIZARD_REQUIREMENTS, "mission_need": WIZARD_NEED})
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ── 1. alternatives vs alternatives_considered, and the top-5 slice ──────────

async def test_wp0_1_alternatives_are_stored_all_of_them(client):
    sid = await _wizard_study(client)
    need = (await client.get(f"/api/studies/{sid}")).json()["mission_need"]
    alts = need["alternatives_considered"]
    assert len(alts) == 6, "every ranked alternative is kept (the chosen one was #6)"
    assert {a["type"] for a in alts} >= {"space_existing", "aerial_aircraft", "ground_network", "space_dedicated"}
    assert need["selected_alternative_id"] in {a["id"] for a in alts}


async def test_wp0_1_old_alternatives_key_is_still_accepted(client):
    need = {**WIZARD_NEED, "alternatives": WIZARD_NEED["alternatives_considered"]}
    need.pop("alternatives_considered")
    r = await client.post("/api/studies/", json={"requirements": WIZARD_REQUIREMENTS, "mission_need": need})
    sid = r.json()["id"]
    assert r.json()["mission_need_populated"] is True
    assert len((await client.get(f"/api/studies/{sid}")).json()["mission_need"]["alternatives_considered"]) == 6


# ── 2. MDR evaluated on client missionNeed / "Problem statement is empty" ────

async def test_wp0_2_mdr_checklist_reads_the_stored_study(client):
    sid = await _wizard_study(client)
    g = (await client.get(f"/api/studies/{sid}/rules/gates/mdr")).json()
    by = {c["id"]: c for c in g["criteria"]}
    for cid in ("MDR-EC-01", "MDR-EC-02", "MDR-EC-03", "MDR-EC-04", "MDR-EC-05"):
        assert by[cid]["status"] == "pass", (cid, by[cid]["evidence_found"])
    assert by["MDR-EC-01"]["evidence_found"] == "Problem statement defined"
    # the legacy POST route ignores a client body that would empty the need
    r = await client.post(f"/api/ecss/gate-evaluate/{sid}/mcr", json={"mission_need": {}})
    assert {c["id"]: c for c in r.json()["criteria"]}["MDR-EC-01"]["status"] == "pass"


# ── 3. "Run the design loop first" reads client parameters ────────────────────

async def test_wp0_3_gate_reads_the_server_design_run(client):
    sid = await _wizard_study(client)
    before = {c["id"]: c for c in (await client.get(f"/api/studies/{sid}/rules/gates/mdr")).json()["criteria"]}
    assert before["MDR-EC-07"]["status"] == "not_evaluated"
    r = await client.post(f"/api/design/{sid}/run", json={})
    assert r.status_code == 200, r.text
    after = {c["id"]: c for c in (await client.get(f"/api/studies/{sid}/rules/gates/mdr")).json()["criteria"]}
    for cid in ("MDR-EC-07", "MDR-EC-08", "MDR-EC-09"):   # Tier 2 outputs (after convergence) included
        assert after[cid]["status"] in ("pass", "fail"), (cid, after[cid]["evidence_found"])
    g = (await client.get(f"/api/studies/{sid}/rules/gates/mdr")).json()
    assert g["ready"] and g["state"] == "ready", "a complete need + a design run: the MDR is ready for review"


async def test_wp0_3_design_params_fall_back_to_the_last_recorded_run(client, study_obj, monkeypatch):
    """After a restart the in-memory iterations are gone: the last design-loop run's series is used."""
    from spacecdf_server.routers import gates
    from spacecdf_server.db import analysis_repo

    async def fake_last_run(study_id, analysis, option_id):
        return {"id": "r1", "series_ref": "analysis/r1.json"}
    monkeypatch.setattr(analysis_repo, "get_last_run", fake_last_run)
    monkeypatch.setattr("spacecdf_server.services.analysis_results.load_series",
                        lambda ref: {"parameters": {"systems.mass_margin_percent": {"value": 12.0}}})
    params = await gates.design_params(study_obj.id, study_obj)
    assert params == {"systems.mass_margin_percent": 12.0}


# ── 4 (backend half). Run Analysis now runs the study's own loop ─────────────

async def test_wp0_4_design_run_persists_the_study(client, monkeypatch):
    sid = await _wizard_study(client)
    saved = []

    async def spy(study):
        saved.append(len(study.iterations))
    monkeypatch.setattr("spacecdf_server.db.study_repo.db_save_study", spy)
    r = await client.post(f"/api/design/{sid}/run", json={})
    assert r.status_code == 200
    assert saved and saved[-1] >= 1, "the run's iterations are written through to the DB"


# ── 7. Example load drops elements ────────────────────────────────────────────

async def test_wp0_7_example_loads_with_its_element_tree(client):
    examples = (await client.get("/api/lifecycle/example-missions")).json()["missions"]
    r = await client.post(f"/api/lifecycle/example-missions/{examples[0]['id']}/load")
    assert r.status_code == 200, r.text
    body = r.json()
    els = (await client.get(f"/api/studies/{body['id']}/elements")).json()
    types = [e["element_type"] for e in els]
    assert types.count("mission") == 1 and types.count("segment") == 4 and types.count("system") == 1
    assert body["components"] > 0 and types.count("component") == body["components"]
    assert all(e.get("kb_component_id") for e in els if e["element_type"] == "component")
    # the example's design result is the study's last iteration (gates can read it)
    study = (await client.get(f"/api/studies/{body['id']}")).json()
    assert study["iterations"] and study["iterations"][-1]["parameter_snapshot"]
    prr = {c["id"]: c for c in (await client.get(f"/api/studies/{body['id']}/rules/gates/prr")).json()["criteria"]}
    assert prr["PRR-EC-04"]["status"] == "pass", prr["PRR-EC-04"]["evidence_found"]
    assert (await client.post("/api/lifecycle/example-missions/nope/load")).status_code == 404


# ── 9. Risk register and Pugh in localStorage → server per study ──────────────

async def test_wp0_9_risk_register_is_per_study_on_the_server(client, study_obj):
    sid = study_obj.id
    r = await client.post(f"/api/studies/{sid}/risks", json={"description": "Battery cell failure",
                                                             "likelihood": 2, "consequence": 5})
    assert r.status_code == 200 and r.json()["id"] == "RSK-001" and r.json()["rpn"] == 10
    r = await client.patch(f"/api/studies/{sid}/risks/RSK-001", json={"likelihood": 4, "status": "mitigating"})
    assert r.json()["rpn"] == 20 and r.json()["status"] == "mitigating"
    assert len((await client.get(f"/api/studies/{sid}/risks")).json()) == 1
    # another study does not see it
    from spacecdf_common.models.study import Study
    from spacecdf_server.routers.studies import get_study_store
    get_study_store()["other"] = Study(id="other", name="Other")
    assert (await client.get("/api/studies/other/risks")).json() == []
    # the PRR risk criterion now reads it
    prr = {c["id"]: c for c in (await client.get(f"/api/studies/{sid}/rules/gates/prr")).json()["criteria"]}
    assert prr["PRR-EC-10"]["status"] == "pass"
    assert (await client.delete(f"/api/studies/{sid}/risks/RSK-001")).status_code == 200
    assert (await client.delete(f"/api/studies/{sid}/risks/RSK-001")).status_code == 404


async def test_wp0_9_old_browser_register_is_imported_once(client, study_obj):
    sid = study_obj.id
    legacy = [{"id": "RSK-001", "description": "Late launch", "category": "Schedule", "likelihood": 3,
               "consequence": 3, "rpn": 9, "mitigation": "", "owner": "Ava", "status": "open"},
              {"id": "RSK-002", "description": "", "likelihood": 1, "consequence": 1}]   # empty: dropped
    r = (await client.post(f"/api/studies/{sid}/risks/import", json={"risks": legacy})).json()
    assert r["imported"] == 1
    again = (await client.post(f"/api/studies/{sid}/risks/import", json={"risks": legacy})).json()
    assert again["imported"] == 0, "only_if_empty: a second browser does not duplicate it"


async def test_wp0_9_pugh_trade_is_per_study_with_versions(client, study_obj):
    sid = study_obj.id
    assert (await client.get(f"/api/studies/{sid}/trades/pugh")).json() == {"state": None, "version": 0}
    state = {"criteria": ["Mass", "Cost"], "options": ["A", "B"], "datum": 0, "scores": {"B": {"Mass": 1}},
             "comparisons": {"Mass|Cost": 1}}
    r = await client.put(f"/api/studies/{sid}/trades/pugh", json={"state": state, "version": 0})
    assert r.status_code == 200 and r.json()["version"] == 1
    stale = await client.put(f"/api/studies/{sid}/trades/pugh", json={"state": state, "version": 0})
    assert stale.status_code == 409, "a stale editor cannot overwrite a teammate's edit"
    assert (await client.get(f"/api/studies/{sid}/trades/pugh")).json()["state"]["scores"] == {"B": {"Mass": 1}}
    assert (await client.get(f"/api/studies/{sid}/trades/other")).status_code == 404


# ── 10. Presence keyed by name → by identity ──────────────────────────────────

def test_wp0_10_presence_is_keyed_by_identity_not_name():
    from fastapi.testclient import TestClient
    from spacecdf_server.app import app

    c = TestClient(app)
    with c.websocket_connect("/ws/study/presence-test?name=Ben%20(Power)&client_id=browser-a") as a:
        assert a.receive_json()["type"] == "welcome"
        assert len(a.receive_json()["users"]) == 1
        a.receive_json()   # locks_state
        with c.websocket_connect("/ws/study/presence-test?name=Ben%20(Power)&client_id=browser-b") as b:
            you = b.receive_json()["you"]
            users = b.receive_json()["users"]
            assert len(users) == 2, "two people with the same display name stay distinct"
            assert {u["name"] for u in users} == {"Ben (Power)"} and you["id"] == "client:browser-b"
            b.receive_json()   # locks_state
            assert len(a.receive_json()["users"]) == 2
        # the duplicate left: the first Ben is still listed for everyone
        users = a.receive_json()["users"]
        assert [u["id"] for u in users] == ["client:browser-a"]


def test_wp0_10_iap_identity_wins_and_locks_follow_identity():
    from fastapi.testclient import TestClient
    from spacecdf_server.app import app

    c = TestClient(app)
    hdr = {"x-goog-authenticated-user-email": "accounts.google.com:ava@example.org"}
    with c.websocket_connect("/ws/study/lock-test?name=Ava&client_id=x", headers=hdr) as a:
        assert a.receive_json()["you"]["id"] == "iap:ava@example.org"
        a.receive_json(); a.receive_json()
        with c.websocket_connect("/ws/study/lock-test?name=Ava&client_id=y") as b:   # same name, other person
            b.receive_json(); b.receive_json(); b.receive_json(); a.receive_json()
            a.send_json({"type": "lock_request", "element_id": "e1"})
            assert a.receive_json()["held_by_id"] == "iap:ava@example.org"
            b.receive_json()
            b.send_json({"type": "lock_request", "element_id": "e1"})
            denied = b.receive_json()
            assert denied["type"] == "lock_denied", "the same display name does not take someone else's lock"


# ── 11. /api/positions/answers shadowed by /{position_id} ─────────────────────

async def test_wp0_11_positions_answers_route_is_reachable(client):
    r = await client.post("/api/positions/answers", json={"question_id": "q1", "position_id": "power_engineer",
                                                          "text": "77 Wh"})
    assert r.status_code == 200
    r = await client.get("/api/positions/answers")
    assert r.status_code == 200 and any(a["question_id"] == "q1" for a in r.json()["answers"])


# ── 12. SEDTI branding → C2O ──────────────────────────────────────────────────

def test_wp0_12_exports_carry_c2o_not_a_wrong_sedti_expansion():
    from spacecdf_server.services.branding import BRANDING
    texts = [BRANDING.department, BRANDING.footer_left, BRANDING.footer_brand, BRANDING.publisher]
    assert all("C2O" in t for t in texts)
    assert not any("SEDTI" in t or "Space Exploration" in t for t in texts)


@pytest.mark.parametrize("module", [
    "spacecdf_server.services.docx_generator", "spacecdf_server.services.branding",
    "spacecdf_agents.exporters.docs.theme", "spacecdf_agents.exporters.docs.generator",
    "spacecdf_agents.exporters.docs.docx_generator",
])
def test_wp0_12_no_sedti_left_in_export_code(module):
    import importlib
    import inspect
    src = inspect.getsource(importlib.import_module(module))
    assert "Space Exploration & Design Technology Initiative" not in src.replace("said \"SEDTI — Space Exploration & Design Technology Initiative\"", "")
    assert "uOttawa SEDTI" not in src


# ── Also: unrelated new studies are not hurt by an unknown element ────────────

async def test_new_gate_inputs_work_without_a_mission_need(client, study_obj):
    await make_element(client, study_obj.id, "EPS", "subsystem")
    g = (await client.get(f"/api/studies/{study_obj.id}/rules/gates/mdr")).json()
    assert g["state"] == "not_ready" and g["criteria"][0]["id"] == "MDR-EC-01"
