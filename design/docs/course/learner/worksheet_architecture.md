# Worksheet: System Architecture Selection

**Name:** ___________________________  **Date:** ___________

---

## Part A: Architecture Decisions

For each subsystem, record your selected architecture, the key rationale, and the primary derived requirement:

| Subsystem | Options Considered | Selected Architecture | Rationale | Key Derived Requirement |
|-----------|-------------------|---------------------|-----------|----------------------|
| **EPS** | | | | |
| **AOCS** | | | | |
| **TTC** | | | | |
| **Thermal** | | | | |
| **Structure** | | | | |
| **Propulsion** | | | | |
| **OBC** | | | | |
| **Ground** | | | | |

---

## Part B: Architecture Trade Study

For one contested subsystem (where 2+ options were viable), complete a formal trade:

**Subsystem:** _______________

| Criterion | Weight | Option A: _______ | Option B: _______ | Option C: _______ |
|-----------|--------|-------------------|-------------------|-------------------|
| Mass | 0.20 | | | |
| Power | 0.15 | | | |
| Cost | 0.20 | | | |
| TRL / Heritage | 0.20 | | | |
| Performance | 0.15 | | | |
| Risk | 0.10 | | | |
| **Weighted Score** | | | | |

**Winner:** _________  **Rationale:** _______________________________________________

---

## Part C: Derived Requirements Review

From SpaceCDF Architecture tab, list all derived requirements for your AOCS selection:

| Req ID | Level | Requirement Text | Verification Method |
|--------|-------|-----------------|-------------------|
| | | | |
| | | | |
| | | | |
| | | | |

Are any requirements missing? What would you add?

_______________________________________________

---

## Part D: Block Diagram Analysis

For your selected TTC architecture, draw the block diagram showing:
- All components (blocks)
- Signal flow (connections with labels)
- Interface to other subsystems (OBC, AOCS for antenna pointing)

---

## Part E: Discussion

1. Which architecture decision had the biggest impact on your overall design?

   _______________________________________________

2. Where did architecture choices create new interface requirements?

   _______________________________________________

3. Did any architecture selection conflict with another subsystem's choice?

   _______________________________________________

---

## Part F: 1U CubeSat Architecture Exercise (UniSat-1)

Use the SpaceCDF "Load Example" button to load the **UniSat-1 (1U Tech Demo)** mission. This pre-loads a MEMS magnetometer technology demonstrator with all requirements and equipment pre-selected.

### F1: Mass Budget Analysis

The 1U CubeSat standard allows 1.33 kg maximum. Complete the table from the loaded equipment:

| Component | Mass (kg) | % of Total |
|-----------|-----------|------------|
| Structure (ISIS 1U) | 0.200 | |
| EPS (NanoPower P31us) | 0.042 | |
| Battery (NanoPower P31u) | 0.060 | |
| Solar Panels (5x body-mount) | 0.150 | |
| UHF Transceiver (ISIS TRXVU) | 0.080 | |
| UHF Monopole Antenna | 0.010 | |
| OBC (Endurosat Type I) | 0.058 | |
| Payload (MEMS Magnetometer) | 0.050 | |
| **Harness + fasteners (est.)** | 0.050 | |
| **Total** | | |
| **Margin to 1.33 kg** | | |

Is the margin sufficient for a 1U mission? What is the typical recommended margin at Phase A?

_______________________________________________

### F2: Power Budget (Orbit-Average)

With 5 body-mounted solar panels (2.3 W each, but only ~2-3 faces illuminated at any time):

| Parameter | Value |
|-----------|-------|
| Max solar input (2-3 panels illuminated) | _____ W |
| Eclipse fraction (ISS orbit, 400 km) | ~35% |
| Orbit-average solar power | _____ W |
| Battery discharge during eclipse | _____ W |
| Payload (always on) | 0.2 W |
| OBC (always on) | 0.4 W |
| Comms (UHF, ~10% duty cycle) | _____ W avg |
| **Total orbit-average consumption** | _____ W |

Is the power budget positive? What happens if the magnetometer duty cycle is reduced to 50%?

_______________________________________________

### F3: 1U Architecture Constraints

Answer the following questions about the 1U form factor:

1. Why is passive thermal control (no heaters) acceptable for this mission?

   _______________________________________________

2. Why is a magnetometer-only payload well-suited to a 1U platform?

   _______________________________________________

3. What AOCS approach is appropriate for a magnetometer mission on 1U? (Hint: consider magnetic cleanliness vs. magnetic torquers)

   _______________________________________________

4. The selected UHF link gives ~1 kbps. How much data can be downlinked per 10-minute ground pass?

   _______________________________________________

5. Is this sufficient for the magnetometer's data rate? Show your calculation.

   _______________________________________________

### F4: What Would Break at 1U?

List three mission types that would NOT fit in a 1U form factor, and explain the limiting constraint for each:

| Mission Type | Limiting Constraint |
|-------------|-------------------|
| 1. | |
| 2. | |
| 3. | |
