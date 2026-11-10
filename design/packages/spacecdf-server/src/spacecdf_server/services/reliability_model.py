"""Reliability analysis and FMEA/FMECA worksheet (wave 3, 3.A5; PI addendum).

**Reliability block diagram.** One block per space hardware unit of the product tree (lenses,
filters, fasteners and other passive parts fold into their assembly), grouped by subsystem. Each
block carries a failure rate in FIT with its source: the element's own ``failure_rate_fit`` or
``mtbf_h`` (supplier data), the KB part's, else the planning rate of its unit type
(``configs/reliability_rates.yaml``, C2O default). Redundancy is ``k`` of ``n``: a quantity of n
identical units in parallel when the element says ``redundancy_k`` (or ``redundancy_type``), e.g.
the two solar wings of which one is enough (SYS-REL-03). One-time events (deployments) multiply by
their success probability. A unit that is switched off part of the time fails at the dormant
ratio while off.

**Mission-success horizon.** ``R`` is computed over the study's mission-success horizon, not the
design life: ``mission.success_horizon_months`` (e.g. 12 months of science operations after
commissioning, MIS-LIF-02), plus LEOP and commissioning from the ConOps phases. The design life
gives a second figure for comparison. Without a horizon the design life is used, with a warning.

**FMEA/FMECA worksheet.** ``propose_fmea`` takes every failure mode of the failure-mode library
(``services/fmeca_library``) for each unit, as rows the team edits: severity, probability,
criticality (S × P), detection, the FDIR monitor of the CDR model that detects it and the study
risks it feeds. PDR-EC-05 (wired by R) reads :func:`evidence`.

Public API::

    await run(study_id) -> {"blocks", "result"}      # propose / refresh blocks and compute R
    await get(study_id) -> {"blocks", "result", "fmea", "counts"}
    await propose_fmea(study_id) -> {"added", "items"}
    await evidence(study_id) -> {"ok", "reliability", "target", "horizon_months", "fmea_rows", ...}
"""
from __future__ import annotations

import logging
import math
import re
from typing import Any

from ..db.models_reliability import FmeaRow, ReliabilityBlockRow
from . import rule_config as rc
from . import study_rows as sr

logger = logging.getLogger(__name__)

CONFIG = "reliability_rates"
HOURS_PER_MONTH = 365.25 * 24 / 12
SUBSYSTEM_CODE = {"payload": "PAY", "power": "EPS", "aocs": "AOCS", "ttc": "COM", "obc": "OBC", "thermal": "THM",
                  "structure": "STR", "propulsion": "DIS", "harness": "HAR"}


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _study(study_id: str):
    from ..routers.studies import get_study_store
    return get_study_store().get(study_id)


