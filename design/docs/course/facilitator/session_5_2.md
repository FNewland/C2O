# Session 5.2: Mission Operations Concepts

**Duration:** 2 hours
**Prerequisites:** Session 5.1 (ground segment architecture understood)
**References:** ECSS-E-ST-70-11C (Space Segment Operability), ECSS-E-ST-70-32C (Procedures), ECSS-E-ST-70-41C (Packet Utilisation Standard), NPR 7120.5F, NASA Fault Management Handbook (NASA-HDBK-1002)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Define a Concept of Operations (ConOps) with operational modes and transitions
2. Design an FDIR (Fault Detection, Isolation, Recovery) architecture
3. Write operational procedures for routine and contingency operations
4. Describe anomaly response process with escalation levels
5. Plan spacecraft operational modes and their entry/exit criteria

---

## 1. Concept of Operations (ConOps) (25 min)

### Teaching Notes

The ConOps is the bridge between engineering design and operational reality. It describes HOW the system will be used, not just WHAT it can do.

*[Source: ECSS-E-ST-70-11C (Space Segment Operability); IEEE 1362 (Concept of Operations Document)]*

### ConOps Structure

A complete ConOps document covers:

1. **Mission overview** -- Objectives, stakeholders, success criteria
2. **System description** -- Space segment, ground segment, user segment
3. **Operational scenarios** -- Nominal operations, contingency operations
4. **Operational modes** -- Definition, transitions, constraints
5. **Resource management** -- Power, data, propellant budgets over time
6. **Communication plan** -- Contact schedule, data flow, latency requirements
7. **Staffing plan** -- Personnel, shifts, training requirements
8. **Maintenance and logistics** -- Software updates, ground equipment maintenance

### Operational Modes

Every spacecraft has a defined set of operational modes. Each mode specifies which subsystems are active, power consumption, and data rates.

| Mode | Description | Power (W) | Data Rate | Typical Duration | Entry Condition |
|------|------------|-----------|-----------|-----------------|----------------|
| **Safe** | Minimum functionality; survival only | 5-10 | Beacon only (1 bps) | Until ground intervenes | Autonomous fault detection |
| **Detumble** | Stop rotation after deployment | 8-12 | HK only (100 bps) | Minutes to hours | Post-separation; high angular rate |
| **Standby** | Sun-pointing; all subsystems ready | 12-18 | HK telemetry (1 kbps) | Between activities | After detumble; idle periods |
| **Science** | Payload operating; attitude controlled | 25-40 | Science data (variable) | Target-dependent | Scheduled; attitude achieved |
| **Downlink** | High-rate data transfer to ground | 20-30 | Full rate (2-10 Mbps) | During GS contact | GS in view; link established |
| **Manoeuvre** | Orbit adjustment or desaturation | 15-25 | HK only | Minutes | Scheduled; constraints met |
| **Eclipse** | Reduced operations during eclipse | 8-15 | HK only (100 bps) | ~35 min (LEO) | Sun not in view |

### Mode Transition State Machine

```
                    +----------+
      Separation    |          |    Fault
   +--------------->| DETUMBLE |<-----------+
   |                |          |            |
   |                +----+-----+            |
   |                     | Angular rate     |
   |                     | < threshold      |
   |                +----v-----+            |
   |                |          |    Fault   |
   |     +--------->| STANDBY  |----------->+--------+
   |     |          |          |<-----+     |        |
   |     |          +--+----+--+      |     |  +-----v----+
   |     |             |    |         |     |  |          |
   |     |    Schedule |    | GS      |     +--+  SAFE    |
   |     |             |    | contact |        |  MODE    |
   |     |       +-----v-+  +---v----++        |          |
   |     |       |       |  |        |         +-----+----+
   |     +-------+SCIENCE|  |DOWNLINK|               |
   |    Complete |       |  |        |      Ground    |
   |             +-------+  +--------+      command   |
   |                                        recovery  |
   +--------------------------------------------------+
```

### Real Mission Example: PROBA-2 Operations

