"""Closing step of wave 3 (plan 3.F1, 3.F2) on the Northern Fire and Ice study.

* **Round trip, 100 %** (3.F1): the finished study (the dry run's end state, with a team and the
  logbook) is exported, imported and exported again. Every row of every table comes back once ids
  are mapped, and every row of the frozen v1 checklist (``roundtrip_checklist.yaml``, not edited)
  plus every object wave 3 added is named here with the records that hold it, found non-empty and
  found equal. The checklist file is frozen baseline, so the mapping lives in this test: a new
  checklist row without a mapping fails the test.
* **Example project** (3.F2): ``configs/examples/nfi/project.json`` is listed in "Load Example
  Mission"; loading it and exporting it again gives the shipped file after id mapping.
* **Name gate** (W10.02): the exports generated from the example (every gate pack, every licensing
  document, the project file) and the repository's own text never contain the working name of the
  proposal the mission came from, nor its variants. The name is not written in this file.
"""
from __future__ import annotations

import base64
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

import pytest

from tests.fixtures.nfi import load
from tests.fixtures.nfi.example_project import EXAMPLE_PATH, finished_study

REPO = Path(__file__).resolve().parents[4]


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(tmp_path / "logbook"))
    monkeypatch.delenv("SPACECDF_INSTRUCTORS", raising=False)
    monkeypatch.delenv("SMO_INSTRUCTORS", raising=False)
    from spacecdf_server.routers import elements, stack
    from spacecdf_server.seats import store
    stack.reset_stack_cache()
    store.reset_memory()
    elements._budget_allocations.clear()
    yield
    stack.reset_stack_cache()
    store.reset_memory()
    elements._budget_allocations.clear()


async def _ok(r, codes=(200, 201)):
    assert r.status_code in codes, (r.request.url, r.status_code, r.text[:600])
    return r.json()


# ─── where each round-trip item lives in the project file ──────────────────────────────────
# ``t:<table>`` every row of a table; ``m:<path>`` a field of the study record (``studies``
# meta_json, dotted path); ``f:<key>`` a top-level key of the file. A source marked ``?`` may be
# empty in this study (the reason is given); every other source must hold data.

#: the v1 checklist (frozen): (area, tab) -> sources
CHECKLIST_SOURCES: dict[tuple[str, str], tuple[str, ...]] = {
    ("Study", "Wizard step 1"): ("m:name", "m:mission_need.problem_statement", "m:mission_need.operational_context",
                                 "m:requirements.mission_type"),
    ("Mission need", "Wizard step 2"): ("m:mission_need.stakeholders", "m:mission_need.objectives"),
    ("Mission need", "Wizard step 3"): ("m:mission_need.alternatives_considered",
                                        "m:mission_need.selected_alternative_id", "m:mission_need.selection_rationale"),
    ("Mission need", "Mission definition editor"): ("m:mission_need.conops_summary",),
    ("Mission requirements", "Mission definition editor"): ("m:requirements.orbit", "m:requirements.payloads",
                                                            "m:requirements.ground_stations", "m:requirements.link"),
    ("Seats", "Wizard step 4 / Seats drawer"): ("t:study_teams", "t:seat_events"),
    ("Product tree", "Blocks"): ("t:design_elements",),
    ("Elements", "Blocks inline"): ("t:design_elements",),
    ("Elements", "Properties: <name>"): ("t:design_elements",),
    ("Elements", "API"): ("t:design_elements",),
    ("Elements", "Blocks drag"): ("t:design_elements",),
    ("Modes", "Modes rows"): ("t:design_elements",),
    ("Modes", "Transitions"): ("t:mode_transitions",),
    ("Modes", "Matrix"): ("t:mode_elements",),
    # v2 allocations are the ledger's lines (3.A2); the legacy table is kept for older studies
    ("Budget", "Budget"): ("t:allocation_ledger", "?t:budget_allocations"),
    ("Requirements", "Requirements"): ("t:requirements",),
    ("Requirements", "link ↑ / flow ↓"): ("t:requirements", "t:requirement_relations"),
    ("Requirements", "API"): ("t:requirements",),
    ("Requirements", "auto (AUTO_IRD)"): ("t:requirements",),
    ("Functions", "Functions"): ("t:functions", "t:function_ports", "t:function_allocations", "t:functional_exchanges"),
    ("Interfaces", "Interfaces"): ("t:element_interfaces",),
    ("Electrical", "Electrical"): ("t:power_rails", "t:power_lines"),
    ("Data", "Data"): ("t:data_buses", "t:bus_nodes"),
    ("ICD", "ICD"): ("t:exchange_items",),
    ("TM/TC", "TM/TC"): ("t:cdr_rows",),
    ("FDIR", "FDIR"): ("t:cdr_rows",),
    ("AOCS modes", "AOCS modes"): ("t:cdr_rows",),
    ("Operations", "Operations"): ("t:cdr_rows",),
    ("Stack", "Spacecraft"): ("t:stack_layouts",),
    ("Trades", "Decide"): ("m:trade_records",),
    ("Options", "Analyses / API"): ("t:options",),
    ("Risks", "V&V Risk Register"): ("m:risk_register",),
    # gate_profile "" is the configured default (full ECSS); the passed gates are in gate_states
    ("Gates", "V&V Review Gates"): ("?m:gate_profile", "m:gate_states", "t:gate_baselines", "t:review_items"),
    ("V&V", "V&V Requirements / analyses"): ("t:verification_items",),
    ("Analyses", "Analyses"): ("t:analysis_runs", "f:files"),
    ("Parameters", "Blocks → Parameters & equations"): ("?t:element_parameters",),
    ("Ground stations", "Blocks (ground)"): ("t:design_elements", "m:requirements.ground_stations"),
    ("Link budget", "Analyses → Link budget"): ("t:link_budgets",),
    ("Logbook", "Logbook"): ("f:logbook",),
    ("UI state", "breadcrumb, level, panel"): (),     # per browser by design: the importer only remaps ``ui``
}

