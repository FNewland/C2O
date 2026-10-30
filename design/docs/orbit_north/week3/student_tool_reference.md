---
title: "Student MCS & MPS Reference"
subtitle: "ORBIT NORTH · Week 3 operations tools quick reference"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "students"
expected-reading: "Sections 1 – 4 before Training Day 2; sections 5 – 7 before Wednesday LEOP day"
---

# Student MCS & MPS Reference

This document is the operator's reference for the two tools you will
use during Week 3 of ORBIT NORTH:

- **MCS** — the Mission Control System (telemetry, commanding,
  procedure panel, FDIR panel)
- **MPS** — the Mission Planning System (imaging targets, pass
  planning, conflict checking)

You do **not** need to know how the underlying simulator works.
You **do** need to be fluent in the MCS and MPS UIs.

---

## 1. The console at a glance

The default console is the *modern* MCS (`smo-mcs --ui modern`;
`--ui classic` serves the older layout that textbook Part 2, §7.1,
describes). It has four regions:

- **Top bar** — the mission tag (EO1 · EOSAT-1); three clocks (UTC,
  MET and spacecraft time), with a TRAINING chip because the ground
  clock is simulator time; the POSITION selector; the alarm button
  with its count of unacknowledged alarms; DELAYED TM and REPORTS;
  the GUIDED (numbered teaching annotations), GREY (greyscale check)
  and THEME toggles; the EN/FR switch, help and the connection dot.
  Beneath it, the situation strip answers four questions: *Can I see
  it?*, *Can I talk?*, *Is it well?* and *What's next?*
- **Navigation rail** (left) — OVR, EPS, TCS, AOC, TTC, PLD, PRP, OBD,
  then CMD, FDR, PRC, TRD, PUS and MAN. Your position decides which
  buttons appear (§1.1); the Flight Director sees them all.
- **Main work area** (centre) — the page chosen on the rail:
  schematics and telemetry mosaics, commanding, procedures, FDIR,
  trends.
