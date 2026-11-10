"""3.S3 stakeholders and MOEs, 3.S5 validation, 3.S6 assumptions on the Northern Fire and Ice v2 fixture,
with a project round trip. Counts come from the fixture files and the store."""
from __future__ import annotations

import re

from tests.fixtures.nfi import load, seed_nfi


def _categories_in_fixture() -> set[str]:
    from spacecdf_common.models.mission_need import parse_categories
    return {c for s in load("stakeholders")["stakeholders"] for c in parse_categories(s["category"])}


async def test_s0_stakeholders_needs_and_moes(client):
    sh = load("stakeholders")
    s = await seed_nfi(client, "S0")
    sid = s.study_id
    reg = (await client.get(f"/api/studies/{sid}/stakeholders")).json()
    c = reg["counts"]
    assert c["stakeholders"] == len(sh["stakeholders"]) and c["needs"] == len(sh["needs"])
    assert c["categories"] == len(_categories_in_fixture()) == 5 and c["unclassified"] == 0
    assert set(c["by_category"]) == {"decision_authority", "beneficiary", "affected_party", "rights_holder", "non_human"}
    stk = {x["id"]: x for x in reg["items"]}
    assert stk["STK-02"]["categories"] == ["decision_authority", "rights_holder"]
    assert stk["STK-02"]["need_ids"] == ["SN-02", "SN-09"] and stk["STK-02"]["engagement"]
    moes = (await client.get(f"/api/studies/{sid}/moes")).json()
    assert moes["counts"]["total"] == len(sh["moes"])
    ph = sorted(m["code"] for m in moes["items"] if m["placeholder"])
    assert ph == ["MOE-04", "MOE-10"]
    assert all(m["approval"] == "" for m in moes["items"])           # PI approved the wording
    m11 = next(m for m in moes["items"] if m["code"] == "MOE-11")
    assert not m11["placeholder"] and m11["pending_parts"]          # one pending part, still a defined MOE
    # MDR-EC-02 and MDR-EC-03 pass on the imported register
    g = (await client.get(f"/api/studies/{sid}/rules/gates/mdr")).json()
    st = {x["id"]: x["status"] for x in g["criteria"]}
    assert st["MDR-EC-02"] == "pass" and st["MDR-EC-03"] == "pass"
    # each objective is linked to the holders of its needs
    study = (await client.get(f"/api/studies/{sid}")).json()
    o1 = next(o for o in study["mission_need"]["objectives"] if o["id"] == "O1")
    assert "STK-02" in o1["stakeholder_ids"]


async def test_moe_and_stakeholder_editing(client):
    s = await seed_nfi(client, "S0")
    sid = s.study_id
    r = await client.patch(f"/api/studies/{sid}/moes/MOE-10", json={
        "threshold": "majority of the community review panels say the product helped", "defined_by": "communities"})
    assert r.status_code == 200 and r.json()["placeholder"] is False
    new = (await client.post(f"/api/studies/{sid}/moes", json={"measure": "Products in the community language",
                                                                "objectives": ["O3"], "needs": ["SN-10"]})).json()
    assert new["code"] == "MOE-16"
    assert (await client.post(f"/api/studies/{sid}/moes", json={"measure": ""})).status_code == 422
    assert (await client.delete(f"/api/studies/{sid}/moes/MOE-16")).json() == {"deleted": "MOE-16"}
    up = await client.put(f"/api/studies/{sid}/stakeholders/STK-09", json={"category": "beneficiary / affected party"})
    assert up.status_code == 200 and up.json()["categories"] == ["beneficiary", "affected_party"]
    add = await client.put(f"/api/studies/{sid}/stakeholders/STK-13", json={"name": "Local schools", "category": "beneficiary"})
    assert add.status_code == 200
    assert (await client.get(f"/api/studies/{sid}/stakeholders")).json()["counts"]["stakeholders"] == 13


async def test_s3_validation_activities_and_need_validation(client):
    plan = load("vv_plan")["validation_plan"]
    sh = load("stakeholders")
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    acts = (await client.get(f"/api/studies/{sid}/validation/activities")).json()["items"]
    assert [a["code"] for a in acts] == [v["id"] for v in plan]
    v1 = acts[0]
    assert v1["requirement_codes"] == ["MIS-VAL-01", "MIS-SCI-14"]
    assert v1["performer"] == next(v["who"] for v in plan if v["id"] == "V1")
    assert v1["performer"].startswith("each stakeholder group") and not v1["engineers_only"]
    assert set(v1["performer_ids"]) == {x["id"] for x in sh["stakeholders"]}
    assert v1["stages"] == ["MDR", "PRR"] and "MOE-04" in v1["moes"] and "O1" in v1["objectives"]
    # ORR and CRR are validation stages, not gates (PI default)
    stages = {a["code"]: a["stages"] for a in acts}
    assert "ORR" in stages["V4"] and stages["V5"] == ["CRR"]
    nv = (await client.get(f"/api/studies/{sid}/validation/need-validation")).json()["items"]
    assert len(nv) == len(sh["need_validation"]) == 12
    sn02 = next(n for n in nv if n["need_code"] == "SN-02")
    assert sn02["activity_codes"] == ["V1", "V3", "V6"] and "PHASE_E" in sn02["stages"]
    cov = (await client.get(f"/api/studies/{sid}/validation/coverage")).json()
    assert cov["ok"] and cov["primary"] == ["O1", "O3", "O4"] and cov["needs_without_validation"] == []
    # an activity performed by the engineering team alone is flagged
    r = await client.post(f"/api/studies/{sid}/validation/activities",
                          json={"title": "Desk review", "performer": "student engineering team", "stage": "PDR"})
    assert r.status_code == 200 and r.json()["engineers_only"] is True
    assert (await client.patch(f"/api/studies/{sid}/validation/activities/V2", json={"stage": "XYZ"})).status_code == 422


