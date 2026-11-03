"""HTTP layer of the deterministic rule engines (routers/rules.py)."""
from __future__ import annotations

from tests.test_api.conftest import make_element, make_requirement


async def _cubesat(client, sid):
    sysel = await make_element(client, sid, "Spacecraft", "system")
    for name, mass, power, kb in (("OBC", 0.1, 0.5, "obc-isis-iobc"), ("UHF transceiver", 0.1, 1.5, None),
                                  ("Structure", 0.6, None, "struct-isis-3u")):
        r = await client.post(f"/api/elements/?study_id={sid}", json={
            "name": name, "element_type": "component", "parent_id": sysel["id"], "mass_kg": mass,
            "power_avg_w": power, "kb_component_id": kb})
        assert r.status_code == 200, r.text
    return sysel


async def test_catalogue(client):
    r = await client.get("/api/rules/catalogue")
    assert r.status_code == 200
    body = r.json()
    assert set(body["files"]) == {"margin_policy", "cds_rules", "requirement_rules", "failure_modes"}
    kinds = {s["kind"] for f in body["files"].values() for s in f["sources"].values()}
    assert {"standard", "c2o_default"} <= kinds
    assert any(c["id"] == "R7-VAGUE" for c in body["requirement_checks"])


async def test_adhoc_quality(client):
    r = await client.post("/api/rules/requirement-quality",
                          json={"texts": ["The OBC shall boot within 10 s.", "Le système doit être convivial."]})
    rows = r.json()["rows"]
    assert rows[0]["status"] == "pass" and rows[1]["status"] == "fail" and rows[1]["language"] == "fr"


async def test_study_rules(client, study_obj):
    sid = study_obj.id
    await _cubesat(client, sid)
    await make_requirement(client, sid, "r1", text="The spacecraft shall downlink at least 1 GB per day.")
    await make_requirement(client, sid, "r2", text="The spacecraft dry mass shall not exceed 5 kg.",
                           threshold_param_path="mass.dry_mass_kg", verification_method="T")

    m = (await client.get(f"/api/studies/{sid}/rules/margins")).json()
    assert m["form_factor"] == "3U" and m["mass"]["limit_kg"] == 6.0 and m["mass"]["cbe_kg"] > 0
    cds = (await client.get(f"/api/studies/{sid}/rules/cds")).json()
    assert cds["applicable"] and any(c["id"] == "CDS-RF-INH" for c in cds["checks"])
    q = (await client.get(f"/api/studies/{sid}/rules/requirements-quality")).json()
    assert q["summary"]["total"] == 2
    v = (await client.get(f"/api/studies/{sid}/rules/verification-defaults")).json()
    assert v["summary"]["missing_method"] == 1 and v["summary"]["differs_from_default"] == 1

    applied = (await client.post(f"/api/studies/{sid}/rules/verification-defaults/apply")).json()
    assert applied["count"] == 1 and applied["applied"][0]["requirement_id"] == "r1"
    assert (await client.get("/api/requirements/r1")).json()["verification_method"] == "T"
    assert (await client.get("/api/requirements/r2")).json()["verification_method"] == "T"   # not overwritten

    f = (await client.get(f"/api/studies/{sid}/rules/fmeca-skeleton")).json()
    assert f["summary"]["modes"] >= 3
    g = (await client.get(f"/api/studies/{sid}/rules/gates/PDR")).json()
    assert g["gate"]["id"] == "pdr" and g["criteria"] and len(g["checks"]) == 8
    assert (await client.get(f"/api/studies/{sid}/rules/gates/XYZ")).status_code == 404
    s = (await client.get(f"/api/studies/{sid}/rules/summary")).json()
    assert {"margins", "cds", "requirements_quality", "verification", "fmeca"} <= set(s)


async def test_unknown_study_404(client):
    assert (await client.get("/api/studies/nope/rules/margins")).status_code == 404
