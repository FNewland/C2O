# Script review D: V-SCDF-01, V-SCDF-02 (SpaceCDF design side)

Scope keys in this file are SpaceCDF seats (`design/configs/seats.yaml`, ids reuse the
chapter 21 / Table 1.4 positions): `team_leader`, `systems_engineer`, `mission_analyst`,
`payload_lead`, `power_engineer`, `aocs_engineer`, `comms_engineer`, `thermal_engineer`,
`structures_engineer`, `propulsion_engineer`, `cost_engineer`, `customer`. Decision-record
owners come from `design/configs/worksheets/decision_catalogue.yaml` (`seat:`).

Validation: `python3 -m c2ovideo validate V-SCDF-01 V-SCDF-02` gives `ok` for both, with no
`! acronym:` warnings. Both files load as YAML.

## V-SCDF-01 — Mission need to decision record

Audience now: all. Recommendation: **whole team.** It is the first wizard pass of the
study. All three decision records it touches (D-1.4-PROBLEM, -OBJECTIVES, -SPACE) belong to
the `team_leader` seat, but every seat has to agree the problem and objectives, and the
logbook mechanics (record, save, download) apply to everyone.

| Step | Deeper explanation (what, and the source: file § heading) | Animation idea (what moves; route) | Scope: Team or seat (why) |
|---|---|---|---|
| home | What a CDF is and why concurrent design beats passing the design from one discipline to the next. Source: `01_concurrent_design.md` §1.1.1 The problem with sequential design, §1.1.3 Key principles of concurrent design; the seats are in §1.5.1 Table 1.4. | Sequential handoff (a design passed along a line of desks, coming back again and again) against a ring of seats round one shared model, where a change spreads to every seat in one step. Route: Motion Canvas. | Team (what the tool is; every seat works in it) |
| problem | What a good problem statement contains (gap, who is affected, impact, no hardware) and the WHAT versus HOW principle. Source: `04_mission_needs_conops.md` §4.1.2 Structure of a good problem statement, §4.1.4 The WHAT versus HOW principle. | A sentence that names hardware ("6U CubeSat…") gets its solution words struck out and turned into a need. Route: Motion Canvas (text animation). | Team (shape) + `team_leader` (owns D-1.4-PROBLEM); the operational context feeds `mission_analyst` (ConOps) and `customer`. |
| record | Why decisions are recorded with a rationale and the runner-up, and what makes a decision record auditable. Source: `04_mission_needs_conops.md` §4.7 Documenting the trade decision. | none (the live UI is clearer) | Team (every seat writes records for its own decisions) |
| save | none: this is tool mechanics (privacy, 48-hour deletion, download). | none | Team |
| stakeholders | Stakeholder categories and the analysis matrix; measurable objectives, and the MoE/MoP/TPM chain that makes them verifiable. Source: `04_mission_needs_conops.md` §4.2.2 Stakeholder categories, §4.2.3 Stakeholder analysis matrix, §4.3.2 Writing good objectives, §4.3.3 The MoE / MoP / TPM hierarchy. | An objective splits into its measure ("≥ 90 %, pixel ≤ 60 m") and then into one TPM at a time, and each TPM is ticked at a review gate. Route: Motion Canvas. | Team (shape) + `team_leader` (owns D-1.4-OBJECTIVES); `customer` voices user needs; `payload_lead` checks that the measures can actually be met. |
| alternatives | The space versus non-space trade and the criteria for when space is justified; weighted scoring and sensitivity analysis. Source: `04_mission_needs_conops.md` §4.6.2 Alternative categories, §4.6.3 Decision criteria: when is space justified?, §4.5.5 Weighted score calculation, §4.5.6 Sensitivity analysis. | A weighted trade matrix fills in row by row; then one weight slider moves and the ranking reorders (or does not), which shows what sensitivity means. Route: Motion Canvas, or a SpaceCDF Decide-tab capture if it shows scores. | Team (the trade every seat must accept) + `team_leader` (owns D-1.4-SPACE); `mission_analyst` gives the coverage and revisit evidence. |

Acronyms changed:
- EN: CDF ("SpaceCDF. CDF stands for concurrent design facility…", with a plain gloss);
  PDR expanded in the stakeholders question ("preliminary design review (PDR)"), because the
  narration never says PDR, so the question is where a learner first meets it.
