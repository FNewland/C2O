# Errata packet EF: SMO operations procedures (EN and FR)

Paths are relative to `/home/claude/work/smo/configs/eosat1/`. Every EN fix is mirrored in `i18n/fr/procedures/`. mdparity passes on all 54 touched pairs. `tools.i18n status`: [procedures] 67 of 67 in sync. `tools.i18n check`: 0 errors. The parser (`smo_common.procedures.markdown_steps`) extracts identical step lists from EN and FR on all 67 cards, with 0 TC_DROPPED / ACTION_INERT / BAD_BRANCH.
Tests (`tests/test_content tests/test_i18n`): 13 failed at the 19:41 baseline and 11 failed both at this session's resume point and after these edits. No new failures. The same 11 pre-existing ids remain: generated exports ×3, modern_inventory ×2, parameter_chain ×2, procedure_audit_gate PARAM_NOT_REACHABLE + uncategorised, and s19 rules 4001/4003. `tools/procedure_audit.py` reports 114 findings both at HEAD and now. Generated files were restored with git checkout.
`procedure_index.yaml`: only the derived `command_services` changed (CTG-002, CTG-007, CTG-026: [3, 8, 20] → [3, 8], because the invalid SET_PARAMs were removed). No title or ID changed, so no overlay update or extract/build was needed.

