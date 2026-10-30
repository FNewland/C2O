# English-source errata — found during the French translation (packet E1)

*Compiled 2026-10-28 from the translator notes in `/home/claude/work/xlate/*/NOTES.md` and `Y1_NOTES.md` (~25 packets). Every Section 1 item was checked against `smo/configs/eosat1/` (tc_catalog.yaml, telemetry, events, aocs, subsystems, mission/orbit) and the simulator code in `smo/packages`; every Section 2 item was recomputed in Python. Translator claims that the tree contradicts are kept and marked NOT CONFIRMED. Line numbers are real source-file lines (packet lines converted with the packet offsets) and were machine-checked against the quoted text. No source file was edited.*

## Summary

| Document | §1 wrong/rejected TC | §2 numbers | §3 inconsistencies | §4 editorial | Total | Confirmed / not confirmed |
|---|---:|---:|---:|---:|---:|---:|
| SpaceCDF course textbook + learner workbook (Drive) | 0 | 20 | 18 | 17 | 55 | 36 / 0 |
| ORBIT NORTH ops book, ops workbook, instructor book, back cover (Drive) | 17 | 9 | 16 | 14 | 56 | 39 / 5 |
| ORBIT NORTH week-3 pack (cdf/docs/orbit_north/week3) | 3 | 0 | 6 | 2 | 11 | 8 / 0 |
| OER *Concurrent Spacecraft Design* | 0 | 3 | 8 | 1 | 12 | 8 / 0 |
| EOSAT-1 manual (smo/configs/eosat1/manual) | 15 | 2 | 22 | 6 | 45 | 35 / 1 |
| SMO procedures (LEOP, commissioning, nominal, contingency, emergency) | 41 | 0 | 20 | 1 | 62 | 51 / 1 |
| SMO operator docs + SpaceCDF guides / course plan | 10 | 2 | 10 | 5 | 27 | 20 / 0 |
| **Total** | **86** | **36** | **100** | **46** | **268** | **197 / 7** |

The remaining 64 entries are REPORTED (translator observation; line verified, claim not independently checked) or PLAUSIBLE (needs the author). Many entries group several occurrences of one defect (e.g. one MAG_SELECT entry per document), so the number of edits is larger than the entry count.

### How to fix in both languages

1. Edit the **English** source only (the French files mirror the English errors on purpose, so they stay aligned).
2. Run `python3 -m tools.i18n status` in the repo that owns the file (`smo/` for the manual, procedures and `docs/`; `cdf/` for the course books on Drive, the OER, the week-3 pack and the SpaceCDF docs). Each edited English section shows as **stale**.
3. Run `python3 -m tools.i18n translate --stale` (add `--api` to use the configured model) to get a minimal-edit bundle; apply the French, then `python3 -m tools.i18n check` and `accept`.
4. Procedure cards: after editing, re-run the parser equivalence check (`smo_common.procedures.schema`) so EN and FR still extract identical steps. Course books live on Google Drive (`SpaceCDF/docs/course/`, French in `…/course/fr/`); the week-3 French files are not yet installed under `cdf/docs/orbit_north/week3/fr/` (staged in `xlate/W2/<name>/fr.md`).

### The ten most important confirmed items

1. **CTG-026 sends a non-existent command on ST2's function ID.** `AOCS_3W_MODE` (func_id 5) in `procedures/contingency/aocs_actuator_stuck_recovery.md` L54/L103; func 5 is `ST2_POWER`. Use `AOCS_DISABLE_WHEEL` (func 2).
1. **Reboot-cause codes are decoded wrongly in CTG-018, CTG-021 and CTG-011.** The model uses 1=commanded, 2=watchdog, 3=memory, 4=switchover. As written, a memory-error boot skips the memory check.
1. **`ST_SELECT` uses unit 0/1.** Unit 0 is refused and unit 1 re-selects the failed ST1. Found in the ops book (L2184, L7126, L8118/8125, L8691/8700), ops workbook L1444, walkthrough L553, OPERATIONS_GUIDE L1572 and PUS reference L422. The catalogue encoding is 1=ST1, 2=ST2.
1. **`MAG_SELECT` (func 7) was removed and is refused with 0x0007, but is still taught.** Found in the ops book (COM-003, COM-013, CTG-025, Table 7.6a), instructor book L841/L881, CTG-026 L226, OPERATIONS_GUIDE L1573 and PUS reference L423. Dual-magnetometer prose remains in the ops book, manual 00 and software_architecture.
1. **The PUS reference EPS function table (L438–446) is stale.** For example, func 19 is listed as charge rate but is `EPS_POWER_ON`. The translator note had this backwards: the quick reference is correct. Separately, OPERATIONS_GUIDE Pass 3 sends `EPS_SWITCH_LOAD` as func 17, which is `EPS_FPA_COOLER`.
1. **AOCS mode numbers are wrong.** `AOCS_SET_MODE(mode=0)` is used to 'return to NADIR_POINT' (manual 08 L131/L145, 09_leop L438/L457), but mode 0 is OFF. NOM-009 expects mode 0 = NOMINAL. CTG-009, CTG-023 and CTG-024 verify 3 = NOMINAL / 2 = COARSE_SUN; the correct values are 4 and 3.
1. **The manual leaves the bootloader with `OBC_SET_MODE(0)`** (func 50, refused 0x0006) instead of `OBC_BOOT_APP` (func 55) in 09_leop L187/L200/L546 and 04_obdh. It also sets time with `SET_TIME` in the bootloader, which fails at execution.
1. **'There is no phase-transition telecommand' is wrong.** The claim appears in instructor book L40 and ops workbook L563/L674/L1077. breakpoint_spec L168 uses func 80 (GPS time sync), and walkthrough §16.3 expects an automatic transition. `SYS_SET_MISSION_PHASE` (func 120) is the only way to reach phases 5 and 6.
1. **Walkthrough §11.1 powers the GPS with `SET_PARAM(0x0230, 1)`.** 0x0230 is `aocs.wheel_torque_cmd`, and the GPS fix, satellite-count and altitude IDs are also wrong. Use S2 device 0x020F; the correct IDs are 0x0274, 0x0276 and 0x0212.
1. **The manual's contingency chapter (10_commissioning_contingency_procedures.md) has 36 procedure links that open the right file under the wrong CTG/EMG ID.** The desk-procedure escalation table also cites a non-existent CON-xxx family and wrong EMG titles.

Status key: **CONFIRMED** = verified against the tree or by recomputation; **NOT CONFIRMED** = the translator's note is wrong (kept so nobody 'fixes' correct text); **REPORTED** = translator observation, line checked but not independently verified; **PLAUSIBLE** = likely, needs the author.

## Section 1 — Would make a student/operator send a wrong or rejected telecommand

### High severity

#### E1-1.01 · CONFIRMED (new) · Procedure — contingency/aocs_actuator_stuck_recovery.md, line 103

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/aocs_actuator_stuck_recovery.md` — L103
- **Says:** `AOCS_3W_MODE(exclude_wheel=<N>)` (Service 8, Subtype 1, func_id 5); also Required Commands table L54 `| AOCS_3W_MODE | 8 | 1 | 5 |`.
- **Should say:** `AOCS_DISABLE_WHEEL(wheel_idx=<N>)` (Service 8, Subtype 1, func_id 2) — the catalogue's 3-of-4 wheel isolation command; restore with `AOCS_ENABLE_WHEEL` (func_id 3). Fix the L54 table row too.
- **Evidence:** tc_catalog.yaml has no AOCS_3W_MODE; func_id 5 is `ST2_POWER(on)`. A raw func-5 send would power-cycle star tracker 2 instead of isolating a wheel. Not caught by any translator note; found by this audit.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/aocs_actuator_stuck_recovery.md`

#### E1-1.02 · CONFIRMED (P2a #6) · Procedure — contingency/boot_loader_recovery.md, line 52

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/boot_loader_recovery.md` — L52
- **Says:** CTG-018 Step 1 decodes `obdh.last_reboot_cause` as 0=none, 1=watchdog, 2=memory, 3=switchover, 4=commanded (L51–55), the L59 note uses 3=memory, and the Step 2 branch (L64–75) routes on that list. The telemetry table at L24 says 1=commanded, 2=watchdog, 3=memory, 4=switchover.
- **Should say:** 0=none, 1=commanded, 2=watchdog, 3=memory, 4=switchover in Step 1, the L59 note (`= 3 (memory)` is right) and the Step 2 branches: memory → cause 3, switchover → cause 4, watchdog → cause 2, commanded → cause 1.
- **Evidence:** obdh_basic.py L44–48 `REBOOT_COMMAND=1, REBOOT_WATCHDOG=2, REBOOT_MEMORY_ERROR=3, REBOOT_SWITCHOVER=4`; parameters.yaml 0x0316 description identical. As written, a memory-error boot (cause 3) is routed to the 'switchover → attempt boot' path and skips the memory check.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/boot_loader_recovery.md`

#### E1-1.03 · CONFIRMED (P2b) · Procedure — contingency/obc_bootloader_recovery.md, line 65

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/obc_bootloader_recovery.md` — L65
- **Says:** CTG-021 Step 1 (L64–68) and Step 2 branch (L80 ff.) use 1=watchdog, 2=memory, 3=switchover, 4=commanded; the telemetry table (L32) uses 1=commanded…4=switchover.
- **Should say:** Use the L32 encoding (1=commanded, 2=watchdog, 3=memory, 4=switchover) in Step 1 and in every Step 2 branch.
- **Evidence:** obdh_basic.py REBOOT_* constants; parameters.yaml 0x0316. Same consequence as CTG-018: memory-error boots skip the memory check.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/obc_bootloader_recovery.md`

#### E1-1.04 · CONFIRMED (P2b) · Procedure — contingency/obc_redundancy_switchover.md, line 54

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/obc_redundancy_switchover.md` — L54
- **Says:** Step 1: `0 = none, 1 = watchdog, 2 = memory, 3 = switchover, 4 = commanded`, while L30 and Step 3 (L81) expect 4 = switchover after the switch.
- **Should say:** `0 = none, 1 = commanded, 2 = watchdog, 3 = memory, 4 = switchover`.
- **Evidence:** obdh_basic.py L940 sets `REBOOT_SWITCHOVER` (=4) on OBC_SWITCH_UNIT.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/obc_redundancy_switchover.md`

#### E1-1.05 · CONFIRMED (M2 #27) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 497

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L497
- **Says:** §11.1 'Enable GPS Receiver': `SET_PARAM(0x0230, 1)` (S20.1) — GPS receiver power ON; verify table: GPS fix 0x0210 (approx), satellites 0x0232, altitude 0x0235.
- **Should say:** Power the receiver with `S2_AOCS_GPS_RECEIVER(device_id=0x020F, state=1)` (S2.1). Verify `aocs.gps_fix` 0x0274 = 3, `aocs.gps_num_sats` 0x0276 ≥ 4, `aocs.gps_alt` 0x0212 ≈ 513 km.
- **Evidence:** parameters.yaml: 0x0230 = `aocs.wheel_torque_cmd` (the TC would overwrite the commanded wheel torque), 0x0210 = gps_lat, 0x0232 = gps_ecef_y, 0x0235 = gps_vel_y. tc_catalog.yaml L150 `S2_AOCS_GPS_RECEIVER` is the GPS power command. orbit.yaml altitude_km 513.0.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-1.06 · CONFIRMED (M1) · EOSAT-1 manual — 08_fdir.md, line 131

- **File:** `/home/claude/work/smo/configs/eosat1/manual/08_fdir.md` — L131
- **Says:** Safe-mode recovery step 6: 'Command `AOCS_SET_MODE` (mode=0) to return to NADIR_POINT'; L145 'Ground commands `AOCS_SET_MODE` (mode=0) to enter NADIR_POINT'.
- **Should say:** `AOCS_SET_MODE(mode=4)` (NOMINAL) at both lines; there is no NADIR_POINT mode.
- **Evidence:** tc_catalog.yaml AOCS_SET_MODE enum: 0=OFF … 4=NOMINAL_NADIR; aocs_mode_codes.yaml 4=NOMINAL. Mode 0 switches AOCS off.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/08_fdir.md`

#### E1-1.07 · CONFIRMED (M2 #3) · EOSAT-1 manual — 09_leop.md, line 438

- **File:** `/home/claude/work/smo/configs/eosat1/manual/09_leop.md` — L438
- **Says:** §8: 'Command AOCS to NADIR_POINT mode via `AOCS_SET_MODE` (mode=0)'; checklist L457 'NADIR_POINT (mode=0)'; §8 also uses SAFE_POINT (L427, L431).
- **Should say:** `AOCS_SET_MODE(mode=4)` NOMINAL (L438, L457); replace SAFE_POINT with COARSE_SUN (mode 3).
- **Evidence:** aocs_mode_codes.yaml / tc_catalog.yaml AOCS_SET_MODE enum.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/09_leop.md`

#### E1-1.08 · CONFIRMED (P3) · Procedure — nominal/routine_health_check.md, line 42

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/routine_health_check.md` — L42
- **Says:** NOM-009 Verify: `aocs.mode` (0x020F) = 0 (NOMINAL / NOMINAL).
- **Should say:** `aocs.mode` (0x020F) = 4 (NOMINAL).
- **Evidence:** aocs_mode_codes.yaml: 0 = OFF, 4 = NOMINAL. The runner check fails on a healthy spacecraft.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/routine_health_check.md`

#### E1-1.09 · CONFIRMED (P2b) · Procedure — contingency/solar_array_degradation.md, line 41

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/solar_array_degradation.md` — L41
- **Says:** CTG-009 Step Verify: `aocs.mode` (0x020F) = 3 (NOMINAL) or 2 (COARSE_SUN); L70 then commands mode=3 as COARSE_SUN.
- **Should say:** `aocs.mode` = 4 (NOMINAL) or 3 (COARSE_SUN).
- **Evidence:** aocs_mode_codes.yaml: 2 = DETUMBLE, 3 = COARSE_SUN, 4 = NOMINAL.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/solar_array_degradation.md`

#### E1-1.10 · CONFIRMED (P2b) · Procedure — contingency/solar_panel_loss_response.md, line 84

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/solar_panel_loss_response.md` — L84
- **Says:** CTG-024 Step 3 Verify: `aocs.mode` = 3 (NOMINAL) or 2 (COARSE_SUN); Step 6 (L136/L144) uses 3 = COARSE_SUN, 4 = NOMINAL.
- **Should say:** `aocs.mode` = 4 (NOMINAL) or 3 (COARSE_SUN).
- **Evidence:** aocs_mode_codes.yaml.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/solar_panel_loss_response.md`

#### E1-1.11 · CONFIRMED (P2b) · Procedure — contingency/progressive_load_shed.md, line 202

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/progressive_load_shed.md` — L202
- **Says:** CTG-023 Step 8 Verify: `aocs.mode` = nominal mode (3 = NOMINAL if restored); Step 7a (L163) correctly commands 3 = COARSE_SUN.
- **Should say:** `aocs.mode` = 4 (NOMINAL) if restored, or 3 (COARSE_SUN) if still holding.
- **Evidence:** aocs_mode_codes.yaml.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/progressive_load_shed.md`

#### E1-1.12 · CONFIRMED (O1 #9) · ORBIT NORTH operations book, line 2184

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L2184
- **Says:** Ops book Table 7.6a: `ST_SELECT(unit=0/1)` — 'Select primary star tracker (0=ST1, 1=ST2)'.
- **Should say:** `ST_SELECT(unit=1/2)` — 1=ST1, 2=ST2 (0 is refused). §6.3 (L1017) already says '1 or 2'.
- **Evidence:** tc_catalog.yaml ST_SELECT `unit: 1=ST1, 2=ST2 (0 is refused)`; aocs_basic.py L3969 `if unit not in (1, 2): Invalid ST unit`.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.13 · CONFIRMED (O4a #2) · ORBIT NORTH operations book, line 7126

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L7126
- **Says:** COM-003 card step 5: `ST_SELECT(unit=0)` (func_id 6) to select the prime tracker.
- **Should say:** `ST_SELECT(unit=1)` (selects ST1).
- **Evidence:** tc_catalog.yaml ST_SELECT; aocs_basic.py L3969 refuses unit 0. The shipped card procedures/commissioning/aocs_sensor_calibration.md L91 already uses unit=1.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.14 · CONFIRMED (new) · ORBIT NORTH operations book, line 8125

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L8125
- **Says:** CTG-008 card: 'AOCS: select ST2 as primary | `ST_SELECT(unit=1)`'; decision tree L8118 'IF ST2 = 2 (TRACKING) … → `ST_SELECT(unit=1)`'.
- **Should say:** `ST_SELECT(unit=2)` at L8118 and L8125.
- **Evidence:** tc_catalog.yaml: unit 1 = ST1. As written the operator re-selects the failed ST1. Shipped card star_tracker_failure.md L83 uses unit=2. Not in the translator notes; found by this audit.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.15 · CONFIRMED (new) · ORBIT NORTH operations book, line 8700

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L8700
- **Says:** CTG-025 card step 2: 'if ST1 faulted, power on ST2 and select it | `ST2_POWER(on=1)`; `ST_SELECT(unit=1)`'; same in the decision tree L8691.
- **Should say:** `ST_SELECT(unit=2)` at L8691 and L8700.
- **Evidence:** tc_catalog.yaml: unit 1 = ST1. Shipped aocs_sensor_loss_recovery.md L99 uses unit=2. Found by this audit.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.16 · CONFIRMED (W2) · ORBIT NORTH week-3 operations workbook, line 1444

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3_workbook.md` (local copy `/home/claude/work/drive_course/orbit_north_week3_workbook.md`) — L1444
- **Says:** Ops workbook CTG-008 confirm sheet step 3: 'Select it: `ST_SELECT(unit=1)`' — selecting ST2 after ST1 failed.
- **Should say:** `ST_SELECT(unit=2)`.
- **Evidence:** tc_catalog.yaml ST_SELECT 1=ST1, 2=ST2.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3_workbook.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3_workbook.md`)

