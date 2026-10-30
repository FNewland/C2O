# Chapter 15 — Risk Management, Interface Control and FMECA

> **Recommended background.** ECSS-M-ST-80C (Risk management); ECSS-Q-ST-30-02C (Failure modes, effects and criticality analysis); ECSS-Q-ST-30C (Dependability); ECSS-E-ST-10-24C (Interface management); NASA SEH Rev 2 §6.4 (Technical risk management); NASA NPR 8000.4B (Agency risk management). This chapter assumes the equipment has been selected (Chapter 13) and the verification methods assigned (Chapter 14); it draws on the N² interface analysis of Chapter 8 §8.3 and feeds the cost-risk treatment of Chapter 16 and the FDIR design of Chapter 18.

## Learning objectives

By the end of this chapter, you will be able to:

1. Construct and populate a risk register using a 5×5 likelihood–consequence matrix
2. Treat the interfaces identified in an N² matrix as a source of risk and carry interface conflicts into the risk register
3. Perform a simplified FMEA/FMECA for critical subsystems
4. Identify single-point failures and compute series, parallel and $k$-of-$n$ reliability
5. Classify risks and select appropriate mitigation strategies (accept, mitigate, transfer, avoid)

Vendor products named in this chapter are representative examples, not endorsements.

---

## 15.1 Risk management process

*[Source: ECSS-M-ST-80C (Risk Management); NASA SEH Rev 2 §6.4 (Process 13: Technical Risk Management)]*

### 15.1.1 The four-step process

Risk management is continuous throughout the project lifecycle. The four steps are:

1. **Identify** — What can go wrong? (Brainstorming, checklists, historical data, expert judgement)
2. **Assess** — How likely is it? How severe would the consequence be? (Scoring)
3. **Mitigate** — What can we do to reduce the likelihood or the consequence? (Strategy selection)
4. **Monitor** — Is the risk increasing, decreasing or stable? (Tracking, triggers, escalation)

### 15.1.2 Risk sources

| Source | Example risks |
|--------|--------------|
| **Technical** | Component failure, interface mismatch, performance shortfall, software defect |
| **Schedule** | Component delivery delay, test facility unavailable, regulatory delay |
| **Cost** | Component price increase, scope creep, test-campaign overrun |
| **Programmatic** | Funding cut, personnel turnover, partner withdrawal |
| **External** | Launch delay or failure, spectrum interference, export-control denial |

---

## 15.2 The 5×5 risk matrix

The 5×5 matrix is the standard risk-scoring tool used across ESA, NASA and commercial space programmes. Figure 15.1 shows it in the ECSS-M-ST-80C form.

### 15.2.1 Likelihood scale

| Level | Likelihood | Description | Probability range |
|-------|-----------|-------------|-------------------|
| 1 | Remote | Very unlikely; no precedent in similar missions | < 5 % |
| 2 | Unlikely | Could happen but improbable; has occurred rarely | 5–20 % |
| 3 | Possible | Has happened on similar missions; credible scenario | 20–50 % |
| 4 | Likely | Expected to occur at least once during the mission | 50–80 % |
| 5 | Almost certain | Will almost certainly occur; multiple precedents | > 80 % |

### 15.2.2 Consequence scale

| Level | Consequence | Technical impact | Cost impact | Schedule impact |
|-------|-----------|-----------------|-------------|----------------|
| 1 | Negligible | No performance impact | < 1 % overrun | < 1 week slip |
| 2 | Minor | Minor performance degradation; workaround exists | 1–5 % overrun | 1–4 week slip |
| 3 | Moderate | Significant performance loss; mission degraded | 5–15 % overrun | 1–3 month slip |
| 4 | Major | Mission capability severely degraded; partial loss | 15–30 % overrun | 3–6 month slip |
| 5 | Catastrophic | Mission failure; total loss | > 30 % overrun | > 6 month slip or cancellation |

### 15.2.3 Risk score and classification

> **Risk score:**
>
> $$R = L \times C$$
>
> where $L$ = likelihood (1–5) and $C$ = consequence (1–5).

