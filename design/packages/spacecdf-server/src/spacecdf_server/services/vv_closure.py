"""V&V closure (SCDF-175, design SCDF-170 §2.3).

``run_vv(ctx)`` walks the study's persisted requirements (``ctx.requirements``,
the write-through cache in ``routers/requirements``) and its typed relations
(``ctx.relations``) and builds / refreshes one ``verification_items`` row per
requirement through ``services/vv_planner.generate_vv_plan``:

* **method** — ``requirement.verification_method``; else inferred: a
  numeric threshold means the requirement can be closed by analysis (``A``);
  mission-level narrative requirements go to review (``R``); anything else
  follows the planner's domain rules (``METHOD_RULES``).
* **level** — ``requirement.level`` → segment / system / subsystem / unit
  (``LEVEL_MAP``); a requirement allocated to a component is verified at unit
  level whatever its own level says.
* **phase** — ``requirement.verification_phase``; else ``A``/``R`` at PDR,
  ``T``/``I``/``D`` by level (``PHASE_BY_LEVEL``).
* **facility** — ``vv_planner._assign_facility`` with the allocated element's
  ``subsystem_domain`` (``satisfies`` / ``allocates`` relations, else
  ``requirement.element_id``, else the threshold path's domain prefix).
* **acceptance_criterion** — auto-text from ``threshold_param_path/op/value``
  + method + phase, e.g. ``"Battery DoD <= 30 % (analysis: power budget), PDR"``.

Human edits win: rows with ``edited_by_user=True`` only get their *empty*
fields filled (``verification_repo.upsert_generated``).

**Auto-closure by analysis** — ``install_auto_closure()`` registers
``auto_close_from_publish`` with ``analysis_results.on_publish``: after any
analysis publishes and the compliance tracker has been rechecked, items whose
method is ``A`` follow their requirement's latest ``ComplianceResult``
(PASS → ``passed``, FAIL → ``failed``) with ``evidence_ref='analysis:<run_id>'``.
Items that are ``waived`` or user-edited are never touched. ``run_vv`` itself
evaluates every requirement against the context it ran on and applies the
same rule, so the first run already closes what the design already proves.

Outputs (mission root): ``vv_items_total``, ``vv_items_passed``,
``vv_items_failed``, ``vv_items_planned``, ``vv_closure_pct``
(passed + waived over total), ``vv_by_analysis_pct`` (share of items verified
by analysis). Conflicts: ``VV_REQ_UNVERIFIABLE`` (warning: no method and no
threshold), ``VV_FAILED`` (major, one per failed item, requirement code in
the title).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from ..db import verification_repo
from .analysis_context import AnalysisContext
from .analysis_results import ANALYSIS_INPUT_KEYS, Conflict, ParamWrite, PublishResult, get_tracker, on_publish
from .compliance_tracker import LINK_RELATION_KINDS
from .vv_planner import METHOD_RULES, _assign_facility, generate_vv_plan

logger = logging.getLogger(__name__)

ANALYSIS = "vv"
ANALYSIS_INPUT_KEYS.setdefault(ANALYSIS, ("requirements", "elements"))

OUTPUT_PARAMETERS: tuple[str, ...] = (
    "vv_items_total", "vv_items_passed", "vv_items_failed", "vv_items_planned",
    "vv_closure_pct", "vv_by_analysis_pct",
)
CONFLICT_CODES = ("VV_REQ_UNVERIFIABLE", "VV_FAILED")

METHOD_NAMES = {"A": "analysis", "T": "test", "I": "inspection", "R": "review of design", "D": "demonstration"}
#: requirement.level -> verification level
LEVEL_MAP = {"mission": "segment", "segment": "segment", "system": "system", "subsystem": "subsystem",
             "unit": "unit", "component": "unit", "equipment": "unit"}
PHASE_BY_LEVEL = {"unit": "CDR", "subsystem": "CDR", "system": "QR", "segment": "AR"}
LEVEL_ORDER = ("unit", "subsystem", "system", "segment")
#: element subsystem_domain -> vv_planner domain key
DOMAIN_TO_PLANNER = {"power": "power", "ttc": "link", "comms": "link", "aocs": "pointing", "adcs": "pointing",
                     "thermal": "thermal", "structure": "structure", "propulsion": "propulsion",
                     "obc": "systems", "cdh": "systems", "payload": "payload", "ground": "link"}
#: threshold path prefix -> (planner domain, analysis label)
PATH_DOMAINS = {
    "power": ("power", "power budget"), "mass": ("mass", "mass budget"), "link": ("link", "link budget"),
    "thermal": ("thermal", "thermal analysis"), "aocs": ("pointing", "pointing analysis"),
    "pointing": ("pointing", "pointing analysis"), "propulsion": ("propulsion", "propulsion budget"),
    "delta_v": ("propulsion", "delta-v budget"), "data": ("systems", "data budget"),
    "cost": ("cost", "cost model"), "orbit": ("systems", "orbit analysis"), "structure": ("structure", "structural analysis"),
    "systems": ("systems", "system budget"), "gs": ("link", "ground segment closure"),
    "sim": ("power", "mission simulation"),
}
OP_TEXT = {"<=": "≤", ">=": "≥", "==": "=", "<": "<", ">": ">", "in_range": "within", "exists": "defined"}
_UNIT_SUFFIX = {
    "kg": "kg", "g": "g", "w": "W", "wh": "Wh", "db": "dB", "dbi": "dBi", "percent": "%", "pct": "%", "km": "km",
    "m": "m", "m2": "m²", "deg": "°", "arcsec": "arcsec", "s": "s", "min": "min", "h": "h", "keur": "kEUR",
    "bps": "bit/s", "mbps": "Mbit/s", "gb": "GB", "mb": "MB", "c": "°C", "k": "K", "hz": "Hz", "ghz": "GHz",
    "mhz": "MHz", "cm3": "cm³", "ms": "m/s", "years": "years", "days": "days",
}
_ACRONYMS = {"dod": "DoD", "soc": "SoC", "eol": "EOL", "bol": "BOL", "rf": "RF", "eps": "EPS", "aocs": "AOCS",
             "adcs": "ADCS", "sa": "solar array", "ttc": "TT&C", "obc": "OBC", "trl": "TRL", "emc": "EMC",
             "gs": "ground station", "sim": "simulated", "vv": "V&V", "eirp": "EIRP", "snr": "SNR", "ber": "BER",
             "cog": "CoG", "com": "CoM", "moi": "MoI", "gsd": "GSD", "id": "ID"}


@dataclass
class AnalysisOutput:
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    series: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ── helpers ─────────────────────────────────────────────────────────────

def _threshold(req: dict) -> tuple[str | None, str | None, Any]:
    path, op, raw = req.get("threshold_param_path"), req.get("threshold_op"), req.get("threshold_value")
    if not path or not op or raw is None:
        return None, None, None
    value: Any = raw
    if isinstance(raw, str):
        try:
            value = json.loads(raw)
        except (ValueError, TypeError):
            value = raw
    return path, op, value


def has_threshold(req: dict) -> bool:
    path, op, value = _threshold(req)
    return path is not None and op is not None and value is not None


def _fmt_value(v: Any) -> str:
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float)):
        return f"{v:g}"
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return f"[{_fmt_value(v[0])}, {_fmt_value(v[1])}]"
    return str(v)


def humanise_path(path: str, element_names: dict[str, str] | None = None) -> tuple[str, str]:
    """``power.battery_dod_percent`` -> ("Battery DoD", "%"); ``el:EPS.mass_kg`` -> ("EPS mass", "kg").

    ``element_names`` (id -> name) turns an ``el:<id>.x`` reference into the element's name
    (SCDF-170 verification fix: the acceptance text showed the raw 32-hex id, capitalised)."""
    if path.startswith("el:"):
        ref, _, name = path[3:].rpartition(".")
        prefix = (element_names or {}).get(ref, ref)
    else:
        prefix, _, name = path.rpartition(".")
        prefix = ""
    tokens = [t for t in re.split(r"[_\s]+", name) if t]
    unit = ""
    if tokens and tokens[-1].lower() in _UNIT_SUFFIX and len(tokens) > 1:
        unit = _UNIT_SUFFIX[tokens[-1].lower()]
        tokens = tokens[:-1]
    words = [_ACRONYMS.get(t.lower(), t.lower()) for t in tokens]
    label = " ".join(words) if words else name
    if prefix:
        label = f"{prefix} {label}"
    label = label[:1].upper() + label[1:]
    return label, unit


def _path_domain(path: str | None) -> tuple[str | None, str | None]:
    """(planner domain, analysis label) from a threshold path prefix."""
    if not path:
        return None, None
    if path.startswith("el:"):
        # closure outputs on the mission root carry a prefix (SCDF-173..177)
        name = path.rpartition(".")[2].lower()
        for pfx, label in (("sim_", "mission simulation"), ("gs_", "ground segment"), ("aocs_", "physics (AOCS)"),
                           ("mp_", "physics (mass properties)"), ("thermal_", "physics (thermal)"),
                           ("fmeca_", "FMECA"), ("vv_", "V&V")):
            if name.startswith(pfx):
                return None, label
        return None, "design loop"
    prefix = path.split(".", 1)[0].lower()
    d = PATH_DOMAINS.get(prefix)
    if d:
        return d
    for key, val in PATH_DOMAINS.items():
        if prefix.startswith(key):
            return val
    return None, f"{prefix} analysis"


def acceptance_text(req: dict, method: str, phase: str, analysis_label: str | None = None,
                    element_names: dict[str, str] | None = None) -> str:
    """``"Battery DoD <= 30 % (analysis: power budget), PDR"`` — or a narrative fallback."""
    path, op, value = _threshold(req)
    mname = METHOD_NAMES.get(method, "analysis")
    if path is None:
        text = (req.get("text") or "").strip().rstrip(".")
        core = text[:120] if text else f"Requirement {req.get('code') or req.get('id')}"
        return f"{core} ({mname}), {phase}"
    label, unit = humanise_path(path, element_names)
    unit_txt = f" {unit}" if unit else ""
    if op == "in_range" and isinstance(value, (list, tuple)) and len(value) == 2:
        cond = f"{label} within {_fmt_value(value[0])}–{_fmt_value(value[1])}{unit_txt}"
    elif op == "exists":
        cond = f"{label} defined"
    else:
        cond = f"{label} {OP_TEXT.get(op, op)} {_fmt_value(value)}{unit_txt}"
    how = mname if not analysis_label else f"{mname}: {analysis_label}"
    return f"{cond} ({how}), {phase}"


def _linked_elements(req: dict, relations: list[dict]) -> list[str]:
    """Element ids bound to the requirement by satisfies/allocates relations, plus its own element_id."""
    rid = req.get("id")
    out: list[str] = []
    for rel in relations:
        if rel.get("kind") not in LINK_RELATION_KINDS:
            continue
        if rel.get("source_kind") == "requirement" and rel.get("source_id") == rid:
            kind, other = rel.get("target_kind"), rel.get("target_id")
        elif rel.get("target_kind") == "requirement" and rel.get("target_id") == rid:
            kind, other = rel.get("source_kind"), rel.get("source_id")
        else:
            continue
        if kind == "element" and other and other not in out:
            out.append(other)
    if req.get("element_id") and req["element_id"] not in out:
        out.append(req["element_id"])
    return out


def _linked_functions(req: dict, relations: list[dict]) -> list[str]:
    rid = req.get("id")
    out: list[str] = []
    for rel in relations:
        if rel.get("kind") not in LINK_RELATION_KINDS:
            continue
        if rel.get("source_kind") == "requirement" and rel.get("source_id") == rid:
            kind, other = rel.get("target_kind"), rel.get("target_id")
        elif rel.get("target_kind") == "requirement" and rel.get("target_id") == rid:
            kind, other = rel.get("source_kind"), rel.get("source_id")
        else:
            continue
        if kind == "function" and other and other not in out:
            out.append(other)
    return out


def _element_domain(ctx: AnalysisContext, element_ids: list[str]) -> tuple[str | None, str | None]:
    """(subsystem_domain, element_type) of the first linked element that has a domain (walking up parents)."""
    by_id = ctx.elements_by_id
    first_type: str | None = None
    for eid in element_ids:
        el = by_id.get(eid)
        if el is None:
            continue
        if first_type is None:
            first_type = el.get("element_type")
        hops = 0
        while el is not None and hops < 8:
            if el.get("subsystem_domain"):
                return el["subsystem_domain"], first_type
            el = by_id.get(el.get("parent_id") or "")
            hops += 1
    return None, first_type


def plan_item(req: dict, ctx: AnalysisContext) -> dict:
    """The generated (study, requirement) item — pure function of requirement + context."""
    relations = ctx.relations or []
    linked = _linked_elements(req, relations)
    sub_domain, el_type = _element_domain(ctx, linked)
    path, op, value = _threshold(req)
    path_domain, analysis_label = _path_domain(path)
    planner_domain = DOMAIN_TO_PLANNER.get(sub_domain or "", sub_domain) or path_domain or "systems"

    # method
    method = (req.get("verification_method") or "").strip().upper()[:1]
    inferred = False
    if method not in METHOD_NAMES:
        inferred = True
        if has_threshold(req):
            method = "A"
        elif (req.get("level") or "") == "mission":
            method = "R"
        else:
            method = METHOD_RULES.get(planner_domain, "A")

    # level
    level = LEVEL_MAP.get((req.get("level") or "system").lower(), "system")
    if el_type == "component":
        level = "unit"

    # phase
    phase = (req.get("verification_phase") or "").strip().upper()
    if phase not in PHASE_BY_LEVEL.values():
        phase = "PDR" if method in ("A", "R") else PHASE_BY_LEVEL.get(level, "CDR")

    # facility (planner: only for tests) + planner entry for cross-check
    planner_entry = generate_vv_plan([{**req, "text": req.get("text") or "", "domain": planner_domain, "verification_method": method}]).verification_matrix[0]
    facility = _assign_facility(method, planner_domain) or planner_entry.facility
    if method == "A":
        facility = "analysis desk"
    elif method == "R":
        facility = "design review"
    elif method in ("I", "D") and not facility:
        facility = "clean_room"

    return {
        "study_id": ctx.study_id, "requirement_id": req["id"],
        "method": method, "level": level, "phase": phase, "facility": facility,
        "acceptance_criterion": acceptance_text(req, method, phase, analysis_label if method == "A" else None,
                                                {e["id"]: e.get("name") or e["id"] for e in ctx.elements}),
        "procedure_ref": None,
        "_inferred_method": inferred, "_linked_elements": linked,
        "_linked_functions": _linked_functions(req, relations), "_domain": planner_domain,
    }


# ── auto-closure ────────────────────────────────────────────────────────

def closure_status(compliance_status: str | None) -> str | None:
    return {"pass": "passed", "fail": "failed"}.get((compliance_status or "").lower())


async def apply_auto_closure(study_id: str, results: dict[str, Any], evidence_ref: str | None,
                             items: list[dict] | None = None) -> list[dict]:
    """Set ``passed`` / ``failed`` on method-``A`` items from ``results``
    (``{req_id: ComplianceResult | {status: ...}}``). Skips waived and
    user-edited items. Returns the updated item dicts."""
    items = items if items is not None else await verification_repo.list_by_study(study_id)
    by_req = {it["requirement_id"]: it for it in items}
    changed: list[dict] = []
    for rid, res in results.items():
        status = res.get("status") if isinstance(res, dict) else getattr(res, "status", None)
        target = closure_status(status)
        item = by_req.get(rid)
        if target is None or item is None:
            continue
        if item.get("method") != "A" or item.get("status") == "waived" or item.get("edited_by_user"):
            continue
        ref = evidence_ref or item.get("evidence_ref")
        if item.get("status") == target and item.get("evidence_ref") == ref:
            continue
        try:
            updated = await verification_repo.set_status(item["id"], target, ref)
        except ValueError:
            continue
        changed.append(updated)
    if changed:
        try:
            from ..routers._arcadia_events import broadcast_mutation
            for it in changed:
                await broadcast_mutation(study_id, "verification_item_updated", "verification_item", it["id"],
                                         {"requirement_id": it["requirement_id"], "status": it["status"],
                                          "evidence_ref": it["evidence_ref"], "auto": True})
        except Exception:  # pragma: no cover - defensive
            logger.debug("verification_item_updated broadcast failed", exc_info=True)
    return changed


async def auto_close_from_publish(study_id: str, analysis: str, result: PublishResult) -> None:
    """``analysis_results.on_publish`` hook — closes A-items from the rechecked compliance."""
    if analysis == ANALYSIS or not result.compliance_results:
        return
    evidence = f"analysis:{result.run_id}" if result.run_id else f"analysis:{analysis}"
    await apply_auto_closure(study_id, result.compliance_results, evidence)


_installed = False


def install_auto_closure() -> None:
    """Register the publish hook once (called on router import and by tests)."""
    global _installed
    on_publish(auto_close_from_publish)
    _installed = True


# ── run ─────────────────────────────────────────────────────────────────

def _rollup(items: list[dict]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {lvl: {"total": 0, "planned": 0, "in_progress": 0, "passed": 0, "failed": 0, "waived": 0}
                                      for lvl in LEVEL_ORDER}
    for it in items:
        lvl = it.get("level") if it.get("level") in out else "system"
        out[lvl]["total"] += 1
        st = it.get("status") or "planned"
        out[lvl][st if st in out[lvl] else "planned"] += 1
    return out


async def run_vv(ctx: AnalysisContext, *, run_id: str | None = None) -> AnalysisOutput:
    """Build / refresh the verification items of ``ctx.study_id`` and score closure."""
    out = AnalysisOutput()
    reqs = [r for r in (ctx.requirements or []) if r.get("status") != "retired"]
    by_req_id = {r["id"]: r for r in reqs}
    generated: dict[str, dict] = {}
    items: list[dict] = []

    for req in reqs:
        plan = plan_item(req, ctx)
        generated[req["id"]] = plan
        row = await verification_repo.upsert_generated({k: v for k, v in plan.items() if not k.startswith("_")})
        items.append(row)

    # stale items of retired / deleted requirements are dropped
    for it in await verification_repo.list_by_study(ctx.study_id):
        if it["requirement_id"] not in by_req_id:
            await verification_repo.soft_delete_item(it["id"])

    # evaluate every requirement against this context and close what analysis proves
    tracker = get_tracker(ctx.study_id)
    tracker.set_requirements(reqs)
    tracker.set_relations(ctx.relations or [])
    await tracker.recheck(ctx, None)
    results = tracker.get_all_results()
    evidence = f"analysis:{run_id}" if run_id else "analysis:vv"
    changed = await apply_auto_closure(ctx.study_id, {rid: r for rid, r in results.items() if rid in by_req_id},
                                       evidence, items)
    if changed:
        by_id = {c["id"]: c for c in changed}
        items = [by_id.get(it["id"], it) for it in items]

    # conflicts
    for req in reqs:
        if not req.get("verification_method") and not has_threshold(req):
            code = req.get("code") or req["id"]
            out.conflicts.append(Conflict(
                "warning", "VV_REQ_UNVERIFIABLE", f"{code}: no verification method and no threshold",
                f"Requirement {code} has neither a verification method nor a measurable threshold; the plan "
                f"assumed {METHOD_NAMES[generated[req['id']]['method']]}.",
                element_ids=generated[req["id"]]["_linked_elements"], requirement_ids=[req["id"]],
                suggested_fix="Set verification_method (A/T/I/R/D) on the requirement or give it a threshold "
                              "(threshold_param_path / op / value) so it can be closed by analysis."))
    for it in items:
        if it.get("status") == "failed":
            req = by_req_id.get(it["requirement_id"], {})
            code = req.get("code") or it["requirement_id"]
            res = results.get(it["requirement_id"])
            detail = ""
            if res is not None and res.achieved_value is not None:
                detail = (f"Achieved {res.achieved_value:g} against threshold {res.threshold_value:g} "
                          f"({req.get('threshold_op')}); margin {res.margin_pct if res.margin_pct is not None else '?'} %.")
            out.conflicts.append(Conflict(
                "major", "VV_FAILED", f"{code} failed verification",
                detail or f"Verification item {it['id']} is in status failed (evidence {it.get('evidence_ref') or '-'}).",
                element_ids=generated.get(it["requirement_id"], {}).get("_linked_elements", []),
                requirement_ids=[it["requirement_id"]],
                suggested_fix="Change the design so the analysis meets the threshold, or waive the item with a rationale."))

    # parameters
    total = len(items)
    passed = sum(1 for it in items if it.get("status") == "passed")
    failed = sum(1 for it in items if it.get("status") == "failed")
    planned = sum(1 for it in items if (it.get("status") or "planned") in ("planned", "in_progress"))
    waived = sum(1 for it in items if it.get("status") == "waived")
    by_analysis = sum(1 for it in items if it.get("method") == "A")
    closure_pct = (100.0 * (passed + waived) / total) if total else 0.0
    by_analysis_pct = (100.0 * by_analysis / total) if total else 0.0
    values = {
        "vv_items_total": float(total), "vv_items_passed": float(passed), "vv_items_failed": float(failed),
        "vv_items_planned": float(planned), "vv_closure_pct": round(closure_pct, 1),
        "vv_by_analysis_pct": round(by_analysis_pct, 1),
    }
    descr = {
        "vv_items_total": "Verification items (one per requirement)", "vv_items_passed": "Items passed",
        "vv_items_failed": "Items failed", "vv_items_planned": "Items still planned / in progress",
        "vv_closure_pct": "Closed items (passed + waived) over total", "vv_by_analysis_pct": "Items verified by analysis",
    }
    for name in OUTPUT_PARAMETERS:
        out.parameters.append(ParamWrite(name, values[name], unit="%" if name.endswith("_pct") else "",
                                         quantity_kind="ratio" if name.endswith("_pct") else "count",
                                         description=descr[name]))

    if not reqs:
        out.warnings.append("Study has no requirements — nothing to verify.")
    inferred = sum(1 for g in generated.values() if g["_inferred_method"])
    if inferred:
        out.warnings.append(f"{inferred} verification method(s) inferred from threshold / level / domain.")

    out.summary = {
        **values, "items_waived": waived, "items_auto_closed": len(changed), "run_id": run_id,
        "by_level": _rollup(items),
        "by_method": {m: sum(1 for it in items if it.get("method") == m) for m in METHOD_NAMES},
        "conflicts": len(out.conflicts),
        "items": [{**it, "requirement_code": by_req_id.get(it["requirement_id"], {}).get("code"),
                   "linked_elements": generated.get(it["requirement_id"], {}).get("_linked_elements", []),
                   "linked_functions": generated.get(it["requirement_id"], {}).get("_linked_functions", [])}
                  for it in items],
    }
    return out
