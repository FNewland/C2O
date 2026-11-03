# Screen review: information that should not be on each screen, by role

*Audit date 2026-11-03, branch `screen-review` (fresh copy of `main` at `9da3724`). The audit was read-only on the code.*

**How it was run**
- The full suite ran locally with `sim/start.sh --rf` (all profile, modern UI). SpaceCDF ran as its backend plus a production build of `design/frontend`, the same pairing as `design/Dockerfile.web`.
- Simulator state: phase 6 (NOMINAL), pass override ON, HK SIDs 1–12 enabled through MCS `/api/pus-command`, `eps/undervoltage` injected at 10 %, and one S15 dump taken.
- Captures used Playwright/Chromium at 1440×900. Every MCS page was captured for all 7 positions in EN, and for the Flight Director in FR. Every other tool page was captured in EN and FR.
- I also captured the rendered page text (`innerText`) of each screen, so findings can be grepped.

**Evidence**
- Screenshots are in `/tmp/claude-0/-home-claude/1321a170-74b6-5d07-9a93-b12889d176dd/scratchpad/screen_review_shots/`, called **`$S/`** below. File names follow `mcs_<lang>_<position>_<page>.png`.
- The text dumps are in `$S/text/` under the same names.
- The scratchpad is session-local. Copy any shot you want to keep.

**What I judged against**
- `docs/ui/C2O_UI_BRIEF.md`, in particular §1.5: "Instructor-only values never appear on operator screens", progressive disclosure, and calm when nominal.
- `docs/plan_2026-11/REDESIGN_DECISIONS.md`: the MDR naming, the hidden Instructor/SIM voice loop, and the logbook privacy rules.
- `sim/configs/eosat1/mcs/positions.yaml`: `visible_tabs`, `allowed_services`, `allowed_func_ids`.
- `sim/docs/design_2026-08/POSITION_NEEDS.md`.
- The procedure cards.
- The pictorial-displays research report (`/home/claude/reports/Pictorial mission control displays.md`): picture first, the number on demand, and no decorative or duplicate readouts.
- The SpaceCDF seat model in the redesign notes (s5: Team leader, Systems, Mission analysis & ops, Payload, Power, AOCS, Comms & OBDH, Thermal, Structures, Propulsion, Customer, Observer, Instructor).

**Severity labels**

| Label | Meaning |
|---|---|
| **leak** | Simulator truth or instructor knowledge reaches students or operators. |
| **clutter** | The information is not needed on this screen: debug or developer leftovers, duplicates, or text off the page's subject. |
| **wrong role** | A control or datum that this role cannot use or should not see. |
| **missing** | Information the role needs and does not get (secondary findings). |
| **misleading** | Not one of the four labels in the brief. I added it for contradictory or mislabelled values, because removing the duplicate usually fixes them. |

**Roles used**
- MCS positions: FD, EPS/TCS, AOCS (Flight Dynamics), TTC, PLD (payload_ops), FDIR (fdir_systems), PROP.
- *Students*: anyone on the student-visible tools (radio, delayed TM, orbit, docs, portal, planner).
- *Instructor*.
- CDF seats, named as in s5.

The instructor console is being redesigned separately. Its items are tagged **→ instructor redesign**.

---

## 0. Top 20 prioritised fixes

The list is ordered by leak first, then reach: how many roles and screens are affected.

