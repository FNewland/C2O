# SpaceCDF Ultraplan 3 — Deep Capability Expansion

## Status as of 2026-05-04

Comprehensive review covering constellation support, beyond-LEO missions,
RF licensing/spectrum, launch integration, equipment intelligence, regulatory
paperwork, and validation against 7 real CubeSat missions.

---

## Issue Catalogue

### Category A: Multi-Satellite & Constellation Support

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| A1 | No constellation mode — only single satellite design | HIGH | 8h | TODO |
| A2 | No constellation orbit design (Walker delta, flower, etc.) | HIGH | 6h | TODO |
| A3 | No inter-satellite link modelling | MED | 4h | TODO |
| A4 | No constellation-level coverage/revisit analysis | HIGH | 6h | TODO |

### Category B: Beyond-LEO Orbit Support

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| B1 | MEO/GEO/HEO orbit mechanics not modelled (Van Allen, thermal, power at distance) | HIGH | 6h | TODO |
| B2 | Lunar orbit support (NRHO, low lunar orbit, halo) | HIGH | 6h | TODO |
| B3 | Deep space power scaling (solar flux vs distance) | MED | 3h | TODO |
| B4 | DSN link budget for beyond-LEO | MED | 4h | TODO |
| B5 | Propulsion budgets for orbit insertion (lunar, interplanetary) | MED | 4h | TODO |

### Category C: RF Licensing & Spectrum Module

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| C1 | No licensing constraints in comms selection — can pick any band freely | CRITICAL | 6h | TODO |
| C2 | No spectrum allocation database / interference analysis | HIGH | 12h | TODO |
| C3 | No ITU filing paperwork template generator | HIGH | 8h | TODO |
| C4 | No IARU amateur coordination form support | MED | 4h | TODO |
| C5 | Transceiver options should be filtered by available spectrum for mission need | HIGH | 4h | TODO |
| C6 | Multispectral imagery assumed for non-optical missions | HIGH | 2h | TODO |

### Category D: Regulatory Paperwork & Export Control

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| D1 | No Canadian RSSSA filing template for remote sensing | HIGH | 6h | TODO |
| D2 | No export permit paperwork (ITAR/EAR assessment, CGP, OGEL) | HIGH | 6h | TODO |
| D3 | No COPUOS registration template (UN Registration Convention Art IV) | MED | 4h | TODO |
| D4 | No end-of-life analysis report for ITU/regulatory filing | MED | 3h | TODO |

### Category E: Launch Integration Module

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| E1 | No launch broker/provider database with current pricing | HIGH | 6h | TODO |
| E2 | No launch ICD template generated from spacecraft design | HIGH | 6h | TODO |
| E3 | No deployer selection linked to structure size | MED | 3h | TODO |
| E4 | No separation switch requirement tracking | MED | 2h | TODO |
| E5 | No environmental test levels from launch vehicle | MED | 4h | TODO |

### Category F: Equipment Intelligence (bugs + enhancements)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| F1 | Can still select S-band transceiver with X-band antenna — compatibility not enforced at selection time | CRITICAL | 3h | TODO |
| F2 | Only one component selectable per category — need multiples (e.g. 4 RW, 2 antennas, multiple harnesses) | HIGH | 3h | TODO |
| F3 | No volume fit check when selecting structure size | HIGH | 4h | TODO |
| F4 | Budget summary doesn't compare to parametric breakdown or show % margin change | HIGH | 3h | TODO |
| F5 | Cost not updated from equipment selections | HIGH | 2h | TODO |
| F6 | No command/telemetry interface modelling per component | MED | 6h | TODO |
| F7 | No PC/104 pinout reference | MED | 3h | TODO |
| F8 | No power bus switched-line allocation / converter needs | MED | 4h | TODO |
| F9 | Orbit maintenance assumed for all missions — should be optional for low-cost | MED | 2h | TODO |

