"""Gate review API (author ruling Q23): /api/ecss/gate-evaluate/{study}/{gate}.

Nov 2026 (WP0): canonical gates MDR/PRR/SRR/PDR (CDR added in phase 2) ("mcr" still means MDR), and the
evaluation reads the stored study only — a POST body is ignored.
"""
from __future__ import annotations

from tests.test_api.conftest import make_element, make_requirement


async def test_gates_listing(client):
    r = await client.get("/api/ecss/gates")
    assert r.status_code == 200
    assert [g["gate"] for g in r.json()] == ["MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR"]   # W4.09


async def test_get_accepts_gate_names(client, study_obj, study):
    for gate, phase in (("mcr", "phase_0"), ("mdr", "phase_0"), ("prr", "phase_a"), ("srr", "phase_b1"),
                        ("pdr", "phase_b")):
        r = await client.get(f"/api/ecss/gate-evaluate/{study}/{gate}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["phase"] == phase and data["found"] and data["criteria"]
        assert data["study_found"] is True


async def test_unknown_gate_is_404(client, study_obj, study):
    r = await client.get(f"/api/ecss/gate-evaluate/{study}/xyz")
    assert r.status_code == 404


async def test_post_ignores_client_state(client, study_obj, study):
    """WP0: the V&V panel sent the empty legacy mission need and the gate believed it."""
    from spacecdf_common.models.mission_need import MissionNeed
    study_obj.mission_need = MissionNeed(problem_statement="Smoke detection",
                                         stakeholders=[{"name": "OFFS"}])
    # A client that sends an EMPTY mission need and invented parameters changes nothing
    body = {"mission_need": {"problem_statement": ""}, "parameters": {"systems.mass_margin_percent": 99}}
    r = await client.post(f"/api/ecss/gate-evaluate/{study}/mdr", json=body)
    by = {c["id"]: c for c in r.json()["criteria"]}
    assert by["MDR-EC-01"]["status"] == "pass"
    assert by["MDR-EC-02"]["status"] == "pass"
    assert by["MDR-EC-07"]["status"] == "not_evaluated"   # no design run on the server


async def test_post_without_stored_study(client):
    r = await client.post("/api/ecss/gate-evaluate/local/pdr", json={})
    assert r.status_code == 200
    assert r.json()["study_found"] is False
