# Session 3.4: Structure, Propulsion, & Data Handling

**Duration:** 2 hours
**Prerequisites:** Sessions 3.1-3.3
**References:** CDS Rev 14.1; SMAD4 Ch.11.3 (Structure), Ch.11.7 (Propulsion), Ch.11.2 (C&DH)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Verify CubeSat Design Specification compliance for 1U-12U form factors
2. Understand launch load factors and structural margin of safety
3. Evaluate propulsion options (or justify no propulsion)
4. Size onboard data storage from the data budget
5. Select equipment using SpaceCDF's equipment browser

---

## 1. CubeSat Structure & CDS Compliance (30 min)

### Teaching Notes

*[Source: Cal Poly CubeSat Design Specification Rev 14.1 (February 2022)]*

### CDS Dimensional Specifications

| Form Factor | Dimensions (mm) | Max Mass (kg) | Internal Volume (cm³) |
|------------|-----------------|---------------|----------------------|
| 1U | 100 × 100 × 113.5 | 2.0 | ~1000 |
| 1.5U | 100 × 100 × 170.2 | 3.0 | ~1500 |
| 2U | 100 × 100 × 227.0 | 4.0 | ~2000 |
| 3U | 100 × 100 × 340.5 | 6.0 | ~3000 |
| 6U | 100 × 226.3 × 340.5 | 12.0 | ~6000 |
| 12U | 226.3 × 226.3 × 340.5 | 24.0 | ~12000 |

### CDS Key Requirements

| Requirement | Specification |
|------------|---------------|
| Rail material | Hard anodised aluminium (7075 or 6061-T6) |
| Rail width | 8.5 × 8.5 mm minimum |
| Surface finish | All surfaces anodised or non-outgassing coating |
| Deployment switches | Minimum: 1 on each accessible +X/-X rail face |
| RBF pin | Required; physically disables all power |
| Protrusions | None beyond rail envelope in stowed configuration |
| Centre of gravity | Within 2 cm of geometric centre (per deployer ICD) |
| Fundamental frequency | > 40 Hz (typical deployer requirement) |

### PC/104 Bus Standard

Most CubeSat avionics use the PC/104 form factor for inter-board connections:
- **Board size:** 96 × 90 mm
- **Connector:** 104-pin stack-through (2 rows × 52 pins)
- **Pitch:** 2.54 mm
- **Signals:** 3.3V, 5V, 12V, GND + I²C, SPI, UART, CAN, GPIO
- **Stack height:** 1U ~70 mm (4 boards), 3U ~250 mm (12 boards)

### Launch Loads

| Load Type | Typical Level | Verification |
|-----------|--------------|-------------|
| Quasi-static | 6-9g axial, 2-4g lateral | Analysis + sine vibe |
| Random vibration | Per launch vehicle PUG (20-2000 Hz) | Random vibe test |
| Shock | 500-2000g at separation | Shock test (2 reps/axis) |
| Acoustic | Per vehicle spec | Usually covered by random vibe |

### Structural Margin of Safety (MoS)

```
MoS = (Allowable Load / (Design Load × Factor of Safety)) - 1
```

**Requirement:** MoS ≥ 0 (positive margin) for all load cases.

Typical factors of safety:
- Yield: 1.25 (metallic), 1.5 (composite)
- Ultimate: 1.5 (metallic), 2.0 (composite)

---

## 2. Propulsion (25 min)

### Teaching Notes

*[Source: SMAD4 §17; Enpulsion, VACCO, ThrustMe vendor data]*

### When Propulsion is Needed

| Need | ΔV Required | Example |
|------|------------|---------|
| **Orbit maintenance** | 5-15 m/s/year | Drag compensation at low altitude |
| **Deorbit** | 50-150 m/s | Lowering perigee from >600 km |
| **Collision avoidance** | 1-5 m/s/event | Conjunction avoidance manoeuvre |
| **Constellation deployment** | 10-50 m/s | Phasing between orbital planes |

### When NO Propulsion is Needed

- Orbit < 500 km: natural deorbit within 5-15 years (FCC-compliant)
- Low-cost mission: propulsion adds mass, cost, and complexity
- Technology demo: limited lifetime acceptable
- Constellation using differential drag for phasing

### CubeSat Propulsion Options

