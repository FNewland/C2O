# NOM-014: End-of-Life Disposal (Perigee Lowering and Passivation)

**Subsystem:** Propulsion / Flight Dynamics / all subsystems
**Phase:** NOMINAL (end of mission)
**Revision:** 1.0 --- new card (author ruling Q3 as amended, 2026-10-30)
**Approved:** Flight Operations Director

## Purpose
Lower the perigee with the existing thruster so that EOSAT-1 re-enters within
5 years even at solar minimum, then passivate the spacecraft: deplete the
propellant, discharge the battery and silence the transmitters.

**Why a burn is needed.** From the 513 km operational orbit (ballistic
coefficient B = 77.9 kg/m2) natural decay takes about 5.0 years at mean solar
activity and about 14 years at solar minimum. The earlier "1.7-4.8 years, no
deorbit capability" was derived at the retired 450 km altitude. Derivation and
budget: `subsystems/prop.yaml`.

| Disposal design | Value |
|-----------------|-------|
| Target orbit | apogee ~513 km, perigee 390 km |
| Disposal delta-V | 34.3 m/s retrograde, in six burns of ~5.72 m/s |
| Residual lifetime | ~1.5 years (mean solar activity), ~4.2 years (solar minimum) |
| Burn location | all six burns at the same orbital position, which becomes the apogee |
| Burn length | ~320-480 s each at end-of-life thrust (0.15-0.22 N) |
| Propellant | ~0.21 kg of the 0.400 kg load |

Each retrograde burn lowers the orbit on the opposite side, so the burn point
stays the apogee and every burn lowers the same perigee. Six burns keep each one
inside the arm interlocks (daylight, attitude error < 2 deg) and inside the
600 s burn watchdog set in Step 3.

## Prerequisites
- [ ] End of mission declared by the Flight Director; imaging campaign closed
      and the last science data downlinked
- [ ] Mission phase 6 (NOMINAL): `eps.spacecraft_phase` (0x0129) = 6 --- the
      propulsion arm interlock needs it
- [ ] `prop.dv_remaining` (0x0B0C) >= 38 m/s (the 34.3 m/s burn plus the 10 %
      dispersion reserve)
- [ ] Propulsion health nominal: `prop.state` (0x0B00) = 0, no latched
      inhibit, tank pressure 6.0-24.0 bar (`prop.tank_pressure` 0x0B01)
- [ ] Battery SoC > 55 %: `eps.bat_soc` (0x0101)
- [ ] Flight Dynamics has the current orbit from GPS (`aocs.gps_alt` 0x0212)
      and a burn plan for six consecutive daylight burns

## Procedure Steps

### Step 1 --- FDS Disposal Plan
**Evaluate:** Choose the burn position (argument of latitude) in daylight and
over a ground station if possible. For each of the six burns: dV, burn epoch,
predicted burn time at the current tank state, and predicted perigee after the
burn (513 -> ~492 -> ~471 -> ~451 -> ~431 -> ~410 -> 390 km).
**Evaluate:** Retrograde attitude: the inertial quaternion that turns the
nominal attitude 180 deg in yaw so that +X body points along the anti-velocity
direction at the burn mid-point. During a 480 s burn the velocity direction
turns ~30 deg in inertial space; holding the mid-point attitude costs about 1 %
of the dV, which the reserve covers.
**Record:** The six burn epochs (CUC), dV per burn, target quaternion.
**GO/NO-GO:** Flight Director authorises the disposal plan

### Step 2 --- Propulsion Health Check
**TC:** `HK_ENABLE(sid=9)` (Service 3, Subtype 5) --- PROP housekeeping
**Verify:** `prop.state` (0x0B00) = 0 within 20s
**Verify:** `prop.tank_pressure` (0x0B01) in range [6.0, 24.0] within 20s
**Verify:** `prop.propellant_mass` (0x0B02) reported within 20s --- record
**Verify:** `prop.dv_remaining` (0x0B0C) >= 38 within 20s
**Verify:** `prop.arm_inhibit_mask` (0x0B15) reported within 20s --- record
**GO/NO-GO:** Propulsion able to deliver the disposal delta-V; otherwise run
CTG-028 first

### Step 3 --- Raise the Burn Watchdog
**TC:** `PROP_SET_LIMITS(att_err_max_deg=2.0, p_min_bar=4.0, catbed_max_c=350.0, t_burn_max_s=600.0)` (Service 8, Subtype 1, func_id 115) --- default watchdog is 300 s
**Note:** At end of life a 5.72 m/s burn lasts up to ~480 s. Only the burn
watchdog changes; the attitude, pressure and catbed abort limits keep their
default values.

