"""Mission definition editing (Nov 2026).

``PATCH /api/studies/{id}/mission`` changes what the wizard fixed at creation: the mission
need (problem, context, stakeholders, objectives), the orbit (type, altitude, inclination,
LTAN …), the payloads, the spacecraft class, the lifetime, the launch / disposal choices,
the link and the ground-station names — all on ``study.requirements`` /
``study.mission_need``, which every analysis reads (``services/analysis_context.py``).

Nothing is "marked" stale by hand: the analyses' ``inputs_hash`` covers the orbit and the
mission definition (``analysis_context.HASH_KEYS`` ``orbit`` / ``mission``), so the next
``GET …/analyses`` reports every run made with the old values as ``stale``.

Public API:
    MissionPatch                         request body (every field optional)
    apply_mission_patch(study, patch) -> (changed_paths, warnings)   raises ValueError
    SPACECRAFT_CLASSES, DISPOSAL_METHODS
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from spacecdf_common.models.mission_need import MissionNeed
from spacecdf_common.models.study import (
    LinkRequirements, MissionRequirements, MissionType, OrbitType, PayloadRequirements, Study,
)

SPACECRAFT_CLASSES = ("nano", "micro", "small", "medium", "large", "flagship")
DISPOSAL_METHODS = ("natural_decay", "drag_sail", "propulsive", "graveyard", "none")
_LTAN_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

#: Altitude range (km) accepted per orbit type; outside it the patch is refused.
_ALTITUDE_RANGE: dict[str, tuple[float, float]] = {
    "leo": (150.0, 2000.0), "sso": (150.0, 6000.0), "meo": (2000.0, 35000.0),
    "geo": (35000.0, 36500.0), "gto": (150.0, 40000.0), "heo": (150.0, 400000.0),
}
#: SSO inclination further than this from the J2 value gets a warning (deg).
SSO_TOLERANCE_DEG = 0.5


class OrbitPatch(BaseModel):
    orbit_type: OrbitType | None = None
    altitude_km: float | None = Field(default=None, gt=0)
    inclination_deg: float | None = Field(default=None, ge=0, le=180)
    eccentricity: float | None = Field(default=None, ge=0, lt=1)
    raan_deg: float | None = Field(default=None, ge=0, lt=360)
    ltan: str | None = None
    repeat_cycle_days: int | None = Field(default=None, ge=0)
    mission_duration_years: float | None = Field(default=None, gt=0, le=50)
    deorbit_required: bool | None = None
    #: true: recompute the SSO inclination from the altitude (also the default for an SSO
    #: patch that changes the altitude or type without giving an inclination)
    auto_inclination: bool | None = None

    @field_validator("ltan")
    @classmethod
    def _ltan(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        v = v.strip()
        if re.match(r"^\d:[0-5]\d$", v):
            v = "0" + v
        if not _LTAN_RE.match(v):
            raise ValueError("ltan must be HH:MM (00:00-23:59)")
        return v


class MissionPatch(BaseModel):
    """Partial update of a study's mission definition. Absent fields are left unchanged;
    ``payloads`` and ``ground_stations`` replace the whole list; ``link``, ``constraints``
    and ``mission_need`` are merged key by key."""
    name: str | None = Field(default=None, min_length=1, max_length=200)
    mission_type: MissionType | None = None
    spacecraft_class: str | None = None
    design_lifetime_years: float | None = Field(default=None, gt=0, le=50)
    reliability_target: float | None = Field(default=None, gt=0, le=1)
    # wave 3 (3.A1/3.A5): the mission-success horizon (months) the reliability analysis uses
    success_horizon_months: float | None = Field(default=None, gt=0, le=600)
    target_cost_meur: float | None = Field(default=None, ge=0)
    target_mass_kg: float | None = Field(default=None, gt=0)
    num_spacecraft: int | None = Field(default=None, ge=1, le=10000)
    launch_date_target: str | None = None
    launch_vehicle: str | None = None
    disposal_method: str | None = None
    ground_stations: list[str] | None = None
    constraints: dict[str, Any] | None = None
    orbit: OrbitPatch | None = None
    payloads: list[PayloadRequirements] | None = None
    link: dict[str, Any] | None = None
    mission_need: dict[str, Any] | None = None

    @field_validator("spacecraft_class")
    @classmethod
    def _class(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in SPACECRAFT_CLASSES:
            raise ValueError(f"spacecraft_class must be one of {', '.join(SPACECRAFT_CLASSES)}")
        return v

    @field_validator("payloads")
    @classmethod
    def _payloads(cls, v: list[PayloadRequirements] | None) -> list[PayloadRequirements] | None:
        for p in v or []:
            for f in ("mass_kg", "power_w", "power_peak_w", "data_rate_mbps", "data_volume_per_day_gb"):
                if getattr(p, f) < 0:
                    raise ValueError(f"payload {p.name!r}: {f} must not be negative")
            if not 0 <= p.duty_cycle_percent <= 100:
                raise ValueError(f"payload {p.name!r}: duty_cycle_percent must be 0-100")
            for f in ("gsd_m", "swath_km", "data_per_image_mb"):
                val = getattr(p, f)
                if val is not None and val <= 0:
                    raise ValueError(f"payload {p.name!r}: {f} must be positive")
            if any(w <= 0 for w in p.wavelengths_nm):
                raise ValueError(f"payload {p.name!r}: wavelengths must be positive")
        return v


def sso_inclination_deg(altitude_km: float) -> float:
    from spacecdf_common.physics.orbit import sso_inclination
    return round(sso_inclination(altitude_km), 2)


def _diff(before: Any, after: Any, prefix: str, out: list[str]) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        for k in sorted(set(before) | set(after)):
            _diff(before.get(k), after.get(k), f"{prefix}.{k}" if prefix else k, out)
    elif before != after:
        out.append(prefix)


def apply_mission_patch(study: Study, patch: MissionPatch) -> tuple[list[str], list[str]]:
    """Apply ``patch`` to ``study`` in place (validated as a whole first: on ValueError
    nothing changes). Returns ``(changed_paths, warnings)``."""
    warnings: list[str] = []
    sent = patch.model_fields_set
    req_before = study.requirements.model_dump(mode="json")
    need_before = study.mission_need.model_dump(mode="json")
    req = study.requirements.model_dump()

    for f in ("name", "mission_type", "spacecraft_class", "design_lifetime_years", "reliability_target",
              "success_horizon_months", "target_cost_meur", "target_mass_kg", "num_spacecraft",
              "launch_date_target", "launch_vehicle", "ground_stations"):
        if f in sent and (getattr(patch, f) is not None or f in ("target_cost_meur", "target_mass_kg",
                                                                 "launch_date_target", "launch_vehicle",
                                                                 "success_horizon_months")):
            req[f] = getattr(patch, f)
    if "disposal_method" in sent:
        dm = (patch.disposal_method or "").strip().lower() or None
        if dm is not None and dm not in DISPOSAL_METHODS:
            warnings.append(f"disposal method {dm!r} is not one of {', '.join(DISPOSAL_METHODS)}; kept as entered")
        req["disposal_method"] = dm
        if dm in ("drag_sail", "propulsive", "natural_decay"):
            req["orbit"]["deorbit_required"] = True
    if patch.constraints is not None:
        req["constraints"] = {**(req.get("constraints") or {}), **patch.constraints}
    if patch.payloads is not None:
        req["payloads"] = [p.model_dump() for p in patch.payloads]
    if patch.link is not None:
        unknown = set(patch.link) - set(LinkRequirements.model_fields)
        if unknown:
            raise ValueError(f"unknown link field(s): {', '.join(sorted(unknown))}")
        for k in ("downlink_frequency_mhz", "uplink_frequency_mhz", "downlink_rate_bps", "uplink_rate_bps",
                  "tx_power_w", "system_noise_temp_k", "slant_range_km"):
            v = patch.link.get(k)
            if v is not None and (not isinstance(v, (int, float)) or v <= 0):
                raise ValueError(f"link.{k} must be a positive number")
        req["link"] = {**(req.get("link") or {}), **patch.link}

    orbit = dict(req["orbit"])
    if patch.orbit is not None:
        o_sent = patch.orbit.model_fields_set - {"auto_inclination"}
        for f in o_sent:
            v = getattr(patch.orbit, f)
            if v is None and f not in ("ltan", "raan_deg", "repeat_cycle_days"):
                continue
            orbit[f] = v
        otype = str(getattr(orbit["orbit_type"], "value", orbit["orbit_type"]))
        auto = patch.orbit.auto_inclination
        if auto is None:
            auto = otype == "sso" and "inclination_deg" not in o_sent and bool({"altitude_km", "orbit_type"} & o_sent)
        if auto and otype == "sso":
            orbit["inclination_deg"] = sso_inclination_deg(float(orbit["altitude_km"]))
    otype = str(getattr(orbit["orbit_type"], "value", orbit["orbit_type"]))
    lo, hi = _ALTITUDE_RANGE.get(otype, (100.0, 2_000_000.0))
    if not lo <= float(orbit["altitude_km"]) <= hi:
        raise ValueError(f"altitude {orbit['altitude_km']} km is outside {lo:.0f}-{hi:.0f} km for a {otype.upper()} orbit")
    if otype == "sso":
        ideal = sso_inclination_deg(float(orbit["altitude_km"]))
        if abs(float(orbit["inclination_deg"]) - ideal) > SSO_TOLERANCE_DEG:
            warnings.append(f"inclination {orbit['inclination_deg']}° is not sun-synchronous at "
                            f"{orbit['altitude_km']} km (J2 value {ideal}°)")
    if otype != "sso" and orbit.get("ltan"):
        warnings.append("LTAN only holds for a sun-synchronous orbit")
    # The lifetime is stated twice (requirements and orbit): keep them together.
    if "design_lifetime_years" in sent and patch.design_lifetime_years is not None and not (
            patch.orbit is not None and "mission_duration_years" in patch.orbit.model_fields_set):
        orbit["mission_duration_years"] = patch.design_lifetime_years
    req["orbit"] = orbit

    try:
        new_req = MissionRequirements(**req)
    except Exception as exc:  # pydantic ValidationError
        raise ValueError(str(exc)) from exc

    new_need = study.mission_need
    if patch.mission_need is not None:
        merged = {**study.mission_need.model_dump(), **patch.mission_need}
        try:
            new_need = MissionNeed(**merged)
        except Exception as exc:
            raise ValueError(f"mission_need: {exc}") from exc

    # ── commit ──
    study.requirements = new_req
    study.name = new_req.name or study.name
    objectives_changed = patch.mission_need is not None and "objectives" in patch.mission_need
    study.mission_need = new_need

    changed: list[str] = []
    _diff(req_before, new_req.model_dump(mode="json"), "requirements", changed)
    _diff(need_before, new_need.model_dump(mode="json"), "mission_need", changed)

    # Derived study content that the creation step generated from these values
    if any(c.startswith(("requirements.payloads", "requirements.spacecraft_class",
                         "requirements.design_lifetime_years")) for c in changed):
        # W7.01: the regenerated legacy ConOps model never replaces what the team edited (phases,
        # summary, ground segment, data pipeline); only its auto modes follow the new values.
        # The ConOps document reads the Modes tab, not these auto modes.
        from ..routers.studies import _generate_default_conops
        auto = _generate_default_conops(new_req)
        if study.conops.phases_edited:
            study.conops = study.conops.model_copy(update={"modes": auto.modes})
        else:
            study.conops = auto
    if objectives_changed and new_need.objectives and not study.functional_decomposition.functions:
        # only fill an empty decomposition: a populated one may hold the team's work
        from spacecdf_common.models.functions import generate_starter_decomposition
        study.functional_decomposition = generate_starter_decomposition(
            [o.model_dump() for o in new_need.objectives])
    return changed, warnings
