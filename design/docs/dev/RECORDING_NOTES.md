# Northern Fire and Ice walkthrough: recording notes

How `DESIGN_SCRIPT_V2.md` was turned into course videos, what each video covers, what could not be
shown and why, and what looked wrong on camera. Written 2026-11-11 on branch `nfi-recording`.

## How the videos are made

- **Pipeline.** The existing `video/c2ovideo` pipeline, unchanged: one storyboard per video in
  `video/storyboards/`, captured in headless Chromium against `python3 -m c2ovideo stack up spacecdf`,
  narration in English and French in the storyboard (`say`), rendered with
  `python3 -m c2ovideo build <ID>`. Nothing in `video/c2ovideo/` that the fingerprint covers was
  edited, so no other video went stale because of this work.
- **Starting point of each video.** `video/c2ovideo/nfi_seed.py:seed` (a setup `python:` call)
  runs `design/tests/fixtures/nfi/recording.py`: the recording seed (`seed_nfi(..., recording=True)`)
  plus the scenes filmed in the earlier videos (`--after`, the same API calls as
  `test_w3_integration.py`), then the team of script §0.3: the 9-seat preset with Propulsion and
  Cost & risk, every seat (and the Customer) held by one presenter whose browser is
  `scdf.client_id = nfirec`. `nfi_seed.py:after` applies the same steps to the filmed study in the
  middle of a video, for what "the other seats do the same way" (the ledger agreements, the rest of
  the Licensing tab). Manual dry run: `python -m tests.fixtures.nfi.recording --stage S4 --after
  "licensing ledger" --client nfirec` from `design/`.
- **Seats.** Every scene starts by switching the active seat (`[data-testid=active-seat]`), so each
  write is recorded for the seat that owns it.
- **Captions.** The script's Caption EN / FR is drawn as a lower third (scene number and seat above
  the caption line) by a small script each storyboard installs in its setup (`x-caption-js`, called
  as `__lt(kicker, text)` per scene). The lower third dims while a highlight ring overlaps it. The
  narration also produces the usual WebVTT captions.
- **Narration.** Plain professional register, EN and FR, first use of each acronym expanded
  (`validate` shows no acronym warning for these videos). Rendered here with the silent backend only
  (`--tts silence`): timing and captions are checked, the voice is not. On the Mac:
  `bash video/scripts/render_all.sh scdf` (or the IDs) renders them with the cloned voice; the
  capture follows the real narration length.
- **Typed data.** What the team types (wizard texts, logbook entries, licensing entries) is the
  English baseline of `tests/fixtures/nfi/*.yaml` in both languages, like every seeded row the later
  videos show; the UI and the narration are French in the French video. The go / no-go records are
  typed in the language of the video.

## Storyboards and scenes

Ids reuse the VIDEO_REVIEW plan where it assigns the topic (V-SCDF-08 … -15, -17). V-SCDF-16
("Taking a seat and reviewing a change") is not used: claiming the seats is in V-SCDF-08 and the
change review in V-SCDF-22. V-SCDF-18 … -24 are **proposed** ids for the walkthrough chapters the plan
does not name (budgets and negotiations, licensing, the reviews). V-SCDF-01 … -07 are untouched.

