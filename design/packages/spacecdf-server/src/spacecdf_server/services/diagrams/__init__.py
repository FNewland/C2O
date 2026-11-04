"""SEMP / ECSS diagram set (design rules §3): the catalogue and the builders.

``KINDS`` lists every diagram with the review gates that expect it (ECSS product maturity:
D draft, B baselined, U updated; reconstructed from ECSS-E-ST-10C Annex A and the §3 table,
to verify) and the gate-profile product it is evidence for (configs/gate_profiles.yaml).

    build(kind, data, **opts) -> diagram model (see base.py)
    catalogue(data, gate=None) -> [{kind, title, group, gates, product, ref, gaps, completeness, …}]
"""
from __future__ import annotations

from typing import Any, Callable

from . import b_conops, b_electrical, b_other, b_physical, b_trees
from .base import T
from .data import DiagramData, load

__all__ = ["KINDS", "GROUPS", "build", "catalogue", "load", "DiagramData", "gate_kinds"]

# English text is the key (vocab.ts)
GROUPS = {
    "conops": "Concept of operations", "architecture": "Architecture", "interfaces": "Interfaces",
    "electrical": "Electrical and data", "rf": "Communications", "thermal_mech": "Thermal and mechanical",
    "ground": "Ground segment", "vv": "Requirements and verification", "management": "Management",
}

# English text is the key (vocab.ts)
TITLES = {
    "phases": "Mission phase timeline",
    "modes": "Mode state diagram",
    "ops_pass": "Operations scenario — one ground-station pass",
    "product_tree": "Product tree",
    "function_tree": "Function tree",
    "allocation": "Function × product allocation",
    "block": "Physical block diagram",
    "n2": "N² chart",
    "power": "Electrical power block diagram",
    "switch_matrix": "Switch matrix — power lines × modes",
    "data_bus": "Data-handling block diagram — bus topology",
    "rf": "RF block diagram",
    "thermal": "Thermal node diagram",
    "stack": "Mechanical stack — elevation",
    "ground": "Ground segment diagram",
    "req_tree": "Requirement tree and traceability",
    "vcd": "Verification matrix (VCD)",
    "risk": "Risk matrix (5 × 5)",
    "budgets": "Budget charts (mass, power, data, link, ΔV)",
}

KINDS: dict[str, dict[str, Any]] = {
    "phases": {"title": "Mission phase timeline", "group": "conops", "fn": b_conops.phases,
               "gates": {"mdr": "D", "prr": "U"}, "product": "conops", "ref": "ECSS-E-ST-70C; NASA SEH App. S"},
    "modes": {"title": "Mode state diagram", "group": "conops", "fn": b_conops.modes,
              "gates": {"mdr": "D", "pdr": "B"}, "product": "conops", "ref": "ECSS-E-ST-70C; ECSS-E-ST-10C DDF"},
    "ops_pass": {"title": "Operations scenario — one ground-station pass", "group": "conops", "fn": b_conops.ops_pass,
                 "gates": {"prr": "D", "pdr": "U"}, "product": "conops", "ref": "ECSS-E-ST-70C; NASA SEH App. S"},
    "product_tree": {"title": "Product tree", "group": "architecture", "fn": b_trees.product_tree,
                     "gates": {"prr": "D", "srr": "U", "pdr": "B"}, "product": "product_tree", "ref": "ECSS-M-ST-10C §5.3"},
    "function_tree": {"title": "Function tree", "group": "architecture", "fn": b_trees.function_tree,
                      "gates": {"prr": "D", "srr": "U"}, "product": "function_tree", "ref": "ECSS-E-ST-10C Annex H; NASA SEH §4.3"},
    "allocation": {"title": "Function × product allocation", "group": "architecture", "fn": b_trees.allocation,
                   "gates": {"srr": "B", "pdr": "U"}, "product": "function_tree", "ref": "ECSS-E-ST-10C; NASA SEH §4.3"},
    "block": {"title": "Physical block diagram", "group": "architecture", "fn": b_physical.block,
              "gates": {"prr": "D", "pdr": "B"}, "product": "design_files", "ref": "ECSS-E-ST-10C DDF; NASA SEH §4.3"},
    "n2": {"title": "N² chart", "group": "interfaces", "fn": b_physical.n2,
           "gates": {"prr": "D", "srr": "U", "pdr": "B"}, "product": "interfaces", "ref": "ECSS-E-ST-10-24C; NASA SEH §4.3"},
    "power": {"title": "Electrical power block diagram", "group": "electrical", "fn": b_electrical.power,
              "gates": {"pdr": "B"}, "product": "design_files", "ref": "ECSS-E-ST-20C"},
    "switch_matrix": {"title": "Switch matrix — power lines × modes", "group": "electrical", "fn": b_electrical.switch_matrix,
                      "gates": {"pdr": "D"}, "product": "design_files", "ref": "ECSS-E-ST-20C"},
    "data_bus": {"title": "Data-handling block diagram — bus topology", "group": "electrical", "fn": b_electrical.data_bus,
                 "gates": {"pdr": "B"}, "product": "interfaces", "ref": "ECSS-E-ST-50C; ECSS-E-ST-40C"},
    "rf": {"title": "RF block diagram", "group": "rf", "fn": b_other.rf,
           "gates": {"prr": "D", "pdr": "B"}, "product": "spectrum", "ref": "ECSS-E-ST-50C"},
    "thermal": {"title": "Thermal node diagram", "group": "thermal_mech", "fn": b_other.thermal,
                "gates": {"pdr": "D"}, "product": "design_files", "ref": "ECSS-E-ST-31C"},
    "stack": {"title": "Mechanical stack — elevation", "group": "thermal_mech", "fn": b_other.stack,
              "gates": {"pdr": "B"}, "product": "cds_matrix", "ref": "ECSS-E-ST-32C; CDS rev 14.1"},
    "ground": {"title": "Ground segment diagram", "group": "ground", "fn": b_other.ground,
               "gates": {"prr": "D", "pdr": "U"}, "product": "conops", "ref": "ECSS-E-ST-70C"},
    "req_tree": {"title": "Requirement tree and traceability", "group": "vv", "fn": b_trees.req_tree,
                 "gates": {"srr": "B", "pdr": "U"}, "product": "trs", "ref": "ECSS-E-ST-10-06C; NASA SEH §4.2"},
    "vcd": {"title": "Verification matrix (VCD)", "group": "vv", "fn": b_other.vcd,
            "gates": {"srr": "D", "pdr": "U"}, "product": "vcd", "ref": "ECSS-E-ST-10-02C; NASA SEH §5.3"},
    "risk": {"title": "Risk matrix (5 × 5)", "group": "management", "fn": b_other.risk,
             "gates": {"mdr": "D", "prr": "U", "srr": "U", "pdr": "U"}, "product": "risk_register", "ref": "ECSS-M-ST-80C"},
    # charts that already exist elsewhere: linked, not redrawn
    "budgets": {"title": "Budget charts (mass, power, data, link, ΔV)", "group": "management", "fn": None, "link": "budget",
                "gates": {"prr": "D", "srr": "U", "pdr": "B"}, "product": "budgets", "ref": "ECSS-E-ST-10C Annex I"},
}

