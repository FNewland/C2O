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
  rungs — **BEACON 1 kbps / LOW 16 kbps / HIGH 128 kbps**
  (`ttc.tm_data_rate` 0x0506 in bps, `ttc.tm_tier` 0x0539 =
  0/1/2). LOW is the routine operations rung; HIGH is for dumps
  only and needs DOWNLINK mode on (func 79) plus elevation ≥ 10°.
  BEACON is not selectable with `TTC_SET_DATA_RATE` (S8 func 65).
  EOSAT-1 flies the **five-station** teaching baseline (`orbit.yaml`).
- **Beacon rate (kbps):** ______   **Routine LOW rate (kbps):** ______
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
| 1 | Ground Seg | Confirm the scheduled station is tracking | station = TRACKING in MPS (five-station network) | ☐ | |
| 2 | TT&C | Verify the S-band chain is radiating | `ttc.pa_on` (0x0516) = 1 and `ttc.tx_active` (0x0525) = 1 before AOS-2 min; if 0, read `ttc.tx_gate_status` (0x052B) | ☐ | |
| 3 | TT&C | At AOS, verify link lock acquired | `ttc.link_status` (0x0501) = **2** (LOCKED) within 30 s of AOS; `ttc.carrier_lock` (0x0510) = 1 | ☐ | |
| 4 | SPACON | Issue `CONNECTION_TEST` (S17.1) | S1.1 ack + S17.2 report received | ☐ | |
| 5 | SPACON | Verify full HK reporting | SIDs 1, 2, 3, 4, 5, 6 periodic (only 1 EPS and 11 Beacon are on at power-up — the rest need `HK_ENABLE`, S3.5); on-demand reads use `HK_REQUEST`, **S3.27** | ☐ | |
| 6 | AOCS | Confirm AOCS mode and rates | `aocs.mode` (0x020F) = **4** (NOMINAL, nadir-tracking); `aocs.rate_roll`/`rate_yaw` (0x0204/0x0206) < 0.05°/s, `aocs.rate_pitch` (0x0205) ≈ −0.063 ± 0.02°/s (nadir tracking rate) | ☐ | |
| 7 | EPS | Confirm battery and bus state | `eps.bat_soc` (0x0101) > 50 %, `eps.bus_voltage` (0x0105) > 27.0 V (nominal band 26–30 V; FDIR undervoltage at **24.5 V**) | ☐ | |
| 8 | Thermal | Confirm zones in band | All zones green | ☐ | |
| 9 | Payload | Confirm payload state matches plan | mode = per plan | ☐ | |
| 10 | SPACON | Log pass start in shift log | Log entry created | ☐ | |

**Off-nominal items observed:** __________________________________

___________________________________________________________________

**FD signature:** ________________   **Time complete:** _________

---

# Worksheet WB-5.4-C003 — CTG-003 TTC Link Loss Recovery (confirm each step)

**Operator:** ___________________   **Trigger time:** _________

| # | Owner | Action | Expected verification | ☐ done | Note / actual value |
|---|-------|--------|----------------------|:------:|---------------------|
| 1 | TT&C | Confirm link loss on `ttc.link_status` (0x0501) and `ttc.frame_sync` (0x0512) | link_status ≠ 2, frame sync lost | ☐ | |
| 2 | Ground Seg | Verify ground station still tracking | Antenna pointing correct, baseband nominal | ☐ | |
| 3 | SPACON | Open FDIR panel; identify the rule that fired | rule + `fdir.level` (0x0700) recorded | ☐ | |
| 4 | TT&C | Blind `HK_REQUEST(sid=6)` (S3.27), then `CONNECTION_TEST` (S17.1) | If it responds, go to step 8 | ☐ | |
| 5 | TT&C | If step 4 fails, blind `TTC_SWITCH_REDUNDANT` (S8 func 64), then `TTC_SWITCH_PRIMARY` (func 63) | `ttc.link_status` = 2 within 45 s | ☐ | |
| 6 | TT&C | Once locked, verify link quality and subsystem health: `HK_REQUEST(sid=6)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` (S3.27) | RSSI (0x0502) > −90 dBm; margin (0x0503) > 3.0 dB; bus > 27.0 V; record the active transponder (`ttc.mode` 0x0500) | ☐ | |
| 7 | TT&C | If still silent after both transponders: log every blind command, notify the Mission Director and FDS, book the next pass | 24 h no-contact timer confirmed running | ☐ | |
| 8 | SPACON | Acknowledge FDIR rule, log recovery actions | FDIR cleared, log entry | ☐ | |
| 9 | TT&C | File anomaly ticket. If no link after two consecutive passes, escalate **EMG-004** Loss of Communication | Ticket logged | ☐ | |

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

Tool: `python3 tools/orbit_tools.py predict --hours 24`. Compare
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
| `pass_override = 1` confirmed (param 0x05FF) | ☐ |
| FD has loaded LEOP procedure pack into procedure panel | ☐ |
| SPACON has reviewed the FDIR rule set on the FDIR panel (there is **no** FDIR table-load telecommand — the rule set is `subsystems/fdir.yaml` + `monitoring/`) | ☐ |
| AOCS has reviewed residual tumble rates (~1–2 °/s per axis from the separation impulse) | ☐ |
| EPS confirms SoC ~90 % (`eps.bat_soc` 0x0101); only the non-switchable `obc` (line 0) and `ttc_rx` (line 1) are ON — every switchable line defaults OFF | ☐ |
| TT&C has confirmed UHF beacon reception (`ttc.beacon_active` 0x0527 = 1); note the beacon is a separate radio from the S-band prime | ☐ |
| Ground Seg has confirmed Iqaluit antenna on-target, demodulator on the **BEACON** rung (1 000 bps, BPSK, conv(7,1/2)+RS, 1 kBd) | ☐ |
| FDS has produced 24-h pass schedule and handed to FD/TT&C/Ground Seg | ☐ |
| Anomaly ticket forms blank-printed and available at each console | ☐ |
| Voice-loop language declared (callouts in English) | ☐ |

**FD ready call (verbatim):** ________________________________

**Pass start (UTC):** _____________

---

# Worksheet WB-5.5-L001 — LEOP-001 First Acquisition of Signal & OBC Boot (confirm each step)

**Operator (TT&C lead):** ___________________   **Pass start:** ________

