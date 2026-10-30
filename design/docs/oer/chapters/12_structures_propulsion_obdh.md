# Chapter 12 — Structures, Propulsion and On-Board Data Handling

> **Recommended background.** Cal Poly, *CubeSat Design Specification* Rev 14.1; SMAD4 Ch. 11.3 (Structures) and Ch. 17 (Propulsion); ECSS-E-ST-32C (Structural general requirements) and ECSS-E-ST-35C (Propulsion general requirements); Sutton & Biblarz, *Rocket Propulsion Elements*, Ch. 2–4; Sarafin, *Spacecraft Structures and Mechanisms*, Ch. 1–3. This chapter closes the subsystem-design sequence: it uses the deorbit ΔV of Chapter 7 §7.5, the mass budget and margin schedule of Chapter 8 §8.4 (Table 8.3), the power budget of Chapter 9 and the data budget of Chapter 11 §11.9. The Tsiolkovsky equation and the structural margin of safety are derived in Part V §V.3 and V.13.

## Learning objectives

By the end of this chapter, you will be able to:

1. Verify CubeSat Design Specification (CDS) compliance for 1U–12U form factors
2. Explain the structural load environment (quasi-static, vibration, shock) and its physical origins
3. Compute the structural margin of safety for quasi-static launch loads
4. Estimate the fundamental-frequency requirement and verify it against deployer specifications
5. Apply the Tsiolkovsky rocket equation to compute propellant mass for a given $\Delta V$
6. Explain the physics of each propulsion technology and select one based on mission requirements
7. Select an on-board computer architecture based on processing, radiation and interface requirements
8. Size on-board data storage from the data budget
9. Assemble an equipment list from the subsystem designs and check that every engineering budget closes

Vendor products named in this chapter are representative examples, not endorsements; prices are indicative (2026).

---

## 12.1 CubeSat structure and CDS compliance

*[Source: Cal Poly CDS Rev 14.1, February 2022; ECSS-E-ST-32C]*

### 12.1.1 CDS dimensional specifications

| Form factor | Dimensions (mm) | Max mass (kg) | Internal volume (cm$^3$) | Typical deployer |
|------------|-----------------|---------------|------------------------|-----------------|
| 1U | 100 × 100 × 113.5 | 2.0 | ~1000 | ISIPOD, P-POD |
| 1.5U | 100 × 100 × 170.2 | 3.0 | ~1500 | ISIPOD |
| 2U | 100 × 100 × 227.0 | 4.0 | ~2000 | ISIPOD, P-POD |
| 3U | 100 × 100 × 340.5 | 6.0 | ~3000 | P-POD, ISIPOD, NanoRacks NRCSD |
| 6U | 100 × 226.3 × 366.0 | 12.0 | ~6000 | 6U deployer (Exolaunch, D-Orbit) |
| 12U | 226.3 × 226.3 × 366.0 | 24.0 | ~12000 | 12U deployer (Exolaunch) |

Figure 12.1 draws the 3U envelope to scale with the features the deployer interface depends on: the rails, their contact pads, the deployment switches, the remove-before-flight pin access, the protrusion allowance between the rails and the centre-of-gravity limit.

![3U CubeSat envelope per CDS Rev 14 in side and end views, with rails, contact pads, deployment switches, RBF pin access, protrusion envelope and CG box.](../assets/figures/fig_cds_envelope.png)

**Figure 12.1** — The 3U CubeSat envelope of the CubeSat Design Specification Rev 14, drawn to scale (dimensions in mm). Left, side view: the 100 × 100 × 340.5 mm body with its four hard-anodised rails, the rail-end contact pads that bear on the deployer, the two deployment switches on the −Z rail ends, the remove-before-flight pin access and the centre-of-gravity limit of 2 cm about the geometric centre. Right, end view: the 8.5 × 8.5 mm rail cross-sections and the 6.5 mm protrusion envelope permitted on the ±X and ±Y faces between the rails in the stowed configuration.

### 12.1.2 Structural materials

**CubeSat rail material: aluminium 7075-T6**

This is the most commonly specified structural aluminium alloy for CubeSat rails. The CDS mandates hard-anodised aluminium for the rails (the four load-bearing edges that slide along the deployer guide channels).

| Property | Al 7075-T6 | Al 6061-T6 | Ti-6Al-4V | CFRP (quasi-isotropic) |
|----------|-----------|-----------|-----------|----------------------|
| Density (kg/m$^3$) | 2810 | 2700 | 4430 | 1600 |
| Yield strength $\sigma_y$ (MPa) | 503 | 276 | 880 | N/A (use ultimate) |
| Ultimate strength $\sigma_u$ (MPa) | 572 | 310 | 950 | 500–800 |
| Young's modulus $E$ (GPa) | 71.7 | 68.9 | 114 | 70–150 (direction-dependent) |
| CTE (ppm/°C) | 23.6 | 23.1 | 8.6 | 0–2 (tuneable) |
| Thermal conductivity (W/m/K) | 130 | 167 | 6.7 | 3–10 |

*[Source: MMPDS / ASM Handbook; Hexcel HexPly datasheets]*

**Why Al 7075-T6 for rails:**
- High strength-to-weight ratio (superior to 6061-T6)
- Hard anodisation provides a durable, low-friction surface finish for deployer guide-channel contact (reduces galling, provides electrical insulation)
- Good machinability
- Extensive flight heritage (virtually every CubeSat ever launched)
- CTE-matched to the Al deployer structure (prevents differential thermal expansion binding)

**Why not other materials for rails:**
- **Titanium:** excellent strength but poor thermal conductivity (thermal hot spots), difficult to machine, risk of galling against the aluminium deployer
- **CFRP:** cannot be anodised; CTE mismatch with the Al deployer causes binding at temperature extremes; poor electrical conductivity (grounding/bonding issues)
- **Stainless steel:** too heavy; poor CTE match

**Anodisation physics:** Anodisation is an electrochemical process that grows a hard aluminium oxide ($\text{Al}_2\text{O}_3$) layer on the surface. Hard anodisation (Type III) produces a 25–75 µm thick oxide layer with hardness of 60–70 HRC (harder than most steel). This layer provides wear resistance against deployer contact, electrical insulation (prevents arcing between satellite and deployer), corrosion resistance, and controlled surface optical properties ($\alpha_s \approx 0.3$–$0.5$, $\varepsilon \approx 0.8$–$0.85$ for clear anodise; $\alpha_s \approx 0.9$, $\varepsilon \approx 0.85$ for black anodise — see Chapter 9 §9.4).

### 12.1.3 Key CDS requirements

| Requirement | Specification | Physical rationale |
|------------|---------------|-------------------|
| Rail material | Hard-anodised aluminium (7075-T6 or 6061-T6) | Wear resistance, CTE match to deployer, electrical isolation |
| Rail cross-section | 8.5 × 8.5 mm minimum contact area | Adequate bearing area for launch loads; prevents rail yielding under quasi-static acceleration |
| Surface finish | All external surfaces anodised or non-outgassing coating | Prevent contamination of other payloads on the launch vehicle (molecular outgassing deposits on optics) |
| Deployment switches | Minimum 1 on each accessible rail face (+X, −X) | Inhibit all spacecraft activity until fully deployed from the deployer (prevents inadvertent deployment, RF emissions in the fairing) |
| Remove-before-flight (RBF) pin | Required; physically disables all power systems | Final safety inhibit; removed at the launch pad after integration; ensures zero RF emissions and zero deployment-actuator current until intentional removal |
| Protrusions | None beyond the rail envelope in stowed configuration | Ensures clean ejection from the deployer; prevents snagging on guide rails or an adjacent CubeSat |
| Centre of gravity | Within 2 cm of the geometric centre (per deployer ICD) | Prevents wobble during deployment ejection; ensures all CubeSats eject with similar tip-off rates |
| Fundamental frequency | > 40 Hz first mode (typical deployer requirement) | Prevents dynamic coupling between satellite and launch-vehicle structural modes (which cluster at 10–30 Hz) |

### 12.1.4 PC/104 stack architecture

Most CubeSat avionics use the PC/104-compatible stack architecture, a heritage from the industrial embedded-computing standard adapted for space:

**Physical specifications:**
- **Board size:** 96 × 90 mm (standard) or 90 × 96 mm
- **Connector:** 104-pin stack-through header (2 × 52 pins, 2.54 mm pitch) — the original PC/104 pinout carries power + I²C + SPI + UART + GPIO
- **Stack spacing:** typically 10–15 mm between boards (constrained by component height and connector mating height)
- **Stack capacity:** 1U accommodates ~4 boards; 3U accommodates ~12 boards (340 mm / ~28 mm per board slot)

**What rides on the stack:**
- EPS board (battery management, MPPT, power distribution)
- OBC board (processor, memory, interfaces)
- Communications board (UHF radio, or S-band transponder)
- AOCS board (if integrated — some vendors combine IMU + magnetorquer driver + reaction-wheel interface on one PCB)
- Payload interface board (ADC, sensor interfaces)

