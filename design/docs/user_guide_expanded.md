---
title: "SpaceCDF User Guide"
subtitle: "AI-assisted Concurrent Design Facility — operator's reference"
course-codes: "SpaceCDF · v6"
term: "2026"
version: "v2 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
footer-en: "SpaceCDF User Guide · 2026"
footer-fr: "Guide d'utilisation SpaceCDF · 2026"
running: "SpaceCDF — User Guide"
---

# User Guide

## What SpaceCDF is

**SpaceCDF** is an AI-assisted Concurrent Design Facility for space
mission design. It guides you from problem definition to a complete,
verified CubeSat preliminary design with ECSS-compliant
documentation. The tool sits at the centre of the CDF intensive
described in the *Course Plan* and the *Facilitator's Book*.

The platform is implemented as a Python backend and a web frontend.
You run it locally for solo work, or as a shared server for
concurrent team sessions where each user occupies a CDF position
(Power, AOCS, Comms, Payload, etc.).

> **Expected reading.** Before opening the tool for the first time,
> skim the *3-Week Syllabus* and *Course Plan* (this PDF set). They
> describe the workflow this guide assumes you know.

![Lifecycle phases — what SpaceCDF helps you do where](../assets/figures/fig_lifecycle.png)

*Figure 3.1 — SpaceCDF carries you from Pre-Phase A (mission need)
through end of Phase B (PDR). Operations (Phase E) is covered
separately by the EOSAT-1 simulator and Week 3 packs.*

---

## Getting started

### System requirements

| Component | Requirement |
|-----------|-------------|
| OS | macOS 13+, Ubuntu 22+, Windows 10/11 (WSL2 recommended) |
| Python | 3.11 or newer |
| Node.js | 18 LTS or newer |
| Browser | Chrome 120+ / Safari 17+ / Firefox 120+ — Edge 120+ |
| RAM | 8 GB minimum, 16 GB recommended |
| Disk | 4 GB free for source + database |

### Installation (local)

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

Open `http://localhost:5173` in your browser.

### Connecting to a remote instance

Edit `frontend/vite.config.ts` and change the proxy target:

```javascript
proxy: { '/api': 'http://REMOTE_HOST:8000' }
```

This routes API and WebSocket traffic to your shared CDF server.
For Cyberrange-hosted teaching, the `REMOTE_HOST` is provided in
Brightspace at start of Week 2.

---

## Workflow at a glance

The five-step workflow follows the System-V (see *Course Plan*
Figure 2.2). Each step has a dedicated screen and a recognisable
gate to the next:

| Step | Screen | Gate to next | Course session |
|------|--------|--------------|----------------|
| 1 — Need | Stepper · Step 1 (Need) | Stakeholder map + objectives written | 1.2 |
| 2 — Concept | Stepper · Step 2 (Concept) | Mission alternatives traded; archetype chosen | 1.3 – 1.4 |
| 3 — Requirements | Stepper · Step 3 (Reqs) | Orbit / class chosen, design loop run | 2.1 – 2.4 |
| 4 — Design | Tabbed workspace (5 groups) | Subsystems converged, interfaces clean | 3.1 – 4.4 |
| 5 — Review | Gate Review tab | PDR exit criteria met | 5.1 – 5.4 |

### Step 1 — Mission need

1. Click **Step 1 (Need)** in the left stepper.
2. Enter your **problem statement**. *WHAT not HOW* — see Course
   Plan §2.1.
3. Add **stakeholders** with role and need.
4. Define **objectives** with measurable success criteria.
5. The tool auto-detects mission type from objective keywords.

### Step 2 — Concept exploration

1. Click **Step 2 (Concept)**.
2. Enter trade parameters: GSD, revisit, coverage, latency, budget.
3. Click **Run Analysis** to evaluate space vs non-space alternatives.
4. Review scored results — the tool indicates whether space is
   justified.

### Step 3 — Requirements

