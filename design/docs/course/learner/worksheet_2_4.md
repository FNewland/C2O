# Worksheet 2.4: Mission Architecture -- Segments, Interfaces, and Budgets

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** System Architecture, Interfaces, Dashboard, Budget Breakdown

---

## Key Equations Reference

> **Mass margin:** $\text{Margin}_\% = \frac{M_{\text{alloc}} - M_{\text{MEV}}}{M_{\text{alloc}}} \times 100\%$
> &nbsp;&nbsp; Green: > 20% | Amber: 10--20% | Red: < 10%
>
> **MEV:** $M_{\text{MEV}} = M_{\text{CBE}} + \text{equipment margin} + \text{system margin}$
>
> **Orbit-average power:** $P_{\text{avg}} = \sum (P_{\text{mode}} \times f_{\text{duty}})$
>
> **SA power:** $P_{\text{SA}} = P_{\text{peak}} + \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}}$
>
> **ECSS Phase A margins:** Equipment 20% + System 20% = ~44% compound

---

## Part A: Mass Budget (15 min)

Complete from your SpaceCDF design (or estimate if pre-run):

| Subsystem | CBE Mass (kg) | % of Dry | Equip. Margin (20%) | MEV (kg) |
|-----------|--------------|----------|---------------------|---------|
| Payload | | | | |
| EPS | | | | |
| AOCS | | | | |
| Comms (TTC) | | | | |
| OBC | | | | |
| Thermal | | | | |
| Structure | | | | |
| Harness | | | | |
| Propulsion | | | | |
| **Dry Total (CBE)** | | 100% | | |
| **System margin (20%)** | | | | |
| **Dry MEV** | | | | |
| Propellant | | | | |
| **Wet Mass** | | | | |
| **Launcher Allocation** | | | | |
| **Mass Margin** | | | | |
| **Mass Margin %** | | | G / A / R | |

**Show margin calculation:**

_____________________________________________________________________

_____________________________________________________________________

---

## Part B: Power Budget by Mode (15 min)

| Subsystem | Safe (W) | Idle (W) | Imaging (W) | Downlink (W) | Eclipse (W) |
|-----------|---------|---------|-------------|-------------|-------------|
| OBC | | | | | |
| AOCS | | | | | |
| Payload | | | | | |
| Comms (TX) | | | | | |
| Thermal | | | | | |
| **Total** | | | | | |
| **Duty cycle (%)** | | | | | |

**Orbit-average power calculation (show working):**

$P_{\text{avg}} = $ _____ $\times$ _____ $+$ _____ $\times$ _____ $+$ _____ $\times$ _____ $+$ _____ $\times$ _____ $= $ _____ W

_____________________________________________________________________

**SA power required:**

$P_{\text{recharge}} = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}} = \frac{\ \ \ \ \times \ \ \ \ }{\ \ \ \ \times 0.9} = $ _____ W

$P_{\text{SA,EOL}} = P_{\text{peak}} + P_{\text{recharge}} = $ _____ $+$ _____ $= $ _____ W

$P_{\text{SA,BOL}} = P_{\text{SA,EOL}} / (1 - 0.025)^n = $ _____ $/ $ _____ $= $ _____ W

_____________________________________________________________________

---

## Part C: Interface Identification (15 min)

List the 5 most critical interfaces in your design:

| # | Subsystem A | Subsystem B | Interface Types (M/E/T/D/R/O) | Key Concern |
|---|-------------|-------------|-------------------------------|-------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Write 2 formal interface requirements** for your most critical pair:

Interface: ____________ <-> ____________

**IR-001:** _______________________________________________

_____________________________________________________________________

**IR-002:** _______________________________________________

_____________________________________________________________________

Verification method for IR-001: _____ &nbsp; IR-002: _____

---

## Part D: Conflict Resolution (10 min)

From the SpaceCDF Interface Matrix, identify one conflict (red border):

**Conflict description:** _______________________________________________

_____________________________________________________________________

**Severity:** Critical / Major / Minor

**Resolution options considered:**

| # | Option | Pros | Cons |
|---|--------|------|------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Selected resolution:** _______________________________________________

**Rationale:** _______________________________________________

---

## Part E: Budget Health Check (10 min)

From the SpaceCDF Dashboard, record all KPIs:

| Budget | Value | Margin | Status (G/A/R) |
|--------|-------|--------|----------------|
| Mass | _____ kg wet vs _____ kg alloc | _____% | |
| Power (worst mode) | _____ W vs _____ W SA | _____% | |
| Link | _____ dB margin | >= 3 dB? | |
| Cost | _____ MEUR vs _____ ceiling | _____% | |
| Pointing | _____ deg vs _____ deg req | _____% | |

**Which budget is tightest?** _______________________________________________

**What single design change would improve it?** ____________________________

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
