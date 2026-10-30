# Session 5.3: Mission Simulation Day


**Prerequisites:** Sessions 5.1-5.2 (ground segment designed, operations concepts defined)
**References:** ECSS-E-ST-70-11C (Operability), ECSS-E-ST-70-32C (Procedures), ESA OPS-G Training Manual, NASA Mission Operations Directorate Training Handbook

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Execute a simulated LEOP sequence from separation through first telemetry
2. Perform commissioning activities using operational procedures
3. Respond to injected anomalies using the FDIR architecture and contingency procedures
4. Document anomaly response in real-time using structured forms
5. Conduct nominal science operations with live data budget tracking

---

## 1. Simulation Overview & Roles
This session is a **hands-on simulation** of mission operations. The facilitator acts as the "Universe" -- injecting events, anomalies, and time jumps. The team operates the mission using SpaceCDF and their procedures from Session 5.2.

### Role Assignments

| Role | Responsibility | SpaceCDF Feature Used |
|------|---------------|---------------------|
| **Flight Director (FD)** | Overall decision authority; coordinates team | Dashboard, all tabs |
| **Spacecraft Controller (SC)** | Sends commands; monitors housekeeping telemetry | ConOps Editor, mode control |
| **Ground Station Operator (GSO)** | Manages antenna scheduling; link acquisition | Data Budget, Link Budget |
| **Payload Operator (PO)** | Plans and executes science observations | Payload parameters, data budget |
| **Flight Dynamics (FD-nav)** | Monitors orbit; plans manoeuvres (if propulsion) | Orbit parameters, sustainability |
| **Anomaly Logger** | Documents all events, anomalies, and decisions | Worksheet 5.3 |

*For smaller teams, combine roles: SC+GSO and PO+FD-nav are natural pairings.*

### Simulation Timeline

| Sim Time | Real Time | Phase | Events |
|----------|----------|-------|--------|
| T+0 to T+1 hr | 0-20 min | LEOP | Separation, beacon acquisition, deploy, health check |
| T+1 hr to T+24 hr | 20-35 min | Early LEOP | SA deploy, ADCS init, comms chain validation |
| T+1 day to T+7 days | 35-50 min | Commissioning | Subsystem checkout, first payload activation |
| T+7 days to T+30 days | 50-65 min | Early Operations | Nominal science, orbit maintenance |
| *Anomaly injection* | 65-85 min | Contingency | Anomaly response exercise |
| T+30 days to T+1 year | 85-100 min | Nominal Operations | Routine operations, data review |
| Debrief | 100-120 min | Wrap-up | Lessons learned, documentation review |

---

## 2. LEOP Simulation
The facilitator narrates the simulation. Time is compressed. Each team executes their LEOP procedure.

### Facilitator Script -- LEOP

**[T+0 -- Separation]**
*"Your satellite has separated from the deployer. Deployment switches have released. The 30-minute timer has started. You are in radio silence -- no RF emissions allowed until the timer expires. What is your spacecraft doing right now?"*

Worked response: Timer counting down. Battery providing power. No subsystems active except OBC running timer.

**[T+30 min -- Timer Expires]**
*"The 30-minute timer has expired. Your OBC has commanded antenna deployment. What do you expect to see?"*

Expected: Antenna deployment command sent. Beacon should begin transmitting.

**[T+35 min -- First Pass Over Ground Station]**
*"Your ground station at [location] has line of sight. The antenna operator reports: carrier detected at [frequency] with Doppler of -25 kHz. Signal strength is -110 dBm. Is this what you expected?"*

Teams should verify:
- Carrier frequency matches expected (accounting for Doppler)
- Signal strength is consistent with link budget at current range
- Beacon data rate is as designed

**[T+40 min -- First Telemetry]**
*"Beacon lock achieved. You are receiving housekeeping telemetry. I am going to read you the first HK frame:"*

