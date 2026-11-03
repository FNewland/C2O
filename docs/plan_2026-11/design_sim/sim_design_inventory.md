# EOSAT-1 simulator design-decision inventory and SpaceCDF traceability

Read-only analysis of `/home/claude/c2o` (sim = `sim/`, SpaceCDF = `design/`), 2026-11-03.
Question: for every design decision embodied in the EOSAT-1 simulator + ground segment, where would it be decided in a design
tool, can SpaceCDF decide it today, and what must a design hand the simulator (the design-to-sim export contract)?

## 0. Legend and coverage rule

| Column | Values |
|---|---|
| Cls | **T** top-level design decision (trade/architecture choice) · **D** derived/detailed design value (sizing result, threshold, table entry) · **S** simulator-only implementation detail (not a design decision; listed in §13, not counted) |
| Gate | Normal ECSS gate by which it is baselined: MDR (Ph 0) · PRR (Ph A) · SRR (Ph B start) · PDR · CDR (ops products: CDR→ORR) |
| CDF | **C** SpaceCDF has a field/parameter/KB key with the right semantics that an exporter could map · **P** partly: coarser fidelity, single value where sim needs a table, free-form `performance_json` key, or only a text decision record (logbook `D-*`) · **M** no structure at all (only a generic unnamed ElementParameter slot could hold it) |
| Owner | EPS, AOCS, TCS, OBDH, SW (flight/ground software, TM/TC DB), TTC, PL, PROP, STR/CFG, SYS (system eng.), MA (mission analysis), FDIR (dependability/systems), OPS, GS |

SpaceCDF reference points used below (all under `design/`):
- `MissionRequirements` / `OrbitRequirements` / `PayloadRequirements` — `packages/spacecdf-common/src/spacecdf_common/models/study.py`
- DesignState params from tier-1/2 agents — `packages/spacecdf-agents/src/spacecdf_agents/tier1/*.py` (`power.*`, `aocs.*`, `link.*`, `data.*`, `thermal.*`, `propulsion.*`, `mass.*`, `orbit.*`)
- Element tree `DesignElementRow` (mass, power_avg/peak, dimensions, `position_json`, quantity, `redundancy_type`, `kb_component_id`, free `performance_json`) + typed `ElementParameter` — `packages/spacecdf-server/src/spacecdf_server/db/models.py`, `models/parameters.py`
- `ModeElementRow` (element on/off + power per mode), ConOps `OperationalMode` / `MissionPhase` / `GroundStation` — `models/conops.py`
- Interfaces with 9 canonical types and per-type property fields — `models/interface_types.py`; rule proposer `configs/interface_rules.yaml`
- Physics closure (mass properties → inertia diag + CoM + cp-cg; AOCS disturbance/wheel margin; lumped thermal network) — `services/physics_closure.py`, `thermal_network.py`, `mass_properties.py`
- KB equipment catalogue (24 categories) — `packages/spacecdf-kb/src/spacecdf_kb/data/components/*.yaml`
- FMECA library — `configs/failure_modes.yaml`, `services/fmeca*.py`
- Decision catalogue (61 decisions, text records, gates MDR→PDR only) — `configs/worksheets/decision_catalogue.yaml`
- Gates: `configs/gate_profiles.yaml` canonical_gates = [mdr, prr, srr, pdr] (**no CDR**; 20 gate products, none is TM/TC DB, FDIR spec, FOP or thermal model)
- Seats: `configs/seats.yaml` 14 design seats; none for OBDH/software, operations, ground segment or FDIR (frontend `constants.ts` still lists `software_engineer`, `mission_ops`, `ground_segment` positions)

---

## 1. Existing design-to-simulator exports in SpaceCDF (status)

