# Chapter 14 — Verification and Validation

> **Recommended background.** ECSS-E-ST-10-02C Rev. 1 (Verification); ECSS-E-ST-10-03C (Testing); NASA SEH Rev 2 §5.3–5.4 (Product verification and validation); MIL-STD-1540E (Test requirements for launch, upper-stage and space vehicles); MIL-STD-461G (EMI/EMC). This chapter closes the right-hand side of the V-model introduced in Chapter 1 (Figure 1.1): the requirements of Chapter 5, each tagged with a verification method, now meet the hardware of Chapters 12 and 13. The launch-load environment that the test programme reproduces is described in Chapter 12 §12.1.5.

## Learning objectives

By the end of this chapter, you will be able to:

1. Distinguish between verification and validation using the ECSS and NASA definitions
2. Assign an appropriate verification method — analysis, test, inspection, review of design or demonstration, ATIR(D) — to each requirement using a decision logic
3. Define environmental test levels derived from launch-vehicle interface specifications
4. Construct a compliance verification matrix mapping every requirement to its method, level and phase
5. Identify when waivers are appropriate and document the waiver rationale

---

## 14.1 Verification versus validation: precise definitions

*[Source: ECSS-E-ST-10-02C Rev. 1 §4 and §5.2.2; NASA SEH Rev 2 §5.3 (Process 7: Product Verification) and §5.4 (Process 8: Product Validation)]*

| | **Verification** | **Validation** |
|--|-----------------|----------------|
| **Question** | "Did we build the system right?" | "Did we build the right system?" |
| **Checks against** | Requirements ("shall" statements) | Stakeholder needs and operational expectations |
| **Standard** | ECSS-E-ST-10-02C | ECSS-E-ST-10-06C |
| **Performed by** | Engineering team | Users, operators, stakeholders |
| **When** | Throughout development (Phases B–D) | End of development + early operations (Phases D–E) |
| **Methods** | ATIR(D): analysis, test, inspection, review of design, demonstration | Operational demonstration, user acceptance testing |
| **Output** | Verification control document (VCD) | Validation report |

### 14.1.1 The critical distinction

A system can be **verified** (every requirement marked "pass") but still **fail validation** if the requirements were written incorrectly. This happens when:
- Requirements were derived from misunderstood stakeholder needs
- The operational environment differs from the assumptions
- Edge cases were not captured in the requirements

### 14.1.2 Example

- **Requirement:** "The system shall achieve GSD ≤ 10 m from 500 km altitude"
- **Verification (test):** calibration-target imagery at 500 km → measured GSD = 9.2 m → **verified**
- **Validation:** users attempt crop assessment with 9.2 m imagery → "We can see field boundaries but cannot distinguish crop types; we needed GSD ≤ 5 m" → **not validated**

*The requirement was met, but the stakeholder need was not satisfied because the requirement was insufficiently stringent. This is why the stakeholder analysis and the MoE/MoP/TPM hierarchy of Chapter 4 matter: validation is only as good as the needs that were captured at the start.*

---

## 14.2 The ATIR(D) verification methods in detail

ECSS-E-ST-10-02C Rev. 1 §5.2.2.1 defines four verification methods — **test, analysis, review of design and inspection** — and NASA practice adds **demonstration** as a fifth. This book abbreviates the set as **ATIR(D)**, with the D in parentheses because ECSS counts demonstration as part of test ("test (including demonstration)") while NASA lists it separately. The ordering of the letters varies between documents; the methods are the same. Chapter 5 §5.5 introduced the five-row table; this section explains when each applies and what evidence it produces.

*[Source: ECSS-E-ST-10-02C Rev. 1 §5.2.2; NASA SEH Rev 2 §5.3.2]*

### 14.2.1 Analysis (A)

**Definition:** Mathematical models, simulations, statistical analysis or heritage comparison demonstrate compliance with acceptable confidence. ECSS includes *verification by similarity* (heritage) under analysis.

