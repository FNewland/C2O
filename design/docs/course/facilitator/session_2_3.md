# Session 2.3: Orbit Selection and Mission Architecture


**Prerequisites:** Sessions 2.1--2.2 (requirements and functions defined)
**SpaceCDF Tabs:** Mission Architecture, Orbit Trade Advisor

---

## References

- [Vallado, *Fundamentals of Astrodynamics and Applications*, 4th ed., 2013, Ch. 2--6](https://www.amazon.com/Fundamentals-Astrodynamics-Applications-Technology-Library/dp/1881883183)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 5--7](https://www.space.com/smad)
- [Curtis, *Orbital Mechanics for Engineering Students*, 4th ed., 2020, Ch. 2--4](https://www.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-08-102133-0)
- [NASA, *Systems Engineering Handbook*, 2016, Sec. 4.4 (Process 4: Design Solution Definition)](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ECSS, *ECSS-U-AS-10C Rev.2: Space Debris Mitigation Requirements*, 2023](https://ecss.nl/standard/ecss-u-as-10c-rev-2-space-debris-mitigation-requirements/)
- [IADC, *Space Debris Mitigation Guidelines*, IADC-02-01 Rev 3, 2021](https://www.iadc-home.org/documents_public/)
- [FCC, *Report and Order FCC 22-74: Space Innovation*, 2022](https://www.fcc.gov/document/fcc-adopts-new-5-year-rule-deorbiting-satellites)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Define and compute the six Keplerian orbital elements
2. Calculate orbital period, velocity, and eclipse fraction for circular orbits
3. Compute the Sun-synchronous inclination using J2 precession
4. Evaluate orbit trade-offs across altitude, coverage, lifetime, radiation, and debris compliance
5. Apply the Hohmann transfer $\Delta V$ equations for orbit raising and deorbit
6. Use SpaceCDF's orbit trade advisor with mission-appropriate scoring weights

---

## 1. Keplerian Orbital Elements
Six parameters (the *classical orbital elements*) fully describe the size, shape, and orientation of an orbit, plus the satellite's position on it.

*[Source: Vallado, Ch. 2; Curtis, Ch. 2]*

| Element | Symbol | Physical Meaning | Typical Range |
|---------|--------|-----------------|---------------|
| Semi-major axis | $a$ | Size of the orbit | 6571--42164 km (LEO to GEO) |
| Eccentricity | $e$ | Shape (0 = circle, 0 < e < 1 = ellipse) | 0--0.001 for LEO circular |
| Inclination | $i$ | Tilt of orbit plane from equatorial plane | 0--180 deg |
| RAAN | $\Omega$ | Orientation of ascending node in equatorial plane | 0--360 deg |
| Argument of perigee | $\omega$ | Orientation of perigee within orbit plane | 0--360 deg |
| True anomaly | $\nu$ | Satellite position along the orbit | 0--360 deg |

For **circular LEO** missions (the most common CubeSat orbit type), the key design parameters reduce to three: **altitude** ($h$), **inclination** ($i$), and **LTAN** (local time of ascending node, for Sun-synchronous orbits).

<svg viewBox="0 0 500 400" xmlns="http://www.w3.org/2000/svg" style="max-width:450px; font-family: sans-serif; font-size: 11px;">
  <!-- Earth -->
  <circle cx="250" cy="200" r="80" fill="#bfdbfe" stroke="#2563eb" stroke-width="2"/>
  <text x="250" y="205" text-anchor="middle" fill="#1e3a5f" font-size="12">Earth</text>
  <!-- Equatorial plane -->
  <ellipse cx="250" cy="200" rx="160" ry="30" fill="none" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="420" y="195" fill="#94a3b8" font-size="10">Equatorial plane</text>
  <!-- Orbit ellipse (tilted) -->
  <ellipse cx="250" cy="185" rx="160" ry="120" fill="none" stroke="#dc2626" stroke-width="2" transform="rotate(-15, 250, 185)"/>
  <!-- Ascending node -->
  <circle cx="405" cy="195" r="5" fill="#dc2626"/>
  <text x="415" y="200" fill="#dc2626" font-weight="bold">AN</text>
  <!-- Labels -->
  <text x="250" y="50" text-anchor="middle" fill="#dc2626" font-weight="bold">Orbit plane (inclined)</text>
  <line x1="250" y1="200" x2="250" y2="100" stroke="#16a34a" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="260" y="145" fill="#16a34a" font-size="10">i (inclination)</text>
  <!-- RAAN arrow -->
  <path d="M 330 200 A 80 15 0 0 1 370 195" fill="none" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="345" y="220" fill="#7c3aed" font-size="10">$\Omega$ (RAAN)</text>
  <!-- Satellite -->
  <rect x="310" y="88" width="12" height="8" fill="#f59e0b" stroke="#92400e"/>
  <text x="330" y="95" fill="#92400e" font-size="10">Satellite</text>
</svg>

### Key Equations

> **Key Equations -- Orbital Mechanics Fundamentals**
>
> **Orbital period** (circular orbit):
> $$T = 2\pi \sqrt{\frac{a^3}{\mu}}$$
> where $a = R_E + h$ is the semi-major axis (m), $\mu = 3.986 \times 10^{14}$ m$^3$/s$^2$ is Earth's gravitational parameter, and $R_E = 6371$ km.
>
> **Orbital velocity** (circular):
> $$v = \sqrt{\frac{\mu}{a}}$$
>
> **Eclipse fraction** (maximum, circular orbit, cylindrical shadow):
> $$f_{\text{eclipse}} = \frac{1}{\pi} \arccos\left(\frac{\sqrt{a^2 - R_E^2}}{a}\right)$$
>
> **Sun-synchronous inclination** (J2-driven RAAN precession = 360 deg/year):
> $$\cos(i) = -\frac{2 \dot{\Omega}_{\text{req}} \, a^{7/2}}{3 R_E^2 \, J_2 \, \sqrt{\mu}}$$
> where $J_2 = 1.0826 \times 10^{-3}$, $\dot{\Omega}_{\text{req}} = \frac{2\pi}{365.25 \times 86400}$ rad/s.

---

## 2. Worked Examples: Orbital Computations
> **Worked Example -- 500 km Circular LEO**
>
> **Given:** $h = 500$ km, circular orbit.
>
> **Step 1 -- Semi-major axis:**
> $a = 6371 + 500 = 6871$ km $= 6.871 \times 10^6$ m
>
> **Step 2 -- Orbital period:**
> $T = 2\pi \sqrt{\frac{(6.871 \times 10^6)^3}{3.986 \times 10^{14}}} = 2\pi \sqrt{8.137 \times 10^{5}} = 2\pi \times 5668 = 5669$ s $\approx$ **94.5 min**
>
> **Step 3 -- Orbital velocity:**
> $v = \sqrt{\frac{3.986 \times 10^{14}}{6.871 \times 10^6}} = \sqrt{5.802 \times 10^7} =$ **7617 m/s** $\approx$ 7.62 km/s
>
> **Step 4 -- Eclipse fraction (maximum):**
> $f = \frac{1}{\pi} \arccos\left(\frac{\sqrt{6871^2 - 6371^2}}{6871}\right) = \frac{1}{\pi} \arccos\left(\frac{2594}{6871}\right) = \frac{1}{\pi} \arccos(0.3774) = \frac{1}{\pi} \times 67.8\degree = $ **0.376** (37.6%)
>
> **Step 5 -- Eclipse and sunlight duration:**
> $t_{\text{eclipse}} = 94.5 \times 0.376 =$ **35.5 min**; $\quad t_{\text{sun}} = 94.5 - 35.5 =$ **59.0 min**
>
> **Step 6 -- Sun-synchronous inclination:**
> $\cos(i) = -\frac{2 \times 1.991 \times 10^{-7} \times (6.871 \times 10^6)^{3.5}}{3 \times (6.371 \times 10^6)^2 \times 1.0826 \times 10^{-3} \times \sqrt{3.986 \times 10^{14}}}$
>
> Numerator: $\approx -1.301 \times 10^{17}$; Denominator: $\approx 1.006 \times 10^{18}$
>
> $\cos(i) \approx -0.1293 \Rightarrow i \approx$ **97.4 deg**

---

## 3. Orbit Selection Trade-Offs
The orbit is the single most impactful early design decision. It cascades to every subsystem.

*[Source: SMAD, Ch. 7; Wertz et al., "Reducing Space Mission Cost," Ch. 3]*

| Parameter | Lower Altitude (300--400 km) | Higher Altitude (600--800 km) |
|-----------|------------------------------|-------------------------------|
| **GSD** | Better (shorter range to target) | Worse (longer range) |
| **Orbital lifetime** | Short (1--5 years, natural decay) | Long (25--100+ years) |
| **Debris compliance** | Easy (FCC 5-year rule met naturally) | May require active deorbit propulsion |
| **Radiation (TID)** | Lower (2--5 krad/yr) | Higher (10--20 krad/yr above 700 km) |
| **Launch cost** | Lower $\Delta V$ to orbit | Slightly higher |
| **Link budget** | Better (shorter slant range) | Worse (longer path loss) |
| **Coverage/swath** | Narrower per pass | Wider per pass |
| **Atmospheric drag** | Significant (limits lifetime) | Negligible above ~700 km |
| **Eclipse fraction** | ~35--38% | ~33--35% |

### Orbit Types and Applications

| Orbit | Altitude | Inclination | Best For | Real Example |
|-------|----------|-------------|----------|-------------|
| **LEO (non-SSO)** | 300--600 km | Any | Technology demos, ISS deployment | Many CubeSats |
| **SSO** | 400--800 km | 97--99 deg | EO (consistent solar illumination) | Planet SuperDove (475 km) |
| **ISS orbit** | ~410 km | 51.6 deg | ISS-deployed CubeSats | NanoRacks deployments |
| **MEO** | 2000--20200 km | Various | Navigation | GPS (20200 km) |
| **GEO** | 35786 km | 0 deg | Comms, weather | Anik F2 (Telesat) |
| **HEO (Molniya)** | 500--40000 km | 63.4 deg | High-latitude coverage | Meridian (Russia) |
| **Lunar NRHO** | 1500--70000 km | Lunar | Cislunar operations | CAPSTONE (NASA/Advanced Space) |

### Debris Compliance Rules

| Rule | Requirement | Applies To |
|------|------------|-----------|
| **IADC guideline** (2021) | Post-mission disposal within 25 years | International (voluntary but expected) |
| **FCC rule** (2024+) | Post-mission disposal within **5 years** | All FCC-licensed LEO satellites |
| **ECSS-U-AS-10C Rev.2** | Compliance with IADC + ESA Zero Debris Charter | ESA missions |
| **ISED (Canada)** | Currently 25-year rule; tightening under review | Canadian-licensed satellites |

**Critical altitude boundaries for FCC 5-year compliance:**

| Altitude | Natural Lifetime | FCC Compliant? | Action Needed |
|----------|-----------------|---------------|---------------|
| < 450 km | < 5 years | Yes | None (natural decay) |
| 450--550 km | 5--20 years | Marginal | Drag augmentation may suffice |
| 550--650 km | 20--50 years | **No** | Active deorbit (propulsion or drag sail) |
| > 700 km | > 100 years | **No** | Propulsion mandatory; ESA Zero Debris zone |

*[Source: IADC-02-01 Rev 3, Sec. 5.3.2; FCC 22-74; ECSS-U-AS-10C Rev.2]*

### Perturbation Effects

| Perturbation | Cause | Effect on Orbit | Design Impact |
|-------------|-------|----------------|---------------|
| **$J_2$ (Earth oblateness)** | Equatorial bulge | RAAN precession, argument of perigee drift | Enables Sun-synchronous; frozen orbits at $\omega = 90\degree$ |
| **Atmospheric drag** | Residual atmosphere | Semi-major axis decay, eventual re-entry | Limits lifetime below ~600 km; drives propulsion need |
| **Solar radiation pressure** | Photon momentum | Eccentricity oscillations, orbit perturbation | Significant for large A/m ratio (drag sails, large SA) |
| **Third-body (Moon/Sun)** | Gravitational pull | Long-period oscillations in $e$, $i$ | Significant for GEO and HEO; negligible for LEO |
| **Magnetic field** | Lorentz force on charged S/C | Very small drag-like effect | Negligible for most missions |

---

## 4. Ground Coverage and Revisit
> **Key Equations -- Ground Coverage**
>
> **Swath width** (nadir-pointing sensor with half-cone angle $\theta$):
> $$W_{\text{swath}} = 2h \tan(\theta)$$
>
> **Ground track spacing** (for a single satellite in LEO):
> The Earth rotates ~22.9 deg per orbit (for $T \approx 95$ min). At the equator, this corresponds to:
> $$\Delta_{\text{lon}} = \frac{360\degree}{T_{\text{sidereal}}} \times T_{\text{orbit}} \approx 22.9\degree \approx 2550 \text{ km (at equator)}$$
>
> **Revisit time** (approximate, single satellite):
> $$t_{\text{revisit}} \approx \frac{\Delta_{\text{lon}}}{W_{\text{swath}}} \times T_{\text{orbit}}$$
>
> **Constellation revisit** (N identical satellites in same plane):
> $$t_{\text{revisit,constellation}} \approx \frac{t_{\text{revisit,single}}}{N}$$

**Example -- SuperDove constellation:**
Planet operates ~200 SuperDove satellites. With a ~24 km swath at 475 km and multiple orbital planes, the constellation achieves daily global revisit -- a dramatic improvement over a single satellite's ~7-day revisit.

### Ground Station Contact Geometry

**Contact time per pass** depends on the minimum elevation angle $\epsilon_{\min}$ (typically 5--10 deg):

$$t_{\text{contact}} \approx \frac{T}{\pi} \arccos\left(\frac{\cos(\rho)}{\cos(\epsilon_{\min})}\right) - \text{geometric correction}$$

**Simplified rule of thumb** for LEO at 500 km, $\epsilon_{\min} = 10\degree$:
- Maximum pass duration: ~10 min (overhead pass)
- Average pass duration: ~6--7 min
- Passes per day (mid-latitude station): ~4--6

---

## 5. Hohmann Transfer and Deorbit
> **Key Equations -- Hohmann Transfer**
>
> The minimum-energy transfer between two circular orbits of radii $r_1$ and $r_2$:
>
> $$\Delta V_1 = \sqrt{\frac{\mu}{r_1}} \left(\sqrt{\frac{2r_2}{r_1 + r_2}} - 1\right)$$
>
> $$\Delta V_2 = \sqrt{\frac{\mu}{r_2}} \left(1 - \sqrt{\frac{2r_1}{r_1 + r_2}}\right)$$
>
> $$\Delta V_{\text{total}} = |\Delta V_1| + |\Delta V_2|$$

> **Worked Example -- Deorbit from 600 km to 200 km (re-entry perigee)**
>
> $r_1 = 6971$ km, $r_2 = 6571$ km
>
> $\Delta V_1 = \sqrt{\frac{3.986 \times 10^5}{6971}} \left(\sqrt{\frac{2 \times 6571}{6971 + 6571}} - 1\right)$
> $= 7.561 \times (\sqrt{0.9705} - 1) = 7.561 \times (-0.01498) = -0.1133$ km/s
>
> $\Delta V_{\text{total}} \approx$ **113 m/s** (only the first burn needed to lower perigee)

This deorbit $\Delta V$ is a critical input to the propulsion sizing in Session 3.4.

---

## 6. Radiation Environment
*[Source: ECSS-E-ST-10-04C Rev.1; SMAD, Ch. 8.1]*

### Total Ionising Dose (TID) by Orbit

| Orbit | TID (krad/year behind 2mm Al) | Electronics Class |
|-------|-------------------------------|-------------------|
| ISS (410 km, 51.6 deg) | 2--5 | Commercial COTS OK |
| SSO 500 km | 5--10 | Commercial / rad-tolerant |
| SSO 800 km | 10--20 | Rad-tolerant recommended |
| MEO 2000 km | 50--100 | Rad-hard required |
| GEO 35786 km | 10--20 | Rad-hard required |

**Rule of thumb:** Below 600 km in LEO, commercial COTS electronics can survive 3-year missions with modest shielding (2--3 mm Al equivalent). Above 600 km, radiation becomes a significant design driver and component cost escalates.

### South Atlantic Anomaly (SAA)

At 200--600 km altitude over South America, trapped protons from the inner Van Allen belt dip to lower altitudes. The SAA causes:
- Single-event upsets (SEU) in memory
- Single-event latch-ups (SEL) in CMOS
- Increased background noise in optical detectors

Mitigation: error-correcting memory (EDAC), watchdog timers, latch-up protection circuits.

---

### 1U Worked Example: UniSat-1

**Orbit Selection: ISS Orbit (400 km, 51.6 deg) for Rideshare**

UniSat-1 selects the ISS orbit not by optimisation but by **access**: deployment from the ISS via NanoRacks or a similar deployer is the cheapest and most accessible launch opportunity for a university 1U CubeSat.

> **Worked Example -- Orbital Parameters at 400 km, 51.6 deg**
>
> **Step 1 -- Semi-major axis:**
> $a = 6371 + 400 = 6771$ km $= 6.771 \times 10^6$ m
>
> **Step 2 -- Orbital period:**
> $T = 2\pi \sqrt{\frac{(6.771 \times 10^6)^3}{3.986 \times 10^{14}}} = 2\pi \times 5564 = 5565$ s $\approx$ **92.4 min**
>
> **Step 3 -- Orbital velocity:**
> $v = \sqrt{\frac{3.986 \times 10^{14}}{6.771 \times 10^6}} =$ **7672 m/s** $\approx$ 7.67 km/s
>
> **Step 4 -- Eclipse fraction (maximum):**
> $f = \frac{1}{\pi} \arccos\left(\frac{\sqrt{6771^2 - 6371^2}}{6771}\right) = \frac{1}{\pi} \arccos(0.3423) = \frac{1}{\pi} \times 70.0\degree \approx$ **0.389** (38.9%)
>
> **Step 5 -- Eclipse and sunlight duration:**
> $t_{\text{eclipse}} = 92.4 \times 0.389 \approx$ **36 min**; $\quad t_{\text{sun}} = 92.4 - 36 =$ **56 min**

**Why this orbit works for UniSat-1:**

| Factor | 400 km / 51.6 deg | Impact on UniSat-1 |
|--------|-------------------|-------------------|
| Launch cost | Lowest (ISS resupply rideshare) | Fits university budget |
| Orbital lifetime | ~1 year (natural decay) | Exceeds 6-month mission; compliant with FCC 5-year rule without propulsion |
| Radiation | Low (~2--3 krad/yr behind 2 mm Al) | COTS electronics safe for 6-month mission |
| Inclination | 51.6 deg | Adequate latitude coverage for space weather science |
| Eclipse | ~36 min (~39% of orbit) | Manageable with 10 Wh battery |
| Ground contacts | Mid-latitude stations: ~4--6 passes/day | Sufficient for 9600 bps UHF downlink |

**What this orbit does NOT provide:**
- Sun-synchronous lighting (not needed -- magnetometer is not an optical instrument)
- Polar coverage (acceptable -- 51.6 deg covers the majority of magnetic field variation)
- Long lifetime (acceptable -- 6-month design life is well within ~1-year natural lifetime)

**No propulsion trade:** At 400 km, atmospheric drag causes natural re-entry within approximately 1 year (depending on solar activity and ballistic coefficient). UniSat-1 therefore needs no propulsion system for either orbit maintenance or debris compliance. This eliminates an entire subsystem -- a major simplification for a 1U mission.

---

## 7. SpaceCDF Orbit Trade Exercise
### Instructions

1. Navigate to the **Mission Architecture** tab in SpaceCDF
2. Open the **Orbit Trade Advisor** panel
3. Enter your mission parameters:
   - GSD target (optical missions) or "N/A" for non-optical
   - Revisit target (days)
   - Mission lifetime (years)
   - Latitude band of interest
   - Cost ceiling (MEUR)
   - Aperture diameter (if known from optical sizing)
4. Click **"Compute Orbit Trade"**
5. Review the scored candidates:
   - Which orbit scores highest overall?
   - Is it debris-compliant (FCC 5-year rule)?
   - What is the natural orbital lifetime?
6. Click **"Use"** on your preferred orbit to populate the design parameters
7. Verify orbit fields updated in the dashboard (look for "Set from advisor" badge)

### Discussion Points

- Does the best-scoring orbit match your engineering intuition?
- What happens when you change scoring weights (prioritise GSD over cost, or vice versa)?
- For non-optical missions (comms, AIS), does the orbit scoring still make physical sense?
- If your selected orbit is above 600 km, what deorbit strategy will you use?
- Complete Worksheet 2.3

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Keplerian elements | Six parameters define the orbit; for LEO: altitude + inclination + LTAN |
| Key formulae | $T = 2\pi\sqrt{a^3/\mu}$; $v = \sqrt{\mu/a}$; eclipse fraction from geometry |
| Sun-synchronous | Requires specific inclination (~97 deg at 500 km) using $J_2$ precession |
| Perturbations | $J_2$ enables SSO; drag limits lifetime; SRP affects high-A/m satellites |
| Trade-offs | Lower altitude = better GSD and link but shorter lifetime and more drag |
| Debris rules | FCC 5-year, IADC 25-year; above ~550 km requires active deorbit |
| Hohmann transfer | $\Delta V_{\text{deorbit}} \approx 100$ m/s from 600 km; critical propulsion input |
| Radiation | Below 600 km: COTS OK; above: rad-tolerant/hard needed; SAA causes SEU |
| Cascade | Orbit choice affects every subsystem -- highest-leverage design decision |
