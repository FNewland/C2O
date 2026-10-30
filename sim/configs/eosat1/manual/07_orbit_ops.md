# EOSAT-1 Orbit Operations {#eosat-1-orbit-operations}

**Document ID:** EOSAT1-UM-ORB-008
**Issue:** 2.0
**Date:** 2026-03-13
**Classification:** UNCLASSIFIED — Mission Operations

---

## 1. Overview {#1-overview}

This document describes the orbital characteristics of EOSAT-1 and their operational
implications, including eclipse cycles, ground station contact geometry, imaging target
planning for ocean current monitoring, and pass-based scheduling.

## 2. Orbit Definition {#2-orbit-definition}

| Parameter              | Value                        |
|------------------------|------------------------------|
| Orbit Type             | Sun-Synchronous (SSO)        |
| Semi-Major Axis        | 6873.7 km                    |
| Altitude               | ~513 km mean geodetic (503–530 km) |
| Inclination            | 97.39 deg                    |
| Eccentricity           | ~0 (near-circular)           |
| LTAN                   | ~10:00 (descending node ~22:00) |
| Orbital Period         | ~94.5 min                    |
| Revolutions per Day    | 15.24                        |
| Nodal Regression Rate  | ~0.9856 deg/day (= 1 deg/day)|
| Ground Track Velocity  | ~7.06 km/s                   |

### 2.1 Sun-Synchronous Properties {#21-sun-synchronous-properties}

The 97.39 deg inclination causes the orbital plane to precess eastward at approximately
0.9856 deg/day, matching the Earth's mean motion around the Sun. It is the exact
sun-synchronous value for the TLE mean motion of 15.24 rev/day: SGP4's secular J2/J4 node
rate equals the Sun's rate at 97.39 deg, and the node drifts by less than 0.1 deg (under half
a minute of LTAN) over the 2-year active phase. (The earlier 98.0 deg figure precessed the
node about 1.07 deg/day and drifted the LTAN by about 2 h a year; the interim 97.45 deg,
computed from the altitude rather than the mean motion, drifted it about 0.4 h in 2 years.)
This ensures that:

- The local solar time at the ascending node (LTAN) remains approximately constant at ~10:00.
- The daylit ascending pass crosses the equator in mid-morning, so ocean imaging targets are
  observed under consistent lighting conditions across revisits, which is critical for ocean
  colour measurements.
- The orbit is not dawn-dusk: the spacecraft is eclipsed on every orbit (§3).

### 2.2 Ground Track {#22-ground-track}

The ground track repeats approximately every 5 days. The sub-satellite point traces a
sinusoidal pattern between latitudes +/- 82.6 deg (supplement of the inclination, 180 − 97.39). Successive
ground tracks are ~2 630 km apart at the equator; the 5-day repeat grid spacing is ~525 km. At the ~513 km mean
altitude the imager delivers a ~33 m ground sampling distance and a ~273 km swath
(both scale linearly with altitude), well matched to ocean feature detection.

## 3. Eclipse Cycle {#3-eclipse-cycle}

### 3.1 Eclipse Geometry {#31-eclipse-geometry}

At the ~513 km mean altitude, the Earth's shadow cone produces eclipses when the spacecraft passes
through the anti-solar region. For the ~10:00 LTAN orbit:

| Parameter              | Value                        |
|------------------------|------------------------------|
| Max Eclipse Duration   | ~35.2 min (beta about −21 deg) |
| Min Eclipse Duration   | ~33.2 min (beta about −31 deg) |
| Eclipse Season         | Every orbit, all year        |
| Orbit Fraction (max)   | ~37% of orbital period       |

### 3.2 Seasonal Variation {#32-seasonal-variation}

With the LTAN held at ~10:00, the beta angle stays between −20.8 and −31.2 deg over the
first year (SGP4 propagation of the `orbit.yaml` TLE, `tools/power_budget.py`). EOSAT-1 is
therefore eclipsed on every orbit, for 33.2–35.2 min (eclipse fraction 0.351–0.372). The table gives eclipse duration against beta at ~513 km (cylindrical
shadow, 94.5 min period); the rows above |beta| ~ 31 deg apply only to off-nominal orbits:

| Beta Angle Range | Eclipse Duration | Notes                        |
|------------------|------------------|------------------------------|
| |beta| > 68 deg  | 0 min            | Full sunlight (no eclipse)   |
| |beta| ~ 60 deg  | ~21 min          | Short eclipse                |
| |beta| ~ 30 deg  | ~34 min          | EOSAT-1 range (21–31 deg)    |
| |beta| < 20 deg  | ~35–36 min       | Maximum eclipse duration     |

### 3.3 Eclipse Operational Impact {#33-eclipse-operational-impact}

During eclipse:

1. **EPS**: Solar array output drops to zero. Battery provides full spacecraft power.
   Depth of discharge depends on eclipse duration and power consumption.
2. **TCS**: Rapid cooling of exposed surfaces. Battery and OBC heaters may activate.
3. **AOCS**: Star tracker may experience Earth/Sun blinding during eclipse transitions.
   Gyro-only propagation is used for up to 60 seconds.
4. **Payload**: Imaging produces dark frames (useful for detector calibration).

## 4. Ground Station Contact Geometry {#4-ground-station-contact-geometry}

### 4.1 Station Locations {#41-station-locations}

| Station    | Latitude   | Longitude  | Min Elev. | Approx. Contacts/Day |
|------------|------------|------------|-----------|----------------------|
| Iqaluit    | 63.747 N   | 68.518 W   | 5 deg     | ~9                   |
| Troll      | 72.012 S   | 2.535 E    | 5 deg     | ~11                  |
| Svalbard   | 78.230 N   | 15.398 E   | 5 deg     | ~13                  |
| Inuvik     | 68.320 N   | 133.550 W  | 5 deg     | ~10.5                |
| O'Higgins  | 63.321 S   | 57.901 W   | 5 deg     | ~8                   |

The five-station network (canonical list in `orbit.yaml`) provides bipolar coverage:

- **Svalbard** (KSAT SvalSat, Norway): the highest-latitude station, with the most passes and
  the highest elevations; the planner's first-priority downlink.
- **Inuvik** (Northwest Territories, Canada) and **Iqaluit** (Nunavut, Canada): northern
  hemisphere passes at the western and eastern longitudes of the Canadian Arctic.
- **Troll** (Queen Maud Land, Antarctica) and **O'Higgins** (Antarctic Peninsula): southern
  hemisphere passes. The 72 deg S latitude of Troll gives the most southern contacts.

All five carry the same role, S-band TT&C and data dump (manual 05 §5).

### 4.2 Typical Pass Profile {#42-typical-pass-profile}

A typical ground station contact follows this elevation profile:

```
Elevation
(deg)
  80 |          ___
  60 |        /     \
  40 |      /         \
  20 |    /             \
   5 |--/                 \--
   0 +-------------------------> Time
     AOS     TCA         LOS
```

| Phase | Abbreviation | Description                              |
|-------|--------------|------------------------------------------|
| AOS   | Acquisition  | Signal acquired at minimum elevation     |
| TCA   | Closest      | Maximum elevation (shortest slant range) |
| LOS   | Loss         | Signal lost below minimum elevation      |

### 4.3 Contact Duration vs. Maximum Elevation {#43-contact-duration-vs-maximum-elevation}

| Max Elevation | Approx. Duration | Link Quality     |
|---------------|-------------------|------------------|
| 5–10 deg      | up to ~6 min      | Marginal         |
| 10–30 deg     | ~6–9 min          | Acceptable       |
| 30–60 deg     | ~9 min            | Good             |
| 60–90 deg     | ~9.5 min          | Excellent        |

Durations are for the ~513 km orbit and the 5 deg mask (spherical geometry, Earth rotation
neglected). Over 48 h the mean contact is 6.7 min at Iqaluit, 7.4 min at Inuvik, 7.5 min at
O'Higgins and 7.8 min at Svalbard and Troll.

