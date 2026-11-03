# Decisions — SpaceCDF redesign and voice loops (Franz, 2026-11-02)

Answers to the "Decisions for Franz" table of the SpaceCDF workflow redesign
(Claude Doc "SpaceCDF workflow redesign", §6) and the voice questions in
`docs/web_2026-10/ARCHITECTURE.md` §12.

| # | Decision | Ruling |
|---|---|---|
| 1 | Default gate profile | **Full ECSS: MDR → PRR → SRR → PDR** (four separate gates). IOD and the three-gate C2O profile stay selectable per study. |
| 2 | System margin ladder | **Stricter: 25 / 20 / 20 / 10 %** (MDR / PRR–SRR / PDR / CDR), labelled "C2O default" in `margin_policy.yaml`. |
| 3 | Phase 0 gate label | **Rename MCR → MDR**; "MCR" only in the NASA skin. |
| 4 | Seat claiming | **Self-claim + instructor override**, with an instructor lock. |
| 5 | Ownership enforcement | **Warn, then owner review.** Editing a parameter owned by another seat warns the editor first ("owned by Power — your change goes to them for review"). If they continue, the edit is stored as a *pending change* the owning seat must accept or reject; until accepted, the owner's value stands in analyses. Team leader and Instructor follow the same rule unless they hold the owning seat. Every edit and review is logged. |
| 6 | SMO seat authority | **MCS on the ground**; instructor board via a local GSG route; no identity crosses the link. |
| V1 | Voice platform | **LiveKit.** |
| V2 | Voice server host | **Its own small VM** with a public IP, started/stopped with `c2o up/down`. |
| V3 | Recordings | Off by default (opt-in). |
| V4 | Loops | **FD loop** (all positions), **Ops-coord**, **one per subsystem** (EPS/TCS, AOCS/FD, TTC, Payload, FDIR/Systems, Propulsion), **Instructor/SIM** loop hidden from students; more loops to be decided — keep loops data-driven in `voice_loops.yaml`. |
| L1 | Logbook visibility | Private to the participant (instructor sees counts at most). |
| L2 | Logbook retention | 48 h after last write; 7-day hard cap. |

## Model round 2 — thermal, payload, FDIR and instructor rulings (Franz, 2026-11-03)

Answers to `OBC_THERMAL_ANALYSIS.md` §8.5, `THERMAL_MODEL.md` §7, `INSTRUCTOR_CONSOLE_DESIGN.md` §13 and the
open S19 item in `manual/08_fdir.md`. Branch `model-round2`.

