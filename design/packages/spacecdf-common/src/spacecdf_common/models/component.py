"""SpaceCDF — Component and Launch Vehicle data models for the Knowledge Base."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Component(BaseModel):
    """A COTS or heritage component in the knowledge base."""

    id: str
    name: str
    manufacturer: str
    category: str = Field(description="e.g. 'reaction_wheel', 'star_tracker', 'solar_cell'")
    subcategory: str = ""
    mass_kg: float
    power_w: float
    power_peak_w: float = 0.0
    dimensions_mm: list[float] = Field(default_factory=list, description="[L, W, H] or [D, H]")
    cost_keur: float | None = None
    trl: int = Field(ge=1, le=9)
    heritage_missions: list[str] = Field(default_factory=list)
    temperature_range_c: list[float] = Field(default_factory=lambda: [-40.0, 85.0])
    radiation_tolerance_krad: float | None = None
    interfaces: list[str] = Field(default_factory=list, description="e.g. ['CAN', 'RS-422', 'SpaceWire']")
    performance: dict[str, Any] = Field(default_factory=dict, description="Category-specific metrics")
    datasheet_url: str = ""
    notes: str = ""

    @property
    def is_flight_proven(self) -> bool:
        return self.trl >= 8

    @property
    def is_innovative(self) -> bool:
        return self.trl <= 6


class LaunchVehicle(BaseModel):
    """Launch vehicle in the knowledge base."""

    id: str
    name: str
    manufacturer: str
    country: str
    status: str = Field(description="operational, development, retired")
    first_flight: str = ""
    performance_kg: dict[str, float] = Field(
        description="Orbit -> capacity mapping, e.g. {'LEO_200': 22800, 'SSO_500': 15000}"
    )
    fairing_diameter_m: float
    fairing_height_m: float
    cost_musd: float | None = None
    rideshare_available: bool = False
    rideshare_cost_keur_per_kg: float | None = None
    launch_sites: list[str] = Field(default_factory=list)
    reliability: float | None = Field(default=None, description="Historical success rate 0-1")
    turnaround_months: int | None = None
    notes: str = ""

    def capacity_for_orbit(self, orbit_key: str) -> float | None:
        """Get payload capacity for a given orbit. Tries exact match then prefix match."""
        if orbit_key in self.performance_kg:
            return self.performance_kg[orbit_key]
        for key, val in self.performance_kg.items():
            if key.startswith(orbit_key):
                return val
        return None


class GroundStationEntry(BaseModel):
    """Ground station in the knowledge base."""

    id: str
    name: str
    network: str = Field(description="e.g. 'ESTRACK', 'DSN', 'KSAT', 'Atlas'")
    lat_deg: float
    lon_deg: float
    alt_km: float = 0.0
    antenna_diameter_m: float = 13.0
    frequency_bands: list[str] = Field(default_factory=lambda: ["S", "X"])
    g_over_t_db_k: float | None = None
    eirp_dbw: float | None = None
    min_elevation_deg: float = 5.0
    availability_percent: float = 95.0
    cost_per_pass_eur: float | None = None
    notes: str = ""


class MaterialProperty(BaseModel):
    """Structural material in the knowledge base."""

    id: str
    name: str
    category: str = Field(description="e.g. 'aluminium', 'cfrp', 'titanium', 'honeycomb'")
    density_kg_m3: float
    yield_strength_mpa: float
    elastic_modulus_gpa: float
    thermal_conductivity_w_mk: float
    cte_um_mk: float = Field(description="Coefficient of thermal expansion (um/m/K)")
    max_temperature_c: float
    cost_eur_per_kg: float | None = None
    notes: str = ""