Higher maximum elevation passes provide longer contact times and better link margins.
The 10 deg line is not a rule of thumb here — it is the HIGH tier's hard gate. A pass
whose maximum elevation is below 10 deg can never run the 128 kbps dump tier, so it is
usable for commanding and for routine housekeeping at LOW (16 kbps) but carries no
imagery. Above 10 deg, only the arc above 10 deg holds HIGH: a 30 deg pass spends about
77 % of its window above the gate, a 12 deg pass only 47 %. The mission planner computes
that fraction from the pass geometry and books dumps accordingly, so a plan cannot quietly
assume a flat rate.

### 4.4 Visibility and Scheduling {#44-visibility-and-scheduling}

The bipolar station network provides complementary coverage. Combined, the five stations
provide:

- **Total contacts per day**: ~51
- **Cumulative contact time**: ~385 min/day
- **Gap between contacts**: ~33 min (median), ~79 min (worst case)

(48 h from the TLE epoch, `tools/pass_gap_analysis.py`.) With Iqaluit and Troll alone there
would be about 20 contacts per day and a worst gap of about 2.5 hours.

The contact window timeline in the MCS displays a 24-hour horizontal bar with the passes of
each station, with AOS/LOS times and maximum elevation annotated.

## 5. Orbit Determination {#5-orbit-determination}

Orbit determination is performed using:

- **Onboard GPS**: The zenith-mounted GPS receiver provides continuous position and velocity
  measurements (sub-satellite latitude, longitude, altitude). This is the primary orbit
  determination source.
- **Ranging data**: Slant range measurements from the S-band transponder during contacts,
  used for independent verification.
- **Two-line elements (TLE)**: Published by space surveillance networks, used as backup.

The `range_km` (0x0509) and `contact_elevation` (0x050A) telemetry parameters provide
real-time range and elevation data during ground contacts. The GPS-derived position is
available in `sc_lat` (0x0210), `sc_lon` (0x0211), and `sc_alt` (0x0212).

The OBC runs ADCS software for orbit determination. Orbit control is limited to
ground-planned burns of the propulsion module (see §6).

## 6. Orbit Maintenance {#6-orbit-maintenance}

EOSAT-1 carries a 1U green-monopropellant blowdown module (0.400 kg LMP-103S, ~67 m/s total delta-V;
S8 funcs 108–118) for debris-avoidance manoeuvres, limited drag make-up and the end-of-life
disposal burn (ruling Q3 as amended, 2026-10-30).

**Orbital Decay Characteristics:**

| Parameter             | Value                        |
|-----------------------|------------------------------|
| Drag Area             | ~0.07 m² (C_D = 2.2)         |
| Ballistic Coefficient | 77.9 kg/m² (`subsystems/prop.yaml`) |
| Natural Decay         | ~5 years (mean solar activity), ~14 years (solar minimum) from 513 km (`subsystems/prop.yaml`) |
| Disposal              | Perigee-lowering burn to 390 km, 34.3 m/s in six retrograde burns (NOM-014); re-entry in ~1.5 years (mean) and ~4.2 years (solar minimum), inside the 5-year rule |

Natural decay alone does not meet the 5-year disposal rule at solar minimum. The figures come
from integrating the drag decay with the CIRA-72 exponential atmosphere (mean activity) and
0.35 times it (solar minimum), the method and scaling of the original propulsion sizing; the
earlier "1.7–4.8 years" was computed at the retired 450 km altitude. The disposal burn is part
of the delta-V budget (64.1 m/s required against 66.9 m/s), so at least 38 m/s must stay in
reserve for it.

**Operational Implications:**

1. **Limited Orbit Correction Capability:** A single thruster supports drag make-up and the
   disposal burn within the delta-V budget (`subsystems/prop.yaml`). Plane changes are out of scope.
2. **Altitude Monitoring:** Continuous GPS-based altitude tracking is essential for:
   - Planning the end-of-life disposal burn and predicting re-entry
   - Accurate ground track prediction (critical for imaging target planning)
   - Early warning of anomalous decay (potential sign of atmosphere disturbance event)
3. **Mission Planning:** All payload scheduling, imaging window availability, and contact
   window geometry assume the natural, gradually-decaying orbit. The planner uses current
   orbit state to predict future pass availability.

