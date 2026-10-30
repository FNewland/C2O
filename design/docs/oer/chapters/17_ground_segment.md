# Chapter 17 — Ground Segment Architecture

> **Recommended background.** ECSS-E-ST-70C (Ground systems and operations); CCSDS 131.0-B (TM synchronisation and channel coding), CCSDS 231.0-B (TC synchronisation and channel coding) and CCSDS 133.0-B (Space Packet Protocol); NASA DSN Telecommunications Link Design Handbook (810-005) for the large-aperture end of the scale. This chapter builds on the link budget and ground-station types of Chapter 11 (§11.7–§11.9), the pass geometry of Chapter 7 §7.4.1 and the ground-segment functions F-G01…F-G04 allocated in Chapter 6 §6.2.4; the lifecycle phases it operates within are those of Chapter 1 Figure 1.4.

## Learning objectives

By the end of this chapter, you will be able to:

1. Describe the components of a ground-segment architecture (ground-station network, mission control system, flight dynamics, mission planning, data processing)
2. Calculate ground-station contact time and data volume per pass for a given orbit and elevation mask
3. Explain the CCSDS protocol stack for space communication and choose a forward-error-correction scheme
4. Design a ground-station network for a given orbit and daily data-downlink requirement
5. Construct a mission operations timeline from launch to end of life, with staffing by phase

Vendor products and software named in this chapter are representative examples, not endorsements; prices are indicative (2026).

---

## 17.1 Ground segment architecture

The ground segment is everything on the ground that supports the space mission. It is frequently underestimated in early mission design, yet it accounts for 5–15 % of total mission cost (Chapter 16 §16.2.1 allocates 5 % to the ground segment and a further 5 % to operations) and is critical to mission success: a spacecraft that cannot be commanded or whose data cannot be received has no mission.

*[Source: ECSS-E-ST-70C (Ground Systems and Operations)]*
*[URL: https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/]*

### 17.1.1 Ground-segment components

Figure 17.1 shows the five functional blocks and the data network that joins them; the RF link to the space segment enters at the ground-station network, and mission products leave from the data-processing block to the user segment. Five functional blocks appear in every ground segment, however small; in a university CubeSat project they may all run on one computer in one room, but they are still five distinct functions with distinct interfaces.

![Ground-segment block diagram](../assets/figures/fig_ground_segment.png)

**Figure 17.1** — Ground-segment block diagram. The ground-station network, mission control system, flight dynamics system, mission planning system and data processing and archive are joined by a data network; the RF interface to the space segment enters at the ground-station network and mission products leave the data-processing block for the user segment.

### 17.1.2 Ground-station components

| Component | Function | Typical specification |
|-----------|----------|---------------------|
| **Antenna** | Transmit uplink commands, receive downlink telemetry | 3–13 m dish (S/X-band); Yagi/turnstile (UHF) |
| **RF front-end** | Low-noise amplifier (LNA), power amplifier, filters | LNA noise figure < 1 dB; PA 50–500 W |
| **Modem/baseband** | Modulation/demodulation, coding/decoding | CCSDS-compliant; BPSK/QPSK/8PSK |
| **Tracking system** | Antenna pointing, Doppler tracking, ranging | Autotrack or programme-track |
| **Data capture** | Record raw baseband data for post-processing | High-speed disk array |
| **Timing** | GPS-disciplined oscillator for time synchronisation | < 1 µs accuracy |

The ground-station types available to a CubeSat mission — volunteer networks, university dishes, commercial networks and (for deep space) the DSN — with their $G/T$ and indicative prices are tabulated in Chapter 11 §11.7.1 and are not repeated here.

### 17.1.3 Mission control system (MCS)

| Function | Description | Tools (representative) |
|----------|------------|-------|
| **Telemetry processing** | Decode, decommutate, display and archive TM packets | COSMOS, YAMCS, EGOS (ESA) |
| **Telecommand generation** | Create, validate, encode and uplink TC packets | Same MCS tools |
| **Pass scheduling** | Schedule antenna time, plan contact windows | STK, GMAT, custom schedulers |
| **Monitoring and control** | Real-time health monitoring, limit checking, alarming | MCS dashboards |
| **Anomaly management** | Detect, diagnose and resolve anomalies | Procedures + expert judgement (Chapter 18 §18.5) |

### 17.1.4 Flight dynamics system (FDS)

