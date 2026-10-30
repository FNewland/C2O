# SCDF-160 Arcadia spine — independent verification

**Branch:** `arcadia-spine` (10 build commits + 2 verifier fix commits)
**Date:** 2026-09-09
**Method:** static checks, then a real `uvicorn` server on a throw-away SQLite DB
(`DATABASE_URL=sqlite+aiosqlite:////tmp/e2e/spine.db`) driven only through the public
HTTP API with `httpx`; exports reloaded with `capellambse`, `zipfile`, `json`; a second DB
was created by the `master` app (git worktree) and then opened by this branch.

## 1. Results per step

| Step | What | Result |
|---|---|---|
| 1 | `pytest tests --ignore=tests/test_level_workbench.py` | **PASS** 225 passed / 1 skipped before fixes; **227** after (2 regression tests added) |
| 1 | `npx vite build` | **PASS** (chunk-size warning only) |
| 1 | `npx tsc -b` error count | **PASS** 105 (= pre-existing ceiling) |
| 2 | Study + populate-subsystems + elements | PASS (`populate-subsystems` requires `?parent_element_id=<segment>`; created 19 elements incl. 10 KB equipment) |
| 2 | Requirements MR→SR→SSR with parent links, threshold on `power.eps_mass_kg` | PASS |
| 2 | 2 functions, allocation to subsystem, ports, 1 functional exchange | PASS |
| 2 | Exchange item + attach to interface, ICD JSON + CSV | PASS (populate creates **no** interfaces; one was created by hand) |
| 2 | `satisfies` relation element→requirement | PASS |
| 2 | Formulas `mass_kg * 1.2` (ref), `children("mass_kg")` (ref) on subsystem and system | PASS with caveat — see finding N1 |
| 2 | PATCH component mass → formulas recompute on GET | PASS (children_mass 3.495 → 5.495) |
| 2 | `GET /studies/{id}/traceability/tree` | **FAIL → FIXED** (bug B1) |
| 3 | Capella zip → `capellambse.MelodyModel` reload | PASS: 4 files; SA functions, PA components, `ComponentExchange`, `FunctionalExchange`, `ExchangeItem`, 3 requirements (parents as `Requirements:Folder`), in/out relations, `FloatPropertyValue`s incl. the formula parameters |
| 3 | Capella zip → `import/capella` into a new study | PASS: counts identical (23 el / 2 fn / 1 if / 3 req / 1 xi / 1 fx); re-export of the imported study has identical Capella counts |
| 3 | `export/ecss-10-25.zip` | PASS: 5 files in Annex C.3 layout, JSON arrays parse, 32 `Parameter` each with a `ParameterValueSet`, `Iteration.element` ⊆ ElementDefinition iids, `topElement` valid |
| 3 | ReqIF export → import into new study | PASS for count + hierarchy + level; **thresholds not round-tripped** (finding N2) |
| 3 | `export/model.sysml` | PASS: elements, attributes with units, `action`/`allocate`, `requirement`, `satisfy SR_1 by EPS`; braces balanced |
| 3 | `export/capella/summary`, `push/comet` | PASS (summary counts + cross-layer warning; comet → 501) |
| 4 | Lifecycle endpoints via `_study_functions` on legacy-only and on rows | `requirements/generate`, `traceability/{id}/mass_dry` PASS both ways; `consistency/{id}` **500 → FIXED** (bug B2, pre-existing) |
| 5 | `migrate-legacy` on a study with 14 auto-generated JSON functions | PASS: 14 rows, 6 parent links, 11 allocations to subsystems (payload/aocs/obc/ttc…), legacy ids kept; second call → 0 created / 14 updated, counts unchanged |
| 6 | `master` DB opened by `arcadia-spine` | PASS: 9 tables added, `design_elements.layer`, `element_interfaces.exchange_item_ids_json`, `requirements.external_id(s_json)` added; old study/elements/interfaces readable; ICD, parameters, functions tree, migrate-legacy, Capella and 10-25 exports all work on the old data |
| 7 | Spec review | see §4 |

