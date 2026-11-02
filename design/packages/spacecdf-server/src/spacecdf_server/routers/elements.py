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
    db_update_interface,
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
    # SCDF-170 verification fix: settable at create but silently dropped on PATCH before —
    # the physics envelope/box inertia (dimensions) and the FMECA single-point rule
    # (redundancy_type) depend on them.
    dimensions_mm: list[float] | None = None
    redundancy_type: str | None = None
    part_number: str | None = None
    subsystem_domain: str | None = None
    owner_position: str | None = None


class InterfaceCreate(BaseModel):
    name: str = ""
    # Canonical type (spacecdf_common.models.interface_types); old spellings
    # (electrical, propulsion, software, command, signal, ...) are mapped.
    interface_type: str | None = None
    type: str | None = None
    subtype: str | None = None
    direction: str = "bidirectional"
    from_element_id: str
    to_element_id: str
    properties: dict[str, Any] | None = None
    diagram_label: str = ""
    origin: str = "user"            # "user" | "import" | "rule:<id>"
    status: str = "accepted"        # "suggested" | "accepted" | "rejected"
    rationale: dict[str, str] | None = None
    standard_ref: str | None = None
    criticality: str = "standard"


class BudgetAllocationCreate(BaseModel):
    budget_type: str  # mass|power|cost|data|delta_v|volume
    allocation_value: float
    unit: str = ""
    source: str = "manual"
    rationale: str = ""


# Element fields whose change can change the expected links (Nov 2026 proposer)
_LINK_RELEVANT_FIELDS = {"name", "parent_id", "kb_component_id", "subsystem_domain", "power_avg_w",
                         "power_peak_w", "performance", "in_scope", "description"}