1. Click **Step 3 (Requirements)**.
2. **Orbit Advisor:** enter targets, click **Compute** → scored
   orbit candidates. Click **Use** to apply.
3. **Class Advisor:** enter known parameters (all optional). Click
   **Compute** → spacecraft class recommendation.
4. Set orbit, payload, and mission parameters in the form.
5. Click **Run Design (solo)** → 20 agents converge the design.

### Step 4 — Design phase

After running the design, the tool switches to a tabbed design
workspace organised into five groups:

| Group | Tabs |
|-------|------|
| Design | Dashboard · ConOps · Functions · Requirements · Interfaces |
| Analysis | Link Budget · Trade Studies · Optimizer · Cost |
| Verify | Compliance · V&V Matrix · Gate Review |
| Team | Positions · Q&A |
| Data | Exports · Parametric · Changes · Help |

### Step 5 — Review

Use the **Gate Review** tab to walk through PDR exit criteria.
Resolve action items inline. Generate the ECSS document set from
the **Exports** tab.

---

## Key features

### Dashboard

The main design view showing:

- **KPI cards:** mass margin, power margin, link margin, cost,
  sustainability, reliability, conflicts.
- **Mass waterfall** and **power profile** charts.
- **Budget breakdown:** per-subsystem mass / power with editable
  allocations.
- **Engineering budgets:** pointing (RSS), data (pipeline flow),
  timing (orbit timeline).
- **Spectrum selector:** choose licence type and frequency band.
- **Launch selector:** pick a provider with live mass-allocation
  update.
- **ECSS margin enforcement:** per-domain margin vs policy check.

![A canonical mass budget rendered in the dashboard](../assets/figures/fig_mass_budget.png)

*Figure 3.2 — Mass distribution and the ECSS margin policy by
phase. The dashboard's mass card shows this same data live.*

### Equipment browser

Click **Equipment** in the header bar.

- **18 categories** grouped by domain (Power, AOCS, Comms,
  Propulsion, Structure, Data, Thermal, Integration).
- **Need annotations:** blue dot = required, circle = optional,
  dimmed = not needed.
- **Multiple selection:** select multiple items per category
  (e.g., 4 reaction wheels).
- **RF compatibility:** warning when selecting mismatched
  transponder / antenna bands.
- **Live budget bar:** running mass / power / cost totals.
- **Compare mode:** side-by-side comparison of up to 3 components.

### Trade studies

Two modes:

- **Parametric Sweep** — vary one parameter, see effect on key
  metrics (chart).
- **Tabular Trade** — define criteria with weights, add options,
  score quantitatively or qualitatively (low / medium / high), see
  ranked results.

### Link Budget tool

Full interactive cascade — TX power → antenna gain → losses →
free-space path loss → atmospheric / pointing / polarisation → RX
gain → G/T → C/N₀ → Eb/N₀ → margin. Each term editable, margin
colour-coded.

![Link-budget waterfall — S-band downlink, 1500 km slant](../assets/figures/fig_link_budget.png)

*Figure 3.3 — A canonical link-budget waterfall as rendered by
SpaceCDF. Required C/N₀ and link margin sit at the bottom-right.*

### Optimizer

- **Single objective:** minimise mass, cost, or maximise link
  margin.
- **Pareto (NSGA-II):** multi-objective with up to 10 objectives.
- **Mission-type aware:** variables auto-filtered (no propulsion
  vars without propulsion).
- **Sensitivity (Morris):** ranks which parameters most influence
  the objective.

### Exports

Generates 18+ document types:

- **ECSS:** MRD, TS, IRD, SEMP, RMP, ConOps, VP, Test Plan.
- **Regulatory:** ITU API, IARU coordination, RSSSA, export
  control, COPUOS, EOL report.
- **Design data:** parametric model data, duty cycles, consistency
  check, margin enforcement.

### Cross-tool reactivity

- **Design state bar:** shows when design is outdated after any
  parameter change.
- **Auto-reconverge:** optional toggle — re-runs design
  automatically after each edit.
