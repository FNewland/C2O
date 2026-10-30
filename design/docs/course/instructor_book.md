# SpaceCDF Instructor Book

**Supplement to SpaceCDF_Textbook.pdf · Audience: simulator operator and instructor coach**

This short volume covers the simulator-side material referenced in the
textbook's Part 2 (CubeSat Operations). It is not for trainees on
console; it is the runbook for the person driving the simulator and
the coach watching the room.

Contents:

1. Simulator setup and breakpoints
2. Anomaly scenario catalogue (per-scenario YAML, cue moments, expected operator response)
3. Multi-anomaly composition
4. Coaching protocols and pass-criteria scoring

---

# Chapter 5.10 — Scenario Catalogue

This chapter is the instructor's anomaly-injection menu. For
each scenario, the table gives the YAML filename, scenario name,
difficulty, sim duration, the canonical recovery procedure, and
the recommended cue moment (when in a pass to inject it).

## 5.10.0 Starting the simulator

The simulator takes `--config` (default `configs/eosat1/`),
`--speed` (default 1.0), `--host` and **`--port`**. `--port`
defaults to `$SMO_SIM_HTTP_PORT` and then to **8080**; the MCS and
the planner take their own `--port`, so if 8080 is already in use
on the teaching host, move the simulator rather than the clients:

```
python -m smo_simulator --config configs/eosat1/ --port 8081 --speed 1.0
```

Two operating rules that shape everything below:

* **Phase transitions past LEOP are flight telecommands.** Nothing on
  board advances the phase beyond 4 (LEOP): the team declares
  COMMISSIONING (5) and NOMINAL (6) with `SYS_SET_MISSION_PHASE(phase=N)`
  (S8.1 func 120; the FORCE flag permits a backwards move). The instructor
  console's `set_phase` (phases 0–6) is an instructor override for setting
  up or repairing a session, and `SET_PHASE` is not an alias of anything
  — expect the team to send func 120 at the end of LEOP-007 and COM-013.
* Instructor commands (`set_speed`, `freeze`, `resume`, `inject`,
  `clear_failure`, `override_passes`, `set_phase`, the
  `scenario_*` calls, breakpoint save/load) go over the instructor
  HTTP channel. That channel **rejects spacecraft telecommands
  with HTTP 403** — real TCs must go through the MCS.

## 5.10.1 Breakpoints (4)

Breakpoints are named full-state snapshots, saved and reloaded from
the instructor UI (`/api/breakpoint/save`, `/api/breakpoint/load`).
A save that cannot serialise every component fails outright rather
than writing a partial snapshot.

| ID | Name | Phase | Use |
|---|---|---|---|
| BP-1 | Nominal Post-Commissioning | 6 (NOMINAL) | Routine pass training (`scenarios/nominal_ops.yaml`) |
| BP-2 | LEOP Day Start | 3 (BOOTLOADER) | Day 3 (`scenarios/first_contact.yaml`) |
| BP-3 | Commissioning Day Start | 4 (LEOP complete) | Day 4 (`scenarios/commissioning_day_start.yaml` — instructor-authored, see below; not in the shipped set) |
| BP-4 | What-If Branch | (any) | Day 5 replay — save a breakpoint before the decision point, then reload it from the instructor UI |

### BP-3 scenario YAML to add to the simulator

Written against the schema the loader actually accepts.
`initial_conditions` supports only `spacecraft_phase`, `speed`,
`override_passes`, `soc_pct`, `power_lines` (by line name),
`params` (by numeric parameter id) and `failures`. Events must use
`time_offset_s` (or a `condition`) plus one of the supported
actions — `inject`, `clear`, `set_parameter`, `message`,
`set_speed`, `set_phase`. Anything else is dropped at load time and
raised as a `SCENARIO_CONFIG_INVALID` event, so a scenario that
looks fine can silently do nothing. `difficulty` must be one of
BASIC / BEGINNER / INTERMEDIATE / ADVANCED.

```yaml
name: "Commissioning Day Start"
difficulty: INTERMEDIATE
duration_s: 14400          # 4 hours of compressed time across multiple passes
briefing: |
  EOSAT-1 has just exited LEOP. The S-band antenna is deployed, the
  application image is running, detumble has completed, time is set,
  and the spacecraft is in phase 4 (LEOP) holding COARSE_SUN.
  Your shift covers the first 4 hours of commissioning across
  ~4 ground passes (compressed).
  Goals for the shift:
    1. Complete the commissioning entry criteria and call for the
       phase advance to 5 (COMMISSIONING). The instructor performs
       that advance on the console — there is no telecommand.
    2. Run COM-001 through COM-008 in order.
    3. Power on the payload, cool the FPA to its -15 C setpoint, and
       complete COM-012 (First Light) before LOS at end of pass 4.

initial_conditions:
  spacecraft_phase: 4
  override_passes: true
  soc_pct: 90.0
  power_lines:
    ttc_tx: true
    htr_bat: true
    htr_obc: true
    aocs_wheels: true
    payload: false
    fpa_cooler: false
    prop: false
  params:
    0x020F: 3        # aocs.mode = COARSE_SUN
    0x0600: 0        # payload.mode = OFF

events:
  - time_offset_s: 600
    action: message
    params:
      text: "Optional: inject eps overcurrent on line 3 during COM-009 payload power-on"
  - time_offset_s: 5400
    action: message
    params:
      text: "Optional: inject tcs cooler_failure during COM-010 FPA cool-down"

expected_responses:
  - { category: command, description: "Report commissioning entry criteria met and request the console phase advance to 5" }
  - { category: command, description: "Run COM-001 EPS Checkout" }
  - { category: command, description: "Run COM-005 AOCS Mode Transitions (COARSE_SUN 3 -> NOMINAL 4 -> FINE_POINT 5)" }
  - { category: command, description: "Run COM-006 TTC Link Verification (LOW 16 kbps / HIGH 128 kbps)" }
  - { category: command, description: "Run COM-008 FDIR Configuration — verify and exercise the rule set; there is no table to load" }
  - { category: command, description: "Run COM-009 Payload Power On (EPS_POWER_ON line_index=3, then PAYLOAD_SET_MODE mode=1)" }
  - { category: command, description: "Run COM-010 FPA Cooler Activation (FPA_COOLER on=1, S8 func 43)" }
  - { category: command, description: "Run COM-012 First Light — capture and assess one image" }
```

Optional anomalies are left as `message` cues rather than pre-armed
injections so the instructor keeps the decision. Inject them live
from the instructor UI when the moment arrives.

## 5.10.2 Anomaly scenario catalogue (36)

Every file below exists in `configs/eosat1/scenarios/`. Sim
durations are the `duration_s` in the file.

