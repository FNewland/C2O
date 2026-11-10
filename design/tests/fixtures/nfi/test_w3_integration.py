"""Wave 3 integration: the Northern Fire and Ice walkthrough script for the SRR and the PDR.

ONE path of team actions, through the API only, that makes the SRR and then the PDR passable
(every must-pass criterion passes) on the nfi v2 seed. The same actions are the script of the
recording: on the full seed (tests, example project) and on the ``--recording`` seed, where the
team also fills the Licensing tab and the allocation ledger on camera.

Before the actions the two gates are "not ready" for the reasons v2's own readiness review gives
(no SEMP issued, no debris assessment, ECP-02 open; ICDs not at Issue A, no reliability analysis
or FMEA, no thermal model, ECP-01 open). After them, both are ready, legitimately: each criterion
reads the record the tool wrote.

SRR: issue the SEMP (Phase panel), run and accept the debris assessment (Licensing, Disposal),
decide ECP-02 through change control (Decide). PDR: raise Issue A of the five PDR ICDs and sign
each by both owning seats (ICD tab), build the reliability block diagram and propose the FMEA
(V&V, Reliability), build, solve and take the sized heaters of the thermal model (V&V, Thermal),
check the logic of the T-A01 score and decide ECP-01 (Decide; the
teaching scene ``ecp01_scene``); the allocation ledger is agreed (seeded, or filled on camera).
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import seed_nfi
from tests.fixtures.nfi.seed import PDR_ICDS, _Api, _s4_licensing

GATES = ("mdr", "prr", "srr", "pdr")


async def _gate(client, sid: str, gate: str) -> dict:
    r = await client.get(f"/api/studies/{sid}/rules/gates/{gate}")
    assert r.status_code == 200, r.text
    return r.json()


async def _table(client, sid: str) -> dict[str, dict]:
    """Per gate: ready, must-pass met/total and the must-pass criteria that do not pass."""
    out = {}
    for g in GATES:
        ev = await _gate(client, sid, g)
        s = ev["summary"]
        out[g] = {"ready": ev["ready"], "must": (s["must_pass_met"], s["must_pass"]),
                  "open": {c["id"]: c.get("evidence_found") for c in ev["criteria"]
                           if c["priority"] == "must_pass" and c["status"] != "pass"}}
    return out


async def _ok(r, *codes: int):
    assert r.status_code in (codes or (200,)), (r.request.url, r.status_code, r.text[:600])
    return r.json()


async def _decide_change(client, sid: str, code: str, decision: str, note: str) -> dict:
    """Change control (D 3.D7): start (impact preview, affected seats), every affected seat
    agrees, the board decides."""
    st = await _ok(await client.post(f"/api/studies/{sid}/changes/{code}/control/start"))
    assert st["impact"]["source"] == "impact_preview", st["impact"]          # L's preview of the record
    for seat in st["pending_seats"]:
        await _ok(await client.post(f"/api/studies/{sid}/changes/{code}/control/agree",
                                    json={"seat": seat, "decision": "agree", "note": note}))
    return await _ok(await client.post(f"/api/studies/{sid}/changes/{code}/control/decide",
                                       json={"decision": decision, "note": note}))


async def srr_actions(client, sid: str) -> None:
    # 1. the SEMP generated from the study is reviewed and issued (Phase panel)
    sm = await _ok(await client.get(f"/api/studies/{sid}/semp/issue"))
    assert sm["ready"] and sm["issue"] is None
    assert (await _ok(await client.post(f"/api/studies/{sid}/semp/issue", json={"note": "Reviewed for the SRR"})))["semp"]["issue"] == "A"
    # 2. the debris assessment is run and accepted at the SRR (Licensing, Disposal)
    run = await _ok(await client.post(f"/api/studies/{sid}/debris-assessment/run", json={}))
    assert run["version"] >= 1
    await _ok(await client.post(f"/api/studies/{sid}/debris-assessment/accept",
                                json={"gate": "srr", "note": "Lifetime, casualty risk and collision probability reviewed"}))
    # 3. ECP-02 (the launch request: 590 km nominal, 550-600 km acceptable) through change control
    dec = await _decide_change(client, sid, "ECP-02", "approve", "Injection 550-600 km acceptable")
    assert dec["state"] == "approved"


async def pdr_actions(client, sid: str) -> None:
    # 4. Issue A of each PDR ICD, signed by the provider and the consumer seat (ICD tab)
    for ref in PDR_ICDS:
        await _ok(await client.post(f"/api/studies/{sid}/icds/{ref}/issue", json={"change_note": "Issue A for the PDR"}))
        for side in ("provider", "consumer"):
            await _ok(await client.post(f"/api/studies/{sid}/icds/{ref}/signoff", json={"side": side}))
    # 5. the reliability block diagram over the mission-success horizon, and the FMEA (V&V)
    rel = await _ok(await client.post(f"/api/studies/{sid}/reliability/run"))
    assert rel["result"]["mission_reliability"] >= 0.80
    await _ok(await client.post(f"/api/studies/{sid}/fmea/propose"))
    ev = await _ok(await client.get(f"/api/studies/{sid}/reliability/evidence"))
    assert ev["ok"], ev["reasons"]
    # 6. the thermal nodal model: built, solved, the sized heaters taken, solved again (V&V)
    await _ok(await client.post(f"/api/studies/{sid}/thermal-model/propose"))
    await _ok(await client.post(f"/api/studies/{sid}/thermal-model/run"))
    await _ok(await client.post(f"/api/studies/{sid}/thermal-model/heaters/accept"))
    await _ok(await client.post(f"/api/studies/{sid}/thermal-model/run"))
    th = await _ok(await client.get(f"/api/studies/{sid}/thermal-model/evidence"))
    assert th["ok"], th["reasons"]
    # 7. ECP-01 (second IMX992 camera) decided at the PDR. Teaching scene (PI, 2026-11-10): the
    # matrix says C; the team disagrees and checks its logic before overruling the score.
    await ecp01_scene(client, sid)


#: the reasons the team records for keeping A, none of which is a criterion of the matrix
ECP01_RATIONALE = (
    "The matrix ranks C first (3.65 vs 3.50) and the ranking survives every +-20 % weight change, but "
    "weight sensitivity does not test the scores. The 0.15 margin is smaller than one score step on any "
    "criterion weighted 0.2 or more, and two of C's gains rest on calculation, not measurement: the NIR "
    "SNR is scaled from a datasheet and the snow exposure limit is scaled from the IMX542. The trade's "
    "own conditions (quote for the 875/50 filter, breadboard measurement over snow, 0.82 kg payload "
    "allocation) are not met. Keep A, the cameras in hand; revisit if the evidence arrives before CDR.")


async def ecp01_scene(client, sid: str) -> None:
    """When the team disagrees with a score, check the logic before following or overruling it:
    (1) what does the matrix say, and how robust is it; (2) is the margin bigger than the
    uncertainty of the scores; (3) which scores are measured and which assumed; (4) were the
    trade's own conditions met. Then decide, record why, and say what would reopen it."""
    t = await _ok(await client.get(f"/api/studies/{sid}/trades/T-A01"))
    ev = t["evaluation"]
    # (1) the score: C first, robust to +-20 % on every weight
    assert ev["ranking_eligible"][0] == "C" and ev["runner_up"] == "A" and ev["robust_pm20"]
    # (2) the margin is smaller than one score step on the heavier criteria
    assert ev["margin"] < max(ev["weights"].values())
    # (3)/(4) the evidence behind C's gains is calculated or assumed, and the conditions are open
    evid = t["state"].get("evidence_by_criterion") or {}
    assert "Calculated" in str(evid.get("Technical risk (custom parts, TRL)")) and "Assumed" in str(evid.get("Cost"))
    # the decision: A, conditional, reopened before CDR if the evidence arrives
    d = await _ok(await client.post(f"/api/studies/{sid}/trades/T-A01/decision", json={
        "selected": "A", "rationale": ECP01_RATIONALE, "seat": "payload_lead",
        "condition": "Reopen ECP-01 if the 875/50 filter is quoted and the IMX992 breadboard measurement over snow "
                     "is in before CDR",
        "due": "2028-06-30", "fallback": "Keep A (IMX992 SWIR + IMX542 VNIR)", "risks": ["RSK-035"],
        "blocks_gate": "cdr"}))
    assert d["state"]["status"] == "decided"
    dec = await _decide_change(client, sid, "ECP-01", "reject",
                               "Score overruled after checking the logic; see T-A01. Revisit before CDR if the "
                               "filter quote and the breadboard measurement arrive.")
    assert dec["state"] == "rejected"


