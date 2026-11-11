"""The walkthrough recording's starting points: the recording seed plus the scenes filmed before.

Each course video of the Northern Fire and Ice walkthrough (``video/storyboards/V-SCDF-*``,
``docs/dev/RECORDING_NOTES.md``) starts from the recording seed (``seed_nfi(..., recording=True)``)
with the scenes filmed in the earlier videos already done, through the same API calls as
``test_w3_integration.py``. Then the team is set up as in script §0.3: the 9-seat preset with the
two optional seats, every seat claimed by one presenter (the browser's ``scdf.client_id``)::

    python -m tests.fixtures.nfi.recording --url http://127.0.0.1:18800 --stage S4 \
        --after licensing,ledger,negotiations,price --client nfirec

prints ``{"study": "<id>", ...}`` on its last line. ``--after`` takes, in order:

==============  ===========================================================================
licensing       the Licensing tab filled from the baseline (scene 5.10)
ledger          the allocation ledger proposed and every line agreed by its owner (3.3)
negotiations    GS4, N1, N3 and N7 opened, the baseline option chosen, every seat signed
neg:<CODE>      one negotiation only (GS4, N1, N3, N7)
price           the project priced (2.9)
semp            the SEMP issued (6.3)
debris          the debris assessment run and accepted at the SRR (6.4)
ecp02           ECP-02 approved through change control (6.5)
pass:<g,g>      the named gates reviewed and passed (mdr, prr, srr, pdr)
icds            the five PDR ICDs at Issue A, signed by both seats (6.6)
reliability     the reliability block diagram run and the FMEA proposed (6.7)
thermal         the thermal model built, solved, heaters taken, solved (6.8)
ecp01           T-A01 decided A (conditional) and ECP-01 rejected (6.9)
==============  ===========================================================================
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from tests.fixtures.nfi import seed_nfi
from tests.fixtures.nfi.seed import NEGOTIATIONS, PDR_ICDS, _Api, _s4_licensing

SEATS = ("team_leader", "systems_engineer", "mission_analyst", "payload_lead", "power_engineer",
         "aocs_engineer", "comms_engineer", "thermal_engineer", "structures_engineer",
         "propulsion_engineer", "cost_engineer", "customer")


async def _ok(r, *codes: int):
    if r.status_code not in (codes or (200, 201)):
        raise RuntimeError(f"{r.request.method} {r.request.url}: {r.status_code} {r.text[:500]}")
    return r.json() if r.content else None


async def _change(c, sid: str, code: str, decision: str, note: str) -> None:
    st = await _ok(await c.post(f"/api/studies/{sid}/changes/{code}/control/start"))
    for seat in st["pending_seats"]:
        await _ok(await c.post(f"/api/studies/{sid}/changes/{code}/control/agree",
                               json={"seat": seat, "decision": "agree", "note": note}))
    await _ok(await c.post(f"/api/studies/{sid}/changes/{code}/control/decide", json={"decision": decision, "note": note}))


async def _negotiation(c, sid: str, code: str, opt: str) -> None:
    rec = await _ok(await c.post(f"/api/studies/{sid}/negotiations", json={"template": code}))
    url = f"/api/studies/{sid}/negotiations/{rec['id']}"
    rec = await _ok(await c.patch(url, json={"chosen_option": opt}))
    for seat in rec["seats"]:
        await _ok(await c.post(f"{url}/signoff", json={"seat": seat, "note": "agreed"}))


async def after(c, seed, step: str) -> None:
    from tests.fixtures.nfi.test_w3_integration import ecp01_scene

    sid = seed.study_id
    if step == "licensing":
        await _s4_licensing(_Api(c, seed), seed)
    elif step == "ledger":
        await _ok(await c.post(f"/api/studies/{sid}/allocation-ledger/propose"))
        for ln in (await _ok(await c.get(f"/api/studies/{sid}/allocation-ledger")))["items"]:
            if ln["status"] != "agreed":
                await _ok(await c.post(f"/api/studies/{sid}/allocation-ledger/{ln['id']}/agree",
                                       json={"seat": ln["owner_seat"]}))
    elif step == "negotiations":
        for code, opt in NEGOTIATIONS:
            await _negotiation(c, sid, code, opt)
    elif step.startswith("neg:"):
        code = step[4:].upper()
        await _negotiation(c, sid, code, dict(NEGOTIATIONS)[code])
    elif step == "price":
        await _ok(await c.post(f"/api/studies/{sid}/cost/price", json={}))
    elif step == "semp":
        await _ok(await c.post(f"/api/studies/{sid}/semp/issue", json={"note": "Reviewed for the SRR"}))
    elif step == "debris":
        await _ok(await c.post(f"/api/studies/{sid}/debris-assessment/run", json={}))
        await _ok(await c.post(f"/api/studies/{sid}/debris-assessment/accept",
                               json={"gate": "srr", "note": "Lifetime, casualty risk and collision probability reviewed"}))
    elif step == "ecp02":
        await _change(c, sid, "ECP-02", "approve", "Injection 550-600 km acceptable")
    elif step.startswith("pass:"):
        for g in step[5:].split(","):
            for action in ("start", "pass"):
                await _ok(await c.post(f"/api/studies/{sid}/gates/{g}/review", json={"action": action, "by": "board"}))
    elif step == "icds":
        for ref in PDR_ICDS:
            await _ok(await c.post(f"/api/studies/{sid}/icds/{ref}/issue", json={"change_note": "Issue A for the PDR"}))
            for side in ("provider", "consumer"):
                await _ok(await c.post(f"/api/studies/{sid}/icds/{ref}/signoff", json={"side": side}))
    elif step == "reliability":
        await _ok(await c.post(f"/api/studies/{sid}/reliability/run"))
        await _ok(await c.post(f"/api/studies/{sid}/fmea/propose"))
    elif step == "thermal":
        for path in ("propose", "run", "heaters/accept", "run"):
            await _ok(await c.post(f"/api/studies/{sid}/thermal-model/{path}"))
    elif step == "ecp01":
        await ecp01_scene(c, sid)
    else:
        raise SystemExit(f"unknown --after step {step!r}")


async def team(c, sid: str, client_id: str, name: str, claim: bool = True) -> None:
    """Script §0.3: the 9-seat preset with Propulsion and Cost & risk; one presenter holds every seat."""
    h = {"X-C2O-Client": client_id, "X-C2O-Name": name}
    await _ok(await c.post(f"/api/studies/{sid}/team/preset", headers=h,
                           json={"team_size": "9", "optional": ["propulsion_engineer", "cost_engineer"]}))
    if claim:
        await _ok(await c.post(f"/api/studies/{sid}/team/claim", headers=h, json={"seats": list(SEATS)}))
        await _ok(await c.post(f"/api/studies/{sid}/team/active", headers=h, json={"seat": "team_leader"}))


async def run(url: str, stage: str, steps: list[str], client_id: str, name: str, claim: bool) -> dict:
    import httpx

    async with httpx.AsyncClient(base_url=url.rstrip("/"), timeout=900) as c:
        seed = await seed_nfi(c, stage, recording=True)
        for s in steps:
            await after(c, seed, s)
        if client_id:
            await team(c, seed.study_id, client_id, name, claim)
        return {"study": seed.study_id, "stage": stage, "after": steps, "calls": seed.report["calls"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tests.fixtures.nfi.recording", description=__doc__.splitlines()[0])
    ap.add_argument("--url", default="http://127.0.0.1:18800")
    ap.add_argument("--stage", default="S4", type=str.upper)
    ap.add_argument("--after", default="", help="comma-free list separated by '+' or spaces; see the module doc")
    ap.add_argument("--client", default="", help="browser client id that claims every seat (empty: solo study)")
    ap.add_argument("--name", default="NFI Team")
    ap.add_argument("--no-claim", action="store_true", help="set the team preset but claim no seat")
    a = ap.parse_args(argv)
    steps = [s for s in a.after.replace("+", " ").split() if s]
    out = asyncio.run(run(a.url, a.stage, steps, a.client, a.name, not a.no_claim))
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
