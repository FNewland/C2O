"""Wave 3, agent H acceptance on the Northern Fire and Ice v2 fixture: the design loop's data and
link (3.H1), the contact-plan capacity (3.H2), the mode shares from the ConOps (3.H3), the orbit
season and thermal cases (3.H4), the sensitivity view (3.H5) and the negotiation records (3.H6).

Every expected figure is read from the fixture (NUMBERS.yaml, budgets.yaml, hk_sids.yaml) or from the
store; tolerances are those of the plan.
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import load, seed_nfi

N = load("NUMBERS")
B = load("budgets")
DB = N["data_budget"]
ORB = N["orbit"]


def _close(a, b, rel=0.01):
    return a == pytest.approx(b, rel=rel)


# ───────────────────────────────────────────────────────────── 3.H2, 3.H3, 3.H4 on one S4 study

async def test_h2_h3_h4_capacity_shares_season(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    # 3.H2: the Modes data chain applies the acquisition and the availability, with both labelled figures
    dc = (await client.get(f"/api/studies/{sid}/modes/data-chain")).json()
    dl = dc["downlink"]
    assert _close(dl["total_capacity_mb_per_day"], B["data"]["capacity_mb_per_day"])
    assert _close(dl["allocatable_mb_per_day"], B["data"]["allocatable_90pct_mb_per_day"])
    assert dl["allocatable_percent"] == 90
    assert dl["acquisition_s"] == DB["pass_overheads"]["acquisition_s_per_window"]
    assert dl["availability"] == DB["pass_overheads"]["availability"]
    assert dl["remaining_after_realtime_hk_mb_per_day"] == pytest.approx(
        dl["total_capacity_mb_per_day"] - dl["realtime_hk_mb_per_day"], abs=0.02)
    # per station: usable minutes after acquisition and availability, never above the raw pass time
    for st in dl["stations"]:
        assert 0 < st["usable_min_per_day"] < st["contact_min_per_day"]
    # what goes down the link is the product set + stored HK, so the chain closes (no 21 GB/day of frames)
    assert dc["generation_basis"] == "products" and dc["acquired_gb_per_day"] > dc["generated_gb_per_day"]
    checks = {c["id"]: c["status"] for c in dc["checks"]}
    assert checks["DC-DOWNLINK"] == "pass" and checks["DC-STORAGE"] == "pass"
    assert dc["backlog_growth_gb_per_day"] < 0

    # 3.H3: the shares proposed from the ConOps, with provenance
    sh = (await client.get(f"/api/studies/{sid}/modes/share-proposals")).json()
    props = {p["kind"]: p for p in sh["proposals"]}
    union = sh["union_min_per_day"]
    ev = N["v2_trade_evidence"]["contacts_union_min_per_day"]
    assert union == pytest.approx(ev["four_sites_590"], abs=1.0)
    assert props["downlink"]["proposed_fraction"] == pytest.approx(union / 1440.0, abs=1e-4)
    assert props["downlink"]["proposed_fraction"] == pytest.approx(0.087, abs=0.001)
    assert "1440" in props["downlink"]["provenance"]["en"] and "1440" in props["downlink"]["provenance"]["fr"]
    assert props["imaging"]["proposed_fraction"] == pytest.approx(N["power"]["mode_mix_pct"]["imaging"] / 100, abs=0.005)
    assert props["downlink"]["status"] == "proposed"
    # an override needs a reason
    bad = await client.post(f"/api/studies/{sid}/modes/share-proposals/accept",
                            json={"mode_id": props["imaging"]["mode_id"], "fraction": 0.07})
    assert bad.status_code == 422
    acc = (await client.post(f"/api/studies/{sid}/modes/share-proposals/accept", json={"by": "test"})).json()
    after = {p["kind"]: p for p in acc["proposals"]}
    assert after["downlink"]["status"] == "accepted" and after["nominal"]["current_fraction"] == pytest.approx(
        1 - after["downlink"]["current_fraction"] - after["imaging"]["current_fraction"] - 0.01, abs=1e-3)
    en = (await client.get(f"/api/studies/{sid}/modes/energy")).json()
    assert en["operational_orbit"]["share_total"] == pytest.approx(1.0, abs=1e-3)
    assert en["operational_orbit"]["orbit_average_cbe_w"] == pytest.approx(B["power"]["totals"]["orbit_average_w"], abs=0.02)

    # 3.H4: β and eclipse over the launch year, the thermal cases, the freeze-up flag
    season = (await client.get(f"/api/thermal/studies/{sid}/orbit-season")).json()
    assert season["inputs"]["year"] == 2030
    assert season["beta"]["min_deg"] == pytest.approx(ORB["beta_deg_2030"]["min"], abs=0.5)
    assert season["beta"]["max_deg"] == pytest.approx(ORB["beta_deg_2030"]["max"], abs=0.5)
    assert season["eclipse"]["min_min"] == pytest.approx(ORB["eclipse_min"]["min"], abs=0.3)
    assert season["eclipse"]["max_min"] == pytest.approx(ORB["eclipse_min"]["max"], abs=0.3)
    assert season["eclipse"]["eclipse_free_days"] == ORB["eclipse_min"]["eclipse_free_days"]
    assert season["sun_elevation"]["freeze_up_not_observable"] is True
    assert all(f["north_of_deg"] >= 60 for f in season["sun_elevation"]["freeze_up_flags"])
    assert any(f["month"] == 11 and f["day_of_month"] > 15 for f in season["sun_elevation"]["freeze_up_flags"])
    cases = (await client.get(f"/api/thermal/studies/{sid}/cases")).json()
    assert cases["source"] == "orbit_season"
    want = B["thermal"]["cases"]
    assert f"beta {cases['cold']['beta_deg']} deg" in want["cold"] and f"node {cases['cold']['node']}" in want["cold"]
    assert f"beta {cases['hot']['beta_deg']} deg" in want["hot"] and f"node {cases['hot']['node']}" in want["hot"]
    assert cases["cold"]["eclipse_min"] > cases["hot"]["eclipse_min"]
    assert en["season"]["eclipse"]["max_min"] == pytest.approx(season["eclipse"]["max_min"], abs=0.1)
    assert en["season"]["worst_eclipse_orbit"]["dod_percent"] is not None

    # 3.H3 ripple: without the northern site the downlink share is re-proposed and the accepted one is stale
    gs = (await client.get(f"/api/studies/{sid}/ground-stations")).json()["selected"]
    worst = next(g for g in gs if g["name"].endswith("Inuvik"))
    assert (await client.delete(f"/api/elements/{worst['element_id']}")).status_code == 200
    sh2 = {p["kind"]: p for p in (await client.get(f"/api/studies/{sid}/modes/share-proposals")).json()["proposals"]}
    assert sh2["downlink"]["proposed_fraction"] == pytest.approx(0.065, abs=0.001)
    assert sh2["downlink"]["inputs"]["union_min_per_day"] == pytest.approx(ev["three_no_inuvik_590"], abs=0.5)
    assert sh2["downlink"]["status"] == "stale"


# ───────────────────────────────────────────────────────────── 3.H1 and 3.H5

async def test_h1_design_loop_reads_the_data_budget_and_h5_sensitivity(client):
    from spacecdf_agents.tier1.data import DataAgent
    from spacecdf_agents.tier1.link import LinkAgent
    from spacecdf_agents.tier2.conflicts import ConflictDetectionAgent
    from spacecdf_common.agents.base import DesignState
    from spacecdf_common.models.parameter import ParameterSource, ParameterValue
    from spacecdf_server.routers.studies import get_study_store
    from spacecdf_server.services import data_budget as dbs

    s = await seed_nfi(client, "S4")
    sid = s.study_id
    ov = await dbs.design_overlay_for_study(sid)
    prod = DB["products"]["planned_set_per_day"]
    assert ov["data.science_raw_mb_per_day"] == pytest.approx(prod["raw_mb"], abs=0.05)
    assert ov["data.science_delivered_mb_per_day"] == DB["science_target_mb_per_day_after_compression"]["value"]
    assert _close(ov["data.capacity_mb_per_day"], DB["capacity_mb_per_day"]["value"])
    # the design state the loop starts from (A's seed_design_state + this overlay), with the payloads'
    # acquired volumes still in it: the "Phase 0 estimate" the old loop compared with the downlink
    study = get_study_store()[sid]

    def pv(k: str, v: float) -> ParameterValue:
        return ParameterValue(id=k, name=k, value=v, unit="", domain=k.split(".")[0], source=ParameterSource.COMPUTED,
                              confidence=0.7, margin_percent=0.0, updated_by="test")
    pays = load("mission")["mission_patch"]["requirements"]["payloads"] if "requirements" in load("mission")["mission_patch"] \
        else load("mission")["mission_patch"].get("payloads") or []
    params = {k: pv(k, v) for k, v in ov.items()}
    for i, p in enumerate(pays):
        params[f"payload.{i}.data_volume_per_day_gb"] = pv(f"payload.{i}.data_volume_per_day_gb", p["data_volume_per_day_gb"])
    phase0 = sum(p["data_volume_per_day_gb"] for p in pays)
    state = DesignState(parameters=params, requirements=study.requirements.model_dump())
    link = await LinkAgent().execute(state)
    out = {k: p.value for k, p in link.parameters.items()}
    assert out["link.payload_margin_db"] == pytest.approx(study.requirements.link.margin_db, abs=0.05)
    assert out["link.payload_margin_db"] == pytest.approx(4.0, abs=0.1)          # the design case: rural site, 1 W
    assert out["link.data_per_day_gb"] * 1000 == pytest.approx(ov["data.capacity_mb_per_day"], abs=0.01)
    assert "link.phase0_payload_margin_db" in out and "design link case" in link.rationale
    state.parameters.update({k: pv(k, v) for k, v in out.items()})
    data = await DataAgent().execute(state)
    dout = {k: p.value for k, p in data.parameters.items()}
    assert dout["data.generated_per_day_gb"] * 1000 == pytest.approx(
        ov["data.science_on_channel_mb_per_day"] + ov["data.hk_stored_mb_per_day"] + ov["data.hk_realtime_mb_per_day"], abs=0.01)
    assert dout["data.phase0_generated_per_day_gb"] == pytest.approx(phase0, abs=0.01)   # the per-payload sum, labelled
    assert dout["data.phase0_delta_gb"] > 1.0 and not data.warnings
    state.parameters.update({k: pv(k, v) for k, v in dout.items()})
    conf = await ConflictDetectionAgent().execute(state)
    text = " ".join(conf.warnings + conf.recommendations)
    assert "CONF-DATA-001" not in text and "Data Rate vs Downlink" not in text and "Ka-band" not in text
    # a deficit on a UHF study: band-aware advice, never Ka-band
    from spacecdf_agents.tier2.conflicts import capacity_resolutions
    assert not [r for r in capacity_resolutions("UHF") if "Ka" in r.description]
    assert any("Ka" in r.description for r in capacity_resolutions("X"))
    state.parameters["data.demand_mb_per_day"] = pv("data.demand_mb_per_day", 40.0)
    conf = await ConflictDetectionAgent().execute(state)
    recs = " ".join(conf.recommendations)
    assert "CONF-DATA-001" in recs and "Ka" not in recs and "ground station" in recs

    # 3.H5: margin against the science target and the rate tier (10 % margin)
    st = (await client.get(f"/api/studies/{sid}/sensitivity?parameter=science_target")).json()
    big = DB["largest_science_with_10pct_margin_mb"]
    assert st["largest_with_margin_mb_per_day"] == pytest.approx(big["at_38k4"], abs=0.1)
    assert st["owner"] == "H" and st["items"] == st["points"]
    assert [p for p in st["points"] if p["x"] == 13.0][0]["margin_pct"] == pytest.approx(
        B["data"]["cases"]["C1_per_pass_profiles_BASELINE"]["margin_pct"], abs=0.3)
    rt = (await client.get(f"/api/studies/{sid}/sensitivity?parameter=rate_tier")).json()
    by_rate = {p["x"]: p for p in rt["points"]}
    assert by_rate[19200.0]["largest_with_margin_mb_per_day"] == pytest.approx(big["at_19k2"], abs=0.1)
    assert by_rate[19200.0]["margin_pct"] == pytest.approx(
        B["data"]["cases"]["C5_C1_at_19k2_fallback"]["margin_pct"], abs=1.0)
    cr = (await client.get(f"/api/studies/{sid}/sensitivity?parameter=compression_ratio")).json()
    assert cr["needed_for_target"] == pytest.approx(DB["products"]["compression_needed_to_fit_13mb"]["value"], abs=0.01)
    im = (await client.get(f"/api/studies/{sid}/sensitivity?parameter=imaging_share&values=0.05,0.08")).json()
    p5, p8 = sorted(im["points"], key=lambda p: p["x"])
    assert p5["orbit_average_cbe_w"] == pytest.approx(B["power"]["totals"]["orbit_average_w"], abs=0.02)
    assert p8["orbit_average_cbe_w"] > p5["orbit_average_cbe_w"] and p8["margin_pct"] < p5["margin_pct"]
    assert (await client.get(f"/api/studies/{sid}/sensitivity?parameter=nope")).status_code == 422
    alt = (await client.get(f"/api/studies/{sid}/sensitivity/altitude")).json()
    p590 = next(p for p in alt["points"] if p["altitude_km"] == 590)
    assert p590["with_device_nominal_y"] == pytest.approx(3.0, abs=0.15)
    assert p590["with_device_weak_y"] == pytest.approx(3.4, abs=0.15)
    assert alt["lines"]["max_start_altitude_5y_weak_km"] == pytest.approx(649, abs=5)
    assert alt["lines"]["max_start_altitude_5y_nominal_km"] == pytest.approx(688, abs=5)
    assert alt["lines"]["apogee_without_propulsion_km"] == 600
    assert p590["gsd_m"] == pytest.approx(58.2, abs=0.5) and p590["union_min_per_day"] == pytest.approx(125.7, abs=1)
    assert p590["link_margin_db"] == pytest.approx(study.requirements.link.margin_db, abs=0.01)
    hs = [p["altitude_km"] for p in alt["points"]]
    assert hs == sorted(hs) and all(not p["apogee_ok"] for p in alt["points"] if p["altitude_km"] > 600)
    p550 = next(p for p in alt["points"] if p["altitude_km"] == 550)
    assert p550["without_device_strong_y"] < 5 < p590["without_device_weak_y"]


# ───────────────────────────────────────────────────────────── 3.H6

async def test_h6_negotiation_records_sign_off_reopen_and_round_trip(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    lst = (await client.get(f"/api/studies/{sid}/negotiations")).json()
    assert lst["counts"] == {"total": 4, "proposed": 0, "agreed": 4, "reopened": 0}
    assert {t["code"] for t in lst["templates"]} == {"N1", "N3", "N7", "GS4"}
    by = {r["code"]: r for r in lst["items"]}
    for r in by.values():
        assert r["signed_count"] == r["seat_count"] >= 2 and r["agreed_snapshot"]
    # N1's options are computed by the data-budget scenario: 13 MB/day keeps +38.5 %, 19.9 MB/day +10 %
    n1 = by["N1"]
    opts = {o["key"]: o for o in n1["options"]}
    assert opts["keep"]["effects"]["margin_c1_pct"] == pytest.approx(B["data"]["cases"]["C1_per_pass_profiles_BASELINE"]["margin_pct"], abs=0.3)
    assert opts["raise"]["values"]["data.science_delivered_mb_per_day"] == pytest.approx(
        DB["largest_science_with_10pct_margin_mb"]["at_38k4"], abs=0.1)
    assert opts["raise"]["effects"]["margin_c1_pct"] == pytest.approx(10.0, abs=0.5)
    assert opts["keep"]["effects"]["margin_worst_site_out_pct"] == pytest.approx(
        B["data"]["cases"]["C4_C1_inuvik_out"]["margin_pct"], abs=0.5)
    assert set(n1["seats"]) == {"payload_lead", "comms_engineer", "mission_analyst", "customer"}
    assert n1["trigger"] == {"fired": False, "condition": {"key": "data.compression_ratio", "op": "<", "value": 1.3},
                             "value": pytest.approx(1.5)}
    assert "D-PI-01" in n1["links"]["decisions"]
    # GS4: the ripple names who the site affects and the deltas, computed
    gs4 = {o["key"]: o for o in by["GS4"]["options"]}
    assert gs4["without"]["effects"]["union_min_per_day"] == pytest.approx(
        N["v2_trade_evidence"]["contacts_union_min_per_day"]["three_no_inuvik_590"], abs=0.5)
    assert gs4["with"]["delta"]["capacity_mb_per_day"] > 5 and gs4["with"]["delta"]["orbit_average_cbe_w"] > 0
    assert {a["seat"] for a in gs4["with"]["affects"]} <= set(by["GS4"]["seats"])
    # N7 closes with the 20 % hold
    n7 = {o["key"]: o for o in by["N7"]["options"]}
    assert n7["hold"]["effects"]["closes"] is True and n7["hold"]["values"]["mass.system_margin_percent"] == 20

    # a new N1 stays proposed until Payload, Comms, MA and the Customer have signed
    new = (await client.post(f"/api/studies/{sid}/negotiations", json={"template": "N1"})).json()
    rid = new["id"]
    assert new["status"] == "proposed" and new["signed_count"] == 0
    early = await client.post(f"/api/studies/{sid}/negotiations/{rid}/signoff", json={"seat": "payload_lead"})
    assert early.status_code == 409                       # nothing chosen yet
    await client.patch(f"/api/studies/{sid}/negotiations/{rid}", json={"chosen_option": "keep"})
    outsider = await client.post(f"/api/studies/{sid}/negotiations/{rid}/signoff", json={"seat": "power_engineer"})
    assert outsider.status_code == 403
    for i, seat in enumerate(["payload_lead", "comms_engineer", "mission_analyst"]):
        r = (await client.post(f"/api/studies/{sid}/negotiations/{rid}/signoff", json={"seat": seat, "by": "t"})).json()
        assert r["status"] == "proposed" and r["signed_count"] == i + 1
    r = (await client.post(f"/api/studies/{sid}/negotiations/{rid}/signoff", json={"seat": "customer", "by": "t"})).json()
    assert r["status"] == "agreed" and r["agreed"] == {"data.science_delivered_mb_per_day": 13.0}
    # a substantive change voids the sign-offs; reopening needs a reason and clears them too
    r = (await client.patch(f"/api/studies/{sid}/negotiations/{rid}", json={"chosen_option": "raise"})).json()
    assert r["status"] == "proposed" and r["signed_count"] == 0 and r["version"] == 3
    assert (await client.post(f"/api/studies/{sid}/negotiations/{rid}/reopen", json={})).status_code == 422
    r = (await client.post(f"/api/studies/{sid}/negotiations/{rid}/reopen", json={"reason": "measured 1.2:1"})).json()
    assert r["status"] == "reopened" and [h["action"] for h in r["history"]][-1] == "reopened"
    # the trigger fires on the live value
    await client.patch(f"/api/studies/{sid}/negotiations/{rid}", json={"reopen_condition": {"key": "data.compression_ratio",
                                                                                            "op": "<", "value": 1.6}})
    assert (await client.get(f"/api/studies/{sid}/negotiations/{rid}")).json()["trigger"]["fired"] is True
    bad = await client.post(f"/api/studies/{sid}/negotiations", json={"template": "N9"})
    assert bad.status_code == 422

    # the export section and the project round trip
    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=negotiations")).json()["negotiations"]
    assert sx["counts"]["total"] == 5 and sx["counts"]["agreed"] == 4 and sx["items"][0]["issue_text"]
    doc = (await client.get(f"/api/studies/{sid}/export")).json()
    imp = (await client.post("/api/studies/import", json=doc)).json()
    nid = imp.get("study_id") or imp.get("id") or (imp.get("study") or {}).get("id")
    back = (await client.get(f"/api/studies/{nid}/negotiations")).json()
    assert back["counts"] == (await client.get(f"/api/studies/{sid}/negotiations")).json()["counts"]
    key = lambda r: (r["code"], r["status"], r["chosen_option"], tuple(sorted(r["signoffs"])), r["version"])  # noqa: E731
    assert sorted(map(key, back["items"])) == sorted(map(key, (await client.get(f"/api/studies/{sid}/negotiations")).json()["items"]))


async def test_h6_recording_seed_leaves_the_negotiations_to_the_team(client):
    s = await seed_nfi(client, "S3", recording=True)
    lst = (await client.get(f"/api/studies/{s.study_id}/negotiations")).json()
    assert lst["items"] == [] and lst["counts"]["total"] == 0 and len(lst["templates"]) == 4