| Video | Title | Scenes | Starts from | Length EN / FR (silent) |
|---|---|---|---|---|
| V-SCDF-08 | Defining the mission from a proposal | 1.1–1.6 (wizard, seats claimed) | empty server (live wizard) | 6:03 / 6:12 |
| V-SCDF-17 | The V in SpaceCDF: phases, deliverables and reviews | 1.7, 5.8, 5.11, 5.12 | S4 + licensing, ledger, negotiations, price | 3:36 / 3:49 |
| V-SCDF-11 | Ground stations and contact time | 2.1, 2.2, 2.3 (GS4 signed), 2.7, 4.9 | S4 + Inuvik RF chain | 3:23 / 3:30 |
| V-SCDF-12 | The requirements tree | 2.6, 3.1 | S4 | 2:00 / — |
| V-SCDF-18 | Allocations every seat agrees: budgets, cost and risk | 2.4, 3.3 (ledger, N7 signed), 2.9, 2.8, 4.10 (3.2 inside 3.3) | S4 + licensing | 3:16 / — |
| V-SCDF-10 | Weighting criteria and the Pugh matrix | 3.4, 3.4b, 3.6 | S4 + licensing, ledger, negotiations, price | 2:19 / 2:29 |
| V-SCDF-09 | Choosing equipment from the catalogue | 4.1, 4.2, 4.3, 4.5, 4.6, 4.7, 4.8 | S4 + licensing, ledger, negotiations, price | 3:09 / 3:28 |
| V-SCDF-19 | Modes, power and the downlink: two negotiations | 2.5, 4.11, 4.4, 4.12 (N1 signed), 4.13 (N3 signed) | S4 + licensing, ledger, GS4, N7, price | 3:13 / 3:36 |
| V-SCDF-20 | Integration: interfaces, stack, power lines, FDIR and operations | 3.5, 3.7, 3.8, 5.1, 5.2, 5.3, 5.4, 5.6, 5.7, 5.9 | S4 + licensing, ledger, negotiations, price | 3:37 / 3:51 |
| V-SCDF-13 | Designing housekeeping telemetry | 5.5 | S4 + licensing, ledger, negotiations, price | 1:38 / 1:47 |
| V-SCDF-21 | Licensing from the design | 5.10 (filled on camera) | S4 + ledger, negotiations, price | 2:13 / 2:24 |
| V-SCDF-15 | Building the review package | 5.13 | everything to the PDR passed | 1:04 / 1:09 |
| V-SCDF-22 | Passing the MDR, PRR and SRR | 6.1, 6.2, 6.3, 6.4, 6.5 (ECP-02), SRR pass of 6.6 | S4 + licensing, ledger, negotiations, price | 4:26 / 4:21 |
| V-SCDF-23 | PDR evidence: interfaces, reliability and the thermal model | 6.6 (ICDs), 6.7, 6.8 | + SEMP, debris, ECP-02, MDR/PRR/SRR passed | 2:47 / 2:47 |
| V-SCDF-24 | When you disagree with the score, check the logic | 6.9 (ECP-01), 6.10 (PDR passed) | + ICDs, reliability, thermal | 4:09 / 4:23 |
| V-SCDF-14 | Saving, sharing and reopening a study | chapter 8 | everything to the PDR passed | 1:28 / 1:28 |

Total: 48 min in English, 45 min in French (silent backend: about 150 words a minute; the cloned voice will change each length a little).

Order of the walkthrough: 08 → 17 (1.7) → 11 → 12 → 18 → 10 → 09 → 19 → 20 → 13 → 21 → 17 (5.8,
5.11, 5.12) → 15 → 22 → 23 → 24 → 14. V-SCDF-17 gathers the protocol scenes (1.7, 5.8, 5.11,
5.12) in one video, as SE_INTEGRATION §3.3 asks.

Every scene of the script is in one video except: 2.3–4.13 are not re-filmed where they are only
"show the seeded rows"; the list below says what is shown instead.

## What the script asks that is not shown, and why