#: what wave 3 added (SE protocol, change control, negotiations, licensing, analyses, cost …)
NEW_OBJECTS: dict[str, tuple[str, ...]] = {
    "allocation ledger": ("t:allocation_ledger",),
    "stakeholders (interest, authority) and MOEs": ("m:mission_need.stakeholders", "t:se_moes"),
    "validation activities and need validation": ("t:se_validation_activities", "t:se_need_validation"),
    "assumption register": ("t:se_assumptions",),
    "change proposals and change control": ("t:change_proposals", "t:change_approvals"),
    "open items": ("t:open_items",),
    "negotiation records": ("t:negotiation_records",),
    "ICD issues and sign-offs": ("t:icd_issues",),
    "debris assessment": ("t:debris_assessments",),
    "reliability and FMEA": ("t:reliability_blocks", "t:fmea_rows"),
    "thermal nodal model": ("t:thermal_nodes", "t:thermal_couplings", "t:thermal_cases"),
    "cost pricing": ("t:cost_items",),
    "licensing record": ("t:licensing_records",),
    "AIT, schedule and settings": ("t:ait_models", "t:ait_tests", "t:project_settings", "t:schedule_milestones",
                                   "t:work_packages"),
    "SEMP issue": ("m:document_issues.semp",),
    "study margin policy": ("m:margin_policy",),
    "mission-success horizon": ("m:requirements.success_horizon_months",),
    "change baselines (approved ECP-02)": ("t:gate_baselines",),
}

_VOLATILE = {"inputs_hash"}


def _get(d, path: str):
    for k in path.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _canon(v) -> str:
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(y) for k, y in x.items() if k not in _VOLATILE}
        if isinstance(x, list):
            return [strip(y) for y in x]
        return x
    return json.dumps(strip(v), sort_keys=True, default=str)


def _source(doc: dict, src: str, ints: dict[str, set[str]]):
    kind, _, what = src.lstrip("?").partition(":")
    if kind == "t":
        rows = doc["tables"].get(what) or []
        return sorted(_canon({k: v for k, v in r.items() if k not in ints.get(what, set())}) for r in rows)
    if kind == "m":
        return _get(doc["tables"]["studies"][0]["meta_json"], what)
    if what == "logbook":       # an imported entry is a new entry of the importing person (new id, time)
        return sorted(_canon({k: e.get(k) for k in ("kind", "text", "context")}) for e in doc.get("logbook") or [])
    return doc.get(what)


def _mapped(doc: dict, id_map: dict) -> dict:
    from spacecdf_server.services.project_file import IdMap
    m = IdMap("", "")
    m.ids = dict(id_map)
    return {**doc, "tables": {n: [m.value(r) for r in rows] for n, rows in doc["tables"].items()},
            "files": m.value(doc.get("files") or {}), "logbook": [m.value(e) for e in doc.get("logbook") or []]}


def _empty(v) -> bool:
    return v is None or v == "" or v == [] or v == {}


async def _logbook(client, sid: str) -> int:
    """The decision records of the baseline (LB-01 …), written by this client tagged with the study."""
    n = 0
    for e in load("logbook")["entries"]:
        await _ok(await client.post("/api/logbook/entries", json={
            "kind": "decision", "text": f"{e['id']} {e['title']}: {e['text']}",
            "context": {"study_id": sid, "where": e["decision"], "seat": e["seat"]}}))
        n += 1
    return n


