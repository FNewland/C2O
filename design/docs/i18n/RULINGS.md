# Author rulings on OPEN_QUESTIONS.md

Rulings Franz gave on 2026-10-30. Each one is applied in English and French, and in the simulator where it says so.

| Q | Ruling | Applies to |
|---|---|---|
| 1 | **513 km everywhere.** The books follow the simulator. GSD becomes 33.4 m and swath 273 km; every derived figure is recomputed. | Ops book, manual, OER/course where quoted |
| 2 | **LTAN 10:00 with eclipses.** This is the TLE as flown. Manual chapters 00 and 07 lose "dawn–dusk 06:00/18:00". | Manual 00, 07 and anything quoting it |
| 2b | **Inclination 97.45°**, the true SSO value for 513 km. It was 98.0°, which drifts the node time about 1.7 h per year. The TLE changes, so pass-time tests and any documented pass tables are re-baselined. | `orbit.yaml` TLE, tests, docs |
| 3 | **Decay figures from `prop.yaml`.** Ballistic coefficient 77.9 kg/m², natural decay 1.7–4.8 years from 513 km. This meets the 5-year disposal rule without a burn, so "no dedicated deorbit capability" stands. The manual's ~200 kg/m² and >7 years are wrong. | Manual, ops book |
| 4 | **Body +Z = zenith, −Z = nadir.** The imager and radiator are on −Z. `eps.yaml` already agrees (no cells on −Z). The attitude model's "+Z = nadir boresight" convention and manual chapters 00, 02 and 06 change to −Z nadir. | AOCS attitude frame, SADA comment, manual |
| 5 | **The bootloader is shown by `sw_image = 0`.** OBC modes stay 0/1/2 = nominal/safe/emergency, and the manual stops calling mode 2 BOOTLOADER. | Manual, procedures |
| 6 | **AOCS modes 4/8 are named NOMINAL / ECLIPSE**, as the telemetry decoder (`aocs_mode_codes.yaml`) has them. The command catalogue, manual and procedures change to match. | `tc_catalog.yaml`, planner activity types, manual 09, procedures, tests |
| 7 | **Transponder auto-switch is a 24 h command-loss timer.** The 120 s figure goes. The timer value (and one RSSI threshold) go into `ttc.yaml` so docs and simulator agree. | Manual 05/08, `ttc.yaml` |
| 8 | **EOSAT-1** in every document and UI. "EO-Sat-1" goes. | All docs, EN and FR |

## B. Procedures (ruled 2026-10-30)

| Q | Ruling |
|---|---|
| 9 | **CTG-025.** Step 2b becomes `**BRANCH:** aocs.st2_status == 2 (timeout 120 s)`: GO selects ST2; NO-GO power-cycles ST2 once and then goes to Step 5. Step 5 becomes a branch chain: a tracker is valid → mode 4; else CSS valid → mode 3; else MAG enabled → mode 2; else hold and escalate. |
| 10 | **EMG-001.** Delete the commanded COARSE_SUN, because the simulator promotes DETUMBLE → COARSE_SUN at < 0.5 °/s held for 30 s. Step 3 becomes `**BRANCH:** aocs.mode == 3 (timeout 1800 s)`: GO → Step 4, NO-GO → EMG-005. "Return to Step 7" becomes a bounded loop, max 2. |
| 11 | **CTG-010.** End of Step 5: `**BRANCH:** obdh.mode == 1`, GO → Step 6. Step 4 always resyncs time (SET_TIME or OBC_GPS_TIME_SYNC) and then verifies `obdh.time_ref` ≠ 0 and drift < 1 s (NOM-008). |
| 12 | **No `obdh.task_shed`.** CTG-004 OBC hot: HEATER_OBC off, then OBC_SET_MODE(1). CTG-010 CPU > 90 %: OBC_SET_MODE(1) and verify that `cpu_load` falls. |
| 13 | **CTG-004 escalation** is a branch on the zone heater state: heater on → EMG-006, else EMG-001. |
| 14 | **CTG-008** AOCS safe-mode trigger → CTG-002. Add a note that the simulator may already have resumed mode 4. |
| 15 | **CTG-021 is canonical.** Repoint the six CTG-018 references and retire CTG-018 in `procedure_index.yaml`. |
| 16 | **COM-003.** Calibration moves after COM-004 (wheel-controlled NOMINAL) and keeps the 0.10 °/s gate. The 0x0A03 line becomes "wait for `est_source` bit 0". "300 s of NOMINAL" becomes the Step 10 five-minute check. The heading becomes "Revision history (1.0 → 3.0)". |
| 17 | **LEOP bands.** LEOP-003 keeps 495–540 km as the check and labels 400–550 km as the anomaly band. LEOP-004 bus becomes 26.0–30.0 V. |
| 18 | **EMG-002 survival table** is rebuilt from the simulator at about 20 W: OBC 6, RX 1.5, AOCS 4, battery heater 8 (TX 5 in a pass). Steps 5–6 use 20 W, eclipse drain is about 12 Wh, and the GO limit stays < 50 W. |
| 19 | **NOM-006.** Delete "previous image retained in alternate bank" and the `sw_version` verifies; reverting means re-uploading. |
| 20 | **COM-007.** Memory errors come from 0x031E and 0x0319. The watchdog is checked through the OBC_DIAGNOSTIC reply (byte 5 = 1) and re-enabled with OBC_WATCHDOG_ENABLE (func 59). The Step 6 TM counter is 0x0307, not 0x0312. |
| 21 | **COM-012.** An image is 4 MB raw and 1.0–2.7 MB stored. Step 6 checks the change in 0x060B, which must be 1.0–4.0 MB. "> 10 MB" goes, and "< 1 MB" becomes "< 0.5 MB". |
| 22 | **Ops book renumbered to simulator IDs** for both EMG and CTG cards. The old mapping table is kept only as a footnote. |
| — | **Simulator bug fix.** S19 rule `tcs_obc_overtemp_safe_mode` (ea 3003) calls S8 func 40 (HEATER_BATTERY) with no arguments. It must put the OBC in SAFE. |

