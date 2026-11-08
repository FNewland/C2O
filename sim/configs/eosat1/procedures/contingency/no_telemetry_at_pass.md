# CTG-019: No Telemetry at Pass Start

**Category:** Contingency
**Position Lead:** TT&C
**Cross-Position:** Flight Director, EPS/TCS
**Difficulty:** Advanced
**Revision:** 1.1 --- 2026-11-07 (ruling: the card follows the auto-TX hold-down). Step 2's blind HK request also keys the transmitter for 300 s, so the old blind power-on branch (2B) is gone; RSSI limits aligned on -126 dBm (a healthy pass reads about -121 dBm).

## Objective
Recover telemetry downlink when no spacecraft signal is received at the predicted
acquisition-of-signal (AOS) time. This procedure systematically walks through the
RF chain from the ground station through the spacecraft transponder, power amplifier,
and antenna system to identify and resolve the root cause. It covers EPS power line
verification, PA commanding, antenna deployment checks, and transponder switchover.

## Prerequisites
- [ ] Ground station is tracking spacecraft with valid antenna pointing
- [ ] Orbit prediction is current (propagated within last 6 hours)
- [ ] Ground station RF chain verified: uplink transmitter on, receiver locked to expected frequency
- [ ] Doppler pre-compensation applied for current pass geometry
- [ ] At least 8 minutes of predicted pass time remaining
- [ ] Flight Director notified of no-TM condition

## Required Telemetry
| Parameter | ID | Expected Value |
|---|---|---|
| ttc.link_status | 0x0501 | 2 (LOCKED) — currently 0 (NO_LINK) or 1 (ACQUIRING) (triggering condition) |
| ttc.rssi | 0x0502 | > -126 dBm when link is active |
| ttc.link_margin | 0x0503 | > 3.0 dB when link is active |
| ttc.pa_on | 0x0516 | 1 (PA enabled) |
| ttc.pa_temp | 0x050F | < 55 C |
| ttc.tx_fwd_power | 0x050D | Nominal forward power |
| ttc.carrier_lock | 0x0510 | 1 (locked) |
| ttc.bit_sync | 0x0511 | 1 (synchronized) |
| ttc.antenna_deployed | 0x0520 | 1 (deployed) |
| ttc.eb_n0 | 0x0519 | > 10 dB when link is active |
| ttc.ber | 0x050C | < -5 when link is active |
| eps.pl_ttc_tx | 0x0112 | 1 (TX power line energised) |
| eps.bus_voltage | 0x0105 | > 30.9 V |

## Required Commands
| Command | Service | Subtype | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | -- | Request one-shot HK report |
| EPS_POWER_ON | 8 | 1 | 19 | Switch power line ON |
| TTC_PA_ON | 8 | 1 | 66 | Enable power amplifier |
| TTC_PA_OFF | 8 | 1 | 67 | Disable power amplifier |
| TTC_DEPLOY_ANTENNA | 8 | 1 | 69 | Fire burn-wire antenna deployment |
| TTC_SWITCH_REDUNDANT | 8 | 1 | 64 | Switch to redundant transponder |
| TTC_SWITCH_PRIMARY | 8 | 1 | 63 | Switch to primary transponder |
| TTC_SET_TX_POWER | 8 | 1 | 68 | Set transmit power level |
| CONNECTION_TEST | 17 | 1 | -- | S17 connection test (ping) |

## Procedure Steps

### Step 1: Confirm Ground Station Is Nominal
**Action:** Verify ground station antenna is tracking the spacecraft with valid pointing data.
**Action:** Confirm uplink transmitter is powered and set to correct frequency and polarisation.
**Action:** Verify Doppler pre-compensation is applied for current pass geometry.
**Action:** Check for local RFI or adverse weather conditions at the ground station.
**Action:** Confirm receiver is scanning on the expected downlink frequency.
**Note:** If the ground station is found to be at fault (antenna stow, TX off, wrong
frequency), resolve locally. Do not proceed with spacecraft-side recovery until ground
is confirmed nominal.
**GO/NO-GO:** Ground station confirmed nominal — proceed with spacecraft-side diagnosis.

