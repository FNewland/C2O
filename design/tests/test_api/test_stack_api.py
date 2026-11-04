"""Stack builder API (routers/stack.py): propose, edit, approve by the Structures seat,
positions written to the elements, CDS matrix / GC-STACK, geometry export."""
from __future__ import annotations

import pytest
import yaml

from tests.test_api.test_seats_api import PROF, TL, _seat_env, claim, iap, seat_study  # noqa: F401  (autouse seat reset)

STR = iap("structures@c2o.live", "Kim")


@pytest.fixture(autouse=True)
def _fresh_layouts():
    from spacecdf_server.routers import stack
    stack.reset_stack_cache()
    yield
    stack.reset_stack_cache()

PARTS = [
    ("Structure 6U", "struct-isis-6u", "structure", 1, 1.2),
    ("OBC", "obc-isis-iobc", "obc", 1, 0.06),
    ("EPS", "eps-gom-nanopow-p60", "power", 1, 0.25),
    ("Battery", "bat-gom-nanopow-bpx", "power", 1, 0.2),
    ("S-band transmitter", "txrx-endurosat-s-band-tx", "ttc", 1, 0.2),
    ("S-band patch", "ant-endurosat-sband-patch", "ttc", 1, 0.045),
    ("UHF antenna", "ant-endurosat-uhf-dipole", "ttc", 1, 0.04),
    ("Reaction wheels", "rw-cubespace-cubewheel-medium", "aocs", 4, 0.12),
    ("Star tracker", "st-bct-nst", "aocs", 1, 0.35),
    ("Imager", "pl-imager-2u-eosat", "payload", 1, 1.1),
    ("Solar wings", "sp-clyde-3u-deploy", "power", 2, 0.3),
]


async def build(client, study: str) -> dict[str, dict]:
    r = await client.post(f"/api/elements/?study_id={study}", json={"name": "EOSAT", "element_type": "system"})
    assert r.status_code == 200, r.text
    sc = r.json()
    out = {}
    for name, kb, dom, q, m in PARTS:
        r = await client.post(f"/api/elements/?study_id={study}", json={
            "name": name, "element_type": "component", "parent_id": sc["id"], "subsystem_domain": dom,
            "kb_component_id": kb, "quantity": q, "mass_kg": m})
        assert r.status_code == 200, r.text
        out[name] = r.json()
    return out


