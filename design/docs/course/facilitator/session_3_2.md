# Session 3.2: Attitude and Orbit Control System (AOCS)

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--2.4 and 3.1 (requirements, orbit, power defined)
**SpaceCDF Tabs:** Dashboard (AOCS KPI), Pointing Budget, Architecture (AOCS)

---

## References

- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.1 (ADCS)](https://www.space.com/smad)
- [Sidi, *Spacecraft Dynamics and Control*, 1997, Ch. 4--9](https://www.cambridge.org/core/books/spacecraft-dynamics-and-control/82B47C7B6E2AA53BFAADAF26C2A79F14)
- [Markley & Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*, 2014](https://link.springer.com/book/10.1007/978-1-4939-0802-8)
- [ECSS, *ECSS-E-ST-60-10C: Control Performance*, 2008](https://ecss.nl/standard/ecss-e-st-60-10c-control-performance/)
- [ECSS, *ECSS-E-ST-60-20C: Star Tracker Performance Testing*, 2019](https://ecss.nl/standard/ecss-e-st-60-20c-star-tracker-performance-testing/)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Explain the distinction between attitude determination and attitude control
2. Select AOCS hardware architecture based on pointing requirements
3. Compute a pointing error budget using root-sum-square (RSS) combination
4. Calculate disturbance torques from gravity gradient, aerodynamic drag, solar radiation pressure, and residual magnetic dipole
5. Size actuators (reaction wheels, magnetorquers) for the computed disturbance environment
6. Verify AOCS design against requirements using SpaceCDF's pointing budget tool

---

## 1. AOCS Fundamentals (20 min)

### Teaching Notes

*[Source: SMAD, Ch. 11.1; Markley & Crassidis, Ch. 1--3]*

The AOCS performs two distinct functions:

| Function | Purpose | Hardware |
|----------|---------|---------|
| **Attitude Determination** (AD) | Know the spacecraft's orientation relative to a reference frame | Sensors: star tracker, sun sensors, magnetometer, gyroscope, Earth sensor |
| **Attitude Control** (AC) | Change or maintain the spacecraft's orientation | Actuators: reaction wheels, magnetorquers, thrusters, control moment gyros |

### AOCS Architecture Selection by Pointing Requirement

| Pointing Requirement | Architecture | Typical Hardware | Mass | Power | Cost |
|---------------------|-------------|-----------------|------|-------|------|
| > 5 deg | Passive magnetic | Permanent magnet + hysteresis rods | ~0.05 kg | 0 W | ~2 kEUR |
| 2--5 deg | Magnetorquers + sun sensors | 3-axis MTQ + coarse sun sensors | ~0.10 kg | 0.2 W | ~8 kEUR |
| 0.1--2 deg | Reaction wheels + MTQ | 3--4 RW + 3 MTQ + fine sun sensors | ~0.50 kg | 2--4 W | ~35 kEUR |
| < 0.1 deg | Fine pointing (RW + star tracker) | 4 RW + ST + 3 MTQ + sun sensors | ~0.80 kg | 3--5 W | ~55 kEUR |
| < 0.01 deg | Very fine pointing | 4 RW + ST + MEMS gyro + 3 MTQ | ~1.20 kg | 4--6 W | ~80 kEUR |

**Real mission examples:**

| Mission | Pointing Req | Architecture | Mass |
|---------|-------------|-------------|------|
| **Astrocast** (IoT) | ~5 deg | MTQ + sun sensors | 0.1 kg |
| **Planet SuperDove** (EO) | ~0.1 deg | 4 RW + ST + MTQ | 0.8 kg |
| **CAPSTONE** (cislunar) | ~0.05 deg | RW + ST + sun sensors | ~1.0 kg |

---

## 2. Disturbance Torques (25 min)

### Teaching Notes

In LEO, four external torques disturb the spacecraft attitude. The AOCS must counteract them continuously.

*[Source: SMAD, Ch. 11.1; Sidi, Ch. 5]*

> **Key Equations -- Disturbance Torques**
>
> **Gravity gradient torque** (worst case, 45 deg off nadir):
> $$T_{gg} = \frac{3\mu}{2a^3} |I_z - I_x| \sin(2\theta) \approx \frac{3\mu}{2a^3} |I_z - I_x|$$
> where $I_z$, $I_x$ are principal moments of inertia (kg m$^2$) and $\theta = 45\degree$ for worst case.
>
> **Aerodynamic torque:**
> $$T_{\text{aero}} = \frac{1}{2} \rho v^2 C_D A_{\text{ref}} \, d_{cp-cm}$$
> where $\rho$ = atmospheric density (kg/m$^3$), $v$ = orbital velocity (m/s), $C_D \approx 2.2$, $A_{\text{ref}}$ = cross-sectional area (m$^2$), $d_{cp-cm}$ = offset between centre of pressure and centre of mass (m).
>
> **Solar radiation pressure torque:**
> $$T_{\text{SRP}} = \frac{S}{c} A_s (1 + q) \, d_{sp-cm}$$
> where $S = 1361$ W/m$^2$, $c = 3 \times 10^8$ m/s, $A_s$ = illuminated area (m$^2$), $q$ = reflectance (0--1), $d_{sp-cm}$ = offset between solar pressure centre and centre of mass (m).
>
> **Residual magnetic dipole torque:**
> $$T_{\text{mag}} = M \times B$$
> where $M$ = spacecraft residual magnetic dipole moment (A m$^2$), $B$ = local geomagnetic field strength (T). For LEO: $B \approx 3 \times 10^{-5}$ T; typical CubeSat $M \approx 0.01$--$0.1$ A m$^2$.

> **Worked Example -- Disturbance Torques for a 3U CubeSat at 500 km**
>
> **Spacecraft properties:** 3U (100 x 100 x 340 mm), mass = 5 kg, $I_z = 0.035$ kg m$^2$, $I_x = 0.007$ kg m$^2$, $A_{\text{ref}} = 0.034$ m$^2$ (3U face), $d_{cp-cm} = 0.02$ m.
>
> **Gravity gradient:**
> $T_{gg} = \frac{3 \times 3.986 \times 10^{14}}{2 \times (6.871 \times 10^6)^3} \times |0.035 - 0.007|$
> $= \frac{1.196 \times 10^{15}}{6.494 \times 10^{20}} \times 0.028 = 1.84 \times 10^{-6} \times 0.028 = 5.2 \times 10^{-8}$ N m
>
> **Aerodynamic** (at 500 km, $\rho \approx 6 \times 10^{-13}$ kg/m$^3$):
> $T_{\text{aero}} = 0.5 \times 6 \times 10^{-13} \times 7617^2 \times 2.2 \times 0.034 \times 0.02$
> $= 0.5 \times 6 \times 10^{-13} \times 5.80 \times 10^7 \times 2.2 \times 0.034 \times 0.02 = 1.6 \times 10^{-8}$ N m
>
> **Solar radiation pressure:**
> $T_{\text{SRP}} = \frac{1361}{3 \times 10^8} \times 0.034 \times 1.5 \times 0.02 = 4.6 \times 10^{-9}$ N m
>
> **Magnetic** ($M = 0.05$ A m$^2$, $B = 3 \times 10^{-5}$ T):
> $T_{\text{mag}} = 0.05 \times 3 \times 10^{-5} = 1.5 \times 10^{-6}$ N m
>
> **Summary:**
>
> | Source | Torque (N m) | Dominant? |
> |--------|-------------|-----------|
> | Gravity gradient | $5.2 \times 10^{-8}$ | No |
> | Aerodynamic | $1.6 \times 10^{-8}$ | No |
> | Solar radiation pressure | $4.6 \times 10^{-9}$ | No |
> | Residual magnetic dipole | $1.5 \times 10^{-6}$ | **Yes** |
> | **Total (RSS)** | $\approx 1.5 \times 10^{-6}$ | |
>
> The residual magnetic dipole dominates for CubeSats due to COTS electronics and short wiring runs. This is a key finding -- magnetic cleanliness matters.

---

## 3. Actuator Sizing (20 min)

### Teaching Notes

### Reaction Wheel Sizing

> **Key Equations -- Reaction Wheel Sizing**
>
> **Torque requirement** (to counteract disturbances + provide control authority):
> $$T_{\text{RW}} \geq k \times T_{\text{disturbance,total}}$$
> where $k \geq 2$ is the control margin factor (typically 2--5).
>
> **Momentum storage requirement** (accumulation between desaturation cycles):
> $$H_{\text{required}} = T_{\text{disturbance}} \times \frac{t_{\text{desat}}}{2}$$
> where $t_{\text{desat}}$ is the time between magnetorquer desaturation events (typically one orbit).
>
> **Slew rate** (for agile missions):
> $$\dot{\theta}_{\text{max}} = \frac{H_{\text{RW,max}}}{I_{\text{axis}}}$$

> **Worked Example -- Reaction Wheel for 3U CubeSat**
>
> **Given:** $T_{\text{disturbance}} = 1.5 \times 10^{-6}$ N m, desaturation interval = 1 orbit (5670 s).
>
> **Momentum storage:**
> $H_{\text{required}} = 1.5 \times 10^{-6} \times \frac{5670}{2} = 4.25 \times 10^{-3}$ N m s $= 4.25$ mN m s
>
> **Typical CubeSat reaction wheels:**
>
> | Product | Torque (mN m) | Momentum (mN m s) | Mass (g) | Manufacturer |
> |---------|--------------|-------------------|----------|-------------|
> | RW-0.01 | 0.23 | 1.0 | 30 | Hyperion |
> | RW210 | 1.0 | 10 | 55 | Blue Canyon |
> | RW400 | 4.0 | 40 | 120 | Blue Canyon |
> | RW3-1.0 | 1.0 | 15 | 50 | CubeSpace |
>
> The RW210 (10 mN m s) exceeds the 4.25 mN m s requirement with 135% margin. **Selected.**

### Magnetorquer Sizing

Magnetorquers (MTQs) provide torque by interacting with Earth's magnetic field. They are essential for momentum dumping from reaction wheels.

> **Key Equations -- Magnetorquer Torque**
>
> $$T_{\text{MTQ}} = m_{\text{dipole}} \times B \times \sin(\alpha)$$
>
> where $m_{\text{dipole}}$ = magnetic dipole moment (A m$^2$), $B$ = local field (T), $\alpha$ = angle between dipole and field.
>
> **Desaturation time** (to dump one wheel from full momentum):
> $$t_{\text{dump}} = \frac{H_{\text{wheel}}}{T_{\text{MTQ,avg}}}$$

For a CubeSat MTQ with $m = 0.2$ A m$^2$ and $B = 3 \times 10^{-5}$ T:
$T_{\text{MTQ}} = 0.2 \times 3 \times 10^{-5} = 6 \times 10^{-6}$ N m

This is 4x the total disturbance torque -- sufficient for desaturation within a fraction of an orbit.

---

## 4. Pointing Error Budget (25 min)

### Teaching Notes

*[Source: ECSS-E-ST-60-10C; SMAD, Ch. 11.1]*

The pointing error budget combines all independent error sources using root-sum-square (RSS) to determine the total pointing uncertainty.

> **Key Equations -- Pointing Error Budget (RSS)**
>
> $$\theta_{\text{total}} = \sqrt{\theta_{\text{sensor}}^2 + \theta_{\text{actuator}}^2 + \theta_{\text{alignment}}^2 + \theta_{\text{thermal}}^2 + \theta_{\text{jitter}}^2 + \theta_{\text{orbit}}^2 + \theta_{\text{timing}}^2}$$
>
> The result must satisfy:
> $$\theta_{\text{total}} \leq \theta_{\text{requirement}}$$

### Error Source Definitions

| Source | Description | Typical Values (Star Tracker) | Typical Values (Sun Sensor) |
|--------|------------|------------------------------|----------------------------|
| **Sensor accuracy** | Intrinsic measurement noise of attitude sensor | 3--10 arcsec (0.001--0.003 deg) | 0.5--2 deg |
| **Actuator resolution** | Minimum controllable torque/step of actuators | 2--5 arcsec (0.001 deg) | N/A (MTQ: 1--5 deg) |
| **Alignment knowledge** | Misalignment between sensor boresight and payload boresight | 30--60 arcsec (0.01--0.02 deg) | 0.5 deg |
| **Thermal distortion** | Structural deformation with temperature | 10--30 arcsec (0.003--0.01 deg) | 0.1 deg |
| **Jitter** | High-frequency vibration from reaction wheels | 5--20 arcsec (0.001--0.006 deg) | N/A |
| **Orbit knowledge** | Uncertainty in satellite position (affects nadir pointing) | 1--5 arcsec (< 0.001 deg) | 0.05 deg |
| **Timing** | Time-stamping error between sensor read and actuator command | 1--3 arcsec (< 0.001 deg) | 0.01 deg |

> **Worked Example -- Pointing Budget for 3U EO CubeSat (Star Tracker + RW)**
>
> | Error Source | Value (deg) | Value$^2$ |
> |-------------|------------|-----------|
> | Star tracker accuracy | 0.003 | $9.0 \times 10^{-6}$ |
> | Reaction wheel resolution | 0.001 | $1.0 \times 10^{-6}$ |
> | Alignment knowledge | 0.020 | $4.0 \times 10^{-4}$ |
> | Thermal distortion | 0.010 | $1.0 \times 10^{-4}$ |
> | RW jitter | 0.005 | $2.5 \times 10^{-5}$ |
> | Orbit knowledge | 0.001 | $1.0 \times 10^{-6}$ |
> | Timing error | 0.001 | $1.0 \times 10^{-6}$ |
> | **RSS Total** | $\sqrt{5.37 \times 10^{-4}}$ = **0.023 deg** | |
>
> **Requirement:** 0.1 deg (3-sigma)
> **Margin:** 0.1 - 0.023 = 0.077 deg (77% margin) -- **comfortable**.
>
> **Key insight:** Alignment knowledge (0.020 deg) dominates the budget. Improving the star tracker accuracy from 0.003 to 0.001 deg would have negligible impact. **Budget-driven design** means investing effort in the dominant term.

---

## 5. Momentum Management and Desaturation (10 min)

### Teaching Notes

Disturbance torques cause angular momentum to accumulate in reaction wheels over time. Without management, wheels saturate and lose control authority.

**Desaturation cycle:**
1. Wheels accumulate momentum from disturbance torques (~$10^{-6}$ N m continuous)
2. At scheduled intervals (typically once per orbit), MTQs are activated
3. MTQs generate torque against Earth's magnetic field, slowing the wheels
4. Process takes 5--15 minutes per desaturation cycle

**Limitation:** MTQs can only generate torque **perpendicular** to the local magnetic field vector. They cannot dump momentum in all three axes simultaneously. This requires a multi-axis dumping strategy timed with the magnetic field rotation along the orbit.

### 3+1 Redundancy

The standard 4-wheel configuration provides full 3-axis control with one spare:
- **3 wheels** in the body X, Y, Z axes provide minimum control
- **4th wheel** on a skew axis provides redundancy and enhanced torque distribution
- If one wheel fails, the remaining three (including the skew wheel) maintain 3-axis control

---

## 6. SpaceCDF Exercise (30 min)

### Instructions

1. **Architecture tab (AOCS):** Select the AOCS architecture appropriate for your pointing requirement
   - Review the derived requirements that appear
   - Check that the selected hardware fits within your power and mass budgets
2. **Pointing Budget** card on the Dashboard:
   - Review the RSS error tree
   - Identify the largest contributor
   - Verify the total is within your pointing requirement
3. **Dashboard AOCS KPI:**
   - Pointing accuracy achieved
   - Margin to requirement
   - AOCS power demand by mode
4. **Equipment Browser (if time permits):**
   - Browse reaction wheels: compare mass, torque, momentum, cost
   - Browse star trackers: compare accuracy, mass, FOV

### Worksheet 3.2 Tasks

1. Select AOCS architecture and justify based on pointing requirement
2. Calculate at least 2 disturbance torques for your orbit and spacecraft
3. Size the reaction wheel (torque and momentum storage)
4. Complete the pointing error budget table (RSS)
5. Verify margin to pointing requirement

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| AD vs AC | Determination = know orientation (sensors); Control = change orientation (actuators) |
| Architecture selection | Driven by pointing requirement: MTQ for > 2 deg; RW+ST for < 0.1 deg |
| Disturbance torques | Gravity gradient, aero, SRP, magnetic dipole; magnetic dominates for CubeSats |
| RW sizing | Torque >= 2x disturbance; momentum storage >= half-orbit accumulation |
| MTQ sizing | Desaturation torque must exceed disturbance accumulation rate |
| Pointing budget | RSS of 5--7 independent sources; alignment knowledge typically dominates |
| Budget-driven design | Improve the dominant error source, not the smallest one |
| Redundancy | 4-wheel (3+1 skew) provides single-fault tolerance for 3-axis control |
| Momentum management | MTQs dump momentum against Earth's B-field; ~once per orbit |
