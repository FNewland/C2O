# EOSAT-1 LEOP Operations Guide {#eosat-1-leop-operations-guide}

**Document ID:** EOSAT1-UM-LEOP-010
**Issue:** 1.0
**Date:** 2026-03-13
**Classification:** UNCLASSIFIED — Mission Operations

---

## 1. Purpose {#1-purpose}

This document provides the complete operations guide for the Launch and Early Orbit Phase
(LEOP) of the EOSAT-1 mission. It covers the separation sequence, first ground contact,
bootloader operations, application boot, sequential subsystem power-on, ADCS commissioning,
and the transition to nominal operations. All GO/NO-GO checkpoints are identified.

## 2. LEOP Overview {#2-leop-overview}

**Definitive procedure-card order (2026-08c flow redesign).** The LEOP flight
cards are executed in this order — NOT in card-number order — and each card
declares its Entry state and Exit state and ends with an explicit NEXT:

1. **LEOP-001** First Acquisition & OBC Boot — link, application image,
   beacon-mode clear, LOW rung, platform HK SIDs.
2. **LEOP-002** Initial Health Check — observation only; confirms the
   unpowered subsystems (AOCS, payload, cooler, prop) are still dark.
3. **LEOP-004** Solar Array Verification — wing deployment.
4. **LEOP-007** Sequential Power-On — LEOP loads ONLY: heater lines as
   needed, the AOCS suite line, magnetometer + magnetorquers + GPS devices,
   then the commanded DETUMBLE. The payload line belongs to COM-009, the FPA
   cooler to COM-010, the wheel ENABLE to COM-004, the prop line to
   manoeuvre preparation.
5. **LEOP-005** Sun Acquisition — OBSERVES the automatic DETUMBLE →
   COARSE_SUN handover (nothing is commanded); LEOP parks in the sun hold.
6. **LEOP-006** Time Synchronisation — BOTH paths in one card: ground
   SET_TIME immediately, then OBC_GPS_TIME_SYNC once the GPS fix is in;
   enables HK SID 12 (GPS_NAV).
7. **LEOP-003** Initial Orbit Determination — verifies the SID-12 PVT, and
   as the LAST LEOP card declares `SYS_SET_MISSION_PHASE(phase=5)` and hands
   over to commissioning (COM-001).

Commissioning then runs COM-001 … COM-010, **COM-012 (First Light),
COM-011 (Calibration)**, COM-013 — with COM-003 (gyro calibration,
startable in the COARSE_SUN hold) deliberately BEFORE COM-004 (wheel
enable), and COM-013 alone declaring phase 6.

LEOP begins at spacecraft separation from the launcher and concludes when the spacecraft
is declared operational in nominal mode. The phase typically lasts 1-3 days and proceeds
through the following major milestones:

| Milestone                  | Approx. Time    | Description                          |
|----------------------------|-----------------|--------------------------------------|
| Separation                 | T+0             | Launcher release, timer start        |
| Antenna deployment         | T+30 min        | Burn wire activation                 |
| First contact              | T+30 min to T+6 h | Beacon acquisition at Iqaluit or Troll |
| Application boot           | First contact   | Transition from the bootloader           |
| Detumble complete          | T+1 to T+12 h  | Body rates < 0.5 deg/s              |
| Solar wing deployment      | T+2 to T+14 h  | Deploy +Y and -Y solar wings        |
| Sequential power-on        | T+12 to T+24 h | Subsystem activation                 |
| ADCS commissioning         | T+24 to T+72 h | Sensor/actuator checkout             |
| Nominal transition         | T+48 to T+72 h | Full operational capability          |

## 3. Separation Sequence {#3-separation-sequence}

### 3.1 Separation State Machine {#31-separation-state-machine}

The separation sequence follows a 7-phase state machine implemented in the OBC:

