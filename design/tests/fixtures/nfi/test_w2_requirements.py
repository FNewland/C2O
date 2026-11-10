"""W2 acceptance (agent R): the Northern Fire and Ice requirement baseline in SpaceCDF.

Stage S1 of the seed imports the whole baseline through the bulk import. These tests check
what the plan's acceptance tests ask: the counts per level, a parent for every row, every
objective covered, every field kept, allocation by element name, the drag-sail seat rule,
idempotent re-import scoped to the study, validation, the SMART / quality checkers, the
threshold model, the gate criteria and the ReqIF round trip.
"""
from __future__ import annotations

import time

import pytest

from tests.fixtures.nfi import load, seed_nfi

BASE = load("requirements")
ROWS = BASE["requirements"]
BY_CODE = {r["id"]: r for r in ROWS}


async def _reqs(client, sid: str) -> list[dict]:
    r = await client.get(f"/api/requirements/tree?study_id={sid}")
    assert r.status_code == 200, r.text
    return r.json()


def _yaml_fields(r: dict) -> dict:
    """The 16 fields of a baseline row, in the tool's model (threshold dates become ``before``)."""
    th = r.get("threshold") or {}
    op, value, unit = th.get("op"), th.get("value"), th.get("unit")
    if unit == "date":
        op, unit = ("before" if op in ("<=", "<") else "after"), None
    return {"code": r["id"], "level": r["level"], "category": r["category"], "type": r["type"], "text": r["text"],
            "rationale": r["rationale"], "parents": list(r["parents"]), "objectives": list(r["objectives"]),
            "method": r["verification_method"], "stage": r["verification_phase"], "owner": r["owner_seat"],
            "priority": r["priority"], "source": r["source"], "status": r["status"],
            "threshold": (op, value, unit), "subsystem": r["subsystem"]}


def _tool_fields(q: dict, code_of: dict, name_of: dict) -> dict:
    return {"code": q["code"], "level": q["level"], "category": q["category"], "type": q["req_type"],
            "text": q["text"], "rationale": q["rationale"], "parents": [code_of[p] for p in q["parent_ids"]],
            "objectives": q["objective_ids"], "method": q["verification_method"], "stage": q["verification_phase"],
            "owner": q["responsible_position"], "priority": q["priority"], "source": q["source_ref"],
            "status": q["status"], "threshold": (q["threshold_op"], q["threshold_value"], q["threshold_unit"]),
            "subsystem": name_of.get(q["element_id"])}


async def _names(client, sid: str) -> dict:
    els = (await client.get(f"/api/studies/{sid}/elements")).json()
    return {e["id"]: e["name"] for e in els}


async def test_w2_s1_imports_the_whole_baseline_with_every_field(client):
    s = await seed_nfi(client, "S1")
    rep = s.report["requirements_import"]
    assert rep["unallocated"] == []
    reqs = await _reqs(client, s.study_id)
    by_level: dict[str, int] = {}
    for q in reqs:
        by_level[q["level"]] = by_level.get(q["level"], 0) + 1
    counts = BASE["baseline"]["counts"]
    assert by_level == {"stakeholder": len(BASE["stakeholder_needs"]),
                        "mission": counts["level_mission"] + len(BASE["objectives"]),
                        "segment": counts["level_segment"], "system": counts["level_system"],
                        "subsystem": counts["level_subsystem"], "interface": counts["level_interface"]}
    assert len(s.requirements) == len(ROWS) + len(BASE["objectives"])

    code_of = {q["id"]: q["code"] for q in reqs}
    name_of = await _names(client, s.study_id)
    tool = {q["code"]: q for q in reqs}
    for r in ROWS:   # W2.02: every field equal on 216/216 rows
        assert _tool_fields(tool[r["id"]], code_of, name_of) == _yaml_fields(r), r["id"]
    # W2.02: IOV stage, D never stored; W2.09: SEG-US rows on the science (user) segment
    assert sum(1 for q in reqs if q["verification_phase"] == "IOV") == sum(
        1 for r in ROWS if r["verification_phase"] == "IOV")
    assert all(name_of[tool[c]["element_id"]] == "Science Segment" for c in tool if c.startswith("SEG-US"))
    # every requirement below the needs has a parent; 99 rows have several, all shown
    assert all(q["parent_ids"] for q in reqs if q["level"] != "stakeholder")
    assert sum(1 for q in reqs if q["code"] in BY_CODE and len(q["parent_ids"]) > 1) == sum(
        1 for r in ROWS if len(r["parents"]) > 1)
    # objective rows carry their objective and hang off the needs
    for o in BASE["objectives"]:
        q = tool[o["code"]]
        assert q["objective_id"] == o["id"] and [code_of[p] for p in q["parent_ids"]] == o["needs"]


