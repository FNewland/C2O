# Chapter 19 — Rehearsing the Mission: Operations Simulation

> **Recommended background.** ECSS-E-ST-70C (Ground systems and operations, §5 operations validation); ECSS-E-ST-70-11C (Space segment operability); ECSS-E-ST-70-32C (Procedures); the mission-operations chapters of SMAD. This chapter assumes the ground segment of Chapter 17 and the modes, FDIR rules and procedures of Chapter 18 exist on paper; its purpose is to find out whether they work before the spacecraft leaves the ground.

## Learning objectives

By the end of this chapter, you will be able to:

1. Explain why space agencies rehearse operations before launch, and what a rehearsal finds that analysis cannot
2. Structure an operations rehearsal through LEOP, commissioning, nominal operations and anomaly injection, at a fidelity appropriate to the project
3. Allocate operations roles for a team of any size, including the simulation controller
4. Select, script and inject anomaly scenarios from a reusable library, each with symptoms, expected diagnosis and recovery
5. Run a structured debrief and feed its findings back into the ConOps, the FDIR rules, the procedures and the requirements

---

## 19.1 Why agencies rehearse

A spacecraft is operated by people following procedures through a ground segment, and none of those three has flown before launch. Analysis can show that the power budget closes and that the FDIR rules are consistent; it cannot show that an operator at the end of a night shift will read the right telemetry page, that the safe-mode recovery procedure has a step whose expected result is unobservable, or that two roles both believe the other owns the decision to command a reset. Those are found by rehearsal.

### 19.1.1 Agency practice

- **ESA** runs a *simulation campaign* at ESOC for every mission in the months before launch: the flight-control team operates a software simulator of the spacecraft through LEOP and early operations, while a simulations officer injects faults into the simulator and the ground segment without warning. Campaigns run to dozens of simulation runs, and the launch is not approved until the team has recovered from the injected contingencies with the real procedures and the real control system. ECSS-E-ST-70C requires that the ground segment and the operations preparation be validated before launch; the simulation campaign is how the operations part of that requirement is met.
- **NASA** and its centres run *operational readiness tests* (ORTs) and mission readiness tests in which the flight team, the ground network and the spacecraft (or its simulator) are exercised end to end against the launch timeline, with anomalies scripted by a test conductor. The flight-rules and procedure sets are frozen only after the ORTs are complete.
- **Both** continue to rehearse after launch: before every critical event — orbit insertion, a landing, a safe-mode exit after a long outage — the team runs the sequence against the simulator first. The operating principle is *train like you fly, fly like you train*: the rehearsal uses the real consoles, the real procedures and the real voice loops, so that the only thing different on the day is the spacecraft.

### 19.1.2 What a rehearsal finds

Experience across agency and university missions gives a consistent list:

| Finding | Typical example | Where it should have been caught |
|---------|-----------------|------------------------------|
| Procedure gaps | A step whose "expected result" is a telemetry point not in the housekeeping packet | Procedure review (Chapter 18 §18.4) |
| FDIR gaps | A fault the rules detect but whose response leaves the spacecraft in a mode with no path to Safe | State-machine check (Chapter 18 §18.2.2) |
| Role ambiguity | Two people both wait for the other to authorise a command; or both send one | ConOps staffing plan (Chapter 18 §18.1.1) |
| Timeline optimism | The LEOP plan needs three activities on a five-minute pass | Operations timeline (Chapter 17 §17.4) |
| Ground-segment faults | Wrong Doppler sign in the tracking software; a pass predicted from a stale element set | Ground-segment validation |
| Design weaknesses | Safe mode is not power-positive in the tumbling attitude the rehearsal put it in | Power budget (Chapter 9) |

The last row is the important one for a design textbook: the rehearsal is a *verification activity for the design*, late in Phase D, and its findings are requirement changes. Operations reveal what analysis cannot.

### 19.1.3 Fidelity levels

A rehearsal does not need a flight-software simulator to be useful. Four levels, in increasing cost:

