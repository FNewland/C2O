# Worksheet 3.3: Power, AOCS, & Thermal

**Name:** ___________________________  **Date:** ___________

---

## Part A: Solar Array Sizing (show calculations)

1. Peak sunlight power demand: P_peak = _____ W (from mode: _________)
2. Eclipse power demand: P_eclipse = _____ W
3. Eclipse time: t_ecl = _____ min; Sunlight time: t_sun = _____ min
4. Recharge power: P_rech = (P_ecl × t_ecl)/(t_sun × 0.9) = _____ W
5. **SA EOL required:** P_SA = P_peak + P_rech = _____ W
6. EOL degradation factor (3yr, 2.5%/yr): (1-0.025)^3 = _____
7. **SA BOL required:** P_SA_BOL = P_SA_EOL / factor = _____ W
8. SA area: A = P_BOL / (0.295 × 1361 × 0.85) = _____ m^2
9. SA type needed: Body-mounted / Single deploy / Dual deploy

---

## Part B: Battery Sizing

1. Eclipse energy: E = P_ecl × t_ecl/60 = _____ Wh
2. Battery capacity: C = E / (DoD × eta) = _____ / (0.3 × 0.95) = _____ Wh
3. Battery mass: m = C / 150 = _____ kg

---

## Part C: AOCS Selection

**Pointing requirement:** _____ °

**AOCS architecture selected:** (tick one)
- [ ] Passive magnetic (>5°)
- [ ] Magnetorquers only (2-5°)
- [ ] Reaction wheels + MTQ (0.1-2°)
- [ ] Fine pointing: RW + star tracker + MTQ (<0.1°)

---

## Part D: Pointing Error Budget

| Error Source | Value (°) | Value^2 |
|-------------|----------|--------|
| Sensor accuracy | | |
| Actuator resolution | | |
| Alignment knowledge | | |
| Thermal distortion | | |
| Jitter | | |
| Orbit knowledge | | |
| **RSS Total** | **=?(?) =** | |

**Requirement:** _____ °  **Margin:** _____ ° ( _____ %)

---

## Part E: Thermal Check

From SpaceCDF Dashboard, record:
- Predicted hot case temp: _____ °C
- Predicted cold case temp: _____ °C
- Component max operating: _____ °C -> Hot margin: _____ °C (need >=5°C)
- Component min operating: _____ °C -> Cold margin: _____ °C (need >=5°C)
