"""Test support for agent X's wave-3 work (3.X1–3.X3): the wave-3 export sections built from the
v2 baseline files, and the v2 function tree written straight into the store.

In wave 3 the owners fill these sections (S stakeholders/validation/assumptions, A allocations/
reliability/thermal/cost, H negotiations, L changes/debris, D open items/change control, R ICDs).
Until they merge, X's tests register collectors that return the same records **from the
baseline files** (``register_sections``), in the item shapes the generators read (documented in
``services/diagrams/b_se.py`` and ``exporters/docs/study_pack.py``: the table columns, without
``_json``). After the merge the real collectors replace them; the tests that use the real
sections are the owners'.
"""
from __future__ import annotations

from typing import Any

from tests.fixtures.nfi import load
from tests.fixtures.nfi.seed import ELEMENT_IDS

# ─────────────────────────────────────────────────────────────── sections from the baseline


def stakeholders_section() -> dict:
    s = load("stakeholders")
    items = [{"id": x["id"], "code": x["id"], "name": x["name"], "category": x.get("category", ""), "role": x.get("role", ""),
              "authority": x.get("authority", ""), "engagement": x.get("engagement", ""), "needs": x.get("needs") or []}
             for x in s["stakeholders"]]
    needs = [{"id": n["id"], "code": n["id"], "need": n.get("need", ""), "stakeholder": n.get("stakeholder", "")}
             for n in s["needs"]]
    moes = []
    for m in s["moes"]:
        ph = "co-defin" in str(m.get("defined_by", "")).lower() or "placeholder" in str(m).lower()
        moes.append({"id": m["id"], "code": m["id"], "name": m.get("measure", ""), "measure": m.get("measure", ""),
                     "threshold": str(m.get("threshold", "")), "objectives": m.get("objectives") or [],
                     "needs": m.get("needs") or [], "defined_by": str(m.get("defined_by", "")), "placeholder": ph})
    cats = sorted({i["category"] for i in items})
    return {"items": items, "needs": needs, "moes": moes,
            "counts": {"stakeholders": len(items), "categories": len(cats), "needs": len(needs), "moes": len(moes),
                       "placeholders": sum(1 for m in moes if m["placeholder"])}}


def validation_section() -> dict:
    vv = load("vv_plan")
    items = [{"code": v["id"], "title": v.get("name", ""), "stage": str(v.get("when", "")), "performer": v.get("who", ""),
              "method": v.get("method", ""), "acceptance": v.get("exit", ""), "requirement_codes": v.get("requirements") or [],
              "status": "planned"} for v in vv["validation_plan"]]
    nv = [{"need_code": n.get("need"), "activity_codes": [w for w in str(n.get("method", "")).split() if w[:1] == "V"
                                                         and w[1:].isdigit()],
           "method": n.get("method", ""), "stage": n.get("stage", ""), "status": "planned"}
          for n in load("stakeholders")["need_validation"]]
    return {"items": items, "need_validation": nv, "coverage": {"needs": len(nv), "covered": len(nv)},
            "counts": {"activities": len(items), "needs": len(nv)}}


