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

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Construct a complete link budget from first principles (in decibels)
2. Compute free space path loss for any frequency and slant range
3. Select an appropriate frequency band based on data rate, licensing, and equipment availability
4. Choose modulation and coding scheme based on required $E_b/N_0$
5. Size an antenna (gain, beamwidth, mass) for the selected frequency
6. Determine data throughput and verify the data budget closes
7. Use SpaceCDF's link budget tool and spectrum selector

---

## 1. The Link Budget Concept (15 min)

### Teaching Notes

*[Source: SMAD, Ch. 13; ECSS-E-ST-50-05C; Roddy, Ch. 4]*

The link budget is the accounting statement for the communication link. Every gain and every loss from transmitter to receiver is tallied in **decibels (dB)** to determine whether the link "closes" -- meaning the received signal is strong enough to decode with acceptable error rate.

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

| Conversion | Formula |
|-----------|---------|
| Watts to dBW | $P_{\text{dBW}} = 10 \log_{10}(P_W)$ |
| dBW to Watts | $P_W = 10^{P_{\text{dBW}}/10}$ |
| Ratio to dB | $G_{\text{dB}} = 10 \log_{10}(G)$ |
| Common values | 2 W = +3.0 dBW; 1 W = 0 dBW; 0.5 W = -3.0 dBW |

---

## 2. Complete Link Budget Equation (30 min)

### Teaching Notes

> **Key Equations -- Link Budget (dB form)**
>
> **EIRP** (Effective Isotropic Radiated Power):
> $$\text{EIRP} = P_{TX} + G_{TX} - L_{TX} \quad \text{(dBW)}$$
>
> **Free Space Path Loss:**
> $$\text{FSPL} = 20\log_{10}\left(\frac{4\pi d}{\lambda}\right) = 20\log_{10}\left(\frac{4\pi d f}{c}\right) \quad \text{(dB)}$$
> where $d$ = slant range (m), $f$ = frequency (Hz), $c = 3 \times 10^8$ m/s.
>
> **Receiver figure of merit:**
> $$G/T = G_{RX} - 10\log_{10}(T_{sys}) \quad \text{(dB/K)}$$
>
> **Carrier-to-noise density ratio:**
> $$C/N_0 = \text{EIRP} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} + G/T - k \quad \text{(dBHz)}$$
> where $k = -228.6$ dBW/K/Hz (Boltzmann constant).
>
> **Energy per bit to noise density:**
> $$E_b/N_0 = C/N_0 - 10\log_{10}(R_b) \quad \text{(dB)}$$
> where $R_b$ = data rate (bps).
>
> **Link margin:**
> $$\text{Margin} = E_b/N_{0,\text{available}} - E_b/N_{0,\text{required}} - L_{\text{implementation}} \quad \text{(dB)}$$
>
> **Requirement:** Margin $\geq$ 3 dB for Phase B+ (per ECSS-E-ST-50-05C).

### Complete Link Budget Table

| Line | Parameter | Formula / Typical Value | Unit |
|------|-----------|------------------------|------|
| 1 | TX Power | $P_{TX}$ (e.g., 2 W = +3.0) | dBW |
| 2 | TX Antenna Gain | $G_{TX}$ (e.g., +6.0 for patch) | dBi |
| 3 | TX Line Losses | $L_{TX}$ (cables, filters: -1.5) | dB |
| 4 | **EIRP** | $= P_{TX} + G_{TX} - L_{TX}$ | dBW |
| 5 | Free Space Path Loss | $\text{FSPL} = 20\log_{10}(4\pi d f/c)$ | dB |
| 6 | Atmospheric Loss | $L_{\text{atm}}$ (-0.5 typical for S-band) | dB |
| 7 | Pointing Loss | $L_{\text{point}}$ (-1.0 typical) | dB |
| 8 | Polarisation Loss | $L_{\text{pol}}$ (-0.3 typical for circular) | dB |
| 9 | RX Antenna Gain | $G_{RX}$ (e.g., +35 for 3 m dish) | dBi |
| 10 | System Noise Temp | $T_{sys}$ (e.g., 150 K = 21.8 dBK) | dBK |
| 11 | **G/T** | $= G_{RX} - 10\log_{10}(T_{sys})$ | dB/K |
| 12 | Boltzmann Constant | $k = -228.6$ | dBW/K/Hz |
| 13 | **C/N$_0$** | $= \text{EIRP} - \text{FSPL} + G/T - k - L_{\text{losses}}$ | dBHz |
| 14 | Data Rate | $10\log_{10}(R_b)$ | dBbps |
| 15 | **$E_b/N_0$ available** | $= C/N_0 - 10\log_{10}(R_b)$ | dB |
| 16 | $E_b/N_0$ required | From modulation/coding selection | dB |
| 17 | Implementation Loss | Typically 2.0 dB | dB |
| 18 | **LINK MARGIN** | $= E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}}$ | dB |

