# Constraint Propagation Engine — Deep Design

## Current State: 50 interconnections
## Target State: 220+ interconnections (from research)

## Architecture for Deep Concurrent Design

The constraint engine needs to operate at THREE levels simultaneously:

### Level 1: Parameter-to-Parameter (current, expand to 220+)
When parameter A changes, parameters B, C, D are affected.
Direction: A→B, sensitivity, nature (linear/threshold/inverse).

### Level 2: Requirement Compliance Cascade (NEW)
When a subsystem parameter changes, check:
1. Does the subsystem requirement still hold?
2. If not, does the system requirement still hold?
3. If not, does the mission requirement still hold?
4. Flag at the HIGHEST level where compliance fails.

Example: 
- Equipment selection changes AOCS mass from 0.5 to 0.8 kg
- SSR-AOCS-001 (mass <= 1.0 kg): still OK ✓
- SR-MASS-001 (total dry mass <= 6 kg): check → if now 6.3 kg → VIOLATED
- MR-001 (system achievable): may need review

### Level 3: Resolution Impact Analysis (expand)
For each violation, compute the FULL cascade of each resolution option:
- "Increase TX power" → power budget impact + thermal impact + mass impact + cost impact
- Show ALL affected budgets, not just the primary one
- Rank resolutions by: fewest cross-budget impacts, lowest mass impact, lowest cost

## Interconnection Categories (from research)

| Category | Connections | Key Coupling |
|----------|-------------|-------------|
| Orbit ↔ Payload | 20 | Altitude drives GSD, coverage, signal |
| Orbit ↔ Power | 12 | Eclipse fraction, beta angle, solar flux |
| Orbit ↔ Thermal | 8 | Albedo, IR, eclipse cold |
| Orbit ↔ Link | 10 | Range, Doppler, contact geometry |
| Orbit ↔ Propulsion | 8 | Drag, station-keeping, deorbit |
| Orbit ↔ Radiation | 5 | Van Allen, SAA, trapped particles |
| Payload ↔ AOCS | 12 | Pointing, stability, jitter, slew |
| Payload ↔ Data | 8 | Generation, storage, compression |
| Payload ↔ Power | 6 | Duty cycle, peak vs average |
| Payload ↔ Thermal | 6 | Dissipation, detector cooling |
| Power ↔ Mass | 8 | SA, battery, EPS board mass |
| Power ↔ Thermal | 6 | SA/radiator competition, PA heat |
| Power ↔ Volume | 4 | SA stowage, battery volume |
| AOCS ↔ Mass | 8 | Sensor/actuator mass |
| AOCS ↔ Power | 6 | RW power, ST power |
| AOCS ↔ Link | 4 | Antenna pointing, FOV exclusion |
| Link ↔ Power | 6 | TX DC power, PA efficiency |
| Link ↔ Thermal | 4 | PA waste heat |
| Link ↔ Mass | 4 | TX, antenna mass |
| Link ↔ Ground | 6 | Station G/T, contact time, bands |
| Structure ↔ All | 12 | Form factor limits everything |
| Propulsion ↔ Mass | 6 | Propellant, tank, dry system |
| Propulsion ↔ Volume | 4 | Tank sizing |
| Thermal ↔ Mass | 4 | Radiator, MLI, heaters |
| Cost ↔ All | 15 | Launch, ops, hardware, NRE |
| Schedule ↔ All | 10 | TRL, test scope, procurement |
| Requirements ↔ Design | 20 | Circular: req→design→violates→change req |
| **TOTAL** | **220+** | |

## Implementation Approach

### Step 1: Expand INTERCONNECTION_MAP to 220 entries
Each entry: {source, target, budget, relationship, sensitivity, description, positions, bidirectional}

### Step 2: Add Requirement Compliance Layer
When parameters change, trace UP through requirement hierarchy:
- Check SSR satisfaction → SR satisfaction → MR satisfaction
- Flag violations at correct level with traceability

### Step 3: Resolution Impact Computation
For each resolution option:
- Estimate the parameter change needed
- Propagate through interconnection map
- Compute net impact on ALL 8 budgets
- Rank by total system impact (weighted sum of budget changes)

### Step 4: Circular Dependency Detection
Some changes create loops:
- Mass too high → reduce battery → power margin too low → reduce duty cycle → less data → ...
The engine must detect cycles and present them as trade-off decisions (human resolves, not auto).

### Step 5: Sensitivity Dashboard
Show the N² matrix of interconnections graphically:
- Color by strength of coupling
- Click any cell to see the specific relationship
- Highlight critical path (tightest margin chain)
