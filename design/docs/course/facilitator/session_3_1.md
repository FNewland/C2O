# Session 3.1: Orbit Design & Selection

**Duration:** 2 hours
**Prerequisites:** Day 2 complete (requirements and budgets understood)
**References:** SMAD4 Ch.5-7; Vallado, Fundamentals of Astrodynamics; ECSS-U-AS-10C Rev.2

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe Keplerian orbital elements and their physical meaning
2. Compute orbital period, velocity, and eclipse fraction
3. Evaluate trade-offs between orbit altitude, coverage, lifetime, and radiation
4. Apply debris compliance rules (25-year IADC, 5-year FCC) to orbit selection
5. Use SpaceCDF's orbit trade advisor with mission-type-appropriate scoring

---

## 1. Orbital Mechanics Fundamentals (30 min)

### Teaching Notes

### Keplerian Elements

Six parameters fully describe a satellite's orbit:

| Element | Symbol | Description | Typical Range |
|---------|--------|-------------|---------------|
| Semi-major axis | *a* | Size of the orbit (km) | 6671-42164 km (LEO-GEO) |
| Eccentricity | *e* | Shape (0 = circle, <1 = ellipse) | 0-0.001 for LEO |
| Inclination | *i* | Tilt of orbit plane from equator (°) | 0-180° |
| RAAN | *Ω* | Orientation of ascending node (°) | 0-360° |
| Argument of perigee | *ω* | Orientation of ellipse in orbit plane (°) | 0-360° |
| True anomaly | *ν* | Position of satellite in orbit (°) | 0-360° |

For circular LEO, the key parameters reduce to: **altitude** (*h*), **inclination** (*i*), and **LTAN** (local time of ascending node for SSO).

### Key Formulae

**Orbital period:**
```
T = 2π √(a³/μ)
```
Where *a* = R_E + h (semi-major axis), μ = 3.986 × 10¹⁴ m³/s² (Earth gravitational parameter).

*Example: h = 500 km → a = 6871 km → T = 5693 s = 94.9 min*

**Orbital velocity (circular):**
```
v = √(μ/a)
```
*Example: h = 500 km → v = 7613 m/s = 7.61 km/s*

**Eclipse fraction** (maximum, circular orbit):
```
f_eclipse = (1/π) × arccos(√(1 - (R_E/a)²))
```
*Example: h = 500 km → f = 0.376 = 37.6% maximum*

*[Verified: T computed = 94.9 min ✓; f computed = 37.6% ✓ — see Session 1.4 verification]*

**Sun-synchronous inclination** (J₂ precession = 360°/year):
```
cos(i) = -a^(7/2) × Ω̇_req / (1.5 × R_E² × J₂ × √μ)
```
Where J₂ = 1.0826 × 10⁻³, Ω̇_req = 2π / (365.25 × 86400) rad/s.

*Example: h = 500 km → i = 97.4°*

**Hohmann transfer ΔV** (circular to circular):
```
ΔV₁ = √(μ/r₁) × (√(2r₂/(r₁+r₂)) - 1)
ΔV₂ = √(μ/r₂) × (1 - √(2r₁/(r₁+r₂)))
ΔV_total = |ΔV₁| + |ΔV₂|
```
*Example: 500 km → 200 km deorbit: ΔV = 89 m/s*

### Ground Track and Revisit

**Swath width** for nadir-pointing sensor with half-angle *θ*:
```
Swath = 2h × tan(θ)
```

**Revisit time** depends on number of ground tracks that cover a latitude band. For a single satellite in SSO:
- 400 km, 20° swath: ~7 day revisit at equator
- 500 km, 20° swath: ~5 day revisit at equator
- Constellation of N satellites: revisit ≈ single/N (approximately)

---

## 2. Orbit Selection Trade-Offs (25 min)

### Teaching Notes

The orbit is the single most impactful early design decision. It affects nearly every subsystem:

| Parameter | Lower Altitude (300-400 km) | Higher Altitude (600-800 km) |
|-----------|---------------------------|------------------------------|
| **GSD** | Better (shorter range) | Worse (longer range) |
| **Lifetime** | Short (1-5 years natural) | Long (25-100+ years) |
| **Debris compliance** | Easy (natural deorbit) | May need propulsion |
| **Radiation** | Lower | Approaching Van Allen protraps |
| **Launch cost** | Lower | Slightly higher |
| **Link budget** | Better (shorter range) | Worse |
| **Coverage** | Narrower swath per pass | Wider swath per pass |
| **Drag** | Significant | Negligible above ~700 km |
| **Eclipse fraction** | ~35-38% | ~33-35% |

### Orbit Types and Applications

| Orbit | Altitude | Inclination | Best For |
|-------|----------|-------------|----------|
| **LEO (non-SSO)** | 300-600 km | Any | Technology demos, ISS deploy |
| **SSO** | 400-800 km | 97-99° | Earth observation (consistent lighting) |
| **ISS orbit** | 410 km | 51.6° | CubeSat deployment from NanoRacks |
| **MEO** | 2000-20200 km | Various | Navigation (GPS), comms |
| **GEO** | 35786 km | 0° | Communications, weather |
| **HEO (Molniya)** | 500-40000 km | 63.4° | High-latitude coverage |
| **NRHO** | 1500-70000 km | Lunar | Lunar gateway, cislunar ops |