---

## 3. Free Space Path Loss by Band (10 min)

### Teaching Notes

FSPL increases with both frequency and distance. At a fixed slant range, higher-frequency bands lose more signal.

> **Key Equations -- FSPL (expanded form)**
>
> $$\text{FSPL (dB)} = 20\log_{10}(4\pi) + 20\log_{10}(d) + 20\log_{10}(f) - 20\log_{10}(c)$$
> $$= 21.98 + 20\log_{10}(d_m) + 20\log_{10}(f_{Hz}) - 169.54$$

| Band | Centre Frequency | FSPL at 500 km (nadir) | FSPL at 1300 km (10 deg elev) |
|------|-----------------|----------------------|-------------------------------|
| **UHF** | 437 MHz | 148.3 dB | 157.6 dB |
| **S-band** | 2250 MHz | 162.5 dB | 170.8 dB |
| **X-band** | 8200 MHz | 173.8 dB | 182.1 dB |
| **Ka-band** | 26 GHz | 183.8 dB | 192.1 dB |

**Note:** The 10 deg minimum elevation corresponds to a slant range of approximately 1300 km for a 500 km orbit. All link budgets should be computed at the worst-case (minimum elevation) geometry.

---

## 4. Modulation, Coding, and Eb/N0 (15 min)

### Teaching Notes

*[Source: CCSDS 131.0-B-4; DVB-S2 standard; Maral & Bousquet, Ch. 5]*

The choice of modulation scheme and forward error correction (FEC) code determines the required $E_b/N_0$ for a target bit error rate (BER).

| Modulation + Coding | $E_b/N_0$ Required (BER $10^{-6}$) | Spectral Efficiency | Typical Use |
|--------------------|------------------------------------|---------------------|------------|
| BPSK uncoded | 10.5 dB | 1.0 bps/Hz | Legacy telecommand |
| QPSK uncoded | 10.5 dB | 2.0 bps/Hz | Simple telemetry |
| QPSK + convolutional (r=1/2) | 5.0 dB | 1.0 bps/Hz | Standard CCSDS TM |
| QPSK + LDPC (r=1/2) | 2.0 dB | 1.0 bps/Hz | High-efficiency downlink |
| QPSK + LDPC (r=3/4) | 4.0 dB | 1.5 bps/Hz | Balanced performance |
| 8PSK + LDPC (r=3/4) | 6.5 dB | 2.25 bps/Hz | High-rate downlink |
| 16APSK + LDPC (r=3/4) | 8.5 dB | 3.0 bps/Hz | Maximum throughput |

**Design guidance:** For CubeSat missions, QPSK + LDPC (r=1/2 or r=3/4) is the most common choice, offering a good balance of coding gain and implementation simplicity.

---

## 5. Frequency Band Selection and Licensing (15 min)

### Teaching Notes

*[Source: ITU Radio Regulations, Articles 5 and 22; ISED RSS-SAT; FCC Part 25]*

Band selection is a **design constraint** that affects data rate, antenna size, atmospheric losses, equipment availability, licensing cost, and data policy.

