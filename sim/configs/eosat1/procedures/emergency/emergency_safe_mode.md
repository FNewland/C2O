# EMG-001: Emergency Safe Mode
**Subsystem:** OBDH / All Subsystems
**Phase:** EMERGENCY
**Revision:** 1.1 --- 2026-11-02 (Franz's rulings P1/P3): check what on-board
FDIR has already shed BEFORE shedding from the ground, and power a unit's EPS
line before any heater or mode command to it. The old card commanded loads
whose lines FDIR had already opened (refused S1.8 "power line … is OFF") and
switched heaters on with their lines dark.
**Approved:** Flight Operations Director

## Purpose
Master procedure for EOSAT-1 emergency safe mode entry when multiple concurrent anomalies are
detected or the spacecraft has autonomously transitioned to EMERGENCY mode. This procedure
coordinates OBC emergency mode commanding, verifies automatic load shedding, confirms safe
sun-pointing attitude, establishes communication, and provides an orbit-by-orbit recovery
timeline back to nominal operations.

## Prerequisites
- [ ] Multiple anomaly indicators present OR `obdh.mode` (0x0300) = EMERGENCY (2) confirmed
- [ ] Flight Director has declared spacecraft emergency
- [ ] Emergency Response Team fully staffed (Power, AOCS, TT&C, Thermal, Payload engineers)
- [ ] All ground stations alerted for priority tracking
- [ ] Anomaly log initiated with timeline of events

## Trigger Conditions (Any Two or More)
- `eps.bat_soc` (0x0101) < 15% --- low power
- `aocs.att_error` (0x0217) > 30 deg --- attitude anomaly
- Any body rate > 2 deg/s --- tumbling
- `obdh.reboot_count` (0x030A) incremented by >= 2 in 1 hour --- OBC instability
- `tcs.temp_battery` (0x0407) outside range -10 degC to +45 degC --- thermal violation
- `ttc.link_status` (0x0501) != 2 (not LOCKED) for > 1 pass --- communication degraded
- `obdh.mode` (0x0300) = EMERGENCY (2) --- autonomous transition detected

## Procedure Steps

### Step 1 --- Command Emergency Mode (If Not Already Autonomous)
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) --- EMERGENCY mode.
**Verify:** `obdh.mode` (0x0300) = EMERGENCY (2) within 5s.
**Effect:** Onboard software executes automatic load shedding sequence, reduces telemetry rate,
disables all scheduled operations, and enables survival-only power distribution.
**GO/NO-GO:** OBC emergency mode confirmed. If OBC not responding, proceed with manual commanding at Step 2.