| Function | Description | Inputs |
|----------|------------|--------|
| **Orbit determination** | Compute the current orbit from tracking data | Range, Doppler, GPS (if on board) |
| **Orbit prediction** | Propagate the orbit forward for pass planning | Current state vector, perturbation models (Chapter 7) |
| **Manoeuvre planning** | Compute ΔV for orbit maintenance | Target orbit, propulsion model (Chapter 12 §12.2) |
| **Conjunction assessment** | Predict close approaches with debris or other objects | TLE catalogue, own orbit |
| **End-of-life planning** | Compute the de-orbit manoeuvre or passivation plan | Remaining propellant, target orbit (Chapter 3 §3.6) |

For a CubeSat without propulsion the FDS collapses to orbit determination and prediction — typically from the published two-line elements, refined with on-board GPS if available — but conjunction assessment remains: a CubeSat that cannot manoeuvre still needs to know when it is at risk, if only to tell the other operator.

---

## 17.2 Ground-station contact analysis

Understanding how much data can be transferred per pass is fundamental to mission design. The data budget depends on the contact geometry, the data rate and the pass duration.

### 17.2.1 Contact geometry

For a circular LEO orbit, the visibility of a ground station is determined by the minimum elevation angle $\varepsilon_{\min}$ at which the link is usable (typically 5–10°). The slant range at that elevation, which sets the worst-case free-space path loss in the link budget (Chapter 11 §11.4.1), is

$$\rho = R_E \left[\sqrt{\left(\frac{R_E + h}{R_E}\right)^2 - \cos^2\varepsilon_{\min}} - \sin\varepsilon_{\min}\right]$$

with $R_E = 6378.137$ km and $h$ the orbital altitude.

> **Worked example — maximum slant range.** For $h = 500$ km and $\varepsilon_{\min} = 5°$:
>
> $(R_E + h)/R_E = 6878.137/6378.137 = 1.0784$, squared $= 1.1629$; $\cos^2 5° = 0.9924$; difference $= 0.1705$, square root $= 0.4129$; minus $\sin 5° = 0.0872$ gives $0.3258$;
>
> $\rho = 6378.137 \times 0.3258 \approx 2\,080$ km.
>
> At a 10° mask the same orbit gives 1 695 km — the value used in the EOSat-3U link budget of Chapter 11 §11.8.1.

The pass duration follows from the Earth-central angle subtended by the visibility circle. Chapter 7 §7.4.1 gives

$$\lambda_{\max} = \arccos\!\left(\frac{R_E}{R_E + h}\cos\varepsilon_{\min}\right) - \varepsilon_{\min}, \qquad t_{\text{contact,max}} \approx \frac{T}{\pi}\,\lambda_{\max}$$

where $T$ is the orbital period and $\lambda_{\max}$ is in radians. This is the duration of an *overhead* pass; a pass whose peak elevation is lower is shorter.

> **Worked example — maximum pass duration.** For the 500 km orbit ($T = 94.6$ min, Chapter 7 §7.7):
>
> at $\varepsilon_{\min} = 10°$: $\lambda_{\max} = \arccos(0.9273 \times 0.9848) - 10° = 24.0° - 10° = 14.0° = 0.245$ rad, so $t_{\max} \approx (94.6/\pi) \times 0.245 \approx 7.4$ min;
>
> at $\varepsilon_{\min} = 5°$: $\lambda_{\max} = 22.5° - 5° = 17.5° = 0.306$ rad, so $t_{\max} \approx 9.2$ min.
>
> *Typical average usable pass duration (not all passes are overhead, and the first and last 30–60 s are spent acquiring the link): ≈ 6 min.*

Figure 17.2 shows the elevation-versus-time profile of a single pass. Three instants matter operationally: **AOS** (acquisition of signal, when the spacecraft rises above the mask), **TCA** (time of closest approach, maximum elevation and minimum slant range) and **LOS** (loss of signal). The high-rate portion of the pass, where the link margin is largest, is the central window above about 30° elevation; a pass whose peak elevation never reaches 30° may be usable only for housekeeping telemetry. The corresponding ground track — which passes over which stations — is shown in Chapter 7 Figure 7.3.

![Pass elevation profile for an S-band contact](../assets/figures/fig_pass_geometry.png)

**Figure 17.2** — Elevation-versus-time profile of a single S-band pass over a high-latitude station (Iqaluit, 63.7° N) for a 450 km sun-synchronous orbit, illustrative: AOS and LOS at the 5° mask, TCA at peak elevation, and the ≥ 30° window in which the high-rate downlink is scheduled.

### 17.2.2 Data volume per pass

$$V_{\text{pass}} = R \; t_{\text{contact}} \; \eta_{\text{protocol}}$$

