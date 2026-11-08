"""The requirement type has its own field (it used to be stored in ``rationale``)."""
from __future__ import annotations


async def test_type_is_its_own_field_and_legacy_rationale_moves(client, study_obj):
    sid = study_obj["id"] if isinstance(study_obj, dict) else study_obj.id
    r = await client.post("/api/requirements/", json={"study_id": sid, "level": "system", "code": "SR-T1",
                                                       "text": "The system shall do X.", "req_type": "functional",
                                                       "rationale": "Because the mission needs X."})
    assert r.status_code in (200, 201), r.text
    assert r.json()["req_type"] == "functional" and r.json()["rationale"] == "Because the mission needs X."
    legacy = (await client.post("/api/requirements/", json={"study_id": sid, "level": "system", "code": "SR-T2",
                                                            "text": "The system shall do Y.",
                                                            "rationale": "performance"})).json()
    assert legacy["req_type"] == "performance" and legacy["rationale"] is None
    p = await client.patch(f"/api/requirements/{legacy['id']}", json={"req_type": "interface"})
    assert p.json()["req_type"] == "interface"
