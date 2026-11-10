"""Wave 3, 3.A2 acceptance on the Northern Fire and Ice fixture: the allocation ledger.

S2 imports every allocation of ``budgets.yaml`` agreed by its owner seat; the counts, sums and the
Systems reserve come from the fixture. A non-owner edit in a seat study becomes a pending change
the owner accepts; the owner agrees or disputes its line; the recording seed leaves the ledger
empty (the scene is filmed); the ledger survives a project round trip.
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import load, seed_nfi

INSTRUCTOR = "prof@c2o.live"


def _iap(email: str, name: str) -> dict:
    return {"X-Goog-Authenticated-User-Email": f"accounts.google.com:{email}", "X-C2O-Name": name}


@pytest.fixture()
def _seats(monkeypatch):
    from spacecdf_server.seats import store
    from spacecdf_server.seats.instructor import invalidate_gate_cache
    monkeypatch.setenv("SPACECDF_INSTRUCTORS", INSTRUCTOR)
    monkeypatch.delenv("SMO_INSTRUCTORS", raising=False)
    store.reset_memory()
    invalidate_gate_cache()
    yield
    store.reset_memory()


def _expected_counts(b: dict) -> dict:
    return {
        "mass": len(b["mass"]["allocations"]), "power_avg": len(b["power"]["allocations"]),
        "power_peak": sum(1 for v in b["power"]["peak_allocations"].values() for k in v if k.endswith("_w")),
        "power_mode": sum(len(v) for v in b["power"]["mode_allocations"].values()),
        "data": len(b["data"]["allocations"]), "pointing": 5,
        "registration": len(b["registration"]["allocations"]), "timing": len(b["timing"]["contributors"]),
    }


async def test_ledger_imported_agreed_with_reserve_and_status(client):
    s = await seed_nfi(client, "S2")
    sid = s.study_id
    b = load("budgets")
    led = (await client.get(f"/api/studies/{sid}/allocation-ledger")).json()
    exp = _expected_counts(b)
    assert led["counts"]["by_type"] == exp
    assert exp["mass"] == 8 and exp["power_avg"] == 8 and exp["power_peak"] == 1 and exp["power_mode"] == 4 and exp["data"] == 4
    assert led["counts"]["by_status"]["agreed"] == led["counts"]["lines"] == sum(exp.values())
    items = led["items"]
    mass = [i for i in items if i["budget_type"] == "mass"]
    assert sum(i["value"] for i in mass) == pytest.approx(b["mass"]["closure"]["sum_allocations_kg"], abs=1e-6)  # 4.43
    power = [i for i in items if i["budget_type"] == "power_avg"]
    assert sum(i["value"] for i in power) == pytest.approx(b["power"]["closure"]["sum_allocations_w"], abs=1e-6)  # 4.91
    peak = next(i for i in items if i["budget_type"] == "power_peak")
    assert peak["element_code"] == "PAY" and peak["value"] == b["power"]["peak_allocations"]["PAY"]["acquisition_w"]
    # every mass and power line is covered by its v2 requirement and owned by the seat of budgets.yaml
    pay = next(i for i in mass if i["element_code"] == "PAY")
    assert pay["requirement_code"] == "PAY-BUD-01" and pay["requirement_id"] and pay["owner_seat"] == "payload_lead"
    assert all(i["element_id"] for i in mass + power)
    dis = next(i for i in mass if i["element_code"] == "DIS")
    assert dis["owner_seat"] == "propulsion_engineer"       # the drag sail belongs to Propulsion (PI)
    # Systems reserve: limit − Σ × (1 + 20 % hold) = 6.0 − 5.316 = 0.684 kg; power 12.2 − 5.892; data 6.45
    cl = led["closure"]
    assert cl["mass"]["with_system_margin"] == pytest.approx(b["mass"]["closure"]["with_system_margin_kg"], abs=1e-3)
    assert led["reserve"]["mass"]["value"] == pytest.approx(b["mass"]["closure"]["left_to_limit_kg"], abs=1e-3)
    assert cl["power_avg"]["with_system_margin"] == pytest.approx(b["power"]["closure"]["with_system_margin_w"], abs=1e-3)
    assert cl["power_avg"]["limit"] == pytest.approx(b["power"]["closure"]["eol_generation_w"], abs=0.01)
    assert led["reserve"]["data"]["value"] == pytest.approx(b["data"]["reserve_mb_per_day"], abs=0.01)
    assert cl["mass"]["closes"] and cl["power_avg"]["closes"] and cl["data"]["closes"]
    st = (await client.get(f"/api/studies/{sid}/allocation-ledger/status")).json()
    assert st["ok"] and st["agreed"] == st["lines"] == 16 and not st["missing"]
    # readiness at the spacecraft level counts the agreed lines
    sc = s.elements["spacecraft"]["id"]
    rd = (await client.get(f"/api/studies/{sid}/readiness?element_id={sc}")).json()
    item = next(i for i in rd["items"] if i["id"] == "allocations_agreed")
    assert item["ok"] and item["counts"]["lines"] == sum(1 for i in items if i["element_code"] not in ("SYS", "SC"))
    # export section
    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=allocations")).json()["allocations"]
    assert sx["status"] == "ok" and len(sx["items"]) == led["counts"]["lines"] and sx["reserve"]["mass"]["value"] == pytest.approx(0.684, abs=1e-3)

    # an open study: an edit by the owner keeps the line agreed; by Systems it goes back to proposed,
    # the requirement is marked stale with the new value, and the reserve follows
    eps = next(i for i in mass if i["element_code"] == "EPS")
    r = await client.patch(f"/api/studies/{sid}/allocation-ledger/{eps['id']}", json={"value": 1.80, "seat": "systems_engineer",
                                                                                         "why": "wing datasheet"})
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["status"] == "proposed" and out["version"] == 2
    try:   # agent R's AR-01 hook (3.R3) owns the requirement once it lands; until then the ledger marks it
        from spacecdf_server.services import allocation_requirements as _ar
        hook = hasattr(_ar, "ledger_changed")
    except ImportError:
        hook = False
    if not hook:
        sync = out["data_json"]["requirement_sync"]
        assert sync["requirement_code"] == "EPS-BUD-01" and sync["proposed_value"] == 1.80 and sync["old_value"] == 1.75
    led2 = (await client.get(f"/api/studies/{sid}/allocation-ledger")).json()
    assert led2["reserve"]["mass"]["value"] == pytest.approx(6.0 - 4.48 * 1.2, abs=1e-3)
    st2 = (await client.get(f"/api/studies/{sid}/allocation-ledger/status")).json()
    assert not st2["ok"] and [x["element_code"] for x in st2["not_agreed"]] == ["EPS"]
    r = await client.post(f"/api/studies/{sid}/allocation-ledger/{eps['id']}/agree", json={"seat": "power_engineer"})
    assert r.json()["status"] == "agreed"
    r = await client.post(f"/api/studies/{sid}/allocation-ledger/{eps['id']}/dispute", json={"reason": "no room"})
    assert r.json()["status"] == "disputed" and r.json()["data_json"]["dispute"]["reason"] == "no room"
    assert (await client.post(f"/api/studies/{sid}/allocation-ledger/{eps['id']}/dispute", json={})).status_code == 422
    hist = r.json()["history_json"]
    assert [h["field"] for h in hist][-3:] == ["value", "status", "status"]

    # round trip: the ledger travels with the project file
    a = (await client.get(f"/api/studies/{sid}/export")).json()
    imp = (await client.post("/api/studies/import", json=a)).json()
    led3 = (await client.get(f"/api/studies/{imp['id']}/allocation-ledger")).json()
    assert led3["counts"]["by_type"] == led2["counts"]["by_type"] and led3["counts"]["lines"] == led2["counts"]["lines"]
    assert sorted((i["element_code"], i["budget_type"], i["mode_key"], i["value"], i["status"]) for i in led3["items"]) == \
        sorted((i["element_code"], i["budget_type"], i["mode_key"], i["value"], i["status"])
               for i in (await client.get(f"/api/studies/{sid}/allocation-ledger")).json()["items"])


async def test_recording_seed_leaves_the_ledger_to_the_team_and_propose_fills_it(client):
    s = await seed_nfi(client, "S2", recording=True)
    sid = s.study_id
    led = (await client.get(f"/api/studies/{sid}/allocation-ledger")).json()
    assert led["items"] == []
    res = (await client.post(f"/api/studies/{sid}/allocation-ledger/propose")).json()
    kinds = {(i["budget_type"], i["element_code"]) for i in res["items"]}
    assert {("mass", "PAY"), ("mass", "EPS"), ("power_avg", "AOCS")} <= kinds
    assert all(i["status"] == "proposed" and i["value"] >= (i["margined"] or 0) for i in res["items"])
    # Σ mass lines ≈ the roll-up with maturity (each rounded up to 10 g)
    rollup = (await client.get(f"/api/studies/{sid}/rollup")).json()
    wm = rollup["mass"]["with_maturity_kg"]
    total = sum(i["value"] for i in res["items"] if i["budget_type"] == "mass")
    assert wm <= total <= wm + 0.01 * 10
    again = (await client.post(f"/api/studies/{sid}/allocation-ledger/propose")).json()
    assert again["proposed"] == 0


async def test_non_owner_edit_is_a_pending_change_the_owner_accepts(client, _seats):
    s = await seed_nfi(client, "S2")
    sid = s.study_id
    prof, pay, pwr = _iap(INSTRUCTOR, "Prof"), _iap("pay@c2o.live", "Pat"), _iap("pwr@c2o.live", "Pia")
    assert (await client.post(f"/api/studies/{sid}/team/preset", json={"team_size": "9"}, headers=prof)).status_code == 200
    assert (await client.post(f"/api/studies/{sid}/team/claim", json={"seats": ["payload_lead"]}, headers=pay)).status_code == 200
    assert (await client.post(f"/api/studies/{sid}/team/claim", json={"seats": ["power_engineer"]}, headers=pwr)).status_code == 200
    led = (await client.get(f"/api/studies/{sid}/allocation-ledger")).json()
    eps = next(i for i in led["items"] if i["budget_type"] == "mass" and i["element_code"] == "EPS")
    # the Payload seat edits the EPS line: first the warning, then a pending change for Power
    r = await client.patch(f"/api/studies/{sid}/allocation-ledger/{eps['id']}", json={"value": 1.70}, headers=pay)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "owned_by_other_seat"
    r = await client.patch(f"/api/studies/{sid}/allocation-ledger/{eps['id']}", json={"value": 1.70, "why": "lighter wings"},
                           headers={**pay, "X-C2O-Confirm-Review": "1"})
    assert r.status_code == 202, r.text
    pc = r.json()["pending_change"]
    assert pc["owner_seat"] == "power_engineer" and pc["kind"] == "allocation_ledger"
    line = (await client.get(f"/api/studies/{sid}/allocation-ledger")).json()
    assert next(i for i in line["items"] if i["id"] == eps["id"])["value"] == 1.75     # the owner's value stands
    # the Payload seat cannot agree the EPS line
    r = await client.post(f"/api/studies/{sid}/allocation-ledger/{eps['id']}/agree", json={}, headers=pay)
    assert r.status_code == 403
    # the owner accepts the change (seats/changes.apply_pending → allocation_ledger.apply_ledger_change)
    from spacecdf_server.seats import store
    from spacecdf_server.services.allocation_ledger import apply_ledger_change
    pend = await store.get_pending(pc["id"])
    out = await apply_ledger_change(pend)
    assert out["value"] == 1.70 and out["status"] == "agreed" and out["version"] == 2
    # the owner edits its own line directly and stays agreed
    r = await client.patch(f"/api/studies/{sid}/allocation-ledger/{eps['id']}", json={"value": 1.72}, headers=pwr)
    assert r.status_code == 200 and r.json()["status"] == "agreed" and r.json()["version"] == 3
