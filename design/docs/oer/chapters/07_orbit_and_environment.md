# Chapter 7 — Orbit Selection and the Space Environment

> **Recommended background.** SMAD4 Ch. 5–7 (orbit and mission geometry); Vallado, *Fundamentals of Astrodynamics and Applications*, Ch. 2 and 9; ECSS-E-ST-10-04C (space environment); ECSS-U-AS-10C Rev.2 (debris mitigation). The derivations of Kepler's third law, the J₂ nodal regression and the eclipse fraction are given in Part V (§V.2, §V.4, §V.5); this chapter uses the results.

## Learning objectives

By the end of this chapter, you will be able to:

1. Define the six Keplerian orbital elements and reduce them to the three that matter for circular LEO design
2. Calculate orbital period, velocity, and eclipse fraction for circular orbits, including the dependence on the solar β-angle
3. Compute the Sun-synchronous inclination from the J₂ nodal precession
4. Evaluate orbit trade-offs across altitude, coverage, lifetime, radiation, and debris compliance, and estimate orbital lifetime from first principles
5. Apply the Hohmann transfer ΔV equations for orbit raising and deorbit
6. Score candidate orbits against mission-appropriate criteria and defend the selection

---

## 7.1 Keplerian orbital elements

Six parameters (the *classical orbital elements*) fully describe the size, shape, and orientation of an orbit, plus the satellite's position on it.

*[Source: Vallado, Ch. 2; Curtis, Ch. 2]*

| Element | Symbol | Physical meaning | Typical range |
|---------|--------|-----------------|---------------|
| Semi-major axis | $a$ | Size of the orbit | 6578–42 164 km (LEO to GEO) |
| Eccentricity | $e$ | Shape (0 = circle, 0 < e < 1 = ellipse) | 0–0.001 for LEO circular |
| Inclination | $i$ | Tilt of orbit plane from equatorial plane | 0–180° |
| RAAN | $\Omega$ | Orientation of ascending node in equatorial plane | 0–360° |
| Argument of perigee | $\omega$ | Orientation of perigee within orbit plane | 0–360° |
| True anomaly | $\nu$ | Satellite position along the orbit | 0–360° |

For **circular LEO** missions (the most common CubeSat orbit type), the key design parameters reduce to three: **altitude** ($h$), **inclination** ($i$), and **LTAN** (local time of ascending node, for Sun-synchronous orbits). Figure 7.1 sketches the geometry.

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
  <text x="345" y="220" fill="#7c3aed" font-size="10">Ω (RAAN)</text>
  <!-- Satellite -->
  <rect x="310" y="88" width="12" height="8" fill="#f59e0b" stroke="#92400e"/>
  <text x="330" y="95" fill="#92400e" font-size="10">Satellite</text>
</svg>

**Figure 7.1** — Orbit geometry: the inclined orbit plane, the equatorial plane, the ascending node (AN), inclination $i$ and right ascension of the ascending node $\Omega$.

### 7.1.1 Key equations

Throughout this book the Earth constants are $R_E = 6378.137$ km (WGS-84 equatorial radius), $\mu = 398\,600.44$ km³/s² $= 3.986\,00 \times 10^{14}$ m³/s² and $J_2 = 1.0826 \times 10^{-3}$ (Part V §V.1).

> **Key equations — orbital mechanics fundamentals**
>
> **Orbital period** (circular orbit; Part V §V.2):
> $$T = 2\pi \sqrt{\frac{a^3}{\mu}}$$
> where $a = R_E + h$ is the semi-major axis.
>
> **Orbital velocity** (circular):
> $$v = \sqrt{\frac{\mu}{a}}$$
>
> **Sun-synchronous inclination** ($J_2$-driven RAAN precession of 360° per year; Part V §V.4):
> $$\cos i = -\frac{2 \dot{\Omega}_{\text{req}} \, a^{7/2}}{3 R_E^2 \, J_2 \, \sqrt{\mu}}$$
> where $\dot{\Omega}_{\text{req}} = \dfrac{2\pi}{365.25 \times 86\,400} = 1.991 \times 10^{-7}$ rad/s.

### 7.1.2 Eclipse fraction and the β-angle

Whether, and for how long, a circular orbit passes through Earth's shadow depends on the **solar β-angle**: the angle between the Sun vector and the orbit plane. It is obtained from the orbit orientation and the Sun's position (right ascension $\alpha_\odot$, declination $\delta_\odot$):