- FR: CDF, using the glossary term ("Le sigle CDF désigne un centre de conception concourante",
  replacing "installation de conception concourante", which is not the house term); PDR in the
  question ("revue de conception préliminaire (PDR)").
- Jargon glossed: "Markdown, a plain-text format" (FR "un format texte simple").
- Not spoken, so not added: ConOps, TRL, EPS, MDR, CDR. The "operational context" field is the
  first ConOps statement. I did not add the term to keep the step length, but see the notes below.

Notes / risks:
- The header comment says it prepares "LW-1.4 parts A–E", but `ties.worksheets` lists A, B, C
  and E. Part D (MoE / MoP / TPM trace) is not covered by any step, and D-1.4-OBJECTIVES is
  highlighted in the stakeholders step but is missing from `ties.decisions`. Either add it to
  the ties or change the comment.
- In the stakeholders step the narration says "you cannot verify at the review" and the
  true/false question asks about the PDR. It is consistent, but the narration already gives
  the answer away. That is acceptable because this is not a graded item.
- The textbook's first gate is the MCR (Table 1.3), while the SpaceCDF margin ladder starts at
  the MDR. Learners who meet both names will need one sentence on why. See explainer 3.
- "ConOps" is the name of LW-1.4 Part F and of the `mission_analyst` seat's focus. A follow-up
  video on the architecture step (promised at the end, "Next time, the architecture step")
  should expand it: "concept of operations, ConOps — con-ops".

## V-SCDF-02 — Budgets, margins and energy per orbit

Audience now: all. Recommendation: **whole team for the mass and allocation steps;
`systems_engineer` and `power_engineer` for the power, modes and energy steps.** Every seat
reads the budget bar and has to live within its allocation (the mass bar is where every seat's
equipment shows up). The power-by-mode table and the energy check are the Power seat's job
(seats.yaml: power_engineer `sees_first` "Power by mode, EPS equipment, eclipse energy"; it owns
D-2.4-POWER). The Systems seat holds the margins and owns D-2.4-MASS. Splitting it in two
(a 2-minute team part and a 2-minute Power/Systems part) would fit the seat model. Short of
that, keep it for the whole team, because every seat supplies its own units' power in each
mode.

