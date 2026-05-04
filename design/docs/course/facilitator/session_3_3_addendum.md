# Session 3.3 Addendum: System Architecture Selection

**Added to:** Session 3.3 (Power, AOCS, Thermal), replacing the last 20 minutes

---

## Architecture Selection in SpaceCDF (20 min)

### Teaching Notes

Before sizing individual components, the team selects the **architecture** for each subsystem. This is NASA SEH Process 4 (Design Solution Definition) -- choosing among alternative architectures based on mission requirements.

### The Architecture Selection Process

```
Mission Requirements (from Level 1)
  -> Architecture Options (presented as cards)
    -> Team selects preferred option
      -> System-level requirements auto-derived
        -> Subsystem-level requirements auto-derived
          -> Component selection guided by architecture
```

### SpaceCDF Architecture Tab

Navigate to the **Architecture** tab (in the Design group). For each subsystem:

1. **Select a subsystem** (EPS, AOCS, TTC) from the tab bar
2. **Review option cards** -- each shows:
   - Name and description
   - Mass/power/cost/TRL impact
   - Pros and cons
   - Number of derived requirements
   - Pointing accuracy (for AOCS) or data rate (for TTC)
3. **Click to select** -- the tool:
   - Shows the block diagram for the selected architecture
   - Lists all derived requirements (system + subsystem level)
   - Marks the design as stale for reconvergence

### Example: AOCS Architecture Decision

For a mission requiring 0.1deg pointing:

| Option | Pointing | Mass | Cost | Decision |
|--------|----------|------|------|----------|
| Passive magnetic | 10deg | 0.05 kg | 2 kEUR | Too coarse |
| Magnetorquer-only | 3deg | 0.1 kg | 8 kEUR | Too coarse |
| 3 RW + MTQ | 0.5deg | 0.5 kg | 35 kEUR | Marginal |
| **4 RW + ST + MTQ** | **0.05deg** | **0.8 kg** | **55 kEUR** | **Selected** |

Selecting "4 RW + ST + MTQ" derives:
- SR-AOCS-001: "The AOCS shall achieve <=0.1deg pointing in imaging mode"
- SR-AOCS-002: "The AOCS shall autonomously enter safe mode on anomaly"
- SSR-AOCS-001: "The star tracker shall provide <=10 arcsec attitude knowledge"
- SSR-AOCS-002: "Each reaction wheel shall provide >=5 mNm torque"

These requirements appear in the **Requirements** tab at system and subsystem levels.

### Discussion Prompt

*For your mission: which EPS architecture is appropriate? Does your payload power demand require deployable panels? What are the deployment risks?*

---

### Updated Worksheet 3.3 Addition

**Part F: Architecture Selection**

For each subsystem, record your architecture choice and the key derived requirement:

| Subsystem | Architecture Chosen | Key Derived Requirement |
|-----------|-------------------|----------------------|
| EPS | | |
| AOCS | | |
| TTC | | |
| Thermal | | |
| Structure | | |
| Propulsion | | |

**Rationale for AOCS choice:** _______________________________________________

**Rationale for TTC choice:** _______________________________________________
