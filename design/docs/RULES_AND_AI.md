# SpaceCDF: design rules instead of AI

*2 November 2026. Applies to SpaceCDF 2.x (`design/`).*

SpaceCDF makes its baseline design choices with **scripts that apply published
standards and stated engineering defaults**, not with a language model. AI is
**off by default**. It is kept for three optional prose tasks only, and its output
goes through the same rule checks as a student's text.

This document lists every former AI capability, the deterministic engine that now
does the job, and the rules and sources each engine uses.

## 1. How to read a source label

Every rule value in the configuration files names one source. A source is one of
two kinds.

| Label in the UI and API | Meaning |
|---|---|
| A document reference, for example `ESA margin philosophy (SCI) 1.3 R-M1-7`, `CDS rev 14.1 2.3.7` or `ECSS-E-ST-10-02C Rev.1 5.2.2.1` | A **cited standard or guideline** that was read and checked. The clause is given. |
| `C2O default` | A **SpaceCDF choice**: established practice or a teaching choice. It is **not** a quotation of a standard, even when it is close to one. An instructor may change it. |

The API returns `standard_ref` (the string above) and `c2o_default` (true or false)
on every check, so a page can always show which kind it is. `GET /api/rules/catalogue`
lists all sources, with `verified: true` for the documents that were checked.

## 2. Former AI capabilities and what replaced them

The audit of 2 November 2026 found 13 AI capabilities. None was called by the
shipped user interface, and most duplicated an engine that already existed.

| # | Former AI capability (`genai.yaml` key) | Now done by | Rules and sources | Status |
|---|---|---|---|---|
| 1a | `design_advisor`: critique of the mission need | MCR gate criteria (`gate_evaluator.py`, `gate_exit_criteria.yaml`), mission-need validators, the requirement checks below | ECSS-M-ST-10C review objectives; thresholds are C2O defaults | **Rules.** AI kept only for a prose critique of stakeholder text (optional). |
| 1b | `design_advisor`: component recommendation | `fit_gap_analysis.py`, `equipment.search_compatible_equipment`, `equipment_logic.check_interface_compatibility` / `check_rf_compatibility` | KB data; C2O priority order | **Rules** (retired from AI, HTTP 410) |
| 1c | `design_advisor`: ConOps generation | default ConOps (`studies._generate_default_conops`, `conops_executor.py`) | CDS 2.4.4/2.4.5 timers; ECSS-M-ST-10C phases | **Rules** (retired, 410) |
| 1d | `design_advisor`: free questions | none | none | **AI kept** (optional) |
| 2 | `requirements_decomposition` | `requirement_engine.py` (requirement templates from parameters), **new** `requirement_quality.py` | EARS (Mavin et al. 2009); INCOSE GtWR rule subset; C2O word lists | **Rules** for structure and quality. AI kept for **polishing free-text objectives into shall statements**, always checked by `requirement_quality`. |
| 3 | `consistency_checking` | `consistency_engine.py`, Tier 2 conflicts agent, **new** `margin_policy.py`, `cds_checks.py`, `gate_checks.py` | ESA margin philosophy 1.3; CDS rev 14.1; ECSS-M-ST-10C | **Rules** (retired, 410) |
| 4 | `trade_analysis` | `tabular_trade.py` (weights, thresholds, sensitivity), `mission_trade.py`, `orbit_trade.py` | Weighted-sum method; weights set by the team | **Rules** (retired, 410) |
| 5 | `cost_estimation` | `cost_engine.py` | NASA CEH cost-estimating relationships | **Rules** (removed) |
| 6 | `report_narrative` | `did_generator.py`, `semp_generator.py`, `docx_generator.py` templates | ECSS DRD structures | **Templates.** AI kept for **narrative and executive-summary prose** (optional). |
| 7 | `fmea_generation` | `fmeca_closure.py`, **new** `fmeca_library.py` + `configs/failure_modes.yaml` | ECSS-Q-ST-30-02C method; library and scales are C2O defaults | **Rules** (removed) |
| 8 | `cad_scripting` | `physics_closure.place_elements`, `mass_properties.py` | Geometry from the model | **Rules** (removed; a CadQuery box-stack exporter is possible later) |
| 9 | `wiring_generation` | `harness_designer.py`; the interface proposer (`interface_proposer.py`, `configs/interface_rules.yaml`) | ECSS-E-ST-10-24C Annex E natures; C2O default interface matrix | **Rules** (removed) |
| 10 | `fsw_generation` | `exporters/fsw/generator.py`, `mode_manager.py` | Deterministic skeleton | **Rules** (removed) |
| 11 | `aocs_design` | Tier 1 AOCS agent, `physics_closure.run_aocs_closure` | SMAD disturbance-torque equations | **Rules** (removed) |
| 12 | `thermal_setup` | `thermal_network.py`, `thermal_transient.py` | Lumped-node model | **Rules** (removed) |
| 13 | `structural_setup` | `structures.py`, Tier 1 structure agent | Launcher load factors from the KB | **Rules** (removed) |