## Errata lines
E1-1.01 | FIXED (AOCS_3W_MODE func 5 → note: AOCS_DISABLE_WHEEL func 2 from Step 2 is the whole 3-of-4 isolation; table row → AOCS_DISABLE_WHEEL/AOCS_ENABLE_WHEEL. Also the Step 7 `SET_PARAM(aocs.wheel_config)`, a non-existent parameter, became a note) | contingency/aocs_actuator_stuck_recovery.md
E1-1.02 | FIXED (reboot cause decoded 1=commanded, 2=watchdog, 3=memory, 4=switchover; Step 2 branches re-routed and encoded as BRANCH) | contingency/boot_loader_recovery.md
E1-1.03 | FIXED (same decoding, Step 2 branches encoded) | contingency/obc_bootloader_recovery.md
E1-1.04 | FIXED | contingency/obc_redundancy_switchover.md
E1-1.08 | FIXED (aocs.mode = 4 NOMINAL) | nominal/routine_health_check.md
E1-1.09 | FIXED (4 NOMINAL / 3 COARSE_SUN) | contingency/solar_array_degradation.md
E1-1.10 | FIXED | contingency/solar_panel_loss_response.md
E1-1.11 | FIXED | contingency/progressive_load_shed.md
E1-1.33 | FIXED (MAG_SELECT removed; single magnetometer, power-cycle via S2 device 0x0209) | contingency/aocs_actuator_stuck_recovery.md
E1-1.46 | FIXED (T-300 / T-120 / T) | nominal/orbit_manoeuvre_planning.md
E1-1.47 | FIXED (HK_REQUEST S3.27 one-shots, SAVE_CONFIG deleted; Step 5 also requests SID 4 for the OBDH counters it verifies) | nominal/hk_configuration.md
E1-1.48 | FIXED (8 segments, index 0–7, 2,500 MB each, 12.5 %; thresholds > 1 / > 2 of 8) | contingency/memory_segment_failure.md
E1-1.49 | FIXED (blue_ms/green_ms/red_ms/nir_ms) | commissioning/first_light.md
E1-1.50 | FIXED (0x0604 store_used %, 0x0605 image_count baseline, 0x0603 imager_temp; Step 6 reads 0x0604) | commissioning/first_light.md
E1-1.51 | FIXED (TC counters 0x0304/0x0306/0x0307, reboot cause 0x0316 = 0, OBC_MEMORY_SCRUB func 51, no counter reset; the 0x0304 EDAC and 0x0305 watchdog reads are under Needs-Franz) | commissioning/obdh_checkout.md
E1-1.52 | FIXED ([21.5 V, 29.2 V], 8S 100 Wh 3 Ah, nominal 26.4 V; wing currents 0x0146/0x0147) | commissioning/eps_checkout.md
E1-1.53 | FIXED (Verify `obdh.mode <= 1`) | leop/time_sync.md
E1-1.54 | FIXED (HK_ENABLE sid=6) | emergency/obc_reboot.md
E1-1.55 | FIXED (HK_REQUEST sid=6) | contingency/ttc_link_loss.md
E1-1.56 | FIXED (sid=6 line → sid=5 payload, duplicate removed) | contingency/corrupted_image.md
E1-1.57 | FIXED (second line → sid=3 TCS) | contingency/progressive_load_shed.md
E1-1.58 | FIXED (OBC_DIAGNOSTIC func 61, then OBC_REBOOT func 52 if FD authorises) | emergency/emergency_safe_mode.md
E1-1.59 | FIXED (TCS = SID 3 in prereq/Step 3/Step 5, plus SID 1 in Step 3 for bat_soc; off_temp = on_temp + 5 °C) | contingency/thermal_exceedance.md
E1-1.60 | FIXED (Payload SID 5, TCS SID 3; stale sid=6/sid=4 lines merged) | contingency/payload_anomaly.md
E1-1.61 | FIXED (aocs.mag_x/y/z; aocs.mag_enabled 0x025C) | contingency/aocs_actuator_stuck_recovery.md
E1-1.62 | FIXED (0x040B tcs.htr_obc) | commissioning/tcs_verification.md
E1-1.63 | FIXED (thruster catbed heater is already OFF and manual in LEOP, so HEATER_THRUSTER(on=0) saves nothing; the ineffective command was dropped, no new load-cut invented) | leop/solar_array_verification.md
E1-1.64 | FIXED (CTG-002 Step 7, both places) | contingency/aocs_actuator_stuck_recovery.md
E1-1.65 | FIXED (CTG-002, CTG-008) | contingency/aocs_sensor_loss_recovery.md
E1-1.66 | FIXED | contingency/obc_bootloader_recovery.md
E1-1.67 | FIXED (CTG-002 AOCS; CTG-001 Under-Voltage Load Shed) | contingency/solar_panel_loss_response.md
E1-1.68 | FIXED | contingency/progressive_load_shed.md
E1-1.69 | FIXED (CTG-011 OBC Redundancy Switchover) | contingency/no_telemetry_at_pass.md
E1-1.70 | FIXED (LEOP-007 order / CTG-023 restoration) | contingency/thermal_exceedance.md
E1-1.71 | FIXED (CTG-010 only) | contingency/ttc_link_loss.md
E1-1.72 | FIXED (CTG-004 (Thermal Exceedance)) | contingency/propulsion_anomaly.md
E1-1.73 | FIXED (NOM-007) | nominal/routine_health_check.md
E1-1.74 | FIXED (LEOP-004 → COM-005 / COM-013 in Step 5 and References; EMG-005 retitled Loss of Attitude) | contingency/gps_time_sync_recovery.md
E1-1.75 | FIXED (COM-011) | commissioning/fpa_cooler_activation.md
E1-1.79 | LEFT (NOT CONFIRMED: reference resolves) + NEEDS-FRANZ (Which bootloader card is canonical: CTG-018 or CTG-021?) | —
E1-1.83 | FIXED (duplicate TTC_SET_DATA_RATE removed) | contingency/ber_anomaly.md
E1-3.07 | FIXED (labelled TCs made runnable `**TC:**` lines behind BRANCH/GO-NO-GO forks: CTG-004 battery/OBC cold, FPA/battery hot; CTG-010 conditional OBC_BOOT_APP; CTG-007 recovery → AOCS_ENABLE_WHEEL func 3; CTG-001 Step 7 restore list → 4 TCs with 5-min GO/NO-GO pauses; CTG-012 merged list). CTG-004's `SET_PARAM(obdh.task_shed)` stays non-runnable, see Needs-Franz | contingency/thermal_exceedance.md, obdh_watchdog_recovery.md, reaction_wheel_anomaly.md, undervoltage_loadshed.md, overcurrent_response.md
E1-3.16 | FIXED (+5 / +10 °C, GO/NO-GO > +5 °C) | emergency/total_power_failure.md
E1-3.19 | LEFT + NEEDS-FRANZ (The ground truth disagrees with itself. tc_catalog labels mode 4/8 NOMINAL_NADIR / ECLIPSE_PROPAGATE, while aocs_mode_codes.yaml says NOMINAL / ECLIPSE. Which labels are canonical?) | —
E1-3.28 | FIXED (Step 8 + post-condition: MCS 10° warning is a ground rule, no on-board rejection; same stale "elevation gate" also removed from CTG-018/CTG-021 Step 3a notes and NOM-011 contingency) | commissioning/ttc_link_verification.md (+ contingency/boot_loader_recovery.md, obc_bootloader_recovery.md, nominal/data_rate_change.md)
E1-3.29 | FIXED (st_selected = 2 and st1_num_stars = 0; same fix applied to CTG-025 Step 2c) | contingency/star_tracker_failure.md, aocs_sensor_loss_recovery.md
E1-3.30 | FIXED (AOCS_DISABLE_WHEEL func 2; func_ids added: AOCS_DESATURATE 1 in CTG-002/CTG-007, PAYLOAD_SET_MODE 26 and OBC_SET_MODE 50 in CTG-005, OBC_SET_MODE 50 in CTG-010) | contingency/aocs_anomaly.md, reaction_wheel_anomaly.md, eps_safe_mode.md, obdh_watchdog_recovery.md
E1-3.31 | FIXED in part (time fix → SET_TIME S9.1 / OBC_GPS_TIME_SYNC func 80; "CON" → "CTG") + NEEDS-FRANZ (One drift threshold for CTG-010: 2 s, 5 s as in CTG-021, or the 1 s of NOM-008?) | contingency/obdh_watchdog_recovery.md
E1-3.50 | FIXED (rate_roll/pitch/yaw 0x0204–0x0206) | contingency/gps_time_sync_recovery.md
E1-3.51 | FIXED (FPA_COOLER(on=1) func 43) | contingency/payload_anomaly.md
E1-3.52 | FIXED (prereq ~2.4 W standby + cooler later; Step 8 SID 3; Step 9 and off-nominal no firmware/self-test; exit: SID 5 on request, periodic SID 5 enabled by NOM-005) | commissioning/payload_power_on.md
E1-3.53 | NEEDS-FRANZ (COM-003: tracker-in-COARSE_SUN vs Step 4 precondition, the uncommanded "300 s of NOMINAL", the 0.10 °/s Step 6 gate wheels-off, and the "Revision 2.0" heading need an author ruling) | —
E1-3.54 | FIXED in part (LEOP-001 purpose no longer claims time sync; exit-state disabled SIDs 2/5/7/8/9/12; Step 5a hand-off reworded; LEOP-002 entry SIDs 1/3/4/6/11) + NEEDS-FRANZ (Which band is right: LEOP-003 [400, 550] or [495, 540] km, and LEOP-004 bus [27.0, 29.5] or [26.0, 30.0] V?) | leop/first_acquisition.md, leop/initial_health_check.md
E1-3.55 | FIXED in procedure (COM-004: < 3 of 4 wheels = no 3-axis control; < 2 trips FDIR, per fault_propagation.yaml and aocs_basic.py). The manual lines belong to the manual packet | commissioning/aocs_actuator_checkout.md
E1-3.56 | NEEDS-FRANZ (EMG-002 survival load: the table sums to 45 W but Steps 5/6 use 32 W. Which is it?). Battery capacity "~120 Wh" corrected to 100 Wh (~19 %) | emergency/total_power_failure.md
E1-3.57 | FIXED (FPA at setpoint ≤ −10.0 °C) | nominal/imaging_session.md
E1-3.58 | FIXED (~10.5 dB = 9.03 + 1.5 coding) | nominal/data_rate_change.md
E1-3.59 | FIXED (SIDs 1 and 11 come back after reboot) | nominal/hk_configuration.md
E1-3.60 | LEFT (not a contradiction: Step 5 forbids commanding a mode after a completed desat, while the off-nominal line is a mid-desat abort, and commanding a mode is the only abort path) | —
E1-3.61 | FIXED in part (no load session; recovery 1 "re-upload, do not boot"; no "region cleared") + NEEDS-FRANZ (Is the post-condition "previous image retained in alternate bank" true, given that Recovery Action 2 re-uploads and only OBC-B holds its own image?) | nominal/software_upload.md
E1-3.62 | FIXED (cause 2 = watchdog) | emergency/obc_reboot.md
E1-4.43 | FIXED (ber_anomaly L136, no_telemetry L159, eclipse_transition L66/71, obc_redundancy_switchover ×3, obc_bootloader "via", progressive_load_shed "via", overcurrent merged list, battery_cell list numbering, bus_failure_switchover premature "complete", data_downlink post-condition Vf < V0, imaging_session teaching note, loss_of_attitude heater comment). The data_downlink "Step 5a before Step 5" order is LEFT: renaming the headings breaks the i18n section IDs | several