def allocations_section() -> dict:
    b = load("budgets")
    items = []
    for code, x in b["mass"]["subsystems"].items():
        items.append({"element_code": code, "budget_type": "mass", "line_kind": "allocation", "value": x["allocation_kg"],
                      "unit": "kg", "cbe": x["cbe_kg"], "margined": x["margined_kg"], "requirement_code": x.get("requirement", ""),
                      "owner_seat": x.get("owner_seat", ""), "status": "agreed"})
    for code, x in b["power"]["subsystems"].items():
        if x.get("allocation_w") is None:
            continue
        items.append({"element_code": code, "budget_type": "power_avg", "line_kind": "allocation", "value": x["allocation_w"],
                      "unit": "W", "cbe": x.get("orbit_average_w"), "margined": x.get("margined_w"),
                      "requirement_code": x.get("requirement", ""), "owner_seat": x.get("owner_seat", ""), "status": "agreed"})
    for code, x in b["data"]["allocations"].items():
        items.append({"element_code": code, "budget_type": "data", "line_kind": "allocation", "value": x["mb_per_day"],
                      "unit": "MB/day", "cbe": x.get("cbe_mb_per_day"), "margined": None,
                      "requirement_code": x.get("requirement", ""), "owner_seat": x.get("owner_seat", ""), "status": "agreed"})
    items.append({"element_code": "SYS", "budget_type": "data", "line_kind": "reserve", "value": b["data"]["reserve_mb_per_day"],
                  "unit": "MB/day", "requirement_code": "SYS-BUD-05", "owner_seat": "systems_engineer", "status": "agreed"})
    for x in b["registration"]["allocations"]:
        items.append({"element_code": "", "budget_type": "registration", "line_kind": "allocation", "value": x["px_rms"],
                      "unit": "px", "requirement_code": x.get("requirement", ""), "status": "agreed",
                      "data": {"contributor": x["contributor"]}})
    for x in b["timing"]["contributors"]:
        items.append({"element_code": "", "budget_type": "timing", "line_kind": "allocation", "value": x["ms"], "unit": "ms",
                      "requirement_code": x.get("requirement", ""), "status": "agreed", "data": {"contributor": x["contributor"]}})
    for k in ("control", "knowledge", "alignment"):
        x = b["pointing"][k]
        items.append({"element_code": "AOCS", "budget_type": "pointing", "line_kind": "allocation",
                      "value": x.get("ape_deg_3sigma") or x.get("deg_3sigma"), "unit": "deg", "requirement_code": x["requirement"],
                      "status": "agreed", "data": {"contributor": k}})
    closure = {"mass": {"limit": b["mass"]["closure"]["limit_kg"], "margin_percent": b["mass"]["system_margin_pct"],
                        "requirement_code": b["mass"]["closure"]["requirement"]},
               "power_avg": {"limit": b["power"]["closure"]["eol_generation_w"], "margin_percent": 20.0,
                             "requirement_code": b["power"]["closure"]["requirement"]},
               "data": {"limit": b["data"]["capacity_mb_per_day"], "margin_percent": None}}
    return {"items": items, "reserve": {}, "closure": closure, "counts": {"lines": len(items)}}


def assumptions_section() -> dict:
    reqs = [r for r in load("requirements")["requirements"] if r.get("open_item_note")]
    items = [{"code": f"ASM-{i + 1:02d}", "statement": r["open_item_note"], "affects": [{"kind": "requirement", "ref": r["id"]}],
              "replace_with": "", "owner_seat": r.get("owner_seat", ""), "due_gate": "PDR", "status": "open",
              "source": r["id"]} for i, r in enumerate(reqs)]
    return {"items": items, "counts": {"open": len(items)}}


def negotiations_section() -> dict:
    items = [
        {"code": "N1", "issue": "Science volume delivered per day against the downlink margin",
         "parameters": ["data.science_delivered_mb_per_day", "data.margin_pct"],
         "seats": ["payload_lead", "comms_engineer", "mission_analyst", "customer"],
         "options": [{"label": "13 MB/day", "effects": {"data.margin_pct": 38.5}},
                     {"label": "19.9 MB/day", "effects": {"data.margin_pct": 10.0}}],
         "agreed": {"data.science_delivered_mb_per_day": 13.0},
         "signoffs": {"payload_lead": {"by": "seat"}, "comms_engineer": {"by": "seat"}, "mission_analyst": {"by": "seat"},
                      "customer": {"by": "seat"}},
         "reopen_trigger": "compression < 1.3:1", "links": {"requirements": ["PAY-DAT-01"], "risks": [], "trades": []},
         "status": "agreed"},
        {"code": "N3", "issue": "Payload peak power against the battery", "parameters": ["power.orbit_average_w"],
         "seats": ["payload_lead", "power_engineer"], "options": [], "agreed": {}, "signoffs": {"payload_lead": {"by": "seat"}},
         "reopen_trigger": "", "links": {}, "status": "proposed"},
        {"code": "N7", "issue": "Mass envelopes per subsystem", "parameters": ["mass.with_system_margin_kg"],
         "seats": ["systems_engineer"], "options": [], "agreed": {"mass.allocations_kg": 4.43}, "signoffs": {},
         "reopen_trigger": "", "links": {}, "status": "proposed"},
    ]
    return {"items": items, "counts": {"total": 3, "agreed": 1}}


