# EOSAT-1 Thermal Control Subsystem (TCS) {#eosat-1-thermal-control-subsystem-tcs}

**Document ID:** EOSAT1-UM-TCS-004
**Issue:** 2.0
**Date:** 2026-03-13
**Classification:** UNCLASSIFIED — Mission Operations

---

## 1. Overview {#1-overview}

The Thermal Control Subsystem (TCS) maintains all spacecraft components within their
allowable temperature ranges throughout the mission. EOSAT-1 uses passive thermal control
(surface coatings, the body-mounted cells, an isolated nadir radiator for the imager, and
where each unit is mounted) with three thermostat-controlled heaters: battery (8 W), OBC
(4 W) and thruster catalyst bed (12 W). Every unit's temperature follows the power it
dissipates, so the spacecraft cools in safe mode and in a load shed. The focal plane array
(FPA) cooler is managed as part of the payload subsystem.

## 2. Passive Thermal Control {#2-passive-thermal-control}

### 2.1 Insulation (no external MLI) {#21-multi-layer-insulation-mli}

EOSAT-1 flies no MLI blankets on its external faces: the body-mounted cells cover most of
the outside, and a 6U is too small for a blanketed bus to reject ~25–40 W. Insulation is
used internally instead:

- The imager and its nadir (-Z) radiator form a thermal island on low-conductance
  (titanium / G10) mounts, so the bus electronics and the FPA cooler's 15 W do not raise
  the cooler's heat sink.
- The battery stands off the frame on the cold +Y wall (see §2.2).

### 2.2 Radiators {#22-radiators}

The bus has no separate radiator panels: it rejects its heat through all six faces
(0.28 m2, emittance ~0.87 — cell coverglass and white paint). Two faces have a dedicated
thermal job:

| Face        | Area      | Role                                                                 |
|-------------|-----------|----------------------------------------------------------------------|
| -Z (nadir)  | 0.023 m2  | Imager radiator: white Z-93 paint, isolated from the bus with the imager |
| +Y          | 0.037 m2  | Battery wall: EOSAT-1's beta angle is -21 to -31 deg all year, so the Sun is always on the -Y side and +Y is never sunlit |

### 2.3 Surface Coatings {#23-surface-coatings}

| Surface                           | Solar absorptance | IR emittance |
|-----------------------------------|-------------------|--------------|
| Triple-junction cells, coverglass | 0.91              | 0.85         |
| White paint (Z-93), non-cell areas and -Z radiator | 0.17 | 0.92  |
| Imager aperture / baffle (black)  | 0.90              | 0.88         |

While the arrays are delivering power, about a fifth of the sunlight on the cells leaves as
electricity instead of heat.

## 3. Active Thermal Control {#3-active-thermal-control}

### 3.1 Battery Heater Circuit {#31-battery-heater-circuit}

The battery heater is the only active thermal control element on EOSAT-1. All other
components (OBC, structure, transponder) rely on passive thermal management through
spacecraft orientation, internal heat dissipation, and MLI/radiator design.

| Circuit     | Location         | Setpoint On | Setpoint Off | Power  |
|-------------|------------------|-------------|--------------|--------|
| Battery     | Battery pack     | 5 deg C     | 10 deg C     | 8 W    |

The battery heater is controlled via the `HEATER_CONTROL` command (S8,S1) with parameters
`circuit=battery` and `on` (boolean). Autonomous heater control is implemented in the FDIR
logic and will activate the heater if battery temperature falls below 5 deg C, overriding
ground commands if temperatures approach red limits.

**Note:** EOSAT-1 also carries an OBC heater and a thruster heater. The OBC heater
(`HEATER_OBC`, S8 func 41; status `htr_obc` 0x040B; 4 W on PDM line 6; thermostat ON -10 C /
OFF -5 C) is a survival heater: the OBC's own dissipation keeps it well above -10 C in
nominal and safe operations, and the heater works in a long load shed or cold-season
survival. It has about 7 K of authority (4 W across the stack's 0.6 W/K mount). The thruster catalyst-bed heater (`HEATER_THRUSTER`, S8 func 42;
status 0x041B; 12 W from the `prop` line) preheats the thruster before a manoeuvre.

### 3.2 Orientation for Passive Thermal Control {#32-orientation-for-passive-thermal-control}

EOSAT-1 uses spacecraft orientation as a passive thermal control strategy. The AOCS
attitude can be adjusted to present different faces to the Sun, allowing operators to
influence the thermal environment:

| Strategy                    | Effect                                          |
|-----------------------------|-------------------------------------------------|
| Nadir-point (nominal)       | Balanced thermal environment, standard ops      |
| Sun-point (+Y to Sun)       | Maximises solar heating on +Y, warms battery    |
| Eclipse-prep (thermal spin) | Distributes heat across faces before eclipse     |

