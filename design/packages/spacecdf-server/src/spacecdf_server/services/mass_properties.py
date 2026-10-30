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
    dims_m: tuple[float, float, float] | None = None  # box (dx, dy, dz) about the component CoM (SCDF-176)


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
    principal_axes: list[list[float]] | None = None  # rows = unit vectors in the body frame (SCDF-176)
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def principal_moments(ixx: float, iyy: float, izz: float, ixy: float, ixz: float, iyz: float,
                      ) -> tuple[list[float], list[list[float]]]:
    """Eigen-decomposition of the symmetric inertia tensor (cyclic Jacobi).

    ``ixy/ixz/iyz`` are the *products of inertia* in the negative convention
    (the off-diagonal tensor entries). Returns ``(moments, axes)`` with the
    moments ascending and ``axes[i]`` the unit eigenvector of ``moments[i]``.
    """
    a = [[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]]
    v = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for _ in range(50):
        off = abs(a[0][1]) + abs(a[0][2]) + abs(a[1][2])
        if off < 1e-15 * max(1.0, abs(ixx) + abs(iyy) + abs(izz)):
            break
        for p, q in ((0, 1), (0, 2), (1, 2)):
            if abs(a[p][q]) < 1e-300:
                continue
            theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
            t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
            c = 1.0 / math.sqrt(t * t + 1.0)
            s_ = t * c
            for k in range(3):
                akp, akq = a[k][p], a[k][q]
                a[k][p], a[k][q] = c * akp - s_ * akq, s_ * akp + c * akq
            for k in range(3):
                apk, aqk = a[p][k], a[q][k]
                a[p][k], a[q][k] = c * apk - s_ * aqk, s_ * apk + c * aqk
            for k in range(3):
                vkp, vkq = v[k][p], v[k][q]
                v[k][p], v[k][q] = c * vkp - s_ * vkq, s_ * vkp + c * vkq
    order = sorted(range(3), key=lambda i: a[i][i])
    moments = [a[i][i] for i in order]
    axes = [[v[0][i], v[1][i], v[2][i]] for i in order]
    return moments, axes


def compute_mass_properties(
    components: list[MassComponent],
    spacecraft_dims_m: tuple[float, float, float] = (0.1, 0.1, 0.3),
    *,
    body_inertia: bool = True,
) -> MassPropertiesResult:
    """Compute CoM and inertia from component placements.

    Args:
        components: List of mass components with positions. A component with
            ``dims_m`` contributes its own box inertia about its CoM (SCDF-176);
            the others are point masses.
        spacecraft_dims_m: (x, y, z) dimensions for geometric center.
        body_inertia: add the uniform-cuboid term of the whole envelope about
            the CoM (legacy single-body approximation). Pass ``False`` when the
            components carry their own ``dims_m`` — otherwise the mass is
            counted twice.

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

    # Own box inertia of the components that carry dimensions (about their CoM)
    for c in components:
        if c.dims_m:
            cx, cy, cz = c.dims_m
            ixx += c.mass_kg * (cy ** 2 + cz ** 2) / 12
            iyy += c.mass_kg * (cx ** 2 + cz ** 2) / 12
            izz += c.mass_kg * (cx ** 2 + cy ** 2) / 12

    # Add body contribution (uniform cuboid about CoM)
    if body_inertia:
        dx, dy, dz = spacecraft_dims_m
        ixx += total_mass * (dy ** 2 + dz ** 2) / 12
        iyy += total_mass * (dx ** 2 + dz ** 2) / 12
        izz += total_mass * (dx ** 2 + dy ** 2) / 12

    # Principal moments / axes (Jacobi eigen-decomposition of the tensor)
    moments, axes = principal_moments(ixx, iyy, izz, ixy, ixz, iyz)
    # keep the body-axis naming: the principal moment closest to each body axis
    principal = [0.0, 0.0, 0.0]
    used: set[int] = set()
    for body_axis in range(3):
        best = max((i for i in range(3) if i not in used), key=lambda i: abs(axes[i][body_axis]))
        used.add(best)
        principal[body_axis] = moments[best]
    principal_ixx, principal_iyy, principal_izz = principal

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
        principal_axes=[[round(x, 6) for x in ax] for ax in axes],
        warnings=warnings,
    )