| Likelihood ↓ / Consequence → | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | 5 (M) | 10 (H) | 15 (H) | 20 (C) | 25 (C) |
| **4** | 4 (L) | 8 (M) | 12 (H) | 16 (C) | 20 (C) |
| **3** | 3 (L) | 6 (M) | 9 (M) | 12 (H) | 15 (H) |
| **2** | 2 (L) | 4 (L) | 6 (M) | 8 (M) | 10 (H) |
| **1** | 1 (L) | 2 (L) | 3 (L) | 4 (L) | 5 (M) |

- **L = Low (1–4):** accept and monitor
- **M = Medium (5–9):** mitigate if cost-effective
- **H = High (10–15):** active mitigation required
- **C = Critical (16–25):** redesign or descope required

![5×5 risk matrix (ECSS-M-ST-80C).](../assets/figures/fig_risk_matrix.png)

**Figure 15.1** — The 5×5 likelihood–consequence matrix with the four acceptance bands (low, medium, high, critical) and representative CubeSat risks plotted at their scores. A mitigation moves a risk down (lower likelihood) or left (lower consequence); the register records both the pre- and post-mitigation position.

### 15.2.4 CubeSat-specific risk examples

| Risk | L | C | Score | Category | Typical mitigation |
|------|---|---|-------|----------|-------------------|
| Deployment mechanism failure (antenna, solar array) | 3 | 4 | 12 | High | Redundant mechanisms; 100+ ground test cycles |
| Communication loss after separation | 2 | 5 | 10 | High | Beacon mode; timer-based antenna deployment; multiple ground stations |
| ADCS does not achieve the pointing specification | 3 | 3 | 9 | Medium | Margin in the pointing budget; on-orbit calibration plan |
| Power budget negative during eclipse | 2 | 4 | 8 | Medium | Conservative duty cycling; 20 % battery margin |
| COTS component radiation failure (SEU/SEL) | 2 | 4 | 8 | Medium | Watchdog resets; latch-up protection circuits; EDAC |
| Software bug causing spurious safe-mode entry | 4 | 2 | 8 | Medium | Extensive software testing; staged upload; safe mode must work independently |
| Thermal exceedance (hot case) | 2 | 3 | 6 | Medium | Additional radiator area; duty-cycle limit |
| Launch delay (vehicle failure) | 3 | 2 | 6 | Medium | Manifest on multiple vehicles; schedule buffer |
| Spectrum licensing delay | 3 | 2 | 6 | Medium | Start filing 12+ months before the planned launch (Chapter 2 §2.7) |

### 15.2.5 Mitigation strategies

| Strategy | Description | When to use | Cost impact |
|----------|-------------|-------------|-------------|
| **Accept** | Risk is within tolerance; monitor only | Score 1–4 (low) | None |
| **Mitigate** | Reduce $L$ or $C$ through design changes, testing or procedures | Score 5–15 | Moderate — cost of mitigation |
| **Transfer** | Pass the risk to another party (insurance, supplier warranty) | Financial risk; operational risk | Premium or contract cost |
| **Avoid** | Change the design to eliminate the risk entirely | Score 16–25 (critical) | May affect performance or cost |

---

## 15.3 Interfaces as a source of risk

The N² matrix is constructed in Chapter 8 §8.3: Table 8.1 is the six-subsystem example, Table 8.2 defines the interface-type codes **M** (mechanical), **E** (electrical/power), **T** (thermal), **D** (data), **R** (RF), **O** (optical) and **S** (software), and §8.3.5 gives the conflict-detection checks and the I²C/RS-422 worked example. None of that is repeated here. What this section adds is the link from the interface register to the risk register.

Every off-diagonal cell of the N² matrix is a place where two subsystems — and usually two engineers, and often two suppliers — must agree. NASA's experience that most system failures trace back to interface problems (Chapter 8 §8.3) is a statement about likelihood: an interface that has not been written down as a requirement has a high probability of being wrong at integration. Interfaces therefore enter the risk register in three ways:

1. **Unresolved conflicts.** A conflict found by the checks of §8.3.5 (voltage, protocol, band, mounting location) that has not yet been resolved is a risk with $L$ = 4–5 and $C$ set by the severity class of §8.3.5 (critical → $C$ = 4–5, major → 3, minor → 2). It stays in the register until the resolution has become an interface requirement and been verified (Chapter 14).
2. **Undocumented interfaces.** A cell that the N² matrix shows as active but for which no interface requirement or ICD entry exists is a risk in its own right, typically $L$ = 3, $C$ = 3 ("significant performance loss; mission degraded") — the classic case is the R-type coupling between the transmitter and the payload receiver, which no supplier datasheet covers.
3. **Interface-driven failure modes.** The FMECA of §15.4 asks, for each item, "what happens at the boundary?" — a connector that unmates under vibration (M), a bus that is pulled low by one failed device (D), a radiator face that is shadowed by a deployed panel (T). Each of these is tagged with its letter code so that the owner of the interface, not just the owner of the item, sees it.

