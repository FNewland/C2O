# Propulsion (propulsion) -- Role Analysis

**Position ID:** `propulsion`
**Display Name:** Propulsion
**Subsystems:** prop
**Allowed Subsystems:** prop, tcs (the catalyst-bed heater is TCS circuit 2)
**Allowed PUS Services:** 1, 3, 5, 8, 11, 17, 20
**Allowed func_ids:** 42 (HEATER_THRUSTER), 108-118 (PROP_*)
**Visible Tabs:** overview, prop, tcs, commanding, procedures, trends, manual
**Manual Sections:** 07_orbit_ops

Source of truth for this card: `mcs/positions.yaml` (the console), `subsystems/prop.yaml`
(the module), `commands/tc_catalog.yaml` (func 108-118), `mcs/displays.yaml` (the PROP tab),
`mcs/limits.yaml` and `monitoring/s19_rules.yaml` (ea 8001-8006). Added 2026-10-30 (author
ruling Q25) so that the MCS round-robin has a propulsion score card like the other six desks.

## 0. What the Propulsion System Is For

EOSAT-1 carries a 1U green-monopropellant blowdown module (LMP-103S/ADN): one thruster on
the -X face thrusting along +X body, 0.400 kg of propellant, 22.0 -> 9.33 bar blowdown,
0.33 -> 0.14 N, Isp 220 -> 196 s, about 66.9 m/s of total delta-V.

Its job is **limited orbit maintenance, collision avoidance and the end-of-life disposal
burn** (ruling Q3 as amended, 2026-10-30):

| Use | Budget (m/s) | Notes |
|---|---|---|
| Drag make-up | 15.1 | Keeps the 513 km orbit against decay over the 2-year active phase (design solar activity) |
| SMA / LTAN biasing | 3.0 | Semi-major-axis and LTAN biasing |
| Collision avoidance (CAM, 6 events) | 0.6 | The reserve the dV-remaining alarm protects |
| Commissioning / calibration burns | 1.0 | |
| Eccentricity control | 1.5 | |
| End-of-life disposal (513 -> 390 km perigee) | 34.3 | NOM-014, six retrograde burns |
| Margins (5 % + 10 %) | 8.6 | |
| **Required vs capability** | **64.1 vs 66.9** | +4.4 % (+2.6 % against the 65.8 m/s blowdown-integrated capability) |

Natural decay from 513 km (ballistic coefficient 77.9 kg/m2) takes about 5 years at mean
solar activity and about 14 years at solar minimum, which breaks the 5-year disposal rule.
The disposal burn lowers the perigee to 390 km, for re-entry in about 1.5 years (mean) and
4.2 years (solar minimum). The desk keeps at least 38 m/s of `prop.dv_remaining` (0x0B0C)
in reserve for it from mid-mission. There are no plane changes, no orbit raising and no
autonomous orbit control: every burn is planned on the ground by Flight Dynamics and executed
by this desk.

## 1. Mission Lifecycle Phases and Applicable Procedures

### LEOP and Commissioning

No LEOP or commissioning card requires this position. LEOP-007 deliberately leaves the
`prop` power line OFF; it is first powered by NOM-004/NOM-013. Arming also requires mission
phase >= 6 (NOMINAL), so no burn is possible before COM-013 closes commissioning.

### Nominal Operations

| Procedure | ID | propulsion Role |
|---|---|---|
| Orbit Maintenance Manoeuvre Planning | NOM-004 | Verify propulsion health, load S11 sequence |
| Orbit Maintenance Manoeuvre Execution | NOM-013 | Preheat, arm, execute, monitor thrust, post-burn OD |
| End-of-Life Disposal | NOM-014 | Burn watchdog, preheat, six retrograde burns, depletion, safing |

### Contingency

| Procedure | ID | propulsion Role |
|---|---|---|
| Propulsion Anomaly | CTG-028 | Isolate, bound remaining delta-V, ticket |

### Emergency

No emergency card requires this position. On safe-mode entry the spacecraft disarms the
propulsion itself (S19 ea 8005), and the desk confirms `prop.state` (0x0B00) left ARMED/FIRING.

## 2. Available Commands and Telemetry

### Commands

#### Propulsion Commands (S8, func_ids 108-118)

