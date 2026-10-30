# Errata packet EE: EOSAT-1 manual (EN and FR)

Paths are relative to `/home/claude/work/smo/configs/eosat1/`: EN is `manual/`, FR is `i18n/fr/manual/`. Each fix is mirrored in FR. mdparity passes on all 17 touched pairs. `tools.i18n status` [manual] shows 19 of 19 in sync. The 13 `check` errors are all in FR procedure cards from another packet; none are in the manual.

Generator: `09_command_reference.md` is generated and was not hand-edited. `tools/gen_command_reference.py` was changed. It now writes the FR `06_payload.md` settings block from `i18n/fr/db.yaml`. Labels are cut at the first sentence, so "…3 (CALI" no longer appears. It also adds the classification and regenerate-command lines. `gen_command_reference.py --check` passes for EN, FR 06 and 09.

Tests (`tests/test_content tests/test_i18n`):
- Before (main tree, start of packet): 10 failed.
- After: 13 failed.
- Removed: `test_reference_exists_and_is_marked_generated` and `test_regeneration_is_a_no_op`.
- Added, none from this packet: 3 × `test_regeneration_is_byte_stable` (they also fail on a clean HEAD worktree because the generated xtce/smdl/PARAMETER_MAP revision stamps are stale), `test_command_services_matches_the_extracted_steps[CTG-002]` and `test_i18n_check_has_no_errors` (FR procedure files from another packet).
- The gonogo mirror tests pass (7). Generated files were restored with git checkout.