async def fill_recording_scenes(client, seed) -> None:
    """What the recording seed leaves to the team on camera that the gates read: the Licensing
    tab (the seed's own licensing record) and the allocation ledger (Systems proposes from the
    roll-up, each owner seat agrees its line)."""
    sid = seed.study_id
    await _s4_licensing(_Api(client, seed), seed)
    led = await _ok(await client.post(f"/api/studies/{sid}/allocation-ledger/propose"))
    assert led
    lines = (await _ok(await client.get(f"/api/studies/{sid}/allocation-ledger")))["items"]
    assert lines
    for ln in lines:
        if ln["status"] != "agreed":
            await _ok(await client.post(f"/api/studies/{sid}/allocation-ledger/{ln['id']}/agree",
                                        json={"seat": ln["owner_seat"]}))


def _assert_before(t: dict) -> None:
    assert t["mdr"]["ready"] and t["prr"]["ready"], t
    assert not t["srr"]["ready"] and not t["pdr"]["ready"], t
    assert {"SRR-EC-09", "SRR-EC-10", "SRR-RD-03"} <= set(t["srr"]["open"]), t["srr"]
    assert {"PDR-EC-02", "PDR-EC-05", "PDR-RD-03", "PDR-RD-04"} <= set(t["pdr"]["open"]), t["pdr"]