async def _auto_propose(study_id: str | None) -> None:
    """Re-run the rule-based link proposer after the tree changed (never raises).

    Set SPACECDF_AUTO_PROPOSE=0 to turn the automatic run off (POST
    /studies/{id}/interfaces/propose still works).
    """
    import os
    if not study_id or os.environ.get("SPACECDF_AUTO_PROPOSE", "1") in ("0", "false", "no"):
        return
    try:
        from .interfaces import run_proposer
        await run_proposer(study_id)
    except Exception:
        logger.exception("automatic interface proposal failed for %s", study_id)


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
    try:
        await _broadcast_study(study_id, {"type": "element_created", "element": element})
    except Exception as exc:
        logger.warning("Broadcast failed: %s", exc)

    await _auto_propose(study_id)
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

    # SCDF-160 §1.5: re-evaluate parameter formulas that depend on this element (never raises)
    from ..services.equations import on_change as _equations_on_change
    await _equations_on_change(el["study_id"], [element_id])

    # Broadcast update via study WebSocket
    from .ws import _broadcast_study
    try:
        await _broadcast_study(el["study_id"], {"type": "element_updated", "element": el})
    except Exception as exc:
        logger.warning("Broadcast failed: %s", exc)

    if set(updates) & _LINK_RELEVANT_FIELDS:
        await _auto_propose(el["study_id"])
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
        await _broadcast_interface(study_id_for_broadcast, {"type": "interface_deleted", "id": iface_id})

    result = {"id": element_id, "deleted": True, "children_deleted": len(children_to_delete), "interfaces_deleted": len(iface_ids_to_delete)}

    # Broadcast deletion via study WebSocket
    if study_id_for_broadcast:
        from .ws import _broadcast_study
        try:
            await _broadcast_study(study_id_for_broadcast, {
                "type": "element_deleted", "element_id": element_id,
                "children_deleted": children_to_delete,
            })
        except Exception as exc:
            logger.warning("Broadcast failed: %s", exc)
        await _auto_propose(study_id_for_broadcast)

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
        "data": "_data",  # sentinel — handled specially below
    }
    prop = prop_map.get(budget_type)
    if not prop:
        raise HTTPException(400, f"Unknown budget type: {budget_type}")

    is_power_budget = budget_type == "power"
    is_data_budget = budget_type == "data"

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

    # ── Power-specific rollup: returns (avg_total, peak_total) tuples ──
    def _rollup_power(eid: str) -> tuple[float, float]:
        """Recursively sum power values from leaf elements.
        Returns (average_power, peak_power) per-spacecraft."""
        avg_total = 0.0
        peak_total = 0.0
        has_children = False
        for ch in _elements.values():
            if ch.get("parent_id") == eid and not ch.get("deleted_at"):
                has_children = True
                a, p = _rollup_power(ch["id"])
                avg_total += a
                peak_total += p
        if not has_children:
            leaf = _elements.get(eid)
            if leaf:
                qty = leaf.get("quantity", 1)
                perf = leaf.get("performance") or {}
                duty_cycle = perf.get("duty_cycle", 1.0)
                power_avg = leaf.get("power_avg_w") or 0
                power_peak = leaf.get("power_peak_w") or power_avg
                avg_total = power_avg * duty_cycle * qty
                peak_total = power_peak * qty
        return avg_total, peak_total

    # ── Data-specific rollup: returns (data_rate_mbps, volume_gb_per_day) tuples ──
    def _rollup_data(eid: str) -> tuple[float, float]:
        """Recursively sum data values from leaf elements.
        Returns (data_rate_mbps, data_volume_gb_per_day) per-spacecraft."""
        rate_total = 0.0
        vol_total = 0.0
        has_children = False
        for ch in _elements.values():
            if ch.get("parent_id") == eid and not ch.get("deleted_at"):
                has_children = True
                r, v = _rollup_data(ch["id"])
                rate_total += r
                vol_total += v
        if not has_children:
            leaf = _elements.get(eid)
            if leaf:
                qty = leaf.get("quantity", 1)
                perf = leaf.get("performance") or {}
                duty_cycle = perf.get("duty_cycle", 1.0)
                data_rate = perf.get("data_rate_mbps") or 0
                data_vol = perf.get("data_volume_gb_per_day") or 0
                rate_total = data_rate * duty_cycle * qty
                vol_total = data_vol * qty
        return rate_total, vol_total

    # Sum children — actuals come from recursive rollup of components
    lines = []
    total_nominal = 0
    # Power budget extra totals
    total_avg_power = 0.0
    total_peak_power = 0.0
    # Data budget extra totals
    total_data_rate = 0.0
    total_data_volume = 0.0

    for e in _elements.values():
        if e.get("parent_id") == element_id and not e.get("deleted_at"):
            qty = e.get("quantity", 1)
            perf = e.get("performance") or {}
            duty_cycle = perf.get("duty_cycle", 1.0)

            if is_power_budget:
                # ── Power budget: compute avg and peak separately ──
                if e.get("element_type") == "component":
                    power_avg = e.get("power_avg_w") or 0
                    power_peak = e.get("power_peak_w") or power_avg
                    avg_per_unit = power_avg * duty_cycle
                    peak_per_unit = power_peak
                else:
                    a, p = _rollup_power(e["id"])
                    avg_per_unit = a / qty if qty > 0 else 0
                    peak_per_unit = p / qty if qty > 0 else 0

                avg_total = avg_per_unit * qty
                peak_total = peak_per_unit * qty
                # "nominal" for power budget = average power (duty-cycle-aware)
                per_unit = avg_per_unit
                val_total = avg_total
                total_avg_power += avg_total
                total_peak_power += peak_total

            elif is_data_budget:
                # ── Data budget: data rates and volumes ──
                if e.get("element_type") == "component":
                    data_rate = perf.get("data_rate_mbps") or 0
                    data_vol = perf.get("data_volume_gb_per_day") or 0
                    rate_per_unit = data_rate * duty_cycle
                    vol_per_unit = data_vol
                else:
                    r, v = _rollup_data(e["id"])
                    rate_per_unit = r / qty if qty > 0 else 0
                    vol_per_unit = v / qty if qty > 0 else 0

                rate_total = rate_per_unit * qty
                vol_total_val = vol_per_unit * qty
                # "nominal" for data budget = data rate (Mbps)
                per_unit = rate_per_unit
                val_total = rate_total
                total_data_rate += rate_total
                total_data_volume += vol_total_val

            else:
                # ── Standard budget (mass, cost, volume) ──
                if e.get("element_type") == "component":
                    per_unit = e.get(prop) or 0
                else:
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

            # Add power-specific fields
            if is_power_budget:
                line["power_avg_w"] = round(avg_total, 3)
                line["power_peak_w"] = round(peak_total, 3)
                line["duty_cycle"] = duty_cycle

            # Add data-specific fields
            if is_data_budget:
                line["data_rate_mbps"] = round(rate_total, 3)
                line["data_volume_gb_per_day"] = round(vol_total_val, 3)
                line["duty_cycle"] = duty_cycle
                # Volume per orbit (assume ~95 min LEO orbit)
                # rate_total already includes duty_cycle from rollup, so no extra multiply
                orbit_period_min = 95.0
                volume_per_orbit_mb = (rate_total * orbit_period_min * 60) / 8  # Mbps * seconds / 8 = MB
                line["volume_per_orbit_mb"] = round(volume_per_orbit_mb, 3)

            lines.append(line)

    total_with_margin = sum(l["with_margin"] for l in lines)

    # Allocation is per-spacecraft when inside a constellation
    allocation_per_sc = round(allocation / constellation_qty, 3) if allocation and is_constellation else allocation
    effective_alloc = allocation_per_sc if is_constellation else allocation

    remaining = (effective_alloc - total_with_margin) if effective_alloc else None
    margin_pct = ((effective_alloc - total_with_margin) / effective_alloc * 100) if effective_alloc and effective_alloc > 0 else None
    status = "green" if (margin_pct and margin_pct > 20) else "amber" if (margin_pct and margin_pct > 0) else "red" if margin_pct is not None else "undefined"

    # Determine unit label
    if is_data_budget:
        unit_label = "Mbps"
    elif "_" in prop:
        unit_label = prop_map[budget_type].split("_")[-1]
    else:
        unit_label = ""

    result: dict[str, Any] = {
        "element_id": element_id,
        "element_name": el["name"],
        "budget_type": budget_type,
        "context": "per_spacecraft" if is_constellation else "total",
        "allocation": allocation,
        "unit": unit_label,
        "sum_nominal": round(total_nominal, 3),
        "sum_with_margin": round(total_with_margin, 3),
        "remaining": round(remaining, 3) if remaining is not None else None,
        "margin_pct": round(margin_pct, 1) if margin_pct is not None else None,
        "status": status,
        "lines": lines,
    }

    # Add power-specific summary fields
    if is_power_budget:
        result["total_avg_power"] = round(total_avg_power, 3)
        result["total_peak_power"] = round(total_peak_power, 3)

    # Add data-specific summary fields
    if is_data_budget:
        result["total_data_rate_mbps"] = round(total_data_rate, 3)
        result["total_data_volume_gb_per_day"] = round(total_data_volume, 3)

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


