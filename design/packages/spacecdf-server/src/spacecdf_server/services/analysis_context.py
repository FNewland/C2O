"""AnalysisContext — the single, read-only input of every engineering analysis
(SCDF-170 §1.1).

``build_context(study_id, option_id=None)`` assembles, from the persisted
model, everything the design loop, the mission simulation, the ground /
thermal / physics closures and the V&V planner need:

* ``elements`` / ``interfaces`` / ``exchange_items`` / ``functions`` /
  ``allocations`` — dicts exactly as ``routers.elements`` serves them
  (cache first, DB when the cache does not hold the study);
* ``params`` — ``{element_id: {name: EffectiveParam}}`` with the *effective*
  value of every typed parameter (manual / reference override, ``ref`` or
  ``calc`` formula, else computed / column) from ``services.equations``;
* ``flat`` — the ``parameter_path -> value`` dict the agents consume:
  ``element_projection.project_elements_to_params`` over the element tree
  **with effective parameter values overlaid** on the six well-known columns
  (an overridden roll-up on a subsystem replaces the sum of its children).
  ``overridden_paths`` lists the flat paths that inherit at least one manual /
  reference / formula value; ``seed_design_state`` marks those
  ``POSITION_OVERRIDE`` (sticky) so the agents cannot overwrite them
  (SCDF-171 coupling). Computed mirrors never displace a value the last
  design loop produced — they only fill paths the agents have not set;
* ``orbit`` / ``modes`` / ``power`` / ``thermal`` / ``ground_stations`` /
  ``requirements`` — derived views, see the field docs on
  :class:`AnalysisContext`.

``context_hash(ctx, keys)`` is a stable SHA-256 over the named subsets and
is what ``analysis_results`` stores as ``inputs_hash`` for stale detection.

Option scoping (SCDF-172): ``option_id`` selects parameter rows whose
``option_id`` matches and falls back to the baseline rows (``NULL``) for
everything else (``equations.evaluate_study(study_id, option_id)``).
``EffectiveParam.option_id`` is set on the overrides. Elements are not cloned
per option; analysis runs/conflicts are option-scoped.

Public API:
    build_context(study_id, *, option_id=None) -> AnalysisContext
    context_hash(ctx, keys) -> str
    seed_design_state(ctx, *, requirements, conops, knowledge_base) -> DesignState
    HASH_KEYS — the valid names for ``context_hash``
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS

from .element_projection import contributing_elements, project_elements_to_params

logger = logging.getLogger(__name__)

#: owner_domain of parameter rows written by the engineering closures (their outputs)
CLOSURE_OWNED_DOMAINS = frozenset({"mission_simulation", "ground_segment", "physics", "fmeca", "vv"})

HASH_KEYS: tuple[str, ...] = (
    "elements", "params", "modes", "orbit", "power", "thermal", "stations", "requirements", "mission",
)

#: Provenances whose effective value is an *override* of the column / agent value.
OVERRIDE_PROVENANCES = ("manual", "formula", "reference")

_GUARD_RE = re.compile(r"^\s*guard\s*:\s*(?P<cond>[^-\n]+?)\s*->\s*(?P<target>[\w-]+)\s*$", re.I | re.M)


# ── Data classes ────────────────────────────────────────────────────────

@dataclass
class EffectiveParam:
    """One typed parameter on an element, as evaluated by ``services.equations``."""
    element_id: str
    name: str
    value: float | None
    unit: str = ""
    quantity_kind: str = ""
    switch: str = "computed"          # manual | computed | reference
    provenance: str = "column"        # manual | formula | column | agent | reference
    formula: str | None = None
    formula_kind: str | None = None   # ref | calc | None
    owner_domain: str | None = None
    option_id: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def is_override(self) -> bool:
        return self.provenance in OVERRIDE_PROVENANCES and self.value is not None


@dataclass
class ModeSpec:
    """An operational mode built from a ``mode`` element + its member rows."""
    id: str
    name: str
    power_w: float
    duty_cycle_percent: float = 100.0
    active_element_ids: list[str] = field(default_factory=list)
    payload_active: bool = False
    data_rate_bps: float = 0.0
    pointing: str = "nadir"
    guards: list[dict] = field(default_factory=list)   # [{condition, target_mode, priority}]
    source: str = "element"                             # element | conops | default
    # Nov 2026 mode model (services/mode_model.py): per-member rows and the ConOps attributes
    members: list[dict] = field(default_factory=list)   # [{element_id, power_w, duty, data_rate_bps, dissipation_w, state}]
    kind: str = ""                                      # leop|commissioning|nominal|imaging|downlink|safe|survival|custom
    orbit_fraction: float | None = None
    sunlit_only: bool = False
    phase: str = ""                                     # mission phase (launch|leop|commissioning|operations|disposal|...)


@dataclass
class AnalysisContext:
    study_id: str
    option_id: str | None = None
    study: Any = None                                  # spacecdf_common.models.study.Study | None
    latest_design: dict[str, dict] = field(default_factory=dict)  # last design_loop parameters {path: {value, unit, ...}}
    elements: list[dict] = field(default_factory=list)
    interfaces: list[dict] = field(default_factory=list)
    exchange_items: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    allocations: list[dict] = field(default_factory=list)
    params: dict[str, dict[str, EffectiveParam]] = field(default_factory=dict)
    flat: dict[str, Any] = field(default_factory=dict)
    overridden_paths: set[str] = field(default_factory=set)
    orbit: dict[str, Any] = field(default_factory=dict)     # altitude_km, inclination_deg, period_s, eclipse_fraction, sunlight_fraction, raan_deg, ltan, orbit_type
    modes: list[ModeSpec] = field(default_factory=list)
    power: dict[str, Any] = field(default_factory=dict)     # battery_capacity_wh, battery_dod_percent, battery_efficiency, sa_power_bol_w, sa_power_eol_w, sa_area_m2
    thermal: dict[str, Any] = field(default_factory=dict)   # nodes: [{element_id, name, domain, dissipation_w, mass_kg}], emissivity, absorptivity
    ground_stations: list[dict] = field(default_factory=list)
    all_kb_stations: list[dict] = field(default_factory=list)
    requirements: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    link: dict[str, Any] = field(default_factory=dict)       # derived downlink: band, frequency_ghz, source
    warnings: list[str] = field(default_factory=list)

    # -- lookups ---------------------------------------------------------
    @property
    def elements_by_id(self) -> dict[str, dict]:
        return {e["id"]: e for e in self.elements}

    @property
    def mission_root(self) -> dict | None:
        """The ``mission`` element, else the first root element, else ``None``."""
        for e in self.elements:
            if e.get("element_type") == "mission":
                return e
        ids = {e["id"] for e in self.elements}
        for e in self.elements:
            if not e.get("parent_id") or e["parent_id"] not in ids:
                return e
        return None

    def element(self, ref: str) -> dict | None:
        """Element by id, else by unique name (``None`` when ambiguous / unknown)."""
        by_id = self.elements_by_id
        if ref in by_id:
            return by_id[ref]
        hits = [e for e in self.elements if e.get("name") == ref]
        return hits[0] if len(hits) == 1 else None

    def subsystem(self, domain: str) -> dict | None:
        for e in self.elements:
            if e.get("element_type") == "subsystem" and e.get("subsystem_domain") == domain:
                return e
        return None

    def param(self, element_ref: str, name: str) -> EffectiveParam | None:
        el = self.element(element_ref)
        if el is None:
            return None
        return self.params.get(el["id"], {}).get(name)

    def canonical_path(self, path: str) -> str:
        """``el:<name>.<param>`` -> ``el:<id>.<param>``; flat paths unchanged."""
        if not path.startswith("el:"):
            return path
        ref, _, name = path[3:].rpartition(".")
        el = self.element(ref) if ref else None
        return f"el:{el['id']}.{name}" if el else path

    def resolve(self, path: str) -> float | None:
        """Value behind a threshold / input path.

        ``el:<element id or name>.<param>`` reads the effective typed parameter
        (falling back to the element column for well-known names); anything
        else is looked up in ``flat``. ``None`` when unknown or non-numeric.
        """
        if path.startswith("el:"):
            ref, _, name = path[3:].rpartition(".")
            el = self.element(ref) if ref else None
            if el is None or not name:
                return None
            p = self.params.get(el["id"], {}).get(name)
            if p is not None and isinstance(p.value, (int, float)):
                return float(p.value)
            if name in WELL_KNOWN_PARAMETERS and isinstance(el.get(name), (int, float)):
                return float(el[name])
            return None
        v = self.flat.get(path)
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    def get(self, path: str, default: float | None = None) -> float | None:
        """``ComplianceTracker``-compatible accessor (``state.get(path)``)."""
        v = self.resolve(path)
        return default if v is None else v


# ── Loading helpers ─────────────────────────────────────────────────────

async def _load_elements(study_id: str) -> tuple[list[dict], list[dict]]:
    from ..routers import elements as elements_router
    els = [e for e in elements_router._elements.values()
           if e.get("study_id") == study_id and not e.get("deleted_at")]
    from .interface_model import is_active   # rejected links never feed analyses
    ifs = [i for i in elements_router._interfaces.values()
           if i.get("study_id") == study_id and is_active(i)]
    if els:
        return els, ifs
    from ..db.element_repo import load_all_elements
    all_els, all_ifs = await load_all_elements()
    return ([e for e in all_els.values() if e.get("study_id") == study_id and not e.get("deleted_at")],
            [i for i in all_ifs.values() if i.get("study_id") == study_id and is_active(i)])


async def _load_params(study_id: str, option_id: str | None) -> dict[str, dict[str, EffectiveParam]]:
    from ..db import parameter_repo
    from . import equations

    out: dict[str, dict[str, EffectiveParam]] = {}
    # SCDF-172: the equation engine evaluates baseline ∪ option overrides in one
    # pass (option rows shadow baseline rows; formulas see the option's values).
    res = await equations.evaluate_study(study_id, option_id=option_id)
    for p in res.get("parameters", []):
        ep = EffectiveParam(
            element_id=p["element_id"], name=p["name"], value=p.get("effective_value"),
            unit=p.get("unit") or "", quantity_kind=p.get("quantity_kind") or "",
            switch=p.get("value_switch") or "computed", provenance=p.get("provenance") or "column",
            formula=p.get("formula"), formula_kind=p.get("formula_kind"),
            owner_domain=p.get("owner_domain"), option_id=p.get("option_id"),
            errors=list(p.get("errors") or []),
        )
        if ep.switch == "reference" and ep.provenance == "agent":
            ep.provenance = "reference"
        out.setdefault(ep.element_id, {})[ep.name] = ep
    return out


def _effective_elements(elements: list[dict], params: dict[str, dict[str, EffectiveParam]]
                        ) -> tuple[list[dict], set[tuple[str, str]]]:
    """Copy of the elements with override values on the well-known columns,
    plus the set of ``(element_id, column)`` that were overridden."""
    overridden: set[tuple[str, str]] = set()
    out: list[dict] = []
    for e in elements:
        ee = dict(e)
        for name in WELL_KNOWN_PARAMETERS:
            p = params.get(e["id"], {}).get(name)
            if p is not None and p.is_override:
                ee[name] = p.value
                overridden.add((e["id"], name))
        out.append(ee)
    return out, overridden


def _enum_str(v: Any) -> str:
    return str(getattr(v, "value", v) or "")


def _build_orbit(flat: dict, latest: dict, study: Any) -> dict[str, Any]:
    """The orbit every analysis uses.

    Nov 2026 (mission definition editor): the study's mission definition
    (``study.requirements.orbit``, editable with ``PATCH /api/studies/{id}/mission``) wins
    over the last design run's copy, and the derived period / eclipse values of that run
    are reused only when it ran at the same altitude and inclination. Before, an edited
    orbit (e.g. 500 -> 590 km) kept the old period and eclipse until the design loop re-ran.
    An element override in ``flat`` still wins over both.
    """
    def pick_flat(path: str) -> float | None:
        v = flat.get(path)
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    def pick_latest(path: str) -> float | None:
        if path not in latest:
            return None
        v = latest[path].get("value") if isinstance(latest[path], dict) else latest[path]
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    req_orbit = getattr(getattr(study, "requirements", None), "orbit", None)
    alt = pick_flat("orbit.altitude_km")
    if alt is None:
        alt = req_orbit.altitude_km if req_orbit else (pick_latest("orbit.altitude_km") or 500.0)
    inc = pick_flat("orbit.inclination_deg")
    if inc is None:
        inc = req_orbit.inclination_deg if req_orbit else (pick_latest("orbit.inclination_deg") or 97.4)
    l_alt, l_inc = pick_latest("orbit.altitude_km"), pick_latest("orbit.inclination_deg")
    latest_matches = (l_alt is None or abs(l_alt - alt) < 1e-6) and (l_inc is None or abs(l_inc - inc) < 1e-6)

    def pick(path: str) -> float | None:
        v = pick_flat(path)
        if v is None and latest_matches:
            v = pick_latest(path)
        return v

    period = pick("orbit.period_s")
    ecl = pick("orbit.eclipse_fraction")
    sun = pick("orbit.sunlight_fraction")
    if period is None or ecl is None:
        try:
            from spacecdf_common.physics.orbit import compute_orbit_params
            op = compute_orbit_params(alt, inc)
            period = period or op.period_s
            ecl = op.eclipse_fraction if ecl is None else ecl
        except Exception:  # pragma: no cover - defensive
            period, ecl = period or 5700.0, 0.35 if ecl is None else ecl
    if sun is None:
        sun = 1.0 - ecl
    return {
        "altitude_km": alt, "inclination_deg": inc, "period_s": period,
        "eclipse_fraction": ecl, "sunlight_fraction": sun,
        "eccentricity": getattr(req_orbit, "eccentricity", 0.0) if req_orbit else 0.0,
        "raan_deg": getattr(req_orbit, "raan_deg", None) if req_orbit else None,
        "ltan": getattr(req_orbit, "ltan", None) if req_orbit else None,
        "orbit_type": _enum_str(getattr(req_orbit, "orbit_type", "")) if req_orbit else "",
        "contact_time_per_day_s": pick("orbit.contact_time_per_day_s"),
    }


#: Mission-definition link fields (``study.requirements.link``) → flat paths the closures read.
_LINK_TO_FLAT: tuple[tuple[str, str, float], ...] = (
    ("downlink_frequency_mhz", "link.frequency_ghz", 1e-3),
    ("downlink_rate_bps", "link.downlink_rate_bps", 1.0),
    ("tx_power_w", "link.tx_power_w", 1.0),
    ("tx_antenna_gain_dbi", "link.tx_antenna_gain_dbi", 1.0),
)


def _overlay_mission_link(flat: dict, study: Any) -> None:
    """Put the mission definition's link choice on the flat paths the ground / simulation
    closures read (``_pick``: flat before the last design run), unless an element
    parameter already sets the path. Nov 2026: the link-budget tool's "Apply to Design"
    writes ``study.requirements.link``."""
    link = getattr(getattr(study, "requirements", None), "link", None)
    if link is None:
        return
    for field_name, path, scale in _LINK_TO_FLAT:
        v = getattr(link, field_name, None)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 and path not in flat:
            flat[path] = float(v) * scale


#: Band centre frequencies (GHz) for a band named without a frequency; the same table as the
#: ground closure's, so the derived frequency maps back to the same band letter.
_BAND_CENTRE_GHZ: dict[str, float] = {
    "VHF": 0.145, "UHF": 0.437, "L": 1.6, "S": 2.2, "C": 4.0, "X": 8.2, "KU": 12.0, "K": 20.0, "KA": 26.0,
}


def _band_ghz(band: Any) -> float | None:
    if not isinstance(band, str) or not band.strip():
        return None
    key = band.upper().replace("-BAND", "").replace("BAND", "").strip().split("/")[0].strip()
    return _BAND_CENTRE_GHZ.get(key)


def _pos(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 else None


def _ttc_link(eff_elements: list[dict]) -> tuple[float | None, str | None, str, dict[str, float]]:
    """(frequency GHz, band, source, other flat paths) from the space TT&C elements: a frequency in
    ``performance``, else a band in ``performance`` or in the copied KB spec
    (``kb_spec.frequency_band``); with it the downlink rate and transmit power the TT&C elements
    state, since the last design run's values belong to its own (class default) band."""
    freq, band, src = None, None, ""
    extra: dict[str, float] = {}
    for e in eff_elements:
        if e.get("subsystem_domain") != "ttc" or (e.get("segment") or "space") != "space":
            continue
        perf = e.get("performance_json") or e.get("performance") or {}
        perf = perf if isinstance(perf, dict) else {}
        if freq is None:
            for k, scale in (("frequency_ghz", 1.0), ("downlink_frequency_ghz", 1.0),
                             ("downlink_frequency_mhz", 1e-3), ("frequency_mhz", 1e-3)):
                f = _pos(perf.get(k))
                if f is not None:
                    freq, src = f * scale, f"ttc element {e.get('name')}"
                    break
        spec = e.get("kb_spec") if isinstance(e.get("kb_spec"), dict) else {}
        for v in (perf.get("rf_band"), perf.get("frequency_band"), perf.get("band"), spec.get("frequency_band")):
            if band is None and _band_ghz(v) is not None:
                band = str(v)
                src = src or f"ttc element {e.get('name')}"
        if "link.downlink_rate_bps" not in extra:
            for k, scale in (("downlink_rate_bps", 1.0), ("data_rate_bps", 1.0), ("downlink_rate_kbps", 1e3),
                             ("data_rate_kbps", 1e3), ("downlink_rate_mbps", 1e6), ("data_rate_mbps", 1e6)):
                r = _pos(perf.get(k))
                if r is not None:
                    extra["link.downlink_rate_bps"] = r * scale
                    break
        if "link.tx_power_w" not in extra:
            for k in ("tx_power_w", "power_tx_w", "rf_power_w"):
                w = _pos(perf.get(k))
                if w is not None:
                    extra["link.tx_power_w"] = w
                    break
    if freq is None and band is not None:
        freq = _band_ghz(band)
    return freq, band, src, extra