| Phase             | Trigger                    | Duration   | Actions                           |
|-------------------|----------------------------|------------|-----------------------------------|
| PRE_SEPARATION    | Power-on (in launcher)     | —          | All systems off except timer circuit |
| SEP_DETECTED      | Separation switch opens    | Instant    | Timer starts; unswitchable PDM on |
| POWER_STABILIZE   | Unswitchable PDM active    | ~30 s      | OBC boots; RX powers on           |
| TIMER_WAIT        | OBC boot complete          | ~30 min    | No RF transmissions; OBC in the bootloader |
| ANTENNA_DEPLOY    | 30-min timer expires       | ~60 s      | Burn wire commanded; antenna deploys |
| BEACON_START      | Antenna deploy confirmed   | ~10 s      | TX enabled; beacon SID 11 on the SAFE tier (1 kbps; renamed from BEACON, 2026-08c) |
| NOMINAL           | Beacon transmission active | —          | Ready for ground contact          |

### 3.2 Unswitchable Line Power-On {#32-unswitchable-line-power-on}

Upon separation detection, the unswitchable PDM lines activate automatically:

- **UNSW-1 (OBC)**: The primary OBC (OBC-A) powers on and boots into the bootloader.
- **UNSW-2 (RX)**: The transponder receiver powers on, ready to accept ground commands
  via the dedicated PDM command channel.

No ground command is required for these lines. They are hardwired to activate when the
separation switch opens and the timer circuit initialises.

### 3.3 30-Minute Timer Hold {#33-30-minute-timer-hold}

During the TIMER_WAIT phase:

- The OBC is operational in the bootloader but does not transmit.
- The receiver is powered and listening for commands (not expected pre-deployment).
- All switchable PDM lines remain inhibited.
- The spacecraft is tumbling freely (no attitude control in the bootloader).
- Battery power supports this minimal configuration indefinitely.

The 30-minute hold satisfies regulatory requirements prohibiting RF transmissions
immediately after separation from the launcher.

### 3.4 Antenna Deployment {#34-antenna-deployment}

After the 30-minute timer expires:

1. OBC commands the primary burn wire circuit.
2. Current passes through the restraining wire (~2 A for 5 seconds).
3. The wire melts and spring-loaded hinges deploy the antenna elements.
4. Deployment is verified by monitoring microswitches (if available) or by RSSI
   improvement once transmissions begin.
5. If the primary burn wire fails to deploy the antenna, the OBC commands the
   redundant burn wire circuit after a 60-second timeout.

### 3.5 Beacon Transmission Start {#35-beacon-transmission-start}

Once the antenna is deployed:

1. The TX switchable PDM line (SW-1) is enabled.
2. The transmitter and power amplifier power on.
3. The OBC begins transmitting beacon packets (**SID 11**) on the **SAFE tier** of the TM rate ladder (renamed from BEACON, 2026-08c — “beacon” now always means the UHF whip transmitter) — 1 kbps, 1 kBd, BPSK with conv(7,1/2)+RS, ~3.1 kHz occupied bandwidth — sourced from the **bootloader APID (0x002)**. This is the ONLY HK packet emitted in bootloader mode — SIDs 1–6 remain silent until application boot. No TM storage, no attitude control, and no payload operations are possible while in bootloader. SAFE is a lifeline rung, not an operations rate: at 1 kbps it carries SID 11 with over 100x headroom but cannot carry the 1557 bps periodic housekeeping stream at all.
4. The 15-minute TX auto-off timer starts, but is reset each time a beacon is transmitted.

The spacecraft is now ready for ground acquisition.

**GO/NO-GO Checkpoint 1: Separation Sequence Complete**
- Criteria: Beacon transmission active, antenna deployed.
- Decision: Proceed to first contact operations.

## 4. First Contact — RF Acquisition {#4-first-contact--rf-acquisition}

### 4.1 Ground Station Preparation {#41-ground-station-preparation}

Before the expected first contact window:

1. Configure ground station antenna for S-band acquisition at predicted AOS azimuth/elevation.
2. Set the demodulator to the SAFE tier: 1 kBd, BPSK, conv(7,1/2)+RS. This is the only
   waveform the bootloader transmits; a demodulator configured for the LOW tier (16 kBd)
   will not lock it.