$$\sin\beta = \cos\delta_\odot \sin i \sin(\Omega - \alpha_\odot) + \sin\delta_\odot \cos i$$

Because $\Omega$ precesses and the Sun moves along the ecliptic, β varies through the year. For a Sun-synchronous orbit the precession tracks the Sun, so β stays within a narrow band fixed by the LTAN (a dawn–dusk orbit has $|\beta|$ near 90° and is almost never eclipsed; a 10:30 LTAN orbit has $|\beta|$ of order 20–30°). For an ISS-like orbit β sweeps a wide range and can reach the fully sunlit condition for a few days at a time.

> **Key equation — eclipse fraction (circular orbit, cylindrical shadow; Part V §V.5)**
>
> Define the shadow half-angle seen from the orbit, $\beta^* = \arcsin\!\left(\dfrac{R_E}{R_E + h}\right)$. For $|\beta| < \beta^*$,
> $$f_{\text{ecl}} = \frac{1}{\pi} \arccos\left(\frac{\sqrt{h^2 + 2 R_E h}}{(R_E + h)\cos\beta}\right)$$
> and for $|\beta| \geq \beta^*$ the orbit is fully sunlit ($f_{\text{ecl}} = 0$).
>
> **Corollary — worst case, β = 0** (Sun in the orbit plane). Since $\sqrt{h^2 + 2R_E h}/(R_E + h) = \sqrt{1 - (R_E/(R_E+h))^2} = \cos\beta^*$, the maximum eclipse fraction is simply
> $$f_{\text{ecl,max}} = \frac{\beta^*}{\pi} = \frac{1}{\pi}\arcsin\!\left(\frac{R_E}{R_E + h}\right)$$
> This is the value used for power sizing in Chapter 9 unless the mission's β-angle history is known to exclude β = 0.

Figure 7.2 shows both halves of this behaviour: the annual β-angle envelope for an ISS-like orbit and a 10:30 LTAN Sun-synchronous orbit (left), and the eclipse fraction as a function of β, with its plateau near β = 0 and its sharp fall to zero at $\beta^*$ (right).

![β-angle envelope over a year and eclipse fraction versus β.](../assets/figures/fig_beta_eclipse.png)

**Figure 7.2** — Left: annual β-angle envelope for an ISS-like orbit (51.6°, 400 km) and a 10:30 LTAN Sun-synchronous orbit (98°, 600 km). Right: eclipse fraction versus β for the same two orbits; the plateau at low |β| is the worst-case value used for power sizing, and the orbit is fully sunlit beyond $\beta^*$ (≈ 70° at 400 km, ≈ 66° at 600 km).

---

## 7.2 Worked examples: orbital computations

> **Worked example — 500 km circular LEO**
>
> **Given:** $h = 500$ km, circular orbit.
>
> **Step 1 — Semi-major axis:**
> $a = 6378.137 + 500 = 6878.137$ km $= 6.878 \times 10^6$ m
>
> **Step 2 — Orbital period:**
> $a^3 = 6878.137^3 = 3.254 \times 10^{11}$ km³; $\quad a^3/\mu = 3.254 \times 10^{11} / 398\,600.44 = 8.163 \times 10^{5}$ s²
>
> $T = 2\pi \sqrt{8.163 \times 10^{5}} = 2\pi \times 903.5 = 5677$ s $\approx$ **94.6 min**
>
> **Step 3 — Orbital velocity:**
> $v = \sqrt{\dfrac{398\,600.44}{6878.137}} = \sqrt{57.95} =$ **7.613 km/s**
>
> **Step 4 — Shadow half-angle and maximum eclipse fraction (β = 0):**
> $\beta^* = \arcsin\!\left(\dfrac{6378.137}{6878.137}\right) = \arcsin(0.9273) = 68.0°$
>
> Check via the general form: $\sqrt{h^2 + 2R_E h} = \sqrt{500^2 + 2 \times 6378.137 \times 500} = \sqrt{6\,628\,137} = 2574.5$ km; $\;2574.5/6878.137 = 0.3743$; $\;\arccos(0.3743) = 68.0°$ ✓
>
> $f_{\text{ecl,max}} = 68.0/180 =$ **0.378** (37.8 %)
>
> **Step 5 — Eclipse and sunlight duration:**
> $t_{\text{ecl}} = 94.6 \times 0.378 =$ **35.8 min**; $\quad t_{\text{sun}} = 94.6 - 35.8 =$ **58.8 min**
>
> **Step 6 — Sun-synchronous inclination:**
> $a^{7/2} = a^3 \sqrt{a} = 3.254 \times 10^{20} \times 2622.6 = 8.534 \times 10^{23}$ (SI units)
>
> Numerator: $2 \times 1.991 \times 10^{-7} \times 8.534 \times 10^{23} = 3.398 \times 10^{17}$
>
> Denominator: $3 \times (6.378137 \times 10^6)^2 \times 1.0826 \times 10^{-3} \times \sqrt{3.986 \times 10^{14}} = 3 \times 4.068 \times 10^{13} \times 1.0826 \times 10^{-3} \times 1.9965 \times 10^{7} = 2.638 \times 10^{18}$
>
> $\cos i = -\dfrac{3.398 \times 10^{17}}{2.638 \times 10^{18}} = -0.1288 \Rightarrow i \approx$ **97.4°**