async def test_w2_orphans_coverage_and_drag_sail_seat(client):
    s = await seed_nfi(client, "S1")
    ver = (await client.get(f"/api/requirements/verify?study_id={s.study_id}")).json()
    assert ver["orphans"] == 0
    cov = (await client.get(f"/api/studies/{s.study_id}/requirements/coverage")).json()
    assert cov["orphans"] == []
    for o in BASE["objectives"]:
        direct = sum(1 for r in ROWS if o["id"] in r["objectives"]) + 1   # + the OBJ row
        assert cov["objectives"][o["id"]]["direct"] == direct, o["id"]
        assert cov["objectives"][o["id"]]["reached"] >= direct
    # PI rule: the drag sail is owned by the Propulsion seat
    reqs = await _reqs(client, s.study_id)
    name_of = await _names(client, s.study_id)
    sail = [q for q in reqs if name_of.get(q["element_id"]) == "Disposal (drag sail)"]
    assert sail and all(q["responsible_position"] == "propulsion_engineer" for q in sail)
    # the traceability tree shows a multi-parent row under each parent
    tree = (await client.get(f"/api/studies/{s.study_id}/traceability/tree")).json()
    seen: dict[str, set] = {}

    def walk(nodes, parent):
        for n in nodes:
            seen.setdefault(n["code"], set()).add(parent)
            walk(n["children"], n["code"])
    for o in tree["objectives"]:
        walk(o["requirements"], o["id"])
    walk(tree["unlinked_requirements"], None)
    multi = [r for r in ROWS if len(r["parents"]) > 1]
    assert all(set(r["parents"]) <= seen.get(r["id"], set()) for r in multi)


async def test_w2_reimport_is_idempotent_and_scoped_to_the_study(client):
    s = await seed_nfi(client, "S1")
    t0 = time.perf_counter()
    rep = (await client.post(f"/api/studies/{s.study_id}/requirements/import", json={"document": BASE})).json()
    assert time.perf_counter() - t0 < 10
    assert (rep["created"], rep["updated"], rep["relations_created"], rep["relations_removed"]) == (0, 0, 0, 0)
    # the same codes into a second, fresh study: new ids there, the first study unchanged
    before = {q["id"]: q for q in await _reqs(client, s.study_id)}
    st2 = (await client.post("/api/studies/", json={"requirements": {"name": "Second"}})).json()["id"]
    rep2 = (await client.post(f"/api/studies/{st2}/requirements/import",
                              json={"document": BASE, "element_map": {}})).json()
    assert rep2["created"] == len(ROWS) + len(BASE["objectives"]) + len(BASE["stakeholder_needs"])
    assert not set(rep2["id_map"].values()) & set(before)
    after = {q["id"]: q for q in await _reqs(client, s.study_id)}
    assert after == before
    # no interface requirement was proposed by the import
    assert not [q for q in await _reqs(client, st2) if str(q["code"]).startswith("IR-")]


async def test_w2_validation_conflicts_and_bulk_edit(client):
    s = await seed_nfi(client, "S0")
    sid = s.study_id
    r = await client.post("/api/requirements/", json={"study_id": sid, "code": "X-1", "level": "foo", "text": "x"})
    assert r.status_code == 422
    ok = await client.post("/api/requirements/", json={"study_id": sid, "code": "X-1", "level": "segment",
                                                       "text": "The ground segment shall exist.",
                                                       "verification_method": "D", "verification_stage": "IOV"})
    assert ok.status_code == 200 and ok.json()["verification_method"] == "T"
    assert ok.json()["verification_phase"] == "IOV"
    dup = await client.post("/api/requirements/", json={"study_id": sid, "code": "X-1", "level": "system", "text": "y"})
    assert dup.status_code == 409
    other = await client.post("/api/requirements/", json={"study_id": sid, "code": "X-2", "level": "system",
                                                          "text": "z", "parent_id": ok.json()["id"]})
    assert (await client.patch(f"/api/requirements/{other.json()['id']}", json={"code": "X-1"})).status_code == 409
    assert (await client.patch(f"/api/requirements/{other.json()['id']}", json={"code": "X-3"})).json()["code"] == "X-3"
    assert (await client.patch(f"/api/requirements/{other.json()['id']}", json={"level": "bar"})).status_code == 422
    bulk = await client.patch("/api/requirements/bulk", json={"study_id": sid, "ids": [ok.json()["id"], other.json()["id"]],
                                                             "changes": {"priority": 2, "category": "operations"}})
    assert bulk.status_code == 200
    assert {q["priority"] for q in await _reqs(client, sid)} == {2}
    # a bad import row stops everything (nothing written) and is reported
    bad = {"requirements": [{"id": "Y-1", "level": "system", "text": "The y shall be.", "parents": ["NOPE"]}]}
    r = await client.post(f"/api/studies/{sid}/requirements/import", json={"document": bad})
    assert r.status_code == 422 and r.json()["detail"]["errors"][0]["field"] == "parents"
    dry = (await client.post(f"/api/studies/{sid}/requirements/import", json={"document": BASE, "dry_run": True})).json()
    assert dry["ok"] and dry["created"] == len(ROWS) + len(BASE["objectives"]) + len(BASE["stakeholder_needs"])
    assert len(await _reqs(client, sid)) == 2


