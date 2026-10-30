# COM-004: AOCS Actuator Checkout
**Subsystem:** AOCS
**Phase:** COMMISSIONING
**Revision:** 2.1 --- 2026-10-30 (author ruling Q16): this card now flies
straight after COM-002, BEFORE COM-003, from the LEOP COARSE_SUN hold with no
star tracker up. Nothing promotes the AOCS out of that hold without a tracker,
so the card enables the wheels and then COMMANDS NOMINAL (Step 1b); COM-003
then calibrates the gyros in this wheel-controlled NOMINAL. Revision 2.0
(2026-08c) made the ordering rule explicit: the wheels are ENABLED (Step 1)
before anything "checks them working". No card upstream reads wheel telemetry
any more; the old LEOP-002 "verify all four wheels responding" step, which ran
before the wheels were even powered, is gone.
**Approved:** Flight Operations Director

**Entry state:** COM-002 exit state --- spacecraft in the COARSE_SUN hold left
by LEOP (`aocs.mode` 0x020F = 3), wheels DISABLED (`aocs.wheels_enabled`
0x0260 = 0), star trackers and gyro units OFF, SID 2 downlinking, mission
phase 5.

## Purpose
Commission all four reaction wheels individually. Perform controlled spin-up and
spin-down tests on each wheel, verify speed control accuracy, measure wheel
temperatures, and validate momentum management (desaturation) capability using
magnetorquers.

## Prerequisites
- [ ] COM-001 and COM-002 completed. COM-003 is NOT a prerequisite: it runs
      after this card (ruling Q16)
- [ ] AOCS in the LEOP COARSE_SUN hold (`aocs.mode` 0x020F = 3, or 8 in
      eclipse). With no tracker up it will not promote itself; Step 1b
      commands NOMINAL
- [ ] Body rates < 0.5 deg/s per axis. The magnetorquer-only hold hunts at
      0.1-0.4 deg/s; the wheels settle it
- [ ] `eps.pl_aocs_wheels` (0x0117) == 1 — the suite power line is ON (LEOP-007).
      The wheels themselves are still DISABLED at this point; Step 1 enables
      them, and only THEN does any step read or exercise wheel telemetry.
- [ ] `eps.bat_soc` (0x0101) > 65%
- [ ] Bidirectional S-band link active
- [ ] Minimum 20 minutes of ground station pass remaining

## Procedure Steps

### Step 1 — Enable the Four Reaction Wheels
**Action:** The reaction wheels come out of the bootloader DISABLED and stay that way until the wheel-enable function below is commanded, once per wheel. Powering the `aocs_wheels` EPS line energises the drive electronics but does NOT enable the wheels — that separation is deliberate, so a power-line switch can never silently hand attitude authority back to the control loop.
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=0)` (Service 8, Subtype 1, func_id 3)
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=1)` (Service 8, Subtype 1, func_id 3)
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=2)` (Service 8, Subtype 1, func_id 3)
**TC:** `AOCS_ENABLE_WHEEL(wheel_idx=3)` (Service 8, Subtype 1, func_id 3)
**Verify:** `aocs.wheels_enabled` (0x0260) == 4 within 10s
**Verify:** `aocs.rw1_enabled` (0x0254) == 1 within 10s
**Verify:** `aocs.rw2_enabled` (0x0255) == 1 within 10s
**Verify:** `aocs.rw3_enabled` (0x0256) == 1 within 10s
**Verify:** `aocs.rw4_enabled` (0x0257) == 1 within 10s
**Action:** With fewer than three of the four wheels enabled the spacecraft has no three-axis actuation, and with fewer than two the on-board FDIR rule on `aocs.wheels_enabled` will safe the AOCS once the mission phase reaches NOMINAL. Do not leave this card with fewer than three wheels enabled.
**GO/NO-GO:** All four wheels report enabled

### Step 1b — Command Wheel-Controlled NOMINAL
**TC:** `AOCS_SET_MODE(mode=4)` (Service 8, Subtype 1, func_id 0) --- NOMINAL
**Note:** The simulator accepts NOMINAL without a star tracker; attitude
knowledge stays on the coarse sun/magnetometer path until COM-003 brings the
tracker into the estimator. This command also latches `aocs.commanded_mode`
(0x0297) = 4.
**Verify:** `aocs.mode` (0x020F) in {4, 8} within 300s --- 8 (ECLIPSE) is the
shadow-side handover of the same commanded state
**Verify:** `aocs.commanded_mode` (0x0297) = 4 within 10s
**GO/NO-GO:** AOCS in NOMINAL on the wheels

### Step 2 — Record Baseline Wheel Speeds
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.rw1_speed` (0x0207) reported within 10s — record value
**Verify:** `aocs.rw2_speed` (0x0208) reported within 10s — record value
**Verify:** `aocs.rw3_speed` (0x0209) reported within 10s — record value
**Verify:** `aocs.rw4_speed` (0x020A) reported within 10s — record value
**Action:** Newly-enabled wheels in NOMINAL pick up the control load at once and may show non-zero speeds. Record as baseline.
**GO/NO-GO:** All four wheels responding with valid speed readings