| File | Difficulty | Sim duration | What it does | Canonical procedure | Suggested day |
|---|---|---|---|---|---|
| `aocs_actuator_stuck.yaml` | Medium | continuous | Seizes one reaction wheel (`rw_seizure`) — 4 wheels are flown, so this leaves 3 | CTG-026 / CTG-007 | Day 3 LEOP |
| `aocs_sensor_cascade.yaml` | Hard | 2700 s | ST1 fails, +X CSS head fails, the magnetometer fails, then at T+600 s a **persistent 0.05 °/s gyro bias** on all three channels | CTG-008 → CTG-002 | Day 4 |
| `aocs_star_tracker_failure.yaml` | Medium | continuous | Star tracker fails outright | CTG-008 | Day 3 or 4 |
| `aocs_wheel_failure.yaml` | Hard | continuous | Wheel bearing failure mid-pass | CTG-007 | Day 4 (chain with `transponder_failure.yaml`) |
| `eps_anomaly.yaml` | Medium | varies | Generic EPS fault, often paired with `eps_undervoltage` | CTG-001 / CTG-012 | Day 3 or 4 |
| `eps_overcurrent.yaml` | Easy | continuous | Sustained overcurrent on selected line | CTG-012 | Days 2, 3, 4 |
| `eps_progressive_load_shed.yaml` | Hard | 1800 s | Battery cell degrades, forces progressive shed | CTG-001 | Day 4 |
| `eps_solar_panel_loss.yaml` | Hard | continuous | One solar array string fails | CTG-001 | Day 3 |
| `eps_undervoltage.yaml` | Medium | continuous | Voltage drops below caution band | CTG-001 | Day 3 or 4 |
| `first_contact.yaml` | (BP-2) | 5400 s | LEOP Day Start scenario | — | Day 3 |
| `fpa_overtemp.yaml` | Medium | 1200 s | FPA cooler under-spec: it cannot hold the commanded setpoint (default **−15 °C**; envelope −20 to 0 °C), so `payload.cooler_margin_k` (0x064B) goes ≤ 0 | CTG-004 | Day 4 |
| `gs_antenna_failure.yaml` | Very hard | continuous | Primary GS antenna fails mid-pass | CTG-020 (**advisory** card — ground-side only, no spacecraft TCs) | Day 4 |
| `gs_rf_degradation.yaml` | Easy | 600 s | BER climbs over the pass | CTG-014 / CTG-003 | Day 3 |
| `gs_tracking_loss.yaml` | Medium | 300 s | GS antenna loses tracking briefly | CTG-020 | Day 3 or 4 |
| `nominal_ops.yaml` | (BP-1) | continuous | Healthy spacecraft for tools practice | — | Days 1, 2 |
| `obc_bus_failure.yaml` | Hard | continuous | CAN bus A drops | CTG-017 | Day 3 |
| `obc_crash.yaml` | Hard | one-shot | OBC application crash, reboot required | CTG-010 | Day 3 |
| `obc_watchdog.yaml` | Hard | one-shot | Watchdog event mid-procedure | CTG-010 | Day 3 |
| `obdh_bootloader_recovery.yaml` | Medium | continuous | Bootloader will not boot app SW | bootloader-specific | Day 3 |
| `obdh_bus_isolation.yaml` | Medium | continuous | Subsystem CAN node isolation | CTG-017 | Day 3 |
| `payload_corrupt_image.yaml` | Medium | one-shot | Next image returns corrupt | CTG-015 | Day 4 |
| `payload_memory_failure.yaml` | Hard | continuous | Mass-memory ECC errors climbing | payload-specific | Day 4 |
| `rw_bearing.yaml` | Medium | gradual | Wheel bearing wear, current climbs over hours | CTG-007 | Day 4 |
| `separation.yaml` | (LEOP) | one-shot | Separation event | — | n/a Week 3 |
| `separation_sequence.yaml` | (LEOP) | one-shot | Full separation through detumble | — | n/a Week 3 |
| `sequential_checkout.yaml` | (commissioning) | continuous | LEOP-007 walk-through | — | Day 3 reference |
| `transponder_failure.yaml` | Hard | continuous | S-band transponder fails | CTG-003 → **EMG-004** (Loss of Communication) | Day 4 |
| `ttc_no_tm_at_aos.yaml` | Easy | continuous | UHF beacon present but no S-band HK — the two are separate radios | CTG-019 | Day 3 |
| `ttc_pa_overheat.yaml` | Medium | gradual | S-band power amplifier overheating | CTG-003 | Day 3 or 4 |
| `debris_impact_hermes3.yaml` | Hard | one-shot | Conjunction / debris-impact case study | CTG-028 / NOM-004 | Day 3 or 4 |
| `scenario_2_cerise_adcs_fault.yaml` | Hard | continuous | Cerise-style ADCS fault case study | CTG-002 | Day 4 |
| `prop_slow_leak.yaml` | Medium | gradual | Propellant slow leak, tank pressure decaying | CTG-028 | Day 3 or 4 |
| `prop_underperformance.yaml` | Medium | one-shot | Burn delivers less Δv than planned | CTG-028 → NOM-004 replan | Day 3 or 4 |
| `prop_valve_stuck_open.yaml` | Hard | continuous | Isolation valve stuck open | CTG-028 | Day 4 |
| `prop_burn_eclipse_power.yaml` | Hard | one-shot | Manoeuvre attempted into an eclipse power hole | CTG-028 / CTG-001 | Day 4 |
| `prop_attitude_loss_mid_burn.yaml` | Very hard | one-shot | Attitude error exceeds the burn limit mid-firing; on-board abort | CTG-028 → CTG-002 | Day 4 |

**EO-Sat-1 flies propulsion.** A 1U green monoprop, 66.9 m/s total,
for debris avoidance and limited orbit maintenance (not end-of-life
deorbit). Propulsion telecommands are S8 funcs 108–118, telemetry
base 0x0B00, HK SID **9**. A burn re-fits the SGP4 element set, so
passes and eclipses genuinely move afterwards (1 m/s gives Δa
+1.800 km and −33.5 s at +24 h), and time acceleration is clamped
to ≤ 10× while a burn is firing. Do not describe this mission as
having no propulsion.

### Failure injections without a scenario file

The instructor UI can inject any failure the models implement
directly, without a scenario. Ones worth knowing for this week:

| Subsystem | Injection | What it does |
|---|---|---|
| eps | `sada_stuck` | Seizes the solar-array drive. `eps.solar_array_drive_angle` (0x0133) goes flat while the wing currents (0x0146 / 0x0147) start cycling with the orbit — generation drops to the fixed-wing duty |
| eps | `solar_panel_loss`, `bus_short`, `overcurrent`, `undervoltage`, `bat_cell` | the EPS ladder |
| aocs | `gyro_bias` | **Persistent** rate offset — see 18.10 |
| aocs | `rw_seizure`, `rw_bearing`, `st_failure`, `st_blind`, `mag_failure`, `css_head_fail`, `mtq_failure` | the AOCS set |
| tcs | `cooler_failure`, `heater_stuck_on`, `heater_open_circuit`, `sensor_drift` | the thermal set |
| ttc | `primary_failure`, `pa_overheat`, `high_ber`, `antenna_deploy_failed`, `gs_*` (ground-side) | the link set |
| obdh | `watchdog_reset`, `obc_crash`, `bus_failure`, `stuck_in_bootloader` | the platform set |