async def _link_cases(study_id: str) -> list[dict]:
    try:
        from ..routers.link_budgets import list_cases
        return await list_cases(study_id)
    except Exception:  # noqa: BLE001 — no link cases is not an error
        logger.debug("link cases unavailable", exc_info=True)
        return []


async def _derive_link(ctx: "AnalysisContext", eff_elements: list[dict]) -> dict[str, Any]:
    """The downlink the analyses use when the mission definition gives no downlink frequency.

    Wave 2 (hand-off X→A): an empty ``requirements.link`` used to leave the ground closure on the
    last design run's class default (X-band), which excluded every UHF station. Now, in order:

    1. ``requirements.link`` with a downlink frequency: nothing to derive (``_overlay_mission_link``);
    2. ``requirements.link.band`` alone: the band centre;
    3. the study's downlink design case (``link_budgets.is_design_case``), else its first downlink
       case: frequency, rate, transmit power and antenna gain of the case;
    4. the TT&C equipment: a frequency in ``performance``, else its band (``rf_band``,
       ``frequency_band``, or the KB spec's ``frequency_band``).

    The values go on the flat paths that are still free, so an element parameter keeps winning,
    and they win over the last design run's values (``ground_closure._pick`` reads flat first).
    """
    link = getattr(getattr(ctx.study, "requirements", None), "link", None)
    if link is not None and _pos(getattr(link, "downlink_frequency_mhz", None)):
        return {"band": getattr(link, "band", None), "frequency_ghz": float(link.downlink_frequency_mhz) * 1e-3,
                "source": "mission_definition"}
    out: dict[str, Any] = {}
    paths: dict[str, float] = {}
    band = getattr(link, "band", None) if link is not None else None
    if _band_ghz(band) is not None:
        out = {"band": band, "frequency_ghz": _band_ghz(band), "source": "mission_definition_band"}
        paths["link.frequency_ghz"] = out["frequency_ghz"]
    else:
        cases = [c for c in await _link_cases(ctx.study_id)
                 if c.get("direction") == "downlink" and _pos(c.get("frequency_mhz"))]
        case = next((c for c in cases if c.get("is_design_case")), cases[0] if cases else None)
        if case is not None:
            out = {"band": case.get("band") or None, "frequency_ghz": float(case["frequency_mhz"]) * 1e-3,
                   "source": f"link_case:{case.get('name') or case.get('id')}",
                   "design_case": bool(case.get("is_design_case"))}
            paths["link.frequency_ghz"] = out["frequency_ghz"]
            for key, path in (("data_rate_bps", "link.downlink_rate_bps"), ("tx_power_w", "link.tx_power_w"),
                              ("tx_antenna_gain_dbi", "link.tx_antenna_gain_dbi")):
                v = case.get(key)
                if isinstance(v, (int, float)) and not isinstance(v, bool) and (key == "tx_antenna_gain_dbi" or v > 0):
                    paths[path] = float(v)
        else:
            f, b, src, extra = _ttc_link(eff_elements)
            if f is not None:
                out = {"band": b, "frequency_ghz": f, "source": src}
                paths["link.frequency_ghz"] = f
                paths.update(extra)
    derived = []
    for path, v in paths.items():
        if path not in ctx.flat:
            ctx.flat[path] = v
            derived.append(path)
    if derived:
        out["derived_paths"] = derived   # provenance: these flat paths came from ``source``
    return out