### Category G: UI & Workflow Bugs

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| G1 | Cannot answer position questions in single-user mode | HIGH | 2h | TODO |
| G2 | Gate review shows FAIL for completed alternatives | HIGH | 2h | TODO |
| G3 | Optimizer only available in session mode — should work solo | HIGH | 2h | TODO |
| G4 | Requirements with multiple parts not split into individual testable requirements | MED | 3h | TODO |
| G5 | Need to edit parametric data in design, equipment list directly | MED | 3h | TODO |

### Category H: Trade Studies & Positions

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| H1 | Trade studies need tabular format with criteria, weightings, thresholds, ratings | HIGH | 6h | TODO |
| H2 | Need additional positions: compliance/regulatory, user representative | MED | 3h | TODO |
| H3 | Simulator integration for equipment interface modelling | LOW | 8h | TODO |

---

## Reference Data (from deep research)

### CubeSat RF Licensing Options

| License Type | Band | Use Case | Restrictions | Cost | Timeline |
|-------------|------|----------|-------------|------|----------|
| IARU Amateur | VHF 145.8-146 MHz, UHF 435-438 MHz | Educational, non-commercial | No encryption (except TC), no revenue, open data | Free | 2-6 months |
| FCC Part 5 Experimental | Any (justified) | R&D, tech demo | No revenue, time-limited | ~$5K | 3-6 months |
| ISED Developmental (Canada) | Any (justified) | R&D, tech demo | No revenue, no-interference basis | Varies | 126 days |
| FCC Part 25 Commercial | S-band 2200-2290, X-band 8025-8400, Ka | Commercial operations | Full ITU filing required | $30-45K + ITU fees | 6-12 months |
| ISED CPC-2-6-02 (Canada) | S/X/Ka | Commercial operations | 50% Canadian capacity for 6 months | Varies | 126 days |

### Launch Provider Pricing (2026)

| Provider | Vehicle | Price | Capacity | Lead Time |
|----------|---------|-------|----------|-----------|
| SpaceX Transporter | Falcon 9 | $350K min (≤50kg) + $7K/kg above | SSO 525 km | 6-12 months |
| Rocket Lab | Electron | ~$7.5M dedicated | 200 kg SSO | 6-18 months |
| Exolaunch | Broker (various) | Custom quotes | Via F9/Vega-C | 9-18 months |
| D-Orbit | ION carrier | ~$100K per CubeSat | Custom orbits | 12+ months |
| ISILaunch | Broker (various) | Custom quotes | Via PSLV/F9/Vega | 12-24 months |
| Firefly | Alpha | ~$15M dedicated | 745 kg SSO | 12-18 months |
| NanoRacks | ISS deploy | ~$90K/U | ISS orbit only | 6-12 months |

### Validation Missions

| Mission | Type | Form | Mass | Orbit | Comms | Propulsion |
|---------|------|------|------|-------|-------|------------|
| Planet SuperDove | EO optical | 3U | 5.2 kg | 525 km SSO | UHF + X-band 220 Mbps | None |
| MarCO | Deep space relay | 6U | 14 kg | Heliocentric | X-band + UHF (DSN) | Cold gas 40 m/s |
| Spire LEMUR-2 | AIS + GNSS-RO | 3U | 4.6 kg | 400-600 km SSO | UHF + S + X-band | None |
| ICEYE | SAR | Micro 85 kg | 85 kg | SSO | X-band 140 Mbps | Ion |
| CAPSTONE | Lunar NRHO | 12U | 25 kg | Lunar NRHO | X + S-band (DSN) | Hydrazine 200 m/s |
| Astrocast | IoT/M2M | 3U | 4 kg | 500 km SSO | L-band | None |
| NorSat-1 | AIS + science | NEMO micro | 16 kg | 600 km SSO | VHF + S-band | None |

---

## Prioritised Resolution Phases

### Phase 1: Critical Bug Fixes & Immediate Usability
*Estimated: 1 day*

