# Worksheet 3.1: Power System and Thermal Control Design

| | |
|---|---|
| **Name:** | _______________________________________ |
| **Date:** | _______________________________________ |
| **Team / Mission:** | _______________________________________ |
| **Role / Position:** | _______________________________________ |

**SpaceCDF Tabs:** Dashboard (Power KPI), Engineering Budgets, Timing Budget, Parametric

---

## Quick Reference: Power and Thermal Concepts

### What is a Solar Array?

A solar array converts sunlight into electrical power using photovoltaic cells. In space, the solar flux (called the solar constant) is $S = 1361$ W/m$^2$ at 1 AU from the Sun -- about 40% more intense than at Earth's surface because there is no atmosphere absorbing part of the spectrum.

**Solar cell types and efficiency (AM0, space spectrum):**

| Cell Technology | Typical Efficiency | Degradation Rate | Cost Relative | Notes |
|----------------|-------------------|------------------|--------------|-------|
| Silicon (Si) | 16--18% | ~3.5%/yr | Low | Legacy; rarely used in new missions |
| Gallium Arsenide (GaAs) single-junction | 22--24% | ~2.5%/yr | Medium | Good radiation tolerance |
| Triple-junction GaAs (InGaP/GaAs/Ge) | 28--30% | ~2.5%/yr | High | CubeSat standard today |
| Multi-junction (4J, 5J) | 32--35% | ~2%/yr | Very high | Emerging; used on flagship missions |

For CubeSat design, assume **triple-junction GaAs cells at 29.5% efficiency** ($\eta = 0.295$). Cells are mounted on panels with a **packing factor** of $f_{\text{pack}} = 0.80$--$0.85$, meaning 80--85% of the panel area is actually covered by active cells (the rest is gaps, wiring, and structural margin).

**Degradation:** Solar cells lose efficiency over time due to radiation damage (proton and electron bombardment in the Van Allen belts). At a rate of $\delta = 2.5\%$ per year, after $n$ years the remaining efficiency is $(1 - 0.025)^n$. This means a 3-year mission loses about 7.3% of its beginning-of-life (BOL) power, and a 5-year mission loses about 11.9%.

### Body-Mounted vs Deployable Solar Arrays

| Configuration | Advantages | Disadvantages | Typical Power |
|--------------|-----------|---------------|---------------|
| **Body-mounted** | No moving parts, no deployment risk, no stowed volume penalty | Limited area (only the sunlit faces), power varies with attitude | 1U: ~2 W, 3U: ~7 W, 6U: ~12 W |
| **Single deployable** | More area, moderate complexity | One mechanism, partially blocks FOV | 1U: ~4 W, 3U: ~15 W, 6U: ~30 W |
| **Dual deployable** | Maximum area for the form factor | Two mechanisms, larger stowed volume, deployment risk | 3U: ~25 W, 6U: ~48 W |

**Rule of thumb:** If your total power demand (including battery recharge) exceeds what body-mounted panels can provide, you need deployable arrays. Compare your $P_{\text{SA,BOL}}$ to the reference power values above.

### How Batteries Work in Space

