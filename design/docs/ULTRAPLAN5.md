# SpaceCDF Ultraplan 5 — Systems & Subsystem Architecture

## Problem Statement

The tool currently supports:
- Mission-level architecture (space/ground/user segments via ConOps)
- Parametric subsystem sizing (agents compute mass/power/cost)
- Equipment selection (COTS components)

**Missing middle layer:**
- System architecture (block diagrams for each segment, interface definitions)
- Subsystem architecture (internal structure of each subsystem, redundancy choices)
- System-level requirements (derived from mission architecture selection)
- Subsystem-level requirements (derived from system architecture selection)

Per NASA SEH Process 4 (Design Solution Definition) and ECSS-E-ST-10C §5.4:
the architecture defines system boundaries, identifies interfaces, and enables
decomposition of requirements to lower levels.

---

## Architecture Levels (per NASA SEH §2.3)

```
Level 1: Mission Architecture (DONE — ConOps editor)
  "What segments exist? What are the external interfaces?"
  → Derives: Mission-level requirements

Level 2: System Architecture (NEW — this ultraplan)
  "What systems make up each segment? What are their functions?"
  → Space segment: Platform + Payload subsystem
  → Ground segment: Ground Station + MCC + Data Processing
  → Derives: System-level requirements

Level 3: Subsystem Architecture (NEW — this ultraplan)
  "How is each system structured internally? What redundancy?"
  → EPS: SA + Battery + PCDU + Distribution
  → AOCS: Sensors + Actuators + Control Electronics
  → TTC: TX + RX + Antenna + Diplexer
  → Derives: Subsystem-level requirements

Level 4: Component Selection (DONE — Equipment Browser)
  "Which specific hardware fulfils each function?"
  → Derives: Component specifications (from KB)
```

---

## What Each Position Needs at Each Level

### Systems Engineer
**Level 2 (System Architecture):**
- Define system boundaries (what belongs to platform vs payload vs ground)
- Allocate mass/power/cost budget to each system
- Identify inter-system interfaces (platform↔payload, spacecraft↔ground)
- Select architecture option (single-string vs redundant, centralised vs distributed)

**Level 3 (Subsystem Architecture):**
- Review each subsystem's internal architecture for single-point failures
- Verify interfaces between subsystems (N² matrix already exists)
- Track margin allocation per subsystem

### Power Engineer
**Level 2:** Define EPS architecture type
- Options: Direct Energy Transfer (DET) vs Peak Power Tracking (PPT)
- Battery topology: single string vs redundant, series/parallel configuration
- Bus type: unregulated, semi-regulated, fully regulated

**Level 3:** Internal EPS block diagram
- SA → MPPT → Bus → Battery charge controller → Distribution
- Switched lines allocation per subsystem
- Over-current protection strategy
- Heritage selection: which COTS EPS board

**Derived requirements:**
- SR-PWR-001: "The EPS shall provide regulated 3.3V and 5.0V buses"
- SR-PWR-002: "The EPS shall support ≥4 independently switched payload lines"
- SSR-PWR-001: "The battery shall provide ≥10 Wh at 30% DoD"

### AOCS Engineer
**Level 2:** Define AOCS architecture type
- Options: 3-axis stabilised, spin-stabilised, gravity gradient
- Sensor suite: fine (ST+gyro) vs medium (ST only) vs coarse (sun sensors)
- Actuator suite: RW+MTQ vs MTQ-only vs passive magnetic

**Level 3:** Internal AOCS block diagram
- Sensors → OBC (ADCS algorithm) → Actuators
- Redundancy: 4-wheel config (3+1) vs 3-wheel (no redundancy)
- Safe mode architecture (sun-pointing via sun sensors + MTQ)
- Momentum management strategy (MTQ desaturation frequency)

**Derived requirements:**
- SR-AOCS-001: "The AOCS shall achieve ≤0.1° pointing in imaging mode"
- SR-AOCS-002: "The AOCS shall autonomously enter safe mode on anomaly"
- SSR-AOCS-001: "Each reaction wheel shall provide ≥5 mNm torque"

### Communications Engineer
**Level 2:** Define comms architecture
- TTC approach: separate TTC + payload DL vs combined
- Bands: single-band (S-band for everything) vs dual-band (UHF TTC + X-band DL)
- Ground station strategy: own station, KSAT network, SatNOGS, DSN

**Level 3:** RF chain block diagram
- TX chain: Baseband → Modulator → Upconverter → PA → Filter → Antenna
- RX chain: Antenna → LNA → Downconverter → Demodulator → Baseband
- Redundancy: cold redundant TX? Dual antennas?
- Link budget per mode (TTC uplink, TTC downlink, payload downlink)

**Derived requirements:**
- SR-TTC-001: "The TTC shall provide ≥3 dB link margin at 10° elevation"
- SR-TTC-002: "The TTC shall support store-and-forward data delivery"
- SSR-TTC-001: "The S-band transmitter shall provide ≥2W RF output"

