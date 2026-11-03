# SpaceCDF — AI-Assisted Concurrent Design Facility for Space Missions

SpaceCDF is an open-source web tool for collaborative spacecraft mission design, following the System-V model from NASA SEH and ECSS standards. A team walks in with a problem and walks out with a complete, buildable CubeSat design.

SpaceCDF is now part of the C2O repository, <https://github.com/FNewland/C2O>: it lives in the `design/` folder, next to the SMO mission simulator in `sim/`.

## What It Does

- **Mission Definition**: Problem statement, stakeholders, objectives, space vs non-space trade analysis (mission-type-aware, constellation options)
- **Requirements Engineering**: SMART requirements generation, traceability to objectives, suggest-then-approve workflow
- **Concept of Operations**: Mission architecture diagrams, phases, operational modes, data flow
- **Functional Decomposition**: Mission-type-aware function trees (comms/SAR/EO/generic) with multi-subsystem allocation
- **Design Sizing**: 20 parametric design agents (power, mass, AOCS, thermal, link, propulsion, cost, etc.) with CubeSat-calibrated mass/power fractions
- **Equipment Selection**: 18 component categories (150+ COTS components), RF compatibility checking, live budget tracking, multiple selections per category
- **Engineering Budgets**: Mass, power, cost, link, pointing — per-subsystem breakdown with ECSS margin enforcement
- **Trade Studies**: Tabular multi-criteria trades with weightings, thresholds, sensitivity analysis, plus parametric sweeps
- **Multi-Objective Optimizer**: NSGA-II Pareto with 10 objectives, 12 design variables, Morris screening sensitivity analysis
- **Constellation Design**: Walker delta configurations with coverage analysis and learning-curve costing
- **Beyond-LEO**: MEO, GEO, HEO, Lunar (NRHO), interplanetary with DSN link budgets and transfer ΔV
- **RF Spectrum & Licensing**: Amateur/experimental/commercial band database, ITU/IARU filing templates
- **Regulatory Paperwork**: RSSSA, export control (ITAR/EAR/CGP), COPUOS registration, end-of-life analysis
- **ECSS Document Generation**: MRD, TS, IRD, SEMP, RMP, ConOps, VP, VCD, Test Plan, Tailoring Matrix
- **Gate Reviews**: MCR exit criteria with "Go fix" navigation
- **Concurrent Design Sessions**: WebSocket real-time collaboration with 15 engineering positions
- **Cross-Tool Reactivity**: Stale detection, auto-reconverge, conflict review modal, impact preview, change audit with undo

## Architecture

```
frontend/          React + TypeScript + Zustand + Vite
packages/
  spacecdf-common/ Shared models, physics engines (orbit, power, thermal, debris, payload sizing)
  spacecdf-agents/ 20 design agents (9 Tier 1 sizing + 11 Tier 2 analysis)
  spacecdf-server/ FastAPI backend (105 API endpoints, 17 routers)
  spacecdf-kb/     Knowledge base (18 component categories, 150+ COTS, launch providers, validation missions)
configs/           ECSS standards, margin data, review gates, positions
docs/              Ultraplans, redesign architecture, validation results
scripts/           Mission validation harness
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Install & Run

```bash
git clone https://github.com/FNewland/C2O.git
cd C2O/design

# Backend
pip install -e packages/spacecdf-common
pip install -e packages/spacecdf-agents
pip install -e packages/spacecdf-kb
pip install -e packages/spacecdf-server
uvicorn spacecdf_server.app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Connect to Remote Instance
Edit `frontend/vite.config.ts` proxy target to point to the remote backend URL. For Tailscale access, see `docs/REMOTE_ACCESS.md`.

## Workflow

1. **Mission Need** (Step 1): Define problem, stakeholders, objectives
2. **Concept Exploration** (Step 2): Mission trade analysis — is space the right answer?
3. **Requirements** (Step 3): Orbit/class advisors, payload parameters
4. **Design** (Step 4): "Run Design" — 20 agents converge in seconds
5. **Iterate**: Equipment selection, trade studies, optimization, conflict resolution
6. **Export**: ECSS documents, regulatory filings, BOM, simulator configs