| Scene | Not shown | Why |
|---|---|---|
| 1.6 | The four ground stations in the mission definition editor | The editor has no station field; the stations are elements (scene 2.1, seeded). |
| 1.7 | The Instructor switching the protocol checks to Block | The presenter holds the team seats, not the instructor seat (needs an instructor e-mail on the server); the narration says Block exists and the card shows "Protocol checks: Warn". |
| 2.1 | Renaming the spacecraft, adding Harness, the stations and the out-of-scope launch segment | Seeded (S1); the video walks the finished tree. |
| 2.2 | Evaluate Ground Architectures, Predict Contact Windows, Record as trade | Both ground widgets give wrong figures on this study (see larger defects); T-M01 and T-M02 are seeded as decided, so the video shows the trade-by-gate summary and the T-M01 matrix instead. |
| 2.4 | Allocation entered at level 0; the 12.2 W power allocation; D-2.4-MASS | The 6.0 kg allocation is typed at level 2 (the spacecraft row); the power line and the decision record are not re-entered. |
| 2.6 | Typing the five mission rows and running the bulk import | The 302 rows are seeded; the video opens + Add Requirement and the import panel, then filters on MIS-SCI. |
| 2.8 | RSK-035 entry form; Export CSV | The register has no CSV export (BOM has one, shown in 4.10); the row is highlighted. |
| 3.3 | AR rows under SYS-BUD in Requirements | Not filmed (time). One agreement (Power, EPS) is filmed; the others are applied mid-video. |
| 3.4 | Record decision on T-04/T-05, D-2.4-POWER | Seeded as decided; the matrices and totals are shown. |
| 3.5 | Propose links → Accept all; the ten added links | Seeded (S2); the buttons and the N² chart are shown. |
| 3.6 | Option B overrides (EPS −0.32 kg, −0.4 W) | Option B is branched on camera; the per-option overrides were not entered, so Compare options shows two equal options. The narration states the trade result instead. |
| 3.7 | Auto-place, moving the star tracker, Approve layout | Seeded as approved. The checks under the views fail on this study (larger defect). |
| 3.8 | Run Analysis result frame | The run is filmed; the Analyses card shows the result. |
| 4.1–4.8 | Selecting each unit from the catalogue, custom components with TRL, Properties, the trades T-01…T-08 | The equipment is seeded (S2); each seat opens its subsystem and the payload seat searches the catalogue. |
| 4.4 | "DL-2" and Apply as design case | The stored cases are named by site ("DL Inuvik 1 W rural (300 K)"); the two cases of the caption are highlighted; Use as design case is not clicked. |
| 4.9 | Entering the RF chains of all stations, Yamcs, LB-19 | The Inuvik chain is seeded except the time reference, which is added on camera. |
| 4.10 | RSK-009 to mitigating | Not filmed. |
| 4.11 | Propose powers per mode, typing the differences, Accept, Run the rules | Seeded; the matrix and the energy view are shown. |
| 4.12 | D-PI-01 in the open-item register | Not pointed at (it is listed in V-SCDF-17, scene 5.12). |
| 5.1–5.4, 5.6 | The proposals and the line, bus and item entries | Seeded (S2–S4); each tab is shown. |
| 5.7 | Add rule FR-01 … FR-11 | The NFI rules are not in the seed: the Operations tab shows the rule-proposed FR-01…FR-05, whose FR-01 is a different rule (RF inhibit before separation). The caption "Flight rule one pauses the transmitter…" does not match the screen; see larger defects. |
| 5.8 | Gaps fixed, the diagrams document downloaded | Not filmed. |
| 5.10 | Every licensing field typed | The applicant and three protection-plan fields are typed and saved on camera; the other seats' entries (the baseline's `licensing_record`) are saved mid-video. The ISED brief is a DOCX download and cannot be opened in the browser, so the document list is shown. |
| 6.1 | Deleting the regulator link to provoke the inventory warning | The inventory shows the real warning of this study (the partial MOE deliverable and the unread textbook chapter), which is the same teaching beat. |
| 6.3 | The note "Reviewed for the SRR" | The SEMP issue button takes no note. |
| 6.6 | The note "Issue A for the PDR" | The Raise Issue A button takes no note. |
| 6.10 | Instructor sign-off | Not filmed (no instructor seat). |
| 8 | Load from File through the file chooser | The capture cannot drive a native file chooser; the storyboard feeds the file the study just exported to the Load button's input (a few lines of `js`), which is what a user does by picking the saved file. |

## What looked wrong on camera

### Fixed on this branch

1. **Seat switching did not stick** (`seats/SeatLayer.tsx`): the switch refetched the team with the
   old `X-C2O-Seat` header, so the server answered with the old seat and the select jumped back.
   The answer of the switch is now taken at once.
2. **Seats drawer showed the wrong team size** right after the wizard (`seats/SeatDrawer.tsx`): it
   kept its defaults when it mounted before the team arrived, so Propulsion and Cost & risk looked
   unchecked.
3. **Stakeholder ids** printed as timestamps (`1794366217375 Northern communities…`) in the register
   after the wizard (`MissionWizard.tsx`): the wizard now numbers them.
4. **Orbit trade GSD** (`services/orbit_trade.py`, `routers/lifecycle.py`): the table printed a
   generic 15 cm telescope (3.2 m at 590 km) next to a 58 m camera; it now scales the study's camera
   (58.2 m, 150.7 km swath at 590 km) to each candidate. Test added in `tests/test_decision_tools.py`.
