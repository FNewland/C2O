"""SpaceCDF — the ConOps mode model and the budgets per mode (Nov 2026, rules MO-01..06, EB-01..06).

Pure functions over plain dicts (no I/O apart from the cached ``configs/mode_rules.yaml``):

* ``unit_class`` / ``propose_member``  — MO-01 / EB-02: the power state, power, data rate of a
  unit in a mode, from the part's ``power_modes_w`` (KB) or the per-class defaults (C2O default),
  with source, rationale and an inputs hash (rule 13 staleness);
* ``dissipation_w``                     — EB-05: heat per unit per mode (power − RF out);
* ``energy_balance``                    — MO-02: per-mode energy per orbit (eclipse fraction from
  the orbit), DoD, the operational-orbit mix and the sustainable duty of short modes;
* ``data_chain``                        — EB-03 / MO-03: generation → storage → downlink capacity
  from the contact plan and the link-budget rate;
* ``validate_machine``                  — MO-05 / MO-06: unreachable modes, modes without exit,
  autonomous transitions without a monitored guard;
* ``equipment_budgets``                 — equipment selection → every budget (mass, power by mode,
  data, cost, dissipation, link) with the maturity margins of ``margin_policy`` and the system
  margin of the gate ladder (one source, F2/F3).

Every number carries ``standard_ref`` / ``c2o_default`` like the other rule engines.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from . import rule_config as rc
from .rule_inputs import kb_component, perf, qty, space_hardware

CONFIG = "mode_rules"
STATES = ("off", "standby", "nominal", "peak")


def cfg() -> dict[str, Any]:
    return rc.load(CONFIG)


def ref(node: dict, c: dict | None = None) -> dict[str, Any]:
    """``{standard_ref, c2o_default}`` of a config node."""
    r = rc.ref_of(c or cfg(), node)
    return {"standard_ref": r["standard_ref"], "c2o_default": r["c2o_default"]}


def validate_config(c: dict | None = None) -> list[str]:
    """Schema check of mode_rules.yaml (errors as text; empty = valid)."""
    errs: list[str] = []
    try:
        c = c or cfg()
    except rc.RuleConfigError as exc:
        return [str(exc)]
    known = set((c.get("sources") or {}).keys())
    keys = {m.get("key") for m in (c.get("template") or {}).get("modes") or []}
    for m in (c.get("template") or {}).get("modes") or []:
        if m.get("kind") not in c.get("mode_kinds", []):
            errs.append(f"template mode {m.get('key')}: unknown kind {m.get('kind')}")
        if m.get("pointing") not in c.get("pointing_kinds", []):
            errs.append(f"template mode {m.get('key')}: unknown pointing {m.get('pointing')}")
    for t in (c.get("template") or {}).get("transitions") or []:
        if t.get("from") not in keys or t.get("to") not in keys:
            errs.append(f"template transition {t}: unknown mode")
        if t.get("trigger") not in c.get("trigger_kinds", []):
            errs.append(f"template transition {t}: unknown trigger")
    for cls, row in ((c.get("states") or {}).get("classes") or {}).items():
        for kind, st in row.items():
            if st not in STATES:
                errs.append(f"states.classes.{cls}.{kind}: unknown state {st}")
    for fn in (c.get("fdir") or {}).get("by_type", {}).values():
        if fn.get("action") not in {f["id"] for f in c["fdir"]["function_catalogue"]}:
            errs.append(f"fdir action {fn.get('action')} not in the function catalogue")

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            s = node.get("source")
            if isinstance(s, str) and s not in known:
                errs.append(f"{path}: unknown source {s}")
            for k, v in node.items():
                if k != "sources":
                    walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
    walk(c, "mode_rules")
    return errs


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _num(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    return float(v) if isinstance(v, (int, float)) else None


# ───────────────────────────────────────────────────────────── unit classes and states

def unit_class(e: dict, c: dict | None = None) -> str:
    """The mode-rules class of a unit: KB category, then name keyword, then domain."""
    c = c or cfg()
    kb = kb_component(e) or {}
    cat = kb.get("category") or (e.get("kb_spec") or {}).get("category")
    name = str(e.get("name") or "").lower()
    dom = e.get("subsystem_domain")
    rules = c["states"]["match"]
    if cat:
        for r in rules:
            if cat in (r.get("kb") or []):
                return r["class"]
    for r in rules:
        if any(k in name for k in (r.get("keywords") or [])):
            return r["class"]
    for r in rules:
        if dom and dom in (r.get("domains") or []):
            return r["class"]
    return "generic"


def _power_modes(e: dict) -> dict | None:
    kb = kb_component(e) or {}
    pm = (e.get("kb_spec") or {}).get("power_modes_w") or kb.get("power_modes_w") or perf(e).get("power_modes_w")
    return pm if isinstance(pm, dict) else None


def member_inputs(e: dict, mode_kind: str) -> dict[str, Any]:
    """The facts a mode-power proposal depends on (hashed for staleness, rule 13)."""
    return {"kind": mode_kind, "kb": e.get("kb_component_id"), "kb_hash": (e.get("kb_spec") or {}).get("kb_hash"),
            "p_avg": e.get("power_avg_w"), "p_peak": e.get("power_peak_w"), "qty": qty(e),
            "rate": perf(e).get("data_rate_bps"), "name": e.get("name"), "domain": e.get("subsystem_domain")}


def propose_member(e: dict, mode_kind: str, c: dict | None = None) -> dict[str, Any]:
    """MO-01 / EB-02: proposed row of the mode × element matrix for one unit.

    Returns ``{power_state, power_w_in_mode (per unit × quantity), duty_cycle_percent,
    data_rate_bps, source_ref, c2o_default, rationale{en,fr}, inputs_hash, unit_class}``.
    """
    c = c or cfg()
    st_cfg = c["states"]
    cls = unit_class(e, c)
    row = st_cfg["classes"].get(cls) or st_cfg["classes"]["generic"]
    state = row.get(mode_kind) or row.get("nominal") or "nominal"
    n = qty(e)
    avg = _num(e.get("power_avg_w")) or 0.0
    peak = _num(e.get("power_peak_w"))
    pm = _power_modes(e)
    pm_key = ((st_cfg.get("power_mode_keys") or {}).get(cls) or {}).get(state, state)
    cls_w = _num(((st_cfg.get("class_power_w") or {}).get(cls) or {}).get(state))
    kb_w = _num((kb_component(e) or {}).get("power_w")) or _num((e.get("kb_spec") or {}).get("power_w"))
    if pm and _num(pm.get(pm_key)) is not None:
        p = float(pm[pm_key])
        src, c2o = "KB power_modes_w", False
        why_en = f"{pm_key} power of the part from the knowledge base"
        why_fr = f"puissance « {pm_key} » de la pièce, base de connaissances"
    elif pm_key != state and state != "off" and (kb_w or avg or peak):
        # e.g. a de-orbit device: the KB power is the release actuation, drawn only in the disposal mode
        p = float(kb_w or peak or avg)
        src, c2o = "KB power_w", False
        why_en = f"{pm_key} power of the part (KB power_w), drawn only in {mode_kind} mode"
        why_fr = f"puissance « {pm_key} » de la pièce (KB power_w), appelée seulement en mode {mode_kind}"
    elif cls_w is not None and not avg and not peak:
        p = cls_w
        r = ref(st_cfg, c)
        src, c2o = r["standard_ref"], True
        why_en = f"{cls} units draw about {cls_w:g} W when {state} (C2O default)"
        why_fr = f"les unités {cls} consomment environ {cls_w:g} W à l’état « {state} » (défaut C2O)"
    else:
        if state == "off":
            p = 0.0
        elif state == "standby":
            p = avg * float(st_cfg["standby_factor"])
        elif state == "peak":
            p = peak if peak else avg * float(st_cfg["peak_factor"])
        else:
            p = avg
        r = ref(st_cfg, c)
        src, c2o = r["standard_ref"], True
        why_en = f"{cls} units are {state} in {mode_kind} mode (C2O default state table)"
        why_fr = f"les unités {cls} sont « {state} » en mode {mode_kind} (table d’états par défaut C2O)"
    rate = 0.0
    prod = (c["states"].get("produces") or {}).get(cls)
    if prod and state in ("nominal", "peak"):
        rate = _num(perf(e).get("data_rate_bps")) or (((_num(perf(e).get("data_rate_mbps")) or 0.0) * 1e6) or None) \
            or float(prod.get("default_bps") or 0.0)
        rate *= n
    return {"power_state": state, "power_w_in_mode": round(p * n, 4), "duty_cycle_percent": 100.0,
            "data_rate_bps": round(rate, 1), "source_ref": src, "c2o_default": c2o,
            "rationale": {"en": why_en, "fr": why_fr}, "unit_class": cls,
            "inputs_hash": _hash(member_inputs(e, mode_kind))}


def proposal_units(elements: list[dict]) -> list[dict]:
    """The units that get a row in the mode × element matrix: space hardware leaves."""
    hw = space_hardware(elements)
    parents = {e.get("parent_id") for e in hw}
    return [e for e in hw if e.get("element_type") in ("component", "subsystem") and e["id"] not in parents]


# ───────────────────────────────────────────────────────────── thermal dissipation (EB-05)

def rf_out_w(e: dict, state: str | None, power_w: float, c: dict | None = None) -> float:
    """RF power radiated by a transmitter in a transmitting state (W); 0 for other units."""
    c = c or cfg()
    if state != "peak" or unit_class(e, c) != "transmitter" or power_w <= 0:
        return 0.0
    kb = kb_component(e) or {}
    tx = _num(perf(e).get("tx_power_w")) or _num((kb.get("performance") or {}).get("tx_power_w"))
    if tx is not None:
        return min(tx * qty(e), power_w)
    return power_w * float(c["thermal"]["rf_out_fraction_default"]["value"])


def dissipation_w(e: dict, member: dict, c: dict | None = None) -> float:
    """Heat dissipated by the unit in the mode (W, duty-averaged): power − RF out, or the override."""
    if _num(member.get("dissipation_w")) is not None:
        return float(member["dissipation_w"])
    p = float(member.get("power_w") if member.get("power_w") is not None else member.get("power_w_in_mode") or 0.0)
    duty = member.get("duty")
    if duty is None:
        duty = float(member.get("duty_cycle_percent") or 100.0) / 100.0
    state = member.get("state") or member.get("power_state")
    return max(0.0, (p - rf_out_w(e, state, p, c)) * float(duty))


def dissipation_cases(elements: list[dict], modes: list[Any], c: dict | None = None) -> dict[str, dict]:
    """``{element_id: {hot_w, cold_w, by_mode{mode_id: W}}}`` from the mode members.

    Hot case = the largest dissipation over the operational modes; cold case = the smallest
    over the fallback modes (safe/survival) if any, else over every mode. Units that appear in
    no mode are absent (the thermal analysis keeps its own estimate for them).
    """
    c = c or cfg()
    by_id = {e["id"]: e for e in elements}
    out: dict[str, dict] = {}
    cold_kinds = {"safe", "survival"}
    have_cold = any(_attr(m, "kind") in cold_kinds for m in modes)
    for m in modes:
        mid, kind = _attr(m, "id"), _attr(m, "kind")
        for mem in _attr(m, "members") or []:
            e = by_id.get(mem.get("element_id"))
            if e is None:
                continue
            w = dissipation_w(e, mem, c)
            row = out.setdefault(e["id"], {"by_mode": {}, "hot_w": 0.0, "cold_w": None})
            row["by_mode"][mid] = round(w, 4)
            row["hot_w"] = max(row["hot_w"], w)
            if not have_cold or kind in cold_kinds:
                row["cold_w"] = w if row["cold_w"] is None else min(row["cold_w"], w)
    for row in out.values():
        row["hot_w"] = round(row["hot_w"], 4)
        row["cold_w"] = round(row["cold_w"] or 0.0, 4)
    return out


def _attr(m: Any, k: str) -> Any:
    return m.get(k) if isinstance(m, dict) else getattr(m, k, None)


# ───────────────────────────────────────────────────────────── margins helpers

def _maturity_pct(e: dict) -> float:
    from .margin_policy import maturity_percent
    return maturity_percent(e, resource="power")   # wave 3 step 0: the unit's power maturity


def mode_power(mode: Any, by_id: dict[str, dict]) -> dict[str, float]:
    """CBE and with-maturity power of a mode (W, duty-averaged)."""
    cbe = mat = 0.0
    for mem in _attr(mode, "members") or []:
        e = by_id.get(mem.get("element_id"))
        if e is None:
            continue
        p = float(mem.get("power_w") or 0.0) * float(mem.get("duty") if mem.get("duty") is not None else 1.0)
        cbe += p
        mat += p * (1 + _maturity_pct(e) / 100)
    if not (_attr(mode, "members") or []):
        cbe = mat = float(_attr(mode, "power_w") or 0.0)   # a mode with only a total
    return {"cbe_w": cbe, "with_maturity_w": mat}


# ───────────────────────────────────────────────────────────── energy balance (MO-02)

MIX_KINDS = ("nominal", "imaging", "downlink")


def in_operational_mix(m: Any) -> bool:
    """A mode of the operational orbit: kind nominal / imaging / downlink with a share of orbit,
    or a custom mode of the nominal phase with 0 < share < 1."""
    f = _num(_attr(m, "orbit_fraction")) or 0.0
    kind = _attr(m, "kind") or "custom"
    if kind in MIX_KINDS:
        return f > 0
    phase = _attr(m, "phase")
    return kind == "custom" and (phase or "nominal") == "nominal" and 0 < f < 1


def _gen_factor(pointing: str | None, c: dict) -> float:
    vals = c["energy"]["array_pointing_factor"]["values"]
    return float(vals.get(str(pointing or "nadir"), vals.get("nadir", 0.65)))


def energy_balance(modes: list[Any], elements: list[dict], *, period_s: float, eclipse_fraction: float,
                   sa_power_eol_w: float | None, battery_wh: float | None, system_margin_percent: float,
                   battery_efficiency: float | None = None, max_dod_percent: float | None = None,
                   c: dict | None = None) -> dict[str, Any]:
    """Per-mode power and energy per orbit, battery DoD, the operational orbit and short-mode duty.

    Power per mode = Σ unit power × duty × (1 + maturity) × (1 + system margin) — the convention of
    margin_policy (percent added to the nominal). Generation = sun-pointed EOL array power ×
    the attitude factor of the mode's pointing, over the sunlit arc. Eclipse energy comes from
    the battery through the round-trip efficiency.
    """
    c = c or cfg()
    en = c["energy"]
    eta = float(battery_efficiency or en["battery_round_trip_efficiency"]["value"])
    dod_lim = float(max_dod_percent or en["max_dod_percent"]["value"])
    T = float(period_s or 5700.0)
    e = min(max(float(eclipse_fraction if eclipse_fraction is not None else 0.35), 0.0), 0.95)
    t_sun, t_ecl = (1 - e) * T, e * T
    by_id = {x["id"]: x for x in elements}
    sysf = 1 + float(system_margin_percent) / 100
    warnings: list[str] = []
    if not sa_power_eol_w:
        warnings.append("no EOL array power (power.sa_power_eol_w or a solar array part): generation unknown")
    if not battery_wh:
        warnings.append("no battery capacity (power.battery_capacity_wh or a battery part): DoD unknown")

    rows = []
    load_w: dict[str, float] = {}
    cbe_w: dict[str, float] = {}
    for m in modes:
        pw = mode_power(m, by_id)
        p_tot = pw["with_maturity_w"] * sysf
        load_w[_attr(m, "id")] = p_tot
        cbe_w[_attr(m, "id")] = pw["cbe_w"]
        f = _gen_factor(_attr(m, "pointing"), c)
        gen = (sa_power_eol_w or 0.0) * f
        e_gen = gen * t_sun / 3600
        e_load = p_tot * T / 3600
        e_need = p_tot * t_sun / 3600 + p_tot * t_ecl / 3600 / eta
        e_batt = p_tot * t_ecl / 3600
        dod = 100 * e_batt / battery_wh if battery_wh else None
        bal = e_gen - e_need if sa_power_eol_w else None
        status = "not_evaluated"
        if bal is not None:
            status = "pass" if bal >= 0 and (dod is None or dod <= dod_lim) else "fail"
        rows.append({
            "mode_id": _attr(m, "id"), "name": _attr(m, "name"), "kind": _attr(m, "kind") or "",
            "pointing": _attr(m, "pointing"), "sunlit_only": bool(_attr(m, "sunlit_only")),
            "power_cbe_w": round(pw["cbe_w"], 3), "power_with_maturity_w": round(pw["with_maturity_w"], 3),
            "power_total_w": round(p_tot, 3), "generation_sunlit_w": round(gen, 3), "array_factor": f,
            "energy_generated_wh": round(e_gen, 3), "energy_load_wh": round(e_load, 3),
            "energy_needed_wh": round(e_need, 3), "balance_wh": round(bal, 3) if bal is not None else None,
            "battery_drawn_wh": round(e_batt, 3), "dod_percent": round(dod, 2) if dod is not None else None,
            "held_full_orbit": (_attr(m, "kind") or "") in en["full_orbit_kinds"],
            "status": status,
        })

    # Operational orbit: the nominal-phase mix by orbit_fraction (sunlit-only modes in the sun):
    # nominal, imaging and downlink modes, plus custom modes of the nominal phase with a share of
    # an orbit (W1.03: e.g. an exploratory night acquisition mode).
    mix = [(m, float(_attr(m, "orbit_fraction") or 0.0)) for m in modes if in_operational_mix(m)]

    def mix_balance(fracs: list[tuple[Any, float]]) -> dict[str, float] | None:
        tot = sum(f for _, f in fracs)
        if tot <= 0:
            return None
        fracs = [(m, f / tot) for m, f in fracs]
        sun_only = [(m, f * T) for m, f in fracs if _attr(m, "sunlit_only")]
        others = [(m, f * T) for m, f in fracs if not _attr(m, "sunlit_only")]
        s_used = min(sum(t for _, t in sun_only), t_sun)
        s_rem = max(t_sun - s_used, 0.0)
        r = sum(t for _, t in others) or 1.0
        e_gen = e_need = e_batt = 0.0
        for m, t in sun_only:
            e_gen += (sa_power_eol_w or 0.0) * _gen_factor(_attr(m, "pointing"), c) * t / 3600
            e_need += load_w[_attr(m, "id")] * t / 3600
        for m, t in others:
            ts = t * s_rem / r
            te = t - ts
            e_gen += (sa_power_eol_w or 0.0) * _gen_factor(_attr(m, "pointing"), c) * ts / 3600
            e_need += load_w[_attr(m, "id")] * (ts + te / eta) / 3600
            e_batt += load_w[_attr(m, "id")] * te / 3600
        return {"generated_wh": e_gen, "needed_wh": e_need, "battery_drawn_wh": e_batt, "balance_wh": e_gen - e_need}

    ops = None
    duty = []
    if mix:
        b = mix_balance(mix)
        if b:
            dod = 100 * b["battery_drawn_wh"] / battery_wh if battery_wh else None
            ops = {"modes": [{"mode_id": _attr(m, "id"), "name": _attr(m, "name"), "orbit_fraction": f} for m, f in mix],
                   "generated_wh": round(b["generated_wh"], 3), "needed_wh": round(b["needed_wh"], 3),
                   "balance_wh": round(b["balance_wh"], 3) if sa_power_eol_w else None,
                   "orbit_average_load_w": round(sum(load_w[_attr(m, "id")] * f for m, f in mix) / (sum(f for _, f in mix) or 1), 3),
                   # wave 3 (3.H3): the current best estimate over the mix (no maturity, no system margin)
                   "orbit_average_cbe_w": round(sum(cbe_w[_attr(m, "id")] * f for m, f in mix) / (sum(f for _, f in mix) or 1), 3),
                   "share_total": round(sum(f for _, f in mix), 4),
                   "dod_percent": round(dod, 2) if dod is not None else None,
                   "status": ("not_evaluated" if not sa_power_eol_w else
                              "pass" if b["balance_wh"] >= 0 and (dod is None or dod <= dod_lim) else "fail")}
        background = next((m for m, _ in mix if (_attr(m, "kind") or "") == "nominal"), None)
        if background is not None and sa_power_eol_w:
            for m, _f in mix:
                if m is background:
                    continue
                b0 = mix_balance([(background, 1.0)])
                b1 = mix_balance([(m, 1.0)]) if not _attr(m, "sunlit_only") else None
                # sustainable duty x: balance(x) = (1-x)·b0 + x·b1 is linear; sunlit-only modes are
                # limited to the sunlit arc
                lim = (1 - e) if _attr(m, "sunlit_only") else 1.0
                if _attr(m, "sunlit_only"):
                    bx = mix_balance([(background, 1 - lim), (m, lim)])
                    b1v = (bx["balance_wh"] - (1 - lim) * b0["balance_wh"]) / lim if bx and lim > 0 else 0.0
                else:
                    b1v = b1["balance_wh"] if b1 else 0.0
                b0v = b0["balance_wh"] if b0 else 0.0
                if b0v < 0:
                    x = 0.0
                elif b1v >= 0:
                    x = lim
                else:
                    x = min(lim, b0v / (b0v - b1v))
                duty.append({"mode_id": _attr(m, "id"), "name": _attr(m, "name"),
                             "sustainable_fraction": round(x, 4), "planned_fraction": _attr(m, "orbit_fraction"),
                             "status": "pass" if (_attr(m, "orbit_fraction") or 0) <= x + 1e-9 else "fail"})

    return {
        "orbit": {"period_s": T, "eclipse_fraction": e, "sunlit_s": round(t_sun, 1), "eclipse_s": round(t_ecl, 1)},
        "inputs": {"sa_power_eol_w": sa_power_eol_w, "battery_capacity_wh": battery_wh,
                   "battery_efficiency": eta, "max_dod_percent": dod_lim,
                   "system_margin_percent": float(system_margin_percent),
                   **{f"{k}_ref": ref(en[k], c) for k in ("battery_round_trip_efficiency", "max_dod_percent")},
                   "array_factor_ref": ref(en["array_pointing_factor"], c)},
        "modes": rows, "operational_orbit": ops, "sustainable_duty": duty, "warnings": warnings,
    }


# ───────────────────────────────────────────────────────────── data chain (EB-03 / MO-03)

def storage_capacity_gb(elements: list[dict]) -> tuple[float | None, list[str]]:
    """On-board storage (GB): Σ storage_gb of OBC / mass-memory / payload parts (element, then KB)."""
    tot, used = 0.0, []
    for e in space_hardware(elements):
        kb = (kb_component(e) or {}).get("performance") or {}
        for src in (perf(e), kb):
            v = _num(src.get("storage_gb")) or _num(src.get("mass_memory_gb"))
            if v:
                tot += v * qty(e)
                used.append(e["id"])
                break
    return (tot if tot > 0 else None), used


def data_chain(modes: list[Any], *, period_s: float, link_rate_bps: float, stations: list[dict],
               storage_gb: float | None, storage_margin_percent: float, budget: dict | None = None,
               c: dict | None = None) -> dict[str, Any]:
    """Generation per mode → per day (operational orbit) → storage need vs capacity → downlink capacity.

    ``budget`` (``services/data_budget.compute``): housekeeping from the study's SIDs — stored HK
    per mode is generated all orbit, real-time HK uses the channel during contact — and the
    capacity from the **union** of the station contacts (overlapping passes count once) after
    framing, acquisition and availability. Without a budget, or without SIDs, the
    ``housekeeping_bps`` constant is used and flagged ``not designed``.
    ``stations``: ``[{name, contact_min_per_day, margin_db, status}]`` (per-station rows).
    """
    c = c or cfg()
    d = c["data"]
    hk_const = float(d["housekeeping_bps"]["value"])
    eff = float(d["protocol_efficiency"]["value"])
    buffer_days = float(d["buffer_days"]["value"])
    min_margin = float(d["min_link_margin_db"]["value"])
    T = float(period_s or 5700.0)
    orbits_per_day = 86400.0 / T
    designed = bool(budget) and budget.get("status") in ("designed", "legacy")
    hk_by_mode = {r["id"]: r for r in (budget or {}).get("modes") or []}
    per_mode = []
    for m in modes:
        pay = float(_attr(m, "data_rate_bps") or 0.0)
        hkr = hk_by_mode.get(_attr(m, "id"))
        hk_st = float(hkr["store_bps"]) if (designed and hkr) else hk_const
        rate = pay + hk_st
        per_mode.append({"mode_id": _attr(m, "id"), "name": _attr(m, "name"), "kind": _attr(m, "kind") or "",
                         "payload_bps": round(pay, 1), "hk_stored_bps": round(hk_st, 1),
                         "hk_realtime_bps": round(float(hkr["rt_bps"]), 1) if (designed and hkr) else None,
                         "generation_bps": round(rate, 1), "orbit_fraction": _attr(m, "orbit_fraction"),
                         "in_mix": in_operational_mix(m), "per_orbit_mb": round(rate * T / 8e6, 3)})
    mix = [p for m, p in zip(modes, per_mode) if in_operational_mix(m)]
    tot = sum(p["orbit_fraction"] for p in mix) or 0.0
    if mix:
        bits_orbit = sum(p["generation_bps"] * p["orbit_fraction"] / tot * T for p in mix)
    else:
        bits_orbit = (max((p["generation_bps"] for p in per_mode), default=hk_const)) * T
    gen_gb_day = bits_orbit * orbits_per_day / 8e9
    if designed:
        gen_gb_day += float(budget["stored"]["events_mb_per_day"]) / 1000.0

    # Wave 3 (3.H2): with a data budget, every capacity figure applies what the ground closure
    # applies: the frame efficiency, the acquisition time of each window and the availability.
    fr_b = (budget or {}).get("framing") or {}
    acq_s = float(fr_b.get("acquisition_s") or 0.0) if budget else 0.0
    avail = float(fr_b.get("availability") or 1.0) if budget else 1.0
    st_eff = float(fr_b.get("frame_efficiency") or eff) if budget else eff
    st_rows = []
    contact_sum = 0.0
    for s in stations:
        ok = s.get("margin_db") is None or float(s["margin_db"]) >= 0
        ok = ok and s.get("status") != "excluded"
        low = s.get("margin_db") is not None and float(s["margin_db"]) < min_margin
        mins = float(s.get("contact_min_per_day") or 0.0) if ok else 0.0
        contact_sum += mins
        usable = max(0.0, mins - float(s.get("contacts_per_day") or 0.0) * acq_s / 60.0) * avail
        st_rows.append({**s, "used": ok, "low_margin": bool(low and ok), "usable_min_per_day": round(usable, 2),
                        "capacity_gb_per_day": round(usable * 60 * link_rate_bps * st_eff / 8e9, 4)})
    rt_mb = 0.0
    total_mb = alloc_mb = None
    if budget and budget.get("capacity"):
        cap = budget["capacity"]
        contact_min = float(cap["union_min_per_day"])
        rt_mb = float(next((x["rt_hk_mb"] for x in budget.get("cases") or [] if x["id"] == "C1"), 0.0)) if designed else 0.0
        total_mb = float(cap["capacity_mb_per_day"])
        alloc_mb = cap.get("allocatable_mb_per_day")
        cap_gb_day = max(0.0, total_mb - rt_mb) / 1000.0
        eff_used = float(fr_b.get("frame_efficiency") or eff)
        cap_src = "union"
    else:
        contact_min = contact_sum
        cap_gb_day = contact_min * 60 * link_rate_bps * eff / 8e9
        eff_used = eff
        cap_src = "sum_of_stations"
    # What goes down the link: with designed payload products (TM/TC → payload products) the
    # science files after compression on the channel plus the stored HK, not the frames the
    # camera writes at its interface rate during an acquisition (those stay on the payload store
    # and are sized there). Without products, every mode's data rate counts (the older model).
    sci = (budget or {}).get("science") or {}
    products = bool(sci.get("products")) and sci.get("on_channel_mb_per_day") is not None
    acquired_gb_day = gen_gb_day
    if products:
        stored_mb = float(budget["stored"]["mb_per_day"]) if designed else hk_const * 86400 / 8e6
        to_dl_gb_day = (float(sci["on_channel_mb_per_day"]) + stored_mb) / 1000.0
        gen_basis = "products"
    else:
        to_dl_gb_day = gen_gb_day
        gen_basis = "modes"
    need_gb = to_dl_gb_day * buffer_days
    need_with_margin = need_gb * (1 + storage_margin_percent / 100)
    growth = to_dl_gb_day - cap_gb_day
    gen_gb_day = to_dl_gb_day
    days_to_full = None
    if storage_gb and growth > 0:
        days_to_full = round(storage_gb / growth, 2)
    checks = []
    checks.append({"id": "DC-DOWNLINK", "label": {"en": "Downlink capacity covers the data generated",
                                                   "fr": "La capacité de transmission au sol couvre les données produites"},
                   "status": "pass" if cap_gb_day >= gen_gb_day else ("fail" if stations else "not_evaluated"),
                   "value": round(cap_gb_day, 4), "limit": round(gen_gb_day, 4), "unit": "GB/day",
                   **ref(d["protocol_efficiency"], c)})
    checks.append({"id": "DC-STORAGE", "label": {"en": "Storage holds the buffer with margin",
                                                  "fr": "Le stockage contient la réserve avec marge"},
                   "status": ("not_evaluated" if not storage_gb else "pass" if storage_gb >= need_with_margin else "fail"),
                   "value": storage_gb, "limit": round(need_with_margin, 4), "unit": "GB",
                   **ref(d["buffer_days"], c)})
    if not designed:
        checks.append({"id": "DC-HK-NOT-DESIGNED", "label": {
            "en": f"Housekeeping is the {hk_const / 1000:g} kbit/s default: no SID is designed in TM/TC",
            "fr": f"La télémesure de servitude est la valeur par défaut de {hk_const / 1000:g} kbit/s : aucun SID n’est conçu dans TM/TC"},
            "status": "warn", "value": hk_const, "limit": None, "unit": "bit/s", **ref(d["housekeeping_bps"], c)})
    if any(r["low_margin"] for r in st_rows):
        checks.append({"id": "DC-LINK-MARGIN", "label": {"en": f"Link margin ≥ {min_margin:g} dB at every station used",
                                                         "fr": f"Marge de liaison ≥ {min_margin:g} dB à chaque station utilisée"},
                       "status": "warn", "value": min(r["margin_db"] for r in st_rows if r["low_margin"]),
                       "limit": min_margin, "unit": "dB", **ref(d["min_link_margin_db"], c)})
    hk = {"designed": designed, "source": "TM/TC SIDs" if designed else "mode_rules.data.housekeeping_bps (not designed)",
          "stored_mb_per_day": round(float(budget["stored"]["mb_per_day"]), 3) if designed else round(hk_const * 86400 / 8e6, 3),
          "realtime_mb_per_day": round(rt_mb, 3),
          "realtime_contact_bps": (budget or {}).get("realtime", {}).get("full_designed_bps") if designed else None,
          "realtime_allocation_bps": (budget or {}).get("realtime", {}).get("full_allocation_bps") if designed else None}
    return {
        "per_mode": per_mode, "housekeeping_bps": hk_const if not designed else round(float(budget["stored"]["mix_bps"]), 1),
        "housekeeping": hk, "orbits_per_day": round(orbits_per_day, 3),
        "generated_gb_per_day": round(gen_gb_day, 4),
        # "products": generated = science files on the channel + stored HK; "acquired" is what the
        # payload writes at its interface rate over the operational mix (mode data rates)
        "generation_basis": gen_basis, "acquired_gb_per_day": round(acquired_gb_day, 4),
        "storage": {"capacity_gb": storage_gb, "buffer_days": buffer_days, "need_gb": round(need_gb, 4),
                    "need_with_margin_gb": round(need_with_margin, 4), "margin_percent": storage_margin_percent},
        "downlink": {"rate_bps": link_rate_bps, "protocol_efficiency": round(eff_used, 4), "contact_min_per_day": round(contact_min, 2),
                     "sum_of_stations_min_per_day": round(contact_sum, 2), "contact_basis": cap_src,
                     "capacity_gb_per_day": round(cap_gb_day, 4), "stations": st_rows,
                     # the figure above is what is LEFT for stored data after the real-time HK of the
                     # passes; the data budget's total channel capacity is beside it (labelled in the UI)
                     "capacity_basis": "after_realtime_hk" if rt_mb > 0 else "total",
                     "total_capacity_mb_per_day": round(total_mb, 2) if total_mb is not None else round(cap_gb_day * 1000.0, 2),
                     "remaining_after_realtime_hk_mb_per_day": round(cap_gb_day * 1000.0, 2),
                     "allocatable_mb_per_day": alloc_mb,
                     "allocatable_percent": (budget or {}).get("capacity", {}).get("allocatable_percent"),
                     "acquisition_s": acq_s if budget else None, "availability": avail if budget else None,
                     "realtime_hk_mb_per_day": round(rt_mb, 3),
                     "usable_min_per_day": (budget or {}).get("capacity", {}).get("usable_min_per_day")},
        "backlog_growth_gb_per_day": round(growth, 4), "days_to_full": days_to_full,
        "checks": checks,
    }


# ───────────────────────────────────────────────────────────── mode shares from the ConOps (3.H3)

def share_inputs(products: dict | None = None, c: dict | None = None) -> dict[str, float]:
    """Imaging-share inputs: the payload products row (TM/TC) first, then ``mode_rules.shares``."""
    c = c or cfg()
    sh = c.get("shares") or {}
    p = products or {}

    def pick(k: str, dflt: float) -> float:
        v = _num(p.get(k))
        return float(v) if v is not None and v >= 0 else float(_num((sh.get(k) or {}).get("value")) or dflt)
    return {"acquisitions_per_orbit": pick("acquisitions_per_orbit", 1.0), "acquisition_s": pick("acquisition_s", 240.0),
            "settle_s": pick("settle_s", 60.0)}


def share_proposals(modes: list[Any], *, union_min_per_day: float | None, period_s: float,
                    products: dict | None = None, stations: list[str] | None = None,
                    c: dict | None = None) -> list[dict[str, Any]]:
    """The proposed share of the operational orbit of every mode of the mix (A4), with provenance.

    * downlink kind: union of the station passes ÷ 1440 min (the radio transmits on every pass);
    * imaging kind: acquisitions per orbit × (acquisition + settle) ÷ period;
    * nominal kind: the balance, 1 − the other modes of the operational mix;
    * other modes of the mix (custom, e.g. a seasonal night mode) keep their share (no rule).

    Each row carries ``inputs`` and their hash, and the mode's accepted ``share_basis`` (stored in
    the mode's performance by the accept route): ``status`` is ``matches`` (current = proposed),
    ``proposed``, ``accepted``, ``overridden`` (accepted with a reason) or ``stale`` (accepted on
    other inputs: the stations, the settle time or the products changed since)."""
    c = c or cfg()
    tol = float((c.get("shares") or {}).get("match_tolerance") or 0.0005)
    T = float(period_s or 5700.0)
    si = share_inputs(products, c)
    mix = [m for m in modes if in_operational_mix(m) or (_attr(m, "kind") or "") in MIX_KINDS]
    rows: list[dict[str, Any]] = []
    proposed: dict[str, float | None] = {}
    for m in mix:
        kind = _attr(m, "kind") or "custom"
        mid = _attr(m, "id")
        inp: dict[str, Any] = {}
        if kind == "downlink":
            if union_min_per_day is None:
                val, prov = None, {"en": "no contact plan: add ground stations", "fr": "pas de plan de contact : ajouter des stations sol"}
            else:
                val = float(union_min_per_day) / 1440.0
                inp = {"union_min_per_day": round(float(union_min_per_day), 2), "stations": sorted(stations or [])}
                prov = {"en": f"union of the station passes {union_min_per_day:.1f} min/day ÷ 1440 min = {100 * val:.1f} %",
                        "fr": f"union des passages aux stations {union_min_per_day:.1f} min/j ÷ 1440 min = {100 * val:.1f} %"}
            basis = "union_contact"
        elif kind == "imaging":
            dur = si["acquisition_s"] + si["settle_s"]
            val = si["acquisitions_per_orbit"] * dur / T
            inp = {**si, "period_s": round(T, 1)}
            prov = {"en": f"{si['acquisitions_per_orbit']:g} acquisition(s) per orbit × ({si['acquisition_s']:g} s + "
                          f"{si['settle_s']:g} s settle) ÷ {T / 60:.1f} min = {100 * val:.1f} %",
                    "fr": f"{si['acquisitions_per_orbit']:g} acquisition(s) par orbite × ({si['acquisition_s']:g} s + "
                          f"{si['settle_s']:g} s de stabilisation) ÷ {T / 60:.1f} min = {100 * val:.1f} %"}
            basis = "acquisitions"
        else:
            continue
        proposed[mid] = val
        rows.append({"mode_id": mid, "name": _attr(m, "name"), "kind": kind, "basis": basis, "inputs": inp,
                     "proposed_fraction": round(val, 4) if val is not None else None, "provenance": prov})
    nominal = next((m for m in mix if (_attr(m, "kind") or "") == "nominal"), None)
    if nominal is not None:
        others = 0.0
        for m in mix:
            if m is nominal:
                continue
            v = proposed.get(_attr(m, "id"))
            others += float(v if v is not None else (_num(_attr(m, "orbit_fraction")) or 0.0))
        val = max(0.0, 1.0 - others)
        rows.append({"mode_id": _attr(nominal, "id"), "name": _attr(nominal, "name"), "kind": "nominal", "basis": "balance",
                     "inputs": {"other_modes": round(others, 4)}, "proposed_fraction": round(val, 4),
                     "provenance": {"en": f"balance of the orbit: 100 % − {100 * others:.1f} % of the other modes = {100 * val:.1f} %",
                                    "fr": f"solde de l’orbite : 100 % − {100 * others:.1f} % des autres modes = {100 * val:.1f} %"}})
    by_id = {_attr(m, "id"): m for m in mix}
    for r in rows:
        m = by_id[r["mode_id"]]
        cur = _num(_attr(m, "orbit_fraction"))
        r["current_fraction"] = cur
        r["inputs_hash"] = _hash(r["inputs"])
        acc = _attr(m, "share_basis") or None
        r["accepted"] = acc
        p = r["proposed_fraction"]
        if p is None:
            r["status"] = "not_evaluated"
        elif acc and acc.get("inputs_hash") and acc["inputs_hash"] != r["inputs_hash"] and \
                (cur is None or abs(cur - p) > tol):
            r["status"] = "stale"
        elif cur is not None and abs(cur - p) <= tol:
            r["status"] = "accepted" if acc and not acc.get("override_reason") else "matches"
        elif acc and acc.get("override_reason") and acc.get("inputs_hash") == r["inputs_hash"]:
            r["status"] = "overridden"
        else:
            r["status"] = "proposed"
    order = {"downlink": 0, "imaging": 1, "nominal": 2}
    return sorted(rows, key=lambda r: order.get(r["kind"], 3))


# ───────────────────────────────────────────────────────────── mode machine checks (MO-05/06)

def validate_machine(modes: list[dict], transitions: list[dict], monitors: Iterable[str] = ()) -> list[dict]:
    """Findings on the mode machine: ``[{id, severity, mode_id?, transition_id?, text{en,fr}}]``.

    * MM-UNREACHABLE: a mode no transition path reaches from the initial mode(s);
    * MM-NO-EXIT: a mode with no outgoing transition;
    * MM-AUTO-NO-GUARD: an autonomous/event transition without a monitored parameter;
    * MM-NO-SAFE: no safe mode (CON-OPS-01 / MO-08);
    * MM-DANGLING: a transition to/from a mode that no longer exists.
    """
    out: list[dict] = []
    ids = {m["id"] for m in modes}
    names = {m["id"]: m.get("name") or m["id"] for m in modes}
    for t in transitions:
        if t.get("from_mode_id") not in ids or t.get("to_mode_id") not in ids:
            out.append({"id": "MM-DANGLING", "severity": "major", "transition_id": t.get("id"),
                        "text": {"en": "Transition refers to a deleted mode.",
                                 "fr": "La transition renvoie à un mode supprimé."}})
    live_t = [t for t in transitions if t.get("from_mode_id") in ids and t.get("to_mode_id") in ids]
    initial = [m["id"] for m in modes if (m.get("performance") or {}).get("initial")] or \
              [m["id"] for m in modes if (m.get("performance") or {}).get("mode_kind") == "leop"] or \
              ([modes[0]["id"]] if modes else [])
    seen = set(initial)
    frontier = list(initial)
    while frontier:
        cur = frontier.pop()
        for t in live_t:
            if t["from_mode_id"] == cur and t["to_mode_id"] not in seen:
                seen.add(t["to_mode_id"])
                frontier.append(t["to_mode_id"])
    for m in modes:
        if m["id"] not in seen:
            out.append({"id": "MM-UNREACHABLE", "severity": "major", "mode_id": m["id"],
                        "text": {"en": f"{names[m['id']]} cannot be reached from the initial mode.",
                                 "fr": f"{names[m['id']]} est inatteignable depuis le mode initial."}})
        if len(modes) > 1 and (m.get("performance") or {}).get("mode_kind") != "disposal" \
                and not any(t["from_mode_id"] == m["id"] for t in live_t):
            out.append({"id": "MM-NO-EXIT", "severity": "minor", "mode_id": m["id"],
                        "text": {"en": f"{names[m['id']]} has no exit transition.",
                                 "fr": f"{names[m['id']]} n’a aucune transition de sortie."}})
    mon = set(monitors)
    for t in live_t:
        if t.get("trigger") in ("autonomous", "event"):
            g = t.get("guard") or t.get("guard_json") or {}
            if not g.get("param") and not t.get("monitor_ref"):
                out.append({"id": "MM-AUTO-NO-GUARD", "severity": "major", "transition_id": t.get("id"),
                            "text": {"en": f"Autonomous transition {names[t['from_mode_id']]} → {names[t['to_mode_id']]} "
                                           "names no monitored parameter.",
                                     "fr": f"La transition autonome {names[t['from_mode_id']]} → {names[t['to_mode_id']]} "
                                           "ne nomme aucun paramètre surveillé."}})
            elif t.get("monitor_ref") and mon and t["monitor_ref"] not in mon:
                out.append({"id": "MM-MONITOR-MISSING", "severity": "minor", "transition_id": t.get("id"),
                            "text": {"en": "The monitor this transition names is not accepted.",
                                     "fr": "La surveillance nommée par cette transition n’est pas acceptée."}})
    if modes and not any((m.get("performance") or {}).get("mode_kind") == "safe" or "safe" in str(m.get("name", "")).lower()
                         for m in modes):
        out.append({"id": "MM-NO-SAFE", "severity": "major",
                    "text": {"en": "No Safe mode in the mode machine.", "fr": "Aucun mode survie dans la machine de modes."}})
    return out


# ───────────────────────────────────────────────────────────── equipment → budgets

def equipment_budgets(elements: list[dict], modes: list[Any], *, gate: str | None,
                      link_rows: dict[str, dict] | None = None, c: dict | None = None) -> dict[str, Any]:
    """Every budget one equipment line feeds, with maturity margins (margin_policy) and the system
    margin of the gate ladder.

    ``rows``: one per hardware leaf — mass, power per mode, data per mode, cost, dissipation per
    mode, link facts (transmitters) — each with CBE, maturity category/percent and with-margin.
    ``totals``: per budget; mass and power also with the system margin.
    """
    from .margin_policy import convention, maturity, system_margin_percent
    c = c or cfg()
    units = proposal_units(elements)
    mode_ids = [_attr(m, "id") for m in modes]
    members = {(_attr(m, "id"), mem.get("element_id")): mem for m in modes for mem in (_attr(m, "members") or [])}
    sys_m = system_margin_percent(gate, "mass")
    sys_p = system_margin_percent(gate, "power")
    rows = []
    tot = {"mass_cbe_kg": 0.0, "mass_with_maturity_kg": 0.0, "cost_keur": 0.0, "power_by_mode_w": {},
           "power_by_mode_with_maturity_w": {}, "data_by_mode_bps": {}, "dissipation_by_mode_w": {}}
    for e in units:
        mat = maturity(e)
        k = 1 + mat["percent"] / 100
        n = qty(e)
        mass = (_num(e.get("mass_kg")) or 0.0) * n
        cost = (_num(e.get("cost_recurring_keur")) or _num((kb_component(e) or {}).get("cost_keur")) or 0.0) * n
        p_by, d_by, h_by = {}, {}, {}
        for mid in mode_ids:
            mem = members.get((mid, e["id"]))
            if mem is None:
                continue
            p = float(mem.get("power_w") or 0.0) * float(mem.get("duty") if mem.get("duty") is not None else 1.0)
            p_by[mid] = round(p, 4)
            d_by[mid] = round(float(mem.get("data_rate_bps") or 0.0), 1)
            h_by[mid] = round(dissipation_w(e, mem, c), 4)
            tot["power_by_mode_w"][mid] = tot["power_by_mode_w"].get(mid, 0.0) + p
            tot["power_by_mode_with_maturity_w"][mid] = tot["power_by_mode_with_maturity_w"].get(mid, 0.0) + p * k
            tot["data_by_mode_bps"][mid] = tot["data_by_mode_bps"].get(mid, 0.0) + d_by[mid]
            tot["dissipation_by_mode_w"][mid] = tot["dissipation_by_mode_w"].get(mid, 0.0) + h_by[mid]
        tot["mass_cbe_kg"] += mass
        tot["mass_with_maturity_kg"] += mass * k
        tot["cost_keur"] += cost
        rows.append({
            "element_id": e["id"], "name": e.get("name"), "quantity": n, "kb_component_id": e.get("kb_component_id"),
            "unit_class": unit_class(e, c), "maturity_category": mat["category"], "maturity_percent": mat["percent"],
            "maturity_from": mat["category_from"],
            "mass_kg": round(mass, 4), "mass_with_maturity_kg": round(mass * k, 4),
            "power_avg_w": _num(e.get("power_avg_w")), "power_by_mode_w": p_by, "data_by_mode_bps": d_by,
            "dissipation_by_mode_w": h_by, "cost_keur": round(cost, 2) if cost else None,
            "link": (link_rows or {}).get(e["id"]),
            "stale": bool((e.get("kb_spec") or {}).get("stale")),
        })
    for key in ("power_by_mode_w", "power_by_mode_with_maturity_w", "data_by_mode_bps", "dissipation_by_mode_w"):
        tot[key] = {k2: round(v, 3) for k2, v in tot[key].items()}
    tot["power_by_mode_total_w"] = {k2: round(v * (1 + sys_p / 100), 3)
                                    for k2, v in tot["power_by_mode_with_maturity_w"].items()}
    tot["mass_total_kg"] = round(tot["mass_with_maturity_kg"] * (1 + sys_m / 100), 4)
    tot["mass_cbe_kg"] = round(tot["mass_cbe_kg"], 4)
    tot["mass_with_maturity_kg"] = round(tot["mass_with_maturity_kg"], 4)
    tot["cost_keur"] = round(tot["cost_keur"], 2)
    return {"rows": rows, "totals": tot, "modes": [{"id": _attr(m, "id"), "name": _attr(m, "name"),
                                                    "kind": _attr(m, "kind")} for m in modes],
            "system_margin": {"gate": gate, "mass_percent": sys_m, "power_percent": sys_p, **convention()},
            "note": {"en": "Mass total excludes harness (5 %) and propellant; the full mass budget is under Budget → Mass.",
                     "fr": "La masse totale exclut le harnais (5 %) et les ergols ; le bilan de masse complet est dans Bilan → Masse."}}
