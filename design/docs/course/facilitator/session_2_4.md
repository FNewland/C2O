# Session 2.4: Design Budgets Introduction

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1-2.3
**References:** ECSS-E-HB-10-02A §5.2 (Mass margins), ECSS-E-ST-20C (Power), SMAD4 Ch.10-11

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Construct a mass budget with per-subsystem allocations and margins
2. Apply ECSS margin philosophy by project phase
3. Construct a power budget using duty cycle analysis
4. Understand the role of design margins and how they decrease with maturity
5. Read SpaceCDF's engineering budget displays

---

## 1. Why Budgets Matter (15 min)

### Teaching Notes

Engineering budgets are the quantitative backbone of systems engineering. They answer: **"Will this design work?"**

A budget tracks the balance between **allocation** (what's available) and **demand** (what's needed):

```
Margin = Allocation - Demand (with margins)
```

If margin is negative, the design **does not close**. The team must either:
- Reduce demand (lighter/lower-power components)
- Increase allocation (bigger solar array, larger launcher)
- Accept higher risk (reduce margin policy)

### Types of Engineering Budgets

| Budget | Allocation From | Demand From | Margin Policy |
|--------|----------------|-------------|---------------|
| **Mass** | Launcher capacity | Sum of all subsystem masses | ECSS-E-HB-10-02A |
| **Power** | Solar array EOL output | Sum of all mode demands | ECSS-E-ST-20C |
| **Cost** | Programme budget ceiling | Sum of all cost elements | ECSS-M-ST-60C |
| **ΔV** | Propulsion capacity | Sum of all manoeuvre needs | ECSS-E-ST-35C |
| **Link** | TX power + antenna gain | Path loss + noise + threshold | ECSS-E-ST-50-05C |
| **Pointing** | Sensor + actuator capability | RSS of all error sources | Subsystem-specific |
| **Data** | Downlink capacity per day | Data generation per day | Mission-specific |

---

## 2. Mass Budget (30 min)

### Teaching Notes

*[Source: ECSS-E-HB-10-02A §5.2; SMAD4 Table 10-8]*

### Structure

```
Mass Budget:
  Payload:        1.50 kg  ← from payload specification
  EPS:            0.75 kg  ← SA + battery + EPS board
  AOCS:           0.55 kg  ← RW + MTQ + ST + sun sensors
  TTC:            0.25 kg  ← transponder + antenna
  OBC:            0.08 kg  ← flight computer
  Thermal:        0.05 kg  ← heaters + MLI
  Structure:      0.35 kg  ← frame + fasteners
  Harness:        0.15 kg  ← cables + connectors
  ────────────────────────
  Dry Mass (CBE): 3.68 kg  ← Current Best Estimate
  + System Margin (20%): 0.74 kg
  ────────────────────────
  Dry Mass (MEV): 4.42 kg  ← Maximum Expected Value
  + Propellant:   0.00 kg
  ────────────────────────
  Wet Mass:       4.42 kg
  
  Launcher Allocation: 6.00 kg (3U CubeSat limit)
  Mass Margin:    1.58 kg (26.4%) → GREEN
```

### Key Terms

| Term | Definition |
|------|-----------|
| **CBE** (Current Best Estimate) | Best estimate of actual mass based on current knowledge |
| **MEV** (Maximum Expected Value) | CBE + maturity margin = worst case expected mass |
| **Contingency/Maturity Margin** | Added at equipment level based on design maturity |
| **System Margin** | Added at system level as management reserve |

### Formula: Mass Margin

```
Mass_Margin_% = (Allocation - MEV) / Allocation × 100
```

Green: >20% | Amber: 10-20% | Red: <10% | Exceeded: <0%

### ECSS Margin Policy by Phase

*[Source: ECSS-E-HB-10-02A §5.2 — Verified, see Session 1.3-1.4 verification]*

| Phase | Equipment Margin | System Margin | Compound |
|-------|-----------------|---------------|----------|
| **0/A** | 20% | 20% | ~44% |
| **B1** | 10% | 20% | ~32% |
| **B2** | 5% | 15% | ~21% |
| **C/D** | 3% | 10% | ~13% |
| **E** (as-built) | 0% | 5% | ~5% |

**Key insight:** Margins decrease as design maturity increases. In Phase A, you're 44% uncertain about mass; by Phase D, you've weighed everything and you're only 13% uncertain.

---

## 3. Power Budget (30 min)

### Teaching Notes

*[Source: ECSS-E-ST-20C; SMAD4 §11.4]*

### Mode-Based Power Budget

The power budget is computed **per operational mode** because not all subsystems are active simultaneously:

