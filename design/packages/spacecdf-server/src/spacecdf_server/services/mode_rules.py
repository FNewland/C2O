"""SpaceCDF — design rules that turn analyses into proposals (Nov 2026).

* rule 8 (FD-01 / FD-02): FMECA failure mode with S ≥ 3 → proposed ST[12]-like monitor on a
  parameter of the unit + an ST[19]-like event-action stub calling a function of the placeholder
  catalogue (``mode_rules.yaml fdir.function_catalogue``). The stub is validated: the function
  exists, a "switch to redundant" action needs a redundant unit, a "power off / cycle" action
  needs a switchable line and is refused for units that must never switch themselves off
  (OBC, EPS, battery, receiver). Data only — the TM/TC and FDIR design model is phase 2.
* rule 9 (FD-03 / RV-04): FMECA single points and requirements verified by analysis or review
  only → risk register entries (proposed; accepting one adds it to the study's register).
* rule 7 (EI-05): a unit whose cold case is below its minimum operating temperature → a
  heater with a thermostat (on/off set-points) and a proposed switched power line.

Each function returns proposal dicts ``{rule_id, kind, target_key, element_id, payload,
standard_ref, c2o_default, rationale{en,fr}, inputs_hash}`` for ``db/mode_repo.upsert_proposals``.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

from . import rule_config as rc
from .mode_model import cfg as mode_cfg
from .mode_model import ref, unit_class
from .rule_inputs import kb_component, perf

STEFAN_BOLTZMANN = 5.670374419e-8


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")[:24] or "unit"


def _op_range(e: dict) -> tuple[float, float] | None:
    for src in ((e.get("kb_spec") or {}), perf(e), kb_component(e) or {}, (kb_component(e) or {}).get("performance") or {}):
        r = src.get("operating_temp_c") if isinstance(src, dict) else None
        if isinstance(r, (list, tuple)) and len(r) == 2:
            try:
                return float(r[0]), float(r[1])
            except (TypeError, ValueError):
                continue
    p = perf(e)
    if isinstance(p.get("op_temp_min_c"), (int, float)) and isinstance(p.get("op_temp_max_c"), (int, float)):
        return float(p["op_temp_min_c"]), float(p["op_temp_max_c"])
    return None


def _redundant(e: dict) -> bool:
    from .fmeca_library import _redundant as red
    return red(e)


# ───────────────────────────────────────────────────────────── rule 8: FMECA → monitor + action

def validate_action(action_id: str, e: dict, *, switchable: bool | None = None, c: dict | None = None) -> list[dict]:
    """Problems with an action stub: ``[{code, text{en,fr}}]`` (empty = valid)."""
    c = c or mode_cfg()
    fd = c["fdir"]
    cat = {f["id"]: f for f in fd["function_catalogue"]}
    out: list[dict] = []
    fn = cat.get(action_id)
    if fn is None:
        return [{"code": "FD-02-UNKNOWN-FUNCTION",
                 "text": {"en": f"{action_id} is not in the function catalogue.",
                          "fr": f"{action_id} n’est pas dans le catalogue de fonctions."}}]
    cls = unit_class(e, c)
    needs = set(fn.get("needs") or [])
    if "redundancy" in needs and not _redundant(e):
        out.append({"code": "FD-02-NO-REDUNDANCY",
                    "text": {"en": "Switch-over needs a redundant unit or bus; this unit has none.",
                             "fr": "La bascule exige une unité ou un bus redondant ; cette unité n’en a pas."}})
    if "switchable_line" in needs:
        if cls in set(fd.get("never_off_classes") or []):
            out.append({"code": "FD-02-SELF-OFF",
                        "text": {"en": "The action would switch off a unit that must stay powered (its own line).",
                                 "fr": "L’action couperait une unité qui doit rester alimentée (sa propre ligne)."}})
        elif switchable is False:
            out.append({"code": "FD-02-NOT-SWITCHABLE",
                        "text": {"en": "The unit is on a non-switchable line.",
                                 "fr": "L’unité est sur une ligne non commutable."}})
    return out


def _fallback_action(e: dict, c: dict) -> str:
    """A valid action when the library's default is not (C2O default chain)."""
    for a in ("SWITCH_TO_REDUNDANT", "POWER_CYCLE_LINE", "ENTER_SAFE_MODE", "EVENT_ONLY"):
        if not validate_action(a, e, c=c):
            return a
    return "EVENT_ONLY"