**Mechanical concerns:**
- Solder joints are the weakest point; random vibration causes fatigue cracking at heavy component leads (especially tall electrolytic capacitors, large connectors and crystal oscillators)
- Board-to-board connectors must be properly preloaded (too loose = intermittent contact; too tight = difficult assembly/disassembly during integration and test)
- Standoffs and spacers must be correctly torqued; a low-strength threadlocker (e.g. Loctite 222) is standard

### 12.1.5 Launch load environment

The launch environment subjects the satellite to loads from engine thrust, aerodynamic buffeting, stage separation and pyrotechnic events. The satellite must survive all of these without structural failure or functional degradation. The test programme that demonstrates this is described in Chapter 14 §14.3.

| Load type | Physical source | Typical level | Duration | Frequency range | Verification method |
|-----------|----------------|--------------|----------|----------------|---------------------|
| **Quasi-static acceleration** | Engine thrust + aero-loading | 6–12 g axial, 2–4 g lateral | Seconds to minutes | 0 (static equivalent) | Analysis + sine vibration test |
| **Sine vibration** | Low-frequency vehicle dynamics | 0.5–3 g (5–100 Hz) | Minutes | 5–100 Hz | Sine sweep test (3 axes) |
| **Random vibration** | Acoustic noise + turbulent boundary layer | 5–15 g$_{\text{rms}}$ (20–2000 Hz) | 60–120 s per axis | 20–2000 Hz | Random vibration test (3 axes) |
| **Shock** | Pyrotechnic separation events (stage separation, fairing separation, deployer spring release) | 500–2000 g at separation (high frequency) | < 10 ms | 100–10 000 Hz | Shock response spectrum (SRS) test |
| **Acoustic** | Sound pressure from engine exhaust, aerodynamic noise | 120–140 dB (20–10 000 Hz) | Minutes | 20–10 000 Hz | Usually covered by random vibration for CubeSats |

*[Source: ECSS-E-ST-10-03C; NASA GEVS (GSFC-STD-7000B); Falcon 9 Payload User's Guide; PSLV User's Guide]*

**Random vibration PSD profile (typical CubeSat deployer level):**

| Frequency (Hz) | ASD level (g$^2$/Hz) | Notes |
|----------------|---------------------|-------|
| 20 | 0.01 | Low-frequency start (ramp up) |
| 50 | 0.04 | Ramp up at +6 dB/octave |
| 100 | 0.04 | Flat region start |
| 800 | 0.04 | Flat region end |
| 2000 | 0.01 | Roll-off at −6 dB/octave |
| **Overall** | **~7 g$_{\text{rms}}$** | Typical for CubeSat deployer qualification level |

The flat region at 0.04 g$^2$/Hz from 100–800 Hz is where most structural damage occurs, because this is where PCB resonances and solder-joint fatigue are excited.

**What fails during vibration testing:**
1. **Solder joints:** heavy components (connectors, tall capacitors, transformers) with long lever arms crack at their solder joints. Mitigation: use surface-mount components, stake tall components with adhesive, use conformal coating.
2. **Deployable mechanisms:** antenna hinges, solar-panel hold-down mechanisms and deployment springs can fail if not properly constrained. Mitigation: adequate preload on hold-down mechanisms, shock testing of release devices.
3. **Optical components:** lenses and mirrors can shift or crack if not properly mounted with strain relief. Mitigation: RTV potting, flexure mounts.
4. **Wire harness:** chafing against structure edges. Mitigation: edge radii > 1 mm, harness tie-downs every 50 mm, protective sleeving.

### 12.1.6 Structural margin of safety

This is the book's canonical statement of the margin of safety; Chapter 3 §3.3.3 introduced it as an example of ECSS depth, and Part V §V.13 derives the factor-of-safety logic.

> **Key equations — structural margin of safety**
>
> $$\text{MoS} = \frac{\sigma_{\text{allowable}}}{\sigma_{\text{design}} \times \text{FoS}} - 1$$
>
> where:
> - $\sigma_{\text{allowable}}$ = material yield or ultimate strength (MPa)
> - $\sigma_{\text{design}}$ = computed stress under design loads (MPa)
> - FoS = factor of safety
>
> **Requirement:** MoS ≥ 0 for all load cases.
>
> **Factors of safety (ECSS-E-ST-32C / ECSS-E-ST-32-10C):**
>
> | Material / joint | Yield FoS | Ultimate FoS | Rationale |
> |-----------------|----------|-------------|-----------|
> | Metallic (Al 7075-T6) | 1.25 | 1.5 | Standard structural metals |
> | Composite (CFRP) | 1.5 | 2.0 | Higher variability in laminate properties |
> | Bonded joints | 1.5 | 2.0 | Bond strength is highly process-dependent |
> | Pressurised systems | 1.5 | 2.0 | Burst hazard to other payloads |
> | Mechanisms (single-use) | — | 2.0 | Must work first time; no test opportunity |
>
> **Design loads:** The design load includes the quasi-static acceleration (from the launch-vehicle user guide), multiplied by a dynamic amplification factor ($DAF \approx 1.25$–$1.5$) if the satellite's natural frequency is near any launch-vehicle forcing frequency.

> **Worked example — axial load on a 3U CubeSat rail (SuperDove-class)**
>
> **Given:** 3U CubeSat, mass = 5 kg, axial launch load = 9 g (Falcon 9 typical), 4 rails (load shared equally), rail cross-section = 8.5 × 8.5 mm, material = Al 7075-T6 ($\sigma_y = 503$ MPa, $\sigma_u = 572$ MPa).
>
> **Step 1 — Design load per rail:**
> $F = \dfrac{m \times n \times g_0}{4} = \dfrac{5 \times 9 \times 9.80665}{4} = \dfrac{441.3}{4} = 110.3$ N
>
> **Step 2 — Compressive stress:**
> $\sigma = \dfrac{F}{A_{\text{rail}}} = \dfrac{110.3}{8.5 \times 10^{-3} \times 8.5 \times 10^{-3}} = \dfrac{110.3}{7.225 \times 10^{-5}} = 1.53$ MPa
>
> **Step 3 — Margin of safety (yield):**
> $\text{MoS}_y = \dfrac{503}{1.53 \times 1.25} - 1 = \dfrac{503}{1.91} - 1 = 262 \gg 0$ — **Pass** (by a very large margin)
>
> **Step 4 — Margin of safety (ultimate):**
> $\text{MoS}_u = \dfrac{572}{1.53 \times 1.5} - 1 = \dfrac{572}{2.30} - 1 = 248 \gg 0$ — **Pass**
>
> **Key insight:** For CubeSats, quasi-static axial stress on the rails is never the critical load case. The rails are massively over-designed for direct compression. The critical structural design drivers are usually:
> 1. **Stiffness** (fundamental frequency > 40 Hz) — driven by internal board and component mounting, not rail strength
> 2. **Random-vibration fatigue** on PCB solder joints — the real failure mode
> 3. **Deployment mechanism reliability** — spring force, latch engagement, alignment tolerances
> 4. **CG location** — difficult to achieve with asymmetric payloads or propulsion tanks

### 12.1.7 Fundamental frequency

> **Key equations — fundamental frequency (simplified beam model)**
>
> For a cantilevered beam (simplified CubeSat model, clamped at the deployer interface):
> $$f_1 = \frac{1.875^2}{2\pi L^2} \sqrt{\frac{EI}{\rho_L}}$$
>
> where $E$ = Young's modulus (Pa), $I$ = second moment of area (m$^4$), $\rho_L = \rho A_{\text{cross}}$ = mass per unit length (kg/m) and $L$ = length (m).
>
> **Requirement:** $f_1 > 40$ Hz (from the deployer ICD). Some deployers require $> 90$ Hz (e.g. NanoRacks NRCSD).
>
> **For a 3U CubeSat modelled as a cantilevered Al box beam:**
> - $L = 0.34$ m, $E = 72$ GPa, box wall thickness $t = 1.5$ mm
> - $I \approx \dfrac{b^4 - (b-2t)^4}{12} = \dfrac{0.10^4 - 0.097^4}{12} = \dfrac{1.000 \times 10^{-4} - 0.885 \times 10^{-4}}{12} \approx 9.6 \times 10^{-7}$ m$^4$
> - Linear mass: $\rho_L = m/L = 5/0.34 = 14.7$ kg/m
>
> $f_1 = \dfrac{3.516}{2\pi \times 0.34^2} \sqrt{\dfrac{72 \times 10^9 \times 9.6 \times 10^{-7}}{14.7}} = \dfrac{3.516}{0.726} \sqrt{4700} = 4.84 \times 68.6 \approx 330$ Hz
>
> **This easily exceeds 40 Hz.** The structure itself is very stiff. However, the actual first mode is usually determined by (a) the heaviest internal component on its mounting bracket (e.g. a 350 g star tracker cantilevered on a bracket), or (b) a deployable mechanism in its stowed configuration (e.g. a folded solar panel constrained only by a hold-down pin). **These local modes, not the overall structural mode, are typically the design concern.**

---

## 12.2 Propulsion system design

*[Source: SMAD, Ch. 17; Sutton & Biblarz, Ch. 2–4; Goebel & Katz, *Fundamentals of Electric Propulsion*, 2008]*