| Level | Spacecraft representation | Telemetry source | Suited to |
|-------|---------------------------|------------------|-----------|
| **Tabletop** | None; the simulation controller narrates state and reads out telemetry values | Prepared tables | Early Phase C; concept-level ConOps; any team |
| **Spreadsheet model** | Power, data and mode state tracked in a spreadsheet the controller updates per orbit | Spreadsheet | Phase C/D; checking budgets under operations |
| **Software simulator** | Flight-software model with a telemetry/telecommand interface to the real control system | Simulator | Phase D; procedure validation; agency standard |
| **Hardware-in-the-loop** | Engineering model on the bench, fed by simulated sensors | Flight-like | Phase D; end-to-end validation; mission-critical procedures |

This chapter is written so that it can be run at the first two levels by any team, and scaled to the upper two when the project has them. Everything in §19.3–§19.6 is independent of fidelity.

---

## 19.2 Structuring a rehearsal

### 19.2.1 The elements

Every operations rehearsal, from a two-hour tabletop to a three-month agency campaign, has the same five elements:

1. **A simulated spacecraft** — at one of the fidelity levels of §19.1.3 — whose state evolves according to the mission's own mode table, power budget and data budget.
2. **A simulation controller** ("the Universe"), who holds the script, advances simulated time, reads out telemetry, decides what the spacecraft does in response to each command, and injects the anomalies. The controller is not a member of the operations team and does not help it.
3. **Compressed time.** Simulated time jumps between events; a 72-hour LEOP is rehearsed in an hour or two by playing only the passes and the decisions. The controller announces each jump ("it is now T+24 h; eight passes have occurred with nominal housekeeping").
4. **A script** — the sequence of events, the telemetry the controller will read out at each, and the expected responses (§19.4).
5. **A log**, kept in real time by a named role, of every event, telemetry readout, command and decision, with simulated and real time stamps. The log is the input to the debrief, and real-time logging is itself a skill being rehearsed: memory is unreliable under pressure.

### 19.2.2 Phases

A full rehearsal walks the operations timeline of Chapter 17 §17.4.1 in order, because each phase assumes the previous one succeeded:

| Simulated time | Phase | What is rehearsed |
|----------|-------|--------|
| T+0 to T+1 h | LEOP | Separation, RF-inhibit timer, antenna deployment, beacon acquisition, first housekeeping, first uplink |
| T+1 h to T+24 h | Early LEOP | Array deployment, AOCS initialisation, communication-chain validation |
| T+1 to T+7 days | Commissioning | Subsystem checkout, AOCS calibration, payload first light, first data download |
| T+7 to T+30 days | Early operations | Nominal science or service, procedure refinement |
| *(any phase)* | Anomaly injection | Two or three scenarios from the library of §19.5, chosen for the mission |
| T+30 days to T+1 year | Nominal operations | Metrics review against plan |
| — | Debrief | §19.6 |

A shorter rehearsal takes a subset: LEOP alone (the most time-critical phase, and the one the team will fly only once); or nominal operations with anomaly injection (the phase the team will fly for years). The anomaly injections are placed in whichever phase makes them hardest — a battery under-voltage is a different problem during commissioning, when the team has not yet seen a normal eclipse, than in month six.

### 19.2.3 Pacing

LEOP should feel time-pressured: passes are short, and decisions must be made before loss of signal or wait ninety minutes. Commissioning can be slower. Anomaly injection should be challenging but solvable with the team's own procedures — the aim is to test the procedures, not to defeat the team. The debrief should be given more time than seems necessary; it is where the findings are turned into changes.

---

## 19.3 Role allocation for any team size

### 19.3.1 Operations roles

The roles mirror a real flight-control team, scaled down. Each has a defined authority and a defined set of telemetry it watches.

| Role | Responsibility | Authority | Watches |
|------|---------------|-----------|---------|
| **Flight director (FD)** | Overall decision authority; coordinates the team; declares anomaly severity (Chapter 18 §18.5.1) | GO/NO GO on every non-routine command | The whole picture; the clock |
| **Spacecraft controller (SC)** | Sends commands; monitors housekeeping telemetry; executes procedures step by step | Routine commands within an approved procedure | Bus housekeeping; mode; FDIR flags |
| **Ground-station operator (GSO)** | Antenna scheduling; link acquisition; signal quality | Ground-segment configuration | Carrier, Doppler, signal strength, frame lock |
| **Payload operator (PO)** | Plans and executes observations; tracks the data budget | Payload commands within an approved procedure | Payload housekeeping; mass-memory fill |
| **Flight dynamics (FDyn)** | Orbit knowledge; pass predictions; manoeuvre planning if there is propulsion; conjunction alerts | Element-set updates | Orbit, eclipse times, pass geometry |
| **Anomaly logger** | Records every event, readout, command and decision with time stamps; maintains the anomaly report (Chapter 18 §18.5.3) | None — deliberately | Everything |
| **Simulation controller** | Runs the script; advances time; injects anomalies; plays the spacecraft and the outside world | Absolute, over the simulated universe | The team |

