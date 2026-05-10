"""Design Element CRUD API — model-centric architecture.

Every block in a diagram is a rich object. This router provides CRUD,
tree traversal, budget computation, and interface management.

Persistence: write-through cache.  In-memory dicts are the primary read
path (fast).  Every mutation is mirrored to the database via element_repo
so data survives restarts.
"""
from __future__ import annotations

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
    diagram_x: float | None = None
    diagram_y: float | None = None


class ElementUpdate(BaseModel):
    version: int  # Required for optimistic locking
    name: str | None = None
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
    return el


@router.delete("/elements/{element_id}")
async def delete_element(element_id: str) -> dict:
    """Soft-delete a design element."""
    el = _elements.get(element_id)
    if not el:
        raise HTTPException(404, f"Element {element_id} not found")
    from datetime import datetime, timezone
    deleted_at = datetime.now(timezone.utc).isoformat()
    el["deleted_at"] = deleted_at

    # Persist soft-delete to DB
    await db_soft_delete_element(element_id, deleted_at)
    return {"id": element_id, "deleted": True}


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

    # Find allocation if set
    allocation = None
    for alloc in _budget_allocations:
        if alloc["element_id"] == element_id and alloc["budget_type"] == budget_type:
            allocation = alloc["allocation_value"]
            break

    # Sum children
    lines = []
    total_nominal = 0
    for e in _elements.values():
        if e.get("parent_id") == element_id and not e.get("deleted_at"):
            val = (e.get(prop) or 0) * (e.get("quantity", 1))
            margin = e.get("margin_percent", 20) / 100
            val_with_margin = val * (1 + margin)
            total_nominal += val
            lines.append({
                "element_id": e["id"],
                "name": e["name"],
                "nominal": round(val, 3),
                "margin_pct": e.get("margin_percent", 20),
                "with_margin": round(val_with_margin, 3),
                "quantity": e.get("quantity", 1),
            })

    total_with_margin = sum(l["with_margin"] for l in lines)
    remaining = (allocation - total_with_margin) if allocation else None
    margin_pct = ((allocation - total_with_margin) / allocation * 100) if allocation and allocation > 0 else None
    status = "green" if (margin_pct and margin_pct > 20) else "amber" if (margin_pct and margin_pct > 0) else "red" if margin_pct is not None else "undefined"

    return {
        "element_id": element_id,
        "element_name": el["name"],
        "budget_type": budget_type,
        "allocation": allocation,
        "unit": prop_map[budget_type].split("_")[-1] if "_" in prop else "",
        "sum_nominal": round(total_nominal, 3),
        "sum_with_margin": round(total_with_margin, 3),
        "remaining": round(remaining, 3) if remaining is not None else None,
        "margin_pct": round(margin_pct, 1) if margin_pct is not None else None,
        "status": status,
        "lines": lines,
    }


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


@router.post("/studies/{study_id}/seed-elements")
async def seed_elements_from_design(study_id: str, body: SeedRequest) -> dict:
    """Seed the element tree from a design run result.

    Creates the initial hierarchy: mission → segments → systems → subsystems.
    Called automatically after the first successful runDesign().
    Idempotent: if elements already exist for this study, returns them without re-creating.
    """
    # Check if already seeded
    existing = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    if existing:
        return {"status": "already_seeded", "element_count": len(existing)}

    from ..services.element_projection import seed_elements_from_design_result
    elements, interfaces = seed_elements_from_design_result(
        study_id=study_id,
        result_params=body.parameters,
        mission_type=body.mission_type,
        spacecraft_class=body.spacecraft_class,
    )

    for el in elements:
        _elements[el["id"]] = el
    for iface in interfaces:
        _interfaces[iface["id"]] = iface

    # Bulk-persist to DB
    await db_bulk_create_elements(elements)
    await db_bulk_create_interfaces(interfaces)

    return {"status": "seeded", "element_count": len(elements), "interface_count": len(interfaces)}
