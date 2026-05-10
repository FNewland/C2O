# Session 3.3: Communications and Link Budget Design

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--3.2 (requirements, orbit, power, AOCS defined)
**SpaceCDF Tabs:** Link Budget, Spectrum Selector, Equipment Browser (Comms)

---

## References

- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 13 (Communications)](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-50-05C: Radio Frequency and Modulation*, 2011](https://ecss.nl/standard/ecss-e-st-50-05c-radio-frequency-and-modulation/)
- [CCSDS, *131.0-B-4: TM Synchronization and Channel Coding*, 2023](https://public.ccsds.org/Pubs/131x0b4.pdf)
- [ITU, *Radio Regulations*, 2020 (Articles 5 and 22)](https://www.itu.int/en/publications/ITU-R/pages/default.aspx)
- [Maral & Bousquet, *Satellite Communications Systems*, 6th ed., 2020, Ch. 5](https://www.wiley.com/en-us/Satellite+Communications+Systems)
- [Roddy, *Satellite Communications*, 4th ed., 2006, Ch. 4--6](https://www.mhprofessional.com)
- [Haykin, *Communication Systems*, 5th ed., 2009](https://www.wiley.com)
- [Sklar, *Digital Communications: Fundamentals and Applications*, 2nd ed., 2001](https://www.pearson.com)
- [IARU, *Amateur Satellite Frequency Coordination*, 2023](https://www.iaru.org/satellite/)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Construct a complete link budget from first principles (in decibels)
2. Compute free space path loss for any frequency and slant range
3. Select an appropriate frequency band based on data rate, licensing, and equipment availability
4. Explain the physics of each antenna type and compute antenna gain and beamwidth
5. Choose modulation and coding scheme based on required $E_b/N_0$ and spectral efficiency
6. Explain the physical basis for coding gain and why FEC is essential for space links
7. Size an antenna (gain, beamwidth, mass) for the selected frequency
8. Determine data throughput and verify the data budget closes
9. Identify ground station options and compute contact geometry
10. Use SpaceCDF's link budget tool and spectrum selector

---

## 1. The Link Budget Concept (15 min)

### Teaching Notes

*[Source: SMAD, Ch. 13; ECSS-E-ST-50-05C; Roddy, Ch. 4]*

The link budget is the accounting statement for the communication link. Every gain and every loss from transmitter to receiver is tallied in **decibels (dB)** to determine whether the link "closes" -- meaning the received signal is strong enough to decode with acceptable error rate.

The fundamental question: **does the received signal have enough energy per bit, relative to the noise, to achieve the required bit error rate?** This is quantified by $E_b/N_0$ -- the ratio of energy per information bit to noise spectral density.

### Link Budget Flow

<svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" style="max-width:750px; font-family: sans-serif; font-size: 11px;">
  <!-- TX -->
  <rect x="20" y="60" width="100" height="80" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="70" y="85" text-anchor="middle" fill="#1e40af" font-weight="bold">Transmitter</text>
  <text x="70" y="100" text-anchor="middle" fill="#1e40af" font-size="9">P_TX (dBW)</text>
  <text x="70" y="115" text-anchor="middle" fill="#1e40af" font-size="9">G_TX (dBi)</text>
  <text x="70" y="130" text-anchor="middle" fill="#1e40af" font-size="9">L_TX (dB)</text>
  <!-- EIRP label -->
  <rect x="145" y="80" width="70" height="30" rx="4" fill="#fef3c7" stroke="#d97706"/>
  <text x="180" y="100" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="10">EIRP</text>
  <line x1="120" y1="100" x2="145" y2="95" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Path -->
  <rect x="240" y="60" width="120" height="80" rx="6" fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
  <text x="300" y="85" text-anchor="middle" fill="#991b1b" font-weight="bold">Channel Losses</text>
  <text x="300" y="100" text-anchor="middle" fill="#991b1b" font-size="9">FSPL (dB)</text>
  <text x="300" y="115" text-anchor="middle" fill="#991b1b" font-size="9">Atmospheric (dB)</text>
  <text x="300" y="130" text-anchor="middle" fill="#991b1b" font-size="9">Pointing loss (dB)</text>
  <line x1="215" y1="100" x2="240" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- RX -->
  <rect x="390" y="60" width="110" height="80" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="445" y="85" text-anchor="middle" fill="#166534" font-weight="bold">Receiver</text>
  <text x="445" y="100" text-anchor="middle" fill="#166534" font-size="9">G_RX (dBi)</text>
  <text x="445" y="115" text-anchor="middle" fill="#166534" font-size="9">T_sys (K)</text>
  <text x="445" y="130" text-anchor="middle" fill="#166534" font-size="9">G/T (dB/K)</text>
  <line x1="360" y1="100" x2="390" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Result -->
  <rect x="530" y="60" width="120" height="80" rx="6" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="590" y="85" text-anchor="middle" fill="#3730a3" font-weight="bold">Demodulator</text>
  <text x="590" y="100" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 avail (dB)</text>
  <text x="590" y="115" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 req (dB)</text>
  <text x="590" y="130" text-anchor="middle" fill="#3730a3" font-size="9">Impl. loss (dB)</text>
  <line x1="500" y1="100" x2="530" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Margin -->
  <rect x="680" y="70" width="90" height="55" rx="6" fill="#d1fae5" stroke="#059669" stroke-width="3"/>
  <text x="725" y="93" text-anchor="middle" fill="#065f46" font-weight="bold" font-size="13">MARGIN</text>
  <text x="725" y="112" text-anchor="middle" fill="#065f46" font-size="11">>= 3 dB</text>
  <line x1="650" y1="100" x2="680" y2="97" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <defs><marker id="a3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#64748b"/></marker></defs>
</svg>

### Decibel Refresher

All link budget terms are in decibels to convert multiplication/division into addition/subtraction:

| Conversion | Formula | Example |
|-----------|---------|---------|
| Watts to dBW | $P_{\text{dBW}} = 10 \log_{10}(P_W)$ | 2 W = +3.0 dBW |
| Milliwatts to dBm | $P_{\text{dBm}} = 10 \log_{10}(P_{mW})$ | 1 W = +30 dBm |
| dBW to Watts | $P_W = 10^{P_{\text{dBW}}/10}$ | -3 dBW = 0.5 W |
| Ratio to dB | $G_{\text{dB}} = 10 \log_{10}(G)$ | Gain of 100 = 20 dB |
| dBW vs dBm | dBm = dBW + 30 | 0 dBW = 30 dBm |

**Common power values:**

| Power | dBW | dBm |
|-------|-----|-----|
| 0.1 W | -10.0 | +20.0 |
| 0.5 W | -3.0 | +27.0 |
| 1 W | 0.0 | +30.0 |
| 2 W | +3.0 | +33.0 |
| 5 W | +7.0 | +37.0 |
| 10 W | +10.0 | +40.0 |

---

## 2. Complete Link Budget Equation (25 min)

### Teaching Notes

> **Key Equations -- Link Budget (dB form)**
>
> **EIRP** (Effective Isotropic Radiated Power):
> $$\text{EIRP} = P_{TX} + G_{TX} - L_{TX} \quad \text{(dBW)}$$
>
> EIRP represents the power that an isotropic antenna would need to radiate to produce the same signal strength in the direction of maximum antenna gain. It combines the transmitter power, antenna gain (directivity), and cable/filter losses.
>
> **Free Space Path Loss:**
> $$\text{FSPL} = 20\log_{10}\left(\frac{4\pi d}{\lambda}\right) = 20\log_{10}\left(\frac{4\pi d f}{c}\right) \quad \text{(dB)}$$
> where $d$ = slant range (m), $f$ = frequency (Hz), $c = 3 \times 10^8$ m/s.
>
> **Physical interpretation:** FSPL is not "energy absorption" -- no energy is lost. It is the geometric spreading of radiated power over a sphere of radius $d$. An isotropic antenna radiates equally in all directions, so the power per unit area at distance $d$ is $P/(4\pi d^2)$. The $\lambda^2$ dependence arises because a receive antenna's effective aperture scales as $A_{\text{eff}} = G\lambda^2/(4\pi)$ -- at higher frequencies the receive antenna "captures" less of the available flux (unless the antenna is physically larger).
>
> **Receiver figure of merit:**
> $$G/T = G_{RX} - 10\log_{10}(T_{sys}) \quad \text{(dB/K)}$$
>
> $G/T$ is the single most important parameter of any receive station. It combines the antenna gain (signal capture) with the system noise temperature (noise floor). A high $G/T$ means good sensitivity.
>
> **System noise temperature** $T_{sys}$ includes:
> - Antenna noise temperature $T_A$ (depends on what the antenna "sees": sky ~10--50 K at zenith, ~150--300 K looking at Earth/ground)
> - Feed/cable losses: $T_{\text{feed}} = T_{\text{physical}} (L-1)$ where $L$ = loss factor
> - LNA noise temperature: $T_{\text{LNA}} = T_0 (F-1)$ where $F$ = noise figure, $T_0 = 290$ K
> - Subsequent stages (reduced by LNA gain)
>
> Rule of thumb: $T_{sys} \approx 100$--$200$ K for a professional ground station with cryogenic or low-noise LNA; $T_{sys} \approx 400$--$800$ K for an amateur station with COTS LNA.
>
> **Carrier-to-noise density ratio:**
> $$C/N_0 = \text{EIRP} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} + G/T - k \quad \text{(dBHz)}$$
> where $k = -228.6$ dBW/K/Hz (Boltzmann constant: $k = 1.381 \times 10^{-23}$ J/K).
>
> **Energy per bit to noise density:**
> $$E_b/N_0 = C/N_0 - 10\log_{10}(R_b) \quad \text{(dB)}$$
> where $R_b$ = data rate (bps). This is the fundamental quality metric: each bit needs a certain amount of energy ($E_b$) relative to the noise floor ($N_0$) to be correctly demodulated.
>
> **Link margin:**
> $$\text{Margin} = E_b/N_{0,\text{available}} - E_b/N_{0,\text{required}} - L_{\text{implementation}} \quad \text{(dB)}$$
>
> **Requirement:** Margin $\geq$ 3 dB for Phase B+ (per ECSS-E-ST-50-05C). This 3 dB margin covers:
> - Transmitter power variation (aging, temperature)
> - Antenna gain uncertainties
> - Atmospheric scintillation
> - Pointing error variations
> - Ground station performance variation

### Complete Link Budget Table

| Line | Parameter | Formula / Typical Value | Unit | Physical Meaning |
|------|-----------|------------------------|------|-----------------|
| 1 | TX Power | $P_{TX}$ (e.g., 2 W = +3.0) | dBW | RF power from amplifier output |
| 2 | TX Antenna Gain | $G_{TX}$ (e.g., +6.0 for patch) | dBi | Directivity relative to isotropic |
| 3 | TX Line Losses | $L_{TX}$ (cables, filters: -1.5) | dB | Ohmic loss in RF cables and connectors |
| 4 | **EIRP** | $= P_{TX} + G_{TX} - L_{TX}$ | dBW | Effective radiated power |
| 5 | Free Space Path Loss | $\text{FSPL} = 20\log_{10}(4\pi d f/c)$ | dB | Geometric spreading + aperture effect |
| 6 | Atmospheric Loss | $L_{\text{atm}}$ (-0.3 to -3.0) | dB | Molecular absorption (O$_2$, H$_2$O) |
| 7 | Pointing Loss | $L_{\text{point}}$ (-0.5 to -3.0) | dB | Signal reduction from antenna mispointing |
| 8 | Polarisation Loss | $L_{\text{pol}}$ (-0.1 to -3.0) | dB | Mismatch between TX and RX polarisation |
| 9 | RX Antenna Gain | $G_{RX}$ (e.g., +35 for 3 m dish) | dBi | Ground antenna directivity |
| 10 | System Noise Temp | $T_{sys}$ (e.g., 150 K = 21.8 dBK) | dBK | Total noise temperature of receive chain |
| 11 | **G/T** | $= G_{RX} - 10\log_{10}(T_{sys})$ | dB/K | Receiver figure of merit |
| 12 | Boltzmann Constant | $k = -228.6$ | dBW/K/Hz | Thermal noise power spectral density |
| 13 | **C/N$_0$** | $= \text{EIRP} - \text{FSPL} + G/T - k - L_{\text{losses}}$ | dBHz | Signal-to-noise density ratio |
| 14 | Data Rate | $10\log_{10}(R_b)$ | dBbps | Information throughput |
| 15 | **$E_b/N_0$ available** | $= C/N_0 - 10\log_{10}(R_b)$ | dB | Available energy per bit |
| 16 | $E_b/N_0$ required | From modulation/coding selection | dB | Minimum needed for target BER |
| 17 | Implementation Loss | Typically 1.5--2.5 dB | dB | Real vs ideal demodulator performance |
| 18 | **LINK MARGIN** | $= E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}}$ | dB | Must be $\geq$ 3 dB |

---

## 3. Antenna Types -- Physics and Selection (15 min)

### Teaching Notes

*[Source: SMAD, Ch. 13; Balanis, *Antenna Theory: Analysis and Design*, 4th ed., 2016]*

The antenna converts guided RF energy (in cables/waveguides) into radiated electromagnetic waves (and vice versa for receive). The key performance parameters are:

- **Gain** ($G$): How much more signal the antenna concentrates in its beam direction compared to an isotropic radiator. Higher gain = narrower beam = more signal but requires more precise pointing.
- **Beamwidth** ($\theta_{3\text{dB}}$): The angular width of the main beam between the -3 dB (half-power) points.
- **Polarisation:** Linear (vertical/horizontal), circular (RHCP/LHCP), or elliptical.

**Fundamental trade-off:** $G \propto 1/\theta_{3\text{dB}}^2$. A higher-gain antenna has a narrower beam and requires more precise pointing. For a spacecraft without accurate pointing, a low-gain omnidirectional antenna is mandatory. For a spacecraft with 0.1 deg pointing, a high-gain directional antenna is feasible.

### Antenna Types for Spacecraft

| Antenna Type | Gain (dBi) | Beamwidth | Pointing Needed? | Mass (CubeSat) | Physics |
|-------------|-----------|-----------|-------------------|----------------|---------|
| **Monopole/Dipole** | 0--2 | ~omnidirectional (toroidal pattern) | No | 5--20 g (deployable wire) | Current distribution on a wire radiates; $\lambda/4$ monopole on ground plane or $\lambda/2$ dipole | 
| **Turnstile** | 0--3 | Hemispherical | No | 10--30 g | Two crossed dipoles fed 90 deg apart; produces circular polarisation |
| **Patch (microstrip)** | 5--8 | 60--90 deg | Loose (~10 deg) | 10--50 g | Resonant conducting patch on dielectric substrate over ground plane; $\lambda/2$ patch at resonance |
| **Patch array (2x2, 4x4)** | 10--18 | 15--40 deg | Moderate (~5 deg) | 50--200 g | Multiple patch elements with corporate feed network; gain = $G_{\text{element}} + 10\log_{10}(N)$ |
| **Horn** | 15--25 | 10--25 deg | Yes (~2 deg) | 100--500 g | Flared waveguide; smooth aperture illumination gives low side lobes |
| **Parabolic reflector** | 25--45 | 1--5 deg | Yes (< 1 deg) | 500 g -- 5 kg | Feed at focal point illuminates parabolic dish; $G = \eta_a (\pi D/\lambda)^2$ |
| **Phased array** | 15--35 | Electronically steered, 1--30 deg | Electronic (no mechanical) | 200 g -- 2 kg | Array of elements with individual phase shifters; beam steered by adjusting relative phases; no moving parts |

**Monopole/dipole physics:** A quarter-wave monopole ($L = \lambda/4$) is the simplest antenna. At 437 MHz (UHF), $\lambda = 0.686$ m, so a monopole is 17.2 cm long -- easily deployable from a CubeSat using a spring-loaded tape measure or nitinol wire. The radiation pattern is omnidirectional in the azimuthal plane (perpendicular to the wire) and null along the wire axis. Gain is approximately 0--2 dBi depending on the ground plane size.

**Patch antenna physics:** A microstrip patch antenna consists of a conducting patch (typically rectangular, $L \approx \lambda/2$ at the desired frequency) printed on a dielectric substrate (e.g., Rogers RT/duroid, $\varepsilon_r = 2.2$--$10.2$, thickness 1--3 mm) above a ground plane. The patch resonates at the frequency where its length equals $\lambda_{eff}/2$ (where $\lambda_{eff} = \lambda_0/\sqrt{\varepsilon_r}$). At S-band (2.25 GHz), a patch is approximately 40 x 40 mm -- small enough to mount on a CubeSat face. Gain is typically 5--8 dBi with a hemispherical pattern. Circular polarisation is achieved by feeding two orthogonal modes 90 deg apart (dual-feed or corner-truncated patch).

**Parabolic reflector physics:** A parabolic dish focuses incoming plane waves to its focal point (for receive) or collimates spherical waves from a feed at the focus into a parallel beam (for transmit). The gain depends on the dish diameter $D$ and the wavelength $\lambda$:

> **Key Equations -- Antenna**
>
> **Gain of a parabolic antenna:**
> $$G = \eta_a \left(\frac{\pi D}{\lambda}\right)^2$$
>
> In dBi: $G_{\text{dBi}} = 10\log_{10}\left[\eta_a \left(\frac{\pi D}{\lambda}\right)^2\right]$
>
> where $\eta_a \approx 0.55$--$0.65$ (aperture efficiency, accounting for illumination taper, spillover, blockage, and surface errors), $D$ = antenna diameter (m), $\lambda = c/f$.
>
> **Half-power beamwidth (HPBW):**
> $$\theta_{3\text{dB}} \approx \frac{70\lambda}{D} \quad \text{(degrees)}$$
>
> **Patch antenna gain** (single element): typically 5--8 dBi, beamwidth ~60--90 deg
>
> **Patch array gain** ($N$ elements): $G_{\text{array}} = G_{\text{element}} + 10\log_{10}(N)$
>
> **Pointing loss** (when antenna is mispointed by angle $\Delta\theta$):
> $$L_{\text{point}} \approx -12 \left(\frac{\Delta\theta}{\theta_{3\text{dB}}}\right)^2 \quad \text{(dB)}$$
>
> This shows that a narrower beam (smaller $\theta_{3\text{dB}}$) is more sensitive to pointing errors.

**Worked example -- antenna gain at different bands for a 30 cm dish:**

| Band | Frequency | $\lambda$ (mm) | $D/\lambda$ | Gain (dBi) | HPBW (deg) | Pointing req |
|------|-----------|----------------|-------------|-----------|-----------|-------------|
| S-band | 2.25 GHz | 133 | 2.3 | 14.3 | 30 | ~5 deg |
| X-band | 8.4 GHz | 35.7 | 8.4 | 25.4 | 8.3 | ~1 deg |
| Ka-band | 26 GHz | 11.5 | 26.1 | 35.2 | 2.7 | ~0.3 deg |

This table illustrates the fundamental link between frequency, antenna size, gain, and pointing requirement. At Ka-band, even a small dish provides high gain -- but the beamwidth is so narrow that sub-degree pointing accuracy is essential. This is why Ka-band CubeSat links require star tracker + reaction wheel AOCS.

**Phased array physics:** A phased array consists of multiple antenna elements (patch, dipole, or slot) arranged in a grid. Each element has an individual phase shifter (and sometimes amplitude control). By adjusting the relative phase between elements, the beam can be electronically steered without moving the antenna. The beam direction $\theta_s$ for element spacing $d$ and phase increment $\Delta\phi$:

$$\sin(\theta_s) = \frac{\Delta\phi \cdot \lambda}{2\pi d}$$

Advantages: no moving parts, fast beam steering (microseconds), multiple simultaneous beams possible. Disadvantages: complex, expensive, high power consumption for active arrays, scan loss at wide angles ($\cos\theta_s$ factor). Phased arrays are used on Starlink satellites (Ka-band), Iridium NEXT (L-band), and are emerging for CubeSats in Ka-band.

---

## 4. Free Space Path Loss by Band (10 min)

### Teaching Notes

FSPL increases with both frequency and distance. At a fixed slant range, higher-frequency bands lose more signal -- but this is offset by the ability to use smaller, higher-gain antennas at higher frequencies.

> **Key Equations -- FSPL (expanded form)**
>
> $$\text{FSPL (dB)} = 20\log_{10}(4\pi) + 20\log_{10}(d) + 20\log_{10}(f) - 20\log_{10}(c)$$
> $$= 21.98 + 20\log_{10}(d_m) + 20\log_{10}(f_{Hz}) - 169.54$$
>
> **Practical form (with km and GHz):**
> $$\text{FSPL (dB)} = 92.45 + 20\log_{10}(d_{km}) + 20\log_{10}(f_{GHz})$$

### Slant Range Geometry

The slant range $d$ from a LEO spacecraft to a ground station depends on the orbit altitude $h$ and the elevation angle $\varepsilon$ above the horizon:

$$d = R_E \left[\sqrt{\left(\frac{R_E + h}{R_E}\right)^2 - \cos^2(\varepsilon)} - \sin(\varepsilon)\right]$$

For typical LEO orbits:

| Altitude | Elevation 90 deg (nadir) | Elevation 30 deg | Elevation 10 deg | Elevation 5 deg |
|----------|------------------------|-------------------|-------------------|-------------------|
| 400 km | 400 km | 723 km | 1150 km | 1500 km |
| 500 km | 500 km | 875 km | 1300 km | 1650 km |
| 600 km | 600 km | 1020 km | 1460 km | 1820 km |

**Design rule:** Always compute the link budget at the **minimum elevation angle** (worst case), typically 5--10 deg. Below 5 deg, atmospheric losses increase sharply, ground clutter enters the antenna sidelobes, and the link is generally unusable.

### FSPL by Band and Geometry

| Band | Centre Frequency | FSPL at 500 km (nadir) | FSPL at 1300 km (10 deg elev) | Difference |
|------|-----------------|----------------------|-------------------------------|------------|
| **VHF** | 146 MHz | 139.0 dB | 147.3 dB | 8.3 dB |
| **UHF** | 437 MHz | 148.3 dB | 157.6 dB | 9.3 dB |
| **S-band** | 2250 MHz | 162.5 dB | 170.8 dB | 8.3 dB |
| **X-band** | 8200 MHz | 173.8 dB | 182.1 dB | 8.3 dB |
| **Ka-band** | 26 GHz | 183.8 dB | 192.1 dB | 8.3 dB |

**The elevation angle penalty:** Going from nadir to 10 deg elevation increases FSPL by ~8 dB (distance increases by ~2.6x; FSPL scales as $20\log_{10}(2.6) = 8.3$ dB). This is a significant loss and is why contact time at high elevations is much more valuable than contact time at low elevations.

---

## 5. Frequency Band Selection and Licensing (15 min)

### Teaching Notes

*[Source: ITU Radio Regulations, Articles 5 and 22; ISED RSS-SAT; FCC Part 25; IARU Satellite Frequency Coordination]*

Band selection is a **design constraint** that affects data rate, antenna size, atmospheric losses, equipment availability, licensing cost, and data policy. The choice of band is one of the earliest and most consequential decisions in mission design.

### Band Comparison Table

| Band | Frequency Range | Allocation | Max BW | Practical Data Rate | Atmospheric Loss (10 deg) | Rain Fade | Licensing | Equipment Availability |
|------|----------------|-----------|--------|--------------------|--------------------------|-----------|-----------|-----------------------|
| **VHF** | 144--146 MHz | Amateur | 15 kHz | < 9.6 kbps | 0.1 dB | None | IARU coord (free, 3--6 mo) | Many COTS, low cost |
| **UHF** | 435--438 MHz | Amateur | 20 kHz | < 19.2 kbps | 0.2 dB | Negligible | IARU coord (free, 3--6 mo) | Many COTS, low cost |
| **S-band** | 2200--2290 MHz | Space research/EES | 5 MHz | 0.1--10 Mbps | 0.5 dB | < 0.5 dB | ISED/FCC ($30--45K, 6--12 mo) | Many COTS |
| **X-band** | 8025--8400 MHz | EES | 375 MHz | 10--400 Mbps | 1.0 dB | 1--3 dB | ISED/FCC + ITU ($50--80K, 12+ mo) | Growing COTS |
| **Ka-band** | 25.5--27.0 GHz | EES/FSS | 1.5 GHz | 100--2000+ Mbps | 2--5 dB | 3--15 dB (location-dependent) | Complex ITU ($100K+, 18+ mo) | Emerging COTS |

*EES = Earth Exploration Satellite; FSS = Fixed Satellite Service*

**Atmospheric attenuation physics:** The atmosphere absorbs and scatters RF energy. Molecular oxygen has a strong absorption line at 60 GHz (used for inter-satellite links where atmospheric penetration is not needed). Water vapour absorbs at 22.2 GHz (near Ka-band). At S-band and below, atmospheric losses are minimal (< 1 dB). At Ka-band, losses of 2--5 dB are typical at 10 deg elevation, and rain fade can add 3--15 dB in tropical regions.

**Rain fade:** Raindrops scatter and absorb RF energy. The effect scales approximately as $f^2$ -- negligible below 4 GHz, significant above 10 GHz, and severe above 20 GHz. Rain fade is characterised by the rain rate (mm/hr) and the path length through rain. In tropical regions, rain rates of 50+ mm/hr can cause 10+ dB additional loss at Ka-band. Mitigation: adaptive data rate (reduce rate during rain), site diversity (multiple ground stations), power control (increase TX power during fade). For Ka-band links, a rain fade margin of 5--10 dB is typically included.

**Amateur band regulations (IARU):**
- Non-commercial, educational, and experimental use only
- Open data policy: all transmissions must be unencrypted and the protocol must be published
- No commercial data or imagery downlink
- Coordination through IARU (International Amateur Radio Union): free but takes 3--6 months
- Very popular for university CubeSats (low cost, no license fees, large amateur community provides free ground station support via SatNOGS network)

**Commercial band licensing:**
- Requires national filing (FCC in US, ISED in Canada, Ofcom in UK, CNES/ANFR in France) + ITU coordination for frequencies above 1 GHz
- Costs: $30--45K for S-band (typical), $50--80K for X-band, $100K+ for Ka-band
- Timeline: 6--12 months for S-band, 12--18 months for X-band, 18+ months for Ka-band
- Commercial data can be encrypted and proprietary
- Bandwidth allocation may be limited by the national authority

### Band Selection Decision Tree

```
Required data rate?
  <= 9.6 kbps AND non-commercial/educational -> VHF/UHF amateur (IARU, free, 3-6 mo)
  <= 10 Mbps                                 -> S-band commercial (ISED/FCC, $30-45K, 6-12 mo)
  <= 400 Mbps                                -> X-band (ISED/FCC + ITU, $50-80K, 12+ mo)
  > 400 Mbps                                 -> Ka-band (complex ITU, $100K+, 18+ mo, rain fade)
```

---

## 6. Modulation and Coding -- Physics and Selection (20 min)

### Teaching Notes

*[Source: CCSDS 131.0-B-4; Sklar, Ch. 7--8; Haykin, Ch. 10; DVB-S2 standard]*

### Modulation -- How Information Becomes RF

Modulation encodes digital data onto an RF carrier by varying the carrier's amplitude, frequency, or phase.

**Phase Shift Keying (PSK):** The most common modulation family for space communications. The carrier phase is shifted by discrete amounts to represent different bit patterns:

- **BPSK (Binary PSK):** 2 phase states (0 deg and 180 deg). Each symbol carries 1 bit. Spectral efficiency: 1 bps/Hz. Most robust to noise.
- **QPSK (Quadrature PSK):** 4 phase states (0, 90, 180, 270 deg). Each symbol carries 2 bits. Spectral efficiency: 2 bps/Hz. Requires the same $E_b/N_0$ as BPSK but doubles the data rate for the same bandwidth. **The standard choice for most space links.**
- **8PSK:** 8 phase states, 3 bits/symbol, spectral efficiency 3 bps/Hz. Requires ~3.5 dB more $E_b/N_0$ than QPSK for the same BER.
- **16APSK:** 16 states (amplitude + phase), 4 bits/symbol, spectral efficiency 4 bps/Hz. Requires ~7 dB more $E_b/N_0$ than QPSK.

**Frequency Shift Keying (FSK):** The carrier frequency is shifted between discrete values. Less spectrally efficient than PSK but more tolerant of amplifier nonlinearity. Variants:
- **FSK:** Simple frequency switching. 
- **GFSK (Gaussian FSK):** Gaussian filter smooths frequency transitions, reducing spectral spreading. Used by many CubeSat UHF radios (AX.25 protocol at 9600 bps).
- **MSK (Minimum Shift Keying):** A special case of FSK with minimum frequency deviation that still allows coherent detection. Constant envelope (important for nonlinear amplifiers). Spectral efficiency ~1 bps/Hz.

**Why QPSK is preferred over BPSK for space links:** QPSK transmits 2 bits per symbol while requiring the same energy per bit as BPSK. This means QPSK achieves twice the data rate for the same bandwidth and the same $E_b/N_0$ performance. The only additional complexity is that the receiver must resolve 4 phase states instead of 2, which is trivial for modern digital receivers.

### Forward Error Correction (FEC) -- Coding Gain

FEC adds redundant bits to the data stream before transmission. The receiver uses these redundant bits to detect and correct bit errors without retransmission. The improvement in $E_b/N_0$ requirement (compared to uncoded) is called the **coding gain**.

**Why coding is essential for space links:** Space links operate at very low received signal power (femtowatts to picowatts). Without coding, the required $E_b/N_0$ for BER $10^{-6}$ is 10.5 dB. With LDPC coding, this drops to 2.0 dB -- a coding gain of 8.5 dB. This is equivalent to either: increasing the TX power by 7x, or increasing the antenna diameter by 2.7x, or reducing the data rate by 7x. Coding achieves the same benefit at the cost of only a few watts of digital processing power.

**Code types used in space communications:**

| Code Type | Code Rate | Coding Gain at BER $10^{-6}$ | Decoding Complexity | Standard | Use |
|-----------|-----------|-------------------------------|---------------------|----------|-----|
| **Convolutional** (K=7) | 1/2 | ~5.5 dB | Low (Viterbi decoder, hardware) | CCSDS | Legacy telecommand, AX.25 |
| **Convolutional + RS** (concatenated) | ~0.44 | ~7.5 dB | Medium | CCSDS | Standard CCSDS telemetry (many heritage missions) |
| **Turbo code** | 1/2 to 1/6 | ~8--10 dB | High (iterative decoder) | CCSDS | Deep space links (Mars, Jupiter) |
| **LDPC** (Low-Density Parity Check) | 1/2 | ~8.5 dB | Medium-High (iterative BP decoder) | CCSDS, DVB-S2 | Modern space downlinks, **recommended for CubeSats** |
| **LDPC** | 3/4 | ~6.5 dB | Medium-High | CCSDS, DVB-S2 | Balanced performance and throughput |
| **LDPC** | 7/8 | ~5.0 dB | Medium-High | DVB-S2 | Maximum throughput, strong signal |

*[Source: CCSDS 131.0-B-4; DVB-S2 ETSI EN 302 307]*

**Code rate $r$:** The ratio of information bits to total transmitted bits. A rate-1/2 code transmits 1 information bit for every 2 transmitted bits (50% overhead). This means the channel data rate must be $R_{\text{channel}} = R_{\text{info}} / r$ -- a rate-1/2 code requires twice the channel bandwidth for a given information rate.

### Complete Modulation + Coding Table

| Modulation + Coding | $E_b/N_0$ Required (BER $10^{-6}$) | Spectral Efficiency (bps/Hz) | Typical Use | Implementation |
|--------------------|------------------------------------|-------------------------------|------------|----------------|
| GMSK uncoded | 10.5 dB | ~1.0 | AX.25 amateur, legacy | Simple radio IC |
| BPSK uncoded | 10.5 dB | 1.0 | Legacy telecommand | Simple |
| QPSK uncoded | 10.5 dB | 2.0 | Simple telemetry | Moderate |
| QPSK + conv (r=1/2, K=7) | 5.0 dB | 1.0 | Standard CCSDS TM | Hardware Viterbi |
| QPSK + conv + RS (concat) | 3.0 dB | 0.88 | Heritage CCSDS | Hardware |
| QPSK + LDPC (r=1/2) | 2.0 dB | 1.0 | High-efficiency downlink | FPGA-based |
| QPSK + LDPC (r=3/4) | 4.0 dB | 1.5 | **Balanced -- recommended** | FPGA-based |
| QPSK + LDPC (r=7/8) | 5.5 dB | 1.75 | Bandwidth-limited | FPGA-based |
| 8PSK + LDPC (r=3/4) | 6.5 dB | 2.25 | High-rate downlink | FPGA-based |
| 16APSK + LDPC (r=3/4) | 8.5 dB | 3.0 | Maximum throughput | FPGA-based |

**Design guidance for CubeSats:** 
- **UHF amateur:** GMSK or AFSK (AX.25 protocol) at 1.2--9.6 kbps channel rate. Add convolutional coding if link margin is tight.
- **S-band:** QPSK + LDPC (r=1/2 or r=3/4). This is the sweet spot: 5.5--8.5 dB coding gain with manageable complexity. Most COTS S-band CubeSat transmitters (Endurosat, NanoAvionics, AAC Clyde) support DVB-S2 or CCSDS LDPC natively.
- **X-band / Ka-band:** 8PSK or 16APSK + LDPC for maximum spectral efficiency when bandwidth is limited.

---

## 7. Ground Stations (10 min)

### Teaching Notes

The ground station is half of the communication link. Its performance ($G/T$) directly determines the achievable data rate. Upgrading the ground station is often the cheapest way to improve link performance (compared to upgrading the spacecraft transmitter or antenna).

### Ground Station Types

| Type | Antenna | G/T (S-band) | Cost | Availability | Examples |
|------|---------|-------------|------|-------------|---------|
| **Amateur (SatNOGS)** | 10--15 dBi Yagi | -15 to -10 dB/K | Free (volunteer-operated) | Global network, 200+ stations | SatNOGS network |
| **University** | 2--3 m dish | +10 to +15 dB/K | $50--200K (build) | Limited availability | Many universities have S-band stations |
| **Commercial (small)** | 3--5 m dish | +15 to +25 dB/K | $500/pass or $5--20K/month | KSAT Lite, AWS Ground Station | KSAT, Amazon, Leaf Space |
| **Commercial (large)** | 5--13 m dish | +25 to +35 dB/K | $1000/pass or $20--50K/month | SSC, KSAT, ATLAS | SSC (Esrange), KSAT (Svalbard), ATLAS (Fairbanks) |
| **Deep Space Network** | 34--70 m dish | +45 to +60 dB/K | NASA-funded only | DSN (3 sites globally) | Goldstone, Canberra, Madrid |

*[Source: KSAT Lite pricing 2024; AWS Ground Station pricing; SSC SmallSat ground segment]*

**Contact geometry and pass duration:**

A LEO satellite is in view of a ground station for a limited time per orbit. The pass duration depends on the orbit altitude and the maximum elevation angle:

$$t_{\text{pass}} \approx \frac{2}{n} \arccos\left(\frac{\cos(\varepsilon_{\text{max}})}{\cos(\varepsilon_{\text{min}})}\right)$$

For a simplified estimate:

| Altitude | Min Elevation | Max Pass Duration | Typical Usable Duration | Passes/Day (mid-latitude) |
|----------|--------------|-------------------|------------------------|--------------------------|
| 400 km | 10 deg | ~7 min | ~5 min | 3--4 |
| 500 km | 10 deg | ~8 min | ~6 min | 4--5 |
| 600 km | 10 deg | ~9 min | ~7 min | 4--5 |
| 800 km | 10 deg | ~11 min | ~9 min | 5--6 |

The "usable duration" is shorter than the total pass because the link only closes above the minimum elevation angle, and the first/last 30--60 seconds are used for signal acquisition and link setup.

**Ground station selection criteria:**
- **Location:** Polar stations (Svalbard at 78 degN, McMurdo at 78 degS) see every orbit of a polar/SSO satellite, providing 12+ contacts per day. Mid-latitude stations see only 3--5 passes. Equatorial stations see even fewer passes of polar satellites.
- **G/T:** Determines the achievable data rate. A 3 dB improvement in G/T allows doubling the data rate.
- **Licensing:** Must be compatible with the spacecraft frequency allocation
- **Cost:** Ranges from free (SatNOGS, university) to $1000+/pass (commercial)
- **Reliability:** SLA (service-level agreement) for commercial stations; university stations may have limited operator availability

**EIRP (ground station transmit, for uplink):** For telecommand uplink, the ground station transmits to the spacecraft. Ground station EIRP is typically 40--60 dBW for commercial stations, sufficient for robust command links even with low-gain spacecraft receive antennas.

---

## 8. Worked Examples: Complete Link Budgets (15 min)

### 3U EO CubeSat -- S-band Downlink

> **Worked Example -- S-band Downlink for 3U EO CubeSat (SuperDove-class)**
>
> **Scenario:** 500 km SSO, S-band (2250 MHz), 1 Mbps downlink, 10 deg minimum elevation (slant range 1300 km), 3 m ground station dish ($T_{sys} = 150$ K, $G_{RX} = 35$ dBi at S-band).
>
> | Line | Parameter | Value | Unit | Calculation/Source |
> |------|-----------|-------|------|--------------------|
> | 1 | TX Power (2 W) | +3.0 | dBW | COTS S-band TX (Endurosat) |
> | 2 | TX Antenna Gain (patch) | +6.0 | dBi | Single-element S-band patch |
> | 3 | TX Line Losses | -1.5 | dB | 15 cm cable + connector |
> | 4 | **EIRP** | **+7.5** | dBW | $3.0 + 6.0 - 1.5$ |
> | 5 | FSPL (2250 MHz, 1300 km) | -170.8 | dB | $92.45 + 20\log_{10}(1300) + 20\log_{10}(2.25)$ |
> | 6 | Atmospheric Loss | -0.5 | dB | S-band, 10 deg elevation |
> | 7 | Pointing Loss | -1.0 | dB | 5 deg mispoint, 80 deg beamwidth patch |
> | 8 | Polarisation Loss (RHCP-RHCP) | -0.3 | dB | Minor axial ratio mismatch |
> | 9 | RX Antenna Gain (3 m dish) | +35.0 | dBi | $10\log_{10}(0.6 \times (\pi \times 3.0 / 0.133)^2)$ |
> | 10 | System Noise Temp (150 K) | 21.8 | dBK | Professional LNA + sky temp |
> | 11 | **G/T** | **+13.2** | dB/K | $35.0 - 21.8$ |
> | 12 | Boltzmann Constant | +228.6 | dBW/K/Hz | $-k$ in link equation |
> | 13 | **C/N$_0$** | **+76.7** | dBHz | $7.5 - 170.8 - 0.5 - 1.0 - 0.3 + 13.2 + 228.6$ |
> | 14 | Data Rate (1 Mbps) | 60.0 | dBbps | $10\log_{10}(10^6)$ |
> | 15 | **$E_b/N_0$ available** | **+16.7** | dB | $76.7 - 60.0$ |
> | 16 | $E_b/N_0$ required (QPSK + LDPC r=3/4) | 4.0 | dB | From modulation/coding table |
> | 17 | Implementation Loss | 2.0 | dB | Real demodulator vs ideal |
> | 18 | **LINK MARGIN** | **+10.7** | dB | $16.7 - 4.0 - 2.0$ |
>
> **Result:** Link closes with 10.7 dB margin (requirement: >= 3 dB). **Pass.**
>
> **Design insight:** The generous 10.7 dB margin suggests the link is over-designed for 1 Mbps. The team could increase the data rate:
>
> Maximum data rate at 3 dB margin:
> $E_b/N_0 \text{ available at max rate} = 4.0 + 2.0 + 3.0 = 9.0$ dB
>
> $C/N_0 = 76.7$ dBHz, so $R_{b,\text{max}} = 10^{(76.7 - 9.0)/10} = 10^{6.77} \approx$ **5.9 Mbps** at 3 dB margin.
>
> Alternatively, at 5 Mbps ($10\log_{10}(5 \times 10^6) = 67.0$ dBbps):
> $E_b/N_0 = 76.7 - 67.0 = 9.7$ dB. Margin = $9.7 - 4.0 - 2.0 = 3.7$ dB. **Pass** (barely).

### 1U Worked Example: UniSat-1

**UHF Link Budget: 437 MHz at 9600 bps**

UniSat-1 uses the UHF amateur band at 437 MHz with a ground station equipped with a 10 dBi Yagi antenna. This is the lowest-cost and simplest communication architecture available to CubeSat missions.

> **Worked Example -- UHF Downlink Link Budget for UniSat-1**
>
> **Scenario:** 400 km orbit, UHF (437 MHz), 9600 bps downlink (GMSK), 10 deg minimum elevation angle, amateur ground station with 10 dBi Yagi antenna, $T_{sys} = 600$ K (COTS LNA, coax cable losses, sky noise near horizon).
>
> **Slant range at 10 deg elevation:**
> From 400 km altitude, the worst-case slant range at 10 deg elevation is approximately 1150 km.
>
> | Line | Parameter | Value | Unit | Notes |
> |------|-----------|-------|------|-------|
> | 1 | TX Power (0.5 W) | -3.0 | dBW | Standard CubeSat UHF radio |
> | 2 | TX Antenna Gain (monopole) | 0.0 | dBi | Quarter-wave monopole, ~omnidirectional |
> | 3 | TX Line Losses | -0.5 | dB | Short cable to antenna |
> | 4 | **EIRP** | **-3.5** | dBW | Low EIRP is the fundamental UHF challenge |
> | 5 | FSPL (437 MHz, 1150 km) | -155.5 | dB | Lower than S-band (good) |
> | 6 | Atmospheric Loss | -0.3 | dB | UHF atmospheric loss is minimal |
> | 7 | Pointing Loss (omni antenna) | -0.5 | dB | Omni pattern -- negligible |
> | 8 | Polarisation Loss (linear-linear) | -3.0 | dB | **Major loss** -- Faraday rotation in ionosphere rotates polarisation randomly |
> | 9 | RX Antenna Gain (10 dBi Yagi) | +10.0 | dBi | 5-element Yagi, manually tracked |
> | 10 | System Noise Temp (600 K) | 27.8 | dBK | Amateur station: warm LNA + cable loss |
> | 11 | **G/T** | **-17.8** | dB/K | Low G/T is the ground station limitation |
> | 12 | Boltzmann Constant | +228.6 | dBW/K/Hz | |
> | 13 | **C/N$_0$** | **+48.0** | dBHz | |
> | 14 | Data Rate (9600 bps) | 39.8 | dBbps | |
> | 15 | **$E_b/N_0$ available** | **+8.2** | dB | |
> | 16 | $E_b/N_0$ required (GMSK uncoded) | 10.5 | dB | |
> | 17 | Implementation Loss | -2.0 | dB | |
>
> **Margin = 8.2 - 10.5 - 2.0 = -4.3 dB. The link does NOT close!**
>
> **Fix 1: Add FEC.** Convolutional coding (r=1/2, K=7):
> - $E_b/N_0$ required drops to **5.0 dB** (5.5 dB coding gain)
> - Channel rate remains 9600 bps, but useful throughput is 4800 bps (half is redundancy)
> - **Margin** = 8.2 - 5.0 - 2.0 = **+1.2 dB** -- still below 3 dB requirement.
>
> **Fix 2: Upgrade ground antenna to cross-Yagi (13 dBi) with circular polarisation:**
> - RX gain: +13.0 dBi (was +10.0) -> +3.0 dB improvement
> - Polarisation loss: -0.5 dB (was -3.0 dB, now RHCP-to-RHCP) -> +2.5 dB improvement
> - Net improvement: +5.5 dB
> - New C/N$_0$: 53.5 dBHz
> - New $E_b/N_0$ available: 53.5 - 39.8 = 13.7 dB
> - **Margin** = 13.7 - 5.0 - 2.0 = **+6.7 dB** -- **Pass** (> 3 dB).
>
> **Polarisation loss physics:** At UHF (437 MHz), the ionosphere causes Faraday rotation of linearly polarised signals. The rotation angle depends on the total electron content (TEC) along the path and varies with time of day, solar activity, and signal path. If the satellite transmits linear polarisation and the ground station receives with linear polarisation, the polarisation planes may be orthogonal at times, causing up to complete signal loss (theoretically infinite loss, practically 20+ dB fades). Using circular polarisation on at least one end (preferably both) eliminates Faraday rotation loss, reducing it to ~0.3--0.5 dB axial ratio mismatch. **This is why circular polarisation is mandatory for reliable UHF satellite links.**
>
> **Final link budget summary (with FEC + cross-Yagi):**
>
> | Parameter | Value |
> |-----------|-------|
> | TX power | 0.5 W |
> | TX antenna | Monopole (0 dBi) |
> | Frequency | 437 MHz |
> | Channel rate | 9600 bps |
> | Useful throughput | 4800 bps (with r=1/2 FEC) |
> | Ground antenna | 13 dBi cross-Yagi, RHCP |
> | Link margin | **+6.7 dB** |

**Data throughput for UniSat-1:** At 4800 bps useful throughput, a 7-minute pass delivers:
$V_{\text{pass}} = 4800 \times 420 \times 0.85 = 1.71$ Mbit $= 214$ kB per pass.

The 0.85 factor accounts for protocol overhead (packet headers, acknowledgements, retransmissions, link setup time).

With 4 passes/day: $V_{\text{daily}} = 856$ kB/day $\approx$ **0.84 MB/day**. The magnetometer generates $< 1$ kbps $\times$ 600 s/orbit $\times$ 15 orbits $= 9$ Mbit/day $= 1.13$ MB/day. This is **marginal** -- the team may need to prioritise data or add a second ground station. Using the SatNOGS network (200+ volunteer stations worldwide) could provide 10+ additional contacts per day at no cost.

**Key lesson from UniSat-1 link budget:** UHF links are power-starved compared to S-band or X-band. The lower FSPL at 437 MHz (~15 dB less than S-band) does not compensate for the low TX power (0.5 W vs 2 W = 6 dB less), low antenna gain (0 dBi vs 6 dBi = 6 dB less), and higher system noise temperature of amateur stations (600 K vs 150 K = 6 dB worse). FEC coding and circular polarisation are essential for closing a UHF CubeSat link.

---

## 9. Data Budget (10 min)

### Teaching Notes

The data budget determines whether the communication system can deliver all mission data to the ground. Even if the link budget closes, the mission fails if the total data volume exceeds the downlink capacity.

> **Key Equations -- Data Budget**
>
> **Daily data generation:**
> $$V_{\text{gen}} = R_{\text{payload}} \times t_{\text{imaging}} \times N_{\text{orbits}} \times f_{\text{compression}}$$
>
> **Daily downlink capacity:**
> $$V_{\text{DL}} = R_{\text{downlink}} \times t_{\text{contact}} \times N_{\text{passes}} \times \eta_{\text{protocol}}$$
>
> where $\eta_{\text{protocol}} = 0.80$--$0.90$ accounts for packet overhead, retransmissions, link setup time, and handshaking.
>
> **Data budget closure:**
> $$V_{\text{DL}} \geq V_{\text{gen}} \quad \text{(data budget closes)}$$
>
> **Backlog clearance time:** If $V_{\text{DL}} < V_{\text{gen}}$ per day, data accumulates in onboard storage. The backlog clearance time is:
> $$t_{\text{clear}} = \frac{V_{\text{stored}}}{V_{\text{DL}} - V_{\text{gen}}}$$
> If $V_{\text{DL}} < V_{\text{gen}}$, the backlog grows forever -- the mission cannot sustain its data generation rate.

> **Worked Example -- Data Budget for 3U EO CubeSat**
>
> **Generation:** 240 Mbps raw imaging data x 5 min/orbit x 15 orbits/day x 0.25 (4:1 JPEG2000 compression)
> = 240 x 300 x 15 x 0.25 = 270,000 Mbit/day = **33.75 GB/day**
>
> Wait -- that's extremely high. Let's be more realistic about imaging time. Not every orbit has a target. Assume 4 imaging passes per day, 5 minutes each:
>
> $V_{\text{gen}} = 240 \times 10^6 \times 300 \times 4 \times 0.25 = 72,000$ Mbit $= 9.0$ GB/day
>
> Still high. Planet SuperDove images approximately 1--2 minutes per orbit over priority targets, compresses heavily (10:1+), and downlinks selectively.
>
> **Revised:** 240 Mbps x 1 min/pass x 4 passes/day x 0.10 (10:1 compression) = 240 x 60 x 4 x 0.10 = 5,760 Mbit = **720 MB/day**
>
> **Downlink (S-band at 5 Mbps):** 5 Mbps x 6 min/pass x 5 passes/day x 0.85 = 153 Mbit/pass x 5 = 765 Mbit = **95.6 MB/day x 5 = 478 MB/day**
>
> Hmm, let's recompute carefully:
> $V_{\text{DL}} = 5 \times 10^6 \times 360 \times 5 \times 0.85 = 7,650$ Mbit $= 956$ MB/day
>
> **Result:** 956 MB/day > 720 MB/day. **Data budget closes** with 33% margin.
>
> **Sensitivity:** If imaging duty cycle doubles (2 min/pass), generation rises to 1440 MB/day > 956 MB/day. Options: (a) X-band for higher data rate, (b) additional ground stations, (c) more aggressive compression, (d) onboard data prioritisation/selection.

---

## 10. SpaceCDF Exercise (25 min)

### Instructions

1. **Spectrum Selector** (Dashboard): Select your license type and frequency band
2. **Link Budget** tab:
   - Enter TX power, antenna type, frequency, ground station parameters
   - Review the computed link margin
   - Verify it meets >= 3 dB requirement
3. **Compare** to your hand calculation from the worked example
4. **Equipment Browser:** Select a transponder and antenna that match your band choice
   - Note RF compatibility warnings (band mismatch between transponder and antenna)
5. Complete Worksheet 3.3

### Discussion Questions

- What is the most impactful parameter in your link budget? (Usually FSPL or G/T)
- How does doubling the data rate affect link margin? (Reduces by 3 dB -- because $10\log_{10}(2) = 3$ dB)
- Could you use a lower-power transmitter and still close the link? What is the minimum TX power?
- Does your data budget close? If not, what is the cheapest fix? (Usually: more ground station passes, or lower imaging duty cycle)
- What is the effect of Faraday rotation on your UHF link? (If applicable)

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Link budget | $\text{Margin} = E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} \geq 3$ dB |
| EIRP | $\text{EIRP} = P_{TX} + G_{TX} - L_{TX}$ -- transmitter's effective power in beam direction |
| FSPL physics | Geometric spreading ($1/d^2$) + aperture scaling ($\lambda^2$); not energy absorption |
| FSPL formula | $92.45 + 20\log_{10}(d_{km}) + 20\log_{10}(f_{GHz})$; increases 6 dB per doubling of frequency or distance |
| G/T | Receiver figure of merit: antenna gain minus noise temperature; most important ground station parameter |
| Antenna types | Monopole (0 dBi, omni) to parabolic (25--45 dBi, narrow beam); gain vs pointing trade-off |
| Antenna gain | $G = \eta_a (\pi D/\lambda)^2$; patch ~6 dBi; 3 m dish: 35 dBi at S-band, 25 dBi at X-band |
| Pointing loss | $-12(\Delta\theta/\theta_{3\text{dB}})^2$ dB; narrower beam = more sensitive to pointing errors |
| Modulation | QPSK: 2 bits/symbol, same $E_b/N_0$ as BPSK but 2x spectral efficiency; **standard choice** |
| FEC coding | LDPC (r=3/4): $E_b/N_0 = 4.0$ dB, coding gain ~6.5 dB; **essential for space links** |
| Coding gain | 5--10 dB improvement for free (just digital processing); equivalent to 3--10x power increase |
| UHF challenges | Low EIRP, Faraday rotation (use circular polarisation), high ground station noise; FEC mandatory |
| Band selection | UHF for < 9.6 kbps (free, amateur); S-band for < 10 Mbps; X-band for < 400 Mbps; Ka-band for > 400 Mbps |
| Rain fade | Negligible below 4 GHz; 1--3 dB at X-band; 3--15 dB at Ka-band; add margin or adaptive rate |
| Ground stations | G/T: amateur -15 dB/K, university +12 dB/K, commercial +25 dB/K; polar stations see every orbit |
| Data budget | Daily downlink capacity must exceed daily data generation; compression ratio is a key lever |
| Licensing | Amateur (free, IARU, 3--6 mo); S-band ($30--45K, 6--12 mo); X-band ($50--80K, 12+ mo) |
