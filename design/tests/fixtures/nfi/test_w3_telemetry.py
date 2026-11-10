"""W1.03, W3.01-W3.04, W4.05 acceptance on the Northern Fire and Ice fixture (agent H).

Every expected number is read from NUMBERS.yaml (or hk_sids.yaml for the stores), never retyped.
"""
from __future__ import annotations

import io

import pytest

from tests.fixtures.nfi import load, seed_nfi

N = load("NUMBERS")
HK = load("hk_sids")
TEL = N["telemetry"]
DB = N["data_budget"]


def _by_key(seed, rows: list[dict], field: str = "id") -> dict[str, dict]:
    ids = {m["id"]: k for k, m in seed.modes.items()}
    return {ids[r[field]]: r for r in rows if r[field] in ids}


# ───────────────────────────────────────────────────────────── W1.03 mode rules

async def test_w103_mode_rules_power_the_right_units(client):
    from spacecdf_server.services import mode_model as mm
    s = await seed_nfi(client, "S2")
    from spacecdf_server.routers.elements import _elements
    els = [e for e in _elements.values() if e.get("study_id") == s.study_id and not e.get("deleted_at")]
    by_name = {e["name"]: e for e in els}
    adcs = by_name["CubeADCS Gen 2 (Core + 3x CW0017 + CR torquers + CubeStar)"]
    sun = by_name["CubeSense Sun (fine sun sensor)"]
    sail = by_name["NPC Spacemind ARTICA drag sail (config A, 2.1 m2, 0.35U)"]
    timer = by_name["Independent deorbit timer and battery (2 release circuits)"]
    # integrated ADCS nominal in LEOP (B-dot), separate sun sensor powered in LEOP
    assert mm.propose_member(adcs, "leop")["power_state"] == "nominal" and mm.propose_member(adcs, "leop")["power_w_in_mode"] > 0
    assert mm.propose_member(sun, "leop")["power_state"] == "nominal" and mm.propose_member(sun, "leop")["power_w_in_mode"] > 0
    # the sail: 0 W everywhere except the disposal mode, where it draws the KB release power (6 W)
    for kind in ("leop", "commissioning", "nominal", "imaging", "downlink", "safe", "survival"):
        assert mm.propose_member(sail, kind)["power_w_in_mode"] == 0, kind
    assert mm.unit_class(sail) == "deorbit_device"
    assert mm.propose_member(sail, "disposal")["power_w_in_mode"] == pytest.approx(6.0)
    # the independent timer runs in every mode at about 0.05 W
    assert mm.unit_class(timer) == "deorbit_timer"
    for kind in ("leop", "nominal", "safe", "survival", "disposal"):
        assert mm.propose_member(timer, kind)["power_w_in_mode"] == pytest.approx(0.05)
    ov = (await client.get(f"/api/studies/{s.study_id}/modes")).json()
    kinds = [m["kind"] for m in ov["modes"]]
    assert kinds.count("disposal") == 1 and len(ov["modes"]) == len(load("modes")["modes"])
    want = {(t["from"], t["to"], t["trigger"]) for t in mm.cfg()["template"]["transitions"]} | \
        {(t["from"], t["to"], t["trigger"]) for t in load("modes")["transitions_added"]}
    assert len(ov["transitions"]) == len(want) == 19         # duplicates of template transitions kept once
    assert not [f for f in ov["findings"] if f["id"] == "MM-NO-EXIT" and f.get("mode_id") == s.modes["eol"]["id"]]
    # the drag sail is a propulsion (disposal) item: KB category -> propulsion domain (PI decision)
    from spacecdf_server.services.equipment import DOMAIN_TO_CATEGORIES
    assert "deorbit_devices" in DOMAIN_TO_CATEGORIES["propulsion"] and "deorbit_devices" not in DOMAIN_TO_CATEGORIES["structure"]
    # Night SWIR (custom, nominal phase, 1 %) enters the operational mix: orbit average 4.17 W
    en = (await client.get(f"/api/studies/{s.study_id}/modes/energy")).json()
    assert len(en["operational_orbit"]["modes"]) == 4
    ru = (await client.get(f"/api/studies/{s.study_id}/rollup?gate=mdr")).json()
    assert ru["power"]["orbit_average_w"] == pytest.approx(N["power"]["orbit_average_w"]["value"], abs=0.03)


