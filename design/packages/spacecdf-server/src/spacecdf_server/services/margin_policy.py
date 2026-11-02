"""SpaceCDF — margin policy engine (replaces AI "consistency checking" of budgets).

Applies ``configs/margin_policy.yaml`` (ESA "Margin philosophy for science assessment
studies" issue 1.3, plus labelled C2O defaults) to the element tree and the design
parameters:

* mass: per-unit maturity margin (category A/B 5 %, C 10 %, D 20 %), harness 5 % of
  nominal dry mass, system margin 20 % → total dry mass with margins, compared with
  the CubeSat Design Specification limit or the study mass target;
* power: per-unit maturity margin + 20 % system margin, compared with the EOL array
  power when the design loop has produced it;
* propellant residual 2 %, tank volume +10 %;
* ΔV: 5 % on calculated manoeuvres, 100 % on orbit maintenance and attitude control;
* data handling: RAM ≤ 50 % used, CPU peak ≤ 50 %, storage margin (C2O default).

Pure function: ``evaluate_margins(elements, params, ...)`` → dict. No AI, no I/O
apart from the cached config and KB.
"""
from __future__ import annotations

from typing import Any

from . import rule_config as rc
from .rule_inputs import kb_component, leaves_with, param, perf, qty

CONFIG = "margin_policy"


def _category(e: dict, cfg: dict) -> tuple[str, str]:
    """(category letter, how it was chosen: element | trl | no_kb)."""
    cats = cfg["maturity_margins"]["categories"]
    explicit = str(perf(e).get("maturity_category") or "").strip().upper()
    if explicit in cats:
        return explicit, "element"
    kb = kb_component(e) or {}
    trl = e.get("trl") if e.get("trl") is not None else kb.get("trl")
    heritage = bool(e.get("heritage_json") or kb.get("heritage_missions"))
    if trl is None and not kb:
        return cfg["category_from_trl"].get("no_kb_component", "D"), "no_kb"
    trl = int(trl or 0)
    for r in cfg["category_from_trl"]["rules"]:
        if trl >= int(r.get("min_trl", 0)) and (heritage or not r.get("requires_heritage")):
            return r["category"], "trl"
    return "D", "trl"


def _units(elements: list[dict], field: str, cfg: dict) -> list[dict]:
    cats = cfg["maturity_margins"]["categories"]
    rows = []
    for e in leaves_with(elements, field):
        cat, how = _category(e, cfg)
        cbe = float(e.get(field) or 0) * qty(e)
        pct = float(cats[cat]["percent"])
        rows.append({"element_id": e["id"], "name": e.get("name", ""), "quantity": qty(e),
                     "cbe": round(cbe, 4), "category": cat, "category_from": how,
                     "margin_percent": pct, "with_margin": round(cbe * (1 + pct / 100), 4)})
    rows.sort(key=lambda r: -r["cbe"])
    return rows


def _val(node: dict) -> float:
    return float(node["value"])


