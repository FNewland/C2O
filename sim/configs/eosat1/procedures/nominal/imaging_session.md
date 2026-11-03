# NOM-002: Imaging Session
**Subsystem:** PAYLOAD / AOCS / TCS
**Phase:** NOMINAL
**Revision:** 1.1 --- 2026-11-03: the FPA cooler is OFF in STANDBY; Step 2
switches it on (imaging preparation) and Step 6 releases it.
**Approved:** Flight Operations Director

## Purpose
Execute a planned Earth-observation imaging session. This procedure transitions the
payload from STANDBY to IMAGING mode, monitors image acquisition, and returns the
payload to STANDBY upon completion. Fine pointing performance and focal plane
thermal conditions must be confirmed before imaging begins.

## Prerequisites
- [ ] NOM-001 Pass Startup completed with all-GO declaration
- [ ] Payload in STANDBY mode (`payload.mode` (0x0600) = 1)
- [ ] FPA cooler switched on (Step 2) at least 10 min before the imaging window.
      STANDBY no longer runs the cooler: the cool-down is part of the preparation.
- [ ] Target scene parameters uploaded to onboard scheduler
- [ ] AOCS in FINE_POINT (`aocs.mode` (0x020F) = **5**). The payload capture gate
      demands EXACTLY mode 5. There is no NOMINAL mode and mode 0 is OFF —
      the codes are 0 OFF, 1 SAFE_BOOT, 2 DETUMBLE, 3 COARSE_SUN, 4 NOMINAL,
      5 FINE_POINT, 6 SLEW, 7 DESAT, 8 ECLIPSE, 9 INERTIAL
      (`configs/eosat1/aocs/aocs_mode_codes.yaml`). A card that asked the operator
      to confirm mode 0 was asking them to confirm the AOCS was switched off.
- [ ] EPS battery SoC > 50 % (`eps.bat_soc` (0x0101) > 50)
- [ ] Imaging window confirmed by flight dynamics (target in view)

## Procedure Steps

### Step 1 --- Verify Fine Pointing Performance
**TC:** `AOCS_FINE_READY_CHECK` (Service 8, Subtype 1, func_id 89) --- read the FINE precondition mask
**Verify:** `aocs.fine_ready == 0` (0x02C5, timeout 10 s) --- every precondition bit clear
**TC:** `AOCS_SET_MODE(mode=5)` (Service 8, Subtype 1, func_id 0) --- FINE_POINT
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- request AOCS housekeeping
**Verify:** `aocs.mode == 5` (0x020F, timeout 60 s) --- FINE_POINT
**Verify:** `aocs.mode_demoted == 0` (0x0298, timeout 10 s) --- the spacecraft is in
the mode the ground asked for. If this is 1, `aocs.commanded_mode` (0x0297) says
what was asked and the 0x0200 event description says why the demotion happened.
**Note:** `aocs.fine_degraded` (0x0299) = 1 means FINE is being flown on a THREE-wheel
set. That is legal and captures normally --- the capture gate enforces pointing error
and rate stability, which are what determine image quality, not a wheel count. It is
recorded on every product (bit 0 of the catalogue `flags` octet) so a reprocessing
campaign can find those strips.
**Note:** `aocs.desat_inhibit` (0x029A) is asserted automatically while
`payload.mode` = 2, so a momentum dump can no longer pre-empt a strip. Watch
`0x02C5` bit 4 (momentum envelope >= 70 %) as the honest "a desat is coming"
planning warning BEFORE committing to a long strip.
**Verify:** `aocs.att_error` (0x0217) < 0.1 deg within 5 s
**Verify:** `aocs.rate_roll` (0x0204) < 0.01 deg/s
**Verify:** `aocs.rate_pitch` (0x0205) in range [0.053, 0.073] deg/s (nadir tracking carries the orbit rate, +0.063 deg/s on this console; a zero pitch rate would mean the spacecraft is NOT tracking nadir)
**Verify:** `aocs.rate_yaw` (0x0206) < 0.01 deg/s
**GO/NO-GO:** If att_error >= 0.1 deg, HOLD. Wait up to 60 s for convergence.
If still not met, abort imaging and investigate AOCS performance.

### Step 2 --- Prepare the Focal Plane (FPA Cooler On)
**Note:** The FPA cooler is OFF in STANDBY (2026-11-03). Switching it on is the
imaging preparation: from the uncooled STANDBY equilibrium (about +10 C) the
detector needs about 6.5 min to reach `payload.fpa_ready` = 1 (60 s of that is
the readiness hysteresis). Send this step at least 10 min before the imaging
window, before Step 1 if the window is close; the planner's `imaging_pass` books
480 s for it. If `tcs.cooler_fpa` (0x040C) already reads 1, skip the TC.
**TC:** `FPA_COOLER(on=1)` (Service 8, Subtype 1, func_id 43) --- FPA cooler ON
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- request TCS housekeeping
**Verify:** `tcs.cooler_fpa` (0x040C) = 1 (ACTIVE) within 10 s
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- payload housekeeping (`payload.fpa_ready`)
**Verify:** `payload.fpa_ready` (0x0610) = 1 within 600 s
**Verify:** `tcs.temp_fpa` (0x0408) < -10.0 C within 5 s
**GO/NO-GO:** If `payload.fpa_ready` is still 0 after 10 min, HOLD. Read
`payload.cooler_margin_k` (0x064B): a value <= 0 means the setpoint is out of
reach at the present sink. If the temperature is not decreasing, check the
cooler status and abort if necessary.