> **Check — 450 km Sun-synchronous orbit** (the altitude used for the Part V §V.2 verification):
> $a = 6828.137$ km; $a^3/\mu = 3.1835 \times 10^{11}/398\,600.44 = 7.987 \times 10^{5}$ s²; $\sqrt{\cdot} = 893.7$ s; $T = 2\pi \times 893.7 = 5615$ s $\approx$ **93.6 min**. Using the older $R_E = 6371$ km value gives 93.5 min; the difference is below 0.2 % but every number in this book uses 6378.137 km so that the chapters agree.

---

## 7.3 Orbit selection trade-offs

The orbit is the single most impactful early design decision. It cascades to every subsystem.

*[Source: SMAD, Ch. 7; Wertz et al., "Reducing Space Mission Cost," Ch. 3]*

| Parameter | Lower altitude (300–400 km) | Higher altitude (600–800 km) |
|-----------|------------------------------|-------------------------------|
| **GSD** | Better (shorter range to target) | Worse (longer range) |
| **Orbital lifetime** | Short (months to a few years, natural decay) | Long (25–100+ years) |
| **Debris compliance** | Easy (FCC 5-year rule met naturally) | May require active deorbit propulsion |
| **Radiation (TID)** | Lower (2–5 krad/yr) | Higher (10–20 krad/yr above 700 km) |
| **Launch cost** | Lower ΔV to orbit | Slightly higher |
| **Link budget** | Better (shorter slant range) | Worse (longer path loss) |
| **Coverage/swath** | Narrower per pass | Wider per pass |
| **Atmospheric drag** | Significant (limits lifetime) | Negligible above ~700 km |
| **Eclipse fraction (β = 0)** | ~38–39 % | ~35–37 % |

### 7.3.1 Orbit types and applications

| Orbit | Altitude | Inclination | Best for | Real example |
|-------|----------|-------------|----------|-------------|
| **LEO (non-SSO)** | 300–600 km | Any | Technology demos, ISS deployment | Many CubeSats |
| **SSO** | 400–800 km | 97–99° | EO (consistent solar illumination) | Planet SuperDove (475 km) |
| **ISS orbit** | ~410 km | 51.6° | ISS-deployed CubeSats | NanoRacks deployments |
| **MEO** | 2000–20 200 km | Various | Navigation | GPS (20 200 km) |
| **GEO** | 35 786 km | 0° | Comms, weather | Anik F2 (Telesat) |
| **HEO (Molniya)** | 500–40 000 km | 63.4° | High-latitude coverage | Meridian (Russia) |
| **Lunar NRHO** | 1500–70 000 km | Lunar | Cislunar operations | CAPSTONE (NASA/Advanced Space) |

### 7.3.2 Debris compliance rules

| Rule | Requirement | Applies to |
|------|------------|-----------|
| **IADC guideline** (2021) | Post-mission disposal within 25 years | International (voluntary but expected) |
| **FCC rule** (2024+) | Post-mission disposal within **5 years** | All FCC-licensed LEO satellites |
| **ECSS-U-AS-10C Rev.2** | Compliance with IADC + ESA Zero Debris Charter | ESA missions |
| **ISED (Canada)** | Currently 25-year rule; tightening under review | Canadian-licensed satellites |

**Critical altitude boundaries for FCC 5-year compliance** (typical CubeSat ballistic coefficients, mean solar activity):

| Altitude | Natural lifetime | FCC compliant? | Action needed |
|----------|-----------------|---------------|---------------|
| < 450 km | < 5 years | Yes | None (natural decay) |
| 450–550 km | 5–20 years | Marginal | Drag augmentation may suffice |
| 550–650 km | 20–50 years | **No** | Active deorbit (propulsion or drag sail) |
| > 700 km | > 100 years | **No** | Propulsion mandatory; ESA Zero Debris zone |

