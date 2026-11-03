# SpaceCDF design rules, design elements, SEMP diagram set and CubeSat stack builder

Read-only analysis, 2026-11-03. Code: `/home/claude/c2o/design` (paths below are relative to it unless they start with `sim/` = `/home/claude/c2o/sim`). Redesign context: `docs/plan_2026-11/REDESIGN_DECISIONS.md` (repo root `/home/claude/c2o/docs/...`) and redesign sections s1–s6 (scratchpad).

Caveats:
- The systems-engineering skill on this machine has only `SKILL.md`; the `references/standards/ecss-se.md`, `nasa-se.md`, `methods/*.md` files do not exist. ECSS and NASA clause and DRD numbers below come from my own knowledge and the redesign §3 tables. **Every clause or annex letter is "to verify"** against ecss.nl and the NASA SEH before it goes into the tool.
- "Today" means what the code does now, cited by file and function. "Missing" means I found no code that does it.

---

## 0. What the model holds today (the base the rules build on)

| Entity | Where | Fields that matter for these rules |
|---|---|---|
| Design element (mission/segment/system/subsystem/component/software/mode/logical) | `db/models.py` `DesignElementRow`; API `routers/elements.py` `ElementCreate` | `mass_kg`, `power_avg_w`, `power_peak_w`, `volume_cm3`, `dimensions_json`, `position_json` (body frame, m), `kb_component_id`, `trl`, `quantity`, `redundancy_type`, `performance_json`, `margin_percent` (default 20), `owner_position`, `subsystem_domain`, `segment` |
| Interface (link) | `ElementInterfaceRow`; type vocabulary `spacecdf_common/models/interface_types.py` | `interface_type` (9 canonical), `subtype`, `direction`, `origin` (`user`/`import`/`rule:<id>`), `standard_ref`, `rationale_json`, `properties_json`, `exchange_item_ids_json`, `status` suggested/accepted/rejected |
| Interface type reference fields | `TYPE_METADATA` in `interface_types.py` | power: rail_voltage, current_a, power_w, switched, grounding, connector; data: protocol, data_rate_bps, data_format, **address**, endianness, connector; rf: band, frequency_mhz, power_dbm, polarisation, connector; mechanical: mount_type, fastener, torque_nm, envelope_mm, material; thermal: conductance_w_k, heat_flow_w, interface_temp_c, contact_area_mm2, heater_power_w; timing; optical: boresight, fov_deg, keep_out; fluid; electrical_signal: signal, inhibit_count, delay_min, level |
| Exchange item (ICD line) | `ExchangeItemRow`; `routers/exchange_items.py` `build_icd_rows` | kind, properties |
| Requirement | `RequirementRow` | `level` mission/system/subsystem, `parent_id`, `threshold_param_path/op/value`, `verification_method` A/T/I/R/D, `verification_phase` PDR/CDR/QR/AR, `responsible_position`, `status` draft/approved/violated/verified/retired, `element_id`, `objective_id` |
| Typed trace relation | `RequirementRelationRow` | kind satisfies/verifies/refines/derives/traces/allocates; source/target kind requirement/element/function/**interface**/parameter/test. Nothing creates a relation with kind `interface` today (grep). |
| Verification item | `VerificationItemRow`; `services/vv_closure.py` `plan_item`, `apply_auto_closure` | method, level, phase, facility, acceptance_criterion, status, evidence_ref, `edited_by_user` |
| Function, port, allocation, functional exchange, realization | `FunctionRow`, `FunctionPortRow`, `FunctionAllocationRow`, `FunctionalExchangeRow`, `RealizationRow` | Arcadia spine (LA↔PA) |
| Mode membership | `ModeElementRow` | `is_active`, `power_w_in_mode`, `duty_cycle_percent` per (mode element, element); read by `services/analysis_context.py` `_build_modes` → `ModeSpec` (power_w, duty, payload_active, data_rate_bps, pointing, `guards` parsed from text by `_parse_guards`) |
| ConOps (second mode source) | `spacecdf_common/models/conops.py` `OperationalMode`, `MissionPhase`, `GroundStation`, `DataPipelineStep` | per-mode power_w, payload/platform/heater power, internal_dissipation_w, data_rate_mbps, pointing_requirement_deg, duty_cycle_percent; phases with modes, entry/exit criteria |
| Budget allocation | `BudgetAllocationRow` | budget_type mass/power/cost/data/delta_v/volume per element |
| Parameter ownership | `configs/seats.yaml` `owns.prefixes/element_types/element_domains`; `seats/guard.py`; `PendingChangeRow` | Decision 5 (warn, then owner review) |
| Gate baseline | `GateBaselineRow`, `ElementBaselineRow` | snapshot per gate |

Rule engines that already exist (all config-driven, all carry `standard_ref` or "C2O default"):

| Engine | File | Config | What it does |
|---|---|---|---|
| Interface proposer | `services/interface_proposer.py` `plan`, `_refine`, `reconcile`, `check_link`, `conflicts_for` | `configs/interface_rules.yaml` (roles, 27 rules at segment/subsystem/component level, coverage) | Proposes links with origin `rule:<id>`; refines rail voltage, battery bus, protocol, payload protocol, RF band, mount type from KB; keeps rejected links so they are never re-proposed; checks protocol, rail voltage and RF band mismatches |
| Margin policy | `services/margin_policy.py` `_category`, `evaluate_margins`, `system_margin_percent` | `configs/margin_policy.yaml` | Maturity category A/B 5 %, C 10 %, D 20 % from TRL + heritage (`category_from_trl`), harness 5 %, system ladder MDR 25 / PRR 20 / SRR 20 / PDR 20 / CDR 10 % (C2O default), mass vs CDS limit, power vs EOL array |
| CDS checks | `services/cds_checks.py` `evaluate_cds` | `configs/cds_rules.yaml` | CDS-MASS, CDS-COG (needs `position_json` on every massive unit), CDS-SW, CDS-RBF, CDS-RF-INH, CDS-DEP-INH, CDS-PROP-INH, CDS-DEP-T, CDS-RF-T, CDS-PROTR, CDS-TML… |
| Requirement quality | `services/requirement_quality.py` | `configs/requirement_rules.yaml` (EARS patterns + INCOSE-style checks R-MODAL, R7-VAGUE, R6-UNITS, R33-TOLERANCE…) | Text checks EN/FR |
| Verification defaults | `services/verification_defaults.py` `classify`, `suggest`, `suggest_all` | `requirement_rules.yaml#verification` | Method by threshold path prefix then keyword; A/R-only flagged for risk assessment (ECSS-E-ST-10-02C 5.2.2.1) |
| FMECA skeleton | `services/fmeca_library.py` `build_skeleton` | `configs/failure_modes.yaml` | Modes per unit type; S−1 if redundant, O+1 if TRL<6, **D−1 if the element has any data interface** |
| Gate checks | `services/gate_evaluator.py` `_auto`, `services/gate_checks.py` (GC-MARGINS, GC-CDS, GC-FMECA) | `configs/gate_exit_criteria.yaml`, `configs/gate_profiles.yaml` (products × maturity per gate) | Server-side checklist |
| Consistency | `services/consistency_engine.py` `run_consistency_check` | hard-coded | CON-MN, CON-REQ-01/02, CON-FN-01/02, CON-IF-01 (coverage), CON-BDG (own margin ladder), CON-OPS-01, CON-EQ-01 |
| Physics closure | `services/physics_closure.py` `place_elements`, `run_mass_properties`, `run_aocs_closure`, `run_thermal_closure` | constants in file | Auto +z stack, CoM/inertia, disturbance torques vs wheel, lumped thermal network with heater suggestion text |
| Harness | `services/harness_designer.py` `design_harness` | `BUS_SPECS` in file | Wires, connectors, harness mass per protocol |
| SMO export | `spacecdf-agents/.../exporters/smo/exporter.py` `SMOExporter.export` | — | Writes ~20 sim YAML files from the legacy `DesignState` |

