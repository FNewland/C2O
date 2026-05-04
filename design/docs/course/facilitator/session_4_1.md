# Session 4.1: Equipment Selection & Integration

**Duration:** 2 hours
**Prerequisites:** Day 3 complete (subsystems sized, components identified)
**References:** ECSS-E-ST-10-24C (Interfaces), CDS Rev 14.1, PC/104 Standard

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Select COTS components that meet subsystem requirements
2. Verify RF chain compatibility (transponder <-> antenna band matching)
3. Verify electrical interface compatibility (bus voltage, data protocols)
4. Track cumulative mass/power/cost against budgets during selection
5. Perform a component-level trade study for a contested subsystem

---

## 1. Component Selection Methodology (20 min)

### Teaching Notes

Component selection bridges parametric sizing (Day 3) and physical hardware. The process:

```
Parametric estimate (agent output)
  -> Requirement derived from sizing
    -> Search KB for candidates meeting requirement
      -> Score candidates (fit, mass, power, cost, TRL, heritage)
        -> Trade study if multiple viable candidates
          -> Select, verify compatibility, update budgets
```

### Selection Criteria Hierarchy

| Priority | Criterion | Rationale |
|----------|----------|-----------|
| 1 | **Meets performance requirement** | Must-have -- non-negotiable |
| 2 | **Interface compatible** | Must physically connect (voltage, protocol, band) |
| 3 | **Fits within envelope** | Mass, power, volume within subsystem allocation |
| 4 | **TRL >= 6** | Flight-demonstrated technology preferred |
| 5 | **Heritage** | Flown on similar missions = lower risk |
| 6 | **Cost** | Within budget; consider NRE for custom items |
| 7 | **Procurement** | Available within schedule; lead time acceptable |

### The "No Perfect Component" Reality

In practice, no component is perfect. Every selection involves trade-offs:
- Lighter -> more expensive
- Higher TRL -> possibly older technology with less performance
- Best performance -> highest power consumption

This is why trade studies are essential at the component level.

---

## 2. RF Chain Compatibility (20 min)

### Teaching Notes

The RF chain (transponder -> cable -> antenna) must be frequency-matched. This is the most common equipment incompatibility for CubeSat newcomers.

### Compatibility Rules

| Rule | Correct Example | Incorrect Example |
|------|----------------|-------------------|
| **Band match** | S-band transponder + S-band patch antenna | S-band transponder + X-band horn |
| **Impedance match** | 50? transponder + 50? cable + 50? antenna | Mixed impedances cause reflections |
| **Connector match** | SMA on transponder + SMA-SMA cable + SMA on antenna | SMA to N-type needs adapter |
| **Polarisation** | RHCP antenna + RHCP ground station | RHCP to LHCP -> 20+ dB loss |

### SpaceCDF RF Compatibility Check

When selecting a transponder or antenna in the Equipment Browser:
1. If you've already selected a transponder and then select an antenna in a different band -> **warning dialog** appears
2. The dialog shows: band mismatch, affected components, and asks for confirmation
3. If the spectrum selector has a band chosen -> only matching components shown

### Dual-Band Missions

Many CubeSats use two RF chains:
- **TTC (S-band UHF):** Low-rate commanding and housekeeping telemetry
- **Payload downlink (X-band):** High-rate science data

This requires:
- 2 transponders (one per band)
- 2 antennas (one per band)
- 2 RF cables
- Diplexer or separate feed if using shared antenna

SpaceCDF supports **multiple selections per category** -- select both an S-band and X-band transponder.

---

## 3. Electrical & Data Interface Verification (20 min)

### Teaching Notes

### Power Bus Compatibility

All components must operate from the EPS bus voltage. Check:

| Parameter | Typical CubeSat | What to Verify |
|-----------|----------------|----------------|
| Bus voltage | 3.3V, 5V, or unregulated battery (6-8.4V) | Component input voltage range |
| Peak current | Per switched line limit | Component inrush current |
| Connector | PC/104 or custom | Physical connector type |

### Data Bus Compatibility

Components communicate via standard protocols. Verify all components on the same bus use compatible protocols:

