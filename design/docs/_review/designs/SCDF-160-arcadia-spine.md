# SCDF-160 — Arcadia Spine (delta edition): design document

**Status:** accepted for build (Sept 2026)
**Scope:** turn the existing SpaceCDF "data spine" into an Arcadia-shaped, ECSS-E-TM-10-25-shaped model with Capella / 10-25 / ReqIF / SysML v2 as exchange adapters. Keeps SpaceCDF MIT; all new dependencies Apache-2.0/MIT/BSD.
**Binding for:** agents building SCDF-160..168. Deviations require an ADR in `docs/_review/adr/`.

---

## 0. Where we start (verified against `master` @ 4b9d4b4)

Already present — DO NOT re-create:

| Concept (Arcadia / 10-25) | Already in SpaceCDF | File |
|---|---|---|
| Physical component tree (PA / EPBS) | `DesignElementRow` (mission→segment→system→subsystem→component; `element_type`, `subsystem_domain`, `parent_id`, KB link, mass/power/cost columns, `performance_json`, diagram xy, `version`, soft-delete) | `packages/spacecdf-server/src/spacecdf_server/db/models.py:200` |
| Component exchange / physical link | `ElementInterfaceRow` (typed electrical/data/rf/mechanical/thermal/optical, from/to element, `properties_json`) | `db/models.py:272` |
| Modes & states (partial) | `ModeElementRow` + elements of `element_type='mode'` | `db/models.py:300` |
| Budget allocation | `BudgetAllocationRow` | `db/models.py:314` |
| Requirements hierarchy | `RequirementRow` (SPINE_SPEC §6.1: level, parent, threshold, V-method, `element_id`) | `db/models.py:122` |
| Reactive spine | `services/change_events.py`, `dirty_set.py`, `compliance_tracker.py`, `reconvergence.py` | services/ |
| Element ↔ agent parameter bridge | `services/element_projection.py` (element tree ⇄ flat DesignState) | services/ |
| Functions (pydantic only, in study JSON) | `spacecdf_common/models/functions.py::Function` — `allocated_to` is a **domain string**, not an element | common/models |
| Legacy MBSE export | `spacecdf_agents/exporters/mbse/generator.py` ("10-25-like" JSON) | agents/exporters |
| Element API | `routers/elements.py` (CRUD, tree, allocations, interfaces, modes, populate-subsystems) | routers/ |

Conventions to copy: string ids, `study_id` FK, `version` optimistic lock, `deleted_at` soft delete, `_utcnow` timestamps, dict-based repo functions in `db/element_repo.py`, in-memory cache + write-through as `routers/elements.py` does.

## 1. The delta (what this build adds)

### 1.1 Functions as persisted, allocatable elements (Arcadia `fa` + allocation)
- `FunctionRow` (`functions` table): `id, study_id, parent_id, name, description, layer ('OA'|'SA'|'LA'|'PA', default 'SA'), function_type, level, is_leaf, position_responsible, external_id, external_ids_json, version, deleted_at, created_at, updated_at`.
- `FunctionPortRow` (`function_ports`): `id, function_id, name, direction ('in'|'out'), exchange_item_ids_json`.
- `FunctionAllocationRow` (`function_allocations`): `id, study_id, function_id, element_id, layer` — unique per (function, layer).
- `FunctionalExchangeRow` (`functional_exchanges`): `id, study_id, name, from_port_id, to_port_id, exchange_item_ids_json, realized_by_interface_id (FK element_interfaces, nullable), external_id, deleted_at`.
- `RealizationRow` (`realizations`): `id, study_id, source_kind ('function'|'element'), source_id, target_kind, target_id` — SA→LA→PA function realizations and LA→PA element realizations.
- Migration service: `services/function_migration.py` imports `study.functional_decomposition.functions[]` into `FunctionRow` (layer=SA), and each `allocated_to` domain string into a `FunctionAllocationRow` to the study's matching subsystem element (via `element_projection.DOMAIN_SUBSYSTEM_MAP` + `subsystem_domain`). Idempotent (keyed on legacy function id stored in `external_ids_json['legacy']`). Study JSON remains readable; rows are the truth; `lifecycle.py` call sites that read `study.functional_decomposition` are switched to a helper `get_functions(study_id)` that prefers rows.