*[Source: IADC-02-01 Rev 3, Sec. 5.3.2; FCC 22-74; ECSS-U-AS-10C Rev.2]*

### 7.3.3 Orbital lifetime from first principles

Chapter 3 §3.6.4 introduced the ballistic coefficient $B = m/(C_D A)$, the lifetime-versus-altitude chart (Figure 3.2) and a quick rule of thumb. The rule of thumb is a curve fit for mid-altitude, moderate-$B$ spacecraft and badly overestimates lifetime below about 500 km (it returns ~18 years at 400 km for a 4 kg, 0.03 m² 3U CubeSat, which is wrong by more than an order of magnitude). The physically based estimate is short and worth doing properly.

For a circular orbit, drag removes semi-major axis at the rate

$$\frac{da}{dt} = -\sqrt{\mu a}\,\frac{\rho}{B}, \qquad B = \frac{m}{C_D A}$$

(this follows from the per-orbit decrement $\Delta a = -2\pi\,\rho\,a^2/B$ divided by the period). Because atmospheric density falls roughly exponentially with altitude, $\rho \propto e^{-h/H}$ with scale height $H$, almost all of the remaining lifetime is spent within the first scale height below the initial altitude, so

$$\tau \approx \frac{H}{|da/dt|_{h_0}} = \frac{H\,B}{\rho(h_0)\sqrt{\mu a}}$$

> **Worked example — 3U CubeSat lifetime at 400 km and 500 km**
>
> **Given:** $m = 4$ kg, tumbling-average area $A = 0.03$ m², $C_D = 2.2$, so $B = 4/(2.2 \times 0.03) = 60.6$ kg/m².
>
> **400 km, mean solar activity:** $\rho \approx 2.8 \times 10^{-12}$ kg/m³, $H \approx 58$ km.
> $\sqrt{\mu a} = \sqrt{3.986 \times 10^{14} \times 6.778 \times 10^{6}} = 5.20 \times 10^{10}$ m²/s
> $|da/dt| = 5.20 \times 10^{10} \times 2.8 \times 10^{-12} / 60.6 = 2.4 \times 10^{-3}$ m/s $= 207$ m/day $= 76$ km/yr
> $\tau \approx 58 / 76 \approx 0.76$ yr $\approx$ **9 months**
>
> Across the solar cycle the density at 400 km varies by roughly a factor of 8 ($\sim 1 \times 10^{-12}$ at solar minimum to $\sim 8 \times 10^{-12}$ at solar maximum), so the lifetime ranges from about **3 months (solar maximum) to about 2 years (solar minimum)**.
>
> **500 km, mean solar activity:** $\rho \approx 5 \times 10^{-13}$ kg/m³, $H \approx 65$ km, $\sqrt{\mu a} = 5.24 \times 10^{10}$ m²/s.
> $|da/dt| = 5.24 \times 10^{10} \times 5 \times 10^{-13} / 60.6 = 4.3 \times 10^{-4}$ m/s $= 13.6$ km/yr; $\quad \tau \approx 65/13.6 \approx$ **5 years** (roughly 2–12 years across the cycle).
>
> **Reading the result.** At 400 km a 3U CubeSat re-enters naturally in about a year and needs no deorbit device; at 500 km the design sits on the FCC 5-year boundary and the answer depends on the launch date within the solar cycle. For a precise figure use a density model (NRLMSISE-00 or JB2008) and numerical propagation — but the estimate above is accurate to within a factor of two, which is enough to decide whether a deorbit subsystem is required.

### 7.3.4 Perturbation effects

| Perturbation | Cause | Effect on orbit | Design impact |
|-------------|-------|----------------|---------------|
| **$J_2$ (Earth oblateness)** | Equatorial bulge | RAAN precession, argument of perigee drift | Enables Sun-synchronous; frozen orbits at $\omega = 90°$ |
| **Atmospheric drag** | Residual atmosphere | Semi-major axis decay, eventual re-entry | Limits lifetime below ~600 km; drives propulsion need |
| **Solar radiation pressure** | Photon momentum | Eccentricity oscillations, orbit perturbation | Significant for large A/m ratio (drag sails, large SA) |
| **Third-body (Moon/Sun)** | Gravitational pull | Long-period oscillations in $e$, $i$ | Significant for GEO and HEO; negligible for LEO |
| **Magnetic field** | Lorentz force on charged S/C | Very small drag-like effect | Negligible for most missions |

