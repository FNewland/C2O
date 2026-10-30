# Worksheet 3.4: Structure, Propulsion, and Equipment Selection

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Equipment Browser, Dashboard, Trade Studies, Budget Breakdown

---

## Quick Reference: Structure and Propulsion Concepts

### CubeSat Design Specification (CDS Rev 14) Key Dimensions

The CDS defines standard CubeSat form factors. All CubeSats must comply with these dimensions to fit inside standard deployers (e.g., ISIPOD, NRCSD, Exolaunch). The unit "U" represents a 10 x 10 x 11.35 cm cube.

| Form Factor | Dimensions (mm) | Max Mass (kg) | Internal Volume (cm$^3$) | Rails | Typical Use |
|------------|-----------------|---------------|------------------------|-------|-------------|
| **1U** | 100 x 100 x 113.5 | 2.0 | ~1,000 | 4 | Technology demo, simple sensors |
| **1.5U** | 100 x 100 x 170.2 | 3.0 | ~1,500 | 4 | Extended 1U with more volume |
| **2U** | 100 x 100 x 227.0 | 4.0 | ~2,000 | 4 | IoT, AIS, simple payloads |
| **3U** | 100 x 100 x 340.5 | 6.0 | ~3,000 | 4 | Standard EO, comms, science |
| **6U** | 100 x 226.3 x 340.5 | 12.0 | ~6,000 | 4 | High-performance EO, SAR, comms |
| **12U** | 226.3 x 226.3 x 340.5 | 24.0 | ~12,000 | 8 | Advanced payloads, propulsion |
| **16U** | 226.3 x 226.3 x 454.0 | 32.0 | ~16,000 | 8 | Microsatellite-class missions |

**Key CDS requirements (all form factors):**

| Requirement | Specification | Why It Matters |
|------------|---------------|---------------|
| Rail material | Hard anodised Al 7075-T6 or 6061-T6 | Prevents cold welding in vacuum; provides structural load path |
| Rail cross-section | 8.5 x 8.5 mm minimum contact | Transmits launch loads through deployer rails |
| Deployment switches | Minimum 1 per accessible rail face | Ensures spacecraft is powered off until deployed |
| RBF (Remove Before Flight) pin | Required | Physically disconnects batteries during ground handling |
| No protrusions beyond rail envelope (stowed) | Required | Prevents jamming inside the deployer |
| CG offset from geometric centre | <= 2 cm | Prevents uncontrolled tumbling at deployment; deployer balance |
| Fundamental frequency | > 40 Hz (first mode) | Avoids resonance with launch vehicle modes |

### Structural Loads and Margins

During launch, the spacecraft experiences:

- **Quasi-static acceleration:** 6--9 g axial (along rocket axis), 2--4 g lateral (sideways). Think of your 5 kg CubeSat feeling like it weighs 45 kg.
- **Random vibration:** Broadband shaking at 20--2000 Hz. Critical for PCB solder joints and connectors.
- **Shock:** Brief, high-g pulses (500--2000 g) at separation events. Critical for brittle components.

**Margin of Safety (MoS):** The ratio of what the structure can withstand to what it must withstand, minus 1. Must be >= 0. If MoS is negative, the structure fails under the design load.

**Material properties (Al 7075-T6):** Yield strength $\sigma_y = 503$ MPa, Ultimate strength $\sigma_u = 572$ MPa. Factor of Safety: 1.25 (yield), 1.5 (ultimate).

### Propulsion Decision Tree

Not every CubeSat needs propulsion. Use this decision tree:

```
START: Does my mission need propulsion?
  |
  +-- Orbit altitude < 500 km?
  |     YES --> Natural atmospheric drag deorbits within 5 years (FCC compliant)
  |             Do I need orbit maintenance to extend lifetime?
  |               NO  --> NO PROPULSION NEEDED
  |               YES --> Need drag compensation (5-15 m/s per year)
  |
  +-- Orbit altitude 500-700 km?
  |     Natural lifetime is 5-25+ years
  |     FCC 5-year rule: likely NON-COMPLIANT without active deorbit
  |     --> PROPULSION REQUIRED for deorbit (50-150 m/s)
  |
  +-- Orbit altitude > 700 km?
  |     Natural lifetime is decades to centuries
  |     IADC 25-year guideline: NON-COMPLIANT
  |     --> PROPULSION REQUIRED for deorbit (high Delta-V)
  |
  +-- Constellation phasing needed?
  |     YES --> Add 10-50 m/s for orbit plane/phase adjustment
  |
  +-- Collision avoidance needed?
        YES --> Add 1-5 m/s reserve per manoeuvre
```

