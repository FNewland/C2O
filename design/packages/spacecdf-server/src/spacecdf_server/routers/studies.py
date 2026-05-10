"""SpaceCDF — Study Management API.

CRUD operations for design studies. Accepts full V-model data:
MissionNeed + ConOps + requirements. Auto-generates functional
decomposition and default ConOps modes when mission need is provided.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from spacecdf_common.models.study import Study, MissionRequirements
from spacecdf_common.models.mission_need import MissionNeed
from spacecdf_common.models.conops import ConceptOfOperations, OperationalMode, MissionPhase, ModeType, MissionPhaseType
from spacecdf_common.models.functions import FunctionalDecomposition, generate_starter_decomposition
from spacecdf_common.models.interfaces import generate_standard_interface_matrix
from ..db.study_repo import db_save_study, db_delete_study, db_load_all_studies

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Write-through cache — primary read path (fast), backed by DB
_studies: dict[str, Study] = {}


async def init_study_cache() -> None:
    """Load all persisted studies from DB into the in-memory cache."""
    loaded = await db_load_all_studies()
    _studies.update(loaded)
    logger.info("Study cache initialized with %d studies", len(_studies))


class CreateStudyRequest(BaseModel):
    """Accepts full V-model input: requirements + optional mission need."""
    requirements: MissionRequirements
    mission_need: dict[str, Any] | None = None


@router.get("/")
async def list_studies() -> list[dict]:
    """List all studies."""
    return [
        {"id": s.id, "name": s.name, "phase": s.phase.value, "created": s.created.isoformat()}
        for s in _studies.values()
    ]


@router.post("/")
async def create_study(req: CreateStudyRequest) -> dict:
    """Create a new design study from mission requirements + optional mission need.

    When mission_need is provided, auto-generates:
    - Default ConOps modes (safe, nominal, downlink, eclipse)
    - Functional decomposition from objectives
    - Standard interface matrix
    """
    requirements = req.requirements

    # Parse mission need if provided
    mission_need = MissionNeed()
    if req.mission_need:
        try:
            mission_need = MissionNeed(**req.mission_need)
        except Exception:
            mission_need = MissionNeed()

    # Auto-generate ConOps with default modes from requirements
    conops = _generate_default_conops(requirements)

    # Auto-generate functional decomposition from objectives
    func_decomp = FunctionalDecomposition()
    if mission_need.objectives:
        obj_dicts = [o.model_dump() for o in mission_need.objectives]
        func_decomp = generate_starter_decomposition(obj_dicts)

    # Auto-generate interface matrix
    interface_matrix = generate_standard_interface_matrix()

    study = Study(
        id=str(uuid.uuid4())[:8],
        name=requirements.name,
        mission_need=mission_need,
        conops=conops,
        functional_decomposition=func_decomp,
        interface_matrix=interface_matrix,
        requirements=requirements,
        created=datetime.now(timezone.utc),
    )
    _studies[study.id] = study

    # Persist to DB (fire-and-forget — errors logged, never crash the API)
    try:
        await db_save_study(study)
    except Exception:
        logger.exception("Failed to persist study %s to DB", study.id)

    return {
        "id": study.id,
        "name": study.name,
        "phase": study.phase.value,
        "mission_need_populated": bool(mission_need.problem_statement),
        "conops_modes": len(conops.modes),
        "functions": len(func_decomp.functions),
        "interfaces": len(interface_matrix.subsystem_interfaces),
    }


def _generate_default_conops(req: MissionRequirements) -> ConceptOfOperations:
    """Generate default ConOps modes from mission requirements.

    Every spacecraft needs at least: safe, nominal, downlink, eclipse modes.
    Power/pointing profiles are estimated from the requirements.
    """
    # Estimate platform power
    payload_power = sum(p.power_w for p in req.payloads) if req.payloads else 30
    payload_duty = max((p.duty_cycle_percent for p in req.payloads), default=25) / 100
    pointing = min((p.pointing_accuracy_deg for p in req.payloads), default=1.0)
    platform_power = 15 if req.spacecraft_class == "nano" else (25 if req.spacecraft_class == "micro" else 40)

    modes = [
        OperationalMode(
            id="safe", name="Safe Mode", mode_type=ModeType.SAFE,
            power_w=platform_power * 0.6 + 10,  # Reduced bus + heaters
            payload_active=False, payload_power_w=0,
            platform_power_w=platform_power * 0.6, heater_power_w=10,
            pointing_requirement_deg=5.0, sun_illuminated=False,
            is_critical=True, autonomous=True,
            description="Minimum power survival mode. Entered on any anomaly.",
        ),
        OperationalMode(
            id="nominal", name="Nominal Science", mode_type=ModeType.NOMINAL_SCIENCE,
            power_w=platform_power + payload_power * payload_duty,
            payload_active=True, payload_power_w=payload_power,
            platform_power_w=platform_power, heater_power_w=0,
            pointing_requirement_deg=pointing, sun_illuminated=True,
            duty_cycle_percent=payload_duty * 100,
            description="Primary science/payload operations during sunlight.",
        ),
        OperationalMode(
            id="downlink", name="Downlink", mode_type=ModeType.DOWNLINK,
            power_w=platform_power + 15,  # TX power
            payload_active=False, payload_power_w=0,
            platform_power_w=platform_power + 15, heater_power_w=0,
            pointing_requirement_deg=2.0, sun_illuminated=True,
            data_downlink_active=True, requires_ground_contact=True,
            description="Ground station pass — telemetry and data downlink.",
        ),
        OperationalMode(
            id="eclipse", name="Eclipse", mode_type=ModeType.ECLIPSE,
            power_w=platform_power * 0.8 + 5,  # Reduced + heaters
            payload_active=False, payload_power_w=0,
            platform_power_w=platform_power * 0.8, heater_power_w=5,
            pointing_requirement_deg=5.0, sun_illuminated=False,
            description="Eclipse cruise — battery powered, heaters on.",
        ),
    ]

    phases = [
        MissionPhase(id="leop", name="LEOP", phase_type=MissionPhaseType.LEOP,
                     duration_days=3, modes=["safe"], primary_mode="safe"),
        MissionPhase(id="commissioning", name="Commissioning", phase_type=MissionPhaseType.COMMISSIONING,
                     duration_days=30, modes=["safe", "nominal", "downlink"], primary_mode="nominal"),
        MissionPhase(id="nominal", name="Nominal Operations", phase_type=MissionPhaseType.NOMINAL,
                     duration_days=int(req.design_lifetime_years * 365 * 0.8),
                     modes=["nominal", "downlink", "eclipse"], primary_mode="nominal"),
        MissionPhase(id="disposal", name="Disposal", phase_type=MissionPhaseType.DISPOSAL,
                     duration_days=14, modes=["safe"], primary_mode="safe"),
    ]

    return ConceptOfOperations(modes=modes, phases=phases)


@router.get("/{study_id}")
async def get_study(study_id: str) -> Study:
    """Get a study by ID."""
    study = _studies.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    return study


@router.delete("/{study_id}")
async def delete_study(study_id: str) -> dict:
    """Delete a study."""
    if study_id not in _studies:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    # Remove from DB first, then cache
    try:
        await db_delete_study(study_id)
    except Exception:
        logger.exception("Failed to delete study %s from DB", study_id)
    del _studies[study_id]
    return {"deleted": study_id}


def get_study_store() -> dict[str, Study]:
    """Access the study store (for use by other routers)."""
    return _studies
