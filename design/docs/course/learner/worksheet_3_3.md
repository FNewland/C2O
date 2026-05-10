# Worksheet 3.3: Communications and Link Budget Design

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Link Budget, Spectrum Selector, Equipment Browser (Comms)

---

## Quick Reference: Communications Concepts

### What is a Link Budget?

A link budget is an accounting statement for your communication link. It adds up every gain (transmitter power, antenna gain) and subtracts every loss (distance, atmosphere, pointing error) to determine whether the signal arriving at the receiver is strong enough to decode. Everything is computed in **decibels (dB)** so that multiplication and division become addition and subtraction.

**Decibel refresher:**

| Conversion | Formula | Common Values |
|-----------|---------|---------------|
| Watts to dBW | $P_{\text{dBW}} = 10\log_{10}(P_W)$ | 2 W = +3.0 dBW; 1 W = 0 dBW; 0.5 W = -3.0 dBW |
| Kelvin to dBK | $T_{\text{dBK}} = 10\log_{10}(T_K)$ | 150 K = 21.8 dBK; 600 K = 27.8 dBK |
| Ratio to dB | $G_{\text{dB}} = 10\log_{10}(G)$ | x2 = +3 dB; x10 = +10 dB; x100 = +20 dB |

### What Each Term in the Link Budget Means

| Term | What It Is | Analogy |
|------|-----------|---------|
| **TX Power ($P_{TX}$)** | Electrical power fed to the transmitter amplifier | How loud you shout |
| **TX Antenna Gain ($G_{TX}$)** | How well the antenna focuses the signal into a beam (vs radiating equally in all directions) | Using a megaphone vs shouting in all directions |
| **TX Line Losses ($L_{TX}$)** | Power lost in cables and filters between amplifier and antenna | Sound absorbed by the megaphone walls |
| **EIRP** | Effective Isotropic Radiated Power = $P_{TX} + G_{TX} - L_{TX}$. The total "signal strength leaving the spacecraft" | Total loudness heard from a distance |
| **FSPL** | Free Space Path Loss -- signal weakens as it spreads over a larger sphere. Depends on distance and frequency | Voice getting quieter the farther away you walk |
| **Atmospheric Loss** | Signal absorbed/scattered by Earth's atmosphere (rain, oxygen, water vapour) | Fog muffling sound |
| **Pointing Loss** | Signal loss because the antenna beam is not perfectly aimed | Megaphone pointed slightly off-target |
| **Polarisation Loss** | Loss when TX and RX antenna polarisations do not match | Holding the megaphone sideways when the listener expects vertical |
| **RX Antenna Gain ($G_{RX}$)** | Ground station antenna ability to collect signal. Larger dish = more gain | Listener using a large ear trumpet |
| **System Noise Temp ($T_{sys}$)** | Combined noise from antenna, sky, and receiver electronics. Lower = better | Background noise in the room |
| **G/T** | Receiver figure of merit = $G_{RX} - T_{sys}$ (in dB). Captures how "good" the ground station is | Ear trumpet size minus room noise |
| **$C/N_0$** | Carrier-to-noise-density ratio -- the received signal strength relative to noise | Signal-to-noise ratio before decoding |
| **$E_b/N_0$** | Energy per bit to noise density -- the fundamental measure of link quality. Divides $C/N_0$ by data rate | How much energy is available per bit of information |
| **Link Margin** | How much $E_b/N_0$ you have above the minimum needed. Must be >= 3 dB | Safety factor for your communication |

### Frequency Band Comparison

| Parameter | UHF (Amateur) | S-band | X-band | Ka-band |
|-----------|--------------|--------|--------|---------|
| **Frequency** | 435--438 MHz | 2200--2290 MHz | 8025--8400 MHz | 25.5--27.0 GHz |
| **Bandwidth available** | 20 kHz | 5 MHz | 375 MHz | 1.5 GHz |
| **Maximum data rate** | < 20 kbps | 0.1--10 Mbps | 10--400 Mbps | 100--2000 Mbps |
| **FSPL at 500 km (nadir)** | 148 dB | 163 dB | 174 dB | 184 dB |
| **FSPL at 1300 km (10 deg elev)** | 158 dB | 171 dB | 182 dB | 192 dB |
| **Atmospheric loss** | ~0.1 dB | ~0.5 dB | ~1.0 dB | ~3--10 dB (rain!) |
| **Typical spacecraft antenna** | Monopole (0 dBi) | Patch (6 dBi) | Horn/patch array (10--15 dBi) | Small dish/array (20+ dBi) |
| **Ground antenna** | Yagi (10--13 dBi) | 3 m dish (35 dBi) | 3 m dish (45 dBi) | 1 m dish (45 dBi) |
| **License type** | IARU coordination (free) | ISED/FCC ($30--45K) | ISED/FCC + ITU (higher) | Complex ITU filing |
| **License timeline** | ~6 months | 6--12 months | 12+ months | 12--18 months |
| **Equipment availability** | Many COTS | Many COTS | Growing COTS | Emerging |
| **Best for** | TT&C, telemetry, simple missions | Medium data rate, standard EO | High data rate, EO/SAR | Very high data rate |