@router.get("/studies/{study_id}/allocations")
async def list_allocations(study_id: str) -> list[dict]:
    """List all budget allocations for a study."""
    return [a for a in _budget_allocations if a.get("study_id") == study_id]


# ─── Interfaces ───
#
# Nov 2026 contract: every interface carries a canonical ``type`` (also stored as
# ``interface_type``), ``subtype``, ``properties``, ``origin`` ("user" | "import" |
# "rule:<id>"), ``status`` ("suggested" | "accepted" | "rejected"), ``rationale``
# {en, fr} and ``standard_ref``. Every create/update/delete is written through to
# the database and broadcast on the study WebSocket as
# ``{type: "interface_changed", interface}`` / ``{type: "interface_deleted", id}``.

def _canonical_type_or_400(raw: Any) -> str:
    from spacecdf_common.models.interface_types import INTERFACE_TYPE_VALUES, canonical_interface_type
    canon = canonical_interface_type(raw)
    if not canon:
        raise HTTPException(400, f"interface type must be one of {INTERFACE_TYPE_VALUES} (got {raw!r})")
    return canon


def _status_or_400(raw: Any) -> str:
    from spacecdf_common.models.interface_types import INTERFACE_STATUSES
    if raw not in INTERFACE_STATUSES:
        raise HTTPException(400, f"status must be one of {INTERFACE_STATUSES} (got {raw!r})")
    return raw


async def _broadcast_interface(study_id: str | None, message: dict) -> None:
    if not study_id:
        return
    from .ws import _broadcast_study
    try:
        await _broadcast_study(study_id, message)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Broadcast failed: %s", exc)


def active_interfaces(study_id: str) -> list[dict]:
    """Interfaces that count in analyses, exports and budgets: not deleted, not rejected."""
    from ..services.interface_model import is_active
    return [i for i in _interfaces.values() if i.get("study_id") == study_id and is_active(i)]


async def store_interface(iface: dict, *, broadcast: bool = True) -> dict:
    """Normalise, persist, cache and announce a NEW interface (used by REST, WebSocket and the proposer)."""
    from ..services.interface_model import normalise_interface
    iface.setdefault("id", uuid4().hex)
    iface.setdefault("version", 1)
    iface.setdefault("deleted_at", None)
    normalise_interface(iface)
    await db_create_interface(iface)
    _interfaces[iface["id"]] = iface
    if broadcast:
        await _broadcast_interface(iface.get("study_id"), {"type": "interface_changed", "interface": iface})
    return iface


async def save_interface(iface: dict, *, broadcast: bool = True) -> dict:
    """Write an EXISTING interface through to the DB (version bump) and announce it."""
    iface["version"] = int(iface.get("version") or 1) + 1
    await db_update_interface(iface["id"], iface)
    if broadcast:
        await _broadcast_interface(iface.get("study_id"), {"type": "interface_changed", "interface": iface})
    return iface


async def remove_interface(iface: dict, *, broadcast: bool = True) -> None:
    from datetime import datetime, timezone
    deleted_at = datetime.now(timezone.utc).isoformat()
    iface["deleted_at"] = deleted_at
    await db_soft_delete_interface(iface["id"], deleted_at)
    if broadcast:
        await _broadcast_interface(iface.get("study_id"), {"type": "interface_deleted", "id": iface["id"]})


