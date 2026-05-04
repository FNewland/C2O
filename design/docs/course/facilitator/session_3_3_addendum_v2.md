# Session 3.3 Addendum v2: System Architecture Selection (Complete)

**Replaces:** Last 30 minutes of Session 3.3
**References:** NASA SEH SS4.4 (Process 4), ECSS-E-ST-10C SS5.4

---

## Architecture Selection Workflow (15 min)

### Teaching Notes

After sizing each subsystem parametrically (Day 3 morning), the team now selects the **architecture** -- the structural approach for each subsystem. This is the bridge between "how much" (parametric sizing) and "how exactly" (detailed design).

### The Architecture Tab in SpaceCDF

Navigate to the **Architecture** tab (Design group). The tool shows:

1. **8 subsystem tabs**: EPS, AOCS, TTC, Thermal, Structure, Propulsion, OBC, Ground
2. **Progress bar**: X/8 subsystems configured, N requirements derived
3. **Position indicator**: shows which subsystem is "yours" based on your role
4. **Option cards** per subsystem with one-click selection

### Position-Specific Default Views

When you open the Architecture tab, it defaults to YOUR subsystem:
- Power Engineer -> EPS tab
- AOCS Engineer -> AOCS tab
- Comms Engineer -> TTC tab
- Thermal Engineer -> Thermal tab
- Structures Engineer -> Structure tab
- Propulsion Engineer -> Propulsion tab
- Software Engineer -> OBC tab
- Ground Segment -> Ground tab
- Systems Engineer -> EPS (reviews all)

### Requirement Derivation

When you select an architecture, the tool **automatically derives requirements** at two levels:

**System-level** (SR-xxx): What the system must achieve
> "The AOCS shall achieve <=0.1deg pointing accuracy in imaging mode"

**Subsystem-level** (SSR-xxx): What specific components must provide
> "The star tracker shall provide <=10 arcsec attitude knowledge"

These appear in the **Requirements** tab with purple "Architecture-Derived" badges.

---

## Architecture Exercise (15 min)

### Instructions

1. Open the **Architecture** tab
2. Your subsystem tab should be highlighted -- click it if not
3. **Review all options** for your subsystem -- read pros/cons and metrics
4. **Select the architecture** that best fits the mission requirements
5. **Review the derived requirements** that appear below your selection
6. **Check the block diagram** -- does it match your understanding?
7. Move to the next subsystem (or coordinate with your team)

### Team Coordination

After each position selects their architecture:
1. Systems Engineer reviews all selections for consistency
2. Check: does the EPS generate enough power for the selected AOCS?
3. Check: does the structure have enough volume for the selected propulsion?
4. Check: does the ground segment support the selected TTC bands?

If conflicts arise, negotiate changes in the Architecture tab.

### Checking Requirements

Navigate to the **Requirements** tab:
- Use the level filter: "system" or "subsystem"
- Architecture-derived requirements appear with purple badges
- Each shows the subsystem that generated it
- Total count: typically 15-30 requirements from 8 architecture selections
