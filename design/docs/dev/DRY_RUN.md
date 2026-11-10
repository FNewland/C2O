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
| AIT model philosophy, test matrix, verification plan | V&V view, once `AitPanel` is mounted there (hand-off to D); until then `GET /api/studies/{id}/ait` and `…/ait/verification-plan?fmt=docx` | S4 |
| Licensing (filings, ISED / ITU / RSSSA documents) | its own workbench tab once mounted (hand-off from L); until then the Export drawer's regulatory group | not seeded |
| Review packs (MDR, PRR, SRR, PDR…), every document and data export, project file | header **Export** | all |

## 5. What to check

- The seed printed 0 × 403 and no `FAILED` line.
- The ground-segment run lists all four UHF stations as `ok` (the analyses take the band from the
  design link case; with an empty mission link they take the design case, then the TT&C equipment).
- The debris score counts the drag sail (`deorbit.drag_area_m2` = 2.1 m² on the design state), so
  MDR-EC-10 and PRR-EC-12 pass once a design loop has run.
- Export → project file, then Load it as a new study: the round trip of
  `design/tests/fixtures/nfi/roundtrip_checklist.yaml`.