**Telemetry for Orbit Monitoring:**
- `sc_alt` (0x0212): Orbital altitude from GPS (km)
- `sc_lat` (0x0210): Sub-satellite latitude (deg)
- `sc_lon` (0x0211): Sub-satellite longitude (deg)

## 7. Imaging Target Planning for Ocean Currents {#7-imaging-target-planning-for-ocean-currents}

### 7.1 Target Ocean Regions {#71-target-ocean-regions}

EOSAT-1 imaging is planned around ocean current monitoring regions:

| Region                      | Latitude Range   | Target Feature                   |
|-----------------------------|------------------|----------------------------------|
| Gulf Stream (western boundary)| 25–45 N         | Current meander, eddies          |
| Kuroshio Current            | 25–40 N          | Western Pacific boundary current |
| Antarctic Circumpolar Current| 45–65 S         | Frontal zones, upwelling         |
| Benguela Current            | 15–35 S          | Eastern boundary upwelling       |
| North Atlantic Drift        | 45–60 N          | Subpolar gyre circulation        |

### 7.2 Imaging Opportunity Computation {#72-imaging-opportunity-computation}

Imaging opportunities are computed by the mission planner based on:

1. **Orbital geometry**: Sub-satellite point within target region.
2. **Solar illumination**: Target must be sunlit (solar elevation > 10 deg at target).
3. **Spacecraft constraints**: Battery SoC > 40%, AOCS in NOMINAL (4), att_error < 0.5 deg.
4. **Data budget**: Sufficient mass memory and downlink capacity for the image data volume.
5. **Contact timing**: Downlink pass available within a reasonable time after acquisition.

## 8. Pass-Based Scheduling {#8-pass-based-scheduling}

The mission planner uses a pass-based scheduling approach where activities are allocated
to individual orbital passes:

### 8.1 Pass Types {#81-pass-types}

| Pass Type     | Activities                                              |
|---------------|---------------------------------------------------------|
| Imaging Pass  | Payload activation, image acquisition, return to standby|
| Downlink Pass | Science data dump, stored TM playback (any of the five stations)|
| Combined Pass | Imaging followed by downlink (if contact window allows) |
| Idle Pass     | Housekeeping only, battery charging                     |

### 8.2 Scheduling Constraints {#82-scheduling-constraints}

The scheduler must satisfy the following constraints:

| Constraint          | Rule                                                   |
|---------------------|--------------------------------------------------------|
| Power budget        | SoC must remain > 25% at all times (predict per orbit) |
| Data volume         | Mass memory must not exceed 90% capacity               |
| Thermal             | Payload duty cycle limited to 10 min per imaging window|
| Contact conflicts   | No imaging during active downlink pass                 |
| Minimum gap         | At least 5 min between end of imaging and start of downlink |

### 8.3 Power and Data Budget Tracking {#83-power-and-data-budget-tracking}

The planner tracks two budgets across the planning horizon:

- **Power budget**: Predicted battery SoC trajectory based on solar generation model,
  eclipse timing, and planned load profile. The planner will not schedule imaging if
  the predicted SoC drops below 40% at any point.
- **Data budget**: Accumulated data volume from imaging vs. downlink capacity.
  Scene-dependent compression ratios are estimated based on the target type (ocean,
  coastal, land). Downlink capacity is computed from contact duration and data rate mode.

## 9. Relevant Telemetry {#9-relevant-telemetry}

| Param ID | Name              | Unit | Description                          |
|----------|-------------------|------|--------------------------------------|
| 0x0210   | sc_lat            | deg  | Sub-satellite latitude (GPS)         |
| 0x0211   | sc_lon            | deg  | Sub-satellite longitude (GPS)        |
| 0x0212   | sc_alt            | km   | Orbital altitude (GPS)               |
| 0x0509   | range_km          | km   | Slant range to ground station        |
| 0x050A   | contact_elevation | deg  | Ground station elevation angle       |
| 0x0108   | eclipse_flag      | bool | Eclipse state                        |

---

*End of Document — EOSAT1-UM-ORB-008*
