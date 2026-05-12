"""Design Element CRUD API — model-centric architecture.

Every block in a diagram is a rich object. This router provides CRUD,
tree traversal, budget computation, and interface management.

Persistence: write-through cache.  In-memory dicts are the primary read
path (fast).  Every mutation is mirrored to the database via element_repo
so data survives restarts.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..db.element_repo import (
    db_bulk_create_elements,
    db_bulk_create_interfaces,
    db_create_element,
    db_create_interface,
    db_soft_delete_element,
    db_soft_delete_interface,
    db_update_element,
    load_all_elements,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── In-memory store (write-through cache — DB is source of truth) ───
_elements: dict[str, dict] = {}
_interfaces: dict[str, dict] = {}
_mode_elements: list[dict] = []
_budget_allocations: list[dict] = []


async def init_element_cache() -> None:
    """Load persisted elements and interfaces into the in-memory cache.

    Called once during application startup (from app.py lifespan).
    """
    loaded_els, loaded_ifaces = await load_all_elements()
    _elements.update(loaded_els)
    _interfaces.update(loaded_ifaces)
    logger.info(
        "Element cache initialized: %d elements, %d interfaces",
        len(_elements), len(_interfaces),
    )


# ─── Pydantic models ───

class ElementCreate(BaseModel):
    name: str
    element_type: str  # mission|segment|system|subsystem|component|software|mode|logical
    parent_id: str | None = None
    subsystem_domain: str | None = None
    segment: str = "space"
    description: str = ""
    mass_kg: float | None = None
    power_avg_w: float | None = None
    power_peak_w: float | None = None
    volume_cm3: float | None = None
    dimensions_mm: list[float] | None = None
    cost_nre_keur: float | None = None
    cost_recurring_keur: float | None = None
    trl: int | None = None
    manufacturer: str | None = None
    part_number: str | None = None
    kb_component_id: str | None = None
    quantity: int = 1
    redundancy_type: str | None = None
    performance: dict[str, Any] | None = None
    margin_percent: float = 20.0
    owner_position: str | None = None
    in_scope: bool = True
    frozen: bool = False
    diagram_x: float | None = None
    diagram_y: float | None = None


class ElementUpdate(BaseModel):
    version: int  # Required for optimistic locking
    name: str | None = None
    in_scope: bool | None = None
    frozen: bool | None = None
    parent_id: str | None = None
    description: str | None = None
    mass_kg: float | None = None
    power_avg_w: float | None = None
    power_peak_w: float | None = None
    volume_cm3: float | None = None
    cost_nre_keur: float | None = None
    cost_recurring_keur: float | None = None
    trl: int | None = None
    manufacturer: str | None = None
    kb_component_id: str | None = None
    quantity: int | None = None
    performance: dict[str, Any] | None = None
    margin_percent: float | None = None
    diagram_x: float | None = None
    diagram_y: float | None = None
    diagram_collapsed: bool | None = None


class InterfaceCreate(BaseModel):
    name: str = ""
    interface_type: str  # electrical|data|rf|mechanical|thermal|optical
    direction: str = "bidirectional"
    from_element_id: str
    to_element_id: str
    properties: dict[str, Any] | None = None
    diagram_label: str = ""


class BudgetAllocationCreate(BaseModel):
    budget_type: str  # mass|power|cost|data|delta_v|volume
    allocation_value: float
    unit: str = ""
    source: str = "manual"
    rationale: str = ""


# ─── Element CRUD ───

@router.post("/elements/")
async def create_element(body: ElementCreate, study_id: str = Query(...)) -> dict:
    """Create a new design element."""
    el_id = uuid4().hex
    element = {
        "id": el_id,
        "study_id": study_id,
        **body.model_dump(),
        "version": 1,
        "deleted_at": None,
    }

    # Auto-populate from KB if kb_component_id is set
    if body.kb_component_id:
        kb_data = _lookup_kb_component(body.kb_component_id)
        if kb_data:
            for k, v in kb_data.items():
                if element.get(k) is None and v is not None:
                    element[k] = v

    # Write to DB first, then cache
    await db_create_element(element)
    _elements[el_id] = element

    # Broadcast creation via study WebSocket
    from .ws import _broadcast_study
    asyncio.ensure_future(_broadcast_study(study_id, {
        "type": "element_created", "element": element,
    }))

    return element


@router.get("/elements/{element_id}")
async def get_element(element_id: str) -> dict:
    """Get a single design element."""
    el = _elements.get(element_id)
    if not el or el.get("deleted_at"):
        raise HTTPException(404, f"Element {element_id} not found")
    return el


@router.patch("/elements/{element_id}")
async def update_element(element_id: str, body: ElementUpdate) -> dict:
    """Update element with optimistic locking."""
    el = _elements.get(element_id)
    if not el or el.get("deleted_at"):
        raise HTTPException(404, f"Element {element_id} not found")

    # Optimistic lock check
    if el["version"] != body.version:
        raise HTTPException(409, {
            "error": "version_conflict",
            "your_version": body.version,
            "current_version": el["version"],
            "current_state": el,
        })

    # Apply updates
    updates = body.model_dump(exclude_unset=True, exclude={"version"})
    for k, v in updates.items():
        if v is not None:
            el[k] = v
    el["version"] += 1

    # Persist to DB
    await db_update_element(element_id, el)

    # Broadcast update via study WebSocket
    from .ws import _broadcast_study
    asyncio.ensure_future(_broadcast_study(el["study_id"], {
        "type": "element_updated", "element": el,
    }))

    return el


@router.delete("/elements/{element_id}")
async def delete_element(element_id: str) -> dict:
    """Delete a design element and cascade to all children."""
    el = _elements.get(element_id)
    if not el:
        raise HTTPException(404, f"Element {element_id} not found")
    study_id_for_broadcast = el.get("study_id")
    from datetime import datetime, timezone
    deleted_at = datetime.now(timezone.utc).isoformat()

    # Find all children recursively (cascade delete)
    children_to_delete: list[str] = []
    def find_children(parent_id: str) -> None:
        for e in list(_elements.values()):
            if e.get("parent_id") == parent_id and not e.get("deleted_at"):
                children_to_delete.append(e["id"])
                find_children(e["id"])
    find_children(element_id)

    # REMOVE from in-memory dict — not just soft-delete flag
    # This is the critical fix: previously only set deleted_at but left
    # the element in the dict, causing it to reappear on model reload
    del _elements[element_id]
    for child_id in children_to_delete:
        if child_id in _elements:
            del _elements[child_id]

    # Also remove associated interfaces
    iface_ids_to_delete = []
    for iface_id, iface in list(_interfaces.items()):
        if iface.get("from_element_id") == element_id or iface.get("to_element_id") == element_id:
            iface_ids_to_delete.append(iface_id)
        elif iface.get("from_element_id") in children_to_delete or iface.get("to_element_id") in children_to_delete:
            iface_ids_to_delete.append(iface_id)
    for iface_id in iface_ids_to_delete:
        if iface_id in _interfaces:
            del _interfaces[iface_id]

    # Persist to DB (soft-delete for recovery if needed)
    await db_soft_delete_element(element_id, deleted_at)
    for child_id in children_to_delete:
        await db_soft_delete_element(child_id, deleted_at)
    for iface_id in iface_ids_to_delete:
        await db_soft_delete_interface(iface_id, deleted_at)

    result = {"id": element_id, "deleted": True, "children_deleted": len(children_to_delete), "interfaces_deleted": len(iface_ids_to_delete)}

    # Broadcast deletion via study WebSocket
    if study_id_for_broadcast:
        from .ws import _broadcast_study
        asyncio.ensure_future(_broadcast_study(study_id_for_broadcast, {
            "type": "element_deleted",
            "element_id": element_id,
            "children_deleted": children_to_delete,
        }))

    return result


# ─── Tree Traversal ───

@router.get("/studies/{study_id}/elements/tree")
async def get_element_tree(study_id: str) -> list[dict]:
    """Get full element tree for a study."""
    elements = [e for e in _elements.values() if e["study_id"] == study_id and not e.get("deleted_at")]

    # Build tree
    by_id = {e["id"]: {**e, "children": []} for e in elements}
    roots = []
    for e in elements:
        node = by_id[e["id"]]
        parent_id = e.get("parent_id")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("/elements/{element_id}/subtree")
async def get_subtree(element_id: str) -> dict:
    """Get element with all descendants."""
    el = _elements.get(element_id)
    if not el:
        raise HTTPException(404)

    def _build(eid: str) -> dict:
        node = {**_elements[eid], "children": []}
        for e in _elements.values():
            if e.get("parent_id") == eid and not e.get("deleted_at"):
                node["children"].append(_build(e["id"]))
        return node

    return _build(element_id)


@router.get("/studies/{study_id}/elements")
async def list_elements(
    study_id: str,
    element_type: str | None = None,
    domain: str | None = None,
    segment: str | None = None,
) -> list[dict]:
    """List elements with optional filters."""
    results = []
    for e in _elements.values():
        if e["study_id"] != study_id or e.get("deleted_at"):
            continue
        if element_type and e["element_type"] != element_type:
            continue
        if domain and e.get("subsystem_domain") != domain:
            continue
        if segment and e.get("segment") != segment:
            continue
        results.append(e)
    return results


# ─── Budget Computation ───

@router.get("/elements/{element_id}/budget/{budget_type}")
async def compute_budget(element_id: str, budget_type: str) -> dict:
    """Compute budget by summing child elements recursively."""
    el = _elements.get(element_id)
    if not el:
        raise HTTPException(404)

    prop_map = {
        "mass": "mass_kg",
        "power": "power_avg_w",
        "power_peak": "power_peak_w",
        "cost": "cost_recurring_keur",
        "volume": "volume_cm3",
    }
    prop = prop_map.get(budget_type)
    if not prop:
        raise HTTPException(400, f"Unknown budget type: {budget_type}")

    # ── Constellation awareness: walk up the parent chain to find
    #    the highest ancestor with quantity > 1.  When present, budget
    #    values are reported *per spacecraft* so the user sees what one
    #    satellite costs, not the whole constellation total.
    def _find_constellation_qty(eid: str) -> int:
        """Walk up parent_id chain; return the product of all ancestor
        quantities > 1 (constellation multiplier).  Returns 1 when the
        element is not inside a constellation."""
        qty = 1
        cur = _elements.get(eid)
        while cur:
            eq = cur.get("quantity", 1)
            if eq > 1:
                qty *= eq
            pid = cur.get("parent_id")
            cur = _elements.get(pid) if pid else None
        return qty

    constellation_qty = _find_constellation_qty(element_id)
    is_constellation = constellation_qty > 1

    # Find allocation if set
    allocation = None
    for alloc in _budget_allocations:
        if alloc["element_id"] == element_id and alloc["budget_type"] == budget_type:
            allocation = alloc["allocation_value"]
            break

    # Build per-element allocation lookup
    child_allocations: dict[str, float] = {}
    for alloc in _budget_allocations:
        if alloc["budget_type"] == budget_type:
            child_allocations[alloc["element_id"]] = alloc["allocation_value"]

    # Recursive rollup helper: sum leaf (component) values through the tree.
    # Returns the total for ONE spacecraft (divides by the constellation
    # ancestor quantity, not by the child's own quantity).
    def _rollup(eid: str) -> float:
        """Recursively sum property values from leaf elements (components).

        The returned value is the *per-spacecraft* total: leaf values are
        multiplied by their own quantity (units within the subsystem) but
        NOT by any constellation-level quantity from an ancestor.
        """
        total = 0.0
        has_children = False
        for ch in _elements.values():
            if ch.get("parent_id") == eid and not ch.get("deleted_at"):
                has_children = True
                total += _rollup(ch["id"])
        if not has_children:
            # Leaf element — use its direct value * local quantity
            leaf = _elements.get(eid)
            if leaf:
                total = (leaf.get(prop) or 0) * leaf.get("quantity", 1)
        return total

    # Sum children — actuals come from recursive rollup of components
    lines = []
    total_nominal = 0
    for e in _elements.values():
        if e.get("parent_id") == element_id and not e.get("deleted_at"):
            qty = e.get("quantity", 1)

            # For components (leaf), use direct value
            # For systems/subsystems, recursively roll up from their children
            if e.get("element_type") == "component":
                per_unit = e.get(prop) or 0
            else:
                # Recursive rollup from descendants — _rollup already
                # returns per-spacecraft values, so divide by the CHILD's
                # own quantity to get the per-unit value for that child.
                per_unit = _rollup(e["id"]) / qty if qty > 0 else 0

            val_total = per_unit * qty
            margin = e.get("margin_percent", 20) / 100
            val_with_margin = val_total * (1 + margin)
            total_nominal += val_total
            child_alloc = child_allocations.get(e["id"])
            # For allocation: if set on this element, it's the total allocation
            # Per-instance allocation = total allocation / quantity
            alloc_per_unit = round(child_alloc / qty, 3) if child_alloc and qty > 1 else child_alloc
            line: dict[str, Any] = {
                "element_id": e["id"],
                "name": e["name"],
                "per_unit": round(per_unit, 3),
                "nominal": round(val_total, 3),
                "margin_pct": e.get("margin_percent", 20),
                "with_margin": round(val_with_margin, 3),
                "quantity": qty,
                "allocation": child_alloc,
                "allocation_per_unit": alloc_per_unit,
            }
            lines.append(line)

    total_with_margin = sum(l["with_margin"] for l in lines)

    # Allocation is per-spacecraft when inside a constellation
    allocation_per_sc = round(allocation / constellation_qty, 3) if allocation and is_constellation else allocation
    effective_alloc = allocation_per_sc if is_constellation else allocation

    remaining = (effective_alloc - total_with_margin) if effective_alloc else None
    margin_pct = ((effective_alloc - total_with_margin) / effective_alloc * 100) if effective_alloc and effective_alloc > 0 else None
    status = "green" if (margin_pct and margin_pct > 20) else "amber" if (margin_pct and margin_pct > 0) else "red" if margin_pct is not None else "undefined"

    result: dict[str, Any] = {
        "element_id": element_id,
        "element_name": el["name"],
        "budget_type": budget_type,
        "context": "per_spacecraft" if is_constellation else "total",
        "allocation": allocation,
        "unit": prop_map[budget_type].split("_")[-1] if "_" in prop else "",
        "sum_nominal": round(total_nominal, 3),
        "sum_with_margin": round(total_with_margin, 3),
        "remaining": round(remaining, 3) if remaining is not None else None,
        "margin_pct": round(margin_pct, 1) if margin_pct is not None else None,
        "status": status,
        "lines": lines,
    }

    # Add constellation-specific fields when applicable
    if is_constellation:
        result["constellation_quantity"] = constellation_qty
        result["per_spacecraft_nominal"] = round(total_nominal, 3)
        result["per_spacecraft_with_margin"] = round(total_with_margin, 3)
        result["total_nominal"] = round(total_nominal * constellation_qty, 3)
        result["total_with_margin"] = round(total_with_margin * constellation_qty, 3)
        result["allocation_per_spacecraft"] = allocation_per_sc

    return result


@router.post("/elements/{element_id}/allocations")
async def set_allocation(element_id: str, body: BudgetAllocationCreate) -> dict:
    """Set a budget allocation constraint on an element."""
    if element_id not in _elements:
        raise HTTPException(404)
    alloc = {
        "element_id": element_id,
        "study_id": _elements[element_id]["study_id"],
        **body.model_dump(),
    }
    # Replace existing allocation for same type
    _budget_allocations[:] = [a for a in _budget_allocations if not (a["element_id"] == element_id and a["budget_type"] == body.budget_type)]
    _budget_allocations.append(alloc)
    # Persist to DB
    from ..db.element_repo import db_upsert_budget_allocation
    await db_upsert_budget_allocation(alloc)
    return alloc


# ─── Interfaces ───

@router.post("/interfaces/")
async def create_interface(body: InterfaceCreate, study_id: str = Query(...)) -> dict:
    """Create an interface (connection) between two elements."""
    if body.from_element_id not in _elements:
        raise HTTPException(400, f"from_element {body.from_element_id} not found")
    if body.to_element_id not in _elements:
        raise HTTPException(400, f"to_element {body.to_element_id} not found")

    iface_id = uuid4().hex
    iface = {
        "id": iface_id,
        "study_id": study_id,
        **body.model_dump(),
        "status": "defined",
        "criticality": "standard",
        "version": 1,
        "deleted_at": None,
    }
    # Write to DB first, then cache
    await db_create_interface(iface)
    _interfaces[iface_id] = iface
    return iface


@router.get("/elements/{element_id}/interfaces")
async def get_element_interfaces(element_id: str) -> list[dict]:
    """Get all interfaces for an element."""
    return [
        i for i in _interfaces.values()
        if not i.get("deleted_at") and (i["from_element_id"] == element_id or i["to_element_id"] == element_id)
    ]


@router.get("/studies/{study_id}/interfaces")
async def list_interfaces(study_id: str, interface_type: str | None = None) -> list[dict]:
    """List all interfaces for a study."""
    results = []
    for i in _interfaces.values():
        if i["study_id"] != study_id or i.get("deleted_at"):
            continue
        if interface_type and i["interface_type"] != interface_type:
            continue
        results.append(i)
    return results


@router.patch("/interfaces/{interface_id}")
async def update_interface(interface_id: str, body: dict[str, Any]) -> dict:
    """Update interface properties."""
    iface = _interfaces.get(interface_id)
    if not iface or iface.get("deleted_at"):
        raise HTTPException(404)
    for key in ("name", "interface_type", "direction", "properties", "status",
                "criticality", "diagram_label"):
        if key in body:
            if key == "properties" and isinstance(body[key], dict):
                # Merge properties rather than replace
                existing = iface.get("properties") or {}
                if isinstance(existing, dict):
                    existing.update(body[key])
                    iface["properties"] = existing
                else:
                    iface["properties"] = body[key]
            else:
                iface[key] = body[key]
    return iface


@router.delete("/interfaces/{interface_id}")
async def delete_interface(interface_id: str) -> dict:
    """Soft-delete an interface."""
    iface = _interfaces.get(interface_id)
    if not iface:
        raise HTTPException(404)
    from datetime import datetime, timezone
    deleted_at = datetime.now(timezone.utc).isoformat()
    iface["deleted_at"] = deleted_at

    # Persist soft-delete to DB
    await db_soft_delete_interface(interface_id, deleted_at)
    return {"id": interface_id, "deleted": True}


# ─── Modes ───

@router.post("/elements/{mode_id}/activate")
async def activate_element_in_mode(mode_id: str, element_id: str = Query(...), power_w: float | None = None, duty_cycle: float = 100.0) -> dict:
    """Add an element to a mode (mark it as active in that mode)."""
    if mode_id not in _elements:
        raise HTTPException(404, "Mode not found")
    if element_id not in _elements:
        raise HTTPException(404, "Element not found")
    entry = {"mode_id": mode_id, "element_id": element_id, "is_active": True, "power_w_in_mode": power_w, "duty_cycle_percent": duty_cycle}
    _mode_elements.append(entry)
    return entry


@router.get("/elements/{mode_id}/mode-profile")
async def get_mode_profile(mode_id: str) -> dict:
    """Get power/data profile for a mode."""
    members = [m for m in _mode_elements if m["mode_id"] == mode_id and m["is_active"]]
    total_power = 0
    items = []
    for m in members:
        el = _elements.get(m["element_id"])
        if not el:
            continue
        pw = m["power_w_in_mode"] if m["power_w_in_mode"] is not None else (el.get("power_avg_w") or 0)
        dc = m["duty_cycle_percent"] / 100
        total_power += pw * dc
        items.append({"element_id": m["element_id"], "name": el["name"], "power_w": pw, "duty_cycle": dc})
    return {"mode_id": mode_id, "total_power_w": round(total_power, 2), "elements": items}


# ─── KB Lookup Helper ───

def _lookup_kb_component(kb_id: str) -> dict | None:
    """Look up a component from the KB YAML files and return its properties."""
    import yaml
    from pathlib import Path
    kb_dir = Path(__file__).resolve().parents[4] / "spacecdf-kb" / "src" / "spacecdf_kb" / "data" / "components"
    if not kb_dir.exists():
        return None
    for f in kb_dir.glob("*.yaml"):
        try:
            with open(f) as fp:
                data = yaml.safe_load(fp) or {}
            components = data.get("components", [])
            for c in components:
                if isinstance(c, dict) and (c.get("id") == kb_id or c.get("name") == kb_id):
                    return {
                        "mass_kg": c.get("mass_kg"),
                        "power_avg_w": c.get("power_w"),
                        "cost_recurring_keur": c.get("cost_keur"),
                        "trl": c.get("trl"),
                        "manufacturer": c.get("manufacturer"),
                        "part_number": c.get("part_number", c.get("id")),
                        "performance": c.get("performance"),
                    }
        except Exception:
            continue
    return None


# ─── Seed from design result ───

class SeedRequest(BaseModel):
    parameters: dict[str, Any]
    mission_type: str = "earth_observation"
    spacecraft_class: str = "nano"


@router.post("/studies/{study_id}/seed-elements", deprecated=True)
async def seed_elements_from_design(study_id: str, body: SeedRequest) -> dict:
    """DEPRECATED: Element tree is now built explicitly by the user via HierarchicalDesigner.

    Design agents annotate existing elements — they do not create new ones.
    This endpoint is retained for backward compatibility but is a no-op.
    """
    return {"status": "deprecated", "message": "Element tree is built by user, not auto-seeded from design results."}
