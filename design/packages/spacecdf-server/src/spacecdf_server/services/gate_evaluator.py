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
import re
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
    "No spacecraft mass limit set: enter the target mass in the mission brief",
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
    # CDR (Nov 2026, phase 2): the CDR model (routers/cdr.py)
    "The CDR model is not available",
    "No TM/TC database yet: propose it from the design (CDR model)",
    "{{params}} parameters, {{hk}} HK structures, {{tc}} telecommands, {{events}} events; {{suggested}} suggestion(s) to review, {{alarms}} alarm finding(s)",
    "No rate tier or HK structure to check the downlink budget",
    "Housekeeping fits the downlink in {{ok}}/{{total}} regimes",
    # W3.05: the daily data budget (services/data_budget.gate_check)
    "No data budget yet: no mode, no contact plan or no link rate",
    "Daily budget case {{case}}: margin {{margin}} % (required {{required}} %); no HK store sized yet",
    "Daily budget case {{case}}: margin {{margin}} % (required {{required}} %); the stores hold {{days}} days at the worst rate (required {{need}})",
    "Housekeeping fits the downlink in {{ok}}/{{total}} regimes; daily budget case {{case}}: margin {{margin}} % (required {{required}} %); the stores hold {{days}} days (required {{need}})",
    "{{recovered}}/{{critical}} critical failure modes detected and recovered; {{alarms}} FDIR alarm finding(s)",
    "Safe mode and load-shed table defined; {{alarms}} alarm finding(s)",
    "Safe mode or load-shed table missing",
    "No AOCS mode table yet",
    "{{modes}} AOCS mode(s), {{transitions}} transition(s); {{alarms}} alarm and {{cautions}} caution finding(s)",
    "No rate ladder yet",
    "{{tiers}} rate tier(s), command-loss timer {{hours}} h; {{alarms}} alarm finding(s)",
    "{{positions}} position(s), {{gonogo}} GO/NO-GO situation(s), {{rules}} flight rule(s); {{uncovered}} critical telecommand(s) without a GO/NO-GO entry",
    "{{ok}}/{{total}} requirements have a verification method",
    # Nov 2026 (W2.03, W2.05, W1.08): requirement baseline fields and the one roll-up
    "{{ok}}/{{total}} requirements have a verification method and a threshold or an acceptance criterion",
    "{{n}} requirement(s) below mission level without a parent",
    "Mass {{mass}} kg + {{margin}}% system margin = {{total}} kg vs {{limit}} kg; orbit-average power {{power}} W ({{ptotal}} W with {{margin}}% margin) vs {{avail}} W generated at end of life",
    "Orbit-average power {{power}} W ({{ptotal}} W with {{pmargin}}% margin) vs {{avail}} W generated at end of life; mass margin {{mass}}%",
    # wave 2 (W4.09): QR-EC-01
    "{{ok}}/{{total}} requirements have a verification method and a close-out stage; without: {{codes}}",
    "All {{total}} requirements have a verification method and a close-out stage",
    # wave 2 integration: SRR-EC-04, 05, 07, 08 and the harness allowance of PDR-EC-04
    "{{answered}}/{{total}} must-answer position questions answered by the design; open: {{open}}",
    "All {{total}} must-answer position questions answered by the design",
    "No position questions to check",
    "{{critical}} critical conflict(s) unresolved: {{codes}}",
    "No critical conflict unresolved ({{major}} major, {{other}} other open)",
    "No model philosophy yet: propose the AIT models and test matrix",
    "{{philosophy}} model philosophy: {{models}} model(s), {{tests}} test(s) covering {{reqs}} requirement(s)",
    "{{philosophy}} model philosophy with {{models}} model(s) but no test in the test matrix",
    "Lowest subsystem TRL {{trl}} ({{subsystem}}); {{low}} subsystem(s) below TRL {{min}}: {{names}}",
    "Every subsystem at TRL {{min}} or above (lowest: {{subsystem}} at TRL {{trl}})",
    "No component has a TRL yet",
    "{{ok}}/{{total}} subsystems have at least one component or a mass allowance",
    # wave 3 (3.R4, 3.R5): SE deliverables, function coverage, allocated baseline, validation,
    # Decide-panel decisions (SRR-EC-04), ICD issue control (PDR-EC-02), reliability horizon
    "All {{total}} ICDs under issue control at Issue A and signed by both seats",
    "{{agreed}}/{{total}} ICDs under issue control at Issue A and signed by both seats; not agreed: {{unsigned}}",
    "All {{total}} trades due by the SRR decided in the Decide panel",
    "{{recorded}}/{{total}} trades due by the SRR decided in the Decide panel; open: {{open}}",
    "No trade due by the SRR recorded in the Decide panel",
    "All {{total}} deliverables of the gate ready",
    "{{ok}}/{{total}} deliverables of the gate ready; missing: {{names}}",
    "No deliverables listed for this gate",
    "The deliverables check is not available yet",
    "All {{total}} primary objectives have a validation activity performed by a stakeholder",
    "{{ok}}/{{total}} primary objectives have a validation activity performed by a stakeholder; without: {{ids}}",
    "All {{total}} primary objectives have an in-orbit validation activity planned",
    "{{ok}}/{{total}} primary objectives have an in-orbit validation activity planned; without: {{ids}}",
    "No in-orbit validation activity planned",
    "The validation plan is not available yet",
    "Allocations with the system margin exceed the limit: {{mass}} kg vs {{mlimit}} kg; {{power}} W vs {{plimit}} W",
    "Lines not agreed by their owner: {{names}}; {{mass}} kg vs {{mlimit}} kg; {{power}} W vs {{plimit}} W",
    "Mass and power lines agreed for {{n}} subsystem(s); {{mass}} ≤ {{mlimit}} kg; {{power}} ≤ {{plimit}} W",
    "No allocation ledger lines yet",
    "No mass or power line for: {{names}}",
    "{{n}} allocation line(s) without a covering requirement: {{names}}",
    "No function tree yet",
    "{{leaves}} leaf function(s) covered by requirements; {{subs}} space subsystem(s) with requirements",
    "{{uncovered}}/{{leaves}} leaf function(s) without a requirement: {{codes}}; {{nosubs}} space subsystem(s) without one: {{names}}",
    "{{n}} function(s); {{allocated}}/{{leaves}} leaf function(s) allocated",
    "{{n}} function(s); {{allocated}}/{{leaves}} leaf function(s) allocated; unallocated: {{codes}}",
    "Reliability {{rel}} over {{horizon}} vs target {{target}}",
    # integration (wave 3): ConOps scenarios (D), SEMP issue (X), debris assessment (L), reliability + FMEA (A)
    "ConOps summary documented; {{n}} operational scenario(s) with requirements",
    "{{n}} operational scenario(s) with requirements",
    "SEMP issue {{issue}} recorded",
    "SEMP content ready ({{parts}}/{{of}} parts): review it and record its issue",
    "The SEMP generator has no content yet ({{parts}}/{{of}} parts)",
    "No debris assessment has been run",
    "Debris assessment v{{version}} not accepted yet",
    "Debris assessment v{{version}} accepted, but the design changed since the run: run it again",
    "Debris assessment v{{version}} accepted, not compliant and no deviation recorded",
    "Debris assessment v{{version}} accepted at {{gate}}",
    "Reliability {{rel}} over {{horizon}} vs target {{target}}; FMEA {{rows}} line(s), {{critical}} critical, all linked",
    "Reliability analysis not acceptable: {{reasons}}",
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


#: wave 2 (W4.09): ``evaluated_by`` value of the QR / AR / FRR items that gate_reviews evaluates
REVIEW_RECORD = "review_record"


def review_record_criteria(canonical: str) -> list[dict[str, Any]]:
    """The review-record items of a gate after CDR (``qr``, ``ar``, ``frr``), from
    gate_exit_criteria.yaml, in the shape of the interim ``gate_reviews.POST_CDR_CRITERIA``
    rows: ``{id, question, category, owner_seat, evidence, auto?}`` (plus ``step``)."""
    gate = get_gate(canonical)
    out = []
    for ec in (gate or {}).get("exit_criteria") or []:
        if ec.get("evaluated_by") != REVIEW_RECORD:
            continue
        spec = {"id": ec["id"], "owner_seat": ec.get("owner_seat"), "category": ec.get("category", "review"),
                "question": ec.get("question", ""), "step": ec.get("step")}
        if ec.get("auto"):
            spec["auto"] = ec["auto"]
        else:
            spec["evidence"] = ec.get("evidence", "")
        out.append(spec)
    return out