"Removed" means the capability module and its prompt were deleted from
`packages/spacecdf-ai`. "Retired, 410" means `/api/ai/ask` answers HTTP 410 for that
name and gives the endpoint that replaced it.

## 3. The deterministic engines

All engines are pure functions in `packages/spacecdf-server/src/spacecdf_server/services/`.
They read YAML files in `design/configs/`. The server validates these files at
start-up (`rule_config.py`): an unknown source id, a missing value or a bad regular
expression is logged, shown by `/api/rules/catalogue`, and the rule endpoints refuse
to run on the broken file (HTTP 500 with the reasons).

### 3.1 Margin policy (`margin_policy.py`, `configs/margin_policy.yaml`)

| Rule | Value | Source |
|---|---|---|
| Equipment maturity margin, category A or B (off the shelf) | 5 % | ESA margin philosophy 1.3, R-M1-4 / R-M2-4 (mass), R-P-11..13 (power) |
| Category C (minor modification) | 10 % | same |
| Category D (new design or major modification) | 20 % | same |
| Category from TRL and heritage (TRL ≥ 8 with heritage → A; TRL ≥ 8 → B; TRL ≥ 6 → C; else D; no KB part and no TRL → D) | — | **C2O default** |
| System mass margin | 20 % of nominal dry mass | ESA 1.3, 2.1.1 R-M1-1 |
| Harness | 5 % of nominal dry mass | ESA 1.3, R-M1-7 |
| Propellant residuals | 2 % | ESA 1.3, R-M1-6 |
| Tank volume | +10 % | ESA 1.3, R-M1-10 |
| System power margin | 20 % | ESA 1.3, R-P-3 |
| ΔV, calculated manoeuvres / orbit maintenance / attitude control | 5 % / 100 % / 100 % | ESA 1.3, R-DV-11 / 12 / 13 |
| Which SpaceCDF parameter belongs to which ΔV class | — | **C2O default** |
| On-board RAM | ≤ 50 % used | ESA 1.3, R-SW-1 ("margin ≥ 50 %", read as half the capacity free) |
| Processor peak load | ≤ 50 % | ESA 1.3, R-SW-2 |
| Mass-memory storage margin | 50 % | **C2O default** (mirrors the RAM rule) |
| Heat-rejection margin | 50 % | ESA 1.3, R-T-2 |

The roll-up uses the **most detailed level that has a value**. A subsystem estimate
is replaced by its components as soon as one of them has a mass. Ground-segment
elements are excluded. The mass limit is the CDS limit for the form factor, else the
study mass target.

*Note.* The older `ecss_margin_enforcer.py` (Phase/ECSS page) still uses phase
tables labelled "ECSS-E-HB-10-02A §5.2". That attribution could not be verified;
treat those tables as C2O defaults until it is checked.

### 3.2 CubeSat Design Specification checks (`cds_checks.py`, `configs/cds_rules.yaml`)

Source: Cal Poly CubeSat Design Specification rev 14.1 (2022-02-09).

| Check | Rule | CDS clause |
|---|---|---|
| Mass per form factor | 1U 2.00 kg … 3U 6.00 kg, 6U 12.00 kg, 12U 24.00 kg (typical; the dispenser may differ) | 2.2.10, Table 1 |
| Centre of gravity | inside the Table 2 box (e.g. 3U ±2/±2/±7 cm); checked when every massive unit has a position | 2.2.11, Table 2 |
| Deployment switch | ≥ 1 | 2.3.2 |
| RBF pin | present | 2.3.4 / 2.3.5 |
| RF inhibits | ≥ 3 independent, when the design has a transmitter (a timer does not count) | 2.3.7 |
| Deployable inhibits | ≥ 3, when the design has a deployable | 2.3.8 |
| Propulsion inhibits | ≥ 3, when the design has propulsion | 2.1.4 |
| Deployable delay | ≥ 30 min after separation | 2.4.4 |
| RF delay | ≥ 45 min after separation | 2.4.5 |
| Protrusion | ≤ 6.5 mm from the rail plane | 2.2.3 |
| Outgassing | TML ≤ 1.0 %, CVCM ≤ 0.1 % | 2.1.7 |

