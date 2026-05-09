# Worksheet 3.2: Attitude and Orbit Control System (AOCS)

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Dashboard (AOCS KPI), Pointing Budget, Architecture (AOCS)

---

## Key Equations Reference

> **Gravity gradient torque:** $T_{gg} = \frac{3\mu}{2a^3}|I_z - I_x|\sin(2\theta)$
>
> **Aerodynamic torque:** $T_{\text{aero}} = \frac{1}{2}\rho v^2 C_D A \cdot d_{cp-cm}$
>
> **SRP torque:** $T_{\text{SRP}} = \frac{S}{c} A_s (1+q) \cdot d_{sp-cm}$
>
> **Magnetic torque:** $T_{\text{mag}} = M \times B$
>
> **Momentum storage:** $H = T_{\text{dist}} \times t_{\text{desat}}/2$
>
> **Pointing error (RSS):** $\theta_{\text{total}} = \sqrt{\sum \theta_i^2}$
>
> **MTQ torque:** $T_{\text{MTQ}} = m_{\text{dipole}} \times B \times \sin(\alpha)$

---

## Part A: AOCS Architecture Selection (10 min)

**Pointing requirement from your mission:** _____ deg (3-sigma)

**AOCS architecture selected** (tick one):

- [ ] Passive magnetic (> 5 deg)
- [ ] Magnetorquers only (2--5 deg)
- [ ] Reaction wheels + MTQ (0.1--2 deg)
- [ ] Fine pointing: RW + star tracker + MTQ (< 0.1 deg)
- [ ] Very fine: RW + ST + gyro + MTQ (< 0.01 deg)

**Justification for selection:**

_____________________________________________________________________

_____________________________________________________________________

**Estimated AOCS mass:** _____ kg &nbsp;&nbsp;&nbsp; **Estimated AOCS power:** _____ W

---

## Part B: Disturbance Torque Calculations (20 min)

Calculate at least 2 disturbance torques for your spacecraft and orbit. Show all working.

**Spacecraft properties:**

| Parameter | Value | Unit |
|-----------|-------|------|
| Mass | | kg |
| Form factor | | U |
| $I_z$ (largest MOI) | | kg m$^2$ |
| $I_x$ (smallest MOI) | | kg m$^2$ |
| Cross-section area (largest face) | | m$^2$ |
| $d_{cp-cm}$ (CP-CM offset estimate) | | m |
| Orbit altitude | | km |

**1. Gravity gradient torque:**

$T_{gg} = \frac{3 \times 3.986 \times 10^{14}}{2 \times (\ \ \ \ )^3} \times |I_z - I_x| = $

_____________________________________________________________________

_____________________________________________________________________

$T_{gg} = $ _____ N m

**2. Aerodynamic torque** ($\rho$ at _____ km $\approx$ _____ kg/m$^3$):

$T_{\text{aero}} = \frac{1}{2} \times$ _____ $\times$ _____ $^2 \times 2.2 \times$ _____ $\times$ _____ $= $

_____________________________________________________________________

$T_{\text{aero}} = $ _____ N m

**3. (Optional) Solar radiation pressure torque:**

_____________________________________________________________________

_____________________________________________________________________

$T_{\text{SRP}} = $ _____ N m

**4. (Optional) Residual magnetic dipole torque** ($M \approx$ _____ A m$^2$, $B \approx 3 \times 10^{-5}$ T):

$T_{\text{mag}} = $ _____ $\times$ _____ $= $ _____ N m

**Summary:**

| Source | Torque (N m) |
|--------|-------------|
| Gravity gradient | |
| Aerodynamic | |
| SRP | |
| Magnetic dipole | |
| **Total (RSS or sum)** | |

**Which disturbance dominates?** _______________________________________________

---

## Part C: Reaction Wheel Sizing (10 min)

**1. Torque requirement** ($\geq 2\times$ total disturbance):

$T_{\text{RW,req}} = 2 \times$ _____ $= $ _____ N m $= $ _____ mN m

**2. Momentum storage** (desaturation interval = 1 orbit = _____ s):

$H = T_{\text{dist}} \times \frac{t_{\text{desat}}}{2} = $ _____ $\times \frac{\ \ \ \ }{2} = $ _____ mN m s

**3. Selected reaction wheel:**

| Parameter | Required | Selected Product |
|-----------|----------|-----------------|
| Torque | _____ mN m | _____ mN m |
| Momentum | _____ mN m s | _____ mN m s |
| Mass | -- | _____ g |
| Power | -- | _____ W |
| Quantity | 4 (3+1 redundancy) | |

---

## Part D: Pointing Error Budget (15 min)

Complete the RSS pointing error budget:

| Error Source | Value (deg) | Value$^2$ |
|-------------|------------|-----------|
| Sensor accuracy | | |
| Actuator resolution | | |
| Alignment knowledge | | |
| Thermal distortion | | |
| Jitter (RW) | | |
| Orbit knowledge | | |
| Timing error | | |
| **Sum of squares** | | |
| **RSS Total** = $\sqrt{\text{sum}}$ | **= _____ deg** | |

**Requirement:** _____ deg

**Margin:** _____ deg (_____ %)

**Does the pointing budget close?** Y / N

**Which error source dominates?** _______________________________________________

**What action would most improve the budget?** _________________________________

_____________________________________________________________________

---

## Part E: SpaceCDF Verification (10 min)

Compare your hand calculations to SpaceCDF's Pointing Budget display:

| Parameter | Hand Calculation | SpaceCDF | Match? |
|-----------|-----------------|----------|--------|
| RSS pointing error | _____ deg | _____ deg | |
| Dominant contributor | ____________ | ____________ | |
| Margin to requirement | _____ % | _____ % | |

If there are differences, explain:

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