E1-1.05 | FIXED. §11.1 now uses `S2_AOCS_GPS_RECEIVER(device_id=0x020F, state=1)` (S2.1). Verify `gps_fix` 0x0274, `gps_num_sats` 0x0276, `gps_alt` 0x0212 ≈ 513 km. All IDs verified in tc_catalog/parameters.yaml | commissioning_sequence_walkthrough.md
E1-1.06 | FIXED. `AOCS_SET_MODE(mode=4)` NOMINAL at §5.1 and §5.3; SAFE_POINT changed to COARSE_SUN | 08_fdir.md
E1-1.07 | FIXED. mode=4 NOMINAL (Step 10, checklist); SAFE_POINT changed to COARSE_SUN (mode 3). Also: COARSE_SUN points +X at the Sun (aocs_basic.py att_error = sun-to-+X), not +Y | 09_leop.md
E1-1.17 | FIXED. `ST_SELECT(unit=1)`, data byte 1 | commissioning_sequence_walkthrough.md
E1-1.22 | FIXED. `OBC_BOOT_APP` (func 55) in the §5.2 table, §6.1 and §10.2. SW_UPLOAD/SW_ACTIVATE removed (not in the catalogue). The table now lists the real bootloader subset. Beacon interval "100 s" changed to 30 s (§5.1 says 30 s) | 09_leop.md
E1-1.23 | FIXED. §3.1, §3.3, §3.4 and the BOOTLOADER table now use OBC_BOOT_APP and the real subset (engine.py L2877) | 04_obdh.md
E1-1.24 | FIXED. §4.3 no longer uplinks SET_TIME in the bootloader; time is set after OBC_BOOT_APP (LEOP-006). Same note in the 00 §6.0 interlock list | 09_leop.md, 00_mission_overview.md
E1-1.27 | FIXED. §16.3 now declares phase 5 then 6 with SYS_SET_MISSION_PHASE (func 120). Also §3.1: the phase advances 3 → 4 on boot (it said "from 0") | commissioning_sequence_walkthrough.md
E1-1.34 | FIXED. All 36 links were relabelled with the target file's own heading ID (checked automatically). The 18 bare in-text IDs (L55, 129, 143×2, 173, 201×2, 231, 291, 347, 393×2, 421, 539, 613, 641, 685) were remapped with the same old→new permutation | 10_commissioning_contingency_procedures.md
E1-1.37 | FIXED. On-board antenna failures (Phase 2, both failures) now route to CTG-019 (no_telemetry_at_pass.md, which covers TTC_DEPLOY_ANTENNA), with a note that CTG-020 is the ground-station card | 10_commissioning_contingency_procedures.md
E1-1.38 | FIXED. Changed to "S9.1 (`SET_TIME`) command rejected" | 10_commissioning_contingency_procedures.md
E1-1.39 | FIXED. The stale S8 list was replaced by the real per-domain ranges plus a pointer to 09_command_reference.md. The S19 example now uses funcs 40/26/43/41/0 with true names; its file path changed to `monitoring/s19_rules.yaml` and it is marked schematic. The positions block now shows seven positions with the positions.yaml ranges | software_architecture.md
E1-1.77 | FIXED. Escalation table: CTG-023/003/002/004/010/011 → EMG-002 Total Power Failure / EMG-004 / EMG-005 / EMG-006 Thermal Runaway / EMG-003 / EMG-003. The CON-xxx/PROC-*-OFF-xxx family also ran through every desk table in the chapter (49 occurrences, none existing anywhere in the tree). All were relabelled to the CTG card with the matching title. The GO/NO-GO section has no such IDs, so gonogo_matrix.yaml was unchanged; the mirror tests pass | 10_desk_procedures.md
E1-2.34 | FIXED. Successive tracks are ~2 630 km apart at the equator; the 5-day grid spacing is ~525 km (40 075/15.24, /5) | 07_orbit_ops.md
E1-2.35 | FIXED. Step 7.3 is now ~40 W (OBC 6, RX 1.5, TX 11, heaters 9, wheels 12; the per-unit values come from 01 §3.1 / eps.yaml). Phase 4 ~20 W (OBC 15 + RX 5) changed to ~8 W | commissioning_sequence_walkthrough.md
E1-3.01 | FIXED. SAFE_POINT changed to COARSE_SUN (3), NADIR_POINT to NOMINAL (4); TARGET_TRACK removed (06 now requires NOMINAL (4) or FINE_POINT (5)). Checked against aocs_mode_codes.yaml; engine safe-mode callback = mode 3 | 00, 01, 03, 04, 06, 07, 08, 09_leop
E1-3.02 | FIXED. Single-string magnetometer in the 00 table and redundancy table, and in the software_architecture model list | 00_mission_overview.md, software_architecture.md
E1-3.03 | FIXED. Propulsion described in 02 §1, 07 §5 and §6 (1U LMP-103S blowdown, 0.400 kg, ~67 m/s, funcs 108–118; CAM + limited drag make-up, not deorbit), all from prop.yaml | 02_aocs.md, 07_orbit_ops.md
E1-3.04 | FIXED. The 03 note now describes HEATER_OBC (func 41, 0x040B, 4 W, line 6, 5/10 °C) and HEATER_THRUSTER (func 42, 0x041B, 12 W) | 03_tcs.md
E1-3.05 | FIXED. S-band 2025/2200 MHz plus a UHF beacon. 05 station antennas changed from "3.7 m VHF/UHF" to 9.0 m / 7.3 m S-band (planning/ground_stations.yaml). The 07 ranging transponder and the 09_leop GS configuration are S-band | 00, 05, 07, 09_leop
E1-3.06 | FIXED. 100 Wh, 3 Ah, 8S1P, 21.5–29.2 V, 26.4 V model / 28.8 V datasheet (eps.yaml) | 00_mission_overview.md, 01_eps.md
E1-3.09 | FIXED. Five cell-carrying faces (−Z none), 0.120 m² wings, 0.198 → 0.438 m² (sums checked) | 00, 01, 03, 09_leop, software_architecture
E1-3.10 | NEEDS-FRANZ. Which body-frame convention should the manual use? eps.yaml puts the imager/radiator on −Z, but 00/02/06 put the payload on +Z = nadir, and 01 §2.1 makes +Z orbit-normal | none
E1-3.11 | FIXED. 00 table: ~89 W peak (BOL), ~29 W average, OBC 6 W. 03 radiator dissipation ~80 W changed to ~29 W; cooler changed to 15 W. 06 IMAGING changed from ~25 W to ~20.5 W (15 W cooler + 5.5 W imager, eps.yaml) | 00, 03, 06
E1-3.18 | FIXED. Mode 3 CALIBRATION added to the 06 §3 table, the TM row and the command row (the PUS reference belongs to another packet) | 06_payload.md
E1-3.21 | FIXED. 00 §6.0 now says S9.1 passes the bootloader acceptance gate but fails at execution until OBC_BOOT_APP. 12_time was already right | 00_mission_overview.md
E1-3.22 | FIXED. The func-69 caveat was replaced with the real subset {19, 20, 52–57, 61, 66, 67, 69, 120} (engine.py L2877) | commissioning_sequence_walkthrough.md
E1-3.23 | FIXED. spacecraft_phase changed to 3 (BOOTLOADER_OPS). obc_mode reads 0 but is "not a boot indicator — read `sw_image`" (obdh_basic.py: mode defaults to 0; the bootloader is shown by sw_image) | commissioning_sequence_walkthrough.md
E1-3.24 | FIXED. The fix progression is now 0 → 1 (2D) → 2 (3D) → 3 (3D+vel) | commissioning_sequence_walkthrough.md
E1-3.25 | FIXED in part. TM format changed to a 9-octet secondary header with data at 15. The config example changed to time_epoch J2000, pus_version 2, dry mass 12.0 (mission.yaml/prop.yaml). The beacon is every 30 s (was 10 Hz) at two places. NEEDS-FRANZ: rewrite of the remaining chapter (Redis IPC/message bus, which no package uses; the architecture diagram, file tree, TTC modulation/rates, contact conditions, HK rates) | software_architecture.md
E1-3.26 | FIXED (verified REPORTED). Coarse+fine CUC; one auto-boot statement (10 s unless OBC_BOOT_INHIBIT, obdh_basic.py L923); both OBC units on unswitchable `obc` line 0; 05 RX/TX lines changed to `ttc_rx` line 1 / `ttc_tx` line 2 per 01 §2.3 | 04_obdh.md, 05_ttc.md
E1-3.27 | FIXED in part. "Receive-only in safe mode" was deleted (TM continues on LOW). The 5° worst-case margin changed from ~3 dB to 34.5 / 33.0 dB (LINK_BUDGET_AND_RATES). NEEDS-FRANZ: TTC-01 auto-switch after 120 s (05 §8) or 24 h (08 §4.5)? Neither, nor the RSSI −105/−100 dBm thresholds, exists in fdir.yaml/ttc.yaml or the simulator code | 05_ttc.md
E1-3.46 | FIXED. The §9 matrix `.yaml` names now point to the real procedures/contingency/*.md files. LEFT: the TCS-01/04 parameter pairs (both valid, as the entry says) | 08_fdir.md
E1-3.47 | FIXED. The FPA zone table now uses the derived bands (−22/14, −25.5/17.5; the predecessor edit matches §5). Cooler power 10–15 W changed to 15 W. NOT CONFIRMED: "cooler starts automatically" is correct, because service_dispatch drives the cooler line from PAYLOAD_SET_MODE ≥ 1. CALIBRATION was added to that sentence | 03_tcs.md
E1-3.48 | FIXED in part. §4 product size changed from "~50–200 MB / 10–40 images / 2 GB" to a 4 MB raw frame (1.0–2.7 MB stored), ~5 000 frames and a 20 000 MB payload store (payload.yaml). LEFT: GSD ~33 m vs ~33.4 m is rounding (computed 33.39 m from 5.5 µm / 84.5 mm at 513 km); the ops-book values are another packet | 06_payload.md
E1-3.49 | NEEDS-FRANZ. Is EO-Sat-1 meant to be dawn–dusk? The orbit.yaml TLE (RAAN 120° at 2026-08-20) gives LTAN ≈ 10:00 and β −13° to −43° through 2026 (sgp4). That matches eps.yaml's "worst beta 49.8°" and 01's β 24/50°, not "06:00/18:00 dawn-dusk". 00/07 LTAN rows and 07 §3 need an owner decision before the eclipse text is rewritten | none
E1-3.100 | LEFT (NOT CONFIRMED: five stations is correct) | none
E1-4.37 | FIXED (EN). The 9 broken walkthrough anchors now use the 10_cc heading slugs. NEEDS-FRANZ: FR anchors still point to EN slugs. mdparity requires identical link targets, and `{#id}` heading ids would fix both languages, but the MCS renderMarkdown prints `{#…}` literally and tools.i18n re-keys sections. Should `{#id}` be added and the renderer taught to strip it? The installation_guide `#service-ports` link has the same FR issue | commissioning_sequence_walkthrough.md
E1-4.38 | FIXED. L5 now names `commissioning_sequence_walkthrough.md`: the phase list (0–16, "Set Time", etc.) is the walkthrough's, so the file was wrong, not the title. The EVA and UPS sentences (L83, L451) were deleted. "Command Downlink" changed to "Command Uplink" (the heading and its i18n section id were re-keyed) | 10_commissioning_contingency_procedures.md
E1-4.39 | FIXED. Offset now `ONBOARD - GROUND UTC`; Appendix headings are now A.1–A.4 (sidecar ids re-keyed) | 12_time_and_clocks.md
E1-4.40 | FIXED. 10_command_reference.md changed to 09_command_reference.md; 11_rf "Section 06" changed to 05 | 00_mission_overview.md, 11_rf_simulation.md
E1-4.41 | FIXED. "TT&C (Telemetry, Tracking and Command)" (heading; sidecar id re-keyed) | software_architecture.md
E1-4.42 | FIXED. `netstat -ano | findstr :8080` (identical fence in FR) | installation_guide.md

## New findings (not in ENGLISH_ERRATA), left for Franz
- NEW-1 | NEEDS-FRANZ. The OBC mode model disagrees with the tree. 04 §3 defines OBC mode 2 = BOOTLOADER, and 04 §3.2 (beacon obc_mode = 2), §3.4, 09_leop §4.2 ("2 (BOOTLOADER) — concern if any other value") and 08 §9 ("mode=2") all rely on it. In the tree, OBC_SET_MODE gives 0 = nominal, 1 = safe, 2 = emergency, and the simulator reads 0 in the bootloader, where `sw_image` 0x0311 = 0 is the indicator. Should the manual be rewritten to sw_image, or is 2 = EMERGENCY to be documented? | 04, 08, 09_leop
- NEW-2 | NEEDS-FRANZ. 07 §6 ballistic coefficient ~200 kg/m² and lifetime ">7 years at 450 km" vs prop.yaml B = 77.9 kg/m², 1.7–4.8 yr (itself flagged for re-derivation at 513 km) | 07_orbit_ops.md
- NOTE | 06 §4 "Mass Memory Total 2 GB" was replaced by the 20 000 MB payload image store (payload.yaml total_storage_mb). 04 still gives the OBC mass memory as 2 GB per unit, which is a different store | 06_payload.md