def _overlay_drag_sail(flat: dict, eff_elements: list[dict], warnings: list[str]) -> None:
    """``deorbit.drag_area_m2`` from the study's deorbit device (wave 2, hand-off L→A).

    The debris agent (design loop) reads this path; without it a study with a drag sail scored
    as if it had none (MDR-EC-10, PRR-EC-12). The area is the element's
    ``performance.deployed_area_m2``, else the KB part's, else the "<n> m2" in its name
    (``services.licensing.disposal_device``). An element parameter on the path still wins."""
    if "deorbit.drag_area_m2" in flat:
        return
    try:
        from .licensing import disposal_device
        dev = disposal_device(eff_elements)
    except Exception:  # noqa: BLE001
        logger.debug("disposal device unavailable", exc_info=True)
        warnings.append("drag sail area unavailable")
        return
    if dev is not None and dev.deployed_area_m2 > 0:
        flat["deorbit.drag_area_m2"] = float(dev.deployed_area_m2)


def _parse_guards(text: str | None) -> list[dict]:
    guards = []
    for i, m in enumerate(_GUARD_RE.finditer(text or "")):
        guards.append({"condition": m.group("cond").strip(), "target_mode": m.group("target"),
                       "priority": 10 - i})
    return guards


async def _load_mode_members(study_id: str, mode_ids: set[str]) -> dict[str, list[dict]]:
    """Members per mode from the in-memory ``_mode_elements`` list + ``mode_elements`` rows."""
    from ..routers import elements as elements_router
    members: dict[str, list[dict]] = {m: [] for m in mode_ids}
    seen: set[tuple[str, str]] = set()
    for m in elements_router._mode_elements:
        if m.get("mode_id") in mode_ids and m.get("is_active", True):
            members[m["mode_id"]].append(dict(m))
            seen.add((m["mode_id"], m["element_id"]))
    try:
        from sqlalchemy import select
        from ..db.engine import get_session_factory
        from ..db.models import ModeElementRow
        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(ModeElementRow).where(ModeElementRow.mode_id.in_(list(mode_ids))))
            for row in res.scalars():
                if not row.is_active or (row.mode_id, row.element_id) in seen:
                    continue
                if getattr(row, "status", "accepted") == "rejected":
                    continue   # a rejected mode-power proposal is not a member
                members[row.mode_id].append({
                    "mode_id": row.mode_id, "element_id": row.element_id, "is_active": True,
                    "power_w_in_mode": row.power_w_in_mode, "duty_cycle_percent": row.duty_cycle_percent,
                    "notes": row.notes, "power_state": getattr(row, "power_state", None),
                    "data_rate_bps": getattr(row, "data_rate_bps", None),
                    "dissipation_w": getattr(row, "dissipation_w", None),
                })
    except Exception:
        logger.debug("mode_elements table unavailable", exc_info=True)
    return members