@pytest.mark.asyncio
async def test_round_trip_covers_the_v1_checklist_and_the_wave3_objects(client):
    from tests.test_api.test_project_file import _int_cols
    sid = await finished_study(client)
    # what the script adds that the seed does not: option B (script §3.6), the logbook, the team
    await _ok(await client.post(f"/api/studies/{sid}/options",
                                json={"name": "B: body-mounted + P31u + BP4", "description": "script §3.6"}))
    assert await _logbook(client, sid) >= 28
    await _ok(await client.post(f"/api/studies/{sid}/team/preset",
                                json={"team_size": "9", "optional": ["propulsion_engineer", "cost_engineer"]}))
    await _ok(await client.post(f"/api/studies/{sid}/team/claim", json={"seats": ["team_leader", "systems_engineer"]},
                                headers={"X-C2O-Name": "NFI Team leader", "X-C2O-Client": "nfi-close"}))

    a = (await client.get(f"/api/studies/{sid}/export")).json()
    res = await _ok(await client.post("/api/studies/import?include_id_map=1", json=a))
    assert not res["warnings"], res["warnings"]
    b = (await client.get(f"/api/studies/{res['id']}/export")).json()
    am, ints = _mapped(a, res["id_map"]), _int_cols()

    # 1. every row of every table, once ids are mapped
    assert set(a["tables"]) == set(b["tables"])
    for t in a["tables"]:
        assert _source(am, f"t:{t}", ints) == _source(b, f"t:{t}", ints), f"table {t} differs after the round trip"
    assert len(b["files"]) == len(a["files"]) and len(b["logbook"]) == len(a["logbook"])

    # 2. the v1 checklist, row by row (frozen file; the mapping is above)
    rows = load("roundtrip_checklist")["checklist"]
    unmapped = [(r["area"], r["tab"]) for r in rows if (r["area"], r["tab"]) not in CHECKLIST_SOURCES]
    assert not unmapped, f"checklist rows with no round-trip source: {unmapped}"
    empty: list[str] = []
    for label, sources in [((r["area"], r["tab"]), CHECKLIST_SOURCES[(r["area"], r["tab"])]) for r in rows] + \
            list(NEW_OBJECTS.items()):
        for src in sources:
            va, vb = _source(am, src, ints), _source(b, src, ints)
            if not src.startswith("?") and _empty(va):
                empty.append(f"{label}: {src}")
            assert _canon(va) == _canon(vb), f"{label}: {src} differs after the round trip"
    assert not empty, f"empty in the finished study: {empty}"
    # 3. the objects carry what the walkthrough did
    meta = b["tables"]["studies"][0]["meta_json"]
    assert meta["document_issues"]["semp"]["issue"] == "A"
    assert {g: meta["gate_states"][g]["state"] for g in ("mdr", "prr", "srr", "pdr")} == dict.fromkeys(
        ("mdr", "prr", "srr", "pdr"), "passed")
    status = {r["code"]: r["status"] for r in b["tables"]["change_proposals"]}
    assert status["ECP-02"] == "accepted" and status["ECP-01"] == "rejected"
    assert {r["status"] for r in b["tables"]["negotiation_records"]} == {"agreed"}
    assert len(b["tables"]["study_teams"]) == 1


# ─── example project ───────────────────────────────────────────────────────────────────────

def _shipped() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_example_project_is_listed_and_reloads_to_the_shipped_file(client):
    from tests.test_api.test_project_file import _int_cols
    shipped = _shipped()
    assert shipped["format"] == "spacecdf-project" and shipped["version"] == 2
    assert shipped["study"]["name"] == "Northern Fire and Ice"
    assert shipped["tables"]["licensing_records"], "the example carries the licensing record"
    listed = {m["id"]: m for m in (await _ok(await client.get("/api/lifecycle/example-missions")))["missions"]}
    assert listed["nfi"]["kind"] == "project" and "Northern Fire and Ice" in listed["nfi"]["name"]
    assert "superdove_3u_eo" not in listed and "generic_3u_eo" in listed

    res = await _ok(await client.post("/api/lifecycle/example-missions/nfi/load?include_id_map=1"))
    assert res["kind"] == "project" and not res["warnings"], res["warnings"]
    again = (await client.get(f"/api/studies/{res['id']}/export")).json()
    m, ints = _mapped(shipped, res["id_map"]), _int_cols()
    # the shipped file is the reference: every table, row and column it holds comes back (columns a
    # newer server adds to the schema are not in the old file and are not compared)
    for t, rows in m["tables"].items():
        cols = set().union(*(r.keys() for r in rows)) if rows else set()
        back = [{k: v for k, v in r.items() if k in cols} for r in again["tables"].get(t, [])]
        assert _source({"tables": {t: rows}}, f"t:{t}", ints) == _source({"tables": {t: back}}, f"t:{t}", ints), \
            f"table {t}: the reloaded example differs from the shipped file"
    assert len(again["files"]) == len(shipped["files"])
    gates = (await _ok(await client.get(f"/api/studies/{res['id']}/gates")))["gates"]
    assert {g["id"]: g["state"] for g in gates if g["id"] in ("mdr", "prr", "srr", "pdr")} == dict.fromkeys(
        ("mdr", "prr", "srr", "pdr"), "passed")
    # the SE-deliverables criterion reads the protocol evidence (the dry run found it never
    # evaluated: gate_inputs overwrote the gates it collects the evidence for)
    for g in ("mdr", "pdr"):
        ev = await _ok(await client.get(f"/api/studies/{res['id']}/rules/gates/{g}"))
        se = next(c for c in ev["criteria"] if c["id"] == f"{g.upper()}-SE-01")
        assert se["status"] in ("pass", "fail") and "deliverables of the gate" in str(se.get("evidence_found")), se


