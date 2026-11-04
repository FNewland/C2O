# CTG-021: OBC Bootloader Recovery

**Category:** Contingency
**Position Lead:** FDIR / Systems
**Cross-Position:** Flight Director
**Difficulty:** Advanced

## Objective
Recover the OBC when it is stuck in bootloader mode after a crash or unexpected
reboot. In bootloader mode, only the beacon HK structure (SID 11) is available,
and it is emitted from the dedicated bootloader APID (0x002) — distinct from the
application APID (0x001). No TM stores exist in bootloader mode; attitude,
thermal, and payload operations are all offline. Ground's first indication of
bootloader entry is that all application-APID traffic ceases and only a SID 11
beacon remains on the bootloader APID. The full application software is not running, meaning
no payload operations, no scheduled commands, and reduced FDIR capability. This
procedure verifies the bootloader state, assesses the reboot cause, attempts to
boot the application software, and if that fails, performs memory integrity checks
before considering a memory reload or OBC unit switchover.

## Prerequisites
- [ ] TT&C link active — `ttc.link_status` (0x0501) = 2 (LOCKED)
- [ ] OBC confirmed in bootloader — `obdh.sw_image` (0x0311) = 0
- [ ] Flight Director notified
- [ ] Bootloader is responding to HK requests (beacon SID 11 received)
- [ ] Previous `obdh.reboot_count` (0x030A) value known from last nominal pass

## Required Telemetry
| Parameter | ID | Expected Value |
|---|---|---|
| obdh.sw_image | 0x0311 | 0 (bootloader) — triggering condition |
| obdh.last_reboot_cause | 0x0316 | Record value (1=commanded, 2=watchdog, 3=memory, 4=switchover) |
| obdh.reboot_count | 0x030A | Record value — compare with last known |
| obdh.active_obc | 0x030C | Which OBC unit is active (0=A, 1=B) |
| obdh.mode | 0x0300 | Current mode (limited in bootloader) |
| obdh.temp | 0x0301 | OBC temperature within limits (< 50 C) |
| obdh.cpu_load | 0x0302 | Record value |
| obdh.boot_count_a | 0x0317 | OBC-A total boot count |
| obdh.boot_count_b | 0x0318 | OBC-B total boot count |
| obdh.bus_a_status | 0x030F | 0 (OK) or 1 (ERROR) |
| obdh.bus_b_status | 0x0310 | 0 (OK) or 1 (ERROR) |
| eps.bus_voltage | 0x0105 | > 30.9 V |
| ttc.link_status | 0x0501 | 2 (LOCKED) |

## Required Commands
| Command | Service | Subtype | Func ID | Description |
|---|---|---|---|---|
| HK_REQUEST | 3 | 27 | -- | Request one-shot HK report |
| OBC_BOOT_APP | 8 | 1 | 55 | Boot application software from bootloader |
| OBC_BOOT_INHIBIT | 8 | 1 | 56 | Inhibit/allow auto-boot |
| MEM_CHECK | 6 | 9 | -- | Check memory CRC integrity |
| MEM_LOAD | 6 | 2 | -- | Load data to onboard memory |
| OBC_SWITCH_UNIT | 8 | 1 | 53 | Switch to redundant OBC (last resort) |
| OBC_REBOOT | 8 | 1 | 52 | Force OBC reboot |

## Procedure Steps

### Step 1: Confirm Bootloader State and Record Diagnostics
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Request OBDH housekeeping
**Note:** In bootloader mode, only SID 11 (beacon) may respond. If SID 4 does not
return, request SID 11 instead.
**Verify:** `obdh.sw_image` (0x0311) = 0 (bootloader, application not running)
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (on-demand: no HK SID carries it)
**Verify:** `obdh.last_reboot_cause` (0x0316) — record value:
- 0 = none (unexpected — should not be in bootloader without cause)
- 1 = commanded (operator-initiated reboot)
- 2 = watchdog (application crashed, watchdog triggered)
- 3 = memory (memory error detected, boot aborted)
- 4 = switchover (OBC unit switchover occurred)
**Verify:** `obdh.reboot_count` (0x030A) — record and compare with last known value
**Verify:** `obdh.active_obc` (0x030C) — record which OBC unit is active
**TC:** `GET_PARAM(param_id=0x0301)` (Service 20, Subtype 3) — `obdh.temp` (on-demand: no HK SID carries it)
**Verify:** `obdh.temp` (0x0301) — within limits (< 50 C)
**Verify:** `obdh.cpu_load` (0x0302) — record (should be low in bootloader)
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — Request EPS housekeeping
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V — confirm power is stable
**Note:** If bus voltage is marginal (< 31.5 V), a brown-out may have caused the crash.
Address EPS before attempting application boot.
**GO/NO-GO:** Bootloader state confirmed, diagnostics recorded — proceed to assessment.

