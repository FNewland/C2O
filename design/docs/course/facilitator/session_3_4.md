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
- [Tyvak, *Structure Specifications*, 2023](https://www.tyvak.com)
- [ECSS, *ECSS-E-ST-10-03C: Testing*, 2012](https://ecss.nl/standard/ecss-e-st-10-03c-testing/)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Verify CubeSat Design Specification (CDS) compliance for 1U--12U form factors
2. Explain the structural load environment (quasi-static, vibration, shock) and its physical origins
3. Compute structural margin of safety for quasi-static launch loads
4. Estimate the fundamental frequency requirement and verify it against deployer specifications
5. Apply the Tsiolkovsky rocket equation to compute propellant mass for a given $\Delta V$
6. Explain the physics of each propulsion technology and select based on mission requirements
7. Select OBC architecture based on processing, radiation, and interface requirements
8. Size onboard data storage from the data budget
9. Select flight hardware using SpaceCDF's equipment browser with budget tracking

---

## 1. CubeSat Structure and CDS Compliance (30 min)

### Teaching Notes

*[Source: Cal Poly CDS Rev 14.1, February 2022; ECSS-E-ST-32C]*

### CDS Dimensional Specifications

| Form Factor | Dimensions (mm) | Max Mass (kg) | Internal Volume (cm$^3$) | Typical Deployer |
|------------|-----------------|---------------|------------------------|-----------------|
| 1U | 100 x 100 x 113.5 | 2.0 | ~1000 | ISIPOD, P-POD |
| 1.5U | 100 x 100 x 170.2 | 3.0 | ~1500 | ISIPOD |
| 2U | 100 x 100 x 227.0 | 4.0 | ~2000 | ISIPOD, P-POD |
| 3U | 100 x 100 x 340.5 | 6.0 | ~3000 | P-POD, ISIPOD, NanoRacks NRCSD |
| 6U | 100 x 226.3 x 340.5 | 12.0 | ~6000 | 6U deployer (Exolaunch, D-Orbit) |
| 12U | 226.3 x 226.3 x 340.5 | 24.0 | ~12000 | 12U deployer (Exolaunch) |

### Structural Materials

**CubeSat rail material: Aluminium 7075-T6**

This is the most commonly specified structural aluminium alloy for CubeSat rails. The CDS mandates hard-anodised aluminium for the rails (the four load-bearing edges that slide along the deployer guide channels).

| Property | Al 7075-T6 | Al 6061-T6 | Ti-6Al-4V | CFRP (quasi-isotropic) |
|----------|-----------|-----------|-----------|----------------------|
| Density (kg/m$^3$) | 2810 | 2700 | 4430 | 1600 |
| Yield strength $\sigma_y$ (MPa) | 503 | 276 | 880 | N/A (use ultimate) |
| Ultimate strength $\sigma_u$ (MPa) | 572 | 310 | 950 | 500--800 |
| Young's modulus $E$ (GPa) | 71.7 | 68.9 | 114 | 70--150 (direction-dependent) |
| CTE (ppm/degC) | 23.6 | 23.1 | 8.6 | 0--2 (tuneable) |
| Thermal conductivity (W/m/K) | 130 | 167 | 6.7 | 3--10 |

*[Source: MMPDS / ASM Handbook; Hexcel HexPly datasheets]*

**Why Al 7075-T6 for rails:**
- High strength-to-weight ratio (superior to 6061-T6)
- Hard anodisation provides a durable, low-friction surface finish for deployer guide channel contact (reduces galling, provides electrical insulation)
- Good machinability
- Extensive flight heritage (virtually every CubeSat ever launched)
- CTE-matched to Al deployer structure (prevents differential thermal expansion binding)

**Why NOT other materials for rails:**
- **Titanium:** Excellent strength but poor thermal conductivity (thermal hot spots), difficult to machine, risk of galling against aluminium deployer
- **CFRP:** Cannot be anodised; CTE mismatch with Al deployer causes binding at temperature extremes; poor electrical conductivity (grounding/bonding issues)
- **Stainless steel:** Too heavy; poor CTE match

**Anodisation physics:** Anodisation is an electrochemical process that grows a hard aluminium oxide ($\text{Al}_2\text{O}_3$) layer on the surface. Hard anodisation (Type III) produces a 25--75 um thick oxide layer with hardness of 60--70 HRC (harder than most steel). This layer provides: wear resistance against deployer contact, electrical insulation (prevents arcing between satellite and deployer), corrosion resistance, and controlled surface optical properties ($\alpha_s \approx 0.3$--$0.5$, $\varepsilon \approx 0.8$--$0.85$ for clear anodise; $\alpha_s \approx 0.9$, $\varepsilon \approx 0.85$ for black anodise).

### Key CDS Requirements

| Requirement | Specification | Physical Rationale |
|------------|---------------|-------------------|
| Rail material | Hard anodised aluminium (7075-T6 or 6061-T6) | Wear resistance, CTE match to deployer, electrical isolation |
| Rail cross-section | 8.5 x 8.5 mm minimum contact area | Adequate bearing area for launch loads; prevents rail yielding under quasi-static acceleration |
| Surface finish | All external surfaces anodised or non-outgassing coating | Prevent contamination of other payloads on launch vehicle (molecular outgassing deposits on optics) |
| Deployment switches | Minimum 1 on each accessible rail face (+X, -X) | Inhibit all spacecraft activity until fully deployed from deployer (prevents inadvertent deployment, RF emissions in fairing) |
| Remove Before Flight (RBF) pin | Required; physically disables all power systems | Final safety inhibit; removed at launch pad after integration; ensures zero RF emissions and zero deployment actuator current until intentional removal |
| Protrusions | None beyond rail envelope in stowed configuration | Ensures clean ejection from deployer; prevents snagging on guide rails or adjacent CubeSat |
| Centre of gravity | Within 2 cm of geometric centre (per deployer ICD) | Prevents wobble during deployment ejection; ensures all CubeSats eject with similar tip-off rates |
| Fundamental frequency | > 40 Hz first mode (typical deployer requirement) | Prevents dynamic coupling between satellite and launch vehicle structural modes (which cluster at 10--30 Hz) |

### PC/104 Stack Architecture

Most CubeSat avionics use the PC/104-compatible stack architecture, a heritage from the industrial embedded computing standard adapted for space:

**Physical specifications:**
- **Board size:** 96 x 90 mm (standard) or 90 x 96 mm
- **Connector:** 104-pin stack-through header (2 x 52 pins, 2.54 mm pitch) -- original PC/104 pinout carries power + I2C + SPI + UART + GPIO
- **Stack spacing:** Typically 10--15 mm between boards (constrained by component height and connector mating height)
- **Stack capacity:** 1U accommodates ~4 boards; 3U accommodates ~12 boards (340 mm / ~28 mm per board slot)

**What rides on the stack:**
- EPS board (battery management, MPPT, power distribution)
- OBC board (processor, memory, interfaces)
- Communications board (UHF radio, or S-band transponder)
- AOCS board (if integrated -- some vendors combine IMU + magnetorquer driver + RW interface on one PCB)
- Payload interface board (ADC, sensor interfaces)

**Mechanical concerns:**
- Solder joints are the weakest point; random vibration causes fatigue cracking at heavy component leads (especially tall electrolytic capacitors, large connectors, and crystal oscillators)
- Board-to-board connectors must be properly preloaded (too loose = intermittent contact; too tight = difficult assembly/disassembly during I&T)
- Standoffs and spacers must be correctly torqued; Loctite 222 (low-strength threadlocker) is standard

### Launch Load Environment

The launch environment subjects the satellite to loads from engine thrust, aerodynamic buffeting, stage separation, and pyrotechnic events. The satellite must survive all of these without structural failure or functional degradation.

| Load Type | Physical Source | Typical Level | Duration | Frequency Range | Verification Method |
|-----------|----------------|--------------|----------|----------------|---------------------|
| **Quasi-static acceleration** | Engine thrust + aeroloading | 6--12 g axial, 2--4 g lateral | Seconds to minutes | 0 (static equivalent) | Analysis + sine vibration test |
| **Sine vibration** | Low-frequency vehicle dynamics | 0.5--3 g (5--100 Hz) | Minutes | 5--100 Hz | Sine sweep test (3 axes) |
| **Random vibration** | Acoustic noise + turbulent boundary layer | 5--15 grms (20--2000 Hz) | 60--120 s per axis | 20--2000 Hz | Random vibration test (3 axes) |
| **Shock** | Pyrotechnic separation events (stage sep, fairing sep, deployer spring release) | 500--2000 g at separation (high frequency) | < 10 ms | 100--10,000 Hz | Shock response spectrum (SRS) test |
| **Acoustic** | Sound pressure from engine exhaust, aerodynamic noise | 120--140 dB (20--10,000 Hz) | Minutes | 20--10,000 Hz | Usually covered by random vib for CubeSats |

*[Source: ECSS-E-ST-10-03C; NASA GEVS (GSFC-STD-7000B); Falcon 9 Payload User's Guide; PSLV User's Guide]*

**Random vibration PSD profile (typical CubeSat deployer level):**

| Frequency (Hz) | ASD Level (g$^2$/Hz) | Notes |
|----------------|---------------------|-------|
| 20 | 0.01 | Low-frequency start (ramp up) |
| 50 | 0.04 | Ramp up at +6 dB/oct |
| 100 | 0.04 | Flat region start |
| 800 | 0.04 | Flat region end |
| 2000 | 0.01 | Roll off at -6 dB/oct |
| **Overall** | **~7 grms** | Typical for CubeSat deployer qualification level |

The flat region at 0.04 g$^2$/Hz from 100--800 Hz is where most structural damage occurs, because this is where PCB resonances and solder joint fatigue are excited.

**What fails during vibration testing:**
1. **Solder joints:** Heavy components (connectors, tall capacitors, transformers) with long lever arms crack at their solder joints. Mitigation: use surface-mount components, stake tall components with adhesive (Loctite 4860 or similar), use conformal coating.
2. **Deployable mechanisms:** Antenna hinges, solar panel hold-down mechanisms, and deployment springs can fail if not properly constrained. Mitigation: adequate preload on hold-down mechanisms, shock testing of pyrotechnic release devices.
3. **Optical components:** Lenses and mirrors can shift or crack if not properly mounted with strain-relief. Mitigation: RTV potting, flexure mounts.
4. **Wire harness:** Chafing against structure edges. Mitigation: edge radii > 1 mm, harness tie-downs every 50 mm, protective sleeving.

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
> | Material / Joint | Yield FoS | Ultimate FoS | Rationale |
> |-----------------|----------|-------------|-----------|
> | Metallic (Al 7075-T6) | 1.25 | 1.5 | Standard structural metals |
> | Composite (CFRP) | 1.5 | 2.0 | Higher variability in laminate properties |
> | Bonded joints | 1.5 | 2.0 | Bond strength is highly process-dependent |
> | Pressurised systems | 1.5 | 2.0 | Burst hazard to other payloads |
> | Mechanisms (single-use) | -- | 2.0 | Must work first time; no test opportunity |
>
> **Design loads:** The design load includes the quasi-static acceleration (from the launch vehicle user guide), multiplied by a dynamic amplification factor ($DAF \approx 1.25$--$1.5$) if the satellite's natural frequency is near any launch vehicle forcing frequency.

> **Worked Example -- Axial Load on 3U CubeSat Rail (SuperDove-class)**
>
> **Given:** 3U CubeSat, mass = 5 kg, axial launch load = 9 g (Falcon 9 typical), 4 rails (load shared equally), rail cross-section = 8.5 x 8.5 mm, material = Al 7075-T6 ($\sigma_y = 503$ MPa, $\sigma_u = 572$ MPa).
>
> **Step 1 -- Design load per rail:**
> $F = \frac{m \times n \times g_0}{4} = \frac{5 \times 9 \times 9.81}{4} = \frac{441.5}{4} = 110.4$ N
>
> **Step 2 -- Compressive stress:**
> $\sigma = \frac{F}{A_{\text{rail}}} = \frac{110.4}{8.5 \times 10^{-3} \times 8.5 \times 10^{-3}} = \frac{110.4}{7.225 \times 10^{-5}} = 1.53$ MPa
>
> **Step 3 -- Margin of safety (yield):**
> $\text{MoS}_y = \frac{503}{1.53 \times 1.25} - 1 = \frac{503}{1.91} - 1 = 262 \gg 0$ **Pass** (by a very large margin)
>
> **Step 4 -- Margin of safety (ultimate):**
> $\text{MoS}_u = \frac{572}{1.53 \times 1.5} - 1 = \frac{572}{2.30} - 1 = 248 \gg 0$ **Pass**
>
> **Key insight:** For CubeSats, quasi-static axial stress on the rails is never the critical load case. The rails are massively over-designed for direct compression. The critical structural design drivers are usually:
> 1. **Stiffness** (fundamental frequency > 40 Hz) -- driven by internal board/component mounting, not rail strength
> 2. **Random vibration fatigue** on PCB solder joints -- the real failure mode
> 3. **Deployment mechanism reliability** -- spring force, latch engagement, alignment tolerances
> 4. **CG location** -- difficult to achieve with asymmetric payloads or propulsion tanks

### Fundamental Frequency

> **Key Equations -- Fundamental Frequency (simplified beam model)**
>
> For a cantilevered beam (simplified CubeSat model, clamped at deployer interface):
> $$f_1 = \frac{1.875^2}{2\pi L^2} \sqrt{\frac{EI}{\rho A_{\text{cross}}}}$$
>
> where $E$ = Young's modulus (Pa), $I$ = second moment of area (m$^4$), $\rho$ = linear density (kg/m), $A_{\text{cross}}$ = cross-section area (m$^2$), $L$ = length (m).
>
> **Requirement:** $f_1 > 40$ Hz (from deployer ICD). Some deployers require $> 90$ Hz (e.g., NanoRacks NRCSD).
>
> **For a 3U CubeSat modelled as a cantilevered Al box beam:**
> - $L = 0.34$ m, $E = 72$ GPa, box wall thickness $t = 1.5$ mm
> - $I \approx \frac{b^4 - (b-2t)^4}{12} = \frac{0.10^4 - 0.097^4}{12} \approx 1.36 \times 10^{-6}$ m$^4$
> - Linear mass: $\rho_L = m/L = 5/0.34 = 14.7$ kg/m
>
> $f_1 = \frac{3.516}{2\pi \times 0.34^2} \sqrt{\frac{72 \times 10^9 \times 1.36 \times 10^{-6}}{14.7}} = \frac{3.516}{0.726} \sqrt{6666} = 4.84 \times 81.6 = 395$ Hz
>
> **This easily exceeds 40 Hz.** The structure itself is very stiff. However, the actual first mode is usually determined by: (a) the heaviest internal component on its mounting bracket (e.g., a 350 g star tracker cantilevered on a bracket), or (b) a deployable mechanism in its stowed configuration (e.g., a folded solar panel constrained only by a hold-down pin). **These local modes, not the overall structural mode, are typically the design concern.**

---

## 2. Propulsion System Design (30 min)

### Teaching Notes

*[Source: SMAD, Ch. 17; Sutton & Biblarz, Ch. 2--4; Goebel & Katz, *Fundamentals of Electric Propulsion*, 2008]*

### When Propulsion is Required

| Need | Typical $\Delta V$ | Example Scenario | Timeline |
|------|-------------------|------------------|----------|
| **Orbit maintenance** (drag compensation) | 5--15 m/s per year | LEO below 400 km in solar maximum | Continuous low-thrust |
| **Deorbit** (active disposal) | 50--150 m/s | Active disposal from > 600 km (FCC 5-year rule) | End of mission |
| **Collision avoidance** | 1--5 m/s per event | Conjunction avoidance, 2--5 events per year for LEO | On-demand, within hours |
| **Constellation phasing** | 10--50 m/s | Spreading satellites into operational orbit slots | Weeks to months |
| **Orbit raising** | 50--200 m/s | Transfer from deployment orbit to operational orbit | Weeks to months |
| **Station-keeping** | 1--10 m/s per year | Maintain orbit altitude and phase | Periodic |

### When NO Propulsion is Needed

- **Orbit < 500 km:** Natural atmospheric decay provides FCC 5-year deorbit compliance (depends on ballistic coefficient and solar activity)
- **Low-cost technology demonstration:** Limited lifetime acceptable, no orbit maintenance needed
- **Constellation using differential drag for phasing** (e.g., Planet SuperDove adjusts its cross-section area to create differential drag, enabling free phasing manoeuvres)
- **Budget-constrained missions** where propulsion cost/risk/mass exceeds benefit

### The Tsiolkovsky Rocket Equation -- Physics

The rocket equation is the fundamental relationship governing all propulsive manoeuvres. It derives from conservation of momentum: the momentum of the exhaust equals the momentum change of the spacecraft.

> **Key Equations -- Tsiolkovsky Rocket Equation**
>
> Starting from $F = \dot{m} v_e$ (thrust = mass flow rate x exhaust velocity) and integrating:
>
> $$\Delta V = v_e \ln\left(\frac{m_0}{m_f}\right) = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)$$
>
> Rearranged for propellant mass:
> $$m_{\text{propellant}} = m_{\text{dry}} \times \left(e^{\Delta V / (I_{sp} \cdot g_0)} - 1\right)$$
>
> where:
> - $v_e = I_{sp} \times g_0$ = effective exhaust velocity (m/s)
> - $I_{sp}$ = specific impulse (s) -- the "fuel efficiency" of the thruster. Physically: how many seconds a thruster can produce 1 N of thrust from 1 kg of propellant under standard gravity. Higher $I_{sp}$ = less propellant needed.
> - $g_0 = 9.80665$ m/s$^2$ -- standard gravitational acceleration (conversion factor)
> - $m_0$ = initial (wet) mass (kg) = $m_f + m_{\text{propellant}}$
> - $m_f$ = final (dry) mass (kg) = spacecraft mass after all propellant is consumed
>
> **The tyranny of the rocket equation:** The propellant mass grows exponentially with $\Delta V / v_e$. For $\Delta V = v_e$ (one exhaust velocity worth of $\Delta V$), 63% of the initial mass must be propellant. For $\Delta V = 2 v_e$, 86% must be propellant. This is why high-$I_{sp}$ systems are so valuable for large $\Delta V$ missions -- they move the $v_e$ in the denominator, dramatically reducing the mass ratio.

### CubeSat Propulsion Technologies -- Physics and Comparison

#### Cold Gas Propulsion

**Physics:** Compressed gas (N$_2$, xenon, R-236fa refrigerant, or other) is stored in a tank at 1--30 MPa. When a valve opens, gas expands through a nozzle, converting thermal/pressure energy to kinetic energy. No combustion, no heating, no chemical reaction.

**Thrust:** $F = \dot{m} v_e + (p_e - p_a) A_e$. For a small converging nozzle, $v_e \approx \sqrt{2 c_p T_0}$ where $T_0$ is the tank temperature. For N$_2$ at 300 K: $v_e \approx 500$--$750$ m/s, giving $I_{sp} \approx 50$--$75$ s.

**Advantages:** Simplest system (no ignition, no power except valve solenoid), fast response (ms-level valve opening), high reliability, no plume contamination concerns.

**Disadvantages:** Low $I_{sp}$ (large propellant mass for given $\Delta V$), bulky high-pressure tank, limited total impulse.

**Products:** VACCO MiPS (R-236fa, $I_{sp} = 40$ s, 4 thrusters, 0.3 kg dry), VACCO ArgoMoon (Xe cold gas), Bradford ECAPS cold gas.

**Missions using cold gas:** MarCO (6U, JPL -- used R-236fa cold gas for trajectory correction and attitude control en route to Mars), many ISS-deployed CubeSats for collision avoidance.

#### Resistojet / Warm Gas

**Physics:** Similar to cold gas, but the propellant is electrically heated before expansion through the nozzle. Heating increases the gas temperature $T_0$, which increases the exhaust velocity ($v_e \propto \sqrt{T_0}$). Common propellants: butane (C$_4$H$_{10}$), water (H$_2$O), ammonia (NH$_3$).

**Butane propulsion:** Butane is stored as a liquid at its saturation pressure (~2 atm at 20 degC). When heated to 200--400 degC and expanded through a nozzle, it achieves $I_{sp} \approx 80$--$100$ s. The liquid storage is much denser than compressed gas, allowing more propellant in a smaller tank.

**Advantages:** Higher $I_{sp}$ than cold gas (~2x), dense liquid storage, moderate complexity.

**Disadvantages:** Requires electrical power for heating (5--15 W during firing), lower thrust than cold gas, potential for nozzle clogging if propellant decomposes.

**Products:** Busek BGT-X5 (butane, $I_{sp} = 80$ s), NanoAvionics EPSS (butane, $I_{sp} = 85$ s), Pale Blue water resistojet ($I_{sp} = 70$--$80$ s).

#### Green Monopropellant

**Physics:** A liquid propellant is injected into a catalyst bed where it decomposes exothermically, producing hot gases that expand through a nozzle. "Green" propellants are alternatives to hydrazine (N$_2$H$_4$) that are less toxic and easier to handle.

| Propellant | Chemical | $I_{sp}$ (s) | Density (kg/m$^3$) | Toxicity | TRL | Heritage |
|-----------|----------|-------------|-------------------|---------|-----|---------|
| **Hydrazine** (N$_2$H$_4$) | Monopropellant, Shell 405 catalyst | 220--230 | 1010 | **Extremely toxic** (carcinogen) | 9 | 50+ years, thousands of missions |
| **AF-M315E (ASCENT)** | HAN-based ionic liquid | 235--250 | 1460 | Low toxicity | 8 | GPIM demo (2019, NASA) |
| **LMP-103S** | ADN-based ionic liquid | 225--235 | 1240 | Low toxicity | 8 | PRISMA demo (2010, SSC), SkySat |
| **HTP (H$_2$O$_2$ 90%)** | Hydrogen peroxide + silver catalyst | 150--165 | 1400 | Moderate (oxidiser) | 7 | Various small satellites |

*[Source: Masse et al., "GPIM AF-M315E Propulsion System," AIAA 2019; Anflo et al., "Flight Demonstration of LMP-103S," AIAA 2011]*

**Advantages:** High thrust (0.1--1 N for CubeSat systems), good $I_{sp}$ (220+ s), proven technology (heritage from hydrazine systems).

**Disadvantages:** Requires catalyst preheating (2--10 W, 10--30 min warmup), higher system mass (tank + catalyst bed + valves + feed system), propellant handling safety requirements (even "green" propellants require PPE), higher cost ($100K+ for flight units).

**Products:** Aerojet MPS-130 (AF-M315E, 1 N thrust, $I_{sp} = 235$ s, 3 kg system mass), Bradford HPGP (LMP-103S, 1 N, $I_{sp} = 230$ s).

#### Electric Propulsion -- Electrospray (FEEP)

**Physics:** Field Emission Electric Propulsion (FEEP) uses a strong electric field (~$10^9$ V/m) at the tip of a needle or along the edge of a slit to ionise and extract metal atoms (typically indium or gallium) or ionic liquid droplets. The ions are accelerated by an electric field to high velocities (10--50 km/s), producing very high $I_{sp}$.

**How it works (indium FEEP):**
1. Solid indium is heated to just above its melting point (157 degC) to form a liquid reservoir
2. Capillary action draws liquid indium to an array of sharp emitter tips
3. A high voltage (1--10 kV) between the emitter tips and an extractor grid creates an intense electric field at the tip apex
4. The field ionises individual indium atoms via field evaporation
5. The ions are accelerated through the extractor grid, creating a beam of In$^+$ ions at 20--40 km/s
6. A neutraliser (typically a carbon nanotube or thermionic emitter) emits electrons to neutralise the beam and prevent spacecraft charging

**Performance:** $I_{sp} = 500$--$5000$ s (adjustable by varying acceleration voltage), thrust = 0.01--1 mN, power = 20--60 W.

**Advantages:** Extremely high $I_{sp}$ (minimal propellant consumption), no pressurised tanks, compact solid propellant storage, precise thrust control (useful for formation flying).

**Disadvantages:** Very low thrust (months-long burn times for significant $\Delta V$), requires significant power (20--60 W for ~0.5 mN thrust), plume contamination from metal ions (indium deposition on surfaces), limited heritage.

**Products:** Enpulsion NANO R3 (indium FEEP, 0.35 mN, $I_{sp} = 1000$--$5000$ s, 0.9 kg dry mass, < 40 W), Accion TILE (ionic liquid electrospray, 0.1 mN, $I_{sp} = 1500$ s).

**Missions using FEEP/electrospray:** LISA Pathfinder (ESA, precision formation flying, used colloid thrusters), SSTL NovaSAR-1 (Enpulsion NANO for orbit maintenance).

#### Electric Propulsion -- Hall Effect Thruster

**Physics:** A Hall effect thruster uses crossed electric and magnetic fields to ionise a neutral propellant gas (xenon, krypton, or iodine) and accelerate the resulting ions to high velocity.

**How it works:**
1. Neutral propellant gas (Xe or I$_2$) is injected into an annular discharge channel
2. A radial magnetic field (from permanent magnets or electromagnets) traps electrons in a Hall current loop, preventing them from reaching the anode
3. The trapped electrons collide with neutral gas atoms, ionising them
4. The ions, being much heavier, are not significantly deflected by the magnetic field and are accelerated axially by the electric field (100--500 V) between anode and cathode
5. An external cathode (hollow cathode or RF cathode) provides electrons for beam neutralisation and to sustain the discharge

**Performance:** $I_{sp} = 800$--$3000$ s, thrust = 1--50 mN for CubeSat-scale systems, power = 50--300 W.

**Advantages:** Higher thrust than FEEP (N range for larger systems), excellent $I_{sp}$, well-proven technology (GEO station-keeping heritage: Aerojet PPS-1350, Busek BHT-200).

**Disadvantages:** Requires significant power (> 50 W for CubeSat-scale), heavy cathode assembly, xenon storage requires high-pressure tanks (100--300 bar), channel erosion limits lifetime.

**Products:** Exotrail ExoMG-nano (40 mN, $I_{sp} = 800$ s, 1.5 kg, 60 W), Busek BHT-200 (13 mN, $I_{sp} = 1370$ s, 1.0 kg, 200 W), Enpulsion MICRO (Hall thruster, iodine propellant, 1 mN, $I_{sp} = 1000$ s).

**Iodine propulsion:** Iodine (I$_2$) is emerging as an alternative to xenon for Hall thrusters and gridded ion engines. Iodine is solid at room temperature (stored without a pressure vessel), has a density of 4940 kg/m$^3$ (vs xenon at ~1600 kg/m$^3$ at 100 bar), and has similar atomic mass (127 vs 131). The Busek BIT-3 (iodine Hall thruster) and ThrustMe NPT30-I2 have demonstrated iodine propulsion in orbit.

#### No Propulsion -- Passive Deorbit Strategies

For missions below ~500 km where propulsion is not needed for operations, passive deorbit can satisfy the FCC 5-year or IADC 25-year guidelines:

| Method | Mechanism | Mass | Volume | Effectiveness | TRL |
|--------|-----------|------|--------|--------------|-----|
| **Atmospheric drag (natural)** | Below 500 km, atmospheric drag naturally decays the orbit | 0 | 0 | Depends on ballistic coefficient and solar cycle | 9 |
| **Drag sail** | Deployable membrane increases cross-section area by 10--100x | 0.1--0.5 kg | 0.25--1U | Very effective above 600 km | 7--8 |
| **Drag chute (tether)** | Electrodynamic tether interacts with geomagnetic field to decelerate | 0.2--0.5 kg | 0.5U | Moderate effectiveness; depends on orbital inclination | 6--7 |

*[Source: Cranfield Icarus drag sail, 0.1 kg; NanoSail-D2, NASA; InflateSail, SSC]*

### Propulsion System Comparison Table

| Parameter | Cold Gas (N$_2$) | Warm Gas (Butane) | Green Monoprop (AF-M315E) | Electrospray (FEEP) | Hall Effect (Xe) |
|-----------|-----------------|------------------|--------------------------|--------------------|--------------------|
| $I_{sp}$ (s) | 40--75 | 80--100 | 230--250 | 500--5000 | 800--3000 |
| Thrust | 10--100 mN | 5--50 mN | 0.1--1 N | 0.01--1 mN | 1--50 mN |
| Propellant mass (100 m/s, 5 kg S/C) | 0.87 kg | 0.44 kg | 0.18 kg | 0.042 kg | 0.055 kg |
| System dry mass | 0.3 kg | 0.5 kg | 3.0 kg | 0.9 kg | 1.5 kg |
| **Total system mass** | **1.17 kg** | **0.94 kg** | **3.18 kg** | **0.94 kg** | **1.55 kg** |
| Burn time (100 m/s) | Minutes | Minutes | Seconds | **Months** | Days--weeks |
| Power during firing | < 1 W (valve) | 5--15 W | 2--10 W (preheat) | 20--60 W | 50--300 W |
| Complexity | Low | Low-medium | High | Medium | High |
| Cost | ~15 kEUR | ~30 kEUR | ~120 kEUR | ~50 kEUR | ~80 kEUR |
| TRL | 9 | 7--8 | 7--8 | 7--8 | 6--8 (CubeSat) |

> **Worked Example -- Propellant Mass Comparison for 100 m/s Deorbit**
>
> **Scenario:** 3U CubeSat, $m_{\text{dry}} = 5.0$ kg, deorbit from 600 km ($\Delta V = 113$ m/s).
>
> **Cold gas** ($I_{sp} = 60$ s, $v_e = 589$ m/s):
> $m_{\text{prop}} = 5.0 \times (e^{113/589} - 1) = 5.0 \times (e^{0.192} - 1) = 5.0 \times 0.212 =$ **1.06 kg**
>
> Total system: 1.06 + 0.3 = 1.36 kg = **23% of 6 kg CubeSat mass limit**
>
> **Green monopropellant** ($I_{sp} = 235$ s, $v_e = 2305$ m/s):
> $m_{\text{prop}} = 5.0 \times (e^{113/2305} - 1) = 5.0 \times (e^{0.0490} - 1) = 5.0 \times 0.0502 =$ **0.251 kg**
>
> Total system: 0.251 + 3.0 = 3.25 kg = **54% of mass limit** (system is heavy even though propellant is light)
>
> **Electrospray (FEEP)** ($I_{sp} = 1200$ s, $v_e = 11,772$ m/s):
> $m_{\text{prop}} = 5.0 \times (e^{113/11772} - 1) = 5.0 \times (e^{0.00960} - 1) = 5.0 \times 0.00965 =$ **0.048 kg**
>
> Total system: 0.048 + 0.9 = 0.95 kg = **16% of mass limit** (lightest total, but takes months to execute)
>
> **Trade-off summary:** The electrospray system is the lightest overall because the high $I_{sp}$ minimises propellant mass, and the dry mass is moderate. Cold gas uses the most propellant but has the lowest dry mass. Green monopropellant is dominated by its heavy feed system. **The optimal choice depends on the mission timeline:** if deorbit must happen quickly (days), cold gas or monoprop; if months are acceptable, electric propulsion wins on mass.

---

## 3. On-Board Data Handling (20 min)

### Teaching Notes

### OBC Architecture -- Processor Selection

The OBC is the spacecraft's brain, managing all data handling, commanding, telemetry generation, and FDIR (Fault Detection, Isolation, and Recovery). Processor selection involves a fundamental trade between radiation tolerance, processing power, power consumption, and cost.

#### Flight-Heritage Processors

| Processor | Architecture | Clock (MHz) | RAM | Rad Tolerance | Power (W) | TRL (Space) | Cost | Typical Use |
|-----------|-------------|-------------|-----|---------------|-----------|------------|------|------------|
| **TI MSP430** | 16-bit RISC | 16--25 | 2--10 kB | Moderate (COTS, tested to 30 krad) | 0.005--0.01 | 9 | < 10 EUR | Ultra-low-power housekeeping, safe mode OBC |
| **ARM Cortex-M4** (STM32F4) | 32-bit ARM | 168 | 192 kB + ext | Low-moderate (COTS, 10--30 krad) | 0.05--0.20 | 8--9 | 10--20 EUR | **Standard CubeSat OBC**, TM/TC handling, ADCS control loop |
| **ARM Cortex-M7** (STM32H7) | 32-bit ARM | 400--480 | 1 MB + ext | Low-moderate (COTS, 10--20 krad) | 0.1--0.5 | 7--8 | 15--30 EUR | Higher-performance CubeSat OBC, onboard image processing |
| **ARM Cortex-A** (Linux-capable, e.g., NXP i.MX6) | 32/64-bit ARM | 500--1200 | 256 MB--1 GB DDR | Low (COTS, < 10 krad) | 1--3 | 6--7 | 20--50 EUR | Payload processing, AI/ML inference, Linux OS |
| **Xilinx Zynq** (SoC: ARM + FPGA) | ARM Cortex-A9 + Artix-7 FPGA | 667 + programmable | 512 MB + FPGA fabric | Moderate (Zynq-7000) to High (Kintex radhard) | 2--5 | 7--8 | 100--500 EUR | High-throughput data processing, SDR (software-defined radio), image compression |
| **LEON3/4** (rad-hard SPARC) | 32-bit SPARC | 50--250 | External | High (100--300 krad, SEL immune) | 1--3 | 9 | 10K--50K EUR | ESA heritage missions, GEO, deep space |
| **RAD750** (BAE Systems) | 32-bit PowerPC | 200 | 128 MB | Very high (1 Mrad, SEL immune) | 5--10 | 9 | 200K+ EUR | NASA flagship missions (MRO, Curiosity, JWST) |

*[Source: ST Microelectronics STM32 datasheets; Xilinx Zynq-7000 datasheet; Cobham Gaisler LEON3 datasheet]*

#### RTOS vs Bare-Metal vs Linux

| Approach | OS | Pros | Cons | When to Use |
|----------|-----|------|------|------------|
| **Bare-metal** | None (custom event loop) | Minimum overhead, deterministic timing, smallest code size | Hard to maintain, no task isolation, no file system | Ultra-simple 1U missions (MSP430) |
| **RTOS** (FreeRTOS, ChibiOS, Zephyr) | Real-time OS | Deterministic scheduling, task isolation, mature ecosystem, small footprint (10--50 kB) | More complex than bare-metal; requires task priority design | **Standard for CubeSat C&DH**: ADCS loop, TM/TC, mode management |
| **Linux** (Yocto, Buildroot) | Full OS | Rich ecosystem (Python, networking, file system, device drivers), easy development | Non-deterministic (not suitable for hard real-time), large footprint (50+ MB), power-hungry processor | Payload data processing, AI/ML, onboard image analysis |

**Radiation effects on processors:**

The space radiation environment causes two categories of effects:

1. **Total Ionising Dose (TID):** Accumulated radiation damage from trapped protons/electrons and solar particles. Measured in rad(Si) or gray. Causes threshold voltage shifts in CMOS transistors, increasing leakage current and eventually causing functional failure.
   - LEO (500 km, 51.6 deg): ~1--5 krad/year behind 2 mm Al shielding
   - LEO polar/SSO (800 km): ~5--10 krad/year
   - MEO (through proton belt): ~50--100 krad/year
   - GEO: ~10--30 krad/year

2. **Single Event Effects (SEE):** A single energetic particle (proton or heavy ion) deposits enough charge in a transistor to flip a bit (SEU -- Single Event Upset), latch a transistor (SEL -- Single Event Latchup, potentially destructive), or burn out a power device (SEB -- Single Event Burnout).
   - **SEU rate in LEO:** ~1--10 bit flips per day per GB of SRAM (highly variable with orbit and shielding)
   - **SEL mitigation:** Current-limiting resistors on power lines, latchup detection circuits, watchdog resets
   - **SEU mitigation:** Error Detection and Correction (EDAC) on memory (Hamming codes, TMR -- Triple Modular Redundancy)

**CubeSat approach to radiation:** Most CubeSats in LEO (< 600 km, < 3-year mission) use COTS processors with EDAC on memory and a watchdog timer. Total dose over a 3-year LEO mission is typically 3--15 krad, which most COTS ARM Cortex-M processors survive (tested and characterised, even if not guaranteed). For longer missions, higher orbits, or critical applications, rad-tolerant or rad-hard processors are needed.

### Data Storage Sizing

> **Key Equations -- Data Storage**
>
> $$S_{\text{required}} = V_{\text{daily}} \times N_{\text{days}} \times f_{\text{safety}}$$
>
> where $V_{\text{daily}}$ = daily data generation, $N_{\text{days}}$ = days between full downlinks (typically 1--3 for LEO), $f_{\text{safety}} = 2$ (to handle missed passes, ground station outages, and safe mode periods).
>
> **Storage technologies:**
>
> | Technology | Capacity | Write Speed | Radiation Tolerance | Power | CubeSat Use |
> |-----------|----------|------------|---------------------|-------|------------|
> | NOR flash | 4--256 MB | 1--5 MB/s | Moderate (10--50 krad) | Low | Code storage, boot ROM, critical parameters |
> | NAND flash (SLC) | 1--128 GB | 10--50 MB/s | Low-moderate (5--20 krad) | Low | **Primary data storage** |
> | NAND flash (MLC/TLC) | 32--512 GB | 50--200 MB/s | Low (< 10 krad) | Low | Maximum capacity (use EDAC and scrubbing) |
> | SD card (industrial) | 4--128 GB | 10--50 MB/s | Low (< 5 krad) | Very low | Budget missions (risk: wear levelling + radiation = data loss) |
> | MRAM | 1--64 MB | 10--50 MB/s | High (> 100 krad) | Very low | Critical parameters, non-volatile log |

> **Worked Example -- Storage for 3U EO CubeSat**
>
> **Given:** Daily generation = 720 MB (from Session 3.3 data budget), daily downlink = 480 MB, days to clear backlog = $720/480 = 1.5$ days.
>
> $S_{\text{required}} = 720 \times 3 \times 2 = 4320$ MB $\approx$ **4.3 GB**
>
> **Specify:** >= 8 GB NAND flash storage (next standard size). The GomSpace A3200 OBC includes 4 GB NAND flash; adding an 8 GB SD card or additional NAND chip provides adequate capacity.
>
> For a high-resolution imager generating 4.5 GB/day, storage requirement is: $4500 \times 3 \times 2 = 27$ GB. Specify >= 32 GB flash storage.

### Flight Software Functions

| Function | Description | Typical Execution Rate | Criticality |
|----------|------------|----------------------|-------------|
| **Mode management** | Transition between Safe, Idle, Imaging, Downlink, Eclipse modes based on state machine | Event-driven | **Critical** (incorrect transition = mission loss) |
| **ADCS control loop** | Read sensors (star tracker, gyro, magnetometer), compute attitude estimate (Kalman filter), command actuators (PID controller) | 1--10 Hz | **Critical** (loss of pointing = loss of mission) |
| **TM/TC handling** | Generate CCSDS telemetry packets, parse and execute telecommands | 1 Hz (TM), event-driven (TC) | **Critical** (loss of communication = loss of mission) |
| **Data handling** | Payload data acquisition, compression (JPEG2000, CCSDS 122.0), buffering, downlink queue management | On-demand | Important |
| **FDIR** | Fault Detection, Isolation, and Recovery: watchdog timer, over-current protection, sensor consistency checks, autonomous safe mode trigger | 1--10 Hz | **Critical** (must detect and recover from faults autonomously) |
| **Housekeeping** | Monitor temperatures, voltages, currents, wheel speeds; log to non-volatile memory | 0.1--1 Hz | Important |
| **Scheduling** | Time-tagged command execution: autonomous imaging over target, downlink preparation before ground pass, desat scheduling | 1 Hz | Important |
| **Thermal control** | Read temperature sensors, control heaters (on/off thermostat or PID) | 0.1 Hz | Moderate (for heater-equipped missions) |

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
   - Is the component qualified for the launch vibration environment?
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

| Budget | Common Fix | Impact | Typical Mass/Power/Cost Trade |
|--------|-----------|--------|------------------------------|
| **Mass** (negative) | Remove propulsion; select lighter components; reduce redundancy; move to larger form factor | Risk / performance trade | Removing propulsion saves 0.5--1.5 kg |
| **Power** (negative) | Add deployable SA; reduce payload duty cycle; select lower-power AOCS; schedule operations to avoid simultaneous loads | Cost / schedule trade | Deployable panel adds ~15 W but costs 0.3 kg + 25 kEUR |
| **Link** (negative) | Increase TX power; use higher-gain antenna; reduce data rate; upgrade coding; upgrade ground station | Mass / power trade | 3 dB gain from coding is "free"; 3 dB from bigger antenna costs mass |
| **Cost** (over ceiling) | Use COTS instead of rad-hard; remove propulsion; reduce ground segment; use SatNOGS instead of commercial ground | Risk / capability trade | COTS vs rad-hard saves 10--100x on processor cost |
| **Pointing** (insufficient) | Upgrade star tracker; improve alignment calibration; add vibration isolation for RW; reduce thermal gradients | Cost / complexity trade | Alignment improvement is usually cheapest |

---

### 1U Worked Example: UniSat-1

**CDS Compliance for 1U Form Factor**

The CubeSat Design Specification (CDS Rev 14) defines the 1U envelope:

| Parameter | 1U Specification | UniSat-1 Design | Compliance |
|-----------|-----------------|-----------------|------------|
| Dimensions | 100.0 x 100.0 x 113.5 mm | 100.0 x 100.0 x 113.5 mm (ISIS 1U frame) | **Pass** |
| Maximum mass | 2.0 kg (CDS Rev 14, ISIPOD) | 1.0 kg target (50% margin to 2 kg limit) | **Pass** |
| Rail material | Hard anodised Al 7075-T6 | Standard (part of ISIS frame, 7075-T6, Type III anodise) | **Pass** |
| Rail cross-section | 8.5 x 8.5 mm minimum | Standard (ISIS: 8.5 x 8.5 mm) | **Pass** |
| Deployment switches | Min 1 per accessible face | 2 switches (ISIS standard, on +X/-X rail faces) | **Pass** |
| RBF pin | Required | Included (ISIS standard, on -Z face) | **Pass** |
| CG offset | <= 2 cm from geometric centre | < 1 cm (symmetric PCB stack layout, battery centred) | **Pass** |
| Protrusions | None beyond rail envelope (stowed) | UHF monopole antenna stowed along rail (spring-loaded, within envelope) | **Pass** |
| Fundamental frequency | > 40 Hz first mode | ~600 Hz (1U Al structure is extremely stiff) | **Pass** |

**Note on CDS mass limit:** The CDS Rev 14 specifies 2.0 kg as the 1U deployer limit for the ISIPOD. However, many deployer providers (e.g., NanoRacks, Exolaunch) specify 1.33 kg for 1U. Always check the specific deployer ICD. UniSat-1 targets 1.0 kg, well within either limit.

**No propulsion:** At 400 km altitude, atmospheric drag provides natural deorbit. The ballistic coefficient for a 1U is:

$BC = \frac{m}{C_D \times A} = \frac{1.0}{2.2 \times 0.01} = 45.5$ kg/m$^2$

This gives an orbital lifetime of approximately 8--14 months depending on solar activity (F10.7 index). At solar maximum (F10.7 > 200), the denser atmosphere deorbits the satellite in ~6 months. At solar minimum (F10.7 ~ 70), lifetime extends to ~18 months. Both are within the FCC 5-year rule and IADC 25-year guideline without any propulsion system.

**OBC selection rationale:** UniSat-1 uses a custom board based on the TI MSP430 (safe mode / housekeeping) + STM32F4 Cortex-M4 (main OBC). The MSP430 runs bare-metal firmware handling the watchdog, power monitoring, and safe-mode recovery. The STM32F4 runs FreeRTOS handling TM/TC, magnetometer data acquisition, and scheduling. Dual-processor architecture provides redundancy: if the STM32F4 fails (SEU, latchup), the MSP430 can maintain safe-mode operations and respond to ground commands.

**Data storage:** With 0.84 MB/day of magnetometer data and 4800 bps downlink, onboard storage is not a bottleneck. A 4 MB NOR flash is more than adequate (stores ~4 days of data as buffer). No NAND flash, no SD card needed.

**Complete 1U Equipment List:**

> | # | Category | Component | Mass (g) | Power (W) | Cost (kEUR) | Qty | Interface |
> |---|----------|-----------|----------|----------|-------------|-----|-----------|
> | 1 | Structure | ISIS 1U CubeSat structure (Al 7075-T6) | 200 | -- | 4.0 | 1 | Mechanical |
> | 2 | EPS | GomSpace NanoPower P31us (EPS board + 2S Li-ion battery, 10 Wh) | 200 | 0.3 (quiescent) | 12.0 | 1 | I$^2$C |
> | 3 | Solar cells | Body-mounted triple-junction GaAs cells (5 faces) | 50 | -- (generates power) | 8.0 | 5 | Direct to EPS |
> | 4 | OBC | Custom MSP430 + STM32F4 board (with 4 MB NOR flash) | 30 | 0.3 | 3.0 | 1 | I$^2$C, SPI, UART |
> | 5 | Comms | UHF transceiver (NanoCom AX100, 0.5 W TX, 9600 bps) | 60 | 0.5 (TX) / 0.1 (RX) | 8.0 | 1 | SPI |
> | 6 | Antenna | UHF monopole (deployable, $\lambda/4 = 17$ cm nitinol) | 20 | -- | 2.0 | 1 | RF coax |
> | 7 | Payload | MEMS magnetometer (custom PCB, PNI RM3100 sensor) | 50 | 0.2 | 5.0 | 1 | SPI |
> | 8 | AOCS (passive) | Permanent magnet (AlNiCo, 0.5 A m$^2$) + 2 hysteresis rods (HyMu-80) | 30 | 0 | 1.0 | 1 | None (passive) |
> | 9 | Harness | Internal cables, connectors, PC/104 stack header | 50 | -- | 1.0 | 1 | Various |
> | | **TOTAL** | | **690** | **~1.3 (peak TX)** | **~44** | | |
>
> **Mass budget:**
>
> | Level | Mass (g) |
> |-------|----------|
> | CBE (Current Best Estimate) | 690 |
> | + 20% equipment margin | 828 |
> | + 20% system margin | 994 |
> | **MEV (Maximum Expected Value)** | **994** |
> | Deployer limit (ISIPOD) | 2000 |
> | **Margin to limit** | **1006 g (50%)** |
>
> **Power budget (worst case: TX mode in sunlight):**
>
> | Load | Power (W) |
> |------|----------|
> | OBC (STM32F4 + MSP430) | 0.3 |
> | EPS quiescent | 0.3 |
> | UHF TX | 0.5 |
> | Magnetometer | 0.2 |
> | **Total peak** | **1.3** |
> | SA available (orbit avg, EOL) | 2.3 |
> | **Margin** | **1.0 W (43%)** |
>
> **Key insight:** The entire UniSat-1 BOM is 5 COTS components plus 2 custom boards (OBC and magnetometer PCB). Total hardware cost is ~44 kEUR -- an order of magnitude less than a typical 3U mission. With labour, I&T, launch, and operations, the total mission cost is 80--150 kEUR. This demonstrates that a useful space mission can be built for less than the cost of a mid-range car.

---

## Worked Example: Complete 3U EO CubeSat Equipment List

> | Category | Component | Mass (kg) | Power (W) | Cost (kEUR) | Qty | Interface |
> |----------|-----------|----------|----------|-------------|-----|-----------|
> | EPS Board | GomSpace P31u (MPPT, 3.3V/5V/batt rails) | 0.10 | 0.5 | 8 | 1 | I$^2$C |
> | Battery | GomSpace BP4 (2S2P, 38 Wh, Li-ion 18650) | 0.20 | -- | 5 | 1 | I$^2$C (telemetry) |
> | Solar Panels | MMA HaWK deployable (TJ GaAs, ~12 W/panel BOL) | 0.45 | -- | 25 | 2 | Direct to EPS |
> | OBC | GomSpace A3200 (ARM Cortex-A, Linux, 4 GB NAND) | 0.08 | 1.0 | 12 | 1 | I$^2$C, SPI, UART |
> | Reaction Wheel | Blue Canyon RW210 (1 mN m torque, 10 mN m s momentum) | 0.055 | 0.6 | 8 | 4 | SPI |
> | Magnetorquer | CubeSpace CubeMAG (0.2 A m$^2$ dipole) | 0.03 | 0.1 | 3 | 3 | I$^2$C |
> | Star Tracker | Blue Canyon NST (10 arcsec accuracy, 2 Hz update) | 0.35 | 1.5 | 35 | 1 | SPI/UART |
> | Sun Sensor | NewSpace NFSS-411 (0.5 deg accuracy, fine analog) | 0.005 | 0.01 | 1 | 6 | Analog/I$^2$C |
> | Transponder | Endurosat S-band TX/RX (2 W, QPSK+LDPC, 1--5 Mbps) | 0.10 | 6.0 (TX) | 15 | 1 | SPI |
> | Antenna | Endurosat S-band patch (6 dBi, RHCP) | 0.02 | -- | 3 | 1 | RF coax |
> | Payload | Custom telescope (multispectral, 5 m GSD) | 1.50 | 5.0 | 150 | 1 | LVDS/SPI |
> | Structure | ISIS 3U frame (Al 7075-T6, hard anodised) | 0.30 | -- | 8 | 1 | Mechanical |
> | Harness | Custom cables, connectors, PC/104 stack | 0.15 | -- | 5 | 1 | Various |
> | **TOTAL** | | **3.57** | **~10 (imaging mode)** | **~290** | | |
>
> **Parametric estimate from Session 2.4:** 3.68 kg CBE. **Equipment total:** 3.57 kg. Difference: -3% (within expected accuracy of parametric models).
>
> **Mass budget:**
> - CBE: 3.57 kg
> - + 20% equipment margin: 4.28 kg
> - + 20% system margin: 5.14 kg (MEV)
> - CDS limit: 6.0 kg
> - **Margin to limit: 0.86 kg (14%)** -- amber, acceptable for Phase A but tight for Phase B+.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| CDS compliance | Standard dimensions, Al 7075-T6 anodised rails (8.5 mm), deployment switches, RBF pin, CG limits |
| Structural materials | Al 7075-T6: $\sigma_y = 503$ MPa, $E = 72$ GPa; anodisation for wear/insulation; CFRP not suitable for rails |
| Launch loads | 6--12 g axial QS, 7 grms random vib (20--2000 Hz), 500--2000 g shock; PCB solder joints are the weak point |
| Structural MoS | $\text{MoS} = \sigma_{\text{allow}}/(\sigma_{\text{design}} \times \text{FoS}) - 1 \geq 0$; FoS 1.25 yield / 1.5 ultimate (metallic) |
| Frequency req | First mode > 40 Hz; CubeSat Al structures easily exceed this; local modes (PCBs, deployables) are the risk |
| Tsiolkovsky equation | $m_{\text{prop}} = m_{\text{dry}} \times (e^{\Delta V/(I_{sp} g_0)} - 1)$; exponential growth with $\Delta V / v_e$ |
| Cold gas | $I_{sp}$ 40--75 s; simple, fast, reliable; heavy propellant penalty for $\Delta V > 30$ m/s |
| Green monoprop | $I_{sp}$ 225--250 s; high thrust (0.1--1 N); heavy feed system; AF-M315E and LMP-103S flight-proven |
| Electrospray (FEEP) | $I_{sp}$ 500--5000 s; minimal propellant; months-long burns; 20--60 W power; indium or ionic liquid |
| Hall thruster | $I_{sp}$ 800--3000 s; moderate thrust (1--50 mN); 50--300 W; iodine emerging as Xe alternative |
| Propulsion trades | High-$I_{sp}$: less propellant, more dry mass, long burns; Low-$I_{sp}$: more propellant, lighter system, fast burns |
| When to skip propulsion | Below 500 km (natural deorbit); tech demo; differential drag constellation |
| OBC processors | MSP430 (0.01 W, safe mode), Cortex-M4 (0.2 W, standard CubeSat), Zynq (3 W, high-throughput), LEON3 (rad-hard, ESA) |
| RTOS vs Linux | FreeRTOS for real-time C&DH (standard); Linux for payload processing (data-intensive) |
| Radiation effects | TID: 1--10 krad/yr LEO; SEU: 1--10 bit flips/day/GB; mitigate with EDAC, watchdog, redundancy |
| Data storage | $S \geq 2\times$ daily generation; SLC NAND flash for primary storage; NOR flash for code/critical params |
| Equipment selection | Live budget tracking; RF compatibility check; interface compatibility; trade study for contested selections |
| Budget closure | All margins must be positive before proceeding to integration week; mass margin > 10% at Phase A |
