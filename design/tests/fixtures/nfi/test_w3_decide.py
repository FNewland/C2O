"""Wave 3, agent D (gates, Phase inventory, trades, open items, ConOps scenarios, risks, change
control) acceptance on the Northern Fire and Ice v2 fixture.

3.D1 protocol enforcement at review start (warn by default, block on the instructor's setting),
baseline kinds; PI addendum: the SRR and PDR review-readiness criteria pass only once the
evidence exists in the tool; 3.D3 the v2 system and architecture trades; 3.D4 the open-item
register; 3.D5 the ConOps scenarios; 3.D6 the v2 risk register; 3.D7 the change-control flow of
ECP-01 and ECP-02. Every figure comes from the fixture files (``load``), never retyped.
"""
from __future__ import annotations

import io
import re
from uuid import uuid4

import pytest
from docx import Document

from tests.fixtures.nfi import load, seed_nfi
from tests.fixtures.nfi.seed import OPEN_DECISION_GATES, PI_RULINGS, SYSTEM_TRADE_CHOICE


def _text(blob: bytes) -> str:
    d = Document(io.BytesIO(blob))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.extend(c.text for c in row.cells)
    return "\n".join(parts)


@pytest.fixture()
async def s3(client):
    return await seed_nfi(client, "S3")


async def _changes(sid: str, *codes: str) -> dict[str, str]:
    """The v2 change records (``risks.yaml``) as L's register holds them: the seed imports them at
    S3 (3.L4, ``_s3_changes``, with the decision gates ECP-01 PDR, ECP-02 SRR, CR-V2 PDR); a
    record still missing is inserted, so D's flow is tested on its own. Returns code -> id."""
    from sqlalchemy import select

    from spacecdf_server.db.engine import get_session_factory
    from spacecdf_server.db.models_changes import ChangeProposalRow
    recs = {c["id"]: c for c in load("risks")["configuration_management"]["change_records"]}
    gates = {"ECP-01": "pdr", "ECP-02": "srr", "CR-V2": "pdr"}
    out = {}
    async with get_session_factory()() as s:
        have = {r.code: r for r in (await s.execute(select(ChangeProposalRow).where(
            ChangeProposalRow.study_id == sid))).scalars().all()}
        for i, code in enumerate(codes):
            if code in have:
                assert have[code].decision_gate == gates[code], (code, have[code].decision_gate)
                out[code] = have[code].id
                continue
            r = recs[code]
            rid = uuid4().hex[:16]
            s.add(ChangeProposalRow(id=rid, study_id=sid, code=code, kind="ecp" if code.startswith("ECP") else "cr",
                                    title=r["title"], change_class=r["class_"], description=r["impact"],
                                    affected_codes_json=list(r["affected"]), source_trade=r["source"],
                                    status="proposed", decision_gate=gates[code], order=i))
            out[code] = rid
        await s.commit()
    return out


# ─── 3.D3 system-level and architecture trades ─────────────────────────────