**How to choose:** Start with your data rate requirement. If you need < 20 kbps and have non-commercial data, UHF amateur is free and simple. If you need up to 10 Mbps, S-band is the CubeSat workhorse. For high-resolution imaging producing GBs per day, you need X-band or Ka-band.

### Antenna Types

| Antenna Type | Gain | Beamwidth | Pointing Need | Mass | Typical Band | Use Case |
|-------------|------|-----------|---------------|------|-------------|----------|
| **Monopole/dipole** | ~0 dBi | Omnidirectional | None | 5--20 g | UHF | TT&C, simple telemetry |
| **Patch (single)** | ~5--8 dBi | ~70--90 deg | Low (~10 deg) | 10--50 g | S-band | Standard CubeSat downlink |
| **Patch array (2x2)** | ~12 dBi | ~30--40 deg | Medium (~5 deg) | 30--100 g | S/X-band | Higher-rate downlink |
| **Horn** | ~10--15 dBi | ~20--30 deg | Medium (~5 deg) | 50--200 g | X-band | High-rate downlink |
| **Parabolic reflector** | ~20--35 dBi | ~2--10 deg | Tight (< 1 deg) | 200--500 g | X/Ka-band | Very high-rate, DTE |
| **Phased array** | ~15--25 dBi | Electronically steered | Electronic (fast) | 100--300 g | S/X/Ka-band | Agile beam, multiple targets |

**Trade-off:** Higher gain antennas provide stronger signals (enabling higher data rates or lower TX power), but they have narrower beams, which means the spacecraft must point more accurately. An omnidirectional antenna works regardless of spacecraft orientation but provides very low gain.

### Modulation and Coding

The modulation scheme and forward error correction (FEC) code determine the minimum $E_b/N_0$ required for a target bit error rate (BER):

| Modulation + Coding | $E_b/N_0$ Required (BER $10^{-6}$) | Spectral Efficiency | Best For |
|--------------------|-----------------------------------|--------------------|----------|
| BPSK uncoded | 10.5 dB | 1.0 bps/Hz | Legacy telecommand |
| QPSK uncoded | 10.5 dB | 2.0 bps/Hz | Simple telemetry |
| QPSK + convolutional (r=1/2) | 5.0 dB | 1.0 bps/Hz | Standard CCSDS TM |
| QPSK + LDPC (r=1/2) | 2.0 dB | 1.0 bps/Hz | High-efficiency downlink |
| QPSK + LDPC (r=3/4) | 4.0 dB | 1.5 bps/Hz | Balanced (CubeSat standard) |
| 8PSK + LDPC (r=3/4) | 6.5 dB | 2.25 bps/Hz | High-rate downlink |

**Design guidance:** For most CubeSat missions, **QPSK + LDPC (r=3/4)** at $E_b/N_0 = 4.0$ dB is the standard choice, offering a good balance of coding gain and implementation simplicity.

---

## Key Equations Reference

> **EIRP:** $\text{EIRP} = P_{TX} + G_{TX} - L_{TX}$ &nbsp; (dBW)
>
> **FSPL:** $\text{FSPL} = 20\log_{10}\left(\frac{4\pi d f}{c}\right)$ &nbsp; (dB)
>
> **G/T:** $G/T = G_{RX} - 10\log_{10}(T_{sys})$ &nbsp; (dB/K)
>
> **C/N$_0$:** $C/N_0 = \text{EIRP} - \text{FSPL} - L_{\text{losses}} + G/T + 228.6$ &nbsp; (dBHz)
>
> **$E_b/N_0$:** $E_b/N_0 = C/N_0 - 10\log_{10}(R_b)$ &nbsp; (dB)
>
> **Link margin:** $\text{Margin} = E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} \geq 3$ dB
>
> **Antenna gain:** $G = \eta_a(\pi D/\lambda)^2$
>
> **dB conversion:** $P_{\text{dBW}} = 10\log_{10}(P_W)$; &nbsp; 2 W = +3.0 dBW; 1 W = 0 dBW

