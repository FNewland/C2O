# Worksheet ↔ screen audit — ORBIT NORTH week-3 ops workbook (2026-11-04)

Franz: "work through the worksheets with the screens to see what can be worked
out from the screens and what needs additional info — then add the additional
info where needed. If you need to link to open source sites outside the tool,
keep a list but add the links (open in new browser window). You will find the
worksheets and the tool pages do not yet line up well."

## What was audited, and how

**Worksheets.** Every question and field of the printed workbook
`design/docs/course/orbit_north_week3_workbook.md` (+ `fr/`) that the logbook
offers: the 43 sheets already generated into
`sim/configs/eosat1/worksheets/ops_week3.yaml`, plus five added to the
generated set by this audit because they are worked on the screens or by
observers at the consoles — **WB-5.1** position score cards, **WB-5.3-PP**
pass-plan exercise, **WB-5.5-OBS / WB-5.6-OBS** observer sheets and the
**WB-5.6-FPA** cool-down monitor sheet (48 sheets, 484 questions). The table
below is one row per question. The sheets the logbook does not offer are
audited at the end of this section.

**Screens.** The stack ran locally from the worktree (simulator, RF bridge in
FRAME mode, MCS modern UI, planner, delayed-TM viewer, orbit tools, radio
view, documentation viewer). The spacecraft was brought to a realistic
commissioned state with the instructor API (`set_phase 6`, pass override) and
ordinary telecommands from the MCS (`HK_ENABLE` of SIDs 2–6 and 12, S-band
chain on, antenna deployed, LOW rung, payload STANDBY, magnetometer / MTQ /
GPS / ST1 on, COARSE_SUN), then every MCS page (OVR, EPS, TCS, AOC, TTC, PLD,
PRP, OBD, CMD, FDR, PRC, TRD, PUS and its tabs, MAN, the bottom drawer), the
planner, orbit tools (after *Convert TLE*), radio view, delayed TM and the
documentation viewer were captured as screenshots and text and read against
each question. A question that names a parameter (`0xHHHH` or its name) was
checked against the operator dictionary the MCS serves
(`/api/param-catalog`: visibility `real` plus the station receiver's
readings) and against the page whose Parameters table lists it.

**Answerable?**
- *screen* — a tool screen shows it; **Where** names tool › page › panel (and
  the parameter row).
- *manual only* — only the manual or a procedure card (documentation viewer)
  says it.
- *not at all* — nothing in the system answers it.
- *n/a* — not a lookup: an observation, a decision, a reflection, a
  signature, room logistics.

The table is generated (`tools/gen_worksheets.py --audit`) from the
hand-maintained `sim/configs/eosat1/worksheets/worksheet_where.yaml`, the same
map that puts the **Where to find this** links on the questions in the
logbook's Workbook tab — so the audit and the links cannot disagree.
"before" is the state found on 2026-11-04 before any change below.

## Summary

| Answerable | before | after |
|---|---:|---:|
| screen | 301 | 314 |
| manual only | 31 | 30 |
| not at all | 15 | 3 |
| n/a | 137 | 137 |

The three left "not at all" are image-processing results (mean DN per band,
twice; cloud cover) that need a ground image quick-look tool: deferred.

## Screen additions (where the operator works; ground-legitimate only)

Every value below is downlinked telemetry, a ground computation on downlinked
telemetry, or the ground's own orbit prediction from the mission TLE — never
simulator truth (`test_operator_feed_denylist.py` passes).

| Screen | Addition | Source | Answers |
|---|---|---|---|
| MCS › EPS › Projections | **Next eclipse** (or *This eclipse*): entry–exit UTC and duration | MCS ground propagator (`OrbitPropagator.eclipse_window`, edges by bisection to 1 s), `/api/state.eclipse_window` | WB-5.1.2, COM-001 steps 4–5, COM-002 step 3 |
| MCS › EPS › Projections | **Orbit-average margin (in − out)**, W | the power-flow "This orbit" ground estimate ÷ the orbit period | COM-001 step 6, CTG-009 step 4 |
| MCS › TTC › Ground station network | elevation, **slant range and OWLT** of the station in contact | MCS ground propagator (`/api/state.gs_geometry`) — the panel used to read `ttc.contact_elevation` / `ttc.range_km`, which the operator dictionary does not carry, so it never showed a number | LEOP-006 step 2, WB-5.1.4 |
| MCS › PUS › S9 TIME | **One-way light time (ground geometry)** and **Δt = T_obc − (T_ground − OWLT)** | `time_correlation.owlt_ms`, `offset_lt_s` | LEOP-006 steps 2–3, NOM-008 |
| MCS › TTC › Projections | **Time to dump the stored image products** at LOW and HIGH | `payload.product_mb` (0x0647) ÷ the TM rate ladder | WB-5.3-PP downlink duration, COM-011 step 10 |
| MCS › AOC › GPS navigation | **\|r\|** (km) and **\|v\|** (m/s) | the six downlinked ECEF components, shown only with a 3D fix and fresh data | LEOP-003 step 3 |
| MCS › FDR › On-board monitoring (S12) | **Severity**, **Persistence** (repetition, consecutive 1 Hz checks) and **Procedure** (the contingency card an S12 alarm of that parameter opens, as a link) | `s12_definitions.yaml` severity / repetition; `alarm_procedures.yaml` through the alarm resolver | WB-5.1.6 (persistence, severity, recommended procedure), WB-5.5-PB |
| Orbit tools › Passes | **TCA** and **LOS** columns, to the second | TCA from a parabola through the elevation peak | WB-5.1.3, WB-5.3-PP, WB-5.4-FD |
| Orbit tools › Eclipses | new panel: every umbra window over 24 h, entry / exit / duration, **longest marked** | the suite's shadow model along the SGP4 track | WB-5.4-FD Ex. 3 |
| Orbit tools › Orbit at epoch | **LTAN** | RAAN against the Sun's right ascension | WB-5.0, LEOP-003 step 4 |
| MCS deep links | `#page=<rail id>&param=0xHHHH&focus=<id>&tab=<PUS tab>&bd=<drawer tab>` opens the page and marks the row/panel for 15 s | `mcs.js applyNavHash` (strict patterns on every value) | every "where" link |

**Defects found on the way and fixed**

