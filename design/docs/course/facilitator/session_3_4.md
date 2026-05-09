# Session 3.4: Structure, Propulsion, and Equipment Selection

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--3.3 (all subsystem sizing complete)
**SpaceCDF Tabs:** Equipment Browser, Dashboard, Trade Studies, Budget Breakdown

---

## References

- [Cal Poly, *CubeSat Design Specification (CDS) Rev 14.1*, February 2022](https://www.cubesat.org/cubesatinfo)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.3 (Structure), Ch. 17 (Propulsion)](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-32C Rev.1: Structural General Requirements*, 2008](https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/)
- [ECSS, *ECSS-E-ST-35C: Propulsion General Requirements*, 2008](https://ecss.nl/standard/ecss-e-st-35c-propulsion-general-requirements/)
- [Sarafin, *Spacecraft Structures and Mechanisms*, 1995](https://www.springer.com/gp/book/9780792334767)
- [Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., 2017, Ch. 2--4](https://www.wiley.com/en-us/Rocket+Propulsion+Elements)
- [Enpulsion, *NANO R3 Thruster Datasheet*, 2023](https://www.enpulsion.com/nano)
- [VACCO, *MiPS Propulsion System Datasheet*, 2023](https://www.cubesat-propulsion.com)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Verify CubeSat Design Specification (CDS) compliance for 1U--12U form factors
2. Compute structural margin of safety for quasi-static launch loads
3. Estimate the fundamental frequency requirement and verify it against deployer specifications
4. Apply the Tsiolkovsky rocket equation to compute propellant mass for a given $\Delta V$
5. Select appropriate propulsion technology based on mission $\Delta V$, thrust level, and form factor
6. Size onboard data storage from the data budget
7. Select flight hardware using SpaceCDF's equipment browser with budget tracking

---

## 1. CubeSat Structure and CDS Compliance (25 min)

### Teaching Notes

*[Source: Cal Poly CDS Rev 14.1, February 2022]*

### CDS Dimensional Specifications

| Form Factor | Dimensions (mm) | Max Mass (kg) | Internal Volume (cm$^3$) |
|------------|-----------------|---------------|------------------------|
| 1U | 100 x 100 x 113.5 | 2.0 | ~1000 |
| 1.5U | 100 x 100 x 170.2 | 3.0 | ~1500 |
| 2U | 100 x 100 x 227.0 | 4.0 | ~2000 |
| 3U | 100 x 100 x 340.5 | 6.0 | ~3000 |
| 6U | 100 x 226.3 x 340.5 | 12.0 | ~6000 |
| 12U | 226.3 x 226.3 x 340.5 | 24.0 | ~12000 |

### Key CDS Requirements

| Requirement | Specification |
|------------|---------------|
| Rail material | Hard anodised aluminium (7075-T6 or 6061-T6) |
| Rail cross-section | 8.5 x 8.5 mm minimum contact area |
| Surface finish | All external surfaces anodised or non-outgassing coating |
| Deployment switches | Minimum 1 on each accessible rail face (+X, -X) |
| Remove Before Flight (RBF) pin | Required; physically disables all power systems |
| Protrusions | None beyond rail envelope in stowed configuration |
| Centre of gravity | Within 2 cm of geometric centre (per deployer ICD) |
| Fundamental frequency | > 40 Hz first mode (typical deployer requirement) |

### Launch Load Environment

| Load Type | Typical Level | Verification Method |
|-----------|--------------|---------------------|
| Quasi-static acceleration | 6--9 g axial, 2--4 g lateral | Analysis + sine vibration test |
| Random vibration | Per launch vehicle PUG (20--2000 Hz spectrum) | Random vibration test (3 axes) |
| Shock | 500--2000 g at separation (high frequency) | Shock response spectrum test |
| Acoustic | Per vehicle specification | Usually covered by random vibration for CubeSats |

### Structural Margin of Safety

> **Key Equations -- Structural Margin of Safety**
>
> $$\text{MoS} = \frac{\sigma_{\text{allowable}}}{\sigma_{\text{design}} \times \text{FoS}} - 1$$
>
> where:
> - $\sigma_{\text{allowable}}$ = material yield or ultimate strength (MPa)
> - $\sigma_{\text{design}}$ = computed stress under design loads (MPa)
> - FoS = factor of safety
>
> **Requirement:** MoS $\geq$ 0 for all load cases.
>
> **Factors of safety (ECSS-E-ST-32C):**
>
> | Material | Yield FoS | Ultimate FoS |
> |----------|----------|-------------|
> | Metallic (Al 7075-T6) | 1.25 | 1.5 |
> | Composite (CFRP) | 1.5 | 2.0 |
> | Bonded joints | 1.5 | 2.0 |

> **Worked Example -- Axial Load on 3U CubeSat Rail**
>
> **Given:** 3U CubeSat, mass = 5 kg, axial launch load = 9 g, 4 rails (load shared equally), rail cross-section = 8.5 x 8.5 mm, material = Al 7075-T6 ($\sigma_y = 503$ MPa, $\sigma_u = 572$ MPa).
>
> **Step 1 -- Design load per rail:**
> $F = \frac{m \times a}{4} = \frac{5 \times 9 \times 9.81}{4} = \frac{441.5}{4} = 110.4$ N
>
> **Step 2 -- Stress:**
> $\sigma = \frac{F}{A} = \frac{110.4}{8.5 \times 10^{-3} \times 8.5 \times 10^{-3}} = \frac{110.4}{7.225 \times 10^{-5}} = 1.53$ MPa
>
> **Step 3 -- Margin of safety (yield):**
> $\text{MoS}_y = \frac{503}{1.53 \times 1.25} - 1 = \frac{503}{1.91} - 1 = 262 \gg 0$ **Pass** (by a very large margin)
>
> **Key insight:** For CubeSats, quasi-static axial stress on the rails is never the critical load case. The critical structural design drivers are usually: **(a)** stiffness (fundamental frequency > 40 Hz), **(b)** random vibration fatigue on PCB solder joints, and **(c)** deployment mechanism reliability.

### Fundamental Frequency

> **Key Equations -- Fundamental Frequency (simplified beam model)**
>
> For a cantilevered beam (simplified CubeSat model):
> $$f_1 = \frac{1.875^2}{2\pi L^2} \sqrt{\frac{EI}{\rho A}}$$
>
> where $E$ = Young's modulus (Pa), $I$ = second moment of area (m$^4$), $\rho$ = density (kg/m$^3$), $A$ = cross-section area (m$^2$), $L$ = length (m).
>
> **Requirement:** $f_1 > 40$ Hz (from deployer ICD).
>
> In practice, CubeSat structures meet this easily with Al frames. The concern is PCB stack assemblies and deployable mechanisms, which may have lower-frequency modes if not properly constrained.

---

## 2. Propulsion System Design (30 min)

### Teaching Notes

*[Source: SMAD, Ch. 17; Sutton & Biblarz, Ch. 2--4]*

### When Propulsion is Required

| Need | Typical $\Delta V$ | Example Scenario |
|------|-------------------|------------------|
| **Orbit maintenance** (drag compensation) | 5--15 m/s per year | LEO below 400 km |
| **Deorbit** | 50--150 m/s | Active disposal from > 600 km |
| **Collision avoidance** | 1--5 m/s per event | Conjunction avoidance manoeuvre |
| **Constellation phasing** | 10--50 m/s | Spreading satellites into operational slots |
| **Orbit raising** | 50--200 m/s | Transfer from deployment orbit to operational orbit |

### When NO Propulsion is Needed

- Orbit < 500 km: natural atmospheric decay provides FCC 5-year deorbit compliance
- Low-cost technology demonstration: limited lifetime acceptable, no orbit maintenance needed
- Constellation using differential drag for phasing (e.g., Planet SuperDove)
- Budget-constrained missions where propulsion cost/risk exceeds benefit

### The Tsiolkovsky Rocket Equation

> **Key Equations -- Tsiolkovsky Rocket Equation**
>
> $$\Delta V = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)$$
>
> Rearranged for propellant mass:
> $$m_{\text{propellant}} = m_{\text{dry}} \times \left(e^{\Delta V / (I_{sp} \cdot g_0)} - 1\right)$$
>
> where:
> - $I_{sp}$ = specific impulse (s) -- thruster efficiency metric
> - $g_0 = 9.80665$ m/s$^2$ -- standard gravitational acceleration
> - $m_0$ = initial (wet) mass (kg)
> - $m_f$ = final (dry) mass (kg)
> - $m_{\text{propellant}} = m_0 - m_f$

### CubeSat Propulsion Options

| Type | $I_{sp}$ (s) | Thrust | Dry Mass | $\Delta V$ (5 kg S/C) | TRL | Example Product |
|------|-------------|--------|----------|----------------------|-----|----------------|
| **Cold gas** (N$_2$, R-236fa) | 40--80 | 10--100 mN | 0.3--1.0 kg | 10--30 m/s | 9 | VACCO MiPS |
| **Resistojet** | 80--150 | 10--50 mN | 0.3--0.8 kg | 20--50 m/s | 7--8 | Busek AMAC |
| **Electrospray** (FEEP) | 500--1500 | 0.01--1 mN | 0.5--1.5 kg | 50--200 m/s | 7--8 | Enpulsion NANO R3 |
| **Hall effect** | 800--1500 | 1--10 mN | 1.0--3.0 kg | 100--500 m/s | 6--8 | Exotrail ExoMG-nano |
| **Hydrazine mono** | 200--230 | 0.1--1 N | 1.0--4.0 kg | 50--200 m/s | 9 | Aerojet MPS-130 |
| **Green monopropellant** | 200--250 | 0.1--1 N | 1.0--3.0 kg | 50--200 m/s | 7--8 | Bradford HPGP |

> **Worked Example -- Propellant Mass for Deorbit**
>
> **Scenario:** 3U CubeSat, $m_{\text{dry}} = 5.0$ kg, deorbit from 600 km ($\Delta V = 113$ m/s), cold gas thruster ($I_{sp} = 60$ s).
>
> $m_{\text{prop}} = 5.0 \times \left(e^{113/(60 \times 9.81)} - 1\right) = 5.0 \times \left(e^{0.192} - 1\right) = 5.0 \times 0.212 = $ **1.06 kg**
>
> **Problem:** 1.06 kg of propellant is 21% of the 3U mass limit (6 kg). This is a significant fraction.
>
> **Alternative with electrospray** ($I_{sp} = 1200$ s):
> $m_{\text{prop}} = 5.0 \times \left(e^{113/(1200 \times 9.81)} - 1\right) = 5.0 \times \left(e^{0.00960} - 1\right) = 5.0 \times 0.00965 = $ **0.048 kg**
>
> But the Enpulsion NANO R3 dry mass is 0.9 kg and thrust is 0.35 mN -- deorbit burn takes months.
>
> **Trade-off:** High-$I_{sp}$ systems use far less propellant but are heavier, lower-thrust, and require longer burn times. Low-$I_{sp}$ systems are lighter and provide immediate thrust but consume much more propellant.

### Propulsion Trade Summary

| Parameter | Cold Gas | Electrospray | Hall Effect |
|-----------|---------|-------------|------------|
| Propellant for 100 m/s | 0.87 kg | 0.042 kg | 0.052 kg |
| System dry mass | 0.3 kg | 0.9 kg | 1.5 kg |
| **Total system mass** | **1.17 kg** | **0.94 kg** | **1.55 kg** |
| Burn time | Minutes | Months | Weeks |
| Complexity | Low | Medium | High |
| Cost | ~15 kEUR | ~50 kEUR | ~80 kEUR |

---

## 3. On-Board Data Handling (15 min)

### Teaching Notes

### OBC Architecture

CubeSat OBCs provide computing, data storage, and bus management:

| Component | Typical Specification |
|-----------|----------------------|
| Processor | ARM Cortex-M4/M7 or Cortex-A (Linux-capable) |
| RAM | 64 MB -- 1 GB |
| Flash storage | 4--128 GB (NOR for code, NAND for data) |
| Interfaces | I$^2$C, SPI, UART, CAN, RS-422, USB |
| Operating system | FreeRTOS (real-time) or Linux (data-intensive) |
| Power | 0.5--3 W depending on processor |

### Data Storage Sizing

> **Key Equations -- Data Storage**
>
> $$S_{\text{required}} = V_{\text{daily}} \times N_{\text{days}} \times f_{\text{safety}}$$
>
> where $V_{\text{daily}}$ = daily data generation, $N_{\text{days}}$ = days between full downlinks (typically 1--2 for LEO), $f_{\text{safety}} = 2$ (to handle missed passes).

> **Worked Example -- Storage for 3U EO CubeSat**
>
> **Given:** Daily generation = 4.5 GB (from Session 3.3 data budget), daily downlink = 1.5 GB, days to clear backlog = $4.5/1.5 = 3$ days.
>
> $S_{\text{required}} = 4.5 \times 3 \times 2 = 27$ GB
>
> **Specify:** >= 32 GB flash storage.

### PC/104 Bus Standard

Most CubeSat avionics use the PC/104 stack architecture:

- **Board size:** 96 x 90 mm
- **Connector:** 104-pin stack-through header (2 x 52 pins, 2.54 mm pitch)
- **Signals:** 3.3 V, 5 V, 12 V, GND + I$^2$C, SPI, UART, CAN, GPIO
- **Stack capacity:** 1U ~ 4 boards; 3U ~ 12 boards; 6U ~ 24 boards

### Flight Software Functions

| Function | Description |
|----------|------------|
| **Mode management** | Transition between Safe, Idle, Imaging, Downlink, Eclipse modes |
| **ADCS control loop** | Attitude determination + control (PD/PID controller, Kalman filter) |
| **TM/TC handling** | Generate telemetry packets, execute telecommands |
| **Data handling** | Payload data acquisition, compression, buffering, downlink queue |
| **FDIR** | Fault Detection, Isolation, and Recovery (watchdog, safe mode triggers) |
| **Housekeeping** | Monitor temperatures, voltages, currents, wheel speeds |
| **Scheduling** | Time-tagged command execution (autonomous imaging, pass prep) |

---

## 4. Equipment Selection Exercise (45 min)

### Instructions

This is the primary hands-on session for Day 4 of the design week. Teams select actual hardware components.

1. **Open the Equipment Browser** (button in header bar)
2. The sidebar shows categories **annotated by need**:
   - Blue dot = Required for your mission
   - Circle = Optional
   - Dimmed = Not applicable
3. **For each required category, select a component:**
   - Check the quantity needed (e.g., 4 reaction wheels, 3 magnetorquers)
   - Note any RF compatibility warnings (transponder band must match antenna band)
   - Watch the **live budget bar** showing running mass / power / cost totals
4. **For each selection, verify:**
   - Does it fit within the subsystem mass allocation?
   - Is power draw within the power budget for its operational mode?
   - Is the interface compatible (PC/104? I$^2$C? SPI? CAN?)
5. **Review the Budget Breakdown** on the Dashboard:
   - Has per-subsystem mass changed from the parametric estimate?
   - Is the overall mass margin still positive?
   - Is the power budget still positive in all modes?

### Component Trade Study

For at least one subsystem, select 2--3 candidate components and run a formal tabular trade:

1. Navigate to the **Trade Studies** tab
2. Load or create a "Component Selection Trade" study
3. Define criteria: mass, power, cost, TRL, heritage, performance
4. Score each candidate (1--5 scale)
5. Apply weights and compute weighted scores
6. Document the winner and rationale

### Real Mission Example: Iridium NEXT Equipment Selection

Iridium NEXT (Thales Alenia Space, 2017--2019) serves as a large-scale example of rigorous equipment selection. For the phased-array antenna:

| Criterion | Weight | Candidate A (Thales) | Candidate B (Raytheon) |
|-----------|--------|---------------------|----------------------|
| Performance | 0.30 | 4.5 | 4.0 |
| Mass | 0.20 | 3.5 | 4.0 |
| Cost | 0.20 | 3.0 | 4.5 |
| TRL | 0.15 | 5.0 | 4.0 |
| Schedule | 0.15 | 4.0 | 3.5 |
| **Weighted** | | **3.95** | **4.00** |

The selection was ultimately Candidate A (Thales) due to contractual considerations beyond the numerical trade -- illustrating that trade studies inform but do not dictate decisions.

---

## 5. SpaceCDF Budget Closure Check (15 min)

### Instructions

After equipment selection, perform a final budget health check:

1. **Dashboard KPIs:** Record all margins
   - Mass margin (%) -- green/amber/red?
   - Power margin per mode (W)
   - Link margin (dB)
   - Cost vs ceiling (MEUR)
   - Pointing accuracy vs requirement (deg)
2. **Budget Comparison:** Compare parametric estimates to equipment-based totals
3. **Identify any negative margins** -- these must be resolved before proceeding to integration (Week 3)

### If a Budget Does Not Close

| Budget | Common Fix | Impact |
|--------|-----------|--------|
| **Mass** (negative) | Remove propulsion; select lighter components; reduce redundancy | Risk / performance trade |
| **Power** (negative) | Add deployable SA; reduce payload duty cycle; select lower-power AOCS | Cost / schedule trade |
| **Link** (negative) | Increase TX power; use higher-gain antenna; reduce data rate; upgrade coding | Mass / power trade |
| **Cost** (over ceiling) | Use COTS instead of rad-hard; remove propulsion; reduce ground segment | Risk / capability trade |

---

## Worked Example: Complete 3U EO CubeSat Equipment List

> | Category | Component | Mass (kg) | Power (W) | Cost (kEUR) | Qty |
> |----------|-----------|----------|----------|-------------|-----|
> | EPS Board | GomSpace P31u | 0.10 | 0.5 | 8 | 1 |
> | Battery | GomSpace BP4 (20 Wh) | 0.20 | -- | 5 | 1 |
> | Solar Panels | MMA HaWK (deploy) | 0.45 | -- | 25 | 2 |
> | OBC | GomSpace A3200 | 0.08 | 1.0 | 12 | 1 |
> | Reaction Wheel | Blue Canyon RW210 | 0.055 | 0.6 | 8 | 4 |
> | Magnetorquer | CubeSpace CubeMAG | 0.03 | 0.1 | 3 | 3 |
> | Star Tracker | Blue Canyon NST | 0.35 | 1.5 | 35 | 1 |
> | Sun Sensor | NewSpace NFSS-411 | 0.005 | 0.01 | 1 | 6 |
> | Transponder | Endurosat S-band TX/RX | 0.10 | 6.0 (TX) | 15 | 1 |
> | Antenna | Endurosat S-band patch | 0.02 | -- | 3 | 1 |
> | Payload | Custom telescope | 1.50 | 5.0 | 150 | 1 |
> | Structure | ISIS 3U frame | 0.30 | -- | 8 | 1 |
> | Harness | Custom | 0.15 | -- | 5 | 1 |
> | **TOTAL** | | **3.57** | **~10 (imaging)** | **~290** | |
>
> **Parametric estimate from Session 2.4:** 3.68 kg CBE. **Equipment total:** 3.57 kg. Difference: -3% (within expected range).

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| CDS compliance | Standard dimensions, rail specs, deployment switches, RBF pin, CG limits |
| Launch loads | 6--9 g axial, random vibe 20--2000 Hz; MoS $\geq$ 0 with FoS 1.25 (yield) / 1.5 (ultimate) |
| Frequency req | First mode > 40 Hz; CubeSat structures easily meet this; PCBs and deployables are the risk |
| Tsiolkovsky | $m_{\text{prop}} = m_{\text{dry}} \times (e^{\Delta V/(I_{sp} g_0)} - 1)$ |
| Propulsion trades | High-$I_{sp}$: less propellant, more dry mass, long burns; Low-$I_{sp}$: more propellant, light system, fast burns |
| When to skip propulsion | Below 500 km (natural deorbit); tech demo; differential drag constellation |
| Data handling | Storage $\geq 2\times$ daily generation; PC/104 stack architecture; FreeRTOS or Linux |
| Equipment selection | Live budget tracking; RF compatibility check; trade study for contested selections |
| Budget closure | All margins must be positive before proceeding to integration week |