ESA's PROBA-2 (launched 2009, still operational in 2026) demonstrates mature CubeSat-class operations:
- **5 operational modes:** Standby, Science, Manoeuvre, Safe, Off
- **Autonomous operations:** 95% of routine activities automated via onboard timeline
- **Ground contacts:** 4-6 passes/day via ESA Redu station (S-band)
- **Anomaly rate:** ~2-3 per year requiring ground intervention (after initial commissioning)
- **Key lesson:** Investing in onboard autonomy dramatically reduces operations cost

*[Source: ESA PROBA-2 Operations Team, "PROBA-2: Over a Decade of Operations", SpaceOps 2020]*

---

## 2. FDIR Architecture (30 min)

### Teaching Notes

FDIR (Fault Detection, Isolation, Recovery) is the spacecraft's autonomous ability to detect failures, determine which component failed, and take corrective action -- all without ground intervention.

*[Source: NASA Fault Management Handbook (NASA-HDBK-1002); ECSS-E-ST-70-11C section 5.3]*
*[URL: https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002]*

### Why FDIR is Critical for CubeSats

- **Limited ground contact:** LEO CubeSats are out of view ~85% of the time
- **No crewed intervention:** Unlike ISS, there is no astronaut to "fix" problems
- **Thermal constraints:** A safe mode must maintain thermal limits within minutes
- **Power constraints:** Battery can discharge completely in one eclipse without load shedding

### FDIR Hierarchy (Levels)

| Level | Detection | Response | Latency | Example |
|-------|-----------|----------|---------|---------|
| **0 -- Hardware** | Built-in watchdog | Component reset | Milliseconds | Processor watchdog timer |
| **1 -- Unit** | Unit-level monitoring | Unit reconfiguration | Seconds | EPS over-current trip |
| **2 -- Subsystem** | Subsystem health check | Subsystem fallback mode | Seconds-minutes | Switch to backup star tracker |
| **3 -- System** | System-level anomaly detection | Mode change (e.g., enter Safe) | Minutes | Transition to Safe Mode |
| **4 -- Ground** | Human-in-the-loop diagnosis | Ground command recovery | Hours-days | Anomaly investigation + patch |

### FDIR State Machine

```
                    NOMINAL OPERATIONS
                           |
              Fault detected (Level 2-3)
                           |
                    +------v------+
                    |  FAULT      |
                    |  DETECTED   |
                    +------+------+
                           |
              +------------+------------+
              |                         |
        Fault isolated            Cannot isolate
              |                         |
        +-----v-----+           +-------v------+
        | ISOLATION  |           | SAFE MODE    |
        | SUCCESS    |           | (Level 3)    |
        +-----+------+           +-------+------+
              |                          |
        Recovery action            Wait for ground
              |                    (Level 4)
        +-----v-----+                   |
        | RECOVERY   |           +------v-------+
        | ATTEMPT    |           | GROUND       |
        +-----+------+           | RECOVERY     |
              |                  +------+-------+
         Success / Fail                 |
              |                    Command sequence
        +-----v-----+                   |
        | RETURN TO  |<----------------+
        | NOMINAL    |
        +------------+
```

### Common CubeSat FDIR Rules

| Fault | Detection Method | Threshold | Response |
|-------|-----------------|-----------|----------|
| Processor lockup | Watchdog timer | No heartbeat for 60 s | Hardware reset (Level 0) |
| Battery under-voltage | EPS voltage monitor | V_bat < 6.0V | Load shedding; enter Safe Mode |
| Battery over-temperature | Temperature sensor | T_bat > 45 C | Disable charging; reduce loads |
| Attitude loss | No attitude solution for 5 min | ADCS health flag timeout | Enter Detumble Mode |
| Communication loss | No uplink for 48 hr | Timer-based | Reset TTC; revert to beacon mode |
| Memory corruption | EDAC error count | > 10 uncorrectable errors/hr | Memory scrub; reboot from backup |
| Solar array current anomaly | Current sensor | I_SA < expected - 30% | Check attitude; enter Standby |
| Reaction wheel over-speed | Wheel speed monitor | Omega > 6000 RPM | Reduce momentum; desaturation |

### Key Design Principles

