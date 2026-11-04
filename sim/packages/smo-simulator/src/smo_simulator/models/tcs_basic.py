"""SMO Simulator — Basic TCS Model.

Thermal zones, heater thermostat control, FPA cooler.
Enhanced with heater setpoint commands, auto mode, sensor drift, heater stuck-on.

Active thermal control (EOSAT-1):
  - Battery heater: thermostat-controlled
  - OBC heater: thermostat-controlled while its EPS line (6) is powered
    (manual override via HEATER_OBC, back to auto via HEATER_AUTO_MODE)
  - Thruster (catalyst-bed) heater: REAL as of Phase D — 12 W catbed preheat
    for the green-monoprop module, commanded via HEATER_THRUSTER (S8 func 42,
    circuit 2), powered from the EPS `prop` line (0x014A), state published at
    0x041B and the bed temperature at 0x0409 (the propulsion arm interlock).
    Manual by default; HEATER_AUTO_MODE circuit=2 enables the thermostat hold.
  - Temperatures (2026-11): a lumped-parameter thermal network
    (models/thermal_network.py, configured in subsystems/tcs.yaml `network:`)
    replaces the fixed +10/+12 C sinks — sun / albedo / Earth IR on the
    external faces from the true attitude, radiation to space, conduction and
    internal radiation, and the electrical power the EPS really delivers to
    each unit. Design note: docs/plan_2026-11/THERMAL_MODEL.md.
"""
import math
import random
from dataclasses import dataclass, field
from typing import Any
from smo_common.config.fpa_envelope import FPAEnvelope
from smo_common.config.schemas import SimTCSEnvironmentConfig, TCSConfig
from smo_common.models.subsystem import SubsystemModel
from smo_simulator.failure_spec import (
    FailureSpec, ParamSpec, T_FLOAT, T_BOOL, enum, number,
)
# The FPA setpoint arrives on the same wire field (S8 func 36, uint16
# centi-kelvin) whether it is routed to the payload or to TCS, so both sides
# must apply the same decode tolerance or the two will disagree about which
# setpoints are legal. One helper, imported.
from smo_simulator.models.payload_basic import snap_to_envelope
from smo_simulator.models import thermal_network as tn

#: Schema defaults, so the model's fallbacks and `subsystems/tcs.yaml`'s
#: accepted keys cannot drift apart (DISPLAY_REQUESTS_PAYLOAD.md §8.2).
_TCS_DEFAULTS = TCSConfig()

@dataclass
class TCSState:
    temp_panel_px: float = 15.0; temp_panel_mx: float = 12.0
    temp_panel_py: float = 20.0; temp_panel_my: float = 18.0
    temp_panel_pz: float = 10.0; temp_panel_mz: float = 8.0
    temp_obc: float = 25.0; temp_battery: float = 15.0
    temp_fpa: float = -5.0; temp_thruster: float = 5.0
    htr_battery: bool = False; htr_obc: bool = False
    htr_thruster: bool = False
    # cooler_fpa: the COMMANDED cooler state — one flag, written by every
    # command path (TCS func 43, EPS func 17, PL_SET_MODE, S2 device — brief
    # 05 WP-2, last command wins). cooler_fpa_active is the EFFECTIVE state
    # (commanded AND EPS line 4 powered AND not failed) — published at 0x040C
    # and the one the thermal physics and EPS billing use.
    cooler_fpa: bool = False
    cooler_fpa_active: bool = False
    # 2026-08b: coldest the cooler can hold at the present sink and load, and
    # how much of that is left below the commanded setpoint. Negative margin =
    # the setpoint is out of reach and FPA READY will not come up.
    fpa_cooler_floor_c: float = 0.0
    fpa_cooler_margin_k: float = 0.0
    htr_battery_failed: bool = False; htr_obc_failed: bool = False
    htr_thruster_failed: bool = False; cooler_failed: bool = False
    obc_internal_heat_w: float = 0.0
    # Thermal network nodes WITHOUT a legacy temp_* field (structure,
    # wings, ttc, payload, aocs, prop) — deg C, keyed by node name.
    node_temps: dict = field(default_factory=dict)
    # Manual override flags (False = auto thermostat, True = manual control)
    htr_battery_manual: bool = False
    htr_obc_manual: bool = False
    # Thruster (catbed) heater defaults to MANUAL: preheat is an explicit
    # NOM-013 step via HEATER_THRUSTER func 42, not an automatic thermostat.
    # HEATER_AUTO_MODE circuit=2 switches it to the thermostat hold.
    htr_thruster_manual: bool = True
    # Sensor drift offsets (failure injection)
    sensor_drift: dict = field(default_factory=dict)
    # Instructor "cold soak" (P1, 2026-11-02): a PHYSICAL sink offset per
    # heated zone (battery / obc / thruster), in degC (negative = colder).
    # Unlike temp_anomaly (a held sensor offset) the zone really cools, the
    # thermostat sees it, and a powered heater can win it back.
    cold_soak: dict = field(default_factory=dict)
    # Heater stuck-on flags
    htr_battery_stuck_on: bool = False
    htr_obc_stuck_on: bool = False
    htr_thruster_stuck_on: bool = False
    # Heater open-circuit flags (heater appears ON but provides no heat)
    htr_battery_open_circuit: bool = False
    htr_obc_open_circuit: bool = False
    htr_thruster_open_circuit: bool = False
    # ── Phase 4: Flight hardware realism ──
    htr_duty_battery: float = 0.0    # Battery heater duty cycle (0-100%)
    htr_duty_obc: float = 0.0       # OBC heater duty cycle (0-100%)
    htr_duty_thruster: float = 0.0  # Thruster heater duty cycle (0-100%)
    htr_total_power_w: float = 0.0  # Total heater power consumption
    # Duty cycle tracking (cumulative on-time in sliding window)
    _htr_on_accum: dict = field(default_factory=lambda: {
        "battery": 0.0, "obc": 0.0, "thruster": 0.0
    })
    _duty_window_s: float = 600.0  # 10-minute sliding window
    # ── Heater setpoints and limits ──
    # Defaults match configs/eosat1/subsystems/tcs.yaml; configure() re-syncs
    # these from the heaters: block (they are the LIVE thermostat band —
    # previously the config band was loaded into _THERMOSTAT while these
    # state fields kept their old defaults and silently won).
    htr_battery_setpoint_on_c: float = 5.0
    htr_battery_setpoint_off_c: float = 10.0
    htr_obc_setpoint_on_c: float = -10.0
    htr_obc_setpoint_off_c: float = -5.0
    # Phase D: catbed hold band (auto mode) — thermostat on below 190 C,
    # off at 230 C; the propulsion arm interlock needs >= 180 C (prop.yaml).
    htr_thruster_setpoint_on_c: float = 190.0
    htr_thruster_setpoint_off_c: float = 230.0
    htr_battery_duty_limit_pct: float = 100.0
    htr_obc_duty_limit_pct: float = 100.0
    htr_thruster_duty_limit_pct: float = 100.0
    # ── Decontamination heating ──
    decontamination_active: bool = False
    decontam_start_time: float = 0.0  # Relative to tick
    decontam_fpa_target_c: float = 50.0
    # ── Event tracking (to avoid repeated events) ──
    _prev_htr_battery_on: bool = False
    _prev_htr_obc_on: bool = False
    _prev_htr_thruster_on: bool = False
    _prev_temp_battery: float = 15.0
    _prev_temp_obc: float = 25.0
    _prev_temp_fpa: float = -5.0
    _prev_htr_battery_failed: bool = False
    _prev_htr_obc_failed: bool = False
    _prev_htr_thruster_failed: bool = False
    _prev_htr_battery_stuck_on: bool = False
    _prev_htr_obc_stuck_on: bool = False
    _prev_htr_thruster_stuck_on: bool = False
    _prev_fpa_ready: bool = False
    _prev_thermal_runaway: bool = False
    # ── Thermal zone coupling ──
    _temp_history: list = field(default_factory=lambda: [])  # For rate calculation

    # S2 Device Access — device on/off states (device_id -> on/off)
    # NOTE (DEFECT 5): S2 device commands are NOT used for EOSAT-1 thermal control.
    # All heater control is via S8 functional commands (HEATER_*, func_id 40-49).
    # This dictionary is kept for future mission variants with multi-zone control.
    device_states: dict = field(default_factory=lambda: {
        0x0300: True,   # Heater zone 1 (unused for EOSAT-1)
        0x0301: True,   # Heater zone 2 (unused for EOSAT-1)
        0x0302: True,   # Heater zone 3 (unused for EOSAT-1)
        0x0303: True,   # Heater zone 4 (unused for EOSAT-1)
        0x0304: True,   # Heater zone 5 (unused for EOSAT-1)
        0x0305: True,   # Heater zone 6 (unused for EOSAT-1)
        0x0306: True,   # Heater zone 7 (unused for EOSAT-1)
        0x0307: True,   # Heater zone 8 (unused for EOSAT-1)
        0x0308: True,   # Heater zone 9 (unused for EOSAT-1)
        0x0309: True,   # Heater zone 10 (unused for EOSAT-1)
        0x030A: True,   # Thermistor array (unused for EOSAT-1)
        0x030B: True,   # Decontamination heater (unused for EOSAT-1)
    })


