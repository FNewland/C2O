# Session 1.4: Concept of Operations

**Duration:** 2 hours
**Prerequisites:** Sessions 1.1-1.3 (need defined, trade completed)
**References:** NASA SEH Appendix S (ConOps Outline), ECSS-E-ST-70C

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the three segments of a space mission architecture
2. Define mission phases from LEOP through disposal
3. Design operational modes with power and data implications
4. Trace data flow from instrument through to end user
5. Use SpaceCDF's ConOps editor to document the operational concept

---

## 1. Mission Architecture (30 min)

### Teaching Notes

Every space mission has three segments that must be designed together:

### Space Segment
- **Platform (bus)**: EPS, AOCS, OBC, thermal, structure, propulsion
- **Payload/Sensor**: The instrument(s) that fulfil the mission objectives
- **Communications**: TT&C for commanding + payload data downlink

### Ground Segment
This is NOT a single entity -- it typically has two distinct functions:

- **Ground Operations** (GS + MCC): Commanding, telemetry monitoring, orbit determination, anomaly response
- **Payload Data Centre**: Data reception, processing (L0->L1->L2->L3), archival, distribution

For CubeSat missions, these may be combined, but the functions are still distinct.

### User Segment
- **Data products and services**: the deliverables to end users
- **APIs, portals, archives**: how users access the data
- **Training and documentation**: how users interpret the data

### Data Interfaces

| Interface | Direction | Type | Example |
|-----------|-----------|------|---------|
| TM/TC (S-band) | Space <-> Ground Ops | RF uplink/downlink | Housekeeping telemetry, commands |
| Payload data (X-band) | Space -> Data Centre | RF downlink | Science/imagery data |
| Orbit/TLE | Ground Ops -> Data Centre | Network | Geolocation metadata |
| Data products | Data Centre -> Users | Internet/API | L2/L3 processed imagery |

### Additional Architecture Options

| Option | Description | When to Use |
|--------|-------------|-------------|
| **Inter-satellite link** | Direct data relay between satellites | Constellations, reducing latency |
| **Store-and-forward** | Ground station stores data, forwards on schedule | Delay-tolerant applications |
| **Bent-pipe relay** | Satellite relays data without processing | TDRSS-style, reducing ground contacts needed |
| **Ground sensor ingestion** | Ground sensors feed data into system | Calibration/validation, multi-source fusion |

### Formula: Ground Station Coverage

The maximum slant range *R* from a ground station at elevation angle *?* above the horizon:

```
R = R_E × [ ?( (h/R_E + 1)^2 - cos^2(?) ) - sin(?) ]
```

Where *R_E* = 6371 km (Earth radius), *h* = orbit altitude (km), *?* = minimum elevation angle.

The fraction of each orbit visible from a single ground station at latitude *?_gs*:

```
contact_fraction ~ (2 × arccos(cos(?_max) / cos(?_gs - i))) / 360°
```

This is a rough estimate; actual contact geometry depends on orbit propagation.

**SpaceCDF exercise:** *In the ConOps tab, examine the mission architecture diagram. Identify the three segments and the data interfaces between them.*

---

## 2. Mission Phases (25 min)

### Teaching Notes

*[Source: ECSS-M-ST-10C Rev.1 for phase definitions; NASA SEH §3 for operational phase concepts]*

Every mission goes through these operational phases:

### LEOP (Launch and Early Orbit Phase)
- **Duration:** Hours to days (typically 1-3 days for CubeSat)
- **Activities:** Deployment from deployer, antenna deployment, first contact acquisition, initial health check
- **Risks:** Deployment failure, tumbling, no first contact
- **Power:** Battery-only until solar array deployment confirmed
- **Comms:** Beacon mode only; ground station must acquire signal

### Commissioning
- **Duration:** 2-8 weeks (CubeSat typical: 2-4 weeks)
- **Activities:** Subsystem checkout, calibration, sensor characterisation, orbit determination
- **Key milestones:** First light (first payload data), attitude control verified, link budget verified
- **Risks:** Subsystem anomalies, calibration issues

### Nominal Operations
- **Duration:** Months to years (design lifetime)
- **Activities:** Routine data acquisition, downlink, orbit maintenance (if applicable)
- **Modes:** Science/imaging, downlink, safe mode, eclipse
- **Ground ops:** Automated commanding with human oversight

### Extended Operations (optional)
- **Duration:** Beyond design lifetime
- **Activities:** Continued operations with degraded performance
- **Decisions:** Is the data still valuable? Are resources available to operate?
- **Considerations:** Component aging, solar array degradation, propellant depletion