where $R$ is the downlink data rate (bit/s), $t_{\text{contact}}$ the usable contact duration (s) and $\eta_{\text{protocol}}$ the protocol efficiency (typically 0.85–0.95 for CCSDS framing; Chapter 11 §11.9 uses 0.80–0.90 to include link set-up and retransmission).

> **Example:** $R = 2$ Mbit/s, $t = 360$ s (6 min average), $\eta = 0.9$:
> $V_{\text{pass}} = 2 \times 10^6 \times 360 \times 0.9 = 648$ Mbit $= 81$ MB per pass.

Summed over the usable passes in a day this is the daily downlink capacity $C_{\text{downlink}} = R\,N_{\text{passes}}\,t_{\text{contact}}\,\eta_{\text{protocol}}$ of Chapter 11 §11.9.

### 17.2.3 Contact frequency

| Orbit | Station latitude | Passes per day | Average usable duration | Daily volume at 2 Mbit/s |
|-------|-------------|----------------|-------------|---------------------------|
| 500 km SSO | 52° N (e.g. southern Ontario) | 3–5 | 6 min | 243–405 MB |
| 500 km SSO | 69° N (e.g. Kiruna) | 6–8 | 7 min | 567–756 MB |
| 500 km, 51.6° (ISS orbit) | 52° N | 2–4 | 5 min | 135–270 MB |
| 500 km SSO | Volunteer network (global, UHF) | 10–15 | 5 min | 3.2–4.9 MB (at 9.6 kbit/s UHF) |

*[Source: orbit-propagation simulations; validated against volunteer-network observation logs. Volumes recomputed from §17.2.2 with η = 0.9.]*

The pattern is the one Chapter 11 §11.7.2 describes: a polar or sun-synchronous satellite is seen by a high-latitude station on almost every orbit, by a mid-latitude station only on the three to five orbits per day whose ground track passes within the visibility circle.

### 17.2.4 Worked example: data-budget closure

*Problem:* An Earth-observation mission generates 500 MB/day of imagery. Is a single ground station at 52° N sufficient with a 2 Mbit/s S-band downlink?

*Calculation:*
- Passes per day: ≈ 4 (500 km SSO from 52° N)
- Average usable pass: 6 min = 360 s
- Data per pass: $2 \times 10^6 \times 360 \times 0.9 / 8 = 81$ MB
- Daily capacity: $4 \times 81 = 324$ MB
- Required: 500 MB/day
- **Shortfall: 176 MB/day — the budget does not close.**

*Solutions:*
1. Add a second ground station at high latitude (e.g. Kiruna → +6 passes → +567 MB)
2. Increase the data rate (X-band at 10 Mbit/s → 405 MB/pass → easily sufficient; see Chapter 11 Problem 4 for the link-budget side)
3. Reduce data generation (lower duty cycle or lower image resolution)
4. Add on-board data compression (2:1 lossless → 250 MB/day required)
5. Use a volunteer UHF network for additional passes (housekeeping only — the rate is too low for imagery)

Each option moves a different budget: (1) moves cost, (2) moves power and the regulatory filing, (3) moves the mission requirement, (4) moves on-board processing and risk. The EOSat-3U data budget of Chapter 11 §11.9 closes at 5 Mbit/s with 5 passes/day (956 MB/day capacity against 720 MB/day generated) — option 2 applied within S-band.

---

## 17.3 CCSDS protocol stack

The Consultative Committee for Space Data Systems (CCSDS) defines the standard protocols for space communication, analogous to TCP/IP for ground networks. Using them is not mandatory for a CubeSat, but it is what makes a commercial or agency ground station able to talk to the spacecraft without custom software.

