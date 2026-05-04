# Verification Record — Day 4: Sessions 4.1-4.4

## Verification Date: 2026-05-04

### Session 4.1 Verifications

#### 1. PC/104 Impedance Standard
**Claim:** 50Ω standard impedance for RF chains.
**Verification:** CONFIRMED. CubeSat RF systems universally use 50Ω characteristic impedance for cables, connectors (SMA), and antenna/transponder ports. This is the standard per MIL-STD-348.
**Source:** MIL-STD-348 (RF connector standard); vendor datasheets
**Confidence:** HIGH

### Session 4.2 Verifications

#### 2. Verification vs Validation Definitions
**Claim:** Verification = "built right" (against requirements); Validation = "right system" (against needs).
**Verification:** CONFIRMED. NASA SEH §5.3: "Verification ensures that the product... conforms to its requirements." §5.4: "Validation ensures that the product... will fulfil its intended use." ECSS-E-ST-10-02C §4.1: similar definitions.
**Source:** NASA SEH §5.3, §5.4; ECSS-E-ST-10-02C §4.1
**Confidence:** HIGH

#### 3. Proto-flight Test Approach
**Claim:** CubeSats typically use proto-flight (single unit tested to qualification levels at acceptance duration).
**Verification:** CONFIRMED as standard CubeSat practice. Most CubeSat programmes cannot afford a separate qualification model. Proto-flight tests the actual flight unit at qualification temperature extremes but for acceptance (shorter) durations.
**Source:** ECSS-E-ST-10-03C §5.5.3; NASA GEVS (GSFC-STD-7000A §2.4)
**Confidence:** HIGH

#### 4. Random Vibration Level ~7 gRMS
**Claim:** Typical qualification random vibration for Falcon 9 rideshare is ~7 gRMS.
**Verification:** APPROXIMATELY CONFIRMED. SpaceX Rideshare PUG specifies maximum predicted environment (MPE); qualification level is MPE + 3 dB for random. Typical MPE for secondary payloads is 4-6 gRMS; qualification at 5.5-8.5 gRMS. The 7 gRMS figure is representative.
**Caveat:** Actual levels vary by deployer, location, and vehicle variant. Always use vehicle-specific PUG data.
**Source:** SpaceX Rideshare Payload User's Guide; Exolaunch EXOpod User Manual
**Confidence:** MEDIUM-HIGH (representative but vehicle-specific)

#### 5. TVAC Cycle Count: 4 Minimum
**Claim:** Minimum 4 thermal vacuum cycles for proto-flight.
**Verification:** CONFIRMED. ECSS-E-ST-10-03C §5.4.2 specifies minimum 4 cycles for qualification (proto-flight tests at qualification extremes). NASA GEVS specifies 8 cycles for proto-flight with abbreviated duration. For CubeSats, 4-8 cycles is standard practice.
**Source:** ECSS-E-ST-10-03C §5.4.2; NASA GSFC-STD-7000A §2.4
**Confidence:** HIGH

### Session 4.3 Verifications

#### 6. 5×5 Risk Matrix Structure
**Claim:** Standard 5-level likelihood × 5-level consequence matrix.
**Verification:** CONFIRMED. This is the standard risk matrix structure used by NASA (NPR 8000.4 §3.4), ESA (ECSS-M-ST-80C §5.3), and DoD (MIL-STD-882E). Exact definitions of levels vary by organisation but 5×5 is the standard grid.
**Source:** NPR 8000.4 §3.4; ECSS-M-ST-80C §5.3
**Confidence:** HIGH

#### 7. CubeSat Reliability and SPF
**Claim:** OBC, battery, and antenna are typical single-point failures for CubeSats.
**Verification:** CONFIRMED. Statistical analysis of CubeSat missions (Langer & Bouwmeester, 2016) identifies electrical power system, communication, and OBC as the three most common failure areas. Single-string architectures (one OBC, one battery) are standard for CubeSats due to mass/volume constraints.
**Source:** Langer & Bouwmeester, USU SmallSat 2016; Swartwout CubeSat mission database
**Confidence:** HIGH

### Session 4.4 Verifications

#### 8. CubeSat Cost Ranges
**Claim:** Professional 3U: $500K-2M; constellation per-unit: $750K-2.5M.
**Verification:** APPROXIMATELY CONFIRMED. Published data: Planet Dove constellation per-unit cost estimated at <$1M; Astrocast target <$1M/sat; MarCO (6U deep space) was $18.5M for two units ($9.25M each); ASTERIA (6U) estimated $5-15M. The range $500K-2M for professional 3U is reasonable.
**Source:** Planet Labs S-1 filing; Astrocast press releases; NASA MarCO cost data
**Confidence:** MEDIUM-HIGH (proprietary; ranges estimated from public data)

#### 9. Learning Curve: 90% Rate
**Claim:** 90% learning rate means each doubling reduces unit cost by 10%.
**Verification:** CONFIRMED by definition. Wright's learning curve: a "90% learning curve" means the cumulative average cost decreases to 90% of the previous level each time production quantity doubles. This is the standard definition.
Numerical check: b = ln(0.9)/ln(2) = -0.1520. Unit 2 cost = Unit 1 × 2^(-0.152) = Unit 1 × 0.9 = 90%. ✓
**Source:** SMAD4 §20.3; Wright (1936) "Factors Affecting the Cost of Airplanes"
**Confidence:** HIGH

#### 10. SpaceX Transporter Minimum Buy
**Claim:** $350K for up to 50 kg to SSO (2026 pricing).
**Verification:** CONFIRMED. SpaceX published rideshare pricing as of February 2026: $350,000 minimum for up to 50 kg; $7,000/kg above 50 kg. Previous pricing was $5,500/kg (2022).
**Source:** SpaceX website; NewSpaceEconomy.ca rideshare pricing analysis (Feb 2026)
**Confidence:** HIGH

#### 11. P80 ≈ P50 × 1.3 Rule of Thumb
**Claim:** P80 estimate is approximately 1.3× the P50 for CubeSat missions.
**Verification:** APPROXIMATELY CONFIRMED. For lognormal cost distributions with σ = 0.25 (moderate uncertainty), P80/P50 = e^(0.84×0.25) = e^0.21 = 1.23. For σ = 0.35 (higher uncertainty), P80/P50 = e^(0.84×0.35) = e^0.294 = 1.34. The 1.3× figure is a reasonable middle ground.
**Source:** Statistical derivation from lognormal; consistent with NASA CEH practice
**Confidence:** MEDIUM-HIGH (rule of thumb)

## Corrections Applied
1. Learning curve numerical example: corrected to use doubling rule rather than N^b formulation which is more complex. Both formulations taught but simplified version highlighted.
2. Random vibration: added caveat that levels are vehicle-specific; 7 gRMS is representative not universal.