## Editing Parametric Data

View/edit via **Exports** tab → **Design Data** → **Parametric Model Data**, or API: `GET /api/lifecycle/parametric-data`. Returns mass fractions, cost fractions, power duty cycles, SA power tables — all editable. Source: `packages/spacecdf-common/src/spacecdf_common/physics/heritage_mass.py`.

## Updating Equipment Database

YAML files in `packages/spacecdf-kb/src/spacecdf_kb/data/components/`. Also supports CSV/JSON import: `POST /api/lifecycle/equipment/import`.

## Validation

Validated against 5 real missions (Spire LEMUR-2 Δ12%, Astrocast Δ6%, CAPSTONE Δ12%). Run: `python scripts/validate_missions.py`

## Standards

34 ECSS standards referenced, 12 fully implemented. See `docs/ULTRAPLAN2.md` for complete cross-reference.

## Seats, ownership and the instructor (WP9)

A study can be **solo** (no seats: everyone edits everything, as before) or have a team of
4, 6 or 7–9 people, chosen when the study is created (wizard step 4) or later by the Team
leader or the instructor (Seats panel). Seats, presets and ownership are data:
`configs/seats.yaml`. The server code is `packages/spacecdf-server/src/spacecdf_server/seats/`.

- **Seats.** Team leader, Systems, Mission analysis & ops, Payload, Power, AOCS, Comms & OBDH,
  Thermal, Structures & config (+ optional Propulsion, Cost & risk); Customer and Observer are
  shared. A person may hold several seats and picks the active one in the app bar.
  Free → Held → Idle (no heartbeat for 3 min) → reclaimable after 5 more minutes; "Request seat"
  gives the holder 60 s to answer; the instructor reassigns and locks seats. Every claim, handover,
  edit and review is logged with person and seat.
- **Ownership (decision 5).** Editing a value owned by another seat warns first ("owned by Power —
  your change goes to them for review"); if you continue it becomes a pending change the owning
  seat accepts or rejects. Until it is accepted the owner's value stands everywhere. The Team leader
  and the instructor follow the same rule unless they hold the owning seat.
- **Roles on the server.** Observer: read-only. Customer: reads the model, writes mission
  requirements. Gate review actions and the gate profile: Team leader or instructor. Deleting an
  element: its owning seat, the Team leader, Systems or the instructor. Deleting a study:
  instructor only. A frozen study refuses all writes except the instructor's.

**Who is the instructor.** Behind Google IAP the server reads `X-Goog-Authenticated-User-Email`.
Set `SPACECDF_INSTRUCTORS` (and/or `SMO_INSTRUCTORS`, the variable the ops tools use) to a
comma- or space-separated list of instructor e-mails; both lists are merged. Only a *verified*
(IAP) listed e-mail is an instructor. **Laptop mode** (no IAP): people type a name, shown as
"unverified"; if no instructor list is set, the first person who presses *Become instructor*
(Seats panel) is the instructor for that server. Until someone does, deleting studies stays open
so a single laptop user is not locked out. A hosted deployment must set the list.

The instructor's **class board** (start screen or app bar) shows every study × seat with the
holder, presence, raised hands and the current gate; it filters on "needs attention" (failed
must-pass item, idle seat, raised hand) and offers shadow (read-only), messages, timers, freeze,
customer requirement injects, sign-off of manual/hybrid gate items and the post-session
timeline export (CSV / Markdown, per person × seat).

## Current Status & Known Issues

See `docs/REDESIGN.md` for the architecture redesign plan addressing:
- System-V hierarchy (mission → system → subsystem requirements)
- Per-level engineering budgets (link, pointing, timing, data)
- Workflow-driven navigation (6 phases instead of 20+ tabs)
- Spectrum/licensing as design constraints
- Full V&V matrix with verification phases

## License

MIT

Diagrams are drawn with [React Flow](https://reactflow.dev) (xyflow, MIT
licence). The in-canvas attribution badge is hidden to keep the work area
clear; this note is the credit.
