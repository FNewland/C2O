# CTG-005: EPS Safe Mode
**Subsystem:** EPS
**Phase:** CONTINGENCY
**Revision:** 1.1 --- 2026-11-02 (Franz's ruling P3): check what on-board FDIR has
already shed before shedding from the ground, and re-power lines before mode
commands. An EPS undervoltage does not by itself put the OBC in SAFE, so Step 1
records the OBC mode instead of requiring SAFE.
**Approved:** Flight Operations Director

## Purpose
Recover the Electrical Power Subsystem from a low-energy state triggered by battery
state-of-charge falling below 20% or main bus voltage dropping below 27.7V. This procedure
sheds non-essential loads to arrest energy depletion, monitors solar array performance during
the sunlit orbital phase, and progressively re-enables loads once the battery has recovered
above 40% SoC.

## Prerequisites
- [ ] Spacecraft has entered OBC safe mode or operator has confirmed EPS anomaly via telemetry
- [ ] TT&C link is active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Current orbit prediction available — next sunlit/eclipse transition times known
- [ ] Power budget spreadsheet (ref: EOSAT1-PWR-BUD-001) accessible on console

## Procedure Steps

### Step 1 — Verify Safe Mode Entry and EPS State
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Platform/OBDH housekeeping
**Verify:** `obdh.mode` (0x0300) — record (1 = SAFE if the OBC was safed; an EPS undervoltage alone leaves it NOMINAL)
**Verify:** `eps.eps_mode` (0x0137) and `eps.load_shed_stage` (0x0134) — record what the EPS has done on its own
**Verify:** `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117) — record each: 0 = already shed on board
**Note:** CHECK THE SPACECRAFT FIRST. A line on-board FDIR has opened cannot be
shed again (the command is refused S1.8 "power line … is OFF"), and its unit's
housekeeping stops, so its mode parameter freezes at its last value. Shed from
the ground only what is still powered.
**Verify:** `eps.bat_soc` (0x0101) — record current value (expected < 20%)
**Verify:** `eps.bus_voltage` (0x0105) — record current value (expected < 27.7V)
**Verify:** `eps.bat_voltage` (0x0100) — record current value
**GO/NO-GO:** Telemetry confirms low-energy state — proceed with load shedding

### Step 2 — Shed Non-Essential Loads: Payload OFF
**BRANCH:** `eps.pl_payload == 1` -> GO `STEP-2-SHED` | NO-GO `STEP-3` (timeout 10 s)
**Note:** GO — the payload line is still ON: shed it from the ground. NO-GO — the
EPS already opened it: nothing to send, the payload is off.
**LABEL:** `STEP-2-SHED`
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26)
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Payload housekeeping
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS housekeeping
**Verify:** `payload.mode` (0x0600) = 0 (OFF) within 10s
**Verify:** `eps.power_cons` (0x0106) decreases by >= 15W within 15s
**GO/NO-GO:** Payload confirmed OFF (by the ground or already on board) and power consumption reduced — proceed

### Step 3 — Verify AOCS Is in Minimum Power Configuration
**LABEL:** `STEP-3`
**BRANCH:** `eps.pl_aocs_wheels == 1` -> GO `STEP-3-ATT` | NO-GO `STEP-3-OFF` (timeout 10 s)
**Note:** GO — the AOCS suite is powered: check its sun hold. NO-GO — a deep shed
has opened the `aocs_wheels` line: the AOCS is OFF (`aocs.mode` 0), the
spacecraft drifts, and `ttc_tx` went before it in the shed order, so only the UHF
beacon (SID 11) is reaching the ground. Do not command the AOCS now; Step 7
re-powers it once the battery has recovered.
**LABEL:** `STEP-3-OFF`
**Note:** AOCS unpowered by the on-board shed — continue at Step 4.
**GO/NO-GO:** Deep shed confirmed — proceed with the AOCS OFF -> GO `STEP-4` | NO-GO `STEP-4`
**LABEL:** `STEP-3-ATT`
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.mode` (0x020F) = 3 (COARSE_SUN) — sun-pointing for maximum array illumination
**Note:** If AOCS is not in COARSE_SUN, command `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) and verify transition within 30s
**GO/NO-GO:** AOCS in COARSE_SUN ensuring optimal solar array orientation — proceed

### Step 4 — Assess Solar Array Performance
**LABEL:** `STEP-4`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.sa_a_current` (0x0103) — record value (expected > 0.5A in sunlight)
**Verify:** `eps.sa_b_current` (0x0104) — record value (expected > 0.5A in sunlight)
**Verify:** `eps.power_gen` (0x0107) — record value (expected > 25W in sunlight, > 45W at optimal incidence)
**GO/NO-GO:** If both SA currents are < 0.2A during confirmed sunlit phase, suspect array failure — escalate to CTG-009. Otherwise proceed.

### Step 5 — Monitor Battery Recovery During Sunlit Phase
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — repeat every 60s
**Verify:** `eps.bat_soc` (0x0101) trending upward (minimum +1% per 10 minutes in sunlight)
**Verify:** `eps.bus_voltage` (0x0105) recovering above 30.9V
**Verify:** `eps.bat_temp` (0x0102) remains within 0 to 40 deg-C during charge
**GO/NO-GO:** SoC increasing and battery temp nominal — continue monitoring until SoC > 40%

### Step 6 — Re-Enable Loads: Payload to Standby
**TC:** `EPS_POWER_ON(line_index=3)` (Service 8, Subtype 1, func_id 19) — the `payload` line first, if `eps.pl_payload` (0x0113) = 0 (an on-board shed opens it; the mode command is then refused S1.8 "power line 'payload' is OFF")
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26)
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) within 10s
**Verify:** `eps.bat_soc` (0x0101) remains > 35% after load addition (allow 60s stabilisation)
**Verify:** `eps.power_cons` (0x0106) increase is consistent with payload standby draw (~8W)
**GO/NO-GO:** SoC stable above 35% with payload in standby — proceed

