# Chapter 16 — Cost Estimation and Design Reviews

> **Recommended background.** NASA Cost Estimating Handbook v4.0 (Appendix C, cost estimating relationships); SMAD4 Chapter 20 (Cost); NPR 7120.5F (work breakdown structures); ECSS-M-ST-60C (Cost and schedule management); ECSS-M-ST-10C Rev. 1 §6 and NPR 7123.1D Appendix G (reviews). This chapter builds on the bill of materials and non-recurring engineering cost of Chapter 13, the verification matrix of Chapter 14 and the risk register of Chapter 15; the review gates themselves are defined in Chapter 1 Table 1.3.

## Learning objectives

By the end of this chapter, you will be able to:

1. Estimate mission cost using parametric (CER), analogy and bottom-up methods, and state the accuracy of each
2. Structure a work breakdown structure (WBS) for a CubeSat project and distribute cost across lifecycle phases
3. Apply learning-curve effects to constellation cost estimation
4. Express cost risk as a distribution and quote P50/P70/P80 confidence levels
5. Prepare for a design review (SRR/PDR/CDR) against explicit gate criteria
6. Present design evidence clearly, respond to review-board questions, and sit on a review board yourself

Vendor products named in this chapter are representative examples, not endorsements; prices are indicative (2026) unless a fiscal year is stated.

---

## 16.1 Cost estimation methodologies