The practical rule is that each interface risk is tagged with the N² cell it belongs to and its letter code, so that the register can be sorted by interface as well as by score. In a concurrent-design tool with a constraint engine the first category is generated automatically whenever an incompatible pair of components is selected; the second and third require the engineering judgement of the FMECA. Chapter 8 §8.3.6 gives the format of the interface requirement that closes an interface risk.

---

## 15.4 FMEA/FMECA

*[Source: ECSS-Q-ST-30-02C (Failure Modes, Effects and Criticality Analysis); ECSS-Q-ST-30C (Dependability)]*

### 15.4.1 Definitions

- **FMEA** (failure mode and effects analysis): identifies failure modes, their causes and their effects on the system
- **FMECA** (failure mode, effects and criticality analysis): FMEA plus a criticality ranking

### 15.4.2 FMEA/FMECA table structure

| Item | Function | Failure mode | Cause | Local effect | System effect | Severity | Detection | Compensating provision | Criticality |
|------|----------|-------------|-------|-------------|---------------|----------|-----------|----------------------|------------|
| OBC | Process commands, run flight software | Processor lock-up | SEU, firmware bug | No command processing | Loss of mission control | 5 | Housekeeping time-out | Watchdog reset; redundant OBC (if fitted) | 1 (SPF) |
| Battery | Store energy | Cell short | Manufacturing defect | Reduced capacity | Shortened eclipse survival | 3 | Voltage monitoring | Cell balancing; margin in capacity | 2 |
| Reaction wheel | Provide torque | Bearing seizure | Lubrication failure | Loss of one axis of control | Degraded pointing | 4 | Current anomaly | 4-wheel configuration (3 + 1 redundancy) | 3 (with redundancy) |
| Antenna | Radiate RF | Deployment failure | Mechanism jam (M interface) | No antenna deployed | No communication | 5 | Beacon absence | Redundant deployment; burn wire + spring | 1 (SPF) |

### 15.4.3 Criticality categories

| Category | Definition | Action required |
|----------|-----------|----------------|
| **1 (Catastrophic)** | A single failure causes mission loss; no compensation | Redesign to add redundancy or accept with justification |
| **2 (Critical)** | A single failure causes significant degradation | Mitigate (redundancy, operational workaround) |
| **3 (Major)** | A single failure causes moderate degradation | Monitor; plan an operational workaround |
| **4 (Minor)** | A single failure has negligible mission impact | Accept |

Where a numerical ranking is wanted — in automotive and some commercial space practice — the **risk priority number** is used:

$$\text{RPN} = S \times O \times D$$

with severity $S$, occurrence $O$ and detectability $D$ each scored 1–10, so that a failure mode that is severe, frequent and hard to detect scores up to 1000. ECSS-Q-ST-30-02C uses the severity categories above together with a probability class rather than an RPN, but the two schemes rank the same failure modes in the same order.

### 15.4.4 Single-point failure (SPF) analysis

A **single-point failure** is any single component whose failure alone causes loss of mission. Identifying SPFs is a critical output of the FMECA.

**Typical CubeSat single-point failures:**

| Component | Why it is an SPF | Common mitigation |
|-----------|-----------------|-------------------|
| OBC (single processor) | No command processing → no mission | Watchdog timer + autonomous safe mode + EDAC memory |
| Battery (single pack) | No stored energy → no eclipse survival | Cell-level monitoring; conservative DoD limit (< 20 %) |
| Antenna (non-redundant deployment) | No RF link → no commanding or telemetry | Redundant deployment mechanisms (burn wire + spring) |
| Solar array (deployment) | No power generation → mission loss within hours | Redundant deployment; hinge spring + motor backup |
| EPS main board | No power distribution | Typically no mitigation (accepted SPF in CubeSats) |

### 15.4.5 Key equations: reliability

