# EOSAT-1 Fault Detection, Isolation and Recovery (FDIR) {#eosat-1-fault-detection-isolation-and-recovery-fdir}

**Document ID:** EOSAT1-UM-FDIR-009
**Issue:** 2.0
**Date:** 2026-03-13
**Classification:** UNCLASSIFIED — Mission Operations

---

## 1. Overview {#1-overview}

The EOSAT-1 Fault Detection, Isolation and Recovery (FDIR) system provides autonomous
onboard protection against anomalies that could endanger the spacecraft or its mission.
FDIR operates in a hierarchical manner with increasing levels of autonomy and severity,
from local subsystem-level responses to spacecraft-wide safe mode transitions.

The FDIR implementation uses PUS Service 12 (Onboard Monitoring) for parameter limit
checking and PUS Service 19 (Event-Action) for automated response triggering. Both
services are evaluated on every on-board processing cycle, giving continuous
monitoring coverage.

## 2. FDIR Hierarchy {#2-fdir-hierarchy}

### 2.1 Autonomy Levels {#21-autonomy-levels}

| Level | Scope           | Response Time | Authority              | Example                     |
|-------|-----------------|---------------|------------------------|-----------------------------|
| 0     | Unit level      | < 1 s         | Hardware               | PCDU over-current trip      |
| 1     | Subsystem level | 1–10 s        | Subsystem SW           | Heater thermostat control   |
| 2     | System level    | 10–60 s       | OBC FDIR application   | Mode transition, load shed  |
| 3     | Ground level    | Minutes–hours | Flight control team    | Manual recovery procedures  |

### 2.2 Design Philosophy {#22-design-philosophy}

- **Fail-safe**: Any unrecoverable anomaly results in a transition to a power-positive,
  thermally safe, and commandable state (Safe Mode).
- **Minimum intervention**: FDIR acts only to preserve spacecraft safety. Restoration of
  nominal operations is a ground-commanded activity (Level 3).
- **Single-event tolerance**: The FDIR design tolerates a single failure without loss of
  spacecraft safety.

## 3. Safe Mode Definition {#3-safe-mode-definition}

When a critical FDIR rule triggers a safe mode entry, the OBC executes the following
sequence autonomously:

| Step | Action                                          | Subsystem |
|------|-------------------------------------------------|-----------|
| 1    | Set OBC mode to SAFE                            | OBDH      |
| 2    | Command AOCS to COARSE_SUN mode (3)             | AOCS      |
| 3    | Power off payload                               | PLD       |
| 4    | Shed non-essential loads                        | EPS       |
| 5    | Activate essential heaters (battery, OBC)       | TCS       |
| 6    | Reduce TM rate to 0.1 Hz                        | OBDH      |
| 7    | Set TTC to receive-priority mode                | TTC       |
| 8    | Generate safe mode event packet                 | OBDH      |

Safe mode is designed to be power-positive under all illumination conditions, ensuring
the spacecraft can sustain itself indefinitely until ground intervention.

## 4. FDIR Rules and Triggers {#4-fdir-rules-and-triggers}

### 4.1 EPS Rules {#41-eps-rules}

| Rule ID | Condition                      | Detection       | Response                    |
|---------|--------------------------------|----------------|-----------------------------|
| EPS-01  | bat_soc < 15%                  | 0x0101 < 15    | Safe mode entry             |
| EPS-02  | bus_voltage < 26.5 V           | 0x0105 < 26.5  | Safe mode entry             |
| EPS-03  | bat_temp > 45 C                | 0x0102 > 45    | Inhibit battery charge      |
| EPS-04  | bat_temp < 0 C                 | 0x0102 < 0     | Battery heater thermostat (see TCS-01) |
| EPS-05  | String yield < 70 % while lit, 30 s | 0x014C / 0x014D (valid while 0x014E bit set) | Payload line OFF (S19 ea 1004 / 1005) |
| EPS-06  | bus_voltage > 29.5 V           | 0x0105 > 29.5  | Shunt excess power          |