### Step 3 — Reaction Wheel 1 Spin-Up Test
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=0, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — bias RW1 by +2000 RPM
**Note:** `RW_SET_SPEED_BIAS` applies a bias *added to the wheel's current speed*; the Step 2 baseline is the reference for every check below. Wheel speeds (0x0207-0x020A) are READ-ONLY telemetry and cannot be commanded with `SET_PARAM`.
**Verify:** `aocs.rw1_speed` (0x0207) reaches baseline +1800 to +2200 RPM within 60s
**Action:** Monitor attitude disturbance — remaining wheels should compensate.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg within 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=0, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — swing RW1 through zero to baseline -2000 RPM
**Verify:** `aocs.rw1_speed` (0x0207) reaches baseline -2200 to -1800 RPM within 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=0, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — return RW1 to zero
**Verify:** `aocs.rw1_speed` (0x0207) returns to < 100 RPM within 60s
**GO/NO-GO:** RW1 speed control verified in both directions

### Step 4 — Reaction Wheel 2 Spin-Up Test
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=1, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — bias RW2 by +2000 RPM
**Verify:** `aocs.rw2_speed` (0x0208) reaches baseline +1800 to +2200 RPM within 60s
**Action:** Monitor attitude disturbance — remaining wheels should compensate.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg within 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=1, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — swing RW2 through zero to baseline -2000 RPM
**Verify:** `aocs.rw2_speed` (0x0208) reaches baseline -2200 to -1800 RPM within 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=1, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — return RW2 to zero
**Verify:** `aocs.rw2_speed` (0x0208) returns to < 100 RPM within 60s
**GO/NO-GO:** RW2 speed control verified in both directions

### Step 5 — Reaction Wheel 3 Spin-Up Test
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=2, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — bias RW3 by +2000 RPM
**Verify:** `aocs.rw3_speed` (0x0209) reaches baseline +1800 to +2200 RPM within 60s
**Action:** Monitor attitude disturbance — remaining wheels should compensate.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg within 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=2, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — swing RW3 through zero to baseline -2000 RPM
**Verify:** `aocs.rw3_speed` (0x0209) reaches baseline -2200 to -1800 RPM within 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=2, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — return RW3 to zero
**Verify:** `aocs.rw3_speed` (0x0209) returns to < 100 RPM within 60s
**GO/NO-GO:** RW3 speed control verified in both directions