### 1.2 Exchange items — what flows over an interface (Arcadia `information` → ICD)
- `ExchangeItemRow` (`exchange_items`): `id, study_id, name, kind ('data'|'power'|'rf'|'thermal'|'mechanical'|'optical'|'fluid'), properties_json (rate_bps, voltage_v, current_a, freq_hz, protocol, connector…), description, external_id, external_ids_json, deleted_at, timestamps`.
- New column `ElementInterfaceRow.exchange_item_ids_json` (JSON list). ICD = projection interface × exchange items × properties.

### 1.3 Layers
- New column `DesignElementRow.layer` (String(4), default `'PA'`; set `'LA'` where `element_type='logical'`). Realizations (1.1) link LA↔PA.

### 1.4 Typed requirement relations (Capella Requirements VP / ReqIF SPEC-RELATION)
- `RequirementRelationRow` (`requirement_relations`): `id, study_id, kind ('satisfies'|'verifies'|'refines'|'derives'|'traces'|'allocates'), source_kind ('requirement'|'element'|'function'|'interface'|'parameter'|'test'), source_id, target_kind, target_id, rationale, external_id, created_at`.
- New columns `RequirementRow.external_id`, `RequirementRow.external_ids_json`.
- `compliance_tracker`: when a requirement is violated, also flag entities linked by `satisfies` (element/function ids in the delta payload). Traceability endpoint walks objectives → MR → SR → SSR → element/function → verification.

### 1.5 Typed parameters + equations (10-25 Annex A shapes + Virtual Satellite `Ref:`/`Calc:`)
- `ParameterDefinitionRow` (`parameter_definitions`): `id, name ('mass_kg','power_avg_w','data_rate_bps'…), quantity_kind, unit, scale, description, is_well_known (bool)`. Seeded from `packages/spacecdf-kb/.../data/reference_data_library.json` (units + quantity kinds; our own data).
- `ElementParameterRow` (`element_parameters`): `id, study_id, element_id, definition_id, owner_domain, manual_value, computed_value, reference_value, value_switch ('manual'|'computed'|'reference', default 'computed'), formula (Text, nullable), formula_kind ('ref'|'calc'|null), option_id (nullable), iteration (int, default 1), version, updated_at`. Unique (element_id, definition_id, iteration).
- Well-known columns on `DesignElementRow` (`mass_kg`, `power_avg_w`, `power_peak_w`, `cost_nre_keur`, `cost_recurring_keur`, `volume_cm3`) stay the fast path; the element repo **mirrors** them into `ElementParameterRow` on write (both directions). New quantities live only as parameters.
- **Equation engine** `services/equations.py`: `simpleeval` (MIT) with a whitelisted function set (`sqrt, sin, cos, tan, atan2, exp, log, min, max, abs, sum`), a per-study namespace where a name is `el("<element name or id>").<param>` or bare `<param>` for the owning element, plus `children("<param>")` (sum over children) and `budget("<budget_type>")`. `formula_kind='ref'` → evaluate, persist `computed_value`; `'calc'` → evaluate on read only. Dependency graph built from formula references; topological evaluation; cycles reported as errors (never raise into the API). Triggered from `change_events` (kinds `parameter_override`, element edits) via `dirty_set` — no polling. Formula and its evaluated value are returned side by side by the API.
- `Option` deferred (column kept so 10-25 export can name the default option).

## 2. Exchange adapters (`packages/spacecdf-agents/src/spacecdf_agents/exporters/`)