3. Load EOSAT-1 frequency plan (2200.0 MHz downlink, 2025.0 MHz uplink, S-band).
4. Prepare pre-planned LEOP command sequence.

### 4.2 Beacon TM Interpretation {#42-beacon-tm-interpretation}

The beacon packet (SID 11) contains minimal but critical health information:

| Parameter       | Expected Value         | Concern If                        |
|-----------------|------------------------|-----------------------------------|
| sw_image        | 0 (bootloader)         | Any other value                   |
| bat_voltage     | 30.9-33.4 V                | < 29.6 V (low battery)             |
| bat_soc         | > 60%                  | < 40% (unexpected power drain)    |
| obc_temp        | 10-40 deg C            | Outside range (thermal issue)     |
| uptime          | ~1800+ s (30 min+)     | < 1800 s (recent reset)          |
| reboot_count    | 0 or 1                 | > 1 (multiple resets, investigate)|

### 4.3 First Contact Procedure {#43-first-contact-procedure}

1. Acquire beacon signal at AOS. Verify carrier lock on ground receiver.
2. Decode beacon packet (SID 11). Record all parameter values.
3. Verify spacecraft health from beacon parameters (see table above).
4. Do not uplink `SET_TIME` yet: S9.1 is accepted in the bootloader but fails at execution.
5. Record the beacon timestamp offset; the clock is set after `OBC_BOOT_APP` (LEOP-006).

**GO/NO-GO Checkpoint 2: First Contact Health Assessment**
- Criteria: Beacon received, all parameters nominal, OBC in the bootloader.
- Decision: Proceed to application boot.

## 5. Bootloader Operations {#5-bootloader-operations}

### 5.1 Limited HK in the Bootloader {#51-limited-hk-in-the-bootloader}

While in the bootloader, **only SID 11 (Beacon)** is emitted, and it is sourced from the dedicated **bootloader APID (0x002)** — distinct from the application APID (0x001) used once the OBC application is running. This gives ground a clear, unambiguous signature of bootloader vs. application state:

- Beacon packet (SID 11) every 30 s on bootloader APID 0x002.
- No TM storage exists — commanded dumps will fail, there are no stores to enable.
- No AOCS / TCS / Payload HK and no subsystem-level telemetry.
- No periodic event log: only severity ≥ 2 events generated by the bootloader itself are emitted.

Full housekeeping telemetry (per-subsystem SIDs 1–6) and onboard TM stores come online only after the application software has booted successfully (phase 4). An OBC reboot at any later phase automatically reverts the spacecraft to this bootloader/beacon-only state until the application re-boots.

### 5.2 Restricted Commands in the Bootloader {#52-restricted-commands-in-the-bootloader}

Only the following commands are accepted:

| Command              | Use During LEOP                                   |
|----------------------|---------------------------------------------------|
| OBC_BOOT_APP (S8.1 func 55) | Boot application software                 |
| SET_TIME (S9.1)      | Accepted, but fails at execution until the application runs — set time after OBC_BOOT_APP (LEOP-006) |
| HK_REQUEST (SID 11)  | Request immediate beacon packet (vs. waiting 30 s) |
| OBC_REBOOT, OBC_SWITCH_UNIT, OBC_SELECT_BUS, OBC_BOOT_INHIBIT, OBC_CLEAR_REBOOT_CNT, OBC_DIAGNOSTIC (funcs 52–54, 56, 57, 61); S17.1; S20.1/S20.3 | Bootloader maintenance, connection test, parameter get/set |
| EPS_POWER_ON / EPS_POWER_OFF (19/20), TTC_PA_ON / TTC_PA_OFF (66/67), TTC_DEPLOY_ANTENNA (69), SYS_SET_MISSION_PHASE (120) | First-contact power lines, transmitter, antenna and mission phase |

All other commands will be rejected at acceptance with failure code 0x0006. Do not attempt subsystem commanding in the bootloader.

