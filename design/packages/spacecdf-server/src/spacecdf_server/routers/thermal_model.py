"""Thermal nodal model with hot and cold cases (wave 3, 3.A6; PI addendum). Owner A (moved from H in
step 0, W0_SEAMS §9). Tables ``thermal_nodes``, ``thermal_couplings``, ``thermal_cases``
(``db/models_thermal.py``); the service is ``services/thermal_model.py``. H's ``orbit_season``
(3.H4) proposes the β / eclipse of the cases. The legacy single-node ``/api/thermal/*`` routes (H)
are unchanged.

    GET   /studies/{id}/thermal-model                 nodes, couplings, cases, last solution, summary
    POST  /studies/{id}/thermal-model/propose         nodes from the product tree, hot and cold cases
    POST  /studies/{id}/thermal-model/nodes           a node of the team's own
    PATCH /studies/{id}/thermal-model/nodes/{node}    edit a node (limits, optics, capacitance, heater)
    PATCH /studies/{id}/thermal-model/couplings/{c}   edit a coupling value
    PATCH /studies/{id}/thermal-model/cases/{case}    edit a case (β, eclipse)
    POST  /studies/{id}/thermal-model/run             solve every case: margins, heater sizing
    POST  /studies/{id}/thermal-model/heaters/accept  take the sized heaters, solve again
    GET   /studies/{id}/thermal-model/evidence        what the thermal gate criteria read (R)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..db.models_thermal import ThermalCaseRow, ThermalCouplingRow, ThermalNodeRow
from ..services import study_rows as sr
from ..services import thermal_model as tm
from .studies import get_study_store

router = APIRouter()


def _study_or_404(study_id: str):
    s = get_study_store().get(study_id)
    if s is None:
        raise HTTPException(404, f"Study {study_id} not found")
    return s


async def _row(model, study_id: str, row_id: str) -> dict:
    r = await sr.get_row(model, row_id)
    if r is None or r.get("study_id") != study_id:
        raise HTTPException(404, "not found")
    return r


@router.get("/studies/{study_id}/thermal-model")
async def get_thermal_model(study_id: str) -> dict:
    _study_or_404(study_id)
    return await tm.get(study_id)


@router.post("/studies/{study_id}/thermal-model/propose")
async def propose_thermal_model(study_id: str, replace: bool = False) -> dict:
    _study_or_404(study_id)
    return await tm.propose(study_id, replace=replace)


@router.get("/studies/{study_id}/thermal-model/evidence")
async def thermal_model_evidence(study_id: str) -> dict:
    _study_or_404(study_id)
    return await tm.evidence(study_id)


@router.post("/studies/{study_id}/thermal-model/nodes")
async def create_thermal_node(study_id: str, body: dict[str, Any]) -> dict:
    _study_or_404(study_id)
    f = {k: body[k] for k in tm.NODE_FIELDS if k in body}
    if not f.get("name"):
        raise HTTPException(422, "a node needs a name")
    n = len(await sr.list_rows(ThermalNodeRow, study_id))
    f.setdefault("code", f"N{n + 1:02d}")
    f["origin"] = "user"
    f["order"] = n
    f["data_json"] = {"key": f"user:{f['code']}", "external": bool(body.get("external")), "elements": []}
    return (await sr.insert_rows(ThermalNodeRow, study_id, [f], prefix="tn"))[0]


@router.patch("/studies/{study_id}/thermal-model/nodes/{node_id}")
async def update_thermal_node(study_id: str, node_id: str, body: dict[str, Any]) -> dict:
    _study_or_404(study_id)
    await _row(ThermalNodeRow, study_id, node_id)
    f = {k: body[k] for k in tm.NODE_FIELDS if k in body}
    f["origin"] = "user"
    return await sr.update_row(ThermalNodeRow, node_id, f)


@router.patch("/studies/{study_id}/thermal-model/couplings/{coupling_id}")
async def update_thermal_coupling(study_id: str, coupling_id: str, body: dict[str, Any]) -> dict:
    _study_or_404(study_id)
    await _row(ThermalCouplingRow, study_id, coupling_id)
    f = {k: body[k] for k in ("value", "kind", "source", "node_a", "node_b") if k in body}
    f["origin"] = "user"
    return await sr.update_row(ThermalCouplingRow, coupling_id, f)


@router.patch("/studies/{study_id}/thermal-model/cases/{case_id}")
async def update_thermal_case(study_id: str, case_id: str, body: dict[str, Any]) -> dict:
    _study_or_404(study_id)
    await _row(ThermalCaseRow, study_id, case_id)
    f = {k: body[k] for k in ("beta_deg", "eclipse_min", "mode_key", "environment_json", "code") if k in body}
    f.update(origin="user", source="user", status="accepted")
    return await sr.update_row(ThermalCaseRow, case_id, f)


@router.post("/studies/{study_id}/thermal-model/heaters/accept")
async def accept_thermal_heaters(study_id: str) -> dict:
    """Take the sized heaters into the model and solve again."""
    _study_or_404(study_id)
    return await tm.accept_heaters(study_id)


@router.post("/studies/{study_id}/thermal-model/run")
async def run_thermal_model(study_id: str) -> dict:
    _study_or_404(study_id)
    return await tm.run(study_id)