async def test_v2_trades_levels_gates_and_sensitivity(client, s3):
    sid, data = s3.study_id, load("trades")
    items = {i["id"]: i for i in (await client.get(f"/api/studies/{sid}/trades")).json()["items"]}
    v2 = {t["id"]: t for t in [*data["system_trades"], *data["architecture_trades"]]}
    assert set(v2) | {t["id"] for t in data["trades"]} == set(items)
    for tid, t in v2.items():
        it = items[tid]
        st, ev = it["state"], it["evaluation"]
        assert st["method"] == "absolute_scale" and st["gate"] == t["gate"].lower()
        assert st["screened"] == t["screened"] and st["dissent"] == t["dissent"]
        assert st["acceptance_conditions"] == t["acceptance_conditions"]
        assert all(st["criteria_meta"][c["name"]]["source"] == c["moe"] for c in t["criteria"])
        tot = {x["option"]: x["weighted"] for x in ev["totals"]}
        assert tot == pytest.approx(t["result"]["totals"], abs=0.01)
        assert ev["winner"] == t["result"]["winner"] and ev["runner_up"] == t["result"]["runner_up"]
        assert ev["robust_pm20"] is t["result"]["robust_to_pm20pct"]
        assert ev["break_even"] == t["result"]["break_even"]
        assert ev["ranking_eligible"] == t["result"]["ranking_eligible"]
        assert ev["issues"] == []
        assert st["status"] == ("decided" if tid in SYSTEM_TRADE_CHOICE else "open")
    m01 = items["T-M01"]["evaluation"]
    tot = {x["option"]: x["weighted"] for x in m01["totals"]}
    assert tot["A"] == pytest.approx(4.25, abs=0.01) and tot["B"] == pytest.approx(4.20, abs=0.01)
    assert items["T-M01"]["state"]["level"] == "mission" and items["T-S01"]["state"]["level"] == "system"
    a01 = {x["option"]: x["weighted"] for x in items["T-A01"]["evaluation"]["totals"]}
    assert a01["C"] > a01["A"] and items["T-A01"]["state"]["level"] == "architecture"
    # the eight v1 trades load as subsystem trades (Pugh), with their subsystem kept
    for t in data["trades"]:
        assert items[t["id"]]["state"]["level"] == "subsystem" and items[t["id"]]["state"]["method"] == "pugh_weighted"
    # Decide summary by gate (PI ruling): MDR 2 (2 decided), SRR 1 (1), PDR 2 (1 undecided)
    summ = (await client.get(f"/api/studies/{sid}/trades/summary")).json()
    bg = summ["by_gate"]
    assert (bg["mdr"]["total"], bg["mdr"]["decided"]) == (2, 2)
    assert (bg["srr"]["total"], bg["srr"]["decided"]) == (1, 1)
    assert (bg["pdr"]["total"], bg["pdr"]["undecided"]) == (2, ["T-A01"])
    assert summ["deliverables"]["mdr"]["state"] == "ok" and summ["deliverables"]["pdr"]["state"] == "warn"
    # a screened option cannot be selected
    r = await client.post(f"/api/studies/{sid}/trades/T-M01/decision", json={"selected": "F"})
    assert r.status_code == 422 and "screened" in r.text
    # weights lock at the first score: a later change is kept but flagged
    st = items["T-S01"]["state"]
    w = {c: 1.0 for c in st["criteria"]}
    r = await client.put(f"/api/studies/{sid}/trades/T-S01", json={"state": {"weights": w}, "version": items["T-S01"]["version"]})
    assert r.status_code == 200
    st2 = r.json()["state"]
    assert st2["post_hoc_weights"] is True and len(st2["weight_history"]) == 1
    assert "weights changed after scoring" in r.json()["evaluation"]["issues"]
    # the trade-off report carries level, gate, sources and the ±20 % sensitivity
    text = _text((await client.post(f"/api/studies/{sid}/trades/report")).content)
    assert "Sensitivity to ±20 % on each weight" in text and "MOE-01" in text and "Break-even" in text
    assert "T-M01" in text and "mission" in text and "MDR" in text
    fr = _text((await client.post(f"/api/studies/{sid}/trades/report?lang=fr")).content)
    assert "Sensibilité à ±20 % sur chaque poids" in fr and "×0,8" in fr


async def test_record_as_trade_from_the_orbit_tool(client, study_obj):
    sid = study_obj.id
    r = await client.post(f"/api/studies/{sid}/trades/from-tool", json={
        "tool": "orbit", "title": "Altitude candidates",
        "options": [{"id": "A", "label": "590 km", "metrics": {"Union contact (min/day)": 125.7, "Life without sail (y)": 14.7}},
                    {"id": "B", "label": "550 km", "metrics": {"Union contact (min/day)": 117.6, "Life without sail (y)": 6.0}}]})
    assert r.status_code == 200, r.text
    t = r.json()
    st = t["state"]
    assert t["id"] == "T-M01" and st["level"] == "mission" and st["gate"] == "mdr" and st["method"] == "absolute_scale"
    assert st["criteria"] == ["Union contact (min/day)", "Life without sail (y)"]
    assert "125.7" in st["evidence_by_criterion"]["Union contact (min/day)"]
    assert "criteria without a source" in " ".join(t["evaluation"]["issues"])