## 5.10.3 Multi-anomaly composition rules

If you chain two scenarios, the second triggers only after the
first is acknowledged (or after a fixed delay if not). Recommended
chains:

- `aocs_wheel_failure.yaml` + `transponder_failure.yaml` — tests
  multi-system anomaly response. Day 4, very hard.
- `eps_overcurrent.yaml` (payload line) + `payload_corrupt_image.yaml`
  — tests sustained anomaly + cascaded effect. Day 4, medium-hard.
- `gs_antenna_failure.yaml` (Iqaluit) + `gs_rf_degradation.yaml`
  (Troll next pass) — forces the team to operate with degraded
  ground assets only. Day 4, very hard.

Do not chain *three* anomalies unless the cohort is exceptional;
the cognitive load exceeds control room training week's pedagogical
intent.

---

---

# Chapter 2 — Mission Simulation Day (Instructor Walkthrough)

> **Expected reading before this session.** Cal Poly CDS Rev 14 §5 (Launch ICD); SMAD4 Ch. 18.



**Prerequisites:** Sessions 5.1-5.2 (ground segment designed, operations concepts defined)
**References:** ECSS-E-ST-70-11C (Operability), ECSS-E-ST-70-32C (Procedures), ESA OPS-G Training Manual, NASA Mission Operations Directorate Training Handbook

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Execute a simulated LEOP sequence from separation through first telemetry
2. Perform commissioning activities using operational procedures
3. Respond to injected anomalies using the FDIR architecture and contingency procedures
4. Document anomaly response in real-time using structured forms
5. Conduct nominal science operations with live data budget tracking

---

## 1. Simulation Overview & Roles
This session is a **hands-on simulation** of mission operations. The facilitator acts as the "Universe" -- injecting events, anomalies, and time jumps. The team operates the mission using SpaceCDF and their procedures from Chapter 5.2.

### Role Assignments

| Role | Responsibility | SpaceCDF Feature Used |
|------|---------------|---------------------|
| **Flight Director (FD)** | Overall decision authority; coordinates team | Dashboard, all tabs |
| **Spacecraft Controller (SC)** | Sends commands; monitors housekeeping telemetry | ConOps Editor, mode control |
| **Ground Station Operator (GSO)** | Manages antenna scheduling; link acquisition | Data Budget, Link Budget |
| **Payload Operator (PO)** | Plans and executes science observations | Payload parameters, data budget |
| **Flight Dynamics (FD-nav)** | Monitors orbit; plans and calls the manoeuvres (EO-Sat-1 has a 1U green monoprop, 66.9 m/s) | Orbit parameters, PROP tab, sustainability |
| **Anomaly Logger** | Documents all events, anomalies, and decisions | Worksheet 5.3 |

*For smaller teams, combine roles: SC+GSO and PO+FD-nav are natural pairings.*

### Simulation Timeline

| Sim Time | Real Time | Phase | Events |
|----------|----------|-------|--------|
| T+0 to T+1 hr | 0-20 min | LEOP | Separation, beacon acquisition, deploy, health check |
| T+1 hr to T+24 hr | 20-35 min | Early LEOP | SA deploy, ADCS init, comms chain validation |
| T+1 day to T+7 days | 35-50 min | Commissioning | Subsystem checkout, first payload activation |
| T+7 days to T+30 days | 50-65 min | Early Operations | Nominal science, orbit maintenance |
| *Anomaly injection* | 65-85 min | Contingency | Anomaly response exercise |
| T+30 days to T+1 year | 85-100 min | Nominal Operations | Routine operations, data review |
| Debrief | 100-120 min | Wrap-up | Lessons learned, documentation review |

---

## 2. LEOP Simulation
The facilitator narrates the simulation. Time is compressed. Each team executes their LEOP procedure.

### Facilitator Script -- LEOP

**[T+0 -- Separation]**
*"Your satellite has separated from the deployer. Deployment switches have released. The 30-minute timer has started. You are in radio silence -- no RF emissions allowed until the timer expires. What is your spacecraft doing right now?"*

Worked response: Timer counting down. Battery providing power. No subsystems active except OBC running timer.

**[T+30 min -- Timer Expires]**
*"The 30-minute timer has expired. Your OBC has commanded antenna deployment. What do you expect to see?"*

Expected: Antenna deployment command sent. Beacon should begin transmitting.

**[T+35 min -- First Pass Over Ground Station]**
*"Your ground station at [location] has line of sight. The antenna operator reports: carrier detected at [frequency] with Doppler of -25 kHz. Signal strength is -110 dBm. Is this what you expected?"*

Teams should verify:
- Carrier frequency matches expected (accounting for Doppler)
- Signal strength is consistent with link budget at current range
- Beacon data rate is as designed

**[T+40 min -- First Telemetry]**
*"Beacon lock achieved. You are receiving housekeeping telemetry. I am going to read you the first HK frame:"*

| Parameter | Mnemonic (id) | Value | Expected Range | Status |
|-----------|---------------|-------|---------------|--------|
| Bus voltage | `eps.bus_voltage` (0x0105) | 27.9 V | 26 - 30 V | Nominal |
| Battery SoC | `eps.bat_soc` (0x0101) | 88 % | > 50 % | Nominal |
| Power generation | `eps.power_gen` (0x0107) | 12 W | low while tumbling | Nominal |
| OBC temperature | `tcs.temp_obc` (0x0406) | 22 C | -5 to +45 C | Nominal |
| Battery temperature | `tcs.temp_battery` (0x0407) | 19 C | +5 to +35 C | Nominal |
| AOCS mode | `aocs.mode` (0x020F) | 2 (DETUMBLE) | Expected | Nominal |
| Body rates | `aocs.rate_roll/pitch/yaw` (0x0204-06) | 1.4 deg/s | Decreasing | Nominal |
| Running image | `obdh.sw_image` (0x0311) | 0 (BOOTLOADER) | Expected pre-boot | Nominal |
| Antenna status | `ttc.antenna_deployed` (0x0520) | 0 (stowed) | deployed in LEOP-007 | -- |
| Beacon | `ttc.beacon_active` (0x0527) | 1 | Expected | Nominal |
| Link status | `ttc.link_status` (0x0501) | 2 (LOCKED) | 2 = LOCKED | Nominal |
| Uplink status | -- | Not yet attempted | -- | -- |

