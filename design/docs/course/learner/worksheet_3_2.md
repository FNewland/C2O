# Worksheet 3.2: Attitude and Orbit Control System (AOCS)

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Dashboard (AOCS KPI), Pointing Budget, Architecture (AOCS)

---

## Quick Reference: AOCS Concepts

### What is AOCS?

The Attitude and Orbit Control System performs two distinct jobs:

- **Attitude Determination (AD):** Figuring out which way the spacecraft is pointing, using sensors.
- **Attitude Control (AC):** Changing or holding the spacecraft's orientation, using actuators.

These are separate problems. You can know your orientation perfectly (great sensors) but still wobble if your actuators are weak. Or you can have powerful actuators but poor knowledge of where you are pointing.

### Sensors: How Do We Know Where We Are Pointing?

| Sensor | What It Measures | Accuracy | Mass | Power | Cost | When You Use It |
|--------|-----------------|----------|------|-------|------|----------------|
| **Magnetometer** | Direction of Earth's magnetic field | ~2--5 deg | ~5 g | ~0.1 W | ~1 kEUR | Coarse determination; always on for B-field knowledge |
| **Coarse sun sensor** | Direction to the Sun (1--2 axes) | ~2--5 deg | ~5 g | ~0.01 W | ~0.5 kEUR | Safe mode; initial acquisition |
| **Fine sun sensor** | Direction to the Sun (2 axes, high precision) | ~0.1--0.5 deg | ~10 g | ~0.05 W | ~2 kEUR | Sun-pointing missions; backup to star tracker |
| **Star tracker** | Full 3-axis attitude from star patterns | ~0.001--0.01 deg (3--30 arcsec) | 50--350 g | ~0.5--1.5 W | ~20--35 kEUR | Precision pointing for imaging, comms, science |
| **MEMS gyroscope** | Angular rate (rotation speed) | Drift: ~1--10 deg/hr | ~20 g | ~0.3 W | ~3 kEUR | Fills gaps during star tracker blinding; slew control |
| **Earth sensor** | Nadir direction (local vertical) | ~0.1--0.5 deg | ~50 g | ~0.5 W | ~5 kEUR | Nadir-pointing missions (less common on CubeSats) |

**Key insight:** Star trackers are by far the most accurate sensor. They work by photographing the sky, matching the observed star pattern to an onboard catalogue, and computing the spacecraft's orientation to within a few arcseconds. However, they are blinded by the Sun, Moon, or Earth limb entering their field of view, so sun sensors or gyroscopes provide backup during these periods.

### Actuators: How Do We Control Our Orientation?

| Actuator | How It Works | Torque | Precision | Mass | Power | When You Use It |
|----------|-------------|--------|-----------|------|-------|----------------|
| **Permanent magnet** | Aligns spacecraft with Earth's B-field like a compass needle | ~$10^{-5}$ N m (restoring) | ~10--15 deg | ~20 g | 0 W | Passive stabilisation for missions with no pointing need |
| **Hysteresis rods** | Dissipate rotational energy through magnetic hysteresis; damp tumbling | N/A (damping only) | N/A | ~10 g each | 0 W | Always paired with permanent magnet for passive stabilisation |
| **Magnetorquers (MTQ)** | Electromagnetic coils that interact with Earth's magnetic field to produce torque | ~$10^{-6}$--$10^{-4}$ N m | ~2--5 deg (as primary); N/A (as desaturation) | ~10--30 g each | 0.1--0.2 W | **Primary control** for low-precision missions; **desaturation** of reaction wheels for all RW-based systems |
| **Reaction wheels (RW)** | Spinning flywheels that exchange angular momentum with the spacecraft | ~$10^{-4}$--$10^{-2}$ N m | ~0.001--0.01 deg | 30--120 g each | 0.3--1.5 W | Precision pointing -- any mission requiring < 2 deg accuracy |
| **Thrusters** | Expel mass (cold gas, ions) to produce torque via offset force | Variable | ~0.1--1 deg | System-dependent | High | Large slews; orbit adjust; when MTQs are insufficient (deep space) |

**Magnetorquers -- two critical roles:**

1. **As primary actuators** (missions needing only 2--5 deg pointing): MTQs alone provide 3-axis control, but only in LEO where Earth's magnetic field is strong. They cannot produce torque parallel to the local field vector, so control authority varies around the orbit.