### 12.2.1 When propulsion is required

| Need | Typical $\Delta V$ | Example scenario | Timeline |
|------|-------------------|------------------|----------|
| **Orbit maintenance** (drag compensation) | 5–15 m/s per year | LEO below 400 km in solar maximum | Continuous low thrust |
| **Deorbit** (active disposal) | 50–150 m/s | Active disposal from > 600 km (FCC 5-year rule, Chapter 7 §7.3.2) | End of mission |
| **Collision avoidance** | 1–5 m/s per event | Conjunction avoidance, 2–5 events per year for LEO | On demand, within hours |
| **Constellation phasing** | 10–50 m/s | Spreading satellites into operational orbit slots | Weeks to months |
| **Orbit raising** | 50–200 m/s | Transfer from deployment orbit to operational orbit | Weeks to months |
| **Station-keeping** | 1–10 m/s per year | Maintain orbit altitude and phase | Periodic |

**When no propulsion is needed:**

- **Orbit < 500 km:** natural atmospheric decay provides FCC 5-year deorbit compliance (depends on ballistic coefficient and solar activity; see Chapter 7 §7.3.3)
- **Low-cost technology demonstration:** limited lifetime acceptable, no orbit maintenance needed
- **Constellation using differential drag for phasing** (e.g. Planet SuperDove adjusts its cross-section area to create differential drag, enabling free phasing manoeuvres)
- **Budget-constrained missions** where propulsion cost, risk and mass exceed the benefit

### 12.2.2 The Tsiolkovsky rocket equation — physics

The rocket equation is the fundamental relationship governing all propulsive manoeuvres. It derives from conservation of momentum: the momentum of the exhaust equals the momentum change of the spacecraft. Part V §V.3 gives the derivation; Figure 12.2 plots the result.

