# Chapter 11 — Communications and Link Budgets

> **Recommended background.** SMAD4 Ch. 13 (Communications); ECSS-E-ST-50-05C (Radio frequency and modulation); CCSDS 131.0-B-4 (TM synchronisation and channel coding); Pratt, Bostian & Allnutt, *Satellite Communications*, Ch. 4; Maral & Bousquet, *Satellite Communications Systems*, Ch. 5. This chapter uses the orbit and contact geometry of Chapter 7, the ground-segment functions of Chapter 6, the pointing capability of Chapter 10 and the regulatory framework of Chapter 2; the free-space path loss and link-budget algebra are derived from first principles in Part V §V.6–V.8.

## Learning objectives

By the end of this chapter, you will be able to:

1. Construct a complete link budget from first principles (in decibels)
2. Compute free-space path loss for any frequency and slant range
3. Select an appropriate frequency band based on data rate, licensing and equipment availability
4. Explain the physics of each antenna type and compute antenna gain and beamwidth
5. Choose a modulation and coding scheme based on required $E_b/N_0$ and spectral efficiency
6. Explain the physical basis for coding gain and why forward error correction is essential for space links
7. Size an antenna (gain, beamwidth, mass) for the selected frequency
8. Determine data throughput and verify that the data budget closes
9. Identify ground-station options and compute contact geometry
10. Compute a link budget by hand and check it against a concurrent-design tool or spreadsheet

Vendor products named in this chapter are representative examples, not endorsements; prices and licensing fees are indicative (2026).

---

## 11.1 The link budget concept

*[Source: SMAD, Ch. 13; ECSS-E-ST-50-05C; Roddy, Ch. 4]*

The link budget is the accounting statement for the communication link. Every gain and every loss from transmitter to receiver is tallied in **decibels (dB)** to determine whether the link "closes" — meaning the received signal is strong enough to decode with an acceptable error rate.

The fundamental question: **does the received signal have enough energy per bit, relative to the noise, to achieve the required bit error rate?** This is quantified by $E_b/N_0$ — the ratio of energy per information bit to noise spectral density.

### 11.1.1 Link budget flow

Figure 11.1 shows the chain: the transmitter's power, antenna gain and line losses combine into an EIRP; the channel removes path, atmospheric and pointing losses; the receiver's antenna gain and noise temperature set its figure of merit $G/T$; and the demodulator compares the available $E_b/N_0$ with what the chosen modulation and coding require. What is left is the margin.

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
  <text x="300" y="85" text-anchor="middle" fill="#991b1b" font-weight="bold">Channel losses</text>
  <text x="300" y="100" text-anchor="middle" fill="#991b1b" font-size="9">FSPL (dB)</text>
  <text x="300" y="115" text-anchor="middle" fill="#991b1b" font-size="9">Atmospheric (dB)</text>
  <text x="300" y="130" text-anchor="middle" fill="#991b1b" font-size="9">Pointing, polarisation (dB)</text>
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
  <text x="590" y="100" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 available (dB)</text>
  <text x="590" y="115" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 required (dB)</text>
  <text x="590" y="130" text-anchor="middle" fill="#3730a3" font-size="9">Implementation loss (dB)</text>
  <line x1="500" y1="100" x2="530" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Margin -->
  <rect x="680" y="70" width="90" height="55" rx="6" fill="#d1fae5" stroke="#059669" stroke-width="3"/>
  <text x="725" y="93" text-anchor="middle" fill="#065f46" font-weight="bold" font-size="13">MARGIN</text>
  <text x="725" y="112" text-anchor="middle" fill="#065f46" font-size="11">≥ 3 dB</text>
  <line x1="650" y1="100" x2="680" y2="97" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <defs><marker id="a3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#64748b"/></marker></defs>
</svg>

**Figure 11.1** — The link chain from transmitter to demodulator. Each block contributes gains (positive) or losses (negative) in decibels; the margin is what remains after the demodulator's requirement has been met.

### 11.1.2 Decibel refresher

All link-budget terms are in decibels to convert multiplication and division into addition and subtraction:

| Conversion | Formula | Example |
|-----------|---------|---------|
| Watts to dBW | $P_{\text{dBW}} = 10 \log_{10}(P_W)$ | 2 W = +3.0 dBW |
| Milliwatts to dBm | $P_{\text{dBm}} = 10 \log_{10}(P_{mW})$ | 1 W = +30 dBm |
| dBW to watts | $P_W = 10^{P_{\text{dBW}}/10}$ | −3 dBW = 0.5 W |
| Ratio to dB | $G_{\text{dB}} = 10 \log_{10}(G)$ | Gain of 100 = 20 dB |
| dBW vs dBm | dBm = dBW + 30 | 0 dBW = 30 dBm |

**Common power values:**

| Power | dBW | dBm |
|-------|-----|-----|
| 0.1 W | −10.0 | +20.0 |
| 0.5 W | −3.0 | +27.0 |
| 1 W | 0.0 | +30.0 |
| 2 W | +3.0 | +33.0 |
| 5 W | +7.0 | +37.0 |
| 10 W | +10.0 | +40.0 |

---

## 11.2 The complete link budget equation