> **Series reliability (all components must work):**
>
> $$R_{\text{series}} = \prod_{i=1}^{n} R_i = R_1 \times R_2 \times \cdots \times R_n$$
>
> Example: 5 components each with $R = 0.99$: $R_{\text{series}} = 0.99^5 = 0.951$

> **Parallel reliability (at least one must work — redundancy):**
>
> $$R_{\text{parallel}} = 1 - \prod_{i=1}^{n} (1 - R_i)$$
>
> For $n$ identical redundant units each with reliability $R$: $R_{\text{parallel}} = 1 - (1 - R)^n$
>
> Example: 2 redundant deployment mechanisms each with $R = 0.95$:
> $R_{\text{parallel}} = 1 - (1 - 0.95)^2 = 1 - 0.05^2 = 1 - 0.0025 = 0.9975$

> **$k$-of-$n$ redundancy (at least $k$ of $n$ identical units must work):**
>
> $$R_{k\text{-of-}n} = \sum_{i=k}^{n} \binom{n}{i} R^i (1 - R)^{n-i}$$

> **Mean time between failures (MTBF):**
>
> $$\text{MTBF} = \frac{\text{total operating hours}}{\text{number of failures}}$$
>
> For a component with constant failure rate $\lambda$ (failures per hour): $\text{MTBF} = 1/\lambda$
>
> **Reliability over time (exponential model):**
> $$R(t) = e^{-t/\text{MTBF}} = e^{-\lambda t}$$
>
> Example: MTBF = 50 000 h, mission duration = 8760 h (1 year):
> $R = e^{-8760/50000} = e^{-0.1752} = 0.839$

> **System availability:**
>
> $$A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}}$$
>
> where MTTR = mean time to repair (or recover, for a spacecraft).
>
> For a spacecraft with MTBF = 50 000 h and MTTR = 2 h (safe-mode recovery): $A = 50000/(50000 + 2) = 0.99996$

### 15.4.6 Worked example: reaction-wheel redundancy

*Problem:* A fine-pointing mission requires 3-axis attitude control. Each reaction wheel has $R = 0.98$ over the 2-year mission.

*Configuration A — 3 wheels (no redundancy):*
$$R_{\text{system}} = R^3 = 0.98^3 = 0.941$$

*Configuration B — 4 wheels in 3-of-4 redundancy (1 spare), using the $k$-of-$n$ formula:*
$$P(\geq 3 \text{ working}) = \binom{4}{4} R^4 + \binom{4}{3} R^3 (1 - R) = 0.98^4 + 4 \times 0.98^3 \times 0.02 = 0.9224 + 4 \times 0.9412 \times 0.02 = 0.9224 + 0.0753 = 0.9977$$

*Adding one spare wheel improves the reliability from 0.941 to 0.998 — a significant improvement for a modest mass and cost increase. The pyramid geometry that lets any three of the four wheels span all three axes is described in Chapter 10 §10.3.* Figure 15.2 draws the two configurations as reliability block diagrams.

![Reliability block diagrams for three wheels in series and four wheels in 3-of-4 voting](../assets/figures/fig_rbd_wheels.png)

**Figure 15.2** — Reliability block diagrams for the reaction-wheel example. Left: three wheels in series, each with R = 0.98, give a system reliability of 0.98³ = 0.941 because any single failure ends three-axis control. Right: four wheels feeding a 3-of-4 voting block give 0.98⁴ + 4 × 0.98³ × 0.02 = 0.9977 ≈ 0.998, since the system survives any one failure.

### 15.4.7 Real mission example: Hitomi (ASTRO-H)

JAXA's Hitomi X-ray observatory was lost on 26 March 2016, just 37 days after launch, owing to a cascading failure in the AOCS subsystem:
1. An incorrect parameter in the star tracker caused an erroneous attitude estimate
2. The reaction wheels applied incorrect torques based on the bad estimate
3. Thrusters fired to "correct" the (phantom) attitude error, causing rapid spin
4. The satellite spun up beyond its structural limits, and the extensible optical bench broke off

**Root cause:** software parameter error (unit conversion) + inadequate FDIR logic + no cross-check between attitude sensors.

*Lesson: FMECA must consider cascading failures and common-cause failures, not just single-component failures. Software errors are failure modes too — and so are interfaces: the S-type interface between the ground-prepared parameter and the on-board estimator is where this failure began.*