- **Bottom drawer** — EVENTS (with a severity filter), TM PACKETS,
  CMD HISTORY, LOG (console log with NOTE and MARK), HANDOVER and
  GO/NO-GO (the FD's poll).

> **TODO (author):** Capture an annotated screenshot of the default
> Flight Director view in the modern MCS and place it here, labelling
> the four regions above.

### 1.1 Position-specific tabs

Each MCS position has a different visible-tab set defined in
`mcs/positions.yaml`. Quick reference:

| Position | Visible tabs |
|----------|-------------|
| Flight Director | system_dashboard, power_monitor, fdir_panel, contact_schedule, procedure_panel, overview, eps, aocs, tcs, obdh, ttc, payload, prop, commanding, pus, procedures, trends, manual |
| Power & Thermal | overview, eps, tcs, commanding, procedures, trends, manual |
| Flight Dynamics | overview, aocs, prop, commanding, procedures, trends, manual |
| TT&C | overview, ttc, commanding, procedures, trends, manual |
| Payload Operations | overview, payload, commanding, procedures, trends, manual |
| FDIR / Systems | overview, obdh, commanding, pus, procedures, trends, manual |
| Propulsion | overview, prop, tcs, commanding, procedures, trends, manual |

The overview tab is always present so every position has shared
situational awareness; the position-specific tabs are where you do
your work.

The printable cheat sheet is textbook Part 2, §7.2 (Table 7.2). Seeing
a tab is not the same as commanding from it: `allowed_services` and
`allowed_func_ids` in `positions.yaml` decide which command buttons
are live, so Flight Dynamics sees the PROP tab but cannot command a
burn.

---

## 2. Reading telemetry

Telemetry arrives in housekeeping structures (SIDs) defined in
`telemetry/hk_structures.yaml`; each parameter has a mnemonic and a
hex id in `telemetry/parameters.yaml` (for example `eps.bat_soc`,
0x0101). Only SIDs 1 (EPS) and 11 (Beacon) are on at application
boot; the others need `HK_ENABLE` (S3.5). A display reading *not
enabled* is not a link fault.

Colour comes from `mcs/limits.yaml`: green inside the nominal band,
yellow in the caution band (call it on the loop), red in the alarm
band (an FDIR rule usually fires at the same time). Staleness is a
separate flag, worked out per parameter from the cadence of the SID
that carries it (`mcs/staleness.yaml`): fresh while the value's age
is under max(10 s, 0.9 × interval), degraded under max(20 s,
1.5 × interval), stale beyond. So a SID 3 (TCS, 60 s) value is not
stale at 15 s. Stale means *I don't know the value*, not *the value
is bad*.

The TRD (Trends) page plots archived values of a parameter against
time. Full detail: textbook Part 2, §7.1 (telemetry mosaic and
status indicators) and §15.1 (compact telemetry reference by
subsystem).

---

## 3. Sending a command

There are two paths. **Procedure-driven** (recommended): run the
card from the PRC (Procedures) page; each **TC** step carries its
command and arguments, and the panel fills the command fields.
**Direct**: build the command on the CMD page — choose the service
or the S8 function, fill the typed argument fields (Tab between
them, Enter to send). Textbook Part 2, §7.8, says when each path is
appropriate.

The seven services you will see most (`mcs/pus_services.yaml`):
**S1** verification — acceptance (1.1), start (1.3), completion
(1.7) or failure (1.2, 1.8) of each TC; **S3** housekeeping —
enable (3.5) and request (3.27) a SID; **S5** event reports;
**S8** function management — every subsystem function is S8.1 with
a func_id, e.g. `OBC_BOOT_APP` (func 55); **S9** time — `SET_TIME`
(9.1); **S11** the on-board time-tagged schedule; **S17** the
connection test (17.1, answered by 17.2). The full primer is §7.6.

Critical commands need two keys: the owning position arms
(first-keys) the command, the FD gives the GO, and only then is it
sent; the CMD page will not send a critical command that has not
been armed.

Common refusals: an argument out of range or missing (refused with
a reason, not silently clamped); a command outside the bootloader
allow-list while `obdh.sw_image` = 0; a function your position is
not allowed (`allowed_func_ids`); and no link — commands only go up
during a contact.

---

## 4. The procedure panel

Textbook Part 2, §7.4, covers the panel in full. In short:

- **Load** a card from the PRC page by ID or title; it becomes the
  shift's active procedure.
- **Steps** follow the file: each **TC**, **Action**, **Verify** and
  **Note** label becomes a line in the panel. The owner is the
  position in the card's `required_positions`.
- **Run** one step at a time: call it on the loop, get the FD's GO,
  send, read the verification back, mark the step verified.
- **Skip** is allowed only when telemetry already shows the step's
  end state, and the skip is logged with that value. **Hold** is
  allowed while the team assesses; the FD authorises the restart.
  Anything else is a procedure violation.
- Every step, skip and hold is time-stamped in the console log
  (bottom drawer, LOG), which is the record the debrief uses.

---

## 5. The FDIR panel

Textbook Part 2, §7.5, covers the panel in full. The rules come from
`monitoring/s12_definitions.yaml` (46 S12 monitors: what is watched,
threshold and persistence) and `monitoring/s19_rules.yaml` (32 S19
event-action rules: what the spacecraft does on its own). The panel
lists active triggers with their severity colour, trigger time and
subsystem; level 3 and 4 raise the red banner.

- **Acknowledge** says you have seen it and silences the alert; the
  parameter is still out of band. In the modern MCS, **A** opens the
  alarm drawer and **K** acknowledges the first unacknowledged
  alarm in the list.
- **Clear** is possible only once the parameter is back in band,
  and always after an anomaly ticket.
- FDIR **severity** (0–4) and on-board **autonomy level** (0–3) are
  different scales; do not mix them.
- **Manual override** (disabling a rule) needs FD authorisation, for
  example during a planned out-of-band calibration; the rule shows
  grey until it is re-enabled.

An anomaly ticket records the time of the first indicator, the
parameter and value, the rule that fired, the procedure run and the
outcome; it goes in the shift log.

---

## 6. The Mission Planning System (MPS)

The MPS is its own webapp at `http://localhost:9091/` (wide layout
at `/wide`); textbook Part 2, §7.3, describes its five panels, and
§8.5 is the Day 1 exercise.

- **Imaging-target picker** — the ocean-current targets of
  `planning/imaging_targets.yaml` (`OCM-001` Gulf Stream, `OCM-002`
  Kuroshio, …), each a lat/lon box with a priority, a revisit
  interval and a `min_solar_elevation_deg` gate. Bands are set per
  acquisition (`PAYLOAD_SET_BAND_CONFIG`), not per target.
- **Activity types** — the ten types of
  `planning/activity_types.yaml` (`imaging_pass`, `data_dump`,
  `calibration`, `housekeeping_collection`, `software_upload`,
  `momentum_desaturation`, `thermal_rebalance`, `load_shedding`,
  `fdir_recovery`, `orbit_manoeuvre`), each with power, thermal,
  pointing and duration.
- **Ground-station schedule** — 24 h of passes over all five
  stations: AOS, maximum elevation, LOS, duration. A pass that never
  clears 10° carries no HIGH-tier dump.
- **Conflict checker** — slew time, power, thermal envelope and
  pointing; red for conflicts, yellow for warnings.
- **Plan export** — the staged plan becomes S11 time-tagged commands
  (`SCHEDULE_TC`, S11.4) that the OBC executes; the activities that
  are linked to procedures (NOM-002, NOM-003, NOM-004, NOM-009) can
  then be run from the MCS Procedures page.

---

## 7. Voice loop & MCS chat

Textbook Part 2, chapter 9, is the reference; Training Day 2 §1 is
the drill.

- **Voice loop.** One softphone headset per position on a single
  conference channel. Address the station first, then yourself, then
  the message: "FD, AOCS — …". Push-to-talk by default; the FD alone
  may go hot-mike for a critical sequence and says so on the loop.
- **MCS chat and console log.** Use them for low-priority notes,
  numbers to copy and handover items. Never put a commanding
  intention or a GO there: a GO is only valid on the loop.
- **Logging.** The loop is recorded for the debrief, and every NOTE,
  MARK, GO/NO-GO poll and procedure step in the console log is
  time-stamped.

---

## 8. Quick keyboard shortcuts

These are the shortcuts in the shipped MCS code (modern console;
the classic console has the first five). Letter keys do nothing
while you are typing in a field.

| Shortcut | Action |
|----------|--------|
| `?` | Show or hide the help panel |
| `Esc` | Close help, the chain view or the alarm drawer; otherwise return to the Overview page |
| `F6` | Move focus to the next region (top bar → rail → main area → bottom drawer) |
| `←` `→` (`↑` `↓`) on the rail | Previous or next page |
| `Enter` in a command field | Send the command (a critical command must be armed first) |
| `A` | Open the alarm drawer |
| `K` | Acknowledge the first unacknowledged alarm in the list |
| `Enter` in the handover box | Add the handover note |
| `Enter` in the console-log box | Post the log note |
| `Tab` in the open alarm drawer | Cycle through its controls |

There is no global quick-command picker and no function-key focus
shortcut beyond `F6`. Textbook Part 2, §7.9, adds that the
installation's own quick-reference card wins where it differs.

---

## 9. Where to read more

| Topic | Source file in simulator |
|-------|--------------------------|
| Subsystem manuals (background) | `configs/eosat1/manual/0*.md` |
| Position role analyses | `configs/eosat1/mcs/role_analysis/*.md` |
| Telemetry parameters | `configs/eosat1/telemetry/parameters.yaml` |
| Telemetry limits | `configs/eosat1/mcs/limits.yaml` |
| Procedure index | `configs/eosat1/procedures/procedure_index.yaml` |
| FDIR rules | `configs/eosat1/monitoring/s19_rules.yaml` |

External references:

- ECSS-E-ST-70-11C — Space segment operability —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- ECSS-E-ST-70-32C — Test and operations procedures —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-32c-test-and-operations-procedures/
- CCSDS Packet Utilization Standard (PUS) —
  https://public.ccsds.org/Pubs/660x0g3.pdf
- NASA *Mission Operations Handbook* — https://nodis3.gsfc.nasa.gov/