**Key rule:** Below ~500 km, you almost certainly do not need propulsion. Above ~600 km, you almost certainly do. The 500--600 km range depends on your specific ballistic coefficient and mission lifetime.

### Propulsion Technologies Comparison

| Type | How It Works | $I_{sp}$ (s) | Thrust | Propellant Mass (100 m/s, 5 kg S/C) | System Dry Mass | Total System Mass | Burn Time | Cost |
|------|-------------|-------------|--------|--------------------------------------|-----------------|-------------------|-----------|------|
| **Cold gas** | Pressurised gas expelled through nozzle | 40--80 | 10--100 mN | 0.87 kg | 0.3 kg | **1.17 kg** | Minutes | ~15 kEUR |
| **Resistojet** | Gas heated before expulsion | 80--150 | 10--50 mN | 0.34 kg | 0.3 kg | **0.64 kg** | Minutes | ~25 kEUR |
| **Electrospray (FEEP)** | Liquid metal ionised and accelerated by electric field | 500--1500 | 0.01--1 mN | 0.04 kg | 0.9 kg | **0.94 kg** | Months | ~50 kEUR |
| **Hall effect** | Xenon ionised and accelerated by magnetic/electric fields | 800--1500 | 1--10 mN | 0.05 kg | 1.5 kg | **1.55 kg** | Weeks | ~80 kEUR |
| **Green monoprop** | Catalytic decomposition of non-toxic propellant | 200--250 | 0.1--1 N | 0.21 kg | 1.0 kg | **1.21 kg** | Seconds | ~60 kEUR |

**The fundamental trade-off:**

- **High $I_{sp}$ (electric propulsion):** Uses very little propellant but has very low thrust, so manoeuvres take weeks or months. The thruster hardware is also heavier and more expensive.
- **Low $I_{sp}$ (chemical/cold gas):** Uses much more propellant but provides high thrust for quick manoeuvres. Hardware is simpler, lighter, and cheaper.

Choose based on: How much $\Delta V$ do you need? How fast must the manoeuvre happen? How much mass/volume/cost can you afford?

---

## Key Equations Reference

> **Structural Margin of Safety:** $\text{MoS} = \frac{\sigma_{\text{allow}}}{\sigma_{\text{design}} \times \text{FoS}} - 1 \geq 0$
> &nbsp;&nbsp; FoS: Yield 1.25, Ultimate 1.5 (metallic)
>
> **Tsiolkovsky rocket equation:** $\Delta V = I_{sp} \cdot g_0 \cdot \ln(m_0/m_f)$
>
> **Propellant mass:** $m_{\text{prop}} = m_{\text{dry}} \times \left(e^{\Delta V/(I_{sp} \cdot g_0)} - 1\right)$
> &nbsp;&nbsp; $g_0 = 9.80665$ m/s$^2$
>
> **Data storage:** $S = V_{\text{daily}} \times N_{\text{days}} \times f_{\text{safety}}$
>
> **Fundamental frequency:** $f_1 > 40$ Hz (deployer requirement)

---

## Worked Example: UniSat-1 (1U) Structure and Propulsion

### CDS Compliance

| Parameter | 1U Specification | UniSat-1 Design | Compliant? |
|-----------|-----------------|-----------------|-----------|
| Dimensions | 100 x 100 x 113.5 mm | 100 x 100 x 113.5 mm (ISIS 1U frame) | Y |
| Maximum mass | 2.0 kg (CDS) / 1.33 kg (NanoRacks) | 1.0 kg target | Y |
| Rail material | Hard anodised Al 7075-T6 | ISIS standard frame | Y |
| Deployment switches | Min 1 per accessible face | 2 (ISIS standard) | Y |
| RBF pin | Required | Included | Y |
| CG offset | <= 2 cm | < 1 cm (symmetric layout) | Y |
| Protrusions (stowed) | None beyond rail envelope | UHF antenna stowed along rail | Y |

### Propulsion Decision

**Orbit altitude:** 400 km. **Natural lifetime:** ~8--14 months (ballistic coefficient $BC = m/(C_D A) = 1.0/(2.2 \times 0.01) = 45.5$ kg/m$^2$).