### Step 2: Assess Reboot Cause and Determine Recovery Path
**Action:** Based on `obdh.last_reboot_cause`, follow the appropriate path:

**If cause = 2 (watchdog) or cause = 1 (commanded):**
- Application image is likely intact but crashed during execution.
- Proceed to Step 3 (attempt application boot).

**If cause = 3 (memory):**
- Application image may be corrupt. Boot was aborted by bootloader CRC check.
- Proceed to Step 4 (memory integrity check before boot attempt).

**If cause = 4 (switchover):**
- Normal condition after OBC unit switchover. Image should be intact.
- Proceed to Step 3 (attempt application boot).

**If cause = 0 (none):**
- Unexpected state. Proceed cautiously to Step 4 (memory check first).

**Action:** Record assessment rationale in operations log.
**GO/NO-GO:** Assessment complete — follow appropriate path.
**TC:** `GET_PARAM(param_id=0x0316)` (Service 20, Subtype 3) — `obdh.last_reboot_cause` (on-demand: no HK SID carries it)
**BRANCH:** `obdh.last_reboot_cause == 3` -> GO `STEP-4` | NO-GO `STEP-2B` (timeout 10 s)
**LABEL:** `STEP-2B`
**BRANCH:** `obdh.last_reboot_cause == 0` -> GO `STEP-4` | NO-GO `STEP-3` (timeout 10 s)

### Step 3: Attempt Application Boot
**LABEL:** `STEP-3`
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — Command application boot
**Note:** The bootloader will attempt to load and start the application software.
This takes approximately 10-30 seconds.
**Verify:** Wait 30 s for application initialization.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Request OBDH housekeeping
**Verify:** `obdh.sw_image` (0x0311) = 1 (application running)
**TC:** `GET_PARAM(param_id=0x030B)` (Service 20, Subtype 3) — `obdh.sw_version` (on-demand: no HK SID carries it)
**Verify:** `obdh.sw_version` (0x030B) — correct application version
**Verify:** `obdh.mode` (0x0300) — OBC should enter SAFE or NOMINAL mode
**Verify:** `obdh.cpu_load` (0x0302) < 80% — normal post-boot load
**Action:** If application booted successfully:
- Proceed to Step 3a (clear beacon mode), then Step 7 (full system verification).
**Action:** If `obdh.sw_image` still = 0 after 30 s:
- Application failed to boot. Proceed to Step 4 (memory integrity check).
**GO/NO-GO:** Boot succeeded — proceed to Step 3a. Boot failed — proceed to Step 4.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-4` (timeout 30 s)

### Step 3a: Clear Beacon Mode and Restore the LOW Rung
**LABEL:** `STEP-3A`
**Note:** Booting the application does **NOT** clear beacon mode. Entering the
bootloader latched `ttc.beacon_mode` (0x0521) = 1, and it stays latched after the
application is running. While it is latched, the SAFE rung (1 000 bps, ex-BEACON) is the ONLY permitted
tier: every `TTC_SET_DATA_RATE` is refused with an S1.8 execution failure, error
`0x0007`, whose failure notice reads "TM rate is forced to the beacon tier in beacon
mode (LOW refused)". The same text is raised as S5 event `0x030B COMMAND_REJECTED`.
**TC:** `TTC_SET_BEACON_MODE(on=0)` (Service 8, Subtype 1, func_id 70) — Clear beacon mode
**Verify:** S1.1 acceptance + S1.7 execution complete within 5 s
**Verify:** `ttc.beacon_mode` (0x0521) = 0 within 10 s
**TC:** `TTC_SET_DATA_RATE(rate=0)` (Service 8, Subtype 1, func_id 65) — Select the routine operations rung
**Verify:** S1.7 execution complete — NOT an S1.8
**Verify:** `ttc.tm_data_rate` (0x0506) = 16000 and `ttc.tm_tier` (0x0539) = 1 (LOW)
**Action:** Re-configure the ground demodulator from 1 kBd to 16 kBd before expecting
SIDs 1–6; the beacon demodulator will not lock 16 kbps.
**Note:** Gate order on the ladder — **beacon mode off** → LOW selectable; **antenna
deployed** (func 69) **+ DOWNLINK mode on** (func 79) → HIGH
selectable (10 deg elevation is a ground rule: the MCS warns, the spacecraft does not refuse). All three on-board gates report error `0x0007`, so read the failure notice, not the
code. Full list in `docs/LINK_BUDGET_AND_RATES.md` §6.3.
**GO/NO-GO:** Beacon mode cleared and downlink at LOW — proceed to Step 7.
**BRANCH:** `ttc.beacon_mode == 0` -> GO `STEP-7` | NO-GO `STEP-END` (timeout 10 s)

### Step 4: Inhibit Auto-Boot and Check Memory Integrity
**LABEL:** `STEP-4`
**Note:** Inhibit auto-boot to prevent a boot loop:
**TC:** `OBC_BOOT_INHIBIT(inhibit=1)` (Service 8, Subtype 1, func_id 56)
**Verify:** OBC remains in bootloader (no automatic boot attempts).
**Note:** Perform memory CRC check on the application image region:
**TC:** `MEM_CHECK(memory_id=1, address=0x00000000, length=0x00100000)` (Service 6, Subtype 9)
**Note:** Address and length refer to the application image in EEPROM. Adjust based
on the actual memory map.
**Verify:** Wait for memory check result report.
**Action:** Assess CRC result:
- **CRC matches expected:** Image is intact. Boot failure may be transient.
  Proceed to Step 5 (retry boot).
- **CRC does NOT match:** Image is corrupt. Proceed to Step 6 (memory reload).
**GO/NO-GO:** Memory check complete — CRC matches the expected value -> GO `STEP-5` | NO-GO `STEP-6`

### Step 5: Retry Application Boot After Memory Verification
**LABEL:** `STEP-5`
**TC:** `OBC_BOOT_INHIBIT(inhibit=0)` (Service 8, Subtype 1, func_id 56) — Disable boot inhibit
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55) — Command application boot
**Verify:** Wait 30 s for application initialization.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Request OBDH housekeeping
**Verify:** `obdh.sw_image` (0x0311) = 1 (application running)
**TC:** `GET_PARAM(param_id=0x030B)` (Service 20, Subtype 3) — `obdh.sw_version` (on-demand: no HK SID carries it)
**Verify:** `obdh.sw_version` (0x030B) — correct application version
**Action:** If boot succeeds: proceed to Step 3a (clear beacon mode), then Step 7 (full system verification).
**Action:** If boot fails again: proceed to Step 6 (memory reload or OBC switch).
**GO/NO-GO:** Boot succeeded — go to Step 3a, then Step 7. Boot failed again — proceed to Step 6.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-6` (timeout 30 s, max 1)