> **Key equations — link budget (dB form)**
>
> **EIRP** (effective isotropic radiated power):
> $$\text{EIRP} = P_{TX} + G_{TX} - L_{TX} \quad \text{(dBW)}$$
>
> EIRP represents the power that an isotropic antenna would need to radiate to produce the same signal strength in the direction of maximum antenna gain. It combines the transmitter power, antenna gain (directivity), and cable/filter losses.
>
> **Free-space path loss:**
> $$\text{FSPL} = 20\log_{10}\left(\frac{4\pi d}{\lambda}\right) = 20\log_{10}\left(\frac{4\pi d f}{c}\right) \quad \text{(dB)}$$
> where $d$ = slant range (m), $f$ = frequency (Hz), $c = 3 \times 10^8$ m/s.
>
> **Physical interpretation:** FSPL is not "energy absorption" — no energy is lost. It is the geometric spreading of radiated power over a sphere of radius $d$. An isotropic antenna radiates equally in all directions, so the power per unit area at distance $d$ is $P/(4\pi d^2)$. The $\lambda^2$ dependence arises because a receive antenna's effective aperture scales as $A_{\text{eff}} = G\lambda^2/(4\pi)$ — at higher frequencies the receive antenna "captures" less of the available flux (unless the antenna is physically larger). Part V §V.6 derives this from the Friis transmission equation.
>
> **Receiver figure of merit:**
> $$G/T = G_{RX} - 10\log_{10}(T_{sys}) \quad \text{(dB/K)}$$
>
> $G/T$ is the single most important parameter of any receive station. It combines the antenna gain (signal capture) with the system noise temperature (noise floor). A high $G/T$ means good sensitivity.
>
> **System noise temperature** $T_{sys}$ includes:
> - Antenna noise temperature $T_A$ (depends on what the antenna "sees": sky ~10–50 K at zenith, ~150–300 K looking at Earth/ground)
> - Feed/cable losses: $T_{\text{feed}} = T_{\text{physical}} (L-1)$ where $L$ = loss factor
> - LNA noise temperature: $T_{\text{LNA}} = T_0 (F-1)$ where $F$ = noise figure, $T_0 = 290$ K
> - Subsequent stages (reduced by LNA gain)
>
> Rule of thumb: $T_{sys} \approx 100$–$200$ K for a professional ground station with a cryogenic or low-noise LNA; $T_{sys} \approx 400$–$800$ K for an amateur station with a COTS LNA.
>
> **Carrier-to-noise density ratio** (the canonical form used throughout this book, including Part IV and Part V §V.7):
> $$C/N_0 = \text{EIRP} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} - L_{\text{rx}} + G/T - k \quad \text{(dBHz)}$$
> where $k = -228.6$ dBW/K/Hz (Boltzmann's constant, $k = 1.381 \times 10^{-23}$ J/K, expressed in dB) and $L_{\text{rx}}$ is the receive-side feed and line loss between the antenna and the point at which $T_{sys}$ is referenced (often absorbed into $G/T$, in which case it is set to 0 dB in the line-by-line table).
>
> **Energy per bit to noise density:**
> $$E_b/N_0 = C/N_0 - 10\log_{10}(R_b) \quad \text{(dB)}$$
> where $R_b$ = data rate (bit/s). This is the fundamental quality metric: each bit needs a certain amount of energy ($E_b$) relative to the noise floor ($N_0$) to be correctly demodulated.
>
> **Link margin:**
> $$\text{Margin} = E_b/N_{0,\text{available}} - E_b/N_{0,\text{required}} - L_{\text{implementation}} \quad \text{(dB)}$$
>
> **Requirement:** Margin ≥ 3 dB for Phase B and beyond (per ECSS-E-ST-50-05C; a 6 dB target is common in Phase A while the design is still fluid). This 3 dB margin covers:
> - Transmitter power variation (ageing, temperature)
> - Antenna gain uncertainties
> - Atmospheric scintillation
> - Pointing error variations
> - Ground station performance variation

### 11.2.1 Complete link budget table

| Line | Parameter | Formula / typical value | Unit | Physical meaning |
|------|-----------|------------------------|------|-----------------|
| 1 | TX power | $P_{TX}$ (e.g. 2 W = +3.0) | dBW | RF power from amplifier output |
| 2 | TX antenna gain | $G_{TX}$ (e.g. +6.0 for patch) | dBi | Directivity relative to isotropic |
| 3 | TX line losses | $L_{TX}$ (cables, filters: −1.5) | dB | Ohmic loss in RF cables and connectors |
| 4 | **EIRP** | $= P_{TX} + G_{TX} - L_{TX}$ | dBW | Effective radiated power |
| 5 | Free-space path loss | $\text{FSPL} = 20\log_{10}(4\pi d f/c)$ | dB | Geometric spreading + aperture effect |
| 6 | Atmospheric loss | $L_{\text{atm}}$ (−0.3 to −3.0) | dB | Molecular absorption (O$_2$, H$_2$O) |
| 7 | Pointing loss | $L_{\text{point}}$ (−0.5 to −3.0) | dB | Signal reduction from antenna mispointing |
| 8 | Polarisation loss | $L_{\text{pol}}$ (−0.1 to −3.0) | dB | Mismatch between TX and RX polarisation |
| 9 | RX antenna gain | $G_{RX}$ (e.g. +35 for 3 m dish) | dBi | Ground antenna directivity |
| 10 | System noise temperature | $T_{sys}$ (e.g. 150 K = 21.8 dBK) | dBK | Total noise temperature of receive chain |
| 11 | **G/T** | $= G_{RX} - 10\log_{10}(T_{sys})$ | dB/K | Receiver figure of merit |
| 12 | Boltzmann constant | $k = -228.6$ | dBW/K/Hz | Thermal noise power spectral density |
| 13 | **C/N$_0$** | $= \text{EIRP} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} - L_{\text{rx}} + G/T - k$ | dBHz | Signal-to-noise density ratio |
| 14 | Data rate | $10\log_{10}(R_b)$ | dBbit/s | Information throughput |
| 15 | **$E_b/N_0$ available** | $= C/N_0 - 10\log_{10}(R_b)$ | dB | Available energy per bit |
| 16 | $E_b/N_0$ required | From modulation/coding selection | dB | Minimum needed for target BER |
| 17 | Implementation loss | Typically 1.5–2.5 dB | dB | Real vs ideal demodulator performance |
| 18 | **LINK MARGIN** | $= E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}}$ | dB | Must be ≥ 3 dB |

---

## 11.3 Antenna types — physics and selection

*[Source: SMAD, Ch. 13; Balanis, *Antenna Theory: Analysis and Design*, 4th ed., 2016]*

The antenna converts guided RF energy (in cables or waveguides) into radiated electromagnetic waves (and vice versa for receive). The key performance parameters are:

- **Gain** ($G$): how much more signal the antenna concentrates in its beam direction compared with an isotropic radiator. Higher gain = narrower beam = more signal, but requires more precise pointing.
- **Beamwidth** ($\theta_{3\text{dB}}$): the angular width of the main beam between the −3 dB (half-power) points.
- **Polarisation:** linear (vertical/horizontal), circular (RHCP/LHCP) or elliptical.

**Fundamental trade-off:** $G \propto 1/\theta_{3\text{dB}}^2$. A higher-gain antenna has a narrower beam and requires more precise pointing. For a spacecraft without accurate pointing, a low-gain omnidirectional antenna is mandatory. For a spacecraft with 0.1° pointing (Chapter 10), a high-gain directional antenna is feasible. Figure 11.2 contrasts the two extremes.

![Antenna patterns: high-gain dish vs patch.](../assets/figures/fig_antenna_pattern.png)

**Figure 11.2** — Gain patterns at 2.25 GHz of a 3 m parabolic dish (35 dBi; narrow 3° main lobe, pronounced sidelobes) and an S-band patch antenna (6 dBi; broad, near-hemispherical lobe). The dish needs AOCS pointing to within a fraction of its beamwidth; the patch tolerates tens of degrees of mispointing at the cost of about 25–30 dB of gain.

### 11.3.1 Antenna types for spacecraft

| Antenna type | Gain (dBi) | Beamwidth | Pointing needed? | Mass (CubeSat) | Physics |
|-------------|-----------|-----------|-------------------|----------------|---------|
| **Monopole/dipole** | 0–2 | ~omnidirectional (toroidal pattern) | No | 5–20 g (deployable wire) | Current distribution on a wire radiates; $\lambda/4$ monopole on ground plane or $\lambda/2$ dipole |
| **Turnstile** | 0–3 | Hemispherical | No | 10–30 g | Two crossed dipoles fed 90° apart; produces circular polarisation |
| **Patch (microstrip)** | 5–8 | 60–90° | Loose (~10°) | 10–50 g | Resonant conducting patch on dielectric substrate over ground plane; $\lambda/2$ patch at resonance |
| **Patch array (2×2, 4×4)** | 10–18 | 15–40° | Moderate (~5°) | 50–200 g | Multiple patch elements with corporate feed network; gain = $G_{\text{element}} + 10\log_{10}(N)$ |
| **Horn** | 15–25 | 10–25° | Yes (~2°) | 100–500 g | Flared waveguide; smooth aperture illumination gives low sidelobes |
| **Parabolic reflector** | 25–45 | 1–5° | Yes (< 1°) | 500 g – 5 kg | Feed at focal point illuminates parabolic dish; $G = \eta_a (\pi D/\lambda)^2$ |
| **Phased array** | 15–35 | Electronically steered, 1–30° | Electronic (no mechanical) | 200 g – 2 kg | Array of elements with individual phase shifters; beam steered by adjusting relative phases; no moving parts |

**Monopole/dipole physics:** A quarter-wave monopole ($L = \lambda/4$) is the simplest antenna. At 437 MHz (UHF), $\lambda = 0.686$ m, so a monopole is 17.2 cm long — easily deployable from a CubeSat using a spring-loaded tape measure or nitinol wire. The radiation pattern is omnidirectional in the azimuthal plane (perpendicular to the wire) and null along the wire axis. Gain is approximately 0–2 dBi depending on the ground-plane size.

**Patch antenna physics:** A microstrip patch antenna consists of a conducting patch (typically rectangular, $L \approx \lambda/2$ at the desired frequency) printed on a dielectric substrate (e.g. Rogers RT/duroid, $\varepsilon_r = 2.2$–$10.2$, thickness 1–3 mm) above a ground plane. The patch resonates at the frequency where its length equals $\lambda_{eff}/2$ (where $\lambda_{eff} = \lambda_0/\sqrt{\varepsilon_r}$). At S-band (2.25 GHz), a patch is approximately 40 × 40 mm — small enough to mount on a CubeSat face. Gain is typically 5–8 dBi with a hemispherical pattern. Circular polarisation is achieved by feeding two orthogonal modes 90° apart (dual-feed or corner-truncated patch).