Note the bus: EO-Sat-1 runs an **8S, 100 Wh** pack — 21.5 V empty,
26.4 V nominal, 29.2 V full, with a ~28 V bus. A 7-8 V reading is
a 2S CubeSat, not this spacecraft. FDIR undervoltage fires at
**24.5 V**.

*"All parameters nominal. Proceed with LEOP sequence."*

**[T+1 hr -- Uplink Validation]**
*"You now attempt your first uplink command. Send a 'NOP' (no operation) command to verify the uplink chain."*

Teams should: compose command, verify encoding, transmit, wait for acknowledgement in telemetry.

---

## 3. Commissioning Simulation
### Facilitator Script -- Commissioning

**[Time Jump: T+24 hr]**
*"Your satellite has completed detumbling. AOCS is in COARSE_SUN (mode 3). All HK parameters are nominal after 8 ground passes. You are ready to begin commissioning. What is your first activity?"*

Expected: AOCS sensor calibration (COM-003) — magnetometer validity check (single unit, nothing to select), sun-sensor head health, and **on-board** gyro bias calibration with `AOCS_GYRO_CALIBRATION` (S8 func 13). There is no ground-computed bias upload.

**[T+3 days -- Payload First Light]**
*"AOCS is calibrated and holding NOMINAL (mode 4) at 0.3 degree attitude error. You are ready for payload first light. Walk me through your procedure."*

Teams execute their science observation procedure from Worksheet 5.2.

**[T+5 days -- First Data Download]**
*"Payload has captured 150 MB of imagery. Your next pass is 12 minutes long over [station]. Can you download all the data in one pass?"*

Teams should calculate:
- Data rate x pass duration x protocol efficiency = available capacity
- Compare to 150 MB -- determine if multiple passes needed
- Plan the download sequence

---

## 4. Anomaly Injection Scenarios
The facilitator selects 2-3 anomalies from the list below, appropriate to the mission design. Teams respond using their FDIR rules and contingency procedures.

### Anomaly Menu (Facilitator selects 2-3)

#### Anomaly A: Battery Under-Voltage

*"During eclipse, you receive an alert: bus voltage has dropped to 24.2 V, below the 24.5 V FDIR undervoltage threshold (the caution band starts at 27.0 V and the in-model load shed at 25.0 V). Battery temperature is 5 C. SoC is estimated at 18%."*

Expected response:
1. Verify FDIR has triggered load shedding (payload off, non-essential heaters off)
2. Check power budget: is consumption > generation?
3. Possible causes: SA degradation, unexpected load, battery degradation, long eclipse
4. Immediate action: Verify safe mode; disable non-essential loads manually
5. Investigation: Review power trends over last 24 hours; compare to power budget

#### Anomaly B: Communication Loss

*"You have not received telemetry for the last 3 scheduled passes (18 hours). The ground station reports pointing and frequency are correct but no carrier detected."*

Expected response:
1. Verify ground station equipment (antenna, LNA, modem) -- rule out ground fault
2. Check with other ground stations (SatNOGS) for any signal detection
3. Consider causes: TX failure, antenna deployment failure, attitude loss (antenna not pointing)
4. Check whether the UHF beacon is still being heard. It is a separate radio on the non-switchable `ttc_rx` line: **PA-off kills the S-band TM while the beacon survives.** Beacon present + S-band silent isolates the fault to the S-band chain.
5. On-board autonomy: the 24-hour no-contact timer will switch to the redundant transponder (FDIR TTC-01)
6. Plan: blind-command the TX chain per CTG-019; if still nothing after two consecutive passes, escalate EMG-004 (Loss of Communication)

#### Anomaly C: ADCS Anomaly -- Loss of Fine Pointing

*"`aocs.att_error` (0x0217) has increased from 0.1 deg to 5 deg. The selected star tracker reports status 4 (failed). `aocs.momentum_saturation_pct` (0x0282) reads 80% -- near saturation."*

Expected response:
1. Diagnose: which head? `aocs.st1_status` (0x0240) / `aocs.st2_status` (0x0243), codes 0 off / 1 boot / 2 tracking / 3 blind / 4 failed. Optical contamination? Sun in FOV?
2. There are **two** trackers -- bring up the other one (`ST2_POWER` func 5 / `ST1_POWER` func 4) and `ST_SELECT` (func 6) before assuming attitude is lost.
3. Check the estimator source bitmask `aocs.est_source` (0x02C1): bit0 ST, bit1 CSS, bit2 MAG, bit3 gyro.
4. Command desaturation with `AOCS_DESATURATE` (S8 func 1). Budget **20-50 min** for a full dump, not five minutes; imaging is inhibited for the duration and the spacecraft returns to its pre-desat mode. Watch `aocs.h_body_mag` (0x02B9) and `aocs.desat_ineffective` (0x029C).
5. If both heads are gone: `AOCS_SET_MODE(mode=3)` COARSE_SUN, the sun-safe hold.
6. Impact assessment: can science continue on CSS + magnetometer + gyro only?

#### Anomaly D: Unexpected Safe Mode Entry

*"Your satellite has autonomously entered Safe Mode. Last telemetry before entry showed: OBC reboot counter incremented by 3 in 10 minutes. All other parameters were nominal."*

Expected response:
1. Investigate: Multiple reboots suggest SEU (Single Event Upset) or firmware bug
2. Check radiation environment: Was the satellite in SAA (South Atlantic Anomaly)?
3. Review FDIR logs (stored in non-volatile memory) for fault triggers
4. Recovery plan: `OBC_SET_MODE(mode=0)` (S8 func 50) back to NOMINAL and `AOCS_SET_MODE` back to the operational mode; re-issue `HK_ENABLE` for any SID lost to a reboot; monitor for recurrence. Note the FDIR rule: `obdh.reboot_count` > 4 escalates to spacecraft emergency.
5. If recurring: Upload software patch to increase SEU robustness

#### Anomaly E: Thermal Exceedance

*"`payload.fpa_temp` (0x0601) has climbed to +19 C during a science observation, outside the FPA health band of −25.5 to +17.5 C, and `payload.fpa_ready` (0x0610) has dropped to 0. `tcs.temp_battery` (0x0407) is 43 C — past the 42 C FDIR heater-off trip and approaching the 45 C over-temperature event."*

Expected response:
1. Immediate: Disable payload to stop heat generation
2. Check attitude: Is the hot radiator face pointing toward the sun?
3. Review thermal model: Was this orbit geometry (high beta angle) predicted?
4. Mitigation: Adjust duty cycle; plan observations for cooler orbit phases
5. If structural: May need to update thermal model and operational constraints

### Anomaly Documentation

For each injected anomaly, teams complete the **Anomaly Response Form** on Worksheet 5.3:

