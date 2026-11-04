"""SEMP / ECSS diagram models (design rules §3; routers/diagrams.py, services/diagrams/).

Every diagram endpoint returns a model with geometry, provenance per item, a gaps list and
a table alternative; the catalogue says which gates expect each diagram; the SVG / PNG and
the docx exports draw the same models; every translatable key is in vocab.ts."""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pytest

from tests.test_api.diagram_seed import seed_eosat

KINDS = ["phases", "modes", "ops_pass", "product_tree", "function_tree", "allocation", "block", "n2", "power",
         "switch_matrix", "data_bus", "rf", "thermal", "stack", "ground", "req_tree", "vcd", "risk"]

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SPACECDF_AUTO_IRD", "1")
    from spacecdf_server.routers import stack
    stack.reset_stack_cache()
    yield
    stack.reset_stack_cache()


@pytest.fixture()
async def eosat(client, study_obj, study):
    parts = await seed_eosat(client, study)
    return study, parts


def _texts(v) -> list[str]:
    """Every translatable key in a model (recursively)."""
    out = []
    if isinstance(v, dict):
        if "t" in v and isinstance(v["t"], str) and set(v) <= {"t", "p"}:
            out.append(v["t"])
        for x in v.values():
            out += _texts(x)
    elif isinstance(v, list):
        for x in v:
            out += _texts(x)
    return out


def _check_structure(m: dict) -> None:
    for k in ("kind", "title", "view", "width", "height", "nodes", "edges", "groups", "labels", "cells", "legend",
              "gaps", "completeness", "table", "gates", "product"):
        assert k in m, k
    assert m["width"] > 0 and m["height"] > 0
    ids = {n["id"] for n in m["nodes"]} | {g["id"] for g in m["groups"]}
    for n in m["nodes"]:
        assert {"x", "y", "w", "h", "prov"} <= set(n) and n["prov"]["source"], n
        assert n["x"] >= 0 and n["y"] >= 0 and n["x"] + n["w"] <= m["width"] and n["y"] + n["h"] <= m["height"], n["id"]
    for e in m["edges"]:
        assert e["from"] in ids and e["to"] in ids, e
        assert len(e["points"]) >= 2 and e["prov"]["source"]
    for g in m["gaps"]:
        assert {"code", "message", "count", "severity"} <= set(g)
    assert set(m["completeness"]) == {"expected", "filled", "score"}


async def test_every_diagram_model_on_the_eosat_study(client, eosat):
    sid, parts = eosat
    for kind in KINDS:
        r = await client.get(f"/api/studies/{sid}/diagrams/{kind}")
        assert r.status_code == 200, (kind, r.text[:300])
        m = r.json()
        assert m["kind"] == kind and m["empty"] is None, (kind, m["empty"], m["gaps"])
        _check_structure(m)
        assert m["table"]["columns"] and m["table"]["rows"], kind
        assert not [g for g in m["gaps"] if g["code"] == "error"], (kind, m["gaps"])


async def test_block_diagram_shows_cross_subsystem_links_with_provenance(client, eosat):
    sid, parts = eosat
    m = (await client.get(f"/api/studies/{sid}/diagrams/block")).json()
    groups = {g["id"] for g in m["groups"]}
    node_group = {n["id"]: n.get("group") for n in m["nodes"]}
    cross = [e for e in m["edges"] if node_group.get(e["from"]) and node_group.get(e["to"])
             and node_group[e["from"]] != node_group[e["to"]]]
    assert len(groups) >= 6 and cross, "unit-to-unit links across subsystems must be drawn"
    assert all(e["prov"]["source"] == "interface" and e["prov"]["ref"] for e in cross)
    eps_to_wheel = [e for e in m["edges"] if e["from"] == parts["EPS"]["id"] and e["to"] == parts["Reaction wheel"]["id"]
                    and e["type"] == "power"]
    assert eps_to_wheel and eps_to_wheel[0]["dash"] == "" and eps_to_wheel[0]["width"] > 2
    assert {x["type"] for x in m["legend"] if x.get("type")} >= {"power", "data"}
    # routed orthogonally: no diagonal segments
    for e in m["edges"]:
        for (x0, y0), (x1, y1) in zip(e["points"], e["points"][1:]):
            assert abs(x0 - x1) < 0.2 or abs(y0 - y1) < 0.2
    sysm = (await client.get(f"/api/studies/{sid}/diagrams/block?level=system")).json()
    assert {n["id"] for n in sysm["nodes"]} >= {parts["sub:power"]["id"], parts["sub:obc"]["id"]}
    foc = (await client.get(f"/api/studies/{sid}/diagrams/block?focus={parts['sub:aocs']['id']}")).json()
    assert parts["Star tracker"]["id"] in {n["id"] for n in foc["nodes"]}
    assert parts["Imager"]["id"] not in {n["id"] for n in foc["nodes"]} or any(
        parts["Imager"]["id"] in (e["from"], e["to"]) for e in foc["edges"])