## 6. Application Boot and Verification {#6-application-boot-and-verification}

### 6.1 Boot Procedure {#61-boot-procedure}

1. Verify beacon health is nominal (Checkpoint 2 passed).
2. Send `OBC_BOOT_APP` (S8.1 func 55) to command transition from the bootloader to the application.
3. Wait 30 seconds for application software to load and perform POST.
4. Monitor for the appearance of full housekeeping telemetry (SID 1-6).
5. If no HK appears within 60 seconds, the application boot may have failed.
   Check for beacon reappearance (indicating fallback to the bootloader).

### 6.2 Post-Boot Verification {#62-post-boot-verification}

Once application software is running, verify:

| Check                          | Parameter        | Expected Value              |
|--------------------------------|------------------|-----------------------------|
| OBC mode                       | obc_mode (0x0300)| 0 (NOMINAL) or 1 (SAFE)    |
| CPU load                       | cpu_load (0x0302)| < 50% (post-boot settling)  |
| HK generation                  | tm_pkt_count     | Incrementing at 1 Hz        |
| Battery health                 | bat_soc (0x0101) | > 50%                       |
| Bus voltage                    | bus_voltage      | 30.9-33.4 V                     |
| TC processing                  | tc_exec_count    | Incrementing normally       |

### 6.3 Recovery from Failed Boot {#63-recovery-from-failed-boot}

If the application fails to start:

1. Wait for OBC to fall back to the bootloader (3 consecutive watchdog resets).
2. Assess reboot_count in beacon packet.
3. Follow CTG-021 (OBC Bootloader Recovery); there is no `SW_UPLOAD` command.
4. If patch is not available, maintain spacecraft in the bootloader with beacon mode
   until a patch can be prepared and uplinked during subsequent contacts.

**GO/NO-GO Checkpoint 3: Application Boot Successful**
- Criteria: Full HK telemetry flowing, OBC in NOMINAL or SAFE mode.
- Decision: Proceed to sequential power-on.

## 6A. Solar Wing Deployment {#6a-solar-wing-deployment}

After application boot and initial detumble (body rates < 0.5 deg/s), the deployable
solar wings on the +Y and -Y faces must be extended to provide full power generation
capability. This step is performed before sequential power-on to ensure adequate power
margin for subsystem activation.

### 6A.1 Pre-Deployment Checks {#6a1-pre-deployment-checks}

1. Verify application software is running (OBC mode = NOMINAL or SAFE).
2. Verify body rates < 0.5 deg/s (detumble complete or sufficient).
3. Verify battery SoC > 50% (wing deployment requires ~2 A per wing for 30 s).
4. Request EPS HK (`HK_REQUEST SID=1`) and confirm nominal bus voltage.

### 6A.2 Deploy +Y Wing {#6a2-deploy-y-wing}

1. Send `EPS_DEPLOY_WING` (func_id 81, wing=0) to deploy the +Y solar wing.
2. Monitor `wing_deploy_timer` (0x0145) counting down from ~30 s.
3. Wait for event 0x0112 (WING_PY_DEPLOYED) confirming deployment.
4. Verify `wing_status` (0x0144) bit 0 is set.
5. Monitor `sa_py_current` (0x012D) for increased current if in sunlight.
6. Wait 60 seconds for attitude transient to settle.

### 6A.3 Deploy -Y Wing {#6a3-deploy--y-wing}

1. Send `EPS_DEPLOY_WING` (func_id 81, wing=1) to deploy the -Y solar wing.
2. Monitor `wing_deploy_timer` (0x0145) counting down from ~30 s.
3. Wait for event 0x0113 (WING_MY_DEPLOYED) confirming deployment.
4. Verify `wing_status` (0x0144) bit 1 is set.
5. Monitor `sa_my_current` (0x012E) for increased current if in sunlight.

### 6A.4 Post-Deployment Verification {#6a4-post-deployment-verification}

