"""W8a acceptance on the Northern Fire and Ice fixture: model philosophy and verification plan.

The S4 seed proposes the default protoflight philosophy (breadboards month 6, engineering model
month 18, protoflight model month 30) and the 12-test matrix. The verification plan lists every
requirement in the store once (less the generated IR-* rows), by its close-out stage, with no
row cap, and the Word document names no launch vehicle the study did not choose.
"""
from __future__ import annotations

import io
from collections import Counter

from tests.fixtures.nfi import load, seed_nfi


STAGES = ("PDR", "CDR", "QR", "AR", "IOV")


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
    ait = (await client.get(f"/api/studies/{sid}/ait")).json()
    assert [m["code"] for m in ait["models"]] == ["BB", "EM", "PFM"]
    assert [m["due_month"] for m in ait["models"]] == [6, 18, 30]
    n = load("NUMBERS")["schedule"]["models"]
    assert [n["breadboard"], n["engineering_model"], n["protoflight_model"]] == [6, 18, 30]
    assert len(ait["tests"]) == 12
    assert {t["category"] for t in ait["tests"]} >= {"environmental", "functional"}
    by_code = {t["code"]: t for t in ait["tests"]}
    assert "VER-ENV-01" in by_code["T-ENV-02"]["requirement_codes"]
    assert "VER-DEP-01" in by_code["T-DEP-01"]["requirement_codes"]
    assert by_code["T-ENV-02"]["environment"]["grms"] > 0

    vp = (await client.get(f"/api/studies/{sid}/ait/verification-plan")).json()
    rows = await _store_rows(client, sid)
    total = len(rows)
    assert vp["counts"]["items"] == total == len(vp["items"])
    assert {i["requirement_id"] for i in vp["items"]} == {r["id"] for r in rows}
    # the store holds the whole baseline: requirements, objectives and stakeholder needs (W2 import)
    base = load("requirements")
    assert total == len(base["requirements"]) + len(base["objectives"]) + len(base["stakeholder_needs"])
    exp = _expected_stages(rows)
    assert vp["counts"]["by_stage"] == {st: exp[st] for st in STAGES}
    # each item keeps its method; test-verified VER rows point at their tests
    ver = {i["code"]: i for i in vp["items"]}
    assert ver["VER-ENV-02"]["methods"] == ["T"] and "T-ENV-03" in ver["VER-ENV-02"]["tests"]

    # the export collector carries the same plan
    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=ait,schedule")).json()
    assert sx["ait"]["status"] == "ok" and sx["ait"]["counts"]["items"] == total
    assert len(sx["ait"]["models"]) == 3 and len(sx["ait"]["tests"]) == 12

    # the Word document: every stage, no cap, no launch vehicle the study did not choose
    r = await client.get(f"/api/studies/{sid}/ait/verification-plan?fmt=docx")
    assert r.status_code == 200, r.text[:300]
    from docx import Document
    doc = Document(io.BytesIO(r.content))
    text = "\n".join(p.text for p in doc.paragraphs) + "\n".join(
        c.text for t in doc.tables for row in t.rows for c in row.cells)
    assert "falcon" not in text.lower()
    for st in STAGES:
        assert f"({st}) — {exp[st]}" in text, st
    assert "VER-MOD-01" in text and "Protoflight model" in text and "T-DIL-01" in text
    fr = await client.get(f"/api/studies/{sid}/ait/verification-plan?fmt=docx&lang=fr")
    frtext = "\n".join(p.text for p in Document(io.BytesIO(fr.content)).paragraphs)
    assert "Philosophie des modèles" in frtext and "Vérification en orbite (IOV)" in frtext


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