def evaluate_margins(
    elements: list[dict],
    params: dict[str, Any] | None = None,
    *,
    mass_limit_kg: float | None = None,
    mass_limit_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Margin policy applied to the design. ``mass_limit_kg`` is the CDS or target limit."""
    cfg = rc.load(CONFIG)
    params = params or {}
    checks: list[dict] = []
    mm_ref = rc.ref_of(cfg, cfg["maturity_margins"])

    # ------------------------------------------------------------------ mass
    m = cfg["mass"]
    units = _units(elements, "mass_kg", cfg)
    cbe = sum(u["cbe"] for u in units)
    maturity = sum(u["with_margin"] for u in units)
    harness = maturity * _val(m["harness_percent"]) / 100
    nominal_dry = maturity + harness
    system = nominal_dry * _val(m["system_margin_percent"]) / 100
    total_dry = nominal_dry + system
    prop = param(params, "propulsion.propellant_mass_kg") or param(params, "mass.propellant_kg")
    residual = (prop or 0) * _val(m["propellant_residual_percent"]) / 100
    total_wet = total_dry + (prop or 0) + residual
    mass = {
        "units": units, "cbe_kg": round(cbe, 3), "with_maturity_kg": round(maturity, 3),
        "harness_kg": round(harness, 3), "nominal_dry_kg": round(nominal_dry, 3),
        "system_margin_kg": round(system, 3), "total_dry_kg": round(total_dry, 3),
        "propellant_kg": prop, "propellant_residual_kg": round(residual, 3) if prop else None,
        "total_wet_kg": round(total_wet, 3), "limit_kg": mass_limit_kg,
    }
    sys_ref = rc.ref_of(cfg, m["system_margin_percent"])
    if not units:
        checks.append(rc.check_item(
            "MP-MASS-01", {"en": "Mass with margins", "fr": "Masse avec marges"}, "not_evaluated",
            {"en": "No space-segment element carries a mass yet.",
             "fr": "Aucun élément du segment spatial n’a encore de masse."}, sys_ref))
    elif mass_limit_kg:
        ok = total_wet <= mass_limit_kg
        checks.append(rc.check_item(
            "MP-MASS-01", {"en": "Mass with margins within the limit", "fr": "Masse avec marges dans la limite"},
            "pass" if ok else "fail",
            {"en": f"{rc.fmt(total_wet, 2)} kg with maturity, harness ({_val(m['harness_percent']):g} %) and "
                   f"system ({_val(m['system_margin_percent']):g} %) margins vs limit {rc.fmt(mass_limit_kg, 2)} kg.",
             "fr": f"{rc.fmt_fr(total_wet, 2)} kg avec les marges de maturité, de harnais ({_val(m['harness_percent']):g} %) "
                   f"et système ({_val(m['system_margin_percent']):g} %) pour une limite de {rc.fmt_fr(mass_limit_kg, 2)} kg."},
            mass_limit_ref or sys_ref, value=round(total_wet, 3), limit=mass_limit_kg, unit="kg"))
    else:
        checks.append(rc.check_item(
            "MP-MASS-01", {"en": "Mass with margins within the limit", "fr": "Masse avec marges dans la limite"},
            "not_evaluated",
            {"en": f"{rc.fmt(total_wet, 2)} kg with margins; no form factor or mass target to compare with.",
             "fr": f"{rc.fmt_fr(total_wet, 2)} kg avec marges ; ni facteur de forme ni masse cible pour comparer."},
            sys_ref, value=round(total_wet, 3), unit="kg"))
    # Units whose maturity category had to be guessed from "no KB part" are worth a look.
    guessed = [u for u in units if u["category_from"] == "no_kb"]
    if guessed:
        checks.append(rc.check_item(
            "MP-MASS-02", {"en": "Maturity category set for every unit", "fr": "Catégorie de maturité définie pour chaque unité"},
            "warn",
            {"en": f"{len(guessed)} unit(s) without a KB part or TRL are treated as new designs (category D, 20 %).",
             "fr": f"{len(guessed)} unité(s) sans pièce de la base ni TRL sont traitées comme des conceptions nouvelles (catégorie D, 20 %)."},
            rc.ref_of(cfg, cfg["category_from_trl"]), count=len(guessed),
            element_ids=[u["element_id"] for u in guessed]))

    # ------------------------------------------------------------------ power
    p = cfg["power"]
    punits = _units(elements, "power_avg_w", cfg)
    p_cbe = sum(u["cbe"] for u in punits)
    p_mat = sum(u["with_margin"] for u in punits)
    p_sys = p_mat * _val(p["system_margin_percent"]) / 100
    p_total = p_mat + p_sys
    available = param(params, "power.sa_power_eol_w")
    power = {"units": punits, "cbe_w": round(p_cbe, 3), "with_maturity_w": round(p_mat, 3),
             "system_margin_w": round(p_sys, 3), "total_w": round(p_total, 3), "available_eol_w": available}
    pref = rc.ref_of(cfg, p["system_margin_percent"])
    if punits and available:
        ok = p_total <= available
        checks.append(rc.check_item(
            "MP-PWR-01", {"en": "Power with margins within EOL generation", "fr": "Puissance avec marges sous la production en fin de vie"},
            "pass" if ok else "fail",
            {"en": f"{rc.fmt(p_total)} W orbit-average demand with margins vs {rc.fmt(available)} W EOL array power.",
             "fr": f"Demande moyenne de {rc.fmt_fr(p_total)} W avec marges pour {rc.fmt_fr(available)} W produits en fin de vie."},
            pref, value=round(p_total, 2), limit=available, unit="W"))
    else:
        checks.append(rc.check_item(
            "MP-PWR-01", {"en": "Power with margins within EOL generation", "fr": "Puissance avec marges sous la production en fin de vie"},
            "not_evaluated",
            {"en": "Needs unit power values and the EOL array power from the design loop.",
             "fr": "Il faut les puissances des unités et la puissance du générateur en fin de vie (boucle de conception)."},
            pref, value=round(p_total, 2) if punits else None, unit="W"))

    # ------------------------------------------------------------------ ΔV
    dv = cfg["delta_v"]
    classes = dv.get("parameter_classes") or {}
    margin_of = {"calculated_manoeuvre": dv["calculated_manoeuvre_percent"],
                 "orbit_maintenance": dv["orbit_maintenance_percent"],
                 "attitude_control": dv["attitude_control_percent"]}
    dv_rows = []
    for cls, pids in classes.items():
        if cls not in margin_of:
            continue
        for pid in pids or []:
            v = param(params, pid)
            if v is None or v <= 0:
                continue
            pct = _val(margin_of[cls])
            dv_rows.append({"parameter": pid, "class": cls, "delta_v_ms": v, "margin_percent": pct,
                            "with_margin_ms": round(v * (1 + pct / 100), 2),
                            **{k: rc.ref_of(cfg, margin_of[cls])[k] for k in ("standard_ref", "c2o_default")}})
    dv_total = sum(r["with_margin_ms"] for r in dv_rows)
    dv_avail = param(params, "propulsion.delta_v_total_ms")
    delta_v = {"rows": dv_rows, "total_with_margin_ms": round(dv_total, 2), "available_ms": dv_avail}
    dvref = rc.ref_of(cfg, dv["calculated_manoeuvre_percent"])
    if dv_rows and dv_avail is not None:
        ok = dv_avail >= dv_total
        checks.append(rc.check_item(
            "MP-DV-01", {"en": "ΔV capability covers ΔV with margins", "fr": "Le ΔV disponible couvre le ΔV avec marges"},
            "pass" if ok else "fail",
            {"en": f"{rc.fmt(dv_avail)} m/s available vs {rc.fmt(dv_total)} m/s needed with margins.",
             "fr": f"{rc.fmt_fr(dv_avail)} m/s disponibles pour {rc.fmt_fr(dv_total)} m/s nécessaires avec marges."},
            dvref, value=dv_avail, limit=round(dv_total, 2), unit="m/s"))
    elif dv_rows:
        checks.append(rc.check_item(
            "MP-DV-01", {"en": "ΔV capability covers ΔV with margins", "fr": "Le ΔV disponible couvre le ΔV avec marges"},
            "not_evaluated",
            {"en": f"{rc.fmt(dv_total)} m/s needed with margins; propulsion capability not computed yet.",
             "fr": f"{rc.fmt_fr(dv_total)} m/s nécessaires avec marges ; capacité de propulsion pas encore calculée."},
            dvref, limit=round(dv_total, 2), unit="m/s"))

    # ------------------------------------------------------------------ data handling
    dh = cfg["data_handling"]
    ram_used, ram_cap, cpu_peak = _obc_figures(elements, params)
    if ram_used is not None and ram_cap:
        pct = 100 * ram_used / ram_cap
        lim = _val(dh["ram_max_used_percent"])
        checks.append(rc.check_item(
            "MP-DH-01", {"en": "On-board RAM use", "fr": "Utilisation de la mémoire vive embarquée"},
            "pass" if pct <= lim else "fail",
            {"en": f"{rc.fmt(pct, 0)} % of RAM used (limit {lim:g} %).",
             "fr": f"{rc.fmt_fr(pct, 0)} % de la mémoire vive utilisée (limite {lim:g} %)."},
            rc.ref_of(cfg, dh["ram_max_used_percent"]), value=round(pct, 1), limit=lim, unit="%"))
    if cpu_peak is not None:
        lim = _val(dh["cpu_max_peak_percent"])
        checks.append(rc.check_item(
            "MP-DH-02", {"en": "Processor peak load", "fr": "Charge de pointe du processeur"},
            "pass" if cpu_peak <= lim else "fail",
            {"en": f"Peak CPU load {rc.fmt(cpu_peak, 0)} % (limit {lim:g} %).",
             "fr": f"Charge de pointe {rc.fmt_fr(cpu_peak, 0)} % (limite {lim:g} %)."},
            rc.ref_of(cfg, dh["cpu_max_peak_percent"]), value=cpu_peak, limit=lim, unit="%"))
    need = param(params, "data.storage_required_gb")
    cap = _obc_storage_gb(elements)
    if need is not None and cap:
        smargin = _val(dh["storage_margin_percent"]) if "storage_margin_percent" in dh else 50.0
        ok = cap >= need * (1 + smargin / 100)
        checks.append(rc.check_item(
            "MP-DH-03", {"en": "Mass-memory storage margin", "fr": "Marge de stockage en mémoire de masse"},
            "pass" if ok else "fail",
            {"en": f"{rc.fmt(cap, 1)} GB on board vs {rc.fmt(need, 2)} GB needed + {smargin:g} %.",
             "fr": f"{rc.fmt_fr(cap, 1)} Go à bord pour {rc.fmt_fr(need, 2)} Go nécessaires + {smargin:g} %."},
            rc.ref_of(cfg, dh.get("storage_margin_percent", {"source": "c2o_default"})),
            value=cap, limit=round(need * (1 + smargin / 100), 2), unit="GB"))

    policy = {
        "maturity_margins": {c: {"percent": v["percent"], "label": v["label"]}
                             for c, v in cfg["maturity_margins"]["categories"].items()},
        "maturity_ref": mm_ref["standard_ref"],
        **{f"{sect}.{k}": {"value": v["value"], **{kk: rc.ref_of(cfg, v)[kk] for kk in ("standard_ref", "c2o_default")}}
           for sect in ("mass", "power", "delta_v", "data_handling", "thermal")
           for k, v in cfg[sect].items() if isinstance(v, dict) and "value" in v},
    }
    return {"policy": policy, "mass": mass, "power": power, "delta_v": delta_v,
            "checks": checks, "summary": rc.summarise(checks)}


def _obc_elements(elements: list[dict]) -> list[dict]:
    out = []
    for e in leaves_with(elements, "mass_kg") + [x for x in elements if x.get("subsystem_domain") == "obc"]:
        kb = kb_component(e) or {}
        if kb.get("category") == "obc" or e.get("subsystem_domain") == "obc" or "obc" in (e.get("name") or "").lower():
            out.append(e)
    return out


def _obc_figures(elements: list[dict], params: dict) -> tuple[float | None, float | None, float | None]:
    """(RAM used MB, RAM capacity MB, CPU peak %) from parameters or OBC element performance."""
    ram_used = param(params, "data.ram_used_mb")
    ram_cap = param(params, "data.ram_capacity_mb")
    cpu = param(params, "data.cpu_peak_percent")
    for e in _obc_elements(elements):
        pf = perf(e)
        kb = (kb_component(e) or {}).get("performance") or {}
        ram_used = ram_used if ram_used is not None else _num(pf.get("ram_used_mb"))
        ram_cap = ram_cap or _num(pf.get("ram_mb")) or _num(kb.get("ram_mb"))
        cpu = cpu if cpu is not None else _num(pf.get("cpu_peak_percent"))
    return ram_used, ram_cap, cpu


def _obc_storage_gb(elements: list[dict]) -> float | None:
    for e in _obc_elements(elements):
        pf = perf(e)
        kb = (kb_component(e) or {}).get("performance") or {}
        for src in (pf, kb):
            for k in ("storage_gb", "mass_memory_gb", "flash_gb"):
                v = _num(src.get(k))
                if v:
                    return v
    return None


def _num(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None