async def _build_modes(study_id: str, eff_elements: list[dict], study: Any) -> list[ModeSpec]:
    by_id = {e["id"]: e for e in eff_elements}
    mode_els = [e for e in eff_elements if e.get("element_type") == "mode"]
    if mode_els:
        members = await _load_mode_members(study_id, {m["id"] for m in mode_els})
        specs = []
        for m in mode_els:
            total = 0.0
            active: list[str] = []
            rows: list[dict] = []
            payload_active = False
            data_bps = 0.0
            for mem in members.get(m["id"], []):
                el = by_id.get(mem["element_id"])
                if el is None:
                    continue
                pw = mem.get("power_w_in_mode")
                if pw is None:
                    pw = el.get("power_avg_w") or 0.0
                duty = (mem.get("duty_cycle_percent") if mem.get("duty_cycle_percent") is not None else 100.0) / 100.0
                total += float(pw) * duty
                rate = float(mem.get("data_rate_bps") or 0.0) * duty
                data_bps += rate
                rows.append({"element_id": el["id"], "power_w": float(pw), "duty": duty, "data_rate_bps": rate,
                             "dissipation_w": mem.get("dissipation_w"), "state": mem.get("power_state")})
                if mem.get("power_state") == "off" or float(pw) <= 0:
                    continue
                active.append(el["id"])
                if el.get("subsystem_domain") == "payload":
                    payload_active = True
            perf = m.get("performance_json") or m.get("performance") or {}
            if data_bps <= 0:
                data_bps = float(perf.get("data_rate_bps") or 0.0)
            if not active and isinstance(perf.get("power_w"), (int, float)):
                total = float(perf["power_w"])
            if not active and isinstance(m.get("power_avg_w"), (int, float)):
                total = float(m["power_avg_w"])
            specs.append(ModeSpec(
                id=m["id"], name=m["name"], power_w=round(total, 3), active_element_ids=active,
                payload_active=payload_active or bool(perf.get("payload_active")),
                data_rate_bps=data_bps,
                pointing=str(perf.get("pointing") or "nadir"),
                guards=_parse_guards(m.get("description")), source="element",
                members=rows, kind=str(perf.get("mode_kind") or ""),
                orbit_fraction=perf.get("orbit_fraction") if isinstance(perf.get("orbit_fraction"), (int, float)) else None,
                sunlit_only=bool(perf.get("sunlit_only")),
                phase=str(perf.get("phase") or ""),
            ))
        return specs
    conops = getattr(study, "conops", None)
    if conops is not None and getattr(conops, "modes", None):
        return [ModeSpec(id=om.id or om.name, name=om.name or om.id, power_w=float(om.power_w or 0.0),
                         payload_active=bool(om.payload_active), data_rate_bps=float(om.data_rate_mbps or 0) * 1e6,
                         source="conops") for om in conops.modes]
    from .conops_executor import DEFAULT_MODES
    return [ModeSpec(id=dm.name, name=dm.name, power_w=dm.power_draw_w, payload_active=dm.is_payload_active,
                     data_rate_bps=dm.data_rate_bps, pointing=dm.pointing, source="default") for dm in DEFAULT_MODES]