**EPS-05 is judged only in sunlight.** Until November 2026 the solar-array
rules (S19 ea 1004/1005) watched the raw string currents 0x0103/0x0104 against
a 0.1 A floor. Every eclipse entry crosses that floor, so both rules fired at
every eclipse. The S12 monitors now watch the string **yield**: the measured
current as a percentage of what a healthy string would deliver at the present
sun geometry (0x014C `eps.sa_a_yield_pct`, 0x014D `eps.sa_b_yield_pct`). They
also carry a PUS-C validity condition: a monitor is checked only while its
string's bit is set in 0x014E `eps.sa_string_lit` (bit 0 = A, bit 1 = B). The
bit is set when the spacecraft is sunlit, the string is enabled, and a healthy
string would give at least 0.2 A. In eclipse, in deep penumbra, or with the
string facing away from the sun, the monitor is *unchecked*, not violated. A
repetition count of 30 (30 s at 1 Hz) rides through slews and the shadow
boundary. A real loss in sunlight (a failed string or a damaged panel) still
trips the rule within about 30 s and switches the payload line OFF. While the fault persists, the monitor reports again after
each eclipse exit; repeating the action does no harm. Diagnosis: CTG-009.

### 4.2 AOCS Rules {#42-aocs-rules}

| Rule ID | Condition                      | Detection       | Response                    |
|---------|--------------------------------|----------------|-----------------------------|
| AOCS-01 | att_error > 2 deg (sustained)  | 0x0217 > 2     | Transition to COARSE_SUN    |
| AOCS-02 | Body rate > 2 deg/s            | 0x0204–0206    | Transition to DETUMBLE      |
| AOCS-03 | RW speed > 5500 RPM            | 0x0207–020A    | Initiate desaturation       |
| AOCS-04 | RW temp > 70 C                 | 0x0218–021B    | Reduce RW torque demand     |
| AOCS-05 | Star tracker failure            | Validity flag  | Switch to gyro propagation  |

### 4.3 OBDH Rules {#43-obdh-rules}

| Rule ID | Condition                      | Detection       | Response                    |
|---------|--------------------------------|----------------|-----------------------------|
| OBDH-01 | Watchdog timeout               | HW watchdog    | OBC reset                   |
| OBDH-02 | 3 consecutive WD resets        | reboot_count   | Stay in bootloader (`sw_image` = 0) |
| OBDH-03 | cpu_load > 98%                 | 0x0302 > 98    | Task priority adjustment    |
| OBDH-04 | mmm_used > 95%                 | 0x0303 > 95    | Inhibit payload acquisition |

### 4.4 TCS Rules {#44-tcs-rules}

| Rule ID | Condition                      | Detection       | Response                    |
|---------|--------------------------------|----------------|-----------------------------|
| TCS-01  | bat_temp < 1 C                | 0x0407 < 1     | Battery heater back to thermostat control (`HEATER_AUTO_MODE`) |
| TCS-02  | obc_temp > 70 C (red high)    | 0x0406 > 70    | OBC SAFE (S19 ea 3003, high limit only) |
| TCS-03  | obc_temp < 0 C (red low)      | 0x0406 < 0     | No on-board action: OBC heater thermostat; S12 report to ground |
| TCS-04  | fpa_temp above +17.5 C        | 0x0408 S12 alarm | Power off payload (S19 ea_id 3001) |
| TCS-05  | bat_temp > 42 C               | 0x0407 > 42    | Battery heater OFF; back to thermostat when ≤ 42 C |

TCS-04 fires off the **S12 alarm** on 0x0408, whose band is derived from
`subsystems/tcs.yaml: fpa_envelope` (DECISIONS §3). The documented threshold
used to be a bare `> 12 C`, which is *inside* the normal uncooled resting
state (+11.5 C measured, +12.4 C peak): the rule would have powered off a
payload that was correctly switched off already, on every orbit.