1. **Safe Mode must always work** -- It is the last resort; it must be tested exhaustively
2. **Fail operational, then fail safe** -- Try to continue the mission before giving up
3. **No single fault should cause mission loss** -- Cross-reference with FMECA
4. **Ground override capability** -- Every autonomous action must be commandable from ground
5. **Logging** -- Record all fault events in non-volatile memory for post-analysis

---

## 3. Operational Procedures (20 min)

### Teaching Notes

*[Source: ECSS-E-ST-70-32C (Procedure Definition Language); ECSS-E-ST-70-01C section 5.6]*

### Procedure Types

| Type | Purpose | Execution | Example |
|------|---------|-----------|---------|
| **Nominal** | Routine scheduled operations | Automated (timeline) or manual | Science observation sequence |
| **Contingency** | Response to known anomaly types | Semi-automated; operator decision | Safe mode recovery |
| **Emergency** | Response to critical unexpected events | Manual; real-time decision | Communication loss recovery |
| **Maintenance** | Periodic calibration or updates | Scheduled manual | Magnetometer calibration |

### Procedure Structure (ECSS-E-ST-70-32C)

Each procedure has:
1. **Identifier** -- Unique procedure number (e.g., NOM-001)
2. **Purpose** -- What the procedure accomplishes
3. **Preconditions** -- System state required before starting
4. **Steps** -- Ordered list of actions, verifications, decisions
5. **Expected results** -- What should happen at each step
6. **Recovery actions** -- What to do if expected results are not observed
7. **Post-conditions** -- System state after successful completion

### Example: Science Observation Procedure

```
Procedure: NOM-SCI-001 "Earth Observation Target Acquisition"
Preconditions: Mode = Standby, Battery SoC > 60%, Target in FOV within 10 min

Step 1: Verify ADCS mode = Fine Pointing
  Expected: ADCS status = FINE, pointing error < 0.1 deg
  If not: Wait 60 s, retry. If still not achieved -> ABORT, remain in Standby

Step 2: Command payload power ON
  Expected: Payload HK reports power = ON within 5 s
  If not: Retry power command. If 3 fails -> ABORT, log anomaly

Step 3: Wait for payload thermal stabilisation (90 s)
  Expected: Payload temperature within operational range

Step 4: Command payload to imaging mode
  Expected: Payload status = IMAGING, frame counter incrementing

Step 5: Wait for target acquisition (ground-predicted start time)
  Expected: Imaging starts at predicted time +/- 5 s

Step 6: Collect imagery for scheduled duration

Step 7: Command payload to standby
  Expected: Payload status = STANDBY

Step 8: Command payload power OFF (if no more targets this orbit)
  Expected: Payload HK reports power = OFF

Post-conditions: Mode = Standby, imagery stored in mass memory
```

---

## 4. Anomaly Response Process (20 min)

### Teaching Notes

*[Source: NASA-HDBK-1002 (Fault Management Handbook); ESA Anomaly Review Board procedures]*

### Anomaly Escalation Levels

| Level | Severity | Response Time | Authority | Example |
|-------|----------|--------------|-----------|---------|
| **Green** | Informational | Next business day | Operations engineer | Minor parameter out of expected range |
| **Yellow** | Warning | Within 4 hours | Lead operator | Subsystem performance degraded |
| **Orange** | Serious | Within 1 hour | Flight director | Mode change required; mission impact |
| **Red** | Critical | Immediate | Project manager + FD | Mission-threatening; safe mode entered |

### Anomaly Response Workflow

```
1. DETECT: Telemetry alarm or operator observation
2. ASSESS: Is this a known anomaly type? Check procedures library
   -> Known: Execute contingency procedure
   -> Unknown: Continue to step 3
3. DIAGNOSE: Gather additional telemetry, correlate events, form hypothesis
4. PLAN: Develop response plan (may require Anomaly Review Board)
5. EXECUTE: Implement recovery commands (verify each step)
6. VERIFY: Confirm system returned to expected state
7. DOCUMENT: Record anomaly, root cause, response, and lessons learned
```

### Anomaly Report Form Fields