#: diagrams that go into each exported document (same models as the screen)
DOCUMENT_SETS: dict[str, list[str]] = {
    "semp": ["phases", "modes", "ops_pass", "product_tree", "function_tree", "allocation", "block", "n2", "ground",
             "req_tree", "vcd", "risk"],
    "ird": ["block", "n2", "power", "switch_matrix", "data_bus", "rf"],
    "all": [k for k in KINDS if KINDS[k]["fn"] is not None],
}


def build(kind: str, data: DiagramData, **opts: Any) -> dict:
    spec = KINDS[kind]
    fn: Callable[..., dict] | None = spec["fn"]
    if fn is None:
        raise KeyError(kind)
    clean = {k: v for k, v in opts.items() if v not in (None, "")}
    try:
        model = fn(data, **clean)
    except Exception as exc:  # noqa: BLE001 — a broken builder must not take the view down
        import logging
        logging.getLogger(__name__).exception("diagram %s failed for %s", kind, data.study_id)
        from .base import Diagram
        D = Diagram(kind, T(spec["title"]), "graph")
        D.empty(T("This diagram could not be drawn: {{error}}", error=str(exc)[:160]))
        D.gap("error", T("This diagram could not be drawn: {{error}}", error=str(exc)[:160]), severity="alarm")
        model = D.finish()
    model["gates"] = [{"gate": g, "maturity": m} for g, m in spec["gates"].items()]
    model["product"] = spec["product"]
    model["ref"] = spec["ref"]
    model["group"] = spec["group"]
    model["study_id"] = data.study_id
    return model


def gate_kinds(covers: list[str]) -> list[str]:
    return [k for k, s in KINDS.items() if any(g in s["gates"] for g in covers)]


def catalogue(data: DiagramData, covers: list[str] | None = None) -> list[dict]:
    """Every diagram with its gap count and completeness (each model is built once)."""
    out = []
    for kind, spec in KINDS.items():
        if covers and not any(g in spec["gates"] for g in covers):
            continue
        entry = {"kind": kind, "title": T(spec["title"]), "group": spec["group"], "group_label": T(GROUPS[spec["group"]]),
                 "gates": [{"gate": g, "maturity": m} for g, m in spec["gates"].items()], "product": spec["product"],
                 "ref": spec["ref"], "link": spec.get("link")}
        if spec["fn"] is not None:
            m = build(kind, data)
            entry.update({"gaps": len(m["gaps"]), "gap_alarm": sum(1 for g in m["gaps"] if g["severity"] == "alarm"),
                          "completeness": m["completeness"], "empty": m["empty"] is not None,
                          "top_gaps": [g["message"] for g in m["gaps"] if g["severity"] != "info"][:3]})
        else:
            entry.update({"gaps": 0, "gap_alarm": 0, "completeness": None, "empty": False, "top_gaps": []})
        out.append(entry)
    return out