**When to use:**
- Physical testing is impossible or impractical (orbital lifetime, radiation total ionising dose)
- Early in development (Phase B) before hardware exists
- To demonstrate margin (link budget, thermal model, structural FEA)
- Statistical parameters (reliability prediction, debris casualty risk)
- Requirements involving orbital mechanics or mission-level performance

**Evidence produced:** Analysis report with model description, assumptions, inputs, results, uncertainty assessment and sensitivity analysis.

**Examples for CubeSats:**
- Orbital-mechanics analysis → verifies the revisit-time requirement (Chapter 7)
- Thermal model (finite difference/finite element) → verifies temperatures within limits (Chapter 9 §9.4)
- Link-budget calculation → verifies margin ≥ 3 dB at worst case (Chapter 11)
- Structural FEA → verifies a positive margin of safety under launch loads (Chapter 12 §12.1.6)

> **Margin of safety (structural)** — the canonical form is Chapter 12 §12.1.6:
> $$\text{MoS} = \frac{\sigma_{\text{allowable}}}{\text{FoS} \times \sigma_{\text{applied}}} - 1 \geq 0 \quad \text{for all load cases}$$
> with FoS = 1.25 (yield) and 1.5 (ultimate) for metallic structure per ECSS-E-ST-32-10C. An analysis report that verifies a structural requirement reports the MoS for every load case, not just the worst.

### 14.2.2 Test (T)

**Definition:** Physical hardware subjected to controlled conditions; measured performance compared quantitatively with the requirement thresholds.

**When to use:**
- Physical properties must be proven with quantitative measurement
- Environmental survivability must be demonstrated (vibration, thermal vacuum, EMC)
- End-to-end functional chains must be proven under representative conditions
- Performance must be measured, not just observed

**Test types by purpose:**

| Test type | Purpose | Level | Phase | Loads/conditions |
|-----------|---------|-------|-------|-----------------|
| **Development** | Explore the design space, find problems early | Unit/breadboard | B | As needed |
| **Qualification** | Prove the design withstands worst case + margin | Unit/system | C | Qualification levels (MPE + margin) |
| **Acceptance** | Prove the flight hardware is defect-free | System | D | Acceptance levels (MPE) |
| **Proto-flight** | Combined qualification + acceptance (single unit) | System | C/D | Qualification levels, acceptance duration |

*MPE = maximum predicted environment.*

**The proto-flight approach.** For CubeSats, the **proto-flight** approach is standard because building a separate qualification unit is prohibitively expensive. The flight unit is tested to **qualification levels** but for **acceptance duration**.

*[Source: ECSS-E-ST-10-03C §4.5.4; MIL-STD-1540E §6.2.4]*

**Rationale:** Qualification duration is longer and more stressful — this is acceptable for a dedicated qualification model that will not fly. For proto-flight, the shorter duration reduces fatigue-life consumption while still screening for workmanship defects.

| Parameter | Qualification | Acceptance | Proto-flight |
|-----------|-------------|-----------|-------------|
| Vibration level | MPE + 3 dB | MPE | MPE + 3 dB |
| Vibration duration | 2 min/axis | 1 min/axis | 1 min/axis |
| TVAC temperature range | Predicted ± 15 °C | Predicted ± 10 °C | Predicted ± 10 °C |
| TVAC cycles | 8 | 4 | 4 |
| Sine sweep rate | 2 oct/min | 4 oct/min | 4 oct/min |

The proto-flight levels follow the standards. GSFC-STD-7000B §2.6 tests a proto-flight unit at the maximum and minimum predicted temperatures ± 10 °C, with at least 4 cycles; ECSS-E-ST-10-03C reaches the same 10 °C with its 5 °C acceptance and 5 °C qualification margins on the predicted range. ECSS-E-ST-10-03C sweeps sine at 2 oct/min for qualification (Table 5-2) and 4 oct/min for acceptance (Table 5-4), and proto-flight takes the acceptance duration, hence 4 oct/min. The qualification and acceptance temperature columns are those of Chapter 9 §9.4.11.