### Step 2 --- Verify Automatic Load Shedding (check the spacecraft first)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- full EPS housekeeping.
**Verify:** `eps.load_shed_stage` (0x0134) --- record what the on-board shedder has done (events LOAD_SHED_STAGE_1..3, 0x0106-0x0108)
**Verify:** `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117) --- record each: 0 = already shed on board
**Note:** A line that on-board FDIR has opened cannot be shed again --- its unit's
commands are refused S1.8 "power line … is OFF" and its housekeeping stops, so
its mode parameter (e.g. `payload.mode`) freezes at its last value. Judge a shed
by the LINE state. Shed from the ground only what is still powered.
**Verify:** `eps.power_cons` (0x0106) < 50W.
**BRANCH:** `eps.pl_payload == 1` -> GO `STEP-2-PLD` | NO-GO `STEP-2-HTR` (timeout 10 s)
**Note:** GO --- the payload line is still ON: shed the payload from the ground.
NO-GO --- FDIR has already opened it: nothing to send.

**LABEL:** `STEP-2-PLD`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) --- payload OFF.
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Payload housekeeping
**Verify:** `payload.mode` (0x0600) = 0 (OFF) within 10s.

**LABEL:** `STEP-2-HTR`
**TC:** `HEATER_OBC(on=0)` (Service 8, Subtype 1, func_id 41) --- OBC heater OFF (if needed).
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1, func_id 42) --- thruster heater OFF.
**Verify:** `eps.power_cons` (0x0106) < 50W within 15s of manual commanding.
**GO/NO-GO:** Total spacecraft power consumption confirmed below 50W.

### Step 3 --- Verify AOCS Safe-Pointing
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- AOCS housekeeping.
**Check:** `aocs.mode` (0x020F) --- should be COARSE_SUN (3) or DETUMBLE (2).
**Note:** Do NOT command COARSE_SUN. The AOCS hands itself from DETUMBLE to
COARSE_SUN automatically once the body rates have stayed below 0.5 deg/s for
30 s (the same handover LEOP-005 observes). Commanding it is unnecessary, and a
COARSE_SUN entered above the rate threshold will not hold.
**BRANCH:** `aocs.mode == 0` -> GO `STEP-3-DETUMBLE` | NO-GO `STEP-3-WAIT` (timeout 10 s)
**Note:** GO --- the AOCS is OFF: command DETUMBLE first. NO-GO --- the AOCS is
already in a mode: command nothing and wait for the sun hold.

**LABEL:** `STEP-3-DETUMBLE`
**Note:** An AOCS that reads OFF has usually lost its `aocs_wheels` line to an
on-board shed (the AOCS collapses to OFF when the line opens); DETUMBLE is then
refused "EPS aocs_wheels line (0x0117) is off". Re-power the line first ---
`EPS_POWER_ON` on a line that is already ON is a no-op.
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) --- the `aocs_wheels` line (AOCS suite)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- EPS housekeeping (line states)
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 within 5s
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) --- DETUMBLE (AOCS was OFF).

**LABEL:** `STEP-3-WAIT`
**BRANCH:** `aocs.mode == 3` -> GO `STEP-4` | NO-GO `STEP-3-EMG-005` (timeout 1800 s)
**Note:** GO --- COARSE_SUN, either already held or reached by the automatic
handover: go to Step 4, which verifies the sun pointing. NO-GO --- no COARSE_SUN
after 30 min: the spacecraft is tumbling or the detumble is not converging.

**LABEL:** `STEP-3-EMG-005`
**Note:** Execute EMG-005 (Loss of Attitude) now. Resume this card at Step 4 only
when EMG-005 has left the AOCS in COARSE_SUN.
**GO/NO-GO:** EMG-005 complete and AOCS in COARSE_SUN --- resume at Step 4 -> GO `STEP-4` | NO-GO `STEP-END`

### Step 4 --- Verify Sun Acquisition and Power State
**LABEL:** `STEP-4`
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg (sun-pointing achieved).
**Verify:** `eps.sa_a_current` (0x0103) > 0.5A --- solar array A illuminated.
**Verify:** `eps.sa_b_current` (0x0104) > 0.5A --- solar array B illuminated.
**Verify:** `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106) --- power-positive.
**Verify:** `eps.bat_soc` (0x0101) --- record value and start trend tracking.
**TC:** `EPS_POWER_ON(line_index=5)` (Service 8, Subtype 1, func_id 19) --- the battery heater line first: a heater with its line dark heats nothing and its ON command is refused
**Verify:** `eps.pl_htr_bat` (0x0115) = 1 within 5s
**TC:** `HEATER_AUTO_MODE(circuit=0)` (Service 8, Subtype 1, func_id 45) --- ensure battery thermostat active (ON below +5 degC, OFF above +10 degC).
**Note:** If the battery is already colder than its thermostat band and not
recovering, force the heater: `HEATER_BATTERY(on=1)` (func_id 40); return it to
`HEATER_AUTO_MODE(circuit=0)` once `tcs.temp_battery` (0x0407) is back above +10 degC.
**GO/NO-GO:** Power-positive state confirmed. If not, execute EMG-002.

### Step 5 --- Establish Stable Communication
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED).
**Verify:** TT&C page (ground): `ttc.rssi` (0x0502) > -128 dBm.
**Verify:** `ttc.mode` (0x0500) = NOMINAL or SAFE.
**Action:** If link marginal, schedule subsequent passes at high-elevation (> 20 deg) ground stations only.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- TT&C subsystem housekeeping.
**GO/NO-GO:** Two-way communication stable. If unstable, reference EMG-004.

### Step 6 --- Full Housekeeping Assessment
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) --- EPS HK.
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- AOCS HK.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- OBDH HK.
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- TCS HK.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- TT&C HK.
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- Payload HK.
**Action:** Engineering team reviews all parameters against nominal ranges.
**Record:** `obdh.reboot_count` (0x030A) --- note any unexpected increments.
**Record:** All temperatures: `tcs.temp_obc` (0x0406), `tcs.temp_battery` (0x0407).
**Record:** `eps.bat_voltage` (0x0100), `eps.bus_voltage` (0x0105) --- full power state.
**GO/NO-GO:** Anomaly Review Board convenes to assess data and approve recovery plan.

