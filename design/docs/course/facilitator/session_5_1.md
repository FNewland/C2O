# Session 5.1: Ground Segment & Operations Architecture

**Duration:** 2 hours
**Prerequisites:** Week 2 complete (full design cycle through cost estimation)
**References:** ECSS-E-ST-70C (Ground Systems), ECSS-E-ST-70-01C (Ground Segment), CCSDS 131.0-B-4 (TM Coding), CCSDS 231.0-B-4 (TC Coding), CCSDS 133.0-B-2 (Space Packet Protocol), NASA DSN Handbook (810-005)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the components of a ground segment architecture (antennas, MCS, FDS, networks)
2. Calculate ground station contact time and data volume per pass
3. Explain the CCSDS protocol stack for space communication
4. Design a ground station network for a given orbit and data downlink requirement
5. Construct a mission operations timeline with key milestones

---

## 1. Ground Segment Architecture (25 min)

### Teaching Notes

The ground segment is everything on the ground that supports the space mission. It is frequently underestimated in early mission design but accounts for 5-15% of total mission cost and is critical to mission success.

*[Source: ECSS-E-ST-70C (Ground Systems and Operations); ECSS-E-ST-70-01C (Ground Segment)]*
*[URL: https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/]*

### Ground Segment Components

```
+------------------------------------------------------------------+
|                        GROUND SEGMENT                            |
|                                                                  |
|  +------------------+    +------------------+    +-----------+   |
|  | Ground Station   |    | Mission Control  |    | Flight    |   |
|  | Network          |    | System (MCS)     |    | Dynamics  |   |
|  |                  |    |                  |    | System    |   |
|  | - Antenna(s)     |    | - TM processing |    | (FDS)     |   |
|  | - RF front-end   |    | - TC generation  |    |           |   |
|  | - Modem/baseband |    | - Scheduling     |    | - Orbit   |   |
|  | - Tracking       |    | - Monitoring     |    |   determ. |   |
|  | - Data capture   |    | - Anomaly mgmt  |    | - Maneuver|   |
|  +--------+---------+    +--------+---------+    |   planning|   |
|           |                       |               +-+---+-----+   |
|           |    Data Network       |                 |   |         |
|           +----------+------------+-----------------+   |         |
|                      |                                  |         |
|  +------------------+v--+    +--------------------+     |         |
|  | Mission Planning     |    | Data Processing &  |     |         |
|  | System               |    | Archiving          |     |         |
|  | - Pass scheduling    |    | - Level 0-2 data   |     |         |
|  | - Resource planning  |    | - Archive/catalog  |     |         |
|  | - Conflict resoln.   |    | - Distribution     |     |         |
|  +----------------------+    +--------------------+     |         |
+------------------------------------------------------------------+
```

### Ground Station Components

| Component | Function | Typical Specification |
|-----------|----------|---------------------|
| **Antenna** | Transmit uplink commands, receive downlink telemetry | 3-13 m dish (S/X-band); Yagi/turnstile (UHF) |
| **RF front-end** | Low-noise amplifier (LNA), power amplifier, filters | LNA NF < 1 dB; PA 50-500 W |
| **Modem/baseband** | Modulation/demodulation, coding/decoding | CCSDS-compliant; BPSK/QPSK/8PSK |
| **Tracking system** | Antenna pointing, Doppler tracking, ranging | Autotrack or program-track |
| **Data capture** | Record raw baseband data for post-processing | High-speed disk array |
| **Timing** | GPS-disciplined oscillator for time synchronisation | < 1 microsecond accuracy |

### Mission Control System (MCS)

| Function | Description | Tools |
|----------|------------|-------|
| **Telemetry processing** | Decode, decommutate, display, and archive TM packets | COSMOS, YAMCS, EGOS (ESA) |
| **Telecommand generation** | Create, validate, encode, and uplink TC packets | Same MCS tools |
| **Pass scheduling** | Schedule antenna time, plan contact windows | STK, GMAT, custom schedulers |
| **Monitoring & control** | Real-time health monitoring, limit checking, alarming | MCS dashboards |
| **Anomaly management** | Detect, diagnose, and resolve anomalies | Procedures + expert judgment |

