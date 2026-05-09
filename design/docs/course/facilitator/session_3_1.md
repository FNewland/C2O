# Session 3.1: Power System and Thermal Control Design

**Duration:** 2 hours
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

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Size a solar array from mission power demand, eclipse profile, and degradation
2. Size a battery from eclipse energy demand, depth-of-discharge, and cycle-life requirements
3. Compute orbit-average power using duty cycle analysis
4. Explain EPS architecture (DET vs PPT, MPPT, bus regulation)
5. Perform first-order thermal balance analysis (hot case and cold case)
6. Select thermal control methods and apply ECSS thermal margins
7. Verify power and thermal budgets in SpaceCDF

---

## 1. Electrical Power System Architecture (20 min)

### Teaching Notes

*[Source: SMAD, Ch. 11.4; ECSS-E-ST-20C; Patel, Ch. 3]*

The EPS is the "utility company" of the spacecraft. It must continuously supply regulated power to all subsystems through every operational mode, including eclipse.

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

### Architecture Types

| Architecture | Description | Efficiency | Complexity | Typical Use |
|-------------|-------------|-----------|-----------|------------|
| **DET** (Direct Energy Transfer) | SA connects directly to bus through shunt regulator | 80--85% | Low | Small satellites, CubeSats |
| **PPT** (Peak Power Tracking / MPPT) | DC-DC converter maximises SA power extraction | 90--95% | Medium | Most modern CubeSats |
| **Unregulated bus** | Battery voltage varies (3.0--4.2 V per cell) | Highest | Lowest | Very simple CubeSats |
| **Regulated bus** | Fixed voltage rails (3.3 V, 5 V, 12 V) | Good | Medium | Most CubeSat COTS EPS |

**CubeSat standard:** Most commercial EPS boards (GomSpace P31u, Endurosat, AAC Clyde) use MPPT + regulated bus with 3.3 V and 5 V rails.

---

## 2. Solar Array Sizing (25 min)

### Teaching Notes

> **Key Equations -- Solar Array Sizing**
>
> **Step 1: Orbit-average power demand:**
> $$P_{\text{avg}} = \sum_{\text{modes}} P_{\text{mode}} \times f_{\text{duty,mode}}$$
>
> **Step 2: SA end-of-life power requirement:**
> $$P_{\text{SA,EOL}} = P_{\text{peak,sunlight}} + \frac{P_{\text{eclipse}} \times t_{\text{eclipse}}}{t_{\text{sunlight}} \times \eta_{\text{charge}}}$$
> where $\eta_{\text{charge}} \approx 0.9$ (battery charge efficiency for Li-ion).
>
> **Step 3: Account for degradation:**
> $$P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{(1 - \delta)^n}$$
> where $\delta = 0.025$ (2.5% per year degradation for triple-junction GaAs in LEO), $n$ = mission lifetime in years.
>
> **Step 4: Compute SA area:**
> $$A_{\text{SA}} = \frac{P_{\text{SA,BOL}}}{\eta_{\text{cell}} \times S \times \cos(\theta) \times f_{\text{pack}}}$$
> where:
> - $\eta_{\text{cell}} = 0.295$ (triple-junction GaAs efficiency, AM0)
> - $S = 1361$ W/m$^2$ (solar constant at 1 AU)
> - $\theta$ = sun incidence angle (0 deg for ideal tracking)
> - $f_{\text{pack}} = 0.85$ (cell packing factor)
>
> **Step 5: SA mass:**
> $$m_{\text{SA}} = A_{\text{SA}} \times \sigma_{\text{SA}}$$
> where $\sigma_{\text{SA}}$ = 2.5 kg/m$^2$ (body-mounted) or 1.5 kg/m$^2$ (deployable).

