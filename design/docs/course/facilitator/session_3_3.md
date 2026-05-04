# Session 3.3: Power, AOCS, & Thermal Design

**Duration:** 2 hours
**Prerequisites:** Sessions 3.1-3.2 (orbit and payload sized)
**References:** SMAD4 Ch.11 (EPS), Ch.11.1 (AOCS), Ch.11.5 (Thermal); ECSS-E-ST-20C, ECSS-E-ST-31C

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Size a solar array and battery from the power budget
2. Select AOCS hardware based on pointing requirements
3. Construct a pointing error budget (RSS)
4. Perform basic thermal analysis (hot case, cold case)
5. Review power/AOCS/thermal outputs in SpaceCDF

---

## 1. Electrical Power System (30 min)

### Teaching Notes

### EPS Architecture

CubeSat EPS typically consists of:
- **Solar array** (body-mounted or deployable): primary power source
- **Battery** (Li-ion): energy storage for eclipse
- **EPS board** (COTS, e.g., GomSpace P31u): power conditioning, MPPT, distribution
- **Switched lines**: controlled power to each subsystem

### Solar Array Sizing (detailed)

*[Recap from Session 2.4 with additional detail]*

**Step 1:** Determine orbit-average power demand using duty cycle analysis (from Timing Budget):
```
P_avg = ?(P_mode × duty_mode)
```

**Step 2:** Determine SA EOL power requirement:
```
P_SA_EOL = P_peak_sunlight + (P_eclipse × t_eclipse)/(t_sunlight × eta_charge)
```

**Step 3:** Account for degradation:
```
P_SA_BOL = P_SA_EOL / (1 - degradation_rate)^years
```

Typical degradation: 2.5%/year for triple-junction GaAs in LEO.

**Step 4:** Compute SA area:
```
A_SA = P_SA_BOL / (eta_cell × S × cos(theta) × eta_packing)
```

Where:
- eta_cell = cell efficiency (29.5% for triple-junction GaAs)
- S = solar flux (1361 W/m^2 at 1 AU)
- theta = sun incidence angle (0° for ideal pointing)
- eta_packing = packing factor (0.85 typical)

*Example: P_SA_BOL = 13.2 W, eta=0.295, S=1361, theta=0°, eta_p=0.85*
*A_SA = 13.2 / (0.295 × 1361 × 1.0 × 0.85) = 13.2 / 341.2 = **0.039 m^2** (e.g., 20×20 cm panel)*

**Step 5:** Compute SA mass:
```
m_SA = A_SA × sigma_SA
```
Where sigma_SA = specific mass (body-mounted: 2.5 kg/m^2; deployable: 1.5 kg/m^2).

### CubeSat SA Power Reference

| Configuration | 1U | 3U | 6U |
|--------------|----|----|-----|
| Body-mounted only | 2 W | 7 W | 12 W |
| Single deployable | 4 W | 15 W | 30 W |
| Dual deployable | -- | 25 W | 48 W |

*[Source: GomSpace, ISIS, MMA Design vendor data; ASTERIA 6U = 48 W BOL confirmed]*

### Battery Sizing

```
C_bat = (P_eclipse × t_eclipse/60) / (DoD × eta_discharge)
```

| Parameter | Typical CubeSat Value |
|-----------|----------------------|
| DoD | 30% (for >10,000 cycle life) |
| eta_discharge | 0.95 |
| Specific energy | 150-200 Wh/kg (Li-ion 18650) |

---

## 2. Attitude and Orbit Control System (30 min)

### Teaching Notes

*[Source: SMAD4 §11.1; ECSS-E-ST-60-10C]*

### AOCS Selection by Pointing Requirement

| Pointing Req | Architecture | Typical CubeSat Hardware | Mass |
|-------------|-------------|-------------------------|------|
| > 5° | Passive magnetic | Permanent magnet + hysteresis rods | ~0.05 kg |
| 2-5° | Magnetorquers only | 3-axis magnetorquers + sun sensors | ~0.1 kg |
| 0.1-2° | Reaction wheels + magnetorquers | 3-4 RW + 3 MTQ + sun sensors | ~0.5 kg |
| < 0.1° | Fine pointing (RW + star tracker) | 4 RW + ST + MTQ + sun sensors | ~0.8 kg |
| < 0.01° | Very fine (+ gyros) | 4 RW + ST + gyro + MTQ | ~1.2 kg |

### Pointing Error Budget

*[Recap from PointingBudget component; RSS combination]*

```
theta_total = ?(theta_sensor^2 + theta_actuator^2 + theta_alignment^2 + theta_thermal^2 + theta_jitter^2 + theta_orbit^2 + theta_timing^2)
```

| Source | Star Tracker (arcsec) | Sun Sensor (deg) |
|--------|----------------------|------------------|
| Sensor accuracy | 3-10" (0.001-0.003°) | 0.5-2° |
| Actuator resolution | 2-5" (0.001°) | N/A (MTQ: 1-5°) |
| Alignment knowledge | 30-60" (0.01-0.02°) | 0.5° |
| Thermal distortion | 10-30" (0.003-0.01°) | 0.1° |
| Jitter (RW) | 5-20" (0.001-0.006°) | N/A |