# ───────────────────────────────────────────────────────────── W3 data budget

@pytest.fixture
async def s4(client):
    return await seed_nfi(client, "S4")


async def test_w3_sid_table_rates_and_closure(client, s4):
    s = s4
    b = (await client.get(f"/api/studies/{s.study_id}/data-budget")).json()
    assert b["status"] == "designed" and b["packet"]["overhead_bytes"] == TEL["packet_overhead_bytes"]["value"]
    sids = {x["sid"]: x for x in b["sids"]}
    for sid, row in TEL["sid_table"].items():
        assert sids[int(sid)]["bytes"] == row[1], (sid, sids[int(sid)]["bytes"])
    # real-time and stored HK per mode (periodic SIDs, routine set; the diagnostic SID is not billed)
    modes = _by_key(s, b["modes"])
    key = {"leop": "leop", "commissioning": "commissioning", "nominal": "nominal", "imaging": "imaging",
           "downlink": "downlink", "night_swir": "night_swir", "safe": "safe", "survival": "survival", "eol": "eol"}
    for k, v in TEL["realtime_by_mode_bps"].items():
        assert modes[key[k]]["rt_bps"] == pytest.approx(v, abs=1.0), k
    for k, v in TEL["stored_by_mode_bps"].items():
        assert modes[key[k]]["store_bps"] == pytest.approx(v, abs=0.2), k
    assert modes["nominal"]["rt_diag_bps"] == pytest.approx(1200, abs=1)
    rt = b["realtime"]
    assert rt["full_designed_bps"] == pytest.approx(TEL["realtime_full_designed_bps"]["value"], abs=1.5)
    assert rt["full_allocation_bps"] == TEL["realtime_allocation_bps"]["value"]
    assert rt["lean_bps"] == pytest.approx(TEL["realtime_lean_bps"]["value"], abs=1.5)
    assert rt["with_diag_bps"] == pytest.approx(TEL["realtime_with_adcs_diag_bps"]["value"], abs=1.5)
    assert b["stored"]["mix_bps"] == pytest.approx(TEL["stored_nominal_mix_bps"]["value"], abs=0.3)
    assert b["stored"]["mb_per_day"] == pytest.approx(TEL["stored_mb_per_day"]["value"], abs=0.02)
    assert b["stored"]["diag_mb_per_orbit"] == pytest.approx(TEL["adcs_diag_stored_mb_per_orbit"]["value"], abs=0.005)
    # framing and capacity from the union of the passes (not the sum)
    assert b["framing"]["frame_efficiency"] == pytest.approx(DB["framing"]["frame_efficiency"], abs=1e-3)
    assert b["capacity"]["union_min_per_day"] == pytest.approx(N["ground_network"]["union_min_per_day"]["value"], abs=1.0)
    assert b["contacts"]["union"]["sum_of_stations_min_per_day"] == pytest.approx(N["ground_network"]["sum_of_sites_min_per_day"]["value"], abs=2.0)
    assert b["capacity"]["usable_min_per_day"] == pytest.approx(DB["usable_min_per_day"]["value"], abs=1.0)
    assert b["capacity"]["capacity_mb_per_day"] == pytest.approx(DB["capacity_mb_per_day"]["value"], abs=0.3)
    # science: 13 MB/day delivered after compression, 1.28:1 needed for the planned product set
    sc = b["science"]
    assert sc["on_channel_mb_per_day"] == pytest.approx(DB["science_on_channel_mb_per_day"]["value"], abs=0.02)
    assert sc["compression_needed"] == pytest.approx(DB["products"]["compression_needed_to_fit_13mb"]["value"], abs=0.01)
    # the closure cases of NUMBERS.yaml (margin within 1 percentage point)
    cases = {c["id"]: c for c in b["cases"]}
    nc = DB["cases"]
    assert cases["C0"]["rt_hk_mb"] == pytest.approx(nc["C0_full_rt_hk_every_pass"]["rt_hk"], abs=0.05)
    assert cases["C0"]["margin_pct"] == pytest.approx(nc["C0_full_rt_hk_every_pass"]["margin_pct"], abs=1.0)
    assert cases["C1"]["rt_hk_mb"] == pytest.approx(nc["C1_per_pass_profiles_BASELINE"]["rt_hk"], abs=0.15)
    assert cases["C1"]["margin_pct"] == pytest.approx(nc["C1_per_pass_profiles_BASELINE"]["margin_pct"], abs=1.0)
    assert cases["C2"]["other_mb"] == pytest.approx(nc["C2_C1_plus_adcs_diag_campaign"]["other"], abs=0.06)
    assert cases["C2"]["margin_pct"] == pytest.approx(nc["C2_C1_plus_adcs_diag_campaign"]["margin_pct"], abs=1.0)
    assert cases["C3"]["rt_hk_mb"] == pytest.approx(nc["C3_commissioning_day"]["rt_hk"], abs=0.05)
    assert cases["C3"]["other_mb"] == pytest.approx(nc["C3_commissioning_day"]["other"], abs=0.05)
    c4 = next(c for k, c in cases.items() if k.startswith("C4-"))
    assert c4["capacity_mb"] == pytest.approx(nc["C4_C1_inuvik_out"]["capacity"], abs=0.4)
    assert c4["margin_pct"] == pytest.approx(nc["C4_C1_inuvik_out"]["margin_pct"], abs=1.5)
    assert cases["C6"]["science_mb"] == pytest.approx(nc["C6_C1_planned_set_uncompressed"]["science"], abs=0.05)
    assert b["closure"]["id"] == "C1" and b["closure"]["status"] == "pass"
    # pass classes: two operations passes a day on the control station
    ops = next(p for p in b["pass_classes"] if p["name"] == "OPS")
    assert ops["per_day"] == pytest.approx(2.0, abs=0.1)
    # stores: days held (hk_sids.yaml stores / NUMBERS hk_store_days)
    st = {x["name"]: x for x in b["stores"]}
    hd = TEL["hk_store_days"]
    assert st["HK_STORE"]["days_held"]["nominal_mix"] == pytest.approx(hd["nominal"], abs=1)
    assert st["HK_STORE"]["days_held"]["commissioning"] == pytest.approx(hd["commissioning"], abs=1)
    assert st["HK_STORE"]["days_held"]["safe"] == pytest.approx(hd["safe"], abs=1)
    assert st["HK_STORE"]["check"]["ok"] is True
    assert st["ADCS_DIAG_STORE"]["orbits_held"] == pytest.approx(HK["stores"][2]["orbits_held"], abs=0.5)
    assert st["EVENT_STORE"]["days_held"]["nominal_mix"] == pytest.approx(HK["stores"][1]["days_held"], abs=2)
    # day in the life and backlog
    dil = b["day_in_the_life"]
    assert len(dil["windows"]) == pytest.approx(DB["day_in_the_life"]["windows"], abs=2)
    assert sum(1 for w in dil["windows"] if w["class"] == "OPS") == 2
    assert dil["totals"]["payload_mb"] > 15
    assert len(b["backlog"]["days"]) == 7 and not b["backlog"]["growing"]