### Step 2: Blind HK Request — It Also Keys the Transmitter
**Note:** Any telecommand the spacecraft accepts energises the `ttc_tx` power line for
300 s (the auto-TX hold-down, `auto_tx_hold_s` in simulation.yaml), so the first
command of a pass is also what turns the downlink on. No telemetry before it is
normal; no telemetry AFTER it is the contingency.
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — blind EPS housekeeping request
**Action:** Wait 30 s and watch the frame counter and the ground station receiver.
**Action:** If telemetry returns: the transmitter was simply not keyed, or its line had
tripped and the command re-energised it. Read why in the HK that arrived: `eps.pl_ttc_tx`
(0x0112), `ttc.pa_on` (0x0516) and the EPS events (an overcurrent trip on `ttc_tx`).
Keep commanding (HK every 60 s): the hold-down lasts 300 s from the last accepted TC.
**Note:** The UHF beacon (HK SID 11, every 30 s) is a separate radio that transmits
whenever the S-band chain is silent. Beacon frames mean the OBC is alive, but they are
not the S-band telemetry this step is waiting for. The beacon carries `ttc.pa_on`
(0x0516): 0 means the power amplifier is off, so go straight to Step 4.
**Action:** If nothing returns: the line is now powered, so it is not the cause. Look
further down the chain: transponder (Step 3), power amplifier (Step 4), antenna (Step 5).
**GO/NO-GO:** S-band telemetry returned after the blind request -> GO `STEP-6` | NO-GO `STEP-3` (or `STEP-4` when the beacon reads `ttc.pa_on` = 0)

### Step 3: Command Transponder Switch (Blind)
**LABEL:** `STEP-3`
**Note:** The primary transponder may have failed. Attempt blind switchover.
The transponders are cold-redundant: the switch is received only by the SELECTED unit.
If the primary is dead it hears nothing and this command is lost; the switch then
happens only on board, when the 24 h command-loss timer expires (Step 7, EMG-004).
It is still worth sending: the receiver may be alive with the loss further down the
transmit chain (the PA, Step 4), and then the switch is executed.
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64) — blind command
**Verify:** Wait 45 s for redundant transponder power-up and frequency lock.
**Verify:** Check ground station receiver for downlink carrier on redundant transponder frequency.
**Action:** If signal detected on redundant: proceed to Step 6 (link verification).
**GO/NO-GO:** Signal detected on the redundant transponder -> GO `STEP-6` | NO-GO `STEP-3B`
**LABEL:** `STEP-3B`
**Note:** Only if the redundant transponder produced no signal either.
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63) — revert to the primary transponder
**Action:** Wait 30 s.
**GO/NO-GO:** If neither transponder produces signal, proceed to Step 4 (PA check).

### Step 4: Command PA ON (Blind)
**LABEL:** `STEP-4`
**Note:** The PA may be disabled. Send blind PA enable command:
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66)
**Verify:** Wait 15 s for PA power-up.
**Verify:** Check ground station receiver for downlink carrier.
**Action:** If signal detected: proceed to Step 6 (link verification).
**GO/NO-GO:** Signal detected after PA ON -> GO `STEP-6` | NO-GO `STEP-4B`
**LABEL:** `STEP-4B`
**Note:** If no signal: the PA enable may not have taken effect. Try cycling the PA:
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1, func_id 67) — wait 10 s
**TC:** `TTC_PA_ON` (Service 8, Subtype 1, func_id 66) — wait 15 s
**Verify:** Check ground station receiver for downlink carrier.
**GO/NO-GO:** If signal detected, proceed to Step 6. If still no signal, proceed to Step 5. -> GO `STEP-6` | NO-GO `STEP-5`

### Step 5: Check Antenna Deployment and Deploy If Needed
**LABEL:** `STEP-5`
**Action:** If the spacecraft is in early mission (post-separation) or the antenna
deployment status is uncertain, the antennas may still be stowed. A stowed antenna
will produce a severely attenuated signal (>20 dB loss).
**GO/NO-GO:** Antenna deployment status genuinely uncertain or known to be stowed -> GO `STEP-5D` | NO-GO `STEP-7`
**LABEL:** `STEP-5D`
**Note:** Send the blind antenna deployment command. The mnemonic is
`TTC_DEPLOY_ANTENNA` (singular) and the function is **69**.
**DANGER — corrected 2026-08b:** this card previously named `func_id 56`.
Func 56 is `OBC_BOOT_INHIBIT`, whose data byte makes the OBC stay in the
bootloader. Sent blind, on a spacecraft that already has no telemetry, on the
hypothesis that its antenna is stowed, it would have INHIBITED AUTO-BOOT — the
one action that turns a recoverable RF problem into a spacecraft that comes up
in the bootloader with the S-band PA inhibited and only HK SID 11 on the UHF
beacon. It was also blind, so nobody would have known.
**TC:** `TTC_DEPLOY_ANTENNA` (Service 8, Subtype 1, func_id 69) — fires the burn-wire for antenna release
**CAUTION:** This is an irreversible, one-shot pyrotechnic command. Only execute if
antenna deployment status is genuinely uncertain or known to be stowed.
**Verify:** Wait 30 s for the deployment mechanism to actuate and the antenna to
extend. If any telemetry is being received, `ttc.antenna_deployed` (0x0520)
goes to 1 and `ttc.antenna_deployment_sensor` (0x0536) reads 2 (DEPLOYED);
`ttc.antenna_deployment_ready` (0x0535) = 0 before the attempt would mean
the pyro continuity is already faulty and the command will not fire.
**Verify:** Check ground station receiver for downlink carrier. Antenna deployment should
produce a dramatic improvement in signal level (15-25 dB gain increase).
**GO/NO-GO:** If signal detected, proceed to Step 6 (link verification). If still no signal after all RF chain checks, proceed to Step 7 (escalation). -> GO `STEP-6` | NO-GO `STEP-7`