**Temperature rules act on one side only.** An S12 temperature monitor has a
low limit and a high limit. Until November 2026, every S19 rule attached to
such a monitor fired on *either* crossing. As a result, ea 3003 (OBC overtemp
→ OBC SAFE) put the OBC in SAFE on every cold soak, and ea 3002 (battery
overtemp → transmitter OFF) switched the transmitter off when the battery was
cold. The overtemperature rules 3001, 3002, 3003, 4002 and 6002 are now armed
on the high limit only (`limit: high` in `s19_rules.yaml`, section 7.1). The
low crossing is still reported to the ground as TM(12,9) and as an S5 event
(0x9406 for the OBC).

**OBC under-temperature (TCS-03).** The on-board response to a cold OBC is the
OBC heater thermostat, which runs while EPS line 6 (`htr_obc`) is powered. Safe
mode is not used: SAFE does not warm the OBC, and the load shedding that comes
with it removes internal heat. The S12 low-limit report and its S5 event tell
the ground. The ground then checks line 6 and the heater state (manual 03) and
decides. No autonomous mode change is made for a cold OBC.

**Battery heater (TCS-01, TCS-05).** The battery heater is thermostat-
controlled. FDIR acts only when the thermostat is clearly not holding the
band, and it never leaves the heater in a manual state afterwards:

- Below 1 C (TCS-01), FDIR returns the heater to thermostat control
  (`HEATER_AUTO_MODE`). At that temperature the thermostat switches the heater
  on at once.
- Above 42 C (TCS-05), FDIR forces the heater OFF. It hands the heater back to
  the thermostat when the battery is at or below 42 C again (`on_clear` in
  `subsystems/fdir.yaml`).

Until November 2026 the cold response was a manual HEATER ON that nothing ever
undid. After a cold excursion the battery then stayed at +15 to +18 C,
above the +10 C OFF point. FDIR does not re-power heater line
5 (`htr_bat`) if load shedding or the ground has switched it off. That
decision stays with the ground.

### 4.5 TTC Rules {#45-ttc-rules}

| Rule ID | Condition                      | Detection       | Response                    |
|---------|--------------------------------|----------------|-----------------------------|
| TTC-01  | No valid telecommand for > 24 hours | 0x053D ≥ 86400 s (then every further 86400 s) → event 0x0514 | Switch to the other XPDR (S19 ea 4003) |
| TTC-02  | XPDR temp out of range         | 0x0507         | Switch transponder          |
| TTC-03  | Uplink lock dropout (lock lost and regained within 60 s) | event 0x0513 | TX power HIGH, 5 W (S19 ea 4001) |

**What the spacecraft can and cannot see.** Link margin (0x0503), BER (0x050C),
Eb/N0 (0x0519), AGC (0x051A) and downlink RSSI (0x0502) are measured by the
**ground** receiver (`visibility: ground_derived`). The spacecraft cannot
measure them, so no on-board rule can use them. Until November 2026, rules 4001 and
4003 triggered on link margin and BER, and so could never fire. The two TTC
autonomy rules now trigger on what the on-board receiver and OBC really
observe:

- **TTC-01: command-loss timer (ea 4003).** 0x053D `ttc.time_since_last_tc`
  counts the seconds since the OBC last accepted a telecommand, and every S1.1
  acceptance restarts it. When it reaches `cmd_loss_switch_timeout_s` in
  `subsystems/ttc.yaml` (86400 s), event 0x0514 CMD_LOSS_TIMEOUT fires and
  S19 ea 4003 dispatches `TTC_SWITCH_OTHER` (S8 func 99), which selects
  whichever transponder is not selected. If the selected receiver chain has
  gone deaf, the other one may still hear the ground. The timer re-arms: with
  still no accepted telecommand it fires again at 48 h, 72 h, ..., toggling
  each time, so the rule works both ways (a dead REDUNDANT unit is switched
  back to the primary; until 2026-11-02 the action was `TTC_SWITCH_REDUNDANT`,
  which could not). The switch is blind: the spare unit is unpowered (cold
  redundancy), so the OBC cannot check it before selecting it. With both
  units dead the timer keeps toggling every 24 h, which is harmless, and it
  finds a unit that recovers within 24 h. The autonomous switch is not an
  accepted telecommand, so it does not reset the timer. The 24 h value is
  long on purpose: a quiet weekend must not swap transponders. Once the link
  is back, any accepted telecommand stops the next toggle.
  The ground can always command the switch (`TTC_SWITCH_REDUNDANT`, see
  `05_ttc.md` §6.1). Event 0x0511 UPLINK_TIMEOUT is a different signal (no
  uplink lock for 300 s) and fires after every LOS.