### Flight Dynamics System (FDS)

| Function | Description | Inputs |
|----------|------------|--------|
| **Orbit determination** | Compute current orbit from tracking data | Range, Doppler, GPS (if onboard) |
| **Orbit prediction** | Propagate orbit forward for pass planning | Current state vector, perturbation models |
| **Manoeuvre planning** | Compute delta-V for orbit maintenance | Target orbit, propulsion model |
| **Conjunction assessment** | Predict close approaches with debris/other objects | TLE catalogue, own orbit |
| **End-of-life planning** | Compute deorbit manoeuvre or passivation plan | Remaining propellant, target orbit |

---

## 2. Ground Station Contact Analysis (25 min)

### Teaching Notes

Understanding how much data can be transferred per pass is fundamental to mission design. The data budget depends on the contact geometry, data rate, and pass duration.

### Contact Geometry

For a circular LEO orbit, the visibility of a ground station is determined by the minimum elevation angle constraint.

> **Maximum Slant Range at Minimum Elevation:**
>
> rho = R_E x (sqrt((h/R_E + 1)^2 - cos^2(epsilon)) - sin(epsilon))
>
> Where:
> - R_E = Earth radius (6371 km)
> - h = orbital altitude
> - epsilon = minimum elevation angle (typically 5-10 degrees)
>
> For h = 500 km, epsilon = 5 degrees:
> rho = 6371 x (sqrt((500/6371 + 1)^2 - cos^2(5)) - sin(5))
> rho = 6371 x (sqrt(1.0785^2 - 0.9962^2) - 0.0872)
> rho = 6371 x (sqrt(1.1632 - 0.9924) - 0.0872)
> rho = 6371 x (sqrt(0.1708) - 0.0872)
> rho = 6371 x (0.4133 - 0.0872)
> rho = 6371 x 0.3261
> rho = 2077 km

> **Maximum Pass Duration (overhead pass):**
>
> T_max = 2 x R_E x arccos(R_E x cos(epsilon) / (R_E + h)) / V_ground_track
>
> Simplified approximation for LEO:
> T_max ~ (2 x rho_max) / V_orbital x (R_E / (R_E + h))
>
> For 500 km SSO:
> V_orbital = sqrt(mu / (R_E + h)) = sqrt(3.986e14 / 6.871e6) = 7613 m/s
> T_max ~ 2 x 2077e3 / 7613 x (6371/6871) ~ 505 s ~ 8.4 minutes
>
> *Typical average pass duration (not all passes are overhead): ~6 minutes*

> **Data Volume per Pass:**
>
> V_data = R_data x T_contact x eta_protocol
>
> Where:
> - R_data = downlink data rate (bps)
> - T_contact = contact duration (seconds)
> - eta_protocol = protocol efficiency (typically 0.85-0.95 for CCSDS)
>
> Example: R = 2 Mbps, T = 360 s (6 min average), eta = 0.9:
> V_data = 2e6 x 360 x 0.9 = 648 Mbit = 81 MB per pass

### Contact Frequency

| Orbit | GS Latitude | Passes per Day | Avg Duration | Daily Data Volume (2 Mbps) |
|-------|-------------|----------------|-------------|---------------------------|
| 500 km SSO | 52 N (e.g., Waterloo) | 3-5 | 6 min | 243-405 MB |
| 500 km SSO | 69 N (e.g., Kiruna) | 6-8 | 7 min | 544-726 MB |
| 500 km, 51.6 (ISS) | 52 N | 2-4 | 5 min | 130-260 MB |
| 500 km SSO | SatNOGS network (global) | 10-15 | 5 min | 648-972 MB |

*[Source: STK simulations; validated against SatNOGS observation logs]*

### Worked Example: Data Budget Closure

*Problem:* An Earth observation mission generates 500 MB/day of imagery. Is a single ground station at 52 N latitude sufficient with 2 Mbps S-band downlink?

*Calculation:*
- Passes per day: ~4 (500 km SSO from 52 N)
- Avg pass duration: 6 min = 360 s
- Data per pass: 2e6 bps x 360 s x 0.9 / 8 = 81 MB
- Daily capacity: 4 x 81 = 324 MB
- Required: 500 MB/day
- **Shortfall: 176 MB/day -- budget does not close!**

