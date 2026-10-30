# Chapter 8 — Mission Architecture: Segments, Interfaces and Engineering Budgets

> **Recommended background.** NASA Systems Engineering Handbook §4.4 (Design Solution Definition) and §6.3 (Interface Management); ECSS-E-ST-10-24C (Interface management); ECSS-E-HB-10-02A §5.2 and ECSS-E-ST-10-02C (margin philosophy); SMAD4 Ch. 10–11. This chapter assumes requirements (Chapter 5), functions (Chapter 6) and an orbit (Chapter 7) have been defined.

## Learning objectives

By the end of this chapter, you will be able to:

1. Decompose a space mission into its constituent segments (space, ground, launch, user)
2. Construct a system architecture block diagram with subsystem boundaries
3. Identify and classify all subsystem-to-subsystem interfaces using an N² matrix, and detect interface conflicts
4. Write formal interface requirements for critical subsystem pairs
5. Construct a mass budget with the two-level ECSS margin policy and a mode-based power budget
6. Read a set of budget indicators (margin by budget, margin by mode) and decide whether a design closes

---

## 8.1 Mission segment decomposition

*[Source: NASA SEH Sec. 4.4; ECSS-E-ST-10C Sec. 5.4; SMAD, Ch. 1]*

Every space mission decomposes into segments, each with distinct functions and interfaces. Chapter 4 §4.8.1 introduced the segments at the ConOps level; this section is the canonical treatment. Figure 8.1 shows the four segments and the links between them.

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

**Figure 8.1** — The four mission segments and their principal links: the launch segment deploys the space segment; space and ground segments exchange telemetry, telecommands and data over RF; the ground segment delivers data products to the user segment.

| Segment | Elements | Key interfaces |
|---------|----------|---------------|
| **Space** | Spacecraft bus, payload, flight software | To ground (RF), to launch (mechanical/electrical) |
| **Ground** | Ground station, MCC, data processing | To space (RF), to user (network) |
| **Launch** | Launch vehicle, deployer, adapter | To space (mechanical, electrical inhibits) |
| **User** | End users, applications, data consumers | To ground (data products) |

The ground segment is designed in Chapter 17 and operated in Chapter 18; the launch interface (deployer, inhibits, the CubeSat Design Specification) is treated with the structure in Chapter 12.

---

## 8.2 System architecture block diagram

The system block diagram shows the internal architecture of the space segment — all subsystems and their data, power and mechanical connections. Figure 8.2 is the reference CubeSat architecture used for the 3U EO CubeSat running example (EOSat-3U) throughout Chapters 9–12.

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
  <text x="400" y="153" text-anchor="middle" fill="#dc2626" font-size="10" font-weight="bold">Power Bus (3.3 V / 5 V / Battery)</text>
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

**Figure 8.2** — Reference CubeSat system block diagram: the OBC at the centre of the data bus, the EPS feeding a regulated power bus to every subsystem, and the structure enclosing all of them.

### 8.2.1 Subsystem roles (CubeSat reference)

| Subsystem | Abbreviation | Primary function | Typical mass fraction |
|-----------|-------------|-----------------|----------------------|
| **Payload** | PL | Mission-specific sensing or communication | 25–40 % |
| **Electrical Power System** | EPS | Generate, store, distribute electrical power | 15–25 % |
| **Attitude & Orbit Control** | AOCS | Determine and control attitude; orbit knowledge | 8–15 % |
| **Communications (TTC)** | LINK / TTC | Telemetry downlink, telecommand uplink, data downlink | 5–10 % |
| **On-Board Computer** | OBC / C&DH | Command execution, data handling, flight software | 2–5 % |
| **Thermal Control** | TCS | Maintain all components within temperature limits | 1–5 % |
| **Structure** | STR | Mechanical support, launch load path, CDS compliance | 15–25 % |
| **Propulsion** | PROP | Orbit manoeuvres, deorbit (if required) | 0–15 % |
| **Harness** | HAR | Electrical interconnections | 3–7 % |

---

## 8.3 The N² interface matrix

*[Source: NASA SEH Sec. 6.3 — Process 12: Interface Management; ECSS-E-ST-10-24C]*

