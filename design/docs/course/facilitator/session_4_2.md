# Session 4.2: Verification & Validation Matrix and Compliance


**Prerequisites:** Session 4.1 (equipment selected, BOM constructed)
**References:** ECSS-E-ST-10-02C Rev.1 (Verification), ECSS-E-ST-10-03C (Testing), NASA SEH Rev 2 sections 5.3-5.4, MIL-STD-1540E, MIL-STD-461G

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Distinguish between verification and validation using the ECSS/NASA definitions
2. Assign appropriate verification methods (ATIR(D)) to each requirement using a decision logic
3. Define environmental test levels derived from launch vehicle ICD specifications
4. Construct a compliance verification matrix mapping every requirement to its method, level, and phase
5. Identify when waivers are appropriate and document the waiver rationale

---

## 1. Verification vs Validation: Precise Definitions
*[Source: ECSS-E-ST-10-02C Rev.1 section 4; NASA SEH Rev 2 section 5.3 (Process 7: Product Verification) and section 5.4 (Process 8: Product Validation)]*

| | **Verification** | **Validation** |
|--|-----------------|----------------|
| **Question** | "Did we build the system right?" | "Did we build the right system?" |
| **Checks against** | Requirements (shall statements) | Stakeholder needs and operational expectations |
| **Standard** | ECSS-E-ST-10-02C | ECSS-E-ST-10-06C |
| **Performed by** | Engineering team | Users, operators, stakeholders |
| **When** | Throughout development (Phases B-D) | End of development + early operations (Phase D-E) |
| **Methods** | ATIR(D) (Analysis, Test, Inspection, Review of design, Demonstration) | Operational demonstration, user acceptance testing |
| **Output** | Verification Control Document (VCD) | Validation report |

### The Critical Distinction

A system can be **verified** (every requirement marked "pass") but still **fail validation** if the requirements were written incorrectly. This happens when:
- Requirements were derived from misunderstood stakeholder needs
- The operational environment differs from assumptions
- Edge cases were not captured in requirements

### Example

- **Requirement:** "The system shall achieve GSD <= 10 m from 500 km altitude"
- **Verification (Test):** Calibration target imagery at 500 km -> measured GSD = 9.2 m -> **verified**
- **Validation:** Users attempt crop assessment with 9.2 m imagery -> "We can see field boundaries but cannot distinguish crop types; we needed GSD <= 5 m" -> **not validated**

*The requirement was met, but the stakeholder need was not satisfied because the requirement was insufficiently stringent.*

---

## 2. ATIR(D) Verification Methods in Detail
ECSS-E-ST-10-02C Rev.1 §5.2.2.1 defines four verification methods: test (including demonstration), analysis (including similarity), review of design and inspection. NASA practice lists demonstration separately as a fifth method. This book uses the full set, abbreviated ATIR(D); review of design is described in the facilitator book, Chapter 4.2.