### Debris Compliance Rules

| Rule | Requirement | Applies To |
|------|------------|-----------|
| **IADC guideline** | Post-mission lifetime ≤ 25 years | International (voluntary but expected) |
| **FCC rule (2024+)** | Post-mission lifetime ≤ 5 years | All FCC-licensed satellites in LEO |
| **ECSS-U-AS-10C** | Compliance with IADC + additional ESA requirements | ESA missions |
| **ISED (Canada)** | Currently 25-year rule; tightening under review | Canadian-licensed satellites |

**Critical altitude boundaries:**
- < 500 km: Natural deorbit within ~5-15 years (FCC-compliant without propulsion)
- 500-600 km: Natural deorbit ~10-40 years (may need drag augmentation for FCC)
- > 600 km: Likely needs active deorbit (propulsion or drag sail)
- > 700 km: ESA Zero Debris zone — additional scrutiny

*[Source: IADC-02-01 Rev 3 (2021) §5.3.2; FCC 22-74; ECSS-U-AS-10C Rev.2]*

---

## 3. Radiation Environment (15 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-04C Rev.1; SMAD4 §8.1]*

### Van Allen Radiation Belts

| Belt | Altitude | Particle | Impact on CubeSats |
|------|----------|----------|-------------------|
| **Inner** | 1000-6000 km | Protons | Most damaging; avoid for CubeSats |
| **Slot** | 6000-13000 km | Low flux | Relatively benign |
| **Outer** | 13000-60000 km | Electrons | Charging, some dose |
| **SAA** | 200-600 km at Brazil | Trapped protons | Single-event effects |

### Total Ionising Dose (TID) by Orbit

| Orbit | TID (krad/year) | Electronics Class |
|-------|-----------------|-------------------|
| ISS (410 km, 51.6°) | 2-5 | Commercial OK |
| SSO 500 km | 5-10 | Commercial / rad-tolerant |
| SSO 800 km | 10-20 | Rad-tolerant recommended |
| MEO 2000 km | 50-100 | Rad-hard required |
| GEO | 10-20 | Rad-hard required |

**Rule of thumb:** Below 600 km in LEO, commercial COTS electronics survive 3-year missions with modest shielding (2-3 mm Al equivalent). Above 600 km, radiation becomes a significant design driver.

---

## 4. SpaceCDF Orbit Trade Exercise (35 min)

### Instructions

1. Navigate to **Step 3 (Requirements)** → **Orbit Trade Advisor**
2. Enter your mission parameters:
   - GSD target (optical missions) or leave default for non-optical
   - Revisit target (days)
   - Lifetime (years)
   - Latitude band of interest
   - Maximum cost (MEUR)
   - Aperture (if optical)
3. Click **"Compute Orbit Trade"**
4. Review the scored candidates:
   - Which orbit scores highest?
   - Is it debris-compliant (5-year rule)?
   - What is the natural lifetime?
5. Click **"Use"** on your preferred orbit to populate the design parameters
6. Verify the orbit fields updated (check for "Set from advisor" badge)

### Discussion Points

- Does the best-scoring orbit match your intuition?
- What happens if you change the weights (GSD more important vs cost)?
- For non-optical missions, does the scoring still make sense?
- If your orbit is above 600 km, how will you handle deorbit?

---

## 5. Link to Downstream Design (15 min)

### Teaching Notes

The orbit selection cascades to every subsystem:

| Orbit Parameter | Affects | How |
|----------------|---------|-----|
| Altitude | Payload GSD, link range, eclipse fraction, lifetime | Lower = better GSD but shorter life |
| Inclination | Coverage latitude band, SSO lighting | Higher = polar coverage; SSO = consistent sun |
| Period | Contact time per pass, power cycling, thermal cycling | ~90-100 min for LEO |
| Eclipse fraction | Battery sizing, thermal cold case | 33-38% for LEO |
| Lifetime | Debris compliance, propulsion need | <5yr orbit avoids FCC propulsion need |
| Radiation | Electronics class, shielding mass | Higher orbit = more shielding |

After selecting an orbit, the design loop will re-converge all subsystems based on the new parameters. This is why the orbit trade is done early — it's the highest-leverage decision.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Keplerian elements | 6 parameters define the orbit; key for LEO: altitude + inclination |
| Key formulae | T = 2π√(a³/μ); v = √(μ/a); eclipse fraction from geometry |
| Trade-offs | Lower altitude = better GSD/link but shorter lifetime |
| Debris rules | FCC 5-year, IADC 25-year; above 600 km needs active deorbit |
| Radiation | Below 600 km: COTS OK; above: rad-tolerant/hard needed |
| Cascade | Orbit choice affects every subsystem — highest-leverage decision |