---

## 7.4 Ground coverage and revisit

> **Key equations — ground coverage**
>
> **Swath width** (nadir-pointing sensor with half-cone angle $\theta$):
> $$W_{\text{swath}} = 2h \tan\theta$$
>
> **Ground-track spacing** (single satellite in LEO). Earth rotates beneath the orbit by $\omega_E T$ per revolution; for $T = 94.6$ min,
> $$\Delta_{\text{lon}} = \frac{360°}{86\,164 \text{ s}} \times 5677 \text{ s} \approx 23.7° \approx 2640 \text{ km at the equator}$$
> (for a Sun-synchronous orbit the nodal precession adds about 0.07° per orbit in the opposite sense — negligible here).
>
> **Revisit time** (approximate, single satellite, swath narrower than the track spacing):
> $$t_{\text{revisit}} \approx \frac{\Delta_{\text{lon}}}{W_{\text{swath}}} \times T_{\text{orbit}}$$
>
> **Constellation revisit** ($N$ identical satellites, evenly phased):
> $$t_{\text{revisit,constellation}} \approx \frac{t_{\text{revisit,single}}}{N}$$

**Example — SuperDove constellation:** Planet operates ~200 SuperDove satellites. With a ~24 km swath at 475 km the single-satellite revisit at the equator would be $(2640/24) \times 94.6$ min $\approx 110$ orbits $\approx 7$ days; with multiple orbital planes the constellation achieves daily global revisit.

Figure 7.3 shows one and a half revolutions of a 600 km Sun-synchronous ground track. Each successive ascending-node crossing is displaced westward by $\Delta_{\text{lon}}$, the track reaches latitude $\pm(180° - i) \approx \pm 82°$, and a mid-latitude site such as Ottawa is overflown on only a fraction of the daily passes — which is why the swath, not the orbit alone, sets the revisit.

![Ground track of a 600 km Sun-synchronous orbit.](../assets/figures/fig_ground_track.png)

**Figure 7.3** — Ground track of a 600 km Sun-synchronous orbit ($i = 97.79°$) over one and a half revolutions. Successive tracks shift westward by the Earth rotation during one orbit (≈ 24°); the maximum latitude reached is $180° - i$.

### 7.4.1 Ground-station contact geometry

The length of a pass depends on the minimum elevation angle $\varepsilon_{\min}$ at which the station can track (typically 5–10°). The Earth central angle from the station to the satellite at that elevation is

$$\lambda_{\max} = \arccos\!\left(\frac{R_E}{R_E + h}\cos\varepsilon_{\min}\right) - \varepsilon_{\min}$$

and the longest (overhead) pass lasts approximately

$$t_{\text{contact,max}} \approx \frac{T}{\pi}\,\lambda_{\max} \quad (\lambda_{\max} \text{ in radians})$$

> **Example — 500 km, $\varepsilon_{\min} = 10°$:** $\dfrac{R_E}{R_E+h}\cos 10° = 0.9273 \times 0.9848 = 0.9132$; $\arccos(0.9132) = 24.0°$; $\lambda_{\max} = 24.0° - 10° = 14.0° = 0.245$ rad; $t_{\text{contact,max}} = (5677/\pi) \times 0.245 \approx 442$ s $\approx$ **7.4 min**. With a 5° mask the same orbit gives $\lambda_{\max} = 17.5°$ and about 9.2 min.

**Rules of thumb** for LEO at 500 km with a 10° mask: maximum pass ≈ 7–8 min (overhead), average pass ≈ 5 min, and 4–6 usable passes per day from a mid-latitude station. Chapter 17 develops the full pass geometry (slant range, Doppler and elevation profile) for the ground-segment design.

---

## 7.5 Hohmann transfer and deorbit

> **Key equations — Hohmann transfer** (Part V §V.3 gives the LEO → GEO sanity check)
>
> The minimum-energy two-impulse transfer between coplanar circular orbits of radii $r_1$ and $r_2$:
>
> $$\Delta V_1 = \sqrt{\frac{\mu}{r_1}} \left(\sqrt{\frac{2r_2}{r_1 + r_2}} - 1\right)$$
>
> $$\Delta V_2 = \sqrt{\frac{\mu}{r_2}} \left(1 - \sqrt{\frac{2r_1}{r_1 + r_2}}\right)$$
>
> $$\Delta V_{\text{total}} = |\Delta V_1| + |\Delta V_2|$$

