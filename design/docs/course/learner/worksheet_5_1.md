# Worksheet 5.1: Ground Segment & Operations Architecture

**Name:** ___________________________  **Date:** ___________  **Team:** ___________

**Mission Name:** ___________________________  **Orbit:** _____ km, _____ deg inclination

---

## Part A: Ground Station Contact Analysis

**Calculate contact time and data volume per pass for your mission.**

### Input Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Orbital altitude (h) | _____ km | SpaceCDF orbit selection |
| Minimum elevation angle (epsilon) | _____ deg | Ground station spec (typically 5-10) |
| Downlink data rate (R) | _____ Mbps | SpaceCDF link budget |
| Protocol efficiency (eta) | _____ (typically 0.85-0.95) | CCSDS overhead estimate |
| Ground station latitude | _____ deg | Selected station |
| Earth radius (R_E) | 6371 km | Constant |

### Calculations

**Maximum slant range:**

rho = R_E x (sqrt((h/R_E + 1)^2 - cos^2(epsilon)) - sin(epsilon))

rho = 6371 x (sqrt((_____/6371 + 1)^2 - cos^2(_____)) - sin(_____))

rho = _____ km

**Average pass duration (approximate):**

T_avg ~ _____ minutes (from STK/SpaceCDF or estimate: ~6 min for 500 km SSO)

**Data volume per pass:**

V_data = R x T x eta = _____ Mbps x _____ s x _____ = _____ Mbit = _____ MB

---

## Part B: Data Budget Closure

| Parameter | Value | Unit |
|-----------|------:|------|
| Daily data generation (payload) | | MB/day |
| Daily data generation (housekeeping) | | MB/day |
| **Total daily generation** | | **MB/day** |
| | | |
| Passes per day (GS 1: _____________) | | passes |
| Data per pass (GS 1) | | MB |
| Subtotal downlink (GS 1) | | MB/day |
| | | |
| Passes per day (GS 2: _____________) | | passes |
| Data per pass (GS 2) | | MB |
| Subtotal downlink (GS 2) | | MB/day |
| | | |
| **Total daily downlink capacity** | | **MB/day** |
| | | |
| **Data budget margin** | | **MB/day** |
| **Margin percentage** | | **%** |

**Does the data budget close?** Y / N

If not, what changes would close it? (check all that apply)

- [ ] Add another ground station at: _______________
- [ ] Increase data rate to: _____ Mbps (requires: _______________)
- [ ] Reduce payload data generation to: _____ MB/day (impact: _______________)
- [ ] Add onboard compression (ratio: _____:1)
- [ ] Use SatNOGS network for additional passes
- [ ] Other: _______________________________________________

---

## Part C: Ground Station Network Design

| Station # | Location | Latitude | Antenna | Band | Data Rate | Passes/Day | Role |
|:-:|---------|:--------:|---------|:----:|:---------:|:----------:|------|
| 1 | | | | | | | Primary TTC |
| 2 | | | | | | | Payload DL |
| 3 | | | | | | | Backup/SatNOGS |

**Total ground segment cost estimate:** _____ kEUR

| Cost Element | Annual Cost (kEUR) | Notes |
|-------------|-------------------:|-------|
| Antenna rental / ownership | | |
| MCS software licence | | |
| Network connectivity | | |
| Operations staff (_____ FTE) | | |
| **Total annual** | | |
| **Mission lifetime (_____ yr)** | | |

---

## Part D: LEOP Timeline

Construct the LEOP timeline for the first 72 hours after separation:

| Time (UTC) | Sim Time | Activity | Success Criterion | Status |
|-----------|----------|---------|-------------------|:------:|
| T+0 | Separation | Deployment switches release | | [ ] |
| T+30 min | Timer expires | Antenna deployment commanded | | [ ] |
| T+_____ | | Beacon acquisition | Carrier lock | [ ] |
| T+_____ | | First HK telemetry | Data decoded | [ ] |
| T+_____ | | First uplink command | ACK received | [ ] |
| T+_____ | | SA deployment (if separate) | Power generation confirmed | [ ] |
| T+_____ | | ADCS initialisation | Attitude determination active | [ ] |
| T+_____ | | ADCS calibration | Pointing < _____ deg | [ ] |
| T+_____ | | Full duplex validation | Uplink + downlink at ops rate | [ ] |
| T+_____ | | Health assessment complete | All subsystems nominal | [ ] |

---

## Part E: Mission Operations Timeline (Gantt Chart)

Sketch the operations timeline from launch to end of life:

```
Phase:       LEOP  Commission  Early Ops    Nominal Operations         EOL
Week:     1  2  3  4  5  6  7  8  9  ... 26 ... 52 ... 104 ... 156
          |  |  |  |  |  |  |  |  |       |      |       |       |
Staffing: ________________________________________________
          24/7     16/7        8/5         8/5 or automated    8/5
          
Key milestones:
  L+___: First light
  L+___: Commissioning complete
  L+___: Orbit maintenance manoeuvre (if applicable)
  L+___: End of nominal mission
  L+___: Extended mission (if applicable)
  L+___: Passivation and deorbit
```

---

## Notes & Reflections

What is the most challenging aspect of your ground segment design? What would you do differently with more budget?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________