*[Source: CCSDS 131.0-B-4 (TM Synchronization and Channel Coding); CCSDS 231.0-B-4 (TC Synchronization and Channel Coding); CCSDS 133.0-B-2 (Space Packet Protocol)]*
*[URL: https://public.ccsds.org/Pubs/131x0b4.pdf (freely available)]*

### 17.3.1 Protocol layers

| Layer | CCSDS standard | Function | Ground analogy |
|-------|---------------|----------|----------------|
| **Application** | CCSDS 133.0 (Space Packet) | Mission data and housekeeping packets | HTTP/application data |
| **Network** | CCSDS 732.0 (AOS) or 132.0 (TM) | Virtual channels, multiplexing | IP routing |
| **Data link** | CCSDS 131.0 (TM coding) / 231.0 (TC coding) | FEC, frame synchronisation, CRC | Ethernet |
| **Physical** | CCSDS 401.0 (RF and modulation) | Modulation, frequency, power | Physical layer |

### 17.3.2 Telemetry (TM) frame structure

```
+--------+------------------+----+
| Header | Data field       | EC |
| 6 bytes| 1–1019 bytes     | 2 B|
+--------+------------------+----+
  |
  +-- Spacecraft ID (10 bits)
  +-- Virtual channel ID (3 bits)
  +-- Frame counter (8 bits)
  +-- Frame length
```

The frame counter is what lets the ground detect a missing frame and request retransmission; the virtual-channel ID is what lets housekeeping and payload data share one RF link while being routed to different consumers on the ground.

### 17.3.3 Forward error correction (FEC) options

| Code | Rate | Coding gain (dB) | Use case |
|------|------|------------------|----------|
| Convolutional (7, 1/2) | 1/2 | 5.5 | Legacy CubeSats |
| Reed–Solomon (255, 223) | 0.87 | 3.5 | Combined with convolutional |
| Turbo (rate 1/2) | 1/2 | 7.5 | High-performance CubeSats |
| LDPC (rate 7/8) | 7/8 | 6.0 | High data rate, bandwidth-efficient |

*Modern CubeSats typically use LDPC coding for the downlink (high data rate) and convolutional + Reed–Solomon for the uplink (robustness priority).* The coding gain enters the link budget as a reduction in the required $E_b/N_0$ (Chapter 11 §11.6); the code rate reduces the useful information rate for a given channel rate, which is why the data-budget calculations of §17.2 use the *information* rate $R$.

---

## 17.4 Operations timeline construction

The operations timeline defines all major activities from launch to end of life. It is part of the ConOps (Chapter 4 §4.8 for the concept; Chapter 18 for the operational detail) and drives ground-segment design: the number of stations, the staffing and the automation level all follow from it.

### 17.4.1 Mission phases from the operations perspective

| Phase | Duration | Key activities | Staffing |
|-------|----------|---------------|---------|
| **LEOP** | 0–72 hours | Separation, beacon acquisition, antenna/array deployment, initial health check | 24/7 (3 shifts) |
| **Commissioning** | 1–4 weeks | Subsystem checkout, AOCS calibration, payload first light | 16/7 (2 shifts) |
| **Early operations** | 1–3 months | Performance characterisation, procedure refinement | 8/5 (1 shift) |
| **Nominal operations** | Mission lifetime | Routine science or service, orbit maintenance | 8/5 or automated |
| **Extended operations** | If approved | Degraded-mode operations, reduced data | Part-time |
| **End of life** | 1–4 weeks | Passivation, de-orbit manoeuvre, final telemetry | 8/5 |

### 17.4.2 Operations timeline (Gantt style)

Figure 17.3 lays the phases of §17.4.1 out against the calendar, with the staffing level beneath them.

![Operations timeline for the first year](../assets/figures/fig_ops_timeline.png)

**Figure 17.3** — Gantt-style operations timeline for the first year of a CubeSat mission: LEOP occupies the first 72 hours, commissioning runs to week 4, early operations to month 3 and nominal operations thereafter. The staffing profile beneath falls from 24/7 (three shifts) during LEOP to 16/7 (two shifts) during commissioning and to 8/5 — a single shift, or automated passes — from early operations onward.

Staffing cost falls steeply after commissioning (Figure 17.3). The operations line of the WBS (Chapter 16 §16.2.1, 5 %) assumes this profile; a mission that stays at 16/7 because its procedures were never automated will exceed it within months.

### 17.4.3 LEOP timeline detail

| Time (after separation) | Activity | Success criterion |
|------------------------|----------|-------------------|
| T+0 s | Separation from deployer | Deployment switches released |
| T+0 to T+30 min | Deployment-timer countdown (no RF) | Timer runs; all inhibits clear |
| T+30 min | Antenna deployment | Beacon detected by ground station |
| T+30 to T+60 min | Beacon acquisition | Carrier lock; beacon decoded |
| T+1 h | First telemetry downlink | Housekeeping data received and validated |
| T+1 to T+6 h | Initial health assessment | All subsystems reporting nominal housekeeping |
| T+6 to T+12 h | Solar-array deployment (if separate) | Power generation confirmed |
| T+12 to T+24 h | AOCS initialisation | Attitude determination active |
| T+24 to T+48 h | AOCS calibration (magnetometer, sun sensor) | Pointing within coarse specification |
| T+48 to T+72 h | Communication-chain validation (full duplex) | Uplink and downlink at operational rate |

The 30-minute RF silence after deployment is a launch-provider requirement (Chapter 3 §3.5.2), not a design choice; the first pass may therefore occur before the spacecraft is allowed to transmit, and the LEOP plan must say what the team does with a silent first pass. Chapter 19 rehearses exactly this.

---

## 17.5 Sizing the ground segment

Three questions size a CubeSat ground segment, in this order:

1. **Does the data budget close with one station?** (§17.2.4; Chapter 11 §11.9.) If not, the choice is between a second station, a higher rate and less data — and the second station is usually bought, not built: a commercial network sells passes by the minute (Chapter 11 §11.7.1), which converts a capital cost into an operating cost that scales with the mission.
2. **What is the minimum staffing that keeps the spacecraft safe?** A spacecraft whose FDIR (Chapter 18 §18.3) can hold safe mode indefinitely needs ground attention only at the next working day; one that cannot needs a 24/7 on-call rota from LEOP onwards, which costs more than any antenna.
3. **Who else must be able to talk to it?** A spacecraft using CCSDS framing (§17.3) can be supported by any compliant station in an emergency; a spacecraft with a proprietary protocol depends on its own station working.

A representative ground-segment budget for a 3U mission — one dedicated S-band station (≈ 50–200 kEUR to build, Chapter 11 §11.7.1), a volunteer UHF network for housekeeping, open-source MCS software and 0.5 FTE of operations — is the "Ground 8 kEUR + Operations 40 kEUR" pair in the bottom-up column of Chapter 16 §16.1.6, which assumes the station already exists.

---

## 17.6 Returning to UniSat-1: a minimum ground segment

UniSat-1's ground segment is a single UHF Yagi station at the university plus the volunteer network (Chapter 13 §13.6 costs it at 5 kEUR). Chapter 11 §11.8.2 showed what that buys: at 400 km with a 10° mask the usable contact is about 5 min per pass (6.2 min maximum, Chapter 7 §7.4.1), giving 153 kB per pass and **0.61 MB/day against 1.13 MB/day generated** — the data budget does not close with one station.

Working through §17.5 for UniSat-1:

1. *Second station or higher rate?* The UHF link is power-limited and already uses FEC (Chapter 11 §11.8.2), so the rate cannot rise much; the volunteer network adds passes at zero cost but with no guarantee of availability. The realistic fix is on the generation side — an on-board averaging mode, or a lower magnetometer sampling rate outside the regions of scientific interest — which is a requirements change (Chapter 5 §5.6.2), not a ground-segment one. This is risk R-02 in the UniSat-1 register of Chapter 15 §15.5, and its mitigation is exactly that pair: register with the volunteer network, and halve the data rate on board.
2. *Minimum staffing?* UniSat-1 has passive attitude control and a beacon-only safe mode that is power-positive (Chapter 9 §9.5), so it can wait days for attention: student operators at 0.2 FTE suffice.
3. *Who else can talk to it?* The AX.25-style framing common on volunteer networks is not CCSDS, so no agency station can help in an emergency; the mission accepts this, and the acceptance should be recorded in the register as a risk in its own right.

The LEOP timeline of §17.4.3 collapses for UniSat-1 to the first five rows: there is no array to deploy and no AOCS to calibrate, so commissioning is complete once the magnetometer returns plausible field values on the second day.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Ground segment | Ground-station network + MCS + FDS + mission planning + data processing (§17.1.1) |
| Contact analysis | Slant range at the elevation mask sets the worst-case FSPL; $t_{\max} \approx (T/\pi)\lambda_{\max}$ ≈ 7.4 min at 500 km / 10°; usable average ≈ 6 min |
| Data volume | $V_{\text{pass}} = R\,t_{\text{contact}}\,\eta_{\text{protocol}}$; 2 Mbit/s × 6 min × 0.9 ≈ 81 MB per pass |
| Data budget | Must close: daily generation ≤ daily downlink capacity; add a station, raise the rate, compress or generate less |
| CCSDS | Standard stack: Space Packet, AOS/TM frames, FEC coding, RF modulation; coding gain reduces required $E_b/N_0$ |
| Operations timeline | LEOP (24/7) → commissioning (16/7) → nominal (8/5 or automated); staffing drives operations cost |
| LEOP | First 72 hours are critical: antenna deployment, beacon acquisition, health check, AOCS calibration |
| UniSat-1 | One UHF station does not close the data budget; the fix is on the generation side |

---

## Problems

1. **Slant range and pass duration.** For a 550 km circular orbit, compute the slant range at 5°, 10° and 20° elevation and the maximum pass duration at each mask (use $R_E = 6378.137$ km and $\mu = 398\,600.44$ km³/s²). Comment on the trade between a low mask (longer passes) and the FSPL penalty it carries into the link budget of Chapter 11.

2. **Data volume per pass.** A 3U Earth-observation CubeSat downlinks at 5 Mbit/s with LDPC rate 7/8 coding and a CCSDS protocol efficiency of 0.85. For an average usable pass of 6 min, compute the useful data per pass. How many passes per day are needed to clear 1.2 GB/day of imagery, and from which station latitude in §17.2.3 is that achievable with one station?

3. **Ground-station network design.** A 500 km SSO mission must downlink 2 GB/day. Design a station network — locations, antenna sizes, data rates — using the station types of Chapter 11 §11.7.1 and the pass counts of §17.2.3, for (a) minimum capital cost and (b) minimum operating cost over three years. State the annual cost of each and the point at which they cross.

4. **LEOP timeline.** Construct an hourly LEOP timeline for the first 72 hours of a 3U CubeSat deployed from the ISS orbit (51.6°, 400 km) with a single station at 45° N. Mark every pass (you may assume four passes per day of 5 min each, clustered in two groups), state which activity of §17.4.3 is attempted on each, and identify the longest gap during which the spacecraft is unobserved.

5. **Silent first pass.** The first pass after deployment occurs 20 minutes after separation, while the RF inhibit timer is still running. Write the decision tree the operations team follows for the next three passes if (a) a beacon is heard on pass 2, (b) nothing is heard on passes 2 and 3, and (c) a carrier is heard but no frames decode. For each branch, name the ground-segment component or spacecraft subsystem that is suspected first and the test that discriminates it.

6. **Operations timeline and staffing.** Draft a weekly-resolution operations timeline for a 12-month EO mission following §17.4.2, then cost the staffing at 60 kEUR per FTE-year for the 24/7 → 16/7 → 8/5 profile. Recompute if commissioning slips from 4 weeks to 10 weeks. Which single automation investment most reduces the sensitivity to that slip?

7. **FEC selection.** A UHF downlink closes with 2.8 dB of margin uncoded (Chapter 11 §11.8.2) against a 3 dB requirement. Using the coding gains of §17.3.3, choose a code that meets the requirement with the least loss of information rate, and compute the resulting daily data volume for 4 passes of 5 min. Then repeat the choice for an S-band link that is bandwidth-limited rather than power-limited, and explain why the answer differs.

8. **Minimum ground segment.** Specify the minimum ground segment that could support the UniSat-1 mission of §17.6 — hardware, software, staffing and network membership — and estimate its cost. Then list what that minimum segment *cannot* do (ranging, conjunction response, high-rate recovery) and assign each gap a risk score on the 5×5 matrix of Chapter 15.

9. **Safe mode on a weekend.** A 3U spacecraft enters safe mode at 03:00 on a Saturday; the next staffed contact is Monday 09:00. Using the safe-mode power of Chapter 18 Table 18.1 (2 W) and the battery of Chapter 9 §9.3 (20 Wh, at the depth-of-discharge limit used there), determine whether the spacecraft survives 54 hours of eclipses without ground intervention, and what minimum on-call arrangement, if any, the ground segment must provide.

---

## References

1. ECSS, *ECSS-E-ST-70C: Ground Systems and Operations*, 2008. https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/
2. CCSDS, *TM Synchronization and Channel Coding*, CCSDS 131.0-B-4, 2022. https://public.ccsds.org/Pubs/131x0b4.pdf
3. CCSDS, *Space Packet Protocol*, CCSDS 133.0-B-2, 2020. https://public.ccsds.org/Pubs/133x0b2.pdf
4. CCSDS, *TC Synchronization and Channel Coding*, CCSDS 231.0-B-4, 2021. https://public.ccsds.org/Pubs/231x0b4.pdf
5. SatNOGS, *Global Network of Satellite Ground Stations*. https://network.satnogs.org/
6. NASA JPL, *DSN Telecommunications Link Design Handbook*, 810-005. https://deepspace.jpl.nasa.gov/dsndocs/810-005/
7. Space Applications Services, *Yamcs Mission Control Software* (open source). https://yamcs.org/
8. Wertz, J. R., Everett, D. F. & Puschell, J. J. (eds.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, Chapters 28–29 (Ground segment; Mission operations).