async def test_power_and_data_diagrams_follow_the_electrical_model(client, eosat):
    sid, parts = eosat
    elec = (await client.get(f"/api/studies/{sid}/electrical")).json()
    p = (await client.get(f"/api/studies/{sid}/diagrams/power")).json()
    rail_nodes = [n for n in p["nodes"] if n["prov"]["source"] == "rail"]
    line_nodes = [n for n in p["nodes"] if n["prov"]["source"] == "line"]
    assert len(rail_nodes) == len(elec["rails"]) and len(line_nodes) == len(elec["lines"])
    assert any("28.8" in str(n["label"]) for n in rail_nodes)
    assert all(any(str(b).startswith("LCL") for b in n["badges"]) for n in line_nodes)
    assert parts["Solar wings"]["id"] in {n["id"] for n in p["nodes"]}
    b = (await client.get(f"/api/studies/{sid}/diagrams/data_bus")).json()
    trunks = [n for n in b["nodes"] if n["shape"] == "trunk"]
    assert len(trunks) == len(elec["buses"]) and trunks
    bus_nodes = [n for n in b["nodes"] if n["prov"]["source"] == "node"]
    assert len(bus_nodes) == len(elec["nodes"])
    with_addr = [n for n in elec["nodes"] if n.get("address") is not None]
    assert sum(1 for n in bus_nodes if str(n["badges"][0]).startswith("0x")) == len(with_addr)
    sm = (await client.get(f"/api/studies/{sid}/diagrams/switch_matrix")).json()
    modes = (await client.get(f"/api/studies/{sid}/modes")).json()["modes"]
    assert len(sm["table"]["columns"]) == 2 + len(modes)
    assert any(c.get("text", "").startswith("ON") for c in sm["cells"]) and any(c.get("text") == "off" for c in sm["cells"])


async def test_gaps_name_what_is_missing(client, eosat):
    sid, parts = eosat
    # remove two bus addresses: the data diagram says so
    nodes = [n for n in (await client.get(f"/api/studies/{sid}/electrical")).json()["nodes"] if n.get("address") is not None]
    for n in nodes[:2]:
        r = await client.patch(f"/api/studies/{sid}/electrical/nodes/{n['id']}", json={"address": None})
        assert r.status_code == 200, r.text
    b = (await client.get(f"/api/studies/{sid}/diagrams/data_bus")).json()
    g = next(g for g in b["gaps"] if g["code"] == "addresses")
    assert g["count"] >= 2 and g["message"]["t"] == "missing: bus addresses for {{n}} units" and g["fix"] == "data"
    # a unit with no interface at all
    await client.post(f"/api/elements/?study_id={sid}", json={"name": "Spare sensor", "element_type": "component",
                                                               "parent_id": parts["sub:aocs"]["id"], "subsystem_domain": "aocs"})
    blk = (await client.get(f"/api/studies/{sid}/diagrams/block")).json()
    assert any(g["code"] == "isolated_units" and "Spare sensor" in g["message"]["p"]["names"] for g in blk["gaps"])


async def test_empty_study_gives_empty_models_with_gaps(client, study_obj, study):
    for kind in KINDS:
        r = await client.get(f"/api/studies/{study}/diagrams/{kind}")
        assert r.status_code == 200, (kind, r.text[:200])
        m = r.json()
        _check_structure(m)
        assert m["gaps"], kind
    assert (await client.get(f"/api/studies/{study}/diagrams/nope")).status_code == 404
    assert (await client.get("/api/studies/does-not-exist/diagrams/block")).status_code == 404