| Band | Frequency | Max BW | Data Rate | Antenna Size | License | Equipment |
|------|-----------|--------|-----------|-------------|---------|-----------|
| **UHF (amateur)** | 435--438 MHz | 20 kHz | < 20 kbps | Dipole/monopole | IARU coord (free) | Many COTS |
| **S-band** | 2200--2290 MHz | 5 MHz | 0.1--10 Mbps | Patch antenna | ISED/FCC ($30--45K) | Many COTS |
| **X-band** | 8025--8400 MHz | 375 MHz | 10--400 Mbps | Horn/patch array | ISED/FCC + ITU | Growing COTS |
| **Ka-band** | 25.5--27.0 GHz | 1.5 GHz | 100--2000 Mbps | Small dish/array | Complex ITU | Emerging |

### Antenna Gain and Beamwidth

> **Key Equations -- Antenna**
>
> **Gain of a parabolic antenna:**
> $$G = \eta_a \left(\frac{\pi D}{\lambda}\right)^2$$
>
> In dBi: $G_{\text{dBi}} = 10\log_{10}\left[\eta_a \left(\frac{\pi D}{\lambda}\right)^2\right]$
>
> where $\eta_a \approx 0.55$--$0.65$ (aperture efficiency), $D$ = antenna diameter (m), $\lambda = c/f$.
>
> **Half-power beamwidth (HPBW):**
> $$\theta_{3\text{dB}} \approx \frac{70\lambda}{D} \quad \text{(degrees)}$$
>
> **Patch antenna gain** (single element): typically 5--8 dBi
> **Patch array gain** (N elements): $G_{\text{array}} = G_{\text{element}} + 10\log_{10}(N)$

### Band Selection Decision Tree

```
Required data rate?
  <= 20 kbps AND non-commercial data -> UHF amateur (IARU, free, 6 mo)
  <= 10 Mbps                         -> S-band commercial (ISED/FCC, $30-45K, 6-12 mo)
  <= 400 Mbps                        -> X-band (ISED/FCC + ITU, higher cost, 12+ mo)
  > 400 Mbps                         -> Ka-band (complex ITU, rain fade, emerging)
```

---

## 6. Worked Example: Complete Link Budget (15 min)

> **Worked Example -- S-band Downlink for 3U EO CubeSat**
>
> **Scenario:** 500 km SSO, S-band (2250 MHz), 1 Mbps downlink, 10 deg minimum elevation, 3 m ground station dish.
>
> | Line | Parameter | Value | Unit |
> |------|-----------|-------|------|
> | 1 | TX Power (2 W) | +3.0 | dBW |
> | 2 | TX Antenna Gain (patch) | +6.0 | dBi |
> | 3 | TX Line Losses | -1.5 | dB |
> | 4 | **EIRP** | **+7.5** | dBW |
> | 5 | FSPL (2250 MHz, 1300 km slant) | -170.8 | dB |
> | 6 | Atmospheric Loss | -0.5 | dB |
> | 7 | Pointing Loss | -1.0 | dB |
> | 8 | Polarisation Loss | -0.3 | dB |
> | 9 | RX Antenna Gain (3 m dish) | +35.0 | dBi |
> | 10 | System Noise Temp (150 K) | 21.8 | dBK |
> | 11 | **G/T** | **+13.2** | dB/K |
> | 12 | Boltzmann Constant | +228.6 | dBW/K/Hz |
> | 13 | **C/N$_0$** = 7.5 - 170.8 - 0.5 - 1.0 - 0.3 + 13.2 + 228.6 | **+76.7** | dBHz |
> | 14 | Data Rate (1 Mbps = $10\log_{10}(10^6)$) | 60.0 | dBbps |
> | 15 | **$E_b/N_0$ available** = 76.7 - 60.0 | **+16.7** | dB |
> | 16 | $E_b/N_0$ required (QPSK + LDPC r=3/4) | 4.0 | dB |
> | 17 | Implementation Loss | 2.0 | dB |
> | 18 | **LINK MARGIN** = 16.7 - 4.0 - 2.0 | **+10.7** | dB |
>
> **Result:** Link closes with 10.7 dB margin (requirement: >= 3 dB). **Pass.**
>
> **Design insight:** The generous 10.7 dB margin suggests the link is over-designed for 1 Mbps. The team could increase the data rate:
> $R_{b,\text{max}} = 10^{(16.7 - 4.0 - 2.0 - 3.0)/10} \times 10^6 = 10^{0.77} \times 10^6 \approx$ **5.9 Mbps** at minimum 3 dB margin.

