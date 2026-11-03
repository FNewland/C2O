# Part 5 — OrbitNorth Week 3 Workbook

This part of the workbook is the operator's pad for the five-day
**OrbitNorth Week 3** spacecraft operations training. It runs
Monday 17 August to Friday 21 August 2026 at the uOttawa
Cyberrange.

The structure mirrors Part 2 of the textbook. For every nominal
and contingency procedure run during the week, there is a
**confirm-each-step** worksheet: you tick each step when
verified, write the actual telemetry value in the *note* column,
and flag anything off-nominal. Anomaly tickets, handover
templates, observer worksheets, and end-of-shift debrief pages
are between the day worksheets.

**How to use these worksheets.**

- Bring the printed worksheet to the console at the start of
  every shift.
- Write in pen so corrections are visible (cross out, don't
  erase).
- Fill in every box, even if the answer is "nominal" or
  "n/a — not run".
- Hand the completed worksheet to the instructor at end of shift.
  The cohort lessons-learned register feeds off them.

The worksheet IDs follow the pattern `WB-5.X-NAME` so they
cross-reference cleanly with textbook chapters.

---

# Worksheet WB-5.0 — Orientation Check

**Use:** complete *before* arriving at the Cyberrange Monday
morning. Brings you up to a common baseline with the rest of the
cohort.

**Name:** _________________________________   **Date:** ______________

### Section A — Mission facts

Fill in each value. Source: textbook §5.0.7.

| Item | Your answer |
|------|-------------|
| EOSAT-1 platform (bus type, units) | |
| Orbit altitude (km) | |
| Orbit inclination (°) | |
| Local time of ascending node (LTAN) | |
| Mission band | |
| Number of imager bands and their centre wavelengths (nm) | |
| Ground stations — all five (name and latitude) | |
| Battery capacity (Wh) | |
| Battery chemistry and cell configuration | |
| Instrument swath (km) and GSD (m) | |
| Pointing requirement in NOMINAL, mode 4 (°) | |
| Pointing requirement in FINE_POINT, mode 5 (°) | |
| Propulsion: type and total Δv (m/s) | |

### Section B — Control room positions

For each position, write a one-sentence mandate in your own words.

| Position | Mandate (one sentence) |
|----------|------------------------|
| Flight Director | |
| SPACON / FDIR & Systems | |
| AOCS Engineer | |
| EPS Engineer | |
| Thermal Engineer | |
| TT&C Engineer | |
| Payload Operations | |
| FDS / Orbit Analyst | |
| Ground Segment Engineer | |
| Mission Manager | |

### Section C — Pre-week reflection

What part of the operations work are you most looking forward to?

_____________________________________________________________

_____________________________________________________________

What part are you most nervous about?

_____________________________________________________________

_____________________________________________________________

---

# Worksheet WB-5.1 — Position score cards (round-robin)

**Use:** Monday afternoon 13:00 – 15:00: a 15-minute briefing, then
seven 15-minute stations, one per configured MCS console
(`configs/eosat1/mcs/positions.yaml`). One card per console. As
each station's 15-minute slot ends, write a one-sentence
observation under "Insight" and a one-sentence question under
"Question to ask". Mission Manager and Ground Segment are room
roles, not consoles; the ground-segment checks sit on the TT&C card.

**Name:** _________________________________

## 5.1.1 Flight Director

- **Task:** Run a GO/NO-GO round on the live dashboard. Poll three
  positions for *go for* `CONNECTION_TEST` (S17.1) — there is no
  NOOP or heartbeat command on this spacecraft; record the responses.
- **Polled positions:** _____________ , _____________ , _____________
- **Responses recorded (verbatim):**
  - _____________________________________________
  - _____________________________________________
  - _____________________________________________
- **Time on FD seat:** ____ : ____  to  ____ : ____
- **Insight:** _________________________________________________
- **Question to ask:** _________________________________________

## 5.1.2 Power & Thermal

- **Task:** Predict battery SoC at exit of the next eclipse, then
  identify which heater is at the highest duty cycle and predict
  whether it will saturate next eclipse.
- **SoC at eclipse entry:** ____ %   **Eclipse duration:** ____ min  (33.2–35.2 min over the year)
- **Predicted SoC at exit:** ____ %   **(Method:** P_avg × t / E_batt,
  with E_batt = **100 Wh** and the nominal orbit-average load  P_avg ≈ **28.8 W** **)**
- **Cross-check vs eclipse model:** ☐ matches  ☐ off by ____ %
- **Heater with highest duty:** _______________   **Duty:** ____ %
- **Predicted next-eclipse duty:** ____ %   **Will saturate?** ☐ yes ☐ no
- **Insight:** _________________________________________________
- **Question to ask:** _________________________________________

## 5.1.3 Flight Dynamics

- **Task:** Read `aocs.att_error` (0x0217) and verify it is inside
  the NOMINAL (mode 4, nadir-tracking) budget of < 1.0°. In
  FINE_POINT (mode 5) the budget is < 0.1°. Then compute AOS, TCA
  and LOS for the next Iqaluit pass and compare with the MPS
  contact schedule.
- **Reading:** ______ °   **In band?** ☐ yes  ☐ no
- **AOCS mode (`aocs.mode` 0x020F):** ____ (0 OFF, 1 SAFE_BOOT,
  2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT, 6 SLEW,
  7 DESAT, 8 ECLIPSE, 9 INERTIAL)
- **Star tracker status** (`aocs.st1_status` 0x0240 / `aocs.st2_status`
  0x0243; 0=off, 1=boot, 2=tracking, 3=blind, 4=failed):
  ST1 ____  ST2 ____   **Selected** (`aocs.st_selected` 0x0244): ____
- **Next Iqaluit pass:** AOS ______ TCA ______ LOS ______ max el ____ °
- **MPS agreement:** ☐ exact  ☐ off by < 5 s  ☐ off by > 5 s
- **Insight:** _________________________________________________
- **Question to ask:** _________________________________________

## 5.1.4 TT&C

- **Task:** Walk the TM rate ladder at AOS and confirm which ground
  station is carrying the pass. The ladder has three
  rungs — **SAFE 1 kbps / LOW 16 kbps / HIGH 128 kbps**
  (`ttc.tm_data_rate` 0x0506 in bps, `ttc.tm_tier` 0x0539 =
  0/1/2). LOW is the routine operations rung; HIGH is for dumps
  only and needs the deployed antenna and DOWNLINK mode on (func 79);
  the 10° elevation rule is ground arm-through policy, not an on-board gate.
  SAFE (called BEACON until 2026-08c) is not selectable with
  `TTC_SET_DATA_RATE` (S8 func 65).
  EOSAT-1 flies the **five-station** teaching baseline (`orbit.yaml`).
- **SAFE rate (kbps):** ______   **Routine LOW rate (kbps):** ______
  **Dump HIGH rate (kbps):** ______
- **Link margin post-transition (dB):** ______ (`ttc.link_margin` 0x0503)
- **BER reading (`ttc.ber` 0x050C, log10):** ____________________
- **Active station (`ttc.active_gs` 0x0523):** ______  ☐ Iqaluit
  ☐ Troll ☐ Svalbard ☐ Inuvik ☐ O'Higgins
- **Baseband config (rate, encoding):** ______________________
- **Insight:** _________________________________________________
- **Question to ask:** _________________________________________

## 5.1.5 Payload Operations

- **Task:** Schedule a single imaging session via MPS. Confirm FPA
  temperature is at setpoint before commanding.
- **Imaging target chosen:** _______________________________
- **FPA temperature reading (`payload.fpa_temp` 0x0601, °C):** ______
  **At setpoint?** ☐ yes ☐ no — the gate is `payload.fpa_ready`
  (0x0610) = 1, not a remembered temperature. Default setpoint
  **−15 °C** (`payload.fpa_setpoint` 0x0631; commandable envelope
  −20 °C to 0 °C).
- **Storage usage (`payload.mem_used_mb` 0x060B):** ______ / 20000 MB
- **Insight:** _________________________________________________
- **Question to ask:** _________________________________________

## 5.1.6 FDIR / Systems

- **Task:** Walk through one FDIR rule on the FDIR panel; explain
  its trigger, threshold, severity, and the contingency procedure
  it points to.
- **Rule name selected:** _____________________________
- **Trigger parameter:** _____________________________
- **Threshold:** ___________________   **Persistence:** _________
- **Severity:** ____   **Recommended procedure:** ________________
- **Insight:** _________________________________________________
- **Question to ask:** _________________________________________

## 5.1.7 Propulsion

- **Task:** Without commanding anything, read the propulsion state
  and name the interlock that is currently blocking an arm. Role
  brief: `configs/eosat1/mcs/role_analysis/propulsion_role.md`.
- **State (`prop.state` 0x0B00; 0 SAFED, 1 ARMED, 2 FIRING,
  3 INHIBIT):** ____
- **Tank pressure (`prop.tank_pressure` 0x0B01, bar):** ______
  **Propellant (`prop.propellant_mass` 0x0B02, g):** ______ / 400
- **Arm interlock mask (`prop.arm_inhibit_mask` 0x0B15):** ______
  **Bits set** (b0 catbed, b1 tank P, b2 propellant, b3 AOCS mode,
  b4 att err, b5 SoC, b6 phase, b7 eclipse, b8 valves, b9 inhibit
  latched, b10 no burn loaded): ______________________
- **Gate blocking the arm, in words:** ______________________
- **Insight:** _________________________________________________
- **Question to ask:** _________________________________________

---

# Worksheet WB-5.3-PP — Day 1 Pass-Plan Team Exercise

**Team:** ☐ Borealis  ☐ Austral   **Lead:** _______________

| Field | Entry |
|-------|-------|
| Target pass (station + AOS time) | |
| TCA time | |
| LOS time | |
| Pass duration (min) | |
| Procedures to run (IDs, in order) | |
| Imaging target ID | |
| Imaging window inside pass | |
| Bands selected and integration time | |
| Predicted ground swath (km) | |
| Downlink rate planned (kbps) | |
| Expected downlink duration (s) | |
| **Plausible failure 1** | |
| Recovery procedure for failure 1 | |
| **Plausible failure 2** | |
| Recovery procedure for failure 2 | |

### Read-aloud notes

What the other team challenged: ________________________________

___________________________________________________________________

What we accepted: _________________________________________________

What we defended: _________________________________________________

---

# Worksheet WB-5.4-VL — Day 2 Voice-Loop Callout Drill

**Use:** Tuesday 09:00 – 10:00. Pair drill. One plays FD, the
other plays the named subsystem. Record what was said.

| # | Scenario | Your callout (verbatim) | Pass/Fail |
|---|----------|------------------------|-----------|
| 1 | FD asks AOCS for pointing report | | ☐ ☐ |
| 2 | AOCS reports pointing 0.28°, nominal | | ☐ ☐ |
| 3 | FD asks EPS for eclipse-entry predictor | | ☐ ☐ |
| 4 | EPS reports eclipse entry T+04:12, SoC at exit 78% | | ☐ ☐ |
| 5 | FD polls 3 positions for GO on payload power-on | | ☐ ☐ |
| 6 | EPS responds: "no-go, payload line 3 already drawing 0.35 A with the line commanded OFF" | | ☐ ☐ |
| 7 | FD calls HOLD on payload power-on | | ☐ ☐ |
| 8 | TT&C calls anomaly: BER climbed to 1e-3 | | ☐ ☐ |
| 9 | FD requests rate fallback | | ☐ ☐ |
| 10 | TT&C reports tier stepped down HIGH→LOW, rate 16 kbps, BER 1e-7 nominal | | ☐ ☐ |

**Self-score (out of 10):** ______

**One callout I want to practice more:** ____________________

---

# Worksheet WB-5.4-N001 — NOM-001 Pass Startup (confirm each step)

**Use:** Tuesday afternoon dry-run, every nominal pass thereafter.

**Operator:** ___________________   **Pass:** ___________________

| # | Owner | Action | Expected verification | ☐ done | Note / actual value |
|---|-------|--------|----------------------|:------:|---------------------|
| 1 | SPACON | Verify OBC status: `HK_REQUEST(sid=4)` (S3.27) | `obdh.mode` (0x0300) = 0 (NOMINAL) and `obdh.cpu_load` (0x0302) < 80 % within 10 s; `obdh.uptime` (0x0308) consistent with the last known value. `obdh.mode` ≠ 0: abort the pass, run CTG-010 | ☐ | |
| 2 | EPS | Verify EPS health: `HK_REQUEST(sid=1)` | `eps.bat_soc` (0x0101) > 50 %; `eps.bus_voltage` (0x0105) > 27.0 V; `eps.power_gen` (0x0107) > `eps.power_cons` (0x0106). Either limit missed: CTG-005, no payload operations | ☐ | |
| 3 | AOCS | Verify AOCS pointing: `HK_REQUEST(sid=2)` | `aocs.mode` (0x020F) in {4, 8} (NOMINAL, or ECLIPSE on the shadow side); `aocs.att_error` (0x0217) < 1.0° (allow 400 s to re-converge after a disturbance); `aocs.rate_roll` (0x0204) and `aocs.rate_yaw` (0x0206) within ±0.05°/s; `aocs.rate_pitch` (0x0205) in [0.043, 0.083]°/s — nadir tracking carries the orbit rate, +0.063°/s | ☐ | |
| 4 | TT&C | Establish the link: `TTC_SWITCH_PRIMARY` (S8.1) | `ttc.link_status` (0x0501) = **2** (LOCKED) within 15 s; TT&C page (ground): `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB. No link in 15 s: `TTC_SWITCH_REDUNDANT` and verify again; both fail → TT&C anomaly | ☐ | |
| 5 | SPACON | Full housekeeping collection: `HK_REQUEST` (S3.27) of SIDs 1 EPS, 2 AOCS, 3 TCS, 4 OBDH, 5 Payload, 6 TT&C | all six packets within 30 s; no out-of-limit parameter flagged by the MCS limit checker | ☐ | |
| 6 | Payload | Payload preparation, only if imaging or a downlink is planned: `PAYLOAD_SET_MODE(mode=1)` STANDBY (S8.1 func 26) | `payload.mode` (0x0600) = 1 within 20 s; `tcs.cooler_fpa` (0x040C) = 0 (STANDBY does not run the cooler; it is switched on as the imaging preparation, NOM-002 step 2); `payload.store_used` (0x0604) < 90 % | ☐ | not planned ☐ |
| 7 | FD | Pass readiness declaration: poll each position GO / NO-GO | EPS: SoC > 50 %, bus > 27 V, margin positive · AOCS: NOMINAL, error < 1°, rates < 0.05°/s · TT&C: link up, RSSI > −100 dBm, margin > 3 dB · TCS: every zone inside the limits on the TCS page · OBDH: NOMINAL, CPU < 80 % · Payload: STANDBY if needed, store < 90 %. Any NO-GO: its off-nominal procedure first | ☐ | |

On-demand reads are `HK_REQUEST` (S3.27); periodic reporting is switched on with
`HK_ENABLE` (S3.5). Only SIDs 1 (EPS) and 11 (beacon) are enabled at boot; the
others are enabled by the cards that power their subsystems.

No link at step 4 although the ground is nominal: the S-band chain only radiates
when `ttc.tx_active` (0x0525) = 1, and `ttc.tx_gate_status` (0x052B) names the
missing permission — that is CTG-019, not this card.

**Off-nominal items observed:** __________________________________

___________________________________________________________________

**FD signature:** ________________   **Time complete:** _________

---

# Worksheet WB-5.4-C003 — CTG-003 TTC Link Loss Recovery (confirm each step)

**Operator:** ___________________   **Trigger time:** _________

Link loss is confirmed when `ttc.link_status` = 0 for more than 30 s after the
predicted AOS, or when an established link drops mid-pass. Every command after
step 1 is sent **blind**: no telemetry is expected until the link returns.

| # | Owner | Action | Expected verification | ☐ done | Note / actual value |
|---|-------|--------|----------------------|:------:|---------------------|
| 1 | Ground Seg | Confirm the link loss is not a ground issue: antenna tracking, uplink transmitter power, receiver lock, Doppler pre-compensation, local RFI or weather | ground fault → resolve locally; ground confirmed nominal → spacecraft-side recovery | ☐ | |
| 2 | TT&C | Re-acquire on the primary transponder: blind `HK_REQUEST(sid=6)` (S3.27), wait 30 s | `ttc.link_status` (0x0501) = **2** (LOCKED) within 30 s; TT&C page (ground): `ttc.rssi` (0x0502) > −126 dBm. Link back → step 5; no response → step 3 | ☐ | |
| 3 | TT&C | Switch to the redundant transponder: blind `TTC_SWITCH_REDUNDANT` (S8.1 func 64), wait 45 s | `ttc.link_status` = 2 within 45 s; `ttc.mode` (0x0500) shows the redundant unit. Link back → step 5; none → step 4 | ☐ | |
| 4 | TT&C | Second attempt on the primary: blind `TTC_SWITCH_PRIMARY` (S8.1 func 63), wait 45 s | `ttc.link_status` = 2 within 45 s. Link back → step 5; still none after both units → step 6 | ☐ | |
| 5 | TT&C | Verify link quality and subsystem health: `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `ttc.link_status` = 2; TT&C page (ground): `ttc.rssi` > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB; active unit `ttc.mode` (0x0500) recorded; `eps.bus_voltage` (0x0105) > 27.0 V; `obdh.mode` (0x0300) not SAFE or EMERGENCY. Margin > 3 dB and all nominal → recovered | ☐ | unit: ____ |
| 6 | TT&C | Escalation, no link: log every blind command with its time; notify the Mission Director and Flight Dynamics; book the next pass; record the time of the last **accepted** telecommand (last S1.1) | first passes planned after T+24 h and T+48 h: the command-loss timer `ttc.time_since_last_tc` (0x053D, FDIR TTC-01) switches to the OTHER transponder 24 h after the last accepted TC (event CMD_LOSS_TIMEOUT 0x0514) and again every further 24 h. No link after two consecutive passes → **EMG-004** | ☐ | last S1.1: ____ |