| Subsystem | Safe (W) | Idle (W) | Imaging (W) | Downlink (W) | Eclipse (W) |
|-----------|---------|---------|-------------|-------------|-------------|
| OBC | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| AOCS | 0.5 | 1.0 | 3.0 | 2.0 | 0.5 |
| Payload | 0 | 0 | 5.0 | 0 | 0 |
| TTC (TX) | 0.5 | 0.5 | 0.5 | 6.0 | 0 |
| Thermal | 0.5 | 0.5 | 0.5 | 0.5 | 2.0 |
| **Total** | **2.5** | **3.0** | **10.0** | **9.5** | **3.5** |

### Orbit-Average Power

Not all modes run for the full orbit. Use duty cycling:

```
P_orbit_avg = Σ (P_mode × duty_cycle_mode)
```

**Example for 95-min orbit (60 min sun, 35 min eclipse):**

| Mode | Power (W) | Duty (%) | Contribution (W) |
|------|----------|----------|-------------------|
| Idle | 3.0 | 45% | 1.35 |
| Imaging | 10.0 | 10% | 1.00 |
| Downlink | 9.5 | 8% | 0.76 |
| Eclipse | 3.5 | 37% | 1.30 |
| **Total orbit-average** | | | **4.41 W** |

### Solar Array Sizing

The SA must provide power for:
1. The highest sunlight mode (peak demand)
2. Battery recharge for eclipse energy

```
P_SA_required = P_peak_sunlight + (P_eclipse × t_eclipse) / (t_sunlight × η_charge)
```

*[Verified: SMAD4 §11.4, ECSS-E-ST-20C — see Session 1.4 verification]*

**Numerical example:**
- P_peak_sunlight = 10 W (imaging mode)
- P_eclipse = 3.5 W, t_eclipse = 35 min, t_sunlight = 60 min, η_charge = 0.9
- P_recharge = (3.5 × 35) / (60 × 0.9) = 2.27 W
- **P_SA_required = 10.0 + 2.27 = 12.3 W** (before degradation margin)
- With 3-year EOL degradation (2.5%/yr): P_SA_BOL = 12.3 / (1-0.025)³ = **13.2 W**

### Battery Sizing

```
Battery_Capacity = (P_eclipse × t_eclipse) / (DoD_max × η_discharge)
```

Where DoD_max ≈ 0.3 (30% depth of discharge for long cycle life)

**Example:**
- Energy per eclipse = 3.5 W × 35/60 h = 2.04 Wh
- Battery = 2.04 / (0.3 × 0.95) = **7.2 Wh** minimum
- With margin: specify ≥ **10 Wh** battery

---

## 4. Other Budget Types (20 min)

### Link Budget (brief — full session in Day 3)

Key equation (decibels):
```
Margin = EIRP - FSPL + G/T - k - 10·log₁₀(R_b) - Eb/N₀_required - Implementation_Loss
```

Where:
- EIRP = TX power (dBW) + TX antenna gain (dBi) - TX losses (dB)
- FSPL = 20·log₁₀(4πd/λ) — Free Space Path Loss
- G/T = RX antenna gain (dBi) - 10·log₁₀(T_sys) — Ground station figure of merit
- k = -228.6 dBW/K/Hz (Boltzmann constant)
- R_b = data rate (bps)

*[Verified: this is the standard link budget equation per ECSS-E-ST-50-05C]*

### Pointing Budget

Root-Sum-Square of independent error sources:

```
θ_total = √(θ_sensor² + θ_actuator² + θ_alignment² + θ_thermal² + θ_jitter²)
```

Must be less than the pointing requirement.

### Data Budget

```
Daily Generation = Data_rate × Duty_cycle × Orbits_per_day × Time_per_pass
Daily Downlink = DL_rate × Contact_time_per_day

Balance: Daily Downlink ≥ Daily Generation
```

---

## 5. SpaceCDF Budget Exercise (25 min)

### Instructions

1. Run the design in SpaceCDF if not already done
2. Review the **Dashboard** — examine each KPI card (mass, power, link, cost margins)
3. Open the **Budget Breakdown** section — examine per-subsystem mass and power
4. Check the **Pointing Budget** — is the RSS total within the requirement?
5. Check the **Data Budget** — does downlink balance with generation?
6. Check the **Timing Budget** — review mode durations in one orbit
7. Open the **Parametric** tab to see the mass/cost/power fractions used by the tool

### Discussion

- Which budget is tightest (closest to zero margin)?
- What design change would improve the tightest budget?
- How does the margin policy affect your design freedom?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Budgets | Allocation - Demand = Margin; negative margin means design doesn't close |
| Mass budget | CBE + equipment margin + system margin = MEV; compare to launcher allocation |
| Power budget | Mode-based; duty cycling determines orbit-average; SA must cover peak + recharge |
| ECSS margins | Decrease with maturity: 44% in Phase 0/A → 13% in Phase C/D |
| Other budgets | Link (dB), pointing (RSS), data (GB/day), ΔV (m/s) |
| SpaceCDF | Dashboard KPIs + Budget Breakdown + Pointing + Data + Timing |
