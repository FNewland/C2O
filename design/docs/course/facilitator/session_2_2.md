# Session 2.2: Functional Decomposition

**Duration:** 2 hours
**Prerequisites:** Session 2.1 (requirements defined)
**References:** NASA SEH §4.3 (Process 3: Logical Decomposition), ECSS-E-ST-10C §5.3

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Decompose mission objectives into functions and subfunctions
2. Allocate functions to subsystems (with multi-allocation for shared responsibilities)
3. Derive requirements from functions
4. Identify coverage gaps (leaf functions without requirements)
5. Use SpaceCDF's function tree editor

---

## 1. What is Functional Decomposition? (20 min)

### Teaching Notes

*[Source: NASA SEH §4.3 -- Process 3: Logical Decomposition]*

Functional decomposition answers: **"What must the system DO to meet the requirements?"**

It bridges requirements (WHAT) and design (HOW) by identifying the functions the system must perform, without yet specifying the physical implementation.

### The Decomposition Flow

```
Objective: "Provide 10m imagery with 5-day revisit"
   ? what functions are needed?
F-001: Acquire imagery of target
   ??? F-002: Point instrument at target (needs: AOCS)
   ??? F-003: Store acquired data onboard (needs: OBC/storage)
   ??? F-004: Downlink data to ground station (needs: comms)

F-005: Generate electrical power (universal function)
F-006: Maintain thermal environment (universal function)
F-007: Survive launch environment (universal function)
F-008: Communicate with ground for TTC (universal function)
F-009: Dispose of spacecraft at end of life (universal function)
```

### Function Types

| Type | Description | Example |
|------|-------------|---------|
| **Observe** | Sense/measure the environment | Acquire imagery, receive AIS signals |
| **Communicate** | Transfer information | Downlink data, relay commands, uplink TC |
| **Navigate** | Determine/control position | Maintain orbit, perform manoeuvres |
| **Point** | Orient the spacecraft | Nadir pointing, target tracking, slewing |
| **Power** | Generate/store/distribute energy | Solar power generation, battery management |
| **Protect** | Maintain environment | Thermal control, radiation shielding |
| **Store** | Record data | Onboard data storage, buffering |
| **Process** | Transform data | On-board compression, L0 processing |
| **Support** | Structural/mechanical | Survive launch, deploy mechanisms |

### Universal Functions

Every spacecraft needs these regardless of mission type:
1. Generate electrical power
2. Maintain thermal environment
3. Survive launch environment
4. Communicate with ground (TTC)
5. Dispose of spacecraft at end of life

The SpaceCDF tool auto-generates these for every mission.

---

## 2. Mission-Type-Specific Functions (20 min)

### Teaching Notes

Different mission types require different primary function trees:

### Earth Observation (Optical/SAR)
```
F-001: Acquire imagery
   ??? Point instrument at target
   ??? Capture image data
   ??? Store data onboard
   ??? Downlink to ground
```

### Communications Relay
```
F-001: Relay communications between users
   ??? Receive uplink signal from user terminal
   ??? Process and route data (store-and-forward or bent-pipe)
   ??? Transmit downlink signal to destination
```

### AIS / IoT Receiver
```
F-001: Receive and process signals of interest
   ??? Receive AIS/IoT signals (passive receive)
   ??? Decode and validate messages
   ??? Store processed data
   ??? Downlink to ground for distribution
```

### Ground Segment Functions

Missions that include ground processing need ground-side functions:
```
F-G01: Receive satellite data at ground station
F-G02: Process data (L0 -> L1 -> L2)
F-G03: Archive and distribute to users
F-G04: Operate mission control centre
```

SpaceCDF supports ground allocation domains: `ground_station`, `ground_processing`, `ground_sensor`.

---

## 3. Allocation to Subsystems (25 min)

### Teaching Notes

Each function must be **allocated** to one or more responsible subsystems. This allocation defines the system boundaries.

### Allocation Rules

| Function | Typical Allocation | Multi-allocation? |
|----------|-------------------|-------------------|
| Acquire imagery | Payload | No (single owner) |
| Point at target | AOCS | No |
| Store data | OBC/Data | No |
| Downlink data | Link (+ AOCS for pointing) | Yes -- link for RF chain, AOCS for antenna pointing |
| Generate power | Power | No |
| Maintain thermal | Thermal | No |
| Relay communications | Payload + Link | Yes -- boundary depends on architecture |

### Multi-Allocation and System Boundaries

Some functions can reasonably be allocated to more than one subsystem. This creates an **interface** between those subsystems that must be managed.

**Example:** "Downlink data to ground station"
- Link subsystem: transponder, antenna, modulation
- AOCS subsystem: antenna pointing towards ground station
- Data handling: data packaging, prioritisation, error correction

SpaceCDF allows multi-allocation (comma-separated domains).

**Discussion prompt:** *For each multi-allocated function, where should the system boundary be drawn? Who "owns" the function?*

### Derived Requirements

Each function generates **derived requirements** -- requirements not explicitly stated by stakeholders but necessary for the function to work:

| Function | Derived Requirement |
|----------|-------------------|
| "Point instrument at target" | "AOCS shall provide <= 0.1° pointing accuracy during imaging" |
| "Store data onboard" | "OBDH shall provide >= 32 GB solid-state storage" |
| "Downlink within daily contact window" | "TX shall provide >= 50 Mbps data rate" |

*[Source: NASA SEH §4.3.3 -- derived requirements from functional allocation]*

---

## 4. Performance Criteria (15 min)

### Teaching Notes

Each function should have **performance criteria** -- quantitative measures that define "how well" the function must be performed:

| Function | Performance Criteria |
|----------|---------------------|
| Acquire imagery | GSD <= 10 m; SNR >= 100:1; 4+ spectral bands |
| Point at target | Accuracy <= 0.1°; stability <= 0.01°/s; slew rate >= 1°/s |
| Downlink data | Link margin >= 3 dB; daily throughput >= 5 GB |
| Generate power | Positive margin in all modes; battery DoD <= 30% |

Performance criteria form the basis for subsystem-level requirements.

### Coverage Check

Every **leaf function** (a function with no subfunctions) should trace to at least one requirement. If it doesn't, there's a **coverage gap** -- the function is defined but has no verification path.

SpaceCDF shows coverage status:
- Green badge: function has linked requirements
- Amber badge: "no requirements" -- coverage gap

---

## 5. SpaceCDF Function Tree Exercise (40 min)

### Instructions

1. Navigate to the **Functions** tab
2. The tool auto-generates functions based on your mission type
3. Review: are the functions appropriate for YOUR mission?
   - For comms missions: should show relay/receive/transmit (not multispectral imagery)
   - For EO missions: should show acquire/point/store/downlink
4. Edit functions:
   - Click **edit** to change name, domain allocation, performance criteria
   - Click **+sub** to add subfunctions
   - Click **x** to remove inappropriate functions
5. Add ground segment functions if your mission includes ground processing
6. Check coverage: are there leaf functions without requirements?

### Worksheet 2.2 Tasks

1. Draw your function tree (3 levels minimum)
2. For each leaf function, write one derived requirement
3. Create a function-to-requirement traceability table
4. Identify any multi-allocated functions and define the interface

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Functions | WHAT the system does, not HOW -- bridges requirements to design |
| Types | Observe, communicate, navigate, point, power, protect, store, process, support |
| Mission-specific | Different mission types need different primary function trees |
| Allocation | Each function assigned to subsystem(s); multi-allocation creates interfaces |
| Derived requirements | Functions generate new requirements not stated by stakeholders |
| Coverage | Every leaf function must trace to at least one requirement |
