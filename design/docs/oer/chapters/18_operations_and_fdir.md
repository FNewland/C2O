# Chapter 18 — Mission Operations and FDIR

> **Recommended background.** ECSS-E-ST-70-11C (Space segment operability); ECSS-E-ST-70-32C (Test and operations procedure language); ECSS-E-ST-70-41C (Packet utilisation standard); NASA Fault Management Handbook (NASA-HDBK-1002). This chapter builds on the *concept* of a ConOps — mission phases, segments and the idea of operational modes — introduced in Chapter 4 §4.8, on the ground-segment architecture and operations timeline of Chapter 17, on the per-mode power budget of Chapter 8 Table 8.4 and Chapter 9, and on the FMECA and single-point-failure analysis of Chapter 15. It supplies the operational detail: the full mode table, the mode-transition logic, the FDIR architecture, procedures and anomaly response.

## Learning objectives

By the end of this chapter, you will be able to:

1. Structure a Concept of Operations document and specify operational modes with entry and exit conditions
2. Draw the mode-transition state machine for a spacecraft and check that safe mode is reachable from every state
3. Design an FDIR (fault detection, isolation and recovery) architecture with a hierarchy of autonomous responses
4. Write operational procedures for routine and contingency operations in the ECSS-E-ST-70-32C structure
5. Describe the anomaly-response process with escalation levels and document an anomaly

Vendor products named in this chapter are representative examples, not endorsements.

---

## 18.1 The ConOps as an operations document

The ConOps is the bridge between engineering design and operational reality. It describes *how* the system will be used, not just *what* it can do. Chapter 4 introduced it as a mission-definition artefact — the phases of the mission, the three segments and the notion that a spacecraft has modes — because those decisions shape the architecture. By the time the design reaches PDR the same document has acquired a second audience: the people who will fly the spacecraft. This chapter is written for them.

*[Source: ECSS-E-ST-70-11C (Space Segment Operability); IEEE 1362 (Concept of Operations Document)]*

### 18.1.1 ConOps structure

A complete ConOps document covers:

1. **Mission overview** — objectives, stakeholders, success criteria (Chapter 4)
2. **System description** — space segment, ground segment, user segment (Chapter 8 §8.1, Chapter 17)
3. **Operational scenarios** — nominal operations, contingency operations
4. **Operational modes** — definition, transitions, constraints (§18.2)
5. **Resource management** — power, data and propellant budgets over time (Chapters 9, 11, 12)
6. **Communication plan** — contact schedule, data flow, latency requirements (Chapter 17 §17.2)
7. **Staffing plan** — personnel, shifts, training requirements (Chapter 17 §17.4)
8. **Maintenance and logistics** — software updates, ground-equipment maintenance

Items 3, 4 and 8 are the ones that only operations people write well, and they are the ones most often missing at PDR.

### 18.1.2 Autonomy: where the line falls

Every ConOps embodies a decision about how much the spacecraft does on its own. The decision is driven by contact time — a LEO CubeSat is out of view of a single station about 85 % of the time (Chapter 17 §17.2.3) — and by staffing cost. The two reference points are:

- **Ground-driven:** the spacecraft executes a time-tagged command schedule uploaded each day; any deviation is handled by entering safe mode and waiting. Simple flight software, expensive operations, slow recovery.
- **On-board autonomy:** the spacecraft plans its own imaging from an uploaded target list, manages its own power and data, and recovers from most faults without the ground. Complex flight software, cheap operations, fast recovery.

ESA's PROBA-2 (launched 2009 and still operating as of 2026) is the standard demonstration of where the second option leads for a small satellite: five operational modes (Standby, Science, Manoeuvre, Safe, Off), about 95 % of routine activities automated via an on-board timeline, four to six passes per day from a single station, and only two or three anomalies per year that need ground intervention after commissioning. The lesson is that investment in on-board autonomy pays back directly in operations cost. *[Source: ESA PROBA-2 Operations Team, "PROBA-2: Over a Decade of Operations", SpaceOps 2020]*

---

## 18.2 Operational modes

Every spacecraft has a defined set of operational modes. Each mode specifies which subsystems are active, the power consumption and the data rates — and, critically, the conditions under which the spacecraft enters and leaves it.

### 18.2.1 Mode table for the 3U EO CubeSat

