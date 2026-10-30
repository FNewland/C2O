# Part V — First-Principles Derivations

This part derives, from first principles, the formulas applied in Parts I–III. Every derivation is paired with a worked sanity check against a published reference value, and — where the chapters do not already show it — with a plot of the formula in action.

The aim is twofold: (a) to give the reader a place to look up the *why* behind any formula they are applying; (b) to provide a worked verification trail that a reviewer can audit at a design review. Where the same equation appears in a chapter of Parts I–III, the derivation here uses exactly the symbols of that chapter, so that the two can be read side by side.

> **Standard reference.** The constants and conventions used throughout this part follow Vallado, *Fundamentals of Astrodynamics and Applications* (4th ed.) and the IERS Conventions 2010 — [https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html](https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html).

---

## V.1 — Constants used (Earth)

| Symbol | Value | Meaning | Source |
|--------|-------|---------|--------|
| $\mu$ | 398 600.44 km³/s² | Earth gravitational parameter | IERS Conventions 2010 |
| $R_E$ | 6378.137 km | Earth equatorial radius | WGS-84 |
| $J_2$ | 1.0826 × 10⁻³ | Earth oblateness coefficient | Vallado §3.3 |
| $\omega_E$ | 7.292 115 × 10⁻⁵ rad/s | Earth rotation rate | IERS |
| $g_0$ | 9.806 65 m/s² | Standard gravity | ISO 80000-3 |
| $S$ | 1361 W/m² | Solar constant at 1 AU | Kopp and Lean (2011); NASA SORCE |
| $\sigma$ | 5.670 374 × 10⁻⁸ W/(m²·K⁴) | Stefan–Boltzmann constant | CODATA 2018 |
| $k_B$ | 1.380 649 × 10⁻²³ J/K | Boltzmann constant | CODATA 2018 |
| $k$ | −228.6 dBW/K/Hz | Boltzmann constant in link-budget units, $10\log_{10} k_B$ | derived |
| $c$ | 2.997 924 58 × 10⁸ m/s | Speed of light | exact (SI) |

These are the values used in every worked number in Parts I–III. In particular, all orbital quantities use $R_E = 6378.137$ km; older references that use a mean radius of 6371 km give periods about 0.1 min shorter at LEO altitudes.

---

## V.2 — Kepler's Third Law

### Derivation

For a circular orbit of radius $a$, centripetal acceleration equals gravitational attraction:

$$ \frac{v^2}{a} = \frac{\mu}{a^2} $$

Substitute $v = 2\pi a / T$ and solve for $T$:

$$ T = 2\pi \sqrt{\frac{a^3}{\mu}} $$

For elliptical orbits the same formula applies with $a$ the semi-major axis. The circular velocity is $v = \sqrt{\mu/a}$. These are the forms used in Chapter 7 §7.1.1.

### Verification

Figure D.1 overplots the analytical curve with the periods of known orbits.