### Step 7 --- Stabilisation Hold (Minimum 3 Orbits)
**LABEL:** `STEP-7`
**Duration:** Maintain emergency safe mode for minimum 3 orbits (~4.75 hours).
**Monitor:** All critical parameters on every ground station pass.
**Confirm:** No new anomalies, no additional OBC reboots, temperatures stable, power trending positive.
**Verify:** `eps.bat_soc` (0x0101) > 25% by end of stabilisation period.
**Action:** Engineering team completes root cause analysis of triggering anomalies.
**GO/NO-GO:** Flight Director approves transition to staged recovery.

## Orbit-by-Orbit Recovery Timeline

### Recovery Orbit R+1 --- Restore Thermal Control (SoC > 30% Required)
**TC:** `EPS_POWER_ON(line_index=6)` (Service 8, Subtype 1, func_id 19) --- the OBC heater line first (no-op if already ON)
**Verify:** `eps.pl_htr_obc` (0x0116) = 1 within 5s
**TC:** `HEATER_AUTO_MODE(circuit=1)` (Service 8, Subtype 1, func_id 45) --- restore the OBC heater to its thermostat (Step 2 switched it OFF manually).
**Note:** If the OBC is colder than +5 degC and not recovering, force it ON with
`HEATER_OBC(on=1)` (func_id 41) and return it to AUTO once warm.
**Verify:** `tcs.temp_obc` (0x0406) trending toward nominal range (-10 degC to +40 degC).
**Verify:** `eps.power_cons` (0x0106) increase < 10W. Spacecraft remains power-positive.
**GO/NO-GO:** Thermal subsystem nominal, power budget accommodates added load; no new anomaly -> GO `STEP-R2` | NO-GO `STEP-7` (max 2)

