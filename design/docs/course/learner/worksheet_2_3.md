# Worksheet 2.3: Orbit Selection and Mission Architecture

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Mission Architecture, Orbit Trade Advisor

---

## Key Equations Reference

> **Orbital period:** $T = 2\pi \sqrt{a^3/\mu}$ &nbsp;&nbsp; where $a = R_E + h$, $\mu = 3.986 \times 10^{14}$ m$^3$/s$^2$, $R_E = 6371$ km
>
> **Orbital velocity:** $v = \sqrt{\mu/a}$
>
> **Eclipse fraction:** $f_{\text{ecl}} = \frac{1}{\pi} \arccos\left(\frac{\sqrt{a^2 - R_E^2}}{a}\right)$
>
> **Sun-synchronous inclination:** $\cos(i) = -\frac{2\dot{\Omega} a^{7/2}}{3 R_E^2 J_2 \sqrt{\mu}}$ &nbsp;&nbsp; where $J_2 = 1.0826 \times 10^{-3}$
>
> **Hohmann $\Delta V$:** $\Delta V_1 = \sqrt{\mu/r_1}\left(\sqrt{2r_2/(r_1+r_2)} - 1\right)$
>
> **Swath width:** $W = 2h\tan(\theta)$

---

## Part A: Orbital Mechanics Calculations

**Your selected orbit:** Altitude $h$ = _____ km, &nbsp; Inclination $i$ = _____ deg, &nbsp; Type: __________

Show all working for each calculation:

**1. Semi-major axis:**

$a = R_E + h = 6371 + $ _____ $= $ _____ km $= $ _____ m

_____________________________________________________________________

**2. Orbital period:**

$T = 2\pi\sqrt{a^3/\mu} = 2\pi\sqrt{$ _____ $^3 /\ 3.986 \times 10^{14}} = $ _____ s $= $ _____ min

_____________________________________________________________________

_____________________________________________________________________

**3. Orbital velocity:**

$v = \sqrt{\mu/a} = \sqrt{3.986 \times 10^{14} /\ }$ _____ $= $ _____ m/s

_____________________________________________________________________

**4. Eclipse fraction (maximum):**

$f = \frac{1}{\pi}\arccos\left(\frac{\sqrt{a^2 - R_E^2}}{a}\right) = \frac{1}{\pi}\arccos\left(\frac{\sqrt{\ }}{\ }\right) = $ _____

_____________________________________________________________________

_____________________________________________________________________

**5. Sunlight and eclipse time per orbit:**

$t_{\text{sun}} = T \times (1 - f) = $ _____ $\times$ _____ $= $ _____ min

$t_{\text{ecl}} = T \times f = $ _____ $\times$ _____ $= $ _____ min

**6. Sun-synchronous inclination** (if applicable):

$\cos(i) = $ _____ $\Rightarrow i = $ _____ deg

Does this match your selected inclination? Y / N

_____________________________________________________________________

---

## Part B: Orbit Trade Matrix

From SpaceCDF's Orbit Trade Advisor, record the top 3 candidates:

| Rank | Orbit Type | Alt (km) | Inc (deg) | GSD (m) | Revisit (d) | Natural Lifetime (yr) | FCC 5-yr? | Score |
|------|-----------|---------|---------|---------|-------------|----------------------|-----------|-------|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |

**Selected orbit:** ___________ **Rationale:** ___________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Part C: Debris Compliance

For your selected orbit:

| Parameter | Value |
|-----------|-------|
| Natural orbital lifetime | _____ years |
| FCC 5-year compliant? | Y / N |
| IADC 25-year compliant? | Y / N |
| Propulsion needed for deorbit? | Y / N |
| If yes, estimated deorbit $\Delta V$ | _____ m/s |
| Deorbit method (if needed) | _____________________________________ |

**Show $\Delta V$ calculation if propulsion needed:**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Part D: Downstream Cascade Analysis

How does your orbit selection affect each subsystem? Fill in the impact:

| Subsystem | Orbit Parameter That Matters | Impact on Your Design |
|-----------|-----------------------------|-----------------------|
| Payload (GSD) | Altitude = _____ km | GSD = _____ m |
| EPS (eclipse) | Eclipse fraction = _____ | Eclipse duration = _____ min |
| Comms (link) | Slant range at 10 deg elev = _____ km | FSPL increase = _____ dB |
| Thermal | Eclipse/sunlight cycling | Hot case / Cold case concern: ______ |
| AOCS | Orbit rate = _____ deg/min | Nadir tracking rate needed |
| Propulsion | Lifetime = _____ yr | Propulsion needed? Y / N |
| Radiation | TID estimate = _____ krad/yr | Electronics class: ____________ |

---

## Part E: Discussion

What would happen to your mission if you moved the orbit **100 km higher**?

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

What would happen if you moved it **100 km lower**?

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