Interface problems are the leading cause of integration failures. NASA SEH states: "Most system failures can be traced back to interface problems." The N² matrix, popularised by NASA and ESA concurrent-design practice, is the standard tool for finding every interface before it finds you. This section is the book's canonical treatment; Chapter 15 returns to interfaces as a source of risk.

### 8.3.1 N² matrix structure

For a system with $N$ subsystems, the N² matrix is an $N \times N$ grid where:

- **Diagonal cells** contain the subsystem names (EPS, AOCS, Comms, Thermal, Structure, Propulsion, OBC, Payload)
- **Off-diagonal cells** contain the interfaces between subsystems
- **Cell $(i, j)$** = outputs FROM subsystem $i$ TO subsystem $j$ (read across the row)
- **Cell $(j, i)$** = outputs FROM subsystem $j$ TO subsystem $i$ (read down the column)

For 8 subsystems there are $8 \times 7 / 2 = 28$ potential interface pairs (56 directed cells). A typical CubeSat has 18–22 active pairs.

### 8.3.2 A six-subsystem example

The table below is a complete N² matrix for a six-subsystem CubeSat. Each cell is read as "what the row subsystem delivers to the column subsystem".

| FROM ↓ / TO → | EPS | OBC | AOCS | TTC | Payload | Structure |
|---|---|---|---|---|---|---|
| **EPS** | *[EPS]* | 28 V bus; 5 V reg; I²C HK | 28 V bus; 5 V reg; I²C HK | 28 V bus; 5 V reg; I²C HK | 28 V bus; 5 V reg; I²C HK | Mounting bolts |
| **OBC** | Power commands; telemetry | *[OBC]* | Commands (I²C/SPI) | TC data (UART) | Commands (SPI/UART) | — |
| **AOCS** | Power request | Attitude data; AOCS HK | *[AOCS]* | Attitude for antenna pointing | Attitude data for pointing | Mount; vibration |
| **TTC** | Power request | RX data; command forwarding | — | *[TTC]* | — | Antenna mount |
| **Payload** | Power request | Science data; payload HK | Pointing request | — | *[Payload]* | FOV clearance |
| **Structure** | — | — | Sensor mounting | Antenna mounting | Payload mounting | *[Structure]* |

**Table 8.1** — N² matrix for a six-subsystem CubeSat. Row = source, column = destination.

### 8.3.3 Interface types

Every entry in the matrix is tagged with one or more interface types. The letter codes below are used throughout the book (Chapter 15 uses the same codes in the interface-risk register).

| Type | Code | Description | Examples |
|------|------|-------------|----------|
| **Mechanical** | M | Physical attachment, loads, alignment tolerances, thermal straps, alignment pins | Payload mounting to structure face |
| **Electrical / power** | E | Power connections, bus voltage, switched lines | 28 V bus, 5 V regulated, switched lines to all subsystems |
| **Thermal** | T | Heat transfer paths, conductive and radiative coupling | Transponder waste heat to radiator panel |
| **Data** | D | Digital bus (I²C, SPI, UART, CAN, RS-422) | OBC commands to AOCS controller |
| **RF** | R | Intentional RF paths (coaxial cable, waveguide) and electromagnetic coupling | TX emissions coupling into payload receiver |
| **Optical** | O | Light paths, field-of-view clearance, stray light | Star tracker FOV clearance from solar array |
| **Software** | S | Command interfaces, telemetry packet definitions, mode transitions | OBC-to-AOCS command dictionary |

**Table 8.2** — Interface-type codes used throughout this book.

Figure 8.3 shows a colour-coded N² matrix for an eight-subsystem 6U CubeSat using these codes. Notice how the Power row is almost entirely E (every subsystem draws power), the Data/OBC row and column are mostly D, and the sparse M, T, R and O entries are the ones most likely to be forgotten.

![N² interface matrix for a 6U CubeSat.](../assets/figures/fig_n2_matrix.png)

**Figure 8.3** — Illustrative N² interface matrix for an eight-subsystem 6U CubeSat, colour-coded by interface type (M mechanical, E electrical, T thermal, D data, R RF, O optical, S software — Table 8.2). Diagonal cells name the subsystems; off-diagonal cells are read row → column.

### 8.3.4 Common CubeSat interface concerns

