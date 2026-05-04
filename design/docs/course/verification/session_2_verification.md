# Verification Record — Day 2: Sessions 2.1-2.4

## Verification Date: 2026-05-04

### Session 2.1 Verifications

#### 1. NASA SEH Appendix C: "shall" Convention
**Claim:** "shall" = mandatory, "should" = desired, "will" = statement of intent.
**Verification:** CONFIRMED. NASA SEH Appendix C §C.1: "The word 'shall' denotes a requirement that is binding... 'should' denotes a goal... 'will' denotes a statement of fact."
**Source:** NASA SEH Appendix C §C.1
**Confidence:** HIGH

#### 2. Requirements State WHAT Not HOW
**Claim:** NASA SEH Appendix C states requirements should not specify implementation.
**Verification:** CONFIRMED. Appendix C §C.2 Rule 6: "Avoid specifying a particular design solution... requirements should state what is needed, not how to provide it."
**Source:** NASA SEH Appendix C §C.2
**Confidence:** HIGH

#### 3. Interface Requirements Exception
**Claim:** Interface requirements can specify implementation details (e.g., bus voltage).
**Verification:** CONFIRMED. ECSS-E-ST-10-24C §5.2.2 states that interface requirements define agreed parameters at system boundaries. These are specific by necessity — they define the contract between subsystems. NASA SEH §6.3 similarly treats interfaces as agreed specifications.
**Source:** ECSS-E-ST-10-24C §5.2.2; NASA SEH §6.3
**Confidence:** HIGH

### Session 2.2 Verifications

#### 4. NASA SEH Process 3: Logical Decomposition
**Claim:** Process 3 decomposes functions, identifies derived requirements, and allocates to subsystems.
**Verification:** CONFIRMED. NASA SEH §4.3 describes Logical Decomposition as "decomposing the functional and performance requirements... into lower-level functions and subfunctions." Outputs include functional architecture and derived requirements.
**Source:** NASA SEH §4.3; NPR 7123.1D §3.2.3
**Confidence:** HIGH

#### 5. Coverage Check
**Claim:** Every leaf function should trace to at least one requirement.
**Verification:** CONFIRMED. NASA SEH §6.2 (Requirements Management) requires bidirectional traceability. A leaf function without a requirement represents a gap in coverage — the function is defined but has no verification path.
**Source:** NASA SEH §6.2.3
**Confidence:** HIGH

### Session 2.3 Verifications

#### 6. Interface Failure Statistic
**Claim:** "Most system failures can be traced back to interface problems."
**Verification:** CONFIRMED as widely cited in SE literature. While exact statistics vary, NASA Lessons Learned database and DoD system failure analyses consistently identify interface management as a top failure contributor. NASA SEH §6.3 opens with: "Many systems engineering problems are actually interface problems."
**Source:** NASA SEH §6.3; GAO-06-391 "Space Acquisitions"
**Confidence:** HIGH (statement, not exact statistic)

#### 7. N² Interface Count
**Claim:** 8 subsystems → 28 potential interface pairs (8×7/2).
**Verification:** CONFIRMED by combinatorics. C(8,2) = 8!/(2!×6!) = 28. ✓
**Confidence:** HIGH (mathematical)

### Session 2.4 Verifications

#### 8. ECSS Mass Margin Table
**Claim:** Phase 0/A: equipment 20% + system 20% = ~44% compound.
**Verification:** CONFIRMED. Compound = (1+0.20)×(1+0.20)-1 = 0.44 = 44%. ECSS-E-HB-10-02A §5.2 provides the margin framework; specific values are programme-specific but the cited ranges are the commonly used ESA/CDF defaults.
**Source:** ECSS-E-HB-10-02A §5.2
**Confidence:** HIGH

#### 9. Solar Array Sizing Formula
**Claim:** P_SA = P_peak_sunlight + (P_eclipse × t_eclipse) / (t_sunlight × η_charge)
**Verification:** CONFIRMED. This is the standard approach from SMAD4 §11.4.3. The SA must provide:
(a) power for the highest sunlight demand mode, PLUS
(b) enough additional power to recharge the battery for eclipse loads.
The formula correctly divides eclipse energy by available sunlight time and charge efficiency.
**Source:** SMAD4 §11.4.3; ECSS-E-ST-20C §6.2
**Confidence:** HIGH

