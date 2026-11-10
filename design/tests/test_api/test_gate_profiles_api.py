"""Gate engine v2 (WP6, Nov 2026): profiles as data, server-only checklists, gate states,
baseline snapshots, MCR→MDR migration, and the logbook's decisions-due per profile."""
from __future__ import annotations

import pytest

from spacecdf_common.models.mission_need import MissionNeed
from spacecdf_common.models.study import DesignIteration, Study
from spacecdf_server.services import gate_profiles as gp
from spacecdf_server.services.gate_reviews import GateTransitionError, display_state, transition
from tests.test_api.test_wp0_basics import WIZARD_NEED

IAP = {"x-goog-authenticated-user-email": "accounts.google.com:bob@example.org"}


# ── profiles as data ───────────────────────────────────────────────────────

def test_profiles_validate_and_full_ecss_is_the_default():
    assert gp.validate() == []
    assert gp.default_profile_id() == "full_ecss"
    assert [g["id"] for g in gp.get_profile(None)["gates"]] == ["mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr"]


@pytest.mark.parametrize("profile,gates,covers", [
    ("full_ecss", ["MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR"],
     [["mdr"], ["prr"], ["srr"], ["pdr"], ["cdr"], ["qr"], ["ar"], ["frr"]]),
    ("esa_iod", ["CR", "PDR", "CDR"], [["mdr", "prr"], ["srr", "pdr"], ["cdr"]]),
    ("c2o_3gate", ["MDR", "PRR+SRR", "PDR"], [["mdr"], ["prr", "srr"], ["pdr"]]),
    ("nasa", ["MCR", "SRR", "MDR/SDR", "PDR", "CDR"], [["mdr"], ["prr"], ["srr"], ["pdr"], ["cdr"]]),
])
def test_profile_gates(profile, gates, covers):
    p = gp.get_profile(profile)
    assert [g["short"] for g in p["gates"]] == gates
    assert [g["covers"] for g in p["gates"]] == covers
    assert all(g["name"]["en"] and g["name"]["fr"] for g in p["gates"])


def test_gate_lookup_accepts_legacy_and_merged_ids():
    iod = gp.get_profile("esa_iod")
    assert gp.gate_of(iod, "cr")["id"] == "cr"
    assert gp.gate_of(iod, "mdr")["id"] == "cr" and gp.gate_of(iod, "mcr")["id"] == "cr"
    assert gp.gate_of(gp.get_profile("full_ecss"), "MCR")["id"] == "mdr"
    assert gp.due_canonical(gp.gate_of(gp.get_profile("c2o_3gate"), "prr")) == ["mdr", "prr", "srr"]
    assert gp.margin_gate(gp.gate_of(iod, "cr")) == "prr"


def test_bad_profile_is_reported():
    data = {"default_profile": "x", "profiles": {"x": {"label": {"en": "X", "fr": "X"}, "gates": [
        {"id": "a", "name": {"en": "A", "fr": "A"}, "covers": ["mdr", "srr"]}]}}, "steps": {}}
    errs = gp.validate(data)
    assert any("cover" in e for e in errs)


# ── API ────────────────────────────────────────────────────────────────────

async def test_profiles_endpoint(client):
    body = (await client.get("/api/gate-profiles")).json()
    assert body["default"] == "full_ecss" and body["errors"] == []
    assert {p["id"] for p in body["profiles"]} == {"full_ecss", "esa_iod", "c2o_3gate", "nasa"}
    assert body["steps"]["S1"]["fr"]


async def test_prr_is_shown_with_its_criteria_and_owners(client, study_obj):
    g = (await client.get(f"/api/studies/{study_obj.id}/rules/gates/prr")).json()
    assert g["gate"]["short"] == "PRR" and g["profile"]["id"] == "full_ecss"
    ids = [c["id"] for c in g["criteria"]]
    assert ids[0] == "PRR-EC-01" and len(ids) == 12
    c = g["criteria"][0]
    assert c["owner_seat"] == "systems_engineer" and c["owner_seat_label"]["fr"]
    assert c["step"] == "S4" and c["step_label"] == {"en": "Alternatives", "fr": "Solutions de rechange"}
    assert {x["id"] for x in g["checks"]} == {"GC-PRODUCT-TREE", "GC-MARGINS"}
    assert g["system_margin"] == {"gate": "prr", "mass_percent": 20.0, "power_percent": 20.0}


