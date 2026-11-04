# Simulation Configuration Reference (`configs/<mission>/simulation.yaml`)

Single, editable home for the **simulation / scenario** parameters that were
previously Python literals in `engine.py`, `models/eps_basic.py`,
`models/tcs_basic.py`, `fdir.py` and `failure_manager.py` (defect #51).

The file is optional: `load_simulation_config()` returns an all-defaults
`SimulationConfig` when it is missing, and every default reproduces the value
the simulator used before the file existed. Deleting `simulation.yaml` therefore
changes nothing except the item-9 power tuning captured in it.

Schema: `SimulationConfig` in
`packages/smo-common/src/smo_common/config/schemas.py`.
Loader: `load_simulation_config()` in `.../config/loader.py`.

## Which file owns what

| File | Owns |
|---|---|
| `simulation.yaml` | Sim behaviour: tick rate, speed limits, phase timing, protection ladders, initial conditions, thermal environment, failure-onset timing, scenario defaults |
| `subsystems/*.yaml` | **Hardware**: array areas, battery capacity, equipment power ratings, thermal zones/heaters, param ids |
| `mission.yaml` | Identity, APIDs, ports, `network.sim_tick_hz` |
| `orbit.yaml` | TLE, T-0 epoch, canonical ground stations |
| `fdir/`, `monitoring/` | FDIR rules, fault cascades, limit checks, autonomy rules |

No key is defined in two files. Where two files necessarily describe the same
ladder (`simulation.yaml eps.load_shed.soc_stage_thresholds_pct` vs
`fdir/fault_propagation.yaml` stage `soc_threshold`), `simulation.yaml` wins and
the engine logs a warning if the two diverge.

## Key reference

| Key | Meaning | Default | Effect when changed |
|---|---|---|---|
| `tick_hz` | Main-loop rate; `null` inherits `mission.yaml network.sim_tick_hz` | `null` (→1.0 Hz) | Wall-clock resolution of the sim loop; `dt_sim = speed / tick_hz` |
| `speed.default` | Startup time acceleration | 1.0 | Initial `engine.speed` |
| `speed.max` | Clamp applied to every `set_speed` (UI + scenarios) | 1000.0 | Prevents an absurd `dt_sim` stalling the loop |
| `phases.separation_timer_s` | PRE_SEPARATION → INITIAL_POWER_ON countdown | 1800.0 | Length of the LEOP separation wait |
| `ttc.auto_tx_hold_s` | TX line forced ON after any accepted TC (re-armed per TC) | 900.0 (**EOSAT-1: 300**) | Longer hold = more TX energy per pass and defeats the `ttc_tx` shed stage during contacts |
| `eps.initial.soc_pct` | Battery SoC at engine start | 75.0 (**EOSAT-1: 90**) | Starting energy margin; 75 % started inside the old shed band |
| `eps.initial.bat_temp_c` | Battery temperature at start (also the thermal environment) | 15.0 | Battery thermal transient |
| `eps.line_power_w.<line>` | Wattage billed for lines with no rating in `eps.yaml` (`htr_bat`, `htr_obc`, `aocs_wheels`) | 6/4/6 W (**EOSAT-1: 8/4/12**) | Platform load; `aocs_wheels` covers the whole AOCS suite (Phase B, sized for Phase C's 4/9/15 W modes) |
| `eps.heater_duty_from_tcs` | Bill heater lines from the ACTUAL TCS heater state (0x040A/0x040B) instead of 100 % duty while the line is ON | false (**EOSAT-1: true**) | Phase B (brief 01 WP-5): removes the ~8 W phantom heater bill |
| `eps.bus_protection.{uv_v, eps_safe_v, aocs_safe_v, cascade_v, ov_v}` | The bus-voltage protection ladder — ONE named value per decision (2026-11) | 28.4 / 27.7 / 26.1 / 25.9 / 34.0 | uv_v drives `uv_flag`, the in-model shed and S5 0x0103; eps_safe_v S5 0x0104; ov_v `ov_flag`. fdir.yaml / fault_propagation.yaml rules name their level with `threshold_ref`; S12 and MCS limits are held equal by tests/test_content/test_sim_consistency.py. BPX 8S-1P curve: 45.8 / 38.5 / 21.9 / 19.8 % SoC |
| `eps.uv_threshold_v` / `ov_threshold_v` | Harness override of the UV/OV flags | `null` (= bus_protection) | not set by the mission config |
| `eps.load_shed.order` | Bus-voltage shed priority (first = shed first) | payload, fpa_cooler, ttc_tx, aocs_wheels | Which load dies first in a brown-out |
| `eps.load_shed.bus_voltage_v` | Harness override of the shed trigger | `null` (= `bus_protection.uv_v`, 28.4 V ≈ 46 % SoC) | the retired 26.5 V sat at ≈ 65 % SoC, inside the normal eclipse band → shed every orbit |
| `eps.load_shed.restore_hysteresis_v` | Restore margin above the shed voltage | 0.5 | Anti-chatter band |
| `eps.load_shed.auto_restore` | Restore shed lines (one per tick, reverse shed order) once the bus recovers above threshold + hysteresis | false (**EOSAT-1: true**) | Phase B (brief 01 WP-7): the documented restore now exists |
| `eps.load_shed.soc_stage_thresholds_pct` | FDIR shed stage 1/2/3 SoC entry levels | [30, 20, 10] | Canonical source for `LoadSheddingManager`; cross-checked against `fault_propagation.yaml` |
| `eps.overcurrent.thresholds_a.<line>` | Per-line trip current | 150 % of nominal at 28 V | Overcurrent trips and `oc_trip_flags` telemetry |
| `eps.overcurrent.trip_time_s` | Trip delay (immediate at 1 Hz) | 0.05 | Reserved for sub-second ticks |
| `eps.event_thresholds.soc_low_pct` / `soc_critical_pct` | S5 low/critical SoC events | 20 / 10 | Operator warning points |
| `eps.event_thresholds.soc_charge_complete_pct` | Charge-complete event | 99.0 | — |
| `eps.event_thresholds.bus_warning_v` / `bus_critical_v` | Harness override of the bus undervoltage events | `null` (= `bus_protection.uv_v` / `eps_safe_v`) | — |
| `eps.event_thresholds.bat_overtemp_c` / `bat_undertemp_c` | Battery temperature events | 45 / −5 | — |
| `eps.event_thresholds.sa_degraded_fraction` | Array-degraded event trigger (actual < fraction × expected) | 0.7 | Sensitivity of array-degradation detection |
| `tcs.environment.solar_flux_w_m2` / `scale_solar_with_distance` | Solar flux at 1 AU; scaled by (1 AU / r)² from the propagator's Sun vector (2026-11 thermal network) | 1361 / true | Absorbed sunlight on every external surface (≈1322 W/m² July, 1414 January) |
| `tcs.environment.albedo` / `earth_ir_w_m2` | Orbit-average Earth albedo and outgoing long-wave radiation (Gilmore ch. 2) | 0.30 / 237 | Albedo and Earth-IR heating through the flat-plate Earth view factor. The old fixed sink keys (eclipse/sunlit internal and external sinks, battery sink, panel solar-heat fraction/gain) were removed with the zone model; the network itself lives in `subsystems/tcs.yaml network:` (docs/plan_2026-11/THERMAL_MODEL.md) |
| `failures.default_onset_duration_s` | `onset: gradual` ramp time | 90.0 | How fast injected failures reach full magnitude |
| `failures.intermittent.first_flicker_s` / `on_s` / `off_s` | Intermittent-failure timing ranges | [2,6] / [2,8] / [5,20] | Flicker cadence of intermittent injects |
| `scenario_defaults.default_duration_s` | Scenario duration when the YAML omits it | 1800.0 | Auto-stop point |
| `scenario_defaults.default_difficulty` / `valid_difficulties` | Difficulty default and accepted values | BASIC / BASIC, BEGINNER, INTERMEDIATE, ADVANCED | Load-time validation warning |
| `scenario_defaults.eq_tolerance` | Tolerance of `==` in scenario `condition:` | 0.01 | Condition sensitivity |
| `scenario_defaults.response_targets_s` | Scenario score: target time (s after the first fault) per response category, unless the response sets `within_s` | detect 300, isolate 600, recover 900, verify 1200, command/action/monitor 600, plan 1800 | "done" vs "late" (50 %) in the debrief (`scenario_scoring.py`) |
| `auto_snapshots.dir` | Folder of the automatic snapshots taken before each injected fault (`SMO_AUTO_SNAPSHOT_DIR` overrides) | `workspace/snapshots/auto` | Where an instructor restores from after a restart |
| `auto_snapshots.keep_per_run` / `max_age_h` | Newest N per scenario run (or free run); age limit | 10 / 48 h | Disk use; a new scenario run deletes the previous runs' files |
| `auto_snapshots.max_snapshot_mb` / `max_total_mb` / `min_free_mb` | Per-snapshot cap (above: memory only), folder cap, free-disk floor | 25 / 250 / 200 MB | Bounded disk use |

## Scenario YAML schema (validated at load — defect #52)

Top level: `name`, `difficulty`, `duration_s`, `briefing`, `initial_conditions`,
`events`, `expected_responses`, `harmful_commands`.

```yaml
initial_conditions:      # applied by the scenario engine on start()
  spacecraft_phase: 0    # 0..6, routed through the set_phase command
  speed: 10              # clamped to speed.max
  override_passes: true  # force RF contact
  soc_pct: 95.0          # battery SoC
  power_lines: {aocs_wheels: true}
  params: {0x0101: 95.0} # raw parameter pre-sets
  failures:              # pre-injected failures
    - {subsystem: eps, failure: bus_short, magnitude: 1.0}

events:
  - time_offset_s: 300   # or `condition: "<param_id> <op> <value>"`
    action: inject | clear | set_parameter | message | set_speed | set_phase
    params: {...}
```

Load-time validation rejects (skips, and records a `SCENARIO_CONFIG_INVALID`
event 0x0F20) any event that:

* uses an action outside the supported set;
* injects a failure mode the target subsystem model does not implement
  (the registry is introspected from the model's own `inject_failure`);
* has neither `time_offset_s` nor `condition` (it could never fire).

The score is computed from the team's telecommands and the resulting state
(`smo_simulator/scenario_scoring.py`; the instructor guide, "Scoring a
Scenario", has the model):

```yaml
expected_responses:
  - category: recover            # detect | isolate | recover | verify | command | ...
    description: "..."           # FR overlay key scnresp:<file>.<index>:description
    id: shed                     # optional, for `after:`
    tc: [PAYLOAD_SET_MODE(mode=0|1), EPS_POWER_OFF(line_index=3)]   # any of
    state: "payload.mode <= 1"   # or a list: all of them
    within_s: 900                # default: scenario_defaults.response_targets_s
    after: [isolate_a]           # only counts once these are met
    ref: inject                  # inject (default) | start | event:<index>
    weight: 1
harmful_commands:
  - tc: PAYLOAD_SET_MODE(mode=2)
    reason: "..."                # FR overlay key scnharm:<file>.<index>:reason
    penalty: 10                  # percentage points, once per entry
```

An unknown command, argument or parameter in these fields is a load issue
(same `SCENARIO_CONFIG_INVALID` path); the response stays listed but unchecked.

Ground-segment failures (`ground_failure`) are **not** simulator failures: the
ground station RF chain is modelled in `packages/smo-rfsim` and injected from
the Radio UI, so the affected scenarios carry instructor-cue `message` events
instead.