async def test_w2_csv_import_keeps_the_fields(client):
    s = await seed_nfi(client, "S0")
    csv = ("id,level,type,text,parents,objectives,verification_method,verification_phase,priority,category,"
           "source,threshold_op,threshold_value,threshold_unit\n"
           "M-1,mission,performance,The mission shall image 3 sites.,,O1,T,IOV,1,science,brief,>=,3,sites\n"
           "S-1,system,performance,The spacecraft shall downlink 13 MB per day.,M-1,O1;O3,A,PDR,2,data,"
           "calc,>=,13,MB/day\n")
    rep = (await client.post(f"/api/studies/{s.study_id}/requirements/import",
                             json={"content": csv, "format": "csv"})).json()
    assert rep["created"] == 2 and not rep["errors"]
    q = {x["code"]: x for x in await _reqs(client, s.study_id)}
    assert q["S-1"]["objective_ids"] == ["O1", "O3"] and q["S-1"]["threshold_unit"] == "MB/day"
    assert q["S-1"]["threshold_value"] == 13 and q["M-1"]["verification_phase"] == "IOV"


async def test_w1_01_threshold_decode_and_smart_after_restart(client):
    from spacecdf_server.routers import requirements as rr
    s = await seed_nfi(client, "S1")
    v1 = (await client.get(f"/api/requirements/verify?study_id={s.study_id}")).json()
    before = {q["code"]: q["threshold_value"] for q in await _reqs(client, s.study_id)}
    rr.reset_requirement_cache()          # a restart: the store reloads from the database
    v2 = (await client.get(f"/api/requirements/verify?study_id={s.study_id}")).json()
    after = {q["code"]: q["threshold_value"] for q in await _reqs(client, s.study_id)}
    assert after == before
    m = lambda v: sum(1 for i in v["issues"] if "measurable" in i["codes"])  # noqa: E731
    assert m(v1) == m(v2) <= 10
    # the date and the dimensionless values survive as their own types
    assert after["REG-SPC-01"] == "2027-03-31" and after["MIS-DIS-02"] == 0.001


async def test_w2_05_threshold_model_and_srr_criteria(client):
    from spacecdf_server.services.gate_evaluator import evaluate_gate
    s = await seed_nfi(client, "S3")
    reqs = await _reqs(client, s.study_id)
    q = {x["code"]: x for x in reqs}
    assert q["REG-SPC-01"]["threshold_op"] == "before"
    rng = await client.patch(f"/api/requirements/{q['COM-UL-01']['id']}",
                             json={"threshold_op": "in_range", "threshold_value": {"min": "449.75", "max": 450.25},
                                   "threshold_unit": "MHz"})
    assert rng.json()["threshold_value"] == {"min": 449.75, "max": 450.25}
    bad = await client.patch(f"/api/requirements/{q['COM-UL-01']['id']}", json={"threshold_op": "~"})
    assert bad.status_code == 422
    st = (await client.get(f"/api/studies/{s.study_id}")).json()
    ifs = (await client.get(f"/api/studies/{s.study_id}/interfaces")).json()
    res = evaluate_gate("SRR", mission_need=st["mission_need"], requirements=await _reqs(client, s.study_id),
                        interfaces=ifs)
    by = {c["id"]: c for c in res["criteria"]}
    assert by["SRR-EC-01"]["status"] == "pass", by["SRR-EC-01"]
    assert by["SRR-EC-02"]["status"] == "pass", by["SRR-EC-02"]["evidence_found"]
    assert by["SRR-EC-11"]["status"] == "pass", by["SRR-EC-11"]["evidence_found"]


async def test_w2_06_quality_and_smart_false_positives(client):
    from spacecdf_server.services.requirement_engine import validate_smart
    from spacecdf_server.services.requirement_quality import check_requirements
    out = check_requirements([{"id": r["id"], "code": r["id"], "text": r["text"]} for r in ROWS])
    rules = out["summary"]["by_rule"]
    assert rules.get("R6-UNITS", 0) <= 10
    assert rules.get("R24-PRONOUN", 0) <= 13
    assert out["summary"]["by_ears_pattern"].get("none", 0) <= 5
    for code in ("EPS-SAF-01", "COM-DL-02", "HAR-SEG-01"):
        r = BY_CODE[code]
        chk = validate_smart({"id": code, "text": r["text"], "level": r["level"], "req_type": r["type"],
                              "verification_method": r["verification_method"], "parent_id": "x"})
        assert "how" not in chk.codes, code