def _elements(study_id: str) -> list[dict]:
    from ..routers.elements import _elements as cache
    return [e for e in cache.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


# ───────────────────────────────────────────────────────── horizon

def horizon(study: Any) -> dict[str, Any]:
    """Mission-success horizon: months of operations after commissioning (the study's
    ``success_horizon_months``) plus LEOP and commissioning from the ConOps phases."""
    req = getattr(study, "requirements", None)
    months = _num(getattr(req, "success_horizon_months", None))
    life_y = _num(getattr(req, "design_lifetime_years", None)) or 3.0
    pre_days = 0.0
    conops = getattr(study, "conops", None)
    for ph in (getattr(conops, "phases", None) or []):
        pt = str(getattr(getattr(ph, "phase_type", ""), "value", getattr(ph, "phase_type", "")) or "").lower()
        if pt in ("leop", "commissioning"):
            pre_days += float(getattr(ph, "duration_days", 0) or 0)
    pre_months = round(pre_days / 30.4375, 2)
    warnings = []
    if months is None:
        warnings.append("No mission-success horizon in the mission definition (success_horizon_months): "
                        "the design life is used instead.")
        exposure = life_y * 12
        basis = f"design life {life_y:g} years"
    else:
        exposure = months + pre_months
        basis = (f"{months:g} months of operations after commissioning"
                 + (f" (+{pre_months:g} months LEOP and commissioning)" if pre_months else ""))
    return {"success_horizon_months": months, "pre_operations_months": pre_months,
            "exposure_months": round(exposure, 2), "design_life_years": life_y, "basis": basis,
            "warnings": warnings}


# ───────────────────────────────────────────────────────── blocks

def _subsystem(e: dict, idx: dict[str, dict]) -> dict | None:
    cur, seen = e, set()
    while cur is not None and cur["id"] not in seen:
        seen.add(cur["id"])
        if cur.get("element_type") == "subsystem":
            return cur
        cur = idx.get(cur.get("parent_id") or "")
    return None


def _perf(e: dict) -> dict:
    p = e.get("performance") if e.get("performance") is not None else e.get("performance_json")
    return p if isinstance(p, dict) else {}


def mode_duty(modes: list) -> dict[str, float]:
    """Element id -> share of the orbit it is powered, from the Modes tab (operational modes with a
    share of the orbit); elements that are never off in those modes get no entry (always on)."""
    ops = [m for m in modes if getattr(m, "source", "") == "element" and getattr(m, "orbit_fraction", None)]
    if not ops:
        return {}
    on: dict[str, float] = {}
    seen: set[str] = set()
    for m in ops:
        for mem in m.members:
            seen.add(mem["element_id"])
            if float(mem.get("power_w") or 0.0) > 0 and mem.get("state") != "off":
                on[mem["element_id"]] = on.get(mem["element_id"], 0.0) + float(m.orbit_fraction) * float(mem.get("duty") or 1.0)
    total = sum(float(m.orbit_fraction) for m in ops) or 1.0
    return {eid: round(min(1.0, on.get(eid, 0.0) / total), 4) for eid in seen if on.get(eid, 0.0) / total < 0.999}


def proposed_blocks(elements: list[dict], duty: dict[str, float] | None = None) -> list[dict]:
    """One block per space hardware unit (pure). ``duty``: share of the orbit each unit is on."""
    from .fmeca_library import match_type
    from .rule_inputs import kb_component, space_hardware
    cfg = rc.load(CONFIG)
    fm_cfg = rc.load("failure_modes")
    duty_map = duty
    hw = space_hardware(elements)
    idx = {e["id"]: e for e in elements}
    kids = {e.get("parent_id") for e in hw}
    passive = [k.lower() for k in (cfg.get("passive_keywords") or [])]
    out = []
    for e in hw:
        if e.get("element_type") not in ("component", "subsystem"):
            continue
        if e.get("element_type") == "subsystem" and e["id"] in kids:
            continue
        name = str(e.get("name") or "")
        low = name.lower()
        if not (e.get("power_avg_w") or 0) and any(k in low for k in passive):
            continue
        sub = _subsystem(e, idx) or e
        tid = "harness" if "harness" in low else (match_type(e, fm_cfg) or "generic")
        t = (cfg.get("types") or {}).get(tid) or {}
        perf, kbp = _perf(e), ((kb_component(e) or {}).get("performance") or {})
        fit, src = None, ""
        for where, d in (("element", perf), ("kb", kbp)):
            if _num(d.get("failure_rate_fit")):
                fit, src = float(d["failure_rate_fit"]), f"{where}: failure_rate_fit"
                break
            if _num(d.get("mtbf_h")):
                fit, src = 1e9 / float(d["mtbf_h"]), f"{where}: mtbf_h"
                break
        if fit is None:
            fit = float(t.get("fit") or cfg.get("default_fit") or 1000)
            src = f"planning rate ({tid}, C2O default)"
        n = max(1, int(e.get("quantity") or 1))
        k = n
        kf = _num(((cfg.get("redundancy") or {}).get(tid) or {}).get("k_fraction"))
        if kf and n > 1:
            k = max(1, math.ceil(n * kf - 1e-9))
        if _num(perf.get("redundancy_k")):
            k = max(1, min(n, int(perf["redundancy_k"])))
        elif str(e.get("redundancy_type") or "").lower() in ("cold", "hot", "warm", "standby", "dual", "redundant"):
            k = 1
        duty = _num(perf.get("duty_cycle")) if e.get("element_type") == "component" else None
        if duty is None and duty_map is not None and e["id"] in duty_map and float(e.get("power_avg_w") or 0) > 0:
            duty = duty_map[e["id"]]
        out.append({
            "element_id": e["id"], "name": name, "subsystem": SUBSYSTEM_CODE.get(sub.get("subsystem_domain") or "", "SC"),
            "arrangement": "series" if k == n else ("parallel" if k == 1 else "k_of_n"), "k": k, "n": n,
            "failure_rate_fit": round(fit, 3), "rate_source": src,
            "duty_cycle": duty if duty is not None and 0 <= duty <= 1 else None,
            "data_json": {"unit_type": tid, "one_shot": t.get("one_shot"),
                          "mission_success": t.get("mission_success", True) is not False,
                          "rate_source_ref": "c2o_rates" if src.startswith("planning") else src},
            "origin": "proposed",
        })
    out.sort(key=lambda b: (b["subsystem"], b["name"]))
    for i, b in enumerate(out):
        b["order"] = i
    return out


def block_reliability(b: dict, hours: float, dormant_ratio: float = 0.1) -> float:
    """R of one block over ``hours``: k-of-n identical units, duty-weighted rate, one-shot event."""
    lam = float(b.get("failure_rate_fit") or 0.0) * 1e-9
    d = b.get("duty_cycle")
    if d is not None:
        lam *= float(d) + (1 - float(d)) * dormant_ratio
    r1 = math.exp(-lam * hours)
    n, k = int(b.get("n") or 1), int(b.get("k") or b.get("n") or 1)
    if k >= n:
        r = r1 ** n
    else:
        r = sum(math.comb(n, i) * r1 ** i * (1 - r1) ** (n - i) for i in range(k, n + 1))
    one = (b.get("data_json") or {}).get("one_shot")
    if _num(one):
        # deployment: k of n deployments must succeed
        p = float(one)
        if k >= n:
            r *= p ** n
        else:
            r *= sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))
    return r