**Parabolic reflector physics:** A parabolic dish focuses incoming plane waves to its focal point (for receive) or collimates spherical waves from a feed at the focus into a parallel beam (for transmit). The gain depends on the dish diameter $D$ and the wavelength $\lambda$:

> **Key equations — antenna**
>
> **Gain of a parabolic antenna:**
> $$G = \eta_a \left(\frac{\pi D}{\lambda}\right)^2$$
>
> In dBi: $G_{\text{dBi}} = 10\log_{10}\left[\eta_a \left(\frac{\pi D}{\lambda}\right)^2\right]$
>
> where $\eta_a \approx 0.55$–$0.65$ (aperture efficiency, accounting for illumination taper, spillover, blockage and surface errors), $D$ = antenna diameter (m), $\lambda = c/f$.
>
> **Half-power beamwidth (HPBW):**
> $$\theta_{3\text{dB}} \approx \frac{70\lambda}{D} \quad \text{(degrees)}$$
>
> **Patch antenna gain** (single element): typically 5–8 dBi, beamwidth ~60–90°
>
> **Patch array gain** ($N$ elements): $G_{\text{array}} = G_{\text{element}} + 10\log_{10}(N)$
>
> **Pointing loss** (when the antenna is mispointed by angle $\Delta\theta$):
> $$L_{\text{point}} \approx -12 \left(\frac{\Delta\theta}{\theta_{3\text{dB}}}\right)^2 \quad \text{(dB)}$$
>
> This shows that a narrower beam (smaller $\theta_{3\text{dB}}$) is more sensitive to pointing errors.

**Worked example — antenna gain at different bands for a 30 cm dish** ($\eta_a = 0.55$):

| Band | Frequency | $\lambda$ (mm) | $D/\lambda$ | Gain (dBi) | HPBW (°) | Pointing requirement |
|------|-----------|----------------|-------------|-----------|-----------|-------------|
| S-band | 2.25 GHz | 133 | 2.25 | 14.4 | 31 | ~5° |
| X-band | 8.4 GHz | 35.7 | 8.4 | 25.8 | 8.3 | ~1° |
| Ka-band | 26 GHz | 11.5 | 26.1 | 35.7 | 2.7 | ~0.3° |

This table illustrates the fundamental link between frequency, antenna size, gain and pointing requirement. At Ka-band, even a small dish provides high gain — but the beamwidth is so narrow that sub-degree pointing accuracy is essential. This is why Ka-band CubeSat links require a star-tracker and reaction-wheel AOCS (Chapter 10 §10.1).

**Phased array physics:** A phased array consists of multiple antenna elements (patch, dipole or slot) arranged in a grid. Each element has an individual phase shifter (and sometimes amplitude control). By adjusting the relative phase between elements, the beam can be electronically steered without moving the antenna. The beam direction $\theta_s$ for element spacing $d$ and phase increment $\Delta\phi$ is

$$\sin(\theta_s) = \frac{\Delta\phi \cdot \lambda}{2\pi d}$$

Advantages: no moving parts, fast beam steering (microseconds), multiple simultaneous beams possible. Disadvantages: complex, expensive, high power consumption for active arrays, scan loss at wide angles ($\cos\theta_s$ factor). Phased arrays are used on Starlink satellites (Ka-band) and Iridium NEXT (L-band), and are emerging for CubeSats in Ka-band.

---

## 11.4 Free-space path loss by band

FSPL increases with both frequency and distance. At a fixed slant range, higher-frequency bands lose more signal — but this is offset by the ability to use smaller, higher-gain antennas at higher frequencies.

> **Key equations — FSPL (expanded form)**
>
> $$\text{FSPL (dB)} = 20\log_{10}(4\pi) + 20\log_{10}(d) + 20\log_{10}(f) - 20\log_{10}(c)$$
> $$= 21.98 + 20\log_{10}(d_m) + 20\log_{10}(f_{Hz}) - 169.54$$
>
> **Practical form (with km and GHz):**
> $$\text{FSPL (dB)} = 92.45 + 20\log_{10}(d_{km}) + 20\log_{10}(f_{GHz})$$

Figure 11.3 plots this relation for five bands over the slant ranges of interest, from a few hundred kilometres (LEO overhead) to geostationary distance.

![Free-space path loss vs slant range across bands.](../assets/figures/fig_fspl.png)

**Figure 11.3** — Free-space path loss versus slant range (logarithmic) for VHF, UHF, S-, X- and Ka-band. Each doubling of range or of frequency adds 6 dB; the vertical markers show a 1000 km LEO slant range, a low-elevation polar pass and the direct GEO distance.

### 11.4.1 Slant range geometry

The slant range $d$ from a LEO spacecraft to a ground station depends on the orbit altitude $h$ and the elevation angle $\varepsilon$ above the horizon:

$$d = R_E \left[\sqrt{\left(\frac{R_E + h}{R_E}\right)^2 - \cos^2(\varepsilon)} - \sin(\varepsilon)\right]$$

With $R_E = 6378.137$ km, typical LEO orbits give:

| Altitude | Elevation 90° (nadir) | Elevation 30° | Elevation 10° | Elevation 5° |
|----------|------------------------|-------------------|-------------------|-------------------|
| 400 km | 400 km | 740 km | 1440 km | 1800 km |
| 500 km | 500 km | 910 km | 1695 km | 2080 km |
| 600 km | 600 km | 1075 km | 1930 km | 2330 km |

**Design rule:** Always compute the link budget at the **minimum elevation angle** (worst case), typically 5–10°. Below 5°, atmospheric losses increase sharply, ground clutter enters the antenna sidelobes, and the link is generally unusable.

### 11.4.2 FSPL by band and geometry

| Band | Centre frequency | FSPL at 500 km (nadir) | FSPL at 1695 km (10° elevation) | Difference |
|------|-----------------|----------------------|-------------------------------|------------|
| **VHF** | 146 MHz | 129.7 dB | 140.3 dB | 10.6 dB |
| **UHF** | 437 MHz | 139.2 dB | 149.8 dB | 10.6 dB |
| **S-band** | 2250 MHz | 153.5 dB | 164.1 dB | 10.6 dB |
| **X-band** | 8200 MHz | 164.7 dB | 175.3 dB | 10.6 dB |
| **Ka-band** | 26 GHz | 174.7 dB | 185.3 dB | 10.6 dB |

**The elevation angle penalty:** Going from nadir to 10° elevation at 500 km increases FSPL by ~10.6 dB (the distance increases by a factor of 3.4; FSPL scales as $20\log_{10}(3.4) = 10.6$ dB). This is a significant loss and is why contact time at high elevations is much more valuable than contact time at low elevations.

---

## 11.5 Frequency band selection and licensing

*[Source: ITU Radio Regulations, Articles 5 and 22; ISED RSS-SAT; FCC Part 25; IARU Satellite Frequency Coordination]*

Band selection is a **design constraint** that affects data rate, antenna size, atmospheric losses, equipment availability, licensing cost and data policy. The choice of band is one of the earliest and most consequential decisions in mission design. The regulatory process itself is described in Chapter 2 §2.7; this section concentrates on the engineering consequences.

### 11.5.1 Band comparison table

