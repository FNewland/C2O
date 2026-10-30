# CTG-030: Telecommand Rejection and Verification Failure
**Subsystem:** OBDH / TT&C
**Phase:** ALL (LEOP, COMMISSIONING, NOMINAL)
**Revision:** 1.0 --- new card (author ruling Q22 as amended, 2026-10-30). It
replaces the ops book's temporary CTG-B02 "TC Reject Rate Anomaly" and is built
on the PUS Service 1 verification the simulator actually generates.
**Approved:** Flight Operations Director

**Entry state:** any of
- an S1.2 acceptance failure or an S1.8 execution failure on a telecommand the
  ground believes is valid;
- `obdh.tc_rej_count` (0x0306) incrementing, or event `COMMAND_REJECTED` (0x030B);
- a telecommand with **no** S1 report at all (verification time-out in the MCS
  command log).

## Purpose
Find why telecommands are being refused or are not verified, remove the cause and
restore clean commanding.

**What the simulator reports.** Every telecommand that reaches the on-board
software gets an S1 report, and every refusal carries a 16-bit failure code and a
reason text (the failure notice). The same code is latched in
`obdh.last_tc_error_code` (0x0315), and an on-board refusal also raises event
`COMMAND_REJECTED` (0x030B), whose text names the command, the stage and the code.
The MCS decodes the codes from one shared vocabulary (`GET /api/failure-codes`).

| Report | Stage | Codes and meaning |
|--------|-------|-------------------|
| S1.2 | acceptance | 0x0001 unknown service, 0x0002 unknown subtype, 0x0003 invalid parameter or data length, 0x0004 target subsystem unpowered, 0x0005 uplink not available, 0x0006 not in the bootloader command subset |
| S1.4 | start of execution | S6 memory requests: illegal address, write-protected, bad argument, length over the limit |
| S1.8 | execution | 0x0005 invalid in the current mode, 0x0007 not permitted in the current state, and the subsystem families: 0x0021-0x0028 payload, 0x0A01-0x0A08 gyro calibration, 0x0A20-0x0A22 AOCS mode entry, 0x0B01-0x0B13 propulsion, 0x0C01-0x0C04 mission phase |

Two cases are not rejections:
- **0x0005 at acceptance with no `COMMAND_REJECTED` event.** The uplink had no
  command-channel lock, so the on-board software never saw the telecommand.
- **No S1 report at all.** The telecommand did not reach the spacecraft (link
  problem), or it is a deferred-completion command whose S1.7 only arrives when
  the action ends (gyro calibration, application boot, propulsion burn). Check
  which before re-sending anything.

## Prerequisites
- [ ] Bidirectional S-band link expected (inside a predicted pass)
- [ ] MCS command log available with the S1 reports and failure notices

## Procedure Steps

### Step 1 --- Read the On-Board Command Counters and State
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) --- OBDH housekeeping
**Verify:** `obdh.tc_rx_count` (0x0304) reported within 20s --- record
**Verify:** `obdh.tc_acc_count` (0x0305) reported within 20s --- record
**Verify:** `obdh.tc_rej_count` (0x0306) reported within 20s --- record
**Verify:** `obdh.last_tc_error_code` (0x0315) reported within 20s --- record
**Verify:** `obdh.sw_image` (0x0311) reported within 20s --- 0 = bootloader, 1 = application
**Verify:** `obdh.mode` (0x0300) reported within 20s --- 0 nominal, 1 safe, 2 emergency
**Verify:** `eps.spacecraft_phase` (0x0129) reported within 20s --- record
**Note:** If this request itself gets no reply, the problem is the link, not the
commands: go to CTG-003 (TTC Link Loss Recovery), or CTG-019 if there is no
telemetry at all.
**GO/NO-GO:** Counters and on-board state recorded

### Step 2 --- Check the Uplink Chain
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) --- TT&C housekeeping
**Verify:** `ttc.carrier_lock` (0x0510) == 1 within 20s
**Verify:** `ttc.frame_sync` (0x0512) == 1 within 20s
**Verify:** `ttc.cmd_rx_count` (0x0513) reported within 20s --- record
**Verify:** `ttc.beacon_mode` (0x0521) reported within 20s --- record
**Note:** A telecommand with no S1 report and no change in `ttc.cmd_rx_count`
never reached the spacecraft. No carrier lock or no frame sync means a link
problem: go to CTG-003 (TTC Link Loss Recovery), or CTG-019 if there is no
telemetry either.
**GO/NO-GO:** Uplink locked and the spacecraft is receiving telecommands

