# CTG-001: Under-Voltage Load Shed

**Category:** Contingency
**Position Lead:** Power & Thermal (EPS/TCS)
**Cross-Position:** Flight Director, all positions
**Difficulty:** Advanced
**Revision:** 1.1 --- 2026-11-02 (Franz's ruling P3: "if the spacecraft does not
shed, the ground should --- but check the spacecraft first"). Each shed level now
reads the line state first and sheds from the ground only what on-board FDIR has
not already switched off; restoration re-powers each line before its mode command.

## Objective
Respond to an undervoltage condition on the main power bus by completing, from the
ground, the load shedding the spacecraft has not already done, in a controlled
priority order. The EPS sheds on its own below 25.0 V (payload → FPA cooler →
`ttc_tx` → AOCS wheels → prop, one line per second, events LOAD_SHED_STAGE_1..3
0x0106-0x0108), and EPS safe/emergency modes and the S19 SoC rules open lines too:
by the time this card is flown some lines may already be off. Loads are shed starting with the lowest
priority (payload) and progressing through the FPA cooler, TX transmitter, and reaction
wheels to arrest bus voltage decline and protect critical spacecraft functions. Recovery
is monitored until battery state-of-charge and bus voltage return to safe levels.

## Prerequisites
- [ ] Undervoltage flag detected — `eps.uv_flag` (0x010E) = 1 or bus voltage observed < 27.0 V
- [ ] TT&C link active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Flight Director notified and authorizes manual load shedding
- [ ] Current orbit prediction available (eclipse entry/exit times)

## Required Telemetry
| Parameter | ID | Expected Value |
|---|---|---|
| eps.uv_flag | 0x010E | 1 (undervoltage detected) |
| eps.bus_voltage | 0x0105 | Monitoring — expected < 27.0 V at detection |
| eps.bat_soc | 0x0101 | Monitoring — record trend |
| eps.bat_voltage | 0x0100 | Monitoring — record value |
| eps.bat_current | 0x0109 | Negative (discharging) |
| eps.power_cons | 0x0106 | Monitoring — record before/after each shed |
| eps.power_gen | 0x0107 | Record — may be 0 if in eclipse |
| eps.eclipse_flag | 0x0108 | Current sun/eclipse state |
| payload.mode | 0x0600 | Current payload mode |
| tcs.cooler_fpa | 0x040C | Current cooler state |
| ttc.pa_on | 0x0516 | Current PA state |
| aocs.mode | 0x020F | Current AOCS mode |
| eps.load_shed_stage | 0x0134 | On-board shed stage (0 = nothing shed on board) |
| eps.pl_payload | 0x0113 | Payload line (0 = already shed) |
| eps.pl_fpa_cooler | 0x0114 | FPA cooler line (0 = already shed) |
| eps.pl_ttc_tx | 0x0112 | TX line (0 = already shed) |
| eps.pl_aocs_wheels | 0x0117 | AOCS wheels line (0 = already shed) |

## Required Commands
| Command | Service | Subtype | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | — | Request one-shot HK report |
| PAYLOAD_SET_MODE | 8 | 1 | 26 | Set payload mode to OFF |
| FPA_COOLER | 8 | 1 | 43 | Disable FPA cooler |
| TTC_PA_OFF | 8 | 1 | 67 | Disable power amplifier (TX) |
| EPS_POWER_OFF | 8 | 1 | 20 | Switch power line OFF |
| OBC_SET_MODE | 8 | 1 | 50 | Set OBC mode (safe/emergency) |
| EPS_POWER_ON | 8 | 1 | 19 | Re-power a line before restoring its unit |
| TTC_PA_ON | 8 | 1 | 66 | Re-enable the power amplifier |
| AOCS_SET_MODE | 8 | 1 | 0 | Restart the AOCS after its line is restored |

## Procedure Steps

### Step 1: Detect and Confirm Undervoltage Condition
**LABEL:** `STEP-1`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Request EPS housekeeping
**Verify:** `eps.uv_flag == 1` (0x010E, timeout 10 s)
**Verify:** `eps.bus_voltage` (0x0105) — record current value (expected < 27.0 V)
**Verify:** `eps.bat_soc` (0x0101) — record current value
**Verify:** `eps.bat_voltage` (0x0100) — record current value
**Verify:** `eps.power_cons` (0x0106) — record total power consumption
**Verify:** `eps.power_gen` (0x0107) — record power generation
**Verify:** `eps.eclipse_flag` (0x0108) — determine if in eclipse
**Verify:** `eps.load_shed_stage` (0x0134) — record what the on-board shedder has already done
**Verify:** `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117) — record each: 1 = still ON, 0 = already shed on board
**Note:** CHECK THE SPACECRAFT FIRST. A line FDIR has already opened cannot be
shed again: its command is refused S1.8 "power line … is OFF", and that unit's
housekeeping stops, so its mode parameter (e.g. `payload.mode`) freezes at its
last value and can never read the new state. Each level below therefore branches
on the LINE: shed from the ground only what is still ON.
**Action:** Announce "UNDERVOLTAGE — completing load shed from the ground" on the operations loop.
**GO/NO-GO:** Undervoltage confirmed. Flight Director authorizes load shedding — proceed.

### Step 2: Shed Load Priority 1 — Payload OFF
**LABEL:** `STEP-2`
**BRANCH:** `eps.pl_payload == 1` -> GO `STEP-2-SHED` | NO-GO `STEP-2-CHECK` (timeout 10 s)
**Note:** GO — the payload line is still ON: shed it from the ground. NO-GO —
on-board FDIR has already opened it: send nothing and go to the voltage check.

**LABEL:** `STEP-2-SHED`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — Command payload to OFF
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Payload housekeeping
**Verify:** `payload.mode` (0x0600) = 0 (OFF) within 10 s
**Verify:** `eps.power_cons` (0x0106) decreases (expected -45 W if imaging, -8 W if standby)

**LABEL:** `STEP-2-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Wait 30 s and re-check bus voltage
**Verify:** `eps.bus_voltage` (0x0105) — record new value
**BRANCH:** `eps.bus_voltage > 26.5` -> GO `STEP-6` | NO-GO `STEP-3` (timeout 60 s)
**Note:** GO — the shed worked; HOLD at this level and go straight to monitoring.
NO-GO — still declining; fall through to the next shed level. The 60 s branch
timeout is what the prose called "wait 30 s and re-check": it gives the bus two
1 Hz SID 1 samples to settle before the predicate is judged.

### Step 3: Shed Load Priority 2 — FPA Cooler OFF
**LABEL:** `STEP-3`
**BRANCH:** `eps.pl_fpa_cooler == 1` -> GO `STEP-3-SHED` | NO-GO `STEP-3-CHECK` (timeout 10 s)
**Note:** GO — the cooler line is still ON: shed it. NO-GO — already shed on board.

**LABEL:** `STEP-3-SHED`
**TC:** `FPA_COOLER(on=0)` (Service 8, Subtype 1, func_id 43) — Disable FPA cooler
**TC:** `GET_PARAM(param_id=0x040C)` (Service 20, Subtype 3) — `tcs.cooler_fpa`: SID 3 is periodic only every 60 s, so fetch the value this check reads
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS housekeeping
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 (OFF) within 5 s
**Verify:** `eps.power_cons` (0x0106) decreases by ~15 W

**LABEL:** `STEP-3-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Wait 30 s and re-check bus voltage
**Verify:** `eps.bus_voltage` (0x0105) — record new value
**BRANCH:** `eps.bus_voltage > 26.0` -> GO `STEP-6` | NO-GO `STEP-4` (timeout 60 s)

### Step 4: Shed Load Priority 3 — TX Transmitter OFF
**LABEL:** `STEP-4`
**BRANCH:** `eps.pl_ttc_tx == 1` -> GO `STEP-4-SHED` | NO-GO `STEP-4-CHECK` (timeout 10 s)
**Note:** GO — the `ttc_tx` line is still ON: switch the PA off. NO-GO — the line
is already open on board (`TTC_PA_OFF` would be refused S1.8) and the S-band
downlink is already gone.

**LABEL:** `STEP-4-SHED`
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1, func_id 67) — Disable power amplifier
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TT&C housekeeping
**Verify:** `ttc.pa_on` (0x0516) = 0 within 5 s
**Verify:** `eps.power_cons` (0x0106) decreases by ~20 W
**Note:** WARNING — This will terminate downlink capability. Uplink (RX) remains active.
The spacecraft can still receive commands but cannot send telemetry.

**LABEL:** `STEP-4-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Wait 30 s and re-check bus voltage
**Verify:** `eps.bus_voltage` (0x0105) — record new value
**BRANCH:** `eps.bus_voltage > 25.5` -> GO `STEP-6` | NO-GO `STEP-5` (timeout 60 s)
**Note:** After this step the S-band downlink is INHIBITED — `ttc.tx_active`
(0x0525) goes to 0 and telemetry stops. The UHF beacon is a separate radio on the
non-switchable `ttc_rx` line and keeps sending HK SID 11, so the ground can still
see the spacecraft's state; the branch predicate is evaluated from the last
SID 1 sample received before the PA went down, or from the beacon.

### Step 5: Shed Load Priority 4 — Reaction Wheels OFF
**LABEL:** `STEP-5`
**BRANCH:** `eps.pl_aocs_wheels == 1` -> GO `STEP-5-SHED` | NO-GO `STEP-5-CHECK` (timeout 10 s)
**Note:** GO — the wheels line is still ON: open it. NO-GO — already shed on board
(the AOCS has already dropped to OFF, `aocs.mode` 0).

**LABEL:** `STEP-5-SHED`
**TC:** `EPS_POWER_OFF(line_index=7)` (Service 8, Subtype 1, func_id 20) — Power off AOCS wheels
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 0 (OFF) within 5 s
**Note:** WARNING — Spacecraft will lose active attitude control. Residual momentum
will cause slow drift. Magnetic detumbling (if available) or gravity gradient will
provide passive stabilization only.

**LABEL:** `STEP-5-CHECK`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Wait 30 s and re-check
**Verify:** `eps.bus_voltage` (0x0105) — record new value
**BRANCH:** `eps.bus_voltage > 25.0` -> GO `STEP-6` | NO-GO `STEP-5B` (timeout 60 s)

### Step 5B: Last Resort — OBC EMERGENCY Mode
**LABEL:** `STEP-5B`
**Note:** Reached only when every shed level has been taken and the bus is still
below 25.0 V.
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) — EMERGENCY
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Platform/OBDH housekeeping
**Verify:** `obdh.mode == 2` (0x0300, timeout 15 s) — EMERGENCY
**Note:** This step existed only as prose inside Step 5's GO/NO-GO line. Run flat,
the old card would have sent it on EVERY execution — including the common case
where shedding the payload alone recovered the bus.