*[Source: JAXA Hitomi Investigation Report, 2016]*

---

## 15.5 Returning to UniSat-1: risk register and single-point failures

The UniSat-1 design of Chapters 9–13 is simple enough for its full risk register to fit on one page. The five highest-scoring technical risks, with their owners from the position list of Chapter 1 Table 1.4:

| ID | Risk | N² cell / code | L | C | Score | Strategy | Mitigation | Owner |
|----|------|----------------|---|---|-------|----------|------------|-------|
| R-01 | UHF monopole fails to deploy from its stowed position | Structure → TTC (M) | 3 | 5 | 15 (H) | Mitigate | Burn-wire release with spring backup; 50 deployment cycles in test; beacon on a secondary stub antenna | Structures |
| R-02 | Data budget does not close with a single ground station (Chapter 11 §11.8.2) | TTC → Ground (R, D) | 4 | 3 | 12 (H) | Mitigate | Register with the SatNOGS network before launch; on-board averaging mode halves the data rate | Comms |
| R-03 | Custom OBC (TRL 5) fails in the radiation environment | OBC (SEU/SEL) | 2 | 5 | 10 (H) | Mitigate | MSP430 safe-mode processor with independent watchdog; latch-up current limiting; EDAC on external RAM | OBDH |
| R-04 | Magnetometer data corrupted by the on-board permanent magnet and the EPS switching noise | AOCS → Payload (M, E) | 3 | 3 | 9 (M) | Mitigate | Boom-less placement at the far corner of the stack; characterise the magnet's field in test and subtract it; shielded harness | Payload |
| R-05 | Battery falls below 0 °C in eclipse and cannot charge | EPS ↔ Thermal (T) | 2 | 4 | 8 (M) | Mitigate | Battery heater with thermostat (Chapter 9 §9.5); TVAC verification of the cold case (Chapter 14 §14.5) | Thermal |

**Single-point failures.** UniSat-1 has four: the EPS board, the single battery pack, the UHF transceiver and the antenna deployment. The first three are accepted with justification (a redundant EPS or radio would double the cost of the smallest subsystems and is not CubeSat practice); the fourth is mitigated by R-01. A series reliability estimate for the accepted chain — EPS 0.97, battery 0.98, transceiver 0.97 over one year — gives $R = 0.97 \times 0.98 \times 0.97 = 0.92$, which, combined with the 0.9975 of the redundant deployment, sets the mission's one-year success probability near 0.92. For an 85 kEUR technology demonstration that is acceptable; for the EOSat-3U mission the same calculation is what justifies the fourth reaction wheel.

> **Think about it.** R-02 is the only risk in the register that was created by a budget, not by hardware. Which chapter's calculation would have to change for it to disappear, and what would that change cost?

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Risk process | Identify → assess → mitigate → monitor (continuous throughout the lifecycle) |
| 5×5 matrix | $R = L \times C$; low (1–4), medium (5–9), high (10–15), critical (16–25) |
| Strategies | Accept (low), mitigate (medium–high), transfer (financial), avoid (critical) |
| Interfaces as risk | Every N² cell (Chapter 8 §8.3, Table 8.1) is a risk source; tag interface risks with the M/E/T/D/R/O/S code of Table 8.2 |
| Interface conflicts | Protocol mismatch, voltage mismatch, band mismatch — detect early; unresolved conflicts enter the register |
| FMECA | Failure mode → cause → local effect → system effect → severity → detection → mitigation → criticality (or $\text{RPN} = S \times O \times D$) |
| SPF | Single-point failures must be identified, assessed, and accepted or mitigated |
| Reliability | $R_{\text{series}} = \prod R_i$; $R_{\text{parallel}} = 1 - \prod(1 - R_i)$; $R_{k\text{-of-}n} = \sum_{i=k}^{n}\binom{n}{i}R^i(1-R)^{n-i}$; $R(t) = e^{-\lambda t}$ |

---

## Problems

1. **Risk register.** Identify five technical risks for a 3U Earth-observation CubeSat with a deployable solar array, a star tracker and an S-band downlink. Score each on the 5×5 matrix, classify it, define a mitigation for any risk scoring ≥ 10, and assign an owner from the position list of Chapter 1 Table 1.4. Then re-score each risk after mitigation and show the moves on a sketch of Figure 15.1.