- **TTC-03: uplink lock dropout (ea 4001).** On board, a normal LOS and a
  fade look identical at the moment the carrier lock drops. They differ only
  in what happens next: after a fade, lock comes back within seconds; after
  a LOS, it is gone for tens of minutes. Event 0x0513 UPLINK_LOCK_DROPOUT is
  therefore raised when the lock is *regained* within 60 s of being lost.
  S19 ea 4001 then commands `TTC_SET_TX_POWER` level 2 (HIGH, 5 W), which
  gives the ground station about 4 dB more downlink while the pass is
  marginal. The boost **latches**: once the pass is understood, the ground
  restores NOMINAL (`TTC_SET_TX_POWER` level 1). Leaving the PA at 5 W costs
  about 17 W DC on every pass and heats the PA towards the TTC-02/ea 4002
  limit.

The ground side of the same story is on the radio page and the TT&C page:
the RF bridge computes BER and AGC at the ground receiver and alarms them
with limits labelled **ground** (see `05_ttc.md`).

### 4.6 Payload Rules {#46-payload-rules}

| Rule ID | Condition                      | Detection       | Response                    |
|---------|--------------------------------|----------------|-----------------------------|
| PLD-01  | checksum_errors > threshold    | 0x0609         | Alert, inhibit imaging      |
| PLD-02  | Imaging with att_error > 1 deg | 0x0217         | Abort imaging, go STANDBY   |

## 5. Recovery Procedures {#5-recovery-procedures}

### 5.1 Safe Mode Recovery (Level 3 — Ground) {#51-safe-mode-recovery-level-3--ground}

1. Establish ground contact and verify spacecraft telemetry.
2. Review event log and FDIR trigger history.
3. Identify and resolve root cause of the anomaly.
4. Verify all subsystem parameters are within nominal limits.
5. Command `OBC_SET_MODE` (mode=0) to return to NOMINAL.
6. Command `AOCS_SET_MODE` (mode=4) to return to NOMINAL (nadir).
7. Reactivate payload and resume nominal operations.

### 5.2 Transponder Recovery {#52-transponder-recovery}

1. If primary transponder is unresponsive, send `TTC_SWITCH_REDUNDANT`.
2. Wait 30 seconds for transponder warm-up.
3. Verify link acquisition via `link_status` (0x0501).
4. If redundant also fails, wait for next contact attempt (ground-initiated).

### 5.3 AOCS Recovery from DETUMBLE {#53-aocs-recovery-from-detumble}

1. Monitor body rates (0x0204–0x0206) decreasing towards zero.
2. Once rates < 0.5 deg/s sustained for 30 s, AOCS autonomously transitions to COARSE_SUN.
3. Ground commands `AOCS_SET_MODE` (mode=4) to enter NOMINAL (nadir) when ready.

## 6. PUS Service 12 — Onboard Monitoring {#6-pus-service-12--onboard-monitoring}

Service 12 implements the parameter monitoring framework used by the FDIR system. All
monitoring definitions are evaluated on every on-board processing cycle
(nominally 1 Hz), providing continuous limit-checking coverage.

### 6.1 Monitoring Enforcement {#61-monitoring-enforcement}

Each monitoring definition specifies:

| Field               | Description                                        |
|---------------------|----------------------------------------------------|
| Parameter ID        | The telemetry parameter to monitor                 |
| Check Type          | Limit check, expected value, or delta check        |
| Low Limit           | Lower threshold for limit check                    |
| High Limit          | Upper threshold for limit check                    |
| Event ID            | S5 event generated on violation                    |
| Repetition Count    | Number of consecutive violations before triggering |
| Validity condition  | Optional `validity: {param_id, mask, value}`: check only while `(param & mask) == value` |
| Enabled             | Whether this monitor is currently active           |