### 19.3.2 Scaling the team

For smaller teams, combine roles; SC+GSO and PO+FDyn are natural pairings because each pair watches related telemetry. The flight director and the simulation controller must never be the same person, and the logger should not also be the flight director.

| People available | Allocation |
|------------------|-----------|
| 2 | Simulation controller; one operator who is FD, SC, GSO, PO and logger at once (useful for a solo walk-through of a procedure, not for a team rehearsal) |
| 3 | Simulation controller; FD + logger; SC + GSO + PO + FDyn |
| 4 | Simulation controller; FD; SC + GSO; PO + FDyn + logger |
| 5 | Simulation controller; FD; SC + GSO; PO + FDyn; logger |
| 6–7 | Simulation controller; FD; SC; GSO; PO + FDyn; logger (+ a second controller to play the ground station) |
| 8+ | All seven roles, plus a second shift — which allows the most instructive injection of all, a handover in the middle of an anomaly |

### 19.3.3 Communication discipline

Three rules borrowed from real control rooms, each of which the rehearsal will test:

- **Every command is called before it is sent** ("SC to FD: request GO for payload power ON, step 2 of NOM-SCI-001") and acknowledged ("FD: GO").
- **Every telemetry readout is stated with its expected range** ("bus voltage 7.8, expected 7.0 to 8.4, nominal"), so that the logger and the flight director hear the comparison, not just the number.
- **Nobody acts outside a procedure without the flight director saying so.** Improvisation is sometimes right; silent improvisation never is.

---

## 19.4 Scripting the phases

The scripts below are written for the 3U Earth-observation CubeSat, EOSat-3U, with the modes of Chapter 18 Table 18.1; the simulation controller adapts the telemetry values to the mission being rehearsed. Each entry gives the controller's narration, what the team is expected to do, and what a good response looks like.

### 19.4.1 LEOP

**[T+0 — Separation]** *"The satellite has separated from the deployer. Deployment switches have released. The 30-minute timer has started. You are in radio silence — no RF emission is allowed until the timer expires. What is the spacecraft doing right now?"*

Expected: the timer is counting down; the battery is powering the OBC and nothing else; the spacecraft is tumbling at the separation rate; no deployments have occurred. A good team also states what it *cannot* know — the attitude, the battery state — and when it first will.

**[T+30 min — Timer expires]** *"The timer has expired. The OBC has commanded antenna deployment. What do you expect to see, and from where?"*

Expected: the antenna deployment command has been issued by the on-board sequence; the beacon should begin transmitting; nothing can be confirmed until a station is in view. The team should already know when the first pass is (flight dynamics) and whether it falls before or after T+30 min (Chapter 17 §17.4.3).

**[T+35 min — First pass]** *"Your ground station has line of sight. The antenna operator reports: carrier detected at the expected frequency with a Doppler offset consistent with an approaching pass. Signal strength is −110 dBm. Is this what you expected?"*

The team should verify that the carrier frequency matches the prediction (accounting for Doppler), that the signal strength is consistent with the link budget at the current slant range (Chapter 11 §11.8.1), and that the beacon data rate is as designed. A team that simply says "yes" has not checked.

**[T+40 min — First telemetry]** *"Beacon lock achieved. You are receiving housekeeping. Here is the first frame:"*