| Interface pair | Types | Key concern |
|----------------|-------|-------------|
| EPS ↔ AOCS | E | Bus voltage compatibility; reaction-wheel peak power draw |
| EPS ↔ Comms | E | TX peak power demand (~6–10 W); switched-line allocation |
| EPS ↔ Thermal | E, T | SA thermal coupling; radiator vs SA area competition on external faces |
| EPS ↔ Payload | E | Peak power switching; duty-cycle coordination |
| Structure ↔ AOCS | M | Reaction wheel and star tracker mounting alignment; vibration isolation |
| Structure ↔ Payload | M, O | Payload alignment stability; optical FOV clearance |
| OBC ↔ AOCS | D, S | Attitude data for payload pointing; mode-transition commands |
| OBC ↔ Comms | D, S | Telemetry packet routing; telecommand distribution |
| OBC ↔ Payload | D, S | Science-data acquisition trigger; instrument commanding |
| Comms ↔ Payload | R | **EMC:** TX conducted/radiated emissions vs payload receiver sensitivity |
| Comms ↔ AOCS | R, O | Antenna pattern vs star tracker FOV; antenna pointing coordination |
| Thermal ↔ Payload | T | Detector cooling requirement; operating temperature limits |
| AOCS ↔ Payload | M | Reaction-wheel micro-vibration vs payload pointing stability (jitter) |

### 8.3.5 Conflict detection and resolution

An **interface conflict** exists when two subsystems have incompatible expectations at their shared boundary. Typical cases:

- Subsystem A expects to send 28 V but subsystem B only accepts 5 V (E)
- Subsystem A uses I²C but subsystem B only has SPI or RS-422 (D)
- Subsystem A transmits in S-band but subsystem B's antenna is X-band (R)
- Subsystem A mounts on the +Z face but the structure has no mounting provision on +Z (M)

Many of these are mechanical checks — compare the two sides of every cell for voltage, protocol, band and location — and a concurrent-design tool with a constraint engine will flag them automatically as equipment is selected. The remainder require engineering judgement, which is where the severity classification helps.

**Severity classification:**

| Severity | Description | Example | Required action |
|----------|-------------|---------|----------------|
| **Critical** | Design cannot close without resolution | EMC: TX radiation prevents payload operation | Must resolve before PDR |
| **Major** | Significant impact on design margin | Radiator area competes with SA area | Mitigation plan required by PDR |
| **Minor** | Manageable with minor adjustment | Star tracker FOV partially blocked by stowed antenna | Accommodation analysis |

**Resolution options:**

1. **Relocate:** Move a component to avoid the conflict (e.g., star tracker to a different face)
2. **Shield/isolate:** Add EMC shielding, vibration isolators, thermal insulation
3. **Time-division:** Schedule conflicting activities to avoid simultaneity (e.g., no TX during imaging)
4. **Accept risk:** Document residual risk and margin impact in the risk register (Chapter 15)

> **Worked example — detecting a data-protocol conflict**
>
> *Problem:* The OBC sends commands to the reaction wheels via I²C. The selected reaction-wheel unit (a Blue Canyon RWP100 — a representative example, not an endorsement) uses RS-422. Cell (OBC → AOCS) of the N² matrix therefore reads "commands, I²C" on one side of the boundary and "commands, RS-422" on the other: a D-type interface conflict.
>
> *Resolution options:*
> 1. Select a different reaction wheel that supports I²C
> 2. Add an I²C-to-RS-422 bridge (additional component, mass, cost and failure point)
> 3. Select a different OBC that supports RS-422
>
> *Severity:* Major — the design can close with option 2, but at a cost in mass, harness and reliability. The conflict is recorded in the interface register with its resolution and owner, and the resolution becomes an interface requirement (below). In a concurrent-design tool with equipment-level protocol data this conflict appears as a warning the moment the wheel is selected.

### 8.3.6 Writing interface requirements

For each significant interface, write formal requirements in the "shall" form of Chapter 5:

**Example — EPS ↔ all subsystems:**
```
IR-PWR-001: "The EPS shall provide regulated bus voltages of
             3.3 V ± 0.1 V and 5.0 V ± 0.25 V to all subsystems."
IR-PWR-002: "Each subsystem shall not exceed its allocated power
             draw without EPS coordination."
```

