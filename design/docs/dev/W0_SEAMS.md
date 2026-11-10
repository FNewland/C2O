# W0 seams: module map, shared APIs and file ownership

Work package W0 ("Enablers") of the SpaceCDF change plan for the Northern Fire and Ice teaching
mission (prefix `nfi`). W0 gives the six wave-1 agents stable seams so that each of them edits its
own files only. This page is the contract. Change it only with the agent that owns the seam.

Path abbreviations (all relative to `design/`):

| Abbreviation | Path |
|---|---|
| `S/` | `packages/spacecdf-server/src/spacecdf_server/` |
| `C/` | `packages/spacecdf-common/src/spacecdf_common/` |
| `AG/` | `packages/spacecdf-agents/src/spacecdf_agents/` |
| `FE/` | `frontend/src/` |

Agents: **R** requirements, **H** telemetry and modes, **X** export core, **L** licensing and
disposal, **D** decide, mission and ConOps, **A** platform, AIT and schedule.

---

## 1. Export router: `S/routers/exports/` (was `routers/exports.py`, 2,325 lines)

One module per document family. Each module has its own `router = APIRouter()`. The package
`__init__.py` includes the routers in `FAMILIES` order. That order is the route order of the old
single file, so `/openapi.json` did not change.

| Module | Routes (prefix `/api/exports`) | Owner (wave 1) |
|---|---|---|
| `_common.py` | none: `_run_design_for_study`, `_read_orbit_params`, `_form_factor_from_mass` (legacy) | X |
| `smo.py` | `POST /smo/{id}`, `GET /smo/{id}/validate` | H (with the sim export) |
| `packs.py` | `POST /docs/{id}` (review data packs) | X |
| `fsw.py` | `POST /fsw/{id}` | D (W7.03, wave 3) |
| `mbse.py` | `POST /mbse/{id}` | D (W7.03, wave 3) |
| `docx.py` | `POST /docx/{doc_type}` | X |
| `launch_icd.py` | `POST /launch-icd/{id}` | X |
| `rsssa.py` | `POST /rsssa/{id}` | L |
| `deorbit.py` | `POST /deorbit/{id}` | L |
| `thermal.py` | `POST /thermal-report/{id}` | X |
| `test_plan.py` | `POST /test-plan/{id}` | X (A writes the environment levels through W8a) |
| `worksheet.py` | `POST /worksheet/{template_id}` | X |
| `regulatory.py` | empty router: the seam for `POST /regulatory/{kind}/{id}` (W5.04) | L |

Rules:

- A new export family is a new module plus **one line** in `FAMILIES` in `__init__.py`. Nothing
  else in `__init__.py` changes. To keep the new routes at the end of `/openapi.json`, append the
  module to the end of `FAMILIES`.
- The design loop is called as `_common._run_design_for_study(...)`. Tests patch it in one place:
  `monkeypatch.setattr(routers.exports._common, "_run_design_for_study", fake)`.
- `routers.compliance` and `routers.lifecycle` still import `_run_design_for_study` from
  `routers.exports`. The package re-exports it, as it re-exports every endpoint function.
- This FastAPI version keeps included routers lazily, so `app.routes` does not list
  `/api/exports/...`. To inspect routes, walk `exports.FAMILIES[i].router.routes` or
  `app.openapi()["paths"]`.

## 2. Word generators: `S/services/docx/` (was `services/docx_generator.py`)