| Parameter | Value | Expected range | Status |
|-----------|-------|---------------|--------|
| Bus voltage | 7.8 V | 7.0–8.4 V | Nominal |
| Battery state of charge | 72 % | > 50 % | Nominal |
| Solar-array current | 0.45 A | 0.3–0.6 A | Nominal |
| OBC temperature | 22 °C | −10 to +50 °C | Nominal |
| Battery temperature | 19 °C | 0 to 45 °C | Nominal |
| AOCS mode | Detumble | Expected | Nominal |
| Angular rate | 3.2 °/s | Decreasing | Nominal |
| Antenna status | Deployed | Expected | Nominal |
| Beacon mode | Active | Expected | Nominal |
| Uplink status | Not yet attempted | — | — |

Expected: the spacecraft controller reads each value against its range aloud; the flight director declares LEOP step "first telemetry" complete; the logger records the frame. A controller who wants to make this harder changes one value — a battery temperature of −2 °C, say — and watches whether anyone notices.

**[T+1 h — Uplink validation]** *"Send a no-operation command to verify the uplink chain."*

Expected: the controller composes the command, verifies its encoding, calls it to the flight director, transmits, and waits for the acknowledgement counter in the next telemetry frame to increment. The uplink is not validated until that counter is seen.

### 19.4.2 Commissioning

**[Time jump: T+24 h]** *"Detumbling is complete. The AOCS is in sun-pointing mode. All housekeeping parameters have been nominal across eight passes. You are ready to begin commissioning. What is your first activity?"*

Expected: AOCS calibration — magnetometer bias estimation, sun-sensor alignment verification — before anything that depends on attitude. A team that goes straight to the payload has skipped the step the payload's pointing will rely on.

**[T+3 days — Payload first light]** *"The AOCS is calibrated and achieving 0.3° pointing. You are ready for payload first light. Walk me through your procedure."*

The team executes its science-observation procedure (Chapter 18 §18.4.3) step by step, calling each expected result. The controller plays the spacecraft: for each step, either the expected result is reported or it is not, and the team must take the recovery action the procedure specifies. A procedure with no recovery action for a step is a finding.

**[T+5 days — First data download]** *"The payload has captured 150 MB of imagery. Your next pass is 8 minutes above the mask. Can you download it all in one pass?"*

Expected calculation (Chapter 17 §17.2.2): at 2 Mbit/s, 8 min and $\eta = 0.9$, the capacity is $2 \times 10^6 \times 480 \times 0.9 / 8 = 108$ MB — so no; two passes are needed, and the payload operator plans the sequence and states which data go first. A team that answers without calculating has not understood why the data budget exists.

### 19.4.3 Nominal operations

**[Time jump: T+30 days to T+1 year]** *"The mission has been operational for a month. Commissioning is complete. Review your operational metrics."*

The team reports:
- total data downlinked in 30 days versus plan
- number of observations completed versus plan
- anomalies encountered (from the injection exercise) and their status
- current budget status: power margin, data margin, propellant remaining if applicable
- orbit status: conjunction alerts, debris-compliance tracking (Chapter 3 §3.6)

This is the moment at which the rehearsal checks whether the mission, operated as the ConOps describes, actually delivers what the requirements promised. A data return of 60 % of plan is a common and instructive result.

---

## 19.5 A library of anomaly scenarios

Each scenario below is written as the simulation controller injects it, followed by the symptoms the team can observe, the diagnosis a well-prepared team should reach, the recovery it should execute, and the FDIR rule or design feature the scenario exercises. Choose two or three per rehearsal, appropriate to the mission — do not inject a propulsion anomaly into a mission without propulsion — and keep one in reserve for a team that resolves the first quickly.

### 19.5.1 Battery under-voltage

**Injection.** *"During eclipse you receive an alert: battery voltage has dropped to 6.2 V, below the 6.5 V warning threshold. Battery temperature is 5 °C. State of charge is estimated at 18 %."*

**Symptoms.** Voltage below warning, state of charge far below the end-of-eclipse value the power budget predicts; low battery temperature reducing available capacity; possibly a mode change already executed by FDIR.

**Expected diagnosis.** Consumption has exceeded generation over several orbits. Candidate causes: solar-array degradation or a string failure; an unexpected load (a heater stuck on, a payload left powered); battery degradation; an attitude that under-illuminates the array; a longer eclipse than planned (β-angle season, Chapter 7 §7.1.2). The discriminating telemetry is the array current trend over the last 24 hours against the attitude history.