def _first_perf(eff_elements: list[dict], domain: str, key: str) -> float | None:
    for e in eff_elements:
        if e.get("subsystem_domain") != domain:
            continue
        perf = e.get("performance_json") or e.get("performance") or {}
        v = perf.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def _build_power(flat: dict, latest: dict, eff_elements: list[dict]) -> dict[str, Any]:
    def pick(path: str, default: float | None = None) -> float | None:
        v = flat.get(path)
        if v is None and path in latest:
            v = latest[path].get("value") if isinstance(latest[path], dict) else latest[path]
        return float(v) if isinstance(v, (int, float)) else default
    return {
        "battery_capacity_wh": pick("power.battery_capacity_wh"),
        "battery_dod_percent": _first_perf(eff_elements, "power", "dod_percent") or pick("power.battery_dod_percent", 30.0),
        "battery_efficiency": _first_perf(eff_elements, "power", "efficiency") or pick("power.battery_efficiency", 0.9),
        "min_soc_pct": _first_perf(eff_elements, "power", "min_soc_pct") or 20.0,
        "sa_power_bol_w": pick("power.sa_power_bol_w"),
        "sa_power_eol_w": pick("power.sa_power_eol_w"),
        "sa_area_m2": pick("power.sa_area_m2"),
        "heater_power_w": pick("thermal.heater_power_w"),
    }


