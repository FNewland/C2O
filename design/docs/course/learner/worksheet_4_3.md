# Worksheet 4.3: Risk, Interfaces & FMECA

**Name:** ___________________________  **Date:** ___________  **Team:** ___________

**Mission Name:** ___________________________

---

## Part A: Risk Register

Identify at least 5 technical risks for your mission design. Score each on the 5x5 matrix.

**Scoring reminder:** L x C = Score. Low (1-4), Medium (5-9), High (10-15), Critical (16-25).

| # | Risk Description | L (1-5) | C (1-5) | Score | Category (L/M/H/C) | Mitigation Strategy | Owner (Position) | Post-Mitigation Score |
|:-:|-----------------|:-:|:-:|:-:|:-:|-------------------|:-:|:-:|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |
| 6 | | | | | | | | |
| 7 | | | | | | | | |

**How many risks are High or Critical (before mitigation)?** _____

**How many remain High or Critical after mitigation?** _____

---

## Part B: 5x5 Risk Matrix Plot

Plot your risks on the matrix below. Write the risk number in the appropriate cell.

```
             Consequence ->
             1       2       3       4       5
  L   5 |       |       |       |       |       |
  i   4 |       |       |       |       |       |
  k   3 |       |       |       |       |       |
  e   2 |       |       |       |       |       |
  l   1 |       |       |       |       |       |
```

---

## Part C: N-Squared (N^2) Interface Matrix

Fill in the interface matrix for your mission's subsystems. Use abbreviations:
- **P** = Power (electrical)
- **D** = Data (I2C, SPI, UART, CAN, RS-422)
- **R** = RF (coaxial)
- **M** = Mechanical (mounting, alignment)
- **T** = Thermal (conductive/radiative)

|  | EPS | OBC | AOCS | TTC | Payload | Structure |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **EPS** | --- | | | | | |
| **OBC** | | --- | | | | |
| **AOCS** | | | --- | | | |
| **TTC** | | | | --- | | |
| **Payload** | | | | | --- | |
| **Structure** | | | | | | --- |

**Total number of interfaces identified:** _____

**Interface conflicts detected:** (describe at least 2)

1. Conflict: _______________________________________________

   Resolution: _______________________________________________

2. Conflict: _______________________________________________

   Resolution: _______________________________________________

---

## Part D: FMECA Table

Complete for 4 critical components:

| Component | Function | Failure Mode | Cause | Local Effect | System Effect | Severity (1-5) | Detection Method | Compensating Provision |
|-----------|----------|-------------|-------|-------------|---------------|:-:|:-:|:-:|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |

---

## Part E: Single-Point Failure Analysis

List all single-point failures in your design:

| # | Component | Failure Mode | Effect on Mission | SPF? | Acceptable? | Mitigation (if not acceptable) |
|:-:|-----------|-------------|-------------------|:-:|:-:|:-:|
| 1 | | | | Y/N | Y/N | |
| 2 | | | | Y/N | Y/N | |
| 3 | | | | Y/N | Y/N | |
| 4 | | | | Y/N | Y/N | |
| 5 | | | | Y/N | Y/N | |

**Total SPFs identified:** _____    **Accepted:** _____    **Mitigated:** _____

---

## Part F: Reliability Calculation

Calculate the series reliability for your mission's critical chain (components that must all work for mission success):

| Component | Individual Reliability (R_i) | Mission Duration Used |
|-----------|:--:|:-:|
| | | |
| | | |
| | | |
| | | |
| | | |

**R_series = R_1 x R_2 x ... x R_n = _____________________________**

**R_series = ___________**

If you added redundancy to one component (e.g., dual deployment mechanism), recalculate:

**R_redundant = 1 - (1 - R)^2 = 1 - (1 - _____)^2 = _____**

**New R_series (with redundancy) = _____**

**Improvement: from _____ to _____ (+ _____ percentage points)**

---

## Part G: Risk Discussion

What is the highest-risk item in your design? What would it take (cost, mass, schedule) to bring the risk to an acceptable level?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

---

## Notes & Reflections

Which single-point failure concerns you the most? Would you accept it, or is mitigation essential?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________
