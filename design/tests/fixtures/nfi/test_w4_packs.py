"""W1.09 (a, b, f, g, i, j) and W4.01-W4.03 acceptance on the Northern Fire and Ice fixture (S4).

The review packs report what the team entered (collector + roll-up), not the parametric design
loop: the UHF 401 MHz link and not an invented X-band one, the team's risks, the selected
equipment, the roll-up mass; every requirement, no truncation; one pack per gate of the PI's
profile (MDR, PRR, SRR, PDR complete; CDR, QR, AR, FRR skeletons) with an index of what is
included and what is still missing.
"""
from __future__ import annotations

import io
import re
import zipfile

import pytest

from tests.fixtures.nfi import load, seed_nfi

INVENTED = ("X-band", "8.2 GHz", "13.0 m", "HUMAN INPUT REQUIRED", "SpaceWire", "28V regulated")


def _docx_text(data: bytes) -> str:
    from docx import Document
    d = Document(io.BytesIO(data))
    out = [p.text for p in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            out.append(" | ".join(c.text for c in r.cells))
    return "\n".join(out)


def _xlsx(data: bytes):
    import openpyxl
    return openpyxl.load_workbook(io.BytesIO(data))


def _text(name: str, data: bytes) -> str:
    if name.endswith(".docx"):
        return _docx_text(data)
    if name.endswith(".xlsx"):
        wb = _xlsx(data)
        return "\n".join(" | ".join("" if v is None else str(v) for v in row)
                         for ws in wb for row in ws.iter_rows(values_only=True))
    return data.decode("utf-8-sig")


async def _md(client, sid: str, review: str, lang: str = "en") -> dict:
    r = await client.post(f"/api/exports/docs/{sid}?review={review}&fmt=markdown&crosscheck=false&lang={lang}")
    assert r.status_code == 200, r.text
    return r.json()


async def test_gate_packs_differ_and_report_the_study(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    n = load("NUMBERS")
    reqs = load("requirements")["requirements"]
    risks = load("risks")["risks"]

    packs = (await client.get(f"/api/studies/{sid}/review-packs")).json()["packs"]
    assert [p["id"] for p in packs] == ["mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr"]
    assert [p["complete"] for p in packs] == [True] * 4 + [False] * 4

    # W1.09g: every gate of the profile (and the legacy mcr) is accepted; an unknown one is a 422
    md = {g: await _md(client, sid, g) for g in ("mdr", "prr", "srr", "pdr", "cdr", "frr")}
    assert (await _md(client, sid, "mcr"))["section_titles"] == md["mdr"]["section_titles"]
    assert (await client.post(f"/api/exports/docs/{sid}?review=xyz&fmt=markdown")).status_code == 422

    def titles(g):
        return {re.sub(r" \[[DBU]\]$", "", t) for t in md[g]["section_titles"]}
    assert titles("mdr") != titles("prr") != titles("pdr")
    assert len(titles("pdr") - titles("mdr")) >= 8, titles("pdr") - titles("mdr")
    assert "Test results" in titles("frr") and "Operations readiness" in titles("frr")

    pdr = md["pdr"]["document_markdown"]
    assert pdr.startswith("# Preliminary Design Review (PDR) — Northern Fire and Ice")
    for bad in INVENTED:
        assert bad not in pdr, bad
    # mass from the roll-up at the PDR step of the ladder
    ru = (await client.get(f"/api/studies/{sid}/rollup?gate=pdr")).json()
    assert ru["mass"]["cbe_kg"] == pytest.approx(n["mass"]["nominal_kg"], abs=0.01)
    assert ru["mass"]["with_maturity_kg"] == pytest.approx(n["mass"]["with_maturity_kg"], abs=0.01)
    for v in (ru["mass"]["cbe_kg"], ru["mass"]["with_maturity_kg"], ru["mass"]["with_system_margin_kg"]):
        assert f"| {v:g} |" in pdr, v
    assert f"| MDR | {ru['mass']['ladder']['mdr']:g} |" in pdr          # 4.98 kg, NUMBERS with system margin
    # the UHF link, the selected radio, the equipment list, every requirement, every risk
    assert "| downlink_band_mhz | 401, 402 |" in pdr and "| uplink_band_mhz | 449.75, 450.25 |" in pdr
    assert "Spacemanic Murgas UHF transceiver" in pdr
    eq = load("equipment")
    n_eq = sum(len(sub["items"]) for sub in eq["spacecraft"]["subsystems"])
    assert f"{n_eq} equipment lines" in pdr and n_eq == 32
    for r in reqs:
        assert f"| {r['id']} |" in pdr, r["id"]
    for i in range(1, len(risks) + 1):
        assert f"| RSK-{i:03d} |" in pdr
    assert f"{len(risks)} risks, highest likelihood x consequence first" in pdr
    # the MDR pack holds the need; open items are listed, never placeholders
    mdr = md["mdr"]["document_markdown"]
    assert "Mission statement and need" in md["mdr"]["section_titles"][2]
    assert "## " in mdr and "Open items" in md["mdr"]["section_titles"][-1]
    # French headings
    fr = await _md(client, sid, "pdr", "fr")
    assert "Bilan de masse" in fr["document_markdown"] and "Registre des risques [U]" in fr["section_titles"]

    # ── the PDR zip: every expected document, the index, the master budget (W4.03)
    r = await client.post(f"/api/exports/docs/{sid}?review=pdr&crosscheck=false")
    assert r.status_code == 200
    assert "PDR_Northern_Fire_and_Ice" in r.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = set(z.namelist())
    for f in ("INDEX.md", "docs/pdr.docx", "docs/pdr.md", "documents/TS_technical_requirements.docx",
              "documents/IRD_interfaces.docx", "documents/VP_verification_plan.docx",
              "documents/VCD_verification_control.docx", "documents/RMP_risk_management.docx",
              "documents/Launch_ICD.docx", "budgets/master_budget.xlsx", "budgets/bill_of_materials.xlsx",
              "data/requirements.csv", "data/risk_register.csv"):
        assert f in names, f
    index = z.read("INDEX.md").decode()
    assert "| included |" in index and "| missing |" in index and "generator not available yet" in index
    texts = {nm: _text(nm, z.read(nm)) for nm in names if nm.endswith((".docx", ".md", ".csv", ".xlsx"))}
    for nm, txt in texts.items():
        if nm == "documents/Diagrams.docx":
            continue   # the ops-pass figure takes its band from the analysis context (hand-off, see W0_SEAMS)
        for bad in INVENTED:
            assert bad not in txt, (nm, bad)
    # W1.09a: the TS lists every team requirement with its threshold, no IR-* row
    ts = texts["documents/TS_technical_requirements.docx"]
    assert all(r["id"] in ts for r in reqs) and "IR-" not in ts
    assert "MIS-COV-01 | performance | " in ts and "| >= 10 |" in ts
    # W1.09b: the RMP carries the register
    rmp = texts["documents/RMP_risk_management.docx"]
    assert all(f"RSK-{i:03d}" in rmp for i in range(1, len(risks) + 1))
    assert "to be populated" not in rmp
    # W4.03: the master budget opens, the mass total is the roll-up, P50 > 0
    wb = _xlsx(z.read("budgets/master_budget.xlsx"))
    assert {"Summary", "Mass", "Power", "Data", "Link", "Pointing", "Margins", "Cost", "Open items"} <= set(wb.sheetnames)
    ms = wb["Mass"]
    cbe = sum(float(row[2]) * float(row[3]) for row in ms.iter_rows(min_row=2, values_only=True)
              if isinstance(row[2], (int, float)) and isinstance(row[3], (int, float)))
    assert cbe == pytest.approx(ru["mass"]["cbe_kg"], abs=0.005)
    summary = {row[0]: row[1] for row in wb["Summary"].iter_rows(min_row=2, values_only=True) if row[0]}
    assert summary["Equipment cost P50"] > 0 and summary["Equipment cost P90"] > summary["Equipment cost P50"]
    assert summary["Equipment cost P50"] == pytest.approx(n["cost"]["flight_hardware_keur"]["value"], abs=0.5)
    assert len([r for r in wb["Power"].iter_rows(min_row=2, max_row=10, values_only=True) if r[0]]) == 9


async def test_did_route_xlsx_buttons_and_test_plan_launcher(client):
    s = await seed_nfi(client, "S3")
    sid = s.study_id
    n_req = len(load("requirements")["requirements"]) + len(load("requirements")["objectives"])
    n_risk = len(load("risks")["risks"])
    # W1.09f: the DID JSON reads the requirement store, the risks, the modes and the stations
    mrd = (await client.post(f"/api/ecss/dids/mrd/generate?study_id={sid}")).json()
    assert mrd["total_requirements"] == n_req
    rmp = (await client.post(f"/api/ecss/dids/rmp/generate?study_id={sid}")).json()
    assert rmp["total_risks"] >= n_risk
    conops = (await client.post(f"/api/ecss/dids/conops/generate?study_id={sid}")).json()
    assert conops["ground_stations"] == 4 and conops["total_modes"] >= 9
    ts = (await client.post(f"/api/ecss/dids/ts/generate?study_id={sid}")).json()
    assert ts["total_requirements"] == n_req
    # W1.09i: real workbooks behind the XLSX buttons, V&V columns right
    r = await client.get(f"/api/studies/{sid}/export/vv.xlsx")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/vnd.openxmlformats")
    ws = _xlsx(r.content)["V&V matrix"]
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0][:4] == ("Code", "Level", "Type", "Requirement") and len(rows) - 1 == n_req
    assert {r[2] for r in rows[1:]} <= {"functional", "performance", "interface", "process", "regulatory", None, ""}
    r = await client.get(f"/api/studies/{sid}/export/bom.xlsx")
    assert r.status_code == 200 and _xlsx(r.content)["Bill of materials"].max_row > 30
    # W1.09j: the launcher comes from the launch segment, not a silent default
    tp = (await client.post(f"/api/exports/test-plan/{sid}")).json()
    env = tp["environmental_profile"]
    assert "falcon" not in str(env["launch_vehicle"]).lower()
    assert env["launch_vehicle_source"] == "launch segment element" and "generic" in env["levels_source"]