@router.post("/interfaces/")
async def create_interface(body: InterfaceCreate, study_id: str = Query(...)) -> dict:
    """Create an interface (connection) between two elements."""
    from ..services.interface_model import valid_origin
    if body.from_element_id not in _elements:
        raise HTTPException(400, f"from_element {body.from_element_id} not found")
    if body.to_element_id not in _elements:
        raise HTTPException(400, f"to_element {body.to_element_id} not found")
    itype = _canonical_type_or_400(body.type or body.interface_type)
    status = _status_or_400(body.status)
    if not valid_origin(body.origin):
        raise HTTPException(400, "origin must be 'user', 'import' or 'rule:<rule_id>'")
    data = body.model_dump(exclude={"type"})
    iface = {
        "id": uuid4().hex,
        "study_id": study_id,
        **data,
        "interface_type": itype,
        "status": status,
        "version": 1,
        "deleted_at": None,
    }
    return await store_interface(iface)


@router.get("/elements/{element_id}/interfaces")
async def get_element_interfaces(element_id: str) -> list[dict]:
    """Get all interfaces for an element."""
    return [
        i for i in _interfaces.values()
        if not i.get("deleted_at") and (i["from_element_id"] == element_id or i["to_element_id"] == element_id)
    ]


@router.get("/studies/{study_id}/interfaces")
async def list_interfaces(study_id: str, interface_type: str | None = None, type: str | None = None,
                          status: str | None = None) -> list[dict]:
    """List all interfaces for a study (rejected ones included; filter with ``status``)."""
    want = None
    if interface_type or type:
        want = _canonical_type_or_400(type or interface_type)
    results = []
    for i in _interfaces.values():
        if i["study_id"] != study_id or i.get("deleted_at"):
            continue
        if want and i["interface_type"] != want:
            continue
        if status and i.get("status") != status:
            continue
        results.append(i)
    return results


_EDIT_FIELDS = ("name", "interface_type", "subtype", "direction", "properties",
                "from_element_id", "to_element_id")


async def _patch_interface(iface: dict, body: dict[str, Any]) -> dict:
    if "version" in body and body["version"] is not None and int(body["version"]) != int(iface.get("version") or 1):
        raise HTTPException(409, {"error": "version_conflict", "your_version": body["version"],
                                  "current_version": iface.get("version"), "current_state": iface})
    body = dict(body)
    if "type" in body:
        body["interface_type"] = body.pop("type")
    if "interface_type" in body:
        body["interface_type"] = _canonical_type_or_400(body["interface_type"])
    if "status" in body:
        _status_or_400(body["status"])
    for end in ("from_element_id", "to_element_id"):
        if end in body and body[end] not in _elements:
            raise HTTPException(400, f"{end} {body[end]} not found")
    if "origin" in body:
        from ..services.interface_model import valid_origin
        if not valid_origin(body["origin"]):
            raise HTTPException(400, "origin must be 'user', 'import' or 'rule:<rule_id>'")

    edited = False
    for key in ("name", "interface_type", "subtype", "direction", "properties", "status", "criticality",
                "diagram_label", "from_element_id", "to_element_id", "rationale", "standard_ref", "origin"):
        if key not in body:
            continue
        val = body[key]
        if key == "properties":
            if not isinstance(val, dict):
                raise HTTPException(400, "properties must be an object")
            # Merge; a key sent as null is removed
            merged = dict(iface.get("properties") or {})
            for k, v in val.items():
                if v is None:
                    merged.pop(k, None)
                else:
                    merged[k] = v
            if merged != (iface.get("properties") or {}):
                edited = True
            iface["properties"] = merged
            continue
        if key in _EDIT_FIELDS and iface.get(key) != val:
            edited = True
        iface[key] = val
    iface["type"] = iface["interface_type"]

    # A user edit of a rule-made link makes it the user's: origin=user, accepted,
    # never touched again by the proposer.
    if edited and str(iface.get("origin") or "").startswith("rule:") and "origin" not in body:
        iface["origin"] = "user"
        if body.get("status") in (None, "suggested"):
            iface["status"] = "accepted"
    return await save_interface(iface)


@router.patch("/interfaces/{interface_id}")
async def update_interface(interface_id: str, body: dict[str, Any]) -> dict:
    """Update an interface: status (accept/reject/restore), type, subtype, properties, endpoints.

    Persisted (write-through) and broadcast as ``interface_changed``.
    """
    iface = _interfaces.get(interface_id)
    if not iface or iface.get("deleted_at"):
        raise HTTPException(404)
    return await _patch_interface(iface, body)