Table 18.1 is the canonical mode table for the 3U Earth-observation running example, **EOSat-3U**. The four power figures for Safe, Nominal, Imaging and Downlink are the same ones used in Chapter 4 Table 4.1 (the illustrative three-row version), in Chapter 8 Table 8.4 (the per-subsystem breakdown) and in the Chapter 9 array and battery sizing; the eclipse load is Chapter 8's 3.5 W. Chapter 12 §12.5.3 notes that the *equipment-based* imaging-mode load is nearer 10 W than the 8 W parametric allocation — a budget tension that the operations concept has to respect by limiting imaging duty cycle until the power design is re-run.

**Table 18.1 — Operational modes of EOSat-3U (3U Earth-observation CubeSat, 500 km SSO)**

| Mode | Description | Power (W) | Data rate | Typical duration | Entry condition |
|------|------------|-----------|-----------|-----------------|----------------|
| **Safe** | Minimum functionality; survival only; sun-pointing by magnetic control; payload and wheels off | 2.0 | Beacon only | Until the ground intervenes | Autonomous fault detection (FDIR Level 3) or ground command |
| **Detumble** | Reduce angular rate after deployment with magnetorquers only | —, magnetorquers only | Housekeeping only (100 bit/s) | Minutes to hours | Post-separation; angular rate above threshold |
| **Nominal (standby)** | Sun-pointing; all subsystems powered and ready; wheel desaturation runs here | 4.0 | Housekeeping telemetry (1 kbit/s) | Between activities | After detumble; idle periods |
| **Imaging (science)** | Payload operating; fine pointing on wheels and star tracker | 8.0 | Science data to mass memory | Target-dependent (≈ 1 min per pass) | Scheduled; fine pointing achieved; battery state of charge above limit |
| **Downlink** | High-rate S-band transfer to ground | 10.0 | 1–5 Mbit/s (Chapter 11 §11.8.1) | During ground contact (≈ 6 min) | Station in view; link established |
| **Eclipse** | Reduced operations in shadow; heaters as required | 3.5 | Housekeeping only | ≈ 36 min per orbit (Chapter 7 §7.7) | Sun not in view |

EOSat-3U has no propulsion, so there is no manoeuvre mode; momentum desaturation with the magnetorquers (Chapter 10 §10.5) is a sub-state of Nominal. A mission with propulsion adds a **Manoeuvre** mode (housekeeping only, strict attitude constraints, typically 15–25 W for a larger bus) with its own entry conditions.

Two checks apply to every mode table:

- **Safe mode must be power-positive in the worst case.** With the 2.0 W safe-mode load the EOSat-3U array of Chapter 9 §9.2 charges the battery even in a tumbling attitude; Chapter 9 §9.4.11 uses the same 2.0 W as the cold-case internal dissipation.
- **Eclipse must be survivable from any mode.** The battery sizing of Chapter 9 §9.3 uses the 3.5 W eclipse load; if the spacecraft is still in Downlink when it enters shadow, the 10 W load must be shed within the battery's margin.

### 18.2.2 Mode-transition state machine

The mode table says what each mode is; the state machine of Figure 18.1 says how the spacecraft moves between them. Three properties are required of it: every state must have a path to Safe; Safe must have a path back to Nominal that *requires a ground command*; and no transition may depend on a resource (power, attitude knowledge) that the destination mode does not itself maintain.

![EOSat-3U mode-transition state machine](../assets/figures/fig_mode_state_machine.png)

**Figure 18.1** — Mode-transition state machine of EOSat-3U. Detumble is entered at separation and hands over to Nominal once the angular rate is below threshold; Imaging and Downlink are excursions from Nominal entered on schedule or on station contact and returning on completion; Eclipse is entered from Nominal, Imaging or Downlink when the Sun leaves the field of view and returns to Nominal when it reappears. A fault in any state leads to Safe mode, which is left only by ground command (or, if the rate limit is exceeded, by re-entering Detumble).

Reading Figure 18.1: Detumble is entered once at separation and again from Safe if the rate limit is exceeded; Nominal is the hub; Imaging and Downlink are excursions from Nominal that return on completion or on loss of their entry condition; Safe is reachable from every state by a fault and is left only by ground command. A fault during Downlink does not return to Nominal and then fall to Safe — it goes straight to Safe, because the intermediate transition could be the thing that is broken.

---

## 18.3 FDIR architecture