### Step 4 --- Power, Preheat and Valves (T-25 min)
**TC:** `EPS_POWER_ON(line_index=8)` (Service 8, Subtype 1) func_id = 19 --- energise the propulsion line
**TC:** `HEATER_THRUSTER(on=1)` (Service 8, Subtype 1) func_id = 42 --- catbed preheat, 12 W
**TC:** `PROP_ISO_OPEN(branch=2)` (Service 8, Subtype 1, func_id 113) --- open both latch-valve branches
**Verify:** `eps.pl_prop` (0x014A) = 1 within 10s
**Verify:** `prop.latch_a_state` (0x0B06) = 1 within 10s
**TC:** `GET_PARAM(param_id=0x0409)` (Service 20, Subtype 3) — `tcs.temp_thruster` (on-demand: no HK SID carries it)
**Verify:** `tcs.temp_thruster` (0x0409) >= 180 within 1500s
**GO/NO-GO:** Catbed hot and propellant path open

### Step 5 --- Retrograde Attitude
**TC:** `AOCS_SET_TARGET_QUAT(q_x=QX, q_y=QY, q_z=QZ, q_w=QW)` (Service 8, Subtype 1, func_id 86) --- the Step 1 retrograde quaternion
**TC:** `AOCS_SET_MODE(mode=9)` (Service 8, Subtype 1) func_id = 0 --- INERTIAL hold
**Verify:** `aocs.mode` (0x020F) = 9 within 120s
**Verify:** `aocs.att_error` (0x0217) < 0.5 within 600s
**Note:** The 180 deg yaw turns the -X thruster face so that the +X thrust
axis points against the velocity. Plan the slew to finish before the arm.

### Step 6 --- Disposal Burn (repeat for each of the six burns)
**TC:** `PROP_SET_BURN(dv_m_s=5.72, direction=1, mode=1, t_start_cuc=0)` (Service 8, Subtype 1, func_id 110) --- retrograde, closed-loop dV cut-off
**Verify:** `prop.burn_time_cmd` (0x0B10) within 10 % of the FDS prediction
**TC:** `PROP_ARM(arm_code=0xA5C3)` (Service 8, Subtype 1) func_id = 108 --- within 300 s of SET_BURN
**Verify:** `prop.state` (0x0B00) = 1 within 10s
**TC:** `PROP_EXECUTE` (Service 8, Subtype 1) func_id = 111 --- start the burn (or time-tag it with S11 as in NOM-004)
**Verify:** `prop.state` (0x0B00) = 2 within 10s
**Monitor:** `prop.thrust_est` (0x0B09), `aocs.att_error` (0x0217),
`prop.burn_time_elapsed` (0x0B11). Abort criteria and the manual abort are
NOM-013 Step 5.
**Verify:** event PROP_BURN_COMPLETE (0x0804) received within 600s
**Verify:** `prop.burn_dv_achieved` (0x0B0F) within 2 % of 5.72
**TC:** `PROP_DISARM` (Service 8, Subtype 1) func_id = 109 --- ARMED -> SAFED; PROP_ARM is refused (0x0B10) unless the system is SAFED
**Verify:** `prop.state` (0x0B00) = 0 within 10s
**Note:** Keep the catbed heater on between burns on consecutive orbits. After
each burn, return to NOMINAL (`AOCS_SET_MODE`, mode 4) for the eclipse and
re-enter the retrograde hold before the next one. Repeat Steps 5 and 6 until
all six burns are complete; the predicted perigee after each burn is in Step 1.
**GO/NO-GO:** Burn achieved; continue with the next burn or Step 7

### Step 7 --- Confirm the Disposal Orbit
**TC:** `HK_REQUEST(sid=12)` (Service 3, Subtype 27) --- GPS navigation, sample over one full orbit
**Verify:** `aocs.gps_alt` (0x0212) minimum over the orbit in range [380, 400]
**Evaluate:** FDS fits the orbit (expected semi-major axis ~6830 km) and computes the residual lifetime at mean
activity and at solar minimum. If the solar-minimum lifetime exceeds 5 years,
plan a trim burn (Step 6 again, smaller dV) before passivation.
**GO/NO-GO:** Perigee at ~390 km; residual lifetime < 5 years at solar minimum

### Step 8 --- Propellant Depletion
**Note:** Fly it from the retrograde hold of Step 5, in daylight, like a disposal burn.
**TC:** `PROP_SET_BURN(dv_m_s=DVREM, direction=1, mode=0, t_start_cuc=0)` (Service 8, Subtype 1, func_id 110) --- DVREM = the current `prop.dv_remaining` reading, retrograde, open loop
**TC:** `PROP_ARM(arm_code=0xA5C3)` (Service 8, Subtype 1) func_id = 108
**TC:** `PROP_EXECUTE` (Service 8, Subtype 1) func_id = 111 --- burn to depletion
**Verify:** `prop.propellant_mass` (0x0B02) < 5 within 900s
**Note:** Burning the residue retrograde lowers the perigee further, which only
shortens the decay. Below 5 g the arm interlock refuses (0x0B03): that residue
cannot be expelled and is recorded. Split the burn if it would exceed the 600 s
watchdog.