Blind commands that are not received do not restart the command-loss timer.
When the link returns, send a telecommand at once, or the timer switches away
from the working unit 24 h later. With both transponders failed the link is
really cut — no telecommand is received and nothing is transmitted, beacon
included — and nothing from the ground can recover it: escalate to EMG-004 and
keep listening.

**Step at which link was recovered (if any):** ______

**Anomaly ticket number:** ______

**FD signature:** ________________   **Time complete:** _________

---

# Worksheet WB-5.4-N012 — NOM-012 Shift Handover Template

**Use:** every shift change. Outgoing FD reads each row; incoming
FD reads back items 3 and 7. Target: under 6 minutes.

**Outgoing FD:** _____________   **Incoming FD:** _____________
**Shift end:** _______________   **Handover start:** _________

| # | Item | Outgoing FD says | Incoming FD reads back? |
|---|------|------------------|:----------------------:|
| 1 | Phase and time | | |
| 2 | Last completed pass | | |
| 3 | **Open anomalies** (rule name, status, recovery procedure step) | | ☐ |
| 4 | Open work items (procedures in progress) | | |
| 5 | Next pass (station, AOS, planned procedures, operator-of-record) | | |
| 6 | Customer commitments active | | |
| 7 | **GO authorisations outstanding** | | ☐ |
| 8 | Voice-loop tone (team rested / tense / etc.) | | |

**Handover end:** _________   **Duration:** ____ : ____ (target < 6:00)

**Both FDs sign below to acknowledge handover complete.**

Outgoing: ____________________  Incoming: ____________________

---

# Worksheet WB-5.4-FD — Day 2 Flight-Dynamics Workshop

**Operator:** ___________________

### Exercise 1 — Predict next three AOS times

Tool: the Orbit Tools page (`python3 tools/orbit_tools.py --serve`, port 8093):
load the current TLE and read the pass list and 24 h contact timeline. Compare
to MPS contact schedule.

| Pass | Station | AOS (your prediction, UTC) | AOS (MPS, UTC) | Δ (s) |
|------|---------|---------------------------|----------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

### Exercise 2 — Pass duration vs max elevation

| Pass | Max el (°) | Predicted duration (min) | Actual duration from MPS (min) |
|------|------------|---------------------------|-------------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

Formula used (write here): _____________________________________

### Exercise 3 — Eclipse arithmetic

- **Longest eclipse in next 24 h:** ____________ UTC, duration ____ min
- **Predicted SoC at exit** (using $SoC_{exit} = SoC_{entry} - P_{avg} \cdot t / E_{battery}$):
  ____ %
- **Actual SoC at exit:** ____ %   **Δ:** ____ %
- **Concern?** ☐ no  ☐ yes — note: _____________________________

---

# Worksheet WB-5.4-Q — Day 2 Operations Training Quiz Response Sheet

**Name:** ___________________   **Time started:** _____________

Pass mark: 11 of 15. Solutions on the back of the instructor pack.

### Voice-loop discipline (3 Qs)

1. ____________________________________________________________
2. ____________________________________________________________
3. ____________________________________________________________

### MCS UI navigation (3 Qs)

4. ____________________________________________________________
5. ____________________________________________________________
6. ____________________________________________________________

### Telemetry interpretation — limits and SIDs (3 Qs)

7. ____________________________________________________________
8. ____________________________________________________________
9. ____________________________________________________________

### Procedure structure (2 Qs)

10. ____________________________________________________________
11. ____________________________________________________________

### Anomaly response (2 Qs)

12. ____________________________________________________________
13. ____________________________________________________________

### Pass timing arithmetic (2 Qs)

14. ____________________________________________________________
15. ____________________________________________________________

**Self-mark when graded:** ____ / 15   **Pass?** ☐ yes ☐ no

---

# Worksheet WB-5.5-PB — Day 3 LEOP Pre-Pass Briefing Checklist

**Team:** ☐ Borealis ☐ Austral   **Pass:** ☐ Pass 1 ☐ Pass 2

| Item | ☐ |
|------|:--:|
| Position assignments confirmed and posted | ☐ |
| Comm check completed (all positions readable) | ☐ |
| BP-2 (`first_contact.yaml`) loaded; spacecraft in phase 3 (BOOTLOADER) | ☐ |
| A real Iqaluit pass is scheduled for first contact (pass override is an instructor control; no operator forces contact) | ☐ |
| FD has loaded LEOP procedure pack into procedure panel | ☐ |
| SPACON has reviewed the FDIR rule set on the FDIR panel (there is **no** FDIR table-load telecommand — the rule set is `subsystems/fdir.yaml` + `monitoring/`) | ☐ |
| AOCS has reviewed residual tumble rates (~1–2 °/s per axis from the separation impulse) | ☐ |
| EPS confirms SoC ~90 % (`eps.bat_soc` 0x0101); only the non-switchable `obc` (line 0) and `ttc_rx` (line 1) are ON — every switchable line defaults OFF | ☐ |
| TT&C has confirmed UHF beacon reception (`ttc.beacon_active` 0x0527 = 1); note the beacon is a separate radio from the S-band prime | ☐ |
| Ground Seg has confirmed Iqaluit antenna on-target, demodulator on the **SAFE** rung (1 000 bps, BPSK, conv(7,1/2)+RS, 1 kBd) | ☐ |
| FDS has produced 24-h pass schedule and handed to FD/TT&C/Ground Seg | ☐ |
| Anomaly ticket forms blank-printed and available at each console | ☐ |
| Voice-loop language declared (callouts in English) | ☐ |

**FD ready call (verbatim):** ________________________________

**Pass start (UTC):** _____________

---

# Worksheet WB-5.5-L001 — LEOP-001 First Acquisition of Signal & OBC Boot (confirm each step)

**Operator (TT&C lead):** ___________________   **Pass start:** ________

Entry state: cold boot — OBC in the bootloader, only the `obc` and `ttc_rx`
lines on, clock unset. The pass is a **scheduled** one: pass override is an
instructor control, and no card asks an operator to force contact.

| # | Owner | Action | Expected verification | ☐ done | Actual note |
|---|-------|--------|----------------------|:------:|-------------|
| 1 | Ground Seg | Configure the Iqaluit receiver for the scheduled pass: point at the predicted AOS, auto-track, wide acquisition (±40 kHz), demodulator on the **SAFE** rung (1 kBd BPSK, conv(7,1/2)+RS) | station TRACKING_READY at the predicted AOS; pass window open | ☐ | |
| 2 | TT&C | First uplink, sent blind into the window: `CONNECTION_TEST` (S17.1) | S1.1 acceptance < 10 s; S17.2 report < 10 s; beacon SID 11 arriving < 30 s — the auto-TX hold-down has powered the `ttc_tx` line | ☐ | |
| 3 | TT&C | Verify carrier lock and link quality | beacon frames decode continuously < 30 s; TT&C page (ground): `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB. `ttc.link_status` is in SID 6, which the bootloader does not emit: it is checked at step 5a | ☐ | Doppler: ____ |
| 4 | SPACON | Confirm the bootloader: `HK_REQUEST(sid=11)` (S3.27) | beacon packet received; `obdh.sw_image` (0x0311) = 0 (BOOTLOADER) < 10 s | ☐ | |
| 5 | SPACON | Boot the application: `OBC_BOOT_APP` (S8.1 func 55); after its S1.7, `HK_ENABLE(sid=3)`, `HK_ENABLE(sid=4)`, `HK_ENABLE(sid=6)` (**S3.5**) | S1.1 + S1.3 < 5 s; S1.7 < 15 s (event 0x0310 BOOT_COMPLETE; a CRC failure gives S1.8 and 0x0305 BOOT_FAILURE); `obdh.sw_image` = 1 < 15 s; `obdh.boot_state` (0x0A15) = 2; only SIDs 1 and 11 stream after the boot, then SIDs 3 (60 s), 4 (8 s), 6 (8 s) appear | ☐ | |
| 5a | TT&C | Clear beacon mode, then select LOW: `TTC_SET_BEACON_MODE(on=0)` (S8.1 func 70), `TTC_SET_DATA_RATE(rate=0)` (func 65). Re-configure the ground demodulator to 16 kBd first | S1.1 + S1.7, not S1.8, < 5 s each; `ttc.beacon_mode` (0x0521) = 0; `ttc.link_status` (0x0501) = **2** (LOCKED) < 15 s; `ttc.tm_data_rate` (0x0506) = 16000 bps, `ttc.tm_tier` (0x0539) = 1, `ttc.tm_symbol_rate` (0x053B) = 16000 Bd | ☐ | |
| 6 | SPACON | Note the unset clock — **do not sync here**: time is LEOP-006's job | `obdh.time_ref` (0x0A13) = 0 (NONE); timestamps read year-2000 CUC — correct behaviour, not a fault | ☐ | |
| 7 | SPACON | Power sanity check: `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) 26.0–30.0 V; `eps.bat_soc` (0x0101) > 50 %; `eps.pl_ttc_tx` (0x0112) = 1 (auto-TX hold-down); `eps.power_gen` (0x0107) reported, small while tumbling | ☐ | |
| 8 | TT&C | Log and report: AOS, first accepted TC, application boot, HK values; confirm the pass is long enough for LEOP-002 or book the next one | First Acquisition Report distributed; clear to LEOP-002 | ☐ | |

**Recorded values:**
- AOS time (UTC): ____________
- First accepted TC: ____________
- App boot complete: ____________
- `obdh.time_ref` (expect 0): ____
- `eps.bus_voltage`: ____ V    `eps.bat_soc`: ____ %