| Adapter | Direction | Library | Notes |
|---|---|---|---|
| `capella/` | export + import | `capellambse>=0.8,<0.9` (Apache-2.0) | Export: build decl YAML from the spine → apply to the vendored empty Capella 7.0 template (`exporters/capella/template/{.project,empty.afm,empty.aird,empty.capella}`, Apache-2.0 from dbinfrago/py-capellambse tests — keep attribution file) → `model.save()` → zip. Mapping: SA functions → `model.sa.root_function.functions`; LA elements → `model.la.root_component.owned_components`; PA elements → `model.pa.root_component.owned_components` (`element_type='software'` → behaviour PC, else node); interfaces → `ComponentExchange` between components' ports; exchange items → `information` `ExchangeItem`s; functional exchanges → `FunctionalExchange` (use `!promise` in decl); requirements → Requirements-VP module (create `CapellaModule` under `oa.requirement_modules` if none) + relations; budgets/parameters → core `PropertyValueGroup` named "SpaceCDF.Budgets" with `FloatPropertyValue`s (PVMT config is absent in the empty template — do not depend on PVMT). Store the Capella UUID for every exported entity in `external_ids_json['capella']` so a re-export uses decl `sync` and does not duplicate. Import: load `.aird` (dir or zip), upsert elements/functions/interfaces/exchange items/requirements by `external_ids_json['capella']` (create when unknown). Verified in this sandbox: `MelodyModel(empty.aird)`, `sa.root_function.functions.create`, `pa.root_component.owned_components.create`, `decl.apply`, `save()` all work. |
| `ecss_10_25/` | export (Annex C.3 zip) + client (Annex C.2) | none (`httpx`) | Pydantic mirror of the needed Annex A classes (classKind strings as CDP4Common uses them): `SiteDirectory`, `SiteReferenceDataLibrary` (with `MeasurementUnit`, `RatioScale`, `SimpleQuantityKind`, `Category`), `DomainOfExpertise` (one per agent domain + "System"), `Person/Participant` minimal, `EngineeringModelSetup`, `EngineeringModel`, `Iteration`, `IterationSetup`, `Option` (single "Baseline"), `ElementDefinition`/`ElementUsage` (tree), `Parameter` + `ParameterValueSet` (`manual`, `computed`, `reference`, `valueSwitch`), `RequirementsSpecification`/`RequirementsGroup`/`Requirement`/`Definition`. C.3 zip layout: `Header.json`, `SiteDirectory.json`, `SiteReferenceDataLibraries/<iid>.json`, `EngineeringModels/<iid>/EngineeringModel.json` + `Iterations/<iid>.json` (JSON arrays of objects each with `iid`, `classKind`, `revisionNumber`) — mirror the public `STARIONGROUP/CDP4-COMET-MODELS` sample layout; state any assumption in the module docstring. C.2 client: `post_iteration(base_url, em_iid, iteration_iid, body={_create,_update,_delete}, auth)`; integration test only when `COMET_URL` is set. Keep `exporters/mbse/generator.py` reachable as `mbse-legacy`. |
| `reqif/` | export + import | `reqif` (strictdoc, Apache-2.0) | Requirements, hierarchy (SPEC-HIERARCHY), attributes (code, text, rationale, verification method), relations (SPEC-RELATION kinds) ↔ ReqIF 1.2. SPEC-OBJECT identifier = `external_id` (generate stable `SCDF-REQ-<id>` on first export). Round-trip test. |
| `sysmlv2/` | export | Jinja2 | Textual SysML v2: `package <Study>`; `part def` per element type, `part` tree with `attribute` values + units; `action def`/`action` from functions with `allocate`; `connection` per interface; `requirement def`/`requirement` with `subject` and `require constraint` from thresholds; `satisfy` from relations. Optional validation by `opensysml` if importable; otherwise a bracket/keyword smoke test. |

## 3. API (new router files; registered in `app.py`)

