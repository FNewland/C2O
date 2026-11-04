# Design to simulator: exporting a SpaceCDF study as a simulator configuration

Status: implemented 2026-11-03 (branch `sim-export`). This document covers the export
contract of `sim_design_inventory.md` §15 and the CDR export map
(`GET /api/cdr/export-map`).

## 1. What it does

SpaceCDF writes a **simulator configuration directory** from a study. The directory has
the layout of `sim/configs/eosat1` and runs with the EOSAT-1-class simulator, MCS and
planner. Every value in it comes from one of two places:

- the **design model**, written with `# design: <source>`, for example
  `capacity_wh: 100.0  # design: battery Battery (KB capacity_wh)`;
- a **documented default**, written with `# C2O default: <reason>`, for example
  `wing_deploy_time_s: 30.0  # C2O default: hinge release time not in the design (EOSAT-1 30 s)`.

Unless a note says otherwise, a default is the EOSAT-1 reference value. Simulator
implementation details carry the note `C2O default: simulator implementation detail (not a
design decision)`. Examples are the tick, the RNG seed, integrators, ports and snapshot
policy (inventory §13).

The export replaces the placeholder "Simulator Model Inputs" exporter
(`spacecdf_agents/exporters/smo/exporter.py`, now deleted). That exporter wrote an old
array format and X-band 8200 MHz, hard-coded its FDIR, limit, event, command and HK
tables, and wrote two keys the strict loader rejects.

## 2. How to export

**In SpaceCDF:** open *Export* and choose **Simulator configuration → ZIP**. A dialog opens
with the **readiness checklist**. For each CDR area it counts the values in four classes:

- taken from the design;
- still default;
- *missing in the design* (the design should hold it but does not);
- *not supported by the simulator* (the design holds it but the EOSAT-1-class models
  cannot represent it).

Each entry gives its reason, file and key. The dialog also shows whether the result loads
with the simulator's own strict loaders. **Download ZIP** fetches the directory.

**Over HTTP:**

| Route | Returns |
|---|---|
| `GET /api/studies/{sid}/export/sim-config` | readiness by area (`areas[].items[]`: `item`, `status`, `file`, `key`, `source`), `totals`, `dataset`, `validation {available, errors, checked}` |
| `GET /api/studies/{sid}/export/sim-config.zip` | the directory as `<mission>/…` in a zip, plus `README.md` (readiness in prose) and `export_report.json`. The `X-C2O-Validation` header is `ok`, `errors` or `unavailable` |
| `POST /api/exports/smo/{sid}` | the same files as JSON (`files: {path: yaml text}`, `readiness`, `is_valid`) for older clients |

The server needs the EOSAT-1 reference configuration, which supplies the defaults. It is
found at `sim/configs/eosat1` in the monorepo, or in `$SPACECDF_SIM_CONFIG_DIR`.
Validation also needs the simulator packages (`sim/packages/*/src`). When they are missing
the export still works and reports `validation.available = false`.

## 3. How to run it

```bash
unzip eosat_1_simconfig.zip -d ~/missions
cd sim
./start.sh --config=~/missions/eosat_1          # or: SMO_CONFIG_DIR=~/missions/eosat_1 ./start.sh
```

`start.sh --config=DIR` (new) points every service at `DIR`: the simulator, MCS, planner,
RF bridge and doc viewer. The default is still `configs/eosat1`. A relative path is taken
from where you run the script. A directory without `mission.yaml` stops start-up.

For a headless run, `SimulationEngine("<dir>")` works the same way. Set
`SMO_CONFIG_DIR=<dir>` as well so the commanding catalogue resolves against the same
directory. `sim/tools/power_budget.py --config <dir>` gives the power budget of the exported
design.

**Not exported:**

- `procedures/`, `manual/` and `worksheets/`. These are written for a spacecraft, not
  generated. The MCS and planner run without them.
- `i18n/`, `xtce/` and `smdl/`. To regenerate XTCE and SMDL, point
  `sim/tools/generate_xtce.py` and `generate_smdl.py` at the directory.

## 4. Where each value comes from

The simulator runs **EOSAT-1-class models**: a 9-line PCDU, a 4-wheel pyramid, a 16-node
thermal network, a fixed TM point set and a fixed S8 function map (the *model interface*).
A design sets the models' **numbers** and maps its own items onto the models' slots by
role:

- a design power line maps to a simulator line by the units it feeds;
- a design TM point or command maps by name;
- a design AOCS mode maps by name.

Anything with no slot is reported as *not supported*. Nothing is dropped silently.