### 14.2.3 Inspection (I)

**Definition:** Visual or physical examination of the product, without operation or stimulation, to verify conformance to requirements.

**When to use:**
- Physical characteristics (dimensions, mass, surface finish, labelling)
- Manufacturing workmanship (solder joints, cable routing, MLI installation)
- Markings, identification and safety labels
- Mechanical fit (deployer rail compliance)

**Evidence produced:** Inspection report with photographs, measurements and a pass/fail checklist.

**Examples for CubeSats:**
- Mass measurement on a calibrated scale → verifies "$M_{\text{dry}} \leq 4.0$ kg"
- Calliper measurement of the rail profile → verifies CDS dimensional compliance (Chapter 12 §12.1.3)
- Visual inspection of antenna stowage → verifies no protrusions beyond the deployer envelope
- Workmanship inspection of PCB solder joints → verifies IPC-A-610 Class 3

### 14.2.4 Review of design (R)

**Definition:** Verification by examination of design documentation — drawings, schematics, software design, analyses already performed, process records — to confirm that the design as documented satisfies the requirement. In ECSS-E-ST-10-02C this is a formal method in its own right, distinct from analysis: no new model is built; the evidence is the documented design.

**When to use:**
- Requirements on the existence or content of a document, process or plan ("a verification plan shall be produced", "the software shall be developed under ECSS-E-ST-40C")
- Design features that are self-evident from the drawings (number of deployment switches, presence of an RBF pin, connector pin-out)
- Requirements already covered by an approved heritage design

**Evidence produced:** Review-of-design record citing the documents examined, with the reviewer's signature; typically closed at a design review (Chapter 16).

**Examples for CubeSats:**
- Inspection of the stack schematic → verifies "two independent deployment switches shall inhibit all power"
- Examination of the software architecture document → verifies "the watchdog shall be implemented in hardware, independent of the main processor"

### 14.2.5 Demonstration (D)

**Definition:** The system is operated under controlled conditions to show that it performs as required, without requiring precise measurement of performance parameters.

**When to use:**
- Functional requirements ("the system shall deploy the antenna within 30 minutes of separation")
- Operational procedures ("the system shall respond to a mode-change command within 5 seconds")
- Software functional requirements ("FDIR shall autonomously switch to safe mode on loss of attitude")

**Evidence produced:** Demonstration report with procedure, observations, photographs or video, and a pass/fail statement.

**Examples for CubeSats:**
- Antenna deployment test → demonstrates deployment within the time limit
- Safe-mode entry test → demonstrates the autonomous FDIR response (Chapter 18)
- Ground-station commanding test → demonstrates the full command chain (Chapter 17)

---

## 14.3 Environmental test programme

