# Worksheet 3.4: Structure, Propulsion, and Equipment Selection

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Equipment Browser, Dashboard, Trade Studies, Budget Breakdown

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

## Part A: CDS Compliance Check (10 min)

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

## Part B: Structural Margin Calculation (10 min)

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

## Part C: Propulsion Decision (15 min)

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

## Part D: Equipment Selection Log (25 min)

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

## Part E: Component Trade Study (15 min)

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

## Part F: Final Budget Health Check (10 min)

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

## Notes & Reflections

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________