| Export | Code | Target | Status vs current sim schema |
|---|---|---|---|
| SMO config exporter (~20 YAML files) | `packages/spacecdf-agents/src/spacecdf_agents/exporters/smo/exporter.py` (+ `param_id_allocator.py`, `orbit_gen.py`); API `POST /exports/smo/{study_id}` and `GET /exports/smo/{id}/validate` in `packages/spacecdf-server/.../routers/exports.py:641`; UI ExportPanel "Simulator Model Inputs" (`frontend/src/workbench/ExportPanel.tsx:147`) | `sim/configs/<mission>/` | **Stale, would not load.** Writes keys the strict sim schemas (`sim/packages/smo-common/src/smo_common/config/schemas.py`, `extra="forbid"`) reject: `mission.yaml: ground_segment` (removed, defect X-11), `eps.yaml: platform_idle_power_w`. Uses the retired legacy `arrays:` block (two half-areas) and no `solar_panels`/wings/`array_losses`/SADA → zero or wrong generation. TTC `dl_freq_mhz: 8200` (X-band; sim DL allocation 2200–2290 MHz, `ttc_basic.DL_BAND_MHZ`), `eirp_dbw: 0`, `gs_g_t_db: 32`, no rate ladder/beacon. TCS = 9 legacy zones, no 16-node network. AOCS: no inertia, wheels geometry, MTQ, sensors, gains. OBDH: model name + param_ids only. FDIR/S12/S19/events/TC catalogue are **hard-coded placeholders** (5 rules, 5 S12, 3 S19, 10 events, 11 S8 functions) unrelated to the design. HK = 6 SIDs, every param uint16 ×100. Ground stations: unknown names silently get Svalbard coordinates. Param IDs are allocated from *design* quantities (e.g. `power.sa_area_m2`), not from telemetry points. No `prop.yaml`, `geometry.yaml`, `rfsim.yaml`, `simulation.yaml`, procedures, planner, limits written. |
| Router enrichment | `routers/exports.py:458-640` `_derive_mission_profile`, `_derive_perturbations`, `_derive_simulation_config`, `_derive_orbit_initial_conditions` | JSON blob | Generic: fixed LEOP timeline (detumble T+30 min…), RAAN = 0, epoch 2026-01-01 hard-coded, RK45 — not consumed by the SMO sim. |
| Geometry `c2o.geometry/1` | `frontend/src/spacecraft/designAdapter.ts:128-215` (`designGeometry`) | same schema as `sim/configs/eosat1/geometry.yaml` (display only; sim physics never reads it) | Works, but most layout is **heuristic, not designed**: body-cell area spread over faces by face area, wings always 2×2 panels on ±Y, ST1 +Z / ST2 canted 45° hard-coded, payload always −Z, FOV default 10°. |
| FSW scaffolding | `exporters/fsw/generator.py`, `fsw/mode_manager.py` (`POST /exports/fsw`) | cFS C headers | APID per subsystem 0x100…0x700 (conflicts with sim's app APID 1 / bootloader APID 2); TM fields per KB category; mode table from ConOps; FDIR rule table generic. |
| Ground MCS config | `services/ground_configurator.py` | COSMOS / Yamcs / OpenMCT | TM points = design params as FLOAT32 (first 50), APID 0x0100; not an XTCE of the real TM. |
| XTCE / SMP2 | none in `design/`. Sim generates its own from its own DB: `sim/tools/generate_xtce.py` → `sim/configs/eosat1/xtce/eosat1.xml`; `sim/tools/generate_smdl.py` → `smdl/*.xml` | — | No design-side TM/TC DB exists to generate from. |
| Validation reference | `design/configs/validation/eosat_6u_reference.yaml`, `configs/templates/6u_eo_cubesat.yaml` | — | Stale vs sim: 450 km (sim 513 km), LTAN 10:30 (sim 10:00), "no primary propulsion" (sim flies 0.4 kg ADN), payload 20 W / FOV 5° (sim 5.5 W / 29.9°), stations KSAT Svalbard + Troll (sim 5 stations). |

---

## 2. Mission and orbit

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| MO-1 | Mission objective: ocean-current monitoring, 6U multispectral EO | `mission.yaml` name/description/payload | SYS/PL | Mission statement, MRD | MDR | T | C | `MissionRequirements.mission_type`, `payloads[0].type/description`; D-1.4-OBJECTIVES |
| MO-2 | Orbit family SSO | `mission.yaml orbit.type`, `orbit.yaml` | MA | Mission analysis report | MDR | T | C | `OrbitRequirements.orbit_type`; D-2.3-ORBIT |
| MO-3 | Altitude 513 km mean (503–530 km) — "TLE is the truth" | `orbit.yaml altitude_km`, `mission.yaml` | MA | Mission analysis | PRR | T | C | `OrbitRequirements.altitude_km` (template still 450) |
| MO-4 | Inclination 97.39° = exact SSO for n = 15.24 rev/d | `orbit.yaml inclination_deg` + TLE | MA | Mission analysis | PRR | D | P | input only; orbit agent outputs `orbit.raan_drift_deg_day` but no "solve i for SSO" |
| MO-5 | LTAN 10:00 (RAAN 120° at epoch) | TLE line 2 | MA | Mission analysis | PRR | T | P | `OrbitRequirements.ltan` string, `raan_deg`; `orbit_gen.keplerian_to_tle` takes RAAN default 0, LTAN never converted |
| MO-6 | e = 0.00012, ω = 90°, M = 270° | TLE | MA | Orbit file | PDR | D | P | `eccentricity` only |
| MO-7 | Reference orbit as TLE + epoch 2026-08-20T12:00Z (`t0_epoch`) | `orbit.yaml tle_line1/2, t0_epoch` | MA/OPS | Launch ICD / injection orbit, orbit file | CDR | T | M | no epoch/state; `orbit_gen` stamps epoch = now; router epoch 2026-01-01 |
| MO-8 | Design life 3 yr; EOL sizing case | `eps.yaml design_life_years` | SYS | MRD | MDR | T | C | `mission_duration_years`, `design_lifetime_years` |
| MO-9 | Eclipse 33.2–35.2 min (fraction 0.351–0.372); \|β\| 20.8–31.2° over the year | `sim/tools/power_budget.py`, eps.yaml comment | MA | Mission analysis (illumination) | PRR | D | P | `orbit.eclipse_fraction`, `eclipse_duration_min` single value; physics has `beta_angle_deg` arg but no yearly β range |
| MO-10 | Thermal environment: S = 1361 W/m² (1/r²), albedo 0.30, OLR 237 W/m² | `simulation.yaml tcs.environment` | TCS/MA | Thermal analysis environment (ECSS-E-ST-31C) | PDR | D | P | hot/cold constants hard-coded in `physics_closure` / `thermal_network`, not per study |
| MO-11 | Atmosphere for torques ρ = 2e-12 kg/m³ | `aocs.yaml disturbances.rho_kgm3` | MA/AOCS | Disturbance analysis | PDR | D | P | `physics/aocs.compute_disturbance_torques` derives density from altitude internally |
| MO-12 | Mission phases 0 PRE_SEPARATION, 1 SEPARATION_TIMER, 2 INITIAL_POWER_ON, 3 BOOTLOADER_OPS, 4 LEOP, 5 COMMISSIONING, 6 NOMINAL | `service_dispatch._PHASE_NAMES`, TC f120 `SYS_SET_MISSION_PHASE`, param 0x0129 | SYS/OPS | ConOps / mission phase plan (ECSS-E-ST-70C) | SRR | T | P | `ConOps.MissionPhase` (leop/commissioning/transfer/nominal/extended/disposal + duration + entry/exit text); no pre-sep/bootloader phases, no codes |
| MO-13 | Separation inhibit timer 1800 s | `simulation.yaml phases.separation_timer_s` | SYS/STR | CDS compliance (CDS rev 14.1 §3.4), launch ICD | PRR | T | C | `cds_rules.yaml safety.min_deploy_delay_min / min_rf_delay_min`; electrical_signal interface `delay_min` |
| MO-14 | Power-up into bootloader/beacon mode | `mission.yaml start_in_bootloader` | OBDH/OPS | FSW boot concept, ConOps | SRR | T | M | — |
| MO-15 | Imaging target set | `planning/imaging_targets.yaml` | PL/MA | Mission requirements (coverage) | PRR | T | M | no area-of-interest model |

## 3. EPS (power)

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| EP-1 | Bus topology: unregulated 8S Li-ion battery bus 21.5–29.2 V, MPPT array input | `eps.yaml battery.*`; `simulation.yaml uv/ov` | EPS | EPS architecture (ECSS-E-ST-20C) | SRR | T | P | D-3.1-EPS text; `interface_rules.yaml defaults.battery_bus_by_class` gives **7.4 V for nano** (would not reproduce 28 V); power-interface `rail_voltage`; KB `eps_boards.bus_voltage_v` |
| EP-2 | Battery 100 Wh (GomSpace NanoPower BPX 8S1P, 3 Ah) | `battery.capacity_wh` | EPS | Battery sizing / power budget | PDR | T | C | `power.battery_capacity_wh`; KB `batteries.yaml` has NanoPower BPX 100 Wh; D-3.1-BATTERY |
| EP-3 | OCV end-points 29.2/21.5 V, V_nom 26.4 V (BPX datasheet 28.8 V), R_int 0.05 Ω | `battery.voltage_nom/soc_100_v/soc_0_v/internal_r_ohm` | EPS | Battery model (datasheet) | CDR | D | P | KB `voltage_v` only; no OCV curve, R_int |
| EP-4 | Coulombic eff 0.94 charge / 1.0 discharge; CV taper from 90 % SoC | `battery.*` | EPS | Battery model | CDR | D | P | physics uses fixed round-trip 0.90 (`physics/power.py:117`); no taper |
| EP-5 | SoC policy: load-shed 30/20/10 %, FDIR 20/15 %, planner min 25 %, prop burn ≥45 % | `simulation.yaml`, `fdir.yaml`, `planner.yaml`, `prop.yaml` | EPS/SYS | Power budget (DoD), FDIR | PDR | T | P | `power.battery_dod_pct`, physics `battery_max_dod` 0.30, `mission_simulation` guard "soc<20→safe" from mode notes |
| EP-6 | Cell technology TJ GaAs, η 0.295 | `technology`, `cell_efficiency` | EPS | SA design | SRR | T | C | KB `solar_cells.efficiency`; `power.solar_array.cell_equipment_id` |
| EP-7 | SA loss stack: inherent 0.85, −0.0020/°C @ 28 °C ref, array 65 °C, MPPT 0.97, harness 0.95 → K = 292 W/m² BOL | `array_losses.*` | EPS | Power budget (EOL power) | PDR | D | P | KB `temp_coefficient_pmax`; physics has η + degradation only |
| EP-8 | Degradation 2.75 %/yr; EOL factor 0.9175 @ 3 yr | `array_losses.annual_degradation` | EPS | Power budget | PDR | D | C | physics `sa_degradation_per_year`; KB `radiation_degradation_per_year` |
| EP-9 | Body cells per face: ±X 0.060, ±Y 0.030, +Z 0.018, −Z 0 m² (−Z = aperture + radiator) | `solar_panels.*_area_m2` | EPS/CFG | SA layout, configuration | PDR | T | P | `designAdapter.designGeometry` spreads body area by face area; no per-face field; −Z exclusion not a decision |
| EP-10 | Deployable wings: 2 × 0.120 m² cells, 2 panels 209×342 mm each, on ±Y (Endurosat DSA) | `solar_panels.wing_*`; `geometry.yaml wings` | EPS/CFG | SA design, configuration | PDR | T | P | `power.sa_area_m2` total; KB `solar_panels.area_m2/deployment`; adapter always 2 wings × 2 panels |
| EP-11 | Wing deploy 30 s (burn wire + spring) | `wing_deploy_time_s` | EPS/STR | Mechanism spec | CDR | D | P | KB `mechanical_hardware.activation_time_s` |
| EP-12 | SADA: single-axis about body Y (orbit normal), sun-tracking, ≤1 °/s | `sada_present/axis/tracking/max_rate_deg_s` | EPS/AOCS | SA drive design | SRR | T | M | no SADA KB category; adapter only name-matches "sada" |
| EP-13 | Peak gen 88.6 W; EOL orbit-avg 45.1 W vs 28.8 W nominal load (1.57×) | `tools/power_budget.py` | EPS | Power budget | PDR | D | C | `power.sa_power_bol_w/eol_w`, `systems.power_margin_percent` |
| EP-14 | PCDU line list: obc, ttc_rx non-switchable; ttc_tx, payload, fpa_cooler, htr_bat, htr_obc, aocs_wheels, prop switchable (9 lines) | `eps_basic.POWER_LINE_DEFS` (code) | EPS/SYS | Power distribution / EPS ICD (LCL allocation) | PDR | T | P | power interfaces with subtype `switched` and `switched` (LCL) flag per element pair; no PCDU channel table |
| EP-15 | Line states at power-on: only obc + ttc_rx energised | `eps.yaml power_lines` | EPS/OPS | LEOP sequence, CDS inhibits | PDR | D | M | — |
| EP-16 | Line loads: OBC+PDU 6 W (3+3), payload 5.5/2.4 W, FPA cooler 15 W, TX 5/11 W, RX 1.5 W, htr_bat 8 W, htr_obc 4 W, wheels 12 W fallback, prop 14 W | `eps.yaml`, `simulation.yaml eps.line_power_w` | EPS/all | Power budget (equipment list) | PDR | T | C | element `power_avg_w/power_peak_w`; KB `power_w`; `ModeElementRow.power_w_in_mode` |
| EP-17 | Mode-dependent unit powers (AOCS 1/2.5/4/4/9/15/12/6/7/9 W by mode) | `aocs_basic._MODE_POWER_W` (code) | AOCS/EPS | Power budget per mode | PDR | D | P | `ModeElementRow` power + duty; `OperationalMode.power_w`; `budgets.PowerModeProfile` |
| EP-18 | Load-shed order payload → fpa_cooler → ttc_tx → aocs_wheels → prop; trigger bus 25.0 V, hysteresis 0.5 V, auto-restore; SoC stages 30/20/10 % | `simulation.yaml eps.load_shed`; code `LOAD_SHED_ORDER`, `LOAD_SHED_VOLTAGE` 26.5 | EPS/FDIR | FDIR analysis, power management | CDR | T | M | — |
| EP-19 | UV/OV 26.5/29.5 V | `simulation.yaml` | EPS | EPS spec, FDIR | CDR | D | M | — |
| EP-20 | LCL trip per line (~150 %): obc 2.0, ttc_rx 0.3, ttc_tx 1.0, payload 2.5, cooler 1.0, htr_bat 0.5, htr_obc 0.3, wheels 0.8, prop 0.8 A; 50 ms | `simulation.yaml eps.overcurrent`; code `OC_THRESHOLDS` | EPS | EPS ICD / LCL ratings | CDR | D | P | power interface `current_a` (nominal), no trip level |
| EP-21 | S5 event levels: SoC 20/10/99 %, bus 27/25 V, bat 45/−5 °C, SA degraded < 0.7×expected | `simulation.yaml eps.event_thresholds` | EPS/FDIR | Event definitions | CDR | D | M | — |
| EP-22 | Array MPP voltage 32.4 V | `eps_basic._SA_MPP_V` (code) | EPS | Array string design | CDR | D | P | KB `solar_cells.voc_v`; no string/series design |

## 4. AOCS

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| AO-1 | Architecture: 3-axis zero-bias-momentum; 4 RW + 3 MTQ; 2 ST + gyro + 6 CSS + MAG + GPS | `aocs.yaml`, `aocs_basic.py` | AOCS | AOCS design report (ECSS-E-ST-60-30C) | SRR | T | P | KB RW/MTQ/ST/sun-sensor/GPS; `aocs.*.equipment_id`; D-3.2-AOCS; **no gyro/IMU and no standalone magnetometer KB category** |
| AO-2 | Mode set and codes OFF 0 … INERTIAL 9 (SAFE_BOOT, DETUMBLE, COARSE_SUN, NOMINAL, FINE_POINT, SLEW, DESAT, ECLIPSE) | `aocs/aocs_mode_codes.yaml` | AOCS/SYS | AOCS mode diagram, FSW mode manager | SRR | T | P | ConOps system modes only; `fsw/mode_manager.py` builds table from ConOps |
| AO-3 | Mode transitions/guards: min dwell 5/10/20/10 s…, DETUMBLE exit 0.5 °/s, auto ECLIPSE | `aocs_basic._MIN_DWELL` + logic | AOCS | Mode transition table | CDR | D | M | — |
| AO-4 | Mass 12 kg, inertia [[0.180,0.002,−0.003],[0.002,0.150,0.001],[−0.003,0.001,0.060]] kg·m² | `aocs.yaml mass_properties` | STR/AOCS | Mass-properties budget | PDR | T | P | `physics_closure` `mp_ixx/iyy/izz`, `mp_total_mass_kg` (diagonal only; `mass_properties.py` computes products but they are not published) |
| AO-5 | RW: 4 in pyramid az 45/135/225/315°, el 30°; 30 mN·m·s, 5500 rpm, 2 mN·m, I_w 5.2e-5 kg·m², bias 1200 rpm [+,−,+,−], desat 200 rpm | `reaction_wheels.*` | AOCS | Momentum budget / actuator sizing | PDR | T | P | KB `reaction_wheels` momentum/torque/speed (Sinclair RW-0.03 class present); `aocs.wheel_momentum_nms`, `aocs_wheel_margin_pct`; no geometry/cant/bias |
| AO-6 | RW motor τ 0.05 s, Coulomb 2e-6 N·m, viscous 1e-8 | `reaction_wheels.*` | AOCS | Unit model | CDR | D | M | — |
| AO-7 | MTQ 3 rods × 1.6 A·m² (NCTR-M016) | `magnetorquers` | AOCS | Actuator sizing | PDR | T | C | KB `dipole_moment_am2` (NCTR-M012 listed, not M016), element quantity |
| AO-8 | B-dot gain 5e5 A·m²/(T/s) | `bdot_gain_am2_per_tps` | AOCS | Control design | CDR | D | M | — |
| AO-9 | Desat law k = 0.002 s⁻¹, deadband 5e-4 N·m·s, timeout 3600 s, linear (not saturated) | `magnetorquers.desaturation` | AOCS | Momentum management | CDR | D | M | — |
| AO-10 | PD gains per mode (ωn, ζ): NOMINAL 0.040/0.70, FINE 0.080/0.75, SLEW 0.060/0.90, DESAT 0.020/0.70, ECLIPSE & INERTIAL 0.040/0.70 | `aocs_basic._MODE_CTRL` (code) | AOCS | Control design | CDR | D | M | — |
| AO-11 | FINE deadband 0.005°; 3-of-4 wheel FINE allowed, deadband ×4, flagged 0x0299 | `attitude_error_deadband_deg`; code | AOCS | Pointing budget, FDIR | CDR | D | M | — |
| AO-12 | Disturbances: residual dipole [0.008,−0.005,0.006] A·m², drag area 0.06 m², cp-cg 0.03 m, SRP area 0.34 m², Cd 2.2, Cr 1.5 | `disturbances.*` | AOCS | Disturbance-torque analysis | PDR | D | P | `aocs_*_torque_nm`, `mp_cp_cg_offset_m`; KB MTQ `residual_dipole_am2`; scalar dipole, Cd/Cr not exposed |
| AO-13 | Pointing performance NOMINAL 0.020° / FINE 0.007° 1σ; imaging band ~0.05° | `_MODE_ERR_SIGMA_DEG` (code) | AOCS/PL | Pointing error budget (ECSS-E-ST-60-10C) | PDR | T | C | `aocs.pointing_accuracy_deg`, `aocs_pointing_est_deg/margin_deg`; `payloads[0].pointing_accuracy_deg` |
| AO-14 | ST: NEA 6″ cross / 40″ roll, LF bias 3″, misalign 15″, 4 Hz FINE/1 Hz, boot 60 s, sun exclusion 15° | `sensors.star_tracker`; `_ST_BOOT_TIME`, `_ST_EXCLUSION_DEG` | AOCS | Sensor spec | PDR | D | P | KB `star_trackers.accuracy_arcsec/update_rate_hz/sun_exclusion_deg/fov_deg` (NST present) |
| AO-15 | ST accommodation: ST1 +Z, ST2 +Z canted 45° to +Y (anti-sun side for this LTAN) | `_ST_BORESIGHTS`; `geometry.yaml` | AOCS/CFG | Accommodation / FOV-exclusion analysis | PDR | T | P | optical interface `boresight/fov_deg/keep_out`; adapter hard-codes the same layout |
| AO-16 | Gyro: ARW 0.001 °/√s, bias 0.1 °/h (τ 1800 s), range 400 °/s, tempco 2e-6 °/s/K | `sensors.gyro` | AOCS | Sensor spec | PDR | D | M | no gyro KB category |
| AO-17 | Gyro calibration arc 300 s (30–1800), rate ≤ 0.10 °/s, settle 30 s | `sensors.gyro.calibration` | AOCS/OPS | Commissioning plan | CDR | D | M | — |
| AO-18 | MAG noise 50 nT; CSS on 6 faces (noise 0.02) | code `mag_noise`, `CSS_NORMALS` | AOCS | Sensor spec / accommodation | PDR | D | P | KB `sun_sensors.accuracy_deg/fov_deg`; MTQ `includes_magnetometer` |
| AO-19 | GPS TTFF cold/warm/hot 60/30/5 s; ECEF PVT | code `_gps_*_ttff_s` | AOCS/OBDH | GNSS spec | PDR | D | P | KB `gps_receivers.cold_start_s/position_accuracy_m` |
| AO-20 | Estimator MEKF (q + gyro bias), dead-axis ARW 0.1 | code; `dead_axis_arw_dps_rtsec` | AOCS | AOCS design (estimation) | CDR | D | M | — |

## 5. TCS (thermal)

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| TC-1 | Philosophy: passive coatings + Z-93 radiator on −Z; 3 heater circuits (battery, OBC, catbed); FPA cooler | `tcs.yaml` | TCS | TCS architecture (ECSS-E-ST-31C) | SRR | T | P | `thermal.heater_power_w`, `thermal.radiator_area_m2`; KB `thermal_hardware`; D-3.1-THERMAL |
| TC-2 | 16-node network: structure 3.2 kg; panels ±X 0.42, ±Y 0.19, +Z 0.12, −Z 0.15 kg; wings 1.07 kg; obc 0.35; battery 540 J/K; ttc 0.30; payload 1.1; aocs 0.9; prop 1830 J/K; thruster 50 J/K; cp 896/900 | `network.nodes` | TCS | Thermal mathematical model (TMM) | PDR | T | P | `run_thermal_closure`: one node per subsystem / hot component + bus; no face-panel or wing nodes |
| TC-3 | External surfaces: area per face, coating fractions α/ε (cells 0.91/0.85; Z-93 0.17/0.92; aperture 0.90/0.88; wing back 0.75/0.85) | `network.surfaces` | TCS/CFG | GMM/TMM, coating selection | PDR | T | P | agent extras `thermal.surfaces` (one OSR radiator + MLI), `thermal_network` per-node ε; KB α/ε; no per-face coating map |
| TC-4 | 18 conductive links G (e.g. payload–panel_mz 1.5, battery–panel_py 0.25, hinge 0.05, thruster–prop 0.0417 W/K) | `network.conductors` | TCS/STR | TMM | PDR | D | P | thermal interfaces `properties.conductance_w_per_k` (used by `physics_closure`) |
| TC-5 | 7 internal radiative links εA | `network.radiative` | TCS | TMM | CDR | D | M | — |
| TC-6 | Dissipation map line → node (OBC 50/50 obc/structure; TX 85 % heat; cooler rejects to structure) | `network.dissipation`, `residual_node` | TCS/EPS | TMM heat-load map | PDR | D | P | element power → node heat at 100 %; no RF-out fraction or reject node |
| TC-7 | Heaters: battery 8 W on 5/off 10 °C; OBC 4 W −10/−5 °C; catbed 12 W 190/230 °C | `heaters` (code fallback battery 6 W) | TCS | Heater sizing, thermostat setpoints | PDR | T | P | total `thermal.heater_power_w`; thermal interface `heater_power_w`; no setpoints |
| TC-8 | Temperature limits: battery warn 0/40, alarm −10/50; OBC −10/50, −20/60; FPA −22/14, −25.5/17.5; runaway 2 °C/min | `event_thresholds`; `mcs/limits.yaml` | TCS | Temperature-limits table (TCS spec) | PDR | T | C | element `performance.op_temp_min_c/max_c`, KB `operating_temp_c`, `thermal_margin_hot/cold_c` |
| TC-9 | FPA cooler: set-point −15 °C (−20…0), lift 40 K, 15 W, Carnot 0.23, imaging load 2 W, ±0.5 K 3σ, imaging max −3 °C, uncooled max 12.5 °C | `fpa_*`, `fpa_envelope`; `payload.yaml` | TCS/PL | Payload thermal ICD | PDR | T | M | no cooler KB; payload only `temperature_range_c` |
| TC-10 | Cold-soak conductances/offsets (battery 0.30, obc 0.6, thruster 0.0417 W/K) | `cold_soak` | TCS | TMM (failure cases) | CDR | D | M | — |
| TC-11 | Stowed-wing contact 1.0 W/K | `stowed_wing_contact_w_per_k` | TCS/STR | TMM (stowed config) | CDR | D | M | — |
| TC-12 | Decontamination heating capability (TC f47/48, 0x0418) | `tc_catalog`, code | TCS/PL | Contamination control plan | PDR | D | M | — |
| TC-13 | Hot/cold case predictions | emergent | TCS | Thermal analysis report | PDR | D | C | `thermal_t_hot_c/t_cold_c` per element, `THERMAL_OUT_OF_RANGE` |

## 6. OBDH (on-board computer, buses, time, memory)

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| OB-1 | Dual cold-redundant OBC A/B | `obdh_basic.py` (`obc_b_status`), S2 0x0500/0x0501 | OBDH | Avionics architecture (ECSS-E-ST-50) | SRR | T | P | element `quantity`, `redundancy_type` (no hot/cold semantics); KB `obcs` |
| OB-2 | Dual CAN bus; bus A = eps, tcs, aocs; bus B = ttc, payload | `obdh_basic` `bus_a/b_subsystems` (code default) | OBDH | Data-bus ICD / avionics block diagram | PDR | T | P | data interfaces `protocol/address`; `interface_rules` default **I2C for nano**; `harness_designer`; no bus redundancy/node allocation |
| OB-3 | OBC modes nominal / safe / emergency | `obdh.yaml modes` | OBDH/SYS | FSW mode concept | SRR | T | P | ConOps modes |
| OB-4 | Boot concept: bootloader (APID 2, beacon SID 11) → `OBC_BOOT_APP`, 10 s CRC window, boot inhibit, image A/B | code `BOOT_STATE_*`; `memory_map.yaml` | OBDH/SW | FSW architecture / boot SRS | PDR | T | M | — |
| OB-5 | Watchdog 30 s, enable/disable | `watchdog_period_ticks` | OBDH | FSW / FDIR | CDR | D | M | template requirement text SR-OBC-001 only |
| OB-6 | Reboot handling: >4 reboots → emergency; reboot cause codes; switch bus after excessive reboots | `fdir.yaml`, `s19_rules.yaml` | FDIR | FDIR analysis | CDR | D | M | — |
| OB-7 | CPU 35 % baseline, 12 tasks, stack 35 %, heap 40 % | `cpu_baseline_pct`; code | SW | Computer-resource budget (ECSS-E-ST-40C) | PDR | D | P | `margin_policy.yaml data_handling.cpu_max_peak_percent/ram_max_used_percent` (policy only); KB `clock_mhz/ram_mb` |
| OB-8 | Memory map: Boot ROM 64 KiB ×2, App A/B 512 KiB, Config 128 KiB, HK 1 MiB, Event 512 KiB, Science 8 MiB, Alarm 256 KiB, RAM 256+128 KiB | `subsystems/memory_map.yaml`, `memory/memory_map.yaml` | OBDH/SW | Memory budget / SDD | CDR | D | P | `data.storage_required_gb`; KB `flash_mb/ram_mb/storage_gb`; no partition map |
| OB-9 | S15 stores HK 1 MiB, Event 512 KiB, Science 8 MiB, Alarm 256 KiB | `mcs/pus_services.yaml s15` | OBDH/OPS | Data budget, PUS tailoring | PDR | D | P | `data.storage_required_gb` only |
| OB-10 | Mass memory for science 20 000 MB, 8 segments | `payload.yaml total_storage_mb, num_memory_segments` | PL/OBDH | Data budget | PDR | T | C | `data.storage_required_gb`; D-3.3-DATA (segments not modelled) |
| OB-11 | Onboard clock: TCXO 12 ± 4 ppm, GPS discipline + holdover, jump event 1 s | `clock_*` | OBDH | Time-management design (PUS S9) | PDR | D | P | timing interface (`pps/clock`, `accuracy_us`); KB timing only for ground |
| OB-12 | Time code CUC coarse+fine, epoch J2000 | `mission.yaml time_epoch` | SW | TM/TC ICD (CCSDS 301.0-B) | PDR | D | M | — |
| OB-13 | SEU counting + memory scrub (EDAC) | code `seu_count`, TC f51 | OBDH | SEE mitigation | PDR | D | P | `radiation.see_rate_per_day`, `radiation.electronics_class` |
| OB-14 | OBC dissipation 3 W | `eps.yaml obc_power_w` split | OBDH | Power budget | PDR | D | C | element `power_avg_w` |

## 7. TT&C and RF chain

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| TT-1 | Band plan: S-band UL 2025 / DL 2200 MHz; UHF beacon 437.5 MHz | `ttc.yaml` | TTC | Frequency plan, spectrum filing (ITU RR, ECSS-E-ST-50-05C) | SRR | T | P | KB `transponders.band/frequency_mhz`; rf interface `band/frequency_mhz`; `services/spectrum.py`; D-3.3-BAND; `interface_rules` default UHF for nano; SMO exporter hard-codes DL 8200 MHz |
| TT-2 | Two transponders primary/redundant; auto-switch after 24 h command loss or RSSI < −105 dBm | code `mode`, `cmd_loss_*` | TTC/FDIR | TT&C architecture; FDIR | SRR | T | P | `quantity/redundancy_type`; no command-loss timer |
| TT-3 | TM rate ladder: SAFE 1 kbps BPSK conv+RS (7.5 dB, bootloader only); LOW 16 kbps BPSK conv+RS; HIGH 128 kbps QPSK RS (6.0 dB; needs antenna deployed, downlink mode, el ≥ 10°) | `tm_rate_tiers` | TTC | Link budget / modcod plan (CCSDS 131.0-B, 401.0-B) | PDR | T | P | `link.downlink_rate_bps` single rate; KB `data_rate_bps/modulation`; D-3.3-MODCOD text |
| TT-4 | TC uplink 4000 bps (1 k / 64 k lock pacing) | `tc_uplink_rate_bps`; code | TTC | Link budget | PDR | T | P | `link.uplink_margin_db` computed; no uplink-rate design parameter |
| TT-5 | EIRP 10 dBW @ 2 W RF; PA levels 1/2/5 W; S/C gain 3 dBi | `eirp_dbw`, `pa_*`, `sc_gain_dbi` | TTC | Link budget | PDR | T | C | `compute_link_budget(tx_power_w, tx_antenna_gain_dbi)`; KB `tx_power_w`, antenna `gain_dbi` |
| TT-6 | Losses atm 0.5, pol 0.3, impl 2.0 dB; G/T derate < 10° 1.5 dB, < 30° 0.5 dB; required Eb/N0 9.6 dB | `ttc.yaml` | TTC | Link budget | PDR | D | C | link-budget args (`polarisation_mismatch_loss_db`, `implementation_loss_db`, `required_eb_n0_db`); elevation derate absent |
| TT-7 | DC power TX 5/11 W, RX 1.5 W | `eps.yaml transponder_*` | TTC/EPS | Power budget | PDR | D | C | `link.ttc_power_w`, element power |
| TT-8 | Antennas: S-band patch (face not fixed; −Z assumed), UHF tape dipole 0.17 m deployable; HIGH tier needs antenna deployed | `geometry.yaml antennas`; code `antenna_deployed` | TTC/CFG | Antenna accommodation, deployment ICD | PDR | T | P | KB `antennas.gain_dbi/deployment`; adapter places patches nadir |
| TT-9 | Beacon: 1 W RF, 1 kbps, 0 dBi, GS G/T −8 dB/K, DC 1.8/0.2 W, on ttc_rx line, HK SID 11 @ 30 s | `ttc.yaml beacon` | TTC/OPS | Beacon definition (IARU coordination) | SRR | T | P | can be modelled as 2nd transponder element; no beacon content |
| TT-10 | Coherent transponder / ranging (TC f76–78) | code | TTC/MA | Orbit-determination concept | SRR | T | M | — |
| TT-11 | CCSDS TM frame 1115 B, SCID 1, VC0 RT / VC1 playback / VC7 idle, FECF, RS(255,223) (+conv K=7 r=1/2 on air) | `rfsim.yaml ccsds` | TTC/SW | Space-link ICD (CCSDS 132.0-B, 131.0-B), SANA SCID | PDR | T | M | — |
| TT-12 | Modulator: RRC α 0.35, Gray coding, CLTU 4 ksym/s, loop BW 0.08 | `rfsim.yaml pipeline` | TTC | Transponder ICD | CDR | D | M | — |
| TT-13 | Path loss 153.5 dB, delay 1.71 ms, Eb/N0 10 dB, BER 1e-6 | `rfsim.yaml channel` | TTC | Link budget | PDR | D | C | link budget FSPL/margins |
| TT-14 | Ground RF limits: BER yellow 1e-5 / red 1e-4; AGC thresholds | `rfsim.yaml ground_limits` | GS/OPS | Ground MCS limits | CDR | D | M | — |
| TT-15 | S-band allocation checks 2025–2110 / 2200–2290 MHz | `ttc_basic.UL/DL_BAND_MHZ` | TTC | Spectrum (ITU RR) | SRR | D | C | `services/spectrum.py` |

## 8. Payload

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| PL-1 | Pushbroom multispectral, 4 bands 443/560/665/865 nm (bw 20/20/20/40), SNR 40/50/48/42 | `mission.yaml payload.bands`; `payload_basic.SPECTRAL_BANDS` (code) | PL | Instrument requirements | MDR/PDR | T | P | `PayloadRequirements.type/description` (bands as text) |
| PL-2 | Reference part Simera TriScape100 (1.1 kg, 98×98×176 mm) | `eps.yaml` comments; tcs payload node | PL | Equipment list | PDR | T | M | **no payload/imager KB category** |
| PL-3 | Optics 8192 px × 5.5 µm, f = 84.5 mm → FOV 29.856° (GSD ≈ 33 m @ 513 km) | `payload.yaml`; `planner.yaml imaging.fov_deg`; `geometry.yaml` | PL | Instrument design / coverage | PDR | T | P | `PayloadRequirements.fov_deg` (template 5°); `physics/payload_sizing.py` |
| PL-4 | 12 bit/px, line rate 244 Hz, 96 Mbps, image 4 MB | `payload.yaml` | PL/OBDH | Data budget | PDR | T | C | `payload.0.data_rate_mbps`, `duty_cycle`, `data.generated_per_day_gb` (image size absent) |
| PL-5 | Power imaging 5.5 W / idle 2.4 W | `eps.yaml payload_*` | PL/EPS | Power budget | PDR | T | C | `PayloadRequirements.power_w/power_peak_w` |
| PL-6 | Storage 8 segments with bad-segment marking | `num_memory_segments`; TC f31 | PL/OBDH | Mass-memory design | CDR | D | M | — |
| PL-7 | Commandable settings: compression, integration time, gain, band config, filter, shutter, cal lamp | TC f26–39, 92–95, 119 | PL | Instrument ICD / user manual | CDR | D | M | — |
| PL-8 | Calibration concept (dark, cal lamp, inertial star fields via mode 9) | COM-011, AOCS mode 9 | PL/OPS | Calibration plan | PDR | D | P | ConOps `ModeType.CALIBRATION` |
| PL-9 | Imaging activity 660 s (630–900), daylight, nominal attitude, max off-nadir, min solar elevation | `planning/activity_types.yaml`, `planner.yaml imaging` | PL/OPS | ConOps / planning rules | SRR | T | P | `OperationalMode.typical_duration_s/duty_cycle/sun_illuminated/nadir_pointing`; no solar-elevation / off-nadir limits |

## 9. Propulsion

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| PR-1 | Need + type: 1 × green monoprop ADN (LMP-103S) thruster for drag make-up | `prop.yaml` | PROP/MA | Propulsion architecture | SRR | T | C | `propulsion.type`; KB `thrusters` (HPGP-01, 1N HPGP); D-3.4-PROPULSION |
| PR-2 | Propellant 0.400 kg, ρ 1240 kg/m³, tank 560 cm³ | `prop.yaml` | PROP | Propellant budget, tank sizing | PDR | T | P | `propulsion.propellant_mass_kg`; `margin_policy tank_volume_margin_percent`; **no tank KB category** |
| PR-3 | Blow-down 22 → 9.33 bar | `tank_pressure_bol/eol_bar` | PROP | Pressure schedule | PDR | D | P | fluid interface `pressure_bar` |
| PR-4 | Thrust 0.33 N BOL; Isp 220 → 196 s | `thrust_bol_n`, `isp_*` | PROP | Performance model | PDR | T | C | `propulsion.isp_s`; KB `thrust_n/isp_s` (no blow-down curve) |
| PR-5 | ΔV capability / budget | `dv_remaining` | PROP/MA | ΔV budget | PRR | T | C | `propulsion.delta_v_total_ms`, `orbit.delta_v_*` |
| PR-6 | Thrust axis +X, offset 5 mm → 1.65 mN·m | `thrust_axis`, `thrust_offset_mm`; `geometry.yaml thrusters` | PROP/AOCS/CFG | Configuration, disturbance analysis | PDR | D | P | element `position_json`, `mp_com_*`; no thrust vector / misalignment |
| PR-7 | Valve drivers 2 W, catbed heater 12 W, catbed ≥ 180 °C | `valve_power_w`, `catbed_heater_w` | PROP/TCS | Power budget | PDR | D | P | element power |
| PR-8 | Inhibits: arm code 0xA5C3, arm window 300 s, latch A/B + FCV | `prop.yaml`, code | PROP/SYS | Safety (CDS min propulsion inhibits), FDIR | PDR | T | P | `cds_rules safety.min_propulsion_inhibits`; electrical_signal `inhibit_count` |
| PR-9 | Burn interlocks: catbed ≥ 180 °C, 6–24 bar, ≥ 5 g, AOCS mode ∈ {4,5,9}, att err ≤ 2°, SoC ≥ 45 %, phase ≥ NOMINAL, no eclipse burn | `prop.yaml interlocks` | PROP/FDIR/OPS | Flight rules / FDIR | CDR | D | M | — |
| PR-10 | Abort limits: att err 2°, p < 4 bar, catbed > 350 °C, t_burn > 300 s | `prop.yaml abort` | PROP/FDIR | FDIR | CDR | D | M | — |

## 10. Structure, configuration and mass

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| ST-1 | 6U, CDS envelope 100 × 226 × 366 mm | `geometry.yaml bus.size_m` | STR/SYS | Configuration, CDS compliance | SRR | T | C | `spacecraft_class`, `cds_rules.yaml envelope_mm/cubesat_form_factors`, D-3.4-FORMFACTOR, adapter `formFactor` |
| ST-2 | Body frame +X ≈ velocity, +Y = orbit normal, +Z = zenith, −Z = nadir (ruling Q4) | `geometry.yaml`, `aocs.yaml` | SYS/AOCS | Coordinate-systems definition | PDR | T | P | `mass_properties.py` uses x forward, y starboard, **z nadir** — opposite Z sense to the sim |
| ST-3 | Quaternion convention xyzw, ECI → body | `geometry.yaml quaternion` | AOCS/SW | TM/TC ICD | PDR | D | M | — |
| ST-4 | Unit placement (payload −Z 0.183 m, ST positions, thruster −X, antennas) | `geometry.yaml position_m` | CFG | Configuration drawing | PDR | D | P | element `position_json`; adapter heuristics |
| ST-5 | Dry mass 12.0 kg | `aocs.yaml mass_kg`, `prop.yaml sc_dry_mass_kg` | SYS | Mass budget | PDR | T | C | `mass.dry_mass_kg`, element roll-up |
| ST-6 | Wet mass 12.4 kg | derived | SYS | Mass budget | PDR | D | C | `mass.wet_mass_kg` |

## 11. Data handling: TM/TC database, PUS, FDIR

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| DH-1 | PUS-C as TM/TC standard; services 1, 2, 3, 5, 6, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20 | `mission.yaml pus_version`, `mcs/pus_services.yaml` | SW/OPS | PUS tailoring (ECSS-E-ST-70-41C), SSRD | SRR | T | P | FSW generator's architecture doc names ST[03] etc.; template `applicable_ecss` has no ECSS-E-ST-70-41C |
| DH-2 | Service capacities: S3 32 SIDs, S5 500 log, S6 4096 B dump, S11 256, S12 64, S18 16 × 32 steps, S19 32 | `pus_services.yaml` | SW | PUS tailoring / SRS | PDR | D | M | — |
| DH-3 | APID plan: application 1, bootloader 2 | `mission.yaml` | SW | TM/TC ICD, APID allocation (CCSDS 133.0-B) | PDR | T | P | FSW generator uses per-subsystem APIDs 0x100–0x700 (conflict); SMO exporter hard-codes 1/2 |
| DH-4 | SCID 1 | `rfsim.yaml ccsds.scid` | TTC/SW | Space-link ICD / SANA | PDR | T | M | — |
| DH-5 | Parameter catalogue: 457 TM parameters (aocs 154, eps 79, payload 61, ttc 46, tcs 41, obdh 38, prop 28, other 10), id blocks 0x01xx–0x0Bxx, units | `telemetry/parameters.yaml` | SW/all | TM/TC DB (ECSS-E-ST-70-31C, XTCE CCSDS 660) | CDR | D | P | `ParamIDAllocator` numbers *design* quantities; `fsw/generator.CATEGORY_TM_FIELDS` gives per-KB-category TM field lists |
| DH-6 | HK definitions: 11 SIDs — 1 EPS 1 s/52 p; 8 EPS-PM 8 s/15; 2 AOCS 4 s/75; 7 AOCS-DET 4 s/42; 3 TCS 60 s/18; 4 Platform 8 s/36; 5 Payload 8 s/29; 6 TTC 8 s/25; 9 PROP 8 s/23; 11 Beacon 30 s/7; 12 GPS 8 s/12; pack formats; default-enabled SIDs 1, 11 | `telemetry/hk_structures.yaml`, `simulation.yaml housekeeping` | SW/OPS | TM DB, HK plan | CDR | D | M | exporter hard-codes 6 SIDs |
| DH-7 | HK data volume (feeds data budget) | derived | SW/TTC | Data budget | PDR | D | P | data budget is payload-only; planner `hk_background_mb_per_hour` |
| DH-8 | TC catalogue: 220 TCs; S8,1 120 function IDs (AOCS 0–15/84–91/96, EPS 16–25/81–83, payload 26–39/92–95/119, TCS 40–49, OBC 50–62/80, TTC 63–79/97–99, PROP 108–118, SYS 120, legacy 100–107); quick commands | `commands/tc_catalog.yaml` | SW/all | TC DB / SSRD / SUM | CDR | D | M | exporter emits 11 placeholder S8 functions |
| DH-9 | S2 device table: 48 devices 0x0100–0x0604 (PDU buses, 4 RW, 2 ST, 3 gyros, MAG, 3 MTQ, CSS, GPS, 10 heater zones, thermistors, 2 xpdr, PA, LNA, antenna drive, OBC A/B, MMU, WDT, CAN, FPA, cooler, cal lamp, shutter, compression) | `tc_catalog.yaml` S2 | SW/SYS | Equipment list ↔ device ICD | CDR | D | P | element tree + quantity is the equipment list; no device IDs |
| DH-10 | Event catalogue: 155 S5 events with severities | `events/event_catalog.yaml` | SW/FDIR | Event definitions | CDR | D | M | — |
| DH-11 | Derived parameters | `telemetry/derived.yaml` | OPS | MCS DB | CDR | D | M | — |
| DH-12 | OBCPs: pass preparation, safe-mode entry, orbit manoeuvre, payload checkout | `obcp/*.yaml` | OPS/SW | OBCP definitions (ECSS-E-ST-70-01C) | CDR | D | M | — |
| DH-13 | Generated XTCE + SMP2/SMDL | `xtce/eosat1.xml`, `smdl/*.xml` | SW | XTCE, SMP2 (ECSS-E-ST-40-07) | CDR | D | M | nothing to generate from on design side |
| FD-1 | FDIR concept: levels 1 (unit) → 2 (subsystem safe) → 3 (spacecraft emergency); onboard S12 + S19 + rule table | `subsystems/fdir.yaml`, `monitoring/*` | SYS/FDIR | FDIR concept / analysis (ECSS-E-ST-70-11C operability; FMECA ECSS-Q-ST-30-02C) | SRR | T | P | D-5.2-FDIR text record; FMECA gives modes, not detection/response |
| FD-2 | S12 monitoring table: 41 definitions (SoC 20/10 %, bus 27/25 V, RW ±5000 rpm, att err 1°, ST blind, gyro bias ±0.5, FPA −22/14, OBC −20/60, CPU 90 %, storage 95 %, prop bands…) | `monitoring/s12_definitions.yaml` | FDIR | S12 table | CDR | D | M | — |
| FD-3 | S19 event-action: 30 rules (UV → payload off; SoC crit → cooler/payload off; momentum sat → desat; ST blind → switch/fallback; PA overheat → PA off; cmd loss → switch xpdr; reboots → switch bus; storage full; prop aborts…) | `monitoring/s19_rules.yaml` | FDIR | Event-action table | CDR | D | M | — |
| FD-4 | Onboard rule table: 17 rules (SoC < 20 payload off L1, < 15 safe L2; bus < 24.5 safe, < 23.2 AOCS safe; bat > 42 heater off; att err > 5° for 420 s (phase ≥ 6) safe; OBC > 65 °C; reboot > 4 emergency; RW temp > 65 disable; wheels < 2 safe; CAN loss emergency; PA > 75 °C) | `subsystems/fdir.yaml` | FDIR | FDIR analysis | CDR | D | M | — |
| FD-5 | Fault cascades (9) + recovery escalation 3 attempts, 30/60/120 s; recovery procedures per level | `fdir/fault_propagation.yaml`, `fdir/procedures/*.yaml` | FDIR | FDIR analysis / FMECA effects | PDR | D | P | `fmeca.py` effect propagation through subsystem graph; `failure_modes.yaml` local/system effects |
| FD-6 | Safe-mode definition (COARSE_SUN, TX LOW tier, payload/cooler off) | `fdir/procedures/safe_mode_entry.yaml`, `obcp/02_safe_mode_entry.yaml`, `ttc.yaml safe_tier` | SYS/FDIR | Safe-mode spec | SRR | T | P | ConOps `ModeType.SAFE` (power, pointing); `mission_simulation` guard |
| FD-7 | Failure catalogue: 61 injectable failures with expected symptoms (ttc 14, aocs 11, obdh 10, eps 9, tcs 8, payload 5, prop 4) | `instructor/expected_symptoms.yaml`, model `FAILURE_SPECS` | FDIR/RAMS | FMECA (ECSS-Q-ST-30-02C) | PDR | D | P | `failure_modes.yaml`: 15 unit types, ~22 modes; RPN; no symptom/detection parameter link |

## 12. Operations and ground segment

| ID | Decision (value) | Sim source | Owner | Design product / standard | Gate | Cls | CDF | SpaceCDF evidence / gap |
|---|---|---|---|---|---|---|---|---|
| GS-1 | Ground network: Iqaluit, Troll, Svalbard, Inuvik, O'Higgins; lat/lon/alt; mask 5° | `orbit.yaml ground_stations` | GS/MA | Ground-segment design, contact analysis | SRR | T | C | `MissionRequirements.ground_stations` (names), KB `ground_stations/networks.yaml`, `ground_closure`, D-5.1-GROUND (exporter maps unknown names to Svalbard coordinates) |
| GS-2 | Station RF: dishes 9 / 7.3 / 11.3 m…, G/T 20 / 18.5 dB/K…, TX 200 W, S-band | `planning/ground_stations.yaml` | GS/TTC | Link budget, GS ICD | PDR | T | C | KB `g_over_t_db_k/eirp_dbw/antenna_diameter_m`; per-station margins in `ground_closure` |
| GS-3 | Contact statistics 103 passes / 48 h, median gap 33 min, max 79 min | `tools/pass_gap_analysis.py` | MA/OPS | Contact analysis | PRR | D | C | `orbit.contact_time_per_day_s`, `gs_contacts_per_day`, `ground_scheduler` |
| GS-4 | Station planning priority / payload-dump support | `planner.yaml stations` | OPS | Ops plan | PDR | D | M | — |
| GS-5 | Auto TX-off hold 300 s after contact | `simulation.yaml ttc.auto_tx_hold_s` | OPS/TTC | Onboard autonomy / RF inhibit policy | CDR | D | M | — |
| OP-1 | Ops organisation: 7 positions (Flight Director, Power & Thermal, Flight Dynamics/AOCS, TT&C, Payload Ops, FDIR/Systems, Propulsion) with allowed services, function IDs, tabs | `mcs/positions.yaml`, `mcs/role_analysis/*.md` | OPS | Mission operations plan (ECSS-E-ST-70C) | PDR | T | P | design `seats.yaml` is the design team, not ops; frontend positions `mission_ops/ground_segment`; D-5.2-STAFFING text; exporter emits 6 hard-coded names |
| OP-2 | GO/NO-GO matrix: 11 situations | `mcs/gonogo_matrix.yaml` | OPS | Flight rules | CDR | D | M | — |
| OP-3 | Procedures (FOP): 70 = LEOP 7, commissioning 13, nominal 14, contingency 30, emergency 6 | `procedures/procedure_index.yaml` | OPS | Flight operations plan (ECSS-E-ST-70C) | CDR | D | P | ConOps phases; `ground_configurator` generic commissioning sequence |
| OP-4 | LEOP sequence: sep timer → bootloader beacon → first AOS → boot app → detumble → sun acquisition + wing deploy → time sync → IOD → sequential power-on | `procedures/leop/*` | OPS/SYS | LEOP plan, ConOps | SRR | T | P | D-5.1-LEOP text; `_derive_mission_profile` fixed T+ offsets |
| OP-5 | Commissioning order COM-001 … COM-013 | `procedures/commissioning/*` | OPS | Commissioning plan | PDR | D | P | `ground_configurator` commissioning sequence |
| OP-6 | MCS limits: 49 yellow/red sets | `mcs/limits.yaml` | OPS | MCS DB limits | CDR | D | P | requirement thresholds + element temperature ranges could seed red limits |
| OP-7 | Staleness rules, displays, alarm procedures, voice loops | `mcs/staleness.yaml`, `displays.yaml`, `alarm_procedures.yaml`, `voice/voice_loops.yaml` | OPS | MCS configuration | CDR | D | M | — |
| OP-8 | Planner activity types (10): imaging 660 s, dump 360 s, calibration 330 s, HK 60 s, SW upload 1200 s, desat 1800 s, thermal rebalance 300 s, load shed 60 s, FDIR recovery 180 s, manoeuvre 2100 s — each with power, data, attitude/daylight/contact/subsystem constraints | `planning/activity_types.yaml` | OPS/MA | ConOps / planning rules | PDR | D | P | `OperationalMode` (power, duration, contact, sunlit) + `ModeElementRow` |
| OP-9 | Planner resource rules: initial SoC 80 %, min SoC 25 %, protocol overhead, storage margin, HK background | `planner.yaml budget` | OPS/SYS | Ops resource rules | PDR | D | P | `margin_policy storage_margin_percent`; battery min SoC |
| OP-10 | Standard plans | `planning/standard_plans.yaml` | OPS | Ops plan | CDR | D | M | — |
| OP-11 | Ops reports (pass report, daily ops review, anomaly investigation) | `reports/*.yaml` | OPS | Ops products | CDR | D | M | — |

## 13. Simulator-only implementation details (not design decisions; design tool need not decide)

| Item | Value | Source |
|---|---|---|
| Tick / sub-stepping | dt_max 1 s, 600 substeps; `tick_hz` null; mission `network.sim_tick_hz` 1.0 | `simulation.yaml tick` |
| RNG seed | 20260731 (models), rfsim 42 | `simulation.yaml seed`, `rfsim.yaml channel.seed` |
| Time acceleration | default 1×, max 1000× | `simulation.yaml speed` |
| AOCS integrator | RK4 h 0.5 s, 120 substeps, SECULAR bypass > 60× | `aocs.yaml integration` |
| TCS integrator, sensor noise | 0.4 τ, ≤ 20 s; 0.05 K | `tcs.yaml network.integration` |
| Initial conditions | SoC 90 %, battery 15 °C, node temps 5–15 °C, FPA −5 °C | `simulation.yaml eps.initial`, `tcs.yaml` |
| Failure onset/intermittency | gradual 90 s; flicker 2–6 s, on 2–8 s, off 5–20 s | `simulation.yaml failures` |
| Scenario defaults | 1800 s, difficulty levels, response targets detect 300 … plan 1800 s | `simulation.yaml scenario_defaults`, `scenarios/*.yaml` (36) |
| Snapshots | keep 10, 48 h, 25/250 MB | `simulation.yaml auto_snapshots` |
| Ports / transport | TC 8001, TM 8002, instr 8003, HTTP 8080, VR 8100/8101, MCS 8011/8012, radio 8094, ZMQ 5555 | `mission.yaml network`, `rfsim.yaml network` |
| RF sim fidelity | PACKET/FRAME/RF mode, sps 8, conv coding disabled (Python Viterbi too slow), fading/phase-noise flags | `rfsim.yaml` |
| Model selectors | `model: eps_basic` etc. | all subsystem files |
| RT TM pacing, backlog 2000 | — | `simulation.yaml ttc` |
| Planner horizons, refresh, alignment tolerances | — | `planner.yaml` |
| Worksheets, manuals, i18n | — | `worksheets/`, `manual/`, `i18n/` |

---

## 14. Coverage summary (T + D rows; S excluded)

### By subsystem

| Section | Rows | C | P | M | % C | % C+P |
|---|---|---|---|---|---|---|
| Mission and orbit | 15 | 5 | 7 | 3 | 33 | 80 |
| EPS | 22 | 5 | 12 | 5 | 23 | 77 |
| AOCS | 20 | 2 | 9 | 9 | 10 | 55 |
| TCS | 13 | 2 | 6 | 5 | 15 | 62 |
| OBDH | 14 | 2 | 8 | 4 | 14 | 71 |
| TT&C + RF | 15 | 5 | 6 | 4 | 33 | 73 |
| Payload | 9 | 2 | 4 | 3 | 22 | 67 |
| Propulsion | 10 | 3 | 5 | 2 | 30 | 80 |
| Structure / config / mass | 6 | 3 | 2 | 1 | 50 | 83 |
| TM/TC DB + FDIR | 20 | 0 | 9 | 11 | 0 | 45 |
| Ops + ground | 16 | 3 | 7 | 6 | 19 | 63 |
| **Total** | **160** | **32** | **75** | **53** | **20** | **67** |

### By class

| Class | Rows | C | P | M |
|---|---|---|---|---|
| T (top-level) | 70 | 22 | 37 | 11 |
| D (derived/detailed) | 90 | 10 | 38 | 42 |

### By gate

| Gate | Rows | C | P | M | Note |
|---|---|---|---|---|---|
| MDR | 3 | 3 | 0 | 0 | |
| PRR | 8 | 4 | 3 | 1 | |
| SRR | 23 | 5 | 15 | 3 | architecture choices mostly held only as logbook text (P) |
| PDR | 79 | 20 | 47 | 12 | sizing values captured; layouts and tables partial |
| CDR | 47 | 0 | 10 | 37 | **SpaceCDF has no CDR gate** (`gate_profiles.yaml` canonical_gates = mdr, prr, srr, pdr): 79 % of CDR items missing, none captured |

(Counted mechanically from the §2–§12 tables; PL-1 "MDR/PDR" counted at PDR.)

Reading: what SpaceCDF does well is the Phase 0–B **sizing** (budgets, equipment choice, link and power numbers). What it lacks is (1) everything the simulator needs at **CDR**: TM/TC DB, FDIR tables, control laws/gains, mode machines, thermal network detail, onboard autonomy thresholds; (2) **structured tables** where it only has a scalar (rate ladder, per-face array areas, per-line LCLs, per-mode powers by unit, coating map, heater set-points); (3) operations products (positions, FOP, flight rules).

---

## 15. Model needs — the design-to-sim export contract

What a design must supply to configure the EOSAT-1-class simulator automatically. Target = current sim schema (`sim/packages/smo-common/src/smo_common/config/schemas.py`, strict). "Source" = existing SpaceCDF source or **NEW** (structure SpaceCDF must add).

### 15.1 Mission / orbit / environment → `mission.yaml`, `orbit.yaml`, `simulation.yaml tcs.environment`

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `name`, `description` | str | — | `MissionRequirements.name`, mission statement |
| `spacecraft_apid`, `bootloader_apid` | int (11-bit) | — | **NEW** APID plan (data-handling element) |
| `start_in_bootloader` | bool | — | **NEW** boot concept |
| `pus_version`, `time_epoch` | int, ISO-8601 | — | **NEW** PUS tailoring / time-code decision |
| `tle_line1/2` or (a, e, i, Ω, ω, M) + `t0_epoch` | str / float[6] + ISO-8601 | km, deg | `OrbitRequirements` + **NEW** epoch, LTAN→RAAN conversion (`orbit_gen.keplerian_to_tle` exists) |
| `altitude_km`, `inclination_deg` | float | km, deg | `OrbitRequirements` |
| `ground_stations[]` {name, lat_deg, lon_deg, alt_km, min_elevation_deg} | list | deg, km | KB `ground_stations` via selected ground elements (`ground_closure` context) |
| `solar_flux_w_m2`, `albedo`, `earth_ir_w_m2` | float | W/m², — | thermal environment constants (make per-study) |

### 15.2 EPS → `subsystems/eps.yaml`, `simulation.yaml eps`

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `battery.capacity_wh, voltage_nom, soc_100_v, soc_0_v, internal_r_ohm, charge_efficiency, discharge_efficiency, cv_taper_start_soc_pct` | float | Wh, V, Ω, —, % | KB battery (`capacity_wh`, `voltage_v`) + **NEW** KB fields (OCV end-points, R_int, η) |
| `cell_efficiency`, `technology` | float, str | — | KB `solar_cells` |
| `array_losses.{inherent_degradation, temp_coeff_per_c, temp_ref_c, array_temp_sunlit_c, harness_efficiency, annual_degradation, design_life_years}` | float | —, 1/°C, °C, %/yr, yr | KB cell + **NEW** loss-stack params on SA element |
| `solar_panels.{px,mx,py,my,pz,mz}_area_m2` | float ×6 | m² | **NEW** per-face cell area on body-panel elements |
| `solar_panels.wing_{py,my}_area_m2`, `wing_deploy_time_s` | float | m², s | SA wing elements (`performance.area_m2`, mounting face **NEW**), HDRM `activation_time_s` |
| `sada_present, sada_axis, sada_tracking, sada_max_rate_deg_s` | bool, enum{x,y,z}, bool, float | deg/s | **NEW** SADA element/KB category |
| `obc_power_w, payload_power_w, payload_standby_power_w, fpa_cooler_power_w, transponder_power_w, transponder_hi_power_w, transponder_rx_power_w` | float | W | element `power_avg_w/power_peak_w` + `ModeElementRow` per-mode power |
| `simulation.yaml eps.line_power_w{htr_bat, htr_obc, aocs_wheels, prop}` | float | W | heater / wheel / prop elements |
| `power_lines{name: default_on}` + line list (code `POWER_LINE_DEFS`) | map<str,bool> | — | **NEW** PCDU channel table: power interfaces `switched` + LEOP default state |
| `uv_threshold_v, ov_threshold_v` | float | V | **NEW** EPS protection spec |
| `load_shed.{order[], bus_voltage_v, restore_hysteresis_v, auto_restore, soc_stage_thresholds_pct[]}` | list<str>, float, bool | V, % | **NEW** load-shed table (FDIR) |
| `overcurrent.{trip_time_s, thresholds_a{line}}` | float, map | s, A | **NEW** LCL rating on each switched power interface |
| `event_thresholds.{soc_low_pct, soc_critical_pct, soc_charge_complete_pct, bus_warning_v, bus_critical_v, bat_overtemp_c, bat_undertemp_c, sa_degraded_fraction}` | float | %, V, °C | **NEW** EPS monitoring table |

### 15.3 AOCS → `subsystems/aocs.yaml`, `aocs/aocs_mode_codes.yaml` (+ values now hard-coded in `aocs_basic.py`)

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `mass_properties.mass_kg`, `inertia_kgm2` | float, float[3][3] | kg, kg·m² | `physics_closure` mp_* (publish full tensor incl. products) |
| `reaction_wheels.{count, geometry, max_speed_rpm, nominal_speed_rpm, desaturation_speed_rpm, rotor_inertia_kgm2, max_torque_nm, motor_tau_s, coulomb_friction_nm, viscous_friction_nm_per_rads}` | int, enum, float | rpm, kg·m², N·m, s | KB RW (+ **NEW** rotor inertia, friction, τ) + **NEW** wheel-geometry decision (az/el) |
| `magnetorquers.{count, max_dipole_am2, bdot_gain_am2_per_tps, desaturation.{gain_per_s, deadband_nms, timeout_s, saturate_rods}}` | int, float, bool | A·m², s⁻¹, N·m·s, s | KB MTQ + **NEW** control-law parameters |
| `disturbances.{residual_dipole_am2[3], drag_area_m2, cp_cg_offset_m, srp_area_m2, cd, cr, rho_kgm3}` | float[3], float | A·m², m², m, —, kg/m³ | `mp_cp_cg_offset_m`, areas from geometry, KB residual dipole (vector **NEW**) |
| `sensors.star_tracker.{nea_cross_arcsec, nea_roll_arcsec, lf_bias_arcsec, misalign_arcsec}` + boresights, exclusion, boot time | float, vec3 | arcsec, deg, s | KB star tracker (+ split NEA **NEW**), optical interface boresight/keep-out |
| `sensors.gyro.{arw_dps_rtsec, bias_tau_s, bias_ss_dps, noise_dps, max_rate_dps, tempco_dps_per_k, dead_axis_arw_dps_rtsec, calibration.*}` | float | °/√s, s, °/s, °/s/K | **NEW** gyro/IMU KB category |
| magnetometer noise, CSS faces/noise, GPS TTFF | float, list | nT, —, s | **NEW** magnetometer KB; KB sun sensors; KB GPS `cold_start_s` |
| `modes[]` + mode codes, min dwell, transition guards, per-mode (ωn, ζ), per-mode power, per-mode pointing σ | table | rad/s, —, W, deg, s | **NEW** AOCS mode table (could extend ConOps `OperationalMode` with an `aocs_mode` child table) |
| `attitude_error_deadband_deg` | float | deg | `aocs.pointing_accuracy_deg` (today mis-mapped by exporter: accuracy ≠ deadband) |

### 15.4 TCS → `subsystems/tcs.yaml`

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `network.nodes[] {name, mass_kg, cp_j_per_kg_k | capacitance_j_per_k, initial_c}` | list | kg, J/kg/K, J/K, °C | `physics_closure` thermal nodes (add face-panel + wing nodes; cp per material from KB `materials`) |
| `network.surfaces[] {node, normal|wing+side, area_m2, array_face, coatings[]{fraction, alpha, epsilon}}` | list | m², — | **NEW** per-face coating map (geometry + KB `thermal_hardware` α/ε) |
| `network.conductors[] {a, b, g_w_per_k}` | list | W/K | thermal interfaces `conductance_w_per_k` |
| `network.radiative[] {a, b, ea_m2}` | list | m² | **NEW** |
| `network.dissipation{line: {node: fraction}}`, `residual_node`, `default_dissipation_w` | map | —, W | element→node mapping from element tree + **NEW** heat fraction (TX RF-out) |
| `heaters[] {name, power_w, on_temp_c, off_temp_c}`, `heater_nodes` | list | W, °C | heater elements + **NEW** thermostat set-points |
| `fpa_cooler_* , fpa_envelope.*` | float | °C, K, W | **NEW** cooler element (payload thermal ICD) |
| `event_thresholds.temperature_warning/alarm{unit: [lo, hi]}`, `thermal_runaway_rate_deg_per_min` | map<str,[float,float]> | °C | element `op_temp_min/max_c` (+ alarm margin policy **NEW**) |
| `cold_soak.*`, `stowed_wing_contact_w_per_k` | map, float | W/K, °C | **NEW** |

### 15.5 OBDH → `subsystems/obdh.yaml`, `memory_map.yaml`, `mcs/pus_services.yaml`

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `modes[]` | list<str> | — | **NEW** OBC mode list |
| `watchdog_period_ticks`, `cpu_baseline_pct` | int, float | s, % | **NEW** FSW resource budget |
| `clock_drift_ppm_nominal, clock_drift_sigma_ppm, clock_gps_discipline, clock_jump_event_threshold_s` | float, bool | ppm, s | KB OBC (**NEW** oscillator stability), timing interface |
| OBC redundancy (A/B cold), bus A/B membership (code default) | enum, map<bus,[subsystem]> | — | element `redundancy_type` + data interfaces grouped by bus (**NEW** expose as config) |
| `memory_regions[] {name, start, size, type}` | list | bytes | **NEW** memory map from OBC flash/RAM + storage budget |
| `s15.stores[] {id, name, capacity_bytes}` and service capacities | list | bytes | **NEW** PUS tailoring |

### 15.6 TT&C / RF → `subsystems/ttc.yaml`, `rfsim.yaml`, `planning/ground_stations.yaml`

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `ul_freq_mhz, dl_freq_mhz` | float | MHz | KB transponder `frequency_mhz` / rf interface |
| `tm_rate_tiers[] {name, bps, command_code, modulation, coding, coding_gain_db, bootloader_only, requires_antenna, requires_downlink_mode, min_elevation_deg}`, `default_tier, beacon_tier, safe_tier` | list | bps, dB, deg | **NEW** rate-ladder table (today single `link.downlink_rate_bps`) |
| `tc_uplink_rate_bps` | int | bps | **NEW** design param (link agent input) |
| `eirp_dbw, pa_ref_power_w, pa_low/nominal/max_power_w, sc_gain_dbi` | float | dBW, W, dBi | KB transponder + antenna; link budget |
| `atmospheric/polarization/implementation_loss_db, gt_derate_below_10/30deg_db, required_eb_n0_db, coding_gain_db` | float | dB | link-budget inputs (+ derate **NEW**) |
| `cmd_loss_switch_timeout_s, cmd_loss_rssi_threshold_dbm` | float | s, dBm | **NEW** TT&C FDIR |
| `beacon.{enabled, dl_freq_mhz, band_mhz, rf_power_w, sc_gain_dbi, gs_g_t_db, bps, …, dc_power_w, standby_dc_power_w, eps_line, hk_sid}` | object | MHz, W, dB | beacon transponder element (**NEW** role) |
| `rfsim.ccsds.{tm_frame_length, scid, vc_*, fecf_present, rs_enabled, convolutional_enabled}` | int, bool | bytes | **NEW** space-link ICD |
| `rfsim.link_budget.*`, `ground_limits.*` | float | dB | link budget + **NEW** ground limits |
| station `{antenna_diameter_m, band, g_t_db, tx_power_w, tx/rx_freq_mhz}` | float, str | m, dB/K, W, MHz | KB ground stations / ground elements |

### 15.7 Payload → `subsystems/payload.yaml` (+ `SPECTRAL_BANDS` now in code)

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `pixels_across_track, pixel_pitch_um, focal_length_mm, bits_per_pixel, line_rate_hz, data_rate_mbps` | int, float | —, µm, mm, bit, Hz, Mbps | **NEW** imager KB/element fields (`payload_sizing.py` has some physics) |
| bands[] {id, center_nm, bandwidth_nm, snr_nominal} | list | nm, — | **NEW** band table in `PayloadRequirements` |
| `image_size_mb, total_storage_mb, num_memory_segments` | float, int | MB | data budget + **NEW** image size |
| `fpa_cooler_target_c, fpa_ambient_c, fpa_tau_cooling_s, fpa_tau_warming_s, detector_offset_c` | float | °C, s | **NEW** cooler/FPA thermal |
| imaging/idle power | float | W | `PayloadRequirements.power_w/peak` |

### 15.8 Propulsion → `subsystems/prop.yaml`

| Sim key | Type | Unit | Source |
|---|---|---|---|
| `propellant, sc_dry_mass_kg, propellant_mass_kg, propellant_density_kg_m3, tank_volume_cm3` | str, float | kg, kg/m³, cm³ | `propulsion.*`, `mass.dry_mass_kg` + **NEW** tank KB |
| `tank_pressure_bol_bar, tank_pressure_eol_bar` | float | bar | **NEW** blow-down; fluid interface |
| `thrust_bol_n, isp_bol_s, isp_eol_s` | float | N, s | KB thruster (+ EOL **NEW**) |
| `thrust_axis[3], thrust_offset_mm` | float[3], float | —, mm | **NEW** thruster mounting (element position + axis) |
| `valve_power_w, catbed_heater_w` | float | W | element power |
| `arm_code, arm_window_s, interlocks.*, abort.*` | int, float, list | s, °C, bar, g, deg, % | **NEW** propulsion safety/FDIR table |

### 15.9 Geometry → `geometry.yaml` (`c2o.geometry/1`)
Already emitted by `designAdapter.designGeometry`; needs designed (not heuristic) inputs: per-face cell areas, wing face/panel count/size, SADA axis and 0°/90° normals, ST boresights/positions/FOV/exclusions, payload boresight/position/FOV, antenna kind/position/boresight/length, thruster position/axis. Also add frame convention (sim +Z zenith vs `mass_properties.py` z nadir).

### 15.10 TM/TC DB, monitoring, ops (CDR products) → `telemetry/*`, `commands/tc_catalog.yaml`, `events/`, `monitoring/`, `fdir/`, `mcs/`, `procedures/`, `planning/`

| Sim file | Content type | Source |
|---|---|---|
| `telemetry/parameters.yaml` | list {id uint16, name, subsystem, units, description} | **NEW** TM point list per element (seed: `fsw/generator.CATEGORY_TM_FIELDS`) |
| `telemetry/hk_structures.yaml` | list {sid, name, interval_s, parameters[]{param_id, pack_format, scale}} | **NEW** HK plan (rates feed data budget) |
| `commands/tc_catalog.yaml` | list {name, service, subtype, func_id/device_id, fields[]{name, type}} | **NEW** TC list per element/function (functions model exists: `models/functions.py`) |
| `events/event_catalog.yaml` | list {id, name, severity, subsystem} | **NEW** |
| `monitoring/s12_definitions.yaml` | list {param_id, check_type, low, high, severity} | **NEW** (seed from requirements with `threshold_param_path` + element temperature ranges) |
| `monitoring/s19_rules.yaml`, `subsystems/fdir.yaml`, `fdir/fault_propagation.yaml`, `fdir/procedures/*` | event→action / param→action tables, cascades, escalation | **NEW** FDIR table linked to FMECA rows |
| `mcs/positions.yaml` | positions {subsystems, allowed_services, allowed_func_ids, visible_tabs} | **NEW** ops organisation (seat → position mapping) |
| `mcs/limits.yaml`, `staleness.yaml` | limits per param | derive from S12 + TM DB |
| `planning/activity_types.yaml`, `planner.yaml` | activities {duration, power, data, attitude, daylight, contact, subsystems} | ConOps `OperationalMode` + `ModeElementRow` |
| `procedures/procedure_index.yaml` + bodies | FOP | out of scope for auto-generation; LEOP/commissioning skeleton from ConOps phases |
| `instructor/expected_symptoms.yaml`, scenarios | failure → symptom | FMECA rows + TM DB |

---

## 16. Fifteen most important gaps (ranked)

1. **No CDR gate or CDR products in SpaceCDF** (`gate_profiles.yaml` stops at PDR; no TM/TC DB, FDIR spec, FOP, TMM product) — 37 of 47 CDR-level simulator decisions have nowhere to live and none is fully captured.
2. **SMO exporter is stale and would be rejected** by the sim's strict schemas (`ground_segment`, `platform_idle_power_w`), uses retired `arrays:`, X-band 8200 MHz, and emits hard-coded placeholder FDIR/S12/S19/events/TC/HK unrelated to the design (`exporters/smo/exporter.py`).
3. **No TM/TC database model** (parameters, HK SIDs/rates, TC/function IDs, S2 device IDs, events, APIDs/SCID) — the sim's 457 params, 11 SIDs, 220 TCs, 155 events cannot be designed or exported; nothing for XTCE.
4. **No FDIR design model**: S12 limits, S19 event-actions, rule levels, persistence, load-shed order/stages, safe-mode content, recovery escalation. FMECA modes are not linked to detection parameters or responses. The sim spreads one bus-UV decision over 6 inconsistent values (UV 26.5, event 27/25, load-shed 25.0, FDIR 24.5 and 23.2, cascade 23.0 V).
5. **No AOCS mode machine or control design**: mode codes, transition guards, per-mode gains (ωn/ζ), B-dot and desat gains, deadbands — several are hard-coded in `aocs_basic.py` and not configurable either.
6. **TT&C rate ladder / modcod table missing**: SpaceCDF has one `link.downlink_rate_bps`; sim needs SAFE/LOW/HIGH tiers with modulation, coding gain, tier gating, plus beacon, uplink rate and command-loss switch-over.
7. **PCDU line table and protection missing**: switchable vs non-switchable lines, default states at separation, LCL trip currents, UV/OV, event thresholds (line list hard-coded in `eps_basic.POWER_LINE_DEFS`).
8. **Thermal model too coarse for export**: no per-face panel/wing nodes, no per-face coating map, no internal radiative couplings, no heater set-points, no cooler; the physics-closure network cannot become `tcs.yaml network`.
9. **Missing KB categories for flown units**: gyro/IMU, standalone magnetometer, payload imager (TriScape100), FPA cooler, propellant tank, SADA — so their model parameters have no home.
10. **Array layout not designed**: per-face body-cell areas, wing count/face/panel size, SADA axis are heuristics in `designAdapter.ts`; SA loss stack (inherent, temperature, MPPT, harness) absent from power physics.
11. **Reference orbit/epoch not a design product**: no TLE/epoch/LTAN→RAAN; `orbit_gen` uses RAAN 0 and epoch = now, router epoch 2026-01-01; EOSAT validation/template still 450 km, LTAN 10:30.
12. **OBDH architecture undecidable**: OBC cold redundancy, dual-CAN bus membership (code default), boot concept (bootloader/app, APID 2 beacon), watchdog, memory map, S15 store sizes, clock stability. The `interface_rules.yaml` nano-class defaults (7.4 V bus, I2C, UHF) would not reproduce EOSAT-1's 28 V / CAN / S-band design.
13. **Operations organisation and products absent**: design seats ≠ ops positions; no flight-ops seat, no positions/allowed-services model, no GO/NO-GO, no flight rules; the exporter hard-codes 6 position names.
14. **Inertia tensor and frame conventions incomplete**: products of inertia computed but not published; `mass_properties.py` z = nadir vs sim +Z = zenith; quaternion convention not recorded; residual dipole scalar instead of vector.
15. **Propulsion safety/ops table missing**: arm code/window, burn interlocks (catbed, pressure, AOCS mode, attitude error, SoC, phase, eclipse), abort limits, thrust axis/offset, blow-down curve, tank.

## 17. Simulator-side inconsistencies found while tracing (worth fixing in the sim or in the design record)

| Item | Evidence |
|---|---|
| Payload optics vs cited part | `payload.yaml` f = 84.5 mm, 5.5 µm → GSD ≈ 33 m @ 513 km; the comment's reference part (TriScape100) is quoted at 4.75 m GSD @ 500 km |
| Science store size | `mcs/pus_services.yaml` S15 Science Store 8 MiB (and `memory_map.yaml` 0x800000) vs `payload.yaml total_storage_mb: 20000` |
| Battery nominal voltage | `eps.yaml voltage_nom: 26.4` vs BPX datasheet 28.8 V quoted in the same block |
| Bus under-voltage thresholds | 26.5 (UV, code `LOAD_SHED_VOLTAGE`), 27/25 (events, S12), 25.0 (load shed), 24.5 and 23.2 (`fdir.yaml`), 23.0 (`fault_propagation.yaml`) |
| Heater fallbacks in code | `tcs_basic._HEATER_POWER battery 6.0` / thermostat (5, 1) vs `tcs.yaml` 8 W, 5/10 °C |
| Load-shed stage table | `fault_propagation.yaml` stages refer to lines that do not exist in the PCDU (`payload_aux`, `aocs_secondary`, `ttc_secondary`, `non_essential_heaters`) |
| S-band patch face | `geometry.yaml` notes ttc.yaml does not fix the mounting face (assumed −Z) |
