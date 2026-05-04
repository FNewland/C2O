# Session 4.2: Verification & Validation Planning

**Duration:** 2 hours
**Prerequisites:** Session 4.1 (equipment selected, design converged)
**References:** ECSS-E-ST-10-02C Rev.1; NASA SEH §5.3-5.4; ECSS-E-ST-10-03C

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Distinguish between verification (meets requirements) and validation (meets needs)
2. Assign appropriate verification methods (ATRI) to each requirement
3. Define verification phases and levels (unit → subsystem → system)
4. Specify environmental test requirements from launch vehicle ICD
5. Use SpaceCDF's V&V Matrix to plan verification

---

## 1. Verification vs Validation (15 min)

### Teaching Notes

*[Source: NASA SEH §5.3 (Process 7) and §5.4 (Process 8); ECSS-E-ST-10-02C §4]*

| | **Verification** | **Validation** |
|--|-----------------|----------------|
| **Question** | "Did we build the system right?" | "Did we build the right system?" |
| **Checks against** | Requirements (shall statements) | Stakeholder needs and expectations |
| **Performed by** | Engineering team | Users/stakeholders |
| **When** | Throughout development (B-D) | End of development + operations (D-E) |
| **Methods** | ATRI (Analysis, Test, Review, Inspection) | Operational demonstration, user acceptance |

### Example

- **Requirement:** "The system shall achieve GSD ≤ 10 m"
- **Verification:** Calibration target imagery → measured GSD = 9.2 m → **requirement verified** ✓
- **Validation:** Users confirm imagery is adequate for crop assessment → **need validated** ✓

A system can be verified (meets every requirement) but still fail validation (doesn't actually solve the user's problem) — this happens when requirements were written incorrectly.

---

## 2. Verification Methods in Detail (25 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-02C Rev.1 §5.3 — verified in Session 2.1]*

### Analysis (A)

**What:** Mathematical models, simulations, or heritage comparison demonstrate compliance.

**When to use:**
- Physical testing impossible or impractical (e.g., orbital lifetime, radiation dose)
- Early in development (Phase B) before hardware exists
- To demonstrate margin (e.g., link budget analysis shows 6 dB margin)
- For statistical parameters (e.g., reliability prediction)

**Evidence produced:** Analysis report with model description, inputs, results, uncertainty assessment.

**Examples:**
- Orbital mechanics analysis → demonstrates revisit requirement met
- Thermal model → demonstrates temperature within limits
- Link budget → demonstrates margin ≥ 3 dB
- Structural FEA → demonstrates positive MoS under launch loads

### Test (T)

**What:** Physical hardware subjected to controlled conditions; measured performance compared to requirement.

**When to use:**
- Physical properties must be proven (mass, strength, functional performance)
- Environment survivability must be demonstrated (vibration, thermal-vacuum, EMC)
- Functional chains must be proven end-to-end

**Test types by purpose:**

| Test | Purpose | Level | Phase |
|------|---------|-------|-------|
| **Development** | Explore design space, find problems early | Unit/BB | B |
| **Qualification** | Prove design withstands worst-case + margin | Unit/system | C |
| **Acceptance** | Prove flight hardware is defect-free | System | D |
| **Proto-flight** | Combined qual+acceptance (for CubeSats) | System | C/D |

**Proto-flight approach:** CubeSats typically use proto-flight testing — the flight unit is tested to qualification levels (but qualification duration) because building a separate qualification unit is too expensive.

### Review of Design (R)

**What:** Examination of design documentation, drawings, analyses, or procedures.

**When to use:**
- Programmatic requirements (e.g., "shall have a risk management plan")
- Process requirements (e.g., "shall use CM procedures")
- Requirements verifiable by examining the design itself

**Examples:**
- Operations manual review → demonstrates ops procedures defined
- Software architecture review → demonstrates FDIR implemented
- ICD review → demonstrates interfaces defined

### Inspection (I)

**What:** Visual or physical examination without operation or stimulation.

**When to use:**
- Physical characteristics (dimensions, labelling, surface finish)
- Manufacturing workmanship (solder joints, cable routing)
- Markings and identification

**Examples:**
- Measure mass on scale → demonstrates mass ≤ requirement
- Measure dimensions with caliper → demonstrates CDS compliance
- Visual inspection of thermal blankets → demonstrates proper installation

---

## 3. Environmental Test Programme (30 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-03C; Launch vehicle ICDs]*

