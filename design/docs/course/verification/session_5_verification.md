# Verification Record — Day 5: Sessions 5.1-5.4

## Verification Date: 2026-05-04

### Session 5.1 Verifications

#### 1. MCR Exit Criteria
**Claim:** MCR evaluates mission need justification, stakeholder identification, objectives, alternatives, and feasibility.
**Verification:** CONFIRMED. NPR 7123.1D Appendix G Table G-2 lists MCR success criteria including: "mission need is approved," "concept is feasible," "key risks identified." ECSS-M-ST-10C §6.2.2 (MDR) has similar criteria.
**Source:** NPR 7123.1D Appendix G; ECSS-M-ST-10C §6.2.2
**Confidence:** HIGH

#### 2. Review Outcomes (GO/NO-GO/GO with Actions)
**Claim:** Three possible outcomes from a gate review.
**Verification:** CONFIRMED. This is standard review practice per both NASA and ECSS. NPR 7120.5F §2.4.2 defines KDP outcomes as "proceed," "proceed with actions," or "no-proceed."
**Source:** NPR 7120.5F §2.4.2
**Confidence:** HIGH

### Session 5.2 Verifications

#### 3. ISED Service Standard: 126 Calendar Days
**Claim:** ISED processes space station spectrum licence applications within 126 calendar days.
**Verification:** CONFIRMED. ISED CPC-2-6-02 (Issue 6) states a service standard of 126 calendar days for space station spectrum licence applications.
**Source:** ISED CPC-2-6-02 Issue 6
**Confidence:** HIGH

#### 4. RSSSA Applies to Any Earth-Imaging Capability
**Claim:** No minimum GSD threshold for RSSSA applicability.
**Verification:** CONFIRMED. RSSSA (S.C. 2005, c. 45) §2 defines "remote sensing" broadly as "the sensing of the Earth's surface by means of the electromagnetic properties of emitted or reflected radiation." No resolution threshold is specified. A 1U CubeSat with a basic camera still triggers the requirement.
**Source:** RSSSA (S.C. 2005, c. 45) §2
**Confidence:** HIGH

#### 5. ITU Filing Timeline: 12-24 Months
**Claim:** Complete ITU coordination process takes 12-24 months.
**Verification:** CONFIRMED. ITU RR Article 9 defines the timeline: API processing (~2 months), comment period (4 months), coordination filing (no sooner than 4 months after API receipt), coordination period (6-24 months depending on complexity). Total: minimum 12 months, often 18-24 months.
**Source:** ITU Radio Regulations Article 9; ITU BR Coordination and Notification Procedures
**Confidence:** HIGH

### Session 5.3 Verifications

#### 6. Three-Inhibit Rule
**Claim:** CubeSats require 3 independent inhibits (2 deployment switches + 1 RBF pin).
**Verification:** CONFIRMED. CDS Rev 14.1 §3.1.4 requires minimum of 1 deployment switch that deactivates the satellite while in the deployer. Most deployer ICDs require 2 switches + 1 RBF for triple redundancy. ISIPOD IDD and NanoRacks NRCSD IDD both specify this requirement.
**Caveat:** CDS itself only requires 1 switch; the 3-inhibit requirement comes from deployer ICDs (ISIPOD, NRCSD, EXOpod). State "per deployer ICD" rather than "per CDS."
**Source:** CDS Rev 14.1 §3.1.4; NanoRacks NRCSD IDD §4.2; ISIPOD IDD
**Confidence:** HIGH (with deployer ICD attribution)

#### 7. Battery State at Delivery: ≤50% SoC
**Claim:** Batteries must be at ≤50% state of charge at delivery to integration facility.
**Verification:** CONFIRMED. Most launch provider ICDs require batteries to be in a "safe state" with SoC between 30-50% at delivery. SpaceX Rideshare PUG and NanoRacks NRCSD IDD both specify this. The exact limit varies by provider.
**Source:** SpaceX Rideshare PUG; NanoRacks NRCSD IDD §4.3
**Confidence:** HIGH

### Session 5.4 Verifications

#### 8. Pareto Optimality Definition
**Claim:** A Pareto-optimal design is one where no objective can be improved without worsening another.
**Verification:** CONFIRMED. This is the standard definition from multi-objective optimisation theory (Pareto, 1896). Also known as "Pareto efficiency" or "non-dominated" solutions.
**Source:** Deb, Multi-Objective Optimization Using Evolutionary Algorithms (2001) §2.2
**Confidence:** HIGH

#### 9. Morris Screening Method
**Claim:** Morris method uses elementary effects (μ* and σ) to rank variable importance.
**Verification:** CONFIRMED. Morris (1991) "Factorial Sampling Plans for Preliminary Computational Experiments" introduced the one-at-a-time (OAT) screening method. μ* (mean of absolute elementary effects) measures overall importance; σ (standard deviation) measures non-linearity/interaction effects. This is the standard interpretation.
**Source:** Morris (1991); Campolongo et al. (2007) "An effective screening design for sensitivity analysis of large models"
**Confidence:** HIGH

#### 10. NSGA-II Algorithm
**Claim:** SpaceCDF uses NSGA-II for multi-objective Pareto optimisation.
**Verification:** CONFIRMED. NSGA-II (Deb et al., 2002) uses non-dominated sorting and crowding distance for diversity preservation. The SpaceCDF implementation includes SBX crossover (η=20), polynomial mutation (η=20), and tournament selection — standard NSGA-II operators.
**Source:** Deb et al. (2002) "A fast and elitist multiobjective genetic algorithm: NSGA-II"
**Confidence:** HIGH

## Corrections Applied
1. Three-inhibit rule: attributed to deployer ICDs rather than CDS (CDS requires only 1 switch)