### Recovery Orbit R+2 --- Restore Full AOCS (SoC > 40% Required)
**LABEL:** `STEP-R2`
**TC:** `OBC_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 50) --- OBC SAFE mode (from EMERGENCY).
**Verify:** `obdh.mode` (0x0300) = SAFE (1) within 5s.
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) --- the `aocs_wheels` line before the mode command (no-op if Step 3 already re-powered it)
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 within 5s
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) --- NOMINAL mode.
**Verify:** `aocs.mode` (0x020F) = NOMINAL (4) within 5s.
**Verify:** `aocs.att_error` (0x0217) < 1.0 deg within 20 minutes.
**Verify:** `aocs.rw1_speed` (0x0207) through `aocs.rw4_speed` (0x020A) all within limits.
**GO/NO-GO:** Full attitude control restored, all 4 wheels operational; no new anomaly -> GO `STEP-R3` | NO-GO `STEP-7` (max 2)

### Recovery Orbit R+3 --- Restore Thruster Heater and Full Thermal (SoC > 50% Required)
**LABEL:** `STEP-R3`
**Note:** The catalyst-bed (thruster) heater is OFF in nominal operations and
its `prop` line (8) with it: it is powered only for manoeuvre preheat (NOM-013).
Send the two commands below only if a manoeuvre is planned; otherwise there is
nothing to restore and this orbit verifies thermal state only.
**TC:** `EPS_POWER_ON(line_index=8)` (Service 8, Subtype 1, func_id 19) --- the `prop` line first; HEATER_THRUSTER is refused while it is dark
**Verify:** `eps.pl_prop` (0x014A) = 1 within 5s
**TC:** `HEATER_THRUSTER(on=1)` (Service 8, Subtype 1, func_id 42) --- restore thruster heater.
**Verify:** `eps.power_cons` (0x0106) within nominal budget (< 90W).
**Verify:** All temperatures within nominal ranges.
**GO/NO-GO:** Full thermal control restored, power margin adequate; no new anomaly -> GO `STEP-R4` | NO-GO `STEP-7` (max 2)

### Recovery Orbit R+4 --- Restore OBC Nominal Mode (SoC > 55% Required)
**LABEL:** `STEP-R4`
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50) --- OBC NOMINAL mode.
**Verify:** `obdh.mode` (0x0300) = NOMINAL (0) within 5s.
**Verify:** Onboard scheduling resumed, housekeeping at nominal rate.
**Verify:** No anomalous reboot counter increments: `obdh.reboot_count` (0x030A) stable.
**GO/NO-GO:** OBC nominal operations confirmed; no new anomaly -> GO `STEP-R5` | NO-GO `STEP-7` (max 2)

### Recovery Orbit R+5 --- Restore Payload (SoC > 60% Required)
**LABEL:** `STEP-R5`
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) --- the `payload` line first: an on-board shed opened it, and the mode command is refused S1.8 while it is dark
**Verify:** `eps.pl_payload` (0x0113) = 1 within 5s
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) --- payload STANDBY.
**Verify:** `payload.mode` (0x0600) = STANDBY (1) within 10s.
**Verify:** `eps.power_cons` (0x0106) within full operational budget (< 110W).
**Verify:** Spacecraft remains power-positive across full orbit including eclipse.
**GO/NO-GO:** Full nominal operations restored; no new anomaly. Close emergency and resume mission timeline. -> GO `STEP-END` | NO-GO `STEP-7` (max 2)
**LABEL:** `STEP-END`

## Recovery Timeline Summary
| Phase | Orbit | SoC Gate | Duration from Emergency | Key Action |
|---|---|---|---|---|
| Emergency hold | R+0 to R+3 | -- | 0 to 4.75h | Stabilise, assess, plan |
| Thermal restore | R+1 recovery | > 30% | ~6.3h | OBC heater ON |
| AOCS restore | R+2 recovery | > 40% | ~7.9h | Nadir pointing |
| Full thermal | R+3 recovery | > 50% | ~9.5h | Thruster heater ON (only if a manoeuvre is planned) |
| OBC nominal | R+4 recovery | > 55% | ~11.1h | Resume scheduling |
| Payload standby | R+5 recovery | > 60% | ~12.6h | Mission resumed |

## Off-Nominal Handling
- If OBC does not accept mode commands: request an OBC health report with `OBC_DIAGNOSTIC` (func_id 61) and, if the Flight Director authorises, reset with `OBC_REBOOT` (func_id 52), then re-command. If persistent, spacecraft remains in autonomous emergency mode until next OBC reboot cycle.
- If multiple wheels failed during anomaly: remain in COARSE_SUN indefinitely. Nadir pointing requires minimum 3 wheels. Plan reduced-capability operations.
- If SoC does not reach 30% within 10 orbits: possible solar array degradation. Reassess power budget for long-term reduced operations. Reference EMG-002.
- If new anomaly occurs during recovery: halt recovery, return to Step 7 stabilisation hold, re-assess before continuing. This is the NO-GO arm of each recovery-orbit gate and it is a bounded loop (max 2): if the same gate fails a third time, stop the staged recovery, hold emergency safe mode and convene the Anomaly Review Board.
- If `obdh.reboot_count` (0x030A) continues incrementing: suspect OBC hardware fault. Maintain emergency mode, reduce commanding to minimum, plan OBC memory patch or cold redundancy switch if available.

## Post-Conditions
- [ ] `obdh.mode` (0x0300) = NOMINAL (0)
- [ ] `aocs.mode` (0x020F) = NOMINAL (4) with `aocs.att_error` (0x0217) < 1.0 deg
- [ ] `eps.bat_soc` (0x0101) > 60% and stable
- [ ] `eps.bus_voltage` (0x0105) > 28.0V
- [ ] All heaters operational, temperatures within nominal ranges
- [ ] `payload.mode` (0x0600) = STANDBY (1) or higher
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED) on scheduled passes
- [ ] All anomaly root causes identified or formal investigation open
- [ ] Flight Director has formally closed the emergency declaration
- [ ] Lessons learned documented and procedure updates initiated if required

## Recovery Path — Re-Powering Shed Loads
After this procedure has stabilised the bus and the root cause is understood, **any subsystems whose power lines were de-energised during load shed must be brought back up in the controlled order defined by LEOP-007 (Sequential Power-On)**. Do **not** simply re-enable lines ad-hoc: LEOP-007 enforces the correct subsystem→line→mode sequencing, the inrush spacing, the thermal pre-conditioning of the OBC/battery heaters, and the AOCS/payload set_mode exemptions to the two-stage TC power gate. Cross-reference: `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