### Standard Environmental Test Sequence

For a CubeSat proto-flight campaign:

```
1. Initial functional test (reference baseline)
2. Vibration testing (sine + random, 3 axes)
3. Intermediate functional test (check nothing broke)
4. Thermal vacuum testing (qualification temp range, 4-8 cycles)
5. Final functional test (confirm full functionality)
6. EMC testing (if required by launch provider)
7. Mass properties measurement (mass, CG)
8. Fit check in deployer (dimensional verification)
```

### Vibration Test Levels

Derived from launch vehicle ICD (Payload User's Guide). Typical for Falcon 9 Transporter:

**Random vibration (per axis, 1 minute qualification duration):**

| Frequency (Hz) | PSD Level (g²/Hz) |
|---------------|--------------------|
| 20-50 | +3 dB/oct ramp |
| 50-800 | 0.04 |
| 800-2000 | -6 dB/oct ramp |
| Overall (gRMS) | ~7.0 gRMS |

**Sine vibration (per axis):**
| Frequency (Hz) | Level (g) |
|---------------|----|
| 5-8 | 12.5 mm (displacement) |
| 8-100 | 1.25 g |

### Thermal Vacuum Test

| Parameter | Proto-flight Level | Notes |
|-----------|-------------------|-------|
| Hot case | Predicted max + 10°C | Qualification margin |
| Cold case | Predicted min - 10°C | Qualification margin |
| Cycles | 4 minimum | Start/end at hot; functional at each extreme |
| Vacuum | < 10⁻⁵ mbar | Space-representative |
| Dwell time | ≥ 1 hour at each extreme | Thermal stabilisation |

### EMC Testing

| Test | Standard | Purpose |
|------|----------|---------|
| Conducted emissions | MIL-STD-461G CE102 | TX spurious on power lines |
| Radiated emissions | MIL-STD-461G RE102 | Unintentional radiation |
| Conducted susceptibility | MIL-STD-461G CS101 | Immunity to power line noise |
| Radiated susceptibility | MIL-STD-461G RS103 | Immunity to external RF |

---

## 4. V&V Matrix Assignment (20 min)

### Teaching Notes

The V&V Matrix assigns a verification method, phase, level, and responsible position to each requirement.

### Decision Logic

```
Is it a physical property (mass, dimensions)?
  → Inspection (I), Phase D
Can it only be proven by operating the hardware?
  → Test (T), Phase C/D
Can it be demonstrated by analysis with acceptable confidence?
  → Analysis (A), Phase B/C
Is it a process, document, or plan?
  → Review (R), Phase B
```

### Multiple Methods

Some requirements need **both** analysis (early confidence) and test (final proof):
- "Structure shall survive launch loads" → Analysis (Phase B FEA) + Test (Phase C vibration)
- "Pointing shall be ≤ 0.1°" → Analysis (Phase B error budget) + Test (Phase D on-orbit calibration)

In the V&V matrix, list the primary method for Phase B/C and note "confirmed by test" for Phase D.

---

## 5. SpaceCDF V&V Matrix Exercise (30 min)

### Instructions

1. Navigate to the **V&V Matrix** tab
2. Requirements are auto-populated from the design
3. For each requirement, assign:
   - **Method:** A, T, R, or I (use the decision logic above)
   - **Phase:** When will verification occur (B, C, D)?
   - **Level:** Unit, subsystem, or system level?
   - **Status:** All should be "planned" at this stage
4. Use the **filter buttons** to view by method type:
   - How many are Analysis? Test? Review? Inspection?
   - Are there any that have no method assigned?
5. Discuss with your team: which tests are most critical?

### Worksheet 4.2 Tasks

1. Assign ATRI method to 10 key requirements (justify each choice)
2. Identify 3 requirements that need both analysis AND test
3. Specify the environmental test sequence for your mission
4. Determine which test levels apply from your selected launch vehicle

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| V vs V | Verification = meets requirements; Validation = meets needs |
| ATRI | Analysis (models), Test (hardware), Review (documents), Inspection (physical) |
| Proto-flight | CubeSats: single flight unit tested to qualification levels |
| Environmental | Vibration → TVAC → EMC → mass → fit check sequence |
| Test levels | Derived from launch vehicle ICD (PUG); 7 gRMS random typical |
| V&V matrix | Per-requirement: method + phase + level + responsible + status |