def fdir_proposals(fmeca_rows: list[dict], elements: list[dict], *, safe_mode_id: str | None = None,
                   c: dict | None = None) -> list[dict]:
    """FD-01 monitor + FD-02 action stub per FMECA row with S ≥ min_severity."""
    c = c or mode_cfg()
    fd = c["fdir"]
    r = ref(fd, c)
    by_id = {e["id"]: e for e in elements}
    out: list[dict] = []
    # one monitor (and one action) per (unit, monitored parameter): several failure modes of a
    # unit are often detected by the same parameter; the worst one sets the response.
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in fmeca_rows:
        if int(row.get("severity") or 0) < int(fd["min_severity"]):
            continue
        spec = fd["by_type"].get(row.get("library_type") or "generic") or fd["by_type"]["generic"]
        groups.setdefault((row.get("element_id"), spec["param"]), []).append(row)
    for (_eid, _param), rows in groups.items():
        rows = sorted(rows, key=lambda r: -int(r.get("severity") or 0))
        row = rows[0]
        e = by_id.get(row.get("element_id"))
        if e is None:
            continue
        lib_type = row.get("library_type") or "generic"
        spec = fd["by_type"].get(lib_type) or fd["by_type"]["generic"]
        if spec.get("check") == "none":
            continue
        unit = _slug(e.get("name") or e["id"])
        param = f"{unit}.{spec['param']}"
        low, high, lim_src = spec.get("low"), spec.get("high"), "C2O default"
        if spec.get("limit") == "op_range":
            rng = _op_range(e)
            if rng:
                low, high, lim_src = rng[0], rng[1], "unit operating range (KB / element)"
            else:
                low, high, lim_src = -20.0, 50.0, "C2O default range (no operating range on the unit)"
        monitor = {
            "pmon_id": f"MON-{unit}-{_slug(spec['param'])}"[:40],
            "parameter": param, "check": spec["check"], "low": low, "high": high,
            "expected": spec.get("expected"), "limit_source": lim_src,
            "persistence": fd["persistence"], "period_s": fd["period_s"],
            "valid_when": {"en": f"{e.get('name')} powered", "fr": f"{e.get('name')} alimenté"},
            "failure_mode": row.get("mode"), "fmeca_row_id": row.get("id"), "severity": row.get("severity"),
            "fmeca_row_ids": [x.get("id") for x in rows],
        }
        inputs = {"rows": [x.get("id") for x in rows], "s": row.get("severity"), "lim": [low, high],
                  "red": _redundant(e), "type": lib_type}
        modes_en = ", ".join(f"'{(x.get('mode') or {}).get('en', '')}' (S{x.get('severity')})" for x in rows)
        modes_fr = ", ".join(f"« {(x.get('mode') or {}).get('fr', '')} » (S{x.get('severity')})" for x in rows)
        out.append({
            "rule_id": "FD-01", "kind": "monitor", "target_key": f"monitor:{e['id']}:{spec['param']}",
            "element_id": e["id"], "payload": monitor, **r,
            "rationale": {"en": f"Detects {modes_en} on {e.get('name')}.",
                          "fr": f"Détecte {modes_fr} sur {e.get('name')}."},
            "inputs_hash": _hash(inputs),
        })
        action = spec["action"]
        problems = validate_action(action, e, c=c)
        chosen = action if not problems else _fallback_action(e, c)
        fn = next(f for f in fd["function_catalogue"] if f["id"] == chosen)
        stub = {
            "event_from": monitor["pmon_id"], "function_id": chosen, "function_name": fn["name"],
            "level": spec.get("level"), "target_element_id": e["id"],
            "target_mode_id": safe_mode_id if chosen == "ENTER_SAFE_MODE" else None,
            "replaced": {"function_id": action, "problems": problems} if problems else None,
            "problems": validate_action(chosen, e, c=c),
        }
        out.append({
            "rule_id": "FD-02", "kind": "action", "target_key": f"action:{e['id']}:{spec['param']}",
            "element_id": e["id"], "payload": stub, **r,
            "rationale": {"en": f"On {monitor['pmon_id']}: {fn['name']['en']}." +
                                (f" ({action} not valid here: {problems[0]['text']['en']})" if problems else ""),
                          "fr": f"Sur {monitor['pmon_id']} : {fn['name']['fr']}." +
                                (f" ({action} non valable ici : {problems[0]['text']['fr']})" if problems else "")},
            "inputs_hash": _hash({**inputs, "action": chosen}),
        })
    return out