@router.patch("/studies/{study_id}/interfaces/{interface_id}")
async def update_study_interface(study_id: str, interface_id: str, body: dict[str, Any]) -> dict:
    iface = _interfaces.get(interface_id)
    if not iface or iface.get("deleted_at") or iface.get("study_id") != study_id:
        raise HTTPException(404)
    return await _patch_interface(iface, body)


@router.delete("/interfaces/{interface_id}")
async def delete_interface(interface_id: str) -> dict:
    """Soft-delete an interface (broadcast ``interface_deleted``).

    To dismiss a rule suggestion use PATCH status=rejected instead: a deleted
    suggestion is proposed again on the next run, a rejected one is not.
    """
    iface = _interfaces.get(interface_id)
    if not iface:
        raise HTTPException(404)
    await remove_interface(iface)
    return {"id": interface_id, "deleted": True}


@router.delete("/studies/{study_id}/interfaces/{interface_id}")
async def delete_study_interface(study_id: str, interface_id: str) -> dict:
    iface = _interfaces.get(interface_id)
    if not iface or iface.get("study_id") != study_id:
        raise HTTPException(404)
    await remove_interface(iface)
    return {"id": interface_id, "deleted": True}


# ─── Exchange items on interfaces (SCDF-160 §1.2; used by routers/exchange_items.py) ───

async def set_interface_exchange_items(interface_id: str, exchange_item_ids: list[str]) -> dict:
    """Replace the exchange-item list of an interface, write-through to DB.

    Kept here so the interface cache stays the single source for readers.
    Raises ``KeyError`` when the interface is unknown or deleted.
    """
    iface = _interfaces.get(interface_id)
    if not iface or iface.get("deleted_at"):
        raise KeyError(interface_id)
    ids = list(dict.fromkeys(exchange_item_ids))
    iface["exchange_item_ids_json"] = ids
    iface["exchange_item_ids"] = ids
    iface["version"] = int(iface.get("version") or 1) + 1
    await db_update_interface(interface_id, iface)
    return iface


# ─── Modes ───

@router.post("/elements/{mode_id}/activate")
async def activate_element_in_mode(mode_id: str, element_id: str = Query(...), power_w: float | None = None, duty_cycle: float = 100.0) -> dict:
    """Add an element to a mode (mark it as active in that mode)."""
    if mode_id not in _elements:
        raise HTTPException(404, "Mode not found")
    if element_id not in _elements:
        raise HTTPException(404, "Element not found")
    entry = {"mode_id": mode_id, "element_id": element_id, "is_active": True, "power_w_in_mode": power_w, "duty_cycle_percent": duty_cycle}
    _mode_elements[:] = [m for m in _mode_elements if not (m["mode_id"] == mode_id and m["element_id"] == element_id)]
    _mode_elements.append(entry)
    # SCDF-170 verification fix: persist the membership (the analysis context reads
    # ``mode_elements`` rows; before, a restart emptied every mode -> 0 W in the simulation)
    await _db_upsert_mode_member(entry)
    return entry


async def _db_upsert_mode_member(entry: dict) -> None:
    try:
        from sqlalchemy import select
        from ..db.engine import get_session_factory
        from ..db.models import ModeElementRow
        async with get_session_factory()() as session:
            res = await session.execute(select(ModeElementRow).where(
                ModeElementRow.mode_id == entry["mode_id"], ModeElementRow.element_id == entry["element_id"]))
            row = res.scalars().first()
            if row is None:
                row = ModeElementRow(mode_id=entry["mode_id"], element_id=entry["element_id"])
                session.add(row)
            row.is_active = bool(entry.get("is_active", True))
            row.power_w_in_mode = entry.get("power_w_in_mode")
            row.duty_cycle_percent = float(entry.get("duty_cycle_percent") or 100.0)
            await session.commit()
    except Exception:
        logger.exception("mode_elements persist failed for mode %s", entry.get("mode_id"))


async def _db_load_mode_members(mode_id: str) -> list[dict]:
    try:
        from sqlalchemy import select
        from ..db.engine import get_session_factory
        from ..db.models import ModeElementRow
        async with get_session_factory()() as session:
            res = await session.execute(select(ModeElementRow).where(ModeElementRow.mode_id == mode_id))
            return [{"mode_id": r.mode_id, "element_id": r.element_id, "is_active": bool(r.is_active),
                     "power_w_in_mode": r.power_w_in_mode, "duty_cycle_percent": r.duty_cycle_percent}
                    for r in res.scalars()]
    except Exception:
        logger.debug("mode_elements table unavailable", exc_info=True)
        return []