| Command | func_id | Criticality / effect | Fields |
|---|---|---|---|
| PROP_ARM | 108 | ARMED; runs every interlock | arm_code (0xA5C3 = 42435) |
| PROP_DISARM | 109 | ARMED -> SAFED, closes the flow-control valve | (none) |
| PROP_SET_BURN | 110 | critical; loads the manoeuvre, must precede PROP_ARM by <= 300 s | dv_m_s (0.01-20), direction (0 PROGRADE, 1 RETROGRADE), mode (0 OPEN_LOOP, 1 DV_CUTOFF), t_start_cuc |
| PROP_EXECUTE | 111 | ARMED -> FIRING; normally delivered by the S11 schedule | (none) |
| PROP_ABORT | 112 | FIRING -> SAFED immediately | (none) |
| PROP_ISO_OPEN | 113 | Open latch-valve branch(es) | branch (0 A, 1 B, 2 BOTH) |
| PROP_ISO_CLOSE | 114 | Close latch-valve branch(es) | branch (0 A, 1 B, 2 BOTH) |
| PROP_SET_LIMITS | 115 | Reconfigure on-board burn-abort thresholds | att_err_max_deg, p_min_bar, catbed_max_c, t_burn_max_s |
| PROP_INHIBIT_SET | 116 | Ground-latched inhibit | on |
| PROP_INHIBIT_CLR | 117 | Clear ground or FDIR/double-abort inhibit | key (0xA5C3) |
| PROP_GET_STATUS | 118 | On-demand status report, TM(8,2) | (none) |

#### Thermal (S8, func_id 42)

| Command | func_id | Description |
|---|---|---|
| HEATER_THRUSTER | 42 | Catalyst-bed preheat, 12 W, about 20 min before arming (TCS circuit 2) |

#### General Services

| Service | Use at this desk |
|---|---|
| S3 | HK_ENABLE / HK_REQUEST for SID 9 (propulsion, 8 s). SID 9 is not enabled by default |
| S5 | Propulsion events 0x0800-0x0812 |
| S11 | Time-tagged PROP_EXECUTE for a planned burn (NOM-004) |
| S17 | Connection test |
| S20 | GET_PARAM for on-demand values (e.g. `eps.pl_prop` 0x014A) |

### Burn Sequence and Arm Interlocks

The two-step sequence is PROP_SET_BURN, then PROP_ARM with the arm code within 300 s, then
PROP_EXECUTE (or the S11 time tag). PROP_ARM is refused unless ALL of the following hold,
and each failure sets its bit in `prop.arm_inhibit_mask` (0x0B15):

| Interlock | Value (`subsystems/prop.yaml`) |
|---|---|
| Catalyst bed `tcs.temp_thruster` (0x0409) | >= 180 C |
| Tank pressure | 6.0-24.0 bar |
| Propellant | >= 5 g |
| AOCS mode | 4 NOMINAL, 5 FINE_POINT or 9 INERTIAL |
| `aocs.att_error` (0x0217) | <= 2.0 deg |
| `eps.bat_soc` (0x0101) | >= 45 % |
| Mission phase | >= 6 (NOMINAL) |
| Eclipse | no eclipse burn |

The thruster fires along +X body, which is prograde in the nominal nadir attitude. A
retrograde burn needs a deliberate 180-degree yaw (INERTIAL hold), which Flight Dynamics
(aocs desk) sets up.

### Telemetry (HK SID 9, 8 s, and on-demand)

| Parameter | ID | Meaning |
|---|---|---|
| prop.state | 0x0B00 | SAFED / ARMED / FIRING / INHIBIT |
| prop.tank_pressure | 0x0B01 | bar |
| prop.propellant_mass | 0x0B02 | g |
| prop.propellant_pct | 0x0B03 | % |
| prop.tank_temp | 0x0B04 | C |
| prop.catbed_temp | 0x0B05 | C |
| prop.latch_a_state / latch_b_state | 0x0B06 / 0x0B07 | Latch valves |
| prop.fcv_state | 0x0B08 | Flow-control valve |
| prop.thrust_est / isp_est | 0x0B09 / 0x0B0A | mN / s |
| prop.dv_accum / dv_remaining | 0x0B0B / 0x0B0C | m/s |
| prop.burn_status | 0x0B0D | Burn status |
| prop.burn_dv_cmd / burn_dv_achieved | 0x0B0E / 0x0B0F | m/s |
| prop.burn_time_cmd / burn_time_elapsed | 0x0B10 / 0x0B11 | s (predicted duration for the FDS cross-check) |
| prop.burn_count / total_on_time | 0x0B12 / 0x0B13 | Lifetime counters |
| prop.abort_reason | 0x0B14 | Last abort reason |
| prop.arm_inhibit_mask | 0x0B15 | Arm interlock bits |
| prop.leak_rate | 0x0B16 | mg/s |
| prop.sc_mass | 0x0B18 | kg |
| prop.orbit_epoch_version | 0x0B19 | Bumped when a burn re-fits the orbit |
| prop.sma_km | 0x0B1A | Semi-major axis, km |
| prop.power_draw | 0x0B1B | W |

