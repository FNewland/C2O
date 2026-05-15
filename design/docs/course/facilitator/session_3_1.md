# Session 3.1: Power System and Thermal Control Design


**Prerequisites:** Sessions 2.1--2.4 (requirements, functions, orbit, architecture defined)
**SpaceCDF Tabs:** Dashboard (Power KPI), Engineering Budgets, Timing Budget, Parametric

---

## References

- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.4 (EPS), Ch. 11.5 (Thermal)](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-20C: Electrical and Electronic*, 2021](https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/)
- [ECSS, *ECSS-E-ST-31C: Thermal Control*, 2020](https://ecss.nl/standard/ecss-e-st-31c-thermal-control/)
- [Patel, *Spacecraft Power Systems*, 2005, Ch. 3--8](https://www.taylorfrancis.com/books/mono/10.1201/9781420038217/spacecraft-power-systems-mukund-patel)
- [Gilmore, *Spacecraft Thermal Control Handbook, Vol. 1*, 2002](https://arc.aiaa.org/doi/book/10.2514/4.104503)
- [GomSpace, *P31u EPS Datasheet*, 2023](https://www.gomspace.com)
- [MMA Design, *HaWK Solar Array Datasheet*, 2023](https://mmadesignllc.com)
- [Spectrolab, *30% Triple-Junction Solar Cell Datasheet*, 2020](https://www.spectrolab.com)
- [Ratnakumar et al., *Lithium-Ion Batteries for Space*, NASA JPL, 2003](https://trs.jpl.nasa.gov)
- [Gilmore, *Spacecraft Thermal Control Handbook, Vol. 2: Cryogenics*, 2003](https://arc.aiaa.org/doi/book/10.2514/4.104515)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Size a solar array from mission power demand, eclipse profile, and degradation
2. Size a battery from eclipse energy demand, depth-of-discharge, and cycle-life requirements
3. Compute orbit-average power using duty cycle analysis
4. Explain EPS architecture (DET vs PPT, MPPT, bus regulation) and articulate the physics of each
5. Perform first-order thermal balance analysis (hot case and cold case) with full radiative derivation
6. Select thermal control methods and apply ECSS thermal margins
7. Explain MLI construction, heat pipe operation, and heater sizing
8. Verify power and thermal budgets in SpaceCDF

---

## 1. Electrical Power System Architecture
*[Source: SMAD, Ch. 11.4; ECSS-E-ST-20C; Patel, Ch. 3]*

The EPS is the "utility company" of the spacecraft. It must continuously supply regulated power to all subsystems through every operational mode, including eclipse. Unlike terrestrial power systems, spacecraft EPS cannot draw from a grid -- the solar array, battery, and power conditioning electronics must form a fully self-contained, autonomous energy system with zero maintenance for the mission lifetime.

### EPS Block Diagram

<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 11px;">
  <!-- Solar Array -->
  <rect x="30" y="100" width="120" height="60" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="90" y="125" text-anchor="middle" fill="#92400e" font-weight="bold">Solar Array</text>
  <text x="90" y="142" text-anchor="middle" fill="#92400e" font-size="10">GaAs 29.5%</text>
  <text x="90" y="155" text-anchor="middle" fill="#92400e" font-size="9">1361 W/m^2</text>
  <!-- MPPT -->
  <rect x="200" y="100" width="100" height="60" rx="4" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="250" y="125" text-anchor="middle" fill="#3730a3" font-weight="bold">MPPT</text>
  <text x="250" y="142" text-anchor="middle" fill="#3730a3" font-size="10">Regulator</text>
  <line x1="150" y1="130" x2="200" y2="130" stroke="#64748b" stroke-width="2" marker-end="url(#arr)"/>
  <!-- Bus -->
  <line x1="300" y1="130" x2="480" y2="130" stroke="#dc2626" stroke-width="3"/>
  <text x="390" y="120" text-anchor="middle" fill="#dc2626" font-weight="bold">Regulated Bus (3.3V / 5V / Batt)</text>
  <!-- Battery -->
  <rect x="330" y="200" width="120" height="55" rx="4" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="390" y="222" text-anchor="middle" fill="#166534" font-weight="bold">Battery</text>
  <text x="390" y="239" text-anchor="middle" fill="#166534" font-size="10">Li-ion, DOD 30%</text>
  <line x1="390" y1="200" x2="390" y2="133" stroke="#16a34a" stroke-width="2"/>
  <text x="408" y="175" fill="#16a34a" font-size="9">charge/discharge</text>
  <!-- Loads -->
  <rect x="520" y="40" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="62" text-anchor="middle" fill="#1e40af" font-size="10">Payload (SW)</text>
  <rect x="520" y="85" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="107" text-anchor="middle" fill="#1e40af" font-size="10">AOCS (SW)</text>
  <rect x="520" y="130" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="152" text-anchor="middle" fill="#1e40af" font-size="10">Comms TX (SW)</text>
  <rect x="520" y="175" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="197" text-anchor="middle" fill="#1e40af" font-size="10">OBC (always on)</text>
  <rect x="520" y="220" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="242" text-anchor="middle" fill="#1e40af" font-size="10">Heaters (thermo)</text>
  <!-- Switch lines -->
  <line x1="480" y1="57" x2="520" y2="57" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="102" x2="520" y2="102" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="147" x2="520" y2="147" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="192" x2="520" y2="192" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="237" x2="520" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="57" x2="480" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <text x="490" y="30" fill="#64748b" font-size="10">Switched lines</text>
  <text x="490" y="42" fill="#64748b" font-size="9">(SW = switchable)</text>
  <defs><marker id="arr" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
</svg>

### Solar Cell Physics

A photovoltaic cell converts photon energy into electrical energy via the photovoltaic effect. When a photon with energy $E = h\nu \geq E_g$ (where $E_g$ is the semiconductor bandgap) strikes the cell, it promotes an electron from the valence band to the conduction band, creating an electron-hole pair. The built-in electric field at the p-n junction sweeps carriers to opposite terminals, producing a voltage ($V_{oc}$) and current ($I_{sc}$).

**Single-junction vs multi-junction cells:**

A single-junction cell (e.g., silicon, $E_g = 1.12$ eV) can only absorb photons with $E \geq E_g$. Photons with $E < E_g$ pass through unabsorbed; photons with $E \gg E_g$ lose excess energy as heat (thermalisation loss). The theoretical maximum efficiency for a single-junction cell under AM0 (space) illumination is approximately 31% (Shockley-Queisser limit).

Multi-junction (MJ) cells stack two or three p-n junctions of different semiconductor materials, each tuned to absorb a different portion of the solar spectrum:

| Cell Technology | Structure | Bandgaps (eV) | AM0 Efficiency | Temp Coefficient | Flight Heritage |
|----------------|-----------|---------------|----------------|------------------|-----------------|
| **Monocrystalline Si** | Single junction | 1.12 | 16--18% | $-0.45$%/degC | Extensive (ISS, many LEO) |
| **GaAs single-junction** | Single junction | 1.42 | 22--24% | $-0.21$%/degC | Moderate |
| **InGaP/GaAs dual-junction** | 2-junction | 1.86 / 1.42 | 26--28% | $-0.20$%/degC | Moderate |
| **InGaP/GaAs/Ge triple-junction** | 3-junction (lattice-matched) | 1.86 / 1.42 / 0.67 | 28--30% | $-0.19$%/degC | Extensive (>90% of modern S/C) |
| **InGaP/GaAs/InGaAs IMM** | 3-junction (inverted metamorphic) | 1.86 / 1.42 / 1.0 | 32--33% | $-0.18$%/degC | Growing (SolAero ZTJ, Spectrolab XTJ Prime) |

*[Source: Spectrolab XTJ Prime datasheet; SolAero ZTJ datasheet; Green et al., "Solar Cell Efficiency Tables," Progress in Photovoltaics, v.62, 2024]*

**Why triple-junction GaAs dominates space:** The AM0 solar spectrum (above the atmosphere) is richer in UV and blue photons than the AM1.5 terrestrial spectrum. Triple-junction cells capture this energy across three bandgaps. The top cell (InGaP, $E_g = 1.86$ eV) absorbs blue/UV, the middle cell (GaAs, $E_g = 1.42$ eV) absorbs visible, and the bottom cell (Ge, $E_g = 0.67$ eV) absorbs near-IR. Each junction contributes voltage in series, while current is limited by the lowest-current junction (current matching constraint).

**Temperature effects:** In orbit, solar cells operate at 40--80 degC depending on mounting and orbit. Cell efficiency decreases with temperature due to increased intrinsic carrier concentration (which reduces $V_{oc}$). The temperature coefficient for triple-junction GaAs is approximately $-0.19$%/degC relative -- meaning a cell rated at 29.5% at 28 degC drops to approximately 28.5% at 80 degC. This must be included in power budget calculations:

$$\eta_{\text{cell}}(T) = \eta_{\text{ref}} \times [1 + \beta (T - T_{\text{ref}})]$$

where $\beta \approx -0.0019$ /degC for triple-junction GaAs and $T_{\text{ref}} = 28$ degC (standard test conditions).

**Degradation mechanisms:** Solar cells degrade in orbit due to:
- **Radiation damage:** Energetic protons and electrons (trapped in the Van Allen belts and from solar particle events) displace atoms in the crystal lattice, creating recombination centres that reduce minority carrier lifetime and thus current. Degradation is characterised as equivalent 1 MeV electron fluence. Typical rates: 2--3%/year in LEO, 5--8%/year in MEO (through proton belt), 1--2%/year in GEO.
- **UV darkening:** Ultraviolet radiation darkens cover glass adhesive over time, reducing transmission.
- **Micrometeoroid erosion:** Gradual pitting of cover glass reduces optical transmission.
- **Electrostatic discharge (ESD):** In GEO or polar orbits, differential charging can cause arcing between cells, permanently damaging interconnects.

Cover glass (typically ceria-doped borosilicate, 100--150 um thick) mitigates radiation and UV effects. The combined degradation factor is:

$$L_d = (1 - \delta)^n$$

where $\delta = 0.025$ (2.5%/year for triple-junction GaAs in LEO with standard cover glass) and $n$ = mission lifetime in years.

### Body-Mounted vs Deployable Solar Arrays

**Body-mounted cells** are bonded directly to the spacecraft's external panels. They are the simplest and most reliable option (no deployment mechanism, no hinges, no drive motors) but are severely area-limited.

| Mounting | Advantages | Disadvantages | Typical Power |
|----------|-----------|---------------|--------------|
| **Body-mounted** | No mechanism risk, no power for tracking, low mass, low cost | Limited area (satellite surface only), poor illumination geometry for nadir-pointing S/C, high cell temperature | 1U: ~2 W, 3U: ~7 W, 6U: ~12 W |
| **Fixed deployable** | 2--4x more area, better sun angle, lower cell temp (radiative cooling from back side) | Deployment mechanism (single point of failure), aerodynamic drag increase, structural dynamics | 3U: ~15--25 W, 6U: ~30--48 W |
| **Tracking deployable** | Optimal sun incidence ($\cos\theta \approx 1$), maximum power | SADM (Solar Array Drive Mechanism) adds mass/cost/complexity, continuous power for motor | Large S/C: 100+ W |

**Real mission examples:**
- **Planet SuperDove (3U+):** Body-mounted + two fixed deployable wings. ~25 W BOL. The deployables are spring-hinged panels that fold against the 3U body during launch and deploy after ejection from the P-POD.
- **Asteria (6U, JPL):** Dual deployable arrays, 48 W BOL. Used MMA Design HaWK panels with triple-junction GaAs cells.
- **ISS CubeSats (various 1U):** Body-mounted only, 2--3 W. Adequate for simple sensor missions with low duty cycles.

### Architecture Types

| Architecture | How It Works (Physics) | Efficiency | Complexity | Typical Use |
|-------------|----------------------|-----------|-----------|------------|
| **DET** (Direct Energy Transfer) | SA connects directly to bus; a shunt regulator diverts excess current to a resistor bank (dissipated as heat) when SA output exceeds load. No series regulator between SA and bus. Voltage varies with illumination. | 80--85% (shunt losses) | Low | Heritage GEO spacecraft, some CubeSats |
| **PPT / MPPT** (Peak Power Tracking) | A DC-DC converter (typically boost or buck-boost) between SA and bus continuously adjusts its input impedance to operate the SA at its maximum power point (MPP). Uses perturb-and-observe or incremental conductance algorithm. Extracts 10--15% more power than DET, especially at off-nominal temperatures and end-of-life. | 90--95% | Medium | Most modern CubeSats |
| **Unregulated bus** | Battery connects directly to the power bus through protection FETs only. Bus voltage equals battery voltage (varies from 3.0 V at empty to 4.2 V at full per cell, or 6.0--8.4 V for 2S configuration). Subsystems must tolerate voltage variation. | Highest (no regulator losses) | Lowest | Very simple CubeSats, 1U missions |
| **Regulated bus** | DC-DC converters create fixed voltage rails (3.3 V, 5 V, 12 V) from battery/SA input. Subsystems see constant voltage regardless of battery state. Adds ~5--10% losses in regulators but greatly simplifies subsystem design. | Good (85--90% overall) | Medium | Most CubeSat COTS EPS (GomSpace P31u, Endurosat, AAC Clyde) |

**MPPT physics:** A solar cell's I-V curve has a distinct "knee" where the maximum power ($P = I \times V$) is extracted. At open-circuit ($I = 0$), voltage is maximum but power is zero. At short-circuit ($V = 0$), current is maximum but power is zero. The MPP sits at approximately 75--80% of $V_{oc}$ and 90--95% of $I_{sc}$. Temperature shifts the I-V curve (higher T moves $V_{oc}$ left), so the MPP moves. An MPPT controller dynamically tracks this point, typically updating every 0.1--1 s. Common CubeSat MPPT converters achieve 95--97% tracking efficiency.

**Battery charge regulation:** The EPS must prevent overcharging (which causes lithium plating, gas generation, and thermal runaway in Li-ion cells) and overdischarging (which causes copper dissolution from the negative current collector, permanently damaging the cell). Modern CubeSat EPS boards implement:
- **CC-CV charging:** Constant-current charging until cell voltage reaches 4.2 V, then constant-voltage taper until current drops below C/20
- **Under-voltage lockout:** Bus disconnect when cell voltage falls below 3.0 V (or 2.8 V for emergency)
- **Cell balancing:** For multi-cell series configurations (2S or higher), passive or active balancing circuits ensure cells remain within 50 mV of each other
- **Temperature cutoffs:** Charging inhibited below 0 degC and above 45 degC (Li-ion charging below 0 degC causes lithium plating)

**CubeSat standard:** Most commercial EPS boards (GomSpace P31u, Endurosat, AAC Clyde) use MPPT + regulated bus with 3.3 V and 5 V rails, plus an unregulated battery rail (6.0--8.4 V for 2S Li-ion).

---

## 2. Solar Array Sizing
> **Key Equations -- Solar Array Sizing (Full Derivation)**
>
> **Step 1: Orbit-average power demand:**
> $$P_{\text{avg}} = \sum_{\text{modes}} P_{\text{mode}} \times f_{\text{duty,mode}}$$
>
> This is computed from the ConOps mode table. For each mode (imaging, downlink, eclipse/safe, idle), multiply the mode power by the fraction of orbit spent in that mode.
>
> **Step 2: SA end-of-life power requirement:**
>
> During sunlight, the SA must simultaneously: (a) power all sunlit loads and (b) recharge the battery for the upcoming eclipse. The recharge power accounts for battery charge/discharge efficiency:
>
> $$P_{\text{SA,EOL}} = P_{\text{peak,sunlight}} + \frac{P_{\text{eclipse}} \times t_{\text{eclipse}}}{t_{\text{sunlight}} \times \eta_{\text{path,eclipse}}}$$
>
> where $\eta_{\text{path,eclipse}} = \eta_{\text{charge}} \times \eta_{\text{discharge}} \times \eta_{\text{regulator}}$.
>
> For a typical CubeSat EPS: $\eta_{\text{charge}} \approx 0.92$ (Li-ion coulombic efficiency $\times$ charge regulator), $\eta_{\text{discharge}} \approx 0.95$ (battery internal resistance losses), $\eta_{\text{regulator}} \approx 0.90$ (DC-DC converter). Combined: $\eta_{\text{path,eclipse}} \approx 0.79$.
>
> A simpler approximation uses $\eta_{\text{charge}} \approx 0.90$ as a lumped path efficiency, which is common in textbooks but slightly optimistic.
>
> **Step 3: Account for degradation and temperature:**
> $$P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{L_d \times L_T}$$
>
> where:
> - $L_d = (1 - \delta)^n$ is the radiation degradation factor ($\delta = 0.025$/yr for TJ GaAs in LEO)
> - $L_T = 1 + \beta(T_{\text{cell}} - T_{\text{ref}})$ is the temperature derating factor ($\beta = -0.0019$/degC, $T_{\text{ref}} = 28$ degC, $T_{\text{cell}}$ typically 60--80 degC in LEO)
>
> For a cell operating at 65 degC: $L_T = 1 + (-0.0019)(65 - 28) = 1 - 0.070 = 0.930$ (7% power loss from temperature).
>
> **Step 4: Compute SA area:**
> $$A_{\text{SA}} = \frac{P_{\text{SA,BOL}}}{\eta_{\text{cell}} \times S \times \cos(\theta) \times f_{\text{pack}} \times f_{\text{cover}}}$$
> where:
> - $\eta_{\text{cell}} = 0.295$ (triple-junction GaAs efficiency at AM0, 28 degC -- STC rating)
> - $S = 1361$ W/m$^2$ (solar constant at 1 AU, per [Kopp & Lean 2011](https://doi.org/10.1029/2010GL045777))
> - $\theta$ = sun incidence angle (0 deg for ideal tracking; for body-mounted, use orbit-averaged $\cos\theta$)
> - $f_{\text{pack}} = 0.85$--$0.90$ (cell packing factor -- fraction of panel area covered by cells; gaps exist for cell interconnects, edge clearance, and harness routing)
> - $f_{\text{cover}} = 0.97$ (cover glass transmission loss, typically 2--4%)
>
> **Step 5: SA mass:**
> $$m_{\text{SA}} = A_{\text{SA}} \times \sigma_{\text{SA}} + m_{\text{mechanism}}$$
> where $\sigma_{\text{SA}}$ = areal density of the panel:
> - Body-mounted (cells on Al substrate): $\sigma \approx 2.0$--$2.5$ kg/m$^2$
> - Rigid deployable (cells on Al honeycomb/CFRP panel): $\sigma \approx 1.5$--$2.0$ kg/m$^2$
> - Flexible deployable (roll-out or fold-out): $\sigma \approx 0.8$--$1.2$ kg/m$^2$
> - $m_{\text{mechanism}}$ = hinge, spring, hold-down mechanism: typically 0.1--0.3 kg per panel for CubeSats

> **Worked Example -- 3U EO CubeSat (SuperDove-class) Solar Array**
>
> **Given:** $P_{\text{peak,sunlight}} = 10.0$ W (imaging mode), $P_{\text{eclipse}} = 3.5$ W, $t_{\text{eclipse}} = 35$ min, $t_{\text{sunlight}} = 60$ min, mission lifetime = 3 years, cell temperature = 65 degC, single deployable panel with fixed sun angle $\theta = 23$ deg (average over orbit for SSO with body-fixed panel).
>
> **Step 2:** Recharge power (using detailed path efficiency):
> $\eta_{\text{path}} = 0.92 \times 0.95 \times 0.90 = 0.786$
>
> $P_{\text{recharge}} = \frac{3.5 \times 35}{60 \times 0.786} = \frac{122.5}{47.2} = 2.60$ W
>
> $P_{\text{SA,EOL}} = 10.0 + 2.60 = 12.60$ W
>
> **Step 3:** BOL accounting for 3-year degradation + temperature:
> $L_d = (1 - 0.025)^3 = 0.9269$
>
> $L_T = 1 + (-0.0019)(65 - 28) = 0.930$
>
> $P_{\text{SA,BOL}} = \frac{12.60}{0.9269 \times 0.930} = \frac{12.60}{0.862} = 14.62$ W
>
> **Step 4:** SA area:
> $A_{\text{SA}} = \frac{14.62}{0.295 \times 1361 \times \cos(23\degree) \times 0.85 \times 0.97}$
>
> $= \frac{14.62}{0.295 \times 1361 \times 0.921 \times 0.85 \times 0.97}$
>
> $= \frac{14.62}{305.0} = 0.0479$ m$^2$
>
> This is approximately 22 cm x 22 cm -- achievable with a single deployable panel on a 3U CubeSat (the MMA HaWK panel provides up to 0.06 m$^2$ per wing).
>
> **Step 5:** SA mass (deployable, rigid):
> $m_{\text{SA}} = 0.0479 \times 1.8 + 0.15 = 0.086 + 0.15 = 0.24$ kg (panel + mechanism)
>
> **Comparison to Planet SuperDove:** The actual SuperDove uses body-mounted cells plus two deployable wings, achieving ~25 W BOL. Our calculation (14.6 W BOL from one panel) is consistent -- SuperDove's higher power supports continuous imaging plus S-band downlink simultaneously.

### CubeSat SA Power Reference

| Configuration | 1U | 3U | 6U | 12U |
|--------------|-----|-----|-----|------|
| Body-mounted only | ~2 W | ~7 W | ~12 W | ~20 W |
| Single deployable | ~4 W | ~15 W | ~30 W | ~55 W |
| Dual deployable | -- | ~25 W | ~48 W | ~100 W |
| Quad deployable | -- | -- | ~80 W | ~180 W |

*[Source: GomSpace, ISIS, MMA Design vendor datasheets; ASTERIA 6U confirmed 48 W BOL; Dove/SuperDove confirmed ~25 W]*

---

## 3. Battery Sizing
### Li-ion Cell Chemistry and Physics

All modern spacecraft batteries use lithium-ion (Li-ion) chemistry. During discharge, lithium ions migrate from the graphite anode (negative electrode) through an organic electrolyte and polymer separator to the lithium metal oxide cathode (positive electrode), while electrons flow through the external circuit doing work. During charging, the process reverses.

**Common cathode chemistries used in space:**

| Chemistry | Cathode | Nominal Voltage | Energy Density | Cycle Life (30% DOD) | Thermal Stability | Space Heritage |
|-----------|---------|----------------|---------------|----------------------|-------------------|----------------|
| **LCO** (LiCoO$_2$) | Cobalt oxide | 3.7 V | 150--200 Wh/kg | ~10,000 | Moderate | ISS, many CubeSats (18650 cells) |
| **NMC** (LiNiMnCoO$_2$) | Nickel-manganese-cobalt | 3.7 V | 170--250 Wh/kg | ~5,000 | Moderate | Growing heritage |
| **LFP** (LiFePO$_4$) | Iron phosphate | 3.2 V | 90--120 Wh/kg | ~50,000 | Excellent | Niche (when cycle life is paramount) |
| **NCA** (LiNiCoAlO$_2$) | Nickel-cobalt-aluminium | 3.6 V | 200--260 Wh/kg | ~3,000 | Lower | Limited space heritage |

*[Source: Ratnakumar et al., NASA JPL; Saft VES-16 space cell datasheet; Samsung SDI 18650 specifications]*

**Cell form factors:**

- **18650 cylindrical:** 18 mm diameter, 65 mm long. The workhorse of CubeSat missions. Common cells: Samsung 25R (2500 mAh, 20A continuous), Panasonic NCR18650B (3350 mAh, moderate rate), Sony VTC6 (3000 mAh, high rate). Energy: 9--12 Wh per cell.
- **Pouch cells:** Custom dimensions, higher energy density (~250 Wh/kg) but require external structural support. Used in some 6U+ missions and all large spacecraft. GomSpace NanoPower BPX uses pouch cells.
- **Prismatic cells:** Rigid case, intermediate between cylindrical and pouch. Used in some mission-specific designs.

**Cell configuration:**

Cells are arranged in series (S) to increase voltage and parallel (P) to increase capacity:
- **1S (single cell):** 3.0--4.2 V bus. Used for very simple 1U CubeSats.
- **2S (two in series):** 6.0--8.4 V bus. Standard for most CubeSats (matches GomSpace P31u default).
- **2S2P (two series, two parallel):** 6.0--8.4 V bus, double capacity. Used for higher-energy missions (e.g., GomSpace BP4 pack: 4 cells, 2S2P, ~38 Wh).

**Protection circuits:** Every flight battery pack includes:
- **Cell voltage monitoring:** Per-cell voltage measurement to detect over/under-voltage
- **Over-current protection:** Current-sense resistors + MOSFET switches to disconnect at overcurrent (prevents short-circuit thermal runaway)
- **Temperature monitoring:** Thermistors on each cell; inhibit charging below 0 degC and above 45 degC
- **Heater circuit:** Kapton heater on battery pack, thermostatically controlled, to maintain cells above minimum charging temperature during eclipse

**Capacity fade model:** Li-ion cells lose capacity over time due to solid electrolyte interphase (SEI) growth on the anode. A simplified calendar + cycling fade model:

$$C(t, N) = C_0 \times (1 - \alpha \sqrt{t}) \times (1 - \beta \cdot N \cdot DOD^{\gamma})$$

where $C_0$ = initial capacity, $t$ = time (years), $N$ = number of cycles, $\alpha \approx 0.02$ (calendar fade), $\beta \approx 3 \times 10^{-6}$, $\gamma \approx 2.1$ (cycling fade). For LEO at 30% DOD, this gives approximately 5--8% capacity loss per year -- consistent with flight data from ISS battery replacements and CubeSat fleet telemetry.

> **Key Equations -- Battery Sizing**
>
> **Required battery energy:**
> $$E_{\text{bat}} = \frac{P_{\text{eclipse}} \times t_{\text{eclipse}}}{DOD \times \eta_{\text{discharge}}}$$
> where:
> - $DOD$ = maximum depth of discharge
> - $\eta_{\text{discharge}} = 0.95$ (discharge efficiency, accounting for internal resistance $I^2R$ losses)
> - $t_{\text{eclipse}}$ in hours
>
> **Battery mass:**
> $$m_{\text{bat}} = \frac{E_{\text{bat}}}{e_{\text{specific}}}$$
> where $e_{\text{specific}} = 150$--$200$ Wh/kg for packaged Li-ion 18650 cells (cell-level energy density is higher, but packaging adds ~30% mass).
>
> **Cycle life vs DOD relationship** (Li-ion 18650, LCO chemistry):
>
> | DOD | Typical Cycle Life | Suitable Mission Duration | Annual Eclipses (LEO, 15/day) |
> |-----|-------------------|--------------------------|-------------------------------|
> | 80% | ~500 cycles | < 1 month | 450 |
> | 50% | ~2,000 cycles | < 4 months | 1,800 |
> | 30% | ~10,000 cycles | 1--2 years | 5,475 |
> | 20% | ~30,000 cycles | 3--5 years | 10,950 |
> | 10% | ~100,000 cycles | > 7 years | 38,325 |
>
> **Design rule of thumb:** For a multi-year LEO mission, start with 20--30% DOD. For a short technology demonstration (< 6 months), 40--50% DOD is acceptable and significantly reduces battery size/mass/cost.

> **Worked Example -- Battery for 3U EO CubeSat (SuperDove-class)**
>
> **Given:** $P_{\text{eclipse}} = 3.5$ W, $t_{\text{eclipse}} = 35$ min $= 0.583$ h, $DOD = 0.25$ (conservative for 3-year mission), $\eta = 0.95$.
>
> **Step 1 -- Required battery energy:**
> $E_{\text{bat}} = \frac{3.5 \times 0.583}{0.25 \times 0.95} = \frac{2.04}{0.2375} = 8.59$ Wh
>
> **Step 2 -- Apply ECSS margin (20% at Phase A/B):**
> $E_{\text{bat,spec}} \geq 8.59 \times 1.20 = 10.3$ Wh. Specify **minimum 10 Wh**, ideally **20 Wh** for operational flexibility.
>
> **Step 3 -- Verify cycle life:**
> 3-year mission at 15 orbits/day = 16,425 eclipses. At 25% DOD, Li-ion 18650 cells provide ~20,000 cycles. **Margin = 22%. Pass.**
>
> Including capacity fade: after 3 years, ~15--20% capacity loss from calendar + cycling aging. Effective DOD increases to $0.25 / 0.82 = 0.30$ -- still within the 10,000-cycle regime. **Acceptable with monitoring.**
>
> **Step 4 -- Battery mass:**
> $m_{\text{bat}} = \frac{20}{170} = 0.118$ kg (using 170 Wh/kg for packaged 18650 cells)
>
> **Step 5 -- Battery volume:**
> Two 18650 cells in 2S1P: $2 \times 18\text{mm} \times 65\text{mm} = $ approximately 34 mL, fitting easily within a 3U stack.
>
> **Comparison to Planet SuperDove:** SuperDove carries approximately 20 Wh in a 2S2P configuration (4 cells), consistent with our sizing. The actual operating DOD is estimated at 10--15% per eclipse, giving substantial cycle-life margin for the multi-year constellation replenishment cadence.

**Failure modes to watch for:**
- **Thermal runaway:** If a cell is overcharged, mechanically damaged, or experiences an internal short, the exothermic decomposition of the cathode material can lead to thermal runaway (self-heating > heat dissipation), potentially reaching 600+ degC. Mitigation: cell-level fuses, per-cell voltage monitoring, thermal cutoffs.
- **Lithium plating:** Charging below 0 degC causes metallic lithium to deposit on the anode surface rather than intercalating into graphite. This is irreversible, reduces capacity, and can cause internal shorts. Mitigation: battery heater + thermostat + software lockout.
- **Capacity imbalance:** In series configurations, the weakest cell limits the pack. If cells age at different rates, the weakest cell hits under-voltage lockout while others still have capacity. Mitigation: cell balancing circuits, matched cell lots.

---

## 4. Thermal Control System
*[Source: ECSS-E-ST-31C; Gilmore, Ch. 1--4; SMAD, Ch. 11.5]*

### The Physics of Spacecraft Thermal Control

Spacecraft thermal control is fundamentally different from terrestrial thermal engineering because **there is no convection in vacuum**. The only heat transfer mechanisms are:

1. **Conduction:** Heat flow through solid material, governed by Fourier's law: $\dot{Q} = -kA \frac{dT}{dx}$. Critical within the spacecraft structure and between components and mounting surfaces.
2. **Radiation:** Heat transfer via electromagnetic radiation, governed by the Stefan-Boltzmann law: $\dot{Q} = \varepsilon \sigma A T^4$. This is the **only** mechanism for rejecting heat to the environment.

There is no convective cooling. A component that overheats cannot be cooled by a fan. All waste heat must be conducted to a radiating surface and then radiated to space. This is the central constraint of spacecraft thermal design.

### Thermal Environment in LEO

A spacecraft in LEO experiences four thermal inputs and one thermal sink:

| Source | Flux | Direction | Variability |
|--------|------|-----------|-------------|
| **Direct solar** | $S = 1361 \pm 1$ W/m$^2$ (at 1 AU) | Sun-facing surfaces only | Seasonal ($\pm 3.3$% due to Earth's orbital eccentricity: $S_{\text{perihelion}} = 1414$ W/m$^2$ in January, $S_{\text{aphelion}} = 1322$ W/m$^2$ in July) |
| **Earth albedo** | $\alpha_E \times S \approx 0.30 \times 1361 \approx 408$ W/m$^2$ | Earth-facing surfaces (nadir) | Varies with cloud cover, surface type (0.06 for ocean to 0.80 for fresh snow); orbit-average range 0.25--0.35 |
| **Earth infrared** | $q_{\text{IR}} \approx 240$ W/m$^2$ (orbit average) | Earth-facing surfaces (nadir) | Range 200--270 W/m$^2$ depending on latitude, season, cloud cover |
| **Internal dissipation** | $Q_{\text{int}} = P_{\text{dissipated}}$ | From electronics waste heat | Varies with operational mode; nearly all electrical power eventually becomes heat |
| **Deep space** (sink) | $T_{\text{space}} \approx 2.7$ K (CMB) | Zenith-facing radiator surfaces | Effectively 0 K for engineering purposes |

### View Factors

The fraction of a surface's radiative "view" that sees each thermal source is critical for accurate thermal modelling. For a nadir-pointing spacecraft in LEO:

$$F_{\text{Earth}} = \frac{1}{1 + (h/R_E)^2 + 2(h/R_E)}$$

where $h$ = altitude (km) and $R_E = 6371$ km. For a 500 km orbit: $F_{\text{Earth}} = 1 / (1 + (500/6371)^2 + 2 \times 500/6371) = 1 / 1.163 = 0.860$. The nadir face sees 86% Earth and 14% deep space. The zenith face sees 100% deep space (assuming no S/C self-shadowing). Side faces see a mix.

At higher altitudes, $F_{\text{Earth}}$ decreases: at 800 km it is 0.79, at 35,786 km (GEO) it is only 0.018 -- which is why GEO thermal design is dominated by solar flux and internal dissipation, not Earth IR/albedo.

### Thermal Balance Equation -- Full Derivation

> **Key Equations -- Thermal Equilibrium**
>
> At steady state, the absorbed heat equals the radiated heat:
>
> $$Q_{\text{in}} = Q_{\text{out}}$$
>
> **Absorbed heat (expanded):**
>
> $$Q_{\text{in}} = \underbrace{\alpha_s \cdot A_{\text{sun}} \cdot S}_{\text{direct solar}} + \underbrace{\alpha_s \cdot A_{\text{alb}} \cdot F_{\text{alb}} \cdot \alpha_E \cdot S}_{\text{Earth albedo}} + \underbrace{\varepsilon \cdot A_{\text{IR}} \cdot F_{\text{IR}} \cdot q_{\text{IR}}}_{\text{Earth IR}} + \underbrace{Q_{\text{int}}}_{\text{internal dissipation}}$$
>
> **Radiated heat:**
>
> $$Q_{\text{out}} = \varepsilon \cdot \sigma \cdot A_{\text{rad}} \cdot T^4$$
>
> where:
> - $\alpha_s$ = solar absorptance of surface coating (dimensionless, 0--1)
> - $\varepsilon$ = infrared emittance of surface coating (dimensionless, 0--1)
> - $\sigma = 5.670 \times 10^{-8}$ W/m$^2$/K$^4$ (Stefan-Boltzmann constant)
> - $A_{\text{sun}}$, $A_{\text{alb}}$, $A_{\text{IR}}$, $A_{\text{rad}}$ = projected areas for each flux (m$^2$)
> - $F_{\text{alb}}$, $F_{\text{IR}}$ = view factors to Earth for albedo and IR surfaces
> - $T$ = equilibrium temperature (K)
>
> **Note on $\alpha_s$ vs $\varepsilon$:** Solar absorptance ($\alpha_s$) is measured over the solar spectrum (0.2--2.5 um, peak at 0.5 um visible). Infrared emittance ($\varepsilon$) is measured over the thermal IR spectrum (3--50 um, peak at ~10 um for room-temperature objects). These are **different spectral ranges**, so $\alpha_s \neq \varepsilon$ for most real surfaces. This decoupling is the basis of all passive thermal control: by choosing the $\alpha_s / \varepsilon$ ratio, the designer controls the equilibrium temperature.
>
> **Solving for equilibrium temperature:**
> $$T = \left(\frac{Q_{\text{absorbed}} + Q_{\text{internal}}}{\varepsilon \sigma A_{\text{rad}}}\right)^{1/4}$$
>
> This equation is valid only for a single isothermal node (lumped-parameter model). For multi-node thermal models (which are needed for any real spacecraft), the heat balance is solved simultaneously for all nodes using numerical methods (Thermal Desktop, ESATAN, or similar thermal analysis software).

### Hot Case and Cold Case

| Case | Conditions | Design Concern |
|------|-----------|----------------|
| **Hot case** | Maximum solar exposure ($S = 1414$ W/m$^2$, perihelion), all subsystems active (max $Q_{\text{int}}$), worst sun angle (max $A_{\text{sun}}$), BOL coatings ($\alpha_s$ at minimum -- fresh white paint), max albedo (0.35) | Components exceed maximum operating temperature |
| **Cold case** | Eclipse (no solar), minimum power dissipation (safe mode, min $Q_{\text{int}}$), EOL coatings ($\alpha_s$ increased by UV darkening), minimum Earth IR (200 W/m$^2$), deep space view | Components fall below minimum operating temperature |

**Design philosophy:** The thermal engineer designs to keep all components within their qualified temperature range under both worst-case hot and worst-case cold conditions, with ECSS-mandated margins applied.

### Surface Coatings -- The Passive Thermal Toolbox

| Coating | $\alpha_s$ (BOL) | $\alpha_s$ (EOL, 5 yr LEO) | $\varepsilon$ | $\alpha_s / \varepsilon$ (BOL) | Use Case |
|---------|-----------|---------------------------|--------------|------------------------|----------|
| White paint (AZ-93, S13G-LO) | 0.14--0.20 | 0.25--0.35 | 0.89--0.92 | 0.16--0.22 | Radiator surfaces (stay cool; low solar absorption, high IR emission) |
| Black paint (Aeroglaze Z306) | 0.95 | 0.95 | 0.89 | 1.07 | Internal surfaces (maximise radiative exchange between components) |
| Gold tape (2 mil Kapton + VDA) | 0.22--0.25 | 0.25--0.30 | 0.03--0.05 | 5.0--7.5 | MLI outer layer, thermal isolation |
| Bare aluminium (polished) | 0.10--0.15 | 0.15--0.20 | 0.03--0.05 | 2.5--4.0 | Reflective surfaces, low emissivity |
| Alodine (chromate conversion on Al) | 0.35--0.40 | 0.40--0.50 | 0.12--0.16 | 2.5--3.0 | Moderate thermal control, structural surfaces |
| Anodised aluminium (clear or black) | 0.30--0.50 | 0.35--0.55 | 0.75--0.86 | 0.4--0.65 | CubeSat external structure (standard finish per CDS) |
| MLI blanket (effective) | 0.05--0.15 | 0.10--0.20 | 0.02--0.05 | ~3 | Thermal isolation of sensitive components |
| Solar cells (with cover glass) | 0.75--0.92 | 0.78--0.92 | 0.80--0.85 | ~1.0 | SA surfaces (high absorption is unavoidable; cells get hot) |
| OSR (Optical Solar Reflector) | 0.05--0.08 | 0.08--0.12 | 0.78--0.80 | 0.06--0.10 | High-performance radiators (large S/C, GEO) |

**Key design insight:** A surface with low $\alpha_s / \varepsilon$ (e.g., white paint: 0.2) stays cool because it reflects most solar energy but efficiently radiates thermal IR. A surface with high $\alpha_s / \varepsilon$ (e.g., gold tape: 6.0) stays warm because it absorbs solar energy but barely radiates. This is why white paint is used on radiators and gold/MLI is used for insulation.

**Coating degradation:** UV radiation darkens most white paints over time, increasing $\alpha_s$ while leaving $\varepsilon$ nearly unchanged. This means $\alpha_s / \varepsilon$ increases, and the surface gets hotter at EOL. The thermal engineer must design the hot case with BOL coatings (which give the highest $\alpha_s$... wait -- actually BOL white paint has the *lowest* $\alpha_s$, so the **cold case** is more conservative at BOL, and the **hot case** is more conservative at EOL when $\alpha_s$ has increased. This is a common source of confusion: BOL coatings give a colder cold case; EOL coatings give a hotter hot case.

### MLI (Multi-Layer Insulation) -- Construction and Physics

MLI blankets are the most common thermal insulation on spacecraft. They work by minimising both radiation and conduction heat transfer through multiple reflective layers separated by low-conductance spacers.

**Construction (typical MLI blanket):**
1. **Outer cover:** 1 mil (25 um) aluminised Kapton (VDA -- Vapour Deposited Aluminium on one side). Provides mechanical protection and low solar absorptance.
2. **Inner reflective layers:** 10--20 layers of 0.25 mil (6 um) double-aluminised Mylar (DAM). Each layer reflects IR radiation, and the vacuum gaps between layers have zero convection.
3. **Spacer material:** Dacron or Nomex netting between each DAM layer, preventing conductive contact between adjacent reflective sheets.
4. **Inner cover:** 1 mil aluminised Kapton, protecting the inner layers.

**Effective emissivity:** An ideal MLI blanket with $N$ reflective layers has an effective emissivity of:

$$\varepsilon_{\text{eff}} = \frac{1}{2/\varepsilon_{\text{inner}} + (N-1)(2/\varepsilon_{\text{layer}} - 1)}$$

For 20 layers of DAM ($\varepsilon_{\text{layer}} = 0.03$): $\varepsilon_{\text{eff}} \approx 0.002$. In practice, real MLI achieves $\varepsilon_{\text{eff}} = 0.01$--$0.03$ due to seams, penetrations (harness, mounting), and edge effects. The ratio of actual to theoretical performance is typically 2--5x worse.

**CubeSat MLI challenges:** CubeSats have limited surface area and many penetrations (connectors, antennas, sensors, solar cells), making it difficult to achieve good MLI performance. Most CubeSats in LEO do not use MLI -- they rely on the moderate thermal environment (Earth IR provides a "warm floor") and surface coatings. MLI becomes essential for deep-space CubeSats (e.g., MarCO, CAPSTONE) or missions with sensitive payloads (IR detectors, laser systems).

### Heater Sizing

When passive thermal control cannot prevent a component from falling below its minimum temperature (typically during eclipse or safe mode), electrical heaters are required.

> **Key Equations -- Heater Sizing**
>
> **Required heater power** (to maintain minimum temperature during worst cold case):
>
> $$P_{\text{heater}} = \varepsilon \sigma A_{\text{rad}} T_{\text{min}}^4 - Q_{\text{environment,cold}} - Q_{\text{internal,cold}}$$
>
> where $T_{\text{min}}$ is the minimum allowable temperature of the component (converted to Kelvin).
>
> **Heater types for CubeSats:**
> - **Kapton foil heaters:** Etched-foil resistance elements laminated between Kapton sheets. Flexible, thin (0.2--0.5 mm), lightweight (2--10 g each). Typical power: 0.5--5 W per heater. Bond directly to component surface with pressure-sensitive adhesive.
> - **Cartridge heaters:** Cylindrical, inserted into drilled holes. Higher power density but heavier and less common on CubeSats.
>
> **Thermostat control:** Simple bimetallic thermostats (e.g., Honeywell Klixon) switch heaters on/off at set temperatures (e.g., on at -5 degC, off at +5 degC). Mass: ~2 g each. For higher reliability, software-controlled heaters using temperature sensor feedback and EPS switches are preferred on modern CubeSats -- but this requires OBC to be running, which may not be the case in safe mode.

### Heat Pipes and Thermal Straps

**Heat pipes** are passive two-phase heat transfer devices that transport large amounts of thermal energy with very small temperature differences. They are widely used on larger spacecraft and are beginning to appear on 6U+ CubeSats.

**How a heat pipe works:**
1. Working fluid (ammonia, methanol, or water) evaporates at the hot end (evaporator), absorbing latent heat
2. Vapour travels through the hollow pipe core to the cold end (condenser)
3. At the condenser, vapour releases latent heat and condenses back to liquid
4. Liquid returns to the evaporator via capillary action in a wick structure (sintered metal, axial grooves, or screen mesh)
5. The process is continuous, passive (no moving parts, no power), and can transport 10--100 W across 20--50 cm with < 5 degC temperature difference

**Thermal conductance of a heat pipe:** Effective thermal conductivity is 10,000--100,000 W/m/K (compared to copper at 400 W/m/K and aluminium at 237 W/m/K). A 6 mm diameter ammonia heat pipe can transport ~30 W over 30 cm with < 3 degC gradient.

**Thermal straps** are flexible conductive links (braided copper, graphite fibre, or pyrolytic graphite sheet) used to conduct heat between components that cannot be rigidly connected (e.g., across a hinge or between a vibration-isolated payload and the spacecraft bus). Typical conductance: 0.5--5 W/K.

| Heat Transport Method | Conductance | Mass | Power | Orientation Sensitivity | CubeSat Use |
|----------------------|-------------|------|-------|------------------------|------------|
| Aluminium conduction | ~0.5--2 W/K per path | Part of structure | 0 W | None | Always (inherent) |
| Copper thermal strap | 1--5 W/K | 10--50 g | 0 W | None | Occasional (6U+) |
| Heat pipe (ammonia) | 5--50 W/K | 20--100 g | 0 W | Gravity-dependent (must test in relevant orientation) | Rare (6U+, some 3U) |
| Pumped fluid loop | 50--500 W/K | 500+ g | 5--20 W | None | Large S/C only |

### Thermal Control Methods Summary

| Method | Type | Mass Impact | Typical Use | Key Design Parameter |
|--------|------|-------------|------------|---------------------|
| **Surface coatings** | Passive | Negligible | Always -- select $\alpha_s/\varepsilon$ ratio per face | $\alpha_s/\varepsilon$ ratio |
| **MLI blankets** | Passive | 0.5--2.0 kg/m$^2$ | Insulate sensitive components from environment | Number of layers, $\varepsilon_{\text{eff}}$ |
| **Radiators** | Passive | Part of structure | Reject internal waste heat to deep space | Radiator area, $\varepsilon$, view to space |
| **Heaters** | Active | 0.005--0.02 kg each | Maintain minimum temp during eclipse/safe mode | Power, thermostat set point |
| **Heat pipes** | Passive | 0.02--0.10 kg each | Transport heat from source to radiator | Working fluid, $Q_{\text{max}}$, orientation |
| **Thermal straps** | Passive | 0.01--0.05 kg each | Flexible conductive link across joints/hinges | Conductance (W/K) |
| **Louvers** | Active | 0.1--0.5 kg | Variable-conductance radiators (rare on CubeSats) | Open/close temperature range |

### ECSS Thermal Margins

*[Source: ECSS-E-ST-31C, Table 5-1]*

| Phase | Hot Margin (above predicted max) | Cold Margin (below predicted min) |
|-------|----------------------------------|-----------------------------------|
| **Qualification** | Predicted + 15 degC | Predicted - 15 degC |
| **Acceptance** | Predicted + 10 degC | Predicted - 10 degC |
| **Operating** | Predicted + 5 degC | Predicted - 5 degC |

These margins ensure that thermal model uncertainties (typically $\pm 5$--$10$ degC for simplified models, $\pm 2$--$5$ degC for detailed correlated models) do not cause in-orbit temperature exceedances.

> **Worked Example -- 3U CubeSat Full Thermal Analysis**
>
> **Hot case (sunlit, all systems active, perihelion, EOL coatings):**
>
> Simplified single-node model. 3U CubeSat, nadir-pointing.
>
> - Sun-facing area ($+Z$, zenith-facing 3U panel): $A_{\text{sun}} = 0.034$ m$^2$
> - SA surfaces (sun-facing): $\alpha_s = 0.85$, $\varepsilon = 0.82$ (solar cell properties)
> - Nadir face ($-Z$): $A_{\text{nadir}} = 0.034$ m$^2$, anodised Al ($\alpha_s = 0.45$ EOL, $\varepsilon = 0.82$)
> - Side faces (4x): $A_{\text{side}} = 4 \times 0.01$ m$^2$ = $0.04$ m$^2$, anodised Al
> - Internal dissipation (imaging mode): $Q_{\text{int}} = 10.0$ W
>
> $Q_{\text{solar}} = 0.85 \times 0.034 \times 1414 = 40.9$ W (ouch -- but much of this is captured by the SA and converted to electricity, so the net thermal input from solar cells is $Q_{\text{solar,thermal}} = \alpha_s \times A \times S \times (1 - \eta_{\text{cell}}) = 0.85 \times 0.034 \times 1414 \times 0.705 = 28.8$ W)
>
> $Q_{\text{albedo}} = 0.45 \times 0.034 \times 0.35 \times 1414 = 7.6$ W
>
> $Q_{\text{Earth IR}} = 0.82 \times 0.034 \times 270 = 7.5$ W (nadir face, hot case Earth IR)
>
> $Q_{\text{int}} = 10.0$ W (but ~12.6 W of the 10 W load power ultimately becomes heat after doing useful work)
>
> Total $Q_{\text{in}} \approx 28.8 + 7.6 + 7.5 + 10.0 = 53.9$ W
>
> Total radiating area (all 6 faces, minus SA area which is a net absorber): $A_{\text{rad}} \approx 0.066$ m$^2$ (accounting for partial Earth blockage on nadir face)
>
> Average emissivity: $\varepsilon_{\text{avg}} \approx 0.82$
>
> $T_{\text{hot}} = \left(\frac{53.9}{0.82 \times 5.67 \times 10^{-8} \times 0.066}\right)^{0.25} = \left(\frac{53.9}{3.07 \times 10^{-9}}\right)^{0.25}$
>
> $= (1.756 \times 10^{10})^{0.25} = 364$ K $= +91$ degC
>
> **This exceeds most component limits!** However, this simplified calculation overestimates temperature because it treats the satellite as a single isothermal node and includes solar cell thermal absorption on the zenith face. In practice:
> - The zenith face (solar cells) runs hotter than the bus
> - Internal components are conductively coupled to all faces, including the cold nadir face
> - A multi-node model typically predicts peak internal temperatures of +40 to +55 degC for this scenario
>
> **Thermal engineer's response:** If the single-node calculation exceeds 60 degC, a detailed multi-node thermal model is required. The simplified calculation is a screening tool, not a design tool.
>
> **Cold case (eclipse, safe mode, aphelion, BOL coatings):**
>
> - No solar flux, no albedo
> - Earth IR only: $Q_{\text{Earth IR}} = 0.82 \times 0.034 \times 200 = 5.58$ W (cold case: 200 W/m$^2$)
> - Internal dissipation (safe mode): $Q_{\text{int}} = 1.5$ W (OBC + heater)
> - Total $Q_{\text{in}} = 5.58 + 1.5 = 7.08$ W
>
> $T_{\text{cold}} = \left(\frac{7.08}{0.82 \times 5.67 \times 10^{-8} \times 0.070}\right)^{0.25}$
>
> $= \left(\frac{7.08}{3.26 \times 10^{-9}}\right)^{0.25} = (2.172 \times 10^{9})^{0.25} = 216$ K $= -57$ degC
>
> **This is too cold** for Li-ion batteries (min -20 degC operating, min 0 degC charging) and most COTS electronics (min -40 degC).
>
> **Action:** Add battery heater. To maintain battery at $T_{\text{min}} = -10$ degC = 263 K:
>
> Need additional heat input: $Q_{\text{heater}} = \varepsilon \sigma A_{\text{rad}} T_{\text{min}}^4 - Q_{\text{other}}$
>
> $= 0.82 \times 5.67 \times 10^{-8} \times 0.070 \times 263^4 - 7.08 = 3.26 \times 10^{-9} \times 4.78 \times 10^{9} - 7.08 = 15.6 - 7.08 = 8.5$ W
>
> **Problem:** 8.5 W heater in eclipse exceeds the battery capacity. **Resolution:** This is an isothermal whole-spacecraft calculation. In reality, the battery is inside the bus, partially insulated by the structure and surrounding boards. A targeted heater of 0.5--1.0 W directly on the battery pack, with some MLI wrapping, is typically sufficient to keep the battery above -10 degC in a 35-minute eclipse. The structure's thermal mass (aluminium at $c_p = 900$ J/kg/K) provides significant thermal inertia -- a 1 kg 1U CubeSat cooling from +20 degC at 7 W net loss drops only about 16 degC in 35 minutes.
>
> **Transient check:**
> $\Delta T = \frac{Q_{\text{net}} \times t}{m \times c_p} = \frac{(7.08 - 0) \times 35 \times 60}{5.0 \times 900} = \frac{14,868}{4500} = 3.3$ degC per 35-min eclipse
>
> Wait -- in eclipse $Q_{\text{out}} > Q_{\text{in}}$: net cooling rate = $\varepsilon \sigma A_{\text{rad}} T^4 - Q_{\text{in,eclipse}}$. At $T = 293$ K (20 degC):
>
> $Q_{\text{out}} = 0.82 \times 5.67 \times 10^{-8} \times 0.070 \times 293^4 = 3.26 \times 10^{-9} \times 7.37 \times 10^{9} = 24.0$ W
>
> $Q_{\text{net cooling}} = 24.0 - 7.08 = 16.9$ W
>
> $\Delta T = \frac{16.9 \times 2100}{5.0 \times 900} = \frac{35,490}{4500} = 7.9$ degC drop in 35 minutes
>
> So from +20 degC, the satellite cools to about +12 degC after one eclipse -- well within limits. **No heater needed for the bus; battery heater only if battery is thermally isolated from bus.**
>
> **ECSS margin check -- Payload CCD:**
> Predicted maximum temperature of payload CCD = 42 degC.
> - Operating limit = 50 degC. Margin = 50 - 42 = 8 degC > 5 degC. **Pass.**
> - Qualification test: must test at 42 + 15 = 57 degC. If qualification limit is 60 degC: **Pass.**
>
> Predicted minimum temperature of battery = -8 degC during worst eclipse.
> - Operating limit = -10 degC. Margin = -8 - (-10) = 2 degC < 5 degC. **Fail -- inadequate margin.**
> - **Action:** Add heater (0.5 W survival heater with thermostat set to -5 degC), or add MLI around battery pack.

---

### 1U Worked Example: UniSat-1

**Power Sizing: Body-Mounted Only**

UniSat-1 uses body-mounted solar cells on all five sun-exposed faces (the sixth face mounts the deployment switch interface). With no deployable panels, the power system is simpler, lighter, and cheaper -- but severely power-limited.

> **Worked Example -- UniSat-1 Solar Array Sizing**
>
> **Given:** Body-mounted cells on 5 faces of a 1U (100 x 100 mm each). ISS orbit: 400 km, 51.6 deg inclination, 92.4 min period, 56 min sunlight, 36 min eclipse. $P_{\text{eclipse}} = 0.5$ W (OBC only), $P_{\text{peak,sunlight}} = 1.2$ W (science + downlink overlap avoided by scheduling). Mission lifetime = 6 months. Cell temperature = 55 degC (body-mounted cells run cooler on 1U due to better thermal coupling to bus mass).
>
> **Step 1 -- Effective illuminated area:**
> At any given time in LEO with passive magnetic attitude (slow tumble ~1 deg/s), on average only ~1.5 faces are well-illuminated. Effective average area:
> $A_{\text{eff}} \approx 1.5 \times (0.10 \times 0.10) = 0.015$ m$^2$
>
> **Step 2 -- SA BOL power (with temperature derating):**
> $L_T = 1 + (-0.0019)(55 - 28) = 0.949$
>
> $P_{\text{SA,BOL}} = \eta_{\text{cell}} \times L_T \times S \times A_{\text{eff}} \times f_{\text{pack}} = 0.295 \times 0.949 \times 1361 \times 0.015 \times 0.80 = 4.57$ W (illuminated peak)
>
> **Step 3 -- Orbit-average power available:**
> $P_{\text{avg,avail}} = P_{\text{SA,BOL}} \times \frac{t_{\text{sun}}}{T} \times \eta_{\text{EPS}} = 4.57 \times \frac{56}{92.4} \times 0.85 = 2.35$ W
>
> After 6-month degradation ($(1 - 0.025)^{0.5} = 0.987$):
> $P_{\text{avg,EOL}} = 2.35 \times 0.987 = 2.32$ W
>
> **Step 4 -- Power demand (orbit-average):**
> From Session 2.4: $P_{\text{avg,demand}} = 0.68$ W.
>
> **Power margin:** $2.32 - 0.68 = 1.64$ W (**71% margin**). Even with conservative geometry assumptions, the link closes comfortably.
>
> **Note on body-mounted vs tumbling:** The key uncertainty in 1U body-mounted power is the attitude. With passive magnetic stabilisation, the satellite aligns roughly with Earth's magnetic field, providing more predictable illumination than a random tumble. However, the effective area varies significantly around the orbit as the B-field direction changes with latitude. The 1.5-face average is conservative. A Monte Carlo simulation of illumination geometry over many orbits typically yields a more optimistic 1.7--1.9 effective face average.

> **Worked Example -- UniSat-1 Battery Sizing**
>
> **Given:** $P_{\text{eclipse}} = 0.5$ W, $t_{\text{eclipse}} = 36$ min $= 0.60$ h, $DOD = 0.50$ (acceptable for 6-month mission: ~2,740 cycles), $\eta = 0.95$.
>
> $E_{\text{bat}} = \frac{0.5 \times 0.60}{0.50 \times 0.95} = \frac{0.30}{0.475} = 0.63$ Wh
>
> With margin: specify minimum **10 Wh** (standard GomSpace NanoPower P31u battery pack -- this is the smallest available COTS battery with flight heritage).
>
> **Cycle count check:** 6 months at 15 orbits/day = 2,740 eclipses. At 50% DOD, Li-ion cells comfortably survive > 2,000 cycles. **Pass.**
>
> **Actual operating DOD:** With 10 Wh battery and 0.63 Wh per eclipse demand, actual DOD = 0.63 / 10 = **6.3%** per eclipse. At this DOD, cycle life exceeds 100,000 cycles. **Battery degradation is negligible** over the 6-month mission.
>
> **Key insight:** The 10 Wh battery is massively oversized for the actual eclipse demand. This is common in 1U missions -- the minimum COTS battery available provides far more capacity than needed. The excess capacity provides excellent margin and enables recovery from anomalies (multiple missed sunlit periods).

**Thermal: Passive Only**

UniSat-1 uses no heaters, no MLI, and no active thermal control. This is justified by three factors:

1. **Low altitude (400 km):** Strong Earth IR flux (~240 W/m$^2$) provides a warm floor, preventing extreme cold cases
2. **Short mission (6 months):** No long-term coating degradation to worry about
3. **Tolerant components:** COTS electronics typically operate from -20 degC to +60 degC; the 400 km LEO thermal environment stays within -10 degC to +45 degC for a 1U with standard aluminium/anodised surfaces

> **Quick Thermal Check -- UniSat-1 Cold Case (Transient)**
>
> Worst eclipse, all subsystems off except OBC (0.5 W internal dissipation):
> - Earth IR absorbed: $\varepsilon \times A_{\text{nadir}} \times q_{\text{IR}} = 0.85 \times 0.01 \times 240 = 2.04$ W
> - Internal dissipation: 0.5 W
> - Total heat in: 2.54 W
>
> Steady-state temperature (if eclipse were infinite):
> $T_{\text{steady}} = (2.54 / (0.85 \times 5.67 \times 10^{-8} \times 0.045))^{0.25} = 195$ K $= -78$ degC
>
> **This looks alarming** -- but the eclipse is only 36 minutes, and the thermal mass prevents the satellite from reaching steady state.
>
> **Transient analysis:** Starting at $T_0 = +15$ degC (293 K) at eclipse entry:
>
> Net cooling rate at 293 K: $Q_{\text{rad,out}} = 0.85 \times 5.67 \times 10^{-8} \times 0.045 \times 293^4 = 2.17 \times 10^{-9} \times 7.37 \times 10^{9} = 16.0$ W
>
> Net cooling: $16.0 - 2.54 = 13.5$ W
>
> Temperature drop: $\Delta T = \frac{Q_{\text{net}} \times t}{m \times c_p} = \frac{13.5 \times 36 \times 60}{1.0 \times 900} = \frac{29,160}{900} = 32$ degC
>
> But this is a linear approximation -- as the satellite cools, the radiation rate drops as $T^4$, so the actual cooling slows. A more accurate estimate gives $\Delta T \approx 20$--$25$ degC, resulting in a minimum temperature of about $-5$ to $-10$ degC.
>
> **Conclusion:** The 1U at 400 km reaches approximately -5 to -10 degC during worst-case eclipse, starting from a warm sunlit entry. This is within COTS operating limits (-20 degC to +60 degC for most components) and within battery operating range (-20 degC to +60 degC for discharge). **No heaters needed.** The ISS orbit's relatively short eclipse (36 min vs 35 min for SSO) and the strong Earth IR flux at 400 km make passive thermal control viable for a 1U mission.

---

## 5. Real Mission Examples
### Planet SuperDove EPS

| Parameter | Value | Design Rationale |
|-----------|-------|-----------------|
| Form factor | 3U+, ~5 kg | Flock constellation; P-POD compatible |
| SA configuration | Body-mounted + two deployable wings | ~25 W BOL needed for continuous imaging + S-band downlink |
| SA cells | Triple-junction GaAs (Spectrolab or SolAero) | Standard space-grade, 29.5% AM0 |
| Battery | Li-ion, ~20 Wh (2S2P 18650) | Supports ~3.5 W eclipse load for 35 min at < 20% DOD |
| Bus voltage | Unregulated 7.2--8.4 V (2S) + regulated 3.3 V, 5 V | Standard CubeSat EPS architecture |
| Peak demand | ~18 W (imaging mode) | Multi-spectral imager + star tracker + reaction wheels + OBC |
| Orbit | 475 km SSO, ~94 min period | Optimal for EO: sun-synchronous for consistent lighting |
| Eclipse | ~35 min max, ~3 W demand | OBC + AOCS only during eclipse; no imaging or downlink |
| Thermal | Body-mounted radiator panels + battery heater | Passive thermal control; battery heater for eclipse charging margin |

*[Source: Planet Labs conference presentations; Salas et al., "SuperDove Constellation," SSC 2021]*

### CAPSTONE Thermal Design

NASA's CAPSTONE (12U, 25 kg) operates in a near-rectilinear halo orbit (NRHO) around the Moon with extreme thermal cycling:

- Perilune: strong Earth/Moon IR + solar
- Apolune: deep space cold, long shadow periods (up to 12+ hours)
- Thermal control: MLI wrapping (10-layer DAM blankets), heaters on propulsion lines (to prevent propellant freezing), passive radiator panels with white paint (AZ-93)
- Battery heaters: 5 W total, thermostatically controlled, critical for survival during long eclipses
- Operating temperature range: -20 degC to +50 degC for electronics; propulsion lines maintained above +5 degC

*[Source: Advanced Space, "CAPSTONE Design Overview," SmallSat Conference 2022]*

---

## 6. SpaceCDF Exercise
### Instructions

1. **Run the design** in SpaceCDF if not already converged
2. **Dashboard** -- review power KPIs:
   - Is power margin positive in **all** modes (sunlight, eclipse, safe)?
   - What is the orbit-average power demand?
   - What SA configuration was selected (body/deployable)?
3. **Timing Budget** card -- review mode durations:
   - Does the duty cycle match your ConOps modes?
   - Is eclipse time consistent with your orbit calculation from Session 2.3?
4. **Engineering Budgets** -- review the power waterfall:
   - Which subsystem is the largest power consumer in each mode?
   - Where could power be reduced if the budget is tight?
5. **Parametric** tab -- review thermal predictions:
   - Hot case temperature prediction
   - Cold case temperature prediction
   - Any exceedances?

### Worksheet 3.1 Tasks

1. Size the solar array for your mission (show all 5 calculation steps, including temperature derating)
2. Size the battery (show calculation with DOD justification and cycle-life verification)
3. Compute orbit-average power using duty cycle table
4. Identify hot case and cold case conditions for your orbit
5. Check thermal margins against ECSS requirements
6. Identify the dominant thermal concern for your mission (hot case or cold case) and propose a mitigation

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Solar cell physics | Triple-junction GaAs (InGaP/GaAs/Ge) achieves 28--30% AM0; multi-junction stacking captures broader solar spectrum |
| Temperature effects | Cells lose ~0.19%/degC (relative); operating at 65 degC costs ~7% power vs STC |
| Degradation | Radiation damage: $(1-\delta)^n$, $\delta \approx 2.5$%/yr LEO; cover glass mitigates proton/electron damage |
| EPS architecture | MPPT + regulated bus is CubeSat standard; MPPT extracts 10--15% more power than DET |
| SA sizing | $P_{\text{SA}} = P_{\text{peak}} + P_{\text{recharge}}$; derate for degradation $(1-\delta)^n$ and temperature $L_T$ |
| SA area | $A = P_{\text{BOL}} / (\eta \cdot S \cdot \cos\theta \cdot f_{\text{pack}} \cdot f_{\text{cover}})$ |
| Battery chemistry | Li-ion (LCO/NMC): 150--200 Wh/kg packaged; 3.0--4.2 V per cell; CC-CV charging |
| Battery sizing | $E = P_{\text{ecl}} \cdot t_{\text{ecl}} / (DOD \cdot \eta)$; DOD 20--30% for multi-year LEO |
| Battery failure modes | Thermal runaway (overcharge), lithium plating (cold charge), capacity imbalance (series cells) |
| SA power reference | Body-mounted: 2--12 W; single deploy: 4--30 W; dual deploy: 25--48 W |
| Thermal physics | No convection in vacuum; radiation ($\varepsilon \sigma T^4$) is only mechanism for heat rejection |
| Thermal balance | $Q_{\text{in}} = Q_{\text{out}}$; solve for $T = (Q/\varepsilon\sigma A)^{1/4}$ (single-node); multi-node for real design |
| $\alpha_s / \varepsilon$ ratio | Low ratio = cold surface (radiator); high ratio = warm surface (insulation) |
| MLI construction | VDA Kapton outer + 10--20 DAM layers + Dacron spacers; $\varepsilon_{\text{eff}} = 0.01$--$0.03$ |
| Heater sizing | $P_{\text{heater}} = \varepsilon\sigma A T_{\text{min}}^4 - Q_{\text{env}} - Q_{\text{int}}$; Kapton foil heaters, thermostat control |
| Thermal margins | ECSS: +/-5 degC operating, +/-10 degC acceptance, +/-15 degC qualification |
| Transient effects | Thermal mass ($mc_p$) prevents reaching steady state during short eclipses; 1U at 400 km cools ~20--25 degC in 36 min eclipse |
