# CTG-003: TTC Link Loss Recovery
**Subsystem:** TT&C
**Phase:** CONTINGENCY
**Revision:** 1.1 --- 2026-11-02 (Franz's ruling S4): with both transponders
failed the link is really cut (no TC received, no TM, beacon included), so the
card now says what the blind steps can and cannot reach, and Step 6 names the
real on-board autonomy (FDIR TTC-01 command-loss timer, 24 h).
**Approved:** Flight Operations Director

## Purpose
Recover communications with the EOSAT-1 spacecraft when the TT&C link is lost during
a predicted acquisition-of-signal (AOS) window. Link loss is confirmed when
`ttc.link_status` = 0 persists for more than 30 seconds after predicted AOS, or when an
established link drops unexpectedly mid-pass. This procedure attempts transponder switching
and link restoration before escalating to emergency autonomous operations.

## Prerequisites
- [ ] Ground station antenna is confirmed tracking the spacecraft with valid pointing
- [ ] Orbit prediction is current (propagated within last 6 hours) and AOS/LOS times are valid
- [ ] Ground station RF chain has been verified nominal (uplink power, frequency, polarisation)
- [ ] At least 5 minutes of pass time remaining for recovery attempt
- [ ] Emergency procedure EMG-004 is available for escalation

## Procedure Steps

### Step 1 — Confirm Link Loss Is Not a Ground Issue
**Action:** Verify ground station status — antenna tracking, uplink transmitter power, receiver lock
**Action:** Confirm Doppler pre-compensation is applied correctly for current pass
**Action:** Check for local RFI or weather-related attenuation at the ground station
**GO/NO-GO:** If ground station anomaly identified, resolve locally. If ground confirmed nominal, proceed with spacecraft-side recovery.

### Step 2 — Attempt Re-Acquisition on Primary Transponder
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — blind command, no telemetry expected
**Action:** Wait 30s for transponder to process and attempt downlink re-acquisition
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) within 30s
**Verify:** TT&C page (ground): `ttc.rssi` (0x0502) > -126 dBm if link restores
**GO/NO-GO:** If link restores, proceed to Step 5 for health check. If no response, proceed to Step 3.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-5` | NO-GO `STEP-3` (timeout 30 s)

### Step 3 — Switch to Redundant Transponder
**LABEL:** `STEP-3`
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1) — blind command
**Note:** The transponders are cold-redundant: the switch is received only by
the SELECTED unit. If the primary is dead it hears nothing and this command is
lost --- the switch then happens only on board, when the command-loss timer
expires (Step 6). It is still worth sending: if the loss is on the transmit side
(PA off, `ttc_tx` line shed) the receiver is alive and acts on it.
**Action:** Wait 45s for redundant transponder power-up and frequency lock
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) within 45s
**Verify:** `ttc.mode` (0x0500) indicates redundant unit active
**GO/NO-GO:** If link restores on redundant, proceed to Step 5. If no response, proceed to Step 4.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-5` | NO-GO `STEP-4` (timeout 45 s)

### Step 4 — Second Attempt: Retry Primary Transponder
**LABEL:** `STEP-4`
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1) — blind command
**Action:** Wait 45s for primary transponder re-initialisation
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) within 45s
**GO/NO-GO:** If link restores, proceed to Step 5. If still no link after both transponders attempted, proceed to Step 6 (Escalation).
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-5` | NO-GO `STEP-6` (timeout 45 s)

### Step 5 — Verify Link Quality and Subsystem Health
**LABEL:** `STEP-5`
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27)
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Verify:** TT&C page (ground): `ttc.rssi` (0x0502) > -126 dBm (nominal signal strength)
**Verify:** TT&C page (ground): `ttc.link_margin` (0x0503) > 3.0 dB
**Verify:** `ttc.mode` (0x0500) — record which transponder is active
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Platform/OBDH housekeeping
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TT&C housekeeping
**Verify:** `eps.bus_voltage` (0x0105) > 27.0V — confirm no EPS anomaly caused the link loss
**Verify:** `obdh.mode` (0x0300) — confirm OBC did not enter safe/emergency mode
**GO/NO-GO:** Link margin > 3 dB and all subsystems nominal — recovery complete -> GO `STEP-END` | NO-GO `STEP-6`

### Step 6 — Escalation: No Link Recovery
**LABEL:** `STEP-6`
**Action:** Log the failed recovery attempt with timestamps of all blind commands sent
**Action:** Notify Mission Director and Flight Dynamics of sustained link loss
**Action:** Schedule next available ground station pass for re-acquisition attempt
**Action:** Record the time of the last ACCEPTED telecommand (last S1.1). The on-board command-loss timer (FDIR TTC-01, `ttc.time_since_last_tc` 0x053D) switches the spacecraft to the redundant transponder 24 h after it (event CMD_LOSS_TIMEOUT 0x0514, S19 ea 4003): schedule the first passes after that time. Blind commands that are not received do not reset it
**GO/NO-GO:** If no link after two consecutive passes, escalate to EMG-004 (Loss of Communication)

## Off-Nominal Handling
- If link restores but RSSI < -95 dBm or margin < 1.5 dB: Step the TM rate ladder down to LOW (16 kbps) via `TTC_SET_DATA_RATE(rate=0)` (func_id 65) to improve margin. LOW is the routine operations rung — the link keeps full housekeeping, it just cannot dump
- If OBC is found in SAFE mode after link restoration: Execute CTG-010 (OBDH Watchdog Recovery) before resuming nominal operations
- If redundant transponder also fails: no telecommand can be received and no telemetry is transmitted, beacon included; the TTC-01 switch is refused. Nothing from the ground can recover this: escalate to EMG-004 and keep listening for a transponder recovery (in the simulator, the instructor clearing a transponder failure)
- If link is intermittent (toggling): Suspect antenna deployment anomaly or attitude issue — request AOCS telemetry and check `aocs.att_error` (0x0217)

## Post-Conditions
**LABEL:** `STEP-END`
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] `ttc.link_margin` (0x0503) > 3.0 dB
- [ ] Active transponder identified and logged
- [ ] Root cause documented (ground issue, transponder failure, attitude, or EPS)
- [ ] If unrecovered: EMG-004 escalation initiated with next pass plan