**Recovery.** Verify that FDIR has shed loads (payload off, non-essential heaters off); if not, command Safe manually. Then review the power trend and compare with the budget; do not leave Safe until generation exceeds consumption with margin and the cause is known.

**Exercises.** The under-voltage rule of Chapter 18 §18.3.4; whether Safe is power-positive (Chapter 9 §9.2); whether the team can read a trend, not just a value.

### 19.5.2 Communication loss

**Injection.** *"You have received no telemetry for the last three scheduled passes (18 hours). The ground station reports pointing and frequency correct, but no carrier detected."*

**Symptoms.** Silence. Nothing else — which is the point.

**Expected diagnosis.** Rule out the ground first: antenna, LNA, modem, element set, Doppler sign. Then seek independent evidence — ask a volunteer network or another station whether anyone has heard the beacon. Then consider the spacecraft: transmitter failure, antenna not deployed, attitude loss (antenna pointed away), a power fault that has taken the transmitter down, an OBC hang. If the mission has a no-uplink timer (48 h in Chapter 18 §18.3.4), the spacecraft will reset its TT&C and revert to beacon on its own.

**Recovery.** Fix or exclude the ground; configure a wide-beam antenna for a beacon search; wait for the timer-based reset; plan the uplink that follows it. The flight director must decide how long to wait before escalating to Red (Chapter 18 §18.5.1).

**Exercises.** The communication-loss FDIR rule; the ground-segment fault tree; the team's discipline in not commanding blind.

### 19.5.3 Loss of fine pointing

**Injection.** *"Pointing error has increased from 0.1° to 5°. The star tracker reports 'no solution'. Reaction wheels are at 80 % of capacity."*

**Symptoms.** Pointing degraded; attitude-determination source lost; momentum near saturation.

**Expected diagnosis.** Star-tracker failure, optical contamination, Sun or Earth in its field of view, or a wheel approaching saturation that has driven the attitude away from the tracker's acquisition range. Check the coarse attitude from magnetometer and sun sensors — is it consistent with the last good tracker solution? Check the wheel-speed history — was momentum building before the tracker dropped out?

**Recovery.** Command desaturation with the magnetorquers first (Chapter 10 §10.5); then switch to coarse pointing (sun sensors + magnetometer); then attempt tracker reacquisition. Assess the impact: can imaging continue in coarse pointing, and at what cost in image quality (Chapter 10 §10.4)?

**Exercises.** The wheel over-speed rule; the subsystem-level (Level 2) fallback of Chapter 18 §18.3.2; graceful degradation versus safe mode.

### 19.5.4 Unexpected safe-mode entry

**Injection.** *"The satellite has autonomously entered Safe. The last telemetry before entry showed the OBC reboot counter incrementing three times in ten minutes. All other parameters were nominal."*

**Symptoms.** Safe mode with no obvious hardware cause; a reboot cluster.

**Expected diagnosis.** Repeated reboots suggest a single-event upset or a firmware fault. Was the spacecraft in the South Atlantic Anomaly (Chapter 7 §7.6)? Read the FDIR log from non-volatile memory for the fault triggers. Correlate with the orbit position and with any command sent just before.

**Recovery.** Command exit from Safe only after the log has been read and the cause assigned; monitor for recurrence over several SAA passes; if it recurs, upload a software patch (or change the EDAC scrub rate) to improve upset robustness.

**Exercises.** The watchdog and memory-corruption rules; the "recovery requires a diagnosis" precondition of Chapter 18 §18.4.3; the radiation design of Chapter 7 §7.6 and risk R-03 of Chapter 15 §15.5.

### 19.5.5 Thermal exceedance

**Injection.** *"Payload temperature has reached 58 °C during an observation, above the 55 °C operational limit. Battery temperature is 38 °C, approaching the 45 °C limit."*

**Symptoms.** Payload over its operational limit; battery warming towards its limit; both during a sunlit observation.

**Expected diagnosis.** The hot case has been exceeded. Is the radiator face Sun-pointed in the imaging attitude? Is the orbit in a high-β season the thermal model (Chapter 9 §9.4) did not cover? Has the imaging duty cycle crept above the value the thermal case assumed?

**Recovery.** Disable the payload immediately; check and if necessary change the attitude; review the thermal model against the actual orbit geometry; reduce duty cycle and schedule observations for cooler orbit phases; if the model is wrong, update it and the operational constraints with it.