How SpaceCDF finds the evidence is a **C2O convention**. It reads the proposed or
accepted links of type `electrical_signal` (rejected links are ignored). An `inhibit`
link that ends on a transmitter, or on the subsystem that contains it, counts as
`properties.inhibit_count` RF inhibits and gives its `properties.delay_min`. A
`release` link to a deployable counts the same way for deployables. Links with
subtype `deployment_switch` and `rbf` count as those features. These are the links
that the link proposer creates (§3.7). An element can also declare values in
`performance.cds`, for example
`{"rf_inhibits": 3, "rbf": true, "rf_delay_min": 45, "tml_percent": 0.4}`. A
deployable is recognised from the KB `deployment` field (`body_mounted` is not a
deployable), else from its name. When nothing is declared the check says
**caution, not declared**. It says **fail** only when a declared value breaks the rule.

### 3.3 Requirement quality (`requirement_quality.py`, `configs/requirement_rules.yaml`)

**EARS pattern** (Mavin, Wilkinson, Harwood, Novak, RE'09, IEEE, DOI 10.1109/RE.2009.9):
ubiquitous, state-driven (*While*), event-driven (*When*), optional (*Where*),
unwanted behaviour (*If … then*), complex. The French keywords (*Tant que*,
*Lorsque*, *Si … alors*, *Là où*) are a **C2O adaptation**.

**Pinned INCOSE GtWR subset.** The rule numbers follow the community quick-reference
card (a secondary source). The word lists are **C2O defaults**.

| Id | Rule | Severity |
|---|---|---|
| R-MODAL | one obligation with *shall* / *doit* | error |
| R18-SINGLE | only one *shall* per requirement | error |
| R7-VAGUE | vague terms (*adequate, fast, user-friendly …*) | error |
| R8-ESCAPE | escape clauses (*where possible, as appropriate …*) | error |
| R9-OPEN | open-ended clauses (*including but not limited to, etc.*) | warning |
| R19-COMBINATOR | *and/or, unless, otherwise* | warning |
| R24-PRONOUN | pronouns (*it, they, this …*) | warning |
| R26-ABSOLUTE | absolutes (*always, never, 100 %*) | warning |
| R6-UNITS | a number without a unit | warning |
| C2O-TBD | open items (TBD, TBC, TBR) | warning (**C2O default**) |
| R2-PASSIVE | passive voice with an agent (*shall be … by*) | info |
| R17-SLASH | "/" between words | info |
| R20-PURPOSE | purpose phrases (*in order to, so that*) | info |
| R33-TOLERANCE | a measured value without a bound or tolerance | info |

A requirement with any error is **fail** and should be rewritten before a baseline.

### 3.4 Verification method defaults (`verification_defaults.py`)

ECSS-E-ST-10-02C Rev.1 gives four methods: Test (with demonstration), Analysis (with
similarity), Review of design and Inspection (4.2.2). It also requires a **risk
assessment for any requirement verified only by Analysis or Review of design**
(5.2.2.1). SpaceCDF flags these requirements.

The type-to-method mapping is a **C2O default**. It is applied first by threshold
parameter, then by keywords.

| Type | Recognised by | Default |
|---|---|---|
| Budget, margin or lifetime | `mass.`, `power.`, `systems.`, `orbit.`, `propulsion.` … parameters; *margin, lifetime, reliability, de-orbit* | A |
| Performance or function | `link.`, `data.`, `aocs.`, `payload.` … ; *downlink, point, deploy, image, survive …* | T |
| Compliance or documentation | *comply, in accordance with, ITU, licence, standard* | R |
| Physical feature or workmanship | *dimension, envelope, protrude, label, connector, material* | I |
| Anything else | — | A |

`POST …/rules/verification-defaults/apply` fills **empty** methods only. It never
overwrites a designer's choice.

### 3.5 FMECA skeleton (`fmeca_library.py`, `configs/failure_modes.yaml`)

The method follows ECSS-Q-ST-30-02C. The library is a **C2O default** compiled from
common CubeSat practice: battery, EPS, solar array, OBC, transceiver, antenna,
reaction wheel, star tracker, magnetorquer, sun sensor, GNSS, propulsion, thermal
hardware, structure, payload, and a generic mode. The 1–5 severity, occurrence and
detection scales are also C2O defaults (the standard's own scale was not available to
check). Each element is matched by its KB category, then its name, then its domain.
Three per-element adjustments apply:

- redundancy lowers severity by 1;
- TRL < 6 raises occurrence by 1;
- a `data` link (telemetry) lowers detection by 1.

A row is a **single-point failure** when severity ≥ 4 without redundancy. It is
**critical** when RPN ≥ 60 (C2O default).

### 3.6 Review-gate checks (`gate_checks.py`)

For each gate, the computed checks follow the ECSS-M-ST-10C Rev.1 review objectives
(SRR 4.4.3.4.3; PDR 4.4.3.4.4: product tree, specification tree and verification plan
released). The rule engines feed them:

| Gate | Checks |
|---|---|
| MCR | product tree |
| SRR | specification tree; requirement quality (≥ 80 % without an error, **C2O default**); a verification method for every requirement; margins |
| PDR | product tree with components; specification tree with derived subsystem requirements; requirement quality (100 %); verification methods; A/R-only risk flags; margins; CDS; FMECA single points |

`gate_exit_criteria.yaml` criteria marked `manual` or `hybrid` get **computed
evidence** where the model can answer them. For example, SRR-EC-08 is answered from
the TRL of every component. The reviewer still signs off. The interface criterion
PDR-EC-02 is answered by the interface readiness service (see §3.7).

### 3.7 Expected links between elements

The link proposer (`interface_proposer.py`, `configs/interface_rules.yaml`) creates the
expected TM/TC, power, RF, mechanical, thermal, timing, fluid and signal links. It
uses ECSS-E-ST-10-24C Annex E interface natures. The default interface matrix itself
is a **C2O default**, not a standard. Each proposal carries its `rationale` and
`standard_ref`, and the designer accepts, edits or rejects it. See that file's header
for the rules.

## 4. Where AI remains, and how it is controlled

| Kept capability | `/api/ai` name | Why a script cannot do it |
|---|---|---|
| `design_advisor` | `critique_need`, `general` | Reading and critiquing free stakeholder prose; open questions |
| `requirements_decomposition` | `write_requirements` | Turning free-text objectives into well-worded shall statements |
| `report_narrative` | `narrative` | Executive-summary style prose |

- **Off by default.** In `configs/genai.yaml`, `enabled: false` is the shipped value.
- **One kill switch.** When `enabled` is false or the capability is off, every
  `/api/ai` endpoint answers **503** before any model is called. This holds for the
  `spacecdf-ai` service and for the legacy direct path, whatever API key is set in the
  environment or sent in `X-API-Key`. Before this fix, the legacy path ran whenever a
  key was present.
- **Never required.** No workflow, gate or export calls AI.
- **Always checked.** Every AI answer is returned with `rule_checks`. Each proposed
  requirement, and each sentence with *shall* or *doit* in prose, is checked against
  EARS and the INCOSE subset. Statements with an error are marked `needs_revision`.
- **Only these three.** `spacecdf_ai.config.RETAINED_CAPABILITIES` holds the list.
  Any other name is refused even if `genai.yaml` enables it.

Fixed defects in the AI path: the HTTP `context` reached no capability (now spread
into the capability arguments); `max_tokens` was ignored (now forwarded and capped
by `budget.max_tokens_per_call`); the interface context read keys that do not exist
(now `from_element_id`, `to_element_id`, `interface_type`).

## 5. Endpoints

| Method and path | Returns |
|---|---|
| `GET /api/rules/catalogue` | rule files, sources (cited or C2O default), validation errors, requirement checks |
| `POST /api/rules/requirement-quality` `{texts, language?}` | checks for texts being typed |
| `GET /api/studies/{sid}/rules/margins?form_factor=` | mass and power roll-up with margins, ΔV, data handling, checks |
| `GET /api/studies/{sid}/rules/cds?form_factor=` | CDS checks and the evidence used |
| `GET /api/studies/{sid}/rules/requirements-quality` | one row per requirement: EARS pattern, findings, score |
| `GET /api/studies/{sid}/rules/verification-defaults` | default method, current method, risk-assessment flag |
| `POST /api/studies/{sid}/rules/verification-defaults/apply` | fills empty methods |
| `GET /api/studies/{sid}/rules/fmeca-skeleton` | FMECA rows (EN/FR text), single points, critical rows |
| `GET /api/studies/{sid}/rules/gates/{MCR\|SRR\|PDR}` | gate criteria, computed checks, computed evidence |
| `GET /api/studies/{sid}/rules/summary` | one summary per engine |

Each check is `{id, label{en,fr}, status: pass|warn|fail|not_evaluated, severity:
nominal|caution|alarm|info, detail{en,fr}, standard_ref, c2o_default, source, …}`.

## 6. Changing a default

1. Edit the value in the YAML file under `design/configs/`. Keep its `source:`. If
   the new value is your own choice, set `source: c2o_default`.
2. Restart the server. The start-up validation reports any error.
3. Run `pytest tests/test_services/test_rule_engines.py` to see which pinned numbers
   changed.

## 7. Not verified, to check before quoting as a standard

- ECSS-Q-ST-30-02C severity and probability scales and the criticality threshold
  (the library uses C2O 1–5 scales).
- INCOSE GtWR rule numbering (taken from a secondary quick-reference card; pin a
  version of the guide).
- ECSS-E-ST-50-05C link-margin values and ECSS-E-HB-10-02A phase margins used by
  `ecss_margin_enforcer.py`.
- Deployer-specific limits (mass, tuna can, rails), which override the CDS typical
  values.
- The expected interface matrix (`interface_rules.yaml`) is established practice, not
  a standard.
