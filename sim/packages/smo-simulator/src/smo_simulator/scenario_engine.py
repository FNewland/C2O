"""SMO Simulator — YAML Scenario Engine.

Loads scenario definitions from YAML, manages execution, tracks operator responses.
Refactored from scenario_engine.py — scenarios are now purely YAML-defined.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ScenarioEvent:
    time_offset_s: float | None = None
    condition: str | None = None
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    fired: bool = False


@dataclass
class ScenarioDefinition:
    name: str = ""
    difficulty: str = "BASIC"
    duration_s: float = 1800.0
    briefing: str = ""
    events: list[ScenarioEvent] = field(default_factory=list)
    expected_responses: list[dict[str, Any]] = field(default_factory=list)
    # Commands the scenario marks as harmful (penalised in the score).
    harmful_commands: list[dict[str, Any]] = field(default_factory=list)
    # Compiled scoring rules (scenario_scoring.compile_rules), built at load.
    scoring: Optional[tuple] = None
    # Applied to the simulator when the scenario starts (phase, speed, SoC,
    # pass override, power lines, params, pre-injected failures).
    initial_conditions: dict[str, Any] = field(default_factory=dict)
    # YAML file stem: the stable id the i18n overlay keys use (scn:<id>:name).
    file_id: str = ""


# Actions the scenario engine can actually execute. Anything else is a
# scenario-authoring mistake and is rejected at load time (defect #52).
SUPPORTED_ACTIONS = frozenset({
    "inject", "clear", "set_parameter", "message", "set_speed", "set_phase",
})

# Event id used to surface load-time scenario config errors as real telemetry.
EVENT_SCENARIO_CONFIG_INVALID = 0x0F20


@dataclass
class ScenarioDebrief:
    """Result of one scenario run (scenario_scoring.py has the model).

    ``score_pct`` is None when the scenario declares nothing the simulator can
    check (every expected response is observational) — "not scored", not 0 %.
    ``responses`` lists EVERY expected response with its status and the
    evidence (command, time) that satisfied it, or none.
    """
    name: str = ""
    id: str = ""
    duration_s: float = 0.0
    score_pct: float | None = None
    mttd_s: float | None = None
    mtti_s: float | None = None
    mttr_s: float | None = None
    responses: list[dict] = field(default_factory=list)
    harmful: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    commands: list[dict] = field(default_factory=list)
    marks: list[dict] = field(default_factory=list)
    earned: float = 0.0
    possible: float = 0.0
    penalty: float = 0.0
    ref_s: float = 0.0
    model: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


class ScenarioEngine:
    """Manages scenario loading, execution, and scoring."""

    def __init__(self, failure_manager=None, engine=None, defaults=None):
        self._fm = failure_manager
        self._engine = engine
        # simulation.yaml scenario_defaults: (pydantic model or dict); the
        # fallbacks reproduce the previous hard-coded values.
        self._defaults = {
            "default_duration_s": 1800.0,
            "default_difficulty": "BASIC",
            "eq_tolerance": 0.01,
            "valid_difficulties": ["BASIC", "BEGINNER", "INTERMEDIATE", "ADVANCED"],
            "response_targets_s": {},
        }
        if defaults is not None:
            for key in list(self._defaults):
                val = (defaults.get(key) if isinstance(defaults, dict)
                       else getattr(defaults, key, None))
                if val is not None:
                    self._defaults[key] = val
        # Load-time schema problems (skipped events, bad difficulty, duplicates)
        self._load_issues: list[str] = []
        self._issues_emitted = False
        # subsystem -> implemented failure-mode names (lazily introspected)
        self._failure_registry: dict[str, set[str]] = {}
        self._scenarios: dict[str, ScenarioDefinition] = {}
        self._active: Optional[ScenarioDefinition] = None
        # Scenario progress is measured in SIM seconds accumulated by
        # tick(): a paused simulator must not advance a scenario and an
        # accelerated one must advance it at speed. There used to be a
        # `_start_time = time.monotonic()` beside this that nothing read.
        self._elapsed: float = 0.0
        # Evidence log + scorer of the active run (scenario_scoring.py).
        self._scorer = None
        self._last_debrief: Optional[ScenarioDebrief] = None
        # Failure ids injected by the currently-active scenario, so they can be
        # cleared when the scenario stops (auto-end or manual) and don't leak
        # into the next scenario / free run.
        self._injected_fids: list[str] = []
        # Hooks the engine sets: called just before a scenario inject fires
        # (auto snapshot) and when a scenario starts (new run).
        self.on_before_inject = None
        self.on_start = None

    # ------------------------------------------------------------------
    # Loading + schema validation
    # ------------------------------------------------------------------

    def _known_failures(self, subsystem: str) -> set[str]:
        """Failure-mode names a subsystem model actually implements.

        Read from the declarative catalogue (``failure_catalog``), which is
        built from each model's own ``FAILURE_SPECS`` table — so the registry
        cannot drift from the implementation. Returns an empty set for an
        unknown subsystem; callers then skip the check rather than rejecting.
        """
        if subsystem in self._failure_registry:
            return self._failure_registry[subsystem]
        try:
            from smo_simulator.failure_catalog import canonical_subsystem, catalog
            names = set(catalog().get(canonical_subsystem(subsystem), {}))
        except Exception as e:  # noqa: BLE001 — never let this block loading
            logger.debug("Failure catalogue unavailable for %s: %s", subsystem, e)
            names = set()
        self._failure_registry[subsystem] = names
        return names

    # Keys of an `inject` event's params block that belong to the failure
    # MANAGER (timing/severity), not to the failure's own parameter spec.
    _INJECT_META_KEYS = ("subsystem", "failure", "magnitude", "onset",
                         "duration_s", "onset_duration_s")

    @classmethod
    def _validate_inject_params(cls, params: dict) -> str | None:
        """Validate an inject event's typed parameters. None if it is fine."""
        try:
            from smo_simulator.failure_catalog import validate as _validate
            from smo_simulator.failure_spec import FailureParamError
        except Exception:  # noqa: BLE001 — catalogue unavailable, skip
            return None
        extra = {k: v for k, v in params.items()
                 if k not in cls._INJECT_META_KEYS}
        try:
            _validate(params.get("subsystem", ""), params.get("failure", ""),
                      params.get("magnitude"), extra)
        except FailureParamError as e:
            return str(e)
        return None

    def _validate_event(self, ev_data: dict, scenario_name: str) -> str | None:
        """Return an error string if this event cannot execute, else None."""
        action = ev_data.get("action", "")
        if action not in SUPPORTED_ACTIONS:
            return (f"unknown action {action!r} "
                    f"(supported: {', '.join(sorted(SUPPORTED_ACTIONS))})")
        if action == "inject":
            params = ev_data.get("params", {}) or {}
            subsystem = params.get("subsystem", "")
            failure = params.get("failure", "")
            if not subsystem or not failure:
                return "inject event missing params.subsystem/params.failure"
            known = self._known_failures(subsystem)
            if known and failure not in known:
                return (f"unknown failure {failure!r} for subsystem {subsystem!r} "
                        f"(known: {', '.join(sorted(known))})")
            # Typed-parameter check: a scenario that carries a parameter the
            # failure does not accept (a rename, a removed unit, a value out of
            # range) used to load fine and then hit the model's default unit.
            err = self._validate_inject_params(params)
            if err:
                return err
        if ev_data.get("time_offset_s") is None and not ev_data.get("condition"):
            return "event has neither time_offset_s nor condition — can never fire"
        return None

    def load_scenarios_from_dir(self, scenario_dir: Path) -> None:
        """Load and VALIDATE all YAML scenario files from a directory.

        Events referencing an unimplemented action or an unknown failure mode
        are skipped (not loaded) and recorded as load issues, which are logged
        and emitted as SCENARIO_CONFIG_INVALID events. Previously such events
        loaded fine and then did nothing at run time (defect #52).
        """
        if not scenario_dir.exists():
            return
        defaults = self._defaults
        for path in sorted(scenario_dir.glob("*.yaml")):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                name = data.get("name", path.stem)
                events = []
                for idx, ev_data in enumerate(data.get("events", []) or []):
                    err = self._validate_event(ev_data, name)
                    if err:
                        self._record_issue(path.name, name, idx, err)
                        continue
                    events.append(ScenarioEvent(
                        time_offset_s=ev_data.get("time_offset_s"),
                        condition=ev_data.get("condition"),
                        action=ev_data.get("action", ""),
                        params=ev_data.get("params", {}),
                    ))
                difficulty = data.get("difficulty", defaults["default_difficulty"])
                if difficulty not in defaults["valid_difficulties"]:
                    self._record_issue(
                        path.name, name, -1,
                        f"difficulty {difficulty!r} is not one of "
                        f"{defaults['valid_difficulties']}")
                defn = ScenarioDefinition(
                    name=name,
                    difficulty=difficulty,
                    duration_s=data.get("duration_s", defaults["default_duration_s"]),
                    briefing=data.get("briefing", ""),
                    events=events,
                    expected_responses=data.get("expected_responses", []) or [],
                    harmful_commands=data.get("harmful_commands", []) or [],
                    initial_conditions=data.get("initial_conditions", {}) or {},
                    file_id=path.stem,
                )
                # Scoring declarations are checked at load like events are: a
                # misspelt command or parameter would otherwise score "missed"
                # for a team that did the right thing.
                for err in self._compile_scoring(defn):
                    self._record_issue(path.name, name, -1, err)
                if defn.name in self._scenarios:
                    self._record_issue(path.name, defn.name, -1,
                                       "duplicate scenario name — previous definition replaced")
                self._scenarios[defn.name] = defn
                logger.info("Loaded scenario: %s (%d events)", defn.name, len(defn.events))
            except Exception as e:
                logger.warning("Failed to load scenario %s: %s", path.name, e)
                self._record_issue(path.name, path.stem, -1, f"parse error: {e}")

    def _config_dir(self):
        return getattr(self._engine, "config_dir", None) if self._engine is not None else None

    def _compile_scoring(self, defn: ScenarioDefinition) -> list[str]:
        """Compile expected_responses / harmful_commands; return the errors."""
        from smo_simulator import scenario_scoring as sc
        try:
            catalog = sc._tc_catalog(self._config_dir())
            params = sc._param_ids(self._config_dir())
        except Exception as e:  # noqa: BLE001 — no catalogue: nothing is checkable
            defn.scoring = None
            return [f"scoring disabled: {e}"]
        targets = dict(sc.DEFAULT_TARGETS_S)
        targets.update({str(k): float(v) for k, v in
                        (self._defaults.get("response_targets_s") or {}).items()})
        responses, harmful, errors = sc.compile_rules(
            defn.expected_responses, defn.harmful_commands, catalog=catalog,
            param_ids=params, targets=targets, n_events=len(defn.events))
        defn.scoring = (responses, harmful, catalog)
        return errors

    def _new_scorer(self, defn: ScenarioDefinition):
        from smo_simulator.scenario_scoring import ScenarioScorer
        if defn.scoring is None:
            self._compile_scoring(defn)
        if defn.scoring is None:
            return None
        responses, harmful, catalog = defn.scoring
        return ScenarioScorer(
            responses, harmful, catalog=catalog,
            has_inject_events=any(ev.action == "inject" for ev in defn.events),
            has_initial_failures=bool((defn.initial_conditions or {}).get("failures")))

    def _record_issue(self, file_name: str, scenario: str, index: int,
                      message: str) -> None:
        where = f"event[{index}]" if index >= 0 else "definition"
        text = f"{file_name}: {scenario}: {where}: {message}"
        logger.warning("Scenario config invalid — %s", text)
        self._load_issues.append(text)

    def load_issues(self) -> list[str]:
        """Load-time scenario schema problems (skipped events, bad difficulty)."""
        return list(self._load_issues)

    def emit_load_issues(self) -> None:
        """Emit one SCENARIO_CONFIG_INVALID event per load issue (once).

        Called by the engine after its TM/dispatcher plumbing exists, because
        scenarios are loaded earlier in engine construction.
        """
        if self._issues_emitted or self._engine is None:
            return
        self._issues_emitted = True
        for text in self._load_issues:
            try:
                self._engine._emit_event({
                    'event_id': EVENT_SCENARIO_CONFIG_INVALID,
                    'severity': 2,
                    'description': f"Scenario config invalid: {text}"[:200],
                })
            except Exception as e:  # noqa: BLE001 — never block startup
                logger.debug("Could not emit scenario load issue: %s", e)

    def list_scenarios(self) -> list[dict]:
        # "id" (YAML file stem) is additive: the instructor UI looks up the
        # French overlay by it (scn:<id>:name / :briefing); "name" stays the key.
        return [{"name": s.name, "difficulty": s.difficulty, "duration_s": s.duration_s,
                 "briefing": s.briefing, "id": s.file_id or s.name}
                for s in self._scenarios.values()]

    def start(self, name: str) -> bool:
        defn = self._scenarios.get(name)
        if defn is None:
            logger.warning("Unknown scenario: %s", name)
            return False
        # Reset fired flags
        for ev in defn.events:
            ev.fired = False
        self._active = defn
        self._elapsed = 0.0
        self._injected_fids = []
        self._scorer = self._new_scorer(defn)
        if callable(self.on_start):
            try:
                self.on_start(defn)
            except Exception as e:  # noqa: BLE001 — never block a scenario start
                logger.warning("Scenario start hook failed: %s", e)
        self._apply_initial_conditions(defn)
        logger.info("Scenario started: %s", name)
        return True

    def _apply_initial_conditions(self, defn: ScenarioDefinition) -> None:
        """Put the simulator into the scenario's declared starting state.

        Supported keys (all optional):
            spacecraft_phase: 0-6      speed: float
            override_passes: bool      soc_pct: float
            power_lines: {name: bool}  params: {param_id: value}
            failures: [{subsystem, failure, magnitude, onset, duration_s}]

        Previously ``initial_conditions:`` was parsed by nothing at all — three
        scenarios carried dead blocks and started in the wrong state (defect #52).
        """
        ic = defn.initial_conditions or {}
        if not ic:
            return
        engine = self._engine
        if engine is None:
            logger.warning("Scenario %s: initial_conditions ignored (no engine)",
                           defn.name)
            return

        phase = ic.get("spacecraft_phase")
        if phase is not None:
            try:
                engine._handle_instructor_cmd({'type': 'set_phase', 'phase': int(phase)})
            except Exception as e:  # noqa: BLE001
                logger.warning("Scenario %s: set_phase failed: %s", defn.name, e)

        if ic.get("speed") is not None:
            self._set_speed(float(ic["speed"]))

        if ic.get("override_passes") is not None:
            try:
                engine._handle_instructor_cmd({
                    'type': 'override_passes', 'value': bool(ic["override_passes"])})
            except Exception as e:  # noqa: BLE001
                logger.warning("Scenario %s: override_passes failed: %s", defn.name, e)

        eps = getattr(engine, "subsystems", {}).get("eps")
        if ic.get("soc_pct") is not None and eps is not None and hasattr(eps, "_state"):
            soc = float(ic["soc_pct"])
            eps._state.bat_soc_pct = soc
            eps._state._prev_soc = soc
            eps._state.bat_dod_pct = 100.0 - soc

        for line, on in (ic.get("power_lines") or {}).items():
            if eps is not None and hasattr(eps, "_state") and line in eps._state.power_lines:
                eps._state.power_lines[line] = bool(on)
            else:
                logger.warning("Scenario %s: unknown power line %r in "
                               "initial_conditions", defn.name, line)

        for pid_raw, value in (ic.get("params") or {}).items():
            try:
                pid = int(pid_raw, 0) if isinstance(pid_raw, str) else int(pid_raw)
                engine.params[pid] = value
            except Exception as e:  # noqa: BLE001
                logger.warning("Scenario %s: bad initial param %r: %s",
                               defn.name, pid_raw, e)

        for f in (ic.get("failures") or []):
            if not self._fm:
                break
            # Pass the TYPED parameters through: this used to forward only
            # subsystem/failure/magnitude/onset/duration_s, so a pre-injected
            # failure lost its unit selector (`wheel`, `unit`, `line_index`,
            # `face`, ...) and silently hit the default unit instead.
            extra = {k: v for k, v in f.items()
                     if k not in ("subsystem", "failure", "magnitude", "onset",
                                  "duration_s", "onset_duration_s")}
            if f.get("onset_duration_s") is not None:
                extra["onset_duration_s"] = float(f["onset_duration_s"])
            fid = self._fm.inject(
                subsystem=f.get("subsystem", ""), failure=f.get("failure", ""),
                magnitude=float(f.get("magnitude", 1.0)),
                onset=f.get("onset", "step"),
                duration_s=float(f.get("duration_s", 0)),
                **extra,
            )
            if fid:
                self._injected_fids.append(fid)
        logger.info("Scenario %s: applied initial conditions %s",
                    defn.name, sorted(ic.keys()))

    def _set_speed(self, value: float) -> None:
        """Set the engine's time acceleration, clamped to simulation.yaml max."""
        engine = self._engine
        if engine is None:
            logger.warning("Scenario set_speed: no engine reference")
            return
        max_speed = float(getattr(engine, "_speed_max", 1000.0))
        speed = max(0.0, min(float(value), max_speed))
        if speed != float(value):
            logger.warning("Scenario set_speed %.1f clamped to %.1f", value, speed)
        engine.speed = speed
        logger.info("Scenario set_speed: %.1fx", speed)

    def stop(self) -> Optional[ScenarioDebrief]:
        """Stop the active scenario, returning (and caching) its debrief.

        Idempotent: returns ``None`` and does nothing if no scenario is active.
        """
        return self._finish(reason="stopped")

    def _finish(self, reason: str) -> Optional[ScenarioDebrief]:
        """Tear down the active scenario exactly once.

        Builds the debrief, caches it on ``self._last_debrief`` for later
        retrieval, clears any failures this scenario injected, resets the
        per-event ``fired`` flags, and deactivates the scenario. Safe to call
        when nothing is active (returns ``None``).
        """
        if self._active is None:
            return None
        debrief = self._build_debrief()
        self._last_debrief = debrief
        # Clear failures injected by this scenario so they don't leak past the
        # scenario's lifetime. Timed injects (finite duration_s) auto-clear via
        # the failure_manager; this also catches indefinite (duration_s<=0)
        # injects that would otherwise stay active forever.
        if self._fm is not None:
            for fid in self._injected_fids:
                try:
                    self._fm.clear(fid)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Scenario stop: failed to clear failure %s: %s",
                                   fid, e)
        self._injected_fids = []
        # Reset fired-event state so the definition can be re-run cleanly.
        for ev in self._active.events:
            ev.fired = False
        logger.info("Scenario '%s' %s after %.1fs (score %s)",
                    self._active.name, reason, debrief.duration_s,
                    "not scored" if debrief.score_pct is None
                    else f"{debrief.score_pct:.0f} %")
        self._active = None
        return debrief

    def last_debrief(self) -> Optional[ScenarioDebrief]:
        """Return the debrief from the most recently finished scenario."""
        return self._last_debrief

    # ─── State save/restore (plan A-4) ───────────────────────────────

    def get_state(self) -> dict:
        """Serialise the running scenario's progress for breakpoint save."""
        state: dict[str, Any] = {"active": None}
        if self._active is not None:
            state.update({
                "active": self._active.name,
                "elapsed": self._elapsed,
                "scoring": self._scorer.get_state() if self._scorer is not None else None,
                "injected_fids": list(self._injected_fids),
                "fired": [i for i, ev in enumerate(self._active.events)
                          if ev.fired],
            })
        return state

    def set_state(self, state: dict) -> None:
        """Restore scenario progress from a breakpoint.

        The scenario definition itself is config (reloaded at boot); only the
        run-time progress is state. A snapshot naming a scenario that is no
        longer configured deactivates cleanly.
        """
        name = state.get("active")
        if not name:
            # No scenario was running at save time; clear any current one
            # WITHOUT firing debrief/cleanup side effects — the restored
            # failure-manager state already reflects the snapshot.
            self._active = None
            self._injected_fids = []
            return
        defn = self._scenarios.get(name)
        if defn is None:
            logger.warning("Breakpoint restore: scenario %r not configured — "
                           "deactivating", name)
            self._active = None
            self._injected_fids = []
            return
        self._active = defn
        self._elapsed = float(state.get("elapsed", 0.0))
        self._scorer = self._new_scorer(defn)
        if self._scorer is not None:
            if state.get("scoring"):
                self._scorer.set_state(state["scoring"])
            else:
                # A pre-scoring snapshot: keep its instructor-recorded responses.
                for r in state.get("responses", []) or []:
                    self._scorer.mark(float(r.get("time_s", 0.0)),
                                      str(r.get("category", "")), str(r.get("description", "")))
        self._injected_fids = list(state.get("injected_fids", []))
        fired = set(int(i) for i in state.get("fired", []))
        for i, ev in enumerate(defn.events):
            ev.fired = i in fired

    def is_active(self) -> bool:
        return self._active is not None

    def current_name(self) -> str:
        return self._active.name if self._active else ""

    @property
    def elapsed_s(self) -> float:
        return self._elapsed

    def tick(self, dt_sim: float, shared_params: dict) -> None:
        if self._active is None:
            return
        self._elapsed += dt_sim

        # Check timed events
        for idx, ev in enumerate(self._active.events):
            if ev.fired:
                continue
            if ev.time_offset_s is not None and self._elapsed >= ev.time_offset_s:
                self._fire_event(ev, idx)
            elif ev.condition is not None:
                if self._eval_condition(ev.condition, shared_params):
                    self._fire_event(ev, idx)
            if self._active is None:     # a hook may have stopped the scenario
                return

        # Resulting-state evidence for the score (cheap: only declared checks).
        if self._scorer is not None and shared_params:
            self._scorer.observe_params(self._elapsed, shared_params)

        # Auto-end on duration: deactivate the scenario so the engine's main
        # loop stops ticking it. Previously this only logged "duration expired"
        # and left ``self._active`` set, so the scenario ran forever.
        if self._elapsed >= self._active.duration_s:
            self._finish(reason="duration expired")

    def _fire_event(self, ev: ScenarioEvent, index: int = -1) -> None:
        action = ev.action
        params = ev.params
        if action == "inject" and callable(self.on_before_inject):
            # Auto snapshot BEFORE the event is marked fired: restoring it
            # puts the team just before the fault, which then fires again.
            try:
                self.on_before_inject(params, index)
            except Exception as e:  # noqa: BLE001 — never block the inject
                logger.warning("Scenario pre-inject hook failed: %s", e)
        ev.fired = True
        if self._scorer is not None:
            self._scorer.observe_event(index, action, self._elapsed)

        if action == "inject" and self._fm:
            fid = self._fm.inject(
                subsystem=params.get("subsystem", ""),
                failure=params.get("failure", ""),
                magnitude=float(params.get("magnitude", 1.0)),
                onset=params.get("onset", "step"),
                duration_s=float(params.get("duration_s", 0)),
                **{k: v for k, v in params.items()
                   if k not in ("subsystem", "failure", "magnitude", "onset", "duration_s")},
            )
            # Track so it can be cleared if the scenario ends while still active.
            if fid:
                self._injected_fids.append(fid)
        elif action == "clear" and self._fm:
            fid = params.get("failure_id", "")
            if fid:
                self._fm.clear(fid)
            else:
                self._fm.clear_all()
        elif action == "set_parameter":
            # Drive a telemetry parameter to a specific value (e.g. force a bus
            # voltage drop in a scenario). Numeric ``param_id`` is supported
            # directly; symbolic ``parameter`` names without a numeric id are
            # logged as unresolved because the scenario engine has no name→id
            # registry. Without this branch, set_parameter events fired silently
            # (no effect, no warning) — broken scenario authoring would look fine.
            if self._engine is None:
                logger.warning("Scenario set_parameter: no engine reference")
                return
            pid_raw = params.get("param_id")
            value = params.get("value")
            if pid_raw is None:
                logger.warning(
                    "Scenario set_parameter: symbolic 'parameter=%s' has no numeric "
                    "param_id — skipping (use hex/decimal param_id instead)",
                    params.get("parameter", "?"))
                return
            try:
                pid = int(pid_raw, 0) if isinstance(pid_raw, str) else int(pid_raw)
                self._engine.params[pid] = value
                logger.info("Scenario set_parameter: 0x%04X = %r", pid, value)
            except Exception as e:
                logger.warning("Scenario set_parameter failed: %s", e)
        elif action == "message":
            logger.info("Scenario message: %s", params.get("text", ""))
        elif action == "set_speed":
            # Time acceleration, e.g. to run through the separation timer and
            # then drop back to real time for the first pass. Accepts
            # params.value or a top-level `value:` mapped in by the loader.
            self._set_speed(float(params.get("value", params.get("speed", 1.0))))
        elif action == "set_phase":
            if self._engine is None:
                logger.warning("Scenario set_phase: no engine reference")
                return
            try:
                self._engine._handle_instructor_cmd({
                    'type': 'set_phase', 'phase': int(params.get("phase", 6))})
                logger.info("Scenario set_phase: %s", params.get("phase"))
            except Exception as e:  # noqa: BLE001
                logger.warning("Scenario set_phase failed: %s", e)
        else:
            # Unrecognised action — surface it so scenario-authoring mistakes
            # are visible. Previously these fired silently.
            logger.warning("Scenario: unknown action %r (params=%r)", action, params)

    def _eval_condition(self, condition: str, params: dict) -> bool:
        """Simple condition evaluator: 'param_name op value'."""
        try:
            parts = condition.split()
            if len(parts) != 3:
                return False
            param_name, op, threshold = parts[0], parts[1], float(parts[2])
            # Try to resolve param name
            value = None
            for pid, val in params.items():
                if str(pid) == param_name:
                    value = float(val)
                    break
            if value is None:
                return False
            if op == "<": return value < threshold
            if op == ">": return value > threshold
            if op == "==": return abs(value - threshold) < self._defaults["eq_tolerance"]
            if op == "<=": return value <= threshold
            if op == ">=": return value >= threshold
        except Exception:
            pass
        return False

    # ── evidence feeds (called by the engine) ────────────────────────
    def observe_tc(self, svc: int, sub: int, data: bytes, apid: int, seq: int,
                   *, link_refused: bool = False) -> None:
        """A telecommand reached the spacecraft (or was refused at the link)."""
        if self._active is None or self._scorer is None:
            return
        self._scorer.observe_tc(self._elapsed, svc, sub, data or b"", apid, seq,
                                link_refused=link_refused)

    def observe_tm(self, pkt: bytes) -> None:
        """A generated TM packet: S1 reports settle each command's fate."""
        if self._active is None or self._scorer is None or len(pkt) < 9:
            return
        try:
            from smo_common.protocol.ecss_packet import decommutate_packet
            from smo_common.protocol.pus_services import VerificationData
            p = decommutate_packet(bytes(pkt))
            if p is None or p.secondary is None or p.secondary.service != 1:
                return
            sub = p.secondary.subtype
            v = VerificationData.parse(p.data_field or b"", sub)
        except Exception:  # noqa: BLE001
            return
        self._scorer.observe_verification(sub, v.tc_apid, v.tc_seq,
                                          v.error_code, v.reason)

    def record_response(self, category: str, description: str = "") -> None:
        """An instructor-recorded response (a mark, not command evidence).

        Listed in the debrief and used for a mean time only where no command
        evidence exists; it never changes the score.
        """
        if self._active is None or self._scorer is None:
            return
        self._scorer.mark(self._elapsed, category, description)

    def live_score(self) -> Optional[dict]:
        """Provisional evaluation of the running scenario (None if idle)."""
        if self._active is None or self._scorer is None:
            return None
        return self._scorer.evaluate(self._elapsed)

    def _build_debrief(self) -> ScenarioDebrief:
        defn = self._active
        base = ScenarioDebrief(name=defn.name, id=defn.file_id or defn.name,
                               duration_s=self._elapsed)
        if self._scorer is None:
            base.responses = [{"i": i, "id": f"r{i}", "category": r.get("category", ""),
                               "description": r.get("description", ""), "status": "observed",
                               "scored": False, "evidence": [], "credit": None,
                               "note": "scoring unavailable"}
                              for i, r in enumerate(defn.expected_responses or [])]
            return base
        ev = self._scorer.evaluate(self._elapsed)
        m = ev["metrics"]
        base.score_pct = ev["score_pct"]
        base.mttd_s = (m.get("mttd") or {}).get("s")
        base.mtti_s = (m.get("mtti") or {}).get("s")
        base.mttr_s = (m.get("mttr") or {}).get("s")
        base.responses = ev["responses"]
        base.harmful = ev["harmful"]
        base.metrics = m
        base.commands = ev["commands"]
        base.marks = ev["marks"]
        base.earned, base.possible, base.penalty = ev["earned"], ev["possible"], ev["penalty"]
        base.ref_s = ev["ref_s"]
        base.model = ev["model"]
        return base
