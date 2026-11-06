# Course video scripts: acronyms, deeper explanation, team vs position (2026-11-06)

This review covers all 12 current scripts and the 19 scripts still to come. It looks at three
things:

- whether each acronym is spoken in full the first time;
- where the textbook could go deeper, and whether that depth could be animated;
- which material the whole team needs and which belongs to one console position.

| Group | Videos | Detailed review |
|---|---|---|
| A | V-OPS-01–04 (NOM-001, LEOP-001/002, alarms) | [A_ops_01-04.md](A_ops_01-04.md) |
| B | V-OPS-05–07 (LEOP-004/007/005) | [B_ops_05-07.md](B_ops_05-07.md) |
| C | V-OPS-08–09, V-PLN-01 (LEOP-006/003, planner) | [C_ops_08-09_pln_01.md](C_ops_08-09_pln_01.md) |
| D | V-SCDF-01–02 (SpaceCDF) | [D_scdf_01-02.md](D_scdf_01-02.md) |
| E | Coming: COM-001…013, CTG-001, five concept explainers | [E_upcoming.md](E_upcoming.md) |
| — | Evidence: acronyms in narration, animation, team vs position training | [RESEARCH.md](RESEARCH.md) |

## 1. Acronyms: what changed

- **First use, full form, then the short form the team says**, once per video and per
  language. Examples:
  - "the nominal procedure NOM-001, nom for short";
  - "the attitude and orbit control system, the AOCS" / « le système de contrôle d’attitude et
    d’orbite, le SCAO »;
  - "structure identifier two, SID two";
  - "the packet utilisation standard, PUS, service nine, time management".

  After the first use, only the short form is used, so learners get used to working in
  acronyms.
- **Card numbers are read the way the team says them:** "nom zero zero one", "lee-op zero zero
  one", "com…", "contingency…", "emergency…". Before this change they were spelled out
  "N O M".
- **Opaque jargon gets a one-clause gloss of what it does at first use.** This covers
  bootloader, B-dot, magnetorquers, body rates, light time, the J2000 epoch, orbit-average
  margin, insertion, off-nadir angle, the system margin, and the mode names (DETUMBLE,
  COARSE_SUN).
- **A register** in `video/lexicon/acronyms.yaml` now holds about 120 entries. Each gives the
  English and French expansion and how the team says the short form. Names, mode names and
  on-screen values are marked as needing no expansion.
- **`validate` warns** when a video says an acronym for the first time without its expansion
  nearby. The warning never blocks a build.
- **The rule is written into `video/README.md`** for future scripts.
- **The French narration now follows the glossary:**
  - "B-dot", not « B-point »;
  - « magnétocoupleur »;
  - « senseur stellaire ».

All 12 storyboards validate with no acronym warnings, and the pipeline tests pass. The
narration has changed, so **every rendered video needs re-rendering**.

## 2. Where deeper explanation helps, and what to animate

The per-step tables in A–E name the textbook section for each step. The same few concepts came
up again and again across the five reviews. They are better served by short concept explainers
(3–6 min, segmented, one H5P question per segment) than by making the walkthroughs longer. The
research supports animating **only change over time that the console cannot show**
(Höffler & Leutner: representational animation d ≈ 0.40, decorative ≈ 0).

| # | Explainer | Raised by | Source | Animation route | Audience |
|---|---|---|---|---|---|
| 1 | **Energy balance through an orbit** (orbit-average margin, β angle, eclipse) | A, B, C, D, E | ch. 09, ch. 07 § 7.1.2 | replay `shared/ui-viz/powerflow.js` over a `power_budget.py` orbit | Team |
| 2 | **A telecommand's life: S1 accepted ≠ completed** | A, E | PUS_SERVICE_REFERENCE § Service 1 | Motion Canvas packet path | Team |
| 3 | **CCSDS packets and PUS services; housekeeping and SIDs** (enabled vs requested; powering a unit does not switch on its report) | A, C, E | ch. 12; PUS_SERVICE_REFERENCE | Manim packet layout | Team |
| 4 | **Commanded vs flying mode: the AOCS mode machine** (DETUMBLE → COARSE_SUN handover, demotion, eclipse) | B, E | ch. 10; ch. 18 § 18.2.2 | Motion Canvas state machine + `attitude3d.js` replay | Team, deeper for aocs |
| 5 | **B-dot: what magnetorquers can and cannot do** | B | ch. 10 | `attitude3d.js` replay of rates decaying | aocs |
| 6 | **Spacecraft time** (epochs, CUC, three clocks, NONE/GROUND/GPS) | C | TIME_ARCHITECTURE | Manim timeline | Team shape; fdir_systems |
| 7 | **From a GPS fix to an orbit** (state vector → elements, SSO, LTAN) | C | ch. 07 | `groundtrack.js` + Manim | aocs, flight_director |
| 8 | **Link budget term by term and the rate ladder** (SAFE / LOW / HIGH) | A, E | ch. 11; LINK_BUDGET_AND_RATES | Manim waterfall + `skyplot.js` | ttc |
| 9 | **Line before unit** (power the line, then command the unit) | E | ch. 09 § 9.1.3 | Motion Canvas | Team |
| 10 | **On-board protection ladder** (S12 monitor → S19 event-action → load shed) | E | ch. 18; CTG-001 | Motion Canvas | Team (+ fdir_systems, eps_tcs) |
| 11 | **Maturity, margins and review gates** (how margins shrink from MDR to CDR) | D | ch. 08 Table 8.3; ch. 16 | Motion Canvas | design team |