*[Source: ECSS-E-ST-10-02C Rev.1 §5.2.2; freely available from https://ecss.nl]*

### Inspection (I)

**Definition:** Visual or physical examination of the product, without operation or stimulation, to verify conformance to requirements.

**When to use:**
- Physical characteristics (dimensions, mass, surface finish, labelling)
- Manufacturing workmanship (solder joints, cable routing, MLI installation)
- Markings, identification, and safety labels
- Mechanical fit (deployer rail compliance)

**Evidence produced:** Inspection report with photographs, measurements, pass/fail checklist.

**Examples for CubeSats:**
- Mass measurement on calibrated scale -> verifies "M_dry <= 4.0 kg"
- Caliper measurement of rail profile -> verifies CDS dimensional compliance
- Visual inspection of antenna stowage -> verifies no protrusions beyond deployer envelope
- Workmanship inspection of PCB solder joints -> verifies IPC-A-610 Class 3

### Analysis (A)

**Definition:** Mathematical models, simulations, statistical analysis, or heritage comparison demonstrate compliance with acceptable confidence.

**When to use:**
- Physical testing is impossible or impractical (orbital lifetime, radiation total ionising dose)
- Early in development (Phase B) before hardware exists
- To demonstrate margin (link budget, thermal model, structural FEA)
- Statistical parameters (reliability prediction, debris casualty risk)
- Requirements involving orbital mechanics or mission-level performance

**Evidence produced:** Analysis report with model description, assumptions, inputs, results, uncertainty assessment, and sensitivity analysis.

**Examples for CubeSats:**
- Orbital mechanics analysis -> verifies revisit time requirement
- Thermal model (finite difference/finite element) -> verifies temperature within limits
- Link budget calculation -> verifies margin >= 3 dB at worst case
- Structural FEA -> verifies positive Margin of Safety under launch loads

> **Margin of Safety (structural):**
>
> MoS = (Allowable_stress / (Factor_of_Safety x Applied_stress)) - 1
>
> MoS must be >= 0 for all load cases.
> Factor_of_Safety: 1.25 (yield), 1.5 (ultimate) per ECSS-E-ST-32-10C.

### Demonstration (D)

**Definition:** The system is operated under controlled conditions to show that it performs as required, without requiring precise measurement of performance parameters.

**When to use:**
- Functional requirements ("the system shall deploy the antenna within 30 minutes of separation")
- Operational procedures ("the system shall respond to a mode change command within 5 seconds")
- Software functional requirements ("FDIR shall autonomously switch to safe mode on loss of attitude")

**Evidence produced:** Demonstration report with procedure, observations, photographs/video, pass/fail.

**Examples for CubeSats:**
- Antenna deployment test -> demonstrates deployment within time limit
- Safe mode entry test -> demonstrates autonomous FDIR response
- Ground station commanding test -> demonstrates full command chain

### Test (T)

**Definition:** Physical hardware subjected to controlled conditions; measured performance compared quantitatively to requirement thresholds.

**When to use:**
- Physical properties must be proven with quantitative measurement
- Environmental survivability must be demonstrated (vibration, thermal-vacuum, EMC)
- End-to-end functional chains must be proven under representative conditions
- Performance must be measured, not just observed

**Test types by purpose:**

| Test Type | Purpose | Level | Phase | Loads/Conditions |
|-----------|---------|-------|-------|-----------------|
| **Development** | Explore design space, find problems early | Unit/BB | B | As needed |
| **Qualification** | Prove design withstands worst-case + margin | Unit/System | C | Qual levels (MPE + margin) |
| **Acceptance** | Prove flight hardware is defect-free | System | D | Acceptance levels (MPE) |
| **Proto-flight** | Combined qual + acceptance (single unit) | System | C/D | Qual levels, acceptance duration |

### Proto-Flight Approach

For CubeSats, the **proto-flight** approach is standard because building a separate qualification unit is prohibitively expensive. The flight unit is tested to **qualification levels** but for **acceptance duration**.

*[Source: ECSS-E-ST-10-03C §4.5.4; MIL-STD-1540E section 6.2.4]*

**Rationale:** Qualification duration is longer and more stressful -- this is acceptable for a dedicated qualification model that will not fly. For proto-flight, the shorter duration reduces fatigue life consumption while still screening for workmanship defects.

| Parameter | Qualification | Acceptance | Proto-flight |
|-----------|-------------|-----------|-------------|
| Vibration level | MPE + 3 dB | MPE | MPE + 3 dB |
| Vibration duration | 2 min/axis | 1 min/axis | 1 min/axis |
| TVAC temperature range | Predicted +/- 15 C | Predicted +/- 10 C | Predicted +/- 10 C |
| TVAC cycles | 8 | 4 | 4 |
| Sine sweep rate | 2 oct/min | 4 oct/min | 4 oct/min |

The proto-flight levels follow the standards: GSFC-STD-7000B §2.6 (predicted +/- 10 C, at least 4 cycles) and ECSS-E-ST-10-03C (sine at 2 oct/min for qualification, Table 5-2, and 4 oct/min for acceptance, Table 5-4; proto-flight takes the acceptance duration).

---

## 3. Environmental Test Programme
*[Source: ECSS-E-ST-10-03C (Testing); Launch vehicle Payload User's Guides; MIL-STD-1540E]*

### Standard Environmental Test Sequence

The test sequence is designed so that each test stresses the hardware in a specific way, and functional tests between environmental tests detect any damage.

<!--
SVG Description: Environmental Test Sequence Flow Diagram

A vertical flowchart with boxes connected by downward arrows:
1. [Receive Flight Hardware] -> 
2. [Initial Functional Test (baseline)] ->
3. [Sine Vibration (3 axes)] ->
4. [Random Vibration (3 axes)] ->
5. [Post-Vibration Functional Test] ->
6. [Thermal Vacuum (4 cycles)] ->
7. [Post-TVAC Functional Test] ->
8. [EMC Test (if required)] ->
9. [Mass Properties Measurement] ->
10. [Deployer Fit Check] ->
11. [Final Functional Test] ->
12. [Pack and Ship to Launch Site]

Decision diamond after step 5: "Any anomaly?" 
  Yes -> "Investigate and resolve before proceeding"
  No -> Continue to step 6
-->

```
 +--------------------------+
 | Receive Flight Hardware  |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Initial Functional Test  |  <- Reference baseline
 +-----------+--------------+
             |
 +-----------v--------------+
 | Sine Vibration (3 axes)  |  <- Low-frequency loads
 +-----------+--------------+
             |
 +-----------v--------------+
 | Random Vibration (3 axes)|  <- Broadband acoustic loads
 +-----------+--------------+
             |
 +-----------v--------------+        +-------------------+
 | Post-Vibe Functional Test| ------>| Anomaly?          |
 +-----------+--------------+  Fail  | Investigate &     |
             | Pass                  | resolve           |
 +-----------v--------------+        +-------------------+
 | Thermal Vacuum Testing   |  <- 4 cycles, func at extremes
 +-----------+--------------+
             |
 +-----------v--------------+
 | Post-TVAC Functional Test|
 +-----------+--------------+
             |
 +-----------v--------------+
 | EMC Test (if required)   |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Mass + CG Measurement    |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Deployer Fit Check       |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Pack & Ship to Launch    |
 +--------------------------+
```

### Sine Vibration Test Levels

*[Source: representative CubeSat rideshare envelope; the deployer or launch-vehicle user's guide sets the binding levels]*

Sine vibration simulates the low-frequency launch vehicle structural modes (typically 5-100 Hz). These are quasi-static loads.

| Frequency Range (Hz) | Level | Notes |
|----------------------|-------|-------|
| 5 - 100 | 1.25 g (0-peak) | Acceleration-controlled over the whole band; no displacement band |
| Sweep rate | 4 octaves/minute (proto-flight) | 2 oct/min is the qualification rate |
| Axes | 3 (X, Y, Z) | Sequential, one axis at a time |

> **Why there is no displacement band -- the crossover frequency:**
>
> a = (2 * pi * f)^2 * d, so f_c = sqrt(a / d) / (2 * pi)
>
> For a = 1.25 g = 12.26 m/s^2 and a typical shaker stroke limit d = 12.5 mm = 0.0125 m:
> f_c = sqrt(12.26 / 0.0125) / (2 * pi) = 31.3 / 6.283 = 4.98 Hz, about 5 Hz
>
> *Below about 5 Hz, holding 1.25 g would need more than 12.5 mm of displacement. This profile starts at 5 Hz, so it is acceleration-controlled throughout.*

### Random Vibration Test Levels

Random vibration simulates the broadband acoustic and mechanical environment during launch. Levels are specified as Power Spectral Density (PSD) in g^2/Hz.

| Frequency (Hz) | PSD Level (g^2/Hz) | Notes |
|----------------|---------------------|-------|
| 20 | 0.01 | Start of profile |
| 20 - 80 | +3 dB/octave ramp | Rising |
| 80 - 500 | 0.04 (flat) | Maximum level plateau |
| 500 - 2000 | -3 dB/octave ramp | Falling |
| 2000 | 0.01 | End of profile |
| **Overall gRMS** | **6.8 gRMS** | GSFC-STD-7000B (GEVS) minimum workmanship level |
| **Proto-flight** | **+3 dB: 9.6 gRMS** | PSD doubled at every frequency; 1 min per axis, 3 axes |

> **Computing Overall gRMS from PSD Profile:**
>
> gRMS = sqrt( integral from f1 to f2 of PSD(f) df )
>
> For a flat PSD region: gRMS_flat = sqrt(PSD_flat x (f2 - f1))
>
> Example: PSD = 0.04 g^2/Hz from 80-500 Hz:
> gRMS_flat = sqrt(0.04 x 420) = sqrt(16.8) = 4.10 gRMS
>
> The ramp sections and flat section are summed in quadrature:
> gRMS_total = sqrt(gRMS_ramp1^2 + gRMS_flat^2 + gRMS_ramp2^2)
>
> Integrating each sloped segment in log-log form gives 1.50 g^2 (20-80 Hz) + 16.80 g^2 (80-500 Hz) + 27.73 g^2 (500-2000 Hz) = 46.03 g^2, so gRMS = 6.78, about 6.8; proto-flight (+3 dB, PSD x 2) gives sqrt(92.06) = 9.6 gRMS.

### Thermal Vacuum Test Profile

| Parameter | Proto-flight Level | Notes |
|-----------|-------------------|-------|
| Hot case temperature | Predicted max + 10 C | e.g., if thermal model predicts +55 C -> test to +65 C |
| Cold case temperature | Predicted min - 10 C | e.g., if thermal model predicts -20 C -> test to -30 C |
| Number of cycles | 4 (proto-flight) | Start and end at hot; functional test at each extreme |
| Vacuum level | < 10^-5 mbar | Space-representative vacuum |
| Dwell time at extreme | >= 1 hour | Allow thermal stabilisation (< 1 C/hr gradient) |
| Temperature transition rate | 1-3 C/min | Limited by chamber capability |
| Functional test | Full performance at hot and cold extremes | Subset functional at intermediate transitions |

> **TVAC Cycle Duration Estimate:**
>
> t_cycle = 2 x (Delta_T / ramp_rate) + 2 x t_dwell + 2 x t_functional
>
> Example: Delta_T = 95 C (from -30 to +65 C), ramp = 2 C/min, dwell = 1 hr, functional = 2 hr:
> t_cycle = 2 x (95/2 min) + 2 x 60 min + 2 x 120 min = 95 + 120 + 240 = 455 min = 7.6 hr
>
> Total TVAC campaign (4 cycles + setup): ~4 x 7.6 + 8 = 38.4 hr ~ 5 working days

### EMC Testing

*[Source: MIL-STD-461G; ECSS-E-ST-20-07C]*

| Test | Standard | Purpose |
|------|----------|---------|
| CE102 Conducted Emissions | MIL-STD-461G | Measure spurious conducted emissions on power lines |
| RE102 Radiated Emissions | MIL-STD-461G | Measure unintentional RF radiation from satellite |
| CS101 Conducted Susceptibility | MIL-STD-461G | Verify immunity to power line transients |
| RS103 Radiated Susceptibility | MIL-STD-461G | Verify immunity to external RF fields |

*Note: EMC testing is not always required for CubeSats. It depends on the launch provider and co-manifested payloads. Check the rideshare ICD.*

---

## 4. Compliance Verification Matrix Construction
The Verification Matrix (also called Compliance Matrix or Verification Cross-Reference Matrix, VCRM) is the central document linking every requirement to its verification evidence.

*[Source: ECSS-E-ST-10-02C Rev.1 section 6; DRD in Annex A]*

### Matrix Structure

| Req ID | Requirement Text | Method | Phase | Level | Responsible | Facility | Status | Evidence |
|--------|-----------------|--------|-------|-------|-------------|----------|--------|----------|
| SYS-001 | M_dry <= 4.0 kg | I | D | System | Structures | Clean room | Planned | Mass measurement report |
| SYS-002 | Survive 9.6 gRMS random (proto-flight) | T | C/D | System | Structures | Vibe lab | Planned | Vibration test report |
| SYS-003 | GSD <= 10 m at 500 km | A | B | System | Payload | N/A | Planned | Optical analysis report |
| SYS-004 | Link margin >= 3 dB | A | B | System | Comms | N/A | Planned | Link budget analysis |
| SYS-005 | Antenna deploys < 30 min | D | D | System | Mechanisms | Clean room | Planned | Deployment demonstration |

### ATIR(D) Assignment Decision Logic

```
Is it a physical property (mass, dimensions, surface finish)?
  -> Inspection (I), Phase D, System level

Can it only be proven by quantitative measurement under controlled conditions?
  -> Test (T), Phase C/D, Unit or System level

Can it be demonstrated by operating the system (functional, not precision)?
  -> Demonstration (D), Phase D, System level

Can it be shown with acceptable confidence through modelling or similarity?
  -> Analysis (A), Phase B/C, System level

Is it a document, a process, a plan, or a design feature evident from the drawings?
  -> Review of design (R), Phase B
```

### Multiple Methods

Some requirements need **both** analysis (early confidence) and test (final proof):

| Requirement | Analysis (Phase B) | Test (Phase C/D) |
|------------|-------------------|------------------|
| Structural survival under launch loads | FEA with positive MoS | Vibration test -- no damage |
| Pointing accuracy <= 0.1 deg | Error budget analysis | On-orbit calibration measurement |
| Thermal within limits (-20 to +55 C) | Thermal model simulation | TVAC functional test at extremes |
| RF link margin >= 3 dB | Link budget calculation | RF compatibility test (if feasible) |

In the matrix, list the **primary** method and note "confirmed by [secondary method] in Phase [X]".

### Waiver Process

When a requirement cannot be verified by the prescribed method, a **waiver** is needed:

| Waiver Type | When Used | Approval Level |
|-------------|-----------|---------------|
| **Non-compliance** | Requirement cannot be met; accept deviation | Project manager + customer |
| **Method deviation** | Different verification method used (e.g., analysis instead of test) | Systems engineer + quality |
| **Tailoring** | Standard requirement not applicable to this mission | Systems engineer |

**Waiver documentation must include:** Requirement ID, deviation description, technical justification, risk assessment, and compensating measures.

---

## 5. SpaceCDF V&V Matrix Exercise
### Instructions

1. Navigate to the **V&V Matrix** tab in SpaceCDF
2. Requirements are auto-populated from the design
3. For each requirement, assign:
   - **Method:** A, T, I, R or D (use the decision logic above)
   - **Phase:** When will verification occur (B, C, D)?
   - **Level:** Unit, subsystem, or system level?
   - **Status:** All should be "Planned" at this stage
4. Use the **filter buttons** to view by method type:
   - Count: How many are Analysis? Test? Inspection? Review of design? Demonstration?
   - Are there any requirements with no method assigned?
5. Identify requirements that need **two methods** (analysis in Phase B + test in Phase D)
6. Discuss with your team: which tests are most critical? Which drive the test campaign schedule?

### Worksheet 4.2 Tasks

1. Assign an ATIR(D) method to 10 key requirements (justify each choice)
2. Identify 3 requirements that need both analysis AND test
3. Specify the complete environmental test sequence for your mission
4. Determine which test levels apply from your selected launch vehicle PUG
5. Identify any requirements that may need waivers -- document the rationale

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-10-02C Rev.1 (Verification) | https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification/ |
| 2 | ECSS-E-ST-10-03C (Testing) | https://ecss.nl/standard/ecss-e-st-10-03c-testing/ |
| 3 | NASA SEH Rev 2 sections 5.3-5.4 | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| 4 | MIL-STD-1540E (Test Requirements for Launch/Upper Stage/Space Vehicles) | https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=36197 |
| 5 | MIL-STD-461G (EMI/EMC) | https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=35789 |
| 6 | CubeSat Design Specification Rev 14.1 | https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| V vs V | Verification = meets requirements (ATIR(D)); Validation = meets stakeholder needs |
| ATIR(D) | Analysis (models and similarity), Test (quantitative), Inspection (physical), Review of design (documents and drawings), Demonstration (functional) |
| Proto-flight | CubeSats: single flight unit tested to qualification levels, acceptance duration |
| Sine vibration | 5-100 Hz, 1.25 g, 4 oct/min for proto-flight (2 oct/min for qualification), 3 axes, no displacement band; quasi-static launch loads |
| Random vibration | 20-2000 Hz, GEVS workmanship 6.8 gRMS; proto-flight +3 dB (about 9.6 gRMS), 1 min/axis |
| TVAC | Proto-flight at predicted +/- 10 C (GSFC-STD-7000B / ECSS-E-ST-10-03C), 4 cycles, functional at each extreme; ~7.6 h per cycle |
| Compliance matrix | Per requirement: method + phase + level + responsible + status + evidence |
| Waivers | Document deviation, justification, risk, and compensating measures |