### Step 6: Escalate — Memory Reload or OBC Switchover
**LABEL:** `STEP-6`
**TC:** `OBC_BOOT_INHIBIT(inhibit=1)` (Service 8, Subtype 1, func_id 56) — Ensure boot inhibit is active
**GO/NO-GO:** Pass time permits a memory reload (Option A); otherwise Option B -> GO `STEP-6A` | NO-GO `STEP-6B`

**Option A — Memory Reload (if pass time permits):**
**LABEL:** `STEP-6A`
**Note:** Upload application software image via memory load commands:
**TC:** `MEM_LOAD(memory_id=1, address=ADDR, data=BLOCK)` (Service 6, Subtype 2)
**Note:** Full image upload is a lengthy process and may require multiple contacts
depending on image size and uplink data rate.
**TC:** `MEM_CHECK(memory_id=1, address=ADDR, length=LEN)` (Service 6, Subtype 9) — After upload, verify image
**Verify:** CRC matches expected value.
**Note:** Disable boot inhibit and boot:
**TC:** `OBC_BOOT_INHIBIT(inhibit=0)` (Service 8, Subtype 1, func_id 56)
**TC:** `OBC_BOOT_APP` (Service 8, Subtype 1, func_id 55)
**Verify:** `obdh.sw_image` (0x0311) = 1 within 30 s.
**Action:** If boot succeeds, proceed to Step 3a (clear beacon mode), then Step 7.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-6B` (timeout 30 s, max 1)

**Option B — OBC Unit Switchover (if memory reload not feasible):**
**LABEL:** `STEP-6B`
**Note:** Command switchover to redundant OBC:
**TC:** `OBC_SWITCH_UNIT` (Service 8, Subtype 1, func_id 53)
**CAUTION:** This is a critical command. The active OBC will power down and the
redundant unit will boot from its own EEPROM image.
**Verify:** Wait 60 s for redundant OBC to boot.
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Request OBDH housekeeping
**Verify:** `obdh.active_obc` (0x030C) reflects the new unit
**Verify:** `obdh.sw_image` (0x0311) = 1 (application running on backup)
**Action:** If backup OBC boots successfully, proceed to Step 3a (clear beacon mode), then Step 7.

**GO/NO-GO:** Application restored via reload or switchover — proceed to Step 3a, then Step 7.
If neither option succeeds, escalate to EMG-003.
**BRANCH:** `obdh.sw_image == 1` -> GO `STEP-3A` | NO-GO `STEP-END` (timeout 30 s, max 1)

### Step 7: Verify All Subsystems Nominal
**LABEL:** `STEP-7`
**Note:** Request HK from all subsystems:
**TC:** `HK_REQUEST(sid=1)` (Service 3, Subtype 27) — EPS
**TC:** `HK_REQUEST(sid=2)` (Service 3, Subtype 27) — AOCS
**TC:** `HK_REQUEST(sid=3)` (Service 3, Subtype 27) — TCS
**TC:** `HK_REQUEST(sid=6)` (Service 3, Subtype 27) — TTC
**TC:** `HK_REQUEST(sid=5)` (Service 3, Subtype 27) — Payload
**TC:** `HK_REQUEST(sid=4)` (Service 3, Subtype 27) — Platform/OBDH housekeeping
**Verify:** All five HK responses received within 30 s.
**Verify:** `eps.bus_voltage` (0x0105) > 30.9 V
**Verify:** `aocs.mode` (0x020F) — record and restore if needed
**Verify:** `payload.mode` (0x0600) — record and restore if needed
**Verify:** `obdh.mode` (0x0300) — if SAFE, consider restoring to NOMINAL:
`OBC_SET_MODE(mode=0)` (func_id 50)
**Note:** Verify onboard time against ground reference:
**TC:** `SET_TIME(cuc_seconds=T_corrected)` (Service 9, Subtype 1) — if drift > 5 s, synchronise the onboard time with this command
**Action:** Log recovery event:
- Reboot cause and count
- Number of boot attempts required
- Memory check results (if performed)
- Time spent in bootloader
- Application version confirmed
- Post-recovery subsystem states
**GO/NO-GO:** All subsystems nominal, application running — recovery complete.

## Verification Criteria
**LABEL:** `STEP-END`
- [ ] `obdh.sw_image` (0x0311) = 1 (application running)
- [ ] `obdh.sw_version` (0x030B) = correct application version
- [ ] `obdh.mode` (0x0300) = 0 (NOMINAL) or 1 (SAFE) as appropriate
- [ ] `obdh.cpu_load` (0x0302) < 80%
- [ ] All subsystem HK reports received and nominal
- [ ] `obdh.reboot_count` (0x030A) documented
- [ ] No subsequent unexpected reboots for at least 30 minutes
- [ ] Recovery event documented in anomaly log

## Contingency
- If OBC reboots again during application boot attempt: Immediately command
  `OBC_BOOT_INHIBIT(inhibit=1)` (func_id 56) to prevent boot loop. If
  `obdh.reboot_count` increments by > 3 within 1 hour, suspect boot loop.
  Escalate to EMG-003 (Emergency OBC Reboot).
- If bootloader itself becomes unresponsive (no HK at all): This is a critical
  failure. No software recovery is possible on this OBC unit. Switch to redundant
  OBC immediately: `OBC_SWITCH_UNIT` (func_id 53).
- If memory reload fails due to uplink errors: Verify TTC link quality. Retry
  failed blocks. Hold the downlink at LOW (16 kbps, BPSK conv(7,1/2)+RS — the
  routine operations rung and the most robust commandable one):
  `TTC_SET_DATA_RATE(rate=0)` (func_id 65). Note the TELECOMMAND uplink is a
  fixed 4 kbps and is not affected by the TM rate ladder; what LOW buys here is
  a quieter, better-locked downlink for verifying each block.
- If backup OBC also fails to boot application: Both application images may be
  corrupt. This requires a double memory reload — one per OBC unit. Coordinate with
  ground software team and plan multi-contact upload campaign.
- If AOCS reverted to DETUMBLE after OBC reboot: Execute CTG-002 (AOCS Anomaly
  Recovery) to restore pointing after OBC is confirmed stable.
- If memory check reveals corruption in the bootloader region: Do NOT attempt to
  write to the bootloader region. Switch to redundant OBC. Bootloader corruption
  is not safely recoverable from ground.