- **Conflict review:** modal appears when critical conflicts
  detected; requires resolution.
- **Impact preview:** shows which agents and budgets a change will
  affect before accepting.
- **Change audit:** full history with undo capability.

### Progressive level unlocking

The tool follows the System-V (see Figure 3.4) with 5 progressive
levels:

- **Level 0** — Help only (define mission need first).
- **Level 1** — Mission architecture (after need defined). ConOps,
  Functions, Requirements.
- **Level 2** — System architecture (after design run).
  Architecture options, Interfaces, Budgets, Trade Studies, Project
  Management.
- **Level 3** — Subsystem design (after architecture selected).
  Link Budget, Optimizer, Cost, Equipment Browser.
- **Level 4** — Verification (after subsystem design). Compliance,
  V&V Matrix, Gate Review.

The level indicator bar shows your current progress and what to do
next.

![System-V — what SpaceCDF unlocks at each level](../assets/figures/fig_system_v.png)

*Figure 3.4 — System-V model. Level unlocking in SpaceCDF tracks
the left-hand decomposition leg.*

### Interactive mission architecture editor

In the **ConOps** tab, a drag-and-drop diagram editor lets you
build your mission architecture:

- **6 node types** — Satellite · Ground Station · Processing ·
  User · Sensor · GNSS/External.
- Drag nodes to position, connect with labelled lines.
- Architecture drives what systems need to be defined at the next
  level.

### System architecture selection

In the **Architecture** tab:

- **Top half** — select architecture options for each of 8
  subsystems (EPS, AOCS, TT&C, Thermal, Structure, Propulsion, OBC,
  Ground).
- **Bottom half** — auto-generated block diagram showing
  subsystems and their connections.
- Each selection derives requirements (tagged performance /
  interface / budget / functional).

### Engineering budgets (unified view)

The **Eng. Budgets** tab shows all 8 budgets in one place:

| Budget | Source | Margin (Phase A / B / C) |
|--------|--------|--------------------------|
| Mass | Equipment + structure model | 20 % / 15 % / 10 % |
| Power | Equipment + duty-cycle model | 25 % / 20 % / 10 % |
| Link | Link-budget cascade | 6 dB / 3 dB / 3 dB |
| Pointing | RSS pointing tree | 30 % / 20 % / 10 % |
| Δv | Propulsion model | 25 % / 15 % / 10 % |
| Volume | Cal Poly CDS envelope | 10 % / 5 % / 2 % |
| Data | Pipeline flow model | 30 % / 20 % / 10 % |
| Cost | Parametric CER + COTS | 30 % / 20 % / 15 % |

Per-subsystem breakdown shows margin source (COTS vs new design)
and rolls up from equipment selections.

### Constraint propagation engine

187 design-point interconnections detected automatically:

- When any parameter changes, the engine identifies ALL affected
  budgets.
- Shows resolution options for violations with cross-budget
  trade-off analysis.
- Detects circular dependencies (trade-off loops requiring team
  decision).

### Project management

The **Project Mgmt** tab provides:

- **5×5 risk matrix** — interactive, colour-coded by L × C score.
  See Course Plan Figure 2.11.
- **Schedule** — 10 milestones from MCR through commissioning.
- **WBS** — 9 work packages with effort hours and status tracking.
- **Project Manager** position included.

### Word document export

ECSS documents can be exported as editable `.docx` files:

- Click **Word** button next to MRD, ConOps, or VP in the
  **Exports** tab.
- Documents populated from live design state.
- Editable in Microsoft Word or LibreOffice.

### Session persistence

Design state persists across page refreshes:

- All data saved to browser localStorage automatically.
- No need to "save" — it's always saved.
- To clear: browser DevTools → Application → Local Storage →
  delete `spacecdf-design-state`.

---

## Concurrent design sessions

1. Click **Start Session** in the header.
2. Select your position(s) and enter a display name.
3. Share the URL with team members — they join the same session.
4. Edits propagate in real-time via WebSocket.
5. Each position can only edit their owned parameters.
6. Convergence runs automatically after each edit.

