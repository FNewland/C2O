# SpaceCDF Product Roadmap

## Vision

A team walks into a room with a problem ("farmers need crop health data").
They walk out with a complete, buildable CubeSat design — flight software,
ground software, test procedures, procurement list, launch contract draft,
and training simulator — generated directly from the design decisions they
made together. The space mission design process compressed from years to days.

## Scope tiers

| Tier | Mission class | Goal | Feasibility |
|------|--------------|------|-------------|
| **Tier 1: Full lifecycle** | CubeSat (1U-12U) | Design through to flight-ready package | Achievable — COTS components, standard interfaces, published data |
| **Tier 2: Full lifecycle** | SmallSat (20-150 kg) | Design through to CDR-ready package | Achievable with deeper component DB and custom interface support |
| **Tier 3: Concept design** | Any mission (including deep space) | Pre-Phase A through PDR-level design | Achievable — parametric sizing + decision support (current capability) |
| **Tier 4: Full lifecycle** | Large/flagship missions | Not in scope — too bespoke, too many custom interfaces, ITAR constraints |

The sweet spot: **Tier 1 is the priority.** CubeSats have standardised buses,
COTS components with published datasheets, standard deployment interfaces
(P-POD, ISIPOD), well-documented RF allocations, and a mature rideshare
launch market. Everything needed to go from concept to "ready to order parts"
is available in the public domain.

## Roadmap stages

### Stage 1: Decision Engine (current work)
*Where we are now*

**Goal:** Every design decision is a structured question with alternatives,
consequences, and rationale — not a form field.

- [ ] Decision engine data model (46 decisions mapped to phases/gates)
- [ ] Decision cards in UI (question → alternatives → fit-gap → consequences)
- [ ] Ground segment architecture trade (first concrete decision module)
- [ ] Component fit-gap analysis (requirement vs capability, gap, downstream impact)
- [ ] TPM tracking with trend monitoring
- [ ] Verification traceability (requirement → test method → test status → objective)
- [ ] Decision maturity dashboard (how many decisions open/traded/decided/baselined)

### Stage 2: CubeSat Component Database
*Making Tier 1 real*

**Goal:** Complete COTS component coverage for CubeSat-class missions with
published specifications, so component selection produces buildable BOMs.

- [ ] Expand KB from 68 components to ~300+ covering all CubeSat subsystems:
  - Batteries (GomSpace, EXA, Clyde Space, Endurosat)
  - Solar panels (body-mount, deployable — GomSpace, DHV, Endurosat, MMA)
  - EPS/PCDU boards (GomSpace NanoPower, Clyde Space, Endurosat)
  - OBC boards (GomSpace NanoMind, ISIS iOBC, Endurosat OBC, Unibap iX5)
  - UHF/VHF transceivers (GomSpace AX100, Endurosat UHF, NanoAvionics)
  - S-band transceivers (Syrlinks, IQ Wireless, Endurosat)
  - X-band transmitters (Syrlinks, Tethers Unlimited, Endurosat)
  - Star trackers (Berlin Space Tech, Hyperion, Jena-Optronik)
  - Reaction wheels (Hyperion, CubeSpace, NewSpace Systems, Sinclair)
  - Magnetorquers (ZARM, CubeSpace, ISIS)
  - Sun sensors (Solar MEMS, NSS, Bradford)
  - GPS receivers (SkyFox Labs, NovAtel, u-blox)
  - Propulsion (Enpulsion, ThrustMe, Phase Four, Busek, Bradford)
  - Structures (ISIS, Endurosat, NanoAvionics, Pumpkin)
  - Deployment mechanisms (ISIS, Tyvak, Astro Digital)
  - Antennas (Endurosat, ISIS, Anywaves)
- [ ] Each component: full datasheet parameters (mass, dimensions, power,
  voltage range, temperature range, interfaces, TRL, heritage missions,
  price, lead time, export control status)
- [ ] Fit-gap scoring: automated comparison of component specs vs derived
  requirements, with gap identification and consequence analysis
- [ ] Bill of Materials (BOM) generator from selected components

### Stage 3: Interface & Harness Design
*Connecting the boxes*

**Goal:** Define every signal, connector, and cable between components.

- [ ] Standard CubeSat bus interfaces (PC/104, CAN, I2C, SPI, UART, SpaceWire)
- [ ] Connector library (Micro-D, SAMTEC, Hirose) with pin assignments
- [ ] Harness mass estimation from interface matrix + physical layout
- [ ] Interface verification matrix: every interface has a defined test
- [ ] EMC compatibility check: TX frequency vs detector sensitivity
- [ ] Auto-generated ICD documents per interface pair

### Stage 4: Flight Software Generation
*From ConOps modes to running code*

**Goal:** Generate compilable, testable flight software from design decisions.

- [ ] Extended cFS app generation from ConOps modes (mode manager, FDIR,
  safe mode entry/exit logic, autonomous decisions)
- [ ] Telemetry packet definitions from every output parameter
- [ ] Telecommand definitions from every controllable function
- [ ] Parameter database (on-board) from design state
- [ ] FDIR rules from FMECA: "if sensor X fails → switch to redundant Y →
  if Y also fails → enter safe mode"
- [ ] Mode transition state machine from ConOps mode table
- [ ] Housekeeping telemetry collection schedule
- [ ] FPrime / COSMOS / KubOS framework options alongside cFS

### Stage 5: Ground Segment & Operations
*Mission control from design*

