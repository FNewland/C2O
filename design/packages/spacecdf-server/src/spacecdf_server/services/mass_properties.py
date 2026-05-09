"""SpaceCDF — Mass Properties Service.

Accumulates center of mass (CoM) from component placement and mass.
Foundation for AOCS disturbance-torque validation (gravity gradient
torque depends on principal axis offset from orbit frame).

Per ECSS-E-ST-31C (Mass Properties).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class MassComponent:
    """A component with mass and position in the spacecraft body frame."""
    name: str
    mass_kg: float
    x_m: float = 0.0  # Forward (velocity direction)
    y_m: float = 0.0  # Starboard
    z_m: float = 0.0  # Nadir


@dataclass
class MassPropertiesResult:
    """Result of mass properties computation."""
    total_mass_kg: float
    com_x_m: float
    com_y_m: float
    com_z_m: float
    com_offset_m: float  # Distance from geometric center
    # Moments of inertia (kg·m²) — parallel axis theorem
    ixx: float = 0.0
    iyy: float = 0.0
    izz: float = 0.0
    # Products of inertia (kg·m²) — for full 3x3 tensor
    ixy: float = 0.0
    ixz: float = 0.0
    iyz: float = 0.0
    # Principal axes
    principal_ixx: float = 0.0
    principal_iyy: float = 0.0
    principal_izz: float = 0.0
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def compute_mass_properties(
    components: list[MassComponent],
    spacecraft_dims_m: tuple[float, float, float] = (0.1, 0.1, 0.3),
) -> MassPropertiesResult:
    """Compute CoM and inertia from component placements.

    Args:
        components: List of mass components with positions.
        spacecraft_dims_m: (x, y, z) dimensions for geometric center.

    Returns:
        MassPropertiesResult with CoM, offset, and inertias.
    """
    total_mass = sum(c.mass_kg for c in components)
    if total_mass <= 0:
        return MassPropertiesResult(0, 0, 0, 0, 0)

    # Center of mass
    com_x = sum(c.mass_kg * c.x_m for c in components) / total_mass
    com_y = sum(c.mass_kg * c.y_m for c in components) / total_mass
    com_z = sum(c.mass_kg * c.z_m for c in components) / total_mass

    # Offset from geometric center
    geo_x, geo_y, geo_z = spacecraft_dims_m[0] / 2, spacecraft_dims_m[1] / 2, spacecraft_dims_m[2] / 2
    offset = math.sqrt((com_x - geo_x) ** 2 + (com_y - geo_y) ** 2 + (com_z - geo_z) ** 2)

    # Full inertia tensor via parallel axis theorem
    # Each component treated as point mass offset from CoM
    ixx = sum(c.mass_kg * ((c.y_m - com_y) ** 2 + (c.z_m - com_z) ** 2) for c in components)
    iyy = sum(c.mass_kg * ((c.x_m - com_x) ** 2 + (c.z_m - com_z) ** 2) for c in components)
    izz = sum(c.mass_kg * ((c.x_m - com_x) ** 2 + (c.y_m - com_y) ** 2) for c in components)
    # Products of inertia (negative by convention)
    ixy = -sum(c.mass_kg * (c.x_m - com_x) * (c.y_m - com_y) for c in components)
    ixz = -sum(c.mass_kg * (c.x_m - com_x) * (c.z_m - com_z) for c in components)
    iyz = -sum(c.mass_kg * (c.y_m - com_y) * (c.z_m - com_z) for c in components)

    # Add body contribution (uniform cuboid about CoM)
    dx, dy, dz = spacecraft_dims_m
    ixx += total_mass * (dy ** 2 + dz ** 2) / 12
    iyy += total_mass * (dx ** 2 + dz ** 2) / 12
    izz += total_mass * (dx ** 2 + dy ** 2) / 12

    # Principal moments (eigenvalues of inertia tensor — simplified for near-diagonal)
    # For a proper solution, would need eigenvalue decomposition; for CubeSats
    # the off-diagonals are usually small, so approximate as diagonal values
    principal_ixx = ixx
    principal_iyy = iyy
    principal_izz = izz

    warnings = []
    if offset > max(spacecraft_dims_m) * 0.1:
        warnings.append(f"CoM offset {offset:.3f} m exceeds 10% of max dimension — check component placement")
    # Check if products of inertia are significant (>5% of diagonal)
    max_diag = max(ixx, iyy, izz) if max(ixx, iyy, izz) > 0 else 1
    if max(abs(ixy), abs(ixz), abs(iyz)) > 0.05 * max_diag:
        warnings.append("Significant products of inertia — principal axes may not align with body frame")

    return MassPropertiesResult(
        total_mass_kg=round(total_mass, 3),
        com_x_m=round(com_x, 4),
        com_y_m=round(com_y, 4),
        com_z_m=round(com_z, 4),
        com_offset_m=round(offset, 4),
        ixx=round(ixx, 4), iyy=round(iyy, 4), izz=round(izz, 4),
        ixy=round(ixy, 4), ixz=round(ixz, 4), iyz=round(iyz, 4),
        principal_ixx=round(principal_ixx, 4),
        principal_iyy=round(principal_iyy, 4),
        principal_izz=round(principal_izz, 4),
        warnings=warnings,
    )
