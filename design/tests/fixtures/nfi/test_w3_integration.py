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
decide ECP-01 (Decide); the allocation ledger is agreed (seeded, or filled on camera).
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
    # 7. ECP-01 (second IMX992 camera) decided at the PDR: kept open in v2 for the NIR filter
    # quote; the board rejects it for now and keeps the VNIR camera
    dec = await _decide_change(client, sid, "ECP-01", "reject", "Keep the VNIR camera; the NIR filter quote is not in")
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
