# Session 5.3: Launch Integration

**Duration:** 2 hours
**Prerequisites:** Session 5.2 (regulatory understood)
**References:** CDS Rev 14.1; SpaceX Rideshare PUG; Exolaunch EXOpod User Manual

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Select a launch provider based on mission requirements
2. Understand Launch ICD requirements (mechanical, electrical, environmental)
3. Identify deployer compatibility for their CubeSat form factor
4. Specify separation switch and inhibit requirements
5. Derive environmental test levels from the selected launch vehicle

---

## 1. Launch Provider Selection (25 min)

### Teaching Notes

### Selection Criteria

| Criterion | Weight | Rationale |
|-----------|--------|-----------|
| **Cost** | High | Launch is 10-20% of total mission cost |
| **Orbit** | Critical | Must reach desired orbit (altitude, inclination) |
| **Schedule** | High | Manifest date must align with development timeline |
| **Deployer compatibility** | Critical | CubeSat form factor must fit available deployer |
| **Track record** | Medium | Flight heritage reduces risk |
| **Regulatory** | Medium | ITAR implications for non-US payloads on US vehicles |

### Available Providers (2026)

*[Source: SpaceCDF launch_providers.yaml — verified against public data]*

| Provider | Vehicle | Type | Price | Orbit | Cadence |
|----------|---------|------|-------|-------|---------|
| SpaceX | Falcon 9 Transporter | Rideshare | $350K (≤50kg) | SSO 525 km | 4/year |
| Rocket Lab | Electron | Dedicated | $7.5M | Custom | 12/year |
| Exolaunch | Various | Broker | Custom | SSO | 6/year |
| D-Orbit | ION Carrier | Space tug | ~$100K/slot | Custom precise | 4/year |
| ISILaunch | Various | Broker | Custom | SSO/LEO | 4/year |
| NanoRacks | ISS deploy | ISS deploy | $90K/U | 51.6°, 410 km | 6/year |
| Firefly | Alpha | Dedicated | $15M | Custom | 4/year |
| ISRO | PSLV | Rideshare | Custom | SSO/LEO | 4/year |

### Decision Flow

```
Is your orbit ISS (51.6°, 410 km)?
  → Yes: NanoRacks ISS deploy ($90K/U)
  → No: ↓
Is your mass ≤ 50 kg AND SSO acceptable?
  → Yes: SpaceX Transporter ($350K minimum)
  → No: ↓
Do you need a specific non-SSO orbit?
  → Yes: Dedicated launcher (Rocket Lab $7.5M, Firefly $15M)
  → No: Broker (Exolaunch, ISILaunch) for best value
```

### SpaceCDF Launch Selector

The Dashboard includes a **Launch Provider Selector** that:
- Shows all providers filtered by spacecraft mass (over-capacity flagged)
- Displays pricing, orbit, deployer compatibility
- Selecting a provider auto-sets the **target mass allocation** (85% of capacity)
- Marks design as stale (mass budget updates)

---

## 2. Interface Control Document (ICD) (25 min)

### Teaching Notes

The Launch ICD defines the contractual interface between the satellite and the launch vehicle/deployer.

### Mechanical Interface

| Parameter | CDS 3U Requirement | Typical ICD Check |
|-----------|--------------------|--------------------|
| Dimensions | 100 × 100 × 340.5 ±0.5 mm | Fit check in deployer |
| Rail dimensions | 8.5 × 8.5 mm ± 0.1 mm | Caliper measurement |
| Surface roughness | Rail surfaces < 1.6 μm Ra | Surface finish inspection |
| CG location | Within 2 cm of geometric centre | Mass properties measurement |
| No protrusions | Nothing beyond rail envelope (stowed) | Visual inspection |

### Electrical Interface

| Parameter | Requirement | Verification |
|-----------|------------|-------------|
| **Deployment switches** | Min 2 on rail faces (+X, -X) | Functional test |
| **RBF pin** | 1 minimum; deactivates all power | Functional test |
| **Total switch force** | ≤ 9 N (NanoRacks) / per deployer ICD | Force gauge measurement |
| **Battery state** | ≤ 50% SoC at delivery | Voltage measurement |
| **No RF emissions** | No TX while in deployer | Test in integration |
| **Charging port** | Access for pre-launch top-up | Design review |

### Three-Inhibit Rule

The satellite must have at least **3 independent inhibits** preventing activation while in the deployer:
1. **Deployment switch 1** (rail contact switch)
2. **Deployment switch 2** (second rail contact switch)
3. **RBF pin** (physical pin removed before encapsulation)