**Example — Comms ↔ Payload (EMC):**
```
IR-EMC-001: "TX conducted emissions shall be below −60 dBm in the
             payload receiver band (1.5–1.6 GHz) during imaging mode."
IR-EMC-002: "TX and payload acquisition shall not operate simultaneously
             unless IR-EMC-001 is verified by test."
```

**Example — OBC ↔ AOCS (data), from the worked example:**
```
IR-DAT-003: "The OBC shall command the reaction-wheel assembly over
             RS-422 at 115.2 kbit/s via the I²C-to-RS-422 bridge;
             the bridge shall be powered from the AOCS switched line."
```

---

## 8.4 Engineering budgets: mass and power

*[Source: ECSS-E-HB-10-02A Sec. 5.2; ECSS-E-ST-10-02C; SMAD, Ch. 10–11]*

Engineering budgets are the quantitative backbone of the design. They answer: **"Will this design close?"**

### 8.4.1 Mass budget

> **Key equations — mass budget**
>
> **Mass margin:**
> $$\text{Margin}_{\%} = \frac{M_{\text{allocation}} - M_{\text{MEV}}}{M_{\text{allocation}}} \times 100\,\%$$
>
> where MEV = Maximum Expected Value = CBE + maturity margins (equipment level), to which the system-level margin is added before comparison with the allocation.
>
> **Status thresholds:** Green: > 20 % | Amber: 10–20 % | Red: < 10 % | Exceeded: < 0 %

| Term | Definition |
|------|-----------|
| **CBE** (Current Best Estimate) | Best estimate of actual mass based on current knowledge |
| **MEV** (Maximum Expected Value) | CBE + equipment maturity margin = worst-case expected mass |
| **Equipment maturity margin** | Applied per component based on design maturity (TRL / heritage) |
| **System margin** | Applied at system level as management reserve, decreasing with project phase |

### 8.4.2 The ECSS margin policy — two levels

The ECSS margin philosophy has **two levels**, and both must be applied. First, each piece of equipment carries a **maturity margin** that depends on how well its mass is known; second, the project carries a **system-level margin** on the summed MEV that depends on the lifecycle phase (Chapter 1 §1.4). Table 8.3 is the single statement of the policy used throughout this book; Part IV and later chapters refer to it rather than restating the numbers.

| Level | Basis | Margin |
|-------|-------|--------|
| **Equipment maturity** | Off-the-shelf, flown, unmodified | 5 % |
| | Off-the-shelf with minor modification | 10 % |
| | New design or major modification | 20 % |
| **System level, by phase** | Phase 0 / A (concept, feasibility) | 20 % |
| | Phase B (preliminary definition) | 15 % |
| | Phase C (detailed definition) | 10 % |
| | Phase D (qualification and production) | 5 % |

**Table 8.3** — Canonical ECSS mass-margin schedule: equipment maturity margins (applied per item to obtain MEV) plus a system-level margin by phase (applied to the summed MEV). Source: ECSS-E-HB-10-02A §5.2 and the margin philosophy of ECSS-E-ST-10-02C.

The two levels compound. For a Phase A design in which most equipment is new (20 % maturity margin), the total allowance above CBE is $1.20 \times 1.20 - 1 \approx 44\,\%$; by Phase C with largely flight-proven equipment it falls to roughly $1.05 \times 1.10 - 1 \approx 16\,\%$, and in Phase D, when masses are measured, to about 5 %. Figure 8.4 shows this shrinking envelope alongside a typical dry-mass distribution.

![Mass distribution and ECSS margin policy by phase.](../assets/figures/fig_mass_budget.png)

**Figure 8.4** — Left: typical dry-mass distribution for an 8.5 kg CubeSat-class spacecraft (structure, power and payload dominate). Right: the compound equipment-plus-system margin envelope by phase, illustrating how the allowance above CBE shrinks as the design matures (Table 8.3).

