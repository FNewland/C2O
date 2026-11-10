"""Thermal nodal model with hot and cold cases (PI addendum). Owner A (3.A6; moved from H in step 0 to balance the load, W0_SEAMS §9). Tables ``thermal_nodes``, ``thermal_couplings``, ``thermal_cases`` (``db/models_thermal.py``). H's ``orbit_season`` (3.H4) proposes the β / eclipse of the cases. The legacy single-node ``/api/thermal/*`` routes (H) are unchanged.

STEP 0 STUB (wave 3, PI addendum): the routes exist so the other agents and the frontend can code
against them; the owner replaces each body.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ._wave3_stub import not_implemented, stub_list, study_or_404

router = APIRouter()
OWNER, WP = "A", "3.A6"


@router.get("/studies/{study_id}/thermal-model")
async def get_thermal_model(study_id: str) -> dict:
    """TODO(A, 3.A6): nodes, couplings, cases and the last solution with margins."""
    return stub_list(study_id, OWNER, WP)


@router.post("/studies/{study_id}/thermal-model/propose")
async def propose_thermal_model(study_id: str) -> dict:
    """TODO(A, 3.A6): 6-10 nodes from the product tree with KB limits; hot and cold cases from the orbit."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/thermal-model/nodes")
async def create_thermal_node(study_id: str, body: dict[str, Any]) -> dict:
    """TODO(A, 3.A6): ."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.patch("/studies/{study_id}/thermal-model/nodes/{node_id}")
async def update_thermal_node(study_id: str, node_id: str, body: dict[str, Any]) -> dict:
    """TODO(A, 3.A6): ."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)


@router.post("/studies/{study_id}/thermal-model/run")
async def run_thermal_model(study_id: str) -> dict:
    """TODO(A, 3.A6): solve every case; margins (design, acceptance, qualification), heater sizing."""
    study_or_404(study_id)
    raise not_implemented(OWNER, WP)
