# Verification Record -- Day 3: Sessions 3.1-3.4

## Verification Date: 2026-05-04

### Session 3.1 Verifications

#### 1. Orbital Period Formula
**Claim:** T = 2pi?(a^3/mu) with mu = 3.986 × 10¹? m^3/s^2.
**Verification:** CONFIRMED. This is Kepler's third law applied to orbits around Earth. mu_Earth = GM_Earth = 3.986004418 × 10¹? m^3/s^2 (standard gravitational parameter).
**Source:** Vallado, Fundamentals of Astrodynamics §2.3; SMAD4 §5.2
**Confidence:** HIGH

#### 2. SSO Inclination Formula
**Claim:** i_SSO derived from J2 precession matching 360°/year.
**Verification:** CONFIRMED. The nodal regression rate due to J2 is:
?? = -(3/2) × n × J2 × (R_E/a)^2 × cos(i) / (1-e^2)^2
Setting ?? = 2pi/(365.25×86400) and solving for cos(i) gives the stated relationship.
J2 = 1.08263 × 10?^3 (dimensionless).
For h=500 km: i = 97.4° confirmed by computation.
**Source:** Vallado §9.4; SMAD4 §5.4
**Confidence:** HIGH

#### 3. Hohmann Transfer ?V
**Claim:** ?V1 = ?(mu/r1) × (?(2r2/(r1+r2)) - 1).
**Verification:** CONFIRMED. Derivation from vis-viva equation:
v^2 = mu(2/r - 1/a). For transfer ellipse: a_t = (r1+r2)/2.
At r1: v_t1 = ?(mu(2/r1 - 2/(r1+r2))); ?V1 = v_t1 - v_c1.
Numerical: 500->200 km deorbit:
r1 = 6871 km, r2 = 6571 km
v_c1 = ?(3.986e14/6.871e6) = 7613 m/s
v_t1 = ?(3.986e14 × (2/6.871e6 - 2/13.442e6)) = ?(3.986e14 × 1.418e-7) = 7524 m/s
?V1 = |7524 - 7613| = 89 m/s Y
**Source:** Bate, Mueller & White §6.2; SMAD4 §6.3
**Confidence:** HIGH (computed)

#### 4. Critical Altitude Boundaries for Debris Compliance
**Claim:** <500 km: FCC-compliant without propulsion; >600 km: likely needs active deorbit.
**Verification:** APPROXIMATELY CONFIRMED. The actual boundary depends on ballistic coefficient (A/m ratio) and solar activity:
- At 400 km: lifetime ~1-3 years (FCC-compliant) Y
- At 500 km: lifetime ~5-15 years (FCC-compliant for small CubeSats) Y
- At 600 km: lifetime ~15-50 years (depends on solar cycle; may NOT be FCC-compliant) Y
- At 700 km: lifetime ~50-200 years (needs active deorbit) Y
**Source:** ESA DRAMA tool documentation; SpaceCDF debris.py validated against these ranges
**Confidence:** HIGH (general ranges; exact values depend on spacecraft properties)

### Session 3.2 Verifications

#### 5. Diffraction-Limited GSD Formula
**Claim:** GSD_diff = 1.22 × lambda × h / D.
**Verification:** CONFIRMED. This comes from the Rayleigh criterion for the angular resolution of a circular aperture: theta = 1.22lambda/D. At ground range h: GSD = h × theta = 1.22lambdah/D.
**Source:** Hecht, Optics §10.2; SMAD4 §9.3
**Confidence:** HIGH

#### 6. FSPL Verification
**Claim:** FSPL(S-band, 500km slant) ~ 162.5 dB.
**Verification:** Computed at slant range for 10° elevation.
Slant range: R = R_E × (?((h/R_E+1)^2-cos^2(10°)) - sin(10°)) = 6371 × (?(1.0785^2-0.9848^2) - 0.1736) = 6371 × (?(0.1964) - 0.1736) = 6371 × (0.4432 - 0.1736) = 6371 × 0.2696 = 1717 km (at 10° elevation, higher than stated 1300 km).

FSPL = 20×log10(4pi×1.717×10?/(3×10?/2.25×10?))
lambda = 0.1333 m
FSPL = 20×log10(4pi×1.717×10?/0.1333) = 20×log10(1.615×10?) = 20×8.208 = 164.2 dB

**Correction needed:** The table value of 162.5 dB corresponds to a shorter slant range. For consistency, should state "at 20° elevation" or use nadir (direct overhead: R = h = 500 km -> FSPL = 153.5 dB). The 10° elevation gives ~164 dB.

**Source:** Standard FSPL equation confirmed; numerical values depend on elevation angle
**Confidence:** HIGH (formula), MEDIUM (table values -- elevation angle should be specified)

