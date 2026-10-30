# Chapter 10 — Attitude and Orbit Control

> **Recommended background.** SMAD4 Ch. 11.1 (ADCS); Markley & Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*, Ch. 1–3; Sidi, *Spacecraft Dynamics and Control*, Ch. 4–9; ECSS-E-ST-60-10C (control performance). This chapter uses the orbit of Chapter 7 and the mass, power and interface framework of Chapter 8; the reaction-wheel momentum relations are derived in Part V §V.14.

## Learning objectives

By the end of this chapter, you will be able to:

1. Explain the distinction between attitude determination and attitude control and the physics of each sensor and actuator type
2. Select an AOCS hardware architecture based on pointing requirements
3. Compute a pointing error budget using root-sum-square (RSS) combination
4. Calculate disturbance torques from gravity gradient, aerodynamic drag, solar radiation pressure, and residual magnetic dipole
5. Size actuators (reaction wheels, magnetorquers) for the computed disturbance environment with worked equations
6. Explain the physics of momentum storage, saturation, and desaturation
7. Compare control moment gyroscopes with reaction wheels and articulate when each is appropriate
8. Verify an AOCS design against its pointing requirement

---

## 10.1 AOCS fundamentals

*[Source: SMAD, Ch. 11.1; Markley & Crassidis, Ch. 1–3]*

The AOCS performs two distinct functions:

| Function | Purpose | Hardware |
|----------|---------|---------|
| **Attitude determination** (AD) | Know the spacecraft's orientation relative to a reference frame | Sensors: star tracker, sun sensors, magnetometer, gyroscope, Earth sensor, GPS receiver |
| **Attitude control** (AC) | Change or maintain the spacecraft's orientation | Actuators: reaction wheels, magnetorquers, thrusters, control moment gyros |

**The attitude state:** A spacecraft's attitude is its orientation in 3D space relative to a reference frame (typically J2000 Earth-centred inertial, or the local-vertical/local-horizontal frame for nadir-pointing missions). The attitude is described by a rotation (quaternion, direction-cosine matrix, or Euler angles) plus angular velocity $\vec{\omega}$. Euler's equation of rotational motion governs the dynamics:

$$\mathbf{I} \dot{\vec{\omega}} + \vec{\omega} \times (\mathbf{I} \vec{\omega}) = \vec{T}_{\text{external}} + \vec{T}_{\text{control}}$$

where $\mathbf{I}$ is the spacecraft inertia tensor, $\vec{T}_{\text{external}}$ is the sum of disturbance torques, and $\vec{T}_{\text{control}}$ is the actuator torque. The $\vec{\omega} \times (\mathbf{I} \vec{\omega})$ term is the gyroscopic coupling — it means that rotating about one axis can induce motion about other axes if the inertia tensor is not spherically symmetric.

The closed loop is the same for every architecture in this chapter (Figure 10.1): sensors measure, an estimator fuses the measurements into an attitude and rate estimate, a controller computes the torque needed to drive the error to zero, and actuators apply it to the spacecraft — while the disturbance torques of §10.2 push back.

![AOCS control-loop block diagram: reference attitude, controller, actuators, spacecraft dynamics with disturbance torques injected, sensors and Kalman-filter estimator in the feedback path.](../assets/figures/fig_aocs_loop.png)

**Figure 10.1** — The AOCS closed loop. The controller turns the error between the commanded and estimated attitude into a torque demand, the actuators apply it, and Euler's equation governs the response of the spacecraft together with the external disturbance torques injected at the plant. Sensors measure the true attitude with noise and bias, and a Kalman-filter estimator fuses those measurements into the attitude and rate estimate fed back to the summing junction.

### 10.1.1 Attitude sensors — how they work

Vendor products named in this chapter are representative examples, not endorsements; prices are indicative (2026).

#### Star trackers

A star tracker is the most accurate attitude sensor available, providing absolute attitude knowledge to arcsecond-level accuracy.

**How it works:**

1. A CMOS or CCD detector (typically 1024 × 1024 to 2048 × 2048 pixels) images a patch of sky through a wide-angle lens (typically 15–25° FOV)
2. The on-board processor detects bright point sources (stars) in the image, computing their centroid positions to sub-pixel accuracy using Gaussian fitting
3. The processor matches the observed pattern of star positions against an on-board star catalogue (typically Hipparcos or Tycho-2, containing 3 000–10 000 stars, stored in a k-d tree or hash table for fast lookup)
4. The "lost in space" algorithm identifies the star pattern without any prior attitude knowledge (first acquisition), typically taking 1–5 seconds
5. Once identified, the processor computes a quaternion rotation from the catalogue (inertial) frame to the camera (body) frame
6. In tracking mode, the processor tracks known stars frame-to-frame, providing updates at 1–10 Hz with 3–10 arcsec accuracy (1σ, per axis)

**Key specifications:**

| Parameter | Typical CubeSat star tracker | Large S/C star tracker |
|-----------|------------------------------|----------------------|
| Accuracy (1σ, boresight) | 5–15 arcsec | 0.5–3 arcsec |
| Accuracy (1σ, roll) | 30–100 arcsec | 5–20 arcsec |
| FOV | 10–15° circular | 15–25° circular |
| Update rate | 2–5 Hz | 5–20 Hz |
| Sensitivity | Stars to magnitude 6–7 | Stars to magnitude 8–10 |
| Mass | 50–350 g | 1–5 kg |
| Power | 0.5–2 W | 5–15 W |
| Products | Blue Canyon NST (350 g), Sinclair SS-411 (90 g), CubeSpace CubeStar (50 g) | Sodern Hydra, Leonardo AA-STR |

*[Source: vendor star-tracker datasheets; ECSS-E-ST-60-20C]*

**Exclusion zones:** Star trackers cannot operate when bright objects are in or near the FOV:

- **Sun:** Exclusion angle typically 25–45° (direct sunlight saturates the detector and can cause permanent damage to some sensor types)
- **Earth (illuminated limb):** Exclusion angle typically 25–35° (Earth's brightness overwhelms star signals)
- **Moon:** Exclusion angle typically 10–15°
- **Stray light:** Internal reflections from nearby spacecraft structure can create false stars

**Implication for mission design:** A nadir-pointing spacecraft in LEO always has the Earth within ~65° of one hemisphere. The star tracker must be mounted on a face that never points toward Earth (typically the zenith or anti-velocity face). If the Sun is near the orbital plane (β-angle near 0, Chapter 7 §7.1.2), the star tracker may be periodically blinded. Two star trackers mounted on different faces provide redundancy and eliminate single-axis exclusion-zone gaps. These constraints are O-type interfaces in the N² matrix of Chapter 8.

**Why star trackers are the most accurate:** Other sensors measure vectors to specific objects (Sun, Earth, magnetic field) — each provides only 2 of the 3 attitude degrees of freedom (direction but not roll around that vector). A star tracker measures multiple star directions simultaneously, providing a full 3-axis attitude fix from a single measurement. The accuracy is limited by optical diffraction, centroiding noise, and catalogue accuracy — all of which are extremely well characterised.

#### Sun sensors

Sun sensors determine the direction to the Sun, providing 2-axis attitude information (the Sun vector in the body frame). They are simple, reliable, radiation-tolerant, and low-power.

**Coarse sun sensors (photodiode-based):**
A coarse sun sensor consists of one or more photodiodes behind a mask or window. The photocurrent is proportional to the cosine of the incidence angle:

$$I = I_0 \cos\theta$$

A set of 6 coarse sun sensors (one per face of the spacecraft) determines the Sun direction to 2–5° accuracy by comparing the photocurrents from each face. The face with the highest current is Sun-facing; the ratio between adjacent faces gives the angle.

**Fine sun sensors (linear array or quadrant detector):**
A fine sun sensor uses a slit mask above a linear photodiode array (similar to a miniature sundial). Sunlight passes through the slit and illuminates a specific position on the array, which is proportional to the incidence angle. Fine sun sensors achieve 0.1–1.0° accuracy.

| Type | Accuracy | FOV | Mass | Power | Products |
|------|----------|-----|------|-------|----------|
| Coarse (photodiode) | 2–5° | ~hemisphere | 1–5 g | < 1 mW | NewSpace NCSS-SA05, Solar MEMS nanoSSOC-A60 |
| Fine (analogue, slit + array) | 0.1–0.5° | 60–120° | 5–30 g | 10–50 mW | NewSpace NFSS-411, Solar MEMS nanoSSOC-D60 |
| Digital (APS detector + slit) | 0.01–0.05° | 60–120° | 30–50 g | 50–200 mW | TNO micro digital sun sensor |

*[Source: vendor sun-sensor datasheets]*

**Why every spacecraft needs sun sensors:** Sun sensors are the only sensor guaranteed to work in any attitude, at any rate, in any environment (LEO, GEO, deep space). They are the primary sensor for safe mode: when the spacecraft tumbles, the OBC reboots, or the star tracker is blinded, the sun sensors can determine the Sun direction and enable the spacecraft to orient its solar arrays for power generation. Without sun sensors, a spacecraft that enters safe mode may not recover power.

#### Magnetometers

A magnetometer measures the local geomagnetic field vector $\vec{B}$ in the body frame. By comparing the measured $\vec{B}$ to a model of Earth's magnetic field (IGRF — International Geomagnetic Reference Field) at the known orbit position, the spacecraft attitude can be determined.

**How it works:**

- **Fluxgate magnetometer:** A ferromagnetic core is periodically driven into saturation by an excitation coil. The presence of an external magnetic field creates an asymmetry in the saturation waveform, which is detected by a sense coil. Three orthogonal fluxgate elements provide the 3-axis field vector. Resolution: 1–10 nT. Accuracy: ±200–500 nT (limited by spacecraft residual magnetic-dipole contamination).
- **Magnetoresistive (AMR/GMR):** Thin-film magnetic sensors. Smaller and cheaper than fluxgates but noisier and less stable. Common in COTS CubeSat magnetometers.

**Attitude determination from magnetometers:**

- A single magnetometer measurement provides the magnetic-field direction in the body frame (2 DOF, analogous to a sun sensor providing the Sun direction)
- Comparing with the IGRF model gives attitude, but accuracy is limited by IGRF model uncertainty (~100 nT in LEO), spacecraft residual magnetic-dipole contamination (can be 1000+ nT close to electronics), and the fact that only 2 DOF are available per measurement (no roll determination around the field vector)
- Magnetometer-only attitude determination: ~5–10° accuracy
- Magnetometer + sun sensor (combined): ~1–3° accuracy (the two independent vectors provide a full 3-axis solution via TRIAD or the q-method)

**Residual dipole contamination:** Every electronic circuit creates a magnetic field. Current loops, permanent magnets in motors, magnetised structural components, and battery cells all contribute to the spacecraft's residual magnetic dipole. This contaminates the magnetometer reading. Mitigation: mount the magnetometer on a deployable boom (10–30 cm from the bus), use magnetically clean design practices (twisted pairs, balanced current loops), and perform a residual-dipole calibration in orbit by comparing magnetometer readings during eclipse (no solar-array current) with sunlit readings.

| Parameter | Typical CubeSat magnetometer |
|-----------|------------------------------|
| Range | ±60 000 nT (sufficient for LEO: B ~20 000–50 000 nT) |
| Resolution | 10–100 nT |
| Accuracy (after calibration) | 200–1000 nT |
| Mass | 5–30 g |
| Power | 10–50 mW |
| Products | NewSpace NMAG, PNI RM3100, Honeywell HMC5883L |

#### Gyroscopes (rate sensors)

Gyroscopes measure angular velocity $\vec{\omega}$ rather than absolute attitude. They provide high-bandwidth rate information for control loops and bridge the gap between star-tracker updates.

**Types used on CubeSats:**

- **MEMS gyroscope:** Vibrating structure (tuning fork or ring) whose Coriolis force is proportional to rotation rate. Small, cheap (< 50 EUR per axis, indicative), low power. Bias drift: 1–10°/h.
- **MEMS IMU (6-axis):** Combined 3-axis accelerometer + 3-axis gyroscope. Mass 5–15 g. Very common in CubeSats.
- **Fibre-optic gyroscope (FOG):** Much better stability (bias drift 0.01–1°/h) but larger, heavier (200+ g) and more expensive. Used on high-end CubeSats and small satellites.

**Why gyroscopes drift:** MEMS gyroscopes have a non-zero bias (a constant offset in the measured rate even when stationary) that changes with temperature and time. Integrating angular rate to get attitude ($\theta = \int \omega \, dt$) accumulates this bias error linearly. A 1°/h bias drift means the attitude estimate drifts 1° per hour. Star trackers provide absolute attitude corrections that reset this drift — the combination of star tracker (low rate, absolute) and gyroscope (high rate, relative) via a Kalman filter is the standard approach for high-performance attitude determination.

#### GPS receivers for orbit determination

GPS receivers determine the spacecraft's **position and velocity** (orbit determination), not attitude (though multi-antenna GPS can provide coarse attitude).

**How it works in LEO:**

- GPS satellites orbit at ~20 200 km altitude; LEO spacecraft orbit below them at 300–800 km
- GPS signals travel downward through the ionosphere to the LEO receiver
- The receiver must use a specialised correlator that handles Doppler shifts up to ±40 kHz (LEO relative velocity ~7.5 km/s vs GPS satellite velocity ~3.9 km/s)
- Typical accuracy: 5–20 m position, 0.1–0.5 m/s velocity (single frequency, C/A code)
- Dual-frequency GPS with carrier phase: sub-metre position accuracy

**Why GPS matters for AOCS:** Accurate orbit knowledge is needed for nadir pointing (knowing where "down" is requires knowing position), ground-target tracking, IGRF evaluation (magnetometer attitude determination needs position input) and orbit-manoeuvre planning.

| Parameter | Typical CubeSat GPS receiver |
|-----------|------------------------------|
| Position accuracy | 5–20 m (C/A code) |
| Velocity accuracy | 0.1–0.5 m/s |
| Time accuracy | 100 ns |
| Altitude limit | Typically 600 km (verify that COCOM limits are removed) |
| Mass | 15–30 g |
| Power | 0.5–1.0 W |
| Products | SkyFox Labs piNAV-NG, NovAtel OEM719, Hemisphere V200 |

### 10.1.2 AOCS architecture selection by pointing requirement

| Pointing requirement | Architecture | Sensors | Actuators | Mass | Power | Cost (indicative, 2026) |
|---------------------|-------------|---------|-----------|------|-------|------|
| > 5° | Passive magnetic | None (or 1 magnetometer) | Permanent magnet + hysteresis rods | ~0.05 kg | 0 W | ~2 kEUR |
| 2–5° | B-dot detumble + magnetic pointing | 3-axis magnetometer + coarse sun sensors | 3-axis magnetorquers | ~0.10 kg | 0.2 W | ~8 kEUR |
| 0.1–2° | Active 3-axis (RW + sensors) | Fine sun sensors + magnetometer + (optional gyro) | 3–4 RW + 3 MTQ for desaturation | ~0.50 kg | 2–4 W | ~35 kEUR |
| < 0.1° | Fine pointing (RW + star tracker) | Star tracker + fine sun sensors + magnetometer + gyro | 4 RW + 3 MTQ | ~0.80 kg | 3–5 W | ~55 kEUR |
| < 0.01° | Very fine pointing | Dual star trackers + MEMS gyro + fine sun sensors + magnetometer | 4 RW + 3 MTQ | ~1.20 kg | 4–6 W | ~80 kEUR |

**Real mission examples:**

| Mission | Form factor | Pointing req. | Architecture | AOCS mass | Key sensor |
|---------|------------|-------------|-------------|-----------|------------|
| **Astrocast** (3U, IoT) | 3U | ~5° | MTQ + sun sensors + magnetometer | 0.1 kg | Sun sensors |
| **Planet SuperDove** (3U+, EO) | 3U+ | ~0.1° | 4 RW + ST + 3 MTQ + 6 sun sensors | 0.8 kg | Star tracker |
| **CAPSTONE** (12U, cislunar nav) | 12U | ~0.05° | 4 RW + ST + sun sensors + IMU | ~1.0 kg | Star tracker + IMU |
| **ASTERIA** (6U, exoplanet) | 6U | ~0.003° (10 arcsec) | 4 RW + ST + fine guidance sensor | ~1.2 kg | Custom fine-guidance camera |

*[Source: Pong et al., "ASTERIA: Achieving 10-arcsecond Pointing on a 6U CubeSat," SSC 2018]*

---

## 10.2 Disturbance torques

In LEO, four external torques disturb the spacecraft attitude. The AOCS must counteract them continuously. Understanding the source and magnitude of each disturbance is essential for sizing actuators.

*[Source: SMAD, Ch. 11.1; Sidi, Ch. 5; Wertz 1999, Ch. 11]*

### 10.2.1 Gravity-gradient torque

**Physics:** A spacecraft in orbit experiences a non-uniform gravitational field — the side closer to Earth is pulled more strongly than the far side. For an elongated body, this differential pull creates a torque that tends to align the long axis with the local vertical (nadir direction). This is the principle behind gravity-gradient stabilisation.

> **Key equation — gravity-gradient torque**
>
> $$T_{gg} = \frac{3\mu}{2a^3} |I_z - I_x| \sin(2\theta)$$
>
> where $\mu = 3.986 \times 10^{14}$ m³/s², $a = R_E + h$ (semi-major axis in metres), $I_z$, $I_x$ are the principal moments of inertia about the maximum and minimum axes (kg m²), and $\theta$ is the angle between the long axis and the local vertical. Worst case occurs at $\theta = 45°$, where $\sin(2\theta) = 1$.
>
> For a body with $I_z \approx I_x$ (a cube), $T_{gg} \approx 0$ — this is why 1U CubeSats experience minimal gravity-gradient torque.

### 10.2.2 Aerodynamic torque

**Physics:** At LEO altitudes (200–600 km), residual atmospheric molecules collide with the spacecraft surface. The force acts through the centre of pressure (cp), which generally does not coincide with the centre of mass (cm). The offset creates a torque.

> **Key equation — aerodynamic torque**
>
> $$T_{\text{aero}} = \frac{1}{2} \rho v^2 C_D A_{\text{ref}} \, d_{cp-cm}$$
>
> where:
> - $\rho$ = atmospheric density (kg/m³) — varies by orders of magnitude with altitude, solar activity (F10.7) and local time:
>   - 300 km: $\rho \approx 2 \times 10^{-11}$ (solar min) to $3 \times 10^{-10}$ (solar max)
>   - 400 km: $\rho \approx 4 \times 10^{-12}$ to $1 \times 10^{-11}$
>   - 500 km: $\rho \approx 6 \times 10^{-13}$ to $5 \times 10^{-12}$
>   - 600 km: $\rho \approx 1 \times 10^{-13}$ to $8 \times 10^{-13}$
> - $v$ = orbital velocity (7.61 km/s at 500 km, Chapter 7)
> - $C_D \approx 2.0$–$2.3$ (free-molecular-flow drag coefficient; 2.2 is standard for flat plates)
> - $A_{\text{ref}}$ = cross-sectional area perpendicular to velocity (m²)
> - $d_{cp-cm}$ = offset between centre of pressure and centre of mass (m); typically 0.5–5 cm for CubeSats depending on deployable configuration

### 10.2.3 Solar radiation pressure torque

**Physics:** Sunlight carries momentum. When photons strike a surface, they transfer momentum ($p = E/c$ for absorption, $p = 2E/c$ for specular reflection). The resulting force acts through the centre of solar pressure, which may not coincide with the cm.

> **Key equation — SRP torque**
>
> $$T_{\text{SRP}} = \frac{S}{c} A_s (1 + q) \, d_{sp-cm}$$
>
> where $S = 1361$ W/m², $c = 3 \times 10^8$ m/s, $S/c = 4.54 \times 10^{-6}$ N/m² (solar radiation pressure at 1 AU), $A_s$ = illuminated area (m²), $q$ = surface reflectance (0 for a perfect absorber, 1 for a perfect specular reflector), and $d_{sp-cm}$ = offset between the solar-pressure centre and the centre of mass (m).
>
> **Note:** SRP torque is tiny in LEO compared with aerodynamic and magnetic torques. It becomes the dominant disturbance in GEO and deep space (where there is no atmosphere and the magnetic field is weak).

### 10.2.4 Residual magnetic dipole torque

**Physics:** A spacecraft with a net magnetic dipole moment $\vec{M}$ (from current loops in wiring, permanent magnets in reaction-wheel motors, magnetised ferromagnetic components) interacts with Earth's magnetic field $\vec{B}$ to produce a torque:

> **Key equation — magnetic dipole torque**
>
> $$\vec{T}_{\text{mag}} = \vec{M} \times \vec{B}$$
>
> Magnitude: $T_{\text{mag}} = M \cdot B \cdot \sin\alpha$
>
> where $M$ = spacecraft residual magnetic dipole moment (A m²), $B$ = local geomagnetic field strength (T): LEO (400–600 km) $B \approx 2$–$5 \times 10^{-5}$ T (strongest near the poles, weakest near the equator); GEO $B \approx 1 \times 10^{-7}$ T; $\alpha$ = angle between $\vec{M}$ and $\vec{B}$.
>
> **Typical CubeSat residual dipole moments:**
>
> | Source | Dipole moment (A m²) | Notes |
> |--------|-------------------------|-------|
> | Reaction-wheel motor | 0.005–0.02 per wheel | Permanent magnets in brushless motor |
> | Solar-array wiring | 0.001–0.01 | Current loops from SA to EPS |
> | Battery cells | 0.001–0.005 | Nickel in cell casing |
> | Unshielded cables | 0.005–0.05 | Depends on routing and length |
> | **Total (typical 3U)** | **0.01–0.10** | Varies significantly with design |
>
> **Why magnetic torque dominates for CubeSats:** COTS electronics are not designed for magnetic cleanliness. Short wiring runs create small but unbalanced current loops. Reaction-wheel motors contain permanent magnets. The result is a residual dipole of 0.01–0.1 A m², which in a 30 µT field produces $3 \times 10^{-7}$ to $3 \times 10^{-6}$ N m — often larger than gravity-gradient or SRP torques.

> **Worked example — disturbance torques for EOSat-3U at 500 km**
>
> **Spacecraft properties:** 3U (100 × 100 × 340 mm), mass 5 kg, $I_z = 0.035$ kg m² (long axis), $I_x = 0.007$ kg m² (short axis), $A_{\text{ref}} = 0.034$ m² (3U face), $d_{cp-cm} = 0.02$ m (deployable panel offsets the cm from the geometric centre). Orbit: $a = 6878.137$ km, $v = 7613$ m/s (Chapter 7 §7.2).
>
> **Gravity gradient** (worst case, $\theta = 45°$):
> $T_{gg} = \dfrac{3 \times 3.986 \times 10^{14}}{2 \times (6.878 \times 10^{6})^3} \times |0.035 - 0.007| \times 1 = \dfrac{1.196 \times 10^{15}}{6.508 \times 10^{20}} \times 0.028 = 1.84 \times 10^{-6} \times 0.028 = 5.1 \times 10^{-8}$ N m
>
> **Aerodynamic** (at 500 km, solar minimum, $\rho \approx 6 \times 10^{-13}$ kg/m³):
> $F_{\text{aero}} = 0.5 \times 6 \times 10^{-13} \times 7613^2 \times 2.2 \times 0.034 = 1.30 \times 10^{-6}$ N
>
> $T_{\text{aero}} = F_{\text{aero}} \times d_{cp-cm} = 1.30 \times 10^{-6} \times 0.02 = 2.6 \times 10^{-8}$ N m
>
> Note: at solar maximum ($\rho \approx 5 \times 10^{-12}$), this increases by ~8× to $2.2 \times 10^{-7}$ N m.
>
> **Solar radiation pressure:**
> $F_{\text{SRP}} = \dfrac{1361}{3 \times 10^8} \times 0.034 \times 1.5 = 2.31 \times 10^{-7}$ N
>
> $T_{\text{SRP}} = F_{\text{SRP}} \times d_{sp-cm} = 2.31 \times 10^{-7} \times 0.02 = 4.6 \times 10^{-9}$ N m
>
> **Residual magnetic dipole** ($M = 0.05$ A m², $B = 3 \times 10^{-5}$ T):
> $T_{\text{mag}} = 0.05 \times 3 \times 10^{-5} = 1.5 \times 10^{-6}$ N m
>
> **Summary:**
>
> | Source | Torque (N m) | Rank | Notes |
> |--------|-------------|------|-------|
> | Gravity gradient | $5.1 \times 10^{-8}$ | 3rd | Small because a 3U is not very elongated |
> | Aerodynamic (solar min) | $2.6 \times 10^{-8}$ | 4th | Increases 8× at solar max |
> | Solar radiation pressure | $4.6 \times 10^{-9}$ | 5th | Negligible at LEO |
> | Residual magnetic dipole | $1.5 \times 10^{-6}$ | **1st** | **Dominates by > 10×** |
> | **Total (worst-case sum)** | $\approx 1.6 \times 10^{-6}$ | | Conservative estimate |
> | **Total (RSS)** | $\approx 1.5 \times 10^{-6}$ | | More realistic (uncorrelated sources) |
>
> **Key finding:** The residual magnetic dipole dominates for CubeSats because of COTS electronics and short wiring runs. **Magnetic cleanliness matters.** Reducing the residual dipole from 0.05 to 0.01 A m² (achievable with careful wire routing, twisted pairs and degaussing) would reduce the total disturbance by 5×.

---

## 10.3 Attitude actuators — physics and sizing

### 10.3.1 Reaction wheels — physics of angular-momentum storage

A reaction wheel is a flywheel (typically a brass or steel ring, 20–200 g for CubeSats) spun by a brushless DC motor. By Newton's third law, changing the wheel's angular momentum produces an equal and opposite torque on the spacecraft:

$$\vec{H}_{\text{total}} = \vec{H}_{\text{spacecraft}} + \vec{H}_{\text{wheels}} = \text{constant}$$

If the wheel speeds up ($\Delta H_{\text{wheel}} > 0$), the spacecraft receives an equal and opposite angular-momentum change ($\Delta H_{\text{SC}} = -\Delta H_{\text{wheel}}$), causing it to rotate. The control torque is:

$$T_{\text{control}} = \frac{dH_{\text{wheel}}}{dt} = I_{\text{wheel}} \cdot \dot{\omega}_{\text{wheel}}$$

where $I_{\text{wheel}}$ is the wheel's moment of inertia and $\dot{\omega}_{\text{wheel}}$ its angular acceleration.

**Momentum storage:** The maximum angular momentum a wheel can store is:

$$H_{\text{max}} = I_{\text{wheel}} \times \omega_{\text{max}}$$

For a representative 10 mN m s CubeSat wheel: $I_{\text{wheel}} \approx 1.5 \times 10^{-5}$ kg m², $\omega_{\text{max}} \approx 6000$ rpm $= 628$ rad/s, giving $H_{\text{max}} = 0.0094$ N m s $\approx 10$ mN m s.

**Saturation:** As disturbance torques act on the spacecraft, the reaction wheels absorb angular momentum. Over time, the wheel speed increases until it reaches $\omega_{\text{max}}$ (saturation). At saturation, the wheel can no longer absorb momentum in that direction, and control authority is lost. The time to saturation from zero speed is:

$$t_{\text{sat}} = \frac{H_{\text{max}}}{T_{\text{disturbance}}} = \frac{10 \times 10^{-3}}{1.5 \times 10^{-6}} = 6667 \text{ s} \approx 111 \text{ minutes}$$

This is approximately 1.2 orbits — so the wheels would saturate after about one orbit without desaturation. This is why magnetorquers are essential companions to reaction wheels.

**The zero-crossing problem:** When a reaction wheel passes through zero speed (reversing direction), the static friction in the bearings creates a "dead zone" where the wheel cannot produce smooth, continuous torque. This causes a brief loss of control authority and increased jitter. Mitigations:

- **Bias momentum:** Operate all wheels with a positive bias speed (e.g., 500 rpm), so they never cross zero during normal operations
- **4-wheel pyramid configuration:** The skewed geometry means individual wheels reverse less frequently
- **Lubrication:** Space-rated bearings use solid or vapour-deposited lubricants (MoS₂, Braycote) that minimise static friction

**Jitter:** Reaction-wheel imbalance (mass asymmetry in the flywheel) creates vibrations at the spin frequency and its harmonics. For imaging missions, this jitter degrades image quality. Jitter amplitude depends on wheel speed, imbalance mass, and the spacecraft's structural transfer function. Typical CubeSat reaction-wheel jitter: 5–20 arcsec at the payload, depending on isolation.

### 10.3.2 Reaction-wheel configurations

| Configuration | Description | Pros | Cons | Use |
|--------------|------------|------|------|-----|
| **3 orthogonal** | One wheel per body axis (X, Y, Z) | Minimum mass, simple control | No redundancy; single wheel failure = loss of 1-axis control | Low-cost missions with short lifetime |
| **3 + 1 skew** | 3 orthogonal + 1 on a skew axis (e.g., [1,1,1] direction) | Single-fault tolerant; the skew wheel + remaining 2 provide 3-axis control | Slightly more complex control-law distribution | **Standard for CubeSats** |
| **4-wheel pyramid** | 4 wheels tilted ~20–30° from body axes, symmetrically arranged | Optimal torque/momentum distribution; single-fault tolerant; reduced zero-crossings | More complex mounting, heavier | High-performance missions, agile S/C |

Figure 10.2 shows the four-wheel pyramid geometry: each spin axis is raised by the cant angle β above the body X–Y plane, and the four axes are spaced 90° apart in azimuth along ±X and ±Y.

![Four-wheel reaction-wheel pyramid: oblique view of the body frame with four canted spin axes, and a top view showing the 90° azimuth spacing.](../assets/figures/fig_rw_pyramid.png)

**Figure 10.2** — Four-wheel pyramid geometry, drawn for β = 30°. Left: the four wheel spin axes w1–w4, each raised by the cant angle β above the body X–Y plane; right: the view along +Z, showing the 90° azimuth spacing along +X, +Y, −X and −Y. The unit vector of each spin axis in the body frame is the corresponding column of the distribution matrix $\mathbf{D}$ below, so with all four wheels running the torque capability is $2\cos\beta$ times a single wheel about X or Y and $4\sin\beta$ about Z.

The **distribution matrix** maps wheel torques to body-frame torques:

$$\vec{T}_{\text{body}} = \mathbf{D} \cdot \vec{T}_{\text{wheels}}$$

For a 4-wheel pyramid with cant angle $\beta$ (here the wheel cant angle, not the orbit β-angle):

$$\mathbf{D} = \begin{bmatrix} \cos\beta & 0 & -\cos\beta & 0 \\ 0 & \cos\beta & 0 & -\cos\beta \\ \sin\beta & \sin\beta & \sin\beta & \sin\beta \end{bmatrix}$$

> **Key equations — reaction-wheel sizing**
>
> **Torque requirement** (to counteract disturbances and provide slewing capability):
> $$T_{\text{RW,min}} \geq k \times T_{\text{disturbance,total}}$$
> where $k \geq 2$ is the control margin factor (typically 2–5 to provide adequate control bandwidth and slewing performance).
>
> **Momentum-storage requirement** (accumulation between desaturation cycles):
> $$H_{\text{required}} = T_{\text{disturbance}} \times \frac{t_{\text{desat}}}{2}$$
> where $t_{\text{desat}}$ is the time between magnetorquer desaturation events (typically one half-orbit to one orbit). The factor of ½ accounts for the average (sinusoidal disturbance torques average to half their peak over a quarter orbit).
>
> **Slew rate** (for agile/imaging missions):
> $$\dot{\theta}_{\text{max}} = \frac{H_{\text{RW,max}}}{I_{\text{axis}}}$$
>
> For a 3U CubeSat with a 10 mN m s wheel and $I_{\text{axis}} = 0.035$ kg m²:
> $\dot{\theta}_{\text{max}} = 0.010 / 0.035 = 0.286$ rad/s $= 16.4°$/s — more than adequate for target-to-target slewing.
>
> **Slew time for a given angle** (torque-limited, triangular rate profile):
> $$t_{\text{slew}} = 2\sqrt{\frac{\theta_{\text{slew}} \cdot I_{\text{axis}}}{T_{\text{RW}}}}$$
>
> For a 90° (1.57 rad) slew with $T = 1.0$ mN m and $I = 0.035$ kg m²:
> $t_{\text{slew}} = 2\sqrt{\dfrac{1.57 \times 0.035}{0.001}} = 2\sqrt{54.95} = 14.8$ s
>
> This formula assumes the wheel never reaches its momentum limit during the slew; if $T_{\text{RW}} \cdot t_{\text{slew}}/2 > H_{\text{max}}$ the slew becomes momentum-limited and the spacecraft coasts at $\dot{\theta}_{\text{max}}$ for the middle portion, which takes longer.

> **Worked example — reaction-wheel sizing for EOSat-3U**
>
> **Given:** $T_{\text{disturbance}} = 1.5 \times 10^{-6}$ N m (from §10.2), desaturation interval = 1 orbit (5677 s), pointing requirement = 0.1°, slew requirement = 90° in < 60 s.
>
> **Torque requirement:**
> $T_{\text{RW,min}} = 3 \times 1.5 \times 10^{-6} = 4.5 \times 10^{-6}$ N m $= 0.0045$ mN m
>
> This is a very low torque requirement. The smallest available CubeSat wheel (0.23 mN m) exceeds it by 50×. The sizing driver is actually the slew rate and momentum storage, not the disturbance-rejection torque.
>
> **Momentum storage:**
> $H_{\text{required}} = 1.5 \times 10^{-6} \times \dfrac{5677}{2} = 4.26 \times 10^{-3}$ N m s $= 4.26$ mN m s
>
> **Slew-time check with candidate wheels** (representative examples, not endorsements):
>
> | Product class | Torque (mN m) | Momentum (mN m s) | Mass (g) | 90° slew (s) | Momentum margin |
> |---------|--------------|-------------------|----------|----------------|-----------------|
> | Micro wheel (e.g., Hyperion RW-0.01) | 0.23 | 1.0 | 30 | ≈ 59 s (momentum-limited: the 1 mN m s limit is reached after 4.3 s and the slew coasts at 1.6°/s) | −3.26 mN m s (FAIL) |
> | Small wheel (e.g., Blue Canyon RW210) | 1.0 | 10 | 55 | 14.8 s | +5.74 mN m s (135 %) |
> | Small wheel (e.g., CubeSpace RW3-1.0) | 1.0 | 15 | 50 | 14.8 s | +10.74 mN m s (252 %) |
> | Medium wheel (e.g., Blue Canyon RW400) | 4.0 | 40 | 120 | 7.4 s | +35.74 mN m s (839 %) |
>
> The micro wheel fails the momentum-storage requirement (it would saturate in well under one orbit) and the slew requirement is marginal. The 10 mN m s small wheel provides 135 % margin and a 14.8 s slew. **Selected: 10 mN m s class wheel.**
>
> **Configuration:** 4 wheels (3 + 1 skew) for single-fault tolerance. Total wheel mass: 4 × 55 g = 220 g.

### 10.3.3 Magnetorquers — physics of magnetic torque generation

A magnetorquer (MTQ) is simply a coil of wire (or a ferromagnetic rod wrapped with wire). When current flows through the coil, it creates a magnetic dipole moment:

$$\vec{m} = N \cdot I \cdot A \cdot \hat{n}$$

where $N$ = number of turns, $I$ = current (A), $A$ = coil cross-sectional area (m²), and $\hat{n}$ is the coil normal direction.

This magnetic dipole interacts with Earth's geomagnetic field $\vec{B}$ to produce a torque:

$$\vec{T}_{\text{MTQ}} = \vec{m} \times \vec{B}$$

The torque is **perpendicular** to both the dipole moment and the magnetic field. This has a critical implication: **a magnetorquer cannot produce torque parallel to the local magnetic-field vector.** At any instant, only 2 of 3 axes can be torqued. Over a full orbit, as the field direction rotates, all 3 axes become accessible — but not simultaneously.

**Magnetorquer types for CubeSats:**

| Type | Dipole moment | Mass | Power | Form factor | Products |
|------|--------------|------|-------|-------------|----------|
| **Air-core coil** (PCB trace) | 0.01–0.05 A m² | 1–5 g | 0.1–0.3 W | Flat PCB, integrates into solar-panel substrate | ZARM Technik MTC-1, custom |
| **Air-core rod** (wound wire) | 0.05–0.50 A m² | 10–30 g | 0.2–0.5 W | Cylindrical, 60–100 mm long | CubeSpace CubeMAG, NewSpace NTQS |
| **Ferromagnetic-core rod** | 0.2–5.0 A m² | 20–100 g | 0.3–1.0 W | Cylindrical with mu-metal core, 60–100 mm long | ZARM Technik MTQ-1, ISIS iMTQ |

The ferromagnetic core concentrates the magnetic flux, providing 5–20× more dipole moment per unit current than an air-core coil of the same size. However, ferromagnetic cores can retain residual magnetism after power-off, contributing to the spacecraft's residual magnetic dipole.

**Why magnetorquers cannot point (only detumble and desaturate):**

The torque $\vec{T} = \vec{m} \times \vec{B}$ is always perpendicular to $\vec{B}$. This means:

1. You cannot generate torque about the $\vec{B}$ direction at any given instant
2. The achievable torque direction changes continuously as the spacecraft orbits (because $\vec{B}$ rotates)
3. Pointing control requires torque in any direction at any time — magnetorquers cannot provide this

Magnetorquers are excellent for:

- **Detumbling:** The B-dot controller ($\vec{m} = -k \dot{\vec{B}}$) brakes spacecraft rotation by opposing the change in the measured B-field. Works regardless of attitude.
- **Desaturation:** Systematically dumping momentum from reaction wheels by applying the correct dipole moment: $\vec{m} = -k (\vec{H}_{\text{wheel}} \times \hat{B})$
- **Coarse pointing** (2–10°): Possible over time using model-predictive control that plans the dipole commands over a full orbit, exploiting the field rotation. But accuracy is limited.

> **Key equations — magnetorquer sizing**
>
> **Desaturation torque:**
> $$T_{\text{MTQ}} = m_{\text{dipole}} \times B \times \sin\alpha$$
>
> Average torque over an orbit (accounting for varying $\alpha$): $T_{\text{MTQ,avg}} \approx 0.7 \times m_{\text{dipole}} \times B_{\text{avg}}$
>
> **Desaturation time** (to dump one wheel from full momentum):
> $$t_{\text{dump}} = \frac{H_{\text{wheel}}}{T_{\text{MTQ,avg}}}$$
>
> **Design requirement:** $t_{\text{dump}}$ must fit within the portion of the orbit where the field geometry is favourable and no imaging is scheduled — in practice, well under one orbit.

> **Worked example — magnetorquer sizing for EOSat-3U**
>
> **Given:** wheel momentum = 10 mN m s, $B_{\text{avg}} = 3 \times 10^{-5}$ T.
>
> **Option 1: air-core rod** ($m = 0.2$ A m²):
> $T_{\text{MTQ,avg}} = 0.7 \times 0.2 \times 3 \times 10^{-5} = 4.2 \times 10^{-6}$ N m
>
> $t_{\text{dump}} = \dfrac{10 \times 10^{-3}}{4.2 \times 10^{-6}} = 2381$ s $\approx 40$ min
>
> This is approximately 42 % of one orbit period. **Acceptable** — desaturation can be scheduled once per orbit during the non-imaging portion.
>
> **Disturbance-rejection check:** The MTQ average torque ($4.2 \times 10^{-6}$ N m) is 2.8× the total disturbance torque ($1.5 \times 10^{-6}$ N m). The MTQ can dump momentum faster than it accumulates. **Pass.**
>
> **Configuration:** 3 MTQ rods, one per body axis (X, Y, Z). This ensures torque can be generated about any two axes at any given time. Total MTQ mass: 3 × 30 g = 90 g.

### 10.3.4 Control moment gyroscopes vs reaction wheels

**CMGs** are an alternative momentum-exchange device used on large, agile spacecraft. A CMG consists of a spinning flywheel mounted on a gimbal. Instead of changing the wheel speed (as in a reaction wheel), the CMG changes the direction of the angular-momentum vector by rotating the gimbal. This produces a gyroscopic output torque:

$$T_{\text{CMG}} = H_{\text{wheel}} \times \dot{\delta}$$

where $H_{\text{wheel}}$ is the constant wheel momentum and $\dot{\delta}$ is the gimbal rate.

**The torque-amplification effect:** For a CMG wheel spinning at high speed ($H = 1$–$100$ N m s), even a slow gimbal rate ($\dot{\delta} = 1$ rad/s) produces a large output torque ($T = 1$–$100$ N m). This is orders of magnitude more than a reaction wheel of similar mass. CMGs are "torque machines"; reaction wheels are "momentum machines."

| Parameter | Reaction wheel | CMG (single gimbal) |
|-----------|---------------|---------------------|
| Output torque | $T = I_w \dot{\omega}_w$ (low, 0.001–10 N m) | $T = H_w \dot{\delta}$ (high, 0.1–1000+ N m) |
| Control complexity | Simple (speed command) | Complex (gimbal singularity avoidance) |
| Mass efficiency | Lower torque/kg | Higher torque/kg (10–100×) |
| Failure mode | Bearing wear, motor failure | Gimbal lock (singularity), bearing wear |
| Typical use | CubeSats, small satellites, non-agile | Large agile satellites, ISS, Earth observation with rapid retargeting |
| CubeSat status | Standard (many COTS products) | Emerging (micro-CMG products, research prototypes) |

**When to use CMGs:** spacecraft requiring rapid slewing (> 3°/s for large spacecraft); large moments of inertia where reaction-wheel torque is insufficient; missions requiring frequent retargeting (video from orbit, rapid-revisit EO).

**When to use reaction wheels:** CubeSats and small satellites (adequate torque, simpler control, more COTS options); missions with modest agility requirements (< 10°/s slew for CubeSats); cost-constrained missions (CMGs are significantly more expensive).

The ISS uses four 4600 kg CMGs, each storing 3500 N m s of momentum, to maintain attitude without propellant. The Pléiades Neo Earth-observation satellites use CMGs for rapid retargeting between imaging strips.

---

## 10.4 Pointing error budget

*[Source: ECSS-E-ST-60-10C; SMAD, Ch. 11.1]*

The pointing error budget combines all independent error sources using root-sum-square (RSS) to determine the total pointing uncertainty. This is a statistical combination assuming errors are uncorrelated and normally distributed.

**ECSS pointing performance taxonomy:**

| Term | Definition | Measured over |
|------|-----------|---------------|
| **APE** (Absolute Performance Error) | Total error between actual pointing and commanded pointing | Single measurement |
| **RPE** (Relative Performance Error) | Variation in pointing over a short time (jitter/stability) | Measurement window (e.g., integration time) |
| **MPE** (Mean Performance Error) | Systematic bias in pointing | Long-term average |

For most CubeSat missions, APE is the primary requirement. RPE matters for long-exposure imaging (e.g., ASTERIA's 10-arcsec stability over 20-minute exposures).

> **Key equations — pointing error budget (RSS)**
>
> $$\theta_{\text{APE}} = \sqrt{\theta_{\text{sensor}}^2 + \theta_{\text{actuator}}^2 + \theta_{\text{alignment}}^2 + \theta_{\text{thermal}}^2 + \theta_{\text{jitter}}^2 + \theta_{\text{orbit}}^2 + \theta_{\text{timing}}^2}$$
>
> The result must satisfy:
> $$\theta_{\text{APE}} \leq \theta_{\text{requirement}}$$

### 10.4.1 Error source definitions and physics

| Source | Description | Physics | Typical values (star tracker) | Typical values (sun sensor) |
|--------|------------|---------|------------------------------|----------------------------|
| **Sensor accuracy** | Intrinsic measurement noise of attitude sensor | Photon noise, centroiding error, optical distortion | 3–15 arcsec (0.001–0.004°) | 0.5–2° |
| **Actuator resolution** | Minimum controllable torque step; control-loop dead band | Motor cogging torque, driver quantisation, control bandwidth | 2–5 arcsec (0.001°) | N/A (MTQ: 1–5°) |
| **Alignment knowledge** | Misalignment between sensor boresight and payload boresight; measured during I&T | Mechanical tolerances, shimming, bonding accuracy, measurement uncertainty | 30–60 arcsec (0.01–0.02°) | 0.5° |
| **Thermal distortion** | Structural deformation with temperature changes; orbital thermal cycling | CTE mismatch between materials, temperature gradients across structure | 10–30 arcsec (0.003–0.01°) | 0.1° |
| **Jitter** | High-frequency vibration from reaction wheels, mechanisms | Wheel imbalance forces at spin frequency and harmonics, structural resonances | 5–20 arcsec (0.001–0.006°) | N/A |
| **Orbit knowledge** | Uncertainty in satellite position (affects nadir pointing vector computation) | GPS accuracy, propagation error between GPS fixes | 1–5 arcsec (< 0.001°) | 0.05° |
| **Timing** | Time-stamping error between sensor read and actuator command | Clock synchronisation, interrupt latency, bus communication delay | 1–3 arcsec (< 0.001°) | 0.01° |

Figure 10.3 shows a pointing budget drawn as a waterfall: each contributor as a bar, grouped into knowledge, control and alignment terms, with the group RSS values and the allocation line. The worked example below builds the same kind of budget for EOSat-3U.

![Pointing error budget waterfall.](../assets/figures/fig_pointing_tree.png)

**Figure 10.3** — Pointing error budget for a star-tracker/reaction-wheel small satellite, drawn as a waterfall of 1σ contributions grouped into knowledge, control and alignment terms (values in millidegrees). The group RSS values and the total RSS are compared against the allocation; the alignment group dominates, as it does in the worked example below.

> **Worked example — pointing budget for EOSat-3U (star tracker + reaction wheels)**
>
> | Error source | Value (°) | Value (arcsec) | Value² (°²) | Notes |
> |-------------|------------|----------------|---------------|-------|
> | Star-tracker accuracy | 0.003 | 10.8 | $9.0 \times 10^{-6}$ | CubeSat-class star tracker, 1σ boresight |
> | Reaction-wheel resolution | 0.001 | 3.6 | $1.0 \times 10^{-6}$ | Motor cogging + control dead band |
> | Alignment knowledge | 0.020 | 72 | $4.0 \times 10^{-4}$ | **Dominant** — shimmed to 1 arcmin |
> | Thermal distortion | 0.010 | 36 | $1.0 \times 10^{-4}$ | Al structure, 40 °C orbital range |
> | RW jitter | 0.005 | 18 | $2.5 \times 10^{-5}$ | At 3000 rpm, no isolation mount |
> | Orbit knowledge (GPS) | 0.001 | 3.6 | $1.0 \times 10^{-6}$ | GPS fix every 10 s |
> | Timing error | 0.001 | 3.6 | $1.0 \times 10^{-6}$ | < 1 ms timestamp sync |
> | **RSS total** | $\sqrt{5.37 \times 10^{-4}}$ = **0.023°** | **83 arcsec** | | |
>
> **Requirement:** 0.1° (3σ) — typical for a 5 m GSD imager at 500 km (where 0.1° corresponds to ~870 m pointing error on the ground, or ~175 pixels for a 5 m GSD sensor).
>
> **Margin:** 0.1 − 0.023 = 0.077° (77 % margin) — **comfortable**.
>
> **Key insight:** Alignment knowledge (0.020° = 72 arcsec) dominates the budget at 74 % of the RSS variance. Improving the star-tracker accuracy from 10 to 3 arcsec would change the RSS total from 83 to 82.3 arcsec — a negligible improvement. **Budget-driven design** means investing effort in the dominant term: better alignment calibration (e.g., on-orbit calibration using ground targets) would have far more impact than upgrading any sensor.
>
> To achieve < 0.01° (36 arcsec) pointing, the alignment must be improved to < 0.005° (18 arcsec), which requires precision optical alignment during I&T and/or on-orbit alignment calibration.

---

## 10.5 Momentum management and desaturation

Disturbance torques cause angular momentum to accumulate in reaction wheels over time. Without management, wheels saturate and lose control authority. Understanding this cycle is essential for AOCS design.

**The momentum lifecycle:**

1. **Accumulation:** External disturbance torques (gravity gradient, aero, SRP, magnetic) act on the spacecraft body. The control loop commands the reaction wheels to counteract these torques, absorbing the angular momentum. Wheel speed increases (or decreases) at a rate of $\dot{H} = T_{\text{disturbance}}$.

2. **Monitoring:** The OBC monitors wheel speeds. When any wheel exceeds a threshold (typically 80 % of maximum), a desaturation manoeuvre is triggered.

3. **Desaturation:** The OBC activates the magnetorquers to generate a torque that opposes the stored wheel momentum. The algorithm computes the optimal dipole command:

$$\vec{m}_{\text{cmd}} = -k_d (\vec{H}_{\text{wheel}} \times \hat{B})$$

where $k_d$ is the desaturation gain and $\hat{B}$ is the unit magnetic-field vector. This produces a torque $\vec{T} = \vec{m} \times \vec{B}$ in the direction that reduces $\vec{H}_{\text{wheel}}$.

4. **Completion:** Wheel speeds return to near zero (or bias speed). The cycle repeats.

Figure 10.4 shows the accumulation side of this cycle for the EOSat-3U case of §10.2, whose disturbance budget is dominated by the residual magnetic dipole rather than by drag, with the saturation lines of three wheel sizes, together with the order-of-magnitude ranking of disturbance sources.

![Reaction-wheel momentum accumulation and disturbance torque magnitudes.](../assets/figures/fig_rw_momentum.png)

**Figure 10.4** — Left: accumulated wheel momentum versus orbits since the last desaturation for the EOSat-3U case of §10.2 (1.5 µN m total disturbance at 500 km), against the capacity of 1, 10 and 40 mN m s wheels; the shaded band spans a 0.5–1.5× uncertainty on the residual dipole. The 10 mN m s wheel saturates after roughly one orbit, hence the once-per-orbit desaturation of §10.5. Right: the §10.2 disturbance torques — the residual magnetic dipole dominates by more than ten times, which is why the CubeSat case is magnetically rather than drag dominated.

**Desaturation constraints:**

- MTQs can only generate torque **perpendicular** to the local magnetic-field vector. They cannot dump momentum parallel to $\vec{B}$.
- Near the magnetic equator, $\vec{B}$ is nearly horizontal (north-pointing). MTQs can effectively dump momentum about the pitch and roll axes but not yaw.
- Near the magnetic poles, $\vec{B}$ is nearly vertical. MTQs can dump pitch and yaw but not roll.
- Over a full orbit, the field direction rotates sufficiently to dump all three axes. But at any instant, one axis is poorly controllable.
- A multi-pass desaturation strategy (spreading the dump over a full orbit) is more efficient than a single-point dump.

**Typical desaturation frequency for CubeSats:**

- At 500 km with 1.5 µN m total disturbance and 10 mN m s wheels: one desaturation per orbit (every ~95 minutes)
- Duration: 5–15 minutes per cycle
- Power: 0.5–1.5 W during desaturation (3 MTQ rods active)
- During desaturation, pointing accuracy degrades slightly (the MTQ torques perturb the attitude). Imaging should be inhibited during desaturation — a mode-transition rule that belongs in the ConOps (Chapter 18).

### 10.5.1 Wheel configurations — 3 + 1 redundancy

The standard 4-wheel configuration provides full 3-axis control with one spare:

- **3 wheels** in the body X, Y, Z axes provide minimum control
- **4th wheel** on a skew axis (typically [1,1,1] normalised, or cant angle 20–30° from each axis) provides redundancy and enhanced torque distribution
- If one wheel fails, the remaining three (including the skew wheel) maintain 3-axis control with reduced but adequate authority

**4-wheel torque envelope:** With 4 wheels in a pyramid configuration, the maximum torque in any body direction is:

$$T_{\text{max,body}} = \sqrt{2} \cdot T_{\text{wheel}} \approx 1.41 \times T_{\text{wheel}}$$

for the optimal distribution. This is better than the 3-orthogonal configuration where $T_{\text{max,body}} = T_{\text{wheel}}$ along any axis.

---

## 10.6 Worked example: UniSat-1 passive magnetic stabilisation

Returning to UniSat-1, the 1U demonstrator of Chapter 1 §1.7: it does not have an active AOCS. Instead, it uses **passive magnetic stabilisation** — the simplest and cheapest attitude-control method, requiring zero power and minimal mass.

**How it works — physics:**

1. **Permanent magnet:** A small bar magnet (typically AlNiCo or NdFeB, ~10–20 g, dipole moment $M_p = 0.1$–$1.0$ A m²) is embedded along one body axis (say, the Z-axis). In Earth's magnetic field $\vec{B}$, the magnet experiences a restoring torque:

$$\vec{T}_{\text{restoring}} = \vec{M}_p \times \vec{B}$$

This torque acts to align the magnet axis with the local field direction, analogous to a compass needle aligning with magnetic north. The restoring torque is maximum when the magnet is perpendicular to the field ($\alpha = 90°$) and zero when aligned ($\alpha = 0$).

For $M_p = 0.5$ A m² and $B = 3 \times 10^{-5}$ T: $T_{\text{max}} = 0.5 \times 3 \times 10^{-5} = 1.5 \times 10^{-5}$ N m. This is ~10× larger than any environmental disturbance torque, ensuring stable alignment.

2. **Hysteresis rods:** Two or more strips of magnetically soft material (e.g., Permalloy, HyMu-80, ~5–10 g each, dimensions ~60 × 1 × 1 mm) are mounted perpendicular to the permanent magnet. As the satellite oscillates around the field-aligned equilibrium, the external field component along the hysteresis rod alternates, driving the rod material around its B–H hysteresis loop. The area enclosed by the hysteresis loop represents energy dissipated per cycle as heat in the rod material. This extracts kinetic energy from the satellite's oscillation, damping it over time.

The energy dissipated per oscillation cycle is:

$$E_{\text{dissipated}} = V_{\text{rod}} \times \oint H \, dB$$

where $V_{\text{rod}}$ is the rod volume and $\oint H \, dB$ is the area of the hysteresis loop. For HyMu-80 material, typical energy density is ~100 J/m³ per cycle.

**Damping time constant:** From initial tumble (~10°/s after deployment) to settled oscillation (~1–5° amplitude), the damping process typically takes hours to days, depending on the hysteresis-rod material, volume, and the initial tumble rate.

**Performance:**

| Parameter | Passive magnetic | Active (RW + ST) |
|-----------|-----------------|------------------|
| Pointing accuracy | ~10–15° (to local B-field) | < 0.1° (to inertial frame) |
| Settling time | Hours to days after deployment | Minutes after mode transition |
| Residual tumble rate | ~1–5°/s (damped from initial ~10°/s) | < 0.01°/s |
| Power | 0 W | 3–5 W |
| Mass | ~30–50 g | 500–800 g |
| Cost (indicative, 2026) | ~2 kEUR | ~55 kEUR |
| Failure modes | Demagnetisation (radiation, temperature) | Motor failure, bearing wear, software bugs |

**Why this works for UniSat-1:** The MEMS magnetometer payload does not require accurate pointing. In fact, it benefits from being in a slowly rotating state because this provides magnetic-field measurements across multiple directions, improving the scientific data quality. The magnetometer can measure the field vector regardless of spacecraft orientation.

**No pointing budget needed:** Since there is no payload pointing requirement — recall that the UniSat-1 function tree of Chapter 6 has no "point" function — there is no need for a pointing error budget. This eliminates the star tracker, reaction wheels, magnetorquers (as actuators), sun sensors, and gyroscopes — removing the most expensive and power-hungry subsystem from the design.

> **Disturbance environment for a 1U at 400 km:**
>
> | Source | Torque (N m) | Calculation | Notes |
> |--------|-------------|-------------|-------|
> | Gravity gradient | ~$1 \times 10^{-8}$ | $\frac{3\mu}{2a^3} \Delta I$; $\Delta I \approx 0.001$ kg m² for a 1U | Small because nearly cubic ($I_z \approx I_x$) |
> | Aerodynamic | ~$3 \times 10^{-8}$ | $\frac{1}{2}\rho v^2 C_D A d$; $\rho(400 \text{ km}) \approx 5 \times 10^{-12}$ | Higher $\rho$ at 400 km than 500 km |
> | Solar radiation pressure | ~$1 \times 10^{-9}$ | $\frac{S}{c} A (1+q) d$; $A = 0.01$ m² | Small area |
> | Permanent magnet (restoring) | ~$1 \times 10^{-5}$ | $M_p \times B \times \sin\alpha$ | **Dominant** — this IS the control torque |
>
> The permanent-magnet restoring torque (~$10^{-5}$ N m) is three orders of magnitude larger than all disturbances combined. This ensures the satellite remains approximately field-aligned.

**Limitation:** Passive magnetic stabilisation provides alignment to the *local* magnetic field, which rotates as the satellite orbits. The satellite does not point at nadir, the Sun, or any fixed direction. For missions requiring Earth-pointing or Sun-tracking, active AOCS is mandatory. For UniSat-1's magnetometer mission, this is not a limitation — it is a feature.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| AD vs AC | Determination = know orientation (sensors); control = change orientation (actuators) |
| Star trackers | Pattern-match stars against catalogue; 3–15 arcsec accuracy; exclusion zones (Sun 25–45°, Earth 25–35°); most accurate sensor |
| Sun sensors | Coarse (photodiode, 2–5°) or fine (slit + array, 0.1°); essential for safe mode; every S/C needs them |
| Magnetometers | Measure $\vec{B}$ field; compare with IGRF model; 5–10° accuracy alone; residual dipole contamination is the key error source |
| GPS receivers | Orbit determination (position/velocity), not attitude; 5–20 m accuracy in LEO; needed for nadir-pointing computation |
| Gyroscopes | Measure angular rate $\vec{\omega}$; MEMS drift 1–10°/h; combined with star tracker via Kalman filter for high-bandwidth estimation |
| Architecture selection | Driven by pointing requirement: passive magnetic for > 5°; MTQ for 2–5°; RW + ST for < 0.1° |
| Disturbance torques | Gravity gradient, aero, SRP, magnetic dipole; **magnetic dipole dominates for CubeSats** |
| Reaction-wheel physics | $H = I_w \omega_w$; $T = dH/dt$; saturation occurs when $\omega \rightarrow \omega_{\text{max}}$; zero-crossing jitter |
| RW sizing | Torque ≥ 2× disturbance; momentum ≥ half-orbit accumulation; check slew time (torque- or momentum-limited) |
| Magnetorquer physics | $\vec{T} = \vec{m} \times \vec{B}$; torque always perpendicular to $\vec{B}$; cannot point, only detumble/desaturate |
| MTQ sizing | Desaturation torque must exceed disturbance accumulation rate; dump time well under one orbit |
| CMGs vs RWs | CMGs: torque amplification ($T = H \dot{\delta}$), for large/agile S/C; RWs: simpler, cheaper, standard for CubeSats |
| Pointing budget | RSS of 7 independent sources; alignment knowledge typically dominates; improve the dominant term |
| Budget-driven design | Investing in the smallest error source has negligible impact on the total; focus on the dominant term |
| Redundancy | 4-wheel (3 + 1 skew) provides single-fault tolerance; distribution matrix maps wheels to body torques |
| Momentum management | MTQs dump momentum against Earth's $\vec{B}$-field; ~once per orbit; 5–15 min; imaging inhibited during dump |

## Problems

1. **Architecture selection.** For (a) a 3U Earth-observation CubeSat requiring 0.05° pointing, (b) a 6U store-and-forward relay requiring 3° antenna pointing, and (c) UniSat-1, select an AOCS architecture from §10.1.2, list the sensors and actuators, and estimate mass, power and indicative cost. Justify each choice in two sentences.

2. **Disturbance torques.** Compute all four disturbance torques for a 6U CubeSat (12 kg, 0.06 m² reference area, $I_z = 0.10$ kg m², $I_x = 0.03$ kg m², cp–cm offset 3 cm, residual dipole 0.08 A m²) at 400 km (solar maximum) and at 700 km. Rank them in each case and identify the altitude at which aerodynamic torque overtakes the magnetic torque.

3. **Magnetic cleanliness.** Using the EOSat-3U worked example, recompute the total disturbance torque, the momentum-storage requirement and the desaturation duty if the residual dipole is reduced to 0.01 A m². How much smaller a wheel would suffice, and what would it save in mass and power?

4. **Reaction-wheel sizing.** A 3U CubeSat must perform a 60° slew in under 20 s and hold pointing between desaturations spaced one orbit apart at 550 km. With $I_{\text{axis}} = 0.04$ kg m² and a total disturbance of $2 \times 10^{-6}$ N m, compute the required torque, the required momentum, and check both torque-limited and momentum-limited slew times for the wheel classes in §10.3.2. Which wheel do you select?

5. **Momentum-limited slew.** Derive the slew time for the case in which the wheel reaches $H_{\text{max}}$ before the half-way point: show that $t_{\text{slew}} = \theta I/H_{\text{max}} + H_{\text{max}}/T_{\text{RW}}$ and verify the ≈ 59 s figure quoted for the micro wheel in §10.3.2.

6. **Magnetorquer sizing.** Size a magnetorquer set to dump 15 mN m s of wheel momentum within 25 minutes at 500 km ($B_{\text{avg}} = 3 \times 10^{-5}$ T). What dipole moment is needed, which magnetorquer type from §10.3.3 provides it, and what is the power cost per orbit if desaturation occurs once per orbit?

7. **Pointing budget.** Build the RSS pointing budget for a 3U Earth-observation CubeSat with a fine sun sensor and magnetometer (no star tracker) and reaction wheels, using the sun-sensor column of §10.4.1. Does it meet a 0.5° requirement? Identify the dominant term and the single most cost-effective improvement.

8. **Budget-driven design.** In the EOSat-3U pointing budget, the alignment term is 0.020°. Show quantitatively that halving the alignment error reduces the RSS more than eliminating every other term combined. Then determine the alignment knowledge required to meet a 0.02° (3σ) requirement with the remaining terms unchanged.

9. **Star-tracker accommodation.** A nadir-pointing 3U CubeSat in a 10:30 LTAN Sun-synchronous orbit mounts its star tracker on the zenith face. Using the exclusion angles of §10.1.1 and the β-angle behaviour of Chapter 7 §7.1.2, argue whether the Sun ever enters the exclusion zone, and propose a second mounting face that eliminates any outage. Record the resulting entries in the N² matrix of Chapter 8.

10. **UniSat-1 damping.** Estimate how many oscillation cycles UniSat-1's hysteresis rods (two rods of 60 × 1 × 1 mm, 100 J/m³ per cycle) need to remove the rotational kinetic energy of a 1.3 kg 1U ($I \approx 0.002$ kg m²) tumbling at 10°/s. If the oscillation period is of order one orbit, how long does settling take, and what does this imply for the start of science operations?

## References

1. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.1 (ADCS). https://www.space.com/smad
2. Markley, F. L. & Crassidis, J. L., *Fundamentals of Spacecraft Attitude Determination and Control*, Springer, 2014. https://link.springer.com/book/10.1007/978-1-4939-0802-8
3. Sidi, M. J., *Spacecraft Dynamics and Control*, Cambridge University Press, 1997, Ch. 4–9. https://www.cambridge.org/core/books/spacecraft-dynamics-and-control/82B47C7B6E2AA53BFAADAF26C2A79F14
4. Hughes, P. C., *Spacecraft Attitude Dynamics*, Wiley, 1986 (Dover reprint 2004). https://store.doverpublications.com
5. Wertz, J. R. & Larson, W. J. (eds.), *Space Mission Analysis and Design*, 3rd ed., 1999, Ch. 11 (ADCS). https://www.springer.com
6. ECSS, *ECSS-E-ST-60-10C: Control Performance*, 2008. https://ecss.nl/standard/ecss-e-st-60-10c-control-performance/
7. ECSS, *ECSS-E-ST-60-20C Rev.2: Star sensor terminology and performance specification*, 15 May 2019. https://ecss.nl/standard/ecss-e-st-60-20c-rev-2-star-sensor-terminology-and-performance-specification-15-may-2019/
8. Pong, C. M. et al., "ASTERIA: Achieving 10-arcsecond pointing on a 6U CubeSat," Small Satellite Conference, 2018. https://digitalcommons.usu.edu/smallsat/
9. Blue Canyon Technologies, *XACT ADCS and reaction-wheel datasheets*, 2023 (representative example). https://www.bluecanyontech.com
10. CubeSpace, *ADCS Product Catalogue*, 2023 (representative example). https://www.cubespace.co.za