*[Source: NASA CEH v4.0 Appendix C; SMAD4 Chapter 20; Aerospace Corp SSCM]*
*[URL: https://www.nasa.gov/offices/ocfo/references-and-tools/ (NASA CEH)]*

Cost is an engineering budget like mass or power: it has a current best estimate, a margin and an allocation, and it must close. The difference is that cost cannot be measured on a bench — it is *estimated*, and the quality of the estimate depends on how much of the design exists when the estimate is made.

### 16.1.1 Three primary methods

| Method | Description | Accuracy (1σ) | When to use | Data required |
|--------|-------------|---------------|-------------|---------------|
| **Parametric** | Cost estimating relationships (CERs) fitted to a historical database | ± 30–50 % | Phase 0/A (few details known) | Mass, power, mission type |
| **Analogy** | Compare with a similar past mission, adjust for differences | ± 20–40 % | Phase A/B (reference mission available) | Detailed knowledge of the reference |
| **Bottom-up** | Sum vendor quotes + labour estimates + facilities | ± 10–20 % | Phase B/C (detailed design) | BOM, vendor quotes, labour rates |

The three methods are not alternatives but a sequence: the estimate narrows as the lifecycle proceeds, from a parametric band at mission-concept review to a bottom-up figure at CDR. Figure 16.1 shows this funnel — the uncertainty band narrows from ± 50 % to ± 10 % as the estimating method changes with design maturity.

![Cost-estimate accuracy band narrowing from parametric to bottom-up](../assets/figures/fig_cost_funnel.png)

**Figure 16.1** — Cost-estimate accuracy versus lifecycle phase. The ± 1σ band around the point estimate narrows from about ± 50 % at mission concept review to about ± 10 % at CDR as the estimating method moves from parametric (Phase 0/A) through analogy (A/B) to bottom-up (B/C/D); the review gates of Chapter 1 Table 1.3 are marked on the phase axis.

### 16.1.2 Parametric cost estimating relationships (CERs)

CERs express cost as a function of technical parameters, derived from regression analysis of historical data. The general form is

$$C = a \, M^{\,b} \, f_{\text{complexity}}$$

where $a$ is the regression coefficient, $M$ is the driving parameter (usually dry mass in kg, sometimes power in W or data rate), $b$ is the exponent (typically 0.5–1.0, so that cost grows more slowly than mass) and $f_{\text{complexity}}$ is an adjustment for mission difficulty. A CER is only as good as the database behind it: it must not be used outside the mass and technology range of the missions it was fitted to.

### 16.1.3 USCM (Unmanned Space Vehicle Cost Model) CERs

*[Source: SMAD4 Table 20-8; US Air Force USCM database]*

| Subsystem | CER (FY2010 \$K) | Parameter | Typical $b$ |
|-----------|-----------------|-----------|-------------|
| Structure | $157\,M_{\text{struct}}^{0.83}$ | Dry mass (kg) | 0.83 |
| Thermal | $394\,M_{\text{therm}}^{0.635}$ | Dry mass (kg) | 0.635 |
| EPS | $62.7\,M_{\text{EPS}}^{1.00}$ | Dry mass (kg) | 1.00 |
| TT&C | $545\,M_{\text{TTC}}^{0.761}$ | Dry mass (kg) | 0.761 |
| AOCS | $464\,M_{\text{AOCS}}^{0.867}$ | Dry mass (kg) | 0.867 |
| Propulsion | $17.8\,M_{\text{prop}}^{0.75}$ | Dry mass (kg) | 0.75 |
| Integration and test | $10.4\,M_{\text{dry}}^{0.907}$ | Total dry mass (kg) | 0.907 |
| Programme management | 12.3 % of hardware cost | — | — |
| Systems engineering | 14.2 % of hardware cost | — | — |

### 16.1.4 SSCM (Small Satellite Cost Model)

The Aerospace Corporation SSCM was specifically calibrated for satellites below 500 kg. It provides more accurate estimates for CubeSats than USCM.

*[Source: Aerospace Corp, "Small Satellite Cost Model (SSCM)", available through Aerospace TOR]*

**Key SSCM adjustments for CubeSats:**
- COTS hardware costs are catalogue prices, not mass-based CERs
- Labour costs dominate for university and small-team projects
- NRE depends heavily on mission uniqueness (Chapter 13 §13.1.3 gives the NRE equation)
- Standard CERs (designed for > 100 kg) over-predict by 2–6× for the nano/micro class

### 16.1.5 CubeSat-calibrated pricing: COTS flat prices versus CERs

A practical hybrid approach uses COTS flat pricing for the nano/micro class and CERs for larger spacecraft. The comparison below shows why: for CubeSat-mass subsystems the CER is evaluated far below the mass range it was fitted to, and the fit breaks down.

| Subsystem | CubeSat COTS cost (kEUR) | USCM CER (kEUR, at CubeSat mass) | Ratio |
|-----------|--------------------------|-----------------------------------|-------|
| EPS | 15 | 60 | CER 4× higher |
| AOCS (fine) | 40 | 66 | CER 1.6× higher |
| TT&C (S-band) | 20 | 25 | Similar |
| OBC | 10 | 12 | Similar |
| Structure | 8 | 3 | CER lower (minimum-order effect) |
| Payload | 50 (variable) | 300 | CER 6× higher for COTS payloads |

*This confirms that for CubeSats, COTS pricing is more reliable than parametric CERs for hardware cost.*

### 16.1.6 Worked example: parametric versus bottom-up for the 3U EO CubeSat

*EOSat-3U, 3U Earth-observation mission (representative vendors, indicative 2026 prices):*

| WBS element | Parametric (kEUR) | Bottom-up (kEUR) | Notes |
|-------------|-------------------|-------------------|-------|
| Structure | 8 | 8.5 | ISIS 3U structure |
| EPS | 18 | 16.2 | GomSpace P31u + solar array |
| OBC | 12 | 10.0 | NanoAvionics SatBus |
| AOCS | 45 | 42.0 | BCT XACT-15 |
| TT&C | 22 | 20.5 | Endurosat S-band |
| Thermal | 5 | 3.0 | Passive only |
| Payload | 65 | 58.0 | Simera Sense xScape |
| Harness | 3 | 2.5 | Custom cables |
| **Hardware subtotal** | **178** | **160.7** | |
| I&T (12 %) | 21 | 19.3 | |
| Software (8 %) | 14 | 12.9 | |
| PM/SE/MA (13 %) | 23 | 20.9 | |
| Launch | 200 | 195.0 | Rideshare |
| Ground (5 %) | 9 | 8.0 | Volunteer network + dedicated station |
| Operations (3 yr) | 45 | 40.0 | 0.5 FTE |
| **TOTAL** | **490** | **456.8** | |

*The parametric estimate is ~7 % higher than bottom-up. This is expected: parametric includes inherent uncertainty and contingency.* The ~490 kEUR total is the figure carried in Chapter 13 §13.6 for the 1U-versus-3U comparison.

---

## 16.2 Cost breakdown structure (WBS)

The work breakdown structure (WBS) is the hierarchical decomposition of all work required to complete the mission. It is the foundation for cost estimation, scheduling and management: every euro and every hour is booked against exactly one WBS element, so nothing is counted twice and nothing is forgotten.

*[Source: NPR 7120.5F Appendix G; ECSS-M-ST-60C; NASA CEH v4.0 Appendix B]*

### 16.2.1 Standard CubeSat WBS

```
WBS Level 1: Mission Total
  1.0  Programme Management                5 %   (oversight, reviews, reporting)
  2.0  Systems Engineering                 5 %   (budgets, interfaces, trade studies)
  3.0  Mission Assurance                   3 %   (quality, reliability, parts)
  4.0  Payload                            20 %   (instrument + calibration)
    4.1  Payload instrument hardware
    4.2  Payload software
    4.3  Payload calibration and characterisation
  5.0  Spacecraft Bus Hardware            30 %   (all subsystems)
    5.1  Structure and mechanisms
    5.2  EPS (solar array + battery + board)
    5.3  AOCS (sensors + actuators)
    5.4  TT&C (transponder + antenna)
    5.5  OBC and data handling
    5.6  Thermal control
    5.7  Propulsion (if applicable)
    5.8  Harness and cabling
  6.0  Integration and Test               12 %   (assembly, environmental testing)
    6.1  Assembly and integration
    6.2  Environmental test campaign
    6.3  Test facilities rental
  7.0  Software (Flight + Ground)          8 %   (FSW, GSW, mission planning)
    7.1  Flight software
    7.2  Ground segment software
    7.3  Mission planning tools
  8.0  Launch Services                    10 %   (vehicle, deployer, integration)
  9.0  Ground Segment                      5 %   (antennas, MCS, networks)
  10.0 Operations (mission lifetime)       5 %   (staff, consumables, maintenance)
```

![Standard CubeSat WBS tree](../assets/figures/fig_wbs_tree.png)

**Figure 16.2** — The standard CubeSat work breakdown structure as a tree: Mission Total branches to the ten Level-1 elements, each with its typical share of total cost, and 5.0 Spacecraft Bus Hardware is expanded to its eight Level-2 elements. The colours group the elements into management (1–3), space segment (4–6), software (7), launch (8) and ground and operations (9–10).

The percentages (Figure 16.2) are typical of a university or small-company CubeSat and are a starting allocation, not a law: a mission with a custom payload will push 4.0 towards 35 %, and a mission bought as a turnkey bus will collapse 5.0 and 6.0 into a single procurement line.

### 16.2.2 Cost by phase

The distribution of cost across lifecycle phases matters for budgeting and cash flow:

| Phase | % of total | Activities | Peak staffing |
|-------|-----------|-----------|---------------|
| 0/A (Concept) | 5–10 % | Studies, trade-offs, requirements | Low |
| B (Preliminary design) | 15–20 % | PDR, detailed analysis, long-lead procurement | Growing |
| C (Detailed design) | 30–40 % | CDR, manufacturing, software development | Peak |
| D (Integration and test) | 20–25 % | Assembly, environmental testing, commissioning | High |
| E (Operations) | 10–20 % | Routine operations, anomaly management | Low, steady |
| F (Disposal) | 1–3 % | Decommissioning, de-orbit | Minimal |

---

## 16.3 Learning curve for constellations

*[Source: SMAD4 §20.3; Wright's learning-curve theory (1936)]*

When building multiple identical units, the cost per unit decreases because of manufacturing efficiency, reduced test time, bulk purchasing and labour learning. Chapter 4 §4.6.4 used the cumulative form of this effect to size a constellation budget; here we develop the unit form it rests on.

### 16.3.1 Wright's learning curve

The cost (or labour time) of the $n$-th unit is

$$T_n = T_1 \, n^{\log_2 L}$$

where $T_1$ is the first-unit cost, $L$ is the *learning rate* (0.90 for a "90 % curve") and the exponent $b = \log_2 L = \ln L / \ln 2$ is negative. Writing cost explicitly, $C_n = C_1\, n^{b}$:

| Learning rate $L$ | $b = \log_2 L$ | Cost of 10th unit (% of 1st) |
|--------------|-----|-----|
| 95 % | −0.074 | 84 % |
| 90 % | −0.152 | 70 % |
| 85 % | −0.234 | 58 % |

The total cost of $N$ units is the cumulative sum, which is the form used in Chapter 4:

$$C_{\text{total}} = C_1 \sum_{i=1}^{N} i^{\log_2 L}
\;\approx\; C_1\,\frac{N^{\,1+b}}{1+b} \quad\text{(continuous approximation)}$$

The continuous approximation overestimates the sum by a few per cent for small $N$; use the exact sum when $N < 10$.

### 16.3.2 Simplified rule of thumb

> At a **90 % learning rate**, every time you **double** the number of units, the unit cost drops by **10 %**:
>
> Unit 1: EUR 800 k · Unit 2: EUR 720 k · Unit 4: EUR 648 k · Unit 8: EUR 583 k · Unit 16: EUR 525 k

### 16.3.3 Worked example: 20-satellite constellation

*First-unit cost (bus + payload + I&T): EUR 800 k. Learning rate: 90 % ($b = -0.152$). Totals use the exact cumulative sum.*

| Units $N$ | $\sum_{i=1}^{N} i^{b}$ | Average unit cost | Total hardware | Calculation |
|-------|---|--------------|----------------|------|
| 1 | 1.000 | EUR 800 k | EUR 800 k | First unit |
| 5 | 4.34 | EUR 694 k | EUR 3 470 k | $800 \times 4.34$ |
| 10 | 8.00 | EUR 640 k | EUR 6 400 k | $800 \times 8.00$ |
| 20 | 14.61 | EUR 584 k | EUR 11 690 k | $800 \times 14.61$ (continuous approx. gives 11 960 k) |

Total constellation estimate:
- 20 satellites, hardware: EUR 11.7 M
- 2 spare units (built as units 21–22 at ≈ 0.63 × 800 k each): EUR 1.0 M
- Launch (20 satellites × EUR 200 k rideshare): EUR 4.0 M
- Ground segment: EUR 1.0 M
- Operations (3 years): EUR 0.9 M
- PM/SE/MA (10 % of the above): EUR 1.9 M
- **Total: ≈ EUR 20.5 M**

Without the learning curve the 22 units alone would cost EUR 17.6 M; the curve saves about EUR 4.9 M, which is the business case for building a constellation rather than a series of one-offs.

---

## 16.4 Cost risk and confidence levels

Point estimates are misleading. Every cost estimate has uncertainty, and the standard practice is to express cost as a probability distribution rather than a single number.

*[Source: NASA CEH v4.0 §2.3; JPL parametric estimation practice]*

### 16.4.1 Uncertainty by cost element

| Cost element | Distribution | Uncertainty (1σ) | Rationale |
|-------------|-------------|----------------------|-----------|
| COTS hardware | Normal | ± 10 % | Known pricing from vendor quotes |
| Custom hardware | Lognormal | ± 30 % | Development uncertainty skews high |
| Software | Triangular | ± 40 % | Hardest to estimate; frequent overruns |
| Launch | Normal | ± 15 % | Published pricing; contract negotiation |
| Operations | Uniform | ± 25 % | Staffing-level uncertainty |
| I&T | Lognormal | ± 25 % | Test anomalies cause schedule and cost growth |

Each WBS element is assigned a distribution; a Monte Carlo simulation draws from all of them and sums, producing a distribution of total cost. Its cumulative form is the **S-curve** of Figure 16.3 — the probability that the mission costs no more than a given amount — from which the confidence levels are read. Because lognormal and triangular elements are right-skewed, the point (current best) estimate falls to the *left* of P50: a single-number estimate is more likely to be exceeded than met.

![Cost S-curve with P50, P70 and P80 marked](../assets/figures/fig_cost_scurve.png)

**Figure 16.3** — Cost S-curve and confidence levels for the EOSat-3U bottom-up estimate of §16.1.6 (456.8 kEUR), from a Monte Carlo of 200 000 draws in which each cost element follows the distribution of the table above and the elements are independent. The result gives P50 ≈ 459 kEUR, P70 ≈ 479 kEUR and P80 ≈ 491 kEUR; the point estimate sits at about P47, slightly to the left of P50 because the custom-payload and integration elements are right-skewed, and the P50-to-P80 reserve is about 31 kEUR (7 %).

For this mostly-COTS mission, whose largest element is a fixed-price launch, the per-element table gives P80 ≈ 1.07 × P50 — well below the 1.3 rule of thumb in §16.4.2. The difference is deliberate: the rule of thumb also covers the correlated, programme-level growth that per-element distributions do not capture (requirement changes, schedule slip that drives every labour line, a payload that turns out to need a second iteration), which is why the NASA Cost Estimating Handbook requires inter-element correlation to be modelled in a joint cost-and-schedule confidence analysis, and why the rule of thumb is still the better planning figure at Phase A.

### 16.4.2 Confidence levels

| Percentile | Meaning | Use |
|-----------|---------|-----|
| **P50** | 50 % probability of being at or below this cost | Project baseline; "expected" cost |
| **P70** | 70 % probability | NASA standard commitment level (NPR 7120.5F) |
| **P80** | 80 % probability | Conservative planning; typical for proposals |

> **Rule of thumb for CubeSat missions:**
>
> $$P_{70} \approx 1.2\,P_{50}, \qquad P_{80} \approx 1.3\,P_{50}$$
>
> Example: if $P_{50} =$ EUR 500 k, then $P_{80} \approx$ EUR 650 k.
>
> *This approximation assumes moderate complexity and well-understood COTS hardware. For missions with custom payloads or new technology, use $P_{80} \approx 1.5\,P_{50}$.*

The difference between P50 and the committed level is the **cost reserve**. It belongs to the project manager, not to the subsystem leads, and is released against the risk register of Chapter 15 — a risk that materialises draws on the reserve; a risk that is retired returns its share.

### 16.4.3 Returning to UniSat-1: cost structure

**Simple WBS, mostly COTS.** UniSat-1's cost structure is fundamentally different from that of larger missions because (a) nearly all hardware is COTS, so NRE is near zero, and (b) the team is small and university-based, so labour costs are low. Chapter 13 §13.6 gave the BOM-based cost summary (≈ 85 kEUR, without operations and with a single management line; the WBS estimate below adds both and comes to ≈ 91 kEUR); here the same mission is estimated by both methods against the WBS of §16.2.1 and carried to a P80 figure.

> **UniSat-1 WBS cost estimate (parametric versus bottom-up; indicative 2026):**
>
> | WBS element | Parametric (kEUR) | Bottom-up (kEUR) | Notes |
> |-------------|-------------------|-------------------|-------|
> | 1.0 Programme management | 4 | 5 | Faculty oversight, 0.1 FTE × 12 months |
> | 2.0 Systems engineering | 3 | 3 | Team lead |
> | 3.0 Mission assurance | 1 | 1 | Minimal QA for a university mission |
> | 4.0 Payload | 8 | 8 | MEMS sensor PCB + calibration |
> | 5.0 Bus hardware | 39 | 38 | BOM in Chapter 13 §13.6 |
> |   5.1 Structure | 4 | 4 | 1U frame |
> |   5.2 EPS + solar array | 20 | 19.5 | EPS board + body-mounted cells |
> |   5.3 AOCS (passive) | 1 | 1 | Magnet + hysteresis rods |
> |   5.4 Comms (UHF) | 11 | 10.5 | Transceiver + antenna |
> |   5.5 OBC | 3 | 3 | Custom Cortex-M board |
> | 6.0 I&T | 8 | 8 | University clean room + vibration facility |
> | 7.0 Software | 5 | 5 | FSW (RTOS) + GSW |
> | 8.0 Launch | 15 | 15 | 1U ISS deployment |
> | 9.0 Ground segment | 5 | 5 | Yagi antenna + volunteer network |
> | 10.0 Operations (6 months) | 3 | 3 | Student operators, 0.2 FTE |
> | **TOTAL (P50)** | **≈ 91** | **≈ 91** | |
> | **P80 (× 1.3)** | **≈ 118** | **≈ 118** | Conservative estimate |

**Key cost observations for 1U missions:**

1. **Hardware is cheap.** Total COTS hardware cost is ≈ 36–44 kEUR. This is less than a single star tracker for a 3U mission.
2. **NRE is minimal.** Only the OBC and payload require custom development. NRE is estimated at ≈ 8 kEUR (payload calibration + OBC board layout), compared with ≈ 50–150 kEUR for custom payloads on larger missions.
3. **Launch cost is proportionally large.** At 15 kEUR, the launch represents ≈ 18 % of total cost. For a 3U mission at ≈ 200 kEUR launch cost, launch is ≈ 40 % of total. The 1U launch cost is low in absolute terms but still a significant fraction.
4. **Labour dominates.** For a university team, the "free" student labour is the hidden cost. If students were costed at professional rates (≈ 50 EUR/h), the total labour cost would be ≈ 100–200 kEUR, far exceeding the hardware cost. This is typical of educational missions.
5. **No cost drivers from complexity.** There is no AOCS software development, no deployable-mechanism qualification, no propulsion integration, no thermal-vacuum testing of heaters — all of which add 10–50 kEUR each on a 3U mission.

**Learning-curve applicability.** If a university builds a series of 1U demonstrators (UniSat-1, UniSat-2, UniSat-3 …), a 90 % learning rate applies to the hardware and to the recurring labour (software, calibration, I&T, management ≈ 21 kEUR), while launch (15 kEUR) and ground segment (5 kEUR) are fixed:

| Unit | Hardware cost (kEUR) | Total cost (kEUR) |
|------|---------------------|-------------------|
| UniSat-1 | 44 | 85 |
| UniSat-2 | 40 | 79 |
| UniSat-4 | 36 | 73 |
| UniSat-8 | 32 | 67 |

The asymptotic floor is dominated by launch cost (15 kEUR) and irreducible ground-segment and operations costs (≈ 8 kEUR), giving a minimum mission cost of ≈ 40–50 kEUR for repeat builds.

---

## 16.5 Design reviews: gate criteria and presentation

Design reviews are formal decision gates at which the project demonstrates readiness to proceed to the next lifecycle phase. The sequence of gates — MCR, SDR, SRR, PDR, CDR, TRR, QR, FRR — and the key question each one answers are given in Chapter 1 Table 1.3 and are not repeated here. This section covers what a review *checks* and how to present at one.

*[Source: NPR 7123.1D Appendix G; ECSS-M-ST-10C Rev. 1 §6; NASA SEH Rev 2 §3.7]*
*[URL: https://www.nasa.gov/reference/systems-engineering-handbook/]*

### 16.5.1 Gate criteria for SRR (Phase A → B)

| # | Criterion | Priority | Evidence |
|---|-----------|----------|----------|
| 1 | All Level 0/1 requirements baselined | Must pass | Requirements document signed (Chapter 5) |
| 2 | ConOps defined (all mission phases) | Must pass | ConOps document (Chapter 4, Chapter 18) |
| 3 | Mission architecture trades completed | Must pass | Trade-study reports with rationale (Chapter 4 §4.6) |
| 4 | Feasibility confirmed (all budgets positive) | Must pass | Mass, power, link budgets with margin (Chapter 8) |
| 5 | Risk register established with mitigations | Must pass | Risk register with scores and plans (Chapter 15) |
| 6 | Preliminary V&V approach defined | Should pass | Verification matrix with ATIR(D) methods assigned (Chapter 14) |
| 7 | Schedule and cost estimate (P50/P80) | Must pass | Cost estimate with WBS (§16.2, §16.4) |
| 8 | Interface requirements identified | Should pass | N² matrix or ICD outline (Chapter 8 §8.3) |

### 16.5.2 Gate criteria for PDR (Phase B → C)

| # | Criterion | Priority | Evidence |
|---|-----------|----------|----------|
| 1 | All requirements allocated to subsystems | Must pass | Requirements allocation matrix (Chapter 6) |
| 2 | Preliminary design complete for all subsystems | Must pass | Design documents, block diagrams (Chapters 9–12) |
| 3 | All budgets close with ≥ 20 % margin | Must pass | Mass, power, link, data, pointing budgets (Chapter 8 Table 8.3 for the margin schedule) |
| 4 | Equipment selected (BOM) | Must pass | BOM with TRL, heritage, cost, lead time (Chapter 13) |
| 5 | All interfaces defined (N² matrix) | Must pass | Interface control documents (Chapter 8 §8.3) |
| 6 | Verification matrix complete with methods assigned | Must pass | Verification matrix (Chapter 14 §14.4) |
| 7 | Risk register updated; no critical risks unmitigated | Must pass | Risk register (Chapter 15) |
| 8 | Test plan outline approved | Should pass | Environmental test plan (Chapter 14 §14.3) |
| 9 | Software architecture defined | Should pass | Software design document |
| 10 | Cost estimate updated (bottom-up) | Must pass | Cost estimate with vendor quotes (§16.1.6) |

A criterion marked *must pass* that fails produces a NO GO or a GO WITH ACTIONS; a *should pass* that fails produces an action item with an owner and a date.

### 16.5.3 Presenting at a review

**Do:**
- Lead with the conclusion ("Mass budget closes with 22 % margin")
- Show evidence, not just assertions ("Link-budget analysis shows 4.2 dB margin at worst case")
- Acknowledge risks honestly ("Antenna deployment is our highest risk at L3 × C4 = 12")
- State assumptions before results
- Answer questions directly; say "I don't know — we will take an action" if needed

**Do not:**
- Read slides aloud
- Hide problems (review boards always find them)
- Present analysis without stating its assumptions
- Skip backup slides — have the detailed data ready for the question-and-answer period
- Spend the time on the mission description and rush the technical results

---

## 16.6 Conducting a review board

An independent board — people who did not do the design — evaluates the project against the gate criteria. The independence is the point: the board exists to find what the team can no longer see. Sitting on a board is as much a skill as presenting to one.

### 16.6.1 Review-board roles

| Role | Responsibility | Key question to ask |
|------|---------------|---------------------|
| **Chair** | Manages the review; ensures all criteria are covered | "Let's systematically check each gate criterion." |
| **Systems reviewer** | Evaluates overall architecture and budgets | "Do all budgets close? What is the minimum margin?" |
| **Technical reviewer** | Evaluates subsystem design decisions | "Why did you choose this component over the alternatives?" |
| **Risk reviewer** | Evaluates risk management and verification | "What is your highest risk? Is the mitigation adequate?" |
| **Operations reviewer** | Evaluates ConOps, ground segment, regulatory status | "What happens if you lose contact for 48 hours?" |

For a small board the Chair may also take one of the reviewer roles, but the Risk reviewer and the Technical reviewer should be different people: the first is looking for what could go wrong, the second for whether the design is right, and one person rarely does both well at once.

### 16.6.2 Reviewer question bank

Standard questions for the board to ask, each of which maps to a chapter of this book:

- "Why is space the right answer? What alternatives were considered?" (Chapter 4)
- "What is your mass margin? What drives it? What if the payload is 20 % heavier than estimated?" (Chapter 8)
- "Walk me through your link budget at worst case. What is the minimum margin?" (Chapter 11)
- "What are your top three risks? What is the residual risk after mitigation?" (Chapter 15)
- "Show me your data budget. Does it close with a single ground station?" (Chapter 11 §11.9, Chapter 17)
- "What happens during a safe-mode entry in eclipse? Does the thermal budget survive?" (Chapters 9, 18)
- "Which component has the lowest TRL? What is your qualification plan?" (Chapters 13, 14)
- "Have you started spectrum licensing? What is on the critical path?" (Chapter 2)
- "What is your single-point-failure list? Which ones have you accepted?" (Chapter 15 §15.4.4)
- "If you had six more months and 20 % more budget, what would you change?"

### 16.6.3 Outcome

The board closes with one of three recommendations — **GO**, **NO GO**, or **GO WITH ACTIONS** — announced by the Chair, together with a list of action items, each with a responsible person and a deadline. Actions are tracked to closure before the next gate; an action that is still open at the next review is itself a finding.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Cost methods | Parametric (early, CERs), analogy (reference mission), bottom-up (vendor quotes); accuracy narrows from ± 50 % to ± 10 % through the lifecycle |
| CubeSat costs | COTS pricing is often lower than CER predictions; use a hybrid approach |
| WBS | Standard ten-element structure: PM, SE, MA, payload, bus, I&T, software, launch, ground, operations |
| CERs | $C = a\,M^{b}\,f_{\text{complexity}}$; USCM/SSCM databases; CubeSats need calibrated CERs |
| Learning curve | $T_n = T_1\,n^{\log_2 L}$; at a 90 % rate each doubling of quantity reduces unit cost by 10 % |
| Cost risk | P50 (baseline), P70 (NASA commitment), P80 (conservative); $P_{80} \approx 1.3\,P_{50}$; the difference is the reserve |
| Reviews | Gates per Chapter 1 Table 1.3; SRR and PDR criteria are explicit "must/should pass" lists with named evidence |
| Presentation | Lead with conclusions, show evidence, acknowledge risks, answer directly |
| Review board | Chair + systems, technical, risk and operations reviewers; GO / NO GO / GO WITH ACTIONS with tracked actions |

---

## Problems

1. **Parametric estimate.** A 6U CubeSat has a structure mass of 1.2 kg, an EPS of 1.5 kg, a TT&C subsystem of 0.4 kg and an AOCS of 1.1 kg. Evaluate the USCM CERs of §16.1.3 for each subsystem (FY2010 $K), add programme management and systems engineering, and compare the result with a COTS bottom-up estimate built from the catalogue prices of §16.1.5. By what factor does the CER over-predict, and which subsystem is responsible for most of the difference?

2. **WBS allocation.** A 3U Earth-observation CubeSat has a cost ceiling of 320 kEUR. Allocate it across the ten Level-1 WBS elements of §16.2.1 using the default percentages, then re-allocate for a mission whose payload is a custom hyperspectral imager with 60 kEUR of NRE (Chapter 13 §13.1.3). Which elements shrink to absorb the payload growth, and what does that imply for the test campaign?

3. **Cost by phase.** Using the phase percentages of §16.2.2 and a total of 490 kEUR, draw the cumulative spend curve for the 3U mission over a 26-month development schedule (Phase 0/A 4 months, B 6, C 8, D 8, E 36 following). In which month does the project need its largest cash injection, and what happens to the curve if the launch (WBS 8.0) is paid 50 % at contract signature in Phase B?

4. **Learning curve — exact versus approximate.** For first-unit cost $C_1 =$ 800 kEUR and learning rates of 95 %, 90 % and 85 %, compute the total cost of 8, 16 and 32 units using (a) the exact sum $C_1\sum i^{\log_2 L}$ and (b) the continuous approximation of §16.3.1. Tabulate the percentage error of (b) and state the smallest $N$ for which it is below 3 %.

5. **Constellation business case.** Repeat the worked example of §16.3.3 for a 12-satellite constellation at an 85 % learning rate, with two spares, 250 kEUR launch per satellite and a 3-year operations cost of 1.2 MEUR. Compare the per-satellite cost with the single-satellite total of §16.1.6 and explain which WBS elements do *not* benefit from the learning curve.

6. **P50/P80 by Monte Carlo.** Model the bottom-up column of §16.1.6 with the distributions and 1σ values of §16.4.1 (treat a triangular distribution as symmetric about the estimate and a lognormal as having its median at the estimate). Using a spreadsheet with 1 000 trials, estimate P50, P70 and P80 for the total, and compare the P80/P50 ratio with the 1.3 rule of thumb. Which single element contributes most of the spread?

7. **Cost reduction.** Identify the three largest cost drivers in the bottom-up estimate of §16.1.6 and propose a package of changes that cuts the total by 20 % without changing the mission objectives. For each change, state which engineering budget (mass, power, link, data) or risk score moves, and in which direction.

8. **SRR readiness.** For the UniSat-1 design developed in Chapters 5, 8, 9, 11, 13, 14 and 15, assess each SRR criterion of §16.5.1 as pass, partial or fail, name the evidence (section and table number), and write the action item — owner, deliverable, date — for each criterion that is not a clear pass.

9. **Review board.** Form a five-person board using the roles of §16.6.1 to review the EOSat-3U closure table of Chapter 12 §12.5.3, which flags one red line (imaging-mode power). Write the five questions the board would ask, the evidence it would demand for each, and the recommendation (GO / NO GO / GO WITH ACTIONS) you would expect, with the action items.

10. **Presentation.** Draft a six-slide outline for a PDR presentation of the 3U EO mission — mission need, why space, system design and budgets, equipment and verification, risk and cost, operations — and for each slide write the one-sentence conclusion that opens it, in the "lead with the conclusion" form of §16.5.3, with the figure or table of this book that would serve as its evidence.

---

## References

1. NASA, *Cost Estimating Handbook*, version 4.0, 2015. https://www.nasa.gov/offices/ocfo/references-and-tools/
2. Wertz, J. R., Everett, D. F. & Puschell, J. J. (eds.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, Chapter 20 (Cost).
3. The Aerospace Corporation, *Small Satellite Cost Model (SSCM)*. https://www.aerospace.org/capabilities/small-satellite-cost-model
4. NASA, *NPR 7120.5F: NASA Space Flight Program and Project Management Requirements*, 2021 (work breakdown structures). https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7120&s=5F
5. ECSS, *ECSS-M-ST-60C: Cost and Schedule Management*, 2008. https://ecss.nl/standard/ecss-m-st-60c-cost-and-schedule-management/
6. NASA, *NPR 7123.1D: NASA Systems Engineering Processes and Requirements*, Appendix G (Technical Review Process), 2023. https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1D
7. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §3.7 (Technical Reviews). https://www.nasa.gov/reference/systems-engineering-handbook/
8. ECSS, *ECSS-M-ST-10C Rev. 1: Project Planning and Implementation*, 2009, §6 (Reviews). https://ecss.nl/standard/ecss-m-st-10c-rev-1-project-planning-and-implementation/
9. Wright, T. P., "Factors Affecting the Cost of Airplanes", *Journal of the Aeronautical Sciences*, 3(4), 1936, pp. 122–128.
