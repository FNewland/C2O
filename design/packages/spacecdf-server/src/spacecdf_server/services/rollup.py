"""SpaceCDF — the ONE mass / power / form-factor roll-up of a study (W0.3).

Every export, pack, gate and budget view that quotes "the spacecraft mass", "the power" or
"the form factor" takes it from here, so a document can never disagree with the Budget tab.

Rules (the same ones ``services/margin_policy.py`` applies; this module reuses its unit table):

* **Mass**: the most detailed level that carries a value wins (``rule_inputs.leaves_with``), so a
  subsystem estimate and its components are never both counted; ground, operations and user
  segment elements, modes, software and segment/mission nodes are excluded. Each unit counts
  ``mass_kg × quantity``.
  - ``cbe_kg``: nominal (current best estimate);
  - ``with_maturity_kg``: plus each unit's maturity margin (A/B 5 %, C 10 %, D 20 %);
  - ``with_system_margin_kg``: ``with_maturity_kg × (1 + system margin)``, the system margin of the
    gate (MDR/PRR 20 %, SRR/PDR 15 %, CDR 10 %; ``configs/margin_policy.yaml``);
  - ``harness_kg`` / ``total_dry_kg``: the full margin-policy figure (harness 5 % of the
    maturity mass, then the system margin), i.e. what MP-MASS-01 compares with the limit;
  - ``ladder``: ``with_system_margin_kg`` at every gate of the ladder.
* **Power**: ``sum_on_power_w`` is the sum of the units' ON power (``power_avg_w × quantity``, leaf
  rule as above; "Budget › Power"); ``orbit_average_w`` is the operational-orbit load from the
  Modes tab energy balance (``mode_model.energy_balance`` → ``operational_orbit.orbit_average_load_w``;
    only modes of kind nominal / imaging / downlink enter that mix), None
  while no operational mode mix exists. ``orbit_average_with_maturity_w`` applies each unit's power
  maturity margin first (wave 3; ``performance.power_maturity_category``, else the unit's
  category; ESA R-P-11..13) and ``orbit_average_with_margin_w`` adds the system margin to that.
* **System margin**: the ladder step of the gate, unless the study holds a larger one through that
  gate (``study.margin_policy.study_override`` = ``{percent, through_gate, resources, rationale}``,
  wave 3). ``system_margin_source`` says which (``ladder`` | ``study_hold``) and
  ``ladder_percent`` keeps the ladder's own value, so a view can say "20 % (study hold; ladder
  15 %)". ``ladder`` always lists the ladder values.
* **Form factor**: ``rule_inputs.form_factor`` (structure KB part > ``structure.form_factor_u`` >
  element ``performance.form_factor``). ``form_factor_source`` says which; when nothing in the
  design states it, the legacy mass-based guess on the *correct* nominal mass is given with
  source ``"mass_estimate"`` so old documents keep a value.

API::

    from spacecdf_server.services import rollup
    ru = await rollup.compute(study_id, gate=None)      # reads the server caches + modes energy
    ru.mass.cbe_kg, ru.mass.with_maturity_kg, ru.mass.with_system_margin_kg
    ru.power.sum_on_power_w, ru.power.orbit_average_w, ru.form_factor
    ru.as_dict()                                        # JSON-ready
    rollup.rollup_elements(elements, gate=..., orbit_average_w=...)   # pure, for tests and tools

``GET /api/studies/{study_id}/rollup?gate=`` returns ``as_dict()``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from . import margin_policy as mp
from . import rule_config as rc
from .rule_inputs import form_factor as _find_form_factor
from .rule_inputs import kb_component, perf

#: Legacy thresholds of the old exports' ``_form_factor_from_mass`` (only a fallback now).
_MASS_FORM_FACTORS = ((2, "1U"), (4, "2U"), (6, "3U"), (12, "6U"), (24, "12U"))


def form_factor_from_mass(mass_kg: float) -> str:
    """Legacy guess from the total mass. Only used when the design does not state a form factor."""
    for limit, ff in _MASS_FORM_FACTORS:
        if mass_kg < limit:
            return ff
    return "Custom"


@dataclass
class MassRollup:
    cbe_kg: float = 0.0
    with_maturity_kg: float = 0.0
    system_margin_percent: float = 0.0
    ladder_percent: float = 0.0
    system_margin_source: str = "ladder"          # ladder | study_hold
    with_system_margin_kg: float = 0.0
    harness_kg: float = 0.0
    total_dry_kg: float = 0.0
    limit_kg: float | None = None
    limit_source: str | None = None
    ladder: dict[str, float] = field(default_factory=dict)
    units: list[dict] = field(default_factory=list)


@dataclass
class PowerRollup:
    sum_on_power_w: float = 0.0
    sum_on_power_with_maturity_w: float = 0.0
    orbit_average_w: float | None = None
    orbit_average_with_maturity_w: float | None = None
    orbit_average_with_margin_w: float | None = None
    system_margin_percent: float = 0.0
    ladder_percent: float = 0.0
    system_margin_source: str = "ladder"          # ladder | study_hold
    orbit_average_source: str | None = None
    units: list[dict] = field(default_factory=list)


@dataclass
class RollUp:
    study_id: str | None
    gate: str | None
    mass: MassRollup
    power: PowerRollup
    form_factor: str | None
    form_factor_source: str
    warnings: list[str] = field(default_factory=list)
    #: the study's margin hold when one applies at this gate ({percent, through_gate, rationale, label})
    margin_hold: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _form_factor_with_source(elements: list[dict], params: dict | None, cbe_kg: float) -> tuple[str | None, str]:
    ff = _find_form_factor(elements, params or {})
    if ff:
        norm = lambda v: str(v or "").upper().replace(" ", "")  # noqa: E731
        kb_hit = next((kb_component(e) for e in elements
                       if (kb_component(e) or {}).get("category") == "cubesat_structure"
                       and norm((kb_component(e) or {}).get("form_factor")) == ff), None)
        if kb_hit:
            return ff, f"kb:{kb_hit.get('id')}"
        el_hit = next((e for e in elements if norm(perf(e).get("form_factor")) == ff), None)
        return ff, (f"element:{el_hit.get('id')}" if el_hit else "design")
    if cbe_kg > 0:
        return form_factor_from_mass(cbe_kg), "mass_estimate"
    return None, "unknown"


def _mass_limit(form_factor: str | None, target_mass_kg: float | None) -> tuple[float | None, str | None]:
    """CDS limit of the form factor, else the study mass target (as routers/rules.py does)."""
    if form_factor:
        try:
            cds = rc.load("cds_rules")
            lim = (cds.get("max_mass_kg") or {}).get("values", {}).get(form_factor)
            if lim:
                return float(lim), f"cds:{form_factor}"
        except Exception:  # noqa: BLE001 — a broken CDS file must not break the roll-up
            pass
    if target_mass_kg:
        return float(target_mass_kg), "study.target_mass_kg"
    return None, None


def margin_hold(policy: dict | None, gate: str | None, resource: str) -> dict | None:
    """The study's system-margin hold for ``resource`` at ``gate``, or None.

    ``policy`` is ``study.margin_policy``; the hold applies at every ladder gate up to and including
    ``through_gate`` (no ``through_gate``: every gate), to the listed ``resources`` (default mass
    and power), and only when it is above the ladder's step (a hold never lowers the margin)."""
    ov = (policy or {}).get("study_override") if isinstance(policy, dict) else None
    if not isinstance(ov, dict) or ov.get("percent") in (None, ""):
        return None
    try:
        pct = float(ov["percent"])
    except (TypeError, ValueError):
        return None
    if resource not in (ov.get("resources") or ["mass", "power"]):
        return None
    g = (gate or "").strip().lower()
    g = "mdr" if g == "mcr" else g
    through = str(ov.get("through_gate") or "").strip().lower()
    if through and through in mp.LADDER_GATES:
        if g not in mp.LADDER_GATES or mp.LADDER_GATES.index(g) > mp.LADDER_GATES.index(through):
            return None
    ladder_pct = mp.system_margin_percent(g or None, resource)
    if pct <= ladder_pct:
        return None
    return {"percent": pct, "through_gate": through or None, "rationale": ov.get("rationale") or "",
            "ladder_percent": ladder_pct}


