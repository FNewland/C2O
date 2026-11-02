"""Expected-interface routes (Nov 2026): the rule-based proposer, the type
catalogue and the server-side readiness checklist.

    GET  /api/studies/{sid}/interfaces/types      canonical types, labels EN/FR, glyph, Annex E fields
    GET  /api/studies/{sid}/interfaces/rules      rules file status + disclaimer
    POST /api/studies/{sid}/interfaces/propose    {level?, element_id?, dry_run?} → created/updated/…
    GET  /api/studies/{sid}/readiness?level=&element_id=

Interface CRUD stays in ``routers/elements.py`` (it owns the cache).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# One proposer run at a time per study (element create bursts call it back to back)
_locks: dict[str, asyncio.Lock] = {}


class ProposeRequest(BaseModel):
    level: int | None = None
    element_id: str | None = None
    dry_run: bool = False
    # Optional override (populate-subsystems passes the class it built for)
    spacecraft_class: str | None = None


@router.get("/studies/{study_id}/interfaces/types")
async def interface_types(study_id: str) -> list[dict]:
    """Canonical interface types (ECSS-E-ST-10-24C Annex E natures) with EN/FR labels,
    the glyph name, the reference-data fields per type and the subtypes."""
    from spacecdf_common.models.interface_types import interface_type_catalog
    return interface_type_catalog()


@router.get("/studies/{study_id}/interfaces/rules")
async def interface_rules_info(study_id: str) -> dict:
    """Rules file status and the disclaimer to show beside suggestions."""
    from ..services.interface_proposer import load_rules, rules_status
    st = rules_status()
    out: dict[str, Any] = {**st, "disclaimer": None, "rules": []}
    if st["ok"]:
        cfg = load_rules()
        out["disclaimer"] = dict(cfg["disclaimer"])
        out["rules"] = [{"id": r["id"], "level": r["level"], "type": r["type"], "subtype": r.get("subtype"),
                         "name": dict(r["name"]), "rationale": dict(r["rationale"]),
                         "standard_ref": r["standard_ref"]} for r in cfg["rules"]]
    return out


async def _ensure_exchange_items(study_id: str, names: list[str], specs: dict) -> dict[str, str]:
    """``{name: exchange_item_id}`` — reuse the study's items by name, create the rest."""
    from ..db.exchange_item_repo import create_exchange_item, list_exchange_items_by_study
    existing = {x["name"]: x["id"] for x in await list_exchange_items_by_study(study_id)}
    out: dict[str, str] = {}
    for name in names:
        if name in existing:
            out[name] = existing[name]
            continue
        spec = specs[name]
        item = await create_exchange_item({"study_id": study_id, "name": name, "kind": spec["kind"],
                                           "properties": dict(spec.get("properties") or {}),
                                           "description": "default (interface_rules.yaml)"})
        out[name] = existing[name] = item["id"]
    return out


async def run_proposer(study_id: str, *, level: int | None = None, element_id: str | None = None,
                       dry_run: bool = False, spacecraft_class: str | None = None) -> dict:
    """Propose the expected links and apply them (unless ``dry_run``). Idempotent.

    Returns ``{created, updated, removed, unchanged, skipped_rejected, unmet, conflicts}``.
    Raises :class:`RuleConfigError` when ``interface_rules.yaml`` is invalid.
    """
    from ..services.interface_proposer import conflicts_for, plan, reconcile
    from ..services.readiness import build_context
    from . import elements as el

    lock = _locks.setdefault(study_id, asyncio.Lock())
    async with lock:
        elements = [e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
        interfaces = [i for i in el._interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")]
        ctx = build_context(study_id, elements, spacecraft_class)
        p, ctx = plan(elements, ctx.config, level=level, element_id=element_id, ctx=ctx)
        rec = reconcile(p, ctx, interfaces, study_id, ctx.config)

        created: list[dict] = []
        updated: list[dict] = []
        removed: list[str] = []
        if dry_run:
            created = [dict(new, id=None, version=0, exchange_item_ids_json=[]) for _, new in rec.create]
            updated = [{**own, **changes} for own, changes in rec.update]
            removed = [i["id"] for i in rec.remove]
            check_set = [i for i in interfaces if i["id"] not in set(removed)] + created
            for u in updated:
                check_set = [u if c.get("id") == u["id"] else c for c in check_set]
        else:
            names = sorted({n for d, _ in rec.create for n in d.rule.get("exchange_items") or []})
            item_ids = await _ensure_exchange_items(study_id, names, ctx.config.get("exchange_items") or {}) \
                if names else {}
            for d, new in rec.create:
                new["id"] = uuid4().hex
                new["exchange_item_ids_json"] = [item_ids[n] for n in d.rule.get("exchange_items") or []]
                created.append(await el.store_interface(new))
            for own, changes in rec.update:
                own.update(changes)
                updated.append(await el.save_interface(own))
            for i in rec.remove:
                await el.remove_interface(i)
                removed.append(i["id"])
            check_set = [i for i in el._interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")]
            if created or updated or removed:
                await el._broadcast_interface(study_id, {
                    "type": "interfaces_proposed", "created": len(created), "updated": len(updated),
                    "removed": len(removed)})

        conflicts = conflicts_for(ctx, check_set, p.scope_ids)
        return {
            "created": created,
            "updated": updated,
            "removed": removed,
            "unchanged": rec.unchanged,
            "skipped_rejected": rec.skipped_rejected,
            "unmet": p.unmet,
            "conflicts": conflicts,
            "spacecraft_class": ctx.spacecraft_class,
            "cubesat": ctx.cubesat,
            "dry_run": dry_run,
        }


@router.post("/studies/{study_id}/interfaces/propose")
async def propose_interfaces(study_id: str, body: ProposeRequest | None = None) -> dict:
    """Propose the expected links between the study's elements from ``configs/interface_rules.yaml``.

    Body ``{level?: int, element_id?: str, dry_run?: bool}``. New links are created with
    ``status="suggested"``, ``origin="rule:<id>"``, a bilingual ``rationale`` and a
    ``standard_ref``. Accepted, user-edited and rejected links are never changed;
    a rejected pair+type is never proposed again. Running it twice changes nothing.
    """
    from ..services.interface_proposer import RuleConfigError
    body = body or ProposeRequest()
    if body.element_id:
        from .elements import _elements
        e = _elements.get(body.element_id)
        if not e or e.get("study_id") != study_id or e.get("deleted_at"):
            raise HTTPException(404, f"Element {body.element_id} not found in this study")
    try:
        return await run_proposer(study_id, level=body.level, element_id=body.element_id,
                                  dry_run=body.dry_run, spacecraft_class=body.spacecraft_class)
    except RuleConfigError as e:
        raise HTTPException(422, {"error": "interface_rules_invalid", "errors": e.errors}) from e


@router.get("/studies/{study_id}/readiness")
async def readiness(study_id: str, level: int | None = Query(None),
                    element_id: str | None = Query(None)) -> dict:
    """Server-side readiness checklist for one workbench level (children of ``element_id``,
    or the study roots when it is omitted)."""
    from ..services.readiness import compute_readiness
    return await compute_readiness(study_id, level=level, element_id=element_id)
