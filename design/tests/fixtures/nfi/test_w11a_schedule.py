"""W11a and W5.05 acceptance on the Northern Fire and Ice fixture: schedule-lite, cost, BOM export control.

* Milestones: the gate profile's reviews plus QR, AR and the Flight Readiness Review, the model
  deliveries and launch, dated from 2027-05 (launch target 2030-06 minus 37 months) to 2030-06.
* WBS: at least 10 work packages, one per space subsystem element under the platform package.
* Long-lead items from the KB lead times; the cost is the sum of the selected equipment
  (NUMBERS flight hardware), in EUR and CAD, with no launch cost when the launch is provided.
* Export control per part: the SWIR camera is flagged 6A003 and the encrypted radio 5A002.
"""
from __future__ import annotations

import pytest

from tests.fixtures.nfi import load, seed_nfi


async def test_schedule_milestones_wbs_long_lead_and_cost(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    sch = (await client.get(f"/api/studies/{sid}/schedule")).json()
    assert sch["settings"]["start_date"] == "2027-05" and sch["settings"]["launch_provided"] is True
    reviews = [m for m in sch["milestones"] if m["kind"] == "review"]
    codes = [m["code"] for m in reviews]
    assert len(reviews) >= 6 and codes[0] == "MDR" and {"PDR", "CDR", "QR", "AR", "FRR"} <= set(codes)
    frr = next(m for m in reviews if m["code"] == "FRR")
    assert frr["date"] == "2030-04"
    assert next(m for m in sch["milestones"] if m["code"] == "LAUNCH")["date"] == "2030-06"
    # wave 3 (3.A4): the v2 model philosophy (BB 6, EM 18, GS 24, PFM 30, LV 34, flight 36)
    v2 = sorted(load("vv_plan")["model_philosophy"], key=lambda m: m["month"])
    assert [m["month"] for m in sch["milestones"] if m["kind"] == "model"] == [m["month"] for m in v2]
    assert [m["date"] for m in sch["milestones"] if m["kind"] == "model"][:2] == ["2027-11", "2028-11"]
    dates = [m["date"] for m in sch["milestones"]]
    assert dates == sorted(dates)

    # wave 3 (3.A3): need-by dates of the long-lead parts and the licence filings as milestones
    adcs = next(r for r in sch["need_by"] if r["name"].startswith("CubeADCS"))
    em = next(m for m in v2 if m["model"] == "EM")["month"]
    assert adcs["model"] == "EM" and adcs["model_month"] == em == 18
    weeks = adcs["lead_time_weeks"]
    assert 12 <= weeks <= 20
    assert adcs["order_by_month"] == em - 1 - -(-weeks // 4.345) == 13
    assert adcs["freeze_by_month"] == adcs["order_by_month"] - 1 and not adcs["before_project_start"]
    filings = [m for m in sch["milestones"] if m["kind"] == "filing"]
    from spacecdf_server.services.licensing import DEFAULT_FILINGS
    assert len(filings) == len(DEFAULT_FILINGS) == sch["counts"]["filings"]
    pre = next(m for m in filings if "PRECONSULTATION" in m["code"])
    launch = next(m for m in sch["milestones"] if m["code"] == "LAUNCH")["month"]
    assert pre["month"] == launch - 42 < 0
    assert any(w["kind"] == "filing_before_start" and w["code"] == pre["code"] for w in sch["warnings"])

    wps = sch["work_packages"]
    assert len(wps) >= 10
    platform = [w for w in wps if w["parent_code"] == "4"]
    assert {w["name"] for w in platform} >= {"EPS", "AOCS", "Disposal (drag sail)"}
    assert all(w["element_id"] for w in platform)

    lead = sch["long_lead"]
    assert len(lead) >= 5 and all(item["source"] in ("kb", "element") for item in lead)
    assert any(item["name"].startswith("CubeADCS") for item in lead)
    assert lead[0]["max_weeks"] >= lead[-1]["max_weeks"]

    cost = sch["cost"]
    n = load("NUMBERS")["cost"]
    assert cost["flight_hardware"]["keur"] == pytest.approx(n["flight_hardware_keur"]["value"], abs=0.2)
    assert cost["launch"]["keur"] == 0 and cost["launch"]["provided"] is True
    assert cost["currency"] == "CAD"
    assert cost["total"]["kcad"] == pytest.approx(cost["total"]["keur"] * cost["eur_to_cad"], rel=1e-3)
    assert cost["p50"]["keur"] > 0 and cost["p90"]["keur"] >= cost["p50"]["keur"]
    largest = {i["name"]: i["total_keur"] for i in cost["items"][:3]}
    assert largest[next(k for k in largest if k.startswith("CubeADCS"))] == pytest.approx(53.5)

    # a bought launch is costed per CubeSat unit of the roll-up form factor (3U)
    r = await client.put(f"/api/studies/{sid}/schedule/settings", json={"launch_provided": False})
    assert r.status_code == 200
    c2 = (await client.get(f"/api/studies/{sid}/cost")).json()
    assert c2["launch"]["keur"] == pytest.approx(200.0, abs=0.1)
    # moving the start re-dates every milestone
    await client.put(f"/api/studies/{sid}/schedule/settings", json={"start_date": "2027-06"})
    sch2 = (await client.get(f"/api/studies/{sid}/schedule")).json()
    assert next(m for m in sch2["milestones"] if m["code"] == "FRR")["date"] == "2030-05"
    assert (await client.put(f"/api/studies/{sid}/schedule/settings", json={"currency": "USD"})).status_code == 422

    sx = (await client.get(f"/api/studies/{sid}/export-context?sections=schedule")).json()["schedule"]
    assert sx["status"] == "ok" and sx["counts"]["work_packages"] == len(wps)


async def test_bom_export_control_per_part(client):
    s = await seed_nfi(client, "S2")
    bom = (await client.get(f"/api/lifecycle/bom/{s.study_id}")).json()
    by_kb = {l["item_id"]: l for l in bom["lines"]}
    swir = by_kb["pl-av-alvium-1800c-530-vswir"]
    assert swir["export_controlled"] and swir["eccn"].startswith("6A003") and swir["origin"] == "DE"
    radio = by_kb["txr-spacemanic-murgas"]
    assert radio["export_controlled"] and "5A002" in radio["eccn"] and "EC-5A002" in radio["export_rules"]
    vnir = by_kb["pl-av-alvium-1800c-1620m"]
    assert not vnir["export_controlled"]
    gnss = by_kb["gps-gom-nanosense-gpskit"]
    assert "EC-GNSS" in gnss["export_rules"] and gnss["eccn"].startswith("7A994")
    listed = {e["name"] for e in bom["export_control"]}
    assert swir["name"] in listed and radio["name"] in listed
    assert bom["summary"]["export_controlled_items"] == 2
    csv = (await client.get(f"/api/lifecycle/bom/{s.study_id}?fmt=csv")).text
    assert "ECCN" in csv.splitlines()[0] and "6A003" in csv


def test_export_assessment_flags_from_the_parts():
    from spacecdf_server.services.bom_generator import export_assessment_flags
    els = [
        {"id": "com", "element_type": "subsystem", "name": "Communications", "subsystem_domain": "ttc",
         "performance": {"encryption": "AES-256"}},
        {"id": "r", "element_type": "component", "parent_id": "com", "name": "UHF transceiver", "subsystem_domain": "ttc",
         "kb_component_id": "txr-spacemanic-murgas"},
        {"id": "c", "element_type": "component", "name": "SWIR camera", "subsystem_domain": "payload",
         "kb_component_id": "pl-av-alvium-1800c-530-vswir"},
        {"id": "s", "element_type": "component", "name": "Copper thermal strap (SWIR camera to radiator)",
         "subsystem_domain": "thermal", "kb_component_id": "th-thermal-strap-01"},
    ]
    flags = {f["flag"]: f for f in export_assessment_flags(els)}
    assert set(flags) == {"PART_6A003", "PART_5A002"}
    assert flags["PART_6A003"]["components"][0]["component"] == "SWIR camera"