| Field | Description |
|-------|------------|
| **Anomaly ID** | Unique identifier (e.g., ANO-2026-042) |
| **Date/Time (UTC)** | When the anomaly was detected |
| **Severity** | Green / Yellow / Orange / Red |
| **Affected subsystem** | EPS, AOCS, TTC, Payload, etc. |
| **Observation** | What was observed (TM values, trends) |
| **Diagnosis** | Root cause analysis |
| **Action taken** | Commands sent, procedures executed |
| **Result** | System state after response |
| **Status** | Open / Resolved / Under investigation |
| **Lessons learned** | Preventive measures for future |

### Real Mission Example: Kepler Reaction Wheel Failure

NASA's Kepler space telescope lost reaction wheel #2 in July 2012, followed by wheel #4 in May 2013. The anomaly response:

1. **Detection:** Elevated friction torque in wheel #2 HK telemetry
2. **Assessment:** Known degradation signature; monitoring intensified
3. **Failure:** Wheel #2 ceased operation. Mission continued on 3 wheels.
4. **Second failure:** Wheel #4 failed 10 months later. Only 2 wheels remaining -- insufficient for fine pointing.
5. **Recovery:** Engineering team developed the "K2" mission concept using solar radiation pressure as a "virtual third wheel"
6. **Result:** K2 operated for 4+ additional years, discovering 2,700+ exoplanet candidates

*Lesson: Creative operational workarounds can save missions. FDIR should be designed with graceful degradation, not just "safe mode or nothing."*

*[Source: Howell et al., "The K2 Mission: Characterization and Early Results", PASP, 2014]*

---

## 5. Operations Concepts Exercise (25 min)

### Instructions

1. **ConOps Editor** in SpaceCDF:
   - Define all operational modes for your mission (at least 5)
   - Set entry/exit conditions for each mode
   - Verify power budget closes in each mode (especially Safe and Eclipse)

2. **FDIR Design:**
   - Define 5 FDIR rules for your mission (fault, detection, threshold, response)
   - Verify that Safe Mode power budget is sustainable indefinitely
   - Check: Can every FDIR response be overridden from ground?

3. **Worksheet 5.2:**
   - Complete the operational modes table
   - Write one nominal procedure (science observation or downlink)
   - Write one contingency procedure (safe mode recovery)
   - Fill in the FDIR rules table

### Discussion Prompts

- "What is the worst anomaly that could happen to your satellite? How would you respond?"
- "If the satellite enters safe mode on Friday evening and the next ground contact is Monday, will it survive?"
- "How much autonomy should the spacecraft have? Where is the line between onboard and ground decision-making?"

### Worksheet 5.2 Tasks

1. Complete the operational modes table (5+ modes with power, data rate, entry/exit)
2. Design the FDIR state machine (at least 5 rules)
3. Write one nominal and one contingency procedure
4. Complete the anomaly response form for a hypothetical scenario
5. Estimate operations staffing requirements by mission phase

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-70-11C (Space Segment Operability) | https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/ |
| 2 | ECSS-E-ST-70-32C (Procedures) | https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/ |
| 3 | NASA Fault Management Handbook (NASA-HDBK-1002) | https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002 |
| 4 | ESA PROBA-2 Operations, SpaceOps 2020 | https://www.spaceops.org/ |
| 5 | Howell et al., K2 Mission, PASP 2014 | https://doi.org/10.1086/676406 |
| 6 | ECSS-E-ST-70-41C (Packet Utilisation Standard) | https://ecss.nl/standard/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| ConOps | Defines HOW the system is operated: modes, transitions, schedules, staffing |
| Operational modes | Safe, Detumble, Standby, Science, Downlink, Manoeuvre, Eclipse (minimum set) |
| Mode transitions | Defined by entry/exit conditions; Safe Mode always reachable from any mode |
| FDIR | 5 levels: Hardware -> Unit -> Subsystem -> System -> Ground; Safe Mode is last resort |
| Procedures | Nominal (routine), Contingency (known faults), Emergency (unknown), Maintenance |
| Anomaly response | Detect -> Assess -> Diagnose -> Plan -> Execute -> Verify -> Document |
| Design principles | Safe Mode must always work; fail operational before fail safe; ground override always |
