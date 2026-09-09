"""Mission simulation closure (SCDF-173, design SCDF-170 §2.1).

Wraps ``conops_executor.simulate_orbit`` with everything built from the
:class:`AnalysisContext` instead of the executor's built-in defaults:

* modes from ``ctx.modes`` (power = sum of active elements' power in mode);
  a study without modes gets a 3-mode default derived from the subsystem
  powers (safe = platform x 0.6, nominal = platform + payload, downlink =
  nominal + TT&C peak) and a warning;
* guards from the mode notes (``guard: soc < 20 -> safe``) else the SoC /
  temperature defaults, with the SoC threshold = the battery ``min_soc_pct``;
* orbit / power / thermal from ``ctx.orbit`` / ``ctx.power`` / ``ctx.thermal``
  (KB component values already overlay these in the context);
* contacts: the ground closure's last run (``gs_contact_min_per_day``) when
  present, else ``orbit.contact_time_per_day_s``, spread uniformly — one
  window at the start of every orbit (that is where the executor places it).

Executor facts this module relies on (``conops_executor.simulate_orbit``):
fixed 30 s step, starts at 80 % SoC, one continuous run for ``duration_s``
(so ``n_orbits`` orbits are simulated in one call and the state is
continuous), data accumulates only in modes with ``is_payload_active`` and is
drained only in the mode named exactly ``"downlink"`` during contact, and
the guard fires again every step while its condition holds. ``dt_s`` is
therefore only the *floor* of the output resampling step.

Public API:
    AnalysisOutput(parameters, conflicts, series, summary, warnings)
    run_mission_simulation(ctx, *, n_orbits=15, dt_s=10) -> AnalysisOutput
    OUTPUT_PARAMETERS — the names written on the mission root
    CONFLICT_CODES
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from .analysis_context import AnalysisContext, ModeSpec
from .analysis_results import Conflict, ParamWrite
from .conops_executor import (
    ConOpsMode,
    ModeGuard,
    OrbitParams,
    PowerParams,
    ThermalParams,
    TimeSeriesResult,
    SIGMA,
    _in_sunlight,
    simulate_orbit,
)

logger = logging.getLogger(__name__)

ANALYSIS = "mission_simulation"
MAX_SERIES_POINTS = 2000
EXECUTOR_DT_S = 30.0
SAFE_TIME_WARN_PCT = 10.0

OUTPUT_PARAMETERS: tuple[str, ...] = (
    "sim_min_soc_pct", "sim_max_dod_pct", "sim_energy_balance_wh_per_orbit",
    "sim_data_buffer_max_gb", "sim_data_backlog_end_gb", "sim_heater_energy_wh_per_orbit",
    "sim_time_in_safe_pct", "sim_orbits",
)
CONFLICT_CODES: tuple[str, ...] = (
    "SIM_SOC_BELOW_MIN", "SIM_DOD_EXCEEDED", "SIM_ENERGY_NEGATIVE", "SIM_DATA_OVERFLOW",
    "SIM_DATA_BACKLOG", "SIM_SAFE_TIME",
)

#: Executor defaults used when the model gives nothing (each adds a warning).
FALLBACK_BATTERY_WH = 40.0
FALLBACK_DOWNLINK_BPS = 2e6
FALLBACK_HEATER_W = 5.0
SPECIFIC_HEAT_J_PER_KG_K = 900.0     # aluminium-dominated spacecraft
EOL_FACTOR = 0.85                    # SA EOL / BOL when only BOL is known
STATION_PASSES_PER_DAY = 4           # LEO / polar station estimate when no closure has run
STATION_PASS_S = 480.0


@dataclass
class AnalysisOutput:
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    series: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class _SimInputs:
    modes: list[ConOpsMode]
    display: dict[str, str]           # executor mode name -> model mode name
    nominal: str
    safe: str
    downlink: str | None
    guards: list[ModeGuard]
    orbit: OrbitParams
    power: PowerParams
    thermal: ThermalParams
    schedule: list[dict]
    min_soc_pct: float
    dod_limit_pct: float | None
    storage_gb: float | None
    contact_s_per_orbit: float
    contact_source: str
    battery_element_id: str | None
    sa_element_id: str | None
    area_source: str = ""
    warnings: list[str] = field(default_factory=list)


# ── input helpers ───────────────────────────────────────────────────────

def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _pick(ctx: AnalysisContext, *paths: str) -> float | None:
    """First numeric value among ``paths`` in ``flat`` then ``latest_design``."""
    for p in paths:
        v = _num(ctx.flat.get(p))
        if v is not None:
            return v
    for p in paths:
        entry = ctx.latest_design.get(p)
        v = _num(entry.get("value") if isinstance(entry, dict) else entry)
        if v is not None:
            return v
    return None


def _perf(e: dict) -> dict:
    perf = e.get("performance_json") or e.get("performance") or {}
    return perf if isinstance(perf, dict) else {}


def _leaves(ctx: AnalysisContext) -> list[dict]:
    """Space-segment subsystem / component leaves (what carries the power columns)."""
    parents = {e.get("parent_id") for e in ctx.elements}
    return [e for e in ctx.elements
            if e.get("element_type") in ("subsystem", "component")
            and (e.get("segment") or "space") == "space"
            and e["id"] not in parents]


def _eff_col(ctx: AnalysisContext, e: dict, name: str) -> float:
    p = ctx.params.get(e["id"], {}).get(name)
    if p is not None and p.value is not None and p.is_override:
        return float(p.value)
    return _num(e.get(name)) or 0.0


def _override(ctx: AnalysisContext, e: dict | None, *names: str) -> float | None:
    """Manual / reference / formula value of a typed parameter on ``e`` (the
    context overlays overrides on the well-known columns only, so component
    performance values such as ``capacity_wh`` are honoured here)."""
    if e is None:
        return None
    for name in names:
        p = ctx.params.get(e["id"], {}).get(name)
        if p is not None and p.is_override:
            v = _num(p.value)
            if v is not None:
                return v
    return None


def _first_element(ctx: AnalysisContext, domain: str, *perf_keys: str) -> dict | None:
    for e in ctx.elements:
        if e.get("subsystem_domain") == domain and any(k in _perf(e) for k in perf_keys):
            return e
    return None


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name.strip().lower()).strip("_") or "mode"


def _default_modes(ctx: AnalysisContext) -> tuple[list[ModeSpec], str]:
    leaves = _leaves(ctx)
    platform = sum(_eff_col(ctx, e, "power_avg_w") for e in leaves if e.get("subsystem_domain") != "payload")
    payload = sum(_eff_col(ctx, e, "power_avg_w") for e in leaves if e.get("subsystem_domain") == "payload")
    ttc = [e for e in leaves if e.get("subsystem_domain") == "ttc"]
    ttc_peak = sum(_eff_col(ctx, e, "power_peak_w") or _eff_col(ctx, e, "power_avg_w") * 2.0 for e in ttc)
    if ttc_peak <= 0:
        ttc_peak = _pick(ctx, "link.ttc_power_w") or 0.0
    if platform <= 0:
        platform = _pick(ctx, "power.total_eclipse_w") or 10.0
    nominal = platform + payload
    modes = [
        ModeSpec(id="safe", name="Safe", power_w=round(platform * 0.6, 3), source="derived"),
        ModeSpec(id="nominal", name="Nominal", power_w=round(nominal, 3), payload_active=True, source="derived"),
        ModeSpec(id="downlink", name="Downlink", power_w=round(nominal + ttc_peak, 3), source="derived"),
    ]
    note = (f"study has no operational modes: derived Safe {modes[0].power_w:.1f} W (platform x 0.6), "
            f"Nominal {modes[1].power_w:.1f} W (platform {platform:.1f} + payload {payload:.1f}), "
            f"Downlink {modes[2].power_w:.1f} W (nominal + TT&C peak {ttc_peak:.1f})")
    return modes, note


def _classify(specs: list[ModeSpec]) -> tuple[str, str, str | None]:
    """(nominal, safe, downlink) model mode names."""
    def find(*words: str) -> str | None:
        for m in specs:
            n = m.name.lower()
            if any(w in n for w in words):
                return m.name
        return None
    safe = find("safe", "survival") or min(specs, key=lambda m: m.power_w).name
    downlink = find("downlink", "contact", "comm", "tx")
    nominal = find("nominal", "imaging", "science", "payload", "mission")
    if nominal is None:
        pay = [m for m in specs if m.payload_active and m.name not in (safe, downlink)]
        others = [m for m in specs if m.name not in (safe, downlink)]
        nominal = (pay or others or specs)[0].name
    return nominal, safe, downlink


def _build_inputs(ctx: AnalysisContext, n_orbits: int, contact_override_s_per_day: float | None,
                  contact_source: str) -> _SimInputs:
    warnings: list[str] = []
    specs = [m for m in ctx.modes if m.source != "default"]
    if not specs:
        specs, note = _default_modes(ctx)
        warnings.append(note)
    nominal_name, safe_name, downlink_name = _classify(specs)

    # executor names: the downlink mode MUST be called "downlink" (data drain), safe keeps a slug
    exec_name: dict[str, str] = {}
    for m in specs:
        if m.name == downlink_name:
            exec_name[m.name] = "downlink"
        else:
            base = _slug(m.name)
            if base == "downlink":
                base = "downlink_mode"
            while base in exec_name.values():
                base += "_"
            exec_name[m.name] = base
    display = {v: k for k, v in exec_name.items()}

    # data rates
    payload_bps = _pick(ctx, "payload.data_rate_bps")
    if payload_bps is None:
        mbps = _pick(ctx, "payload.data_rate_mbps")
        payload_bps = mbps * 1e6 if mbps is not None else None
    if payload_bps is None:
        pl = _first_element(ctx, "payload", "data_rate_bps", "data_rate_mbps")
        if pl is not None:
            perf = _perf(pl)
            payload_bps = _num(perf.get("data_rate_bps")) or ((_num(perf.get("data_rate_mbps")) or 0.0) * 1e6 or None)
    if payload_bps is None:
        gb_day = _pick(ctx, "data.generated_per_day_gb")
        payload_bps = gb_day * 8e9 / 86400.0 if gb_day is not None else None
    downlink_bps = _pick(ctx, "link.downlink_rate_bps")
    if downlink_bps is None:
        mbps = _pick(ctx, "link.data_rate_mbps", "link.downlink_rate_mbps")
        downlink_bps = mbps * 1e6 if mbps is not None else None

    modes: list[ConOpsMode] = []
    for m in specs:
        rate = m.data_rate_bps
        if m.name == downlink_name:
            rate = -abs(rate) if rate else -(downlink_bps or 0.0)
            if not rate:
                rate = -FALLBACK_DOWNLINK_BPS
                warnings.append(f"no downlink rate in the model (link.downlink_rate_bps); assumed {FALLBACK_DOWNLINK_BPS/1e6:.0f} Mbps")
        elif m.payload_active and rate <= 0 and payload_bps:
            rate = payload_bps
        modes.append(ConOpsMode(name=exec_name[m.name], power_draw_w=max(0.0, m.power_w),
                                pointing=m.pointing or "nadir", data_rate_bps=rate,
                                is_payload_active=bool(m.payload_active)))
    # executor starts in modes[0]: make it the nominal mode
    modes.sort(key=lambda cm: 0 if cm.name == exec_name[nominal_name] else 1)
    if downlink_name is None:
        warnings.append("no downlink mode in the model: data is never drained")

    # power
    battery_el = _first_element(ctx, "power", "capacity_wh")
    cap = _override(ctx, battery_el, "capacity_wh", "battery_capacity_wh")
    if cap is None:
        cap = _num(ctx.power.get("battery_capacity_wh"))
    if cap is None or cap <= 0:
        cap = FALLBACK_BATTERY_WH
        warnings.append(f"no battery capacity in the model (power.battery_capacity_wh); assumed {cap:.0f} Wh")
    min_soc = _num(ctx.power.get("min_soc_pct")) or 20.0
    dod_limit = _num(ctx.power.get("battery_dod_percent"))
    sa_el = _first_element(ctx, "power", "sa_power_eol_w", "sa_power_bol_w", "power_eol_w", "power_bol_w")
    sa_eol = _override(ctx, sa_el, "sa_power_eol_w", "power_eol_w")
    if sa_eol is None:
        sa_eol = _num(ctx.power.get("sa_power_eol_w"))
    if sa_eol is None:
        bol = _num(ctx.power.get("sa_power_bol_w"))
        if bol is not None:
            sa_eol = bol * EOL_FACTOR
            warnings.append(f"SA EOL power taken as {EOL_FACTOR:.2f} x BOL ({bol:.1f} W)")
    if sa_eol is None and sa_el is not None:
        p = _perf(sa_el)
        sa_eol = _num(p.get("sa_power_eol_w")) or _num(p.get("power_eol_w")) or \
            ((_num(p.get("sa_power_bol_w")) or _num(p.get("power_bol_w")) or 0.0) * EOL_FACTOR) or None
    sun = _num(ctx.orbit.get("sunlight_fraction")) or 0.65
    if sa_eol is None:
        nominal_w = next(cm.power_draw_w for cm in modes if cm.name == exec_name[nominal_name])
        sa_eol = nominal_w / sun * 1.1
        warnings.append(f"no solar-array power in the model (power.sa_power_eol_w); assumed {sa_eol:.1f} W "
                        f"(nominal load / sunlight fraction x 1.1) — run the design loop to size it")
    heater = _num(ctx.power.get("heater_power_w"))
    if heater is None:
        heater = _pick(ctx, "thermal.heater_power_w")
    if heater is None:
        heater = FALLBACK_HEATER_W
    power = PowerParams(sa_power_eol_w=sa_eol, battery_capacity_wh=cap, heater_power_w=heater)

    # orbit + contacts
    period = _num(ctx.orbit.get("period_s")) or 5700.0
    ecl = _num(ctx.orbit.get("eclipse_fraction"))
    ecl = 0.35 if ecl is None else min(max(ecl, 0.0), 0.95)
    orbits_per_day = 86400.0 / period
    per_day = contact_override_s_per_day
    if per_day is None:
        per_day = _num(ctx.orbit.get("contact_time_per_day_s")) or _pick(ctx, "orbit.contact_time_per_day_s")
        contact_source = "orbit.contact_time_per_day_s" if per_day is not None else "none"
    if per_day is None and ctx.ground_stations:
        per_day = len(ctx.ground_stations) * STATION_PASSES_PER_DAY * STATION_PASS_S
        contact_source = f"{len(ctx.ground_stations)} station(s) x {STATION_PASSES_PER_DAY} passes x {STATION_PASS_S:.0f} s (estimate)"
        warnings.append(f"no contact time in the model: assumed {per_day / 60:.0f} min/day from {contact_source}; run the ground closure")
    if per_day is None:
        per_day = 0.0
        warnings.append("no contact time in the model (orbit.contact_time_per_day_s, ground closure, stations): no downlink windows")
    contact_s = min(per_day / orbits_per_day, period * 0.5)
    orbit = OrbitParams(altitude_km=_num(ctx.orbit.get("altitude_km")) or 500.0,
                        inclination_deg=_num(ctx.orbit.get("inclination_deg")) or 97.4,
                        eclipse_fraction=ecl, period_s=period, contact_time_per_orbit_s=contact_s)

    # thermal (single node)
    mass = sum(float(n.get("mass_kg") or 0.0) for n in (ctx.thermal.get("nodes") or []))
    if mass <= 0:
        mass = _pick(ctx, "mass.dry_mass_kg") or 5.0
    eps_ = _num(ctx.thermal.get("emissivity")) or 0.85
    alpha = _num(ctx.thermal.get("absorptivity")) or 0.3
    area = _pick(ctx, "thermal.radiator_area_m2")
    area_source = "thermal.radiator_area_m2"
    if area is None:
        # size the single-node radiator so the orbit-mean equilibrium at the nominal
        # dissipation is ~20 C (the executor default 0.04 m2 is tuned for a 45 W bus)
        nominal_w = next(cm.power_draw_w for cm in modes if cm.name == exec_name[nominal_name])
        q_int = nominal_w * 0.6
        sink = eps_ * SIGMA * (20.0 + 273.15) ** 4 - alpha * 1361.0 * 0.25 * (1.0 - ecl)
        area = max(0.005, q_int / max(sink, 50.0))
        area_source = "sized for 20 C orbit-mean equilibrium at the nominal load"
    thermal = ThermalParams(capacitance_j_per_k=mass * SPECIFIC_HEAT_J_PER_KG_K, radiator_area_m2=area,
                            emissivity=eps_, absorptivity=alpha)

    # guards
    guards: list[ModeGuard] = []
    for m in specs:
        for g in m.guards or []:
            target = g.get("target_mode") or ""
            tgt_model = next((s.name for s in specs if s.name.lower() == target.lower() or _slug(s.name) == _slug(target)), None)
            if tgt_model is None:
                warnings.append(f"guard '{g.get('condition')}' on mode {m.name} targets unknown mode {target!r}; ignored")
                continue
            guards.append(ModeGuard(condition=str(g.get("condition")), target_mode=exec_name[tgt_model],
                                    priority=int(g.get("priority") or 0)))
    if not guards:
        guards = [ModeGuard(condition=f"soc < {min_soc:g}", target_mode=exec_name[safe_name], priority=10),
                  ModeGuard(condition="temp > 65", target_mode=exec_name[safe_name], priority=9)]

    # schedule: downlink at the start of every orbit (the executor's contact window), nominal after
    schedule: list[dict] = []
    for k in range(n_orbits):
        t0 = k * period
        if downlink_name is not None and contact_s > 0:
            schedule.append({"time_s": t0, "mode": "downlink"})
            schedule.append({"time_s": t0 + contact_s, "mode": exec_name[nominal_name]})
        else:
            schedule.append({"time_s": t0, "mode": exec_name[nominal_name]})

    storage = None
    obc = _first_element(ctx, "obc", "storage_gb", "memory_gb") or _first_element(ctx, "data", "storage_gb")
    if obc is not None:
        storage = _num(_perf(obc).get("storage_gb")) or _num(_perf(obc).get("memory_gb"))
    if storage is None:
        storage = _pick(ctx, "data.storage_gb", "data.storage_capacity_gb")

    return _SimInputs(
        modes=modes, display=display, nominal=exec_name[nominal_name], safe=exec_name[safe_name],
        downlink="downlink" if downlink_name else None, guards=guards, orbit=orbit, power=power,
        thermal=thermal, schedule=schedule, min_soc_pct=min_soc, dod_limit_pct=dod_limit,
        storage_gb=storage, contact_s_per_orbit=contact_s, contact_source=contact_source,
        battery_element_id=battery_el["id"] if battery_el else None,
        sa_element_id=sa_el["id"] if sa_el else None, area_source=area_source, warnings=warnings,
    )


async def _contact_from_ground_closure(ctx: AnalysisContext) -> tuple[float | None, str]:
    """``(seconds per day, source)`` from the last ground-closure run, if any."""
    try:
        from .analysis_results import get_last_run
        for name in ("ground_segment", "ground"):
            run = await get_last_run(ctx.study_id, name, ctx.option_id, ctx=ctx)
            if not run or run.get("status") != "ok":
                continue
            s = run.get("summary") or {}
            minutes = _num(s.get("gs_contact_min_per_day"))
            if minutes is None:
                minutes = _num(s.get("contact_min_per_day"))
            if minutes is not None:
                return minutes * 60.0, f"ground closure run {run['id']}"
    except Exception:
        logger.debug("ground closure lookup failed", exc_info=True)
    return None, "none"


# ── post-processing ─────────────────────────────────────────────────────

def _downsample(n: int, dt_s: float) -> int:
    stride = max(1, int(math.ceil(n / MAX_SERIES_POINTS)), int(math.ceil(dt_s / EXECUTOR_DT_S)))
    return stride


def _fmt_mode(inp: _SimInputs, name: str) -> str:
    return inp.display.get(name, name)


def _hms(t: float) -> str:
    h, rem = divmod(int(t), 3600)
    return f"{h:02d}:{rem // 60:02d}"


def _post_process(ctx: AnalysisContext, inp: _SimInputs, res: TimeSeriesResult, n_orbits: int,
                  dt_s: float) -> AnalysisOutput:
    out = AnalysisOutput(warnings=list(inp.warnings))
    n = len(res.time_s)
    if n == 0:
        out.warnings.append("simulation produced no samples")
        return out
    dt = EXECUTOR_DT_S
    period = inp.orbit.period_s
    mode_w = {m.name: m.power_draw_w for m in inp.modes}

    p_gen: list[float] = []
    p_load: list[float] = []
    heater_wh = 0.0
    for t, mode, temp in zip(res.time_s, res.mode, res.temp_c):
        g = inp.power.sa_power_eol_w if _in_sunlight(t, inp.orbit) else 0.0
        load = mode_w.get(mode, 0.0)
        if temp < 0.0:
            load += inp.power.heater_power_w
            heater_wh += inp.power.heater_power_w * dt / 3600.0
        p_gen.append(g)
        p_load.append(load)
    net_wh_total = sum(g - l for g, l in zip(p_gen, p_load)) * dt / 3600.0
    sim_s = res.time_s[-1] + dt
    orbits_done = max(sim_s / period, 1e-9)
    energy_balance = net_wh_total / orbits_done
    heater_per_orbit = heater_wh / orbits_done

    min_soc = min(res.soc_pct)
    i_min = res.soc_pct.index(min_soc)
    max_dod = 100.0 - min_soc
    safe_steps = sum(1 for m in res.mode if m == inp.safe)
    safe_pct = 100.0 * safe_steps / n
    buf_gb = [mb / 8000.0 for mb in res.data_buffer_mbit]     # Mbit -> GB (1 GB = 8000 Mbit)
    buf_max = max(buf_gb)
    buf_end = buf_gb[-1]
    buf_mid = buf_gb[n // 2]
    cap = inp.power.battery_capacity_wh

    # parameters
    P = out.parameters
    P.append(ParamWrite("sim_min_soc_pct", round(min_soc, 2), unit="%", description="Minimum battery state of charge over the simulated orbits"))
    P.append(ParamWrite("sim_max_dod_pct", round(max_dod, 2), unit="%", description="Maximum depth of discharge (100 - min SoC)"))
    P.append(ParamWrite("sim_energy_balance_wh_per_orbit", round(energy_balance, 3), unit="Wh", description="Mean generated minus consumed energy per orbit (unclamped)"))
    P.append(ParamWrite("sim_data_buffer_max_gb", round(buf_max, 4), unit="GB", description="Peak on-board data buffer"))
    P.append(ParamWrite("sim_data_backlog_end_gb", round(buf_end, 4), unit="GB", description="Data still on board at the end of the simulation"))
    P.append(ParamWrite("sim_heater_energy_wh_per_orbit", round(heater_per_orbit, 3), unit="Wh", description="Heater energy per orbit (single-node thermal model)"))
    P.append(ParamWrite("sim_time_in_safe_pct", round(safe_pct, 2), unit="%", description="Share of the simulated time spent in the safe mode"))
    P.append(ParamWrite("sim_orbits", float(n_orbits), unit="", description="Number of orbits simulated"))

    # conflicts
    C = out.conflicts
    bat_ids = [inp.battery_element_id] if inp.battery_element_id else []
    sa_ids = [inp.sa_element_id] if inp.sa_element_id else []
    if min_soc < inp.min_soc_pct:
        # keep the observed absolute drain above the threshold, and at least cover one
        # eclipse in the nominal mode (the observed minimum already benefits from the safe-mode guard)
        need_obs = cap * (100.0 - min_soc) / max(100.0 - inp.min_soc_pct, 1.0)
        eclipse_wh = (mode_w.get(inp.nominal, 0.0) + (inp.power.heater_power_w if heater_per_orbit > 0 else 0.0)) \
            * inp.orbit.eclipse_fraction * period / 3600.0
        need = max(need_obs, eclipse_wh / max(1.0 - inp.min_soc_pct / 100.0, 0.05))
        fixes = [f"raise battery capacity to {need:.1f} Wh (now {cap:.1f} Wh)"]
        if energy_balance < 0:
            fixes.append(f"or restore a positive energy balance ({energy_balance:+.2f} Wh/orbit)")
        C.append(Conflict("critical", "SIM_SOC_BELOW_MIN",
                          f"Battery SoC {min_soc:.1f} % below minimum {inp.min_soc_pct:g} %",
                          f"Minimum {min_soc:.1f} % reached at t={_hms(res.time_s[i_min])} (orbit {int(res.time_s[i_min] // period) + 1}) "
                          f"in mode {_fmt_mode(inp, res.mode[i_min])}; battery {cap:.1f} Wh, SA EOL {inp.power.sa_power_eol_w:.1f} W.",
                          element_ids=bat_ids, suggested_fix="; ".join(fixes)))
    elif inp.dod_limit_pct is not None and max_dod > inp.dod_limit_pct:
        need = cap * max_dod / inp.dod_limit_pct
        C.append(Conflict("major", "SIM_DOD_EXCEEDED",
                          f"Depth of discharge {max_dod:.1f} % exceeds design limit {inp.dod_limit_pct:g} %",
                          f"Deepest discharge at t={_hms(res.time_s[i_min])} in mode {_fmt_mode(inp, res.mode[i_min])}.",
                          element_ids=bat_ids, suggested_fix=f"raise battery capacity to {need:.1f} Wh or cut eclipse load"))
    if energy_balance < 0:
        sun_h = inp.orbit.period_s * (1.0 - inp.orbit.eclipse_fraction) / 3600.0
        extra_w = -energy_balance / max(sun_h, 1e-6)
        C.append(Conflict("major", "SIM_ENERGY_NEGATIVE",
                          f"Energy balance {energy_balance:+.2f} Wh per orbit",
                          f"Generation {inp.power.sa_power_eol_w:.1f} W in sunlight ({(1 - inp.orbit.eclipse_fraction) * 100:.0f} % of the orbit) does not "
                          f"cover the loads (nominal {mode_w.get(inp.nominal, 0):.1f} W); the battery drains {-energy_balance:.2f} Wh every orbit.",
                          element_ids=sa_ids,
                          suggested_fix=f"raise SA EOL power to {inp.power.sa_power_eol_w + extra_w:.1f} W (+{extra_w:.1f} W) "
                                        f"or reduce the average load by {-energy_balance / (period / 3600.0):.1f} W"))
    if inp.storage_gb is not None and buf_max > inp.storage_gb:
        C.append(Conflict("major", "SIM_DATA_OVERFLOW",
                          f"Data buffer {buf_max:.2f} GB exceeds storage {inp.storage_gb:.2f} GB",
                          f"Peak buffer reached at t={_hms(res.time_s[buf_gb.index(buf_max)])}; backlog at end {buf_end:.2f} GB.",
                          suggested_fix=f"raise storage to {buf_max * 1.2:.1f} GB, add contact time or downlink rate"))
    elif buf_end > 1e-6 and buf_end > buf_mid * 1.2 and buf_end > 0.05:
        per_day = (buf_end - buf_mid) / max(sim_s / 2.0 / 86400.0, 1e-9)
        C.append(Conflict("major", "SIM_DATA_BACKLOG",
                          f"Data backlog grows {per_day:.2f} GB/day",
                          f"Buffer {buf_mid:.2f} GB at mid-run, {buf_end:.2f} GB at the end: downlink does not keep up "
                          f"({inp.contact_s_per_orbit:.0f} s contact per orbit from {inp.contact_source}).",
                          suggested_fix=f"add {per_day * 8000.0 / max(abs(next((m.data_rate_bps for m in inp.modes if m.name == 'downlink'), 1.0)) / 1e6, 1e-6) / 60.0:.0f} min/day of contact "
                                        f"or raise the downlink rate"))
    if safe_pct > SAFE_TIME_WARN_PCT:
        C.append(Conflict("warning", "SIM_SAFE_TIME",
                          f"{safe_pct:.1f} % of the time in {_fmt_mode(inp, inp.safe)} mode",
                          f"Guards ({'; '.join(g.condition for g in inp.guards)}) fired {sum(1 for e in res.events if e['type'] == 'guard_trigger')} times.",
                          suggested_fix="fix the energy balance / battery sizing so the SoC guard stops firing"))

    # series (downsampled)
    stride = _downsample(n, dt_s)
    idx = list(range(0, n, stride))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    out.series = {
        "analysis": ANALYSIS, "n_orbits": n_orbits, "period_s": period, "dt_s": dt * stride,
        "t_s": [res.time_s[i] for i in idx],
        "mode": [_fmt_mode(inp, res.mode[i]) for i in idx],
        "soc_pct": [res.soc_pct[i] for i in idx],
        "p_gen_w": [round(p_gen[i], 3) for i in idx],
        "p_load_w": [round(p_load[i], 3) for i in idx],
        "data_buffer_gb": [round(buf_gb[i], 5) for i in idx],
        "temp_c": [res.temp_c[i] for i in idx],
        "events": res.events[:200],
        "modes": [{"name": _fmt_mode(inp, m.name), "power_w": m.power_draw_w, "data_rate_bps": m.data_rate_bps,
                   "payload_active": m.is_payload_active} for m in inp.modes],
        "inputs": {
            "battery_capacity_wh": cap, "min_soc_pct": inp.min_soc_pct, "sa_power_eol_w": inp.power.sa_power_eol_w,
            "heater_power_w": inp.power.heater_power_w, "eclipse_fraction": inp.orbit.eclipse_fraction,
            "contact_s_per_orbit": inp.contact_s_per_orbit, "contact_source": inp.contact_source,
            "storage_gb": inp.storage_gb, "radiator_area_m2": round(inp.thermal.radiator_area_m2, 4),
            "radiator_area_source": inp.area_source, "capacitance_j_per_k": round(inp.thermal.capacitance_j_per_k, 1),
            "guards": [g.condition + " -> " + _fmt_mode(inp, g.target_mode) for g in inp.guards],
        },
    }
    out.summary = {
        **{p.name: p.value for p in P},
        "min_soc_pct": round(min_soc, 2), "min_soc_at_s": res.time_s[i_min], "min_soc_mode": _fmt_mode(inp, res.mode[i_min]),
        "energy_balance_wh_per_orbit": round(energy_balance, 3), "data_backlog_end_gb": round(buf_end, 4),
        "time_in_safe_pct": round(safe_pct, 2), "min_temp_c": round(min(res.temp_c), 2), "max_temp_c": round(max(res.temp_c), 2),
        "guard_triggers": sum(1 for e in res.events if e["type"] == "guard_trigger"),
        "samples": len(idx), "duration_s": sim_s, "n_orbits": n_orbits,
        "modes": [_fmt_mode(inp, m.name) for m in inp.modes],
        "conflict_codes": [c.code for c in C], "warnings": out.warnings,
    }
    return out


# ── public entry ────────────────────────────────────────────────────────

async def run_mission_simulation(ctx: AnalysisContext, *, n_orbits: int = 15, dt_s: float = 10) -> AnalysisOutput:
    """Simulate ``n_orbits`` orbits of the study's ConOps and grade the result.

    Pure with respect to the model: nothing is written — the router hands the
    returned parameters / conflicts to ``ResultsSink``.
    """
    n_orbits = max(1, int(n_orbits))
    contact_s_day, source = await _contact_from_ground_closure(ctx)
    inp = _build_inputs(ctx, n_orbits, contact_s_day, source)
    res = simulate_orbit(modes=inp.modes, guards=inp.guards, orbit_params=inp.orbit, power_params=inp.power,
                         thermal_params=inp.thermal, duration_s=n_orbits * inp.orbit.period_s - EXECUTOR_DT_S / 2,
                         mode_schedule=inp.schedule)
    return _post_process(ctx, inp, res, n_orbits, float(dt_s))