| Area | From the design | Default (reason) |
|---|---|---|
| Mission & orbit | name; TLE from the orbit requirements (altitude, inclination, eccentricity); RAAN from the LTAN at T-0, using the solar right ascension (or `raan_deg`); T-0 = launch date at 12:00 UTC; ground stations (selected KB stations: lat, lon, altitude, mask) | epoch 2026-08-20T12:00Z without a launch date; LTAN 10:00 without LTAN or RAAN; argument of perigee and mean anomaly 90°/270° |
| EPS | battery capacity and OCV curve (KB `voltage_v` min/nominal/max); cell efficiency and type; body cells per face and ±Y wings (approved stack layout, else array elements: `performance.face_areas_m2` for body cells, deployable area split over ±Y); SADA present or absent; design life; OBC-line power (OBC + EPS boards); payload imaging/standby power (mode matrix, else peak/average); TX LOW/HIGH power; line state at power-on and LCL trips (electrical model lines mapped to the PCDU); bus-protection ladder, load-shed order, SoC stages, hysteresis and auto-restore (CDR load-shed table); heater, wheel and propulsion line powers; battery temperature events (operating range ± 5 K) | battery R_int, coulombic efficiencies, CV taper; array loss stack; wing deploy time; FPA cooler; ladder levels the design does not name (cascade = AOCS-safe − 0.2 V) |
| AOCS | mass and full inertia tensor (physics closure; SpaceCDF z-nadir frame rotated 180° about X into the simulator body frame); CP–CG; wheel speed, torque, rotor inertia (momentum ÷ speed); MTQ dipole; residual dipole; star-tracker NEA; drag/SRP areas; B-dot gain, desaturation law, deadband, wheel bias, DETUMBLE exit rate (CDR AOCS control); per-mode ωn/ζ, minimum dwell, power and pointing σ (CDR AOCS modes → `control.modes`) | wheel friction/motor model; gyro (no KB category); other transition guards; modes the design does not have |
| TCS | heater power and set-points (heater rows → battery / OBC / thruster circuits); battery and OBC warning limits (operating range) and alarm limits (± 10 K); node masses of structure, OBC, payload, TT&C, AOCS and battery capacitance | 16-node network couplings, surfaces, coatings; FPA envelope; thermal environment constants |
| OBDH | OBC count / redundancy (reported) | modes, watchdog, CPU budget, onboard clock |
| TT&C | DL frequency; antenna gain; EIRP and PA levels from the transmitter's RF power; ground-station G/T (lowest selected); rate ladder, default/beacon/safe tiers, uplink rate, command-loss timer, beacon (CDR TT&C); S-band patches (stack layout) | UL frequency without a KB value; link losses |
| Payload | detector pixels and pitch, focal length, data rate, line rate (= data rate ÷ pixels × bits × 4 bands), mass memory, FOV (planner) | band table (in the model), FPA/cooler model, image size, segments |
| Propulsion | thrust, Isp, propellant mass, dry mass | inhibits, interlocks, abort limits |
| Geometry | approved stack layout (`c2o.geometry/1` + frame/internal/mass_properties) | EOSAT-1 geometry with the exported cell areas and FOV copied in |
| TM/TC database | APIDs, PUS version, CUC epoch, SCID (CDR settings); per-subsystem HK APIDs (`mission.yaml hk_apids`) | see §5 |
| FDIR | bus-protection ladder, load shed (above); S12/S19/rule tables (§5) | — |
| Operations | flight rules → `ops/flight_rules.yaml` (read by nothing yet); GO/NO-GO; positions | procedures (not exported) |

**Copies the simulator cross-checks follow their single source.** The engine and geometry
loaders check some values against copies held in other files. The export keeps each copy
equal to its source:

- the S12 definitions and MCS limits on `eps.bus_voltage` follow
  `simulation.yaml eps.bus_protection`;
- the literal `threshold` next to a `threshold_ref` follows the named level;
- the fault-propagation load-shed SoC stages follow `load_shed.soc_stage_thresholds_pct`;
- the geometry cell areas follow `eps.yaml solar_panels`, the S-band patches follow
  `ttc.yaml sband_antennas`, and the payload FOV follows `planner.yaml`.

## 5. The TM/TC database: three cases

The case is the `dataset` value of the study's CDR model.