2. **As desaturation actuators** (all RW-based missions): Reaction wheels absorb disturbance torques by spinning up. Over time, they accumulate angular momentum and reach saturation (maximum spin speed). MTQs "dump" this stored momentum by generating opposing torque against Earth's magnetic field. This is done approximately once per orbit, taking 5--15 minutes.

**Reaction wheels -- why 4 wheels?** Three wheels (one per axis) provide minimum 3-axis control. A 4th wheel on a skew axis provides single-fault tolerance: if any one wheel fails, the remaining three still provide full 3-axis control.

### AOCS Architecture Decision Table

Use this table to select your architecture based on your pointing requirement:

| Pointing Requirement | Architecture | Sensors | Actuators | Mass | Power | Cost |
|---------------------|-------------|---------|-----------|------|-------|------|
| > 5 deg (no pointing need) | Passive magnetic | Magnetometer | Permanent magnet + hysteresis rods | ~50 g | 0 W | ~2 kEUR |
| 2--5 deg | Magnetorquer-based | Coarse sun sensors + magnetometer | 3-axis MTQ | ~100 g | 0.2 W | ~8 kEUR |
| 0.1--2 deg | Reaction wheel system | Fine sun sensors + magnetometer | 3--4 RW + 3 MTQ (desaturation) | ~500 g | 2--4 W | ~35 kEUR |
| < 0.1 deg | Fine pointing | Star tracker + fine sun sensors | 4 RW + 3 MTQ | ~800 g | 3--5 W | ~55 kEUR |
| < 0.01 deg | Very fine pointing | Star tracker + MEMS gyro + sun sensors | 4 RW + 3 MTQ | ~1200 g | 4--6 W | ~80 kEUR |

**How to use this table:** Find your mission's pointing requirement (from your requirements worksheet). Read across to find the architecture, sensors, and actuators you need. If your mission is an Earth-observation camera needing 0.05 deg pointing, you need fine pointing (star tracker + 4 RW + 3 MTQ). If your mission is an IoT relay needing only 5 deg pointing, magnetorquers alone suffice.

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

## Worked Example: UniSat-1 (1U) AOCS

### Architecture Selection

UniSat-1 carries a MEMS magnetometer payload that does not require accurate pointing. In fact, a slowly rotating/tumbling state provides magnetic field measurements across multiple directions, improving data quality.

**Architecture: Passive magnetic stabilisation** (permanent magnet + hysteresis rods). No pointing error budget is needed because there is no pointing requirement.

| Parameter | Value |
|-----------|-------|
| Pointing accuracy | ~10--15 deg (to local magnetic field) |
| Mass | ~30--50 g |
| Power | 0 W |
| Cost | ~1--2 kEUR |

### Disturbance Torques at 400 km

Even though UniSat-1 has no active AOCS, understanding the disturbance environment confirms that the passive magnet provides sufficient restoring torque.

**Gravity gradient** (1U is nearly cubic, so $I_z \approx I_x$, making this very small):

$T_{gg} \approx \frac{3 \times 3.986 \times 10^{14}}{2 \times (6.771 \times 10^6)^3} \times |I_z - I_x| \approx 1 \times 10^{-8}$ N m

**Aerodynamic** ($\rho$ at 400 km $\approx 4 \times 10^{-12}$ kg/m$^3$, $v \approx 7670$ m/s):

$T_{\text{aero}} = 0.5 \times 4 \times 10^{-12} \times 7670^2 \times 2.2 \times 0.01 \times 0.01 \approx 3 \times 10^{-8}$ N m

**Permanent magnet restoring torque:** $\sim 1 \times 10^{-5}$ N m -- three orders of magnitude larger than all disturbances. **The satellite stays field-aligned.**

---

## Part A: AOCS Architecture Selection

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

## Part B: Disturbance Torque Calculations

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

## Part C: Reaction Wheel Sizing

*Skip this section if your mission uses passive magnetic or MTQ-only architecture.*

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

## Part D: Pointing Error Budget

*Skip this section if your mission uses passive magnetic stabilisation (no pointing requirement).*

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

## Part E: SpaceCDF Verification

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

## Decision Justification

Explain WHY you chose your AOCS architecture. Consider the alternatives and what drove your decision.

**Why this architecture and not a simpler one?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Why this architecture and not a more capable one?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**What is the single biggest risk in your AOCS design?**

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
