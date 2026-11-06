# Course videos: decisions, pipeline, backlog (2026-11-05)

Research: project doc `research/Free H5P and animation tools.md`. Code: `video/` (see `video/README.md`).

## Franz's rulings (2026-11-05)

| # | Question | Ruling | What it means |
|---|---|---|---|
| 1 | H5P at uOttawa | uOttawa licenses H5P in Brightspace | The `.h5p` per language is the Brightspace deliverable; upload as is. |
| 2 | Hosting | In the tool itself | The welcome page serves `/videos` (library), `/videos/<id>` (H5P player, answers go to the logbook) and `/media/videos/…`. `c2o videos push` ships the published folder to the ground VM. The `.h5p` also carries its own MP4, so Brightspace does not depend on c2o.live being up. |
| 3 | Licence | CC0 for the videos, MIT for the code | Every input has to allow it. Kokoro weights are Apache-2.0, and the fonts (IBM Plex, OFL) are rendered, not redistributed. Natural Earth is public domain. The H5P libraries are MIT. Excluded: XTTS-v2 (non-commercial), edge-tts (service terms), Remotion (company licence), and screens carrying third-party logos. |
| 4 | French | European French | Kokoro `ff_siwis`. Piper `fr_FR` voices are an alternative (check each model card). |
| 5 | French review | Franz first, then a francophone student testing the platform | Review page with a note per step and language. `SMO_VIDEO_REVIEWERS` lets a non-instructor review. `python -m c2ovideo check` runs speech recognition and lists the worst sentences first. |
| 6 | Scripted generation | Yes, all of it | Storyboard → narration (per sentence, cached) → capture (Playwright + DevTools screencast at 1920×1080, drawn cursor, cue log) → MP4 + VTT + chapters + transcript + poster → H5P (questions from the storyboard, tied to worksheet ids) → review data → publish. |

## How a video ties to the workbook

* `ties.worksheets` / `ties.decisions` appear in three places: the closing card ("Now, in your workbook"), the library, and the player side panel.
* Each embedded question has a `worksheet:` id. When a student answers in the in-tool player, the logbook gets a `worksheet` entry with that id and the `video` context. Brightspace keeps the score itself.
* A `reflect` question is free text. The student copies it into the workbook part named in the question.
* WB-5.4-Q (the graded gate quiz) cannot be tied to a video, and the code enforces this.

## What exists (2026-11-05)

| Id | Week | Tool | Ties | Status |
|---|---|---|---|---|
| V-SCDF-01 | 2 | SpaceCDF wizard → decision records | LW-1.4 A/B/C/E, D-1.4-PROBLEM, D-1.4-SPACE | rendered EN+FR, published locally; French narration check mean 0.88 (EN 0.96) |
| V-OPS-01 | 2 | MCS NOM-001 card as workbook | WB-5.4-N001 q1/q2/q8 | rendered EN+FR (fast-forward to a real pass, battery set below the Step 2 check) |
| V-OPS-02 | 4 | LEOP-001 by hand: blind uplink, bootloader, boot, HK on | WB-5.5-L001 q2/q5/q9 | rendered EN+FR from breakpoint `card-LEOP-001` |
| V-OPS-03 | 5 | Alarm → ACK → anomaly ticket → the call | WB-5.5-AT q4/q10/q12 | rendered EN+FR from `card-END`; star-tracker failure (not a scored-run fault), no recovery shown |
| V-PLN-01 | 3 | Planner: 24 h view, next contact, ground track and beta, imaging activity, constraint check | WB-5.3-PP q1/q3/q7 | rendered EN+FR (fresh simulator: same passes in both takes) |
| V-SCDF-02 | 5 | SpaceCDF mass and power budgets, margins, allocations, power by mode, energy per orbit | LW-2.4 A/B/E, D-2.4-MASS, D-2.4-POWER | rendered EN+FR on an EOSAT-1-like study seeded through the API |
| V-OPS-04 | 5 | LEOP-001 Step 5a (LOW refused, beacon mode off, LOW) and LEOP-002 health check | WB-5.5-L002 q1/q2 | rendered EN+FR from `card-LEOP-001`, Steps 2–5 sent through the MCS API in setup |
| V-OPS-05 | 5 | LEOP-004: wings deployed, read on the EPS power flow and the orbit-average margin | card LEOP-004 | rendered EN+FR from `card-LEOP-004` |
| V-OPS-06 | 5 | LEOP-007: AOCS line, SID 2, magnetometer and magnetorquers before DETUMBLE | WB-5.5-L007 q3/q4/q5 | rendered EN+FR from `card-LEOP-007` |
| V-OPS-07 | 5 | LEOP-005: starting rates, the automatic COARSE_SUN handover live, sun hold, power | WB-5.5-L005 q1/q3/q4 | dry-run only: held until COARSE_SUN holds the Sun ([AOCS_COARSE_SUN_MTQ_ONLY.md](AOCS_COARSE_SUN_MTQ_ONLY.md)) |
| V-OPS-08 | 5 | LEOP-006: unset clock, offset with light time, set from the ground, residual | WB-5.5-L006 q2/q3/q5 | rendered EN+FR from `card-LEOP-006` |
| V-OPS-09 | 5 | LEOP-003: GPS fix, altitude check band, comparison, end of LEOP | WB-5.5-L003 q1/q2/q7 | dry-run only: held for the same reason (0x0217 ~60° HH alarm on screen) |
| V-CON-06 | 4 | Concept: a telecommand's life — acceptance checks, S1 1,1/1,2/1,3/1,7/1,8, failure notice, deferred completion, completed ≠ verified | — (team) | rendered EN+FR (animated page `video/explainers/tc-life.html`); check EN 0.92, FR 0.85 |
| V-CON-05 | 4 | Concept: CCSDS packet, primary and PUS headers, APID 0x002 → 0x001, services, HK SIDs, requested vs enabled, powered ≠ reporting | — (team) | rendered EN+FR (`packets.html`) |
| V-CON-04 | 7 | Concept: FDIR hierarchy, then S12 → S5 → S19 rule 2001 → S8 desaturation → S1 → TM(12,10) | — (team, deeper for fdir_systems) | rendered EN+FR (`fdir.html`); nominal momentum chain, no scored recovery |
| V-CON-02 | 6 | Concept: energy balance through one orbit — eclipse, generation, load, SoC, orbit-average margin, the eclipse trap | card LEOP-004 (team) | rendered EN+FR (`energy.html`, one orbit from the production EPS model: `explainers/data/gen_energy_orbit.py`) |

