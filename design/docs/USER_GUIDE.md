# SpaceCDF User Guide

## Overview

SpaceCDF is an AI-assisted Concurrent Design Facility for space mission design. It guides you from problem definition through to a complete, verified CubeSat design with ECSS-compliant documentation.

---

## Getting Started

### Installation

**Prerequisites:** Python 3.11+, Node.js 18+

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
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 in your browser.

### Connecting to a Remote Instance

Edit `frontend/vite.config.ts` and change the proxy target:
```javascript
proxy: { '/api': 'http://REMOTE_HOST:8000' }
```

---

## Workflow

### Step 1: Mission Need

1. Click **Step 1 (Need)** in the left stepper
2. Enter your **problem statement** (WHAT, not HOW)
3. Add **stakeholders** with roles and needs
4. Define **objectives** with measurable success criteria
5. The tool auto-detects mission type from objective keywords

### Step 2: Concept Exploration

1. Click **Step 2 (Concept)**
2. Enter trade parameters: GSD, revisit, coverage, latency, budget
3. Click **"Run Analysis"** to evaluate space vs non-space alternatives
4. Review scored results → the tool indicates whether space is justified

### Step 3: Requirements

1. Click **Step 3 (Requirements)**
2. **Orbit Advisor:** Enter targets, click "Compute" → scored orbit candidates. Click "Use" to apply.
3. **Class Advisor:** Enter known parameters (all optional). Click "Compute" → spacecraft class recommendation.
4. Set orbit, payload, and mission parameters in the form
5. Click **"Run Design (solo)"** → 20 agents converge the design

### Step 4: Design Phase

After running the design, the tool switches to the tabbed design workspace organised into 5 groups:

**Design:** Dashboard, ConOps, Functions, Requirements, Interfaces
**Analysis:** Link Budget, Trade Studies, Optimizer, Cost
**Verify:** Compliance, V&V Matrix, Gate Review
**Team:** Positions, Q&A
**Data:** Exports, Parametric, Changes, Help

---

## Key Features

### Dashboard

The main design view showing:
- **KPI cards:** Mass margin, power margin, link margin, cost, sustainability, reliability, conflicts
- **Mass waterfall** and **power profile** charts
- **Budget Breakdown:** Per-subsystem mass/power with editable allocations
- **Engineering budgets:** Pointing (RSS), Data (pipeline flow), Timing (orbit timeline)
- **Spectrum Selector:** Choose license type and frequency band
- **Launch Selector:** Pick a provider with live mass allocation update
- **ECSS Margin Enforcement:** Per-domain margin vs policy check

### Equipment Browser

Click "Equipment" in the header bar:
- **18 categories** grouped by domain (Power, AOCS, Comms, Propulsion, Structure, Data, Thermal, Integration)
- **Need annotations:** Blue dot = required, circle = optional, dimmed = not needed
- **Multiple selection:** Select multiple items per category (e.g., 4 reaction wheels)
- **RF compatibility:** Warning when selecting mismatched transponder/antenna bands
- **Live budget bar:** Running mass/power/cost totals
- **Compare mode:** Side-by-side comparison of up to 3 components

### Trade Studies

Two modes:
- **Parametric Sweep:** Vary one parameter, see effect on key metrics (chart)
- **Tabular Trade:** Define criteria with weights, add options, score quantitatively or qualitatively (low/medium/high), see ranked results

### Link Budget Tool

Full interactive cascade: TX power → antenna gain → losses → FSPL → atmospheric/pointing/polarisation → RX gain → G/T → C/N₀ → Eb/N₀ → margin. Each term editable, margin color-coded.

### Optimizer

- **Single objective:** Minimise mass, cost, or maximise link margin
- **Pareto (NSGA-II):** Multi-objective with up to 10 objectives
- **Mission-type aware:** Variables auto-filtered based on mission (no propulsion vars without propulsion)
- **Sensitivity (Morris):** Ranks which parameters most influence the objective

### Exports

Generates 18+ document types:
- **ECSS:** MRD, TS, IRD, SEMP, RMP, ConOps, VP, Test Plan
- **Regulatory:** ITU API, IARU coordination, RSSSA, export control, COPUOS, EOL report
- **Design data:** Parametric model data, duty cycles, consistency check, margin enforcement

### Cross-Tool Reactivity

- **Design State Bar:** Shows when design is outdated after any parameter change
- **Auto-Reconverge:** Optional toggle → re-runs design automatically after each edit
- **Conflict Review:** Modal appears when critical conflicts detected; requires resolution
- **Impact Preview:** Shows which agents and budgets a change will affect before accepting
- **Change Audit:** Full history with undo capability

### Analyses tab (workbench)

The Level Workbench has an **Analyses** tab (bottom panel, after Decide). It shows one card per engineering analysis, with the last run time, an `ok` / `stale` / `failed` badge (stale = the model changed since the run), two or three headline numbers from the run summary, the number of open conflicts it raised, and a **Run** button. Click a card to open its full panel below the grid; the **Options ▸** button opens the A/B option comparison. A **Conflicts** list at the bottom merges the design-loop conflicts with every analysis' conflicts (source badge, severity, element chips — click one to focus that element in Blocks — the suggested fix, and **Resolve**).

The active design option is chosen in the **Option** switcher in the presence bar (top left area, next to the AI status). Every run and every parameter read on this tab is scoped to that option; the baseline sends no option.

What each analysis needs from the model before its result means anything:

