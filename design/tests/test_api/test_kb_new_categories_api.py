"""New KB categories over HTTP: the Equipment Catalog shows them under their domain, and
selecting an integrated ADCS, a drag sail, and a camera + lens + controller lands in the
equipment budgets (mass, cost, power per mode) and satisfies the equipment needs."""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element

ADCS = "adcs-cubespace-cubeadcs-3axis-small"
SAIL = "deorb-npc-artica"
CAM = "pl-av-alvium-1800c-530-vswir"
LENS = "opt-kowa-lm35hc-sw"
FILTER = "opt-edmund-85-903"
CTRL = "pc-rpi-cm4"


def _kb(cid: str) -> dict:
    from spacecdf_kb.loader import KnowledgeBase
    return next(c for c in KnowledgeBase().search_components() if c["id"] == cid)


@pytest.mark.parametrize("domain, category, n", [
    ("aocs", "adcs_integrated", 4), ("propulsion", "deorbit_devices", 6),
    ("payload", "payload_optics", 9), ("payload", "payload_controllers", 5),
])
async def test_catalog_lists_new_categories_under_their_domain(client, domain, category, n):
    r = await client.get(f"/api/engineering/equipment/{domain}/search")
    assert r.status_code == 200, r.text
    items = r.json()["categories"][category]
    assert len(items) == n
    assert all(i["component"]["sources"] for i in items)


async def test_catalog_with_a_study_scores_the_new_parts(client, study_obj):
    r = await client.get(f"/api/engineering/equipment/propulsion/search?study_id={study_obj.id}")
    assert r.status_code == 200, r.text
    ids = {i["component"]["id"] for i in r.json()["categories"]["deorbit_devices"]}
    assert SAIL in ids and "deorb-sfl-canx7-dsm" in ids        # null-mass reference entry still listed


async def _nfi_sat(client, sid: str) -> dict:
    sc = await make_element(client, sid, "Spacecraft", "system")
    subs = {d: (await make_element(client, sid, n, "subsystem", sc["id"], d))["id"]
            for d, n in (("aocs", "AOCS"), ("structure", "Structure"), ("payload", "Payload"))}
    out = {}
    for key, kid, dom, qty in (("adcs", ADCS, "aocs", 1), ("sail", SAIL, "structure", 1), ("cam", CAM, "payload", 1),
                               ("lens", LENS, "payload", 1), ("filter", FILTER, "payload", 1), ("ctrl", CTRL, "payload", 1)):
        kb = _kb(kid)
        # the body the Equipment Catalog's "+ Add" sends (workbench/EquipmentBrowser.tsx)
        r = await client.post(f"/api/elements/?study_id={sid}", json={
            "name": kb["name"], "element_type": "component", "parent_id": subs[dom], "segment": "space",
            "subsystem_domain": dom, "mass_kg": kb.get("mass_kg"), "power_avg_w": kb.get("power_w"),
            "cost_recurring_keur": kb.get("cost_keur"), "trl": kb.get("trl"), "manufacturer": kb.get("manufacturer"),
            "kb_component_id": kid, "quantity": qty})
        assert r.status_code == 200, r.text
        out[key] = r.json()
    out["subs"] = subs
    return out


async def test_selected_parts_show_in_the_equipment_budgets(client, study_obj):
    sid = study_obj.id
    els = await _nfi_sat(client, sid)
    assert (await client.post(f"/api/studies/{sid}/modes/template", json={})).status_code == 200
    assert (await client.post(f"/api/studies/{sid}/modes/propose")).status_code == 200
    ov = (await client.get(f"/api/studies/{sid}/modes")).json()
    classes = {u["id"]: u["unit_class"] for u in ov["units"]}
    assert classes[els["adcs"]["id"]] == "adcs_unit" and classes[els["sail"]["id"]] == "passive"
    assert classes[els["lens"]["id"]] == "passive" and classes[els["ctrl"]["id"]] == "payload_electronics"
    assert classes[els["cam"]["id"]] == "payload"

    eq = (await client.get(f"/api/studies/{sid}/budgets/equipment")).json()
    rows = {r["kb_component_id"]: r for r in eq["rows"]}
    kinds = {m["id"]: m["kind"] for m in eq["modes"]}
    for kid in (ADCS, SAIL, CAM, LENS, FILTER, CTRL):
        kb = _kb(kid)
        assert rows[kid]["mass_kg"] == pytest.approx(kb["mass_kg"]), kid
        assert rows[kid]["cost_keur"] == pytest.approx(kb["cost_keur"]), kid
    # mass and cost totals are the sum of the parts
    assert eq["totals"]["mass_cbe_kg"] == pytest.approx(sum(_kb(k)["mass_kg"] for k in rows), abs=1e-3)
    assert eq["totals"]["cost_keur"] == pytest.approx(sum(_kb(k)["cost_keur"] for k in rows), abs=0.01)

    def p(kid: str, kind: str) -> float:
        return next(v for mid, v in rows[kid]["power_by_mode_w"].items() if kinds[mid] == kind)

    # the integrated ADCS is on from LEOP (detumbling); wheels at peak while imaging
    assert p(ADCS, "leop") == pytest.approx(_kb(ADCS)["power_w"]) and p(ADCS, "imaging") > p(ADCS, "nominal")
    # the drag sail's release power is not a running load; optics draw nothing
    assert all(v == 0 for v in rows[SAIL]["power_by_mode_w"].values())
    assert all(v == 0 for v in rows[LENS]["power_by_mode_w"].values())
    # the controller runs with the camera while imaging, and adds no data of its own
    assert p(CTRL, "imaging") == pytest.approx(_kb(CTRL)["power_w"]) and p(CTRL, "safe") == 0
    data_imaging = next(v for mid, v in eq["totals"]["data_by_mode_bps"].items() if kinds[mid] == "imaging")
    assert data_imaging == pytest.approx(_kb(CAM)["performance"]["data_rate_mbps"] * 1e6, rel=1e-6)

    # the payload subsystem's mass budget carries camera + lens + filter + controller
    b = (await client.get(f"/api/elements/{els['subs']['payload']}/budget/mass")).json()
    assert {ln["element_id"] for ln in b["lines"]} == {els[k]["id"] for k in ("cam", "lens", "filter", "ctrl")}
    assert b["sum_nominal"] == pytest.approx(sum(_kb(k)["mass_kg"] for k in (CAM, LENS, FILTER, CTRL)), abs=1e-3)


async def test_needs_are_satisfied_by_integrated_adcs_and_drag_sail(client, study_obj):
    sid = study_obj.id
    before = {n["category"]: n for n in (await client.get(f"/api/engineering/equipment/needs/{sid}")).json()["needs"]}
    assert not before["reaction_wheels"]["satisfied"] and "adcs_integrated" in before["reaction_wheels"]["alternatives"]
    await _nfi_sat(client, sid)
    needs = {n["category"]: n for n in (await client.get(f"/api/engineering/equipment/needs/{sid}")).json()["needs"]}
    for part in ("reaction_wheels", "star_trackers", "magnetorquers", "sun_sensors"):
        assert needs[part]["satisfied_by"] == "adcs_integrated", part
    assert needs["deorbit_devices"]["satisfied_by"] == "deorbit_devices"
    if "thrusters" in needs:  # listed only when the mission needs delta-V
        assert needs["thrusters"]["satisfied_by"] == "deorbit_devices"
    assert not needs["batteries"]["satisfied"]