**Exercises.** The battery over-temperature rule; whether the ConOps carries thermal constraints as operational limits; feedback from operations to the thermal design.

### 19.5.6 Ground fault masquerading as a spacecraft fault

**Injection.** *"On the pass you receive carrier and frames, but every frame fails its checksum. Signal strength is 6 dB lower than on the previous pass."*

**Symptoms.** Link present but unusable; reduced signal.

**Expected diagnosis.** A 6 dB loss with a lock still achieved points at the ground — a mis-pointed antenna, a wrong polarisation, a cable or LNA fault, rain — before the spacecraft. A spacecraft transmitter fault would more often give no carrier at all. Compare with another station if one is available.

**Recovery.** Ground-segment checks between passes; a second station if available; if the loss persists across stations, revisit the spacecraft antenna and attitude.

**Exercises.** Rule-out-the-ground discipline; the ground-station operator's role; the link margin of Chapter 11 §11.8.1 (is 6 dB within margin or not?).

### 19.5.7 Mass memory full

**Injection.** *"The payload operator reports that the mass memory is at 97 % and the next three passes are over the low-elevation station."*

**Symptoms.** Storage nearly exhausted; downlink capacity for the next day below generation.

**Expected diagnosis.** The data budget (Chapter 11 §11.9, Chapter 17 §17.2.4) is not closing at the current duty cycle and station schedule — possibly because a station outage, a missed pass or a higher-than-planned imaging rate has eaten the margin.

**Recovery.** Prioritise: which data are downlinked first, which may be overwritten? Reduce the imaging duty cycle until the backlog clears; buy or borrow passes if the mission can; check the on-board storage sizing of Chapter 12 §12.3.3 against the outage assumption it was built on.

**Exercises.** Data-budget management under operations; payload-operator judgement; the outage case in storage sizing.

### 19.5.8 Command rejected

**Injection.** *"The safe-mode exit command has been sent three times. Telemetry shows the command counter incrementing but the mode unchanged, and a 'command rejected' flag set."*

**Symptoms.** Uplink works; the spacecraft refuses the command.

**Expected diagnosis.** An on-board precondition is not met — a battery state-of-charge interlock, an attitude-knowledge flag, a FDIR inhibit still active — or the command is being sent with a wrong parameter or in a wrong mode. Read the rejection reason if the telemetry has one; if it does not, that is a finding.

**Recovery.** Satisfy the precondition (wait for charge; clear the inhibit by its own command) rather than overriding it; override only on flight-director authority with the reason logged.

**Exercises.** Procedure preconditions; the ground-override principle of Chapter 18 §18.3.5 and its limits; whether the telemetry tells the operator *why*.

### 19.5.9 Shift handover during an anomaly

**Injection** (teams with a second shift). *"It is the end of the shift. The battery under-voltage of §19.5.1 is still under investigation. Hand over."*

**Symptoms.** None in the spacecraft; the hazard is in the team.

**Expected response.** A structured handover: current mode, open anomalies and their severity, actions in progress and who owns them, next pass time and what is planned on it, outstanding decisions for the flight director. The incoming shift repeats it back.

**Exercises.** The staffing plan of Chapter 18 §18.1.1; the log as the handover document; whether anything was known only in someone's head.

### 19.5.10 Recording the response

For each injected scenario the anomaly logger completes the response record, which is the Chapter 18 §18.5.3 report in its shortest form:

| Field | What to record |
|-------|---------------|
| Time (simulated) | When the anomaly was detected |
| Observation | Exact telemetry values and symptoms |
| Initial assessment | Severity level (Green / Yellow / Orange / Red) and who declared it |
| Diagnosis | Suspected root cause, and the telemetry that supports it |
| Action taken | Commands sent, procedures executed, by whom, authorised by whom |
| Result | System state after the response |
| Follow-up required | Further investigation; procedure, FDIR or requirement updates |

---

## 19.6 The debrief

The debrief is where the rehearsal pays for itself. It is run by someone other than the flight director, works from the log and the response records rather than from memory, and is organised around three questions.

### 19.6.1 Three questions