def rollup_elements(
    elements: list[dict],
    *,
    gate: str | None = None,
    params: dict[str, Any] | None = None,
    orbit_average_w: float | None = None,
    orbit_average_with_maturity_w: float | None = None,
    orbit_average_source: str | None = None,
    target_mass_kg: float | None = None,
    study_id: str | None = None,
    margin_policy: dict | None = None,
) -> RollUp:
    """Pure roll-up of an element list (dicts as the element cache holds them).

    ``orbit_average_with_maturity_w`` is the operational mix with each unit's power maturity
    margin (the Modes energy balance); without it the nominal figure is used. ``margin_policy``
    is ``study.margin_policy`` (the study's hold, see :func:`margin_hold`)."""
    els = [e for e in elements if not e.get("deleted_at")]
    pol = mp.evaluate_margins(els, params or {}, gate=gate)
    m, p = pol["mass"], pol["power"]
    ladder_m = sys_m = float(m["system_margin_percent"])
    ladder_p = sys_p = float(p["system_margin_percent"])
    hold_m, hold_p = margin_hold(margin_policy, gate, "mass"), margin_hold(margin_policy, gate, "power")
    if hold_m:
        sys_m = hold_m["percent"]
    if hold_p:
        sys_p = hold_p["percent"]
    with_mat = float(m["with_maturity_kg"])

    ladder = {}
    for g in mp.LADDER_GATES:
        pct = mp.system_margin_percent(g, "mass")
        ladder[g] = round(with_mat * (1 + pct / 100), 3)

    ff, ff_src = _form_factor_with_source(els, params, float(m["cbe_kg"]))
    limit, limit_src = _mass_limit(ff if ff_src != "mass_estimate" else None, target_mass_kg)
    mass = MassRollup(
        cbe_kg=round(float(m["cbe_kg"]), 3),
        with_maturity_kg=round(with_mat, 3),
        system_margin_percent=sys_m, ladder_percent=ladder_m,
        system_margin_source="study_hold" if hold_m else "ladder",
        with_system_margin_kg=round(with_mat * (1 + sys_m / 100), 3),
        harness_kg=round(float(m["harness_kg"]), 3),
        total_dry_kg=round(float(m["total_dry_kg"]), 3),
        limit_kg=limit, limit_source=limit_src, ladder=ladder, units=m["units"],
    )
    oa_mat = orbit_average_with_maturity_w if orbit_average_with_maturity_w is not None else orbit_average_w
    power = PowerRollup(
        sum_on_power_w=round(float(p["cbe_w"]), 3),
        sum_on_power_with_maturity_w=round(float(p["with_maturity_w"]), 3),
        orbit_average_w=round(orbit_average_w, 3) if orbit_average_w is not None else None,
        orbit_average_with_maturity_w=round(oa_mat, 3) if oa_mat is not None else None,
        orbit_average_with_margin_w=round(oa_mat * (1 + sys_p / 100), 3) if oa_mat is not None else None,
        system_margin_percent=sys_p, ladder_percent=ladder_p,
        system_margin_source="study_hold" if hold_p else "ladder",
        orbit_average_source=orbit_average_source if orbit_average_w is not None else None,
        units=p["units"],
    )
    warnings = []
    if ff_src == "mass_estimate":
        warnings.append("No structure part or form factor in the design: form factor guessed from the nominal mass.")
    if orbit_average_w is None:
        warnings.append("No operational mode mix yet: orbit-average power not available (Modes tab).")
    hold = hold_m or hold_p
    if hold:
        hold = {**hold, "label": ((rc.load("margin_policy").get("study_override") or {}).get("label")
                                  or {"en": "Study hold", "fr": "Marge retenue par l’étude"})}
    return RollUp(study_id=study_id, gate=gate, mass=mass, power=power, form_factor=ff,
                  form_factor_source=ff_src, warnings=warnings, margin_hold=hold)