- `routers/functions.py`: functions CRUD (+ports), functional exchanges CRUD, `POST /functions/{id}/allocate {element_id, layer}`, `GET /studies/{id}/functions/tree`, `POST /studies/{id}/functions/migrate-legacy`, realizations CRUD.
- `routers/exchange_items.py`: CRUD; `PATCH /interfaces/{id}/exchange-items`; `GET /studies/{id}/icd` (rows: interface, from, to, type, exchange item, kind, properties).
- `routers/relations.py`: requirement relations CRUD; `GET /studies/{id}/traceability/tree`; `GET /requirements/{id}/trace`.
- `routers/parameters.py`: definitions list/seed; `GET /elements/{id}/parameters`; `PUT /elements/{id}/parameters/{name}` (`{manual_value | formula, formula_kind, value_switch}`); `POST /studies/{id}/parameters/recompute`; `GET /studies/{id}/parameters/graph` (dependency edges + cycles).
- `routers/exchange.py`: `GET /studies/{id}/export/capella.zip`, `/export/ecss-10-25.zip`, `/export/requirements.reqif`, `/export/model.sysml`; `POST /studies/{id}/import/capella` (multipart zip), `/import/reqif`; `POST /studies/{id}/push/comet` (C.2; 501 unless configured).

All routes async, follow `routers/elements.py` error/response style, broadcast `ChangeEvent`s for mutations.

## 4. Frontend (minimal, editable, in the existing workbench idiom; `frontend/src/components/`)

- `FunctionTree.tsx` — replaces the broken `FunctionTreeView`: tree editor (add/rename/delete, parent move), layer badge, "Allocate to…" element picker, exchanges list; "Migrate legacy functions" button when the study has JSON functions and no rows.
- `ICDTable.tsx` — interface × exchange item table; add/edit exchange items and properties inline; CSV download.
- `TraceabilityTree.tsx` — objective → requirement chain → element/function → verification, status pills from compliance.
- `ParameterPanel.tsx` — for the selected element: name, value (switch manual/computed/reference), unit, **formula shown beside the value**, provenance; inline formula edit with error display; "recompute".
- `ExchangePanel.tsx` — under Exports: download Capella / ECSS-E-TM-10-25 / ReqIF / SysML v2; import drop-zones for Capella zip and ReqIF.
Mount them where `FunctionTreeView`, `InterfaceMatrixView`, `VerificationMatrix`, element detail, and `ExportsPanel` live today (find with grep; keep existing tabs, replace the broken one).

## 5. Non-goals (this build)
Options/variants; diagram layout round-trip into `.aird`; OA-layer UI (schema supports `layer='OA'`); SysML v2 import; hosting a COMET server; PVMT.

## 6. Tests (binding)
- Every new table: repo tests (create/update/soft-delete/list) under `tests/test_repositories/`.
- Migration: legacy `functional_decomposition` JSON → rows with allocations, idempotent.
- Equations: `ref` persists, `calc` doesn't, cycle detection, children-sum, recompute on change_event.
- Capella: export → reload with capellambse → counts/names; export→import→export idempotent; zip contains the four files.
- 10-25: C.3 zip structure; every `Parameter` has a `ParameterValueSet`; JSON round-trips through the pydantic mirror.
- ReqIF: export → parse → import round-trip preserves ids/hierarchy/relations.
- SysML v2: smoke parse.
- Existing suite stays green; fix `pytest-asyncio` config (`[tool.pytest.ini_options] asyncio_mode = "auto"` in root `pyproject.toml`; add `aiosqlite`, `greenlet` to server deps).

## 7. Licences of new runtime deps
`capellambse` Apache-2.0 (+OFL font), `reqif` Apache-2.0, `simpleeval` MIT, `jinja2` BSD, `httpx` BSD. Vendored empty Capella template Apache-2.0 (dbinfrago/py-capellambse). No EPL, no AGPL code enters the repo. SpaceCDF remains MIT.