**Example: Fine pointing (ST + RW):**
theta = ?(0.003^2 + 0.001^2 + 0.02^2 + 0.01^2 + 0.005^2) = ?(0.000554) = **0.024°**

This meets a 0.1° requirement with **76% margin** -- comfortable.

### Momentum Management

Disturbance torques cause angular momentum buildup in reaction wheels. Magnetorquers "dump" this momentum using Earth's magnetic field.

**Key sizing parameter:** momentum storage capacity of wheels must exceed worst-case accumulation over a desaturation interval:

```
H_required = T_disturbance × t_accumulation / 2
```

For LEO CubeSats, typical disturbance torques are 10?? to 10?? Nm. A single desaturation per orbit keeps wheels within capacity.

---

## 3. Thermal Control (20 min)

### Teaching Notes

*[Source: ECSS-E-ST-31C; SMAD4 §11.5]*

### Thermal Environment

In LEO, the spacecraft experiences:
- **Direct solar flux:** 1361 W/m^2 (sun-facing surfaces)
- **Earth albedo:** ~400 W/m^2 (Earth-reflected sunlight)
- **Earth IR:** ~240 W/m^2 (thermal emission from Earth)
- **Deep space:** ~3 K (cold sink for radiators)

### Hot Case / Cold Case

| Case | Conditions | Design Concern |
|------|-----------|----------------|
| **Hot** | Maximum solar exposure, all subsystems active, worst sun angle | Components exceed max operating temp |
| **Cold** | Eclipse, minimum power dissipation, deep space exposure | Components fall below min operating temp |

### Thermal Control Methods

| Method | Type | Mass Impact | Use When |
|--------|------|-------------|----------|
| **Surface coatings** | Passive | Negligible | Always (paint, anodise, tape) |
| **MLI blankets** | Passive | 0.05-0.2 kg | Insulate from external environment |
| **Radiators** | Passive | Included in structure | Reject internal heat to space |
| **Heaters** | Active | 0.005-0.02 kg each | Maintain min temp during eclipse |
| **Heat pipes** | Active | 0.05-0.1 kg | High heat transport requirements |

### Thermal Balance Equation

```
Q_absorbed + Q_internal = Q_radiated
```

Where:
- Q_absorbed = ? × A_sun × S + ? × A_albedo × S × ? + ? × A_earth × sigmaT_earth?
- Q_internal = P_dissipated (waste heat from electronics)
- Q_radiated = ? × A_rad × sigma × T?

sigma = 5.67 × 10?? W/m^2/K? (Stefan-Boltzmann constant)

### ECSS Thermal Margins

*[Source: ECSS-E-ST-31C -- verified in Session 2.4]*

| Level | Hot Margin | Cold Margin |
|-------|-----------|-------------|
| Qualification | ±15°C | ±15°C |
| Acceptance | ±10°C | ±10°C |
| Operating | ±5°C | ±5°C |

**Example:** If component max operating temp is 50°C and predicted hot case is 42°C:
- Operating margin: 50 - 42 = 8°C > 5°C Y
- But for qualification testing: need to test at 42 + 15 = 57°C (exceeds 50°C operating limit -> need to check qualification limit)

---

## 4. SpaceCDF Exercise (40 min)

### Instructions

1. **Run the design** if not already converged
2. **Dashboard** -- review power, AOCS, thermal KPIs and budgets:
   - Power margin: is it positive in all modes?
   - AOCS: what pointing accuracy was computed?
   - Thermal: any temperature exceedances?
3. **Pointing Budget** card -- review the RSS error tree:
   - What's the largest contributor?
   - Is there margin to the requirement?
4. **Timing Budget** card -- review mode durations:
   - Does the duty cycle match your ConOps modes?
5. **Parametric** tab -- review the power duty cycle data:
   - Do the per-mode power values match your expectations?
   - What happens if you change the payload duty cycle?

### Worksheet 3.3 Tasks
1. Size the solar array for your mission (show calculation)
2. Size the battery (show calculation)
3. Select AOCS hardware class based on your pointing requirement
4. Complete the pointing error budget table
5. Identify hot case and cold case for your orbit

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| EPS | SA sized from peak sunlight + recharge; battery from eclipse energy / DoD |
| SA power | Body-mounted: 2-12W; single deploy: 4-30W; dual deploy: 25-48W for CubeSats |
| AOCS | Driven by pointing req: MTQ-only for >2°; RW+ST for <0.1° |
| Pointing budget | RSS of 5-7 independent sources; ST+RW gives ~0.02° typical |
| Thermal | Hot case (max exposure) and cold case (eclipse); ECSS margins ±5/10/15°C |
| Coupling | Power mode -> duty cycle -> SA size -> mass -> structure -> thermal |