> **Worked example — EOSat-3U mass budget (Phase A)**
>
> All equipment is treated as new design (20 % maturity margin); system margin 20 % (Phase A).
>
> | Subsystem | CBE (kg) | Equipment margin (20 %) | MEV (kg) |
> |-----------|---------|---------------------|---------|
> | Payload | 1.50 | 0.30 | 1.80 |
> | EPS | 0.75 | 0.15 | 0.90 |
> | AOCS | 0.55 | 0.11 | 0.66 |
> | Comms (TTC) | 0.25 | 0.05 | 0.30 |
> | OBC | 0.08 | 0.02 | 0.10 |
> | Thermal | 0.05 | 0.01 | 0.06 |
> | Structure | 0.35 | 0.07 | 0.42 |
> | Harness | 0.15 | 0.03 | 0.18 |
> | **Dry total** | **3.68** | | **4.42** |
> | System margin (20 %) | | | **0.88** |
> | **Dry MEV + system margin** | | | **5.30** |
> | Propellant | | | 0.00 |
> | **Wet mass** | | | **5.30** |
> | **Launcher allocation** | | | **6.00** (3U limit) |
> | **Mass margin** | | | **0.70 kg (11.7 %)** — Amber |
>
> The 3.68 kg CBE is the parametric estimate that Chapter 12 later replaces with a bottom-up equipment list.

### 8.4.3 Mode-based power budget

The power budget is computed **per operational mode** because not all subsystems draw power simultaneously. The modes are those of the ConOps (Chapter 4 §4.8.3; the full mode table with transitions and FDIR triggers is in Chapter 18). The table below is the per-subsystem breakdown for EOSat-3U; its totals (Safe 2 W, Nominal 4 W, Imaging 8 W, Downlink 10 W) are the values used in Chapters 4, 9 and 18.

| Subsystem | Safe (W) | Nominal (W) | Imaging (W) | Downlink (W) | Eclipse (W) |
|-----------|---------|---------|-------------|-------------|-------------|
| OBC | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| AOCS | 0.3 | 1.5 | 2.5 | 2.0 | 1.5 |
| Payload | 0 | 0 | 3.5 | 0 | 0 |
| Comms (RX always on; TX in downlink) | 0.2 | 0.5 | 0.5 | 6.0 | 0.5 |
| Thermal (heaters) | 0.5 | 1.0 | 0.5 | 1.0 | 0.5 |
| **Total** | **2.0** | **4.0** | **8.0** | **10.0** | **3.5** |

**Table 8.4** — EOSat-3U mode-based power budget. The eclipse column is the nominal mode with the thermal and AOCS loads of the eclipse arc; it is the $P_{\text{ecl}}$ used for battery sizing in Chapter 9.

### 8.4.4 Orbit-average power

> **Key equation — orbit-average power**
>
> $$P_{\text{avg}} = \sum_{\text{modes}} \left(P_{\text{mode}} \times \text{duty}_{\text{mode}}\right)$$
>
> **Example for the 94.6-min, 500 km orbit of Chapter 7 (58.8 min sunlight, 35.8 min eclipse):**
>
> | Mode | Power (W) | Duty (%) | Contribution (W) |
> |------|----------|----------|-------------------|
> | Nominal (sunlit) | 4.0 | 45 % | 1.80 |
> | Imaging | 8.0 | 10 % | 0.80 |
> | Downlink | 10.0 | 7 % | 0.70 |
> | Eclipse | 3.5 | 38 % | 1.33 |
> | **Total** | | **100 %** | **4.63 W** |

The orbit-average demand is what the solar array must deliver on average; the peak sunlit mode (10 W) and the eclipse load (3.5 W) are what size the array and the battery respectively (Chapter 9 §9.2–§9.3).

### 8.4.5 Other budget types (preview)

Each of the remaining budgets is developed in its own chapter:

| Budget | Key equation | Chapter |
|--------|-------------|---------|
| **Link** | $\text{Margin} = \text{EIRP} - \text{FSPL} + G/T - k - 10\log_{10}(R_b) - E_b/N_0$ | 11 |
| **Pointing** | $\theta_{\text{total}} = \sqrt{\sum \theta_i^2}$ (RSS) | 10 |
| **ΔV** | $\Delta V = I_{sp} \cdot g_0 \cdot \ln(m_0/m_f)$ (Tsiolkovsky) | 12 |
| **Data** | Daily downlink capacity ≥ daily generation | 11 |