*[Source: ECSS-E-ST-10-03C (Testing); launch-vehicle payload user's guides; MIL-STD-1540E]*

### 14.3.1 Standard environmental test sequence

The test sequence is designed so that each test stresses the hardware in a specific way, and functional tests between environmental tests detect any damage. Figure 14.1 shows the usual sequence for a proto-flight CubeSat. The levels in §14.3.2–14.3.4 are representative teaching values: the binding levels for a given flight are set by the deployer or launch-vehicle user's guide.

![Environmental test flow for a proto-flight CubeSat](../assets/figures/fig_test_flow.png)

**Figure 14.1** — The standard environmental test sequence for a proto-flight CubeSat. Functional tests bracket every environmental test so that damage is attributed to the test that caused it; an anomaly after vibration is investigated and resolved before the hardware goes into the thermal-vacuum chamber. The qualification, acceptance and proto-flight levels of §14.2.2 are listed beside the vibration and thermal-vacuum steps.

### 14.3.2 Sine vibration test levels

*[Source: representative CubeSat rideshare envelope; the deployer or launch-vehicle user's guide sets the binding levels]*

Sine vibration simulates the low-frequency launch-vehicle structural modes (typically 5–100 Hz). These are quasi-static loads.

| Frequency range (Hz) | Level | Notes |
|----------------------|-------|-------|
| 5–100 | 1.25 g (0–peak) | Acceleration-controlled over the whole band; no displacement band |
| Sweep rate | 4 octaves/minute (proto-flight) | 2 oct/min is the qualification rate |
| Axes | 3 (X, Y, Z) | Sequential, one axis at a time |

> **Why there is no displacement band — the crossover frequency:**
>
> For a sinusoid, $a = (2\pi f)^2\, d$, so the frequency at which a given acceleration corresponds to a given displacement is
>
> $$f_c = \frac{1}{2\pi}\sqrt{\frac{a}{d}}$$
>
> For $a = 1.25\,g_0 = 12.26$ m/s$^2$ and a typical shaker stroke limit $d = 12.5$ mm $= 0.0125$ m:
> $f_c = \sqrt{12.26/0.0125}\,/\,2\pi = 31.3/6.283 = 4.98$ Hz $\approx 5$ Hz
>
> *Below about 5 Hz, holding 1.25 g would need more than 12.5 mm of displacement, so a profile reaching lower frequencies needs a displacement-controlled band. This profile starts at 5 Hz, so it is acceleration-controlled throughout.*

### 14.3.3 Random vibration test levels

Random vibration simulates the broadband acoustic and mechanical environment during launch. Levels are specified as power spectral density (PSD) in g$^2$/Hz. The profile below is the GSFC-STD-7000B (GEVS) component minimum workmanship level (Table 2.4-4); GEVS Table 2.4-1 sets the proto-flight level at +3 dB for 1 minute per axis.

| Frequency (Hz) | PSD level (g$^2$/Hz) | Notes |
|----------------|---------------------|-------|
| 20 | 0.01 | Start of profile |
| 20–80 | +3 dB/octave ramp | Rising |
| 80–500 | 0.04 (flat) | Maximum-level plateau |
| 500–2000 | −3 dB/octave ramp | Falling |
| 2000 | 0.01 | End of profile |
| **Overall g$_{\text{rms}}$** | **6.8 g$_{\text{rms}}$** | Workmanship (acceptance) level |
| **Proto-flight** | **+3 dB: 9.6 g$_{\text{rms}}$** | PSD doubled at every frequency; 1 min per axis, 3 axes |

> **Computing the overall g$_{\text{rms}}$ from a PSD profile:**
>
> $$g_{\text{rms}} = \sqrt{\int_{f_1}^{f_2} \text{PSD}(f)\, df}$$
>
> For a flat PSD region: $g_{\text{rms,flat}} = \sqrt{\text{PSD}_{\text{flat}} \times (f_2 - f_1)}$
>
> Example: PSD = 0.04 g$^2$/Hz from 80–500 Hz:
> $g_{\text{rms,flat}} = \sqrt{0.04 \times 420} = \sqrt{16.8} = 4.10$ g$_{\text{rms}}$
>
> The ramp sections and the flat section are summed in quadrature:
> $$g_{\text{rms,total}} = \sqrt{g_{\text{rms,ramp1}}^2 + g_{\text{rms,flat}}^2 + g_{\text{rms,ramp2}}^2}$$
> A sloped segment is a straight line in log–log axes, $\text{PSD}(f) = P_1 (f/f_1)^n$ with $n = (\text{dB/oct})/3.01$, and integrates exactly to $\frac{P_1 f_1}{n+1}\left[(f_2/f_1)^{n+1} - 1\right]$ (or $P_1 f_1 \ln(f_2/f_1)$ when $n = -1$). The rising ramp ($n = +1$) gives $\frac{0.01 \times 20}{2}(4^2 - 1) = 1.50$ g$^2$, i.e. 1.22 g$_{\text{rms}}$, and the falling ramp ($n = -1$) gives $0.04 \times 500 \times \ln 4 = 27.73$ g$^2$, i.e. 5.27 g$_{\text{rms}}$, so $g_{\text{rms,total}} = \sqrt{1.50 + 16.80 + 27.73} = \sqrt{46.03} = 6.78 \approx 6.8$ g$_{\text{rms}}$. At proto-flight (+3 dB, PSD × 2), $\sqrt{92.06} = 9.59 \approx 9.6$ g$_{\text{rms}}$.

### 14.3.4 Thermal vacuum test profile

| Parameter | Proto-flight level | Notes |
|-----------|-------------------|-------|
| Hot-case temperature | Predicted max + 10 °C | e.g. if the thermal model predicts +55 °C → test to +65 °C |
| Cold-case temperature | Predicted min − 10 °C | e.g. if the thermal model predicts −20 °C → test to −30 °C |
| Number of cycles | 4 (proto-flight) | Start and end at hot; functional test at each extreme |
| Vacuum level | < 10$^{-5}$ mbar | Space-representative vacuum |
| Dwell time at extreme | ≥ 1 hour | Allow thermal stabilisation (< 1 °C/h gradient) |
| Temperature transition rate | 1–3 °C/min | Limited by chamber capability |
| Functional test | Full performance at hot and cold extremes | Subset functional at intermediate transitions |

The ± 10 °C proto-flight band is the GSFC-STD-7000B §2.6 proto-flight margin (§14.2.2); the predicted extremes come from the hot and cold cases of the thermal analysis.

> **TVAC cycle duration estimate:**
>
> $$t_{\text{cycle}} = 2\,\frac{\Delta T}{\dot{T}_{\text{ramp}}} + 2\, t_{\text{dwell}} + 2\, t_{\text{functional}}$$
>
> Example: $\Delta T = 95$ °C (from −30 to +65 °C), ramp = 2 °C/min, dwell = 1 h, functional test = 2 h:
> $t_{\text{cycle}} = 2 \times (95/2) + 2 \times 60 + 2 \times 120 = 95 + 120 + 240 = 455$ min $\approx 7.6$ h
>
> Total TVAC campaign (4 cycles + set-up): $\approx 4 \times 7.6 + 8 = 38.4$ h $\approx$ 5 working days of continuous chamber operation.

### 14.3.5 EMC testing

*[Source: MIL-STD-461G; ECSS-E-ST-20-07C]*

| Test | Standard | Purpose |
|------|----------|---------|
| CE102 conducted emissions | MIL-STD-461G | Measure spurious conducted emissions on power lines |
| RE102 radiated emissions | MIL-STD-461G | Measure unintentional RF radiation from the satellite |
| CS101 conducted susceptibility | MIL-STD-461G | Verify immunity to power-line transients |
| RS103 radiated susceptibility | MIL-STD-461G | Verify immunity to external RF fields |

*Note: EMC testing is not always required for CubeSats. It depends on the launch provider and co-manifested payloads. Check the rideshare interface control document. The transmitter-to-payload coupling identified as an R-type interface concern in Chapter 8 §8.3.4 is the internal EMC case that a self-compatibility test addresses.*

---

## 14.4 Compliance verification matrix construction

The verification matrix (also called the compliance matrix or verification cross-reference matrix, VCRM) is the central document linking every requirement to its verification evidence. It extends the requirements verification matrix of Chapter 5 §5.5 with the phase, level, responsibility, facility and status columns needed to plan and track the campaign.

*[Source: ECSS-E-ST-10-02C Rev. 1 §6; DRD in Annex A]*

### 14.4.1 Matrix structure

| Req ID | Requirement text | Method | Phase | Level | Responsible | Facility | Status | Evidence |
|--------|-----------------|--------|-------|-------|-------------|----------|--------|----------|
| SYS-001 | $M_{\text{dry}} \leq 4.0$ kg | I | D | System | Structures | Clean room | Planned | Mass measurement report |
| SYS-002 | Survive 9.6 g$_{\text{rms}}$ random vibration (proto-flight) | T | C/D | System | Structures | Vibration laboratory | Planned | Vibration test report |
| SYS-003 | GSD ≤ 10 m at 500 km | A | B | System | Payload | N/A | Planned | Optical analysis report |
| SYS-004 | Link margin ≥ 3 dB | A | B | System | Comms | N/A | Planned | Link-budget analysis |
| SYS-005 | Antenna deploys < 30 min | D | D | System | Mechanisms | Clean room | Planned | Deployment demonstration |
| SYS-006 | Two independent deployment switches inhibit all power | R | B | System | EPS | N/A | Planned | Review of stack schematic |

### 14.4.2 ATIR(D) assignment decision logic

```
Is it a physical property (mass, dimensions, surface finish)?
  → Inspection (I), Phase D, system level

Can it only be proven by quantitative measurement under controlled conditions?
  → Test (T), Phase C/D, unit or system level

Can it be demonstrated by operating the system (functional, not precision)?
  → Demonstration (D), Phase D, system level
    (ECSS records this as a test without quantitative measurement)

Can it be shown with acceptable confidence through modelling or similarity?
  → Analysis (A), Phase B/C, system level

Is it a document, a process, a plan, or a design feature evident from the drawings?
  → Review of design (R), Phase B
```

### 14.4.3 Multiple methods

Some requirements need **both** analysis (early confidence) and test (final proof):

| Requirement | Analysis (Phase B) | Test (Phase C/D) |
|------------|-------------------|------------------|
| Structural survival under launch loads | FEA with positive MoS | Vibration test — no damage |
| Pointing accuracy ≤ 0.1° | Error-budget analysis (Chapter 10 §10.4) | On-orbit calibration measurement |
| Thermal within limits (−20 to +55 °C) | Thermal model simulation | TVAC functional test at extremes |
| RF link margin ≥ 3 dB | Link-budget calculation | RF compatibility test (if feasible) |

In the matrix, list the **primary** method and note "confirmed by [secondary method] in Phase [X]".

### 14.4.4 Waiver process

When a requirement cannot be verified by the prescribed method, or cannot be met, a **waiver** is needed:

| Waiver type | When used | Approval level |
|-------------|-----------|---------------|
| **Non-compliance** | Requirement cannot be met; accept the deviation | Project manager + customer |
| **Method deviation** | A different verification method is used (e.g. analysis instead of test) | Systems engineer + quality |
| **Tailoring** | Standard requirement not applicable to this mission | Systems engineer |

**Waiver documentation must include:** requirement ID, deviation description, technical justification, risk assessment (in the terms of Chapter 15) and compensating measures.

---

## 14.5 Returning to UniSat-1: a verification matrix

The requirements below are drawn from the UniSat-1 examples of Chapters 5, 9, 11 and 12. Each is assigned a method by the logic of §14.4.2.

| Req ID | Requirement | Method | Phase | Level | Evidence |
|--------|-------------|--------|-------|-------|----------|
| US-SYS-001 | Wet mass ≤ 1.33 kg (deployer limit) | I | D | System | Calibrated-scale measurement |
| US-SYS-002 | Conform to CDS Rev 14 1U envelope and rail profile | I | D | System | Calliper and profile-gauge report; deployer fit check |
| US-STR-001 | First structural mode > 90 Hz | A, confirmed by T | B / C | System | Modal analysis; low-level sine survey before random vibration |
| US-STR-002 | Survive 9.6 g$_{\text{rms}}$ (proto-flight) random vibration without degradation | T | C/D | System | Pre/post functional comparison, vibration test report |
| US-EPS-001 | Two deployment switches and an RBF pin inhibit all power | R, confirmed by D | B / D | System | Schematic review; inhibit demonstration with switches depressed |
| US-COM-001 | Downlink margin ≥ 3 dB at 10° elevation | A | B | System | Link budget (Chapter 11 §11.8.2) |
| US-COM-002 | Antenna deploys within 30 min of separation-switch release | D | D | System | Timed deployment demonstration (3 repetitions) |
| US-THM-001 | Battery temperature within 0–45 °C charging limits in all modes | A, confirmed by T | B / C | System | Thermal analysis (Chapter 9 §9.5); TVAC with battery temperature monitored |
| US-PL-001 | Magnetometer noise < 10 nT/√Hz at 1 Hz | T | C | Unit | Laboratory measurement in a shielded chamber |
| US-OPS-001 | Autonomous safe-mode entry on bus under-voltage | D | D | System | Fault-injection demonstration with the flight software |

Two features of this table are worth noting. First, the only requirements that need the environmental facilities of §14.3 are US-STR-002 and US-THM-001 — a single vibration and TVAC campaign of about two weeks verifies both, which is why those tests dominate the schedule and cost of a small mission's verification. Second, the two "make" items of Chapter 13 §13.6 (the OBC and the magnetometer board) carry the unit-level test and the fault-injection demonstration; the TRL risk identified there is retired by evidence here.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| V versus V | Verification = meets requirements (ATIR(D)); validation = meets stakeholder needs |
| ATIR(D) | Analysis (models and similarity), test (quantitative), inspection (physical), review of design (documents and drawings), demonstration (functional) |
| Proto-flight | CubeSats: a single flight unit tested to qualification levels for acceptance duration |
| Sine vibration | 5–100 Hz, 1.25 g, 4 oct/min for proto-flight (2 oct/min for qualification), 3 axes, no displacement band (crossover $f_c = \sqrt{a/d}/2\pi \approx 5$ Hz at 12.5 mm); quasi-static launch loads |
| Random vibration | 20–2000 Hz, GEVS workmanship 6.8 g$_{\text{rms}}$ ($g_{\text{rms}} = \sqrt{\int \text{PSD}\, df}$); proto-flight +3 dB, about 9.6 g$_{\text{rms}}$, 1 min per axis |
| TVAC | Proto-flight at predicted ± 10 °C (GSFC-STD-7000B / ECSS-E-ST-10-03C), 4 cycles, functional at each extreme; ~7.6 h per cycle |
| Compliance matrix | Per requirement: method + phase + level + responsible + facility + status + evidence |
| Waivers | Document the deviation, justification, risk and compensating measures |

---

## Problems

1. **Verification or validation?** For each of the following, state whether it is a verification or a validation activity and justify the choice in one sentence: (a) measuring the dry mass of the flight unit; (b) an agricultural user assessing a sample image; (c) running the thermal model for the hot case; (d) a 30-day operations rehearsal with simulated anomalies (Chapter 19); (e) confirming that the GSD of on-orbit imagery is 9.2 m.

2. **Method assignment.** Assign a primary ATIR(D) method, phase and level to each of these EOSat-3U requirements, using the logic of §14.4.2, and state the evidence produced: (a) the spacecraft shall provide ≥ 3 dB link margin at 10° elevation; (b) the solar arrays shall deploy within 10 minutes of separation; (c) the star-tracker boresight shall be aligned to the payload within 1 arcmin; (d) the flight software shall be developed under ECSS-E-ST-40C; (e) the spacecraft shall deorbit within 5 years of end of mission; (f) all external surfaces shall be anodised or coated with a non-outgassing finish.

3. **Both analysis and test.** Choose three EOSat-3U requirements that need both analysis in Phase B and test in Phase C/D, and for each explain what the analysis can and cannot establish, what the test adds, and what happens to the matrix if the test is descoped for cost.

4. **Sine profile.** A launch provider specifies 10 mm (0–peak) displacement from 4 Hz and 2.0 g (0–peak) up to 100 Hz. Compute the crossover frequency at which the two limits coincide, and the acceleration the test article would see at 4 Hz if the displacement limit were applied there. Explain why the controller must switch from displacement to acceleration control.

5. **Random vibration g$_{\text{rms}}$.** A deployer specifies a random profile of 0.02 g$^2$/Hz flat from 20 to 1000 Hz, falling at −6 dB/octave to 2000 Hz. Compute the flat-section g$_{\text{rms}}$ and, treating the falling ramp as a straight line in linear PSD, estimate its contribution and the overall g$_{\text{rms}}$. Is the level above or below the 6.8 g$_{\text{rms}}$ workmanship profile of §14.3.3?

6. **TVAC planning.** The EOSat-3U thermal analysis (Chapter 9 §9.4) predicts −15 °C to +50 °C at the battery. State the proto-flight test temperatures, then compute the cycle duration for a 1.5 °C/min chamber, 1 h dwells and 90-minute functional tests, and the total campaign duration for six cycles plus 8 h of set-up. If the chamber costs 2 kEUR per day (indicative), what does the campaign cost, and how does this compare with the UniSat-1 integration-and-test budget of Chapter 13 §13.6?

7. **Test sequence.** Explain why the random-vibration test precedes TVAC in §14.3.1 and why a functional test sits between them. What would be lost if the order were reversed? Name one defect that vibration reveals but TVAC does not, and one that TVAC reveals but vibration does not.

8. **Proto-flight versus qualification model.** A mission is offered two options: build a qualification model and test it to full qualification levels and durations (adding 60 kEUR and 4 months), or proto-flight test the single flight unit. List the risks each option carries, and decide for (a) UniSat-1 and (b) a 12U commercial mission with a 2 MEUR payload. Justify each decision in terms of the consequence scale of Chapter 15.

9. **Waiver.** The EOSat-3U EMC test (RE102) cannot be performed because no chamber is available before shipment. Write the waiver: requirement ID, deviation, technical justification based on Chapter 8 §8.3.4 and Chapter 11, a risk assessment on the 5×5 matrix of Chapter 15, and two compensating measures.

10. **Compliance matrix audit.** A verification matrix for a 6U CubeSat has 142 requirements: 61 verified by analysis, 48 by test, 20 by inspection, 9 by review of design and 4 by demonstration. Twelve requirements have no method, and six "test" entries have no facility named. List the questions a reviewer should ask at CDR (Chapter 16), and estimate how many requirements can be closed before the environmental campaign starts.

---

## References

1. ECSS, *ECSS-E-ST-10-02C Rev. 1: Verification*, 2018. https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification/
2. ECSS, *ECSS-E-ST-10-03C: Testing*, 2012. https://ecss.nl/standard/ecss-e-st-10-03c-testing/
3. ECSS, *ECSS-E-ST-10-06C: Technical Requirements Specification*, 2009. https://ecss.nl
4. ECSS, *ECSS-E-ST-32-10C Rev. 2: Structural Factors of Safety for Spaceflight Hardware*, 2019. https://ecss.nl
5. ECSS, *ECSS-E-ST-20-07C Rev. 2: Electromagnetic Compatibility*, 2022. https://ecss.nl
6. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §5.3–5.4. https://www.nasa.gov/reference/systems-engineering-handbook/
7. US Department of Defense, *MIL-STD-1540E: Test Requirements for Launch, Upper-Stage and Space Vehicles*. https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=36197
8. US Department of Defense, *MIL-STD-461G: Requirements for the Control of Electromagnetic Interference Characteristics of Subsystems and Equipment*. https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=35789
9. NASA, *General Environmental Verification Standard (GEVS)*, GSFC-STD-7000B, 2021.
10. Cal Poly, *CubeSat Design Specification Rev 14.1*, 2022. https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf
11. SpaceX, *Rideshare Payload User's Guide*, 2024 (representative launch-vehicle interface specification). https://www.spacex.com/rideshare/