Batteries store electrical energy to power the spacecraft during eclipse (when the satellite is in Earth's shadow and receives no sunlight). In LEO, eclipses occur every orbit -- typically 30--36 minutes out of a ~95-minute orbit period.

**Key battery parameters:**

- **Depth of Discharge (DOD):** The fraction of total battery capacity used each cycle. Lower DOD dramatically extends cycle life but requires a larger (heavier) battery.
- **Cycle life:** The number of charge/discharge cycles before the battery degrades below 80% of its original capacity.
- **Specific energy:** Energy stored per unit mass (Wh/kg). For space-grade Li-ion 18650 cells: 150--200 Wh/kg.

| DOD | Typical Cycle Life (Li-ion 18650) | Suitable Mission Duration |
|-----|----------------------------------|--------------------------|
| 80% | ~500 cycles | Short missions (< 1 month) |
| 50% | ~2,000 cycles | Medium missions (< 6 months) |
| 30% | ~10,000 cycles | Multi-year LEO missions |
| 20% | ~30,000 cycles | Long-life LEO (> 5 years) |

**Design guidance:** For a multi-year LEO mission (15 orbits/day), use DOD = 30%. For a 6-month technology demonstration, DOD = 50% is acceptable.

### What Does the EPS Do?

The Electrical Power System (EPS) is the spacecraft's power utility. A typical CubeSat EPS board (e.g., GomSpace P31u) includes:

- **MPPT (Maximum Power Point Tracking):** A DC-DC converter that continuously adjusts the operating voltage of the solar array to extract maximum power. Efficiency: 90--95%.
- **Battery charge controller:** Manages battery charging with voltage and current limits to protect battery life.
- **Regulated voltage rails:** Provides fixed voltages (typically 3.3 V, 5 V, and unregulated battery voltage) to all subsystems.
- **Switched outputs:** Allows the OBC to turn subsystems on/off for power management and safe mode.
- **Overcurrent protection:** Protects against short circuits in any subsystem.

### Thermal Control Basics

In space, there is no air for convection. Heat transfer occurs only by **radiation** and **conduction**. A spacecraft reaches thermal equilibrium when absorbed heat (solar flux, Earth albedo, Earth IR, internal electronics waste heat) equals radiated heat (to deep space at ~3 K).

**ECSS thermal margins (ECSS-E-ST-31C):** Operating $\pm$5 degC, Acceptance $\pm$10 degC, Qualification $\pm$15 degC. If the predicted temperature of any component is within 5 degC of its operating limit, you must add thermal control (heater, coating change, or radiator).

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

## Worked Example: UniSat-1 (1U) Power and Thermal

### Solar Array Sizing (Body-Mounted)

UniSat-1 uses body-mounted solar cells on 5 faces (the 6th face is the deployment interface). ISS orbit: 400 km altitude, 92.4 min period, 56 min sunlight, 36 min eclipse.

**Given:** $P_{\text{peak,sunlight}} = 1.2$ W, $P_{\text{eclipse}} = 0.5$ W (OBC only), mission lifetime = 6 months.

**Step 1 -- Effective illuminated area (passive magnetic attitude, ~1.5 faces average):**

$A_{\text{eff}} = 1.5 \times (0.10 \times 0.10) = 0.015$ m$^2$

**Step 2 -- SA BOL power:**

$P_{\text{SA,BOL}} = \eta \times S \times A_{\text{eff}} \times f_{\text{pack}} = 0.295 \times 1361 \times 0.015 \times 0.80 = 4.82$ W (illuminated peak)

**Step 3 -- Orbit-average power available:**

$P_{\text{avg}} = P_{\text{SA,BOL}} \times \frac{t_{\text{sun}}}{T_{\text{orbit}}} \times \eta_{\text{EPS}} = 4.82 \times \frac{56}{92.4} \times 0.85 = 2.48$ W

**Step 4 -- After 6-month degradation:**

$(1 - 0.025)^{0.5} = 0.987$, so $P_{\text{avg,EOL}} = 2.48 \times 0.987 = 2.45$ W

**Step 5 -- Power demand:** $P_{\text{avg,demand}} = 0.68$ W. Margin = $2.45 - 0.68 = 1.77$ W (72%). **Comfortable.**

### Battery Sizing

**Given:** $P_{\text{ecl}} = 0.5$ W, $t_{\text{ecl}} = 36$ min $= 0.60$ h, $DOD = 0.50$ (acceptable for 6-month mission), $\eta = 0.95$.

$C_{\text{bat}} = \frac{0.5 \times 0.60}{0.50 \times 0.95} = \frac{0.30}{0.475} = 0.63$ Wh

Specify minimum **10 Wh** (standard GomSpace NanoPower P31u battery). Actual DOD per eclipse = 0.63/10 = 6.3%. Cycle count: 6 months at 15 orbits/day = 2,740 eclipses. At 6.3% actual DOD, battery life is not a concern. **Pass.**

### Thermal Check (Passive Only)

UniSat-1 uses no heaters or MLI. At 400 km, strong Earth IR (~240 W/m$^2$) provides a warm floor. With COTS electronics rated -20 to +60 degC and a 400 km orbit, the thermal environment stays within approximately -10 to +45 degC for a 1U with aluminium/anodised surfaces. A simplified cold-case equilibrium calculation gives a very cold steady-state temperature, but the thermal mass of a 1 kg CubeSat limits actual cooling during 36-minute eclipses. **No heaters required for a 6-month mission at 400 km.**

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

## Decision Justification

Explain WHY you chose each element of your power and thermal design. Consider the alternatives you rejected and the trade-offs involved.

**Solar array configuration choice and rationale:**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Battery sizing rationale (why this DOD? why this capacity margin?):**

_____________________________________________________________________

_____________________________________________________________________

_____________________________________________________________________

**Thermal control approach (passive only? heaters? coatings?):**

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