### Step 3 --- Classify the Rejection
**Note:** Read the failure notice of each rejected telecommand in the MCS command
log, or the text of event 0x030B. Use the code and the stage:
- **0x0006 at acceptance** with `obdh.sw_image` (0x0311) = 0: the OBC is in the
  bootloader, which accepts only the bootloader subset (S17.1, S9.1, S3 beacon
  HK, S20.1/3 and the S8.1 maintenance functions). Boot the application:
  LEOP-001 Step 5 on first contact, CTG-021 (OBC Bootloader Recovery) after a
  reboot. Inside the 10 s CRC window after OBC_BOOT_APP the OBC is still the
  bootloader: wait for its S1.7 first.
- **0x0004 at acceptance:** the target subsystem's power line is off. Switch the
  line on (EPS_POWER_ON) before re-sending.
- **0x0003 at acceptance:** the telecommand was built wrongly (argument count,
  type or length). Rebuild it from the command builder; do not edit raw hex.
- **0x0001 / 0x0002 at acceptance:** the service or subtype is not implemented.
  Check the command against the catalogue.
- **0x0005 / 0x0007 at execution:** the command is valid but not allowed now.
  The reason text names the state (for example a TM rung refused while
  `ttc.beacon_mode` (0x0521) = 1 --- clear beacon mode first with
  TTC_SET_BEACON_MODE, as in LEOP-001).
- **0x0Axx, 0x0Bxx, 0x0Cxx at execution:** a named interlock. Gyro calibration:
  CTG-029. Propulsion arm: read `prop.arm_inhibit_mask` (0x0B15), NOM-013 or
  CTG-028. Mission phase: `SYS_SET_MISSION_PHASE` guards, LEOP-003 / COM-013.
- **Time-tagged commands:** an S11 command released by the schedule is verified
  when it executes, not when it is uploaded. A rejection at release follows the
  same codes.
**GO/NO-GO:** Cause identified for every rejected telecommand

### Step 4 --- Test Clean Commanding
**TC:** `CONNECTION_TEST` (Service 17, Subtype 1) --- link and verification test
**Verify:** S1.1 acceptance and S1.7 execution complete received within 10s
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27)
**Verify:** `obdh.tc_acc_count` (0x0305) incremented within 20s
**Verify:** `obdh.tc_rej_count` (0x0306) unchanged since the connection test within 20s
**GO/NO-GO:** The spacecraft accepts and verifies a known-good telecommand

### Step 5 --- Re-Send the Corrected Telecommand
**Note:** Re-send the rejected telecommand once, only after its cause has been
removed (Step 3). Never repeat a refused telecommand unchanged: it will be
refused again for the same reason, and repeated refusals of a critical command
hide the real state.
**Verify:** S1.1 and S1.7 received for the re-sent telecommand (no S1.2 / S1.8)
**Verify:** `obdh.last_tc_error_code` (0x0315) unchanged by the re-sent telecommand
**GO/NO-GO:** Commanding restored --- clear the anomaly

## Off-Nominal Handling
- **CONNECTION_TEST gets no reply.** The uplink is not working. Go to CTG-003.
- **Rejections continue with a code nobody can explain.** Stop commanding, record
  the code, the reason text and the command, and escalate to the Flight Director.
  Do not try other commands to work around it.
- **Rejections after an OBC reboot.** The OBC restarts in the bootloader
  (`obdh.sw_image` 0x0311 = 0): every application command is refused 0x0006 until
  the application is booted again (EMG-003, CTG-021).
- **Clock-dependent failures.** A time-tagged command scheduled against a wrong
  on-board clock runs at the wrong time rather than being rejected. If
  `obdh.time_ref` (0x0A13) = 0 or `obdh.time_since_sync_s` (0x0A14) is large,
  resynchronise the clock (NOM-008) before uploading a new schedule.

## Post-Conditions
- [ ] Every rejected telecommand classified with its code and cause
- [ ] Cause removed and the telecommand re-sent once, or deferred with a reason
- [ ] `CONNECTION_TEST` verified (S1.1 + S1.7)
- [ ] Anomaly report raised for any unexplained code

## Exit state
- Commanding restored with clean S1 verification
- On-board state unchanged by this card (it sends only HK requests and a
  connection test)

**NEXT:** resume the interrupted activity or pass plan.
