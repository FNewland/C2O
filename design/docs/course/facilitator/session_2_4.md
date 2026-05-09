# Session 2.4: Mission Architecture -- Segments, Interfaces, and Budgets

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--2.3 (requirements, functions, orbit selected)
**SpaceCDF Tabs:** Mission Architecture, System Architecture, Interfaces, Dashboard

---

## References

- [NASA, *Systems Engineering Handbook*, 2016, Sec. 4.4 (Process 4) & Sec. 6.3 (Process 12: Interface Management)](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ECSS, *ECSS-E-ST-10-24C: Interface Management*, 2015](https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/)
- [ECSS, *ECSS-E-HB-10-02A: Verification Guidelines*, 2010, Sec. 5.2 (Mass Margins)](https://ecss.nl/hbstms/ecss-e-hb-10-02a-verification-guidelines/)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 10--11](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-20C: Electrical and Electronic*, 2021 (Power Budgets)](https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Decompose a space mission into its constituent segments (space, ground, launch, user)
2. Construct a system architecture block diagram with subsystem boundaries
3. Identify and classify all subsystem-to-subsystem interfaces using an N-squared matrix
4. Write formal interface requirements for critical subsystem pairs
5. Construct a mass budget with ECSS margin policy and a mode-based power budget
6. Interpret SpaceCDF's dashboard KPIs and budget displays

---

## 1. Mission Segment Decomposition (15 min)

### Teaching Notes

*[Source: NASA SEH Sec. 4.4; ECSS-E-ST-10C Sec. 5.4; SMAD, Ch. 1]*

Every space mission decomposes into segments, each with distinct functions and interfaces:

<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 12px;">
  <!-- Space Segment -->
  <rect x="50" y="20" width="200" height="110" rx="8" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="150" y="45" text-anchor="middle" fill="#1e40af" font-weight="bold" font-size="14">Space Segment</text>
  <text x="150" y="65" text-anchor="middle" fill="#1e40af" font-size="10">Spacecraft bus</text>
  <text x="150" y="80" text-anchor="middle" fill="#1e40af" font-size="10">Payload instrument(s)</text>
  <text x="150" y="95" text-anchor="middle" fill="#1e40af" font-size="10">Subsystems (EPS, AOCS, TTC...)</text>
  <text x="150" y="110" text-anchor="middle" fill="#1e40af" font-size="10">Flight software</text>
  <!-- Ground Segment -->
  <rect x="300" y="170" width="200" height="110" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="400" y="195" text-anchor="middle" fill="#166534" font-weight="bold" font-size="14">Ground Segment</text>
  <text x="400" y="215" text-anchor="middle" fill="#166534" font-size="10">Ground station(s)</text>
  <text x="400" y="230" text-anchor="middle" fill="#166534" font-size="10">Mission control centre</text>
  <text x="400" y="245" text-anchor="middle" fill="#166534" font-size="10">Data processing pipeline</text>
  <text x="400" y="260" text-anchor="middle" fill="#166534" font-size="10">Operations team</text>
  <!-- Launch Segment -->
  <rect x="550" y="20" width="200" height="80" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="650" y="45" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="14">Launch Segment</text>
  <text x="650" y="65" text-anchor="middle" fill="#92400e" font-size="10">Launch vehicle</text>
  <text x="650" y="80" text-anchor="middle" fill="#92400e" font-size="10">Deployer (e.g., ISIPOD)</text>
  <!-- User Segment -->
  <rect x="550" y="170" width="200" height="80" rx="8" fill="#fce7f3" stroke="#db2777" stroke-width="2"/>
  <text x="650" y="195" text-anchor="middle" fill="#9d174d" font-weight="bold" font-size="14">User Segment</text>
  <text x="650" y="215" text-anchor="middle" fill="#9d174d" font-size="10">End users</text>
  <text x="650" y="235" text-anchor="middle" fill="#9d174d" font-size="10">Data products / applications</text>
  <!-- RF link between space and ground -->
  <line x1="250" y1="100" x2="300" y2="200" stroke="#64748b" stroke-width="2" stroke-dasharray="6,3"/>
  <text x="260" y="155" fill="#64748b" font-size="10" transform="rotate(-35, 260, 155)">RF Link (TTC + Data)</text>
  <!-- Launch to space -->
  <line x1="550" y1="60" x2="250" y2="60" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="52" text-anchor="middle" fill="#d97706" font-size="10">Deploy</text>
  <!-- Ground to user -->
  <line x1="500" y1="230" x2="550" y2="210" stroke="#64748b" stroke-width="1.5"/>
  <text x="530" y="215" fill="#64748b" font-size="10">Data</text>
</svg>

| Segment | Elements | Key Interfaces |
|---------|----------|---------------|
| **Space** | Spacecraft bus, payload, flight software | To ground (RF), to launch (mechanical/electrical) |
| **Ground** | Ground station, MCC, data processing | To space (RF), to user (network) |
| **Launch** | Launch vehicle, deployer, adapter | To space (mechanical, electrical inhibits) |
| **User** | End users, applications, data consumers | To ground (data products) |

---

## 2. System Architecture Block Diagram (20 min)

### Teaching Notes

The system block diagram shows the internal architecture of the space segment -- all subsystems and their data/power/mechanical connections.

<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" style="max-width:750px; font-family: sans-serif; font-size: 11px;">
  <!-- Central bus -->
  <rect x="300" y="200" width="200" height="60" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="225" text-anchor="middle" fill="#92400e" font-weight="bold">OBC / Data Handling</text>
  <text x="400" y="245" text-anchor="middle" fill="#92400e" font-size="10">I2C / SPI / CAN bus</text>
  <!-- EPS -->
  <rect x="50" y="30" width="160" height="55" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="130" y="52" text-anchor="middle" fill="#1e40af" font-weight="bold">EPS</text>
  <text x="130" y="70" text-anchor="middle" fill="#1e40af" font-size="10">SA + Battery + Regulator</text>
  <!-- Power bus lines -->
  <line x1="130" y1="85" x2="130" y2="160" stroke="#dc2626" stroke-width="2"/>
  <line x1="50" y1="160" x2="750" y2="160" stroke="#dc2626" stroke-width="2"/>
  <text x="400" y="153" text-anchor="middle" fill="#dc2626" font-size="10" font-weight="bold">Power Bus (3.3V / 5V / Battery)</text>
  <!-- AOCS -->
  <rect x="50" y="310" width="160" height="55" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="130" y="332" text-anchor="middle" fill="#166534" font-weight="bold">AOCS</text>
  <text x="130" y="350" text-anchor="middle" fill="#166534" font-size="10">RW + MTQ + ST + SS</text>
  <line x1="210" y1="335" x2="300" y2="230" stroke="#64748b" stroke-width="1.5"/>
  <!-- Comms -->
  <rect x="590" y="310" width="160" height="55" rx="6" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="670" y="332" text-anchor="middle" fill="#3730a3" font-weight="bold">Comms (TTC)</text>
  <text x="670" y="350" text-anchor="middle" fill="#3730a3" font-size="10">TX + RX + Antenna</text>
  <line x1="590" y1="335" x2="500" y2="230" stroke="#64748b" stroke-width="1.5"/>
  <!-- Payload -->
  <rect x="590" y="30" width="160" height="55" rx="6" fill="#fce7f3" stroke="#db2777" stroke-width="2"/>
  <text x="670" y="52" text-anchor="middle" fill="#9d174d" font-weight="bold">Payload</text>
  <text x="670" y="70" text-anchor="middle" fill="#9d174d" font-size="10">Telescope / Sensor</text>
  <line x1="590" y1="60" x2="500" y2="220" stroke="#64748b" stroke-width="1.5"/>
  <!-- Thermal -->
  <rect x="300" y="400" width="200" height="45" rx="6" fill="#fef9c3" stroke="#ca8a04" stroke-width="2"/>
  <text x="400" y="420" text-anchor="middle" fill="#854d0e" font-weight="bold">Thermal</text>
  <text x="400" y="437" text-anchor="middle" fill="#854d0e" font-size="10">Heaters + MLI + Radiators</text>
  <line x1="400" y1="400" x2="400" y2="260" stroke="#64748b" stroke-width="1" stroke-dasharray="4,3"/>
  <!-- Structure (background) -->
  <rect x="30" y="10" width="740" height="470" rx="10" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="8,4"/>
  <text x="400" y="490" text-anchor="middle" fill="#94a3b8" font-size="12">Structure (primary + secondary)</text>
  <!-- Power taps -->
  <line x1="130" y1="160" x2="130" y2="310" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="670" y1="160" x2="670" y2="310" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="670" y1="85" x2="670" y2="160" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="400" y1="160" x2="400" y2="200" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
</svg>

### Subsystem Roles (CubeSat Reference)

| Subsystem | Abbreviation | Primary Function | Typical Mass Fraction |
|-----------|-------------|-----------------|----------------------|
| **Payload** | PL | Mission-specific sensing or communication | 25--40% |
| **Electrical Power System** | EPS | Generate, store, distribute electrical power | 15--25% |
| **Attitude & Orbit Control** | AOCS | Determine and control attitude; orbit knowledge | 8--15% |
| **Communications (TTC)** | LINK / TTC | Telemetry downlink, telecommand uplink, data downlink | 5--10% |
| **On-Board Computer** | OBC / C&DH | Command execution, data handling, flight software | 2--5% |
| **Thermal Control** | TCS | Maintain all components within temperature limits | 1--5% |
| **Structure** | STR | Mechanical support, launch load path, CDS compliance | 15--25% |
| **Propulsion** | PROP | Orbit manoeuvres, deorbit (if required) | 0--15% |
| **Harness** | HAR | Electrical interconnections | 3--7% |

---

## 3. The N-Squared Interface Matrix (25 min)

### Teaching Notes

*[Source: NASA SEH Sec. 6.3 -- Process 12: Interface Management; ECSS-E-ST-10-24C]*

Interface problems are the leading cause of integration failures. NASA SEH states: "Most system failures can be traced back to interface problems."

### N-Squared Matrix Structure

The N$^2$ matrix is a standard systems engineering tool for mapping all subsystem interactions:

- **Diagonal cells:** Subsystems (EPS, AOCS, Comms, Thermal, Structure, Propulsion, OBC, Payload)
- **Off-diagonal cells:** Interface between the row subsystem and the column subsystem
- **Upper triangle:** Outputs from row to column (data, power, commands)
- **Lower triangle:** Outputs from column to row

For 8 subsystems: $8 \times 7 / 2 = 28$ potential interface pairs. A typical CubeSat has 18--22 active interfaces.

### Interface Types

| Type | Symbol | Description | Example |
|------|--------|-------------|---------|
| **Mechanical** | M | Physical attachment, loads, alignment tolerances | Payload mounting to structure face |
| **Electrical** | E | Power connections, bus voltage, switched lines | EPS 5V bus to all subsystems |
| **Thermal** | T | Heat transfer paths, thermal coupling, conduction | Transponder waste heat to radiator panel |
| **Data** | D | Digital bus (I$^2$C, SPI, UART, CAN, RS-422) | OBC commands to AOCS controller |
| **RF** | R | Electromagnetic coupling or intentional RF paths | TX emissions coupling into payload receiver |
| **Optical** | O | Light paths, field-of-view clearance, stray light | Star tracker FOV clearance from solar array |

### Common CubeSat Interface Concerns

| Interface Pair | Types | Key Concern |
|----------------|-------|-------------|
| EPS <-> AOCS | E | Bus voltage compatibility; reaction wheel peak power draw |
| EPS <-> Comms | E | TX peak power demand (~6--10 W); switched line allocation |
| EPS <-> Thermal | E, T | SA thermal coupling; radiator vs SA area competition on external faces |
| EPS <-> Payload | E | Peak power switching; duty cycle coordination |
| Structure <-> AOCS | M | Reaction wheel and star tracker mounting alignment; vibration isolation |
| Structure <-> Payload | M, O | Payload alignment stability; optical FOV clearance |
| OBC <-> AOCS | D | Attitude data for payload pointing; mode transition commands |
| OBC <-> Comms | D | Telemetry packet routing; telecommand distribution |
| OBC <-> Payload | D | Science data acquisition trigger; instrument commanding |
| Comms <-> Payload | R | **EMC:** TX conducted/radiated emissions vs payload receiver sensitivity |
| Comms <-> AOCS | R, O | Antenna pattern vs star tracker FOV; antenna pointing coordination |
| Thermal <-> Payload | T | Detector cooling requirement; operating temperature limits |
| AOCS <-> Payload | M | Reaction wheel micro-vibration vs payload pointing stability (jitter) |

### Conflict Detection and Resolution

Interface conflicts arise when two subsystems have incompatible requirements at their shared boundary.

**Severity Classification:**

| Severity | Description | Example | Required Action |
|----------|-------------|---------|----------------|
| **Critical** | Design cannot close without resolution | EMC: TX radiation prevents payload operation | Must resolve before PDR |
| **Major** | Significant impact on design margin | Radiator area competes with SA area | Mitigation plan required by PDR |
| **Minor** | Manageable with minor adjustment | Star tracker FOV partially blocked by antenna stow | Accommodation analysis |

**Resolution Options:**

1. **Relocate:** Move a component to avoid the conflict (e.g., star tracker to different face)
2. **Shield/Isolate:** Add EMC shielding, vibration isolators, thermal insulation
3. **Time-Division:** Schedule conflicting activities to avoid simultaneity (e.g., no TX during imaging)
4. **Accept Risk:** Document residual risk and margin impact in the risk register

### Writing Interface Requirements

For each significant interface, write formal requirements:

**Example -- EPS <-> All Subsystems:**
```
IR-PWR-001: "The EPS shall provide regulated bus voltages of
             3.3 V +/- 0.1 V and 5.0 V +/- 0.25 V to all subsystems."
IR-PWR-002: "Each subsystem shall not exceed its allocated power
             draw without EPS coordination."
```

**Example -- Comms <-> Payload (EMC):**
```
IR-EMC-001: "TX conducted emissions shall be below -60 dBm in the
             payload receiver band (1.5-1.6 GHz) during imaging mode."
IR-EMC-002: "TX and payload acquisition shall not operate simultaneously
             unless IR-EMC-001 is verified by test."
```

---

## 4. Engineering Budgets: Mass and Power (30 min)

### Teaching Notes

*[Source: ECSS-E-HB-10-02A Sec. 5.2; SMAD, Ch. 10--11]*

Engineering budgets are the quantitative backbone of the design. They answer: **"Will this design close?"**

### Mass Budget

> **Key Equations -- Mass Budget**
>
> **Mass margin:**
> $$\text{Margin}_{\%} = \frac{M_{\text{allocation}} - M_{\text{MEV}}}{M_{\text{allocation}}} \times 100\%$$
>
> where MEV = Maximum Expected Value = CBE + maturity margins.
>
> **Status thresholds:** Green: > 20% | Amber: 10--20% | Red: < 10% | Exceeded: < 0%

| Term | Definition |
|------|-----------|
| **CBE** (Current Best Estimate) | Best estimate of actual mass based on current knowledge |
| **MEV** (Maximum Expected Value) | CBE + equipment maturity margin = worst-case expected mass |
| **Equipment maturity margin** | Applied per component based on design maturity (TRL) |
| **System margin** | Applied at system level as management reserve |

### ECSS Margin Policy by Phase

*[Source: ECSS-E-HB-10-02A Sec. 5.2]*

| Phase | Equipment Margin | System Margin | Compound |
|-------|-----------------|---------------|----------|
| **0/A** (concept) | 20% | 20% | ~44% |
| **B1** (preliminary) | 10% | 20% | ~32% |
| **B2** (detailed) | 5% | 15% | ~21% |
| **C/D** (build/test) | 3% | 10% | ~13% |
| **E** (as-built) | 0% | 5% | ~5% |

> **Worked Example -- 3U CubeSat Mass Budget (Phase A)**
>
> | Subsystem | CBE (kg) | Equip. Margin (20%) | MEV (kg) |
> |-----------|---------|---------------------|---------|
> | Payload | 1.50 | 0.30 | 1.80 |
> | EPS | 0.75 | 0.15 | 0.90 |
> | AOCS | 0.55 | 0.11 | 0.66 |
> | Comms (TTC) | 0.25 | 0.05 | 0.30 |
> | OBC | 0.08 | 0.02 | 0.10 |
> | Thermal | 0.05 | 0.01 | 0.06 |
> | Structure | 0.35 | 0.07 | 0.42 |
> | Harness | 0.15 | 0.03 | 0.18 |
> | **Dry Total** | **3.68** | | **4.42** |
> | System Margin (20%) | | | **0.88** |
> | **Dry MEV** | | | **5.30** |
> | Propellant | | | 0.00 |
> | **Wet Mass** | | | **5.30** |
> | **Launcher Allocation** | | | **6.00** (3U limit) |
> | **Mass Margin** | | | **0.70 kg (11.7%)** -- Amber |

### Mode-Based Power Budget

The power budget is computed **per operational mode** because not all subsystems draw power simultaneously:

| Subsystem | Safe (W) | Idle (W) | Imaging (W) | Downlink (W) | Eclipse (W) |
|-----------|---------|---------|-------------|-------------|-------------|
| OBC | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| AOCS | 0.5 | 1.0 | 3.0 | 2.0 | 0.5 |
| Payload | 0 | 0 | 5.0 | 0 | 0 |
| Comms (TX) | 0.5 | 0.5 | 0.5 | 6.0 | 0 |
| Thermal | 0.5 | 0.5 | 0.5 | 0.5 | 2.0 |
| **Total** | **2.5** | **3.0** | **10.0** | **9.5** | **3.5** |

### Orbit-Average Power

> **Key Equations -- Orbit-Average Power**
>
> $$P_{\text{avg}} = \sum_{\text{modes}} \left(P_{\text{mode}} \times \text{duty}_{\text{mode}}\right)$$
>
> **Example for 95-min orbit (60 min sunlight, 35 min eclipse):**
>
> | Mode | Power (W) | Duty (%) | Contribution (W) |
> |------|----------|----------|-------------------|
> | Idle | 3.0 | 45% | 1.35 |
> | Imaging | 10.0 | 10% | 1.00 |
> | Downlink | 9.5 | 8% | 0.76 |
> | Eclipse | 3.5 | 37% | 1.30 |
> | **Total** | | **100%** | **4.41 W** |

### Other Budget Types (Preview)

These budgets will be developed in detail during Week 2 Day 3--4 sessions:

| Budget | Key Equation | Session |
|--------|-------------|---------|
| **Link** | $\text{Margin} = \text{EIRP} - \text{FSPL} + G/T - k - 10\log_{10}(R_b) - E_b/N_0$ | 3.3 |
| **Pointing** | $\theta_{\text{total}} = \sqrt{\sum \theta_i^2}$ (RSS) | 3.2 |
| **$\Delta V$** | $\Delta V = I_{sp} \cdot g_0 \cdot \ln(m_0/m_f)$ (Tsiolkovsky) | 3.4 |
| **Data** | $\text{Daily Downlink} \geq \text{Daily Generation}$ | 3.3 |

---

## 5. SpaceCDF Exercise (30 min)

### Instructions

1. **System Architecture tab:** Review or edit the subsystem block diagram for your mission
2. **Interfaces tab:** Review the N$^2$ matrix
   - Click on 3 interface cells to examine types and concerns
   - For any red-bordered cell (conflict), use the "Resolve Conflict" workflow
   - Write interface requirements for your most critical pair
3. **Dashboard:** Examine all KPI cards:
   - Mass margin: green/amber/red?
   - Power margin per mode
   - Link margin (if computed)
   - Cost vs ceiling
4. **Budget Breakdown:** Open per-subsystem mass and power charts
5. Complete Worksheet 2.4

### Discussion Questions

- Which budget is tightest (closest to zero or negative margin)?
- What single design change would most improve the tightest budget?
- How does the ECSS margin policy affect your design freedom at Phase A vs Phase C?
- Which interface pair is most likely to cause integration problems?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Mission segments | Space, Ground, Launch, User -- each with defined interfaces |
| System architecture | Block diagram shows subsystems, data buses, power distribution |
| N$^2$ matrix | Maps all 28 potential interface pairs; 6 types (M, E, T, D, R, O) |
| Interface conflicts | Severity classification (critical/major/minor); 4 resolution options |
| Interface requirements | Formal boundary agreements; must be verifiable |
| Mass budget | CBE + equipment margin + system margin = MEV; compare to allocation |
| Power budget | Mode-based; duty cycling gives orbit-average; SA must cover peak + recharge |
| ECSS margins | Decrease with maturity: ~44% at Phase A to ~13% at Phase C/D |
| Budget closure | Negative margin = design does not close; reduce demand or increase allocation |