def review_record_table(gates: tuple[str, ...] = ("qr", "ar", "frr")) -> dict[str, list[dict[str, Any]]]:
    """``{canonical gate: review_record_criteria(gate)}``: the drop-in for
    ``gate_reviews.POST_CDR_CRITERIA``."""
    return {g: review_record_criteria(g) for g in gates}


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
    cdr: dict[str, Any] | None = None,
    rollup: dict[str, Any] | None = None,
    conflicts: list[dict] | None = None,
    ait: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate all exit criteria for a gate and return structured results.

    ``phase_id`` is a phase id from the YAML or a gate name (MDR/PRR/SRR/PDR; MCR = MDR).
    ``mission``: the study's MissionRequirements (orbit, ground stations); ``function_count``:
    functions in the study's function tree; ``risks``: the study's risk register;
    ``margin_gate``: the margin-ladder step for budget criteria (default: this gate);
    ``cdr``: the CDR model summary (routers/cdr.cdr_gate_summary) the CDR criteria read.
    ``rollup``: ``services.rollup.compute(...).as_dict()`` (W1.08): when given (or as
    ``design_params["_rollup"]``), MDR-EC-07 and the budget criteria compare the modes
    orbit-average power and the rolled-up mass with EOL generation and the mass limit.
    ``requirements`` may carry ``parent_ids`` / ``objective_ids`` (routers/requirements.with_lists):
    further parents and objectives then count (W2.03).
    ``conflicts``: the study's unresolved analysis conflicts (SRR-EC-05); ``ait``: ``{"models",
    "tests"}`` of the AIT model philosophy (SRR-EC-07). Absent, those criteria are not evaluated.
    ``evidence``: :func:`collect_evidence` of the study (wave 3: function coverage, threshold-binding
    values, ICD issue control, allocation ledger, SE deliverables, validation, logbook decisions);
    else ``design_params["_evidence"]``, else the study's last collection.

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
        "cdr": cdr,
        # W3.05: the daily data budget (services/data_budget) for PDR-EC-06 / CDR-EC-04 — from the
        # CDR model summary (routers/cdr.cdr_gate_summary) or design_params["_data_budget"]
        "data_budget": (cdr or {}).get("data_budget")
        or (design_params.get("_data_budget") if isinstance(design_params, dict) else None),
        "rollup": rollup or (design_params or {}).get("_rollup") if isinstance(design_params, dict) else rollup,
        "conflicts": conflicts,
        "ait": ait,
    }
    ev = evidence
    if ev is None and isinstance(design_params, dict):
        ev = design_params.get("_evidence")
    if ev is None:
        sid = next((r.get("study_id") for r in ctx["reqs"] if r.get("study_id")), None) \
            or next((e.get("study_id") for e in ctx["elements"] if e.get("study_id")), None)
        ev = _EVIDENCE.get(sid or "")
    ctx["ev"] = ev or {}
    # wave 3 (3.R2): the figures the bound thresholds name (allocation closure, per-subsystem
    # roll-up, per-mode power, data budget) are design parameters for the compliance checks
    for k, v in (ctx["ev"].get("binding_values") or {}).items():
        ctx["dp"].setdefault(k, v)
    _add_budget_params(ctx)

    # wave 2 (W4.09): the review-record items of QR / AR / FRR are evaluated with the RID log by
    # services/gate_reviews.post_cdr_criteria (routers/gates.py appends them)
    results = [_evaluate_criterion(ec, ctx) for ec in gate.get("exit_criteria", [])
               if ec.get("evaluated_by") != REVIEW_RECORD]

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
    """A threshold the compliance tracker can check: parameter path, operator and a number."""
    raw = r.get("threshold_value")
    if not r.get("threshold_param_path") or not r.get("threshold_op") or raw in (None, ""):
        return False
    try:
        float(json.loads(raw) if isinstance(raw, str) else raw)
    except (ValueError, TypeError, json.JSONDecodeError):
        return False
    return True


_PASS_FAIL_TYPES = ("functional", "interface", "regulatory", "process")
_SHALL = re.compile(r"\b(shall|doit|doivent)\b")
_CITES_DOCUMENT = ("according to", "in accordance with", "as defined in", "as specified in", " per ", "ecss-",
                   " icd", "standard", "specification", "conformément", "selon la norme")


def _stated_threshold(r: dict) -> bool:
    """A threshold stated on the requirement (W2.05): an operator with a number, a range
    (``in_range``: {min, max}) or a date (``before`` / ``after``), or ``exists``. A parameter path
    is not needed: it only makes the threshold checkable against the design."""
    op = r.get("threshold_op")
    if not op:
        return False
    if op == "exists":
        return True
    raw = r.get("threshold_value")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            pass
    if raw in (None, ""):
        return False
    if op == "in_range":
        return isinstance(raw, dict) and ("min" in raw or "max" in raw)
    if op in ("before", "after"):
        return isinstance(raw, str) and len(raw) >= 4
    try:
        float(raw)
    except (TypeError, ValueError):
        return False
    return True


def _has_acceptance(r: dict) -> bool:
    """An acceptance criterion in place of a threshold (W2.05): an explicit one, or the
    statement itself when it is verified by test, inspection or review (pass/fail outcome), or
    by analysis of a pass/fail statement or of compliance with a cited document."""
    # wave 3 step 0: the v2 ``acceptance`` column is an explicit criterion (3.R2 refines SRR-EC-02)
    if (r.get("acceptance_criterion") or r.get("acceptance") or "").strip():
        return True
    text = f" {(r.get('text') or '').lower()} "
    if not _SHALL.search(text):
        return False                       # no statement to pass or fail
    m = r.get("verification_method")
    if m in ("T", "I", "R", "D"):
        return True
    if m == "A":
        return r.get("req_type") in _PASS_FAIL_TYPES or any(w in text for w in _CITES_DOCUMENT)
    return False


