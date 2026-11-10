"""W1.09 c/e/h, W1.07 (server side), W5.01-W5.04, W5.06: licensing and disposal on the Northern Fire
and Ice fixture.

Numbers are taken from the fixture's NUMBERS.yaml, never retyped.
"""
from __future__ import annotations

import io
import zipfile

import pytest

from tests.fixtures.nfi import load, seed_nfi

N = load("NUMBERS")
DISP = N["disposal"]
SAIL = DISP["sail"]
ORBIT = N["orbit"]


# ───────────────────────────────────────────────────────────── physics (W5.02)

def _assess(**kw):
    from spacecdf_common.physics.disposal import DragDevice, assess_disposal, year_of
    dev = DragDevice(deployed_area_m2=SAIL["area_m2"], mass_kg=SAIL["mass_kg"],
                     independent_circuits=DISP["release_circuits"])
    args = dict(altitude_km=ORBIT["altitude_km"]["value"], mass_kg=N["mass"]["limit_kg"],
                launch_year=year_of("2030-06"), operations_years=2, device=dev, smallest_dimension_cm=10.0)
    args.update(kw)
    return assess_disposal(**args)


def test_sail_lifetime_matches_the_baseline_within_15_percent():
    a = _assess()
    ws = DISP["lifetime_with_sail_y_590km"]
    assert a.lifetime_with_sail_y["nominal"] == pytest.approx(ws["nominal"], rel=0.15)
    assert a.lifetime_with_sail_y["weak"] == pytest.approx(ws["weak"], rel=0.15)
    assert a.lifetime_with_sail_y["strong"] == pytest.approx(ws["strong"], rel=0.15)
    lo, hi = a.without_sail_range_y
    assert lo == pytest.approx(14, rel=0.15) and hi == pytest.approx(42, rel=0.15)
    assert a.highest_start_altitude_5y_km["weak"] == pytest.approx(DISP["highest_start_altitude_for_5y_km"]["weak_cycle"], abs=15)


def test_ised_checks_with_and_without_the_sail():
    a = _assess()
    checks = {c["id"]: c for c in a.checks}
    assert all(c["pass"] for c in a.checks) and a.compliant
    assert checks["ISED-DM-02"]["value"] >= DISP["rules"]["probability_min"]
    assert checks["ISED-DM-03"]["value"] < DISP["rules"]["collision_probability_max"]
    no = _assess(device=None)
    assert {c["id"]: c["pass"] for c in no.checks}["ISED-DM-01"] is False
    high = _assess(altitude_km=640.0)
    assert {c["id"]: c["pass"] for c in high.checks}["ISED-DM-05"] is False      # apogee > 600 km, no propulsion


def test_debris_compliance_score_uses_the_sail_area():
    from spacecdf_common.physics.debris import compute_debris_compliance
    base = compute_debris_compliance(590, 97.75, 3.87, mission_duration_years=2)
    sail = compute_debris_compliance(590, 97.75, 3.87, mission_duration_years=2, drag_device_area_m2=2.1,
                                     start_year=2030.5)
    assert not base.compliant_5yr and sail.compliant_5yr
    assert sail.deorbit_method == "drag_augmentation" and sail.debris_compliance_score >= 50 > base.debris_compliance_score - 10


def test_eol_api_lifetime_depends_on_the_cross_section_and_the_sail():
    from spacecdf_server.services.regulatory import generate_eol_report
    small = generate_eol_report(orbit_altitude_km=590, dry_mass_kg=6.0, cross_section_m2=0.04)
    large = generate_eol_report(orbit_altitude_km=590, dry_mass_kg=6.0, cross_section_m2=0.12)
    sail = generate_eol_report(orbit_altitude_km=590, dry_mass_kg=6.0, cross_section_m2=0.08, drag_sail_area_m2=2.1,
                               start_year=2027.5, mission_duration_years=3)
    lt = lambda r: r["sections"]["orbital_lifetime"]["estimated_orbital_lifetime_years"]["value"]  # noqa: E731
    assert lt(small) > lt(large)                                        # EG D8: the area is used
    assert sail["sections"]["compliance_ised_5yr"]["compliant"]["value"] is True