# ─── 3.D4 open-item register ──────────────────────────────────────────────

async def test_open_item_register_and_conditional_decisions(client, s3):
    sid = s3.study_id
    decisions = load("NUMBERS")["open_decisions"]
    reg = (await client.get(f"/api/studies/{sid}/open-items?include_closed=true")).json()
    stored = {i["code"]: i for i in reg["items"] if i["source"] == "register"}
    assert set(stored) == {d["id"] for d in decisions}
    for code, ruling in PI_RULINGS.items():
        assert stored[code]["status"] == "closed" and stored[code]["resolution"] == ruling
        assert stored[code]["kind"] == "pi_decision"
    still = {d["id"] for d in decisions} - set(PI_RULINGS)
    assert {c for c, i in stored.items() if i["status"] == "open"} == still
    assert stored["D-PAY-01"]["owner_seat"] == "payload_lead" and stored["D-GND-01"]["owner_seat"] == "mission_analyst"
    # T-07 is a conditional decision; the register shows it once, as D-COM-01, with its condition
    t07 = (await client.get(f"/api/studies/{sid}/trades/T-07")).json()["state"]["decision"]
    assert t07["condition"].startswith("450.25 MHz receive edge confirmed") and t07["fallback"] == "AX100UL + R0405"
    assert t07["risks"] == ["RSK-001", "RSK-010"]
    com = stored["D-COM-01"]
    assert com["condition"] == t07["condition"] and com["links"]["risks"] == ["RSK-001", "RSK-010"]
    assert not any(i["kind"] == "conditional_decision" and i["code"] == "D-COM-01" for i in reg["items"])
    # the PDR checklist lists ECP-01 and D-PAY-01 (and T-A01, undecided); the SRR one does not
    ids = await _changes(sid, "ECP-01", "ECP-02")
    pdr = (await client.get(f"/api/studies/{sid}/rules/gates/pdr")).json()
    codes = {i["code"] for i in pdr["open_items"]}
    assert {"ECP-01", "D-PAY-01", "T-A01", "ECP-02"} <= codes
    srr = {i["code"] for i in (await client.get(f"/api/studies/{sid}/open-items?blocks_gate=srr")).json()["items"]}
    assert "ECP-02" in srr and "ECP-01" not in srr and "D-PAY-01" not in srr
    exact = (await client.get(f"/api/studies/{sid}/open-items?blocks_gate=pdr&exact=true")).json()
    assert {i["blocks_gate"] for i in exact["items"]} == {"pdr"}
    assert set(OPEN_DECISION_GATES.values()) >= {"pdr"}
    # close a stored item; RIDs and changes are not editable here
    r = await client.patch(f"/api/studies/{sid}/open-items/{stored['D-GND-01']['id']}",
                           json={"status": "closed", "resolution": "Noise survey done: +1.2 dB at 10 deg"})
    assert r.status_code == 200 and r.json()["status"] == "closed"
    assert (await client.patch(f"/api/studies/{sid}/open-items/change:{ids['ECP-01']}", json={})).status_code == 409
    bad = await client.post(f"/api/studies/{sid}/open-items", json={"title": "x", "blocks_gate": "zzz"})
    assert bad.status_code == 422
    # a conflict resolved with a rationale and a seat is kept in the register
    from spacecdf_server.db.engine import get_session_factory
    from spacecdf_server.db.models import AnalysisConflictRow
    async with get_session_factory()() as s:
        s.add(AnalysisConflictRow(id="cf-nfi-01", study_id=sid, analysis="physics", code="CONF-PWR-001",
                                  title="Peak power above the array", detail="12 W payload peak in imaging"))
        await s.commit()
    r = await client.post("/api/conflicts/cf-nfi-01/resolve", json={"rationale": "Battery covers the peak (N3)",
                                                                     "seat": "Power"})
    assert r.status_code == 200 and r.json()["resolved_at"]
    res = r.json()["resolution"]
    assert res["kind"] == "conflict_resolution" and res["owner_seat"] == "power_engineer" and res["status"] == "closed"
    assert (await client.post("/api/conflicts/cf-nfi-01/resolve")).status_code == 200   # old body-less call
    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=open_items")).json()["open_items"]
    assert sx["counts"]["closed"] >= 4 and "pdr" in sx["by_gate"]