### Step 6 — Reaction Wheel 4 Spin-Up Test
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=3, bias_rpm=2000.0)` (Service 8, Subtype 1, func_id 8) — bias RW4 by +2000 RPM
**Verify:** `aocs.rw4_speed` (0x020A) reaches baseline +1800 to +2200 RPM within 60s
**Action:** Monitor attitude disturbance — remaining wheels should compensate.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg within 60s
**TC:** `RW_SET_SPEED_BIAS(wheel_idx=3, bias_rpm=-4000.0)` (Service 8, Subtype 1, func_id 8) — swing RW4 through zero to baseline -2000 RPM
**Verify:** `aocs.rw4_speed` (0x020A) reaches baseline -2200 to -1800 RPM within 120s
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=3, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14) — return RW4 to zero
**Verify:** `aocs.rw4_speed` (0x020A) returns to < 100 RPM within 60s
**GO/NO-GO:** RW4 speed control verified in both directions

### Step 7 — Check Wheel Temperatures
**TC:** `GET_PARAM(param_id=0x0218)` (Service 20, Subtype 3) — `aocs.rw1_temp`
**TC:** `GET_PARAM(param_id=0x0219)` (Service 20, Subtype 3) — `aocs.rw2_temp`
**TC:** `GET_PARAM(param_id=0x021A)` (Service 20, Subtype 3) — `aocs.rw3_temp`
**TC:** `GET_PARAM(param_id=0x021B)` (Service 20, Subtype 3) — `aocs.rw4_temp`
**Verify:** All wheel temperatures in range [-10C, +55C] within 10s
**Note:** 0x028A-0x028D are CSS head health percentages (`aocs.css_head_health_py/my/pz/mz`),
not wheel temperatures.
**Action:** Post-test temperatures may be slightly elevated. Record for trending.
**GO/NO-GO:** All wheel temperatures within operational limits

### Step 8 — Momentum Desaturation Test
**Action:** Command desaturation to unload accumulated momentum using magnetorquers.
**TC:** `AOCS_DESATURATE` (Service 8, Subtype 1, func_id 1)
**Verify:** `aocs.rw1_speed` (0x0207) trending toward 0 RPM within 300s
**Verify:** `aocs.rw2_speed` (0x0208) trending toward 0 RPM within 300s
**Verify:** `aocs.rw3_speed` (0x0209) trending toward 0 RPM within 300s
**Verify:** `aocs.rw4_speed` (0x020A) trending toward 0 RPM within 300s
**Action:** Desaturation may take 5-10 minutes depending on momentum level and magnetic field strength. Monitor attitude stability during desaturation.
**Verify:** `aocs.att_error` (0x0217) < 5.0 deg during desaturation
**GO/NO-GO:** Desaturation effective — wheel speeds trending toward zero

### Step 9 — Compile Wheel Commissioning Report
**Action:** Record spin-up/spin-down response times, speed control accuracy, temperatures, and desaturation performance for each wheel. Compare with specification. Document any anomalies.
**GO/NO-GO:** All four reaction wheels commissioned successfully

## Off-Nominal Handling
- If any wheel fails to reach commanded speed within 90s: Reduce the commanded bias to +1000 RPM as diagnostic. If still unresponsive, check that the wheel line is powered via `GET_PARAM(param_id=0x0117)` (`eps.pl_aocs_wheels`) and its draw via `GET_PARAM(param_id=0x011F)` (`eps.line_current_7`). If power nominal but wheel unresponsive, flag as failed. AOCS can operate on three wheels.
- If wheel temperature > +55C during testing: Halt testing on that wheel. Allow 10-minute cooldown period. Re-check temperature before resuming. If temperature remains high, reduce the test bias to +1000 RPM.
- If attitude error > 10 deg during wheel test: Halt the wheel test immediately via `AOCS_RW_RAMP_DOWN(wheel_idx=255, target_rpm=0.0)` (Service 8, Subtype 1, func_id 14 — 255 = all wheels). Verify AOCS still controlling. Check if multiple wheels are loaded simultaneously (should not be). Resume testing after attitude recovers.
- If desaturation does not reduce wheel speeds: Verify magnetorquer operation via `GET_PARAM(param_id=0x025E)` (`aocs.mtq_enabled`). Check current orbit position for magnetic field strength (desaturation less effective near equator). Retry during polar passage.
- If one wheel shows significantly different response than others: Record anomaly. Possible bearing wear or drive electronics issue. Continue commissioning with remaining wheels. Schedule detailed investigation.

## Exit state
- All four wheels ENABLED and exercised, momentum unloaded (Step 8), AOCS in
  commanded NOMINAL family holding nadir on wheels
- Star trackers and gyro units still OFF (COM-003 brings them up)
- No power-line, payload or TTC state touched by this card

## Post-Conditions
- [ ] All four reaction wheels enabled — `aocs.wheels_enabled` (0x0260) == 4
- [ ] RW1 spin-up/spin-down verified in both directions
- [ ] RW2 spin-up/spin-down verified in both directions
- [ ] RW3 spin-up/spin-down verified in both directions
- [ ] RW4 spin-up/spin-down verified in both directions
- [ ] All wheel temperatures within operational limits
- [ ] Momentum desaturation via magnetorquers verified
- [ ] Wheel Commissioning Report generated

**NEXT:** COM-003 (AOCS Sensor Calibration --- gyro calibration in wheel-controlled NOMINAL)
