# SpaceCDF — AI-Assisted Concurrent Design Facility for Space Missions

SpaceCDF is an open-source web tool for collaborative spacecraft mission design, following the System-V model from NASA SEH and ECSS standards. A team walks in with a problem and walks out with a complete, buildable CubeSat design.

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
git clone https://github.com/FNewland/SpaceCDF.git
cd SpaceCDF

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

## Current Status & Known Issues

See `docs/REDESIGN.md` for the architecture redesign plan addressing:
- System-V hierarchy (mission → system → subsystem requirements)
- Per-level engineering budgets (link, pointing, timing, data)
- Workflow-driven navigation (6 phases instead of 20+ tabs)
- Spectrum/licensing as design constraints
- Full V&V matrix with verification phases

## License

MIT