This orientation-based thermal control is particularly important during LEOP and contingency
scenarios where active heater power must be conserved. In safe mode, the AOCS COARSE_SUN
mode orients the spacecraft towards the Sun, providing passive heating.

### 3.3 Heater Failure Modes {#33-heater-failure-modes}

| Failure Mode    | Detection                           | Impact                          |
|-----------------|-------------------------------------|---------------------------------|
| Heater stuck_on | Battery temp rising above setpoint; `htr_battery` stays 1 | Excessive power draw, potential battery over-temp |
| Heater open_circuit | Battery temp dropping below setpoint; `htr_battery` = 1 but no temp response | Battery freeze risk in eclipse |

If a stuck-on heater is detected, ground should command `HEATER_CONTROL` (circuit=battery,
on=false) and monitor. If the heater remains on, the PDM outlet feeding the heater circuit
can be commanded off as an isolation measure.

### 3.4 FPA Cooler {#34-fpa-cooler}

The focal plane array cooler is a miniature Stirling-cycle cryocooler that maintains the
imager detector at its operational temperature of approximately -15 deg C. The cooler
draws up to 15 W and requires a 30-minute cooldown period from ambient temperature.

| Parameter         | Value                        |
|-------------------|------------------------------|
| Cooler Type       | Stirling-cycle cryocooler    |
| Target FPA Temp   | -15 deg C (nominal)          |
| Cooldown Time     | ~30 min from ambient         |
| Power Consumption | 15 W                         |
| Control           | Autonomous via payload mode   |

The cooler is activated automatically when the payload transitions to STANDBY, IMAGING or
CALIBRATION mode and deactivated when the payload is set to OFF.

## 4. Temperature Zones {#4-temperature-zones}

| Zone           | Nominal Range    | Yellow Limits    | Red Limits       |
|----------------|------------------|------------------|------------------|
| Battery        | 5–25 deg C       | 2–40 deg C       | 0–45 deg C       |
| OBC            | 10–35 deg C      | -10–60 deg C     | -20–70 deg C     |
| FPA Detector   | -18 to -12 deg C | -22 to 14 deg C  | -25.5 to 17.5 deg C |
| Body panels    | -20 to 40 deg C  | —                | —                |
| Deployed wings | -55 to 65 deg C  | —                | —                |
| Structure      | -20 to 35 deg C  | —                | —                |

Typical orbit ranges (beta -30 deg; the bus tracks the power it dissipates):

| Case                                   | Structure      | OBC            | Battery        |
|----------------------------------------|----------------|----------------|----------------|
| Nominal, payload STANDBY (cooler running) | +15 to +29 deg C | +22 to +33 deg C | +16 to +22 deg C |
| Nominal, cooler off                    | +2 to +16 deg C  | +8 to +20 deg C  | +5 to +10 deg C (heater cycling) |
| Safe mode (sun-pointing)               | -7 to +7 deg C   | -1 to +10 deg C  | +5 to +10 deg C (heater cycling) |
| Long load shed, heater lines OFF       | -15 to -2 deg C  | -9 to +2 deg C   | -11 to -3 deg C  |

## 5. Telemetry Parameters {#5-telemetry-parameters}

| Param ID | Name            | Unit   | Description                          |
|----------|-----------------|--------|--------------------------------------|
| 0x0400   | temp_panel_px   | deg C  | +X panel temperature                 |
| 0x0401   | temp_panel_mx   | deg C  | -X panel temperature                 |
| 0x0402   | temp_panel_py   | deg C  | +Y panel temperature                 |
| 0x0403   | temp_panel_my   | deg C  | -Y panel temperature                 |
| 0x0404   | temp_panel_pz   | deg C  | +Z panel temperature (zenith)        |
| 0x0405   | temp_panel_mz   | deg C  | -Z panel temperature (nadir)         |
| 0x0406   | temp_obc        | deg C  | OBC module temperature               |
| 0x0407   | temp_battery    | deg C  | Battery pack temperature             |
| 0x0408   | temp_fpa        | deg C  | Focal plane array temperature        |
| 0x0409   | temp_thruster   | deg C  | Thruster valve temperature           |
| 0x040A   | htr_battery     | bool   | Battery heater status (on/off)       |
| 0x040B   | htr_obc         | bool   | OBC heater status (on/off)           |
| 0x040C   | cooler_fpa      | bool   | FPA cooler status (on/off)           |

## 6. Limit Definitions {#6-limit-definitions}

| Parameter       | Yellow Low | Yellow High | Red Low | Red High |
|-----------------|------------|-------------|---------|----------|
| temp_obc (C)    | -10        | 60          | -20     | 70       |
| temp_battery (C)| 2          | 40          | 0       | 45       |
| temp_fpa (C)    | -22.0      | 14.0        | -25.5   | 17.5     |

