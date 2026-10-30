# Worksheet 1.3: International Standards for Space Systems

| | |
|---|---|
| **Name:** | __________________________________________ |
| **Date:** | __________________________________________ |
| **Team:** | __________________________________________ |
| **Session:** | 1.3 -- International Standards for Space Systems |

---

## Part A: Standard Applicability Matrix

For your team's mission concept, determine which ECSS and NASA standards apply. For each standard, decide whether it is fully applicable, partially applicable (with tailoring), or not applicable. Justify your decision.

| Standard | Branch | Applicability | Tailoring Notes / Justification |
|----------|--------|--------------|-------------------------------|
| ECSS-M-ST-10C (Project Management) | M | __________ | _____________________________________ |
| ECSS-M-ST-40C (Configuration Management) | M | __________ | _____________________________________ |
| ECSS-M-ST-80C (Risk Management) | M | __________ | _____________________________________ |
| ECSS-E-ST-10C (Systems Engineering) | E | __________ | _____________________________________ |
| ECSS-E-ST-20C (Electrical & Electronic) | E | __________ | _____________________________________ |
| ECSS-E-ST-32C (Structures) | E | __________ | _____________________________________ |
| ECSS-E-ST-40C (Software) | E | __________ | _____________________________________ |
| ECSS-E-ST-50C (Communications) | E | __________ | _____________________________________ |
| ECSS-Q-ST-10C (Product Assurance) | Q | __________ | _____________________________________ |
| ECSS-U-AS-10C (Debris Mitigation) | U | __________ | _____________________________________ |
| ISO 24113 (Debris Mitigation) | -- | __________ | _____________________________________ |
| NPR 7123.1D (SE Processes) | -- | __________ | _____________________________________ |

*Hint: A university CubeSat mission would typically invoke ECSS-E-ST-10C with heavy tailoring, ECSS-U-AS-10C fully, and might waive ECSS-Q-ST-10C (product assurance) due to cost constraints. A CSA-funded mission would typically require more complete ECSS compliance.*

**Question:** What is the minimum set of standards your mission MUST comply with regardless of mission class?

_______________________________________________

_______________________________________________

_______________________________________________

---

## Part B: CDS Rev 14 Compliance Checklist

If your mission uses a CubeSat form factor, complete this compliance checklist. If not, skip to Part C.

| CDS Requirement | Your Design Value | Compliant? | Notes |
|----------------|------------------|-----------|-------|
| Unit dimensions (100 x 100 x 113.5 mm per U) | __________ | __________ | __________ |
| Mass per U ($\leq$ 2.0 kg) | __________ | __________ | __________ |
| Total mass (for your form factor) | __________ | __________ | __________ |
| Rail material (hard-anodised Al) | __________ | __________ | __________ |
| CG within 2 cm of geometric centre | __________ | __________ | __________ |
| No protrusions beyond envelope during launch | __________ | __________ | __________ |
| RF silence for 30 min after deployment | __________ | __________ | __________ |
| Deployment switches on all deployables | __________ | __________ | __________ |
| Propulsion inhibits (3 independent, if applicable) | __________ | __________ | __________ |

*Hint: Use SpaceCDF's Compliance panel to check CDS compliance. The tool will flag non-compliant parameters automatically based on your mass and dimensions entries.*

---

## Part C: Debris Mitigation Compliance

Complete the following debris mitigation assessment for your mission orbit:

1. **Planned orbit altitude:** __________ km

2. **Estimated natural orbital lifetime** (without propulsion):

   *Use the rule of thumb: $\tau_{years} \approx \frac{h - 200}{30} \times \frac{m/A}{50}$ where $h$ is altitude (km), $m$ is mass (kg), $A$ is cross-section area (m$^2$)*

   $h$ = __________ km, $m$ = __________ kg, $A$ = __________ m$^2$

   $m/A$ = __________ kg/m$^2$

   $\tau$ = __________ years (approximate)

3. **Compliance assessment:**

   | Requirement | Limit | Your Mission | Compliant? |
   |-------------|-------|-------------|-----------|
   | IADC post-mission lifetime | $\leq$ 25 years | __________ | __________ |
   | FCC post-mission lifetime (2024+) | $\leq$ 5 years | __________ | __________ |
   | ISO 24113 disposal reliability | $\geq$ 90% | __________ | __________ |

4. **If non-compliant with the 5-year FCC rule, what options exist?**

   _______________________________________________

   _______________________________________________

   _______________________________________________

5. **Passivation plan** (list all stored energy sources and how you will deplete them at end of life):

   | Energy Source | Passivation Method |
   |-------------|-------------------|
   | Battery | __________________________________________ |
   | Pressure vessels (if any) | __________________________________________ |
   | Reaction wheels | __________________________________________ |
   | RF transmitter | __________________________________________ |
   | Other: __________ | __________________________________________ |

---

## Part D: Structural Design Margins

If your mission has preliminary structural design information, calculate the margin of safety:

*Use the formula: $MoS = \frac{\sigma_{allowable}}{FoS \times \sigma_{applied}} - 1$*

**Worked example:** For Al 7075-T6 ($\sigma_{yield}$ = 503 MPa), applied stress = 200 MPa, FoS (yield) = 1.25:

$MoS = \frac{503}{1.25 \times 200} - 1 = \frac{503}{250} - 1 = 1.012$

This is a positive margin (compliant).

**Your calculation:**

Material: __________ , $\sigma_{allowable}$ = __________ MPa

$\sigma_{applied}$ = __________ MPa, FoS = __________

$MoS$ = __________ (show work below)

_______________________________________________

_______________________________________________

---

## Part E: SpaceCDF Compliance Panel

Navigate to the Compliance panel in SpaceCDF and answer:

1. What is the debris mitigation compliance status for your mission?

   _______________________________________________

2. What orbital altitude would be needed to comply with the FCC 5-year rule WITHOUT propulsion? (Use the tool's orbital lifetime calculator)

   _______________________________________________

3. What standards has the tool automatically suggested for your mission type?

   _______________________________________________

   _______________________________________________

4. Are there any compliance flags (warnings or errors) on your current design?

   _______________________________________________

   _______________________________________________

---

## Notes & Reflections

Record key points about standards applicability, compliance challenges, and design implications for your mission:

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________
