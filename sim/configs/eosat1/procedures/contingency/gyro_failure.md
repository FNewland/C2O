# CTG-029: Gyro Failure Recovery
**Subsystem:** AOCS
**Phase:** COMMISSIONING / NOMINAL
**Revision:** 1.0 --- new card (author ruling Q22 as amended, 2026-10-30). It
replaces the ops book's temporary CTG-B01 "IMU / Gyro Anomaly" and is built on
what the simulator models: a persistent rate bias on one or all gyro channels
(failure `gyro_bias`), a gyro unit switched off (S2 devices 0x0206-0x0208), and
rate saturation.
**Approved:** Flight Operations Director

**Entry state:** any of
- event `GYRO_BIAS_HIGH` (0x020B) --- the bias still present at the gyro output
  exceeds 0.05 deg/s (`aocs.gyro_bias_resid` 0x02D2);
- `aocs.gyro_units_mask` (0x02D1) != 7 --- a gyro unit is off;
- `aocs.gyro_saturated` (0x0295) = 1 --- a channel is at its range limit;
- the attitude estimate walks away (`aocs.att_error` 0x0217 growing) while the
  star tracker is out of the loop.

## Purpose
Identify the affected gyro channel, restore a bias-free rate reference with the
on-board bias calibration, and, if the channel cannot be recovered, isolate it
and continue attitude determination on the remaining sensors.

**What the simulator models.** EOSAT-1 carries three single-axis gyros, one per
body axis, and **no redundant unit**: S2 devices `S2_AOCS_GYROSCOPE_0/1/2`
(device ids 0x0206, 0x0207, 0x0208 = 518, 519, 520). There is no IMU power line
and nothing to switch to.
- An injected `gyro_bias` fault is a **persistent** hardware offset on one axis or
  on all three. It does not heal with time. The on-board calibration
  (`AOCS_GYRO_CALIBRATION`, func_id 13) compensates it in the measurement chain; it
  does not repair the unit.
- A unit switched off is a **dead channel**: it reports zero rate and the attitude
  filter stops trusting that axis.
- A channel above its measurement range clips, and `aocs.gyro_saturated` (0x0295)
  is set until the rate falls back inside the range.

The three bias numbers are different quantities. The healthy bias instability is
about 3e-5 deg/s (0.1 deg/h). Event 0x020B fires at 0.05 deg/s of residual bias.
The S12 limit on `aocs.gyro_bias_x/y/z` (0x0270-0x0272) is +/-0.5 deg/s. This card
acts on the 0.05 deg/s event, the earliest actionable signal.

## Prerequisites
- [ ] Bidirectional S-band link active, at least 15 minutes of pass remaining
      (the calibration arc is 300 s)
- [ ] OBC running the application (`obdh.sw_image` 0x0311 = 1)
- [ ] `eps.bat_soc` (0x0101) > 40 %
- [ ] No slew, desaturation or propulsive manoeuvre in progress or planned in
      the next 15 minutes

## Procedure Steps

### Step 1 --- Collect the Gyro and Determination Telemetry
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- AOCS housekeeping
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- AOCS determination
**Verify:** `aocs.gyro_units_on` (0x0294) reported within 20s --- record
**Verify:** `aocs.gyro_units_mask` (0x02D1) reported within 20s --- record (bit0 X, bit1 Y, bit2 Z)
**Verify:** `aocs.gyro_saturated` (0x0295) reported within 20s --- record
**Verify:** `aocs.gyro_bias_x` (0x0270) reported within 20s --- record
**Verify:** `aocs.gyro_bias_y` (0x0271) reported within 20s --- record
**Verify:** `aocs.gyro_bias_z` (0x0272) reported within 20s --- record
**Verify:** `aocs.gyro_bias_resid` (0x02D2) reported within 20s --- record
**Verify:** `aocs.gyro_temp` (0x0273) reported within 20s --- record
**Note:** The axis whose bias in 0x0270-0x0272 stands out is the affected
channel. If all three moved together, the fault is on all axes.
**GO/NO-GO:** Failure classified: unit off (0x02D1 != 7), bias (0x02D2 > 0.05),
saturation (0x0295 = 1), or a combination