def _build_thermal(eff_elements: list[dict]) -> dict[str, Any]:
    nodes = []
    for e in eff_elements:
        if e.get("element_type") not in ("subsystem", "component") or (e.get("segment") or "space") != "space":
            continue
        nodes.append({
            "element_id": e["id"], "name": e.get("name"), "domain": e.get("subsystem_domain"),
            "dissipation_w": float(e.get("power_avg_w") or 0.0), "mass_kg": float(e.get("mass_kg") or 0.0),
            "parent_id": e.get("parent_id"),
        })
    return {"nodes": nodes, "emissivity": 0.85, "absorptivity": 0.3}


def _kb_stations() -> list[dict]:
    """The KB station catalogue. Reads only ``ground_stations/networks.yaml`` (parsed once, re-read
    when the file changes) instead of loading the whole KB on every context build."""
    try:
        from spacecdf_common.config.loader import read_yaml_cached
        from spacecdf_kb.loader import DATA_DIR
        path = DATA_DIR / "ground_stations" / "networks.yaml"
        if not path.exists():
            return []
        data = read_yaml_cached(path) or {}
        return list(data.get("stations", data.get("items", [])) or [])
    except Exception:
        logger.warning("KB ground stations unavailable", exc_info=True)
        return []


def _num_or_none(v: Any) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def custom_station(e: dict) -> dict | None:
    """A ground-segment element that carries its own coordinates (no KB entry): the user's
    station (Nov 2026, ``POST /studies/{id}/ground-stations`` with ``lat``/``lon``).
    ``performance`` keys ``lat``/``lon`` (or ``latitude``/``longitude``)."""
    if e.get("segment") != "ground" or e.get("element_type") not in ("system", "component"):
        return None
    perf = e.get("performance_json") or e.get("performance") or {}
    if not isinstance(perf, dict):
        return None
    lat = _num_or_none(perf.get("lat", perf.get("latitude")))
    lon = _num_or_none(perf.get("lon", perf.get("longitude")))
    if lat is None or lon is None:
        return None
    bands = perf.get("bands") or ([perf["band"]] if perf.get("band") else None)
    out = {"id": f"custom-{e['id']}", "name": e.get("name") or "Ground station", "lat": lat, "lon": lon,
           "custom": True}
    for k in ("alt_m", "antenna_m", "min_elevation_deg", "g_over_t_db_k", "eirp_dbw", "operator"):
        if perf.get(k) is not None:
            out[k] = perf[k]
    if bands:
        out["bands"] = list(bands)
    return out


def _select_stations(elements: list[dict], all_stations: list[dict]) -> list[dict]:
    by_id = {s.get("id"): s for s in all_stations}
    by_name = {s.get("name"): s for s in all_stations}
    out: list[dict] = []
    seen: set[str] = set()
    for e in elements:
        if e.get("segment") != "ground":
            continue
        s = None
        if e.get("kb_component_id"):
            s = by_id.get(e["kb_component_id"]) or by_name.get(e["kb_component_id"])
        if s is None:
            s = custom_station(e)   # a station of the user's own, with its coordinates
        if s and s.get("id") not in seen:
            seen.add(s.get("id"))
            out.append({**s, "element_id": e["id"]})
    return out