| Band | Frequency range | Allocation | Max BW | Practical data rate | Atmospheric loss (10°) | Rain fade | Licensing (indicative, 2026) | Equipment availability |
|------|----------------|-----------|--------|--------------------|--------------------------|-----------|-----------|-----------------------|
| **VHF** | 144–146 MHz | Amateur | 15 kHz | < 9.6 kbit/s | 0.1 dB | None | IARU coordination (free, 3–6 months) | Many COTS, low cost |
| **UHF** | 435–438 MHz | Amateur | 20 kHz | < 19.2 kbit/s | 0.2 dB | Negligible | IARU coordination (free, 3–6 months) | Many COTS, low cost |
| **S-band** | 2200–2290 MHz | Space research/EES | 5 MHz | 0.1–10 Mbit/s | 0.5 dB | < 0.5 dB | ISED/FCC ($30–45K, 6–12 months) | Many COTS |
| **X-band** | 8025–8400 MHz | EES | 375 MHz | 10–400 Mbit/s | 1.0 dB | 1–3 dB | ISED/FCC + ITU ($50–80K, 12+ months) | Growing COTS |
| **Ka-band** | 25.5–27.0 GHz | EES/FSS | 1.5 GHz | 100–2000+ Mbit/s | 2–5 dB | 3–15 dB (location-dependent) | Complex ITU ($100K+, 18+ months) | Emerging COTS |

*EES = Earth Exploration Satellite; FSS = Fixed Satellite Service*

**Atmospheric attenuation physics:** The atmosphere absorbs and scatters RF energy. Molecular oxygen has a strong absorption line at 60 GHz (used for inter-satellite links where atmospheric penetration is not needed). Water vapour absorbs at 22.2 GHz (near Ka-band). At S-band and below, atmospheric losses are minimal (< 1 dB). At Ka-band, losses of 2–5 dB are typical at 10° elevation, and rain fade can add 3–15 dB in tropical regions.

**Rain fade:** Raindrops scatter and absorb RF energy. The effect scales approximately as $f^2$ — negligible below 4 GHz, significant above 10 GHz, and severe above 20 GHz. Rain fade is characterised by the rain rate (mm/h) and the path length through rain. In tropical regions, rain rates of 50+ mm/h can cause 10+ dB additional loss at Ka-band. Mitigation: adaptive data rate (reduce rate during rain), site diversity (multiple ground stations), power control (increase TX power during fade). For Ka-band links, a rain-fade margin of 5–10 dB is typically included.

**Amateur band regulations (IARU):**
- Non-commercial, educational and experimental use only
- Open data policy: all transmissions must be unencrypted and the protocol must be published
- No commercial data or imagery downlink
- Coordination through the IARU (International Amateur Radio Union): free but takes 3–6 months
- Very popular for university CubeSats (low cost, no licence fees, large amateur community provides free ground-station support via the SatNOGS network)

**Commercial band licensing:**
- Requires national filing (FCC in the US, ISED in Canada, Ofcom in the UK, CNES/ANFR in France) plus ITU coordination for frequencies above 1 GHz
- Costs (indicative, 2026): $30–45K for S-band (typical), $50–80K for X-band, $100K+ for Ka-band
- Timeline: 6–12 months for S-band, 12–18 months for X-band, 18+ months for Ka-band
- Commercial data can be encrypted and proprietary
- Bandwidth allocation may be limited by the national authority

### 11.5.2 Band selection decision tree

```
Required data rate?
  ≤ 9.6 kbit/s AND non-commercial/educational → VHF/UHF amateur (IARU, free, 3–6 months)
  ≤ 10 Mbit/s                                 → S-band commercial (ISED/FCC, $30–45K, 6–12 months)
  ≤ 400 Mbit/s                                → X-band (ISED/FCC + ITU, $50–80K, 12+ months)
  > 400 Mbit/s                                → Ka-band (complex ITU, $100K+, 18+ months, rain fade)
```

---

## 11.6 Modulation and coding — physics and selection

*[Source: CCSDS 131.0-B-4; Sklar, Ch. 7–8; Haykin, Ch. 10; DVB-S2 standard]*

### 11.6.1 Modulation — how information becomes RF

Modulation encodes digital data onto an RF carrier by varying the carrier's amplitude, frequency or phase.

**Phase shift keying (PSK):** The most common modulation family for space communications. The carrier phase is shifted by discrete amounts to represent different bit patterns:

- **BPSK (binary PSK):** 2 phase states (0° and 180°). Each symbol carries 1 bit. Spectral efficiency: 1 bit/s/Hz. Most robust to noise.
- **QPSK (quadrature PSK):** 4 phase states (0°, 90°, 180°, 270°). Each symbol carries 2 bits. Spectral efficiency: 2 bit/s/Hz. Requires the same $E_b/N_0$ as BPSK but doubles the data rate for the same bandwidth. **The standard choice for most space links.**
- **8PSK:** 8 phase states, 3 bits/symbol, spectral efficiency 3 bit/s/Hz. Requires ~3.5 dB more $E_b/N_0$ than QPSK for the same BER.
- **16APSK:** 16 states (amplitude + phase), 4 bits/symbol, spectral efficiency 4 bit/s/Hz. Requires ~7 dB more $E_b/N_0$ than QPSK.

**Frequency shift keying (FSK):** The carrier frequency is shifted between discrete values. Less spectrally efficient than PSK but more tolerant of amplifier non-linearity. Variants:
- **FSK:** simple frequency switching.
- **GFSK (Gaussian FSK):** a Gaussian filter smooths frequency transitions, reducing spectral spreading. Used by many CubeSat UHF radios (AX.25 protocol at 9600 bit/s).
- **MSK (minimum shift keying):** a special case of FSK with the minimum frequency deviation that still allows coherent detection. Constant envelope (important for non-linear amplifiers). Spectral efficiency ~1 bit/s/Hz.

**Why QPSK is preferred over BPSK for space links:** QPSK transmits 2 bits per symbol while requiring the same energy per bit as BPSK. This means QPSK achieves twice the data rate for the same bandwidth and the same $E_b/N_0$ performance. The only additional complexity is that the receiver must resolve 4 phase states instead of 2, which is trivial for modern digital receivers.

Figure 11.4 shows the bit-error-rate curves that underlie the required $E_b/N_0$ values used in the rest of this chapter; Part V §V.8 gives the closed-form expressions behind them.

![Eb/N0 vs BER for common modulations.](../assets/figures/fig_signal_noise.png)

**Figure 11.4** — Bit error rate versus $E_b/N_0$ for BPSK/QPSK, 8-PSK and non-coherent FSK, with a representative concatenated (convolutional + Reed–Solomon) coded curve. The horizontal distance between the uncoded and coded curves at a given BER is the coding gain — about 5 dB at BER $10^{-5}$ for this scheme and more for LDPC codes.

### 11.6.2 Forward error correction (FEC) — coding gain

FEC adds redundant bits to the data stream before transmission. The receiver uses these redundant bits to detect and correct bit errors without retransmission. The improvement in $E_b/N_0$ requirement (compared with uncoded) is called the **coding gain**.

**Why coding is essential for space links:** Space links operate at very low received signal power (femtowatts to picowatts). Without coding, the required $E_b/N_0$ for BER $10^{-6}$ is 10.5 dB. With LDPC coding, this drops to 2.0 dB — a coding gain of 8.5 dB. This is equivalent to increasing the TX power by 7×, or increasing the antenna diameter by 2.7×, or reducing the data rate by 7×. Coding achieves the same benefit at the cost of only a few watts of digital processing power.

**Code types used in space communications:**

| Code type | Code rate | Coding gain at BER $10^{-6}$ | Decoding complexity | Standard | Use |
|-----------|-----------|-------------------------------|---------------------|----------|-----|
| **Convolutional** (K = 7) | 1/2 | ~5.5 dB | Low (Viterbi decoder, hardware) | CCSDS | Legacy telecommand, AX.25 |
| **Convolutional + RS** (concatenated) | ~0.44 | ~7.5 dB | Medium | CCSDS | Standard CCSDS telemetry (many heritage missions) |
| **Turbo code** | 1/2 to 1/6 | ~8–10 dB | High (iterative decoder) | CCSDS | Deep-space links (Mars, Jupiter) |
| **LDPC** (low-density parity check) | 1/2 | ~8.5 dB | Medium-high (iterative BP decoder) | CCSDS, DVB-S2 | Modern space downlinks, **recommended for CubeSats** |
| **LDPC** | 3/4 | ~6.5 dB | Medium-high | CCSDS, DVB-S2 | Balanced performance and throughput |
| **LDPC** | 7/8 | ~5.0 dB | Medium-high | DVB-S2 | Maximum throughput, strong signal |