**Common mistakes to avoid (instructor recap):**
- Sending a telecommand outside the bootloader allow-list before the
  application has booted (S1.8 failure code **0x0006**, "Not permitted in
  bootloader"). Inside the CRC window the OBC is still the bootloader: wait
  for the S1.7 of `OBC_BOOT_APP`.
- Synchronising the clock in this card. `SET_TIME` belongs to LEOP-006.
- Letting the auto-TX hold-down (`auto_tx_hold_s` in `simulation.yaml`,
  re-armed by every accepted TC) expire mid-procedure.
- Trying `TTC_SET_DATA_RATE` before clearing beacon mode — refused with
  0x0007; application boot does **not** clear it.
- Expecting SIDs 2 and 5 after step 5 (SID 2 is enabled in LEOP-007 and SID 5
  in COM-009, once their lines are powered), or any SID other than 1 and 11
  without an explicit `HK_ENABLE` (S3.5).

**Exit criterion met?** ☐ yes ☐ no   **FD signature:** _______________

---

# Worksheet WB-5.5-L006 — LEOP-006 Time Synchronisation (confirm each step)

**Operator (SPACON):** ___________________

| # | Action | Expected verification | ☐ done | Note |
|---|--------|----------------------|:------:|------|
| 1 | Verify OBC status and the link: `HK_REQUEST(sid=4)`, `HK_REQUEST(sid=6)` (S3.27) | `obdh.mode` (0x0300) ≤ 1 (NOMINAL or SAFE); `obdh.cpu_load` (0x0302) < 80 %; TT&C page (ground): `ttc.link_margin` (0x0503) > 3.0 dB | ☐ | |
| 2 | Read the clock, its reference and the slant range: `REQUEST_TIME` (**S9.2**), `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=4)` | TM(9,2) < 10 s. T_obc = `obdh.obc_time` (0x0309) + `obdh.obc_time_fine` (0x0A12) / 65536, CUC seconds since J2000; `obdh.time_ref` (0x0A13), expect 0 (NONE); `obdh.time_since_sync_s` (0x0A14), expect 4294967295 (never synced); T_ground; OWLT = `ttc.range_km` (0x0509) / 299792.458 × 1000 ms, expect **3–22 ms** | ☐ | OWLT: ____ ms |
| 3 | Calculate the time delta: Δt = T_obc − (T_ground − OWLT) | a negative Δt of roughly the mission age is the expected LEOP signature; the FD approves the correction | ☐ | Δt: ____ s |
| 4 | Send the time update: `SET_TIME(cuc_seconds=T_corrected)` (**S9.1**), with T_corrected = T_ground at send + OWLT + about 50 ms, on the J2000 epoch — a Unix time is about 9.5e8 s too large, and the argument goes *inside* the backticks: a bare `SET_TIME` sends cuc_seconds = 0 | S1.1 < 5 s; no S1.2 rejection | ☐ | T_corrected: ____ |
| 5 | Verify the time accuracy: `REQUEST_TIME` (S9.2), `HK_REQUEST(sid=4)` | `obdh.time_ref` = 1 (GROUND) < 15 s; `obdh.mode` = 0 < 10 s; residual = T_obc_new − (T_ground − OWLT) within ±1.0 s (LEOP threshold; NOM-008 tightens it) | ☐ | residual: ____ s |
| 6 | Validate the clock rate: a second time report (S9.2) and SID 4 sample after a known ground interval | report < 10 s; drift = ((T_obc2 − T_obc1) − (T_gnd2 − T_gnd1)) / interval × 1e6 < 100 ppm | ☐ | ____ ppm |
| 6a | Path B, GPS time discipline, once the receiver has a fix: `HK_ENABLE(sid=12)` (S3.5), then `OBC_GPS_TIME_SYNC` (S8.1 func **80**) — ground set first, GPS second | SID 12 periodic within 8 s; `aocs.gps_fix` (0x0274) ≥ 2 (TTFF up to 15 min from LEOP-007; no fix yet → sync on the next contact); S1.1 + S1.7 < 5 s; `obdh.time_ref` = 2 (GPS) < 15 s, 3 (HOLDOVER) acceptable; `obdh.time_since_sync_s` small | ☐ | |
| 7 | Confirm time-stamping and log: `HK_REQUEST(sid=4)` | `obdh.uptime` (0x0308) > 0 (no reboot); `obdh.time_ref` in {1, 2, 3}; HK packets carry mission-date timestamps. Log Δt, the jump in event 0x030C, the residual and the drift | ☐ | |

**Exit criterion met?** ☐ yes ☐ no

---

# Worksheet WB-5.5-L002 — LEOP-002 Initial Health Check (confirm each step)

**Operator (SPACON consolidates):**  ___________________

| # | Owner | Action | Expected verification | ☐ done | Note |
|---|-------|--------|----------------------|:------:|------|
| 1 | EPS | Full EPS housekeeping: `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) 26.0–30.0 V; `eps.bat_voltage` (0x0100) reported; `eps.bat_soc` (0x0101) > 50 %; `eps.power_gen` (0x0107) > 0 W in sunlight — 0 W is expected with `eps.eclipse_flag` (0x0108) = 1: re-check after eclipse exit | ☐ | ☐ OK ☐ NOT-OK |
| 2 | EPS | Confirm the unpowered subsystems are dark (same SID 1 report) | `eps.pl_aocs_wheels` (0x0117) = 0 (until LEOP-007); `eps.pl_payload` (0x0113) = 0 (until COM-009); `eps.pl_fpa_cooler` (0x0114) = 0 (until COM-010); `eps.pl_prop` (0x014A) = 0 | ☐ | ☐ dark ☐ powered early |
| 3 | Thermal | Thermal housekeeping: `HK_REQUEST(sid=3)` | `tcs.temp_obc` (0x0406) inside the OBC limits on the TCS page; `tcs.temp_battery` (0x0407) 0 to +35 °C; `tcs.temp_fpa` (0x0408) reported (payload unpowered: ambient) | ☐ | ☐ OK ☐ NOT-OK |
| 4 | SPACON | OBDH housekeeping: `HK_REQUEST(sid=4)` | `obdh.mode` (0x0300) = 0 (NOMINAL) or 1 (SAFE); `obdh.cpu_load` (0x0302) < 70 % | ☐ | ☐ OK ☐ NOT-OK |
| 5 | TT&C | TT&C housekeeping: `HK_REQUEST(sid=6)` | `ttc.link_status` (0x0501) = **2** (LOCKED); TT&C page (ground): `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB | ☐ | ☐ OK ☐ NOT-OK |
| 6 | SPACON | Compile the health assessment summary for the FD; flag any value outside its post-separation range | all powered subsystems nominal → clear to LEOP-004 | ☐ | |

**Consolidated PASS / FAIL:** ☐ PASS ☐ FAIL

**If FAIL, which contingency procedure invoked:** _________________

**Exit criterion met?** ☐ yes ☐ no

---

# Worksheet WB-5.5-L007 — LEOP-007 Sequential Power-On (confirm each step)

**Operator (SPACON lead):**  ___________________

LEOP-007 powers only what the rest of LEOP needs — heaters if their
zones need heat, the AOCS suite line, the magnetometer, magnetorquers
and GPS receiver — and commands DETUMBLE. Steps 1–6 fit one
8-minute contact. Each new line is a separate commanding event with
FD GO. The payload, the cooler, the wheels, the star trackers and
the gyros stay off: their commissioning cards bring them up.

**Power-line index map** (`EPS_POWER_ON` / `EPS_POWER_OFF` /
`EPS_RESET_OC_FLAG` all take `line_index`, range **0–8**):
0 `obc`, 1 `ttc_rx` (both non-switchable), 2 `ttc_tx`, 3 `payload`,
4 `fpa_cooler`, 5 `htr_bat`, 6 `htr_obc`, 7 `aocs_wheels`, 8 `prop`.
Every switchable line defaults **OFF**. There is no IMU power line —
the three gyros are S2 devices `S2_AOCS_GYROSCOPE_0/1/2`.

| # | Owner | Action | Verification | ☐ done | Note |
|---|-------|--------|--------------|:------:|------|
| 1 | EPS | Verify the EPS baseline: `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) 26.0–30.0 V; `eps.bat_soc` (0x0101) > 60 %; `eps.power_gen` (0x0107) > 20 W | ☐ | |
| 2 | EPS | Heater lines **only as needed**: read `tcs.temp_battery` (0x0407) and `tcs.temp_obc` (0x0406) from SID 3; `EPS_POWER_ON(line_index=5)` (S8.1 func **19**) only if the battery is below +5 °C; `EPS_POWER_ON(line_index=6)` only if the OBC zone is below 0 °C | `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc` (0x0116) = 1 within 5 s for each line commanded; the others still off. Log which lines this card energised: COM-002 reads it as its entry state | ☐ | lines energised: ____ |
| 3 | EPS / AOCS | Energise the AOCS suite line and enable its HK: `EPS_POWER_ON(line_index=7)` (func 19), then `HK_ENABLE(sid=2)` (**S3.5**) | `eps.pl_aocs_wheels` (0x0117) = 1 within 5 s; SID 2 periodic within one 4 s interval; the wheels stay disabled until COM-004 | ☐ | |
| 4 | AOCS | Both DETUMBLE legs first, and the GPS receiver: `S2_AOCS_MAGNETOMETER(device_id=521, state=1)`, `MTQ_ENABLE(enable=1)` (S8.1 func_id **9**), `S2_AOCS_GPS_RECEIVER(device_id=527, state=1)` | `aocs.mtq_enabled` (0x025E) = 1 within 10 s | ☐ | |
| 5 | AOCS | Command DETUMBLE: `AOCS_SET_MODE(mode=2)` (S8.1 func_id **0**) — mode **2 = DETUMBLE** | S1.1 + S1.7 < 5 s; `aocs.mode` (0x020F) = 2; `aocs.mag_enabled` (0x025C) = 1; `aocs.mag_field_total` (0x0277) 5000–70000 nT; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` (0x0204–0x0206) trending down within 60 s | ☐ | |
| 6 | EPS | Confirm the exit power state: `HK_REQUEST(sid=1)`, `GET_PARAM(param_id=0x0260)` (S20.3) | `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_prop` (0x014A) = 0; `aocs.wheels_enabled` (0x0260) = 0; margin positive — `eps.power_gen` (0x0107) above `eps.power_cons` (0x0106), or SoC stable or rising | ☐ | |

The DETUMBLE command is refused if a leg is missing (0x0A20 no magnetometer,
0x0A21 no magnetorquers, 0x0004 line off): that is why step 4 comes first.

**End-of-pass state:**
- Phase (0x0129): ____ (expect 4 LEOP)   AOCS mode (0x020F): ____ (expect 2 DETUMBLE)
- Body rates roll/pitch/yaw (°/s): __/__/__ (decreasing)
- Wheels enabled (`aocs.wheels_enabled` 0x0260): ____ (expect 0)
- SoC: ____ %   `tcs.temp_battery`: ____ °C
- SIDs periodic: 1 ☐ 2 ☐ 3 ☐ 4 ☐ 6 ☐ 11 ☐

**Exit criterion met?** ☐ yes ☐ no   **FD signature:** _______________

---

# Worksheet WB-5.5-L005 — LEOP-005 Sun Acquisition (observe, confirm each step)

**Operator (AOCS):**  ___________________

This card commands **no** mode change: the handover from DETUMBLE to
COARSE_SUN is automatic.

| # | Action | Verification | ☐ done | Note |
|---|--------|--------------|:------:|------|
| 1 | Record the initial body rates: `HK_REQUEST(sid=2)` (S3.27) | `aocs.mode` (0x020F) = 2 (DETUMBLE); `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) recorded — 0.5 to 5.0°/s per axis is typical | ☐ | __/__/__ °/s |
| 2 | Monitor rate damping — command nothing: `HK_REQUEST(sid=2)` again at T+5 min | all three rates decreasing (B-dot roughly halves them every 10–15 min); `aocs.mag_field_total` (0x0277) non-zero — zero means the magnetometer dropped out and B-dot is blind | ☐ | |
| 3 | Observe the **automatic** transition to COARSE_SUN: body rates below 0.5°/s for 30 s → the AOCS hands itself over. Send no mode command | `aocs.mode` (0x020F) = 3 (COARSE_SUN) within 1800 s of the rates falling below 0.5°/s; event "AOCS mode change" DETUMBLE → COARSE_SUN in the event log | ☐ | time: ____ |
| 4 | Verify the sun hold: `HK_REQUEST(sid=2)` every 60 s for 5 min, `GET_PARAM(param_id=0x0215)` (S20.3) | `aocs.att_error` (0x0217) < 15° within 600 s; `aocs.css_sun_confidence` (0x0215) > 0.5; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` < 0.5°/s | ☐ | error: ____ ° |
| 5 | Verify power generation in the hold: `HK_REQUEST(sid=1)` | `eps.power_gen` (0x0107) > 40 W in sunlight — with `eps.eclipse_flag` (0x0108) = 1, wait for eclipse exit (up to 35 min) and re-check; `eps.bat_soc` (0x0101) stable or rising | ☐ | ____ W |
| 6 | Log the final AOCS state: rates, attitude error, CSS confidence, power. The spacecraft **stays** in COARSE_SUN: with no star tracker powered (COM-003) the automatic promotion cannot fire — the intended LEOP parking state | Sun Acquisition Report issued | ☐ | |

The B-dot convergence is **slow**: the 0.5°/s guard typically takes about
1 200 s, and a full 14°/s separation tumble about 3.5e3 s.

**Exit criterion met?** ☐ yes ☐ no

---

# Worksheet WB-5.5-L003 — LEOP-003 Initial Orbit Determination and End of LEOP (confirm each step)

**Operator (FDS, with the FD for step 7):**  ___________________

| # | Action | Verification | ☐ done | Note |
|---|--------|--------------|:------:|------|
| 1 | Verify the GPS navigation solution: `HK_REQUEST(sid=12)` (S3.27) | `aocs.gps_fix` (0x0274) ≥ 2 (3D); `aocs.gps_num_sats` (0x0276) ≥ 4; `aocs.gps_pdop` (0x0275) recorded | ☐ | PDOP: ____ |
| 2 | Read the position fix: `GET_PARAM(param_id=0x0210)`, `GET_PARAM(param_id=0x0211)`, `GET_PARAM(param_id=0x0212)` (S20.3) | `aocs.gps_lat` (0x0210) in [−90, +90]°; `aocs.gps_lon` (0x0211) in [−180, +180]°; `aocs.gps_alt` (0x0212) in the 495–540 km check band | ☐ | alt: ____ km |
| 3 | Read the ECEF state vector: `GET_PARAM(param_id=0x0231)` … `GET_PARAM(param_id=0x0236)` | position magnitude 6700–6950 km; velocity magnitude 7400–7900 m/s; vector and its GPS time recorded for Flight Dynamics | ☐ | |
| 4 | Flight Dynamics comparison with the launcher-predicted orbit — **nothing is uploaded to the spacecraft** | i within 0.2° of 97.39°; e < 0.01; LTAN within 15 min of the mission requirement; period agrees with the TLE mean motion | ☐ | i: ____ ° |
| 5 | Second fix consistency check, 10 min later: `HK_REQUEST(sid=12)` | `aocs.gps_alt` (0x0212) within 20 km of step 2; `aocs.gps_fix` (0x0274) still ≥ 2; the position moved along-track as propagated | ☐ | |
| 6 | Distribute the Orbit Determination Report and the refined TLE to the ground network (planner, FDS, stations) | pass predictions refreshed | ☐ | |
| 7 | FD: GO/NO-GO poll of all positions, then **declare COMMISSIONING by telecommand**: `SYS_SET_MISSION_PHASE(phase=5, flags=0)` (S8.1 func **120**) — the only card that sends it; nothing on board advances the phase past 4 | `eps.spacecraft_phase` (0x0129) = 5 within 5 s; event MISSION_PHASE_CHANGED (0x0055) 4 (LEOP) → 5 (COMMISSIONING) | ☐ | |

**Exit criterion met?** ☐ yes ☐ no   **FD signature:** _______________

---

# Worksheet WB-5.5-AT — Day 3 Anomaly Ticket (3 copies)

Print three. Use one per anomaly observed (planned injections or
unplanned). Each ticket signed by FD.

### Ticket — copy 1

| Field | Entry |
|-------|-------|
| Ticket ID (auto-assigned) | |
| Pass / shift | |
| Date / UTC time of first indicator | |
| Triggering parameter and value | |
| FDIR rule that fired (if any) | |
| Severity (0–4) | |
| First operator to call it (position) | |
| First-action time | |
| Procedure invoked (ID) | |
| Recovery actions taken (verbatim from loop) | |
| Outcome (recovered / safe / deferred) | |
| Root cause hypothesis | |
| Open items for next shift | |
| FD signature | |

### Ticket — copy 2

| Field | Entry |
|-------|-------|
| Ticket ID | |
| Pass / shift | |
| Date / UTC time | |
| Parameter and value | |
| FDIR rule | |
| Severity | |
| First operator | |
| First-action time | |
| Procedure invoked | |
| Actions taken | |
| Outcome | |
| Root cause hypothesis | |
| Open items | |
| FD signature | |

### Ticket — copy 3

| Field | Entry |
|-------|-------|
| Ticket ID | |
| Pass / shift | |
| Date / UTC time | |
| Parameter and value | |
| FDIR rule | |
| Severity | |
| First operator | |
| First-action time | |
| Procedure invoked | |
| Actions taken | |
| Outcome | |
| Root cause hypothesis | |
| Open items | |
| FD signature | |

---

# Worksheet WB-5.5-GO — Day 3 End-of-Pass GO/NO-GO Scorecard

**Assessor:** ______________   **Pass:** ☐ Pass 1 (Team A) ☐ Pass 2 (Team B)

| Criterion | ☐ achieved |
|-----------|:----------:|
| OBC application SW running (`obdh.sw_image` 0x0311 = 1) | ☐ |
| Onboard time set, residual < 1.0 s | ☐ |
| Beacon mode cleared, downlink on LOW (`ttc.tm_tier` 0x0539 = 1) | ☐ |
| Antenna still stowed, `ttc.antenna_deployed` (0x0520) = 0 — COM-006 deploys it; LOW needs no deployment | ☐ |
| Heater lines energised only where their zone needed heat, and logged (LEOP-007 step 2) | ☐ |
| AOCS wheels line ON, AOCS through DETUMBLE (2) into COARSE_SUN (3) | ☐ |
| Body rates < 0.5°/s on all axes; `aocs.att_error` < 15° in the COARSE_SUN hold | ☐ |
| Anomaly ticket filed for any injection | ☐ |
| Phase advanced to COMMISSIONING (5) with `SYS_SET_MISSION_PHASE` (func 120) (Pass 2 only) | ☐ |

**Score:** ____ / 9 (Pass 1) or ____ / 9 (Pass 2)

**Notes for debrief:** _________________________________________

---

# Worksheet WB-5.5-OBS — Day 3 Observer Worksheets (axes used: Communications + Technical)

(Print both. Each observer fills one per pass they observe.)

### Observer worksheet — Communications axis

**Observer:** _____________  **Pass observed:** _____________

| Item | Note (timestamp + what + who) |
|------|-------------------------------|
| Voice-loop discipline (callouts, hot-mike) | |
| GO/NO-GO protocol followed | |
| Cross-talk incidents (count + timestamps) | |
| MCS chat — used for what? | |
| Handover: timing, content, completeness | |
| Silent confusion (operator did wrong thing because no one said anything)? | |

**Worked well:** _________________________________________________

**Could improve:** ______________________________________________

**Specific recommendation:** _____________________________________

### Observer worksheet — Technical axis

**Observer:** _____________  **Pass observed:** _____________

| Item | Note |
|------|------|
| Procedure adherence — any skipped or out-of-order steps? | |
| Anomaly detection time — first indicator to first action | |
| Telemetry interpretation — any misreads? | |
| Command discipline — any unauthorised commands? | |
| Use of FDIR panel — did anyone watch it? | |
| Outcome vs pass criteria | |

**Worked well:** _________________________________________________

**Could improve:** ______________________________________________

**Specific recommendation:** _____________________________________

---

# Worksheet WB-5.5-HO — Day 3 Inter-Pass Handover Turnover Form

**Use:** between Pass 1 and Pass 2 (Team A → Team B). One per
position; outgoing operator signs, incoming operator signs.

Print 9 copies (one per console position).

### Handover — Position: ______________________

| Field | Entry |
|-------|-------|
| Outgoing operator | |
| Incoming operator | |
| Current parameter values (top 3 mnemonics) | |
| Current procedure state (file ID + step) | |
| Any pinned widget? | |
| Open question for next shift | |
| Outgoing signature | |
| Incoming signature | |
| Time | |

---

# Worksheet WB-5.5-DB — Day 3 Post-Shift Debrief Reflection

**Name:** _____________________

1. What is one decision you took during the shift that, in
   retrospect, you would not take again? Why?

   ___________________________________________________________
   ___________________________________________________________

2. What is one decision that surprised you with how well it
   worked?

   ___________________________________________________________
   ___________________________________________________________

3. Which voice callout did you most struggle to make in real
   time?

   ___________________________________________________________

4. What is one thing the team did better as a unit than you
   expected?

   ___________________________________________________________

5. What is one specific thing you will do differently tomorrow?

   ___________________________________________________________

---

# Worksheet WB-5.6-PB — Day 4 Commissioning Pre-Pass-Set Briefing

| Item | ☐ |
|------|:-:|
| BP-3 `commissioning_day_start.yaml` scenario loaded (instructor-authored — see the Instructor Book; it is not in the shipped `configs/eosat1/scenarios/` set) | ☐ |
| Spacecraft in phase 4 (LEOP), `eps.spacecraft_phase` (0x0129) = 4 — COMMISSIONING (5) is declared by LEOP-003 step 7 | ☐ |
| Position assignments posted (different team from yesterday) | ☐ |
| Pass-set timeline understood (4 sim passes in 2.5 h real time) | ☐ |
| All 13 commissioning procedures (COM-001…COM-013) loaded in the procedure index | ☐ |
| EPS confirms SoC ~90 %, `eps.pl_payload` (0x0113) = 0 | ☐ |
| Thermal confirms FPA at its uncooled equilibrium, `payload.fpa_temp` (0x0601) +8 to +14 °C | ☐ |
| Payload Ops has reviewed COM-009/-010/-011/-012 in detail | ☐ |
| First Light target candidate selected (FDS) | ☐ |
| Compressed-time speed multiplier set (instructor) | ☐ |

---

# Worksheet WB-5.6-C001 — COM-001 EPS Checkout (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Baseline bus voltage — `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) ∈ [27.0, 29.0] V (nominal regulation point 28.0 ± 0.5 V; a full battery sits near 29 V) | ☐ | V: ____ |
| 2 | Battery V & SoC — `GET_PARAM(param_id=0x0100)`, `GET_PARAM(param_id=0x0101)` (S20.3) | `eps.bat_voltage` (0x0100) ∈ [21.5, 29.2] V (8S pack, 100 Wh: 21.5 V empty, 26.4 V nominal, 29.2 V full); `eps.bat_soc` (0x0101) > 70 % | ☐ | V: ____ SoC: ____ |
| 3 | Solar array sunlit performance — `HK_REQUEST(sid=1)`, sunlit and sun-pointed | `eps.power_gen` (0x0107) ∈ [40, 90] W (88.6 W is the whole-spacecraft peak; about 80 W is normal when sun-pointed) | ☐ | ____ W |
| 4 | Eclipse discharge — `HK_REQUEST(sid=1)` at entry and at mid-eclipse | `eps.power_gen` ~0 W within 30 s of entry; `eps.bat_soc` falling < 1.5 %/min; `eps.bus_voltage` > 27.0 V | ☐ | |
| 5 | Eclipse-exit charge recovery — `HK_REQUEST(sid=1)` at exit + 5 min | `eps.power_gen` > 35 W within 60 s of exit; `eps.bat_soc` rising within 120 s | ☐ | |
| 6 | Power budget — `GET_PARAM(param_id=0x0108)`; orbit-average generation against consumption | orbit-average generation > consumption; end-of-eclipse SoC > 50 % under nominal load | ☐ | margin: ____ W |
| 7 | Bus regulation under a load transient — record `eps.pl_htr_bat` (0x0115) first, then `EPS_POWER_ON(line_index=5)` (S8.1 func_id **19**), and `EPS_POWER_OFF(line_index=5)` (func **20**) only if the line was off at entry. Not the payload: its line is OFF until COM-009 | `eps.bus_voltage` stays in [26.5, 29.5] V within 5 s and returns to [27.0, 29.0] V within 10 s; `eps.pl_htr_bat` back to its entry value | ☐ | min V: ____ |

Budget reference for step 6: the nominal orbit-average load is about **28.8 W**
against about 45.1 W of generation at the worst-generation beta, β = −31.2°
(margin +16.3 W, ratio 1.57; 1.38 while imaging), on the **100 Wh** pack.

**Exit?** ☐ yes ☐ no   **GO COM-002:** ☐

---

# Worksheet WB-5.6-C002 — COM-002 TCS Verification (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Thermal HK — `HK_REQUEST(sid=3)` (S3.27; SID 3 = TCS, 60 s cadence) | `tcs.temp_obc` (0x0406) inside the OBC limits on the TCS page; `tcs.temp_battery` (0x0407) ∈ [+5, +35] °C; `tcs.temp_fpa` (0x0408) reported — payload off and uncooled, +8 to +14 °C | ☐ | obc:__ bat:__ fpa:__ |
| 2 | Sunlit profile — `HK_REQUEST(sid=3)` every 120 s for 30 min | `tcs.temp_obc` stable or rising slower than 1 °C/min; `tcs.temp_battery` stable | ☐ | |
| 3 | Eclipse profile — `HK_REQUEST(sid=3)` at entry, mid-eclipse and exit | `tcs.temp_obc` above the OBC lower limit on the TCS page throughout; `tcs.temp_battery` > +5 °C throughout; drop rates recorded (OBC about 0.5 °C/min, battery buffered) | ☐ | |
| 4 | Battery heater circuit, line first: record `eps.pl_htr_bat` (0x0115); `EPS_POWER_ON(line_index=5)` (S8.1 func 19); `HEATER_BATTERY(on=1)`, then `HEATER_BATTERY(on=0)` (func **40**); `HEATER_AUTO_MODE(circuit=0)` (func **45**) | `eps.pl_htr_bat` = 1 within 5 s; ON and OFF acknowledged; `tcs.temp_battery` (0x0407) rising or stable over 3 min; the line **stays ON** under thermostat control (ON below +5 °C, OFF above +10 °C) | ☐ | entry: ____ |
| 5 | OBC heater circuit, line first: record `eps.pl_htr_obc` (0x0116); `EPS_POWER_ON(line_index=6)`; `HEATER_OBC(on=1)`, then `HEATER_OBC(on=0)` (func **41** — not 42, the thruster catbed heater); `HEATER_AUTO_MODE(circuit=1)` | `eps.pl_htr_obc` = 1 within 5 s; ON and OFF acknowledged; `tcs.temp_obc` (0x0406) stable or rising over 2 min; the line **stays ON** under its thermostat | ☐ | entry: ____ |
| 6 | Read the battery thermostat thresholds — `GET_PARAM(param_id=0x0410)`, `GET_PARAM(param_id=0x0411)` (S20.3) | ON at +5 °C, OFF at +10 °C; the card reads them, it does not change them | ☐ | |
| 7 | FPA cooler interface before activation — `GET_PARAM(param_id=0x040C)`, `GET_PARAM(param_id=0x0114)` | `tcs.cooler_fpa` (0x040C) = 0; `eps.pl_fpa_cooler` (0x0114) = 0; `tcs.temp_fpa` (0x0408) at the uncooled equilibrium, +8 to +14 °C — recorded for COM-010 | ☐ | T_fpa: ____ °C |
| 8 | Compile the thermal baseline report: minimum, maximum and mean of each zone over one orbit, against the thermal model | within the model prediction ± 5 °C | ☐ | |

Both heater lines are left **ON** at the end of this card: thermostat control
is the nominal configuration from now on. A heater whose line is dark obeys
the switch command and heats nothing — that is why each circuit starts by
powering its line.

**Exit?** ☐ yes ☐ no   **GO COM-005:** ☐

---

# Worksheet WB-5.6-C005 — COM-005 AOCS Mode Transitions (confirm each step)

**Mode codes** (`aocs/aocs_mode_codes.yaml`, canonical): 0 OFF,
1 SAFE_BOOT, 2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT,
6 SLEW, 7 DESAT, 8 ECLIPSE, 9 INERTIAL. Every commanded transition is
`AOCS_SET_MODE(mode=N)` (S8.1 **func_id 0**).

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Latch the commanded mode: `AOCS_SET_MODE(mode=4)` — NOMINAL | `aocs.mode` (0x020F) in {4, 8} within 300 s (8 = ECLIPSE, the automatic shadow-side handover); `aocs.commanded_mode` (0x0297) = 4 within 10 s; `aocs.att_error` (0x0217) < 1.0° within 600 s, sunlit side | ☐ | |
| 2 | Commanded NOMINAL → FINE_POINT through its gate: `AOCS_FINE_READY_CHECK` (S8.1 func **89**), then `AOCS_SET_MODE(mode=5)` | `aocs.fine_ready` (0x02C5) = 0, all seven legs green (in eclipse bit 5 holds it non-zero: wait for the sunlit arc); `aocs.mode` = 5 within 30 s; `aocs.att_error` < 0.1° within 300 s | ☐ | mask: ____ error: ____ ° |
| 3 | Commanded FINE_POINT → NOMINAL: `AOCS_SET_MODE(mode=4)` | `aocs.mode` = 4 within 30 s; `aocs.commanded_mode` (0x0297) = 4 within 10 s | ☐ | |
| 4 | Commanded NOMINAL → INERTIAL and back: `AOCS_SET_MODE(mode=9)`, then `AOCS_SET_MODE(mode=4)` | `aocs.mode` = 9, then 4, each within 30 s | ☐ | |
| 5 | COARSE_SUN is a hold, not a destination: `AOCS_SET_MODE(mode=3)`, then **wait** — send nothing | `aocs.mode` = 3 within 30 s and `aocs.mode_demoted` (0x0298) = 1; then `aocs.mode` = 4 **by itself** within 3600 s (about 1850 s in full sun; add an eclipse arc if the hold spans the terminator) and 0x0298 back to 0 | ☐ | promotion: ____ s |
| 6 | Automatic eclipse handover, observed in passing — no command | from the archive: `aocs.mode` in {4, 8} at every sample since step 3; NOMINAL → ECLIPSE (8) at entry and back at exit, `aocs.commanded_mode` (0x0297) = 4 throughout | ☐ | |
| 7 | Commanded with an automatic exit — desaturation: `AOCS_DESATURATE` (S8.1 func **1**) | `aocs.mode` = 7 (DESAT) within 30 s, then 4 within 900 s with no command; an ineffective desaturation times out (0x029C, event 0x020E) | ☐ | |
| 8 | Document the transition matrix: commanded rows carry the TC and its verification, automatic rows the trigger and the observed time | every row evidenced — AOCS mode management commissioned | ☐ | |

A 3-of-4 wheel set still flies FINE_POINT: bit 1 of `aocs.fine_ready` means
*fewer than three* wheels, and a degraded set is flagged at
`aocs.fine_degraded` (0x0299), not refused.

**Exit?** ☐ yes ☐ no

---

# Worksheet WB-5.6-C006 — COM-006 TTC Link Verification (confirm each step)

The TM rate ladder has exactly three rungs: **SAFE 1 kbps / LOW 16 kbps /
HIGH 128 kbps** (SAFE was called BEACON until 2026-08c; "beacon" now means only
the separate UHF transmitter). SAFE is not selectable with
`TTC_SET_DATA_RATE` — its baseline comes from the LEOP-001 pass. HIGH needs the
deployed antenna and DOWNLINK mode; the 10° elevation rule is ground policy,
not an on-board gate.

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 0 | Configure the S-band chain: `EPS_POWER_ON(line_index=2)` (func 19), `TTC_PA_ON` (func **66**), `TTC_SET_BEACON_MODE(on=0)` (func **70**), `TTC_DEPLOY_ANTENNA` (func **69**), `HK_REQUEST(sid=6)` | `eps.pl_ttc_tx` (0x0112) = 1; `ttc.pa_on` (0x0516) = 1; `ttc.beacon_mode` (0x0521) = 0; `ttc.antenna_deployed` (0x0520) = 1 within 30 s; `ttc.tx_active` (0x0525) = 1 (if 0, `ttc.tx_gate_status` (0x052B) names the missing permission) | ☐ | |
| 1 | Baseline the primary transponder: `HK_REQUEST(sid=6)` | `ttc.link_status` (0x0501) = **2** (LOCKED); TT&C page (ground): `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 6.0 dB; elevation and station recorded | ☐ | ____ dB @ ____ ° |
| 2 | RSSI vs elevation, read on the TT&C page at 10°, 30° and 60°+ | `ttc.rssi` (0x0502) > −126 dBm low, > −118 dBm medium, > −114 dBm high; `ttc.link_margin` (0x0503) > 3.0 dB at low elevation; within ± 3 dB of the link budget | ☐ | __ / __ / __ dBm |
| 2a | Baseline each rung, above 30°: `TTC_SET_DATA_RATE(rate=0)` (func **65**) LOW; `TTC_SET_DOWNLINK_MODE(on=1)` (func **79**); `TTC_SET_DATA_RATE(rate=1)` HIGH; then `TTC_SET_DATA_RATE(rate=0)` and `TTC_SET_DOWNLINK_MODE(on=0)` | LOW: `ttc.tm_data_rate` (0x0506) = 16000 bps, `ttc.tm_tier` (0x0539) = 1, margin **55–59 dB** at 30°. HIGH: `ttc.downlink_mode` (0x053C) = 1, 128000 bps, tier 2, `ttc.tm_symbol_rate` (0x053B) = 64000 Bd (QPSK), margin **45–48 dB**. Step margin(LOW) − margin(HIGH) = **10.5 ± 0.5 dB**; back at 16000 bps with DOWNLINK mode 0 | ☐ | step: ____ dB |
| 2b | Ground arm-through policy on HIGH (no on-board gate): below 10° elevation, try to arm HIGH in the MCS command panel **without** confirming the arm-through | the MCS raises its low-elevation warning and releases nothing; no telecommand reaches the spacecraft; the link stays at LOW | ☐ | |
| 3 | Switch to the redundant transponder: `TTC_SWITCH_REDUNDANT` (func **64**) | `ttc.link_status` = 2 within 60 s; `ttc.rssi` > −126 dBm (the station may need a brief re-acquisition) | ☐ | |
| 4 | Redundant transponder performance: `HK_REQUEST(sid=6)` | `ttc.link_margin` (0x0503) > 6.0 dB; RSSI within 2.0 dB of the primary at a similar elevation | ☐ | Δ: ____ dB |
| 5 | Restore the primary: `TTC_SWITCH_PRIMARY` (func **63**) | `ttc.link_status` = 2 within 60 s; `ttc.rssi` > −126 dBm | ☐ | |
| 6 | Command throughput: six rapid `GET_PARAM(param_id=0x0105)` … `GET_PARAM(param_id=0x010A)` (S20.3), then `GET_PARAM(param_id=0x0306)` | all six responses within 30 s; `obdh.tc_rej_count` (0x0306) unchanged across the burst | ☐ | |
| 7 | Multi-station verification on later passes: repeat steps 1–2 over each station of the network | margin > 3 dB at 10° elevation from every station | ☐ | stations: ____ |
| 8 | Compile the link budget report: margin against elevation **and** against rate tier for each station, compared with the baseline table on the card | discrepancies documented; minimum operational elevation per station established | ☐ | |
| 9 | Safe the link: `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)`, `TTC_SWITCH_PRIMARY`, `HK_REQUEST(sid=6)` | `ttc.tm_tier` (0x0539) = 1 and `ttc.tm_tier_cmd` (0x053A) = 1; `ttc.downlink_mode` (0x053C) = 0; `ttc.beacon_mode` (0x0521) = 0; `ttc.antenna_deployed` (0x0520) = 1 and `ttc.pa_on` (0x0516) = 1 — both stay that way for nominal operations | ☐ | |

A refused rate change comes back as S1.8 0x0007 with a notice naming the
on-board gate (beacon mode, antenna, DOWNLINK mode). Read the notice, not the
code: elevation is never one of them.

**Exit?** ☐ yes ☐ no

---

# Worksheet WB-5.6-C007 — COM-007 OBDH Checkout (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Verify the OBC mode: `HK_REQUEST(sid=4)` (S3.27) | `obdh.mode` (0x0300) = 0 (NOMINAL; 1 SAFE, 2 EMERGENCY). SAFE here means an earlier card left an excursion unrestored — investigate before going on | ☐ | |
| 2 | CPU utilisation: `GET_PARAM(param_id=0x0302)` (S20.3) | `obdh.cpu_load` (0x0302) ∈ [10, 50] % (idle is about 15–25 %) | ☐ | ____ % |
| 3 | Memory status: `GET_PARAM(param_id=0x0303)` (`obdh.mmm_used`), `GET_PARAM(param_id=0x031E)` (`obdh.mem_errors`), `GET_PARAM(param_id=0x0319)` (`obdh.seu_count`) | mass memory < 70 %; `obdh.mem_errors` (0x031E) and `obdh.seu_count` (0x0319) recorded as baselines and not incrementing between reads | ☐ | used: ____ % |
| 4 | TC/TM packet counters: `GET_PARAM(param_id=0x0304)`, `GET_PARAM(param_id=0x0306)`, `GET_PARAM(param_id=0x0307)` | `obdh.tc_rx_count` > 0, matching the ground log; `obdh.tc_rej_count` = 0; `obdh.tm_pkt_count` > 0 and incrementing | ☐ | |
| 5 | Confirm NOMINAL-mode services — no mode command: commanding the mode you are in proves nothing | `obdh.mode` (0x0300) = 0; `obdh.cpu_load` (0x0302) < 60 % over 30 s | ☐ | |
| 6 | Autonomous HK generation: `GET_PARAM(param_id=0x0307)`, wait 60 s sending **no** TC, `GET_PARAM(param_id=0x0307)` again | `obdh.tm_pkt_count` has incremented | ☐ | |
| 7 | Watchdog: `OBC_DIAGNOSTIC` (S8.1 func **61**), `GET_PARAM(param_id=0x0316)` | diagnostic reply byte 5 = 1 (watchdog armed — it is in this reply only, not a telemetry parameter); `obdh.last_reboot_cause` (0x0316) = 0 | ☐ | |
| 8 | OBC mode excursion NOMINAL → SAFE → NOMINAL: `OBC_SET_MODE(mode=1)`, then `OBC_SET_MODE(mode=0)` (S8.1 func **50**) | `obdh.mode` = 1 within 15 s, then 0 within 15 s — **the card must not end in SAFE**; the MCS contingency banner is expected while SAFE | ☐ | |
| 9 | Record the OBDH baseline: CPU load, memory usage, error and SEU counters, TC/TM statistics, watchdog status | OBDH Checkout Report filed — the reference for anomaly detection in nominal operations | ☐ | |

There is no watchdog-kick telecommand: the watchdog state is read from the
`OBC_DIAGNOSTIC` reply.

**Exit?** ☐ yes ☐ no

---

# Worksheet WB-5.6-C008 — COM-008 FDIR Configuration (confirm each step)

There is **no** FDIR table-load telecommand. The rule set is
static configuration (`subsystems/fdir.yaml` plus the S12 limit
definitions and S19 event-action rules); commissioning verifies
and exercises it, it does not upload it.

Keep the two ladders distinct: **FDIR severity 0–4** (how bad the
event is) and **autonomy level 0–3** (who is allowed to act —
0 hardware, 1 subsystem SW, 2 OBC FDIR, 3 ground). They are not
the same scale and must never be conflated on the loop.

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Enable and inventory S12 monitoring: `MON_ENABLE` (**S12.1**), `MON_REPORT_DEFS` (S12.12) | TM(12,13) definition report within 10 s; every shipped definition of `monitoring/s12_defs` present, none unexpected | ☐ | count: ____ |
| 2 | Inventory the S19 event-action table: `EA_REPORT_DEFS` (S19.8) | TM(19,128) report within 10 s; shipped rules present and ENABLED — the momentum chain (S12 monitor on `aocs.h_env_frac` (0x02BA) → ea 2001 → S8 func 1, the desaturation) and the TCS over-temperature safing chain (ea 3003) | ☐ | |
| 3 | FDIR summary telemetry: `GET_PARAM(param_id=0x0700)`, `GET_PARAM(param_id=0x0701)` (S20.3) | `fdir.level` (0x0700) = 0; `fdir.active_alarms` (0x0701) = 0. Anything non-zero is a latched alarm: resolve it before step 4 | ☐ | |
| 4 | Functional test of the commanded load-shed latch: record `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112); `EPS_EMERGENCY_LOAD_SHED(stage=1)` (S8.1 func **25**), then `EPS_EMERGENCY_LOAD_SHED(stage=0)`. Never stage 2 or 3 here | stage 1: `eps.load_shed_stage` (0x0134) = 1 and **latches**, event LOAD_SHED_STAGE_1 (0x0106), `eps.pl_payload` = 0. Stage 0: back to 0 and every line flag **unchanged** — stage 0 re-powers nothing | ☐ | |
| 5 | Confirm no residual protection state: `GET_PARAM(param_id=0x0700)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `fdir.level` = 0; `eps.load_shed_stage` = 0; `obdh.mode` (0x0300) = 0 — this card makes no OBC-mode excursion | ☐ | |

Read the FDIR thresholds from the FDIR panel and `subsystems/fdir.yaml`, not
from memory: limits are configuration, and they change.

**Exit?** ☐ yes ☐ no

---

# Worksheet WB-5.6-C009 — COM-009 Payload Power-On (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Pre-power-on EPS baseline: `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) ∈ [27.0, 29.0] V; `eps.bat_soc` (0x0101) > 75 %; `eps.power_gen` (0x0107) > 40 W — all three recorded | ☐ | |
| 2 | Verify the payload is OFF: `HK_REQUEST(sid=5)` | `payload.mode` (0x0600) = 0 (OFF) | ☐ | |
| 3 | Energise the line, then STANDBY: `EPS_POWER_ON(line_index=3)` (S8.1 func_id **19**), `HK_REQUEST(sid=1)`, `PAYLOAD_SET_MODE(mode=1)` (func **26**), `HK_ENABLE(sid=5)` (**S3.5**), `HK_REQUEST(sid=5)` | `eps.pl_payload` (0x0113) = 1 within 10 s; `payload.mode` = 1 (STANDBY) within 60 s, and **still 1** on a SID 5 re-request 60 s later — a mode that reverts to 0 means the line is dark | ☐ | |
| 4 | Payload power draw: `HK_REQUEST(sid=1)`, `GET_PARAM(param_id=0x0106)` (S20.3) | `eps.bus_voltage` > 27.0 V; `eps.power_cons` (0x0106) up **2–3 W** on the baseline (STANDBY about 2.4 W; the 15 W cooler is not on until COM-010) | ☐ | ____ W |
| 5 | Electronics health: `HK_REQUEST(sid=5)`, `GET_PARAM(param_id=0x0611)`, `GET_PARAM(param_id=0x0603)` | `payload.imager_status` (0x0611) without fault bits; `payload.imager_temp` (0x0603) in its operating band | ☐ | |
| 6 | FPA temperature before the cooler: `GET_PARAM(param_id=0x0601)` | `payload.fpa_temp` (0x0601) ∈ [+5, +30] °C — recorded for COM-010 | ☐ | ____ °C |
| 7 | Data interface: `GET_PARAM(param_id=0x0604)`, `GET_PARAM(param_id=0x0648)`, `GET_PARAM(param_id=0x0647)` | `payload.store_used` (0x0604) about 20 % (pre-existing fill: the empty baseline, not a fault); `payload.product_count` (0x0648) = 0 and `payload.product_mb` (0x0647) = 0 | ☐ | |
| 8 | Hold STANDBY 10 min for thermal stabilisation: `HK_REQUEST(sid=3)` at T+5 and T+10 min, `HK_REQUEST(sid=5)` | `tcs.temp_obc` (0x0406) stable; `payload.fpa_temp` stable; `payload.mode` = 1 maintained | ☐ | |
| 9 | Log the Payload Power-On Report: timing, power draw, imager status word, imager and FPA temperatures, store baseline | ready for COM-010 | ☐ | |

