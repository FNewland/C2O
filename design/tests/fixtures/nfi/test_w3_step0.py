"""Wave 3, step 0 acceptance: the v2 baseline in the store, the recording seed, and the contracts
the seven parallel agents code against (stub routes, export sections, ``/phase``, key numbers).

Counts come from the fixture and the store, never typed in.
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import ELEMENT_IDS, load, seed_nfi

#: the wave-3 export sections of step 0 and their owners (W0_SEAMS §9); every one is real now
WAVE3_SECTIONS = {"stakeholders": "S", "allocations": "A", "validation": "S", "assumptions": "S", "changes": "L",
                  "open_items": "D", "negotiations": "H", "se_phase": "S",
                  # PI addendum
                  "semp": "X", "icds": "R", "reliability": "A", "thermal_model": "A", "debris": "L",
                  "change_control": "D", "cost": "A"}

#: one GET per wave-3 router (owner) and the write routes; none answers "not_implemented" any more
WAVE3_GETS = {"/moes": "S", "/validation/activities": "S", "/validation/need-validation": "S",
              "/validation/coverage": "S", "/assumptions": "S", "/negotiations": "H", "/sensitivity": "H",
              "/sensitivity/altitude": "H", "/changes": "L", "/open-items": "D", "/allocation-ledger": "A",
              "/icds": "R", "/reliability": "A", "/fmea": "A", "/thermal-model": "A", "/debris-assessment": "L",
              "/cost/items": "A", "/changes/ECP-01/control": "D"}
WAVE3_POSTS = ("/moes", "/stakeholders/import", "/validation/import", "/assumptions/import", "/negotiations",
               "/changes/import", "/impact/preview", "/open-items/import", "/allocation-ledger/import",
               "/icds/ICD-DEP-01/issue", "/reliability/run", "/fmea/propose", "/thermal-model/propose",
               "/debris-assessment/run", "/changes/ECP-01/control/start", "/cost/price")


async def test_s1_store_holds_the_v2_baseline_by_level(client):
    base = load("requirements")
    counts = base["baseline"]["counts"]
    s = await seed_nfi(client, "S1")
    assert s.report["forbidden"] == 0
    store = (await client.get(f"/api/studies/{s.study_id}/requirements/counts")).json()
    assert store["user"] == len(base["requirements"]) == counts["requirements"]
    assert store["objective"] == len(base["objectives"])
    assert store["stakeholder"] == len(base["stakeholder_needs"])
    lv = store["by_level"]
    assert lv["mission"] == counts["level_mission"] + len(base["objectives"])
    assert lv["segment"] == counts["level_segment"] and lv["system"] == counts["level_system"]
    assert lv["subsystem"] == counts["level_subsystem"]
    assert lv["interface"] == counts["level_interface"] + store["generated_interface"]
    # every v2 allocation code names an element the seed maps
    assert {a for r in base["requirements"] for a in r.get("allocation") or []} <= set(ELEMENT_IDS)
    els = {e["name"] for e in (await client.get(f"/api/studies/{s.study_id}/elements")).json()}
    assert set(ELEMENT_IDS.values()) <= els, set(ELEMENT_IDS.values()) - els


async def test_s0_contracts_phase_sections_and_wave3_routes(client):
    from spacecdf_server.app import app
    s = await seed_nfi(client, "S0")
    sid = s.study_id
    ph = (await client.get(f"/api/studies/{sid}/phase")).json()
    # the contract keys of step 0; 3.S1 fills them (tests/test_se)
    assert {"gate", "phase", "entry", "deliverables", "analysis", "coaching"} <= set(ph)
    assert ph["gate"] == "mdr" and ph["phase"] == "0"
    sx = (await client.get(f"/api/studies/{sid}/export-context")).json()
    import importlib
    for name in WAVE3_SECTIONS:   # every section is real and keeps the keys of its empty shape
        assert sx[name].get("status") != "not_implemented", name
        mod = importlib.import_module(f"spacecdf_server.services.export_context.sections.{name}")
        assert set(mod.empty()) <= set(sx[name]), name
    assert sx["errors"] == {}
    paths = app.openapi()["paths"]
    for p in WAVE3_GETS:
        assert f"/api/studies/{{study_id}}{p}".replace("ECP-01", "{change_id}") in paths, p
        r = await client.get(f"/api/studies/{sid}{p}")
        assert r.status_code in (200, 404), (p, r.status_code)   # 404 for an unknown change id at S0
        if r.status_code == 200 and isinstance(r.json(), dict):
            assert r.json().get("status") != "not_implemented", p
    for p in WAVE3_POSTS:
        r = await client.post(f"/api/studies/{sid}{p}", json={})
        assert r.status_code < 500, (p, r.status_code)
    assert (await client.get("/api/studies/nope/moes")).status_code == 404


async def test_s2_key_numbers_and_margin_policy_route(client):
    b = load("budgets")
    s = await seed_nfi(client, "S2")
    kn = (await client.get(f"/api/studies/{s.study_id}/key-numbers?gate=pdr")).json()["items"]
    assert kn["mass.with_system_margin_kg"]["value"] == pytest.approx(b["mass"]["totals"]["with_system_margin_kg"], abs=0.01)
    assert kn["mass.with_system_margin_kg"]["owner_seat"] == "systems_engineer"
    assert kn["power.orbit_average_with_margin_w"]["value"] == pytest.approx(
        b["power"]["totals"]["with_system_margin_w"], abs=0.02)
    assert kn["mass.margin_to_limit_kg"]["value"] == pytest.approx(b["mass"]["totals"]["margin_to_limit_kg"], abs=0.01)
    assert all({"value", "unit", "source", "owner_seat"} <= set(v) for v in kn.values())
    mp = (await client.get(f"/api/studies/{s.study_id}/margin-policy")).json()
    assert mp["margin_policy"]["study_override"]["through_gate"] == "pdr"
    bad = await client.put(f"/api/studies/{s.study_id}/margin-policy", json={"study_override": {"percent": 80}})
    assert bad.status_code == 422
    # clearing the hold gives the ladder back at PDR
    await client.put(f"/api/studies/{s.study_id}/margin-policy", json={"study_override": None})
    ru = (await client.get(f"/api/studies/{s.study_id}/rollup?gate=pdr")).json()
    assert ru["mass"]["system_margin_source"] == "ladder" and ru["margin_hold"] is None
    assert ru["mass"]["system_margin_percent"] == b["margin_policy"]["course_textbook_ladder"]["PDR"]


async def test_recording_seed_leaves_the_licensing_tab_empty(client):
    """PI ruling: the team fills the Licensing tab on camera; the recording seed skips it."""
    s = await seed_nfi(client, "S4", recording=True)
    assert s.recording and s.report["forbidden"] == 0
    lic = (await client.get(f"/api/lifecycle/licensing/{s.study_id}")).json()
    assert not (lic["record"].get("applicant") or {}).get("legal_name")
    assert not (lic["record"].get("cdpp") or {}).get("command_facility")