| # | Owner | Action | Expected verification | ☐ done | Actual note |
|---|-------|--------|----------------------|:------:|-------------|
| 1 | Ground Seg | Configure GS receiver on the BEACON rung; force pass override in MCS | GS = TRACKING_READY; `pass_override = 1` (0x05FF) | ☐ | |
| 2 | TT&C | Send first uplink: `CONNECTION_TEST` (S17.1) | S1.1 ack < 10 s; S17.2 < 10 s; `eps.pl_ttc_tx` (0x0112) = 1 (auto-TX hold-down armed) | ☐ | |
| 3 | TT&C | Verify carrier lock and link quality | `ttc.link_status` (0x0501) = **2** (LOCKED) < 30 s; `ttc.rssi` (0x0502) > −110 dBm; `ttc.link_margin` (0x0503) > 3 dB | ☐ | |
| 4 | SPACON | Request beacon SID: `HK_REQUEST(sid=11)` (**S3.27**) | Beacon received; `obdh.sw_image` (0x0311) = 0 (BOOTLOADER) < 10 s | ☐ | |
| 5 | SPACON | Boot OBC into application: `OBC_BOOT_APP` (S8.1 func_id 55) | S1.1 ack + S1.7 < 5 s; `obdh.sw_image` = 1 < 15 s. Boot re-applies `default_enabled_sids: [1, 11]` — **only SIDs 1 and 11 stream** | ☐ | |
| 5a | SPACON | Enable the platform SIDs: `HK_ENABLE(sid=3)`, `(sid=4)`, `(sid=6)` (**S3.5**) | SIDs 3 (60 s), 4 (8 s), 6 (8 s) begin within one structure interval | ☐ | |
| 5b | TT&C | Clear the forced beacon tier, then select LOW: `TTC_SET_BEACON_MODE(on=0)` (S8 func 70), `TTC_SET_DATA_RATE(rate=0)` (S8 func 65) | `ttc.beacon_mode` (0x0521) = 0; `ttc.tm_data_rate` (0x0506) = 16000 bps; `ttc.tm_tier` (0x0539) = 1. Re-configure the ground demod to 16 kBd first | ☐ | |
| 6 | SPACON | Synchronise onboard time: `SET_TIME(cuc_seconds=T_corrected)` (S9.1), then `REQUEST_TIME` (S9.2) | Ack + complete < 5 s; \|T_obc − T_gnd\| < 1 s | ☐ | |
| 7 | SPACON | Request EPS HK: `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) 26–30 V; `eps.bat_soc` (0x0101) > 50 % | ☐ | |
| 8 | TT&C | Log times — AOS, override, first accepted TC, app boot, time-sync residual, HK values | All times recorded | ☐ | |

**Recorded values:**
- AOS time (UTC): ____________
- Override engaged: ____________
- First accepted TC: ____________
- App boot complete: ____________
- Time-sync residual: ____ s
- `eps.bus_voltage`: ____ V    `eps.bat_soc`: ____ %

**Common mistakes to avoid (instructor recap):**
- Forgetting `pass_override` before TCs.
- Sending non-bootloader-allowlisted TCs before app boot (gets S1.8
  failure code **0x0006**, "Not permitted in bootloader"). `SET_TIME`
  is one of them.
- Letting the **5-minute** auto-TX hold-down (`auto_tx_hold_s` = 300 s,
  re-armed by every accepted TC) expire mid-procedure.
- Trying `TTC_SET_DATA_RATE` before clearing beacon mode — refused with
  0x0007; application boot does **not** clear it.
- Expecting SIDs 2 and 5 to appear after step 5 (they don't — SID 2 is
  enabled in LEOP-007 and SID 5 in commissioning, once their lines are
  powered), or expecting any
  SID other than 1 and 11 without an explicit `HK_ENABLE` (S3.5).

**Exit criterion met?** ☐ yes ☐ no   **FD signature:** _______________

---

# Worksheet WB-5.5-L006 — LEOP-006 Time Synchronisation (confirm each step)

**Operator (SPACON):** ___________________

| # | Action | Expected verification | ☐ done | Note |
|---|--------|----------------------|:------:|------|
| 1 | `HK_REQUEST(sid=4)` (S3.27); read onboard time from `obdh.obc_time` (0x0309) | timestamp recorded | ☐ | |
| 2 | Issue `REQUEST_TIME` (**S9.2**) for the TM(9,2) report, **and** `HK_REQUEST(sid=6)` for `ttc.range_km` (0x0509) — SID 6 is the structure that carries the slant range | T_obc recorded; TM(9,2) agrees with 0x0309 | ☐ | |
| 3 | Compute OWLT = `ttc.range_km` / 299792.458 × 1000 ms (expect **3–22 ms**), then Δt = T_obc − (T_gnd − OWLT) | OWLT (ms): ______  Δt (s): ______ | ☐ | |
| 4 | Issue `SET_TIME(cuc_seconds=T_corrected)` (**S9.1**) — the argument goes *inside* the backticks; a bare `SET_TIME` packs cuc_seconds = 0, an epoch reset | ack + complete < 5 s, no S1.2 | ☐ | |
| 5 | `REQUEST_TIME` (S9.2) again; verify residual < 1.0 s vs ground reference (LEOP threshold; NOM-008 tightens it in nominal ops) | residual (s): ______ | ☐ | |
| 6 | Enable GPS navigation HK `HK_ENABLE(sid=12)` (S3.5); once `aocs.gps_fix` (0x0274) ≥ 2, discipline the clock with `OBC_GPS_TIME_SYNC` (S8.1 func **80**) — ground set first, GPS second | `obdh.time_ref` (0x0A13) = 2 (GPS) within 15 s; no fix yet → next contact | ☐ | |

**Exit criterion met?** ☐ yes ☐ no

---

# Worksheet WB-5.5-L002 — LEOP-002 Initial Health Check (confirm each step)

**Operator (SPACON consolidates):**  ___________________

| Subsystem | Operator | Tab read | Status reported | ☐ done | Note |
|-----------|----------|----------|-----------------|:------:|------|
| OBDH | SPACON | obdh | ☐ OK ☐ NOT-OK | ☐ | |
| EPS | EPS | eps | ☐ OK ☐ NOT-OK | ☐ | |
| TCS | Thermal | tcs | ☐ OK ☐ NOT-OK | ☐ | |
| TT&C | TT&C | ttc | ☐ OK ☐ NOT-OK | ☐ | |
| AOCS | AOCS | eps (line flag 0x0117) | ☐ dark (line OFF until LEOP-007) ☐ powered early | ☐ | |
| Payload | Payload | eps (line flag 0x0113) | ☐ dark (line OFF until COM-009) ☐ powered early | ☐ | |

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
| 1 | EPS | Verify EPS baseline: `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) 26–30 V; `eps.bat_soc` (0x0101) > 60 %; `eps.power_gen` (0x0107) > 0 W | ☐ | |
| 2 | EPS | Heaters **only if needed**: `EPS_POWER_ON(line_index=5)` (S8.1 func_id **19**) if `tcs.temp_battery` (0x0407) < +5 °C; `EPS_POWER_ON(line_index=6)` if `tcs.temp_obc` (0x0406) < 0 °C | `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc` (0x0116) = 1 for each line energised | ☐ | lines energised: ____ |
| 3 | EPS / AOCS | Energise the AOCS suite line and enable its HK: `EPS_POWER_ON(line_index=7)` (func 19), then `HK_ENABLE(sid=2)` (**S3.5**) | `eps.pl_aocs_wheels` (0x0117) = 1; SID 2 emitting. The wheels stay DISABLED: `aocs.wheels_enabled` (0x0260) = 0 until COM-004 | ☐ | |
| 4 | AOCS | Enable the DETUMBLE legs and the GPS receiver: `S2_AOCS_MAGNETOMETER(device_id=521, state=1)`, `MTQ_ENABLE(enable=1)` (S8.1 func_id **9**), `S2_AOCS_GPS_RECEIVER(device_id=527, state=1)` | `aocs.mtq_enabled` (0x025E) = 1 | ☐ | |
| 5 | AOCS | Command DETUMBLE: `AOCS_SET_MODE(mode=2)` (S8.1 func_id **0**) — mode **2 = DETUMBLE** | `aocs.mode` (0x020F) = 2; `aocs.mag_enabled` (0x025C) = 1, field 5–70 µT; `aocs.rate_roll/pitch/yaw` (0x0204–0x0206) decreasing | ☐ | |
| 6 | EPS | Confirm the exit power state: `HK_REQUEST(sid=1)` | `eps.pl_payload` (0x0113), `eps.pl_fpa_cooler` (0x0114), `eps.pl_prop` (0x014A) = 0; power margin positive | ☐ | |
| 7 | SPACON | Log all step times, rates and line currents | recorded | ☐ | |

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
| 1 | Confirm DETUMBLE active and record the rates: `HK_REQUEST(sid=2)` (S3.27) | `aocs.mode` (0x020F) = 2 (DETUMBLE); rates roll/pitch/yaw: __/__/__ °/s | ☐ | |
| 2 | Watch B-dot convergence — command nothing. This is **slow**: the 0.5°/s guard takes ~1 200 s, and a full 14°/s separation tumble ~3.5e3 s | rates decreasing on all axes; `aocs.mag_field_total` (0x0277) non-zero | ☐ | |
| 3 | Observe the **automatic** handover: rates below 0.5°/s for 30 s → mode 3 by itself. Do **not** send `AOCS_SET_MODE(mode=3)` | `aocs.mode` = 3 (COARSE_SUN) within 1800 s | ☐ | time: ____ |
| 4 | Verify the sun hold: `HK_REQUEST(sid=2)` every 60 s for 5 min | `aocs.att_error` (0x0217) < 15°; `aocs.css_sun_confidence` (0x0215) > 0.5; rates < 0.5°/s | ☐ | |
| 5 | Verify power balance improved: `HK_REQUEST(sid=1)` | `eps.power_gen` (0x0107) > 40 W; margin `eps.power_margin_w` (0x0135): ____ W | ☐ | |
| 6 | Log the final state. The spacecraft stays in COARSE_SUN: no star tracker is powered until COM-003 | error: ____ ° | ☐ | |