| Parameter | Value | Expected Range | Status |
|-----------|-------|---------------|--------|
| Bus voltage | 7.8 V | 7.0 - 8.4 V | Nominal |
| Battery SoC | 72% | > 50% | Nominal |
| Solar array current | 0.45 A | 0.3 - 0.6 A | Nominal |
| OBC temperature | 22 C | -10 to +50 C | Nominal |
| Battery temperature | 19 C | 0 to 45 C | Nominal |
| ADCS mode | Detumble | Expected | Nominal |
| Angular rate | 3.2 deg/s | Decreasing | Nominal |
| Antenna status | Deployed | Expected | Nominal |
| Beacon mode | Active | Expected | Nominal |
| Uplink status | Not yet attempted | -- | -- |

*"All parameters nominal. Proceed with LEOP sequence."*

**[T+1 hr -- Uplink Validation]**
*"You now attempt your first uplink command. Send a 'NOP' (no operation) command to verify the uplink chain."*

Teams should: compose command, verify encoding, transmit, wait for acknowledgement in telemetry.

---

## 3. Commissioning Simulation
### Facilitator Script -- Commissioning

**[Time Jump: T+24 hr]**
*"Your satellite has completed detumbling. ADCS is in sun-pointing mode. All HK parameters are nominal after 8 ground passes. You are ready to begin commissioning. What is your first activity?"*

Expected: ADCS calibration (magnetometer bias estimation, sun sensor alignment verification).

**[T+3 days -- Payload First Light]**
*"ADCS is calibrated and achieving 0.3 degree pointing. You are ready for payload first light. Walk me through your procedure."*

Teams execute their science observation procedure from Worksheet 5.2.

**[T+5 days -- First Data Download]**
*"Payload has captured 150 MB of imagery. Your next pass is 12 minutes long over [station]. Can you download all the data in one pass?"*

Teams should calculate:
- Data rate x pass duration x protocol efficiency = available capacity
- Compare to 150 MB -- determine if multiple passes needed
- Plan the download sequence

---

## 4. Anomaly Injection Scenarios
The facilitator selects 2-3 anomalies from the list below, appropriate to the mission design. Teams respond using their FDIR rules and contingency procedures.

### Anomaly Menu (Facilitator selects 2-3)

#### Anomaly A: Battery Under-Voltage

*"During eclipse, you receive an alert: battery voltage has dropped to 6.2V, below your 6.5V warning threshold. Battery temperature is 5 C. SoC is estimated at 18%."*

Expected response:
1. Verify FDIR has triggered load shedding (payload off, non-essential heaters off)
2. Check power budget: is consumption > generation?
3. Possible causes: SA degradation, unexpected load, battery degradation, long eclipse
4. Immediate action: Verify safe mode; disable non-essential loads manually
5. Investigation: Review power trends over last 24 hours; compare to power budget

#### Anomaly B: Communication Loss

*"You have not received telemetry for the last 3 scheduled passes (18 hours). The ground station reports pointing and frequency are correct but no carrier detected."*

Expected response:
1. Verify ground station equipment (antenna, LNA, modem) -- rule out ground fault
2. Check with other ground stations (SatNOGS) for any signal detection
3. Consider causes: TX failure, antenna deployment failure, attitude loss (antenna not pointing)
4. If 48-hour timer exists: satellite may reset TTC and revert to beacon mode
5. Plan: Wait for timer-based reset; use wide-beam ground antenna for beacon search

#### Anomaly C: ADCS Anomaly -- Loss of Fine Pointing

*"Pointing error has increased from 0.1 deg to 5 deg. Star tracker reports 'no solution'. Reaction wheels are at 80% capacity (near saturation)."*

Expected response:
1. Diagnose: Star tracker failure? Optical contamination? Sun in FOV?
2. Check magnetometer attitude -- is coarse attitude correct?
3. Immediate: Command desaturation using magnetorquers
4. If star tracker failed: switch to coarse pointing mode (sun sensors + magnetometer)
5. Impact assessment: Can mission science continue in coarse pointing mode?

#### Anomaly D: Unexpected Safe Mode Entry

*"Your satellite has autonomously entered Safe Mode. Last telemetry before entry showed: OBC reboot counter incremented by 3 in 10 minutes. All other parameters were nominal."*

