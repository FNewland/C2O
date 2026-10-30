"""SpaceCDF — Ground Segment Scheduler Router (SCDF-221/222/223).

POST /api/ground/schedule — predict contacts and schedule downlinks.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.ground_scheduler import (
    ContactWindow,
    DEFAULT_STATIONS,
    GroundStation,
    OrbitParams,
    ScheduleResult,
    predict_contacts,
    schedule_downlinks,
)

router = APIRouter()  # prefix set in app.py


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class OrbitParamsIn(BaseModel):
    """Orbit parameters for contact prediction."""
    altitude_km: float = Field(600.0, description="Orbit altitude in km")
    inclination_deg: float = Field(97.8, description="Orbit inclination in degrees")
    period_s: float = Field(0.0, description="Orbit period in seconds (0 = auto)")


class StationIn(BaseModel):
    """Ground station input (optional override)."""
    id: str
    name: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float = 0.0
    antenna_diameter_m: float = 13.0
    min_elevation_deg: float = 5.0
    band: str = "X"


class ScheduleRequest(BaseModel):
    """Request body for ground schedule computation."""
    orbit_params: OrbitParamsIn = Field(default_factory=OrbitParamsIn)
    stations: list[StationIn] | None = Field(
        None, description="Custom station list (None = use defaults)"
    )
    data_rate_mbps: float = Field(100.0, description="Downlink data rate in Mbps")
    buffer_size_mbit: float = Field(64000.0, description="Onboard buffer size in Mbit")
    fill_rate_mbps: float = Field(10.0, description="Data generation rate in Mbps")
    duration_hours: float = Field(24.0, description="Scheduling horizon in hours")


class ContactOut(BaseModel):
    """A single contact window in the response."""
    station_id: str
    start_s: float
    end_s: float
    max_elevation_deg: float
    data_volume_mbit: float


class ScheduleResponse(BaseModel):
    """Response from ground schedule computation."""
    contacts: list[ContactOut]
    total_contact_min_per_day: float
    total_data_volume_mbit: float
    max_gap_hours: float
    coverage_pct: float
    station_count: int
    orbit_period_s: float


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/schedule", response_model=ScheduleResponse)
async def compute_ground_schedule(req: ScheduleRequest) -> ScheduleResponse:
    """Predict satellite-ground contacts and schedule downlinks."""
    try:
        # Build orbit params
        orbit = OrbitParams(
            altitude_km=req.orbit_params.altitude_km,
            inclination_deg=req.orbit_params.inclination_deg,
            period_s=req.orbit_params.period_s,
        )

        # Build station list
        if req.stations:
            stations = [
                GroundStation(
                    id=s.id,
                    name=s.name,
                    latitude_deg=s.latitude_deg,
                    longitude_deg=s.longitude_deg,
                    elevation_m=s.elevation_m,
                    antenna_diameter_m=s.antenna_diameter_m,
                    min_elevation_deg=s.min_elevation_deg,
                    band=s.band,
                )
                for s in req.stations
            ]
        else:
            stations = DEFAULT_STATIONS

        # Predict contacts
        contacts = predict_contacts(
            orbit=orbit,
            stations=stations,
            duration_hours=req.duration_hours,
            downlink_rate_mbps=req.data_rate_mbps,
        )

        # Schedule downlinks
        result = schedule_downlinks(
            contacts=contacts,
            data_rate_mbps=req.data_rate_mbps,
            buffer_size_mbit=req.buffer_size_mbit,
            fill_rate_mbps=req.fill_rate_mbps,
            duration_hours=req.duration_hours,
        )

        return ScheduleResponse(
            contacts=[
                ContactOut(
                    station_id=c.station_id,
                    start_s=c.start_s,
                    end_s=c.end_s,
                    max_elevation_deg=c.max_elevation_deg,
                    data_volume_mbit=c.data_volume_mbit,
                )
                for c in result.contacts
            ],
            total_contact_min_per_day=result.total_contact_min_per_day,
            total_data_volume_mbit=result.total_data_volume_mbit,
            max_gap_hours=result.max_gap_hours,
            coverage_pct=result.coverage_pct,
            station_count=len(stations),
            orbit_period_s=round(orbit.period_s, 1),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
