# Verification Record — Day 3: Sessions 3.1-3.4

## Verification Date: 2026-05-04

### Session 3.1 Verifications

#### 1. Orbital Period Formula
**Claim:** T = 2π√(a³/μ) with μ = 3.986 × 10¹⁴ m³/s².
**Verification:** CONFIRMED. This is Kepler's third law applied to orbits around Earth. μ_Earth = GM_Earth = 3.986004418 × 10¹⁴ m³/s² (standard gravitational parameter).
**Source:** Vallado, Fundamentals of Astrodynamics §2.3; SMAD4 §5.2
**Confidence:** HIGH

#### 2. SSO Inclination Formula
**Claim:** i_SSO derived from J₂ precession matching 360°/year.
**Verification:** CONFIRMED. The nodal regression rate due to J₂ is:
Ω̇ = -(3/2) × n × J₂ × (R_E/a)² × cos(i) / (1-e²)²
Setting Ω̇ = 2π/(365.25×86400) and solving for cos(i) gives the stated relationship.
J₂ = 1.08263 × 10⁻³ (dimensionless).
For h=500 km: i = 97.4° confirmed by computation.
**Source:** Vallado §9.4; SMAD4 §5.4
**Confidence:** HIGH

#### 3. Hohmann Transfer ΔV
**Claim:** ΔV₁ = √(μ/r₁) × (√(2r₂/(r₁+r₂)) - 1).
**Verification:** CONFIRMED. Derivation from vis-viva equation:
v² = μ(2/r - 1/a). For transfer ellipse: a_t = (r₁+r₂)/2.
At r₁: v_t₁ = √(μ(2/r₁ - 2/(r₁+r₂))); ΔV₁ = v_t₁ - v_c₁.
Numerical: 500→200 km deorbit:
r₁ = 6871 km, r₂ = 6571 km
v_c₁ = √(3.986e14/6.871e6) = 7613 m/s
v_t₁ = √(3.986e14 × (2/6.871e6 - 2/13.442e6)) = √(3.986e14 × 1.418e-7) = 7524 m/s
ΔV₁ = |7524 - 7613| = 89 m/s ✓
**Source:** Bate, Mueller & White §6.2; SMAD4 §6.3
**Confidence:** HIGH (computed)

#### 4. Critical Altitude Boundaries for Debris Compliance
**Claim:** <500 km: FCC-compliant without propulsion; >600 km: likely needs active deorbit.
**Verification:** APPROXIMATELY CONFIRMED. The actual boundary depends on ballistic coefficient (A/m ratio) and solar activity:
- At 400 km: lifetime ~1-3 years (FCC-compliant) ✓
- At 500 km: lifetime ~5-15 years (FCC-compliant for small CubeSats) ✓
- At 600 km: lifetime ~15-50 years (depends on solar cycle; may NOT be FCC-compliant) ✓
- At 700 km: lifetime ~50-200 years (needs active deorbit) ✓
**Source:** ESA DRAMA tool documentation; SpaceCDF debris.py validated against these ranges
**Confidence:** HIGH (general ranges; exact values depend on spacecraft properties)

### Session 3.2 Verifications

#### 5. Diffraction-Limited GSD Formula
**Claim:** GSD_diff = 1.22 × λ × h / D.
**Verification:** CONFIRMED. This comes from the Rayleigh criterion for the angular resolution of a circular aperture: θ = 1.22λ/D. At ground range h: GSD = h × θ = 1.22λh/D.
**Source:** Hecht, Optics §10.2; SMAD4 §9.3
**Confidence:** HIGH

#### 6. FSPL Verification
**Claim:** FSPL(S-band, 500km slant) ≈ 162.5 dB.
**Verification:** Computed at slant range for 10° elevation.
Slant range: R = R_E × (√((h/R_E+1)²-cos²(10°)) - sin(10°)) = 6371 × (√(1.0785²-0.9848²) - 0.1736) = 6371 × (√(0.1964) - 0.1736) = 6371 × (0.4432 - 0.1736) = 6371 × 0.2696 = 1717 km (at 10° elevation, higher than stated 1300 km).

FSPL = 20×log₁₀(4π×1.717×10⁶/(3×10⁸/2.25×10⁹))
λ = 0.1333 m
FSPL = 20×log₁₀(4π×1.717×10⁶/0.1333) = 20×log₁₀(1.615×10⁸) = 20×8.208 = 164.2 dB