1. **What went well?** Which procedures worked as written? Which FDIR rules triggered correctly? Where did the team communicate effectively?
2. **What could be improved?** Which procedures needed modification in real time? Were there gaps in the FDIR design? Where did decision-making slow down, and why — missing information, unclear authority, or an unobservable expected result?
3. **Lessons for the design.** Did the rehearsal reveal a design weakness? Should any requirement change on the strength of operational experience? What additional autonomy would have helped, and what would it cost?

### 19.6.2 Observations worth recording

A useful debrief looks for specific behaviours rather than general impressions:

- Did the team follow its procedures, or improvise — and when it improvised, was it right, and was it announced?
- Did the flight director coordinate, or operate? (A flight director who is reading telemetry is not directing.)
- Was the anomaly response systematic — detect, assess, diagnose, plan, execute, verify, document — or did it jump from symptom to command?
- Was the log complete enough to reconstruct the anomaly afterwards?
- Did anyone identify a design flaw during operations, and was it captured?

### 19.6.3 Closing the loop

Every finding becomes one of four kinds of change, each with an owner and a date:

| Finding | Becomes | Goes to |
|---------|---------|---------|
| Procedure gap or error | Procedure revision | Operations (Chapter 18 §18.4) |
| FDIR gap or wrong threshold | FDIR rule change | Flight software and the FMECA (Chapter 15, Chapter 18 §18.3) |
| Role or authority ambiguity | ConOps staffing-plan revision | ConOps (Chapter 18 §18.1) |
| Design weakness | Requirement change or waiver | Requirements and the risk register (Chapters 5, 15); the next review gate (Chapter 16) |

A rehearsal whose findings are not tracked to closure was a rehearsal of the wrong thing.

---

## 19.7 Returning to UniSat-1: a rehearsal for a three-person team

UniSat-1's operations team is three students, which §19.3.2 allocates as simulation controller; flight director + logger; and one operator covering spacecraft, ground station, payload and flight dynamics. The rehearsal is a tabletop (§19.1.3), because the spacecraft has three modes (Chapter 18 §18.6) and its state fits on one page.

The script of §19.4 shortens accordingly: there is no array deployment and no AOCS calibration, so commissioning is complete once the magnetometer returns plausible field values on the second day; the first-data-download calculation uses the 5-minute UHF passes and 153 kB per pass of Chapter 11 §11.8.2, which makes the data-budget shortfall (risk R-02 of Chapter 15 §15.5) the natural subject of the nominal-operations metrics review. Of the scenario library, §19.5.1, §19.5.2, §19.5.4 and §19.5.6 apply directly; §19.5.3 does not (no wheels or tracker); and §19.5.8 is worth injecting because the custom OBC's interlocks are the least-tested part of the flight software. The debrief question that matters most for a mission with student operators is the first of §19.6.2: with one operator holding four roles, the procedures must be good enough to be followed exactly, because there is nobody to catch an improvisation.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Why rehearse | Procedures, FDIR, roles and ground segment have never flown; rehearsal finds what analysis cannot; ESA simulation campaigns and NASA readiness tests are the models |
| Fidelity | Tabletop → spreadsheet → software simulator → hardware-in-the-loop; the structure is the same at every level |
| Elements | Simulated spacecraft, simulation controller, compressed time, script, real-time log |
| Phases | LEOP (time-critical, flown once) → commissioning → early and nominal operations, with anomaly injection where it is hardest |
| Roles | FD, SC, GSO, PO, FDyn, logger, simulation controller; combine SC+GSO and PO+FDyn for small teams; FD and controller never the same person |
| Anomaly library | Nine scenarios, each with symptoms → diagnosis → recovery → what it exercises; choose for the mission, keep one in reserve |
| Response | Detect, assess, diagnose, plan, execute, verify, document; rule out the ground first; never command blind |
| Debrief | What went well, what to improve, lessons for the design; every finding becomes a tracked procedure, FDIR, ConOps or requirement change |

---

## Problems

1. **Design a LEOP rehearsal.** For a 3U Earth-observation CubeSat deployed into a 500 km sun-synchronous orbit with one S-band station at 45° N, write the simulation controller's script for the first 24 hours: every pass (use Chapter 17 §17.2.3 for the count and duration), the telemetry read out on each, the activity of Chapter 17 §17.4.3 attempted on each, and the decision the team must make before loss of signal. Mark the pass on which you would inject a modified telemetry value, and say which.

