"""Product tree API: default trees, adding spacecraft, level check and migration.

    GET  /api/product-tree/levels                       ECSS / NASA levels and allowed children
    POST /api/studies/{id}/product-tree/default         mission → segments → spacecraft → subsystems
                                                         (+ User Segment and a Harness subsystem: W2.09)
    POST /api/studies/{id}/spacecraft                   another spacecraft under the space segment
    GET  /api/studies/{id}/product-tree/check           elements placed at the wrong level
    POST /api/studies/{id}/product-tree/migrate         insert a Spacecraft above subsystems that
                                                         hang off the space segment (idempotent)

The rules live in ``services/product_tree.py``. Every study is migrated once at start-up
(``migrate_all``), so existing studies open with the corrected tree.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services import product_tree as pt
from . import elements as er

logger = logging.getLogger(__name__)
router = APIRouter()


def _study_elements(study_id: str) -> list[dict]:
    return [e for e in er._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


async def _new(study_id: str, **kw: Any) -> dict:
    """Create an element without the per-element link proposer (one run at the end)."""
    el = {"id": uuid4().hex, "study_id": study_id, **er.ElementCreate(**kw).model_dump(), "version": 1, "deleted_at": None}
    er._sync_maturity(el)
    await er.db_create_element(el)
    er._elements[el["id"]] = el
    return el


@router.get("/product-tree/levels")
async def levels() -> dict:
    return {"levels": [{"level": n, "name": pt.LEVEL_NAMES[n],
                        "element_types": sorted(t for t, lv in pt.TREE_LEVEL.items() if lv == n)} for n in range(5)],
            "allowed_children": {str(k): list(v) for k, v in pt.ALLOWED_CHILDREN.items()},
            "architectures": {k: [{"name": s["name"], "segment": s["segment"],
                                   "systems": [x["name"] for x in s["systems"]]} for s in v]
                              for k, v in pt.ARCHITECTURES.items()},
            "standard": "ECSS-M-ST-10C Rev.1 product tree; NASA SP-2016-6105 product breakdown"}


class DefaultTreeRequest(BaseModel):
    architecture: str = "single-leo"
    mission_name: str = "Mission"
    spacecraft_class: str = "nano"
    include_equipment: bool = False


@router.post("/studies/{study_id}/product-tree/default")
async def create_default_tree(study_id: str, body: DefaultTreeRequest) -> dict:
    """The wizard's starting tree: Mission → segments → Spacecraft → standard subsystems,
    Ground Segment → ground station(s). Reuses an existing mission root."""
    try:
        arch = pt.default_tree(body.architecture)
    except KeyError:
        raise HTTPException(404, f"Unknown architecture {body.architecture!r}; one of {sorted(pt.ARCHITECTURES)}")
    els = _study_elements(study_id)
    root = next((e for e in els if e.get("element_type") == "mission" and not e.get("parent_id")), None)
    created: list[dict] = []
    if root is None:
        root = await _new(study_id, name=body.mission_name or "Mission", element_type="mission", segment="space")
        created.append(root)
    spacecraft: list[dict] = []
    for i, seg in enumerate(arch):
        s = await _new(study_id, name=seg["name"], element_type="segment", segment=seg["segment"], parent_id=root["id"],
                       diagram_x=80 + (i % 4) * 200, diagram_y=40 + (i // 4) * 140)
        created.append(s)
        for j, sysdef in enumerate(seg["systems"]):
            el = await _new(study_id, name=sysdef["name"], element_type="system", segment=seg["segment"],
                            parent_id=s["id"], subsystem_domain=sysdef.get("domain"),
                            quantity=int(sysdef.get("quantity") or 1),
                            performance=({**(sysdef.get("performance") or {}), "spacecraft_class": body.spacecraft_class}
                                         if sysdef.get("spacecraft") else sysdef.get("performance")),
                            diagram_x=80 + (j % 4) * 200, diagram_y=40 + (j // 4) * 140)
            created.append(el)
            if sysdef.get("spacecraft"):
                spacecraft.append(el)
    populated: list[dict] = []
    for sc in spacecraft:   # subsystems (+ equipment on request), roll-up defaults, expected links
        populated.append(await er.populate_subsystems(
            study_id, parent_element_id=sc["id"],
            body=er.PopulateRequest(spacecraft_class=body.spacecraft_class, include_equipment=body.include_equipment)))
        # W2.09: a Harness subsystem, so harness requirements have an element to land on
        if not any(e.get("parent_id") == sc["id"] and "harness" in (e.get("name") or "").lower()
                   for e in _study_elements(study_id)):
            created.append(await _new(study_id, name="Harness", element_type="subsystem", segment="space",
                                      parent_id=sc["id"], subsystem_domain="harness",
                                      owner_position="systems_engineer"))
    await _broadcast(study_id, "product_tree_created", len(created))
    return {"mission_id": root["id"], "created": len(created) + sum(p.get("created", 0) for p in populated),
            "segment_ids": {e["name"]: e["id"] for e in created if e["element_type"] == "segment"},
            "spacecraft_ids": [e["id"] for e in spacecraft],
            "subsystems": sum(len(p.get("subsystem_ids") or {}) for p in populated)}


class SpacecraftRequest(BaseModel):
    segment_id: str | None = None
    name: str | None = None
    spacecraft_class: str = "nano"
    populate: bool = True
    include_equipment: bool = False


@router.post("/studies/{study_id}/spacecraft")
async def add_spacecraft(study_id: str, body: SpacecraftRequest) -> dict:
    """Another spacecraft (level 2) under the space segment, with the standard subsystems."""
    els = _study_elements(study_id)
    idx = {e["id"]: e for e in els}
    if body.segment_id:
        seg = idx.get(body.segment_id)
        if seg is None or seg.get("element_type") != "segment":
            raise HTTPException(404, f"Segment {body.segment_id} not found in study {study_id}")
    else:
        seg = next((e for e in els if pt.is_space_segment(e, idx)), None)
        if seg is None:
            raise HTTPException(409, {"error": "no_space_segment", "message": {
                "en": "This study has no space segment: add one under the mission first.",
                "fr": "Cette étude n’a pas de segment spatial : en ajouter un sous la mission d’abord."}})
    n = sum(1 for e in els if e.get("parent_id") == seg["id"] and e.get("element_type") == "system")
    name = body.name or ("Spacecraft" if n == 0 else f"Spacecraft {n + 1}")
    if body.populate:
        res = await er.populate_subsystems(study_id, parent_element_id=seg["id"], body=er.PopulateRequest(
            spacecraft_class=body.spacecraft_class, include_equipment=body.include_equipment,
            new_system=True, system_name=name))
        return {"spacecraft_id": res["system_id"], "name": name, "subsystem_ids": res["subsystem_ids"],
                "created": res["created"]}
    el = await _new(study_id, name=name, element_type="system", segment=seg.get("segment") or "space",
                    parent_id=seg["id"], performance={"spacecraft_class": body.spacecraft_class})
    await _broadcast(study_id, "elements_populated", 1)
    return {"spacecraft_id": el["id"], "name": name, "subsystem_ids": {}, "created": 1}


@router.get("/studies/{study_id}/product-tree/check")
async def check(study_id: str) -> dict:
    els = _study_elements(study_id)
    bad = pt.misplaced(els)
    plan = pt.plan_migration(els, lambda: "new")
    return {"ok": not bad, "misplaced": [{"id": e["id"], "name": e.get("name"), "element_type": e.get("element_type"),
                                          "parent_id": e.get("parent_id")} for e in bad],
            "spacecraft": [{"id": s["id"], "name": s.get("name")} for s in pt.spacecraft_systems(els)],
            "migration_pending": bool(plan["create"] or plan["update"]), "ambiguous": plan["ambiguous"]}


async def migrate_study(study_id: str) -> dict:
    """Apply the space-segment migration to one study (write-through: DB then cache)."""
    els = _study_elements(study_id)
    plan = pt.plan_migration(els, lambda: uuid4().hex)
    for c in plan["create"]:
        er._sync_maturity(c)
        await er.db_create_element(c)
        er._elements[c["id"]] = c
    for u in plan["update"]:
        el = er._elements.get(u["id"])
        if el is None:
            continue
        el.update(u["changes"])
        el["version"] = int(el.get("version") or 1) + 1
        await er.db_update_element(el["id"], el)
    if plan["create"] or plan["update"]:
        logger.info("product tree migrated for study %s: %d spacecraft inserted, %d elements moved",
                    study_id, len(plan["create"]), len(plan["update"]))
        await _broadcast(study_id, "product_tree_migrated", len(plan["update"]))
    return {"study_id": study_id, "inserted": [c["id"] for c in plan["create"]],
            "moved": [u["id"] for u in plan["update"]],
            "retyped": [u["id"] for u in plan["update"] if "element_type" in u["changes"]],
            "ambiguous": plan["ambiguous"]}


@router.post("/studies/{study_id}/product-tree/migrate")
async def migrate(study_id: str) -> dict:
    return await migrate_study(study_id)


async def migrate_all() -> dict:
    """Start-up: migrate every study in the element cache (idempotent)."""
    studies = sorted({e.get("study_id") for e in er._elements.values() if e.get("study_id")})
    moved = inserted = 0
    for sid in studies:
        r = await migrate_study(sid)
        moved += len(r["moved"])
        inserted += len(r["inserted"])
    return {"studies": len(studies), "inserted": inserted, "moved": moved}


async def _broadcast(study_id: str, kind: str, count: int) -> None:
    try:
        from .ws import _broadcast_study
        await _broadcast_study(study_id, {"type": kind, "count": count})
    except Exception:  # noqa: BLE001
        logger.debug("broadcast failed", exc_info=True)