### Step 6: Verify Link Quality and Subsystem Health
**LABEL:** `STEP-6`
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — Request TTC housekeeping
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED)
**Verify:** TT&C page (ground): `ttc.rssi` (0x0502) > -126 dBm (nominal signal strength)
**Verify:** TT&C page (ground): `ttc.link_margin` (0x0503) > 3.0 dB
**Verify:** `ttc.pa_on` (0x0516) = 1
**Verify:** `ttc.pa_temp` (0x050F) < 55 C
**Verify:** `ttc.antenna_deployed` (0x0520) = 1
**Verify:** `ttc.carrier_lock` (0x0510) = 1
**Verify:** `ttc.bit_sync` (0x0511) = 1
**Verify:** radio page (ground): `ttc.eb_n0` (0x0519) > 10 dB
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Request EPS housekeeping
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V — confirm no EPS anomaly
**Verify:** `eps.pl_ttc_tx` (0x0112) = 1 — TX power line confirmed ON
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Request OBDH housekeeping
**Verify:** `obdh.mode` (0x0300) — confirm OBC did not enter safe/emergency mode
**Action:** Log which recovery step restored the link:
- Step 2: telemetry returned on the first command (transmitter not keyed, or its line had tripped: see the EPS events)
- Step 3: Primary transponder failure, now on redundant
- Step 4: PA was disabled
- Step 5: Antennas were stowed
**GO/NO-GO:** Link margin > 3 dB, all subsystems nominal — recovery complete. -> GO `STEP-END` | NO-GO `STEP-7`

### Step 7: Escalation — No Link Recovery
**LABEL:** `STEP-7`
**Action:** Log all blind commands sent with timestamps.
**Action:** Notify Flight Director and Mission Director of sustained no-TM condition.
**Action:** Confirm spacecraft autonomous safe mode timer is active (24h no-contact trigger).
**Action:** Schedule next available ground station pass for re-acquisition attempt.
**TC:** `TTC_SET_TX_POWER(level=2)` (Service 8, Subtype 1, func_id 68) — high power mode for the next attempt, for an improved link budget.
**GO/NO-GO:** If no link after two consecutive pass attempts, escalate to EMG-004
(Loss of Communication Emergency).

## Verification Criteria
**LABEL:** `STEP-END`
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED link established)
- [ ] `ttc.rssi` (0x0502) > -126 dBm
- [ ] `ttc.link_margin` (0x0503) > 3.0 dB
- [ ] `ttc.pa_on` (0x0516) = 1
- [ ] `ttc.antenna_deployed` (0x0520) = 1
- [ ] `eps.pl_ttc_tx` (0x0112) = 1 (TX power line ON)
- [ ] Root cause identified and documented
- [ ] If unrecovered: EMG-004 escalation initiated

## Contingency
- If link restores but RSSI < -126 dBm or margin < 1.5 dB: Step down to LOW
  (16 kbps) via `TTC_SET_DATA_RATE(rate=0)` (func_id 65) to gain 9.03 dB of Eb/N0
  plus 1.5 dB of coding gain. LOW is the routine operations rate, so this costs
  nothing but the ability to dump. Investigate antenna or PA degradation.
- If PA cycles on but immediately shuts down: PA may have a thermal or overcurrent
  protection trip. Check `ttc.pa_temp` (0x050F). If > 65 C, PA thermal protection
  is active. Wait for cooldown before retry.
- If antenna deployment command was sent but signal did not improve: Deployment
  mechanism may have failed (burn-wire did not fire, antenna stuck). This is a
  permanent hardware failure. Rely on stub antenna with reduced link budget.
- If OBC is found in SAFE or EMERGENCY mode after link restoration: Execute
  CTG-010 (OBDH Watchdog Recovery) or CTG-011 (OBC Redundancy Switchover) as appropriate before resuming
  nominal operations.
- If signal is intermittent (toggling on/off): Suspect attitude issue causing
  antenna null pattern. Request AOCS telemetry: check `aocs.att_error` (0x0217)
  and `aocs.mode` (0x020F).