async def test_merged_gate_holds_the_criteria_of_both(client, study_obj):
    assert (await client.put(f"/api/studies/{study_obj.id}/gate-profile", json={"profile": "esa_iod"})).status_code == 200
    g = (await client.get(f"/api/studies/{study_obj.id}/rules/gates/cr")).json()
    ids = [c["id"] for c in g["criteria"]]
    assert ids[:10] == [f"MDR-EC-{i:02d}" for i in range(1, 11)] and ids[10:] == [f"PRR-EC-{i:02d}" for i in range(1, 13)]
    assert g["gate"]["covers"] == ["mdr", "prr"]
    assert (await client.get(f"/api/studies/{study_obj.id}/rules/gates/srr")).json()["gate"]["id"] == "pdr"
    assert (await client.put(f"/api/studies/{study_obj.id}/gate-profile", json={"profile": "nope"})).status_code == 400
    assert (await client.get(f"/api/studies/{study_obj.id}/rules/gates/xyz")).status_code == 404


async def test_nasa_skin_only_relabels(client, study_obj):
    await client.put(f"/api/studies/{study_obj.id}/gate-profile", json={"profile": "nasa"})
    ov = (await client.get(f"/api/studies/{study_obj.id}/gates")).json()
    assert [g["short"] for g in ov["gates"]] == ["MCR", "SRR", "MDR/SDR", "PDR", "CDR"]
    g = (await client.get(f"/api/studies/{study_obj.id}/rules/gates/mdr")).json()
    assert g["gate"]["short"] == "MCR" and g["criteria"][0]["id"] == "MDR-EC-01"


# ── states and baselines ───────────────────────────────────────────────────

def _ready_study(sid: str) -> Study:
    s = Study(id=sid, name="Ready study", mission_need=MissionNeed(**WIZARD_NEED))
    s.iterations = [DesignIteration(iteration=1, max_parameter_delta=0, parameter_snapshot={
        "systems.mass_margin_percent": 12.0, "systems.power_margin_percent": 30.0})]
    return s


async def test_state_machine_and_baseline(client, study):
    from spacecdf_server.routers.studies import get_study_store
    get_study_store()[study] = _ready_study(study)
    ov = (await client.get(f"/api/studies/{study}/gates")).json()
    assert ov["current_gate"] == "mdr" and ov["gates"][0]["state"] == "ready"
    assert ov["gates"][1]["state"] == "not_ready"

    url = f"/api/studies/{study}/gates/mdr/review"
    assert (await client.post(url, json={"action": "pass"})).status_code == 409   # not under review
    r = await client.post(url, json={"action": "start"}, headers=IAP)
    assert r.status_code == 200 and r.json()["state"] == "under_review"
    r = await client.post(url, json={"action": "pass"}, headers=IAP)
    body = r.json()
    assert body["state"] == "passed"
    base = body["baselines"][0]
    assert base["id"] and base["by"] == "bob@example.org"
    assert "mission_statement" in base["products"] and "objectives" in base["products"]
    snap = (await client.get(f"/api/studies/{study}/gates/baselines/{base['id']}")).json()
    assert snap["snapshot"]["mission_need"]["problem_statement"].startswith("Wildfires")
    assert snap["gate"] == "mdr" and snap["profile"] == "full_ecss"
    # the study now prepares for the PRR: budgets use the PRR margin step
    assert (await client.get(f"/api/studies/{study}/gates")).json()["current_gate"] == "prr"
    lad = (await client.get(f"/api/studies/{study}/rules/margin-ladder")).json()
    assert lad["gate"] == "prr" and lad["mass_percent"] == 20.0
    r = await client.post(url, json={"action": "reopen"})
    assert r.json()["state"] == "reopened"
    hist = [h["action"] for h in r.json()["history"]]
    assert hist == ["start", "pass", "reopen"]