#### Limit Monitoring (this position must watch)

| Parameter | Yellow | Red |
|---|---|---|
| prop.tank_pressure | 6.0 -- 24.0 bar | 4.0 -- 26.0 bar |
| prop.propellant_mass | 20.0 -- 401.0 g | 5.0 -- 401.0 g |
| prop.catbed_temp | -20.0 -- 300.0 C | -30.0 -- 350.0 C |
| prop.thrust_est | 100.0 -- 400.0 mN | 50.0 -- 450.0 mN |
| prop.dv_remaining | 5.0 -- 100.0 m/s | 1.0 -- 100.0 m/s |

### Display Widgets

**Status & Interlocks:** state, burn status, last abort reason, the arm interlocks as eleven
named indicators, propellant and dV-remaining gauges, EPS prop line.
**Tank & Valves:** tank pressure, propellant, tank and catbed temperatures, thrust and Isp
estimates, leak rate, latch A/B and flow-control valve, pressure/propellant trend.
**Burn:** dV commanded and achieved, predicted and elapsed burn time, attitude error against
the abort threshold, thrust vs attitude-error chart.
**dV Budget:** lifetime dV used and remaining (CAM reserve), burn count, thruster on-time,
spacecraft mass, semi-major axis, element-set version, propulsion event log.

## 3. Inter-Position Coordination Needs

| Scenario | Coordinating With | Coordination Details |
|---|---|---|
| Manoeuvre planning (NOM-004) | aocs, flight_director | Flight Dynamics (aocs desk) produces the dV vector and burn time; propulsion checks it against `prop.dv_remaining` and the predicted duration (0x0B10), then loads the S11 sequence |
| Manoeuvre execution (NOM-013) | aocs, eps_tcs, flight_director | aocs holds the burn attitude (yaw for retrograde); eps_tcs confirms SoC >= 45 % and the 12 W catbed preheat; FD gives the GO to arm |
| Post-burn orbit determination | aocs | aocs re-determines the orbit; propulsion reports `prop.burn_dv_achieved` and the new `prop.sma_km` |
| Propulsion anomaly (CTG-028) | fdir_systems, flight_director | Isolate the latch valves, bound the remaining dV, raise the ticket |
| Safe-mode entry | fdir_systems | Spacecraft disarms on its own (ea 8005); propulsion confirms the state and keeps it SAFED |

### FDIR Rules Relevant to This Position

| FDIR Rule (`s19_rules.yaml`) | Trigger | Action |
|---|---|---|
| prop_burn_abort_on_attitude_error (8001) | `aocs.att_error` (0x0217) S12 monitor | PROP_ABORT |
| prop_abort_on_low_tank_pressure (8002) | `prop.tank_pressure` (0x0B01) out of band | PROP_ABORT |
| prop_abort_on_catbed_overtemp (8003) | event 0x0809 PROP_CATBED_OVERTEMP | PROP_ABORT |
| prop_isolate_on_leak (8004) | event 0x080B PROP_LEAK_DETECTED | PROP_ISO_CLOSE, both branches |
| prop_disarm_on_safe_mode (8005) | event 0x0F0A SAFE_MODE_ENTRY | PROP_DISARM |
| prop_abort_on_soc_critical (8006) | event 0x0102 BATTERY_SOC_CRITICAL | PROP_ABORT |

## 4. GO/NO-GO Responsibilities

The Propulsion position provides GO/NO-GO input to the Flight Director for:

- **Arming:** catbed >= 180 C, tank pressure in band, `prop.arm_inhibit_mask` (0x0B15) clear,
  no leak, and enough `prop.dv_remaining` (0x0B0C) for the burn plus the CAM reserve.
- **Burn execution:** predicted duration (0x0B10) agrees with the Flight Dynamics plan; the
  burn is in sunlight; the attitude and power interlocks hold.
- **Post-burn:** `prop.burn_dv_achieved` (0x0B0F) within tolerance of the commanded value,
  system back to SAFED, catbed heater off.

**Critical Decision Points:**
- If `prop.dv_remaining` drops below 5 m/s (yellow), recommend that remaining propellant be
  held for collision avoidance only.
- If `prop.leak_rate` rises or event PROP_LEAK_DETECTED appears, recommend latch-valve
  isolation (CTG-028) even if the S19 rule has already acted.
- If a burn aborts twice, the system latches INHIBIT; recommend PROP_INHIBIT_CLR only after
  the cause is understood.

---
*AIG --- Artificial Intelligence Generated Content*
*Reference: https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*