def compute(blocks: list[dict], hor: dict, target: float | None, life_hours: float) -> dict[str, Any]:
    cfg = rc.load(CONFIG)
    dr = float(cfg.get("dormant_ratio") or 0.1)
    hours = float(hor["exposure_months"]) * HOURS_PER_MONTH
    by_sub: dict[str, float] = {}
    system = life = 1.0
    excluded = []
    spf = []
    for b in blocks:
        r = block_reliability(b, hours, dr)
        b["reliability"] = round(r, 5)
        b["horizon_months"] = hor["exposure_months"]
        if (b.get("data_json") or {}).get("mission_success", True) is False:
            excluded.append(b["name"])
            continue
        system *= r
        life *= block_reliability(b, life_hours, dr)
        by_sub[b["subsystem"]] = by_sub.get(b["subsystem"], 1.0) * r
        if int(b.get("k") or 1) >= int(b.get("n") or 1):
            spf.append(b["name"])
    weakest = min(by_sub.items(), key=lambda kv: kv[1]) if by_sub else ("", 1.0)
    out = {
        "mission_reliability": round(system, 4), "target": target,
        "meets_target": (system >= target) if target is not None else None,
        "horizon": hor, "design_life_reliability": round(life, 4),
        "by_subsystem": {k: round(v, 4) for k, v in sorted(by_sub.items())},
        "weakest_subsystem": weakest[0], "weakest_reliability": round(weakest[1], 4),
        "single_string_units": len(spf), "excluded_from_mission_success": excluded,
        "blocks": len(blocks), "method": "series chain of k-of-n blocks, exponential failure law, dormant ratio "
                                         f"{dr:g}, one-shot deployments; rates C2O planning values unless sourced",
        "evidence": (f"R = {system:.3f} over {hor['basis']}"
                     + (f" against {target:.2f}" if target is not None else "")),
    }
    return out