#### E1-1.17 · CONFIRMED (M2 #25) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 553

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L553
- **Says:** `ST_SELECT(unit=0)` (S8.1, func_id 6, data byte = 0) — select ST1 as primary.
- **Should say:** `ST_SELECT(unit=1)` (data byte = 1).
- **Evidence:** tc_catalog.yaml; aocs_basic.py L3969.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-1.18 · CONFIRMED (D1a #9) · SMO docs — OPERATIONS_GUIDE.md, line 1572

- **File:** `/home/claude/work/smo/docs/OPERATIONS_GUIDE.md` — L1572
- **Says:** Pass 7 table: step 34 `S8.1 ST_SELECT (unit 0)`; step 35 `S8.1 MAG_SELECT (unit 0)` func 7.
- **Should say:** Step 34: `ST_SELECT (unit 1)`. Step 35: delete (MAG_SELECT removed; single magnetometer) or replace with a read of `aocs.mag_enabled` 0x025C.
- **Evidence:** tc_catalog.yaml ST_SELECT; catalogue comment L546 'MAG_SELECT (S8 func 7) removed'; aocs_basic.py L3977–3985 refuses with 0x0007.
- **French mirror:** `/home/claude/work/smo/docs/fr/OPERATIONS_GUIDE.md`

#### E1-1.19 · CONFIRMED (new) · SMO docs — PUS_SERVICE_REFERENCE.md, line 422

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L422
- **Says:** AOCS function table: func 6 `ST_SELECT | unit (0/1) | (0=ST1, 1=ST2)`; func 7 `MAG_SELECT | unit (0/1)`; func 0 `mode (0-8)`.
- **Should say:** func 6 `unit (1/2) — 1=ST1, 2=ST2 (0 refused)`; delete the func 7 row (or mark 'retired — refused 0x0007'); func 0 `mode (0-9)`.
- **Evidence:** tc_catalog.yaml ST_SELECT, AOCS_SET_MODE enum 0–9 (9 = INERTIAL), no func 7. Not in the translator notes for this file.
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-1.20 · CONFIRMED (D1b #6 — corrected direction) · SMO docs — PUS_SERVICE_REFERENCE.md, line 438

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L438
- **Says:** EPS function table (L436–446): 17 EPS_SWITCH_LOAD, 18 EPS_BATTERY_HEATER, 19 EPS_CHARGE_RATE, 20 EPS_SOLAR_DRIVE, 21 EPS_EMERGENCY_SHED, 22 EPS_BUS_ISOLATION, 23–25 EPS_LOAD_SHED_STAGE_1/2/3.
- **Should say:** 16 EPS_PAYLOAD_MODE, 17 EPS_FPA_COOLER, 18 EPS_TRANSPONDER_TX, 19 EPS_POWER_ON(line_index 0–8), 20 EPS_POWER_OFF, 21 EPS_RESET_OC_FLAG, 22 EPS_SWITCH_LOAD(load_id, state), 23 EPS_SET_CHARGE_RATE, 24 EPS_SOLAR_ARRAY_DRIVE (centi-degrees), 25 EPS_EMERGENCY_LOAD_SHED(stage 0–3). Also list 81 EPS_DEPLOY_WING, 82 EPS_WING_STATUS, 83 EPS_SET_MODE.
- **Evidence:** tc_catalog.yaml S8 func 16–25, 81–83. NOTE: the D1b translator flagged the 'Load Shedding' quick reference (L1228–1239) as the wrong one — it is the reverse: the quick reference is correct and itself says 'earlier revisions mislabelled 23/24/25'; the EPS table is the stale part. An operator using the table to send func 19 'charge rate' would switch a power line on.
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-1.21 · CONFIRMED (new) · SMO docs — OPERATIONS_GUIDE.md, line 1510

- **File:** `/home/claude/work/smo/docs/OPERATIONS_GUIDE.md` — L1510
- **Says:** Pass 3 steps 13–14: `S8.1 EPS_SWITCH_LOAD (line 0, on)` / `(line 1, on)`, func_id 17.
- **Should say:** func_id 22 for EPS_SWITCH_LOAD(load_id, state) — or, for power lines, `EPS_POWER_ON(line_index=N)` func 19.
- **Evidence:** tc_catalog.yaml: func 17 = EPS_FPA_COOLER (the TC as written toggles the FPA cooler), 22 = EPS_SWITCH_LOAD. Found by this audit.
- **French mirror:** `/home/claude/work/smo/docs/fr/OPERATIONS_GUIDE.md`

#### E1-1.22 · CONFIRMED (M2 #4) · EOSAT-1 manual — 09_leop.md, line 200

- **File:** `/home/claude/work/smo/configs/eosat1/manual/09_leop.md` — L200
- **Says:** §5: 'Send `OBC_SET_MODE` (mode=0) to command transition from BOOTLOADER to APPLICATION'; bootloader command table L187 'OBC_SET_MODE (0) | Boot application software'; recovery L546 'Attempt `OBC_SET_MODE` (mode=0) again'.
- **Should say:** `OBC_BOOT_APP` (S8.1 func 55) at L187, L200 and L546.
- **Evidence:** tc_catalog.yaml: OBC_SET_MODE is func 50 (0=nominal,1=safe,2=emergency); OBC_BOOT_APP is func 55. engine.py L2880 bootloader subset {19,20,52–57,61,66,67,69,120} — func 50 is refused at acceptance with 0x0006 while in the bootloader.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/09_leop.md`

#### E1-1.23 · CONFIRMED (M1) · EOSAT-1 manual — 04_obdh.md, line 111

- **File:** `/home/claude/work/smo/configs/eosat1/manual/04_obdh.md` — L111
- **Says:** 'Restricted Command Set in BOOTLOADER' table: OBC_SET_MODE (0) → application; OBC_SET_MODE (2); SET_TIME; HK_REQUEST (SID 11); SW_UPLOAD; SW_ACTIVATE. Also §3 L75/L141/L162 use OBC_SET_MODE (mode=0) to leave the bootloader.
- **Should say:** Replace with the real subset: S17.1; S9.1 (accepted but SET_TIME fails at execution until the application runs); S3 beacon HK (SID 11); S20.1/S20.3; S8.1 funcs 19/20, 52–57 (incl. OBC_BOOT_APP 55), 61, 66/67, 69, 120. Use OBC_BOOT_APP at L75, L141, L162. SW_UPLOAD/SW_ACTIVATE do not exist (software load is S6.2 MEM_LOAD).
- **Evidence:** engine.py L2835–2881; 00_mission_overview.md L176–179 states the correct subset; tc_catalog.yaml has no SW_UPLOAD/SW_ACTIVATE mnemonics.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/04_obdh.md`

#### E1-1.24 · CONFIRMED (M2 #1) · EOSAT-1 manual — 09_leop.md, line 161

- **File:** `/home/claude/work/smo/configs/eosat1/manual/09_leop.md` — L161
- **Says:** §4.3 step 4 uplinks `SET_TIME` while still in BOOTLOADER; bootloader command table L188 lists SET_TIME 'Synchronise onboard clock'.
- **Should say:** Move the time set after OBC_BOOT_APP (as 12_time_and_clocks.md §6/§8 and LEOP-006 do), or state that S9.1 is accepted but fails at execution in the bootloader.
- **Evidence:** engine.py L2858 accepts S9.1 at acceptance, but obdh_basic.py L1058–1075 `_BOOTLOADER_ALLOWED` excludes set_time, so execution fails ('Bootloader: set_time not available pre-boot'). 12_time_and_clocks.md L205/L297 already says so. The catalogue description of SYS_SET_MISSION_PHASE ('S9.1' in the bootloader subset) is itself misleading — see §3.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/09_leop.md`

#### E1-1.25 · CONFIRMED (W2) · Week 3 pack — breakpoint_spec.md, line 168

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/breakpoint_spec.md` — L168
- **Says:** Expected response: 'Transition to COMMISSIONING phase (S8 func_id 80)'.
- **Should say:** 'Declare COMMISSIONING: `SYS_SET_MISSION_PHASE(phase=5)` (S8 func_id 120)'.
- **Evidence:** tc_catalog.yaml: func 80 = OBC_GPS_TIME_SYNC; func 120 = SYS_SET_MISSION_PHASE, 'COMMISSIONING (5) and NOMINAL (6) are ground declarations and this is the telecommand that makes them'.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/breakpoint_spec.md` (not yet installed; staged at `/home/claude/work/xlate/W2/breakpoint_spec/fr.md`)

#### E1-1.26 · CONFIRMED (W2) · Instructor book (scenario catalogue), line 42

- **File:** Drive `SpaceCDF/docs/course/instructor_book.md` (local copy `/home/claude/work/drive_course/instructor_book.md`) — L42
- **Says:** 'Phase transition is console-only … There is **no** flight telecommand for it … do not tell a team to command a phase change.' Same claim in the ops workbook L563, L674, L1077 ('there is no phase-transition telecommand').
- **Should say:** Phases 5 (COMMISSIONING) and 6 (NOMINAL) are declared with `SYS_SET_MISSION_PHASE(phase=N)` (S8.1 func 120, FORCE flag for backwards moves); the instructor `set_phase` is an instructor override. Align the workbook rows (L563, L674, L1077).
- **Evidence:** tc_catalog.yaml func 120 description; event 0x0055 MISSION_PHASE_CHANGED; manual 09_leop.md §9.2 already uses SYS_SET_MISSION_PHASE. The phase gates sc_mode NOMINAL and the propulsion interlock, so 'never command it' leaves teams stuck at phase 4.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/instructor_book.md` (local build `/home/claude/work/out/course_fr/instructor_book.md`)

#### E1-1.27 · CONFIRMED (M2 #29) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 763

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L763
- **Says:** §16.3 'The engine should automatically transition `spacecraft_phase` (0x0129) to 5 (COMMISSIONING) and then to the nominal ops phase once all conditions are met.'
- **Should say:** 'Declare COMMISSIONING then NOMINAL with `SYS_SET_MISSION_PHASE(phase=5)` then `(phase=6)` (S8.1 func 120); nothing advances the phase past 4 automatically.'
- **Evidence:** tc_catalog.yaml SYS_SET_MISSION_PHASE: 'Nothing else advances the phase past 4 (LEOP)'. 09_leop.md §9.2 agrees.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-1.28 · CONFIRMED (W2) · Week 3 pack — student_procedure_quickref.md, line 38

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/student_procedure_quickref.md` — L38
- **Says:** LEOP-001 summary: '(3) issue OBC_BOOT_APP command (S8 func_id 42)'.
- **Should say:** '(S8 func_id 55)'.
- **Evidence:** tc_catalog.yaml: OBC_BOOT_APP = 55; func 42 = HEATER_THRUSTER (also refused in the bootloader).
- **French mirror:** `cdf/docs/orbit_north/week3/fr/student_procedure_quickref.md` (not yet installed; staged at `/home/claude/work/xlate/W2/student_procedure_quickref/fr.md`)

#### E1-1.29 · CONFIRMED (O4a #1) · ORBIT NORTH operations book, line 7125

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L7125
- **Says:** COM-003 card step 4: 'calibrate the magnetometers, select the prime | `MAG_SELECT(unit=0)` (S8 func_id 7) | B agrees with A within 5 %'.
- **Should say:** 'AOCS: verify the magnetometer | read `aocs.mag_enabled` (0x025C) = 1 and `aocs.mag_field_total` (0x0277) 25 000–65 000 nT' — no command; single-string MAG.
- **Evidence:** tc_catalog.yaml L546 'MAG_SELECT (S8 func 7) removed … (2026-08c item 8)'; aocs_basic.py L3977 refuses with 0x0007; parameters.yaml retires 0x0223–0x0229. Shipped COM-003 (aocs_sensor_calibration.md) has no MAG_SELECT.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.30 · CONFIRMED (O4a #1) · ORBIT NORTH operations book, line 7452

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L7452
- **Says:** COM-013 card step 1: 'verify both magnetometers, select the prime | `MAG_SELECT(unit=0)` | A and B agree within 5 %'.
- **Should say:** 'verify the magnetometer | read 0x025C = 1, 0x0277 in 25–65 µT' — no command.
- **Evidence:** As above; shipped adcs_commissioning.md L10 'the MAG_SELECT command are retired — func 7 is REFUSED on board'.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.31 · CONFIRMED (O4b #1) · ORBIT NORTH operations book, line 8702

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L8702
- **Says:** CTG-025 card step 4 'if the magnetometer faulted, switch source | `MAG_SELECT(unit=0|1)`'; decision tree L8693 '`MAG_SELECT(unit=…)`'; step 1 (L8699) reads `mag_select` 0x0229; Table 7.6a L2185 and the glossary row L9282 still list MAG_SELECT.
- **Should say:** Delete the MAG_SELECT step/branch and the L2185/L9282 rows; L8699 read `mag_enabled` 0x025C only; 'magnetometer lost → DETUMBLE/desaturation impossible, escalate' (single-string).
- **Evidence:** tc_catalog.yaml L546; parameters.yaml L172 (0x0223–0x0229 RETIRED). Shipped aocs_sensor_loss_recovery.md L151 says 'no MAG_SELECT'.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.32 · CONFIRMED (W2) · Instructor book (scenario catalogue), line 841

- **File:** Drive `SpaceCDF/docs/course/instructor_book.md` (local copy `/home/claude/work/drive_course/instructor_book.md`) — L841
- **Says:** Scenario timeline `mag_a_fail`: 'magnetometer A fails; operator must `MAG_SELECT` (S8 func 7) to B'; L881 'switches to magnetometer B (`MAG_SELECT`, func 7)'.
- **Should say:** Rewrite the cue: the single magnetometer fails; expected response is to recognise loss of B-dot/desaturation and protect momentum (no switch exists).
- **Evidence:** tc_catalog.yaml L546; aocs_basic.py L3977–3985.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/instructor_book.md` (local build `/home/claude/work/out/course_fr/instructor_book.md`)

#### E1-1.33 · CONFIRMED (P2a #1d) · Procedure — contingency/aocs_actuator_stuck_recovery.md, line 226

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/aocs_actuator_stuck_recovery.md` — L226
- **Says:** Off-nominal: 'first — `MAG_SELECT(select=1)` (func_id 7). If both mags are invalid…'.
- **Should say:** Delete; power-cycle the one magnetometer via S2 device 0x0209 if needed (as the refusal message advises).
- **Evidence:** aocs_basic.py L3983 message 'power the one unit via S2 device 0x0209'.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/aocs_actuator_stuck_recovery.md`

#### E1-1.34 · CONFIRMED (M2 #8, scope new) · EOSAT-1 manual — 10_commissioning_contingency_procedures.md, line 25

- **File:** `/home/claude/work/smo/configs/eosat1/manual/10_commissioning_contingency_procedures.md` — L25
- **Says:** 36 procedure links in this chapter carry the wrong ID for the file they open, e.g. L25 `[CTG-014](…/no_telemetry_at_pass.md)`, L39 `[CTG-025](…/ttc_link_loss.md)`, L97 `[CTG-012](…/gs_antenna_failure.md)`, L171 `[CTG-026](…/undervoltage_loadshed.md)`, L331 `[CTG-010](…/eps_safe_mode.md)`, L449 `[EMG-001](…/total_power_failure.md)`, L463 `[EMG-002](…/loss_of_attitude.md)`, L537 `[CTG-023](…/star_tracker_failure.md)` … (full list: L25, 39, 53×2, 68, 81, 97, 111, 127, 141, 155, 171×2, 185, 199×2, 213, 243, 289, 303, 317×2, 331, 359×2, 405, 449, 463, 537, 551, 567×2, 581, 625, 669, 699).
- **Should say:** Relabel each link with the target file's own ID: no_telemetry_at_pass CTG-019, ttc_link_loss CTG-003, corrupted_image CTG-015, obc_bootloader_recovery CTG-021, battery_cell_failure CTG-013, gs_antenna_failure CTG-020, obc_redundancy_switchover CTG-011, memory_segment_failure CTG-016, undervoltage_loadshed CTG-001, progressive_load_shed CTG-023, bus_failure_isolation CTG-022, bus_failure_switchover CTG-017, thermal_exceedance CTG-004, overcurrent_response CTG-012, solar_array_degradation CTG-009, solar_panel_loss_response CTG-024, eps_safe_mode CTG-005, aocs_actuator_stuck_recovery CTG-026, reaction_wheel_anomaly CTG-007, aocs_sensor_loss_recovery CTG-025, total_power_failure EMG-002, loss_of_attitude EMG-005, star_tracker_failure CTG-008, ber_anomaly CTG-014, payload_anomaly CTG-006. Also fix in-text IDs (L55 'CTG-015', L201 'CTG-008', L291 'CTG-010').
- **Evidence:** Automated check: each link target's '# CTG-NNN:' heading in procedures/. The links resolve to the right file, but an operator who calls the card by the printed ID on the voice loop opens a different card. (M2 #8 noted that the numbering 'does not match' but not that every link is mislabelled.)
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/10_commissioning_contingency_procedures.md`

### Medium severity

#### E1-1.35 · CONFIRMED (M2 #24) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 253

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L253
- **Says:** `TIME_REPORT_REQUEST` (Service 9, Subtype 2); again at L274.
- **Should say:** `REQUEST_TIME` (S9.2).
- **Evidence:** tc_catalog.yaml S9: SET_TIME (9,1), REQUEST_TIME (9,2); no TIME_REPORT_REQUEST.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-1.36 · CONFIRMED (M2 #23) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 102

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L102
- **Says:** 'If sensor reads 3 (PARTIAL/JAMMED), escalate — see CON-015 contingency.'
- **Should say:** Cite an existing card: CTG-019 (No Telemetry at Pass Start) / the antenna-deploy branch of LEOP-001.
- **Evidence:** No CON-xxx family exists in procedures/ (ID map: CTG-001…028, EMG-001…006).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-1.37 · CONFIRMED (M2 #10) · EOSAT-1 manual — 10_commissioning_contingency_procedures.md, line 97

- **File:** `/home/claude/work/smo/configs/eosat1/manual/10_commissioning_contingency_procedures.md` — L97
- **Says:** On-board antenna deployment failure (L97/L111) is routed to `gs_antenna_failure.md`.
- **Should say:** Route to the on-board path (TTC_DEPLOY_ANTENNA retry / CTG-019); gs_antenna_failure.md (CTG-020) is the ground-station antenna card.
- **Evidence:** procedures/contingency/gs_antenna_failure.md title 'CTG-020: Ground Station Antenna Failure'.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/10_commissioning_contingency_procedures.md`

#### E1-1.38 · CONFIRMED (M2 #11) · EOSAT-1 manual — 10_commissioning_contingency_procedures.md, line 254

- **File:** `/home/claude/work/smo/configs/eosat1/manual/10_commissioning_contingency_procedures.md` — L254
- **Says:** Under 'Time Set': 'S9.2 command rejected or not acknowledged'.
- **Should say:** 'S9.1 (SET_TIME) command rejected …'.
- **Evidence:** tc_catalog.yaml: S9.1 = SET_TIME, S9.2 = REQUEST_TIME.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/10_commissioning_contingency_procedures.md`

#### E1-1.39 · CONFIRMED (M2 #32) · EOSAT-1 manual — software_architecture.md, line 363

- **File:** `/home/claude/work/smo/configs/eosat1/manual/software_architecture.md` — L363
- **Says:** 'S8 Function Dispatch' list L363–416 (0 = Mode DETUMBLE … 69 = Data Rate 4.8 kbps), the S19 example L704–713 (func 20 'Battery Heater OFF', 17 'Payload Power OFF', 19 'FPA Cooler OFF', 41 'Thermal Mode SURVIVAL', 1 'AOCS Mode SUN_SAFE') and the position ranges L841–851.
- **Should say:** Replace the list with a pointer to 09_command_reference.md (generated from tc_catalog.yaml) and fix the example funcs (e.g. 40 HEATER_BATTERY(on=0), 26 PAYLOAD_SET_MODE(0), 43 FPA_COOLER(0), 0 AOCS_SET_MODE(3)); positions from mcs/positions.yaml.
- **Evidence:** tc_catalog.yaml (0 AOCS_SET_MODE, 3 AOCS_ENABLE_WHEEL, 19/20 EPS_POWER_ON/OFF, 55 OBC_BOOT_APP, 69 TTC_DEPLOY_ANTENNA, 80 OBC_GPS_TIME_SYNC); positions.yaml aocs allowed_func_ids 0–15, 84–91, 96.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/software_architecture.md`

#### E1-1.40 · CONFIRMED (D1b #15, mnemonics only) · SMO docs — LINK_BUDGET_AND_RATES.md, line 492

- **File:** `/home/claude/work/smo/docs/LINK_BUDGET_AND_RATES.md` — L492
- **Says:** Recovery sequence: 'S8.1 func 19 EPS_POWER_LINE_ON' and 'S8.1 func 66 TTC_PA_ENABLE'.
- **Should say:** `EPS_POWER_ON(line_index=2)` (func 19, ttc_tx line) and `TTC_PA_ON` (func 66).
- **Evidence:** tc_catalog.yaml: func 19 = EPS_POWER_ON, 66 = TTC_PA_ON; the mnemonics used do not exist (func numbers are right). The D1b note's 'PUS reference: func 19 = EPS_CHARGE_RATE' is itself the stale PUS table (see above).
- **French mirror:** `/home/claude/work/smo/docs/fr/LINK_BUDGET_AND_RATES.md`

#### E1-1.41 · CONFIRMED (D1b #1) · SMO docs — PUS_SERVICE_REFERENCE.md, line 785

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L785
- **Says:** S13 transfer protocol table: 'Abort | 7 | TC → — | Cancel transfer'.
- **Should say:** Delete the Abort row (or replace with 'Status | 9 | TC → TM | S13_REPORT_STATUS'). The overview L44 (1, 3, 5, 9) is correct.
- **Evidence:** tc_catalog.yaml S13: 1 CREATE_TRANSFER, 3 DOWNLOAD_SEGMENT, 5 END_TRANSFER, 9 REPORT_STATUS; no subtype 7.
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-1.42 · CONFIRMED (D1b #5, #7) · SMO docs — PUS_SERVICE_REFERENCE.md, line 1194

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L1194
- **Says:** 'Common Error Codes' table: 0x0001 invalid format … 0x0003 'Command rejected (safety)', 0x0007 'Invalid parameter range', 0x0008 'Timeout'; example L1204–1214 uses 0x0003 for a mode-transition refusal.
- **Should say:** Copy FAILURE_CODES: 0x0001 generic/unknown service, 0x0002 unknown subtype, 0x0003 invalid parameter or data length, 0x0004 subsystem unpowered/unreachable, 0x0005 invalid in current mode, 0x0006 not permitted in bootloader, 0x0007 not permitted in current state (no 0x0008). Example → 0x0005 or 0x0007.
- **Evidence:** smo_common/protocol/pus_services.py FAILURE_CODES L33–41.
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-1.43 · CONFIRMED (new, extends D1b #8) · SMO docs — PUS_SERVICE_REFERENCE.md, line 513

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L513
- **Says:** TTC table: 72 `freq_mhz (2000-2100)`, 73 `freq_mhz (8400-8500)`, 74 `mode (0=BPSK, 1=QPSK)`; tier table L497 'HIGH … elevation >= 10 deg' and BEACON 0xFF.
- **Should say:** 72: 2025–2110 MHz; 73: 2200–2290 MHz (S-band); 74: add 2=8PSK…; HIGH has no on-board elevation gate (ground rule, MCS warning); tier 0xFF is SAFE (renamed from BEACON 2026-08c). Add funcs 97/98 TTC_BEACON_TX_ON/OFF and 80–120 to the overview range (L39 says 0–84, 100–107).
- **Evidence:** tc_catalog.yaml funcs 72–74, 65 description ('There is NO on-board elevation gate (2026-08c)'), 97/98, 108–120.
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-1.44 · CONFIRMED (new) · SMO docs — OPERATIONS_GUIDE.md, line 1663

- **File:** `/home/claude/work/smo/docs/OPERATIONS_GUIDE.md` — L1663
- **Says:** Pass 13 step 64: TTC_SET_DATA_RATE(rate=1) '… Requires elevation >= 10 deg'.
- **Should say:** '10° is a ground rule: the MCS warns below 10°; the spacecraft enforces only antenna-deployed + DOWNLINK mode + beacon-mode-off.'
- **Evidence:** tc_catalog.yaml TTC_SET_DATA_RATE: 'There is NO on-board elevation gate (2026-08c)'.
- **French mirror:** `/home/claude/work/smo/docs/fr/OPERATIONS_GUIDE.md`

#### E1-1.45 · CONFIRMED (D1a #12) · SMO docs — OBCP_GUIDE.md, line 192

- **File:** `/home/claude/work/smo/docs/OBCP_GUIDE.md` — L192
- **Says:** §6: the high rate is unreachable because `data_rate_mode` cannot be set by any telecommand.
- **Should say:** `TTC_SET_DATA_RATE` (func 65) sets data_rate_mode (the commanded tier); HIGH additionally needs DOWNLINK mode (func 79) and a deployed antenna.
- **Evidence:** tc_catalog.yaml TTC_SET_DATA_RATE: 'Sets data_rate_mode (the COMMANDED tier)'.
- **French mirror:** `/home/claude/work/smo/docs/fr/OBCP_GUIDE.md`

#### E1-1.46 · CONFIRMED (P3) · Procedure — nominal/orbit_manoeuvre_planning.md, line 62

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/orbit_manoeuvre_planning.md` — L62
- **Says:** All three time-tags use `exec_time_cuc=T` (L62, L64, L66) while the text says T−5 min (PROP_SET_BURN), T−2 min (PROP_ARM), T−0 (PROP_EXECUTE).
- **Should say:** `exec_time_cuc=T-300`, `exec_time_cuc=T-120`, `exec_time_cuc=T`.
- **Evidence:** As written all three would be scheduled for the same second.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/orbit_manoeuvre_planning.md`

#### E1-1.47 · CONFIRMED (P3) · Procedure — nominal/hk_configuration.md, line 26

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/hk_configuration.md` — L26
- **Says:** Steps L26–31 use `HK_ENABLE(sid=N)` (S3.5) to 'request … HK structure report'; L87–88 're-read config'; L120 `SAVE_CONFIG` 'if available'.
- **Should say:** S3.5 enables periodic reporting; for a one-shot read use `HK_REQUEST(sid=N)` (S3.27). Delete SAVE_CONFIG.
- **Evidence:** tc_catalog.yaml S3: 5 HK_ENABLE, 6 HK_DISABLE, 27 HK_REQUEST, 31 HK_SET_INTERVAL; no structure-report subtype and no SAVE_CONFIG.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/hk_configuration.md`

#### E1-1.48 · CONFIRMED (P2a #11) · Procedure — contingency/memory_segment_failure.md, line 50

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/memory_segment_failure.md` — L50
- **Says:** 'Each memory segment … ~250 MB (total 20,000 MB / 80 segments)'; L63 'Segment index ranges from 0 to 79'; thresholds L98/L122 '> 8 / > 16 segments'.
- **Should say:** 8 segments (index 0–7), 2.5 GB each for a 20 GB store; rescale the thresholds (e.g. > 1 / > 2 of 8).
- **Evidence:** subsystems/payload.yaml L50–52 'segment 0-79 documentation was never executable — valid range is 0-7', num_memory_segments: 8; tc_catalog PAYLOAD_MARK_BAD_SEGMENT segment 0–7. A segment_id > 7 is rejected.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/memory_segment_failure.md`

#### E1-1.49 · CONFIRMED (P1) · Procedure — commissioning/first_light.md, line 141

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/first_light.md` — L141
- **Says:** Off-nominal: `PAYLOAD_SET_INTEGRATION_TIME(blue=1.00, green=1.00, red=1.00, nir=1.00 ms)`.
- **Should say:** `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=1.00, green_ms=1.00, red_ms=1.00, nir_ms=1.00)`.
- **Evidence:** tc_catalog.yaml field names blue_ms/green_ms/red_ms/nir_ms; COM-011 L150 uses them.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/first_light.md`

#### E1-1.50 · CONFIRMED (P1) · Procedure — commissioning/first_light.md, line 57

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/first_light.md` — L57
- **Says:** COM-012 Step 3: `GET_PARAM(0x0604)` 'data interface status = READY', `GET_PARAM(0x0605)` 'storage free' (also L78); off-nominal L137 0x0603 'self-test'.
- **Should say:** 0x0604 = `payload.store_used` (%), 0x0605 = `payload.image_count`, 0x0603 = `payload.imager_temp`; rewrite the checks accordingly.
- **Evidence:** parameters.yaml 0x0603–0x0605. L74 of the same card already uses 0x0605 as image_count.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/first_light.md`

#### E1-1.51 · CONFIRMED (P1) · Procedure — commissioning/obdh_checkout.md, line 53

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/obdh_checkout.md` — L53
- **Says:** COM-007: L53 0x0311 'TC rejected counter'; L79 0x0306 'last reset cause'; L101 scrub via `SET_PARAM(0x0308, 1)`; L104 reset counter via `SET_PARAM(0x0311, 0)`.
- **Should say:** TC rejected counter = 0x0306 (`obdh.tc_rej_count`); last reboot cause = 0x0316; memory scrub = `OBC_MEMORY_SCRUB` (S8 func 51). Do not write 0x0311 (`obdh.sw_image`) or 0x0308 (`obdh.uptime`).
- **Evidence:** parameters.yaml 0x0306, 0x0308, 0x0311, 0x0316; tc_catalog.yaml func 51.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/obdh_checkout.md`

#### E1-1.52 · CONFIRMED (P1) · Procedure — commissioning/eps_checkout.md, line 41

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/eps_checkout.md` — L41
- **Says:** COM-001 Verify `eps.bat_voltage` (0x0100) in [14.4 V, 16.8 V]; L43 'Li-Ion 40Ah battery … 14.4V (empty) to 16.8V (full)'; L93 reads 'string currents' at 0x0112/0x0113.
- **Should say:** [21.5 V, 29.2 V] (8S, 100 Wh, 3 Ah; nominal 26.4 V). Per-wing currents are 0x0146/0x0147.
- **Evidence:** subsystems/eps.yaml battery: capacity_wh 100, soc_0_v 21.5, soc_100_v 29.2, voltage_nom 26.4; parameters.yaml 0x0112/0x0113 = pl_ttc_tx / pl_payload line flags, 0x0146/0x0147 wing currents. The Verify fails on every run.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/eps_checkout.md`

#### E1-1.53 · CONFIRMED (P1) · Procedure — leop/time_sync.md, line 53

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/leop/time_sync.md` — L53
- **Says:** LEOP-006 Step 1 hard Verify `obdh.mode == 0`, while the note says SAFE (1) is acceptable (prereq L39 also allows 0 or 1).
- **Should say:** Make the check `obdh.mode` in {0, 1} (or split into a soft check).
- **Evidence:** Runner Verify is a hard equality; a SAFE OBC fails the step the text says is acceptable.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/leop/time_sync.md`

#### E1-1.54 · CONFIRMED (P3) · Procedure — emergency/obc_reboot.md, line 129

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/emergency/obc_reboot.md` — L129
- **Says:** EMG-003: `HK_ENABLE(sid=5)` '— enable TTC periodic reporting'.
- **Should say:** `HK_ENABLE(sid=6)` for TT&C (SID 5 is Payload).
- **Evidence:** hk_structures.yaml: SID 5 Payload, SID 6 TTC.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/emergency/obc_reboot.md`

#### E1-1.55 · CONFIRMED (P2b) · Procedure — contingency/ttc_link_loss.md, line 50

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/ttc_link_loss.md` — L50
- **Says:** CTG-003 Step 5 'Verify Link Quality': `HK_REQUEST(sid=5)` then verifies ttc.link_status / ttc.rssi.
- **Should say:** `HK_REQUEST(sid=6)` (TTC).
- **Evidence:** hk_structures.yaml SID 6 = TTC.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/ttc_link_loss.md`

#### E1-1.56 · CONFIRMED (P2a #8) · Procedure — contingency/corrupted_image.md, line 82

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/corrupted_image.md` — L82
- **Says:** CTG-015 Step 3: `HK_REQUEST(sid=6)` to monitor FPA cooldown.
- **Should say:** `HK_REQUEST(sid=5)` (Payload; fpa_temp 0x0601) or sid=3 (TCS temp_fpa 0x0408).
- **Evidence:** hk_structures.yaml SID 6 = TTC.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/corrupted_image.md`

#### E1-1.57 · CONFIRMED (P2b) · Procedure — contingency/progressive_load_shed.md, line 196

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/progressive_load_shed.md` — L196
- **Says:** Two identical lines L196–197 `HK_REQUEST(sid=2)` — AOCS housekeeping.
- **Should say:** Second line `HK_REQUEST(sid=3)` (TCS), if TCS was intended; otherwise delete the duplicate.
- **Evidence:** Duplicate TC line.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/progressive_load_shed.md`

#### E1-1.58 · CONFIRMED (P3) · Procedure — emergency/emergency_safe_mode.md, line 148

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/emergency/emergency_safe_mode.md` — L148
- **Says:** 'attempt OBC reset via `HK_REQUEST(sid=3)` diagnostic'.
- **Should say:** `OBC_DIAGNOSTIC` (S8 func 61), then `OBC_REBOOT` (func 52) if FD authorises.
- **Evidence:** S3.27 sid=3 is a TCS HK request; it resets nothing.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/emergency/emergency_safe_mode.md`

#### E1-1.59 · CONFIRMED (P2b) · Procedure — contingency/thermal_exceedance.md, line 15

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/thermal_exceedance.md` — L15
- **Says:** CTG-004 prerequisite 'TCS telemetry (SID 4)'; Step 3 monitors temperatures with SID 1, Step 5 with SID 4; L63 on_temp and off_temp placeholders both '<current +5 C>'.
- **Should say:** TCS = SID 3 throughout; off_temp = on_temp + 5 °C (cf. the 5.0/10.0 example L64).
- **Evidence:** hk_structures.yaml SID 3 TCS, SID 4 Platform/OBDH; tcs.yaml thermostats 5/10 °C.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/thermal_exceedance.md`

#### E1-1.60 · CONFIRMED (P2b) · Procedure — contingency/payload_anomaly.md, line 16

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/payload_anomaly.md` — L16
- **Says:** CTG-006 prerequisites say payload TM is SID 6 and TCS SID 4, and the steps request SID 6/SID 4.
- **Should say:** Payload = SID 5, TCS = SID 3.
- **Evidence:** hk_structures.yaml.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/payload_anomaly.md`

#### E1-1.61 · CONFIRMED (P2a #1a,b) · Procedure — contingency/aocs_actuator_stuck_recovery.md, line 44

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/aocs_actuator_stuck_recovery.md` — L44
- **Says:** Telemetry table: 0x020B–0x020D = `aocs.mtq_x/y/z` 'Magnetorquer dipole'; L47 `aocs.mag_valid` 0x0230.
- **Should say:** 0x020B–0x020D = `aocs.mag_x/y/z` (measured field, as L126 says); magnetometer validity = `aocs.mag_enabled` 0x025C (0x0230 is `aocs.wheel_torque_cmd`).
- **Evidence:** parameters.yaml 0x020B–0x020D, 0x0230, 0x025C.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/aocs_actuator_stuck_recovery.md`

#### E1-1.62 · CONFIRMED (P1) · Procedure — commissioning/tcs_verification.md, line 111

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/tcs_verification.md` — L111
- **Says:** COM-002 off-nominal: 'Check if heater stuck ON via `GET_PARAM(param_id=0x0412)`'.
- **Should say:** `GET_PARAM(0x040B)` (`tcs.htr_obc`).
- **Evidence:** parameters.yaml 0x0412 = `tcs.temp_panel_px_ilm` (+X panel temperature); 0x040B = htr_obc.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/tcs_verification.md`

#### E1-1.63 · CONFIRMED (P1) · Procedure — leop/solar_array_verification.md, line 97

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/leop/solar_array_verification.md` — L97
- **Says:** LEOP-004 off-nominal: 'disable non-essential heaters via `HEATER_THRUSTER(on=0)`'.
- **Should say:** Name the intended circuit; the catbed heater is already OFF/manual in LEOP, so the realistic load cut is HEATER_OBC/payload lines — or delete.
- **Evidence:** tcs.yaml: thruster heater MANUAL by default (preheat is a NOM-013 step); func 42 is not in the LEOP load set.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/leop/solar_array_verification.md`

#### E1-1.64 · CONFIRMED (P2a #1c) · Procedure — contingency/aocs_actuator_stuck_recovery.md, line 82

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/aocs_actuator_stuck_recovery.md` — L82
- **Says:** 'escalate to CTG-005 Step 7 (multi-wheel failure)'; again L209.
- **Should say:** 'CTG-002 Step 7' (AOCS Anomaly Recovery, multi-wheel DETUMBLE).
- **Evidence:** procedures/contingency/eps_safe_mode.md = CTG-005 EPS Safe Mode; aocs_anomaly.md = CTG-002.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/aocs_actuator_stuck_recovery.md`

#### E1-1.65 · CONFIRMED (P2a #2) · Procedure — contingency/aocs_sensor_loss_recovery.md, line 26

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/aocs_sensor_loss_recovery.md` — L26
- **Says:** Prereqs L26 'CTG-005 (AOCS Anomaly Recovery)', L27 'CTG-009 (Star Tracker Failure)'; off-nominal L257–258 'recover using CTG-005 (AOCS Anomaly Recovery)'.
- **Should say:** CTG-002 (AOCS Anomaly Recovery); CTG-008 (Star Tracker Failure).
- **Evidence:** Procedure ID map (CTG-005 EPS Safe Mode, CTG-009 Solar Array Degradation).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/aocs_sensor_loss_recovery.md`

#### E1-1.66 · CONFIRMED (P2b) · Procedure — contingency/obc_bootloader_recovery.md, line 245

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/obc_bootloader_recovery.md` — L245
- **Says:** 'CTG-005 (AOCS Anomaly Recovery)'.
- **Should say:** CTG-002.
- **Evidence:** Procedure ID map.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/obc_bootloader_recovery.md`

#### E1-1.67 · CONFIRMED (P2b) · Procedure — contingency/solar_panel_loss_response.md, line 87

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/solar_panel_loss_response.md` — L87
- **Says:** L87–88 'CTG-005 (AOCS Anomaly Recovery)'; L181 'CTG-002 (Undervoltage Load Shed)'.
- **Should say:** CTG-002 (AOCS Anomaly Recovery); CTG-001 (Under-Voltage Load Shed).
- **Evidence:** Procedure ID map.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/solar_panel_loss_response.md`

#### E1-1.68 · CONFIRMED (P2b) · Procedure — contingency/progressive_load_shed.md, line 15

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/progressive_load_shed.md` — L15
- **Says:** 'CTG-002 (Undervoltage Load Shed)'.
- **Should say:** CTG-001 (Under-Voltage Load Shed).
- **Evidence:** Procedure ID map.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/progressive_load_shed.md`

#### E1-1.69 · CONFIRMED (P2a #12) · Procedure — contingency/no_telemetry_at_pass.md, line 185

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/no_telemetry_at_pass.md` — L185
- **Says:** 'CTG-010 (OBDH Watchdog Recovery) or CTG-010 as appropriate'.
- **Should say:** 'CTG-010 (OBDH Watchdog Recovery) or CTG-011 (OBC Redundancy Switchover)'.
- **Evidence:** Duplicate ID.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/no_telemetry_at_pass.md`

#### E1-1.70 · CONFIRMED (P2b) · Procedure — contingency/thermal_exceedance.md, line 77

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/thermal_exceedance.md` — L77
- **Says:** 're-enable per CTG-005 load restoration sequence'.
- **Should say:** 'per CTG-023 (Progressive Load Shed) recovery / LEOP-007 power-on order'.
- **Evidence:** CTG-005 is EPS Safe Mode.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/thermal_exceedance.md`

#### E1-1.71 · CONFIRMED (P2b) · Procedure — contingency/ttc_link_loss.md, line 71

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/ttc_link_loss.md` — L71
- **Says:** 'If OBC is found in SAFE mode … Execute CTG-005 or CTG-010'.
- **Should say:** 'CTG-010 (OBDH Watchdog Recovery)' (CTG-005 is EPS safe mode).
- **Evidence:** Procedure ID map.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/ttc_link_loss.md`

#### E1-1.72 · CONFIRMED (P2b) · Procedure — contingency/propulsion_anomaly.md, line 73

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/propulsion_anomaly.md` — L73
- **Says:** 'GO CTG-004 (Thermal Runaway response)'.
- **Should say:** 'CTG-004 (Thermal Exceedance)', or EMG-006 (Thermal Runaway) if a runaway is meant.
- **Evidence:** Procedure ID map: CTG-004 Thermal Exceedance, EMG-006 Thermal Runaway.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/propulsion_anomaly.md`

#### E1-1.73 · CONFIRMED (P3) · Procedure — nominal/routine_health_check.md, line 52

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/routine_health_check.md` — L52
- **Says:** Momentum check: 'insufficient desaturation — schedule NOM-005'.
- **Should say:** 'schedule NOM-007 (Momentum Management)'.
- **Evidence:** NOM-005 = HK Configuration.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/routine_health_check.md`

#### E1-1.74 · CONFIRMED (P2a #10) · Procedure — contingency/gps_time_sync_recovery.md, line 107

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/gps_time_sync_recovery.md` — L107
- **Says:** 'Follow the commissioning state machine defined in LEOP-004'.
- **Should say:** COM-005 (AOCS Mode Transitions) / COM-013 — LEOP-004 is Solar Array Verification.
- **Evidence:** Procedure ID map.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/gps_time_sync_recovery.md`

#### E1-1.75 · CONFIRMED (P1) · Procedure — commissioning/fpa_cooler_activation.md, line 154

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/fpa_cooler_activation.md` — L154
- **Says:** COM-010 Step 9 GO: 'ready for COM-012'; NEXT (L193) is COM-011.
- **Should say:** 'ready for COM-011 (Payload Calibration)'.
- **Evidence:** Card's own NEXT line.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/fpa_cooler_activation.md`

#### E1-1.76 · CONFIRMED (O1 #8) · ORBIT NORTH operations book, line 966

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L966
- **Says:** AOCS position authority: '`allowed_func_ids` 0–15 plus 84'; L2201 'Flight Dynamics console, func 84 only'.
- **Should say:** '0–15, 84–91 and 96' (as §7.x heading L2171 says).
- **Evidence:** mcs/positions.yaml aocs allowed_func_ids [0–15, 84–91, 96]. Students told 86/87/91/96 are not theirs will route them to FD needlessly.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.77 · CONFIRMED (M2 #13) · EOSAT-1 manual — 10_desk_procedures.md, line 351

- **File:** `/home/claude/work/smo/configs/eosat1/manual/10_desk_procedures.md` — L351
- **Says:** Escalation table L351–356: 'CON-019 (Load Shed) → EMG-001 Total Power Failure', 'CON-004 (Link Loss)', 'CON-001 (AOCS Anomaly)', 'CON-006 (Thermal) → EMG-002 Thermal Runaway', 'CON-005 (OBC Watchdog)', 'PROC-OBC-OFF-003'.
- **Should say:** CTG-001/CTG-023 → EMG-002 Total Power Failure; CTG-003 → EMG-004; CTG-002 → EMG-005; CTG-004 → EMG-006 Thermal Runaway; CTG-010 → EMG-003; CTG-011 → EMG-003.
- **Evidence:** procedures/emergency/*.md headings (EMG-002 Total Power Failure, EMG-006 Thermal Runaway); no CON-xxx or PROC-OBC-OFF-xxx procedures exist.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/10_desk_procedures.md`

#### E1-1.78 · CONFIRMED (W2) · Week 3 pack — sim_commissioning_instructor.md, line 65

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/sim_commissioning_instructor.md` — L65
- **Says:** COM-008 'load nominal table' / 'FDIR nominal table loaded' (also L107; sim_leop_instructor.md L73, L127; breakpoint_spec.md L151, L172).
- **Should say:** 'COM-008: enable S12 monitoring (MON_ENABLE) and the S19 event-actions (EA_ENABLE); verify the FDIR rule set' — there is no table-load TC.
- **Evidence:** tc_catalog.yaml: no FDIR table-load mnemonic (S12 MON_*, S19 EA_* only); the workbook and instructor book already say so.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/sim_commissioning_instructor.md` (not yet installed; staged at `/home/claude/work/xlate/W2/sim_commissioning_instructor/fr.md`)

#### E1-1.79 · NOT CONFIRMED as an error (reference resolves); duplication flagged in §3 · Procedure — contingency/obc_redundancy_switchover.md, line 150

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/obc_redundancy_switchover.md` — L150
- **Says:** 'Follow CTG-018 (Boot Loader Recovery) for memory check and recovery.'
- **Should say:** Either is a valid file (CTG-018 boot_loader_recovery.md and CTG-021 obc_bootloader_recovery.md are near-duplicates). Pick one canonical bootloader card and cite it everywhere (P2b and the ops book cite CTG-021).
- **Evidence:** procedures/contingency/boot_loader_recovery.md (CTG-018) and obc_bootloader_recovery.md (CTG-021) both exist.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/obc_redundancy_switchover.md`

#### E1-1.80 · NOT CONFIRMED (text is correct) · ORBIT NORTH operations book, line 9007

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L9007
- **Says:** Ops book §14.6 correctly warns that NOM-008 is Clock Synchronisation — listed here only because the ID audit hit it.
- **Should say:** No change.
- **Evidence:** procedures/nominal/clock_sync.md = NOM-008.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

### Low severity

#### E1-1.81 · CONFIRMED (O1 #13) · ORBIT NORTH operations book, line 2443

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L2443
- **Says:** Legacy-name table: '`EPS_POWER_ON(line=3)` (19)'.
- **Should say:** `EPS_POWER_ON(line_index=3)`.
- **Evidence:** tc_catalog.yaml field name line_index; §6.4 L1344 uses line_index.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.82 · CONFIRMED (O1 #14) · ORBIT NORTH operations book, line 1978

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L1978
- **Says:** Voice-loop example: 'AOCS, beginning STAR_TRACKER_ENABLE'.
- **Should say:** 'AOCS, beginning ST1_POWER' (or ST2_POWER).
- **Evidence:** §7.7 (L2437) itself lists STAR_TRACKER_ENABLE as a non-existent legacy name; not in tc_catalog.yaml.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.83 · CONFIRMED (P2a #5) · Procedure — contingency/ber_anomaly.md, line 102

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/ber_anomaly.md` — L102
- **Says:** Two consecutive `TTC_SET_DATA_RATE(rate=0)` lines (L102–103).
- **Should say:** Delete the second line.
- **Evidence:** Duplicate TC (harmless but the runner sends it twice).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/ber_anomaly.md`

#### E1-1.84 · NOT CONFIRMED as a book error (O4b #3); simulator/event-catalogue mismatch → §3 · ORBIT NORTH operations book, line 8775

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L8775
- **Says:** CTG-027 card step 4: 'Auto-transition (event 0x020F) on a jump > 5 s'.
- **Should say:** No book change needed: the simulator really emits event 0x020F here (service_dispatch.py L2003–2008, 'AOCS forced to SAFE_BOOT: GPS time sync jump'). The defect is in the tree: events/event_catalog.yaml names 0x020F AOCS_MODE_RESTORED, and the mode change itself is 0x0200 AOCS_MODE_CHANGE.
- **Evidence:** service_dispatch.py L2000–2008 vs event_catalog.yaml L43/L58.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.85 · NOT CONFIRMED (O4a #3) · ORBIT NORTH operations book, line 7364

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L7364
- **Says:** COM-010 note: '`PAYLOAD_COOLER_SETPOINT(setpoint=-15)` … the argument is a uint16 in centi-kelvin — −15.00 °C encodes as 25815'.
- **Should say:** No change.
- **Evidence:** tc_catalog.yaml: field `setpoint` unit degC, raw_unit cK, calibration scale 0.01 offset −273.15, so the engineering value −15 and raw 25815 are the same command.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-1.86 · NOT CONFIRMED (O4b #5, false positive) · ORBIT NORTH operations book, line 8399

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L8399
- **Says:** CTG-016 step 6 `EPS_POWER_OFF(line_index=3)` / `EPS_POWER_ON(line_index=3)` (func_id 20 / 19).
- **Should say:** No change.
- **Evidence:** tc_catalog.yaml: 20 = EPS_POWER_OFF, 19 = EPS_POWER_ON.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

## Section 2 — Numerical and calculation errors

### High severity

#### E1-2.01 · CONFIRMED (F1, OER1 #4; sensitivity new) · Facilitator book (SpaceCDF course textbook), line 2329

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L2329
- **Says:** Table 1.4.21 UniSat-1 weighted totals 0.90 / 0.63 / 0.41; sensitivity check (L2333) 'cost 0.15, schedule 0.15, rest to data return → 0.82 vs 0.68 vs 0.51'.
- **Should say:** Totals 0.91 / 0.665 / 0.495 (the OER ch. 4 §4.9 already prints 0.91 / 0.67 / 0.50). Sensitivity: 0.76 / 0.715 / 0.725 — 1U still wins, but 3U overtakes 2U, so rewrite the sentence.
- **Evidence:** Σw·s with w = (0.35, 0.25, 0.20, 0.10, 0.10): 1U 0.910, 2U 0.665, 3U 0.495. Sensitivity w = (0.15, 0.15, 0.20, 0.10, 0.40): 0.760 / 0.715 / 0.725. The sensitivity error is new (F1 only flagged it as 'unverified').
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.02 · CONFIRMED (F4) · Facilitator book (SpaceCDF course textbook), line 8897

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L8897
- **Says:** Table 4.4.5 cost of 10th unit: 95 % → 77 %, 90 % → 60 %, 85 % → 47 %.
- **Should say:** 84 %, 70 %, 58 % (10^b with b = log2(LR)).
- **Evidence:** 10^−0.074 = 0.843; 10^−0.152 = 0.705; 10^−0.234 = 0.583.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.03 · CONFIRMED (F4; 10-unit row new) · Facilitator book (SpaceCDF course textbook), line 8928

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L8928
- **Says:** Table 4.4.6: 5 units avg EUR 659K, total EUR 3,295K ('5 x 800 x 5^(-0.152)'); 10 units avg 577K, total 5,770K.
- **Should say:** 5 units: avg 626K, total 3,132K. 10 units: avg 564K, total 5,638K (Wright cumulative-average form, as the Calc column states).
- **Evidence:** 800·5^−0.152 = 626.4; ×5 = 3132.0. 800·10^−0.152 = 563.8; ×10 = 5637.5.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.04 · CONFIRMED (F4) · Facilitator book (SpaceCDF course textbook), line 7671

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L7671
- **Says:** Iridium trade (Table 3.4.13 position, ch. 4.1): weighted Candidate A 3.95, Candidate B 4.00.
- **Should say:** A 4.00, B 4.025 — B still wins, by 0.025 instead of 0.05.
- **Evidence:** A: 0.3·4.5+0.2·3.5+0.2·3+0.15·5+0.15·4 = 4.000; B: 0.3·4+0.2·4+0.2·4.5+0.15·4+0.15·3.5 = 4.025.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.05 · CONFIRMED (F4) · Facilitator book (SpaceCDF course textbook), line 8587

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L8587
- **Says:** 'R_system = 4 x R^4 - 3 x R^3'.
- **Should say:** 'R_system = 4R³ − 3R⁴' (the binomial line below is right).
- **Evidence:** R = 0.98: binomial 0.99766 = 4R³−3R⁴; 4R⁴−3R³ = 0.8659.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

### Medium severity

#### E1-2.06 · CONFIRMED (F4, OER4) · Facilitator book (SpaceCDF course textbook), line 8830

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L8830
- **Says:** Standard WBS Level-1 percentages (5+5+3+20+30+12+8+10+5+5).
- **Should say:** Make them sum to 100 % (e.g. Mission Assurance 3 → 0 is wrong; more naturally I&T 12 → 10 and Ops 5 → 4). Same block in OER ch. 16 §16.2.1 L127–156.
- **Evidence:** Sum = 103 %.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.07 · CONFIRMED (F4, OER4) · Facilitator book (SpaceCDF course textbook), line 8996

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L8996
- **Says:** UniSat-1 WBS: row 5.0 = 38 (parametric) / 36 (bottom-up); TOTAL ≈ 90 / ≈ 85.
- **Should say:** Sub-rows 5.1–5.5 sum to 39 / 38, so 5.0 = 39 / 38; totals then 91 / 91 (as printed rows give 90 / 89). Same table in OER ch. 16 §16.4.3 L287–303 (and the '≈ 85 kEUR' at L281/L317).
- **Evidence:** 4+20+1+11+3 = 39; 4+19.5+1+10.5+3 = 38; Σ rows parametric = 90, bottom-up = 89.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.08 · CONFIRMED (F5) · Facilitator book (SpaceCDF course textbook), line 10457

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L10457
- **Says:** Appendix C sanity check: T = 2π√(6828.137³/398600.4418) = 2π × 894.8 = 5621 s = 93.7 min; then 'agreement to ~1 %' with 15.24 rev/day (94.5 min).
- **Should say:** √ = 893.7, T = 5615 s = 93.6 min. 15.24 rev/day ⇒ a = 6872 km, h ≈ 494 km; EOSAT-1 is a 513 km orbit (orbit.yaml) — use h = 513 km or drop the '~1 % / solar day' explanation.
- **Evidence:** Python: √(6828.137³/μ) = 893.68; T = 5615.2 s. a from n = 15.24 rev/day = 6871.9 km. orbit.yaml altitude_km 513.0.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.09 · CONFIRMED (F5, OER5) · Facilitator book (SpaceCDF course textbook), line 10489

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L10489
- **Says:** Hohmann sanity check: v_p = 10.061, ΔV₁ = 2.392, v_a = 1.610, ΔV₂ = 1.465, total 3.857 km/s 'matches 3.854 within rounding'. Identical text in OER ch. 22 §V.3 L82–86.
- **Should say:** v_p = 10.066, ΔV₁ = 2.398, v_a = 1.618, ΔV₂ = 1.457, total 3.854 km/s.
- **Evidence:** μ = 398600, r₁ = 6778, r₂ = 42164: v_p 10.0661, v_a 1.6182, ΔV₁ 2.3975, ΔV₂ 1.4565, Σ 3.8540.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.10 · CONFIRMED (F5) · Facilitator book (SpaceCDF course textbook), line 10739

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L10739
- **Says:** Fig. C.9 caption: white paint ≈ −20 °C; worked check gets 234 K = −39 °C and says 'Matches our plot'.
- **Should say:** Either fix the figure/caption (≈ −39 °C for α/ε = 0.16 with the stated fluxes) or the inputs; remove 'matches'.
- **Evidence:** (157/(0.92·5.67e−8))^¼ = 234.2 K = −38.9 °C.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.11 · CONFIRMED (requirement); 113.6 PLAUSIBLY wrong (F5) · Facilitator book (SpaceCDF course textbook), line 10626

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L10626
- **Says:** Fig. C.6: C/N₀ = 113.6 dB·Hz against a 50 dB·Hz requirement for 1 Mbps.
- **Should say:** A 1 Mbps link needs ≥ 60 dB·Hz + required Eb/N₀ (≈ 70 dB·Hz); recompute C/N₀ (ch. 11 Fig. 11.5 gives 83.4 dB·Hz for the same downlink).
- **Evidence:** 10·log10(10⁶) = 60.0 dB·Hz before Eb/N₀. The 113.6 dB·Hz figure itself not recomputed (figure inputs not in text).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.12 · CONFIRMED (F5) · Facilitator book (SpaceCDF course textbook), line 10825

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L10825
- **Says:** T_drag ≈ 1.1 × 10⁻⁷ N·m 'matching the order-of-magnitude in Figure AC.2'; AC.2 / C.12 captions give ~1 µN·m.
- **Should say:** Keep 1.1 × 10⁻⁷ N·m and fix the figure captions, or drop 'matching'.
- **Evidence:** 0.5·6e−13·7610²·2.2·0.06·0.05 = 1.15 × 10⁻⁷ N·m (calc correct; captions 10× larger).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.13 · CONFIRMED (F3) · Facilitator book (SpaceCDF course textbook), line 6713

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L6713
- **Says:** 'atmospheric loss 0.5 × cosec(5°)-scaled = 2.87 dB'; L1783 'G/T de-rate coming off 1.0 dB'.
- **Should say:** '0.25 dB × cosec(5°) = 2.87 dB' (or keep 0.5 and use 5.74 dB). In L1783 the G/T de-rate is 1.5 dB (L1763), so 5°→10° buys ≈ 4.8 dB, not 4.3.
- **Evidence:** 0.5/sin5° = 5.74; 0.25/sin5° = 2.87; 0.25/sin10° = 1.44 (the 1.43 dB in L1783 confirms the 0.25 factor); 1.85+1.43+1.5 = 4.78.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.14 · CONFIRMED (F3) · Facilitator book (SpaceCDF course textbook), line 6854

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L6854
- **Says:** Summary table: '3 m dish: 35 dBi at S-band, 25 dBi at X-band'.
- **Should say:** '~34 dBi at S-band, ~46 dBi at X-band' (25.8 dBi is the 30 cm dish of the earlier table).
- **Evidence:** G = 0.55(πD/λ)²: D = 3 m → 34.4 dBi at 2.25 GHz, 45.8 dBi at 8.4 GHz.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.15 · CONFIRMED (F2) · Facilitator book (SpaceCDF course textbook), line 4266

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4266
- **Says:** Battery volume '2 × 18 mm × 65 mm = approximately 34 mL'.
- **Should say:** '2 × π × (9 mm)² × 65 mm ≈ 33 mL' (or a 36 × 18 × 65 mm envelope = 42 mL).
- **Evidence:** 2·π·9²·65 mm³ = 33.1 mL; the printed expression is an area.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.16 · CONFIRMED (F2) · Facilitator book (SpaceCDF course textbook), line 4623

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4623
- **Says:** 'Starting at T₀ = +15 degC (293 K)'.
- **Should say:** '+15 °C (288 K)' — or +20 °C (293 K).
- **Evidence:** 15 + 273.15 = 288.15 K.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.17 · CONFIRMED (O1 #17) · ORBIT NORTH operations book, line 2650

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L2650
- **Says:** Table 7.18 daily volumes at 2 Mbps × 0.9: 69 N 544–726 MB, ISS 130–260 MB, SatNOGS 648–972 MB (52 N row 243–405 is right).
- **Should say:** 69 N 567–756 MB; ISS 135–270 MB; SatNOGS 675–1013 MB.
- **Evidence:** passes × min × 60 × 2e6 × 0.9 / 8: 6·7 → 567, 8·7 → 756; 2·5 → 135, 4·5 → 270; 10·5 → 675, 15·5 → 1013.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.18 · CONFIRMED (O3) · ORBIT NORTH operations book, line 5780

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L5780
- **Says:** 'at 100.7 MB an image would need about 4.4 hours of effective contact' (also L6588).
- **Should say:** '≈ 1.75 h at HIGH (128 kbit/s), ≈ 2.2 h with the 20 % protocol allowance' — still several passes, so the argument stands.
- **Evidence:** 100.7e6·8/128e3 = 6294 s = 1.75 h; 4.4 h corresponds to ~51 kbit/s.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.19 · CONFIRMED (O3) · ORBIT NORTH operations book, line 5497

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L5497
- **Says:** COM-009 voice-loop: '2.5 watt-hours — under a third of a percent of the 100 watt-hour pack'.
- **Should say:** '2.5 percent of the 100 watt-hour pack'.
- **Evidence:** 2.5/100 = 2.5 %.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.20 · CONFIRMED (O3) · ORBIT NORTH operations book, line 5630

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L5630
- **Says:** Cooler: 'about 23 % of Carnot … 27 K lift … 22.5 W of parasitic heat on 15 W of input — a COP of 1.50'.
- **Should say:** Make the two consistent: 23 % of Carnot at 258 K / 27 K gives COP ≈ 2.2 (33 W lift on 15 W); a COP of 1.50 is ≈ 16 % of Carnot.
- **Evidence:** 0.23 × 258.15/27 = 2.20; 22.5/15 = 1.50.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.21 · CONFIRMED in part (OER3 #2) · OER *Concurrent Spacecraft Design* — 12_structures_propulsion_obdh.md, line 376

- **File:** `/home/claude/work/cdf/docs/oer/chapters/12_structures_propulsion_obdh.md` — L376
- **Says:** §12.2.5 table: propellant for 100 m/s on 5 kg: cold gas 0.87, butane 0.44, green monoprop 0.18 kg; worked example (L392) uses 5.0 kg as DRY mass (1.05 kg for 112 m/s at 60 s).
- **Should say:** Use one mass convention (worked example: m_prop = m_dry(e^{Δv/g₀I_sp} − 1)) and recompute: at 5 kg dry, cold gas 60 s → 0.93 kg; butane 80–100 s → 0.68–0.54 kg; green 230–250 s → 0.22–0.21 kg.
- **Evidence:** Implied I_sp (5 kg wet): cold 53 s (inside 40–75, OK), butane 111 s (> 80–100), green 278 s (> 230–250). OER3 note's 'cold gas implies 64 s' is wrong; butane/green confirmed.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/12_structures_propulsion_obdh.md`

#### E1-2.22 · CONFIRMED (D1b #12) · SMO docs — LINK_BUDGET_AND_RATES.md, line 697

- **File:** `/home/claude/work/smo/docs/LINK_BUDGET_AND_RATES.md` — L697
- **Says:** UHF-vs-S-band itemisation +14.03, +0.69, −3.0, −2.7, −28.0 with 'Net −28.0 dB' (text: '27.9 dB difference').
- **Should say:** Itemised terms sum to −19.0 dB; add the missing ~−9 dB term(s) (PA power and coding/rate differences) or correct the net.
- **Evidence:** 14.03 + 0.69 − 3.0 − 2.7 − 28.0 = −18.98 dB.
- **French mirror:** `/home/claude/work/smo/docs/fr/LINK_BUDGET_AND_RATES.md`

### Low severity

#### E1-2.23 · PLAUSIBLE (F3) — needs author check · Facilitator book (SpaceCDF course textbook), line 6752

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L6752
- **Says:** Beacon budget 'closes … with about 27 dB' from the listed deltas against 46 dB for LOW.
- **Should say:** Itemise all terms: listed deltas give 46 + 14.0 + 0.3 − 28.0 − 3.0 − 2.7 = 26.6 dB only if the rate (+12.0 dB, 16→1 kbps) and PA (−3.0 dB, 2→1 W) terms cancel against an unstated coding loss (~−9 dB). State them.
- **Evidence:** Arithmetic of the stated terms alone = 26.6 dB, but two stated differences (rate, PA power) are not applied.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.24 · CONFIRMED (F2) · Facilitator book (SpaceCDF course textbook), line 4790

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4790
- **Says:** '12 W reaches the 180 °C … in about 18 min: 12 W × 20 min = 4.0 Wh'.
- **Should say:** Use one duration: 12 W × 18 min = 3.6 Wh, or 'about 20 min … 4.0 Wh'.
- **Evidence:** 12·18/60 = 3.6 Wh.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.25 · CONFIRMED (F2) · Facilitator book (SpaceCDF course textbook), line 4237

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4237
- **Says:** Battery cycle-life table column 'Annual Eclipses (LEO, 15/day)' lists 450 / 1,800 / 5,475 / 10,950 / 38,325.
- **Should say:** Header 'Eclipses over the mission duration (15/day)'.
- **Evidence:** 15/day × 30 d = 450, × 120 d = 1800, × 1 y = 5475, × 2 y = 10950, × 7 y = 38325 — mission totals, not annual.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-2.26 · CONFIRMED (O3) · ORBIT NORTH operations book, line 6244

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L6244
- **Says:** 'roughly 23 300 seconds of contact per day, about 26.6 % of the clock'.
- **Should say:** 'about 27.0 %' (or '≈ 23 000 s, 26.6 %' = 51.5 × 447 s).
- **Evidence:** 23300/86400 = 26.97 %; 51.5 × 447 = 23 020 s.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.27 · CONFIRMED (O3, negligible) · ORBIT NORTH operations book, line 6216

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L6216
- **Says:** 'arccos(0.93403) = 20.87° = 0.36427 rad … t = 657 s'; formula (L1644) uses R_E + h_station, example uses R_E; example h = 450 km.
- **Should say:** '20.93° = 0.3653 rad … t ≈ 659 s'. Consider h = 513 km (EOSAT-1 baseline).
- **Evidence:** acos(0.93403) = 0.36526 rad = 20.928°; 5669/π × 0.36526 = 659.1 s.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.28 · CONFIRMED (O3; factor unstated) · ORBIT NORTH operations book, line 6566

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L6566
- **Says:** '~227 MiB/day if every usable contact second ran at HIGH, ~28 MiB/day … at LOW'.
- **Should say:** State the usable fraction: 23 300 s × 128 kbit/s = 355 MiB raw (44 MiB at LOW); 227/355 = 64 % implies an unstated ~36 % deduction.
- **Evidence:** 23300·128e3/8/2²⁰ = 355.5 MiB; ·16e3 → 44.4 MiB.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.29 · CONFIRMED (O3) · ORBIT NORTH operations book, line 4928

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L4928
- **Says:** 'generation rises to 45.0 W and the nominal case closes at 1.55×'.
- **Should say:** '1.57×'.
- **Evidence:** 45.0/28.7 = 1.568 (table row nominal load 28.7 W).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-2.30 · CONFIRMED (W1) · Learner workbook, line 2430

- **File:** Drive `SpaceCDF/docs/course/learner_workbook_expanded.md` (local copy `/home/claude/work/drive_course/learner_workbook_expanded.md`) — L2430
- **Says:** 'With 4 passes/day: ~0.84 MB/day'.
- **Should say:** '~0.86 MB/day'.
- **Evidence:** 4 × 214.2 kB = 856.8 kB (4800 × 420 × 0.85 = 1.714 Mbit = 214.2 kB).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/learner_workbook_expanded.md` (local build `/home/claude/work/out/course_fr/learner_workbook_expanded.md`)

#### E1-2.31 · CONFIRMED (OER3 #3) · OER *Concurrent Spacecraft Design* — 12_structures_propulsion_obdh.md, line 620

- **File:** `/home/claude/work/cdf/docs/oer/chapters/12_structures_propulsion_obdh.md` — L620
- **Says:** 'lifetime of roughly 6–14 months … at solar minimum the lifetime extends towards 18 months'.
- **Should say:** '6–18 months' (or 8–14 with ~6 / ~18 extremes, as the facilitator book TM had).
- **Evidence:** Range and extreme disagree within one sentence.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/12_structures_propulsion_obdh.md`

#### E1-2.32 · CONFIRMED (OER4) · OER *Concurrent Spacecraft Design* — 16_cost_and_reviews.md, line 440

- **File:** `/home/claude/work/cdf/docs/oer/chapters/16_cost_and_reviews.md` — L440
- **Says:** Problem 3: '30-month schedule (Phase 0/A 4 months, B 6, C 8, D 8 …)'.
- **Should say:** '26-month schedule' or adjust the phase durations.
- **Evidence:** 4 + 6 + 8 + 8 = 26.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/16_cost_and_reviews.md`

#### E1-2.33 · CONFIRMED (D1b #2) · SMO docs — PUS_SERVICE_REFERENCE.md, line 807

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L807
- **Says:** 'Result: 2 MB image downloaded in ~10 seconds over 1 Mbps link' (total_bytes = 2097152).
- **Should say:** '… in ~131 s at HIGH (128 kbit/s)'. No 1 Mbps rung exists.
- **Evidence:** 2 097 152 × 8 / 128 000 = 131 s (16.8 s even at 1 Mbps).
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-2.34 · CONFIRMED (M1) · EOSAT-1 manual — 07_orbit_ops.md, line 45

- **File:** `/home/claude/work/smo/configs/eosat1/manual/07_orbit_ops.md` — L45
- **Says:** §2.2 'Adjacent ground tracks at the equator are separated by approximately 170 km.'
- **Should say:** 'Successive tracks are ~2 630 km apart at the equator; the 5-day repeat grid spacing is ~525 km.'
- **Evidence:** 40 075 km / 15.24 rev/day = 2 630 km; /(5 × 15.24) = 526 km.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/07_orbit_ops.md`

#### E1-2.35 · CONFIRMED (M2 #30) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 355

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L355
- **Says:** `power_cons` ~51 W (OBC ~15 W + RX ~5 W + TX ~12 W + heaters ~9 W + wheels ~12 W).
- **Should say:** ~53 W (or fix an item — eps.yaml obc_power_w is now 6 W, so OBC ~15 W is itself stale).
- **Evidence:** 15+5+12+9+12 = 53; eps.yaml obc_power_w: 6.0.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-2.36 · NOT CONFIRMED (O2) · ORBIT NORTH operations book, line 4445

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L4445
- **Says:** 'Step 2 inrush is 1.2 A (1.5× nominal)'.
- **Should say:** No change unless the author meant htr_bat: the decision point refers to LEOP-007 step 2, not the htr_bat 0.35 A example 160 lines earlier; 1.5× implies a 0.8 A nominal line.
- **Evidence:** Context L4363–4446: the 0.35 A figure is the htr_bat playbook example, not 'step 2'.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

## Section 3 — Inconsistencies between documents (and with the simulator)

### High severity

#### E1-3.01 · CONFIRMED (M1, D1a #3) · EOSAT-1 manual — 00_mission_overview.md, line 257

- **File:** `/home/claude/work/smo/configs/eosat1/manual/00_mission_overview.md` — L257
- **Says:** Non-existent AOCS mode names SAFE_POINT / NADIR_POINT / TARGET_TRACK across the manual: 00 L257/L263/L267, 01 L387, 03 L83, 04 L169, 06 L134/L208, 07 L223, 08 L50/L78/L144/L248 (and 09_leop §8, see §1). Same in INSTRUCTOR_GUIDE.md L264.
- **Should say:** COARSE_SUN (3) for the safe hold, NOMINAL (4) for nadir, FINE_POINT (5) for imaging; TARGET_TRACK is a pointing frame (AOCS_SET_POINTING_FRAME func 85), not a mode.
- **Evidence:** aocs/aocs_mode_codes.yaml (canonical); 02_aocs.md §3 table.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/00_mission_overview.md`

#### E1-3.02 · CONFIRMED (O4b #2, M1, M2 #33, P2a #2) · EOSAT-1 manual — 00_mission_overview.md, line 55

- **File:** `/home/claude/work/smo/configs/eosat1/manual/00_mission_overview.md` — L55
- **Says:** Dual magnetometers A/B with cold redundancy: manual 00 L55/L93; software_architecture.md L479 '2× redundant'; ops book CTG-025 L8680 'two magnetometers (MAG-A/MAG-B)', L8687 'Both magnetometers lost', EMG card L9076 'Magnetometers both invalid' (O4b L990), L4436 'switching both magnetometers off'; instructor book L145 scenario 'MAG-A fails'; procedures aocs_sensor_loss_recovery.md purpose L10–11, L235 'MAG-B', L249/L252 'both magnetometers'.
- **Should say:** One magnetometer (single string); a magnetometer loss ends B-dot and magnetic desaturation.
- **Evidence:** tc_catalog.yaml L546 (2026-08c item 8); parameters.yaml 0x0223–0x0229 RETIRED; 02_aocs.md §2.1.1 and adcs_commissioning.md L10 already single-string.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/00_mission_overview.md`

#### E1-3.03 · CONFIRMED (M1) · EOSAT-1 manual — 02_aocs.md, line 16

- **File:** `/home/claude/work/smo/configs/eosat1/manual/02_aocs.md` — L16
- **Says:** 'EOSAT-1 has no propulsion system' (02 L16, 03 L64–68, 07 §5–6).
- **Should say:** EOSAT-1 carries a green-monopropellant system (PROP_* funcs 108–118, catbed heater, prop interlock at phase 6).
- **Evidence:** subsystems/prop.yaml; tc_catalog.yaml funcs 108–118; parameters 0x0409 temp_thruster; 00 §6.0 and 01 PDM line 8 already describe it.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/02_aocs.md`

#### E1-3.04 · CONFIRMED (M1) · EOSAT-1 manual — 03_tcs.md, line 64

- **File:** `/home/claude/work/smo/configs/eosat1/manual/03_tcs.md` — L64
- **Says:** 03 §3.1 note: 'EOSAT-1 does not carry OBC or thruster heater' circuits (L64–68).
- **Should say:** Both exist. OBC heater: HEATER_OBC (func 41), tcs.htr_obc 0x040B (listed in the same chapter, L139), thermostat 5/10 °C, PDM line 6; thruster catbed heater HEATER_THRUSTER (func 42), 0x041B.
- **Evidence:** tcs.yaml heater 'obc' on 5.0 / off 10.0 °C; parameters 0x040B.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/03_tcs.md`

#### E1-3.05 · CONFIRMED (M1) · EOSAT-1 manual — 00_mission_overview.md, line 114

- **File:** `/home/claude/work/smo/configs/eosat1/manual/00_mission_overview.md` — L114
- **Says:** Main transponder described as VHF/UHF 449/401.5 MHz (00 L114, 05 L15/L244, 07 L161, 05 §5) while 05 §2.1 says S-band 2025/2200 MHz.
- **Should say:** S-band TT&C (UL 2025–2110 MHz, DL 2200–2290 MHz); the only UHF element is the 437.5 MHz whip beacon (TTC_BEACON_TX_ON/OFF 97/98).
- **Evidence:** tc_catalog.yaml funcs 72/73 ranges; LINK_BUDGET_AND_RATES.md beacon at 437.5 MHz.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/00_mission_overview.md`

#### E1-3.06 · CONFIRMED (M1); O3 battery item NOT CONFIRMED · EOSAT-1 manual — 00_mission_overview.md, line 81

- **File:** `/home/claude/work/smo/configs/eosat1/manual/00_mission_overview.md` — L81
- **Says:** Battery '40 Ah @ 28 V' (00 L81), '14.4–16.8 V 40 Ah 4S' (COM-001, see §1), '100 Wh / 3.6 Ah at 28 V' (01 §2.2).
- **Should say:** 100 Wh, 8S1P, 3 Ah (GomSpace BPX), 21.5–29.2 V, model nominal 26.4 V (datasheet 28.8 V).
- **Evidence:** subsystems/eps.yaml battery block. NB the ops book's '28.8 V nominal vs 26.4 V model' (O3 note) is explained in the text (L4845–4848) and is NOT an error.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/00_mission_overview.md`

#### E1-3.07 · CONFIRMED (P2b) · Procedure — contingency/thermal_exceedance.md, line 39

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/thermal_exceedance.md` — L39
- **Says:** TCs written under non-parser labels (`**TC (Battery cold):**`, `**Action (Battery hot):**`, etc.) are invisible to the procedure runner: HEATER_BATTERY, HEATER_OBC, PAYLOAD_SET_MODE, SET_PARAM, HEATER_SET_SETPOINT, AOCS_SET_MODE are never sent. Same pattern: obdh_watchdog_recovery.md L31 `**TC (conditional):**`; reaction_wheel_anomaly.md L73; overcurrent_response.md L116; undervoltage_loadshed.md Step 7 L141–145 (only EPS_POWER_ON is sent).
- **Should say:** Use `**BRANCH:**`/`**LABEL:**` structure with plain `**TC:**` lines (PROCEDURE_SCHEMA.md), or move the conditional TCs into separate labelled steps.
- **Evidence:** smo_common.procedures.schema parses only `**TC:**` (P1/P3 parser checks).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/thermal_exceedance.md`

#### E1-3.08 · CONFIRMED inconsistency (OER1 #1, F1); fact to verify · OER *Concurrent Spacecraft Design* — 02_canadian_ecosystem.md, line 34

- **File:** `/home/claude/work/cdf/docs/oer/chapters/02_canadian_ecosystem.md` — L34
- **Says:** OER ch. 2 presents Lunar Gateway as active ('2019+', Canadarm3 'In development', L45, L139, Problem 6 L377); the facilitator book (L787–788, L800, L896, caption L775) says the Gateway programme was cancelled in March 2026 and Canadarm3's role is under review.
- **Should say:** Make both books state the same, verified status (owner to confirm the March 2026 cancellation and cite a source); update Problem 6.
- **Evidence:** Facilitator book L775–896. External fact not verifiable from the tree.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/02_canadian_ecosystem.md`

### Medium severity

#### E1-3.09 · CONFIRMED (M1, P2b) · EOSAT-1 manual — 00_mission_overview.md, line 72

- **File:** `/home/claude/work/smo/configs/eosat1/manual/00_mission_overview.md` — L72
- **Says:** Panel geometry: 00 L54/L70–72 six body panels, wings 0.24 m², total 0.78 m²; 01 §2.1 five body panels (−Z no cells), wings 0.12 m², 0.438 m²; 01 L13/L364 and 03 §8 'six panels'; CTG-009 L9–10 'six body-mounted panels', CTG-024 L9 'six solar panels on each face'.
- **Should say:** Five cell-carrying body faces (+X 0.060, −X 0.060, +Y 0.030, −Y 0.030, +Z 0.018 m²; −Z none) plus two 0.120 m² wings.
- **Evidence:** subsystems/eps.yaml solar_panels (mz_area_m2: 0.000 — imager aperture + radiator) and wing comment (0.120 m² of cells per wing).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/00_mission_overview.md`

#### E1-3.10 · CONFIRMED (M1) — owner to pick the frame · EOSAT-1 manual — 01_eps.md, line 36

- **File:** `/home/claude/work/smo/configs/eosat1/manual/01_eps.md` — L36
- **Says:** Face assignment: 01 L36/L55 put the imager aperture/radiator on −Z and 01 §2.1 makes +Z orbit-normal; 00 L67–68, 02, 06 put the payload on +Z (nadir); 01 §8.1 calls −Z 'zenith'; 03 §2.2 radiators on ±Y.
- **Should say:** One body-frame convention for the whole manual (the simulator puts the imager aperture/radiator on −Z: eps.yaml mz comment).
- **Evidence:** subsystems/eps.yaml solar_panels comment.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/01_eps.md`

#### E1-3.11 · CONFIRMED (M1) · EOSAT-1 manual — 00_mission_overview.md, line 79

- **File:** `/home/claude/work/smo/configs/eosat1/manual/00_mission_overview.md` — L79
- **Says:** Power: 00 L79–80 peak ~40 W, average ~20 W; 01 peak ~89 W, NOMINAL ~29 W; 03 L34 nominal dissipation ~80 W; 06 §8 payload IMAGING ~25 W vs 01 §3.1 5.5 W + 15 W cooler.
- **Should say:** Use the 01_eps / ops-book power table (nominal 28.7 W; EOL generation 38 W at worst β).
- **Evidence:** Ops book L4919–4924 and eps.yaml (obc_power_w 6.0).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/00_mission_overview.md`

#### E1-3.12 · CONFIRMED (D1a #5, #6) · SMO docs — OPERATIONS_GUIDE.md, line 119

- **File:** `/home/claude/work/smo/docs/OPERATIONS_GUIDE.md` — L119
- **Says:** '98.2° sun-synchronous, 705 km altitude'; L222–235 typical values ±100 Nms wheel momentum, 1000–1500 W generation, 800–1200 W consumption, 0–2000 RPM; FPA '> −3 °C (ALARM)'.
- **Should say:** 98.0°, ~513 km mean; CubeSat-scale values (wheel momentum mN·m·s, generation ~38–45 W orbit average, wheels ≤ 5500 rpm); −3.0 °C is the imaging-readiness gate, health yellow is +14.0 °C.
- **Evidence:** orbit.yaml altitude_km 513.0, inclination 98.0; aocs.yaml max_speed_rpm 5500; INSTRUCTOR_GUIDE FPA limits.
- **French mirror:** `/home/claude/work/smo/docs/fr/OPERATIONS_GUIDE.md`

#### E1-3.13 · CONFIRMED (D1a #8) · SMO docs — OPERATIONS_GUIDE.md, line 1623

- **File:** `/home/claude/work/smo/docs/OPERATIONS_GUIDE.md` — L1623
- **Says:** FPA cooler target −8 °C (L358, L794, L1623, '−8 °C nominal range').
- **Should say:** Default setpoint −15.0 °C; commandable envelope −20 … 0 °C.
- **Evidence:** tcs.yaml fpa_cooler_target_c −15.0; tc_catalog PAYLOAD_COOLER_SETPOINT default −15.0, range −20…0.
- **French mirror:** `/home/claude/work/smo/docs/fr/OPERATIONS_GUIDE.md`

#### E1-3.14 · CONFIRMED (W2) · Week 3 pack — sim_commissioning_instructor.md, line 89

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/sim_commissioning_instructor.md` — L89
- **Says:** FPA cooler 'can't reach −60 °C' (L89) and '≤ −55 °C' (L109).
- **Should say:** Setpoint −15 °C default; envelope −20 … 0 °C (a −55 °C target is outside the commandable range and would be rejected with 0x0003).
- **Evidence:** tc_catalog.yaml PAYLOAD_COOLER_SETPOINT range; tcs.yaml.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/sim_commissioning_instructor.md` (not yet installed; staged at `/home/claude/work/xlate/W2/sim_commissioning_instructor/fr.md`)

#### E1-3.15 · CONFIRMED (O1 #11) · ORBIT NORTH operations book, line 1603

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L1603
- **Says:** MCS mock-up shows fpa_temp −58 °C.
- **Should say:** A value inside the −20…0 °C envelope (e.g. −15.0 °C).
- **Evidence:** As above.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.16 · CONFIRMED (P3) · Procedure — emergency/total_power_failure.md, line 53

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/emergency/total_power_failure.md` — L53
- **Says:** EMG-002: battery-heater thermostat −5 / 0 °C; EMG-006 (thermal_runaway.md L75) +5 / +10 °C.
- **Should say:** +5 / +10 °C.
- **Evidence:** subsystems/tcs.yaml battery heater on_temp_c 5.0, off_temp_c 10.0.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/emergency/total_power_failure.md`

#### E1-3.17 · CONFIRMED (OER5) · OER *Concurrent Spacecraft Design* — 18_operations_and_fdir.md, line 168

- **File:** `/home/claude/work/cdf/docs/oer/chapters/18_operations_and_fdir.md` — L168
- **Says:** FDIR wheel over-speed threshold 6000 rpm (OER ch. 18); facilitator/TM 5000 RPM.
- **Should say:** Match the model: wheel max 5500 rpm; RW_OVERSPEED event at 5000 rpm.
- **Evidence:** aocs.yaml max_speed_rpm 5500; event_catalog.yaml 0x0201 'exceeded speed threshold (5000 RPM)'.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/18_operations_and_fdir.md`

#### E1-3.18 · CONFIRMED (M1) · EOSAT-1 manual — 06_payload.md, line 101

- **File:** `/home/claude/work/smo/configs/eosat1/manual/06_payload.md` — L101
- **Says:** §3 lists payload modes 0–2; the generated command table lists PAYLOAD_SET_MODE 0…3 (3 = CALIBRATION); PUS_SERVICE_REFERENCE func 26 also '0=off, 1=standby, 2=imaging'.
- **Should say:** Add mode 3 = CALIBRATION in 06 §3 and the PUS table.
- **Evidence:** tc_catalog.yaml PAYLOAD_SET_MODE mode 0=off,1=standby,2=imaging,3=calibration.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/06_payload.md`

#### E1-3.19 · CONFIRMED (P3, tree inconsistency) · Procedure — nominal/eclipse_transition.md, line 34

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/eclipse_transition.md` — L34
- **Says:** Mode 8 is 'ECLIPSE_PROPAGATE' (NOM-010 L34/L79) vs 'ECLIPSE' (NOM-002); mode 4 'NOMINAL_NADIR' (eclipse_transition L120, walkthrough L455) vs 'NOMINAL'.
- **Should say:** Fix the tree first: tc_catalog.yaml labels 4/8 as NOMINAL_NADIR / ECLIPSE_PROPAGATE while aocs_mode_codes.yaml ('canonical') says NOMINAL / ECLIPSE — then align the cards.
- **Evidence:** tc_catalog.yaml AOCS_SET_MODE enum vs aocs/aocs_mode_codes.yaml. The inconsistency is in the ground truth itself.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/eclipse_transition.md`

#### E1-3.20 · CONFIRMED (tree defect; O4b #3 misattributed) · ORBIT NORTH operations book, line 8775

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L8775
- **Says:** Book says the AOCS drop to SAFE_BOOT after a GPS time jump raises event 0x020F.
- **Should say:** Book matches the simulator; fix the tree: either emit 0x0200 AOCS_MODE_CHANGE (with reason) for the forced SAFE_BOOT, or rename/define 0x020F in event_catalog.yaml, then update the book.
- **Evidence:** service_dispatch.py L2003–2008 emits 0x020F; event_catalog.yaml L58 defines 0x020F as AOCS_MODE_RESTORED (and 0x020F is also the aocs.mode parameter ID).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.21 · CONFIRMED (tree nuance) · EOSAT-1 manual — 12_time_and_clocks.md, line 205

- **File:** `/home/claude/work/smo/configs/eosat1/manual/12_time_and_clocks.md` — L205
- **Says:** 12_time says SET_TIME is not in the bootloader allowlist; 00_mission_overview L177 and the SYS_SET_MISSION_PHASE catalogue text list S9.1 in the bootloader subset.
- **Should say:** State both halves: S9.1 passes the acceptance gate in the bootloader but fails at execution until OBC_BOOT_APP. (12_time is right in effect; 00 L177 is misleading.)
- **Evidence:** engine.py L2858 (accepts S9.1), obdh_basic.py L1058–1075 (_BOOTLOADER_ALLOWED lacks set_time).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/12_time_and_clocks.md`

#### E1-3.22 · CONFIRMED (M2 #22) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 87

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L87
- **Says:** L91–93: func 69 (TTC_DEPLOY_ANTENNA) may not be in the bootloader-allowed set — 'Add func_id 69 to the engine bootloader-allowed set'.
- **Should say:** Delete the caveat: 69 is in the subset.
- **Evidence:** engine.py L2880 subset includes 69; 00_mission_overview L178.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-3.23 · CONFIRMED (M2 #21) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 69

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L69
- **Says:** Beacon table: `obc_mode` 0x0300 '0 (NOMINAL)' while in the bootloader; `spacecraft_phase` '0 (BOOTLOADER)'.
- **Should say:** spacecraft_phase 3 (BOOTLOADER_OPS); describe obc_mode as the bootloader value (sw_image 0x0311 = 0 is the bootloader indicator).
- **Evidence:** parameters.yaml 0x0129 (0=pre-sep … 3=bootloader); tc_catalog SYS_SET_MISSION_PHASE phase 3 = BOOTLOADER_OPS.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-3.24 · CONFIRMED (M2 #28) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 519

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L519
- **Says:** 'GPS fix type ≥ 2 (3D fix)' vs L500 '1 (2D) → 3 (3D+velocity)'.
- **Should say:** 0=none, 1=2D, 2=3D, 3=3D+vel: '≥ 2 (3D)' is right; make L500 '1 (2D) → 2 (3D) → 3 (3D+vel)'.
- **Evidence:** parameters.yaml 0x0274 'GPS fix type (0=none, 1=2D, 2=3D, 3=3D+vel)'.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-3.25 · REPORTED (M2 #34–38), line checked · EOSAT-1 manual — software_architecture.md, line 663

- **File:** `/home/claude/work/smo/configs/eosat1/manual/software_architecture.md` — L663
- **Says:** TM packet 'PUS-C Secondary Header 4 bytes, data from byte 10' vs L893–908 (9 octets, data at offset 15); `time_epoch: "2024-01-01T00:00:00Z"` vs J2000 in 12_time §2; beacon SID 11 at 10 Hz vs 30 s elsewhere; 'Redis-based IPC'; '6U … ocean current monitoring'.
- **Should say:** Align with 12_time_and_clocks.md (9-octet header, J2000 CUC epoch), beacon period 30 s; review the whole chapter (it predates the 2026-08 build).
- **Evidence:** Same file L893–908; 12_time_and_clocks.md §2–3.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/software_architecture.md`

#### E1-3.26 · REPORTED (M1), line checked · EOSAT-1 manual — 04_obdh.md, line 267

- **File:** `/home/claude/work/smo/configs/eosat1/manual/04_obdh.md` — L267
- **Says:** §8.1 CUC at 1 s resolution; §3.1 'bootloader does NOT auto-transition' vs §3.4 'auto-attempts application boot'; L31 OBC-B on 'Switchable (SW-6)' and 05 L49–51 UNSW-2/SW-1 vs 01 §2.3 (no redundant-OBC line; line 6 = htr_obc).
- **Should say:** Coarse + fine CUC (12_time); one statement on auto-boot (OBC_BOOT_INHIBIT governs it); use the 01 PDM line table.
- **Evidence:** 12_time_and_clocks.md; tc_catalog OBC_BOOT_INHIBIT 'inhibit auto-boot'.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/04_obdh.md`

#### E1-3.27 · REPORTED (M1), line checked · EOSAT-1 manual — 05_ttc.md, line 336

- **File:** `/home/claude/work/smo/configs/eosat1/manual/05_ttc.md` — L336
- **Says:** §8 TTC-01 auto-switch after 120 s vs 08 TTC-01 24 h; RSSI threshold −105 dBm (§8) vs −100 dBm (§7); §5.3 worst-case margin ~3 dB at 5° vs §3.2 33–57 dB; §7 note 'receive-only mode during safe mode' vs 'TM continues at LOW'.
- **Should say:** Take values from subsystems/fdir.yaml / ttc.yaml and LINK_BUDGET_AND_RATES.md; delete 'receive-only'.
- **Evidence:** LINK_BUDGET_AND_RATES.md margin tables (≥ 34.5 dB at 5°).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/05_ttc.md`

#### E1-3.28 · CONFIRMED (P1) · Procedure — commissioning/ttc_link_verification.md, line 28

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/ttc_link_verification.md` — L28
- **Says:** COM-006 post-condition 'HIGH-tier elevation gate verified by rejection below 10 deg' and Step 8 'confirm the 10 deg HIGH-tier gate is enforced at each station' contradict Step 2b and the revision note (no on-board gate).
- **Should say:** 'MCS warns below 10° (ground rule); the spacecraft does not reject HIGH on elevation.'
- **Evidence:** tc_catalog.yaml TTC_SET_DATA_RATE 'There is NO on-board elevation gate (2026-08c)'.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/ttc_link_verification.md`

#### E1-3.29 · CONFIRMED (P2b) · Procedure — contingency/star_tracker_failure.md, line 150

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/star_tracker_failure.md` — L150
- **Says:** Verification criterion `aocs.st1_status` = 0 (OFF) after isolation; Step 4 note (L98–104) says 0x0240 stays 4 (FAILED) after power-off and must not be checked.
- **Should say:** Criterion: `aocs.st_selected` (0x0244) = 2 and ST1 isolated (st1_status may read 4).
- **Evidence:** Card's own Step 4 note; parameters.yaml 0x0240 enum.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/star_tracker_failure.md`

#### E1-3.30 · CONFIRMED (P2a #3, #9; P2b) · Procedure — contingency/aocs_anomaly.md, line 35

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/aocs_anomaly.md` — L35
- **Says:** Step 3 disables a wheel with `SET_PARAM(param_id=aocs.rw<N>_enable, value=0)`; Step 4 `AOCS_DESATURATE` and reaction_wheel_anomaly L48 have no func_id; eps_safe_mode Step 2 PAYLOAD_SET_MODE and Step 8 OBC_SET_MODE have no func_id; obdh_watchdog L70 OBC_SET_MODE without 50.
- **Should say:** `AOCS_DISABLE_WHEEL(wheel_idx=N)` (func 2); add func_ids (AOCS_DESATURATE 1, PAYLOAD_SET_MODE 26, OBC_SET_MODE 50).
- **Evidence:** tc_catalog.yaml.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/aocs_anomaly.md`

#### E1-3.31 · REPORTED (P2b), line checked · Procedure — contingency/obdh_watchdog_recovery.md, line 59

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/obdh_watchdog_recovery.md` — L59
- **Says:** Time fix via `SET_PARAM(param_id=obdh.utc_correction…)`, drift thresholds 2 s vs 5 s; L52 'respective CON procedures'.
- **Should say:** Use SET_TIME (S9.1) / OBC_GPS_TIME_SYNC (func 80) as CTG-021 does; one drift threshold; 'CTG procedures'.
- **Evidence:** tc_catalog.yaml S9.1, func 80.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/obdh_watchdog_recovery.md`

#### E1-3.32 · CONFIRMED (O4a, M2 #13, P2b) · ORBIT NORTH operations book, line 8793

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L8793
- **Says:** The ops book keeps its own EMG numbering (EMG-002 Loss of Attitude, EMG-003 Loss of Communication, EMG-004 OBC Reboot, EMG-005 Thermal Runaway, EMG-006 Total Power Failure) with a mapping table; the instructor book (L170, L385, L575), the procedures and the manual use the simulator numbering (EMG-004 Loss of Communication, EMG-003 OBC Reboot …). CTG numbering diverges the same way (CTG-005, CTG-018 editor notes L8006, L8443).
- **Should say:** Adopt the simulator numbering in the ops book (the cards students open in the MCS) and keep the mapping only as a historical note.
- **Evidence:** procedures/emergency/*.md headings; ops book L8792–8797.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.33 · CONFIRMED (W2) · Instructor book (scenario catalogue), line 60

- **File:** Drive `SpaceCDF/docs/course/instructor_book.md` (local copy `/home/claude/work/drive_course/instructor_book.md`) — L60
- **Says:** BP-1 phase: instructor book L60 says NOMINAL = 6; breakpoint_spec L35 says 5 (NOMINAL) and maps '5+ = COMMISSIONING/NOMINAL'.
- **Should say:** 5 = COMMISSIONING, 6 = NOMINAL everywhere.
- **Evidence:** parameters.yaml 0x0129; tc_catalog SYS_SET_MISSION_PHASE enum.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/instructor_book.md` (local build `/home/claude/work/out/course_fr/instructor_book.md`)

#### E1-3.34 · CONFIRMED (W2) · Week 3 pack — breakpoint_spec.md, line 139

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/breakpoint_spec.md` — L139
- **Says:** YAML uses keys the loader drops (`override_state`, `time_s`, `type`) and `aocs.mode: NADIR_PREP`; L41 'NADIR pointing'.
- **Should say:** Use the loader schema from instructor book §5.10.1; mode NOMINAL (4).
- **Evidence:** aocs_mode_codes.yaml (no NADIR_PREP).
- **French mirror:** `cdf/docs/orbit_north/week3/fr/breakpoint_spec.md` (not yet installed; staged at `/home/claude/work/xlate/W2/breakpoint_spec/fr.md`)

#### E1-3.35 · CONFIRMED (W2, O2) · Week 3 pack — training_day2.md, line 45

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/training_day2.md` — L45
- **Says:** Voice-loop callouts 'may use either language' (training_day2 L44–46); ops book L4130 (O2 L1293) and workbook L453 'Voice-loop language declared. EN or FR'.
- **Should say:** Owner ruling R6 / STYLE_FR §16: callouts stay in English. Fix the English (the French mirrors it).
- **Evidence:** tools/i18n/STYLE_FR.md §16.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/training_day2.md` (not yet installed; staged at `/home/claude/work/xlate/W2/training_day2/fr.md`)

#### E1-3.36 · CONFIRMED inconsistency (OER1 #2) · OER *Concurrent Spacecraft Design* — 03_international_standards.md, line 298

- **File:** `/home/claude/work/cdf/docs/oer/chapters/03_international_standards.md` — L298
- **Says:** 6U envelope 100 × 226.3 × 340.5 mm (OER §3.5.3; facilitator L6931; learner workbook L2639) vs 366.0 mm (facilitator L1503, where 12U in the same table is 340.5).
- **Should say:** Pick one convention and footnote it: the simulator models a 366 mm long 6U (eps.yaml '366x226 face'); CDS 6U Rev 1.0 gives 366 mm. Apply to 6U and 12U rows in all four tables.
- **Evidence:** subsystems/eps.yaml solar_panels comments ('366x226 face').
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/03_international_standards.md`

#### E1-3.37 · CONFIRMED (F1) · Facilitator book (SpaceCDF course textbook), line 1499

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L1499
- **Says:** CubeSat mass limits: 1U 1.33 kg (L687, L694, L2314, L2691), 2U 2.66 kg (L2315), 3U 4.0 kg (L2316) vs 2.0/4.0/6.0 kg (L1499–1502); L1483 '≤ 2.0 kg per U, waiver to 2.66'.
- **Should say:** CDS Rev 14 limits 1U 2.00 kg, 2U 4.00 kg, 3U 6.00 kg everywhere (1.33 kg/U is Rev 13).
- **Evidence:** CDS Rev 14 (2020; 14.1 2022).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.38 · CONFIRMED (F1) · Facilitator book (SpaceCDF course textbook), line 1399

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L1399
- **Says:** For ECSS-E-ST-31C (Thermal) the NASA equivalent given is NASA-STD-5001B (structural design and test factors).
- **Should say:** A thermal equivalent (e.g. NASA GSFC-STD-7000 thermal sections) or 'no direct equivalent'.
- **Evidence:** NASA-STD-5001 = structural factors of safety.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.39 · CONFIRMED (F5, OER5) · Facilitator book (SpaceCDF course textbook), line 9587

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L9587
- **Says:** Appendix: ECSS-E-ST-60-20C cited as 'AOCS — Part 1'; OER ch. 21 L266 'ECSS-E-ST-60-20C — Stars sensors'.
- **Should say:** AOCS: ECSS-E-ST-60-30C (Satellite AOCS requirements); ECSS-E-ST-60-20C is 'Star sensor terminology and performance specification'.
- **Evidence:** ECSS catalogue.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.40 · CONFIRMED (F2) · Facilitator book (SpaceCDF course textbook), line 4362

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4362
- **Says:** Table 3.1.7: hot case with BOL coatings, cold case with EOL; L1616 and the worked example (L1708, L1743) use hot = EOL, cold = BOL (the physically conservative pairing; OER ch. 9 already swapped).
- **Should say:** Hot case: EOL coatings (α_s maximum); cold case: BOL coatings.
- **Evidence:** UV darkening raises α_s at EOL (book L4386).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.41 · PLAUSIBLE (F3) — author check · Facilitator book (SpaceCDF course textbook), line 5593

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L5593
- **Says:** Desaturation geometry: near the magnetic equator the uncontrollable axis is said to be yaw.
- **Should say:** Near the equator B is roughly along-track → roll (along-track axis for a polar orbit) is uncontrollable; near the poles B is radial → yaw.
- **Evidence:** Torque τ = m × B has no component along B.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.42 · CONFIRMED (F4) · Facilitator book (SpaceCDF course textbook), line 7560

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L7560
- **Says:** 'Canadian BRITE satellites (UniBRITE and BRITE-Austria…)'.
- **Should say:** UniBRITE and BRITE-Austria are the Austrian pair (built with UTIAS/SFL); the Canadian pair is BRITE-Toronto and BRITE-Montréal.
- **Evidence:** BRITE constellation membership.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.43 · CONFIRMED (F4) · Facilitator book (SpaceCDF course textbook), line 8604

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L8604
- **Says:** Hitomi root cause given as a star-tracker 'unit conversion' error.
- **Should say:** JAXA: attitude-determination error (IRU bias estimated wrongly after a star-tracker dropout) followed by an incorrectly uploaded thruster-control parameter set.
- **Evidence:** JAXA Hitomi anomaly report (2016).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

### Low severity

#### E1-3.44 · CONFIRMED (D1a #2) · SMO docs — INSTRUCTOR_GUIDE.md, line 545

- **File:** `/home/claude/work/smo/docs/INSTRUCTOR_GUIDE.md` — L545
- **Says:** Troubleshooting `curl http://localhost:8000/api/instructor/snapshot`; L5 says the instructor console is on 8080.
- **Should say:** `curl http://localhost:8080/api/instructor/snapshot`.
- **Evidence:** Same document L5–6.
- **French mirror:** `/home/claude/work/smo/docs/fr/INSTRUCTOR_GUIDE.md`

#### E1-3.45 · CONFIRMED (W2) · Week 3 pack — training_day1.md, line 173

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/training_day1.md` — L173
- **Says:** MPS on port 8080 (same as MCS).
- **Should say:** Use the instructor book §5.10.0 port table (simulator 8080, MCS 9090, planner own port).
- **Evidence:** INSTRUCTOR_GUIDE.md L5–6 (MCS on 9090).
- **French mirror:** `cdf/docs/orbit_north/week3/fr/training_day1.md` (not yet installed; staged at `/home/claude/work/xlate/W2/training_day1/fr.md`)

#### E1-3.46 · CONFIRMED (.yaml); parameter items NOT CONFIRMED as errors · EOSAT-1 manual — 08_fdir.md, line 103

- **File:** `/home/claude/work/smo/configs/eosat1/manual/08_fdir.md` — L103
- **Says:** §9 lists contingency procedure files as `.yaml`; TCS-01 reads bat_temp at 0x0407 while EPS uses 0x0102; TCS-04 detects on 0x0408 while naming fpa_temp (0x0601).
- **Should say:** `.md` under procedures/contingency/. The two temperature pairs are both valid parameters (tcs.temp_battery 0x0407 vs eps.bat_temp 0x0102; tcs.temp_fpa 0x0408 vs payload.fpa_temp 0x0601) — name the one actually monitored.
- **Evidence:** parameters.yaml 0x0102, 0x0407, 0x0408, 0x0601 all exist.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/08_fdir.md`

#### E1-3.47 · REPORTED (M1), line checked · EOSAT-1 manual — 03_tcs.md, line 120

- **File:** `/home/claude/work/smo/configs/eosat1/manual/03_tcs.md` — L120
- **Says:** Zone table still shows FPA bands −18/+8 and −20/+12, which L156 says were superseded; cooler 'starts automatically in STANDBY' vs 01 fpa_cooler PDM line default OFF.
- **Should say:** Update the table to the current bands; cooler is commanded (FPA_COOLER func 43 / EPS_FPA_COOLER func 17).
- **Evidence:** Same file L156.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/03_tcs.md`

#### E1-3.48 · REPORTED (M1, O5), line checked · EOSAT-1 manual — 06_payload.md, line 26

- **File:** `/home/claude/work/smo/configs/eosat1/manual/06_payload.md` — L26
- **Says:** GSD ~33 m (06 §2, 07 §2.2) vs ~33.4 m (06 §2.2) vs 30 m / 29.3 m (ops book §16.3 L9560 / §16.7 L9690); product 100 MB vs '~50–200 MB per image' vs 4 MiB raw frame.
- **Should say:** One GSD at 513 km and one product size (courseware 4 MiB, physical 100.7 MB, as ops book §13.6 explains).
- **Evidence:** orbit.yaml 513 km.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/06_payload.md`

#### E1-3.49 · PLAUSIBLE (M1) · EOSAT-1 manual — 07_orbit_ops.md, line 59

- **File:** `/home/claude/work/smo/configs/eosat1/manual/07_orbit_ops.md` — L59
- **Says:** §3.1/§3.2: '~0 min near equinox' and '|β| < 25° → max eclipse' presented for a dawn–dusk orbit.
- **Should say:** For a near-terminator SSO, eclipses are minimal around the summer solstice and longest near the winter solstice; high |β| is the norm. Rephrase.
- **Evidence:** Orbital-geometry review.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/07_orbit_ops.md`

#### E1-3.50 · CONFIRMED (P2a #10) · Procedure — contingency/gps_time_sync_recovery.md, line 115

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/gps_time_sync_recovery.md` — L115
- **Says:** Step 5 uses `aocs.rate_x/y/z`; other cards use `aocs.rate_roll/pitch/yaw`.
- **Should say:** `aocs.rate_roll/pitch/yaw` (0x0204–0x0206).
- **Evidence:** parameters.yaml has rate_roll (0x0204); no rate_x.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/gps_time_sync_recovery.md`

#### E1-3.51 · CONFIRMED (P2b) · Procedure — contingency/payload_anomaly.md, line 43

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/payload_anomaly.md` — L43
- **Says:** Cooler switched on with `SET_PARAM(param_id=tcs.cooler_fpa, value=1)`.
- **Should say:** `FPA_COOLER(on=1)` (func 43), as corrupted_image.md does.
- **Evidence:** tc_catalog.yaml func 43.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/payload_anomaly.md`

#### E1-3.52 · REPORTED (P1), line checked · Procedure — commissioning/payload_power_on.md, line 72

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/payload_power_on.md` — L72
- **Says:** COM-009: prereq '~15 W' vs Step 4 2–3 W; Step 9/off-nominal cite firmware version/self-test that the Step 5 note says does not exist; exit claims SID 5 enabled but no card enables it; Step 8 requests SID 6 for thermal.
- **Should say:** Align with the step data; enable SID 5 with HK_ENABLE(sid=5) if the exit state needs it; thermal = SID 3.
- **Evidence:** hk_structures.yaml.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/payload_power_on.md`

#### E1-3.53 · REPORTED (P1), line checked · Procedure — commissioning/aocs_sensor_calibration.md, line 22

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/aocs_sensor_calibration.md` — L22
- **Says:** COM-003: off-nominal 0x0A03 'tracker unused in COARSE_SUN, re-command NOMINAL' contradicts the Step 4 precondition; '300 s of NOMINAL after' never commanded; heading 'Revision 2.0 — what changed' in a Rev 3.0 card; Step 6 gate 0.10 deg/s never met wheels-off (owner ruling pending).
- **Should say:** Author review.
- **Evidence:** Card text.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/aocs_sensor_calibration.md`

#### E1-3.54 · REPORTED (P1), line checked · Procedure — leop/first_acquisition.md, line 15

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/leop/first_acquisition.md` — L15
- **Says:** LEOP-001 Purpose says it synchronises on-board time but Step 6 defers time sync to LEOP-006; exit state lists disabled SIDs 2/5/7/12 while Step 5 lists 8 and 9 as the other SIDs. LEOP-002 entry state SIDs 1/3/4/6 vs Step 2 note 1/3/4/6/11. LEOP-003 band [400, 550] vs [495, 540] km. LEOP-004 bus band [27.0, 29.5] vs [26.0, 30.0] V in LEOP-002/007.
- **Should say:** Author review / align.
- **Evidence:** Card texts.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/leop/first_acquisition.md`

#### E1-3.55 · REPORTED (P1, M2 #12, #17), line checked · Procedure — commissioning/aocs_actuator_checkout.md, line 48

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/commissioning/aocs_actuator_checkout.md` — L48
- **Says:** COM-004 Step 1: FDIR safes AOCS with 'fewer than two wheels', then 'do not leave with fewer than three'; 10_desk_procedures L215 '2+ wheels failed' vs L353 '3+'; 10_ccp L361 'continue with 2 of 3 wheels'.
- **Should say:** Four wheels fitted; 3-of-4 required for NOMINAL — state one rule.
- **Evidence:** AOCS_DISABLE_WHEEL wheel_idx 0–3 (four wheels).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/commissioning/aocs_actuator_checkout.md`

#### E1-3.56 · REPORTED (P3), line checked · Procedure — emergency/total_power_failure.md, line 10

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/emergency/total_power_failure.md` — L10
- **Says:** EMG-002 survival load '~45 W' (table L10) vs '~32 W minimum load' (L83/L92).
- **Should say:** One survival-load figure.
- **Evidence:** Card text.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/emergency/total_power_failure.md`

#### E1-3.57 · CONFIRMED (P3) · Procedure — nominal/imaging_session.md, line 138

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/imaging_session.md` — L138
- **Says:** Post-condition 'FPA below −20.0 C' while the card's gates are −10.0 C (abort −5.0 C); setpoint envelope floor is −20 °C.
- **Should say:** 'FPA at setpoint (≤ −10.0 °C)'.
- **Evidence:** tc_catalog PAYLOAD_COOLER_SETPOINT range −20…0.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/imaging_session.md`

#### E1-3.58 · CONFIRMED (P3) · Procedure — nominal/data_rate_change.md, line 89

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/data_rate_change.md` — L89
- **Says:** LOW→HIGH step is 9.03 dB, but the next sentence says margin at HIGH is '12 dB below' LOW.
- **Should say:** 'about 10.5 dB below' (9.03 dB rate + 1.5 dB coding), as LINK_BUDGET_AND_RATES.md §2 states.
- **Evidence:** LINK_BUDGET_AND_RATES.md L265–266 (−10.53 dB predicted).
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/data_rate_change.md`

#### E1-3.59 · REPORTED (P3), line checked · Procedure — nominal/hk_configuration.md, line 70

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/hk_configuration.md` — L70
- **Says:** 'Only SID 1 survives a reboot enabled' vs L35 'SIDs 1 and 11 are enabled at power-up'.
- **Should say:** Reconcile (beacon SID 11 runs in the bootloader).
- **Evidence:** Card text.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/hk_configuration.md`

#### E1-3.60 · REPORTED (P3), line checked · Procedure — nominal/momentum_management.md, line 145

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/momentum_management.md` — L145
- **Says:** 'Abort and return to NOMINAL' contradicts Step 5 ('Do not command a mode here').
- **Should say:** Align.
- **Evidence:** Card text.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/momentum_management.md`

#### E1-3.61 · REPORTED (P3), line checked · Procedure — nominal/software_upload.md, line 148

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/nominal/software_upload.md` — L148
- **Says:** 'Verify memory region cleared' after a note saying the region is only overwritten; L193 'previous image retained in alternate bank' vs Recovery Action 2 (re-upload); L57 'start load' (S6.2 has no session).
- **Should say:** Author review.
- **Evidence:** tc_catalog S6.2 MEM_LOAD.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/nominal/software_upload.md`

#### E1-3.62 · CONFIRMED (P3) · Procedure — emergency/obc_reboot.md, line 108

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/emergency/obc_reboot.md` — L108
- **Says:** Step 5 expects last_reboot_cause = 1 (commanded) — correct per the model; off-nominal L195 treats 1 as watchdog.
- **Should say:** L195: 'If cause is 2 (watchdog)'.
- **Evidence:** obdh_basic.py REBOOT_WATCHDOG = 2.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/emergency/obc_reboot.md`

#### E1-3.63 · REPORTED (W2), line checked · Week 3 pack — training_day1.md, line 118

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/training_day1.md` — L118
- **Says:** MCS round-robin: six positions, 15-min stations; workbook WB-5.1 (L95–96) nine cards, 12-minute slot; student_tool_reference §1.1 six positions vs workbook 9–10.
- **Should say:** One position count and slot length (positions.yaml defines the consoles).
- **Evidence:** mcs/positions.yaml.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/training_day1.md` (not yet installed; staged at `/home/claude/work/xlate/W2/training_day1/fr.md`)

#### E1-3.64 · REPORTED (W2), line checked · Week 3 pack — student_tool_reference.md, line 118

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/student_tool_reference.md` — L118
- **Says:** Escalation ladder level 0…4 vs workbook C008 L897 `fdir.level` 0–3 alongside 'FDIR severity 0–4'.
- **Should say:** Separate the autonomy level (0–3) from event severity.
- **Evidence:** parameters.yaml fdir.level.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/student_tool_reference.md` (not yet installed; staged at `/home/claude/work/xlate/W2/student_tool_reference/fr.md`)

#### E1-3.65 · REPORTED (O1 #6, #7), line checked · ORBIT NORTH operations book, line 820

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L820
- **Says:** Ch. 6: 'There is no voice-loop chat in the MCS' and (L839) 'There is no second-key interlock in the MCS'; §7.1 (L1624/L1770, L1796–1819) describes a voice-loop chat panel and a Second-Key button required for critical commands.
- **Should say:** Delete the two ch. 6 sentences (§7.1 describes the current MCS).
- **Evidence:** Same book §7.1.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.66 · CONFIRMED (O1 #10, O2, O5) · ORBIT NORTH operations book, line 1763

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L1763
- **Says:** 'eight per-line currents (0x0118–0x011F)'; O2 L1081 'nine lines (0–8)' vs L1086 0x0118–0x011F; ops book §15 (O5 L497) 'nine line currents (0x0118–0x011F …)'.
- **Should say:** 'nine per-line currents: 0x0118–0x011F (lines 0–7) and 0x014B (line 8, propulsion)'.
- **Evidence:** parameters.yaml 0x0118 line_current_0 … 0x011F line_current_7, 0x014B line_current_8.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.67 · CONFIRMED (O2) · ORBIT NORTH operations book, line 3260

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L3260
- **Says:** 'both stations' / 'both ground stations' (L3260, L3948).
- **Should say:** 'the five stations' (or 'the station in view').
- **Evidence:** orbit.yaml ground_stations: Iqaluit, Troll, Svalbard, Inuvik, O'Higgins.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.68 · REPORTED (O2), line checked · ORBIT NORTH operations book, line 4216

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L4216
- **Says:** S1.7 timeout after OBC_BOOT_APP is 20 s in Table 10.8 but 30 s in Table 10.12 (L1444).
- **Should say:** One timeout (the simulator defers S1.7 by the ~10 s CRC window).
- **Evidence:** engine.py comment on deferred S1.7.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.69 · CONFIRMED (O2) · ORBIT NORTH operations book, line 4388

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L4388
- **Says:** Step 8 says the mission manager declares phase 5 and expects `eps.spacecraft_phase` = 5 within 5 s; §10.5 (L1020) says the instructor advances it on the console.
- **Should say:** Phase 5 is declared with SYS_SET_MISSION_PHASE(phase=5) (see §1).
- **Evidence:** tc_catalog.yaml func 120.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.70 · CONFIRMED (O4a #6, P3) · ORBIT NORTH operations book, line 7698

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L7698
- **Says:** NOM-009 bus band 27.0–32.0 V (also procedures/nominal/routine_health_check.md L34); COM-001 says the 8S pack tops out at 29.2 V; other cards 27.0–29.5 V.
- **Should say:** 27.0–29.5 V.
- **Evidence:** eps.yaml soc_100_v 29.2.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.71 · REPORTED (O4a #4), line checked · ORBIT NORTH operations book, line 7838

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L7838
- **Says:** NOM-012 note: step 1 'a real six-structure housekeeping sweep', step 4 'a real S11 schedule request'; the table's step 1 is a voice-loop statement and step 4 '(FDS)' with no TC.
- **Should say:** Align note and table.
- **Evidence:** Card text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.72 · CONFIRMED (O5) · ORBIT NORTH operations book, line 9672

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L9672
- **Says:** HIGH tier 'closes at Troll at 5 degrees'; §15.5 (L9396) and L9657 say HIGH needs ≥ 10°.
- **Should say:** HIGH closes at 5° on link margin but is planned only above 10° (ground rule) — say so.
- **Evidence:** tc_catalog TTC_SET_DATA_RATE (10° is a ground rule).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.73 · REPORTED (O5), line checked · ORBIT NORTH operations book, line 9611

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L9611
- **Says:** Cool-down narrative: '−2 C, on profile' at 20 min, then at 30 min 'profile says −4 C, reality −2 C', at 35 min −3 C vs −5 C.
- **Should say:** Make the profile/actual pairs monotonic and consistent.
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.74 · REPORTED (O5), line checked · ORBIT NORTH operations book, line 9803

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L9803
- **Says:** §16.10 bulletin: deferral due to star-tracker degradation, 'carries a second star tracker', yet falls back to gyro-propagated attitude; §16.7 has First Light succeeding.
- **Should say:** Explain why ST2 is not used, or drop the sentence.
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.75 · CONFIRMED (O3) · ORBIT NORTH operations book, line 6724

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L6724
- **Says:** §13.8: '328 s … against a 450-second window above 10 degrees'; the same pass is AOS→LOS 7:30 = 450 s in total.
- **Should say:** Time above 10° is shorter than AOS→LOS; recompute or say 'pass'.
- **Evidence:** Same section.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.76 · REPORTED (O3), line checked · ORBIT NORTH operations book, line 6230

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L6230
- **Says:** Mean pass 447 s (§13.2) vs '445 s average pass' (§13.6.1, L6543).
- **Should say:** One value.
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-3.77 · CONFIRMED (F1) · Facilitator book (SpaceCDF course textbook), line 1183

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L1183
- **Says:** CDS Rev 14 dated 2023 (L1183) vs 2022 (L1474, L1693).
- **Should say:** Rev 14 (2020) / Rev 14.1 (Feb 2022); use one.
- **Evidence:** CDS revision history.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.78 · CONFIRMED (F1, OER1 #5) · Facilitator book (SpaceCDF course textbook), line 368

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L368
- **Says:** Verification-method acronym TAID (L368, L418), ATID (L2395, L2610), 'ATRI or ATID' (L2613); OER uses ATIR(D); OER ch. 1 §1.2.4 'plus demonstration where ECSS lists it' vs ch. 5 'NASA practice adds demonstration'.
- **Should say:** One acronym book-wide (e.g. TARI + D) and one statement of who lists D.
- **Evidence:** ECSS-E-ST-10-02C lists test, analysis, review of design, inspection.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.79 · CONFIRMED (F2; intended) · Facilitator book (SpaceCDF course textbook), line 4653

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4653
- **Says:** §2–3 use β = −0.0019/°C and δ = 2.5 %/yr; the EO-Sat-1 section (L1885–1891) uses −0.0020 and 2.75 %/yr.
- **Should say:** Say explicitly that the EO-Sat-1 section uses the flight configuration (−0.0020/°C, 2.75 %/yr).
- **Evidence:** subsystems/eps.yaml temp_coeff_per_c −0.0020, annual_degradation 0.0275 — the EO-Sat-1 numbers are the simulator's.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.80 · REPORTED (F2), line checked · Facilitator book (SpaceCDF course textbook), line 4872

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4872
- **Says:** SuperDove bus unregulated 7.2–8.4 V (2S) vs 6.0–8.4 V for 2S elsewhere (L1297, L1308, L1438).
- **Should say:** 6.0–8.4 V.
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.81 · REPORTED (F3), line checked · Facilitator book (SpaceCDF course textbook), line 6463

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L6463
- **Says:** LDPC coding gain 5.5–8.5 dB; Table 3.3.8 gives 6.5–8.5 dB. Propulsion summary ranges (cold gas 40–75 s, green 225–250 s, L1072–1073) differ from the tables (L909/L833).
- **Should say:** Use the table values.
- **Evidence:** Same chapter.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.82 · REPORTED (F3), line checked · Facilitator book (SpaceCDF course textbook), line 5850

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L5850
- **Says:** Row 'Drag chute (tether)' described as an electrodynamic tether; L535 'slow gimbal rate (δ̇ = 1 rad/s)'.
- **Should say:** 'Electrodynamic tether'; '0.1 rad/s' or drop 'slow'.
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.83 · CONFIRMED (F4, OER4) · Facilitator book (SpaceCDF course textbook), line 7435

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L7435
- **Says:** '3U CubeSat BOM Summary' uses a 6U allocation (12 000 g); UniSat-1 BOM '5–7 line items' (L574) vs 9 rows, '5 COTS plus 2 custom' (L913); OER ch. 13 L326 same.
- **Should say:** 3U allocation 6 000 g; '9 line items (8 + harness)'.
- **Evidence:** CDS mass limits; table row count.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.84 · REPORTED (F4), line checked · Facilitator book (SpaceCDF course textbook), line 7452

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L7452
- **Says:** UniSat-1 BOM (L580–588) vs equipment list (L879–887): solar cells 7.5 vs 8.0 kEUR, UHF transceiver 55 vs 60 g, antenna 25 g/2.5 kEUR vs 20 g/2.0 kEUR (totals both 690 g / 44 kEUR); downlink 4800 bps (L873) vs AX100 9600 bps (L883).
- **Should say:** One set of line values; one data rate.
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.85 · REPORTED (F4, OER4), line checked · Facilitator book (SpaceCDF course textbook), line 8090

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L8090
- **Says:** Sine profile 1.25 g above 8 Hz vs crossover 3.22 g at 8 Hz (note acknowledges); random-vibration profiles differ between ch. 3.4 (+6 dB/oct, 0.01) and ch. 4.2 (+3 dB/oct, 0.004), both '~7 grms'; proto-flight TVAC range = acceptance range (L1169). Same sine issue in OER ch. 14 L194.
- **Should say:** Reconcile the profile and example; one random profile; proto-flight at qualification temperatures.
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.86 · CONFIRMED (F5) · Facilitator book (SpaceCDF course textbook), line 9804

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L9804
- **Says:** 'patch tolerates ~30° body rate'.
- **Should say:** '~30° pointing error'.
- **Evidence:** Units.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-3.87 · REPORTED (OER5), line checked · OER *Concurrent Spacecraft Design* — 17_ground_segment.md, line 154

- **File:** `/home/claude/work/cdf/docs/oer/chapters/17_ground_segment.md` — L154
- **Says:** Daily capacity 956 MB/day explained as 'four 8-minute passes' (ch. 22 L419) vs '5 passes/day' (ch. 17 §17.2.4); ch. 17 L129 volunteer UHF row computed at 2 Mbit/s.
- **Should say:** One pass count; UHF row at UHF rates (9.6 kbit/s), consistent with the text's 'housekeeping only'.
- **Evidence:** Text.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/17_ground_segment.md`

#### E1-3.88 · REPORTED (OER3), line checked · OER *Concurrent Spacecraft Design* — 10_aocs.md, line 585

- **File:** `/home/claude/work/cdf/docs/oer/chapters/10_aocs.md` — L585
- **Says:** Text: figure is 'for a drag-dominated small satellite'; Figure 10.4 caption (L589): CubeSat case 'magnetically rather than drag dominated'.
- **Should say:** Align text and caption.
- **Evidence:** Text.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/10_aocs.md`

#### E1-3.89 · CONFIRMED (OER2) · OER *Concurrent Spacecraft Design* — 09_power_and_thermal.md, line 91

- **File:** `/home/claude/work/cdf/docs/oer/chapters/09_power_and_thermal.md` — L91
- **Says:** §9.1.1 cites Green et al. 'Solar Cell Efficiency Tables, v.62, 2024'; Reference 9 gives version 62, Progress in Photovoltaics 31, 2023. Summary row 'dual deployable 25–48 W' omits the 12U value (~100 W).
- **Should say:** Version 62 is 2023 (Prog. Photovolt. 31(7)); add the 12U row.
- **Evidence:** Reference list.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/09_power_and_thermal.md`

#### E1-3.90 · REPORTED (OER2), line checked · OER *Concurrent Spacecraft Design* — 06_functional_decomposition.md, line 64

- **File:** `/home/claude/work/cdf/docs/oer/chapters/06_functional_decomposition.md` — L64
- **Says:** §6.1.1 SVG numbers universal functions F-010…F-014; §6.5 uses F-010/F-020/F-030/F-040/F-050.
- **Should say:** One numbering (the learner workbook skeleton uses F-010, F-020 …).
- **Evidence:** Text.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/06_functional_decomposition.md`

#### E1-3.91 · REPORTED (D2), line checked · SpaceCDF — docs/course/3_WEEK_SYLLABUS.md, line 28

- **File:** `/home/claude/work/cdf/docs/course/3_WEEK_SYLLABUS.md` — L28
- **Says:** Week 2 Friday gate review uses MCR criteria (3_WEEK_SYLLABUS L28) vs PDR criteria (3_week_syllabus_expanded L144). course_plan_expanded Day 3 sessions (Power/Structure/Thermal/Comms) vs COURSE_PLAN (Orbit/Payload & Comms/Power-AOCS-Thermal/Structure-Prop-Data); session 2.4 differs; Phase A mass margin +44 % (course_plan_expanded Fig 2.7, syllabus_expanded Fig 1.5) vs 20 % in the user guides; AOCS Engineer 'drives' 3.2/4.3 with no AOCS session on Day 3.
- **Should say:** Align the expanded and short versions.
- **Evidence:** Cross-document.
- **French mirror:** `/home/claude/work/cdf/docs/course/fr/3_WEEK_SYLLABUS.md`

#### E1-3.92 · REPORTED (D1b #4), line checked · SMO docs — PUS_SERVICE_REFERENCE.md, line 738

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L738
- **Says:** S12 example: EPS_BATTERY_SOC_WARNING '< 20 %' paired with S19 'Battery SoC critical → Payload off', contradicting the S12 table (L699, < 20 % → reduce loads) and S19 table (L990, SoC critical 0x0102 → FPA cooler off).
- **Should say:** Align the example with the two tables.
- **Evidence:** Same document.
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-3.93 · REPORTED (D1b #11, #14), line checked · SMO docs — LINK_BUDGET_AND_RATES.md, line 265

- **File:** `/home/claude/work/smo/docs/LINK_BUDGET_AND_RATES.md` — L265
- **Says:** 'Measured (Iqaluit @5°)' 57.8 / 45.7 / 35.2 vs the 5° margin table (SAFE 57.0, LOW 45.0, HIGH 34.5); §4.2 gives LOW at 5° NOMINAL as 45.7; L468 gate 4 (antenna deployed) applies to LOW and HIGH vs §2.2/§2.3 (HIGH only).
- **Should say:** One set of 5° values; antenna gate on HIGH only.
- **Evidence:** tc_catalog TTC_SET_DATA_RATE: 'HIGH requires a deployed antenna'.
- **French mirror:** `/home/claude/work/smo/docs/fr/LINK_BUDGET_AND_RATES.md`

#### E1-3.94 · REPORTED (D1a #4), line checked · SMO docs — INSTRUCTOR_GUIDE.md, line 325

- **File:** `/home/claude/work/smo/docs/INSTRUCTOR_GUIDE.md` — L325
- **Says:** Failure onset types 'Immediate/Gradual'; the modern console offers Step/Gradual/Intermittent.
- **Should say:** Step / Gradual / Intermittent.
- **Evidence:** Console UI.
- **French mirror:** `/home/claude/work/smo/docs/fr/INSTRUCTOR_GUIDE.md`

#### E1-3.95 · REPORTED (D1a #7), line checked · SMO docs — OPERATIONS_GUIDE.md, line 344

- **File:** `/home/claude/work/smo/docs/OPERATIONS_GUIDE.md` — L344
- **Says:** Timeline download at T+65 min vs Step 4 T+30 min (L340–344 vs L389).
- **Should say:** One time.
- **Evidence:** Text.
- **French mirror:** `/home/claude/work/smo/docs/fr/OPERATIONS_GUIDE.md`

#### E1-3.96 · CONFIRMED (D1a #14) · SMO docs — README.md, line 183

- **File:** `/home/claude/work/smo/docs/README.md` — L183
- **Says:** Statistics/limitations tables (April 2026: 'Service 2 not implemented', 'no gravity gradient torques', 'Service 18 defined but not auto-invoked').
- **Should say:** Refresh after the 2026-08 build (S2 device access and S18 OBCPs exist).
- **Evidence:** tc_catalog.yaml S2/S18 entries; OBCP_GUIDE.
- **French mirror:** `/home/claude/work/smo/docs/fr/README.md`

#### E1-3.97 · CONFIRMED (D1a #13) · SMO docs — PROPULSION_GUIDE.md, line 6

- **File:** `/home/claude/work/smo/docs/PROPULSION_GUIDE.md` — L6
- **Says:** Decay figures at 450 km (the document's own 2026-08 caution says re-derive at 513 km).
- **Should say:** Re-derive at 513 km.
- **Evidence:** orbit.yaml 513 km.
- **French mirror:** `/home/claude/work/smo/docs/fr/PROPULSION_GUIDE.md`

#### E1-3.98 · REPORTED (W1), line checked · Learner workbook, line 2649

- **File:** Drive `SpaceCDF/docs/course/learner_workbook_expanded.md` (local copy `/home/claude/work/drive_course/learner_workbook_expanded.md`) — L2649
- **Says:** Deployment switches 'Minimum 1 per accessible rail face' (L2649), 'Min 1 per accessible face' (L2743) vs Part A checklist 'Min 2' (L2792); propulsion decision tree 500–700 km → propulsion required (L2680–2683) vs Key rule 500–600 km depends on ballistic coefficient (L2697); gate criterion '25-year rule' (L4690) vs worksheets' FCC 5-year rule.
- **Should say:** Align within the workbook (CDS: ≥ 1 deployment switch; FCC 5-year rule binding).
- **Evidence:** Text.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/learner_workbook_expanded.md` (local build `/home/claude/work/out/course_fr/learner_workbook_expanded.md`)

#### E1-3.99 · CONFIRMED (OER5) · OER *Concurrent Spacecraft Design* — 21_position_reference.md, line 266

- **File:** `/home/claude/work/cdf/docs/oer/chapters/21_position_reference.md` — L266
- **Says:** 'ECSS-E-ST-60-20C — Stars sensors'.
- **Should say:** 'Star sensors'.
- **Evidence:** ECSS title.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/21_position_reference.md`

#### E1-3.100 · NOT CONFIRMED (M1 station item reversed) · EOSAT-1 manual — 06_payload.md, line 184

- **File:** `/home/claude/work/smo/configs/eosat1/manual/06_payload.md` — L184
- **Says:** 06 §8 note 4 speaks of five-station contact statistics (M1 flagged this as the odd one out).
- **Should say:** No change — five stations is correct; the two-station wording elsewhere is stale.
- **Evidence:** orbit.yaml lists five stations.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/06_payload.md`

## Section 4 — Editorial

### High severity

#### E1-4.01 · CONFIRMED (W2, O5, O3) · Instructor book (scenario catalogue), line 61

- **File:** Drive `SpaceCDF/docs/course/instructor_book.md` (local copy `/home/claude/work/drive_course/instructor_book.md`) — L61
- **Says:** 46 occurrences of the template leftover 'this shift' (global replace of 'Day 3/Day 4'): L61–63, 'Suggested day' column L144–179, L211–217, L533 'in the this shift and this shift instructor menus', L581, L645–648, L732, L938. The ops book has the same artefact in ch. 16 (L9510 'mid-this shift', L9538, L9575, L9655, L9721 'this shift morning', L9751 'this shift LEOP', L9776, L9783) and L4805 (lower-case paragraph start, O3 L242).
- **Should say:** Restore the intended day names (Day 3 / Day 4 …) or rewrite each sentence.
- **Evidence:** `grep -o 'this shift'` = 46 in instructor_book.md; 13 in orbit_north_week3.md (L856 and L3650 read naturally and may stay).
- **French mirror:** Drive `SpaceCDF/docs/course/fr/instructor_book.md` (local build `/home/claude/work/out/course_fr/instructor_book.md`)

#### E1-4.02 · CONFIRMED (D2) · SpaceCDF — docs/USER_GUIDE.md, line 56

- **File:** `/home/claude/work/cdf/docs/USER_GUIDE.md` — L56
- **Says:** Encoding round-trip turned '→' into '?' (L56, 61, 62, 64, 109, 128, 191, 213) and 'C/N₀', 'Eb/N₀' into 'C/N?', 'Eb/N?' (L109).
- **Should say:** Restore '→', 'C/N₀', 'Eb/N₀' (user_guide_expanded.md has the right characters).
- **Evidence:** grep of the file.
- **French mirror:** `/home/claude/work/cdf/docs/fr/USER_GUIDE.md`

#### E1-4.03 · CONFIRMED (F1) · Facilitator book (SpaceCDF course textbook), line 1872

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L1872
- **Says:** Ch. 1.4 table captions shifted by one table from Table 1.4.7 (L1872) to 1.4.22 (L2341); the 'Bad Objective' table (L1860) has no caption; Table 2.1.13 (L2757) captions the session summary with a verification-table caption. Visible example: Table 1.4.20 (L2310) 'End-to-end data-flow stages' heads the UniSat-1 alternatives; 1.4.21 heads the scoring table.
- **Should say:** Move each caption down one table and caption the Bad-Objective table; fix 2.1.13.
- **Evidence:** Viewed L2310–2322.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.04 · REPORTED (F2), line checked · Facilitator book (SpaceCDF course textbook), line 3741

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L3741
- **Says:** Ch. 2.4 captions 2.4.6–2.4.13 shifted (L972, 1006, 1037, 1054, 1072, 1085, 1104, 1155 in packet = source +2769); Table 2.3.8 (packet L684) captions the session summary while the UniSat-1 orbit-fit table (L634) has none; ch. 2.3 has Figure 2.3.2 but no 2.3.1.
- **Should say:** Realign captions; number figures.
- **Evidence:** Packet F2 notes; line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.05 · REPORTED (F3), line checked · Facilitator book (SpaceCDF course textbook), line 5699

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L5699
- **Says:** Ch. 3.2 propulsion captions are numbered 3.4.x and shifted by one (packet L748, 829, 893, 905; Figure 3.4.1 at L944).
- **Should say:** Renumber 3.2.x and realign.
- **Evidence:** Packet F3 notes; line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.06 · CONFIRMED (F4) · Facilitator book (SpaceCDF course textbook), line 7121

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L7121
- **Says:** Ch. 3.4/4.1/4.4 captions shifted: 3.4.10–3.4.16 (packet L251, 267, 322, 339, 792 [in ch. 4.1], 831, 849), 4.1.4–4.1.14 (L509 … L1003), 4.4.6–4.4.14 (L2053 … L2283). Example: L7662 'Table 3.4.13 — Non-volatile storage technologies' heads the Iridium trade.
- **Should say:** Realign all captions in ch. 3.4–4.4.
- **Evidence:** Viewed L7662–7672.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

### Medium severity

#### E1-4.07 · REPORTED (F2), line checked · Facilitator book (SpaceCDF course textbook), line 3997

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L3997
- **Says:** Empty section '### EPS Block Diagram'; the PCDU/EPS figure appears later (packet L1313) unnumbered; several ch. 3.1 figures and the N² figure (L865–867) unnumbered.
- **Should say:** Move the figure under the heading; number figures.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.08 · CONFIRMED (F1, F2, F3) · Facilitator book (SpaceCDF course textbook), line 256

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L256
- **Says:** Mangled SVG namespace `xmlns="[http://www.w3.org/2000/svg"](http://www.w3.org/2000/svg")` at L256, 471, 1242, 1910, (F2) 2814, 3556, (F3) 6081.
- **Should say:** `xmlns="http://www.w3.org/2000/svg"` — the SVGs may not render as written.
- **Evidence:** grep.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.09 · REPORTED (F4) · Facilitator book (SpaceCDF course textbook), line 6871

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L6871
- **Says:** Ch. 3.4 learning objectives 5–6 and reading list cover propulsion (Tsiolkovsky), but the chapter body has no propulsion section.
- **Should say:** Drop the objectives or add the section.
- **Evidence:** Packet F4 notes.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.10 · REPORTED (F1, F4), line checked · Facilitator book (SpaceCDF course textbook), line 2403

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L2403
- **Says:** Reference to 'Figure 1.1.3'; ch. 1.1 has no numbered figures. Similar: 'Figure 4.3.2' (packet F4 L1525) unnumbered risk matrix.
- **Should say:** Number the figures or remove the references.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.11 · REPORTED (F5) · Facilitator book (SpaceCDF course textbook), line 9166

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L9166
- **Says:** Index: 'N² interface matrix' and 'N-Squared interface matrix' duplicate entries; 'Structure, propulsion & equipment (ch.)' points to `#chapter-34-spacecraft-structure-and-on-board-data-handling`; all index href targets are English slugs (break once headings are translated).
- **Should say:** Merge duplicates; fix the target; add explicit `{#id}` anchors to the English headings so EN and FR share slugs.
- **Evidence:** Packet F5 notes.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.12 · CONFIRMED (O1, W2) · ORBIT NORTH operations book, line 80

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L80
- **Says:** 'Part 5' should be 'Part 2' (L80, L365, L380, L415); instructor book L3 'Part 5 (Spacecraft Operations)' vs back cover L20 'Part 2 — CubeSat Operations'.
- **Should say:** 'Part 2'.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.13 · CONFIRMED (O1, W2) · ORBIT NORTH operations book, line 57

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L57
- **Says:** NPR 7120.5F presented as NASA's Mission Operations Handbook (L57, L429; training_day1 L92, L193; student_procedure_quickref L166); L758 has it right. ECSS-E-ST-70-01C cited as 'Ground Segment'/procedures (L529, L568) — it is on-board control procedures (ground segment is ECSS-E-ST-70C).
- **Should say:** 'NPR 7120.5F, NASA Space Flight Program and Project Management Requirements'; 'ECSS-E-ST-70C Ground systems and operations'.
- **Evidence:** Standards titles.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.14 · REPORTED (W2) · ORBIT NORTH week-3 operations workbook, line 848

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3_workbook.md` (local copy `/home/claude/work/drive_course/orbit_north_week3_workbook.md`) — L848
- **Says:** Seven confirm sheets have an orphan table-header row followed by prose: C006 L848–849, C008 L883–884, C011 L988–989, CTG-007 L1410–1411, CTG-008 L1430–1431, CTG-012 L1465–1466, CTG-017 L1495–1496; 'CFMR' undefined (L1275); L789 'All 13 commissioning procedures'.
- **Should say:** Complete or remove the header rows; define CFMR.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3_workbook.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3_workbook.md`)

#### E1-4.15 · CONFIRMED (W2) · Week 3 pack — breakpoint_spec.md, line 203

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/breakpoint_spec.md` — L203
- **Says:** Unfilled authoring placeholders '[Claude Code: …]' in breakpoint_spec (1), peer_review_worksheets (5), sim_commissioning_instructor (5), sim_leop_instructor (3), student_procedure_quickref (6), student_tool_reference (9), training_day1 (8), training_day2 (8).
- **Should say:** Fill or delete before release.
- **Evidence:** `grep -c 'Claude Code:'` per file.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/breakpoint_spec.md` (not yet installed; staged at `/home/claude/work/xlate/W2/breakpoint_spec/fr.md`)

#### E1-4.16 · CONFIRMED (W2) · Instructor book (scenario catalogue), line 531

- **File:** Drive `SpaceCDF/docs/course/instructor_book.md` (local copy `/home/claude/work/drive_course/instructor_book.md`) — L531
- **Says:** Heading 'Chapter X — Anomaly Cue Card Reference Anomaly Cue Cards' (placeholder X, duplicated words; sections numbered 18.x); headings with no body L508–525.
- **Should say:** 'Chapter 18 — Anomaly Cue Cards'; remove empty headings.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/instructor_book.md` (local build `/home/claude/work/out/course_fr/instructor_book.md`)

#### E1-4.17 · REPORTED (D1a #1) · SMO docs — INSTRUCTOR_GUIDE.md, line 195

- **File:** `/home/claude/work/smo/docs/INSTRUCTOR_GUIDE.md` — L195
- **Says:** 'Breakpoints are used to:' list duplicated (updated 4-item list then old 3-item list, L195–205).
- **Should say:** Delete the old list.
- **Evidence:** Line checked.
- **French mirror:** `/home/claude/work/smo/docs/fr/INSTRUCTOR_GUIDE.md`

### Low severity

#### E1-4.18 · REPORTED (F1), line checked · Facilitator book (SpaceCDF course textbook), line 2377

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L2377
- **Says:** Ch. 2.1 puts References before Learning Objectives, unlike other chapters.
- **Should say:** Move References to the end.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.19 · CONFIRMED (F1, F5) · Facilitator book (SpaceCDF course textbook), line 32

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L32
- **Says:** Grammar: 'every formula students uses'; F5 L9197 'before students takes its CDF positions'; L10862 "students's PDR pack"; L11020 'a student in students'.
- **Should say:** 'students use'; 'before students take their positions'; "students' PDR pack"; 'a student in the cohort'.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.20 · CONFIRMED (F1) · Facilitator book (SpaceCDF course textbook), line 783

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L783
- **Says:** Table 1.2.1 lists 'CSA established 1990' after RADARSAT-1 (1995).
- **Should say:** Chronological order.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.21 · CONFIRMED (F1) · Facilitator book (SpaceCDF course textbook), line 2244

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L2244
- **Says:** Typo 'Wertz et al.,;'; L2382 SMAD link points to space.com/smad; L1129 'ITAR Technology Transfer Agreement' (standard instruments are TAA / MLA).
- **Should say:** 'Wertz et al.;'; publisher link; 'Technical Assistance Agreement (TAA)'.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.22 · REPORTED (F2), line checked · Facilitator book (SpaceCDF course textbook), line 4585

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L4585
- **Says:** UniSat-1 power example: 'the link closes comfortably' (power budget, not a link); L4633 eclipse 'relatively short (36 min vs 35 min for SSO)' (36 is longer); 3U example illustrates inertia with 'a 1 kg 1U CubeSat' (L4531); Table 2.4.9 'Payload' row has 4 cells in a 5-column table (packet L1062).
- **Should say:** 'the power budget closes comfortably'; 'comparable (36 min vs 35 min)'; consistent spacecraft; add the missing cell.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.23 · REPORTED (F5), line checked · Facilitator book (SpaceCDF course textbook), line 10789

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L10789
- **Says:** Garbled sentence 'For a 1 Wh/cell at nominal voltage, capacity C = …'; first person 'my approximation' (L10659); 'kbps' (L10281).
- **Should say:** Rewrite; textbook voice; 'kbit/s'.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.24 · REPORTED (F5, O1) · Facilitator book (SpaceCDF course textbook), line 10338

- **File:** Drive `SpaceCDF/docs/course/facilitator_book_expanded.md` (local copy `/home/claude/work/drive_course/facilitator_book_expanded.md`) — L10338
- **Says:** Spelling 'EO-Sat-1' vs 'EOSAT-1' (here, ops book L2376 and elsewhere; the OER uses 'EOSat-3U' for a different spacecraft).
- **Should say:** Pick one spelling for the simulated spacecraft.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/facilitator_book_expanded.md` (local build `/home/claude/work/out/course_fr/facilitator_book_expanded.md`)

#### E1-4.25 · CONFIRMED (O1, W2) · ORBIT NORTH operations book, line 342

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L342
- **Says:** Double sign: 'Troll (Antarctica, −72.01° S)' and O'Higgins '−63.32° S' (L345); training_day1 L43 'Troll (-72° S)'.
- **Should say:** '72.01° S' (or −72.01°).
- **Evidence:** orbit.yaml lat −72.012.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.26 · REPORTED (O1, W2), line checked · ORBIT NORTH operations book, line 442

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L442
- **Says:** §5.20 prerequisite 'Chapter 6 (ground segment architecture)' (ground segment is §7.20); expected readings that do not match the topic at L438 (ITU RR Art. 21, RSSSA) and L524 (ECSS-M-ST-10C review gates, figure 'Gate sequence'); instructor book L231 (CDS Launch ICD; SMAD4 ch. 18) with stray title line L229.
- **Should say:** Fix the cross-reference and the reading lists.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.27 · REPORTED (O1), line checked · ORBIT NORTH operations book, line 2552

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L2552
- **Says:** Table numbering gaps 7.3 → 7.5, 7.6g → 7.12 → 7.14; 'Figure 7.3 (§7.1)' (L2552) and 'Figure 7.2' (L2698) refer to unnumbered figures; imported session numbers '5.20', '7.20 Chapter 20'; 'critical for Thursday' (L1197).
- **Should say:** Renumber; remove course-day references.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.28 · REPORTED (O2), line checked · ORBIT NORTH operations book, line 2975

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L2975
- **Says:** Malformed link `` `[http://localhost:9091/`.](http://localhost:9091/`.) ``; §8.3/8.4, §10.2/10.6/10.8 missing; L3098 'drill exercises are at the end (§9.7)' (drills are §9.2); 'Table 7.4' inside ch. 9 (L3183); LEOP expanded as 'Launch and Early Operations Phase' (L3759); 'The five LEOP procedures' with six rows (L3816); §10.11 'This chapter expands…' (L4088).
- **Should say:** Fix link; renumber; '§9.2'; 'Table 9.x'; 'Launch and Early Orbit Phase'; 'six'; 'This section'.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.29 · REPORTED (O3), line checked · ORBIT NORTH operations book, line 4761

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L4761
- **Says:** Ch. 11 numbering skips 11.2 and 11.6 (Table 11.2 sits under §11.5 with a deleted heading at L4758–4760); COM-006 jumps Step 3 → Step 9 (L5344); product size '4 MiB' / '4 MB' / '4 megabytes'; unit 'Whr' (L6269–6287); 'a level-1 caution' ambiguous (L5874).
- **Should say:** Renumber; one unit form (MiB, Wh); say 'severity-1' or 'autonomy level 1'.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.30 · CONFIRMED (O4a #5) · ORBIT NORTH operations book, line 7840

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L7840
- **Says:** No blank line between '**Full template:** see §9.5.' and the table — some renderers will not render the table.
- **Should say:** Insert a blank line.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.31 · CONFIRMED (O4b) · ORBIT NORTH operations book, line 9064

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L9064
- **Says:** 'Three things in the tree that predate no printing of this book' (awkward).
- **Should say:** 'Three things in the tree that are newer than every printing of this book'.
- **Evidence:** Line checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.32 · REPORTED (O5) · ORBIT NORTH operations book, line 9115

- **File:** Drive `SpaceCDF/docs/course/orbit_north_week3.md` (local copy `/home/claude/work/drive_course/orbit_north_week3.md`) — L9115
- **Says:** Ch. 15 tables numbered 15.0 / 15.0b before 15.1; unnumbered 'Table — …' captions in §15.5.
- **Should say:** Renumber 15.1 …
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/orbit_north_week3.md` (local build `/home/claude/work/out/course_fr/orbit_north_week3.md`)

#### E1-4.33 · CONFIRMED (W2) · Back cover, line 15

- **File:** Drive `SpaceCDF/docs/course/back_cover.md` (local copy `/home/claude/work/drive_course/back_cover.md`) — L15
- **Says:** 'the seven major subsystems' followed by eight items; L49–50 'Senior Lecturer … leading the School of Engineering Design and Teaching Innovation' — check the author's current title.
- **Should say:** 'eight'; confirm the title (Associate Professor?).
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/back_cover.md` (local build `/home/claude/work/out/course_fr/back_cover.md`)

#### E1-4.34 · REPORTED (W2), line checked · Week 3 pack — sim_leop_instructor.md, line 95

- **File:** `/home/claude/work/cdf/docs/orbit_north/week3/sim_leop_instructor.md` — L95
- **Says:** 'The five medium and hard scenarios' — table has four; student_procedure_quickref L17 'Twenty procedures' — 25 listed plus 2 optional; training_day1 L94–95 vs quickref L164: same URL labelled 'Mission Operations Reference Architecture (MOSE-IDP)' and 'Mission Operations Procedures'; training_day2 L179 'CCSDS Pus standards' (PUS is ECSS-E-ST-70-41C); peer_review_worksheets L49 'Read the worksheet after the shift'.
- **Should say:** 'four'; 'Twenty-five'; one label; 'ECSS PUS (ECSS-E-ST-70-41C)'; 'Complete the worksheet after the shift'.
- **Evidence:** Lines checked.
- **French mirror:** `cdf/docs/orbit_north/week3/fr/sim_leop_instructor.md` (not yet installed; staged at `/home/claude/work/xlate/W2/sim_leop_instructor/fr.md`)

#### E1-4.35 · CONFIRMED (D1a #10, D1b #3, #9) · SMO docs — PUS_SERVICE_REFERENCE.md, line 319

- **File:** `/home/claude/work/smo/docs/PUS_SERVICE_REFERENCE.md` — L319
- **Says:** Typo 'overspecc' (PUS L319, OPERATIONS_GUIDE L918, both inside code blocks); PUS L3/L1284 cite 'ECSS-E-70-41C' vs body 'ECSS-E-ST-70-41'; TOC anchors point at English slugs.
- **Should say:** 'overspeed'; 'ECSS-E-ST-70-41C'; add explicit `{#id}` anchors to headings.
- **Evidence:** Lines checked.
- **French mirror:** `/home/claude/work/smo/docs/fr/PUS_SERVICE_REFERENCE.md`

#### E1-4.36 · CONFIRMED (D1b #10, #13, #16) · SMO docs — LINK_BUDGET_AND_RATES.md, line 203

- **File:** `/home/claude/work/smo/docs/LINK_BUDGET_AND_RATES.md` — L203
- **Says:** 'see §4.3 — the EIRP is no longer a constant' (derivation is §4.2); L538–540 'so step 2 above is mandatory' (the beacon-clear step is step 3); L703 'closes anyway, by 30 dB' vs 29.1 dB worst case.
- **Should say:** '§4.2'; 'step 3'; 'by about 29 dB'.
- **Evidence:** Viewed L488–494, L536–541.
- **French mirror:** `/home/claude/work/smo/docs/fr/LINK_BUDGET_AND_RATES.md`

#### E1-4.37 · REPORTED (M2 #31, #40) · EOSAT-1 manual — commissioning_sequence_walkthrough.md, line 77

- **File:** `/home/claude/work/smo/configs/eosat1/manual/commissioning_sequence_walkthrough.md` — L77
- **Says:** Anchors `#phase-1--first-signal`, `#phase-7--sequential-power-on`, `#phase-9--aocs-mode-progression`, `#phase-12--star-tracker-commissioning` do not match the target headings ('Phase 1 — Spacecraft Activation' …) — broken in English already. installation_guide.md L160 `#service-ports` will break in FR.
- **Should say:** Fix the slugs; add explicit `{#id}` anchors.
- **Evidence:** Heading text.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/commissioning_sequence_walkthrough.md`

#### E1-4.38 · REPORTED (M2 #7, #9, #14) · EOSAT-1 manual — 10_commissioning_contingency_procedures.md, line 5

- **File:** `/home/claude/work/smo/configs/eosat1/manual/10_commissioning_contingency_procedures.md` — L5
- **Says:** L5 calls 09_leop.md the 'Commissioning Sequence Walkthrough'; L83/L451 'May require EVA intervention', 'operate on UPS backup' (CubeSat); L617 'Bit Error Rate Anomaly During Command Downlink' (commands are uplinked).
- **Should say:** 'LEOP chapter'; delete EVA/UPS; 'Command Uplink'.
- **Evidence:** Lines checked.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/10_commissioning_contingency_procedures.md`

#### E1-4.39 · REPORTED (M2 #19, #20) · EOSAT-1 manual — 12_time_and_clocks.md, line 222

- **File:** `/home/claude/work/smo/configs/eosat1/manual/12_time_and_clocks.md` — L222
- **Says:** Offset defined as `ONBOARD - SIM UTC` in a flight chapter whose text speaks of GROUND UTC; Appendix A headings numbered 12.1–12.4.
- **Should say:** `ONBOARD − GROUND UTC`; number A.1–A.4.
- **Evidence:** Lines checked.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/12_time_and_clocks.md`

#### E1-4.40 · CONFIRMED (M1) · EOSAT-1 manual — 00_mission_overview.md, line 294

- **File:** `/home/claude/work/smo/configs/eosat1/manual/00_mission_overview.md` — L294
- **Says:** Related-documents table cites `10_command_reference.md` (generated file is `09_command_reference.md`); 11_rf_simulation L231 labels TTC 'Section 06' (it is 05).
- **Should say:** Fix file name and section number.
- **Evidence:** manual/ directory listing.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/00_mission_overview.md`

#### E1-4.41 · CONFIRMED (M2 #36) · EOSAT-1 manual — software_architecture.md, line 544

- **File:** `/home/claude/work/smo/configs/eosat1/manual/software_architecture.md` — L544
- **Says:** Typo 'TTC (TeleTeleCommunications)'.
- **Should say:** 'TT&C (Telemetry, Tracking and Command)'.
- **Evidence:** Line checked.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/software_architecture.md`

#### E1-4.42 · CONFIRMED (M2 #39) · EOSAT-1 manual — installation_guide.md, line 189

- **File:** `/home/claude/work/smo/configs/eosat1/manual/installation_guide.md` — L189
- **Says:** Windows PowerShell example uses `netstat -tulpn | grep 8080` (Linux syntax).
- **Should say:** `netstat -ano | findstr :8080` (or `Get-NetTCPConnection -LocalPort 8080`).
- **Evidence:** Line checked.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/manual/installation_guide.md`

#### E1-4.43 · REPORTED (P2a, P2b, P3) · Procedure — contingency/ber_anomaly.md, line 136

- **File:** `/home/claude/work/smo/configs/eosat1/procedures/contingency/ber_anomaly.md` — L136
- **Says:** Garbled sentences split across `**Note:**`/`**TC:**` lines: ber_anomaly L136–137; no_telemetry_at_pass L159; eclipse_transition L71–72; obc_redundancy_switchover L88–89, L115–116 and a backtick span broken across L151–152; obc_bootloader_recovery L208 and progressive_load_shed L76 sentences ending in 'via'; overcurrent_response L112–114 merged list; battery_cell_failure Step 4 list starts at '2.'; bus_failure_switchover Step 4 'procedure complete' before Step 5; data_downlink Step 5a before Step 5 and post-condition 'Sf < S0' (steps define V/N); imaging_session L81 refers to a deleted teaching note; loss_of_attitude L25 comment 'disable non-critical heaters' on an OBC-heater-only command.
- **Should say:** Rejoin/rewrite each; renumber.
- **Evidence:** Packet P2a/P2b/P3 notes; lines checked where given.
- **French mirror:** `/home/claude/work/smo/configs/eosat1/i18n/fr/procedures/contingency/ber_anomaly.md`

#### E1-4.44 · REPORTED (OER3, OER4, OER5) · OER *Concurrent Spacecraft Design* — 23_appendix_tool.md, line 3

- **File:** `/home/claude/work/cdf/docs/oer/chapters/23_appendix_tool.md` — L3
- **Says:** Repository URL still the placeholder `<repository URL>`; ch. 11 problem 9 escaped `\$500` while other amounts are unescaped; ch. 16 header 'CER (FY2010 $K)' bare `$` can pair as maths; ch. 11 §11.7.2 L436 cites 'Figure 17.2' for the pass profile (XREF_NOTES says 17.1); ch. 18 L340 Problem 2 unclear wording.
- **Should say:** Insert the URL; escape consistently ('k$'); confirm the figure number.
- **Evidence:** Lines checked.
- **French mirror:** `/home/claude/work/cdf/docs/oer/fr/chapters/23_appendix_tool.md`

#### E1-4.45 · REPORTED (D2) · SpaceCDF — docs/course/3_week_syllabus_expanded.md, line 76

- **File:** `/home/claude/work/cdf/docs/course/3_week_syllabus_expanded.md` — L76
- **Says:** Cites 'NASA SEH 17 processes overview (see Figure 2)' — the document has no Figure 2; user_guide_expanded.md L538 glossary 'SCM — Space Mission Engineering (textbook)' (usually SME / New SMAD).
- **Should say:** Point to the course plan Figure 2.3; 'SME — Space Mission Engineering: The New SMAD'.
- **Evidence:** Lines checked.
- **French mirror:** `/home/claude/work/cdf/docs/course/fr/3_week_syllabus_expanded.md`

#### E1-4.46 · REPORTED (W1) · Learner workbook, line 4752

- **File:** Drive `SpaceCDF/docs/course/learner_workbook_expanded.md` (local copy `/home/claude/work/drive_course/learner_workbook_expanded.md`) — L4752
- **Says:** 'Building the right thing (V&V) is as important as designing it' conflates verification and validation; 'DOD' vs 'DoD' (L1659 …); UHF 9600 bps example assumes QPSK + r=1/2 (amateur UHF 9600 is GMSK/FSK, L2398).
- **Should say:** 'Building the thing right (verification) and building the right thing (validation)…'.
- **Evidence:** Lines checked.
- **French mirror:** Drive `SpaceCDF/docs/course/fr/learner_workbook_expanded.md` (local build `/home/claude/work/out/course_fr/learner_workbook_expanded.md`)