### Step 3 --- Verify Storage Capacity
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- request Payload housekeeping
**Verify:** `payload.store_used` (0x0604) < 90 % within 5 s
**Note:** Record `payload.product_count` (0x0648) as baseline N0 and
`payload.product_mb` (0x0647) as the catalogued volume. These are the Phase 4
parameters that count REAL products; `payload.store_used` (0x0604) also carries
the store's pre-existing ~20 % non-product fill, so it is not a product count.
**GO/NO-GO:** If storage >= 90 %, abort imaging. Schedule data downlink first
(NOM-003) to free storage before retrying.

### Step 4 --- Command Imaging Mode
**TC:** `PAYLOAD_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 26) --- command IMAGING
**Verify:** `payload.mode` (0x0600) = 2 (IMAGING) within 15 s
**Verify:** `eps.power_cons` (0x0106) increase observed (payload power draw)
**Note:** Imaging session timer starts. Nominal session duration per pass plan.
**Note:** Since Phase 4, entering IMAGING does NOT by itself generate data.
The store only grows while a commanded strip is being read out --- a few seconds per
capture, shown by `payload.readout_active` (0x0649) and reflected in
`payload.mem_used_mb` (0x060B). (There are no `payload.line_rate` / `payload.data_rate`
parameters; 0x0607 and 0x0608 are not allocated in `telemetry/parameters.yaml`.) Before the fix, IMAGING alone accreted about
9.7 MB/s and filled the 20 GB store in ~33 minutes with zero captures, which is
why an earlier teaching note on this card used to contradict the spacecraft.

### Step 5 --- Trigger the Acquisition(s)
**TC:** `PAYLOAD_CAPTURE(scene_id=N, lines=2048)` (Service 8, Subtype 1, func_id 28)  \
**Wire:** `1C <scene_id:uint16> 08 00` --- e.g. scene 1042 = `1C 04 12 08 00`
**Note:** Images do NOT appear on their own. Each capture is one commanded
acquisition: `scene_id` is the ground-assigned product id (0 = let the payload
auto-assign) and `lines` is the along-track strip length, 256-20000. 2048 lines
at the 500 Hz line rate is a 4.10 s acquisition and, at four enabled bands, the
4.0 MB reference frame; halving `lines` halves the stored volume. Geolocation is
stamped on board from the ephemeris at shutter open --- it is not an argument.
**Note:** Repeat for each planned target in this session. A capture is REFUSED
with TM(1,8) if AOCS is not holding FINE_POINT with total error < 0.05 deg, if
the FPA is not ready, or if the store cannot hold the frame --- the failure
notice names which gate refused it.
**Verify:** `payload.last_scene_id` (0x060C) = the commanded `scene_id` within 10 s
**Note:** Image quality is not telemetered: it is checked on the ground on the quick-look of each product after downlink. Record the scene ids now so each product can be checked then.

### Step 5a --- Monitor Image Acquisition
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- payload HK, poll every 30 s
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) --- AOCS HK, poll every 30 s
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) --- TCS HK, poll every 30 s
**Verify:** `payload.image_count` (0x0605) incrementing (current > N0)
**Verify:** `payload.store_used` (0x0604) < 95 % throughout session
**Verify:** `aocs.att_error` (0x0217) remains < 0.1 deg throughout session
**Verify:** `tcs.temp_fpa` (0x0408) remains < -10.0 C throughout session
**Action:** If `payload.store_used` >= 95 %, terminate the session at once (Step 6).
**Action:** If `aocs.att_error` >= 0.5 deg, terminate the session at once (Step 6).

### Step 6 --- Terminate Imaging Session
**TC:** `PAYLOAD_SET_MODE(mode=1)` (Service 8, Subtype 1, func_id 26) --- command STANDBY
**Verify:** `payload.mode` (0x0600) = 1 (STANDBY) within 15 s
**Verify:** `tcs.cooler_fpa` (0x040C) = 0 within 10 s --- STANDBY releases the FPA cooler
**Verify:** `eps.power_cons` (0x0106) decrease observed (imaging load and the 15 W cooler off)
**Note:** Record final `payload.image_count` (0x0605) as Nf. Images acquired = Nf - N0.

### Step 7 --- Post-Imaging Assessment
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) --- final payload HK
**Verify:** `payload.store_used` (0x0604) < 95 %
**Verify:** `payload.image_count` (0x0605) = Nf (no unexpected increment)
**Log:** Record images acquired, storage delta, and session duration in pass log.

## Off-Nominal Handling
- If `payload.mode` does not transition to IMAGING within 15 s: Re-send command
  once. If still no transition, abort and flag payload anomaly.
- If `payload.image_count` not incrementing: Possible detector or data-path
  fault. Command STANDBY and report anomaly.
- If `aocs.att_error` exceeds 0.5 deg during imaging: Abort session immediately.
  Images captured during high error may be unusable --- flag for ground review.
- If `tcs.temp_fpa` rises above -5.0 C: Abort imaging to protect detector.
  Investigate cooler performance.
- If `eps.bat_soc` drops below 40 % during session: Abort imaging to preserve
  power margin for safe spacecraft operations.

## Post-Conditions
- [ ] Payload returned to STANDBY mode, FPA cooler off
- [ ] Image count and storage usage logged
- [ ] AOCS remained in fine-pointing throughout (att_error < 0.1 deg)
- [ ] FPA temperature remained at setpoint (<= -10.0 C) throughout
- [ ] Pass log updated with imaging session summary
