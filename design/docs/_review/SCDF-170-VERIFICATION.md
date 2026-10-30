# SCDF-170 "closing the loop" — independent verification

**Branch:** `arcadia-spine` (15 build commits `4e2f432..00ab00c` + 1 verifier fix commit **3acdf76**)
**Date:** 2026-09-09
**Method:** static checks; then a real `uvicorn` on a throw-away SQLite DB
(`DATABASE_URL=sqlite+aiosqlite:////tmp/e2e2/db.sqlite`, `SPACECDF_DATA_DIR=/tmp/e2e2/data`)
driven only through the public HTTP API with `httpx`, on a **6U EO CubeSat**: template
`6u_eo_cubesat` (EOSAT-1, 450 km SSO, 36 % eclipse), mission root + space segment,
`populate-subsystems` (nano, KB equipment: BPX 77 Wh battery, P60 PCDU, P110 panel, CubeWheel
Medium 0.011 N m s, CubeStar 20", CSS, iMTQ, UHF TRX + dipole, NanoMind A3200), plus a
multispectral imager (1.5 kg, 20 W, 1 Mbps @ 10 % duty, −20…40 °C), a 6U deployable array
(32 W EOL), an S-band transmitter (2 W, 6 dBi, 2 Mbps), 1.8 kg structure, 6U envelope
100×226×366 mm, component dimensions, PCDU cold-redundant, 4 modes (Safe 1.9 W, Nominal 4.1 W,
Imaging 25.1 W, Downlink 9.6 W) as `mode` elements with `activate` rows, 7 requirements
(MR-1 → SR-PWR-1 `el:<root>.sim_min_soc_pct ≥ 20`, SR-AOCS-1 `el:<root>.aocs_pointing_est_deg ≤ 0.5`,
SR-MASS-1 `mass.dry_mass_kg ≤ 12`, SR-GS-1 `el:<root>.gs_data_return_gb_per_day ≥ 1`, SR-STR-1 (T),
SR-EPS-1 `el:<EPS>.mass_kg ≤ 2.5`), stations SvalSat + TrollSat. The server was restarted
between every step (the sandbox kills background processes per call), which is what exposed
three of the persistence bugs below. Scripts: `/tmp/e2e2/e2e_[a-g].py` (not committed).

## 1. Results per step

| Step | What | Result |
|---|---|---|
| 1 | `pytest tests --ignore=tests/test_level_workbench.py` | **PASS** 294 passed / 1 skipped before fixes; **301** after (7 regression tests added) |
| 1 | `npx vite build` | **PASS** (chunk-size warning only) |
| 1 | `npx tsc -b` error count | **PASS** 105 (= ceiling) |
| 2 | Template instantiate → study | **FAIL → FIXED** (B1: never persisted, gone after restart) |
| 2 | N1/N3 | PASS: all 8 subsystems numeric mass/power (roll-up or heritage), 12 interfaces (6 power bus, 6 data bus) + 4 exchange items. Caveat N1-b below |
| 2 | Modes via `activate` / `mode-profile` | **FAIL → FIXED** (B2: in-memory only; after restart every mode = 0 W and the sim ran with `p_load = 0`) |
| 2 | Design loop | PASS: converged 16 it / 0.5 s; root `mass_dry_mass_kg` 7.03, `power_sa_area_m2` 0.216, SA 76.5/70.9 W BOL/EOL |
| 2 | mission_simulation / ground_segment / physics / fmeca / vv | PASS after fixes — numbers in §2 |
| 2 | RTM CSV rows = requirements | PASS 7 = 7; VCD docx 200 |
| 3 | Override BPX `mass_kg` 0.2→1.2, run design | PASS: EPS 0.495→2.395 kg, `mass_dry_mass_kg` 7.03→7.99, `budget/mass.sum_nominal` 6.201→7.201, agent input `power.eps_mass_kg` = 2.395 `position_override` |
| 3 | `ref` formula `children("power_avg_w")*3` on Communications | PASS: `link.ttc_power_w` 11→42 W (override), `power_sa_area_m2` 0.216→**0.362**, sunlight load 31→62 W. Caveat N4 (column keeps 42 W after the formula is deleted) |
| 4a | Battery 77→4 Wh | PASS: `SIM_SOC_BELOW_MIN` critical, "Minimum 0.0 % at t=02:37 (orbit 2) in mode Safe", fix "raise battery capacity to 5.5 Wh (now 4.0 Wh)", element = BPX |
| 4b | Remove both stations | **DEVIATION** (N5): no `GS_NO_STATIONS`; the closure silently used catalogue defaults (SvalSat, Kiruna) with a warning |
| 4c | Imager data rate ×10 | **DEVIATION** (N6): no effect — `data.generated_per_day_gb` from the design-loop run (2.0 GB/d) outranks the payload element; `GS_DATA_DEFICIT` not reachable from the model |
| 4d | Structure moved to (0.09, 0.20, 0.05) m | PASS: CP-CG offset 0.167→0.073 m, momentum/orbit 2.51e-3→2.30e-3 N m s, wheel margin 338→378 %; `physics` stale after the PATCH; `AOCS_CG_OFFSET_HIGH` still (73 mm > 2 %) |
| 4e | Imager 50 W | PASS: `THERMAL_OUT_OF_RANGE` "98.1 / −11.1 °C outside −20..40", fix "~3007 cm² radiator" |
| 4f | SR-AOCS-1 0.5→0.005° | PASS: `AOCS_POINTING_MARGIN` major "0.013 deg exceeds 0.005", `requirement_ids=['SR-AOCS-1']`, VI → failed; physics stale on the edit only after fix B6 |
| 4g | PCDU `redundancy_type` cold→none | PASS after fix B3: `FMECA_SINGLE_POINT` on NanoPower P60 with the redundancy fix text; before B3 the PATCH silently dropped the field |
| 4 | `POST /conflicts/{id}/resolve` | PASS: `resolved_at` set, open count 7→6 |
| 5 | Stale after run-all | **FAIL → FIXED** (B4): 4 of 6 stale immediately; after fix all 6 fresh, second pass fresh, requirement *text* edit → none stale, pointing *threshold* edit → design_loop + vv (+ physics after B6), wheel power edit → all |
| 5 | Auto-closure | PASS: SR-PWR-1 A-item `failed` with `evidence analysis:<run>` after the 4 Wh run, `passed` after restore |
| 6 | Branch Baseline → "Big battery", override 300 Wh in option | **FAIL → FIXED** (B5): option sim gave DoD **51 %** with 300 Wh (ran on the 2.2 W KB panel because the option had no design run). After fix: baseline DoD 3.97 % vs option 1.02 % (ratio 3.9 ≈ 300/77); compare lists 4 deltas; baseline rows unchanged |
| 7 | Kill + restart on same DB | PASS: analyses (6, all fresh), 21 conflicts, 2 options, 7 VIs, 2 stations, mode profile 25.1 W, 57 root params (baseline and option), sim series file — identical snapshot before/after |
| 8 | Frontend vs observed shapes | PASS with one fix (B8, timestamps) — §4 |
| 9 | §13 / non-goals | PASS — §5 |

## 2. Numbers (final state, BPX override 1.2 kg still active)

| Parameter | Value | Plausibility |
|---|---|---|
| `sim_min_soc_pct` / `sim_max_dod_pct` | 96.03 % / 3.97 % at t=9480 s (orbit 2), Nominal | Hand check: 5.1 W × 0.36 × 93.6 min = 2.9 Wh = 3.7 % of 77 Wh ✓. Before fix B7 both were 80 %/20 % for every design (initial condition) |
| `sim_energy_balance_wh_per_orbit` | +59.2 Wh | SA 70.9 W × 0.64 sunlit × 1.56 h ≈ 71 Wh − loads ≈ 12 Wh ✓; sign and magnitude vs SA consistent |
| series | 1402 samples, SoC 100→96→100, `p_load` {5.1, 10.6} W, `p_gen` max 70.9 W, modes {Nominal, Downlink}, buffer 0 GB | **Imaging never scheduled** (N2): payload mode and data generation absent from the sim, so backlog/buffer are trivially 0 |
| `gs_contact_min_per_day` | 153.3 min (15 passes × 8.6 min per station) | High end for 450 km/97.4°, but Svalbard + Troll see essentially every pass; 2 × 128 min is symmetric and within reason |
| `gs_data_return` / generated | 1.935 / 2.0 GB/d, backlog 0.115 GB, closure 96.8 % | Return < generated only by the post-last-pass residual ✓ |
| `gs_min_link_margin_db` | 2.47 dB (Troll, G/T 22) vs 8.97 dB (Svalbard, G/T 28.5) | 6.5 dB difference = G/T difference ✓. Rate 9.34 Mbps/tx power come from the *link agent*, not the modelled 2 Mbps/2 W transmitter (N6) |
| `mp_total_mass_kg` | 7.201 | = leaf sum incl. override ✓ (design-loop dry mass 7.99 adds agent margins) |
| CoM (x,y,z) | 0.05, 0.113, 0.350 m in a 0.1×0.226×0.366 envelope | Inside, x/y centred ✓; z near the top face because the auto-placer stacks 16 boxes to 0.52 m in +z (N3) |
| `mp_ixx/iyy/izz` | 0.0939 / 0.0876 / 0.0225 kg m² | Positive-definite; Izz ≪ Ixx ≈ Iyy as expected for a tall stack; order matches m·L²/12 |
| `mp_cp_cg_offset_m` | 0.167 m | Consistent with CoM vs envelope centre (0.183 − …); warning fires correctly |
| Torques (GG/aero/SRP/mag/total) | 1.35e-7 / 3.38e-7 / 9.4e-8 / 2.44e-7 / 4.48e-7 N m | Right order for a 6U at 450 km; GG ≈ 3n²ΔI ✓ |
| `aocs_momentum_per_orbit_nms` / capacity / margin | 2.51e-3 / 0.011 (CubeWheel Medium from KB perf) / 338 % | 0.011/0.00251 = 4.4 → 338 % ✓ |
| `aocs_pointing_est_deg` / req / margin | 0.0130° / 0.5° / 0.487° | 47" vs 20" star tracker + control error — plausible |
| Thermal (hot/cold) | bus 59.4/−20.1 °C; EPS 43.9/−20.8; Imager 98.4/−15.9; wheel 64.8/−16.3 | Bus hot consistent with a sunlit steady state at peak power (~65 W internal). Component hot cases pessimistic: 0.5 W/K joints put the 20 W imager 39 K above the bus → 10 of 14 nodes out of range (N7). Battery not a node (< 0.5 W) |
| FMECA | 21 modes, max RPN 32 (structure deployment), 12 single points, 7 critical | PCDU excluded once `redundancy_type=cold` ✓ |
| V&V | 7 items, 5 A auto-passed, 1 T planned, 1 R planned, closure 71.4 %, `VV_REQ_UNVERIFIABLE` on MR-1 | ✓ |
| Option "Big battery" | DoD 1.02 % vs baseline 3.97 %; balance 59.9 vs 59.2 Wh | ✓ after B5 |

## 3. Bugs found and fixed (all in commit **3acdf76**, suite 301 green)

* **B1 — template studies never persisted.** `POST /templates/{id}/instantiate` put the `Study` in the in-memory store only; gone after restart (all elements/analyses orphaned). Now `db_save_study` like `POST /studies`.
* **B2 — mode membership in-memory only.** `POST /elements/{mode}/activate` appended to `_mode_elements`; nothing wrote `ModeElementRow`, which is what `analysis_context` reads. After a restart every mode had 0 members → sim ran with `p_load = 0 W`, "97.6 % of the time in Nominal" flagged as safe time. Now upserted to `mode_elements`; `mode-profile` falls back to the table.
* **B3 — PATCH silently dropped `dimensions_mm`, `redundancy_type`, `part_number`, `subsystem_domain`, `owner_position`.** `ElementUpdate` lacked them (pydantic ignores unknown keys, 200 returned). The physics envelope fell back to the class default and the FMECA fix "set redundancy_type='cold'" was unreachable on existing elements. Added to `ElementUpdate`.
* **B4 — every analysis stale after any closure ran.** The `params` hash subset included the closures' own computed output rows; running V&V last flagged sim/ground/physics/design stale. `_hash_subset("params")` now skips rows that are `computed`, formula-less and owned by one of the five closures (`CLOSURE_OWNED_DOMAINS`); manual/formula rows still count; design-loop/agent rows still count (the sim reads them).
* **B5 — option without its own design run lost every agent-derived input.** `_load_latest_design(option_id)` returned `{}` → SA power fell to the first KB panel (2.2 W) → DoD 51 % with a 300 Wh battery. Now falls back to the baseline's design run (reads = baseline ∪ overrides).
* **B6 — physics not stale on a pointing-requirement change.** It reads requirements but declared only `elements/params/orbit/thermal`. Added `requirements`.
* **B7 — `sim_min_soc_pct` was the initial condition.** `conops_executor` starts at a hard-coded 80 % SoC; the closure took the minimum over the whole run, so every energy-positive design reported 80 %/DoD 20 % (a 300 Wh battery scored *worse* than 77 Wh). `PowerParams.initial_soc_pct` (default 80, bare endpoint unchanged); the closure starts full and skips the first orbit.
* **B8 — timestamps naive → wrong "last run … ago" in the browser.** SQLite drops tzinfo; `row_to_dict` emitted `2026-09-10T00:09:14` which `new Date()` parses as local time (hours in the future for UTC−n users → "just now"). Now `+00:00`-tagged.
* Cosmetic: V&V acceptance text showed the raw capitalised element id for `el:<id>.x` paths and labelled every `el:` path "design loop"; now element name + closure label ("…(analysis: mission simulation)").

## 4. Findings NOT fixed (design-level or out of scope)

* **N1-b — subsystem roll-up columns are not refreshed when a child is added.** EPS showed 0.495 kg (populate-time value) after the 0.9 kg array was added, until a design run rewrote it. The flat/budget sums were right (leaves only), so the parameter panel and the budget disagree until a design loop runs.
* **N2 — user modes other than nominal/safe/downlink are never scheduled.** `_classify` maps the model's modes onto the executor's three slots; "Imaging" (payload on, 25 W, data generation) never runs, so the sim's energy balance is optimistic and its data buffer is 0 while the ground closure sees 2 GB/day. The closure should at least warn "mode X is never scheduled" and ideally drive the payload mode from the modes' duty cycles (`conops_executor` limitation; design §2.1 promised modes from `ModeElementRow`).
* **N3 — +z auto-stack ignores the 2×3U footprint.** 16 components stacked to 0.523 m in a 0.366 m envelope; warning is correct but `AOCS_CG_OFFSET_HIGH` fires on every unplaced 6U. A footprint-aware packer would be a small improvement.
* **N4 — agent write-back sticks in the element column.** After deleting the `ref` formula, Communications `power_avg_w` column stayed 42 W (merged by the design loop) while the effective value went back to 11 W; and `link.ttc_power_w` = 11 W is the link agent's estimate, not the leaf sum (14 W) — `seed_design_state` lets the previous run's `COMPUTED` value outrank a non-overridden model sum (§1.5 precedence). Worth an ADR: model leaf sums should outrank stale agent outputs.
* **N5 — `GS_NO_STATIONS` is unreachable in practice.** With no selected station the closure uses catalogue defaults (warning only). A study can "close" its ground segment on stations nobody chose; consider making the fallback opt-in or raising the conflict as `warning`.
* **N6 — the ground closure is driven by the link agent, not the modelled radio.** `_pick` order is `flat` → `latest_design` → element performance, so `link.downlink_rate_mbps` 9.34 and the agent's tx power beat the S-band transmitter element (2 Mbps, 2 W) and `data.generated_per_day_gb` (2.0, from the template) beats the imager's data rate. Physically the modelled hardware is the truth once it exists; same precedence question as N4. Also means the ×10 data-rate scenario cannot trigger `GS_DATA_DEFICIT` through the model.
* **N7 — thermal joints.** 0.5 W/K per joint gives ΔT ≈ 40 K for a 20 W payload; 10/14 nodes out of range is conflict noise on a nominal design. A per-class or mass-scaled joint conductance (1–5 W/K bolted) would be more representative.
* **N8 — adding a ground station flags fmeca/vv/physics stale** (elements hash includes ground elements). Harmless but noisy.
* **N9 — PATCH cannot clear a field** (`None` values skipped); `redundancy_type` must be set to the string `none`.

## 5. Spec §13 / design §4 review

`SPINE_SPEC.md` is still not in the repo; the four prohibitions were checked on `git diff 4e2f432..arcadia-spine`: no new ORM (4 new `Base` tables `analysis_runs`, `analysis_conflicts`, `options`, `verification_items`; dict repos in the `element_repo` style); no Redis or new runtime dependency (`scipy` already in `spacecdf-common`); no duplicate registries — every closure imports the existing calculator (`compute_disturbance_torques`, `compute_mass_properties`, `thermal_network`, `compute_link_budget`, `predict_contacts/schedule_downlinks`, `simulate_orbit`, `fmeca` catalogue, `generate_vv_plan`) and `PROPERTY_TO_PARAM` is extended, not copied; mutations broadcast via `_arcadia_events.broadcast_mutation` as in SCDF-160. Non-goals respected: no attitude/multi-body integration (momentum = RSS torque × period), no radiation, greedy scheduler, options do not clone the tree (documented), no SysML v2 import, no cost 2.0.

## 6. Verdict

**Accept with the fix commit.** The loop is genuinely closed: model → context → six analyses → parameters, conflicts, compliance, V&V items → back to the model, with options and stale tracking, and the numbers are physically consistent once the eight bugs above are fixed (two of them — the 0 W modes and the 80 % initial SoC — made the simulation's headline number meaningless in every restarted session). The remaining findings are precedence/design questions (N2, N4, N6 deserve a decision before SCDF-180) rather than defects in the range's contract.