*[Source: CCSDS 131.0-B-4; DVB-S2 ETSI EN 302 307]*

**Code rate $r$:** The ratio of information bits to total transmitted bits. A rate-1/2 code transmits 1 information bit for every 2 transmitted bits (50 % overhead). This means the channel data rate must be $R_{\text{channel}} = R_{\text{info}} / r$ — a rate-1/2 code requires twice the channel bandwidth for a given information rate.

### 11.6.3 Complete modulation and coding table

| Modulation + coding | $E_b/N_0$ required (BER $10^{-6}$) | Spectral efficiency (bit/s/Hz) | Typical use | Implementation |
|--------------------|------------------------------------|-------------------------------|------------|----------------|
| GMSK uncoded | 10.5 dB | ~1.0 | AX.25 amateur, legacy | Simple radio IC |
| BPSK uncoded | 10.5 dB | 1.0 | Legacy telecommand | Simple |
| QPSK uncoded | 10.5 dB | 2.0 | Simple telemetry | Moderate |
| QPSK + conv (r = 1/2, K = 7) | 5.0 dB | 1.0 | Standard CCSDS TM | Hardware Viterbi |
| QPSK + conv + RS (concatenated) | 3.0 dB | 0.88 | Heritage CCSDS | Hardware |
| QPSK + LDPC (r = 1/2) | 2.0 dB | 1.0 | High-efficiency downlink | FPGA-based |
| QPSK + LDPC (r = 3/4) | 4.0 dB | 1.5 | **Balanced — recommended** | FPGA-based |
| QPSK + LDPC (r = 7/8) | 5.5 dB | 1.75 | Bandwidth-limited | FPGA-based |
| 8PSK + LDPC (r = 3/4) | 6.5 dB | 2.25 | High-rate downlink | FPGA-based |
| 16APSK + LDPC (r = 3/4) | 8.5 dB | 3.0 | Maximum throughput | FPGA-based |

**Design guidance for CubeSats:**
- **UHF amateur:** GMSK or AFSK (AX.25 protocol) at 1.2–9.6 kbit/s channel rate. Add convolutional coding if the link margin is tight.
- **S-band:** QPSK + LDPC (r = 1/2 or r = 3/4). This is the sweet spot: 5.5–8.5 dB coding gain with manageable complexity. Most COTS S-band CubeSat transmitters (Endurosat, NanoAvionics, AAC Clyde — representative examples) support DVB-S2 or CCSDS LDPC natively.
- **X-band / Ka-band:** 8PSK or 16APSK + LDPC for maximum spectral efficiency when bandwidth is limited.

---

## 11.7 Ground stations

The ground station is half of the communication link. Its performance ($G/T$) directly determines the achievable data rate. Upgrading the ground station is often the cheapest way to improve link performance (compared with upgrading the spacecraft transmitter or antenna). The ground-segment architecture as a whole — stations, networks, mission control and data systems — is the subject of Chapter 17.

### 11.7.1 Ground station types

| Type | Antenna | G/T (S-band) | Cost (indicative, 2026) | Availability | Examples |
|------|---------|-------------|------|-------------|---------|
| **Amateur (SatNOGS)** | 10–15 dBi Yagi | −15 to −10 dB/K | Free (volunteer-operated) | Global network, 200+ stations | SatNOGS network |
| **University** | 2–3 m dish | +10 to +15 dB/K | $50–200K (build) | Limited availability | Many universities have S-band stations |
| **Commercial (small)** | 3–5 m dish | +15 to +25 dB/K | $500/pass or $5–20K/month | KSAT Lite, AWS Ground Station | KSAT, Amazon, Leaf Space |
| **Commercial (large)** | 5–13 m dish | +25 to +35 dB/K | $1000/pass or $20–50K/month | SSC, KSAT, ATLAS | SSC (Esrange), KSAT (Svalbard), ATLAS (Fairbanks) |
| **Deep Space Network** | 34–70 m dish | +45 to +60 dB/K | NASA-funded only | DSN (3 sites globally) | Goldstone, Canberra, Madrid |

*[Source: KSAT Lite pricing 2024; AWS Ground Station pricing; SSC SmallSat ground segment]*

### 11.7.2 Contact geometry and pass duration

A LEO satellite is in view of a ground station for a limited time per orbit. The pass duration depends on the orbit altitude and the minimum usable elevation angle. Chapter 7 §7.4.1 gives the geometry: the Earth central angle from the station to the satellite at the elevation mask is

$$\lambda_{\max} = \arccos\!\left(\frac{R_E}{R_E + h}\cos\varepsilon_{\min}\right) - \varepsilon_{\min}$$

and the longest (overhead) pass lasts approximately $t_{\text{contact,max}} \approx (T/\pi)\,\lambda_{\max}$, with $T$ the orbital period. Passes that do not go overhead are shorter; the full elevation-versus-time profile of a pass is shown in Chapter 17 (see Figure 17.2).

| Altitude | Min elevation | Max pass duration | Typical usable duration | Passes/day (mid-latitude) |
|----------|--------------|-------------------|------------------------|--------------------------|
| 400 km | 10° | ~6 min | ~5 min | 3–4 |
| 500 km | 10° | ~7.4 min | ~6 min | 4–5 |
| 600 km | 10° | ~8.5 min | ~7 min | 4–5 |
| 800 km | 10° | ~10.5 min | ~9 min | 5–6 |

The "usable duration" is shorter than the total pass because the link only closes above the minimum elevation angle, and the first and last 30–60 seconds are used for signal acquisition and link set-up.

**Ground station selection criteria:**
- **Location:** Polar stations (Svalbard at 78° N, McMurdo at 78° S) see every orbit of a polar/SSO satellite, providing 12+ contacts per day. Mid-latitude stations see only 3–5 passes. Equatorial stations see even fewer passes of polar satellites.
- **G/T:** Determines the achievable data rate. A 3 dB improvement in G/T allows the data rate to be doubled.
- **Licensing:** Must be compatible with the spacecraft frequency allocation
- **Cost:** Ranges from free (SatNOGS, university) to $1000+/pass (commercial)
- **Reliability:** SLA (service-level agreement) for commercial stations; university stations may have limited operator availability

**EIRP (ground-station transmit, for uplink):** For telecommand uplink, the ground station transmits to the spacecraft. Ground-station EIRP is typically 40–60 dBW for commercial stations, sufficient for robust command links even with low-gain spacecraft receive antennas.

---

## 11.8 Worked examples: complete link budgets

### 11.8.1 EOSat-3U — S-band downlink