FDIR — fault detection, isolation and recovery — is the spacecraft's autonomous ability to detect failures, determine which component failed and take corrective action, all without ground intervention.

*[Source: NASA Fault Management Handbook (NASA-HDBK-1002); ECSS-E-ST-70-11C §5.3]*
*[URL: https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002]*

### 18.3.1 Why FDIR is critical for CubeSats

- **Limited ground contact:** LEO CubeSats are out of view ≈ 85 % of the time
- **No crewed intervention:** unlike the ISS, there is nobody on board to fix anything
- **Thermal constraints:** a safe mode must hold thermal limits within minutes (Chapter 9 §9.4.11: the EOSat-3U cold case drops 7.8 °C in one 36-minute eclipse)
- **Power constraints:** the battery can discharge completely in one eclipse without load shedding

### 18.3.2 FDIR hierarchy

FDIR is layered (Figure 18.2). Each level detects a class of fault, responds within a characteristic latency, and — if its response does not clear the fault — hands the problem up to the next level. The ground is the top level, which is why every autonomous action must be visible in telemetry and reversible by command.

| Level | Detection | Response | Latency | Example |
|-------|-----------|----------|---------|---------|
| **0 — Hardware** | Built-in watchdog | Component reset | Milliseconds | Processor watchdog timer |
| **1 — Unit** | Unit-level monitoring | Unit reconfiguration | Seconds | EPS over-current trip |
| **2 — Subsystem** | Subsystem health check | Subsystem fallback mode | Seconds to minutes | Switch to backup star tracker |
| **3 — System** | System-level anomaly detection | Mode change (enter Safe) | Minutes | Transition to safe mode |
| **4 — Ground** | Human-in-the-loop diagnosis | Ground-command recovery | Hours to days | Anomaly investigation and patch |

![FDIR hierarchy from hardware watchdog to ground](../assets/figures/fig_fdir_hierarchy.png)

**Figure 18.2** — The FDIR hierarchy as a layered pyramid. Each layer, from the Level 0 hardware watchdog at the base to the Level 4 ground at the apex, has its own detection means, response and characteristic latency; a fault that a layer cannot clear escalates upward, and the ground can override any autonomous action because every one is visible in telemetry and reversible by command.

### 18.3.3 FDIR decision flow

```
                    NOMINAL OPERATIONS
                           |
              Fault detected (Level 2–3)
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

The branch that matters is "cannot isolate". A spacecraft that cannot tell *which* unit has failed must not guess; it goes to Safe and lets the ground diagnose with the full telemetry history. The Hitomi loss of Chapter 15 §15.4.7 is the canonical example of an autonomous system acting on a wrong isolation.

### 18.3.4 Common CubeSat FDIR rules

| Fault | Detection method | Threshold | Response |
|-------|-----------------|-----------|----------|
| Processor lock-up | Watchdog timer | No heartbeat for 60 s | Hardware reset (Level 0) |
| Battery under-voltage | EPS voltage monitor | $V_{\text{bat}} <$ 6.0 V | Load shedding; enter Safe |
| Battery over-temperature | Temperature sensor | $T_{\text{bat}} >$ 45 °C | Disable charging; reduce loads |
| Attitude loss | No attitude solution for 5 min | AOCS health-flag timeout | Enter Detumble |
| Communication loss | No uplink for 48 h | Timer-based | Reset TT&C; revert to beacon mode |
| Memory corruption | EDAC error count | > 10 uncorrectable errors/h | Memory scrub; reboot from backup image |
| Solar-array current anomaly | Current sensor | $I_{\text{SA}} <$ expected − 30 % | Check attitude; enter Nominal (standby) |
| Reaction-wheel over-speed | Wheel-speed monitor | $\omega >$ 6 000 rpm | Reduce momentum; desaturate (Chapter 10 §10.5) |

Each rule should trace to a row of the FMECA (Chapter 15 §15.4): the FMECA says what can fail and how it would be detected; the FDIR rule says what the spacecraft does about it. The UniSat-1 register's R-03 (custom OBC in the radiation environment) is mitigated by exactly the first and sixth rows of this table.

### 18.3.5 Key design principles

1. **Safe mode must always work.** It is the last resort; it must be tested exhaustively, including from every other mode and in eclipse.
2. **Fail operational, then fail safe.** Try to continue the mission before giving up.
3. **No single fault should cause mission loss.** Cross-reference with the single-point-failure list of Chapter 15 §15.4.4.
4. **Ground override.** Every autonomous action must be commandable — and *inhibitable* — from the ground.
5. **Logging.** Record every fault event in non-volatile memory for post-analysis; an FDIR action that leaves no trace cannot be diagnosed.

---

## 18.4 Operational procedures

*[Source: ECSS-E-ST-70-32C (Test and Operations Procedure Language); ECSS-E-ST-70-01C (On-board control procedures)]*

### 18.4.1 Procedure types

| Type | Purpose | Execution | Example |
|------|---------|-----------|---------|
| **Nominal** | Routine scheduled operations | Automated (timeline) or manual | Science observation sequence |
| **Contingency** | Response to known anomaly types | Semi-automated; operator decision | Safe-mode recovery |
| **Emergency** | Response to critical unexpected events | Manual; real-time decision | Communication-loss recovery |
| **Maintenance** | Periodic calibration or updates | Scheduled manual | Magnetometer calibration |

### 18.4.2 Procedure structure (ECSS-E-ST-70-32C)

Each procedure has:

1. **Identifier** — unique procedure number (e.g. NOM-SCI-001)
2. **Purpose** — what the procedure accomplishes
3. **Preconditions** — system state required before starting
4. **Steps** — ordered list of actions, verifications and decisions
5. **Expected results** — what should happen at each step
6. **Recovery actions** — what to do if the expected results are not observed
7. **Post-conditions** — system state after successful completion

The discipline is in items 5 and 6: every step states what *should* be seen and what to do if it is not. A procedure without expected results is a wish list.

### 18.4.3 Example: science observation procedure for EOSat-3U

```
Procedure: NOM-SCI-001 "Earth-observation target acquisition"
Preconditions: Mode = Nominal, battery SoC > 60 %, target in field of view within 10 min