Extra probes (all PASS): `calc` formulas evaluate on read and persist `computed_value=NULL`;
cycle `x→y→x` reported in the row errors and in `parameters/graph.cycles` without a 500;
simpleeval guards hold for `__import__`, `__class__`, `9**9**9**9`, `"a"*10**9` (all rejected
in ≈10 ms); well-known columns are surfaced with `provenance: column` for elements that never
had a parameter row.

## 2. Bugs found and fixed

**B1 — traceability tree never links requirements to objectives via the API.**
`POST /api/requirements/` (and `PATCH`) built the stored dict from an explicit key list that
did not include `objective_id`; `relations.get_traceability_tree` links objectives via
`req.objective_id` (or `Objective.traced_to_requirements`, which nothing in the API can set).
The existing test passed only because it mutated `Study.mission_need` directly. Repro: create a
study with objectives, POST a requirement with `objective_id`, GET the tree →
`requirements_traced_to_objectives: 0`, requirement listed under `unlinked_requirements`.
Fix: keep `objective_id` on create and update. Also `create_study` swallowed an invalid
`mission_need` silently (→ 0 objectives with no trace); now logs a warning.
Regression test `test_traceability_tree_api_seeded_objective_id` (public API only).
Commit **2eb8342**.

**B2 — `GET /api/lifecycle/consistency/{id}` returned 500 on every study.**
It iterated `study.requirements` (the `MissionRequirements` input model) as if it were the
requirement list → `'tuple' object has no attribute 'id'`. Pre-existing on `master`, but the
SCDF-160 `_study_functions` shim in this handler was therefore unverifiable. Fix: read the
requirements router store for the study. Regression test
`test_lifecycle_consistency_reads_functions_from_rows_and_legacy`. Commit **58493d4**.

## 3. Bugs / gaps found, NOT fixed

**N0 — the reason the frontend agent saw 0 objectives *and* 0 requirements.** Requirements
live only in the in-memory dict `routers/requirements.py::_requirements` (pre-existing
"Phase A" store; the `requirements` table + repo exist but are unused). After a server restart
the traceability tree shows `requirements: 0` while `relations` (persisted) still count — I
reproduced this exactly (`objectives: 2, requirements: 0, relations: 1`). The "0 objectives"
half comes from studies created without a valid `mission_need` (silently dropped, now warned).
Out of SCDF-160 scope, but the tree, `_require_study`, exports and ReqIF import all sit on this
volatile store; a ReqIF/Capella import's requirements vanish on restart too.

**N1 — `mass_kg * 1.2` on a subsystem errors.** Subsystem elements from `populate-subsystems`
have `mass_kg = NULL` (mass is not rolled up into the column), so the bare-name reference
yields `TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'` (reported in
`errors`, no 500). Likewise `children("mass_kg")` on the system element is `0.0` because its
children (subsystems) have no column mass. Users will expect a roll-up; consider treating
`None` well-known columns as `children(...)` sum or documenting `children("children_mass")`.

**N2 — ReqIF round trip loses thresholds.** The exporter emits no threshold attributes and
`reqif/adapter.py:285` hardcodes `threshold_param_path/op/value = None` on import. Repro: export
a requirement with `threshold_param_path=power.eps_mass_kg, <=, 5`, import into a new study,
GET tree → all three `None`. Within the design's §2 attribute list (code, text, rationale,
V-method) so not a contract breach, but the compliance tracker cannot act on imported reqs.

**N3 — `populate-subsystems` creates no interfaces**, so the ICD is empty until interfaces are
added by hand (design §0 lists `generate_standard_interface_matrix` in study JSON; it is not
projected to `ElementInterfaceRow`). Pre-existing.

**N4 — Capella export represents every requirement that has children as
`Requirements:Folder`** (text preserved, so Capella shows them; `capellambse.search("Requirement")`
does not return them — use `search("Requirement", "Requirements:Folder")`). Documented in
`mapping.py:552`; noted so nobody "fixes" the count mismatch the wrong way.

## 4. Spec-compliance notes (SPINE_SPEC §13, design §5)

`SPINE_SPEC.md` is not in the repository (it is referenced from `CAPELLA_ASSESSMENT.md` as living
in the Drive review folder); the four §13 prohibitions named in the verification brief were
checked directly.