**Goal:** Generate ground segment configuration and operations procedures.

- [ ] Ground station network selection (KSAT, AWS Ground Station, SatNOGS,
  Leaf Space) with pass prediction from orbit + station lat/long
- [ ] Mission Control System configuration (COSMOS, OpenMCT, Yamcs)
  auto-generated from telemetry/telecommand definitions
- [ ] Operations procedures from ConOps modes: nominal timeline,
  contingency procedures, commissioning sequence
- [ ] Pass planning and scheduling tool
- [ ] Data processing pipeline definition (L0 → L1 → L2) from
  payload specifications + user requirements
- [ ] Frequency coordination documentation (ITU filing prep)

### Stage 6: Test & Verification
*Test what you designed*

**Goal:** Generate test procedures and verification evidence structure.

- [ ] Test procedure generator per requirement (setup, stimulus, measurement,
  pass/fail criteria, data recording)
- [ ] Functional test procedure from interface verification matrix
- [ ] Environmental test specification from launch vehicle ICD
  (vibration, thermal vacuum, EMC levels)
- [ ] Test facility requirements estimation (clean room class,
  thermal vacuum chamber size, vibration table capacity)
- [ ] Verification closure tracking: planned → procedure written →
  executed → pass/fail → closed
- [ ] Test report template generation with auto-populated parameters

### Stage 7: Launch Campaign
*Getting to orbit*

**Goal:** Generate launch-ready documentation from design.

- [ ] Launch vehicle compatibility checker (mass, volume, interface,
  environments) against launcher user guides
- [ ] Rideshare broker integration (Spaceflight, Exolaunch, D-Orbit,
  ISILaunch) — mass/orbit/timeline matching
- [ ] Launch campaign timeline generator (shipping, integration,
  testing, fueling, encapsulation)
- [ ] Range safety documentation from debris compliance model
- [ ] Export control assessment from component origins
- [ ] Insurance documentation support (technical description for
  underwriters from design summary)
- [ ] Regulatory filing support: ITU frequency coordination,
  FCC/Ofcom licensing, space debris compliance certificate

### Stage 8: Training & Simulation
*Fly before you fly*

**Goal:** Generate a training simulator from the design.

- [ ] SpaceMissionSimulation (SMO) integration — extend the existing
  SMO exporter to produce a fully functional simulator, not just config
- [ ] Failure injection scenarios from FMECA
- [ ] Operator training scenarios from operations procedures
- [ ] Scoring criteria from mission success criteria
- [ ] Hardware-in-the-loop interface specification for FlatSat
- [ ] Digital twin configuration for operations support

## Timeline estimate

| Stage | Effort | Dependencies |
|-------|--------|--------------|
| 1: Decision engine | 2-4 weeks | Current work |
| 2: CubeSat component DB | 2-3 weeks | Web scraping + manual curation |
| 3: Interface & harness | 3-4 weeks | Stage 2 |
| 4: Flight software | 4-6 weeks | Stages 2, 3 |
| 5: Ground segment | 3-4 weeks | Stages 2, 4 |
| 6: Test & verification | 3-4 weeks | Stages 2, 3 |
| 7: Launch campaign | 2-3 weeks | Stages 2, 6 |
| 8: Training & simulation | 4-6 weeks | Stages 4, 5 |

**Total for CubeSat full lifecycle: ~6-9 months** of focused development.

The critical path runs through the component database (Stage 2) because
every downstream stage depends on having real, detailed component data.

## What exists today

| Capability | Stage | Status |
|-----------|-------|--------|
| 20 design agents (physics-based sizing) | 1 | Complete |
| Mission need → objectives → alternatives | 1 | Complete |
| ConOps modes → multi-mode sizing | 1 | Complete |
| Functional decomposition → requirements | 1 | Complete |
| Interface matrix with conflict detection | 1 | Complete |
| Gate review exit criteria (MCR/SRR/PDR) | 1 | Complete |
| Position Q&A with cross-position conflicts | 1 | Complete |
| Case studies validated against real missions | 1 | Complete |
| Multi-currency cost with paradigm switches | 1 | Complete |
| ECSS compliance pipeline (VP + tailoring) | 1 | Complete |
| 68 COTS components in KB | 2 | Partial (need ~300+) |
| cFS flight software scaffolding | 4 | Partial (scaffolding, not full apps) |
| SMO simulator config export | 8 | Partial (config only, not full sim) |
| MBSE export (ECSS-E-TM-10-25A JSON) | — | Complete |
| SRR/PDR/CDR document generation | — | Complete |
| Multi-user concurrent design sessions | — | Complete |
| Decision framework architecture | 1 | Documented, not yet implemented |

## Design principles

1. **Decisions, not forms.** Every interaction is a decision with context.
2. **Heritage first.** Prefer COTS components with flight heritage. Flag
   anything without heritage as a risk item requiring justification.
3. **Trace everything.** Every parameter traces to a requirement traces
   to a function traces to an objective traces to a stakeholder need.
4. **Generate, don't write.** Documents, software, test procedures, and
   configurations are generated from the design model — never hand-written
   from scratch.
5. **Verify as you go.** Verification obligations are created the moment
   requirements are written, not bolted on at the end.
6. **CubeSat-native.** The default path assumes CubeSat standards (PC/104,
   CubeSat Design Specification, ISIPOD interface). Larger missions
   are supported but require more manual input.