> **Worked example — S-band downlink for the 3U EO CubeSat (SuperDove-class)**
>
> **Scenario:** 500 km SSO, S-band (2250 MHz), 1 Mbit/s downlink, 10° minimum elevation (slant range 1695 km, §11.4.1), 3 m ground-station dish ($T_{sys} = 150$ K, $G_{RX} = 35$ dBi at S-band).
>
> | Line | Parameter | Value | Unit | Calculation / source |
> |------|-----------|-------|------|--------------------|
> | 1 | TX power (2 W) | +3.0 | dBW | COTS S-band transmitter |
> | 2 | TX antenna gain (patch) | +6.0 | dBi | Single-element S-band patch |
> | 3 | TX line losses | −1.5 | dB | 15 cm cable + connector |
> | 4 | **EIRP** | **+7.5** | dBW | $3.0 + 6.0 - 1.5$ |
> | 5 | FSPL (2250 MHz, 1695 km) | −164.1 | dB | $92.45 + 20\log_{10}(1695) + 20\log_{10}(2.25)$ |
> | 6 | Atmospheric loss | −0.5 | dB | S-band, 10° elevation |
> | 7 | Pointing loss | −1.0 | dB | 5° mispoint, 80° beamwidth patch |
> | 8 | Polarisation loss (RHCP–RHCP) | −0.3 | dB | Minor axial-ratio mismatch |
> | 9 | RX antenna gain (3 m dish) | +35.0 | dBi | $10\log_{10}(0.6 \times (\pi \times 3.0 / 0.133)^2)$ |
> | 10 | System noise temperature (150 K) | 21.8 | dBK | Professional LNA + sky temperature (receive line loss included) |
> | 11 | **G/T** | **+13.2** | dB/K | $35.0 - 21.8$ |
> | 12 | Boltzmann constant | +228.6 | dBW/K/Hz | $-k$ in link equation |
> | 13 | **C/N$_0$** | **+83.4** | dBHz | $7.5 - 164.1 - 0.5 - 1.0 - 0.3 + 13.2 + 228.6$ |
> | 14 | Data rate (1 Mbit/s) | 60.0 | dBbit/s | $10\log_{10}(10^6)$ |
> | 15 | **$E_b/N_0$ available** | **+23.4** | dB | $83.4 - 60.0$ |
> | 16 | $E_b/N_0$ required (QPSK + LDPC r = 3/4) | 4.0 | dB | From modulation/coding table |
> | 17 | Implementation loss | 2.0 | dB | Real demodulator vs ideal |
> | 18 | **LINK MARGIN** | **+17.4** | dB | $23.4 - 4.0 - 2.0$ |
>
> **Result:** Link closes with 17.4 dB margin (requirement: ≥ 3 dB). **Pass.**
>
> **Design insight:** The generous margin shows that the link is power-rich at 1 Mbit/s. The data rate could be raised considerably:
>
> Maximum data rate at 3 dB margin: $E_b/N_0$ available at maximum rate $= 4.0 + 2.0 + 3.0 = 9.0$ dB, so with $C/N_0 = 83.4$ dBHz, $R_{b,\max} = 10^{(83.4 - 9.0)/10} = 10^{7.44} \approx$ **27 Mbit/s** on power grounds alone.
>
> In practice the S-band allocation, not the power, is the limit: a 5 MHz channel at 1.5 bit/s/Hz (QPSK + LDPC r = 3/4) carries at most about 7.5 Mbit/s. At 5 Mbit/s ($10\log_{10}(5 \times 10^6) = 67.0$ dBbit/s): $E_b/N_0 = 83.4 - 67.0 = 16.4$ dB; margin $= 16.4 - 4.0 - 2.0 = 10.4$ dB. **Pass.** The remaining 7 dB above the requirement is worth keeping as design margin at this stage, or it can be traded later for a lower-power transmitter (0.5 W instead of 2 W costs 6 dB and still closes with 4.4 dB) or a smaller ground dish. The 5 Mbit/s case is the one carried into the data budget of §11.9.

Figure 11.5 shows this budget drawn as a waterfall. Reading it left to right, the gains lift the cumulative $C/N_0$ and the losses pull it down; the final value is compared with what the chosen modulation, coding and data rate require.

![S-band downlink link-budget waterfall.](../assets/figures/fig_link_budget.png)

**Figure 11.5** — Link-budget waterfall for the §11.8.1 S-band downlink (2 W transmitter, 6 dBi patch, 2.25 GHz over the 1695 km slant range at 10° elevation, 3 m ground dish at 150 K). Green bars are gains, orange bars are losses; the dashed line is the received $C/N_0$ of 83.4 dBHz and the dotted line the 73.0 dBHz required at 5 Mbit/s (QPSK + LDPC r = 3/4 plus 2 dB implementation loss). The gap between them is the 10.4 dB link margin.

### 11.8.2 Returning to UniSat-1: UHF link budget at 437 MHz and 9600 bit/s

UniSat-1 uses the UHF amateur band at 437 MHz with a ground station equipped with a 10 dBi Yagi antenna. This is the lowest-cost and simplest communication architecture available to CubeSat missions.

> **Worked example — UHF downlink link budget for UniSat-1**
>
> **Scenario:** 400 km orbit, UHF (437 MHz), 9600 bit/s downlink (GMSK), 10° minimum elevation angle, amateur ground station with 10 dBi Yagi antenna, $T_{sys} = 600$ K (COTS LNA, coaxial cable losses, sky noise near the horizon).
>
> **Slant range at 10° elevation:** From 400 km altitude, the worst-case slant range at 10° elevation is 1440 km (§11.4.1).
>
> | Line | Parameter | Value | Unit | Notes |
> |------|-----------|-------|------|-------|
> | 1 | TX power (0.5 W) | −3.0 | dBW | Standard CubeSat UHF radio |
> | 2 | TX antenna gain (monopole) | 0.0 | dBi | Quarter-wave monopole, ~omnidirectional |
> | 3 | TX line losses | −0.5 | dB | Short cable to antenna |
> | 4 | **EIRP** | **−3.5** | dBW | Low EIRP is the fundamental UHF challenge |
> | 5 | FSPL (437 MHz, 1440 km) | −148.4 | dB | $92.45 + 20\log_{10}(1440) + 20\log_{10}(0.437)$ — ~16 dB less than S-band |
> | 6 | Atmospheric loss | −0.3 | dB | UHF atmospheric loss is minimal |
> | 7 | Pointing loss (omni antenna) | −0.5 | dB | Omni pattern — negligible |
> | 8 | Polarisation loss (linear–linear) | −3.0 | dB | **Major loss** — Faraday rotation in the ionosphere rotates the polarisation randomly |
> | 9 | RX antenna gain (10 dBi Yagi) | +10.0 | dBi | 5-element Yagi, manually tracked |
> | 10 | System noise temperature (600 K) | 27.8 | dBK | Amateur station: warm LNA + cable loss |
> | 11 | **G/T** | **−17.8** | dB/K | Low G/T is the ground-station limitation |
> | 12 | Boltzmann constant | +228.6 | dBW/K/Hz | |
> | 13 | **C/N$_0$** | **+55.1** | dBHz | $-3.5 - 148.4 - 0.3 - 0.5 - 3.0 - 17.8 + 228.6$ |
> | 14 | Data rate (9600 bit/s) | 39.8 | dBbit/s | |
> | 15 | **$E_b/N_0$ available** | **+15.3** | dB | |
> | 16 | $E_b/N_0$ required (GMSK uncoded) | 10.5 | dB | |
> | 17 | Implementation loss | 2.0 | dB | |
>
> **Margin = 15.3 − 10.5 − 2.0 = +2.8 dB. Below the 3 dB requirement — the link does not meet the specification**, and the −3.0 dB polarisation line is only an average: when the Faraday-rotated plane is near-orthogonal to the Yagi the loss can reach 20 dB or more, and the link drops out entirely.
>
> **Fix 1: Add FEC.** Convolutional coding (r = 1/2, K = 7):
> - $E_b/N_0$ required drops to **5.0 dB** (5.5 dB coding gain)
> - Channel rate remains 9600 bit/s, but useful throughput is 4800 bit/s (half is redundancy)
> - **Margin** = 15.3 − 5.0 − 2.0 = **+8.3 dB** — meets the requirement, but the Faraday fades remain.
>
> **Fix 2: Upgrade the ground antenna to a cross-Yagi (13 dBi) with circular polarisation:**
> - RX gain: +13.0 dBi (was +10.0) → +3.0 dB improvement
> - Polarisation loss: −0.5 dB (was −3.0 dB, now RHCP-to-RHCP) → +2.5 dB improvement, and the deep fades disappear
> - Net improvement: +5.5 dB
> - New C/N$_0$: 60.6 dBHz
> - New $E_b/N_0$ available: 60.6 − 39.8 = 20.8 dB
> - **Margin** (with FEC) = 20.8 − 5.0 − 2.0 = **+13.8 dB** — **Pass**; even uncoded the margin would be 8.3 dB.
>
> **Polarisation loss physics:** At UHF (437 MHz), the ionosphere causes Faraday rotation of linearly polarised signals. The rotation angle depends on the total electron content (TEC) along the path and varies with time of day, solar activity and signal path. If the satellite transmits linear polarisation and the ground station receives with linear polarisation, the polarisation planes may be orthogonal at times, causing up to complete signal loss (theoretically infinite loss, practically 20+ dB fades). Using circular polarisation on at least one end (preferably both) eliminates Faraday rotation loss, reducing it to ~0.3–0.5 dB axial-ratio mismatch. **This is why circular polarisation is mandatory for reliable UHF satellite links.**
>
> **Final link budget summary (with FEC + cross-Yagi):** The coding is retained even though the circularly polarised link would close uncoded, because the amateur station's noise temperature, the monopole's pattern nulls and the station's tracking are all less certain than the budget assumes. The 13.8 dB margin absorbs those uncertainties; the cost is half the throughput.
>
> | Parameter | Value |
> |-----------|-------|
> | TX power | 0.5 W |
> | TX antenna | Monopole (0 dBi) |
> | Frequency | 437 MHz |
> | Channel rate | 9600 bit/s |
> | Useful throughput | 4800 bit/s (with r = 1/2 FEC) |
> | Ground antenna | 13 dBi cross-Yagi, RHCP |
> | Link margin | **+13.8 dB** |