async def _load_requirements(study_id: str) -> tuple[list[dict], list[dict]]:
    from ..routers import requirements as req_router
    try:
        await req_router.ensure_requirements_loaded()
    except Exception:
        logger.debug("requirement cache hydration failed", exc_info=True)
    reqs = [dict(r) for r in req_router._requirements.values()
            if r.get("study_id") == study_id and r.get("status") != "retired"]
    try:
        from ..db.relation_repo import list_relations_by_study
        rels = await list_relations_by_study(study_id)
    except Exception:
        rels = []
    return reqs, rels


async def _load_latest_design(study_id: str, option_id: str | None) -> dict[str, dict]:
    try:
        from .analysis_results import load_series
        from ..db.analysis_repo import get_last_run
        run = await get_last_run(study_id, "design_loop", option_id)
        if option_id and (not run or run.get("status") != "ok"):
            # SCDF-170 verification fix: an option without a design run of its own
            # inherits the baseline's (reads for X = baseline ∪ X-overrides); before,
            # every agent-derived input (SA power, link rate, ...) vanished in a fresh
            # option and the simulation fell back to the first KB panel it found.
            run = await get_last_run(study_id, "design_loop", None)
        if not run or run.get("status") != "ok":
            return {}
        series = load_series(run.get("series_ref"))
        params = (series or {}).get("parameters") or {}
        return params if isinstance(params, dict) else {}
    except Exception:
        logger.debug("latest design unavailable", exc_info=True)
        return {}


# ── Public API ─────────────────────────────────────────────────────────

async def build_context(study_id: str, *, option_id: str | None = None) -> AnalysisContext:
    """Assemble the analysis context for a study (read-only, never raises for
    missing optional parts — they come back empty with a note in ``warnings``)."""
    from ..routers.studies import get_study_store

    if option_id:
        # SCDF-172: the baseline option's own id addresses the NULL rows.
        try:
            from ..db import option_repo
            option_id = await option_repo.resolve_option_id(option_id)
        except Exception:
            pass   # unknown id → treated as an option without overrides
    ctx = AnalysisContext(study_id=study_id, option_id=option_id)
    ctx.study = get_study_store().get(study_id)

    ctx.elements, ctx.interfaces = await _load_elements(study_id)
    try:
        from ..db.exchange_item_repo import list_exchange_items_by_study
        ctx.exchange_items = await list_exchange_items_by_study(study_id)
    except Exception:
        ctx.warnings.append("exchange items unavailable")
    try:
        from ..db.function_repo import load_all_function_allocations, load_all_functions
        ctx.functions = list((await load_all_functions(study_id)).values())
        ctx.allocations = list((await load_all_function_allocations(study_id)).values())
    except Exception:
        ctx.warnings.append("functions unavailable")

    ctx.params = await _load_params(study_id, option_id)
    ctx.latest_design = await _load_latest_design(study_id, option_id)

    eff_elements, overridden_cols = _effective_elements(ctx.elements, ctx.params)
    ctx.flat = project_elements_to_params(eff_elements, overridden_cols)
    ctx.overridden_paths = {
        path for path, contribs in contributing_elements(eff_elements, overridden_cols).items()
        if any((eid, prop) in overridden_cols for eid, prop in contribs) and path in ctx.flat
    }

    _overlay_mission_link(ctx.flat, ctx.study)
    ctx.link = await _derive_link(ctx, eff_elements)
    _overlay_drag_sail(ctx.flat, eff_elements, ctx.warnings)
    ctx.orbit = _build_orbit(ctx.flat, ctx.latest_design, ctx.study)
    ctx.modes = await _build_modes(study_id, eff_elements, ctx.study)
    ctx.power = _build_power(ctx.flat, ctx.latest_design, eff_elements)
    ctx.thermal = _build_thermal(eff_elements)
    ctx.all_kb_stations = _kb_stations()
    ctx.ground_stations = _select_stations(ctx.elements, ctx.all_kb_stations)
    ctx.requirements, ctx.relations = await _load_requirements(study_id)
    return ctx