**Exit criterion met?** ☐ yes ☐ no

---

# Worksheet WB-5.5-L003 — LEOP-003 Initial Orbit Determination and End of LEOP (confirm each step)

**Operator (FDS, with the FD for step 5):**  ___________________

| # | Action | Verification | ☐ done | Note |
|---|--------|--------------|:------:|------|
| 1 | Request the GPS navigation report: `HK_REQUEST(sid=12)` (S3.27) | `aocs.gps_fix` (0x0274) ≥ 2; `aocs.gps_num_sats` (0x0276) ≥ 4 | ☐ | PDOP: ____ |
| 2 | Read the position: `GET_PARAM(param_id=0x0212)` (S20.3) and the ECEF state 0x0231–0x0236 | `aocs.gps_alt` 495–540 km | ☐ | alt: ____ km |
| 3 | FDS: compare with the launcher-predicted orbit | i within 0.2° of 97.39°; e < 0.01; LTAN within 15 min of 10:00 | ☐ | i: ____ ° |
| 4 | Send the refined TLE to the ground tools (planner, FDS, stations) — **nothing is uploaded to the spacecraft** | pass predictions refreshed | ☐ | |
| 5 | FD: GO/NO-GO poll, then **declare COMMISSIONING by telecommand**: `SYS_SET_MISSION_PHASE(phase=5, flags=0)` (S8.1 func **120**) — nothing on board advances the phase past 4 | `eps.spacecraft_phase` (0x0129) = 5 (COMMISSIONING) < 5 s | ☐ | |

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
| Antenna confirmed deployed (`ttc.antenna_deployed` 0x0520 = 1) | ☐ |
| Battery heater line ON (`eps.pl_htr_bat` 0x0115 = 1) | ☐ |
| AOCS wheels line ON, AOCS through DETUMBLE (2) into COARSE_SUN (3) | ☐ |
| Body rates < 0.5°/s on all axes; `aocs.att_error` < 5° | ☐ |
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
| Spacecraft in phase 4 (LEOP complete), `eps.spacecraft_phase` (0x0129) = 4 | ☐ |
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
| 1 | Baseline bus voltage — `HK_REQUEST(sid=1)` (S3.27) | `eps.bus_voltage` (0x0105) ∈ [27.5, 28.5] V | ☐ | V: ____ |
| 2 | Battery V & SoC — `GET_PARAM(param_id=0x0100)`, `GET_PARAM(param_id=0x0101)` (S20.3) | `eps.bat_voltage` ∈ [26.5, 29.2] V (8S pack: 21.5 V at 0 %, 26.4 V nominal, 29.2 V at 100 %); `eps.bat_soc` > 70 % | ☐ | V: ____ SoC: ____ |
| 3 | Solar array sunlit performance | `eps.power_gen` (0x0107) ∈ [40, 65] W (peak whole-spacecraft 88.6 W; wings 0.120 m² each at 267.9 W/m² EOL) | ☐ | ____ W |
| 4 | Eclipse discharge monitoring | `power_gen` ~0 W < 30 s of entry; SoC drop < 1.5 %/min; `bus_voltage` > 27.0 V mid-eclipse | ☐ | |
| 5 | Eclipse exit charge recovery | `power_gen` > 35 W < 60 s; SoC rising < 120 s | ☐ | |
| 6 | Power budget verification — orbit-average gen > cons | nominal orbit-average load ≈ **28.8 W** against ≈ 45.1 W generation at the worst-generation beta, β = −31.2° (margin +16.3 W, ratio 1.57; 1.38 while imaging); end-of-eclipse SoC > 50 % on the **100 Wh** pack | ☐ | margin: ____ W |
| 7 | Bus regulation under load transient — record `eps.pl_htr_bat` (0x0115), then `EPS_POWER_ON(line_index=5)` (S8.1 func_id **19**), and `EPS_POWER_OFF(line_index=5)` (func **20**) only if the line was off at entry. Not the payload: its line is OFF until COM-009 | bus stays in [26.5, 29.5] V, returns to [27.0, 29.0] V; line back to its entry state | ☐ | min V: ____ |

