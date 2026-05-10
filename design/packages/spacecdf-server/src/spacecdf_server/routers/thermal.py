"""Thermal Network API — SCDF-211/212/213.

Provides REST endpoint for multi-node thermal analysis of spacecraft.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.thermal_network import (
    ThermalConductance,
    ThermalNode,
    analyze_thermal_network,
)
from ..services.thermal_transient import compute_thermal_transient

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ThermalNodeSchema(BaseModel):
    id: str
    name: str
    mass_kg: float
    specific_heat_j_kg_k: float = 900.0
    temperature_c: float = 20.0
    power_dissipation_w: float = 0.0
    emissivity: float = 0.0
    area_m2: float = 0.0
    is_radiator: bool = False
    earth_facing: bool = False


class ThermalConductanceSchema(BaseModel):
    node_a_id: str
    node_b_id: str
    conductance_w_k: float


class OrbitParamsSchema(BaseModel):
    eclipse_fraction: float = 0.35
    period_s: float = 5400.0


class ThermalAnalyzeRequest(BaseModel):
    nodes: Optional[List[ThermalNodeSchema]] = None
    conductances: Optional[List[ThermalConductanceSchema]] = None
    orbit_params: Optional[OrbitParamsSchema] = None
    duration_s: float = 5400.0
    run_transient: bool = True


class SteadyStateResult(BaseModel):
    node_temps: Dict[str, float]
    radiator_heat_rejection_w: float
    max_temp_c: float
    min_temp_c: float
    warnings: List[str]


class TransientResultSchema(BaseModel):
    time_s: List[float]
    temperatures: Dict[str, List[float]]
    radiator_heat_rejection_w: List[float]
    max_temp_c: float
    min_temp_c: float
    warnings: List[str]


class ThermalAnalyzeResponse(BaseModel):
    steady_state: SteadyStateResult
    transient: Optional[TransientResultSchema] = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=ThermalAnalyzeResponse)
async def analyze_thermal(req: ThermalAnalyzeRequest) -> ThermalAnalyzeResponse:
    """Analyze spacecraft thermal network (steady-state and transient).

    All parameters are optional. If nodes/conductances are omitted, a default
    6U CubeSat thermal model is used.
    """
    # Convert Pydantic models to dataclass instances
    nodes = None
    if req.nodes:
        nodes = [
            ThermalNode(
                id=n.id,
                name=n.name,
                mass_kg=n.mass_kg,
                specific_heat_j_kg_k=n.specific_heat_j_kg_k,
                temperature_c=n.temperature_c,
                power_dissipation_w=n.power_dissipation_w,
                emissivity=n.emissivity,
                area_m2=n.area_m2,
                is_radiator=n.is_radiator,
                earth_facing=n.earth_facing,
            )
            for n in req.nodes
        ]

    conductances = None
    if req.conductances:
        conductances = [
            ThermalConductance(
                node_a_id=c.node_a_id,
                node_b_id=c.node_b_id,
                conductance_w_k=c.conductance_w_k,
            )
            for c in req.conductances
        ]

    eclipse_fraction = 0.35
    duration_s = req.duration_s
    if req.orbit_params:
        eclipse_fraction = req.orbit_params.eclipse_fraction
        if req.orbit_params.period_s:
            duration_s = req.orbit_params.period_s

    result = analyze_thermal_network(
        nodes=nodes,
        conductances=conductances,
        duration_s=duration_s,
        eclipse_fraction=eclipse_fraction,
        run_transient=req.run_transient,
    )

    return ThermalAnalyzeResponse(**result)


# ---------------------------------------------------------------------------
# Transient solver endpoint (single-node lumped parameter)
# ---------------------------------------------------------------------------


class ThermalTransientRequest(BaseModel):
    orbit_altitude_km: float = 500
    orbit_inclination_deg: float = 97.4
    mass_kg: float = 4.0
    surface_area_m2: float = 0.06
    alpha_s: float = 0.3
    epsilon_ir: float = 0.8
    internal_power_w: float = 5.0
    num_orbits: int = 3


class ThermalTransientResponse(BaseModel):
    times_s: List[float]
    temperatures_k: List[float]
    hot_case_k: float
    cold_case_k: float
    eclipse_fraction: float
    orbit_period_s: float


@router.post("/transient", response_model=ThermalTransientResponse)
async def thermal_transient(req: ThermalTransientRequest) -> ThermalTransientResponse:
    """Lumped-parameter single-node thermal transient solver.

    Computes temperature profile over multiple orbits including solar,
    albedo, Earth IR, and radiative cooling.
    """
    result = compute_thermal_transient(
        orbit_altitude_km=req.orbit_altitude_km,
        orbit_inclination_deg=req.orbit_inclination_deg,
        mass_kg=req.mass_kg,
        surface_area_m2=req.surface_area_m2,
        alpha_s=req.alpha_s,
        epsilon_ir=req.epsilon_ir,
        internal_power_w=req.internal_power_w,
        num_orbits=req.num_orbits,
    )
    return ThermalTransientResponse(**result)