---

### 1U Worked Example: UniSat-1

**UHF Link Budget: 437 MHz at 9600 bps**

UniSat-1 uses the UHF amateur band at 437 MHz with a ground station equipped with a 10 dBi Yagi antenna. This is the lowest-cost and simplest communication architecture available to CubeSat missions.

> **Worked Example -- UHF Downlink Link Budget for UniSat-1**
>
> **Scenario:** 400 km orbit, UHF (437 MHz), 9600 bps downlink, 10 deg minimum elevation angle, amateur ground station with 10 dBi Yagi antenna.
>
> **Slant range at 10 deg elevation:**
> From 400 km altitude, the worst-case slant range at 10 deg elevation is approximately 1150 km.
>
> | Line | Parameter | Value | Unit |
> |------|-----------|-------|------|
> | 1 | TX Power (0.5 W) | -3.0 | dBW |
> | 2 | TX Antenna Gain (monopole, ~0 dBi) | 0.0 | dBi |
> | 3 | TX Line Losses | -0.5 | dB |
> | 4 | **EIRP** | **-3.5** | dBW |
> | 5 | FSPL (437 MHz, 1150 km slant) | -155.5 | dB |
> | 6 | Atmospheric Loss | -0.3 | dB |
> | 7 | Pointing Loss (omni antenna -- minimal) | -0.5 | dB |
> | 8 | Polarisation Loss (linear to linear, worst case) | -3.0 | dB |
> | 9 | RX Antenna Gain (10 dBi Yagi) | +10.0 | dBi |
> | 10 | System Noise Temp (600 K -- amateur station with LNA) | 27.8 | dBK |
> | 11 | **G/T** | **-17.8** | dB/K |
> | 12 | Boltzmann Constant | +228.6 | dBW/K/Hz |
> | 13 | **C/N$_0$** = -3.5 - 155.5 - 0.3 - 0.5 - 3.0 + (-17.8) + 228.6 | **+48.0** | dBHz |
> | 14 | Data Rate (9600 bps = $10\log_{10}(9600)$) | 39.8 | dBbps |
> | 15 | **$E_b/N_0$ available** = 48.0 - 39.8 | **+8.2** | dB |
> | 16 | $E_b/N_0$ required (GMSK uncoded, BER $10^{-5}$) | 10.5 | dB |
> | 17 | Implementation Loss | -2.0 | dB |
>
> **Wait -- that gives a negative margin!** $8.2 - 10.5 - 2.0 = -4.3$ dB. The link does NOT close with uncoded GMSK.
>
> **Fix: Add forward error correction (FEC).** Using convolutional coding (r=1/2):
> - $E_b/N_0$ required drops to **5.0 dB** (from 10.5 dB uncoded)
> - Effective data rate halves to 4800 bps useful throughput (9600 bps channel rate)
> - **Margin** = 8.2 - 5.0 - 2.0 = **+1.2 dB** -- still marginal.
>
> **Further fix: Upgrade ground antenna to a cross-Yagi (13 dBi) with circular polarisation:**
> - RX gain: +13.0 dBi (was +10.0)
> - Polarisation loss: -0.5 dB (was -3.0 dB, now RHCP-to-RHCP)
> - Net improvement: +3.0 + 2.5 = **+5.5 dB**
> - New C/N$_0$: 53.5 dBHz
> - New $E_b/N_0$ available: 53.5 - 39.8 = 13.7 dB
> - **Margin** = 13.7 - 5.0 - 2.0 = **+6.7 dB** -- **Pass** (> 3 dB).
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

