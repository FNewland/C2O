# SpaceCDF Ultraplan 4 — Frontend Wiring & UX Completeness

## Status as of 2026-05-04

**Problem**: Extensive backend services exist but are NOT wired to the frontend.
The user sees only a fraction of the tool's capability. This ultraplan focuses
entirely on connecting existing backends to the UI.

---

## Audit Results: What's NOT Connected

### Backend services with NO frontend UI (18 services):

| Service | API Exists | Frontend Tab/Button | Gap |
|---------|-----------|-------------------|-----|
| Spectrum allocation | YES | NO | Need new tab or section |
| Regulatory filing (RSSSA, ITAR, COPUOS, EOL) | YES | NO | Need exports section |
| Constellation design | YES | NO | Need constellation UI |
| Beyond-LEO orbits | YES | NO | Need orbit type expansion |
| Tabular trade studies | YES | NO | Need trade study builder UI |
| Parametric data viewer | YES | NO | Need editable tables UI |
| Duty cycle estimator | YES | NO | Need power mode UI |
| Consistency checker | YES | NO | Need dashboard indicator |
| ECSS margin enforcer | YES | NO | Need margin check display |
| Requirements generator | YES | NO trigger | Need "Generate" button |
| Equipment needs analysis | YES | NO | Need needs-driven browser |
| Equipment compatibility | YES (backend logic) | Partial (confirm dialog) | Need visual indicators |
| Harness designer | YES | NO | Need integration tab |
| BOM generator | YES | NO | Need export button |
| Test procedure generator | YES | NO | Need export button |
| Launch planner | YES | NO | Need launch tab |
| Ground segment trade | YES | NO | Need ground segment section |
| Session guidance | YES | Partial (text only) | Need proper guidance flow |

### Frontend bugs:

| Bug | Root Cause |
|-----|-----------|
| Multispectral imagery in comms functions | DEMO_FUNCTIONS hardcoded, not mission-type-aware |
| Only one subsystem allocation per function | Single `allocated_to` string, not list |
| No constellation option in UI | Only `num_spacecraft: 1` default, no constellation form |
| "operate at 500km" requirement appearing | Auto-generated from default, user never approved |
| Can't answer position questions / action items | Buttons work but no visual feedback of submission |
| Can't see export documents | DID generator exists but no download/view for regulatory docs |
| Trade studies limited | Only sensitivity sweep connected, not tabular trades |
| Optimizer limited | Config endpoint not passing mission_type for relevance filtering |

---

## Issue Catalogue

### Category A: Critical Wiring (connect existing backend to existing UI)

| # | Issue | Effort | Status |
|---|-------|--------|--------|
| A1 | Functions DEMO_FUNCTIONS should be mission-type-aware (no multispectral for comms) | 1h | TODO |
| A2 | Function `allocated_to` should support multiple subsystems (list not string) | 1h | TODO |
| A3 | "Generate Requirements" button in RequirementsEditor must call API | 1h | TODO |
| A4 | Remove auto-generated "operate at 500km" — only show user-approved requirements | 1h | TODO |
| A5 | Constellation fields in requirements form (num_spacecraft, constellation_type) | 2h | TODO |
| A6 | Position answers: visual confirmation on submit, persist to backend | 1h | TODO |
| A7 | Optimizer config passes mission_type for relevance filtering | 30min | TODO |

### Category B: New UI Sections for Existing Backends

| # | Issue | Effort | Status |
|---|-------|--------|--------|
| B1 | Exports panel: regulatory documents (RSSSA, ITAR, COPUOS, EOL, ITU, IARU) | 3h | TODO |
| B2 | Spectrum viewer in comms section (show available bands by license type) | 2h | TODO |
| B3 | Tabular trade study builder UI (criteria, weights, options, scores) | 4h | TODO |
| B4 | Parametric data viewer/editor (mass fractions, cost fractions, duty cycles) | 3h | TODO |
| B5 | Power duty cycle mode editor (pre-populate from estimator, user editable) | 2h | TODO |
| B6 | Consistency check indicator on dashboard (health score badge) | 1h | TODO |
| B7 | ECSS margin enforcement display (per-domain margin vs policy) | 2h | TODO |
| B8 | Launch provider selector (from launch_providers.yaml, linked to deployer) | 2h | TODO |
| B9 | BOM export button (from current design + equipment selections) | 1h | TODO |
| B10 | Beyond-LEO orbit options in orbit form (MEO/GEO/lunar with transfer ΔV) | 2h | TODO |

---

## Prioritised Phases

### Phase 1: Critical Bug Fixes (1 day)
A1-A7: Fix functional decomposition, requirements, constellation fields, position answers.

### Phase 2: Exports & Documents (1 day)
B1, B9: New exports panel with all regulatory document generators and BOM.

### Phase 3: Trade Studies & Parametric Data (1 day)
B3, B4, B5: Tabular trade builder, parametric editor, duty cycle modes.

### Phase 4: Spectrum, Launch, Beyond-LEO (1 day)
B2, B8, B10: Spectrum viewer, launch selector, beyond-LEO orbits.

### Phase 5: Dashboard Intelligence (half day)
B6, B7: Consistency health score, margin enforcement display.

**Total: ~4.5 working days**