Figure 7.4 illustrates the geometry for the classic LEO-to-GEO case: a burn at perigee raises apogee to the target radius, and a second burn at apogee circularises. The same equations, with $r_2 < r_1$, describe a deorbit burn.

![Hohmann transfer from 400 km LEO to GEO.](../assets/figures/fig_hohmann.png)

**Figure 7.4** — Hohmann transfer from a 400 km circular orbit to GEO: $\Delta V_1 \approx 2.40$ km/s at perigee, $\Delta V_2 \approx 1.46$ km/s at apogee, total ≈ 3.85 km/s, transfer time ≈ 5.3 h. Part V §V.3 reproduces these numbers.

> **Worked example — deorbit from 600 km to a 200 km re-entry perigee**
>
> $r_1 = 6378.137 + 600 = 6978.137$ km, $\quad r_2 = 6378.137 + 200 = 6578.137$ km
>
> $\sqrt{\mu/r_1} = \sqrt{398\,600.44/6978.137} = \sqrt{57.12} = 7.558$ km/s
>
> $\sqrt{\dfrac{2r_2}{r_1 + r_2}} = \sqrt{\dfrac{13\,156.27}{13\,556.27}} = \sqrt{0.9705} = 0.9851$
>
> $\Delta V_1 = 7.558 \times (0.9851 - 1) = 7.558 \times (-0.0149) = -0.112$ km/s
>
> $\Delta V_{\text{deorbit}} \approx$ **112 m/s** (only the first burn is needed — once perigee is inside the dense atmosphere, drag completes the job)

This deorbit ΔV is a critical input to the propulsion sizing in Chapter 12 and to the debris-compliance decision of §7.3.2.

---

## 7.6 Radiation environment

*[Source: ECSS-E-ST-10-04C Rev.1; SMAD, Ch. 8.1]*

### 7.6.1 Total ionising dose (TID) by orbit

The dose a spacecraft accumulates in LEO is dominated by the trapped protons of the inner Van Allen belt, which it crosses in the South Atlantic Anomaly (§7.6.2); it rises steeply with altitude and falls with shielding thickness. Figure 7.5 shows the trend for the three shielding thicknesses a CubeSat designer can realistically choose between, and the table beneath gives the values by orbit behind 2 mm of aluminium.

![Total ionising dose per year versus altitude for 1, 2 and 4 mm aluminium shielding, with the table ranges marked.](../assets/figures/fig_tid_altitude.png)

**Figure 7.5** — Trapped-proton total ionising dose versus altitude for 1, 2 and 4 mm of aluminium shielding. The 2 mm curve is an illustrative fit through the ranges of the table below (grey bars); halving the shielding roughly doubles or triples the dose, doubling it roughly halves the dose. Below about 600 km commercial electronics survive multi-year missions with modest shielding; above it radiation becomes a design driver.

| Orbit | TID (krad/year behind 2 mm Al) | Electronics class |
|-------|-------------------------------|-------------------|
| ISS (410 km, 51.6°) | 2–5 | Commercial COTS OK |
| SSO 500 km | 5–10 | Commercial / rad-tolerant |
| SSO 800 km | 10–20 | Rad-tolerant recommended |
| MEO 2000 km | 50–100 | Rad-hard required |
| GEO 35 786 km | 10–20 | Rad-hard required |

**Rule of thumb:** Below 600 km in LEO, commercial COTS electronics can survive 3-year missions with modest shielding (2–3 mm Al equivalent). Above 600 km, radiation becomes a significant design driver and component cost escalates.

### 7.6.2 South Atlantic Anomaly (SAA)

At 200–600 km altitude over South America, trapped protons from the inner Van Allen belt dip to lower altitudes. The SAA causes:

- Single-event upsets (SEU) in memory
- Single-event latch-ups (SEL) in CMOS
- Increased background noise in optical detectors

Mitigation: error-correcting memory (EDAC), watchdog timers, latch-up protection circuits.

---

## 7.7 Worked example: UniSat-1 orbit selection

Returning to UniSat-1, the 1U demonstrator of Chapter 1 §1.7: it selects the ISS orbit (400 km, 51.6°) not by optimisation but by **access**. Deployment from the ISS via a commercial deployer is the cheapest and most accessible launch opportunity for a university 1U CubeSat.

