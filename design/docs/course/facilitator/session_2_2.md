# Session 2.2: Functional Decomposition and Allocation


**Prerequisites:** Session 2.1 (requirements defined and validated)
**SpaceCDF Tab:** Functions

---

## References

- [NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, Sec. 4.3 (Process 3: Logical Decomposition)](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ECSS, *ECSS-E-ST-10C Rev.1: System Engineering General Requirements*, 2017, Sec. 5.3](https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/)
- [INCOSE, *Systems Engineering Handbook*, 5th ed., 2023, Ch. 2.3.5.3](https://www.incose.org/products-and-publications/se-handbook)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 2](https://www.space.com/smad)
- [Blanchard & Fabrycky, *Systems Engineering and Analysis*, 5th ed., 2010, Ch. 3](https://www.pearson.com/en-us/subject-catalog/p/systems-engineering-and-analysis/P200000003502)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Explain the purpose of functional decomposition in bridging requirements to design
2. Decompose mission objectives into a hierarchical function tree (3+ levels)
3. Categorise functions by type (observe, communicate, navigate, point, power, protect, store, process, support)
4. Allocate functions to subsystem domains, including multi-allocation for shared responsibilities
5. Derive requirements from functional analysis
6. Identify and resolve coverage gaps (leaf functions without linked requirements)
7. Use SpaceCDF's function tree editor to build and validate a function architecture

---

## 1. What is Functional Decomposition?
*[Source: NASA SEH Sec. 4.3 -- Process 3: Logical Decomposition]*

Functional decomposition answers: **"What must the system DO to satisfy the requirements?"**

It creates a bridge between requirements (WHAT the system must achieve) and physical design (HOW it will be built). Functions describe *actions* the system must perform, without specifying the physical hardware or software that will perform them.

### The Decomposition Flow

<svg viewBox="0 0 800 360" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 12px;">
  <!-- Boxes -->
  <rect x="250" y="10" width="300" height="40" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="400" y="35" text-anchor="middle" fill="#1e40af" font-weight="bold">Objectives & Requirements</text>
  <!-- Arrow -->
  <line x1="400" y1="50" x2="400" y2="80" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead)"/>
  <rect x="250" y="80" width="300" height="40" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="105" text-anchor="middle" fill="#92400e" font-weight="bold">Functional Analysis (WHAT)</text>
  <line x1="400" y1="120" x2="400" y2="150" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead)"/>
  <rect x="250" y="150" width="300" height="40" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="400" y="175" text-anchor="middle" fill="#166534" font-weight="bold">Physical Architecture (HOW)</text>
  <!-- Side annotations -->
  <text x="570" y="70" fill="#64748b" font-size="11">Bridges the gap</text>
  <!-- Function tree below -->
  <rect x="100" y="230" width="180" height="30" rx="4" fill="#fef3c7" stroke="#d97706"/>
  <text x="190" y="250" text-anchor="middle" fill="#92400e" font-size="11">F-001: Acquire Imagery</text>
  <!-- Children -->
  <line x1="190" y1="260" x2="100" y2="290" stroke="#d97706"/>
  <line x1="190" y1="260" x2="280" y2="290" stroke="#d97706"/>
  <line x1="190" y1="260" x2="460" y2="290" stroke="#d97706"/>
  <rect x="20" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="100" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-002: Point at target</text>
  <rect x="200" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="280" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-003: Capture image data</text>
  <rect x="380" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="460" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-004: Store data onboard</text>
  <!-- Universal functions -->
  <rect x="580" y="230" width="180" height="30" rx="4" fill="#e0e7ff" stroke="#4f46e5"/>
  <text x="670" y="250" text-anchor="middle" fill="#3730a3" font-size="11">Universal Functions</text>
  <text x="670" y="280" text-anchor="middle" fill="#3730a3" font-size="10">F-010: Generate power</text>
  <text x="670" y="296" text-anchor="middle" fill="#3730a3" font-size="10">F-011: Maintain thermal env</text>
  <text x="670" y="312" text-anchor="middle" fill="#3730a3" font-size="10">F-012: Survive launch</text>
  <text x="670" y="328" text-anchor="middle" fill="#3730a3" font-size="10">F-013: TTC with ground</text>
  <text x="670" y="344" text-anchor="middle" fill="#3730a3" font-size="10">F-014: Dispose at EOL</text>
  <defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