async def test_catalogue_lists_gates_and_filters_by_gate(client, eosat):
    sid, _ = eosat
    cat = (await client.get(f"/api/studies/{sid}/diagrams")).json()
    kinds = {d["kind"] for d in cat["diagrams"]}
    assert set(KINDS) <= kinds and "budgets" in kinds
    blk = next(d for d in cat["diagrams"] if d["kind"] == "block")
    assert {"gate": "pdr", "maturity": "B"} in blk["gates"] and blk["product"] == "design_files"
    assert isinstance(blk["gaps"], int) and blk["completeness"]["expected"] > 0
    mdr = (await client.get(f"/api/studies/{sid}/diagrams?gate=mdr")).json()
    assert {d["kind"] for d in mdr["diagrams"]} == {"phases", "modes", "risk"}
    pdr = {d["kind"] for d in (await client.get(f"/api/studies/{sid}/diagrams?gate=pdr")).json()["diagrams"]}
    assert {"power", "data_bus", "stack", "block", "modes"} <= pdr and "phases" not in pdr


async def test_svg_png_and_french_labels(client, eosat):
    sid, _ = eosat
    for kind in ("block", "power", "modes", "n2", "stack", "phases"):
        r = await client.get(f"/api/studies/{sid}/diagrams/{kind}/svg")
        assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")
        assert r.text.startswith("<svg") and "</svg>" in r.text
    en = (await client.get(f"/api/studies/{sid}/diagrams/power/svg")).text
    fr = (await client.get(f"/api/studies/{sid}/diagrams/power/svg?lang=fr")).text
    assert "Switched lines" in en and "Lignes commutées" in fr and "Switched lines" not in fr
    png = (await client.get(f"/api/studies/{sid}/diagrams/block/png")).content
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 5000


async def test_exports_embed_the_same_diagrams(client, eosat):
    sid, _ = eosat

    def images(docx: bytes) -> list[str]:
        z = zipfile.ZipFile(io.BytesIO(docx))
        return [n for n in z.namelist() if n.startswith("word/media/")]

    def text(docx: bytes) -> str:
        z = zipfile.ZipFile(io.BytesIO(docx))
        return z.read("word/document.xml").decode("utf8")
    semp = await client.post(f"/api/exports/docx/semp?study_id={sid}")
    assert semp.status_code == 200
    assert len(images(semp.content)) >= 10
    assert "Mode state diagram" in text(semp.content) and "Product tree" in text(semp.content)
    ird = await client.post(f"/api/exports/docx/ird?study_id={sid}")
    assert ird.status_code == 200 and len(images(ird.content)) >= 5
    assert "Electrical power block diagram" in text(ird.content) and "N² chart" in text(ird.content)
    doc = await client.get(f"/api/studies/{sid}/diagrams-document.docx?set=all")
    assert doc.status_code == 200 and len(images(doc.content)) == len(KINDS)
    assert "missing:" in text(doc.content)          # the gaps travel with the figures


def test_vocab_ts_lists_every_server_key():
    """Every T("…") key in services/diagrams is in frontend/src/diagrams/vocab.ts (FR catalog check)."""
    src = ROOT / "packages/spacecdf-server/src/spacecdf_server/services/diagrams"
    keys: set[str] = set()
    for p in src.glob("*.py"):
        text = p.read_text("utf8")
        keys |= set(re.findall(r'\bT\(\s*"((?:[^"\\]|\\.)*)"', text))
        keys |= set(re.findall(r'\{"t":\s*"((?:[^"\\]|\\.)*)"', text))
        # tables marked "English text is the key"
        for block in re.findall(r"# English text is the key[^\n]*\n([A-Z_]+ = \{[^}]*\})", text):
            keys |= set(re.findall(r':\s*"((?:[^"\\]|\\.)*)"', block))
    vocab = (ROOT / "frontend/src/diagrams/vocab.ts").read_text("utf8")
    listed = set(re.findall(r"^\s*'((?:[^'\\]|\\.)*)',?$", vocab, re.M))
    listed = {k.replace("\\'", "'") for k in listed}
    assert keys - listed == set(), sorted(keys - listed)