---

## Editing parametric data

The tool's sizing models use CubeSat-calibrated data. To view and
edit:

1. Go to **Parametric** tab.
2. Four sub-tabs: Mass Fractions · Cost Fractions · Power Duty
   Cycles · SA Power.
3. Values are per spacecraft class (nano, micro, small, medium,
   large).
4. Sources cited alongside each table.

To edit the source data directly:
`packages/spacecdf-common/src/spacecdf_common/physics/heritage_mass.py`.

---

## Updating equipment database

Component data is in YAML files:
`packages/spacecdf-kb/src/spacecdf_kb/data/components/`.

To add a component:

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

The API also supports import: `POST /api/lifecycle/equipment/import`.

---

## Tab-by-tab feature inventory

| Tab | Group | Purpose |
|-----|-------|---------|
| Dashboard | Design | Live KPI overview |
| ConOps | Design | Mission architecture editor & timeline |
| Functions | Design | Function tree, allocation matrix |
| Requirements | Design | SMART requirements, parent/child |
| Interfaces | Design | N² matrix, interface conflict resolver |
| Architecture | Design | Architecture selection, derived reqs |
| Eng. Budgets | Design | All 8 budgets in one place |
| Link Budget | Analysis | Interactive cascade, margin colouring |
| Trade Studies | Analysis | Parametric sweep + tabular |
| Optimizer | Analysis | NSGA-II, Morris sensitivity |
| Cost | Analysis | CER + WBS roll-up |
| Compliance | Verify | Requirement compliance matrix |
| V&V Matrix | Verify | Verification method (A/T/R/I) per req |
| Gate Review | Verify | PDR exit criteria, action items |
| Positions | Team | Position assignments + responsibilities |
| Q&A | Team | Position-specific design questions |
| Project Mgmt | Team | Risk · schedule · WBS |
| Exports | Data | ECSS, regulatory, design-data exports |
| Parametric | Data | Tunable sizing-model coefficients |
| Changes | Data | Audit log + undo |
| Help | Data | Inline help index |

---

## Status-bar legend

The bottom status bar uses 4 colour bands and 6 icons:

| Colour | Meaning | Action |
|--------|---------|--------|
| Green | All margins met, no conflicts | Continue |
| Amber | Margin within 10 % of policy | Tighten or accept and document |
| Red | Margin violated or critical conflict | Resolve before next gate |
| Grey | Design out of date — re-run | Click "Run Design" |

Icons:
🛰 active design · 🟢 nominal · ⚠ warning · 🚨 critical · 🔄 reconverging · 📦 export ready.

---

## File-format support matrix

| Format | Import | Export | Notes |
|--------|:------:|:------:|-------|
| YAML (mission, equipment) | ✓ | ✓ | Canonical interchange |
| JSON (parameters) | ✓ | ✓ | API native |
| CSV (BOM, requirements) | ✓ | ✓ | Excel-friendly |
| Word (.docx) | — | ✓ | ECSS document set |
| PDF | — | ✓ | Generated from .docx |
| Markdown | — | ✓ | Read-only design pack |
| TLE | ✓ | ✓ | Orbit interchange |
| KML | — | ✓ | Ground tracks for visual review |

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl + Enter | Run design |
| Ctrl + S | Force save (no-op — always saved) |
| Esc | Close modal |
| ⌘/Ctrl + K | Quick-search any tab |
| F2 | Focus dashboard |
| F3 | Focus equipment browser |
| F4 | Focus optimiser |
| ⌘/Ctrl + Z | Undo (uses Change Audit) |
| ⌘/Ctrl + Shift + Z | Redo |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Socket not connected" | No active session | Start or join a session first |
| Design shows no results | Design not run | Click **Run Design** in Step 3 |
| Requirements tab empty | No study ID | Run design at least once |
| Optimizer won't start | No active session | Start a session, or use solo mode |
| Equipment browser greyed out | Frontend ↔ backend out of sync | Reload the page; check CORS |
| ECSS export fails | Design has open conflicts | Resolve in Conflict Review modal |
| Word export looks wrong | LibreOffice quirks | Open in Word; missing fonts: install Work Sans/Spectral |
| TLE import rejected | Wrong epoch / line length | Use the canonical 2-line format |