FCC 5-year rule satisfied without propulsion. No orbit maintenance needed (6-month mission). No constellation phasing. **Decision: No propulsion.**

### Structural Margin (Axial Load)

**Given:** Mass = 1.0 kg, axial load = 9 g, 4 rails.

$F_{\text{axial}} = \frac{1.0 \times 9 \times 9.81}{4} = \frac{88.3}{4} = 22.1$ N per rail

$\sigma = \frac{22.1}{8.5 \times 10^{-3} \times 8.5 \times 10^{-3}} = \frac{22.1}{7.225 \times 10^{-5}} = 0.31$ MPa

$\text{MoS}_y = \frac{503}{0.31 \times 1.25} - 1 = \frac{503}{0.39} - 1 = 1289 \gg 0$ **Pass** (by a very large margin)

**Key insight:** Quasi-static axial stress is never the critical case for CubeSats. The real structural risks are: (a) PCB solder joint fatigue from random vibration, (b) deployment mechanism reliability, (c) stiffness (fundamental frequency > 40 Hz).

### Equipment List

| # | Category | Component | Mass (g) | Power (W) | Cost (kEUR) |
|---|----------|-----------|----------|----------|-------------|
| 1 | Structure | ISIS 1U frame | 200 | -- | 4.0 |
| 2 | EPS + Battery | GomSpace P31us | 200 | 0.3 | 12.0 |
| 3 | Solar cells | Body-mounted GaAs (5 faces) | 50 | -- | 8.0 |
| 4 | OBC | Custom MSP430/Cortex-M | 30 | 0.3 | 3.0 |
| 5 | Comms | NanoCom AX100 (UHF) | 60 | 0.5 | 8.0 |
| 6 | Antenna | UHF monopole (deployable) | 20 | -- | 2.0 |
| 7 | Payload | MEMS magnetometer PCB | 50 | 0.2 | 5.0 |
| 8 | AOCS | Permanent magnet + hysteresis rods | 30 | 0 | 1.0 |
| 9 | Harness | Internal cables, connectors | 50 | -- | 1.0 |
| | **TOTAL** | | **690** | **~1.3 (peak)** | **~44** |

Mass margin: 1330 - 690 = 640 g (48%). With 20% equipment margin + 20% system margin (MEV): 1330 - 994 = 336 g (25%). **Green.**

---

## Part A: CDS Compliance Check

| CDS Requirement | Your Design Value | Specification | Compliant? |
|----------------|-------------------|---------------|-----------|
| Form factor: _____ U | Dimensions: _____ mm | _____ mm | Y / N |
| Maximum mass | _____ kg (wet) | _____ kg | Y / N |
| Rail material | | Hard anodised Al | Y / N |
| Deployment switches | _____ (quantity) | Min 2 | Y / N |
| RBF pin provided | Y / N | Required | Y / N |
| No protrusions beyond rails (stowed) | Y / N | Required | Y / N |
| CG within 2 cm of geometric centre | Estimated: _____ cm offset | <= 2 cm | Y / N |
| Fundamental frequency | Estimated: _____ Hz | > 40 Hz | Y / N |

**Non-compliance items and corrective actions:**

_____________________________________________________________________

_____________________________________________________________________

---

## Part B: Structural Margin Calculation

**Axial launch load:** _____ g &nbsp;&nbsp; **Lateral launch load:** _____ g

**Load per rail** (4 rails, equal sharing):

$F_{\text{axial}} = \frac{m \times a_{\text{axial}} \times g_0}{4} = \frac{\ \ \ \ \times \ \ \ \ \times 9.81}{4} = $ _____ N

**Stress in rail** (cross-section 8.5 x 8.5 mm = $7.225 \times 10^{-5}$ m$^2$):

$\sigma = \frac{F}{A} = \frac{\ \ \ \ }{7.225 \times 10^{-5}} = $ _____ MPa

**Margin of safety (yield, Al 7075-T6, $\sigma_y = 503$ MPa):**

$\text{MoS} = \frac{503}{\ \ \ \ \times 1.25} - 1 = $ _____

**Pass?** Y / N

_____________________________________________________________________

---

## Part C: Propulsion Decision

**Does your mission need propulsion?**

| Question | Answer |
|----------|--------|
| Orbit altitude | _____ km |
| Natural orbital lifetime | _____ years |
| FCC 5-year compliant without propulsion? | Y / N |
| Orbit maintenance required? | Y / N |
| Constellation phasing required? | Y / N |
| Active deorbit required? | Y / N |