**Exit?** ☐ yes ☐ no   **GO COM-002:** ☐

---

# Worksheet WB-5.6-C002 — COM-002 TCS Verification (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Thermal HK — `HK_REQUEST(sid=3)` (S3.27; SID 3 = TCS, 60 s cadence) | `tcs.temp_obc` (0x0406) ∈ [−5, +45] °C; `tcs.temp_battery` (0x0407) ∈ [+5, +35] °C; `tcs.temp_fpa` (0x0408) reported | ☐ | obc:__ bat:__ fpa:__ |
| 2 | Exercise each heater with its line powered — `EPS_POWER_ON(line_index=5)` then `HEATER_BATTERY(on=1)` / `(on=0)` (S8.1 func **40**); `EPS_POWER_ON(line_index=6)` then `HEATER_OBC(on=1)` / `(on=0)` (func **41**); switch each line back off only if it was off at entry | `eps.pl_htr_bat` (0x0115) / `eps.pl_htr_obc` (0x0116) = 1; zone temperature rising or stable; lines restored | ☐ | |
| 3 | Read the autonomous battery thermostat thresholds — `GET_PARAM(param_id=0x0410)`, `GET_PARAM(param_id=0x0411)` (S20.3) | ON at +5 °C, OFF at +10 °C; the card reads them, it does not change them | ☐ | |
| 4 | Confirm radiator performance via TCS zone response in eclipse | zones stable, no runaway | ☐ | |

**Exit?** ☐ yes ☐ no   **GO COM-005:** ☐

---

# Worksheet WB-5.6-C005 — COM-005 AOCS Mode Transitions (confirm each step)

**Mode codes** (`aocs/aocs_mode_codes.yaml`, canonical): 0 OFF,
1 SAFE_BOOT, 2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL, 5 FINE_POINT,
6 SLEW, 7 DESAT, 8 ECLIPSE, 9 INERTIAL. Every transition is
`AOCS_SET_MODE(mode=N)` (S8.1 **func_id 0**).

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Latch the commanded mode: `AOCS_SET_MODE(mode=4)` — the AOCS has flown NOMINAL since COM-004 | `aocs.mode` (0x020F) = 4 (or 8 in eclipse); `aocs.commanded_mode` (0x0297) = 4; att_error < 1.0° | ☐ | |
| 2 | Read the FINE precondition mask: `AOCS_FINE_READY_CHECK` (S8.1 func **89**) | `aocs.fine_ready` (0x02C5) = 0. Bit 1 = *fewer than three* wheels — a 3-of-4 set still flies FINE, flagged at `aocs.fine_degraded` (0x0299) | ☐ | mask: ____ |
| 3 | Transition to FINE_POINT (`AOCS_SET_MODE(mode=5)`), then back to NOMINAL (`AOCS_SET_MODE(mode=4)`) | mode = 5 within 30 s; att_error < 0.1° within 300 s; then mode = 4 within 30 s | ☐ | error: ____ ° |
| 4 | INERTIAL and back: `AOCS_SET_MODE(mode=9)`, then `AOCS_SET_MODE(mode=4)` | mode 9, then mode 4, each within 30 s | ☐ | |
| 5 | Command the COARSE_SUN hold (`AOCS_SET_MODE(mode=3)`), then **wait** for the automatic return | mode 3 and `aocs.mode_demoted` (0x0298) = 1; then mode 4 by itself within 1800 s and 0x0298 = 0 | ☐ | |
| 6 | Desaturate: `AOCS_DESATURATE` (S8.1 func **1**) — DESAT exits by itself | mode 7 (DESAT), then back to 4 within 900 s with no command | ☐ | |

**Exit?** ☐ yes ☐ no

---

# Worksheet WB-5.6-C006 — COM-006 TTC Link Verification (confirm each step)

The TM rate ladder has exactly three rungs: **BEACON 1 kbps /
LOW 16 kbps / HIGH 128 kbps**. BEACON is not selectable with
`TTC_SET_DATA_RATE` — its baseline comes from the LEOP-001 pass.

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 0 | Configure the S-band chain: `EPS_POWER_ON(line_index=2)` (func 19), `TTC_PA_ON` (func **66**), `TTC_SET_BEACON_MODE(on=0)` (func **70**), `TTC_DEPLOY_ANTENNA` (func **69**) | `eps.pl_ttc_tx` (0x0112) = 1; `ttc.pa_on` (0x0516) = 1; `ttc.beacon_mode` (0x0521) = 0; `ttc.antenna_deployed` (0x0520) = 1; `ttc.tx_active` (0x0525) = 1 (else read `ttc.tx_gate_status` 0x052B) | ☐ | |
| 1 | Baseline the primary transponder at LOW: `TTC_SET_DATA_RATE(rate=0)` (S8.1 func **65**) | `ttc.link_status` (0x0501) = **2** (LOCKED); `ttc.tm_data_rate` (0x0506) = 16000 bps; `ttc.tm_tier` (0x0539) = 1; `ttc.link_margin` (0x0503) > 6 dB (expect **55–59 dB** at 30° — this link is not power-limited) | ☐ | ____ dB |
| 2 | Step to HIGH: `TTC_SET_DOWNLINK_MODE(on=1)` (func **79**) then `TTC_SET_DATA_RATE(rate=1)` (func 65) | `tm_data_rate` = 128000 bps; `tm_tier` = 2; `ttc.tm_symbol_rate` (0x053B) = 64000 Bd (QPSK); margin expect **45–48 dB** at 30° | ☐ | ____ dB |
| 3 | Compute the rung step: margin(LOW) − margin(HIGH) | **10.5 ± 0.5 dB**. Anything else is a modelling error, not a link problem | ☐ | step: ____ dB |
| 4 | Below 10° elevation (`ttc.contact_elevation` 0x050A), attempt HIGH again | Command **rejected**, S1.8 error 0x0007 naming the elevation gate; rate stays 16000 bps. This is correct behaviour, not an anomaly | ☐ | |
| 5 | Safe the link: `TTC_SET_DATA_RATE(rate=0)`, `TTC_SET_DOWNLINK_MODE(on=0)`, `TTC_SWITCH_PRIMARY` (func **63**) | `tm_tier` = 1, `ttc.tm_tier_cmd` (0x053A) = 1, `ttc.downlink_mode` (0x053C) = 0. Antenna stays deployed and the PA stays ON | ☐ | |
| 6 | Record margins at both operational rungs in the shift log | recorded | ☐ | |