> **Worked Example -- 3U EO CubeSat Solar Array**
>
> **Given:** $P_{\text{peak,sunlight}} = 10.0$ W (imaging mode), $P_{\text{eclipse}} = 3.5$ W, $t_{\text{eclipse}} = 35$ min, $t_{\text{sunlight}} = 60$ min, $\eta_{\text{charge}} = 0.9$, mission lifetime = 3 years.
>
> **Step 2:** Recharge power:
> $P_{\text{recharge}} = \frac{3.5 \times 35}{60 \times 0.9} = \frac{122.5}{54.0} = 2.27$ W
>
> $P_{\text{SA,EOL}} = 10.0 + 2.27 = 12.27$ W
>
> **Step 3:** BOL accounting for 3-year degradation:
> $P_{\text{SA,BOL}} = \frac{12.27}{(1 - 0.025)^3} = \frac{12.27}{0.9269} = 13.24$ W
>
> **Step 4:** SA area:
> $A_{\text{SA}} = \frac{13.24}{0.295 \times 1361 \times 1.0 \times 0.85} = \frac{13.24}{341.2} = 0.0388$ m$^2$
>
> This is approximately 20 cm x 20 cm -- achievable with a single deployable panel on a 3U CubeSat.
>
> **Step 5:** SA mass (deployable):
> $m_{\text{SA}} = 0.0388 \times 1.5 = 0.058$ kg (panel only; mechanism adds ~0.1--0.2 kg)

### CubeSat SA Power Reference

| Configuration | 1U | 3U | 6U |
|--------------|-----|-----|-----|
| Body-mounted only | ~2 W | ~7 W | ~12 W |
| Single deployable | ~4 W | ~15 W | ~30 W |
| Dual deployable | -- | ~25 W | ~48 W |

*[Source: GomSpace, ISIS, MMA Design vendor datasheets; ASTERIA 6U confirmed 48 W BOL]*

---

## 3. Battery Sizing (15 min)

### Teaching Notes

> **Key Equations -- Battery Sizing**
>
> **Required battery capacity:**
> $$C_{\text{bat}} = \frac{P_{\text{eclipse}} \times t_{\text{eclipse}}}{DOD \times \eta_{\text{discharge}}}$$
> where:
> - $DOD$ = maximum depth of discharge (0.30 for > 10,000 cycle life with Li-ion)
> - $\eta_{\text{discharge}} = 0.95$ (discharge efficiency)
> - $t_{\text{eclipse}}$ in hours
>
> **Battery mass:**
> $$m_{\text{bat}} = \frac{C_{\text{bat}}}{E_{\text{specific}}}$$
> where $E_{\text{specific}} = 150$--$200$ Wh/kg for Li-ion 18650 cells.
>
> **Cycle life relationship** (Li-ion 18650):
>
> | DOD | Typical Cycle Life | Suitable For |
> |-----|-------------------|-------------|
> | 80% | ~500 cycles | Short missions (< 1 month) |
> | 50% | ~2,000 cycles | Medium missions (< 6 months) |
> | 30% | ~10,000 cycles | Multi-year LEO missions |
> | 20% | ~30,000 cycles | Long-life LEO (> 5 years) |

> **Worked Example -- Battery for 3U EO CubeSat**
>
> **Given:** $P_{\text{eclipse}} = 3.5$ W, $t_{\text{eclipse}} = 35$ min $= 0.583$ h, $DOD = 0.30$, $\eta = 0.95$.
>
> $C_{\text{bat}} = \frac{3.5 \times 0.583}{0.30 \times 0.95} = \frac{2.04}{0.285} = 7.16$ Wh
>
> With 20% margin: $C_{\text{bat,spec}} \geq 8.6$ Wh. Specify **10 Wh** minimum.
>
> Battery mass: $m_{\text{bat}} = \frac{10}{150} = 0.067$ kg
>
> **Verification:** 3-year mission at 15 orbits/day = 16,425 eclipses. At 30% DOD, Li-ion 18650 cells provide > 10,000 cycles. **Marginal** -- consider 20% DOD for extra life margin ($C_{\text{bat}} = 10.7$ Wh, specify 13 Wh).

---

## 4. Thermal Control System (30 min)