**Data throughput for UniSat-1:** At 4800 bit/s useful throughput, a pass with 5 minutes of usable contact (§11.7.2, 400 km) delivers:
$V_{\text{pass}} = 4800 \times 300 \times 0.85 = 1.22$ Mbit $= 153$ kB per pass.

The 0.85 factor accounts for protocol overhead (packet headers, acknowledgements, retransmissions, link set-up time).

With 4 passes/day: $V_{\text{daily}} = 612$ kB/day $\approx$ **0.6 MB/day**. The magnetometer generates $< 1$ kbit/s $\times$ 600 s/orbit $\times$ 15 orbits $= 9$ Mbit/day $= 1.13$ MB/day. **The data budget does not close with a single ground station** — roughly eight passes a day are needed. The cheapest fix is more contact time: using the SatNOGS network (200+ volunteer stations worldwide) can provide 10+ additional contacts per day at no cost, since the open amateur protocol lets any station receive the data. The alternatives are to reduce the data (lower sampling rate or on-board averaging) or to drop the FEC and accept the smaller margin.

**Key lesson from the UniSat-1 link budget:** UHF links are power-starved compared with S-band or X-band. The lower FSPL at 437 MHz (~16 dB less than S-band at a comparable elevation) does not compensate for the low TX power (0.5 W vs 2 W = 6 dB less), low antenna gain (0 dBi vs 6 dBi = 6 dB less), and the higher system noise temperature of amateur stations (600 K vs 150 K = 6 dB worse). FEC coding and circular polarisation are essential for closing a UHF CubeSat link.

---

## 11.9 Data budget

The data budget determines whether the communication system can deliver all mission data to the ground. Even if the link budget closes, the mission fails if the total data volume exceeds the downlink capacity. Chapter 4 §4.8.5 introduced the concept as part of the ConOps data flow; this section quantifies it, and Chapter 12 §12.3.3 sizes the on-board storage that buffers the difference.

> **Key equations — data budget**
>
> **Daily data generation:**
> $$V_{\text{gen}} = R_{\text{payload}} \times t_{\text{imaging}} \times N_{\text{orbits}} \times f_{\text{compression}}$$
>
> **Daily downlink capacity** (the canonical form used throughout this book):
> $$C_{\text{downlink}} = R \cdot N_{\text{passes}} \cdot t_{\text{contact}} \cdot \eta_{\text{protocol}}$$
>
> where $R$ is the useful (information) data rate, $N_{\text{passes}}$ the number of usable passes per day, $t_{\text{contact}}$ the usable contact time per pass and $\eta_{\text{protocol}} = 0.80$–$0.90$ accounts for packet overhead, retransmissions, link set-up time and handshaking. (Some texts write the capacity as $V_{\text{DL}}$; the quantity is the same.)
>
> **Data budget closure:**
> $$C_{\text{downlink}} \geq V_{\text{gen}} \quad \text{(data budget closes)}$$
>
> **Backlog clearance time:** If a temporary excess $V_{\text{stored}}$ has accumulated in on-board storage (after an outage, say) and $C_{\text{downlink}} > V_{\text{gen}}$, the backlog clears in
> $$t_{\text{clear}} = \frac{V_{\text{stored}}}{C_{\text{downlink}} - V_{\text{gen}}}$$
> If $C_{\text{downlink}} < V_{\text{gen}}$ on a sustained basis, the backlog grows without limit — the mission cannot sustain its data generation rate.

> **Worked example — data budget for the 3U EO CubeSat**
>
> **First estimate of generation:** 240 Mbit/s raw imaging data × 5 min/orbit × 15 orbits/day × 0.25 (4:1 JPEG2000 compression)
> $= 240 \times 300 \times 15 \times 0.25 = 270\,000$ Mbit/day = **33.75 GB/day**
>
> That is far beyond any S-band downlink, and it is also unrealistic: not every orbit has a target. Assuming 4 imaging passes per day of 5 minutes each:
>
> $V_{\text{gen}} = 240 \times 10^6 \times 300 \times 4 \times 0.25 = 72\,000$ Mbit $= 9.0$ GB/day
>
> Still too high. Planet's SuperDove images for approximately 1–2 minutes per orbit over priority targets, compresses heavily (10:1 or more) and downlinks selectively.
>
> **Revised generation:** 240 Mbit/s × 1 min/pass × 4 passes/day × 0.10 (10:1 compression) $= 240 \times 60 \times 4 \times 0.10 = 5\,760$ Mbit = **720 MB/day**
>
> **Downlink capacity (S-band at 5 Mbit/s, §11.8.1):**
> $C_{\text{downlink}} = 5 \times 10^6 \times 5 \times 360 \times 0.85 = 7\,650$ Mbit $= 956$ MB/day
>
> **Result:** 956 MB/day > 720 MB/day. **The data budget closes** with 33 % margin.
>
> **Sensitivity:** If the imaging duty cycle doubles (2 min/pass), generation rises to 1440 MB/day > 956 MB/day. Options: (a) X-band for a higher data rate, (b) additional ground stations, (c) more aggressive compression, (d) on-board data prioritisation and selection.

Figure 11.6 puts these numbers in context: daily downlink capacity by band for a single polar ground station, against the daily production of representative payloads. A UHF link cannot even carry housekeeping for an imaging mission; S-band comfortably carries a single-band imager at 1–4 Mbit/s; SAR and hyperspectral payloads need X-band or better.

![Daily downlink capacity by band — data budget closure check.](../assets/figures/fig_data_volume.png)