Payload modes: 0 OFF, 1 STANDBY, 2 IMAGING, **3 CALIBRATION**. STANDBY draws
about 0.09 A at 28 V on line 3.

**Exit?** ☐ yes ☐ no   **GO COM-010:** ☐

---

# Worksheet WB-5.6-C010 — COM-010 FPA Cooler Activation (confirm each step; spans eclipse)

The FPA cooler is a **miniature Stirling-class cryocooler** running
at about 23 % of Carnot (`fpa_cooler_carnot_fraction` 0.23) — not a
Peltier stack. Its authority falls as the lift grows, so the
achievable floor moves with the sink temperature and the imaging
load. Default setpoint **−15 °C**; commandable envelope **−20 °C to
0 °C** (`PAYLOAD_COOLER_SETPOINT`, S8.1 func **36**, argument is a
uint16 in **centi-kelvin** — −15 °C is 0x64D7). The loop settles in
about 10 minutes and never overshoots the setpoint.

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Record the pre-activation state, cooler OFF (cool-down T = 0): `HK_REQUEST(sid=3)`, `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=5)` (S3.27) | `payload.fpa_temp` (0x0601) ∈ [+8, +14] °C; `tcs.temp_fpa` (0x0408) consistent with it; `payload.mode` (0x0600) = 1 | ☐ | T_fpa: ____ °C |
| 2 | Enable the cooler: `FPA_COOLER(on=1)` (S8.1 func_id **43**), then `GET_PARAM(param_id=0x040C)`, `GET_PARAM(param_id=0x0114)` | `tcs.cooler_fpa` (0x040C) = 1 **and** `eps.pl_fpa_cooler` (0x0114) = 1 — both, or the cooler is not actually running | ☐ | |
| 3 | Cooler power draw: `HK_REQUEST(sid=1)`, `GET_PARAM(param_id=0x0106)` (S20.3) | `eps.power_cons` (0x0106) up **14–16 W** on the pre-cooler baseline within 30 s; `eps.bus_voltage` (0x0105) > 27.0 V | ☐ | ____ W |
| 4 | First 5 minutes: `GET_PARAM(param_id=0x0601)` at T+2 and T+5 min (every minute on WB-5.6-FPA) | `payload.fpa_temp` < +4 °C at T+2 and < −8 °C at T+5. The ramp is exponential: slower at T+5 than at T+2 is expected | ☐ | T+5: __ °C |
| 5 | Settling: `GET_PARAM(param_id=0x0601)` at T+10 and T+15 min | T+10 ∈ [−16.0, −14.0] °C; T+15 ∈ [−16.0, −15.0] °C. A reading below −16.5 °C is a **control fault**, not an over-performing cooler | ☐ | T+15: __ °C |
| 6 | Operational temperature: `GET_PARAM(param_id=0x0601)`, `GET_PARAM(param_id=0x0610)`, `GET_PARAM(param_id=0x0631)`, `GET_PARAM(param_id=0x064A)`, `GET_PARAM(param_id=0x064B)` | `payload.fpa_temp` ∈ [−16.5, −14.5] °C; `payload.fpa_ready` (0x0610) = 1 within 60 s (hysteresis); `payload.fpa_setpoint` (0x0631) = −15.0; `payload.cooler_margin_k` (0x064B) > 0 (about +5 K); floor at `payload.cooler_floor_c` (0x064A) | ☐ | margin: ____ K |
| 7 | Stability: `GET_PARAM(param_id=0x0601)` at T+35, T+40 and T+45 min | `payload.fpa_temp` ∈ [−16.5, −14.5] °C at every sample; peak-to-peak < 1.0 °C over 10 min (below 0.5 °C is normal control) | ☐ | p-p: ____ °C |
| 8 | Through eclipse, if the pass spans one: `GET_PARAM(param_id=0x0601)` | `payload.fpa_temp` ∈ [−16.5, −14.5] °C; `eps.bus_voltage` (0x0105) > 27.0 V with the cooler load | ☐ | |
| 9 | Generate the Cooler Activation Report: cool-down curve, cooler power, stability and eclipse data | ready for COM-011 | ☐ | |