| Field | What to Record |
|-------|---------------|
| Time (sim) | When the anomaly was detected |
| Observation | Exact telemetry values and symptoms |
| Initial assessment | **FDIR severity 0–4** (how serious the event is). Record separately from the **autonomy level 0–3** (who acted: 0 hardware, 1 subsystem SW, 2 OBC FDIR, 3 ground). The two scales are different things and must never be conflated. |
| Diagnosis | Suspected root cause |
| Action taken | Commands sent, procedures executed |
| Result | System state after response |
| Follow-up required | Additional investigation, procedure updates |

---

## 5. Nominal Operations & Debrief
### Nominal Operations
**[Time Jump: T+30 days to T+1 year]**
*"Your mission has been operational for one month. All commissioning activities are complete. You are now in nominal operations. Let's review your operational metrics."*

Teams report:
- Total data downlinked in 30 days vs plan
- Number of science observations completed vs plan
- Any anomalies encountered (from injection exercise)
- Current budget status: power margin (nominal orbit-average load ≈ 28.7 W against ≈ 38 W generation at worst beta), data margin, propellant remaining out of the 66.9 m/s total
- Orbit status: any conjunction alerts? Debris compliance on track?

### Debrief
1. **What went well?**
   - Which procedures worked as written?
   - Which FDIR rules triggered correctly?
   - Where did the team communicate effectively?

2. **What could be improved?**
   - Which procedures needed real-time modification?
   - Were there gaps in the FDIR design?
   - Where did decision-making slow down?

3. **Lessons for the design:**
   - Did the simulation reveal any design weaknesses?
   - Should any requirements be changed based on operational experience?
   - What additional autonomy would help?

---

## Facilitator Notes

### Preparation