def monitored_element_ids(proposals: list[dict]) -> set[str]:
    """Elements with an accepted (or edited) monitor: the FMECA detection credit (F10)."""
    return {p["element_id"] for p in proposals
            if p.get("kind") == "monitor" and p.get("status") in ("accepted", "edited") and p.get("element_id")}


# ───────────────────────────────────────────────────────────── rule 9: risks

def risk_proposals(fmeca_rows: list[dict], requirements: list[dict], c: dict | None = None) -> list[dict]:
    """FD-03: one risk per single-point failure mode; RV-04: one per A/R-only requirement."""
    c = c or mode_cfg()
    rk = c["risks"]
    out: list[dict] = []
    sp = rk["single_point"]
    for row in fmeca_rows:
        if not row.get("single_point"):
            continue
        name = row.get("component") or row.get("element_id")
        mode = row.get("mode") or {}
        risk = {
            "description": f"Single-point failure: {name} — {mode.get('en', '')} ({row.get('library_id')})",
            "category": sp["category"],
            "likelihood": max(1, min(5, int(row.get("occurrence") or 3))) if sp.get("likelihood_from_occurrence") else 3,
            "consequence": max(1, min(5, int(row.get("severity") or 4))) if sp.get("consequence_from_severity") else 4,
            "mitigation": (row.get("mitigation") or {}).get("en", ""),
            "status": "open", "source": f"rule:FD-03:{row.get('id')}"[:120],
        }
        out.append({"rule_id": "FD-03", "kind": "risk", "target_key": f"risk:fmeca:{row.get('id')}",
                    "element_id": row.get("element_id") or "", "payload": risk, **ref(sp, c),
                    "rationale": {"en": f"{name}: no redundancy for a severity-{row.get('severity')} failure mode.",
                                  "fr": f"{name} : aucune redondance pour un mode de défaillance de gravité {row.get('severity')}."},
                    "inputs_hash": _hash({"s": row.get("severity"), "o": row.get("occurrence"), "sp": True})})
    ao = rk["analysis_only"]
    for r in requirements:
        if r.get("status") == "retired":
            continue
        m = str(r.get("verification_method") or "").strip().upper()
        if m not in ("A", "R"):
            continue
        rid = r.get("id")
        risk = {
            "description": f"Requirement {rid} is verified by {'analysis' if m == 'A' else 'review'} only: "
                           f"{str(r.get('text') or '')[:200]}",
            "category": ao["category"], "likelihood": ao["likelihood"], "consequence": ao["consequence"],
            "mitigation": "Add a test or inspection, or record the analysis uncertainty and its margin.",
            "status": "open", "source": f"rule:RV-04:{rid}"[:120],
        }
        out.append({"rule_id": "RV-04", "kind": "risk", "target_key": f"risk:req:{rid}",
                    "element_id": r.get("element_id") or "", "payload": risk, **ref(ao, c),
                    "rationale": {"en": f"{rid}: method {m} alone needs a risk assessment.",
                                  "fr": f"{rid} : la méthode {m} seule exige une évaluation du risque."},
                    "inputs_hash": _hash({"m": m, "text": r.get("text")})})
    return out


# ───────────────────────────────────────────────────────────── rule 7: heaters from the cold case

def _survival_min(e: dict | None, op_min: float, h: dict) -> tuple[float, str]:
    for src in ((e or {}).get("kb_spec") or {}, perf(e or {}), kb_component(e or {}) or {}):
        r = src.get("survival_temp_c") if isinstance(src, dict) else None
        if isinstance(r, (list, tuple)) and len(r) == 2 and isinstance(r[0], (int, float)):
            return float(r[0]), "survival range of the part"
    return op_min - float(h.get("survival_below_op_c", 15)), "C2O default (operating minimum − {:g} K)".format(
        float(h.get("survival_below_op_c", 15)))


