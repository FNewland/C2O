# CTG-009: Solar Array Degradation
**Subsystem:** EPS
**Phase:** CONTINGENCY
**Revision:** 1.0
**Approved:** Flight Operations Director

## Purpose
Respond to detected degradation in solar array power output, indicated by array current
falling below the expected value for the current illumination conditions. EOSAT-1 has six body-mounted panels and two
deployable solar wings (+/-Y) that together produce approximately 64W at optimal sun angle
(wings deployed, 0.78 m² total area). A sustained current shortfall of more than 20% from predicted values on either
array requires investigation and potential operational adjustments to maintain a positive
power budget throughout each orbit.

The spacecraft detects a degraded string (S12 yield monitor, TM(12,9) and S5 event
0x914C / 0x914D) but takes no action on it: whether the payload goes off is the
team's decision, made at Step 4 from how serious the loss is (string yield and power
balance). If the power really runs out first, the on-board bus-voltage load shed
(below 25.0 V, payload first) takes the payload off by itself; that is the safety net,
not the plan.

## Prerequisites
- [ ] EPS telemetry (SID 1) is being received at >= 0.5 Hz
- [ ] Current orbit illumination data is available — beta angle, sunlit fraction, incidence angles
- [ ] Predicted SA-A and SA-B current values for current attitude and illumination are on console (ref: EOSAT1-PWR-BUD-001)
- [ ] AOCS is in NOMINAL or COARSE_SUN with known solar array orientation
- [ ] `eps.bat_soc` (0x0101) > 25% — sufficient margin for investigation period

## Procedure Steps

### Step 1 — Quantify the Degradation
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.sa_a_current` (0x0103) — record value and compare to predicted (expected > 1.0A at optimal)
**Verify:** `eps.sa_b_current` (0x0104) — record value and compare to predicted (expected > 1.0A at optimal)
**Verify:** `eps.power_gen` (0x0107) — record total generation
**TC:** `GET_PARAM(param_id=0x014C)` (Service 20, Subtype 3) — `eps.sa_a_yield_pct`
**TC:** `GET_PARAM(param_id=0x014D)` (Service 20, Subtype 3) — `eps.sa_b_yield_pct`
**TC:** `GET_PARAM(param_id=0x014E)` (Service 20, Subtype 3) — `eps.sa_string_lit`
**Verify:** `eps.sa_a_yield_pct` (0x014C) and `eps.sa_b_yield_pct` (0x014D) — the on-board yield of each string against a healthy string at the same sun geometry (valid only while `eps.sa_string_lit` (0x014E) has the string's bit set). Below 70 % for 30 s in sunlight the spacecraft reports it (TM(12,9) and S5 event 0x914C for A, 0x914D for B) and does nothing else: the payload is still as you left it. Check `eps.pl_payload` (0x0113): if it is already OFF, the bus-voltage load shed took it (event 0x0106) and the power situation is already serious
**Action:** Calculate percentage shortfall: (predicted - actual) / predicted x 100 for each array
**GO/NO-GO:** If shortfall > 20% on either array during confirmed sunlit phase, proceed. If < 20%, log for trend monitoring only. -> GO `STEP-2` | NO-GO `STEP-END`

### Step 2 — Compare SA-A versus SA-B Performance
**LABEL:** `STEP-2`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — sample 3 times at 30s intervals
**Action:** Compute SA-A to SA-B current ratio (nominal ratio is 0.9 to 1.1)
**Verify:** `eps.sa_a_current` (0x0103) and `eps.sa_b_current` (0x0104) — determine if degradation is on one or both arrays
**Action:** If only one array degraded, suspect localised failure (cell damage, wiring, deployment issue). If both arrays degraded proportionally, suspect attitude error or environmental factor.
**GO/NO-GO:** Degradation source identified (single array vs both) — proceed

### Step 3 — Verify Attitude Is Not the Cause
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.mode` (0x020F) = 4 (NOMINAL) or 3 (COARSE_SUN)
**Verify:** `aocs.att_error` (0x0217) < 2.0 deg — large attitude error could reduce array illumination
**Action:** If attitude error > 5 deg, execute CTG-002 first, then reassess array performance
**GO/NO-GO:** Attitude confirmed nominal — degradation is intrinsic to array hardware or environment