### Thermal Engineer
**Level 2:** Define thermal architecture
- Approach: fully passive vs passive + heaters vs active (heat pipes)
- Radiator allocation: dedicated face(s) vs distributed
- Insulation strategy: MLI coverage

**Level 3:** Thermal control block diagram
- Heat sources → Conduction paths → Radiator surfaces → Space
- Heater zones and control logic (thermostatic vs proportional)
- Temperature sensor placement

**Derived requirements:**
- SR-TCS-001: "All components shall remain within operating range [-20°C, +50°C]"
- SSR-TCS-001: "Radiator area shall be ≥0.02 m² on -Y face"

### Structures Engineer
**Level 2:** Define structural architecture
- CDS form factor selection (1U/3U/6U/12U) with volume budget
- Deployment mechanism architecture (SA hinges, antenna deployment)
- Launch interface (deployer type)

**Level 3:** Structural block diagram
- Primary structure (frame + rails)
- Secondary structure (brackets, mounting hardware)
- Mechanisms (deployment, separation)
- Component mounting plan (which board on which slot in PC/104 stack)

**Derived requirements:**
- SR-STR-001: "Structure shall survive qualification loads with MoS ≥0"
- SR-STR-002: "First natural frequency shall be ≥40 Hz"
- SSR-STR-001: "PC/104 stack shall accommodate ≥8 boards in 3U"

### Propulsion Engineer
**Level 2:** Propulsion architecture decision
- Options: no propulsion, cold gas, electric, chemical
- If propulsion: tank location, thruster orientation, plume shielding

**Level 3:** Propulsion block diagram (if applicable)
- Tank → Feed system → Thruster
- Valve control logic
- Propellant management (passive/active)

### Payload Lead
**Level 2:** Payload architecture
- Instrument type and operating concept
- Data handling approach (raw storage vs on-board processing)
- Payload-bus interface definition

**Level 3:** Payload internal block diagram
- Sensor → Electronics → Data interface → OBC
- Calibration approach
- Thermal control needs (detector cooling?)

### Data/OBC Engineer (Software Engineer)
**Level 2:** C&DH architecture
- OBC redundancy (single vs hot/cold redundant)
- Data storage approach (onboard NVM, SRAM, flash)
- Software architecture (RTOS, Linux, bare-metal)

**Level 3:** Software block diagram
- Mode manager → ADCS control → TM/TC handler → Payload interface → FDIR
- Inter-process communication
- Watchdog and safe mode entry logic

### Ground Segment Engineer
**Level 2:** Ground architecture
- Station network (single owned, commercial, federated)
- MCS architecture (COSMOS, OpenMCT, Yamcs, custom)
- Data processing pipeline (L0→L1→L2→L3)

**Level 3:** Ground block diagram
- Antenna → Front-end → Baseband → Frame sync → TM extraction
- MCS → Commanding → Scheduling → Planning
- Data pipeline → Archive → Distribution API

---

## UI Design: Architecture Selection Tool

### New Component: SystemArchitectureEditor

A tabbed editor that works at Level 2 and Level 3:

**Tab structure:**
```
Space Segment Architecture
  ├── Platform Architecture (block diagram with options)
  ├── EPS Architecture (DET/PPT/regulated/unregulated)
  ├── AOCS Architecture (3-axis/spin/gravity-gradient)
  ├── TTC Architecture (single/dual-band, ground strategy)
  ├── Thermal Architecture (passive/active)
  ├── Structure Architecture (form factor, mechanisms)
  ├── Propulsion Architecture (none/cold-gas/electric/chemical)
  ├── OBC Architecture (single/redundant, OS choice)
  └── Payload Architecture (type-specific)

Ground Segment Architecture
  ├── Station Network (topology, coverage)
  ├── Mission Control (MCS choice)
  └── Data Processing (pipeline definition)
```

### Interaction Pattern

For each subsystem:
1. **Show architecture options** as selectable cards (e.g., "3-axis stabilised" vs "magnetorquer-only")
2. **Each option shows:** typical mass/power/cost impact, TRL, heritage, pros/cons
3. **Selecting an option:**
   - Auto-derives system requirements for that subsystem
   - Updates the parametric model (e.g., selecting "4-wheel redundant" changes AOCS mass estimate)
   - Identifies interfaces created by this choice
   - Marks design as stale → triggers reconvergence
4. **Show block diagram** (SVG) for the selected architecture
5. **Show derived requirements** that result from this architecture choice

### Requirement Generation Flow

```
Architecture selection → Derived requirements generated
  → Requirements appear in Requirements Editor (level: system/subsystem)
  → Requirements feed into V&V matrix
  → Requirements feed into compliance checking
```

---

## Implementation Plan

### Phase 1: Data Model (backend)
- Add `SystemArchitecture` model with per-subsystem architecture choices
- Add architecture options catalogue (EPS: 3 options, AOCS: 4 options, etc.)
- Add requirement derivation rules per architecture choice
- Add block diagram SVG generation per architecture

### Phase 2: Architecture Options API
- GET /api/architecture/options/{subsystem} → available architectures
- POST /api/architecture/select → choose architecture, derive requirements
- GET /api/architecture/diagram/{subsystem} → SVG block diagram