# ─── 3.D5 ConOps scenarios ────────────────────────────────────────────────

async def test_conops_scenarios(client, s3):
    sid = s3.study_id
    plan = load("vv_plan")["conops_scenarios_for_requirements_validation"]
    view = (await client.get(f"/api/studies/{sid}/conops/scenarios")).json()
    assert view["counts"]["total"] == len(plan) == 12
    for sc, p in zip(view["items"], plan):
        assert sc["id"] == p["id"] and sc["requirement_codes"] == p["requirements"]
        assert len(sc["requirements"]) >= 1 and sc["missing"] == [], (sc["id"], sc["missing"])
    kinds = {sc["id"]: sc["kind"] for sc in view["items"]}
    assert kinds["S1"] == "nominal" and kinds["S7"] == "degraded" and kinds["S9"] == "end_of_life"
    text = _text((await client.post(f"/api/studies/{sid}/conops/document")).content)
    assert "11 Operational scenarios" in text and "LEOP" in text
    s1 = plan[0]
    sec = text[text.index("11.1 S1"):]
    for code in s1["requirements"]:
        assert code in sec
    assert len(s1["requirements"]) == 8
    # edit and validation
    edited = [{**x, "requirement_codes": x["requirement_codes"]} for x in view["items"]][:3]
    edited[2]["kind"] = "contingency"
    r = await client.put(f"/api/studies/{sid}/conops/scenarios", json={"scenarios": edited})
    assert r.status_code == 200 and r.json()["counts"]["total"] == 3 and r.json()["counts"]["by_kind"]["contingency"] == 1
    assert (await client.put(f"/api/studies/{sid}/conops/scenarios",
                             json={"scenarios": [{"id": "X", "kind": "weird"}]})).status_code == 422


# ─── 3.D6 risk register v2 ────────────────────────────────────────────────

async def test_risk_register_v2_residual_and_seats(client, s3):
    sid = s3.study_id
    rows = load("risks")["risks"]
    risks = (await client.get(f"/api/studies/{sid}/risks")).json()
    assert len(risks) == len(rows) == 37
    assert all(r["residual_likelihood"] and r["residual_consequence"] and r["owner_seat"] for r in risks)
    r1 = next(r for r in risks if r["id"] == "RSK-001")
    assert (r1["likelihood"], r1["consequence"], r1["residual_likelihood"], r1["residual_consequence"]) == (4, 4, 3, 3)
    assert r1["owner_seat"] == "comms_engineer" and r1["residual_rpn"] == 9
    for posted, y in zip(risks, rows):
        assert [posted["residual_likelihood"], posted["residual_consequence"]] == list(y["residual"])


async def test_scenarios_risks_and_trades_round_trip(client, s3):
    sid = s3.study_id
    a = (await client.get(f"/api/studies/{sid}/export")).json()
    res = (await client.post("/api/studies/import", json=a)).json()
    new = res["id"]
    assert len((await client.get(f"/api/studies/{new}/conops/scenarios")).json()["items"]) == 12
    rk = (await client.get(f"/api/studies/{new}/risks")).json()
    assert sum(1 for r in rk if r["residual_rpn"]) == 37
    tr = {i["id"]: i for i in (await client.get(f"/api/studies/{new}/trades")).json()["items"]}
    assert tr["T-M01"]["state"]["gate"] == "mdr" and tr["T-07"]["state"]["decision"]["fallback"] == "AX100UL + R0405"
    oi = (await client.get(f"/api/studies/{new}/open-items?include_closed=true")).json()
    assert {i["code"] for i in oi["items"] if i["source"] == "register"} >= set(PI_RULINGS)


