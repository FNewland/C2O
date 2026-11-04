"""SpaceCDF — Gate exit criteria evaluator.

Loads ``configs/gate_exit_criteria.yaml`` and evaluates each criterion of one
canonical review gate (MDR / PRR / SRR / PDR) against the stored study state:
the Mission Need, the design parameters, the study's requirements, its element
tree, functions and risk register. ``MCR`` (the old name of MDR, ruling 3) and
``pre_phase_a`` still resolve to the MDR. Which gates a study holds is its gate
profile's business (services/gate_profiles.py, services/gate_reviews.py).

Every criterion comes back with

* ``status``   — ``pass`` | ``fail`` | ``manual`` | ``not_evaluated``
  (what the evidence says);
* ``verdict``  — ``pass`` | ``fail`` | ``advisory`` | ``manual`` |
  ``not_evaluated`` (what it means for the gate). A ``should_pass`` criterion
  that is not met is ``advisory``: it is reported but never blocks the gate
  (author ruling Q23: PDR should-pass items stay advisory);
* ``evidence_found`` — an English message, plus ``evidence_key`` /
  ``evidence_params`` so the UI can render the same message in French
  (the key is the English template with ``{{var}}`` placeholders).

``ready`` is True when every ``must_pass`` criterion has status ``pass``.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

#: Message used when a criterion needs parameters the design loop has not produced yet.
MSG_RUN_DESIGN = "Run the design loop first: {{params}} not available"

# Every ``evidence_key`` this module can emit. The frontend lists the same
# strings in components/gateReviewText.ts so they are translated; a test keeps
# the three (this tuple, the frontend table, the French catalog) in step.
EVIDENCE_KEYS: tuple[str, ...] = (
    "Requires manual assessment",
    "Auto-evaluation not implemented for this criterion",
    MSG_RUN_DESIGN,
    "Problem statement defined",
    "Problem statement is empty",
    "{{n}} stakeholder(s) identified",
    "{{n}} primary objective(s) with measurable criteria",
    "{{n}} alternative(s), including a non-space option",
    "{{n}} alternative(s), no non-space option",
    "Concept selected with rationale",
    "Concept selected, rationale missing",
    "No concept selected",
    "ConOps summary documented",
    "ConOps summary is empty",
    "Mass margin {{mass}}%, power margin {{power}}%",
    "No cost target set",
    "Cost {{cost}} MEUR vs target {{target}} MEUR",
    "Risk analysis run: {{n}} risk(s) identified",
    "Debris compliance score {{score}}/100",
    "No objectives defined",
    "{{traced}}/{{total}} objectives traced to requirements",
    "No requirements defined",
    "{{ok}}/{{total}} requirements have a verification method and a threshold",
    "No requirement threshold can be checked against the design yet",
    "{{met}}/{{total}} checkable requirements met ({{pct}}%)",
    "Mass margin {{mass}}%, power margin {{power}}% (required ≥ {{min}}%)",
    "Sustainability score {{score}}/100; casualty risk compliant",
    "Sustainability score {{score}}/100; casualty risk not compliant",
    "{{n}} requirement(s) not met: {{codes}}",
    "All {{n}} checkable requirements met",
    "No subsystem elements defined",
    "{{ok}}/{{total}} subsystems have at least one component",
    "Reliability {{rel}} vs target {{target}}",
    # PDR-EC-02 (Nov 2026): expected-interface coverage from configs/interface_rules.yaml
    "All {{required}} expected subsystem links present and reviewed",
    "All {{total}} accepted links have approved interface requirements agreed by both parties",
    "{{complete}}/{{total}} accepted links have approved interface requirements agreed by both parties; {{approved}} approved, {{agreed}} agreed",
    "{{n}} interface requirement(s) name no accepted interface",
    "{{met}}/{{required}} expected subsystem links present; {{suggested}} suggested link(s) not reviewed",
    "Interface rules are invalid",
    # PRR (Nov 2026, WP6) and the margin ladder (margin_policy.yaml system_margin_ladder)
    "Concept selected with rationale; {{n}} alternative(s) considered",
    "Orbit baseline: {{orbit}} {{alt}} km, {{inc}}°, {{life}} year(s)",
    "No orbit baseline",
    "{{n}} function(s) in the function tree",
    "{{systems}} system(s), {{subsystems}} subsystem(s) in the product tree",
    "Mass {{mass}} kg + {{margin}}% system margin = {{total}} kg vs {{limit}} kg; power {{power}} W + {{margin}}% = {{ptotal}} W vs {{avail}} W",
    "No mass target or form factor to check the mass budget against",
    "{{mission}} mission and {{system}} system requirement(s); {{nomethod}} without a verification method",
    "{{rated}}/{{total}} components have a TRL",
    "No components selected yet",
    "{{n}} ground station(s) identified",
    "{{n}} risk(s) in the risk register",
)


def _criteria_file() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "configs" / "gate_exit_criteria.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("configs/gate_exit_criteria.yaml not found")


@lru_cache(maxsize=4)
def _load_file(path: str, stamp: int) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {"phases": {}}


def _load() -> dict[str, Any]:
    try:
        path = _criteria_file()
        return _load_file(str(path), path.stat().st_mtime_ns)
    except (FileNotFoundError, OSError, yaml.YAMLError) as exc:
        logger.warning("Gate criteria file failed to load: %s", exc)
        return {"phases": {}}


def canonical_criterion_id(cid: str) -> str:
    """``MCR-EC-03`` (stored before Nov 2026) → ``MDR-EC-03``."""
    for old, new in ((_load().get("aliases") or {}).get("criteria_prefix") or {}).items():
        if cid.startswith(old):
            return new + cid[len(old):]
    return cid


def list_gates() -> list[str]:
    """Phase ids configured in the YAML (pre_phase_a, phase_a, ...)."""
    return list(_load().get("phases", {}).keys())


def list_gate_options() -> list[dict[str, str]]:
    """[{phase, gate, gate_name}] in YAML order — for selectors."""
    return [
        {"phase": pid, "gate": g.get("gate", ""), "gate_name": g.get("gate_name", "")}
        for pid, g in _load().get("phases", {}).items()
    ]


def resolve_phase(key: str) -> str | None:
    """Accept a phase id (``phase_b``) or a gate name (``PDR``/``pdr``; ``MCR`` = MDR)."""
    data = _load()
    phases = data.get("phases", {})
    if not key:
        return None
    if key in phases:
        return key
    aliases = data.get("aliases") or {}
    phase_alias = aliases.get("phases") or {}
    if phase_alias.get(key) in phases:
        return phase_alias[key]
    gate_alias = {a.lower(): v for a, v in (aliases.get("gates") or {}).items()}
    k = key.strip().lower()
    k = str(gate_alias.get(k, k)).lower()
    for pid, g in phases.items():
        if pid.lower() == k or str(g.get("gate", "")).lower() == k:
            return pid
    return None


def get_gate(phase_id: str) -> dict[str, Any] | None:
    pid = resolve_phase(phase_id)
    return _load().get("phases", {}).get(pid) if pid else None


# --------------------------------------------------------------------------- inputs

def _mn_view(mission_need: Any) -> dict[str, Any]:
    """Plain-dict view of a Mission Need (pydantic model or the frontend's dict).

    The frontend store calls the alternatives list ``alternatives``; the model
    calls it ``alternatives_considered``. Both are accepted.
    """
    if mission_need is None:
        return {}
    if hasattr(mission_need, "model_dump"):
        d = mission_need.model_dump(mode="json")
    elif isinstance(mission_need, dict):
        d = dict(mission_need)
    else:
        return {}
    if not d.get("alternatives_considered") and d.get("alternatives"):
        d["alternatives_considered"] = d["alternatives"]
    return d


def _plain(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return dict(obj) if isinstance(obj, dict) else {}


def _flat_params(design_params: Any) -> dict[str, Any]:
    """{param id: number} from a dict of numbers, ``{"value": ...}`` dicts or
    objects with ``.value``. Keys starting with ``_`` are kept as-is."""
    out: dict[str, Any] = {}
    for k, v in (design_params or {}).items():
        if k.startswith("_"):
            out[k] = v
            continue
        if isinstance(v, dict):
            v = v.get("value")
        elif hasattr(v, "value"):
            v = v.value
        if isinstance(v, bool):
            v = 1.0 if v else 0.0
        if isinstance(v, (int, float)):
            out[k] = float(v)
    return out


def _get_param(dp: dict, pid: str, default: float | None = None) -> float | None:
    """Numeric parameter value, or ``default`` when absent / non-numeric."""
    p = dp.get(pid)
    if p is None:
        return default
    if isinstance(p, dict):
        p = p.get("value")
    elif hasattr(p, "value"):
        p = p.value
    if isinstance(p, bool):
        return 1.0 if p else 0.0
    if isinstance(p, (int, float)):
        return float(p)
    return default


# --------------------------------------------------------------------------- evaluation

def evaluate_gate(
    phase_id: str,
    mission_need: Any = None,
    design_params: dict[str, Any] | None = None,
    position_answers: list[Any] | None = None,
    target_mass_kg: float | None = None,
    target_cost_meur: float | None = None,
    reliability_target: float | None = None,
    requirements: list[dict] | None = None,
    elements: list[dict] | None = None,
    interfaces: list[dict] | None = None,
    mission: Any = None,
    function_count: int | None = None,
    risks: list[dict] | None = None,
    margin_gate: str | None = None,
) -> dict[str, Any]:
    """Evaluate all exit criteria for a gate and return structured results.

    ``phase_id`` is a phase id from the YAML or a gate name (MDR/PRR/SRR/PDR; MCR = MDR).
    ``mission``: the study's MissionRequirements (orbit, ground stations); ``function_count``:
    functions in the study's function tree; ``risks``: the study's risk register;
    ``margin_gate``: the margin-ladder step for budget criteria (default: this gate).

    Returns::

        {
            "phase": str, "gate": str, "gate_name": str, "purpose": str,
            "authority": str, "found": bool,
            "criteria": [{"id", "question", "category", "priority", "advisory",
                          "status", "verdict", "evidence_required",
                          "evidence_found", "evidence_key", "evidence_params"}],
            "summary": {"total", "pass", "fail", "manual", "not_evaluated",
                        "advisory", "must_pass", "must_pass_met"},
            "ready": bool,  # True if all must_pass criteria pass
            "ready_pending_manual": bool,  # must_pass all pass or manual
        }
    """
    pid = resolve_phase(phase_id)
    gate = _load().get("phases", {}).get(pid) if pid else None
    if not gate:
        return {"phase": phase_id, "gate": "?", "gate_name": "", "purpose": "", "authority": "",
                "found": False, "criteria": [], "summary": {}, "ready": False,
                "ready_pending_manual": False}

    ctx = {
        "mn": _mn_view(mission_need),
        "dp": _flat_params(design_params),
        "answers": position_answers or [],
        "target_mass": target_mass_kg,
        "target_cost": target_cost_meur,
        "rel_target": reliability_target,
        "reqs": [r for r in (requirements or []) if r.get("status") != "retired"],
        "elements": [e for e in (elements or (design_params or {}).get("_elements") or [])
                     if not e.get("deleted_at")],
        "interfaces": [i for i in (interfaces or (design_params or {}).get("_interfaces") or [])
                       if not i.get("deleted_at")],
        "mission": _plain(mission),
        "function_count": function_count,
        "risks": list(risks or []),
        "margin_gate": (margin_gate or str(gate.get("gate", ""))).lower(),
    }

    results = [_evaluate_criterion(ec, ctx) for ec in gate.get("exit_criteria", [])]

    must_pass = [r for r in results if r["priority"] == "must_pass"]
    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "manual": sum(1 for r in results if r["status"] == "manual"),
        "not_evaluated": sum(1 for r in results if r["status"] == "not_evaluated"),
        "advisory": sum(1 for r in results if r["verdict"] == "advisory"),
        "must_pass": len(must_pass),
        "must_pass_met": sum(1 for r in must_pass if r["status"] == "pass"),
    }
    ready = all(r["status"] == "pass" for r in must_pass) if must_pass else False
    # Nothing automatic blocks the gate; only manual sign-offs remain open.
    ready_pending_manual = (all(r["status"] in ("pass", "manual") for r in must_pass)
                            if must_pass else False)

    return {
        "phase": pid,
        "gate": gate.get("gate", ""),
        "gate_name": gate.get("gate_name", ""),
        "purpose": " ".join(str(gate.get("purpose", "")).split()),
        "authority": gate.get("authority", ""),
        "found": True,
        "criteria": results,
        "summary": summary,
        "ready": ready,
        "ready_pending_manual": ready_pending_manual,
    }


def _render(template: str, params: dict[str, Any]) -> str:
    out = template
    for k, v in params.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def _set(result: dict, status: str, key: str, **params: Any) -> None:
    result["status"] = status
    result["evidence_key"] = key
    result["evidence_params"] = params
    result["evidence_found"] = _render(key, params)


def _fmt(v: float, d: int = 0) -> str:
    return f"{v:.{d}f}"


def _need(result: dict, dp: dict, *pids: str) -> list[float] | None:
    """Values of ``pids``; when any is missing mark the criterion not evaluated."""
    vals = [_get_param(dp, p) for p in pids]
    missing = [p for p, v in zip(pids, vals) if v is None]
    if missing:
        _set(result, "not_evaluated", MSG_RUN_DESIGN, params=", ".join(missing))
        return None
    return vals  # type: ignore[return-value]


def _threshold_results(reqs: list[dict], dp: dict) -> list[tuple[dict, str]]:
    """(requirement, pass|fail|untestable) for every requirement with a threshold."""
    from .compliance_tracker import ComplianceTracker

    tracker = ComplianceTracker()
    plain = {k: v for k, v in dp.items() if not k.startswith("_")}
    out = []
    for r in reqs:
        if not r.get("threshold_param_path"):
            continue
        out.append((r, tracker.evaluate_single(r, plain).status))
    return out


def _has_threshold(r: dict) -> bool:
    raw = r.get("threshold_value")
    if not r.get("threshold_param_path") or not r.get("threshold_op") or raw in (None, ""):
        return False
    try:
        float(json.loads(raw) if isinstance(raw, str) else raw)
    except (ValueError, TypeError, json.JSONDecodeError):
        return False
    return True


def _evaluate_criterion(ec: dict, ctx: dict) -> dict[str, Any]:
    """Evaluate a single exit criterion."""
    cid = ec.get("id", "")
    status_mode = ec.get("status", "manual")
    priority = ec.get("priority", "should_pass")
    result: dict[str, Any] = {
        "id": cid,
        "question": ec.get("question", ""),
        "category": ec.get("category", ""),
        "owner_seat": ec.get("owner_seat"),
        "mode": status_mode,               # auto | hybrid | manual (sign-off: WP9 class board)
        "step": ec.get("step"),
        "fix": ec.get("fix"),
        "priority": priority,
        "advisory": priority != "must_pass",
        "evidence_required": ec.get("evidence", ""),
        "status": "not_evaluated",
        "verdict": "not_evaluated",
        "evidence_found": "",
        "evidence_key": "",
        "evidence_params": {},
    }

    if status_mode == "manual":
        _set(result, "manual", "Requires manual assessment")
    else:
        try:
            _auto(cid, result, ctx)
        except Exception as e:  # noqa: BLE001 — one bad criterion must not sink the gate
            logger.warning("Gate criterion %s failed to evaluate: %s", cid, e)
            result["status"] = "not_evaluated"
            result["evidence_key"] = ""
            result["evidence_params"] = {}
            result["evidence_found"] = f"Evaluation error: {e}"

    st = result["status"]
    if st == "pass":
        result["verdict"] = "pass"
    elif result["advisory"]:
        result["verdict"] = "advisory"
    else:
        result["verdict"] = st
    return result


def _auto(cid: str, result: dict, ctx: dict) -> None:  # noqa: C901 — one branch per criterion
    mn, dp = ctx["mn"], ctx["dp"]
    reqs, elements = ctx["reqs"], ctx["elements"]

    # ---------------------------------------------------------------- MDR (was MCR)
    if cid == "MDR-EC-01":
        if (mn.get("problem_statement") or "").strip():
            _set(result, "pass", "Problem statement defined")
        else:
            _set(result, "fail", "Problem statement is empty")

    elif cid == "MDR-EC-02":
        n = len(mn.get("stakeholders") or [])
        _set(result, "pass" if n >= 1 else "fail", "{{n}} stakeholder(s) identified", n=n)

    elif cid == "MDR-EC-03":
        n = len([o for o in mn.get("objectives") or []
                 if o.get("priority", "primary") == "primary" and (o.get("measurable_criterion") or "").strip()])
        _set(result, "pass" if n >= 1 else "fail", "{{n}} primary objective(s) with measurable criteria", n=n)

    elif cid == "MDR-EC-04":
        alts = mn.get("alternatives_considered") or []
        non_space = {"aerial_drone", "aerial_aircraft", "ground_sensor", "ground_network", "space_existing"}
        has_ns = any(a.get("type") in non_space for a in alts)
        ok = len(alts) >= 2 and has_ns
        key = ("{{n}} alternative(s), including a non-space option" if has_ns
               else "{{n}} alternative(s), no non-space option")
        _set(result, "pass" if ok else "fail", key, n=len(alts))

    elif cid == "MDR-EC-05":
        sel = bool(mn.get("selected_alternative_id"))
        rat = bool((mn.get("selection_rationale") or "").strip())
        if sel and rat:
            _set(result, "pass", "Concept selected with rationale")
        elif sel:
            _set(result, "fail", "Concept selected, rationale missing")
        else:
            _set(result, "fail", "No concept selected")

    elif cid == "MDR-EC-06":
        if (mn.get("conops_summary") or "").strip():
            _set(result, "pass", "ConOps summary documented")
        else:
            _set(result, "fail", "ConOps summary is empty")

    elif cid == "MDR-EC-07":
        v = _need(result, dp, "systems.mass_margin_percent", "systems.power_margin_percent")
        if v:
            mass, power = v
            _set(result, "pass" if mass > -50 and power > 0 else "fail",
                 "Mass margin {{mass}}%, power margin {{power}}%", mass=_fmt(mass), power=_fmt(power))

    elif cid == "MDR-EC-08":
        target = ctx["target_cost"]
        if not target or target <= 0:
            _set(result, "pass", "No cost target set")
        else:
            v = _need(result, dp, "cost.total_meur")
            if v:
                cost = v[0]
                # 20 % allowance on Phase 0 estimates
                _set(result, "pass" if cost <= target * 1.2 else "fail",
                     "Cost {{cost}} MEUR vs target {{target}} MEUR", cost=_fmt(cost, 1), target=_fmt(target, 1))

    elif cid == "MDR-EC-09":
        v = _need(result, dp, "risk.total_risks")
        if v:
            _set(result, "pass", "Risk analysis run: {{n}} risk(s) identified", n=int(v[0]))

    elif cid == "MDR-EC-10":
        v = _need(result, dp, "debris.compliance_score")
        if v:
            _set(result, "pass" if v[0] >= 50 else "fail",
                 "Debris compliance score {{score}}/100", score=_fmt(v[0]))

    # ---------------------------------------------------------------- SRR
    elif cid == "SRR-EC-01":
        objectives = mn.get("objectives") or []
        if not objectives:
            _set(result, "fail", "No objectives defined")
        else:
            traced_ids = {r.get("objective_id") for r in reqs if r.get("objective_id")}
            traced = sum(1 for o in objectives
                         if o.get("traced_to_requirements") or (o.get("id") and o.get("id") in traced_ids))
            _set(result, "pass" if traced == len(objectives) else "fail",
                 "{{traced}}/{{total}} objectives traced to requirements", traced=traced, total=len(objectives))

    elif cid == "SRR-EC-02":
        # Interface requirements (level "interface") are checked by test or inspection of the
        # interface, not against a design threshold: they are counted for completeness only.
        sys_reqs = [r for r in reqs if r.get("level") != "interface"]
        from .interface_requirements import ird_status
        orphans = ird_status(ctx["interfaces"], reqs)["without_interface"]
        if not sys_reqs:
            _set(result, "fail", "No requirements defined")
        else:
            ok = sum(1 for r in sys_reqs if r.get("verification_method") and _has_threshold(r))
            if ok == len(sys_reqs) and orphans:
                _set(result, "fail", "{{n}} interface requirement(s) name no accepted interface", n=len(orphans))
            else:
                _set(result, "pass" if ok == len(sys_reqs) else "fail",
                     "{{ok}}/{{total}} requirements have a verification method and a threshold",
                     ok=ok, total=len(sys_reqs))

    elif cid == "SRR-EC-03":
        res = [s for _, s in _threshold_results(reqs, dp) if s != "untestable"]
        if not res:
            _set(result, "not_evaluated", "No requirement threshold can be checked against the design yet")
        else:
            met = sum(1 for s in res if s == "pass")
            pct = 100.0 * met / len(res)
            _set(result, "pass" if pct >= 80 else "fail",
                 "{{met}}/{{total}} checkable requirements met ({{pct}}%)",
                 met=met, total=len(res), pct=_fmt(pct))

    elif cid in ("SRR-EC-06", "PDR-EC-03", "PRR-EC-05"):
        _ladder_budget(result, ctx)

    elif cid == "SRR-EC-10":
        v = _need(result, dp, "sustainability.score", "debris.casualty_compliant")
        if v:
            score, casualty = v
            ok = score >= 55 and casualty >= 1
            key = ("Sustainability score {{score}}/100; casualty risk compliant" if casualty >= 1
                   else "Sustainability score {{score}}/100; casualty risk not compliant")
            _set(result, "pass" if ok else "fail", key, score=_fmt(score))

    # ---------------------------------------------------------------- PDR
    elif cid == "PDR-EC-01":
        res = [(r, s) for r, s in _threshold_results(reqs, dp) if s != "untestable"]
        if not res:
            _set(result, "not_evaluated", "No requirement threshold can be checked against the design yet")
        else:
            failed = [r.get("code") or r.get("id", "") for r, s in res if s == "fail"]
            if failed:
                _set(result, "fail", "{{n}} requirement(s) not met: {{codes}}",
                     n=len(failed), codes=", ".join(failed[:8]) + (" …" if len(failed) > 8 else ""))
            else:
                _set(result, "pass", "All {{n}} checkable requirements met", n=len(res))

    elif cid == "PDR-EC-02":
        # Every subsystem has its expected power/data/mechanical/thermal links
        # (coverage rules of interface_rules.yaml) and no suggestion is left unreviewed.
        subs = [e for e in elements if e.get("element_type") == "subsystem" and e.get("in_scope") is not False]
        if not subs:
            _set(result, "not_evaluated", "No subsystem elements defined")
        else:
            from .interface_proposer import Context, RuleConfigError, load_rules
            from .readiness import interface_coverage
            try:
                cctx = Context(elements, load_rules())
            except RuleConfigError:
                _set(result, "not_evaluated", "Interface rules are invalid")
            else:
                ifaces = ctx["interfaces"]
                cov = interface_coverage(cctx, ifaces, [e["id"] for e in subs])
                sub_ids = {e["id"] for e in subs}
                suggested = sum(1 for i in ifaces if i.get("status") == "suggested"
                                and (i.get("from_element_id") in sub_ids or i.get("to_element_id") in sub_ids))
                if cov["missing"] or suggested:
                    _set(result, "fail",
                         "{{met}}/{{required}} expected subsystem links present; {{suggested}} suggested link(s) not reviewed",
                         met=cov["met"], required=cov["required"], suggested=suggested)
                else:
                    # F5 (design rules IF-01/IF-05): the criterion asks for interface REQUIREMENTS,
                    # so every accepted link needs an approved, current interface requirement and
                    # the agreement of both seats.
                    from .interface_requirements import ird_status
                    ird = ird_status(ifaces, reqs)
                    orphans = len(ird["without_interface"])
                    if ird["accepted"] and ird["complete"] == ird["accepted"] and not orphans:
                        _set(result, "pass",
                             "All {{total}} accepted links have approved interface requirements agreed by both parties",
                             total=ird["accepted"], required=cov["required"])
                    elif ird["accepted"] and ird["complete"] == ird["accepted"]:
                        _set(result, "fail", "{{n}} interface requirement(s) name no accepted interface", n=orphans)
                    else:
                        _set(result, "fail",
                             "{{complete}}/{{total}} accepted links have approved interface requirements agreed by both parties; {{approved}} approved, {{agreed}} agreed",
                             complete=ird["complete"], total=ird["accepted"], approved=ird["approved"],
                             agreed=ird["agreed"])


    elif cid == "PDR-EC-04":
        subs = [e for e in elements if e.get("element_type") == "subsystem"]
        if not subs:
            _set(result, "not_evaluated", "No subsystem elements defined")
        else:
            children: dict[str, list[dict]] = {}
            for e in elements:
                if e.get("parent_id"):
                    children.setdefault(e["parent_id"], []).append(e)

            def has_component(eid: str, depth: int = 0) -> bool:
                if depth > 20:
                    return False
                return any(c.get("element_type") == "component" or has_component(c.get("id", ""), depth + 1)
                           for c in children.get(eid, []))

            ok = sum(1 for s in subs if has_component(s.get("id", "")))
            _set(result, "pass" if ok == len(subs) else "fail",
                 "{{ok}}/{{total}} subsystems have at least one component", ok=ok, total=len(subs))

    elif cid in ("PDR-EC-05",):
        v = _need(result, dp, "reliability.mission_reliability")
        if v:
            target = ctx["rel_target"] or 0.9
            _set(result, "pass" if v[0] >= target else "fail",
                 "Reliability {{rel}} vs target {{target}}", rel=_fmt(v[0], 3), target=_fmt(target, 2))

    # ---------------------------------------------------------------- PRR
    elif cid == "PRR-EC-01":
        alts = mn.get("alternatives_considered") or []
        sel = bool(mn.get("selected_alternative_id"))
        rat = bool((mn.get("selection_rationale") or "").strip())
        if not sel:
            _set(result, "fail", "No concept selected")
        elif not rat:
            _set(result, "fail", "Concept selected, rationale missing")
        else:
            _set(result, "pass" if len(alts) >= 2 else "fail",
                 "Concept selected with rationale; {{n}} alternative(s) considered", n=len(alts))

    elif cid == "PRR-EC-02":
        orbit = (ctx["mission"] or {}).get("orbit") or {}
        alt = orbit.get("altitude_km")
        if orbit.get("orbit_type") and isinstance(alt, (int, float)) and alt > 0:
            life = orbit.get("mission_duration_years") or (ctx["mission"] or {}).get("design_lifetime_years") or 0
            _set(result, "pass" if life else "fail", "Orbit baseline: {{orbit}} {{alt}} km, {{inc}}°, {{life}} year(s)",
                 orbit=str(orbit.get("orbit_type")).upper(), alt=_fmt(float(alt)),
                 inc=_fmt(float(orbit.get("inclination_deg") or 0), 1), life=_fmt(float(life), 1))
        else:
            _set(result, "fail", "No orbit baseline")

    elif cid == "PRR-EC-03":
        n = ctx["function_count"] or 0
        _set(result, "pass" if n >= 1 else "fail", "{{n}} function(s) in the function tree", n=n)

    elif cid == "PRR-EC-04":
        hw = [e for e in elements if e.get("segment", "space") == "space" and e.get("in_scope") is not False]
        systems = sum(1 for e in hw if e.get("element_type") == "system")
        subs = sum(1 for e in hw if e.get("element_type") == "subsystem")
        _set(result, "pass" if systems >= 1 and subs >= 1 else "fail",
             "{{systems}} system(s), {{subsystems}} subsystem(s) in the product tree", systems=systems, subsystems=subs)

    elif cid == "PRR-EC-06":
        n_mission = sum(1 for r in reqs if r.get("level") == "mission")
        n_system = sum(1 for r in reqs if r.get("level") == "system")
        nomethod = sum(1 for r in reqs if not (r.get("verification_method") or "").strip())
        ok = n_mission >= 1 and n_system >= 1 and nomethod == 0
        _set(result, "pass" if ok else "fail",
             "{{mission}} mission and {{system}} system requirement(s); {{nomethod}} without a verification method",
             mission=n_mission, system=n_system, nomethod=nomethod)

    elif cid == "PRR-EC-07":
        comps = [e for e in elements if e.get("element_type") == "component"]
        if not comps:
            _set(result, "not_evaluated", "No components selected yet")
        else:
            rated = sum(1 for e in comps if e.get("trl") is not None)
            _set(result, "pass" if rated == len(comps) else "fail",
                 "{{rated}}/{{total}} components have a TRL", rated=rated, total=len(comps))

    elif cid == "PRR-EC-09":
        stations = list((ctx["mission"] or {}).get("ground_stations") or [])
        ground_els = [e for e in elements if e.get("segment") == "ground" and e.get("element_type") != "segment"]
        n = len(stations) or len(ground_els)
        _set(result, "pass" if n >= 1 else "fail", "{{n}} ground station(s) identified", n=n)

    elif cid == "PRR-EC-10":
        n = len([r for r in ctx["risks"] if (r.get("status") or "open") != "deleted"])
        _set(result, "pass" if n >= 1 else "fail", "{{n}} risk(s) in the risk register", n=n)

    elif cid == "PRR-EC-11":
        target = ctx["target_cost"]
        if not target or target <= 0:
            _set(result, "pass", "No cost target set")
        else:
            v = _need(result, dp, "cost.total_meur")
            if v:
                _set(result, "pass" if v[0] <= target else "fail",
                     "Cost {{cost}} MEUR vs target {{target}} MEUR", cost=_fmt(v[0], 1), target=_fmt(target, 1))

    elif cid == "PRR-EC-12":
        v = _need(result, dp, "debris.compliance_score")
        if v:
            _set(result, "pass" if v[0] >= 50 else "fail",
                 "Debris compliance score {{score}}/100", score=_fmt(v[0]))

    else:
        _set(result, "not_evaluated", "Auto-evaluation not implemented for this criterion")


def _ladder_budget(result: dict, ctx: dict) -> None:
    """Mass and power close with the system margin of the gate (margin_policy.yaml ladder).

    Convention (stated in the ladder): total = nominal × (1 + margin). Mass is the design
    loop's dry mass against the study mass target; power is the orbit demand in sunlight
    against the EOL array power.
    """
    from .margin_policy import system_margin_percent

    dp = ctx["dp"]
    v = _need(result, dp, "mass.dry_mass_kg", "power.total_sunlight_w", "power.sa_power_eol_w")
    if not v:
        return
    dry, demand, avail = v
    limit = ctx["target_mass"]
    if not limit or limit <= 0:
        _set(result, "not_evaluated", "No mass target or form factor to check the mass budget against")
        return
    m_pct = system_margin_percent(ctx["margin_gate"], "mass")
    p_pct = system_margin_percent(ctx["margin_gate"], "power")
    total = dry * (1 + m_pct / 100)
    ptotal = demand * (1 + p_pct / 100)
    ok = total <= limit and (avail > 0 and ptotal <= avail)
    _set(result, "pass" if ok else "fail",
         "Mass {{mass}} kg + {{margin}}% system margin = {{total}} kg vs {{limit}} kg; power {{power}} W + {{margin}}% = {{ptotal}} W vs {{avail}} W",
         mass=_fmt(dry, 2), margin=_fmt(m_pct), total=_fmt(total, 2), limit=_fmt(limit, 2),
         power=_fmt(demand, 1), ptotal=_fmt(ptotal, 1), avail=_fmt(avail, 1))