## Prose branching (22 EN cards flagged by _PROSE_BRANCH at HEAD)
Converted to **BRANCH:** / **LABEL:** / GO/NO-GO targets, mirrored byte-identically in FR (18): CTG-002, -003, -004, -009, -010 (Step 1b only), -013, -014, -015, -018, -019, -020, -021, -022, -024, -027, EMG-004, NOM-003, NOM-011.
Re-worded, because the prose was not a fork (the next step follows anyway) (2): LEOP-001 Step 5a hand-off, NOM-002 Step 5a.
Needs-Franz (2): CTG-025 and EMG-001, plus CTG-010 Step 5→6.
Unsafe flat executions now fixed include: CTG-022 sent both OBC_SELECT_BUS(1) and (0); NOM-011 sent both rate=1 and rate=0; CTG-002 ran recovery and then the DETUMBLE escalation; CTG-004 and CTG-014 commanded every hot/cold or PA arm in sequence.
FR workaround: the i18n tool's own check (tools/i18n/docs.py, forbidden FR wording) still rejects « passer à l'étape N » in any procedure, even when BRANCH structure is declared. Removing « l'étape N s'applique » therefore makes `i18n check` fail (37 errors), so the descriptive form was kept.

## Extra fixes (same defect classes, found while verifying)
- CTG-007 Step 3 and CTG-026 Step 7: `SET_PARAM(aocs.wheel_config)` names a parameter that does not exist. Both became notes, and command_services was updated.
- CTG-003: EMG-001 "(Loss of Communication)" changed to EMG-004 (4 places). NOM-001: CTG-001 "EPS Safe Mode" changed to CTG-005 (2 places). CTG-023: CTG-009 title aligned.
- CTG-025: dual-magnetometer (MAG-A/MAG-B) purpose, criteria and off-nominal text changed to describe the single unit.

