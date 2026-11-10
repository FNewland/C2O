"""Wave 3, agent X (3.X1 SE diagrams, 3.X2 packs carry the V, 3.X3 SEMP) on the nfi v2 fixture.

The wave-3 sections other agents own are still stubs on this branch: ``w3x_support`` registers
collectors that return the baseline records (only where the section is still a stub), and writes
the v2 function tree into the store (agent R's bulk import does it through the API). Counts come
from the store and the baseline files, never from typed constants.
"""
from __future__ import annotations

import io
import zipfile

import pytest

from tests.fixtures.nfi import load, seed_nfi
from tests.fixtures.nfi.w3x_support import counts_by_stage, register_sections, write_functions


def _docx_text(data: bytes) -> str:
    from docx import Document
    d = Document(io.BytesIO(data))
    out = [p.text for p in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            out.append(" | ".join(c.text for c in r.cells))
    return "\n".join(out)


async def _seeded(client, monkeypatch, stage: str = "S4"):
    s = await seed_nfi(client, stage)
    register_sections(monkeypatch)
    await write_functions(s.study_id, s.elements)
    return s


async def _dgm(client, sid: str, kind: str, **q) -> dict:
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    r = await client.get(f"/api/studies/{sid}/diagrams/{kind}" + (f"?{qs}" if qs else ""))
    assert r.status_code == 200, r.text
    return r.json()


async def test_se_diagram_set_from_the_model(client, monkeypatch):
    s = await _seeded(client, monkeypatch)
    sid = s.study_id
    sh = load("stakeholders")
    fns = load("functions")
    tops = [f for f in fns["functions"] if not f.get("parent")]

    # context: the 4 stations, the launch segment, 12 stakeholders and the regulator, 0 gaps
    ctx = await _dgm(client, sid, "context")
    assert ctx["counts"]["stakeholders"] == len(sh["stakeholders"]) == 12
    from spacecdf_server.services.export_context import collect
    els = (await collect(sid, sections=["elements"])).elements["items"]
    stations = [e for e in els if (e.get("performance") or {}).get("lat") is not None]
    assert ctx["counts"]["stations"] == len(stations) == 4
    assert ctx["counts"]["launch"] == 1 and ctx["counts"]["regulators"] >= 1
    assert ctx["gaps"] == [], ctx["gaps"]
    assert any(n["id"].startswith("sh:") for n in ctx["nodes"])

    # stakeholder map: grouped by category, MOE-04 and MOE-10 flagged to co-define
    smap = await _dgm(client, sid, "stakeholder_map")
    cats = {x["category"] for x in sh["stakeholders"]}
    assert smap["counts"]["categories"] == len(cats) == 5
    assert smap["counts"]["needs"] == len(sh["needs"]) == 12
    assert {g["id"] for g in smap["groups"]} == {"cat:" + c for c in cats}
    ph = next(g for g in smap["gaps"] if g["code"] == "moe_placeholder")
    assert ph["severity"] == "info" and "MOE-04" in ph["message"]["p"]["ids"] and "MOE-10" in ph["message"]["p"]["ids"]

    # FFBD: the 13 top functions and their exchanges
    ff = await _dgm(client, sid, "ffbd")
    assert ff["counts"]["functions"] == len(tops) == 13
    top_pairs = {(x["from"].split(".")[0], x["to"].split(".")[0]) for x in fns["functional_interfaces"]}
    top_pairs = {p for p in top_pairs if p[0] != p[1]}
    assert ff["counts"]["exchange_pairs"] == len(top_pairs)
    assert len(ff["edges"]) == len(top_pairs)
    assert len({g["id"] for g in ff["groups"]}) >= 4          # ConOps-phase lanes

    # functional N²: 13 × 13, cells name the items
    n2f = await _dgm(client, sid, "n2", view="functions")
    assert n2f["options"]["view"] == "functions" and n2f["counts"]["functions"] == 13
    assert n2f["counts"]["cells"] == len(top_pairs)
    n2s = await _dgm(client, sid, "n2", level="system")
    assert n2s["options"]["level"] == "system"

    # V diagram: stage counts equal the store
    reqs = (await collect(sid, sections=["requirements"])).requirements["items"]
    store = counts_by_stage(reqs)
    v = await _dgm(client, sid, "v_model")
    assert v["counts"]["by_stage"] == store
    vv = load("vv_plan")
    for st in ("PDR", "CDR", "QR", "AR", "IOV"):
        assert store[st] == sum(1 for r in vv["matrix"] if str(r.get("stage")).upper() == st), st
    assert v["counts"]["validation"] == len(vv["validation_plan"]) == 7
    assert v["counts"]["documents"]["srr"] >= 1

    # one trade matrix per trade, with the ±20 % sensitivity columns
    cat = (await client.get(f"/api/studies/{sid}/diagrams")).json()["diagrams"]
    tm_entry = next(e for e in cat if e["kind"] == "trade_matrix")
    trade_ids = [t["id"] for t in (await client.get(f"/api/studies/{sid}/trades")).json()["items"]]
    assert sorted(tm_entry["instances"]) == sorted(trade_ids) and trade_ids
    for tid in tm_entry["instances"]:
        tm = await _dgm(client, sid, "trade_matrix", focus=tid)
        assert tm["options"]["focus"] == tid
        assert tm["table"]["columns"][-2:] == ["−20 %", "+20 %"]
        assert tm["counts"]["winner"]

    # budget flow-down from the ledger: closes at 4.43 kg and 4.91 W
    b = load("budgets")
    bf = await _dgm(client, sid, "budget_flowdown")
    assert bf["counts"]["sums"]["mass"] == pytest.approx(b["mass"]["closure"]["sum_allocations_kg"], abs=1e-6)
    assert bf["counts"]["sums"]["power_avg"] == pytest.approx(b["power"]["closure"]["sum_allocations_w"], abs=1e-6)
    assert not [g for g in bf["gaps"] if g["severity"] == "alarm"]

    # verification flow: level → method → model → stage, same stage counts
    vf = await _dgm(client, sid, "verification_flow")
    assert vf["counts"]["by_stage"] == store

    # SVG and the SE document (every trade gets its own figure)
    r = await client.get(f"/api/studies/{sid}/diagrams/v_model/svg?lang=fr")
    assert r.status_code == 200 and "<svg" in r.text
    r = await client.get(f"/api/studies/{sid}/diagrams-document.docx?set=se")
    assert r.status_code == 200
    txt = _docx_text(r.content)
    assert txt.count("Trade matrix — ") >= len(trade_ids)
    for title in ("Context diagram", "Stakeholder map", "Functional flow block diagram", "V diagram", "Budget flow-down",
                  "Verification flow", "N² chart — functions"):
        assert title in txt, title


async def test_se_diagrams_report_gaps_on_an_empty_study(client):
    s = await seed_nfi(client, "S0")
    for kind in ("context", "stakeholder_map", "ffbd", "v_model", "trade_matrix", "budget_flowdown", "verification_flow"):
        m = await _dgm(client, s.study_id, kind)
        assert m["kind"] == kind
        assert m["gaps"] or m["empty"], kind
    m = await _dgm(client, s.study_id, "n2", view="functions")
    assert m["empty"] is not None


def _xlsx_sheet(data: bytes, name: str) -> list[tuple]:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data))
    return list(wb[name].iter_rows(values_only=True))