### Step 2 --- Protect the Attitude Estimate
**Verify:** `aocs.mode` (0x020F) reported within 20s --- record
**Verify:** `aocs.est_source` (0x02C1) reported within 20s --- bit 0 = star tracker aiding
**Verify:** `aocs.st1_status` (0x0240) == 2 within 20s --- selected tracker TRACKING
**Verify:** `aocs.att_error` (0x0217) < 1.0 within 20s
**Note:** With a star tracker in the loop the filter estimates the bias and the
attitude stays bounded. Without one, the estimate coasts on the faulty gyro: a
0.05 deg/s bias walks the attitude tens of degrees in ten minutes and trips the
`aocs.att_error` FDIR rule. If the tracker is not tracking, recover it first
(CTG-008 Star Tracker Failure) and return here.
**Note:** Saturation (0x0295 = 1) means the vehicle is rotating faster than the
gyro range. That is an attitude anomaly, not a gyro fault: go to CTG-002 and come
back once the rates are under control.
**GO/NO-GO:** Star tracker in the determination loop and attitude error bounded

### Step 3 --- Restore Any Unit That Is Off
**Note:** Only needed if Step 1 found `aocs.gyro_units_mask` (0x02D1) != 7. The
commands below are idempotent: a unit that is already ON stays ON.
**TC:** `S2_AOCS_GYROSCOPE_0(device_id=518, state=1)` (Service 2, Subtype 1) --- X unit ON
**TC:** `S2_AOCS_GYROSCOPE_1(device_id=519, state=1)` (Service 2, Subtype 1) --- Y unit ON
**TC:** `S2_AOCS_GYROSCOPE_2(device_id=520, state=1)` (Service 2, Subtype 1) --- Z unit ON
**Verify:** `aocs.gyro_units_mask` (0x02D1) == 7 within 20s
**Verify:** `aocs.gyro_units_on` (0x0294) == 3 within 20s
**GO/NO-GO:** All three gyro units powered (a calibration with a dead channel is
refused with 0x0A02)

### Step 4 --- Run the On-Board Bias Calibration
**Note:** The vehicle must be quiescent: rates within 0.10 deg/s of the
reference. Hold NOMINAL (mode 4, or 8 in eclipse); do not slew or desaturate.
**TC:** `AOCS_GYRO_CALIBRATION(action=0, duration_s=300)` (Service 8, Subtype 1, func_id 13)
**Verify:** `aocs.gyro_cal_state` (0x02C9) == 1 within 20s --- RUNNING
**Verify:** `event 0x0210 AOCS_GYRO_CAL_START` received within 20s
**Note:** If the command is refused, the S1.8 failure notice and
`aocs.gyro_cal_reject` (0x02D0) name the gate: 0x0A01 AOCS unpowered,
0x0A02 a unit is off (Step 3), 0x0A03 no star tracker in the loop (Step 2),
0x0A04 body rate above 0.10 deg/s, 0x0A05 a calibration is already running.
**Note:** The S1.7 execution complete arrives when the arc ends, not on
acceptance.
**GO/NO-GO:** Calibration RUNNING

### Step 5 --- Monitor the Calibration Arc
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- poll every 30 s
**Verify:** `aocs.gyro_cal_progress` (0x02CA) >= 100 within 330s
**Note:** Any manoeuvre above the 0.10 deg/s limit aborts the arc with
`AOCS_GYRO_CAL_ABORT` (0x0212). Nothing is applied after an abort; fix the cause
named in 0x02D0 and re-run Step 4.
**GO/NO-GO:** Arc complete without an abort

### Step 6 --- Verify the Result and Record the Bias
**Verify:** `aocs.gyro_cal_state` (0x02C9) == 2 within 30s --- COMPLETE
**Verify:** `aocs.gyro_cal_result` (0x02CF) == 1 within 30s --- SUCCESS
**Verify:** `event 0x0211 AOCS_GYRO_CAL_COMPLETE` received within 30s
**TC:** `GET_PARAM(param_id=0x02CB)` (Service 20, Subtype 3) --- estimated X bias
**TC:** `GET_PARAM(param_id=0x02CC)` (Service 20, Subtype 3) --- estimated Y bias
**TC:** `GET_PARAM(param_id=0x02CD)` (Service 20, Subtype 3) --- estimated Z bias
**Verify:** `aocs.gyro_cal_bias_x` (0x02CB) reported within 20s --- record
**Verify:** `aocs.gyro_cal_bias_y` (0x02CC) reported within 20s --- record
**Verify:** `aocs.gyro_cal_bias_z` (0x02CD) reported within 20s --- record
**GO/NO-GO:** SUCCESS, and every axis within +/-0.5 deg/s. Above that, do not
accept the result: go to Step 7.