async def run(study_id: str, *, replace: bool = False) -> dict[str, Any]:
    """Propose the blocks the study does not have (user rows are kept), then compute R."""
    study = _study(study_id)
    existing = await sr.list_rows(ReliabilityBlockRow, study_id)
    if replace:
        await sr.delete_rows(ReliabilityBlockRow, study_id, ids=[b["id"] for b in existing if b.get("origin") != "user"])
        existing = [b for b in existing if b.get("origin") == "user"]
    have = {b.get("element_id") for b in existing}
    duty: dict[str, float] = {}
    try:
        from .analysis_context import build_context
        duty = mode_duty((await build_context(study_id)).modes)
    except Exception:  # noqa: BLE001 — no modes yet: every unit always on
        logger.debug("mode duty unavailable", exc_info=True)
    new = [b for b in proposed_blocks(_elements(study_id), duty) if b["element_id"] not in have]
    if new:
        await sr.insert_rows(ReliabilityBlockRow, study_id, new, prefix="rb")
    blocks = await sr.list_rows(ReliabilityBlockRow, study_id)
    req = getattr(study, "requirements", None)
    target = _num(getattr(req, "reliability_target", None))
    hor = horizon(study)
    res = compute(blocks, hor, target, hor["design_life_years"] * 8766.0)
    for b in blocks:
        await sr.update_row(ReliabilityBlockRow, b["id"], {"reliability": b["reliability"],
                                                           "horizon_months": b["horizon_months"]})
    return {"study_id": study_id, "blocks": blocks, "result": res}


async def get(study_id: str) -> dict[str, Any]:
    blocks = await sr.list_rows(ReliabilityBlockRow, study_id)
    fmea = await sr.list_rows(FmeaRow, study_id)
    res: dict[str, Any] = {}
    if blocks:
        study = _study(study_id)
        req = getattr(study, "requirements", None)
        hor = horizon(study)
        res = compute(blocks, hor, _num(getattr(req, "reliability_target", None)), hor["design_life_years"] * 8766.0)
    crit = [r for r in fmea if (r.get("criticality") or 0) >= CRITICAL]
    return {"study_id": study_id, "blocks": blocks, "result": res, "fmea": fmea,
            "counts": {"blocks": len(blocks), "fmea_rows": len(fmea), "critical": len(crit),
                       "single_points": sum(1 for r in fmea if r.get("single_point")),
                       "with_fdir": sum(1 for r in fmea if r.get("fdir_ref")),
                       "with_risk": sum(1 for r in fmea if r.get("risk_ids_json")),
                       "subsystems": sorted({r.get("subsystem") for r in fmea if r.get("subsystem")})}}


# ───────────────────────────────────────────────────────── FMEA

#: criticality (severity × probability, 1..25) at or above which a row is critical
CRITICAL = 12

_STOP = {"with", "and", "the", "unit", "kit", "board", "custom", "assembly", "config", "panel"}
#: unit type -> words that name it in a risk description
TYPE_WORDS = {"battery": ["battery", "batteries", "cell"], "eps": ["eps", "power", "p60"],
              "solar_array": ["solar", "wing", "array", "dmsa"], "obc": ["obc", "on-board computer", "a3200"],
              "transceiver": ["radio", "transceiver", "uhf", "murgas", "450"], "antenna": ["antenna", "dipole"],
              "adcs_unit": ["adcs", "star tracker", "wheel", "pointing"], "sun_sensor": ["sun sensor"],
              "gnss": ["gnss", "gps"], "deorbit_device": ["sail", "deorbit", "disposal", "timer"],
              "payload": ["camera", "payload", "swir", "vnir", "detector", "filter"], "thermal": ["heater", "thermal"]}