async def test_w301_data_chain_and_tmtc_budget_use_the_sids(client, s4):
    s = s4
    dc = (await client.get(f"/api/studies/{s.study_id}/modes/data-chain")).json()
    assert dc["housekeeping"]["designed"] and dc["downlink"]["contact_basis"] == "union"
    assert dc["downlink"]["contact_min_per_day"] == pytest.approx(N["ground_network"]["union_min_per_day"]["value"], abs=1.0)
    assert dc["downlink"]["sum_of_stations_min_per_day"] > dc["downlink"]["contact_min_per_day"] + 40
    assert not any(c["id"] == "DC-HK-NOT-DESIGNED" for c in dc["checks"])
    rows = _by_key(s, dc["per_mode"], "mode_id")
    assert rows["nominal"]["hk_stored_bps"] == pytest.approx(TEL["stored_by_mode_bps"]["nominal"], abs=0.2)
    assert dc["housekeeping"]["stored_mb_per_day"] == pytest.approx(TEL["stored_mb_per_day"]["value"], abs=0.02)
    v = (await client.get(f"/api/studies/{s.study_id}/cdr")).json()
    bud = v["budget"]
    assert bud["packet_overhead_bytes"] == 23
    assert 20 in bud["excluded_sids"] and not any(20 in r["sids"] for r in bud["regimes"])
    dl = next(r for r in bud["regimes"] if r["regime"] == "downlink")
    assert dl["hk_bps"] == pytest.approx(TEL["realtime_by_mode_bps"]["downlink"], abs=1.0)
    assert not [f for f in v["checks"] if f["rule"] in ("TMTC-HK-DAY", "TMTC-STORE", "TMTC-DIAG")]
    # a scenario: the planned products sent uncompressed
    sc = (await client.post(f"/api/studies/{s.study_id}/data-budget/scenario",
                            json={"compression_ratio": 1.0, "basis": "products"})).json()
    assert sc["closure"]["id"] == "SCENARIO"
    assert sc["closure"]["science_mb"] == pytest.approx(DB["cases"]["C6_C1_planned_set_uncompressed"]["science"], abs=0.05)
    # the ground-segment analysis bills stored HK and runs on the J2 contacts
    run = (await client.post(f"/api/studies/{s.study_id}/analyses/ground_segment/run")).json()
    assert run["summary"]["housekeeping"]["stored_mb_per_day"] == pytest.approx(TEL["stored_mb_per_day"]["value"], abs=0.02)
    assert run["summary"]["union"]["min_per_day"] == pytest.approx(N["ground_network"]["union_min_per_day"]["value"], abs=1.0)