@router.get("/elements/{mode_id}/mode-profile")
async def get_mode_profile(mode_id: str) -> dict:
    """Get power/data profile for a mode."""
    members = [m for m in _mode_elements if m["mode_id"] == mode_id and m["is_active"]]
    if not members:
        members = [m for m in await _db_load_mode_members(mode_id) if m["is_active"]]
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
                        "name": c.get("name"),
                        "mass_kg": c.get("mass_kg"),
                        "power_avg_w": c.get("power_w") or c.get("power_avg_w"),
                        "cost_recurring_keur": c.get("cost_keur"),
                        "trl": c.get("trl"),
                        "manufacturer": c.get("manufacturer"),
                        "part_number": c.get("part_number", c.get("id")),
                        "performance": c.get("performance"),
                        "category": c.get("category"),
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


# ─── Populate subsystem tree with recommended equipment ───

class PopulateRequest(BaseModel):
    """Request to auto-populate a segment with subsystems and initial equipment."""
    spacecraft_class: str = "nano"  # nano|micro|small|medium|large
    include_equipment: bool = True  # Also add recommended components from KB


# Standard subsystems per spacecraft class
_SUBSYSTEM_TEMPLATES: dict[str, list[dict]] = {
    "space": [
        {"name": "Payload", "domain": "payload"},
        {"name": "EPS", "domain": "power"},
        {"name": "AOCS", "domain": "aocs"},
        {"name": "Communications", "domain": "ttc"},
        {"name": "On-Board Computer", "domain": "obc"},
        {"name": "Thermal", "domain": "thermal"},
        {"name": "Structure", "domain": "structure"},
        {"name": "Propulsion", "domain": "propulsion"},
    ],
    "ground": [
        {"name": "Ground Station Antenna System", "domain": "ground_rf"},
        {"name": "Ground Station Electronics", "domain": "ground_rf"},
        {"name": "Mission Control Centre", "domain": "ground_ops"},
        {"name": "Ground Network & Communications", "domain": "ground_ops"},
    ],
}

# Default equipment per subsystem domain for CubeSat-class missions
_DEFAULT_EQUIPMENT: dict[str, list[str]] = {
    "power": ["bat-gom-nanopow-bpx", "eps-gom-nanopow-p60", "sp-gom-nanopow-p110"],
    "aocs": ["rw-cubew-medium", "st-cubespace-cubestar", "ss-nss-css-01", "mtq-isis-imtq"],
    "ttc": ["txr-endurosat-uhf-ii", "ant-endurosat-uhf-dipole"],
    "obc": ["obc-gom-nanomind-a3200"],
    "thermal": [],  # Thermal hardware depends heavily on the mission
    "structure": [],  # Structure is mission-specific
    "propulsion": [],  # Not all missions need propulsion
}

# Default equipment for ground segment
_DEFAULT_GROUND_EQUIPMENT: dict[str, list[str]] = {
    "ground_rf": ["gs-ant-uhf-crossyagi", "gs-rf-lna-uhf", "gs-bb-gnuradio-sdr"],
    "ground_ops": ["gs-sw-openc3", "gs-time-gpsdo"],
}

# SCDF-170 N1: class heritage (mass_kg, power_avg_w) per subsystem domain, used
# when a subsystem has no equipment to roll up. Order of magnitude values from
# CubeSat / SmallSat heritage (3U, ~50 kg, ~200 kg, ~800 kg, ~2.5 t buses).
_CLASS_HERITAGE_DEFAULTS: dict[str, dict[str, tuple[float, float]]] = {
    "nano":   {"payload": (1.0, 3.0), "power": (0.6, 0.5), "aocs": (0.5, 1.5), "ttc": (0.3, 2.0),
               "obc": (0.15, 0.5), "thermal": (0.1, 0.5), "structure": (0.8, 0.0), "propulsion": (0.5, 1.0)},
    "micro":  {"payload": (10.0, 20.0), "power": (6.0, 2.0), "aocs": (5.0, 8.0), "ttc": (3.0, 10.0),
               "obc": (2.0, 5.0), "thermal": (2.0, 5.0), "structure": (8.0, 0.0), "propulsion": (6.0, 5.0)},
    "small":  {"payload": (40.0, 60.0), "power": (25.0, 5.0), "aocs": (20.0, 25.0), "ttc": (10.0, 20.0),
               "obc": (6.0, 10.0), "thermal": (8.0, 15.0), "structure": (35.0, 0.0), "propulsion": (25.0, 10.0)},
    "medium": {"payload": (150.0, 200.0), "power": (90.0, 10.0), "aocs": (70.0, 60.0), "ttc": (30.0, 50.0),
               "obc": (15.0, 20.0), "thermal": (30.0, 40.0), "structure": (130.0, 0.0), "propulsion": (90.0, 20.0)},
    "large":  {"payload": (500.0, 600.0), "power": (280.0, 20.0), "aocs": (200.0, 150.0), "ttc": (80.0, 120.0),
               "obc": (40.0, 40.0), "thermal": (90.0, 100.0), "structure": (400.0, 0.0), "propulsion": (300.0, 40.0)},
}
_GROUND_HERITAGE_DEFAULTS: dict[str, tuple[float, float]] = {"ground_rf": (50.0, 500.0), "ground_ops": (0.0, 200.0)}

