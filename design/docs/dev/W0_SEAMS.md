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
| `requirements` | real | `items` (level, then code order; `generated_interface` flag for `IR-*`), `counts` | X (fields: R) |
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

Until then the pack index lists it as missing with its owner. Hooks expected: `trades` (D, W6),
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
- `requirements.yaml`: 216 rows, plus 5 objectives;
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
| S0 | Study created solo, with the mission definition and the mission need |
| S1 | Product tree; 4 generic ground stations (Ottawa, Yellowknife, Iqaluit, Inuvik); mission control; launch segment; OBJ-* requirements and the mission-level requirements |
| S2 | Equipment, with maturity categories; links, electrical and data accepted; modes patched to `modes.yaml`, with shares of orbit, the power matrix and the extra transitions |
| S3 | All 216 requirements and the risk register |
| S4 | CDR model accepted; stack placed and approved; V&V, ground-segment, physics and mission-simulation runs |

To run the fixture tests: `pytest tests/fixtures/nfi`. Use `-k seed` for the seed tests. Measured
times:

- S4 builds in about 30 s, with 0 errors and 0 `403`s.
- The S2 roll-up gives 3.871 / 4.147 / 4.976 kg (NUMBERS: 3.87 / 4.15 / 4.98) and 3U.

Each work package extends the seed for its model, in `seed.py`, in its own stage step. Add to the
end of a step and never reorder earlier calls. Each package also adds its acceptance test as
`tests/fixtures/nfi/test_<wp>.py` or in its own test folder. What is still missing, and who adds
it:

| Missing today | Added by |
|---|---|
| `stakeholder`/`segment`/`interface` levels (rows are posted with `tool_level`) | R: W2.01 |
| Extra parents and objectives, priority, category, unit, source | R: W2.02, W2.03 |
| Bulk import: the seed creates requirements one by one today | R: W2.04 |
| Science Segment and Harness elements, so every row can be allocated | R: W2.09 |
| HK SIDs from `hk_sids.yaml` | H: W3 |
| Trades from `trades.yaml` | D: W6 |
| Link cases | D: W4.04 |
| Licensing | L: W5.03 |
| AIT | A: W8a |
| Schedule | A: W11a |

Requirement ids are `"<study id>:<code>"`, so several seeded studies can share one database.

**Known tool finding.** The Modes energy mix leaves out custom modes, so the exploratory Night SWIR
mode (1 %) is not counted. The tool gives an orbit average of about 4.09 W, against 4.17 W in
`NUMBERS.yaml`. The fixture test allows ±0.1 W. H decides whether custom modes with an
`orbit_fraction` enter the mix (W1.03/W3).

To refresh the fixture, copy the newer baseline files over these and run `pytest tests/fixtures/nfi`.

## 6. Stale frontend guard (W0.5)

`video/c2ovideo/stack.py` `frontend_build_problem()` checks the frontend build. `stack up spacecdf`
exits non-zero, before touching any state, when:

- `design/frontend/dist/index.html` is missing; or
- any file in `src/`, `index.html`, `package*.json`, `vite.config.ts` or `tsconfig*.json` is newer
  than the build.

The message names the newest file. `C2O_VIDEO_ALLOW_STALE_DIST=1` films an old build on purpose.
`dist/` is not tracked by git: rebuild it with `cd design/frontend && npm run build` in every
checkout that films.

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
