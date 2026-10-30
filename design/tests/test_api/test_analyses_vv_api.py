"""SCDF-175 — V&V closure over HTTP: run -> items -> patch (user edit) ->
re-run preserves the edit -> evidence post; RTM CSV has rows; VCD docx is a
valid zip; auto-closure through a design-loop publish; stale after a
requirement change."""
from __future__ import annotations

import csv
import io
import zipfile

import pytest

from tests.test_api.conftest import make_element, make_requirement


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    from spacecdf_server.services import analysis_results
    analysis_results.reset_trackers()
    yield
    analysis_results.reset_trackers()


async def _tree(client, study):
    mission = await make_element(client, study, "Mission", "mission")
    seg = await make_element(client, study, "Space Segment", "segment", mission["id"])
    sc = await make_element(client, study, "Spacecraft", "system", seg["id"])
    eps = await make_element(client, study, "EPS", "subsystem", sc["id"], "power")
    r = await client.patch(f"/api/elements/{eps['id']}", json={"mass_kg": 2.0, "version": eps["version"]})
    assert r.status_code == 200, r.text
    str_ = await make_element(client, study, "Structure", "subsystem", sc["id"], "structure")
    await make_requirement(client, study, "MR-1", level="mission", text="Mission shall image the coast")
    await make_requirement(client, study, "SR-PWR-1", text="EPS mass <= 5 kg", threshold_param_path="el:EPS.mass_kg",
                           threshold_op="<=", threshold_value="5")
    await make_requirement(client, study, "SR-STR-1", level="subsystem", element_id=str_["id"], verification_method="T",
                           text="Structure first mode", threshold_param_path="structure.first_mode_hz",
                           threshold_op=">=", threshold_value="90")
    r = await client.post(f"/api/relations/?study_id={study}", json={
        "study_id": study, "kind": "satisfies", "source_kind": "element", "source_id": eps["id"],
        "target_kind": "requirement", "target_id": "SR-PWR-1"})
    assert r.status_code in (200, 201), r.text
    return {"mission": mission, "eps": eps, "str": str_}