### Step 7 --- Isolate an Unrecoverable Channel (only if Step 6 failed)
**Note:** Skip this step if Step 6 was GO. Isolate a channel only if its bias is
above 0.5 deg/s after a 900 s calibration, or if two calibrations in a row abort
with 0x0A06. Command OFF the faulty axis only; the X unit is shown. Use
device 519 for Y or 520 for Z.
**TC:** `S2_AOCS_GYROSCOPE_0(device_id=518, state=0)` (Service 2, Subtype 1) --- faulty unit OFF (X shown)
**TC:** `AOCS_EST_RESET(mode=1)` (Service 8, Subtype 1, func_id 91) --- warm reset: keep the attitude, re-inflate the covariance
**Verify:** `aocs.gyro_units_mask` (0x02D1) reported within 20s --- the faulty bit is clear
**Verify:** `aocs.est_source` (0x02C1) reported within 60s --- bit 0 still set
**Note:** With a channel off, that axis's rate comes from the star tracker alone.
Fine pointing and imaging on that axis are degraded until the end of the
mission; there is no spare unit. Through a tracker outage the estimator has no
rate reference on that axis.
**GO/NO-GO:** Faulty channel isolated, estimator re-converging

### Step 8 --- Confirm the Recovery
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27)
**Verify:** `aocs.gyro_bias_resid` (0x02D2) < 0.005 within 60s
**TC:** `HK_REQUEST(sid=7)` (Service 3, Subtype 27) --- poll every 60 s for 5 minutes
**Verify:** `aocs.gyro_cal_comp_mag` (0x02CE) reported within 60s --- record
**Verify:** `aocs.knowledge_err_3sig` (0x02A7) < 120 within 300s --- arcsec
**Verify:** `aocs.control_err` (0x02A8) < 1.0 within 300s --- deg
**Note:** A successful calibration moves the bias from 0x02D2 (left at the
output) into 0x02CE (compensation applied). Event 0x020B clears because it is
measured on the residual; the hardware fault is still there.
**GO/NO-GO:** Rate reference restored or channel isolated; determination stable

## Off-Nominal Handling
- **All three units off or failed.** The filter has no rate reference and coasts on
  the star tracker, sun sensors and magnetometer only. Hold NOMINAL if the tracker
  is valid; otherwise go to EMG-005 (Loss of Attitude).
- **Refused with 0x0A03.** No star tracker in the loop. Recover the tracker
  (CTG-008), wait for `aocs.est_source` (0x02C1) bit 0, then retry Step 4.
- **Refused with 0x0A04.** The vehicle is not quiescent. Wait for any slew or
  desaturation to end (`aocs.mode` 0x020F != 6 and != 7) and retry.
- **Bias reappears after a good calibration.** A temperature-driven drift follows
  `aocs.gyro_temp` (0x0273); re-run the calibration after the thermal transient.
  A bias that returns at constant temperature is a degrading unit: raise an anomaly
  report.
- **Calibration over-corrects after the fault is cleared.** If the instructor
  removes an injected bias after a calibration, the stored compensation now
  over-corrects with the opposite sign (0x02D2 and 0x02CE both non-zero). Re-run
  Step 4 to load a fresh compensation.

## Post-Conditions
- [ ] Affected channel identified and recorded
- [ ] Either `aocs.gyro_cal_result` (0x02CF) = 1 with `aocs.gyro_bias_resid`
      (0x02D2) < 0.005 deg/s, or the faulty unit isolated and recorded in
      `aocs.gyro_units_mask` (0x02D1)
- [ ] Attitude knowledge error below 120 arcsec 3-sigma (`aocs.knowledge_err_3sig` 0x02A7)
- [ ] Anomaly report raised with the recorded biases, temperature and decision

## Exit state
- AOCS in NOMINAL (mode 4, or 8 in eclipse) with the star tracker in the loop
- Gyro bias compensated, or one channel isolated with degraded rate knowledge on
  that axis
- No power-line, TTC or payload state changed

**NEXT:** resume the interrupted activity. If a channel was isolated, check
`aocs.fine_ready` (0x02C5) before the next imaging session: FINE_POINT is
refused while it is non-zero.