- **F1**: Enforce RF compatibility at selection time — block incompatible antenna/transponder pairs
- **F2**: Allow multiple selections per category (multiple antennas, RW, harnesses, thermal items)
- **G1**: Position questions work in single-user mode (remove session gate)
- **G2**: Gate review properly evaluates mission alternatives from store
- **G3**: Optimizer works without session (use designStore directly)
- **C6**: Remove multispectral assumption for non-optical missions
- **F9**: Orbit maintenance optional (checkbox in requirements)

### Phase 2: Equipment Budget Intelligence
*Estimated: 2 days*

- **F3**: Volume fit check — when selecting structure, show whether selected equipment fits
- **F4**: Budget comparison — show parametric estimate vs selected equipment, margin % change
- **F5**: Cost updates from selections — replace parametric cost with actual COTS pricing
- **F8**: Power bus allocation — show which equipment on which EPS switched lines
- **G4**: Split compound requirements into individually testable requirements
- **G5**: Editable parametric data and equipment list in design view

### Phase 3: RF Licensing & Spectrum
*Estimated: 3 days*

- **C1**: Licensing constraints in comms — filter transponders by license type (amateur/experimental/commercial)
- **C5**: Transceiver options driven by mission need + available spectrum
- **C3**: ITU filing paperwork template generator (API, CR/C, notification)
- **C4**: IARU amateur coordination form generator
- **C2**: Spectrum allocation viewer — show allocated bands for orbit + ground location, identify clear frequencies

### Phase 4: Regulatory Paperwork
*Estimated: 2 days*

- **D1**: Canadian RSSSA filing template (for remote sensing missions)
- **D2**: Export control assessment — ITAR/EAR classification, controlled goods checklist
- **D3**: COPUOS registration template (UN Art IV fields)
- **D4**: End-of-life analysis report (debris compliance + passivation plan)

### Phase 5: Launch Integration Module
*Estimated: 2 days*

- **E1**: Launch provider database (pricing, capacity, orbits, lead times)
- **E2**: Launch ICD template generator (mechanical, electrical, environmental, schedule)
- **E3**: Deployer selection linked to structure size (ISIPOD/EXOpod/CSD/NRCSD)
- **E4**: Separation switch tracking (3 inhibits, RBF pin, deployment switches)
- **E5**: Environmental test levels from selected launch vehicle

### Phase 6: Trade Studies & Positions
*Estimated: 2 days*

- **H1**: Tabular trade studies with criteria, weightings, thresholds, qualitative ratings
- **H2**: Additional positions (compliance/regulatory engineer, user representative, mission ops)
- **F6**: Command/telemetry interface modelling per component
- **F7**: PC/104 pinout reference

### Phase 7: Constellation & Beyond-LEO
*Estimated: 3 days*

- **A1-A4**: Constellation mode (Walker delta, coverage analysis, per-satellite + constellation budgets)
- **B1-B5**: Beyond-LEO orbits (MEO/GEO/HEO/Lunar), power scaling, DSN links, insertion ΔV

### Phase 8: Validation & Deep Integration
*Estimated: 2 days*

- Validate against 7 reference missions (Planet, MarCO, Spire, ICEYE, CAPSTONE, Astrocast, NorSat)
- Fix any systematic errors found in sizing models
- **H3**: Simulator integration for equipment interfaces

---

## Total Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Phase 1: Bug fixes | 1 day | None |
| Phase 2: Budget intelligence | 2 days | Phase 1 |
| Phase 3: Spectrum/licensing | 3 days | Phase 1 |
| Phase 4: Regulatory | 2 days | Phase 3 |
| Phase 5: Launch integration | 2 days | Phase 1 |
| Phase 6: Trades & positions | 2 days | None |
| Phase 7: Constellation/beyond-LEO | 3 days | Phase 2 |
| Phase 8: Validation | 2 days | All above |
| **TOTAL** | **~17 working days** | |