All three must be active simultaneously to keep the satellite powered off.

---

## 3. Deployer Selection (20 min)

### Teaching Notes

*[Source: Vendor documentation — ISIPOD, EXOpod, CSD, NRCSD]*

| Deployer | Provider | Sizes | Mass Limit | Heritage |
|----------|---------|-------|-----------|---------|
| **ISIPOD** | ISISPACE | 1-16U | Per CDS | 300+ CubeSats; most-flown |
| **EXOpod Nova** | Exolaunch | 6-16U | 8-36 kg | 280+ CubeSats |
| **EXOpod AIR** | Exolaunch | 6U | 16 kg | Lightweight (6.5 kg deployer) |
| **CSD** | Rocket Lab | 3-12U | Per CDS | No pyrotechnics; DC motor door |
| **NRCSD** | NanoRacks | 1-6U | Per CDS | ISS deployment only |
| **XPOD** | UTIAS/SFL | Custom | 16 kg | Spring-loaded; custom shapes |

### Deployer-Satellite Compatibility Check

Verify:
1. **Form factor fits** (e.g., 3U satellite → 3U deployer slot)
2. **Mass within deployer limit** (not just CDS limit)
3. **Rail profile compatible** (CDS-standard rails required for most deployers)
4. **Deployment switches in correct positions** (varies by deployer)
5. **No protrusions** that would jam the deployer rails
6. **Antenna stowage** doesn't interfere with deployer door

---

## 4. Environmental Test Levels (20 min)

### Teaching Notes

Test levels derive from the **launch vehicle Payload User's Guide (PUG)**:

### Process

```
Launch vehicle PUG → Maximum Predicted Environment (MPE)
  → Add qualification margin (+3 dB for random, +5°C for thermal)
    → Qualification/Proto-flight test levels
```

### Example: SpaceX Transporter Rideshare

| Test | Proto-flight Level | Duration |
|------|-------------------|----------|
| Random vibration | MPE + 3 dB; ~7 gRMS overall | 1 min/axis × 3 axes |
| Sine vibration | 1.25 g, 8-100 Hz | 2 oct/min sweep |
| Shock | 500 g at 500 Hz to 1500 g at 5000 Hz | 2 reps/axis |
| TVAC hot | Predicted max + 10°C | 4 cycles, 1 hr dwell |
| TVAC cold | Predicted min - 10°C | 4 cycles, 1 hr dwell |
| Mass | Measured on calibrated scale | ±0.01 kg precision |

### Test Sequence

```
1. Receive flight hardware from assembly
2. Initial functional test (reference baseline) ✓
3. Random vibration (3 axes, 1 min each) ✓
4. Post-vibe functional test ✓
5. Thermal vacuum (4-8 cycles, func at extremes) ✓
6. Post-TVAC functional test ✓
7. EMC test (if required) ✓
8. Final mass measurement ✓
9. Deployer fit check ✓
10. Pack and ship to launch site
```

---

## 5. SpaceCDF Launch Integration Exercise (30 min)

### Instructions

1. **Launch Selector** on Dashboard:
   - Review available providers filtered by your spacecraft mass
   - Select a provider — note the mass allocation update
   - Which deployer is compatible?

2. **Exports** tab → generate documents:
   - **Launch ICD template** (if available) — review mechanical/electrical interface
   - **End-of-Life Analysis** — confirm debris compliance for selected orbit

3. **Worksheet 5.3** — ICD compliance checklist:
   - Verify CDS dimensional compliance
   - Verify deployment switch locations
   - Verify RBF pin provision
   - Verify CG location (from mass budget)
   - List the environmental test sequence and levels

### Discussion Points
- What if your preferred launch vehicle has a schedule delay?
- What ITAR implications arise from launching on a US vehicle?
- How does the deployer selection constrain your antenna deployment design?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Provider selection | Cost, orbit, schedule, deployer compatibility, track record |
| ICD | Mechanical (dimensions, CG) + Electrical (switches, RBF) + Environmental (test levels) |
| Three-inhibit rule | 2 deployment switches + 1 RBF pin = 3 independent inhibits |
| Deployers | ISIPOD (most heritage), EXOpod (lightweight), CSD (no pyrotechnics), NRCSD (ISS) |
| Test levels | From launch vehicle PUG + qualification margin; proto-flight for CubeSats |
| SpaceCDF | Launch Selector auto-sets mass allocation; Exports generates ICD template |
