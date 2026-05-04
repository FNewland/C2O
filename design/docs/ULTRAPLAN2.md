# SpaceCDF Ultraplan 2 — Comprehensive Design Process Review

## Status as of 2026-05-04

Rigorous review by a simulated team of CubeSat mission designers covering
every step of the workflow, every ECSS standard, and every user-facing issue.

---

## Issue Catalogue

### Category A: Payload Type Bias (optical-only assumptions)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| A1 | Payload sizing is optical-only (GSD/aperture) — no RF, SAR, AIS, comms relay | CRITICAL | 6h | TODO |
| A2 | Orbit trade scores only on GSD — penalises non-optical orbits | CRITICAL | 4h | TODO |
| A3 | Mission trade alternatives are all EO — no comms/SAR/AIS alternatives | HIGH | 3h | TODO |
| A4 | Class advisor scores on GSD — penalises non-optical missions | HIGH | 2h | TODO |
| A5 | Requirement generator examples assume optical imagery | MED | 1h | TODO |
| A6 | PayloadType enum exists in model but is never wired to sizing/trade logic | HIGH | 2h | TODO |

### Category B: Ground Segment & Architecture

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| B1 | Mission architecture shows no sensors, single monolithic ground segment | HIGH | 4h | TODO |
| B2 | No support for ground equipment in functional decomposition | HIGH | 3h | TODO |
| B3 | Store-and-forward / bent-pipe relay architectures not modelled | HIGH | 3h | TODO |
| B4 | Data flow directions and connection types not shown | MED | 2h | TODO |
| B5 | Systems in use per mode not shown in architecture | MED | 2h | TODO |
| B6 | Ground segment should separate ops station from payload processing | MED | 2h | TODO |

### Category C: Workflow & UI Bugs

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| C1 | "Use" on orbit options sets store but UI form fields don't reflect it | HIGH | 1h | TODO |
| C2 | Class advisor requires data user doesn't have yet (data rate, pointing, budget) | HIGH | 2h | TODO |
| C3 | Requirements generation requires session (studyId gate) — should work solo | CRITICAL | 2h | TODO |
| C4 | Compliance tab shows auto-generated reqs not from Requirements Editor | HIGH | 2h | TODO |

### Category D: Lifetime & Physics

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| D1 | Lifetime calculations inaccurate (simplified King-Hele, factor-2 error) | HIGH | 4h | TODO |
| D2 | No eccentricity support in lifetime model | MED | 2h | TODO |
| D3 | No time-dependent solar cycle modelling | MED | 2h | TODO |
| D4 | Cross-section estimation crude (0.01 × m^(2/3)) | MED | 1h | TODO |

### Category E: Optimizer

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| E1 | Only 6 design variables — missing architecture/redundancy/thermal | HIGH | 3h | TODO |
| E2 | Only 4 objectives — missing reliability, thermal, data latency, TRL | HIGH | 2h | TODO |
| E3 | No explicit constraints — only soft penalty for conflicts | HIGH | 3h | TODO |
| E4 | No sensitivity analysis or robustness metrics | MED | 3h | TODO |
| E5 | Pareto visualization 2D only — need parallel coordinates or spider | MED | 2h | TODO |

### Category F: ECSS Standard Implementation Gaps

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| F1 | ECSS-E-ST-20C (Electrical): margin rules referenced but not enforced | MED | 2h | TODO |
| F2 | ECSS-E-ST-31C (Thermal): no thermal environment per standard | MED | 3h | TODO |
| F3 | ECSS-E-ST-32C (Structural): no structural analysis per standard | MED | 3h | TODO |
| F4 | ECSS-E-ST-60-10C (AOCS): pointing budget not per standard | MED | 2h | TODO |
| F5 | ECSS-E-ST-70C (Ground ops): ground ConOps not per standard | MED | 2h | TODO |
| F6 | ECSS-E-ST-10-03C (Testing): test plan DID is skeleton only | MED | 2h | TODO |
| F7 | ECSS-M-ST-10C (Project mgmt): phase/review lifecycle partially mapped | LOW | 2h | TODO |
| F8 | ECSS-Q-ST-40C (Safety): no safety analysis implementation | LOW | 3h | TODO |
| F9 | ECSS-E-ST-10-04C (Environment): radiation model basic, no trapped proton/electron | MED | 3h | TODO |

