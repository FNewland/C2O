"""Gate review API (author ruling Q23): /api/ecss/gate-evaluate/{study}/{gate}."""
from __future__ import annotations

from tests.test_api.conftest import make_element, make_requirement


async def test_gates_listing(client):
    r = await client.get("/api/ecss/gates")
    assert r.status_code == 200
    assert [g["gate"] for g in r.json()][:3] == ["MCR", "SRR", "PDR"]


async def test_get_accepts_gate_names(client, study_obj, study):
    for gate, phase in (("mcr", "pre_phase_a"), ("srr", "phase_a"), ("pdr", "phase_b1")):
        r = await client.get(f"/api/ecss/gate-evaluate/{study}/{gate}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["phase"] == phase and data["found"] and data["criteria"]
        assert data["study_found"] is True


async def test_unknown_gate_is_404(client, study_obj, study):
    r = await client.get(f"/api/ecss/gate-evaluate/{study}/xyz")
    assert r.status_code == 404


async def test_post_uses_client_state(client, study_obj, study):
    eps = await make_element(client, study, "EPS", "subsystem")
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "Battery", "element_type": "component", "parent_id": eps["id"]})
    assert r.status_code == 200, r.text
    await make_requirement(client, study, "R-GATE-1", code="SYS-001",
                           threshold_param_path="systems.mass_margin_percent",
                           threshold_op=">=", threshold_value="10", verification_method="A")

    body = {"parameters": {"systems.mass_margin_percent": {"value": 14},
                           "systems.power_margin_percent": 11,
                           "reliability.mission_reliability": 0.97}}
    r = await client.post(f"/api/ecss/gate-evaluate/{study}/PDR", json=body)
    assert r.status_code == 200, r.text
    by = {c["id"]: c for c in r.json()["criteria"]}
    assert by["PDR-EC-01"]["status"] == "pass"
    assert by["PDR-EC-03"]["status"] == "pass"
    assert by["PDR-EC-04"]["status"] == "pass"
    assert by["PDR-EC-05"]["status"] == "pass"
    # Nov 2026: PDR-EC-02 is computed from the study's interfaces (none here → not met)
    assert by["PDR-EC-02"]["status"] == "fail"
    assert r.json()["ready_pending_manual"] is False


async def test_post_mission_need_overrides_study(client, study_obj, study):
    body = {"mission_need": {"problem_statement": "Smoke detection", "stakeholders": [{"name": "OFFS"}]}}
    r = await client.post(f"/api/ecss/gate-evaluate/{study}/mcr", json=body)
    by = {c["id"]: c for c in r.json()["criteria"]}
    assert by["MCR-EC-01"]["status"] == "pass"
    assert by["MCR-EC-02"]["status"] == "pass"


async def test_post_without_stored_study(client):
    r = await client.post("/api/ecss/gate-evaluate/local/pdr", json={})
    assert r.status_code == 200
    assert r.json()["study_found"] is False