## Needs-Franz (short)
1. CTG-025: L98 says to go to Off-Nominal if ST2 does not track, but L110 says Step 5. Which is right? Also, how should Step 5 choose among modes 4/3/2? As written, a flat runner sends all three.
2. EMG-001 Step 3: in DETUMBLE with rates not yet < 0.1 °/s, should the runner wait (and with what timeout) or go on to Step 4? Should "return to Step 7" during recovery be a bounded loop?
3. CTG-010 Step 5→6: the text sends "systemic" causes to Step 6 ("restore NOMINAL if in SAFE"). Should the fork be on obdh.mode == 1 instead?
4. CTG-004 OBC-hot and CTG-010 off-nominal use `SET_PARAM(obdh.task_shed)`, but no such parameter exists. What is the intended OBC-load reduction?
5. CTG-004 red limit and battery > 45 °C both "escalate to EMG-002" (Total Power Failure). Should that be EMG-006 Thermal Runaway?
6. CTG-008 off-nominal: after an AOCS safe-mode trigger, follow "CTG-005 (EPS Safe Mode Recovery)". Should it be CTG-002?
7. COM-012: the image volume "50–200 MB" and "file size > 10 MB" contradict the 4 MB frame (1–2.7 MB compressed).
8. COM-007: 0x0304 is read as "EDAC error count" and 0x0305 as "watchdog status", but they are tc_rx_count and tc_acc_count. No watchdog-status or EDAC parameter exists (0x031E mem_errors?).
9. E1-1.79, E1-3.19, E1-3.31 threshold, E1-3.53, E1-3.54 bands, E1-3.56, E1-3.61 fallback bank (see lines above).