![Kepler's Third Law verified against known orbits.](../assets/figures/fig_kepler_proof.png)

**Figure D.1** — The analytical period–altitude curve overplotted with known orbits (ISS, Sentinel-2, GPS, GEO). Agreement is to better than 0.5 %, the remaining error attributable to the $J_2$ secular correction not applied here. At GEO, $T = 1436$ min against the sidereal day of 23.93 h × 60 = 1436 min.

**Worked sanity check.** For a 450 km Sun-synchronous orbit:

$a = 6378.137 + 450 = 6828.137$ km;
$a^3/\mu = 6828.137^3 / 398\,600.44 = 7.987 \times 10^5$ s²; $\sqrt{\,\cdot\,} = 893.7$ s;
$T = 2\pi \times 893.7 = 5615$ s $= 93.6$ min.

The same arithmetic at 500 km gives $a = 6878.137$ km and $T = 94.6$ min, and at 400 km gives 92.6 min — the values used throughout Chapter 7 and the subsystem chapters. Expressed as a mean motion, 93.6 min is 15.38 revolutions per day; the slightly lower figures quoted in two-line element sets for real spacecraft at this altitude (≈ 15.2–15.3 rev/day) reflect the $J_2$ perturbation of the nodal period, not an error in the formula.

---

## V.3 — Tsiolkovsky Rocket Equation

### Derivation

For a rocket with constant exhaust velocity $v_e$, momentum conservation between time $t$ and $t + dt$ gives

$$ m\, dv = -v_e\, dm $$

Integrate from $m_0$ (initial total mass) to $m_f$ (final dry mass):

$$ \Delta V = v_e \ln \frac{m_0}{m_f} = I_{sp}\, g_0\, \ln \frac{m_0}{m_f} $$

since $v_e = I_{sp}\, g_0$ by the definition of specific impulse. The propellant mass follows as $m_p = m_f\,(e^{\Delta V/(I_{sp} g_0)} - 1)$ and the total impulse as $I_{tot} = m_p\, I_{sp}\, g_0$. Chapter 12 §12.2.2 applies the equation and Figure 12.2 plots $\Delta V$ against mass ratio for representative specific impulses.

### Verification

**Worked sanity check.** Hohmann transfer from a 400 km circular orbit to GEO (the case plotted in Chapter 7 Figure 7.4):

$r_1 = 6778.137$ km, $r_2 = 42\,164$ km, $a_t = (r_1 + r_2)/2 = 24\,471$ km.

At perigee: $v_1 = \sqrt{\mu/r_1} = 7.669$ km/s; $v_p = \sqrt{\mu\,(2/r_1 - 1/a_t)} = 10.066$ km/s; $\Delta V_1 = 2.397$ km/s.

At apogee: $v_2 = \sqrt{\mu/r_2} = 3.075$ km/s; $v_a = \sqrt{\mu\,(2/r_2 - 1/a_t)} = 1.618$ km/s; $\Delta V_2 = 1.456$ km/s.

Total $\Delta V = 3.854$ km/s — matching Figure 7.4 (≈ 3.85 km/s); the rounded components sum to 3.853 km/s. For the deorbit case of Chapter 12 §12.2.5 (600 km circular to a 200 km perigee) the same vis-viva arithmetic gives 112 m/s.

---

## V.4 — $J_2$ Nodal Regression

### Derivation

The dominant secular perturbation from Earth's oblateness $J_2$ produces a nodal regression rate (Vallado eq. 9-37):

$$ \dot{\Omega} = -\frac{3}{2}\, n\, J_2\, \left(\frac{R_E}{a(1-e^2)}\right)^2 \cos i $$

where $n = \sqrt{\mu/a^3}$ is the mean motion. The minus sign means the node regresses for prograde orbits ($\cos i > 0$) and progresses for retrograde orbits ($\cos i < 0$).

### Sun-synchronous condition

For a Sun-synchronous orbit, set $\dot{\Omega}$ equal to Earth's mean motion around the Sun (360°/365.25 days = 0.9856°/day = 1.991 × 10⁻⁷ rad/s):

$$ \cos i_{SSO} = -\frac{2\, \dot{\Omega}_\odot\, a^{7/2}\, (1-e^2)^2}{3\, J_2\, R_E^2\, \sqrt{\mu}} $$

This is the condition applied in Chapter 7 §7.3.4.

### Verification

Figure D.2 shows the regression rate against inclination for several altitudes.

![J₂ nodal regression rate versus inclination at several altitudes.](../assets/figures/fig_j2_nodal.png)

**Figure D.2** — Nodal regression rate $\dot{\Omega}$ as a function of inclination for several altitudes. The dashed horizontal at 0.9856°/day is the Sun-synchronous target; its intersection with each altitude curve gives the Sun-synchronous inclination at that altitude (≈ 98.2° at 700 km).

**Worked sanity check.** For 700 km circular ($e = 0$):

$a = 7078.137$ km; $n = \sqrt{398\,600.44 / 7078.137^3} = 1.060 \times 10^{-3}$ rad/s;
$\dot{\Omega}_\odot = 2\pi/(365.25 \times 86\,400) = 1.991 \times 10^{-7}$ rad/s;
$\cos i = -(2 \times 1.991 \times 10^{-7} \times 7078.137^{7/2}) / (3 \times 1.0826 \times 10^{-3} \times 6378.137^2 \times \sqrt{398\,600.44}) = -0.143$;
$i = \arccos(-0.143) = 98.2°$.

At 600 km the same calculation gives 97.8°, and at 500 km 97.4° — the Chapter 7 values.

---

## V.5 — Eclipse Fraction (analytical, circular orbit)

### Derivation

For a circular orbit of altitude $h$, the spacecraft is in eclipse when the line to the Sun is occulted by the Earth (the cylindrical-shadow approximation, which neglects the penumbra). Let $\beta$ be the angle between the Sun vector and the orbit plane. Seen from the orbit, the Earth subtends a half-angle $\beta^* = \arcsin\!\big(R_E/(R_E+h)\big)$; for $|\beta| \ge \beta^*$ the orbit never crosses the shadow.

For $|\beta| < \beta^*$, project the geometry onto the orbit plane. The shadow cylinder of radius $R_E$ cuts the orbit plane in an ellipse whose semi-minor axis (across the Sun line) is $R_E$ and whose semi-major axis (along the Sun line) is $R_E/\cos\beta$. The spacecraft, at radius $R_E + h$, is in shadow over the arc of orbit angle $2\phi$ for which its across-Sun-line distance is less than $R_E$ and its along-Sun-line position is on the anti-Sun side; solving the ellipse intersection gives

$$ \cos\phi = \frac{\sqrt{h^2 + 2 R_E h}}{(R_E + h)\cos\beta} $$

and hence the eclipse fraction of the orbit period (Wertz, *Mission Geometry*, eq. 5-24):

$$ f_{ecl} = \frac{1}{\pi}\, \arccos\!\left(\frac{\sqrt{h^2 + 2 R_E h}}{(R_E + h) \cos\beta}\right), \qquad |\beta| < \beta^* $$

with $f_{ecl} = 0$ for $|\beta| \ge \beta^*$. This is the form given in Chapter 7 §7.1.2.

**Corollary ($\beta = 0$).** With the Sun in the orbit plane the argument becomes $\sqrt{h^2 + 2R_E h}/(R_E+h) = \cos\beta^*$, so

$$ f_{ecl,max} = \frac{\beta^*}{\pi} = \frac{1}{\pi}\arcsin\!\left(\frac{R_E}{R_E + h}\right) $$

— the maximum-eclipse case used for power and thermal sizing (Chapter 7 presents this as the corollary; Chapter 9 §9.2–§9.3 use it). The eclipse duration is $t_{ecl} = f_{ecl}\,T$.

### Verification

The annual $\beta$ envelope and the eclipse-fraction curves for an ISS-like orbit and a 600 km Sun-synchronous orbit are plotted in Chapter 7 Figure 7.2: both show the characteristic plateau at low $|\beta|$ and the sharp transition at $\beta^*$.

**Worked sanity check.** ISS-like orbit, $h = 400$ km, $\beta = 0$:

$\beta^* = \arcsin(6378.137 / 6778.137) = \arcsin(0.9410) = 70.2°$;
$h^2 + 2 R_E h = 160\,000 + 5\,102\,510 = 5\,262\,510$ km²; $\sqrt{\,\cdot\,} = 2294.0$ km;
argument $= 2294.0 / 6778.137 = 0.3384$; $\arccos(0.3384) = 70.2° = 1.2256$ rad;
$f_{ecl} = 1.2256/\pi = 0.390 \approx 39\,\%$.

This agrees with the corollary ($\beta^*/\pi = 70.2°/180° = 0.390$) and with the observed ISS maximum eclipse fraction of about 39 % (≈ 36 min of a 92.6 min orbit). At 500 km the same calculation gives $f_{ecl,max} = 0.378$, $t_{ecl} = 35.8$ min — the EOSat-3U values of Chapter 7 §7.2 and Chapter 9.

---

## V.6 — Free-Space Path Loss

### Derivation

An isotropic radiator of power $P_t$ at distance $d$ produces a power flux $P_t / (4\pi d^2)$. A receiving antenna of effective aperture $A_e$ captures $A_e$ times the flux, and antenna theory relates aperture to gain by $A_e = G_r \lambda^2 / (4\pi)$. With a directional transmit antenna of gain $G_t$ the received power is the Friis transmission equation:

$$ P_r = P_t\, G_t\, G_r \left(\frac{\lambda}{4 \pi d}\right)^2 $$

The free-space path loss is the inverse of the geometric term, in decibels:

$$ \text{FSPL} = 20 \log_{10}\!\left(\frac{4 \pi d}{\lambda}\right) = 20 \log_{10}\!\left(\frac{4 \pi d f}{c}\right)\ \text{dB} $$

No energy is absorbed: the $d^2$ term is spherical spreading and the $\lambda^2$ term is the shrinking capture area of a fixed-gain antenna at higher frequency. Each doubling of $d$ or of $f$ adds 6.02 dB. Chapter 11 §11.4 and Figure 11.3 plot the loss by band against slant range.

### Verification

**Worked sanity check.** S-band (2.2 GHz) at 1500 km slant range:

$\lambda = c/f = 2.998 \times 10^8 / 2.2 \times 10^9 = 0.1363$ m;
$\text{FSPL} = 20\log_{10}(4\pi \times 1.5 \times 10^6 / 0.1363) = 20\log_{10}(1.383 \times 10^8) = 162.8$ dB.

For the EOSat-3U worked case of Chapter 11 §11.8 (2.25 GHz, 1695 km slant range at 10° elevation) the same formula gives 164.1 dB, which is the FSPL bar of the link-budget waterfall in Chapter 11 Figure 11.5.

---

## V.7 — Link-Budget Algebra

### Derivation

Write the Friis equation of V.6 in decibels and collect the transmitter terms into the effective isotropic radiated power, $\text{EIRP} = P_{TX} + G_{TX} - L_{TX}$ (dBW). Adding the losses that free space does not include — atmospheric absorption $L_{atm}$, antenna mispointing $L_{point}$, polarisation mismatch $L_{pol}$ and the receive-side feed and line loss $L_{rx}$ between the antenna and the point at which the system noise is referenced — the received carrier power is

$$ C = \text{EIRP} - \text{FSPL} - L_{atm} - L_{point} - L_{pol} - L_{rx} + G_{RX} \quad \text{(dBW)} $$

The noise power spectral density at the same reference point is $N_0 = k_B T_{sys}$ (W/Hz), or in decibels $N_0 = k + 10\log_{10} T_{sys}$ with $k = 10\log_{10}(1.380\,649 \times 10^{-23}) = -228.6$ dBW/K/Hz. Subtracting, and grouping the receive gain with the noise temperature into the figure of merit $G/T = G_{RX} - 10\log_{10} T_{sys}$ (dB/K), gives the canonical form of Chapter 11 §11.2:

$$ \frac{C}{N_0} = \text{EIRP} - \text{FSPL} - L_{atm} - L_{point} - L_{pol} - L_{rx} + G/T - k \quad \text{(dBHz)} $$

(Note the sign: subtracting a negative $k$ adds 228.6 dB.) The energy per bit follows by dividing by the bit rate, $E_b/N_0 = C/N_0 - 10\log_{10} R_b$, and the required $E_b/N_0$ depends on the modulation and coding (V.8, Figure 11.4). The link margin is

$$ \text{Margin} = (E_b/N_0)_{available} - (E_b/N_0)_{required} - L_{impl} $$

where $L_{impl}$ is the modem implementation loss. ECSS-E-ST-50-05C calls for at least 3 dB from Phase B onward; a 6 dB target is common in Phase A while the design is still fluid.

### Verification

The S-band waterfall of Chapter 11 Figure 11.5 (2 W transmitter, 6 dBi patch antenna, 2.25 GHz over 1695 km, 3 m ground dish at 150 K) reads left to right exactly as the equation above: gains add, losses subtract, and the final received $C/N_0$ closes at 83.4 dBHz against the 73.0 dBHz required at 5 Mbit/s, leaving the 10.4 dB margin. The EOSat-3U budget of Chapter 11 §11.8.1 is the same calculation line by line (EIRP 7.5 dBW, FSPL 164.1 dB, $C/N_0 = 83.4$ dBHz, margin 10.4 dB at 5 Mbit/s).

---

## V.8 — $E_b/N_0$ versus BER

### Derivation

For coherent BPSK over an additive white Gaussian noise channel, the bit-error probability is

$$ P_b = \frac{1}{2}\,\mathrm{erfc}\!\left(\sqrt{\frac{E_b}{N_0}}\right) $$

For QPSK with Gray coding the same expression applies per bit. For 8-PSK:

$$ P_b \approx \frac{2}{3}\, Q\!\left(\sqrt{2 \tfrac{E_b}{N_0}}\, \sin\!\frac{\pi}{8}\right) $$

For non-coherent FSK:

$$ P_b = \frac{1}{2}\,e^{-E_b/(2 N_0)} $$

Chapter 11 §11.6 and Figure 11.4 plot these curves together with a representative concatenated (convolutional + Reed–Solomon) coded curve, whose horizontal offset from the uncoded curve at a given BER is the coding gain — about 5 dB at BER $10^{-5}$ for that scheme, more for LDPC codes.

### Verification

**Sanity check.** BPSK at $E_b/N_0 = 9.6$ dB:

$P_b = 0.5 \times \mathrm{erfc}(\sqrt{10^{0.96}}) = 0.5 \times \mathrm{erfc}(3.02) = 0.5 \times 1.9 \times 10^{-5} \approx 9.5 \times 10^{-6}$.

The standard textbook value is $10^{-5}$ at 9.6 dB; the small difference is the resolution of the plot grid.

---

## V.9 — Ground Sample Distance Geometry

### Derivation (diffraction limit)

For an unobstructed circular aperture of diameter $D$, the first minimum of the Airy pattern lies at the half-angle

$$ \theta_{Airy} = 1.22\, \frac{\lambda}{D} $$

Projected onto the ground at range $h$ (nadir viewing from altitude $h$):

$$ \text{GSD}_{diff} = \theta_{Airy}\, h = 1.22\, \frac{\lambda\, h}{D} $$

### Derivation (pixel limit)

A detector pixel of pitch $p$ at the focal plane subtends an angle $p/f$, where $f$ is the focal length. Projected at range $h$:

$$ \text{GSD}_{pix} = \frac{p\, h}{f} $$

The achievable GSD is the *larger* of the two — the system cannot resolve better than the optics allow, nor better than the detector samples. Matching the two (so that $p/f \approx 1.22\lambda/D$, i.e. an f-number of about $p/(1.22\lambda)$) is the design condition the Payload Lead briefing of Part IV warns about. Off-nadir, replace $h$ by the slant range.

### Verification

Figure D.3 plots both limits against aperture diameter.

![GSD versus aperture diameter — diffraction and pixel limits.](../assets/figures/fig_gsd.png)

**Figure D.3** — Ground sample distance against aperture diameter for visible imagers ($\lambda = 550$ nm) at four altitudes, with the diffraction limit as solid curves and the pixel limit at 500 km (6 µm pitch, $f/D = 5$) as the dashed line. Sentinel-2 heritage at 786 km: the diffraction limit for a 0.135 m aperture is ≈ 3.9 m, consistent with the published 10 m bands once the detector pitch and f-number are accounted for.

**Worked sanity check.** A 3U CubeSat imager with $D = 90$ mm at $h = 500$ km: $\text{GSD}_{diff} = 1.22 \times 550 \times 10^{-9} \times 5 \times 10^5 / 0.09 = 3.7$ m; with $p = 5.5$ µm and $f = 500$ mm, $\text{GSD}_{pix} = 5.5 \times 10^{-6} \times 5 \times 10^5 / 0.5 = 5.5$ m — pixel-limited, so the achievable GSD is 5.5 m.

---

## V.10 — Radiative Thermal Equilibrium

### Derivation

Energy balance for a flat plate in steady state:

Absorbed = Emitted.
Absorbed = $\alpha_s\, S_{eff} + \varepsilon\, \phi_{IR}$ (solar input at the orbit-average effective flux $S_{eff}$, plus the Earth-IR contribution, absorbed at the IR emittance by Kirchhoff's law).
Emitted = $\varepsilon\, \sigma\, T^4$ per unit radiating area.

Solving for the equilibrium temperature:

$$ T_{eq} = \left(\frac{\alpha_s\, S_{eff} + \varepsilon\, \phi_{IR}}{\sigma\, \varepsilon}\right)^{1/4} $$

The ratio $\alpha_s/\varepsilon$ is the dominant design knob. Chapter 9 §9.4 gives the full balance with the albedo term, view factors and internal dissipation, and Figure 9.6 plots $T_{eq}$ against $\alpha_s/\varepsilon$ with common coatings marked.

### Verification

**Worked sanity check.** A white-painted radiator, $\alpha_s = 0.15$, $\varepsilon = 0.92$ ($\alpha_s/\varepsilon = 0.163$), one-sided, orbit-averaged at $\beta = 0$:

solar: $S_{eff} \approx 1361/4 = 340$ W/m², absorbed $0.15 \times 340 = 51$ W/m²;
Earth IR: $\phi_{IR} \approx 230/2 = 115$ W/m² seen by a nadir-facing plate at LEO, absorbed $0.92 \times 115 = 106$ W/m²;
total absorbed = 157 W/m²;
$T_{eq} = (157 / (0.92 \times 5.670 \times 10^{-8}))^{1/4} = (3.01 \times 10^9)^{1/4} = 234$ K $= -39$ °C.

This matches Figure 9.6 at $\alpha_s/\varepsilon \approx 0.16$. The same balance with $\alpha_s/\varepsilon \approx 5$ (bare polished aluminium) gives roughly +120 °C — the reason bare metal is never left facing the Sun.

---

## V.11 — Solar Array Sizing

### Derivation

Consider one orbit of period $T = t_{sun} + t_{ecl}$. The array generates only during the sunlit arc $t_{sun}$; the loads run throughout. Let $P_{sun}$ be the peak sunlit-mode demand and $P_{ecl}$ the eclipse demand. Energy delivered to the loads over the orbit must be supplied by the array, through two paths of different efficiency: the direct array-to-load path in sunlight ($\eta_{sun}$, the regulator alone) and the array-to-battery-to-load path for the eclipse energy ($\eta_{ecl} = \eta_{charge}\,\eta_{discharge}\,\eta_{regulator}$). The energy balance over one orbit is therefore

$$ P_{SA,EOL}\, t_{sun} = \frac{P_{sun}\, t_{sun}}{\eta_{sun}} + \frac{P_{ecl}\, t_{ecl}}{\eta_{ecl}} $$

and, dividing by $t_{sun}$,

$$ P_{SA,EOL} = \frac{\dfrac{P_{sun}\, t_{sun}}{\eta_{sun}} + \dfrac{P_{ecl}\, t_{ecl}}{\eta_{ecl}}}{t_{sun}} $$

— the array power required at end of life (Chapter 9 §9.2, step 2). The array must deliver this at end of life, so the beginning-of-life rating is higher by the radiation degradation factor $L_d = (1-\delta)^n$ and the temperature derating $L_T = 1 + \beta_T (T_{cell} - T_{ref})$ (the cell temperature coefficient is written $\beta_T$ to avoid confusion with the orbit $\beta$-angle):

$$ P_{SA,BOL} = \frac{P_{SA,EOL}}{L_d\, L_T} $$

Finally the cells convert the solar flux $S$ at efficiency $\eta_{cell}$, reduced by the cosine of the Sun incidence angle $\theta$ on the array, the packing factor $f_{pack}$ and the cover-glass transmission $f_{cover}$:

$$ A_{SA} = \frac{P_{SA,BOL}}{\eta_{cell}\, S\, \cos\theta\, f_{pack}\, f_{cover}} $$

Here $\theta$ is the angle between the array normal and the Sun vector — zero for a Sun-tracking array; for a body-fixed panel on a nadir-pointed spacecraft it is set by the orbit $\beta$-angle (a panel whose normal is perpendicular to the orbit plane sees $\theta = 90° - |\beta|$ constantly; a zenith panel sees $\cos\theta = \cos\beta\cos\nu$ varying through the sunlit arc, so its sunlit-arc average is used). Chapter 9 §9.2 states the same chain and works the EOSat-3U numbers.

### Equivalence to the eclipse-fraction form

Many references write the sizing in terms of the eclipse fraction $f_{ecl} = t_{ecl}/T$ and sunlit fraction $f_{sun} = t_{sun}/T$, with a single orbit-average load $P_{avg}$ and a single degradation factor. Set $P_{sun} = P_{ecl} = P_{avg}$, absorb the sunlit-path efficiency into the load ($\eta_{sun} \to 1$), write $\eta_{ecl} \to \eta_{dis}$, and divide numerator and denominator of the first equation by $T$:

$$ P_{SA} = P_{avg}\left(1 + \frac{f_{ecl}}{f_{sun}\, \eta_{dis}}\right) $$

and, with $L_d L_T \to (1 - D_{deg})$ and $f_{pack} f_{cover}$ absorbed into $\eta_{cell}$,

$$ A_{SA} = \frac{P_{avg}\left(1 + \dfrac{f_{ecl}}{f_{sun}\,\eta_{dis}}\right)}{S\, \eta_{cell}\, \cos\theta\, (1 - D_{deg})} $$

The two forms are the same energy balance. The Chapter 9 form is preferred because it separates the peak sunlit mode from the eclipse mode (the array must cover the worst sunlit mode, not the average) and because it keeps the two path efficiencies distinct.

### Verification

The sizing nomograph of Chapter 9 Figure 9.3 is drawn in the eclipse-fraction form ($\eta_{cell} = 30$ %, 10 % EOL degradation, $\theta = 20°$, $\eta_{dis} = 85$ %): a 6U at 15 W orbit-average load needs about 870 cm² at end of life.

**Worked check.** $P_{sun} = P_{ecl} = 15$ W, $t_{ecl}/t_{sun} = 0.35/0.65 = 0.538$, $\eta_{sun} = 1$, $\eta_{ecl} = 0.85$:

$P_{SA} = 15 + 15 \times 0.538 / 0.85 = 15 + 9.5 = 24.5$ W during the sunlit arc;
$A_{SA} = 24.5 / (1361 \times 0.30 \times \cos 20° \times 0.90) = 24.5 / 345.0 = 0.071$ m² $= 710$ cm².

The nomograph reads about 870 cm² because it is drawn for orbit-averaged rather than sunlit-arc generation, the more conservative convention; the two agree to within that modelling choice. The EOSat-3U case of Chapter 9 §9.2 — $P_{sun} = 10$ W, $P_{ecl} = 3.5$ W, $t_{sun} = 58.8$ min, $t_{ecl} = 35.8$ min, $\eta_{sun} = 0.90$, $\eta_{ecl} = 0.786$ — gives $P_{SA,EOL} = 13.8$ W, $P_{SA,BOL} = 16.0$ W and $A_{SA} = 0.0526$ m².

---

## V.12 — Battery Sizing

### Derivation

The energy drawn from the battery during one eclipse is $E_{ecl} = P_{ecl}\, t_{ecl}$. The battery must supply this through the discharge path (efficiency $\eta_{dis}$) while using only the fraction DoD of its rated capacity, so that it reaches the required cycle life:

$$ E_{bat} = \frac{P_{ecl}\, t_{ecl}}{\text{DoD}\, \eta_{dis}} $$

— the form of Chapter 9 §9.3. The rated capacity in ampere-hours is $C = E_{bat} / V_{bus}$, and the mass follows from the specific energy of the chemistry. The cycle count is the number of eclipses over the mission (≈ 15 per day in LEO, about 5500 per year), which, through the cycle-life-versus-DoD curves of Chapter 9 Figure 9.4, sets the permissible DoD.

### Verification

**Worked check.** EOSat-3U, $P_{ecl} = 3.5$ W, $t_{ecl} = 35.8$ min $= 0.597$ h, DoD $= 25$ %, $\eta_{dis} = 0.95$:

$E_{bat} = 3.5 \times 0.597 / (0.25 \times 0.95) = 2.09 / 0.2375 = 8.8$ Wh,

as in Chapter 9 §9.3, where the requirement is rounded up with margin and a 20 Wh pack is selected. A three-year mission at 15 eclipses per day is about 16 000 cycles; Figure 9.4 shows that NCA/NMC cells reach this at 25–30 % DoD with margin, whereas heritage LCO cells need a shallower DoD.

---

## V.13 — Margin of Safety (structures)

The structural margin of safety compares the allowable stress with the applied stress multiplied by the factor of safety:

$$ \text{MoS} = \frac{\sigma_{allow}}{\text{FoS} \cdot \sigma_{applied}} - 1 $$

A positive margin is compliant; zero is exactly at the allowable with the factor applied; negative is a failure of the requirement. Chapter 12 §12.1.6 is the canonical treatment (Chapter 3 §3.3.3 and Chapter 14 defer to it) and gives the ECSS-E-ST-32-10C factors.

**Worked check.** Al 7075-T6, yield allowable $\sigma_{yield} = 503$ MPa, yield factor of safety 1.25, applied stress 200 MPa:

$\text{MoS} = 503 / (1.25 \times 200) - 1 = 1.012$,

i.e. 100 % positive margin. Compliant. (For the 3U box-beam of Chapter 12 §12.1 the first natural frequency, $f_1 \approx 330$ Hz, is checked separately against the 100 Hz requirement.)

---

## V.14 — Disturbance Torque Order-of-Magnitude

### Derivation (aerodynamic drag)

The drag force on an exposed area $A_{ref}$ is $\tfrac{1}{2}\rho V^2 C_D A_{ref}$; it acts at the centre of pressure, offset from the centre of mass by a lever arm $\ell$, giving the torque

$$ T_{drag} = \tfrac{1}{2}\,\rho\, V^2\, C_D\, A_{ref}\, \ell $$

where $\rho$ is the atmospheric density, $V$ the orbital velocity and $C_D \approx 2.2$. Chapter 10 §10.2 gives the companion expressions for gravity gradient, magnetic and solar-pressure torques and the EOSat-3U worked values.

**Worked estimate.** A 6U CubeSat at 500 km, $\rho \approx 6 \times 10^{-13}$ kg/m³ (mean solar activity), $V = 7.61$ km/s, $A_{ref} = 0.06$ m², $C_D = 2.2$, $\ell = 0.02$ m:

$T_{drag} \approx 0.5 \times 6 \times 10^{-13} \times 7610^2 \times 2.2 \times 0.06 \times 0.02 \approx 4.6 \times 10^{-8}$ N m.

With a 10 cm lever arm (a deployed panel far off the centre of mass) the figure is five times larger; across the solar cycle $\rho$ at 500 km varies by more than an order of magnitude either way, which is why Chapter 10 Figure 10.4 shows a band rather than a line.

### Verification

Chapter 10 Figure 10.4 shows the accumulated wheel momentum against orbits since the last desaturation, and the order-of-magnitude disturbance torques by source, for a spacecraft of a few tens of kilograms; the EOSat-3U values of Chapter 10 §10.2 are roughly a tenth of those, and for a 3U at 500 km the magnetic torque, not drag, dominates. The reaction-wheel momentum capacity follows as $H \ge T_{dist}\, t_{desat}\, k_{margin}$ (Chapter 10 §10.3 and §10.5).

---

## V.15 — Daily Data Volume Closure

The closure check between data generation (payload) and downlink capacity (communications) is a classic mission-design failure point. The payload generates $V_{gen} = R_{gen}\, t_{imaging}$ per day; the ground segment can receive, with $N_{passes}$ usable passes per day of average usable duration $t_{contact}$, at data rate $R$ and protocol efficiency $\eta_{protocol}$ (acknowledgements, framing, re-transmissions):

$$ C_{downlink} = R \cdot N_{passes} \cdot t_{contact} \cdot \eta_{protocol} $$

and the mission closes if

$$ V_{gen} \le C_{downlink} $$

This is the form of Chapter 11 §11.9. If the inequality fails, the options are a faster downlink (more bandwidth or a higher band), more stations or passes, on-board compression, or fewer images. Chapter 11 Figure 11.6 plots daily capacity by band against representative payload volumes: UHF closes only for housekeeping; S-band suits a multispectral imager; X-band is needed for SAR or hyperspectral data.

**Worked check.** EOSat-3U at 5 Mbit/s with five 6-minute passes per day and $\eta_{protocol} = 0.85$: $C = 5 \times 10^6 \times 5 \times 360 \times 0.85 / 8 = 956$ MB/day against 720 MB/day generated — closes (the case of Chapter 11 §11.9 and Chapter 17 §17.2.4). UniSat-1 at 4800 bit/s with five minutes of usable contact per pass to a single station: 0.61 MB/day against 1.13 MB/day generated — does not close (Chapter 11 §11.8.2, Chapter 17 §17.6).

---

## V.16 — Cross-method verification matrix

For a design review, every quantitative claim should be verified by at least two methods. The following matrix lists the two methods expected for each quantity derived in this part.

| Quantity | Method 1 | Method 2 | Derivation |
|----------|---------|---------|--------|
| Orbital period | Kepler (analytical) | Numerical propagation (GMAT or equivalent) | V.2 |
| SSO inclination | Analytical $J_2$ condition | Tabulated (SMAD4 Table 9-2) | V.4 |
| Eclipse fraction | Analytical β-form | Numerical eclipse model | V.5 |
| FSPL | $20\log_{10}(4\pi d/\lambda)$ | ITU-R P.525 | V.6 |
| Link budget | Spreadsheet, line by line | Concurrent-design tool or vendor link calculator | V.7 |
| GSD (diffraction) | $1.22\,\lambda h/D$ | Detailed optical ray-trace | V.9 |
| GSD (pixel) | $p\,h/f$ | Detector data sheet | V.9 |
| Thermal equilibrium | $\alpha_s/\varepsilon$ analytical | Thermal network model (ESATAN or equivalent) | V.10 |
| Solar-array area | Orbit energy balance | Vendor sizing tool | V.11 |
| Battery capacity | DoD and cycle-life curve | Vendor cycle test data | V.12 |
| Margin of safety | Hand calculation | Finite-element analysis | V.13 |
| Disturbance torque | First-principles estimate | Atmospheric model (NRLMSISE-00) with geometry | V.14 |
| Data budget | $R\,N_{passes}\,t_{contact}\,\eta$ | Pass-by-pass simulation with the station schedule | V.15 |

---

## V.17 — Key references

- **Vallado**, *Fundamentals of Astrodynamics and Applications*, 4th ed., Microcosm Press / Springer.
- **Curtis**, *Orbital Mechanics for Engineering Students*, 3rd ed., Butterworth-Heinemann.
- **Wertz**, *Mission Geometry: Orbit and Constellation Design and Management*, Microcosm Press.
- **Wertz, Everett and Puschell**, *Space Mission Engineering: The New SMAD*, 2011.
- **Larson and Wertz**, *Space Mission Analysis and Design*, 4th ed.
- **Pratt, Bostian and Allnutt**, *Satellite Communications*, 3rd ed.
- **Sutton and Biblarz**, *Rocket Propulsion Elements*, 9th ed.
- **Gilmore**, *Spacecraft Thermal Control Handbook*, Vol. I and II.
- **Sarafin**, *Spacecraft Structures and Mechanisms*.
- **Markley and Crassidis**, *Fundamentals of Spacecraft Attitude Determination and Control*.
- **Patel**, *Spacecraft Power Systems*.
- **Kopp and Lean**, "A new, lower value of total solar irradiance", *Geophysical Research Letters* 38, 2011.
- **NASA SEH (SP-2016-6105 Rev 2)** — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).
- **IERS Conventions 2010** — [https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html](https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html).
- **CODATA 2018 fundamental constants** — [https://physics.nist.gov/cuu/Constants/](https://physics.nist.gov/cuu/Constants/).
- **ITU-R P.525** (free-space attenuation) — [https://www.itu.int/rec/R-REC-P.525/en](https://www.itu.int/rec/R-REC-P.525/en).
- **NRLMSISE-00 atmospheric model** — [https://ccmc.gsfc.nasa.gov/models/NRLMSIS~00/](https://ccmc.gsfc.nasa.gov/models/NRLMSIS~00/).
- **NASA GMAT** — [https://software.nasa.gov/software/GSC-17177-1](https://software.nasa.gov/software/GSC-17177-1).