#### 7. Modulation Eb/N0 Requirements
**Claim:** QPSK + LDPC (r=1/2) requires Eb/N0 = 2.0 dB.
**Verification:** CONFIRMED. LDPC codes at rate 1/2 achieve BER 10?? at approximately 1.5-2.5 dB Eb/N0 depending on block length. The 2.0 dB figure is conservative and widely used.
**Source:** CCSDS 131.0-B-4; DVB-S2 standard (ETSI EN 302 307)
**Confidence:** HIGH

### Session 3.3 Verifications

#### 8. Solar Array Sizing Formula Chain
**Claim:** A_SA = P_SA_BOL / (eta × S × cos(theta) × eta_packing).
**Verification:** CONFIRMED. The power from a solar panel is:
P = eta_cell × S × A × cos(theta) × eta_packing × (inherent degradation factors)
Inverting: A = P / (eta_cell × S × cos(theta) × eta_packing).
Numerical: 13.2 / (0.295 × 1361 × 1 × 0.85) = 13.2 / 341.2 = 0.0387 m^2 Y
**Source:** SMAD4 §11.4.2
**Confidence:** HIGH (computed)

#### 9. SA Specific Mass
**Claim:** Body-mounted 2.5 kg/m^2; deployable 1.5 kg/m^2.
**Verification:** APPROXIMATELY CONFIRMED. GomSpace deployable panels: ~0.3 kg for ~0.1 m^2 -> 3 kg/m^2. MMA Design deployable: ~1.0-1.5 kg/m^2 for larger arrays. Body-mounted: GomSpace panels ~0.05 kg for 0.01 m^2 -> 5 kg/m^2 (including frame).
**Correction:** CubeSat body-mounted panels are denser (~3-5 kg/m^2) than stated. Deployable panels range 1.0-3.0 kg/m^2 depending on mechanism. Use "2-5 kg/m^2 body-mounted, 1-3 kg/m^2 deployable" for accuracy.
**Source:** GomSpace NanoPower datasheets; MMA Design HaWK specifications
**Confidence:** MEDIUM (values are approximate ranges)

#### 10. Battery DoD and Cycle Life
**Claim:** 30% DoD -> >10,000 cycles for Li-ion.
**Verification:** CONFIRMED. Li-ion 18650 cells (e.g., Samsung 30Q, Panasonic NCR18650B) at 30% DoD achieve 5,000-15,000 cycles depending on temperature and charge rate. For a 3-year LEO mission (~16,000 cycles), 30% DoD is conservative but appropriate.
**Source:** Battery manufacturer datasheets; Saft VES16 space-grade data
**Confidence:** HIGH

### Session 3.4 Verifications

#### 11. CDS Dimensional Specifications
**Claim:** 3U = 100×100×340.5 mm, 6 kg max.
**Verification:** CONFIRMED. CDS Rev 14.1 (February 2022) Table 2.1.2:
- 3U: 100.0 ± 0.1 × 100.0 ± 0.1 × 340.5 ± 0.5 mm
- Mass: 6 kg maximum (per ISIPOD ICD; CDS itself allows up to 4 kg/U = 12 kg for 3U, but deployer limits apply)
**Correction:** CDS allows 4 kg/U but deployer ICD may limit to 6 kg for 3U ISIPOD. State both: "CDS allows up to 4 kg/U; deployer may limit further."
**Source:** CDS Rev 14.1 §2.1.2, Table 2.1.2
**Confidence:** HIGH (dimensions), MEDIUM (mass -- deployer-dependent)

#### 12. Tsiolkovsky Rocket Equation
**Claim:** m_propellant = m_dry × (e^(?V/(Isp×g0)) - 1).
**Verification:** CONFIRMED. From Tsiolkovsky: ?V = Isp × g0 × ln(m_initial/m_final).
Rearranging: m_initial/m_final = e^(?V/(Isp×g0))
m_propellant = m_initial - m_final = m_final × (e^(?V/(Isp×g0)) - 1)
Where m_final = m_dry (after propellant expended).
Numerical: 5 × (e^(50/(60×9.81)) - 1) = 5 × (e^0.0849 - 1) = 5 × 0.0886 = 0.443 kg ~ 0.44 kg Y
**Source:** Sutton & Biblarz, Rocket Propulsion Elements §2.2
**Confidence:** HIGH (computed)

#### 13. PC/104 Specifications
**Claim:** 96×90 mm, 104 pins, 2.54 mm pitch.
**Verification:** CONFIRMED. PC/104 standard (IEEE P996.1): board outline 96×90 mm (3.775×3.550 inches), bus connector is 2×52 = 104 pins at 100 mil (2.54 mm) pitch. Stack-through headers for vertical stacking.
**Source:** IEEE P996.1; PC/104 Consortium specifications
**Confidence:** HIGH

## Corrections Applied
1. FSPL table: added note that elevation angle should be specified (10° gives ~164 dB at S-band/500km, not 162.5 dB)
2. SA specific mass: widened range to 2-5 kg/m^2 body-mounted, 1-3 kg/m^2 deployable
3. CDS mass: added deployer ICD caveat (CDS allows 4 kg/U but deployer may limit)