*Solutions:*
1. Add a second ground station at high latitude (e.g., Kiruna -> +6 passes -> +486 MB)
2. Increase data rate to X-band (10 Mbps -> 405 MB/pass -> easily sufficient)
3. Reduce data generation (lower duty cycle or reduce image resolution)
4. Add onboard data compression (2:1 lossless -> 250 MB/day required)
5. Use SatNOGS network for additional UHF passes (housekeeping only)

---

## 3. CCSDS Protocol Stack (20 min)

### Teaching Notes

The Consultative Committee for Space Data Systems (CCSDS) defines the standard protocols for space communication, analogous to TCP/IP for ground networks.

*[Source: CCSDS 131.0-B-4 (TM Synchronization and Channel Coding); CCSDS 231.0-B-4 (TC Synchronization and Channel Coding); CCSDS 133.0-B-2 (Space Packet Protocol)]*
*[URL: https://public.ccsds.org/Pubs/131x0b4.pdf (freely available)]*

### Protocol Layers

| Layer | CCSDS Standard | Function | Ground Analogy |
|-------|---------------|----------|----------------|
| **Application** | CCSDS 133.0 (Space Packet) | Mission data and housekeeping packets | HTTP/application data |
| **Network** | CCSDS 732.0 (AOS) or 132.0 (TM) | Virtual channels, multiplexing | IP routing |
| **Data Link** | CCSDS 131.0 (TM coding) / 231.0 (TC coding) | FEC, frame sync, CRC | Ethernet |
| **Physical** | CCSDS 401.0 (RF & Modulation) | Modulation, frequency, power | Physical layer |

### Telemetry (TM) Frame Structure

```
+--------+------------------+----+
| Header | Data Field       | EC |
| 6 bytes| 1-1019 bytes     | 2B |
+--------+------------------+----+
  |
  +-- Spacecraft ID (10 bits)
  +-- Virtual Channel ID (3 bits)
  +-- Frame Counter (8 bits)
  +-- Frame Length
```

### Forward Error Correction (FEC) Options

| Code | Rate | Coding Gain (dB) | Use Case |
|------|------|------------------|----------|
| Convolutional (7, 1/2) | 1/2 | 5.5 | Legacy CubeSats |
| Reed-Solomon (255, 223) | 0.87 | 3.5 | Combined with convolutional |
| Turbo (rate 1/2) | 1/2 | 7.5 | High-performance CubeSats |
| LDPC (rate 7/8) | 7/8 | 6.0 | High data rate, bandwidth efficient |

*Modern CubeSats typically use LDPC coding for downlink (high data rate) and convolutional + RS for uplink (robustness priority).*

---

## 4. Operations Timeline Construction (25 min)

### Teaching Notes

The operations timeline (or operations concept timeline) defines all major activities from launch to end of life. It is part of the ConOps and drives ground segment design.

### Mission Phases (Operations Perspective)

| Phase | Duration | Key Activities | Staffing |
|-------|----------|---------------|---------|
| **LEOP** | 0-72 hours | Separation, beacon acquisition, SA/antenna deploy, initial health check | 24/7 (3 shifts) |
| **Commissioning** | 1-4 weeks | Subsystem checkout, ADCS calibration, payload first light | 16/7 (2 shifts) |
| **Early Operations** | 1-3 months | Performance characterisation, procedure refinement | 8/5 (1 shift) |
| **Nominal Operations** | Mission lifetime | Routine science/service, orbit maintenance | 8/5 or automated |
| **Extended Operations** | If approved | Degraded mode operations, reduced data | Part-time |
| **End of Life** | 1-4 weeks | Passivation, deorbit manoeuvre, final telemetry | 8/5 |

### Operations Timeline (Gantt-Style)

```
Week:  1    2    3    4    5    6    7    8   ...  52
       |LEOP|
       |    |Commissioning         |
       |    |    |    |    |Early Operations    |
       |    |    |    |    |    |    |    |Nominal Operations ------>
       |    |    |    |    |    |    |    |    |    |    |    |    |
24/7:  XXXX
16/7:       XXXXXXXXXXXXXXX
8/5:                        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...
```

### LEOP Timeline Detail

| Time (after separation) | Activity | Success Criterion |
|------------------------|----------|-------------------|
| T+0 s | Separation from deployer | Deployment switches released |
| T+0 to T+30 min | Deployment timer countdown (no RF) | Timer runs; all inhibits clear |
| T+30 min | Antenna deployment | Beacon detected by ground station |
| T+30 to T+60 min | Beacon acquisition | Carrier lock; beacon decoded |
| T+1 hr | First telemetry downlink | Housekeeping data received and validated |
| T+1 to T+6 hr | Initial health assessment | All subsystems reporting nominal HK |
| T+6 to T+12 hr | Solar array deployment (if separate) | Power generation confirmed |
| T+12 to T+24 hr | ADCS initialisation | Attitude determination active |
| T+24 to T+48 hr | ADCS calibration (magnetometer, sun sensor) | Pointing within coarse spec |
| T+48 to T+72 hr | Communication chain validation (full duplex) | Uplink and downlink at operational rate |

### SpaceCDF Operations Planning

SpaceCDF's **ConOps Editor** allows you to:
- Define mission phases with start/end conditions
- Specify operational modes per phase (safe, nominal, science, downlink)
- Set ground contact requirements per phase (frequency, duration)
- The system validates that the ground segment design supports the operations concept

---

## 5. Ground Segment Design Exercise (25 min)

### Instructions

1. **Data Budget** tab -- Review the daily data generation vs downlink capacity
   - Is the data budget closing? If not, identify the bottleneck
   - How many ground station passes per day does your orbit provide?

2. **ConOps Editor** -- Define mission phases:
   - LEOP (duration, staffing, contact requirements)
   - Commissioning (activities, success criteria)
   - Nominal operations (duty cycle, data volume, contact frequency)

3. On Worksheet 5.1:
   - Calculate data volume per pass for your mission
   - Determine number of ground stations needed to close the data budget
   - Construct a LEOP timeline
   - Draft a simplified operations timeline (Gantt chart)

### Discussion Prompts

- "What happens if your first pass after deployment has no signal?"
- "How would you handle a safe mode entry at 3 AM on a Saturday?"
- "What is the minimum ground segment that could support your mission?"

### Worksheet 5.1 Tasks

1. Calculate ground station contact time and data volume per pass
2. Design a ground station network (locations, antenna sizes, data rates)
3. Construct a LEOP timeline (first 72 hours, hourly resolution)
4. Draft a mission operations timeline (Gantt chart, weekly resolution)
5. Estimate ground segment cost (antennas + MCS + FDS + operations staff)

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-70C (Ground Systems and Operations) | https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/ |
| 2 | CCSDS 131.0-B-4 (TM Synchronization and Channel Coding) | https://public.ccsds.org/Pubs/131x0b4.pdf |
| 3 | CCSDS 133.0-B-2 (Space Packet Protocol) | https://public.ccsds.org/Pubs/133x0b2.pdf |
| 4 | CCSDS 231.0-B-4 (TC Synchronization and Channel Coding) | https://public.ccsds.org/Pubs/231x0b4.pdf |
| 5 | SatNOGS Network | https://network.satnogs.org/ |
| 6 | NASA DSN Handbook (810-005) | https://deepspace.jpl.nasa.gov/dsndocs/810-005/ |
| 7 | YAMCS Mission Control Software | https://yamcs.org/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Ground segment | Antenna network + MCS + FDS + mission planning + data processing |
| Contact analysis | Pass duration ~6 min (LEO/SSO); data volume = rate x time x efficiency |
| Data budget | Must close: daily generation <= daily downlink capacity; add GS or increase rate |
| CCSDS | Standard protocol stack: Space Packet, AOS/TM frames, FEC coding, RF modulation |
| Operations timeline | LEOP (24/7) -> Commissioning (16/7) -> Nominal (8/5 or automated) |
| LEOP | First 72 hours critical: antenna deploy, beacon acquisition, health check |
| SpaceCDF | ConOps Editor defines phases; Data Budget validates ground segment sizing |