async def test_run_items_patch_rerun_exports(client, study_obj, study):
    els = await _tree(client, study)
    assert (await client.get(f"/api/studies/{study}/analyses/vv")).status_code == 404
    assert (await client.get(f"/api/studies/{study}/verification-items")).json()["total"] == 0

    r = await client.post(f"/api/studies/{study}/analyses/vv/run")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok" and body["stale"] is False
    assert body["summary"]["vv_items_total"] == 3 and body["summary"]["vv_items_passed"] == 1
    assert {p["name"] for p in body["parameters"]} >= {"vv_items_total", "vv_closure_pct", "vv_by_analysis_pct"}
    assert all(p["element_id"] == els["mission"]["id"] for p in body["parameters"])
    assert [c["code"] for c in body["conflicts"]] == ["VV_REQ_UNVERIFIABLE"]
    items = {i["requirement_id"]: i for i in body["items"]}
    pwr = items["SR-PWR-1"]
    assert pwr["status"] == "passed" and pwr["evidence_ref"] == f"analysis:{body['run_id']}" and pwr["auto_closed"] is True
    assert pwr["linked_elements"] == [els["eps"]["id"]] and pwr["linked_element_names"] == ["EPS"]
    assert pwr["requirement_code"] == "SR-PWR-1" and pwr["level"] == "system"
    assert items["SR-STR-1"]["facility"] == "shaker_table" and items["MR-1"]["method"] == "R"

    # last run + params on the mission root
    r = await client.get(f"/api/studies/{study}/analyses/vv")
    assert r.status_code == 200 and r.json()["id"] == body["run_id"] and r.json()["stale"] is False
    r = await client.get(f"/api/studies/{study}/verification-items?status=passed")
    assert r.status_code == 200 and [i["requirement_id"] for i in r.json()["items"]] == ["SR-PWR-1"]
    assert r.json()["by_level"]["system"]["passed"] == 1

    # user edit -> locked
    st = items["SR-STR-1"]
    r = await client.patch(f"/api/verification-items/{st['id']}", json={"facility": "ESA ESTEC shaker", "phase": "QR"})
    assert r.status_code == 200, r.text
    assert r.json()["edited_by_user"] is True and r.json()["phase"] == "QR"
    assert (await client.patch(f"/api/verification-items/{st['id']}", json={"bogus": 1})).status_code == 400
    assert (await client.patch(f"/api/verification-items/{st['id']}", json={"status": "nope"})).status_code == 400
    assert (await client.patch("/api/verification-items/vi-none", json={"phase": "QR"})).status_code == 404

    # re-run preserves the edit and keeps one item per requirement
    r = await client.post(f"/api/studies/{study}/analyses/vv/run")
    assert r.status_code == 200, r.text
    items2 = {i["requirement_id"]: i for i in r.json()["items"]}
    assert len(items2) == 3 and items2["SR-STR-1"]["id"] == st["id"]
    assert items2["SR-STR-1"]["facility"] == "ESA ESTEC shaker" and items2["SR-STR-1"]["phase"] == "QR"

    # evidence post closes a test item
    r = await client.post(f"/api/verification-items/{st['id']}/evidence",
                          json={"evidence_ref": "TR-STR-001", "status": "passed"})
    assert r.status_code == 200 and r.json()["status"] == "passed" and r.json()["evidence_ref"] == "TR-STR-001"
    assert (await client.post(f"/api/verification-items/{st['id']}/evidence", json={"status": "x"})).status_code == 400

    # RTM CSV
    r = await client.get(f"/api/studies/{study}/export/rtm.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "RTM.csv" in r.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert [row["requirement_code"] for row in rows] == ["MR-1", "SR-PWR-1", "SR-STR-1"]
    pw = rows[1]
    assert pw["method"] == "A" and pw["status"] == "passed" and pw["linked_elements"] == "EPS"
    assert pw["acceptance_criterion"].startswith("EPS mass") and pw["evidence_ref"].startswith("analysis:")
    assert rows[2]["evidence_ref"] == "TR-STR-001" and rows[2]["facility"] == "ESA ESTEC shaker"

    # VCD docx: valid zip with a document body mentioning the requirement codes
    r = await client.get(f"/api/studies/{study}/export/vcd.docx")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert "VCD.docx" in r.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert zf.testzip() is None
        xml = zf.read("word/document.xml").decode("utf-8")
    assert "Verification Control Document" in xml and "SR-PWR-1" in xml and "TR-STR-001" in xml


async def test_auto_closure_via_design_loop_and_stale(client, study_obj, study):
    from spacecdf_server.services.analysis_results import ParamWrite, ResultsSink

    els = await _tree(client, study)
    r = await client.post(f"/api/studies/{study}/analyses/vv/run")
    assert r.status_code == 200, r.text
    run_id = r.json()["run_id"]
    pwr = next(i for i in r.json()["items"] if i["requirement_id"] == "SR-PWR-1")
    assert pwr["status"] == "passed"

    # another analysis publishes a breaking EPS mass -> the A item fails with that run's evidence
    await ResultsSink().publish(study, "design_loop", run_id="run-dl-9",
                                parameters=[ParamWrite("mass_kg", 7.0, element_id=els["eps"]["id"])])
    r = await client.get(f"/api/studies/{study}/verification-items")
    pwr = next(i for i in r.json()["items"] if i["requirement_id"] == "SR-PWR-1")
    assert pwr["status"] == "failed" and pwr["evidence_ref"] == "analysis:run-dl-9" and pwr["auto_closed"] is True

    # V&V run is stale once a requirement threshold changes; the next run raises VV_FAILED
    r = await client.patch("/api/requirements/SR-PWR-1", json={"threshold_value": "5.5"})
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/studies/{study}/analyses/vv")
    assert r.json()["id"] == run_id and r.json()["stale"] is True
    r = await client.post(f"/api/studies/{study}/analyses/vv/run")
    assert r.status_code == 200
    assert [(c["code"], c["severity"]) for c in r.json()["conflicts"] if c["code"] == "VV_FAILED"] == [("VV_FAILED", "major")]
    assert r.json()["summary"]["vv_items_failed"] == 1
    r = await client.get(f"/api/studies/{study}/conflicts")
    assert r.status_code == 200
    assert any(c["code"] == "VV_FAILED" and c["analysis"] == "vv" for c in r.json()["analysis"])