def _risk_links(rtype: str, name: str, risks: list[dict]) -> list[str]:
    words = list(TYPE_WORDS.get(rtype, []))
    words += [w for w in re.findall(r"[a-z0-9]{4,}", name.lower()) if w not in _STOP][:3]
    out = []
    for r in risks:
        text = f"{r.get('description') or ''} {r.get('title') or ''}".lower()
        if any(w in text for w in words):
            out.append(str(r.get("id") or r.get("code") or ""))
    return [x for x in out if x][:4]


async def _fdir_monitors(study_id: str) -> dict[str, str]:
    """element id -> the key of its FDIR monitor in the CDR model (accepted or proposed)."""
    try:
        from ..db.cdr_repo import list_rows
        rows = await list_rows(study_id, "monitors")
    except Exception:  # noqa: BLE001
        return {}
    out: dict[str, str] = {}
    for r in rows:
        eid = (r.get("data") or r.get("data_json") or {}).get("element_id")
        if eid and r.get("status") != "rejected":
            out.setdefault(eid, r.get("key") or r.get("id"))
    return out


async def propose_fmea(study_id: str, *, replace: bool = False) -> dict[str, Any]:
    """FMEA rows for every unit from the failure-mode library, linked to FDIR monitors and risks.
    Rows the team wrote or edited (``origin = user``) are kept."""
    from .fmeca_library import build_skeleton
    els = _elements(study_id)
    idx = {e["id"]: e for e in els}
    sk = build_skeleton(els, None)
    existing = await sr.list_rows(FmeaRow, study_id)
    if replace:
        await sr.delete_rows(FmeaRow, study_id, ids=[r["id"] for r in existing if r.get("origin") != "user"])
        existing = [r for r in existing if r.get("origin") == "user"]
    have = {(r.get("element_id"), (r.get("data_json") or {}).get("library_id")) for r in existing}
    study = _study(study_id)
    risks = list(getattr(study, "risk_register", None) or []) if study is not None else []
    monitors = await _fdir_monitors(study_id)
    lang_text = lambda v: (v.get("en") if isinstance(v, dict) else str(v or ""))  # noqa: E731
    counters: dict[str, int] = {}
    for r in existing:
        sub = r.get("subsystem") or "SC"
        counters[sub] = max(counters.get(sub, 0), int(str(r.get("code") or "0").rsplit("-", 1)[-1] or 0)
                            if str(r.get("code") or "").rsplit("-", 1)[-1].isdigit() else 0)
    rows = []
    for m in sorted(sk["rows"], key=lambda x: (x["element_id"], x["library_id"])):
        if (m["element_id"], m["library_id"]) in have:
            continue
        e = idx.get(m["element_id"]) or {}
        sub_el = _subsystem(e, idx) if e else None
        sub = SUBSYSTEM_CODE.get((sub_el or {}).get("subsystem_domain") or "", "SC")
        counters[sub] = counters.get(sub, 0) + 1
        s, o, d = int(m["severity"]), int(m["occurrence"]), int(m["detection"])
        fdir = monitors.get(m["element_id"], "")
        rows.append({
            "code": f"FM-{sub}-{counters[sub]:02d}", "element_id": m["element_id"], "subsystem": sub,
            "item": m["component"], "function": "", "failure_mode": lang_text(m["mode"]), "cause": lang_text(m["cause"]),
            "local_effect": lang_text(m["local_effect"]), "system_effect": lang_text(m["system_effect"]),
            "severity": s, "probability": o, "criticality": s * o,
            "detection": (f"FDIR monitor {fdir}" if fdir else "housekeeping telemetry / ground check")
                         + f" (D={d})",
            "fdir_ref": fdir, "mitigation": lang_text(m["mitigation"]),
            "risk_ids_json": _risk_links(m["library_type"], m["component"], risks) or None,
            "single_point": bool(m["single_point"]), "status": "open", "origin": "proposed",
            "data_json": {"library_id": m["library_id"], "library_type": m["library_type"], "detection_score": d,
                          "rpn": m["rpn"], "fr": {k: (m[k].get("fr") if isinstance(m[k], dict) else "")
                                                  for k in ("mode", "cause", "local_effect", "system_effect", "mitigation")}},
            "order": len(existing) + len(rows),
        })
    await sr.insert_rows(FmeaRow, study_id, rows, prefix="fm")
    out = await get(study_id)
    return {"added": len(rows), **out}


