"""SpaceCDF seats (redesign WP9): seats, handover, ownership with pending changes (ruling 5),
role permissions on the server, the instructor class board and the timeline export.

Identity is simulated the way it arrives in production: ``X-Goog-Authenticated-User-Email``
from Google IAP, or ``X-C2O-Client`` + ``X-C2O-Name`` in laptop mode.
"""
from __future__ import annotations

import time

import pytest

from tests.test_api.conftest import make_element

INSTRUCTOR = "prof@c2o.live"


def iap(email: str, name: str | None = None, seat: str | None = None, confirm: bool = False) -> dict:
    h = {"X-Goog-Authenticated-User-Email": f"accounts.google.com:{email}"}
    if name:
        h["X-C2O-Name"] = name
    if seat:
        h["X-C2O-Seat"] = seat
    if confirm:
        h["X-C2O-Confirm-Review"] = "1"
    return h


TL = iap("tl@c2o.live", "Alex")
PWR = iap("power@c2o.live", "Alex")          # same display name, different person
TH = iap("thermal@c2o.live", "Sam")
PROF = iap(INSTRUCTOR, "Prof")


@pytest.fixture(autouse=True)
def _seat_env(monkeypatch):
    from spacecdf_server.seats import store
    from spacecdf_server.seats.instructor import invalidate_gate_cache
    monkeypatch.setenv("SPACECDF_INSTRUCTORS", INSTRUCTOR)
    monkeypatch.delenv("SMO_INSTRUCTORS", raising=False)
    store.reset_memory()
    invalidate_gate_cache()
    yield
    store.reset_memory()


async def seat_study(client, study, size="9"):
    r = await client.post(f"/api/studies/{study}/team/preset", json={"team_size": size}, headers=PROF)
    assert r.status_code == 200, r.text
    assert r.json()["enabled"] is True
    return r.json()


async def claim(client, study, headers, *seats, status=200):
    r = await client.post(f"/api/studies/{study}/team/claim", json={"seats": list(seats)}, headers=headers)
    assert r.status_code == status, r.text
    return r.json()


async def power_tree(client, study):
    root = await make_element(client, study, "Mission", "mission")
    sc = await make_element(client, study, "Spacecraft", "system", parent_id=root["id"])
    eps = await make_element(client, study, "EPS", "subsystem", parent_id=sc["id"], subsystem_domain="power")
    tcs = await make_element(client, study, "Thermal", "subsystem", parent_id=sc["id"], subsystem_domain="thermal")
    return root, sc, eps, tcs


# ─── identity and claiming ──────────────────────────────────────────────────

async def test_same_display_name_different_iap_emails_stay_distinct(client, study_obj, study):
    await seat_study(client, study)
    await claim(client, study, TL, "team_leader")
    await claim(client, study, PWR, "power_engineer")
    team = (await client.get(f"/api/studies/{study}/team", headers=TL)).json()
    holders = {s["id"]: s["holders"] for s in team["seats"]}
    assert holders["team_leader"][0]["person_id"] == "iap:tl@c2o.live"
    assert holders["power_engineer"][0]["person_id"] == "iap:power@c2o.live"
    assert holders["team_leader"][0]["name"] == holders["power_engineer"][0]["name"] == "Alex"
    assert team["me"]["held"] == ["team_leader"]
    me2 = (await client.get(f"/api/studies/{study}/team", headers=PWR)).json()["me"]
    assert me2["held"] == ["power_engineer"] and me2["verified"] is True


async def test_laptop_names_are_distinct_and_unverified(client, study_obj, study):
    await seat_study(client, study)
    a = {"X-C2O-Client": "browser-a", "X-C2O-Name": "Kim"}
    b = {"X-C2O-Client": "browser-b", "X-C2O-Name": "Kim"}
    await claim(client, study, a, "payload_lead")
    r = await client.post(f"/api/studies/{study}/team/claim", json={"seats": ["payload_lead"]}, headers=b)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "seat_held"
    me = (await client.get(f"/api/studies/{study}/team", headers=a)).json()["me"]
    assert me["id"] == "local:browser-a" and me["verified"] is False


async def test_exclusive_seat_refuses_second_holder_shared_seats_do_not(client, study_obj, study):
    await seat_study(client, study)
    await claim(client, study, TL, "systems_engineer")
    r = await client.post(f"/api/studies/{study}/team/claim", json={"seats": ["systems_engineer"]}, headers=PWR)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "seat_held"
    await claim(client, study, PWR, "observer")
    await claim(client, study, TH, "observer")
    team = (await client.get(f"/api/studies/{study}/team", headers=TL)).json()
    obs = next(s for s in team["seats"] if s["id"] == "observer")
    assert len(obs["holders"]) == 2


