"""3.S1 / 3.S2: the protocol file, its loader and the phase API on the Northern Fire and Ice v2 fixture.

Counts come from the fixture and the store, never typed in.
"""
from __future__ import annotations

import copy

import pytest

from tests.fixtures.nfi import load, seed_nfi


def _proto():
    from spacecdf_server.services import se_protocol as sp
    return sp, copy.deepcopy(sp.load())


def test_protocol_file_is_valid_and_covers_every_gate():
    sp, data = _proto()
    assert sp.validate(data) == []
    assert set(data["phases"]) == set(sp.CANONICAL)
    assert data["enforcement_default"] == "warn"           # PI ruling: warn by default
    # PI ruling: system-level trades orbit + launch at MDR, data architecture at SRR, architecture at PDR
    trade = {g: [d for d in data["phases"][g]["deliverables"] if d["kind"] == "trade"] for g in ("mdr", "srr", "pdr")}
    assert trade["mdr"][0]["gates"] == ["mdr"] and trade["mdr"][0]["min"] == 2
    assert trade["srr"][0]["gates"] == ["srr"] and "system" in trade["srr"][0]["levels"]
    assert "architecture" in trade["pdr"][0]["levels"]
    assert not [d for d in data["phases"]["prr"]["deliverables"] if d["kind"] == "trade"]


@pytest.mark.parametrize("breakage, message", [
    (lambda d: d["phases"]["mdr"]["deliverables"][0]["label"].pop("fr"), "needs non-empty en and fr"),
    (lambda d: d["phases"]["srr"]["deliverables"].append(
        {"id": "SRR-DL-99", "kind": "diagram", "ref": "no_such_kind", "label": {"en": "x", "fr": "x"}}), "unknown diagram kind"),
    (lambda d: d["phases"]["pdr"]["deliverables"].append(
        {"id": "PDR-DL-99", "kind": "telepathy", "label": {"en": "x", "fr": "x"}}), "unknown kind"),
    (lambda d: d["phases"]["prr"]["deliverables"].append(
        {"id": "PRR-DL-99", "kind": "product", "ref": "budgets", "owner_seat": "chief_wizard",
         "label": {"en": "x", "fr": "x"}}), "unknown seat"),
    (lambda d: d["phases"]["prr"]["deliverables"].append(
        {"id": "PRR-DL-98", "kind": "product", "ref": "no_product", "label": {"en": "x", "fr": "x"}}), "unknown product"),
    (lambda d: d["phases"]["mdr"]["coaching"]["seats"].pop("power_engineer"), "no card for power_engineer"),
    (lambda d: d["phases"]["mdr"]["coaching"]["seats"]["aocs_engineer"]["focus"].pop("fr"), "needs non-empty en and fr"),
    (lambda d: d["phases"].pop("frr"), "phases.frr is missing"),
])
def test_loader_rejects_a_broken_block(breakage, message):
    sp, data = _proto()
    breakage(data)
    errs = sp.validate(data)
    assert any(message in e for e in errs), errs


async def test_s0_phase_is_mdr_with_entry_deliverables_and_coaching(client):
    s = await seed_nfi(client, "S0")
    ph = (await client.get(f"/api/studies/{s.study_id}/phase")).json()
    assert ph["gate"] == "mdr" and ph["phase"] == "0" and ph["covers"] == ["mdr"]
    assert ph["enforcement"] == "warn" and ph["upcoming"][:3] == ["prr", "srr", "pdr"]
    by = {d["id"]: d for d in ph["deliverables"]}
    proto = _proto()[1]["phases"]["mdr"]
    assert set(by) == {d["id"] for d in proto["deliverables"]}
    assert all(d["state"] in ("ok", "warn", "missing", "info") and d["evidence"] for d in ph["deliverables"])
    # S0 holds the v2 register: 12 stakeholders in 5 categories
    n = len(load("stakeholders")["stakeholders"])
    assert by["MDR-DL-02"]["state"] == "ok" and f"{n} stakeholders in 5 categories" in by["MDR-DL-02"]["evidence"]
    # no trade yet at S0: the system-trade deliverable is a gap, named with what exists
    assert by["MDR-DL-05"]["state"] == "missing" and "MDR" in by["MDR-DL-05"]["evidence"]
    assert ph["coaching"]["register"] == "learning" and len(ph["coaching"]["phase"]) >= 3
    fr = (await client.get(f"/api/studies/{s.study_id}/phase?lang=fr")).json()
    assert fr["deliverables"][1]["evidence"] == by["MDR-DL-02"]["evidence_i18n"]["fr"]


