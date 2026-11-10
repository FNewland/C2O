"""V&V closure routes (SCDF-175, design SCDF-170 §2.3).

    POST  /api/studies/{study_id}/analyses/vv/run?option_id=
          start_run -> build_context -> run_vv -> ResultsSink.publish -> finish_run
          -> refresh_inputs_hash; returns {run_id, summary, items, parameters, conflicts, warnings, stale: false}
    GET   /api/studies/{study_id}/analyses/vv?option_id=
          last run (+ ``stale``) with its unresolved conflicts and the current items
          (``analyses_common`` serves the plain GET first when mounted in the app —
          the UI reads items from /verification-items)
    GET   /api/studies/{study_id}/verification-items          items (+ requirement code / text / linked entities)
    PATCH /api/verification-items/{item_id}                    user edit (stamps edited_by_user)
    POST  /api/verification-items/{item_id}/evidence           {evidence_ref, status}
    GET   /api/studies/{study_id}/export/rtm.csv               requirement traceability matrix
    GET   /api/studies/{study_id}/export/vcd.docx              Verification Control Document
    GET   /api/studies/{study_id}/export/vv.xlsx               V&V matrix workbook (W1.09i: was CSV under an XLSX label)
    GET   /api/studies/{study_id}/export/bom.xlsx              bill of materials workbook (W1.09i)

Broadcasts ``verification_item_updated`` on every item write and
``analysis_completed`` (via ``ResultsSink.publish`` / on failure from here).
Importing this module installs the analysis auto-closure hook
(``vv_closure.install_auto_closure``).
"""
from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..db import analysis_repo, verification_repo
from ..services import analysis_results
from ..services.analysis_context import build_context, context_hash
from ..services.analysis_results import ResultsSink, finish_run, input_keys_for, refresh_inputs_hash, start_run
from ..services.vv_closure import (
    ANALYSIS, LEVEL_ORDER, METHOD_NAMES, _linked_elements, _linked_functions, install_auto_closure, run_vv,
)
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)
router = APIRouter()

install_auto_closure()

EDITABLE_FIELDS = ("method", "level", "phase", "facility", "procedure_ref", "acceptance_criterion",
                   "status", "evidence_ref", "notes")
RTM_COLUMNS = ("requirement_code", "requirement_text", "requirement_level", "method", "verification_level",
               "phase", "facility", "acceptance_criterion", "status", "evidence_ref", "linked_elements",
               "linked_functions")


# ── helpers ─────────────────────────────────────────────────────────────

async def _requirements(study_id: str) -> dict[str, dict]:
    from .requirements import _requirements as store, ensure_requirements_loaded
    await ensure_requirements_loaded()
    return {r["id"]: r for r in store.values() if r.get("study_id") == study_id and r.get("status") != "retired"}


def _study_name(study_id: str) -> str:
    try:
        from .studies import get_study_store
        s = get_study_store().get(study_id)
        return getattr(s, "name", None) or study_id
    except Exception:
        return study_id


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "").strip("_")
    return s or "study"


def _download(data: bytes, filename: str, media_type: str) -> StreamingResponse:
    return StreamingResponse(io.BytesIO(data), media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(data)),
    })


async def _enriched_items(study_id: str) -> list[dict]:
    """Items joined with their requirement (code, text, level) and linked entities."""
    reqs = await _requirements(study_id)
    try:
        from ..db.relation_repo import list_relations_by_study
        relations = await list_relations_by_study(study_id)
    except Exception:
        relations = []
    from .elements import _elements
    names = {e["id"]: e.get("name") for e in _elements.values()}
    out: list[dict] = []
    for it in await verification_repo.list_by_study(study_id):
        req = reqs.get(it["requirement_id"])
        if req is None:
            continue
        els = _linked_elements(req, relations)
        out.append({
            **it,
            "requirement_code": req.get("code") or req["id"], "requirement_text": req.get("text") or "",
            "requirement_level": req.get("level"), "threshold_param_path": req.get("threshold_param_path"),
            "threshold_op": req.get("threshold_op"), "threshold_value": req.get("threshold_value"),
            # wave 3 (3.X2): the v2 verification fields of the requirement (model, event, acceptance)
            "verification_model": req.get("verification_model") or "", "verification_event": req.get("verification_event") or "",
            "requirement_acceptance": req.get("acceptance") or "",
            "linked_elements": els, "linked_element_names": [names.get(e) or e for e in els],
            "linked_functions": _linked_functions(req, relations),
            "auto_closed": bool((it.get("evidence_ref") or "").startswith("analysis:")) and not it.get("edited_by_user")
                           and it.get("status") in ("passed", "failed"),
        })
    return out