---

## 8.5 Worked example: UniSat-1 architecture

Returning to UniSat-1, the 1U demonstrator of Chapter 1 §1.7: it shows that a 1U CubeSat can be built with a radically simplified architecture compared with the 3U EO mission. Several subsystems are eliminated entirely.

| Subsystem | EOSat-3U | UniSat-1 (1U) | Rationale for elimination |
|-----------|--------------|---------------|--------------------------|
| **EPS** | Required | **Required** | Always needed |
| **OBC** | Required | **Required** | Always needed (minimal: MSP430 or ARM Cortex-M class) |
| **Comms** | S-band + X-band | **UHF only** | 9600 bps is sufficient for < 1 kbps payload data |
| **Structure** | Required | **Required** | Always needed (COTS 1U frame) |
| **Payload** | Telescope (complex) | **MEMS magnetometer** (simple: 50 g, 0.2 W) | — |
| **AOCS** | Star tracker + RWs + MTQs | **Eliminated** | Passive magnetic only (permanent magnet + hysteresis rods, treated as structure, not a subsystem) |
| **Thermal** | MLI + heaters | **Eliminated** | Passive coatings only; 400 km LEO thermal environment is benign for a 6-month mission |
| **Propulsion** | May be needed | **Eliminated** | 400 km orbit decays naturally in under a year (Chapter 7 §7.7); no orbit maintenance needed |
| **Harness** | Significant | **Minimal** | Only 3–4 board-to-board connections via PC/104 stack |

**N² matrix — drastically reduced:** For UniSat-1 the interface matrix shrinks from 28 potential pairs (8 subsystems) to just 10 pairs (5 subsystems). The active interfaces are:

| Interface pair | Types | Key concern |
|----------------|-------|-------------|
| EPS ↔ OBC | E, D | Power regulation, housekeeping telemetry |
| EPS ↔ Comms | E | TX peak power (~0.5 W — small relative to budget) |
| EPS ↔ Payload | E | Payload switching (0.2 W — trivial) |
| OBC ↔ Comms | D, S | TM/TC packet routing |
| OBC ↔ Payload | D | Magnetometer data acquisition (I²C or SPI) |
| Structure ↔ All | M | Mounting, CDS rail compliance |

**Mass budget (Phase A):**

| Subsystem | CBE (g) | Equipment margin (20 %) | MEV (g) |
|-----------|---------|---------------------|---------|
| Payload (MEMS magnetometer) | 50 | 10 | 60 |
| EPS (board + battery + body-mounted cells) | 250 | 50 | 300 |
| OBC (MSP430/Cortex-M board) | 30 | 6 | 36 |
| Comms (UHF transceiver + antenna) | 80 | 16 | 96 |
| Structure (1U frame) | 200 | 40 | 240 |
| Passive magnetic AOCS (magnet + rods) | 30 | 6 | 36 |
| Harness | 50 | 10 | 60 |
| **Dry total** | **690** | | **828** |
| System margin (20 %) | | | **166** |
| **Dry MEV + system margin** | | | **994** |
| **CDS allocation** | | | **1330** |
| **Mass margin** | | | **336 g (25.3 %)** — Green |

**Power budget (all modes use the same simple duty cycle):**

| Mode | Power (W) | Duty (%) | Contribution (W) |
|------|----------|----------|-------------------|
| Idle (OBC + beacon) | 0.7 | 50 % | 0.35 |
| Science (+ magnetometer) | 0.9 | 10 % | 0.09 |
| Downlink (+ UHF TX) | 1.2 | 5 % | 0.06 |
| Eclipse (OBC only) | 0.5 | 35 % | 0.18 |
| **Orbit average** | | **100 %** | **0.68 W** |

With ~2 W available from body-mounted cells, the power margin is substantial (~1.3 W, or 66 %). This is one of the luxuries of a simple payload on a 1U bus.