**Exit?** ☐ yes ☐ no

---

# Worksheet WB-5.6-C007 — COM-007 OBDH Checkout (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | Verify the watchdog: `OBC_DIAGNOSTIC` (S8.1 func **61**), `GET_PARAM(param_id=0x0316)` (S20.3). (There is no `OBC_WATCHDOG_KICK` command) | diagnostic reply: watchdog armed; `obdh.last_reboot_cause` = 0; `obdh.reboot_count` (0x030A) unchanged | ☐ | |
| 2 | Read and verify mass-memory usage — `HK_REQUEST(sid=4)` (S3.27) | `obdh.mmm_used` (0x0303, %) as expected; payload store `payload.mem_used_mb` (0x060B) of `payload.mem_total_mb` (0x060A) | ☐ | used: ____ MB |
| 3 | Baseline the memory error and SEU counters — `GET_PARAM(param_id=0x031E)`, `GET_PARAM(param_id=0x0319)` (S20.3); then the mode excursion `OBC_SET_MODE(mode=1)`, `OBC_SET_MODE(mode=0)` (func **50**) | counters not incrementing between reads; `obdh.mode` (0x0300) back to 0 — the card ends in NOMINAL | ☐ | |
| 4 | Verify bus A and bus B health | `obdh.bus_a_status` (0x030F) = 0 and `obdh.bus_b_status` (0x0310) = 0 (0 = OK); active bus at `obdh.active_bus` (0x030E) | ☐ | |

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
| 1 | Read the FDIR state — `GET_PARAM(param_id=0x0700)` (S20.3) | `fdir.level` = 0 (0 nominal, 1 caution, 2 warning, 3 critical); `fdir.active_alarms` (0x0701) = 0 | ☐ | |
| 2 | Review the rule set on the FDIR panel against `subsystems/fdir.yaml` | key thresholds confirmed: `eps.bus_voltage` < **24.5 V**, `eps.bat_soc` < 20 % / < 15 %, `aocs.att_error` > 5° sustained 420 s, `obdh.temp` > 65 °C | ☐ | count: ____ rules |
| 3 | Enable/verify the S12 monitoring service — `MON_ENABLE` (**S12.1**), `MON_REPORT_DEFS` (S12.12) | definition list returned; alarms visible in the MCS | ☐ | |
| 4 | Functional test of the commanded load-shed latch: `EPS_EMERGENCY_LOAD_SHED(stage=1)` (S8.1 func **25**), then `EPS_EMERGENCY_LOAD_SHED(stage=0)`. Never stage 2 or 3 here — stage 3 sheds `ttc_tx` | stage 1: `eps.load_shed_stage` (0x0134) = 1 and **latches**, event 0x0106; stage 0: back to 0 and **no line re-powered** | ☐ | |
| 5 | Confirm no residual protection state: `GET_PARAM(param_id=0x0700)`, `HK_REQUEST(sid=1)`, `HK_REQUEST(sid=4)` | `fdir.level` = 0; `eps.load_shed_stage` = 0; `obdh.mode` (0x0300) = 0 — no OBC-mode excursion | ☐ | |

**Exit?** ☐ yes ☐ no

---

# Worksheet WB-5.6-C009 — COM-009 Payload Power-On (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | FD GO confirmed | recorded | ☐ | |
| 2 | Energise the payload line: `EPS_POWER_ON(line_index=3)` (S8.1 func_id **19**) | `eps.pl_payload` (0x0113) = 1 < 5 s; `eps.line_current_3` (0x011B) within envelope — standby is 2.4 W, i.e. ≈ **0.09 A** at 28 V (the overcurrent trip on this line is 2.5 A) | ☐ | I: ____ A |
| 3 | Command STANDBY: `PAYLOAD_SET_MODE(mode=1)` (S8.1 func_id **26**) | `payload.mode` (0x0600) = 1 (STANDBY). Modes: 0 OFF, 1 STANDBY, 2 IMAGING, **3 CALIBRATION** | ☐ | |
| 4 | Enable payload HK: `HK_ENABLE(sid=5)` (**S3.5**), then `HK_REQUEST(sid=5)` (S3.27) | SID 5 periodic within one 8 s interval; `payload.imager_status` (0x0611) no fault bits; `payload.fpa_temp` (0x0601) valid, +8 to +14 °C | ☐ | |
| 5 | Verify storage initialised | `payload.mem_used_mb` (0x060B) of `payload.mem_total_mb` (0x060A) = 20000 MB; `payload.product_count` (0x0648) | ☐ | ____ MB |

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
| 1 | Record the pre-activation state; cooler OFF | `payload.fpa_temp` (0x0601) at the uncooled equilibrium +8 to +14 °C; `payload.mode` (0x0600) = 1 | ☐ | T_fpa: ____ °C |
| 2 | Enable the cooler: `FPA_COOLER(on=1)` (S8.1 func_id **43**) | `tcs.cooler_fpa` (0x040C) = 1 **and** `eps.pl_fpa_cooler` (0x0114) = 1 — both, or the cooler is not actually running | ☐ | |
| 3 | Verify the power draw — `HK_REQUEST(sid=1)` (S3.27) | `eps.power_cons` (0x0106) up **14–16 W**; `payload.cooler_pwr` (0x0602) ≈ 15 W; `eps.bus_voltage` (0x0105) > 27.0 V | ☐ | ____ W |
| 4 | Monitor the ramp (exponential, not linear — a slower reading at T+5 than at T+2 is expected) | T+2 min < +4 °C; T+5 min < −8 °C | ☐ | T at 5 min: __ °C |
| 5 | Monitor settling | T+10 min ∈ [−16.0, −14.0] °C; T+15 min ∈ [−16.0, −15.0] °C. A reading below −16.5 °C is a **control fault**, not an over-performing cooler | ☐ | T at 15 min: __ °C |
| 6 | Verify readiness and margin | `payload.fpa_ready` (0x0610) = 1 (60 s hysteresis); `payload.fpa_setpoint` (0x0631) = −15.0; `payload.cooler_margin_k` (0x064B) > 0 (expect ≈ +5 K); floor at `payload.cooler_floor_c` (0x064A) | ☐ | margin: ____ K |
| 7 | Hold through eclipse | T_fpa stays in [−16.5, −14.5] °C; bus > 27.0 V | ☐ | |