**Key lesson from UniSat-1 link budget:** UHF links are power-starved compared to S-band or X-band. The lower FSPL at 437 MHz does not compensate for the low TX power (0.5 W vs 2 W), low antenna gain (0 dBi vs 6 dBi), and higher system noise temperature of amateur stations. FEC coding and a reasonable ground antenna are essential for closing a UHF CubeSat link.

**Data throughput:** At 4800 bps useful throughput, a 7-minute pass delivers:
$V_{\text{pass}} = 4800 \times 420 \times 0.85 = 1.71$ Mbit $= 214$ kB per pass.

With 4 passes/day: $V_{\text{daily}} = 856$ kB/day $\approx$ **0.84 MB/day**. The magnetometer generates < 1 kbps $\times$ 600 s/orbit $\times$ 15 orbits = 9 Mbit/day = 1.13 MB/day. This is marginal -- the team may need to prioritise data or add a second ground station.

---

## 7. Data Budget (10 min)

### Teaching Notes

> **Key Equations -- Data Budget**
>
> **Daily data generation:**
> $$V_{\text{gen}} = R_{\text{payload}} \times t_{\text{imaging}} \times N_{\text{orbits}} \times f_{\text{compression}}$$
>
> **Daily downlink capacity:**
> $$V_{\text{DL}} = R_{\text{downlink}} \times t_{\text{contact}} \times N_{\text{passes}} \times \eta_{\text{protocol}}$$
>
> **Data budget closure:**
> $$V_{\text{DL}} \geq V_{\text{gen}} \quad \text{(data budget closes)}$$

> **Worked Example -- Data Budget for 3U EO CubeSat**
>
> **Generation:** 240 Mbps raw x 5 min/orbit x 15 orbits/day x 0.25 (4:1 compression) = **4.5 GB/day**
>
> **Downlink:** 5 Mbps effective x 7 min/pass x 5 passes/day x 0.85 (protocol overhead) = **1.49 GB/day**
>
> **Result:** 1.49 GB/day < 4.5 GB/day. **Data budget does NOT close.**
>
> **Options:** (a) reduce imaging duty cycle, (b) increase data rate (X-band), (c) add ground stations, (d) increase compression ratio.

---

## 8. SpaceCDF Exercise (30 min)

### Instructions

1. **Spectrum Selector** (Dashboard): Select your license type and frequency band
2. **Link Budget** tab:
   - Enter TX power, antenna type, frequency, ground station parameters
   - Review the computed link margin
   - Verify it meets >= 3 dB requirement
3. **Compare** to your hand calculation from the worked example
4. **Equipment Browser:** Select a transponder and antenna that match your band choice
   - Note RF compatibility warnings
5. Complete Worksheet 3.3

### Discussion Questions

- What is the most impactful parameter in your link budget? (Usually FSPL or G/T)
- How does doubling the data rate affect link margin? (Reduces by 3 dB)
- Could you use a lower-power transmitter and still close the link?
- Does your data budget close? If not, what is the cheapest fix?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Link budget | $\text{Margin} = E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} \geq 3$ dB |
| EIRP | $\text{EIRP} = P_{TX} + G_{TX} - L_{TX}$ -- transmitter's effective power |
| FSPL | $20\log_{10}(4\pi df/c)$; increases 6 dB per doubling of frequency or distance |
| G/T | Receiver figure of merit: antenna gain minus noise temperature |
| Modulation | QPSK + LDPC (r=3/4): $E_b/N_0 = 4.0$ dB -- standard CubeSat choice |
| Band selection | UHF for < 20 kbps; S-band for < 10 Mbps; X-band for < 400 Mbps |
| Antenna gain | $G = \eta_a (\pi D/\lambda)^2$; patch ~6 dBi; 3 m dish ~35 dBi at S-band |
| Data budget | Daily downlink capacity must exceed daily data generation |
| Licensing | Amateur (free, IARU); Commercial (ISED/FCC, $30--45K, 6--12 months) |