async def test_packs_carry_the_v(client, monkeypatch):
    s = await _seeded(client, monkeypatch)
    sid = s.study_id
    sh = load("stakeholders")
    b = load("budgets")
    n = load("NUMBERS")
    md = {}
    for gate in ("mdr", "prr", "srr", "pdr"):
        r = await client.post(f"/api/exports/docs/{sid}?review={gate}&fmt=markdown&crosscheck=false")
        assert r.status_code == 200, r.text
        md[gate] = r.json()
        text = md[gate]["document_markdown"]
        assert "1103 MB" not in text and "1103" not in text, gate
        for bad in ("HUMAN INPUT REQUIRED", "[To be defined]", "Collector section"):
            assert bad not in text, (gate, bad)
        # stakeholder register: 12 stakeholders, 15 MOEs, the two placeholders to co-define
        assert f"{len(sh['stakeholders'])} stakeholders in 5 categories" in text, gate
        for m in sh["moes"]:
            assert f"| {m['id']} |" in text, (gate, m["id"])
        row04 = next(line for line in text.splitlines() if line.startswith("| MOE-04 |"))
        row10 = next(line for line in text.splitlines() if line.startswith("| MOE-10 |"))
        assert "to co-define" in row04 and "to co-define" in row10
        # payload definition: frames acquired next to the products delivered
        frames = sum(p["data_volume_per_day_gb"] for p in load("mission")["requirements"]["payloads"]) \
            if "requirements" in load("mission") else None
        assert "GB/day" in text and "Frames acquired on board per day" in text, gate
        delivered = n["data_budget"]["science_target_mb_per_day_after_compression"]["value"]
        assert f"{delivered:g} MB/day" in text or f"{delivered:.1f} MB/day" in text, gate
        assert "Products selected per day, raw" in text
        _ = frames
    titles = {g: " ".join(md[g]["section_titles"]) for g in md}
    assert "Allocation ledger" in titles["srr"] and "Allocation ledger" in titles["pdr"]
    assert "Allocation ledger" not in titles["mdr"]
    assert "Negotiation records" in titles["pdr"] and "Validation plan" in titles["prr"]
    assert "Appendix: assumption register" in titles["pdr"]
    assert "Reliability analysis and FMEA" in titles["pdr"] and "Thermal model" in titles["pdr"]
    assert "Interface control documents: issue and sign-off" in titles["pdr"]
    assert "Systems-engineering figures" in titles["mdr"]
    pdr = md["pdr"]["document_markdown"]
    assert pdr.count("| N1 |") == 1 and "| N3 |" in pdr and "| N7 |" in pdr
    mass_sum = b["mass"]["closure"]["sum_allocations_kg"]
    assert f"Sum of the allocations: {mass_sum:g} kg" in pdr
    assert f"Sum of the allocations: {b['power']['closure']['sum_allocations_w']:g} W" in pdr
    for fig in ("Context diagram", "V diagram", "Budget flow-down", "N² chart"):
        assert fig in pdr, fig
    # the protocol deliverables: listed when agent S's service answers, else an open item for S
    dl = md["pdr"]["deliverables"]
    assert dl.get("items") or dl.get("owner") == "S"

    # the PDR zip: Diagrams.docx carries context, N², V and the flow-down; ledger sheet sums;
    # SEMP from the study; TS and VCD with acceptance, model and event
    r = await client.post(f"/api/exports/docs/{sid}?review=pdr&fmt=zip&crosscheck=false")
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    dg_txt = _docx_text(z.read("documents/Diagrams.docx"))
    for fig in ("Context diagram", "N² chart", "N² chart — functions", "V diagram", "Budget flow-down", "Trade matrix — "):
        assert fig in dg_txt, fig
    rows = _xlsx_sheet(z.read("budgets/master_budget.xlsx"), "Ledger")
    mass = sum(float(x[3]) for x in rows[1:] if x and x[0] == "Mass" and x[2] == "allocation" and x[3] is not None)
    power = sum(float(x[3]) for x in rows[1:] if x and x[0] == "Orbit-average power" and x[2] == "allocation"
                and x[3] is not None)
    assert mass == pytest.approx(mass_sum, abs=1e-6) and power == pytest.approx(b["power"]["closure"]["sum_allocations_w"],
                                                                                 abs=1e-6)
    perf = _xlsx_sheet(z.read("budgets/master_budget.xlsx"), "Performance")
    assert {x[0] for x in perf[1:] if x and x[0]} >= {"pointing", "registration", "timing"}
    data_sheet = "\n".join(" | ".join("" if v is None else str(v) for v in row)
                           for row in _xlsx_sheet(z.read("budgets/master_budget.xlsx"), "Data"))
    assert "Frames acquired" in data_sheet and "Products delivered per day" in data_sheet and "1103" not in data_sheet
    semp = _docx_text(z.read("documents/SEMP.docx"))
    for h in ("Organisation and seats", "Life cycle, reviews and baselines", "Technical processes",
              "Model philosophy and verification approach", "Risk management", "Configuration management", "Tailoring"):
        assert h in semp, h
    ts = _docx_text(z.read("documents/TS_technical_requirements.docx"))
    assert "Acceptance" in ts and "Event" in ts and "RV-CDR-LCH" in ts
    vcd = _docx_text(z.read("documents/VCD_verification_control.docx"))
    assert "Model" in vcd and "Event" in vcd
    idx = z.read("INDEX.md").decode()
    assert "Systems-engineering deliverables" in idx
    assert "documents/SEMP.docx" in names

    # the MRD carries the register, the MOEs and the need validation
    r = await client.post(f"/api/exports/docx/mrd?study_id={sid}")
    mrd = _docx_text(r.content)
    assert "Measures of Effectiveness" in mrd and "to co-define" in mrd and "Need Validation" in mrd
    assert all(x["id"] in mrd for x in sh["stakeholders"])