# ───────────────────────────────────────────────────────────── spectrum (W1.09h)

async def test_spectrum_catalogue_and_itu_template(client):
    bands = (await client.get("/api/lifecycle/spectrum/bands?license_type=academic")).json()["bands"]
    by = {(b["freq_min_mhz"], b["freq_max_mhz"]): b for b in bands}
    assert by[(449.75, 450.25)]["service"] == "Space Operation (Earth-to-space)"
    assert by[(401.0, 402.0)]["service"] == "Space Operation (space-to-Earth)"
    assert (148.0, 149.9) in by
    assert all("Amateur" not in b["service"] and "MetAids" not in b["service"] for b in by.values())
    r = await client.post("/api/lifecycle/spectrum/itu-api-template", json={
        "frequency_bands": [{"freq_min_mhz": 401.0, "freq_max_mhz": 402.0, "direction": "downlink"}]})
    assert r.status_code == 200 and "Space Operation" in r.json()["sections"]["satellite_network"]["service_type"]
    bad = await client.post("/api/lifecycle/spectrum/itu-api-template", json={"frequency_bands": [{"band": "UHF"}]})
    assert bad.status_code == 422
    assert (await client.get("/api/lifecycle/spectrum/bands?license_type=pirate")).status_code == 422


# ───────────────────────────────────────────────────────────── the study (S2)

@pytest.fixture()
async def s2(client):
    return await seed_nfi(client, "S2")


async def test_assignments_deorbit_and_rsssa_on_s2(client, s2):
    sid = s2.study_id
    j = (await client.get(f"/api/lifecycle/licensing/{sid}")).json()
    asg = {a["id"]: a for a in j["derived"]["assignments"]}
    dl = asg["SS-TX-DL"]                                                # W5.01
    assert dl["centre_frequency_mhz"] == 401.5 and dl["emission_designator"] == "50K0G1D"
    assert dl["service"] == "Space Operation (space-to-Earth)" and dl["pfd_5deg_dbw_m2"] < -100
    ups = [a for a in asg.values() if a["side"] == "earth" and a["transmits"]]
    assert len(ups) == 4 and {a["centre_frequency_mhz"] for a in ups} == {450.0}
    assert all("9.21" in a["coordination"] for a in ups)
    assert asg["SS-RX-UL-VHF"]["fallback"] and asg["SS-RX-UL-VHF"]["band_mhz"] == [148.0, 149.9]

    # W1.09c / W5.02: the deorbit report runs, with the sail, and no propellant item
    rep = (await client.post(f"/api/exports/deorbit/{sid}")).json()
    blob = str(rep)
    assert "not available" not in blob and "Vent propellant" not in blob
    ws = rep["analysis"]["lifetime_with_sail_years"]
    assert ws["nominal"] == pytest.approx(DISP["lifetime_with_sail_y_590km"]["nominal"], rel=0.15)
    assert ws["weak"] == pytest.approx(DISP["lifetime_with_sail_y_590km"]["weak"], rel=0.15)
    assert rep["compliance_summary"]["ised_5yr"] is True and rep["compliance_summary"]["compliant"] is True
    assert rep["spacecraft"]["drag_sail"]["deployed_area_m2"] == SAIL["area_m2"]
    docx = await client.post(f"/api/exports/deorbit/{sid}?fmt=docx")
    assert docx.status_code == 200 and len(docx.content) > 1000

    # W1.09e: GSD from the payload, not altitude x pointing accuracy
    rs = (await client.post(f"/api/exports/rsssa/{sid}")).json()
    assert rs["gsd_estimate_m"] == pytest.approx(N["payload"]["swir"]["gsd_m_590km"], abs=1.0)
    assert len(rs["ground_stations"]) == 4 and rs["orbital_lifetime"]["with_drag_sail"] is True


