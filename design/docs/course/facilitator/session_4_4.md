# Session 4.4: Cost Estimation & Design Review


**Prerequisites:** Sessions 4.1-4.3 (equipment selected, V&V planned, risks assessed)
**References:** SMAD4 Ch.20, NASA Cost Estimating Handbook (CEH) v4.0, Aerospace Corp SSCM, NPR 7120.5F (WBS), ECSS-M-ST-60C (Cost Management), NPR 7123.1D Appendix G (Reviews)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Estimate mission cost using parametric (CER), analogy, and bottom-up methods
2. Structure a Work Breakdown Structure (WBS) for a CubeSat project
3. Apply learning curve effects for constellation cost estimation
4. Assess cost risk using confidence levels (P50/P70/P80)
5. Prepare for and conduct a design review (SRR/PDR/CDR) with gate criteria
6. Present design evidence clearly and respond to review board questions

---

## 1. Cost Estimation Methodologies
*[Source: NASA CEH v4.0 Appendix C; SMAD4 Chapter 20; Aerospace Corp SSCM]*
*[URL: https://www.nasa.gov/offices/ocfo/references-and-tools/ (NASA CEH)]*

### Three Primary Methods

| Method | Description | Accuracy (1-sigma) | When to Use | Data Required |
|--------|-------------|-------------------|-------------|---------------|
| **Parametric** | Cost Estimating Relationships (CERs) from historical database | +/- 30-50% | Phase 0/A (few details known) | Mass, power, mission type |
| **Analogy** | Compare to similar past mission, adjust for differences | +/- 20-40% | Phase A/B (reference mission available) | Detailed knowledge of reference |
| **Bottom-up** | Sum actual vendor quotes + labour estimates + facilities | +/- 10-20% | Phase B/C (detailed design) | BOM, vendor quotes, labour rates |

### Parametric Cost Estimating Relationships (CERs)

CERs express cost as a function of technical parameters, derived from regression analysis of historical data.

> **General CER Form:**
>
> Cost = a x (Parameter)^b x Complexity_factor
>
> Where:
> - a = coefficient (from regression)
> - Parameter = usually dry mass (kg), power (W), or data rate
> - b = exponent (typically 0.5-1.0)
> - Complexity_factor = adjustment for mission difficulty

### USCM (Unmanned Space Vehicle Cost Model) CERs

*[Source: SMAD4 Table 20-8; US Air Force USCM database]*

| Subsystem | CER (FY2010 $K) | Parameter | Typical b |
|-----------|-----------------|-----------|-----------|
| Structure | 157 x M_struct^0.83 | Dry mass (kg) | 0.83 |
| Thermal | 394 x M_therm^0.635 | Dry mass (kg) | 0.635 |
| EPS | 62.7 x M_EPS^1.00 | Dry mass (kg) | 1.00 |
| TTC | 545 x M_TTC^0.761 | Dry mass (kg) | 0.761 |
| AOCS | 464 x M_AOCS^0.867 | Dry mass (kg) | 0.867 |
| Propulsion | 17.8 x M_prop^0.75 | Dry mass (kg) | 0.75 |
| Integration & Test | 10.4 x M_dry^0.907 | Total dry mass (kg) | 0.907 |
| Program Management | 12.3% of hardware cost | N/A | N/A |
| Systems Engineering | 14.2% of hardware cost | N/A | N/A |

### SSCM (Small Satellite Cost Model)

The Aerospace Corporation SSCM was specifically calibrated for satellites < 500 kg. It provides more accurate estimates for CubeSats than USCM.

*[Source: Aerospace Corp, "Small Satellite Cost Model (SSCM)", available through Aerospace TOR]*

**Key SSCM adjustments for CubeSats:**
- COTS hardware costs are catalogue prices, not mass-based CERs
- Labour costs dominate for university/small-team projects
- NRE is heavily dependent on mission uniqueness
- Standard CERs (designed for > 100 kg) over-predict by 2-6x for nano/micro class

### CubeSat-Calibrated Pricing (SpaceCDF)

SpaceCDF uses a hybrid approach: COTS flat pricing for nano/micro class, CERs for larger spacecraft.

| Subsystem | CubeSat COTS Cost (kEUR) | USCM CER (kEUR, for CubeSat mass) | Ratio |
|-----------|--------------------------|-----------------------------------|-------|
| EPS | 15 | 60 | CER 4x higher |
| AOCS (fine) | 40 | 66 | CER 1.6x higher |
| TTC (S-band) | 20 | 25 | Similar |
| OBC | 10 | 12 | Similar |
| Structure | 8 | 3 | CER lower (min order effect) |
| Payload | 50 (variable) | 300 | CER 6x higher for COTS payloads |

*This confirms that for CubeSats, COTS pricing is more reliable than parametric CERs for hardware cost.*

### Worked Example: Parametric vs Bottom-Up

*3U Earth observation mission:*

| WBS Element | Parametric (kEUR) | Bottom-Up (kEUR) | Notes |
|-------------|-------------------|-------------------|-------|
| Structure | 8 | 8.5 | ISIS 3U structure |
| EPS | 18 | 16.2 | GomSpace P31u + SA |
| OBC | 12 | 10.0 | NanoAvionics SatBus |
| AOCS | 45 | 42.0 | BCT XACT-15 |
| TTC | 22 | 20.5 | Endurosat S-band |
| Thermal | 5 | 3.0 | Passive only |
| Payload | 65 | 58.0 | Simera Sense xScape |
| Harness | 3 | 2.5 | Custom cables |
| **Hardware subtotal** | **178** | **160.7** | |
| I&T (12%) | 21 | 19.3 | |
| Software (8%) | 14 | 12.9 | |
| PM/SE/MA (13%) | 23 | 20.9 | |
| Launch | 200 | 195.0 | SpaceX Transporter |
| Ground (5%) | 9 | 8.0 | SatNOGS + dedicated |
| Operations (3 yr) | 45 | 40.0 | 0.5 FTE |
| **TOTAL** | **490** | **456.8** | |

*The parametric estimate is ~7% higher than bottom-up. This is expected: parametric includes inherent uncertainty and contingency.*

---

## 2. Cost Breakdown Structure (WBS)
The Work Breakdown Structure (WBS) is the hierarchical decomposition of all work required to complete the mission. It is the foundation for cost estimation, scheduling, and management.

*[Source: NPR 7120.5F Appendix G; ECSS-M-ST-60C; NASA CEH v4.0 Appendix B]*

### Standard CubeSat WBS

```
WBS Level 1: Mission Total
  1.0  Programme Management                5%    (oversight, reviews, reporting)
  2.0  Systems Engineering                 5%    (budgets, interfaces, trade studies)
  3.0  Mission Assurance                   3%    (quality, reliability, parts)
  4.0  Payload                            20%    (instrument + calibration)
    4.1  Payload instrument hardware
    4.2  Payload software
    4.3  Payload calibration & characterisation
  5.0  Spacecraft Bus Hardware            30%    (all subsystems)
    5.1  Structure & mechanisms
    5.2  EPS (solar array + battery + board)
    5.3  AOCS (sensors + actuators)
    5.4  TTC (transponder + antenna)
    5.5  OBC & data handling
    5.6  Thermal control
    5.7  Propulsion (if applicable)
    5.8  Harness & cabling
  6.0  Integration & Test                 12%    (assembly, env. testing)
    6.1  Assembly & integration
    6.2  Environmental test campaign
    6.3  Test facilities rental
  7.0  Software (Flight + Ground)          8%    (FSW, GSW, mission planning)
    7.1  Flight software
    7.2  Ground segment software
    7.3  Mission planning tools
  8.0  Launch Services                    10%    (vehicle, deployer, integration)
  9.0  Ground Segment                      5%    (antennas, MCS, networks)
  10.0 Operations (mission lifetime)       5%    (staff, consumables, maintenance)
```

<!--
SVG Description: Cost Breakdown Structure (WBS) Tree Diagram

A hierarchical tree with "Mission Total" at the top, branching to 10 WBS Level 1 
elements (1.0 PM through 10.0 Operations). WBS 5.0 (Bus Hardware) further branches 
into 5.1-5.8 subsystems. Each box shows the WBS number, name, and percentage of total.
Colour coding: Blue for management (1-3), Green for space segment (4-6), 
Orange for software (7), Red for launch (8), Grey for ground/ops (9-10).
-->

### Cost by Phase

The distribution of cost across lifecycle phases is important for budgeting:

| Phase | % of Total | Activities | Peak Staffing |
|-------|-----------|-----------|---------------|
| 0/A (Concept) | 5-10% | Studies, trade-offs, requirements | Low |
| B (Preliminary Design) | 15-20% | PDR, detailed analysis, long-lead procurement | Growing |
| C (Detailed Design) | 30-40% | CDR, manufacturing, software development | Peak |
| D (Integration & Test) | 20-25% | Assembly, environmental testing, commissioning | High |
| E (Operations) | 10-20% | Routine operations, anomaly management | Low-steady |
| F (Disposal) | 1-3% | Decommissioning, deorbit | Minimal |

---

## 3. Learning Curve for Constellations
*[Source: SMAD4 section 20.3; Wright's Learning Curve Theory (1936)]*

When building multiple identical units, the cost per unit decreases due to manufacturing efficiency, reduced test time, bulk purchasing, and labour learning.

### Wright's Learning Curve

> **Nth Unit Cost:**
>
> C_N = C_1 x N^b
>
> Where b = ln(learning_rate) / ln(2)
>
> | Learning Rate | b | Cost of 10th Unit (% of 1st) |
> |--------------|-----|-----|
> | 95% | -0.074 | 77% |
> | 90% | -0.152 | 60% |
> | 85% | -0.234 | 47% |

> **Total Cost for N Units (cumulative):**
>
> C_total = C_1 x Sum from i=1 to N of (i^b)
>
> Or approximately: C_total ~ C_1 x N^(1+b) / (1+b)  (continuous approximation)

### Simplified Rule of Thumb

> At a **90% learning rate**, every time you **double** the number of units, the unit cost drops by **10%**.
>
> Unit 1: EUR 800K
> Unit 2: EUR 720K (800 x 0.90)
> Unit 4: EUR 648K (720 x 0.90)
> Unit 8: EUR 583K (648 x 0.90)
> Unit 16: EUR 525K (583 x 0.90)

### Worked Example: 20-Satellite Constellation

*First unit cost (bus + payload + I&T): EUR 800K. Learning rate: 90%.*

| Units | b | Avg Unit Cost | Total Hardware | Calc |
|-------|---|--------------|----------------|------|
| 1 | -0.152 | EUR 800K | EUR 800K | First unit |
| 5 | -0.152 | EUR 659K | EUR 3,295K | 5 x 800 x 5^(-0.152) |
| 10 | -0.152 | EUR 577K | EUR 5,770K | Cumulative sum |
| 20 | -0.152 | EUR 505K | EUR 10,100K | Cumulative sum |

Total constellation estimate:
- 20 satellites hardware: EUR 10.1M
- 2 spare units (10%): EUR 1.0M
- Launch (20 sats x EUR 200K rideshare): EUR 4.0M
- Ground segment: EUR 1.0M
- Operations (3 years): EUR 0.9M
- PM/SE/MA (10%): EUR 1.7M
- **Total: ~EUR 18.7M**

---

## 4. Cost Risk and Confidence Levels
Point estimates are misleading. Every cost estimate has uncertainty. The standard practice is to express cost as a probability distribution.

*[Source: NASA CEH v4.0 section 2.3; JPL parametric estimation practice]*

### Uncertainty by Cost Element

| Cost Element | Distribution | Uncertainty (1-sigma) | Rationale |
|-------------|-------------|----------------------|-----------|
| COTS hardware | Normal | +/- 10% | Known pricing from vendor quotes |
| Custom hardware | Lognormal | +/- 30% | Development uncertainty skews high |
| Software | Triangular | +/- 40% | Hardest to estimate; frequent overruns |
| Launch | Normal | +/- 15% | Published pricing; contract negotiation |
| Operations | Uniform | +/- 25% | Staffing level uncertainty |
| I&T | Lognormal | +/- 25% | Test anomalies cause schedule/cost growth |

### Confidence Levels

| Percentile | Meaning | Use |
|-----------|---------|-----|
| **P50** | 50% probability of being at or below this cost | Project baseline; "expected" cost |
| **P70** | 70% probability | NASA standard commitment level (NPR 7120.5F) |
| **P80** | 80% probability | Conservative planning; typical for proposals |

> **Rule of Thumb for CubeSat Missions:**
>
> P70 ~ P50 x 1.2
> P80 ~ P50 x 1.3
>
> Example: If P50 = EUR 500K, then P80 ~ EUR 650K.
>
> *This approximation assumes moderate complexity and well-understood COTS hardware. For missions with custom payloads or new technology, use P80 ~ P50 x 1.5.*

---

### 1U Worked Example: UniSat-1

**Cost Breakdown: Simple WBS, Mostly COTS**

UniSat-1's cost structure is fundamentally different from larger missions because (a) nearly all hardware is COTS, so NRE is near zero, and (b) the team is small and university-based, so labour costs are low.

> **UniSat-1 WBS Cost Estimate (Parametric vs Bottom-Up):**
>
> | WBS Element | Parametric (kEUR) | Bottom-Up (kEUR) | Notes |
> |-------------|-------------------|-------------------|-------|
> | 1.0 Programme Management | 4 | 5 | Faculty oversight, 0.1 FTE x 12 months |
> | 2.0 Systems Engineering | 3 | 3 | Student team lead |
> | 3.0 Mission Assurance | 1 | 1 | Minimal QA for university mission |
> | 4.0 Payload | 8 | 8 | MEMS sensor PCB + calibration |
> | 5.0 Bus Hardware | 38 | 36 | See BOM from Session 4.1 |
> |   5.1 Structure | 4 | 4 | ISIS 1U frame |
> |   5.2 EPS + SA | 20 | 19.5 | P31us + body-mounted cells |
> |   5.3 AOCS (passive) | 1 | 1 | Magnet + hysteresis rods |
> |   5.4 Comms (UHF) | 11 | 10.5 | AX100 + antenna |
> |   5.5 OBC | 3 | 3 | Custom Cortex-M board |
> | 6.0 I&T | 8 | 8 | University clean room + vibe test facility |
> | 7.0 Software | 5 | 5 | FSW (FreeRTOS) + GSW |
> | 8.0 Launch | 15 | 15 | NanoRacks 1U ISS deployment |
> | 9.0 Ground Segment | 5 | 5 | Yagi antenna + SatNOGS network |
> | 10.0 Operations (6 months) | 3 | 3 | Student operators, 0.2 FTE |
> | **TOTAL (P50)** | **~90** | **~85** | |
> | **P80 (x 1.3)** | **~117** | **~111** | Conservative estimate |

**Key cost observations for 1U missions:**

1. **Hardware is cheap:** Total COTS hardware cost is ~36--44 kEUR. This is less than a single star tracker for a 3U mission.

2. **NRE is minimal:** Only the OBC and payload require custom development. NRE is estimated at ~8 kEUR (payload calibration + OBC board layout), compared to ~50--150 kEUR for custom payloads on larger missions.

3. **Launch cost is proportionally large:** At 15 kEUR, the launch represents ~18% of total cost. For a 3U mission at ~200 kEUR launch cost, launch is ~40% of total. The 1U launch cost is low in absolute terms but still a significant fraction.

4. **Labour dominates:** For a university team, the "free" student labour is the hidden cost. If students were costed at professional rates (~50 EUR/hr), the total labour cost would be ~100--200 kEUR, far exceeding the hardware cost. This is typical for educational missions.

5. **No cost drivers from complexity:** There is no AOCS software development, no deployable mechanism qualification, no propulsion system integration, no thermal vacuum testing of heaters -- all of which add 10--50 kEUR each on a 3U mission.

**Learning curve applicability:** If a university builds a series of 1U demonstrators (UniSat-1, UniSat-2, UniSat-3...), the 90% learning rate applies:

| Unit | Hardware Cost (kEUR) | Total Cost (kEUR) |
|------|---------------------|-------------------|
| UniSat-1 | 44 | 85 |
| UniSat-2 | 40 | 77 |
| UniSat-4 | 36 | 69 |
| UniSat-8 | 32 | 62 |

The asymptotic floor is dominated by launch cost (15 kEUR) and irreducible ground segment + operations costs (~8 kEUR), giving a minimum mission cost of ~40--50 kEUR for repeat builds.

---

## 5. Design Review Process
Design reviews are formal decision gates where the project demonstrates readiness to proceed to the next lifecycle phase.

*[Source: NPR 7123.1D Appendix G; ECSS-M-ST-10C Rev.1 section 6; NASA SEH Rev 2 section 3.7]*
*[URL: https://www.nasa.gov/reference/systems-engineering-handbook/]*

### Review Sequence

| Review | Phase Transition | Key Question | Entry Criteria |
|--------|-----------------|-------------|----------------|
| **MCR** | Pre-A -> A | Is the mission need justified? | Problem statement, stakeholders, objectives defined |
| **SRR** | A -> B | Are requirements complete, consistent, traceable? | Requirements baselined, ConOps defined, feasibility shown |
| **PDR** | B -> C | Does preliminary design meet requirements with margin? | All budgets close, interfaces defined, risks identified |
| **CDR** | C -> D | Is detailed design complete and ready to build? | All drawings released, test plan approved, suppliers under contract |
| **TRR** | Pre-test | Is the system ready for environmental testing? | Assembly complete, procedures approved, facility booked |
| **QR** | Post-test | Has the system passed all tests? | All test reports approved, NCRs closed, V&V matrix complete |
| **FRR** | Pre-launch | Is everything ready for launch? | Shipping approved, launch manifest confirmed, operations ready |

### Gate Criteria for SRR (Phase A -> B)

| # | Criterion | Priority | Evidence |
|---|-----------|----------|----------|
| 1 | All Level 0/1 requirements baselined | Must pass | Requirements document signed |
| 2 | ConOps defined (all mission phases) | Must pass | ConOps document |
| 3 | Mission architecture trades completed | Must pass | Trade study reports with rationale |
| 4 | Feasibility confirmed (all budgets positive) | Must pass | Mass, power, link budgets with margin |
| 5 | Risk register established with mitigations | Must pass | Risk register with scores and plans |
| 6 | Preliminary V&V approach defined | Should pass | V&V matrix with methods assigned |
| 7 | Schedule and cost estimate (P50/P80) | Must pass | Cost estimate with WBS |
| 8 | Interface requirements identified | Should pass | N^2 matrix or ICD outline |

### Gate Criteria for PDR (Phase B -> C)

| # | Criterion | Priority | Evidence |
|---|-----------|----------|----------|
| 1 | All requirements allocated to subsystems | Must pass | Requirements allocation matrix |
| 2 | Preliminary design complete for all subsystems | Must pass | Design documents, block diagrams |
| 3 | All budgets close with >= 20% margin | Must pass | Mass, power, link, data, pointing budgets |
| 4 | Equipment selected (BOM) | Must pass | BOM with TRL, heritage, cost, lead time |
| 5 | All interfaces defined (N^2 matrix) | Must pass | Interface control documents |
| 6 | V&V matrix complete with methods assigned | Must pass | V&V matrix |
| 7 | Risk register updated; no Critical risks unmitigated | Must pass | Risk register |
| 8 | Test plan outline approved | Should pass | Environmental test plan |
| 9 | Software architecture defined | Should pass | Software design document |
| 10 | Cost estimate updated (bottom-up) | Must pass | Cost estimate with vendor quotes |

### Presentation Skills for Reviews

**Do:**
- Lead with the conclusion ("Mass budget closes with 22% margin")
- Show evidence, not just assertions ("Link budget analysis shows 4.2 dB margin at worst case")
- Acknowledge risks honestly ("Antenna deployment is our highest risk at L3 x C4 = 12")
- Answer questions directly; say "I don't know, we'll take an action" if needed

**Do not:**
- Read slides aloud
- Hide problems (review boards always find them)
- Present analysis without assumptions stated
- Skip backup slides -- have detailed data ready

---

## 6. Cost & Review Exercise
### Instructions

**Part A: Cost Estimation**

1. **Dashboard** -- Check the Cost KPI card (total cost in MEUR)
2. **Cost Breakdown** tab -- Review the breakdown by subsystem
3. **Exports** tab -- Generate BOM and sum COTS component costs
4. On Worksheet 4.4:
   - Fill in the WBS cost table using both parametric and bottom-up methods
   - Compute P50 and P80 estimates
   - If constellation: apply 90% learning curve

**Part B: Design Review Preparation**

1. Open the **Gate Review** tab in SpaceCDF
2. Check all criteria: which are Pass/Fail/Manual?
3. For any failing criteria, click **"Go fix"** and resolve
4. Prepare a 3-minute summary of your design for peer review

### Worksheet 4.4 Tasks

1. Build a complete WBS cost table (parametric and bottom-up columns)
2. Compute P50 and P80 total cost estimates
3. If constellation: compute total cost with learning curve applied
4. Identify top 3 cost drivers and propose 20% cost reduction
5. List the gate criteria for SRR/PDR and assess your readiness

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | NASA Cost Estimating Handbook v4.0 | https://www.nasa.gov/offices/ocfo/references-and-tools/ |
| 2 | SMAD4 Chapter 20 (Cost) | Wertz, Everett, Puschell (eds.), Space Mission Engineering, Microcosm 2011 |
| 3 | Aerospace Corp SSCM | https://www.aerospace.org/capabilities/small-satellite-cost-model |
| 4 | NPR 7120.5F (WBS) | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7120&s=5F |
| 5 | ECSS-M-ST-60C (Cost Management) | https://ecss.nl/standard/ecss-m-st-60c-cost-and-schedule-management/ |
| 6 | NPR 7123.1D (SE Processes) Appendix G | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1D |
| 7 | NASA SEH Rev 2, section 3.7 | https://www.nasa.gov/reference/systems-engineering-handbook/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Cost methods | Parametric (early, CERs), Analogy (reference mission), Bottom-up (vendor quotes) |
| CubeSat costs | COTS pricing often lower than CER predictions; use hybrid approach |
| WBS | Standard 10-element structure: PM, SE, MA, Payload, Bus, I&T, SW, Launch, Ground, Ops |
| CERs | Cost = a x M^b; USCM/SSCM databases; CubeSats need calibrated CERs |
| Learning curve | 90% rate: each doubling of quantity reduces unit cost by 10% |
| Cost risk | P50 (baseline), P70 (NASA commitment), P80 (conservative); P80 ~ P50 x 1.3 |
| Reviews | SRR, PDR, CDR: formal gates with exit criteria; must pass before proceeding |
| Presentation | Lead with conclusions, show evidence, acknowledge risks, answer directly |
