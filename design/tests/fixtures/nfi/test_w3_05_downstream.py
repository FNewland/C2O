"""W3.05 acceptance on the Northern Fire and Ice fixture (agent H, wave 2): the downstream use of
the data budget.

* the ``data_budget`` and ``contacts`` export sections have the shape the packs, the master budget
  and the ConOps read (``cases: [{capacity, demand, margin_pct}]``, ``union: {min_per_day,
  longest_gap_h}``);
* the Modes data chain, the Data budget page, the ground-segment analysis, the contact table and
  the TM/TC database export quote the same numbers (HK rates, union contact minutes, capacity);
* the day in the life follows the per-pass plan; the ``ops_pass`` diagram is a real OPS pass with
  its VC0/VC1/VC2 split;
* PDR-EC-06 and CDR-EC-04 ask "daily budget closes with margin, stores hold N days" and pass at C2;
* the Modes panel mounts the ConOps phases and shows the daily closure (static UI smoke check).

Expected numbers come from NUMBERS.yaml or from the data budget itself, never retyped.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.fixtures.nfi import load, seed_nfi

N = load("NUMBERS")
GN = N["ground_network"]
DB = N["data_budget"]
FRONT = Path(__file__).resolve().parents[3] / "frontend" / "src"


async def test_w305_downstream_agree_on_s4(client):
    s = await seed_nfi(client, "S4")
    sid = s.study_id
    b = (await client.get(f"/api/studies/{sid}/data-budget")).json()

    # ── export sections: the shape the packs read
    ex = (await client.get(f"/api/studies/{sid}/export-context?sections=data_budget,contacts")).json()
    xdb, xc = ex["data_budget"], ex["contacts"]
    cases = {c["id"]: c for c in xdb["cases"]}
    for c in xdb["cases"]:
        assert {"capacity", "demand", "margin_pct", "rt_hk", "stored_hk", "science", "other", "status"} <= set(c)
        assert isinstance(c["label"], str) and c["label"]
    nc = DB["cases"]
    assert cases["C1"]["capacity"] == pytest.approx(nc["C1_per_pass_profiles_BASELINE"]["capacity"], abs=0.3)
    assert cases["C1"]["margin_pct"] == pytest.approx(nc["C1_per_pass_profiles_BASELINE"]["margin_pct"], abs=1.0)
    assert cases["C2"]["demand"] == pytest.approx(nc["C2_C1_plus_adcs_diag_campaign"]["demand"], abs=0.2)
    daily = xdb["daily"]
    assert daily["closure"]["id"] == daily["closure_case"] == "C1"
    assert daily["capacity_mb_per_day"] == b["capacity"]["capacity_mb_per_day"]
    assert daily["union_min_per_day"] == b["capacity"]["union_min_per_day"]
    assert all(not isinstance(v, (dict, list)) for k, v in daily.items() if k != "closure")
    u = xc["union"]
    assert u["min_per_day"] == pytest.approx(GN["union_min_per_day"]["value"], abs=0.5)
    assert u["longest_gap_h"] == pytest.approx(GN["longest_gap_h"]["value"], abs=0.5)
    assert u["passes_per_day"] == u["windows_per_day"] and u["max_pass_min"] == u["max_window_min"]
    for st in xc["stations"]:
        assert {"name", "min_per_day", "passes_per_day", "mean_pass_min", "max_pass_min"} <= set(st)

    # ── one set of numbers: data budget = data chain = ground analysis = contact table = TM/TC export
    union = b["capacity"]["union_min_per_day"]
    dc = (await client.get(f"/api/studies/{sid}/modes/data-chain")).json()
    run = (await client.post(f"/api/studies/{sid}/analyses/ground_segment/run")).json()["summary"]
    assert dc["downlink"]["contact_min_per_day"] == pytest.approx(union, abs=0.05)
    assert run["union"]["min_per_day"] == pytest.approx(union, abs=0.05)
    assert u["min_per_day"] == pytest.approx(union, abs=0.1)          # contact table: 5 s step, budget 10 s
    assert dc["housekeeping"]["stored_mb_per_day"] == run["housekeeping"]["stored_mb_per_day"] == b["stored"]["mb_per_day"]
    assert dc["data_budget"]["closure"] == b["closure"]
    assert dc["downlink"]["usable_min_per_day"] == pytest.approx(b["capacity"]["usable_min_per_day"], abs=0.05)
    assert run["housekeeping"]["capacity_mb_per_day"] == pytest.approx(b["capacity"]["capacity_mb_per_day"], abs=0.05)
    # the data chain shows the capacity left after the real-time HK of the passes (GB, 3 decimals)
    assert dc["downlink"]["capacity_gb_per_day"] * 1000 == pytest.approx(
        b["capacity"]["capacity_mb_per_day"] - dc["housekeeping"]["realtime_mb_per_day"], abs=0.6)
    tm = (await client.get(f"/api/studies/{sid}/cdr/export/tmtc.json")).json()
    names = {m["id"]: m["name"] for m in b["modes"]}
    by_sid = {x["sid"]: x for x in b["sids"]}
    for row in tm["sids"]:
        if row["copy"] != "real-time":
            continue
        ref = by_sid[row["sid"]]
        assert row["packet_bytes"] == ref["bytes"], row["sid"]
        for mid, iv in ref["rt_interval_by_mode"].items():
            got = row.get(f"interval_s[{names[mid]}]")
            assert (got in ("-", None, "")) if iv is None else got == pytest.approx(iv), (row["sid"], names[mid])

    # ── day in the life: steady state, the delayed-HK dumps carry one day of stored HK
    dil = b["day_in_the_life"]
    assert sum(w["delayed_hk_mb"] for w in dil["windows"]) == pytest.approx(b["stored"]["mb_per_day"], abs=0.15)
    assert dil["totals"]["minutes"] == pytest.approx(GN["representative_day"]["union_min"], abs=3)
    ops = [w for w in dil["windows"] if w["class"] == "OPS"]
    assert len(ops) == 2 and all(w["first_vc"] == "VC1" and w["payload_mb"] > 0 for w in ops)

    # ── the ops_pass diagram is the first real OPS pass, with its VC0/VC1/VC2 bars
    from spacecdf_server.services.data_budget import ops_pass
    op = ops_pass(b)
    assert op["class"] == "OPS" and op["index"] == ops[0]["index"] and op["minutes"] == ops[0]["minutes"]
    assert sum(v["mb"] for v in op["vcs"]) + op["idle_mb"] == pytest.approx(op["channel_mb"], abs=0.02)
    assert xdb["ops_pass"]["index"] == op["index"]
    dg = (await client.get(f"/api/studies/{sid}/diagrams/ops_pass")).json()
    bars = [c for c in dg["cells"] if str(c.get("title", "")).startswith(("VC0", "VC1", "VC2"))]
    assert [c["title"][:3] for c in bars] == ["VC0", "VC1", "VC2"]
    caption = next(lb["text"] for lb in dg["labels"] if isinstance(lb.get("text"), dict) and "{{cls}}" in lb["text"]["t"])
    assert caption["p"]["min"] == f"{op['minutes']:.1f}" and caption["p"]["cls"] == "OPS"
    assert not any(g["code"] == "no_rate" for g in dg["gaps"])
    steps = [n["label"]["t"] for n in dg["nodes"]]
    assert steps.index("VC1 delayed HK dump: {{mb}} MB") < steps.index("VC2 payload files: {{mb}} MB")

    # ── the ConOps data-flow section (D's hook) quotes the same closure and cases
    cv = (await client.get(f"/api/studies/{sid}/conops")).json()["data_flow"]
    assert cv["status"] == "ready" and cv["daily"]["margin_pct"] == b["closure"]["margin_pct"]
    assert [c["id"] for c in cv["cases"]] == [c["id"] for c in b["cases"]]

    # ── the per-pass plan is reflected in the day in the life (and in the ops_pass diagram)
    first_ops, other = ops[0]["index"], next(w["index"] for w in dil["windows"] if w["class"] == "DUMP")
    r = await client.post(f"/api/studies/{sid}/cdr/pass_plan",
                          json={"data": {"overrides": {str(first_ops): {"first": "VC2"}, str(other): {"class": "OPS"}}}})
    assert r.status_code in (200, 201), r.text
    b2 = (await client.get(f"/api/studies/{sid}/data-budget")).json()
    w2 = {w["index"]: w for w in b2["day_in_the_life"]["windows"]}
    assert w2[first_ops]["first_vc"] == "VC2" and w2[first_ops]["override"]
    assert w2[first_ops]["payload_mb"] > ops[0]["payload_mb"]
    assert w2[other]["class"] == "OPS" and w2[other]["rt_profile"] == "FULL"
    assert w2[other]["rt_hk_mb"] > w2[other]["usable_min"] * 60 * 4000 / 8e6     # FULL profile, not LEAN
    op2 = ops_pass(b2)
    assert op2["index"] == min(first_ops, other) and op2["order"][:2] == ["VC0", w2[op2["index"]]["first_vc"]]

    # ── the gate question: PDR-EC-06 and CDR-EC-04 pass at C2 with the stores holding 7 days
    pdr = (await client.get(f"/api/studies/{sid}/rules/gates/pdr")).json()
    c6 = next(c for c in pdr["criteria"] if c["id"] == "PDR-EC-06")
    assert c6["status"] == "pass", c6
    p = c6["evidence_params"]
    assert p["case"] == "C2" and float(p["margin"]) == pytest.approx(cases["C2"]["margin_pct"], abs=0.1)
    assert float(p["days"]) >= float(p["need"]) == 7
    cdr = (await client.get(f"/api/studies/{sid}/rules/gates/cdr")).json()
    c4 = next(c for c in cdr["criteria"] if c["id"] == "CDR-EC-04")
    assert c4["evidence_params"].get("case") == "C2" and "daily budget" in c4["evidence_found"]

    # ── the master budget workbook and the study pack read the section shape
    from spacecdf_agents.exporters.docs.master_budget import generate_master_budget
    from spacecdf_server.services.export_context import collect
    sx = (await collect(sid, gate="pdr", sections=["mission", "data_budget", "contacts"])).as_dict()
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(generate_master_budget(sx)))
    rows = list(wb["Data"].iter_rows(values_only=True))
    head = rows[0]
    c2 = next(r for r in rows if r[0] == "C2")
    assert c2[head.index("margin_pct")] == cases["C2"]["margin_pct"] and c2[head.index("capacity")] == cases["C2"]["capacity"]
    assert sx["data_budget"]["gate_check"]["ok"] is True and sx["data_budget"]["gate_check"]["required_percent"] == 10


def test_w305_modes_panel_mounts_conops_phases_and_daily_closure():
    """UI smoke check without a browser: the Modes panel mounts the ConOps phases (D's hand-off)
    and the data chain shows the data budget's closure case; every new text has a French entry."""
    import json
    src = (FRONT / "modes" / "ModesPanel.tsx").read_text(encoding="utf-8")
    assert "import { ConopsPhases } from '../workbench/ConopsPhases'" in src
    assert re.search(r"view === 'machine' && <ConopsPhases studyId=\{sid\} />", src)
    assert "<DailyClosure c={data.data_budget.closure} />" in src
    api = (FRONT / "modes" / "api.ts").read_text(encoding="utf-8")
    assert "data_budget?: { status: string; closure: DailyCase | null } | null" in api
    fr = json.loads((FRONT / "i18n" / "locales" / "fr.u_hk.json").read_text(encoding="utf-8"))
    body = src[src.index("function DailyClosure"):]
    body = body[: body.index("\n}\n")]
    keys = re.findall(r"t\('((?:[^'\\]|\\.)*)'", body)
    assert len(keys) == 2 and all(k in fr for k in keys), keys
