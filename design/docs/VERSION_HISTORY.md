# SpaceCDF Version History

## Summary of Development Sessions

This document consolidates the planning documents, feedback sessions, and architectural decisions made during SpaceCDF development. The original documents have been archived after their content was addressed.

---

### Session 1-2: Initial Build
- Built core CDF with 15 engineering positions, 20 automated design agents
- Concurrent design via WebSocket with real-time parameter editing
- Parametric design loop covering all subsystems

### Session 3: Test Campaign (6 Real Missions)
- Tested with SuperDove, Astrocast, AIS receiver, Iridium, CAPSTONE, LEMUR-2
- Found and fixed: cost model 3-5x too high (COTS pricing), SA undersized (peak+charging), link budget single-link (added dual TTC+payload), disturbance torques zeros (removed deep-space stub), data volume hardcoded
- 45+ issues identified and resolved

### Session 4: Frontend Redesign
- Redesigned from 22-tab progressive unlock to 6-phase System-V navigation
- Eliminated Recharts (infinite loop with Zustand), replaced with pure SVG charts
- Multi-segment design: Space, Ground, Launch, Operations in parallel tabs

### Session 5: Model-Centric Architecture
- Implemented backend-first element tree (DesignElement with mass/power/cost/interfaces)
- Zustand modelStore as optimistic cache with WebSocket sync
- Element projection layer bridging flat DesignState to tree hierarchy
- Seed endpoint bootstraps element tree from design results

### Session 6: System-V Wiring (12 Items)
- Wired Phase 1→2→3 so each phase creates objects for the next
- Budget cascade reads from element tree
- Interface matrix derives from model
- V&V matrix includes component-level verification
- Phase completion tracking and cross-level conflict detection

### Session 7: Data Integrity & Polish (15 Items)
- Persisted: budget allocations, interface resolutions, V&V change log
- WebSocket wired to modelStore for concurrent design sync
- Equipment removal from subsystems
- Architecture selection upsert (no duplicates)
- Error boundaries per phase
- Save/Load includes element tree snapshot
- Component maturity tracking (undefined→parametric→estimated→selected→specified→verified)

### Session 8: Documentation Architecture (5 Parts)
- **BOM generator** from element tree with subsystem grouping, model level, procurement, export control
- **V&V matrix** with change tracking, save/load, requirement ID immutability ({NAME}-{LEVEL}-{SEQ})
- **SEMP generator** with 5-page questionnaire wizard, 14 auto-populated sections, SVG timeline
- **Enriched ECSS DIDs** — all 7 documents produce substantive content with tables, equations, traceability
- **Regulatory auto-population** — RSSSA, ITU API (PFD computation), COPUOS, EOL (orbital lifetime), export control

### Session 9: Integration & Course Documentation
- Docx generator renders tables, bullet lists, cover pages, TOC
- Document preview component replaces raw JSON viewer
- Mission reload by study ID
- 22 automated tests for document pipeline
- Requirement IDs wired to sequential counters
- SEMP TRLs from element tree, regulatory params from design state
- **Complete course rewrite** — 20 facilitator sessions + 20 learner worksheets as textbook-quality content with 338 equations, 11 SVG diagrams, 166 citations with URLs

---

### Architecture Decisions Record

| Decision | Chosen Approach | Rationale |
|----------|----------------|-----------|
| Data ownership | Backend-first (DB owns model) | Safe for concurrent design |
| Frontend state | Zustand with optimistic cache | Fast UI, WebSocket sync |
| Charts | Pure SVG (no Recharts) | Avoided infinite loop with Zustand |
| Navigation | 6-phase System-V sidebar | Matches engineering workflow |
| Requirement IDs | {MISSIONNAME}-{LEVEL}-{SEQ} | Human-readable, never reused, level-scoped |
| Model philosophy | Per-subsystem via SEMP questionnaire | TRL-based defaults, user-overridable |
| Regulatory focus | Canadian (ISED/RSSSA) + international (ITU/COPUOS) | User's primary jurisdiction |
| Document format | JSON sections → docx via python-docx | Standards-compliant, printable |
| BOM source | Element tree (not flat store) | Single source of truth |

### Constraint Engine
- 187 interconnections mapped across all subsystems
- Cascade propagation on parameter changes
- Cross-domain conflict detection (mass/power/link/thermal/pointing/cost)

### Knowledge Base
- 175+ space components across 19 YAML files
- 14 ground equipment components
- Fit scoring against mission requirements