5. **"38.6 % %"** in the negotiation tables (`NegotiationPanel.tsx`).
6. **Quick Start "give this spacecraft its subsystems"** offered on a ground station
   (`blockLevels.ts`); and a station's parts can now be added as components (`BlocksPanel.tsx`).
7. **Level tag** "Stakeholder need" covered the requirement text in the table (`RequirementsTable.css`).
8. **Change control impact** printed raw keys (`contacts.station.inuvik_min_per_day -5.03`) and seat
   ids (`DecideV2.tsx`): it now lists named lines, before → after (delta) and the owning seat, in EN
   and FR.
9. **Spacecraft tab crashed** ("Cannot read properties of null (reading 'toFixed')") on the recording
   seed (`components/ui/MarginBar.tsx`, a zero allocation).
10. **Phase card** printed seat ids (`Owner: team_leader`) and two status glyphs per deliverable
    (`PhasePanel.tsx`).

### Larger, left open

1. **Stack layout fails its own checks** (scene 3.7): on the recording seed the Spacecraft tab
   shows column height 706.6 / 328.5 mm, the centre of gravity 11.7 cm off in Z (limit 7), three
   overlaps and four units outside their column or face, against the script's ≈ 295 of 328 mm. The
   video narrates "the checks list what still needs attention", but the scene caption ("The stack
   fits with a tenth of its height to spare") contradicts the screen until the seeded layout or the
   auto-placement is fixed. **Re-render V-SCDF-20 after the fix.**
2. **Flight rules** (scene 5.7): the seed does not load the NFI rules FR-01…FR-11 of v1 §5.7; the
   proposed rules use the same ids with other texts. Seed them (or rename the proposals) and
   re-render V-SCDF-20.
3. **Energy per orbit** (scene 4.11, Modes → Energy per orbit): generated 7.9 Wh against needed
   9.1 Wh with a "Negative or DoD over limit" alarm, while the script expects ≈ 19.6 Wh against
   ≈ 6.7 Wh (the wings' 12.2 W EOL generation does not seem to reach this view). The orbit average
   (4.17 W) is right.
4. **Ground Segment Trade** (level 1): every architecture scores 0 % and the list names commercial
   providers (KSAT, AWS), against the "no partner or institution" rule. Not filmed.
5. **Ground Contact Schedule** (level 1): 318.6 min/day with identical 8.4-minute windows at every
   station and data volumes in Gbit (0.0), against the union of 125.7 min/day that the data budget
   and GS4 use. Not filmed.
6. **Ground-segment analysis card** (scene 2.7): contact 115 min/d (−8.5 % from 125.7, outside the
   ±5 % of the TOOL-CHECK) and "returned 0.00 / 0.00 GB/d" in red (13 MB/day rounds to zero GB).
7. **Orbit trade period**: 96.3 min at 590 km (R = 6371 km) against the script's 96.5–96.6
   [TOOL-CHECK].
8. **Spacecraft-level canvas** shows the mode nodes as blocks next to the subsystems, which pushes the
   subsystem row out of the small canvas; the storyboards drill in with a dispatched double-click.
   Design tools (orbit and constellation presets) also appear at subsystem level.
9. **Console 404** on every gate view: `GET …/gate-baselines/diff?gate=…` before two gates have
   passed. Harmless, but it fills the console of every capture.
10. **Risk register** wraps the risk text in a very narrow column (RSK-034/-035 rows several
    lines tall).
11. **Alternatives ranking** (wizard step 3, scene 1.4): the list ranks commercial imagery first and
    Landsat 13th of 13, against the script's "Sentinel-2 and Landsat ranked high" (the mission's
    60 m, 3-day, community-owned values do not seem to drive the ranking). The narration only says
    the free missions are in the list. The list also names commercial providers (Planet, Maxar,
    ICEYE, Spire, Iridium).
12. **French UI, English server texts**: in the French videos the wizard's key question and the
    alternatives' descriptions, the evidence column of the Phase card ("Problem statement written
    (115 words)") and several analysis findings stay in English. "Science Segment" is not
    translated while the other segment names are ("Segment spatial", "Segment sol").
13. **End-of-review logbook prompt** ("Review finished: download your logbook") opens by itself a
    while after a gate has passed, including gates passed through the API, and blocks the page
    until dismissed. The storyboards dismiss it before each gate action.
14. **Smaller points seen in passing**: the French decimal comma is used in the Modes tab only
    (other panels show "4.17"); Load gives no visible confirmation that the study was opened; the
    gate verdict takes several seconds to change from "Under review" to "Passed" after the pass
    (the storyboards wait for it); each ICD row repeats its reference inside its title.

## Tool checks read on camera

| Scene | Script | On screen |
|---|---|---|
| 2.2 | period 96.5–96.6 min, eclipse 34–36 min | 96.3 min, 37 % (≈ 35.6 min) |
| 2.3 | union 93.4 → 125.7 min/day, margin −12 → +38.5 % | 126 min/day, 38.6 % (with) |
| 4.1 | GSD 58.2 m, swath 150.7 km | 58.2 m, 150.7 km (mission need card, orbit trade after fix 4) |
| 4.4 | DL Ottawa urban +0.4 dB, northern +4.0 dB | +0.4 dB, +4.0 dB |
| 4.11 | orbit average 4.17 W | 4.168 W |
| 5.5 | FULL 3.75 kbit/s designed, 4.8 allocated | 3748 / 4800 bit/s |
| 6.5 | union 125.7 → 118.0, margin 38.6 → 34.6 %, sail lifetime 3.3 → 2.3 y | 126 → 118 min/day, 38.6 → 34.6 %, 3.3 → 2.3 y |
| 6.7 | reliability ≈ 0.88 | 0.88 |
| 6.9 | C 3.65, A 3.50, robust | C 3.65, A 3.50, robust, runner-up A behind by 0.15 |

## Stills

Two stills per scene (English and French, 1280 px, taken near the end of each step) are kept with the
renders, outside git: `video/out/<id>/stills/{en,fr}_<step>.jpg`. Key frames:

| Scene | Still |
|---|---|
| 1.5 seats | `video/out/v-scdf-08/stills/en_seats.jpg` |
| 1.6 mission definition | `video/out/v-scdf-08/stills/en_missiondef.jpg` |
| 1.7 Phase card | `video/out/v-scdf-17/stills/en_phase.jpg` |
| 2.3 GS4 agreed | `video/out/v-scdf-11/stills/en_gs4.jpg` |
| 3.3 N7 agreed | `video/out/v-scdf-18/stills/en_n7.jpg` |
| 2.9 priced project | `video/out/v-scdf-18/stills/en_price.jpg` |
| 4.12 N1 agreed | `video/out/v-scdf-19/stills/en_n1.jpg` |
| 5.5 housekeeping | `video/out/v-scdf-13/stills/en_sids.jpg` |
| 5.8 V diagram | `video/out/v-scdf-17/stills/en_vdiagram.jpg` |
| 5.10 licensing | `video/out/v-scdf-21/stills/en_protection.jpg` |
| 6.5 ECP-02 approved | `video/out/v-scdf-22/stills/en_ecp02.jpg` |
| 6.6 ICDs at Issue A | `video/out/v-scdf-23/stills/en_icds.jpg` |
| 6.8 thermal model | `video/out/v-scdf-23/stills/en_thermal.jpg` |
| 6.9 T-A01 evidence | `video/out/v-scdf-24/stills/en_evidence.jpg` |
| 6.9 decision, ECP-01 rejected | `video/out/v-scdf-24/stills/en_decide.jpg` |
| 6.10 PDR passed | `video/out/v-scdf-24/stills/en_pdr.jpg` |

## Left to do

- Render with the cloned voice on the Mac (`bash video/scripts/render_all.sh scdf`), then the
  French review (`python -m c2ovideo check <ID>`).
- Fix larger defects 1–3 and re-render V-SCDF-19 and V-SCDF-20.
- Decide whether V-SCDF-18 … -24 keep these ids, and place them in `design/moodle/course/manifest.py`
  and the decks (VIDEO_REVIEW §3.4).
- Revise V-SCDF-01 … -07 to the Northern Fire and Ice example as the VIDEO_REVIEW plan says; the
  walkthrough videos overlap them (01 ↔ 08, 02 ↔ 18/19, 03 ↔ 19, 04 ↔ 12, 05 ↔ 20, 06 ↔ 18, 07 ↔ 22).