async def test_cannot_start_a_review_that_is_not_ready(client, study_obj):
    r = await client.post(f"/api/studies/{study_obj.id}/gates/prr/review", json={"action": "start"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_ready"


def test_transitions_pure():
    e = transition(None, "start", ready=True, by="a")
    assert e["state"] == "under_review"
    with pytest.raises(GateTransitionError):
        transition(e, "start", ready=True)
    with pytest.raises(GateTransitionError) as exc:
        transition(e, "pass", ready=False)
    assert exc.value.code == "not_ready"
    assert transition(e, "cancel", ready=True)["state"] is None
    p = transition(e, "pass", ready=True)
    assert display_state(p, ready=False) == "passed"
    r = transition(p, "reopen", ready=False)
    assert display_state(r, ready=False) == "reopened"
    assert display_state(None, ready=True) == "ready" and display_state(None, ready=False) == "not_ready"


# ── migration of studies that have "MCR" data ──────────────────────────────

def test_stored_mcr_gate_state_migrates_to_mdr():
    s = Study(**{"id": "old", "name": "Old", "gate_states": {"mcr": {"state": "passed",
                 "history": [{"gate": "MCR", "action": "pass"}]}}})
    assert "mcr" not in s.gate_states and s.gate_states["mdr"]["state"] == "passed"
    assert s.gate_states["mdr"]["history"][0]["gate"] == "mdr"
    assert s.gate_profile == "" and gp.get_profile(s.gate_profile or None)["id"] == "full_ecss"


async def test_old_mcr_urls_still_work(client, study_obj):
    g = (await client.get(f"/api/studies/{study_obj.id}/rules/gates/mcr")).json()
    assert g["gate"]["id"] == "mdr"
    r = await client.get(f"/api/ecss/gate-evaluate/{study_obj.id}/MCR")
    assert r.json()["gate"] == "MDR"


# ── logbook: decisions due follow the study's profile ──────────────────────

async def test_logbook_decisions_due_follow_the_profile(client, study_obj):
    sid = study_obj.id
    full = (await client.get(f"/api/logbook/decisions?study_id={sid}&gate=prr")).json()
    prr_ids = {d["id"] for d in full["decisions"] if d["ecss_gate"] == "prr"}
    assert prr_ids and prr_ids <= set(full["due"]["open"]), "PRR decisions are due at the PRR"
    assert not any(d["ecss_gate"] == "srr" and d["id"] in full["due"]["open"] for d in full["decisions"])
    assert [g["short"] for g in full["gates"]] == ["MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR"]

    await client.put(f"/api/studies/{sid}/gate-profile", json={"profile": "esa_iod"})
    iod = (await client.get(f"/api/logbook/decisions?study_id={sid}&gate=cr&lang=fr")).json()
    assert [g["id"] for g in iod["gates"]] == ["cr", "pdr", "cdr"]
    assert iod["gates"][0]["label"].startswith("CR — revue de concept")
    assert iod["due"]["gate"] == "cr" and iod["due"]["short"] == "CR"
    assert {d["gate"] for d in iod["decisions"]} == {"cr", "pdr", "cdr"}
    assert prr_ids <= set(iod["due"]["open"]), "the concept review holds the PRR decisions"

    await client.put(f"/api/studies/{sid}/gate-profile", json={"profile": "c2o_3gate"})
    c2o = (await client.get(f"/api/logbook/decisions?study_id={sid}&gate=prr")).json()
    srr_ids = {d["id"] for d in c2o["decisions"] if d["ecss_gate"] == "srr"}
    assert srr_ids <= set(c2o["due"]["open"]), "PRR+SRR holds the SRR decisions too"