class TCSBasicModel(SubsystemModel):
    # Fallbacks only (configure() loads tcs.yaml `heaters:`); they now EQUAL
    # tcs.yaml (2026-11 consistency pass — battery used to fall back to 6 W
    # and ON 1 / OFF 5 C while every config said 8 W, ON 5 / OFF 10 C).
    # Thermostat tuples are (off_temp_c, on_temp_c).
    _HEATER_POWER = {"battery": 8.0, "obc": 4.0, "thruster": 12.0}
    _THERMOSTAT = {"battery": (10.0, 5.0), "obc": (-5.0, -10.0),
                   "thruster": (230.0, 190.0)}
    # Phase D retires the last leg of defect #31: the thruster circuit now
    # drives the REAL green-monoprop catalyst-bed heater (12 W, EPS `prop`
    # line), so every heater circuit accepts setpoint/auto-mode commands.
    _NO_HEATER_CIRCUITS = frozenset()
    # Legacy zone constants. Only `fpa` is still used (the controlled FPA
    # node and the cooler's parasitic UA = C / tau); every other temperature
    # comes from the thermal network. The rest are kept so code that reads
    # them (and old breakpoints) does not break.
    _TAU = {"panel_px":600,"panel_mx":600,"panel_py":500,"panel_my":500,
            "panel_pz":800,"panel_mz":800,"obc":900,"battery":1200,"fpa":120,"thruster":1200}
    _CAP = {"panel_px":5000,"panel_mx":5000,"panel_py":4000,"panel_my":4000,
            "panel_pz":3000,"panel_mz":3000,"obc":800,"battery":2000,"fpa":100,"thruster":50}

    def __init__(self):
        self._state = TCSState()
        # Per-model RNG (plan A-2). Standalone construction gets a fresh
        # unseeded stream so existing unit tests keep working; the engine
        # replaces this with a Random derived from simulation.yaml `seed`.
        import random as _random
        self.rng = _random.Random(20260731)  # deterministic standalone fallback; engine overrides via derive_rng
        self._param_ids: dict[str, int] = {}
        self._fpa_cooler_target: float = -5.0
        # Envelope defaults, replaced by configure() from tcs.yaml. Set here
        # too so a directly instantiated model still has the readiness rule.
        self._fpa_env = FPAEnvelope()
        self._engine = None
        # Instance copies so configure() doesn't mutate class-level dicts
        self._TAU = dict(TCSBasicModel._TAU)
        self._CAP = dict(TCSBasicModel._CAP)
        self._HEATER_POWER = dict(TCSBasicModel._HEATER_POWER)
        self._THERMOSTAT = dict(TCSBasicModel._THERMOSTAT)
        # ── Thermal network (2026-11, THERMAL_MODEL.md) ──────────────────
        # The fixed-surroundings zone model (+10/+12 C "internal sink", a
        # zone-conductance dict and a 3 K "radiation conductance") is gone:
        # temperatures now come from a lumped-parameter network whose
        # definition lives in subsystems/tcs.yaml `network:`. An
        # unconfigured model (unit tests construct TCSBasicModel() bare)
        # loads the shipped EOSAT-1 network so it is still physical.
        self._net_cfg: dict = {}
        self._net = None
        self._solver = None
        self._load_network(None)
        # Event thresholds (can be overridden by config)
        self._temp_warning_limits = {
            "battery": (0.0, 40.0),  # (low_warn, high_warn)
            "obc": (-10.0, 50.0),
            "fpa": (-50.0, -5.0),
        }
        self._temp_alarm_limits = {
            "battery": (-10.0, 50.0),
            "obc": (-20.0, 60.0),
            "fpa": (-60.0, 0.0),
        }
        self._thermal_runaway_rate = 2.0  # deg/min
        # Thermal environment (simulation.yaml tcs.environment overrides
        # these; the defaults are the schema's, i.e. one source).
        _env_defaults = SimTCSEnvironmentConfig()
        self._env = {
            "solar_flux_w_m2": _env_defaults.solar_flux_w_m2,
            "albedo": _env_defaults.albedo,
            "earth_ir_w_m2": _env_defaults.earth_ir_w_m2,
            "scale_solar_with_distance": _env_defaults.scale_solar_with_distance,
        }
        # Standalone harnesses (no engine, no AOCS model) that publish a sun
        # vector are assumed to be holding the NOMINAL nadir attitude; once
        # seen, keep assuming it through eclipse (the vector is zeroed there).
        self._standalone_nadir = False
        # Bounded cooler heat lift (brief 05 WP-1): the FPA cannot be driven
        # more than this many kelvin below its ambient sink. Retained as the
        # ABSOLUTE ceiling on the machine; the achievable lift at any instant
        # is now computed from the cooler's efficiency (see
        # `_fpa_achievable_lift_k`) and is smaller than this almost everywhere.
        self._fpa_cooler_max_lift_k = 40.0
        # ── Cooler efficiency model (2026-08b) — see `_fpa_achievable_lift_k`
        # The numbers live in TCSConfig (and therefore in subsystems/tcs.yaml),
        # not here: they used to be literals in this constructor AND in
        # configure(), while TCSConfig — a StrictModel — did not declare them,
        # so a YAML override was REJECTED by the loader and these were the only
        # live values. One source now.
        self._fpa_cooler_power_w = _TCS_DEFAULTS.fpa_cooler_power_w
        self._fpa_cooler_carnot_fraction = _TCS_DEFAULTS.fpa_cooler_carnot_fraction
        self._fpa_imaging_load_w = _TCS_DEFAULTS.fpa_imaging_load_w

    # ── FPA cooler authority (2026-08b) ─────────────────────────────────
    #
    # WHAT WAS WRONG. `fpa_cooler_max_lift_k` was a flat 40 K with no coupling
    # whatever to `fpa_cooler_power_w`, so the cooler had exactly as much
    # authority at a 39 K lift as at a 1 K lift and "the cooler is struggling"
    # was not a state the model could enter. The number was also not
    # achievable by the machine the envelope docstring named. Holding -15 C
    # against the +12 C internal sink is a 27 K lift; the FPA node's UA is
    # C/tau = 100/120 = 0.833 W/K, so the parasitic heat to be pumped is
    # 0.833 x 27 = 22.5 W, from 15 W of input — a COP of 1.50. A single-stage
    # Bi2Te3 thermoelectric cannot do that. At its optimum-COP current,
    #
    #     COP_max = (Tc/dT) . (g - Th/Tc)/(g + 1),  g = sqrt(1 + Z.Tm)
    #
    # (Goldsmid's standard result, reproduced in every TEC selection guide —
    # e.g. Ferrotec, "Mathematical Modeling of Modules"), with Tc = 258.15 K,
    # Th = 285.15 K and the ZT ~ 0.73 of commercial bismuth telluride at this
    # mean temperature, gives COP_max = 0.88. The required 1.50 is 1.7x what
    # the material allows, and at the 40 K flat lift the model claimed it is
    # worse still: a single-stage module's dTmax is only ~70 K at zero heat
    # load, where the COP is zero by definition.
    #
    # WHAT IT IS INSTEAD. 1.50 is 15.7 % of the Carnot COP at this lift
    # (Tc/dT = 258.15/27 = 9.56). That is squarely inside the 10-25 % of
    # Carnot that miniature Stirling / free-piston space coolers achieve at
    # near-ambient lifts, and cooled small-satellite EO detectors use exactly
    # that class of machine (the CubeSat cryocooler literature — Lockheed
    # Martin Microcryocooler, AIM SX030/SF-100 — is all Stirling/pulse-tube,
    # not thermoelectric). So the hardware is reclassified: this is a
    # miniature Stirling-class cooler, `fpa_cooler_carnot_fraction` of Carnot,
    # and the "Peltier envelope" wording in the refusal messages and in
    # smo_common.config.fpa_envelope is what was wrong, not the mission.
    #
    # WHAT THE MODEL NOW DOES. Cooling authority is the steady state where the
    # cooler's heat lift equals the heat arriving at the node:
    #
    #     Qc(dT) = eta . P . Tc/dT              (fraction of Carnot)
    #     Qc(dT) = UA.dT + Q_load               (steady state, Tc = Th - dT)
    #  => UA.dT^2 + (Q_load + eta.P).dT - eta.P.Th = 0
    #
    # solved for the positive root. Authority therefore FALLS as the sink
    # warms and as the detector's own dissipation rises, which is what makes
    # "the cooler is struggling under imaging load" — the thing COM-011's
    # off-nominal section asks the trainee to diagnose — a real, reachable,
    # measurable state instead of a story.
    #
    # Sized (fpa_cooler_carnot_fraction 0.23, 15 W, UA 0.833 W/K):
    #   sink +12 C, idle       32.3 K of lift -> floor -20.3 C  (-20 C just holds)
    #   sink +12 C, imaging    31.2 K         -> floor -19.2 C  (-20 C does NOT)
    #   sink +20 C, idle       32.8 K         -> floor -12.8 C  (-15 C does NOT)
    # The nominal -15 C setpoint keeps ~5 K of margin, so the shipped mission
    # is unchanged; the margin is now finite, visible (0x0424/0x0425) and
    # spendable, which is the teaching point.
    def _fpa_achievable_lift_k(self, sink_c: float, q_load_w: float) -> float:
        """Steady-state lift (K) the cooler can hold below `sink_c`."""
        ua = self._CAP.get("fpa", 100.0) / max(self._TAU.get("fpa", 120.0), 1e-6)
        eta_p = max(0.0, self._fpa_cooler_carnot_fraction
                    * self._fpa_cooler_power_w)
        if eta_p <= 0.0:
            return 0.0
        th = sink_c + 273.15
        b = q_load_w + eta_p
        disc = b * b + 4.0 * ua * eta_p * th
        lift = (math.sqrt(max(0.0, disc)) - b) / (2.0 * ua)
        # The absolute machine ceiling still applies: no working fluid, no
        # regenerator and no number of stages here goes past it.
        return max(0.0, min(lift, self._fpa_cooler_max_lift_k))

    @property
    def name(self) -> str: return "tcs"

    def configure(self, config: dict[str, Any]) -> None:
        self._param_ids = config.get("param_ids", {
            "temp_panel_px":0x0400,"temp_panel_mx":0x0401,"temp_panel_py":0x0402,
            "temp_panel_my":0x0403,"temp_panel_pz":0x0404,"temp_panel_mz":0x0405,
            "temp_obc":0x0406,"temp_battery":0x0407,"temp_fpa":0x0408,
            "temp_thruster":0x0409,"htr_battery":0x040A,"htr_obc":0x040B,
            "cooler_fpa":0x040C,"htr_thruster":0x041B,
        })
        # Override thermal zone constants from config
        for zone in config.get("zones", []):
            name = zone.get("name") if isinstance(zone, dict) else getattr(zone, "name", None)
            if not name:
                continue
            tau = zone.get("time_constant_s") if isinstance(zone, dict) else getattr(zone, "time_constant_s", None)
            cap = zone.get("capacitance_j_per_c") if isinstance(zone, dict) else getattr(zone, "capacitance_j_per_c", None)
            init_temp = zone.get("initial_temp_c") if isinstance(zone, dict) else getattr(zone, "initial_temp_c", None)
            if tau is not None:
                self._TAU[name] = tau
            if cap is not None:
                self._CAP[name] = cap
            if init_temp is not None:
                attr = f"temp_{name}"
                if hasattr(self._state, attr):
                    setattr(self._state, attr, init_temp)
        # Override heater constants from config
        for heater in config.get("heaters", []):
            name = heater.get("name") if isinstance(heater, dict) else getattr(heater, "name", None)
            if not name:
                continue
            power = heater.get("power_w") if isinstance(heater, dict) else getattr(heater, "power_w", None)
            on_t = heater.get("on_temp_c") if isinstance(heater, dict) else getattr(heater, "on_temp_c", None)
            off_t = heater.get("off_temp_c") if isinstance(heater, dict) else getattr(heater, "off_temp_c", None)
            if power is not None:
                self._HEATER_POWER[name] = power
            if on_t is not None and off_t is not None:
                self._THERMOSTAT[name] = (off_t, on_t)
                # Sync the live per-circuit state setpoints too — the
                # thermostat reads these, and they used to keep stale
                # dataclass defaults that silently overrode the config.
                if hasattr(self._state, f"htr_{name}_setpoint_on_c"):
                    setattr(self._state, f"htr_{name}_setpoint_on_c", float(on_t))
                    setattr(self._state, f"htr_{name}_setpoint_off_c", float(off_t))
        # FPA cooler target
        self._fpa_cooler_target = config.get("fpa_cooler_target_c", -5.0)
        self._fpa_cooler_max_lift_k = float(
            config.get("fpa_cooler_max_lift_k", 40.0))
        # Cooler efficiency model — now REAL configuration: TCSConfig declares
        # all three, so subsystems/tcs.yaml can set them and the loader accepts
        # the file. The fallbacks are the schema defaults, never fresh literals.
        self._fpa_cooler_power_w = float(
            config.get("fpa_cooler_power_w", self._fpa_cooler_power_w))
        self._fpa_cooler_carnot_fraction = float(
            config.get("fpa_cooler_carnot_fraction",
                       self._fpa_cooler_carnot_fraction))
        self._fpa_imaging_load_w = float(
            config.get("fpa_imaging_load_w", self._fpa_imaging_load_w))
        # FPA envelope — the single source for readiness and for the derived
        # limit bands (DECISIONS §3, ruled in G3-d).
        self._fpa_env = FPAEnvelope.from_config(config)

        # ── tcs.yaml `network:` — the thermal network (2026-11) ──────────
        # Replaces `thermal_coupling:` (a zone-conductance dict + a 3 K
        # "radiation conductance") and the fixed-sink environment.
        if config.get("network"):
            self._load_network(config["network"])
        # ── tcs.yaml event_thresholds (same dead-config story) ───────────
        evt = config.get("event_thresholds", {}) or {}
        for zone, limits in (evt.get("temperature_warning", {}) or {}).items():
            if isinstance(limits, (list, tuple)) and len(limits) == 2:
                self._temp_warning_limits[zone] = (float(limits[0]), float(limits[1]))
        for zone, limits in (evt.get("temperature_alarm", {}) or {}).items():
            if isinstance(limits, (list, tuple)) and len(limits) == 2:
                self._temp_alarm_limits[zone] = (float(limits[0]), float(limits[1]))
        if evt.get("thermal_runaway_rate_deg_per_min") is not None:
            self._thermal_runaway_rate = float(evt["thermal_runaway_rate_deg_per_min"])

        # ── simulation.yaml `tcs.environment:` block (defect #51) ────────
        # Orbital heating constants (solar flux at 1 AU, Earth albedo,
        # Earth OLR). The old fixed-sink keys are gone with the zone model.
        env = (config.get("simulation", {}) or {}).get("environment", {}) or {}
        self._env = dict(self._env)
        for k, v in env.items():
            if v is None:
                continue
            self._env[k] = bool(v) if isinstance(v, bool) else float(v)

    # ── Thermal network plumbing (2026-11) ──────────────────────────────
    #: Network node -> legacy TCSState field. These nodes keep their
    #: published parameters (0x0400-0x0409) and every existing reader of
    #: `_state.temp_*`; the other nodes live in `_state.node_temps`.
    _FIELD_NODES = ("panel_px", "panel_mx", "panel_py", "panel_my",
                    "panel_pz", "panel_mz", "obc", "battery", "thruster")

    @staticmethod
    def _default_network_spec() -> dict:
        """The shipped EOSAT-1 network (subsystems/tcs.yaml `network:`).

        Used only by a model that is never configured (bare unit-test
        construction). Same lookup rule as the commanding catalog:
        $SMO_CONFIG_DIR, else the repository's configs/eosat1.
        """
        import os
        from pathlib import Path
        import yaml
        cands = []
        if os.environ.get("SMO_CONFIG_DIR"):
            cands.append(Path(os.environ["SMO_CONFIG_DIR"]))
        cands.append(Path(__file__).resolve().parents[5] / "configs" / "eosat1")
        for c in cands:
            f = c / "subsystems" / "tcs.yaml"
            if f.is_file():
                net = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("network")
                if net:
                    return net
        raise RuntimeError("TCS: no thermal network configured and no "
                           "subsystems/tcs.yaml `network:` found")

    _NETWORK_KEYS = frozenset({
        "sensor_noise_k", "integration", "nodes", "surfaces", "conductors",
        "radiative", "dissipation", "residual_node", "heater_nodes",
        "battery_heat", "fpa", "wing_panels", "stowed_wing_contact_w_per_k",
        "default_dissipation_w", "cold_soak"})

    def _load_network(self, spec: dict | None) -> None:
        spec = dict(spec) if spec else self._default_network_spec()
        unknown = set(spec) - self._NETWORK_KEYS
        if unknown:
            raise ValueError(f"tcs.yaml network: unknown key(s) {sorted(unknown)}")
        net, init = tn.build_network(spec)
        integ = spec.get("integration", {}) or {}
        self._net_cfg = spec
        self._net = net
        self._solver = tn.NetworkSolver(
            net, init,
            stability_fraction=float(integ.get("stability_fraction", 0.4)),
            max_step_s=float(integ.get("max_step_s", 20.0)))
        self._sensor_noise_k = float(spec.get("sensor_noise_k", 0.0))
        self._dissipation = {str(k): {str(n): float(f) for n, f in (v or {}).items()}
                             for k, v in (spec.get("dissipation", {}) or {}).items()}
        for line, shares in self._dissipation.items():
            for node in shares:
                if node not in net.index:
                    raise ValueError(f"TCS network dissipation {line}: unknown node {node!r}")
        self._residual_node = spec.get("residual_node", "structure")
        self._heater_nodes = dict(spec.get("heater_nodes", {
            "battery": "battery", "obc": "obc", "thruster": "thruster"}))
        bh = spec.get("battery_heat", {}) or {}
        self._battery_heat_node = bh.get("node", "battery")
        self._fpa_sink_node = (spec.get("fpa", {}) or {}).get("sink_node", "payload")
        self._stowed_contact = float(spec.get("stowed_wing_contact_w_per_k", 1.0))
        self._wing_panels = dict(spec.get("wing_panels", {"wing_py": "panel_py",
                                                         "wing_my": "panel_my"}))
        cs = spec.get("cold_soak", {}) or {}
        self._soak_g = {k: float(v) for k, v in (cs.get("conductance_w_per_k", {}) or {}).items()}
        self._soak_default = {k: float(v) for k, v in (cs.get("default_offset_c", {}) or {}).items()}
        # Seed the published / extra node temperatures from the network's
        # initial conditions.
        s = self._state
        s.node_temps = {}
        for name in net.names:
            if name in self._FIELD_NODES:
                setattr(s, f"temp_{name}", init[name])
            else:
                s.node_temps[name] = init[name]

    def set_uniform_temperature(self, temp_c: float) -> None:
        """Put every network node (and the FPA) at one temperature.

        The engine's separation state uses this (all zones at ambient)."""
        s = self._state
        for name in self._net.names:
            if name in self._FIELD_NODES:
                setattr(s, f"temp_{name}", float(temp_c))
            else:
                s.node_temps[name] = float(temp_c)
        s.temp_fpa = float(temp_c)

    def node_temperature(self, name: str) -> float:
        """Current temperature of any network node (deg C)."""
        if name in self._FIELD_NODES:
            return float(getattr(self._state, f"temp_{name}"))
        if name == "fpa":
            return float(self._state.temp_fpa)
        return float(self._state.node_temps[name])

    def _sync_in(self) -> None:
        s = self._state
        sol = self._solver
        for name in self._net.names:
            if name in self._FIELD_NODES:
                sol.set_temp_c(name, getattr(s, f"temp_{name}"))
            else:
                sol.set_temp_c(name, s.node_temps.get(name, sol.temp_c(name)))

    def _sync_out(self) -> None:
        s = self._state
        for name, t in self._solver.temps_c().items():
            if name in self._FIELD_NODES:
                setattr(s, f"temp_{name}", t)
            else:
                s.node_temps[name] = t

    def _geometry(self, orbit_state: Any, p: dict[int, float]) -> "tn.Geometry":
        """Sun / nadir in the body frame, illumination and altitude.

        Attitude priority: the AOCS model's TRUE quaternion (engine runs,
        AOCS ticking: phase >= 4); else a published sun-body vector
        (standalone harnesses) with the nominal nadir hold (-Z); else a
        tumbling body (orientation averages) — the same rule EPS uses for
        array power, so the thermal and power pictures agree.
        """
        import numpy as np
        alt = getattr(orbit_state, "alt_km", 513.0)
        alt = float(alt) if isinstance(alt, (int, float)) and alt else 513.0
        re = 6378.137
        h_ratio = (re + max(alt, 100.0)) / re
        in_ecl = bool(getattr(orbit_state, "in_eclipse", False))
        sun_frac = getattr(orbit_state, "sun_fraction", None)
        if not isinstance(sun_frac, (int, float)) or isinstance(sun_frac, bool):
            sun_frac = 0.0 if in_ecl else 1.0     # duck-typed orbit stub
        sun_frac = max(0.0, min(1.0, float(sun_frac)))
        pos = getattr(orbit_state, "pos_eci", None)
        sun = getattr(orbit_state, "sun_eci", None)
        if not isinstance(pos, (np.ndarray, list, tuple)) or \
                not isinstance(sun, (np.ndarray, list, tuple)):
            pos = sun = None
        r_hat = s_hat = None
        sun_dist_km = None
        try:
            if pos is not None and sun is not None:
                pos = np.asarray(pos, float)
                sun = np.asarray(sun, float)
                rn, sn = float(np.linalg.norm(pos)), float(np.linalg.norm(sun))
                if rn > 1.0 and sn > 1.0:
                    r_hat, s_hat, sun_dist_km = pos / rn, sun / sn, sn
        except Exception:  # noqa: BLE001 — duck-typed orbit stubs
            r_hat = s_hat = None
        if r_hat is not None:
            albedo_cos = max(0.0, float(r_hat @ s_hat))
        else:
            beta = math.radians(float(getattr(orbit_state, "solar_beta_deg", 0.0)))
            albedo_cos = 0.0 if in_ecl else 0.5 * math.cos(beta)

        sun_b = nadir_b = None
        eng = self._engine
        aocs = eng.subsystems.get("aocs") if eng is not None and hasattr(eng, "subsystems") else None
        if (aocs is not None and r_hat is not None
                and int(getattr(eng, "_spacecraft_phase", 0)) >= 4
                and hasattr(getattr(aocs, "_state", None), "q_true")):
            from smo_common import attitude as att
            C = att.quat_to_dcm(np.asarray(aocs._state.q_true, float))
            sb = C @ s_hat
            nb = C @ (-r_hat)
            sun_b = (float(sb[0]), float(sb[1]), float(sb[2]))
            nadir_b = (float(nb[0]), float(nb[1]), float(nb[2]))
        elif eng is None:
            sx, sy, sz = (p.get(0x02B3, 0.0) or 0.0, p.get(0x02B4, 0.0) or 0.0,
                          p.get(0x02B5, 0.0) or 0.0)
            mag = math.sqrt(sx * sx + sy * sy + sz * sz)
            if mag > 0.01:
                self._standalone_nadir = True
                sun_b = (sx / mag, sy / mag, sz / mag)
            if self._standalone_nadir:
                nadir_b = (0.0, 0.0, -1.0)
                if sun_b is None:
                    sun_b = (0.0, 0.0, 0.0)   # eclipse: no direct sun
        # Wings: deployment bits (0x0144 bit0 = +Y, bit1 = -Y) and the SADA
        # shaft angle (0x0133). Absent (reduced harness) = deployed.
        ws = p.get(0x0144)
        if ws is None:
            dep = (True, True)
        else:
            ws = int(ws)
            dep = (bool(ws & 1), bool(ws & 2))
        if 0x0133 in p:
            sada = float(p[0x0133])
        elif sun_b is not None and (sun_b[0] or sun_b[2]):
            sada = math.degrees(math.atan2(sun_b[2], sun_b[0]))
        else:
            sada = 0.0
        geo = tn.Geometry(sun_body=sun_b, nadir_body=nadir_b,
                          sun_fraction=sun_frac, albedo_cos=albedo_cos,
                          h_ratio=h_ratio, sada_angle_deg=sada,
                          wings_deployed=dep)
        geo.sun_dist_km = sun_dist_km
        return geo

    #: EPS line -> (current parameter). Lines 0-7 publish at 0x0118+i,
    #: prop at 0x014B (eps_basic POWER_LINE_DEFS / _EXTRA_LINE_PARAM_IDS).
    _LINE_CURRENT_IDS = {"obc": 0x0118, "ttc_rx": 0x0119, "ttc_tx": 0x011A,
                         "payload": 0x011B, "fpa_cooler": 0x011C,
                         "htr_bat": 0x011D, "htr_obc": 0x011E,
                         "aocs_wheels": 0x011F, "prop": 0x014B}
    #: Array face -> EPS current parameter (body faces 0x012B-0x0130 include
    #: the wing on +-Y; the wings alone are 0x0146 / 0x0147).
    _ARRAY_CURRENT_IDS = {"px": 0x012B, "mx": 0x012C, "py": 0x012D,
                          "my": 0x012E, "pz": 0x012F, "mz": 0x0130,
                          "wing_py": 0x0146, "wing_my": 0x0147}

    def _electrical_inputs(self, p: dict[int, float], htr_w: dict[str, float]
                           ) -> tuple[list[float], dict[str, float]]:
        """Dissipation per node [W] from what the EPS actually delivers.

        Every watt a load draws ends up as heat in the node that carries it
        (minus the RF that leaves the antenna, via the share < 1 on ttc_tx).
        Line powers are I x V exactly as EPS computed them (I = P / max(V,
        20)). The unattributed rest of the bus load (EPS housekeeping noise,
        an injected bus short) goes to `residual_node`. Heaters are added
        from TCS's own heater state, not the EPS line, so an open-circuit
        heater bills but does not heat (the failure's teaching point).
        """
        net = self._net
        pw = [0.0] * len(net.names)
        array_w: dict[str, float] = {}
        if self._unpowered():
            # Phases 0-1 (pre-separation / separation timer): the separation
            # switches are open, nothing on board is powered, so the only
            # heat is what the tumbling body absorbs (2026-11-03).
            return pw, array_w
        if 0x0106 not in p:
            # No EPS in the loop (bare TCS harness): use the configured
            # default loads so the network still has its nominal dissipation.
            for node, w in (self._net_cfg.get("default_dissipation_w", {}) or {}).items():
                if node in net.index:
                    pw[net.index[node]] += float(w)
        else:
            v = max(float(p.get(0x0105, 28.0) or 28.0), 20.0)
            attributed = 0.0
            for line, pid in self._LINE_CURRENT_IDS.items():
                w = float(p.get(pid, 0.0) or 0.0) * v
                attributed += w
                if line == "prop" and self._state.htr_thruster:
                    # The catbed heater rides on the prop line; its heat is
                    # applied to the thruster node below.
                    w = max(0.0, w - self._HEATER_POWER["thruster"])
                for node, share in self._dissipation.get(line, {}).items():
                    pw[net.index[node]] += w * share
            residual = float(p.get(0x0106, 0.0) or 0.0) - attributed
            if self._residual_node in net.index:
                pw[net.index[self._residual_node]] += residual
            # Battery: I^2 R plus the charge inefficiency (eps.yaml
            # internal_r_ohm / charge_efficiency, read off the live EPS model
            # when the engine runs — no second copy of the numbers).
            eps = self._engine.subsystems.get("eps") if (
                self._engine is not None and hasattr(self._engine, "subsystems")) else None
            r_int = float(getattr(eps, "_internal_r", 0.05))
            eta_c = float(getattr(eps, "_charge_eff", 0.94))
            i_bat = float(p.get(0x0109, 0.0) or 0.0)
            q_bat = i_bat * i_bat * r_int
            if i_bat > 0:
                q_bat += (1.0 - eta_c) * i_bat * v
            if self._battery_heat_node in net.index:
                pw[net.index[self._battery_heat_node]] += q_bat
            for face, pid in self._ARRAY_CURRENT_IDS.items():
                array_w[face] = float(p.get(pid, 0.0) or 0.0) * v
            for wf, body in (("wing_py", "py"), ("wing_my", "my")):
                array_w[body] = max(0.0, array_w.get(body, 0.0) - array_w.get(wf, 0.0))
        for circuit, w in htr_w.items():
            node = self._heater_nodes.get(circuit)
            if node in net.index:
                pw[net.index[node]] += w
        return pw, array_w

    def _unpowered(self) -> bool:
        """True before the separation timer expires (spacecraft phase < 2):
        separation switches open, no load and no heater is powered."""
        eng = self._engine
        if eng is None or not hasattr(eng, "_spacecraft_phase"):
            return False
        try:
            return int(eng._spacecraft_phase) < 2
        except (TypeError, ValueError):
            return False

    def _thermostat_control(self, circuit: str, temp: float) -> None:
        """Apply thermostat control for a heater circuit (auto mode only)."""
        s = self._state
        manual_flag = getattr(s, f"htr_{circuit}_manual", False)
        stuck_on = getattr(s, f"htr_{circuit}_stuck_on", False)
        failed = getattr(s, f"htr_{circuit}_failed", False)

        if stuck_on:
            # Heater stays on regardless of commands
            setattr(s, f"htr_{circuit}", True)
            return
        if manual_flag:
            # Manual mode — don't apply thermostat
            return
        if failed:
            setattr(s, f"htr_{circuit}", False)
            return

        # Get dynamic setpoints (allow override via commands)
        on_attr = f"htr_{circuit}_setpoint_on_c"
        off_attr = f"htr_{circuit}_setpoint_off_c"
        lo = getattr(s, on_attr, self._THERMOSTAT[circuit][1])
        hi = getattr(s, off_attr, self._THERMOSTAT[circuit][0])

        if temp <= lo:
            setattr(s, f"htr_{circuit}", True)
        elif temp >= hi:
            setattr(s, f"htr_{circuit}", False)

    def _generate_events(self, dt: float) -> None:
        """Generate TCS events with edge detection."""
        if not hasattr(self, '_engine') or not self._engine:
            return

        s = self._state
        events = []

        # Helper: emit event with edge detection
        def emit_if_changed(event_dict: dict, condition_now: bool, prev_attr: str) -> None:
            prev = getattr(s, prev_attr, False)
            if condition_now and not prev:
                events.append(event_dict)
                setattr(s, prev_attr, True)
            elif not condition_now and prev:
                setattr(s, prev_attr, False)

        # Temperature warning/alarm events
        bat_temp = s.temp_battery
        obc_temp = s.temp_obc
        fpa_temp = s.temp_fpa

        # Battery overtemp warning
        bat_warn_low, bat_warn_high = self._temp_warning_limits["battery"]
        emit_if_changed(
            {"event_id": 0x0400, "severity": "MEDIUM", "subsystem": "tcs",
             "description": f"TCS_OVERTEMP_WARNING: Battery {bat_temp:.1f}C"},
            (bat_temp > bat_warn_high),
            "_prev_bat_overtemp_warn"
        )

        # Battery overtemp alarm
        bat_alarm_low, bat_alarm_high = self._temp_alarm_limits["battery"]
        emit_if_changed(
            {"event_id": 0x0401, "severity": "HIGH", "subsystem": "tcs",
             "description": f"TCS_OVERTEMP_ALARM: Battery {bat_temp:.1f}C"},
            (bat_temp > bat_alarm_high),
            "_prev_bat_overtemp_alarm"
        )

        # Battery undertemp warning
        emit_if_changed(
            {"event_id": 0x0402, "severity": "MEDIUM", "subsystem": "tcs",
             "description": f"TCS_UNDERTEMP_WARNING: Battery {bat_temp:.1f}C"},
            (bat_temp < bat_warn_low),
            "_prev_bat_undertemp_warn"
        )

        # Battery undertemp alarm
        emit_if_changed(
            {"event_id": 0x0403, "severity": "HIGH", "subsystem": "tcs",
             "description": f"TCS_UNDERTEMP_ALARM: Battery {bat_temp:.1f}C"},
            (bat_temp < bat_alarm_low),
            "_prev_bat_undertemp_alarm"
        )

        # Heater on/off events
        if s.htr_battery != s._prev_htr_battery_on:
            if s.htr_battery:
                events.append({"event_id": 0x0404, "severity": "INFO", "subsystem": "tcs",
                              "description": "HEATER_ON: Battery heater activated"})
            else:
                events.append({"event_id": 0x0405, "severity": "INFO", "subsystem": "tcs",
                              "description": "HEATER_OFF: Battery heater deactivated"})
            s._prev_htr_battery_on = s.htr_battery

        # Heater failure events
        if s.htr_battery_stuck_on != s._prev_htr_battery_stuck_on:
            if s.htr_battery_stuck_on:
                events.append({"event_id": 0x0406, "severity": "HIGH", "subsystem": "tcs",
                              "description": "HEATER_STUCK_ON: Battery heater cannot turn off"})
            s._prev_htr_battery_stuck_on = s.htr_battery_stuck_on

        if s.htr_battery_failed != s._prev_htr_battery_failed:
            if s.htr_battery_failed:
                events.append({"event_id": 0x0407, "severity": "HIGH", "subsystem": "tcs",
                              "description": "HEATER_STUCK_OFF: Battery heater circuit failure"})
            s._prev_htr_battery_failed = s.htr_battery_failed

        # Mode change event
        decontam_now = s.decontamination_active
        prev_decontam = getattr(s, "_prev_decontam_active", False)
        if decontam_now != prev_decontam:
            events.append({"event_id": 0x0408, "severity": "INFO", "subsystem": "tcs",
                          "description": f"TCS_MODE_CHANGE: Decontamination {'START' if decontam_now else 'STOP'}"})
            s._prev_decontam_active = decontam_now

        # Thermal runaway detection (temperature rate > 2 deg/min).
        # Use a SMOOTHED rate over the temperature-history window rather than the
        # tick-to-tick delta: consecutive-sample deltas are dominated by the
        # per-tick gaussian noise on bat_temp, so abs(rate) chattered across the
        # 2 deg/min threshold every tick and re-fired the event continuously.
        # Combined with hysteresis (trigger at the limit, only clear well below),
        # this yields one event per genuine runaway onset.
        if len(s._temp_history) >= 3:
            oldest_temp = s._temp_history[0][1]
            span_min = max(len(s._temp_history) * dt / 60.0, 1e-6)
            rate_deg_per_min = (bat_temp - oldest_temp) / span_min
            high = self._thermal_runaway_rate          # 2.0 deg/min — trigger
            low = self._thermal_runaway_rate * 0.5      # 1.0 deg/min — clear
            if abs(rate_deg_per_min) > high:
                runaway_now = True
            elif abs(rate_deg_per_min) < low:
                runaway_now = False
            else:
                runaway_now = s._prev_thermal_runaway   # hold state inside deadband
            # Rising-edge: fire once when the rate first exceeds the limit.
            if runaway_now and not s._prev_thermal_runaway:
                events.append({"event_id": 0x0409, "severity": "HIGH", "subsystem": "tcs",
                              "description": f"THERMAL_RUNAWAY: Battery rate {rate_deg_per_min:.1f} deg/min"})
            s._prev_thermal_runaway = runaway_now

        # Track temperature for rate calculation
        s._temp_history.append((0, bat_temp))
        if len(s._temp_history) > 10:
            s._temp_history.pop(0)

        # FPA thermal readiness (G3-d).
        #
        # This used to be `warn_low <= T <= warn_high` off the event
        # thresholds, which forced those thresholds to be an imaging-readiness
        # band ([-50, -5]) rather than a health band — the root of the FPA's
        # five-way disagreement. Worse, it was absolute: after Phase E made
        # the setpoint commandable, a perfectly regulated node at a commanded
        # -2 C reported NOT READY while the payload's own flag reported READY.
        #
        # Readiness is now the same rule in both subsystems: the loop has
        # settled about the ACTIVE setpoint, AND the detector is cold enough
        # for the dark current to be tolerable.
        fpa_ready = self._fpa_env.is_ready(fpa_temp, self._fpa_cooler_target)
        if fpa_ready and not s._prev_fpa_ready:
            events.append({"event_id": 0x040A, "severity": "INFO", "subsystem": "tcs",
                          "description": f"FPA_THERMAL_READY: FPA {fpa_temp:.1f}C in operational range"})
            s._prev_fpa_ready = True
        elif not fpa_ready and s._prev_fpa_ready:
            events.append({"event_id": 0x040B, "severity": "MEDIUM", "subsystem": "tcs",
                          "description": f"FPA_THERMAL_NOT_READY: FPA {fpa_temp:.1f}C out of range"})
            s._prev_fpa_ready = False

        # Dispatch all events to the engine (defect #23)
        for event in events:
            try:
                self._engine._model_event_queue.put_nowait(event)
            except Exception:
                pass  # Queue full, skip event

    def tick(self, dt: float, orbit_state: Any, shared_params: dict[int, float]) -> None:
        s = self._state

        # ── 1. Heater circuits: thermostat / manual / failure state ─────
        # (logic unchanged from the zone model; only the physics moved)
        # Battery: thermostat-controlled, gated on EPS power line 5 (0x0115).
        bat_eps_on = bool(shared_params.get(0x0115, 0))
        if bat_eps_on:
            self._thermostat_control("battery", s.temp_battery)
        else:
            s.htr_battery = False  # No power -> heater off
        if s.htr_battery_stuck_on:
            s.htr_battery = True  # Cannot turn off

        # OBC (defect #11): auto = thermostat on the obc setpoints while
        # line 6 (0x0116) is powered; a direct HEATER_OBC command (manual)
        # is honoured but can only energise with the line powered (P1,
        # 2026-11-02: a real smallsat leaves its heater lines powered under
        # thermostat control).
        obc_eps_on = bool(shared_params.get(0x0116, 0))
        if getattr(s, "htr_obc_manual", False):
            s.htr_obc = bool(s.htr_obc) and obc_eps_on
        elif obc_eps_on:
            self._thermostat_control("obc", s.temp_obc)
        else:
            s.htr_obc = False

        # Thruster catbed (Phase D): gated on the EPS `prop` line (0x014A);
        # manual by default, HEATER_AUTO_MODE circuit=2 runs the 190/230 C
        # hold.
        prop_line_on = bool(shared_params.get(0x014A, 0))
        if not prop_line_on:
            s.htr_thruster = False   # no power -> heater off
        elif not s.htr_thruster_manual:
            self._thermostat_control("thruster", s.temp_thruster)
        if s.htr_thruster_stuck_on:
            s.htr_thruster = True

        # Defect #31: heater duty-cycle limits. If the measured duty for a
        # circuit has reached its configured limit (<100 %), the heater is
        # forced off. Applied BEFORE the physics now, so a limited heater
        # really delivers no heat this step (it used to heat, then switch).
        for circuit in ("battery", "obc", "thruster"):
            limit = getattr(s, f"htr_{circuit}_duty_limit_pct", 100.0)
            if limit < 100.0 and getattr(s, f"htr_duty_{circuit}", 0.0) >= limit:
                setattr(s, f"htr_{circuit}", False)

        if self._unpowered():
            # Before the separation timer expires nothing is powered — not
            # even a heater line that was left ON in the configuration.
            s.htr_battery = s.htr_obc = s.htr_thruster = False
        htr_w = {}
        for circuit in ("battery", "obc", "thruster"):
            on = getattr(s, f"htr_{circuit}")
            open_c = getattr(s, f"htr_{circuit}_open_circuit", False)
            htr_w[circuit] = self._HEATER_POWER[circuit] if (on and not open_c) else 0.0

        # ── 2. Thermal network step (THERMAL_MODEL.md) ──────────────────
        net = self._net
        self._sync_in()
        geo = self._geometry(orbit_state, shared_params)
        env = dict(self._env)
        d_km = getattr(geo, "sun_dist_km", None)
        if env.get("scale_solar_with_distance", True) and d_km:
            env["solar_flux_w_m2"] = env["solar_flux_w_m2"] * (
                tn.AU_KM / d_km) ** 2
        power, array_w = self._electrical_inputs(shared_params, htr_w)
        q_abs, emit_ea = tn.absorbed_flux(net, geo, env, array_w)
        idx = net.index
        # Failure: extra dissipation inside the OBC box.
        if "obc" in idx:
            power[idx["obc"]] += s.obc_internal_heat_w
        # Catbed decomposition heat while FIRING (prop.state 0x0B00 == 2).
        if "thruster" in idx and int(shared_params.get(0x0B00, 0)) == 2:
            power[idx["thruster"]] += 30.0
        # Instructor cold soak: an extra heat leak G_soak x offset out of the
        # zone (offset < 0), i.e. the zone's mounting interface is `offset`
        # colder than the rest of the spacecraft. The thermostat sees the
        # result and a powered heater fights it.
        for zone, off in s.cold_soak.items():
            if zone in idx:
                power[idx[zone]] += self._soak_g.get(zone, 0.0) * float(off)
        # Stowed wings lie on their body face (contact conductance).
        extra = []
        for wing, panel in self._wing_panels.items():
            side = 0 if wing.endswith("py") else 1
            if wing in idx and panel in idx and not geo.wings_deployed[side]:
                extra.append((idx[wing], idx[panel], self._stowed_contact))

        # ── 3. FPA (single node, controlled; brief 05 WP-1 / 2026-08b) ──
        # Unchanged control law: the cooler drives the node towards its
        # setpoint, bounded by the efficiency-limited lift below the sink.
        # The sink is now the PAYLOAD node (the instrument the cold finger
        # is mounted in) instead of the fixed +12 C internal sink, and the
        # heat the FPA gains/loses is taken from/given to that node, so
        # energy is conserved. The cooler's 15 W of electrical input is
        # dissipation in the network (fpa_cooler line, tcs.yaml).
        sink_c = self._solver.temp_c(self._fpa_sink_node) \
            if self._fpa_sink_node in idx else 12.0
        fpa_line_on = (bool(shared_params.get(0x0114, 0))
                       if 0x0114 in shared_params else True)
        s.cooler_fpa_active = bool(s.cooler_fpa and fpa_line_on
                                   and not s.cooler_failed)
        t_fpa0 = s.temp_fpa
        if s.decontamination_active:
            # Defect #31: the bake-out actively heats the FPA towards its
            # target, overriding the cooler.
            s.temp_fpa += (s.decontam_fpa_target_c - s.temp_fpa) / self._TAU["fpa"] * dt
        else:
            if s.cooler_fpa_active:
                q_load = (self._fpa_imaging_load_w
                          if int(shared_params.get(0x0600, 0)) == 2 else 0.0)
                s.fpa_cooler_floor_c = sink_c - self._fpa_achievable_lift_k(
                    sink_c, q_load)
                fpa_target = max(self._fpa_cooler_target, s.fpa_cooler_floor_c)
            else:
                s.fpa_cooler_floor_c = sink_c
                fpa_target = sink_c
            s.fpa_cooler_margin_k = (self._fpa_cooler_target
                                     - s.fpa_cooler_floor_c)
            k = min(1.0, dt / self._TAU["fpa"]) if dt > 0 else 0.0
            s.temp_fpa += (fpa_target - s.temp_fpa) * k
        if dt > 0 and self._fpa_sink_node in idx:
            power[idx[self._fpa_sink_node]] -= (
                self._CAP["fpa"] * (s.temp_fpa - t_fpa0) / dt)

        self._last_radiated_j = self._solver.step(dt, q_abs, emit_ea, power, extra)
        self._last_inputs = {"q_abs": q_abs, "emit_ea": emit_ea,
                             "power": power, "geometry": geo}
        self._sync_out()

        # Phase 4: Heater duty cycle tracking
        decay = dt / s._duty_window_s
        for circuit in ("battery", "obc", "thruster"):
            on = getattr(s, f"htr_{circuit}")
            if on:
                s._htr_on_accum[circuit] += dt
            # Exponential decay to approximate sliding window
            s._htr_on_accum[circuit] *= (1.0 - decay)
            duty = min(100.0, s._htr_on_accum[circuit] / s._duty_window_s * 100.0)
            setattr(s, f"htr_duty_{circuit}", duty)

        # Total heater power
        s.htr_total_power_w = 0.0
        if s.htr_battery:
            s.htr_total_power_w += self._HEATER_POWER["battery"]
        if s.htr_obc:
            s.htr_total_power_w += self._HEATER_POWER["obc"]
        if s.htr_thruster:
            s.htr_total_power_w += self._HEATER_POWER["thruster"]

        # Write shared params — apply sensor drift offsets for failure simulation
        p = self._param_ids
        # Sensor drift (failure) plus thermistor measurement noise. The
        # physics itself is deterministic now (the zone model's process
        # noise is gone); the noise lives where it does on a spacecraft, in
        # the measurement. sensor_noise_k in tcs.yaml `network:`.
        sig = self._sensor_noise_k
        if sig > 0.0:
            drift = {z: s.sensor_drift.get(z, 0.0) + self.rng.gauss(0.0, sig)
                     for z in ("panel_px", "panel_mx", "panel_py", "panel_my",
                               "panel_pz", "panel_mz", "obc", "battery",
                               "fpa", "thruster")}
        else:
            drift = s.sensor_drift

        shared_params[p.get("temp_panel_px",0x0400)] = s.temp_panel_px + drift.get("panel_px", 0.0)
        shared_params[p.get("temp_panel_mx",0x0401)] = s.temp_panel_mx + drift.get("panel_mx", 0.0)
        shared_params[p.get("temp_panel_py",0x0402)] = s.temp_panel_py + drift.get("panel_py", 0.0)
        shared_params[p.get("temp_panel_my",0x0403)] = s.temp_panel_my + drift.get("panel_my", 0.0)
        shared_params[p.get("temp_panel_pz",0x0404)] = s.temp_panel_pz + drift.get("panel_pz", 0.0)
        shared_params[p.get("temp_panel_mz",0x0405)] = s.temp_panel_mz + drift.get("panel_mz", 0.0)
        shared_params[p.get("temp_obc",0x0406)] = s.temp_obc + drift.get("obc", 0.0)
        shared_params[p.get("temp_battery",0x0407)] = s.temp_battery + drift.get("battery", 0.0)
        shared_params[p.get("temp_fpa",0x0408)] = s.temp_fpa + drift.get("fpa", 0.0)
        shared_params[p.get("temp_thruster",0x0409)] = s.temp_thruster + drift.get("thruster", 0.0)
        shared_params[p.get("htr_battery",0x040A)] = 1 if s.htr_battery else 0
        shared_params[p.get("htr_obc",0x040B)] = 1 if s.htr_obc else 0
        # 0x040C is the EFFECTIVE cooler state (commanded AND powered AND not
        # failed) — the flag EPS bills from and the displays show (WP-2).
        shared_params[p.get("cooler_fpa",0x040C)] = 1 if s.cooler_fpa_active else 0
        # Phase D: htr_thruster publishes at 0x041B (0x040D belongs to
        # ttc.pa_backup_temp — the Phase B collision is NOT reintroduced).
        # EPS bills the 12 W from this parameter via the prop line (0x0B1B).
        shared_params[p.get("htr_thruster", 0x041B)] = 1 if s.htr_thruster else 0
        # 2026-08b cooler authority. Published in the TCS-owned 0x04xx range;
        # the payload mirrors them at 0x064A/0x064B for its own HK structure.
        shared_params[0x0424] = s.fpa_cooler_floor_c
        shared_params[0x0425] = s.fpa_cooler_margin_k
        # 2026-11-03 (Franz's ruling): FPA/imager limit validity. The FPA
        # bands (S12 0x0408 / 0x0601, MCS 0x0408 / 0x0601 / 0x0617) describe a
        # detector that is powered or regulated. With the payload OFF in a
        # long survival the uncooled imager follows its isolated radiator to
        # -23...-27 C, which is not a fault. 1 = payload powered (mode >= 1)
        # or the cooler / decontamination heater running: the monitors are
        # checked; 0 = unchecked (PUS-C validity, s12_definitions.yaml).
        shared_params[0x0426] = 1 if (
            int(shared_params.get(0x0600, 0) or 0) >= 1
            or s.cooler_fpa_active or s.decontamination_active) else 0
        # Phase 4: Flight hardware params
        shared_params[0x040E] = s.htr_duty_battery
        shared_params[0x040F] = s.htr_duty_obc
        shared_params[0x0410] = s.htr_duty_thruster
        shared_params[0x0411] = s.htr_total_power_w
        # Panel temperatures (illumination-coupled, secondary param IDs)
        shared_params[0x0412] = s.temp_panel_px + drift.get("panel_px", 0.0)
        shared_params[0x0413] = s.temp_panel_mx + drift.get("panel_mx", 0.0)
        shared_params[0x0414] = s.temp_panel_py + drift.get("panel_py", 0.0)
        shared_params[0x0415] = s.temp_panel_my + drift.get("panel_my", 0.0)
        shared_params[0x0416] = s.temp_panel_pz + drift.get("panel_pz", 0.0)
        shared_params[0x0417] = s.temp_panel_mz + drift.get("panel_mz", 0.0)

        # New telemetry parameters (Phase 5: Event generation support)
        shared_params[0x0418] = 1.0 if s.decontamination_active else 0.0  # DECONTAMINATION_ACTIVE
        # Thermal gradient (max temp difference between zones)
        all_temps = [s.temp_panel_px, s.temp_panel_mx, s.temp_panel_py, s.temp_panel_my,
                     s.temp_panel_pz, s.temp_panel_mz, s.temp_obc, s.temp_battery, s.temp_fpa]
        thermal_gradient = max(all_temps) - min(all_temps)
        shared_params[0x0419] = thermal_gradient

        # Thermal regulation margin (0x041A) — the minimum distance of any
        # actively-regulated zone to its ALARM band. Declared by the MCS gauge
        # and the planner imaging pre-condition but previously written by
        # nothing (brief 05 finding 12 / WP-7). Negative = a zone is outside
        # its alarm band (e.g. FPA not yet cooled for imaging).
        zones = [("battery", s.temp_battery), ("obc", s.temp_obc)]
        if s.cooler_fpa_active or s.decontamination_active:
            # The FPA only counts while actively regulated (cooler running or
            # bake-out) — unpowered it legitimately floats to ambient.
            zones.append(("fpa", s.temp_fpa))
        margin = 999.0
        for zone, temp in zones:
            lo, hi = self._temp_alarm_limits.get(zone, (-999.0, 999.0))
            margin = min(margin, hi - temp, temp - lo)
        shared_params[0x041A] = margin

        # Radiator panel temperatures (0x0420/0x0421). Simple derived nodes:
        # the north/south radiator edges ride the -Z panel (nadir-facing in
        # NOMINAL; it carries the radiator and the imager aperture — ruling
        # Q4) a few kelvin colder. Declared in parameters.yaml since Phase 5 but
        # never written; full radiator physics is deferred (WP-8 out-of-scope
        # note) — these are honest first-order proxies, not stubs.
        shared_params[0x0420] = s.temp_panel_mz - 4.0
        shared_params[0x0421] = s.temp_panel_mz - 5.0

        # Setpoint readback (0x0330, 0x0331) — DEFECT 3 fix
        # Allow operators to verify heater setpoints after command via S20 parameter read
        shared_params[0x0330] = s.htr_battery_setpoint_on_c
        shared_params[0x0331] = s.htr_obc_setpoint_on_c

        # Generate events
        self._generate_events(dt)

    def get_telemetry(self) -> dict[int, float]:
        return {0x0408: self._state.temp_fpa, 0x0407: self._state.temp_battery}

    def handle_command(self, cmd: dict[str, Any]) -> dict[str, Any]:
        command = cmd.get("command", "")
        if command == "heater":
            circuit = cmd.get("circuit", "battery")
            on = bool(cmd.get("on", True))
            failed = getattr(self._state, f"htr_{circuit}_failed", False)
            stuck = getattr(self._state, f"htr_{circuit}_stuck_on", False)
            if stuck:
                return {"success": False, "message": "Heater stuck on, cannot control"}
            if failed and on:
                return {"success": False, "message": "Heater failed"}
            # Fail loudly when the command cannot take effect (brief 05 WP-4):
            # switching a heater ON whose EPS power line is dark used to
            # return success and be silently reverted on the next tick — the
            # trainee saw TC accepted while 0x040A stayed 0 forever.
            if on:
                eng = getattr(self, "_engine", None)
                line_param = {"battery": 0x0115, "obc": 0x0116,
                              "thruster": 0x014A}.get(circuit)
                if eng is not None and line_param is not None \
                        and not bool(getattr(eng, "params", {}).get(line_param, 0)):
                    line_no = {"battery": 5, "obc": 6, "thruster": 8}[circuit]
                    # 0x0004 = "Subsystem unpowered or unreachable"
                    return {"success": False, "error_code": 0x0004,
                            "message": (f"{circuit} heater EPS power line "
                                        f"{line_no} is OFF — command cannot "
                                        f"take effect (EPS_POWER_ON first)")}
            setattr(self._state, f"htr_{circuit}", on)
            # Manual override — disable thermostat auto control
            setattr(self._state, f"htr_{circuit}_manual", True)
            return {"success": True}
        elif command == "set_setpoint":
            circuit_idx = cmd.get("circuit", 0)
            circuits = ["battery", "obc", "thruster"]
            if isinstance(circuit_idx, int) and 0 <= circuit_idx < len(circuits):
                circuit = circuits[circuit_idx]
            elif isinstance(circuit_idx, str) and circuit_idx in circuits:
                circuit = circuit_idx
            else:
                # Unknown circuit index: reject honestly instead of a false
                # success that would pollute state with phantom htr_* fields.
                return {"success": False,
                        "message": f"Unknown heater circuit {circuit_idx!r}"}
            # Defect #31 (historic): a circuit without a heater can never apply a
            # setpoint — reject honestly instead of a false success.
            if circuit in self._NO_HEATER_CIRCUITS:
                return {"success": False,
                        "message": f"No heater on '{circuit}' circuit — setpoint not applicable"}
            on_temp = cmd.get("on_temp")
            off_temp = cmd.get("off_temp")
            if on_temp is not None and off_temp is not None:
                # Update both instance dict and state object
                self._THERMOSTAT[circuit] = (float(off_temp), float(on_temp))
                setattr(self._state, f"htr_{circuit}_setpoint_on_c", float(on_temp))
                setattr(self._state, f"htr_{circuit}_setpoint_off_c", float(off_temp))
                return {"success": True}
            return {"success": False, "message": "Missing on_temp or off_temp"}
        elif command == "auto_mode":
            circuit_idx = cmd.get("circuit", 0)
            circuits = ["battery", "obc", "thruster"]
            if isinstance(circuit_idx, int) and 0 <= circuit_idx < len(circuits):
                circuit = circuits[circuit_idx]
            elif isinstance(circuit_idx, str) and circuit_idx in circuits:
                circuit = circuit_idx
            else:
                return {"success": False,
                        "message": f"Unknown heater circuit {circuit_idx!r}"}
            # Defect #31 (historic). Battery (thermostat) and
            # OBC (manual-override flag, see #11) both honour auto-mode.
            if circuit in self._NO_HEATER_CIRCUITS:
                return {"success": False,
                        "message": f"No heater on '{circuit}' circuit — auto-mode not applicable"}
            setattr(self._state, f"htr_{circuit}_manual", False)
            return {"success": True}
        elif command == "fpa_cooler":
            on = bool(cmd.get("on", True))
            if self._state.cooler_failed and on:
                return {"success": False, "error_code": 0x0006,
                        "message": "FPA cooler has failed — cannot be "
                                   "commanded ON"}
            # ── 2026-08b PL-a: fail loudly when the EPS line is dark ──
            # This handler used to `return {"success": True}` unconditionally,
            # so an operator commanding the cooler on TCS func 43 — the ONLY
            # path COM-009, the mission's only cooler-activation procedure,
            # uses — got a clean S1.7 "execution complete" while 0x040C stayed
            # 0, the node stayed at +11.94 C and FPA READY stayed NO forever.
            # The heater circuit right next door has implemented this exact
            # "the command cannot take effect" refusal since brief 05 WP-4;
            # the cooler is now consistent with it. Service dispatch also
            # energises the line on every request path
            # (`ServiceDispatcher._request_fpa_cooler`), so on the nominal
            # ground path this refusal never fires — it catches the FDIR,
            # procedure and OBCP paths that reach the model directly.
            if on:
                eng = getattr(self, "_engine", None)
                if eng is not None and not bool(
                        getattr(eng, "params", {}).get(0x0114, 0)):
                    # 0x0004 = "Subsystem unpowered or unreachable"
                    return {"success": False, "error_code": 0x0004,
                            "message": "FPA cooler EPS power line 4 is OFF — "
                                       "command cannot take effect "
                                       "(EPS_FPA_COOLER / EPS_POWER_ON first)"}
            self._state.cooler_fpa = on
            return {"success": True}
        elif command == "set_fpa_setpoint":
            # Phase E (brief 05 deferred item): PAYLOAD_COOLER_SETPOINT
            # (S8 func 36) drives the TCS-OWNED FPA node end-to-end — TCS is
            # the single integrator since Phase B (WP-1); the payload's
            # fpa_temp is the detector-side lag onto this node. Same Peltier
            # envelope as the payload model so both sides agree on rejection.
            env = self._fpa_env
            setpoint = float(cmd.get("setpoint_c", env.setpoint_default_c))
            # Same wire-decode epsilon as the payload side: raw 27315 cK
            # decodes to +5.68e-14 degC, which is > 0.0 and was refused.
            setpoint = snap_to_envelope(setpoint, env.setpoint_min_c,
                                        env.setpoint_max_c)
            if not (env.setpoint_min_c <= setpoint <= env.setpoint_max_c):
                return {"success": False, "error_code": 0x0003,
                        "message": f"FPA setpoint {setpoint:.2f} C outside "
                                   f"the Peltier envelope "
                                   f"({env.setpoint_min_c:.0f} C to "
                                   f"{env.setpoint_max_c:.0f} C)"}
            self._fpa_cooler_target = setpoint
            return {"success": True}
        elif command == "set_heater_duty_limit":
            circuit_idx = cmd.get("circuit", 0)
            circuits = ["battery", "obc", "thruster"]
            if isinstance(circuit_idx, int) and 0 <= circuit_idx < len(circuits):
                circuit = circuits[circuit_idx]
            else:
                circuit = str(circuit_idx)
            duty_pct = cmd.get("duty_limit_pct", 100.0)
            duty_pct = max(0.0, min(100.0, float(duty_pct)))
            setattr(self._state, f"htr_{circuit}_duty_limit_pct", duty_pct)
            return {"success": True, "message": f"Heater {circuit} duty limit set to {duty_pct}%"}
        elif command == "decontamination_start":
            self._state.decontamination_active = True
            self._state.decontam_start_time = 0.0
            self._state.decontam_fpa_target_c = cmd.get("target_temp_c", 50.0)
            return {"success": True, "message": "Decontamination heating started"}
        elif command == "decontamination_stop":
            self._state.decontamination_active = False
            return {"success": True, "message": "Decontamination heating stopped"}
        elif command == "get_thermal_map":
            thermal_map = {
                "temp_panel_px": self._state.temp_panel_px,
                "temp_panel_mx": self._state.temp_panel_mx,
                "temp_panel_py": self._state.temp_panel_py,
                "temp_panel_my": self._state.temp_panel_my,
                "temp_panel_pz": self._state.temp_panel_pz,
                "temp_panel_mz": self._state.temp_panel_mz,
                "temp_obc": self._state.temp_obc,
                "temp_battery": self._state.temp_battery,
                "temp_fpa": self._state.temp_fpa,
                "temp_thruster": self._state.temp_thruster,
            }
            # Every thermal-network node (2026-11), including the ones with
            # no published parameter (structure, wings, payload, ...).
            nodes = {n: self.node_temperature(n) for n in self._net.names}
            return {"success": True, "thermal_map": thermal_map,
                    "network_nodes": nodes}
        return {"success": False, "message": f"Unknown: {command}"}

    # ─── Failure injection ───────────────────────────────────────────
    # Declarative parameter specs — single source for the instructor form,
    # FailureManager validation and the scenario content gate.
    _HEATER_CIRCUITS = ["battery", "obc", "thruster"]
    _HEATER_LABELS = ["Battery heater", "OBC heater", "Thruster catbed heater"]
    # Thermal zones = the `temp_<zone>` fields the model publishes.
    _ZONES = ["battery", "obc", "fpa", "thruster",
              "panel_px", "panel_mx", "panel_py", "panel_my",
              "panel_pz", "panel_mz"]

    FAILURE_SPECS = {
        "heater_failure": FailureSpec(
            name="heater_failure", label="Heater circuit failure",
            effect="Selected heater cannot energise — its zone cools to the "
                   "passive equilibrium and the low-temperature limit trips.",
            magnitude=ParamSpec(name="magnitude", type=T_BOOL,
                                label="Failed", default=True),
            params=(enum("circuit", "Heater circuit", _HEATER_CIRCUITS,
                         labels=_HEATER_LABELS, default="battery"),),
        ),
        "heater_stuck_on": FailureSpec(
            name="heater_stuck_on", label="Heater stuck ON",
            effect="Selected heater cannot be commanded off — the zone "
                   "overheats and heater power stays on the EPS budget.",
            magnitude=None,
            params=(enum("circuit", "Heater circuit", _HEATER_CIRCUITS,
                         labels=_HEATER_LABELS, default="battery"),),
        ),
        "heater_open_circuit": FailureSpec(
            name="heater_open_circuit", label="Heater open circuit",
            effect="Heater commands are accepted and the status reads ON, but "
                   "no heat is delivered and no current is drawn — the "
                   "'commanded on but still cooling' teaching case.",
            magnitude=None,
            params=(enum("circuit", "Heater circuit", _HEATER_CIRCUITS,
                         labels=_HEATER_LABELS, default="battery"),),
        ),
        "cooler_failure": FailureSpec(
            name="cooler_failure", label="FPA cooler failure",
            effect="The Stirling-class FPA cooler stops: the focal plane warms "
                   "off its centi-kelvin setpoint and imaging quality degrades.",
            magnitude=ParamSpec(name="magnitude", type=T_BOOL,
                                label="Failed", default=True),
        ),
        "obc_thermal": FailureSpec(
            name="obc_thermal", label="OBC internal heat rise",
            effect="Extra dissipation inside the OBC box drives temp_obc "
                   "(0x0406) up toward its red limit.",
            magnitude=None,
            params=(number("heat_w", "Extra dissipation", unit="W", lo=0.0,
                           hi=200.0, default=30.0, step=0.5),),
        ),
        "sensor_drift": FailureSpec(
            name="sensor_drift", label="Temperature sensor drift",
            effect="Adds a fixed offset to ONE reported zone temperature while "
                   "the true temperature is unchanged — the classic "
                   "'is it the sensor or the hardware?' exercise.",
            magnitude=ParamSpec(
                name="magnitude", type=T_FLOAT, label="Sensor offset",
                unit="degC", min=-100.0, max=100.0, default=10.0, step=0.1),
            params=(enum("zone", "Thermal zone", _ZONES,
                         labels=[z.replace("_", " ").upper() for z in _ZONES],
                         default="battery"),),
        ),
        "cold_soak": FailureSpec(
            name="cold_soak", label="Zone cold soak (heater test)",
            effect="Opens an extra heat leak from a heated zone (as if its "
                   "mounting interface were `offset` colder) and steps it "
                   "cold: the zone really cools, its thermostat sees it, and "
                   "the heater can recover it once its EPS line is powered "
                   "(EMG-001/002/003, CTG-004 heater steps).",
            magnitude=None,
            params=(
                enum("zone", "Heated zone", ["battery", "obc", "thruster"],
                     labels=["BATTERY", "OBC", "THRUSTER"], default="battery"),
                # No default: blank = the zone's own default from tcs.yaml
                # network.cold_soak.default_offset_c, sized so that zone's
                # heater can win it back (THERMAL_MODEL.md §5).
                number("offset_c", "Sink offset", unit="degC", lo=-60.0,
                       hi=0.0, default=None, step=0.5,
                       description="Blank = the zone's default depth "
                                   "(tcs.yaml network.cold_soak), sized so "
                                   "its heater can recover it."),
            ),
        ),
        "temp_anomaly": FailureSpec(
            name="temp_anomaly", label="Zone over-temperature",
            effect="Pushes a zone over its red limit and holds it there, "
                   "driving the thermal-exceedance contingency.",
            magnitude=None,
            params=(
                enum("zone", "Thermal zone", _ZONES,
                     labels=[z.replace("_", " ").upper() for z in _ZONES],
                     default="battery"),
                number("offset_c", "Temperature rise", unit="degC", lo=-100.0,
                       hi=200.0, default=30.0, step=0.5),
            ),
        ),
    }

    def inject_failure(self, failure: str, magnitude: float = 1.0, **kw) -> None:
        if failure == "heater_failure":
            c = kw.get("circuit", "battery")
            setattr(self._state, f"htr_{c}_failed", bool(magnitude))
            if magnitude: setattr(self._state, f"htr_{c}", False)
        elif failure == "cooler_failure":
            self._state.cooler_failed = bool(magnitude)
            if magnitude: self._state.cooler_fpa = False
        elif failure == "obc_thermal":
            self._state.obc_internal_heat_w = float(kw.get("heat_w", 30.0))
        elif failure == "sensor_drift":
            zone = kw.get("zone", "battery")
            self._state.sensor_drift[zone] = magnitude
        elif failure == "heater_stuck_on":
            c = kw.get("circuit", "battery")
            setattr(self._state, f"htr_{c}_stuck_on", True)
            setattr(self._state, f"htr_{c}", True)
        elif failure == "heater_open_circuit":
            c = kw.get("circuit", "battery")
            setattr(self._state, f"htr_{c}_open_circuit", True)

        elif failure == "cold_soak":
            zone = kw.get("zone", "battery")
            if zone in ("battery", "obc", "thruster"):
                # No offset given = the zone's own default, re-derived on the
                # thermal network (tcs.yaml network.cold_soak).
                if kw.get("offset_c") is None:
                    offset_c = self._soak_default.get(zone, -25.0) * float(magnitude or 1.0)
                else:
                    offset_c = float(kw["offset_c"])
                self._state.cold_soak[zone] = offset_c
                attr = f"temp_{zone}"
                setattr(self._state, attr, getattr(self._state, attr) + offset_c)

        elif failure == "temp_anomaly":
            # Force a sensor over its red line — drives thermal_exceedance.md.
            zone = kw.get("zone", "battery")
            offset_c = float(kw.get("offset_c", magnitude * 30.0))
            attr = f"temp_{zone}"
            if hasattr(self._state, attr):
                setattr(self._state, attr, getattr(self._state, attr) + offset_c)
            # Persist via sensor_drift so subsequent ticks keep it elevated.
            self._state.sensor_drift[zone] = self._state.sensor_drift.get(zone, 0.0) + offset_c

    def clear_failure(self, failure: str, **kw) -> None:
        if failure == "heater_failure":
            c = kw.get("circuit", "battery")
            setattr(self._state, f"htr_{c}_failed", False)
        elif failure == "cooler_failure":
            self._state.cooler_failed = False
        elif failure == "obc_thermal":
            self._state.obc_internal_heat_w = 0.0
        elif failure == "sensor_drift":
            zone = kw.get("zone", "battery")
            self._state.sensor_drift.pop(zone, None)
        elif failure == "heater_stuck_on":
            c = kw.get("circuit", "battery")
            setattr(self._state, f"htr_{c}_stuck_on", False)
        elif failure == "heater_open_circuit":
            c = kw.get("circuit", "battery")
            setattr(self._state, f"htr_{c}_open_circuit", False)

        elif failure == "temp_anomaly":
            zone = kw.get("zone", "battery")
            self._state.sensor_drift.pop(zone, None)
        elif failure == "cold_soak":
            zone = kw.get("zone")
            if zone:
                self._state.cold_soak.pop(zone, None)
            else:
                self._state.cold_soak.clear()

    def get_state(self) -> dict[str, Any]:
        import dataclasses
        from smo_common.state import rng_state_to_json
        d = dataclasses.asdict(self._state)
        d["_rng_state"] = rng_state_to_json(self.rng.getstate())
        # The commanded FPA setpoint lives on the model, not on _state, so
        # `dataclasses.asdict` missed it and a breakpoint load silently reset
        # the cooler to the configured default (B-2 class, found in G3-d).
        d["_fpa_cooler_target"] = self._fpa_cooler_target
        return d

    def set_state(self, state: dict[str, Any]) -> None:
        # Container fields are deep-copied by restore_dataclass_state: the
        # plain setattr this used to do aliased the snapshot's own dicts and
        # lists into live model state (G2-f).
        from smo_common.state import restore_dataclass_state, restore_rng
        restore_rng(self.rng, state.get("_rng_state"))
        if "_fpa_cooler_target" in state:
            self._fpa_cooler_target = float(state["_fpa_cooler_target"])
        restore_dataclass_state(self._state, state,
                                skip=("_rng_state", "_fpa_cooler_target"))

    def get_battery_temp(self) -> float: return self._state.temp_battery

    # S2 Device Access — device-level on/off control (reserved for future multi-zone variants)
    # NOTE (DEFECT 5): Not used for EOSAT-1. All control via S8 functional commands.
    def set_device_state(self, device_id: int, on_off: bool) -> bool:
        """Set device on/off state. Returns True if successful.
        Reserved for future missions with zone-level heater control."""
        if device_id not in self._state.device_states:
            return False
        self._state.device_states[device_id] = on_off
        return True

    def get_device_state(self, device_id: int) -> bool:
        """Get device on/off state. Returns True if on, False if off or invalid.
        Reserved for future missions with zone-level heater control."""
        return self._state.device_states.get(device_id, False)