> **Worked example — orbital parameters at 400 km, 51.6°**
>
> **Step 1 — Semi-major axis:**
> $a = 6378.137 + 400 = 6778.137$ km $= 6.778 \times 10^6$ m
>
> **Step 2 — Orbital period:**
> $a^3/\mu = 3.114 \times 10^{11}/398\,600.44 = 7.813 \times 10^{5}$ s²; $\quad T = 2\pi \times 883.9 = 5554$ s $\approx$ **92.6 min**
>
> **Step 3 — Orbital velocity:**
> $v = \sqrt{398\,600.44/6778.137} = \sqrt{58.81} =$ **7.669 km/s**
>
> **Step 4 — Maximum eclipse fraction (β = 0):**
> $\beta^* = \arcsin(6378.137/6778.137) = \arcsin(0.9410) = 70.2°$; $\quad f_{\text{ecl,max}} = 70.2/180 \approx$ **0.390** (39.0 %)
>
> **Step 5 — Eclipse and sunlight duration:**
> $t_{\text{ecl}} = 92.6 \times 0.390 \approx$ **36 min**; $\quad t_{\text{sun}} = 92.6 - 36 \approx$ **56.5 min**
>
> **Step 6 — Lifetime** (§7.3.3): $m = 1.3$ kg, $A = 0.01$ m², $B = 1.3/(2.2 \times 0.01) = 59$ kg/m² — almost the same ballistic coefficient as the 3U case, so the same answer: **about 9 months at mean solar activity, 3 months to 2 years across the cycle.**

**Why this orbit works for UniSat-1:**

| Factor | 400 km / 51.6° | Impact on UniSat-1 |
|--------|-------------------|-------------------|
| Launch cost | Lowest (ISS resupply rideshare) | Fits university budget |
| Orbital lifetime | ~9 months at mean activity (natural decay) | Covers the 6-month mission at mean or low solar activity; compliant with FCC 5-year rule without propulsion |
| Radiation | Low (~2–3 krad/yr behind 2 mm Al) | COTS electronics safe for 6-month mission |
| Inclination | 51.6° | Adequate latitude coverage for space-weather science |
| Eclipse | ~36 min (~39 % of orbit) | Manageable with 10 Wh battery |
| Ground contacts | Mid-latitude stations: ~4–6 passes/day | Sufficient for 9600 bps UHF downlink |

**What this orbit does NOT provide:**

- Sun-synchronous lighting (not needed — magnetometer is not an optical instrument)
- Polar coverage (acceptable — 51.6° covers the majority of magnetic-field variation)
- Long lifetime (acceptable — the 6-month design life is within the natural lifetime at mean solar activity, but see below)

**No propulsion trade:** At 400 km, atmospheric drag causes natural re-entry within roughly a year. UniSat-1 therefore needs no propulsion system for either orbit maintenance or debris compliance. This eliminates an entire subsystem — a major simplification for a 1U mission. The one risk the lifetime estimate exposes is **launch timing**: deployed at solar maximum, a 1U at 400 km may re-enter in about three months, shorter than the 6-month mission. The mission plan should either accept a shortened mission in that case or ask for a slightly higher deployment altitude.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Keplerian elements | Six parameters define the orbit; for LEO: altitude + inclination + LTAN |
| Key formulae | $T = 2\pi\sqrt{a^3/\mu}$; $v = \sqrt{\mu/a}$; eclipse fraction from geometry and β-angle |
| Eclipse | $f_{\text{ecl}}$ depends on β; worst case at β = 0 is $\beta^*/\pi$ (≈ 38 % at 500 km, 39 % at 400 km) |
| Sun-synchronous | Requires specific inclination (~97.4° at 500 km) using $J_2$ precession |
| Perturbations | $J_2$ enables SSO; drag limits lifetime; SRP affects high-A/m satellites |
| Trade-offs | Lower altitude = better GSD and link but shorter lifetime and more drag |
| Lifetime | $\tau \approx H B/(\rho \sqrt{\mu a})$: ~9 months at 400 km, ~5 years at 500 km for a CubeSat; strongly solar-cycle dependent |
| Debris rules | FCC 5-year, IADC 25-year; above ~550 km requires active deorbit |
| Hohmann transfer | $\Delta V_{\text{deorbit}} \approx 110$ m/s from 600 km; critical propulsion input |
| Radiation | Below 600 km: COTS OK; above: rad-tolerant/hard needed; SAA causes SEU |
| Cascade | Orbit choice affects every subsystem — highest-leverage design decision |

## Problems

1. **Orbit basics.** For circular orbits at 350, 550 and 700 km, compute the period, velocity, shadow half-angle $\beta^*$ and worst-case eclipse fraction. Tabulate the results and comment on how weakly the eclipse fraction depends on altitude compared with the lifetime.