**If `cooler_margin_k` ≤ 0:** the cooler physically cannot reach the
commanded setpoint at the present sink and load. The answer is a
**warmer setpoint**, not more waiting.

The readiness flag, not a remembered temperature, is the gate for imaging. The
cooler's own draw is `payload.cooler_pwr` (0x0602), about 15 W.

**Exit?** ☐ yes ☐ no   **GO COM-011:** ☐

---

# Worksheet WB-5.6-FPA — FPA Cool-Down Monitor Sheet

**Use:** during COM-010. The loop closes in about 10 minutes, so
record `payload.fpa_temp` (0x0601) every minute for the first
15 minutes, then every 5 minutes through the stability hold.

| Elapsed | T_fpa (°C) | `payload.cooler_pwr` 0x0602 (W) | Eclipse? | Note |
|---------|-----------|------------------|:--------:|------|
| 0:00 | | | ☐ | start, +8 to +14 °C |
| 0:01 | | | ☐ | |
| 0:02 | | | ☐ | expect < +4 °C |
| 0:03 | | | ☐ | |
| 0:04 | | | ☐ | |
| 0:05 | | | ☐ | expect < −8 °C |
| 0:06 | | | ☐ | |
| 0:07 | | | ☐ | |
| 0:08 | | | ☐ | |
| 0:09 | | | ☐ | |
| 0:10 | | | ☐ | expect −16.0 to −14.0 °C |
| 0:11 | | | ☐ | |
| 0:12 | | | ☐ | |
| 0:13 | | | ☐ | |
| 0:14 | | | ☐ | |
| 0:15 | | | ☐ | setpoint band expected by here |
| 0:20 | | | ☐ | stability hold |
| 0:25 | | | ☐ | |
| 0:30 | | | ☐ | |
| 0:35 | | | ☐ | |
| 0:40 | | | ☐ | |
| 0:45 | | | ☐ | p-p variation < 1.0 °C over the hold |

**`payload.fpa_ready` (0x0610) set at elapsed:** ______ min
**`payload.cooler_margin_k` (0x064B) at setpoint:** ______ K

---

# Worksheet WB-5.6-C011 — COM-011 Payload Calibration (confirm each step)

Radiometric calibration is its own payload mode: `payload.mode`
(0x0600) = **3 (CALIBRATION)**. Dark calibration no longer requires
IMAGING mode. If a calibration is refused, read the reason code —
0x0024 refused because IMAGING, 0x0025 FPA not ready, 0x0026
shutter in the wrong position, 0x0027 lamp in the wrong state,
0x0028 capture with the shutter closed.

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Pre-calibration state, cooler ON first: `FPA_COOLER(on=1)` (S8.1 func **43**), `HK_REQUEST(sid=3)`, `HK_REQUEST(sid=5)` (S3.27), `GET_PARAM(param_id=0x060B)`, `GET_PARAM(param_id=0x060A)` (S20.3) | `tcs.cooler_fpa` (0x040C) = 1 within 10 s; `payload.mode` (0x0600) = 1 (STANDBY); `payload.fpa_ready` (0x0610) = 1 within 600 s (cool-down about 6.5 min); `payload.fpa_temp` (0x0601) ∈ [−16.5, −14.5] °C; free store (total − used) > 1000 MB | ☐ | free: ____ MB |
| 2 | Close the shutter: `PAYLOAD_SET_SHUTTER(position=0)` (S8.1 func **119**), `GET_PARAM(param_id=0x063C)` | `payload.shutter_pos` (0x063C) = 0 (CLOSED) | ☐ | |
| 3 | Dark set, from STANDBY with no mode command (STANDBY would switch the cooler off): `PAYLOAD_CAL_LAMP(on=0)` (func **95**), `PAYLOAD_START_CALIBRATION(mode=0)` (func **37**, 0 = DARK), `HK_REQUEST(sid=5)` twice, `GET_PARAM(param_id=0x0642)` | `payload.mode` = 3 (CALIBRATION) within 15 s; `payload.calibration_active` (0x062A) = 1, then 0 within 120 s; `payload.cal_abort_reason` (0x0645) = 0; `payload.dark_frame_cnt` (0x0642) > 0 | ☐ | frames: ____ |
| 3a | Flat-field set: `PAYLOAD_SET_SHUTTER(position=1)`, `PAYLOAD_CAL_LAMP(on=1)`, `GET_PARAM(param_id=0x0615)`, `GET_PARAM(param_id=0x063C)`, `PAYLOAD_START_CALIBRATION(mode=1)` (1 = FLAT), `HK_REQUEST(sid=5)`, `PAYLOAD_CAL_LAMP(on=0)` | `payload.cal_lamp_on` (0x0615) = 1; `payload.shutter_pos` = 1 (OPEN); `payload.calibration_active` = 0 within 120 s; `payload.cal_abort_reason` = 0; `payload.cal_valid_mask` (0x0646) = 15 — bias and gain on all four bands | ☐ | mask: ____ |
| 4 | Dark-frame quality, on the ground from the downlinked frames: `GET_PARAM(param_id=0x0642)` | mean dark signal < 100 DN (12-bit, 0–4095); standard deviation < 10 DN | ☐ | mean __ σ __ |
| 5 | Open the shutter; the sequencer has already put the payload back in STANDBY, cooler running — no mode command: `PAYLOAD_SET_SHUTTER(position=1)`, `HK_REQUEST(sid=5)`, `GET_PARAM(param_id=0x063C)` | `payload.mode` = 1 within 15 s; `payload.shutter_pos` (0x063C) = 1 | ☐ | |
| 6 | Calibration-site overpass: `AOCS_FINE_READY_CHECK` (func 89), then `AOCS_SET_MODE(mode=5)` (func 0) — FINE_POINT is mode **5** | `aocs.fine_ready` (0x02C5) = 0; `aocs.mode` (0x020F) = 5 within 30 s; `aocs.att_error` (0x0217) < 0.1° within 300 s | ☐ | overpass: ____ |
| 7 | Site image at the overpass: `PAYLOAD_SET_MODE(mode=2)` (IMAGING), `PAYLOAD_CAPTURE(scene_id=0, lines=2048)` (func 28) | `payload.mode` = 2 within 30 s; `payload.last_scene_id` (0x060C, by `GET_PARAM`) increments within 30 s; time, GPS position, sun angle and view geometry recorded | ☐ | scene: ____ |
| 8 | Linearity pair: `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=1.00, green_ms=1.00, red_ms=1.00, nir_ms=1.00)` (func 34) and `PAYLOAD_CAPTURE(scene_id=0, lines=2048)`; then `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=4.00, green_ms=4.00, red_ms=4.00, nir_ms=4.00)` and a second capture | on the ground: the half-integration mean is about half the nominal one; the double is about twice, not clipped at 4095 DN | ☐ | |
| 9 | Return to the standard configuration: `PAYLOAD_SET_MODE(mode=1)`, `PAYLOAD_SET_INTEGRATION_TIME(blue_ms=2.00, green_ms=2.00, red_ms=2.00, nir_ms=2.00)`, `AOCS_SET_MODE(mode=4)` | `payload.mode` = 1 within 15 s; `tcs.cooler_fpa` (0x040C) = 0 (STANDBY releases the cooler); integration time restored; `aocs.mode` = 4 within 30 s | ☐ | |
| 10 | Data stored, downlink scheduled: `GET_PARAM(param_id=0x0647)`, `GET_PARAM(param_id=0x0648)` | storage consistent with about 13 frames (10 dark + 3 site images); full downlink booked for the next pass | ☐ | |