### Teaching Notes

*[Source: ECSS-E-ST-31C; Gilmore, Ch. 1--4; SMAD, Ch. 11.5]*

### Thermal Environment in LEO

A spacecraft in LEO experiences four thermal inputs and one thermal sink:

| Source | Flux | Direction |
|--------|------|-----------|
| **Direct solar** | $S = 1361$ W/m$^2$ | Sun-facing surfaces only |
| **Earth albedo** | $\alpha_E \times S \approx 0.30 \times 1361 \approx 408$ W/m$^2$ | Earth-facing surfaces (nadir) |
| **Earth infrared** | $q_{\text{IR}} \approx 240$ W/m$^2$ | Earth-facing surfaces (nadir) |
| **Internal dissipation** | $Q_{\text{int}} = P_{\text{dissipated}}$ | From electronics waste heat |
| **Deep space** (sink) | $T_{\text{space}} \approx 3$ K | Zenith-facing radiator surfaces |

### Thermal Balance Equation

> **Key Equations -- Thermal Equilibrium**
>
> At steady state, the absorbed heat equals the radiated heat:
>
> $$Q_{\text{in}} = Q_{\text{out}}$$
>
> $$\alpha_s A_{\text{sun}} S + \alpha_s A_{\text{alb}} \alpha_E S + \varepsilon A_{\text{IR}} q_{\text{IR}} + Q_{\text{int}} = \varepsilon \sigma A_{\text{rad}} T^4$$
>
> where:
> - $\alpha_s$ = solar absorptance of surface coating
> - $\varepsilon$ = infrared emittance of surface coating
> - $\sigma = 5.67 \times 10^{-8}$ W/m$^2$/K$^4$ (Stefan-Boltzmann constant)
> - $A_{\text{sun}}$, $A_{\text{alb}}$, $A_{\text{IR}}$, $A_{\text{rad}}$ = projected areas for each flux
> - $T$ = equilibrium temperature (K)
>
> **Solving for equilibrium temperature:**
> $$T = \left(\frac{Q_{\text{absorbed}} + Q_{\text{internal}}}{\varepsilon \sigma A_{\text{rad}}}\right)^{1/4}$$

### Hot Case and Cold Case

| Case | Conditions | Design Concern |
|------|-----------|----------------|
| **Hot case** | Maximum solar exposure, all subsystems active, worst sun angle, BOL coatings | Components exceed maximum operating temperature |
| **Cold case** | Eclipse, minimum power dissipation, degraded coatings (EOL), deep space view | Components fall below minimum operating temperature |

### Surface Coatings

| Coating | $\alpha_s$ | $\varepsilon$ | $\alpha_s / \varepsilon$ | Use |
|---------|-----------|--------------|------------------------|-----|
| White paint (S13G) | 0.20 | 0.85 | 0.24 | Radiators (stay cool) |
| Black paint (Aeroglaze Z306) | 0.95 | 0.85 | 1.12 | Internal surfaces (maximize exchange) |
| Gold tape | 0.25 | 0.04 | 6.25 | MLI outer layer (minimize radiation) |
| Alodine (bare Al) | 0.38 | 0.15 | 2.53 | Moderate thermal control |
| MLI blanket (effective) | 0.05--0.15 | 0.02--0.05 | ~3 | Thermal isolation |
| Solar cells | 0.75--0.92 | 0.80--0.85 | ~1.0 | SA surfaces (high absorption) |

### Thermal Control Methods

| Method | Type | Mass Impact | Typical Use |
|--------|------|-------------|------------|
| **Surface coatings** | Passive | Negligible | Always -- select $\alpha_s/\varepsilon$ ratio per face |
| **MLI blankets** | Passive | 0.05--0.2 kg | Insulate sensitive components from environment |
| **Radiators** | Passive | Part of structure | Reject internal waste heat to deep space |
| **Heaters** | Active | 0.005--0.02 kg each | Maintain minimum temp during eclipse/safe mode |
| **Heat pipes** | Active/passive | 0.05--0.1 kg | Transport heat from source to radiator |
| **Louvers** | Active | 0.1--0.5 kg | Variable-conductance radiators (rare on CubeSats) |