**Key architectural insight:** The UniSat-1 architecture is so simple that a small team (3–5 people) can design, build, test and operate it. This makes it ideal for a university or educational programme. The concurrent-design process still applies — but the design loops are shorter and the trade space is narrower.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Mission segments | Space, Ground, Launch, User — each with defined interfaces |
| System architecture | Block diagram shows subsystems, data buses, power distribution |
| N² matrix | Maps all 28 potential interface pairs; 7 types (M, E, T, D, R, O, S); read row → column |
| Interface conflicts | Detect by comparing both sides of every cell; severity (critical/major/minor); 4 resolution options |
| Interface requirements | Formal boundary agreements; must be verifiable |
| Mass budget | CBE + equipment maturity margin = MEV; + system margin; compare to allocation |
| ECSS margins | Two levels: equipment 5/10/20 % by maturity; system 20/15/10/5 % by phase (Table 8.3) |
| Power budget | Mode-based; duty cycling gives orbit-average; SA must cover peak + recharge |
| Budget closure | Negative margin = design does not close; reduce demand or increase allocation |

## Problems

1. **Segments and interfaces.** For a 3U Earth-observation CubeSat that delivers imagery to agricultural users through a commercial ground-station network, list every segment, the elements in each, and the interface between each pair of segments with its type code (Table 8.2). Which segment interface is governed by a document the mission team does not control?

2. **Build an N² matrix.** Construct the full 8 × 8 N² matrix for the reference architecture of Figure 8.2 (Payload, EPS, AOCS, Comms, OBC, Thermal, Structure, Harness). Fill every active cell with the item delivered and its type code(s). Count the active pairs and compare with the 18–22 typical range.

3. **Conflict detection.** In your matrix from Problem 2, introduce three conflicts: a voltage mismatch, a protocol mismatch and a field-of-view obstruction. For each, classify the severity, choose a resolution option, and write the interface requirement that records the resolution.

4. **EMC interface.** The comms transmitter radiates 2 W at 2.2 GHz and the payload includes a GNSS receiver at 1.575 GHz. Explain why this is an R-type conflict even though the frequencies differ, propose two resolution options from §8.3.5, and write a verifiable interface requirement for the one you select.

5. **Mass budget by phase.** Take the EOSat-3U CBE values of §8.4.2 and recompute the mass margin against a 6.0 kg allocation for Phase B (assume the payload and AOCS are now off-the-shelf with minor modification, the rest new design) and for Phase C (all equipment off-the-shelf unmodified). At which phase does the budget turn green?

6. **Allocation sensitivity.** The launch provider reduces the 3U allocation from 6.0 kg to 5.5 kg. Using the Phase A budget of §8.4.2, compute the new margin and status. Identify the two subsystems whose CBE reduction would most quickly restore a 10 % margin and state how much each must lose.

7. **Mode-based power.** Using Table 8.4, compute the orbit-average power for a 92.6-min ISS-type orbit (36 min eclipse) in which imaging occupies 15 % and downlink 5 % of the orbit. Then recompute for a dawn–dusk Sun-synchronous orbit with no eclipse. By how much does the average demand change, and which subsystem rows are affected?

8. **UniSat-1 interfaces.** Write the complete 5 × 5 N² matrix for UniSat-1 (§8.5), including the Structure row and column, and tag every cell with type codes. Identify the single interface you would verify by test rather than by inspection, and justify.

9. **Budget tightness.** A design shows mass margin 12 %, power margin in imaging mode 4 %, link margin 6 dB and pointing margin 60 %. Which budget is tightest, what single design change would most improve it, and which other budgets would that change affect (trace the coupling through the N² matrix)?

## References

1. NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, §4.4 (Process 4) and §6.3 (Process 12: Interface Management). https://www.nasa.gov/reference/systems-engineering-handbook/
2. ECSS, *ECSS-E-ST-10-24C: Interface Management*, 2015. https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/
3. ECSS, *ECSS-E-HB-10-02A: Verification Guidelines*, 2010, §5.2 (Mass Margins). https://ecss.nl/hbstms/ecss-e-hb-10-02a-verification-guidelines/
4. ECSS, *ECSS-E-ST-10-02C Rev.1: Verification*, 2018. https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification-1-february-2018/
5. Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 10–11. https://www.space.com/smad
6. ECSS, *ECSS-E-ST-20C Rev.1: Electrical and Electronic*, 2019 (power budgets). https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/
7. ECSS, *ECSS-E-ST-10C Rev.1: System Engineering General Requirements*, 2017, §5.4. https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/