# ─── 3.D1 enforcement, order, baseline kinds ──────────────────────────────

async def test_gate_start_enforcement_warn_and_block(client):
    s1 = await seed_nfi(client, "S1")
    sid = s1.study_id
    assert (await client.get(f"/api/studies/{sid}/gate-enforcement")).json()["mode"] == "warn"
    assert (await client.put(f"/api/studies/{sid}/gate-enforcement", json={"mode": "loud"})).status_code == 422
    r = await client.put(f"/api/studies/{sid}/gate-enforcement", json={"mode": "block"})
    assert r.status_code == 200 and r.json()["mode"] == "block" and r.json()["source"] == "study"
    # S1, no trade: block refuses the MDR start and names the system-trade deliverable
    r = await client.post(f"/api/studies/{sid}/gates/mdr/review", json={"action": "start"})
    assert r.status_code == 409
    det = r.json()["detail"]
    # (since S's protocol landed the deliverables come from se_deliverables; the system trades
    # of the MDR are one of the missing items at S1)
    assert det["code"] == "deliverables_missing" and det["items"]
    assert any("trade" in str(i.get("id") or "") or i.get("kind") == "trade" for i in det["items"]), det["items"]
    inv = (await client.get(f"/api/studies/{sid}/gates/mdr/inventory")).json()
    assert {f["id"] for f in inv["findings"]} >= {i["id"] for i in det["items"] if i.get("code") != "entry_missing"} \
        and inv["baseline_kind"] == "mission"


