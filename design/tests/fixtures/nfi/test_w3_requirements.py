"""Wave 3 acceptance (agent R): functions and coverage (3.R1), threshold binding (3.R2),
allocation requirements (3.R3), gate criteria of the V (3.R4), agreed interface requirements
(3.R5) and ICD issue control (3.R6) on the Northern Fire and Ice v2 fixture.

Figures come from the fixture files (``load("functions")``, ``load("budgets")``); counts come from
the store.
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import load, seed_nfi

FUNCS = load("functions")


# ─────────────────────────────────────────────────────────────── 3.R1 functions

def _expected_functions() -> dict:
    fs = FUNCS["functions"]
    leaves = [f for f in fs if f["leaf"]]
    depth: dict[str, int] = {}
    for f in fs:
        depth[str(f["depth"])] = depth.get(str(f["depth"]), 0) + 1
    return {"functions": len(fs), "by_depth": depth, "leaves": len(leaves),
            "processes": len(FUNCS["enabling_processes"]), "exchanges": len(FUNCS["functional_interfaces"])}


@pytest.mark.asyncio
async def test_r1_function_import_and_coverage(client):
    exp = _expected_functions()
    assert (exp["functions"], exp["by_depth"], exp["leaves"], exp["processes"], exp["exchanges"]) == \
        (86, {"1": 13, "2": 70, "3": 3}, 72, 5, 37)          # the plan's figures, from the fixture
    s = await seed_nfi(client, "S1")
    rep = s.report["functions_import"]
    assert rep["functions"] == exp["functions"] and rep["by_depth"] == exp["by_depth"]
    assert rep["leaves"] == rep["leaves_allocated"] == exp["leaves"]
    assert rep["processes"] == exp["processes"] and rep["exchanges_created"] == exp["exchanges"]
    sid = s.study_id

    cov = (await client.get(f"/api/studies/{sid}/requirements/function-coverage")).json()
    counts = (await client.get(f"/api/studies/{sid}/requirements/counts")).json()
    spec_rows = counts["user"]                     # 302: every row but the needs and the OBJ-* rows
    assert cov["functions"] == exp["functions"] and cov["processes"] == exp["processes"]
    assert cov["leaves"] == cov["leaves_allocated"] == exp["leaves"]
    assert cov["leaves_without_requirement"] == []
    assert cov["requirements_without_function"] == []
    assert cov["requirements_with_function"] == cov["requirements"] == len(load("requirements")["requirements"])
    if spec_rows is not None:
        assert cov["requirements"] == spec_rows
    assert cov["subsystems_without_requirement"] == []

    # a function on several elements keeps all of them (F9.2: OBC, AOCS and EPS)
    fns = (await client.get(f"/api/studies/{sid}/functions")).json()
    f92 = next(f for f in fns if f["external_id"] == "F9.2")
    allocs = (await client.get(f"/api/functions/{f92['id']}/allocations")).json()
    assert len(allocs) == len(next(f for f in FUNCS["functions"] if f["id"] == "F9.2")["allocation"])

    # the allocation diagram has no gap
    cat = await client.get(f"/api/studies/{sid}/diagrams/allocation")
    if cat.status_code == 200:
        gaps = [g for g in cat.json().get("gaps") or [] if g.get("severity") != "info"]
        # the enabling processes (kind ``process``) are not allocated to products; until the
        # diagram leaves them out (hand-off to X) they are its only "unallocated" rows
        assert all(g["code"] == "unallocated" and g["count"] <= exp["processes"] for g in gaps), gaps

    # idempotent: a second import changes nothing
    again = (await client.post(f"/api/studies/{sid}/functions/import", json={"document": FUNCS})).json()
    assert again["created"] == 0 and again["updated"] == 0 and again["exchanges_created"] == 0

    # the picker: SYS-BUD-09 satisfied by F10.2 only, then by F10.2 and F10.1
    links = (await client.get(f"/api/studies/{sid}/requirements/function-links")).json()
    rid = s.requirements["SYS-BUD-09"]
    assert [x["code"] for x in links["links"][rid]] == ["F10.2"]
    ids = {f["external_id"]: f["id"] for f in fns}
    r = await client.put(f"/api/requirements/{rid}/functions", json={"function_ids": [ids["F10.2"], ids["F10.1"]]})
    assert r.status_code == 200, r.text
    assert sorted(r.json()["function_codes"]) == ["F10.1", "F10.2"]
    links = (await client.get(f"/api/studies/{sid}/requirements/function-links")).json()
    assert sorted(x["code"] for x in links["links"][rid]) == ["F10.1", "F10.2"]


# ─────────────────────────────────────────────────────────────── helpers

BUDGETS = load("budgets")
from tests.fixtures.nfi.seed import PDR_ICDS  # noqa: E402


@pytest.fixture(autouse=True)
def _logbook(monkeypatch, tmp_path):
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(tmp_path / "logbook"))


async def _ledger(sid: str, *, unagreed: tuple[str, ...] = (), skip: tuple[tuple[str, str], ...] = ()) -> dict:
    """The mass and power lines of ``budgets.yaml`` in the allocation ledger (A's table, 3.A2),
    written directly, replacing the lines the seed imported (A's ``_s2_allocations``), so the
    test controls every line. Returns {(type, code): line id}."""
    from sqlalchemy import delete

    from spacecdf_server.db.engine import get_session_factory
    from spacecdf_server.db.models_alloc import AllocationLedgerRow
    from spacecdf_server.services.requirement_queries import element_code_map
    codes = await element_code_map(sid)
    ids = {}
    async with get_session_factory()() as s:
        await s.execute(delete(AllocationLedgerRow).where(AllocationLedgerRow.study_id == sid))
        n = 0
        for btype, src, unit in (("mass", BUDGETS["mass"]["allocations"], "kg"),
                                 ("power_avg", BUDGETS["power"]["allocations"], "W")):
            for code, value in src.items():
                if (btype, code) in skip:
                    continue
                n += 1
                lid = f"al{sid[:8]}{n:03d}"
                ids[(btype, code)] = lid
                s.add(AllocationLedgerRow(id=lid, study_id=sid, element_id=codes[code], element_code=code,
                                          budget_type=btype, value=float(value), unit=unit, order=n,
                                          status="proposed" if code in unagreed else "agreed"))
        await s.commit()
    return ids


async def _set_line(lid: str, **kw) -> None:
    from spacecdf_server.db.engine import get_session_factory
    from spacecdf_server.db.models_alloc import AllocationLedgerRow
    async with get_session_factory()() as s:
        row = await s.get(AllocationLedgerRow, lid)
        if kw.pop("_delete", False):
            await s.delete(row)
        for k, v in kw.items():
            setattr(row, k, v)
        await s.commit()


async def _gate(client, sid: str, gate: str) -> dict:
    """The gate evaluation with fresh wave-3 evidence (GET …/gate-evidence keeps it for the study
    until the gate route passes it itself: hand-off to D)."""
    from spacecdf_server.routers.gates import evaluate_study_gate
    assert (await client.get(f"/api/studies/{sid}/gate-evidence")).status_code == 200
    res = await evaluate_study_gate(sid, gate)
    return {c["id"]: c for c in res["criteria"]}


# ─────────────────────────────────────────────────────────────── 3.R2 binding

@pytest.mark.asyncio
async def test_r2_threshold_binding(client):
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    b = (await client.get(f"/api/studies/{sid}/requirements/bindings")).json()
    rows = {r["code"]: r for r in b["rows"]}
    with_ref = [r for r in load("requirements")["requirements"] if r.get("budget_ref")]
    assert len(with_ref) == 62
    proposed = [r for r in b["rows"] if r["proposal"] and r["proposal"]["reason"] == "budget_ref"]
    assert len(proposed) >= 30
    for code in ("SYS-BUD-01", "SYS-BUD-02", "SYS-BUD-03", "SYS-BUD-05", "SYS-BUD-06", "SYS-BUD-09", "SYS-BUD-10"):
        assert rows[code]["proposal"] and rows[code]["accepted"], code     # accepted by the seed (_s1_bindings)
    # after accept the compliance tracker evaluates them against the computed figures
    closure_m, closure_p = BUDGETS["mass"]["closure"], BUDGETS["power"]["closure"]
    assert rows["SYS-BUD-09"]["status"] == "pass"
    assert rows["SYS-BUD-09"]["achieved"] == pytest.approx(closure_m["with_system_margin_kg"], abs=1e-3)   # 5.316 ≤ 6.0
    assert rows["SYS-BUD-10"]["status"] == "pass"
    assert rows["SYS-BUD-10"]["achieved"] == pytest.approx(closure_p["with_system_margin_w"], abs=1e-3)    # 5.892 ≤ 12.2
    for code, sub in BUDGETS["mass"]["subsystems"].items():
        r = rows[sub["requirement"]]
        assert r["achieved"] == pytest.approx(sub["margined_kg"], abs=2e-3) and r["status"] == "pass", code
    # a keyword guess is offered but not taken in bulk; a hand binding is kept, then cleared
    assert rows["DIS-SAIL-03"]["proposal"]["reason"] == "keywords" and not rows["DIS-SAIL-03"]["current_path"]
    rid = s.requirements["SYS-BUD-04"]
    r = await client.put(f"/api/requirements/{rid}/binding", json={"path": "budget.data_margin_percent"})
    assert r.status_code == 200 and r.json()["threshold_param_path"] == "budget.data_margin_percent"
    again = (await client.post(f"/api/studies/{sid}/requirements/bindings/accept", json={})).json()
    assert again["accepted"] == 0
    r = await client.put(f"/api/requirements/{rid}/binding", json={"path": None})
    assert r.json()["threshold_param_path"] is None
    # SRR-EC-02 passes on every row (acceptance text in place of a numeric threshold)
    by = await _gate(client, sid, "srr")
    p = by["SRR-EC-02"]["evidence_params"]
    assert by["SRR-EC-02"]["status"] == "pass" and p["ok"] == p["total"]


# ─────────────────────────────────────────────────────────────── 3.R3 AR-01

@pytest.mark.asyncio
async def test_r3_allocation_requirements_follow_the_ledger(client):
    s = await seed_nfi(client, "S2")
    sid = s.study_id
    ids = await _ledger(sid)
    rep = (await client.post(f"/api/studies/{sid}/requirements/allocation-sync")).json()
    assert rep["created"] == [] and rep["stale"] == [] and rep["retired"] == []
    st = (await client.get(f"/api/studies/{sid}/requirements/allocation-sync")).json()
    by = {(x["budget_type"], x["element_code"]): x for x in st["lines"]}
    assert by[("mass", "PAY")]["requirement_code"] == "PAY-BUD-01" and by[("mass", "PAY")]["state"] == "covered"
    nil = [k for k, v in BUDGETS["power"]["allocations"].items() if not v]
    assert st["counts"]["uncovered"] == 0 and st["counts"]["nil"] == len(nil)          # STR 0 W needs no row

    # the EPS mass allocation grows 1.75 -> 1.80 kg: EPS-BUD-01 is stale and proposes 1.80, logged
    await _set_line(ids[("mass", "EPS")], value=1.80)
    rep = (await client.post(f"/api/studies/{sid}/requirements/allocation-sync")).json()
    assert rep["stale"] == ["EPS-BUD-01"]
    row = (await client.get(f"/api/requirements/{s.requirements['EPS-BUD-01']}")).json()
    flag = row["external_ids"]["allocation_sync"]
    assert flag["state"] == "stale" and flag["proposed_value"] == 1.80 and flag["log"][-1]["to"] == 1.80
    from spacecdf_server.seats import store
    assert any(e["action"] == "allocation_changed" and e["target"] == "EPS-BUD-01" for e in store._events_mem)
    r = await client.post(f"/api/requirements/{s.requirements['EPS-BUD-01']}/allocation-sync", json={"action": "accept"})
    assert r.status_code == 200 and float(r.json()["threshold_value"]) == 1.80

    # the THM mass line is deleted: THM-BUD-01 is flagged "allocation retired"
    await _set_line(ids[("mass", "THM")], _delete=True)
    rep = (await client.post(f"/api/studies/{sid}/requirements/allocation-sync")).json()
    assert rep["retired"] == ["THM-BUD-01"]

    # a line no row covers gets an AR row (IF-01 pattern), parent from the system budget rows
    from spacecdf_server.db.engine import get_session_factory
    from spacecdf_server.db.models_alloc import AllocationLedgerRow
    from spacecdf_server.services.requirement_queries import element_code_map
    har = (await element_code_map(sid))["HAR"]
    async with get_session_factory()() as db:
        db.add(AllocationLedgerRow(id=f"al{sid[:8]}har", study_id=sid, element_id=har, element_code="HAR",
                                   budget_type="mass", value=0.12, unit="kg", status="proposed"))
        await db.commit()
    rep = (await client.post(f"/api/studies/{sid}/requirements/allocation-sync")).json()
    assert rep["created"] == ["AR-MASS-HAR"]
    tree = (await client.get(f"/api/requirements/tree?study_id={sid}")).json()
    ar = next(r for r in tree if r["code"] == "AR-MASS-HAR")
    assert ar["parent_id"] == s.requirements["SYS-BUD-09"] and ar["threshold_op"] == "<=" and ar["element_id"] == har
    again = (await client.post(f"/api/studies/{sid}/requirements/allocation-sync")).json()
    assert again["created"] == [] and again["stale"] == [] and again["retired"] == []


# ─────────────────────────────────────────────────────────────── 3.R4 gate criteria

@pytest.mark.asyncio
async def test_r4_gate_criteria_of_the_v(client):
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    srr = await _gate(client, sid, "srr")
    assert srr["SRR-EC-12"]["status"] == "pass"
    assert srr["SRR-EC-12"]["priority"] == "should_pass"
    prr = await _gate(client, sid, "prr")
    assert prr["PRR-EC-03"]["status"] == "pass"
    assert prr["PRR-EC-03"]["evidence_params"]["allocated"] == prr["PRR-EC-03"]["evidence_params"]["leaves"] == 72
    qr = await _gate(client, sid, "qr")
    assert "OBJ-" not in str(qr["QR-EC-01"]["evidence_params"].get("codes", ""))

    # PDR-EC-07 passes on the ledger the seed imported, agreed by its owners (A, 3.A2); it fails
    # naming EPS until the Power seat agrees, then passes (5.316 ≤ 6.0 kg; 5.892 ≤ 12.2 W)
    pdr = await _gate(client, sid, "pdr")
    assert pdr["PDR-EC-07"]["status"] == "pass" and pdr["PDR-EC-07"]["priority"] == "must_pass"
    assert pdr["PDR-EC-08"]["status"] == "pass" and pdr["PDR-EC-08"]["priority"] == "must_pass"
    ids = await _ledger(sid, unagreed=("EPS",))
    pdr = await _gate(client, sid, "pdr")
    assert pdr["PDR-EC-07"]["status"] == "fail" and pdr["PDR-EC-07"]["evidence_params"]["names"] == "EPS"
    for t in ("mass", "power_avg"):
        await _set_line(ids[(t, "EPS")], status="agreed")
    pdr = await _gate(client, sid, "pdr")
    c = pdr["PDR-EC-07"]
    assert c["status"] == "pass", c["evidence_found"]
    assert (c["evidence_params"]["mass"], c["evidence_params"]["mlimit"]) == ("5.316", "6.0")
    assert (c["evidence_params"]["power"], c["evidence_params"]["plimit"]) == ("5.892", "12.2")

    # SRR-EC-04: every trade due by the SRR is decided in the Decide panel; personal logbooks
    # are never read (PI ruling)
    trades = (await client.get(f"/api/studies/{sid}/trades")).json()["items"]
    due = [t for t in trades if str(t["state"].get("gate") or "").lower() in ("mdr", "prr", "srr")]
    assert due, "the seed has trades due by the SRR"
    open_ = [t for t in due if t["state"].get("status") != "decided"]
    c = srr["SRR-EC-04"]
    assert c["evidence_params"].get("total", len(due)) == len(due)
    assert c["status"] == ("fail" if open_ else "pass"), c["evidence_found"]
    for t in open_:
        r = await client.post(f"/api/studies/{sid}/trades/{t['id']}/decision",
                              json={"selected": t["state"]["options"][0], "rationale": "Closes the trade."})
        assert r.status_code == 200, r.text
    srr = await _gate(client, sid, "srr")
    assert srr["SRR-EC-04"]["status"] == "pass", srr["SRR-EC-04"]["evidence_found"]
    r = await client.post("/api/logbook/entries", json={       # a logbook record changes nothing
        "kind": "decision", "tool": "design", "text": "Decision D-3.1-EPS",
        "context": {"study_id": sid, "decision_id": "D-3.1-EPS"},
        "record": {"decision_id": "D-3.1-EPS", "choice": "Option A", "rationale": "Private note."}})
    assert r.status_code == 201, r.text
    assert (await _gate(client, sid, "srr"))["SRR-EC-04"]["evidence_params"] == srr["SRR-EC-04"]["evidence_params"]


def test_r4_validation_criteria_read_the_validation_coverage():
    """SRR-EC-13 (should) and FRR-EC-01 (must) on the shape of S's validation coverage: the
    v2 primary objectives O1, O3 and O4 (from the fixture) each with a stakeholder-performed and
    an in-orbit activity."""
    from spacecdf_server.services import gate_evaluator as ge
    objs = [{"id": o["id"], "priority": o["priority"], "measurable_criterion": o.get("measure", "")}
            for o in load("requirements")["objectives"]]
    prim = [o["id"] for o in objs if o["priority"] == "primary"]
    assert prim == ["O1", "O3", "O4"]
    items = [{"objective_id": o, "activities": [{"id": f"V-{o}", "performer_kind": "stakeholder", "stage": "IOV"}]}
             for o in prim]
    need = {"objectives": objs}
    for gate, cid in (("srr", "SRR-EC-13"), ("frr", "FRR-EC-01")):
        by = {c["id"]: c for c in ge.evaluate_gate(gate, mission_need=need, evidence={"validation": {"items": items}})["criteria"]}
        assert by[cid]["status"] == "pass", by[cid]
        part = {c["id"]: c for c in ge.evaluate_gate(gate, mission_need=need,
                                                      evidence={"validation": {"items": items[:2]}})["criteria"]}
        assert part[cid]["status"] == "fail" and part[cid]["evidence_params"]["ids"] == "O4"
    assert {c["id"]: c for c in ge.evaluate_gate("frr")["criteria"]}["FRR-EC-01"]["priority"] == "must_pass"


# ─────────────────────────────────────────────────────────────── 3.R5 / 3.R6 ICDs

@pytest.mark.asyncio
async def test_r5_r6_icds_at_issue_a_signed_by_both_seats(client):
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    # the seed (end of S3) put the five ICDs the v2 PDR needs under issue control, as drafts
    st = (await client.get(f"/api/studies/{sid}/icds")).json()
    assert st["inventory"] == sorted(PDR_ICDS) and st["counts"]["at_issue_a"] == 0
    r = await client.post(f"/api/studies/{sid}/icds/inventory", json={"icd_refs": list(PDR_ICDS)})
    assert r.status_code == 200 and r.json()["declared"] == []          # idempotent
    pdr = await _gate(client, sid, "pdr")
    c = pdr["PDR-EC-02"]
    assert c["status"] == "fail" and c["evidence_params"]["agreed"] == 0 and c["evidence_params"]["total"] == 5
    assert all(k in c["evidence_params"]["unsigned"] for k in PDR_ICDS)

    # a draft cannot be signed; Issue A is raised, then each seat signs its side
    assert (await client.post(f"/api/studies/{sid}/icds/ICD-SAIL/signoff", json={})).status_code == 409
    for k in PDR_ICDS:
        r = await client.post(f"/api/studies/{sid}/icds/{k}/issue", json={"change_note": "Issue A for the PDR"})
        assert r.status_code == 200 and r.json()["issue"] == "A" and r.json()["state"] == "issue_a"
    st = (await client.get(f"/api/studies/{sid}/icds")).json()
    sail = next(i for i in st["items"] if i["icd_ref"] == "ICD-SAIL")
    assert (sail["provider_seat"], sail["consumer_seat"]) == ("propulsion_engineer", "power_engineer")
    for k in PDR_ICDS[:4]:
        for side in ("provider", "consumer"):
            r = await client.post(f"/api/studies/{sid}/icds/{k}/signoff", json={"side": side})
            assert r.status_code == 200
    r = await client.post(f"/api/studies/{sid}/icds/ICD-SPACE-GROUND/signoff", json={"side": "provider"})
    assert r.json()["agreed"] is False and r.json()["unsigned"] == ["mission_analyst"]
    pdr = await _gate(client, sid, "pdr")
    assert pdr["PDR-EC-02"]["status"] == "fail"
    assert pdr["PDR-EC-02"]["evidence_params"]["unsigned"] == "mission_analyst: ICD-SPACE-GROUND (A)"
    await client.post(f"/api/studies/{sid}/icds/ICD-SPACE-GROUND/signoff", json={"side": "consumer"})
    pdr = await _gate(client, sid, "pdr")
    assert pdr["PDR-EC-02"]["status"] == "pass", pdr["PDR-EC-02"]["evidence_found"]

    # a change to a row of a signed ICD makes its sign-offs stale; Issue B is signed again
    rid = s.requirements["IF-DIS-EPS-01"]
    old = (await client.get(f"/api/requirements/{rid}")).json()["text"]
    assert (await client.patch(f"/api/requirements/{rid}", json={"text": old + " (rev)"})).status_code == 200
    st = (await client.get(f"/api/studies/{sid}/icds")).json()
    sail = next(i for i in st["items"] if i["icd_ref"] == "ICD-SAIL")
    assert sail["agreed"] is False and sail["stale"] is True
    r = await client.post(f"/api/studies/{sid}/icds/ICD-SAIL/issue", json={"change_note": "release timer"})
    assert r.json()["issue"] == "B"
    await client.post(f"/api/studies/{sid}/icds/ICD-SAIL/signoff", json={"side": "both"})
    hist = (await client.get(f"/api/studies/{sid}/icds/ICD-SAIL/history")).json()["items"]
    assert [(h["issue"], h["state"]) for h in hist] == [("", "superseded"), ("A", "superseded"), ("B", "issue_b")]
    r = await client.post(f"/api/studies/{sid}/icds/ICD-SAIL/issue", json={"baseline": True})
    assert r.status_code == 200 and r.json()["state"] == "baselined"

    # the agreement state survives a round trip (project file export -> import)
    doc = (await client.get(f"/api/studies/{sid}/export")).json()
    new = (await client.post("/api/studies/import", json=doc)).json()["id"]
    st2 = (await client.get(f"/api/studies/{new}/icds")).json()
    keep = ("icd_ref", "issue", "revision", "state", "agreed", "provider_seat", "consumer_seat", "signed")
    assert [{k: i[k] for k in keep} for i in st2["items"]] == [{k: i[k] for k in keep}
                                                                for i in (await client.get(f"/api/studies/{sid}/icds")).json()["items"]]
    sec = (await client.get(f"/api/studies/{sid}/export-context?sections=icds")).json()
    assert (sec.get("icds") or sec.get("sections", {}).get("icds", {})).get("counts", {}).get("agreed") == 5