2. **β-angle and power.** A 3U Earth-observation CubeSat is in a 550 km Sun-synchronous orbit with 10:30 LTAN; assume its β-angle stays between 15° and 35° through the year. Compute the eclipse fraction at β = 15°, 25° and 35° and compare with the β = 0 corollary. By what percentage would the battery sized in Chapter 9 be oversized if the β = 0 value were used?

3. **Sun-synchronous inclination.** Compute the Sun-synchronous inclination at 400, 600 and 800 km. Plot (or tabulate) $i$ against altitude and explain, using the $a^{7/2}$ dependence, why higher orbits need a more retrograde inclination.

4. **Lifetime and the solar cycle.** A 6U CubeSat ($m = 10$ kg, tumbling-average area 0.06 m², $C_D = 2.2$) is to be deployed at 500 km. Using the method of §7.3.3 with densities of $2 \times 10^{-13}$, $5 \times 10^{-13}$ and $2 \times 10^{-12}$ kg/m³ (solar minimum, mean, maximum), estimate the lifetime in each case. Does the mission comply with the FCC 5-year rule without a deorbit device? What would you recommend?

5. **Rule of thumb versus physics.** Apply the Chapter 3 §3.6.4 rule of thumb to the 400 km, 4 kg, 0.03 m² case and compare with the §7.3.3 result. Over what altitude range do the two agree to within a factor of two, and why does the rule fail at low altitude?

6. **Deorbit ΔV.** Compute the single-burn deorbit ΔV from 500 km and from 700 km to a 200 km perigee. If the spacecraft instead carries a drag sail that raises its area from 0.03 m² to 1.0 m², estimate the new lifetime at 700 km (take $\rho \approx 2 \times 10^{-14}$ kg/m³ and $H \approx 90$ km) and compare the two deorbit strategies in terms of mass and risk.

7. **Coverage.** A single satellite at 500 km carries an imager with a 3° half-cone angle. Compute the swath, the ground-track spacing, and the approximate equatorial revisit time. How many evenly phased satellites would be needed for a two-day revisit?

8. **Contact time.** For a 400 km orbit and a station with a 5° elevation mask, compute the maximum pass duration. If the average pass is about 60 % of the maximum and the station sees five passes per day, how many minutes of contact are available daily, and (anticipating Chapter 11) what data rate would be needed to downlink 500 MB per day?

9. **Orbit scoring.** Define a weighted scoring scheme (weights summing to 1) over GSD, revisit, lifetime/debris compliance, radiation and launch cost, and score three candidate orbits (400 km ISS, 500 km SSO, 700 km SSO) for (a) an optical Earth-observation mission and (b) a magnetometer science mission like UniSat-1. Explain why the winning orbit differs, and what happens to the ranking if the lifetime weight is doubled.

## References

1. Vallado, D., *Fundamentals of Astrodynamics and Applications*, 4th ed., 2013, Ch. 2–6, 9. https://celestrak.org/software/vallado-sw.php
2. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 5–7. https://www.space.com/smad
3. Curtis, H., *Orbital Mechanics for Engineering Students*, 4th ed., 2020, Ch. 2–4. https://www.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-08-102133-0
4. NASA, *Systems Engineering Handbook*, 2016, §4.4 (Process 4: Design Solution Definition). https://www.nasa.gov/reference/systems-engineering-handbook/
5. ECSS, *ECSS-E-ST-10-04C Rev.1: Space Environment*, 2020. https://ecss.nl/standard/ecss-e-st-10-04c-rev-1-space-environment-15-june-2020/
6. ECSS, *ECSS-U-AS-10C Rev.2: Space Debris Mitigation Requirements*, 2023. https://ecss.nl/standard/ecss-u-as-10c-rev-2-space-debris-mitigation-requirements/
7. IADC, *Space Debris Mitigation Guidelines*, IADC-02-01 Rev 3, 2021. https://www.iadc-home.org/documents_public/
8. FCC, *Report and Order FCC 22-74: Space Innovation (5-year rule)*, 2022. https://www.fcc.gov/document/fcc-adopts-new-5-year-rule-deorbiting-satellites
9. Wertz, J. R., *Mission Geometry: Orbit and Constellation Design and Management*, 2001 (eclipse geometry, eq. 5.24). https://www.springer.com
10. Picone, Hedin, Drob & Aikin, "NRLMSISE-00 empirical model of the atmosphere," *J. Geophys. Res.* 107, 2002. https://doi.org/10.1029/2002JA009430