Step 1: Verify AOCS mode = Fine pointing
  Expected: AOCS status = FINE, pointing error < 0.1°
  If not: wait 60 s, retry. If still not achieved → ABORT, remain in Nominal

Step 2: Command payload power ON
  Expected: payload housekeeping reports power = ON within 5 s
  If not: retry power command. If 3 failures → ABORT, log anomaly

Step 3: Wait for payload thermal stabilisation (90 s)
  Expected: payload temperature within operational range

Step 4: Command payload to imaging mode
  Expected: payload status = IMAGING, frame counter incrementing

Step 5: Wait for target acquisition (ground-predicted start time)
  Expected: imaging starts at predicted time ± 5 s

Step 6: Collect imagery for the scheduled duration

Step 7: Command payload to standby
  Expected: payload status = STANDBY

Step 8: Command payload power OFF (if no more targets this orbit)
  Expected: payload housekeeping reports power = OFF

Post-conditions: Mode = Nominal, imagery stored in mass memory
```

A contingency procedure — safe-mode recovery, say — has the same shape but its preconditions are the *diagnosis*: "FDIR log read out and cause identified; cause cleared or inhibited; battery SoC > 80 %". Recovery without a diagnosis is the most common way to enter safe mode twice.

---

## 18.5 Anomaly response process

*[Source: NASA-HDBK-1002 (Fault Management Handbook); ESA anomaly review board procedures]*

### 18.5.1 Anomaly escalation levels

| Level | Severity | Response time | Authority | Example |
|-------|----------|--------------|-----------|---------|
| **Green** | Informational | Next working day | Operations engineer | Minor parameter outside expected range |
| **Yellow** | Warning | Within 4 hours | Lead operator | Subsystem performance degraded |
| **Orange** | Serious | Within 1 hour | Flight director | Mode change required; mission impact |
| **Red** | Critical | Immediate | Project manager + flight director | Mission-threatening; safe mode entered |

### 18.5.2 Anomaly response workflow

```
1. DETECT:   Telemetry alarm or operator observation
2. ASSESS:   Is this a known anomaly type? Check the procedures library
             → Known:   execute the contingency procedure
             → Unknown: continue to step 3