def open_items_section() -> dict:
    n = load("NUMBERS")
    items = [{"code": d["id"], "kind": "pi_decision" if "PI" in d["id"] else "seat_decision", "title": d.get("question", "")[:200],
              "owner_seat": d.get("owner", ""), "status": "open", "blocks_gate": "pdr"} for d in n.get("open_decisions") or []]
    by_gate: dict[str, int] = {}
    for i in items:
        by_gate[i["blocks_gate"]] = by_gate.get(i["blocks_gate"], 0) + 1
    return {"items": items, "by_gate": by_gate, "counts": {"open": len(items)}}


def changes_section() -> dict:
    items = [{"code": "ECP-01", "kind": "ecp", "title": "NIR filter change", "change_class": "II", "status": "proposed",
              "decision_gate": "pdr", "affected_codes": ["PAY-OPT-01"], "impact": {"mass_kg": 0.0}},
             {"code": "ECP-02", "kind": "ecp", "title": "Accept 550–600 km injection", "change_class": "II", "status": "accepted",
              "decision_gate": "srr", "affected_codes": ["SEG-LS-02"], "source_trade": "T-M01", "impact": {}}]
    return {"items": items, "counts": {"total": 2}}


def change_control_section() -> dict:
    return {"items": [{"change_code": "ECP-02", "kind": "seat", "seat": "mission_analyst", "decision": "agree"},
                      {"change_code": "ECP-02", "kind": "board", "seat": "team_leader", "decision": "approve",
                       "baseline_ref": "SRR functional baseline"}], "counts": {"total": 2}}


def icds_section() -> dict:
    return {"items": [{"icd_ref": "ICD-DEP-01", "title": "Deployer interface", "issue": "A", "revision": 0, "state": "issue_a",
                       "provider_seat": "structures_engineer", "consumer_seat": "systems_engineer",
                       "signoffs": {"structures_engineer": {"by": "seat"}, "systems_engineer": {"by": "seat"}}}],
            "counts": {"total": 1, "issue_a": 1}}


def reliability_section() -> dict:
    return {"blocks": [{"name": "EPS", "subsystem": "EPS", "arrangement": "series", "failure_rate_fit": 500.0,
                        "rate_source": "heritage", "reliability": 0.995, "horizon_months": 12}],
            "result": {"reliability": 0.86, "horizon_months": 12, "target": 0.80},
            "fmea": [{"code": "FM-EPS-01", "subsystem": "EPS", "item": "Battery", "failure_mode": "cell open",
                      "system_effect": "loss of eclipse power", "severity": 2, "probability": 2, "criticality": 4,
                      "fdir_ref": "FDIR-EPS-01", "mitigation": "4S cells, undervoltage safe mode", "single_point": False}],
            "counts": {"blocks": 1, "fmea": 1}}


def thermal_model_section() -> dict:
    return {"nodes": [{"code": "N01", "name": "Battery", "op_min_c": 0, "op_max_c": 45, "heater_w": 0.3, "limits_source": "kb"}],
            "couplings": [{"node_a": "N01", "node_b": "space", "kind": "radiative", "value": 0.01}],
            "cases": [{"code": "COLD-OP", "kind": "cold", "beta_deg": 0, "eclipse_min": 35.0, "status": "solved",
                       "results": {"N01": {"t_c": 5.0, "margin_design_c": 5.0}}}],
            "counts": {"nodes": 1, "cases": 1}}


def debris_section() -> dict:
    return {"assessment": {"version": 1, "lifetime_y": 3.0, "lifetime_without_device_y": 14.7, "casualty_risk": 0.0,
                           "collision_probability": 1e-4, "status": "accepted", "accepted_gate": "srr",
                           "accepted_by": "mission_analyst"}, "history": []}