| Step | Deeper explanation (what, and the source: file § heading) | Animation idea (what moves; route) | Scope: Team or seat (why) |
|---|---|---|---|
| mass | The two-level margin policy: a maturity margin per item, then a system margin by phase, and how they compound (1.20 × 1.20 − 1 ≈ 44 %). Source: `08_architecture_interfaces_budgets.md` §8.4.1 Mass budget, §8.4.2 The ECSS margin policy — two levels (Table 8.3, Figure 8.4); `21_position_reference.md` Systems Engineer, Common pitfalls ("Margin is not slack"). Ladder: `design/configs/margin_policy.yaml` `system_margin_ladder`. | A stacked bar grows segment by segment (estimate, then each item's maturity margin, then the system margin), then steps through the review gates as the margin layers shrink. Route: Manim (bar and labels), or SpaceCDF Budget tab captures at each gate. | Team (everyone reads the bar) + `systems_engineer` (sets the margin policy, owns D-2.4-MASS); `structures_engineer` owns the mass parameters (`mass.*`). |
| allocate | Roll-up against allocation: estimates add up from the bottom, allocations are handed down from the top, and when an estimate overruns, it eats margin rather than adding to its allocation. Source: `08_architecture_interfaces_budgets.md` §8.4.1 Mass budget; `21_position_reference.md` Systems Engineer, Decisions you own 2 (budget closure) and Common pitfalls (margin depletion goes in the change log); `01_concurrent_design.md` §1.5.2 Interface conflicts ("Mass budget exceeded"). | A top-down allocation tree and bottom-up estimate bars meet in the middle; one element's estimate grows past its allocation line, turns red, and the Systems seat moves margin over to cover it. Route: Motion Canvas. | Team (every seat negotiates its own allocation) + `systems_engineer` (arbitrates) |
| power | Orbit-average power as the sum of mode power × duty cycle; why the peak and the eclipse load size different things. Source: `08_architecture_interfaces_budgets.md` §8.4.4 Orbit-average power (key equation and worked table); `09_power_and_thermal.md` §9.2 Solar array sizing. | A power-versus-time trace over one orbit (sunlit and eclipse bands, imaging and downlink spikes) with the average line drawn through it and the peak marked. Route: ui-viz replay (`powerflow.js` fed a one-orbit time series from `power_budget.py`) or Manim. | `power_engineer` (owns D-2.4-POWER) + `systems_engineer` (power margin); Team only for the definitions |
| modes | Mode-based power budget and duty cycling; where the modes come from (the ConOps). Source: `08_architecture_interfaces_budgets.md` §8.4.3 Mode-based power budget (Table 8.4); `04_mission_needs_conops.md` §4.8.3 Operational modes, §4.8.4 Duty cycling; `18_operations_and_fdir.md` Table 18.1. | The mode-by-unit matrix lights up one column at a time as the spacecraft steps through its modes. Each unit's state (off, standby, on, peak) changes colour, and the column total feeds a bar. Route: Motion Canvas, or ui-viz `powerflow.js` replay. | Team (every seat supplies its units' rows: `payload_lead` for the imager, `comms_engineer` for the transceiver) + `power_engineer` (owns the table) |
| energy | Energy balance per orbit: what the array generates in each mode's attitude against the load with margins; battery depth of discharge for modes that run short. Source: `09_power_and_thermal.md` §9.2 Solar array sizing, §9.3.2 Sizing equations; `21_position_reference.md` Power Engineer, Formulas ("the array must cover the worst sunlit mode…") and Common pitfalls (the β-angle and which panels see the Sun). | A battery gauge over one orbit for each mode: Nominal ends level, while Imaging and Downlink drain steadily, which shows "fine for minutes, not for an orbit". Route: ui-viz replay (`powerflow.js`) with a series from `power_budget.py`. | `power_engineer` (judges it) + `systems_engineer` (budget health, LW-2.4/E); Team for the takeaway |