def _trade(tid: str, level: str, gate: str, decided: bool) -> dict:
    st = {"id": tid, "title": tid, "level": level, "gate": gate, "status": "decided" if decided else "open",
          "options": ["A", "B"], "criteria": ["c"], "scores": {}, "decision": {"selected": "A"} if decided else {}}
    return {"state": st, "version": 1}


async def test_s3_mdr_passed_srr_and_pdr_blocks_show_the_system_trades(client):
    """3.S1 acceptance: with MDR passed, the SRR block shows "system trade ✅ (T-S01)" and the PDR
    block "architecture trade ⚠️ T-A01 undecided". The system and architecture trades are written
    in agent D's shape (``level`` enum, ``gate``), from the v2 ``trades.yaml``."""
    from spacecdf_server.routers.studies import get_study_store
    s = await seed_nfi(client, "S3")
    st = get_study_store()[s.study_id]
    st.gate_states = {**(st.gate_states or {}), "mdr": {"state": "passed", "history": []}}
    v2 = {t["id"]: t for t in [*load("trades")["system_trades"], *load("trades")["architecture_trades"]]}
    level = {"Mission": "mission", "System": "system", "System architecture": "architecture"}
    recs = dict(st.trade_records or {})
    for tid, t in v2.items():
        recs[tid] = _trade(tid, level[t["level"]], t["gate"].lower(), decided=tid != "T-A01")
    st.trade_records = recs
    ph = (await client.get(f"/api/studies/{s.study_id}/phase")).json()
    assert ph["gate"] == "prr" and ph["current_gate"] == "prr"
    assert {e["id"]: e["state"] for e in ph["entry"]}["PRR-IN-01"] == "ok"
    srr = {d["id"]: d for d in (await client.get(f"/api/studies/{s.study_id}/phase?gate=srr")).json()["deliverables"]}
    assert srr["SRR-DL-01"]["state"] == "ok" and srr["SRR-DL-01"]["refs"] == ["T-S01"]
    pdr = {d["id"]: d for d in (await client.get(f"/api/studies/{s.study_id}/phase?gate=pdr")).json()["deliverables"]}
    assert pdr["PDR-DL-01"]["state"] == "warn" and "T-A01 undecided" in pdr["PDR-DL-01"]["evidence"]
    mdr = {d["id"]: d for d in (await client.get(f"/api/studies/{s.study_id}/phase?gate=mdr")).json()["deliverables"]}
    assert mdr["MDR-DL-05"]["state"] == "ok" and set(mdr["MDR-DL-05"]["refs"]) == {"T-M01", "T-M02"}


async def test_s4_deliverables_evaluate_with_evidence_and_match_the_service(client):
    """3.S2 acceptance: at S4 the MDR, PRR, SRR and PDR deliverables evaluate with evidence; the
    result is the same through ``/phase`` and through the service the gate ``start`` reads."""
    from spacecdf_server.services import se_deliverables
    s = await seed_nfi(client, "S4")
    for g in ("mdr", "prr", "srr", "pdr"):
        ph = (await client.get(f"/api/studies/{s.study_id}/phase?gate={g}")).json()
        ev = await se_deliverables.evaluate(s.study_id, g)
        assert [(d["id"], d["state"], d["evidence"]) for d in ph["deliverables"]] == \
            [(d["id"], d["state"], d["evidence"]) for d in ev["deliverables"]]
        assert ph["deliverables"] and all(d["evidence"] for d in ph["deliverables"])
        assert set(ev["missing"]) == {d["id"] for d in ev["deliverables"]
                                      if d["state"] in ("warn", "missing") and d["severity"] != "info"}
        assert all(w["evidence"] and w["label"]["fr"] for w in ev["warnings"])
    # the AIT model philosophy exists at S4: the PDR verification-plan product is evidenced
    pdr = {d["id"]: d for d in (await se_deliverables.evaluate(s.study_id, "pdr"))["deliverables"]}
    assert pdr["PDR-DL-09"]["state"] == "ok"
    alone = (await client.get(f"/api/studies/{s.study_id}/phase/deliverables?gate=pdr")).json()
    assert alone["missing"] == (await se_deliverables.evaluate(s.study_id, "pdr"))["missing"]


async def test_unknown_study_and_protocol_route(client):
    assert (await client.get("/api/studies/nope/phase")).status_code == 404
    r = (await client.get("/api/se-protocol")).json()
    assert r["errors"] == [] and r["registers"] == ["learning", "plain", "practitioner"]