---

## Error-message reference

| Code | Message | What it means | What to do |
|------|---------|---------------|------------|
| `E_NEED_001` | "Problem statement required" | Step 1 incomplete | Write the WHAT in Step 1 |
| `E_REQ_017` | "SMART check failed: vague verb" | Requirement not testable | Use *shall* + measurable verb |
| `E_INT_004` | "Interface conflict — voltage mismatch" | Two subsystems disagree on bus voltage | Decide bus voltage at architecture level |
| `E_BUD_022` | "Mass margin violated" | Total > policy | Trade structure / payload / propellant |
| `E_OPT_011` | "Optimizer not converging" | Search space empty | Widen variable bounds |
| `E_EXP_003` | "ECSS export blocked: open conflicts" | Conflicts not resolved | Resolve in Conflict Review |

---

## Glossary

| Term | Meaning |
|------|---------|
| AOCS | Attitude & Orbit Control System |
| AOS | Acquisition of Signal (start of pass) |
| BOM | Bill of Materials |
| CDF | Concurrent Design Facility |
| CER | Cost Estimating Relationship |
| ConOps | Concept of Operations |
| CDS | (Cal Poly) CubeSat Design Specification |
| DoD | Depth of Discharge (battery) |
| ECSS | European Cooperation for Space Standardization |
| EIRP | Effective Isotropic Radiated Power |
| EPS | Electrical Power Subsystem |
| FDIR | Fault Detection, Isolation, and Recovery |
| FOV | Field of View |
| FSPL | Free-Space Path Loss |
| GSD | Ground Sample Distance |
| ICD | Interface Control Document |
| IRD | Interface Requirements Document |
| ITU | International Telecommunication Union |
| LEOP | Launch and Early Orbit Phase |
| LOS | Loss of Signal (end of pass) |
| MCR | Mission Concept Review |
| MoE / MoP | Measure of Effectiveness / Performance |
| MRD | Mission Requirements Document |
| OBDH | On-Board Data Handling |
| OBC | On-Board Computer |
| PCDU | Power Conditioning & Distribution Unit |
| PDR | Preliminary Design Review |
| PUS | (CCSDS) Packet Utilization Standard |
| RAAN | Right Ascension of Ascending Node |
| RACI | Responsible / Accountable / Consulted / Informed |
| RSSSA | Remote Sensing Space Systems Act (Canada) |
| RW | Reaction Wheel |
| SAR | Synthetic-Aperture Radar |
| SCM | Space Mission Engineering (textbook) |
| SMAD | Space Mission Analysis & Design (textbook) |
| SMART | Specific · Measurable · Achievable · Relevant · Traceable |
| SSO | Sun-Synchronous Orbit |
| TC | Telecommand |
| TCA | Time of Closest Approach |
| TM | Telemetry |
| TPM | Technical Performance Measure |
| TRL | Technology Readiness Level |
| TT&C | Tracking, Telemetry & Command |
| WBS | Work Breakdown Structure |

---

## Reference list

- **NASA SEH** — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- **NASA CubeSat 101** — [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)
- **ECSS standards** — [https://ecss.nl/](https://ecss.nl/)
- **Cal Poly CDS Rev 14** — [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement)
- **CCSDS PUS** — [https://public.ccsds.org/Pubs/660x0g3.pdf](https://public.ccsds.org/Pubs/660x0g3.pdf)
- **ITU Radio Regulations** — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR)
- **ISED CPC-2-6-02** — [https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en](https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en)
- **SpaceCDF source** — [https://github.com/FNewland/SpaceCDF](https://github.com/FNewland/SpaceCDF)