async def test_licensing_record_tracker_and_validation(client, s2):
    sid = s2.study_id
    j = (await client.get(f"/api/lifecycle/licensing/{sid}")).json()
    assert j["version"] == 0 and len(j["filings"]) == 6
    body = {"applicant": {"legal_name": "Example applicant", "address": "1 Example Street"},
            "cdpp": {"command_encryption": "AES-256 (CCSDS SDLS)", "key_management": "keys loaded before launch"},
            "filings": [{"id": "ised_preconsultation", "status": "submitted", "submitted": "2026-11-10"}],
            "version": 0}
    r = await client.put(f"/api/lifecycle/licensing/{sid}", json=body)
    assert r.status_code == 200, r.text
    assert (await client.put(f"/api/lifecycle/licensing/{sid}", json=body)).status_code == 409   # stale version
    bad = await client.put(f"/api/lifecycle/licensing/{sid}", json={"filings": [{"id": "x", "status": "maybe"}]})
    assert bad.status_code == 422
    j = (await client.get(f"/api/lifecycle/licensing/{sid}")).json()
    pre = next(f for f in j["filings"] if f["id"] == "ised_preconsultation")
    assert pre["status"] == "submitted" and j["record"]["cdpp"]["command_encryption"].startswith("AES")
    # W5.06: the export-context section feeds the packs
    from spacecdf_server.services.export_context import collect
    sx = await collect(sid, gate="pdr", sections=["mission", "elements", "rollup", "licensing"])
    assert sx.errors == {} and len(sx.licensing["filings"]) == 6
    assert all(f["start_by"] for f in sx.licensing["filings"]) and sx.licensing["filing_counts"]["submitted"] == 1
    # DRAMA / DAS import: numbers read from a pasted report
    ev = await client.post(f"/api/lifecycle/licensing/{sid}/evidence", json={
        "text": "DRAMA 3.1 OSCAR\nOrbital lifetime (years): 3.2\nCollision probability: 2.1e-6\n"})
    assert ev.status_code == 200 and ev.json()["evidence"]["lifetime_years"] == 3.2
    deb = (await client.post(f"/api/exports/regulatory/debris/{sid}")).json()
    assert any("DRAMA" in r["label"] for s in deb["sections"] for r in s["rows"])


async def test_licensing_seat_guard(client, s2):
    sid = s2.study_id

    def who(email: str) -> dict:
        return {"X-Goog-Authenticated-User-Email": f"accounts.google.com:{email}", "X-C2O-Name": "x"}
    prof = who("prof@c2o.live")
    import os
    os.environ["SPACECDF_INSTRUCTORS"] = "prof@c2o.live"
    try:
        r = await client.post(f"/api/studies/{sid}/team/preset", json={"team_size": "6"}, headers=prof)
        if r.status_code != 200:
            pytest.skip(f"seat preset unavailable: {r.status_code}")
        await client.post(f"/api/studies/{sid}/team/claim", json={"seats": ["power_engineer"]}, headers=who("p@c2o.live"))
        r = await client.put(f"/api/lifecycle/licensing/{sid}", json={"notes": "x"}, headers=who("p@c2o.live"))
        assert r.status_code == 403
        await client.post(f"/api/studies/{sid}/team/claim", json={"seats": ["comms_engineer"]}, headers=who("c@c2o.live"))
        r = await client.put(f"/api/lifecycle/licensing/{sid}", json={"notes": "y"}, headers=who("c@c2o.live"))
        assert r.status_code == 200, r.text
    finally:
        os.environ.pop("SPACECDF_INSTRUCTORS", None)
        from spacecdf_server.seats import store
        store.reset_memory()


async def test_element_trl_and_sequential_property_edits(client, s2):
    """W1.07 server side: TRL is editable on a custom element, and edits sent one after another
    with the version each response returns never conflict (the debounced client protocol)."""
    el = s2.elements["Independent deorbit timer and battery (2 release circuits)"]
    r = await client.patch(f"/api/elements/{el['id']}", json={"version": el["version"], "trl": 4})
    assert r.status_code == 200 and r.json()["trl"] == 4
    v = r.json()["version"]
    statuses = []
    for i in range(20):
        r = await client.patch(f"/api/elements/{el['id']}", json={"version": v, "performance": {"note": "x" * (i + 1)}})
        statuses.append(r.status_code)
        v = r.json().get("version", v)
    assert 409 not in statuses
    assert (await client.get(f"/api/elements/{el['id']}")).json()["performance"]["note"] == "x" * 20


# ───────────────────────────────────────────────────────────── documents (W5.04, S4)

