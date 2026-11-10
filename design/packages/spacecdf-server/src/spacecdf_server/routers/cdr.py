"""CDR design model routes: TM/TC database, FDIR, AOCS modes, TT&C ladder, line states, operations.

    GET    /api/studies/{sid}/cdr                       rows by kind, checks, HK budget, FMECA coverage, dataset
    GET    /api/studies/{sid}/cdr/checks
    POST   /api/studies/{sid}/cdr/propose               {dry_run?} → created / updated / removed / …
    POST   /api/studies/{sid}/cdr/{kind}                {data} create (origin user, accepted)
    PATCH  /api/studies/{sid}/cdr/{kind}/{id}           {data?, status?, accept_update?, dismiss_update?, version?}
    DELETE /api/studies/{sid}/cdr/{kind}/{id}           user row deleted, rule row rejected
    POST   /api/studies/{sid}/cdr/accept-all            {group?} accept the suggestions the caller may review
    POST   /api/studies/{sid}/cdr/import/eosat1         {replace?} load the EOSAT-1 reference database (read-only)
    DELETE /api/studies/{sid}/cdr/import                remove the reference database
    GET    /api/studies/{sid}/cdr/export/sim            the rows in the simulator's file shapes
    GET    /api/cdr/export-map                          CDR kind/field → simulator file/key
    GET    /api/studies/{sid}/cdr/export/tmtc.{json,csv,xlsx}  the TM/TC database generated from the SIDs (W4.05)
    GET    /api/studies/{sid}/data-budget               the data budget (W3.02, services/data_budget.py)
    POST   /api/studies/{sid}/data-budget/scenario      {compression_ratio, science_mb_per_day, rt_policy, diagnostics, …}

Ownership (REDESIGN_DECISIONS.md ruling 5): the TM/TC database belongs to Comms & OBDH and each
parameter (and its monitors and limits) to the seat of its subsystem; event-actions, safe mode
and FDIR levels to Systems; the load-shed table and line states to Power; AOCS modes and
control to AOCS; the operations tables to Mission analysis & ops. Another seat's edit is
refused with 409 ``owned_by_other_seat`` first, then stored as a pending change
(``X-C2O-Confirm-Review: 1``) the owner accepts or rejects. The Team leader may accept or reject
proposals for any seat. Rows of the EOSAT-1 reference import are read-only (423).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from ..db import cdr_repo as repo
from ..services import cdr_model as cm

logger = logging.getLogger(__name__)
router = APIRouter()
_locks: dict[str, asyncio.Lock] = {}

STATUSES = ("suggested", "accepted", "rejected")


class ProposeBody(BaseModel):
    dry_run: bool = False


class ImportBody(BaseModel):
    replace: bool = False


class AcceptAllBody(BaseModel):
    group: str | None = None      # tmtc | fdir | aocs | ops; None = every kind


def _kind_or_404(kind: str) -> str:
    if kind not in cm.KINDS:
        raise HTTPException(404, f"unknown CDR collection {kind!r}; one of {list(cm.KINDS)}")
    return kind


def _els(study_id: str) -> list[dict]:
    from . import elements as el
    return [e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


async def _broadcast(study_id: str, what: str) -> None:
    try:
        from .ws import _broadcast_study
        await _broadcast_study(study_id, {"type": "cdr_changed", "what": what})
    except Exception:
        logger.debug("cdr broadcast failed", exc_info=True)


# ───────────────────────────────────────────────────────────── facts

async def gather_facts(study_id: str) -> dict[str, Any]:
    """Everything the proposer and the checks read, from the stored study."""
    from ..db import electrical_repo, mode_repo
    els = _els(study_id)
    elec = await electrical_repo.load_all(study_id)
    modes = [{"id": m["id"], "name": m.get("name"), "kind": (m.get("performance") or {}).get("mode_kind") or "custom"}
             for m in sorted([e for e in els if e.get("element_type") == "mode"],
                             key=lambda m: (float((m.get("performance") or {}).get("order") or 999), m.get("name") or ""))]
    try:
        members = await mode_repo.list_members([m["id"] for m in modes])
    except Exception:  # noqa: BLE001
        members = []
    try:
        props = [p for p in await mode_repo.list_proposals(study_id) if p.get("kind") in ("monitor", "action")]
        heaters = await mode_repo.list_heaters(study_id)
    except Exception:  # noqa: BLE001
        props, heaters = [], []
    return {"elements": els, "lines": elec.get("lines") or [], "rails": elec.get("rails") or [],
            "buses": elec.get("buses") or [], "heaters": heaters, "modes": modes, "members": members,
            "fdir_proposals": props}


def credited_elements(rows: list[dict], proposals: list[dict]) -> set[str]:
    """Elements with an ACCEPTED monitor (rule-8 proposal or CDR monitor): FMECA detection credit."""
    from ..services.mode_rules import monitored_element_ids
    out = set(monitored_element_ids(proposals))
    for r in rows:
        if r.get("kind") == "monitors" and r.get("status") == "accepted" and not r.get("deleted_at"):
            eid = (r.get("data") or {}).get("element_id")
            if eid:
                out.add(eid)
    return out


def _fmeca(study_id: str, els: list[dict], monitored: set[str]) -> list[dict]:
    try:
        from ..services.fmeca_library import build_skeleton
        from .elements import active_interfaces
        return build_skeleton(els, active_interfaces(study_id), monitored=monitored)["rows"]
    except Exception:  # noqa: BLE001
        logger.debug("FMECA unavailable for %s", study_id, exc_info=True)
        return []


async def cdr_view(study_id: str, *, rows: list[dict] | None = None, keep: dict | None = None) -> dict[str, Any]:
    from ..services.cdr_checks import fmeca_coverage, hk_budget, run_checks, summarise
    from ..services.cdr_propose import design_facts
    rows = rows if rows is not None else await repo.list_rows(study_id)
    facts = await gather_facts(study_id)
    dataset = cm.dataset_of(rows)
    ref = dataset == "reference"
    units = [] if ref else [{"id": u["id"], "cls": u["cls"], "sub": u["sub"], "name": u["name"]}
                            for u in design_facts(facts)["units"]]
    fmeca = [] if ref else _fmeca(study_id, facts["elements"], credited_elements(rows, facts["fdir_proposals"]))
    ctx = {"lines": [] if ref else facts["lines"], "units": units, "members": facts["members"],
           "modes": [] if ref else facts["modes"], "fmeca_rows": fmeca, "reference": ref}
    if not ref and any(r.get("kind") == "hk" and not r.get("deleted_at") for r in rows):
        try:
            from ..services.data_budget import for_study
            ctx["data_budget"] = await for_study(study_id, rows=rows, include_degraded=False)
        except Exception:  # noqa: BLE001 — the checks run without the daily budget
            logger.debug("data budget unavailable for %s", study_id, exc_info=True)
    findings = run_checks(rows, ctx)
    if keep is not None and "data_budget" in ctx:
        keep["data_budget"] = ctx["data_budget"]
    c = cm.cfg()
    return {
        "study_id": study_id, "dataset": dataset,
        "rows": cm.group_rows(rows),
        "checks": findings, "summary": summarise(findings),
        "budget": hk_budget(rows, ctx["modes"]),
        "fmeca": fmeca_coverage(rows, fmeca),
        "owners": {k: v["owner"] for k, v in cm.KINDS.items()},
        "groups": {k: v["group"] for k, v in cm.KINDS.items()},
        "modes": facts["modes"], "lines": [{"id": l["id"], "name": l.get("name"), "line_no": l.get("line_no"),
                                            "switchable": l.get("switchable"), "status": l.get("status")}
                                           for l in facts["lines"] if l.get("status") != "rejected"],
        "vocabulary": {
            "check_types": c["fdir"]["check_types"], "monitor_severities": c["fdir"]["monitor_severities"],
            "event_severities": c["events"]["severities"], "types": list(c["types"]["bytes"]),
            "modulations": c["ttc"]["modulations"], "codings": c["ttc"]["codings"],
            "criticalities": ["normal", "caution", "critical"], "triggers": ["ground_tc", "autonomous", "timer", "event"],
            "limits": ["high", "low", "any"],
            "subsystems": [{"key": s["key"], "label": s["label"], "seat": s["seat"]} for s in cm.subsystems(c)],
            "pus_services": [{"service": s["service"], "name": s["name"]} for s in c["pus_services"]["list"]],
        },
        "refs": {g: cm.ref(c[sec], c) for g, sec in (("tmtc", "functions"), ("pus", "pus_services"), ("fdir", "fdir"),
                                                       ("aocs", "aocs"), ("ttc", "ttc"), ("ops", "ops"),
                                                       ("budget", "downlink_budget"))},
    }


async def cdr_gate_summary(study_id: str) -> dict[str, Any]:
    """What the CDR exit criteria read (routers/gates.gate_inputs → ctx["cdr"]). ``data_budget``:
    the daily data budget (W3.05: PDR-EC-06 and CDR-EC-04 read it through gate_evaluator)."""
    rows = await repo.list_rows(study_id)
    keep: dict[str, Any] = {}
    v = await cdr_view(study_id, rows=rows, keep=keep)
    budget = keep.get("data_budget")
    if budget is None and v["dataset"] != "reference":
        try:
            from ..services.data_budget import for_study
            budget = await for_study(study_id, rows=rows, include_degraded=False)
        except Exception:  # noqa: BLE001 — no modes or no network: the criteria say so
            logger.debug("data budget unavailable for %s", study_id, exc_info=True)
    return {"dataset": v["dataset"], "rows": rows, "checks": v["checks"], "summary": v["summary"],
            "budget": v["budget"], "fmeca": v["fmeca"]["summary"], "lines": v["lines"], "modes": v["modes"],
            "data_budget": budget}


# ───────────────────────────────────────────────────────────── routes: read

@router.get("/studies/{study_id}/cdr")
async def get_cdr(study_id: str) -> dict:
    """The CDR design model of the study with its checks, HK downlink budget and FMECA coverage."""
    return jsonable_encoder(await cdr_view(study_id))


@router.get("/studies/{study_id}/cdr/checks")
async def get_cdr_checks(study_id: str) -> list[dict]:
    return (await cdr_view(study_id))["checks"]


@router.get("/cdr/export-map")
async def export_map() -> dict:
    from ..services.cdr_sim import EXPORT_MAP
    return {"map": EXPORT_MAP}


@router.get("/studies/{study_id}/cdr/export/sim")
async def export_sim(study_id: str) -> dict:
    from ..services.cdr_sim import EXPORT_MAP, export_sim as to_sim
    rows = await repo.list_rows(study_id)
    return jsonable_encoder({"study_id": study_id, "files": to_sim(rows), "map": EXPORT_MAP})


@router.get("/studies/{study_id}/data-budget")
async def get_data_budget(study_id: str) -> dict:
    """W3.02: real-time and stored HK per mode and profile, stores, per-pass allocation, day in the
    life, 7-day backlog and the daily closure cases — the numbers every other view quotes."""
    from ..services.data_budget import for_study
    await _study_or_404(study_id)
    return jsonable_encoder(await for_study(study_id))


class ScenarioBody(BaseModel):
    compression_ratio: float | None = None
    science_mb_per_day: float | None = None
    basis: str | None = None                 # target | products
    rt_policy: str | None = None             # per_pass | full_every_pass
    diagnostics: bool = False
    other_mb: float | None = None
    link_rate_bps: float | None = None


@router.post("/studies/{study_id}/data-budget/scenario")
async def data_budget_scenario(study_id: str, body: ScenarioBody) -> dict:
    """The data budget with what-if values (nothing is stored); the closure is the scenario case."""
    from ..services.data_budget import for_study
    await _study_or_404(study_id)
    sc = {k: v for k, v in body.model_dump().items() if v is not None and v is not False}
    return jsonable_encoder(await for_study(study_id, sc or {"rt_policy": "per_pass"}))


async def _study_or_404(study_id: str) -> None:
    from .studies import get_study_store
    if get_study_store().get(study_id) is None and not _els(study_id):
        raise HTTPException(404, f"Study {study_id} not found")


@router.get("/studies/{study_id}/cdr/export/tmtc.{fmt}")
async def export_tmtc(study_id: str, fmt: str):
    """W4.05: the TM/TC database generated from the study's SIDs — parameters, SIDs with their
    real-time and stored intervals per mode and enable flags, stores, profiles, services, events
    and commands — as JSON, CSV (one file, a ``table`` column per section) or XLSX (one sheet each)."""
    from fastapi.responses import Response
    from ..services import tmtc_export
    await _study_or_404(study_id)
    if fmt not in ("json", "csv", "xlsx"):
        raise HTTPException(404, "format must be json, csv or xlsx")
    rows = await repo.list_rows(study_id)
    modes = (await gather_facts(study_id))["modes"]
    data = tmtc_export.tables(rows, modes)
    if fmt == "json":
        return jsonable_encoder(data)
    if fmt == "csv":
        return Response(tmtc_export.to_csv(data), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="tmtc_{study_id[:8]}.csv"'})
    return Response(tmtc_export.to_xlsx(data),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="tmtc_{study_id[:8]}.xlsx"'})


# ───────────────────────────────────────────────────────────── routes: propose / import

async def run_propose(study_id: str, *, dry_run: bool = False) -> dict:
    from ..services.cdr_propose import plan
    lock = _locks.setdefault(study_id, asyncio.Lock())
    async with lock:
        existing = await repo.list_rows(study_id, include_deleted=False)
        if cm.dataset_of(existing) == "reference":
            raise HTTPException(409, {"code": "reference_dataset",
                                      "message": "This study holds the EOSAT-1 reference database; remove it before proposing a design database."})
        facts = await gather_facts(study_id)
        facts["existing"] = existing
        desired = plan(study_id, facts)
        ops = cm.reconcile(desired, existing)
        summary = {"created": len(ops["create"]), "updated": len(ops["update"]), "removed": len(ops["remove"]),
                   "unchanged": ops["unchanged"], "skipped_rejected": ops["skipped_rejected"], "dry_run": dry_run}
        if dry_run:
            summary["operations"] = jsonable_encoder({k: ops[k] for k in ("create", "update", "remove")})
            return summary
        await repo.create_rows([{**r, "study_id": study_id} for r in ops["create"]])
        await repo.update_rows(ops["update"])
        await repo.soft_delete_rows(ops["remove"])
    if ops["create"] or ops["update"] or ops["remove"]:
        await _broadcast(study_id, "proposed")
    return summary


@router.post("/studies/{study_id}/cdr/propose")
async def propose(study_id: str, body: ProposeBody | None = None) -> dict:
    """Propose the default CDR database from the design (elements, modes, power lines, buses,
    sensors/actuators, rule-8 FDIR proposals). New rows are ``suggested`` (origin ``rule:<id>``);
    accepted and edited rows are never changed (a moved input marks them stale); rejected rows are
    never proposed again. Running it twice changes nothing."""
    return await run_propose(study_id, dry_run=(body or ProposeBody()).dry_run)


@router.post("/studies/{study_id}/cdr/accept-all")
async def accept_all(study_id: str, request: Request, body: AcceptAllBody | None = None) -> dict:
    """Accept every suggested row (of a group) the caller may review: rows of the seats they hold,
    or any row for the Team leader / instructor / a study without seats. Others are left for
    their owner (counted in ``left_for_owner``)."""
    from ..seats import config as seat_cfg
    from ..seats.service import seat_ctx, used_seats
    body = body or AcceptAllBody()
    rows = await repo.list_rows(study_id)
    ctx = await seat_ctx(request, study_id)
    todo, left = [], 0
    for r in rows:
        if r.get("status") != "suggested" or r.get("origin") == cm.IMPORT_ORIGIN:
            continue
        if body.group and cm.KINDS.get(r["kind"], {}).get("group") != body.group:
            continue
        if ctx.enabled and not (ctx.instructor or ctx.holds("team_leader")):
            owner = seat_cfg.resolve_in_study(r.get("owner_seat"), used_seats(ctx.state))
            if owner is not None and not ctx.holds(owner):
                left += 1
                continue
        todo.append((r["id"], {"status": "accepted"}))
    await repo.update_rows(todo)
    if todo:
        await _broadcast(study_id, "accepted")
    return {"accepted": len(todo), "left_for_owner": left}


@router.post("/studies/{study_id}/cdr/import/eosat1")
async def import_eosat1(study_id: str, request: Request, body: ImportBody | None = None) -> dict:
    """Load the EOSAT-1 database (sim/configs/eosat1) into the study, read-only, as a reference
    example. Refused (409) when the study already holds design rows, unless ``replace``."""
    from ..seats.service import require_gate_role
    from ..services.cdr_sim import import_eosat1 as do_import
    await require_gate_role(request, study_id)
    body = body or ImportBody()
    existing = await repo.list_rows(study_id)
    design = [r for r in existing if r.get("origin") != cm.IMPORT_ORIGIN]
    if design and not body.replace:
        raise HTTPException(409, {"code": "study_has_design",
                                  "message": f"The study has {len(design)} design rows; import into an empty study, or pass replace=true."})
    try:
        rows = do_import(study_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, {"code": "sim_config_missing", "message": str(exc)}) from exc
    await repo.purge_study(study_id)
    await repo.create_rows(rows)
    await _broadcast(study_id, "imported")
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    return {"study_id": study_id, "imported": len(rows), "counts": counts, "dataset": "reference"}


@router.delete("/studies/{study_id}/cdr/import")
async def remove_import(study_id: str, request: Request) -> dict:
    from ..seats.service import require_gate_role
    await require_gate_role(request, study_id)
    n = await repo.purge_study(study_id, origin_prefix=cm.IMPORT_ORIGIN)
    await _broadcast(study_id, "import_removed")
    return {"study_id": study_id, "removed": n}


# ───────────────────────────────────────────────────────────── ownership

async def _decide(request: Request, study_id: str, owner_seat: str | None, *, review_only: bool) -> dict:
    """``{"mode": open|direct|pending, ...}`` per ruling 5 (raises the 403/409)."""
    from ..seats import config as seat_cfg
    from ..seats.identity import confirmed_review
    from ..seats.service import _http, seat_ctx, used_seats
    ctx = await seat_ctx(request, study_id)
    if not ctx.enabled:
        return {"mode": "open", "ctx": ctx, "owner": None}
    owner = seat_cfg.resolve_in_study(owner_seat, used_seats(ctx.state)) if owner_seat else None
    if owner is None or ctx.holds(owner) or ctx.instructor or (review_only and ctx.holds("team_leader")):
        return {"mode": "direct", "ctx": ctx, "owner": owner}
    if ctx.active_kind not in seat_cfg.EDITING_KINDS:
        raise _http(403, "read_only_seat", "Your seat cannot edit design parameters")
    if not confirmed_review(request):
        raise _http(409, "owned_by_other_seat",
                    f"Owned by {seat_cfg.label(owner)['en']} — your change goes to them for review",
                    owner_seat=owner, owner_label=seat_cfg.label(owner), element_name="")
    return {"mode": "pending", "ctx": ctx, "owner": owner}


def _read_only(row: dict) -> None:
    if row.get("origin") == cm.IMPORT_ORIGIN:
        raise HTTPException(423, {"code": "reference_read_only",
                                  "message": "The EOSAT-1 reference database is read-only. Remove the import to design your own."})


def _clean_data(kind: str, data: Any) -> dict:
    if not isinstance(data, dict):
        raise HTTPException(400, "data must be an object")
    out = {k: v for k, v in data.items() if not str(k).startswith("_")}
    for k in ("param_id", "func_id", "event_id", "sid", "apid", "code", "service", "ea_id", "level"):
        if k in out and isinstance(out[k], str):
            s = out[k].strip()
            try:
                out[k] = int(s, 16) if s.lower().startswith("0x") else int(s)
            except ValueError as e:
                raise HTTPException(400, f"{k} must be an integer or 0x.. hex (got {s!r})") from e
    return out


async def apply_change(study_id: str, row_id: str, changes: dict) -> dict:
    """Apply a (reviewed) change: data merge, status, accept / dismiss the rule's update.
    Shared by PATCH and the pending-change acceptance (seats/changes.apply_pending)."""
    row = await repo.get_row(row_id)
    if row is None or row.get("deleted_at") or row.get("study_id") != study_id:
        raise HTTPException(404, f"CDR row {row_id} not found")
    _read_only(row)
    upd: dict[str, Any] = {}
    if changes.get("accept_update"):
        prop = row.get("proposed")
        if row.get("review") == "orphan":
            upd["status"] = "rejected"
        if prop:
            upd["data"] = prop
            upd["inputs_hash"] = cm.inputs_hash({"key": row.get("key"), "data": prop})
        upd.update({"review": None, "proposed": None, "edited": False})
    elif changes.get("dismiss_update"):
        prop = row.get("proposed")
        if prop:
            upd["inputs_hash"] = cm.inputs_hash({"key": row.get("key"), "data": prop})
        upd.update({"review": None, "proposed": None})
    if "data" in changes and changes["data"] is not None:
        new = {**(row.get("data") or {}), **_clean_data(row["kind"], changes["data"])}
        if new != row.get("data"):
            upd["data"] = new
            upd["key"] = cm.key_of(row["kind"], new)
            upd["owner_seat"] = cm.owner_seat(row["kind"], new)
            upd["edited"] = True
            if row.get("status") == "suggested":
                upd["status"] = "accepted"
    if "status" in changes:
        if changes["status"] not in STATUSES:
            raise HTTPException(400, f"status must be one of {STATUSES}")
        upd["status"] = changes["status"]
    if not upd:
        return row
    out = await repo.update_row(row_id, upd)
    await _broadcast(study_id, row["kind"])
    return out


@router.post("/studies/{study_id}/cdr/{kind}")
async def create_row(study_id: str, kind: str, body: dict[str, Any], request: Request) -> Any:
    _kind_or_404(kind)
    data = _clean_data(kind, body.get("data", {}))
    existing = await repo.list_rows(study_id)
    if cm.dataset_of(existing) == "reference":
        raise HTTPException(423, {"code": "reference_read_only", "message": "The study holds the read-only EOSAT-1 reference database."})
    key = cm.key_of(kind, data)
    if not key:
        raise HTTPException(400, "the row needs its key field (name, id, sid …)")
    if any(r["kind"] == kind and r.get("key") == key and r.get("status") != "rejected" for r in existing):
        raise HTTPException(409, {"code": "duplicate_key", "message": f"{kind} {key} already exists"})
    owner = cm.owner_seat(kind, data)
    decision = await _decide(request, study_id, owner, review_only=False)
    if decision["mode"] == "pending":
        raise HTTPException(409, {"code": "owned_by_other_seat", "message": "Ask the owning seat to add it"})
    out = await repo.create_row({"study_id": study_id, "kind": kind, "key": key, "data": data, "owner_seat": owner,
                                 "origin": "user", "status": "accepted", "edited": False})
    await _broadcast(study_id, kind)
    return out


@router.patch("/studies/{study_id}/cdr/{kind}/{row_id}")
async def patch_row(study_id: str, kind: str, row_id: str, body: dict[str, Any], request: Request) -> Any:
    """Edit ``data`` (merged; the row becomes the user's: ``edited``, a suggestion becomes
    accepted), accept / reject a proposal (``status``), or take / dismiss the rule's new values
    on a stale row (``accept_update`` / ``dismiss_update``)."""
    _kind_or_404(kind)
    row = await repo.get_row(row_id)
    if row is None or row.get("deleted_at") or row.get("study_id") != study_id or row.get("kind") != kind:
        raise HTTPException(404, f"{kind} {row_id} not found")
    _read_only(row)
    if body.get("version") is not None and int(body["version"]) != int(row.get("version") or 1):
        raise HTTPException(409, {"error": "version_conflict", "your_version": body["version"],
                                  "current_version": row.get("version"), "current_state": jsonable_encoder(row)})
    changes = {k: v for k, v in body.items() if k != "version"}
    review_only = set(changes) <= {"status", "accept_update", "dismiss_update"}
    decision = await _decide(request, study_id, row.get("owner_seat") or cm.owner_seat(kind, row.get("data") or {}),
                             review_only=review_only)
    if decision["mode"] == "pending":
        from ..seats import changes as seat_changes
        element = {"id": row_id, "study_id": study_id, "name": f"{kind} {row.get('key')}"}
        old = {"data": row.get("data")} if "data" in changes else {k: row.get(k) for k in changes}
        pc = await seat_changes.propose(request, decision, element, "cdr", old, {"_entity": kind, "_id": row_id, **changes})
        return seat_changes.pending_response(row, pc)
    return await apply_change(study_id, row_id, changes)


@router.delete("/studies/{study_id}/cdr/{kind}/{row_id}")
async def delete_row(study_id: str, kind: str, row_id: str, request: Request) -> dict:
    """Delete a user row. A rule row is rejected instead (so it is not proposed again)."""
    _kind_or_404(kind)
    row = await repo.get_row(row_id)
    if row is None or row.get("study_id") != study_id or row.get("kind") != kind:
        raise HTTPException(404)
    _read_only(row)
    decision = await _decide(request, study_id, row.get("owner_seat"), review_only=False)
    if decision["mode"] == "pending":
        raise HTTPException(409, {"code": "owned_by_other_seat", "message": "Ask the owning seat to delete it"})
    if str(row.get("origin") or "").startswith("rule:"):
        await repo.update_row(row_id, {"status": "rejected"})
        result = {"id": row_id, "rejected": True}
    else:
        await repo.soft_delete_rows([row_id])
        result = {"id": row_id, "deleted": True}
    await _broadcast(study_id, kind)
    return result