### Step 6: Monitor Recovery
**LABEL:** `STEP-6`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Monitor EPS telemetry at 60 s intervals
**Verify:** `eps.bus_voltage` (0x0105) — trending upward
**Verify:** `eps.bat_soc` (0x0101) — trending upward (especially in sunlit phase)
**Verify:** `eps.power_gen` (0x0107) > 0 W when in sunlight
**Verify:** `eps.bat_current` (0x0109) — positive (charging) in sunlight
**Action:** Continue monitoring until:
- `eps.bus_voltage` > 28.0 V
- `eps.bat_soc` > 40%
**Note:** Recovery may take multiple orbits depending on depth of discharge and
available solar array power.
**GO/NO-GO:** Bus voltage > 28.0 V and SoC > 40% — proceed to restore loads.

### Step 7: Restore Loads in Reverse Priority Order
**Note:** Re-enable loads one at a time, waiting 5 min between each to verify stability.
Restore only what was shed (on board or by this card), and always re-power the LINE
before the unit's mode command: with the line open every mode command is refused S1.8.
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) — 1. AOCS wheels line, if `eps.pl_aocs_wheels` (0x0117) = 0
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 within 5 s
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) — DETUMBLE, only if `aocs.mode` (0x020F) = 0: the AOCS collapsed to OFF when its line opened and does not restart by itself; it hands itself to COARSE_SUN once the rates are low
**GO/NO-GO:** Bus stable for 5 min with the AOCS wheels restored — restore the next load
**TC:** `EPS_POWER_ON(line_index=2)` (Service 8, Subtype 1, func_id 19) — the `ttc_tx` line first, if `eps.pl_ttc_tx` (0x0112) = 0: with the line open, `TTC_PA_ON` is refused S1.8 "power line 'ttc_tx' is OFF" (on-board FDIR opens it in a deep shed)
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — 2. TX transmitter: verify `ttc.pa_on` (0x0516) = 1
**GO/NO-GO:** Bus stable for 5 min with the transmitter restored — restore the next load
**TC:** `EPS_POWER_ON(line_index=4)` (Service 8, Subtype 1, func_id 19) — the `fpa_cooler` line first, if `eps.pl_fpa_cooler` (0x0114) = 0
**Note:** 3. FPA cooler: leave it OFF. Since 2026-11-03 it runs only to prepare for imaging
(NOM-002 Step 2), and the payload STANDBY command below (4.) would switch it off again.
**GO/NO-GO:** Bus stable for 5 min with the FPA cooler line restored — restore the next load
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) — the `payload` line first, if `eps.pl_payload` (0x0113) = 0: the mode command is otherwise refused S1.8 "power line 'payload' is OFF"
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) — 4. Payload to STANDBY: verify `payload.mode` = 1
**Verify:** After each load addition, confirm `eps.bus_voltage` (0x0105) remains > 27.5 V
and `eps.bat_soc` (0x0101) remains > 35%.
**GO/NO-GO:** All loads restored and power budget positive — procedure complete.

