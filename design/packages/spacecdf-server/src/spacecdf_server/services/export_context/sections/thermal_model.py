"""Section ``thermal_model``: the thermal nodal model: nodes, couplings, hot and cold cases,
temperatures and margins (design, acceptance, qualification), heater sizing. Owner: A (3.A6).

Shape (``services/thermal_model.get``)::

    nodes:     [{code, name, capacitance_j_k, area_m2, absorptivity, emissivity, op_min_c, op_max_c,
                 limits_source, heater_w, heater_needed_w, margins{t_min_c, t_max_c, design,
                 acceptance, qualification, status}}]
    couplings: [{node_a, node_b, kind, value, source}]     (node codes; "space" for the sink)
    cases:     [{code, kind, beta_deg, eclipse_min, source, status, results{node: {t_min_c, t_max_c}}}]
    counts:    {nodes, couplings, cases}
    summary:   {solved, out_of_design_range[], heaters[], worst_design_margin_c, uncertainty_c}
"""
from __future__ import annotations


def empty() -> dict:
    return {"nodes": [], "couplings": [], "cases": [], "counts": {}}


async def collect(ctx) -> dict:
    from ...thermal_model import get
    d = await get(ctx.study_id)
    if not d["nodes"]:
        return {"status": "empty", **empty()}
    code = {n["id"]: n["code"] for n in d["nodes"]}
    nodes = []
    for n in d["nodes"]:
        dj = n.get("data_json") or {}
        nodes.append({k: n.get(k) for k in ("code", "name", "capacitance_j_k", "area_m2", "absorptivity", "emissivity",
                                             "op_min_c", "op_max_c", "limits_source", "heater_w")}
                     | {"name_fr": dj.get("name_fr") or n.get("name"), "heater_needed_w": dj.get("heater_needed_w"),
                        "margins": dj.get("margins") or {}, "external": bool(dj.get("external"))})
    couplings = [{"node_a": code.get(c["node_a"], c["node_a"]), "node_b": code.get(c["node_b"], c["node_b"]),
                  "kind": c.get("kind"), "value": c.get("value"), "source": c.get("source")} for c in d["couplings"]]
    cases = [{k: c.get(k) for k in ("code", "kind", "beta_deg", "eclipse_min", "mode_key", "source", "status")}
             | {"results": c.get("results_json") or {}} for c in d["cases"]]
    return {"status": "ok", "nodes": nodes, "couplings": couplings, "cases": cases, "counts": d["counts"],
            "summary": d["summary"]}
