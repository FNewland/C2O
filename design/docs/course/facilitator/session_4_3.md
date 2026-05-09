# Session 4.3: Risk, Interfaces & FMECA

**Duration:** 2 hours
**Prerequisites:** Sessions 4.1-4.2 (equipment selected, V&V methods assigned)
**References:** ECSS-M-ST-80C (Risk Management), ECSS-Q-ST-30-02C (FMEA/FMECA), ECSS-E-ST-10-24C (Interface Management), NASA SEH Rev 2 section 6.4, NPR 8000.4B

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Construct and populate a risk register using a 5x5 likelihood-consequence matrix
2. Build an N-squared (N^2) interface matrix and identify interface conflicts
3. Perform a simplified FMEA/FMECA for critical subsystems
4. Identify single-point failures and compute series/parallel reliability
5. Classify risks and select appropriate mitigation strategies (accept, mitigate, transfer, avoid)

---

## 1. Risk Management Process (20 min)

### Teaching Notes

*[Source: ECSS-M-ST-80C (Risk Management); NASA SEH Rev 2 section 6.4 (Process 13: Technical Risk Management)]*
*[URL: https://ecss.nl/standard/ecss-m-st-80c-risk-management-31-july-2008/]*

### The Four-Step Process

Risk management is continuous throughout the project lifecycle. The four steps are:

1. **Identify** -- What can go wrong? (Brainstorming, checklists, historical data, expert judgment)
2. **Assess** -- How likely is it? How severe would the consequence be? (Scoring)
3. **Mitigate** -- What can we do to reduce likelihood or consequence? (Strategy selection)
4. **Monitor** -- Is the risk increasing, decreasing, or stable? (Tracking, triggers, escalation)

### Risk Sources

| Source | Example Risks |
|--------|--------------|
| **Technical** | Component failure, interface mismatch, performance shortfall, software defect |
| **Schedule** | Component delivery delay, test facility unavailable, regulatory delay |
| **Cost** | Component price increase, scope creep, test campaign overrun |
| **Programmatic** | Funding cut, personnel turnover, partner withdrawal |
| **External** | Launch delay/failure, spectrum interference, export control denial |

---

## 2. The 5x5 Risk Matrix (25 min)

### Teaching Notes

The 5x5 matrix is the standard risk scoring tool used across ESA, NASA, and commercial space programmes.

### Likelihood Scale

| Level | Likelihood | Description | Probability Range |
|-------|-----------|-------------|-------------------|
| 1 | Remote | Very unlikely; no precedent in similar missions | < 5% |
| 2 | Unlikely | Could happen but improbable; has occurred rarely | 5 - 20% |
| 3 | Possible | Has happened on similar missions; credible scenario | 20 - 50% |
| 4 | Likely | Expected to occur at least once during the mission | 50 - 80% |
| 5 | Almost certain | Will almost certainly occur; multiple precedents | > 80% |

### Consequence Scale

| Level | Consequence | Technical Impact | Cost Impact | Schedule Impact |
|-------|-----------|-----------------|-------------|----------------|
| 1 | Negligible | No performance impact | < 1% overrun | < 1 week slip |
| 2 | Minor | Minor performance degradation; workaround exists | 1 - 5% overrun | 1 - 4 week slip |
| 3 | Moderate | Significant performance loss; mission degraded | 5 - 15% overrun | 1 - 3 month slip |
| 4 | Major | Mission capability severely degraded; partial loss | 15 - 30% overrun | 3 - 6 month slip |
| 5 | Catastrophic | Mission failure; total loss | > 30% overrun | > 6 month slip or cancellation |

### Risk Score and Classification

> **Risk Score:**
>
> R = L x C
>
> Where L = Likelihood (1-5), C = Consequence (1-5)

### 5x5 Risk Matrix (Colour-Coded)

```
             Consequence ->
             1       2       3       4       5
  L   5 |   5(M) | 10(H) | 15(H) | 20(C) | 25(C) |
  i   4 |   4(L) |  8(M) | 12(H) | 16(C) | 20(C) |
  k   3 |   3(L) |  6(M) |  9(M) | 12(H) | 15(H) |
  e   2 |   2(L) |  4(L) |  6(M) |  8(M) | 10(H) |
  l   1 |   1(L) |  2(L) |  3(L) |  4(L) |  5(M) |
  i
  h
  o
  o
  d

  L = Low (1-4):    Accept and monitor
  M = Medium (5-9): Mitigate if cost-effective
  H = High (10-15): Active mitigation required
  C = Critical (16-25): Redesign or descope required
```

### CubeSat-Specific Risk Examples

| Risk | L | C | Score | Category | Typical Mitigation |
|------|---|---|-------|----------|-------------------|
| Deployment mechanism failure (antenna, SA) | 3 | 4 | 12 | High | Redundant mechanisms; 100+ ground test cycles |
| Communication loss after separation | 2 | 5 | 10 | High | Beacon mode; timer-based antenna deploy; multiple GS |
| ADCS does not achieve pointing specification | 3 | 3 | 9 | Medium | Margin in pointing budget; on-orbit calibration plan |
| Power budget negative during eclipse | 2 | 4 | 8 | Medium | Conservative duty cycling; 20% battery margin |
| COTS component radiation failure (SEU/SEL) | 2 | 4 | 8 | Medium | Watchdog resets; latchup protection circuits; EDAC |
| Software bug causing spurious safe mode entry | 4 | 2 | 8 | Medium | Extensive software testing; staged upload; safe mode must work independently |
| Thermal exceedance (hot case) | 2 | 3 | 6 | Medium | Additional radiator area; duty cycle limit |
| Launch delay (vehicle failure) | 3 | 2 | 6 | Medium | Manifest on multiple vehicles; schedule buffer |
| Spectrum licensing delay | 3 | 2 | 6 | Medium | Start filing 12+ months before planned launch |

### Mitigation Strategies

| Strategy | Description | When to Use | Cost Impact |
|----------|-------------|-------------|-------------|
| **Accept** | Risk is within tolerance; monitor only | Score 1-4 (Low) | None |
| **Mitigate** | Reduce L or C through design changes, testing, or procedures | Score 5-15 | Moderate -- cost of mitigation |
| **Transfer** | Pass risk to another party (insurance, supplier warranty) | Financial risk; operational risk | Premium or contract cost |
| **Avoid** | Change design to eliminate the risk entirely | Score 16-25 (Critical) | May affect performance or cost |

---

## 3. N-Squared (N^2) Interface Matrix (25 min)

### Teaching Notes

The N^2 matrix is the standard systems engineering tool for identifying and managing interfaces between subsystems. It was popularised by NASA and ESA CDF practice.

*[Source: ECSS-E-ST-10-24C (Interface Management); NASA SEH Rev 2 section 6.3 (Process 12: Interface Management)]*

### What is an N^2 Matrix?

For a system with N subsystems, the N^2 matrix is an N x N grid where:
- **Diagonal cells** contain the subsystem names
- **Off-diagonal cells** contain the interfaces between subsystems
- **Cell (i, j)** = outputs FROM subsystem i TO subsystem j (read across the row)
- **Cell (j, i)** = outputs FROM subsystem j TO subsystem i (read down the column)

### N^2 Matrix Example (6 Subsystems)

```
         TO ->
         EPS      OBC      AOCS     TTC      Payload  Structure
FROM
EPS      [EPS]    28V bus  28V bus  28V bus  28V bus   Mounting
         ------   5V reg   5V reg   5V reg   5V reg   bolts
                  I2C HK   I2C HK   I2C HK   
OBC      Pwr cmd  [OBC]    Cmd      TC data  Cmd      ---
         Telem    ------   I2C/SPI  UART     SPI/UART
AOCS     Pwr req  Att data [AOCS]   Att for  Att data Mount
         ---      AOCS HK  ------   antenna  pointing vibration
TTC      Pwr req  Rx data  ---      [TTC]    ---      Antenna
         ---      Cmd fwd           ------            mount
Payload  Pwr req  Sci data Pointing ---      [PYLD]   FOV
         ---      PL HK    request           ------   clearance
Struct   ---      ---      Sensor   Antenna  Payload  [STRUCT]
                           mounting mounting mounting  ------
```

### Interface Types

Colour-code the N^2 matrix by interface type:

| Type | Colour | Examples |
|------|--------|---------|
| **Electrical power** | Red | 28V bus, 5V regulated, switched lines |
| **Data** | Blue | I2C, SPI, UART, CAN, RS-422 |
| **RF** | Green | Coaxial cable, waveguide |
| **Mechanical** | Orange | Mounting bolts, thermal straps, alignment pins |
| **Thermal** | Yellow | Conductive paths, radiative coupling |
| **Software** | Purple | Command interfaces, telemetry packets, mode transitions |

### Interface Conflict Detection

An **interface conflict** exists when:
- Subsystem A expects to send 28V but Subsystem B only accepts 5V
- Subsystem A uses I2C but Subsystem B only has SPI
- Subsystem A is in S-band but Subsystem B antenna is X-band
- Subsystem A mounts on the +Z face but Structure has no mounting provision on +Z

SpaceCDF detects many of these automatically through the **constraint engine** and displays conflicts as warning badges on the Dashboard.

### Worked Example: Detecting a Conflict

*Problem:* The OBC sends commands to the reaction wheels via I2C. The selected reaction wheel unit (RWP100 from Blue Canyon) uses RS-422. This is a data protocol mismatch.

*Resolution options:*
1. Select a different reaction wheel that supports I2C
2. Add an I2C-to-RS-422 bridge (additional component, mass, cost, failure point)
3. Select a different OBC that supports RS-422

*In SpaceCDF:* This conflict would appear as a warning in the Equipment Browser when the reaction wheel is selected, because the system checks data protocol compatibility.

---

## 4. FMEA/FMECA (25 min)

### Teaching Notes

*[Source: ECSS-Q-ST-30-02C (Failure Mode, Effects, and Criticality Analysis); ECSS-Q-ST-30C (Dependability)]*
*[URL: https://ecss.nl/standard/ecss-q-st-30-02c-failure-mode-effects-and-criticality-analysis-fmeca-6-march-2009/]*

### Definitions

- **FMEA** (Failure Mode and Effects Analysis): Identifies failure modes, their causes, and effects on the system
- **FMECA** (Failure Mode, Effects, and Criticality Analysis): FMEA + criticality ranking

### FMEA/FMECA Table Structure

| Item | Function | Failure Mode | Cause | Local Effect | System Effect | Severity | Detection | Compensating Provision | Criticality |
|------|----------|-------------|-------|-------------|---------------|----------|-----------|----------------------|------------|
| OBC | Process commands, run FSW | Processor lockup | SEU, firmware bug | No command processing | Loss of mission control | 5 | HK timeout | Watchdog reset; redundant OBC (if fitted) | 1 (SPF) |
| Battery | Store energy | Cell short | Manufacturing defect | Reduced capacity | Shortened eclipse survival | 3 | Voltage monitoring | Cell balancing; margin in capacity | 2 |
| Reaction Wheel | Provide torque | Bearing seizure | Lubrication failure | Loss of one axis control | Degraded pointing | 4 | Current anomaly | 4-wheel config (3+1 redundancy) | 3 (with redundancy) |
| Antenna | Radiate RF | Deployment failure | Mechanism jam | No antenna deployed | No communication | 5 | Beacon absence | Redundant deployment; burn wire + spring | 1 (SPF) |

### Criticality Categories

| Category | Definition | Action Required |
|----------|-----------|----------------|
| **1 (Catastrophic)** | Single failure causes mission loss; no compensation | Redesign to add redundancy or accept with justification |
| **2 (Critical)** | Single failure causes significant degradation | Mitigate (redundancy, operational workaround) |
| **3 (Major)** | Single failure causes moderate degradation | Monitor; plan operational workaround |
| **4 (Minor)** | Single failure has negligible mission impact | Accept |

### Single-Point Failure (SPF) Analysis

A **single-point failure** is any single component whose failure alone causes loss of mission. Identifying SPFs is a critical output of the FMECA.

**Typical CubeSat Single-Point Failures:**

| Component | Why it is an SPF | Common Mitigation |
|-----------|-----------------|-------------------|
| OBC (single processor) | No command processing -> no mission | Watchdog timer + autonomous safe mode + EDAC memory |
| Battery (single pack) | No stored energy -> no eclipse survival | Cell-level monitoring; conservative DoD limit (< 20%) |
| Antenna (non-redundant deploy) | No RF link -> no commanding/telemetry | Redundant deployment mechanisms (burn wire + spring) |
| Solar array (deployment) | No power generation -> mission loss within hours | Redundant deployment; hinge spring + motor backup |
| EPS main board | No power distribution | Typically no mitigation (accepted SPF in CubeSats) |

### Key Equations: Reliability

> **Series Reliability (all components must work):**
>
> R_series = Product of R_i for i = 1 to n
>
> For n components each with reliability R_i:
> R_series = R_1 x R_2 x ... x R_n
>
> Example: 5 components each with R = 0.99:
> R_series = 0.99^5 = 0.951

> **Parallel Reliability (at least one must work -- redundancy):**
>
> R_parallel = 1 - Product of (1 - R_i) for i = 1 to n
>
> For n identical redundant units each with R:
> R_parallel = 1 - (1 - R)^n
>
> Example: 2 redundant deployment mechanisms each with R = 0.95:
> R_parallel = 1 - (1 - 0.95)^2 = 1 - (0.05)^2 = 1 - 0.0025 = 0.9975

> **Mean Time Between Failures (MTBF):**
>
> MTBF = Total_operating_hours / Number_of_failures
>
> For a component with failure rate lambda (failures/hour):
> MTBF = 1 / lambda
>
> **Reliability over time (exponential model):**
> R(t) = e^(-t / MTBF) = e^(-lambda * t)
>
> Example: MTBF = 50,000 hours, mission duration = 8,760 hours (1 year):
> R = e^(-8760/50000) = e^(-0.1752) = 0.839

> **System Availability:**
>
> A = MTBF / (MTBF + MTTR)
>
> Where MTTR = Mean Time To Repair (or recover, for spacecraft)
>
> For a spacecraft with MTBF = 50,000 hr and MTTR = 2 hr (safe mode recovery):
> A = 50000 / (50000 + 2) = 0.99996

### Worked Example: Reaction Wheel Redundancy

*Problem:* A fine-pointing mission requires 3-axis attitude control. Each reaction wheel has R = 0.98 over the 2-year mission.

*Configuration A -- 3 wheels (no redundancy):*
R_system = R^3 = 0.98^3 = 0.941

*Configuration B -- 4 wheels in 3-of-4 redundancy (1 spare):*
R_system = 4 x R^4 - 3 x R^3 ... Using the binomial:
P(>= 3 working) = C(4,4) x R^4 + C(4,3) x R^3 x (1-R)^1
= 0.98^4 + 4 x 0.98^3 x 0.02
= 0.9224 + 4 x 0.9412 x 0.02
= 0.9224 + 0.0753
= 0.9977

*Adding one spare wheel improves reliability from 0.941 to 0.998 -- a significant improvement for modest mass and cost increase.*

### Real Mission Example: Hitomi (ASTRO-H)

JAXA's Hitomi X-ray observatory was lost on 26 March 2016, just 37 days after launch, due to a cascading failure in the AOCS subsystem:
1. An incorrect parameter in the star tracker caused an erroneous attitude estimate
2. The reaction wheels applied incorrect torques based on the bad estimate
3. Thrusters fired to "correct" the (phantom) attitude error, causing rapid spin
4. The satellite spun up beyond structural limits, and the extensible optical bench broke off

**Root cause:** Software parameter error (unit conversion) + inadequate FDIR logic + no cross-check between attitude sensors.

*Lesson: FMECA must consider cascading failures and common-cause failures, not just single-component failures. Software errors are failure modes too.*

*[Source: JAXA Hitomi Investigation Report, 2016, available at https://global.jaxa.jp/press/2016/05/20160531_hitomi.html]*

---

## 5. Risk & Interface Exercise (25 min)

### Instructions

1. **Dashboard** -- Check the reliability score and conflict count
2. **Risk Register Construction** (Worksheet 4.3):
   - Identify **5 technical risks** for your mission design
   - Score each on the 5x5 matrix (L x C)
   - Define mitigation strategy for any scoring >= 10
   - Assign an owner (which CDF position is responsible)
3. **N^2 Matrix** -- Build a simplified N^2 matrix for your mission:
   - List 6 subsystems on the diagonal
   - Fill in the interfaces (power, data, RF, mechanical)
   - Identify at least 2 interface conflicts
4. **SPF Analysis** -- Identify all single-point failures in your design:
   - For each SPF: Is it acceptable? If not, what redundancy is needed?
   - Compute the reliability improvement from adding redundancy to one SPF

### Discussion Prompts

- "What is the highest-risk item in your design? What would it cost to mitigate?"
- "Do you have any interface conflicts that cannot be resolved without changing a component selection?"
- "Which single-point failure are you most concerned about? Would the customer accept it?"

### Worksheet 4.3 Tasks

1. Complete the risk register (5 risks minimum, scored)
2. Build a 6x6 N^2 interface matrix with colour-coded interface types
3. Complete the FMECA table for 4 critical components
4. List all single-point failures with accept/mitigate decision
5. Calculate series reliability for your mission's critical chain

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-M-ST-80C (Risk Management) | https://ecss.nl/standard/ecss-m-st-80c-risk-management-31-july-2008/ |
| 2 | ECSS-Q-ST-30-02C (FMEA/FMECA) | https://ecss.nl/standard/ecss-q-st-30-02c-failure-mode-effects-and-criticality-analysis-fmeca-6-march-2009/ |
| 3 | ECSS-E-ST-10-24C (Interface Management) | https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/ |
| 4 | NASA SEH Rev 2, section 6.4 | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| 5 | JAXA Hitomi Investigation Report | https://global.jaxa.jp/press/2016/05/20160531_hitomi.html |
| 6 | ECSS-Q-ST-30C (Dependability) | https://ecss.nl/standard/ecss-q-st-30c-dependability/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Risk process | Identify -> Assess -> Mitigate -> Monitor (continuous throughout lifecycle) |
| 5x5 matrix | L x C = Risk Score; Low (1-4), Medium (5-9), High (10-15), Critical (16-25) |
| Strategies | Accept (low), Mitigate (medium-high), Transfer (financial), Avoid (critical) |
| N^2 matrix | N x N grid mapping all subsystem interfaces; colour-code by type |
| Interface conflicts | Protocol mismatch, voltage mismatch, band mismatch -- detect early |
| FMECA | Failure mode -> cause -> local effect -> system effect -> severity -> detection -> mitigation |
| SPF | Single-point failures must be identified, assessed, and accepted or mitigated |
| Reliability | R_series = Product(R_i); R_parallel = 1 - Product(1-R_i); R(t) = e^(-lambda*t) |