async def test_w405_contact_table_and_tmtc_export(client, s4):
    s = s4
    t = (await client.get(f"/api/studies/{s.study_id}/contacts")).json()
    want = {x["name"]: x for x in N["ground_network"]["sites"]}
    for st in t["stations"]:
        site = next(v for k, v in want.items() if k in st["name"])
        assert st["min_per_day"] == pytest.approx(site["min_per_day"], rel=0.05), st["name"]
        assert st["passes_per_day"] == pytest.approx(site["passes_per_day"], rel=0.05)
        assert st["max_pass_min"] == pytest.approx(site["max_pass_min"], abs=0.3)
    u = t["union"]
    gn = N["ground_network"]
    assert u["min_per_day"] == pytest.approx(gn["union_min_per_day"]["value"], rel=0.05)
    assert u["windows_per_day"] == pytest.approx(gn["windows_per_day"]["value"], rel=0.05)
    assert u["longest_gap_h"] == pytest.approx(gn["longest_gap_h"]["value"], abs=0.5)
    loo = {x["without"]: x["union_min_per_day"] for x in t["leave_one_out"]}
    assert loo["GS Inuvik"] == pytest.approx(gn["leave_one_out_union_min_per_day"]["without_inuvik"], rel=0.05)
    csv_text = (await client.get(f"/api/studies/{s.study_id}/contacts?format=csv")).text
    assert "UNION" in csv_text and "GS Inuvik" in csv_text
    # export collector sections are real
    ex = (await client.get(f"/api/studies/{s.study_id}/export-context?sections=contacts,data_budget")).json()
    assert ex["contacts"]["union"]["min_per_day"] == pytest.approx(gn["union_min_per_day"]["value"], rel=0.05)
    assert ex["data_budget"]["daily"]["closure"]["id"] == "C1"
    # TM/TC database generated from the SIDs
    j = (await client.get(f"/api/studies/{s.study_id}/cdr/export/tmtc.json")).json()
    sids = {(r["sid"], r["copy"]) for r in j["sids"]}
    assert (20, "real-time") in sids and (120, "stored (of 20)") in sids and (101, "stored (of 1)") in sids
    assert len([p for p in j["parameters"] if str(p["param_id"]).startswith("SID")]) == sum(len(x["parameters"]) for x in HK["sids"])
    r = await client.get(f"/api/studies/{s.study_id}/cdr/export/tmtc.xlsx")
    assert r.status_code == 200
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(r.content))
    assert {"settings", "parameters", "sids", "stores", "rt_profiles"} <= set(wb.sheetnames)
    assert "interval_s[" in (await client.get(f"/api/studies/{s.study_id}/cdr/export/tmtc.csv")).text