3. DIAGNOSE: Gather additional telemetry, correlate events, form a hypothesis
4. PLAN:     Develop the response plan (may require an anomaly review board)
5. EXECUTE:  Implement recovery commands (verify each step)
6. VERIFY:   Confirm the system has returned to the expected state
7. DOCUMENT: Record anomaly, root cause, response and lessons learned
```

Two rules of thumb from agency practice: *rule out the ground first* (a silent spacecraft is more often a mis-pointed antenna or a wrong frequency than a dead transmitter), and *do not send a command you cannot verify* (every uplink in step 5 is followed by a telemetry check before the next).

### 18.5.3 Anomaly report fields

| Field | Description |
|-------|------------|
| **Anomaly ID** | Unique identifier (e.g. ANO-2026-042) |
| **Date/time (UTC)** | When the anomaly was detected |
| **Severity** | Green / Yellow / Orange / Red |
| **Affected subsystem** | EPS, AOCS, TT&C, payload, … |
| **Observation** | What was observed (telemetry values, trends) |
| **Diagnosis** | Root-cause analysis |
| **Action taken** | Commands sent, procedures executed |
| **Result** | System state after the response |
| **Status** | Open / resolved / under investigation |
| **Lessons learned** | Preventive measures for the future |

### 18.5.4 Real mission example: Kepler reaction-wheel failure

NASA's Kepler space telescope lost reaction wheel 2 in July 2012, followed by wheel 4 in May 2013. The anomaly response:

1. **Detection:** elevated friction torque in the wheel-2 housekeeping telemetry
2. **Assessment:** known degradation signature; monitoring intensified
3. **Failure:** wheel 2 ceased operation; the mission continued on three wheels
4. **Second failure:** wheel 4 failed ten months later; two wheels remaining — insufficient for fine pointing
5. **Recovery:** the engineering team developed the "K2" mission concept using solar radiation pressure as a "virtual third wheel"
6. **Result:** K2 operated for more than four additional years, discovering 2 700+ exoplanet candidates

*Lesson: creative operational workarounds can save missions. FDIR should be designed with graceful degradation, not just "safe mode or nothing" — which is the operational counterpart of the 3-of-4 wheel reliability argument in Chapter 15 §15.4.6.*

*[Source: Howell et al., "The K2 Mission: Characterization and Early Results", PASP, 2014]*

---

## 18.6 Returning to UniSat-1: modes and FDIR for a 1U demonstrator

UniSat-1 has passive magnetic attitude control, no wheels, no star tracker, a UHF beacon and a single payload — so most of Table 18.1 does not apply. Its mode set is three states:

| Mode | Description | Power | Entry condition |
|------|------------|-------|----------------|
| **Safe (beacon)** | OBC and beacon only; payload off | Minimum, power-positive in any attitude (Chapter 9 §9.5) | Any FDIR trigger; also the state after every reset |
| **Nominal** | Payload sampling at the science rate; housekeeping stored | Nominal load of Chapter 9 §9.5 | Ground command, after beacon health confirmed |
| **Downlink** | UHF transmitter at full rate during a pass | Transmit load | Station in view; scheduled by uplinked pass list |

There is no Detumble (the permanent magnet and hysteresis rods do that passively over days) and no Imaging (the magnetometer runs continuously in Nominal). The FDIR rules reduce to four: the watchdog reset, the battery under-voltage trip to Safe, the 48-hour no-uplink timer, and the EDAC scrub on the custom OBC — the last two being the mitigations recorded against risk R-03 in Chapter 15 §15.5. The safe-mode recovery procedure is one page long, and because Safe is power-positive and thermally benign, the spacecraft can sit in it for weeks: UniSat-1 can afford a student operations team precisely because its FDIR has nothing to do in a hurry.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| ConOps | Defines *how* the system is operated: modes, transitions, schedules, staffing; the concept is in Chapter 4, the operational detail here |
| Operational modes | EOSat-3U (Table 18.1): Safe 2 W, Nominal 4 W, Imaging 8 W, Downlink 10 W, Eclipse 3.5 W; Safe must be power-positive, Eclipse survivable from any mode |
| Mode transitions | Defined by entry/exit conditions; Safe reachable from every mode and left only by ground command |
| FDIR | Five levels: hardware → unit → subsystem → system → ground; Safe is the last resort; "cannot isolate" goes to Safe, never guesses |
| Procedures | Nominal, contingency, emergency, maintenance; every step has an expected result and a recovery action |
| Anomaly response | Detect → assess → diagnose → plan → execute → verify → document; rule out the ground first |
| Design principles | Safe mode must always work; fail operational before fail safe; ground override always; log everything |

---

## Problems

1. **Mode table.** Construct the operational-mode table for a 6U CubeSat with a cold-gas propulsion system and an X-band downlink: at least six modes with power, data rate, typical duration and entry condition. Identify which mode has the highest power and check, using the battery-sizing method of Chapter 9 §9.3, whether the spacecraft could survive entering eclipse in that mode.

2. **State machine.** Draw the mode-transition state machine for the spacecraft of Problem 1. Verify the three properties of §18.2.2 — Safe reachable from every state, Safe exited only by ground command, no transition dependent on a resource the destination does not maintain — and identify one transition in Figure 18.1 (§18.2.2) that would violate the third property if Eclipse were implemented as a full mode with its own attitude control.

3. **Safe-mode power closure.** EOSat-3U enters Safe in a tumbling attitude. Using the solar-array area of Chapter 9 §9.2 and assuming the orbit-average projected area of a tumbling 3U is 40 % of its maximum, compute the orbit-average generated power at end of life and compare it with the 2.0 W safe-mode load plus the 3.5 W eclipse load for 36 minutes per orbit. Is Safe power-positive? If not, which safe-mode load would you remove first?

4. **FDIR rule set.** Write five FDIR rules for the UniSat-1 mission (fault, detection method, threshold, response) in the format of §18.3.4, assigning each to a level of the hierarchy of §18.3.2. For each rule, cite the FMECA row or risk-register entry of Chapter 15 it responds to, and state how the ground can inhibit it.

5. **Isolation versus safe mode.** A 3U spacecraft carries two redundant magnetometers whose readings disagree by 30 %. Design the Level-2 isolation logic that decides which one to trust, state what third source of information it needs, and specify the condition under which it must give up and go to Safe instead. Relate your answer to the Hitomi sequence of Chapter 15 §15.4.7.

6. **Contingency procedure.** Write a safe-mode recovery procedure for EOSat-3U in the seven-part structure of §18.4.2, with at least eight steps, each with an expected result and a recovery action. The preconditions must include a diagnosis step; the post-conditions must leave the spacecraft in Nominal with the fault inhibited or cleared.

7. **Anomaly report.** The EOSat-3U OBC reboot counter increments three times in ten minutes while the spacecraft is over the South Atlantic, after which FDIR enters Safe. Complete the anomaly report of §18.5.3 for this event, assign a severity level from §18.5.1 with justification, and propose the two telemetry channels that would most quickly discriminate a single-event upset from a software fault.

8. **Autonomy trade.** Estimate the operations cost over three years for the 3U mission under the ground-driven and on-board-autonomy options of §18.1.2 (use 60 kEUR per FTE-year and the staffing profiles of Chapter 17 §17.4.1), and estimate the additional flight-software cost of the autonomous option using the software line of Chapter 16 §16.2.1. At what mission duration does autonomy pay for itself?

9. **Weekend safe mode.** The spacecraft enters Safe on a Friday evening; the next staffed contact is Monday morning (≈ 60 hours, ≈ 38 orbits). Using Table 18.1 and the battery of Chapter 9 §9.3, decide whether EOSat-3U survives without intervention, then repeat for the case where Safe fails to shed the payload heater (an extra 1.5 W). State what the FDIR must guarantee for a mission with no weekend staffing to be acceptable.

---

## References

1. ECSS, *ECSS-E-ST-70-11C: Space Segment Operability*, 2008. https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/
2. ECSS, *ECSS-E-ST-70-32C: Test and Operations Procedure Language*, 2008. https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/
3. ECSS, *ECSS-E-ST-70-01C: Spacecraft On-board Control Procedures*, 2010. https://ecss.nl/standard/ecss-e-st-70-01c-spacecraft-on-board-control-procedures/
4. ECSS, *ECSS-E-ST-70-41C: Telemetry and Telecommand Packet Utilization*, 2016. https://ecss.nl/standard/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/
5. NASA, *Fault Management Handbook*, NASA-HDBK-1002, 2012. https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002
6. IEEE, *IEEE Std 1362-1998: Guide for Information Technology — System Definition — Concept of Operations (ConOps) Document*, 1998.
7. ESA PROBA-2 Operations Team, "PROBA-2: Over a Decade of Operations", *SpaceOps 2020*. https://www.spaceops.org/
8. Howell, S. B. et al., "The K2 Mission: Characterization and Early Results", *Publications of the Astronomical Society of the Pacific*, 126(938), 2014. https://doi.org/10.1086/676406