1. Request EPS HK and verify `power_gen` (0x0107) has increased.
2. Confirm `wing_status` (0x0144) = 0x03 (both wings deployed).
3. Compare total power generation against prediction for deployed configuration
   (total area 0.438 m2 vs. 0.198 m2 stowed).
4. Record deployment times and power readings in LEOP log.

### 6A.5 Off-Nominal: Wing Deployment Failure {#6a5-off-nominal-wing-deployment-failure}

If a wing fails to deploy (no event generated within 60 s, wing_status bit not set):

1. Wait 60 seconds for burn wire cooldown.
2. Retry the deployment command for the failed wing.
3. If second attempt fails, continue LEOP with single wing deployed.
4. Assess power budget viability with reduced solar area.
5. Schedule detailed investigation during commissioning.

**GO/NO-GO Checkpoint 3A: Solar Wing Deployment**
- Criteria: Both wings deployed (wing_status = 0x03), power generation increased.
- Decision: Proceed to sequential power-on.

## 7. Sequential Power-On Procedure {#7-sequential-power-on-procedure}

After application boot and solar wing deployment, subsystems are powered on one at a time
to verify health and manage the power budget. The order is critical — each step must be
verified before proceeding.

### 7.1 Power-On Sequence {#71-power-on-sequence}

| Step | Subsystem           | PDM Line | Verification                          | Power Impact |
|------|---------------------|----------|---------------------------------------|--------------|
| 1    | Battery heater      | SW-5     | ONLY if bat_temp < +5 C: htr line on, temp stabilising | +8 W |
| 2    | Magnetometer        | SW-2     | aocs.mag_enabled (0x025C) = 1; mag readings nominal | +1 W |
| 3    | Magnetorquers       | SW-2     | MTQ_ENABLE accepted; aocs.mtq_enabled (0x025E) = 1 | +2 W |
| 4    | GPS receiver        | SW-2     | TTFF running (fix may take 15-30 min) | +1 W |

Then command DETUMBLE (`AOCS_SET_MODE(mode=2)`) — the mode command REFUSES if
the magnetometer or the magnetorquers are missing (0x0A20 / 0x0A21), which is
why steps 2-3 come first.

**Deliberately NOT powered or enabled during LEOP (2026-08c):**

| Load | Enabled by | Why deferred |
|------|-----------|--------------|
| Star trackers, gyro units | COM-003 | not needed for the sun-safe hold |
| Reaction wheel ENABLE | COM-004 | line SW-2 is hot, but the wheels stay disabled — a power switch never hands authority to the control loop |
| Payload line (SW-4) | COM-009 | commissioning load, not a LEOP need |
| FPA cooler | COM-010 | ~15 W continuous; switching it on in LEOP burnt margin for days (owner finding) |
| Propulsion line | NOM-004/NOM-013 | manoeuvre preparation only |

### 7.2 Power Budget Monitoring {#72-power-budget-monitoring}

After each power-on step, verify:

- `power_cons` (0x0106) has increased by the expected amount.
- `bat_soc` (0x0101) is not declining excessively.
- `power_gen` (0x0107) exceeds `power_cons` during sunlit portions of the orbit.

**GO/NO-GO Checkpoint 4: Sequential Power-On Complete**
- Criteria: The LEOP load set (and only it) powered and healthy; DETUMBLE
  active on magnetometer + magnetorquers; wheels still disabled.
- Decision: Proceed to LEOP-005 (observe the automatic sun acquisition).

## 8. ADCS Commissioning Sequence {#8-adcs-commissioning-sequence}

The ADCS commissioning verifies each attitude determination and control component in a
specific order: sensors first, then determination algorithms, then actuators, then
control loops.

### 8.1 Phase 1: Sensor Commissioning {#81-phase-1-sensor-commissioning}

#### Step 1: Magnetometer Calibration {#step-1-magnetometer-calibration}

1. Verify the magnetometer is powered and `aocs.mag_enabled` (0x025C) = 1.
2. Record magnetometer readings over one full orbit.
3. Compare measured magnetic field against the IGRF model for the current position.
4. Compute and upload calibration offsets if residuals exceed 500 nT.
5. Verify calibrated readings match model to within 200 nT.

