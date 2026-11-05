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

Card-start breakpoints: `sim/tools/card_breakpoints.py` flies the acceptance LEOP + commissioning
sequence and saves `card-LEOP-001` … `card-COM-013`, `card-END` into `workspace/breakpoints`
(loaded by the simulator at start-up; `python -m c2ovideo stack up sim` makes them when missing).
Ops storyboards set `fresh_stack: sim`: the simulator and MCS restart before each take.

Fixed while filming: the MCS PRC page lost the chosen card when its list was rebuilt; alarm ›
Ticket opened an empty Workbook tab when the logbook had never been opened; the procedure-card
parser read `simulation.yaml` as a parameter.

## Backlog (from the research shortlist)

1. LEOP-001 Step 5a and LEOP-002 (same breakpoint pattern).
2. Ground track, eclipse and beta angle (planner + `groundtrack.js`).
3. Energy balance through an orbit (`powerflow.js` with simulator telemetry).
4. Planner pass plan (WB-5.3-PP).
5. Link budget term by term (`link_budget_ladder.py`).
6. CTG-001 under-voltage load shed (instructor inject).
7. Instructor console for TAs (`audience: instructors`).

Enablers still to build:

* an instructor `step` command (advance N sim-seconds while frozen) for frame-exact repeat takes;
* the five ops sheets missing from the worksheet YAML (WB-5.4-VL, WB-5.7-WI, WB-5.7-FR, WB-B, WB-C).