| Module | Function | Owner |
|---|---|---|
| `_common.py` | styles, cover page, footer, ToC, rich content, tables, `_add_section`, `_add_diagrams` | X |
| `did.py` | `generate_did_docx` (used by the VCD) | X |
| `bom.py` | `_render_bom_docx` | A (W5.05 BOM columns) |
| `mrd.py` | `generate_mrd_docx` | D for W1.06 (ConOps summary, success criteria, constraints), then X |
| `conops.py` | `generate_conops_docx` | D (W7.02) |
| `vp.py` | `generate_vp_docx` | X for W1.09a, then **A** (W8a). X does not touch it after W1.09a |
| `ts.py`, `ird.py`, `semp.py`, `rmp.py`, `testplan.py` | the generator of the same name | X |
| `regulatory.py` | `_generate_regulatory_docx` (shared stub) | L (replaced in W5.04) |
| `review.py` | `_generate_review_package_docx` (stub) | X (retired in W4.14) |
| `pack_hooks.py` | interim `HOOKS` for the pack documents `trades`, `review_report`, `ait`, `schedule`, `licensing`, `tmtc` (used until the owner's module defines `pack_docx`) | X |
| new: `trades.py`, `review_report.py` | | D |
| new: `ait.py` | | A |

`services/docx/__init__.py` holds `DOCX_GENERATORS`, the registry behind `/docx/{doc_type}`. The 400
message lists its keys in order, so the order is part of the API. Owner: X. New documents get
their own route in their export family. They are not added to this registry.
`services/docx_generator.py` is now a re-export shim. New code imports from
`spacecdf_server.services.docx`.

## 3. Study collector: `S/services/export_context/` (W0.2)

```python
from spacecdf_server.services.export_context import collect, SECTIONS, StudyExport

sx = await collect(study_id, gate="pdr", lang="en")          # whole study, once
sx = await collect(study_id, sections=["rollup", "risks"])   # only some sections (the others empty)
sx.rollup["mass"]["cbe_kg"]; sx.requirements["items"]; sx.errors   # {section: "Type: message"}
sx.as_dict()                                                  # JSON-ready
```

`GET /api/studies/{id}/export-context?gate=&lang=&sections=a,b` returns `as_dict()` (404 for an
unknown study, 422 for an unknown section).

**Every new or reworked generator takes a `StudyExport`.** It does not read `_elements`,
`_requirements` or `study.*` itself (EG #10).

Sections (`SECTIONS`, in collection order). Each section is one module in
`export_context/sections/<name>.py` with `async def collect(ctx) -> dict` and
`def empty() -> dict`:

| Section | Today | Shape (main keys) | Owner |
|---|---|---|---|
| `need` | real | `MissionNeed` as JSON | X |
| `mission` | real | `name, phase, gate_profile, definition` (`MissionRequirements`), `orbit` (+ period, eclipse, orbits/day) | X |
| `elements` | real | `items` (depth, name order), `interfaces`, `allocations` (budget allocations), `counts` | X |
| `rollup` | real | `services.rollup` `as_dict()` (see §4) | X |
| `requirements` | real | `items` (level, then code order; `generated_interface` flag for `IR-*`; `parent_ids`, `objective_ids`, `parent_codes` from W2.03 relations), `counts` | X (fields: R) |
| `verification` | real | `items`, `counts` by status | X (fields: R, AIT evidence: A) |
| `risks` | real | `items` (with `score` = L×C, highest first), `counts` | X |
| `trades` | real (one Pugh record) | `items` [{id, state, version}] | D (W6.01) |
| `decisions` | real | `items` (`study.decision_records`) | D |
| `gates` | real | `profile, current_gate, gates[], records` | D (W4.08 adds RIDs) |
| `analyses` | real | `last_runs` {analysis: run} | X |
| `modes` | real | `modes, transitions, members, findings, energy` | H |
| `data_budget` | **stub** | `daily, stores, hk` | H (W3.02/W3.05) |
| `links` | partial | `design_case` (`requirements.link`), `items` (named cases from W4.04) | D |
| `contacts` | **stub** | `stations, union` | H (W4.05) |
| `licensing` | **stub** | `applicant, assignments, filings` | L (W5.01/W5.03/W5.06) |
| `ait` | **stub** | `models, tests` | A (W8a) |
| `schedule` | **stub** | `milestones, work_packages, long_lead` | A (W11a) |
| `cdr` | real (W4.01) | `dataset, rows` {kind: rows}, `counts, groups, checks, summary, budget` (CDR model) | X (model: H) |
| `functions` | real (W4.01) | `items` (tree order, `depth`, `allocated_to`), `counts` | X |
| `electrical` | real (W4.07) | `rails, lines, buses, nodes` (names resolved), `ports` {total, by_kind}, `exchange_items` (with `interface_ids`), `counts` | X (model: electrical tab, exchange items) |

The contract for a collector:

- It returns a dict, never `None`. Lists go under `items`.
- An empty study gives the empty shape, not an error.
- A stub returns `{"status": "not_implemented", "owner", "work_package", ...empty shape}`.
  Generators show it as an open item and never crash on it.
- It must not write anything.
- It may read earlier sections from `ctx.sections` and share expensive loads in `ctx.cache`.
  The roll-up is cached as `ctx.cache["rollup"]` (the `RollUp` object).
- A collector that raises does not break the export. Its section falls back to `empty()` and the
  error goes to `StudyExport.errors`.
- A new section needs a name in `SECTIONS`, a field in `StudyExport` (both in `__init__.py`, owner
  X: ask X) and its module.

### 3.1 Review packs and how other work packages light up in them (W4.02)

`POST /api/exports/docs/{id}?review=<gate>` builds the pack of one gate from `collect()`:
`spacecdf_agents/exporters/docs/pack_catalog.py` (products and maturity per gate, the document
list), `study_pack.py` (the review data package, Word + Markdown), `master_budget.py` (the
workbook). `GET /api/studies/{id}/review-packs` lists the packs of the study's profile plus QR,
AR and FRR.

A document another agent writes is a `hook:<module>` in the catalogue. It appears in the pack as
soon as `spacecdf_server/services/docx/<module>.py` defines

```python
def pack_docx(sx: StudyExport, *, gate: str, lang: str) -> bytes | None   # may be async
```

Until then the export core serves it from `services/docx/pack_hooks.py` (`HOOKS`, built from the owner's generator or section: trade-off report, previous review report, AIT programme, schedule, licensing status, TM/TC/FDIR/AOCS tables); the owner's `pack_docx` wins as soon as it exists. A hook that has no data returns `None` and the index lists the document as missing with its owner. Hooks expected: `trades` (D, W6),
`review_report` (D, W4.08), `ait` (A, W8a), `schedule` (A, W11a), `licensing` (L, W5.04),
`tmtc` (H, W3.06). The stub sections (`data_budget`, `contacts`, `licensing`, `ait`, `schedule`)
are already read by the package and the workbook (shapes as in the table above): fill them and
the open items close by themselves.

## 4. One roll-up: `S/services/rollup.py` (W0.3)

```python
from spacecdf_server.services import rollup
ru = await rollup.compute(study_id, gate=None)   # gate defaults to the gate the study prepares for
ru.mass.cbe_kg, ru.mass.with_maturity_kg, ru.mass.with_system_margin_kg, ru.mass.ladder["pdr"]
ru.mass.harness_kg, ru.mass.total_dry_kg, ru.mass.limit_kg, ru.mass.limit_source
ru.power.sum_on_power_w, ru.power.orbit_average_w, ru.power.orbit_average_with_margin_w
ru.form_factor, ru.form_factor_source            # "kb:<id>" | "element:<id>" | "design" | "mass_estimate" | "unknown"
rollup.rollup_elements(elements, gate=..., orbit_average_w=...)   # pure; for unit tests and tools
```

`GET /api/studies/{id}/rollup?gate=` returns `as_dict()`.

Rules:

- **Leaves only.** The most detailed level that has a value wins (`rule_inputs.leaves_with`), so a
  subsystem or system estimate and its components are never both counted.
- **Space hardware only.** Ground, operations and user segments, modes, software and
  mission/segment nodes are left out. Each unit counts `mass_kg × quantity`.
- **Maturity margin** per unit, from `margin_policy`:
  - category from `performance.maturity_category`, else from TRL/KB;
  - A or B: 5 %, C: 10 %, D: 20 %.
- **System margin by gate** (ladder in `configs/margin_policy.yaml`): MDR and PRR 20 %, SRR and PDR
  15 %, CDR 10 %.
  - `with_system_margin_kg = with_maturity_kg × (1 + margin)`. This is the figure the plan quotes,
    for example 4.98 kg.
  - `total_dry_kg` adds the 5 % harness first, as MP-MASS-01 does.
- **Orbit average** is the *nominal* load of the operational mix. It comes from the Modes energy
  balance and uses the per-mode `power_cbe_w` weighted by `orbit_fraction`.
  - That mix holds modes of kind nominal, imaging and downlink only.
  - The energy balance's own `orbit_average_load_w` already includes the maturity and system
    margins. Do not quote it as the nominal value.
- **Form factor** comes from `rule_inputs.form_factor`: a structure KB part, then
  `structure.form_factor_u`, then an element's `performance.form_factor`. When none is set, the
  mass-based guess is used and flagged `mass_estimate`.
- **Already switched to the roll-up:** Launch ICD, RSSSA, Deorbit and Thermal (the mass, form-factor
  and power part of W1.09d). On the EOSAT-1 seed the form factor is now 6U, from the 6U structure;
  before, a mass-based guess gave 2U. W1.08 (Budget tab and PRR-EC-05) and W4.01/W4.03 (packs and
  master budget) must quote `rollup` too. Do not write another sum.

## 5. Fixture: `tests/fixtures/nfi/` (W0.4)

The files are copied unchanged from the frozen Northern Fire and Ice teaching baseline:

- `NUMBERS.yaml` (the source of truth);
- `mission.yaml`, `equipment.yaml`, `modes.yaml`;
- `requirements.yaml`: v2 since wave 3 step 0: 302 rows (mission 68, segment 40, system 67,
  subsystem 115, interface 12), plus 5 objectives and 12 stakeholder needs (v1: 216 + 5 + 6);
- v2 additions: `functions.yaml`, `budgets.yaml`, `stakeholders.yaml`, `vv_plan.yaml`;
  `NUMBERS.yaml`, `risks.yaml` (37 risks) and `trades.yaml` are the v2 copies;
- `hk_sids.yaml`, `risks.yaml`, `trades.yaml`, `ground_stations.yaml`;
- `logbook.yaml`, `roundtrip_checklist.yaml`.

The plan's `requirements_full.yaml` is called `requirements.yaml` here.

```python
from tests.fixtures.nfi import seed_nfi, load, STAGES
s = await seed_nfi(client, "S2")       # client: the httpx AsyncClient of tests/test_api/conftest.py
s.study_id, s.elements["EPS"], s.requirements["MIS-SCI-01"], s.modes["imaging"], s.report
n = load("NUMBERS")                    # assert against these values, never retype them
```

Each stage adds to the one before:

| Stage | Contents |
|---|---|
| S0 | Study created solo, with the mission definition and the mission need (success criteria, constraints) |
| S1 | Product tree; 4 generic ground stations (Ottawa, Yellowknife, Iqaluit, Inuvik); mission control; launch segment; Science Segment, Operations and Harness; OBJ-* rows and the bulk import of the whole requirement baseline (W2.04) |
| S2 | Equipment, with maturity categories; links, electrical and data accepted; modes patched to `modes.yaml`, with shares of orbit, the power matrix, the extra transitions and the disposal mode; ConOps phases; the 8 named link cases, with the rural 1 W downlink and the 600 K uplink applied as design cases (`requirements.link`, UHF) |
| S3 | The remaining requirements and the risk register; IF rows linked to their interfaces; the 8 trades (Pugh, decisions recorded); the MDR review with its RIDs |
| S4 | CDR model accepted; stack placed and approved; V&V, ground-segment, physics and mission-simulation runs; AIT model philosophy and test matrix (W8a); schedule and cost settings (W11a); HK SIDs from `hk_sids.yaml` (W3) |

To run the fixture tests: `pytest tests/fixtures/nfi`. Use `-k seed` for the seed tests. To seed a
running server (the dry run), see `docs/dev/DRY_RUN.md`: `python -m tests.fixtures.nfi --url … --stage S4`.
Measured times (wave 2, after the KB/YAML caches):

- S4 builds in about 14 s on a quiet two-core machine (about 11 s of CPU; it was about 32 s and
  30 s of CPU before). With six test runs on two cores the wall clock stretches to 70–100 s, so
  `test_seed.py` holds the CPU time under 30 s and the wall clock under 60 s only when the load per
  core is at most 1. 0 errors and 0 `403`s.
- The S2 roll-up gave 3.871 / 4.147 / 4.976 kg on v1. On v2 (wave 3) it gives 3.871 / 4.172 /
  5.006 kg and 4.168 / 4.562 / 5.474 W (`budgets.yaml`: 4.555 / 5.466 W; see §9.9), and 3U.

Each work package extends the seed for its model, in `seed.py`, in its own stage step. Add to the
end of a step and never reorder earlier calls. Each package also adds its acceptance test as
`tests/fixtures/nfi/test_<wp>.py` or in its own test folder. What wave 1 delivered, and what is
still missing:

| Item | Status | By |
|---|---|---|
| `stakeholder`/`segment`/`interface` levels | done (rows carry their own level) | R: W2.01 |
| Extra parents and objectives, priority, category, unit, source | done | R: W2.02, W2.03 |
| Bulk import (`POST /studies/{id}/requirements/import`) | done: S1 imports the baseline in one call | R: W2.04 |
| Science Segment, Operations and Harness elements, so every row can be allocated | done (S1) | R: W2.09 |
| Interface requirements per subsystem boundary (`IR-*`), IF rows linked | done (S3); the store holds 216 + 5 + 6 rows plus the generated `IR-*` rows, so count from the store, not from the YAML | R: W2.05–W2.07 |
| HK SIDs from `hk_sids.yaml` | done (S4) | H: W3 |
| Trades from `trades.yaml` | done (S3) | D: W6 |
| Link cases | done (S2), design cases applied | D: W4.04 |
| MDR review and RIDs | done (S3); MDR not passed yet (MDR-EC-07 needs a design-loop run) | D: W4.08 |
| AIT | done (S4) | A: W8a |
| Schedule | done (S4) | A: W11a |
| Licensing (applicant, assignments, filings) | **missing**: the licensing tests seed their own record | L: W5.03 |

Requirement ids are `"<study id>:<code>"`, so several seeded studies can share one database.

Requirement ids are `"<study id>:<code>"`, so several seeded studies can share one database.

**Known tool finding (resolved in wave 1, H: W1.03/W3).** Custom modes with an `orbit_fraction`
now enter the operational mix, so the exploratory Night SWIR mode (1 %) is counted and the orbit
average is 4.17 W, as in `NUMBERS.yaml` (`test_w3_telemetry.py`). `test_seed.py` still allows ±0.1 W.

To refresh the fixture, copy the newer baseline files over these and run `pytest tests/fixtures/nfi`.

## 6. Stale frontend guard (W0.5, wave 2)

`video/c2ovideo/stack.py` `frontend_build_problem()` checks the frontend build. It is stale when:

- `design/frontend/dist/index.html` is missing; or
- any file in `src/`, `index.html`, `package*.json`, `vite.config.ts` or `tsconfig*.json` is newer
  than the build.

Since wave 2, `stack up spacecdf` rebuilds a missing or stale build itself (`vite build` in
`design/frontend`, through its `node_modules`, which may be a link to the main checkout's), so the
server always serves the frontend of the checkout it runs from. It still exits non-zero, before
touching any state, when the build cannot be made (no `node_modules/.bin/vite`, or the build fails)
or when `C2O_VIDEO_NO_BUILD=1`. `C2O_VIDEO_ALLOW_STALE_DIST=1` films an old build on purpose. The
server runs on `C2O_VIDEO_SPACECDF_PYTHON`, else `design/.venv`, else (in a git worktree) the main
checkout's `design/.venv`; `PYTHONPATH` makes it import this checkout's packages. `dist/` is not
tracked by git. See `docs/dev/DRY_RUN.md`.

## 7. Conventions for every wave-1 agent (plan §1 W0 and §3)

1. **New tables** go in `S/db/models_<wp>.py` (precedent: `electrical_models.py`,
   `models_modes.py`), with the additive columns in `S/db/migrate.py`.
   - Every new table is study-owned, so the merged project exporter carries it.
   - Add one round-trip assertion to `tests/test_api/test_project_file.py`.
2. **New FR UI strings** go in `FE/i18n/locales/fr.u_<wp>.json` (precedent: `fr.u_project.json`):
   - R: `u_req`;
   - H: `u_hk`;
   - L: `u_lic`;
   - D: `u_dec`;
   - A: `u_ait`.

   UI text is EN and FR from the start, and `python3 -m tools.i18n check` must report 0 errors.
3. **Shared files are edited by their owner only.** The table below covers the seams above; the
   full split is in plan §3. Other agents ask the owner, or wait for the next wave.
4. **Documents** take their data from `export_context.collect` and their numbers from `rollup`.
5. **Tests** use the nfi fixture and the values in `NUMBERS.yaml`.
6. **Before merge**, these must pass:
   - `pytest` (design suite and package suites);
   - `npx tsc --noEmit -p .`;
   - `vite build`;
   - `tools.i18n check`.
7. **Names.** Call the mission "the Northern Fire and Ice mission" (prefix `nfi`). Never write the
   source proposal's working name, partner or institution names, or people's names in code,
   comments, fixtures or docs.

| Shared seam file | Owner | Others may |
|---|---|---|
| `S/routers/exports/__init__.py` (`FAMILIES`) | X | ask X for one appended line |
| `S/services/docx/__init__.py` (`DOCX_GENERATORS`) | X | not add to it (new docs get routes) |
| `S/services/export_context/__init__.py` (`SECTIONS`, `StudyExport`) | X | ask X for a new section |
| `S/services/export_context/sections/<name>.py` | the owner in §3 | not touch |
| `S/services/rollup.py` | A (platform) | ask A; read freely |
| `S/routers/study_export.py` (`/rollup`, `/export-context`) | X | not touch |
| `tests/fixtures/nfi/seed.py` | append-only within a stage, by any agent | not reorder or rename |
| `tests/fixtures/nfi/*.yaml` | baseline (read-only) | refresh only from the frozen baseline |

## 8. Notes for later work packages

- **Drag-sail ownership (PI decision).** The drag sail belongs to the **Propulsion** seat (the
  disposal function), not Structures. This supersedes recommendation P3 of the plan.
  - Today the KB and `configs/mode_rules.yaml` put deorbit devices in the structure domain.
  - The fixture's equipment already puts the sail under the "Disposal (drag sail)" subsystem
    (domain `propulsion`, seat `propulsion_engineer`).
  - The KB domain, the mode rules and the seat mapping are left to a later work package (W1.03 / R's
    import mapping).
  - The Propulsion seat must also be present for studies that need a disposal device with no ΔV.
- **D6 is fixed in the four reports**, through the roll-up. The rest of W1.09d is still open:
  for example, Launch ICD content beyond mass and form factor (W8e).
- **Pre-existing nondeterminism.** `GET /studies/{id}/electrical` lists rows in database order,
  which follows random ids. The simulator export's bus list can therefore change order between
  runs. This was not changed by W0; add `order_by` if a golden test needs it.
- **Golden check of the split.** It was done once, outside the test suite: 50 export calls on the
  EOSAT-1 seed, dumped to text before and after. They were identical apart from random ids and
  timings, and `openapi.json` was byte-identical. A permanent golden-file test would block the
  intended document changes of W1 and W4. `test_w0_seams.py` pins the routes, their modules,
  their order and the operation ids instead.

## 9. Wave 3 seams (step 0)

Step 0 (agent A) landed before the parallel wave of `WAVE3_PLAN.md`, so seven agents (R, H, X,
L, D, A, S) code against the same tables, routes, sections and seed steps. Each stub is marked
`TODO(<owner>, <item>)`; a stub route answers 200 with `status: "not_implemented"` and its owner
on a GET (empty `items`), and 501 on a write. Every stub section returns `status:
"not_implemented"`, `owner` and its empty shape.

### 9.1 What step 0 delivered

- **Fixture on v2** (3.0a). `tests/fixtures/nfi/*.yaml` hold the v2 copies of `NUMBERS`,
  `requirements`, `risks` and `trades`, plus `functions`, `budgets`, `stakeholders` and
  `vv_plan`. The other v1 files stay. The seed imports by `level`, lays the maturity classes of
  `budgets.yaml` (`mass.items`, `power.units`) over the equipment by item name (mass:
  `performance.maturity_category`; power: the new `performance.power_maturity_category`), and
  sets the study's 20 % hold through PDR. `ELEMENT_IDS` (in `seed.py`) maps the v2 element ids
  to the tool's element names.
- **Recording seed.** `seed_nfi(client, stage, recording=True)` and `python -m tests.fixtures.nfi
  --recording` skip `_s4_licensing` (PI ruling: the Licensing tab is filled on camera).
  `seed.recording` is there for the agents' own steps: `_s2_allocations` and `_s3_negotiations`
  should leave their scenes empty when it is set. Tests and the example project use the full seed.
- **Requirement columns** (3.0b): `acceptance`, `verification_model`, `verification_event`,
  `budget_ref`, `open_item_note`, and the code lists `function_codes` and `allocation_codes`
  (JSON). They go through POST/PATCH, the bulk import (`function` and `allocation` of the v2
  rows) and the ReqIF adapter (lists comma-separated). `element_id` is still resolved from
  `subsystem`, and the first allocation code stays separate until 3.R1. Stages `PRR` and `SRR`
  joined `VERIFICATION_STAGES` (one v2 row each).
- **Roll-up on v2** (3.0c). Each unit's power maturity margin is applied before the system
  margin: `power.orbit_average_with_maturity_w` is new, and `orbit_average_with_margin_w` is now
  based on it (v1 applied the system margin to the nominal figure). A per-study hold lives in
  `study.margin_policy.study_override` = `{percent, through_gate, resources, rationale}`. Use
  `GET/PUT /api/studies/{id}/margin-policy` to read or set it; limits are in
  `configs/margin_policy.yaml` `study_override`. The roll-up reports `system_margin_percent`
  (what is applied), `ladder_percent`, `system_margin_source` (`ladder` | `study_hold`) and
  `margin_hold`. The ladder (`mass.ladder`) keeps the textbook values. A hold only raises the
  margin, and it ends after `through_gate`.
- **Contracts** (3.0d): the tables, routes, sections, `key_numbers` and `/phase` listed below.
- **Risk register fields**: `residual_likelihood`, `residual_consequence` (1–5 or null),
  `residual_rpn` and `owner_seat`, in the study's risk JSON (no column needed). D fills them (3.D6).

### 9.2 Ownership in wave 3 (plan §3.2, plus the PI addendum)

| Agent | Items | Owns exclusively in this wave |
|---|---|---|
| **R** requirements | 3.R1–3.R5, **3.R6** ICD issue control (addendum) | the requirement files of waves 1–2 (`C/models/requirement.py`, RequirementRow, `requirement_repo.py`, `relation_repo.py`, `routers/{requirements,relations,interface_requirements,product_tree}.py`, `services/{requirement_engine,requirement_import,requirement_queries,interface_requirements,gate_evaluator}.py`, `CF/{requirement_rules,interface_requirement_templates,gate_exit_criteria}.yaml`, `AG/exporters/reqif/*`, `FE/workbench/{RequirementsPanel,RequirementsTable,MissionWizard}.tsx`, `FE/components/ICDTable.tsx`, `fr.u_req.json`); new: `S/routers/functions.py`, `S/db/function_repo.py`, `FE/components/FunctionTree.tsx`, `S/services/{allocation_requirements,threshold_binding}.py`, **`S/db/models_icd.py`, `S/routers/icd_issues.py`, section `icds.py`** |
| **H** telemetry, modes, data | 3.H1–3.H6 | as in waves 1–2 (`mode_model.py`, `data_budget.py`, `cdr_*.py`, `ground_closure.py`, `ground_scheduler.py`, `routers/{modes,cdr,analyses_ground}.py`, `AG/tier1/{data,link}.py`, `FE/cdr/*`, `FE/modes/*`, `FE/components/DataBudget.tsx`, `fr.u_hk.json`); new: `AG/tier2/conflicts.py`, `S/routers/thermal.py`, `S/services/orbit_season.py`, `S/{routers,services}/sensitivity.py`, `FE/components/SensitivityView.tsx`, `S/db/models_negotiation.py`, `S/{routers,services}/negotiations.py`, `FE/workbench/NegotiationPanel.tsx`, section `negotiations.py`, `fr.u_neg.json` |
| **X** exports | 3.X1–3.X2, **3.X3** SEMP generator (addendum) | as in waves 1–2 (`S/routers/exports/*` families, `S/services/docx/{mrd,ts,ird,semp,rmp,_common,pack_hooks}.py`, `S/services/export_context/__init__.py`, `AG/exporters/docs/*`, `FE/workbench/ExportPanel.tsx`); new: `S/services/diagrams/__init__.py` (KINDS), `S/services/diagrams/b_se.py`, `FE/diagrams/*`, **section `semp.py`** |
| **L** licensing, disposal, payload, changes, impact | 3.L1–3.L7, **3.L8** debris assessment (addendum) | as in waves 1–2 (`C/physics/debris.py`, `services/{regulatory,spectrum,licensing,licensing_docs}.py`, `routers/licensing.py`, `routers/exports/{deorbit,regulatory,rsssa}.py`, `FE/workbench/{LicensingPanel,BlocksPanel}.tsx`, `fr.u_lic.json`); new: `C/physics/payload_sizing.py`, `ChangeProposalRow` in `S/db/models_changes.py`, `S/routers/changes.py`, `FE/workbench/ChangesPanel.tsx`, section `changes.py`, `S/services/{impact_preview,key_numbers}.py`, `S/routers/impact.py`, `FE/components/ImpactPreview.tsx`, **`S/db/models_debris.py`, `S/routers/debris_assessment.py`, section `debris.py`** |
| **D** decide, gates, ConOps, risks | 3.D1–3.D6, **3.D7** change-control flow (addendum) | as in waves 1–2 (`routers/{gates,trades,link_budgets,conops}.py`, `services/{gate_reviews,mission_definition,trades}.py`, `S/seats/*`, `services/docx/{conops,trades,review_report}.py`, `services/diagrams/b_conops.py`, `FE/workbench/{DecisionPanel,VVPanel,ConopsPhases,GateReviewRecord}.tsx`, `FE/components/{LinkBudgetTool,MissionDefinitionEditor,MissionNeedCard}.tsx`, `FE/seats/*`, `fr.u_dec.json`); new: `CF/gate_profiles.yaml`, `FE/workbench/PhasePanel.tsx`, `OpenItemRow` in `models_changes.py`, `S/routers/open_items.py`, `S/routers/analyses_common.py`, **`ChangeApprovalRow` in `models_changes.py`, `S/routers/change_control.py`, section `change_control.py`** |
| **A** platform, design loop | 3.A1–3.A4, **3.A5** reliability + FMEA, **3.A6** thermal nodal model, **3.A7** cost pricing (addendum); step 0, 3.F2 | as in waves 1–2 (`analysis_context.py`, `rollup.py`, `routers/{elements,ait,schedule}.py`, `services/{ait,schedule,cost_engine,bom_generator,readiness}.py`, `S/db/{element_repo,models_ait,models_schedule}.py`, `services/docx/{vp,ait,bom}.py`, `FE/workbench/{BudgetPanel,AitPanel,ProjectPanel}.tsx`, KB data, `fr.u_ait.json`); new: `S/db/models_alloc.py`, section `allocations.py`, `S/routers/design.py`, `AG/tier1/{orbit,power,mass}.py`, `AG/tier2/{cost,reliability}.py`, the app router list, `S/routers/_wave3_stub.py`, **`S/db/{models_reliability,models_thermal,models_cost}.py`, `S/routers/{reliability,thermal_model}.py`, sections `reliability.py`, `thermal_model.py`, `cost.py`** |
| **S** SE integration | 3.S1–3.S6 | `CF/se_protocol.yaml`, `S/services/{se_protocol,se_deliverables}.py`, `S/routers/{se_phase,moes,validation,assumptions}.py`, `S/db/models_se.py`, `C/models/mission_need.py`, `FE/components/StakeholderEditor.tsx`, `FE/workbench/{ValidationPanel,GuidancePanel}.tsx`, sections `{stakeholders,validation,assumptions,se_phase}.py`, `fr.u_se.json`, `tools/se_paraphrase_check.py`, `tests/test_se/*` |

**Step-0 decision: the thermal model goes to A (3.A6), not H.** H is the critical path at 15.5 pd.
A thermal nodal model with hot and cold cases (about 4 pd) would take H to about 19.5 pd. A has
12 pd in the plan, plus step 0 and 3.F2, and already owns the design loop and the KB limits.

The split between them:

- H keeps 3.H4. `S/services/orbit_season.py` proposes β, the eclipse range and the hot and cold
  β cases. H exposes `orbit_season.thermal_cases(study_id)`.
- A's model (`routers/thermal_model.py`, `thermal_cases.source = "orbit_season"`) reads those
  cases. It does not compute its own β.
- The legacy single-node `/api/thermal/*` routes stay H's.

**Cost.** A owns the cost engine and the pricing (3.A7: labour, test campaigns, reserve, launch
provided). D owns only how the cost criterion shows at MDR and PRR. R wires MDR-EC-08 and PRR-EC-11
to `cost_engine`.

### 9.3 Tables (all study-owned; project file carries them; one-row and empty round trip in `tests/test_api/test_project_file.py`)

| Table | Module | Owner | Item |
|---|---|---|---|
| `allocation_ledger` | `models_alloc.py` | A | 3.A2 |
| `se_moes`, `se_validation_activities`, `se_need_validation`, `se_assumptions` | `models_se.py` | S | 3.S3, 3.S5, 3.S6 |
| `change_proposals` | `models_changes.py` (`ChangeProposalRow`) | L | 3.L4 |
| `open_items` | `models_changes.py` (`OpenItemRow`) | D | 3.D4 |
| `change_approvals` | `models_changes.py` (`ChangeApprovalRow`) | D | 3.D7 |
| `negotiation_records` | `models_negotiation.py` | H | 3.H6 |
| `icd_issues` | `models_icd.py` | R | 3.R6 |
| `reliability_blocks`, `fmea_rows` | `models_reliability.py` | A | 3.A5 |
| `thermal_nodes`, `thermal_couplings`, `thermal_cases` | `models_thermal.py` | A | 3.A6 |
| `debris_assessments` | `models_debris.py` | L | 3.L8 |
| `cost_items` | `models_cost.py` | A | 3.A7 |

`db/migrate.py` lists them in `WAVE3_TABLES`. New columns on existing tables are added
automatically by `_upgrade_sync`. After step 0 the file is append-only: one block per agent at
the end. Every row has `data_json`; prefer it to a new column.

### 9.4 Routes (registered once in `S/app.py`; no edits to the list during the wave)

| Router | Routes (under `/api/studies/{study_id}`) | Owner |
|---|---|---|
| `se_phase.py` | `GET /phase` (stub contract, below) | S 3.S1 |
| `moes.py` | `GET/POST /moes`, `PATCH/DELETE /moes/{id}`, `POST /stakeholders/import` | S 3.S3 |
| `validation.py` | `GET/POST /validation/activities`, `PATCH …/{id}`, `POST /validation/propose`, `POST /validation/import`, `GET /validation/need-validation`, `GET /validation/coverage` | S 3.S5 |
| `assumptions.py` | `GET/POST /assumptions`, `PATCH /assumptions/{id}`, `POST /assumptions/import` | S 3.S6 |
| `negotiations.py` | `GET/POST /negotiations`, `GET/PATCH /negotiations/{id}`, `POST …/{id}/signoff`, `POST …/{id}/reopen` | H 3.H6 |
| `sensitivity.py` | `GET /sensitivity?parameter=`, `GET /sensitivity/altitude` | H 3.H5 |
| `changes.py` | `GET/POST /changes`, `PATCH /changes/{id}`, `POST /changes/import`, `POST /changes/from-trade/{trade_id}` | L 3.L4 |
| `impact.py` | `GET /key-numbers` (real), `POST /impact/preview` | L 3.L6 |
| `open_items.py` | `GET /open-items?blocks_gate=`, `POST /open-items`, `PATCH /open-items/{id}`, `POST /open-items/import` | D 3.D4 |
| `elements.py` | `GET/PUT /margin-policy` (real); `GET/POST /allocation-ledger`, `POST /allocation-ledger/import`, `PATCH …/{id}`, `POST …/{id}/agree`, `POST …/{id}/dispute` | A 3.0c, 3.A2 |
| `icd_issues.py` | `GET /icds`, `POST /icds/{icd_ref}/issue`, `POST /icds/{icd_ref}/signoff`, `GET /icds/{icd_ref}/history` | R 3.R6 |
| `reliability.py` | `GET /reliability`, `POST /reliability/run`, `GET/POST /fmea`, `POST /fmea/propose`, `PATCH /fmea/{id}` | A 3.A5 |
| `thermal_model.py` | `GET /thermal-model`, `POST /thermal-model/propose`, `POST /thermal-model/nodes`, `PATCH …/nodes/{id}`, `POST /thermal-model/run` | A 3.A6 |
| `debris_assessment.py` | `GET /debris-assessment`, `POST /debris-assessment/run`, `POST /debris-assessment/accept` | L 3.L8 |
| `change_control.py` | `GET /changes/{id}/control`, `POST …/control/start`, `POST …/control/agree`, `POST …/control/decide` | D 3.D7 |
| `schedule.py` | `GET/POST /cost/items`, `POST /cost/price` | A 3.A7 |
| (R's own file) `functions.py` | `POST /functions/import` (bulk; R adds it in 3.R1) | R 3.R1 |

The SEMP has no new route. `POST /api/exports/docx/semp` (X) builds it from `collect()`, and the
`semp` section holds the content no other section has.

### 9.5 Export sections (`SECTIONS`; 15 new stubs, each module owned as listed)

`stakeholders` (S), `allocations` (A), `validation` (S), `assumptions` (S), `changes` (L),
`open_items` (D), `negotiations` (H), `se_phase` (S); PI addendum: `semp` (X), `icds` (R),
`reliability` (A), `thermal_model` (A), `debris` (L), `change_control` (D), `cost` (A). Their
empty shapes are in each module's `empty()`; keep the keys when making them real.

### 9.6 Contracts

**`/phase`**: `S/services/se_protocol.py` `phase(study_id, study)` returns
`{study_id, gate, phase, entry[], deliverables[], analysis[], coaching{}}`. On S0 the stub gives
`gate: "mdr"` and `phase: "0"`, plus `status` and `owner` until 3.S1 lands. Item shapes are in
the module docstring.

**`key_numbers`**: `S/services/key_numbers.py`, `async key_numbers(study_id, gate=None)` →
`{key: {value, unit, source, owner_seat}}`. It is filled from the roll-up and the data budget.
The keys are:

- `mass.*`: `cbe_kg`, `with_maturity_kg`, `with_system_margin_kg`, `system_margin_percent`,
  `limit_kg`, `margin_to_limit_kg`;
- `power.*`: `orbit_average_w`, `…_with_maturity_w`, `…_with_margin_w`, `system_margin_percent`;
- `data.*`: `capacity_mb_per_day`, `demand_mb_per_day`, `margin_pct`, `science_delivered_mb_per_day`;
- `contacts.union_min_per_day`.

L owns the file after step 0 and adds keys on request.

**Evidence functions R wires into the gate criteria** (`gate_evaluator.py`):

- S: `se_deliverables.evaluate` and `validation.coverage`;
- A: allocation ledger status, the reliability result (PDR-EC-05) and the cost total (MDR-EC-08,
  PRR-EC-11);
- R: the ICD issue state (PDR-EC-02, SRR);
- L: debris acceptance (SRR);
- A: the thermal model margins (the thermal criteria).

### 9.7 Seed steps (`tests/fixtures/nfi/seed.py`; empty until filled; append-only, never reorder)

| Stage | Step | Owner |
|---|---|---|
| S0 | `_s0_stakeholders` | S |
| S1 | `_s1_functions` (before the requirement import), `_s1_bindings` (after it) | R |
| S2 | `_s2_margin_hold` (done in step 0) | A |
| S2 | `_s2_allocations` (skip when `seed.recording`) | A |
| S2 | `_s2_readiness` | L |
| S2 | `_s2_conops_scenarios` | D |
| S3 | `_s3_risks` (after the risk loop), `_s3_trades`, `_s3_open_items` | D |
| S3 | `_s3_changes` | L |
| S3 | `_s3_validation`, `_s3_assumptions` | S |
| S3 | `_s3_negotiations` (skip when `seed.recording`) | H |
| S4 | `_s4_ait_v2` (after `ait/propose`) | A |
| S4 | `_s4_licensing` (skipped when `seed.recording`) | L |
| S4 | `_s4_negotiations` (last; skipped when `seed.recording`): the S3 records recomputed on the S4 design, the baseline option chosen and signed by every seat | H |

The addendum work (ICD issues, reliability, thermal model, debris assessment, change control,
cost) has no seed step. The walkthrough does it on camera. An owner who needs fixture data for
a test adds a step at the end of its stage, in the same pattern, and lists it here.

### 9.8 Seam files in wave 3

| Seam file | Owner | Others |
|---|---|---|
| `S/db/migrate.py` | step 0 | append-only, one block per agent at the end |
| `S/services/export_context/__init__.py` (`SECTIONS`, `StudyExport`) | X (step 0 registered the 15 sections) | ask X |
| `S/services/diagrams/__init__.py` (KINDS) | X | ask X for a line |
| `S/app.py` router list | A (step 0 registered every router) | no edits during the wave |
| `CF/gate_exit_criteria.yaml`, `S/services/gate_evaluator.py` | R | others expose one evidence function each (9.6) |
| `CF/se_protocol.yaml` | S | D, R and A send rows by note |
| `S/services/key_numbers.py` | L | H and S read it |
| `S/db/models_changes.py` | `change_proposals` L; `open_items`, `change_approvals` D | each edits only its own class |
| `tests/fixtures/nfi/seed.py` | each agent fills only its named step | append-only within a step |
| `tests/fixtures/nfi/*.yaml` | frozen baseline (v2 copies) | read-only; refresh only from `/home/claude/nfi/v2/` |
| `tests/test_api/test_project_file.py` | step 0 added `_wave3_rows` and the round trip | owners may replace their row by a route call; data round-trip tests go in their own files |
| Mount lines | the host's owner, one line each on request | `PhasePanel` in `VVPanel` (D); `ValidationPanel` in `AitPanel` (A); `StakeholderEditor` in `MissionNeedCard` (D); `NegotiationPanel`, `ChangesPanel`, the open-item list and the change-control card in `DecisionPanel` (D); `ImpactPreview` in `SeatDrawer.tsx` (D), Modes (H) and Budget (A); `SensitivityView` in `DataBudget` (H) and Decide (D); the ICD issue column in `ICDTable` (R); the reliability, FMEA and thermal-model views in `VVPanel`/`AitPanel` (A, D mounts in `VVPanel`); the debris assessment in `LicensingPanel` (L) |

### 9.9 Deviations from the plan in step 0

- `mode_model._maturity_pct` (H's file) now passes `resource="power"`, so the Modes energy balance
  uses the power maturity class. This is a one-line change.
  - `mode_model.equipment_budgets` (the per-line "every budget" view) still uses one class per
    unit for mass and power. Left to H.
- `margin_policy._category`, `maturity` and `maturity_percent` take a `resource` argument
  (default `mass`; no behaviour change for existing callers).
- `VERIFICATION_STAGES` gained `PRR` and `SRR`.
- `Study.margin_policy` is a new field on the common Study model.
- The radio's RX and TX power units (5 % and 10 %) share one tool element, so it takes the larger
  class (10 %). The S2 roll-up gives 3.871 / 4.172 / 5.006 kg (exact) and 4.168 / 4.562 /
  5.474 W, against 4.168 / 4.555 / 5.466 W in `budgets.yaml` (within the plan's ±0.02 W). A
  separate RX/TX element would close the 0.008 W gap; it is not worth a new element.
- SRR-EC-02 (`gate_evaluator._has_acceptance`) and the SMART "measurable" check
  (`requirement_engine`) accept a non-empty v2 `acceptance` as the pass criterion. Without it,
  two v2 rows (PAY-OPT-06 and THM-PAY-02, whose measure is only in the text) failed the existing
  tests. This is the minimal part of 3.R2; R refines it.