Acronyms changed:
- EN: MDR ("this first review, the mission definition review, MDR"; the screen shows "System
  margin at MDR"); in the question, MDR, PDR and CDR are expanded, and PRR–SRR is glossed in the
  answer's explanation ("the preliminary and system requirements reviews").
- FR: MDR ("la revue de définition de la mission, la MDR", the glossary form); PDR and CDR in
  the question; PRR–SRR glossed ("la revue préliminaire des exigences et la revue des exigences
  système", glossary terms).
- Jargon glossed: system margin ("insurance the team holds as a whole"; FR "une assurance que
  l'équipe détient dans son ensemble"); orbit average ("the power averaged over sunlight and
  eclipse"; FR "la puissance moyennée sur l'ensoleillement et l'éclipse"); attitude ("the way
  the spacecraft points"; FR "c'est-à-dire son orientation").
- FR fixes: "Par dessus" changed to "Par-dessus". Part E is now named as in the workbook ("le
  contrôle de l'état des bilans", replacing "le bilan de santé des budgets").
- C2O is a product name and is not expanded (register `expand: false`). EPS, TRL and ConOps
  are not spoken in this video.

Notes / risks:
- **Possible content error (power step).** The narration says the orbit average "sizes the
  solar array", and the peak "sizes the power distribution". Chapter 21 (Power Engineer, rule
  of thumb) says "The array must cover the *worst sunlit mode*, not the orbit average", and
  §8.4.4 says the peak sunlit mode and the eclipse load size the array and battery. I left the
  claim as it is because it is content, not wording. Franz should decide. A safe rewording
  would be: "the orbit average, which the array must deliver on average, and the peak, which
  sizes the power distribution and, in the worst sunlit mode, the array".
- **Margin numbers differ between book and tool.** Textbook Table 8.3 gives system margins of
  20 / 15 / 10 / 5 % by phase (0/A, B, C, D), while SpaceCDF's C2O ladder is 25 / 20 / 20 / 10 %
  by gate (MDR, PRR–SRR, PDR, CDR, from GSFC-STD-1000G plus the ESA IOD policy). The question's
  correct answer follows the tool. A learner who reads §8.4.2 first will see different numbers,
  so one sentence in §8.4.2 (or a note in LW-2.4/A) saying "SpaceCDF uses the stricter C2O
  ladder" would prevent confusion.
- `ties.decisions` lists D-2.4-MASS, but no step mentions or highlights it. Only D-2.4-POWER
  is named. Consider one clause in the mass step ("record why in decision D two point four,
  Mass"), or drop it from the ties.
- The energy step's "Nominal can. Imaging and downlink cannot" depends on the seeded
  EOSAT-1-like study (`seed_spacecdf_eosat`). If the seed changes, re-check the claim.
- The energy step has two consecutive `wait`s (1.5 and 1.0). This is harmless. I did not
  change it because `do:` was out of scope.

## Explainer candidates

1. **Margins: maturity, system, and the ladder (4–5 min).** Source:
   `08_architecture_interfaces_budgets.md` §8.4.2 (Table 8.3, Figure 8.4); `21_position_reference.md`
   Systems Engineer; `margin_policy.yaml`. Outline: an estimate is uncertain, and a new design
   is more uncertain than a flown part, so each item carries a maturity margin. The system as a
   whole carries a second margin because the errors are correlated. The two compound, and the
   system margin is released gate by gate as knowledge grows. Margin is insurance, not slack:
   when it is given away, the change is logged. The video also reconciles the book's schedule by
   phase with the C2O ladder by gate. Route: Manim (stacked bars stepping through the gates),
   finishing on the SpaceCDF Budget tab. Prepares LW-2.4/A, LW-2.4/E, D-2.4-MASS. Audience:
   whole team, required for `systems_engineer`.
2. **Orbit-average power and the energy balance (5–6 min).** Source:
   `08_architecture_interfaces_budgets.md` §8.4.3–§8.4.4; `09_power_and_thermal.md` §9.2–§9.3;
   `21_position_reference.md` Power Engineer. Outline: loads by mode, then duty cycles, then
   the orbit average. What the array must cover (the worst sunlit mode, at end of life) and what
   the battery must cover (the longest eclipse at its load). Why a mode can be power-negative
   for minutes but not for a whole orbit. Depth of discharge and cycle life. Route: ui-viz
   `powerflow.js` replay of a one-orbit series from `power_budget.py`, plus Manim for the
   equation. Prepares LW-2.4/B, LW-2.4/E, D-2.4-POWER, and the later power and thermal
   worksheet. Audience: `power_engineer` and `systems_engineer`, recommended for the team. It
   would also bridge to the ops side (`eps_tcs` position, the SoC trend during passes).
3. **Lifecycle phases and review gates (3–4 min).** Source: `01_concurrent_design.md` §1.4.1–§1.4.4
   (Table 1.3); `16_cost_and_reviews.md` (gate evidence); `design/configs/ecss_review_gates.yaml`.
   Outline: the NASA and ECSS phases, the gate at the end of each one (MCR/MDR, PRR, SRR, PDR,
   CDR…), the question each gate answers and the evidence it needs, and why margins and
   verifiable objectives are tied to gates. This is where learners get the full names once, so
   the short forms land in every later video. Route: Motion Canvas timeline. Prepares
   LW-1.4/C (measurable objectives), LW-2.4/A, and the gate checklist in the `team_leader`
   seat's view. Audience: whole team.
4. (Shorter, optional.) **Need to objectives to TPMs (3 min).** Source: `04_mission_needs_conops.md`
   §4.3.3. Covers LW-1.4/D, which V-SCDF-01 skips. Route: Motion Canvas tree. Audience: whole
   team, led by `team_leader`.

## Register additions

- `PRR`: preliminary requirements review / revue préliminaire des exigences (short P-R-R).
  Used in the V-SCDF-02 answer explanation and in `ecss_review_gates.yaml`.
- `SRR`: system requirements review / revue des exigences système (short S-R-R). Used in the
  same places.
- `MCR`: mission concept review / revue de concept de mission (short M-C-R). Not used in these
  scripts, but it is the textbook's first gate (Table 1.3) and will be needed by explainer 3.
- `CBE`: current best estimate / meilleure estimation actuelle (glossary entry "CBE / MEV").
  The narration says the phrase without the short form. Add it if the Budget tab or a later
  video shows "CBE".