Card-start breakpoints: `sim/tools/card_breakpoints.py` flies the acceptance LEOP + commissioning
sequence and saves `card-LEOP-001` … `card-COM-013`, `card-END` into `workspace/breakpoints`
(loaded by the simulator at start-up; `python -m c2ovideo stack up sim` makes them when missing).
Ops storyboards set `fresh_stack: sim`: the simulator and MCS restart before each take.

Fixed while filming (LEOP-004 to LEOP-003): the MCS command builder could not send S2, S13 or
S18 catalogue commands (sent as TC(0,1)); the S9 clock offset grew with the age of the last
OBDH sample. Found and not fixed: COARSE_SUN on magnetorquers alone does not hold the Sun.

Fixed while filming: the MCS event list printed `TC(undefined,undefined)` for every S1
report (it now names the command); the SpaceCDF French allocate button said "les 1
éléments"; the MCS PRC page lost the chosen card when its list was rebuilt; alarm ›
Ticket opened an empty Workbook tab when the logbook had never been opened; the procedure-card
parser read `simulation.yaml` as a parameter.

Concept explainers (2026-11-06): `video/explainers/` holds small bilingual SVG pages
(`explainer.js`, `explainer.css`); `python -m c2ovideo stack up viz` serves them on :18801 and
a storyboard step runs `js: "EX.play('scene', ${say})"`, where `${say}` is that step's
narration length, so each scene is paced to its own narration. Same pipeline, captions, H5P.

**COM card videos are held (2026-11-06).** At `card-COM-002` (COARSE_SUN) the attitude
error hunts with a red alarm on screen, as in LEOP-005. At `card-COM-007` (wheels, NOMINAL)
the error starts at ~25° after the breakpoint loads and then oscillates between 0.3° and
2.5°: `aocs.att_error` red alarms (> 2°) come and go, so every COM video would show an
unexplained AOCS alarm. Also found on COM-002: Step 6 reads 0x0410 / 0x0411 as "battery
heater ON / OFF thresholds", but those ids are `tcs.htr_duty_thruster` and
`tcs.htr_total_power`; and at the breakpoint `tcs.temp_fpa` reads 6.5 °C against the
Step 1 expectation of +8 to +14 °C.

## Backlog (from the research shortlist)

1. Link budget term by term: no screen shows it yet. SpaceCDF's `LinkBudgetTool.tsx` (a
   term-by-term cascade) is not mounted anywhere; the design loop shows only the margins.
   Mount it (Analyses or level 3), then film it (LW-3.3 B, D-3.3-LINK).
2. CTG-001 under-voltage load shed: waiting for a ruling on whether the under-voltage
   scenarios are scored; the video would show a recovery.
3. The COM cards (same breakpoint pattern, `card-COM-001` … `card-COM-013`).

Enablers built (2026-11-05): the instructor `step` command (+10 s button; API up to 1 h) and
the missing ops sheets in the logbook (WB-5.4-VL, WB-5.7-SA, -LL, -WI, -FR, WB-B, WB-C).
WB-5.4-Q (graded) and WB-5.7-CE (anonymous) stay out of the logbook on purpose.

French narration check (2026-11-05): a lone "É" is read "É accent aigu" and "E." is dropped,
so EOSAT-1 is now "Euh-o-satte un", SpaceCDF "Spèïsse C D F", and French acronyms are spelled
without full stops. Every French take was re-rendered.