async def _walkthrough(client, recording: bool) -> dict:
    seed = await seed_nfi(client, "S4", recording=recording)
    sid = seed.study_id
    before = await _table(client, sid)
    _assert_before(before)
    if recording:
        assert "PDR-EC-07" in before["pdr"]["open"]          # the ledger is filled on camera
        await fill_recording_scenes(client, seed)
    await srr_actions(client, sid)
    mid = await _table(client, sid)
    assert mid["srr"]["ready"], mid["srr"]["open"]
    assert not mid["pdr"]["ready"]
    await pdr_actions(client, sid)
    after = await _table(client, sid)
    for g in GATES:
        assert after[g]["ready"], (g, after[g]["open"])
        assert after[g]["must"][0] == after[g]["must"][1]
    # the passes themselves: SRR then PDR through the review (Team leader / instructor)
    for g in ("mdr", "prr", "srr", "pdr"):
        for action in ("start", "pass"):
            r = await client.post(f"/api/studies/{sid}/gates/{g}/review", json={"action": action, "by": "board"})
            assert r.status_code == 200, (g, action, r.text[:400])
    gates = (await _ok(await client.get(f"/api/studies/{sid}/gates")))["gates"]
    assert {x["id"]: x["state"] for x in gates if x["id"] in GATES} == {g: "passed" for g in GATES}
    return {"before": before, "srr_done": mid, "after": after}


@pytest.mark.asyncio
async def test_walkthrough_srr_and_pdr_pass_on_the_full_seed(client):
    await _walkthrough(client, recording=False)


@pytest.mark.asyncio
async def test_walkthrough_srr_and_pdr_pass_on_the_recording_seed(client):
    await _walkthrough(client, recording=True)