# SCDF-170 N3 → Nov 2026: the default interface set is no longer hard-coded here;
# populate-subsystems calls the rule-based proposer (services/interface_proposer.py,
# configs/interface_rules.yaml).


def _heritage_default(spacecraft_class: str, domain: str) -> tuple[float, float]:
    if domain in _GROUND_HERITAGE_DEFAULTS:
        return _GROUND_HERITAGE_DEFAULTS[domain]
    table = _CLASS_HERITAGE_DEFAULTS.get(spacecraft_class) or _CLASS_HERITAGE_DEFAULTS["nano"]
    return table.get(domain, (0.0, 0.0))


async def _roll_up_subsystems(subsystem_ids: dict[str, str], spacecraft_class: str) -> list[str]:
    """N1: give every subsystem a numeric ``mass_kg`` / ``power_avg_w``
    (sum of live children × quantity, else the class heritage default).
    Only ``None`` columns are filled; returns the ids that were updated."""
    updated: list[str] = []
    for domain, sid in subsystem_ids.items():
        sub = _elements.get(sid)
        if not sub or sub.get("deleted_at"):
            continue
        children = [e for e in _elements.values() if e.get("parent_id") == sid and not e.get("deleted_at")]
        default_mass, default_power = _heritage_default(spacecraft_class, domain)
        changed = False
        for col, default in (("mass_kg", default_mass), ("power_avg_w", default_power)):
            if sub.get(col) is not None:
                continue
            if children:
                sub[col] = round(sum((c.get(col) or 0.0) * (c.get("quantity") or 1) for c in children), 4)
            else:
                sub[col] = default
            changed = True
        if changed:
            sub["version"] = int(sub.get("version") or 1) + 1
            await db_update_element(sid, sub)
            updated.append(sid)
    return updated


