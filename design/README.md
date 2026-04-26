# SpaceCDF — AI-Supported Concurrent Design Facility

SpaceCDF is a research tool for rapid, collaborative space mission design. It combines an agent-based design loop (convergence in 3–12 ms on a reference 6U CubeSat design) with real-time multi-user collaboration, NASA CEH-aligned cost estimation, requirement verification, equipment selection from a component knowledge base, and exports to simulator configs, design review documents, and flight software scaffolding.

**Status: Phase 4 complete.** 14 design agents (9 compute + 5 analysis including cross-domain conflict detection), 10 engineering positions, 106 components + 22 launch vehicles + 16 ground stations in the KB, WebSocket live collaboration, SQLite persistence, Monte Carlo cost risk, sensitivity analysis, EOL degradation, equipment browser, compliance matrix, cost breakdown, trade studies, and end-to-end exports (SMO config, docx/xlsx design review package, FSW C scaffolding).

---

## Quick start (local dev)

```bash
# One-off setup
cd SpaceCDF
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi 'uvicorn[standard]' pydantic pyyaml numpy scipy sgp4 jinja2 python-docx \
            'sqlalchemy[asyncio]>=2.0' aiosqlite openpyxl pytest pytest-asyncio

cd frontend && npm install && cd ..

# Start both servers (backend :8000, frontend :5173)
./scripts/start.sh

# Or individually
./scripts/start.sh backend    # uvicorn on :8000
./scripts/start.sh frontend   # vite on :5173
./scripts/start.sh design configs/examples/6u_eo_cubesat.yaml  # headless single-design run
```

Open `http://localhost:5173` in a browser. Left panel: requirements. Center tabs: Design / Positions / Compliance / Cost / Trade Studies. Right tabs: Insights / Conflicts / Exports. Top-left: SessionBar (click Start Session to collaborate).

---

## Architecture

```
frontend/               React + TypeScript + Zustand + @tanstack/react-query
  src/components/       SessionBar, EquipmentBrowser, ComplianceMatrix,
                        CostBreakdown, TradeStudyPanel, LiveEditToast,
                        HistoryDrawer, PositionPanel, ConflictsPanel,
                        InsightsPanel, ExportPanel, DesignWorkspace,
                        RequirementsPanel
  src/hooks/            useSession (react-query), useSessionSocket (WebSocket)
  src/stores/           designStore, sessionStore

packages/
  spacecdf-common/      Models (ParameterValue, Study, Requirement, Session),
                        physics engines (orbit, power, thermal, link, aocs,
                        propulsion, structure), agent base ABC
  spacecdf-agents/      14 agents (9 Tier 1 compute + 5 Tier 2 analysis),
                        orchestrator with Kahn's topological sort,
                        exporters (smo/, docs/ with Jinja2 + docx + xlsx, fsw/)
  spacecdf-server/      FastAPI with 36 endpoints + /ws/session/{id}
                        db/ (SQLAlchemy async + SQLite), services/
                        (session_manager, reconvergence, equipment,
                         cost_engine, verification, analysis)
  spacecdf-kb/          YAML knowledge base — components/, launch_vehicles/,
                        ground_stations/, cost_models/, standards/, positions/
```

---

## Key concepts

**Sticky parameters.** Parameters with `source = KB_COMPONENT` or `POSITION_OVERRIDE` or `REQUIREMENT` are never overwritten by agents during re-convergence. Agents compute *around* human selections. This invariant is enforced in `DesignState.update()` via `ParameterSource.is_sticky` and regression-tested in `tests/test_phase4_invariants.py`.

**Selective re-convergence.** When a single parameter changes (e.g. engineer selects a battery), only affected downstream agents re-run. Reverse dependency index built from agent `input_parameters()`/`dependencies()` declarations. Typical: 0.14 ms p50, 0.30 ms p95.

