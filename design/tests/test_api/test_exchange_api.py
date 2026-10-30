"""SCDF-160 Phase 2d — ``routers/exchange.py`` over the FastAPI app.

All GET exports return the right content type with a non-empty body; the
Capella and ReqIF imports round-trip through the multipart endpoints;
``push/comet`` is 501 unless ``COMET_URL`` is set.
"""
from __future__ import annotations

import io
import json
import zipfile

import pytest

from tests.test_api.conftest import client, make_element, make_interface, make_requirement, study_obj  # noqa: F401
from tests.test_repositories.conftest import db_factory, study  # noqa: F401

pytest.importorskip("capellambse")


async def _seed_api(client, study_id: str) -> dict:  # noqa: F811
    sc = await make_element(client, study_id, "Spacecraft", "system")
    eps = await make_element(client, study_id, "EPS", "subsystem", sc["id"], "power")
    obc = await make_element(client, study_id, "OBDH", "subsystem", sc["id"], "obc")
    pcdu = await make_element(client, study_id, "PCDU", "component", eps["id"])
    await make_interface(client, study_id, pcdu["id"], obc["id"], "28V bus", "electrical")
    await make_requirement(client, study_id, "MR-1", "mission", code="MR-001")
    await make_requirement(client, study_id, "SR-1", "system", parent_id="MR-1", element_id=eps["id"], code="SR-001")
    r = await client.put(f"/api/elements/{eps['id']}/parameters/mass_kg",
                         json={"manual_value": 4.5, "value_switch": "manual"})
    assert r.status_code == 200, r.text
    r = await client.post(f"/api/relations/?study_id={study_id}", json={
        "kind": "satisfies", "source_kind": "element", "source_id": eps["id"],
        "target_kind": "requirement", "target_id": "SR-1"})
    assert r.status_code in (200, 201), r.text
    return {"sc": sc, "eps": eps, "obc": obc, "pcdu": pcdu}


async def test_get_exports(client, study, study_obj):  # noqa: F811
    await _seed_api(client, study)
    base = f"/api/studies/{study}/export"

    r = await client.get(f"{base}/capella.zip")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    assert 'attachment; filename="API_test_study.capella.zip"' == r.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert {n.rsplit(".", 1)[-1] for n in zf.namelist()} == {"project", "afm", "aird", "capella"}
    capella_zip = r.content

    r = await client.get(f"{base}/capella/summary")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["study_id"] == study and body["counts"] and len(body["files"]) == 4

    r = await client.get(f"{base}/ecss-10-25.zip")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert r.headers["content-disposition"].endswith('.ecss-10-25.zip"')
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        names = zf.namelist()
        assert "Header.json" in names and "SiteDirectory.json" in names
        it = [n for n in names if "/Iterations/" in n]
        assert len(it) == 1
        objs = json.loads(zf.read(it[0]))
        assert {o["classKind"] for o in objs} >= {"Iteration", "Option", "ElementDefinition", "ElementUsage",
                                                  "Parameter", "ParameterValueSet", "RequirementsSpecification",
                                                  "Requirement", "Definition"}

    r = await client.get(f"{base}/requirements.reqif")
    assert r.status_code == 200 and r.headers["content-type"] == "application/xml"
    assert r.headers["content-disposition"].endswith('.reqif"')
    assert r.content.startswith(b"<?xml") and b"SCDF-REQ-SR-1" in r.content
    reqif_bytes = r.content

    r = await client.get(f"{base}/model.sysml")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
    assert r.headers["content-disposition"].endswith('.sysml"')
    assert "package API_test_study {" in r.text and "satisfy SR_001 by EPS;" in r.text

    r = await client.get(f"{base}/mbse-legacy.json")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    assert body.get("schema") == "spacecdf.mbse.v1" and body.get("engineering_model")
    assert r.headers["content-disposition"].endswith('.mbse-legacy.json"')

    # 404 for an unknown study
    r = await client.get("/api/studies/nope/export/model.sysml")
    assert r.status_code == 404

    return capella_zip, reqif_bytes


async def test_capella_import_round_trip_via_api(client, study, study_obj):  # noqa: F811
    from spacecdf_common.models.study import Study
    from spacecdf_server.routers.studies import get_study_store

    await _seed_api(client, study)
    r = await client.get(f"/api/studies/{study}/export/capella.zip")
    assert r.status_code == 200
    zip_bytes = r.content

    # import into a second study (registered in the study store)
    other = "study-2"
    get_study_store()[other] = Study(id=other, name="Imported")
    r = await client.post(f"/api/studies/{other}/import/capella",
                          files={"file": ("model.capella.zip", zip_bytes, "application/zip")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["format"] == "capella" and body["study_id"] == other
    assert body["created"].get("element", 0) >= 4

    r = await client.get(f"/api/studies/{other}/elements/tree")
    assert r.status_code == 200, r.text
    names = set()

    def walk(nodes):
        for n in nodes:
            names.add(n["name"])
            walk(n.get("children") or [])
    walk(r.json())
    assert {"EPS", "OBDH", "PCDU"} <= names

    # importing the same zip again updates, does not duplicate
    r = await client.post(f"/api/studies/{other}/import/capella",
                          files={"file": ("model.capella.zip", zip_bytes, "application/zip")})
    assert r.status_code == 200, r.text
    assert r.json()["created"].get("element", 0) == 0

    # garbage upload -> 400
    r = await client.post(f"/api/studies/{other}/import/capella",
                          files={"file": ("x.zip", b"not a zip", "application/zip")})
    assert r.status_code == 400
    r = await client.post(f"/api/studies/{other}/import/capella",
                          files={"file": ("x.zip", b"", "application/zip")})
    assert r.status_code == 400


async def test_reqif_import_via_api(client, study, study_obj):  # noqa: F811
    from spacecdf_common.models.study import Study
    from spacecdf_server.routers.studies import get_study_store

    await _seed_api(client, study)
    r = await client.get(f"/api/studies/{study}/export/requirements.reqif")
    assert r.status_code == 200
    other = "study-3"
    get_study_store()[other] = Study(id=other, name="Imported reqs")
    r = await client.post(f"/api/studies/{other}/import/reqif",
                          files={"file": ("reqs.reqif", r.content, "application/xml")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["format"] == "reqif" and body["created"] == 2 and body["updated"] == 0
    r = await client.get(f"/api/requirements/tree?study_id={other}")
    assert r.status_code == 200
    reqs = {q["external_id"]: q for q in r.json()}
    assert set(reqs) == {"SCDF-REQ-MR-1", "SCDF-REQ-SR-1"}
    assert reqs["SCDF-REQ-SR-1"]["parent_id"] == reqs["SCDF-REQ-MR-1"]["id"]
    assert reqs["SCDF-REQ-SR-1"]["code"] == "SR-001"

    r = await client.post(f"/api/studies/{other}/import/reqif",
                          files={"file": ("bad.reqif", b"<not-reqif/>", "application/xml")})
    assert r.status_code == 400


async def test_push_comet_501_when_unconfigured(client, study, study_obj, monkeypatch):  # noqa: F811
    monkeypatch.delenv("COMET_URL", raising=False)
    r = await client.post(f"/api/studies/{study}/push/comet")
    assert r.status_code == 501