**Decision:** &nbsp; Propulsion / No propulsion

---

**If propulsion is selected, complete this section. Show all working.**

**Total $\Delta V$ required:**

| Manoeuvre | $\Delta V$ (m/s) |
|-----------|-----------------|
| Orbit maintenance (_____ yr) | |
| Deorbit | |
| Collision avoidance margin | |
| **Total** | |

**Propulsion type selected:** _______________ &nbsp;&nbsp; $I_{sp} = $ _____ s

**Propellant mass (Tsiolkovsky):**

$m_{\text{prop}} = m_{\text{dry}} \times \left(e^{\Delta V/(I_{sp} \times g_0)} - 1\right)$

$= $ _____ $\times \left(e^{\ \ \ /(\ \ \ \times 9.81)} - 1\right) = $ _____ $\times \left(e^{\ \ \ } - 1\right) = $ _____ $\times$ _____ $= $ _____ kg

_____________________________________________________________________

_____________________________________________________________________

**System dry mass (thruster + tank + feed):** _____ kg

**Total propulsion system mass:** _____ kg (propellant + dry)

**Fraction of total spacecraft mass:** _____ %

---

## Part D: Equipment Selection Log

Using SpaceCDF's Equipment Browser, select components for each category:

| Category | Component Selected | Manufacturer | Mass (kg) | Power (W) | Cost (kEUR) | Qty | Total Mass |
|----------|-------------------|-------------|-----------|-----------|-------------|-----|-----------|
| EPS Board | | | | | | 1 | |
| Battery | | | | | | 1 | |
| Solar Panels | | | | | | | |
| OBC | | | | | | 1 | |
| Reaction Wheel | | | | | | x | |
| Magnetorquer | | | | | | x | |
| Star Tracker | | | | | | | |
| Sun Sensor | | | | | | x | |
| Transponder | | | | | | 1 | |
| Antenna | | | | | | | |
| Payload | | | | | | 1 | |
| Structure | | | | | | 1 | |
| Harness | | | | | | 1 | |
| Propulsion | | | | | | | |
| **TOTAL** | | | **_____** | | **_____** | | |

**Parametric estimate (from Session 2.4):** _____ kg

**Equipment-based total:** _____ kg

**Difference:** _____ kg ( _____ %)

**Any incompatibilities detected?** (RF band mismatch, voltage mismatch, interface conflict)

_____________________________________________________________________

_____________________________________________________________________

---

## Part E: Component Trade Study

**Subsystem traded:** _____________ &nbsp;&nbsp; **Options compared:** 3

| Criterion | Weight | Option A: _________ | Score | Option B: _________ | Score | Option C: _________ | Score |
|-----------|--------|---------------------|-------|---------------------|-------|---------------------|-------|
| Mass | 0.20 | | | | | | |
| Power | 0.15 | | | | | | |
| Cost | 0.20 | | | | | | |
| TRL | 0.15 | | | | | | |
| Heritage | 0.15 | | | | | | |
| Performance | 0.15 | | | | | | |
| **Weighted** | **1.00** | | **_____** | | **_____** | | **_____** |

**Winner:** _____________ &nbsp;&nbsp; **Score:** _____

**Rationale (beyond the numbers):**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Part F: Final Budget Health Check

After equipment selection, record final budget status:

| Budget | Value | Margin | Status |
|--------|-------|--------|--------|
| Mass (wet vs allocation) | _____ / _____ kg | _____ % | G / A / R |
| Power (worst mode vs SA) | _____ / _____ W | _____ % | G / A / R |
| Link margin | _____ dB | >= 3 dB? | G / A / R |
| Cost vs ceiling | _____ / _____ MEUR | _____ % | G / A / R |
| Pointing (RSS vs req) | _____ / _____ deg | _____ % | G / A / R |
| Data (DL vs gen) | _____ / _____ GB/day | _____ % | G / A / R |

**Any budget that does not close?** _______________________________________________

**Proposed fix:** _______________________________________________

_____________________________________________________________________

---

## Decision Justification

Explain WHY you made each key structural and propulsion decision.

**Form factor selection rationale (why this size and not larger/smaller?):**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Propulsion decision rationale (if no propulsion: why not? if propulsion: why this type?):**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Equipment selection rationale (which component trade-offs were hardest? what compromises did you make?):**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Notes & Reflections

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________
