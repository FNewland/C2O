"""ConOps Executor API — SCDF-201.

Provides REST endpoint to simulate spacecraft operations through orbit(s).
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.conops_executor import (
    ConOpsMode,
    ModeGuard,
    OrbitParams,
    PowerParams,
    ThermalParams,
    TimeSeriesResult,
    simulate_orbit,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ModeSchema(BaseModel):
    name: str
    power_draw_w: float
    pointing: str = "nadir"
    data_rate_bps: float = 0.0
    is_payload_active: bool = False


class GuardSchema(BaseModel):
    condition: str
    target_mode: str
    priority: int = 0


class OrbitParamsSchema(BaseModel):
    altitude_km: float = 550.0
    inclination_deg: float = 97.5
    eclipse_fraction: float = 0.35
    period_s: float = 5800.0
    contact_time_per_orbit_s: float = 600.0


class PowerParamsSchema(BaseModel):
    sa_power_eol_w: float = 60.0
    battery_capacity_wh: float = 40.0
    heater_power_w: float = 5.0


class ThermalParamsSchema(BaseModel):
    capacitance_j_per_k: float = 5000.0
    radiator_area_m2: float = 0.04
    emissivity: float = 0.85
    absorptivity: float = 0.3
    internal_dissipation_fraction: float = 0.6
    solar_flux_w_m2: float = 1361.0
    initial_temp_c: float = 20.0


class SimulateRequest(BaseModel):
    orbit_params: Optional[OrbitParamsSchema] = None
    power_params: Optional[PowerParamsSchema] = None
    thermal_params: Optional[ThermalParamsSchema] = None
    modes: Optional[List[ModeSchema]] = None
    guards: Optional[List[GuardSchema]] = None
    duration_hours: Optional[float] = None
    mode_schedule: Optional[List[Dict[str, Any]]] = None


class SimulateResponse(BaseModel):
    time_s: List[float]
    mode: List[str]
    soc_pct: List[float]
    temp_c: List[float]
    data_buffer_mbit: List[float]
    events: List[Dict[str, Any]]
    summary: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/simulate", response_model=SimulateResponse)
async def simulate_conops(req: SimulateRequest) -> SimulateResponse:
    """Simulate spacecraft ConOps through one or more orbits.

    All parameters are optional — sensible defaults are used for a typical
    LEO Earth-observation mission if not provided.
    """
    # Convert Pydantic models to dataclass instances
    orbit = OrbitParams(**req.orbit_params.model_dump()) if req.orbit_params else None
    power = PowerParams(**req.power_params.model_dump()) if req.power_params else None
    thermal = ThermalParams(**req.thermal_params.model_dump()) if req.thermal_params else None

    modes_dc = None
    if req.modes:
        modes_dc = [ConOpsMode(**m.model_dump()) for m in req.modes]

    guards_dc = None
    if req.guards:
        guards_dc = [ModeGuard(**g.model_dump()) for g in req.guards]

    duration_s = None
    if req.duration_hours is not None:
        duration_s = req.duration_hours * 3600.0

    result: TimeSeriesResult = simulate_orbit(
        modes=modes_dc,
        guards=guards_dc,
        orbit_params=orbit,
        power_params=power,
        thermal_params=thermal,
        duration_s=duration_s,
        mode_schedule=req.mode_schedule,
    )

    # Compute summary statistics
    summary = {
        "min_soc_pct": round(min(result.soc_pct), 2) if result.soc_pct else None,
        "max_soc_pct": round(max(result.soc_pct), 2) if result.soc_pct else None,
        "min_temp_c": round(min(result.temp_c), 2) if result.temp_c else None,
        "max_temp_c": round(max(result.temp_c), 2) if result.temp_c else None,
        "max_data_buffer_mbit": round(max(result.data_buffer_mbit), 3) if result.data_buffer_mbit else None,
        "num_events": len(result.events),
        "num_guard_triggers": sum(1 for e in result.events if e["type"] == "guard_trigger"),
        "duration_s": result.time_s[-1] if result.time_s else 0,
    }

    return SimulateResponse(
        time_s=result.time_s,
        mode=result.mode,
        soc_pct=result.soc_pct,
        temp_c=result.temp_c,
        data_buffer_mbit=result.data_buffer_mbit,
        events=result.events,
        summary=summary,
    )