def _rollup(items: list[dict]) -> dict[str, dict[str, int]]:
    out = {lvl: {"total": 0, "planned": 0, "in_progress": 0, "passed": 0, "failed": 0, "waived": 0} for lvl in LEVEL_ORDER}
    for it in items:
        lvl = it.get("level") if it.get("level") in out else "system"
        out[lvl]["total"] += 1
        st = it.get("status") or "planned"
        out[lvl][st if st in out[lvl] else "planned"] += 1
    return out


async def _broadcast_item(item: dict, auto: bool = False) -> None:
    await broadcast_mutation(item["study_id"], "verification_item_updated", "verification_item", item["id"],
                             {"requirement_id": item["requirement_id"], "status": item["status"],
                              "evidence_ref": item.get("evidence_ref"), "auto": auto})


# ── run / get ───────────────────────────────────────────────────────────

@router.post("/studies/{study_id}/analyses/vv/run")
async def run_vv_analysis(study_id: str, option_id: str | None = Query(None)) -> dict:
    ctx = await build_context(study_id, option_id=option_id)
    run_id = await start_run(study_id, ANALYSIS, context_hash(ctx, input_keys_for(ANALYSIS)), option_id)
    try:
        out = await run_vv(ctx, run_id=run_id)
        pub = await ResultsSink().publish(study_id, ANALYSIS, parameters=out.parameters, conflicts=out.conflicts,
                                          notes=out.warnings, option_id=option_id, run_id=run_id, ctx=ctx)
        summary = {k: v for k, v in out.summary.items() if k != "items"}
        summary.update({"parameters_written": len(pub.written), "shadowed": [s["name"] for s in pub.shadowed],
                        "conflicts": len(pub.conflicts)})
        run = await finish_run(run_id, "ok", summary=summary, series={"items": out.summary["items"]})
        await refresh_inputs_hash(run_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("V&V closure failed for %s", study_id)
        await finish_run(run_id, "failed", summary={"error": str(exc)})
        await broadcast_mutation(study_id, "analysis_completed", "analysis", ANALYSIS,
                                 {"run_id": run_id, "option_id": option_id, "status": "failed", "error": str(exc)})
        raise HTTPException(500, f"V&V closure failed: {exc}") from exc
    return {
        "run_id": run_id, "analysis": ANALYSIS, "option_id": option_id, "status": run["status"],
        "summary": summary, "items": await _enriched_items(study_id),
        "parameters": [{"name": w["name"], "value": w["value"], "element_id": w["element_id"]} for w in pub.written],
        "shadowed": [{"name": s["name"], "value": s["value"], "element_id": s["element_id"]} for s in pub.shadowed],
        "conflicts": pub.conflicts, "warnings": out.warnings, "stale": False,
    }


@router.get("/studies/{study_id}/analyses/vv")
async def get_vv_analysis(study_id: str, option_id: str | None = Query(None)) -> dict:
    run = await analysis_results.get_last_run(study_id, ANALYSIS, option_id=option_id)
    if run is None:
        raise HTTPException(404, f"No {ANALYSIS} run for study {study_id}")
    run["conflicts"] = await analysis_repo.list_conflicts(study_id, option_id=option_id, analysis=ANALYSIS)
    run["items"] = await _enriched_items(study_id)
    return run


# ── items ───────────────────────────────────────────────────────────────

@router.get("/studies/{study_id}/verification-items")
async def list_verification_items(study_id: str, status: str | None = Query(None),
                                  level: str | None = Query(None), method: str | None = Query(None)) -> dict:
    items = await _enriched_items(study_id)
    if status:
        items = [i for i in items if i.get("status") == status]
    if level:
        items = [i for i in items if i.get("level") == level]
    if method:
        items = [i for i in items if i.get("method") == method]
    return {"study_id": study_id, "items": items, "by_level": _rollup(items), "total": len(items)}


@router.get("/verification-items/{item_id}")
async def get_verification_item(item_id: str) -> dict:
    item = await verification_repo.get_item(item_id)
    if item is None:
        raise HTTPException(404, f"Verification item {item_id} not found")
    return item


@router.patch("/verification-items/{item_id}")
async def patch_verification_item(item_id: str, body: dict[str, Any]) -> dict:
    updates = {k: v for k, v in body.items() if k in EDITABLE_FIELDS}
    if not updates:
        raise HTTPException(400, f"Nothing to update; editable fields: {', '.join(EDITABLE_FIELDS)}")
    if "method" in updates and updates["method"]:
        updates["method"] = str(updates["method"]).upper()[:1]
    try:
        item = await verification_repo.update_item(item_id, updates, by_user=True)
    except ValueError as exc:
        raise HTTPException(404 if "not found" in str(exc) else 400, str(exc)) from exc
    await _broadcast_item(item)
    return item


@router.post("/verification-items/{item_id}/evidence")
async def post_verification_evidence(item_id: str, body: dict[str, Any]) -> dict:
    status = body.get("status") or "passed"
    evidence_ref = body.get("evidence_ref")
    if status not in verification_repo.STATUSES:
        raise HTTPException(400, f"status must be one of {verification_repo.STATUSES}")
    updates: dict[str, Any] = {"status": status}
    if evidence_ref is not None:
        updates["evidence_ref"] = evidence_ref
    if body.get("notes") is not None:
        updates["notes"] = body["notes"]
    try:
        item = await verification_repo.update_item(item_id, updates, by_user=True)
    except ValueError as exc:
        raise HTTPException(404 if "not found" in str(exc) else 400, str(exc)) from exc
    await _broadcast_item(item)
    return item


# ── exports ─────────────────────────────────────────────────────────────

@router.get("/studies/{study_id}/export/rtm.csv")
async def export_rtm_csv(study_id: str) -> StreamingResponse:
    items = await _enriched_items(study_id)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(RTM_COLUMNS)
    for it in sorted(items, key=lambda i: i.get("requirement_code") or ""):
        w.writerow([
            it.get("requirement_code") or "", it.get("requirement_text") or "", it.get("requirement_level") or "",
            it.get("method") or "", it.get("level") or "", it.get("phase") or "", it.get("facility") or "",
            it.get("acceptance_criterion") or "", it.get("status") or "", it.get("evidence_ref") or "",
            "; ".join(it.get("linked_element_names") or []), "; ".join(it.get("linked_functions") or []),
        ])
    data = buf.getvalue().encode("utf-8-sig")
    return _download(data, f"{_slug(_study_name(study_id))}_RTM.csv", "text/csv; charset=utf-8")


def build_vcd_did(study_name: str, items: list[dict]) -> dict:
    """DID JSON for ``docx_generator.generate_did_docx`` — one table per level + roll-up."""
    roll = _rollup(items)
    total = len(items)
    closed = sum(r["passed"] + r["waived"] for r in roll.values())
    rollup_lines = ["| Level | Items | Planned | In progress | Passed | Failed | Waived | Closure |",
                    "|---|---|---|---|---|---|---|---|"]
    for lvl in LEVEL_ORDER:
        r = roll[lvl]
        pct = (100.0 * (r["passed"] + r["waived"]) / r["total"]) if r["total"] else 0.0
        rollup_lines.append(f"| {lvl} | {r['total']} | {r['planned']} | {r['in_progress']} | {r['passed']} | "
                            f"{r['failed']} | {r['waived']} | {pct:.0f} % |")
    rollup_lines.append(f"| **Total** | {total} | | | | | | {(100.0 * closed / total if total else 0):.0f} % |")
    by_method = {m: sum(1 for i in items if i.get("method") == m) for m in METHOD_NAMES}
    method_lines = ["| Method | Items |", "|---|---|"] + [f"| {m} ({METHOD_NAMES[m]}) | {n} |" for m, n in by_method.items()]

    def esc(s: Any) -> str:
        return str(s or "").replace("|", "/").replace("\n", " ")

    level_sections = []
    for i, lvl in enumerate(LEVEL_ORDER):
        rows = [it for it in items if it.get("level") == lvl]
        if rows:
            lines = ["| Req | Requirement | Method | Phase | Model | Event | Facility | Acceptance criterion | Status | Evidence |",
                     "|---|---|---|---|---|---|---|---|---|---|"]
            for it in sorted(rows, key=lambda i: i.get("requirement_code") or ""):
                acc = it.get("requirement_acceptance") or it.get("acceptance_criterion")
                lines.append(f"| {esc(it.get('requirement_code'))} | {esc((it.get('requirement_text') or '')[:120])} | "
                             f"{esc(it.get('method'))} | {esc(it.get('phase'))} | {esc(it.get('verification_model'))} | "
                             f"{esc(it.get('verification_event'))} | {esc(it.get('facility'))} | "
                             f"{esc(acc)} | {esc(it.get('status'))} | {esc(it.get('evidence_ref'))} |")
            content = "\n".join(lines)
        else:
            content = f"No verification items at {lvl} level."
        level_sections.append({"number": f"3.{i + 1}", "title": f"{lvl.capitalize()} level", "content": content})

    failed = [it for it in items if it.get("status") == "failed"]
    open_items = [it for it in items if (it.get("status") or "planned") in ("planned", "in_progress")]
    return {
        "document": "Verification Control Document",
        "standard": "ECSS-E-ST-10-02C",
        "study_name": study_name,
        "document_code": "VCD",
        "issue": "1.0",
        "classification": "Internal",
        "change_record": [{"issue": "1.0", "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                           "by": "SpaceCDF", "summary": "Generated from the study's verification items"}],
        "acronyms": {"A": "Analysis", "T": "Test", "I": "Inspection", "R": "Review of design",
                     "D": "Demonstration", "RTM": "Requirement traceability matrix", "VCD": "Verification control document"},
        "sections": [
            {"number": "1", "title": "Introduction", "content":
                f"This Verification Control Document tracks the verification of every requirement of {study_name} "
                f"per ECSS-E-ST-10-02C. Each requirement carries one verification item with a method, a level, "
                f"a phase, a facility, an acceptance criterion, a status and the evidence that closes it.",
             "subsections": [
                 {"number": "1.1", "title": "Verification methods", "content":
                     "- **A** Analysis — closed automatically when the design analyses meet the requirement threshold\n"
                     "- **T** Test — closed by a test report\n- **I** Inspection\n- **R** Review of design\n- **D** Demonstration"},
             ]},
            {"number": "2", "title": "Verification status roll-up", "content": "\n".join(rollup_lines),
             "subsections": [{"number": "2.1", "title": "Items by method", "content": "\n".join(method_lines)}]},
            {"number": "3", "title": "Verification control matrix", "content":
                "One table per verification level; evidence references of the form analysis:<run id> point at "
                "the SpaceCDF analysis run that closed the item.",
             "subsections": level_sections},
            {"number": "4", "title": "Open and failed items", "content":
                (f"**Failed ({len(failed)})**\n" + "\n".join(f"- {esc(it.get('requirement_code'))}: {esc(it.get('acceptance_criterion'))}"
                                                            for it in failed) + "\n\n" if failed else "No failed items.\n\n")
                + (f"**Open ({len(open_items)})**\n" + "\n".join(f"- {esc(it.get('requirement_code'))} — {esc(it.get('method'))} at "
                                                                 f"{esc(it.get('level'))} level, {esc(it.get('phase'))}"
                                                                 for it in open_items) if open_items else "No open items.")},
        ],
    }


@router.get("/studies/{study_id}/export/vcd.docx")
async def export_vcd_docx(study_id: str) -> StreamingResponse:
    from ..services.docx_generator import generate_did_docx
    name = _study_name(study_id)
    items = await _enriched_items(study_id)
    data = generate_did_docx(build_vcd_did(name, items))
    return _download(data, f"{_slug(name)}_VCD.docx",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ── workbooks for the Export drawer (W1.09i) ───────────────────────────

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
VV_COLUMNS = ["Code", "Level", "Type", "Requirement", "Threshold", "Method", "Stage", "Parent", "Allocated to",
              "Rationale", "Verification level", "Facility", "Acceptance criterion", "Verification status", "Evidence"]
BOM_COLUMNS = ["Line", "Item ID", "Name", "Subsystem", "Segment", "Qty", "Unit Mass (kg)", "Total Mass (kg)",
               "Unit Power (W)", "Total Power (W)", "Unit Cost (kEUR)", "Total Cost (kEUR)", "TRL", "Manufacturer",
               "Model Level", "Procurement", "Export Control", "Lead Time (wk)", "Criticality"]


async def vv_matrix_rows(study_id: str) -> list[list[Any]]:
    """One row per requirement (level then code, every one), with its verification item."""
    from ..services.export_context import collect
    from ..services.docx.ts import threshold_text
    from .exports.docx import requirement_rows_for_docs
    sx = await collect(study_id, sections=("elements", "requirements", "verification"))
    reqs = requirement_rows_for_docs(sx.requirements.get("items") or [], sx.elements.get("items") or [])
    vi = {v.get("requirement_id"): v for v in sx.verification.get("items") or []}
    rows = []
    for r in reqs:
        v = vi.get(r.get("id")) or {}
        rows.append([r.get("code") or r.get("id"), r.get("level") or "", r.get("req_type") or "", r.get("text") or "",
                     threshold_text(r), v.get("method") or r.get("verification_method") or "",
                     r.get("verification_phase") or v.get("phase") or "", r.get("parent_code") or "",
                     r.get("allocated_to") or "", r.get("rationale") or "", v.get("level") or "", v.get("facility") or "",
                     v.get("acceptance_criterion") or "", v.get("status") or "", v.get("evidence_ref") or ""])
    return rows


def bom_rows(study_id: str) -> tuple[str, list[list[Any]]]:
    from ..services.bom_generator import generate_bom_from_elements
    from .elements import _elements
    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    name = _study_name(study_id)
    bom = generate_bom_from_elements(elements, study_name=name) if elements else {"lines": []}
    keys = ["line", "item_id", "name", "subsystem", "segment", "quantity", "unit_mass_kg", "total_mass_kg",
            "unit_power_w", "total_power_w", "unit_cost_keur", "total_cost_keur", "trl", "manufacturer",
            "model_level", "procurement_status", "export_control", "lead_time_weeks", "criticality"]
    return name, [[ln.get(k) for k in keys] for ln in bom.get("lines") or []]


@router.get("/studies/{study_id}/export/vv.xlsx")
async def export_vv_xlsx(study_id: str) -> StreamingResponse:
    from spacecdf_agents.exporters.docs.master_budget import table_workbook
    try:
        rows = await vv_matrix_rows(study_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    data = table_workbook([("V&V matrix", VV_COLUMNS, rows)])
    return _download(data, f"{_slug(_study_name(study_id))}_VV_matrix.xlsx", XLSX)


@router.get("/studies/{study_id}/export/bom.xlsx")
async def export_bom_xlsx(study_id: str) -> StreamingResponse:
    from spacecdf_agents.exporters.docs.master_budget import table_workbook
    name, rows = bom_rows(study_id)
    data = table_workbook([("Bill of materials", BOM_COLUMNS, rows)])
    return _download(data, f"{_slug(name)}_BOM.xlsx", XLSX)
