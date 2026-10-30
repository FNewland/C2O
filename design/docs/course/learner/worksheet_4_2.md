# Worksheet 4.2: Verification & Validation Planning

**Name:** ___________________________  **Date:** ___________  **Team:** ___________

**Mission Name:** ___________________________

---

## Part A: IADT Method Assignment

For 10 key requirements from your SpaceCDF V&V Matrix, assign the verification method and justify:

| # | Req ID | Requirement Text (abbreviated) | Method (I/A/D/T) | Phase (B/C/D) | Level (Unit/Sub/Sys) | Justification |
|---|--------|-------------------------------|:-:|:-:|:-:|--------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |

**Summary count:** Analysis: ___ / Test: ___ / Demonstration: ___ / Inspection: ___

---

## Part B: Dual-Method Requirements

Identify 3 requirements that need BOTH analysis (early confidence) AND test (final proof):

| Requirement ID | Requirement Text | Analysis (Phase B) | Test (Phase C/D) | Why Both Needed? |
|---------------|-----------------|-------------------|------------------|-----------------|
| | | | | |
| | | | | |
| | | | | |

---

## Part C: Environmental Test Sequence

For your selected launch vehicle, specify the complete proto-flight test sequence:

**Launch vehicle:** _______________  **PUG reference:** _______________

| Step | Test | Specification | Duration | Pass Criteria |
|:----:|------|--------------|----------|--------------|
| 1 | Initial functional test | Full performance baseline | _____ hr | All parameters nominal |
| 2 | Sine vibration | _____ g, _____ - _____ Hz | _____ min/axis x 3 | No resonance shift > 5% |
| 3 | Random vibration | _____ gRMS overall | _____ min/axis x 3 | No structural damage |
| 4 | Post-vibe functional test | Same as step 1 | _____ hr | Compare to baseline |
| 5 | Thermal vacuum -- hot | + _____ C (predicted max + 10 C) | _____ cycles | Functional at hot extreme |
| 6 | Thermal vacuum -- cold | - _____ C (predicted min - 10 C) | _____ cycles | Functional at cold extreme |
| 7 | Post-TVAC functional test | Same as step 1 | _____ hr | Compare to baseline |
| 8 | EMC test | Required? Y / N | _____ day | No interference |
| 9 | Mass measurement | Calibrated scale (+/- 0.01 kg) | 30 min | M <= _____ kg |
| 10 | Deployer fit check | _____ deployer | 2 hr | Fits; slides freely |

**Total test campaign duration estimate:** _____ weeks

---

## Part D: Vibration Test Profile

Record the random vibration PSD profile from your launch vehicle PUG:

| Frequency (Hz) | PSD Level (g^2/Hz) | Slope |
|:-:|:-:|:-:|
| 20 | | Start |
| 20 - _____ | | + _____ dB/oct |
| _____ - _____ | | Flat |
| _____ - 2000 | | - _____ dB/oct |
| 2000 | | End |

**Overall gRMS (calculated):** _____ gRMS

**Show your calculation:**

_______________________________________________

_______________________________________________

_______________________________________________

---

## Part E: TVAC Cycle Profile

Sketch or describe one TVAC cycle:

**Hot extreme:** + _____ C    **Cold extreme:** - _____ C

**Ramp rate:** _____ C/min    **Dwell time at extreme:** _____ hr

**Functional test at each extreme?** Y / N    **Duration of functional test:** _____ hr

**Calculate time for one cycle:**

t_cycle = _______________________________________________

= _____ hours

**Total TVAC campaign:** _____ cycles x _____ hr + _____ hr setup = _____ hr = _____ days

---

## Part F: Waiver Identification

Are there any requirements that cannot be verified by the standard method? Document potential waivers:

| Req ID | Standard Method | Proposed Alternative | Justification | Risk |
|--------|:-:|:-:|--------------|------|
| | | | | |
| | | | | |

---

## Notes & Reflections

Which environmental test do you consider most critical for your mission? Why?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________