async def test_propose_edit_approve_writes_positions(client, study_obj, study):
    els = await build(client, study)
    r = await client.get(f"/api/studies/{study}/stack")
    body = r.json()
    assert r.status_code == 200 and body["applicable"] and body["form_factor"] == "6U"
    assert body["approved"] is None and body["proposal"] is None and body["can_approve"]
    assert {u["mount_class"] for u in body["units"]} >= {"pc104_board", "u_module", "deployable", "face_panel"}

    r = await client.post(f"/api/studies/{study}/stack/auto-place", json={})
    assert r.status_code == 200, r.text
    prop = r.json()["proposal"]
    assert prop["meta"]["origin"] == "rule:STACK-AUTO" and prop["checks"]
    assert {c["id"] for c in prop["checks"]} >= {"STACK-HEIGHT", "STACK-COG", "STACK-KEEPOUT"}
    spec = prop["spec"]

    # drag the OBC to the other column, lock it
    obc = els["OBC"]["id"]
    ci = next(i for i, c in enumerate(spec["columns"]) if obc in c)
    spec["columns"][ci].remove(obc)
    spec["columns"][1 - ci].insert(1, obc)
    spec["locks"] = {obc: True}
    r = await client.put(f"/api/studies/{study}/stack/proposal", json={"spec": spec, "base_version": r.json()["version"]})
    assert r.status_code == 200, r.text
    prop = r.json()["proposal"]
    assert obc in prop["spec"]["columns"][1 - ci] and prop["spec"]["locks"] == {obc: True}
    assert prop["spec"]["origins"][obc] == "user"
    stale = await client.put(f"/api/studies/{study}/stack/proposal", json={"spec": spec, "base_version": 0})
    assert stale.status_code == 409

    # preview evaluates without saving
    v = r.json()["version"]
    pv = await client.post(f"/api/studies/{study}/stack/preview", json={"spec": spec})
    assert pv.status_code == 200 and pv.json()["checks"]
    assert (await client.get(f"/api/studies/{study}/stack")).json()["version"] == v

    r = await client.post(f"/api/studies/{study}/stack/approve")
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["proposal"] is None and out["approved"]["meta"]["approved_at"] and out["positions_written"] >= len(PARTS)
    el = (await client.get(f"/api/elements/{obc}")).json()
    assert el["position_json"] == pytest.approx(out["approved"]["positions_m"][obc])
    pl = (await client.get(f"/api/elements/{els['Imager']['id']}")).json()["position_json"]
    st = (await client.get(f"/api/elements/{els['Star tracker']['id']}")).json()["position_json"]
    assert pl[2] > st[2]                                  # design frame: +Z nadir, imager at the nadir end

    # the CDS matrix now has the stack checks and a CoG verdict from the written positions
    cds = (await client.get(f"/api/studies/{study}/rules/cds")).json()
    ids = {c["id"]: c for c in cds["checks"]}
    assert "STACK-HEIGHT" in ids and ids["CDS-COG"]["status"] in ("pass", "fail")
    assert ids["CDS-COG"]["status"] == {c["id"]: c for c in out["approved"]["checks"]}["STACK-COG"]["status"]

    geo = await client.get(f"/api/studies/{study}/stack/geometry", params={"format": "yaml"})
    assert geo.status_code == 200 and "c2o.geometry/1" in geo.text
    data = yaml.safe_load(geo.text)
    assert data["internal"] and data["mass_properties"]["mass_kg"] > 0


async def test_not_a_cubesat_is_reported(client, study_obj, study):
    await client.post(f"/api/elements/?study_id={study}", json={"name": "Big sat", "element_type": "system"})
    body = (await client.get(f"/api/studies/{study}/stack")).json()
    assert body["applicable"] is False and body["reason"]["fr"]
    r = await client.post(f"/api/studies/{study}/stack/auto-place", json={})
    assert r.status_code == 409


async def test_only_structures_approves_in_a_seat_study(client, study_obj, study):
    await build(client, study)
    await seat_study(client, study)
    await claim(client, study, TL, "team_leader")
    await claim(client, study, STR, "structures_engineer")
    r = await client.post(f"/api/studies/{study}/stack/auto-place", json={}, headers=TL)
    assert r.status_code == 200, r.text
    assert r.json()["can_approve"] is False and r.json()["proposal"]["meta"]["seat"] == "team_leader"
    r = await client.post(f"/api/studies/{study}/stack/approve", headers=TL)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "structures_only"
    r = await client.get(f"/api/studies/{study}/stack", headers=STR)
    assert r.json()["can_approve"] is True
    r = await client.post(f"/api/studies/{study}/stack/approve", headers=STR)
    assert r.status_code == 200, r.text
    assert r.json()["approved"]["meta"]["approved_seat"] == "structures_engineer"
    # the proposer may withdraw; nothing open now
    assert (await client.post(f"/api/studies/{study}/stack/reject", headers=TL)).status_code == 409


async def test_gate_check_gc_stack_at_pdr(client, study_obj, study):
    from spacecdf_server.services.gate_checks import GATE_CHECKS
    assert "GC-STACK" in GATE_CHECKS["PDR"]
    await build(client, study)
    await client.post(f"/api/studies/{study}/stack/auto-place", json={})
    await client.post(f"/api/studies/{study}/stack/approve")
    from spacecdf_server.routers.elements import _elements
    from spacecdf_server.services.gate_checks import evaluate_gate_checks
    els = [e for e in _elements.values() if e["study_id"] == study]
    res = evaluate_gate_checks("PDR", {"elements": els, "requirements": [], "interfaces": [], "params": {},
                                       "form_factor": "6U"})
    gc = next(c for c in res["checks"] if c["id"] == "GC-STACK")
    assert gc["status"] in ("pass", "warn")
