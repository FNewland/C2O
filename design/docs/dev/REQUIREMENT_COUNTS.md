# Requirement counts of the Northern Fire and Ice study

Wave 2, agent R. For the agents whose tests or documents count requirements: what the
requirement store holds after each seed stage, where every row comes from, and which total a
document should quote. **Count from the store, not from a hard-coded number.** Use
`GET /api/studies/{id}/requirements/counts` (or `services.requirement_queries.requirement_counts`).

## 1. Where the rows come from

| Kind (`counts` key) | Codes | S0 | S1, S2 | S3, S4 | Made by |
|---|---|---|---|---|---|
| `stakeholder` | `SN-01` … `SN-06` | 0 | 6 | 6 | the bulk import (W2.01/W2.04): `stakeholder_needs` of `requirements.yaml`, level `stakeholder` |
| `objective` | `OBJ-O1` … `OBJ-O4`, `OBJ-C1` | 0 | 5 | 5 | W1.05: one mission-level row per mission objective ("The mission shall …"), parent = the need |
| `user` | the baseline (`MIS-`, `SEG-`, `SYS-`, `PAY-` … `IF-`) | 0 | 216 | 216 | the bulk import: the 216 rows of `requirements.yaml` |
| `generated_interface` | `IR-<type>-nnn` | 0 | 0 | 13 | rule IF-01 (`services/interface_requirements.py`) from the accepted links, at the S3 sync |
| **all** | | 0 | **227** | **240** | |

By level at S3/S4: stakeholder 6, mission 58 (53 baseline + 5 objective rows), segment 36,
system 40, subsystem 75, interface 25 (12 baseline `IF-*` + 13 `IR-*`).

The numbers wave-1 tests met:

- **221** = 216 baseline + 5 objective rows. This was the count before W2.01 added the
  stakeholder level and before the IF-01 rows existed in the seed.
- **227** = 221 + 6 stakeholder needs. Stages S1 and S2 (no interface requirement sync yet).
- **237** = 227 + 10 `IR-*` rows. Stages S3 and S4 on main after wave 1.
- **240** = 227 + 13 `IR-*` rows. Stages S3 and S4 after this change (section 2).

All of these are intended. The needs are the stakeholder level of the baseline (W2.01). The
objective rows make every objective a requirement that the rest trace to (W1.05, SRR-EC-01).
The `IR-*` rows are the IRD content of the links that no baseline `IF-*` row covers (IF-01,
W2.07). A test should take the expected total from `counts`, or from the fixture
(`len(ROWS) + len(objectives) + len(stakeholder_needs)`) plus `counts["generated_interface"]`.

## 2. The generated interface requirements (S3/S4)

The seed accepts 139 links. Of these, 109 need no row of their own:

- **internal**: inside one subsystem;
- **link**: a unit link under a subsystem link that has the row;
- **requirement**: covered by a baseline `IF-*` row on the same subsystem pair (W2.07).

17 templates have fewer than half of their values known. They are **suggestions**, not rows:
thermal contact ranges, heater power, mounts of AOCS, Communications, EPS and Harness, the
OBC → Thermal bus, ground TM/TC and the payload time reference. The 13 rows, with the parent
that the trace-word rule picks:

| Row | Parent | Text (short) |
|---|---|---|
| IR-SIG-001 | SEG-LS-01 | Launch Segment signals separation to the Space Segment (deployment switches, or an umbilical if the launch ICD provides one) |
| IR-DAT-001 | DIS-TRG-01 | Drag sail on I2C bus I2C-A, address 0x58, 400 kbit/s |
| IR-DAT-002 | SYS-DH-01 | EPS on CAN bus CAN-A, address 0x10, 1 Mbit/s |
| IR-MEC-001 … 004 | STR-ACC-01 | Drag sail, OBC (PC/104 stack), Payload and Thermal mount to the Structure |
| IR-THM-001 | THM-ALL-01 | OBC interface with the Structure within −30 to 85 °C |
| IR-THM-002 | THM-ALL-01 | Structure rejects the heat conducted from the Thermal |
| IR-SIG-002 | SYS-LCH-02 | EPS holds every Communications transmitter behind 3 inhibits, silent 45 min |
| IR-SIG-003 | EPS-INH-01 | Structure gives the EPS the deployment switch and RBF in the power path |
| IR-SIG-004, 005 | SYS-LCH-02 | OBC commands the wing and antenna release behind 3 inhibits, not before 30 min |

What the full import revealed on main, and what changed in wave 2:

| Finding (main after wave 1) | Fix |
|---|---|
| The 10 `IR-*` rows had no parent, so the SMART check failed "relevant / traceable" on all 10 (plus 7 other failures) | `parent_for`: the user requirement on either end (or on its subsystem, or on a `trace_domains` subsystem) whose text holds most of the template's `trace_words`; process rows are never parents |
| "on CAN bus TBD at address TBD at TBD bit/s" (3 rows): the subsystem link that carries the row has no bus node, while the unit link under it does | `fill_from_members`: a boundary row takes a value it lacks from the links it covers, when they all agree |
| Rows with fewer than half of their values known were still written (W2.07 made a suggestion only when *every* value was unknown) | `known_enough`: at least half of the values known, otherwise a suggestion |
| "provide the Space Segment with umbilical through at least TBD independent inhibits"; a deployment switch asked for an inhibit count | one template per signal kind: `IRT-SIG-INHIBIT`, `-RELEASE`, `-POWER-PATH`, `-SEPARATION`, `-GENERIC` |
| Two rows for one boundary (Structure → EPS deployment switch, and the RBF pin on the unit link under it) | links of one boundary are grouped by the templates they render, not by subtype |
| `OBJ-*` rows "not measurable"; SEG-LS-03 and HAR-DER-01 (levels set by the launch ICD and ECSS-Q-ST-30-11C) "not measurable" | SMART: an objective is measured by its success criterion; a requirement with a method whose text cites a document is measurable (as SRR-EC-02 already did) |

After the change, at S3/S4: SMART passes on 240 of 240 rows, there are 0 orphans, and every row
below the needs has a parent. Every objective is covered (the `direct` count is above 0 for
O1–O4 and C1).

Not fixed here (rule or proposer data, not requirements):

- The interface proposer makes I2C/SPI nodes of passive payload parts: the optical bench and
  the SWIR filter.
- It tags the A3200 → camera CSI-2 links as `tm_tc`.

These links are internal to the Payload or covered by IF-PAY-OBC-01, so they make no IRD row.
They do appear in the IRD dataset's bus nodes.

## 3. Which total a document quotes

| Document | Rows | S3/S4 |
|---|---|---|
| TS (W4.06), V&V matrix, verification plan | `specification`: every live row except the needs (`ts_rows`) | 234 |
| the same without generated rows | `specification_without_generated` (`ts_rows(include_generated=False)`) | 221 |
| IRD (W4.07) | `by_level["interface"]` (`ird_dataset()["requirements"]`) | 25 |
| MRD | the needs and the mission level | 6 + 58 |

The generated rows are drafts that need verification like any other (method T/I/A, stage CDR),
so the V&V matrix should list them. A document that wants only the written baseline uses
`include_generated=False`.

## 4. The queries (`services/requirement_queries.py`)

- `GET /api/studies/{id}/requirements/counts`: kinds, `by_level`, `by_ts_group`,
  `specification`, `specification_without_generated`, `all`.
- `GET /api/studies/{id}/requirements/ts-rows[?include_generated=false]`: `groups` (7, EN/FR
  labels, counts) and `rows`. Each row has `code, level, group, type, category, text, text_fr,
  rationale, unit, threshold, stage, methods, parents` (codes, every parent), `objectives,
  allocation, allocation_path, owner, priority, source, status, open_item, generated, tbd`.
  Rows are ordered by group, then by level and code. Groups: functional, performance, interface,
  environmental, operational, product_assurance, regulatory.
- `GET /api/studies/{id}/ird-dataset`:
  - `interfaces`: accepted links. Each has `from` and `to` (name, boundary subsystem, segment),
    `type`, `subtype`, `properties`, `line` (line no., LCL, rail and voltage, EPS), `node` (bus,
    protocol, address, rate, master), `exchange_items`, `requirements` (codes) and `covered_by`.
  - `segment_interfaces`.
  - `requirements`: the interface rows, with `origin` (rule, import or user), `template_id`,
    `icd_ref`, `interface_ids`, `covers_interface_ids`, `exchange_items`, `parents` and
    `missing`.
  - `exchange_items`, each with its `interfaces` and `requirements`.
  - `suggestions`, `status` (PDR-EC-02) and `counts`.
- `GET /api/studies/{id}/requirements/coverage` also lists `interface_without_parent`.

From Python: `await requirement_counts(sid)`, `await ts_rows(sid)`, `await ird_dataset(sid)`. The
pure helpers are `ts_group(row)`, `counts_of(rows)` and `threshold_text(row)`.
