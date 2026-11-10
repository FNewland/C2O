"""W8a / wave 3 (3.A4) acceptance on the Northern Fire and Ice fixture: model philosophy and
verification plan from the v2 V&V plan.

The S4 seed proposes the default protoflight philosophy, then imports the v2 plan
(``vv_plan.yaml``): the 6 models of its model philosophy and its 75 verification events, with their
requirements, as the test-matrix events (the default proposal is replaced). The verification plan
lists every requirement in the store once (less the generated IR-* rows), by its close-out stage,
with no row cap; each requirement points at its event; the Word document has a Validation chapter
and names no launch vehicle the study did not choose. Counts come from the fixture and the store.
"""
from __future__ import annotations

import io
from collections import Counter

from tests.fixtures.nfi import load, seed_nfi


STAGES = ("PRR", "SRR", "PDR", "CDR", "QR", "AR", "IOV")


async def _store_rows(client, sid: str) -> list[dict]:
    """The study's requirements as the store holds them, less the generated interface requirements
    (``IR-*``: the IRD lists those, not the verification plan)."""
    r = await client.get(f"/api/requirements/tree?study_id={sid}")
    assert r.status_code == 200, r.text[:300]
    return [x for x in r.json() if x.get("status") != "retired" and not str(x.get("code") or "").startswith("IR-")]


def _expected_stages(rows: list[dict]) -> Counter:
    c = Counter()
    for r in rows:
        st = str(r.get("verification_phase") or "").upper()
        # rows with no stage (stakeholder needs, OBJ-*): the V&V planner's verification items close them at PDR
        c[st if st in STAGES else "PDR"] += 1
    return c


async def test_vp_lists_models_tests_and_every_item_by_stage(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    plan = load("vv_plan")
    ait = (await client.get(f"/api/studies/{sid}/ait")).json()
    assert [m["code"] for m in ait["models"]] == [m["model"] for m in plan["model_philosophy"]]
    assert len(ait["models"]) == 6
    assert [m["due_month"] for m in ait["models"]] == [m["month"] for m in plan["model_philosophy"]]
    n = load("NUMBERS")["schedule"]["models"]
    by_model = {m["code"]: m["due_month"] for m in ait["models"]}
    assert [by_model["BB"], by_model["EM"], by_model["PFM"]] == [n["breadboard"], n["engineering_model"],
                                                                  n["protoflight_model"]]
    assert len(ait["tests"]) == len(plan["events"]) == 75
    by_code = {t["code"]: t for t in ait["tests"]}
    an_bud = next(e for e in plan["events"] if e["id"] == "AN-BUD")
    assert by_code["AN-BUD"]["requirement_codes"] == an_bud["requirements"] and len(an_bud["requirements"]) == 28
    assert by_code["AN-BUD"]["category"] == "analysis"
    assert by_code["TS-PFM-VIB"]["models"] == ["PFM"] and by_code["TS-PFM-VIB"]["category"] == "environmental"
    assert by_code["IOV-SCI"]["models"] == ["flight"]

    vp = (await client.get(f"/api/studies/{sid}/ait/verification-plan")).json()
    rows = await _store_rows(client, sid)
    total = len(rows)
    assert vp["counts"]["items"] == total == len(vp["items"])
    assert {i["requirement_id"] for i in vp["items"]} == {r["id"] for r in rows}
    base = load("requirements")
    assert total == len(base["requirements"]) + len(base["objectives"]) + len(base["stakeholder_needs"])
    exp = _expected_stages(rows)
    assert vp["counts"]["by_stage"] == {st: exp[st] for st in STAGES if exp[st] or st not in ("PRR", "SRR")}
    # the v2 matrix rows close at the stage the store holds (PDR 72, CDR 109 … PRR 1, SRR 1)
    v2_stage = Counter(r["stage"] for r in plan["matrix"])
    in_matrix = {r["id"] for r in plan["matrix"]}
    got = Counter(i["stage"] for i in vp["items"] if i["code"] in in_matrix)
    assert got == v2_stage and len(plan["matrix"]) == 302
    # every requirement row points at its verification event, and the event is a test-matrix row
    items = {i["code"]: i for i in vp["items"]}
    for r in plan["matrix"][:40]:
        assert items[r["id"]]["event"] == r["event"] and r["event"] in items[r["id"]]["tests"], r["id"]

    # the export collector carries the same plan
    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=ait,schedule")).json()
    assert sx["ait"]["status"] == "ok" and sx["ait"]["counts"]["items"] == total
    assert len(sx["ait"]["models"]) == 6 and len(sx["ait"]["tests"]) == 75

    # the Word document: every stage, no cap, a Validation chapter, no launch vehicle the study did not choose
    r = await client.get(f"/api/studies/{sid}/ait/verification-plan?fmt=docx")
    assert r.status_code == 200, r.text[:300]
    from docx import Document
    doc = Document(io.BytesIO(r.content))
    text = "\n".join(p.text for p in doc.paragraphs) + "\n".join(
        c.text for t in doc.tables for row in t.rows for c in row.cells)
    assert "falcon" not in text.lower()
    for st in STAGES:
        if exp[st]:
            assert f"({st}) — {exp[st]}" in text, st
    assert "Protoflight model" in text and "TS-PFM-DITL" in text and "Validation" in text
    fr = await client.get(f"/api/studies/{sid}/ait/verification-plan?fmt=docx&lang=fr")
    frtext = "\n".join(p.text for p in Document(io.BytesIO(fr.content)).paragraphs)
    assert "Philosophie des modèles" in frtext and "Vérification en orbite (IOV)" in frtext and "Validation" in frtext


async def test_user_rows_survive_a_new_proposal(client):
    s = await seed_nfi(client, "S2")
    sid = s.study_id
    first = (await client.post(f"/api/studies/{sid}/ait/propose")).json()
    assert first["added"] == 15
    em = next(m for m in first["models"] if m["code"] == "EM")
    r = await client.patch(f"/api/studies/{sid}/ait/models/{em['id']}", json={"due_month": 20})
    assert r.status_code == 200 and r.json()["origin"] == "user"
    r = await client.post(f"/api/studies/{sid}/ait/tests", json={"code": "T-MAG-01", "name": "Magnetic cleanliness",
                                                                 "category": "physical", "models": ["PFM"]})
    assert r.status_code == 200
    again = (await client.post(f"/api/studies/{sid}/ait/propose")).json()
    assert again["added"] == 0
    assert next(m for m in again["models"] if m["code"] == "EM")["due_month"] == 20
    assert len(again["tests"]) == 13
    # an empty study shows the default proposal in the collector, flagged "proposed"
    other = (await client.post("/api/studies/", json={"requirements": {"name": "Empty"}})).json()["id"]
    sx = (await client.get(f"/api/studies/{other}/export-context?sections=ait")).json()
    assert sx["ait"]["status"] == "proposed" and len(sx["ait"]["models"]) == 3
