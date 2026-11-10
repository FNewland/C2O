"""Wave 3, agent L: licensing on camera (3.L1), disposal sweeps (3.L3), change proposals (3.L4),
payload geometry (3.L5), the impact preview (3.L6), the readiness plan (3.L7) and the debris
assessment accepted at SRR (3.L8), on the Northern Fire and Ice v2 fixture.

Figures come from the fixture files (``NUMBERS``, ``risks``, ``budgets``); counts from the store.
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import load, seed_nfi

N = load("NUMBERS")
RISKS = load("risks")
DISP = N["disposal"]
EVID = N["v2_trade_evidence"]


# ───────────────────────────────────────────────────────────── physics (no seed)

def test_l3_decay_sweep_reproduces_the_v2_trade_evidence():
    from spacecdf_common.physics.debris import decay_sweep
    rows = {r["altitude_km"]: r for r in decay_sweep([550, 590], mass_kg=N["mass"]["limit_kg"], start_year=2030.5,
                                                    sail_area_m2=DISP["sail"]["area_m2"])}
    lt = EVID["lifetime_y_from_mid_2030"]
    # ECP-02 evidence: 550 km without the sail, strong cycle (tumbling area 0.12 m2)
    assert rows[550.0]["without_sail_y"]["0.12"]["strong"] == pytest.approx(lt["550"]["nosail_A0.12_strong_y"], rel=0.15)
    assert rows[590.0]["with_sail_y"]["nominal"] == pytest.approx(DISP["lifetime_with_sail_y_590km"]["nominal"], rel=0.15)
    assert rows[590.0]["with_sail_y"]["weak"] == pytest.approx(DISP["lifetime_with_sail_y_590km"]["weak"], rel=0.15)
    assert rows[590.0]["without_sail_y"]["0.08"]["nominal"] == pytest.approx(lt["590"]["nosail_A0.08_nominal_y"], rel=0.15)
    assert rows[550.0]["with_sail_y"]["nominal"] < rows[590.0]["with_sail_y"]["nominal"]


def test_l8_reentry_screening_counts_only_fragments_above_15_joules():
    from spacecdf_common.physics.debris import reentry_casualty
    eq = load("equipment")
    comps = [{"name": i["name"], "mass_kg": i.get("mass_kg"), "quantity": i.get("qty") or 1}
             for s in eq["spacecraft"]["subsystems"] for i in s["items"]]
    r = reentry_casualty(comps, N["orbit"]["inclination_deg"]["value"])
    assert r["compliant"] and 0 < r["casualty_expectation"] < 1e-4
    kits = [f for f in r["fragments"] if "fastener" in f["component"].lower()]
    assert kits and not any(f["counted"] for f in kits)            # 2 g screws carry < 15 J
    assert any(f["counted"] and "wheel" in f["material"] for f in r["fragments"])
    assert reentry_casualty([], 97.75)["casualty_expectation"] == 0


def test_l5_camera_geometry_and_products_from_the_optics():
    from spacecdf_common.physics.payload_sizing import camera_geometry, imaging_chain
    p, alt = N["payload"], N["orbit"]["altitude_km"]["value"]
    cams = []
    for key, focal in (("swir", 35.0), ("vnir", 50.0)):
        g = camera_geometry(altitude_km=alt, pixel_pitch_um=p[key]["pixel_um"], resolution_px=p[key]["format_px"],
                            focal_length_mm=focal)
        cams.append({**g, "name": key})
    sw, vn = cams
    assert sw["gsd_m"] == p["swir"]["gsd_m_590km"] and vn["gsd_m"] == p["vnir"]["gsd_m_native_590km"]
    assert sw["swath_km"] == p["swir"]["swath_km"] and vn["swath_km"] == p["vnir"]["swath_km"]
    assert sw["fov_deg"] == 14.56
    assert sw["frame_mb"] == p["swir"]["frame_mb"] and vn["frame_mb"] == p["vnir"]["frame_mb"]
    pr = N["data_budget"]["products"]
    ch = imaging_chain(cams, alt, roi_per_day=pr["planned_set_per_day"]["roi_pairs"],
                       quicklooks_per_day=pr["planned_set_per_day"]["quicklooks"])
    assert ch["trigger_interval_s"] == p["max_trigger_interval_s_contiguous"]
    assert [c["csi2_mbps"] for c in ch["cameras"]] == [4.5, 13.7]
    assert ch["roi_pair_mb"] == pr["roi_pair_mb_raw"]["value"]
    assert ch["quicklook_mb"] == pr["quicklook_mb_raw"]["value"]
    assert ch["planned_set_raw_mb"] == pr["planned_set_per_day"]["raw_mb"]


def test_l1_progress_and_formats_of_the_licensing_record():
    from spacecdf_server.services import licensing as lic
    empty = lic.progress(lic.EMPTY_RECORD)
    assert empty["filled"] == 0 and empty["total"] == sum(1 for f in lic.FIELDS if f["required"])
    assert empty["rsssa_14_30"]["total"] > 0 and empty["percent"] == 0
    bad = {"applicant": {"contact_email": "not-an-address", "contact_phone": "call me"}, "launch": {"date": "June"}}
    errs = lic.validate_record(bad)
    assert len(errs) == 3 and any("contact_email" in e for e in errs)
    assert {p["path"] for p in lic.progress(lic._merge(lic.EMPTY_RECORD, bad))["problems"]} == {
        "applicant.contact_email", "applicant.contact_phone", "launch.date"}


# ───────────────────────────────────────────────────────────── on the S4 study

def _ui_record() -> dict:
    """What the team types into the Licensing tab on camera, tab by tab (neutral placeholders;
    the baseline record plus the fields it leaves to the applicant)."""
    from tests.fixtures.nfi.seed import licensing_record
    r = licensing_record(N)
    r["cdpp"].update({"backup_facility": "Backup command workstation at the Iqaluit station (placeholder)",
                      "personnel_security": "Reliability screening of every operator with command access (placeholder)",
                      "physical_security": "Badge access to mission control; station huts locked and alarmed"})
    r["data_policy"].update({"disposal": "Data deleted after the 10-year retention unless archived openly",
                             "priority_access": "Government of Canada priority access as the licence requires"})
    r["launch"].update({"provider": "Rideshare launch provider (placeholder)", "vehicle": "Rideshare launcher",
                        "site": "To be assigned by the launch provider (placeholder)", "date": "2030-06"})
    r["affiliates"] = [{"name": "None (placeholder)", "relationship": "-", "country": "Canada"}]
    return r


async def test_l1_recording_seed_tab_filled_through_the_ui_routes(client):
    s = await seed_nfi(client, "S4", recording=True)
    sid = s.study_id
    url = f"/api/lifecycle/licensing/{sid}"
    g = (await client.get(url)).json()
    assert g["progress"]["filled"] == 0 and g["record"]["applicant"]["legal_name"] == ""
    # the panel saves the whole record of a tab (lists replaced whole), tab after tab
    full = _ui_record()
    tabs = [["applicant", "contacts", "participants", "affiliates", "itu_network_name", "notes"], ["cdpp"],
            ["data_policy", "launch"]]
    ver = g["version"]
    pcts = []
    for keys in tabs:
        body = {k: full[k] for k in keys if k in full}
        r = await client.put(url, json={**body, "version": ver})
        assert r.status_code == 200, r.text
        ver = r.json()["version"]
        pcts.append((await client.get(url)).json()["progress"]["percent"])
    assert pcts == sorted(pcts) and pcts[-1] == 100
    # a wrong e-mail is refused with the field named
    bad = await client.put(url, json={"applicant": {**full["applicant"], "contact_email": "x"}, "version": ver})
    assert bad.status_code == 422 and "contact_email" in bad.text
    # overrides of the space downlink antenna gain (0 dBi, then the -3 dBi case): EIRP and PFD
    # recomputed from the typed gain each time, a negative gain accepted (typed as text too)
    import math

    async def dl(gain):
        nonlocal ver
        r = await client.put(url, json={"assignment_overrides": {"SS-TX-DL": {"antenna_gain_dbi": gain}}, "version": ver})
        assert r.status_code == 200, r.text
        ver = r.json()["version"]
        return next(a for a in (await client.get(url)).json()["derived"]["assignments"] if a["id"] == "SS-TX-DL")
    a0 = await dl(0)
    a1 = await dl("-3")
    assert a0["antenna_gain_dbi"] == 0.0 and a1["antenna_gain_dbi"] == -3.0 and "antenna_gain_dbi" in a1["overridden"]
    for a, gain in ((a0, 0.0), (a1, -3.0)):
        assert a["eirp_dbw"] == pytest.approx(round(10 * math.log10(a["tx_power_w"]) + gain - a["line_loss_db"], 1))
    assert a1["eirp_dbw"] == pytest.approx(a0["eirp_dbw"] - 3.0, abs=0.11)
    assert a1["pfd_5deg_dbw_m2"] == pytest.approx(a0["pfd_5deg_dbw_m2"] - 3.0, abs=0.11)
    # the documents carry what was typed
    docs = {}
    for kind in ("rsssa", "ised-space", "debris"):
        r = await client.post(f"/api/exports/regulatory/{kind}/{sid}")
        assert r.status_code == 200
        docs[kind] = r.text
    assert full["applicant"]["legal_name"] in docs["rsssa"] and full["cdpp"]["backup_facility"] in docs["rsssa"]
    assert full["launch"]["provider"] in docs["rsssa"] and full["data_policy"]["disposal"] in docs["rsssa"]
    assert "APPLICANT INPUT REQUIRED" not in docs["rsssa"]
    assert full["itu_network_name"] in docs["ised-space"] and full["applicant"]["legal_name"] in docs["ised-space"]
    assert full["contacts"] and full["applicant"]["contact_name"] in docs["debris"]
    assert f"{a1['eirp_dbw']:g}" in docs["ised-space"]


async def test_l3_l4_l6_l7_l8_on_the_s4_study(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    assert s.report["forbidden"] == 0

    # ── 3.L4 change proposals: 3 records, ECP-01's affected codes resolved
    recs = RISKS["configuration_management"]["change_records"]
    ch = (await client.get(f"/api/studies/{sid}/changes")).json()
    assert ch["counts"]["total"] == len(recs) == 3
    by = {c["code"]: c for c in ch["items"]}
    e1 = by["ECP-01"]
    want = [a for a in next(r for r in recs if r["id"] == "ECP-01")["affected"] if not a.startswith("NUMBERS")]
    assert e1["affected_codes"] == want and e1["unresolved_codes"] == []
    assert len(e1["affected_requirement_ids"]) == len(want)
    assert e1["change_class"] == "I" and e1["status"] == "proposed" and e1["decision_gate"] == "pdr"
    assert e1["source_trade"] == "T-A01" and "NUMBERS payload.vnir" in e1["affected_other"]
    assert by["CR-V2"]["kind"] == "cr" and by["CR-V2"]["status"] == "implemented" and by["CR-V2"]["decision_gate"] == "pdr"   # seed CHANGE_GATES (approved with the allocated baseline)
    assert by["ECP-02"]["decision_gate"] == "srr" and "SEG-LS-02" in by["ECP-02"]["affected_codes"]
    # idempotent import, patch, the section (blocks PDR)
    again = (await client.post(f"/api/studies/{sid}/changes/import",
                               json={"records": recs})).json()
    assert again["created"] == 0 and again["updated"] == 3
    sx = (await client.get(f"/api/studies/{sid}/export-context")).json()
    assert sx["changes"]["status"] == "ok" and sx["changes"]["counts"]["blocks"]["pdr"] == ["ECP-01"]
    p = await client.patch(f"/api/studies/{sid}/changes/ECP-02", json={"decision_gate": "prr"})
    assert p.status_code == 200 and p.json()["decision_gate"] == "prr"
    assert (await client.patch(f"/api/studies/{sid}/changes/ECP-02", json={"decision_gate": "x"})).status_code == 422
    new = (await client.post(f"/api/studies/{sid}/changes", json={"title": "Second UHF antenna", "kind": "ecp"})).json()
    assert new["code"] == "ECP-04" or new["code"].startswith("ECP-")
    # raise change from a decided trade
    trades = (await client.get(f"/api/studies/{sid}/trades")).json()["items"]
    decided = [t for t in trades if (t["state"] or {}).get("status") == "decided"]
    open_ = [t for t in trades if (t["state"] or {}).get("status") != "decided"]
    if decided:
        r = (await client.post(f"/api/studies/{sid}/changes/from-trade/{decided[0]['id']}")).json()
        assert r["source_trade"] == decided[0]["id"] and r["status"] == "proposed"
        r2 = (await client.post(f"/api/studies/{sid}/changes/from-trade/{decided[0]['id']}")).json()
        assert r2.get("existing") and r2["id"] == r["id"]
    if open_:
        assert (await client.post(f"/api/studies/{sid}/changes/from-trade/{open_[0]['id']}")).status_code == 409

    # ── 3.L6 key numbers and the impact preview; ECP previews
    kn = (await client.get(f"/api/studies/{sid}/key-numbers")).json()["items"]
    gn = N["ground_network"]
    assert kn["contacts.union_min_per_day"]["value"] == pytest.approx(gn["union_min_per_day"]["value"], abs=0.5)
    assert kn["disposal.compliant"]["value"] is True
    assert kn["link.design_margin_db"]["value"] is not None and kn["energy.worst_dod_percent"]["value"] > 0
    e1p = (await client.post(f"/api/studies/{sid}/changes/ECP-01/preview")).json()
    lines = {ln["key"]: ln for ln in e1p["lines"]}
    assert lines["allocation.mass"]["after"] == 0.82 and lines["allocation.mass"]["before"] == 0.76
    assert lines["power.orbit_average_w"]["delta"] < 0                       # imaging power -1.1 W
    e2p = (await client.post(f"/api/studies/{sid}/changes/ECP-02/preview")).json()
    l2 = {ln["key"]: ln for ln in e2p["lines"]}
    assert l2["contacts.union_min_per_day"]["after"] == pytest.approx(EVID["contacts_union_min_per_day"]["four_sites_550"], abs=1.5)
    assert l2["disposal.lifetime_with_sail_worst_y"]["delta"] < 0
    # the ripple: a 3-station study, preview "add Inuvik"; nothing written
    els = (await client.get(f"/api/studies/{sid}/elements")).json()
    inu = next(e for e in els if e["name"].endswith("Inuvik"))
    assert (await client.delete(f"/api/elements/{inu['id']}")).status_code == 200
    site = next(x for x in gn["sites"] if x["name"] == "Inuvik")
    n_before = len((await client.get(f"/api/studies/{sid}/elements")).json())
    pv = await client.post(f"/api/studies/{sid}/impact/preview",
                           json={"kind": "station", "action": "add", "name": "GS Inuvik", "lat": site["lat"],
                                 "lon": site["lon"], "min_elevation_deg": gn["min_elevation_deg"]})
    assert pv.status_code == 200, pv.text
    pj = pv.json()
    L = {ln["key"]: ln for ln in pj["lines"]}
    fs = gn["fourth_site_trade"]
    assert L["contacts.union_min_per_day"]["before"] == pytest.approx(fs["three_sites"][0], abs=0.5)
    assert L["contacts.union_min_per_day"]["after"] == pytest.approx(fs["inuvik"][0], abs=0.5)
    assert L["contacts.union_min_per_day"]["delta"] == pytest.approx(fs["inuvik"][0] - fs["three_sites"][0], abs=0.5)
    cases = N["data_budget"]["cases"]
    # capacity: the baseline's own "Inuvik out" case against the baseline C1
    assert L["data.capacity_mb_per_day"]["delta"] == pytest.approx(
        cases["C1_per_pass_profiles_BASELINE"]["capacity"] - cases["C4_C1_inuvik_out"]["capacity"], abs=0.5)
    assert L["modes.downlink_share_proposed_pct"]["delta"] == pytest.approx(
        100 * (fs["inuvik"][0] - fs["three_sites"][0]) / 1440, abs=0.1)
    assert L["power.orbit_average_with_margin_w"]["delta"] == pytest.approx(0.24, abs=0.05)
    seats = {x["seat"] for x in pj["seats"]}
    assert {"comms_engineer", "power_engineer", "systems_engineer", "mission_analyst"} <= seats
    assert len((await client.get(f"/api/studies/{sid}/elements")).json()) == n_before        # dry run
    assert (await client.post(f"/api/studies/{sid}/impact/preview", json={"kind": "nope"})).status_code == 422

    # ── 3.L7 readiness plan on the elements
    els = (await client.get(f"/api/studies/{sid}/elements")).json()
    items = {(e.get("performance") or {}).get("readiness_item") for e in els} - {None}
    assert len(items) == len(RISKS["readiness"]["trl"]) == 8
    for e in els:
        pf = e.get("performance") or {}
        if pf.get("readiness_item", "").startswith(("SWIR camera", "VNIR camera", "SWIR filter", "Optical bench",
                                                   "Independent disposal")):
            assert e["trl"] == 4 and pf["trl_target_cdr"] == 6

    # ── 3.L3 sweep and 3.L8 debris assessment accepted at SRR
    sw = (await client.get(f"/api/studies/{sid}/debris-assessment/sweep?altitudes=550,590")).json()
    rows = {r["altitude_km"]: r for r in sw["rows"]}
    assert rows[590.0]["with_sail_y"]["weak"] == pytest.approx(DISP["lifetime_with_sail_y_590km"]["weak"], rel=0.15)
    assert rows[550.0]["without_sail_y"]["0.12"]["strong"] == pytest.approx(
        EVID["lifetime_y_from_mid_2030"]["550"]["nosail_A0.12_strong_y"], rel=0.15)
    g = (await client.get(f"/api/studies/{sid}/debris-assessment")).json()
    assert g["items"] == [] and g["evidence"]["status"] == "open" and g["current"]["compliant"] is True
    assert (await client.post(f"/api/studies/{sid}/debris-assessment/accept", json={"gate": "srr"})).status_code == 422
    run = (await client.post(f"/api/studies/{sid}/debris-assessment/run", json={})).json()
    assert run["version"] == 1 and run["status"] == "draft" and run["compliant"] is True
    assert run["lifetime"]["worst_with_device_y"] <= 5.0 < run["lifetime"]["worst_without_device_y"]
    assert run["casualty"]["casualty_expectation"] < 1e-4 and run["collision"]["operational_large"] < 1e-3
    assert {c["id"] for c in run["checks"]} >= {"ISED-DM-01", "ISED-DM-03", "ISED-DM-07"}
    acc = (await client.post(f"/api/studies/{sid}/debris-assessment/accept",
                              json={"gate": "SRR", "by": "propulsion_engineer"})).json()
    assert acc["status"] == "accepted" and acc["accepted_gate"] == "srr"
    ev = (await client.get(f"/api/studies/{sid}/debris-assessment")).json()["evidence"]
    assert ev["status"] == "pass" and ev["accepted"] and ev["stale"] is False
    sx = (await client.get(f"/api/studies/{sid}/export-context")).json()
    assert sx["debris"]["assessment"]["status"] == "accepted" and sx["debris"]["history"] == []
    deb = (await client.post(f"/api/exports/regulatory/debris/{sid}")).json()
    sec10 = next(x for x in deb["sections"] if x["number"] == "10")
    assert any("SRR" in r["value"] for r in sec10["rows"])
    # a new run supersedes the accepted one; the gate evidence goes back to open
    run2 = (await client.post(f"/api/studies/{sid}/debris-assessment/run", json={})).json()
    assert run2["version"] == 2
    ev2 = (await client.get(f"/api/studies/{sid}/debris-assessment")).json()
    assert ev2["evidence"]["status"] == "open" and [i["status"] for i in ev2["items"]] == ["draft", "superseded"]

    # ── 3.L5 payload geometry proposed from the optics (Properties chips)
    pg = (await client.get(f"/api/lifecycle/payload-geometry/{sid}")).json()
    assert pg["trigger_interval_s"] == N["payload"]["max_trigger_interval_s_contiguous"]
    gsd = sorted(c["gsd_m"] for c in pg["cameras"])
    assert gsd == sorted([N["payload"]["swir"]["gsd_m_590km"], N["payload"]["vnir"]["gsd_m_native_590km"]])
    assert {p["name"]: p["mb_raw"] for p in pg["products"]} == {
        "ROI pair": N["data_budget"]["products"]["roi_pair_mb_raw"]["value"],
        "Quicklook": N["data_budget"]["products"]["quicklook_mb_raw"]["value"]}
    assert pg["planned_set_raw_mb"] == N["data_budget"]["products"]["planned_set_per_day"]["raw_mb"]

    # ── round trip: change proposals and debris assessments survive export / import
    doc = (await client.get(f"/api/studies/{sid}/export")).json()
    imp = (await client.post("/api/studies/import", json=doc)).json()
    nid = imp["id"]
    ch2 = (await client.get(f"/api/studies/{nid}/changes")).json()
    assert sorted(c["code"] for c in ch2["items"]) == sorted(c["code"] for c in (await client.get(
        f"/api/studies/{sid}/changes")).json()["items"])
    e1b = next(c for c in ch2["items"] if c["code"] == "ECP-01")
    assert e1b["affected_codes"] == e1["affected_codes"] and e1b["previews"] == e1["previews"]
    d2 = (await client.get(f"/api/studies/{nid}/debris-assessment?current=false")).json()
    assert [i["version"] for i in d2["items"]] == [2, 1] and d2["items"][1]["accepted_gate"] == "srr"