A completed calibration also logs the S5 event 0x060B CALIBRATION_COMPLETE.

**Exit?** ☐ yes ☐ no   **GO COM-012:** ☐

---

# Worksheet WB-5.6-C012 — COM-012 First Light (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | AOCS to FINE_POINT: `AOCS_FINE_READY_CHECK` (func 89) — the mask must read 0, or mode 5 is refused TM(1,8) — then `AOCS_SET_MODE(mode=5)` | `aocs.mode` (0x020F) = 5 within 30 s; `aocs.total_pointing_err_3sig` (0x02AA) < 0.05° within 300 s (the capture gate); `aocs.att_error` (0x0217) < 0.1° within 180 s; `aocs.rate_pitch` (0x0205) ∈ [0.053, 0.073]°/s (nadir orbit rate); `aocs.rate_yaw` (0x0206) < 0.01°/s | ☐ | |
| 2 | FPA temperature: `GET_PARAM(param_id=0x0601)` (S20.3) | `payload.fpa_temp` (0x0601) ∈ [−16.5, −14.5] °C — `payload.fpa_ready` (0x0610) = 1 says the same | ☐ | T: ____ °C |
| 3 | Payload ready, baselines: `HK_REQUEST(sid=5)`, `GET_PARAM(param_id=0x0604)`, `GET_PARAM(param_id=0x0605)`, `GET_PARAM(param_id=0x060B)` | `payload.mode` (0x0600) = 1; `payload.store_used` (0x0604) < 97 %; `payload.image_count` (0x0605) and `payload.mem_used_mb` (0x060B) recorded | ☐ | count __ MB __ |
| 4 | IMAGING: `PAYLOAD_SET_MODE(mode=2)` (func **26**) | `payload.mode` = 2 (IMAGING) within 30 s | ☐ | |
| 5 | First capture: `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` (S8.1 func **28**) | `payload.last_scene_id` (0x060C) = 1 within 30 s and `payload.image_count` (0x0605) = 1 within 10 s, both by `GET_PARAM`. 2048 lines at 244 Hz = 8.4 s ≈ 59 km along-track | ☐ | scene: ____ |
| 6 | Image written: `GET_PARAM(param_id=0x0604)`, `GET_PARAM(param_id=0x060B)` | `payload.store_used` (0x0604) up; `payload.mem_used_mb` (0x060B) up by 1.0–4.0 MB since step 3 (one image: 4 MB raw, 1.0–2.7 MB compressed; 0x060B is the total, so only the difference counts) | ☐ | Δ: ____ MB |
| 7 | Back to STANDBY: `PAYLOAD_SET_MODE(mode=1)` | `payload.mode` = 1 within 15 s; `tcs.cooler_fpa` (0x040C) = 0 within 10 s — STANDBY switches the cooler off | ☐ | |
| 8 | Downlink over Service 13: `TTC_SET_DOWNLINK_MODE(on=1)`, `TTC_SET_DATA_RATE(rate=1)` (HIGH), `S13_CREATE_TRANSFER(scene_id=1, size_mb=0)`, `S13_REPORT_STATUS(transfer_id=T)`, `S13_END_TRANSFER(transfer_id=T)`, `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)` | `ttc.tm_data_rate` (0x0506) = 128000 bps; TM(13,2) open report — transfer id, block count and CRC-32 recorded; `payload.transfer_active` (0x062D) = 1, `payload.transfer_progress` (0x062E) rising, then 0x062D = 0; back at 16000 bps with `ttc.downlink_mode` (0x053C) = 0; CRC-32 OK on the ground | ☐ | rx time: ______ |
| 9 | First Light assessment: `AOCS_SET_MODE(mode=4)`, `HK_REQUEST(sid=2)`, `HK_REQUEST(sid=5)` | `aocs.mode` = 4 within 30 s; `payload.mode` = 1; `payload.cooler_pwr` (0x0602) = 0 (cooler released at step 7); payload team: geometry, all four bands, no artefacts, dark current; First Light Report | ☐ | quality: ____ |

Image quality and geo-registration go on WB-5.6-FL. A capture also logs the S5
event 0x0613 IMAGE_CAPTURED.

**Exit?** ☐ yes ☐ no   **First Light declared?** ☐ yes ☐ formally deferred

**If deferred, justification:** ______________________________________

---

# Worksheet WB-5.6-FL — First Light Image Assessment

| Field | Entry |
|-------|-------|
| Image ID | |
| Target name | |
| Acquisition UTC | |
| AOCS mode at acquisition | |
| FPA temperature at acquisition (°C) | |
| Integration time per band (ms), bands at 443/560/665/865 nm | / / / |
| Image size (MB) — expect 1.0–2.7 stored (4 raw) | |
| Ground swath (km) — `payload.swath_width_km` (0x0619) | 273 |
| GSD (m) — `payload.gsd_m` (0x0628) | 33.4 |
| Mean DN per band | |
| Cloud cover (%) | |
| Geo-registration error (m) — `aocs.geoloc_err_m` (0x02C7) | |
| Quality verdict | ☐ science usable ☐ marginal ☐ retake |
| Customer bulletin drafted? (Mission Mgr) | ☐ yes |

---

# Worksheet WB-5.6-MA — Day 4 Multi-Anomaly Response Form

**Use:** if the instructor injects more than one anomaly in a
pass-set. One row per anomaly; signed by FD at end of recovery.

| Anomaly # | First indicator time | Position to flag it | Procedure invoked | Recovery time (s) | Outcome | FD sig |
|-----------|---------------------|--------------------:|-------------------|-------------------|---------|--------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

**Order of priority taken:** _________________________________

**Conflicts encountered (procedure A requires X, procedure B requires not-X):**

___________________________________________________________________

**How conflicts resolved:** _________________________________________

---

# Worksheet WB-5.6-GO — Day 4 Pass-Set Criteria Scorecard

**Assessor:** ______________   **Pass-set:** ☐ Pass-set 1 (Team A) ☐ Pass-set 2 (Team B)

| Criterion | ☐ achieved |
|-----------|:----------:|
| Phase advanced to COMMISSIONING (5) — `SYS_SET_MISSION_PHASE` (func 120) sent and verified | ☐ |
| EPS checkout complete, no faults | ☐ |
| AOCS NOMINAL (mode 4) achieved, `aocs.att_error` < 1.0°; FINE_POINT (5) demonstrated at < 0.1° | ☐ |
| FDIR rule set verified and exercised on the FDIR panel | ☐ |
| Payload powered ON (`eps.pl_payload` 0x0113 = 1, `payload.mode` = 1) | ☐ |
| FPA cooler demonstrated at its commanded setpoint (−15 °C default) in COM-010, `payload.fpa_ready` (0x0610) = 1, `cooler_margin_k` > 0 | ☐ |
| First Light image acquired or formally deferred | ☐ |
| Anomaly tickets filed for all injections | ☐ |

**Score:** ____ / 8

---

# Worksheet WB-5.6-OBS — Day 4 Observer Worksheets (axes: Team + Space usage)

### Observer worksheet — Team axis

**Observer:** _____________

| Item | Note |
|------|------|
| Did each position know its role? | |
| Was the FD authoritative? | |
| Anyone over-loaded or under-utilised? | |
| Did anyone do another position's job? | |
| Was fatigue handled (breaks, water)? | |
| How did the team handle disagreement? | |

**Worked well:** ________________________   **Could improve:** _______________________

**Specific recommendation:** _________________________________________

### Observer worksheet — Space-usage axis

**Observer:** _____________

| Item | Note |
|------|------|
| Console layout — could every position see what they needed? | |
| Line of sight — could FD see all positions? | |
| Distractions (phones, side talk, music)? | |
| Lighting, temperature, noise — issues? | |
| Movement around the room (procedures, water) | |
| Physical comfort — chairs, monitors, posture | |

**Worked well:** ________________________   **Could improve:** _______________________

**Specific recommendation:** _________________________________________

---

# Worksheet WB-5.6-HO — Day 4 Inter-Pass Handover Turnover Form

(Same format as WB-5.5-HO; print 9 copies, one per console
position.)

### Handover — Position: ______________________

| Field | Entry |
|-------|-------|
| Outgoing operator | |
| Incoming operator | |
| Current parameter values (top 3) | |
| Current procedure state (file ID + step) | |
| Any pinned widget? | |
| FDIR rules currently active (acknowledged) | |
| Open question for next shift | |
| Outgoing signature | |
| Incoming signature | |
| Time | |

---

# Worksheet WB-5.6-DB — Day 4 Post-Shift Debrief Reflection

(Same five-question prompt as WB-5.5-DB.)

1. What is one decision you took during the shift that, in
   retrospect, you would not take again? Why?

   ___________________________________________________________

2. What is one decision that surprised you with how well it
   worked?

   ___________________________________________________________

3. Which procedure step did you most struggle to execute in real
   time?

   ___________________________________________________________

4. What is one thing the team did better as a unit than you
   expected?

   ___________________________________________________________

5. What is one specific thing you will take into your future
   engineering work?

   ___________________________________________________________

---

# Worksheet WB-5.7-SA — Day 5 Personal Self-Assessment

**Name:** _____________________

For each row, score yourself 1–3 (1 = developing, 2 = competent,
3 = strong). Be honest — the cohort average is 2.0.

| Row | Competency | Score (1–3) | Evidence |
|-----|------------|:-----------:|----------|
| 1 | Voice-loop discipline | | |
| 2 | Procedure compliance | | |
| 3 | Telemetry interpretation | | |
| 4 | Anomaly response timing | | |
| 5 | Handover quality | | |
| 6 | Position rotation completion | | |
| 7 | Pass-plan quality (Day 1 exercise) | | |
| 8 | Quiz score / 15 | | |
| 9 | Debrief contribution | | |

**Total:** ____ / 27   **Honours threshold:** 22

**Three things I am proudest of this week:**

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

**Three things I want to keep working on:**

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

---

# Worksheet WB-5.7-LL — Cohort Lessons-Learned Contribution

**Name:** _____________________

Each cohort member adds at least three lessons to the cohort
register. The register is read by next year's cohort.

### Lesson 1

**Title:** ____________________________________________________

**What we observed:** _________________________________________

**Why it matters:** ____________________________________________

**Recommendation:** ___________________________________________

### Lesson 2

**Title:** ____________________________________________________

**What we observed:** _________________________________________

**Why it matters:** ____________________________________________

**Recommendation:** ___________________________________________

### Lesson 3

**Title:** ____________________________________________________

**What we observed:** _________________________________________

**Why it matters:** ____________________________________________

**Recommendation:** ___________________________________________

---

# Worksheet WB-5.7-WI — "What If" Branch Reflection

If the instructor ran a branch-replay, fill this in.

**Original decision:** _____________________________________

**Alternative decision tried in replay:** ____________________

**What changed in the next 15 simulated minutes:**

___________________________________________________________________

**Which decision would you take next time? Why?**

___________________________________________________________________

---

# Worksheet WB-5.7-FR — Final Mission Review Prep

The cohort produces a 4–6 page CFMR (final mission review) document on Day 5
afternoon. Use this worksheet to collect material.

### Section 1 — Mission objectives

Were the Week 3 objectives met? (Day 5, list each with PASS/FAIL.)

| Objective | PASS / FAIL | Evidence |
|-----------|:-----------:|----------|
| Operated all 9 positions for at least one full pass | ☐ / ☐ | |
| Ran a planning cycle end-to-end | ☐ / ☐ | |
| Executed one nominal procedure as lead | ☐ / ☐ | |
| Executed one contingency procedure as lead | ☐ / ☐ | |
| Critiqued a peer team's shift | ☐ / ☐ | |
| Produced a shift log and anomaly ticket | ☐ / ☐ | |

### Section 2 — Telemetry summary across the week

Three most-watched parameters and their typical values:

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

### Section 3 — Anomalies log

| Date | Anomaly | Procedure | Outcome | Root cause |
|------|---------|-----------|---------|------------|
| Wed | | | | |
| Wed | | | | |
| Thu | | | | |
| Thu | | | | |

### Section 4 — Compliance with ECSS-E-ST-70-11C

Tick each clause you can demonstrate compliance with from the
cohort's shift logs and worksheets.

| Clause area | ☐ |
|-------------|:-:|
| 5.1 Operability principles | ☐ |
| 5.2 Operations preparation | ☐ |
| 5.3 Procedure design | ☐ |
| 5.4 Anomaly management | ☐ |
| 5.5 Reporting and review | ☐ |

### Section 5 — Crew performance self-assessment

(Aggregated from WB-5.7-SA across the cohort.)

| Position | Cohort mean score (1–3) |
|----------|:-----------------------:|
| FD | |
| SPACON | |
| AOCS | |
| EPS | |
| Thermal | |
| TT&C | |
| Payload | |
| FDS | |
| Ground Seg | |
| Mission Manager | |

### Section 6 — Recommendations for next cycle

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

---

# Worksheet WB-5.7-CE — Course Evaluation

**Anonymous.** Drop in the box by the door.

| Item | 1 (poor) | 2 | 3 | 4 | 5 (excellent) |
|------|:--------:|:-:|:-:|:-:|:-------------:|
| Lesson-plan structure (Mon/Tue) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Simulator realism (Wed/Thu) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Instructor coaching | ☐ | ☐ | ☐ | ☐ | ☐ |
| Cyberrange facility | ☐ | ☐ | ☐ | ☐ | ☐ |
| Workbook usefulness | ☐ | ☐ | ☐ | ☐ | ☐ |
| Pace (too slow / right / too fast) | slow ☐ | ☐ | right ☐ | ☐ | fast ☐ |
| Confidence to operate a real shift now | low ☐ | ☐ | medium ☐ | ☐ | high ☐ |

**One thing you would change for next year:**

___________________________________________________________________

___________________________________________________________________

**One thing you would keep exactly as it is:**

___________________________________________________________________

___________________________________________________________________

---

# Appendix WB-A — Contingency confirm-each-step (Week-3-likely)

The contingency confirm pages below are reference: they sit in
this workbook so that if the instructor injects a scenario, the
team has a ready-printed page to follow on the console.

## CTG-001 Under-Voltage Load Shed

On-board FDIR sheds by itself below 25.0 V (payload → FPA cooler → `ttc_tx` →
AOCS wheels → prop, one line per second, events 0x0106–0x0108). **Check the
spacecraft first**: each level below is a GO only while its line is still ON;
if FDIR has already opened it, send nothing and go to the voltage check. A shed
that worked: hold at that level and go straight to step 6.