def heater_proposals(nodes: list[Any], conductances: list[dict], elements: list[dict], *,
                     emissivity: float, off_in_cold: set[str] | None = None, c: dict | None = None) -> list[dict]:
    """EI-05: a heater + thermostat + switched line for every node whose cold case fails.

    Heater power = (T_min − T_cold) × (ΣG + 4εσA·T³) × (1 + design margin), rounded up; on at
    T_min + on_above, off at T_min + off_above (C2O defaults, mode_rules.yaml thermal.heater).
    """
    c = c or mode_cfg()
    h = c["thermal"]["heater"]
    r = ref(h, c)
    by_id = {e["id"]: e for e in elements}
    out: list[dict] = []
    for n in nodes:
        get = (lambda k: n.get(k)) if isinstance(n, dict) else (lambda k: getattr(n, k, None))
        if get("kind") == "structure":
            continue
        t_cold, t_min = get("t_cold_c"), get("allow_min_c")
        nid = get("element_id")
        limit_src = "operating minimum"
        if t_min is not None and off_in_cold and nid in off_in_cold:
            t_min, limit_src = _survival_min(by_id.get(nid), float(t_min), h)   # switched off: survival limit
        if t_cold is None or t_min is None or float(t_cold) >= float(t_min):
            continue
        g_tot = sum(float(l.get("w_per_k") or 0) for l in conductances if nid in (l.get("a"), l.get("b")))
        area = float(get("area_m2") or 0.0)
        g_rad = 4.0 * emissivity * STEFAN_BOLTZMANN * area * (float(t_cold) + 273.15) ** 3
        raw = (float(t_min) - float(t_cold)) * (g_tot + g_rad)
        w = raw * (1 + float(h["design_margin_percent"]) / 100)
        step = float(h["round_to_w"])
        w = max(step, math.ceil(w / step) * step)
        name = get("name") or (by_id.get(nid) or {}).get("name") or nid
        on_c = float(t_min) + float(h["on_above_min_c"])
        off_c = float(t_min) + float(h["off_above_min_c"])
        v = float(h["line_voltage_v"])
        line = {"name": f"htr_{_slug(name)}", "switchable": True, "default_on": False,
                "current_a": round(w / v, 3), "lcl_limit_a": round(w / v * float(h["lcl_factor"]), 3),
                "voltage_v_assumed": v, "status": "proposed",
                "note": {"en": "Proposed line for the electrical model (power lines are defined there).",
                         "fr": "Ligne proposée au modèle électrique (les lignes d’alimentation y sont définies)."}}
        payload = {"element_id": nid, "name": f"Heater – {name}", "power_w": w, "raw_w": round(raw, 3),
                   "on_c": on_c, "off_c": off_c, "control": "auto", "limit": limit_src,
                   "t_cold_c": round(float(t_cold), 2), "t_min_c": float(t_min), "line": line}
        out.append({"rule_id": "EI-05", "kind": "heater", "target_key": f"heater:{nid}", "element_id": nid,
                    "payload": payload, **r,
                    "rationale": {"en": f"{name}: cold case {float(t_cold):.1f} °C below the {float(t_min):.0f} °C "
                                        f"{'survival minimum (unit off)' if limit_src != 'operating minimum' else 'operating minimum'}; "
                                        f"{w:g} W heater, thermostat on {on_c:g} / off {off_c:g} °C.",
                                  "fr": f"{name} : cas froid {float(t_cold):.1f} °C sous le minimum "
                                        f"{'de survie (unité éteinte)' if limit_src != 'operating minimum' else 'de fonctionnement'} de {float(t_min):.0f} °C ; "
                                        f"réchauffeur de {w:g} W, thermostat marche {on_c:g} / arrêt {off_c:g} °C."},
                    "inputs_hash": _hash({"t": round(float(t_cold), 1), "min": t_min, "w": w})})
    return out


def rules_ref() -> dict[str, Any]:
    """Sources of the proposal rules (for the UI legend)."""
    c = mode_cfg()
    return {"fdir": ref(c["fdir"], c), "single_point": ref(c["risks"]["single_point"], c),
            "analysis_only": ref(c["risks"]["analysis_only"], c), "heater": ref(c["thermal"]["heater"], c),
            "function_catalogue": [{"id": f["id"], "name": f["name"], "needs": f.get("needs") or []}
                                   for f in c["fdir"]["function_catalogue"]],
            "config_errors": _config_errors()}


def _config_errors() -> list[str]:
    from .mode_model import validate_config
    try:
        return validate_config()
    except rc.RuleConfigError as exc:   # pragma: no cover
        return [str(exc)]