### 0.1 Defects and inconsistencies found while reading (relevant to the rules)

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F1 | 6U/12U CDS envelope length 340.5 mm in the tool; the simulator's 6U is 366 mm long and the axes are ordered differently | `configs/cds_rules.yaml envelope_mm "6U": [226.3, 100.0, 340.5]`, `spacecdf_common/models/cubesat_standards.py CDS_SPECS["6U"]`; `sim/configs/eosat1/geometry.yaml bus.size_m [0.100, 0.226, 0.366]` | The 6U/12U length in CDS rev 14.1 (and the 6U spec) is 366 mm to my knowledge, **to verify**. Stack-height and envelope checks would be wrong by 25.5 mm; design→sim geometry would not agree |
| F2 | Two margin ladders | `consistency_engine.py` `phase_min_margins = {phase_0: 30, phase_a: 20, phase_b: 15, phase_c: 10, phase_d: 5}` vs `margin_policy.yaml system_margin_ladder` 25/20/20/20/10 (Decision 2) | CON-BDG and GC-MARGINS can disagree on the same design |
| F3 | Three maturity-margin sources | `services/equipment.py apply_equipment_selection` hard-codes `margin_percent=5.0` (and computes `power` but never writes it); `ElementCreate.margin_percent = 20.0` default; `margin_policy._category` derives A–D properly | The element's `margin_percent` column is a stale third number. Only `margin_policy` should decide |
| F4 | KB → element copy drops most physical data | `routers/elements.py _lookup_kb_component` returns name, mass, power, cost, trl, manufacturer, part_number, performance, category only: no `dimensions_mm`, `interfaces`, `operating_temp_c`, `form_factor`, `heritage_missions` | `physics_closure._dims_m` and the proposer re-read the KB, but a stack builder, the 3D view and exports cannot rely on the element |
| F5 | "Interface requirements" exist only as a label | `gate_exit_criteria.yaml PDR-EC-02` "Are interface requirements defined between all subsystems?" is evaluated as **link coverage** (`gate_evaluator.py:556`); `gate_profiles.yaml products.interfaces` = "Interface requirements and ICDs"; `spacecdf_common/models/interfaces.py InterfaceRequirement` is a Pydantic model that nothing persists | No IRD content in the database; ECSS-E-ST-10-24C IRD cannot be produced from it |
| F6 | SEMP counts interface requirements by keyword | `semp_generator.py _section_9_interface_management`: `"interface" in r["text"].lower()` and estimates n(n−1)/2 interfaces | Number is not the model's |
| F7 | Export block diagram is a fixed picture | `exporters/docs/docx_generator.py:363` calls `figures.subsystem_block_diagram()` without `connections`; boxes are hard-coded in `figures.py:409` | SRR/PDR documents show the same diagram for every mission |
| F8 | Diagram components with hard-coded data (and orphaned) | `components/OBCInterfaceDiagram.tsx` (EPS 0x10, AOCS 0x20, GPS 0x42 …), `components/PowerRailEditor.tsx` (8 V array, 7.4 V battery, 30 %/20 %/50 % split), `PowerDistribution.tsx`, `SystemBlockDiagram.tsx` (0 importers), `ModelBlockDiagram.tsx` (0), `EngineeringBudgets.tsx` (0); phases/* importers are orphaned (s2 §unreachable) | Mock-ups, not model views |
| F9 | SMO export is mostly hard-coded and clashes with the simulator | `exporter.py _gen_eps power_lines` fixed set; `_gen_s12`, `_gen_s19`/`_gen_fdir` fixed rules; `_gen_commands` func ids 0x10 load-shed, 0x20 safe… while the sim catalogue has func 10 = `AOCS_SLEW_TO` (REDESIGN M1); battery 28 V if > 50 Wh else 7.4 V | Design→simulator traceability is broken at the export |
| F10 | FMECA detection credit is a heuristic | `fmeca_library.py` header: "a data interface to the element → D − 1" | No link to an actual monitor; FDIR is not derived from FMECA |
| F11 | KB has no payload category and few physical fields | see §4.2 | Payload, stack and per-mode power cannot be derived |
| F12 | `address`, `current_a`, `switched` fields exist but nothing fills them; EPS `output_channels` never compared with loads | `interface_types.TYPE_METADATA`; `eps_boards.yaml performance.output_channels` | Switch matrix and bus address plan cannot be checked |
| F13 | PC/104 stack heights are C2O guesses not marked as such | `cubesat_standards.py PC104_STANDARD.max_stack_height_mm {1U: 70, 3U: 250, 6U: 250}` | Needs a source or a "C2O default" label |
| F14 | Auto placement ignores mounting class | `physics_closure.place_elements`: every massive element (antennas, solar panels too) stacked on +z, centred in x/y, sorted by domain name | CoG check is meaningless until positions are entered by hand (CDS-COG says "place them all") |
| F15 | Two mode sources | ConOps `OperationalMode` (generated at study creation, s2) and `mode` elements + `ModeElementRow` (`analysis_context._build_modes`, `source = element/conops/default`) | Rules must pick one: promote mode elements, import ConOps once |

---

## 1. Rule catalogue (bidirectional consistency rules)

### 1.1 Mechanics shared by every rule

Generalise what `interface_proposer.reconcile` already does for links (s5 WP1 "proposal framework"):

| Concept | Rule |
|---|---|
| Proposal record | `{target_kind, target_id or new, field/value or new entity, origin: "rule:<RULE-ID>", standard_ref, c2o_default: bool, rationale{en,fr}, inputs_hash, status: suggested/accepted/edited/rejected, owner_seat}` |
| Counts in analyses | A `suggested` value counts until rejected (as interface proposals do today, s4) |
| Rejection memory | Rejected proposals are kept; the same (rule, target, inputs) is never re-proposed (as rejected links today) |
| Edited by user | Never overwritten (as `VerificationItemRow.edited_by_user`); a changed input marks it **stale – review** instead |
| Staleness | Each proposal stores `inputs_hash` of the facts it used (KB id, rail, protocol, mode power…). When the hash changes: suggested → re-proposed silently; accepted → "stale, review" to the owner seat; edited → "input changed since your edit" |
| Approval | By the owning seat (seats.yaml), Team leader may approve for any seat (s4); cross-seat edits become `PendingChangeRow` (Decision 5) |
| Conflict | A rule that finds two accepted facts that cannot both hold raises an `AnalysisConflictRow` with severity caution (suggested involved) or alarm (both accepted), as `conflicts_for` does |
| Gate hook | Each rule declares the gate criterion it feeds (`gate_exit_criteria.yaml id`) so the checklist "Fix" link opens the rule's panel |

Rule IDs below: **E** = exists, **P** = partial, **M** = missing.

### 1.2 Interface ↔ interface requirement (ECSS-E-ST-10-24C IRD/ICD)

ECSS-E-ST-10-24C separates the IRD (requirements on an interface, from the customer/system level, DRD Annex A — to verify) from the ICD (the agreed definition between both parties, DRD Annex B — to verify). In SpaceCDF: the accepted link + its `properties` + exchange items = ICD content; the generated interface requirements = IRD content.

| ID | Direction | Trigger | Proposed / created (source) | Conflict detection | Gate | Today |
|---|---|---|---|---|---|---|
| IF-01 | interface → IR | Link accepted (status `accepted`), or suggested at PRR for external interfaces | One requirement per (link, property group) from the template table below, `level = "interface"`, `parent_id` = the system requirement the link serves (or none), relation `allocates` requirement→interface (`RequirementRelationRow`, `target_kind="interface"`), `responsible_position` = provider seat, verification method from IF-RV map. Source: template id + link `standard_ref` | Two IRs on the same link with contradictory values (e.g. 3.3 V vs 5 V) | PRR (external: launcher, ground, deployer D), SRR (U), **PDR-EC-02 B** — re-point PDR-EC-02 to "every accepted link has ≥ 1 approved IR and both seats agreed" | **M** (F5) |
| IF-02 | IR → interface | IR created manually or imported (ReqIF) naming two elements, or `InterfaceRequirement.subsystem_a/b` | Propose the link (type from IR `interface_type`, endpoints by name match) or flag "IR without interface" | IR names an element that does not exist | SRR-EC-02 (complete, non-conflicting) | **M** |
| IF-03 | interface change → IR | `properties_json` edit (rail, protocol, address, band…) or endpoint KB change | Re-render IR text; accepted IR → "stale, review" to provider + consumer seats | IR value ≠ link property | PDR-EC-02 | **M** |
| IF-04 | interface removed → IR | Link rejected or deleted | Propose IR retirement (`status = retired`) and remove ICD rows | Approved IR whose link is gone | PDR-EC-02 | **M** |
| IF-05 | bilateral agreement | IR approved by provider seat | Request agreement from consumer seat; link status lifecycle identified → defined (IR exists) → agreed (both seats) → verified (VCD item passed). The enum exists (`interfaces.py InterfaceStatus`) but `ElementInterfaceRow.status` only has suggested/accepted/rejected: add `agreement` column | One party rejects | PDR (ICD B) | **M** |
| IF-06 | external interfaces | Launcher/deployer chosen (KB `deployers.yaml`), ground station chosen, operator chosen | External links already proposed by rules `seg-space-launch-mech`, `seg-space-launch-separation`, `seg-space-ground-rf`, `seg-ground-operations-data`; add IRs from the deployer (CDS envelope, mass, rail, switches, RBF) and the S2G link (band, rate, modulation, coding, Eb/N0 margin) | Rail spec ≠ deployer interface | PRR (S2G ICD D, A5 in s4) | **P** (links exist, no IRs) |
| IF-07 | exchange items ↔ data link capacity | Exchange items set on a data link (`set_exchange_items_on_interface`) | Link `data_rate_bps` = Σ item rates; propose bus-load figure | Σ rates on a bus segment > protocol rate (`harness_designer.BUS_SPECS`) × (1 − 50 % C2O margin) | PDR-EC-03 (data margin) | **M** |
| IF-08 | IR ↔ verification | IR created | Verification item: power/data/RF/timing → T (interface test), mechanical/optical → I + T (fit check / alignment), thermal → A then T (TVAC), electrical_signal (CDS) → T + I; `requirement_rules.yaml#verification` already maps "connector, envelope, rail…" → I | IR without item | SRR-EC-03, PDR | **P** (generic defaults only) |

**IR templates (EARS, EN; FR mirrors).** `{}` are link properties; missing values render as `TBD` and the IR stays `draft` (C2O-TBD check in `requirement_rules.yaml`).

| type/subtype | Template | Values from |
|---|---|---|
| power/regulated, switched | "The {from} shall supply the {to} with {rail_voltage} V ± {tol} % on switched line {line_no}, rated {lcl_limit_a} A." + "The {to} shall draw no more than {current_peak_a} A from the {rail_voltage} V line." | rail (`_refine rail_voltage`), new PowerLine (§2.1), KB current |
| power/battery_bus | "The {battery} shall supply the {eps} with {v_min}–{v_max} V over the full state-of-charge range." | KB batteries `voltage_v` |
| power/array_input | "The {array} shall deliver ≥ {p_eol} W at EOL to the {eps} MPPT inputs at ≤ {voc} V open-circuit." | KB solar panels `power_eol_w`, cells `voc_v` |
| data/tm_tc, bus | "The {to} shall respond to TM/TC on {protocol} bus {segment} at address {address} at {rate} bit/s." | protocol (`_refine protocol`), new BusNode address |
| data/payload_data | "The {from} shall transfer payload data to the {to} over {protocol} at ≥ {rate} Mbit/s." | payload rate (sim `payload.yaml data_rate_mbps` analogue) |
| rf/space_ground | "When in contact above {el_min}°, the {sc} downlink shall close at {rate} bit/s with ≥ {margin} dB margin to {station}." | `ground_closure.py` link budget |
| rf/coax | "The {tx} RF port shall connect to the {antenna} through ≤ {loss} dB of {connector} cable in {band}-band." | band check `check_rf_compatibility` |
| mechanical/mount | "The {to} shall mount to the {from} in {mount_type} slot {slot} within envelope {envelope_mm}." | stack builder (§4) |
| mechanical/launcher, deployer | "The spacecraft shall fit the {deployer} envelope {envelope} with rail width ≥ 8.5 mm and mass ≤ {mass} kg." | CDS rev 14.1 2.2.5, Table 1 |
| thermal/conductive | "The {to} interface shall stay within {t_min}…{t_max} °C with conductance ≥ {G} W/K to the {from}." | KB `operating_temp_c`, physics_closure conductance |
| thermal/heater | "When the {to} is below {on_c} °C, the heater on line {line} shall deliver {power} W until {off_c} °C." | Heater entity (§2.3) |
| timing/pps | "The {gnss} shall deliver a PPS to the {obc} with ≤ {accuracy_us} µs error." | KB GPS |
| optical/boresight, fov | "The {unit} {fov}° field of view shall be free of obstruction by any deployed element." | geometry/stack |
| electrical_signal/deployment_switch, rbf, inhibit, release | CDS clauses verbatim-structure: "The spacecraft shall have ≥ 3 independent inhibits on RF transmission (CDS rev 14.1 2.3.7)" etc. | `cds_rules.yaml safety` |
| fluid/propellant | "The {tank} shall feed the {thruster} at {p} bar through {fitting}." | KB thrusters |

### 1.3 Requirement ↔ verification method and closure (ECSS-E-ST-10-02C)

| ID | Direction | Trigger | Proposed (source) | Conflict | Gate | Today |
|---|---|---|---|---|---|---|
| RV-01 | req → method | Requirement approved | Method from `verification_defaults.suggest` (threshold path prefix, then keywords); level/phase/facility from `vv_closure.plan_item` | Method differs from default (`differs`) | PRR-EC-06, SRR-EC-03 | **E** |
| RV-02 | req → threshold | Requirement with method A and no threshold | Propose `threshold_param_path` from the domain (e.g. `power.margin_percent`) and value from the objective measure (s4 S3) | A without threshold cannot auto-close | SRR-EC-02 | **P** (flag only) |
| RV-03 | analysis → closure | Analysis published | A-items passed/failed with `evidence_ref = analysis:<run>` (`apply_auto_closure`), skips waived/edited | Pass→fail flip after a design change | PDR-EC-01 | **E** |
| RV-04 | method A/R only → risk | `needs_risk_assessment` true | Propose a risk register entry "verified only by analysis" (ECSS-E-ST-10-02C 5.2.2.1) | — | PRR-EC-10, SRR | **M** (flag exists, no risk created) |
| RV-05 | T/I → AIV plan | Item method T or I | Propose test campaign line: model (PFM default, IOD §3.1), facility (`_assign_facility`), sequence (functional → vibration → TVAC → EMC) | Test with no facility; I-items after integration closure | PRR-EC-08, PDR (AIV B) | **P** |
| RV-06 | item → requirement (reverse) | Requirement retired/deleted | Retire item | Orphan item | SRR-EC-03 | **M** |
| RV-07 | verification phase ↔ gate | Gate review opened | All items with `phase = <gate>` must be passed or waived | Open items at their phase | PDR-EC-01 | **M** |
| RV-08 | VCD ↔ IR | IR created | See IF-08 | | | **P** |

### 1.4 Function ↔ product allocation

| ID | Direction | Trigger | Proposed (source) | Conflict | Gate | Today |
|---|---|---|---|---|---|---|
| FA-01 | function → element | Leaf function unallocated | Allocation to the subsystem of `allocated_to` domain (`FunctionAllocationRow`) | `CON-FN-02` | PRR-EC-03 | **P** (flag; domain string, not element) |
| FA-02 | element → function | Component/subsystem with no allocated function | Flag "unjustified product" or propose the function its role implies (role table in `interface_rules.yaml roles`) | Element without purpose | PRR-EC-04 | **M** |
| FA-03 | domain → product | Function allocated to a domain with no element | Propose subsystem via `populate-subsystems` (`routers/elements.py:1204`) | — | PRR-EC-04 | **P** |
| FA-04 | functional exchange → interface | `FunctionalExchangeRow` between functions allocated to different elements | Propose a data link (Arcadia component exchange) carrying an exchange item named after the functional exchange | Exchange with no physical path | PDR-EC-02 | **M** |
| FA-05 | function → requirement | Leaf function without requirement | Propose a functional requirement from the function name (EARS "The {element} shall {verb}…") | `CON-FN-01` | SRR-EC-01 | **P** |
| FA-06 | mode → functions | Mode active | Functions active per mode (function × mode matrix) | Function needed in a mode whose element is off | PDR | **M** |

### 1.5 Equipment selection ↔ budgets (with maturity margins)

User's ladder existing / modified / new 5 / 10 / 20 % = `margin_policy.yaml maturity_margins` A/B 5, C 10, D 20 (ESA margin philosophy 1.3, R-M1-4 / R-P-11..13, verified). Category from TRL ≥ 8 + heritage → A, TRL ≥ 8 → B, TRL ≥ 6 → C, else D; no KB part → D (C2O default). Keep that; delete the other two sources (F3).

| ID | Budget | Trigger | Proposed (source) | Conflict | Gate | Today |
|---|---|---|---|---|---|---|
| EB-01 | mass | KB unit selected/changed | Element `mass_kg` × quantity; maturity category + margin from `margin_policy._category`, shown with its source; manual override needs rationale | Total wet with maturity + harness 5 % + system ladder > CDS Table 1 / target | PRR-EC-05, SRR-EC-06, PDR-EC-03, GC-MARGINS, CDS-MASS | **P** (policy correct; element column and `apply_equipment_selection` disagree) |
| EB-02 | power per mode | KB unit selected | `ModeElementRow` proposals per mode: `power_w_in_mode` from KB `power_modes_w` (new) else `power_w` when active / 0 when off; duty from ConOps | Σ mode power × (1 + maturity) × (1 + system) > sunlit array; energy per orbit negative; DoD > limit | PRR-EC-05, PDR-EC-03 | **P** (`margin_policy` uses orbit-average `power_avg_w` only) |
| EB-03 | data | Payload/sensor selected; mode set | Generation per mode (rate × duty) → per-day volume → storage need vs OBC/mass-memory `storage_gb` with 50 % margin (`margin_policy.data_handling.storage_margin_percent`, C2O default) → downlink capacity per day from stations × passes × rate | Backlog grows over N days; storage < 2 days of data | PDR-EC-03 | **P** (legacy agent `tier1/data.py` on `payload.0.*` params, not elements) |
| EB-04 | link | Transceiver/antenna/station selected | Link budget per station (`ground_closure.py compute_link_budget`); margin ≥ 3 dB (ladder RF row, GSFC Rule 1.06, to verify) per rate tier (sim `ttc.yaml tm_rate_tiers`) | Margin < 3 dB at min elevation | PRR-EC-09, PDR-EC-03 | **P** |
| EB-05 | thermal dissipation | Mode power set | Dissipation per element per mode = power in mode − RF radiated (TX) → node heat load; heat-rejection margin 50 % (`margin_policy.thermal`) | Node outside op range hot/cold (`THERMAL_OUT_OF_RANGE`) | PDR-EC-03 | **P** (physics_closure uses peak/safe power, not modes) |
| EB-06 | cost | KB unit selected | Bottom-up recurring cost Σ `cost_recurring_keur` next to the CER estimate (`cost_engine.py`, WBS) | Divergence > 30 % (C2O default) | MDR-EC-08, PRR-EC-11 | **M** (cost_engine is CER-only) |
| EB-07 | volume / U | KB unit selected | Stack builder occupancy (§4) replaces density estimate (`tier2/volume.py`) | Stack height > internal length; U overflow | PDR (CDS matrix) | **P** |
| EB-08 | EPS capacity | Loads connected | Σ current per rail ≤ converter rating; switched loads ≤ `output_channels` (KB eps_boards); battery strings ≤ `max_battery_strings`; array input ≤ `max_solar_input_w` | Over-subscribed rail or channel | PDR-EC-03 | **M** |
| EB-09 | OBC resources | Software functions allocated | CPU/RAM per software element, ≤ 50 % peak (`margin_policy.data_handling`, ESA R-SW-1/2) | > 50 % | PDR-EC-03 | **M** |
| EB-10 | allocation → requirement | Budget allocation accepted (`BudgetAllocationRow`) | Subsystem requirement "The {subsystem} mass shall not exceed {alloc} kg" (s4 B1) with threshold path | Current best estimate > allocation | SRR-EC-01/06 | **M** |
| EB-11 | ΔV | Thruster + orbit | ΔV budget with 5/100/100 % (`margin_policy.delta_v`) vs total impulse/Isp of the KB thruster | Insufficient impulse | PRR-EC-12, PDR | **P** |

### 1.6 Equipment ports ↔ implied interfaces

| ID | Port fact | Trigger | Proposed (source) | Conflict | Gate | Today |
|---|---|---|---|---|---|---|
| EI-01 | Power rail in (V), current nominal/peak/inrush | Unit selected | Link (rule `unit-power`) with rail from `_refine rail_voltage`; **current_a = P/V**; assignment to an EPS **power line** (switch) with LCL limit ≥ 1.5 × peak (C2O default) | Rail not offered (`check_link` voltage); line over-current; non-switchable unit on a switchable line or vice versa | PDR-EC-02/03 | **P** (rail only) |
| EI-02 | Data bus protocol, default address, configurable? | Unit selected | Link (`unit-obc-tmtc`, `unit-adcs-bus`) with protocol; **address** from KB default, re-assigned on clash; bus segment (A/B if redundant CAN, as sim `obdh.active_bus`) | Duplicate address on a segment; > max devices (`BUS_SPECS.max_devices`); no shared protocol (`check_link`) | PDR-EC-02 | **P** (protocol only) |
| EI-03 | RF band, frequency, connector | Transceiver/antenna selected | `unit-rf-coax` and `sub-ttc-ground` (exists); frequency must sit in the filed band (`services/spectrum.py`) | Band mismatch (exists); TX freq outside allocation | PRR (spectrum D) | **P** |
| EI-04 | Mount class, envelope, stack connector | Unit selected | Mount type (`_refine mount_type`: PC/104 stack / external panel / bracket) → placement proposal (§4) | Collision, envelope, CoG | PDR, CDS-COG | **P** |
| EI-05 | Op temperature, dissipation | Unit selected | Conductive link to structure (`unit-conductive`); heater link if min op temp > `cold_case_c` −20 °C (`unit-heater`); then **Heater element + power line + thermostat set-points** from the cold-case result (physics_closure already computes the W in a fix string) | Cold case below min op with no heater | PDR-EC-03 | **P** |
| EI-06 | PPS | GNSS selected | `unit-gnss-pps` | — | — | **E** |
| EI-07 | Boresight, FOV, keep-out | Payload, star tracker, sun sensor, antenna selected | Optical interface to a structure face; keep-out cone; star tracker sun/Earth exclusion (sim `geometry.yaml` 15°/25°) | Deployed panel or antenna inside a keep-out; boresight not on the mode's pointing axis | PDR | **M** (type exists, no rule) |
| EI-08 | CDS discretes | Transmitter/deployable/propulsion present | `sub-rf-inhibits`, `unit-rf-inhibits`, `unit-deployment-switch`, `unit-rbf`, `unit-deploy-release` with `inhibit_count`, `delay_min` | CDS-RF-INH, CDS-DEP-INH, CDS-SW, CDS-RBF, CDS-DEP-T, CDS-RF-T | PDR (CDS) | **E** (declared counts) / **M** (no physical inhibit chain: which switch opens which line) |
| EI-09 | Propellant | Thruster with tank | `unit-propellant` | — | — | **E** |
| EI-10 | Connector/pin | Link accepted | Harness wires from `harness_designer.design_harness`, persisted as connector/pin rows on the link | Pin reused; PC/104 pinout vendor mix (GomSpace/ISIS/EnduroSat differ — C2O caution) | PDR | **P** (computed, not persisted) |

### 1.7 Mode ↔ power and data per mode (ConOps)

| ID | Trigger | Proposed (source) | Conflict | Gate | Today |
|---|---|---|---|---|---|
| MO-01 | Mode created (S5 template: LEOP, commissioning, nominal/imaging, downlink, safe) or unit added | Mode × element matrix (`ModeElementRow`): active, `power_w_in_mode`, duty, plus new **line state** (on/off) and data rate | Unit powered in no mode (dead weight) or in every mode but on a switchable line | PRR-EC-05 | **P** (table exists, no proposals) |
| MO-02 | Matrix changed | Per-mode power with margins; per-orbit energy by phase (eclipse fraction from orbit); battery DoD | Negative energy balance; DoD > limit (designAdapter: 25 % C2O default); sustainable duty (cf. sim M5: break-even 94 %, 77 % with 10 % margin) | PRR-EC-05, PDR-EC-03 | **P** |
| MO-03 | Payload mode duty | Data generated vs storage vs downlink per day (EB-03) | Backlog | PDR-EC-03 | **M** |
| MO-04 | Mode pointing requirement | AOCS sensor/actuator rule (s4 A4: pointing → AOCS type) | Pointing requirement tighter than estimate (`run_aocs_closure`) | PDR | **P** |
| MO-05 | Mode transition | `ModeTransition {from, to, trigger: ground TC / autonomous monitor / timer, guard}` replacing `_parse_guards` text | Autonomous transition without a monitor (FD-01) or action (FD-02); unreachable mode; mode with no exit | PDR (FDIR) | **P** (guards are parsed text) |
| MO-06 | Phase ↔ modes | Each `MissionPhase.modes` must exist; LEOP timer sequence (CDS 30/45 min) produces the first mode | Phase refers to a missing mode | MDR-EC-06 | **P** |
| MO-07 | Mode ↔ switch matrix | Line state per mode → SMO `power_lines` initial state and planner activities | Line on in a mode where its unit is inactive | — | **M** (F9) |
| MO-08 | Minimum mode set | safe + science + downlink | `CON-OPS-01` | MDR-EC-06 | **E** |

### 1.8 FMECA ↔ FDIR monitors and actions

| ID | Trigger | Proposed (source) | Conflict | Gate | Today |
|---|---|---|---|---|---|
| FD-01 | FMECA row with S ≥ 3 | Detection means: S12 monitor on a TM parameter of that unit (limit from KB op range or design value) or an S5 event; **detection score from the monitor's existence** (replaces "has a data link", F10) | Mode with S ≥ 4 and no monitor | PDR-EC-05 | **M** |
| FD-02 | Monitor created | S19 event–action: power-cycle the unit's line, switch to redundant bus/unit, safe mode, load shed stage. Action must reference an existing S8 function id and an existing switchable line | Action routed to the wrong function (cf. REDESIGN M1 ea 1001 dispatched `AOCS_SLEW_TO`); action that switches off the OBC's own line | PDR | **M** |
| FD-03 | Single point (no redundancy, S = 5) | Risk register entry (s4 C2→S6) with owner seat | SPF with no risk | PRR-EC-10, GC-FMECA | **M** (counted only) |
| FD-04 | Redundancy declared (`redundancy_type`) | Second unit or second bus segment + switch-over function | Redundancy declared but no switch-over path | PDR | **M** |
| FD-05 | FMECA effect ↔ simulator symptom | `expected_symptoms` row (sim `configs/eosat1/instructor/expected_symptoms.yaml`, REDESIGN M6) per failure | Failure mode with no expected symptom | — (training) | **M** |
| FD-06 | Monitor validity | Monitor only valid while its unit is on (cf. REDESIGN M2 `valid_when`) | Monitor fires while unit off | PDR | **M** |

### 1.9 Requirement ↔ gate criterion

| ID | Trigger | Proposed | Conflict | Today |
|---|---|---|---|---|
| RG-01 | Gate profile loaded | Each criterion lists `products` (gate_profiles.yaml) and an evidence query; requirements counted by level/status | Criterion with no evidence query (SRR-EC-04 "not implemented", s2) | **P** |
| RG-02 | Gate review | IRs approved for every accepted link (IF-01) feed PDR-EC-02; system reqs with threshold+method+parent feed SRR-EC-02/03 | Re-pointing needed (F5) | **M** |
| RG-03 | Gate passed | Baseline snapshot (`GateBaselineRow`), products → B; later edit → U + log | — | **P** |
| RG-04 | verification_phase | RV-07 | | **M** |

### 1.10 Parameter ownership ↔ seat

| ID | Trigger | Proposed | Conflict | Today |
|---|---|---|---|---|
| PO-01 | Parameter or element created | Owner from `seats.yaml` prefixes/element_domains | Unowned key → "parameters wanted" ledger (s4) | **E** (owner) / **M** (ledger) |
| PO-02 | Interface created | Owner = Systems; **parties** = endpoint seats (bilateral ICD); IR owner = provider seat | Edit by a non-party → pending change | **M** |
| PO-03 | Requirement created | `responsible_position` from threshold path prefix or element domain | Requirement owned by no seat | **P** |
| PO-04 | Proposal raised | Routed to owner seat's Next card (s4 next action #2) | — | **P** |
| PO-05 | Rule input missing | E.g. EPS rails unknown → ask Power seat, not Systems | — | **M** |

### 1.11 Design → simulator export (the traceability end point)

| ID | Model source | Simulator file (EOSAT-1) | Today |
|---|---|---|---|
| SX-01 | PowerLine set + mode line states | `subsystems/eps.yaml power_lines`, line indices used by S8 `EPS_POWER_ON/OFF` | hard-coded (F9) |
| SX-02 | Monitors | `monitoring/s12_definitions.yaml` | 6 fixed defs |
| SX-03 | FDIR actions | `monitoring/s19_rules.yaml`, `subsystems/fdir.yaml` | fixed; func ids clash |
| SX-04 | Functions (S8 ids) | `commands/tc_catalog.yaml` | fixed |
| SX-05 | TM parameters, HK SIDs | `telemetry/parameters.yaml`, `hk_structures.yaml` | `param_id_allocator.py` deterministic by domain ranges 0x0100… (good) |
| SX-06 | Stack/geometry | `geometry.yaml` (c2o.geometry/1; "what SpaceCDF writes for a design") | `frontend/src/spacecraft/designAdapter.ts designGeometry` writes bus + panels + wings, not internals |
| SX-07 | Thermal nodes, heaters | `subsystems/tcs.yaml network.nodes`, `heaters` (name, power_w, on/off °C) | not exported from the network |
| SX-08 | Buses | `obdh.yaml`, params 0x030E–0x0310 bus A/B | not exported |
| SX-09 | RF ladder, link | `ttc.yaml tm_rate_tiers`, `eirp_dbw`, `gs_g_t_db` | partial |

Every SX export should carry, per generated item, `source: spacecdf:<element|line|monitor id>`, so the simulator manual and instructor tools can link back.

---

## 2. Design elements a CubeSat needs (level of EOSAT-1) and how to hold them

Legend for "Representation": **existing** = entity/field exists; **new** = proposed.

### 2.1 Electrical

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| Power source chain | array strings (Voc, Isc, P_BOL/EOL), MPPT channels, battery (cells s×p, V range, Wh, DoD limit), EPS converters (rails V, max A) | existing: elements + KB (`solar_panels`, `solar_cells`, `batteries`, `eps_boards.performance.bus_voltage_v`, `mppt_channels`); **new**: `Rail {eps_element_id, voltage_v, regulated, max_current_a, efficiency}` | `eps.yaml` arrays, battery, `soc_100_v`… |
| Power line / switch (PCDU/LCL) | line number, rail, LCL trip A, latching?, switchable / always-on, default state, inhibit group, loads[] | **new** `PowerLine {id, eps_element_id, line_no, rail_id, lcl_limit_a, switchable, default_on, inhibit_group, s8_function_ids}`; link `power` interface gets `properties.line_id` | `eps.yaml power_lines` (obc, ttc_rx always on; ttc_tx, payload, fpa_cooler, htr_bat, htr_obc, aocs_wheels, prop switchable) |
| Switch matrix per mode | line × mode on/off | **new** column `line_state` on `ModeElementRow` or `ModeLineState {mode_id, line_id, state}` | `power_lines` initial; planner activity line steps |
| Inhibits (CDS) | separation switches (count, position on rail feet), RBF, timers 30/45 min, which line each opens | existing `electrical_signal` links with `inhibit_count`, `delay_min`; **new** `Inhibit {kind, element_id, opens_line_ids[], order}` | sim separation timer (REDESIGN M4) |
| Connectors & harness | connector per port (PC/104 H1/H2, Molex Picoblade, SMA/MMCX), pin, wire gauge, length, mass | partly computed by `harness_designer` (not persisted); **new** `Port {element_id, kind, connector, pin}` and harness rows | — |
| Grounding | single-point / chassis | interface property `grounding` exists | — |

### 2.2 Mechanical

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| Form factor & envelope | 1U…12U, CDS envelope, rails, max mass, CoG box | existing `cds_rules.yaml` (fix F1), structure KB `pc104_slots`, `deployment_switches` | `geometry.yaml bus.size_m` |
| Stack placement | mount class (pc104_board, pc104_module, u_module, face_panel, deployable, bracket), column, slot, z offset, height incl. standoffs, orientation | existing `position_json` (point only); **new** `Placement {element_id, mount_class, column, slot, z_min_mm, z_max_mm, face, orientation, locked, origin}` | — (geometry has only bus/panels/wings/sensors) |
| Deployables | stowed/deployed geometry, hinge axis, release mechanism, inhibits | KB `deployment` text only; **new** `Deployable {element_id, face, hinge_axis, deployed_geometry, release_element_id}` | `geometry.yaml wings[]`, `deployed_bit` |
| Mass properties | CoG, MoI, CP–CG | existing `run_mass_properties` → `mp_*` params | aocs inertia in `aocs.yaml` |
| External faces | per face: cells area, apertures, radiators, antennas, sensors | **new** `Face {face, items[]}` derived from placements | `geometry.yaml body_panels` |

### 2.3 Thermal

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| Dissipation per mode | W per element per mode | **new** derived from `ModeElementRow.power_w_in_mode` − RF out | tcs node loads |
| Nodes | mass, cp, area, emissivity/absorptivity | existing `physics_closure.run_thermal_closure` builds nodes from elements (not persisted); **new** persist `ThermalNode` with element link | `tcs.yaml network.nodes` (structure, panels px…mz, wings, obc, battery…) |
| Couplings | conductive W/K, radiative | existing `thermal` links `properties.conductance_w_k` | `tcs.yaml network` couplings |
| Heaters + thermostats | power, line, on/off set-points, auto/manual | **new** `Heater {element_id, line_id, power_w, on_c, off_c, mode: auto/manual}` (proposed from cold case) | `tcs.yaml heaters` (battery 8 W +5/+10; obc 4 W −10/−5; thruster 12 W 190/230) |
| Op/survival ranges | min/max op, survival | KB `operating_temp_c` (only part of categories); **new** survival range | `tcs.yaml event_thresholds`, `mcs/limits.yaml` |

### 2.4 Data handling

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| Buses | protocol, segment (A/B), master, rate, max devices, length | **new** `Bus {id, protocol, segment, master_element_id, rate_bps, redundant_with}` | obdh bus A/B, `obdh.active_bus` 0x030E |
| Nodes and addresses | element, bus, address (7-bit I2C / CAN node id / RS-485 id), configurable? | `data` link `properties.address` exists but empty; **new** `BusNode {bus_id, element_id, address}` with uniqueness | — |
| Data rates | per exchange item / per mode | existing exchange items; per-mode rate on `ModeElementRow` (new column) | `payload.yaml data_rate_mbps` 96 |
| Storage | capacity, partitions, packet stores | KB `obcs.performance.storage_gb`; **new** `Store {element_id, capacity_mb, segments}` | `payload.yaml total_storage_mb 20000`, `num_memory_segments 8`; `memory/memory_map.yaml` regions |
| CPU/RAM | load per software element | **new** on software elements | `obdh.yaml cpu_baseline_pct` |

### 2.5 Commanding and telemetry (PUS-C, ECSS-E-ST-70-41C)

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| APIDs | per application/subsystem | **new** `Apid {id, element_id/software_id, name}` | packet APIDs in sim (PUS layer) |
| PUS services used | S1,3,5,6,8,9,11,12,13,15,17,19,20 per position | **new** study-level service list | `mcs/positions.yaml` |
| Housekeeping SIDs | sid, period, parameters | **new** `HkStructure {sid, apid, period_s, params[]}` | `telemetry/hk_structures.yaml` |
| Parameters | id, name, unit, type, owning element, limits | partial `param_id_allocator.py` (domain ranges); **new** `TmParameter {id, element_id, name, unit, limits, valid_when}` | `telemetry/parameters.yaml` |
| S8 functions | func id, name, args, target element/line | **new** `TcFunction {func_id, name, element_id, line_id?, args}` | `commands/tc_catalog.yaml` |
| Events | id, severity, source | **new** `EventDef` | `events/event_catalog.yaml` |

### 2.6 RF

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| Bands/frequencies | UL/DL MHz, filing | KB transponders `band`, `frequency_mhz` (8/20); `services/spectrum.py` | `ttc.yaml ul_freq_mhz 2025 / dl_freq_mhz 2200` |
| Modulation/coding | per rate tier | KB `modulation` (13/20) | `coding_gain_db` |
| Rate ladder | beacon / low / high tiers | **new** `RateTier {name, bps, modcod, min_margin_db}` on the transceiver | `ttc.yaml tm_rate_tiers` (SAFE 1 kbps, LOW 16 kbps, HIGH 128 kbps) |
| Antennas | gain, pattern, face, deployable | KB antennas `gain_dbi`, `deployment`; placement (§4) | `geometry.yaml antennas` |
| PA levels | low/nominal/high W | **new** on transceiver | `pa_low/nominal/max_power_w` |

### 2.7 Software and modes

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| Mode machine | modes, transitions, triggers, guards | existing mode elements; **new** `ModeTransition` (MO-05) | sim system modes; `exporters/fsw/mode_manager.py` |
| FDIR | monitors, actions, levels, recovery procedures | **new** `Monitor`, `Action` (FD-01/02); FMECA rows link | `fdir/`, `s12`, `s19`, `fdir/fault_propagation.yaml` |
| OBCPs / procedures | | out of scope for design; link from actions | `obcp/`, `procedures/` |

### 2.8 Ground segment

| Element | Attributes | Representation | Sim counterpart |
|---|---|---|---|
| Stations | lat/lon, dish, G/T, EIRP, bands, min elevation | KB `ground_stations`, ConOps `GroundStation`, `analysis_context._select_stations` | `planning/ground_stations.yaml`, `ttc.yaml gs_g_t_db` |
| MCC, network, data pipeline | | ConOps `mission_control_centre`, `DataPipelineStep`; ground segment elements (`segment = ground`) | MCS, GSG |

---

## 3. SEMP / ECSS diagram set derivable from the model

Gates per Decision 1 (MDR → PRR → SRR → PDR). ECSS: the SEMP equivalent is the System Engineering Plan (SEP, ECSS-E-ST-10C Annex D — to verify); figures live mostly in the DRDs listed. NASA: SEMP outline SEH Appendix J, ConOps Appendix S, N² §4.3/§6.3, review criteria NPR 7123.1 App G (all to verify).

Rendering stack: `@xyflow/react` is already a dependency (workbench `BlockDiagram.tsx`); add `elkjs` for layered/orthogonal layout of block and bus diagrams; plain SVG for matrices, timelines and the stack elevation; three.js from `shared/ui-viz/vendor/three` for 3D. Exports: the server-side matplotlib figures in `exporters/docs/figures.py` must take the same diagram model (today `subsystem_block_diagram(connections)` accepts connections but is called without them, F7). Recommended pattern: the server returns one **diagram model JSON** per diagram (`nodes, edges, groups, annotations, source ids`) from `GET /studies/{id}/diagrams/{kind}`; the React view and the docx exporter both draw it. New SVG modules that MCS also needs (stack, power flow) go in `shared/ui-viz` with the `mount(el,{t}) -> {update, destroy}` contract.

| Diagram | Source data in the model | Missing | Rendering | Gate (maturity) | ECSS DRD / NASA |
|---|---|---|---|---|---|
| Mission context (system of interest + externals) | segments, external links (`seg-*` rules), stakeholders | stakeholder entity link | xyflow + ELK | MDR (D), PRR (B) | E-10 MDD (B) / SEH ConOps |
| ConOps phase timeline | `MissionPhase` (duration, modes, entry/exit) | one mode source (F15) | SVG Gantt band | MDR (D), PRR (U) | E-ST-70 mission ops concept / SEH App S |
| Mode diagram (state machine) | mode elements, guards text | `ModeTransition` entity (MO-05) | ELK layered or Mermaid stateDiagram in exports | MDR (D), PDR (B) | E-10 DDF, E-ST-70 / SEH App S |
| Ops scenario swimlanes (LEOP, imaging pass, downlink) | phases, planner activity types (sim `planning/activity_types.yaml`) | scenario entity (steps × lanes: S/C, station, MCC, operator) | SVG swimlane | PRR (D), PDR (U) | E-ST-70 / SEH App S |
| Product tree | element tree (`parent_id`, types) | level off-by-one fixed (s2 WP0) | xyflow tree (exists in BlocksPanel) | PRR (D), PDR (B) | ECSS-M-ST-10 product tree / SEH product breakdown and WBS (to verify) |
| Function tree | `FunctionRow` tree, `FunctionTree.tsx` (mounted) | — | existing | PRR (D/B), SRR (U) | E-10 Annex H / SEH 4.3 |
| Function × product allocation matrix | `FunctionAllocationRow`, `RealizationRow` | FA-02 | SVG matrix | SRR | E-10 / SEH 4.3 |
| Physical block diagram | elements + accepted links by type | layout persistence per diagram (only `diagram_x/y`) | xyflow + ELK with type glyphs (`InterfaceGlyph.tsx`) | PRR (system), PDR (unit) | E-10 DDF / SEH 4.3 |
| N² chart | accepted links (from→to, type), exchange items | none | SVG matrix, cells = glyphs per type; orphaned `InterfaceMatrixView.tsx` to remount | PRR (D), SRR (U), PDR (B) | E-10-24 / SEH 4.3 N² |
| Electrical power block diagram | array → MPPT → battery → rails → lines → loads | `Rail`, `PowerLine` (§2.1) | ELK left→right; reuse `powerflow.js` styling | PDR (B) | E-ST-20 / SEH |
| Switch matrix (lines × modes) | `PowerLine`, mode line states | MO-07 | SVG table with on/off cells and line current sums | PDR | E-ST-20 / ops |
| Data-handling block diagram / bus topology with addresses | `Bus`, `BusNode`, data links, stores | §2.4 entities; replaces hard-coded `OBCInterfaceDiagram.tsx` | ELK, bus as horizontal trunk, nodes with address badges | PDR | E-ST-50, E-ST-40 / SEH |
| TM/TC architecture (APIDs, SIDs, services) | §2.5 | all new | SVG table + tree | PDR (D), CDR | E-ST-70-41 PUS |
| RF block diagram | transceiver, coax, antennas, ground chain (KB ground_rf/baseband) | rate tiers, PA levels | ELK | PRR (S2G), PDR | E-ST-50 / SEH |
| Link budget waterfall | `ground_closure.py` | per tier | exists `figures.link_budget_waterfall` | PRR/PDR | E-ST-50-05 |
| Thermal network / node diagram | `run_thermal_closure` nodes and couplings, heaters | persistence; heater entity | ELK graph, nodes coloured by hot/cold margin | PDR | E-ST-31 TMM |
| Mechanical stack / exploded view | placements (§4) | `Placement`, KB dims (F4, §4.2) | SVG elevation + three.js | PDR (B) | E-ST-32 / config drawing |
| Ground segment diagram | ground elements, stations, MCC, data pipeline | MCC/network elements | ELK; map inset (groundtrack.js) | PRR (D), PDR | E-ST-70 / SEH |
| Requirement tree / traceability | `RequirementRow.parent_id`, relations, `TraceabilityTree.tsx` (mounted) | IR level, interface targets | existing + interface leaves | SRR (B), PDR | E-10-06 TS / SEH 4.2 |
| Verification matrix (VCD) | `VerificationItemRow` | RV-06/07 | SVG/HTML matrix (req × method/phase/status); `VerificationMatrix.tsx` orphaned | SRR (D), PDR (U) | E-10-02 VCD / SEH 5.3 |
| Budget charts (mass/power/data/link/ΔV) | `margin_policy.evaluate_margins`, `figures.budget_*` | per-mode power, data | exists (charts/) | PRR→PDR | E-10 Annex I |
| Risk matrix (5×5) | risk register (s2: `localStorage` today) + FMECA SPFs | server-side register (WP0 #9), FD-03 | exists `figures.risk_matrix` | MDR→PDR | M-ST-80 / SEH 6.4 |
| FMECA / FDIR tree | FMECA rows, monitors, actions | FD-01/02 | SVG tree (failure → monitor → action → mode) | PDR | Q-ST-30-02 |
| CDS compliance matrix | `evaluate_cds` | — | table | PRR (D), PDR (B) | CDS 14.1 |
| SEMP organisation / seat map | seats, holdings | — | table | PRR | SEP / SEH App J |

---

## 4. CubeSat stack builder and visualisation

### 4.1 Construction rules

| Rule | Value / source |
|---|---|
| Envelope, mass, CoG box | `cds_rules.yaml` `envelope_mm`, `max_mass_kg`, `cog_limits_cm` (CDS rev 14.1 2.2.10–2.2.11 Tables 1–2); fix 6U/12U length (F1, to verify) |
| Rails and protrusion | rail width ≥ 8.5 mm (2.2.5), protrusion ≤ 6.5 mm from rail plane (2.2.3) → stowed deployables and body panels must fit in 6.5 mm |
| Separation switches | on rail end feet (2.3.2), count from structure KB `deployment_switches`; RBF access port (2.3.4/2.3.5) on a face reachable in the deployer |
| Internal columns | 1U/1.5U/2U/3U: one column 100 × 100; 6U: two 1U-wide columns × 3U long (sim: X 0.100, Y 0.226, Z 0.366); 12U: 2 × 2 columns. Each column's usable internal length = envelope length − end-plate allowance (C2O default 2 × 6 mm, to calibrate per structure KB) |
| PC/104 boards | board 96 × 90 mm (`PC104_STANDARD.board_dimensions_mm`), 4 × M3 holes; pitch = max(stack-through connector height, PCB + tallest component + clearance). Common stack-through H1/H2 connectors give 15.24 mm pitch — **C2O default, to verify per vendor**; taller modules (battery packs, RW modules, ADCS units) declare their own height |
| Spacers | standoff height fills pitch − board − 1.6 mm PCB; spacer mass from `mechanical_hardware.yaml` or C2O default |
| Bus connector compatibility | all boards on one stack share the PC/104 header pinout: mixing vendors (GomSpace, ISIS, EnduroSat) raises a caution "check H1/H2 pinout" |
| U budget | payload and modules declare U fraction (0.5U, 1U, 2U…); column length sum ≤ internal length |
| Faces | ±X/±Y/±Z faces hold body solar cells (`designAdapter.designGeometry` splits area by face), sun sensors, antennas, star tracker baffles, radiator, apertures |
| Deployables | wings on ±Y (sim), UHF antennas from +Z end, booms; stowed thickness ≤ 6.5 mm; release on burn wire with ≥ 3 inhibits (2.3.8) and ≥ 30 min delay (2.4.4) |

### 4.2 What the KB has and lacks (counts from `packages/spacecdf-kb/src/spacecdf_kb/data/components/*.yaml`)

| Category (file) | n | dims_mm | form_factor | interfaces (bus) | op temp | power | Missing for stacking/ports |
|---|---|---|---|---|---|---|---|
| obcs | 8 | 7 | PC/104 7 | I2C/SPI/UART/CAN… 8 | 6 | 8 | stack height incl. components, address, CPU/RAM load |
| eps_boards | 6 | 6 | PC/104 6 | 6 | 6 | — (no own consumption) | rail max current per rail, LCL per output, line count is `output_channels` |
| batteries | 11 | **3** | none | I2C 3 | in perf 11 | — | dims, mount class (board/pack), strings s×p, heater built-in |
| reaction_wheels | 12 | **4** | none | 4 | — | 12 | dims, module vs single wheel, inrush, rail V |
| magnetorquers | 6 | 5 | PC/104 2 | 6 | 5 | 6 | rod vs board vs coil |
| star_trackers | 7 | **0** | none | 1 | — | 7 | dims, baffle, boresight, exclusion |
| sun_sensors | 6 | 6 | none | 6 | 5 | 6 | FOV axis, face |
| gps_receivers | 5 | 4 | none | 5 | 4 | 5 | antenna, PPS flag |
| transponders | 20 | **1** | PC/104 2 | 8 | 1 | 20 | dims, rail V, PA levels, rate tiers |
| antennas | 7 | 7 | none | — | 2 | — | face/mount, deployable geometry |
| solar_panels | 7 | 7 | none | — | 1 | (BOL/EOL W) | face, stowed thickness, hinge |
| thrusters | 17 | **0** | none | 4 | 4 | 17 | dims, nozzle face, tank volume |
| cubesat_structures | 8 | 8 | 1U…6U | 1 | 1 | — | internal length per column, end-plate thickness, mounting decks |
| deployers | 5 | 3 | deployer types | — | — | — | envelope tab spec |
| thermal_hardware, mechanical_hardware, harnesses | 6/7/7 | 0 | none | few | — | — | dims |
| **payload / imagers** | **0** | — | — | — | — | — | whole category (s2 L3 finding) |

No KB entry has: CoG offset, connector list, default bus address, per-mode power (standby/nominal/peak beyond `power_peak_w` in the model), inrush current, survival temperature, stack height, mount class.

### 4.3 Placement algorithm (proposed, then approved; origin `rule:STACK-*`)

1. **Classify** each space element by mount class: KB `form_factor == PC/104` or interface `PC/104` → `pc104_board`; battery/RW/ADCS unit with dims ≥ 90 × 90 → `pc104_module`; payload/star tracker/propulsion → `u_module` (length from dims, rounded up to 0.5U unless exact); solar panel/sun sensor/patch antenna → `face_panel`; deployable antenna/wing/boom → `deployable`; else `bracket`. This extends `_refine mount_type`.
2. **Assign faces** (fixed rules, C2O defaults, each with rationale): payload aperture and radiator on nadir face (−Z in sim body frame); GNSS patch zenith (+Z); S/X-band patch on the face the TT&C mode points at the station (nadir by default); UHF deployables at the zenith end; star tracker on a face whose boresight stays > 25° from Earth limb and > 15° from Sun in the nominal attitude (sim `geometry.yaml` exclusions); sun sensors one per face for coarse sun; separation switches on the −Z rail feet.
3. **Order the stack** (per column, lowest score first): payload at the aperture end; battery and EPS adjacent (short high-current path) and near the CoG; ADCS unit/wheels near the CoG; OBC between EPS and radio (shortest buses); radio next to the face of its antenna (coax length); high-dissipation boards next to a radiator face; heater-needing units away from the radiator.
4. **Optimise**: greedy initial order → pairwise swap search minimising `w1·|CoG − centre|/limit + w2·Σ harness length proxy + w3·thermal penalty`, with locked slots kept. Deterministic (seeded by element ids) like `physics_closure.place_elements`.
5. **Write** `Placement` rows and `position_json` (box centre) so the existing `run_mass_properties`, `run_aocs_closure`, CDS-COG and `designGeometry` use real positions instead of the +z auto stack (F14).

### 4.4 Checks

| Check | Rule | Feeds |
|---|---|---|
| Column height | Σ pitch + module lengths ≤ internal length | CDS matrix, EB-07 |
| Envelope | every box inside the envelope; stowed face items ≤ 6.5 mm out of rail plane | CDS-PROTR |
| Collision | pairwise AABB (boxes) on the same column/face; deployed geometry vs body and other deployables | new STACK-COLL |
| CoG | `run_mass_properties` vs `cog_limits_cm` | CDS-COG |
| Keep-out | FOV cones (optical links) vs deployed panels/antennas | EI-07 |
| Mass | total vs Table 1 with margins | CDS-MASS, GC-MARGINS |
| Inertia | principal axes ratio for the AOCS mode (gravity-gradient stability if passive) | AOCS closure |
| Thermal adjacency | dissipating units next to radiator; battery between warm units | thermal closure |
| Connector | PC/104 pinout vendor mix | caution |

### 4.5 Visualisation

| View | How | Interaction |
|---|---|---|
| 2D elevation per column (SVG) | rails, U ruler (mm), slot boxes coloured by subsystem, standoffs hatched, CoG cross with CDS box, height bar against internal length, face strip for ±X/±Y | drag a board to reorder (re-runs checks live, writes a proposal), lock/unlock slot, click → element panel; second column for 6U |
| Face map (SVG) | six unfolded faces with cells, apertures, antennas, sensors, RBF/switch markers | drag items between faces |
| 3D (three.js) | new `shared/ui-viz/stack3d.js` using vendored `three.module.min.js` and the `mount/update/destroy` contract; envelope wireframe, boxes per placement, stowed ↔ deployed toggle, exploded slider along the stack axis, keep-out cones, CoG marker | orbit camera; selection sync with the 2D view; same module usable in the MCS (`geometry.yaml` extended) |
| Export | `geometry.yaml` (c2o.geometry/1) gains optional `internal: [{id, name, box_m: [x,y,z,dx,dy,dz], subsystem}]`; config drawing PNG for PDR docx from the elevation SVG | — |

---

## 5. Data-model additions (consolidated)

| # | Addition | Kind | Used by rules |
|---|---|---|---|
| D1 | Generic `Proposal` (origin rule, standard_ref, c2o_default, inputs_hash, status, owner seat) | new table | all (s5 WP1) |
| D2 | Requirement `level = "interface"`; relation `allocates` requirement→interface; `template_id`, `inputs_hash` | values + 2 columns on `RequirementRow` | IF-01..08 |
| D3 | `ElementInterfaceRow.agreement` (identified/defined/agreed/verified) + `parties` | column | IF-05, PO-02 |
| D4 | `Rail`, `PowerLine`, `ModeLineState`, `Inhibit` | new tables | EI-01, EB-08, MO-07, EI-08, SX-01 |
| D5 | `Bus`, `BusNode` (address, unique per bus) | new tables | EI-02, IF-07, SX-08 |
| D6 | `Port` (element, kind, protocol/rail, connector, pin) | new table; links reference ports | EI-10, harness persistence |
| D7 | `ModeElementRow` + `data_rate_bps`, `dissipation_w`, `line_state`; `ModeTransition` | columns + table | MO-01..07, EB-02/03/05 |
| D8 | `ThermalNode`/`Heater` persisted (element link, thermostat set-points) | new tables | EI-05, SX-07 |
| D9 | `Placement` (mount class, column, slot, z range, face, orientation, locked), `Deployable` | new tables | §4, EI-04, EI-07 |
| D10 | `TmParameter`, `HkStructure`, `Apid`, `TcFunction`, `EventDef`, `Monitor`, `FdirAction` (linked to elements, lines, FMECA rows) | new tables | FD-01..06, SX-02..05 |
| D11 | Risk register on the server, FMECA row id → risk id | table (s5 WP0 #9) | FD-03, RV-04 |
| D12 | Element: copy KB `dimensions_mm`, `interfaces`, `operating_temp_c`, `form_factor`, `heritage` on selection; drop `margin_percent` as a stored number (derive from `margin_policy`) | fix `_lookup_kb_component`, `apply_equipment_selection` | F3, F4, EB-01 |
| D13 | KB component schema v2: `mechanical {mount_class, envelope_mm, stack_height_mm, cog_offset_mm, connectors[]}`, `electrical {rails_in_v[], current_nom_a, current_peak_a, inrush_a, power_modes_w{off, standby, nominal, peak}, switchable}`, `data {buses[{protocol, default_address, configurable, max_rate_bps}]}`, `thermal {op_c, survival_c}`, `rf {band, ul/dl MHz, pa_levels_w, rate_tiers}`, `optical {boresight, fov_deg, exclusion_sun/earth_deg}`, `deployable {stowed_mm, deployed_geometry, release}`; new **payload/imager** category | KB YAML + loader | EB-02, EI-*, §4 |
| D14 | One margin ladder: `consistency_engine` reads `margin_policy.system_margin_percent(gate)` | code fix | F2 |
| D15 | `cds_rules.yaml` 6U/12U envelope and axis convention aligned with `geometry.yaml` (to verify against CDS 14.1) | config fix | F1 |

---

## 6. Top 15 rules missing today (priority order)

1. **IF-01** accepted interface → interface requirement(s) from type templates, with relation to the link; re-point **PDR-EC-02** to approved IRs + agreement (F5).
2. **EI-01 / EB-08** power line (switch) assignment with current = P/V, LCL limit, rail capacity and EPS `output_channels` check.
3. **EI-02** bus address plan: default from KB, unique per bus segment, max devices, bus load from exchange items (IF-07).
4. **EB-01** single maturity-margin source on elements (A–D 5/10/20 % from `margin_policy`), remove the hard-coded 5 % and 20 % (F3); one margin ladder (F2).
5. **MO-01 / MO-02 / EB-02** mode × element power proposals and per-mode power/energy balance from `ModeElementRow`.
6. **EB-03 / MO-03** mode data → storage → downlink chain on elements (retire the `payload.0.*` agent path).
7. **EB-05 / EI-05** per-mode dissipation into the thermal network; heater + thermostat + line as a proposed element from the cold case.
8. **FD-01 / FD-02** FMECA → S12 monitor → S19 action with valid function id and line; detection score from the monitor (F10).
9. **FD-03 / RV-04** single points and A/R-only verification → risk register entries.
10. **FA-04 / FA-02** functional exchange → interface proposal; product without function flagged.
11. **STACK placement (EI-04)** from mount class, writing `position_json`, so CDS-COG and AOCS closure run on real positions (F14).
12. **EI-07** optical keep-out vs deployables and boresight vs mode pointing.
13. **IF-03 / IF-04** staleness propagation link → IR (and KB change → element) through `inputs_hash`.
14. **RV-07 / PO-02** verification phase closure at its gate; bilateral interface ownership.
15. **SX-01..07** SMO export from the model (power lines, S12/S19, TC functions, geometry with internals, heaters) instead of hard-codes (F9).

Fit with the redesign work packages (s5): D1 = WP1; IF/RV/RG = WP5–WP6; EB/MO = WP4; EI/stack/diagrams = new WP "Physical architecture" (≈ 10–12 days, after WP4); FD/SX = new WP "Design → simulator export" (≈ 8 days, after WP10 schema work on the sim side); KB v2 + payload category = WP3 extension.