def _hash_subset(ctx: AnalysisContext, key: str) -> Any:
    if key == "elements":
        return sorted(
            [e["id"], e.get("parent_id"), e.get("name"), e.get("element_type"), e.get("subsystem_domain"),
             e.get("segment"), e.get("quantity", 1), e.get("kb_component_id"),
             [e.get(c) for c in WELL_KNOWN_PARAMETERS],
             e.get("performance_json") or e.get("performance") or {}, e.get("in_scope", True),
             e.get("position_json"), e.get("dimensions_mm") or e.get("dimensions_json"), e.get("redundancy_type")]
            for e in ctx.elements)
    if key == "params":
        # SCDF-170 verification fix: rows that are pure outputs of a closure
        # (computed, owned by mission_simulation/ground_segment/physics/fmeca/vv)
        # are not inputs of anything — hashing them made every analysis stale
        # as soon as any other closure ran. A manual override / formula on such
        # a row is user state and still counts.
        return sorted(
            [eid, name, p.value, p.switch, p.formula, p.formula_kind]
            for eid, ps in ctx.params.items() for name, p in ps.items()
            if not (p.switch == "computed" and not p.formula and p.owner_domain in CLOSURE_OWNED_DOMAINS))
    if key == "modes":
        return [[m.id, m.name, m.power_w, m.duty_cycle_percent, sorted(m.active_element_ids),
                 m.payload_active, m.data_rate_bps, m.pointing, m.guards] for m in ctx.modes]
    if key == "orbit":
        return ctx.orbit
    if key == "power":
        return ctx.power
    if key == "thermal":
        return ctx.thermal
    if key == "stations":
        # Nov 2026: coordinates too — moving a station of the user's own changes its contacts
        return sorted([s.get("id") or s.get("name") or "", s.get("lat"), s.get("lon"), s.get("min_elevation_deg")]
                      for s in ctx.ground_stations)
    if key == "mission":
        # Nov 2026: the mission definition (PATCH /api/studies/{id}/mission) — payloads,
        # class, lifetime, link, launch / disposal. The name is a label, not an input.
        req = getattr(ctx.study, "requirements", None)
        if req is None or not hasattr(req, "model_dump"):
            return {}
        d = req.model_dump(mode="json")
        d.pop("name", None)
        if str(ctx.link.get("source") or "").startswith("link_case:"):
            d["derived_link"] = ctx.link   # the link case the analyses fall back to (wave 2)
        return d
    if key == "requirements":
        return sorted(
            [r.get("id"), r.get("parent_id"), r.get("threshold_param_path"), r.get("threshold_op"),
             r.get("threshold_value"), r.get("status"), r.get("element_id")]
            for r in ctx.requirements)
    raise KeyError(f"unknown context hash key {key!r}; valid: {HASH_KEYS}")


_NUMERIC_TEXT = re.compile(r"^\s*[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?\s*$")


def _canonical(value: Any) -> Any:
    """Canonical form of a hashed value, so that one model state gives one hash
    however it was loaded (W1.01: a run hashed with ``15`` went stale after a
    restart that reloaded ``15.0`` or ``"15"``).

    * an integral float becomes an int (``15.0`` → ``15``); ``-0.0`` → ``0``;
    * numeric text becomes a number (``"15"`` → ``15``, ``"2.5"`` → ``2.5``);
    * JSON object/array text is decoded (``'{"a": 1}'`` → ``{"a": 1}``), so a
      ``performance_json`` string from the database hashes like the dict the
      element cache holds;
    * dict entries whose value is ``None`` are dropped (absent ≡ null);
    * tuples become lists; booleans stay booleans.
    """
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return str(value)
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text[:1] in ("{", "["):
            try:
                return _canonical(json.loads(text))
            except (ValueError, TypeError):
                return value
        if _NUMERIC_TEXT.match(text):
            try:
                return _canonical(float(text)) if any(c in text for c in ".eE") else int(text)
            except (ValueError, OverflowError):
                return value
        return value
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in value.items() if v is not None}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, default=str))
    if hasattr(value, "model_dump"):
        try:
            return _canonical(value.model_dump(mode="json"))
        except Exception:
            return str(value)
    if hasattr(value, "value") and type(value).__module__ != "builtins":   # enums
        return _canonical(value.value)
    return value


def context_hash(ctx: AnalysisContext, keys: list[str] | tuple[str, ...]) -> str:
    """Stable SHA-256 (hex) over the named context subsets (see ``HASH_KEYS``).

    The same model state always yields the same hash; a change in any named
    subset changes it. Unknown keys raise ``KeyError``. Values are passed
    through :func:`_canonical` first, so ``15``, ``15.0`` and ``"15"`` (and a
    JSON string versus its decoded dict) hash the same.
    """
    payload = {k: _canonical(_hash_subset(ctx, k)) for k in sorted(set(keys))}
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def seed_design_state(ctx: AnalysisContext, *, requirements: Any = None, conops: Any = None,
                      knowledge_base: Any = None):
    """``DesignState`` for the orchestrator, seeded from the context (SCDF-171).

    Precedence: overridden flat paths (``POSITION_OVERRIDE``, sticky) >
    last design-loop values (``COMPUTED``) > non-overridden flat paths
    (``COMPUTED``, only where the last loop has no value).
    """
    from spacecdf_common.agents.base import DesignState
    from spacecdf_common.models.parameter import ParameterSource, ParameterValue

    params: dict[str, ParameterValue] = {}

    def _pv(path: str, value: Any, source: ParameterSource, unit: str = "") -> ParameterValue | None:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            return None
        return ParameterValue(id=path, name=path, value=value, unit=unit, domain=path.split(".")[0],
                              source=source, confidence=1.0 if source.is_sticky else 0.7,
                              margin_percent=0.0, updated_by="analysis_context")

    for path, entry in ctx.latest_design.items():
        value = entry.get("value") if isinstance(entry, dict) else entry
        pv = _pv(path, value, ParameterSource.COMPUTED, (entry.get("unit") or "") if isinstance(entry, dict) else "")
        if pv is not None:
            params[path] = pv
    for path, value in ctx.flat.items():
        if path in ctx.overridden_paths:
            pv = _pv(path, value, ParameterSource.POSITION_OVERRIDE)
        elif path in params:
            continue
        else:
            pv = _pv(path, value, ParameterSource.COMPUTED)
        if pv is not None:
            params[path] = pv

    req_dict = requirements.model_dump() if hasattr(requirements, "model_dump") else (requirements or {})
    return DesignState(parameters=params, requirements=req_dict, knowledge_base=knowledge_base, conops=conops)