| # | Owner | Action | Verification | ☐ | Note |
|---|-------|--------|--------------|:-:|------|
| 1 | EPS | Detect and confirm, and read what FDIR has already shed: `HK_REQUEST(sid=1)` (S3.27). FD authorises; announce "UNDERVOLTAGE — completing load shed from the ground" | `eps.uv_flag` (0x010E) = 1; record `eps.bus_voltage` (0x0105, expect < 27.0 V), `eps.bat_soc` (0x0101), `eps.bat_voltage` (0x0100), `eps.power_cons` (0x0106), `eps.power_gen` (0x0107), `eps.eclipse_flag` (0x0108), `eps.load_shed_stage` (0x0134), and `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_ttc_tx` (0x0112), `eps.pl_aocs_wheels` (0x0117): 1 = still ON, 0 = already shed | ☐ | stage: __ V: __ |
| 2 | EPS | Priority 1, payload OFF (payload line still ON): `PAYLOAD_SET_MODE(mode=0)` (S8.1 func **26**), `HK_REQUEST(sid=5)`, `HK_REQUEST(sid=1)` 30 s later | `payload.mode` (0x0600) = 0 within 10 s; `eps.power_cons` down; `eps.bus_voltage` recorded | ☐ | V: ____ |
| 3 | EPS | Priority 2, FPA cooler OFF (cooler line still ON): `FPA_COOLER(on=0)` (func **43**), `GET_PARAM(param_id=0x040C)`, `HK_REQUEST(sid=3)`, `HK_REQUEST(sid=1)` 30 s later | `tcs.cooler_fpa` (0x040C) = 0 within 5 s; `eps.power_cons` down about 15 W; `eps.bus_voltage` recorded | ☐ | V: ____ |
| 4 | EPS | Priority 3, transmitter OFF (`ttc_tx` line still ON): `TTC_PA_OFF` (func **67**), `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)` 30 s later | `ttc.pa_on` (0x0516) = 0 within 5 s; `eps.power_cons` down about 20 W; `eps.bus_voltage` recorded. The S-band downlink is now gone; uplink stays | ☐ | V: ____ |
| 5 | EPS | Priority 4, wheels line OFF (still ON): `EPS_POWER_OFF(line_index=7)` (func **20**), `HK_REQUEST(sid=1)` 30 s later | `eps.pl_aocs_wheels` (0x0117) = 0 within 5 s; `eps.bus_voltage` recorded. Active attitude control is lost | ☐ | V: ____ |
| 5B | EPS | Last resort only, every level taken and the bus still falling — OBC EMERGENCY: `OBC_SET_MODE(mode=2)` (func **50**), `HK_REQUEST(sid=4)` | `obdh.mode` (0x0300) = 2 within 15 s | ☐ | not needed ☐ |
| 6 | EPS | Monitor recovery: `HK_REQUEST(sid=1)` every 60 s | `eps.bus_voltage` and `eps.bat_soc` trending up; `eps.power_gen` > 0 W in sunlight; `eps.bat_current` (0x0109) positive (charging). Restore when bus > 28.0 V **and** SoC > 40 % | ☐ | time: ____ |
| 7 | EPS | Restore in reverse priority, bus stable 5 min between loads, each line powered before its unit: `EPS_POWER_ON(line_index=7)` (+ `AOCS_SET_MODE(mode=2)` only if `aocs.mode` (0x020F) = 0); `EPS_POWER_ON(line_index=2)` if `eps.pl_ttc_tx` = 0, then `TTC_PA_ON`; `EPS_POWER_ON(line_index=4)` if `eps.pl_fpa_cooler` = 0, the cooler itself left OFF (it runs only for imaging preparation; the STANDBY command below would switch it off); `EPS_POWER_ON(line_index=3)` if `eps.pl_payload` = 0, then `PAYLOAD_SET_MODE(mode=1)` | `eps.pl_aocs_wheels` = 1 within 5 s; after each load `eps.bus_voltage` > 27.5 V and `eps.bat_soc` > 35 %; all loads back, power budget positive | ☐ | |

With the S-band PA off, the **UHF beacon survives**: it is a separate radio, so
HK SID 11 keeps arriving (`ttc.beacon_active`, 0x0527). Nothing that FDIR or
this card opened comes back by itself: step 7 re-powers each line explicitly.

## CTG-002 AOCS Anomaly Recovery

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Assess the AOCS state: `HK_REQUEST(sid=2)` (S3.27) | `aocs.mode` (0x020F) and `aocs.att_error` (0x0217) received within 5 s — telemetry live | ☐ | mode __ err __ |
| 2 | Wheel health: `HK_REQUEST(sid=2)` | `aocs.rw1_speed` … `aocs.rw4_speed` (0x0207–0x020A) within ±6000 rpm; `aocs.rw1_temp` … `aocs.rw4_temp` (0x0218–0x021B) < 60 °C. A wheel ≥ 60 °C or oscillating > ±500 rpm/s → step 3; all nominal → step 5 | ☐ | wheel: ____ |
| 3 | Disable the failed wheel: `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8.1 func **2**) | its speed decays toward 0 rpm within 30 s; `aocs.att_error` never above 10° | ☐ | N = __ |
| 4 | Desaturate: `AOCS_DESATURATE` (S8.1 func **1**) | active wheels trend toward 0 rpm within 120 s; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` (0x0204–0x0206) < 0.5°/s; momentum < 20 % of capacity on every active wheel | ☐ | |
| 5 | Body rates stable: `HK_REQUEST(sid=2)` | `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) < 0.1°/s | ☐ | |
| 6 | Restore NOMINAL: `AOCS_SET_MODE(mode=4)` (S8.1 func **0**) | `aocs.mode` = 4 within 10 s; `aocs.att_error` < 1.0° within 120 s → recovered; otherwise step 7 | ☐ | |
| 7 | Escalation on a multi-wheel failure only: `AOCS_SET_MODE(mode=2)` — DETUMBLE | `aocs.mode` = 2 within 5 s; rates trending to 0 within 300 s; not below 2.0°/s in 300 s → EMG-001 | ☐ | not needed ☐ |

There is no SAFE_POINT mode; mode 1 is SAFE_BOOT, a post-boot propagate-only
state, not a recovery target. A star-tracker fault follows CTG-008.

## CTG-007 Reaction Wheel Anomaly

EOSAT-1 flies **four** wheels in a pyramid. Speeds are READ-ONLY
at `aocs.rw1..rw4_speed` (0x0207–0x020A); temps 0x0218–0x021B;
currents 0x0250–0x0253; bearing health 0x0284–0x0287. Speed is
commanded with `RW_SET_SPEED_BIAS` (S8.1 func **8** — the bias is
**added** to the current speed) and `AOCS_RW_RAMP_DOWN` (func
**14**, `wheel_idx` 255 = all).

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identify the wheel: `HK_REQUEST(sid=2)` (S3.27) | `aocs.rw1_speed` … `aocs.rw4_speed` (0x0207–0x020A) value and rate of change; `aocs.rw1_temp` … `aocs.rw4_temp` (0x0218–0x021B). Flag oscillation > ±500 rpm/10 s, speed > 6500 rpm or temperature > 60 °C. More than one wheel → CTG-002 step 7 | ☐ | wheel: ____ |
| 2 | Disable it: `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8.1 func **2**) | its speed starts decaying within 10 s; `aocs.att_error` (0x0217) transient ≤ 5°; `aocs.rate_roll`, `aocs.rate_pitch`, `aocs.rate_yaw` (0x0204–0x0206) < 1.0°/s | ☐ | |
| 3 | Three-wheel control: watch the AOCS reconfigure — no command | control loop reconfigured within 15 s; `aocs.att_error` back below 2.0° within 60 s; the three remaining wheels share the momentum | ☐ | |
| 4 | Desaturate the three: `AOCS_DESATURATE` (S8.1 func **1**) | active wheels toward 0 rpm over 120 s, none above 5000 rpm; rates < 0.5°/s during the manoeuvre; done when every wheel < 2000 rpm and rates < 0.2°/s | ☐ | |
| 5 | Stable pointing on three wheels: `HK_REQUEST(sid=2)` every 60 s for 5 min | `aocs.att_error` (0x0217) < 1.5° (relaxed from 1.0°); `aocs.rate_roll` (0x0204), `aocs.rate_pitch` (0x0205), `aocs.rate_yaw` (0x0206) < 0.1°/s; active wheel temperatures < 55 °C | ☐ | error: ____ ° |
| 6 | NOMINAL on three wheels: `AOCS_SET_MODE(mode=4)` (S8.1 func **0**) | `aocs.mode` (0x020F) = 4 within 15 s; `aocs.att_error` < 1.5° within 120 s | ☐ | |
| 7 | Wheel recovery, ground-authorised attempt only: `AOCS_ENABLE_WHEEL(wheel_idx=N)` (S8.1 func **3**) | smooth spin-up within 30 s, no oscillation → four-wheel control restored; otherwise stay on three. Over-temperature: watch it for 2 orbits (recoverable below 45 °C); oscillation: bearing analysis; divergence: driver electronics, no re-enable without a patch | ☐ | |

A 3-of-4 subset still spans R³, so **FINE_POINT still works** on three wheels —
flagged at `aocs.fine_degraded` (0x0299), not refused.

## CTG-008 Star Tracker Failure

EOSAT-1 carries **two** star trackers, ST1 and ST2 — this is a
redundancy switch, not a single-head loss. There is no
`AOCS_EST_SET` command and no `ss_imu` source name: the estimator
source is the read-only bitmask `aocs.est_source` (**0x02C1**;
bit0 ST, bit1 CSS, bit2 MAG, bit3 gyro), and the only estimator
command is `AOCS_EST_RESET` (S8.1 func **91**, `mode` 0 = cold,
1 = warm).

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the ST1 failure: `HK_REQUEST(sid=2)` (S3.27) | `aocs.st1_status` (0x0240) = 4 (FAILED) within 15 s; `aocs.st1_num_stars` (0x0241) = 0; record `aocs.mode` (0x020F), `aocs.att_error` (0x0217, may be rising) and the body rates (0x0204–0x0206) | ☐ | ST1: __ |
| 2 | Power on ST2: `ST2_POWER(on=1)` (S8.1 func **5**), `HK_REQUEST(sid=2)` | `aocs.st2_status` (0x0243) 0 → 1 (BOOT) within 5 s → 2 (TRACKING) within 60 s; still 1 after 60 s: wait up to 120 s in total | ☐ | |
| 3 | Select ST2: `ST_SELECT(unit=2)` (S8.1 func **6**; wire encoding 1 = ST1, 2 = ST2), `HK_REQUEST(sid=2)` 10 s later | `aocs.st2_status` = 2 (TRACKING, stable) within 15 s; `aocs.att_error` decreasing; `aocs.mode` in (or back in) the pre-failure mode | ☐ | |
| 4 | Isolate ST1: `ST1_POWER(on=0)` (S8.1 func **4**), `HK_REQUEST(sid=2)` | `aocs.st1_num_stars` (0x0241) = 0 within 15 s; `aocs.att_error` < 0.1°; `aocs.rate_roll` and `aocs.rate_yaw` < 0.01°/s; `aocs.rate_pitch` ∈ [0.053, 0.073]°/s (nadir) | ☐ | |
| 5 | Fallback, **both** trackers failed: `AOCS_SET_MODE(mode=3)` COARSE_SUN (S8.1 func **0**), `HK_REQUEST(sid=2)`, `PAYLOAD_SET_MODE(mode=0)` | `aocs.mode` = 3 within 20 s; `aocs.css_valid` (0x0248) = 1; `aocs.css_sun_x` … `aocs.css_sun_z` (0x0245–0x0247) measured; `aocs.att_error` < 5°. Tell the FD: fine pointing lost, no imaging | ☐ | not needed ☐ |
| 6 | End of procedure: a final `HK_REQUEST(sid=2)` | final AOCS state recorded; ST1 failure and ST2 activation in the anomaly report | ☐ | |

`ST_SELECT(unit=1)` would silently re-select the failed ST1: 0 is refused,
1 is ST1, 2 is ST2.

## CTG-009 Solar Array Degradation

The spacecraft **reports** a degraded string (S12 yield monitor below 70 %
in sunlight: TM(12,9) and S5 event 0x914C for A, 0x914D for B) but does
not act on it. Whether the payload goes off is the team's decision, taken
at step 4 from how serious the loss is. If nobody decides and the battery
runs down, the bus-voltage load shed takes the payload off at 25.0 V: that
is the safety net, not the plan.

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Quantify the loss: `HK_REQUEST(sid=1)` (S3.27), `GET_PARAM(param_id=0x014C)`, `GET_PARAM(param_id=0x014D)`, `GET_PARAM(param_id=0x014E)` (S20.3) | record `eps.sa_a_current` (0x0103), `eps.sa_b_current` (0x0104), `eps.power_gen` (0x0107); `eps.sa_a_yield_pct` (0x014C) and `eps.sa_b_yield_pct` (0x014D) are valid while the string's bit is set in `eps.sa_string_lit` (0x014E); `eps.pl_payload` (0x0113) still as you left it (already 0 = the load shed took it) | ☐ | yield A __ % B __ % |
| 2 | Compare the strings: `HK_REQUEST(sid=1)` three times, 30 s apart | `eps.sa_a_current` / `eps.sa_b_current` ratio (nominal 0.9–1.1): one string degraded or both | ☐ | ratio: ____ |
| 3 | Rule out attitude: `HK_REQUEST(sid=2)` | `aocs.mode` (0x020F) = 4 or 3; `aocs.att_error` (0x0217) < 2.0°; above 5° → CTG-002 first | ☐ | |
| 4 | **Decide: shed the payload or continue.** `HK_REQUEST(sid=1)`; judge the severity from the yield (row 1) and the power balance; FD announces "PAYLOAD SHED" or "CONTINUE, MONITORING" | `eps.power_gen` − `eps.power_cons` (0x0106) positive over the orbit **and** `eps.bat_soc` (0x0101) projected above 25 % at the end of the next eclipse → continue (row 7); otherwise shed (row 5) | ☐ | SHED ☐ CONTINUE ☐ SoC min __ % |
| 5 | Shed: `PAYLOAD_SET_MODE(mode=1)` (S8.1 func **26**, STANDBY); still short: `PAYLOAD_SET_MODE(mode=0)` and, if no manoeuvre is planned, `HEATER_THRUSTER(on=0)` (func **42**) | `payload.mode` (0x0600) = 1 (or 0) within 10 s; `eps.power_cons` down by ≥ 12 W; margin ≥ 3 W | ☐ | |
| 6 | Sun-optimal attitude: `AOCS_SET_MODE(mode=3)` (S8.1 func **0**, COARSE_SUN) | `aocs.mode` = 3 within 15 s; `eps.sa_a_current`, `eps.sa_b_current` and `eps.power_gen` higher than in NOMINAL | ☐ | |
| 7 | Monitoring plan: `HK_REQUEST(sid=1)` as the new baseline; one wing lost: `GET_PARAM(param_id=0x0144)` | baseline of `eps.sa_a_current`, `eps.sa_b_current`, `eps.power_gen`, `eps.bat_soc` recorded; `eps.wing_status` (0x0144) read; daily trend for 7 days | ☐ | |