</svg>

### Function Types

Every spacecraft function falls into one of these categories:

| Type | Verb | Description | Example |
|------|------|-------------|---------|
| **Observe** | Sense/measure | Acquire data from the environment | Capture multispectral imagery, receive AIS signals |
| **Communicate** | Transfer | Move information between elements | Downlink science data, uplink telecommands |
| **Navigate** | Determine/control position | Know or change the orbit | Perform orbit maintenance manoeuvre |
| **Point** | Orient | Control spacecraft attitude | Nadir pointing during imaging, target tracking |
| **Power** | Generate/store/distribute | Provide electrical energy | Solar power generation, battery charge management |
| **Protect** | Maintain environment | Keep components within limits | Thermal control, radiation shielding |
| **Store** | Record | Buffer data for later use | Onboard solid-state data recording |
| **Process** | Transform | Convert data between forms | On-board image compression, L0 framing |
| **Support** | Provide structure | Mechanical integrity | Survive launch loads, deploy mechanisms |

### Universal Functions

Regardless of mission type, **every spacecraft** must perform these five functions:

1. **Generate electrical power** (solar, RTG, battery)
2. **Maintain thermal environment** (passive/active thermal control)
3. **Survive the launch environment** (structural loads, vibration, shock)
4. **Communicate with ground for TTC** (telemetry, tracking, command)
5. **Dispose of the spacecraft at end of life** (deorbit, graveyard, passivation)

SpaceCDF auto-generates these universal functions for every mission.

---

## 2. Mission-Type-Specific Function Trees
Different mission types produce fundamentally different primary function trees. The universal functions remain the same; it is the mission-specific branch that differentiates.

### Earth Observation (Optical/SAR)

```
F-001: Acquire imagery of target area
  +-- F-002: Point instrument at target
  +-- F-003: Capture image data (expose detector / SAR pulse)
  +-- F-004: Store acquired data onboard
  +-- F-005: Downlink data to ground station
```

**Real example -- Planet SuperDove:** F-001 decomposes into 8-band pushbroom acquisition, on-board radiometric correction, lossless compression, and X-band downlink. Each sub-function traces to specific SuperDove requirements (3.7 m GSD, 8 spectral bands, 200 Mbps downlink).

### Communications Relay (Store-and-Forward or Bent-Pipe)

```
F-001: Relay communications between users
  +-- F-002: Receive uplink signal from user terminal
  +-- F-003: Process and route data (store-and-forward or bent-pipe)
  +-- F-004: Transmit downlink signal to destination terminal or gateway
```

**Real example -- Astrocast (IoT):** F-001 decomposes into L-band receive (from IoT devices), on-board message deduplication and store-and-forward, and UHF/S-band downlink to gateway stations. Each message is <= 160 bytes.

*[Source: Astrocast, "Astrocast Network Overview," astrocast.com]*

### AIS/IoT Receiver (Passive)

```
F-001: Receive and process signals of interest
  +-- F-002: Receive AIS/IoT signals (passive -- no uplink transmission)
  +-- F-003: Decode and validate messages
  +-- F-004: Store processed data onboard
  +-- F-005: Downlink to ground for distribution
```

### Ground Segment Functions

Missions that include ground-side processing need ground-domain functions:

```
F-G01: Receive satellite data at ground station
F-G02: Process data pipeline (L0 -> L1 -> L2 products)
F-G03: Archive and distribute data products to users
F-G04: Operate mission control centre (planning, commanding, monitoring)
```