| Card | Reads | Writes (mission root) | Needs |
|------|-------|----------------------|-------|
| Design loop | requirements, subsystems by domain | agent parameters, budgets | a mission root with orbit / payload / lifetime requirements and subsystems with a `subsystem_domain` |
| Mission simulation | operational modes, battery `capacity_wh`, array `sa_power_eol_w`, payload `data_rate_bps`, orbit | `sim_min_soc_pct`, `sim_energy_balance_wh_per_orbit`, `sim_data_backlog_end_gb`, `sim_time_in_safe_pct` | at least one operational mode (ConOps) with power and data rate; a battery and a solar array under the power subsystem |
| Ground segment | selected ground stations, TT&C band / rate, orbit, generated data | `gs_contact_min_per_day`, `gs_data_return_gb_per_day`, `gs_data_generated_gb_per_day`, `gs_min_link_margin_db` | one or more ground stations selected from the catalogue (Ground segment panel → add), a radio in the comms subsystem with a band the station supports |
| Physics | component masses / dimensions / body positions, reaction wheel, pointing requirement, dissipations | `mp_*` mass properties, `aocs_*` torques and wheel margin, `thermal_worst_margin_c` | masses on components; positions (Physics panel → placement, or auto-placed inside the structure envelope); a wheel or a pointing requirement for the AOCS part; dissipations for thermal |
| V&V | requirements with verification method and threshold parameters | `vv_closure_pct`, `vv_items_*` | requirements carrying a threshold (`param op value`); analysis runs then close those items automatically |
| FMECA | components with domain, quantity / redundancy, allocated functions | `fmeca_max_rpn`, `fmeca_single_point_failures` | functions allocated to components (Functions tab) so single points on critical functions are found |

The margin bar under the status bar gains **SoC** (minimum battery state of charge from the simulation, against a 20 % floor) and **Data** (fraction of the generated data actually returned) as soon as those parameters exist on the mission root.

---

## Editing Parametric Data

The tool's sizing models use CubeSat-calibrated data. To view and edit:

1. Go to **Parametric** tab
2. Four sub-tabs: Mass Fractions, Cost Fractions, Power Duty Cycles, SA Power
3. Values are per spacecraft class (nano, micro, small, medium, large)
4. Sources cited alongside each table

To edit the source data directly: `packages/spacecdf-common/src/spacecdf_common/physics/heritage_mass.py`

---

## Updating Equipment Database

Component data is in YAML files: `packages/spacecdf-kb/src/spacecdf_kb/data/components/`

To add a component, add an entry to the appropriate YAML file:
```yaml
- id: unique-id
  name: "Component Name"
  manufacturer: "Vendor"
  mass_kg: 0.15
  power_w: 8.0
  cost_keur: 30
  trl: 8
  frequency_band: S  # for RF components
```

The API also supports import: `POST /api/lifecycle/equipment/import`

---

## Concurrent Design Sessions

1. Click **"Start Session"** in the header
2. Select your position(s) and enter a display name
3. Share the URL with team members → they join the same session
4. Edits propagate in real-time via WebSocket
5. Each position can only edit their owned parameters
6. Convergence runs automatically after each edit

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+Enter | Run Design |
| Escape | Close modal |

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| "Socket not connected" | Start or join a session first for equipment selection |
| Design shows no results | Click "Run Design" in Step 3 |
| Requirements tab empty | Need a study ID → run design at least once |
| Optimizer won't start | Need a session (or use 'solo' mode) |

---

## New Features (UP6)

### Progressive Level Unlocking

The tool now follows the System-V model with 5 progressive levels:
- **Level 0**: Help only (define mission need first)
- **Level 1**: Mission Architecture (after need defined) — ConOps, Functions, Requirements
- **Level 2**: System Architecture (after design run) — Architecture options, Interfaces, Budgets, Trade Studies, Project Management
- **Level 3**: Subsystem Design (after architecture selected) — Link Budget, Optimizer, Cost, Equipment Browser
- **Level 4**: Verification (after subsystem design) — Compliance, V&V Matrix, Gate Review

The level indicator bar shows your current progress and what to do next.

### Interactive Mission Architecture Editor

In the ConOps tab, a drag-and-drop diagram editor lets you build your mission architecture:
- **6 node types**: Satellite, Ground Station, Processing, User, Sensor, GNSS/External
- Drag nodes to position, connect with labelled lines
- Architecture drives what systems need to be defined at the next level

### System Architecture Selection

In the Architecture tab:
- **Top half**: Select architecture options for each of 8 subsystems (EPS, AOCS, TTC, Thermal, Structure, Propulsion, OBC, Ground)
- **Bottom half**: Auto-generated block diagram showing subsystems and their connections
- Each selection derives requirements (tagged performance/interface/budget/functional)

### Engineering Budgets (Unified View)

New "Eng. Budgets" tab shows all 8 budgets in one place:
- Mass, Power, Link, Pointing, Delta-V, Volume, Data, Cost
- **Configurable margins** by design phase (Phase A: 20%, B: 15%, C: 10%)
- Per-subsystem breakdown with margin source (COTS vs new design)
- Roll-up from equipment selections

### Constraint Propagation Engine

187 design point interconnections detected automatically:
- When any parameter changes, the engine identifies ALL affected budgets
- Shows resolution options for violations with cross-budget trade-off analysis
- Detects circular dependencies (trade-off loops requiring team decision)

### Project Management

New "Project Mgmt" tab with:
- **5x5 Risk Matrix**: Interactive, color-coded by L×C score
- **Schedule**: 10 milestones from MCR through commissioning
- **WBS**: 9 work packages with effort hours and status tracking
- **Project Manager** position added

### Word Document Export

ECSS documents can now be exported as editable .docx files:
- Click "Word" button next to MRD, ConOps, or VP in the Exports tab
- Documents populated from live design state
- Editable in Microsoft Word or LibreOffice

### Session Persistence

Your design state now persists across page refreshes:
- All data saved to browser localStorage automatically
- No need to "save" — it's always saved
- To clear: browser DevTools → Application → Local Storage → delete 'spacecdf-design-state'
