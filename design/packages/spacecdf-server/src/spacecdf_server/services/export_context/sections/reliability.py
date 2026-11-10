"""Section ``reliability``: the reliability block diagram over the mission-success horizon and
the FMEA/FMECA worksheet. Owner: A (3.A5).

Shape (``services/reliability_model.get``)::

    blocks: [{name, subsystem, arrangement, k, n, failure_rate_fit, rate_source, duty_cycle,
              reliability, horizon_months}]
    result: {mission_reliability, target, meets_target, horizon{...}, design_life_reliability,
             by_subsystem{}, weakest_subsystem, single_string_units, evidence, method}
    fmea:   [{code, subsystem, item, failure_mode, cause, local_effect, system_effect, severity,
              probability, criticality, detection, fdir_ref, mitigation, risk_ids, single_point}]
    counts: {blocks, fmea_rows, critical, single_points, with_fdir, with_risk, subsystems[]}
"""
from __future__ import annotations


def empty() -> dict:
    return {"blocks": [], "result": {}, "fmea": [], "counts": {}}


_BLOCK = ("name", "subsystem", "arrangement", "k", "n", "failure_rate_fit", "rate_source", "duty_cycle",
          "reliability", "horizon_months")
_FMEA = ("code", "subsystem", "item", "function", "failure_mode", "cause", "local_effect", "system_effect", "severity",
         "probability", "criticality", "detection", "fdir_ref", "mitigation", "single_point", "status")


async def collect(ctx) -> dict:
    from ...reliability_model import get
    d = await get(ctx.study_id)
    if not d["blocks"] and not d["fmea"]:
        return {"status": "empty", **empty()}
    blocks = [{k: b.get(k) for k in _BLOCK} for b in d["blocks"]]
    fmea = []
    for r in d["fmea"]:
        row = {k: r.get(k) for k in _FMEA}
        row["risk_ids"] = list(r.get("risk_ids_json") or [])
        fmea.append(row)
    return {"status": "ok", "blocks": blocks, "result": d["result"], "fmea": fmea, "counts": d["counts"]}