async def test_group_claim_in_four_person_preset_is_all_or_nothing(client, study_obj, study):
    team = await seat_study(client, study, "4")
    assert ["power_engineer", "thermal_engineer"] in team["groups"]
    await claim(client, study, TH, "thermal_engineer")
    r = await client.post(f"/api/studies/{study}/team/claim",
                          json={"seats": ["power_engineer", "thermal_engineer"]}, headers=PWR)
    assert r.status_code == 409
    me = (await client.get(f"/api/studies/{study}/team", headers=PWR)).json()["me"]
    assert me["held"] == []


async def test_handover_request_accept_is_logged(client, study_obj, study):
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    r = await client.post(f"/api/studies/{study}/team/request", json={"seat": "power_engineer"}, headers=TH)
    assert r.status_code == 200 and r.json()["claimed"] is False
    assert r.json()["request"]["timeout_s"] == 60
    # the holder sees the request and accepts
    me = (await client.get(f"/api/studies/{study}/team", headers=PWR)).json()["me"]
    assert me["requests_to_me"][0]["seat"] == "power_engineer"
    r = await client.post(f"/api/studies/{study}/team/answer", json={"seat": "power_engineer", "accept": True}, headers=PWR)
    assert r.status_code == 200
    me = (await client.get(f"/api/studies/{study}/team", headers=TH)).json()["me"]
    assert me["held"] == ["power_engineer"]
    acts = [(e["action"], e["person_id"]) for e in (await client.get(f"/api/studies/{study}/team/events", headers=TL)).json()]
    assert ("handover_request", "iap:thermal@c2o.live") in acts
    assert ("handover_accept", "iap:power@c2o.live") in acts


async def test_handover_request_times_out(client, study_obj, study):
    from spacecdf_server.seats import store
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    await client.post(f"/api/studies/{study}/team/request", json={"seat": "power_engineer"}, headers=TH)
    store._team[study]["requests"]["power_engineer"]["expires"] = time.time() - 1
    r = await client.post(f"/api/studies/{study}/team/answer", json={"seat": "power_engineer", "accept": True}, headers=PWR)
    assert r.status_code == 404


async def test_idle_seat_is_reclaimable_after_grace(client, study_obj, study):
    from spacecdf_server.seats import store
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    store._presence[study]["iap:power@c2o.live"]["last"] = time.time() - 200    # 3 min 20 s: idle
    team = (await client.get(f"/api/studies/{study}/team", headers=TH)).json()
    assert next(s for s in team["seats"] if s["id"] == "power_engineer")["state"] == "idle"
    r = await client.post(f"/api/studies/{study}/team/claim", json={"seats": ["power_engineer"]}, headers=TH)
    assert r.status_code == 409                                                     # not yet reclaimable
    store._presence[study]["iap:power@c2o.live"]["last"] = time.time() - 600     # idle 5 min more
    await claim(client, study, TH, "power_engineer")
    evs = (await client.get(f"/api/studies/{study}/team/events", headers=TL)).json()
    assert evs[0]["action"] == "reclaim" and evs[0]["detail"]["from_person"] == "iap:power@c2o.live"


async def test_instructor_reassign_and_lock(client, study_obj, study):
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    r = await client.post(f"/api/studies/{study}/team/reassign",
                          json={"seat": "power_engineer", "person_id": "iap:thermal@c2o.live", "name": "Sam"}, headers=TL)
    assert r.status_code == 403
    r = await client.post(f"/api/studies/{study}/team/reassign",
                          json={"seat": "power_engineer", "person_id": "iap:thermal@c2o.live", "name": "Sam"}, headers=PROF)
    assert r.status_code == 200
    me = (await client.get(f"/api/studies/{study}/team", headers=TH)).json()["me"]
    assert me["held"] == ["power_engineer"]
    assert (await client.post(f"/api/studies/{study}/team/lock", json={"seat": "power_engineer"}, headers=PROF)).status_code == 200
    r = await client.post(f"/api/studies/{study}/team/release", json={"seat": "power_engineer"}, headers=TH)
    assert r.status_code == 423
    r = await client.post(f"/api/studies/{study}/team/claim", json={"seats": ["power_engineer"]}, headers=PWR)
    assert r.status_code == 423