2. **Scale the team.** Allocate the roles of §19.3.1 for teams of 3, 5 and 8 people for the mission of Problem 1, and for each allocation identify the single communication failure most likely to occur (who waits for whom) and the rule of §19.3.3 that prevents it.

3. **Write a scenario.** Add a tenth scenario to the library of §19.5 for a mission with cold-gas propulsion — a thruster that fails to produce the commanded ΔV during a collision-avoidance manoeuvre — in the same format: injection, symptoms, expected diagnosis, recovery, and what it exercises. Cite the flight-dynamics function of Chapter 17 §17.1.4 and the FDIR level of Chapter 18 §18.3.2 it tests.

4. **Spreadsheet-fidelity model.** Specify the minimum spreadsheet model that lets a simulation controller play the EOSat-3U spacecraft credibly through §19.5.1 and §19.5.7: the state variables (mode, battery state of charge, mass-memory fill, wheel momentum), the per-orbit update rules from Chapter 18 Table 18.1 and Chapter 9, and the telemetry values derived from them. State which anomaly injections become mere parameter changes in this model.

5. **Anomaly response record.** Run §19.5.4 against the UniSat-1 design (Chapter 18 §18.6) on paper, playing both the controller and the team, and complete the response record of §19.5.10. Then state which FDIR rule, which procedure precondition and which risk-register entry the exercise touched, and what you would change in each.

6. **Safe-mode survival rehearsal.** Script a rehearsal whose only purpose is to test whether a mission can survive a safe-mode entry at the start of an unstaffed weekend (60 hours). List the telemetry the controller must generate per orbit, the decisions the team must make at the first staffed pass, and the pass/fail criterion. Use the EOSat-3U numbers of Chapter 18 Table 18.1 and the battery of Chapter 9 §9.3.

7. **Debrief to design.** A rehearsal of the 3U mission produces these findings: (a) the safe-mode recovery procedure's step 4 expects a telemetry point that is only in the extended housekeeping packet; (b) the flight director and spacecraft controller both believed the other would decide on the desaturation command; (c) in the tumbling attitude the controller imposed, the orbit-average array power came out below the 2 W safe-mode load. Classify each finding using §19.6.3, write the change it becomes with an owner, and identify the review gate of Chapter 1 Table 1.3 at which each should be re-examined.

8. **Fidelity trade.** For a university 3U mission with 18 months to launch and a flight-software team of two, estimate the effort (person-weeks) to reach each fidelity level of §19.1.3 and the classes of finding from §19.1.2 that each level can and cannot produce. Recommend a level, and say which single finding class you would be accepting not to catch before launch.

---

## References

1. ECSS, *ECSS-E-ST-70C: Ground Systems and Operations*, 2008. https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/
2. ECSS, *ECSS-E-ST-70-11C: Space Segment Operability*, 2008. https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/
3. ECSS, *ECSS-E-ST-70-32C: Test and Operations Procedure Language*, 2008. https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/
4. NASA, *Fault Management Handbook*, NASA-HDBK-1002, 2012. https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002
5. NASA Goddard Space Flight Center, *Rules for the Design, Development, Verification, and Operation of Flight Systems*, GSFC-STD-1000 (the "Gold Rules"), current revision. https://standards.nasa.gov/standard/GSFC/GSFC-STD-1000
6. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §5.5 (Transition to operations) and §6.4. https://www.nasa.gov/reference/systems-engineering-handbook/
7. ESA, *Operations: Mission Control*, European Space Operations Centre. https://www.esa.int/Enabling_Support/Operations
8. Wertz, J. R. & Larson, W. J. (eds.), *Space Mission Analysis and Design*, 3rd ed., Microcosm/Kluwer, 1999, Chapter 14 (Mission Operations).
9. Squibb, G. F., Boden, D. G. & Larson, W. J. (eds.), *Cost-Effective Space Mission Operations*, 2nd ed., McGraw-Hill, 2006.
10. Wertz, J. R., Everett, D. F. & Puschell, J. J. (eds.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, Chapter 29 (Mission Operations).