## C. Course design (ruled 2026-10-30)

| Q | Ruling |
|---|---|
| 23 | **Week-2 Friday is a PDR-style review**; MCR is held informally on week-1 Friday. `3_WEEK_SYLLABUS.md:28` is fixed. The SpaceCDF Gate Review tab gets a gate selector (MCR/SRR/PDR, default PDR) driven by `configs/gate_exit_criteria.yaml`. |
| 24 | **Day 3 follows the books:** 3.1 Power & Thermal, 3.2 AOCS & Propulsion, 3.3 Comms, 3.4 Structure/OBDH, with orbit at 2.3. Both course plans are rewritten to match. |
| 25 | **MCS round-robin is 7 consoles × 15 min** plus 15 min of briefing. The workbook has 7 score cards: EPS and Thermal merged; AOCS and Orbit merged into Flight Dynamics; Ground Segment folded into TT&C; Propulsion added, along with a propulsion role analysis. |
| 26 | **Reading lists.** §5.20: OER ch. 18, ops book §5.2–5.5, ECSS-E-ST-70-11C, NASA Fault Management Handbook, NASA SEH App. S. §7.20: OER ch. 17, ops book §7.1/7.3, ECSS-E-ST-70C, CCSDS 130.0-G, NASA Small Spacecraft SoA (ground data systems). Instructor ch. 2: OER ch. 19, instructor ch. 5.10, ops book §8.1, ECSS-E-ST-70C. The misplaced boxes move to their sessions, and every clause and chapter number is verified against current editions. |
| 27 | **Placeholders.** Fill the 41 `[Claude Code: …]` placeholders from existing material, as cross-references where the text already exists. The 4 that need the author (peer-review worked example, MPS exercise, day-2 workshop figures, 15-question exam) become marked TODO boxes. |
| 28 | **WBS:** Bus 30 → 27 %, total 100 %. Re-render `fig_wbs_tree.py` (EN and FR). |
| 29 | **ATIR(D)** everywhere. Delete "ECSS uses IADT ordering". |
| 30 | **Test levels.** Sine: 5–100 Hz at 1.25 g, 3 axes, no displacement band; the example computes the crossover frequency. Random: GEVS workmanship, 6.8 grms; proto-flight is +3 dB (≈ 9.6 grms), 1 min/axis. TVAC proto-flight: qualification temperatures (predicted ±15 °C), 4 cycles, with the worked example recomputed. Add a note that the deployer or launcher user guide sets the binding levels. All values are verified against GSFC-STD-7000 and ECSS-E-ST-10-03C/31C before editing. |
| 31 | **Back cover:** "Associate Professor, School of Engineering Design and Teaching Innovation (SEDTI), University of Ottawa". The French uses the School's official French name (ECIPG), to be verified. |

## D. Tooling and publication (ruled 2026-10-30)

| Q | Ruling |
|---|---|
| 32 | **The OER's repository links point to the public C2O repository** (github.com/FNewland/C2O). The old repositories get a "moved" note. |
| 33 | **Explicit heading anchors `{#id}`** go in the EN and FR manuals and the PUS reference, with the same id in both languages. The MCS manual viewer hides them. |
| 34 | **Rewrite `software_architecture.md`** from the actual packages and ports, including smo-link and the GSG, in EN and FR. |
| 35 | **The French checker allows « passer à l'étape N »** when the card declares a matching `**BRANCH:**`. |

## Context decided the same day
- The combined repository is **C2O** (« Du Concept à l'Orbite » / "from Concept to Orbit"). It is public: one repository with full history, under the folders sim/, design/, portal/, deploy/ and docs/.
- The web address is **c2o.live**.
