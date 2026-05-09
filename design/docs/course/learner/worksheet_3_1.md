# Worksheet 3.1: Power System and Thermal Control Design

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Dashboard (Power KPI), Engineering Budgets, Timing Budget, Parametric

---

## Key Equations Reference

> **SA EOL power:** $P_{\text{SA,EOL}} = P_{\text{peak}} + \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}}$
>
> **SA BOL power:** $P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{(1 - \delta)^n}$ &nbsp;&nbsp; ($\delta = 0.025$/yr for GaAs)
>
> **SA area:** $A = \frac{P_{\text{BOL}}}{\eta_{\text{cell}} \times S \times \cos\theta \times f_{\text{pack}}}$ &nbsp;&nbsp; ($\eta = 0.295$, $S = 1361$ W/m$^2$, $f_{\text{pack}} = 0.85$)
>
> **Battery capacity:** $C = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{DOD \times \eta_{\text{discharge}}}$ &nbsp;&nbsp; ($DOD = 0.30$, $\eta = 0.95$)
>
> **Thermal equilibrium:** $T = \left(\frac{Q_{\text{abs}} + Q_{\text{int}}}{\varepsilon \sigma A_{\text{rad}}}\right)^{1/4}$ &nbsp;&nbsp; ($\sigma = 5.67 \times 10^{-8}$ W/m$^2$/K$^4$)
>
> **ECSS thermal margins:** Operating +/-5 degC, Acceptance +/-10 degC, Qualification +/-15 degC

---

## Part A: Solar Array Sizing (20 min)

Show all calculations step by step.

**1. Peak sunlight power demand:** $P_{\text{peak}} = $ _____ W (from mode: _____________)

**2. Eclipse power demand:** $P_{\text{ecl}} = $ _____ W

**3. Eclipse and sunlight times (from Worksheet 2.3):**

$t_{\text{ecl}} = $ _____ min &nbsp;&nbsp;&nbsp; $t_{\text{sun}} = $ _____ min

**4. Recharge power:**

$P_{\text{recharge}} = \frac{P_{\text{ecl}} \times t_{\text{ecl}}}{t_{\text{sun}} \times \eta_{\text{charge}}} = \frac{\ \ \ \ \ \times \ \ \ \ \ }{\ \ \ \ \ \times 0.9} = $ _____ W

_____________________________________________________________________

**5. SA EOL required:**

$P_{\text{SA,EOL}} = P_{\text{peak}} + P_{\text{recharge}} = $ _____ $+$ _____ $= $ _____ W

**6. EOL degradation factor** (mission lifetime = _____ years, $\delta = 0.025$/yr):

$(1 - 0.025)^{\ \ \ } = $ _____

**7. SA BOL required:**

$P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{(1-\delta)^n} = \frac{\ \ \ \ \ }{\ \ \ \ \ } = $ _____ W

_____________________________________________________________________

**8. SA area:**

$A = \frac{P_{\text{BOL}}}{0.295 \times 1361 \times \cos(\ \ \ ) \times 0.85} = \frac{\ \ \ \ \ }{\ \ \ \ \ } = $ _____ m$^2$

_____________________________________________________________________

**9. SA type needed** (compare to CubeSat reference values):

- [ ] Body-mounted only (1U: ~2 W, 3U: ~7 W, 6U: ~12 W)
- [ ] Single deployable (1U: ~4 W, 3U: ~15 W, 6U: ~30 W)
- [ ] Dual deployable (3U: ~25 W, 6U: ~48 W)

**10. SA mass:**

$m_{\text{SA}} = A \times \sigma = $ _____ $\times$ _____ $= $ _____ kg

(body-mounted: $\sigma = 2.5$ kg/m$^2$; deployable: $\sigma = 1.5$ kg/m$^2$)

---

## Part B: Battery Sizing (10 min)

Show all calculations:

**1. Eclipse energy:**

$E = P_{\text{ecl}} \times \frac{t_{\text{ecl}}}{60} = $ _____ $\times$ _____ $= $ _____ Wh

**2. Battery capacity required:**

$C = \frac{E}{DOD \times \eta} = \frac{\ \ \ \ \ }{0.30 \times 0.95} = \frac{\ \ \ \ \ }{0.285} = $ _____ Wh

**3. With 20% margin:** $C_{\text{spec}} = $ _____ $\times 1.2 = $ _____ Wh

_____________________________________________________________________

**4. Battery mass:**

$m_{\text{bat}} = \frac{C_{\text{spec}}}{E_{\text{specific}}} = \frac{\ \ \ \ \ }{150} = $ _____ kg

**5. Cycle life check:**

Number of eclipses in mission = _____ orbits/day $\times$ 365 $\times$ _____ years $= $ _____ cycles

At DOD = 30%, Li-ion provides ~10,000 cycles. Is this sufficient? Y / N

_____________________________________________________________________

---

## Part C: Thermal Analysis (15 min)

**1. Identify hot case and cold case for your orbit:**

| Parameter | Hot Case | Cold Case |
|-----------|----------|-----------|
| Solar illumination | | |
| Operational mode | | |
| Internal dissipation | | |
| Coating condition | BOL / EOL | BOL / EOL |
| Key concern | | |

**2. From SpaceCDF Dashboard, record thermal predictions:**

| Component | Min Predicted (degC) | Max Predicted (degC) | Operating Min (degC) | Operating Max (degC) |
|-----------|---------------------|---------------------|---------------------|---------------------|
| Payload / sensor | | | | |
| Battery | | | | |
| OBC | | | | |
| Transponder | | | | |

**3. Margin check (need >= 5 degC):**

| Component | Hot margin = Max_op - Max_pred | Cold margin = Min_pred - Min_op | Pass? |
|-----------|-------------------------------|--------------------------------|-------|
| | | | |
| | | | |
| | | | |
| | | | |

**4. If any margin fails, what thermal control action would you take?**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

---

## Part D: SpaceCDF Verification (15 min)

Compare your hand calculations to SpaceCDF values:

| Parameter | Hand Calculation | SpaceCDF Value | Difference |
|-----------|-----------------|---------------|------------|
| SA power required (BOL) | _____ W | _____ W | _____ W |
| Battery capacity | _____ Wh | _____ Wh | _____ Wh |
| Orbit-average power | _____ W | _____ W | _____ W |
| Eclipse duration | _____ min | _____ min | _____ min |

If there are significant differences, explain why:

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