| Protocol | Speed | Use Case | Wiring |
|----------|-------|----------|--------|
| **I^2C** | 100-400 kbps | Sensors, magnetorquers, EPS | 2 wires (SDA, SCL) + GND |
| **SPI** | 1-50 Mbps | OBC <-> fast peripherals, payload | 4 wires (MOSI, MISO, CLK, CS) |
| **UART** | 9600-115200 bps | Debug, GPS, simple telemetry | 2 wires (TX, RX) |
| **CAN** | 1 Mbps | Distributed bus (multiple nodes) | 2 wires (CAN_H, CAN_L) |
| **RS-422** | Up to 10 Mbps | Point-to-point, longer runs | 4 wires (differential) |

### Volume Fit Verification

After selecting all components, check total volume against structure:

```
Total_volume = ? (component_volume × quantity)
Available_volume = CDS_internal_volume - structure_walls - mounting_overhead
```

SpaceCDF shows a **volume utilisation bar** on the dashboard. If >85%, consider a larger form factor.

---

## 4. Budget Tracking During Selection (15 min)

### Teaching Notes

As components are selected, the **live budget bar** in the Equipment Browser shows running totals:

```
Selected equipment mass:      2.85 kg
Parametric estimate:          3.68 kg
Launcher allocation:          6.00 kg
????????????????????????????????????
Margin remaining:             3.15 kg (52.5%) -> GREEN
```

### What to Watch For

| Indicator | Meaning | Action |
|-----------|---------|--------|
| Selected < parametric | COTS lighter than CER predicted | Margin increases -- good |
| Selected > parametric | COTS heavier than predicted | Re-evaluate; may need lighter alternative |
| Selected > allocation | **Budget exceeded** | Must change component or increase allocation |
| Power exceeds SA | Not enough power generated | Reduce duty cycle or increase SA |
| Cost exceeds ceiling | Over budget | De-scope, use cheaper components, reduce capability |

### Suggest-Then-Approve Pattern

SpaceCDF's Equipment Browser annotates each category with **need status**:
- ? Required -- mission needs this component
- ? Optional -- nice-to-have
- Dimmed -- not needed for this mission

This prevents selecting unnecessary hardware (e.g., thrusters for a mission that doesn't need propulsion).

---

## 5. Component Trade Study Exercise (45 min)

### Instructions

**Part A: Equipment Selection (25 min)**

1. Open the **Equipment Browser**
2. For each **required** category (blue dot), select at least one component:
   - Start with EPS (batteries + solar panels + EPS board)
   - Then OBC, AOCS sensors/actuators, TTC, structure
   - Use quantity selectors (e.g., ×4 for reaction wheels, ×3 for magnetorquers)
3. Watch the **live budget bar** as you select -- keep mass under allocation
4. When selecting TTC: check that the spectrum band matches your earlier selection
5. After all selections, review the **Budget Breakdown** on the Dashboard

**Part B: Component Trade Study (20 min)**

1. Choose a subsystem where you had 2+ viable candidates (e.g., reaction wheels, batteries)
2. Go to the **Trade Studies** tab
3. Load the "Component Selection Trade" template
4. Enter your candidates as options
5. Score each on: mass, power, cost, TRL, heritage, performance
6. Run the trade -- document the winner and rationale
7. Update your equipment selection if needed

### Worksheet 4.1 Tasks

1. Complete equipment selection table: component, manufacturer, mass, power, cost, TRL
2. Total selected mass vs parametric estimate vs allocation -- compute margin
3. Identify any compatibility issues found and how resolved
4. Document one component trade study with scored alternatives

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Selection method | Performance -> compatibility -> envelope -> TRL -> heritage -> cost |
| RF compatibility | Band, impedance, connector, polarisation must all match |
| Electrical | Bus voltage and data protocol compatibility verified per component |
| Volume | Check total against CDS form factor; >85% utilisation = consider upsizing |
| Budget tracking | Live totals during selection; watch for allocation exceedance |
| Need-driven | Only select what the mission requires; avoid unnecessary hardware |