Both the repetition count (`repetition`, default 1) and the validity
condition follow PUS-C. While the validity condition is false, the definition
is *unchecked*: it is neither violated nor nominal. The solar-array yield
monitors (EPS-05) use both fields. Neither field is carried in the TM(12,13)
record. The transition report states which limit was crossed, low or high.

When a monitoring check fails, the OBC generates a PUS S5 event packet with the
corresponding Event ID. This event is:

1. Stored in the event buffer for later downlink.
2. Delivered to the S19 event-action service for automated response.
3. Made available to the MCS alarm journal for operator awareness.

### 6.2 Monitoring Commands {#62-monitoring-commands}

| Command           | Mnemonic          | Subtype | Description                                                |
|-------------------|-------------------|---------|------------------------------------------------------------|
| Enable service    | `MON_ENABLE`      | S12.1   | Enable on-board limit checking globally                     |
| Disable service   | `MON_DISABLE`     | S12.2   | Disable on-board limit checking globally                    |
| Enable one        | `MON_ENABLE_DEF`  | S12.3   | Enable ONE definition, addressed by `mon_id`                |
| Disable one       | `MON_DISABLE_DEF` | S12.4   | Disable ONE definition, addressed by `mon_id`               |
| Add definition    | `MON_ADD_DEF`     | S12.6   | `mon_id`, `param_id`, `check_type`, low and high limits     |
| Delete definition | `MON_DEL_DEF`     | S12.7   | Delete ONE definition, addressed by `mon_id`                |
| Report defs       | `MON_REPORT_DEFS` | S12.12  | Report the whole on-board definition table → **TM(12,13)**  |

There is no S12.15/S12.16: 12.1 and 12.2 are the whole-service switches and
12.3/12.4 are the per-definition ones. `mon_id` addresses the *definition*, not
the parameter — a parameter may carry several monitors (a WARNING tier and an
ALARM tier), which is why the id is separate.

**TC(12,12) → TM(12,13)** is how the ground reads back what the spacecraft
actually holds, rather than what the ground database believes it uploaded. It
is what the MCS FDIR panel's "Refresh from Spacecraft" button sends. The report
is `count(u16)` followed by `count` fixed 14-octet records:

| Field | Type | Meaning |
|---|---|---|
| `mon_id`     | uint16  | Definition id |
| `param_id`   | uint16  | Monitored parameter |
| `check_type` | uint8   | 0 = absolute (value in band), 1 = delta (change since the last check) |
| `enabled`    | uint8   | Per-definition enable state (S12.3 / S12.4) |
| `low_limit`  | float32 | Low limit |
| `high_limit` | float32 | High limit |

Limit *transitions* are reported separately, as TM(12,9) (limit entered) and
TM(12,10) (returned to nominal).

## 7. PUS Service 19 — Event-Action Triggering {#7-pus-service-19--event-action-triggering}

Service 19 links S5 events (generated by S12 monitoring or other sources) to automated
actions, implementing the autonomous FDIR response chain.

### 7.1 Event-Action Mechanism {#71-event-action-mechanism}

When an S5 event is raised:

1. The OBC checks if there is an active S19 event-action definition for that event ID.
2. If found and enabled, the associated action (a stored telecommand) is executed.
3. The action execution is logged in the event buffer.
4. The action can itself trigger further events, allowing cascaded responses.

A rule attached to an S12 monitor (trigger kind `param`) can be limited to one
side of the band. With `limit: high` it fires only on an upper-limit crossing,
with `limit: low` only on a lower-limit crossing, and with `any` (the default)
on both. The overtemperature rules use `high`, the solar-array yield rules use
`low`, and symmetric bands such as wheel overspeed keep `any`. A rule added
from the ground with TC(19,1) always uses `any`.