async def test_active_seat_switch(client, study_obj, study):
    await seat_study(client, study, "4")
    await claim(client, study, TL, "team_leader", "systems_engineer")
    r = await client.post(f"/api/studies/{study}/team/active", json={"seat": "systems_engineer"}, headers=TL)
    assert r.json()["me"]["active"] == "systems_engineer"
    r = await client.post(f"/api/studies/{study}/team/active", json={"seat": "power_engineer"}, headers=TL)
    assert r.status_code == 409


# ─── ownership and pending changes (ruling 5) ───────────────────────────────

async def test_cross_seat_edit_warns_then_goes_to_review_then_accept(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, TL, "team_leader")
    await claim(client, study, PWR, "power_engineer")
    body = {"version": eps["version"], "mass_kg": 2.5}
    # 1. warning first
    r = await client.patch(f"/api/elements/{eps['id']}", json=body, headers=TL)
    assert r.status_code == 409
    d = r.json()["detail"]
    assert d["code"] == "owned_by_other_seat" and d["owner_seat"] == "power_engineer"
    assert d["owner_label"]["fr"] == "Puissance" and d["param_keys"] == ["power.mass_kg"]
    # 2. the editor continues: stored as a pending change, the owner's value stands
    r = await client.patch(f"/api/elements/{eps['id']}", json=body, headers={**TL, "X-C2O-Confirm-Review": "1"})
    assert r.status_code == 202
    pc = r.json()["pending_change"]
    assert pc["owner_seat"] == "power_engineer" and pc["by_seat"] == "team_leader"
    assert r.json()["mass_kg"] is None
    assert (await client.get(f"/api/elements/{eps['id']}")).json()["mass_kg"] is None
    inbox = (await client.get(f"/api/studies/{study}/team/pending?seat=power_engineer", headers=PWR)).json()
    assert [p["id"] for p in inbox] == [pc["id"]] and inbox[0]["new"] == {"mass_kg": 2.5}
    nxt = (await client.get(f"/api/studies/{study}/team/next?seat=power_engineer", headers=PWR)).json()
    assert nxt["kind"] in ("gate_item", "proposals")
    # 3. only the owning seat reviews
    r = await client.post(f"/api/studies/{study}/team/pending/{pc['id']}/accept", json={}, headers=TL)
    assert r.status_code == 403
    r = await client.post(f"/api/studies/{study}/team/pending/{pc['id']}/accept", json={"comment": "ok"}, headers=PWR)
    assert r.status_code == 200 and r.json()["status"] == "accepted"
    assert (await client.get(f"/api/elements/{eps['id']}")).json()["mass_kg"] == 2.5
    acts = [e["action"] for e in (await client.get(f"/api/studies/{study}/team/events", headers=TL)).json()]
    assert "propose" in acts and "accept" in acts


async def test_reject_needs_comment_and_keeps_owner_value(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, TH, "thermal_engineer")
    await claim(client, study, PWR, "power_engineer")
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "power_avg_w": 9.0},
                           headers={**TH, "X-C2O-Confirm-Review": "1"})
    pc = r.json()["pending_change"]
    r = await client.post(f"/api/studies/{study}/team/pending/{pc['id']}/reject", json={"comment": ""}, headers=PWR)
    assert r.status_code == 400
    r = await client.post(f"/api/studies/{study}/team/pending/{pc['id']}/reject",
                          json={"comment": "Heater power is in the thermal budget"}, headers=PWR)
    assert r.json()["status"] == "rejected"
    assert (await client.get(f"/api/elements/{eps['id']}")).json()["power_avg_w"] is None
    mine = (await client.get(f"/api/studies/{study}/team/pending?mine=1&status=all", headers=TH)).json()
    assert mine[0]["comment"] == "Heater power is in the thermal budget"


async def test_owner_edits_directly_and_layout_is_free(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    await claim(client, study, TH, "thermal_engineer")
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.2}, headers=PWR)
    assert r.status_code == 200 and r.json()["mass_kg"] == 1.2
    v = r.json()["version"]
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": v, "diagram_x": 40.0}, headers=TH)
    assert r.status_code == 200 and r.json()["diagram_x"] == 40.0
    ev = next(e for e in (await client.get(f"/api/studies/{study}/team/events", headers=PWR)).json()
              if e["action"] == "edit" and e["detail"]["fields"] == ["mass_kg"])
    assert ev["seat_id"] == "power_engineer" and ev["person_id"] == "iap:power@c2o.live"