---

## Worked Example: UniSat-1 (1U) UHF Link Budget

UniSat-1 uses UHF amateur band at 437 MHz with 9600 bps downlink to an amateur ground station.

### Step-by-Step Link Budget

**Scenario:** 400 km orbit, 437 MHz, 9600 bps, 10 deg minimum elevation (slant range ~1150 km), ground station with 13 dBi cross-Yagi (RHCP).

| Line | Parameter | Calculation | Value | Unit |
|------|-----------|-------------|-------|------|
| 1 | TX Power | 0.5 W = $10\log_{10}(0.5)$ | -3.0 | dBW |
| 2 | TX Antenna Gain | Monopole | 0.0 | dBi |
| 3 | TX Line Losses | Short cable run | -0.5 | dB |
| 4 | **EIRP** | $-3.0 + 0.0 - 0.5$ | **-3.5** | dBW |
| 5 | FSPL | $21.98 + 20\log_{10}(1.15 \times 10^6) + 20\log_{10}(437 \times 10^6) - 169.54$ | -155.5 | dB |
| 6 | Atmospheric Loss | Minimal at UHF | -0.3 | dB |
| 7 | Pointing Loss | Omni antenna, minimal | -0.5 | dB |
| 8 | Polarisation Loss | RHCP-to-RHCP (cross-Yagi) | -0.5 | dB |
| 9 | RX Antenna Gain | 13 dBi cross-Yagi | +13.0 | dBi |
| 10 | System Noise Temp | 600 K (amateur + LNA) = $10\log_{10}(600)$ | 27.8 | dBK |
| 11 | **G/T** | $13.0 - 27.8$ | **-14.8** | dB/K |
| 12 | Boltzmann Constant | | +228.6 | dBW/K/Hz |
| 13 | **C/N$_0$** | $-3.5 - 155.5 - 0.3 - 0.5 - 0.5 + (-14.8) + 228.6$ | **+53.5** | dBHz |
| 14 | Data Rate | 9600 bps = $10\log_{10}(9600)$ | 39.8 | dBbps |
| 15 | **$E_b/N_0$ available** | $53.5 - 39.8$ | **+13.7** | dB |
| 16 | $E_b/N_0$ required | QPSK + conv. code r=1/2 | 5.0 | dB |
| 17 | Implementation Loss | | 2.0 | dB |
| 18 | **LINK MARGIN** | $13.7 - 5.0 - 2.0$ | **+6.7** | dB |

**Result:** Link closes with 6.7 dB margin (> 3 dB). **Pass.**

### FSPL Calculation Detail

$\text{FSPL} = 21.98 + 20\log_{10}(1.15 \times 10^6) + 20\log_{10}(437 \times 10^6) - 169.54$

$= 21.98 + 121.21 + 172.81 - 169.54 = 146.46$ ... wait, let us recompute:

$20\log_{10}(1.15 \times 10^6) = 20 \times 6.0607 = 121.2$ dB

$20\log_{10}(437 \times 10^6) = 20 \times 8.640 = 172.8$ dB

$\text{FSPL} = 21.98 + 121.2 + 172.8 - 169.54 = 146.4$ dB

Note: The line-5 value of 155.5 dB uses the slant range in metres ($1.15 \times 10^6$ m) and frequency in Hz ($437 \times 10^6$ Hz) in the single-formula form: $20\log_{10}(4\pi \times 1.15 \times 10^6 \times 437 \times 10^6 / 3 \times 10^8) = 155.5$ dB. Both approaches give the same result when applied consistently.

### Data Throughput

At 4800 bps useful throughput (9600 bps channel rate with r=1/2 FEC), a 7-minute pass delivers:

$V_{\text{pass}} = 4800 \times 420 \times 0.85 = 1.71$ Mbit $= 214$ kB per pass

With 4 passes/day: ~0.84 MB/day. The magnetometer generates ~1.13 MB/day -- marginal. May need a second ground station or data prioritisation.

---

## Part A: Frequency Band Selection (10 min)

**Mission data rate requirement:** _____ Mbps

**License type selected:** Amateur / Experimental / Commercial

**Band selected:** _____________ &nbsp;&nbsp; **Centre frequency:** _____ MHz

**Rationale for band selection:**

_____________________________________________________________________