SpaceCDF supports allocation to ground domains: `ground_station`, `ground_processing`, `ground_sensor`.

---

## 3. Allocation to Subsystems
Each function must be **allocated** to one or more responsible subsystem domains. This allocation defines system boundaries and, critically, identifies **interfaces** wherever a function is shared.

### Allocation Rules

| Function | Typical Allocation | Multi-allocation? |
|----------|-------------------|-------------------|
| Acquire imagery | Payload | No (single owner) |
| Point at target | AOCS | No |
| Store data | OBC/Data Handling | No |
| Downlink data | Comms + AOCS | **Yes** -- comms for RF chain, AOCS for antenna pointing |
| Generate power | EPS | No |
| Maintain thermal | Thermal | No |
| Relay communications | Payload + Comms | **Yes** -- boundary depends on architecture |
| Survive launch | Structure | No |
| Dispose at EOL | Propulsion (or Ops) | No (or multi if drag-sail) |

### Multi-Allocation and Interface Identification

When a function is allocated to more than one subsystem, it creates an **interface** that must be explicitly managed.

**Example -- "Downlink data to ground station":**

| Responsible Subsystem | Contribution | Interface Created |
|-----------------------|-------------|-------------------|
| Comms (Link) | Transponder, antenna, modulation, RF chain | Comms <-> AOCS (antenna pointing) |
| AOCS | Antenna pointing towards ground station during pass | Comms <-> Data Handling (packet routing) |
| Data Handling | Data packaging, prioritisation, CCSDS framing | Data Handling <-> AOCS (pass scheduling) |

SpaceCDF supports multi-allocation by entering comma-separated domains.

**Discussion point.** *For each multi-allocated function in your design, where should the system boundary be drawn? Who "owns" the function, and who is a "contributor"?*

### Derived Requirements from Functions

Each allocated function generates **derived requirements** -- requirements not explicitly stated by stakeholders but necessary for the function to work:

| Function | Derived Requirement | Derivation Logic |
|----------|-------------------|------------------|
| "Point instrument at target" | "AOCS shall provide <= 0.1 deg pointing accuracy during imaging" | From GSD requirement + optical geometry |
| "Store data onboard" | "OBDH shall provide >= 32 GB solid-state storage" | From data rate x orbit period x missed-pass margin |
| "Downlink within daily contact window" | "TX shall provide >= 50 Mbps effective data rate" | From daily data volume / total contact time |
| "Generate power in all modes" | "SA shall produce >= 15 W EOL" | From worst-case sunlit power demand + recharge |

*[Source: NASA SEH Sec. 4.3.3 -- derived requirements from functional allocation]*

---

## 4. Performance Criteria and Coverage Analysis
Each leaf function (a function with no sub-functions) must have **performance criteria** -- quantitative thresholds that define "how well" the function must be performed:

| Function | Performance Criteria |
|----------|---------------------|
| Acquire imagery | GSD <= 10 m; SNR >= 100:1; >= 4 spectral bands |
| Point at target | Accuracy <= 0.1 deg; stability <= 0.01 deg/s; slew rate >= 1 deg/s |
| Downlink data | Link margin >= 3 dB; daily throughput >= 5 GB |
| Generate power | Positive margin in all modes; battery DOD <= 30% |
| Maintain thermal env | All components within operating range with >= 5 degC margin |

Performance criteria form the quantitative basis for subsystem-level requirements.

### Coverage Analysis

**Every leaf function** must trace to at least one requirement. If it does not, there is a **coverage gap** -- the function is defined but has no verification path.

SpaceCDF shows coverage status with badges:

- **Green badge:** Function has linked requirements (covered)
- **Amber badge:** "No requirements" -- coverage gap detected
- **Red badge:** Function conflicts with existing requirements

### Real Mission Example: CAPSTONE Coverage Gap

