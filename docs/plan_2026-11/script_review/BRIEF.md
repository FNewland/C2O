# Script review brief (2026-11-06)

Franz (course author, SYS5186 / ORBIT NORTH, uOttawa) asked for a full pass through
every course-video script with three goals:

1. **Acronyms.** "Most acronyms stand for something, and when reading them out it is
   generally best to say the full thing, then maybe the shortened acronym the first time —
   but we work in acronyms and abbreviations, so e.g. NOM is nominal, or nom for short."
2. **Deeper explanation.** Where would a deeper explanation, e.g. from the textbook,
   help — and could it be animated?
3. **Team vs role.** Which material is general to the whole team, and which is specific
   to a role or position?

## Where things are (repo root `/home/claude/c2o`)

- Storyboards: `video/storyboards/<ID>.yaml`. Narration is `steps[].say.en` / `.fr`.
  Format and pipeline: `video/README.md`. Validate with
  `cd video && python3 -m c2ovideo validate <ID>` (prints `! acronym:` warnings from the
  new lint `video/c2ovideo/acronyms.py`).
- Acronym register (expansions, EN and FR, and how the team says each short form):
  `video/lexicon/acronyms.yaml`. **Read it first; use its expansions.** If you need an
  acronym that is not in it, do not edit it: list it in your report under
  "Register additions".
- Pronunciation lexicons `video/lexicon/en.yaml`, `fr.yaml`: **do not edit** (another
  agent owns them). Card IDs are already read as "nom zero zero one", "lee-op zero zero
  one", "com…", "contingency…", "emergency…".
- Procedure cards the videos follow: `sim/configs/eosat1/procedures/**` (index in
  `procedure_index.yaml`).
- Worksheets: `sim/configs/eosat1/worksheets/ops_week3.yaml`; learner workbook
  `design/configs/worksheets/learner_workbook.yaml`.
- Textbook (CC BY 4.0 "Concurrent Spacecraft Design"): `design/docs/oer/chapters/*.md`
  (07 orbit & environment, 09 power & thermal, 10 AOCS, 11 communications, 12 structures
  /propulsion/OBDH, 17 ground segment, 18 operations & FDIR, 19 operations rehearsal,
  **21 position reference**, 22 derivations). Course books: `design/docs/course/`.
  Ops docs: `sim/docs/` (OPERATIONS_GUIDE, LINK_BUDGET_AND_RATES, PUS_SERVICE_REFERENCE,
  TIME_ARCHITECTURE, PROPULSION_GUIDE, OBCP_GUIDE, PARAMETER_MAP).
- Console positions (`sim/configs/eosat1/mcs/positions.yaml`): `flight_director`,
  `eps_tcs`, `aocs`, `ttc`, `payload_ops`, `fdir_systems`, `propulsion`.
  Ground/design side (SpaceCDF) has its own seats — see chapter 21 and
  `design/` configs.
- Animation building blocks already in the repo: `shared/ui-viz/` modules
  (`groundtrack.js`, `skyplot.js`, `attitude3d.js`, `attitude2d.js`, `powerflow.js`,
  `stack3d.js`, `overview.js`; each `mount(el) → update(model)`, so a JSON time series can
  be replayed frame by frame). Licence-clean explainer tools: Manim Community (MIT) for
  equations/geometry/packet layouts, Motion Canvas (MIT) for timed block diagrams.
  Telemetry time series: the LEOP/commissioning fly-through test, `power_budget.py`,
  `link_budget_ladder.py`, `pass_gap_analysis.py`.

## Task A — edit the narration (only the storyboards assigned to you)

For each video, per language, across the steps in order:

- The **first time** an acronym is spoken, say the full form, then the short form the team
  uses. Natural, not stilted. Examples:
  - EN: "Open the nominal procedure NOM-001, Pass Startup — nom for short."
    Better still when it reads naturally: "Open nominal procedure one, NOM-001."
  - EN: "the attitude and orbit control system, the AOCS"; FR: "le système de contrôle
    d’attitude et d’orbite, le SCAO".
  - EN: "the launch and early orbit phase, LEOP"; FR: "la phase de lancement et de début
    d’orbite, la LEOP".
  - EN: "housekeeping report, structure ID two — SID two"; FR: "les données de servitude,
    identifiant de structure deux, SID deux".
  - PUS services: "the packet utilisation standard, PUS, service nine, time management —
    S9 on the console".
- After the first use, the short form alone is right: operators work in acronyms, and the
  videos should get learners used to hearing them.
- Each video stands alone (learners watch them out of order), so expand once **per video**.
- Words that are names, mode names or on-screen values (GO, NO-GO, SAFE, LOW, DETUMBLE,
  COARSE_SUN, NONE, GROUND, EOSAT-1, GPS) need no expansion — but a mode name may deserve a
  plain gloss the first time ("DETUMBLE, the mode that slows the tumble").
- Also check *unspoken jargon* that is not an acronym but still opaque to a week-2
  student (e.g. "B-dot", "light time", "orbit-average margin", "bootloader") and gloss it
  briefly at first use if the step does not already.
- Keep EN and FR parallel in meaning. French follows the house style (identifiers stay
  English; French prose expansions; "satellite" for EOSAT-1; typographic apostrophes ’;
  non-breaking space before « : ; ? ! » is not needed in YAML say text — copy the existing
  style). The glossaries `sim/tools/i18n/glossary.csv` and `design/tools/i18n/glossary.csv`
  give the agreed French terms — use them.
- Keep every step's narration roughly the same length (add at most ~15 words per step;
  trim elsewhere if a step grows a lot). Do **not** change `do:`, `setup:`, selectors,
  questions' correctness, ties, or ids. Do not touch question/answer text unless it has an
  unexpanded acronym that a learner meets there first (questions are read, not spoken).
- Never add anything that pre-answers the graded quiz WB-5.4-Q or a scored-scenario
  recovery.
- Do not invent numbers: anything you say about what is on screen must already be in the
  narration or in the procedure card.
- Run `cd /home/claude/c2o/video && python3 -m c2ovideo validate <IDs>` until there are
  no `✗` problems and no `! acronym:` warnings for your files (if a warning is a false
  positive, say why in your report). Also check YAML still loads.

## Task B — write the reflections

Write `docs/plan_2026-11/script_review/<your group>.md` with, for each video:

```
## <ID> — <title>

Audience now: <audience field>. Recommendation: whole team | <positions> (+ why)

| Step | Deeper explanation (what, and the source: file § heading) | Animation idea (what moves; route: ui-viz replay / Manim / Motion Canvas / SpaceCDF tool / none) | Scope: Team or <position keys> (why) |
|---|---|---|---|

Acronyms changed: <list, EN / FR>
Notes / risks: <anything that looked wrong on the card or in the narration>
```

Then a short section **"Explainer candidates"**: concepts that came up repeatedly and
deserve their own short (3–6 min) concept video, each with the textbook section,
a one-paragraph outline, the animation route, the worksheet/decision items it would
prepare, and the audience.

Guidance for the scope column:
- **Team**: everyone at the console needs it to follow the pass or the poll (procedure
  card mechanics, GO/NO-GO, logbook, alarms/ACK, passes, the shape of LEOP, what each
  position owns).
- **<position>**: only that seat commands or judges it (e.g. AOCS rate thresholds and
  B-dot → `aocs`; bus voltage, SoC, heaters → `eps_tcs`; link margins, carrier lock,
  bit rate → `ttc`; S9 time, S1 verification, S12/S19 monitoring → `fdir_systems` /
  `flight_director` depending on the card's "Owner" line; payload → `payload_ops`).
  Check the card's own position/owner lines and chapter 21 before deciding.
- Mixed steps are normal: say "Team (shape) + aocs (thresholds)".

Report back in under 200 words: what you changed, the warnings left, register
additions, and the top 3 explainer candidates.