### Step 7 — Restore Nominal AOCS Mode
**TC:** `EPS_POWER_ON(line_index=7)` (Service 8, Subtype 1, func_id 19) — the `aocs_wheels` line first, if `eps.pl_aocs_wheels` (0x0117) = 0 (a deep shed opens it and drops `aocs.mode` to 0; the mode command is then refused S1.8 "power line 'aocs_wheels' is OFF")
**Verify:** `eps.pl_aocs_wheels` (0x0117) = 1 within 5s
**BRANCH:** `aocs.mode == 0` -> GO `STEP-7-DET` | NO-GO `STEP-7-NOM` (timeout 10 s)
**Note:** GO — the AOCS collapsed to OFF when its line opened and does not
restart by itself: DETUMBLE first. NO-GO — it is already running: go to NOMINAL.
**LABEL:** `STEP-7-DET`
**TC:** `AOCS_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 0) — DETUMBLE; the AOCS hands itself to COARSE_SUN once the rates are low
**BRANCH:** `aocs.mode == 3` -> GO `STEP-7-NOM` | NO-GO `STEP-7-NOM` (timeout 1800 s)
**LABEL:** `STEP-7-NOM`
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0)
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) within 30s
**Verify:** `eps.bat_soc` (0x0101) remains > 30% after AOCS transition
**GO/NO-GO:** Attitude nominal and SoC stable — proceed to restore OBC mode

### Step 8 — Restore OBC to Nominal Mode
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) within 10s
**Verify:** `eps.bat_soc` (0x0101) > 40%
**Verify:** `eps.bus_voltage` (0x0105) > 32.1V
**GO/NO-GO:** All subsystems nominal and energy budget positive — recovery complete

## Off-Nominal Handling
- If SoC drops below 10% at any step: Command `OBC_SET_MODE(mode=2)` for EMERGENCY, execute EMG-002
- If battery temperature exceeds 45 deg-C during charge: Command `HEATER_BATTERY(on=0)` and reduce charge rate via `SET_PARAM(param_id=eps.charge_limit, value=0.5)`
- If solar array output remains < 0.2A for full sunlit pass: Execute CTG-009 (Solar Array Degradation)
- If bus voltage drops below 28.4V: Execute EMG-002 immediately

## Post-Conditions
- [ ] `eps.bat_soc` (0x0101) > 40%
- [ ] `eps.bus_voltage` (0x0105) > 32.1V
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] `payload.mode` (0x0600) >= 1 (STANDBY or higher)
- [ ] Power budget is positive with margin > 5W confirmed by Flight Dynamics

## Recovery Path — Re-Powering Shed Loads
After this procedure has stabilised the bus and the root cause is understood, **any subsystems whose power lines were de-energised during load shed must be brought back up in the controlled order defined by LEOP-007 (Sequential Power-On)**. Do **not** simply re-enable lines ad-hoc: LEOP-007 enforces the correct subsystem→line→mode sequencing, the inrush spacing, the thermal pre-conditioning of the OBC/battery heaters, and the AOCS/payload set_mode exemptions to the two-stage TC power gate. Cross-reference: `configs/eosat1/procedures/leop/sequential_power_on.md` (PROC-LEOP-007).