### 7.2 Event-Action Commands {#72-event-action-commands}

| Command                | Subtype | Description                              |
|------------------------|---------|------------------------------------------|
| Enable event-action    | S19.1   | Enable a specific event-action link      |
| Disable event-action   | S19.2   | Disable a specific event-action link     |
| Report event-actions   | S19.8   | Report all active event-action definitions |

### 7.3 Typical FDIR Chain Example {#73-typical-fdir-chain-example}

```
S12 monitor: bat_soc < 25%
  --> S5 event: EPS_LOW_SOC_WARNING
    --> S19 action: OBC_SET_MODE(SAFE)
      --> Safe mode sequence executes
        --> S5 event: SAFE_MODE_ENTERED
```

## 8. Progressive Load Shed Thresholds {#8-progressive-load-shed-thresholds}

The EPS FDIR implements a tiered load shedding strategy based on battery state of charge.
Each threshold triggers progressively more aggressive power reduction:

| SoC Threshold | FDIR Level | Actions                                               |
|---------------|------------|-------------------------------------------------------|
| < 50%         | Level 1    | Inhibit payload imaging; reduce HK rate to 0.5 Hz     |
| < 35%         | Level 2    | Command AOCS to COARSE_SUN; shed non-essential loads   |
| < 25%         | Level 3    | Safe mode entry; only essential loads remain           |
| < 15%         | Level 4    | Emergency mode; OBC + TTC only; all other loads off    |

Each level includes all actions from previous levels. Recovery from load shedding is a
ground-commanded activity — the FDIR does not automatically restore loads when SoC
recovers.

## 9. Contingency Response Matrix {#9-contingency-response-matrix}

The following matrix cross-references contingency scenarios with the procedures used
for detection and recovery:

| Scenario                    | Detection Method              | Procedure File                        |
|-----------------------------|-------------------------------|---------------------------------------|
| TTC no telemetry            | No TM at expected AOS         | `procedures/contingency/no_telemetry_at_pass.md` |
| Ground station antenna fail | Ground equipment monitoring    | `procedures/contingency/gs_antenna_failure.md` |
| OBC stuck in bootloader     | Beacon SID 11 with `sw_image` = 0 | `procedures/contingency/obc_bootloader_recovery.md` |
| Bus isolation required      | Multiple subsystem anomalies  | `procedures/contingency/bus_failure_isolation.md` |
| Progressive load shed       | bat_soc crossing thresholds   | `procedures/contingency/progressive_load_shed.md` |
| Solar panel loss             | Panel current = 0 sustained  | `procedures/contingency/solar_panel_loss_response.md` |
| AOCS sensor cascade failure | Multiple sensor invalids      | `procedures/contingency/aocs_sensor_loss_recovery.md` |
| AOCS actuator stuck         | Wheel speed constant despite command | `procedures/contingency/aocs_actuator_stuck_recovery.md` |

Each contingency procedure includes:
- **Entry criteria**: How to recognise the scenario.
- **Immediate actions**: Time-critical steps to stabilise the spacecraft.
- **Investigation steps**: How to identify root cause.
- **Recovery actions**: Steps to restore nominal operations.
- **GO/NO-GO checkpoints**: Decision points requiring Flight Director authorisation.

## 10. FDIR Configuration {#10-fdir-configuration}

FDIR thresholds and enable/disable flags are configurable via `SET_PARAM` commands.
Each rule can be individually disabled for testing or commissioning purposes. Disabling
FDIR rules requires explicit ground authorisation and should be time-limited.

| Configuration Parameter      | Default | Modifiable |
|------------------------------|---------|------------|
| Safe mode SoC threshold      | 15%     | Yes        |
| Safe mode voltage threshold  | 26.5 V  | Yes        |
| Attitude error red limit     | 2 deg   | Yes        |
| Body rate red limit          | 2 deg/s | Yes        |
| Watchdog timeout             | 10 s    | No         |
| Command-loss timeout (TTC-01) | 24 h   | Yes        |
| Load shed level 1 threshold  | 50%     | Yes        |
| Load shed level 2 threshold  | 35%     | Yes        |
| Load shed level 3 threshold  | 25%     | Yes        |
| Load shed level 4 threshold  | 15%     | Yes        |