FMEA_EDITABLE = ("code", "element_id", "subsystem", "item", "function", "failure_mode", "cause", "local_effect",
                 "system_effect", "severity", "probability", "detection", "fdir_ref", "mitigation", "risk_ids_json",
                 "single_point", "status")


def _fmea_fields(body: dict) -> dict:
    f = {k: body[k] for k in FMEA_EDITABLE if k in body}
    if "risk_ids" in body and "risk_ids_json" not in f:
        f["risk_ids_json"] = list(body.get("risk_ids") or [])
    for k in ("severity", "probability"):
        if k in f and f[k] is not None:
            f[k] = max(1, min(5, int(f[k])))
    return f


async def create_fmea(study_id: str, body: dict) -> dict:
    f = _fmea_fields(body)
    if f.get("severity") and f.get("probability"):
        f["criticality"] = int(f["severity"]) * int(f["probability"])
    f["origin"] = "user"
    return (await sr.insert_rows(FmeaRow, study_id, [f], prefix="fm"))[0]


async def update_fmea(row: dict, body: dict) -> dict:
    f = _fmea_fields(body)
    s = f.get("severity", row.get("severity"))
    p = f.get("probability", row.get("probability"))
    if s and p:
        f["criticality"] = int(s) * int(p)
    f["origin"] = "user"
    return await sr.update_row(FmeaRow, row["id"], f) or row


# ───────────────────────────────────────────────────────── evidence for the gates

async def evidence(study_id: str) -> dict[str, Any]:
    """PDR-EC-05 (wired by R): the reliability over the mission-success horizon against the target,
    and an FMEA covering every space subsystem with its critical rows linked to FDIR or a risk."""
    data = await get(study_id)
    res = data["result"] or {}
    fmea = data["fmea"]
    subs_with_blocks = {b.get("subsystem") for b in data["blocks"] if b.get("subsystem") not in ("SC", "HAR")}
    covered = {r.get("subsystem") for r in fmea}
    missing_subs = sorted(s for s in subs_with_blocks if s not in covered)
    crit = [r for r in fmea if (r.get("criticality") or 0) >= CRITICAL]
    unlinked = [r["code"] for r in crit if not (r.get("fdir_ref") or r.get("risk_ids_json") or (r.get("mitigation") or "").strip())]
    rel_ok = res.get("meets_target")
    ok = bool(data["blocks"]) and rel_ok is not False and bool(fmea) and not missing_subs and not unlinked
    reasons = []
    if not data["blocks"]:
        reasons.append("no reliability block diagram (run the reliability analysis)")
    elif rel_ok is False:
        reasons.append(res.get("evidence", ""))
    if not fmea:
        reasons.append("no FMEA worksheet")
    if missing_subs:
        reasons.append("FMEA misses " + ", ".join(missing_subs))
    if unlinked:
        reasons.append("critical rows without FDIR, risk or mitigation: " + ", ".join(unlinked[:6]))
    return {"study_id": study_id, "ok": ok, "reliability": res.get("mission_reliability"),
            "target": res.get("target"), "horizon_months": (res.get("horizon") or {}).get("success_horizon_months"),
            "exposure_months": (res.get("horizon") or {}).get("exposure_months"),
            "evidence": res.get("evidence") or "", "fmea_rows": len(fmea), "critical_rows": len(crit),
            "fmea_missing_subsystems": missing_subs, "critical_unlinked": unlinked, "reasons": reasons}