**Figure 11.6** — Daily downlink capacity (GB/day, logarithmic) for five band and data-rate combinations, each assuming four 8-minute passes per day to a single polar ground station and no protocol overhead. Vertical lines mark the daily data production of representative payloads, from housekeeping-only (5 MB) to a compressed SAR (30 GB). A payload line to the right of a bar means that configuration cannot close the data budget.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Link budget | $\text{Margin} = E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} \geq 3$ dB |
| EIRP | $\text{EIRP} = P_{TX} + G_{TX} - L_{TX}$ — transmitter's effective power in the beam direction |
| FSPL physics | Geometric spreading ($1/d^2$) + aperture scaling ($\lambda^2$); not energy absorption |
| FSPL formula | $92.45 + 20\log_{10}(d_{km}) + 20\log_{10}(f_{GHz})$; increases 6 dB per doubling of frequency or distance |
| Slant range | 1440 km at 400 km / 10° elevation; 1695 km at 500 km / 10°; nadir-to-10° costs ~10.6 dB |
| G/T | Receiver figure of merit: antenna gain minus noise temperature; most important ground-station parameter |
| Antenna types | Monopole (0 dBi, omni) to parabolic (25–45 dBi, narrow beam); gain vs pointing trade-off |
| Antenna gain | $G = \eta_a (\pi D/\lambda)^2$; patch ~6 dBi; 3 m dish: 35 dBi at S-band; 30 cm dish: 14 dBi at S-band, 26 dBi at X-band |
| Pointing loss | $-12(\Delta\theta/\theta_{3\text{dB}})^2$ dB; narrower beam = more sensitive to pointing errors |
| Modulation | QPSK: 2 bits/symbol, same $E_b/N_0$ as BPSK but 2× spectral efficiency; **standard choice** |
| FEC coding | LDPC (r = 3/4): $E_b/N_0 = 4.0$ dB, coding gain ~6.5 dB; **essential for space links** |
| Coding gain | 5–10 dB improvement for free (just digital processing); equivalent to a 3–10× power increase |
| UHF challenges | Low EIRP, Faraday rotation (use circular polarisation), high ground-station noise; FEC mandatory |
| Band selection | UHF for < 9.6 kbit/s (free, amateur); S-band for < 10 Mbit/s; X-band for < 400 Mbit/s; Ka-band for > 400 Mbit/s |
| Rain fade | Negligible below 4 GHz; 1–3 dB at X-band; 3–15 dB at Ka-band; add margin or adaptive rate |
| Ground stations | G/T: amateur −15 dB/K, university +12 dB/K, commercial +25 dB/K; polar stations see every orbit |
| Data budget | $C_{\text{downlink}} = R \cdot N_{\text{passes}} \cdot t_{\text{contact}} \cdot \eta_{\text{protocol}}$ must exceed daily generation; compression ratio is a key lever |
| Licensing | Amateur (free, IARU, 3–6 months); S-band ($30–45K, 6–12 months); X-band ($50–80K, 12+ months), indicative 2026 |

---

## Problems

1. **Decibel arithmetic.** Convert the following to the units requested: 4 W to dBW and dBm; −7 dBW to watts; a gain ratio of 2500 to dB; 27 dBm to watts. Then show, using the dB form of the link equation, why doubling the data rate reduces the link margin by exactly 3 dB.

2. **Free-space path loss.** Compute the FSPL for (a) 437 MHz at 1440 km, (b) 2250 MHz at 1695 km and (c) 8.2 GHz at 2330 km, and check (b) against Figure 11.3. Then compute the slant range from a 550 km orbit at 5°, 10° and 30° elevation using the formula of §11.4.1 and state the FSPL penalty, in dB, of designing to a 5° mask instead of 10° at S-band.

3. **Antenna sizing.** A ground station is to use a 1.2 m dish with $\eta_a = 0.6$. Compute its gain and half-power beamwidth at S-band (2.25 GHz) and X-band (8.2 GHz). If the station's tracking error is 0.5° (1σ), compute the pointing loss at each band and comment on whether the dish is usable at X-band without an upgraded pedestal.

4. **X-band link budget.** Repeat the worked example of §11.8.1 for an X-band downlink: 8.2 GHz, 2 W transmitter, 12 dBi patch array on the spacecraft (beamwidth 30°, 3° mispointing), 1695 km slant range, 1.0 dB atmospheric loss, 0.3 dB polarisation loss, 3 m ground dish with $T_{sys} = 200$ K, 8PSK + LDPC r = 3/4 and 2 dB implementation loss. Find the maximum data rate at 3 dB margin and compare it with the S-band result. Is the limit set by power or by the allocated bandwidth?

5. **Minimum transmitter power.** For the UniSat-1 link of §11.8.2 in its final configuration (cross-Yagi, RHCP, rate-1/2 convolutional code), find the lowest transmitter power that still gives a 3 dB margin. Then find the lowest power that closes uncoded at the full 9600 bit/s. State, in one sentence each, what else changes on the spacecraft when the transmitter power is reduced (Chapter 9) and why the uncoded option is riskier than the numbers suggest.

6. **Faraday rotation.** Explain, with reference to the ionospheric total electron content, why a linearly polarised UHF link suffers random polarisation loss while an S-band link does not need the same treatment (the rotation angle scales as $1/f^2$). If UniSat-1's monopole were replaced by a turnstile antenna radiating RHCP, which line of the link budget changes and by how much?

7. **Data budget closure.** A 3U Earth-observation CubeSat generates 1.2 GB/day after compression. Using $C_{\text{downlink}} = R \cdot N_{\text{passes}} \cdot t_{\text{contact}} \cdot \eta_{\text{protocol}}$ with $\eta_{\text{protocol}} = 0.85$ and 6 minutes of usable contact per pass, find the number of 5 Mbit/s S-band passes per day needed to close the budget. If only five passes are available, what minimum data rate is required, and which band of §11.5.1 would you select? Finally, after a three-day ground-station outage, how long does it take to clear the backlog at 5 Mbit/s and seven passes per day?

8. **Band selection.** A commercial start-up proposes a 6U multispectral imager producing 25 GB/day and wants data on the ground within 6 hours of acquisition. Using the band comparison table, the decision tree of §11.5.2 and Figure 11.6, select a band, estimate the licensing cost and lead time (indicative), and identify the two spacecraft subsystems most affected by that choice (Chapters 9 and 10).

9. **Ground-station trade.** Compare two options for the EOSat-3U mission: (a) a university 2.5 m station with $G/T = +12$ dB/K seeing four passes per day, and (b) a commercial polar station with $G/T = +25$ dB/K seeing twelve passes per day at an indicative \$500 per pass. For each, compute the maximum data rate at 3 dB margin (using the §11.8.1 budget with the new $G/T$) and the daily capacity. Which option delivers more data per year, and at what cost per gigabyte?

10. **Coding versus hardware.** Show that replacing an uncoded QPSK link with QPSK + LDPC r = 1/2 at the same *information* rate is equivalent, in link margin, to increasing the transmitter power by a factor of 7, and state the price paid in channel bandwidth. For an S-band link limited to 5 MHz, which scheme in the table of §11.6.3 maximises the information rate while keeping the EOSat-3U margin of §11.8.1 above 3 dB?

---

## References

1. Wertz, J. R., Everett, D. F. & Puschell, J. J. (eds.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, Ch. 13 (Communications). https://www.space.com/smad
2. ECSS, *ECSS-E-ST-50-05C Rev. 2: Radio Frequency and Modulation*, 2011. https://ecss.nl/standard/ecss-e-st-50-05c-radio-frequency-and-modulation/
3. CCSDS, *131.0-B-4: TM Synchronization and Channel Coding*, 2023. https://public.ccsds.org/Pubs/131x0b4.pdf
4. ITU, *Radio Regulations*, 2020 (Articles 5 and 22). https://www.itu.int/en/publications/ITU-R/pages/default.aspx
5. Maral, G. & Bousquet, M., *Satellite Communications Systems*, 6th ed., Wiley, 2020, Ch. 5. https://www.wiley.com/en-us/Satellite+Communications+Systems
6. Roddy, D., *Satellite Communications*, 4th ed., McGraw-Hill, 2006, Ch. 4–6. https://www.mhprofessional.com
7. Haykin, S., *Communication Systems*, 5th ed., Wiley, 2009. https://www.wiley.com
8. Sklar, B., *Digital Communications: Fundamentals and Applications*, 2nd ed., Prentice Hall, 2001. https://www.pearson.com
9. IARU, *Amateur Satellite Frequency Coordination*, 2023. https://www.iaru.org/satellite/
10. Balanis, C. A., *Antenna Theory: Analysis and Design*, 4th ed., Wiley, 2016.
11. ETSI, *EN 302 307: Digital Video Broadcasting (DVB); Second generation framing structure, channel coding and modulation systems (DVB-S2)*, 2014. https://www.etsi.org
12. Pratt, T., Bostian, C. & Allnutt, J., *Satellite Communications*, 3rd ed., Wiley, 2019.
