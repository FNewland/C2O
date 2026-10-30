# CTG-010: OBDH Watchdog Recovery
**Subsystem:** OBDH
**Phase:** CONTINGENCY
**Revision:** 1.0
**Approved:** Flight Operations Director

## Purpose
Investigate and recover from an unexpected on-board computer watchdog reset, indicated by
an increment in `obdh.reboot_count` that was not commanded by ground. A watchdog reset may
be caused by software hang, CPU overload, single-event upset (SEU), or memory corruption.
This procedure verifies the OBC has re-initialised correctly, confirms no data loss, and
assesses whether the root cause is transient or systemic.

## Prerequisites
- [ ] TT&C link is active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] Previous `obdh.reboot_count` (0x030A) value is known from last nominal pass
- [ ] Flight software version and patch level are documented on console
- [ ] Mass memory dump capability is available if data recovery is needed

## Procedure Steps

### Step 1 — Confirm Watchdog Reset Occurrence
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.reboot_count` (0x030A) — compare with last known value; confirm increment
**Verify:** `obdh.mode` (0x0300) — record current mode (expected 0=NOMINAL after clean reboot)
**Verify:** `obdh.cpu_load` (0x0302) — record value (expected < 70% post-boot)
**GO/NO-GO:** Reboot count has incremented and OBC is responsive — proceed with assessment

### Step 1b — Boot OBC into Application Image (if in Bootloader)
**Verify:** `obdh.sw_image` (0x0311) — if 0 (BOOTLOADER), the watchdog reset left the OBC in the bootloader and only boot/maintenance funcs are accepted.
**BRANCH:** `obdh.sw_image == 0` -> GO `STEP-1B-BOOT` | NO-GO `STEP-2` (timeout 10 s)
**LABEL:** `STEP-1B-BOOT`
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — issue only if `obdh.sw_image` = 0
**Verify:** S1.1 acceptance + S1.7 execution complete within 15 s
**Verify:** `obdh.sw_image` (0x0311) = 1 (APPLICATION) within 15 s
**GO/NO-GO:** Application image running before any HK_ENABLE / OBC_SET_MODE TCs are issued.

### Step 2 — Verify OBC Nominal Post-Reboot State
**LABEL:** `STEP-2`
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) — if mode = 1 (SAFE), OBC detected an issue during re-init
**Verify:** `obdh.cpu_load` (0x0302) < 70% — elevated load may indicate boot loop or stuck process
**Action:** If OBC is in SAFE mode, assess whether to remain in SAFE or attempt NOMINAL restoration
**GO/NO-GO:** OBC in NOMINAL mode with CPU load < 70% — proceed. If in SAFE mode, proceed with caution.

### Step 3 — Request All Housekeeping Frames
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — OBDH
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TT&C
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Payload
**Verify:** All six HK frames received within 30s
**Verify:** No subsystem is in an unexpected mode or reporting out-of-limit parameters
**GO/NO-GO:** All subsystems reporting nominal — proceed. Any anomalies trigger the respective CTG procedures.

### Step 4 — Verify Data Integrity and Onboard Storage
**Note:** This step ALWAYS resynchronises the clock. Every OBC reboot resets
the onboard clock to J2000 with `obdh.time_ref` (0x0A13) = 0 (NONE), and the GPS
never re-locks a clock from NONE by itself, so there is no "small drift, leave
it" case after a watchdog reset.
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS HK, for `aocs.gps_fix` (0x0274)
**BRANCH:** `aocs.gps_fix >= 2` -> GO `STEP-4-GPS` | NO-GO `STEP-4-GROUND` (timeout 10 s)
**Note:** GO — the GPS has a 3D fix: discipline the clock from GPS. NO-GO — no
fix: set the clock from the ground.

**LABEL:** `STEP-4-GROUND`
**TC:** `SET_TIME(cuc_seconds=T_corrected)` (Service 9, Subtype 1) — ground time set, as LEOP-006 and CTG-021 do
**GO/NO-GO:** Ground time set sent — go to the time check -> GO `STEP-4-CHECK` | NO-GO `STEP-4-CHECK`

**LABEL:** `STEP-4-GPS`
**TC:** `OBC_GPS_TIME_SYNC` (Service 8, Subtype 1, func_id 80) — GPS time sync

**LABEL:** `STEP-4-CHECK`
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — OBDH HK, for `obdh.time_ref` (0x0A13)
**Verify:** `obdh.time_ref != 0` (0x0A13, timeout 15 s) — the clock has a reference again (1 GROUND or 2 GPS)
**TC:** `REQUEST_TIME` (Service 9, Subtype 2) — TM(9,2) time report
**Verify:** |T_obc − T_ground| < 1 s — the NOM-008 tolerance
**Verify:** Stored telecommand queue status — confirm no commands were lost
**Verify:** Mass memory partition status — confirm science data and HK archives are intact
**GO/NO-GO:** Clock referenced and within 1 s of ground time, data integrity confirmed — proceed.

### Step 5 — Assess Root Cause Indicators
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Action:** Review `obdh.cpu_load` (0x0302) trend — was CPU at 100% before reset?
**Action:** Review EPS data — was there a bus voltage dip that could cause brownout?
**Verify:** `eps.bus_voltage` (0x0105) > 27.0V (stable)
**Action:** Check radiation environment data if available from payload housekeeping
**GO/NO-GO:** Root cause classified. If it appears transient (SEU, brief voltage dip): log it. If systemic (repeated high CPU, memory error): raise it to the ground software team. Either way, the OBC mode decides what follows.
**BRANCH:** `obdh.mode == 1` -> GO `STEP-6` | NO-GO `STEP-END` (timeout 10 s)
**Note:** GO — the OBC is in SAFE: Step 6 restores NOMINAL. NO-GO — the OBC is
already NOMINAL: there is nothing to restore and the recovery is complete.

### Step 6 — Restore Nominal Mode if OBC in SAFE
**LABEL:** `STEP-6`
**TC:** `OBC_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 50)
**Verify:** `obdh.mode` (0x0300) = 0 (NOMINAL) within 10s
**Verify:** `obdh.cpu_load` (0x0302) remains < 70% after transition
**Verify:** `aocs.mode` (0x020F) — confirm AOCS has not been disrupted by mode change
**GO/NO-GO:** OBC in NOMINAL, all subsystems stable — recovery complete
**LABEL:** `STEP-END`

## Off-Nominal Handling
- If OBC reboots again during this procedure: Command `OBC_SET_MODE(mode=1)` for SAFE, abort procedure, and escalate to ground software team for code review
- If `obdh.reboot_count` (0x030A) increments by > 3 within 1 hour: Suspect boot loop — command `OBC_SET_MODE(mode=2)` for EMERGENCY and execute EMG-003
- If CPU load remains > 90% post-reboot: command `OBC_SET_MODE(mode=1)` (SAFE) and verify that `obdh.cpu_load` (0x0302) falls. There is no task-shedding parameter on board; SAFE is the load reduction the OBC offers (about 10 percentage points in the simulator).
- If AOCS reverted to DETUMBLE after OBC reset: Execute CTG-002 to restore pointing after OBC is confirmed stable

## Post-Conditions
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL)
- [ ] `obdh.cpu_load` (0x0302) < 70%
- [ ] `obdh.reboot_count` (0x030A) documented; no further unexpected increments
- [ ] All subsystem HK verified nominal
- [ ] Root cause classified as transient or systemic with follow-up action assigned