## CTG-010 OBDH Watchdog Recovery

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the watchdog reset: `HK_REQUEST(sid=4)` (S3.27) | `obdh.reboot_count` (0x030A) incremented since the last known value; record `obdh.mode` (0x0300, expect 0) and `obdh.cpu_load` (0x0302, expect < 70 %) | ☐ | count: ____ |
| 1b | Only if `obdh.sw_image` (0x0311) = 0 (bootloader): `OBC_BOOT_APP` (S8.1 func **55**) — before any `HK_ENABLE` or `OBC_SET_MODE` | S1.1 + S1.7 within 15 s; `obdh.sw_image` = 1 within 15 s | ☐ | not needed ☐ |
| 2 | Post-reboot state: `HK_REQUEST(sid=4)` | `obdh.mode` (0x0300) = 0 (NOMINAL; 1 SAFE means re-initialisation found an issue — go on with caution); `obdh.cpu_load` (0x0302) < 70 % | ☐ | |
| 3 | All housekeeping: `HK_REQUEST` (S3.27) of SIDs 1, 2, 3, 4, 5, 6 | all six frames within 30 s; no subsystem in an unexpected mode or out of limits (any → its CTG card) | ☐ | |
| 4 | Time and data integrity: `HK_REQUEST(sid=2)` for `aocs.gps_fix`, `SET_TIME(cuc_seconds=T_corrected)` (S9.1), `OBC_GPS_TIME_SYNC` (S8.1 func **80**), `HK_REQUEST(sid=4)`, `REQUEST_TIME` (S9.2) | `obdh.time_ref` (0x0A13) ≠ 0 (1 GROUND or 2 GPS) within 15 s; T_obc within ±1 s of ground time; stored command queue and mass-memory partitions intact | ☐ | residual: ____ s |
| 5 | Root-cause indicators: `HK_REQUEST(sid=1)`; review the `obdh.cpu_load` (0x0302) trend and the EPS data before the reset | `eps.bus_voltage` (0x0105) > 27.0 V; transient (SEU, brief dip) → log it; systemic (repeated high CPU, memory errors) → ground software team | ☐ | cause: ____ |
| 6 | Restore NOMINAL if the OBC is in SAFE: `OBC_SET_MODE(mode=0)` (S8.1 func **50**) | `obdh.mode` (0x0300) = 0 within 10 s; `obdh.cpu_load` < 70 %; `aocs.mode` (0x020F) undisturbed | ☐ | not needed ☐ |

A reset that passes through the bootloader re-applies
`default_enabled_sids: [1, 11]` at application boot: every other SID is off
again until it is re-enabled with `HK_ENABLE` (S3.5).

## CTG-012 Overcurrent Response

Line indices run **0–8**: 0 `obc`, 1 `ttc_rx`, 2 `ttc_tx`,
3 `payload`, 4 `fpa_cooler`, 5 `htr_bat`, 6 `htr_obc`,
7 `aocs_wheels`, 8 `prop`.

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identify the tripped line(s): `HK_REQUEST(sid=1)` (S3.27) | `eps.oc_trip_flags` (0x010D) decoded: bit N = line N (bits 0–1 are the non-switchable `obc` and `ttc_rx`) | ☐ | line: ____ |
| 2 | Per-line current: `HK_REQUEST(sid=1)` | the tripped line's current (0x0118–0x011F) near 0 A — the LCL opened it; still elevated = persistent fault: do NOT re-enable, escalate. Line status (0x0110–0x0117) OFF; `eps.bus_voltage` (0x0105) > 27.0 V | ☐ | I: ____ A |
| 3 | Isolate the fault — coordinate with the affected subsystem's position (TT&C, Payload, EPS/TCS, AOCS): known state before the trip? inrush during a mode change or power-on? | likely transient → step 4; hardware damage suspected → HOLD and escalate | ☐ | |
| 4 | Reset the overcurrent flag: `EPS_RESET_OC_FLAG(line_index=N)` (S8.1 func **21**) | the line's bit of `eps.oc_trip_flags` (0x010D) clear, and still clear 5 s later | ☐ | |
| 5 | Re-enable the line: `EPS_POWER_ON(line_index=N)` (S8.1 func **19**) | line status (0x0110 + N) = 1 within 5 s; line current (0x0118 + N) back to nominal; `eps.oc_trip_flags` still clear after 30 s | ☐ | |
| 6 | Downstream recovery: `HK_REQUEST` of the owner's SID (2 AOCS, 5 Payload, 6 TT&C, 3 heaters) and `HK_REQUEST(sid=1)` | the subsystem works again; `eps.power_cons` (0x0106) shows the load; `eps.bus_voltage` > 27.0 V | ☐ | |

The LCL has normally opened the line before anyone sees the trip: this card
never needs to switch a tripped line off, only to decide whether it may come
back.

## CTG-015 Corrupted Image Recovery

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Detect and quantify: `HK_REQUEST(sid=5)` (S3.27) | `payload.checksum_errors` (0x0609) delta against the baseline; `payload.last_scene_id` (0x060C) — the affected scene; ground quick-look of its last product: missing lines, streaks, corrupt blocks?; `payload.image_count` (0x0605) recorded | ☐ | Δ errors: ____ |
| 2 | FPA check: `HK_REQUEST(sid=5)`, `HK_REQUEST(sid=3)` | `payload.fpa_temp` (0x0601) recorded and cross-checked with `tcs.temp_fpa` (0x0408); `payload.fpa_ready` (0x0610) = 1?; `tcs.cooler_fpa` (0x040C) = 1? FPA warm (not ready) → step 3; cold and ready → step 4 | ☐ | T: ____ °C |
| 3 | FPA warm — abort and cool down: `PAYLOAD_SET_MODE(mode=1)` (S8.1 func **26**), `FPA_COOLER(on=1)` (func **43**), `GET_PARAM(param_id=0x040C)`, `HK_REQUEST(sid=5)` every 60 s, `HK_REQUEST(sid=3)` | `payload.mode` (0x0600) = 1 within 10 s; `tcs.cooler_fpa` (0x040C) = 1 within 5 s; `payload.fpa_temp` falling until `payload.fpa_ready` = 1 → step 5 | ☐ | |
| 4 | Memory segments: `HK_REQUEST(sid=5)` | `payload.mem_segments_bad` (0x0612) and `payload.store_used` (0x0604) recorded. > 0 → CTG-016 marks the bad segment first; 0 with a cold FPA → transient (SEU) → step 5 | ☐ | segments: ____ |
| 5 | Delete and re-capture: `PAYLOAD_DELETE_IMAGE(scene_id=N)` (func **30**), then `PAYLOAD_CAPTURE(scene_id=N, lines=L)` (func **28**) — only with `payload.fpa_ready` = 1, no unmarked bad segment and `aocs.att_error` (0x0217) < 0.1° | the delete: `payload.store_used` falls, `payload.image_count` (0x0605) −1; the capture: `payload.image_count` +1; `payload.checksum_errors` (0x0609) does not increase | ☐ | new scene: ____ |
| 6 | Post-capture verification: `HK_REQUEST(sid=5)` | `payload.checksum_errors` no further increase; on the ground the new product's CRC32 matches the on-board transfer report and the quick-look is clean; `payload.store_used` within capacity. Log scene, error count, root cause (thermal / memory / transient) and result | ☐ | cause: ____ |

The card usually starts from the S5 event 0x0607 IMAGE_CHECKSUM_ERROR. Use the
readiness flag `payload.fpa_ready`, not a remembered temperature, to decide
whether the FPA was warm.

## CTG-017 Bus Failure Switchover

Switching the **bus** and switching the **OBC unit** are different
commands. `OBC_SELECT_BUS` (func 54) changes the CAN bus;
`OBC_SWITCH_UNIT` (func 53) fails over to the redundant OBC and is
CTG-011, not this card.

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Detect missing housekeeping: `HK_REQUEST` (S3.27) of SIDs 1, 2, 3, 4, 5, 6 | which SIDs answer and which are missing; missing from several subsystems → step 2 | ☐ | missing: ____ |
| 2 | Bus status: `HK_REQUEST(sid=4)` | `obdh.bus_a_status` (0x030F), `obdh.bus_b_status` (0x0310) (0 OK, 1 ERROR) and `obdh.active_bus` (0x030E) (0 A, 1 B) recorded. Active bus in ERROR → switch; both OK → look at the subsystems instead | ☐ | A __ B __ active __ |
| 3 | Switch the bus: `OBC_SELECT_BUS(bus=1)` from A to B, or `OBC_SELECT_BUS(bus=0)` from B to A (S8.1 func_id **54**); `HK_REQUEST(sid=4)` 15 s later | `obdh.active_bus` (0x030E) shows the new bus; `obdh.bus_a_status` and `obdh.bus_b_status` recorded | ☐ | |
| 4 | Verify all housekeeping resumes: `HK_REQUEST` of SIDs 1–6 again | every SID answers within 15 s; values sensible (no stuck values, no zeros); `eps.bat_soc` (0x0101) and `eps.bus_voltage` (0x0105) recorded; `aocs.mode` (0x020F) and `payload.mode` (0x0600) unchanged; `obdh.cpu_load` (0x0302) not high; announce "ALL HK RESTORED" | ☐ | |
| 5 | Post-switchover assessment: log the HK-loss time, the failed bus, the gap, the affected subsystems and the new bus; stay on the new bus — no switch back without engineering approval and testing | failed bus recorded for engineering | ☐ | |

After a switchover there is **no bus redundancy left** until engineering clears
the failed bus.

## CTG-019 No Telemetry at Pass Start

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the ground station is nominal: antenna tracking with valid pointing, uplink transmitter on frequency and polarisation, Doppler pre-compensation, no local RFI or weather, receiver on the expected downlink frequency | ground nominal → spacecraft-side diagnosis | ☐ | |
| 2 | TT&C TX power line, blind: `HK_REQUEST(sid=1)` (S3.27), `EPS_POWER_ON(line_index=2)` (S8.1 func **19**); wait 30 s | downlink carrier on the ground receiver? signal → step 6; weak carrier → step 4; nothing → step 3 | ☐ | |
| 3 | Transponder switch, blind: `TTC_SWITCH_REDUNDANT` (func **64**), wait 45 s; then `TTC_SWITCH_PRIMARY` (func **63**) | carrier on the redundant unit's frequency → step 6; neither unit → step 4 | ☐ | |
| 4 | PA on, blind: `TTC_PA_ON` (func **66**), wait 15 s; still nothing: `TTC_PA_OFF` (func **67**), 10 s, `TTC_PA_ON`, 15 s | downlink carrier after PA ON → step 6; still none → step 5 | ☐ | |
| 5 | Antenna, only if its deployment is uncertain or known stowed: `TTC_DEPLOY_ANTENNA` (func **69**) — irreversible burn-wire; wait 30 s | with any TM: `ttc.antenna_deployed` (0x0520) = 1 and `ttc.antenna_deployment_sensor` (0x0536) = 2; signal 15–25 dB stronger (`ttc.antenna_deployment_ready` (0x0535) = 0 beforehand means a pyro continuity fault: it will not fire). Signal → step 6; none → step 7 | ☐ | |
| 6 | Verify link quality and subsystem health: `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `ttc.link_status` (0x0501) = 2; TT&C page (ground): `ttc.rssi` (0x0502) > −126 dBm, `ttc.link_margin` (0x0503) > 3.0 dB; `ttc.pa_on` (0x0516) = 1; `ttc.pa_temp` (0x050F) < 55 °C; `ttc.antenna_deployed` = 1; `ttc.carrier_lock` (0x0510) = 1; `ttc.bit_sync` (0x0511) = 1; radio page: `ttc.eb_n0` (0x0519) > 10 dB; `eps.bus_voltage` (0x0105) > 27.0 V; `eps.pl_ttc_tx` (0x0112) = 1; `obdh.mode` (0x0300) not SAFE or EMERGENCY | ☐ | restored at step: ____ |
| 7 | Escalation, no link: `TTC_SET_TX_POWER(level=2)` (S8.1 func **68**) for the next attempt; log every blind command with its time; notify the FD and the Mission Director; book the next pass | no link after two consecutive passes → **EMG-004** (Loss of Communication) | ☐ | |

The UHF beacon is a **separate radio**: if HK SID 11 still arrives while the
S-band is silent (`ttc.beacon_active`, 0x0527), the fault is in the S-band
chain, not the OBC. The only on-board autonomy for a silent link is the
command-loss timer: it switches to the other transponder 24 h after the last
accepted telecommand, and again every further 24 h (CTG-003 step 6).

## CTG-020 Ground Station Antenna Failure

CTG-020 is an **advisory** card (`advisory: true` in
`procedure_index.yaml`) — it is not machine-runnable, and it
contains **no spacecraft telecommands**. This is a ground-segment
failure: everything is done on the ground side. Do not command the
spacecraft for it.

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the signal loss is not spacecraft-side. Last frame before the loss: `ttc.rssi` (0x0502) nominal, `ttc.link_margin` (0x0503) > 3 dB, `ttc.pa_on` (0x0516) = 1, `ttc.pa_temp` (0x050F) < 55 °C. A sudden drop to the noise floor = equipment. Check antenna tracking, LNA, downconverter, IF/baseband | ground equipment failure confirmed or strongly suspected → step 2; spacecraft side suspected → CTG-019 or CTG-003 | ☐ | |
| 2 | Attempt local ground station recovery: antenna controller reset or re-acquisition of the track; backup LNA, cables, power supplies — up to 2 min | station back → resume and log; not back in 2 min → step 3 | ☐ | result: ______ |
| 3 | Notify the Flight Director and assess the impact: "GS [station] antenna failure at [time]; spacecraft healthy and transmitting; ground cannot receive"; pass time left, pending commands, urgent data, time-critical operations | critical operations pending → step 4 now; otherwise → step 5 | ☐ | |
| 4 | Coordinate an alternate ground station (FD authorises): next windows at the other stations of the network, priority booking, orbit elements and frequency plan, matching uplink and downlink configuration | alternate station coordinated — or none available and the spacecraft safe on its own | ☐ | station: ______ |
| 5 | Replan the contact schedule: drop the failed station until it is repaired, add alternate passes, assess the 24–48 h contact time and the on-board imaging, battery and storage plans; notify engineering; log the incident | schedule replanned, incident logged | ☐ | |

The ground side's health is in `ttc.gs_equipment_status` (0x0524, a set bit =
healthy); a healthy spacecraft keeps radiating throughout.

---

# Appendix WB-B — End-of-Week Shift Log (cohort copy)

**Use:** completed by the FD at end of every shift. One sheet per
shift. Goes into cohort archive.

| Field | Entry |
|-------|-------|
| Shift date | |
| Shift FD | |
| Team | ☐ Borealis ☐ Austral |
| Pass(es) covered | |
| Procedures executed | |
| Anomalies (count + ticket IDs) | |
| FDIR rules triggered | |
| GO/NO-GO outcome | |
| Customer commitments met / deferred | |
| One-line summary for cohort archive | |
| FD signature | |

---

# Appendix WB-C — Workbook self-check

At end of Week 3, the workbook should contain:

- ☐ WB-5.0 orientation check (filled before Monday)
- ☐ WB-5.1 seven position score cards (one per MCS console)
- ☐ WB-5.3-PP pass-plan exercise output
- ☐ WB-5.4-VL voice-loop drill responses
- ☐ WB-5.4-N001 NOM-001 confirm-each-step (one per pass)
- ☐ WB-5.4-C003 CTG-003 confirm-each-step (if invoked)
- ☐ WB-5.4-N012 NOM-012 handover (one per handover)
- ☐ WB-5.4-FD flight-dynamics workshop output
- ☐ WB-5.4-Q quiz response sheet (graded)
- ☐ WB-5.5-PB LEOP pre-pass briefing checklist (one per pass)
- ☐ WB-5.5-L001 / -L006 / -L002 / -L007 / -L005 confirm-each-step (one each per pass operated)
- ☐ WB-5.5-AT anomaly tickets (≥ 1 per pass operated)
- ☐ WB-5.5-GO end-of-pass scorecard
- ☐ WB-5.5-OBS observer worksheet (one per pass observed)
- ☐ WB-5.5-HO inter-pass handover (one per position)
- ☐ WB-5.5-DB debrief reflection
- ☐ WB-5.6-PB pre-pass-set briefing
- ☐ WB-5.6-C001 through WB-5.6-C012 confirm-each-step (one each)
- ☐ WB-5.6-FPA cool-down monitor sheet
- ☐ WB-5.6-FL First Light assessment
- ☐ WB-5.6-MA multi-anomaly form (if applicable)
- ☐ WB-5.6-GO pass-set scorecard
- ☐ WB-5.6-OBS observer worksheet
- ☐ WB-5.6-HO inter-pass handover
- ☐ WB-5.6-DB debrief reflection
- ☐ WB-5.7-SA personal self-assessment
- ☐ WB-5.7-LL ≥ 3 cohort lessons-learned contributions
- ☐ WB-5.7-WI what-if reflection (if a branch replay ran)
- ☐ WB-5.7-FR final mission review prep (cohort copy)
- ☐ WB-5.7-CE course evaluation (anonymous; in the box)
- ☐ WB-A contingency confirm-each-step pages used as needed
- ☐ WB-B shift log per shift

**FD signature at end of Week 3:** _______________________

**Workbook handed to instructor:** ____ : ____ (UTC)