**If `cooler_margin_k` ≤ 0:** the cooler physically cannot reach the
commanded setpoint at the present sink and load. The answer is a
**warmer setpoint**, not more waiting.

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
| 1 | Close the shutter: `PAYLOAD_SET_SHUTTER(position=0)` (S8.1 func **119**) | `payload.shutter_pos` (0x063C) = 0 (closed) | ☐ | |
| 2 | Dark set: `PAYLOAD_SET_MODE(mode=1)` (func 26), `PAYLOAD_CAL_LAMP(on=0)` (func **95**), `PAYLOAD_START_CALIBRATION(mode=0)` (func **37**, 0 = DARK) | `payload.mode` = 3 (CALIBRATION); `payload.calibration_active` (0x062A) = 1; on completion S5 event **0x060B CALIBRATION_COMPLETE**; `payload.dark_frame_cnt` (0x0642) > 0 | ☐ | frames: ____ |
| 3 | Flat set: `PAYLOAD_SET_SHUTTER(position=1)` (func 119), `PAYLOAD_CAL_LAMP(on=1)` (func 95), `PAYLOAD_START_CALIBRATION(mode=1)` (func 37, 1 = FLAT) | `payload.cal_lamp_on` (0x0615) = 1; `payload.bias_frame_cnt` (0x0643) > 0; lamp back OFF afterwards | ☐ | frames: ____ |
| 4 | Verify the correction set is valid across the four bands | `payload.cal_valid_mask` (0x0646) bits 0–3 (blue/green/red/nir) all set; `payload.snr` (0x0616) recorded | ☐ | mask: ____ |
| 5 | Calibration-site overpass: `AOCS_FINE_READY_CHECK` (func 89), then `AOCS_SET_MODE(mode=5)` (func 0) — FINE_POINT is mode **5** | `aocs.fine_ready` (0x02C5) = 0; `aocs.mode` (0x020F) = 5 | ☐ | |
| 6 | Return: `PAYLOAD_SET_MODE(mode=1)` STANDBY, shutter OPEN, `AOCS_SET_MODE(mode=4)` NOMINAL | `payload.mode` = 1; `payload.shutter_pos` = 1; `aocs.mode` = 4 | ☐ | |

**Exit?** ☐ yes ☐ no   **GO COM-012:** ☐

---

# Worksheet WB-5.6-C012 — COM-012 First Light (confirm each step)

| # | Action | Expected | ☐ | Note |
|---|--------|----------|:-:|------|
| 1 | FD GO for First Light | recorded | ☐ | |
| 2 | AOCS to FINE_POINT: `AOCS_FINE_READY_CHECK` (func 89), `AOCS_SET_MODE(mode=5)` (func 0) | `aocs.fine_ready` (0x02C5) = 0; `aocs.mode` (0x020F) = 5 | ☐ | |
| 3 | Verify the FPA is at temperature | `payload.fpa_ready` (0x0610) = 1; `payload.fpa_temp` (0x0601) ∈ [−16.5, −14.5] °C | ☐ | T: ____ °C |
| 4 | Verify the payload is ready and record the baselines: `HK_REQUEST(sid=5)` (S3.27) | `payload.mode` (0x0600) = 1; `payload.store_used` (0x0604) < 97 %; record `payload.image_count` (0x0605) and `payload.mem_used_mb` (0x060B) | ☐ | count: ____ |
| 5 | Command IMAGING and capture: `PAYLOAD_SET_MODE(mode=2)` (func **26**), then `PAYLOAD_CAPTURE(scene_id=1, lines=2048)` (S8.1 func **28**) | S1.1 accept + S1.7 complete; S5 event 0x0613 IMAGE_CAPTURED. 2048 lines at 244 Hz = 8.4 s ≈ 59 km along-track at 7.06 km/s | ☐ | scene: ____ |
| 6 | Verify the product stored | `payload.mem_used_mb` (0x060B) increased; `payload.product_count` (0x0648) +1; size ≈ **4 MB** (`image_size_mb`, the courseware abstraction) | ☐ | ____ MB |
| 7 | Return to STANDBY (`PAYLOAD_SET_MODE(mode=1)`), then downlink over Service 13: `TTC_SET_DOWNLINK_MODE(on=1)`, `TTC_SET_DATA_RATE(rate=1)`, `S13_CREATE_TRANSFER(scene_id=1, size_mb=0)` … `S13_END_TRANSFER(transfer_id=T)`, then back to LOW | 128000 bps; `payload.transfer_active` (0x062D) = 1, `payload.transfer_progress` (0x062E) rising, then 0x062D = 0; CRC-32 OK on the ground | ☐ | rx time: ______ |
| 8 | Quality assessment (next pass if needed) | mean DN, contrast, geo-registration; `payload.last_scene_quality` (0x060D); `aocs.geoloc_err_m` (0x02C7) | ☐ | quality: ____ |

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
| Image size (MB) — expect ~4 | |
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
| FPA cooler at its commanded setpoint (−15 °C default), `payload.fpa_ready` (0x0610) = 1, `cooler_margin_k` > 0 | ☐ |
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

| # | Owner | Action | Verification | ☐ | Note |
|---|-------|--------|--------------|:-:|------|
| 1 | EPS | Confirm `eps.bus_voltage` (0x0105) below the FDIR undervoltage threshold **24.5 V** (in-model shed starts at 25.0 V; bus warning 27.0 V, bus critical 25.0 V) | recorded | ☐ | V: ____ |
| 2 | EPS | Report to FD; recommend priority-1 shed | recommendation logged | ☐ | |
| 3 | FD | GO for load shed | granted | ☐ | |
| 4 | EPS | Priority 1 — payload OFF: `PAYLOAD_SET_MODE(mode=0)` (S8.1 func **26**) | `payload.mode` (0x0600) = 0 | ☐ | |
| 5 | EPS | Priority 2 — cooler OFF: `FPA_COOLER(on=0)` (func **43**) | `tcs.cooler_fpa` (0x040C) = 0 | ☐ | |
| 6 | EPS | Priority 3 — PA off: `TTC_PA_OFF` (func **67**). Note the S-band TM stops but the **UHF beacon survives** — it is a separate radio on the non-switchable `ttc_rx` line, so HK SID 11 keeps arriving | `ttc.pa_on` (0x0516) = 0, `ttc.beacon_active` (0x0527) still 1 | ☐ | |
| 7 | EPS | Priority 4 — wheels line off: `EPS_POWER_OFF(line_index=7)` (func **20**) | `eps.pl_aocs_wheels` (0x0117) = 0 | ☐ | |
| 8 | EPS | (Last resort) staged shed `EPS_EMERGENCY_LOAD_SHED(stage=N)` (S8.1 func **25**, stages 1–3) or `OBC_SET_MODE(mode=2)` EMERGENCY (func **50**) | `eps.load_shed_stage` (0x0134) | ☐ | |
| 9 | EPS | Verify SoC stops dropping; bus recovers above 25.5 V (shed threshold + 0.5 V hysteresis; auto-restore then walks the lines back one per tick, in reverse shed order) | recovery time: ____ s | ☐ | |
| 10 | SPACON | Acknowledge FDIR rule; log | logged | ☐ | |
| 11 | EPS | File anomaly ticket | ticket #: ____ | ☐ | |