async def test_w1_08_prr_budget_quotes_the_orbit_average(client):
    from spacecdf_server.services.gate_evaluator import evaluate_gate
    n = load("NUMBERS")
    s = await seed_nfi(client, "S2")
    ru = (await client.get(f"/api/studies/{s.study_id}/rollup?gate=prr")).json()
    eol = n["power"]["eol_generation_w"]["value"]
    res = evaluate_gate("PRR", design_params={"power.sa_power_eol_w": eol}, rollup=ru,
                        target_mass_kg=ru["mass"]["limit_kg"])
    c = {x["id"]: x for x in res["criteria"]}["PRR-EC-05"]
    avg = ru["power"]["orbit_average_w"]
    assert c["status"] == "pass", c["evidence_found"]
    assert c["evidence_params"]["power"] == f"{avg:.2f}" and c["evidence_params"]["avail"] == f"{eol:.1f}"
    assert c["evidence_params"]["ptotal"] == f"{avg * 1.2:.2f}"
    mdr = {x["id"]: x for x in evaluate_gate("MDR", design_params={"power.sa_power_eol_w": eol},
                                              rollup=ru)["criteria"]}["MDR-EC-07"]
    assert mdr["status"] == "pass", mdr["evidence_found"]


async def test_w2_reqif_round_trip_keeps_every_field(client):
    from spacecdf_agents.exporters.reqif import export_requirements_reqif, import_requirements_reqif
    s = await seed_nfi(client, "S1")
    xml = await export_requirements_reqif(s.study_id)
    st2 = (await client.post("/api/studies/", json={"requirements": {"name": "ReqIF copy"}})).json()["id"]
    # the copy gets the same element names, so the allocation can be matched by name
    names = await _names(client, s.study_id)
    for name in sorted(set(names.values()) & {r["subsystem"] for r in ROWS}):
        await client.post(f"/api/elements/?study_id={st2}", json={"name": name, "element_type": "subsystem"})
    res = await import_requirements_reqif(st2, xml)
    assert res.created == len(ROWS) + len(BASE["objectives"]) + len(BASE["stakeholder_needs"]), res.warnings[:5]
    a, b = await _reqs(client, s.study_id), await _reqs(client, st2)
    ca, cb = {q["id"]: q["code"] for q in a}, {q["id"]: q["code"] for q in b}
    na, nb = names, await _names(client, st2)
    ta = {q["code"]: _tool_fields(q, ca, na) for q in a}
    tb = {q["code"]: _tool_fields(q, cb, nb) for q in b}
    for r in ROWS:
        assert tb[r["id"]] == ta[r["id"]], r["id"]
    assert all(not q["id"].startswith("SCDF-REQ-") for q in b)


async def test_w2_07_interface_requirements_link_to_icd_rows_without_duplicates(client, monkeypatch):
    monkeypatch.setenv("SPACECDF_AUTO_IRD", "1")        # as in the running app
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    reqs = await _reqs(client, sid)
    auto = [q for q in reqs if str(q["code"]).startswith("IR-")]
    assert not [q for q in auto if "TBD bus TBD" in q["text"]]
    assert len(auto) <= 25, sorted(q["text"][:80] for q in auto)
    rels = (await client.get(f"/api/studies/{sid}/relations?kind=allocates")).json()
    to_items = {r["source_id"] for r in rels if r["target_kind"] == "exchange_item"}
    ifrows = [q for q in reqs if q["code"].startswith("IF-")]
    assert len(ifrows) == 12 and all(q["id"] in to_items for q in ifrows)
    status = (await client.get(f"/api/studies/{sid}/interface-requirements")).json()["status"]
    assert status["without_interface"] == []
    # proposing and syncing again adds nothing
    await client.post(f"/api/studies/{sid}/interfaces/propose")
    await client.post(f"/api/studies/{sid}/interface-requirements/sync")
    again = [q for q in await _reqs(client, sid) if str(q["code"]).startswith("IR-")]
    assert len(again) == len(auto)
    # the IR form: pick an interface and an exchange item, edit the text
    q = ifrows[0]
    items = (await client.get(f"/api/studies/{sid}/exchange-items")).json()
    r = await client.patch(f"/api/requirements/{q['id']}", json={"exchange_item_ids": [items[-1]["id"]],
                                                                 "text": q["text"] + " "})
    assert r.status_code == 200 and r.json()["ir_json"]["exchange_item_ids"] == [items[-1]["id"]]