async def test_semp_from_the_study_in_french(client, monkeypatch):
    s = await _seeded(client, monkeypatch, "S3")
    r = await client.post(f"/api/exports/docx/semp?study_id={s.study_id}&lang=fr")
    assert r.status_code == 200
    txt = _docx_text(r.content)
    for h in ("Plan de management de l’ingénierie système", "Organisation et postes", "Cycle de vie, revues et références",
              "Processus techniques", "Gestion de configuration", "Adaptation", "Figures d’ingénierie système"):
        assert h in txt, h
    assert "Diagramme de contexte" in txt and "Diagramme en V" in txt
    sec = (await client.get(f"/api/studies/{s.study_id}/export-context?sections=semp")).json() \
        if False else None
    from spacecdf_server.services.export_context import collect
    sx = await collect(s.study_id, sections=["gates", "requirements", "semp"])
    assert sx.semp.get("status") != "not_implemented"
    assert {"organisation", "lifecycle", "processes", "tailoring", "configuration_management"} <= set(sx.semp)
    assert [g["short"] for g in sx.semp["lifecycle"]][:4] == ["MDR", "PRR", "SRR", "PDR"]
    assert any(g["gate"] == "srr" and g["baseline"]["en"] == "functional baseline" for g in sx.semp["lifecycle"])
    assert any(o["seat"] == "systems_engineer" for o in sx.semp["organisation"])
    _ = sec
