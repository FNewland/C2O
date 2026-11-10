"""W1.01 (context-hash half), W1.02 and W1.10 acceptance on the Northern Fire and Ice fixture.

* W1.01: ``15``, ``15.0`` and ``"15"`` (and a JSON string against its decoded dict) give one
  context hash, so a run stays fresh after a restart that reloads the model from the database.
* W1.02: budget allocations survive a restart (``init_element_cache`` reloads them).
* W1.10: every KB id is unique, and every equipment id the fixture uses exists in the KB.
"""
from __future__ import annotations

import glob
import os

import pytest
import yaml

from tests.fixtures.nfi import load, seed_nfi


# ─────────────────────────────────────────────────────────────── W1.01

def test_canonical_hash_values():
    from spacecdf_server.services.analysis_context import _canonical
    assert _canonical(15) == _canonical(15.0) == _canonical("15") == _canonical(" 15 ") == 15
    assert _canonical("2.50") == _canonical(2.5) == 2.5
    assert _canonical('{"a": 1.0, "b": null}') == _canonical({"a": 1, "b": None}) == {"a": 1}
    assert _canonical([1.0, "3"]) == [1, 3]
    assert _canonical(True) is True and _canonical("abc") == "abc" and _canonical("1e3") == 1000
    assert _canonical(-0.0) == 0


def test_context_hash_ignores_number_spelling():
    from spacecdf_server.services.analysis_context import AnalysisContext, context_hash

    def ctx(v, perf):
        c = AnalysisContext(study_id="s", option_id=None)
        c.elements = [{"id": "e1", "name": "EPS", "mass_kg": v, "performance": perf, "quantity": 1}]
        c.requirements = [{"id": "r1", "threshold_value": v, "threshold_op": "<="}]
        return c

    keys = ["elements", "requirements"]
    h = context_hash(ctx(15, {"gsd_m": 58}), keys)
    assert h == context_hash(ctx(15.0, '{"gsd_m": 58.0}'), keys) == context_hash(ctx("15", {"gsd_m": "58"}), keys)
    assert h != context_hash(ctx(16, {"gsd_m": 58}), keys)


async def _restart() -> None:
    """What a server restart does to the caches: drop them, then reload from the database."""
    from spacecdf_server.routers import elements, requirements, studies
    elements._elements.clear()
    elements._interfaces.clear()
    elements._budget_allocations.clear()
    requirements.reset_requirement_cache()
    studies.get_study_store().clear()
    await studies.init_study_cache()
    await elements.init_element_cache()
    await requirements.init_requirement_cache()


async def test_runs_stay_fresh_after_a_restart(client):
    s = await seed_nfi(client, "S4")
    before = (await client.get(f"/api/studies/{s.study_id}/analyses")).json()
    runs = before.get("runs", before) if isinstance(before, dict) else before
    assert runs, before
    assert not [r for r in runs if r.get("stale")], [r["analysis"] for r in runs if r.get("stale")]
    await _restart()
    after = (await client.get(f"/api/studies/{s.study_id}/analyses")).json()
    runs = after.get("runs", after) if isinstance(after, dict) else after
    stale = [r["analysis"] for r in runs if r.get("stale")]
    assert stale == [], f"stale after restart: {stale}"


# ─────────────────────────────────────────────────────────────── W1.02

async def test_budget_allocations_survive_a_restart(client):
    s = await seed_nfi(client, "S2")
    targets = [s.elements["EPS"], s.elements["AOCS"], s.elements["Payload"]]
    for el, v in zip(targets, (1.8, 0.7, 0.75)):
        r = await client.post(f"/api/elements/{el['id']}/allocations",
                              json={"budget_type": "mass", "allocation_value": v, "unit": "kg"})
        assert r.status_code == 200, r.text
    assert len((await client.get(f"/api/studies/{s.study_id}/allocations")).json()) == 3
    await _restart()
    got = (await client.get(f"/api/studies/{s.study_id}/allocations")).json()
    assert sorted(a["allocation_value"] for a in got) == [0.7, 0.75, 1.8]
    # the Budget tab reads the allocation through the budget route
    b = (await client.get(f"/api/elements/{s.elements['EPS']['id']}/budget/mass")).json()
    assert b["allocation"] == pytest.approx(1.8)