#### Step 2: CSS Verification {#step-2-css-verification}

1. During sunlit portion, verify all 6 CSS heads are reporting non-zero values on
   illuminated faces.
2. Verify that eclipsed faces report near-zero values.
3. Check that the computed Sun vector direction is consistent with the orbital model
   (expected Sun direction for current orbit position and season).
4. Verify geometric consistency: opposite faces should have complementary readings
   (if one face sees the Sun, the opposite face should be dark).

#### Step 3: Star Camera Commissioning {#step-3-star-camera-commissioning}

1. Ensure body rates are below 0.1 deg/s (detumble must be sufficient).
2. Power on zenith star camera (ST-Zenith on +Z face).
3. Wait for star camera to perform lost-in-space acquisition (up to 60 seconds).
4. Verify valid attitude quaternion output (all four components non-zero).
5. Compare star camera attitude against Sun vector (from CSS) for consistency check.
6. Verify star camera is not blinded (check Sun angle to +Z boresight > 15 deg).

#### Step 4: Gyro Bias Calibration {#step-4-gyro-bias-calibration}

1. With star camera providing valid attitude, enable gyro bias estimation algorithm.
2. Accumulate calibration data for at least 10 minutes.
3. Verify gyro bias estimates converge (bias values stabilise).
4. Accept calibration and store in OBC non-volatile memory.
5. Verify calibrated rate measurements match star camera-derived rates to within
   0.01 deg/s.

**GO/NO-GO Checkpoint 5: Sensor Commissioning Complete**
- Criteria: All sensors calibrated and providing valid data.
- Decision: Proceed to attitude determination validation.

### 8.2 Phase 2: Attitude Determination Validation {#82-phase-2-attitude-determination-validation}

1. Verify fused attitude solution (combining star camera, magnetometer, gyros) is stable.
2. Confirm `att_error` (0x0217) is computed and reasonable.
3. Verify attitude quaternion is continuous (no jumps between updates).
4. Cross-check GPS-derived position with expected orbit for consistency.
5. Record attitude solution over at least one full orbit for ground analysis.

**GO/NO-GO Checkpoint 6: Attitude Determination Validated**
- Criteria: Stable attitude solution, consistent across sensors.
- Decision: Proceed to actuator commissioning.

### 8.3 Phase 3: Actuator Commissioning {#83-phase-3-actuator-commissioning}

#### Step 5: Magnetorquer Sign Check {#step-5-magnetorquer-sign-check}

1. Command a known current to each magnetorquer coil (X, Y, Z) individually.
2. Observe the resulting torque on the spacecraft via gyro rate measurements.
3. Verify the torque direction is consistent with the expected interaction between
   the commanded dipole moment and the measured magnetic field.
4. Confirm no sign errors (wrong direction would indicate wiring issue).
5. If a sign error is detected, update the magnetorquer polarity configuration in software.

#### Step 6: Reaction Wheel Spin-Up Test {#step-6-reaction-wheel-spin-up-test}

1. Command each wheel individually to a low speed (+100 RPM).
2. Verify wheel speed telemetry matches the commanded value.
3. Verify the spacecraft experiences a small counter-torque in the expected direction.
4. Spin each wheel to -100 RPM and verify correct reverse direction.
5. Return all wheels to 0 RPM.
6. Verify wheel temperatures remain nominal throughout.

#### Step 7: Control Gain Verification {#step-7-control-gain-verification}

1. Enable the AOCS control law with conservative (low) gains.
2. Command a small attitude offset (1 deg) and observe the response.
3. Verify the spacecraft responds in the correct direction and at a reasonable rate.
4. Check for overshoot or oscillation — adjust gains if necessary.
5. Return to zero offset and verify convergence.

**GO/NO-GO Checkpoint 7: Actuator Commissioning Complete**
- Criteria: All actuators verified, correct direction and magnitude.
- Decision: Proceed to active control tests.