async def test_team_leader_holding_owner_seat_edits_directly(client, study_obj, study):
    _, sc, _, _ = await power_tree(client, study)
    await seat_study(client, study, "4")
    await claim(client, study, TL, "team_leader", "systems_engineer")
    r = await client.patch(f"/api/elements/{sc['id']}", json={"version": sc["version"], "mass_kg": 6.0}, headers=TL)
    assert r.status_code == 200 and r.json()["mass_kg"] == 6.0


async def test_instructor_follows_the_same_rule(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 3.0}, headers=PROF)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "owned_by_other_seat"
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 3.0},
                           headers={**PROF, "X-C2O-Confirm-Review": "1"})
    assert r.status_code == 202 and r.json()["pending_change"]["by_seat"] == "instructor"


async def test_parameter_put_goes_to_review_and_accept_applies(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, TL, "team_leader")
    await claim(client, study, PWR, "power_engineer")
    url = f"/api/elements/{eps['id']}/parameters/battery_capacity_wh"
    r = await client.put(url, json={"manual_value": 40.0, "unit": "Wh"}, headers=TL)
    assert r.status_code == 409
    r = await client.put(url, json={"manual_value": 40.0, "unit": "Wh"}, headers={**TL, "X-C2O-Confirm-Review": "1"})
    assert r.status_code == 202
    pc = r.json()["pending_change"]
    assert pc["param_keys"] == ["power.battery_capacity_wh"]
    params = (await client.get(f"/api/elements/{eps['id']}/parameters")).json()
    assert not any(p["name"] == "battery_capacity_wh" for p in params)
    r = await client.post(f"/api/studies/{study}/team/pending/{pc['id']}/accept", json={}, headers=PWR)
    assert r.status_code == 200, r.text
    params = (await client.get(f"/api/elements/{eps['id']}/parameters")).json()
    assert next(p for p in params if p["name"] == "battery_capacity_wh")["effective_value"] == 40.0


async def test_solo_study_is_unchanged(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.0})
    assert r.status_code == 200
    assert (await client.delete(f"/api/elements/{eps['id']}")).status_code == 200


# ─── role permissions (server side) ─────────────────────────────────────────

async def test_observer_and_seatless_cannot_write(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.0}, headers=TH)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "no_seat"
    await claim(client, study, TH, "observer")
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.0}, headers=TH)
    assert r.json()["detail"]["code"] == "observer_read_only"
    r = await client.post(f"/api/studies/{study}/risks", json={"description": "x"}, headers=TH)
    assert r.status_code == 403
    r = await client.delete(f"/api/elements/{eps['id']}", headers=TH)
    assert r.status_code == 403


async def test_customer_writes_mission_requirements_only(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    cust = iap("customer@agency.ca", "Client")
    await claim(client, study, cust, "customer")
    r = await client.post("/api/requirements/", json={"id": "MIS-9", "study_id": study, "level": "mission",
                                                      "text": "Detect fires within 6 h"}, headers=cust)
    assert r.status_code == 200, r.text
    r = await client.patch("/api/requirements/MIS-9", json={"text": "Detect fires within 3 h"}, headers=cust)
    assert r.status_code == 200
    r = await client.post("/api/requirements/", json={"id": "SYS-9", "study_id": study, "level": "system",
                                                      "text": "x"}, headers=cust)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "customer_requirements_only"
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.0}, headers=cust)
    assert r.status_code == 403
    r = await client.post(f"/api/studies/{study}/gates/mdr/review", json={"action": "start"}, headers=cust)
    assert r.status_code == 403


async def test_gate_decisions_team_leader_or_instructor_only(client, study_obj, study):
    await seat_study(client, study)
    await claim(client, study, TL, "team_leader")
    await claim(client, study, PWR, "power_engineer")
    url = f"/api/studies/{study}/gates/mdr/review"
    r = await client.post(url, json={"action": "start"}, headers=PWR)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "lead_only"
    r = await client.post(url, json={"action": "start"}, headers=TL)
    assert r.status_code in (200, 409)            # 409 = not ready: the permission passed
    r = await client.put(f"/api/studies/{study}/gate-profile", json={"profile": "esa_iod"}, headers=PWR)
    assert r.status_code == 403
    assert (await client.put(f"/api/studies/{study}/gate-profile", json={"profile": "esa_iod"}, headers=PROF)).status_code == 200