# ─────────────────────────────────────────────────────────────── W1.10 + KB reconciliation

def _kb_components() -> dict[str, list[str]]:
    import spacecdf_kb
    root = os.path.join(os.path.dirname(spacecdf_kb.__file__), "data", "components")
    ids: dict[str, list[str]] = {}
    for f in sorted(glob.glob(os.path.join(root, "*.yaml"))):
        data = yaml.safe_load(open(f, encoding="utf-8")) or {}
        items = data if isinstance(data, list) else (data.get("components") or [])
        for it in items:
            ids.setdefault(str(it.get("id")), []).append(os.path.basename(f))
    return ids


def test_kb_component_ids_are_unique():
    dup = {k: v for k, v in _kb_components().items() if len(v) > 1}
    assert dup == {}, dup


def test_every_fixture_equipment_id_is_in_the_kb_with_its_category():
    from spacecdf_server.services.rule_inputs import kb_component
    eq = load("equipment")
    for sub in eq["spacecraft"]["subsystems"]:
        for it in sub["items"]:
            if it.get("custom"):
                continue
            part = kb_component({"kb_component_id": it["kb"]})
            assert part, f"{it['kb']} is not in the KB"
            if it.get("category"):
                assert part["category"] == it["category"], it["kb"]


def test_deorbit_devices_belong_to_the_propulsion_domain():
    from spacecdf_kb.mechanical import mechanical_of
    from spacecdf_server.routers.lifecycle import _EXAMPLE_CATEGORY_DOMAIN
    from spacecdf_server.services.equipment import DOMAIN_TO_CATEGORIES
    assert "deorbit_devices" in DOMAIN_TO_CATEGORIES["propulsion"]
    assert "deorbit_devices" not in DOMAIN_TO_CATEGORIES["structure"]
    assert _EXAMPLE_CATEGORY_DOMAIN["deorbit_devices"] == "propulsion"
    # a bare sail element in the propulsion domain is placed like a deorbit device, not a thruster
    assert mechanical_of(None, domain="propulsion", name="Drag sail")["face"] == "pz"
    assert mechanical_of(None, domain="propulsion", name="Cold-gas thruster")["face"] == "mx"


async def test_sail_is_offered_by_the_propulsion_catalog_and_counted(client):
    r = await client.get("/api/engineering/equipment/propulsion/search")
    assert r.status_code == 200, r.text
    cats = r.json()["categories"]
    assert any(str(m["component"]["id"]).startswith("deorb-") for m in cats.get("deorbit_devices") or [])
    assert "deorbit_devices" not in (await client.get("/api/engineering/equipment/structure/search")).json()["categories"]
    s = await seed_nfi(client, "S2")
    n = load("NUMBERS")
    ru = (await client.get(f"/api/studies/{s.study_id}/rollup?gate=mdr")).json()
    sail = s.elements["NPC Spacemind ARTICA drag sail (config A, 2.1 m2, 0.35U)"]
    assert any(u["element_id"] == sail["id"] for u in ru["mass"]["units"])
    assert ru["mass"]["cbe_kg"] == pytest.approx(n["mass"]["nominal_kg"], abs=0.01)
    bom = (await client.get(f"/api/lifecycle/bom/{s.study_id}")).json()
    line = next(l for l in bom["lines"] if l["name"].startswith("NPC Spacemind ARTICA"))
    assert line["subsystem"] == "Disposal (drag sail)" and line["subsystem_domain"] == "propulsion"
    # the BOM's space mass is the roll-up of the selected equipment (no phantom standard hardware)
    assert bom["summary"]["space_mass_kg"] == pytest.approx(ru["mass"]["cbe_kg"], abs=0.002)