### 8.4 Phase 4: Active Control Validation {#84-phase-4-active-control-validation}

#### Step 8: Rate Damping Test {#step-8-rate-damping-test}

1. Command AOCS to DETUMBLE mode (if not already).
2. If rates are already near zero, introduce a small perturbation via magnetorquers.
3. Verify magnetorquer-based rate damping converges to < 0.5 deg/s.
4. Verify autonomous transition to COARSE_SUN (mode 3) when rates are sufficiently low.

#### Step 9: Sun-Pointing Verification {#step-9-sun-pointing-verification}

1. In COARSE_SUN mode, verify spacecraft orients +X towards the Sun.
2. Monitor `att_error` converging towards zero.
3. Verify CSS-derived Sun vector and star camera attitude are consistent.
4. Monitor power generation — confirm `power_gen` increases as Sun-pointing improves.

#### Step 10: Nadir-Pointing Test {#step-10-nadir-pointing-test}

1. Command AOCS to NOMINAL (nadir) mode via `AOCS_SET_MODE` (mode=4).
2. Verify attitude transitions to nadir-pointing.
3. Monitor `att_error` — should converge to < 0.1 deg within 5 minutes.
4. Verify reaction wheel speeds remain within nominal range.
5. Monitor for at least one full orbit to verify stability through eclipse transitions.

**GO/NO-GO Checkpoint 8: ADCS Commissioning Complete**
- Criteria: Nadir-pointing stable, all ADCS components verified.
- Decision: Proceed to nominal transition.

## 9. Transition to Nominal Operations {#9-transition-to-nominal-operations}

### 9.1 Pre-Transition Checklist {#91-pre-transition-checklist}

Before declaring the spacecraft operational, verify the following:

| Item | Check                                    | Status Required           |
|------|------------------------------------------|---------------------------|
| 1    | OBC mode                                 | NOMINAL (mode=0)          |
| 2    | AOCS mode                                | NOMINAL (mode=4)          |
| 3    | Attitude error                           | < 0.5 deg (sustained)     |
| 4    | Battery SoC                              | > 60%                     |
| 5    | Power margin                             | power_gen > power_cons    |
| 6    | All sensors operational                  | Valid readings from all   |
| 7    | All actuators operational                | Responding to commands    |
| 8    | TTC link                                 | Stable at both stations   |
| 9    | GPS position fix                         | Valid and consistent      |
| 10   | Thermal environment                      | All zones within limits   |
| 11   | S12 monitoring enabled                   | All FDIR rules active     |
| 12   | S19 event-actions enabled                | All automated responses active |

### 9.2 Nominal Transition Command Sequence {#92-nominal-transition-command-sequence}

1. Verify pre-transition checklist (all items pass).
2. Flight Director initiates GO/NO-GO poll of all positions.
3. All positions report GO.
4. Enable all S12 monitoring definitions (if not already enabled).
5. Enable all S19 event-action definitions.
6. Command full-rate housekeeping telemetry (1 Hz, all SIDs).
7. Confirm the TM rate ladder is at **LOW (16 kbps)** — the `default_tier` and the rate
   routine operations run at. `ttc.tm_data_rate` (0x0506) = 16000 and `ttc.tm_tier`
   (0x0539) = 1. Do NOT leave the spacecraft commanded to HIGH: that tier is raised per
   dump (NOM-011 / NOM-003) and released afterwards.
8. **Declare the mission phase.** `SYS_SET_MISSION_PHASE(phase=6, flags=0)`
   (Service 8, Subtype 1, func_id 120). Verify `eps.spacecraft_phase` (0x0129) = 6
   and confirm event `MISSION_PHASE_CHANGED` (0x0055) in the log.
9. Record transition time for mission log.

**On the phase declaration.** This is a real telecommand, not bookkeeping. The
on-board phase state machine advances itself only
as far as LEOP (4); COMMISSIONING (5) and NOMINAL (6) are ground declarations.
Until phase 6 is declared:

* `sat.mode` (0x0001) and the console header stay **SAFE** no matter how
  healthy the spacecraft is — the phase gate outranks the FDIR latches in the
  `sc_mode` derivation;
* the advanced fault-propagation model is **disarmed**, as are the two
  phase-gated legacy FDIR rules (`aocs.wheels_enabled`, `aocs.att_error`);
* the propulsion interlock refuses to arm — `prop.yaml` declares
  `min_phase: 6`, so **no manoeuvre is possible at all** (NOM-004 / NOM-013
  will fail at PROP_ARM).

Phase 5 is declared earlier, at LEOP-003 Step 7 — the last card of the LEOP
sequence (the declaration moved out of LEOP-007 in the 2026-08c redesign, so
exactly one card owns each declaration). Going backwards (NOMINAL →
COMMISSIONING or → LEOP) is refused unless the FORCE flag is set (`flags` bit
0 = 1); use it only to unwind a premature declaration, and record the reason.
Phases 0–2 are pre-separation states and are never ground-commandable. The full
gate inventory is in `00_mission_overview.md` §6.0.

**GO/NO-GO Checkpoint 9: Transition to Nominal Operations**
- Criteria: All checklist items passed, all positions report GO.
- Decision: Spacecraft declared operational; LEOP phase complete; phase = 6.

### 9.3 Post-LEOP Activities {#93-post-leop-activities}

After the LEOP phase is complete, the following commissioning activities continue during
the Commissioning phase:

| Activity                           | Timeline        | Responsibility |
|------------------------------------|-----------------|----------------|
| Payload commissioning              | Day 3–7         | PLD operator   |
| First imaging test                 | Day 7–10        | PLD + FD       |
| Orbit determination convergence    | Day 3–5         | AOCS operator  |
| Thermal model correlation          | Day 3–14        | PT operator    |
| FDIR threshold refinement          | Day 7–21        | All positions  |
| Ground station contact optimisation| Day 3–10        | TTC operator   |
| First science imaging              | Day 14–30       | PLD + FD       |

## 10. Emergency Procedures During LEOP {#10-emergency-procedures-during-leop}

### 10.1 No Beacon After Separation {#101-no-beacon-after-separation}

If no beacon is received at the expected first contact:

1. Wait for the next contact window at the alternate station.
2. If still no signal, command a blind uplink of `HK_REQUEST` (SID 11) at the predicted
   spacecraft position.
3. Listen for any RF energy on the expected downlink frequency.
4. If no response after 24 hours of attempts, consider the possibility of antenna
   deployment failure and command the redundant burn wire circuit via blind uplink.

### 10.2 OBC Stuck in the Bootloader {#102-obc-stuck-in-the-bootloader}

If the OBC cannot transition from the bootloader to the application:

1. Request beacon packet via `HK_REQUEST` (SID 11).
2. Check `reboot_count` — if elevated, the application may be crashing.
3. Attempt `OBC_BOOT_APP` (S8.1 func 55) again.
4. If repeated failures, keep the OBC in the bootloader (`OBC_BOOT_INHIBIT`) and investigate.
5. Refer to CTG-021 (`procedures/contingency/obc_bootloader_recovery.md`) for detailed recovery procedure.

### 10.3 Excessive Tumble Rates {#103-excessive-tumble-rates}

If body rates exceed 5 deg/s after detumble attempt:

1. Verify magnetometer readings are valid (not stuck or noisy).
2. The magnetometer is single-string — there is no MAG-B to switch to. A faulty
   unit means B-dot is blind; expect to rely on passive damping, and escalate to
   the spacecraft manufacturer's support team.
3. If rates continue to increase, check for stuck magnetorquer (driving torque in wrong
   direction).
4. As a last resort, power off all AOCS actuators and allow passive magnetic damping
   (requires hours to days).

---

*This document was generated with AI assistance. Source: https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*

---

*End of Document — EOSAT1-UM-LEOP-010*