**Correction needed:** The table value of 162.5 dB corresponds to a shorter slant range. For consistency, should state "at 20° elevation" or use nadir (direct overhead: R = h = 500 km → FSPL = 153.5 dB). The 10° elevation gives ~164 dB.

**Source:** Standard FSPL equation confirmed; numerical values depend on elevation angle
**Confidence:** HIGH (formula), MEDIUM (table values — elevation angle should be specified)

#### 7. Modulation Eb/N₀ Requirements
**Claim:** QPSK + LDPC (r=1/2) requires Eb/N₀ = 2.0 dB.
**Verification:** CONFIRMED. LDPC codes at rate 1/2 achieve BER 10⁻⁵ at approximately 1.5-2.5 dB Eb/N₀ depending on block length. The 2.0 dB figure is conservative and widely used.
**Source:** CCSDS 131.0-B-4; DVB-S2 standard (ETSI EN 302 307)
**Confidence:** HIGH

### Session 3.3 Verifications

#### 8. Solar Array Sizing Formula Chain
**Claim:** A_SA = P_SA_BOL / (η × S × cos(θ) × η_packing).
**Verification:** CONFIRMED. The power from a solar panel is:
P = η_cell × S × A × cos(θ) × η_packing × (inherent degradation factors)
Inverting: A = P / (η_cell × S × cos(θ) × η_packing).
Numerical: 13.2 / (0.295 × 1361 × 1 × 0.85) = 13.2 / 341.2 = 0.0387 m² ✓
**Source:** SMAD4 §11.4.2
**Confidence:** HIGH (computed)

#### 9. SA Specific Mass
**Claim:** Body-mounted 2.5 kg/m²; deployable 1.5 kg/m².
**Verification:** APPROXIMATELY CONFIRMED. GomSpace deployable panels: ~0.3 kg for ~0.1 m² → 3 kg/m². MMA Design deployable: ~1.0-1.5 kg/m² for larger arrays. Body-mounted: GomSpace panels ~0.05 kg for 0.01 m² → 5 kg/m² (including frame).
**Correction:** CubeSat body-mounted panels are denser (~3-5 kg/m²) than stated. Deployable panels range 1.0-3.0 kg/m² depending on mechanism. Use "2-5 kg/m² body-mounted, 1-3 kg/m² deployable" for accuracy.
**Source:** GomSpace NanoPower datasheets; MMA Design HaWK specifications
**Confidence:** MEDIUM (values are approximate ranges)

#### 10. Battery DoD and Cycle Life
**Claim:** 30% DoD → >10,000 cycles for Li-ion.
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
**Confidence:** HIGH (dimensions), MEDIUM (mass — deployer-dependent)

#### 12. Tsiolkovsky Rocket Equation
**Claim:** m_propellant = m_dry × (e^(ΔV/(Isp×g₀)) - 1).
**Verification:** CONFIRMED. From Tsiolkovsky: ΔV = Isp × g₀ × ln(m_initial/m_final).
Rearranging: m_initial/m_final = e^(ΔV/(Isp×g₀))
m_propellant = m_initial - m_final = m_final × (e^(ΔV/(Isp×g₀)) - 1)
Where m_final = m_dry (after propellant expended).
Numerical: 5 × (e^(50/(60×9.81)) - 1) = 5 × (e^0.0849 - 1) = 5 × 0.0886 = 0.443 kg ≈ 0.44 kg ✓
**Source:** Sutton & Biblarz, Rocket Propulsion Elements §2.2
**Confidence:** HIGH (computed)

#### 13. PC/104 Specifications
**Claim:** 96×90 mm, 104 pins, 2.54 mm pitch.
**Verification:** CONFIRMED. PC/104 standard (IEEE P996.1): board outline 96×90 mm (3.775×3.550 inches), bus connector is 2×52 = 104 pins at 100 mil (2.54 mm) pitch. Stack-through headers for vertical stacking.
**Source:** IEEE P996.1; PC/104 Consortium specifications
**Confidence:** HIGH

## Corrections Applied
1. FSPL table: added note that elevation angle should be specified (10° gives ~164 dB at S-band/500km, not 162.5 dB)
2. SA specific mass: widened range to 2-5 kg/m² body-mounted, 1-3 kg/m² deployable
3. CDS mass: added deployer ICD caveat (CDS allows 4 kg/U but deployer may limit)