| # | Decision | Ruling and what changed |
|---|---|---|
| M1 | S19 ea 1001 (fires on BATTERY_SOC_CRITICAL, dispatched func 10 = `AOCS_SLEW_TO`) | **Take the payload off.** It now dispatches `EPS_POWER_OFF` line 3 (payload), like ea 3001 / 6001. Unpinned from `KNOWN_MISROUTED`; engine test. Its trigger id (SoC critical, not the "bus undervoltage" of its name) stays in `KNOWN_TRIGGER_DRIFT`. Manual 08 EPS-07, PUS service reference. |
| M2 | Imager/FPA limits while the payload is off | **Limits only while the payload or its cooler is on.** New on-board validity parameter 0x0426 `tcs.fpa_limits_valid` (TCS HK SID 3): S12 0x0408 ×2 and 0x0601 carry `validity: {0x0426, 1, 1}`; `mcs/limits.yaml` gains an optional `valid_when` (schema `LimitValidity`, MCS state `"unchecked"`, an active alarm returns to normal) on 0x0408 / 0x0601 / 0x0617. Payload FPA_UNDERTEMP follows the same rule; FPA_OVERTEMP is judged only while cooled operation is expected. No survival band (none exists in the configuration). |
| M3 | FPA cooler in STANDBY | **Off in STANDBY, on only to prepare for imaging.** `PAYLOAD_SET_MODE` 0/1 and `EPS_PAYLOAD_MODE` 0/1 release the cooler, 2/3 request it; imaging preparation is `FPA_COOLER(on=1)`. Cool-down from the STANDBY equilibrium: `fpa_ready` after 378 s, detector at the setpoint ±0.5 K after 579 s. Power-budget `nominal` (cooler off) is now the model's nominal. Planner `imaging_pass`: `FPA_COOLER_ON` + 480 s cool-down, lead time 587 s, booking 660 s, `tcs` added to its subsystems; target-driven sequence likewise. Cards NOM-001/002, COM-010/011/012, CTG-001, progressive load shed, eclipse transition, manuals 03/06, TC catalogue, workbook + textbook (EN+FR). |
| M4 | Cooling between separation and first boot | **Tick the thermal network in phases 0–1** with nothing powered (no dissipation, no heater) before the separation timer expires. The default start (phase 3) is unchanged, so the commissioning walkthrough baseline is unchanged. Separation scenario from +20 °C: at timer expiry (30 min, sunlit, tumbling) structure +19.6, OBC +20.1, battery +20.3, imager +14.8 °C; 60 min after separation (eclipse) structure +7.9, OBC +15.3, battery +14.8, imager +7.2 °C. Battery heater line is OFF until LEOP-007, so there is no battery heating before boot. |
| M5 | Continuous imaging drains the battery | **Keep it, and say so.** `tools/power_budget.py` gains the `imaging_continuous` profile and a sustainable-duty table: at the worst beta (−31.2°, EOL) imaging all orbit is 46.6 W against 45.1 W (−1.4 W, −2.3 Wh per orbit); break-even duty 94 %, 77 % with the 10 % margin (84 % at β −20.8°). Manuals 01 §3.2 and 06 §8 (EN+FR). The planner warns above 77 % of an orbit (`imaging_pass.power_constraints.sustainable_duty_pct`, `PowerConstraintChecker.check_imaging_duty_cycle`, message translated in the planner UI). The thermal limit (30 min per orbit) binds first. |
| M6 | Instructor "first symptom" | **Expected symptoms per failure.** `configs/eosat1/instructor/expected_symptoms.yaml` lists, for every failure in the catalogue, the events / S12 monitors / parameter limits it is expected to trip first (served with `GET /api/failure-catalog`). The recorder times inject → first symptom to the first EXPECTED one (event ids at any severity; parameter symptoms on the on-board values, reaching the ground with the first HK packet carrying them) instead of the first warning. `tools/failure_symptoms.py` injects each failure headless (default parameters, from a flown NOMINAL / imaging / pass-override state) against a run without it, and `--check` verifies the list: 55 of 61 met in the run and not in the control; 6 declared not checkable with a reason (`aocs.mtq_failure`, `aocs.gain_corruption`, `aocs.css_head_fail`, `obdh.boot_image_corrupt`, `tcs.heater_open_circuit`, `ttc.redundant_failure`). |

Findings from the headless injections, for Franz (not changed):

* `eps.sada_stuck` is invisible to the string-yield S12 monitors: their validity ("a healthy string would give ≥ 0.2 A") is computed at the frozen drive angle, so the strings read "not lit", not "degraded". The symptom is the wing current staying low in sunlight.
* `aocs.gain_corruption` at its default (×10 on Y) stays stable in NOMINAL for 30 min; the effect text says the attitude error diverges.
* `ttc.receiver_degrade` (spacecraft receiver noise figure) lowers the DOWNLINK Eb/N0 and margin (0x0519 / 0x0503), not an uplink margin.
* `eps.overcurrent` at its default (×3 on the payload line, 0.26 A in STANDBY) never reaches the line's trip threshold; its only effect is a warmer imager.
* Uncooled STANDBY now rests 2 K inside the FPA high warning limits (node +10.0…+11.8 °C against +14.0; detector +9.8…+11.9 against +13.5, nominal β −30°); a hotter season or a hot payload can reach the yellow.