### Phase 3: Frontend Component
- New `SystemArchitectureEditor` component
- Architecture option cards with select/compare
- Block diagram display (SVG viewer)
- Derived requirements list with accept/reject
- Integration with designStore (stale detection, reconvergence)

### Phase 4: Position-Specific Views
- Each position sees their subsystem architecture prominently
- Systems engineer sees the full picture
- Cross-cutting views for interfaces between subsystems

### Phase 5: Requirement Derivation Engine
- Rules: architecture choice → set of derived requirements
- Each requirement tagged with source (which architecture choice)
- If architecture changes, derived requirements update/remove

---

## Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Phase 1: Data model | 4h | None |
| Phase 2: API | 3h | Phase 1 |
| Phase 3: Frontend | 6h | Phase 2 |
| Phase 4: Position views | 3h | Phase 3 |
| Phase 5: Requirement derivation | 4h | Phase 3 |
| **TOTAL** | **~20h** | |

---

## Architecture Options Catalogue (per subsystem)

### EPS Options
| Option | Description | Mass Impact | Power | Cost | TRL | Pros | Cons |
|--------|-------------|-------------|-------|------|-----|------|------|
| Body-mounted SA + single battery | Simplest, lowest mass | Baseline | 7-12W (3U) | Low | 9 | Simple, proven | Limited power |
| Deployable SA + single battery | Higher power, moderate mass | +0.2 kg | 15-30W (3U) | Medium | 8 | More power | Deployment risk |
| Deployable SA + redundant battery | Highest reliability | +0.4 kg | 15-30W | Higher | 8 | Redundant | Mass, cost |
| Body-mounted + supercapacitor | Peak power handling | Similar | 7-12W + peaks | Medium | 7 | Peak loads | Limited energy storage |

### AOCS Options
| Option | Description | Pointing | Mass | TRL |
|--------|-------------|----------|------|-----|
| Passive magnetic | Permanent magnet alignment | ~10° | 0.05 kg | 9 |
| Magnetorquer-only | Active magnetic control | 2-5° | 0.1 kg | 9 |
| 3-wheel + MTQ | Medium pointing | 0.1-1° | 0.5 kg | 9 |
| 4-wheel + ST + MTQ | Fine pointing | <0.1° | 0.8 kg | 9 |
| 4-wheel + ST + gyro + MTQ | Very fine pointing | <0.01° | 1.2 kg | 8 |

### TTC Options
| Option | Description | Data Rate | Mass | Licensing |
|--------|-------------|-----------|------|-----------|
| UHF only (amateur) | Simple, low-rate | ≤19.2 kbps | 0.1 kg | IARU (free) |
| S-band only | Medium rate, single band | ≤10 Mbps | 0.2 kg | ISED+ITU |
| UHF TTC + S-band DL | Dual-band, moderate | 19.2k + 10M | 0.35 kg | IARU + ISED |
| UHF TTC + X-band DL | Dual-band, high rate | 19.2k + 200M | 0.5 kg | IARU + ISED+ITU |
| S-band TTC + X-band DL | Professional, high rate | 10M + 200M | 0.5 kg | ISED+ITU |

### Thermal Options
| Option | Description | Mass | Power | Typical Use |
|--------|-------------|------|-------|-------------|
| Passive only (coatings) | Surface finishes only | ~0 kg | 0 W | LEO, low power |
| Passive + heaters | Coatings + eclipse heaters | 0.05 kg | 1-3 W | Most CubeSats |
| Passive + heaters + MLI | Insulation blankets added | 0.1 kg | 1-3 W | Higher orbits |
| Active (heat pipes) | High conductance paths | 0.2 kg | 0 W | High-power payloads |

### Structure Options
| Option | Form Factor | Volume | Mass Limit | Deployer |
|--------|-------------|--------|------------|---------|
| 1U standard | 10×10×11.35 cm | 1000 cm³ | 2 kg | ISIPOD 1U |
| 3U standard | 10×10×34.05 cm | 3000 cm³ | 6 kg | ISIPOD 3U |
| 6U standard | 10×22.63×34.05 cm | 6000 cm³ | 12 kg | ISIPOD 6U / EXOpod |
| 12U standard | 22.63×22.63×34.05 cm | 12000 cm³ | 24 kg | ISIPOD 12U |
| Custom micro | Custom dimensions | Custom | Per launcher | Custom deployer |

### Propulsion Options
| Option | When Needed | ΔV Range | Mass | TRL |
|--------|-------------|----------|------|-----|
| None | Alt <500 km, short life OK | 0 | 0 | N/A |
| Drag sail | Alt 500-600 km, passive deorbit | N/A (drag) | 0.1-0.5 kg | 7-8 |
| Cold gas | Small ΔV, simple | 5-30 m/s | 0.3-1.0 kg | 9 |
| Electric (electrospray) | Medium ΔV, long-duration | 50-200 m/s | 0.5-1.5 kg | 7-8 |
| Chemical (green) | High ΔV, fast | 50-200 m/s | 1.0-3.0 kg | 7-8 |