## CTG-002 AOCS Anomaly Recovery

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Read which sensor / actuator is faulted from the FDIR panel; `HK_REQUEST(sid=2)` (S3.27) | identified: ____________ | ☐ | |
| 2 | Command the sun-safe hold: `AOCS_SET_MODE(mode=3)` (S8.1 func **0**) — mode **3 = COARSE_SUN**. (There is no SAFE_POINT mode; mode 1 is SAFE_BOOT, a post-boot propagate-only state, not a recovery target) | `aocs.mode` (0x020F) = 3 | ☐ | |
| 3 | Verify the spacecraft is stable | rates (0x0204–0x0206) < 0.05°/s; `aocs.att_error` (0x0217) < 5°; no further alarm | ☐ | |
| 4 | If momentum is the problem, dump it: `AOCS_DESATURATE` (S8.1 func **1**) — DESAT is mode 7. Budget **20–50 min** for a full dump; imaging is inhibited and the spacecraft returns to its pre-desat mode | `aocs.h_body_mag` (0x02B9) falling; `aocs.desat_ineffective` (0x029C) = 0 | ☐ | |
| 5 | Follow the specific sub-procedure for the failed component (CTG-007 wheel / CTG-008 star tracker) | sub-procedure ID: ____ | ☐ | |
| 6 | Restore NOMINAL: `AOCS_SET_MODE(mode=4)`; escalate to DETUMBLE (`mode=2`) only on multi-wheel failure | `aocs.mode` = 4 | ☐ | |
| 7 | File anomaly ticket | ticket #: ____ | ☐ | |

## CTG-007 Reaction Wheel Anomaly

EOSAT-1 flies **four** wheels in a pyramid. Speeds are READ-ONLY
at `aocs.rw1..rw4_speed` (0x0207–0x020A); temps 0x0218–0x021B;
currents 0x0250–0x0253; bearing health 0x0284–0x0287. Speed is
commanded with `RW_SET_SPEED_BIAS` (S8.1 func **8** — the bias is
**added** to the current speed) and `AOCS_RW_RAMP_DOWN` (func
**14**, `wheel_idx` 255 = all).

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identify the affected wheel (index 0–3) from speed, current and bearing health | wheel: ____ | ☐ | |
| 2 | Disable it: `AOCS_DISABLE_WHEEL(wheel_idx=N)` (S8.1 func **2**) | `aocs.rwN_enabled` (0x0254–0x0257) = 0; `aocs.wheels_enabled` (0x0260) = 3 | ☐ | |
| 3 | Desaturate the remaining set: `AOCS_DESATURATE` (func **1**) | `aocs.h_body_mag` (0x02B9) falling; allow **20–50 min** | ☐ | |
| 4 | Verify pointing on three wheels. A 3-of-4 subset still spans R³, so **FINE_POINT still works** — flagged, not refused | `aocs.att_error` (0x0217): ____ °; `aocs.fine_degraded` (0x0299) = 1; `aocs.fine_ready` (0x02C5) bit 1 clear | ☐ | |
| 5 | If pointing acceptable, stay in NOMINAL (`AOCS_SET_MODE(mode=4)`); else fall back to COARSE_SUN (**3**) | mode: ____ | ☐ | |
| 6 | File anomaly ticket | ticket #: ____ | ☐ | |

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
| 1 | Confirm the failure: `HK_REQUEST(sid=2)` (S3.27) | `aocs.st1_status` (0x0240) = 3 (blind) or 4 (failed); rising `aocs.est_innov_rej_count` (0x02C2) | ☐ | ST1: __ ST2: __ |
| 2 | Bring up the other head: `ST2_POWER(on=1)` (S8.1 func **5**) | `aocs.st2_status` (0x0243) = 2 (tracking) within its boot time | ☐ | |
| 3 | Select it: `ST_SELECT(unit=2)` (S8.1 func **6**) | `aocs.st_selected` (0x0244) updated; `aocs.est_source` (0x02C1) bit 0 still set | ☐ | |
| 4 | Isolate the failed head: `ST1_POWER(on=0)` (S8.1 func **4**) | `aocs.st1_status` = 0 (off) | ☐ | |
| 5 | If the attitude solution has diverged, re-initialise it: `AOCS_EST_RESET(mode=1)` (S8.1 func **91**, warm) — or `mode=0` for a cold reset after a time jump | `aocs.knowledge_err_3sig` (0x02A7) settling; innovation rejections stop climbing | ☐ | |
| 6 | If **both** heads are lost, fall back to the sun-safe hold: `AOCS_SET_MODE(mode=3)` COARSE_SUN, and `PAYLOAD_SET_MODE(mode=0)` | `aocs.mode` (0x020F) = 3; `aocs.est_source` shows CSS+MAG+gyro, ST bit clear | ☐ | mode: ____ |
| 7 | If a head recovers, restore NOMINAL (`AOCS_SET_MODE(mode=4)`); else hold COARSE_SUN | mode: ____ | ☐ | |
| 8 | File anomaly ticket | ticket #: ____ | ☐ | |

## CTG-010 OBDH Watchdog Recovery

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the reboot: `HK_REQUEST(sid=4)` (S3.27) | `obdh.reboot_count` (0x030A) incremented; `obdh.last_reboot_cause` (0x0316) = 1 (watchdog); `obdh.uptime` (0x0308) near zero | ☐ | timestamp: ______ |
| 2 | If the spacecraft came back in the bootloader (`obdh.sw_image` 0x0311 = 0), re-boot the application: `OBC_BOOT_APP` (S8.1 func **55**) | `obdh.sw_image` = 1 within 15 s | ☐ | |
| 3 | Re-enable housekeeping — application boot re-applies `default_enabled_sids: [1, 11]`, so **every other SID is off again**: `HK_ENABLE(sid=2/3/4/5/6)` (**S3.5**) | all required SIDs periodic again | ☐ | |
| 4 | Re-synchronise time: `SET_TIME(cuc_seconds=T_corrected)` (S9.1), verify with `REQUEST_TIME` (S9.2) | residual < 1.0 s | ☐ | |
| 5 | Verify OBC mode; restore NOMINAL if in SAFE: `OBC_SET_MODE(mode=0)` (S8.1 func **50**) | `obdh.mode` (0x0300) = 0 | ☐ | mode: ____ |
| 6 | Re-apply settings lost in the reset (heater setpoints, S12 limit overrides, TM tier, beacon mode) | settings restored | ☐ | |
| 7 | File anomaly ticket | ticket #: ____ | ☐ | |