> **Key equations — Tsiolkovsky rocket equation**
>
> Starting from $F = \dot{m} v_e$ (thrust = mass flow rate × exhaust velocity) and integrating:
>
> $$\Delta V = v_e \ln\left(\frac{m_0}{m_f}\right) = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)$$
>
> Rearranged for propellant mass:
> $$m_{\text{propellant}} = m_{\text{dry}} \times \left(e^{\Delta V / (I_{sp} \cdot g_0)} - 1\right)$$
>
> where:
> - $v_e = I_{sp} \times g_0$ = effective exhaust velocity (m/s)
> - $I_{sp}$ = specific impulse (s) — the "fuel efficiency" of the thruster. Physically: how many seconds a thruster can produce 1 N of thrust from 1 kg of propellant under standard gravity. Higher $I_{sp}$ = less propellant needed.
> - $g_0 = 9.80665$ m/s$^2$ — standard gravitational acceleration (conversion factor)
> - $m_0$ = initial (wet) mass (kg) = $m_f + m_{\text{propellant}}$
> - $m_f$ = final (dry) mass (kg) = spacecraft mass after all propellant is consumed
>
> **The tyranny of the rocket equation:** The propellant mass grows exponentially with $\Delta V / v_e$. For $\Delta V = v_e$ (one exhaust velocity's worth of $\Delta V$), 63 % of the initial mass must be propellant. For $\Delta V = 2 v_e$, 86 % must be propellant. This is why high-$I_{sp}$ systems are so valuable for large-$\Delta V$ missions — they increase the $v_e$ in the denominator, dramatically reducing the mass ratio.

![Tsiolkovsky — Δv vs mass ratio for selected Isp.](../assets/figures/fig_tsiolkovsky.png)

**Figure 12.2** — The Tsiolkovsky relation: achievable $\Delta V$ against mass ratio $m_0/m_f$ for representative specific impulses from cold gas to electric propulsion. For the ~100 m/s of a CubeSat deorbit burn the curves are nearly linear and the mass ratio is close to 1; for the kilometres per second of an orbit transfer the exponential takes over.

### 12.2.3 CubeSat propulsion technologies — physics and comparison

Figure 12.3 places the five technology families compared in this section on a map of specific impulse against thrust: chemical systems sit at the bottom right (high thrust, low $I_{sp}$), electric systems at the top left (high $I_{sp}$, very low thrust), and the power each needs while firing decides which of them a CubeSat bus can actually feed.

![Log–log map of specific impulse versus thrust with labelled regions for cold gas, warm gas, green monopropellant, electrospray and Hall-effect thrusters and the three worked-example design points.](../assets/figures/fig_propulsion_map.png)

**Figure 12.3** — Specific impulse versus thrust for CubeSat propulsion options. Each shaded region spans the $I_{sp}$ and thrust ranges of the §12.2.5 comparison table and is labelled with its power during firing; electrospray thrusters fit the 20–60 W a CubeSat can supply, whereas Hall-effect thrusters generally need more. The stars are the three §12.2.5 worked-example design points for a 112 m/s deorbit of a 5 kg spacecraft, at the $I_{sp}$ used in the example and a thrust representative of the products named in this section, annotated with the propellant mass each requires.

#### Cold gas propulsion

**Physics:** Compressed gas (N$_2$, xenon, R-236fa refrigerant or other) is stored in a tank at 1–30 MPa. When a valve opens, the gas expands through a nozzle, converting thermal/pressure energy to kinetic energy. No combustion, no heating, no chemical reaction.

**Thrust:** $F = \dot{m} v_e + (p_e - p_a) A_e$. For a small converging nozzle, $v_e \approx \sqrt{2 c_p T_0}$ where $T_0$ is the tank temperature. For N$_2$ at 300 K: $v_e \approx 500$–$750$ m/s, giving $I_{sp} \approx 50$–$75$ s.

**Advantages:** simplest system (no ignition, no power except the valve solenoid), fast response (millisecond valve opening), high reliability, no plume-contamination concerns.

**Disadvantages:** low $I_{sp}$ (large propellant mass for a given $\Delta V$), bulky high-pressure tank, limited total impulse.

**Products (representative):** VACCO MiPS (R-236fa, $I_{sp} = 40$ s, 4 thrusters, 0.3 kg dry), VACCO ArgoMoon (Xe cold gas), Bradford ECAPS cold gas.

**Missions using cold gas:** MarCO (6U, JPL — used R-236fa cold gas for trajectory correction and attitude control en route to Mars), many ISS-deployed CubeSats for collision avoidance.

#### Resistojet / warm gas

**Physics:** Similar to cold gas, but the propellant is electrically heated before expansion through the nozzle. Heating increases the gas temperature $T_0$, which increases the exhaust velocity ($v_e \propto \sqrt{T_0}$). Common propellants: butane (C$_4$H$_{10}$), water (H$_2$O), ammonia (NH$_3$).

**Butane propulsion:** Butane is stored as a liquid at its saturation pressure (~2 atm at 20 °C). When heated to 200–400 °C and expanded through a nozzle, it achieves $I_{sp} \approx 80$–$100$ s. The liquid storage is much denser than compressed gas, allowing more propellant in a smaller tank.

**Advantages:** higher $I_{sp}$ than cold gas (~2×), dense liquid storage, moderate complexity.

**Disadvantages:** requires electrical power for heating (5–15 W during firing), lower thrust than cold gas, potential for nozzle clogging if the propellant decomposes.

**Products (representative):** Busek BGT-X5 (butane, $I_{sp} = 80$ s), NanoAvionics EPSS (butane, $I_{sp} = 85$ s), Pale Blue water resistojet ($I_{sp} = 70$–$80$ s).

#### Green monopropellant

**Physics:** A liquid propellant is injected into a catalyst bed where it decomposes exothermically, producing hot gases that expand through a nozzle. "Green" propellants are alternatives to hydrazine (N$_2$H$_4$) that are less toxic and easier to handle.

| Propellant | Chemical | $I_{sp}$ (s) | Density (kg/m$^3$) | Toxicity | TRL | Heritage |
|-----------|----------|-------------|-------------------|---------|-----|---------|
| **Hydrazine** (N$_2$H$_4$) | Monopropellant, Shell 405 catalyst | 220–230 | 1010 | **Extremely toxic** (carcinogen) | 9 | 50+ years, thousands of missions |
| **AF-M315E (ASCENT)** | HAN-based ionic liquid | 235–250 | 1460 | Low toxicity | 8 | GPIM demonstration (2019, NASA) |
| **LMP-103S** | ADN-based ionic liquid | 225–235 | 1240 | Low toxicity | 8 | PRISMA demonstration (2010, SSC), SkySat |
| **HTP (H$_2$O$_2$ 90 %)** | Hydrogen peroxide + silver catalyst | 150–165 | 1400 | Moderate (oxidiser) | 7 | Various small satellites |

*[Source: Masse et al., "GPIM AF-M315E Propulsion System", AIAA 2019; Anflo et al., "Flight Demonstration of LMP-103S", AIAA 2011]*

**Advantages:** high thrust (0.1–1 N for CubeSat systems), good $I_{sp}$ (220+ s), proven technology (heritage from hydrazine systems).

**Disadvantages:** requires catalyst preheating (2–10 W, 10–30 min warm-up), higher system mass (tank + catalyst bed + valves + feed system), propellant-handling safety requirements (even "green" propellants require protective equipment), higher cost ($100K+ for flight units, indicative).

**Products (representative):** Aerojet MPS-130 (AF-M315E, 1 N thrust, $I_{sp} = 235$ s, 3 kg system mass), Bradford HPGP (LMP-103S, 1 N, $I_{sp} = 230$ s).

#### Electric propulsion — electrospray (FEEP)

**Physics:** Field-emission electric propulsion (FEEP) uses a strong electric field (~$10^9$ V/m) at the tip of a needle or along the edge of a slit to ionise and extract metal atoms (typically indium or gallium) or ionic-liquid droplets. The ions are accelerated by an electric field to high velocities (10–50 km/s), producing very high $I_{sp}$.

**How it works (indium FEEP):**
1. Solid indium is heated to just above its melting point (157 °C) to form a liquid reservoir
2. Capillary action draws liquid indium to an array of sharp emitter tips
3. A high voltage (1–10 kV) between the emitter tips and an extractor grid creates an intense electric field at the tip apex
4. The field ionises individual indium atoms via field evaporation
5. The ions are accelerated through the extractor grid, creating a beam of In$^+$ ions at 20–40 km/s
6. A neutraliser (typically a carbon-nanotube or thermionic emitter) emits electrons to neutralise the beam and prevent spacecraft charging

**Performance:** $I_{sp} = 500$–$5000$ s (adjustable by varying the acceleration voltage), thrust = 0.01–1 mN, power = 20–60 W.

**Advantages:** extremely high $I_{sp}$ (minimal propellant consumption), no pressurised tanks, compact solid-propellant storage, precise thrust control (useful for formation flying).

**Disadvantages:** very low thrust (months-long burn times for significant $\Delta V$), requires significant power (20–60 W for ~0.5 mN thrust), plume contamination from metal ions (indium deposition on surfaces), limited heritage.

**Products (representative):** Enpulsion NANO R3 (indium FEEP, 0.35 mN, $I_{sp} = 1000$–$5000$ s, 0.9 kg dry mass, < 40 W), Accion TILE (ionic-liquid electrospray, 0.1 mN, $I_{sp} = 1500$ s).

**Missions using FEEP/electrospray:** LISA Pathfinder (ESA, precision formation flying, used colloid thrusters), SSTL NovaSAR-1 (Enpulsion NANO for orbit maintenance).

#### Electric propulsion — Hall-effect thruster

**Physics:** A Hall-effect thruster uses crossed electric and magnetic fields to ionise a neutral propellant gas (xenon, krypton or iodine) and accelerate the resulting ions to high velocity.

**How it works:**
1. Neutral propellant gas (Xe or I$_2$) is injected into an annular discharge channel
2. A radial magnetic field (from permanent magnets or electromagnets) traps electrons in a Hall-current loop, preventing them from reaching the anode
3. The trapped electrons collide with neutral gas atoms, ionising them
4. The ions, being much heavier, are not significantly deflected by the magnetic field and are accelerated axially by the electric field (100–500 V) between anode and cathode
5. An external cathode (hollow cathode or RF cathode) provides electrons for beam neutralisation and to sustain the discharge

**Performance:** $I_{sp} = 800$–$3000$ s, thrust = 1–50 mN for CubeSat-scale systems, power = 50–300 W.

**Advantages:** higher thrust than FEEP (newton range for larger systems), excellent $I_{sp}$, well-proven technology (GEO station-keeping heritage: Aerojet PPS-1350, Busek BHT-200).

**Disadvantages:** requires significant power (> 50 W for CubeSat scale), heavy cathode assembly, xenon storage requires high-pressure tanks (100–300 bar), channel erosion limits lifetime.

**Products (representative):** Exotrail ExoMG-nano (40 mN, $I_{sp} = 800$ s, 1.5 kg, 60 W), Busek BHT-200 (13 mN, $I_{sp} = 1370$ s, 1.0 kg, 200 W), Enpulsion MICRO (Hall thruster, iodine propellant, 1 mN, $I_{sp} = 1000$ s).

**Iodine propulsion:** Iodine (I$_2$) is emerging as an alternative to xenon for Hall thrusters and gridded ion engines. Iodine is solid at room temperature (stored without a pressure vessel), has a density of 4940 kg/m$^3$ (vs xenon at ~1600 kg/m$^3$ at 100 bar), and has a similar atomic mass (127 vs 131). The Busek BIT-3 (iodine Hall thruster) and ThrustMe NPT30-I2 have demonstrated iodine propulsion in orbit.

### 12.2.4 No propulsion — passive deorbit strategies

For missions below ~500 km where propulsion is not needed for operations, passive deorbit can satisfy the FCC 5-year or IADC 25-year guidelines:

| Method | Mechanism | Mass | Volume | Effectiveness | TRL |
|--------|-----------|------|--------|--------------|-----|
| **Atmospheric drag (natural)** | Below 500 km, atmospheric drag naturally decays the orbit | 0 | 0 | Depends on ballistic coefficient and solar cycle | 9 |
| **Drag sail** | Deployable membrane increases cross-section area by 10–100× | 0.1–0.5 kg | 0.25–1U | Very effective above 600 km | 7–8 |
| **Electrodynamic tether** | Conducting tether interacts with the geomagnetic field to decelerate | 0.2–0.5 kg | 0.5U | Moderate effectiveness; depends on orbital inclination | 6–7 |

*[Source: Cranfield Icarus drag sail, 0.1 kg; NanoSail-D2, NASA; InflateSail, SSC]*

### 12.2.5 Propulsion system comparison

| Parameter | Cold gas (N$_2$) | Warm gas (butane) | Green monoprop (AF-M315E) | Electrospray (FEEP) | Hall effect (Xe) |
|-----------|-----------------|------------------|--------------------------|--------------------|--------------------|
| $I_{sp}$ (s) | 40–75 | 80–100 | 230–250 | 500–5000 | 800–3000 |
| Thrust | 10–100 mN | 5–50 mN | 0.1–1 N | 0.01–1 mN | 1–50 mN |
| Propellant mass (100 m/s, 5 kg dry spacecraft, at the $I_{sp}$ shown) | 0.93 kg (60 s) | 0.60 kg (90 s) | 0.22 kg (235 s) | 0.042 kg | 0.055 kg |
| System dry mass | 0.3 kg | 0.5 kg | 3.0 kg | 0.9 kg | 1.5 kg |
| **Total system mass** | **1.23 kg** | **1.10 kg** | **3.22 kg** | **0.94 kg** | **1.55 kg** |
| Burn time (100 m/s) | Minutes | Minutes | Seconds | **Months** | Days–weeks |
| Power during firing | < 1 W (valve) | 5–15 W | 2–10 W (preheat) | 20–60 W | 50–300 W |
| Complexity | Low | Low–medium | High | Medium | High |
| Cost (indicative, 2026) | ~15 kEUR | ~30 kEUR | ~120 kEUR | ~50 kEUR | ~80 kEUR |
| TRL | 9 | 7–8 | 7–8 | 7–8 | 6–8 (CubeSat) |

> **Worked example — propellant mass comparison for a propulsive deorbit (what-if)**
>
> EOSat-3U itself carries no propulsion: at 500 km it relies on natural decay, and Chapter 7 §7.3.3 shows that its orbital lifetime (≈ 5 yr) meets the disposal rule without a burn, so Chapter 18 defines no Manoeuvre mode for it. The question this example answers is therefore hypothetical — *if* a propulsive deorbit were required for a 3U at 600 km, what would it cost in mass?
>
> **Scenario:** 3U CubeSat, $m_{\text{dry}} = 5.0$ kg, deorbit from 600 km to a 200 km perigee ($\Delta V = 112$ m/s, Chapter 7 §7.5).
>
> **Cold gas** ($I_{sp} = 60$ s, $v_e = 588$ m/s):
> $m_{\text{prop}} = 5.0 \times (e^{112/588} - 1) = 5.0 \times (e^{0.190} - 1) = 5.0 \times 0.210 =$ **1.05 kg**
>
> Total system: 1.05 + 0.3 = 1.35 kg = **23 % of the 6 kg CubeSat mass limit**
>
> **Green monopropellant** ($I_{sp} = 235$ s, $v_e = 2305$ m/s):
> $m_{\text{prop}} = 5.0 \times (e^{112/2305} - 1) = 5.0 \times (e^{0.0486} - 1) = 5.0 \times 0.0498 =$ **0.249 kg**
>
> Total system: 0.249 + 3.0 = 3.25 kg = **54 % of mass limit** (the system is heavy even though the propellant is light)
>
> **Electrospray (FEEP)** ($I_{sp} = 1200$ s, $v_e = 11\,768$ m/s):
> $m_{\text{prop}} = 5.0 \times (e^{112/11768} - 1) = 5.0 \times (e^{0.00952} - 1) = 5.0 \times 0.00956 =$ **0.048 kg**
>
> Total system: 0.048 + 0.9 = 0.95 kg = **16 % of mass limit** (lightest total, but takes months to execute)
>
> **Trade-off summary:** The electrospray system is the lightest overall because the high $I_{sp}$ minimises propellant mass and the dry mass is moderate. Cold gas uses the most propellant but has the lowest dry mass. Green monopropellant is dominated by its heavy feed system. **The optimal choice depends on the mission timeline:** if deorbit must happen quickly (days), cold gas or monopropellant; if months are acceptable, electric propulsion wins on mass.

---

## 12.3 On-board data handling

### 12.3.1 OBC architecture — processor selection

The on-board computer (OBC) is the spacecraft's brain, managing all data handling, commanding, telemetry generation and FDIR (fault detection, isolation and recovery — Chapter 18). Processor selection involves a fundamental trade between radiation tolerance, processing power, power consumption and cost.

**Flight-heritage processors** (representative examples):

| Processor | Architecture | Clock (MHz) | RAM | Radiation tolerance | Power (W) | TRL (space) | Cost (indicative, 2026) | Typical use |
|-----------|-------------|-------------|-----|---------------|-----------|------------|------|------------|
| **TI MSP430** | 16-bit RISC | 16–25 | 2–10 kB | Moderate (COTS, tested to 30 krad) | 0.005–0.01 | 9 | < 10 EUR | Ultra-low-power housekeeping, safe-mode OBC |
| **ARM Cortex-M4** (STM32F4) | 32-bit ARM | 168 | 192 kB + ext | Low–moderate (COTS, 10–30 krad) | 0.05–0.20 | 8–9 | 10–20 EUR | **Standard CubeSat OBC**, TM/TC handling, ADCS control loop |
| **ARM Cortex-M7** (STM32H7) | 32-bit ARM | 400–480 | 1 MB + ext | Low–moderate (COTS, 10–20 krad) | 0.1–0.5 | 7–8 | 15–30 EUR | Higher-performance CubeSat OBC, on-board image processing |
| **ARM Cortex-A** (Linux-capable, e.g. NXP i.MX6) | 32/64-bit ARM | 500–1200 | 256 MB–1 GB DDR | Low (COTS, < 10 krad) | 1–3 | 6–7 | 20–50 EUR | Payload processing, AI/ML inference, Linux OS |
| **Xilinx Zynq** (SoC: ARM + FPGA) | ARM Cortex-A9 + Artix-7 FPGA | 667 + programmable | 512 MB + FPGA fabric | Moderate (Zynq-7000) to high (Kintex rad-hard) | 2–5 | 7–8 | 100–500 EUR | High-throughput data processing, software-defined radio, image compression |
| **LEON3/4** (rad-hard SPARC) | 32-bit SPARC | 50–250 | External | High (100–300 krad, SEL immune) | 1–3 | 9 | 10K–50K EUR | ESA heritage missions, GEO, deep space |
| **RAD750** (BAE Systems) | 32-bit PowerPC | 200 | 128 MB | Very high (1 Mrad, SEL immune) | 5–10 | 9 | 200K+ EUR | NASA flagship missions (MRO, Curiosity, JWST) |

*[Source: STMicroelectronics STM32 datasheets; Xilinx Zynq-7000 datasheet; Cobham Gaisler LEON3 datasheet]*

### 12.3.2 Operating system and radiation effects

**RTOS vs bare-metal vs Linux:**

| Approach | OS | Pros | Cons | When to use |
|----------|-----|------|------|------------|
| **Bare-metal** | None (custom event loop) | Minimum overhead, deterministic timing, smallest code size | Hard to maintain, no task isolation, no file system | Ultra-simple 1U missions (MSP430) |
| **RTOS** (FreeRTOS, ChibiOS, Zephyr) | Real-time OS | Deterministic scheduling, task isolation, mature ecosystem, small footprint (10–50 kB) | More complex than bare-metal; requires task-priority design | **Standard for CubeSat C&DH**: ADCS loop, TM/TC, mode management |
| **Linux** (Yocto, Buildroot) | Full OS | Rich ecosystem (Python, networking, file system, device drivers), easy development | Non-deterministic (not suitable for hard real time), large footprint (50+ MB), power-hungry processor | Payload data processing, AI/ML, on-board image analysis |

**Radiation effects on processors:** The space radiation environment (Chapter 7 §7.6) causes two categories of effects:

1. **Total ionising dose (TID):** accumulated radiation damage from trapped protons/electrons and solar particles. Measured in rad(Si) or gray. Causes threshold-voltage shifts in CMOS transistors, increasing leakage current and eventually causing functional failure.
   - LEO (500 km, 51.6°): ~1–5 krad/year behind 2 mm Al shielding
   - LEO polar/SSO (800 km): ~5–10 krad/year
   - MEO (through the proton belt): ~50–100 krad/year
   - GEO: ~10–30 krad/year

2. **Single-event effects (SEE):** a single energetic particle (proton or heavy ion) deposits enough charge in a transistor to flip a bit (SEU — single-event upset), latch a transistor (SEL — single-event latch-up, potentially destructive), or burn out a power device (SEB — single-event burnout).
   - **SEU rate in LEO:** ~1–10 bit flips per day per GB of SRAM (highly variable with orbit and shielding)
   - **SEL mitigation:** current-limiting resistors on power lines, latch-up detection circuits, watchdog resets
   - **SEU mitigation:** error detection and correction (EDAC) on memory (Hamming codes, TMR — triple modular redundancy)

**CubeSat approach to radiation:** Most CubeSats in LEO (< 600 km, < 3-year mission) use COTS processors with EDAC on memory and a watchdog timer. Total dose over a 3-year LEO mission is typically 3–15 krad, which most COTS ARM Cortex-M processors survive (tested and characterised, even if not guaranteed). For longer missions, higher orbits or critical applications, rad-tolerant or rad-hard processors are needed.

### 12.3.3 Data storage sizing

> **Key equations — data storage**
>
> $$S_{\text{required}} = V_{\text{daily}} \times N_{\text{days}} \times f_{\text{safety}}$$
>
> where $V_{\text{daily}}$ = daily data generation (from the data budget, Chapter 11 §11.9), $N_{\text{days}}$ = days between full downlinks (typically 1–3 for LEO), $f_{\text{safety}} = 2$ (to handle missed passes, ground-station outages and safe-mode periods).
>
> **Storage technologies:**
>
> | Technology | Capacity | Write speed | Radiation tolerance | Power | CubeSat use |
> |-----------|----------|------------|---------------------|-------|------------|
> | NOR flash | 4–256 MB | 1–5 MB/s | Moderate (10–50 krad) | Low | Code storage, boot ROM, critical parameters |
> | NAND flash (SLC) | 1–128 GB | 10–50 MB/s | Low–moderate (5–20 krad) | Low | **Primary data storage** |
> | NAND flash (MLC/TLC) | 32–512 GB | 50–200 MB/s | Low (< 10 krad) | Low | Maximum capacity (use EDAC and scrubbing) |
> | SD card (industrial) | 4–128 GB | 10–50 MB/s | Low (< 5 krad) | Very low | Budget missions (risk: wear levelling + radiation = data loss) |
> | MRAM | 1–64 MB | 10–50 MB/s | High (> 100 krad) | Very low | Critical parameters, non-volatile log |

> **Worked example — storage for the 3U EO CubeSat**
>
> **Given:** daily generation = 720 MB and daily downlink capacity = 956 MB (Chapter 11 §11.9). The capacity exceeds generation, so in nominal operations the store empties every day; the storage must instead cover the *abnormal* case of several days without a successful downlink. Take $N_{\text{days}} = 3$ (a long weekend of ground-station outage, or a safe-mode period) and $f_{\text{safety}} = 2$:
>
> $S_{\text{required}} = 720 \times 3 \times 2 = 4320$ MB $\approx$ **4.3 GB**
>
> **Specify:** ≥ 8 GB NAND flash storage (the next standard size). The OBC selected in §12.5 includes 4 GB of NAND flash; adding an 8 GB SD card or an additional NAND chip provides adequate capacity. After a three-day outage the 2.2 GB backlog clears in $2160/(956 - 720) \approx 9$ days at the nominal downlink rate (Chapter 11 §11.9), which is why a safe-mode return procedure usually includes extra downlink passes.
>
> For a high-resolution imager generating 4.5 GB/day, the storage requirement is $4500 \times 3 \times 2 = 27$ GB. Specify ≥ 32 GB flash storage.

### 12.3.4 Flight software functions

| Function | Description | Typical execution rate | Criticality |
|----------|------------|----------------------|-------------|
| **Mode management** | Transition between Safe, Idle, Imaging, Downlink and Eclipse modes based on a state machine (Chapter 18) | Event-driven | **Critical** (incorrect transition = mission loss) |
| **ADCS control loop** | Read sensors (star tracker, gyro, magnetometer), compute attitude estimate (Kalman filter), command actuators (PID controller) | 1–10 Hz | **Critical** (loss of pointing = loss of mission) |
| **TM/TC handling** | Generate CCSDS telemetry packets, parse and execute telecommands | 1 Hz (TM), event-driven (TC) | **Critical** (loss of communication = loss of mission) |
| **Data handling** | Payload data acquisition, compression (JPEG2000, CCSDS 122.0), buffering, downlink queue management | On demand | Important |
| **FDIR** | Fault detection, isolation and recovery: watchdog timer, over-current protection, sensor consistency checks, autonomous safe-mode trigger | 1–10 Hz | **Critical** (must detect and recover from faults autonomously) |
| **Housekeeping** | Monitor temperatures, voltages, currents, wheel speeds; log to non-volatile memory | 0.1–1 Hz | Important |
| **Scheduling** | Time-tagged command execution: autonomous imaging over target, downlink preparation before ground pass, desaturation scheduling | 1 Hz | Important |
| **Thermal control** | Read temperature sensors, control heaters (on/off thermostat or PID) | 0.1 Hz | Moderate (for heater-equipped missions) |

---

## 12.4 From sizing to equipment: selecting components

The subsystem chapters (9–12) produce *sizes* — a solar-array area, a battery energy, a wheel momentum, a transmitter power, a storage capacity. The next step is to turn each size into a piece of hardware. Chapter 13 treats equipment selection and the bill of materials in full (make/buy/reuse, TRL, export control); this section gives the checks that belong with the sizing itself, because the moment real components replace parametric estimates is the moment the budgets change.

**For each required category, select a component and verify:**
- Does it fit within the subsystem mass allocation of Chapter 8 §8.4?
- Is its power draw within the power budget for the operational modes in which it is on (Chapter 8 Table 8.4)?
- Is the interface compatible (PC/104, I²C, SPI, CAN, RS-422 — Chapter 8 §8.3)?
- Is the RF chain consistent (transponder band = antenna band = ground-station band — Chapter 11)?
- Is the component qualified for the launch vibration environment of §12.1.5?
- Does the quantity make sense (e.g. 4 reaction wheels, 3 magnetorquers — Chapter 10)?

**Component trade study.** For contested selections — two or three credible candidates — run the formal tabular trade of Chapter 4 §4.5: define the criteria (mass, power, cost, TRL, heritage, performance), score each candidate on a 1–5 scale, apply weights, compute weighted scores and document the winner and the rationale.

**Real mission example — Iridium NEXT equipment selection.** Iridium NEXT (Thales Alenia Space, 2017–2019) serves as a large-scale example of rigorous equipment selection. For the phased-array antenna:

| Criterion | Weight | Candidate A (Thales) | Candidate B (Raytheon) |
|-----------|--------|---------------------|----------------------|
| Performance | 0.30 | 4.5 | 4.0 |
| Mass | 0.20 | 3.5 | 4.0 |
| Cost | 0.20 | 3.0 | 4.5 |
| TRL | 0.15 | 5.0 | 4.0 |
| Schedule | 0.15 | 4.0 | 3.5 |
| **Weighted** | | **3.95** | **4.00** |

The selection was ultimately Candidate A (Thales) because of contractual considerations beyond the numerical trade — illustrating that trade studies inform but do not dictate decisions.

---

## 12.5 Budget closure check

Once every subsystem has real components, the engineering budgets of Chapter 8 are re-computed from the equipment list rather than from parametric estimates, and each one is checked against its limit. This is the natural end-point of the subsystem-design sequence and the entry condition for the integration and verification chapters that follow: a design in which any budget is negative is not ready to be verified.

### 12.5.1 Method

1. **Re-total every budget from the equipment list:** mass (with the two-level margin schedule of Chapter 8 Table 8.3), power per operational mode, link margin, data budget, pointing budget, structural margins and cost.
2. **Compare parametric estimates with equipment-based totals** and record the difference; a change of more than about 10 % in any subsystem is a signal that the parametric model, the equipment choice or both need a second look.
3. **Classify each budget** as green (margin comfortably above the phase requirement), amber (positive but below it) or red (negative).
4. **Resolve every red before proceeding,** and carry every amber into the risk register (Chapter 15) with an owner and a mitigation.

### 12.5.2 Worked example — EOSat-3U equipment list

> Mass, power and cost columns are **line totals** (unit value × quantity); the unit value is given in the component description where it differs.
>
> | Category | Component (representative) | Qty | Mass (kg) | Power (W) | Cost (kEUR, indicative) | Interface |
> |----------|-----------|-----|----------|----------|-------------|-----------|
> | EPS board | GomSpace P31u (MPPT, 3.3 V/5 V/battery rails) | 1 | 0.10 | 0.5 | 8 | I²C |
> | Battery | GomSpace BP4 (2S2P, 38 Wh, Li-ion 18650) | 1 | 0.20 | — | 5 | I²C (telemetry) |
> | Solar panels | MMA HaWK deployable, 2 × (0.225 kg, ~12 W BOL, 12.5 kEUR) | 2 | 0.45 | — | 25 | Direct to EPS |
> | OBC | GomSpace A3200 (ARM Cortex-A, Linux, 4 GB NAND) | 1 | 0.08 | 1.0 | 12 | I²C, SPI, UART |
> | Reaction wheels | Blue Canyon RW210, 4 × (0.055 kg, 0.6 W, 8 kEUR; 1 mN m, 10 mN m s) | 4 | 0.22 | 2.4 | 32 | SPI |
> | Magnetorquers | CubeSpace CubeMAG, 3 × (0.03 kg, 0.1 W, 3 kEUR; 0.2 A m$^2$) | 3 | 0.09 | 0.3 | 9 | I²C |
> | Star tracker | Blue Canyon NST (10 arcsec accuracy, 2 Hz update) | 1 | 0.35 | 1.5 | 35 | SPI/UART |
> | Sun sensors | NewSpace NFSS-411, 6 × (5 g, 0.01 W, 1 kEUR; 0.5°) | 6 | 0.03 | 0.06 | 6 | Analogue/I²C |
> | Transponder | Endurosat S-band TX/RX (2 W RF, QPSK + LDPC, 1–5 Mbit/s) | 1 | 0.10 | 6.0 (TX) | 15 | SPI |
> | Antenna | Endurosat S-band patch (6 dBi, RHCP) | 1 | 0.02 | — | 3 | RF coax |
> | Payload | Custom telescope (multispectral, 5 m GSD) | 1 | 1.50 | 5.0 | 150 | LVDS/SPI |
> | Structure | ISIS 3U frame (Al 7075-T6, hard anodised) | 1 | 0.30 | — | 8 | Mechanical |
> | Harness | Custom cables, connectors, PC/104 stack | 1 | 0.15 | — | 5 | Various |
> | **TOTAL** | | | **3.59** | **≈ 10.3 (imaging: payload + OBC + star tracker + wheels + EPS + magnetorquers + sun sensors)** | **313** | |
>
> **Parametric estimate from Chapter 8:** 3.68 kg CBE. **Equipment total:** 3.59 kg. Difference: −2 % (within the expected accuracy of parametric models).
>
> **Mass budget** (Phase A schedule of Chapter 8 Table 8.3, with a uniform 20 % equipment-maturity margin for simplicity):
> - CBE: 3.59 kg
> - + 20 % equipment margin: 4.31 kg
> - + 20 % system margin: 5.17 kg (MEV)
> - CDS limit: 6.0 kg
> - **Margin to limit: 0.83 kg (14 %)** — amber: acceptable for Phase A but tight for Phase B and beyond.

### 12.5.3 Worked example — EOSat-3U closure table

| Budget | Limit / requirement | Equipment-based value | Margin | Status | Source |
|--------|--------------------|----------------------|--------|--------|--------|
| Mass | 6.0 kg (CDS 3U) | MEV 5.17 kg (CBE 3.59 kg) | 0.83 kg (14 %) | Amber | §12.5.2, Table 8.3 |
| Power — array | 16.0 W BOL required | ~24 W BOL (two deployable panels) | ~8 W (50 %) | Green | Chapter 9 §9.2 |
| Power — imaging mode | 8.0 W allocation | ≈ 10.3 W from equipment list (payload 5.0, star tracker 1.5, 4 wheels 2.4, OBC 1.0, EPS 0.5, magnetorquers 0.3, sun sensors 0.06) | −2.3 W | **Red** | Chapter 8 Table 8.4 |
| Battery | ≥ 11 Wh specified | 38 Wh (2S2P) | 27 Wh | Green | Chapter 9 §9.3 |
| Link margin | ≥ 3 dB at 10° elevation | 10.4 dB at 5 Mbit/s | 7.4 dB | Green | Chapter 11 §11.8.1 |
| Data budget | 720 MB/day generated | 956 MB/day capacity | 33 % | Green | Chapter 11 §11.9 |
| Pointing | 0.1° (3σ) | 0.023° RSS | 77 % | Green | Chapter 10 §10.4 |
| Structural | $f_1 > 40$ Hz; MoS ≥ 0 | ≈ 330 Hz global mode; MoS ≫ 0 | Large | Green (local modes to be verified by test) | §12.1.6–§12.1.7 |
| Hardware cost | 320 kEUR ceiling (assumed for the example) | 313 kEUR | 7 kEUR (2 %) | **Red** (below the 10 % Phase A cost reserve) | §12.5.2 |

The 313 kEUR hardware line is driven by the custom 150 kEUR telescope of the §12.5.2 list; the cost chapter's canonical EOSat-3U estimate (Chapter 16 §16.1.6), which assumes a COTS imager, puts hardware alone at ≈ 161–178 kEUR within a ≈ 457–490 kEUR mission total. The two are different payload choices, not an arithmetic disagreement, and the comparison in Chapter 13 §13.6 uses the Chapter 16 figures.

Two red entries are instructive. The cost line shows the custom telescope consuming almost the whole ceiling with only 2 % to spare — well below the 10 % reserve a Phase A estimate should carry (Chapter 16 §16.4) — and is the first thing a review board would challenge. The parametric imaging-mode allocation of 8 W (Chapter 8 Table 8.4) was made before any component was chosen; the chosen star tracker and four wheels add up to more than the parametric AOCS estimate assumed. The design is not broken — the array delivers far more than 10 W in sunlight and the battery is large — but the mode table, the orbit-average power and the eclipse case of Chapter 9 all have to be re-run with the equipment numbers before the budget can be called closed. That re-run, and the decision whether to re-baseline the allocation or to duty-cycle the star tracker during imaging, is exactly what the closure check exists to force.

### 12.5.4 If a budget does not close

| Budget | Common fix | Impact | Typical mass/power/cost trade |
|--------|-----------|--------|------------------------------|
| **Mass** (negative) | Remove propulsion; select lighter components; reduce redundancy; move to a larger form factor | Risk / performance trade | Removing propulsion saves 0.5–1.5 kg |
| **Power** (negative) | Add a deployable array; reduce payload duty cycle; select lower-power AOCS; schedule operations to avoid simultaneous loads | Cost / schedule trade | A deployable panel adds ~15 W but costs 0.3 kg + 25 kEUR (indicative) |
| **Link** (negative) | Increase TX power; use a higher-gain antenna; reduce data rate; upgrade coding; upgrade the ground station | Mass / power trade | 3 dB gain from coding is "free"; 3 dB from a bigger antenna costs mass |
| **Cost** (over ceiling) | Use COTS instead of rad-hard; remove propulsion; reduce the ground segment; use SatNOGS instead of commercial ground stations | Risk / capability trade | COTS vs rad-hard saves 10–100× on processor cost |
| **Pointing** (insufficient) | Upgrade the star tracker; improve alignment calibration; add vibration isolation for wheels; reduce thermal gradients | Cost / complexity trade | Alignment improvement is usually cheapest |

---

## 12.6 Returning to UniSat-1: structure, OBDH and equipment list

**CDS compliance for the 1U form factor.** The CubeSat Design Specification (CDS Rev 14) defines the 1U envelope:

| Parameter | 1U specification | UniSat-1 design | Compliance |
|-----------|-----------------|-----------------|------------|
| Dimensions | 100.0 × 100.0 × 113.5 mm | 100.0 × 100.0 × 113.5 mm (ISIS 1U frame) | **Pass** |
| Maximum mass | 2.0 kg (CDS Rev 14, ISIPOD) | 1.0 kg target (50 % margin to the 2 kg limit) | **Pass** |
| Rail material | Hard-anodised Al 7075-T6 | Standard (part of the ISIS frame, 7075-T6, Type III anodise) | **Pass** |
| Rail cross-section | 8.5 × 8.5 mm minimum | Standard (ISIS: 8.5 × 8.5 mm) | **Pass** |
| Deployment switches | Min 1 per accessible face | 2 switches (ISIS standard, on +X/−X rail faces) | **Pass** |
| RBF pin | Required | Included (ISIS standard, on −Z face) | **Pass** |
| CG offset | ≤ 2 cm from geometric centre | < 1 cm (symmetric PCB stack layout, battery centred) | **Pass** |
| Protrusions | None beyond rail envelope (stowed) | UHF monopole antenna stowed along the rail (spring-loaded, within envelope) | **Pass** |
| Fundamental frequency | > 40 Hz first mode | ~600 Hz (a 1U Al structure is extremely stiff) | **Pass** |

**Note on the CDS mass limit:** CDS Rev 14 specifies 2.0 kg as the 1U deployer limit for the ISIPOD. However, many deployer providers (e.g. NanoRacks, Exolaunch) specify 1.33 kg for 1U. Always check the specific deployer ICD. UniSat-1 targets 1.0 kg, well within either limit.

**No propulsion:** At 400 km altitude, atmospheric drag provides natural deorbit. The ballistic coefficient for a 1U is

$$B = \frac{m}{C_D \times A} = \frac{1.0}{2.2 \times 0.01} = 45.5 \text{ kg/m}^2$$

Using the method of Chapter 7 §7.3.3 this gives an orbital lifetime of roughly 6–18 months depending on solar activity (F10.7 index). At solar maximum (F10.7 > 200) the denser atmosphere deorbits the satellite in about 6 months; at solar minimum (F10.7 ~ 70) the lifetime extends towards 18 months. Both are within the FCC 5-year rule and the IADC 25-year guideline without any propulsion system.

**OBC selection rationale:** UniSat-1 uses a custom board based on the TI MSP430 (safe mode / housekeeping) + STM32F4 Cortex-M4 (main OBC). The MSP430 runs bare-metal firmware handling the watchdog, power monitoring and safe-mode recovery. The STM32F4 runs FreeRTOS handling TM/TC, magnetometer data acquisition and scheduling. The dual-processor architecture provides redundancy: if the STM32F4 fails (SEU, latch-up), the MSP430 can maintain safe-mode operations and respond to ground commands.

**Data storage:** With 1.13 MB/day of magnetometer data (Chapter 11 §11.8.2) and 4800 bit/s useful downlink, on-board storage is not a bottleneck. A 4 MB NOR flash is adequate (it stores about 3.5 days of data as a buffer — enough to ride out the single-station contact shortfall identified in Chapter 11 while additional stations are brought in). No NAND flash and no SD card are needed.

**Complete 1U equipment list:**

> | # | Category | Component (representative) | Mass (g) | Power (W) | Cost (kEUR, indicative) | Qty | Interface |
> |---|----------|-----------|----------|----------|-------------|-----|-----------|
> | 1 | Structure | ISIS 1U CubeSat structure (Al 7075-T6) | 200 | — | 4.0 | 1 | Mechanical |
> | 2 | EPS | GomSpace NanoPower P31us (EPS board + 2S Li-ion battery, 10 Wh) | 200 | 0.3 (quiescent) | 12.0 | 1 | I²C |
> | 3 | Solar cells | Body-mounted triple-junction GaAs cells (5 faces) | 50 | — (generates power) | 8.0 | 5 | Direct to EPS |
> | 4 | OBC | Custom MSP430 + STM32F4 board (with 4 MB NOR flash) | 30 | 0.3 | 3.0 | 1 | I²C, SPI, UART |
> | 5 | Comms | UHF transceiver (NanoCom AX100, 0.5 W TX, 9600 bit/s) | 60 | 0.5 (TX) / 0.1 (RX) | 8.0 | 1 | SPI |
> | 6 | Antenna | UHF monopole (deployable, $\lambda/4 = 17$ cm nitinol) | 20 | — | 2.0 | 1 | RF coax |
> | 7 | Payload | MEMS magnetometer (custom PCB, PNI RM3100 sensor) | 50 | 0.2 | 5.0 | 1 | SPI |
> | 8 | AOCS (passive) | Permanent magnet (AlNiCo, 0.5 A m$^2$) + 2 hysteresis rods (HyMu-80) | 30 | 0 | 1.0 | 1 | None (passive) |
> | 9 | Harness | Internal cables, connectors, PC/104 stack header | 50 | — | 1.0 | 1 | Various |
> | | **TOTAL** | | **690** | **~1.3 (peak TX)** | **~44** | | |
>
> **Mass budget** (Chapter 8 Table 8.3, Phase A):
>
> | Level | Mass (g) |
> |-------|----------|
> | CBE (current best estimate) | 690 |
> | + 20 % equipment margin | 828 |
> | + 20 % system margin | 994 |
> | **MEV (maximum expected value)** | **994** |
> | Deployer limit (ISIPOD) | 2000 |
> | **Margin to limit** | **1006 g (50 %)** |
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
> | Array available (orbit average, EOL — Chapter 9 §9.5) | 2.3 |
> | **Margin** | **1.0 W (43 %)** |
>
> **Key insight:** The entire UniSat-1 equipment list is 5 COTS components plus 2 custom boards (OBC and magnetometer PCB). Total hardware cost is ~44 kEUR — an order of magnitude less than a typical 3U mission. With labour, integration and test, launch and operations, the total mission cost is 80–150 kEUR (Chapter 13 §13.6 gives the breakdown). This demonstrates that a useful space mission can be built for less than the cost of a mid-range car.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| CDS compliance | Standard dimensions, Al 7075-T6 anodised rails (8.5 mm), deployment switches, RBF pin, CG limits |
| Structural materials | Al 7075-T6: $\sigma_y = 503$ MPa, $E = 72$ GPa; anodisation for wear/insulation; CFRP not suitable for rails |
| Launch loads | 6–12 g axial quasi-static, ~7 g$_{\text{rms}}$ random vibration (20–2000 Hz), 500–2000 g shock; PCB solder joints are the weak point |
| Structural MoS | $\text{MoS} = \sigma_{\text{allow}}/(\sigma_{\text{design}} \times \text{FoS}) - 1 \geq 0$; FoS 1.25 yield / 1.5 ultimate (metallic) |
| Frequency requirement | First mode > 40 Hz; CubeSat Al structures easily exceed this (~330 Hz for a 3U box beam); local modes (PCBs, deployables) are the risk |
| Tsiolkovsky equation | $m_{\text{prop}} = m_{\text{dry}} \times (e^{\Delta V/(I_{sp} g_0)} - 1)$; exponential growth with $\Delta V / v_e$ |
| Cold gas | $I_{sp}$ 40–75 s; simple, fast, reliable; heavy propellant penalty for $\Delta V > 30$ m/s |
| Green monopropellant | $I_{sp}$ 225–250 s; high thrust (0.1–1 N); heavy feed system; AF-M315E and LMP-103S flight-proven |
| Electrospray (FEEP) | $I_{sp}$ 500–5000 s; minimal propellant; months-long burns; 20–60 W power; indium or ionic liquid |
| Hall thruster | $I_{sp}$ 800–3000 s; moderate thrust (1–50 mN); 50–300 W; iodine emerging as a xenon alternative |
| Propulsion trades | High $I_{sp}$: less propellant, more dry mass, long burns; low $I_{sp}$: more propellant, lighter system, fast burns |
| When to skip propulsion | Below 500 km (natural deorbit); technology demonstration; differential-drag constellation |
| OBC processors | MSP430 (0.01 W, safe mode), Cortex-M4 (0.2 W, standard CubeSat), Zynq (3 W, high throughput), LEON3 (rad-hard, ESA) |
| RTOS vs Linux | FreeRTOS for real-time C&DH (standard); Linux for payload processing (data-intensive) |
| Radiation effects | TID: 1–10 krad/yr LEO; SEU: 1–10 bit flips/day/GB; mitigate with EDAC, watchdog, redundancy |
| Data storage | $S = V_{\text{daily}} \times N_{\text{days}} \times 2$; SLC NAND flash for primary storage; NOR flash for code and critical parameters |
| Equipment selection | Every selection re-checked against mass, power, interface and RF compatibility; trade study for contested selections |
| Budget closure | All margins must be positive before integration and verification begin; mass margin > 10 % at Phase A; equipment-based totals replace parametric estimates |

---

## Problems

1. **Rail stress and margin of safety.** A 6U CubeSat of 11 kg is launched with a 10 g axial quasi-static load and a dynamic amplification factor of 1.3. The load is shared by four Al 6061-T6 rails of 8.5 × 8.5 mm. Compute the design stress and the yield and ultimate margins of safety using the ECSS factors of §12.1.6. Then explain why a positive MoS of several hundred does not mean the structure is "over-designed".

2. **Fundamental frequency.** Repeat the box-beam estimate of §12.1.7 for a 6U CubeSat (226 × 100 mm cross-section, $L = 0.34$ m, 11 kg) with 1.0 mm walls, treating the section as a rectangular tube and bending about its weak axis. Compare with the 40 Hz and 90 Hz deployer requirements. Then estimate the first mode of a 350 g star tracker mounted on a 40 mm aluminium bracket of 2 mm thickness treated as a cantilever, and state which of the two modes drives the design.

3. **Rocket equation.** A 3U CubeSat with a 5.2 kg dry mass must provide 25 m/s of collision-avoidance ΔV over its life plus the 112 m/s deorbit burn of §12.2.5. Compute the propellant mass for butane ($I_{sp} = 85$ s), AF-M315E ($I_{sp} = 240$ s) and an iodine Hall thruster ($I_{sp} = 1000$ s), add the dry masses from the comparison table, and rank the options by total mass. Which would you choose if the deorbit must be complete within one month, and why?

4. **Burn time and power.** For the FEEP option of §12.2.5 (0.35 mN, 40 W), compute the total burn time for the 112 m/s deorbit of a 5 kg spacecraft and the energy consumed. Using the orbit-average power of Chapter 9 §9.2 for the 3U EO CubeSat, decide whether the thruster can run continuously or must be duty-cycled, and estimate the calendar time to complete the manoeuvre.

5. **Passive deorbit.** Using the ballistic-coefficient lifetime method of Chapter 7 §7.3.3, estimate the orbital lifetime of the EOSat-3U (5 kg, 0.03 m² frontal area) at 550 km, and the area of drag sail required to bring it below 5 years. Compare the sail's mass and stowed volume (table of §12.2.4) with the cold-gas system of §12.2.5 and recommend one.

6. **Processor selection.** A 3U Earth-observation CubeSat must run a 10 Hz attitude control loop, compress 240 Mbit/s of raw imagery to 10:1 in near-real time, and survive a 3-year mission at 550 km SSO. Using the processor table of §12.3.1, propose an OBC architecture (one or two processors), justify the operating-system choice for each, and list the radiation mitigations you would apply.

7. **Storage sizing.** A hyperspectral 6U CubeSat generates 60 GB/day and downlinks over X-band at 150 Mbit/s with six 8-minute passes per day at $\eta_{\text{protocol}} = 0.85$. Check whether the data budget closes (Chapter 11 §11.9), size the on-board storage for $N_{\text{days}} = 2$ and $f_{\text{safety}} = 2$, and select a storage technology from the table of §12.3.3 with a justification that mentions radiation.

8. **Equipment-based versus parametric budgets.** In §12.5.3 the equipment-based imaging-mode power exceeds the parametric allocation. Re-run the orbit-average power of Chapter 8 §8.4.3 with the equipment values (imaging 10 W, other modes unchanged) and the mode duty cycles of Table 8.4, and decide whether the array of Chapter 9 §9.2 still closes. Then propose two design changes that would restore the 8 W allocation and state what each costs in another budget.

9. **Budget closure for a modified mission.** Starting from the EOSat-3U equipment list of §12.5.2, add a cold-gas propulsion system (1.35 kg, 15 kEUR, < 1 W) to meet a 5-year disposal requirement. Re-compute the mass budget with the Phase A margins of Chapter 8 Table 8.3 and the cost, re-classify each line of the closure table of §12.5.3, and state which fix from §12.5.4 you would apply first.

10. **UniSat-1 deployer change.** UniSat-1 is re-manifested on a deployer with a 1.33 kg limit and a 90 Hz first-mode requirement. Re-check every line of the compliance table of §12.6, recompute the mass margin, and identify the single component whose mass growth would most quickly threaten the new limit.

---

## References

1. Cal Poly, *CubeSat Design Specification (CDS) Rev 14.1*, February 2022. https://www.cubesat.org/cubesatinfo
2. Wertz, J. R., Everett, D. F. & Puschell, J. J. (eds.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, Ch. 11.3 (Structures), Ch. 17 (Propulsion). https://www.space.com/smad
3. ECSS, *ECSS-E-ST-32C Rev. 1: Structural General Requirements*, 2008. https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/
4. ECSS, *ECSS-E-ST-32-10C Rev. 2: Structural Factors of Safety for Spaceflight Hardware*, 2019. https://ecss.nl
5. ECSS, *ECSS-E-ST-35C: Propulsion General Requirements*, 2008. https://ecss.nl/standard/ecss-e-st-35c-propulsion-general-requirements/
6. ECSS, *ECSS-E-ST-10-03C: Testing*, 2012. https://ecss.nl/standard/ecss-e-st-10-03c-testing/
7. Sarafin, T. P. (ed.), *Spacecraft Structures and Mechanisms: From Concept to Launch*, Springer, 1995. https://www.springer.com/gp/book/9780792334767
8. Sutton, G. P. & Biblarz, O., *Rocket Propulsion Elements*, 9th ed., Wiley, 2017, Ch. 2–4. https://www.wiley.com/en-us/Rocket+Propulsion+Elements
9. Goebel, D. M. & Katz, I., *Fundamentals of Electric Propulsion: Ion and Hall Thrusters*, Wiley, 2008.
10. Masse, R. K. et al., "Enabling High Performance Green Propulsion for SmallSats", *AIAA Propulsion and Energy Forum*, 2019.
11. Anflo, K. & Crowe, B., "In-Space Demonstration of an ADN-based Propulsion System", *AIAA Joint Propulsion Conference*, 2011.
12. Enpulsion, *NANO R3 Thruster Datasheet*, 2023 (representative example). https://www.enpulsion.com/nano
13. VACCO, *MiPS Propulsion System Datasheet*, 2023 (representative example). https://www.cubesat-propulsion.com
14. NASA, *General Environmental Verification Standard (GEVS)*, GSFC-STD-7000B, 2021.
15. Cobham Gaisler, *LEON3 Processor Datasheet*; STMicroelectronics, *STM32F4 Datasheet*; Xilinx, *Zynq-7000 SoC Datasheet* (representative examples).