Expected response:
1. Investigate: Multiple reboots suggest SEU (Single Event Upset) or firmware bug
2. Check radiation environment: Was the satellite in SAA (South Atlantic Anomaly)?
3. Review FDIR logs (stored in non-volatile memory) for fault triggers
4. Recovery plan: Command exit from Safe Mode; monitor for recurrence
5. If recurring: Upload software patch to increase SEU robustness

#### Anomaly E: Thermal Exceedance

*"Payload temperature has reached 58 C during a science observation, exceeding the 55 C operational limit. Battery temperature is 38 C (approaching 45 C limit)."*

Expected response:
1. Immediate: Disable payload to stop heat generation
2. Check attitude: Is the hot radiator face pointing toward the sun?
3. Review thermal model: Was this orbit geometry (high beta angle) predicted?
4. Mitigation: Adjust duty cycle; plan observations for cooler orbit phases
5. If structural: May need to update thermal model and operational constraints

### Anomaly Documentation

For each injected anomaly, teams complete the **Anomaly Response Form** on Worksheet 5.3:

| Field | What to Record |
|-------|---------------|
| Time (sim) | When the anomaly was detected |
| Observation | Exact telemetry values and symptoms |
| Initial assessment | Severity level (Green/Yellow/Orange/Red) |
| Diagnosis | Suspected root cause |
| Action taken | Commands sent, procedures executed |
| Result | System state after response |
| Follow-up required | Additional investigation, procedure updates |

---

## 5. Nominal Operations & Debrief
### Nominal Operations
**[Time Jump: T+30 days to T+1 year]**
*"Your mission has been operational for one month. All commissioning activities are complete. You are now in nominal operations. Let's review your operational metrics."*

Teams report:
- Total data downlinked in 30 days vs plan
- Number of science observations completed vs plan
- Any anomalies encountered (from injection exercise)
- Current budget status: power margin, data margin, propellant remaining (if applicable)
- Orbit status: any conjunction alerts? Debris compliance on track?

### Debrief
1. **What went well?**
   - Which procedures worked as written?
   - Which FDIR rules triggered correctly?
   - Where did the team communicate effectively?

2. **What could be improved?**
   - Which procedures needed real-time modification?
   - Were there gaps in the FDIR design?
   - Where did decision-making slow down?

3. **Lessons for the design:**
   - Did the simulation reveal any design weaknesses?
   - Should any requirements be changed based on operational experience?
   - What additional autonomy would help?

---

## Facilitator Notes

### Preparation

- Review each team's ConOps, FDIR rules, and procedures from Session 5.2
- Select anomalies appropriate to each team's mission (e.g., don't inject propulsion anomaly for a mission without propulsion)
- Prepare HK data tables for each phase (modify the values in Section 2 to match the team's mission parameters)
- Have backup anomalies ready if teams resolve injections quickly

### Pacing

- LEOP simulation should feel time-pressured (short passes, decisions needed quickly)
- Commissioning can be more relaxed
- Anomaly injection should be challenging but solvable with the team's procedures
- Allow extra time for debrief -- this is where the deepest learning occurs

### Assessment Criteria

Observe and note (for feedback, not formal grading):
- Did the team follow their procedures or improvise?
- Did the Flight Director coordinate effectively?
- Was the anomaly response systematic (detect-diagnose-plan-execute-verify)?
- Did the team document events in real-time?
- Did anyone identify a design flaw during operations?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| LEOP | First 72 hours are critical; every step is time-constrained |
| Commissioning | Systematic subsystem checkout before payload operations |
| Anomaly response | Follow the process: detect, assess, diagnose, plan, execute, verify, document |
| Documentation | Real-time logging is essential -- memory is unreliable under stress |
| FDIR validation | Simulation reveals gaps in FDIR design that analysis alone cannot find |
| Team coordination | Clear roles, communication protocols, and decision authority are essential |
| Design feedback | Operational experience should feed back into design (requirements, FDIR, procedures) |