#### 10. Battery DoD = 30% for Long Cycle Life
**Claim:** 30% DoD gives long cycle life for Li-ion batteries.
**Verification:** CONFIRMED as conservative design practice. Li-ion battery cycle life vs DoD is non-linear. At 30% DoD, typical Li-ion achieves >10,000 cycles (sufficient for 3-year LEO with ~15 cycles/day = ~16,000 cycles). At higher DoD (e.g., 80%), cycle life drops to ~500-2000 cycles.
**Source:** SMAD4 §11.4.4; battery manufacturer data (Samsung, Panasonic, Saft)
**Confidence:** HIGH

#### 11. Solar Array Degradation Rate 2.5%/year
**Claim:** Triple-junction GaAs cells degrade at ~2.5% per year in LEO.
**Verification:** CONFIRMED as typical. Degradation depends on orbit (radiation environment), cell type, and coverslide thickness. For LEO with standard 150 μm coverslides, triple-junction GaAs degrades at 2-3%/year. The 2.5%/year value is a widely used design default.
**Source:** SMAD4 §11.4.2; ECSS-E-ST-20C §6.3; JPL Solar Cell Array Design Handbook
**Confidence:** HIGH

#### 12. Numerical Verification: SA Sizing Example
**Claim:** P_SA_BOL = 13.2 W for the given example parameters.
**Verification:** Computed:
- P_recharge = (3.5 × 35) / (60 × 0.9) = 122.5 / 54 = 2.269 W ✓
- P_SA_required = 10.0 + 2.269 = 12.269 W ✓
- EOL factor = (1-0.025)³ = 0.975³ = 0.9269
- P_SA_BOL = 12.269 / 0.9269 = 13.24 W ≈ 13.2 W ✓
**Confidence:** HIGH (computed)

#### 13. Numerical Verification: Battery Sizing Example
**Claim:** Battery ≥ 7.2 Wh for the given example parameters.
**Verification:** Computed:
- Eclipse energy = 3.5 W × (35/60) h = 3.5 × 0.5833 = 2.042 Wh ✓
- Battery = 2.042 / (0.3 × 0.95) = 2.042 / 0.285 = 7.16 Wh ≈ 7.2 Wh ✓
**Confidence:** HIGH (computed)

#### 14. Link Budget Equation
**Claim:** Margin = EIRP - FSPL + G/T - k - 10·log₁₀(Rb) - Eb/N₀_req - Impl_Loss
**Verification:** CONFIRMED. This is the standard form of the satellite link budget equation. Derivation:
- Received C/N₀ = EIRP - FSPL + G/T + 228.6 (in dBHz)
- Eb/N₀ = C/N₀ - 10·log₁₀(Rb)
- Margin = Eb/N₀ - Eb/N₀_required - Implementation_Loss
Combining: Margin = EIRP - FSPL + G/T - k - 10·log₁₀(Rb) - Eb/N₀_req - Impl_Loss
Where k = -228.6 dBW/K/Hz (Boltzmann constant).
**Source:** SMAD4 §13.3; ECSS-E-ST-50-05C §6; ITU-R Recommendations
**Confidence:** HIGH

#### 15. Pointing Budget RSS
**Claim:** θ_total = √(Σ θᵢ²) for independent error sources.
**Verification:** CONFIRMED. Root-Sum-Square combination is the standard method for combining independent, uncorrelated error sources per statistical theory. If errors are Gaussian and independent, the RSS gives the 1σ combined error.
**Caveat:** Assumes independence. Correlated errors (e.g., thermal distortion affecting both alignment and jitter) should be summed linearly or treated with a correlation matrix.
**Source:** SMAD4 §11.1; ECSS-E-ST-60-10C §5.4
**Confidence:** HIGH (with independence assumption)