NASA's CAPSTONE mission (2022, Advanced Space) experienced a coverage gap during development: the "maintain attitude during trajectory correction manoeuvre" function initially had no formal pointing requirement during burns. This gap was identified during functional review and led to the derivation of SSR-AOCS-007: "The AOCS shall maintain pointing accuracy <= 2 deg during all propulsive manoeuvres."

*[Source: Advanced Space, "CAPSTONE Mission Overview," 2022]*

---

## 5. SpaceCDF Function Tree Exercise
### Instructions

1. Navigate to the **Functions** tab in SpaceCDF
2. The tool auto-generates functions based on your selected mission type
3. **Review the generated tree:** Are the functions appropriate for YOUR mission?
   - For comms missions: should show relay/receive/transmit (not multispectral imagery)
   - For EO missions: should show acquire/point/store/downlink
   - For technology demos: should show demonstrate/characterise/report
4. **Edit functions:**
   - Click **edit** to change name, domain allocation, or performance criteria
   - Click **+sub** to add sub-functions (decompose further)
   - Click **x** to remove inappropriate functions
5. **Add ground segment functions** if your mission includes ground processing
6. **Check multi-allocation:** For any function allocated to multiple domains, verify the interface is captured
7. **Coverage check:** Are there any leaf functions (amber badge) without linked requirements? Derive requirements for them.

### Exercise Tasks

1. Build a function tree with at least 3 levels of decomposition
2. For each leaf function, write one derived requirement with a measurable threshold
3. Create a function-to-requirement traceability table (minimum 8 entries)
4. Identify at least one multi-allocated function and define the interface boundary
5. Complete Worksheet 2.2

---

## Worked Example: 3U EO CubeSat Function Tree

> **Function Tree for Agricultural Monitoring CubeSat**
>
> ```
> F-001: Acquire multispectral imagery
>   +-- F-002: Point telescope at target area (AOCS)
>   +-- F-003: Expose detector and capture image frames (Payload)
>   +-- F-004: Compress and store image data (OBC)
>   +-- F-005: Downlink stored data to ground station (Comms + AOCS)
>
> F-010: Generate electrical power (EPS)
>   +-- F-011: Convert solar energy to electrical (SA)
>   +-- F-012: Store energy for eclipse (Battery)
>   +-- F-013: Regulate and distribute power (EPS board)
>
> F-020: Maintain thermal environment (Thermal)
>   +-- F-021: Reject waste heat from electronics (Radiator)
>   +-- F-022: Maintain battery temperature during eclipse (Heater)
>
> F-030: Survive launch environment (Structure)
> F-040: Communicate with ground for TTC (Comms)
> F-050: Dispose at end of life (Propulsion/Ops)
> ```
>
> **Derived requirements from F-002 (Point telescope at target):**
> - SSR-AOCS-001: "The AOCS shall achieve <= 0.5 deg pointing accuracy during imaging mode"
> - SSR-AOCS-002: "The AOCS shall achieve pointing stability <= 0.01 deg/s during imaging"
>
> **Multi-allocation for F-005 (Downlink data):**
> - Comms subsystem: owns RF chain (transponder, antenna, modulation)
> - AOCS subsystem: provides antenna pointing towards ground station
> - Interface: AOCS must receive pass-schedule triggers from OBC to initiate slew to ground station pointing

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Functional decomposition | Bridges requirements (WHAT) to design (HOW) by identifying system actions |
| Function types | Observe, Communicate, Navigate, Point, Power, Protect, Store, Process, Support |
| Universal functions | Power, thermal, launch survival, TTC, disposal -- every spacecraft needs all five |
| Mission-specific trees | EO: acquire/point/store/downlink; Comms: receive/route/transmit; AIS: receive/decode/store |
| Allocation | Each function assigned to subsystem domain(s); multi-allocation creates interfaces |
| Derived requirements | Functions generate new requirements not stated by stakeholders |
| Coverage analysis | Every leaf function must trace to at least one requirement -- no gaps allowed |
