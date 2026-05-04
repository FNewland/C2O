# SpaceCDF API Documentation

**Base URL:** `http://localhost:8000/api`
**Total Endpoints:** 105+
**Format:** JSON (request and response)

---

## Core Design

### POST /design/quick-design
Run the full design loop (20 agents, convergence in seconds).

**Request:**
```json
{
  "requirements": {
    "name": "My Mission",
    "mission_type": "earth_observation",
    "spacecraft_class": "nano",
    "orbit": { "orbit_type": "sso", "altitude_km": 500, "inclination_deg": 97.4 },
    "payloads": [{ "name": "Imager", "mass_kg": 1.5, "power_w": 8, "data_rate_mbps": 100 }],
    "design_lifetime_years": 3
  }
}
```

**Response:** `{ converged, iterations, total_time_s, parameters: {id: {value, unit, domain}}, budgets, warnings, conflicts }`

### POST /studies/
Create a study (persists requirements + mission need for later reference).

### GET /studies/{id}
Retrieve study state.

---

## Lifecycle Services

### POST /lifecycle/orbit-trade
Compute orbit trade study with scored candidates.

**Request:** `{ target_gsd_m, target_revisit_days, target_latitude_band, aperture_m, max_cost_meur, min_lifetime_years, mission_type }`

**Response:** `{ candidates: [{ name, altitude_km, inclination_deg, achievable_gsd_m, revisit_days, natural_lifetime_years, total_score, rank }] }`

### POST /lifecycle/class-advisor
Recommend spacecraft class from performance/programmatic targets.

### POST /lifecycle/mission-trade
Evaluate space vs non-space alternatives (filtered by mission_type, includes constellation option).

### GET /lifecycle/spectrum/bands
Available frequency bands filtered by mission type and license type.

**Query params:** `mission_type`, `license_type` (amateur/experimental/commercial), `data_rate_mbps`

### POST /lifecycle/spectrum/itu-api-template
Generate ITU Advance Publication Information filing template.

### POST /lifecycle/spectrum/iaru-template
Generate IARU amateur coordination request template.

### POST /lifecycle/regulatory/rsssa
Generate Canadian RSSSA filing template.

### POST /lifecycle/regulatory/export-assessment
Generate export control classification assessment.

### POST /lifecycle/regulatory/copuos-registration
Generate UN Registration Convention Article IV template.

### POST /lifecycle/regulatory/eol-report
Generate end-of-life analysis report.

### GET /lifecycle/parametric-data
Return all parametric model data (mass fractions, cost fractions, power duty cycles, SA power tables) with source citations.

### POST /lifecycle/duty-cycles
Estimate power duty cycles for a mission configuration.

**Request:** `{ spacecraft_class, mission_type, comms_band, eclipse_fraction }`

### GET /lifecycle/consistency/{study_id}
Run full design consistency check. Returns health score, issues by category.

### POST /lifecycle/trade-study
Run a tabular trade study with criteria, weightings, and options.

**Request:** `{ name, criteria: [{id, name, weight, direction}], options: [{id, name, scores: {criterion_id: value}}] }`

### GET /lifecycle/trade-templates
List pre-built trade study templates (orbit, component, ground, architecture).

### POST /lifecycle/constellation/design
Design Walker delta constellation for coverage targets.

### GET /lifecycle/beyond-leo/orbits
List beyond-LEO orbit options (MEO, GEO, HEO, Lunar, interplanetary) with environment data.

### POST /lifecycle/beyond-leo/transfer
Compute transfer orbit ?V from LEO to target orbit.

### POST /lifecycle/beyond-leo/dsn-link
Compute deep-space link budget for DSN communication.

### GET /lifecycle/requirements/generate/{study_id}
Generate SMART requirements from study objectives and functions.

### POST /lifecycle/requirements/validate
Validate a requirement against SMART criteria.

### POST /lifecycle/requirements/check-compliance
Check non-compliance and get resolution options.

---

## Engineering Services

### GET /engineering/equipment/{domain}/search
Search KB for equipment compatible with current design.

**Domains:** power, aocs, link, propulsion, structure, data, thermal, integration

### GET /engineering/equipment/needs/{study_id}
Determine which equipment categories are needed based on requirements.

### POST /engineering/equipment/check-compatibility
Check RF compatibility between transponder and antenna.

### POST /engineering/equipment/budget-impact
Compute live budget impact of current equipment selections.

### GET /engineering/verification
Run requirement verification against current design state.

### GET /engineering/cost
Get cost estimate for current design.

### POST /engineering/analysis/sensitivity
Run parametric sensitivity sweep.

### GET /engineering/analysis/eol-curves
Get end-of-life degradation curves.

### POST /engineering/analysis/trade-study
Run equipment-level trade study.

### POST /engineering/impact-preview
Preview downstream impact of parameter changes (dry run ? no execution).

---

## ECSS Compliance

### GET /ecss/phases
List available ECSS phases.

### GET /ecss/compliance/{phase_id}
Get expected DRDs and SpaceCDF coverage for a phase.

### GET /ecss/margins/{study_id}
Check all budget margins against ECSS phase-appropriate policy.

### GET /ecss/dids
List available DID (Document Item Description) types.

### POST /ecss/dids/{did_type}/generate
Generate an ECSS DID document. Types: mrd, ts, ird, semp, rmp, conops, test_plan.

---

## Optimizer

### GET /optimize/config
Get available objectives and design variables (filtered by mission_type if provided).

**Query params:** `mission_type`, `has_propulsion`, `pointing_accuracy_deg`

### POST /optimize/sessions/{session_id}
Start an optimization run (single-objective or Pareto NSGA-II).

### GET /optimize/runs/{run_id}
Get optimization run status and results.

### POST /optimize/sensitivity/{session_id}
Run Morris screening sensitivity analysis.

---

## Sessions (Concurrent Design)

### POST /sessions/
Create a new design session.

### GET /sessions/{id}
Get session state.

### GET /sessions/{id}/history
Get edit history for a session.

### WebSocket /ws/session/{session_id}
Real-time collaboration. Message types: parameter_update, state_update, convergence_complete, participant_joined/left.

---

## Positions

### GET /positions/
List all engineering positions with roles and key questions.

### GET /positions/{id}/guidance
Get computed guidance for a position based on current design.

### POST /positions/answers
Save a position question answer.

### GET /positions/answers
Get all saved position answers.

---

## Knowledge Base

### GET /kb/components/{category}
Get all components in a category.

### GET /kb/categories
List all component categories.

---

## Exports

### POST /exports/docs/{format}
Generate design review documents (SRR, PDR, CDR).

### POST /exports/mbse/{study_id}
Generate MBSE JSON export (ECSS-E-TM-10-25A style).

### POST /exports/fsw/{study_id}
Generate flight software architecture (mode manager, FDIR, TC/TM).