### Step 4 — Decide: Shed the Payload or Continue
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27)
**Verify:** `eps.power_gen` (0x0107) — actual generation
**Verify:** `eps.power_cons` (0x0106) — current consumption
**Action:** Compute power margin = generation - consumption (must be > 0W averaged over orbit)
**Action:** Compute worst-case eclipse energy deficit using degraded generation values
**Verify:** `eps.bat_soc` (0x0101) — project minimum SoC at end of next eclipse
**Action:** Judge the severity from the yield (Step 1) and this power balance. One string below 70 % with a positive orbit-average margin is a trend to watch; a string near 0 %, both strings low, or a negative margin with the payload on is serious. The payload is the load that decides it: continue only if the budget closes with the payload in its planned mode
**Action:** The Flight Director announces the decision on the loop ("PAYLOAD SHED" or "CONTINUE, MONITORING") and it is logged with the yield and the projected SoC
**GO/NO-GO:** If projected minimum SoC > 25% and the orbit-average margin is positive, continue nominal ops with monitoring. If < 25% or the margin is negative, shed the payload at Step 5. -> GO `STEP-7` | NO-GO `STEP-5`

### Step 5 — Reduce Loads to Match Degraded Power Budget
**LABEL:** `STEP-5`
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1) — reduce from IMAGING to STANDBY
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) within 10s
**Verify:** `eps.power_cons` (0x0106) decreases by >= 12W
**GO/NO-GO:** Margin still insufficient after STANDBY -> GO `STEP-5B` | NO-GO `STEP-6`
**LABEL:** `STEP-5B`
**Note:** Only if the margin is still insufficient after STANDBY.
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1, func_id 26) — full payload shutdown
**Note:** The thruster catbed heater is `HEATER_THRUSTER` (func 42, argument
`on` only — there is no `circuit` argument on this command). Send it only if
no manoeuvre is planned; `HEATER_CONTROL` is an alias of HEATER_BATTERY and
would have switched the wrong circuit.
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1, func_id 42) — catbed heater off
**Verify:** `eps.power_cons` (0x0106) — recompute margin with reduced loads
**GO/NO-GO:** Power margin is positive with at least 3W reserve — proceed

### Step 6 — Optimise Attitude for Solar Array Illumination
**LABEL:** `STEP-6`
**TC:** `AOCS_SET_MODE(mode=3)` (Service 8, Subtype 1, func_id 0) — COARSE_SUN for sun-optimal orientation
**Verify:** `aocs.mode` (0x020F) = 3 within 15s
**Verify:** `eps.sa_a_current` (0x0103) and `eps.sa_b_current` (0x0104) — observe improvement in current
**Verify:** `eps.power_gen` (0x0107) increases relative to NOMINAL values
**GO/NO-GO:** Generation improved sufficiently to maintain positive margin — proceed to monitoring

### Step 7 — Establish Long-Term Monitoring Plan
**LABEL:** `STEP-7`
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — baseline measurement
**Action:** Record SA-A current, SA-B current, power generation, and SoC as new baseline
**Action:** Schedule daily trend comparison for array current vs prediction over next 7 days
**Action:** Coordinate with mission planning to adjust imaging schedule based on degraded power budget
**Action:** If single-wing failure confirmed, assess operations on reduced solar area (~42W peak with one wing, ~32W body-only). Check wing deployment status:
**TC:** `GET_PARAM(param_id=0x0144)` (Service 20, Subtype 3) — `eps.wing_status`
(0x0144 is now in HK SID 1 as well, so an enabled SID 1 already carries it).
**GO/NO-GO:** Monitoring plan established and operations plan adjusted — recovery complete

## Off-Nominal Handling
**LABEL:** `STEP-END`
- If both arrays drop below 0.2A during sunlit phase: Suspect total array failure or severe attitude error — execute CTG-005 (EPS Safe Mode Recovery) immediately
- If SoC drops below 20% during this procedure: Interrupt and execute CTG-005
- If attitude error is the root cause: Execute CTG-002, then re-enter this procedure at Step 1
- If degradation is progressive (> 5% per day): Accelerate mission data downlink priorities, plan reduced-power mission profile

## Post-Conditions
- [ ] Array degradation quantified (percentage shortfall per array documented)
- [ ] Power budget recalculated with degraded values and confirmed positive
- [ ] Operations plan adjusted (imaging frequency, heater usage, AOCS mode)
- [ ] Trend monitoring initiated with daily reporting to Mission Director
- [ ] Root cause hypothesis documented (cell degradation, deployment, wiring, radiation)
