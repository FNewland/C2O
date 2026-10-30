"""Parameters API — typed parameters + equations (SCDF-160 §1.5, §3).

Rows are the truth (``db/parameter_repo``); values are evaluated by
``services/equations`` on every read so ``calc`` formulas are always fresh
and ``ref`` formulas are persisted on write / recompute.

Routes (mounted under ``/api``):
    GET    /parameters/definitions                    ?well_known_only=
    POST   /parameters/definitions/seed               reference data library -> definitions
    GET    /elements/{id}/parameters?option_id=       evaluated view of one element
    PUT    /elements/{id}/parameters/{name}?option_id=  upsert value/formula/switch, then recompute
    DELETE /elements/{id}/parameters/{name}?option_id=  soft delete (well-known rows are reset, not deleted)
    GET    /studies/{id}/parameters?option_id=        flat evaluated list
    POST   /studies/{id}/parameters/recompute?option_id=
    GET    /studies/{id}/parameters/graph             {nodes, edges, cycles}

Option scoping (SCDF-172): ``option_id`` absent or the baseline option's id →
the baseline rows (``option_id IS NULL``). ``option_id=X`` → reads return
baseline ∪ X-overrides (an X row shadows the baseline row of the same
element/parameter, ``option_id`` set on the view); PUT creates/updates the X
row and never the baseline; DELETE removes the X override so the baseline
shows through again (404 if X has no override for that parameter).

Broadcasts (``routers/_arcadia_events.broadcast_mutation``):
    parameter_updated       target_kind='parameter', payload = evaluated parameter (+ option_id)
    parameter_deleted       target_kind='parameter'  (+ option_id)
    parameters_recomputed   target_kind='study',     payload = {persisted, written_back, errors, cycles}
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS

from ..db import option_repo, parameter_repo as repo
from ..services import equations
from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Pydantic models ───

class ParameterUpsert(BaseModel):
    manual_value: float | None = None
    reference_value: float | None = None
    formula: str | None = None
    formula_kind: str | None = None          # ref|calc
    value_switch: str | None = None          # manual|computed|reference
    owner_domain: str | None = None
    # used only when the definition has to be created on the fly
    unit: str | None = None
    quantity_kind: str | None = None
    description: str | None = None


# ─── Helpers ───

async def _element_or_404(element_id: str) -> dict:
    """Element dict from the elements cache, falling back to the DB row."""
    from ..routers import elements as elements_router
    el = elements_router._elements.get(element_id)
    if el and not el.get("deleted_at"):
        return el
    from ..db.engine import get_session_factory
    from ..db.models import DesignElementRow
    factory = get_session_factory()
    async with factory() as session:
        row = await session.get(DesignElementRow, element_id)
        if row is None or row.deleted_at is not None:
            raise HTTPException(404, f"Element {element_id} not found")
        return {c.key: getattr(row, c.key) for c in DesignElementRow.__table__.columns}


async def _evaluated_param(element_id: str, name: str, option_id: str | None = None) -> dict | None:
    res = await equations.evaluate_element(element_id, option_id)
    return next((p for p in res["parameters"] if p["name"] == name), None)


async def _recompute_and_broadcast(study_id: str, changed: list[str], option_id: str | None = None) -> dict:
    await equations.on_change(study_id, changed, option_id)
    result = await equations.evaluate_study(study_id, option_id)
    await broadcast_mutation(study_id, "parameters_recomputed", "study", study_id, {
        "errors": result.get("errors", []), "cycles": result.get("cycles", []), "option_id": option_id,
    })
    return result


async def _scoped_option(option_id: str | None) -> str | None:
    """``?option_id=`` → the id the parameter layer uses (baseline → None); 404 if unknown."""
    try:
        return await option_repo.resolve_option_id(option_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


# ─── Definitions ───

@router.get("/parameters/definitions")
async def list_definitions(well_known_only: bool = Query(False)) -> list[dict]:
    return await repo.list_parameter_definitions(well_known_only=well_known_only)


@router.post("/parameters/definitions/seed")
async def seed_definitions() -> dict:
    counts = await repo.seed_parameter_definitions()
    counts["total"] = len(await repo.list_parameter_definitions())
    return counts


# ─── Element parameters ───

@router.get("/elements/{element_id}/parameters")
async def get_element_parameters(element_id: str, option_id: str | None = Query(None)) -> list[dict]:
    await _element_or_404(element_id)
    option_id = await _scoped_option(option_id)
    res = await equations.evaluate_element(element_id, option_id)
    return res["parameters"]


@router.put("/elements/{element_id}/parameters/{name}")
async def put_element_parameter(element_id: str, name: str, body: ParameterUpsert,
                                option_id: str | None = Query(None)) -> dict:
    el = await _element_or_404(element_id)
    study_id = el["study_id"]
    option_id = await _scoped_option(option_id)
    if body.value_switch is not None and body.value_switch not in repo.VALUE_SWITCHES:
        raise HTTPException(400, f"value_switch must be one of {repo.VALUE_SWITCHES}")
    if body.formula_kind is not None and body.formula_kind not in repo.FORMULA_KINDS:
        raise HTTPException(400, f"formula_kind must be one of {repo.FORMULA_KINDS}")
    formula = (body.formula or "").strip() or None
    if formula:
        parsed = equations.parse_dependencies(formula)
        if parsed.errors:
            raise HTTPException(400, {"error": "invalid_formula", "details": parsed.errors})

    # Definition: reuse or create on the fly
    defn = await repo.get_parameter_definition_by_name(name)
    if defn is None:
        defn = await repo.upsert_parameter_definition({
            "name": name, "unit": body.unit or "", "quantity_kind": body.quantity_kind or "",
            "description": body.description or "", "is_well_known": name in WELL_KNOWN_PARAMETERS,
        })

    sent = body.model_dump(exclude_unset=True)
    updates: dict[str, Any] = {
        "study_id": study_id, "element_id": element_id, "definition_id": defn["id"],
        "option_id": option_id,
    }
    for key in ("manual_value", "reference_value", "value_switch", "owner_domain"):
        if key in sent:
            updates[key] = sent[key]
    if "formula" in sent:
        updates["formula"] = formula
        updates["formula_kind"] = (body.formula_kind or "ref") if formula else None
    elif "formula_kind" in sent:
        updates["formula_kind"] = body.formula_kind
    if "manual_value" in sent and body.manual_value is not None and "value_switch" not in sent:
        # Setting a manual value without saying which switch to use means "use it".
        updates["value_switch"] = "manual"
    if "value_switch" not in updates and updates.get("owner_domain") is None and "owner_domain" not in sent:
        updates.setdefault("owner_domain", el.get("subsystem_domain"))
    if name in WELL_KNOWN_PARAMETERS and el.get(name) is not None:
        updates.setdefault("computed_value", float(el[name]))
    if option_id is not None:
        # A fresh override row starts from the baseline row it shadows, so a
        # PUT that only flips the switch / sets a formula keeps the other fields.
        rows = await repo.list_element_parameters_by_element(element_id, iteration=1, option_id=option_id)
        base = next((r for r in rows if r["definition_id"] == defn["id"]), None)
        if base is not None and (base.get("option_id") or None) != option_id:
            for key in ("manual_value", "reference_value", "computed_value", "formula", "formula_kind",
                        "value_switch", "owner_domain"):
                if key not in updates and base.get(key) is not None:
                    updates[key] = base[key]

    try:
        row = await repo.upsert_element_parameter(updates)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    await _recompute_and_broadcast(study_id, [element_id], option_id)
    view = await _evaluated_param(element_id, name, option_id) or row
    await broadcast_mutation(study_id, "parameter_updated", "parameter", row["id"],
                             {**view, "option_id": option_id})
    return view


@router.delete("/elements/{element_id}/parameters/{name}")
async def delete_element_parameter(element_id: str, name: str,
                                   option_id: str | None = Query(None)) -> dict:
    el = await _element_or_404(element_id)
    study_id = el["study_id"]
    option_id = await _scoped_option(option_id)
    defn = await repo.get_parameter_definition_by_name(name)
    row = None
    if defn is not None:
        rows = await repo.list_element_parameters_by_element(element_id, iteration=1, option_id=option_id)
        row = next((r for r in rows if r["definition_id"] == defn["id"]
                    and (r.get("option_id") or None) == option_id), None)
    if row is None:
        raise HTTPException(404, f"Parameter '{name}' not set on element {element_id}"
                            + (f" in option {option_id}" if option_id else ""))
    if option_id is not None:
        # Removing an override: the baseline row shows through again.
        deleted = await repo.soft_delete_element_parameter(row["id"])
    elif name in WELL_KNOWN_PARAMETERS:
        # The mirror row must survive: reset it to the plain column value.
        await repo.update_element_parameter(row["id"], {
            "formula": None, "formula_kind": None, "value_switch": "computed",
            "manual_value": None, "reference_value": None,
        })
        deleted = False
    else:
        deleted = await repo.soft_delete_element_parameter(row["id"])
    await _recompute_and_broadcast(study_id, [element_id], option_id)
    await broadcast_mutation(study_id, "parameter_deleted", "parameter", row["id"],
                             {"element_id": element_id, "name": name, "reset": not deleted, "option_id": option_id})
    return {"id": row["id"], "element_id": element_id, "name": name, "deleted": deleted, "reset": not deleted,
            "option_id": option_id}


# ─── Study level ───

@router.get("/studies/{study_id}/parameters")
async def list_study_parameters(study_id: str, element_id: str | None = None,
                                name: str | None = None, option_id: str | None = Query(None)) -> list[dict]:
    option_id = await _scoped_option(option_id)
    res = await equations.evaluate_study(study_id, option_id)
    out = res["parameters"]
    if element_id:
        out = [p for p in out if p["element_id"] == element_id]
    if name:
        out = [p for p in out if p["name"] == name]
    return out


@router.post("/studies/{study_id}/parameters/recompute")
async def recompute_study_parameters(study_id: str, option_id: str | None = Query(None)) -> dict:
    option_id = await _scoped_option(option_id)
    result = await equations.recompute_study(study_id, option_id)
    await broadcast_mutation(study_id, "parameters_recomputed", "study", study_id, {
        "persisted": result.get("persisted", 0), "written_back": result.get("written_back", 0),
        "errors": result.get("errors", []), "cycles": result.get("cycles", []),
    })
    return result


@router.get("/studies/{study_id}/parameters/graph")
async def study_parameter_graph(study_id: str) -> dict:
    return await equations.dependency_graph(study_id)
