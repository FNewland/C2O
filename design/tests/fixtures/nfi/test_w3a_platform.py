"""Wave 3, agent A acceptance on the Northern Fire and Ice fixture (S4): the design loop reads the
study (3.A1), the reliability analysis with its FMEA (3.A5), the thermal nodal model (3.A6) and the
priced cost model (3.A7). Figures come from the fixture (NUMBERS, budgets) and the store.
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import load, seed_nfi


def _p(res: dict, path: str):
    return (res["parameters"].get(path) or {}).get("value")


async def test_design_loop_reliability_thermal_and_cost_on_the_study(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    n, b = load("NUMBERS"), load("budgets")

    # ── 3.A5 reliability over the mission-success horizon, FMEA per subsystem ──
    rel = (await client.post(f"/api/studies/{sid}/reliability/run")).json()
    res = rel["result"]
    assert res["horizon"]["success_horizon_months"] == 12 and "12 months" in res["evidence"]
    assert res["horizon"]["pre_operations_months"] > 0                    # LEOP + commissioning from the ConOps
    assert res["target"] == pytest.approx(0.80)
    assert res["mission_reliability"] > res["design_life_reliability"]  # 12 months beats 3 years
    blocks = {b_["name"]: b_ for b_ in rel["blocks"]}
    wing = next(v for k, v in blocks.items() if "DMSA" in k)
    assert (wing["k"], wing["n"]) == (1, 2)                              # one wing is enough (SYS-REL-03)
    sail = next(v for k, v in blocks.items() if "drag sail" in k)
    assert res["excluded_from_mission_success"] == [sail["name"]]
    cam = next(v for k, v in blocks.items() if "C-530" in k)
    assert 0 < cam["duty_cycle"] < 0.2                                   # imaging share from the Modes tab
    fm = (await client.post(f"/api/studies/{sid}/fmea/propose")).json()
    assert fm["added"] == len(fm["fmea"]) > 0
    subs = {r["subsystem"] for r in fm["fmea"]}
    assert {"PAY", "EPS", "AOCS", "COM", "OBC", "DIS"} <= subs
    assert all(r["criticality"] == r["severity"] * r["probability"] for r in fm["fmea"])
    assert any(r["risk_ids_json"] for r in fm["fmea"])
    assert (await client.post(f"/api/studies/{sid}/fmea/propose")).json()["added"] == 0
    row = fm["fmea"][0]
    up = (await client.patch(f"/api/studies/{sid}/fmea/{row['id']}", json={"severity": 2, "probability": 2})).json()
    assert up["criticality"] == 4 and up["origin"] == "user"
    ev = (await client.get(f"/api/studies/{sid}/reliability/evidence")).json()
    assert ev["horizon_months"] == 12 and ev["fmea_rows"] == len(fm["fmea"]) and not ev["fmea_missing_subsystems"]
    assert ev["ok"] == (res["meets_target"] is True and not ev["critical_unlinked"])

    # ── 3.A6 thermal nodal model: nodes from the product tree, hot and cold cases, margins, heaters ──
    th = (await client.post(f"/api/studies/{sid}/thermal-model/run")).json()
    assert 6 <= th["counts"]["nodes"] <= 14 and {c["kind"] for c in th["cases"]} == {"hot", "cold"}
    hot = next(c for c in th["cases"] if c["kind"] == "hot")
    cold = next(c for c in th["cases"] if c["kind"] == "cold")
    assert hot["beta_deg"] > cold["beta_deg"] and hot["eclipse_min"] < cold["eclipse_min"]
    assert all(c["status"] == "solved" for c in th["cases"])
    bat = next(x for x in th["nodes"] if x["name"] == "Battery")
    assert bat["op_min_c"] >= 0                                           # Li-ion charging limit
    m = bat["data_json"]["margins"]
    assert m["acceptance"] == pytest.approx(m["design"] - 5) and m["qualification"] == pytest.approx(m["design"] - 10)
    for x in th["nodes"]:
        r_hot, r_cold = hot["results_json"][x["code"]], cold["results_json"][x["code"]]
        assert r_hot["t_max_c"] >= r_hot["t_min_c"] and -120 < r_cold["t_min_c"] < 120
    if th["summary"]["out_of_design_range"]:
        th2 = (await client.post(f"/api/studies/{sid}/thermal-model/heaters/accept")).json()
        assert len(th2["summary"]["out_of_design_range"]) < len(th["summary"]["out_of_design_range"])
    tev = (await client.get(f"/api/studies/{sid}/thermal-model/evidence")).json()
    assert tev["solved"] and tev["nodes"] >= 6 and tev["cases"] == ["cold", "hot"]

    # ── 3.A7 the priced cost model: labour, test campaigns, hardware, reserve; launch provided ──
    cost = (await client.post(f"/api/studies/{sid}/cost/price")).json()
    cats = cost["by_category"]
    assert cats["launch"] == 0 and cats["labour"] > 0 and cats["test_campaign"] > 0 and cats["reserve"] > 0
    hw = sum(i["total_keur"] for i in cost["items"] if i["category"] == "hardware" and i["name"].startswith("Flight"))
    assert hw == pytest.approx(n["cost"]["flight_hardware_keur"]["value"], abs=0.5)
    base = sum(v for k, v in cats.items() if k not in ("reserve", "launch"))
    assert cats["reserve"] == pytest.approx(base * 0.20, abs=0.1)
    assert cost["total_keur"] == pytest.approx(sum(cats.values()), abs=0.1)
    assert cost["target_meur"] == 0.8 and cost["within_target"] == (cost["total_meur"] <= 0.8)
    kinds = {(i["data_json"] or {}).get("kind") for i in cost["items"] if i["category"] == "test_campaign"}
    assert {"sine", "random", "tvac", "emc"} <= kinds
    # a line the team edits survives the next price, and the reserve follows it
    gse = next(i for i in cost["items"] if i["name"] == "Ground support equipment")
    await client.patch(f"/api/studies/{sid}/cost/items/{gse['id']}", json={"total_keur": 25.0})
    again = (await client.post(f"/api/studies/{sid}/cost/price")).json()
    assert next(i for i in again["items"] if i["name"] == "Ground support equipment")["total_keur"] == 25.0
    assert again["by_category"]["reserve"] == pytest.approx(cats["reserve"] + 2.0, abs=0.1)

    # ── 3.A1 the design loop on the study's own values ──
    loop = (await client.post(f"/api/design/{sid}/run")).json()
    kn = (await client.get(f"/api/studies/{sid}/key-numbers")).json()["items"]
    union = kn["contacts.union_min_per_day"]["value"]
    contact_min = _p(loop, "orbit.contact_time_per_day_s") / 60
    assert contact_min == pytest.approx(union, abs=0.01) and contact_min == pytest.approx(125.7, rel=0.02)
    assert _p(loop, "power.sa_power_eol_w") == pytest.approx(n["power"]["eol_generation_w"]["value"], abs=0.05)
    assert _p(loop, "mass.margin_to_limit_kg") == pytest.approx(b["mass"]["totals"]["margin_to_limit_kg"], abs=0.01)
    assert _p(loop, "systems.mass_margin_percent") > 0
    assert _p(loop, "orbit.delta_v_deorbit_ms") == 0 and _p(loop, "orbit.disposal_method") == "drag_sail"
    assert _p(loop, "reliability.horizon_months") == 12
    assert _p(loop, "reliability.mission_reliability") == pytest.approx(res["mission_reliability"], abs=1e-3)
    assert _p(loop, "cost.launch_keur") == 0
    assert _p(loop, "cost.total_keur") == pytest.approx(again["total_keur"], abs=1)
    assert _p(loop, "cost.phase0_estimate_keur") > 0
    case = next(c for c in (await client.get(f"/api/studies/{sid}/link-budgets")).json()["items"]
                if c.get("is_design_case") and c.get("direction") == "downlink")
    assert _p(loop, "link.downlink_margin_db") == pytest.approx(case["margin_db"], abs=0.01)
    summ = loop["summary"]
    assert summ["eol_power_w"]["value"] == pytest.approx(12.2, abs=0.05)
    assert "parts" in summ["eol_power_w"]["source"] and summ["eol_power_w"]["phase0_estimate"] != summ["eol_power_w"]["value"]
    assert summ["mass_margin_to_limit_kg"]["value"] == pytest.approx(0.994, abs=0.01)
    assert summ["reliability"]["horizon_months"] == 12
    assert summ["cost_keur"]["source"].startswith("priced cost model")
    assert not any("61.1" in w for w in loop["warnings"])   # the link agent's own -0.0 dB warning is H's (3.H1)

    # ── round trip: blocks, FMEA, thermal model and cost lines travel with the project file ──
    a = (await client.get(f"/api/studies/{sid}/export")).json()
    imp = (await client.post("/api/studies/import", json=a)).json()
    for t in ("reliability_blocks", "fmea_rows", "thermal_nodes", "thermal_couplings", "thermal_cases", "cost_items"):
        assert len(a["tables"][t]) > 0, t
    th3 = (await client.get(f"/api/studies/{imp['id']}/thermal-model")).json()
    ids = {x["id"] for x in th3["nodes"]}
    assert all(c["node_a"] in ids and (c["node_b"] in ids or c["node_b"] == "space") for c in th3["couplings"])
    rel3 = (await client.get(f"/api/studies/{imp['id']}/reliability")).json()
    assert rel3["result"]["mission_reliability"] == pytest.approx(res["mission_reliability"], abs=1e-4)
    cost3 = (await client.get(f"/api/studies/{imp['id']}/cost/items")).json()
    assert cost3["total_keur"] == pytest.approx(again["total_keur"], abs=0.01)
    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=reliability,thermal_model,cost")).json()
    assert sx["reliability"]["status"] == sx["thermal_model"]["status"] == sx["cost"]["status"] == "ok"
    assert sx["cost"]["total_keur"] == pytest.approx(again["total_keur"], abs=0.01)