## CTG-012 Overcurrent Response

Line indices run **0–8**: 0 `obc`, 1 `ttc_rx`, 2 `ttc_tx`,
3 `payload`, 4 `fpa_cooler`, 5 `htr_bat`, 6 `htr_obc`,
7 `aocs_wheels`, 8 `prop`.

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Identify the tripped line from `eps.oc_trip_flags` (0x010D) and the per-line currents `eps.line_current_0..7` (0x0118–0x011F; line 8 is 0x014B) | line: ______ | ☐ | I: ____ A |
| 2 | Report to FD; note that the FDIR autonomous action has usually already opened the line | recorded | ☐ | |
| 3 | FD GO | granted | ☐ | |
| 4 | Ensure the line is open: `EPS_POWER_OFF(line_index=N)` (S8.1 func **20**) | `eps.pl_*` status bit = 0 | ☐ | |
| 5 | Verify the line current is 0 | I: ____ A | ☐ | |
| 6 | Only after the fault is understood, clear the latch and re-enable: `EPS_RESET_OC_FLAG(line_index=N)` (S8.1 func **21**), then `EPS_POWER_ON(line_index=N)` (func **19**) | `eps.oc_trip_flags` bit clear; line current back within envelope | ☐ | |
| 7 | File anomaly ticket; root cause for next shift | ticket #: ____ | ☐ | |

## CTG-015 Corrupted Image Recovery

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the S5 event **0x0607 IMAGE_CHECKSUM_ERROR** and read `payload.checksum_errors` (0x0609) | event recorded | ☐ | count: ____ |
| 2 | Check the FPA: `HK_REQUEST(sid=5)` and `(sid=3)` (S3.27) | `payload.fpa_temp` (0x0601) in band and `payload.fpa_ready` (0x0610) = 1 at capture time? | ☐ | T: ____ °C |
| 3 | If the FPA was warm, abort to STANDBY (`PAYLOAD_SET_MODE(mode=1)`, func 26), re-enable the cooler (`FPA_COOLER(on=1)`, func **43**) and wait for `fpa_ready` | ready = 1 | ☐ | |
| 4 | Check memory: `payload.mem_segments_bad` (0x0612); mark a bad segment with `PAYLOAD_MARK_BAD_SEGMENT(segment_id=N)` (S8.1 func **31**) | segments: ____ | ☐ | |
| 5 | Delete and re-capture: `PAYLOAD_DELETE_IMAGE(scene_id=N)` (func **30**), then `PAYLOAD_CAPTURE(scene_id=N, lines=L)` (func **28**) | new scene: ______; S5 0x0613 IMAGE_CAPTURED | ☐ | |
| 6 | If recurring, investigate FPA temperature or pointing | finding: ____________ | ☐ | |
| 7 | File anomaly ticket | ticket #: ____ | ☐ | |

## CTG-017 Bus Failure Switchover

Switching the **bus** and switching the **OBC unit** are different
commands. `OBC_SELECT_BUS` (func 54) changes the CAN bus;
`OBC_SWITCH_UNIT` (func 53) fails over to the redundant OBC and is
CTG-011, not this card.

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the bus fault: `HK_REQUEST(sid=4)` (S3.27) | `obdh.bus_a_status` (0x030F) = 1 (ERROR); `obdh.active_bus` (0x030E) = 0 (A) | ☐ | |
| 2 | FD GO for bus switchover | granted | ☐ | |
| 3 | Issue `OBC_SELECT_BUS(bus=1)` (S8.1 func_id **54**) to move to bus B (use `bus=0` to go back to A) | S1.1 accept + S1.7 complete | ☐ | |
| 4 | Verify bus B in use and all housekeeping resumes | `obdh.active_bus` = 1; `obdh.bus_b_status` (0x0310) = 0; SIDs 1–6 flowing again | ☐ | |
| 5 | File anomaly ticket. Note there is now **no bus redundancy left** | ticket #: ____ | ☐ | |

## CTG-019 No Telemetry at Pass Start

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Verify the scheduled station and baseband config (five-station network) | OK | ☐ | |
| 2 | Verify orbit / pass prediction (could be geometry) | prediction OK | ☐ | |
| 3 | Blind-command the TX chain: `HK_REQUEST(sid=1)` (S3.27), `EPS_POWER_ON(line_index=2)` (func **19**), `TTC_PA_ON` (func **66**) | `eps.pl_ttc_tx` (0x0112) = 1; `ttc.pa_on` (0x0516) = 1 once TM returns | ☐ | |
| 4 | Blind transponder swap: `TTC_SWITCH_REDUNDANT` (func **64**), then `TTC_SWITCH_PRIMARY` (func **63**) | `ttc.link_status` (0x0501) = **2** (LOCKED) | ☐ | |
| 5 | If the antenna was never deployed, `TTC_DEPLOY_ANTENNA` (func **69**) — irreversible burn-wire | `ttc.antenna_deployed` (0x0520) = 1 | ☐ | |
| 6 | Remember the UHF beacon is a **separate radio**: if HK SID 11 is still arriving while the S-band is silent, the fault is in the S-band chain, not the spacecraft | `ttc.beacon_active` (0x0527): ____ | ☐ | |
| 7 | If link established, run NOM-001; if no link after two consecutive passes, escalate **EMG-004** (Loss of Communication) | path: ____ | ☐ | |
| 8 | File anomaly ticket | ticket #: ____ | ☐ | |

## CTG-020 Ground Station Antenna Failure

CTG-020 is an **advisory** card (`advisory: true` in
`procedure_index.yaml`) — it is not machine-runnable, and it
contains **no spacecraft telecommands**. This is a ground-segment
failure: everything is done on the ground side. Do not command the
spacecraft for it.

| # | Action | Verification | ☐ | Note |
|---|--------|--------------|:-:|------|
| 1 | Confirm the failure is ground-side, not spacecraft-side (`ttc.gs_equipment_status` 0x0524 bitmask; a healthy spacecraft still radiates) | confirmed | ☐ | |
| 2 | Attempt local station recovery with the station operator | result: ______ | ☐ | |
| 3 | Notify FD and Mission Manager; assess the impact on the shift plan | logged | ☐ | |
| 4 | Re-plan the remaining activities onto the next station in the five-station network; verify its baseband and tracking | station: ______ | ☐ | |
| 5 | File anomaly ticket | ticket #: ____ | ☐ | |

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
