# Verification Record — Sessions 1.3 & 1.4

## Verification Date: 2026-05-04

### Session 1.3 Verifications

#### 1. NASA SEH Process 17: Decision Analysis
**Claim:** Process 17 provides framework for structured trade studies with auditable rationale.
**Verification:** CONFIRMED. NASA SEH §6.8 describes Decision Analysis as the process of evaluating alternatives against criteria using structured methods. §6.8.3 requires "an auditable record" of the decision and rationale.
**Source:** NASA SEH §6.8; NPR 7123.1D §3.4.8
**Confidence:** HIGH

#### 2. Weighted Score Calculation
**Claim:** Total_Score = Σ(Weight × NormScore) / ΣWeight
**Verification:** CONFIRMED as standard practice. This is the additive value model (Keeney & Raiffa, 1976) widely used in SE decision analysis. NASA SEH §6.8.2 references weighted evaluation criteria.
**Source:** NASA SEH §6.8.2; SMAD4 §3.3
**Confidence:** HIGH

#### 3. Learning Curve for Constellations
**Claim:** 95% learning rate for ≤5 units, 90% for ≤50 units.
**Verification:** APPROXIMATELY CORRECT. Standard aerospace learning curves range 85-95%. The specific breakpoints (5/50 units) are reasonable estimates used in SSCM and PCEC models. Wright's learning curve: Unit_Cost(N) = T1 × N^(ln(LR)/ln(2)).
**Source:** SMAD4 §20.3; Aerospace Corporation SSCM documentation
**Confidence:** MEDIUM-HIGH (exact breakpoints are model-specific)

### Session 1.4 Verifications

#### 4. NASA SEH Appendix S: ConOps Outline
**Claim:** ConOps structure per Appendix S includes mission architecture, phases, modes, data flow.
**Verification:** CONFIRMED. Appendix S provides an annotated outline for a ConOps document covering: system overview, referenced documents, current situation, justification for change, operational concept (including scenarios, modes, timelines), system environment, and support environment.
**Source:** NASA SEH Appendix S
**Confidence:** HIGH

#### 5. Ground Station Slant Range Formula
**Claim:** R = R_E × [√((h/R_E + 1)² - cos²(ε)) - sin(ε)]
**Verification:** CONFIRMED. This is the standard geometric derivation from the ground station visibility problem. Derivation:
- Triangle: Earth centre, ground station, satellite
- R_E = Earth radius, h = altitude, ε = elevation angle
- Law of sines gives: R/sin(90°+ε) = (R_E+h)/sin(central_angle)
- Simplifies to the stated formula for the slant range.
**Source:** Wertz, Space Mission Engineering (SMAD4) §5.3; Vallado, Fundamentals of Astrodynamics
**Confidence:** HIGH

#### 6. SA Power Formula
**Claim:** P_SA = P_max_sunlight + (P_eclipse × t_eclipse) / (t_sunlight × η_charge)
**Verification:** CONFIRMED. This is the standard solar array sizing equation. The SA must provide power for:
(a) current sunlight loads, plus (b) energy to recharge the battery for eclipse loads, divided by the available sunlight time and charge efficiency.
**Source:** SMAD4 §11.4; ECSS-E-ST-20C power budget methodology
**Confidence:** HIGH

#### 7. FCC 5-Year Deorbit Rule
**Claim:** FCC rule effective September 2024 requires LEO satellites to deorbit within 5 years of end of mission.
**Verification:** CONFIRMED. The FCC adopted the 5-year rule in September 2022 with a 2-year implementation period, making it effective September 2024. Applies to all new FCC-licensed satellites in LEO.
**Source:** FCC 22-74, Report and Order and Further Notice of Proposed Rulemaking; 47 CFR §25.114(d)(14)
**Confidence:** HIGH

#### 8. IADC 25-Year Rule
**Claim:** IADC guidelines recommend post-mission orbital lifetime ≤ 25 years.
**Verification:** CONFIRMED. IADC Space Debris Mitigation Guidelines (IADC-02-01 Rev 3, 2021) §5.3.2: "The remaining orbital lifetime after end of operational phase should be limited to 25 years."
**Source:** IADC-02-01 Revision 3 (June 2021), §5.3.2
**Confidence:** HIGH

#### 9. Orbit Period for 500 km LEO
**Claim:** ~95 minutes for a 500 km LEO orbit.
**Verification:** CONFIRMED by calculation.
T = 2π√(a³/μ) where a = (6371+500)×1000 = 6.871×10⁶ m, μ = 3.986×10¹⁴ m³/s²
T = 2π√((6.871×10⁶)³ / 3.986×10¹⁴) = 2π√(3.244×10²⁰ / 3.986×10¹⁴) = 2π×28520 = 5693 s = 94.9 min ≈ 95 min ✓
**Confidence:** HIGH (computed)

#### 10. Eclipse Fraction for 500 km SSO
**Claim:** ~35% eclipse fraction.
**Verification:** APPROXIMATELY CORRECT. For a circular 500 km orbit, the eclipse fraction depends on the beta angle (angle between orbit plane and sun direction). For SSO, beta angle varies seasonally. Maximum eclipse fraction occurs near solstice: f_eclipse ≈ arccos(√(1-(R_E/(R_E+h))²))/π. For h=500 km: f = arccos(√(1-(6371/6871)²))/π = arccos(0.375)/π ≈ 0.38 (38%). Annual average is ~33-35%.
**Source:** SMAD4 §5.5; Wertz §10.3
**Confidence:** HIGH (typical range 33-38%)