| # | Fix | Sev | Roles | Where (evidence) |
|---|---|---|---|---|
| 1 | **Close the config viewers to operators.** MCS `/config` and planner `/config` are linked from the planner header as "Configuration". They list *and serve* every `scenarios/*.yaml`, with the failure, the onset time, the briefing and the expected responses: `GET :9090/api/config/file?path=scenarios/aocs_actuator_stuck.yaml` returns the full scenario. They also serve `fdir/fault_propagation.yaml`, `rfsim.yaml` (the channel model), `telemetry/parameters.yaml` (with 33 `visibility: instructor` parameters), `i18n/fr/db.yaml` (the translated scenario briefings) and the XTCE. **Fix:** serve `/config` only on the instructor host. Failing that, exclude `scenarios/`, `rfsim.yaml`, `fdir/`, `smdl/`, `xtce/` and the instructor-visibility rows from the ground copy. Remove the planner "Configuration" link. | leak | all students | `$S/mcs_config_en.png`, `$S/planner_config.png`; planner `static/modern/index.html:283` |
| 2 | **Radio: remove the classic page and the channel-model truth from the student feed.** The modern footer links `/classic`, which shows CHANNEL MODEL (phase noise, fading, K-factor, interferers), "GS Eb/N0 Penalty" (the instructor's injected ground degradation) and "Pipeline diagnostics" with spacecraft-side `tx_*` counters. Its footer reads "Artificial Intelligence Generated". `/api/status` carries `fading_*`, `n_interferers`, `gs_penalty_db`, `phase_noise_enabled`, `config`, `sc_tx_on`, `sc_pa_on` and `pass_override`. **Fix:** remove the footer link and serve `/classic` only to the instructor. Strip those fields from the student WS/status feed and keep them on an instructor endpoint. | leak | students (radio), TTC | `$S/radio_classic_en.png`; rfsim `static/radio.html:167-225`, `static/modern/index.html:223` |
| 3 | **Radio modern: remove "SC transmitter Radiating/Off · OVR".** The ground cannot know the spacecraft's TX state, and the tooltip itself says "tx_active from the sim". "OVR" reveals the instructor pass override. "Range 500.0 km / Prop delay 1.67 ms" are shown with no lock and no orbit source (a sim placeholder). **Fix:** replace the chip with "carrier detected / not detected". Drop OVR. Take range from the ground propagator, labelled "predicted", or show no data. | leak | students, TTC | `$S/radio_en.png`; rfsim `static/modern/index.html:443-470` |
| 4 | **MCS FDR: remove the simulator-state spacecraft mode.** "LATCHED SAFE · `derived_from_sc_mode`" comes from `/api/fdir` `sc_mode_source: sim_state`. That is simulator truth, not downlinked, and it contradicts "SC MODE NOMINAL (TM obdh.mode)" in the same strip. The sim-mode branch "SIMULATED ON-BOARD AUTONOMY — instructor truth — not downlinked" (active faults, pending cascades, on-board procedure names) is still wired at `mcs.js:4061`. **Fix:** derive the latch from TM only, and delete or instructor-gate the autonomy card and the `sim_health`/`sc_mode` fields in MCS `/api/state`. | leak | FD, FDIR | `$S/mcs_en_flight_director_fdir.png`; `mcs.js:4040-4075`, `server.py:2504-2552` |
| 5 | **PUS S3: stop presenting simulator truth as spacecraft-reported.** "Enable set reported by the spacecraft: enabled [1…12]" and the HK "DISABLED" freshness verdict come from the simulator's `hk_enabled` map (`/api/state`), not from TM. The reset reason names `simulation.yaml housekeeping.default_enabled_sids`. **Fix:** derive the enable set from the TC(3,5)/(3,6) history and HK arrival. Label it "commanded / observed", and drop the config path. | leak | FD, FDIR | `$S/mcs_en_flight_director_diag.png`; `mcs.js:440, 3436` |
| 6 | **Take fault-injection knowledge out of operator-facing text.** Examples: the parameter descriptions on the AOC page ("Compare against aocs.gyro_bias_injected (0x0296) when an instructor has injected a gyro_bias fault", "…while the injected hardware fault persists"); procedures `clock_sync.md`, `time_sync.md`, `gyro_failure.md`, `data_downlink.md`, `loss_of_communication.md`, `ttc_link_loss.md` and `first_acquisition.md` (9 cards, e.g. "500 ppm is the signature of the instructor's `clock_drift` failure injection"). These appear in MCS MAN cards, the PRC document viewer and the docs viewer. **Fix:** move the training notes to the instructor packs. Rewrite descriptions in spacecraft terms ("hardware bias", "drift well above the oscillator spec"). | leak | all positions, students | `$S/mcs_en_aocs_aocs.png` (param table); `configs/eosat1/telemetry/parameters.yaml:276-279`; `procedures/**` |
| 7 | **Docs viewer: hide developer and instructor material from students.** Today it lists "Space Mission Operations Simulator — Software Architecture" (ports, instructor routes, failure injection), "Commissioning walkthrough — development change log", both installation guides, "Startup Guide — RF and Non-RF Modes", "EOSAT-1 RF Simulation Layer" (§10 "Training Scenarios: inject burst errors…"), the seven "(aocs) -- Role Analysis" design docs and "CTG-018 … (RETIRED)". **Fix:** allow-list the manual, the procedures and the command reference, and move the rest to the instructor docs. | leak / clutter | students | `$S/docs_en.png`; `tools/doc_viewer.py:218` (only `i18n` is hidden) |
| 8 | **Remove API-path captions from the MCS.** These are on every operator page: "/api/contacts", "/api/displays/system-overview" plus "source: /api/displays/system-overview", "/api/displays/power-budget", "/api/displays/link-prediction", "/api/ground-stations", "/api/verification-log · 5 s", "S15 dump → /api/tm-dump-data" (7 pages), "AND — generated from /api/param-catalog (P10)" (7 pages) and "/api/gonogo-matrix (mcs/gonogo_matrix.yaml)". **Fix:** remove them all. Where provenance matters, write it in operator words ("ground prediction", "station measured"). | clutter | all positions | `$S/mcs_en_flight_director_ovr.png`, `…_eps.png`, `…_ttc.png`; `mcs.js:1183,1198,1394,1505,1507,1557,1578,1581,2173,2713` |
| 9 | **Remove the requirement tags and implementation notes from the MCS.** Examples: "in place · position-gated (P9)" (7 pages), "(P7.6)", "(P8)", "(P9)" in page intros, "fdir mount — one renderer" (×2), the PUS intro "same renderer FDIR mounts (one implementation, two mounts)", "verification is a stepper … not a separate log (P9)", "PL4: bit4 set…", "server predates POSITION_NEEDS G1?", the help title "Keyboard and design notes", and the chain footer "the mental model the console teaches (P9)". **Fix:** remove them. Keep teaching text only behind the teaching toggle. | clutter | all positions | `$S/mcs_en_flight_director_cmd.png`, `…_diag.png`, `…_fdir.png`; `mcs.js:1574,3934,3978,5127,5262,1840` |
| 10 | **Remove file-system and config paths from operator and student screens.** Examples: the alarm rows ("ground limit 0x0275 · mcs/limits.yaml"); "gates from display_config.yaml"; "baseline: display_config.yaml commissioning snapshot"; "ttc.yaml" in descriptions and in the HIGH-rate policy hold message; the planner's "80 % from planner.yaml"; MCS `/dumps` "store: /home/claude/…/workspace/dumps"; MCS `/reports` "Plots: matplotlib 3.11.2 (Agg backend) under /home/claude/c2o/sim/.venv/bin/python"; DTM "Store workspace/dumps"; and the raw report-template keys `anomaly_id`, `t0`, `suspect_subsystems`. **Fix:** remove them, or rename to operator vocabulary. | clutter (and a minor leak once web-hosted) | all | `$S/mcs_en_alarm_drawer.png`, `$S/mcs_dumps_en.png`, `$S/mcs_reports_en.png`, `$S/dtm_en.png` |
| 11 | **OVR "System board" is wrong and duplicated.** Its "Link Margin" row is bound to 0x0507, which is the **transponder temperature** (TTC Equipment shows "XPDR 0x0507 30.1 °C"). It reads "29.4 dB" beside the TT&C block's "margin 72.5 dB". The other four rows repeat the schematic above it. **Fix:** remove the System board card from OVR. Fix the binding in `displays/system-overview` if it is kept anywhere. | misleading / clutter | all positions | `$S/mcs_en_flight_director_ovr.png` (text dump lines 146-163) |
| 12 | **Give every link and state one source on each MCS screen.** At the same instant, the header showed "In contact · carrier ✓ bit ✓ frame ✓" and "What's next? AOS in 10:55". The TTC page showed "Link lock chain NO SIGNAL" and "predicted-now — (not in pass)", and its schematic "TM TIER … TIER CMD" text overlaps. The planner wide view said "No contact". "Is it well? NOMINAL" sits under a red contingency banner. EPS showed "86 % at eclipse exit" beside a projection reading "INVALID — not in eclipse", and "Net 0 Wh: the battery ends the orbit lower". **Fix:** one selector for link, mode and freshness (R3 #10). Remove the second copy instead of reconciling it. | misleading | all positions | `$S/mcs_en_ttc_ttc.png`, `$S/mcs_en_flight_director_eps.png`, `$S/planner_wide_en.png` |
| 13 | **Remove duplicates on EPS and OVR.** The EPS page shows SoC 5× (power flow, schematic, parameter table, Key parameters, Equipment) and bus voltage 4×, and the "Power budget" card repeats the flow diagram. OVR shows lat/lon/alt, sunlit and in-contact twice (page header and schematic chips), and its contacts table repeats the SA "What's next" and the planner. **Fix:** per page, keep the picture plus the parameter table (detail level). Drop "Key parameters", "Equipment" and "Power budget" where the schematic shows the same values, and collapse the contacts table behind "more". The same applies to AOC/TTC/OBD/PLD/PRP, which all carry schematic, Key parameters and Equipment. | clutter | all positions | `$S/mcs_en_eps_tcs_eps.png`, `$S/mcs_en_flight_director_ovr.png` |
| 14 | **Filter the CMD page to the position's authority.** For EPS/TCS, the catalogue dropdown lists ~120 commands with 🔒 (all AOCS, PROP, PAYLOAD, S2 devices and S6). The raw Service list offers 9, 11, 12, 15 and 19, which `allowed_services` refuses. `*_LEGACY` commands are listed. HK enabling appears 3× (Quick "HK REQUESTS", the "HK SID control" card, PUS S3). Command history appears 3× (the empty "Command history" card, the "Verification log" card and the drawer "Command history", which said "no commands this session" after 12 TCs). **Fix:** show only commands within authority, with a "show all (read-only)" toggle. Remove the LEGACY entries. Keep one history (the drawer) and one HK control (PUS S3, with a shortcut). | wrong role / clutter | EPS/TCS, AOCS, TTC, PLD, FDIR, PROP | `$S/mcs_en_eps_tcs_cmd.png`; `mcs.js:2760` |
| 15 | **Filter alarms and the Overview by position.** Every position sees all subsystems' alarms. The header count is "6 alarms" even for Payload, which owns none. "Acknowledge all" and the `k` key acknowledge other positions' alarms. The Overview for single-subsystem positions draws empty ghost tiles for the five other subsystems plus the full Power card. **Fix:** default the drawer filter and the count to the position's `subsystems` (FD sees all), restrict ack-all to FD, and collapse ghost tiles to a one-line "other subsystems: n alarms" strip. | wrong role / clutter | EPS/TCS, AOCS, TTC, PLD, FDIR, PROP | `$S/mcs_en_payload_ops_ovr.png`, `$S/mcs_en_alarm_drawer.png` |
| 16 | **MAN page: move the course PDFs out of the operations manual.** Each position's MAN page carries the full "Course PDFs" library: SpaceCDF textbook, workbook, peer-review pack, syllabus, simulator *and* SpaceCDF installation guides. Section titles are untranslated machine names ("02 Aocs", "07 Orbit Ops"; in FR "09 Command Reference", "12 Time And Clocks"). **Fix:** keep the manual and the procedure cards. Link to the course PDFs from the portal and docs viewer. Use the documents' real titles. | clutter | all positions | `$S/mcs_en_aocs_man.png` |
| 17 | **Portal: hide the instructor section from students.** It shows the "Instructor — Instructors only" tiles (Instructor console, Scenario generator, ADCS failure viewer) with live "Available" status and their ports, plus "localhost:NNNN" under every tile and "each screen is a separate server started by start.sh". **Fix:** render the instructor section only for an instructor identity. Drop the ports and the dev sentence. | wrong role / clutter | students | `$S/portal_en.png`; `tools/portal.py:121-136` (`instructors_only` only sets a label) |
| 18 | **MCS header clean-up.** "Greyscale" is a P6 design-acceptance check and belongs in help or dev mode. "Delayed TM" and "Reports" open the legacy, EN-only `/dumps` and `/reports` pages (absolute paths, "raw JSON"), which duplicate the :8092 viewer that the portal links. The alarm drawer's "Archive" button also opens `/dumps`, which is the wrong target. The alarm drawer's mute is a 🔔 emoji. **Fix:** move Greyscale to the `?` dialog, point Delayed TM at the :8092 viewer, merge `/dumps` into it, use the trends/alarms archive for "Archive", and use a glyph for mute. | clutter | all positions | `$S/mcs_en_flight_director_ovr.png` (header), `$S/mcs_dumps_en.png` |
| 19 | **SpaceCDF: add role views per seat (s5) and gate the team-leader actions.** Today every participant (Customer and Observer included) sees every tab and can press Run Analysis, Close study, Load, Record go / no-go and Finish MDR review, and can edit every block. **Fix:** implement the "Sees first" view per seat, read-only for Customer and Observer, with gate decisions for Team leader and Instructor only. Also remove the "React Flow" attribution text and "Configuring: Spacecraft(system, space)", replace the raw key `capacity_wh`, drop "Level 4 readiness" on V&V, and merge the Blocks and Spacecraft bottom tabs (same list). | wrong role / clutter | all CDF seats | `$S/cdf_en_level3.png`, `$S/cdf_en_tab07_Review_Gates.png`, `$S/cdf_en_bottom_Spacecraft.png` |
| 20 | **Replace raw identifiers used as labels with operator words, keeping the ids in tooltips.** Examples: Key parameters labelled `eps.bat_soc`; logbook context chips "page ovr · position flight_director"; planner "SOC_CEILING_REACHED:" (also untranslated in FR); the contingency banner and SA "(TM fdir.level 0x0700)" and "mode from TM obdh.mode 0x0300"; "derived_from_sc_mode"; "OBC − ground time offset −840499231115 ms"; Trends "eps.bat_current_A"; PRC activity types "imaging_pass", "data_dump"; DTM SID names "AOCS_DETERMINATION", "GPS_NAV"; unit "C" for °C. | clutter | all | `$S/mcs_en_logbook.png`, `$S/planner_en.png`, `$S/mcs_en_flight_director_trnd.png` |

---

## 1. Welcome portal (`sim/tools/portal.py`, :8090)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| "Instructor — Instructors only" section (3 tiles + status) | Visible and clickable for everyone. Tells students which instructor tools exist and that they are up. | students | wrong role | Render only for an instructor identity (IAP group); otherwise remove. |
| `localhost:8000` … `localhost:8097` under every tile | Port numbers are developer information; on GCP they become hostnames. | students | clutter | Remove; the tile is the link. |
| "Running on this computer: each screen is a separate server started by start.sh." | Developer explanation. | students | clutter | Remove, or show it only in local/dev mode. |
| "Status checked by the server at 17:18:33 UTC. Simulator times are simulation time." | Real UTC next to sim-time status (17:18 vs 12:0x). | students | misleading | Say "checked 5 s ago"; drop the wall-clock time. |
| "Spacecraft mode NOMINAL · TM obdh.mode, 30 s" | Mnemonic in a student-facing summary. | students | clutter | "Spacecraft mode NOMINAL (telemetry, 30 s ago)". |

Evidence: `$S/portal_en.png`, `$S/portal_fr.png`. FR is complete.

## 2. MCS ops console (`smo-mcs`, modern)

### 2.1 Header, SA strip, banners (all pages)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Contingency banner "(TM fdir.level 0x0700) … OBC mode NOMINAL" | Parameter mnemonic and hex in the alert text. It fired for FDIR level WARNING while mode NOMINAL; the SA says "Is it well? NOMINAL" right under the red banner. | all | clutter / misleading | "Contingency: on-board FDIR at WARNING". Put the id in a tooltip. Make "Is it well?" reflect the contingency. |
| SA "Can I see it?" sub-line "tier SAFE · store 1 % (HK SID 4 buffers)" | Internal source name. | all | clutter | "TM rate SAFE 1 kbps · on-board store 1 %". |
| SA "Is it well?" sub-line "mode from TM obdh.mode 0x0300" | Provenance hex on the overview level. | all | clutter | Move to tooltip. |
| SA "What's next? AOS in 10:55" while "Can I talk? In contact" | Contradiction under pass override; "next" should be LOS of the current pass. | all | misleading | Show "LOS in mm:ss" when in contact. |
| "Greyscale" toggle | Design-acceptance tool (P6 check), not an operator function. | all | clutter | Move into the `?` dialog / dev mode. |
| "Delayed TM", "Reports" buttons | Open legacy EN-only `/dumps` and `/reports` pages (§4.2), duplicating the :8092 viewer. | all | clutter | Point to the :8092 viewer; retire `/dumps`. |
| `?` help title "Keyboard shortcuts and design notes" | There are no design notes; the dialog is titled "Keyboard and design". | all | clutter | "Keyboard shortcuts". |
| Position select | Lets anyone switch to any position, including FD. The server trusts the `position` field in `/api/pus-command`. | all | wrong role | Seat binding (s5 / WP10): the server takes the position from the seat. Keep the selector only for positions the person holds. |
| "TRAINING · SIM x1" chip | Correct, but also shown on the voice panel's own position selector (see §2.6). | — | ok | — |

### 2.2 Pages

| Page | Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|---|
| OVR | Page header "Lat/Lon/Alt · ground · Sunlit · In contact" **and** schematic chips "AOCS — · Sunlit · In contact" | Same facts twice; "AOCS —" is a stray empty chip. | all | clutter | Keep the header strip; remove the chips. |
| OVR | "Click the block … Position: FLIGHT DIRECTOR" | The position is already in the header selector. | all | clutter | Drop "Position: …". |
| OVR | "Spacecraft mode EMERGENCY / SAFE / NOMINAL / SCIENCE" segmented row | Looks like a mode-command control but is a read-only indicator. | all | misleading | Render as a single status value with history, not a segmented control. |
| OVR | "Contacts, next 12 h" caption "/api/contacts" + 8-row table | API caption; table duplicates SA "What's next" and the planner. | all | clutter | Remove the caption; show the next 3 passes, the rest behind "more" or a link to the planner. |
| OVR | "System board" card + "source: /api/displays/system-overview" | Duplicates the schematic. "Link Margin 0x0507" is bound to transponder **temperature** (29.4 "dB" vs 72.5 dB in TT&C). | all | misleading / clutter | Remove the card (Top-20 #11). |
| OVR (non-FD) | Ghost tiles for the other 5 subsystems + full Power card | Payload/TTC/PROP get a mostly empty schematic. | EPS/TCS, AOCS, TTC, PLD, FDIR, PROP | clutter | Collapse other subsystems to a one-line alarm strip. Keep Power for EPS/TCS and FD. |
| OVR (PLD) | — | Needs AOCS mode / FINE readiness, next imaging opportunity and data capacity of the next pass on the first screen. These are on PLD/planner only. | PLD | missing | Add a "next capture" line to the PLD position's overview. |
| EPS | Power flow + Schematic + Parameters + Key parameters + Equipment + Power budget | SoC 5×, bus V 4×, generation/consumption 3×. | EPS/TCS, FD | clutter | Picture (flow) + table; drop Key parameters, Equipment and Power budget (Top-20 #13). |
| EPS | "Net 0 Wh: the battery ends the orbit lower" | Text contradicts the number. | EPS/TCS, FD | misleading | Pick the text from the sign, with a zero band. |
| EPS | "86 % at eclipse exit" vs Projections "SoC at eclipse exit … INVALID — not in eclipse" | Two answers to one question. | EPS/TCS, FD | misleading | One projection, one place. |
| EPS | Command card "Deploy Wing +Y/−Y" in NOMINAL phase | LEOP-only commands among routine switches. | EPS/TCS, FD | clutter | Show deployment commands only in LEOP phases, or under a "LEOP" fold. |
| EPS/all subsystem pages | Subtitle "Subsystem eps · alarms for this subsystem" | Lower-case internal id. | all | clutter | "Alarms for EPS". |
| AOC | Attitude card "Pointing error 0.09° … estimate vs commanded" while every AOCS HK value reads "no data" | Draws from a source that is not the downlinked HK. Check whether it is the sim state or the ground propagator; label the source or show no data. | AOCS, FD | misleading (possible leak) | Bind to TM 0x0217 only; otherwise "no data". |
| AOC | Parameter descriptions naming `aocs.gyro_bias_injected`, "instructor has injected", "injected hardware fault" | Instructor knowledge (Top-20 #6). | AOCS, FD | leak | Reword in `parameters.yaml`. |
| AOC/PLD | "FINE-entry readiness aocs.fine_ready 0x02C5 decoded … aocs.fine_ready = 0x0027" | Raw value before the decoded bits. | AOCS, PLD, FD | clutter | Show the decoded blocking list; raw hex in tooltip. |
| AOC | "GPS navigation (PVT)" with 9 zero rows when there is no fix | Nine zeros carry no information. | AOCS | clutter | Collapse to "no 3D fix" until a fix exists. |
| TTC | Schematic "TM TIER SAFE 1 kbps (0)" overlapping "TIER CMD 0" | Text collision. | TTC, FD | clutter | Layout fix. |
| TTC | "Link lock chain NO SIGNAL" vs header "carrier ✓ bit ✓ frame ✓" | Contradiction (Top-20 #12). | TTC, FD | misleading | One source. |
| TTC | "Predicted vs measured link … /api/displays/link-prediction · predicted-now — (not in pass)" | API caption; "not in pass" while in contact. | TTC | clutter / misleading | Remove the caption; predict for the current pass. |
| TTC | "Ground station network /api/ground-stations — station list unavailable (/api/ground-stations)" | Error text with API path; TTC needs the station list. | TTC | missing / clutter | Fix the feed; plain-language empty state. |
| TTC | Key parameter "ttc.pa_temp 33.3 C", "1000 bps L below the caution limit" in SAFE tier | Mnemonic labels, unit C. SAFE tier at 1 kbps raises a caution in a nominal state. | TTC | clutter | Human labels; review the 0x0506 limit. |
| PLD | "Capture readiness (NOM-002) — gates from display_config.yaml", "PL4: bit4 set means a desat is coming" | Config filename, internal tag. | PLD, FD | clutter | Remove. |
| OBD | Projection "OBC − ground time offset −840499231115 ms" | Unreadable value (≈ 26 years, unsynced clock). | FDIR, FD | clutter | "OBC clock not set (never synced)", as the instructor page already words it. |
| PRP | "ARM INHIBIT 0x0B15 1033" | Raw bitmask as a decimal. | PROP, AOCS, FD | clutter | Decode the inhibit bits as on FINE readiness. |
| FDR | "LATCHED SAFE derived_from_sc_mode" | Simulator truth + internal id (Top-20 #4). | FD, FDIR | leak | TM-only. |
| FDR | "fdir mount — one renderer" (×2) | Implementation note. | FD, FDIR | clutter | Remove. |
| FDR | S12 table "En/State/Value" for 41 monitors while `s12_reported: false` | Shows the ground config with live values as if it were the on-board monitor state. | FD, FDIR | misleading | Mark "configured (not yet reported by S12)" until TM(12,13)/(12,9) is received. |
| FDR | S19 rows such as "eps_bus_undervoltage_payload_off · BATTERY_SOC_CRITICAL → 10 - AOCS_SLEW_TO" | Rule name and action disagree (data issue). Snake-case ids as names. | FD, FDIR | misleading | Check `s19_rules.yaml` vs the function-id map; show the human name. |
| FDR | Recovery buttons (ENABLE/DISABLE MONITORING, ADD (12,6), ADD RULE (19,1)) duplicated on PUS | Same tables and buttons on FDR and PUS ("two mounts"). | FD, FDIR | clutter | FDR = state + recovery; PUS = configuration. Do not mount the S12/S19 editors twice. |
| CMD | Catalogue dropdown with ~120 🔒 entries, raw services outside `allowed_services`, `*_LEGACY` entries | Top-20 #14. | all but FD | wrong role / clutter | Filter to authority. |
| CMD | "Command history" card (empty) + "Verification log /api/verification-log · 5 s" + drawer "Command history" | Three histories, one of them with an API caption, one empty after 12 TCs. | all | clutter / misleading | One history in the drawer. |
| CMD | "HK REQUESTS (S3.27)" quick group + "HK SID control (S3)" card + PUS S3 | HK control 3×. | all | clutter | Keep PUS S3 and one quick group. |
| CMD | "raw command — no catalogue entry; length not validated" visible to every position | Raw TC building is an FD/FDIR expert function. | EPS/TCS, AOCS, TTC, PLD, PROP | wrong role | Hide raw mode except for FD/FDIR (or teaching mode). |
| PRC | "Reachable from any alarm row (P7.6)"; procedure list with ids "imaging_pass", "data_dump", … | Requirement tag; internal ids. | all | clutter | Remove the tag; show the procedure title and number (NOM-002…). |
| PRC | START/PAUSE/RESUME/STEP/SKIP/ABORT enabled with nothing loaded (R3 #12, still present) | — | all | misleading | State-machine enablement. |
| PRC | "Manual override — arbitrary TC during a run" | Raw TC entry available to every position. | all but FD/FDIR | wrong role | Same rule as CMD raw mode. |
| TRD | "(P8)"; parameter list "eps.bat_current_A"…; "baseline: display_config.yaml commissioning snapshot · drift … per NOM-011" | Tag, ids, config filename. | all | clutter | Human names; "baseline: commissioning". |
| PUS | Intro "All seven service panels from the classic PUS SERVICES tab … one implementation, two mounts" | Developer history. | FD, FDIR | clutter | One-line purpose. |
| PUS | "Enable set reported by the spacecraft" + `simulation.yaml housekeeping.default_enabled_sids` | Simulator truth and config path (Top-20 #5). | FD, FDIR | leak | TC/HK-derived. |
| MAN | Course PDFs, installation guides, "02 Aocs" | Top-20 #16. | all | clutter | Move. |
| MAN | Card list "LEOP-007 — Sequential Power-On 2 steps yours leop · 17 steps" | Phase tags in lower case and "yours" read as debug. | all | clutter | "LEOP · 17 steps · 2 for you". |

### 2.3 Bottom drawers

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Event severity filter (All/Info/Nominal/…) on every drawer tab | Applies to Events only. | all | clutter | Show it on the Events tab only. |
| Events tab empty while a contingency banner and 6 alarms are active | The operator needs the S5 events that triggered FDIR WARNING. | all | missing | Check the S5 path into the drawer. |
| TM packets "TM(3,25) SID 1" stream | Raw packet log as a peer of Events/Handover. | all but FD/FDIR | clutter | Detail level: move to PUS or keep only for FDIR/FD. |
| Command history "no commands this session" after 12 TCs (sent as flight_director) | Disagrees with the console Log, which lists the 12 S1 verdicts. | all | misleading | One store. |
| Log tab "[TC] AUTO TC seq 12 S1 verdict: COMPLETED (seq:12)" | Seq repeated; S1 verdict auto entries flood the decision log. | all | clutter | Collapse auto TC entries; keep marks, notes, acks and GO/NO-GO. |
| GO/NO-GO "Start poll" | Shown enabled to every position. The server accepts FD only, but the client (`mcs.js:4953`) sends no `position`, so the request is refused for everyone, FD included (`POST /api/go-nogo/poll` with no position → 403 "Only Flight Director can initiate polls"). | all; FD (missing) | wrong role / missing | Show Start poll to FD only and send the position. Response buttons stay for everyone. |

### 2.4 Alarm drawer

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Row meta "· ground limit 0x0275 · mcs/limits.yaml" | Config filename on every row. | all | clutter | "ground limit (hard)"; id in tooltip. |
| "Acknowledge all", `k` key | Any position acknowledges any subsystem's alarms. | all but FD | wrong role | Ack-all FD only; others ack their own subsystems. |
| Default filter "All subsystems" | Non-FD positions see the whole flood (Top-20 #15). | all but FD | wrong role | Default to the position's subsystems. |
| "Archive" → `/dumps` | Wrong target (delayed-TM files, not the alarm archive). | all | misleading | Link to TRD "Alarms in window". |
| 🔔 mute, ⛓ chain | Emoji (brief §2). | all | clutter | Glyphs from `glyphs.svg`. |
| Causal chain dialog "edges are inferred … from fdir/fault_propagation.yaml", "(P9)" | Config filename; tag. `fault_propagation.yaml` is the simulator's fault model, so naming it hints at the truth model. | all | clutter (borderline leak) | "Inferred from the FDIR fault tree". |

### 2.5 Logbook (shared `logbook.js`, every tool)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Context chips "page ovr", "position flight_director" | Internal ids in a participant-facing record. | all | clutter | "Overview", "Flight Director". |
| "Private to you · nothing is stored on the server yet. Entries are kept 48 h after your last one." | The two sentences contradict each other (local vs 48 h server retention, L2). | all | misleading | One sentence matching the actual storage. |

### 2.6 Voice

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Panel "Position" selector | Duplicates the header position selector it follows. | all | clutter | Show the position as text; switch it in the header. |
| `/api/voice/config` `position_labels` carries `en` only | Position names untranslated in FR. | FR users | clutter (i18n) | Add `fr` from `positions.yaml` / `voice_loops.yaml`. |
| Instructor/SIM loop | Correctly hidden (`role_positions` only with the instructor role). | — | ok | — |

### 2.7 French

Untranslated strings in FR (Flight Director captures, `$S/mcs_fr_*`):
- the "(P10)" and "/api/…" captions;
- "REPORT MONITORS (12,12)", "ENABLE/DISABLE MONITORING", "REFRESH (19,8)", "ADD (12,6)", "ADD RULE (19,1)";
- the projection reasons ("not in eclipse — nothing to project", "no downlink backlog telemetry received …");
- the FINE-readiness bit labels ("b5 propagate-only", "b6 slew not idle 60s");
- the HK reset reason;
- the manual section titles ("09 Command Reference", "12 Time And Clocks");
- all parameter descriptions (second line in the table);
- "HK SID 4 buffers".

## 3. Planner (`smo-planner`, :9091 and `/wide`)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Header "Configuration" link | Opens the config viewer that serves scenario files (Top-20 #1). | students | leak | Remove. |
| "Upload next activity" / "On board (S11)" | Any participant can upload the schedule; the planner has no position concept. | all but FD | wrong role | Upload: FD only (or the planner seat); others validate and propose. |
| Next pass shown 4× (Next contact card, ground-track "Next AOS", Next pass polar card, Next contacts table) | Duplication. | all | clutter | Polar card + table; drop the other two. |
| SoC shown 3× (header card, Power budget, SoC per pass); "Initial SoC 80.0 %" vs live 89 % | The budget starts from `planner.yaml` 80 %, not from TM. | FD, EPS/TCS | misleading | Default the assumed SoC to the last TM value, labelled. |
| "Blank uses the planner's configured default (80 % from planner.yaml)" | Config filename. | all | clutter | "Blank = last telemetry value". |
| "SoC saturated against a battery rail (0 at 0 %, 38 at 100 %)…" + "SOC_CEILING_REACHED: the battery reached 100 % …" | The same warning twice, one with a raw code, EN-only in FR. | all | clutter / i18n | One sentence, translated. |
| "Eccentricity not served" | Developer wording. | all | clutter | "—" with tooltip, or hide. |
| `/wide` "API connected", "Last pass not configured" | Dev status on the wall display. | wall | clutter | Remove; show the feed age only when stale. |
| `/wide` "No contact" while the MCS shows "In contact" (pass override) | The planner uses geometry and the MCS the override. On the wall display the contradiction is public. | all | misleading | Follow the MCS link state; show "override" only to the instructor. |

Evidence: `$S/planner_en.png`, `$S/planner_wide_en.png`, `$S/planner_fr.png`, `$S/planner_config.png`.

## 4. Delayed TM

### 4.1 Viewer (`tools/delayed_tm_viewer.py`, :8092)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Header "Store workspace/dumps", "1 in workspace/dumps" | Server path. | students | clutter | "Dump archive". |
| Empty state "Run a pass with an S15 dump in the simulator." | Points students at the simulator; the MCS `/dumps` says "Command an S15 dump (TM_DUMP) from the MCS". | students | clutter | "Request an S15 dump from mission control during a pass". |
| SID labels "AOCS_DETERMINATION", "GPS_NAV", "Beacon" vs "EPS Power Management" | Mixed raw ids and names. | students | clutter | Names from `hk_structures.yaml` display names. |
| Timeline date "2000-01-01 · on-board time" | Correct (OBC never synced) but unexplained. | students | missing | Add "OBC clock not synchronised". |
| Parameter table by mnemonic only | No human name column. | students | clutter | Add the name; mnemonic in mono as a secondary column. |

### 4.2 MCS `/dumps` and `/reports` (legacy pages)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Whole `/dumps` page | Duplicates :8092. EN-only (`?lang=fr` ignored). Shows "store: /home/claude/…/dumps" and a "raw JSON" link. | all | clutter / leak (path) | Retire; redirect to :8092. |
| `/reports` "Plots: matplotlib 3.11.2 (Agg backend) under /home/claude/c2o/sim/.venv/bin/python" | Developer diagnostics with a server path. | all | clutter / leak (path) | Remove. |
| `/reports` template fields `anomaly_id`, `title`, `t0`, `suspect_subsystems` | Raw keys as form labels; EN-only. | all | clutter | Labelled form, translated; move into the :8092 "Generate report…". |

Evidence: `$S/dtm_loaded_en.png`, `$S/mcs_dumps_en.png`, `$S/mcs_reports_en.png`, `$S/mcs_dumps_fr.png`.

## 5. Orbit tools (`tools/orbit_tools.py`, :8093)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| "Epoch 2026-11-03T17:18:00Z" and the pass list | Uses wall-clock time, while the MCS and planner run on sim time (2026-08-20 12:xx). Passes and "Next AOS Troll" differ from those on mission control. | students, AOCS | misleading | Follow `SMO_TIME_SOURCE` (sim time), as the planner does. |
| "75 days from the TLE epoch: accuracy degrades" | A consequence of the same wall-clock use. | students | misleading | Disappears with the sim clock. |
| 47-row "Passes next 24 h" table | Long flat list; the student task is the orbit-update TCs. | students | clutter | Show the next 5, the rest behind "more". |

Evidence: `$S/orbit_en.png`, `$S/orbit_fr.png`.

## 6. Radio view (`smo-rfsim`, :8094)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| "SC transmitter Off/Radiating · OVR" chip | Spacecraft truth plus instructor override (Top-20 #3). | students, TTC | leak | Carrier-detect chip; no OVR. |
| "Range 500.0 km", "Prop delay 1.67 ms" without lock | Constant placeholder from the sim. | students | leak / misleading | Ground prediction or no data. |
| "Receiver diagnostics" (details) | Dumps `diagnostics` keys verbatim, including spacecraft-side `tx_frames_transmitted`, `tx_packet_drops`, `tx_buffer_overflows`, and internals `rx_mod_searches`, `rx_pll_resets`. | students | leak / clutter | Keep the rx-side counters with names. Move tx-side counters to the instructor. |
| Footer "SMO Ground Segment — radio receiver console · classic page" | The link opens the channel-model page (Top-20 #2). | students | leak | Remove the link. |
| Header "Feed live 17:19:03 UTC" | Wall-clock time beside sim-time consoles. | students | misleading | Sim time, or "updated n s ago". |
| `/classic` page | "Channel model", "GS Eb/N0 Penalty", "Pipeline diagnostics", "Artificial Intelligence Generated" footer; EN-only. | students | leak | Instructor-only or retire. |
| `/api/config` (rfsim) | Serves the channel configuration. | students | leak | Instructor-only. |

Evidence: `$S/radio_en.png`, `$S/radio_fr.png`, `$S/radio_classic_en.png`.

## 7. Docs viewer (`tools/doc_viewer.py`, :8095)

| Element | What's wrong | Roles | Sev | Change |
|---|---|---|---|---|
| Manual list: software architecture, development change log, installation guides ×2, startup guide, RF Simulation Layer | Developer and instructor documents (Top-20 #7). | students | leak / clutter | Allow-list. |
| "MCS" category: "Flight Dynamics (aocs) -- Role Analysis" … | Design-analysis documents with internal ids in titles. | students | clutter | Move to `docs/`; not served. |
| "CTG-018: Boot Loader Recovery (RETIRED)" | Retired card listed among live ones. | students | clutter | Hide retired cards. |
| Procedure training notes about injections (9 cards) | Top-20 #6. | students | leak | Move to instructor packs. |
| `manual/*.pdf` beside `.md` (installation_guide.pdf, software_architecture.pdf) | Duplicates of hidden documents. | students | clutter | Same allow-list. |

Evidence: `$S/docs_en.png`, `$S/docs_fr.png`.

## 8. Instructor console (`smo-simulator` instructor, modern, :8080): **→ instructor redesign**

| Element | What's wrong | Sev | Change |
|---|---|---|---|
| "Course PDFs — students see only theirs" (19 documents, ~40 rows) in the console column | Library inside the run-time console. | clutter → instructor redesign | Move to the portal/docs (instructor view); keep a link. |
| Truth dashboard TT&C "Link Down · Range 500.0 km · Elevation 45.0°" while pass override is ON and operators are "In contact" | Placeholders, and the instructor cannot see why operators have a link. | misleading → instructor redesign | Show "Override ON" in TT&C truth; real range and elevation or "no geometry". |
| "Spacecraft mode SAFE" (truth) vs operators' TM "NOMINAL" | Model inconsistency (`sc_mode` 0 vs `obdh.mode` NOMINAL). The instructor cannot tell which is right. | misleading → instructor redesign | Show both, labelled "engine" vs "downlinked", and fix the model. |
| Scenario list names: "Debris Impact — HERMES-3 SA-2B (corrected)", "Scenario 2 — CERISE ADCS Gain Fault"; difficulty BASIC vs BEGINNER | Editing leftovers; two difficulty vocabularies. | clutter → instructor redesign | Clean the names; one scale (BASIC/INTERMEDIATE/ADVANCED/EXPERT, as the generator uses). |
| Deep-dive tabs "0x00xx 1", "0x09xx 4", "0x0Axx 7", "AOCS·raw" … | Developer buckets. | clutter → instructor redesign | Group under subsystem names; raw buckets in a "raw" sub-tab. |
| OBC truth "True offset −840499199.994 s" | Long number with no unit scale (the "about 9728 days" line beside it is better). | clutter → instructor redesign | Lead with days. |
| Speed buttons 0.5×…60× | Fine (R3 noted that 60× was missing; it is now present). | ok | — |
| Event log "--:--:--" stamps for system lines | Missing time. | missing → instructor redesign | Stamp with wall or sim time. |
| `/config` editor and `/reports` | Same legacy look and absolute paths as §4.2 ("instructor — /home/claude/…/configs/eosat1 · history: git"). | clutter → instructor redesign | — |

Evidence: `$S/instructor_en.png`, `$S/instructor_fr.png`, `$S/sim_config.png`, `$S/sim_reports.png`.

## 9. Scenario generator (`tools/scenario_generator.py`, :8096): instructor-only

| Element | What's wrong | Sev | Change |
|---|---|---|---|
| "Writes the scenario YAML to configs/eosat1/scenarios/" | Path. | clutter | "Saves to the scenario library". |
| "Briefing (shown to operators before start)" | No operator screen shows briefings (only the instructor console does), and every shipped briefing describes the failure, its time and its fix. If a briefing ever reached operators it would be a leak. | misleading | Rename "Instructor briefing (not shown to operators)", and add a separate "Operator briefing (no failure names)" field if one is wanted. |
| Difficulty "EXPERT" | Not used by any shipped scenario; the console list uses BEGINNER too. | clutter | One scale (see §8). |

Evidence: `$S/scengen_en.png`, `$S/scengen_fr.png`. FR is mostly complete, but the difficulty values stay EN.

## 10. ADCS failure viewer (`tools/adcs_sim_viewer.py`, :8097): instructor-only

| Element | What's wrong | Sev | Change |
|---|---|---|---|
| "Physics: ADCS_failure_sim/cubesat_adcs_sim.py" | Source path as a subtitle. | clutter | Remove. |
| "Orbit 550 km · 97.4°" | Not EOSAT-1's orbit (≈ 500 km), so the results do not transfer to the class spacecraft. | missing | Load EOSAT-1 orbit/inertia by default, or label it as a generic CubeSat. |
| "Debris Strike / Corrupted Axis / Gain Corruption Factor" fixed to the HERMES/CERISE case | Fine for the instructor; no change needed for students, who never see it. | ok | — |

Evidence: `$S/adcs_en.png`.

## 11. SpaceCDF (`design/`, :8000, production build)

Seats are not implemented yet. Every participant joins by name only, so every seat sees and can use everything. Rows below give the s5 seat each element belongs to.

| Element | What's wrong | Seats affected | Sev | Change |
|---|---|---|---|---|
| Run Analysis, Save, Load, Export, Close study (header) | "Close study" and "Load" (replacing the study) are available to everyone. | Customer, Observer, all discipline seats | wrong role | Close/Load: Team leader + Instructor. Run: everyone except Observer. |
| Review Gates: "Record go / no-go", "Finish MDR review" | Gate decisions are open to all. | all but Team leader / Instructor | wrong role | Team leader + Instructor only; others see status. |
| Block edit "×" (delete), "In scope", "Frozen", "+ Add Element" | Customer and Observer can delete or freeze any element; ownership (decision #5, warn then owner review) is not visible. | Customer, Observer, non-owning seats | wrong role / missing | Read-only for Observer/Customer; owner badge and the pending-change flow for others. |
| No "Sees first" view per seat | Power has no power-by-mode first, AOCS no pointing budget first, etc. The example spacecraft has no AOCS, Thermal or Propulsion element, so those seats have nothing to own. | AOCS, Thermal, Propulsion, Power | missing | Implement the s5 views; add AOCS/TCS elements to the examples. |
| "React Flow" text bottom-right | Library attribution in the work area. | all | clutter | `proOptions={{ hideAttribution: true }}`, or a credits page. |
| "Configuring: Spacecraft(system, space)" | Internal kind tags. | all | clutter | "Configuring: Spacecraft". |
| Analyses "needs: … battery capacity_wh …" | Raw key (EN and FR). | all | clutter | "battery capacity (Wh)". |
| "Design loop · stale · last run just now · converged yes" | "stale" right after a run. | all | misleading | Fix the dirty flag after a run. |
| V&V header "Level 4 readiness 2/4" | V&V is not level 4. | all | misleading | "V&V readiness". |
| Bottom tabs "Blocks" and "Spacecraft" | Same element list twice (plus orbit presets in Spacecraft). | all | clutter | Merge; keep orbit presets under Mission analysis. |
| Budget "Structure 0.42 kg … Spacecraft 3.63 kg" vs Blocks "Structure 1.0 kg", block sum 4.8 kg | Two masses for one element with no label saying which is entered and which is analysed. | Systems, Structures, Team leader | misleading | Show "entered" vs "computed" in one table. |
| Header wraps to two lines at 1440 px (level tabs + session + option + branch + logbook + lang + theme) | Header crowding; "branch" is a bare link. | all | clutter | Move session/option/branch into one "Study" menu. |
| Gate profile list shows "NASA vocabulary (MCR → SRR → MDR/SDR → PDR)" | Correct per decision #3 (MCR only in the NASA skin). | — | ok | — |
| FR: example data "POWER", "PAYLOAD", "On-Board Computer", "Multispectral Imager"; "1.0 kg" with a decimal point | Untranslated example content; number format. | FR users | clutter (i18n) | Translate the example missions; use the French decimal comma. |
| Example "SuperDove-X" | Name borrowed from a commercial product line. | all | clutter | Rename the example. |

Evidence: `$S/cdf_en_level3.png`, `$S/cdf_wb_en.png`, `$S/cdf_en_tab07_Review_Gates.png`, `$S/cdf_en_bottom_Analyses.png`, `$S/cdf_en_bottom_Budget.png`, `$S/cdf_en_bottom_Spacecraft.png`, `$S/cdf_fr_level3.png`.

---

## 12. Notes for the fixer

- **Leak surfaces outside the pages.** Several leaks live in feeds, not pages: MCS `/api/state` (`sim_health`, `sc_mode`, `hk_enabled`), `/api/fdir` (`sc_mode_source: sim_state`), rfsim `/api/status` and `/api/config`, and `confedit` `/api/config/file`. Removing a caption is not enough; the field has to leave the student-facing feed. Add a test that the operator feeds carry no key from a deny-list (`sim_health`, `pass_override`, `fading_*`, `gs_penalty_db`, `n_interferers`, `sc_tx_on`, any `visibility: instructor` id).
- **Ground deployment.** Check whether the ground image (`docker/compose.yaml`, `--profile ground`) ships `configs/eosat1/scenarios/` to the MCS and planner containers. `smo-link/httpproxy.py:45` already keeps `/config` off the GSG proxy, but the MCS and planner serve their own `/config`.
- **Already fine.**
  - The parameter catalog filters the `visibility: instructor` rows (0x0296 is not in MCS `/api/state` or the catalog).
  - The Instructor/SIM voice loop is hidden.
  - Scenario briefings do not reach the MCS.
  - The session label has an explicit "do not name the failure" guard.
  - Disallowed quick commands are rendered disabled with a reason.
- **Environment.** The run needed a symlink `sim/.venv → /home/claude/c2o/sim/.venv` and `design/frontend/node_modules → /home/claude/c2o/design/frontend/node_modules`. Both are untracked in this worktree and are not committed. The SpaceCDF database and the build went to the scratchpad. One S15 dump file was written to `sim/workspace/dumps/` (git-ignored).