async def test_element_delete_owner_lead_or_systems(client, study_obj, study):
    _, _, eps, tcs = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, TH, "thermal_engineer")
    await claim(client, study, TL, "team_leader")
    assert (await client.delete(f"/api/elements/{eps['id']}", headers=TH)).status_code == 403
    assert (await client.delete(f"/api/elements/{tcs['id']}", headers=TH)).status_code == 200
    assert (await client.delete(f"/api/elements/{eps['id']}", headers=TL)).status_code == 200


async def test_only_instructor_deletes_studies(client, study_obj, study):
    await seat_study(client, study)
    await claim(client, study, TL, "team_leader")
    r = await client.delete(f"/api/studies/{study}", headers=TL)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "instructor_only"
    assert (await client.delete(f"/api/studies/{study}", headers=PROF)).status_code == 200


async def test_smo_instructors_variable_is_accepted(client, study_obj, study, monkeypatch):
    monkeypatch.delenv("SPACECDF_INSTRUCTORS")
    monkeypatch.setenv("SMO_INSTRUCTORS", "ops-lead@c2o.live, other@c2o.live")
    me = (await client.get("/api/seats/me", headers=iap("ops-lead@c2o.live"))).json()
    assert me["instructor"] is True and me["instructor_mode"] == "list"
    assert (await client.get("/api/seats/me", headers=PROF)).json()["instructor"] is False


async def test_laptop_first_instructor_only_without_list(client, study_obj, study, monkeypatch):
    monkeypatch.delenv("SPACECDF_INSTRUCTORS")
    a = {"X-C2O-Client": "laptop-a", "X-C2O-Name": "Franz"}
    b = {"X-C2O-Client": "laptop-b", "X-C2O-Name": "Student"}
    # nobody is instructor yet: deleting studies stays open (single-user laptop)
    me = (await client.get("/api/seats/me", headers=a)).json()
    assert me["instructor"] is False and me["instructor_mode"] == "laptop"
    r = await client.post("/api/seats/instructor/claim", headers=a)
    assert r.status_code == 200 and r.json()["instructor"] is True
    assert (await client.post("/api/seats/instructor/claim", headers=b)).status_code == 409
    assert (await client.get("/api/instructor/board", headers=b)).status_code == 403
    assert (await client.get("/api/instructor/board", headers=a)).status_code == 200
    assert (await client.delete(f"/api/studies/{study}", headers=b)).status_code == 403
    # with a list configured the laptop claim is refused
    monkeypatch.setenv("SPACECDF_INSTRUCTORS", INSTRUCTOR)
    assert (await client.post("/api/seats/instructor/claim", headers=b)).status_code == 409


async def test_frozen_study_refuses_writes(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    assert (await client.post(f"/api/instructor/studies/{study}/freeze", json={"frozen": True}, headers=PWR)).status_code == 403
    assert (await client.post(f"/api/instructor/studies/{study}/freeze", json={"frozen": True}, headers=PROF)).status_code == 200
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.0}, headers=PWR)
    assert r.status_code == 423
    await client.post(f"/api/instructor/studies/{study}/freeze", json={"frozen": False}, headers=PROF)
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.0}, headers=PWR)
    assert r.status_code == 200


# ─── subscriptions and the wanted-vs-provided ledger ─────────────────────────

async def test_subscription_changed_marker_and_ledger(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    await claim(client, study, TH, "thermal_engineer")
    await claim(client, study, TL, "systems_engineer")
    subs = (await client.post(f"/api/studies/{study}/team/subscriptions",
                              json={"seat": "thermal_engineer", "element_id": eps["id"], "field": "power_avg_w"},
                              headers=TH)).json()
    assert subs[0]["owner_seat"] == "power_engineer" and subs[0]["changed"] is False
    await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "power_avg_w": 4.0}, headers=PWR)
    subs = (await client.get(f"/api/studies/{study}/team/subscriptions?seat=thermal_engineer", headers=TH)).json()
    assert subs[0]["changed"] is True and subs[0]["value"] == 4.0
    nxt = (await client.get(f"/api/studies/{study}/team/next?seat=thermal_engineer", headers=TH)).json()
    assert nxt["kind"] in ("gate_item", "subscriptions")
    subs = (await client.post(f"/api/studies/{study}/team/subscriptions/seen", json={"seat": "thermal_engineer"},
                              headers=TH)).json()
    assert subs[0]["changed"] is False
    # a parameter nobody provides yet: Cost & risk is not used, its fallback is the Team leader (free)
    await client.post(f"/api/studies/{study}/team/wanted",
                      json={"seat": "systems_engineer", "key": "cost.launch_keur", "note": "for the cost budget"},
                      headers=TL)
    led = (await client.get(f"/api/studies/{study}/team/ledger", headers=TL)).json()
    by = {r["key"]: r for r in led["rows"]}
    assert by["cost.launch_keur"]["status"] == "unowned"
    assert by["power.power_avg_w"]["status"] == "provided"
    assert by["power.power_avg_w"]["wanted_by"] == ["thermal_engineer"]