---

## Prioritised Resolution Phases

### Phase 1: Critical Workflow Fixes (make existing features work)
*Estimated: 1 day*

- **C1**: Orbit "Use" button — form fields must reflect stored values (read from store)
- **C3**: Requirements generation without session — create study on "Run Design" without requiring session start, or enable solo study creation
- **C4**: Reconcile compliance requirements with Requirements Editor — single source of truth
- **C2**: Class advisor pre-populates from orbit trade / mission trade where possible, remaining fields optional with defaults

### Phase 2: Multi-Mission Payload Support
*Estimated: 2 days*

- **A6**: Wire PayloadType enum through all downstream logic
- **A1**: Add payload sizing functions: RF relay, SAR, AIS, radiometer, comms
- **A2**: Orbit trade scoring branches by mission type (GSD for optical, coverage/latency for comms, revisit+incidence for SAR)
- **A3**: Mission trade adds non-optical alternatives (Iridium, ICEYE, existing SAR/comms)
- **A4**: Class advisor scores by mission type not just GSD
- **A5**: Requirement generator uses mission-type-aware templates

### Phase 3: Ground Segment Architecture
*Estimated: 2 days*

- **B1**: Expand mission architecture SVG: payload sensor box, ground ops station, payload processing centre, ground sensors (optional), user segment
- **B6**: Ground segment split: operations (TM/TC/MCC) vs payload (reception/processing/archive/distribution)
- **B4**: Data flow arrows with direction indicators, labelled connection types (RF S-band, X-band, Ka-band, fibre, internet API)
- **B5**: Per-mode activation: show which systems (space + ground) are active in each operational mode
- **B2**: Function tree adds ground domains: ground_station, ground_processing, ground_sensor
- **B3**: ConOps model adds architecture_type (direct_downlink, store_and_forward, bent_pipe, ground_sensor_ingestion)

### Phase 4: Lifetime & Physics Improvement
*Estimated: 1 day*

- **D1**: Improve lifetime model — use proper King-Hele analytical integration, validate against ESA DRAMA or STK baselines
- **D4**: Better cross-section estimation using CubeSat form factors (1U=0.01m², 3U=0.03m², 6U=0.06m², 12U=0.12m²)
- **D2**: Add eccentricity support for non-circular orbits
- **D3**: Add solar cycle phase input (years from solar min) for better mean density

### Phase 5: Optimizer Expansion
*Estimated: 2 days*

- **E1**: Add design variables: battery chemistry, antenna type, thermal approach, redundancy level, bus voltage, propulsion type
- **E2**: Add objectives: max reliability, min thermal exceedance, min data latency, max TRL composite, min schedule risk
- **E3**: Add explicit constraints: mass <= launcher allocation, power margin >= 20%, pointing <= requirement, cost <= ceiling
- **E4**: Post-optimization sensitivity analysis (Morris screening or Sobol indices)
- **E5**: Parallel coordinates plot for multi-objective Pareto visualization

### Phase 6: ECSS Standard Deepening
*Estimated: 2 days*

- **F1-F9**: For each partially-implemented standard:
  - Extract specific margin rules, analysis requirements, and deliverable formats
  - Implement validation checks where possible
  - Generate richer DID content using actual standard structures
  - Add standard-specific warnings when design parameters violate standard rules

---

## ECSS Standards Cross-Reference (complete)

### Fully Implemented (12 standards)