- **Orbit tools RAAN off by +90°** (`atan2(n_x, −n_y)` instead of
  `atan2(n_y, n_x)`; the mission TLE's 120° showed as 210°) and an argument
  of perigee formula that scaled by |h|: both fixed. The LTAN check of
  LEOP-003 step 4 was impossible before.
- **Orbit tools state-vector mode treated the GPS ECEF state as inertial**
  (no GMST rotation, no Earth-rotation term): for EOSAT-1 the inclination
  came out 100.8° instead of 97.39° and the period 97.7 instead of
  94.6 min, so LEOP-003 step 4 ("i within 0.2° of 97.39°") always failed.
  Now ECEF→ECI with v_i = R(v_e) + ω×r.
- **MCS TTC ground-station row** read two parameters the console never
  receives (above) — now the ground geometry.

## Worksheet rewordings (EN and FR, printed workbook)

| Sheet | Was | Now |
|---|---|---|
| WB-5.1.1 | "GO/NO-GO round on the live dashboard" | the MCS **GO/NO-GO** tab (bottom drawer) |
| WB-5.1.2 | eclipse duration "(33.2–35.2 min over the year)", "Cross-check vs eclipse model", method in a broken bold span | read on EPS › Projections › Next eclipse; heater duties on TCS › Equipment; "Cross-check vs the console's prediction (EPS power flow, 'at eclipse exit')"; method as its own line |
| WB-5.1.3 | "compute AOS, TCA and LOS … compare with the MPS contact schedule" | read them in the Orbit tools pass list and compare with the planner's **Next contacts** |
| WB-5.1.4 | "Active station (`ttc.active_gs` 0x0523)", "Baseband config (rate, encoding)" | Station in contact (TT&C page, Ground station network); rate, symbol rate, coding (Radio view, Data link and Link budget) |
| WB-5.1.5 | "via MPS" | planner, **Imaging opportunities → Schedule** |
| WB-5.1.6 | "one FDIR rule on the FDIR panel"; "Rule name" | one monitor in the FDIR page's **On-board monitoring (S12)** table; "Monitor selected (Name column)" |
| WB-5.1.7 | role brief `configs/eosat1/mcs/role_analysis/propulsion_role.md` (not in the documentation viewer) | PRP page **Arm interlocks**; manual 07 §6 |
| WB-5.1 (layout) | fields whose label had no colon or spanned two lines ("In band?", "Will saturate?", "At setpoint?", star-tracker and prop-state rows) were lost by the generator; FR and EN had different shapes | one field per bold label; EN/FR shapes equal (the sheet is now generated) |
| WB-5.4-N012 row 6 | "Customer commitments active" (no tool has the concept) | "(imaging and downlinks booked in the planner)"; same on WB-B |
| WB-5.4-FD | Orbit Tools by command line and port; "MPS" columns | Orbit tools (**Use EOSAT-1 elements**, **Convert TLE**), AOS/TCA/LOS; "AOS (planner, UTC)", "Duration in the planner (min)" |
| WB-5.5-PB | "`ttc.beacon_active` 0x0527 = 1" (not in the operator dictionary) | beacon SID 11 arriving (PUS page, S3 HK, Observed column); same in the CTG-001 and CTG-019 notes |
| WB-5.5-L006 step 2 | "OWLT = `ttc.range_km` (0x0509) / c" (no HK SID carries 0x0509) | OWLT read on PUS › S9 TIME (ground orbit prediction); the LEOP-006 and NOM-008 **procedure cards** (EN + FR) corrected the same way |
| WB-5.5-HO, WB-5.6-HO | "Any pinned widget?" (neither console has pinned widgets) | "Console page left open for the next operator (page, panel)" |
| CTG-020 note | ground health "in `ttc.gs_equipment_status` (0x0524)" (instructor-only) | the station's own monitoring (radio view, station operator) |

The generator now refuses a question that names a parameter the operator
dictionary does not carry, unless the map lists it under `off_screen` with a
gap (none does).

## External links

Ten open references (ECSS PUS and operability, CelesTrak TLE format, ESA
orbit types, NASA small-spacecraft state of the art, five Wikipedia pages
where nothing better is open), each checked on 2026-11-04 and listed with its
reason and where it is used in [EXTERNAL_LINKS.md](EXTERNAL_LINKS.md). They
open in a new window (`target="_blank" rel="noopener noreferrer"`), https
only — enforced by the logbook server, by `where.js` and by the documentation
viewer, which now drops every non-https external scheme (it used to render
`javascript:` links).

## Sheets the logbook does not offer (audited, not generated)

| Sheet | Answerable? | Note |
|---|---|---|
| WB-5.4-VL voice-loop drill | n/a | spoken callouts; the scenario values are given on the sheet |
| WB-5.4-Q quiz response sheet | n/a — **deferred** | the questions are in the instructor pack, not the workbook; their topics (MCS navigation, limits and SIDs, pass timing) are covered by the links of WB-5.1 and WB-5.4-FD. Bringing the quiz into the logbook needs the question text: Franz's call |
| WB-5.7-SA self-assessment, WB-5.7-LL lessons learned, WB-5.7-WI what-if, WB-5.7-CE course evaluation | n/a | reflection and evaluation |
| WB-5.7-FR final review prep | n/a, except §2 "three most-watched parameters" (MCS › TRD trends) and §3 anomalies log (MCS › FDR journal) | ECSS-E-ST-70-11C clause areas: open reference `ecss-ops` |
| WB-B shift log | screen for procedures executed (PRC), anomalies and FDIR rules triggered (FDR journal, S19 fire counts), GO/NO-GO outcome (drawer); n/a otherwise | "Customer commitments" reworded as for NOM-012 |
| WB-C self-check | n/a | a checklist of sheets |

## Deferred, and findings for Franz

- **Image quick-look** (mean DN per band, cloud cover; COM-011 step 8, WB-5.6-FL):
  no ground tool reads the downlinked frames. Needs a payload/delayed-TM
  quick-look; out of this audit's scope.
- **Quiz (WB-5.4-Q)**: see above.
- **Symbol rate** — the radio view shows LOW as 16 kbps at **32 kBd**
  (convolutional r = 1/2 doubles the channel symbols) while `ttc.tm_symbol_rate`
  (0x053B) and the workbook (LEOP-001 step 5a, PB) say **16 kBd**. One of the
  two definitions has to be chosen and the other side relabelled; not changed
  here because it is a modelling ruling.
- **Manual 05 §4 and 07 §5/§9** still list `ttc.range_km` (0x0509) and
  `ttc.contact_elevation` (0x050A) among the telemetry; they are ground
  products the operator dictionary does not carry (the cards and the workbook
  are corrected). Left for the manual owners.
- **Alarm → procedure map** names a card for `aocs.rw1_speed` (0x0207) but not
  for RW2–RW4 (0x0208–0x020A); the S12 table now shows the subsystem
  fallback for those. Worth completing in `alarm_procedures.yaml`.
- The French workbook had 11 sections in i18n *conflict* before this pass
  (N001, L001, L002, L007, C001, C009, C010, CTG-001/009/010/012); the
  sections changed here were reviewed and accepted one by one, the eleven
  were left for review.

## Per-question table

<!-- AUDIT TABLE: generated by tools/gen_worksheets.py --audit; edit worksheet_where.yaml -->

593 questions on 55 generated sheets.

| Answerable | before | after |
|---|---:|---:|
| screen | 311 | 324 |
| manual only | 31 | 30 |
| not at all | 15 | 3 |
| n/a | 236 | 236 |

Deferred: 3 (reason in the Fix column).

### WB-5.0 — Orientation Check

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | EOSAT-1 platform (bus type, units) | manual only | Manual 00 › §4 Spacecraft bus; NASA — State of the Art of Small Spacecraft Technology |  |  |
| q2 | Orbit altitude (km) | screen | Orbit tools › Orbit at epoch (elements, LTAN); Manual 00 › §3 Orbit parameters; ESA — where and why we orbit Earth (orbit types) |  |  |
| q3 | Orbit inclination (°) | screen | Orbit tools › Orbit at epoch (elements, LTAN); Planner › Ground track (period, inclination, beta); Manual 00 › §3 Orbit parameters |  |  |
| q4 | Local time of ascending node (LTAN) | screen (was manual only) | Orbit tools › Orbit at epoch (elements, LTAN); Manual 00 › §3 Orbit parameters; Sun-synchronous orbit (Wikipedia) | Only the manual gave the LTAN; Orbit tools showed a RAAN 90° off (atan2 arguments swapped), so the LTAN could not be checked from a screen. | Orbit tools: RAAN fixed, LTAN shown under Orbit at epoch. |
| q5 | Mission band | manual only | Manual 00 › §2 Mission objectives; Manual 06 Payload › §2 Instrument characteristics |  |  |
| q6 | Number of imager bands and their centre wavelengths (nm) | manual only | Manual 06 Payload › §2 Instrument characteristics |  |  |
| q7 | Ground stations — all five (name and latitude) | screen | MCS › TTC › Ground station network; Manual 00 › §5.1 Ground stations |  |  |
| q8 | Battery capacity (Wh) | manual only | Manual 01 EPS › §2.2 Battery |  |  |
| q9 | Battery chemistry and cell configuration | manual only | Manual 01 EPS › §2.2 Battery |  |  |
| q10 | Instrument swath (km) and GSD (m) | screen | MCS › PLD › payload.swath_width_km (0x0619); MCS › PLD › payload.gsd_m (0x0628); Manual 06 Payload › §2 Instrument characteristics |  |  |
| q11 | Pointing requirement in NOMINAL, mode 4 (°) | manual only | Manual 02 AOCS › §3 AOCS modes |  |  |
| q12 | Pointing requirement in FINE_POINT, mode 5 (°) | manual only | Manual 02 AOCS › §3 AOCS modes |  |  |
| q13 | Propulsion: type and total Δv (m/s) | manual only | Manual 07 Orbit › §6 Orbit maintenance (propulsion) |  |  |
| q14 | Flight Director | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q15 | SPACON / FDIR & Systems | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q16 | AOCS Engineer | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q17 | EPS Engineer | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q18 | Thermal Engineer | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q19 | TT&C Engineer | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q20 | Payload Operations | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q21 | FDS / Orbit Analyst | manual only | Manual 00 › §5.3 Operator positions; Manual 10 › Desk-based procedure assignments |  |  |
| q22 | Ground Segment Engineer | manual only | Manual 00 › §5.3 Operator positions |  |  |
| q23 | Mission Manager | manual only | Manual 00 › §5.3 Operator positions |  |  |
| q24 | What part of the operations work are you most looking forward to? | n/a |  |  |  |
| q25 | What part are you most nervous about? | n/a |  |  |  |

### WB-5.1 — Position score cards (round-robin)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Polled positions | screen | MCS › bottom drawer › GO/NO-GO; Manual 10 › GO/NO-GO call matrix |  |  |
| q2 | Responses recorded (verbatim) | screen | MCS › bottom drawer › GO/NO-GO |  |  |
| q3 | Time on FD seat | n/a |  |  |  |
| q4 | Insight | n/a |  |  |  |
| q5 | Question to ask | n/a |  |  |  |
| q6 | SoC at eclipse entry | screen | MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › Projections › Next eclipse |  |  |
| q7 | Next eclipse duration | screen | MCS › EPS › Projections › Next eclipse; Planner › Next eclipse; Orbit tools › Eclipses | The MCS said only "eclipse in N min"; the duration was on the planner. The printed range (33.2–35.2 min) did not say where to read it. | MCS EPS page, Projections: Next eclipse (entry–exit, duration), ground propagation. Printed row reworded. |
| q8 | Predicted SoC at exit | screen | MCS › EPS page; MCS › EPS › eps.power_cons (0x0106); Manual 01 EPS › §3.2 Orbit-average budget |  |  |
| q9 | Cross-check vs the console's prediction (EPS power flow, "at eclipse exit") | screen | MCS › EPS › Power flow | Was "vs eclipse model": the console calls it the power-flow prediction "at eclipse exit". | Reworded to name the screen. |
| q10 | Heater with highest duty | screen | MCS › TCS › Equipment (DUTY BAT / DUTY OBC); MCS › TCS › tcs.htr_duty_battery (0x040E); MCS › TCS › tcs.htr_duty_obc (0x040F) |  |  |
| q11 | Duty | screen | MCS › TCS › Equipment (DUTY BAT / DUTY OBC) |  |  |
| q12 | Predicted next-eclipse duty | manual only | MCS › TRD (trends); Manual 03 TCS › §3.1 Battery heater circuit |  |  |
| q13 | Will it saturate | n/a |  |  |  |
| q14 | Insight | n/a |  |  |  |
| q15 | Question to ask | n/a |  |  |  |
| q16 | Reading | screen | MCS › AOC › aocs.att_error (0x0217) |  |  |
| q17 | In band | screen | MCS › AOC › aocs.att_error (0x0217); Manual 02 AOCS › §3 AOCS modes |  |  |
| q18 | AOCS mode (aocs.mode 0x020F) | n/a | MCS › AOC › aocs.mode (0x020F) |  |  |
| q19 | ST1 (aocs.st1_status 0x0240) | n/a | MCS › AOC › aocs.st1_status (0x0240) |  |  |
| q20 | ST2 (aocs.st2_status 0x0243) | n/a | MCS › AOC › aocs.st2_status (0x0243) |  |  |
| q21 | Selected (aocs.st_selected 0x0244) | n/a | MCS › AOC › aocs.st_selected (0x0244) |  |  |
| q22 | Next Iqaluit pass | screen | Orbit tools › Passes (AOS, TCA, LOS); Planner › Next contacts; Planner › Next pass (max elevation and its time) | Orbit tools listed AOS, duration and max elevation only; TCA was only in the planner's next-pass card, LOS only in the planner table. | Orbit tools pass list: AOS, TCA and LOS to the second. Printed task now says read, not compute, and names both screens. |
| q23 | Agreement with the planner | screen | Orbit tools › Passes (AOS, TCA, LOS); Planner › Next contacts | Named "MPS"; the screen is the Mission planner. | Reworded. |
| q24 | Insight | n/a |  |  |  |
| q25 | Question to ask | n/a |  |  |  |
| q26 | SAFE rate (kbps) | screen | Manual 05 TTC › §2.4 TM data-rate ladder; MCS › CMD (command builder) |  |  |
| q27 | Routine LOW rate (kbps) | screen | MCS › TTC › ttc.tm_data_rate (0x0506); MCS › TTC › ttc.tm_tier (0x0539); Manual 05 TTC › §2.4 TM data-rate ladder |  |  |
| q28 | Dump HIGH rate (kbps) | screen | Manual 05 TTC › §2.4 TM data-rate ladder |  |  |
| q29 | Link margin post-transition (dB) | screen | MCS › TTC › ttc.link_margin (0x0503); MCS › TTC › Predicted vs measured link |  |  |
| q30 | BER reading (ttc.ber 0x050C, log10) | screen | MCS › TTC › ttc.ber (0x050C); Radio › RF measurements; Eb/N0 and bit error rate (Wikipedia) |  |  |
| q31 | Station in contact (TT&C page, Ground station network) | screen | MCS › TTC › Ground station network | Asked for ttc.active_gs (0x0523), which the operator dictionary does not carry (ground scheduling knowledge). | Reworded to the TT&C page's Ground station network, which marks the station in contact. |
| q32 | Baseband config (rate, symbol rate, coding — Radio view, Data link and Link budget) | screen | Radio › Data link (rate, symbol rate); Radio › Link budget (coding); MCS › TTC › ttc.tm_symbol_rate (0x053B); Manual 05 TTC › §2.4 TM data-rate ladder | "Baseband config" named no screen. | Reworded to the radio view's Data link and Link budget. |
| q33 | Insight | n/a |  |  |  |
| q34 | Question to ask | n/a |  |  |  |
| q35 | Imaging target chosen | screen | Planner › Imaging opportunities |  |  |
| q36 | FPA temperature reading (payload.fpa_temp 0x0601, °C) | n/a | MCS › PLD › payload.fpa_temp (0x0601) |  |  |
| q37 | At setpoint (payload.fpa_ready 0x0610 = 1) | screen | MCS › PLD › payload.fpa_ready (0x0610); MCS › PLD › Capture readiness |  |  |
| q38 | Storage usage (payload.mem_used_mb 0x060B) | n/a | MCS › PLD › payload.mem_used_mb (0x060B) |  |  |
| q39 | Insight | n/a |  |  |  |
| q40 | Question to ask | n/a |  |  |  |
| q41 | Monitor selected (Name column) | screen | MCS › FDR › On-board monitoring (S12) |  |  |
| q42 | Trigger parameter | screen | MCS › FDR › On-board monitoring (S12) |  |  |
| q43 | Threshold | screen | MCS › FDR › On-board monitoring (S12) |  |  |
| q44 | Persistence | screen (was not at all) | MCS › FDR › On-board monitoring (S12); Manual 08 FDIR › §6 PUS service 12 | The S12 table had no persistence (repetition) column. | FDIR page S12 table: Persistence column (consecutive 1 Hz checks). |
| q45 | Severity | screen (was not at all) | MCS › FDR › On-board monitoring (S12) | The S12 table had no severity column. | FDIR page S12 table: Severity column. |
| q46 | Recommended procedure | screen (was not at all) | MCS › FDR › On-board monitoring (S12); Manual 08 FDIR › §9 Contingency response matrix | The monitor-to-procedure link existed only on a raised alarm. | FDIR page S12 table: Procedure column (alarm_procedures.yaml), a link that opens the card. |
| q47 | Insight | n/a |  |  |  |
| q48 | Question to ask | n/a |  |  |  |
| q49 | State (prop.state 0x0B00; 0 SAFED, 1 ARMED, 2 FIRING, 3 INHIBIT) | n/a | MCS › PRP › prop.state (0x0B00) |  |  |
| q50 | Tank pressure (prop.tank_pressure 0x0B01, bar) | n/a | MCS › PRP › prop.tank_pressure (0x0B01) |  |  |
| q51 | Propellant (prop.propellant_mass 0x0B02, g) | n/a | MCS › PRP › prop.propellant_mass (0x0B02) |  |  |
| q52 | Arm interlock mask (prop.arm_inhibit_mask 0x0B15) | n/a | MCS › PRP › prop.arm_inhibit_mask (0x0B15) |  |  |
| q53 | Bits set (b0 catbed, b1 tank P, b2 propellant, b3 AOCS mode, b4 att err, b5 SoC, b6 phase, b7 eclipse, b8 v… | screen | MCS › PRP › Arm interlocks |  |  |
| q54 | Gate blocking the arm, in words | screen | MCS › PRP › Arm interlocks; Manual 07 Orbit › §6 Orbit maintenance (propulsion) |  |  |
| q55 | Insight | n/a |  |  |  |
| q56 | Question to ask | n/a |  |  |  |

### WB-5.3-PP — Day 1 Pass-Plan Team Exercise

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Target pass (station + AOS time) | screen | Planner › Next contacts; Orbit tools › Passes (AOS, TCA, LOS) |  |  |
| q2 | TCA time | screen | Orbit tools › Passes (AOS, TCA, LOS); Planner › Next pass (max elevation and its time) |  |  |
| q3 | LOS time | screen | Orbit tools › Passes (AOS, TCA, LOS); Planner › Next contacts |  |  |
| q4 | Pass duration (min) | screen | Planner › Next contacts; Orbit tools › Passes (AOS, TCA, LOS) |  |  |
| q5 | Procedures to run (IDs, in order) | manual only | MCS › PRC (procedures); Manual 07 Orbit › §8 Pass-based scheduling |  |  |
| q6 | Imaging target ID | screen | Planner › Imaging opportunities; Manual 07 Orbit › §7 Imaging target planning |  |  |
| q7 | Imaging window inside pass | screen | Planner › Imaging opportunities; Planner › Next 24 hours (timeline) |  |  |
| q8 | Bands selected and integration time | manual only | Manual 06 Payload › §2 Instrument characteristics |  |  |
| q9 | Predicted ground swath (km) | screen | MCS › PLD › payload.swath_width_km (0x0619); Manual 06 Payload › §2 Instrument characteristics |  |  |
| q10 | Downlink rate planned (kbps) | screen | Planner › Data budget; Manual 05 TTC › §2.4 TM data-rate ladder |  |  |
| q11 | Expected downlink duration (s) | screen (was not at all) | MCS › TTC › Projections › Time to dump the stored image products; Planner › Data budget | No screen turned a data volume into a dump time; it was arithmetic on the planner's figures. | MCS TTC page, Projections: time to dump the stored image products at LOW and HIGH (payload.product_mb ÷ the rate ladder). |
| q12 | Plausible failure 1 | manual only | Manual 08 FDIR › §9 Contingency response matrix |  |  |
| q13 | Recovery procedure for failure 1 | manual only | Manual 08 FDIR › §9 Contingency response matrix |  |  |
| q14 | Plausible failure 2 | manual only | Manual 08 FDIR › §9 Contingency response matrix |  |  |
| q15 | Recovery procedure for failure 2 | manual only | Manual 08 FDIR › §9 Contingency response matrix |  |  |
| q16 | What the other team challenged | n/a |  |  |  |
| q17 | What we accepted | n/a |  |  |  |
| q18 | What we defended | n/a |  |  |  |

### WB-5.4-N001 — NOM-001 Pass Startup (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | SPACON: Verify OBC status: HK_REQUEST(sid=4) (S3.27) | screen | MCS › OBD › obdh.mode (0x0300); MCS › OBD › obdh.cpu_load (0x0302); MCS › OBD › obdh.uptime (0x0308) |  |  |
| step 2 | EPS: Verify EPS health: HK_REQUEST(sid=1) | screen | MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.power_gen (0x0107); MCS › EPS › eps.power_cons (0x0106) |  |  |
| step 3 | AOCS: Verify AOCS pointing: HK_REQUEST(sid=2) | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217); MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_yaw (0x0206) |  |  |
| step 4 | TT&C: Establish the link: TTC_SWITCH_PRIMARY (S8.1) | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.link_margin (0x0503) |  |  |
| step 5 | SPACON: Full housekeeping collection: HK_REQUEST (S3.27) of SIDs 1 EPS, 2 AOCS, 3 TCS, 4 OBDH, 5 Payload, 6… | screen | MCS › PUS › S3 HK (Observed column); MCS › FDR › Alarm / anomaly journal |  |  |
| step 6 | Payload: Payload preparation, only if imaging or a downlink is planned: PAYLOAD_SET_MODE(mode=1) STANDBY (S… | screen | MCS › PLD › payload.mode (0x0600); MCS › TCS › tcs.cooler_fpa (0x040C); MCS › PLD › payload.store_used (0x0604) |  |  |
| step 7 | FD: Pass readiness declaration: poll each position GO / NO-GO | screen | MCS › bottom drawer › GO/NO-GO; Manual 10 › GO/NO-GO call matrix |  |  |
| q8 | Off-nominal items observed | n/a |  |  |  |

### WB-5.4-C003 — CTG-003 TTC Link Loss Recovery (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Ground Seg: Confirm the link loss is not a ground issue: antenna tracking, uplink transmitter power, receiv… | n/a | Radio › Lock status; Radio › RF measurements |  |  |
| step 2 | TT&C: Re-acquire on the primary transponder: blind HK_REQUEST(sid=6) (S3.27), wait 30 s | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.rssi (0x0502) |  |  |
| step 3 | TT&C: Switch to the redundant transponder: blind TTC_SWITCH_REDUNDANT (S8.1 func 64), wait 45 s | screen | MCS › TTC › ttc.mode (0x0500); MCS › TTC › ttc.link_status (0x0501) |  |  |
| step 4 | TT&C: Second attempt on the primary: blind TTC_SWITCH_PRIMARY (S8.1 func 63), wait 45 s | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › Link lock chain |  |  |
| step 5 | TT&C: Verify link quality and subsystem health: HK_REQUEST(sid=6), HK_REQUEST(sid=1), HK_REQUEST(sid=4) | screen | MCS › TTC › ttc.link_margin (0x0503); MCS › TTC › ttc.mode (0x0500); MCS › EPS › eps.bus_voltage (0x0105); MCS › OBD › obdh.mode (0x0300) |  |  |
| step 6 | TT&C: Escalation, no link: log every blind command with its time; notify the Mission Director and Flight Dy… | screen | MCS › bottom drawer › Command history; MCS › bottom drawer › Log; MCS › TTC › ttc.time_since_last_tc (0x053D); MCS › bottom drawer › Events |  |  |
| q7 | Step at which link was recovered (if any) | n/a |  |  |  |
| q8 | Anomaly ticket number | n/a |  |  |  |

### WB-5.4-N012 — NOM-012 Shift Handover Template

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Phase and time | screen | MCS › EPS › eps.spacecraft_phase (0x0129); MCS › OVR (overview) |  |  |
| q2 | Last completed pass | screen | MCS › header › What's next; Planner › Next contacts |  |  |
| q3 | Open anomalies (rule name, status, recovery procedure step) | screen | MCS › FDR › Alarm / anomaly journal; MCS › FDR › On-board monitoring (S12) |  |  |
| q4 | Open work items (procedures in progress) | screen | MCS › PRC (procedures) |  |  |
| q5 | Next pass (station, AOS, planned procedures, operator-of-record) | screen | MCS › header › What's next; Planner › Next contacts |  |  |
| q6 | Customer commitments active (imaging and downlinks booked in the planner) | screen (was not at all) | Planner › Activity schedule; Planner › Imaging opportunities | "Customer commitments" is a concept no tool has. | Reworded: the imaging and downlinks booked in the planner's activity schedule. |
| q7 | GO authorisations outstanding | screen | MCS › bottom drawer › GO/NO-GO |  |  |
| q8 | Voice-loop tone (team rested / tense / etc.) | n/a | ECSS-E-ST-70-11C — Space segment operability |  |  |

### WB-5.4-FD — Day 2 Flight-Dynamics Workshop

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Station · AOS (your prediction, UTC) · AOS (planner, UTC) · Δ (s) | screen | Orbit tools › Passes (AOS, TCA, LOS); Planner › Next contacts; CelesTrak — the two-line element set format | Asked to compare with the "MPS" (the planner) and named a command line, not the page. | Reworded to Orbit tools and the planner's Next contacts. |
| q2 | Max el (°) · Predicted duration (min) · Duration in the planner (min) | screen | Orbit tools › Passes (AOS, TCA, LOS); Planner › Next contacts; Manual 07 Orbit › §4.3 Contact duration vs maximum elevation |  | "from MPS" reworded to the planner. |
| q3 | Formula used (write here) | manual only | Manual 07 Orbit › §4.3 Contact duration vs maximum elevation; Orbital elements (Wikipedia) |  |  |
| q4 | Longest eclipse in next 24 h | screen (was not at all) | Orbit tools › Eclipses; Planner › Next 24 hours (timeline); Manual 07 Orbit › §3 Eclipse cycle | No screen listed eclipse durations beyond the next one; the longest of 24 h had to be guessed from the planner's timeline. | Orbit tools: Eclipses panel (entry, exit, duration over 24 h, longest marked). |
| q5 | Predicted SoC at exit (using SoC_exit = SoC_entry - P_avg · t / E_battery) | screen | MCS › EPS › Power flow; MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.power_cons (0x0106) |  |  |
| q6 | Actual SoC at exit | screen | MCS › EPS › eps.bat_soc (0x0101); MCS › TRD (trends) |  |  |
| q7 | Δ | n/a |  |  |  |
| q8 | Concern? ☐ no ☐ yes — note | n/a |  |  |  |

### WB-5.4-VL — Day 2 Voice-Loop Callout Drill

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | FD asks AOCS for pointing report | n/a |  |  |  |
| q2 | AOCS reports pointing 0.28°, nominal | n/a |  |  |  |
| q3 | FD asks EPS for eclipse-entry predictor | n/a |  |  |  |
| q4 | EPS reports eclipse entry T+04:12, SoC at exit 78% | n/a |  |  |  |
| q5 | FD polls 3 positions for GO on payload power-on | n/a |  |  |  |
| q6 | EPS responds: "no-go, payload line 3 already drawing 0.35 A with the line commanded OFF" | n/a |  |  |  |
| q7 | FD calls HOLD on payload power-on | n/a |  |  |  |
| q8 | TT&C calls anomaly: BER climbed to 1e-3 | n/a |  |  |  |
| q9 | FD requests rate fallback | n/a |  |  |  |
| q10 | TT&C reports tier stepped down HIGH→LOW, rate 16 kbps, BER 1e-7 nominal | n/a |  |  |  |
| q11 | Self-score (out of 10) | n/a |  |  |  |
| q12 | One callout I want to practice more | n/a |  |  |  |

### WB-5.5-PB — Day 3 LEOP Pre-Pass Briefing Checklist

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Position assignments confirmed and posted | n/a |  |  |  |
| q2 | Comm check completed (all positions readable) | n/a |  |  |  |
| q3 | BP-2 (first_contact.yaml) loaded; spacecraft in phase 3 (BOOTLOADER) | screen | MCS › EPS › eps.spacecraft_phase (0x0129); MCS › OBD › obdh.sw_image (0x0311) |  |  |
| q4 | A real Iqaluit pass is scheduled for first contact (pass override is an instructor control; no operator for… | screen | Planner › Next contacts; MCS › header › What's next |  |  |
| q5 | FD has loaded LEOP procedure pack into procedure panel | screen | MCS › PRC (procedures) |  |  |
| q6 | SPACON has reviewed the FDIR rule set on the FDIR panel (there is no FDIR table-load telecommand — the rule… | screen | MCS › FDR › On-board monitoring (S12); MCS › FDR › Event-action rules (S19); Manual 08 FDIR › §4 FDIR rules and triggers |  |  |
| q7 | AOCS has reviewed residual tumble rates (~1–2 °/s per axis from the separation impulse) | manual only | Manual 09 LEOP › §4 First contact | Before first contact there is no AOCS telemetry: the rates are the LEOP guide's prediction. | Linked to the LEOP guide. |
| q8 | EPS confirms SoC ~90 % (eps.bat_soc 0x0101); only the non-switchable obc (line 0) and ttc_rx (line 1) are O… | screen | MCS › EPS › Power flow; MCS › EPS › eps.bat_soc (0x0101) |  |  |
| q9 | TT&C has confirmed UHF beacon reception: beacon SID 11 arriving (PUS page, S3 HK, Observed column); note th… | screen (was not at all) | MCS › PUS › S3 HK (Observed column); MCS › header › Can I see it? | Asked for ttc.beacon_active (0x0527 = 1), which the operator dictionary does not carry. | Reworded to what the console shows: beacon SID 11 arriving (PUS page, S3 HK, Observed). |
| q10 | Ground Seg has confirmed Iqaluit antenna on-target, demodulator on the SAFE rung (1 000 bps, BPSK, conv(7,1… | screen | Radio › Data link (rate, symbol rate); Radio › Lock status; Manual 09 LEOP › §4 First contact |  |  |
| q11 | FDS has produced 24-h pass schedule and handed to FD/TT&C/Ground Seg | screen | Planner › Next contacts; Orbit tools › Passes (AOS, TCA, LOS) |  |  |
| q12 | Anomaly ticket forms blank-printed and available at each console | n/a |  |  |  |
| q13 | Voice-loop language declared (callouts in English) | n/a |  |  |  |
| q14 | FD ready call (verbatim) | n/a |  |  |  |

### WB-5.5-L001 — LEOP-001 First Acquisition of Signal & OBC Boot (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Ground Seg: Configure the Iqaluit receiver for the scheduled pass: point at the predicted AOS, auto-track, … | screen | Radio › Lock status; Radio › Data link (rate, symbol rate); Planner › Next pass (max elevation and its time) |  |  |
| step 2 | TT&C: First uplink, sent blind into the window: CONNECTION_TEST (S17.1) | screen | MCS › bottom drawer › Command history; MCS › PUS › S3 HK (Observed column) |  |  |
| step 3 | TT&C: Verify carrier lock and link quality | screen | MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.link_margin (0x0503); MCS › TTC › ttc.link_status (0x0501) |  |  |
| step 4 | SPACON: Confirm the bootloader: HK_REQUEST(sid=11) (S3.27) | screen | MCS › OBD › obdh.sw_image (0x0311) |  |  |
| step 5 | SPACON: Boot the application: OBC_BOOT_APP (S8.1 func 55); after its S1.7, HK_ENABLE(sid=3), HK_ENABLE(sid=… | screen | MCS › OBD › obdh.bus_b_status (0x0310); MCS › OBD › obdh.tc_acc_count (0x0305); MCS › OBD › obdh.boot_state (0x0A15); MCS › OBD › obdh.sw_image (0x0311); MCS › bottom drawer › Command history; MCS › bottom drawer › Events |  |  |
| step 5a | TT&C: Clear beacon mode, then select LOW: TTC_SET_BEACON_MODE(on=0) (S8.1 func 70), TTC_SET_DATA_RATE(rate=… | screen | MCS › TTC › ttc.beacon_mode (0x0521); MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.tm_data_rate (0x0506); MCS › TTC › ttc.tm_tier (0x0539); MCS › bottom drawer › Command history |  |  |
| step 6 | SPACON: Note the unset clock — do not sync here: time is LEOP-006's job | screen | MCS › OBD › obdh.time_ref (0x0A13) |  |  |
| step 7 | SPACON: Power sanity check: HK_REQUEST(sid=1) (S3.27) | screen | MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.pl_ttc_tx (0x0112); MCS › EPS › eps.power_gen (0x0107) |  |  |
| step 8 | TT&C: Log and report: AOS, first accepted TC, application boot, HK values; confirm the pass is long enough … | screen | MCS › bottom drawer › Command history; MCS › bottom drawer › Events; Planner › Next contacts |  |  |
| q10 | AOS time (UTC) | screen | MCS › header › What's next; Planner › Next contacts |  |  |
| q11 | First accepted TC | screen | MCS › bottom drawer › Command history |  |  |
| q12 | App boot complete | screen | MCS › bottom drawer › Events; MCS › OBD › Software state |  |  |
| q13 | obdh.time_ref (expect 0) | screen | MCS › OBD › obdh.time_ref (0x0A13) |  |  |
| q14 | eps.bus_voltage | screen | MCS › EPS › eps.bus_voltage (0x0105) |  |  |

### WB-5.5-L006 — LEOP-006 Time Synchronisation (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Verify OBC status and the link: HK_REQUEST(sid=4), HK_REQUEST(sid=6) (S3.27) | screen | MCS › OBD › obdh.mode (0x0300); MCS › OBD › obdh.cpu_load (0x0302); MCS › TTC › ttc.link_margin (0x0503) |  |  |
| step 2 | Read the clock, its reference and the slant range: REQUEST_TIME (S9.2), HK_REQUEST(sid=6), HK_REQUEST(sid=4) | screen (was not at all) | MCS › PUS › S9 TIME (time correlation); MCS › PUS › S9 TIME › One-way light time; MCS › TTC › Ground station network; MCS › OBD › obdh.obc_time (0x0309); MCS › OBD › obdh.obc_time_fine (0x0A12); MCS › OBD › obdh.time_ref (0x0A13) | The row computed OWLT from ttc.range_km (0x0509), which no HK SID carries and the console does not show. | PUS page, S9 TIME: one-way light time from the ground's own geometry; TT&C page, Ground station network: range and OWLT. Printed row and LEOP-006 card reworded. |
| step 3 | Calculate the time delta: Δt = T_obc − (T_ground − OWLT) | screen (was not at all) | MCS › PUS › S9 TIME (time correlation); Manual 12 Time › §9 Reading the correlation on the console | The delta needed OWLT, which no screen gave. | PUS page, S9 TIME: Δt = T_obc − (T_ground − OWLT). |
| step 4 | Send the time update: SET_TIME(cuc_seconds=T_corrected) (S9.1), with T_corrected = T_ground at send + OWLT … | screen | MCS › PUS › S9 TIME (time correlation); MCS › bottom drawer › Command history |  |  |
| step 5 | Verify the time accuracy: REQUEST_TIME (S9.2), HK_REQUEST(sid=4) | screen | MCS › PUS › S9 TIME (time correlation); MCS › OBD › obdh.time_ref (0x0A13); MCS › OBD › obdh.mode (0x0300) |  |  |
| step 6 | Validate the clock rate: a second time report (S9.2) and SID 4 sample after a known ground interval | screen | MCS › PUS › S9 TIME (time correlation); Manual 12 Time › §5 Drift model |  |  |
| step 6a | Path B, GPS time discipline, once the receiver has a fix: HK_ENABLE(sid=12) (S3.5), then OBC_GPS_TIME_SYNC … | screen | MCS › AOC › aocs.gps_fix (0x0274); MCS › OBD › obdh.time_ref (0x0A13); MCS › OBD › obdh.time_since_sync_s (0x0A14); MCS › bottom drawer › Command history |  |  |
| step 7 | Confirm time-stamping and log: HK_REQUEST(sid=4) | screen | MCS › OBD › obdh.uptime (0x0308); MCS › OBD › obdh.active_obc (0x030C); MCS › OBD › obdh.time_ref (0x0A13); MCS › bottom drawer › Events |  |  |

### WB-5.5-L002 — LEOP-002 Initial Health Check (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | EPS: Full EPS housekeeping: HK_REQUEST(sid=1) (S3.27) | screen | MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.bat_voltage (0x0100); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.power_gen (0x0107) |  |  |
| step 2 | EPS: Confirm the unpowered subsystems are dark (same SID 1 report) | screen | MCS › EPS › eps.pl_aocs_wheels (0x0117); MCS › EPS › eps.pl_payload (0x0113); MCS › EPS › eps.pl_fpa_cooler (0x0114); MCS › EPS › eps.pl_prop (0x014A) |  |  |
| step 3 | Thermal: Thermal housekeeping: HK_REQUEST(sid=3) | screen | MCS › TCS › tcs.temp_obc (0x0406); MCS › TCS › tcs.temp_battery (0x0407); MCS › TCS › tcs.temp_fpa (0x0408) |  |  |
| step 4 | SPACON: OBDH housekeeping: HK_REQUEST(sid=4) | screen | MCS › OBD › obdh.mode (0x0300); MCS › OBD › obdh.cpu_load (0x0302) |  |  |
| step 5 | TT&C: TT&C housekeeping: HK_REQUEST(sid=6) | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.link_margin (0x0503) |  |  |
| step 6 | SPACON: Compile the health assessment summary for the FD; flag any value outside its post-separation range | n/a |  |  |  |
| q7 | Consolidated PASS / FAIL | n/a |  |  |  |
| q8 | If FAIL, which contingency procedure invoked | manual only | Manual 08 FDIR › §9 Contingency response matrix |  |  |

### WB-5.5-L007 — LEOP-007 Sequential Power-On (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | EPS: Verify the EPS baseline: HK_REQUEST(sid=1) (S3.27) | screen | MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.power_gen (0x0107) |  |  |
| step 2 | EPS: Heater lines only as needed: read tcs.temp_battery (0x0407) and tcs.temp_obc (0x0406) from SID 3; EPS_… | screen | MCS › TCS › tcs.temp_battery (0x0407); MCS › TCS › tcs.temp_obc (0x0406); MCS › EPS › eps.pl_htr_bat (0x0115); MCS › EPS › eps.pl_htr_obc (0x0116) |  |  |
| step 3 | EPS / AOCS: Energise the AOCS suite line and enable its HK: EPS_POWER_ON(line_index=7) (func 19), then HK_E… | screen | MCS › EPS › eps.pl_aocs_wheels (0x0117) |  |  |
| step 4 | AOCS: Both DETUMBLE legs first, and the GPS receiver: S2_AOCS_MAGNETOMETER(device_id=521, state=1), MTQ_ENA… | screen | MCS › AOC › aocs.mtq_enabled (0x025E); MCS › bottom drawer › Command history |  |  |
| step 5 | AOCS: Command DETUMBLE: AOCS_SET_MODE(mode=2) (S8.1 func_id 0) — mode 2 = DETUMBLE | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.mag_enabled (0x025C); MCS › AOC › aocs.mag_field_total (0x0277); MCS › AOC › aocs.rate_roll (0x0204); MCS › bottom drawer › Command history |  |  |
| step 6 | EPS: Confirm the exit power state: HK_REQUEST(sid=1), GET_PARAM(param_id=0x0260) (S20.3) | screen | MCS › AOC › aocs.wheels_enabled (0x0260); MCS › EPS › eps.pl_payload (0x0113); MCS › EPS › eps.pl_fpa_cooler (0x0114); MCS › EPS › eps.pl_prop (0x014A) |  |  |
| q7 | Phase (0x0129) | screen | MCS › EPS › eps.spacecraft_phase (0x0129) |  |  |
| q8 | Wheels enabled (aocs.wheels_enabled 0x0260) | screen | MCS › AOC › aocs.wheels_enabled (0x0260) |  |  |
| q9 | SoC | screen | MCS › EPS › eps.bat_soc (0x0101); MCS › TCS › tcs.temp_battery (0x0407) |  |  |

### WB-5.5-L005 — LEOP-005 Sun Acquisition (observe, confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Record the initial body rates: HK_REQUEST(sid=2) (S3.27) | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_pitch (0x0205); MCS › AOC › aocs.rate_yaw (0x0206) |  |  |
| step 2 | Monitor rate damping — command nothing: HK_REQUEST(sid=2) again at T+5 min | screen | MCS › AOC › aocs.mag_field_total (0x0277) |  |  |
| step 3 | Observe the automatic transition to COARSE_SUN: body rates below 0.5°/s for 30 s → the AOCS hands itself ov… | screen | MCS › AOC › aocs.mode (0x020F); MCS › bottom drawer › Events |  |  |
| step 4 | Verify the sun hold: HK_REQUEST(sid=2) every 60 s for 5 min, GET_PARAM(param_id=0x0215) (S20.3) | screen | MCS › AOC › aocs.css_sun_confidence (0x0215); MCS › AOC › aocs.att_error (0x0217); MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_pitch (0x0205) |  |  |
| step 5 | Verify power generation in the hold: HK_REQUEST(sid=1) | screen | MCS › EPS › eps.power_gen (0x0107); MCS › EPS › eps.eclipse_flag (0x0108); MCS › EPS › eps.bat_soc (0x0101) |  |  |
| step 6 | Log the final AOCS state: rates, attitude error, CSS confidence, power. The spacecraft stays in COARSE_SUN:… | screen | MCS › AOC page; MCS › EPS › Power flow |  |  |

### WB-5.5-L003 — LEOP-003 Initial Orbit Determination and End of LEOP (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Verify the GPS navigation solution: HK_REQUEST(sid=12) (S3.27) | screen | MCS › AOC › GPS navigation (PVT); Dilution of precision, PDOP (Wikipedia); MCS › AOC › aocs.gps_fix (0x0274); MCS › AOC › aocs.gps_num_sats (0x0276); MCS › AOC › aocs.gps_pdop (0x0275) |  |  |
| step 2 | Read the position fix: GET_PARAM(param_id=0x0210), GET_PARAM(param_id=0x0211), GET_PARAM(param_id=0x0212) (… | screen | MCS › AOC › aocs.gps_lat (0x0210); MCS › AOC › aocs.gps_lon (0x0211); MCS › AOC › aocs.gps_alt (0x0212) |  |  |
| step 3 | Read the ECEF state vector: GET_PARAM(param_id=0x0231) … GET_PARAM(param_id=0x0236) | screen | MCS › AOC › GPS navigation › \|r\| and \|v\|; MCS › AOC › GPS navigation (PVT); MCS › AOC › aocs.gps_ecef_x (0x0231); MCS › AOC › aocs.gps_vel_z (0x0236) | The six components were on screen; the magnitudes the row checks were arithmetic. | AOC page, GPS navigation: \|r\| (km) and \|v\| (m/s) computed from the downlinked components. |
| step 4 | Flight Dynamics comparison with the launcher-predicted orbit — nothing is uploaded to the spacecraft | screen (was not at all) | Orbit tools › State vector (convert the GPS fix); Orbit tools › Orbit at epoch (elements, LTAN); CelesTrak — the two-line element set format; Orbital elements (Wikipedia) | Orbit tools treated the GPS ECEF state as inertial (inclination ~3.5° and period ~3 min off for EOSAT-1) and showed RAAN 90° off, with no LTAN: every check of this row failed or could not be made. | Orbit tools: ECEF→ECI with Earth rotation, RAAN/AOP formulas fixed, LTAN shown. |
| step 5 | Second fix consistency check, 10 min later: HK_REQUEST(sid=12) | screen | MCS › AOC › aocs.gps_alt (0x0212); MCS › AOC › aocs.gps_fix (0x0274) |  |  |
| step 6 | Distribute the Orbit Determination Report and the refined TLE to the ground network (planner, FDS, stations) | n/a | Orbit tools › Passes (AOS, TCA, LOS) |  |  |
| step 7 | FD: GO/NO-GO poll of all positions, then declare COMMISSIONING by telecommand: SYS_SET_MISSION_PHASE(phase=… | screen | MCS › bottom drawer › GO/NO-GO; MCS › EPS › eps.spacecraft_phase (0x0129); MCS › bottom drawer › Events |  |  |

### WB-5.5-AT — Day 3 Anomaly Ticket (3 copies)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Ticket ID (auto-assigned) | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q2 | Pass / shift | screen | MCS › header › What's next |  |  |
| q3 | Date / UTC time of first indicator | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q4 | Triggering parameter and value | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q5 | FDIR rule that fired (if any) | screen | MCS › FDR › Alarm / anomaly journal; MCS › FDR › Event-action rules (S19) |  |  |
| q6 | Severity (0–4) | screen | MCS › FDR › FDIR state; Manual 08 FDIR › §12 MCS alarm lifecycle |  |  |
| q7 | First operator to call it (position) | n/a |  |  |  |
| q8 | First-action time | screen | MCS › bottom drawer › Command history |  |  |
| q9 | Procedure invoked (ID) | screen | MCS › PRC (procedures); MCS › FDR › Alarm / anomaly journal |  |  |
| q10 | Recovery actions taken (verbatim from loop) | screen | MCS › bottom drawer › Command history; MCS › bottom drawer › Log |  |  |
| q11 | Outcome (recovered / safe / deferred) | n/a |  |  |  |
| q12 | Root cause hypothesis | n/a |  |  |  |
| q13 | Open items for next shift | n/a |  |  |  |

### WB-5.5-GO — Day 3 End-of-Pass GO/NO-GO Scorecard

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | OBC application SW running (obdh.sw_image 0x0311 = 1) | n/a | MCS › OBD › obdh.sw_image (0x0311) |  |  |
| q2 | Onboard time set, residual < 1.0 s | screen | MCS › PUS › S9 TIME (time correlation) |  |  |
| q3 | Beacon mode cleared, downlink on LOW (ttc.tm_tier 0x0539 = 1) | n/a | MCS › TTC › ttc.tm_tier (0x0539) |  |  |
| q4 | Antenna still stowed, ttc.antenna_deployed (0x0520) = 0 — COM-006 deploys it; LOW needs no deployment | n/a | MCS › TTC › ttc.antenna_deployed (0x0520) |  |  |
| q5 | Heater lines energised only where their zone needed heat, and logged (LEOP-007 step 2) | screen | MCS › EPS › eps.pl_htr_bat (0x0115); MCS › EPS › eps.pl_htr_obc (0x0116) |  |  |
| q6 | AOCS wheels line ON, AOCS through DETUMBLE (2) into COARSE_SUN (3) | screen | MCS › EPS › eps.pl_aocs_wheels (0x0117); MCS › AOC › AOCS mode chain |  |  |
| q7 | Body rates < 0.5°/s on all axes; aocs.att_error < 15° in the COARSE_SUN hold | screen | MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_pitch (0x0205); MCS › AOC › aocs.rate_yaw (0x0206); MCS › AOC › aocs.att_error (0x0217) |  |  |
| q8 | Anomaly ticket filed for any injection | n/a |  |  |  |
| q9 | Phase advanced to COMMISSIONING (5) with SYS_SET_MISSION_PHASE (func 120) (Pass 2 only) | screen | MCS › EPS › eps.spacecraft_phase (0x0129); MCS › bottom drawer › Command history |  |  |
| q10 | Notes for debrief | n/a |  |  |  |

### WB-5.5-OBS — Day 3 Observer Worksheets (axes used: Communications + Technical)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Voice-loop discipline (callouts, hot-mike) | n/a |  |  |  |
| q2 | GO/NO-GO protocol followed | screen | MCS › bottom drawer › GO/NO-GO |  |  |
| q3 | Cross-talk incidents (count + timestamps) | n/a |  |  |  |
| q4 | MCS chat — used for what? | screen | MCS › bottom drawer › Log |  |  |
| q5 | Handover: timing, content, completeness | n/a |  |  |  |
| q6 | Silent confusion (operator did wrong thing because no one said anything)? | n/a |  |  |  |
| q7 | Worked well | n/a |  |  |  |
| q8 | Could improve | n/a |  |  |  |
| q9 | Specific recommendation | n/a |  |  |  |
| q10 | Procedure adherence — any skipped or out-of-order steps? | n/a | ECSS-E-ST-70-11C — Space segment operability |  |  |
| q11 | Anomaly detection time — first indicator to first action | screen | MCS › FDR › Alarm / anomaly journal; MCS › bottom drawer › Command history |  |  |
| q12 | Telemetry interpretation — any misreads? | n/a |  |  |  |
| q13 | Command discipline — any unauthorised commands? | screen | MCS › bottom drawer › Command history |  |  |
| q14 | Use of FDIR panel — did anyone watch it? | n/a |  |  |  |
| q15 | Outcome vs pass criteria | n/a |  |  |  |
| q16 | Worked well | n/a |  |  |  |
| q17 | Could improve | n/a |  |  |  |
| q18 | Specific recommendation | n/a |  |  |  |

### WB-5.5-HO — Day 3 Inter-Pass Handover Turnover Form

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Outgoing operator | n/a |  |  |  |
| q2 | Incoming operator | n/a |  |  |  |
| q3 | Current parameter values (top 3 mnemonics) | screen | MCS › OVR (overview) |  |  |
| q4 | Current procedure state (file ID + step) | screen | MCS › PRC (procedures) |  |  |
| q5 | Console page left open for the next operator (page, panel) | screen (was not at all) | MCS › OVR (overview) | Asked for a "pinned widget": neither console has pinned widgets. | Reworded: the console page and panel left open for the next operator. |
| q6 | Open question for next shift | n/a |  |  |  |
| q7 | Time | screen | MCS › OVR (overview) |  |  |

### WB-5.5-DB — Day 3 Post-Shift Debrief Reflection

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | What is one decision you took during the shift that, in retrospect, you would not take again? Why? | n/a |  |  |  |
| q2 | What is one decision that surprised you with how well it worked? | n/a |  |  |  |
| q3 | Which voice callout did you most struggle to make in real time? | n/a |  |  |  |
| q4 | What is one thing the team did better as a unit than you expected? | n/a |  |  |  |
| q5 | What is one specific thing you will do differently tomorrow? | n/a |  |  |  |

### WB-5.6-PB — Day 4 Commissioning Pre-Pass-Set Briefing

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | BP-3 commissioning_day_start.yaml scenario loaded (instructor-authored — see the Instructor Book; it is not… | n/a |  |  |  |
| q2 | Spacecraft in phase 4 (LEOP), eps.spacecraft_phase (0x0129) = 4 — COMMISSIONING (5) is declared by LEOP-003… | n/a | MCS › EPS › eps.spacecraft_phase (0x0129) |  |  |
| q3 | Position assignments posted (different team from yesterday) | n/a |  |  |  |
| q4 | Pass-set timeline understood (4 sim passes in 2.5 h real time) | n/a |  |  |  |
| q5 | All 13 commissioning procedures (COM-001…COM-013) loaded in the procedure index | screen | MCS › PRC (procedures) |  |  |
| q6 | EPS confirms SoC ~90 %, eps.pl_payload (0x0113) = 0 | n/a | MCS › EPS › eps.pl_payload (0x0113) |  |  |
| q7 | Thermal confirms FPA at its uncooled equilibrium, payload.fpa_temp (0x0601) about −5 to +7 °C | n/a | MCS › PLD › payload.fpa_temp (0x0601) |  |  |
| q8 | Payload Ops has reviewed COM-009/-010/-011/-012 in detail | manual only | Procedure COM-009; Procedure COM-012 |  |  |
| q9 | First Light target candidate selected (FDS) | screen | Planner › Imaging opportunities |  |  |
| q10 | Compressed-time speed multiplier set (instructor) | n/a |  |  |  |

### WB-5.6-C001 — COM-001 EPS Checkout (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Baseline bus voltage — HK_REQUEST(sid=1) (S3.27) | screen | MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 2 | Battery V & SoC — GET_PARAM(param_id=0x0100), GET_PARAM(param_id=0x0101) (S20.3) | screen | MCS › EPS › eps.bat_voltage (0x0100); MCS › EPS › eps.bat_soc (0x0101) |  |  |
| step 3 | Solar array sunlit performance — HK_REQUEST(sid=1), sunlit and sun-pointed | screen | MCS › EPS › eps.power_gen (0x0107) |  |  |
| step 4 | Eclipse discharge — HK_REQUEST(sid=1) at entry and at mid-eclipse | screen | MCS › EPS › eps.power_gen (0x0107); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › Projections › Next eclipse |  |  |
| step 5 | Eclipse-exit charge recovery — HK_REQUEST(sid=1) at exit + 5 min | screen | MCS › EPS › eps.power_gen (0x0107); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › Projections › Next eclipse |  |  |
| step 6 | Power budget — GET_PARAM(param_id=0x0108); orbit-average generation against consumption | screen | MCS › EPS › Projections › Orbit-average margin; MCS › EPS › Power flow; Manual 01 EPS › §3.2 Orbit-average budget; MCS › EPS › eps.eclipse_flag (0x0108) | The orbit balance was in Wh (power flow, This orbit); the row asks for a margin in W. | EPS page, Projections: orbit-average margin (W). |
| step 7 | Bus regulation under a load transient — record eps.pl_htr_bat (0x0115) first, then EPS_POWER_ON(line_index=… | screen | MCS › EPS › eps.pl_htr_bat (0x0115); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| q8 | GO COM-002 | n/a |  |  |  |

### WB-5.6-C002 — COM-002 TCS Verification (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Thermal HK — HK_REQUEST(sid=3) (S3.27; SID 3 = TCS, 60 s cadence) | screen | MCS › TCS › tcs.temp_obc (0x0406); MCS › TCS › tcs.temp_battery (0x0407); MCS › TCS › tcs.temp_fpa (0x0408) |  |  |
| step 2 | Sunlit profile — HK_REQUEST(sid=3) every 120 s for 30 min | screen | MCS › TRD (trends); MCS › TCS › tcs.temp_obc (0x0406); MCS › TCS › tcs.temp_battery (0x0407) |  |  |
| step 3 | Eclipse profile — HK_REQUEST(sid=3) at entry, mid-eclipse and exit | screen | MCS › TRD (trends); MCS › EPS › Projections › Next eclipse; MCS › TCS › tcs.temp_obc (0x0406); MCS › TCS › tcs.temp_battery (0x0407) |  |  |
| step 4 | Battery heater circuit, line first: record eps.pl_htr_bat (0x0115); EPS_POWER_ON(line_index=5) (S8.1 func 1… | screen | MCS › EPS › eps.pl_htr_bat (0x0115); MCS › TCS › tcs.temp_battery (0x0407) |  |  |
| step 5 | OBC heater circuit, line first: record eps.pl_htr_obc (0x0116); EPS_POWER_ON(line_index=6); HEATER_OBC(on=1… | screen | MCS › EPS › eps.pl_htr_obc (0x0116); MCS › TCS › tcs.temp_obc (0x0406) |  |  |
| step 6 | Read the heater thermostat thresholds — GET_PARAM(param_id=0x0330), GET_PARAM(param_id=0x0331) (S20.3) | screen | MCS › TCS › tcs.setpoint_bat (0x0330); MCS › TCS › tcs.setpoint_obc (0x0331) |  |  |
| step 7 | FPA cooler interface before activation — GET_PARAM(param_id=0x040C), GET_PARAM(param_id=0x0114) | screen | MCS › TCS › tcs.cooler_fpa (0x040C); MCS › EPS › eps.pl_fpa_cooler (0x0114); MCS › TCS › tcs.temp_fpa (0x0408) |  |  |
| step 8 | Compile the thermal baseline report: minimum, maximum and mean of each zone over one orbit, against the the… | screen | MCS › TRD (trends); Manual 03 TCS › §4 Temperature zones | Trends plots each zone over a chosen window; minimum, maximum and mean are read off the plot or the CSV export. | Linked to Trends (24 h window, EXPORT CSV). |
| q9 | GO COM-005 | n/a |  |  |  |

### WB-5.6-C005 — COM-005 AOCS Mode Transitions (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Latch the commanded mode: AOCS_SET_MODE(mode=4) — NOMINAL | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.commanded_mode (0x0297); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 2 | Commanded NOMINAL → FINE_POINT through its gate: AOCS_FINE_READY_CHECK (S8.1 func 89), then AOCS_SET_MODE(m… | screen | MCS › AOC › aocs.fine_ready (0x02C5); MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 3 | Commanded FINE_POINT → NOMINAL: AOCS_SET_MODE(mode=4) | screen | MCS › AOC › aocs.commanded_mode (0x0297); MCS › AOC › aocs.mode (0x020F) |  |  |
| step 4 | Commanded NOMINAL → INERTIAL and back: AOCS_SET_MODE(mode=9), then AOCS_SET_MODE(mode=4) | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › AOCS mode chain |  |  |
| step 5 | COARSE_SUN is a hold, not a destination: AOCS_SET_MODE(mode=3), then wait — send nothing | screen | MCS › AOC › aocs.mode_demoted (0x0298); MCS › AOC › aocs.mode (0x020F) |  |  |
| step 6 | Automatic eclipse handover, observed in passing — no command | screen | MCS › AOC › aocs.commanded_mode (0x0297); MCS › AOC › aocs.mode (0x020F) |  |  |
| step 7 | Commanded with an automatic exit — desaturation: AOCS_DESATURATE (S8.1 func 1) | screen | MCS › AOC › aocs.desat_ineffective (0x029C); MCS › AOC › aocs.mode (0x020F); MCS › bottom drawer › Events |  |  |
| step 8 | Document the transition matrix: commanded rows carry the TC and its verification, automatic rows the trigge… | n/a | MCS › bottom drawer › Command history; MCS › TRD (trends) |  |  |

### WB-5.6-C006 — COM-006 TTC Link Verification (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 0 | Configure the S-band chain: EPS_POWER_ON(line_index=2) (func 19), TTC_PA_ON (func 66), TTC_SET_BEACON_MODE(… | screen | MCS › EPS › eps.pl_ttc_tx (0x0112); MCS › TTC › ttc.pa_on (0x0516); MCS › TTC › ttc.beacon_mode (0x0521); MCS › TTC › ttc.antenna_deployed (0x0520) |  |  |
| step 1 | Baseline the primary transponder: HK_REQUEST(sid=6) | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.link_margin (0x0503) |  |  |
| step 2 | RSSI vs elevation, read on the TT&C page at 10°, 30° and 60°+ | screen | MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.link_margin (0x0503) |  |  |
| step 2a | Baseline each rung, above 30°: TTC_SET_DATA_RATE(rate=0) (func 65) LOW; TTC_SET_DOWNLINK_MODE(on=1) (func 7… | screen | MCS › TTC › ttc.tm_data_rate (0x0506); MCS › TTC › ttc.tm_tier (0x0539); MCS › TTC › ttc.downlink_mode (0x053C); MCS › TTC › ttc.tm_symbol_rate (0x053B) |  |  |
| step 2b | Ground arm-through policy on HIGH (no on-board gate): below 10° elevation, try to arm HIGH in the MCS comma… | screen | MCS › CMD (command builder); MCS › TTC › Ground station network |  |  |
| step 3 | Switch to the redundant transponder: TTC_SWITCH_REDUNDANT (func 64) | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.mode (0x0500) |  |  |
| step 4 | Redundant transponder performance: HK_REQUEST(sid=6) | screen | MCS › TTC › ttc.link_margin (0x0503) |  |  |
| step 5 | Restore the primary: TTC_SWITCH_PRIMARY (func 63) | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.mode (0x0500) |  |  |
| step 6 | Command throughput: six rapid GET_PARAM(param_id=0x0105) … GET_PARAM(param_id=0x010A) (S20.3), then GET_PAR… | screen | MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.bat_capacity_wh (0x010A); MCS › OBD › obdh.tc_rej_count (0x0306) |  |  |
| step 7 | Multi-station verification on later passes: repeat steps 1–2 over each station of the network | screen | MCS › TTC › Ground station network; MCS › TTC › ttc.link_margin (0x0503); Planner › Next contacts |  |  |
| step 8 | Compile the link budget report: margin against elevation and against rate tier for each station, compared w… | screen | MCS › TTC › Predicted vs measured link; Manual 05 TTC › §5.3 Per-station link budget; Link budget (Wikipedia) |  |  |
| step 9 | Safe the link: TTC_SET_DATA_RATE(rate=0), TTC_SET_DOWNLINK_MODE(on=0), TTC_SWITCH_PRIMARY, HK_REQUEST(sid=6) | screen | MCS › TTC › ttc.tm_tier (0x0539); MCS › TTC › ttc.tm_tier_cmd (0x053A); MCS › TTC › ttc.downlink_mode (0x053C); MCS › TTC › ttc.beacon_mode (0x0521) |  |  |

### WB-5.6-C007 — COM-007 OBDH Checkout (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Verify the OBC mode: HK_REQUEST(sid=4) (S3.27) | screen | MCS › OBD › obdh.mode (0x0300) |  |  |
| step 2 | CPU utilisation: GET_PARAM(param_id=0x0302) (S20.3) | screen | MCS › OBD › obdh.cpu_load (0x0302) |  |  |
| step 3 | Memory status: GET_PARAM(param_id=0x0303) (obdh.mmm_used), GET_PARAM(param_id=0x031E) (obdh.mem_errors), GE… | screen | MCS › OBD › obdh.mmm_used (0x0303); MCS › OBD › obdh.mem_errors (0x031E); MCS › OBD › obdh.seu_count (0x0319) |  |  |
| step 4 | TC/TM packet counters: GET_PARAM(param_id=0x0304), GET_PARAM(param_id=0x0306), GET_PARAM(param_id=0x0307) | screen | MCS › OBD › obdh.tc_rx_count (0x0304); MCS › OBD › obdh.tc_rej_count (0x0306); MCS › OBD › obdh.tm_pkt_count (0x0307) |  |  |
| step 5 | Confirm NOMINAL-mode services — no mode command: commanding the mode you are in proves nothing | screen | MCS › OBD › obdh.mode (0x0300); MCS › OBD › obdh.cpu_load (0x0302) |  |  |
| step 6 | Autonomous HK generation: GET_PARAM(param_id=0x0307), wait 60 s sending no TC, GET_PARAM(param_id=0x0307) a… | screen | MCS › OBD › obdh.tm_pkt_count (0x0307) |  |  |
| step 7 | Watchdog: OBC_DIAGNOSTIC (S8.1 func 61), GET_PARAM(param_id=0x0316) | screen | MCS › OBD › obdh.last_reboot_cause (0x0316) |  |  |
| step 8 | OBC mode excursion NOMINAL → SAFE → NOMINAL: OBC_SET_MODE(mode=1), then OBC_SET_MODE(mode=0) (S8.1 func 50) | screen | MCS › OBD › obdh.mode (0x0300); MCS › OBD › Software state |  |  |
| step 9 | Record the OBDH baseline: CPU load, memory usage, error and SEU counters, TC/TM statistics, watchdog status | n/a | MCS › OBD page |  |  |

### WB-5.6-C008 — COM-008 FDIR Configuration (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Enable and inventory S12 monitoring: MON_ENABLE (S12.1), MON_REPORT_DEFS (S12.12) | screen | MCS › FDR › On-board monitoring (S12); MCS › PUS › S12 MONITOR; ECSS-E-ST-70-41C — Packet Utilization Standard (PDF) |  |  |
| step 2 | Inventory the S19 event-action table: EA_REPORT_DEFS (S19.8) | screen | MCS › AOC › aocs.h_env_frac (0x02BA); MCS › bottom drawer › Events |  |  |
| step 3 | FDIR summary telemetry: GET_PARAM(param_id=0x0700), GET_PARAM(param_id=0x0701) (S20.3) | screen | MCS › FDR › fdir.level (0x0700); MCS › FDR › fdir.active_alarms (0x0701) |  |  |
| step 4 | Functional test of the commanded load-shed latch: record eps.pl_payload (0x0113), eps.pl_fpa_cooler (0x0114… | screen | MCS › EPS › eps.pl_payload (0x0113); MCS › EPS › eps.pl_fpa_cooler (0x0114); MCS › EPS › eps.pl_ttc_tx (0x0112); MCS › EPS › eps.load_shed_stage (0x0134); MCS › bottom drawer › Events |  |  |
| step 5 | Confirm no residual protection state: GET_PARAM(param_id=0x0700), HK_REQUEST(sid=1), HK_REQUEST(sid=4) | screen | MCS › FDR › fdir.level (0x0700); MCS › OBD › obdh.mode (0x0300); MCS › EPS › eps.load_shed_stage (0x0134) |  |  |

### WB-5.6-C009 — COM-009 Payload Power-On (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Pre-power-on EPS baseline: HK_REQUEST(sid=1) (S3.27) | screen | MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.power_gen (0x0107) |  |  |
| step 2 | Verify the payload is OFF: HK_REQUEST(sid=5) | screen | MCS › PLD › payload.mode (0x0600) |  |  |
| step 3 | Energise the line, then STANDBY: EPS_POWER_ON(line_index=3) (S8.1 func_id 19), HK_REQUEST(sid=1), PAYLOAD_S… | screen | MCS › EPS › eps.pl_payload (0x0113); MCS › PLD › payload.mode (0x0600) |  |  |
| step 4 | Payload power draw: HK_REQUEST(sid=1), GET_PARAM(param_id=0x0106) (S20.3) | screen | MCS › EPS › eps.power_cons (0x0106); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 5 | Electronics health: HK_REQUEST(sid=5), GET_PARAM(param_id=0x0611), GET_PARAM(param_id=0x0603) | screen | MCS › PLD › payload.imager_status (0x0611); MCS › PLD › payload.imager_temp (0x0603) |  |  |
| step 6 | FPA temperature before the cooler: GET_PARAM(param_id=0x0601) | screen | MCS › PLD › payload.fpa_temp (0x0601) |  |  |
| step 7 | Data interface: GET_PARAM(param_id=0x0604), GET_PARAM(param_id=0x0648), GET_PARAM(param_id=0x0647) | screen | MCS › PLD › payload.store_used (0x0604); MCS › PLD › payload.product_count (0x0648); MCS › PLD › payload.product_mb (0x0647) |  |  |
| step 8 | Hold STANDBY 10 min for thermal stabilisation: HK_REQUEST(sid=3) at T+5 and T+10 min, HK_REQUEST(sid=5) | screen | MCS › TCS › tcs.temp_obc (0x0406); MCS › PLD › payload.fpa_temp (0x0601); MCS › PLD › payload.mode (0x0600) |  |  |
| step 9 | Log the Payload Power-On Report: timing, power draw, imager status word, imager and FPA temperatures, store… | n/a | MCS › PLD page |  |  |
| q10 | GO COM-010 | n/a |  |  |  |

### WB-5.6-C010 — COM-010 FPA Cooler Activation (confirm each step; spans eclipse)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Record the pre-activation state, cooler OFF (cool-down T = 0): HK_REQUEST(sid=3), HK_REQUEST(sid=6), HK_REQ… | screen | MCS › PLD › payload.fpa_temp (0x0601); MCS › TCS › tcs.temp_fpa (0x0408); MCS › PLD › payload.mode (0x0600) |  |  |
| step 2 | Enable the cooler: FPA_COOLER(on=1) (S8.1 func_id 43), then GET_PARAM(param_id=0x040C), GET_PARAM(param_id=… | screen | MCS › TCS › tcs.cooler_fpa (0x040C); MCS › EPS › eps.pl_fpa_cooler (0x0114) |  |  |
| step 3 | Cooler power draw: HK_REQUEST(sid=1), GET_PARAM(param_id=0x0106) (S20.3) | screen | MCS › EPS › eps.power_cons (0x0106); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 4 | First 5 minutes: GET_PARAM(param_id=0x0601) at T+2 and T+5 min (every minute on WB-5.6-FPA) | screen | MCS › PLD › payload.fpa_temp (0x0601) |  |  |
| step 5 | Settling: GET_PARAM(param_id=0x0601) at T+10 and T+15 min | screen | MCS › PLD › payload.fpa_temp (0x0601) |  |  |
| step 6 | Operational temperature: GET_PARAM(param_id=0x0601), GET_PARAM(param_id=0x0610), GET_PARAM(param_id=0x0631)… | screen | MCS › PLD › payload.fpa_temp (0x0601); MCS › PLD › payload.fpa_ready (0x0610); MCS › PLD › payload.fpa_setpoint (0x0631); MCS › PLD › payload.cooler_floor_c (0x064A) |  |  |
| step 7 | Stability: GET_PARAM(param_id=0x0601) at T+35, T+40 and T+45 min | screen | MCS › PLD › payload.fpa_temp (0x0601) |  |  |
| step 8 | Through eclipse, if the pass spans one: GET_PARAM(param_id=0x0601) | screen | MCS › PLD › payload.fpa_temp (0x0601); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 9 | Generate the Cooler Activation Report: cool-down curve, cooler power, stability and eclipse data | screen | MCS › TRD (trends) |  |  |
| q10 | GO COM-011 | n/a |  |  |  |

### WB-5.6-FPA — FPA Cool-Down Monitor Sheet

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | T_fpa (°C) · payload.cooler_pwr 0x0602 (W) · Eclipse? · Note | screen | MCS › PLD › payload.fpa_temp (0x0601); MCS › PLD › payload.cooler_pwr (0x0602); MCS › TRD (trends) |  |  |
| q2 | payload.fpa_ready (0x0610) set at elapsed | screen | MCS › PLD › payload.fpa_ready (0x0610) |  |  |
| q3 | payload.cooler_margin_k (0x064B) at setpoint | screen | MCS › PLD › payload.cooler_margin_k (0x064B) |  |  |

### WB-5.6-C011 — COM-011 Payload Calibration (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Pre-calibration state, cooler ON first: FPA_COOLER(on=1) (S8.1 func 43), HK_REQUEST(sid=3), HK_REQUEST(sid=… | screen | MCS › PLD › payload.mem_used_mb (0x060B); MCS › PLD › payload.mem_total_mb (0x060A); MCS › TCS › tcs.cooler_fpa (0x040C); MCS › PLD › payload.mode (0x0600) |  |  |
| step 2 | Close the shutter: PAYLOAD_SET_SHUTTER(position=0) (S8.1 func 119), GET_PARAM(param_id=0x063C) | screen | MCS › PLD › payload.shutter_pos (0x063C) |  |  |
| step 3 | Dark set, from STANDBY with no mode command (STANDBY would switch the cooler off): PAYLOAD_CAL_LAMP(on=0) (… | screen | MCS › PLD › payload.dark_frame_cnt (0x0642); MCS › PLD › payload.calibration_active (0x062A); MCS › PLD › payload.cal_abort_reason (0x0645); MCS › PLD › payload.mode (0x0600) |  |  |
| step 3a | Flat-field set: PAYLOAD_SET_SHUTTER(position=1), PAYLOAD_CAL_LAMP(on=1), GET_PARAM(param_id=0x0615), GET_PA… | screen | MCS › PLD › payload.cal_lamp_on (0x0615); MCS › PLD › payload.shutter_pos (0x063C); MCS › PLD › payload.cal_valid_mask (0x0646); MCS › PLD › payload.calibration_active (0x062A) |  |  |
| step 4 | Dark-frame quality, on the ground from the downlinked frames: GET_PARAM(param_id=0x0642) | screen | MCS › PLD › payload.dark_frame_cnt (0x0642) |  |  |
| step 5 | Open the shutter; the sequencer has already put the payload back in STANDBY, cooler running — no mode comma… | screen | MCS › PLD › payload.shutter_pos (0x063C); MCS › PLD › payload.mode (0x0600) |  |  |
| step 6 | Calibration-site overpass: AOCS_FINE_READY_CHECK (func 89), then AOCS_SET_MODE(mode=5) (func 0) — FINE_POIN… | screen | MCS › AOC › aocs.fine_ready (0x02C5); MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 7 | Site image at the overpass: PAYLOAD_SET_MODE(mode=2) (IMAGING), PAYLOAD_CAPTURE(scene_id=0, lines=2048) (fu… | screen | MCS › PLD › payload.last_scene_id (0x060C); MCS › PLD › payload.mode (0x0600) |  |  |
| step 8 | Linearity pair: PAYLOAD_SET_INTEGRATION_TIME(blue_ms=1.00, green_ms=1.00, red_ms=1.00, nir_ms=1.00) (func 3… | not at all | Manual 06 Payload › §4 Data storage | The mean DN of a frame is an image-processing result: no tool reads the downlinked frames. | **Deferred:** Needs an image quick-look on the ground (a delayed-TM or payload tool); out of this audit's scope. |
| step 9 | Return to the standard configuration: PAYLOAD_SET_MODE(mode=1), PAYLOAD_SET_INTEGRATION_TIME(blue_ms=2.00, … | screen | MCS › TCS › tcs.cooler_fpa (0x040C); MCS › PLD › payload.mode (0x0600); MCS › AOC › aocs.mode (0x020F) |  |  |
| step 10 | Data stored, downlink scheduled: GET_PARAM(param_id=0x0647), GET_PARAM(param_id=0x0648) | screen | MCS › PLD › payload.product_mb (0x0647); MCS › PLD › payload.product_count (0x0648) |  |  |
| q12 | GO COM-012 | n/a |  |  |  |

### WB-5.6-C012 — COM-012 First Light (confirm each step)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | AOCS to FINE_POINT: AOCS_FINE_READY_CHECK (func 89) — the mask must read 0, or mode 5 is refused TM(1,8) — … | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.total_pointing_err_3sig (0x02AA); MCS › AOC › aocs.att_error (0x0217); MCS › AOC › aocs.rate_pitch (0x0205); MCS › bottom drawer › Command history |  |  |
| step 2 | FPA temperature: GET_PARAM(param_id=0x0601) (S20.3) | screen | MCS › PLD › payload.fpa_temp (0x0601); MCS › PLD › payload.fpa_ready (0x0610) |  |  |
| step 3 | Payload ready, baselines: HK_REQUEST(sid=5), GET_PARAM(param_id=0x0604), GET_PARAM(param_id=0x0605), GET_PA… | screen | MCS › PLD › payload.store_used (0x0604); MCS › PLD › payload.image_count (0x0605); MCS › PLD › payload.mem_used_mb (0x060B); MCS › PLD › payload.mode (0x0600) |  |  |
| step 4 | IMAGING: PAYLOAD_SET_MODE(mode=2) (func 26) | screen | MCS › PLD › payload.mode (0x0600) |  |  |
| step 5 | First capture: PAYLOAD_CAPTURE(scene_id=1, lines=2048) (S8.1 func 28) | screen | MCS › PLD › payload.last_scene_id (0x060C); MCS › PLD › payload.image_count (0x0605) |  |  |
| step 6 | Image written: GET_PARAM(param_id=0x0604), GET_PARAM(param_id=0x060B) | screen | MCS › PLD › payload.store_used (0x0604); MCS › PLD › payload.mem_used_mb (0x060B) |  |  |
| step 7 | Back to STANDBY: PAYLOAD_SET_MODE(mode=1) | screen | MCS › TCS › tcs.cooler_fpa (0x040C); MCS › PLD › payload.mode (0x0600) |  |  |
| step 8 | Downlink over Service 13: TTC_SET_DOWNLINK_MODE(on=1), TTC_SET_DATA_RATE(rate=1) (HIGH), S13_CREATE_TRANSFE… | screen | MCS › TTC › ttc.tm_data_rate (0x0506); MCS › PLD › payload.transfer_active (0x062D); MCS › PLD › payload.transfer_progress (0x062E); MCS › TTC › ttc.downlink_mode (0x053C) |  |  |
| step 9 | First Light assessment: AOCS_SET_MODE(mode=4), HK_REQUEST(sid=2), HK_REQUEST(sid=5) | screen | MCS › PLD › payload.cooler_pwr (0x0602); MCS › AOC › aocs.mode (0x020F); MCS › PLD › payload.mode (0x0600) |  |  |
| q10 | If deferred, justification | n/a |  |  |  |

### WB-5.6-FL — First Light Image Assessment

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Image ID | screen | MCS › PLD › payload.last_scene_id (0x060C); MCS › PLD › payload.image_count (0x0605) |  |  |
| q2 | Target name | screen | Planner › Imaging opportunities |  |  |
| q3 | Acquisition UTC | screen | MCS › bottom drawer › Events |  |  |
| q4 | AOCS mode at acquisition | screen | MCS › AOC › aocs.mode (0x020F); MCS › TRD (trends) |  |  |
| q5 | FPA temperature at acquisition (°C) | screen | MCS › PLD › payload.fpa_temp (0x0601); MCS › TRD (trends) |  |  |
| q6 | Integration time per band (ms), bands at 443/560/665/865 nm | manual only | MCS › bottom drawer › Command history; Manual 06 Payload › §2 Instrument characteristics | The integration times are what was commanded (command history); no parameter reports them. |  |
| q7 | Image size (MB) — expect 1.0–2.7 stored (4 raw) | screen | MCS › PLD › payload.mem_used_mb (0x060B); MCS › PLD › payload.product_mb (0x0647) |  |  |
| q8 | Ground swath (km) — payload.swath_width_km (0x0619) | n/a | MCS › PLD › payload.swath_width_km (0x0619) |  |  |
| q9 | GSD (m) — payload.gsd_m (0x0628) | n/a | MCS › PLD › payload.gsd_m (0x0628) |  |  |
| q10 | Mean DN per band | not at all |  | Image-processing result; no tool reads the frames. | **Deferred:** Needs an image quick-look tool. |
| q11 | Cloud cover (%) | not at all |  | Image-processing result; no tool reads the frames. | **Deferred:** Needs an image quick-look tool. |
| q12 | Geo-registration error (m) — aocs.geoloc_err_m (0x02C7) | n/a | MCS › AOC › aocs.geoloc_err_m (0x02C7) |  |  |
| q13 | Quality verdict | n/a |  |  |  |
| q14 | Customer bulletin drafted? (Mission Mgr) | n/a |  |  |  |

### WB-5.6-MA — Day 4 Multi-Anomaly Response Form

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | First indicator time · Position to flag it · Procedure invoked · Recovery time (s) · Outcome · FD sig | screen | MCS › FDR › Alarm / anomaly journal; MCS › bottom drawer › Command history |  |  |
| q2 | Order of priority taken | n/a |  |  |  |
| q3 | Conflicts encountered (procedure A requires X, procedure B requires not-X) | n/a |  |  |  |
| q4 | How conflicts resolved | n/a |  |  |  |

### WB-5.6-GO — Day 4 Pass-Set Criteria Scorecard

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Phase advanced to COMMISSIONING (5) — SYS_SET_MISSION_PHASE (func 120) sent and verified | screen | MCS › EPS › eps.spacecraft_phase (0x0129); MCS › bottom drawer › Command history |  |  |
| q2 | EPS checkout complete, no faults | n/a | MCS › EPS page |  |  |
| q3 | AOCS NOMINAL (mode 4) achieved, aocs.att_error < 1.0°; FINE_POINT (5) demonstrated at < 0.1° | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| q4 | FDIR rule set verified and exercised on the FDIR panel | screen | MCS › FDR › On-board monitoring (S12); MCS › FDR › Event-action rules (S19) |  |  |
| q5 | Payload powered ON (eps.pl_payload 0x0113 = 1, payload.mode = 1) | n/a | MCS › EPS › eps.pl_payload (0x0113); MCS › PLD › payload.mode (0x0600) |  |  |
| q6 | FPA cooler demonstrated at its commanded setpoint (−15 °C default) in COM-010, payload.fpa_ready (0x0610) =… | n/a | MCS › PLD › payload.fpa_ready (0x0610) |  |  |
| q7 | First Light image acquired or formally deferred | screen | MCS › PLD › payload.image_count (0x0605) |  |  |
| q8 | Anomaly tickets filed for all injections | n/a |  |  |  |

### WB-5.6-OBS — Day 4 Observer Worksheets (axes: Team + Space usage)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Did each position know its role? | n/a |  |  |  |
| q2 | Was the FD authoritative? | n/a |  |  |  |
| q3 | Anyone over-loaded or under-utilised? | n/a |  |  |  |
| q4 | Did anyone do another position's job? | n/a |  |  |  |
| q5 | Was fatigue handled (breaks, water)? | n/a |  |  |  |
| q6 | How did the team handle disagreement? | n/a |  |  |  |
| q7 | Worked well | n/a |  |  |  |
| q8 | Could improve | n/a |  |  |  |
| q9 | Specific recommendation | n/a |  |  |  |
| q10 | Console layout — could every position see what they needed? | n/a |  |  |  |
| q11 | Line of sight — could FD see all positions? | n/a |  |  |  |
| q12 | Distractions (phones, side talk, music)? | n/a |  |  |  |
| q13 | Lighting, temperature, noise — issues? | n/a |  |  |  |
| q14 | Movement around the room (procedures, water) | n/a |  |  |  |
| q15 | Physical comfort — chairs, monitors, posture | n/a |  |  |  |
| q16 | Worked well | n/a |  |  |  |
| q17 | Could improve | n/a |  |  |  |
| q18 | Specific recommendation | n/a |  |  |  |

### WB-5.6-HO — Day 4 Inter-Pass Handover Turnover Form

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Outgoing operator | n/a |  |  |  |
| q2 | Incoming operator | n/a |  |  |  |
| q3 | Current parameter values (top 3) | screen | MCS › OVR (overview) |  |  |
| q4 | Current procedure state (file ID + step) | screen | MCS › PRC (procedures) |  |  |
| q5 | Console page left open for the next operator (page, panel) | screen (was not at all) | MCS › OVR (overview) | Asked for a "pinned widget": neither console has pinned widgets. | Reworded, as on WB-5.5-HO. |
| q6 | FDIR rules currently active (acknowledged) | screen | MCS › FDR › Alarm / anomaly journal; MCS › FDR › Event-action rules (S19) |  |  |
| q7 | Open question for next shift | n/a |  |  |  |
| q8 | Time | screen | MCS › OVR (overview) |  |  |

### WB-5.6-DB — Day 4 Post-Shift Debrief Reflection

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | What is one decision you took during the shift that, in retrospect, you would not take again? Why? | n/a |  |  |  |
| q2 | What is one decision that surprised you with how well it worked? | n/a |  |  |  |
| q3 | Which procedure step did you most struggle to execute in real time? | n/a |  |  |  |
| q4 | What is one thing the team did better as a unit than you expected? | n/a |  |  |  |
| q5 | What is one specific thing you will take into your future engineering work? | n/a |  |  |  |

### WB-A-CTG-001 — CTG-001 Under-Voltage Load Shed

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | EPS: Detect and confirm, and read what FDIR has already shed: HK_REQUEST(sid=1) (S3.27). FD authorises; ann… | screen | MCS › EPS › eps.uv_flag (0x010E); MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.bat_voltage (0x0100) |  |  |
| step 2 | EPS: Priority 1, payload OFF (payload line still ON): PAYLOAD_SET_MODE(mode=0) (S8.1 func 26), HK_REQUEST(s… | screen | MCS › PLD › payload.mode (0x0600); MCS › EPS › eps.power_cons (0x0106); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 3 | EPS: Priority 2, FPA cooler OFF (cooler line still ON): FPA_COOLER(on=0) (func 43), GET_PARAM(param_id=0x04… | screen | MCS › TCS › tcs.cooler_fpa (0x040C); MCS › EPS › eps.power_cons (0x0106); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 4 | EPS: Priority 3, transmitter OFF (ttc_tx line still ON): TTC_PA_OFF (func 67), HK_REQUEST(sid=6), HK_REQUES… | screen | MCS › TTC › ttc.pa_on (0x0516); MCS › EPS › eps.power_cons (0x0106); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 5 | EPS: Priority 4, wheels line OFF (still ON): EPS_POWER_OFF(line_index=7) (func 20), HK_REQUEST(sid=1) 30 s … | screen | MCS › EPS › eps.pl_aocs_wheels (0x0117); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 5B | 5B. EPS: Last resort only, every level taken and the bus still falling — OBC EMERGENCY: OBC_SET_MODE(mode=2… | screen | MCS › OBD › obdh.mode (0x0300) |  |  |
| step 6 | EPS: Monitor recovery: HK_REQUEST(sid=1) every 60 s | screen | MCS › EPS › eps.bat_current (0x0109); MCS › EPS › eps.bus_voltage (0x0105); MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.power_gen (0x0107) |  |  |
| step 7 | EPS: Restore in reverse priority, bus stable 5 min between loads, each line powered before its unit: EPS_PO… | screen | MCS › AOC › aocs.mode (0x020F); MCS › EPS › eps.pl_ttc_tx (0x0112); MCS › EPS › eps.pl_fpa_cooler (0x0114); MCS › EPS › eps.pl_payload (0x0113) |  |  |

### WB-A-CTG-002 — CTG-002 AOCS Anomaly Recovery

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Assess the AOCS state: HK_REQUEST(sid=2) (S3.27) | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 2 | Wheel health: HK_REQUEST(sid=2) | screen | MCS › AOC › aocs.rw1_speed (0x0207); MCS › AOC › aocs.rw4_speed (0x020A); MCS › AOC › aocs.rw1_temp (0x0218); MCS › AOC › aocs.rw4_temp (0x021B) |  |  |
| step 3 | Disable the failed wheel: AOCS_DISABLE_WHEEL(wheel_idx=N) (S8.1 func 2) | screen | MCS › AOC › aocs.rw1_speed (0x0207); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 4 | Desaturate: AOCS_DESATURATE (S8.1 func 1) | screen | MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_yaw (0x0206); MCS › AOC › aocs.rate_pitch (0x0205) |  |  |
| step 5 | Body rates stable: HK_REQUEST(sid=2) | screen | MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_pitch (0x0205); MCS › AOC › aocs.rate_yaw (0x0206) |  |  |
| step 6 | Restore NOMINAL: AOCS_SET_MODE(mode=4) (S8.1 func 0) | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 7 | Escalation on a multi-wheel failure only: AOCS_SET_MODE(mode=2) — DETUMBLE | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.rate_roll (0x0204) |  |  |

### WB-A-CTG-007 — CTG-007 Reaction Wheel Anomaly

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Identify the wheel: HK_REQUEST(sid=2) (S3.27) | screen | MCS › AOC › aocs.rw1_speed (0x0207); MCS › AOC › aocs.rw4_speed (0x020A); MCS › AOC › aocs.rw1_temp (0x0218); MCS › AOC › aocs.rw4_temp (0x021B) |  |  |
| step 2 | Disable it: AOCS_DISABLE_WHEEL(wheel_idx=N) (S8.1 func 2) | screen | MCS › AOC › aocs.att_error (0x0217); MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_yaw (0x0206); MCS › AOC › aocs.rate_pitch (0x0205) |  |  |
| step 3 | Three-wheel control: watch the AOCS reconfigure — no command | screen | MCS › AOC › aocs.att_error (0x0217); MCS › AOC page |  |  |
| step 4 | Desaturate the three: AOCS_DESATURATE (S8.1 func 1) | screen | MCS › AOC › aocs.rw1_speed (0x0207); MCS › AOC › aocs.rw2_speed (0x0208); MCS › AOC › aocs.rw3_speed (0x0209); MCS › AOC › aocs.rw4_speed (0x020A) |  |  |
| step 5 | Stable pointing on three wheels: HK_REQUEST(sid=2) every 60 s for 5 min | screen | MCS › AOC › aocs.att_error (0x0217); MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_pitch (0x0205); MCS › AOC › aocs.rate_yaw (0x0206) |  |  |
| step 6 | NOMINAL on three wheels: AOCS_SET_MODE(mode=4) (S8.1 func 0) | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 7 | Wheel recovery, ground-authorised attempt only: AOCS_ENABLE_WHEEL(wheel_idx=N) (S8.1 func 3) | screen | MCS › AOC page |  |  |

### WB-A-CTG-008 — CTG-008 Star Tracker Failure

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Confirm the ST1 failure: HK_REQUEST(sid=2) (S3.27) | screen | MCS › AOC › aocs.st1_status (0x0240); MCS › AOC › aocs.st1_num_stars (0x0241); MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 2 | Power on ST2: ST2_POWER(on=1) (S8.1 func 5), HK_REQUEST(sid=2) | screen | MCS › AOC › aocs.st2_status (0x0243) |  |  |
| step 3 | Select ST2: ST_SELECT(unit=2) (S8.1 func 6; wire encoding 1 = ST1, 2 = ST2), HK_REQUEST(sid=2) 10 s later | screen | MCS › AOC › aocs.st2_status (0x0243); MCS › AOC › aocs.att_error (0x0217); MCS › AOC › aocs.mode (0x020F) |  |  |
| step 4 | Isolate ST1: ST1_POWER(on=0) (S8.1 func 4), HK_REQUEST(sid=2) | screen | MCS › AOC › aocs.st1_num_stars (0x0241); MCS › AOC › aocs.att_error (0x0217); MCS › AOC › aocs.rate_roll (0x0204); MCS › AOC › aocs.rate_yaw (0x0206) |  |  |
| step 5 | Fallback, both trackers failed: AOCS_SET_MODE(mode=3) COARSE_SUN (S8.1 func 0), HK_REQUEST(sid=2), PAYLOAD_… | screen | MCS › AOC › aocs.css_valid (0x0248); MCS › AOC › aocs.css_sun_x (0x0245); MCS › AOC › aocs.css_sun_z (0x0247); MCS › AOC › aocs.mode (0x020F) |  |  |
| step 6 | End of procedure: a final HK_REQUEST(sid=2) | screen | MCS › AOC page |  |  |

### WB-A-CTG-009 — CTG-009 Solar Array Degradation

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Quantify the loss: HK_REQUEST(sid=1) (S3.27), GET_PARAM(param_id=0x014C), GET_PARAM(param_id=0x014D), GET_P… | screen | MCS › EPS › eps.sa_a_yield_pct (0x014C); MCS › EPS › eps.sa_b_yield_pct (0x014D); MCS › EPS › eps.sa_string_lit (0x014E); MCS › EPS › eps.sa_a_current (0x0103) |  |  |
| step 2 | Compare the strings: HK_REQUEST(sid=1) three times, 30 s apart | screen | MCS › EPS › eps.sa_a_current (0x0103); MCS › EPS › eps.sa_b_current (0x0104) |  |  |
| step 3 | Rule out attitude: HK_REQUEST(sid=2) | screen | MCS › AOC › aocs.mode (0x020F); MCS › AOC › aocs.att_error (0x0217) |  |  |
| step 4 | Decide: shed the payload or continue. HK_REQUEST(sid=1); judge the severity from the yield (row 1) and the … | screen | MCS › EPS › Power flow; MCS › EPS › Projections › Orbit-average margin; MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.power_cons (0x0106); MCS › EPS › eps.power_gen (0x0107) |  | The projected SoC at the end of the next eclipse is the EPS power flow's "at eclipse exit"; the margin is in Projections. |
| step 5 | Shed: PAYLOAD_SET_MODE(mode=1) (S8.1 func 26, STANDBY); still short: PAYLOAD_SET_MODE(mode=0) and, if no ma… | screen | MCS › PLD › payload.mode (0x0600); MCS › EPS › eps.power_cons (0x0106) |  |  |
| step 6 | Sun-optimal attitude: AOCS_SET_MODE(mode=3) (S8.1 func 0, COARSE_SUN) | screen | MCS › AOC › aocs.mode (0x020F); MCS › EPS › eps.sa_a_current (0x0103); MCS › EPS › eps.sa_b_current (0x0104); MCS › EPS › eps.power_gen (0x0107) |  |  |
| step 7 | Monitoring plan: HK_REQUEST(sid=1) as the new baseline; one wing lost: GET_PARAM(param_id=0x0144) | screen | MCS › EPS › eps.wing_status (0x0144); MCS › EPS › eps.sa_a_current (0x0103); MCS › EPS › eps.sa_b_current (0x0104); MCS › EPS › eps.power_gen (0x0107) |  |  |

### WB-A-CTG-010 — CTG-010 OBDH Watchdog Recovery

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Confirm the watchdog reset: HK_REQUEST(sid=4) (S3.27) | screen | MCS › OBD › obdh.reboot_count (0x030A); MCS › OBD › obdh.mode (0x0300); MCS › OBD › obdh.cpu_load (0x0302) |  |  |
| step 1b | Only if obdh.sw_image (0x0311) = 0 (bootloader): OBC_BOOT_APP (S8.1 func 55) — before any HK_ENABLE or OBC_… | screen | MCS › OBD › obdh.sw_image (0x0311); MCS › bottom drawer › Command history |  |  |
| step 2 | Post-reboot state: HK_REQUEST(sid=4) | screen | MCS › OBD › obdh.mode (0x0300); MCS › OBD › obdh.cpu_load (0x0302) |  |  |
| step 3 | All housekeeping: HK_REQUEST (S3.27) of SIDs 1, 2, 3, 4, 5, 6 | screen | MCS › PUS › S3 HK (Observed column) |  |  |
| step 4 | Time and data integrity: HK_REQUEST(sid=2) for aocs.gps_fix, SET_TIME(cuc_seconds=T_corrected) (S9.1), OBC_… | screen | MCS › OBD › obdh.time_ref (0x0A13); MCS › AOC › aocs.gps_fix (0x0274) |  |  |
| step 5 | Root-cause indicators: HK_REQUEST(sid=1); review the obdh.cpu_load (0x0302) trend and the EPS data before t… | screen | MCS › OBD › obdh.cpu_load (0x0302); MCS › EPS › eps.bus_voltage (0x0105) |  |  |
| step 6 | Restore NOMINAL if the OBC is in SAFE: OBC_SET_MODE(mode=0) (S8.1 func 50) | screen | MCS › OBD › obdh.mode (0x0300); MCS › AOC › aocs.mode (0x020F); MCS › OBD › obdh.cpu_load (0x0302) |  |  |

### WB-A-CTG-012 — CTG-012 Overcurrent Response

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Identify the tripped line(s): HK_REQUEST(sid=1) (S3.27) | screen | MCS › EPS › eps.oc_trip_flags (0x010D) |  |  |
| step 2 | Per-line current: HK_REQUEST(sid=1) | screen | MCS › EPS › eps.line_current_0 (0x0118); MCS › EPS › eps.line_current_7 (0x011F); MCS › EPS › eps.pl_obc (0x0110); MCS › EPS › eps.pl_aocs_wheels (0x0117) |  |  |
| step 3 | Isolate the fault — coordinate with the affected subsystem's position (TT&C, Payload, EPS/TCS, AOCS): known… | n/a | MCS › bottom drawer › Command history; MCS › TRD (trends) |  |  |
| step 4 | Reset the overcurrent flag: EPS_RESET_OC_FLAG(line_index=N) (S8.1 func 21) | screen | MCS › EPS › eps.oc_trip_flags (0x010D) |  |  |
| step 5 | Re-enable the line: EPS_POWER_ON(line_index=N) (S8.1 func 19) | screen | MCS › EPS › eps.pl_obc (0x0110); MCS › EPS › eps.line_current_0 (0x0118); MCS › EPS › eps.oc_trip_flags (0x010D) |  |  |
| step 6 | Downstream recovery: HK_REQUEST of the owner's SID (2 AOCS, 5 Payload, 6 TT&C, 3 heaters) and HK_REQUEST(si… | screen | MCS › EPS › eps.power_cons (0x0106); MCS › EPS › eps.bus_voltage (0x0105) |  |  |

### WB-A-CTG-015 — CTG-015 Corrupted Image Recovery

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Detect and quantify: HK_REQUEST(sid=5) (S3.27) | screen | MCS › PLD › payload.checksum_errors (0x0609); MCS › PLD › payload.last_scene_id (0x060C); MCS › PLD › payload.image_count (0x0605) |  |  |
| step 2 | FPA check: HK_REQUEST(sid=5), HK_REQUEST(sid=3) | screen | MCS › PLD › payload.fpa_temp (0x0601); MCS › TCS › tcs.temp_fpa (0x0408); MCS › PLD › payload.fpa_ready (0x0610); MCS › TCS › tcs.cooler_fpa (0x040C) |  |  |
| step 3 | FPA warm — abort and cool down: PAYLOAD_SET_MODE(mode=1) (S8.1 func 26), FPA_COOLER(on=1) (func 43), GET_PA… | screen | MCS › TCS › tcs.cooler_fpa (0x040C); MCS › PLD › payload.mode (0x0600); MCS › PLD › payload.fpa_temp (0x0601); MCS › PLD › payload.fpa_ready (0x0610) |  |  |
| step 4 | Memory segments: HK_REQUEST(sid=5) | screen | MCS › PLD › payload.mem_segments_bad (0x0612); MCS › PLD › payload.store_used (0x0604) |  |  |
| step 5 | Delete and re-capture: PAYLOAD_DELETE_IMAGE(scene_id=N) (func 30), then PAYLOAD_CAPTURE(scene_id=N, lines=L… | screen | MCS › AOC › aocs.att_error (0x0217); MCS › PLD › payload.image_count (0x0605); MCS › PLD › payload.checksum_errors (0x0609); MCS › PLD › payload.fpa_ready (0x0610) |  |  |
| step 6 | Post-capture verification: HK_REQUEST(sid=5) | screen | MCS › PLD › payload.checksum_errors (0x0609); MCS › PLD › payload.store_used (0x0604) |  |  |

### WB-A-CTG-017 — CTG-017 Bus Failure Switchover

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Detect missing housekeeping: HK_REQUEST (S3.27) of SIDs 1, 2, 3, 4, 5, 6 | screen | MCS › PUS › S3 HK (Observed column); MCS › header › Can I see it? |  |  |
| step 2 | Bus status: HK_REQUEST(sid=4) | screen | MCS › OBD › obdh.bus_a_status (0x030F); MCS › OBD › obdh.bus_b_status (0x0310); MCS › OBD › obdh.active_bus (0x030E) |  |  |
| step 3 | Switch the bus: OBC_SELECT_BUS(bus=1) from A to B, or OBC_SELECT_BUS(bus=0) from B to A (S8.1 func_id 54); … | screen | MCS › OBD › obdh.active_bus (0x030E); MCS › OBD › obdh.bus_a_status (0x030F); MCS › OBD › obdh.bus_b_status (0x0310) |  |  |
| step 4 | Verify all housekeeping resumes: HK_REQUEST of SIDs 1–6 again | screen | MCS › EPS › eps.bat_soc (0x0101); MCS › EPS › eps.bus_voltage (0x0105); MCS › AOC › aocs.mode (0x020F); MCS › PLD › payload.mode (0x0600) |  |  |
| step 5 | Post-switchover assessment: log the HK-loss time, the failed bus, the gap, the affected subsystems and the … | n/a | MCS › bottom drawer › Log |  |  |

### WB-A-CTG-019 — CTG-019 No Telemetry at Pass Start

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Confirm the ground station is nominal: antenna tracking with valid pointing, uplink transmitter on frequenc… | n/a | Radio › Lock status; Radio › RF measurements |  |  |
| step 2 | TT&C TX power line, blind: HK_REQUEST(sid=1) (S3.27), EPS_POWER_ON(line_index=2) (S8.1 func 19); wait 30 s | screen | Radio › Lock status; MCS › TTC › Link lock chain |  |  |
| step 3 | Transponder switch, blind: TTC_SWITCH_REDUNDANT (func 64), wait 45 s; then TTC_SWITCH_PRIMARY (func 63) | screen | Radio › Lock status; MCS › TTC › ttc.mode (0x0500) |  |  |
| step 4 | PA on, blind: TTC_PA_ON (func 66), wait 15 s; still nothing: TTC_PA_OFF (func 67), 10 s, TTC_PA_ON, 15 s | screen | Radio › Lock status; MCS › TTC › ttc.pa_on (0x0516) |  |  |
| step 5 | Antenna, only if its deployment is uncertain or known stowed: TTC_DEPLOY_ANTENNA (func 69) — irreversible b… | screen | MCS › TTC › ttc.antenna_deployed (0x0520); MCS › TTC › ttc.antenna_deployment_sensor (0x0536); MCS › TTC › ttc.antenna_deployment_ready (0x0535) |  |  |
| step 6 | Verify link quality and subsystem health: HK_REQUEST(sid=6), HK_REQUEST(sid=1), HK_REQUEST(sid=4) | screen | MCS › TTC › ttc.link_status (0x0501); MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.link_margin (0x0503); MCS › TTC › ttc.pa_on (0x0516) |  |  |
| step 7 | Escalation, no link: TTC_SET_TX_POWER(level=2) (S8.1 func 68) for the next attempt; log every blind command… | n/a | MCS › bottom drawer › Command history |  |  |

### WB-A-CTG-020 — CTG-020 Ground Station Antenna Failure

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| step 1 | Confirm the signal loss is not spacecraft-side. Last frame before the loss: ttc.rssi (0x0502) nominal, ttc.… | screen | MCS › TTC › ttc.rssi (0x0502); MCS › TTC › ttc.link_margin (0x0503); MCS › TTC › ttc.pa_on (0x0516); MCS › TTC › ttc.pa_temp (0x050F) |  |  |
| step 2 | Attempt local ground station recovery: antenna controller reset or re-acquisition of the track; backup LNA,… | n/a |  |  |  |
| step 3 | Notify the Flight Director and assess the impact: "GS [station] antenna failure at [time]; spacecraft healt… | n/a | Planner › Next contacts |  |  |
| step 4 | Coordinate an alternate ground station (FD authorises): next windows at the other stations of the network, … | screen | Planner › Next contacts; Orbit tools › Passes (AOS, TCA, LOS) |  |  |
| step 5 | Replan the contact schedule: drop the failed station until it is repaired, add alternate passes, assess the… | screen | Planner › Activity schedule; Planner › Next contacts |  |  |

### WB-5.7-SA — Day 5 Personal Self-Assessment

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Voice-loop discipline | n/a |  |  |  |
| q2 | Procedure compliance | n/a |  |  |  |
| q3 | Telemetry interpretation | n/a |  |  |  |
| q4 | Anomaly response timing | n/a |  |  |  |
| q5 | Handover quality | n/a |  |  |  |
| q6 | Position rotation completion | n/a |  |  |  |
| q7 | Pass-plan quality (Day 1 exercise) | n/a |  |  |  |
| q8 | Quiz score / 15 | n/a |  |  |  |
| q9 | Debrief contribution | n/a |  |  |  |
| q10 | Three things I am proudest of this week | n/a |  |  |  |
| q11 | Three things I want to keep working on | n/a |  |  |  |

### WB-5.7-LL — Cohort Lessons-Learned Contribution

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Title | n/a |  |  |  |
| q2 | What we observed | n/a |  |  |  |
| q3 | Why it matters | n/a |  |  |  |
| q4 | Recommendation | n/a |  |  |  |
| q5 | Title | n/a |  |  |  |
| q6 | What we observed | n/a |  |  |  |
| q7 | Why it matters | n/a |  |  |  |
| q8 | Recommendation | n/a |  |  |  |
| q9 | Title | n/a |  |  |  |
| q10 | What we observed | n/a |  |  |  |
| q11 | Why it matters | n/a |  |  |  |
| q12 | Recommendation | n/a |  |  |  |

### WB-5.7-WI — "What If" Branch Reflection

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Original decision | n/a |  |  |  |
| q2 | Alternative decision tried in replay | n/a |  |  |  |
| q3 | What changed in the next 15 simulated minutes | n/a |  |  |  |
| q4 | Which decision would you take next time? Why? | n/a |  |  |  |

### WB-5.7-FR — Final Mission Review Prep

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Operated all 9 positions for at least one full pass | n/a |  |  |  |
| q2 | Ran a planning cycle end-to-end | n/a |  |  |  |
| q3 | Executed one nominal procedure as lead | n/a |  |  |  |
| q4 | Executed one contingency procedure as lead | n/a |  |  |  |
| q5 | Critiqued a peer team's shift | n/a |  |  |  |
| q6 | Produced a shift log and anomaly ticket | n/a |  |  |  |
| q7 | Three most-watched parameters and their typical values | screen | MCS › TRD (trends) |  |  |
| q8 | Wed — Anomaly · Procedure · Outcome · Root cause | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q9 | Wed — Anomaly · Procedure · Outcome · Root cause | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q10 | Thu — Anomaly · Procedure · Outcome · Root cause | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q11 | Thu — Anomaly · Procedure · Outcome · Root cause | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q12 | 5.1 Operability principles | n/a | ECSS-E-ST-70-11C — Space segment operability |  |  |
| q13 | 5.2 Operations preparation | n/a | ECSS-E-ST-70-11C — Space segment operability |  |  |
| q14 | 5.3 Procedure design | n/a | ECSS-E-ST-70-11C — Space segment operability |  |  |
| q15 | 5.4 Anomaly management | n/a | ECSS-E-ST-70-11C — Space segment operability |  |  |
| q16 | 5.5 Reporting and review | n/a | ECSS-E-ST-70-11C — Space segment operability |  |  |
| q17 | FD | n/a |  |  |  |
| q18 | SPACON | n/a |  |  |  |
| q19 | AOCS | n/a |  |  |  |
| q20 | EPS | n/a |  |  |  |
| q21 | Thermal | n/a |  |  |  |
| q22 | TT&C | n/a |  |  |  |
| q23 | Payload | n/a |  |  |  |
| q24 | FDS | n/a |  |  |  |
| q25 | Ground Seg | n/a |  |  |  |
| q26 | Mission Manager | n/a |  |  |  |
| q27 | Section 6 — Recommendations for next cycle | n/a |  |  |  |

### WB-B — End-of-Week Shift Log (cohort copy)

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | Shift date | n/a |  |  |  |
| q2 | Shift FD | n/a |  |  |  |
| q3 | Team | n/a |  |  |  |
| q4 | Pass(es) covered | n/a |  |  |  |
| q5 | Procedures executed | screen | MCS › PRC (procedures) |  |  |
| q6 | Anomalies (count + ticket IDs) | screen | MCS › FDR › Alarm / anomaly journal |  |  |
| q7 | FDIR rules triggered | screen | MCS › FDR (FDIR page) |  |  |
| q8 | GO/NO-GO outcome | screen | MCS › bottom drawer › GO/NO-GO |  |  |
| q9 | Customer commitments (planner bookings) met / deferred | screen | Planner › Activity schedule |  |  |
| q10 | One-line summary for cohort archive | n/a |  |  |  |

### WB-C — Workbook self-check

| # | Question | Answerable? | Where | Gap | Fix |
|---|---|---|---|---|---|
| q1 | WB-5.0 orientation check (filled before Monday) | n/a |  |  |  |
| q2 | WB-5.1 seven position score cards (one per MCS console) | n/a |  |  |  |
| q3 | WB-5.3-PP pass-plan exercise output | n/a |  |  |  |
| q4 | WB-5.4-VL voice-loop drill responses | n/a |  |  |  |
| q5 | WB-5.4-N001 NOM-001 confirm-each-step (one per pass) | n/a |  |  |  |
| q6 | WB-5.4-C003 CTG-003 confirm-each-step (if invoked) | n/a |  |  |  |
| q7 | WB-5.4-N012 NOM-012 handover (one per handover) | n/a |  |  |  |
| q8 | WB-5.4-FD flight-dynamics workshop output | n/a |  |  |  |
| q9 | WB-5.4-Q quiz response sheet (graded) | n/a |  |  |  |
| q10 | WB-5.5-PB LEOP pre-pass briefing checklist (one per pass) | n/a |  |  |  |
| q11 | WB-5.5-L001 / -L006 / -L002 / -L007 / -L005 confirm-each-step (one each per pass operated) | n/a |  |  |  |
| q12 | WB-5.5-AT anomaly tickets (≥ 1 per pass operated) | n/a |  |  |  |
| q13 | WB-5.5-GO end-of-pass scorecard | n/a |  |  |  |
| q14 | WB-5.5-OBS observer worksheet (one per pass observed) | n/a |  |  |  |
| q15 | WB-5.5-HO inter-pass handover (one per position) | n/a |  |  |  |
| q16 | WB-5.5-DB debrief reflection | n/a |  |  |  |
| q17 | WB-5.6-PB pre-pass-set briefing | n/a |  |  |  |
| q18 | WB-5.6-C001 through WB-5.6-C012 confirm-each-step (one each) | n/a |  |  |  |
| q19 | WB-5.6-FPA cool-down monitor sheet | n/a |  |  |  |
| q20 | WB-5.6-FL First Light assessment | n/a |  |  |  |
| q21 | WB-5.6-MA multi-anomaly form (if applicable) | n/a |  |  |  |
| q22 | WB-5.6-GO pass-set scorecard | n/a |  |  |  |
| q23 | WB-5.6-OBS observer worksheet | n/a |  |  |  |
| q24 | WB-5.6-HO inter-pass handover | n/a |  |  |  |
| q25 | WB-5.6-DB debrief reflection | n/a |  |  |  |
| q26 | WB-5.7-SA personal self-assessment | n/a |  |  |  |
| q27 | WB-5.7-LL ≥ 3 cohort lessons-learned contributions | n/a |  |  |  |
| q28 | WB-5.7-WI what-if reflection (if a branch replay ran) | n/a |  |  |  |
| q29 | WB-5.7-FR final mission review prep (cohort copy) | n/a |  |  |  |
| q30 | WB-5.7-CE course evaluation (anonymous; in the box) | n/a |  |  |  |
| q31 | WB-A contingency confirm-each-step pages used as needed | n/a |  |  |  |
| q32 | WB-B shift log per shift | n/a |  |  |  |
| q33 | Workbook handed to instructor | n/a |  |  |  |

<!-- END AUDIT TABLE -->