# ─── class board, interventions, export ──────────────────────────────────────

async def test_class_board_needs_attention_and_interventions(client, study_obj, study):
    from spacecdf_server.seats import store
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    assert (await client.get("/api/instructor/board", headers=PWR)).status_code == 403
    await client.post(f"/api/studies/{study}/team/hand", json={"raised": True}, headers=PWR)
    board = (await client.get("/api/instructor/board", headers=PROF)).json()
    row = next(r for r in board["rows"] if r["study_id"] == study)
    assert "raised_hand" in row["needs_attention"]
    assert next(s for s in row["seats"] if s["id"] == "power_engineer")["holders"][0]["hand"] is True
    store._presence[study]["iap:power@c2o.live"]["last"] = time.time() - 200
    row = next(r for r in (await client.get("/api/instructor/board", headers=PROF)).json()["rows"] if r["study_id"] == study)
    assert "idle_seat" in row["needs_attention"] and row["idle_seats"] == ["power_engineer"]
    assert row["gate"]["gate"]                       # the current gate is reported
    # interventions
    assert (await client.post(f"/api/instructor/studies/{study}/message", json={"text": "Five minutes"}, headers=PROF)).status_code == 200
    assert (await client.post("/api/instructor/broadcast", json={"text": "Break"}, headers=PROF)).status_code == 200
    assert (await client.post(f"/api/instructor/studies/{study}/timer", json={"minutes": 10, "label": "MDR"}, headers=PROF)).json()["timer"]["minutes"] == 10
    team = (await client.get(f"/api/studies/{study}/team", headers=PWR)).json()
    assert [m["text"] for m in team["messages"]][-2:] == ["Five minutes", "Break"]
    assert team["timer"]["label"] == "MDR"
    inj = (await client.post(f"/api/instructor/studies/{study}/inject",
                             json={"text": "The customer now needs a 3 h revisit"}, headers=PROF)).json()
    assert inj["requirement"]["level"] == "mission" and inj["requirement"]["code"] == "CUST-001"
    items = (await client.get(f"/api/instructor/studies/{study}/gate-items", headers=PROF)).json()
    if items["items"]:
        cid = items["items"][0]["id"]
        r = await client.post(f"/api/instructor/studies/{study}/signoff", json={"criterion_id": cid, "note": "seen"},
                              headers=PROF)
        item = next(i for i in r.json()["items"] if i["id"] == cid)
        assert item["status"] == "pass" and item["signoff"]["by"] == "Prof"


async def test_timeline_export_per_person_and_seat(client, study_obj, study):
    _, _, eps, _ = await power_tree(client, study)
    await seat_study(client, study)
    await claim(client, study, PWR, "power_engineer")
    await claim(client, study, TL, "team_leader")
    await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "mass_kg": 1.0}, headers=PWR)
    r = await client.post("/api/requirements/", json={"id": "MIS-1", "study_id": study, "level": "mission",
                                                      "text": "Detect fires"}, headers=TL)
    assert r.status_code == 200
    assert (await client.get("/api/instructor/timeline", headers=PWR)).status_code == 403
    csv_text = (await client.get(f"/api/instructor/timeline?study_id={study}&format=csv", headers=PROF)).text
    assert "iap:power@c2o.live" in csv_text and "power_engineer" in csv_text and ",edit," in csv_text
    md = (await client.get(f"/api/instructor/timeline?study_id={study}&format=md&lang=fr", headers=PROF)).text
    assert "Synthèse par personne × poste" in md
    assert "Alex — Puissance" in md and "Alex — Chef d’équipe" in md
    assert "POST /api/requirements/" in md          # every write records person and seat


def test_empty_instructor_list_is_closed_not_first_come(monkeypatch):
    """Hosted with SPACECDF_INSTRUCTORS set but empty: nobody may self-promote."""
    from spacecdf_server.seats.identity import instructor_mode
    monkeypatch.delenv("SMO_INSTRUCTORS", raising=False)
    monkeypatch.setenv("SPACECDF_INSTRUCTORS", "")
    assert instructor_mode() == "list"
    monkeypatch.delenv("SPACECDF_INSTRUCTORS")
    assert instructor_mode() == "laptop"