### ECSS Thermal Margins

*[Source: ECSS-E-ST-31C, Table 5-1]*

| Test Level | Hot Margin | Cold Margin |
|-----------|-----------|-------------|
| **Qualification** | Predicted + 15 degC | Predicted - 15 degC |
| **Acceptance** | Predicted + 10 degC | Predicted - 10 degC |
| **Operating** | Predicted + 5 degC | Predicted - 5 degC |

> **Worked Example -- 3U CubeSat Thermal Check**
>
> **Hot case:** Predicted maximum temperature of payload CCD = 42 degC.
> - Operating limit = 50 degC. Margin = 50 - 42 = 8 degC > 5 degC. **Pass.**
> - Qualification test: must test at 42 + 15 = 57 degC. If qualification limit is 60 degC: **Pass.**
>
> **Cold case:** Predicted minimum temperature of battery = -8 degC during worst eclipse.
> - Operating limit = -10 degC. Margin = -8 - (-10) = 2 degC < 5 degC. **Fail.**
> - **Action:** Add heater (0.5 W survival heater with thermostat set to -5 degC).

---

## 5. Real Mission Examples (10 min)

### Planet SuperDove EPS

| Parameter | Value |
|-----------|-------|
| Form factor | 3U+, ~5 kg |
| SA configuration | Body-mounted + deployable wings |
| SA power (BOL) | ~25 W |
| Battery | Li-ion, ~20 Wh |
| Bus voltage | Unregulated 7.2--8.4 V (2S) |
| Peak demand | ~18 W (imaging mode) |
| Orbit | 475 km SSO, ~94 min period |
| Eclipse | ~35 min max, ~3 W demand |

*[Source: Planet Labs conference presentations; Salas et al., "SuperDove Constellation," SSC 2021]*

### CAPSTONE Thermal Design

NASA's CAPSTONE (12U, 25 kg) operates in a near-rectilinear halo orbit (NRHO) around the Moon with extreme thermal cycling:

- Perilune: strong Earth/Moon IR + solar
- Apolune: deep space cold, long shadow periods
- Thermal control: MLI wrapping, heaters on propulsion lines, passive radiator panels

*[Source: Advanced Space, "CAPSTONE Design Overview," SmallSat Conference 2022]*

---

## 6. SpaceCDF Exercise (30 min)

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

1. Size the solar array for your mission (show all 5 calculation steps)
2. Size the battery (show calculation with DOD justification)
3. Compute orbit-average power using duty cycle table
4. Identify hot case and cold case conditions for your orbit
5. Check thermal margins against ECSS requirements

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| EPS architecture | MPPT + regulated bus is CubeSat standard; 3.3 V / 5 V / battery rails |
| SA sizing | $P_{\text{SA}} = P_{\text{peak}} + P_{\text{recharge}}$; account for degradation $(1-\delta)^n$ |
| SA area | $A = P_{\text{BOL}} / (\eta \cdot S \cdot \cos\theta \cdot f_{\text{pack}})$ |
| Battery | $C = P_{\text{ecl}} \cdot t_{\text{ecl}} / (DOD \cdot \eta)$; DOD 30% for multi-year LEO |
| SA power reference | Body-mounted: 2--12 W; single deploy: 4--30 W; dual deploy: 25--48 W |
| Thermal balance | $Q_{\text{in}} = Q_{\text{out}}$; solve for $T = (Q/\varepsilon\sigma A)^{1/4}$ |
| Hot/cold cases | Hot: max solar + all systems on; Cold: eclipse + min power |
| Thermal margins | ECSS: +/-5 degC operating, +/-10 degC acceptance, +/-15 degC qualification |
| Coatings | $\alpha_s/\varepsilon$ ratio controls equilibrium temperature; white paint for radiators |