# ─── name gate ─────────────────────────────────────────────────────────────────────────────

#: the proposal's working name, kept out of this file's text (base64 of the lower-case word)
_WORD = base64.b64decode(b"ZmxhcmU=").decode()
#: the word on its own, in any case, alone or in compounds (``_DESIGN_SCRIPT``, ``-TB-1``,
#: ``seed_…``, ``…SAT``); not inside a longer word ("Cloudflare", "flared")
NAME = re.compile(rf"(?<![a-z]){_WORD}(?:sat|cube)?(?![a-z])", re.IGNORECASE)


def _texts(name: str, data: bytes) -> list[tuple[str, str]]:
    """The text of an exported file: Office files and zips are opened, everything else is read as
    UTF-8 (binary noise cannot spell the word by accident in a way that matters)."""
    if data[:2] == b"PK":
        out = []
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for n in z.namelist():
                out += _texts(f"{name}/{n}", z.read(n))
        return out
    return [(name, data.decode("utf-8", "replace"))]


def _hits(texts: list[tuple[str, str]]) -> list[str]:
    return [f"{n}: …{t[max(0, m.start() - 30):m.end() + 30]}…" for n, t in texts for m in [NAME.search(t)] if m]


def test_the_name_pattern_finds_the_word_and_its_variants_only():
    w = _WORD
    for s in (w.upper(), w.title(), f"{w.upper()}_DESIGN_SCRIPT", f"seed_{w}", f"{w.upper()}-TB-1",
              f"V-{w.upper()}-", f"{w}sat", f"fig_{w}_stack"):
        assert NAME.search(s), s
    for s in (f"Cloud{w}", f"cloud{w}d", f"{w}d waveguide", "Flame", "Northern Fire and Ice"):
        assert not NAME.search(s), s


@pytest.mark.asyncio
async def test_name_gate_over_the_generated_exports(client):
    from spacecdf_server.services.licensing_docs import KINDS
    res = await _ok(await client.post("/api/lifecycle/example-missions/nfi/load"))
    sid = res["id"]
    texts: list[tuple[str, str]] = []
    r = await client.get(f"/api/studies/{sid}/export")
    texts += _texts("project.json", r.content)
    gates = [g["id"] for g in (await _ok(await client.get(f"/api/studies/{sid}/gates")))["gates"]]
    assert {"mdr", "prr", "srr", "pdr"} <= set(gates)
    for g in gates:
        for lang in ("en", "fr"):
            r = await client.post(f"/api/exports/docs/{sid}?review={g}&fmt=zip&lang={lang}&crosscheck=false")
            assert r.status_code == 200, (g, r.text[:300])
            texts += _texts(f"pack_{g}_{lang}.zip", r.content)
    for kind in KINDS:
        for fmt in ("json", "docx"):
            r = await client.post(f"/api/exports/regulatory/{kind}/{sid}?fmt={fmt}")
            assert r.status_code == 200, (kind, fmt, r.text[:300])
            texts += _texts(f"{kind}.{fmt}", r.content)
    assert len(texts) > 50
    assert any("Northern Fire and Ice" in t for _, t in texts)
    hits = _hits(texts)
    assert not hits, hits[:5]


def _repo_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True, timeout=60).stdout
        return [REPO / p for p in out.decode().split("\0") if p]
    except (OSError, subprocess.SubprocessError):
        skip = {"node_modules", ".venv", "dist", ".git", "__pycache__"}
        return [p for p in (REPO / "design").rglob("*") if p.is_file() and not skip & set(p.parts)]


def test_name_gate_over_the_repository():
    """No tracked file carries the name, in its path or its text (binary files are skipped)."""
    hits = []
    for p in _repo_files():
        rel = str(p.relative_to(REPO))
        if NAME.search(rel):
            hits.append(rel)
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:4096] or data[:2] == b"PK":
            continue
        hits += _hits([(rel, data.decode("utf-8", "replace"))])
    assert not hits, hits[:5]