**Position-scoped editing.** Each of 10 engineering positions (Systems, Mission, Payload, Power, AOCS, Thermal, Comms, Propulsion, Structures, Cost) owns parameters via `fnmatch` patterns declared in `packages/spacecdf-kb/src/spacecdf_kb/data/positions/positions.yaml`. The WebSocket router validates ownership before accepting edits. Systems engineer can edit anything (arbitration fallback).

**Write-through persistence.** Parameter edits flow to an `asyncio.Queue`; a background worker drains and persists to SQLite (or Postgres via `DATABASE_URL`). The hot convergence path never awaits the DB.

---

## Performance (bench_phase4.py, Apple M-series)

| Capability | p50 | p95 | Budget |
|------------|-----|-----|--------|
| Full convergence | 3.0 ms | 4.3 ms | 100 ms |
| Selective re-convergence | 0.14 ms | 0.30 ms | 50 ms |
| Monte Carlo cost (n=1000) | 0.50 ms | 0.59 ms | 100 ms |
| Sensitivity sweep (7 points) | 23 ms | 25 ms | 500 ms |
| Compliance matrix build | 0.03 ms | 0.06 ms | 100 ms |

Run `python3 scripts/bench_phase4.py` to reproduce.

---

## Collaboration (Phase 4D)

1. Click **Start Session** in SessionBar → pick a position → session created, WebSocket connects.
2. Open another browser tab → **Start Session** → pick a different position → both see each other's avatars in SessionBar.
3. Edits are auto-broadcast. Engineer A selects a battery → Engineer B sees:
   - Toast: "Alice set power.battery_capacity_wh: ... → 77.0 [bat-gom-nanopow-bpx]"
   - Updated parameter values in all views
   - Convergence info in SessionBar: "Last reconv: 3 rounds, 0.4 ms, 16 params"
4. Click the **History** button bottom-left to open HistoryDrawer and see the audit trail of all edits (survives server restart).
5. Out-of-scope edits rejected at the server: Power engineer trying to set `aocs.mass_kg` → "Edit rejected" toast.

---

## Persistence (Phase 4C)

Sessions, studies, parameter edits, and periodic state snapshots are persisted to `spacecdf.db` (SQLite) by default. Override with `DATABASE_URL`:

```bash
export DATABASE_URL='postgresql+asyncpg://user:pass@localhost/spacecdf'
```

Schema is created via `Base.metadata.create_all` at startup (no Alembic migrations required). Snapshot cadence: every 10 edits.

Kill the server and restart — `GET /api/sessions/` shows persisted sessions with `persisted: true`. `POST /api/sessions/{id}/resume` rehydrates.

---

## Exports

- `POST /api/exports/smo/{study_id}` — ~20 YAML files for the SpaceMissionSimulation platform.
- `POST /api/exports/docs/{study_id}?review=srr|pdr|cdr` — zip containing Markdown + `.docx` (Word) + `master_budget.xlsx`.
- `POST /api/exports/fsw/{study_id}` — cFS-style C scaffolding driven by selected equipment.

All three are exposed via the **Exports** tab in the UI.

---

## Testing

```bash
# Full Phase 4 invariants suite
pytest tests/test_phase4_invariants.py -v

# All tests
pytest tests/ -v

# Latency benchmark
python3 scripts/bench_phase4.py
```

---

## Extending

**New agent.** Subclass `DesignAgent` in `packages/spacecdf-agents/src/spacecdf_agents/tier1/` or `tier2/`, declare `input_parameters()` and `output_parameters()`, add to `packages/spacecdf-agents/src/spacecdf_agents/registry.py` builtins dict.

**New position.** Add a block to `packages/spacecdf-kb/src/spacecdf_kb/data/positions/positions.yaml` with `key_questions` and `parameters` (owns patterns).

**New KB component category.** Add YAML file under `packages/spacecdf-kb/src/spacecdf_kb/data/components/`. The `/api/kb/components/{category}` endpoint auto-discovers them.

**New requirement type.** Extend `RequirementType` enum in `packages/spacecdf-common/src/spacecdf_common/models/requirements.py` and add generation logic to `generate_requirements()`.