def _is_objective_row(r: dict) -> bool:
    return r.get("category") == "objective" or str(r.get("code") or "").startswith("OBJ-")


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
        # wave 3 (3.D5): the operational scenarios with requirements count as the ConOps too
        n = _ev(ctx).get("conops_scenarios")
        if (mn.get("conops_summary") or "").strip():
            if n:
                _set(result, "pass", "ConOps summary documented; {{n}} operational scenario(s) with requirements", n=n)
            else:
                _set(result, "pass", "ConOps summary documented")
        elif n:
            _set(result, "pass", "{{n}} operational scenario(s) with requirements", n=n)
        else:
            _set(result, "fail", "ConOps summary is empty")

    elif cid == "MDR-EC-07" and _rollup_power(ctx) is not None and _get_param(dp, "power.sa_power_eol_w"):
        # W1.08: the modes orbit average (nominal, with the gate's system margin) against EOL generation
        avg, with_margin, p_pct = _rollup_power(ctx)
        avail = _get_param(dp, "power.sa_power_eol_w") or 0.0
        mass = _get_param(dp, "systems.mass_margin_percent")
        if mass is None:
            ru_mass = (ctx["rollup"] or {}).get("mass") or {}
            lim, tot = ru_mass.get("limit_kg"), ru_mass.get("with_system_margin_kg")
            mass = 100.0 * (lim - tot) / lim if lim and tot is not None else None
        ok = avail > 0 and with_margin <= avail and (mass is None or mass > -50)
        _set(result, "pass" if ok else "fail",
             "Orbit-average power {{power}} W ({{ptotal}} W with {{pmargin}}% margin) vs {{avail}} W generated at end of life; mass margin {{mass}}%",
             power=_fmt(avg, 2), ptotal=_fmt(with_margin, 2), pmargin=_fmt(p_pct), avail=_fmt(avail, 1),
             mass="?" if mass is None else _fmt(mass))

    elif cid == "MDR-EC-07":
        if (_get_param(dp, "systems.power_margin_percent") is not None
                and _get_param(dp, "systems.mass_margin_percent") is None and not ctx["target_mass"]):
            # The design loop ran, but it has no mass limit to compute a margin against.
            _set(result, "not_evaluated", "No spacecraft mass limit set: enter the target mass in the mission brief")
            return
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
            # wave 3: the priced cost (A, 3.A7: labour, test campaigns, reserve) wins over the
            # design loop's parametric estimate
            v = [_cost_total(ctx)] if _cost_total(ctx) is not None else _need(result, dp, "cost.total_meur")
            if v:
                cost = v[0]
                # 20 % allowance on Phase 0 estimates
                _set(result, "pass" if cost <= target * 1.2 else "fail",
                     "Cost {{cost}} MEUR vs target {{target}} MEUR", cost=_fmt(cost, 1), target=_fmt(target, 1))

    elif cid == "MDR-EC-09":
        # The team's register is the evidence (textbook § 15.1); the risk agent's
        # findings count only when the register is still empty.
        n = len([r for r in ctx["risks"] if (r.get("status") or "open") != "deleted"])
        agent = _get_param(dp, "risk.total_risks")
        if n >= 1:
            _set(result, "pass", "{{n}} risk(s) in the risk register", n=n)
        elif agent:
            _set(result, "pass", "Risk analysis run: {{n}} risk(s) identified", n=int(agent))
        else:
            _set(result, "fail", "{{n}} risk(s) in the risk register", n=0)

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
            traced_ids = {o for r in reqs for o in ([r.get("objective_id")] + list(r.get("objective_ids") or []))
                          if o}
            traced = sum(1 for o in objectives
                         if o.get("traced_to_requirements") or (o.get("id") and o.get("id") in traced_ids))
            _set(result, "pass" if traced == len(objectives) else "fail",
                 "{{traced}}/{{total}} objectives traced to requirements", traced=traced, total=len(objectives))

    elif cid == "SRR-EC-02":
        # Interface requirements (level "interface") are checked by test or inspection of the
        # interface, not against a design threshold: they are counted for completeness only.
        # Stakeholder needs and objective rows are verified through the requirements below them.
        # W2.05: a stated threshold (number, range, date) or an acceptance criterion is enough.
        sys_reqs = [r for r in reqs if r.get("level") not in ("interface", "stakeholder") and not _is_objective_row(r)]
        from .interface_requirements import ird_status
        orphans = ird_status(ctx["interfaces"], reqs)["without_interface"]
        if not sys_reqs:
            _set(result, "fail", "No requirements defined")
        else:
            ok = sum(1 for r in sys_reqs if r.get("verification_method")
                     and (_has_threshold(r) or _stated_threshold(r) or _has_acceptance(r)))
            if ok == len(sys_reqs) and orphans:
                _set(result, "fail", "{{n}} interface requirement(s) name no accepted interface", n=len(orphans))
            else:
                _set(result, "pass" if ok == len(sys_reqs) else "fail",
                     "{{ok}}/{{total}} requirements have a verification method and a threshold or an acceptance criterion",
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

    elif cid in ("SRR-EC-06", "PDR-EC-03", "PRR-EC-05", "CDR-EC-10"):
        _ladder_budget(result, ctx)

    elif cid == "SRR-EC-11":
        # W2.03: a further parent (``derives`` relation, served as ``parent_ids``) counts
        live = {r.get("id") for r in reqs}
        below = [r for r in reqs if r.get("level") in ("segment", "system", "subsystem")]
        orphans = [r for r in below
                   if not any(p in live for p in (r.get("parent_ids")
                                                  or [r.get("parent_id") or r.get("derived_from_requirement_id")]))]
        if not below:
            _set(result, "not_evaluated", "No requirements defined")
        else:
            _set(result, "fail" if orphans else "pass",
                 "{{n}} requirement(s) below mission level without a parent", n=len(orphans))

    elif cid == "QR-EC-01":
        # wave 2 (W4.09): the verification control document is complete at qualification
        spec = [r for r in reqs if r.get("level") != "stakeholder"]
        if not spec:
            _set(result, "not_evaluated", "No requirements defined")
        else:
            miss = [r for r in spec if not (r.get("verification_method") or r.get("verification_methods"))
                    or not r.get("verification_phase")]
            if miss:
                codes = sorted(str(r.get("code") or r.get("id")) for r in miss)
                _set(result, "fail", "{{ok}}/{{total}} requirements have a verification method and a close-out stage; without: {{codes}}",
                     ok=len(spec) - len(miss), total=len(spec),
                     codes=", ".join(codes[:12]) + (" …" if len(codes) > 12 else ""))
            else:
                _set(result, "pass", "All {{total}} requirements have a verification method and a close-out stage",
                     total=len(spec))

    elif cid == "SRR-EC-04":
        _decisions_criterion(result, ctx)

    # ---------------------------------------------------------------- wave 3 (3.R4)
    elif cid.endswith("-SE-01"):
        _se_criterion(cid, result, ctx)

    elif cid in ("SRR-EC-12", "PDR-EC-08"):
        _coverage_criterion(result, ctx)

    elif cid == "PDR-EC-07":
        _allocation_criterion(result, ctx)

    elif cid == "SRR-EC-13":
        _validation_criterion(result, ctx)

    elif cid == "FRR-EC-01":
        _iov_criterion(result, ctx)

    elif cid == "SRR-EC-05":
        conflicts = ctx.get("conflicts")
        if conflicts is None:
            _set(result, "not_evaluated", "Auto-evaluation not implemented for this criterion")
        else:
            open_ = [c for c in conflicts if not c.get("resolved") and not c.get("resolved_at")]
            crit = [c for c in open_ if str(c.get("severity") or "").lower() == "critical"]
            if crit:
                codes = sorted({str(c.get("code") or c.get("title") or "?") for c in crit})
                _set(result, "fail", "{{critical}} critical conflict(s) unresolved: {{codes}}",
                     critical=len(crit), codes=", ".join(codes[:8]) + (" …" if len(codes) > 8 else ""))
            else:
                major = sum(1 for c in open_ if str(c.get("severity") or "").lower() == "major")
                _set(result, "pass", "No critical conflict unresolved ({{major}} major, {{other}} other open)",
                     major=major, other=len(open_) - major)

    elif cid == "SRR-EC-07":
        ait = ctx.get("ait")
        if ait is None:
            _set(result, "not_evaluated", "Auto-evaluation not implemented for this criterion")
        else:
            models, tests = list(ait.get("models") or []), list(ait.get("tests") or [])
            phil = sorted({str(m.get("philosophy") or "") for m in models if m.get("philosophy")})
            philosophy = "/".join(phil) or "?"
            if not models:
                _set(result, "fail", "No model philosophy yet: propose the AIT models and test matrix")
            elif not tests:
                _set(result, "fail", "{{philosophy}} model philosophy with {{models}} model(s) but no test in the test matrix",
                     philosophy=philosophy, models=len(models))
            else:
                covered = {c for t in tests for c in (t.get("requirement_codes") or [])}
                _set(result, "pass", "{{philosophy}} model philosophy: {{models}} model(s), {{tests}} test(s) covering {{reqs}} requirement(s)",
                     philosophy=philosophy, models=len(models), tests=len(tests), reqs=len(covered))

    elif cid == "SRR-EC-08":
        _trl_criterion(result, ctx)

    elif cid == "SRR-EC-09":
        _semp_criterion(result, ctx)

    elif cid == "SRR-EC-10" and "debris" in _ev(ctx):
        _debris_criterion(result, ctx)

    elif cid == "SRR-EC-10":
        v = _need(result, dp, "sustainability.score", "debris.casualty_compliant")
        if v:
            score, casualty = v
            ok = score >= 55 and casualty >= 1
            key = ("Sustainability score {{score}}/100; casualty risk compliant" if casualty >= 1
                   else "Sustainability score {{score}}/100; casualty risk not compliant")
            _set(result, "pass" if ok else "fail", key, score=_fmt(score))

    # ---------------------------------------------------------------- PDR
    elif cid in ("PDR-EC-01", "CDR-EC-01"):
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

    elif cid == "PDR-EC-02" and _ev(ctx).get("icds") and _icd_pdr(result, ctx):
        pass

    elif cid in ("PDR-EC-02", "CDR-EC-02"):
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

            # a harness subsystem is carried as a mass allowance in the roll-up (W1.08), not as units
            harness_kg = float((((ctx.get("rollup") or {}).get("mass") or {}).get("harness_kg")) or 0.0)

            def allowance(sub: dict) -> bool:
                return harness_kg > 0 and (sub.get("subsystem_domain") == "harness"
                                           or str(sub.get("name") or "").strip().lower() == "harness")

            ok = sum(1 for s in subs if has_component(s.get("id", "")) or allowance(s))
            key = ("{{ok}}/{{total}} subsystems have at least one component or a mass allowance"
                   if any(allowance(s) for s in subs) else "{{ok}}/{{total}} subsystems have at least one component")
            _set(result, "pass" if ok == len(subs) else "fail", key, ok=ok, total=len(subs))

    elif cid == "PDR-EC-06":
        _data_budget_criterion(result, ctx)

    elif cid == "PDR-EC-05" and isinstance(_ev(ctx).get("reliability"), dict) and "ok" in _ev(ctx)["reliability"]:
        _reliability_criterion(result, ctx)

    elif cid in ("PDR-EC-05",):
        # wave 3 (3.A5): A's reliability analysis wins over the design loop's estimate; the
        # evidence quotes the mission-success horizon it is computed over (3.A1)
        rel_ev = _first_num(_ev(ctx).get("reliability") or {}, "mission_reliability", "reliability")
        v = [rel_ev] if rel_ev is not None else _need(result, dp, "reliability.mission_reliability")
        if v:
            target = ctx["rel_target"] or 0.9
            hz = _reliability_horizon(ctx)
            if hz:
                _set(result, "pass" if v[0] >= target else "fail", "Reliability {{rel}} over {{horizon}} vs target {{target}}",
                     rel=_fmt(v[0], 3), horizon=hz, target=_fmt(target, 2))
            else:
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
        cov = _ev(ctx).get("function_coverage")
        if n >= 1 and cov and cov.get("leaves"):
            # wave 3: every leaf function allocated to an element
            un = list(cov.get("leaves_unallocated") or [])
            if un:
                _set(result, "fail", "{{n}} function(s); {{allocated}}/{{leaves}} leaf function(s) allocated; unallocated: {{codes}}",
                     n=n, allocated=cov.get("leaves_allocated") or 0, leaves=cov["leaves"],
                     codes=", ".join(un[:10]) + (" …" if len(un) > 10 else ""))
            else:
                _set(result, "pass", "{{n}} function(s); {{allocated}}/{{leaves}} leaf function(s) allocated",
                     n=n, allocated=cov.get("leaves_allocated") or 0, leaves=cov["leaves"])
        else:
            _set(result, "pass" if n >= 1 else "fail", "{{n}} function(s) in the function tree", n=n)

    elif cid == "PRR-EC-04":
        hw = [e for e in elements if e.get("segment", "space") == "space" and e.get("in_scope") is not False]
        systems = sum(1 for e in hw if e.get("element_type") == "system")
        subs = sum(1 for e in hw if e.get("element_type") == "subsystem")
        _set(result, "pass" if systems >= 1 and subs >= 1 else "fail",
             "{{systems}} system(s), {{subsystems}} subsystem(s) in the product tree", systems=systems, subsystems=subs)

    elif cid == "PRR-EC-06":
        n_mission = sum(1 for r in reqs if r.get("level") == "mission" and not _is_objective_row(r))
        n_system = sum(1 for r in reqs if r.get("level") in ("segment", "system"))
        nomethod = sum(1 for r in reqs if not (r.get("verification_method") or "").strip()
                       and r.get("level") != "stakeholder" and not _is_objective_row(r))
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
            v = [_cost_total(ctx)] if _cost_total(ctx) is not None else _need(result, dp, "cost.total_meur")
            if v:
                _set(result, "pass" if v[0] <= target else "fail",
                     "Cost {{cost}} MEUR vs target {{target}} MEUR", cost=_fmt(v[0], 1), target=_fmt(target, 1))

    elif cid == "PRR-EC-12":
        v = _need(result, dp, "debris.compliance_score")
        if v:
            _set(result, "pass" if v[0] >= 50 else "fail",
                 "Debris compliance score {{score}}/100", score=_fmt(v[0]))

    # ---------------------------------------------------------------- CDR (Nov 2026)
    elif cid.startswith("CDR-EC-"):
        _cdr_criterion(cid, result, ctx)

    else:
        _set(result, "not_evaluated", "Auto-evaluation not implemented for this criterion")


def _cdr_criterion(cid: str, result: dict, ctx: dict) -> None:  # noqa: C901 — one branch per criterion
    """CDR-EC-03 … 09 and 11 from the CDR model (routers/cdr.cdr_gate_summary)."""
    if cid == "CDR-EC-11":
        reqs = ctx["reqs"]
        if not reqs:
            _set(result, "not_evaluated", "No requirements defined")
            return
        ok = sum(1 for r in reqs if (r.get("verification_method") or "").strip())
        _set(result, "pass" if ok == len(reqs) else "fail", "{{ok}}/{{total}} requirements have a verification method",
             ok=ok, total=len(reqs))
        return
    cdr = ctx.get("cdr")
    if not cdr:
        _set(result, "not_evaluated", "The CDR model is not available")
        return
    rows = [r for r in cdr.get("rows") or [] if not r.get("deleted_at") and r.get("status") != "rejected"]
    checks = cdr.get("checks") or []

    def n(kind: str) -> int:
        return sum(1 for r in rows if r.get("kind") == kind)

    def count(prefixes: tuple[str, ...], severity: str = "alarm") -> int:
        return sum(1 for c in checks if c.get("severity") == severity and str(c.get("rule", "")).startswith(prefixes))

    if cid == "CDR-EC-03":
        if not (n("parameters") and n("hk") and n("commands")):
            _set(result, "fail", "No TM/TC database yet: propose it from the design (CDR model)")
            return
        tm_kinds = {"settings", "apids", "services", "parameters", "hk", "commands", "events"}
        sug = sum(1 for r in rows if r.get("kind") in tm_kinds and r.get("status") == "suggested")
        al = count(("TMTC",))
        ok = n("events") > 0 and sug == 0 and al == 0
        _set(result, "pass" if ok else "fail",
             "{{params}} parameters, {{hk}} HK structures, {{tc}} telecommands, {{events}} events; {{suggested}} suggestion(s) to review, {{alarms}} alarm finding(s)",
             params=n("parameters"), hk=n("hk"), tc=n("commands"), events=n("events"), suggested=sug, alarms=al)
    elif cid == "CDR-EC-04":
        regs = [r for r in (cdr.get("budget") or {}).get("regimes") or [] if r.get("ok") is not None]
        if not regs:
            _set(result, "not_evaluated", "No rate tier or HK structure to check the downlink budget")
            return
        ok = sum(1 for r in regs if r["ok"])
        gc = _data_budget_check(ctx)
        if gc is None:
            _set(result, "pass" if ok == len(regs) else "fail", "Housekeeping fits the downlink in {{ok}}/{{total}} regimes",
                 ok=ok, total=len(regs))
            return
        _set(result, "pass" if ok == len(regs) and gc.get("ok") else "fail",
             "Housekeeping fits the downlink in {{ok}}/{{total}} regimes; daily budget case {{case}}: margin {{margin}} % (required {{required}} %); the stores hold {{days}} days (required {{need}})",
             ok=ok, total=len(regs), **_db_params(gc))
    elif cid == "CDR-EC-05":
        f = cdr.get("fmeca") or {}
        crit, rec = int(f.get("critical") or 0), int(f.get("critical_recovered") or 0)
        al = sum(1 for c in checks if c.get("severity") == "alarm" and str(c.get("rule", "")).startswith("FDIR")
                 and c.get("rule") != "FDIR-FMECA")
        if not n("monitors"):
            _set(result, "fail", "{{recovered}}/{{critical}} critical failure modes detected and recovered; {{alarms}} FDIR alarm finding(s)",
                 recovered=rec, critical=crit, alarms=al)
            return
        _set(result, "pass" if rec == crit and al == 0 else "fail",
             "{{recovered}}/{{critical}} critical failure modes detected and recovered; {{alarms}} FDIR alarm finding(s)",
             recovered=rec, critical=crit, alarms=al)
    elif cid == "CDR-EC-06":
        if not (n("safe_mode") and n("load_shed")):
            _set(result, "fail", "Safe mode or load-shed table missing")
            return
        al = sum(1 for c in checks if c.get("severity") == "alarm"
                 and str(c.get("rule", "")).startswith(("FDIR-SAFE", "FDIR-SHED", "EL-STATE")))
        _set(result, "pass" if al == 0 else "fail", "Safe mode and load-shed table defined; {{alarms}} alarm finding(s)", alarms=al)
    elif cid == "CDR-EC-07":
        if not n("aocs_modes"):
            _set(result, "fail", "No AOCS mode table yet")
            return
        al = count(("AOCS",))
        ca = count(("AOCS",), "caution")
        _set(result, "pass" if al == 0 and ca == 0 else "fail",
             "{{modes}} AOCS mode(s), {{transitions}} transition(s); {{alarms}} alarm and {{cautions}} caution finding(s)",
             modes=n("aocs_modes"), transitions=n("aocs_transitions"), alarms=al, cautions=ca)
    elif cid == "CDR-EC-08":
        if not n("rate_tiers"):
            _set(result, "fail", "No rate ladder yet")
            return
        ttc = next((r.get("data") or {} for r in rows if r.get("kind") == "ttc"), {})
        to = ttc.get("cmd_loss_switch_timeout_s")
        al = count(("TTC",))
        ok = al == 0 and bool(ttc) and isinstance(to, (int, float)) and to > 0
        _set(result, "pass" if ok else "fail", "{{tiers}} rate tier(s), command-loss timer {{hours}} h; {{alarms}} alarm finding(s)",
             tiers=n("rate_tiers"), hours=_fmt(float(to) / 3600.0, 1) if isinstance(to, (int, float)) else "–", alarms=al)
    elif cid == "CDR-EC-09":
        unc = sum(1 for c in checks if c.get("rule") == "OPS-GNG")
        ok = n("positions") > 0 and n("gonogo") > 0 and n("flight_rules") > 0 and unc == 0
        _set(result, "pass" if ok else "fail",
             "{{positions}} position(s), {{gonogo}} GO/NO-GO situation(s), {{rules}} flight rule(s); {{uncovered}} critical telecommand(s) without a GO/NO-GO entry",
             positions=n("positions"), gonogo=n("gonogo"), rules=n("flight_rules"), uncovered=unc)
    else:
        _set(result, "not_evaluated", "Auto-evaluation not implemented for this criterion")


def _data_budget_check(ctx: dict) -> dict | None:
    b = ctx.get("data_budget")
    if not b:
        return None
    from .data_budget import gate_check
    return gate_check(b, ctx.get("margin_gate"))


def _db_params(gc: dict) -> dict:
    held = [x["days_held_worst"] for x in gc.get("stores") or [] if x.get("days_held_worst") is not None]
    return {"case": gc.get("case") or "–", "margin": _fmt(float(gc["margin_pct"]), 1) if gc.get("margin_pct") is not None else "–",
            "required": _fmt(float(gc.get("required_percent") or 0)), "days": _fmt(min(held), 1) if held else "–",
            "need": _fmt(float(gc.get("store_days") or 0))}


def _data_budget_criterion(result: dict, ctx: dict) -> None:
    """PDR-EC-06 (W3.05): the daily data budget closes with the gate's margin in the
    diagnostics-campaign case and every sized HK store holds the required days."""
    gc = _data_budget_check(ctx)
    if gc is None or gc.get("closes") is None:
        _set(result, "not_evaluated" if gc is None else "fail", "No data budget yet: no mode, no contact plan or no link rate")
        return
    if not gc.get("stores"):
        _set(result, "fail", "Daily budget case {{case}}: margin {{margin}} % (required {{required}} %); no HK store sized yet",
             **{k: v for k, v in _db_params(gc).items() if k in ("case", "margin", "required")})
        return
    _set(result, "pass" if gc["ok"] else "fail",
         "Daily budget case {{case}}: margin {{margin}} % (required {{required}} %); the stores hold {{days}} days at the worst rate (required {{need}})",
         **_db_params(gc))


def _rollup_power(ctx: dict) -> tuple[float, float, float] | None:
    """(orbit average, with the gate's system margin, margin %) from the roll-up, or None."""
    ru = ctx.get("rollup") or {}
    p = ru.get("power") or {}
    avg = p.get("orbit_average_w")
    if avg is None:
        return None
    from .margin_policy import system_margin_percent
    pct = system_margin_percent(ctx["margin_gate"], "power")
    return float(avg), float(avg) * (1 + pct / 100), pct


def _ladder_budget(result: dict, ctx: dict) -> None:
    """Mass and power close with the system margin of the gate (margin_policy.yaml ladder).

    Convention (stated in the ladder): total = nominal × (1 + margin). With the roll-up
    (W1.08) the mass is the rolled-up nominal mass with maturity margins and the power is the
    modes orbit average, both against EOL generation and the mass limit; without it, the
    design loop's dry mass and orbit demand in sunlight are used, as before.
    """
    from .margin_policy import system_margin_percent

    dp = ctx["dp"]
    rp = _rollup_power(ctx)
    if rp is not None:
        v = _need(result, dp, "power.sa_power_eol_w")
        if not v:
            return
        avail = v[0]
        ru_mass = (ctx["rollup"] or {}).get("mass") or {}
        nominal = ru_mass.get("with_maturity_kg") or ru_mass.get("cbe_kg")
        limit = ctx["target_mass"] or ru_mass.get("limit_kg")
        if not limit or limit <= 0 or not nominal:
            _set(result, "not_evaluated", "No mass target or form factor to check the mass budget against")
            return
        m_pct = system_margin_percent(ctx["margin_gate"], "mass")
        total = nominal * (1 + m_pct / 100)
        avg, ptotal, _ = rp
        ok = total <= limit and (avail > 0 and ptotal <= avail)
        _set(result, "pass" if ok else "fail",
             "Mass {{mass}} kg + {{margin}}% system margin = {{total}} kg vs {{limit}} kg; orbit-average power {{power}} W ({{ptotal}} W with {{margin}}% margin) vs {{avail}} W generated at end of life",
             mass=_fmt(nominal, 2), margin=_fmt(m_pct), total=_fmt(total, 2), limit=_fmt(limit, 2),
             power=_fmt(avg, 2), ptotal=_fmt(ptotal, 2), avail=_fmt(avail, 1))
        return
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


# --------------------------------------------------------------------------- wave 2 integration

#: budget figures the requirement thresholds can name (``threshold_param_path``), derived from the
#: one roll-up (W1.08), the data budget (W3.02) and the mission's design link case (W4.04) so the
#: budget rows check the study's own numbers, not the design loop's generic ones
BUDGET_PARAMS = ("budget.mass_total_dry_kg", "budget.mass_with_system_margin_kg",
                 "budget.mass_system_margin_available_percent", "budget.power_margin_eol_percent",
                 "budget.data_margin_percent", "budget.link_margin_design_case_db")


def _add_budget_params(ctx: dict) -> None:
    """``budget.*`` parameters in ``ctx["dp"]`` (an explicit parameter of that name wins)."""
    dp = ctx["dp"]
    ru = ctx.get("rollup") or {}
    mass = ru.get("mass") or {}
    vals: dict[str, float] = {}
    if mass.get("total_dry_kg") is not None:
        vals["budget.mass_total_dry_kg"] = float(mass["total_dry_kg"])
    if mass.get("with_system_margin_kg") is not None:
        vals["budget.mass_with_system_margin_kg"] = float(mass["with_system_margin_kg"])
    limit = ctx.get("target_mass") or mass.get("limit_kg")
    wm = mass.get("with_maturity_kg")
    if limit and wm:
        # the system margin the limit leaves on the margined mass: (limit - margined) / margined
        vals["budget.mass_system_margin_available_percent"] = round(100.0 * (float(limit) - float(wm)) / float(wm), 2)
    avg = (ru.get("power") or {}).get("orbit_average_w")
    eol = _get_param(dp, "power.sa_power_eol_w")
    if avg and eol is not None:
        vals["budget.power_margin_eol_percent"] = round(100.0 * (eol - float(avg)) / float(avg), 2)
    try:
        gc = _data_budget_check(ctx)
    except Exception:  # noqa: BLE001 — a malformed budget leaves the figure out
        gc = None
    m = (gc or {}).get("margin_pct") if isinstance(gc, dict) else None
    if m is None:
        cl = (ctx.get("data_budget") or {}).get("closure") if isinstance(ctx.get("data_budget"), dict) else None
        m = (cl or {}).get("margin_pct")
    if isinstance(m, (int, float)) and not isinstance(m, bool):
        vals["budget.data_margin_percent"] = float(m)
    link = (ctx.get("mission") or {}).get("link") or {}
    lm = link.get("margin_db") if isinstance(link, dict) else None
    if isinstance(lm, (int, float)) and not isinstance(lm, bool):
        vals["budget.link_margin_design_case_db"] = float(lm)
    for k, v in vals.items():
        dp.setdefault(k, v)


def _positions_criterion(result: dict, ctx: dict) -> None:
    """SRR-EC-04: every must-answer question of the engineering positions (KB positions.yaml)
    has its related design parameters (routers/positions guidance on the gate's parameters)."""
    try:
        from ..routers.positions import _compute_guidance, _load_positions
        positions = _load_positions()
    except Exception:  # noqa: BLE001 — no positions file: nothing to check
        positions = []
    params = {k: v for k, v in ctx["dp"].items() if not str(k).startswith("_")}
    total, open_ = 0, []
    for pos in positions:
        g = _compute_guidance(pos, params)
        for q in pos.key_questions:
            if q.priority == "must_answer" and q.related_parameters:
                total += 1
        open_ += [f"{pos.id}:{qs.question_id}" for qs in g.open_questions if qs.priority == "must_answer"]
    if not total:
        _set(result, "not_evaluated", "No position questions to check")
    elif open_:
        _set(result, "fail", "{{answered}}/{{total}} must-answer position questions answered by the design; open: {{open}}",
             answered=total - len(open_), total=total, open=", ".join(open_[:8]) + (" …" if len(open_) > 8 else ""))
    else:
        _set(result, "pass", "All {{total}} must-answer position questions answered by the design", total=total)


#: SRR-EC-08: the lowest TRL a subsystem may have at Phase B entry (gate_exit_criteria.yaml evidence)
MIN_TRL_PHASE_B = 4


def _trl_criterion(result: dict, ctx: dict) -> None:
    """SRR-EC-08: a subsystem's TRL is the lowest TRL of the components below it."""
    elements = ctx["elements"]
    by_id = {e.get("id"): e for e in elements}

    def subsystem_of(e: dict) -> dict | None:
        seen = 0
        cur = by_id.get(e.get("parent_id"))
        while cur is not None and seen < 20:
            if cur.get("element_type") == "subsystem":
                return cur
            cur = by_id.get(cur.get("parent_id"))
            seen += 1
        return None

    trl: dict[str, tuple[int, str]] = {}
    for e in elements:
        if e.get("element_type") != "component" or e.get("in_scope") is False:
            continue
        t = e.get("trl")
        if not isinstance(t, (int, float)) or isinstance(t, bool):
            continue
        sub = subsystem_of(e)
        name = str((sub or {}).get("name") or e.get("name") or "?")
        if name not in trl or int(t) < trl[name][0]:
            trl[name] = (int(t), str(e.get("name") or ""))
    if not trl:
        _set(result, "not_evaluated", "No component has a TRL yet")
        return
    lowest = min(trl.items(), key=lambda kv: kv[1][0])
    low = sorted(n for n, (t, _) in trl.items() if t < MIN_TRL_PHASE_B)
    if low:
        _set(result, "fail", "Lowest subsystem TRL {{trl}} ({{subsystem}}); {{low}} subsystem(s) below TRL {{min}}: {{names}}",
             trl=lowest[1][0], subsystem=lowest[0], low=len(low), min=MIN_TRL_PHASE_B, names=", ".join(low))
    else:
        _set(result, "pass", "Every subsystem at TRL {{min}} or above (lowest: {{subsystem}} at TRL {{trl}})",
             min=MIN_TRL_PHASE_B, subsystem=lowest[0], trl=lowest[1][0])


# --------------------------------------------------------------------------- wave 3 (3.R4, 3.R5)
#
# Evidence the wave-3 criteria read. ``collect_evidence(study_id)`` gathers it asynchronously
# from the owners' evidence functions (R: function coverage, threshold-binding values, ICD issue
# control, allocation requirements; A: the allocation ledger, reliability, cost; S: the SE
# deliverables and the validation coverage; the logbook: decisions recorded for the study). The
# gate route passes it to ``evaluate_gate(evidence=…)`` (or as ``design_params["_evidence"]``);
# the last collection per study is also kept, so an evaluation without it still sees it.

_EVIDENCE: dict[str, dict[str, Any]] = {}

#: the space subsystems PDR-EC-07 expects mass and power lines for (v2 element codes); a harness
#: carried as a roll-up allowance has none
LEDGER_TYPES = ("mass", "power_avg")
SE_GATES = ("mdr", "prr", "srr", "pdr", "cdr")


async def _maybe(coro_fn, *a, **k) -> Any:
    try:
        res = await coro_fn(*a, **k)
    except Exception:  # noqa: BLE001 — an owner's evidence is missing: the criterion says so
        logger.debug("evidence %s unavailable", getattr(coro_fn, "__name__", coro_fn), exc_info=True)
        return None
    if isinstance(res, dict) and res.get("status") == "not_implemented":
        return None
    return res


async def _ledger_lines(study_id: str) -> list[dict] | None:
    """The allocation-ledger lines (A, 3.A2): A's ``allocation_ledger.status`` when it exists,
    else the ``allocation_ledger`` table read directly."""
    try:
        from . import allocation_ledger as al            # A's ledger (3.A2)
        led = await al.list_lines(study_id)
        lines = led.get("items") if isinstance(led, dict) else led
        if isinstance(lines, list):
            return lines
    except Exception:  # noqa: BLE001
        pass
    try:
        from .allocation_requirements import _ledger
        return await _ledger(study_id)
    except Exception:  # noqa: BLE001
        return None


def _panel_decisions(study_id: str) -> dict[str, list[str]] | None:
    """Trades of the study due by the SRR and those decided in the Decide panel (SRR-EC-04)."""
    try:
        from . import trades as tr
        from ..routers.studies import get_study_store
        st = get_study_store().get(study_id)
        if st is None:
            return None
        due, decided = [], []
        for tid, rec in tr.normalise_records(getattr(st, "trade_records", None)).items():
            state = rec.get("state") or {}
            if str(state.get("gate") or "").lower() in ("mdr", "prr", "srr"):
                due.append(tid)
                if state.get("status") == "decided":
                    decided.append(tid)
        return {"due": sorted(due), "decided": sorted(decided)}
    except Exception:  # noqa: BLE001
        logger.debug("trades unavailable", exc_info=True)
        return None


async def collect_evidence(study_id: str, gates: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """Everything the wave-3 criteria read (see above). Never raises. ``gates``: the canonical
    gates about to be evaluated (the SE deliverables are evaluated for those only; all when None)."""
    from .requirement_queries import function_coverage
    from .threshold_binding import values as binding_values
    from .interface_requirements import icd_status
    from .allocation_requirements import status as ar_status
    ev: dict[str, Any] = {"study_id": study_id}
    ev["function_coverage"] = await _maybe(function_coverage, study_id)
    ev["binding_values"] = await _maybe(binding_values, study_id) or {}
    ev["icds"] = await _maybe(icd_status, study_id, gate="pdr")
    ev["ledger"] = await _ledger_lines(study_id)
    ev["allocation_requirements"] = await _maybe(ar_status, study_id)
    try:
        from .requirement_queries import element_code_map
        ev["element_codes"] = await element_code_map(study_id)
    except Exception:  # noqa: BLE001
        ev["element_codes"] = {}
    ev["panel_decisions"] = _panel_decisions(study_id)
    try:                                   # S (3.S2): the SE deliverables per gate
        from . import se_deliverables as sd
        want = [g for g in SE_GATES if gates is None or g in gates]
        ev["se_deliverables"] = {g: await _maybe(sd.evaluate, study_id, g) for g in want}
        blocking = getattr(sd, "blocking", None)
        ev["se_blocking"] = bool(await blocking(study_id)) if blocking else False
    except Exception:  # noqa: BLE001
        ev["se_deliverables"] = None
    try:                                   # S (3.S5): validation coverage per objective
        from ..routers.validation import coverage as validation_coverage
        ev["validation"] = await _maybe(validation_coverage, study_id)
    except Exception:  # noqa: BLE001
        ev["validation"] = None
    try:                                   # A (3.A5): reliability over the horizon and the FMEA
        from .reliability_model import evidence as reliability_evidence
        ev["reliability"] = await _maybe(reliability_evidence, study_id)
    except Exception:  # noqa: BLE001
        ev["reliability"] = None
    try:                                   # L (3.L8): the debris assessment accepted at the SRR
        from .debris_assessment import srr_evidence
        ev["debris"] = await _maybe(srr_evidence, study_id)
    except Exception:  # noqa: BLE001
        ev["debris"] = None
    try:                                   # D (3.D5): operational scenarios with requirements
        from ..routers.conops import scenario_count
        from ..routers.studies import get_study_store
        st = get_study_store().get(study_id)
        ev["conops_scenarios"] = scenario_count(st) if st is not None else None
    except Exception:  # noqa: BLE001
        ev["conops_scenarios"] = None
    try:                                   # D's probes: the SEMP content and issue (X 3.X3), the change
        from . import gate_evidence        # proposals (L 3.L4) and the thermal model (A 3.A6)
        ev["readiness"] = await gate_evidence.collect(study_id, probes=("semp", "changes", "thermal"))
    except Exception:  # noqa: BLE001
        ev["readiness"] = {}
    try:                                   # A (3.A7): the priced cost (labour, tests, reserve)
        from ..routers.schedule import list_cost_items
        ev["cost"] = await _maybe(list_cost_items, study_id)
    except Exception:  # noqa: BLE001
        ev["cost"] = None
    _EVIDENCE[study_id] = ev
    return ev


def _ev(ctx: dict) -> dict[str, Any]:
    return ctx.get("ev") or {}


def _first_num(d: Any, *keys: str) -> float | None:
    for k in keys:
        v = d.get(k) if isinstance(d, dict) else None
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


def _se_criterion(cid: str, result: dict, ctx: dict) -> None:
    """``<GATE>-SE-01``: the SE deliverables of the gate (S's ``se_deliverables.evaluate``)."""
    gate = cid.split("-", 1)[0].lower()
    ev = _ev(ctx)
    if ev.get("se_blocking"):
        result["priority"], result["advisory"] = "must_pass", False
    per = (ev.get("se_deliverables") or {}).get(gate) if isinstance(ev.get("se_deliverables"), dict) else None
    items = per.get("deliverables") if isinstance(per, dict) else per
    if items is None:
        _set(result, "not_evaluated", "The deliverables check is not available yet")
        return
    items = [i for i in items if isinstance(i, dict)]
    if not items:
        _set(result, "not_evaluated", "No deliverables listed for this gate")
        return
    ok = [i for i in items if (i.get("state") or i.get("status")) in ("ok", "pass", "done")]
    if len(ok) == len(items):
        _set(result, "pass", "All {{total}} deliverables of the gate ready", total=len(items))
    else:
        def name(i: dict) -> str:
            lb = i.get("label")
            return str((lb.get("en") if isinstance(lb, dict) else lb) or i.get("id") or "?")
        miss = [name(i) for i in items if i not in ok]
        _set(result, "fail", "{{ok}}/{{total}} deliverables of the gate ready; missing: {{names}}",
             ok=len(ok), total=len(items), names=", ".join(miss[:8]) + (" …" if len(miss) > 8 else ""))


def _coverage_criterion(result: dict, ctx: dict) -> None:
    """SRR-EC-12 / PDR-EC-08: every leaf function covered; every space subsystem has a requirement."""
    cov = _ev(ctx).get("function_coverage")
    if not cov or not cov.get("functions"):
        _set(result, "fail" if cov is not None else "not_evaluated", "No function tree yet")
        return
    leaves = cov.get("leaves") or 0
    bad = list(cov.get("leaves_without_requirement") or [])
    nosub = list(cov.get("subsystems_without_requirement") or [])
    if bad or nosub:
        _set(result, "fail",
             "{{uncovered}}/{{leaves}} leaf function(s) without a requirement: {{codes}}; {{nosubs}} space subsystem(s) without one: {{names}}",
             uncovered=len(bad), leaves=leaves, codes=", ".join(bad[:10]) + (" …" if len(bad) > 10 else "") or "-",
             nosubs=len(nosub), names=", ".join(nosub[:8]) or "-")
    else:
        _set(result, "pass", "{{leaves}} leaf function(s) covered by requirements; {{subs}} space subsystem(s) with requirements",
             leaves=leaves, subs=cov.get("subsystems") or 0)


def _allocation_criterion(result: dict, ctx: dict) -> None:
    """PDR-EC-07: mass and power lines agreed for every space subsystem; Σ allocations ×
    (1 + system margin) ≤ the limit; every line covered by a requirement."""
    ev = _ev(ctx)
    lines = ev.get("ledger")
    if not lines:
        _set(result, "fail" if lines is not None else "not_evaluated", "No allocation ledger lines yet")
        return
    elements = ctx["elements"]
    subs = [e for e in elements if e.get("element_type") == "subsystem" and (e.get("segment") or "space") == "space"
            and e.get("in_scope") is not False and e.get("subsystem_domain") != "harness"
            and str(e.get("name") or "").strip().lower() != "harness"]
    alloc = [ln for ln in lines if (ln.get("line_kind") or "allocation") == "allocation"
             and ln.get("budget_type") in LEDGER_TYPES]
    ar = ev.get("allocation_requirements") or {}
    codes = ev.get("element_codes") or {}
    by_el: dict[str, dict[str, dict]] = {}
    for ln in alloc:      # a line names its element by id, or by its v2 code only
        eid = ln.get("element_id") or codes.get(ln.get("element_code") or "") or ""
        by_el.setdefault(eid, {})[ln["budget_type"]] = ln
    missing, unagreed = [], []
    for s in subs:
        mine = by_el.get(s["id"]) or {}
        name = str(s.get("name") or s["id"])
        if any(t not in mine for t in LEDGER_TYPES):
            missing.append(name)
        elif any(mine[t].get("status") != "agreed" for t in LEDGER_TYPES):
            unagreed.append(name)
    ru = ctx.get("rollup") or {}
    sys_m = float(((ru.get("mass") or {}).get("system_margin_percent")) or 0.0)
    sys_p = float(((ru.get("power") or {}).get("system_margin_percent")) or sys_m)
    mass = sum(float(ln.get("value") or 0) for ln in alloc if ln["budget_type"] == "mass") * (1 + sys_m / 100)
    power = sum(float(ln.get("value") or 0) for ln in alloc if ln["budget_type"] == "power_avg") * (1 + sys_p / 100)

    def closure_limit(ref: str) -> float | None:
        for r in ctx["reqs"]:
            if r.get("budget_ref") == ref and r.get("threshold_op") in ("<=", "<"):
                try:
                    raw = r.get("threshold_value")
                    return float(json.loads(raw) if isinstance(raw, str) else raw)
                except (TypeError, ValueError):
                    return None
        return None
    mlim = closure_limit("mass.closure") or (ru.get("mass") or {}).get("limit_kg") or ctx.get("target_mass")
    plim = closure_limit("power.closure") or _get_param(ctx["dp"], "power.sa_power_eol_w")
    params = dict(mass=_fmt(mass, 3), mlimit=_fmt(float(mlim), 1) if mlim else "?",
                  power=_fmt(power, 3), plimit=_fmt(float(plim), 1) if plim else "?")
    uncovered = [x for x in ar.get("lines") or [] if x.get("state") == "uncovered"
                 and x.get("budget_type") in LEDGER_TYPES]
    if missing:
        _set(result, "fail", "No mass or power line for: {{names}}", names=", ".join(missing))
    elif unagreed:
        _set(result, "fail", "Lines not agreed by their owner: {{names}}; {{mass}} kg vs {{mlimit}} kg; {{power}} W vs {{plimit}} W",
             names=", ".join(unagreed), **params)
    elif uncovered:
        _set(result, "fail", "{{n}} allocation line(s) without a covering requirement: {{names}}", n=len(uncovered),
             names=", ".join(f"{x.get('element_code')} {x.get('budget_type')}" for x in uncovered[:8]))
    elif (mlim and mass > float(mlim)) or (plim and power > float(plim)):
        _set(result, "fail", "Allocations with the system margin exceed the limit: {{mass}} kg vs {{mlimit}} kg; {{power}} W vs {{plimit}} W",
             **params)
    elif not mlim or not plim:
        _set(result, "not_evaluated", "No mass target or form factor to check the mass budget against")
    else:
        _set(result, "pass", "Mass and power lines agreed for {{n}} subsystem(s); {{mass}} ≤ {{mlimit}} kg; {{power}} ≤ {{plimit}} W",
             n=len(subs), **params)


def _primary_objectives(ctx: dict) -> list[str]:
    return [str(o.get("id")) for o in ctx["mn"].get("objectives") or []
            if (o.get("priority") or "primary") == "primary" and o.get("id")]


def _validation_items(ctx: dict) -> list[dict] | None:
    v = _ev(ctx).get("validation")
    if v is None:
        return None
    items = v.get("items") if isinstance(v, dict) else v
    if isinstance(v, dict) and isinstance(v.get("objectives"), dict):
        items = [{"objective_id": k, **(x if isinstance(x, dict) else {})} for k, x in v["objectives"].items()]
    return [i for i in items or [] if isinstance(i, dict)]


def _objective_of(i: dict) -> str | None:
    return i.get("objective_id") or i.get("objective") or i.get("id")


def _coverage_of(ctx: dict) -> dict | None:
    """S's ``routers.validation.coverage`` (3.S5): ``{objectives: {id: {stakeholder_performed,
    in_orbit, ...}}, primary, uncovered_primary, in_orbit_planned, ok}``, when that is the shape."""
    v = _ev(ctx).get("validation")
    return v if isinstance(v, dict) and "uncovered_primary" in v and isinstance(v.get("objectives"), dict) else None


def _validation_criterion(result: dict, ctx: dict) -> None:
    """SRR-EC-13: every primary objective has a validation activity performed by a stakeholder."""
    cov = _coverage_of(ctx)
    if cov is not None:
        prim, miss = list(cov.get("primary") or []), list(cov.get("uncovered_primary") or [])
        if not prim:
            _set(result, "fail", "No objectives defined")
        elif miss:
            _set(result, "fail", "{{ok}}/{{total}} primary objectives have a validation activity performed by a stakeholder; without: {{ids}}",
                 ok=len(prim) - len(miss), total=len(prim), ids=", ".join(miss))
        else:
            _set(result, "pass", "All {{total}} primary objectives have a validation activity performed by a stakeholder",
                 total=len(prim))
        return
    items = _validation_items(ctx)
    if items is None:
        _set(result, "not_evaluated", "The validation plan is not available yet")
        return
    prim = _primary_objectives(ctx)
    if not prim:
        _set(result, "fail", "No objectives defined")
        return
    ok = set()
    for i in items:
        acts = [a for a in i.get("activities") or [] if isinstance(a, dict)]
        if i.get("stakeholder_performer") or i.get("has_stakeholder_performer") or i.get("covered") \
                or any(a.get("performer_kind") == "stakeholder" or a.get("stakeholder_performer")
                       or a.get("performer_stakeholder_id") for a in acts):
            o = _objective_of(i)
            if o:
                ok.add(str(o))
    miss = [o for o in prim if o not in ok]
    if miss:
        _set(result, "fail", "{{ok}}/{{total}} primary objectives have a validation activity performed by a stakeholder; without: {{ids}}",
             ok=len(prim) - len(miss), total=len(prim), ids=", ".join(miss))
    else:
        _set(result, "pass", "All {{total}} primary objectives have a validation activity performed by a stakeholder",
             total=len(prim))


def _iov_criterion(result: dict, ctx: dict) -> None:
    """FRR-EC-01: every primary objective has an in-orbit validation activity planned."""
    cov = _coverage_of(ctx)
    if cov is not None:
        prim = list(cov.get("primary") or [])
        objs = cov["objectives"]
        miss = [o for o in prim if not (objs.get(o) or {}).get("in_orbit")]
        if not cov.get("in_orbit_planned"):
            _set(result, "fail", "No in-orbit validation activity planned")
        elif miss:
            _set(result, "fail", "{{ok}}/{{total}} primary objectives have an in-orbit validation activity planned; without: {{ids}}",
                 ok=len(prim) - len(miss), total=len(prim), ids=", ".join(miss))
        else:
            _set(result, "pass", "All {{total}} primary objectives have an in-orbit validation activity planned", total=len(prim))
        return
    items = _validation_items(ctx)
    if items is None:
        _set(result, "not_evaluated", "The validation plan is not available yet")
        return
    prim = _primary_objectives(ctx)
    have = set()
    for i in items:
        for a in [a for a in i.get("activities") or [] if isinstance(a, dict)]:
            stage = str(a.get("stage") or a.get("gate") or "").upper()
            if stage in ("IOV", "COMMISSIONING", "E1", "ORR", "CRR") or a.get("in_orbit"):
                o = _objective_of(i)
                if o:
                    have.add(str(o))
    miss = [o for o in prim if o not in have]
    if not have:
        _set(result, "fail", "No in-orbit validation activity planned")
    elif miss:
        _set(result, "fail", "{{ok}}/{{total}} primary objectives have an in-orbit validation activity planned; without: {{ids}}",
             ok=len(prim) - len(miss), total=len(prim), ids=", ".join(miss))
    else:
        _set(result, "pass", "All {{total}} primary objectives have an in-orbit validation activity planned", total=len(prim))


def _decisions_criterion(result: dict, ctx: dict) -> None:
    """SRR-EC-04: every trade due by the SRR (gate MDR, PRR or SRR) is decided in the Decide panel.
    Only the study's own records are read; personal logbooks are never consulted (PI ruling)."""
    pd = _ev(ctx).get("panel_decisions")
    if pd is None:
        _positions_criterion(result, ctx)          # no study trades readable: the position-guidance check
        return
    if not pd["due"]:
        _set(result, "fail", "No trade due by the SRR recorded in the Decide panel")
        return
    open_ = [t for t in pd["due"] if t not in pd["decided"]]
    if open_:
        _set(result, "fail", "{{recorded}}/{{total}} trades due by the SRR decided in the Decide panel; open: {{open}}",
             recorded=len(pd["due"]) - len(open_), total=len(pd["due"]), open=", ".join(open_[:8]) + (" …" if len(open_) > 8 else ""))
    else:
        _set(result, "pass", "All {{total}} trades due by the SRR decided in the Decide panel", total=len(pd["due"]))


def _icd_criterion(result: dict, ctx: dict) -> bool:
    """PDR-EC-02 (3.R5): when the team has ICDs under issue control, each is at Issue A or later
    and signed by both owning seats (the unsigned ones are listed by seat). Returns False when no
    ICD is under issue control (the per-link agreement check then applies)."""
    st = _ev(ctx).get("icds")
    inv = [i for i in (st or {}).get("items") or [] if i.get("controlled")
           and i.get("required_at") in (None, "", "pdr")]
    if not inv:
        return False
    agreed = [i for i in inv if i.get("agreed")]
    if len(agreed) == len(inv):
        _set(result, "pass", "All {{total}} ICDs under issue control at Issue A and signed by both seats", total=len(inv))
    else:
        by_seat: dict[str, list[str]] = {}
        for i in inv:
            if i.get("agreed"):
                continue
            for s in (i.get("unsigned") or []) or [None]:
                by_seat.setdefault(s or "?", []).append(f"{i['icd_ref']} ({(i.get('issue') or 'draft')})")
        unsigned = "; ".join(f"{s}: {', '.join(v)}" for s, v in sorted(by_seat.items()))
        _set(result, "fail", "{{agreed}}/{{total}} ICDs under issue control at Issue A and signed by both seats; not agreed: {{unsigned}}",
             agreed=len(agreed), total=len(inv), unsigned=unsigned)
    return True


def _reliability_horizon(ctx: dict) -> str | None:
    rel = _ev(ctx).get("reliability") or {}
    m = _first_num(rel, "horizon_months", "mission_success_months")
    y = _first_num(rel, "horizon_years")
    if m is None:
        m = _get_param(ctx["dp"], "reliability.horizon_months")
    if m is not None:
        return f"{_fmt(m)} months"
    if y is None:
        y = _get_param(ctx["dp"], "reliability.horizon_years")
    return f"{_fmt(y, 1)} years" if y is not None else None


def _icd_pdr(result: dict, ctx: dict) -> bool:
    """PDR-EC-02 with ICDs under issue control: the expected subsystem links are present and
    reviewed, then the ICD inventory decides (instead of the per-link agreement)."""
    elements = ctx["elements"]
    subs = [e for e in elements if e.get("element_type") == "subsystem" and e.get("in_scope") is not False]
    if subs:
        from .interface_proposer import Context, RuleConfigError, load_rules
        from .readiness import interface_coverage
        try:
            cov = interface_coverage(Context(elements, load_rules()), ctx["interfaces"], [e["id"] for e in subs])
        except RuleConfigError:
            return False
        sub_ids = {e["id"] for e in subs}
        suggested = sum(1 for i in ctx["interfaces"] if i.get("status") == "suggested"
                        and (i.get("from_element_id") in sub_ids or i.get("to_element_id") in sub_ids))
        if cov["missing"] or suggested:
            _set(result, "fail",
                 "{{met}}/{{required}} expected subsystem links present; {{suggested}} suggested link(s) not reviewed",
                 met=cov["met"], required=cov["required"], suggested=suggested)
            return True
    return _icd_criterion(result, ctx)


def _cost_total(ctx: dict) -> float | None:
    cost = _ev(ctx).get("cost")
    if not isinstance(cost, dict):
        return None
    meur = _first_num(cost, "total_meur")
    if meur is None:
        keur = _first_num(cost, "total_keur")
        meur = keur / 1000.0 if keur is not None else None
    return meur


def _semp_criterion(result: dict, ctx: dict) -> None:
    """SRR-EC-09 (PI addendum; X 3.X3): the SEMP generated from the study and issued by the team.
    Content ready but not issued stays ``manual`` (the instructor may sign it off instead)."""
    sm = (_ev(ctx).get("readiness") or {}).get("semp")
    if not isinstance(sm, dict):
        _set(result, "manual", "Requires manual assessment")
        return
    if sm.get("issue"):
        _set(result, "pass", "SEMP issue {{issue}} recorded", issue=sm["issue"])
    elif sm.get("ready"):
        _set(result, "manual", "SEMP content ready ({{parts}}/{{of}} parts): review it and record its issue",
             parts=sm.get("parts", 0), of=sm.get("of", 0))
    else:
        _set(result, "fail", "The SEMP generator has no content yet ({{parts}}/{{of}} parts)",
             parts=sm.get("parts", 0), of=sm.get("of", 0))


def _debris_criterion(result: dict, ctx: dict) -> None:
    """SRR-EC-10 (PI addendum; L 3.L8): the debris assessment run in the tool, accepted at or
    before the SRR, compliant (or with a recorded deviation) and still about the current design."""
    d = _ev(ctx).get("debris")
    if not isinstance(d, dict) or d.get("version") is None:
        _set(result, "fail", "No debris assessment has been run")
        return
    v = d.get("version")
    if not d.get("accepted"):
        _set(result, "fail", "Debris assessment v{{version}} not accepted yet", version=v)
    elif d.get("stale"):
        _set(result, "fail", "Debris assessment v{{version}} accepted, but the design changed since the run: run it again",
             version=v)
    elif d.get("status") != "pass":
        _set(result, "fail", "Debris assessment v{{version}} accepted, not compliant and no deviation recorded", version=v)
    else:
        _set(result, "pass", "Debris assessment v{{version}} accepted at {{gate}}",
             version=v, gate=str(d.get("gate") or "").upper())


def _reliability_criterion(result: dict, ctx: dict) -> None:
    """PDR-EC-05 (PI addendum; A 3.A5): the reliability block diagram over the mission-success
    horizon against the target, and the FMEA covering every space subsystem with its critical
    rows linked to FDIR, a risk or a mitigation."""
    r = _ev(ctx)["reliability"]
    if r.get("ok"):
        rel, tgt = r.get("reliability"), r.get("target")
        _set(result, "pass",
             "Reliability {{rel}} over {{horizon}} vs target {{target}}; FMEA {{rows}} line(s), {{critical}} critical, all linked",
             rel=_fmt(float(rel), 3) if isinstance(rel, (int, float)) else "?", horizon=_reliability_horizon(ctx) or "?",
             target=_fmt(float(tgt), 2) if isinstance(tgt, (int, float)) else "?",
             rows=r.get("fmea_rows", 0), critical=r.get("critical_rows", 0))
    else:
        _set(result, "fail", "Reliability analysis not acceptable: {{reasons}}",
             reasons="; ".join(x for x in r.get("reasons") or [] if x) or "-")
