# Session 3.2: Attitude and Orbit Control System (AOCS)


**Prerequisites:** Sessions 2.1--2.4 and 3.1 (requirements, orbit, power defined)
**SpaceCDF Tabs:** Dashboard (AOCS KPI), Pointing Budget, Architecture (AOCS)

---

## References

- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.1 (ADCS)](https://www.space.com/smad)
- [Sidi, *Spacecraft Dynamics and Control*, 1997, Ch. 4--9](https://www.cambridge.org/core/books/spacecraft-dynamics-and-control/82B47C7B6E2AA53BFAADAF26C2A79F14)
- [Markley & Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*, 2014](https://link.springer.com/book/10.1007/978-1-4939-0802-8)
- [ECSS, *ECSS-E-ST-60-10C: Control Performance*, 2008](https://ecss.nl/standard/ecss-e-st-60-10c-control-performance/)
- [ECSS, *ECSS-E-ST-60-20C: Star Tracker Performance Testing*, 2019](https://ecss.nl/standard/ecss-e-st-60-20c-star-tracker-performance-testing/)
- [Wertz, *Space Mission Analysis and Design*, 3rd ed., 1999, Ch. 11 (ADCS)](https://www.springer.com)
- [Hughes, *Spacecraft Attitude Dynamics*, 1986](https://www.wiley.com)
- [Blue Canyon Technologies, *XACT ADCS Datasheet*, 2023](https://www.bluecanyontech.com)
- [CubeSpace, *ADCS Product Catalogue*, 2023](https://www.cubespace.co.za)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Explain the distinction between attitude determination and attitude control and the physics of each sensor/actuator type
2. Select AOCS hardware architecture based on pointing requirements
3. Compute a pointing error budget using root-sum-square (RSS) combination
4. Calculate disturbance torques from gravity gradient, aerodynamic drag, solar radiation pressure, and residual magnetic dipole
5. Size actuators (reaction wheels, magnetorquers) for the computed disturbance environment with worked equations
6. Explain the physics of momentum storage, saturation, and desaturation
7. Compare CMGs vs reaction wheels and articulate when each is appropriate
8. Verify AOCS design against requirements using SpaceCDF's pointing budget tool

---

## 1. AOCS Fundamentals
*[Source: SMAD, Ch. 11.1; Markley & Crassidis, Ch. 1--3]*

The AOCS performs two distinct functions:

| Function | Purpose | Hardware |
|----------|---------|---------|
| **Attitude Determination** (AD) | Know the spacecraft's orientation relative to a reference frame | Sensors: star tracker, sun sensors, magnetometer, gyroscope, Earth sensor, GPS receiver |
| **Attitude Control** (AC) | Change or maintain the spacecraft's orientation | Actuators: reaction wheels, magnetorquers, thrusters, control moment gyros |

**The attitude state:** A spacecraft's attitude is its orientation in 3D space relative to a reference frame (typically J2000 Earth-centred inertial, or the local-vertical/local-horizontal frame for nadir-pointing missions). The attitude is described by a rotation (e.g., quaternion, direction cosine matrix, or Euler angles) plus angular velocity $\vec{\omega}$. Euler's equation of rotational motion governs the dynamics:

$$\mathbf{I} \dot{\vec{\omega}} + \vec{\omega} \times (\mathbf{I} \vec{\omega}) = \vec{T}_{\text{external}} + \vec{T}_{\text{control}}$$

where $\mathbf{I}$ is the spacecraft inertia tensor, $\vec{T}_{\text{external}}$ is the sum of disturbance torques, and $\vec{T}_{\text{control}}$ is the actuator torque. The $\vec{\omega} \times (\mathbf{I} \vec{\omega})$ term is the gyroscopic coupling -- it means that rotating about one axis can induce motion about other axes if the inertia tensor is not spherically symmetric.

### Attitude Sensors -- How They Work

#### Star Trackers

A star tracker is the most accurate attitude sensor available, providing absolute attitude knowledge to arcsecond-level accuracy.

**How it works:**
1. A CMOS or CCD detector (typically 1024x1024 to 2048x2048 pixels) images a patch of sky through a wide-angle lens (typically 15--25 deg FOV)
2. The onboard processor detects bright point sources (stars) in the image, computing their centroid positions to sub-pixel accuracy using Gaussian fitting
3. The processor matches the observed pattern of star positions against an onboard star catalogue (typically Hipparcos or Tycho-2, containing 3,000--10,000 stars, stored in a k-d tree or hash table for fast lookup)
4. The "lost in space" algorithm identifies the star pattern without any prior attitude knowledge (first acquisition), typically taking 1--5 seconds
5. Once identified, the processor computes a quaternion rotation from the catalogue (inertial) frame to the camera (body) frame
6. In tracking mode, the processor tracks known stars frame-to-frame, providing updates at 1--10 Hz with 3--10 arcsec accuracy (1-sigma, per axis)

**Key specifications:**

| Parameter | Typical CubeSat Star Tracker | Large S/C Star Tracker |
|-----------|------------------------------|----------------------|
| Accuracy (1-sigma, boresight) | 5--15 arcsec | 0.5--3 arcsec |
| Accuracy (1-sigma, roll) | 30--100 arcsec | 5--20 arcsec |
| FOV | 10--15 deg circular | 15--25 deg circular |
| Update rate | 2--5 Hz | 5--20 Hz |
| Sensitivity | Stars to magnitude 6--7 | Stars to magnitude 8--10 |
| Mass | 50--350 g | 1--5 kg |
| Power | 0.5--2 W | 5--15 W |
| Products | Blue Canyon NST (350g), Sinclair SS-411 (90g), CubeSpace CubeStar (50g) | Sodern Hydra, Leonardo AA-STR |

*[Source: Blue Canyon NST datasheet; CubeSpace CubeStar datasheet; ECSS-E-ST-60-20C]*

**Exclusion zones:** Star trackers cannot operate when bright objects are in or near the FOV:
- **Sun:** Exclusion angle typically 25--45 deg (direct sunlight saturates the detector and can cause permanent damage to some sensor types)
- **Earth (illuminated limb):** Exclusion angle typically 25--35 deg (Earth's brightness overwhelms star signals)
- **Moon:** Exclusion angle typically 10--15 deg
- **Stray light:** Internal reflections from nearby spacecraft structure can create false stars

**Implication for mission design:** A nadir-pointing spacecraft in LEO always has the Earth within ~65 deg of one hemisphere. The star tracker must be mounted on a face that never points toward Earth (typically the zenith or anti-velocity face). If the Sun is near the orbital plane (beta angle near 0), the star tracker may be periodically blinded. Two star trackers mounted on different faces provide redundancy and eliminate single-axis exclusion zone gaps.

**Why star trackers are the most accurate:** Other sensors measure vectors to specific objects (Sun, Earth, magnetic field) -- each provides only 2 of the 3 attitude degrees of freedom (direction but not roll around that vector). A star tracker measures multiple star directions simultaneously, providing a full 3-axis attitude fix from a single measurement. The accuracy is limited by optical diffraction, centroiding noise, and catalogue accuracy -- all of which are extremely well characterised.

#### Sun Sensors

Sun sensors determine the direction to the Sun, providing 2-axis attitude information (the Sun vector in the body frame). They are simple, reliable, radiation-tolerant, and low-power.

**Coarse sun sensors (photodiode-based):**
A coarse sun sensor consists of one or more photodiodes behind a mask or window. The photocurrent is proportional to the cosine of the incidence angle:

$$I = I_0 \cos(\theta)$$

A set of 6 coarse sun sensors (one per face of the spacecraft) determines the Sun direction to 2--5 deg accuracy by comparing the photocurrents from each face. The face with the highest current is sun-facing; the ratio between adjacent faces gives the angle.

**Fine sun sensors (linear array or quadrant detector):**
A fine sun sensor uses a slit mask above a linear photodiode array (similar to a miniature sundial). Sunlight passes through the slit and illuminates a specific position on the array, which is proportional to the incidence angle. Fine sun sensors achieve 0.1--1.0 deg accuracy.

| Type | Accuracy | FOV | Mass | Power | Products |
|------|----------|-----|------|-------|----------|
| Coarse (photodiode) | 2--5 deg | ~hemisphere | 1--5 g | < 1 mW | NewSpace NCSS-SA05, Solar MEMS nanoSSOC-A60 |
| Fine (analog, slit+array) | 0.1--0.5 deg | 60--120 deg | 5--30 g | 10--50 mW | NewSpace NFSS-411, Solar MEMS nanoSSOC-D60 |
| Digital (APS detector + slit) | 0.01--0.05 deg | 60--120 deg | 30--50 g | 50--200 mW | TNO micro digital sun sensor |

*[Source: NewSpace Systems NFSS-411 datasheet; Solar MEMS nanoSSOC datasheets]*

**Why every spacecraft needs sun sensors:** Sun sensors are the only sensor guaranteed to work in any attitude, at any rate, in any environment (LEO, GEO, deep space). They are the primary sensor for safe mode: when the spacecraft tumbles, the OBC reboots, or the star tracker is blinded, the sun sensors can determine the Sun direction and enable the spacecraft to orient its solar arrays for power generation. Without sun sensors, a spacecraft that enters safe mode may not recover power.

#### Magnetometers

A magnetometer measures the local geomagnetic field vector $\vec{B}$ in the body frame. By comparing the measured $\vec{B}$ to a model of Earth's magnetic field (IGRF -- International Geomagnetic Reference Field) at the known orbit position, the spacecraft attitude can be determined.

**How it works:**
- **Fluxgate magnetometer:** A ferromagnetic core is periodically driven into saturation by an excitation coil. The presence of an external magnetic field creates an asymmetry in the saturation waveform, which is detected by a sense coil. Three orthogonal fluxgate elements provide the 3-axis field vector. Resolution: 1--10 nT. Accuracy: $\pm$200--500 nT (limited by spacecraft residual magnetic dipole contamination).
- **Magnetoresistive (AMR/GMR):** Thin-film magnetic sensors. Smaller and cheaper than fluxgates but noisier and less stable. Common in COTS CubeSat magnetometers.

**Attitude determination from magnetometers:**
- A single magnetometer measurement provides the magnetic field direction in the body frame (2 DOF, analogous to a sun sensor providing the Sun direction)
- Comparing with the IGRF model gives attitude, but accuracy is limited by:
  - IGRF model uncertainty (~100 nT in LEO)
  - Spacecraft residual magnetic dipole contamination (can be 1000+ nT close to electronics)
  - Only 2 DOF per measurement (no roll determination around the field vector)
- Magnetometer-only attitude determination: ~5--10 deg accuracy
- Magnetometer + sun sensor (combined): ~1--3 deg accuracy (the two independent vectors provide a full 3-axis solution via TRIAD or q-method)

**Residual dipole contamination:** Every electronic circuit creates a magnetic field. Current loops, permanent magnets in motors/speakers, magnetised structural components, and battery cells all contribute to the spacecraft's residual magnetic dipole. This contaminates the magnetometer reading. Mitigation: mount the magnetometer on a deployable boom (10--30 cm from the bus), use magnetically clean design practices (twisted pairs, balanced current loops), and perform a residual dipole calibration in orbit by comparing magnetometer readings during eclipse (no solar array current) vs sunlit.

| Parameter | Typical CubeSat Magnetometer |
|-----------|------------------------------|
| Range | $\pm$60,000 nT (sufficient for LEO: B ~20,000--50,000 nT) |
| Resolution | 10--100 nT |
| Accuracy (after calibration) | 200--1000 nT |
| Mass | 5--30 g |
| Power | 10--50 mW |
| Products | NewSpace NMAG, PNI RM3100, Honeywell HMC5883L |

#### Gyroscopes (Rate Sensors)

Gyroscopes measure angular velocity $\vec{\omega}$ rather than absolute attitude. They provide high-bandwidth rate information for control loops and bridge the gap between star tracker updates.

**Types used on CubeSats:**
- **MEMS gyroscope:** Vibrating structure (tuning fork or ring) whose Coriolis force is proportional to rotation rate. Small, cheap (< 50 EUR per axis), low power. Bias drift: 1--10 deg/hr. Products: InvenSense MPU-6050, Analog Devices ADIS16265.
- **MEMS IMU (6-axis):** Combined 3-axis accelerometer + 3-axis gyroscope. Mass: 5--15 g. Very common in CubeSats. Products: Sensonor STIM300 (high-end), InvenSense ICM-20948 (COTS).
- **Fibre optic gyroscope (FOG):** Much better stability (bias drift 0.01--1 deg/hr) but larger, heavier (200+ g), and more expensive. Used on high-end CubeSats and small satellites.

**Why gyroscopes drift:** MEMS gyroscopes have a non-zero bias (a constant offset in the measured rate even when stationary) that changes with temperature and time. Integrating angular rate to get attitude ($\theta = \int \omega \, dt$) accumulates this bias error linearly. A 1 deg/hr bias drift means the attitude estimate drifts 1 deg per hour. Star trackers provide absolute attitude corrections that reset this drift -- the combination of star tracker (low rate, absolute) + gyroscope (high rate, relative) via a Kalman filter is the standard approach for high-performance attitude determination.

#### GPS Receivers for Orbit Determination

GPS receivers determine the spacecraft's **position and velocity** (orbit determination), not attitude (though multi-antenna GPS can provide coarse attitude).

**How it works in LEO:**
- GPS satellites orbit at ~20,200 km altitude; LEO spacecraft orbit below them at 300--800 km
- GPS signals travel downward through the ionosphere to the LEO receiver
- The receiver must use a specialised correlator that handles Doppler shifts up to $\pm$40 kHz (LEO relative velocity ~7.5 km/s vs GPS satellite velocity ~3.9 km/s)
- Typical accuracy: 5--20 m position, 0.1--0.5 m/s velocity (single frequency, C/A code)
- Dual-frequency GPS with carrier phase: sub-meter position accuracy

**Why GPS matters for AOCS:** Accurate orbit knowledge is needed for:
- Nadir pointing (must know where "down" is, which requires knowing position)
- Ground target tracking (must know position to compute pointing angles)
- IGRF evaluation (magnetometer attitude determination needs position input)
- Orbit manoeuvre planning

| Parameter | Typical CubeSat GPS Receiver |
|-----------|------------------------------|
| Position accuracy | 5--20 m (C/A code) |
| Velocity accuracy | 0.1--0.5 m/s |
| Time accuracy | 100 ns |
| Altitude limit | Typically 600 km (must verify ITAR/COCOM limits removed) |
| Mass | 15--30 g |
| Power | 0.5--1.0 W |
| Products | SkyFox Labs piNAV-NG, NovAtel OEM719, Hemisphere V200 |

*[Source: SkyFox Labs piNAV datasheet; NovAtel OEM7 specifications]*

### AOCS Architecture Selection by Pointing Requirement

| Pointing Requirement | Architecture | Sensors | Actuators | Mass | Power | Cost |
|---------------------|-------------|---------|-----------|------|-------|------|
| > 5 deg | Passive magnetic | None (or 1 magnetometer) | Permanent magnet + hysteresis rods | ~0.05 kg | 0 W | ~2 kEUR |
| 2--5 deg | B-dot detumble + magnetic pointing | 3-axis magnetometer + coarse sun sensors | 3-axis magnetorquers | ~0.10 kg | 0.2 W | ~8 kEUR |
| 0.1--2 deg | Active 3-axis (RW + sensors) | Fine sun sensors + magnetometer + (optional gyro) | 3--4 RW + 3 MTQ for desaturation | ~0.50 kg | 2--4 W | ~35 kEUR |
| < 0.1 deg | Fine pointing (RW + star tracker) | Star tracker + fine sun sensors + magnetometer + gyro | 4 RW + 3 MTQ | ~0.80 kg | 3--5 W | ~55 kEUR |
| < 0.01 deg | Very fine pointing | Dual star trackers + MEMS gyro + fine sun sensors + magnetometer | 4 RW + 3 MTQ | ~1.20 kg | 4--6 W | ~80 kEUR |

**Real mission examples:**

| Mission | Form Factor | Pointing Req | Architecture | AOCS Mass | Key Sensor |
|---------|------------|-------------|-------------|-----------|------------|
| **Astrocast** (3U, IoT) | 3U | ~5 deg | MTQ + sun sensors + magnetometer | 0.1 kg | Sun sensors |
| **Planet SuperDove** (3U+, EO) | 3U+ | ~0.1 deg | 4 RW + ST + 3 MTQ + 6 sun sensors | 0.8 kg | Blue Canyon NST star tracker |
| **CAPSTONE** (12U, cislunar nav) | 12U | ~0.05 deg | 4 RW + ST + sun sensors + IMU | ~1.0 kg | Star tracker + IMU |
| **ASTERIA** (6U, exoplanet) | 6U | ~0.003 deg (10 arcsec) | 4 RW + ST + fine guidance sensor | ~1.2 kg | Custom fine guidance camera |

*[Source: Pong et al., "ASTERIA: Achieving 10-arcsecond Pointing on a 6U CubeSat," SSC 2018]*

---

## 2. Disturbance Torques
In LEO, four external torques disturb the spacecraft attitude. The AOCS must counteract them continuously. Understanding the source and magnitude of each disturbance is essential for sizing actuators.

*[Source: SMAD, Ch. 11.1; Sidi, Ch. 5; Wertz 1999, Ch. 11]*

### Gravity Gradient Torque

**Physics:** A spacecraft in orbit experiences a non-uniform gravitational field -- the side closer to Earth is pulled more strongly than the far side. For an elongated body, this differential pull creates a torque that tends to align the long axis with the local vertical (nadir direction). This is the principle behind gravity gradient stabilisation.

> **Key Equations -- Gravity Gradient Torque**
>
> $$T_{gg} = \frac{3\mu}{2a^3} |I_z - I_x| \sin(2\theta)$$
>
> where:
> - $\mu = 3.986 \times 10^{14}$ m$^3$/s$^2$ (Earth's gravitational parameter)
> - $a = R_E + h$ (semi-major axis in metres)
> - $I_z$, $I_x$ are principal moments of inertia about the maximum and minimum axes (kg m$^2$)
> - $\theta$ = angle between the long axis and the local vertical
> - Worst case occurs at $\theta = 45$ deg, where $\sin(2\theta) = 1$
>
> For a body with $I_z \approx I_x$ (a cube), $T_{gg} \approx 0$ -- this is why 1U CubeSats experience minimal gravity gradient torque.

### Aerodynamic Torque

**Physics:** At LEO altitudes (200--600 km), residual atmospheric molecules collide with the spacecraft surface. The force acts through the centre of pressure (cp), which generally does not coincide with the centre of mass (cm). The offset creates a torque.

> **Key Equations -- Aerodynamic Torque**
>
> $$T_{\text{aero}} = \frac{1}{2} \rho v^2 C_D A_{\text{ref}} \, d_{cp-cm}$$
>
> where:
> - $\rho$ = atmospheric density (kg/m$^3$) -- varies by orders of magnitude with altitude, solar activity (F10.7), and local time:
>   - 300 km: $\rho \approx 2 \times 10^{-11}$ (solar min) to $3 \times 10^{-10}$ (solar max)
>   - 400 km: $\rho \approx 4 \times 10^{-12}$ to $1 \times 10^{-11}$
>   - 500 km: $\rho \approx 6 \times 10^{-13}$ to $5 \times 10^{-12}$
>   - 600 km: $\rho \approx 1 \times 10^{-13}$ to $8 \times 10^{-13}$
> - $v$ = orbital velocity (~7.6 km/s at 500 km)
> - $C_D \approx 2.0$--$2.3$ (molecular flow drag coefficient; 2.2 is standard for flat plates in free molecular flow)
> - $A_{\text{ref}}$ = cross-sectional area perpendicular to velocity (m$^2$)
> - $d_{cp-cm}$ = offset between centre of pressure and centre of mass (m); typically 0.5--5 cm for CubeSats depending on deployable configuration

### Solar Radiation Pressure Torque

**Physics:** Sunlight carries momentum. When photons strike a surface, they transfer momentum ($p = E/c$ for absorption, $p = 2E/c$ for specular reflection). The resulting force acts through the centre of solar pressure, which may not coincide with the cm.

> **Key Equations -- SRP Torque**
>
> $$T_{\text{SRP}} = \frac{S}{c} A_s (1 + q) \, d_{sp-cm}$$
>
> where:
> - $S = 1361$ W/m$^2$ (solar constant at 1 AU)
> - $c = 3 \times 10^8$ m/s (speed of light)
> - $S/c = 4.54 \times 10^{-6}$ N/m$^2$ (solar radiation pressure at 1 AU)
> - $A_s$ = illuminated area (m$^2$)
> - $q$ = surface reflectance (0 for perfect absorber, 1 for perfect specular reflector)
> - $d_{sp-cm}$ = offset between solar pressure centre and centre of mass (m)
>
> **Note:** SRP torque is tiny in LEO compared to aero and magnetic torques. It becomes the dominant disturbance in GEO and deep space (where there is no atmosphere and the magnetic field is weak).

### Residual Magnetic Dipole Torque

**Physics:** A spacecraft with a net magnetic dipole moment $\vec{M}$ (from current loops in wiring, permanent magnets in reaction wheel motors, magnetised ferromagnetic components) interacts with Earth's magnetic field $\vec{B}$ to produce a torque:

> **Key Equations -- Magnetic Dipole Torque**
>
> $$\vec{T}_{\text{mag}} = \vec{M} \times \vec{B}$$
>
> Magnitude: $T_{\text{mag}} = M \cdot B \cdot \sin(\alpha)$
>
> where:
> - $M$ = spacecraft residual magnetic dipole moment (A m$^2$)
> - $B$ = local geomagnetic field strength (T):
>   - LEO (400--600 km): $B \approx 2$--$5 \times 10^{-5}$ T (varies with latitude; strongest near poles, weakest near equator)
>   - GEO (35,786 km): $B \approx 1 \times 10^{-7}$ T
> - $\alpha$ = angle between $\vec{M}$ and $\vec{B}$
>
> **Typical CubeSat residual dipole moments:**
>
> | Source | Dipole Moment (A m$^2$) | Notes |
> |--------|-------------------------|-------|
> | Reaction wheel motor | 0.005--0.02 per wheel | Permanent magnets in brushless motor |
> | Solar array wiring | 0.001--0.01 | Current loops from SA to EPS |
> | Battery cells | 0.001--0.005 | Nickel in cell casing |
> | Unshielded cables | 0.005--0.05 | Depends on routing and length |
> | **Total (typical 3U)** | **0.01--0.10** | Varies significantly with design |
>
> **Why magnetic torque dominates for CubeSats:** COTS electronics are not designed for magnetic cleanliness. Short wiring runs create small but unbalanced current loops. Reaction wheel motors contain permanent magnets. The result is a residual dipole of 0.01--0.1 A m$^2$, which in a 30 uT field produces $3 \times 10^{-7}$ to $3 \times 10^{-6}$ N m -- often larger than gravity gradient or SRP torques.

> **Worked Example -- Disturbance Torques for 3U CubeSat at 500 km (SuperDove-class)**
>
> **Spacecraft properties:** 3U (100 x 100 x 340 mm), mass = 5 kg, $I_z = 0.035$ kg m$^2$ (long axis), $I_x = 0.007$ kg m$^2$ (short axis), $A_{\text{ref}} = 0.034$ m$^2$ (3U face), $d_{cp-cm} = 0.02$ m (deployable panels offset cm from geometric centre).
>
> **Gravity gradient** (worst case, $\theta = 45$ deg):
> $T_{gg} = \frac{3 \times 3.986 \times 10^{14}}{2 \times (6871 \times 10^{3})^3} \times |0.035 - 0.007| \times 1$
> $= \frac{1.196 \times 10^{15}}{6.494 \times 10^{20}} \times 0.028 = 1.84 \times 10^{-6} \times 0.028 = 5.2 \times 10^{-8}$ N m
>
> **Aerodynamic** (at 500 km, solar minimum, $\rho \approx 6 \times 10^{-13}$ kg/m$^3$):
> $F_{\text{aero}} = 0.5 \times 6 \times 10^{-13} \times 7617^2 \times 2.2 \times 0.034 = 1.30 \times 10^{-6}$ N
>
> $T_{\text{aero}} = F_{\text{aero}} \times d_{cp-cm} = 1.30 \times 10^{-6} \times 0.02 = 2.6 \times 10^{-8}$ N m
>
> Note: at solar maximum ($\rho \approx 5 \times 10^{-12}$), this increases by ~8x to $2.1 \times 10^{-7}$ N m.
>
> **Solar radiation pressure:**
> $F_{\text{SRP}} = \frac{1361}{3 \times 10^8} \times 0.034 \times 1.5 = 2.31 \times 10^{-7}$ N
>
> $T_{\text{SRP}} = F_{\text{SRP}} \times d_{sp-cm} = 2.31 \times 10^{-7} \times 0.02 = 4.6 \times 10^{-9}$ N m
>
> **Residual magnetic dipole** ($M = 0.05$ A m$^2$, $B = 3 \times 10^{-5}$ T):
> $T_{\text{mag}} = 0.05 \times 3 \times 10^{-5} = 1.5 \times 10^{-6}$ N m
>
> **Summary:**
>
> | Source | Torque (N m) | Rank | Notes |
> |--------|-------------|------|-------|
> | Gravity gradient | $5.2 \times 10^{-8}$ | 3rd | Small because 3U is not very elongated |
> | Aerodynamic (solar min) | $2.6 \times 10^{-8}$ | 4th | Increases 8x at solar max |
> | Solar radiation pressure | $4.6 \times 10^{-9}$ | 5th | Negligible at LEO distances |
> | Residual magnetic dipole | $1.5 \times 10^{-6}$ | **1st** | **Dominates by >10x** |
> | **Total (worst-case sum)** | $\approx 1.6 \times 10^{-6}$ | | Conservative estimate |
> | **Total (RSS)** | $\approx 1.5 \times 10^{-6}$ | | More realistic (uncorrelated sources) |
>
> **Key finding:** The residual magnetic dipole dominates for CubeSats due to COTS electronics and short wiring runs. **Magnetic cleanliness matters.** Reducing the residual dipole from 0.05 to 0.01 A m$^2$ (achievable with careful wire routing, twisted pairs, and degaussing) would reduce the total disturbance by 5x.

---

## 3. Attitude Actuators -- Physics and Sizing
### Reaction Wheels -- Physics of Angular Momentum Storage

**How reaction wheels work:**

A reaction wheel is a flywheel (typically a brass or steel ring, 20--200 g for CubeSats) spun by a brushless DC motor. By Newton's third law, changing the wheel's angular momentum produces an equal and opposite torque on the spacecraft:

$$\vec{H}_{\text{total}} = \vec{H}_{\text{spacecraft}} + \vec{H}_{\text{wheels}} = \text{constant}$$

If the wheel speeds up ($\Delta H_{\text{wheel}} > 0$), the spacecraft receives an equal and opposite angular momentum change ($\Delta H_{\text{SC}} = -\Delta H_{\text{wheel}}$), causing it to rotate. The control torque is:

$$T_{\text{control}} = \frac{dH_{\text{wheel}}}{dt} = I_{\text{wheel}} \cdot \dot{\omega}_{\text{wheel}}$$

where $I_{\text{wheel}}$ is the wheel's moment of inertia and $\dot{\omega}_{\text{wheel}}$ is the wheel's angular acceleration.

**Momentum storage:** The maximum angular momentum a wheel can store is:

$$H_{\text{max}} = I_{\text{wheel}} \times \omega_{\text{max}}$$

For a Blue Canyon RW210: $I_{\text{wheel}} \approx 1.5 \times 10^{-5}$ kg m$^2$, $\omega_{\text{max}} \approx 6000$ RPM $= 628$ rad/s, giving $H_{\text{max}} = 0.0094$ N m s $\approx 10$ mN m s.

**Saturation:** As disturbance torques act on the spacecraft, the reaction wheels absorb angular momentum. Over time, the wheel speed increases until it reaches $\omega_{\text{max}}$ (saturation). At saturation, the wheel can no longer absorb momentum in that direction, and control authority is lost. The time to saturation from zero speed is:

$$t_{\text{sat}} = \frac{H_{\text{max}}}{T_{\text{disturbance}}} = \frac{10 \times 10^{-3}}{1.5 \times 10^{-6}} = 6667 \text{ s} \approx 111 \text{ minutes}$$

This is approximately 1.2 orbits -- so the wheels would saturate after about one orbit without desaturation. This is why magnetorquers are essential companions to reaction wheels.

**The zero-crossing problem:** When a reaction wheel passes through zero speed (reversing direction), the static friction in the bearings creates a "dead zone" where the wheel cannot produce smooth, continuous torque. This causes a brief loss of control authority and increased jitter. Mitigations:
- **Bias momentum:** Operate all wheels with a positive bias speed (e.g., 500 RPM), so they never cross zero during normal operations
- **4-wheel pyramid configuration:** The skewed geometry means individual wheels reverse less frequently
- **Lubrication:** Space-rated bearings use solid or vapour-deposited lubricants (MoS$_2$, Braycote) that minimise static friction

**Jitter:** Reaction wheel imbalance (mass asymmetry in the flywheel) creates vibrations at the spin frequency and its harmonics. For imaging missions, this jitter degrades image quality. Jitter amplitude depends on wheel speed, imbalance mass, and the spacecraft's structural transfer function. Typical CubeSat reaction wheel jitter: 5--20 arcsec at the payload, depending on isolation.

### Reaction Wheel Configurations

| Configuration | Description | Pros | Cons | Use |
|--------------|------------|------|------|-----|
| **3 orthogonal** | One wheel per body axis (X, Y, Z) | Minimum mass, simple control | No redundancy; single wheel failure = loss of 1-axis control | Low-cost missions with short lifetime |
| **3 + 1 skew** | 3 orthogonal + 1 on a skew axis (e.g., [1,1,1] direction) | Single-fault tolerant; the skew wheel + remaining 2 provide 3-axis control | Slightly more complex control law distribution | **Standard for CubeSats** |
| **4-wheel pyramid** | 4 wheels tilted ~20--30 deg from body axes, symmetrically arranged | Optimal torque/momentum distribution; single-fault tolerant; reduced zero-crossings | More complex mounting, heavier | High-performance missions, agile S/C |

The **distribution matrix** maps wheel torques to body-frame torques:

$$\vec{T}_{\text{body}} = \mathbf{D} \cdot \vec{T}_{\text{wheels}}$$

For a 4-wheel pyramid with cant angle $\beta$:

$$\mathbf{D} = \begin{bmatrix} \cos\beta & 0 & -\cos\beta & 0 \\ 0 & \cos\beta & 0 & -\cos\beta \\ \sin\beta & \sin\beta & \sin\beta & \sin\beta \end{bmatrix}$$

> **Key Equations -- Reaction Wheel Sizing**
>
> **Torque requirement** (to counteract disturbances + provide slewing capability):
> $$T_{\text{RW,min}} \geq k \times T_{\text{disturbance,total}}$$
> where $k \geq 2$ is the control margin factor (typically 2--5 to provide adequate control bandwidth and slewing performance).
>
> **Momentum storage requirement** (accumulation between desaturation cycles):
> $$H_{\text{required}} = T_{\text{disturbance}} \times \frac{t_{\text{desat}}}{2}$$
> where $t_{\text{desat}}$ is the time between magnetorquer desaturation events (typically one half-orbit to one orbit). The factor of 1/2 accounts for the average (sinusoidal disturbance torques average to half their peak over a quarter orbit).
>
> **Slew rate** (for agile/imaging missions):
> $$\dot{\theta}_{\text{max}} = \frac{H_{\text{RW,max}}}{I_{\text{axis}}}$$
>
> For a 3U CubeSat with RW210 ($H = 10$ mN m s) and $I_{\text{axis}} = 0.035$ kg m$^2$:
> $\dot{\theta}_{\text{max}} = 0.010 / 0.035 = 0.286$ rad/s $= 16.4$ deg/s -- more than adequate for target-to-target slewing.
>
> **Slew time for a given angle** (acceleration-limited, trapezoidal profile):
> $$t_{\text{slew}} = 2\sqrt{\frac{\theta_{\text{slew}} \cdot I_{\text{axis}}}{T_{\text{RW}}}}$$
>
> For a 90 deg (1.57 rad) slew with RW210 ($T = 1.0$ mN m) and $I = 0.035$:
> $t_{\text{slew}} = 2\sqrt{\frac{1.57 \times 0.035}{0.001}} = 2\sqrt{54.95} = 14.8$ s

> **Worked Example -- Reaction Wheel Sizing for 3U CubeSat (SuperDove-class)**
>
> **Given:** $T_{\text{disturbance}} = 1.5 \times 10^{-6}$ N m (from Section 2), desaturation interval = 1 orbit (5670 s), pointing requirement = 0.1 deg, slew requirement = 90 deg in < 60 s.
>
> **Torque requirement:**
> $T_{\text{RW,min}} = 3 \times 1.5 \times 10^{-6} = 4.5 \times 10^{-6}$ N m $= 0.0045$ mN m
>
> This is a very low torque requirement. The minimum available CubeSat wheel (RW-0.01 at 0.23 mN m) exceeds this by 50x. The sizing driver is actually the slew rate and momentum storage, not the disturbance rejection torque.
>
> **Momentum storage:**
> $H_{\text{required}} = 1.5 \times 10^{-6} \times \frac{5670}{2} = 4.25 \times 10^{-3}$ N m s $= 4.25$ mN m s
>
> **Slew time check with candidate wheels:**
>
> | Product | Torque (mN m) | Momentum (mN m s) | Mass (g) | 90 deg Slew (s) | Momentum Margin | Manufacturer |
> |---------|--------------|-------------------|----------|----------------|-----------------|-------------|
> | RW-0.01 | 0.23 | 1.0 | 30 | 69 s | -3.25 mN m s (FAIL) | Hyperion |
> | RW210 | 1.0 | 10 | 55 | 14.8 s | +5.75 mN m s (135%) | Blue Canyon |
> | RW3-1.0 | 1.0 | 15 | 50 | 14.8 s | +10.75 mN m s (253%) | CubeSpace |
> | RW400 | 4.0 | 40 | 120 | 7.4 s | +35.75 mN m s (841%) | Blue Canyon |
>
> The RW-0.01 fails the momentum storage requirement (would saturate in < 1 orbit). The RW210 (10 mN m s) provides 135% margin and 14.8 s slew time. **Selected: RW210 (or CubeSpace RW3-1.0).**
>
> **Configuration:** 4 wheels (3+1 skew) for single-fault tolerance. Total AOCS actuator mass: 4 x 55 g = 220 g.

### Magnetorquers -- Physics of Magnetic Torque Generation

**How magnetorquers work:**

A magnetorquer (MTQ) is simply a coil of wire (or a ferromagnetic rod wrapped with wire). When current flows through the coil, it creates a magnetic dipole moment:

$$\vec{m} = N \cdot I \cdot A \cdot \hat{n}$$

where $N$ = number of turns, $I$ = current (A), $A$ = coil cross-sectional area (m$^2$), and $\hat{n}$ is the coil normal direction.

This magnetic dipole interacts with Earth's geomagnetic field $\vec{B}$ to produce a torque:

$$\vec{T}_{\text{MTQ}} = \vec{m} \times \vec{B}$$

The torque is **perpendicular** to both the dipole moment and the magnetic field. This has a critical implication: **a magnetorquer cannot produce torque parallel to the local magnetic field vector.** At any instant, only 2 of 3 axes can be torqued. Over a full orbit, as the field direction rotates, all 3 axes become accessible -- but not simultaneously.

**Magnetorquer types for CubeSats:**

| Type | Dipole Moment | Mass | Power | Form Factor | Products |
|------|--------------|------|-------|-------------|----------|
| **Air-core coil** (PCB trace) | 0.01--0.05 A m$^2$ | 1--5 g | 0.1--0.3 W | Flat PCB, integrates into solar panel substrate | ZARM Technik MTC-1, custom |
| **Air-core rod** (wound wire) | 0.05--0.50 A m$^2$ | 10--30 g | 0.2--0.5 W | Cylindrical, 60--100 mm long | CubeSpace CubeMAG, NewSpace NTQS |
| **Ferromagnetic core rod** | 0.2--5.0 A m$^2$ | 20--100 g | 0.3--1.0 W | Cylindrical with mu-metal core, 60--100 mm long | ZARM Technik MTQ-1, ISIS iMTQ |

The ferromagnetic core concentrates the magnetic flux, providing 5--20x more dipole moment per unit current than an air-core coil of the same size. However, ferromagnetic cores can retain residual magnetism after power-off, contributing to the spacecraft's residual magnetic dipole.

**Why magnetorquers cannot point (only detumble and desaturate):**

The torque $\vec{T} = \vec{m} \times \vec{B}$ is always perpendicular to $\vec{B}$. This means:
1. You cannot generate torque about the $\vec{B}$ direction at any given instant
2. The achievable torque direction changes continuously as the spacecraft orbits (because $\vec{B}$ rotates)
3. Pointing control requires torque in any direction at any time -- magnetorquers cannot provide this

Magnetorquers are excellent for:
- **Detumbling:** The B-dot controller ($\vec{m} = -k \dot{\vec{B}}$) brakes spacecraft rotation by opposing the change in the measured B-field. Works regardless of attitude.
- **Desaturation:** Systematically dumping momentum from reaction wheels by applying the correct dipole moment: $\vec{m} = -k (\vec{H}_{\text{wheel}} \times \hat{B})$
- **Coarse pointing** (2--10 deg): Possible over time using model-predictive control that plans the dipole commands over a full orbit, exploiting the field rotation. But accuracy is limited.

> **Key Equations -- Magnetorquer Sizing**
>
> **Desaturation torque:**
> $$T_{\text{MTQ}} = m_{\text{dipole}} \times B \times \sin(\alpha)$$
>
> Average torque over an orbit (accounting for varying $\alpha$): $T_{\text{MTQ,avg}} \approx 0.7 \times m_{\text{dipole}} \times B_{\text{avg}}$
>
> **Desaturation time** (to dump one wheel from full momentum):
> $$t_{\text{dump}} = \frac{H_{\text{wheel}}}{T_{\text{MTQ,avg}}}$$
>
> **Design requirement:** $t_{\text{dump}} < t_{\text{shadow}}$ (must complete desaturation during the portion of the orbit where the field geometry is favourable).

> **Worked Example -- Magnetorquer Sizing for 3U CubeSat**
>
> **Given:** RW210 momentum = 10 mN m s, $B_{\text{avg}} = 3 \times 10^{-5}$ T.
>
> **Option 1: CubeMAG rod** ($m = 0.2$ A m$^2$):
> $T_{\text{MTQ,avg}} = 0.7 \times 0.2 \times 3 \times 10^{-5} = 4.2 \times 10^{-6}$ N m
>
> $t_{\text{dump}} = \frac{10 \times 10^{-3}}{4.2 \times 10^{-6}} = 2381$ s $\approx 40$ min
>
> This is approximately 42% of one orbit period. **Acceptable** -- desaturation can be scheduled once per orbit during the non-imaging portion.
>
> **Disturbance rejection check:** The MTQ average torque ($4.2 \times 10^{-6}$ N m) is 2.8x the total disturbance torque ($1.5 \times 10^{-6}$ N m). The MTQ can dump momentum faster than it accumulates. **Pass.**
>
> **Configuration:** 3 MTQ rods, one per body axis (X, Y, Z). This ensures torque can be generated about any two axes at any given time. Total MTQ mass: 3 x 30 g = 90 g.

### Control Moment Gyroscopes (CMGs) vs Reaction Wheels

**CMGs** are an alternative momentum exchange device used on large, agile spacecraft. A CMG consists of a spinning flywheel mounted on a gimbal. Instead of changing the wheel speed (as in a reaction wheel), the CMG changes the direction of the angular momentum vector by rotating the gimbal. This produces a gyroscopic output torque:

$$T_{\text{CMG}} = H_{\text{wheel}} \times \dot{\delta}$$

where $H_{\text{wheel}}$ is the constant wheel momentum and $\dot{\delta}$ is the gimbal rate.

**The torque amplification effect:** For a CMG wheel spinning at high speed ($H = 1$--$100$ N m s), even a slow gimbal rate ($\dot{\delta} = 1$ rad/s) produces a large output torque ($T = 1$--$100$ N m). This is orders of magnitude more than a reaction wheel of similar mass. CMGs are "torque machines"; reaction wheels are "momentum machines."

| Parameter | Reaction Wheel | CMG (Single Gimbal) |
|-----------|---------------|---------------------|
| Output torque | $T = I_w \dot{\omega}_w$ (low, 0.001--10 N m) | $T = H_w \dot{\delta}$ (high, 0.1--1000+ N m) |
| Control complexity | Simple (speed command) | Complex (gimbal singularity avoidance) |
| Mass efficiency | Lower torque/kg | Higher torque/kg (10--100x) |
| Failure mode | Bearing wear, motor failure | Gimbal lock (singularity), bearing wear |
| Typical use | CubeSats, small satellites, non-agile | Large agile satellites, ISS, Earth observation with rapid retargeting |
| CubeSat status | Standard (many COTS products) | Emerging (Honeybee Robotics microCMG, some research prototypes) |

**When to use CMGs:**
- Spacecraft requiring rapid slewing (> 3 deg/s for large spacecraft)
- Large moments of inertia where reaction wheel torque is insufficient
- Missions requiring frequent retargeting (e.g., video from orbit, rapid revisit EO)

**When to use reaction wheels:**
- CubeSats and small satellites (adequate torque, simpler control, more COTS options)
- Missions with modest agility requirements (< 10 deg/s slew for CubeSats)
- Cost-constrained missions (CMGs are significantly more expensive)

The ISS uses four 4600 kg CMGs, each storing 3500 N m s of momentum, to maintain attitude without propellant. The Pleiades Neo Earth observation satellite uses CMGs for rapid retargeting between imaging strips.

---

## 4. Pointing Error Budget
*[Source: ECSS-E-ST-60-10C; SMAD, Ch. 11.1]*

The pointing error budget combines all independent error sources using root-sum-square (RSS) to determine the total pointing uncertainty. This is a statistical combination assuming errors are uncorrelated and normally distributed.

**ECSS pointing performance taxonomy:**

| Term | Definition | Measured Over |
|------|-----------|---------------|
| **APE** (Absolute Performance Error) | Total error between actual pointing and commanded pointing | Single measurement |
| **RPE** (Relative Performance Error) | Variation in pointing over a short time (jitter/stability) | Measurement window (e.g., integration time) |
| **MPE** (Mean Performance Error) | Systematic bias in pointing | Long-term average |

For most CubeSat missions, APE is the primary requirement. RPE matters for long-exposure imaging (e.g., ASTERIA's 10-arcsec stability over 20-minute exposures).

> **Key Equations -- Pointing Error Budget (RSS)**
>
> $$\theta_{\text{APE}} = \sqrt{\theta_{\text{sensor}}^2 + \theta_{\text{actuator}}^2 + \theta_{\text{alignment}}^2 + \theta_{\text{thermal}}^2 + \theta_{\text{jitter}}^2 + \theta_{\text{orbit}}^2 + \theta_{\text{timing}}^2}$$
>
> The result must satisfy:
> $$\theta_{\text{APE}} \leq \theta_{\text{requirement}}$$

### Error Source Definitions and Physics

| Source | Description | Physics | Typical Values (Star Tracker) | Typical Values (Sun Sensor) |
|--------|------------|---------|------------------------------|----------------------------|
| **Sensor accuracy** | Intrinsic measurement noise of attitude sensor | Photon noise, centroiding error, optical distortion | 3--15 arcsec (0.001--0.004 deg) | 0.5--2 deg |
| **Actuator resolution** | Minimum controllable torque step; control loop dead band | Motor cogging torque, driver quantisation, control bandwidth | 2--5 arcsec (0.001 deg) | N/A (MTQ: 1--5 deg) |
| **Alignment knowledge** | Misalignment between sensor boresight and payload boresight; measured during I&T | Mechanical tolerances, shimming, bonding accuracy, measurement uncertainty | 30--60 arcsec (0.01--0.02 deg) | 0.5 deg |
| **Thermal distortion** | Structural deformation with temperature changes; orbital thermal cycling | CTE mismatch between materials, temperature gradients across structure | 10--30 arcsec (0.003--0.01 deg) | 0.1 deg |
| **Jitter** | High-frequency vibration from reaction wheels, mechanisms | Wheel imbalance forces at spin frequency and harmonics, structural resonances | 5--20 arcsec (0.001--0.006 deg) | N/A |
| **Orbit knowledge** | Uncertainty in satellite position (affects nadir pointing vector computation) | GPS accuracy, propagation error between GPS fixes | 1--5 arcsec (< 0.001 deg) | 0.05 deg |
| **Timing** | Time-stamping error between sensor read and actuator command | Clock synchronisation, interrupt latency, bus communication delay | 1--3 arcsec (< 0.001 deg) | 0.01 deg |

> **Worked Example -- Pointing Budget for 3U EO CubeSat (Star Tracker + RW)**
>
> | Error Source | Value (deg) | Value (arcsec) | Value$^2$ (deg$^2$) | Notes |
> |-------------|------------|----------------|---------------------|-------|
> | Star tracker accuracy | 0.003 | 10.8 | $9.0 \times 10^{-6}$ | Blue Canyon NST, 1-sigma boresight |
> | Reaction wheel resolution | 0.001 | 3.6 | $1.0 \times 10^{-6}$ | Motor cogging + control dead band |
> | Alignment knowledge | 0.020 | 72 | $4.0 \times 10^{-4}$ | **Dominant** -- shimmed to 1 arcmin |
> | Thermal distortion | 0.010 | 36 | $1.0 \times 10^{-4}$ | Al structure, 40 degC orbital range |
> | RW jitter | 0.005 | 18 | $2.5 \times 10^{-5}$ | At 3000 RPM, no isolation mount |
> | Orbit knowledge (GPS) | 0.001 | 3.6 | $1.0 \times 10^{-6}$ | GPS fix every 10 s |
> | Timing error | 0.001 | 3.6 | $1.0 \times 10^{-6}$ | < 1 ms timestamp sync |
> | **RSS Total** | $\sqrt{5.37 \times 10^{-4}}$ = **0.023 deg** | **83 arcsec** | | |
>
> **Requirement:** 0.1 deg (3-sigma) -- this is typical for a 5 m GSD imager at 500 km (where 0.1 deg corresponds to ~870 m pointing error on ground, or ~175 pixels for a 5 m GSD sensor).
>
> **Margin:** 0.1 - 0.023 = 0.077 deg (77% margin) -- **comfortable**.
>
> **Key insight:** Alignment knowledge (0.020 deg = 72 arcsec) dominates the budget at 74% of the RSS. Improving the star tracker accuracy from 10 to 3 arcsec would change the RSS total from 83 to 82.3 arcsec -- negligible improvement. **Budget-driven design** means investing effort in the dominant term: better alignment calibration (e.g., on-orbit calibration using ground targets) would have far more impact than upgrading any sensor.
>
> To achieve < 0.01 deg (36 arcsec) pointing, the alignment must be improved to < 0.005 deg (18 arcsec), which requires precision optical alignment during I&T and/or on-orbit alignment calibration.

---

## 5. Momentum Management and Desaturation
Disturbance torques cause angular momentum to accumulate in reaction wheels over time. Without management, wheels saturate and lose control authority. Understanding this cycle is essential for AOCS design.

**The momentum lifecycle:**

1. **Accumulation:** External disturbance torques (gravity gradient, aero, SRP, magnetic) act on the spacecraft body. The control loop commands the reaction wheels to counteract these torques, absorbing the angular momentum. Wheel speed increases (or decreases) at a rate of $\dot{H} = T_{\text{disturbance}}$.

2. **Monitoring:** The OBC monitors wheel speeds. When any wheel exceeds a threshold (typically 80% of maximum), a desaturation manoeuvre is triggered.

3. **Desaturation:** The OBC activates the magnetorquers to generate a torque that opposes the stored wheel momentum. The algorithm computes the optimal dipole command:

$$\vec{m}_{\text{cmd}} = -k_d (\vec{H}_{\text{wheel}} \times \hat{B})$$

where $k_d$ is the desaturation gain and $\hat{B}$ is the unit magnetic field vector. This produces a torque $\vec{T} = \vec{m} \times \vec{B}$ that is in the direction to reduce $\vec{H}_{\text{wheel}}$.

4. **Completion:** Wheel speeds return to near-zero (or bias speed). The cycle repeats.

**Desaturation constraints:**
- MTQs can only generate torque **perpendicular** to the local magnetic field vector. They cannot dump momentum parallel to $\vec{B}$.
- Near the magnetic equator, $\vec{B}$ is nearly horizontal (north-pointing). MTQs can effectively dump momentum about the pitch and roll axes but not yaw.
- Near the magnetic poles, $\vec{B}$ is nearly vertical. MTQs can dump pitch and yaw but not roll.
- Over a full orbit, the field direction rotates sufficiently to dump all three axes. But at any instant, one axis is poorly controllable.
- A multi-pass desaturation strategy (spreading the dump over a full orbit) is more efficient than a single-point dump.

**Typical desaturation frequency for CubeSats:**
- At 500 km with 1.5 uN m total disturbance and 10 mN m s wheels: one desaturation per orbit (every ~95 minutes)
- Duration: 5--15 minutes per cycle
- Power: 0.5--1.5 W during desaturation (3 MTQ rods active)
- During desaturation, pointing accuracy degrades slightly (the MTQ torques perturb the attitude). Imaging should be inhibited during desaturation.

### Wheel Configurations -- 3+1 Redundancy

The standard 4-wheel configuration provides full 3-axis control with one spare:
- **3 wheels** in the body X, Y, Z axes provide minimum control
- **4th wheel** on a skew axis (typically [1,1,1] normalised, or cant angle 20--30 deg from each axis) provides redundancy and enhanced torque distribution
- If one wheel fails, the remaining three (including the skew wheel) maintain 3-axis control with reduced but adequate authority

**4-wheel torque envelope:** With 4 wheels in a pyramid configuration, the maximum torque in any body direction is:

$$T_{\text{max,body}} = \sqrt{2} \cdot T_{\text{wheel}} \approx 1.41 \times T_{\text{wheel}}$$

for the optimal distribution. This is better than the 3-orthogonal configuration where $T_{\text{max,body}} = T_{\text{wheel}}$ along any axis.

---

### 1U Worked Example: UniSat-1

**Passive Magnetic Attitude Stabilisation**

UniSat-1 does not have an active AOCS. Instead, it uses **passive magnetic stabilisation** -- the simplest and cheapest attitude control method, requiring zero power and minimal mass.

**How it works -- physics:**

1. **Permanent magnet:** A small bar magnet (typically AlNiCo or NdFeB, ~10--20 g, dipole moment $M_p = 0.1$--$1.0$ A m$^2$) is embedded along one body axis (say, the Z-axis). In Earth's magnetic field $\vec{B}$, the magnet experiences a restoring torque:

$$\vec{T}_{\text{restoring}} = \vec{M}_p \times \vec{B}$$

This torque acts to align the magnet axis with the local field direction, analogous to a compass needle aligning with magnetic north. The restoring torque is maximum when the magnet is perpendicular to the field ($\alpha = 90$ deg) and zero when aligned ($\alpha = 0$).

For $M_p = 0.5$ A m$^2$ and $B = 3 \times 10^{-5}$ T: $T_{\text{max}} = 0.5 \times 3 \times 10^{-5} = 1.5 \times 10^{-5}$ N m. This is ~10x larger than any environmental disturbance torque, ensuring stable alignment.

2. **Hysteresis rods:** Two or more strips of magnetically soft material (e.g., Permalloy, HyMu-80, ~5--10 g each, dimensions ~60 x 1 x 1 mm) are mounted perpendicular to the permanent magnet. As the satellite oscillates around the field-aligned equilibrium, the external field component along the hysteresis rod alternates, driving the rod material around its B-H hysteresis loop. The area enclosed by the hysteresis loop represents energy dissipated per cycle as heat in the rod material. This extracts kinetic energy from the satellite's oscillation, damping it over time.

The energy dissipated per oscillation cycle is:

$$E_{\text{dissipated}} = V_{\text{rod}} \times \oint H \, dB$$

where $V_{\text{rod}}$ is the rod volume and $\oint H \, dB$ is the area of the hysteresis loop. For HyMu-80 material, typical energy density is ~100 J/m$^3$ per cycle.

**Damping time constant:** From initial tumble (~10 deg/s after deployment) to settled oscillation (~1--5 deg amplitude), the damping process typically takes hours to days, depending on the hysteresis rod material, volume, and the initial tumble rate.

**Performance:**

| Parameter | Passive Magnetic | Active (RW + ST) |
|-----------|-----------------|------------------|
| Pointing accuracy | ~10--15 deg (to local B-field) | < 0.1 deg (to inertial frame) |
| Settling time | Hours to days after deployment | Minutes after mode transition |
| Residual tumble rate | ~1--5 deg/s (damped from initial ~10 deg/s) | < 0.01 deg/s |
| Power | 0 W | 3--5 W |
| Mass | ~30--50 g | 500--800 g |
| Cost | ~2 kEUR | ~55 kEUR |
| Failure modes | Demagnetisation (radiation, temperature) | Motor failure, bearing wear, software bugs |

**Why this works for UniSat-1:**

The MEMS magnetometer payload does not require accurate pointing. In fact, it benefits from being in a slowly rotating/tumbling state because this provides magnetic field measurements across multiple directions, improving the scientific data quality. The magnetometer can measure the field vector regardless of spacecraft orientation.

**No pointing budget needed:** Since there is no payload pointing requirement, there is no need for a pointing error budget. This eliminates the star tracker, reaction wheels, magnetorquers (as actuators), sun sensors, and gyroscopes -- removing the most expensive and power-hungry subsystem from the design.

> **Disturbance environment for 1U at 400 km:**
>
> | Source | Torque (N m) | Calculation | Notes |
> |--------|-------------|-------------|-------|
> | Gravity gradient | ~$1 \times 10^{-8}$ | $\frac{3\mu}{2a^3} \Delta I$; $\Delta I \approx 0.001$ kg m$^2$ for 1U | Small because nearly cubic shape ($I_z \approx I_x$) |
> | Aerodynamic | ~$3 \times 10^{-8}$ | $\frac{1}{2}\rho v^2 C_D A d$; $\rho(400\text{km}) \approx 5 \times 10^{-12}$ | Higher $\rho$ at 400 km than 500 km |
> | Solar radiation pressure | ~$1 \times 10^{-9}$ | $\frac{S}{c} A (1+q) d$; $A = 0.01$ m$^2$ | Small area |
> | Permanent magnet (restoring) | ~$1 \times 10^{-5}$ | $M_p \times B \times \sin(\alpha)$ | **Dominant** -- this IS the control torque |
>
> The permanent magnet restoring torque (~$10^{-5}$ N m) is three orders of magnitude larger than all disturbances combined. This ensures the satellite remains approximately field-aligned.

**Limitation:** Passive magnetic stabilisation provides alignment to the *local* magnetic field, which rotates as the satellite orbits. The satellite does not point at nadir, the Sun, or any fixed direction. For missions requiring Earth-pointing or Sun-tracking, active AOCS is mandatory. For UniSat-1's magnetometer mission, this is not a limitation -- it is a feature.

---

## 6. SpaceCDF Exercise
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
   - Browse star trackers: compare accuracy, mass, FOV, exclusion zones
   - Note that star tracker exclusion zones constrain mounting face options

### Worksheet 3.2 Tasks

1. Select AOCS architecture and justify based on pointing requirement
2. Calculate all 4 disturbance torques for your orbit and spacecraft configuration
3. Size the reaction wheel (torque, momentum storage, and slew time)
4. Size the magnetorquer for desaturation (verify dump time < 1 orbit)
5. Complete the pointing error budget table (RSS of all 7 sources)
6. Verify margin to pointing requirement and identify the dominant error source

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| AD vs AC | Determination = know orientation (sensors); Control = change orientation (actuators) |
| Star trackers | Pattern-match stars against catalogue; 3--15 arcsec accuracy; exclusion zones (Sun 25--45 deg, Earth 25--35 deg); most accurate sensor |
| Sun sensors | Coarse (photodiode, 2--5 deg) or fine (slit+array, 0.1 deg); essential for safe mode; every S/C needs them |
| Magnetometers | Measure $\vec{B}$ field; compare with IGRF model; 5--10 deg accuracy alone; residual dipole contamination is key error source |
| GPS receivers | Orbit determination (position/velocity), not attitude; 5--20 m accuracy in LEO; needed for nadir pointing computation |
| Gyroscopes | Measure angular rate $\vec{\omega}$; MEMS drift 1--10 deg/hr; combined with star tracker via Kalman filter for high-bandwidth estimation |
| Architecture selection | Driven by pointing requirement: passive magnetic for > 5 deg; MTQ for 2--5 deg; RW+ST for < 0.1 deg |
| Disturbance torques | Gravity gradient, aero, SRP, magnetic dipole; **magnetic dipole dominates for CubeSats** |
| Reaction wheel physics | $H = I_w \omega_w$; $T = dH/dt$; saturation occurs when $\omega \rightarrow \omega_{\text{max}}$; zero-crossing jitter |
| RW sizing | Torque $\geq 2\times$ disturbance; momentum $\geq$ half-orbit accumulation; check slew time |
| Magnetorquer physics | $\vec{T} = \vec{m} \times \vec{B}$; torque always perpendicular to $\vec{B}$; cannot point, only detumble/desaturate |
| MTQ sizing | Desaturation torque must exceed disturbance accumulation rate; dump time < 1 orbit |
| CMGs vs RWs | CMGs: torque amplification ($T = H \dot{\delta}$), for large/agile S/C; RWs: simpler, cheaper, standard for CubeSats |
| Pointing budget | RSS of 7 independent sources; alignment knowledge typically dominates; improve the dominant term |
| Budget-driven design | Investing in the smallest error source has negligible impact on total; focus on the dominant term |
| Redundancy | 4-wheel (3+1 skew) provides single-fault tolerance; distribution matrix maps wheels to body torques |
| Momentum management | MTQs dump momentum against Earth's $\vec{B}$-field; ~once per orbit; 5--15 min; imaging inhibited during dump |