- Review each team's ConOps, FDIR rules, and procedures from Chapter 5.2
- Select anomalies appropriate to the point the team has reached (e.g. don't inject a payload anomaly before COM-009 has powered the payload). EO-Sat-1 *does* have propulsion, so the `prop_*` scenarios are all in play once NOM-004 has been briefed.
- Prepare HK data tables for each phase (modify the values in Section 2 to match the team's mission parameters)
- Have backup anomalies ready if teams resolve injections quickly

### Pacing

- LEOP simulation should feel time-pressured (short passes, decisions needed quickly)
- Commissioning can be more relaxed
- Anomaly injection should be challenging but solvable with the team's procedures
- Allow extra time for debrief -- this is where the deepest learning occurs

### Assessment Criteria

Observe and note (for feedback, not formal grading):
- Did the team follow their procedures or improvise?
- Did the Flight Director coordinate effectively?
- Was the anomaly response systematic (detect-diagnose-plan-execute-verify)?
- Did the team document events in real-time?
- Did anyone identify a design flaw during operations?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| LEOP | First 72 hours are critical; every step is time-constrained |
| Commissioning | Systematic subsystem checkout before payload operations |
| Anomaly response | Follow the process: detect, assess, diagnose, plan, execute, verify, document |
| Documentation | Real-time logging is essential -- memory is unreliable under stress |
| FDIR validation | Simulation reveals gaps in FDIR design that analysis alone cannot find |
| Team coordination | Clear roles, communication protocols, and decision authority are essential |
| Design feedback | Operational experience should feed back into design (requirements, FDIR, procedures) |

---

# Anomaly injection menus (moved from textbook Chapters 10 and 11)

*These sections are instructor-only: they list the scenario YAMLs, cue moments, and coaching protocols for anomaly injection during simulation days. Trainees on console should not see them in advance.*


## LEOP anomaly injection menu

## 10.6 Anomaly injection menu (instructor)


## LEOP shift coaching

## 10.8 Coaching during the shift


## Commissioning anomaly injection menu

## 11.6 Anomaly injection menu



---

# Chapter 18 — Anomaly Cue Cards

For each scenario in the Day 3 and Day 4 instructor menus,
this chapter provides a one-page detailed cue card the
instructor uses during the sim and the team uses during
debrief.

Card format:

- **Scenario file**
- **Cue moment** (what in the pass should be happening when
  injection fires)
- **First indicator** (what the operators will see first)
- **Recovery procedure** (the canonical response)
- **Pass criterion** (what defines a successful recovery)
- **Five debrief questions** to ask the team after the pass

### 18.1 No TM at Pass Start (Easy)

- **Cue moment.** Inject at scenario T+0, before any operator
  command. The spacecraft is in BOOTLOADER_OPS; the beacon is
  present but the OBC will not produce full HK even after
  OBC_BOOT_APP.
- **First indicator.** SPACON sees `obdh.sw_image` (0x0311)
  correctly flip to 1 after step 5, but no SID 1 packets arrive
  in the 1-second interval that follows, and the SIDs the operator
  then commands on with `HK_ENABLE` (**S3.5**) — 3 (TCS, 60 s),
  4 (Platform, 8 s), 6 (TT&C, 8 s) — never appear either.
  Note the trap that is *not* the anomaly: application boot
  re-applies `default_enabled_sids: [1, 11]`, so only EPS and the
  Beacon are on by default. A team that has simply forgotten to
  issue `HK_ENABLE` has not found a fault.
- **Recovery procedure.** CTG-019 No Telemetry at Pass Start.
- **Pass criterion.** Team correctly identifies that the
  spacecraft is responding to commands (S1 acks present) but TM
  flow is broken; they invoke CTG-019 within 60 seconds of the
  missing TM; they continue the procedure with blind commanding
  (using S1 acks only as confirmation).
- **Debrief Qs.**
  1. How did SPACON realise full HK wasn't arriving (other than
     waiting for it)?
  2. Did the team correctly distinguish *no TM* from *no
     commanding*?
  3. Did anyone propose invoking EMG-004 (Loss of Communication)?
     Was that justified? (EMG-003 is OBC Reboot, a different
     card.)
  4. At what time did the team decide to continue with blind
     commanding rather than wait?
  5. What was the impact on subsequent procedure steps?

### 18.2 Power-Line Overcurrent (Easy — Day 3 or 4)

- **Cue moment.** During LEOP-007 sequential power-on, inject
  on the line that's about to be enabled — `aocs_wheels`
  (`line_index=7`) or `payload` (`line_index=3`). Or during
  COM-009 payload power-on. Line indices run 0–8: 0 obc,
  1 ttc_rx, 2 ttc_tx, 3 payload, 4 fpa_cooler, 5 htr_bat,
  6 htr_obc, 7 aocs_wheels, 8 prop.
- **First indicator.** EPS sees the per-line current
  (`eps.line_current_N`, 0x0118+N) go over its trip threshold
  (payload 2.5 A, aocs_wheels 0.8 A) for the 50 ms trip time;
  `eps.oc_trip_flags` (0x010D) sets the bit and the line is
  opened autonomously.
- **Recovery procedure.** CTG-012 Overcurrent Response.
- **Pass criterion.** Team acknowledges the FDIR rule within
  20 s; identifies the affected line; files anomaly ticket;
  does NOT re-enable the line in the same pass (the autonomous
  action is correct — leave it off; investigate next shift).
- **Debrief Qs.**
  1. Did the team recognise that FDIR had already opened the
     line, or did they try to issue `EPS_POWER_OFF(line_index=N)`
     (S8 func 20) manually? Did anyone remember that re-enabling
     needs `EPS_RESET_OC_FLAG(line_index=N)` (func 21) *first*?
  2. Did anyone propose re-enabling the line in the same pass?
  3. Was the anomaly ticket filed before pass end?
  4. What downstream procedure steps were affected?
  5. Should the team have invoked the autonomous response
     manually instead of letting FDIR fire (a defensibility
     question — both answers are right depending on context)?

### 18.3 Reaction Wheel Stuck (Medium)

- **Cue moment.** During LEOP-007 step 4 (wheels line energised
  and AOCS booted into DETUMBLE). Inject `rw_seizure` on one wheel
  as it spins up.
- **First indicator.** AOCS sees that wheel's speed
  (`aocs.rw2_speed`, 0x0208 for wheel index 1) pinned at 0 RPM
  while its current (`aocs.rw2_current`, 0x0251) stays high —
  the motor trying to turn a stuck rotor — and its bearing health
  (`aocs.rw2_bearing_health`, 0x0285) collapsing.
- **Recovery procedure.** CTG-026 AOCS Actuator Stuck Recovery /
  CTG-007 Reaction Wheel Anomaly.
- **Pass criterion.** Team identifies the affected wheel within
  60 s; disables it with `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8
  func 2); confirms `aocs.wheels_enabled` (0x0260) = 3; verifies
  detumble continues (B-dot runs on the **magnetorquers**, not the
  wheels, so a stuck wheel does not stop it); files anomaly ticket.
- **Debrief Qs.**
  1. Did AOCS catch the stuck wheel from current draw, or only
     from the FDIR rule?
  2. Was the FD's GO to disable the wheel polled correctly?
  3. Did the team correctly choose to continue detumble rather
     than abandoning — and did anyone spot that detumble never
     needed the wheels in the first place?
  4. Could the team predict the impact on the pointing budget with
     1 of 4 wheels down? (Very little in the mean: a 3-of-4
     pyramid still spans R³ and FINE_POINT holds 0.0188° against
     0.0208° on four. What is lost is the null space — bias-speed
     regulation and zero-crossing avoidance — so short-term
     jitter is worse, and the mode is flagged at
     `aocs.fine_degraded` 0x0299 with the deadband relaxed 4×.)
  5. What's the long-term implication for the mission (e.g.
     reduced agility, more frequent desat)?

### 18.4 Star Tracker Failure (Medium — Day 3 or 4)

- **Cue moment.** Late in LEOP-005 sun acquisition (Day 3), or
  during the COM-005 NOMINAL transition (Day 4).
- **First indicator.** AOCS sees `aocs.st1_status` (0x0240) go to
  **3 (blind)** or **4 (failed)** — the codes are 0 off, 1 boot,
  2 tracking, 3 blind, 4 failed — and `aocs.att_error` (0x0217)
  starts climbing. `aocs.est_innov_rej_count` (0x02C2) rises as
  the estimator gates the bad fixes.
- **Recovery procedure.** CTG-008 Star Tracker Failure.
- **Pass criterion.** Team identifies the failure within 30 s;
  **brings up the second head** (`ST2_POWER(on=1)`, S8 func 5) and
  selects it (`ST_SELECT`, func 6) before treating attitude as
  lost; powers the failed head off (`ST1_POWER(on=0)`, func 4);
  re-initialises the estimator with `AOCS_EST_RESET(mode=1)`
  (func 91, warm) if the solution has diverged; only if *both*
  heads are gone commands COARSE_SUN (`AOCS_SET_MODE(mode=3)`);
  files anomaly ticket.
- **Debrief Qs.**
  1. Did AOCS distinguish blind (3) from failed (4), and what's
     the operational difference?
  2. Did anyone reach for the redundant head first, or did the
     team jump straight to a safe-mode transition? This is a
     two-tracker spacecraft.
  3. Did the team consider deferring imaging if ST2 also fails?
  4. What's the pointing budget on CSS + magnetometer + gyro
     only? (Degrades to roughly a degree — the COARSE_SUN class
     of performance, not the sub-0.1° FINE_POINT budget.)
  5. Mission impact: how many days can the spacecraft operate
     in degraded star-tracker mode before science deliverables
     are missed?

### 18.5 OBC Watchdog Reset (Hard)

- **Cue moment.** Mid-LEOP-007, around step 4 (wheels line and
  AOCS boot). Inject `watchdog_reset` on obdh.
- **First indicator.** All telemetry stops for ~15 s; then the
  UHF beacon comes back with the OBC in BOOTLOADER
  (`obdh.sw_image` 0x0311 = 0), `obdh.reboot_count` (0x030A)
  incremented and `obdh.last_reboot_cause` (0x0316) = 1
  (watchdog).
- **Recovery procedure.** CTG-010 OBDH Watchdog Recovery.
- **Pass criterion.** Team recognises the unexpected reboot
  within 30 s of TM resumption; invokes CTG-010; re-establishes
  application boot (`OBC_BOOT_APP`, S8 func 55 — LEOP-001 step 5);
  **re-issues `HK_ENABLE` (S3.5) for every SID except 1 and 11**,
  because application boot re-applies
  `default_enabled_sids: [1, 11]`; restores time sync
  (`SET_TIME` S9.1); re-clears beacon mode and re-selects the LOW
  tier; logs every step lost; files anomaly ticket.
- **Debrief Qs.**
  1. Did SPACON immediately recognise the bootloader beacon
     pattern?
  2. Did the team avoid panic-commanding while the OBC was
     mid-reboot?
  3. How long from reboot to spacecraft fully recovered?
     (Industry: < 5 min for a clean watchdog recovery.)
  4. Did the team correctly identify which procedure steps
     needed re-execution vs which were preserved?
  5. What's the right way to *prevent* this in future shifts?
     (Hint: ensure watchdog kick is in the procedure pre-conditions
     for long-running activities.)

### 18.6 OBC Bus Failure (Hard)

- **Cue moment.** During LEOP-007, after step 4 (wheels line
  energised, AOCS HK SID 2 appearing).
- **First indicator.** AOCS HK SID 2 stops flowing; OBDH HK
  (SID 4) shows `obdh.bus_a_status` (0x030F) = 1 (ERROR) with
  `obdh.active_bus` (0x030E) = 0 (A).
- **Recovery procedure.** CTG-017 Bus Failure Switchover.
- **Pass criterion.** SPACON recognises bus A failure within
  30 s; commands **`OBC_SELECT_BUS(bus=1)` (S8 func_id 54)** —
  *not* `OBC_SWITCH_UNIT` (func 53), which fails over the OBC
  unit and is CTG-011; verifies `obdh.active_bus` = 1, bus B
  healthy and AOCS HK resumed; files ticket.
- **Debrief Qs.**
  1. How did SPACON distinguish *no AOCS HK* from *bus A
     failure*?
  2. Was the FD GO for switchover authorised cleanly?
  3. Was the recovery faster than the watchdog recovery? Why
     should it be?
  4. Mission impact: are we now running on the redundant bus
     for the rest of the mission? (Yes — bus B can't fail back
     without ground intervention.)
  5. What's the long-term consequence (no more bus redundancy)?

### 18.7 Ground Station Antenna Failure (Very Hard — Day 4)

- **Cue moment.** Mid-pass over Iqaluit, ideally during a
  commanded action.
- **First indicator.** Ground Seg sees Iqaluit antenna gain
  drop; baseband Eb/N0 collapses; TT&C sees BER climb and rx
  lock loss.
- **Recovery procedure.** CTG-020 Ground Station Antenna
  Failure — an **advisory** card. It contains no spacecraft
  telecommands: this is handled entirely on the ground side.
- **Pass criterion.** Team correctly identifies this as a
  ground-side failure (not spacecraft) — `ttc.gs_equipment_status`
  (0x0524) is the bitmask, and a healthy spacecraft is still
  radiating; recognises that the current pass is effectively lost;
  re-plans the remaining activities onto the next station in the
  five-station network (Iqaluit, Troll, Svalbard, Inuvik,
  O'Higgins); files ticket; informs customer (Mission Manager).
- **Debrief Qs.**
  1. Did the team distinguish ground-antenna failure from
     spacecraft TT&C failure?
  2. Did anyone propose escalating to EMG-004 (Loss of Comm)?
     Was that justified? (It should not be — the spacecraft is
     fine.)
  3. Was the re-plan onto the next station done on the ground
     schedule, or did someone try to command the spacecraft for
     a ground fault?
  4. What was the impact on commissioning timeline? Did the
     team miss any time-critical activity (e.g. an eclipse
     window for FPA cool-down)?
  5. Mission Manager: how was the customer bulletin worded?

### 18.8 FPA Cooler Under-Spec (Medium)

- **Cue moment.** During COM-010 FPA cooler activation. The loop
  normally closes in about **10 minutes**, so inject at T+3 to
  T+5 min, while the FPA is still on the ramp between +4 C
  and -8 C.
- **First indicator.** Thermal sees the FPA cool-down flatten
  short of the setpoint; `payload.fpa_ready` (0x0610) never sets;
  `payload.cooler_margin_k` (0x064B) goes **≤ 0** and
  `payload.cooler_floor_c` (0x064A) rises above the commanded
  setpoint. The mirror pair `tcs.fpa_cooler_floor_c` (0x0424) and
  `tcs.fpa_cooler_margin_k` (0x0425) tell the same story on the
  thermal tab.
- **Recovery procedure.** CTG-004 Thermal Exceedance +
  payload-safe.
- **Pass criterion.** Team accepts that the cooler is
  under-spec and understands *why the answer is a warmer
  setpoint, not more waiting* — the cooler is a miniature
  Stirling-class machine at ~23 % of Carnot, so its authority
  falls as the lift grows and a negative margin means the
  setpoint is physically unreachable at the present sink.
  Decides whether to (a) command a warmer setpoint with
  `PAYLOAD_COOLER_SETPOINT` (S8 func 36, uint16 in
  **centi-kelvin**, envelope -20 to 0 C) and continue with
  degraded image quality, or (b) abandon COM-010 and re-plan;
  files ticket; if continuing, runs COM-011 cal and COM-012
  First Light with the warmer FPA.
- **Debrief Qs.**
  1. Did Thermal recognise the flattening cool-down from the
     trend line, or only when `fpa_ready` failed to set?
  2. Did the FD make a clear go/no-go decision on continuing?
  3. Did anyone read `cooler_margin_k` and realise that waiting
     longer could never work? What SNR cost does the warmer
     setpoint carry (`payload.snr`, 0x0616)?
  4. If continuing, was the customer bulletin updated to flag
     the science quality impact?
  5. What's the long-term mission impact if the cooler is
     permanently under-spec?

### 18.9 Corrupt Image Acquired (Medium)

- **Cue moment.** During the COM-012 capture step
  (`PAYLOAD_CAPTURE`, S8 func 28), inject the corruption so the
  resulting image fails its quality assessment.
- **First indicator.** Payload sees S5 event **0x0607
  IMAGE_CHECKSUM_ERROR** after the product is stored, and
  `payload.checksum_errors` (0x0609) increments.
- **Recovery procedure.** CTG-015 Corrupted Image Recovery.
- **Pass criterion.** Team marks the image as failed; re-queues
  for re-acquisition next pass; investigates root cause
  (typically FPA temperature, cosmic ray hit during integration,
  or pointing wobble); files ticket; if re-acquisition succeeds
  next pass, First Light declared.
- **Debrief Qs.**
  1. Did Payload correctly recognise the corruption from the
     0x0607 event, or did they only realise from the quality
     assessment? Did they delete before re-capturing
     (`PAYLOAD_DELETE_IMAGE`, func 30, then `PAYLOAD_CAPTURE`,
     func 28)?
  2. Was the re-acquisition triggered cleanly (i.e. did the
     team re-plan rather than re-running the failed command
     blindly)?
  3. What's the root-cause hypothesis? (Usually cosmic ray for
     a one-off; FPA T for a recurring failure.)
  4. Did the team update the customer bulletin to reflect the
     deferred First Light?
  5. How many image attempts is the team willing to make in one
     shift before formally deferring First Light?

### 18.10 AOCS Sensor Cascade (Hard)

This is `aocs_sensor_cascade.yaml`, and it is where **"IMU drifts"
is real**. The scenario runs 2700 s and fires four injections:

| T+ | Injection | Effect |
|---|---|---|
| 60 s | `st_failure` unit 1 | ST1 → status 4; on-board FDIR should fall to ST2, but the operator must verify |
| 180 s | `css_head_fail` face px | +X coarse sun sensor head dies; composite sun vector degrades |
| 300 s | `mag_failure` | the single magnetometer fails (no B unit, no switch exists); operator must recognise the loss of B-dot and magnetorquer desaturation and protect momentum |
| 600 s | `gyro_bias` axis=all bias=0.05 | **0.05 °/s bias on all three gyro channels** |

The gyro bias is the teaching point and it needs describing
precisely. It is written into the **persistent injected offset**
(`aocs.gyro_bias_injected`, 0x0296 — instructor visibility), not
into the Gauss-Markov truth state, so it does **not** mean-revert
over the 1800 s bias time constant and it **survives ticks and
breakpoint save/load until it is explicitly cleared**. If you
reload a breakpoint expecting a clean spacecraft, clear the
failure first.

0.05 °/s is about 1800× the 0.1 °/h bias instability the MEKF is
built from — and it is **survivable while a star tracker is
healthy**: the filter's bias state absorbs a constant offset. The
operator's only symptoms are a step in the innovation-rejection
counter (`aocs.est_innov_rej_count`, 0x02C2) and
`aocs.gyro_bias_x/y/z` (0x0270–0x0272) diverging from the
estimate. It becomes mission-ending the moment the tracker is also
lost before the filter has re-converged, because ECLIPSE and every
propagate-only phase then drift at 0.05 °/s = **3 °/min**.

Note that the gyros are three single-axis units with **no
redundant unit**, there is no IMU power line and no IMU cold-boot
delay, and gyro bias calibration is on-board
(`AOCS_GYRO_CALIBRATION`, S8 func 13) — not a ground-computed
upload.

- **Cue moment.** Start the scenario just before COM-011 (Payload
  Calibration), so the gyro injection at T+600 s lands around the
  FINE_POINT transition.
- **First indicator.** `aocs.st1_status` (0x0240) → 4 (failed);
  then the sun-vector and magnetometer degradations; then
  `aocs.est_innov_rej_count` (0x02C2) steps up and
  `aocs.att_error` (0x0217) climbs.
- **Recovery procedure.** CTG-008 Star Tracker Failure → CTG-002
  AOCS Anomaly (± CTG-025 AOCS Sensor Loss Recovery) + defer
  First Light.
- **Pass criterion.** Team works the failures in order: verifies
  the fall-back to ST2 (`ST_SELECT`, func 6) rather than assuming
  it; recognises that the magnetometer has no spare (there is no `MAG_SELECT`) and protects momentum; reads
  `aocs.est_source` (0x02C1) to see what the estimator is actually
  using; identifies the gyro bias from 0x0270–0x0272 and the
  rejection counter; recovers gyro knowledge with
  `AOCS_EST_RESET(mode=1)` (S8 **func 91**, warm) once the bias is
  bounded, or accepts ST-only determination. If the pointing
  budget is broken, commands COARSE_SUN
  (`AOCS_SET_MODE(mode=3)`), formally defers First Light, files a
  ticket, tells Mission Manager.
- **Debrief Qs.**
  1. Did the team correctly chain the procedures (CTG-008 for the
     tracker, CTG-002 for the AOCS response)?
  2. Did anyone notice the gyro bias *before* the star tracker
     work was finished — and did they understand why the healthy
     tracker was hiding it?
  3. What happens to this spacecraft at the next eclipse entry
     with the bias uncleared? (Propagate-only at 3 °/min.)
  4. Did anyone propose attempting First Light anyway? Was that
     justified or risky?
  5. Was the formal-deferral decision made by the FD with clear
     team agreement, or unilateral?

### 18.11 Progressive Battery Load-Shed (Hard)

- **Cue moment.** During COM-010 (FPA cooler activation), early
  in the cool-down.
- **First indicator.** EPS sees `eps.bus_voltage` (0x0105)
  trending down unexpectedly and the SoC dropping at roughly
  twice the predicted rate. The ladder the team will walk down:
  bus warning event at 27.0 V, in-model shed at **25.0 V**
  (order payload → fpa_cooler → ttc_tx → aocs_wheels → prop),
  bus critical at 25.0 V, FDIR undervoltage safe-mode at
  **24.5 V**. SoC-driven shed stages sit at 30 / 20 / 10 %
  (`eps.load_shed_stage`, 0x0134).
- **Recovery procedure.** CTG-001 Under-Voltage Load Shed
  (CTG-023 Progressive Load Shed for the staged version).
- **Pass criterion.** Team sheds progressively in priority order —
  payload OFF (`PAYLOAD_SET_MODE(mode=0)`), cooler OFF
  (`FPA_COOLER(on=0)`, func 43), PA off (`TTC_PA_OFF`, func 67),
  wheels line off (`EPS_POWER_OFF(line_index=7)`) — watching for
  recovery between each, rather than dumping everything at once;
  keeps the OBC and receive chain (lines 0 and 1, both
  non-switchable) alive; recognises that the auto-restore walks
  the lines back one per tick once the bus clears 25.5 V; files
  ticket; informs Mission Manager.
- **Debrief Qs.**
  1. Did EPS catch the unexpected SoC trend before FDIR fired,
     or only after?
  2. Was load-shed escalation correct (priority 1 first, watch,
     then escalate)?
  3. Did the team weigh shedding the FPA cooler — which throws
     away the cool-down work — against the fact that it is the
     single biggest switchable load at 15 W?
  4. Was the FD GO chain correct for each escalation?
  5. Root-cause hypothesis? (Usually battery cell degradation
     in real missions.)

### 18.12 `aocs_wheel_failure.yaml` + `transponder_failure.yaml` (Very Hard — Day 4)

This is the multi-anomaly scenario — two faults in quick
succession.

- **Cue moment.** Wheel failure injected mid-Pass 3 during
  imaging; transponder failure injected at start of Pass 4.
- **First indicator (wheel).** AOCS sees that wheel's current
  (`aocs.rwN_current`, 0x0250–0x0253) spike and its speed
  (0x0207–0x020A) drop to 0; `aocs.wheels_enabled` (0x0260)
  falls to 3.
- **First indicator (transponder).** TT&C sees the S-band link
  drop at Pass 4 AOS — `ttc.link_status` (0x0501) ≠ 2, no S1
  acks, no TM — **while the UHF beacon keeps arriving** (HK SID
  11, `ttc.beacon_active` 0x0527 = 1). That contrast is the tell:
  the beacon is a separate radio on a separate band.
- **Recovery procedures.** CTG-007 (wheel) → CTG-003 (link).
- **Pass criterion.** Team handles the wheel failure during
  Pass 3, makes a deliberate decision about Pass 4 (defer
  imaging? image on the remaining three wheels, accepting
  `fine_degraded`?), then when the
  transponder fails at AOS, recognises the second anomaly,
  invokes CTG-003 link recovery, and re-establishes the link
  before LOS.
- **Debrief Qs.**
  1. Did the team correctly handle the first anomaly without
     letting it cascade?
  2. When the second anomaly fired, did anyone confuse the
     symptoms with a continuation of the first?
  3. Was the FD's prioritisation clean (transponder first, then
     wheel work)?
  4. What's the cognitive load lesson here? Multi-anomaly is
     where teams typically break.
  5. Mission Manager: how was the cohort customer bulletin
     worded when *two* things went wrong in one shift?

---