### Step 9 --- Propulsion Safing
**TC:** `PROP_DISARM` (Service 8, Subtype 1) func_id = 109 --- ARMED -> SAFED
**TC:** `HEATER_THRUSTER(on=0)` (Service 8, Subtype 1) func_id = 42 --- catbed heater off
**TC:** `PROP_INHIBIT_SET(on=1)` (Service 8, Subtype 1, func_id 116) --- latch the ground inhibit so nothing can fire again
**Verify:** `prop.state` (0x0B00) = 0 within 10s
**Verify:** `prop.arm_inhibit_mask` (0x0B15) bit 9 set within 10s --- inhibit latched
**TC:** `EPS_POWER_OFF(line_index=8)` (Service 8, Subtype 1) func_id = 20 --- de-energise the propulsion line
**Verify:** `eps.pl_prop` (0x014A) = 0 within 10s
**Note:** The model has no pressurant-vent path: the residual tank pressure
(about 9-10 bar) cannot be vented with the existing commands. Record it in the
disposal report as a known limitation.

### Step 10 --- Payload and Attitude Shutdown
**TC:** `PAYLOAD_SET_MODE(mode=0)` (Service 8, Subtype 1) func_id = 26 --- payload OFF
**TC:** `EPS_POWER_OFF(line_index=3)` (Service 8, Subtype 1) func_id = 20 --- payload line off
**TC:** `AOCS_RW_RAMP_DOWN(wheel_idx=255, target_rpm=0)` (Service 8, Subtype 1, func_id 14) --- spin all wheels down
**Verify:** `payload.mode` (0x0600) = 0 within 30s
**Verify:** `aocs.total_momentum` (0x025B) < 0.01 within 120s
**Note:** With the wheels stopped the spacecraft is no longer three-axis
controlled. That is intended: no stored kinetic energy is left in the wheels.

### Step 11 --- Battery Passivation
**TC:** `S2_EPS_CHARGE_REGULATOR(device_id=271, state=0)` (Service 2, Subtype 1) --- charge regulator OFF: the arrays can no longer charge the battery
**Verify:** `eps.bat_soc` (0x0101) falling over the next 30 minutes in sunlight
**Note:** The remaining loads (OBC, receiver, transmitter) now discharge the
battery. At ~20 W it is empty within a few hours; the spacecraft then goes
dark for good. Steps 11 and 12 must be sent in the same pass.

### Step 12 --- RF Silence (last commands)
**TC:** `TTC_BEACON_TX_OFF` (Service 8, Subtype 1) func_id = 98 --- UHF beacon transmitter off
**TC:** `TTC_PA_OFF` (Service 8, Subtype 1) func_id = 67 --- S-band power amplifier off
**TC:** `EPS_TRANSPONDER_TX(on=0)` (Service 8, Subtype 1) func_id = 18 --- S-band transmitter off
**Note:** After this step no telemetry can be received. Loss of signal is the
expected verification. Confirm at the next two scheduled passes that no carrier
is received.
**GO/NO-GO:** Spacecraft silent --- disposal complete

## Deviations
- **A burn aborts.** Follow NOM-013 Step 5 and CTG-028. The partial dV is already
  in the orbit; FDS re-plans the remaining burns from the new orbit.
- **`prop.dv_remaining` below the plan.** Lower the perigee as far as the
  propellant allows and report the achieved residual lifetime. Every 1 m/s of
  retrograde dV lowers the perigee by about 3.6 km.
- **Propulsion unusable at end of life.** The spacecraft decays naturally in
  about 5 years at mean solar activity, 14 at solar minimum. Passivate (Steps
  9-12) and report the non-compliance.
- **Mission phase.** There is no DISPOSAL phase in `SYS_SET_MISSION_PHASE`
  (phases 3-6 only). The spacecraft stays in phase 6 throughout; the propulsion
  interlock needs it.

## Post-Conditions
- [ ] Perigee ~390 km confirmed by GPS and FDS orbit fit
- [ ] Residual lifetime < 5 years at solar minimum
- [ ] Propellant depleted (< 5 g) and propulsion inhibited
- [ ] Battery charge path disabled
- [ ] All transmitters off; loss of signal confirmed at two passes
- [ ] Disposal report filed (orbit, dV used, residual propellant, residual tank pressure)