def study_elements(study_id: str) -> list[dict]:
    from ..routers.elements import _elements
    return [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


async def _orbit_average(study_id: str, gate: str | None) -> tuple[float | None, float | None, str | None]:
    """Operational-orbit average load from the Modes energy balance: (nominal, with the units'
    power maturity margins, source); Nones without a mode mix."""
    try:
        from ..routers.modes import mode_energy
        res = await mode_energy(study_id, gate=gate)
    except Exception:  # noqa: BLE001 — no modes / no study / rule config problem: not available
        return None, None, None
    ops = res.get("operational_orbit") or {}
    mix = [(m.get("mode_id"), float(m.get("orbit_fraction") or 0)) for m in ops.get("modes") or []]
    tot = sum(f for _, f in mix)
    if not mix or tot <= 0:
        return None, None, None
    # The energy balance's own orbit_average_load_w carries maturity and system margins; the
    # roll-up quotes the nominal (current best estimate) mix, the mix with the maturity margins,
    # and applies the system margin itself.
    rows = {r.get("mode_id"): r for r in res.get("modes") or []}

    def avg(key: str) -> float:
        tot_w = 0.0
        for mid, f in mix:
            r = rows.get(mid) or {}
            v = r.get(key) if r.get(key) is not None else r.get("power_cbe_w")
            tot_w += float(v or 0.0) * f
        return tot_w / tot

    return (avg("power_cbe_w"), avg("power_with_maturity_w"),
            "modes.energy: nominal power of the operational mix (nominal, imaging, downlink kinds)")


async def compute(study_id: str, gate: str | None = None) -> RollUp:
    """Roll-up of a stored study. ``gate`` defaults to the gate the study prepares for."""
    from ..routers.studies import get_study_store
    study = get_study_store().get(study_id)
    if gate is None and study is not None:
        try:
            from ..routers.gates import study_margin_gate
            gate = study_margin_gate(study)
        except Exception:  # noqa: BLE001
            gate = None
    params: dict[str, Any] = {}
    target = None
    if study is not None:
        its = getattr(study, "iterations", None) or []
        if its:
            params.update(getattr(its[-1], "parameter_snapshot", None) or {})
        req = getattr(study, "requirements", None)
        target = getattr(req, "target_mass_kg", None) if req is not None else None
    oa, oa_mat, oa_src = await _orbit_average(study_id, gate)
    return rollup_elements(study_elements(study_id), gate=gate, params=params, orbit_average_w=oa,
                           orbit_average_with_maturity_w=oa_mat, orbit_average_source=oa_src,
                           target_mass_kg=target, study_id=study_id,
                           margin_policy=getattr(study, "margin_policy", None) if study is not None else None)


__all__ = ["MassRollup", "PowerRollup", "RollUp", "compute", "form_factor_from_mass", "margin_hold",
           "rollup_elements", "study_elements"]