| `dataset` | What the export writes |
|---|---|
| `reference` (the read-only EOSAT-1 import) | TM parameters, HK structures, TC catalogue, events, S12, S19, FDIR rules, HK at boot, AOCS mode codes, positions, GO/NO-GO and MCS limits, all written from the CDR rows (`cdr_sim.export_sim`). Template-only keys are kept (quick-command metadata, position tabs). This is the round trip. |
| `design` (the study's own CDR database) | The **model interface catalogue stays**: the models write fixed parameter IDs and dispatch fixed function IDs. Items that map **by name** are applied to it: HK periods by subsystem and HK at boot; `arm_execute` and criticality of commands with a simulator namesake; MCS limits and S12 limits on parameters with a simulator namesake; position names; GO/NO-GO; flight rules. The **whole design database** is written to `design_db/` in the simulator's shapes, for reference. |
| `empty` | Model interface catalogue (EOSAT-1). The checklist reports the TM/TC database, FDIR tables and operations tables as missing. |

## 6. Simulator-side additions (the four gaps of the CDR export map)

| Gap | Now | Without the key |
|---|---|---|
| AOCS gains, minimum dwell, per-mode power and pointing σ, transition guards in `aocs_basic.py` code | `subsystems/aocs.yaml control.modes.<MODE>` (`omega_n_rad_s`, `zeta`, `min_dwell_s`, `power_w`, `pointing_sigma_deg`) and `control.transitions` (`safe_boot_init_s`, `detumble_exit_rate_dps`, `detumble_exit_hold_s`, `coarse_sun_error_deg`, `coarse_sun_hold_s`, `eclipse_entry_debounce_s`, `desat_exit_hold_s`), with a typed schema. EOSAT-1 ships the former code values verbatim. | the code tables (EOSAT-1 behaviour unchanged) |
| One APID for every packet | `mission.yaml hk_apids: {sid: apid}`. In the application image, periodic and requested S3.25 of a SID use its own APID with its own sequence counter. The bootloader keeps `bootloader_apid`; S1, S5 and the other reports stay on `spacecraft_apid`. The ground segment does not filter by APID. | every application packet from `spacecraft_apid` |
| Arm-then-execute only by criticality | `commands/tc_catalog.yaml commands[].arm_execute`. The loader fills it in when it is absent (`criticality: critical` arms). The modern MCS gates the two-step on it (`needsArm`). | inferred as before |
| Flight rules had no file | `ops/flight_rules.yaml` (id, text EN/FR, reference), written by the export and read by nothing yet | — |

Tests: `sim/tests/test_simulator/test_aocs_control_config.py`,
`test_hk_apid_map.py`, `tests/test_common/test_config_validation.py`
(`arm_execute`) and `tests/test_mcs/test_modern_page_behaviour.py` (`needsArm`).

## 7. Verification

`design/tests/test_api/test_sim_export.py`:

1. **Writer.** The commented YAML writer re-reads every one of the 60+ EOSAT-1 YAML files
   unchanged.
2. **EOSAT-1 round trip.** The study has the EOSAT-1 reference CDR import and EOSAT-1-like
   design elements: 6U, BPX battery, per-face body cells, 2 × 0.12 m² wings, SADA,
   S-band, 4 wheels, imager 5.5/2.4 W, 513 km / 97.39° / LTAN 10:00, three KB stations.
   The test exports it, validates the result with the simulator's strict loaders, and
   checks:
   - **exact match with EOSAT-1:** HK structures (SID, interval, parameter list), TM
     parameters, TC catalogue (name, service, subtype, function, position), events,
     S12 and S19 tables, rate ladder and TT&C settings, bus-protection ladder, load-shed
     order, HK enabled at boot, and AOCS `control.modes`;
   - **EPS against EOSAT-1:** battery and array areas, OBC and payload powers;
   - **power budget** (`tools/power_budget.py`, EOL worst β, nominal ops):

     | | EOSAT-1 | Export |
     |---|---|---|
     | Generation | 45.2 W | 44.5 W (−1.6 %) |
     | Load | 22.5 W | 21.8 W |
     | Margin ratio | 2.01 | 2.04 |

     The load is lower because three stations give less TX duty than EOSAT-1's five
     (35 passes/day against 51.5);
   - **the engine flies it headless:** all 7 models load. It cold-boots in the
     bootloader, waits for the first real pass (AOS at 1171 s), and boots the
     application in that pass (phase 3 → 4). HK SID 1 and the beacon arrive on the
     downlink until LOS. There is no engine fault and no copy-drift warning.
3. **A fresh design.** A 3U built from KB parts, not EOSAT: 4S battery, 3 wheels, iMTQ,
   Sagitta, GomSpace S-band, multispectral camera, 550 km, LTAN 13:30, launch
   2027-03-15. The test runs the electrical model, modes, stack layout and **designed**
   CDR database, then exports. The result loads and flies: real pass, boot, no faults.
   The checklist flags the wheel count as *not supported*.
4. **The API.** Readiness by area, validation available and clean, zip contents (no
   procedures or manual), and the old `POST /exports/smo` route.

## 8. Known limits

These are reported in the checklist, not hidden:

- **AOCS.** The simulator models 4 wheels in a pyramid. It has no gyro or magnetometer KB
  category, so their models are EOSAT-1's.
- **PCDU.** It has 9 fixed lines. A design line that feeds no simulator role is *not
  supported*. A design that switches a non-switchable line (OBC, receiver) off at boot is
  flagged.
- **TCS.** The 16-node network keeps EOSAT-1's couplings and coatings. The design sets
  node masses, heaters and limits.
- **TM/TC.** A designed database is applied to the model interface by name only; the rest
  of it is in `design_db/`.
- **Rate tiers.** The simulator's TTC_SET_DATA_RATE selects tiers named LOW and HIGH.
- **No propulsion in the design.** The simulator's propulsion model stays, with its line
  off.
- **Procedures.** Flight operations procedures are not generated.