### 10.1 Phase Gating of FDIR Rules {#101-phase-gating-of-fdir-rules}

Two mechanisms are gated on the mission phase (`eps.spacecraft_phase`, 0x0129):

* the **advanced fault-propagation model** (`fdir/fault_propagation.yaml`) is
  armed only at phase 6 (NOMINAL), as a whole;
* individual **legacy threshold rules** (`subsystems/fdir.yaml`) may carry an
  optional `min_phase:` field. Without it — the default — a rule is armed in
  every phase.

`min_phase` exists for rules whose trigger condition *is* the expected state of
an uncommissioned spacecraft. Two rules carry it, both at `min_phase: 6`:

| Rule | Why it is gated |
|---|---|
| `aocs.wheels_enabled < 2` | The bootloader powers up with all four reaction wheels disabled and they stay disabled until COM-004 commands `AOCS_ENABLE_WHEEL`. Ungated, this level-2 rule latched on the first tick of every run, pinned the spacecraft mode to SAFE and demoted `aocs.mode` out of NOMINAL. |
| `aocs.att_error > 5 deg` (420 s persistence) | A large attitude error is expected while the spacecraft detumbles in LEOP and is slewed around during AOCS checkout (COM-004/005/013). Pointing performance is a requirement only once the spacecraft is declared operational. |

**Everything else stays armed in every phase, deliberately.** Battery SoC and
bus voltage, battery/OBC/wheel/PA temperature, reboot count and CAN bus status
are hardware protection: LEOP is precisely when a mishandled spacecraft
flattens its battery, and a blanket `phase >= 6` on the whole rule set would
switch those protections off for the entire early mission.

A rule below its `min_phase` is **disarmed, not suppressed**: any latch it
holds is dropped and its persistence accumulator is reset, so falling back
below the threshold — an OBC reboot to the bootloader, for instance — cannot
leave a stale contingency behind.

### 10.2 One Spacecraft Mode {#102-one-spacecraft-mode}

`sat.mode` (0x0001) is the telemetered spacecraft mode word — the same value, on
the same scale, that the MCS console header shows:

| Value | Mode | Meaning |
|---|---|---|
| 0 | SAFE      | An FDIR safe-level contingency is latched, **or** the phase is below 6 |
| 1 | NOMINAL   | Commissioned, no contingency, not imaging |
| 2 | SCIENCE   | Commissioned, no contingency, payload actively imaging |
| 3 | EMERGENCY | An FDIR emergency-level contingency is latched |

It previously had a second, independent derivation that read only the FDIR
latches and ignored the phase gate, so a `GET_PARAM(0x0001)` reported NOMINAL
while the console header reported SAFE throughout LEOP. There is now one
derivation (`Engine._update_sc_mode`) and 0x0001 is written from it.

## 11. Operational Notes {#11-operational-notes}

1. After every safe mode entry, a detailed anomaly investigation must be completed before
   returning to nominal operations.
2. FDIR rules should not be disabled during nominal operations. Exceptions require formal
   approval and a risk assessment.
3. The FDIR event log stores the last 100 events in non-volatile memory and survives
   OBC reboots. Events are stored in a linear buffer; housekeeping uses a circular buffer
   (store-1 policy).
4. During commissioning, FDIR rules may be temporarily widened (e.g., attitude error
   limit increased to 5 deg) to allow for calibration activities.
5. S12 monitoring is evaluated every tick. A parameter that transiently violates a limit
   for less than the configured repetition count will not trigger a response.
6. S19 event-action links can be disabled individually for testing. This allows FDIR
   event generation (for visibility) without triggering automatic corrective action.
7. The MCS alarm journal displays all S5 events and S12 violations with severity badges,
   acknowledge/clear functionality, and per-subsystem filtering.

---

*End of Document — EOSAT1-UM-FDIR-009*