async def test_regulatory_documents_on_s4(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    ru = (await client.get(f"/api/studies/{sid}/rollup")).json()

    rs = (await client.post(f"/api/exports/regulatory/rsssa/{sid}")).json()
    nums = [x["number"] for x in rs["sections"]]
    assert [str(i) for i in range(1, 33)] == nums[:32] and "Annex A" in nums and "Annex B" in nums
    derivable = {"9", "10", "11", "12", "13", "16", "17", "23", "24"}
    rows = [(sec["number"], r) for sec in rs["sections"] for r in sec["rows"]]
    leaked = [r for n, r in rows if r["source"] == "design" and "APPLICANT INPUT REQUIRED" in r["value"]]
    assert leaked == []
    assert not [r for n, r in rows if n in derivable and r["source"] == "input"
                and r["label"] in ("Altitude", "Inclination", "Form factor", "Planned launch date")]
    blob = str(rs)
    assert rs["key"]["ltdn"] == "10:30" and "10:30 LTDN" in blob
    assert rs["key"]["gsd_m"] == pytest.approx(N["payload"]["swir"]["gsd_m_590km"], abs=1.0)
    assert rs["key"]["mass_kg"] == pytest.approx(ru["mass"]["cbe_kg"]) and rs["key"]["form_factor"] == "3U"
    tbc = " ".join(rs["to_be_confirmed"])
    assert "SMSE-009-26" in tbc and "SMSE-005-26" in tbc          # listed as to be confirmed, not asserted

    deb = (await client.post(f"/api/exports/regulatory/debris/{sid}")).json()
    assert deb["key"]["lifetime_nominal_y"] == pytest.approx(DISP["lifetime_with_sail_y_590km"]["nominal"], rel=0.15)
    assert deb["key"]["lifetime_weak_y"] == pytest.approx(DISP["lifetime_with_sail_y_590km"]["weak"], rel=0.15)
    assert deb["key"]["reliability"] >= 0.95 and deb["key"]["pc_large"] < 1e-3 and deb["key"]["compliant"]

    earth = (await client.post(f"/api/exports/regulatory/ised-earth/{sid}")).json()
    assert len(earth["documents"]) == 4
    z = await client.post(f"/api/exports/regulatory/ised-earth/{sid}?fmt=docx")
    assert z.status_code == 200 and len(zipfile.ZipFile(io.BytesIO(z.content)).namelist()) == 4
    one = await client.post(f"/api/exports/regulatory/ised-earth/{sid}?fmt=docx&station=GS%20Inuvik")
    assert one.status_code == 200 and one.headers["content-type"].startswith("application/vnd.openxml")

    itu = (await client.post(f"/api/exports/regulatory/itu-api/{sid}")).json()
    assert itu["key"]["services"] and all(s.startswith("Space Operation") for s in itu["key"]["services"])
    space = (await client.post(f"/api/exports/regulatory/ised-space/{sid}")).json()
    assert space["key"]["service"] == "Space Operation (space-to-Earth)" and "Amateur" not in str(space)
    ex = (await client.post(f"/api/exports/regulatory/export-control/{sid}")).json()
    rows = ex["sections"][0]["table"]["rows"]
    assert any("6A003" in r[1] for r in rows) and any("5A002" in r[1] for r in rows)
    st = (await client.post(f"/api/exports/regulatory/status/{sid}")).json()
    assert st["key"]["filings"] == 6
    for kind in ("rsssa", "ised-space", "itu-api", "debris", "un-registration", "export-control", "status"):
        r = await client.post(f"/api/exports/regulatory/{kind}/{sid}?fmt=docx")
        assert r.status_code == 200 and len(r.content) > 1000, kind
    assert (await client.post(f"/api/exports/regulatory/nope/{sid}")).status_code == 400
    assert (await client.post("/api/exports/regulatory/rsssa/no-such-study")).status_code == 404
    # the Word rendering of the debris plan
    from docx import Document
    d = Document(io.BytesIO((await client.post(f"/api/exports/regulatory/debris/{sid}?fmt=docx")).content))
    text = "\n".join(p.text for p in d.paragraphs)
    assert "ISED" in text
