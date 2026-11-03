# EMG-004: Loss of Communication
**Subsystem:** TT&C / Ground Segment
**Phase:** EMERGENCY
**Revision:** 1.2 --- 2026-11-02 (Franz's ruling): FDIR TTC-01 now goes both ways.
Every 24 h without an accepted telecommand the spacecraft toggles to the OTHER
transponder (S8 func 99, TTC_SWITCH_OTHER), so a dead redundant unit is switched
away from too.
Rev 1.1 --- 2026-11-02 (Franz's ruling S4): with both transponders
failed the link is now really cut --- no telecommand is received or executed and
no telemetry leaves the spacecraft, beacon included --- so this card can be
practised as a true loss of communication. Step 5 now describes the autonomy the
spacecraft actually has (FDIR TTC-01: one switch to the redundant transponder
24 h after the last accepted telecommand), not a 6 h cycling sequence it never had.
**Approved:** Flight Operations Director

## Purpose
Recovery procedure when no telemetry has been received from EOSAT-1 for two or more
consecutive pass windows. This procedure defines a structured escalation from ground
station verification through blind commanding and autonomous recovery assessment,
with decision gates at 12h, 24h (the on-board command-loss timer) and 48h elapsed time since last contact.

## Prerequisites
- [ ] Confirmed loss of telemetry for >= 2 consecutive pass windows (~3 hours)
- [ ] Ground station network status page reviewed for planned outages
- [ ] Current Two-Line Element set available (propagated < 24h ago)
- [ ] Blind command stack prepared and validated in simulator
- [ ] Flight Director on console and Emergency Response Team notified

## What the Spacecraft Can and Cannot Do
- The two S-band transponders are **cold-redundant**: only the selected unit is
  powered. A dead selected unit hears nothing and sends nothing, so blind
  commands are only received if the loss is NOT a dead receiver (for example the
  transmitter was switched off, its `ttc_tx` line was shed, or the PA tripped).
  They are still sent on every pass, because the ground cannot tell which case it is.
- With **both** units failed nothing reaches the spacecraft and nothing leaves it,
  not even the beacon. No command can recover this; only a transponder that
  recovers can.
- The only on-board autonomy is the **command-loss timer** (FDIR TTC-01,
  `ttc.time_since_last_tc` 0x053D): 24 h after the last ACCEPTED telecommand it
  raises CMD_LOSS_TIMEOUT (0x0514) and switches to the OTHER transponder
  (S19 ea 4003, S8 func 99), and again at 48 h, 72 h and so on, alternating,
  until a telecommand is accepted. The switch is blind: the spare unit is
  unpowered, so the spacecraft cannot know whether it works. Blind commands that
  are not received do not reset the timer; any accepted telecommand does.
- **Training note (simulator):** the instructor recovers a failed transponder by
  clearing its failure. The instructor pass override is a training aid: with only
  the selected unit dead it lets the team command the switch blind; it cannot
  revive a spacecraft whose two units are dead.

## Procedure Steps

### Step 1 --- Verify Ground Station Infrastructure
**Action:** Confirm operational status of all primary ground stations.
**Check:** Iqaluit (IQ1), Troll (TR1) link status.
**Verify:** Antenna pointing calibration nominal; receiver lock threshold set to minimum (-130 dBm).
**GO/NO-GO:** At least two ground stations fully operational with clear line-of-sight for next pass.

### Step 2 --- Attempt Contact on All Available Ground Stations
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- transmitted blind on each pass.
**Sequence:** Schedule uplink attempts on every visible pass (min elevation 5 deg) across
Iqaluit and Troll in priority order based on maximum elevation.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) within 30s of AOS, and on the TT&C page (ground) `ttc.rssi` (0x0502) > -128 dBm.
**GO/NO-GO:** If telemetry received on any station, exit emergency and transition to EMG-001 assessment. If no response after full ground station rotation, proceed to Step 3. -> GO `STEP-END` | NO-GO `STEP-3`

### Step 3 --- Blind Command on Primary Transponder
**LABEL:** `STEP-3`
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63) --- blind, repeated 3x with 10s spacing.
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- transmitted 15s after switch command.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) within 45s.
**Timing:** Execute at pass with elevation > 20 deg to maximise link margin.
**GO/NO-GO:** If link acquired, proceed to full HK dump. If no response, proceed to Step 4.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-END` | NO-GO `STEP-4` (timeout 45 s)

### Step 4 --- Blind Command on Redundant Transponder
**LABEL:** `STEP-4`
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64) --- blind, repeated 3x with 10s
spacing. (Was annotated Subtype 2; every S8 function-perform is Subtype 1.)
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- transmitted 15s after switch command.
**Verify:** `ttc.link_status` (0x0501) = 2 (LOCKED) within 45s.
**Timing:** Execute at next available high-elevation pass (> 20 deg).
**GO/NO-GO:** If link acquired, remain on redundant transponder and assess primary. If no response, proceed to Step 5.
**BRANCH:** `ttc.link_status == 2` -> GO `STEP-END` | NO-GO `STEP-5` (timeout 45 s)

### Step 5 --- Wait for the On-Board Command-Loss Timer (FDIR TTC-01)
**LABEL:** `STEP-5`
**Action:** Take the time of the last telecommand the spacecraft ACCEPTED (the
last S1.1 in the archive). At that time + 24 h the command-loss timer expires:
the spacecraft raises CMD_LOSS_TIMEOUT (0x0514) and switches itself to the
other transponder (S8 func 99, dispatched on board by S19 ea 4003). If no
telecommand is accepted after that, it switches back at T+48 h, again at T+72 h,
and so on. That is the whole of its communication autonomy: it does not change
beacon power or anything else. Plan the passes immediately after T+24 h and
T+48 h on the best stations; Steps 6 and 7 continue meanwhile.
**Note:** If the selected unit was the dead one --- primary or redundant --- the
link returns on the other unit at the first pass after T+24 h. Send a
telecommand on that pass: an accepted TC stops the timer before it toggles back
to the dead unit 24 h later. If both units are dead, the toggles change nothing
and the link stays cut until a transponder recovers; the toggling then brings
the link back on the recovered unit within 24 h.
**Monitor:** All ground stations in listen-only mode on both primary and redundant frequencies.
**Verify:** Signal detection on any station --- `ttc.rssi` (0x0502) on the TT&C page (station-measured, ground) logged continuously; it shows "no signal" until the spacecraft transmits.
**Duration:** Listen through at least 2 orbit periods (~3.2 hours) after T(last accepted TC) + 24 h.

### Step 6 --- Polar Pass Focused Campaign (12h Threshold)
**Action:** If 12 hours elapsed since last contact, concentrate all resources on high-latitude
stations with optimal geometry.
**Stations:** Iqaluit and Troll --- both provide near-polar pass coverage every ~95 min.
**Note:** Alternate between the two transponders on successive passes: send the
primary select on one pass and the redundant select on the next.
**TC:** `TTC_SWITCH_PRIMARY` (Service 8, Subtype 1, func_id 63) --- odd-numbered passes
**TC:** `TTC_SWITCH_REDUNDANT` (Service 8, Subtype 1, func_id 64) --- even-numbered passes
**TC:** `OBC_SET_MODE(mode=2)` (Service 8, Subtype 1, func_id 50) --- blind emergency mode command.
(Was annotated Subtype 3, which is not an S8 subtype this suite dispatches.)
**Verify:** Any downlink signal within pass window.
**GO/NO-GO:** If contact restored, proceed to EMG-001 for safe mode recovery.

### Step 7 --- Emergency Network Escalation (24h Threshold)
**Action:** Request support from partner agency ground stations (ESA ESTRACK, NASA NEN).
**Expand:** Add Malindi, Maspalomas, and South Point stations to tracking schedule.
**Note:** Continue the Step 6 blind commanding rotation on all passes --- the
commands are `TTC_SWITCH_PRIMARY` (func 63) and `TTC_SWITCH_REDUNDANT`
(func 64), alternating. Nothing new is sent here, so this step carries no
`**TC:**` line of its own.
**Notify:** ESA Space Debris Office of potential uncontrolled spacecraft status.
**GO/NO-GO:** If 24h exceeded with no contact, convene Anomaly Review Board.

### Step 8 --- Extended Loss Assessment (48h Threshold)
**Action:** If 48 hours elapsed with no signal on any station or frequency:
**Assess:** Spacecraft may be in under-voltage lockout or unrecoverable tumble.
**Radar:** Request space surveillance radar tracking to confirm orbit and attitude state.
**Plan:** Develop long-term recovery plan assuming spacecraft will exit safe mode only when
power-positive conditions resume (sunlit orbit phase with favourable beta angle).
**Monitor:** Maintain passive listening campaign for minimum 30 days.

## Decision Tree Summary
| Elapsed Time | Action | Escalation |
|---|---|---|
| 0--12h | Cycle all ground stations, blind command both transponders | Flight Director |
| 12--24h | Polar pass focused campaign, blind emergency mode command; plan the passes after the TTC-01 timer | Mission Manager |
| 24h + 2 orbits | On-board TTC-01 switches to the other transponder (and back at 48 h): listen (Step 5) | Emergency Response Team |
| 24--48h | Emergency network escalation, partner agency support | Anomaly Review Board |
| >48h | Extended loss assessment, radar tracking, 30-day listen | Programme Director |

## Off-Nominal Handling
- If ground station hardware fault confirmed: reroute to backup antenna feed; contact station provider for emergency maintenance.
- If spacecraft detected by radar but no RF signal after the T+24 h and T+48 h TTC-01 switches (both units tried): assume both transponders have failed. No command can reach the spacecraft and it transmits nothing (beacon included); keep listening for a transponder recovery.
- If telemetry received but corrupt/fragmented: step the TM rate ladder down to LOW
  (`TTC_SET_DATA_RATE(rate=0)`, func_id 65 — 16 kbps BPSK conv(7,1/2)+RS, which is both
  9.03 dB of rate margin and 1.5 dB of extra coding gain relative to HIGH). If that
  still does not lock, command beacon mode (`TTC_SET_BEACON_MODE(on=1)`, func_id 70):
  it forces the SAFE rung (ex-BEACON) — 1 000 bps, 1 kBd, ~3.1 kHz occupied bandwidth — which is
  the narrowest, most robust waveform the spacecraft has. Re-configure the ground
  demodulator to 1 kBd before expecting lock.
- If spacecraft orbit decayed significantly from predicted: re-acquire TLE from space surveillance network before next pass attempt.

## Post-Conditions
**LABEL:** `STEP-END`
- [ ] Two-way communication re-established on at least one transponder
- [ ] `ttc.mode` (0x0500) confirmed in NOMINAL or SAFE
- [ ] `ttc.link_status` (0x0501) = 2 (LOCKED) with stable `ttc.rssi` (0x0502) > -120 dBm
- [ ] Full housekeeping dump (all SIDs 1--6) received and reviewed
- [ ] Root cause of communication loss identified or investigation initiated
- [ ] Transition to EMG-001 for staged recovery if spacecraft was in autonomous safe mode