- **No new ORM:** all new tables are SQLAlchemy `Base` subclasses in `db/models.py`; dict-based
  repos follow `element_repo.py`. OK.
- **No Redis / new infrastructure:** new runtime deps are `capellambse`, `reqif`, `jinja2`,
  `simpleeval`, `httpx`, `python-multipart`, `aiosqlite`, `greenlet` — all Apache/MIT/BSD;
  `redis` already in the root deps on master, untouched. OK.
- **No parallel selection-effect maps:** none added. OK.
- **Dispatcher:** mutations do **not** go through `ChangeEventDispatcher` — but nothing on
  `master` does either (`dispatch()` has no callers outside its own module); the branch copies
  the `routers/elements.py` convention (write-through + `ws._broadcast_study`) via
  `_arcadia_events.broadcast_mutation`, and deliberately adds no `ChangeKind`s. Design §1.5
  says equations are "triggered from change_events … via dirty_set"; in practice
  `equations.on_change` marks a **private** `DirtySet()` instance, consumes it immediately and
  recomputes synchronously inside the element PATCH / parameter PUT — the dirty set is
  ceremonial, and the WS `parameter_edit` path (DesignState parameters) does not trigger
  equation recompute at all. Not a §13 violation, but it is not the reactive wiring the design
  text describes; flag for the SCDF-161+ reactive work.
- **§5 non-goals:** Options — only the `option_id` column and a single "Baseline" Option in
  the 10-25 export, nothing half-built. `.aird` layout round-trip — not attempted. OA UI — schema
  accepts `layer='OA'`; no OA panel. SysML import — absent. COMET hosting — absent (501).
  PVMT — not referenced anywhere in the Capella adapter. Vendored template carries `.project`
  and `LICENSE.txt` (Apache-2.0 attribution). OK.
- **Tests (§6):** every new table has repo tests; migration idempotence, equations
  (ref/calc/cycle/children/recompute), Capella reload + idempotent re-export, 10-25 structure,
  ReqIF round-trip, SysML smoke, schema upgrade — all present and green. `asyncio_mode=auto`
  set.

## 5. Verdict

**PASS with fixes.** The spine does what the contract says through the real API: functions,
exchange items/ICD, relations, typed parameters with formulas, and all four exchange adapters
round-trip on a fresh DB and on a DB upgraded from `master`. Two defects were found and fixed on
the branch (B1 was the frontend agent's reported symptom; B2 was a pre-existing 500). The
remaining findings (N0–N4) are pre-existing or out of the design's stated scope, with N0
(volatile requirement store) being the one most likely to bite users next.

## 6. Follow-up — N0 resolved (2026-09-09)

Requirements are now persistent, using the same write-through-cache pattern as
`routers/elements.py`. `routers/requirements.py` keeps `_requirements` as the read path
(still importable by relations/exporters/compliance); POST/PATCH/DELETE/derive mirror to the
`requirements` table via `db/requirement_repo.py` (chosen as canonical — dict-based, column-driven
mapping; `repositories/requirement_repo.py` is the Pydantic-model variant and is untouched).
The cache is hydrated by `init_requirement_cache()` in the app lifespan and lazily on first
access (`ensure_requirements_loaded()`, also awaited by the traceability tree/trace endpoints).
`RequirementRow` gained `objective_id` (the router already served it; `ensure_schema_upgrades`
adds the column to existing DBs — verified). `external_id` is now accepted on POST/PATCH and
persisted. The ReqIF importer upserts imported requirements into the table.

Evidence: `tests/test_api/test_requirements_persistence.py` (create/patch/derive/delete, tree,
traceability tree and trace all correct after a simulated restart); full suite 231 passed,
1 skipped (`--ignore=tests/test_level_workbench.py`). Live: uvicorn on a temp DB, POST + PATCH a
requirement, kill, restart — `GET /api/requirements/{id}`, `/tree` and
`/studies/{id}/traceability/tree` all return it with the patched status.

Still volatile (out of this fix): the Capella importer's `_spine.upsert_requirement` writes into
the cache from a sync path and is not mirrored; it should call `db_upsert_requirement` once that
path is made async.