2. **Consequence scales.** A component delivery slips by 10 weeks and adds 8 % to the hardware cost. Score the consequence on each of the three scales of §15.2.2 (technical, cost, schedule), and explain how a single consequence level is chosen when the three disagree.

3. **Interface risks.** Using Chapter 8 Table 8.1, identify the three cells of the EOSat-3U N² matrix most likely to produce an interface risk, tag each with its letter code from Table 8.2, score it, and write the interface requirement (in the "shall" form of Chapter 8 §8.3.6) whose verification would close it.

4. **FMECA.** Complete a four-row FMECA table, in the format of §15.4.2, for the EOSat-3U solar-array deployment mechanism, the S-band transmitter power amplifier, the OBC flash memory and the battery heater. Assign a severity, a detection means and a compensating provision to each, and state which rows are single-point failures.

5. **Series and parallel reliability.** The EOSat-3U critical chain has seven items with one-year reliabilities 0.995, 0.99, 0.99, 0.98, 0.98, 0.97 and 0.96. Compute the series reliability. If the 0.96 item is duplicated in parallel, what is the new chain reliability, and what is the equivalent improvement if instead the 0.98 items are each raised to 0.995 by better screening? Which is cheaper, and why?

6. **$k$-of-$n$.** A 6U CubeSat flies six solar-array strings and can meet its power requirement with any four. Each string has $R = 0.97$ over three years. Compute the probability that the power requirement is met. Repeat for five strings with four needed, and comment on the mass cost of the sixth string.

7. **Exponential reliability.** A COTS reaction wheel has a quoted MTBF of 120 000 h. Compute its reliability over 1, 2 and 5 years, then the 3-of-4 system reliability at each duration. At what mission duration does a 3-of-4 set fall below the 0.95 that a single wheel offers at one year?

8. **Availability.** A spacecraft enters safe mode on average every 400 h and takes 6 h to recover to nominal operations. Compute the availability. If the FDIR of Chapter 18 is improved so that recovery is autonomous and takes 30 minutes, what is the new availability, and how many additional imaging passes per year does that represent for a 4-pass-per-day mission?

9. **Cascading failures.** Reconstruct the Hitomi sequence of §15.4.7 as a chain of FMECA rows, one per step, with the interface code (from Table 8.2) at which each step crossed a subsystem boundary. Identify the single cross-check that would have broken the chain earliest and estimate its implementation cost relative to the mission.

10. **Accept or mitigate.** The UniSat-1 EPS board is an accepted single-point failure. Estimate the mass, cost and schedule of making it redundant (two boards, cross-strapped, with an isolation switch), re-score the risk, and decide whether the mitigation is justified for (a) UniSat-1 and (b) a commercial 3U mission with a 400 kEUR payload. Use the cost-impact column of §15.2.2 in the argument.

---

## References

1. ECSS, *ECSS-M-ST-80C: Risk Management*, 2008. https://ecss.nl/standard/ecss-m-st-80c-risk-management-31-july-2008/
2. ECSS, *ECSS-Q-ST-30-02C: Failure Modes, Effects (and Criticality) Analysis (FMEA/FMECA)*, 2009. https://ecss.nl/standard/ecss-q-st-30-02c-failure-mode-effects-and-criticality-analysis-fmeca-6-march-2009/
3. ECSS, *ECSS-Q-ST-30C Rev. 1: Dependability*, 2017. https://ecss.nl/standard/ecss-q-st-30c-dependability/
4. ECSS, *ECSS-E-ST-10-24C: Interface Management*, 2015. https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/
5. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §6.4. https://www.nasa.gov/reference/systems-engineering-handbook/
6. NASA, *NPR 8000.4B: Agency Risk Management Procedural Requirements*, 2017. https://nodis3.gsfc.nasa.gov
7. JAXA, *Hitomi (ASTRO-H) Anomaly Investigation Report*, 2016. https://global.jaxa.jp/press/2016/05/20160531_hitomi.html
8. US Department of Defense, *MIL-HDBK-338B: Electronic Reliability Design Handbook*, 1998.
9. O'Connor, P. & Kleyner, A., *Practical Reliability Engineering*, 5th ed., Wiley, 2012.