async def test_fresh_study_proposes_one_activity_per_primary_objective(client):
    s = await seed_nfi(client, "S0")
    sid = s.study_id
    primary = [o["id"] for o in load("requirements")["objectives"] if o["priority"] == "primary"]
    res = (await client.post(f"/api/studies/{sid}/validation/propose")).json()
    assert res["added"] == [f"VAL-{o}" for o in primary] == ["VAL-O1", "VAL-O3", "VAL-O4"]
    first = res["items"][0]
    assert first["status"] == "proposed" and first["performer_ids"] and not first["engineers_only"]
    assert (await client.post(f"/api/studies/{sid}/validation/propose")).json()["added"] == []


def _fixture_assumption_count() -> tuple[int, int, int]:
    """(distinct budget tags, assumption rows, budget tags that name an assumption row), counted
    from the fixture files with plain text rules."""
    reqs = [r for r in load("requirements")["requirements"] if "assumption" in str(r.get("open_item_note") or "").lower()]
    tags: set[tuple[str, str]] = set()
    named: set[str] = set()
    codes = {r["id"] for r in reqs}

    def walk(node, owner=None):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and "[ASSUMPTION" in v:
                    item = str(node.get("contributor") or node.get("unit") or "")
                    tag = v.split("]")[0]
                    tags.add((item, tag))
                    named.update(c for c in codes if c in v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk({k: v for k, v in load("budgets").items() if k not in ("margin_policy", "traceability")})
    return len(tags), len(reqs), len(named)


async def test_s3_assumption_register(client):
    n_tags, n_rows, n_twins = _fixture_assumption_count()
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    items = (await client.get(f"/api/studies/{sid}/assumptions")).json()["items"]
    assert len(items) == n_tags + n_rows - n_twins
    assert all(re.match(r"^ASM-\d\d$", a["code"]) and a["status"] == "open" and a["owner_seat"] for a in items)
    # the timing-budget latency (PAY-FUN-06, budget_ref timing.latency) is due at PDR
    lat = next(a for a in items if any(f["ref"] == "timing.latency" for f in a["affects"]))
    assert lat["due_gate"] == "pdr" and lat["owner_seat"] == "payload_lead"
    # a budget tag that names an assumption row is the same assumption
    bat = [a for a in items if any(f["ref"] == "THM-BAT-01" for f in a["affects"])]
    assert len(bat) == 1 and "budgets.yaml" in bat[0]["source"]
    # the PDR analysis standard warns on them; MDR has none due
    pdr = (await client.get(f"/api/studies/{sid}/phase?gate=pdr")).json()
    an = {x["id"]: x for x in pdr["analysis"]}
    assert an["PDR-AN-01"]["state"] == "warn" and len(an["PDR-AN-01"]["items"]) == len(items)
    mdr = (await client.get(f"/api/studies/{sid}/phase?gate=mdr")).json()
    assert {x["id"]: x["state"] for x in mdr["analysis"]}["MDR-AN-01"] == "ok"
    # closing one needs evidence
    bad = await client.patch(f"/api/studies/{sid}/assumptions/{lat['code']}", json={"status": "confirmed"})
    assert bad.status_code == 422
    ok = await client.patch(f"/api/studies/{sid}/assumptions/{lat['code']}",
                            json={"status": "confirmed", "evidence": "breadboard trigger test: 0.12 ms"})
    assert ok.status_code == 200
    assert len((await client.get(f"/api/studies/{sid}/assumptions?status=open")).json()["items"]) == len(items) - 1
    # re-import does not duplicate
    again = await client.post(f"/api/studies/{sid}/assumptions/import", json={"budgets": load("budgets")})
    assert again.json()["added"] == 0


async def test_sections_and_project_round_trip(client):
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    sx = (await client.get(f"/api/studies/{sid}/export-context?gate=pdr")).json()
    assert sx["errors"] == {}
    for name in ("stakeholders", "validation", "assumptions", "se_phase"):
        assert sx[name].get("status") != "not_implemented", name
    assert sx["stakeholders"]["counts"]["placeholder_moes"] == 2
    assert sx["validation"]["counts"]["activities"] == len(load("vv_plan")["validation_plan"])
    assert sx["se_phase"]["gate"] == "pdr" and sx["se_phase"]["deliverables"]
    before = {p: (await client.get(f"/api/studies/{sid}{p}")).json()
              for p in ("/stakeholders", "/moes", "/validation/activities", "/validation/need-validation", "/assumptions")}
    doc = (await client.get(f"/api/studies/{sid}/export")).json()
    new = (await client.post("/api/studies/import", json=doc)).json()
    nid = new.get("study_id") or new.get("id") or new["study"]["id"]
    strip = ("id", "study_id")

    def clean(v):
        if isinstance(v, list):
            return [clean(x) for x in v]
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items() if k not in strip}
        return v
    for p, old in before.items():
        got = (await client.get(f"/api/studies/{nid}{p}")).json()
        assert clean(got) == clean(old), p