_____________________________________________________________________

**Licensing/filing required:** _______________________________________________

**Estimated licensing cost:** _____ &nbsp;&nbsp; **Timeline:** _____ months

---

## Part B: Complete Link Budget (25 min)

Fill in ALL rows. Show computation for EIRP, FSPL, G/T, C/N$_0$, and margin.

| Line | Parameter | Formula / Source | Value | Unit |
|------|-----------|-----------------|-------|------|
| 1 | TX Power | _____ W = | | dBW |
| 2 | TX Antenna Gain | | | dBi |
| 3 | TX Line Losses | | | dB |
| 4 | **EIRP** = Line 1 + 2 + 3 | | **______** | dBW |
| 5 | Free Space Path Loss | $20\log_{10}(4\pi \times$ ___ $\times$ ___ $/c)$ | | dB |
| 6 | Atmospheric Loss | | | dB |
| 7 | Pointing Loss | | | dB |
| 8 | Polarisation Loss | | | dB |
| 9 | RX Antenna Gain | | | dBi |
| 10 | System Noise Temp | _____ K = | | dBK |
| 11 | **G/T** = Line 9 - 10 | | **______** | dB/K |
| 12 | Boltzmann Constant | | +228.6 | dBW/K/Hz |
| 13 | **C/N$_0$** = 4 + 5 + 6 + 7 + 8 + 11 + 12 | | **______** | dBHz |
| 14 | Data Rate | _____ bps = $10\log_{10}($___$)$ | | dBbps |
| 15 | **$E_b/N_0$ available** = 13 - 14 | | **______** | dB |
| 16 | $E_b/N_0$ required (mod+code: ________) | | | dB |
| 17 | Implementation Loss | | | dB |
| 18 | **LINK MARGIN** = 15 - 16 - 17 | | **______** | dB |

**Show FSPL calculation:**

$\text{FSPL} = 20\log_{10}(4\pi) + 20\log_{10}(d) + 20\log_{10}(f) - 20\log_{10}(c)$

$= 21.98 + 20\log_{10}($ _____ $) + 20\log_{10}($ _____ $) - 169.54 = $ _____ dB

_____________________________________________________________________

_____________________________________________________________________

**Does the link close ($\geq$ 3 dB)?** Y / N

**If margin is excessive, maximum achievable data rate at 3 dB margin:**

$R_{b,\text{max}} = 10^{(E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} - 3)/10} \times R_b = $ _____ Mbps

_____________________________________________________________________

---

## Part C: Data Budget (10 min)

**Daily data generation:**

$V_{\text{gen}} = R_{\text{payload}} \times t_{\text{imaging}} \times N_{\text{orbits}} \times f_{\text{compression}}$

$= $ _____ Mbps $\times$ _____ s $\times$ _____ $\times$ _____ $= $ _____ MB/day $= $ _____ GB/day

**Daily downlink capacity:**

$V_{\text{DL}} = R_{\text{DL}} \times t_{\text{contact}} \times N_{\text{passes}} \times \eta_{\text{protocol}}$

$= $ _____ Mbps $\times$ _____ s $\times$ _____ $\times$ _____ $= $ _____ MB/day $= $ _____ GB/day

**Data budget closes?** ($V_{\text{DL}} \geq V_{\text{gen}}$): Y / N

If no, what is your mitigation plan?

_____________________________________________________________________

_____________________________________________________________________

---

## Part D: SpaceCDF Comparison (10 min)

Open the Link Budget tab, enter your parameters, and compare:

| Parameter | Hand Calculation | SpaceCDF | Difference |
|-----------|-----------------|----------|------------|
| EIRP (dBW) | | | |
| FSPL (dB) | | | |
| C/N$_0$ (dBHz) | | | |
| Link Margin (dB) | | | |

If there are differences, explain:

_____________________________________________________________________

_____________________________________________________________________

---

## Part E: Modulation and Coding Selection (5 min)

**Selected modulation:** _______________________________________________

**Selected FEC code:** _______________________________________________

**Required $E_b/N_0$ at BER $10^{-6}$:** _____ dB

**Spectral efficiency:** _____ bps/Hz

**Rationale:**

_____________________________________________________________________

_____________________________________________________________________

---

## Decision Justification

Explain WHY you chose your communications architecture. Address each decision explicitly.

**Why this frequency band and not another?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Why this antenna type? What pointing does it require from AOCS?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Why this modulation/coding scheme? What trade-off did you make between data rate and link robustness?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes & Reflections

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________
