# Session 2.3: Interface Management

**Duration:** 2 hours
**Prerequisites:** Session 2.2 (functions defined and allocated)
**References:** NASA SEH §6.3 (Process 12), ECSS-E-ST-10-24C

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Identify all subsystem-to-subsystem interfaces using an N^2 matrix
2. Classify interface types (mechanical, electrical, thermal, data, RF, optical)
3. Detect and resolve interface conflicts
4. Write interface requirements for key subsystem pairs
5. Use SpaceCDF's interface matrix and conflict resolution workflow

---

## 1. Why Interface Management Matters (15 min)

### Teaching Notes

*[Source: NASA SEH §6.3 -- Process 12: Interface Management]*

Interface problems are the #1 cause of integration failures. NASA SEH states: "Most system failures can be traced back to interface problems."

**Root causes:**
- Assumptions made by one subsystem about another's behaviour
- Voltage/protocol mismatches (e.g., 3.3V logic driving 5V input)
- Thermal coupling not accounted for (e.g., hot transponder next to cold-sensitive payload)
- Mechanical interference (e.g., antenna deployment blocking star tracker FOV)
- EMC interference (e.g., TX radiation coupling into payload receiver)

**Prevention:** Every subsystem pair must have their interface explicitly defined, agreed, and documented in an Interface Requirements Document (IRD) per ECSS-E-ST-10-24C.

---

## 2. The N^2 (N-Squared) Interface Matrix (25 min)

### Teaching Notes

The N^2 matrix is a standard systems engineering tool that maps all subsystem interactions:

### Structure
- **Diagonal:** Subsystems (power, AOCS, link, thermal, structure, propulsion, data, payload)
- **Off-diagonal cells:** Interface between the row and column subsystems
- **Upper triangle:** Data/command flow in one direction
- **Lower triangle:** Data/command flow in the other direction

### For a CubeSat with 8 subsystems:
- 8 subsystems -> 8×7/2 = **28 potential interface pairs**
- Typical CubeSat: **18-22 defined interfaces** (not all pairs interact)

### Interface Types

| Type | Symbol | Description | Example |
|------|--------|-------------|---------|
| **Mechanical** | M | Physical attachment, loads, alignment | Payload mounting to structure |
| **Electrical** | E | Power connections, bus voltage | EPS 28V bus to all subsystems |
| **Thermal** | T | Heat transfer paths, thermal coupling | Transponder heat to radiator |
| **Data** | D | Digital communication (I^2C, SPI, UART, CAN) | OBC commands to AOCS |
| **RF** | R | Radio frequency coupling or interference | TX interference with payload |
| **Optical** | O | Light path, FOV clearance, stray light | Star tracker FOV clearance |

### Common CubeSat Interfaces (Verified)

| Pair | Types | Key Concern |
|------|-------|-------------|
| Power <-> AOCS | E | Bus voltage compatibility; RW power draw |
| Power <-> Link | E | TX peak power demand; switched line allocation |
| Power <-> Thermal | E, T | SA thermal coupling; radiator vs SA area competition |
| Power <-> Payload | E | Peak power switching; duty cycle coordination |
| Structure <-> AOCS | M | RW/ST mounting alignment; vibration isolation |
| Structure <-> Payload | M, O | Payload alignment stability; FOV clearance |
| Data <-> AOCS | D | Attitude data for payload pointing; mode commands |
| Data <-> Link | D | Telemetry stream routing; TC distribution |
| Data <-> Payload | D | Science data acquisition; instrument commanding |
| Link <-> Payload | R | EMC: TX interference with payload receiver |
| Link <-> AOCS | R, O | Antenna vs star tracker FOV |
| Thermal <-> Payload | T | Detector cooling; operating temperature range |
| AOCS <-> Payload | M | Reaction wheel vibration vs payload stability |

---

## 3. Conflict Detection and Resolution (30 min)

### Teaching Notes

Interface conflicts arise when two subsystems have incompatible requirements at their shared boundary.

### Severity Classification

| Severity | Description | Example | Action Required |
|----------|-------------|---------|----------------|
| **Critical** | Design cannot close without resolving | EMC: TX interference prevents payload operation | Must resolve before PDR |
| **Major** | Significant design impact | Radiator area competes with SA area | Must have mitigation plan by PDR |
| **Minor** | Manageable with minor design adjustment | Star tracker FOV partially blocked by antenna | Accommodation analysis needed |

### Resolution Options

For each conflict, the team has four options:

1. **Relocate:** Move a component to avoid the conflict (e.g., move star tracker to different face)
2. **Shield/Isolate:** Add shielding or isolation (e.g., EMC filter, vibration isolator)
3. **Time-Division:** Schedule activities to avoid simultaneous operation (e.g., no TX during imaging)
4. **Accept Risk:** Document the risk and accept the margin reduction

### Resolution Workflow in SpaceCDF

1. Navigate to **Interfaces** tab
2. Click on a red-bordered cell (conflict detected)
3. Review: affected parameters, responsible positions, severity
4. Click **"Resolve Conflict"**
5. Select resolution option, enter rationale
6. Choose: Resolve / Accept Risk / Defer

**Discussion prompt:** *For the "SA area vs radiator area" conflict -- what are the pros and cons of each resolution option?*

---

## 4. Interface Requirements (20 min)

### Teaching Notes

For each significant interface, write formal requirements that define the boundary agreement:

### Example: EPS <-> All Subsystems (Power Bus)

```
IR-PWR-001: The EPS shall provide a regulated bus voltage of 
            3.3V ± 0.1V and 5.0V ± 0.25V to all subsystems.
IR-PWR-002: Each subsystem shall not draw more than its allocated 
            power from the bus without EPS approval.
IR-PWR-003: The EPS shall provide at least 2 switched power lines 
            for payload and 2 for TTC.
```

### Example: Structure <-> AOCS (Mounting)

```
IR-STR-AOCS-001: The star tracker mounting shall maintain alignment 
                  to within 0.05° over the operating temperature range.
IR-STR-AOCS-002: The reaction wheel mounting shall provide vibration 
                  isolation with first mode > 50 Hz.
```

### Example: Link <-> Payload (EMC)

```
IR-EMC-001: The TX conducted emissions shall be below -60 dBm in the 
            payload receiver band during imaging mode.
IR-EMC-002: Alternatively, TX and imaging shall not operate simultaneously 
            (time-division approach).
```

**Exercise:** *Write 2 interface requirements for the most critical interface pair in your design. Use the "shall" convention and make them verifiable.*

---

## 5. SpaceCDF Interface Matrix Exercise (30 min)

### Instructions

1. Open the **Interfaces** tab
2. Review the N^2 matrix -- each coloured dot represents an interface type
3. Click on 3 interface cells to examine their details:
   - What types are defined?
   - Is there a conflict?
   - What are the responsible positions?
4. For any conflict (red border):
   - Click to view details
   - Use the "Resolve Conflict" workflow
   - Select a resolution and enter rationale
5. Complete Worksheet 2.3: write interface requirements for 2 key pairs

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| N^2 matrix | Maps all subsystem-to-subsystem interfaces systematically |
| 6 types | Mechanical, Electrical, Thermal, Data, RF, Optical |
| Conflicts | Incompatible requirements at shared boundaries; 3 severity levels |
| Resolution | Relocate, Shield/Isolate, Time-Division, or Accept Risk |
| IRD | Formal interface requirements define boundary agreements |
| Prevention | Define interfaces early; most integration failures trace to interface problems |