| Type | Isp (s) | Thrust | Mass | ΔV (5kg SC) | TRL | Example |
|------|---------|--------|------|-------------|-----|---------|
| **Cold gas** | 40-80 | 10-100 mN | 0.3-1.0 kg | 10-30 m/s | 9 | VACCO MiPS |
| **Resistojet** | 80-150 | 10-50 mN | 0.3-0.8 kg | 20-50 m/s | 7-8 | Busek AMAC |
| **Electrospray** | 500-1500 | 0.01-1 mN | 0.5-1.5 kg | 50-200 m/s | 7-8 | Enpulsion NANO |
| **Hall effect** | 800-1500 | 1-10 mN | 1.0-3.0 kg | 100-500 m/s | 6-8 | Exotrail ExoMG |
| **Hydrazine mono** | 200-230 | 0.1-1 N | 1.0-4.0 kg | 50-200 m/s | 9 | Aerojet MPS-130 |
| **Green mono** | 200-250 | 0.1-1 N | 1.0-3.0 kg | 50-200 m/s | 7-8 | Bradford HPGP |

### Propellant Mass (Tsiolkovsky)

```
m_propellant = m_dry × (e^(ΔV/(Isp×g₀)) - 1)
```

Where g₀ = 9.80665 m/s².

*Example: m_dry = 5 kg, ΔV = 50 m/s, Isp = 60 s (cold gas):*
*m_prop = 5 × (e^(50/(60×9.81)) - 1) = 5 × (e^0.085 - 1) = 5 × 0.0887 = **0.44 kg***

---

## 3. On-Board Data Handling (20 min)

### Teaching Notes

### OBC Architecture

CubeSat OBCs typically provide:
- **Processor:** ARM Cortex-M/A or LEON3/4 (rad-tolerant)
- **RAM:** 64 MB - 1 GB
- **Flash storage:** 4-128 GB
- **Interfaces:** I²C, SPI, UART, CAN, RS-422, USB
- **Operating system:** FreeRTOS, Linux, or bare-metal
- **Power:** 0.5-3 W

### Data Storage Sizing

From the data budget:
```
Storage_required = Daily_generation × Days_between_downlinks × Safety_factor
```

**Example:**
- Daily generation = 5 GB
- Days between contacts = 1 (LEO with daily pass)
- Safety factor = 2 (handle missed pass)
- **Storage = 5 × 1 × 2 = 10 GB minimum**

### Flight Software Functions

| Function | Description |
|----------|------------|
| **Mode management** | Safe, nominal, imaging, downlink transitions |
| **ADCS control** | Attitude determination + control loop |
| **TM/TC handling** | Telemetry generation, command execution |
| **Data handling** | Payload data acquisition, compression, storage |
| **FDIR** | Fault detection, isolation, recovery |
| **Housekeeping** | Temperature, voltage, current monitoring |
| **Scheduling** | Time-tagged command execution |

---

## 4. Equipment Selection Exercise (45 min)

### Instructions

This is the main hands-on session for Day 3. Teams will select actual components:

1. **Open the Equipment Browser** (button in header bar or during session)
2. The sidebar shows categories **annotated by need**:
   - 🔵 Blue dot = Required for your mission
   - ⭕ Circle = Optional
   - Dimmed = Not needed
3. **Select equipment for each required category:**
   - Check the quantity needed (e.g., 4 reaction wheels)
   - Note the RF compatibility warning if selecting transponder/antenna
   - Watch the **live budget bar** showing mass/power/cost totals
4. **For each selection, verify:**
   - Does it fit within your subsystem mass allocation?
   - Is the power draw within your power budget for its mode?
   - Is the interface compatible (PC/104? I²C? SPI?)
5. **Review the Budget Breakdown** on the Dashboard:
   - Has per-subsystem mass changed?
   - Is the overall mass margin still positive?

### Trade Study

For at least one subsystem, select 2-3 candidate components and run a tabular trade study:
1. Go to **Trade Studies** tab
2. Load the "Component Selection Trade" template
3. Score the candidates on mass, power, cost, TRL, heritage, performance
4. Identify the winner and document rationale

### Worksheet 3.4 Tasks

1. List all selected components with mass, power, cost, TRL
2. Total the selected equipment mass and compare to parametric estimate
3. Identify any incompatibilities (RF band mismatch, voltage mismatch)
4. Document one component trade study with rationale

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| CDS | Standard CubeSat dimensions, rails, deployment switches, RBF pin |
| PC/104 | 104-pin stack connector; 3.3/5/12V power + I²C/SPI/UART/CAN data |
| Launch loads | 6-9g axial, random vibe 20-2000 Hz; MoS must be ≥ 0 |
| Propulsion | Only if needed (deorbit >600km, maintenance, constellation); cold gas simplest |
| Tsiolkovsky | m_prop = m_dry × (e^(ΔV/Isp·g₀) - 1) |
| Data handling | Storage ≥ 2× daily generation; OBC: ARM/LEON, FreeRTOS/Linux |
| Equipment | Select from KB with RF compatibility, live budget tracking, need annotations |
