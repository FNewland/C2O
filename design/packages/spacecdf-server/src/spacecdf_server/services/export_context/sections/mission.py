"""Section ``mission``: name, phase, the mission definition (``study.requirements``) and the derived
orbit figures (period, eclipse, orbits per day). Owner: X (export core)."""
from __future__ import annotations

from ._util import dump


def empty() -> dict:
    return {"name": "", "phase": None, "definition": {}, "orbit": {}}


def _orbit(defn: dict) -> dict:
    o = dict(defn.get("orbit") or {})
    try:
        from spacecdf_common.physics.orbit import compute_orbit_params
        op = compute_orbit_params(altitude_km=float(o.get("altitude_km") or 500.0),
                                  inclination_deg=float(o.get("inclination_deg") or 97.4),
                                  eccentricity=float(o.get("eccentricity") or 0.0))
        o.update({"period_min": round(op.period_min, 2), "velocity_ms": round(op.velocity_ms, 1),
                  "eclipse_fraction": round(op.eclipse_fraction, 3),
                  "eclipse_duration_min": round(getattr(op, "eclipse_duration_min", 0), 2),
                  "orbits_per_day": round(op.orbits_per_day, 2)})
    except Exception:  # noqa: BLE001 — orbit maths unavailable: the stored values only
        pass
    return o


async def collect(ctx) -> dict:
    s = ctx.study
    if s is None:
        return empty()
    defn = dump(getattr(s, "requirements", None)) or {}
    phase = getattr(s, "phase", None)
    return {"name": getattr(s, "name", "") or "",
            "phase": getattr(phase, "value", phase),
            "gate_profile": getattr(s, "gate_profile", None),
            "definition": defn,
            "orbit": _orbit(defn)}
