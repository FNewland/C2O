# Worksheet 3.3: Communications and Link Budget Design

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Link Budget, Spectrum Selector, Equipment Browser (Comms)

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

## Notes & Reflections

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________