The research also recommends a short **"Words on the console"** team video each week. It would
pretrain that week's subsystems, modes and acronyms before the procedure videos (pretraining,
median d ≈ 0.85).

## 3. Team vs position

The pattern is consistent: **the shape of every card is team material, and the commanding and
judging belong to specific positions.**

| Video | Recommendation |
|---|---|
| V-OPS-01 NOM-001 card as workbook | Whole team |
| V-OPS-02 LEOP-001 | Team for the shape; commanding by ttc + fdir_systems |
| V-OPS-03 Alarm → ticket | Whole team; star-tracker content is aocs |
| V-OPS-04 LEOP-001 5a / LEOP-002 | Team for LEOP-002; rate ladder is ttc, values eps_tcs |
| V-OPS-05 LEOP-004 | Whole team, with an eps_tcs deep dive |
| V-OPS-06 LEOP-007 | Team for card and record steps; eps_tcs + aocs for the commanding |
| V-OPS-07 LEOP-005 | aocs + flight_director, plus a short team cut (do not command what the spacecraft does itself) |
| V-OPS-08 LEOP-006 | Team for the shape; flight_director + fdir_systems for the commanding |
| V-OPS-09 LEOP-003 | Team for the end-of-LEOP poll; aocs for the GPS check band |
| V-PLN-01 Planner | Whole team; imaging step payload_ops (+ eps_tcs) |
| V-SCDF-01 Wizard | Whole design team |
| V-SCDF-02 Budgets | Whole team for mass and allocations; systems + power seats for power and energy |
| Coming COM cards | Mostly one or two positions each (see E) |

The evidence on cross-training (Marks et al. 2002; Salas meta-analyses; NASA and ESOC practice)
gives this routing:

- **Team videos:** everyone watches them.
- **Position videos:** that seat watches them, plus **one neighbouring seat** as
  cross-training.
- **Opening of each position video:** about 15 seconds on who depends on that seat and what it
  reports.

To act on this, the storyboard `audience:` field should take position keys. The single "all"
videos that mix the two (V-OPS-06, 07, 08) would split into a team cut and a position cut.
That is a pipeline change I have **not** made yet.

## 4. Decisions for Franz (found on the way)

**Cards and configs that contradict each other or the simulator**

1. NOM-001 Step 7 polls "rates < 0.05 °/s", but Step 3 expects a pitch rate of 0.063 °/s.
   Read literally, every nominal pass is a NO-GO.
2. LEOP-001 still calls the 1 kbps rate "BEACON" after the SAFE rename, so the on-screen
   failure text says "beacon tier".
3. COM-013 expects `fpa_ready = 1`, but going to STANDBY now switches the cooler off.
4. COM-010: `FPA_COOLER` is only allowed for eps_tcs, so payload_ops cannot send it. Its NEXT
   line also points to COM-011, not COM-012.
5. COM-001 quotes 0.78 m² and a ~64 W peak; the config gives 0.24 m² and 88.6 W.
6. CTG-001 says shedding the transmitter saves ~20 W; `eps.yaml` gives 5 W (LOW) or 11 W
   (HIGH).
7. COM-006 names two stations but its table lists five, and its 0xFF gate value is ambiguous.

**SpaceCDF and textbook**

8. The power step says the orbit average sizes the solar array. Textbook §8.4.4 and chapter 21
   say the worst sunlit mode does.
9. System margins: Table 8.3 gives 20/15/10/5 %; SpaceCDF uses 25/20/20/10 %.

**Grading**

10. The CTG-001 recovery is scored in three scenarios, so its video should read the card
    without flying the recovery. COM-003/006/007/008 also contain scored commands.

**Still open from before**

- The COARSE_SUN magnetorquer-only hold. This now also holds back COM-001 and COM-004.
- Mounting `LinkBudgetTool.tsx`.

## 5. Proposed order for the next videos

1. Concept explainers 2–3 (S1, PUS/SIDs) and 10 (protection ladder). These need no breakpoint
   and do not depend on AOCS.
2. Energy balance (1).
3. COM-007, COM-008, COM-002.
4. COM-006 (after fixing its text), then the link budget (8).
5. COM-005, COM-003, then attitude (4).
6. The payload chain COM-009 → 010 → 012 → 011 → 013, after fixes 3–4.
7. COM-001 and COM-004, after the COARSE_SUN fix.
8. CTG-001, after your scoring ruling, as a card-reading video.