@router.post("/studies/{study_id}/populate-subsystems")
async def populate_subsystems(
    study_id: str,
    parent_element_id: str = Query(..., description="ID of the segment to populate"),
    body: PopulateRequest = PopulateRequest(),
) -> dict:
    """Auto-populate a segment element with standard subsystems and initial equipment.

    Creates:
    1. A system element (e.g. "Spacecraft") under the segment
    2. Standard subsystem elements under the system
    3. Optionally, recommended equipment from the KB under each subsystem

    This bridges the gap between "I have a mission concept" and "I have
    equipment in the tree that drives budgets".

    SCDF-170 N1/N3: every subsystem ends up with a numeric ``mass_kg`` /
    ``power_avg_w`` (children roll-up or class heritage default, so formulas
    like ``mass_kg * 1.2`` work) and the study gets the expected interfaces
    from the rule-based proposer (``configs/interface_rules.yaml``) as
    *suggested* links with exchange items, for the user to accept or reject.
    """
    parent = _elements.get(parent_element_id)
    if not parent:
        raise HTTPException(404, "Parent element not found")
    if parent["study_id"] != study_id:
        raise HTTPException(400, "Element does not belong to this study")

    segment = parent.get("segment", "space")
    subsystem_defs = _SUBSYSTEM_TEMPLATES.get(segment, _SUBSYSTEM_TEMPLATES["space"])

    created_elements: list[dict] = []

    # Check if there's already a system under this segment
    existing_children = [
        e for e in _elements.values()
        if e.get("parent_id") == parent_element_id
        and not e.get("deleted_at")
    ]

    # Create system element if none exists
    system_id = None
    if not any(c.get("element_type") == "system" for c in existing_children):
        system_name = "Spacecraft" if segment == "space" else f"{segment.title()} System"
        system_el = {
            "id": uuid4().hex,
            "study_id": study_id,
            "name": system_name,
            "element_type": "system",
            "parent_id": parent_element_id,
            "segment": segment,
            "version": 1,
            "deleted_at": None,
            "margin_percent": 20.0,
            "quantity": parent.get("quantity", 1),
            # remembered so later proposer runs use the same class defaults (rails, bus, band)
            "performance": {"spacecraft_class": body.spacecraft_class} if segment == "space" else None,
        }
        await db_create_element(system_el)
        _elements[system_el["id"]] = system_el
        created_elements.append(system_el)
        system_id = system_el["id"]
    else:
        system_id = next(c["id"] for c in existing_children if c.get("element_type") == "system")
        sys_el = _elements[system_id]
        if segment == "space" and not (sys_el.get("performance") or {}).get("spacecraft_class"):
            sys_el["performance"] = {**(sys_el.get("performance") or {}), "spacecraft_class": body.spacecraft_class}
            await db_update_element(system_id, sys_el)

    # Create subsystems
    subsystem_ids: dict[str, str] = {}
    existing_subsystems = [
        e for e in _elements.values()
        if e.get("parent_id") == system_id
        and not e.get("deleted_at")
        and e.get("element_type") == "subsystem"
    ]
    existing_domains = {e.get("subsystem_domain") for e in existing_subsystems}

    for i, sub_def in enumerate(subsystem_defs):
        if sub_def["domain"] in existing_domains:
            # Already exists — use it
            match = next(e for e in existing_subsystems if e.get("subsystem_domain") == sub_def["domain"])
            subsystem_ids[sub_def["domain"]] = match["id"]
            continue

        sub_el = {
            "id": uuid4().hex,
            "study_id": study_id,
            "name": sub_def["name"],
            "element_type": "subsystem",
            "parent_id": system_id,
            "segment": segment,
            "subsystem_domain": sub_def["domain"],
            "version": 1,
            "deleted_at": None,
            "margin_percent": 20.0,
            "diagram_x": 80 + (i % 4) * 200,
            "diagram_y": 40 + (i // 4) * 140,
        }
        await db_create_element(sub_el)
        _elements[sub_el["id"]] = sub_el
        created_elements.append(sub_el)
        subsystem_ids[sub_def["domain"]] = sub_el["id"]

    # Add default equipment from KB
    equipment_count = 0
    equip_map = (
        _DEFAULT_EQUIPMENT if segment == "space"
        else _DEFAULT_GROUND_EQUIPMENT if segment == "ground"
        else {}
    )
    if body.include_equipment and equip_map:
        for domain, kb_ids in equip_map.items():
            parent_sub_id = subsystem_ids.get(domain)
            if not parent_sub_id or not kb_ids:
                continue

            # Check existing components in this subsystem
            existing_comps = [
                e for e in _elements.values()
                if e.get("parent_id") == parent_sub_id
                and not e.get("deleted_at")
                and e.get("element_type") == "component"
            ]
            if existing_comps:
                continue  # Don't overwrite existing equipment selections

            for kb_id in kb_ids:
                kb_data = _lookup_kb_component(kb_id)
                if not kb_data:
                    continue
                comp_el = {
                    "id": uuid4().hex,
                    "study_id": study_id,
                    "name": kb_data.get("name") or kb_data.get("part_number", kb_id),
                    "element_type": "component",
                    "parent_id": parent_sub_id,
                    "segment": segment,
                    "subsystem_domain": domain,
                    "kb_component_id": kb_id,
                    "mass_kg": kb_data.get("mass_kg"),
                    "power_avg_w": kb_data.get("power_avg_w"),
                    "cost_recurring_keur": kb_data.get("cost_recurring_keur"),
                    "trl": kb_data.get("trl"),
                    "manufacturer": kb_data.get("manufacturer"),
                    "performance": kb_data.get("performance"),
                    "quantity": 1,
                    "version": 1,
                    "deleted_at": None,
                    "margin_percent": 20.0,
                }
                await db_create_element(comp_el)
                _elements[comp_el["id"]] = comp_el
                created_elements.append(comp_el)
                equipment_count += 1

    # N1: roll-up / heritage defaults so every subsystem has numeric mass & power
    rolled_up = await _roll_up_subsystems(subsystem_ids, body.spacecraft_class)

    # N3: expected interfaces from the rule set (suggested baseline, with exchange items)
    created_interfaces: list[dict] = []
    proposal: dict = {}
    try:
        from .interfaces import run_proposer
        proposal = await run_proposer(study_id, spacecraft_class=body.spacecraft_class)
        created_interfaces = proposal.get("created", [])
    except Exception:
        logger.exception("populate-subsystems: interface proposal failed for %s", study_id)

    # Broadcast
    from .ws import _broadcast_study
    try:
        await _broadcast_study(study_id, {
            "type": "elements_populated",
            "count": len(created_elements),
            "interfaces": len(created_interfaces),
        })
    except Exception:
        pass

    return {
        "created": len(created_elements),
        "system_id": system_id,
        "subsystem_ids": subsystem_ids,
        "equipment_count": equipment_count,
        "rolled_up": rolled_up,
        "interfaces_created": len(created_interfaces),
        "interface_ids": [i["id"] for i in created_interfaces],
        "interfaces_unmet": proposal.get("unmet", []),
        "interface_conflicts": proposal.get("conflicts", []),
        "message": (f"Created {len(created_elements)} elements ({equipment_count} equipment items from KB), "
                    f"{len(created_interfaces)} interfaces"),
    }
