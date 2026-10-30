# Errata packet EB: ORBIT NORTH ops book, ops workbook, instructor book and back cover (EN and FR)

Files are under `/home/claude/work/drive_mirror/` (EN) and `fr/` (FR). Part of this packet was already applied in the mirror when this run started (ST_SELECT, MAG_SELECT, phase telecommand, numbers, "this shift"). Every one of those edits was re-verified against the tree and its French mirror, and the rest was finished here. mdparity: the workbook, instructor book and back cover pass. The ops book fails only on the known waived "24 h/24" item (FR extra '24', '7' in ch. 10, the same as at HEAD). `tools.i18n accept` was run on all four FR files. `check` reports 1 error, and that error is the same waived ch. 10 "24 h/24" item.

E1-1.12 | FIXED. Table 7.6a now reads `ST_SELECT(unit=1/2)`, 1=ST1, 2=ST2, 0 refused (tc_catalog; aocs_basic refuses 0) | orbit_north_week3.md (EN+FR)
E1-1.13 | FIXED. COM-003 step 5 changed to `ST_SELECT(unit=1)` | orbit_north_week3.md
E1-1.14 | FIXED. CTG-008 decision tree and step 3 changed to `ST_SELECT(unit=2)` | orbit_north_week3.md
E1-1.15 | FIXED. CTG-025 decision tree and step 2 changed to `ST_SELECT(unit=2)` | orbit_north_week3.md
E1-1.16 | FIXED. Workbook CTG-008 sheet step 3 changed to `ST_SELECT(unit=2)` | orbit_north_week3_workbook.md
E1-1.26 | FIXED. Instructor book §5.10.0 rule rewritten: phases 5/6 are set with `SYS_SET_MISSION_PHASE` (func 120, FORCE flag), and `set_phase` is an instructor override. Workbook rows L563/L674/L1071 and ops book L375, §7.1 header, §10 intro, LEOP-007 step 8 and §11 were aligned | instructor_book.md, orbit_north_week3_workbook.md, orbit_north_week3.md
E1-1.29 | FIXED. COM-003 step 4 is now "verify the magnetometer: 0x025C = 1, 0x0277 25 000–65 000 nT", with no command (single-string unit, func 7 refused) | orbit_north_week3.md
E1-1.30 | FIXED. COM-013 step 1 changed the same way | orbit_north_week3.md
E1-1.31 | FIXED. CTG-025: MAG_SELECT branch and step replaced by the shipped procedure (power-cycle `S2_AOCS_MAGNETOMETER`, device 0x0209 = 521, per aocs_sensor_loss_recovery.md step 4). `mag_select` 0x0229 read removed. Table 7.6a func 7 marked retired. §15.5 MAG_SELECT row deleted (EN+FR) | orbit_north_week3.md
E1-1.32 | FIXED. `mag_failure` cue and debrief rewritten: single magnetometer, no switch; recognise the loss of B-dot/desaturation and protect momentum | instructor_book.md
E1-1.76 | FIXED. AOCS authority changed to "0–15, 84–91 and 96" (mcs/positions.yaml) in §6.3 and §7.7 | orbit_north_week3.md
E1-1.80 | LEFT (NOT CONFIRMED: NOM-008 text is correct) | none
E1-1.81 | FIXED. Changed to `EPS_POWER_ON(line_index=3)` | orbit_north_week3.md
E1-1.82 | FIXED. Changed to "AOCS, beginning ST1_POWER" | orbit_north_week3.md
E1-1.84 | LEFT (book matches the simulator; see E1-3.20) | none
E1-1.85 | LEFT (NOT CONFIRMED: −15 °C ≡ 25815 cK) | none
E1-1.86 | LEFT (NOT CONFIRMED: func 20/19 correct) | none
E1-2.17 | FIXED. Table 7.18 rows recomputed: 567–756, 135–270, 675–1013 MB | orbit_north_week3.md
E1-2.18 | FIXED. "≈1.75 h at HIGH (≈2.2 h with the 20 % allowance)", in both places (100.7e6·8/128e3 = 6294 s) | orbit_north_week3.md
E1-2.19 | FIXED. Changed to "two and a half percent" (2.5/100) | orbit_north_week3.md
E1-2.20 | FIXED. "a required COP of 1.50 (about 16 % of Carnot, inside the cooler's 23 %)", matching the tcs.yaml derivation (1.50 = 15.7 % of Carnot) | orbit_north_week3.md
E1-2.26 | FIXED. 26.6 % changed to 27 % (23 300/86 400) | orbit_north_week3.md
E1-2.27 | FIXED. arccos(0.93403) = 20.93° = 0.36526 rad, so t = 659 s. h = 450 km kept: it is the book's own example (see NEEDS-FRANZ E1-3.48) | orbit_north_week3.md
E1-2.28 | FIXED. The usable fraction is now stated: raw 23 300 s × 128 kbps ≈ 355 MiB/day, and about 64 % of it is usable → 227 MiB (28 MiB at LOW has the same ratio) | orbit_north_week3.md
E1-2.29 | FIXED. 1.55× changed to 1.57× (45.0/28.7) | orbit_north_week3.md
E1-2.36 | FIXED (errata verdict overturned). LEOP-007 step 2 *is* the battery heater (`EPS_POWER_ON(line_index=5)`), and the same section gives htr_bat nominal as 0.35 A (8 W heater in tcs.yaml), so "1.2 A (1.5× nominal)" contradicts it. Changed to "about 3.4× the 0.35 A nominal" | orbit_north_week3.md
E1-3.02 | FIXED (ops book + instructor parts). One magnetometer throughout: L124, L324, L960, Table 10.14 recovery, B-dot note, CTG-025 inventory and decision, EMG card, instructor scenario row | orbit_north_week3.md, instructor_book.md
E1-3.15 | FIXED. The MCS mock-up fpa_temp changed from −58 °C to −15.0 °C (EN+FR SVG) | orbit_north_week3.md
E1-3.20 | FIXED (book side). The CTG-027 step 4 note says event 0x020F is what the catalogue currently labels `AOCS_MODE_RESTORED`. The tree defect remains (service_dispatch.py L2008 emits 0x020F for the forced SAFE_BOOT, while event_catalog.yaml names 0x020F AOCS_MODE_RESTORED). It needs a code/catalogue fix outside this packet | orbit_north_week3.md
E1-3.32 | NEEDS-FRANZ (Renumber the ops book's EMG cards and about 50 references to the simulator numbering, which changes the card order, or keep the book's own numbering with its mapping table and the "this book's numbering" notes?) | none
E1-3.33 | LEFT (the instructor book is correct, 6 = NOMINAL; the defect is in breakpoint_spec, another packet) | none
E1-3.35 | FIXED (ops book and workbook part). "Voice-loop language declared": callouts in English (STYLE_FR §16 / R6). Training_day2 belongs to another packet | orbit_north_week3.md, orbit_north_week3_workbook.md
E1-3.48 | NEEDS-FRANZ (Ops book "30 m ground sample" changed to 29.3 m, which is fixed. But the whole ops book computes GSD 29.3 m, the 240 km swath and the examples at 450 km, while orbit.yaml is now 513 km, where the live model gives 33.4 m / 273 km. Move the ops book to 513 km?) | orbit_north_week3.md
E1-3.65 | FIXED, in the reverse direction from the errata. The MCS has no chat and no FD second key (verified in smo-mcs static/modern/mcs.js: ARM→SEND for criticality=critical only, 8 s quick-command arm; no chat code). Ch. 6 kept. §7.1 rewritten in place: chat section says there is none and that a text backup is being considered for the planned web-architecture work (no promise). Commanding panel input modes are catalogue / direct hex / quick commands. Steps are authority check, FD GO (voice), ARM (critical) and uplink. Logging covers the command history and verification log, with the FD GO not captured. The critical list now has five commands (`SYS_SET_MISSION_PHASE` added, per tc_catalog). The audio-alert line, Figure 7.1 SVG labels and caption were also aligned | orbit_north_week3.md
E1-3.66 | FIXED. Nine line currents with 0x014B wherever the book lists the currents (L1096, §7.7, §16.3, LEOP EPS playbook). The FDIR-panel sentence now says "lines 0–7", because mcs/alarm_procedures.yaml maps only 0x0118–0x011F to CTG-012 | orbit_north_week3.md
E1-3.67 | FIXED. "both stations" changed to stations in view / station in view (5 stations in orbit.yaml) | orbit_north_week3.md
E1-3.68 | FIXED. One timeout (30 s) in Table 10.8. Verification text now says S1.7 follows the ~10 s CRC check (also §14 LEOP-001 step 6) | orbit_north_week3.md
E1-3.69 | FIXED. LEOP-007 step 8 sends `SYS_SET_MISSION_PHASE(phase=5, flags=0)` | orbit_north_week3.md
E1-3.70 | FIXED. NOM-009 bus band changed to 27.0–29.5 V | orbit_north_week3.md
E1-3.71 | FIXED. NOM-012 table aligned with its note (step 1 `HK_REQUEST(sid=1…6)`, step 4 `LIST_SCHEDULE` S11.17, both in tc_catalog) | orbit_north_week3.md
E1-3.72 | FIXED. "closes at 5° on margin; we only plan it above 10° as a ground rule" | orbit_north_week3.md
E1-3.73 | LEFT (verified consistent: profile 20→−2, 30→−4, 35→−5, 60→−9 °C and actual −2, −2, −3, −4 °C are both monotonic. "2 C behind at 30 min", "0.05 vs 0.15 °C/min" and "floor −6.5 / margin −3.5 vs −10 °C setpoint" all agree) | none
E1-3.74 | FIXED. The Day 4 bulletin now switches to ST2 if the reset fails, with gyro propagation as the fallback | orbit_north_week3.md
E1-3.75 | FIXED. "against a 450-second pass, most of it above 10 degrees … little to spare" | orbit_north_week3.md
E1-3.76 | FIXED. 445 s changed to 447 s; shares recomputed to 73 % / 586 % | orbit_north_week3.md
E1-4.01 | FIXED. Instructor book: all 46 "this shift" restored to Day 3 / Day 4 / Day 5 from context (0 left). Ops book ch. 16 and L4805 restored. The remaining six ops-book uses (L857, L3078 heading, L3087, L3662, L5635 heading, L7424) read naturally and were left | instructor_book.md, orbit_north_week3.md
E1-4.12 | FIXED. "Part 5" changed to "Part 2" (ops book L80/365/380/415, instructor book L3 "Part 2 (CubeSat Operations)", workbook L8) | orbit_north_week3.md, instructor_book.md, orbit_north_week3_workbook.md
E1-4.13 | FIXED. The NPR 7120.5F title is corrected (L56, L429). ECSS-E-ST-70-01C "(Ground Segment)" changed to "(Spacecraft On-Board Control Procedures)" (§7.20 references and source). The L568 OBCP citation is left (it is about procedures) | orbit_north_week3.md
E1-4.14 | FIXED. Orphan table-header rows removed (none remain). CFMR is defined as "(final mission review)". "All 13" is correct (13 COM cards) | orbit_north_week3_workbook.md
E1-4.16 | FIXED in part. Heading changed to "Chapter 18 — Anomaly Cue Cards" and the stray title line under Chapter 2 removed. LEFT: the body-less headings L515–527, because the brief forbids removing headings | instructor_book.md
E1-4.24 | LEFT (EO-Sat-1 vs EOSAT-1 needs one global spelling decision across all packets) | none
E1-4.25 | FIXED. Changed to "72.01° S" and "63.32° S" | orbit_north_week3.md
E1-4.26 | FIXED in part. The §5.20 prerequisite now points to §7.20, and the instructor book's stray title line is removed. NEEDS-FRANZ: off-topic expected-reading lists (§5.20 ITU RR Art. 21/RSSSA; §7.20 ECSS-M-ST-10C + "Gate sequence" figure; instructor ch. 2 CDS Launch ICD/SMAD4 ch. 18). What should students read? | orbit_north_week3.md, instructor_book.md
E1-4.27 | FIXED in part. "Figure 7.3 (§7.1)" now reads the ground-segment architecture figure in §7.5, "Figure 7.2" now reads the protocol-stack figure in §7.2, and "critical for Thursday" now reads "critical for payload commissioning". LEFT: the ch. 7 table-number gaps and imported 5.20/7.20 session headings. smo/docs review/plan files cite Tables 7.5, 7.6a–f and 7.13 by their current numbers, and heading renumbering is out of scope | orbit_north_week3.md
E1-4.28 | FIXED in part. Both malformed MPS links changed to <http://localhost:9091/> (port verified in smo-planner). "§9.7" changed to "§9.2"; LEOP is now "Launch and Early Orbit Phase"; "five LEOP procedures" changed to "six"; "This chapter expands" changed to "This section". LEFT: missing §8.3/8.4/10.2/10.6/10.8 headings and Table 7.4 inside ch. 9 (structural/renumbering; same cross-reference reason) | orbit_north_week3.md
E1-4.29 | FIXED in part. "Whr" changed to "Wh", and "level-1 caution" changed to "FDIR level-1 (caution)". LEFT: the COM-006 Step 3→9 jump (the book uses the card's own step numbers), MB/MiB (each instance pairs consistently: 262 s ↔ MiB, 250 s ↔ MB) and the ch. 11 heading gaps | orbit_north_week3.md
E1-4.30 | FIXED. Blank line inserted before the NOM-012 table | orbit_north_week3.md
E1-4.31 | FIXED. Changed to "newer than every printing of this book" (the FR already said this) | orbit_north_week3.md
E1-4.32 | FIXED. Ch. 15 tables renumbered 15.1–15.13 (15.0/15.0b/15.1–15.3 shifted, and the eight unnumbered §15.5 captions numbered) | orbit_north_week3.md
E1-4.33 | FIXED in part. "seven" changed to "eight major subsystems". NEEDS-FRANZ: the author line says "Senior Lecturer … leading the School of Engineering Design and Teaching Innovation". Should it read "Associate Professor, School of Engineering Design and Teaching Innovation (SEDTI)", and is "leading the School" right? | back_cover.md
EXTRA | FIXED. FR ops book inline SVGs: both SVGs' human-readable `<text>` labels are in French (tab identifiers, parameter names, mnemonics and numbers kept). The broken `xmlns="[http://…"](…)"` attribute on both SVGs is repaired (EN+FR) | orbit_north_week3.md

Tests (smo, tests/test_content + tests/test_i18n): 10 failed, 2068 passed, 3 xfailed. Failures: test_modern_inventory ×2, test_parameter_chain ×2, test_procedure_audit_gate ×2, test_procedure_gates[CTG-002], test_s19_rules_content[4001/4003], test_i18n_gate (smo i18n: 14 errors). None of these come from EB: no smo file was touched and these tests do not read drive_mirror. The background 'before' run was lost, so there is no separate before list; the failures reflect smo files that other packets are editing in parallel. Generated files restored with git checkout. No smo file was touched by this packet. No procedure card was edited, so the parser equivalence check does not apply.