async def test_gate_start_order_warnings_and_baseline_kind(client, s3):
    sid = s3.study_id
    # warn (default): PRR before the MDR passed starts, and the history keeps the warning
    r = await client.post(f"/api/studies/{sid}/gates/prr/review", json={"action": "start"})
    assert r.status_code == 200, r.text
    warns = r.json()["warnings"]
    order = [w for w in warns if w["code"] == "out_of_order"]
    assert len(order) == 1 and order[0]["id"] == "mdr", warns
    assert "out_of_order" in [w["code"] for w in r.json()["history"][-1]["warnings"]]
    await client.post(f"/api/studies/{sid}/gates/prr/review", json={"action": "cancel"})
    # block: the same start is refused, out of order
    await client.put(f"/api/studies/{sid}/gate-enforcement", json={"mode": "block"})
    r = await client.post(f"/api/studies/{sid}/gates/prr/review", json={"action": "start"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "out_of_order"
    # block: MDR with its system trades removed is refused (deliverable missing)
    trades = (await client.get(f"/api/studies/{sid}/trades")).json()["items"]
    saved = {i["id"]: i["state"] for i in trades if i["id"] in ("T-M01", "T-M02")}
    for tid in saved:
        await client.delete(f"/api/studies/{sid}/trades/{tid}")
    r = await client.post(f"/api/studies/{sid}/gates/mdr/review", json={"action": "start"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "deliverables_missing"
    # warn: it starts, with the warning in the history
    await client.put(f"/api/studies/{sid}/gate-enforcement", json={"mode": "warn"})
    r = await client.post(f"/api/studies/{sid}/gates/mdr/review", json={"action": "start"})
    assert r.status_code == 200 and any("trade" in str(w["id"]) or w.get("kind") == "trade" for w in r.json()["warnings"]), r.json()["warnings"]
    await client.post(f"/api/studies/{sid}/gates/mdr/review", json={"action": "cancel"})
    # off: the behaviour before wave 3, no warnings
    await client.put(f"/api/studies/{sid}/gate-enforcement", json={"mode": "off"})
    r = await client.post(f"/api/studies/{sid}/gates/mdr/review", json={"action": "start"})
    assert r.status_code == 200 and "warnings" not in r.json()
    r = await client.post(f"/api/studies/{sid}/gates/mdr/review", json={"action": "pass"})
    assert r.status_code == 200 and r.json()["baselines"][-1]["kind"] == "mission"
    assert r.json()["baseline_kind"] == "mission"
    srr = (await client.get(f"/api/studies/{sid}/rules/gates/srr")).json()
    assert srr["baseline_kind"] == "functional"
    assert (await client.get(f"/api/studies/{sid}/rules/gates/pdr")).json()["baseline_kind"] == "allocated"


# ─── PI addendum: SRR and PDR pass legitimately once the evidence exists ──

async def test_srr_and_pdr_readiness_pass_only_with_the_evidence(client, s3):
    """D's readiness criteria left after the integration (SEMP, debris, ICDs and reliability/FMEA
    are R's YAML criteria SRR-EC-09/10 and PDR-EC-02/05 on the same evidence): the change decisions
    due at the gate (SRR-RD-03, PDR-RD-04) and the thermal model (PDR-RD-03). The whole path, with
    the real tools, is ``test_w3_integration.py``."""
    sid = s3.study_id

    async def crit(g):
        ev = (await client.get(f"/api/studies/{sid}/rules/gates/{g}")).json()
        return {c["id"]: c for c in ev["criteria"] if "-RD-" in c["id"]}, ev

    srr, ev = await crit("srr")
    assert set(srr) == {"SRR-RD-03"} and ev["ready"] is False
    assert srr["SRR-RD-03"]["status"] == "fail" and "ECP-02" in srr["SRR-RD-03"]["evidence_found"]
    by = {c["id"]: c for c in ev["criteria"]}
    assert by["SRR-EC-09"]["priority"] == "must_pass" and by["SRR-EC-09"]["status"] in ("manual", "fail")
    assert by["SRR-EC-10"]["status"] == "fail"                     # no debris assessment run yet
    pdr, ev = await crit("pdr")
    assert set(pdr) == {"PDR-RD-03", "PDR-RD-04"}
    assert pdr["PDR-RD-03"]["status"] == "fail" and pdr["PDR-RD-04"]["status"] == "fail"
    ids = await _changes(sid, "ECP-01", "ECP-02")
    # ECP-02 through change control (decided at SRR); ECP-01 rejected at PDR for the test
    start = (await client.post(f"/api/studies/{sid}/changes/ECP-02/control/start")).json()
    for seat in start["pending_seats"]:
        await client.post(f"/api/studies/{sid}/changes/ECP-02/control/agree", json={"seat": seat, "decision": "agree"})
    assert (await client.post(f"/api/studies/{sid}/changes/ECP-02/control/decide", json={"decision": "approve"})).status_code == 200
    srr, _ = await crit("srr")
    assert srr["SRR-RD-03"]["status"] == "pass" and "ECP-02 (accepted)" in srr["SRR-RD-03"]["evidence_found"]
    pdr, _ = await crit("pdr")
    assert pdr["PDR-RD-04"]["status"] == "fail" and "ECP-01" in pdr["PDR-RD-04"]["evidence_found"]
    await client.post(f"/api/studies/{sid}/changes/{ids['ECP-01']}/control/start")
    await client.post(f"/api/studies/{sid}/changes/{ids['ECP-01']}/control/decide",
                      json={"decision": "reject", "note": "Keep the VNIR camera; filter quote too late"})
    pdr, _ = await crit("pdr")
    assert pdr["PDR-RD-04"]["status"] == "pass"
    # the thermal model with A's tool: built, solved, heaters taken
    for step in ("propose", "run", "heaters/accept"):
        assert (await client.post(f"/api/studies/{sid}/thermal-model/{step}")).status_code == 200
    pdr, _ = await crit("pdr")
    assert pdr["PDR-RD-03"]["status"] == "pass", pdr["PDR-RD-03"]["evidence_found"]


# ─── 3.D7 change control ──────────────────────────────────────────────────

async def test_change_control_flow_updates_the_baseline(client, s3):
    sid = s3.study_id
    ids = await _changes(sid, "ECP-01", "ECP-02")
    v = (await client.get(f"/api/studies/{sid}/changes/ECP-02/control")).json()
    assert v["state"] == "not_started" and v["seats"] == []
    assert (await client.post(f"/api/studies/{sid}/changes/ECP-02/control/agree",
                              json={"seat": "systems_engineer"})).status_code == 409
    st = (await client.post(f"/api/studies/{sid}/changes/ECP-02/control/start")).json()
    assert st["state"] == "in_review"
    seats = [s["seat"] for s in st["seats"]]
    assert "systems_engineer" in seats and "mission_analyst" in seats   # T-M01's seat and SEG-LS-02's owner
    assert st["impact"]["source"] in ("impact_preview", "key_numbers")
    # approval needs every affected seat
    r = await client.post(f"/api/studies/{sid}/changes/ECP-02/control/decide", json={"decision": "approve"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "seats_pending"
    # an objection needs a reason; a seat not affected cannot answer
    assert (await client.post(f"/api/studies/{sid}/changes/ECP-02/control/agree",
                              json={"seat": seats[0], "decision": "object"})).status_code == 422
    assert (await client.post(f"/api/studies/{sid}/changes/ECP-02/control/agree",
                              json={"seat": "observer", "decision": "agree"})).status_code == 409
    for s in seats:
        r = await client.post(f"/api/studies/{sid}/changes/ECP-02/control/agree",
                              json={"seat": s, "decision": "agree", "note": "550-600 km acceptable"})
        assert r.status_code == 200
    assert r.json()["state"] == "agreed"
    seg = (await client.get(f"/api/requirements/{s3.requirements['SEG-LS-02']}")).json()
    new_text = "The launch request shall state a nominal altitude of 590 km and accept an injection altitude of 550 to 600 km."
    r = await client.post(f"/api/studies/{sid}/changes/ECP-02/control/decide",
                          json={"decision": "approve", "note": "Board: accepted", "apply": [{"code": "SEG-LS-02", "text": new_text}]})
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["state"] == "approved" and out["change"]["status"] == "accepted" and out["baseline_ref"]
    base = out["board"]["data"]["baseline"]
    assert base["kind"] == "mission" and base["revision"] == 1 and "ECP-02" in base["label"]
    assert out["board"]["data"]["applied"][0]["before"]["text"] == seg["text"]
    after = (await client.get(f"/api/requirements/{seg['id']}")).json()
    assert after["text"] == new_text
    snap = (await client.get(f"/api/studies/{sid}/gates/baselines/{out['baseline_ref']}")).json()
    assert snap["gate"] == "chg:ECP-02" and snap["snapshot"]["kind"] == "mission"
    assert (await client.post(f"/api/studies/{sid}/changes/ECP-02/control/decide",
                              json={"decision": "reject"})).status_code == 409
    # the register no longer lists ECP-02; the section lists both flows
    codes = {i["code"] for i in (await client.get(f"/api/studies/{sid}/open-items")).json()["items"]}
    assert "ECP-02" not in codes and "ECP-01" in codes
    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=change_control")).json()["change_control"]
    n = len((await client.get(f"/api/studies/{sid}/changes")).json()["items"])   # ECP-01, ECP-02, CR-V2 (seed S3)
    assert sx["counts"]["total"] == n and sx["counts"]["approved"] == 1 and sx["counts"]["not_started"] == n - 1
    assert ids["ECP-01"] in {i["change"]["id"] for i in sx["items"]}
    assert re.search(r"^[0-9a-f]{16}$", out["baseline_ref"])
    # the flow travels with the project file: the imported study shows the same decided flow
    a = (await client.get(f"/api/studies/{sid}/export")).json()
    assert len(a["tables"]["change_approvals"]) == len(seats) + 1
    new = (await client.post("/api/studies/import", json=a)).json()["id"]
    v2 = (await client.get(f"/api/studies/{new}/changes/ECP-02/control")).json()
    assert v2["state"] == "approved" and [s["seat"] for s in v2["seats"]] == seats