The OBC cold limits follow the hardware: CubeSat OBCs are rated down to -25 to -40 C, so
red -20 C keeps 5 K of margin on the -25 C class and yellow -10 C is also the OBC heater's
ON point.

The FPA bands are **derived**, not chosen: `subsystems/tcs.yaml: fpa_envelope`
is the single source, and the ground software computes the rest from it. The FPA node has two legitimate resting states — regulated
anywhere in the commandable **-20…0 deg C** setpoint envelope
(`PAYLOAD_COOLER_SETPOINT`, S8 func 36), and uncooled at about **+11.5 deg C**
(measured peak +12.4). The band brackets both, plus 3 sigma of control noise
(0.5 K) and a 1.5 K margin for yellow, 5.0 K for red. The previous
-18/+8, -20/+12 table predated the commandable setpoint and turned a legal
-20 deg C command into a standing red alarm.

**Being cold enough to image is not a limit.** That is the `fpa_ready` flag
(0x0610) and the `FPA_THERMAL_READY` / `FPA_THERMAL_NOT_READY` events
(0x040A / 0x040B): the loop settled about the *active* setpoint (-1 K / +5 K)
**and** the detector at or below **-3.0 deg C**. A decontamination bake-out
(+50 deg C) will breach the red high — deliberately. You have taken the
detector outside its operating envelope and the console should say so.

## 7. Commands {#7-commands}

| Command           | Service  | Parameters              | Description                        |
|-------------------|----------|-------------------------|------------------------------------|
| HEATER_CONTROL    | S8,S1    | circuit, on             | Enable/disable heater circuit      |
| HK_REQUEST        | S3,S27   | sid=4                   | Request TCS housekeeping packet    |
| GET_PARAM         | S20,S3   | param_id (0x0400–040C)  | Read individual TCS parameter      |
| SET_PARAM         | S20,S1   | param_id, value         | Modify TCS configuration parameter |

## 8. Panel Temperature Coupling to Solar Illumination {#8-panel-temperature-coupling-to-solar-illumination}

The five body-mounted solar panels (every face except -Z) act as the primary thermal interface between the
spacecraft and the space environment. Panel temperatures are strongly coupled to solar
illumination:

| Condition            | Panel Response                                       |
|----------------------|------------------------------------------------------|
| Sunlit (direct)      | Body panel rises to +30…+35 deg C; a wing to about +55…+65 deg C |
| Sunlit (oblique)     | Reduced heating; absorbed sunlight proportional to cos(sun angle) |
| Eclipse (shadowed)   | Wings cool to about -50 deg C at up to ~2 deg C/min; body panels follow the structure |
| Earth albedo / IR    | Steady heating of the nadir face (-Z) and the sides that see the Earth |

The thermal coupling mechanism works in both directions:

1. **Solar heating**: Direct solar flux heats the illuminated panel, which conducts heat
   into the spacecraft structure and adjacent components.
2. **Radiative cooling**: Shadowed panels radiate heat to deep space, drawing heat from
   the spacecraft interior.

This coupling is significant for thermal management because the solar panel temperatures
directly influence the battery compartment temperature (adjacent to the +Y/-Y panels) and
the OBC module temperature. Operators should monitor panel temperatures during attitude
manoeuvres to anticipate thermal transients.

## 9. Operational Notes {#9-operational-notes}

1. Eclipse entry causes a rapid temperature drop on exposed panels. The light deployable
   wings cool fastest, up to ~2 deg C/min.
2. Battery heater activation during eclipse is critical to maintain cell temperature above
   the minimum qualification limit of 0 deg C.
3. The FPA cooler should not be activated until the payload electronics have completed
   their power-on self-test (approximately 10 seconds after STANDBY command).
4. Panel temperatures (0x0400–0x0405) are informational and not subject to FDIR action.
   They are useful for thermal model correlation during commissioning and for predicting
   internal component temperatures based on the solar illumination pattern.
5. In SAFE mode the FPA cooler is powered off and the AOCS points +X at the Sun. Both
   heaters stay under thermostat; the OBC keeps itself warm with its own 3 W. In a long
   load shed (only the OBC and receiver powered, ~7.5 W) the whole spacecraft cools by
   15–25 K and, in the cold season, the OBC heads for its -10 C heater ON point: keep
   heater lines 5 and 6 powered under thermostat whenever the power budget allows.
6. Spacecraft orientation directly affects the thermal environment. During contingency
   operations, the Flight Director should coordinate with Power/Thermal and AOCS operators
   to select an attitude that balances power generation and thermal constraints.

## 10. Thermal Design Margins {#10-thermal-design-margins}

The thermal design provides at least 5 deg C margin to qualification limits under worst-case
hot and cold conditions (end-of-life, worst-case eclipse duration, maximum/minimum solar flux).
Margin verification is based on the thermal mathematical model correlated during the
commissioning phase.

---

*End of Document — EOSAT1-UM-TCS-004*