| Standard | Implementation | Location |
|----------|---------------|----------|
| ECSS-E-ST-10C Rev.1 | Requirements generation, MRD template, SE framework | requirement_engine.py, did_generator.py |
| ECSS-E-ST-10-02C Rev.1 | VP + VCD generation with req-by-req verification | compliance_generator.py |
| ECSS-E-ST-10-06C | Technical Specification DID | did_generator.py |
| ECSS-E-ST-10-24C Rev.1 | IRD generation from interface matrix | did_generator.py, interfaces.py |
| ECSS-E-ST-50-05C Rev.2 | Link budget with modulation, coding, margin | link_budget.py |
| ECSS-Q-ST-30-02C | FMECA-lite with failure rates, SPF identification | reliability.py |
| ECSS-U-AS-10C Rev.2 | Orbital lifetime, 25yr/5yr rule, casualty risk, passivation | debris.py |
| ECSS-S-ST-00-02C | Tailoring matrix with applicability rules | compliance_generator.py |
| ECSS-E-ST-10-04C Rev.1 | Radiation environment (TID, trapped particles) | radiation.py |
| ECSS-E-ST-10-12C | Radiation dose calculations | radiation.py |
| ECSS-M-ST-80C | Risk management plan, risk register | did_generator.py |
| ECSS-E-TM-10-25A | MBSE JSON export (loosely aligned) | mbse/generator.py |

### Partially Implemented (needs deepening)

| Standard | What Exists | What's Missing |
|----------|------------|----------------|
| ECSS-E-ST-20C | Power margin thresholds | Bus voltage rules, harness derating, PCDU architecture |
| ECSS-E-ST-31C | Thermal agent sizes radiators | No formal thermal environment per standard (worst-case hot/cold) |
| ECSS-E-ST-32C Rev.1 | Structure mass allocation | No FEA-level structural analysis, MoS calculation stub |
| ECSS-E-ST-35C Rev.1 | Propulsion Isp/mass | No tank sizing per standard, no compatibility checks |
| ECSS-E-ST-60-10C | AOCS pointing budget | Not structured per standard's error budget tree |
| ECSS-E-ST-70C | Ground ops timeline | No formal ConOps per standard structure |
| ECSS-E-ST-70-01C | Mode manager FSW generation | No PUS packet structure per standard |
| ECSS-M-ST-10C Rev.1 | Phase/review lifecycle | Gate criteria not fully mapped to standard tables |
| ECSS-M-ST-40C Rev.1 | Snapshots/versioning | No formal CM plan or baseline management per standard |
| ECSS-M-ST-60C | Cost CERs and Monte Carlo | No earned value or schedule management per standard |
| ECSS-E-ST-10-03C | Test plan skeleton DID | No environmental test spec derivation from standard |
| ECSS-E-HB-10-02A | Margin table in YAML | Not enforced in verification flow |

### Referenced Only (no implementation)

| Standard | Where Mentioned | Gap |
|----------|----------------|-----|
| ECSS-E-ST-10-09C | Lunar orbiter template | Coordinate system handling |
| ECSS-E-ST-20-07C | Test generator | EMC analysis not implemented |
| ECSS-E-ST-33-01C Rev.1 | Mechanisms | No mechanism design support |
| ECSS-E-ST-60-30C | Templates | AOCS mode definition per standard |
| ECSS-E-ST-70-41C | PUS template | Packet Utilisation Standard |
| ECSS-E-AS-11C | DRD in phase_0 | TRL assessment procedure not implemented |
| ECSS-Q-ST-10C Rev.1 | Templates | Product assurance plan |
| ECSS-Q-ST-30C Rev.1 | Templates | Dependability analysis |
| ECSS-Q-ST-40C | Templates | Safety analysis |
| ECSS-Q-ST-60-15C Rev.1 | Templates | Radiation hardness assurance procedures |

---

## Total Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Phase 1: Workflow fixes | 1 day | None |
| Phase 2: Multi-mission | 2 days | Phase 1 |
| Phase 3: Ground segment | 2 days | Phase 2 |
| Phase 4: Physics | 1 day | None |
| Phase 5: Optimizer | 2 days | Phase 2 |
| Phase 6: ECSS deepening | 2 days | Phase 3 |
| **TOTAL** | **~10 working days** | |

---

## Implementation Order

Phase 1 first — immediate bug fixes and usability.
Phase 2 next — fundamental architecture change (multi-mission).
Phases 3-4 can run in parallel.
Phase 5 after Phase 2 (needs multi-mission variables).
Phase 6 last — deepening rather than new capability.
