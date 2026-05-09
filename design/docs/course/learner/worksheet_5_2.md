# Worksheet 5.2: Mission Operations Concepts

**Name:** ___________________________  **Date:** ___________  **Team:** ___________

**Mission Name:** ___________________________

---

## Part A: Operational Modes

Define all operational modes for your spacecraft. Use the SpaceCDF ConOps Editor to enter these.

| Mode | Description | Power (W) | Data Rate | Entry Condition | Exit Condition |
|------|------------|:---------:|:---------:|----------------|---------------|
| Safe | | | | | |
| Detumble | | | | | |
| Standby | | | | | |
| Science | | | | | |
| Downlink | | | | | |
| Eclipse | | | | | |
| Manoeuvre | | | | | |
| | | | | | |

**Verify:** Does the power budget close in every mode?

| Mode | Power Consumption (W) | Power Available (W) | Margin (W) | Closes? |
|------|:---------------------:|:-------------------:|:----------:|:-------:|
| Safe | | | | Y / N |
| Detumble | | | | Y / N |
| Standby | | | | Y / N |
| Science | | | | Y / N |
| Downlink | | | | Y / N |
| Eclipse (battery only) | | | | Y / N |

---

## Part B: FDIR Rules

Define at least 5 FDIR rules for your spacecraft:

| # | Fault Description | Detection Method | Threshold | FDIR Level (0-4) | Autonomous Response | Recovery Procedure |
|:-:|------------------|-----------------|-----------|:-:|:-:|:-:|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |

**Can Safe Mode sustain the spacecraft indefinitely (power + thermal)?** Y / N

If not, what is the maximum Safe Mode duration? _____ hours

**Can every autonomous FDIR action be overridden from ground?** Y / N

If not, which cannot? _______________________________________________

---

## Part C: Nominal Procedure

Write one nominal procedure for your mission (science observation or data downlink):

**Procedure ID:** _____________  **Title:** _______________________________________________

**Preconditions:**

_______________________________________________

_______________________________________________

| Step | Action | Expected Result | If Not Achieved |
|:----:|--------|----------------|----------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |

**Post-conditions:**

_______________________________________________

---

## Part D: Contingency Procedure

Write one contingency procedure (e.g., safe mode recovery, communication loss recovery):

**Procedure ID:** _____________  **Title:** _______________________________________________

**Trigger condition:**

_______________________________________________

**Severity level:** Green / Yellow / Orange / Red

| Step | Action | Expected Result | If Not Achieved | Timeout |
|:----:|--------|----------------|----------------|:-------:|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |

**Escalation:** If this procedure fails, escalate to: _______________________________________________

**Post-conditions:**

_______________________________________________

---

## Part E: Operations Staffing

Estimate the staffing requirements for each mission phase:

| Phase | Duration | Shifts/Day | Staff/Shift | Total FTE | Annual Cost (kEUR) |
|-------|----------|:----------:|:-----------:|:---------:|---------:|
| LEOP | _____ days | 3 (24/7) | | | |
| Commissioning | _____ weeks | 2 (16/7) | | | |
| Early Operations | _____ months | 1 (8/5) | | | |
| Nominal Operations | _____ years | 1 (8/5) or auto | | | |
| End of Life | _____ weeks | 1 (8/5) | | | |
| **Total** | | | | | |

---

## Part F: Anomaly Scenario

Hypothetical scenario: Your satellite enters Safe Mode during a weekend. The next ground contact is Monday morning (40 hours away). Walk through your response:

1. **What is the spacecraft doing in Safe Mode?**

   _______________________________________________

   _______________________________________________

2. **Will it survive 40 hours? (Check power and thermal)**

   _______________________________________________

   _______________________________________________

3. **What telemetry will you review first on Monday?**

   _______________________________________________

   _______________________________________________

4. **What is your recovery plan?**

   _______________________________________________

   _______________________________________________

---

## Notes & Reflections

How much autonomy should your spacecraft have? Where is the line between onboard decision-making and ground control?

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________
