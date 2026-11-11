# Dry run: the Northern Fire and Ice study in the live tool

How to run the integration dry run (plan W13) before the walkthrough is recorded: start the
server on a fresh database with a freshly built frontend, seed the Northern Fire and Ice study
(prefix `nfi`) through the API up to the stage you want to show, then open it in the browser.

Paths are relative to the repository root. The seed is the one the fixture tests use
(`design/tests/fixtures/nfi/seed.py`, stages in `W0_SEAMS.md` §5).

## 1. Start the server

```bash
cd video
python3 -m c2ovideo stack up spacecdf        # SpaceCDF on http://127.0.0.1:18800
```

- The frontend is rebuilt first (`vite build` in `design/frontend`) when `dist/` is missing or older
  than a source file, so the page is always the one of this checkout. `C2O_VIDEO_NO_BUILD=1`
  refuses a stale build instead of rebuilding it.
- The database, data folder and logbook are new on every `up` (`video/out/_stack/spacecdf/`).
  The server log is `video/out/_stack/spacecdf.log`.
- Another port: `C2O_VIDEO_SPACECDF_PORT=19010`. Another Python: `C2O_VIDEO_SPACECDF_PYTHON=…`
  (by default `design/.venv`, or in a git worktree the main checkout's `design/.venv`; the server
  always imports this checkout's packages).
- Stop it with `python3 -m c2ovideo stack down spacecdf`.

## 2. Seed the study

From `design/`, with the server's Python (it needs `httpx`):

```bash
design/.venv/bin/python -m tests.fixtures.nfi --url http://127.0.0.1:18800 --stage S4
design/.venv/bin/python -m tests.fixtures.nfi --url http://127.0.0.1:18800 --stage S0 S1 S2 S3 S4
```

Each stage given builds one **new** study from scratch up to that stage, and prints its id, the
number of calls, the 403 count (must be 0) and the seconds per stage. S4 takes about 15 s on a quiet
machine and a minute or more when the machine is busy.

| Stage | Show it for |
|---|---|
| S0 | The mission definition and the mission need, before any design |
| S1 | Product tree, ground stations, the requirement baseline (bulk import) |
| S2 | Equipment, budgets, modes and ConOps phases, link cases |
| S3 | All requirements, risks, interface requirements, trades, the MDR review |
| S4 | CDR model, stack, analyses, AIT and schedule, HK SIDs: the full study |

To walk a stage by hand instead (the script's UI steps), seed the stage before it and do the next
stage's steps in the UI.

## 3. Open it in the browser

Open `http://127.0.0.1:18800/?study=<id>` with the id the seed printed, enter a name and join
(the seed creates the study solo, with no team size). "Close study" goes back to the start screen;
the study stays on the server.

## 4. Where each feature lives

The workbench has a breadcrumb (product-tree level, then **V&V**), a tab strip (activity panels)
and the header buttons **Export**, **Guide**, **Save** and **Load**.

| Feature | Where | Seeded at |
|---|---|---|
| Mission need, mission definition (orbit, node time, link, launch, disposal), ConOps phases | **Traceability** tab: the mission-need card at the top (edit opens the mission definition editor) | S0, S2 |
| Product tree, blocks, segments | **Blocks** tab; the breadcrumb drills into an element | S1 |
| Requirements (table, levels, parents, objectives, bulk import), interface requirements | **Requirements** tab | S1, S3 |
| Mass, power and data budgets (one roll-up), margins by gate | **Budget** tab: Mass, Power, Data | S2 |
| Schedule, WBS, long-lead items, bottom-up cost | **Budget** tab → **Cost** (project view) | S4 |
| Modes, power matrix, energy balance, ConOps data flow | **Modes** tab | S2 |
| Interfaces, ICD | **Interfaces** and **ICD** tabs | S2, S3 |
| Electrical (buses, rails, power lines), data buses | **Electrical** and **Data** tabs | S2 |
| CDR model: TM/TC with HK SIDs, FDIR, AOCS modes, operations | **TM/TC**, **FDIR**, **AOCS modes**, **Operations** tabs | S4 |
| Trades (Pugh), decision records | **Decide** tab | S3 |
| Link budget (term by term, named cases, apply as design case) | **Analyses** tab → **Link budget** | S2 |
| Ground segment, physics (stack, thermal), mission simulation, V&V runs | **Analyses** tab | S4 |
| Diagrams | **Diagrams** tab | all |
| Gate reviews, criteria, RIDs, review record, risks, verification matrix | breadcrumb **V&V** (level 4) | S3, S4 |
| AIT model philosophy, test matrix, verification plan | **V&V** → **Traceability** → the AIT panel | S4 |
| Licensing (applicant, protection plan, data policy, frequencies, disposal; the eight documents; filings) | **Licensing** tab; progress counter "RSSSA §14–30: n of m" | S4 (full seed); filled on camera on the recording seed |
| Debris assessment (run, accept at a gate) | **Licensing** tab → Disposal → Debris assessment card | run on camera (SRR) |
| **Phase card**: Before you start, Deliverables this phase (✅ / ⚠️ / ❌, Fix, Draft it), Analysis standard; coaching card; protocol checks Warn / Block / Off | **V&V** → Review Gates → a gate → top of the gate view (also the **Guide** drawer for the coaching) | S0 |
| SEMP issue (SRR-EC-09) | Phase card → **Systems engineering management plan** → Record the SEMP issue | issued on camera (SRR) |
| Stage-transition inventory | **Start review** on any gate (what is missing is written to the gate history in Warn mode) | — |
| Stakeholders (interest, authority), MOEs | **Traceability** → mission-need card → Stakeholders | S0 |
| Allocation ledger (one line per subsystem and resource, system reserve, agree / dispute) | **Budget** → Mass or Power → Allocation ledger; Performance under Data | S2 (full seed); proposed and agreed on camera on the recording seed |
| Function links, coverage, FFBD | **Requirements** (Function column); **Functions**; **Diagrams** → Functional flow block diagram | S1 |
| System-level trades (level, gate, MOE sources, absolute scale, ±20 %, evidence per criterion, conditions) | **Decide** → Trade studies (select by id; the summary by gate on top) | S3 |
| Negotiations (GS4 ripple, N1, N3, N7: options computed, choose, every seat signs, reopen trigger) and the sensitivity strip | **Decide** → Negotiations; Sensitivity below it | S3/S4 (full seed); opened and signed on camera on the recording seed |
| Change proposals and change control (impact preview, seats agree, approve or reject, requirements updated, new baseline revision) | **Decide** → Change control (ECP-01, ECP-02, CR-V2); Changes below | S3 (proposed) |
| Open items (RIDs, conditional decisions, PI decisions, undecided trades, changes; the gate each blocks) | **Decide** → Open items | S3 |
| Validation activities and need validation | **V&V** → **Traceability** → the AIT panel → Validation | S3 |
| Assumption register | Phase card → Analysis standard | S3 |
| ICD issues (Issue A, provider and consumer sign-off) | **ICD** tab | S3 inventory; issued on camera (PDR) |
| Reliability block diagram, FMEA | **V&V** → **Traceability** → the AIT panel → Reliability | run on camera (PDR) |
| Thermal nodal model (nodes, couplings, hot and cold cases, sized heaters) | **V&V** → **Traceability** → the AIT panel → Thermal model | built on camera (PDR) |
| Cost pricing (labour, test campaigns, reserve; launch provided) | **Budget** → **Cost** → Price | priced on camera (MDR) |
| Systems-engineering diagrams (context, stakeholder map, FFBD, V diagram, trade matrix, budget flow-down, verification flow) | **Diagrams** → group "Systems engineering (the V)"; each also from the Phase card | all |
| Example project (this study at the end of the dry run) | Home → **Load Example Mission** → Northern Fire and Ice; the file is `configs/examples/nfi/project.json` | — |
| Review packs (MDR, PRR, SRR, PDR…), every document and data export, project file | header **Export** | all |

## 5. What to check

- The seed printed 0 × 403 and no `FAILED` line.
- The ground-segment run lists all four UHF stations as `ok` (the analyses take the band from the
  design link case; with an empty mission link they take the design case, then the TT&C equipment).
- The debris score counts the drag sail (`deorbit.drag_area_m2` = 2.1 m² on the design state), so
  MDR-EC-10 and PRR-EC-12 pass once a design loop has run.
- Export → project file, then Load it as a new study: the round trip of
  `design/tests/fixtures/nfi/roundtrip_checklist.yaml`.
  `tests/fixtures/nfi/test_w3_close.py` checks it on the finished study: every table, every row of
  the frozen v1 checklist and every wave-3 object comes back identical after id mapping.
- The recording scenes and the reviews, in order: `design/docs/dev/DESIGN_SCRIPT_V2.md`; the same
  actions as API calls: `tests/fixtures/nfi/test_w3_integration.py`.

## 6. Dry-run record (3.F1, 2026-11-10, branch nfi-close)

**How it was run.** In-process (the app over a fresh SQLite database) and against a server started
on a fresh `vite build`: the recording seed (`--stage S4 --recording`), then every on-camera scene
of the script through the API, with the gate table read after each scene; then every gate pack
(MDR … FRR, English and French, zip and Markdown), every licensing document (8 kinds, JSON and
docx), the MRD, ConOps and SEMP, and the project export → import → export. The UI path of each
closing scene was driven with headless Chromium (Playwright) on the built frontend.

**Seed time.** S4 recording seed 15–17 s in-process, 16 s over HTTP (832 calls, 0 × 403);
S0 0.7 s, S1 0.9 s, S2 5.9 s, S3 3.7 s, S4 6.0 s.

**Gate table after each scene (recording seed; must-pass met / total, open must-pass).**

| After | MDR | PRR | SRR | PDR |
|---|---|---|---|---|
| seed S0 | 5/6 | 2/5 | 2/8 | 1/9 |
| seed S1 / S2 | 5/6 | 4/5 | 4/8 | 2/9 |
| seed S3 | ready 6/6 | ready 5/5 | 5/8 | 2/9 |
| recording seed S4 | ready | ready | 5/8 (SRR-EC-09, SRR-EC-10, SRR-RD-03) | 4/9 (PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04) |
| cost priced, Licensing filled | ready | ready | 5/8 | 4/9 |
| allocation ledger agreed | ready | ready | 5/8 | 5/9 (PDR-EC-07 passes) |
| negotiations GS4, N1, N3, N7 signed | ready | ready | 5/8 | 5/9 |
| SEMP Issue A | ready | ready | 6/8 | 5/9 |
| debris assessment accepted | ready | ready | 7/8 | 5/9 |
| ECP-02 approved | ready | ready | **ready 8/8** | 5/9 |
| MDR, PRR, SRR passed | passed | passed | passed | 5/9 |
| five PDR ICDs at Issue A, signed | | | | 6/9 |
| reliability (0.8805 over 12 months) and FMEA | | | | 7/9 |
| thermal model, heaters taken, solved | | | | 8/9 |
| T-A01 decided A (conditional), ECP-01 rejected | | | | **ready 9/9** |
| PDR passed | passed | passed | passed | passed |

**Protocol deliverables MDR–PDR at the end.** All ✅ except two, each with its reason:
MDR-DL-03 ⚠️ (MOE-04 and MOE-10 carry example thresholds and stay "to co-define" with the
communities: PI ruling, 2026-11-10); PDR-DL-08 ⚠️ (10 ICDs under issue control, the 5 due at the
PDR at Issue A and signed by both seats; the other 5 are due at the CDR).

**Packs.** All eight gate packs build in English and French (16–29 documents each). The open-item
lists hold no placeholder for derivable data after the fixes below; what they list is real open
work: MOE-04/10 to co-define, 4 performance requirements without a threshold, 17 requirements not
allocated, Harness without equipment, 3 open risks scored ≥ 16, the PDR seat decisions (D-GND-01,
D-GND-02, D-PAY-01, D-COM-01), 14 assumptions due at the PDR, FMEA single-point failures, units
below TRL 6, and the design alarms the figures show (LCL ratings, stack faces, critical risks).

**Licensing documents.** All 16 build. What they leave as "[APPLICANT INPUT REQUIRED]" is only what
the applicant alone can supply (personnel and physical security, backup facility, data disposal,
priority access, launch site and provider, affiliates, security screening): RSSSA 9, ISED space 1,
ISED earth 4 (JSON); none in ITU API, debris, UN registration, status. The export-control summary
carries two TBC items (camera classification).

**Round trip.** Export → import → export of the finished study: 0 tables or rows differ after id
mapping, no import warning; the checklist test passes.

**Name gate.** 6 384 generated files and documents scanned: 0 hits; the repository: 0 hits.

**UI path (headless, built frontend).** OK for: Traceability mission-need card and stakeholders;
Budget → Cost → Price; allocation ledger propose and agree; Decide → Negotiations (GS4 from its
template); V&V → SRR Phase card → Record the SEMP issue; Licensing tabs (Applicant input, Documents,
Disposal → Run the assessment, accept); Decide → Change control ECP-02 (start, every seat agrees,
approve, "Requirements updated"); ICD tab (Issue, provider and consumer sign-off); V&V →
Traceability → Reliability, Thermal model, Validation panels; T-A01 evidence lines, conditions and
the ±20 % line; ECP-01 card; Diagrams → V diagram. No page error.

**Found and fixed.**

1. `<GATE>-SE-01` (SE deliverables) was never evaluated: `routers/gates.gate_inputs` reused its
   `gates` parameter for the profile's gate list, so the deliverables evidence was collected for
   no gate. Fixed (local renamed); checked in `test_w3_close`.
2. The thermal model's sized battery heater came out 0.01 W short on the full solve (sized on the
   coarse transient), so the battery stayed 0.08 °C below its design range and PDR-RD-03 failed on
   the recording seed. `accept_heaters` now adds a 10 % sizing margin.
3. The change-control card showed "no change to the key numbers" for ECP-02: it read `deltas`, while
   the impact preview answers `lines`. The card now lists the preview lines.
4. ECP-02 had no `apply` list, so its approval edited nothing. It now carries edits to SEG-LS-02,
   MIS-COV-03 and PAY-OPT-04; the card lists "Requirements updated".
5. The T-A01 teaching scene needs the evidence per criterion and the trade's conditions on screen;
   the absolute-scale matrix now shows both.
6. Packs printed "the model lacks data" for figures that have data but show design alarms (risk
   matrix with 37 risks); they now name the alarm. The figure table filled its `{{n}}` placeholders.
7. Packs listed "FMECA: not run": the seed now runs the FMECA analysis with the others at S4 (script
   scene 5.9). The cost is priced in the walkthrough (`mdr_actions`), as the PI asked.

**Left open, with the reason.** The thermal node diagram still reads the parametric thermal
analysis (11 nodes out of range), not the nodal model that passes the PDR: owner A, not needed by
any scene (the scene shows the Thermal model panel). The weight inputs of the absolute-scale matrix
are a little narrow for two decimals (cosmetic).