### Disposal
- **Duration:** Days to weeks for active deorbit; years for natural decay
- **Activities:** Passivation (battery discharge, RF shutdown, wheel spin-down), deorbit manoeuvre (if propulsive)
- **Regulations:** 
  - IADC: post-mission orbital lifetime <= 25 years
  - FCC (2024+): post-mission orbital lifetime <= 5 years
  - ECSS-U-AS-10C Rev.2: debris mitigation compliance

---

## 3. Operational Modes (30 min)

### Teaching Notes

Each operational mode defines which subsystems are active, the pointing mode, power demand, and data flow. Mode design drives the power budget through duty cycling.

### Typical CubeSat Modes

| Mode | Subsystems Active | Pointing | Power | Data Flow |
|------|-------------------|----------|-------|-----------|
| **Safe** | EPS, OBC, TTC (beacon), AOCS (coarse) | Sun-pointing | Minimum (~1-2 W) | Beacon only -> ground |
| **Idle/Housekeeping** | EPS, OBC, AOCS (standby), TTC (beacon) | Inertial hold | Low (~2 W) | Health TM periodically |
| **Science/Imaging** | + Payload, AOCS (fine) | Nadir/target | Medium (~6 W) | Instrument -> OBDH storage |
| **Downlink** | + TTC (full TX) | Ground station | High (~8 W) | OBDH -> TX -> GS |
| **Eclipse** | EPS (battery), OBC, TCS (heaters), AOCS (coarse) | Inertial hold | Battery only (~3 W) | None |
| **Orbit Maintenance** | + Propulsion | Thrust direction | High | Manoeuvre TM |

### Duty Cycling -- The Key to CubeSat Power Management

CubeSats have limited power (7-25 W for a 3U with deployable panels). Not all modes run simultaneously. The orbit timeline determines what can happen when:

**Typical 95-minute orbit for 500 km SSO:**
- 60 min sunlight, 35 min eclipse
- ~10 min imaging per orbit (payload duty cycle ~10%)
- ~8 min downlink per pass (1-2 passes per day)
- ~40 min idle (housekeeping only)
- 35 min eclipse (battery-powered)

### Formula: Orbit-Average Power

```
P_avg = ? (P_mode × duty_cycle_mode)
```

The solar array must provide enough power during sunlight to:
1. Run the current sunlight mode
2. Recharge the battery for eclipse loads

```
P_SA = P_max_sunlight_mode + (P_eclipse × t_eclipse) / (t_sunlight × eta_charge)
```

Where *eta_charge* ~ 0.9 (battery charge efficiency).

*[Verified: this formula is consistent with SMAD4 §11.4 and ECSS-E-ST-20C power budget methodology]*

**Exercise:** *In the SpaceCDF ConOps tab, review the operational modes. Then check the Parametric tab to see how duty cycles are estimated. Calculate the orbit-average power for your mission.*

---

## 4. Data Flow Pipeline (15 min)

### Teaching Notes

The data pipeline determines end-to-end latency and drives the comms architecture:

```
Instrument -> Onboard Storage -> Downlink -> Ground Reception
  -> Processing (L0->L1->L2) -> Archive -> User Delivery
```

### Pipeline Sizing

| Stage | Key Parameter | Driven By |
|-------|--------------|-----------|
| Generation | GB/day | Payload data rate × duty cycle |
| Storage | GB | Must hold >=1 day of data (2× for margin) |
| Downlink | GB/pass | Link data rate × contact time per pass |
| Processing | hours | Algorithm complexity, compute resources |
| Delivery | hours | Archive system, API, network bandwidth |

### Data Budget Rule

For the system to be sustainable:

```
Daily_Downlink_Capacity >= Daily_Data_Generation
```

If downlink < generation, data accumulates on board and eventually the storage fills. Solutions:
- Increase downlink rate (higher-band TX, better antenna)
- Increase contact time (more ground stations, higher orbit)
- Reduce data generation (lower duty cycle, compression, on-board processing)

**SpaceCDF exercise:** *Check the Data Budget on the Dashboard. Does your design balance? If not, what would you change?*

---

## 5. ConOps Exercise (20 min)

### Instructions

1. Navigate to the **ConOps** tab in SpaceCDF
2. Review the mission architecture diagram -- identify each segment
3. Edit the **mission phases**: adjust durations for your mission
4. Review the **operational modes**: are the right modes defined for your mission type?
5. Check the **data flow pipeline**: does it match your architecture?

**Worksheet 1.4:** Document your ConOps outline per NASA SEH Appendix S structure.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Architecture | Three segments (space, ground, user) with distinct interfaces |
| Ground segment | Separate ops station from data processing -- different functions |
| Phases | LEOP -> commissioning -> nominal -> disposal (each with distinct risks) |
| Modes | Duty cycling is critical for CubeSat power management |
| Data pipeline | Downlink capacity must exceed data generation rate |
| Disposal | FCC 5-year rule (2024+) affects orbit selection |