## Verification Criteria
- [ ] `eps.uv_flag` (0x010E) = 0 (cleared)
- [ ] `eps.bus_voltage` (0x0105) > 28.0 V
- [ ] `eps.bat_soc` (0x0101) > 40%
- [ ] All subsystems restored to nominal operating modes
- [ ] Power budget is positive (generation > consumption) with margin
- [ ] No repeat undervoltage events for at least 2 orbits

## Contingency
- If bus voltage drops below 25.0 V after all loads are shed: Command
  `OBC_SET_MODE(mode=2)` for EMERGENCY mode. Spacecraft should enter minimum power
  configuration autonomously.
- If bus voltage does not recover after eclipse exit: Suspect solar array failure.
  Check `eps.sa_a_current` (0x0103) and `eps.sa_b_current` (0x0104). If both near
  zero, escalate to solar array degradation procedure.
- If battery SoC drops below 10%: Risk of battery deep discharge and permanent damage.
  Command EMERGENCY mode immediately. All non-essential functions will be disabled
  by onboard FDIR.
- If loads cannot be restored without triggering undervoltage again: Reduce the
  operational power budget. Operate with reduced payload duty cycle or without FPA
  cooler. Consult with mission planning team.
- If undervoltage recurs within 2 orbits of restoration: Suspect persistent power
  deficit. Re-evaluate power budget with flight dynamics (array degradation,
  eclipse duration, attitude bias).

## Recovery Path — Re-Powering Shed Loads
After this procedure has stabilised the bus and the root cause is understood, **any subsystems whose power lines were de-energised during load shed must be brought back up in the controlled order defined by LEOP-007 (Sequential Power-On)**. Do **not** simply re-enable lines ad-hoc: LEOP-007 enforces the correct subsystem→line→mode sequencing, the inrush spacing, the thermal pre-conditioning of the OBC/battery heaters, and the AOCS/payload set_mode exemptions to the two-stage TC power gate. Cross-reference: `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