def cost_section() -> dict:
    items = [{"category": "hardware", "name": "Flight hardware", "total_keur": 275.0, "source": "equipment list"},
             {"category": "labour", "name": "Student and staff labour", "quantity": 60, "unit": "person-months",
              "unit_cost_keur": 4.0, "total_keur": 240.0, "source": "reference class"},
             {"category": "reserve", "name": "Reserve", "percent_of_base": 20, "total_keur": 103.0}]
    return {"items": items, "by_category": {"hardware": 275.0, "labour": 240.0, "reserve": 103.0}, "total_keur": 618.0}


SECTIONS = {"stakeholders": stakeholders_section, "validation": validation_section, "allocations": allocations_section,
            "assumptions": assumptions_section, "negotiations": negotiations_section, "open_items": open_items_section,
            "changes": changes_section, "change_control": change_control_section, "icds": icds_section,
            "reliability": reliability_section, "thermal_model": thermal_model_section, "debris": debris_section,
            "cost": cost_section}


def register_sections(monkeypatch, names: tuple[str, ...] | None = None) -> None:
    """Register baseline-file collectors for the wave-3 sections that are still stubs here (an
    owner's real collector, once merged, is kept: only stubs are replaced)."""
    from spacecdf_server.services import export_context as ec

    for name, fn in SECTIONS.items():
        if names is not None and name not in names:
            continue
        real, _empty = ec._load(name)
        mod = __import__(f"spacecdf_server.services.export_context.sections.{name}", fromlist=["x"])
        if "STEP 0 STUB" not in (mod.__doc__ or ""):
            continue

        async def collect(ctx, _fn=fn):
            return _fn()
        monkeypatch.setitem(ec._REGISTRY, name, collect)


# ─────────────────────────────────────────────────────────────── functions into the store


async def write_functions(study_id: str, elements: dict[str, dict]) -> dict[str, str]:
    """The v2 function tree (functions.yaml) written into the store: functions named "F1 Acquire
    imagery" (code also in ``external_id``), leaf allocations to the tool elements, and one
    exchange per functional interface. Returns {code: function id}. Agent R's bulk import (3.R1)
    does the same through the API."""
    from spacecdf_server.db import function_repo as fr

    data = load("functions")
    by_name = {e.get("name"): e for e in elements.values()}
    ids: dict[str, str] = {}
    for f in sorted(data["functions"], key=lambda f: int(f.get("depth") or 1)):
        row = await fr.create_function({"study_id": study_id, "name": f"{f['id']} {f['name']}", "external_id": f["id"],
                                        "description": f.get("description", ""), "parent_id": ids.get(f.get("parent") or ""),
                                        "layer": "SA", "level": int(f.get("depth") or 1), "is_leaf": bool(f.get("leaf"))})
        ids[f["id"]] = row["id"]
        if f.get("leaf"):
            for code in f.get("allocation") or []:
                el = by_name.get(ELEMENT_IDS.get(code, ""))
                if el:
                    await fr.allocate_function(study_id, row["id"], el["id"])
                    break
    for k, x in enumerate(data["functional_interfaces"]):
        a, b = ids.get(x["from"]), ids.get(x["to"])
        if not a or not b:
            continue
        pa = await fr.create_function_port({"function_id": a, "name": x["item"][:200], "direction": "out"})
        pb = await fr.create_function_port({"function_id": b, "name": x["item"][:200], "direction": "in"})
        await fr.create_functional_exchange({"study_id": study_id, "name": x["item"], "from_port_id": pa["id"],
                                             "to_port_id": pb["id"]})
    return ids


def counts_by_stage(reqs: list[dict]) -> dict[str, int]:
    """Requirements per closing stage, counted as the V counts them (store rows, without SN-*,
    OBJ-* and generated IR-* rows)."""
    out: dict[str, int] = {}
    for r in reqs:
        if r.get("generated_interface") or r.get("level") == "stakeholder" or str(r.get("code") or "").startswith(("OBJ-", "SN-", "IR-")):
            continue
        st = str(r.get("verification_phase") or "").upper()
        if st:
            out[st] = out.get(st, 0) + 1
    return out


__all__ = ["SECTIONS", "register_sections", "write_functions", "counts_by_stage", "stakeholders_section",
           "allocations_section"]
_ = Any
