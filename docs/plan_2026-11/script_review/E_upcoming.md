# E — Upcoming videos: planning entries with the three reflections built in (2026-11-06)

Scope: the scripts **not yet written** — the thirteen commissioning cards (COM-001 … COM-013),
CTG-001, and five concept videos (link budget, energy balance, attitude/quaternions, FDIR
S12→S19 chain, CCSDS packet + PUS services). No storyboard was edited. Proposed ids follow
the existing pattern (`V-OPS-1x` for card videos, `V-CON-0x` for concept explainers); rename
freely.

How to read each entry:

* **Steps** — 3–6 steps, each with the screen it films. MCS rail labels as they appear in
  `smo_mcs/static/modern/mcs.js`: OVR, EPS, TCS, AOC, TTC, PLD, PRP, OBD | CMD, FDR, PRC, TRD,
  PUS, MAN.
* **Acronyms** — the ones the narration will meet, by code. Expansions and spoken short
  forms are in the **Acronym table** directly below (register entries copied from
  `video/lexicon/acronyms.yaml`; anything marked † is new and is in **Register additions**
  at the end). Expand once per video, per language.
* **Per step** — deeper explanation (source file § heading) · animation idea and route ·
  scope (Team or position keys from `mcs/positions.yaml`). Ch. 21 positions are the *design*
  seats (Power Engineer, AOCS Engineer, Communications Engineer, Mission Operations Engineer,
  Ground Segment Engineer, Software Engineer); I cite them where the explanation is a design
  topic.
* **Audience** — `team`, or one/two positions. No instructor-audience videos.
* **Contradictions / graded** — what on the card would disagree with the simulator, and
  what must not be mirrored because it is graded (WB-5.4-Q, or a scored scenario's
  `expected_responses` / `harmful_commands`).

Scored-scenario check (method: a scenario is scored when an `expected_responses` entry
carries `tc:` or `state:` — `scenario_scoring.py`; matches the "34 of 38" in
INSTRUCTOR_CONSOLE_DESIGN.md). **Not scored**: `eps_solar_panel_loss`, `gs_rf_degradation`,
`nominal_ops`, `prop_burn_eclipse_power`. Every other scenario is scored, including the ones
that overlap these cards: `eps_undervoltage`, `eps_progressive_load_shed`,
`debris_impact_hermes3`, `sequential_checkout`, `aocs_star_tracker_failure`,
`transponder_failure`, `ttc_no_tm_at_aos`, `ttc_pa_overheat`, `obc_watchdog`,
`aocs_wheel_failure` (harmful: re-enabling RW3), `aocs_sensor_cascade`.

WB-5.4-Q: the repo holds only its six categories (voice-loop discipline, MCS UI navigation,
telemetry limits and SIDs, procedure structure, anomaly response, pass-timing arithmetic);
the questions and solutions are in the printed instructor pack. Rule applied below: no
embedded video question may be a limits/SID lookup, a pass-timing sum or an anomaly-response
call in the form a quiz item would take; card videos stay on "what this card proves".

---

## Acronym table (every acronym these videos will speak)

Register entries (from `acronyms.yaml`; EN / FR / short EN / short FR):

| Code | EN | FR | Short EN | Short FR |
|---|---|---|---|---|
| COM | commissioning procedure | procédure de mise en service | com | com |
| CTG | contingency procedure | procédure de contingence | contingency | contingence |
| NOM | nominal procedure | procédure nominale | nom | nom |
| LEOP | launch and early orbit phase | phase de lancement et de début d’orbite | lee-op | Léop |
| AOCS / SCAO | attitude and orbit control (system) | (système de) contrôle d’attitude et d’orbite | A-O-C-S | S-C-A-O |
| ADCS | attitude determination and control | détermination et contrôle d’attitude | A-D-C-S | A-D-C-S |
| EPS | electrical power | sous-système énergie | E-P-S | E-P-S |
| TCS | thermal control | contrôle thermique | T-C-S | T-C-S |
| TTC (TT&C) | telemetry, tracking and command | télémesure, poursuite et télécommande | T-T-C | T-T-C |
| OBC | on-board computer | ordinateur de bord | O-B-C | O-B-C |
| OBDH | on-board data handling | gestion de bord | O-B-D-H | O-B-D-H |
| FDIR | fault detection, isolation and recovery | détection, isolation et reprise des pannes | F-DIR | F-D-I-R |
| MCS | mission control system | système de contrôle de mission | M-C-S | M-C-S |
| PCDU | power conditioning and distribution unit | unité de conditionnement et de distribution de puissance | P-C-D-U | P-C-D-U |
| BCR | battery charge regulator | régulateur de charge batterie | B-C-R | B-C-R |
| LCL | latching current limiter | limiteur de courant à verrouillage | L-C-L | L-C-L |
| MPPT | maximum power point tracking | suivi du point de puissance maximale | M-P-P-T | M-P-P-T |
| MTQ | magnetorquer | magnéto-coupleur | M-T-Q | M-T-Q |
| CSS | coarse sun sensor | capteur solaire grossier | C-S-S | C-S-S |
| RW | reaction wheel | roue de réaction | R-W | R-W |
| OBCP | on-board control procedure | procédure de contrôle de bord | O-B-C-P | O-B-C-P |
| PUS | packet utilisation standard | norme d’utilisation des paquets | P-U-S | P-U-S |
| TM / TC | telemetry / telecommand | télémesure / télécommande | T-M / T-C | T-M / T-C |
| HK | housekeeping | données de servitude | H-K | H-K |
| SID | structure identifier | identifiant de structure | S-I-D | S-I-D |
| APID | application process identifier | identifiant de processus applicatif | A-P-I-D | A-P-I-D |
| CCSDS | Consultative Committee for Space Data Systems | Comité consultatif pour les systèmes de données spatiales | C-C-S-D-S | C-C-S-D-S |
| CUC | CCSDS unsegmented time code | code temporel non segmenté du CCSDS | C-U-C | C-U-C |
| OBT | on-board time | temps de bord | O-B-T | O-B-T |
| S1, S2 … S20 | service n + what it does (S1 request verification, S2 device access, S3 housekeeping, S5 event reporting, S8 function management, S12 on-board monitoring, S13 large data transfer, S19 event-action, S20 parameter management) | service n, … (vérification des requêtes, accès aux équipements, données de servitude, rapport d’événements, gestion des fonctions, surveillance bord, transfert de grands volumes, événement-action, gestion des paramètres) | S one … | S un … |
| AOS / LOS | acquisition / loss of signal | acquisition / perte du signal | A-O-S / L-O-S | A-O-S / L-O-S |
| RF | radio frequency | radiofréquence | R-F | R-F |
| EIRP | equivalent isotropic radiated power | puissance isotrope rayonnée équivalente | E-I-R-P | P-I-R-E |
| BER | bit error rate | taux d’erreur binaire | B-E-R | B-E-R |
| FEC | forward error correction | correction d’erreurs directe | F-E-C | F-E-C |
| LEO / SSO | low Earth orbit / Sun-synchronous orbit | orbite basse / orbite héliosynchrone | L-E-O / S-S-O | L-E-O / S-S-O |
| LTAN | local time of the ascending node | heure locale du nœud ascendant | L-TAN | L-T-A-N |
| TLE | two-line element set | jeu d’éléments à deux lignes | T-L-E | T-L-E |
| SoC / DoD | state of charge / depth of discharge | état de charge / profondeur de décharge | said in full | dit en entier |
| CDF | concurrent design facility | plateau de conception concourante | C-D-F | C-D-F |
| PRC | (rail label) the procedures page | la page des procédures | P-R-C | P-R-C |
| not expanded | GO, NO-GO, SAFE, LOW, HIGH, NONE, DETUMBLE, COARSE_SUN, GPS, EOSAT-1 | | | |

† New codes these videos need are listed once, with EN/FR/short forms, under **Register
additions** at the end of this file.

---

## Commissioning cards (order = `procedure_index.yaml` definitive order)

Common to all thirteen: start from breakpoint `card-COM-0xx`, `fresh_stack: sim`, position
in the URL set to the card's executing seat (not `flight_director`) so the command builder
refuses what that seat cannot send — the refusal is itself a teaching beat. Each card has a
`WB-5.6-C0xx` confirm-each-step sheet **except COM-003, COM-004 and COM-013** (no sheet
exists — ties for those three must be the card only, or new sheets).

**Breakpoint risk (all of COM-001, COM-002, COM-004 Step 1b).** Their entry state is the
LEOP COARSE_SUN hold on magnetorquers alone, which the model does not hold
(AOCS_COARSE_SUN_MTQ_ONLY.md: error swings 3°–100°, rates past 0.5 °/s in eclipse). COM-001
Step 3/5 ("stable sun-pointing", power generation 40–90 W) and COM-004's "rates < 0.5 deg/s"
prerequisite will show the swing on screen. Hold these three like V-OPS-07/09 until the AOCS
fix, or film only sunlit windows and say nothing about the hold quality.

### V-OPS-10 — COM-001 EPS Checkout

Purpose: establish the power baselines — bus follows battery, eclipse discharge, sunlit
recharge, positive orbit-average energy balance, a load transient.

| # | Step (screen) | Deeper explanation (source) | Animation (route) | Scope |
|---|---|---|---|---|
| 1 | Bus and battery baseline, Steps 1–2 (EPS page, SID 1 values; PRC card) | Unregulated bus that follows the battery, 8-cell Li-ion window 24–33.6 V (ch. 09 § 9.1.3 Architecture types; § 9.3.1 Li-ion cell chemistry) | Battery voltage-vs-SoC curve with the 33.4 V cap and the yellow band drawn on it (Manim) | eps_tcs (thresholds) + Team (card mechanics: TC → Verify → GO/NO-GO) |
| 2 | Sunlit generation, Step 3 (EPS power flow) | Array output vs sun angle and wing area (ch. 09 § 9.1.1 Solar cell physics, § 9.1.2 Body-mounted vs deployable) | powerflow.js replay of a sunlit arc, line widths growing with cos(sun angle) (ui-viz replay) | eps_tcs |
| 3 | Eclipse discharge and recovery, Steps 4–5 (EPS page + TRD trend of SoC over one orbit) | Eclipse fraction and β (ch. 07 § 7.1.2 Eclipse fraction and the β-angle); battery sizing (ch. 09 § 9.3.2) | groundtrack.js with the eclipse arc shaded, synced to the SoC trend (ui-viz replay) | Team (eclipse shape) + eps_tcs (rates) |
| 4 | Orbit-average balance, Step 6 (EPS orbit-margin panel) | Orbit-average energy in vs out (ch. 22 V.11 Solar array sizing; power_budget.py) | Stacked energy bars per orbit, sun vs eclipse (Motion Canvas) — shared with V-CON-02 | eps_tcs |
| 5 | Load transient, Step 7 (CMD as eps_tcs: EPS_POWER_ON line 5, then restore) | Why the test uses the 8 W battery-heater line, not the payload (card Step 7 note) | none | eps_tcs |

Acronyms: COM, EPS, SID, HK, TC, PUS + S3/S20/S8, SoC (card writes SOC†), Li-ion†, GaAs†
(only if the 29.5 % cells are mentioned — better to omit), SSO, FD†.
Audience: **eps_tcs** (+ flight_director as approver). The card's owner line is eps_tcs; the
FD only authorises.
Contradictions:
* Step 3 Action says "~64 W peak … deployed wings (0.78 m²)" — `subsystems/eps.yaml` has
  0.120 m² of cells per wing (0.24 m²) and 88.6 W whole-spacecraft peak; the card's own
  Verify line (40–90 W, ~80 W normal) is right. Narrate the Verify line, not the Action.
* Step 1 GO/NO-GO says "Bus voltage regulated within specification"; the Action two lines
  above says the bus is *not* regulated. Narrate "within band".
* Off-nominal: CTG-001 at < 29.6 V, but on-board shed starts at 28.4 V (`simulation.yaml
  eps.bus_protection.uv_v`) — consistent, just make sure the video does not say the
  spacecraft sheds at 29.6.
Graded: off-nominal handling feeds CTG-001 (scored) — do not narrate it.

### V-OPS-11 — COM-002 TCS Verification

Purpose: thermal zones in band through sun and eclipse; each heater line powered *before*
its heater is cycled; both circuits left ON under thermostat.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Zones in band, Steps 1–3 (TCS page, TRD over one orbit) | Thermal balance, hot/cold case (ch. 09 § 9.4.4, § 9.4.5) | Node diagram: sun, Earth IR, albedo in, radiator out; eclipse turns the sun arrow off (Manim) | eps_tcs |
| 2 | "Establish state first": line ON, heater ON, temp rises, AUTO, Steps 4–5 (CMD as eps_tcs, EPS line flags, TCS temp) | Heater sizing (ch. 09 § 9.4.8); the rev 2.0 trap (card header) | Two switches in series — line and heater — with a lamp that only lights when both close (Motion Canvas) — shared with V-CON-02 | Team (the "power the line first" rule recurs in COM-009/010, CTG-001) + eps_tcs (commands) |
| 3 | Thermostat thresholds, Step 6 (S20 GET_PARAM replies) | Thermostat hysteresis +5/+10 °C (card Step 4/6; ch. 09 § 9.4.10) | Hysteresis loop plot (Manim) | eps_tcs |
| 4 | FPA cooler interface baseline, Step 7 (TCS + PLD pages) | Why the FPA is cooled (ch. 13/payload — or ch. 09 § 9.4.6 radiator) | none | eps_tcs + payload_ops (baseline is used in COM-010) |

Acronyms: TCS, EPS, OBC, FPA†, HK, SID, S3/S8/S20, MLI† (off-nominal only — omit), AUTO
(on-screen value, no expansion).
Audience: **eps_tcs**.
Contradictions: none against configs found (heater 8 W battery / 4 W OBC in `tcs.yaml`;
funcs 40/41/45 in eps_tcs's allowed list). Exit state (lines left ON) is the 2026-11-02
ruling — make sure the narration does not say "restore the line to OFF".
Graded: nothing scored.

### V-OPS-12 — COM-004 AOCS Actuator Checkout (flies before COM-003, ruling Q16)

Purpose: enable the four wheels, command NOMINAL, prove each wheel in both directions,
unload momentum with the magnetorquers.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Enable ≠ power, Step 1 (AOC page wheel block; CMD as aocs) | Why line power and wheel enable are separate (card Step 1 Action) | Two-key diagram as in COM-002 (Motion Canvas) | Team (shape) + aocs |
| 2 | Command NOMINAL, slew to nadir, Step 1b (AOC page: mode, att_error trend) | Mode intent vs flying mode (`aocs_mode_codes.yaml`; ch. 18 § 18.2.2 Mode-transition state machine) | attitude3d.js replay of the sun-hold → nadir slew (ui-viz replay) — shared with V-CON-03 | aocs |
| 3 | One wheel test, Step 3 (AOC wheel speeds + att_error); Steps 4–6 cut to a montage | Momentum storage, H = Iω, and why the other wheels absorb the disturbance (ch. 10 § 10.3.1, § 10.3.2) | Four-wheel pyramid with momentum vectors; one wheel spins up, the body stays still (Manim) | aocs |
| 4 | Desaturation, Step 8 (AOC: wheel speeds trending to 0, MTQ on) | Magnetic torque m × B, weak near the equator (ch. 10 § 10.3.3, § 10.5) | groundtrack.js with a field-strength tint; wheel bars falling faster at high latitude (ui-viz replay + overlay) | aocs |

Acronyms: AOCS, RW (RW1–RW4), MTQ, RPM†, NOMINAL (mode, gloss "nadir-pointing on the
wheels"), DESAT† (mode), FDIR, S8/S20/S3, SID, EPS.
Audience: **aocs**.
Contradictions: none against `aocs.yaml` checked here. Breakpoint risk above.
Graded: off-nominal "AOCS can operate on three wheels" is the shape of the scored
`aocs_wheel_failure` recovery (AOCS_DISABLE_WHEEL); do not narrate off-nominal handling.
No WB-5.6 sheet exists for this card.

### V-OPS-13 — COM-003 AOCS Sensor Calibration

Purpose: three gyros on, a star tracker in the estimator, then a 300 s gyro-bias calibration
that moves the bias from "residual" into "compensation".

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Gyros and tracker up, Steps 1–3 (CMD as aocs: HK_ENABLE SID 2/7, S2 device commands, ST power/select; AOC page) | How a star tracker and a rate gyro work (ch. 10 § 10.1.1 Attitude sensors) | Star field → identified triangle → quaternion arrow (Manim) — shared with V-CON-03 | aocs |
| 2 | Tracker aids the estimator, Step 4 (AOC: est_source bit 0, knowledge error) | What the MEKF does with gyro + tracker (ch. 10 § 10.1; § 10.4.1 Error source definitions) | Estimate cone shrinking when tracker updates arrive, growing while coasting (Manim) | aocs |
| 3 | Calibration arc, Steps 6–7 (AOC + SID 7 progress; S1 row stays open until the arc ends) | S1 acceptance vs completion (PUS_SERVICE_REFERENCE § Service 1) | S1 timeline: accept tick, long gap, complete tick (Motion Canvas) — shared with V-CON-05 | aocs (+ Team for the S1 reading) |
| 4 | Result: residual → compensation, Steps 8–9 (two numbers side by side) | Bias vs residual (card Step 9 note) | Bar moving from "residual" pot to "compensation" pot (Motion Canvas) | aocs |

Acronyms: AOCS, ST†, IMU† (card says "no IMU" — gloss once), MEKF†, S1/S2/S3/S8/S20,
SID, HK, RPM no, deg/s (say "degrees per second"), arcsec† (unit: "arc-seconds").
Audience: **aocs**.
Contradictions: Step 8 accepts any bias within ±0.5 deg/s while Step 5 calls ~0.05 deg/s
"a real bias"; not a sim contradiction, but the video should give the healthy order of
magnitude (1e-5) and not the acceptance band. Off-nominal mentions MAG-B / IGRF only to say
they do not exist — do not narrate.
Graded: Step 3 powers ST2 and the off-nominal says `ST_SELECT(unit=2)` — that is the scored
recovery of `aocs_star_tracker_failure`. Show ST_SELECT(unit=1) only and never frame "if the
tracker fails, select the other". `aocs_sensor_cascade` scores AOCS_EST_RESET for a gyro
bias — do not suggest calibration as a fault recovery. No WB-5.6 sheet exists.

### V-OPS-14 — COM-005 AOCS Mode Transitions

Purpose: command what is commanded, wait-and-verify what is automatic, never verify the mode
you just left.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Latch intent, Step 1 (AOC: commanded_mode 0x0297 vs mode 0x020F) | Commanded vs flying mode, demotion flag (card Purpose; ch. 18 § 18.2.2) | State machine with a "commanded" pin and a "flying" token (Motion Canvas) — shared with V-CON-03/04 | Team (the rule) + aocs |
| 2 | FINE_POINT gate, Step 2 (AOCS_FINE_READY_CHECK reply, 7-bit mask) | Pointing error budget (ch. 10 § 10.4) | Seven lights going green one by one (Motion Canvas) | aocs |
| 3 | COARSE_SUN hold and the automatic promotion, Step 5 (AOC, use the instructor time step to skip ~30 min) | Safe hold vs destination (ch. 18 § 18.2.1 Mode table) | Same state machine; token drops, waits, climbs back (Motion Canvas) | aocs |
| 4 | Eclipse handover and DESAT exit, Steps 6–7 (TRD of mode over an orbit) | Automatic transitions (ch. 18 § 18.3.2 FDIR hierarchy, level 0/1) | groundtrack.js eclipse arc with mode ribbon underneath (ui-viz replay) | aocs |
| 5 | The transition matrix, Step 8 (card table) | — | none | Team |

Acronyms: AOCS, NOMINAL/FINE_POINT/INERTIAL/ECLIPSE/DESAT/SAFE_BOOT/SLEW (mode names †,
gloss once), ECI† (INERTIAL = Earth-centred inertial hold), CSS, MEKF†, MTQ, S1/S8.
Audience: **aocs**; the "never verify the mode you just left" rule is Team-worthy — consider a
15 s Team excerpt in V-CON-04.
Contradictions: Step 5 wait "within 3600 s (measured ~1850 s)" — needs the time-step enabler;
narrate "it comes back by itself", not the number. Prerequisites list COM-003 *and* COM-004
in that order; harmless.
Graded: nothing scored. Do not tie a question to the 0x0A22 refusal (anomaly-response-shaped).

### V-OPS-15 — COM-006 TTC Link Verification

Purpose: configure the S-band chain, read margin vs elevation, measure the 10.5 dB LOW→HIGH
step, exercise the ground's 10° arm-through rule, leave the link at LOW.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Chain configuration, Step 0 (CMD as ttc + eps_tcs for line 2; TTC page tx_gate_status bits) | Four permissions to radiate (card Step 0; LINK_BUDGET § 6.3 How to change rate, and why a change can be refused) | Gate byte as eight lamps (Motion Canvas) | ttc (+ eps_tcs for the line) |
| 2 | Margin vs elevation, Step 2 (TTC page "ground" values + skyplot) | Slant range and FSPL (ch. 11 § 11.4.1, § 11.4.2; ch. 22 V.6) | skyplot.js pass with a margin readout following the satellite (ui-viz replay) — shared with V-CON-01 | ttc |
| 3 | The ladder step, Step 2a (TTC: tier, rate, symbol rate, margin) | 16× and 8× in dB, coding gain (LINK_BUDGET § 2.4, § 3) | Bar ladder SAFE/LOW/HIGH with −12.04 and −10.53 dB arrows (Manim) — shared with V-CON-01 | ttc |
| 4 | 10° is policy, not physics, Step 2b (CMD warning dialog) | LINK_BUDGET § 4.3 The ceiling is regulation, not physics; § 2.3 HIGH — earned per dump | none | ttc + flight_director (the arm-through decision) |
| 5 | Safe the link, Step 9 (TTC page end state) | Active vs commanded tier (LINK_BUDGET § 6.2) | none | Team (what "LOW, downlink mode off" means for the next shift) + ttc |

Acronyms: TTC/TT&C, RSSI†, PA†, EIRP, G/T†, dB/dBW/dBi/dBm†, QPSK†, kbps†, Bd†, RS†, UHF†,
S-band (name), HK, SID, S8/S20, MCS, BER, FEC, TLE (off-nominal only).
Audience: **ttc**.
Contradictions:
* Purpose says "both ground stations (Iqaluit and Troll)"; the card's own table has five
  stations (Svalbard, Inuvik, Iqaluit, O'Higgins, Troll) and `power_budget.py` uses "the
  canonical five-station list in orbit.yaml". Step 7 also names only two.
* Post-condition `ttc.tx_gate_status = 0xFF`: in `models/ttc_basic.py` a set bit is
  permissive, but bit 2 (station in view) and bit 4/5 (UHF beacon) need not all be set —
  0xFF is only right in contact with the beacon on. Step 0's note calls the bits "which …
  is missing", i.e. the opposite sense. Say "all four S-band permissions lit", not "0xFF".
* Entry state says the antenna is STOWED and this card deploys it; check against the
  `card-COM-006` breakpoint — LEOP scenarios (`first_contact`, `separation_sequence`) score
  TTC_DEPLOY_ANTENNA earlier. If the breakpoint is already deployed, Step 0's verify passes
  trivially; narrate accordingly.
* Margins in tens of dB vs RSSI thresholds of −126/−118/−114 dBm: the card says these are
  sanity thresholds — keep that framing, do not present them as tight.
Graded: Steps 3–5 (TTC_SWITCH_REDUNDANT and back) are the scored recovery of
`transponder_failure` and `ttc_no_tm_at_aos`; off-nominal (PA off, redundant switch) mirrors
`ttc_pa_overheat`. Film Steps 3–5 as a 10 s "commissioning both units" mention or cut them;
never present the switch as the response to lost telemetry.

### V-OPS-16 — COM-007 OBDH Checkout

Purpose: OBC health baselines (CPU, memory, SEU, packet counters, watchdog) and a clean
NOMINAL→SAFE→NOMINAL excursion.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Mode and CPU, Steps 1–2 (OBD page) | OBC architecture (ch. 12 § 12.3.1) | none | fdir_systems |
| 2 | Memory and SEUs, Step 3 (OBD counters) | Radiation effects, EDAC (ch. 12 § 12.3.2; ch. 07 § 7.6.2 SAA) | groundtrack.js with SEU ticks clustering over the South Atlantic (ui-viz replay — needs a long series) | fdir_systems |
| 3 | Packet counters and autonomous HK, Steps 4–6 (OBD + PUS page) | TC accepted/rejected, TM generated (PUS_SERVICE_REFERENCE § Service 1, § Service 3) | none — or reuse V-CON-05 packet animation | Team (counters explain "my command vanished") + fdir_systems |
| 4 | Watchdog and the excursion, Steps 7–8 (CMD OBC_SET_MODE; contingency banner appears and clears) | Watchdog purpose (ch. 12 § 12.3.4 Flight software functions) | none | fdir_systems + flight_director (banner) |

Acronyms: OBDH, OBC, CPU†, SEU† (glossary: aléa logique), EDAC†, CAN† (Purpose only — omit),
TC/TM, HK, S1/S3/S8/S20, SAFE/EMERGENCY (mode names), FD†.
Audience: **fdir_systems**.
Contradictions: Step 7 expects last reboot cause = 0 "none"; off-nominal says "if last reset
cause != POWER_ON". After the LEOP cold boot the breakpoint may hold POWER_ON. Check the
`card-COM-007` value before filming and narrate what is on screen.
Graded: Step 8's `OBC_SET_MODE(mode=0)` is one of the scored recoveries of `obc_watchdog`.
Show it as "the card must not end in SAFE" (its own reason), not as a recovery from a
watchdog reset.

### V-OPS-17 — COM-008 FDIR Configuration & Protection Functions

Purpose: inventory S12 monitors and S19 event-actions, read FDIR summary telemetry, prove the
load-shed latch and its clear.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | S12 on and the definition report, Step 1 (PUS page TM(12,13)) | S12 check types and limits (PUS_SERVICE_REFERENCE § Service 12) | The S12→S5→S19→S8 chain (Motion Canvas) — this *is* V-CON-04; cut it in | fdir_systems |
| 2 | S19 table, the momentum chain 2001 and the one-sided overtemp rule, Step 2 | trigger_kind and one-sided rules (§ Service 19) | same | fdir_systems |
| 3 | FDIR quiescent, Step 3 (FDR page) | FDIR hierarchy (ch. 18 § 18.3.2–18.3.3) | none | Team (what FDR level means for the poll) + fdir_systems |
| 4 | Latch, event, clear, no re-power, Step 4 (CMD as eps_tcs; EPS stage; event list) | Load-shed ladder (CTG-001 Objective; `simulation.yaml` load_shed) | Ladder with a latch pawl; stage 0 lifts the pawl but leaves the lights off (Motion Canvas) | eps_tcs (sends) + fdir_systems (owns the test) |

Acronyms: FDIR, S12/S19/S5/S8/S20/S3, TM(12,13) (say "T-M twelve-thirteen, the definition
report"), EA† (event-action), FSW†, OBC, EPS, HK.
Audience: **fdir_systems + eps_tcs**.
Contradictions: Step 4 says stage 1 sheds the payload line, yet the card also says payload is
already OFF here — the verify `pl_payload = 0` passes trivially. Narrate "the latch and its
event", as the card intends.
Graded: `EPS_EMERGENCY_LOAD_SHED(stage=…)` is in the scored `tc` lists of `eps_undervoltage`,
`eps_progressive_load_shed`, `debris_impact_hermes3`. Showing stage 1 + clear on a healthy
spacecraft is the card; do not add "this is what you send when the bus drops".

### V-OPS-18 — COM-009 Payload Power On

Purpose: line first, then STANDBY; SID 5 enabled; small power step; imager health; data store.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | EPS can take it, Step 1 (EPS page) | Power budget by mode (ch. 08/ch. 09 § 9.5) | none | eps_tcs |
| 2 | Line, mode, SID 5, Step 3 (CMD: eps_tcs sends line 3, payload_ops sends mode + HK_ENABLE) | The "line before unit" rule again | reuse the two-switch animation | Team (hand-off between two seats) + payload_ops |
| 3 | Power step and health, Steps 4–5 (EPS power_cons; PLD imager status) | — | powerflow.js before/after (ui-viz replay) | payload_ops + eps_tcs |
| 4 | FPA ambient and the data store, Steps 6–7 (PLD page) | Data storage sizing (ch. 12 § 12.3.3) | none | payload_ops |

Acronyms: FPA†, SID, HK, S3/S8/S20, EPS, STANDBY (mode, gloss), MB/GB† (say "megabytes").
Audience: **payload_ops** (+ eps_tcs).
Contradictions: Step 6 band [+5, +30] °C vs COM-002/COM-010 "+8 to +14 °C" — wider, not
wrong; use the narrower number only if it is on screen.
Graded: `sequential_checkout` (scored) still expects `PAYLOAD_SET_MODE(mode=1)` /
`EPS_PAYLOAD_MODE(mode=1)` in **LEOP**; this video shows exactly that command. The scenario
is out of step with the current split (payload line moved from LEOP-007 to COM-009; its
briefing still says "following LEOP-007"). Either retire/update the scenario or accept that
the video mirrors one of its scored lines — Franz's call.

### V-OPS-19 — COM-010 FPA Cooler Activation

Purpose: switch the cooler on, see a 15 W step, watch the focal plane cool to −15 °C and hold
through eclipse.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Baseline and cooler ON, Steps 1–2 (PLD, TCS; CMD) | Why cool a detector: dark current (ch. 09 § 9.4; glossary "dark current") | none | eps_tcs (command) + payload_ops (owner) |
| 2 | 15 W step, Step 3 (EPS power flow) | Orbit-average cost of 15 W (power_budget.py profiles) | powerflow.js before/after (ui-viz replay) | eps_tcs |
| 3 | Cool-down curve, Steps 4–6 (TRD of payload.fpa_temp, time-stepped) | First-order thermal response (ch. 09 § 9.4.4; ch. 22 V.10) | Exponential approach to setpoint with the time constant marked (Manim) | payload_ops |
| 4 | Holds through eclipse, Steps 7–8 (TRD + EPS) | — | none | payload_ops + eps_tcs |

Acronyms: FPA†, TCS, EPS, S8/S20/S3, HK, SID.
Audience: **payload_ops + eps_tcs**.
Contradictions:
* `FPA_COOLER` is func 43, which is in **eps_tcs's** allowed funcs, not payload_ops's
  (payload_ops: 26–39, 92–95, 119). The index gives payload_ops "Activate cooler". Filming as
  payload_ops the command is refused; film it as eps_tcs, or fix the index/positions first.
  Same for COM-011 Step 1.
* NEXT says COM-011; the definitive order is COM-012 (first light) then COM-011.
Graded: `sequential_checkout` scores `FPA_COOLER(on=1)` in LEOP — same note as COM-009.

### V-OPS-20 — COM-012 First Light

Purpose: FINE_POINT through its gate, the first image, product on the store, S13 downlink at
HIGH, release everything.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | FINE_POINT and the orbit-rate pitch, Step 1 (AOC) | Nadir tracking carries orbit rate (ch. 10 § 10.1; card Step 1 note) | attitude3d.js nadir hold in LVLH with the pitch-rate arrow (ui-viz replay) — shared with V-CON-03 | aocs |
| 2 | Capture, Steps 3–6 (PLD: image count, store, mem_used delta) | GSD and the swath (ch. 22 V.9) | Push-broom line sweeping the ground track (Manim) | payload_ops |
| 3 | STANDBY releases the cooler, Step 7 (PLD/TCS) | 2026-11-03 rule | none | payload_ops |
| 4 | S13 transfer at HIGH, Step 8 (TTC tier + PLD transfer progress) | S13 large data transfer (PUS_SERVICE_REFERENCE § Service 13); one image ≈ most of a pass (LINK_BUDGET § 5.1) | Progress bar against pass time remaining (Motion Canvas) | Team (one image = a pass; who does what) + ttc + payload_ops |
| 5 | Release FINE_POINT, Step 9 (AOC) | — | none | aocs |

Acronyms: FINE_POINT (mode, gloss), LVLH†, S13/S8/S20/S3, HK, SID, MB†, kbps†, QPSK† (only if
symbol rate is said), FPA†, GSD (register has it).
Audience: **team** — four seats act in one card, and first light is the milestone everyone
is waiting for.
Contradictions: none against configs spotted. Store sizes (20 GB, ≤ 4 MB raw frame) are
card-stated; check against `payload.yaml` before narrating numbers.
Graded: nothing scored. WB-5.6-FL (assessment) is a worksheet, not graded quiz — fine to tie.

### V-OPS-21 — COM-011 Payload Calibration

Purpose: dark set (shutter closed), flat set (lamp on), all four bands valid, a linearity set
over a calibration site.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Cooler back on, Step 1 (CMD as eps_tcs — see COM-010 note) | — | none | eps_tcs + payload_ops |
| 2 | Dark frames, Steps 2–4 (PLD: shutter, calibration_active, dark_frame_cnt) | Dark current, fixed-pattern noise (glossary "dark frame"; ch. 13 payload section if present) | Pixel grid with per-pixel offset, then subtracted (Manim) | payload_ops |
| 3 | Flat field, Step 3a (lamp on, cal_valid_mask = 15) | Pixel response non-uniformity | Same grid, gain map divided out (Manim) | payload_ops |
| 4 | Linearity set, Steps 6–8 (AOC FINE_POINT + PLD integration times) | Signal ∝ integration time, clipping at 4095 DN | Three bars at ½×, 1×, 2× with the 12-bit ceiling (Manim) | payload_ops + aocs (pointing) |
| 5 | Back to standard configuration, Steps 9–10 | — | none | payload_ops |

Acronyms: DN†, FPA†, S8/S20/S3, HK, SID, FINE_POINT, NOMINAL, STANDBY/IMAGING/CALIBRATION
(mode names †), SNR† (only if 0x0621 is shown).
Audience: **payload_ops**.
Contradictions: Step 10 "consistent with ~13 frames" — the card itself captures 3 site images
plus the dark and flat sets; the count depends on how many frames each calibration run makes.
Check on the breakpoint before narrating the number.
Graded: nothing scored.

### V-OPS-22 — COM-013 Commissioning Closure & NOMINAL Declaration

Purpose: read back the sum of every card's exit state, poll, declare mission phase 6.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | AOCS end state, Step 1 (AOC; aocs reads it out) | — | Checklist ticking against the card list (Motion Canvas) | aocs |
| 2 | Platform end state, Step 2 (EPS/OBD/TTC; eps_tcs reads it out) | — | same | eps_tcs |
| 3 | Payload end state, Step 3 (PLD) | — | same | payload_ops |
| 4 | The poll and the declaration, Step 4 (FD poll; CMD SYS_SET_MISSION_PHASE(6); sat.mode = 1) | Mission phases (ch. 17 § 17.4.1); what phase 6 arms (card Purpose) | Phase timeline LEOP → commissioning → nominal with "FDIR armed" lighting up (Motion Canvas) | Team |
| 5 | Hold through an eclipse, Step 5 (TRD) | — | none | flight_director |

Acronyms: ADCS (title), AOCS, EPS, OBC, TTC, FDIR, S13, NOMINAL, LEOP, COM, NOM (NEXT:
NOM-001), FD†, SoC.
Audience: **team** — closure poll is the whole console.
Contradictions:
* **Step 3 verifies `payload.fpa_ready = 1` "cooler regulating (COM-010)"** — but COM-011
  Step 9 commands STANDBY, which switches the cooler off (2026-11-03), and COM-012 Step 7 /
  COM-011 Step 9 both verify `tcs.cooler_fpa = 0`. At COM-013 entry the FPA is warming and
  `fpa_ready` should be 0. Fix the card (expect 0, cooler off) before filming.
* Step 3 text "STANDBY (never left IMAGING)" reads backwards — should be "never left in
  IMAGING".
* Title says ADCS while every card and the console say AOCS — expand "attitude determination
  and control" once or retitle.
Graded: nothing scored (`sequential_checkout` scores phase **5**, not 6). No WB-5.6 sheet.

---

## V-OPS-23 — CTG-001 Under-Voltage Load Shed

Purpose: how to read a branching contingency card — check the spacecraft first, shed from the
ground only what is still on, stop at the first level that works, restore line-before-unit.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | The ladder before anything happens (PRC: card's BRANCH lines; EPS page) | On-board protection levels 28.4 / 27.7 / 26.1 / 25.9 V and SoC stages 30/20/10 % (`simulation.yaml` eps.bus_protection, load_shed); ch. 18 § 18.3.3 FDIR decision flow | Voltage axis with the on-board thresholds and the card's ground thresholds side by side (Motion Canvas) | Team |
| 2 | Check the spacecraft first, Step 1 (EPS line flags; load_shed_stage) | Ruling P3 (card revision note) | Branch diagram: GO → shed, NO-GO → check (Motion Canvas) | Team + eps_tcs |
| 3 | One level, then the voltage check (PRC branch evaluation) | Why hold at the first level that works (index comment above CTG-001) | same diagram, path lit | eps_tcs + flight_director |
| 4 | Restoration order, Step 7 (card text only) | Line before unit; reverse priority | Reverse ladder (Motion Canvas) | Team |

Acronyms: CTG, UV†, EPS, SoC (card writes SOC/SoC), TX†, PA†, FPA†, AOCS, OBC, S1/S3/S8/S20,
HK, SID, UHF†, FDIR, TT&C.
Audience: **team** — the card's lead is eps_tcs, but its commands cross four seats:
`PAYLOAD_SET_MODE` (func 26) is payload_ops, `TTC_PA_OFF/ON` (67/66) is ttc, `AOCS_SET_MODE`
(0) is aocs; eps_tcs can only send the EPS lines (19/20). Only the FD can send the whole card.
Contradictions:
* Step 4 expects power_cons to fall by **~20 W** when the PA goes off; `eps.yaml` says the
  20 W figure "was invented for the manual" — the transmitter draws 5 W at LOW, 11 W at HIGH
  (1.5 W receive chain stays). Fix to "~5 W (LOW) / ~11 W (HIGH)".
* Ground levels 27.8 / 27.2 / 26.5 V sit **below** the on-board EPS-safe level (27.7 V) and
  around the AOCS-safe level (26.1 V); by the time the card branches to Step 4–5 on-board
  FDIR will normally have acted. The card's "check first" branches handle it, but narration
  must not imply the ground acts first.
* `eps_progressive_load_shed` briefing uses SoC 50/35/25/15 %; the model's stages are
  30/20/10 %.
* Step 7 restarts the AOCS in DETUMBLE "which hands itself to COARSE_SUN" — the
  magnetorquer-only COARSE_SUN does not hold the Sun (AOCS_COARSE_SUN_MTQ_ONLY.md).
Graded: **the whole recovery is scored** in `eps_undervoltage`, `eps_progressive_load_shed`
and `debris_impact_hermes3` (tc lists: PAYLOAD_SET_MODE(0), EPS_POWER_OFF(3),
EPS_EMERGENCY_LOAD_SHED, EPS_POWER_OFF(7)). Recommendation: do **not** film a live recovery.
Make it a card-reading video on the PRC page with no fault injected (or a fault where the
on-board shedder has already done the work, so every branch reads NO-GO and nothing is
sent). Still needs Franz's ruling — the backlog already waits on it.

---

## Concept explainers that the card videos would share (3–6 min each)

### V-CON-01 — Link budget term by term

Purpose: build EOSAT-1's downlink margin from EIRP to margin, then show why the ladder steps
are −12.04 and −10.53 dB.

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | The cascade (SpaceCDF Link Budget tool — **not reachable**: `LinkBudgetTool` lives in `Phase3SubsystemDesign.tsx`, which nothing routes to) | ch. 11 § 11.1.1 Link budget flow, § 11.2 complete equation; ch. 22 V.7 | Waterfall: EIRP + G/T − FSPL − atm/pol/impl − k − 10log R − required Eb/N0 = margin (Manim) | Team |
| 2 | Slant range and FSPL over a pass | ch. 11 § 11.4.1–11.4.2; ch. 22 V.6 | skyplot.js pass with FSPL bar following elevation (ui-viz replay; `link_budget_ladder.py` for numbers) | ttc |
| 3 | Rate and coding: 16× and 8× in dB | LINK_BUDGET § 2.4, § 3; ch. 11 § 11.6.2 | Ladder bars (Manim) | ttc |
| 4 | Why it is not power-limited, and why HIGH is still earned | LINK_BUDGET § 4.1, § 4.3, § 5.1 | Pass timeline with an image-sized block (Motion Canvas) | Team |
| 5 | The other radio: UHF beacon and the three "beacons" | LINK_BUDGET § 9.5 | none | Team |

Acronyms: EIRP, G/T†, FSPL†, Eb/N0†, dB/dBW/dBi/dBm†, k (Boltzmann — say it), QPSK†/BPSK†,
RS†, FEC, BER, kbps†, UHF†, RF, AOS/LOS, CDF.
Audience: **ttc** (the Team beats can be lifted into the TTC card video). Ties LW-3.3 B,
D-3.3-LINK, WB COM-006.
Contradictions: COM-006 table quotes EIRP 10 dBW + 3 dBi — matches `ttc.yaml`
(`eirp_dbw: 10.0`, `sc_gain_dbi: 3.0`). Needs the SpaceCDF tool mounted first (backlog item
1), or film the waterfall only.
Graded: none; avoid a pass-timing arithmetic question (WB-5.4-Q category).

### V-CON-02 — Energy balance through an orbit

| # | Step (screen) | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Sun, eclipse, β | ch. 07 § 7.1.2; ch. 22 V.5 | groundtrack.js with eclipse shading; β slider changes the shadow length (ui-viz) | Team |
| 2 | Generation: cells, wings, sun angle | ch. 09 § 9.1.1–9.1.2, § 9.2 | powerflow.js replay of one orbit from `power_budget.py --report json` (ui-viz replay) | eps_tcs |
| 3 | Loads by mode, and the line-before-unit rule | ch. 09 § 9.1.3; COM-002 | Two-switch animation (Motion Canvas) | Team |
| 4 | Battery as the buffer: SoC through an orbit, DoD | ch. 09 § 9.3.2; ch. 22 V.12 | SoC trace under the powerflow replay | eps_tcs |
| 5 | Orbit-average margin and EOL worst β | power_budget.py docstring (EOL, worst-β); SpaceCDF V-SCDF-02 | Stacked energy bars (Motion Canvas) | Team |

Acronyms: EPS, SoC, DoD, β (say "beta angle"), SSO, LTAN, MPPT, BCR, PCDU, LCL, BOL/EOL†,
GaAs†, W/Wh (say in full).
Audience: **team** (shape) — the power numbers are eps_tcs's, but every seat's request
competes for this budget.
Contradictions: none; use `eps.yaml` figures (0.24 m², 88.6 W), not COM-001 Step 3's.

### V-CON-03 — Attitude, frames and quaternions

| # | Step | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | Frames: ECI, LVLH, body | ch. 10 § 10.1 AOCS fundamentals | attitude3d.js in LVLH (ui-viz) + axes overlay (Manim) | Team |
| 2 | Euler angles and gimbal lock, then the quaternion | ch. 10 § 10.1 (attitude state) | Rotating triad, axis–angle → q (Manim) | aocs |
| 3 | Sensors → estimate (tracker, gyro, MEKF) | ch. 10 § 10.1.1 | Star-field identification (Manim) | aocs |
| 4 | Actuators and momentum | ch. 10 § 10.3, § 10.5 | Wheel pyramid (Manim) | aocs |
| 5 | Modes and intent (commanded vs flying) | ch. 18 § 18.2.2; COM-005 | State machine (Motion Canvas) | Team |

Acronyms: AOCS, ECI†, LVLH†, DCM†, ST†, MEKF†, CSS, MTQ, RW, MAG†, IMU†.
Audience: **aocs** (frames and modes are Team beats).
Note: ch. 10 has no quaternion section (two passing mentions); the derivation would need a
new § in ch. 10 or ch. 22, or cite an external CC source.

### V-CON-04 — FDIR: from S12 monitor to S19 action

| # | Step | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | The hierarchy: unit → subsystem → system → ground | ch. 18 § 18.3.2 | Pyramid (Motion Canvas) | Team |
| 2 | S12: a monitor, its limits, check transition TM(12,9) | PUS_SERVICE_REFERENCE § Service 12 | Parameter trace crossing a limit band (Manim) | fdir_systems |
| 3 | S5 event → S19 rule → S8 function (momentum chain 2001 → DESAT) | § Service 19; COM-008 Step 2 | The chain as moving packets (Motion Canvas) | fdir_systems |
| 4 | One-sided rules and trigger_kind | § Service 19 notes | none | fdir_systems |
| 5 | What the ground sees (FDR page, alarm, ACK) | ch. 18 § 18.5 | none — film FDR page | Team |

Acronyms: FDIR, S5/S8/S12/S19, TM(12,9)/(19,128), EA†, OBCP, ACK†, OBC.
Audience: **fdir_systems** (Team beats 1 and 5).
Graded: do not walk through a specific fault's recovery (anomaly-response category; every
fault scenario but four is scored). Use the momentum-management chain (a nominal function).

### V-CON-05 — CCSDS packets and PUS services

| # | Step | Deeper explanation | Animation | Scope |
|---|---|---|---|---|
| 1 | The stack: packet in frame in coded stream | ch. 17 § 17.3.1–17.3.3 | Nested boxes (Manim) | Team |
| 2 | One space packet: primary header, APID, sequence count, PUS secondary header, CRC | ch. 17 § 17.3.2; ch. 03 (ECSS) | Byte-field layout filling in (Manim) | Team |
| 3 | Service/subtype: TC(3,27) → TM(3,25); S1 acceptance and completion | PUS_SERVICE_REFERENCE § Service 1, § Service 3 | S1 timeline (Motion Canvas) | Team |
| 4 | The services the cards use (S2, S3, S8, S12, S13, S19, S20) | § Service Overview | Service map (Motion Canvas) | Team |
| 5 | Reading it on the PUS page | — | film PUS page | fdir_systems |

Acronyms: CCSDS, PUS, ECSS†, APID, CRC†, TM/TC, HK, SID, CUC, OBT, S1…S20, VC† (virtual
channel — only if frames are named).
Audience: **team** — every seat reads S1 reports and SIDs.
Graded: WB-5.4-Q has a "limits and SIDs" category — no embedded question that asks which SID
carries a parameter.

---

## Proposed production order

1. **V-CON-05 CCSDS + PUS** and **V-CON-04 FDIR chain** — no breakpoint, no AOCS dependency,
   Team audience, and every COM video leans on S1/S3/S8/S12/S19.
2. **V-CON-02 Energy balance** — all ui-viz/`power_budget.py`; feeds COM-001/009/010, CTG-001.
3. **COM-007, COM-008, COM-002** — independent of the COARSE_SUN defect (COM-007/008 fly in
   wheel NOMINAL; COM-002 is thermal, and its screens do not dwell on attitude).
4. **COM-006** after the two text fixes (stations, 0xFF), then **V-CON-01 Link budget** once
   the SpaceCDF tool is routed.
5. **COM-005, COM-003** (wheel-controlled NOMINAL — fine), then **V-CON-03 Attitude**.
6. **COM-009 → COM-010 → COM-012 → COM-011 → COM-013** after the FPA_COOLER position fix, the
   COM-013 `fpa_ready` fix, and the `sequential_checkout` decision.
7. **COM-001, COM-004** once COARSE_SUN on magnetorquers holds the Sun.
8. **CTG-001** only after Franz's scoring ruling, and in the card-reading form above.

## Explainer candidates (shared by several of the above)

| Concept | Textbook / source | Outline | Route | Prepares | Audience |
|---|---|---|---|---|---|
| Line before unit (power the line, then command the unit) | COM-002 rev 2.0 note; CTG-001 Step 7; ch. 09 § 9.1.3 | Two switches in series; three cards where forgetting the line made the command "obey and do nothing" (COM-002, COM-009, CTG-001 restore). 3 min. | Motion Canvas | WB-5.6-C002, -C009; WB-A | Team |
| Commanded vs flying mode | COM-005 Purpose; ch. 18 § 18.2.2 | Intent latch, demotion flag, automatic promotion and eclipse handover; "never verify the mode you just left". 4 min. | Motion Canvas state machine | WB-5.6-C005; COM-004/012/013 | Team (+aocs) |
| S1 verification: accepted ≠ completed | PUS_SERVICE_REFERENCE § Service 1 | Acceptance, start, completion, failure notice and its code; the calibration arc whose completion arrives 300 s later. 3 min. | Motion Canvas | every card's CMD screen | Team |
| Link margin vs elevation and the rate ladder | V-CON-01 (ch. 11; LINK_BUDGET § 2–4) | as V-CON-01 | Manim + skyplot | WB-5.6-C006, LW-3.3 B | ttc |
| Orbit-average energy balance | V-CON-02 (ch. 09; ch. 07 § 7.1.2) | as V-CON-02 | ui-viz powerflow replay | WB-5.6-C001/C010, D-2.4-POWER | Team |
| On-board protection ladder (S12 → S19 → load shed) | V-CON-04 + `simulation.yaml` | as V-CON-04, plus the voltage axis from CTG-001 step 1 | Motion Canvas | WB-5.6-C008, WB-A | Team (+fdir_systems, eps_tcs) |

---

## Register additions (not in `acronyms.yaml`; for the register owner to add)

| Code | en | fr | short-en | short-fr | kind |
|---|---|---|---|---|---|
| SOC | state of charge (card spelling of SoC) | état de charge | state of charge | état de charge | word (alias of SoC, expand false) |
| FD | Flight Director | directeur de vol | F-D | F-D | letters |
| FPA | focal plane array | plan focal | F-P-A | F-P-A | letters |
| ST | star tracker | senseur stellaire | S-T | S-T-R | letters |
| IMU | inertial measurement unit | centrale inertielle | I-M-U | I-M-U | letters |
| MEKF | multiplicative extended Kalman filter | filtre de Kalman étendu multiplicatif | M-E-K-F | M-E-K-F | letters |
| MAG | magnetometer | magnétomètre | mag | mag | word |
| ECI | Earth-centred inertial (frame) | repère inertiel géocentrique | E-C-I | E-C-I | letters |
| LVLH | local vertical, local horizontal (frame) | repère orbital local (verticale locale, horizontale locale) | L-V-L-H | L-V-L-H | letters |
| DCM | direction-cosine matrix | matrice des cosinus directeurs | D-C-M | D-C-M | letters |
| PA | power amplifier | amplificateur de puissance | P-A | P-A | letters |
| TX | transmitter | émetteur | T-X | T-X | letters |
| RSSI | received signal strength indicator | indicateur de puissance du signal reçu | R-S-S-I | R-S-S-I | letters |
| G/T | gain-to-noise-temperature ratio | facteur de mérite G/T | G over T | G sur T | letters |
| dB / dBW / dBi / dBm | decibel / decibels relative to one watt / to an isotropic antenna / to one milliwatt | décibel / décibels par rapport à un watt / à une antenne isotrope / à un milliwatt | dee-bee, dee-bee-W, dee-bee-i, dee-bee-m | dé-bé, dé-bé-W, dé-bé-i, dé-bé-m | letters |
| FSPL | free-space path loss | affaiblissement en espace libre | F-S-P-L | F-S-P-L | letters |
| Eb/N0 | energy per bit to noise power spectral density | énergie par bit sur densité spectrale de bruit | E-b over N-zero | E-b sur N-zéro | letters |
| SNR | signal-to-noise ratio | rapport signal sur bruit | S-N-R | R-S-B | letters |
| QPSK | quadrature phase-shift keying | modulation par déplacement de phase à quatre états (MDP-4) | Q-P-S-K | Q-P-S-K | letters |
| BPSK | binary phase-shift keying | modulation par déplacement de phase à deux états (MDP-2) | B-P-S-K | B-P-S-K | letters |
| RS | Reed–Solomon (code) | code de Reed-Solomon | Reed–Solomon | Reed-Solomon | word (always say in full) |
| kbps | kilobits per second | kilobits par seconde | kilobits per second | kilobits par seconde | word (say in full) |
| Bd | baud | baud | baud | baud | word |
| UHF | ultra-high frequency | ultra-haute fréquence | U-H-F | U-H-F | letters |
| UV | under-voltage | sous-tension | under-voltage | sous-tension | word (say in full) |
| SEU | single-event upset | aléa logique | S-E-U | S-E-U | letters |
| EDAC | error detection and correction | détection et correction d’erreurs | ee-dack | E-D-A-C | word |
| CPU | central processing unit | processeur | C-P-U | C-P-U | letters |
| CAN | controller area network | bus CAN | can | can | word |
| CRC | cyclic redundancy check | contrôle de redondance cyclique | C-R-C | C-R-C | letters |
| VC | virtual channel | canal virtuel | V-C | V-C | letters |
| ECSS | European Cooperation for Space Standardization | Coopération européenne pour la normalisation spatiale | E-C-S-S | E-C-S-S | letters |
| EA | event-action (S19 rule) | événement-action | event-action | événement-action | word (say in full) |
| FSW | flight software | logiciel de vol | flight software | logiciel de vol | word (say in full) |
| ACK | acknowledge (alarm) | acquitter | ack | acquit | word |
| DN | digital number (pixel count) | valeur numérique (compte) | D-N | D-N | letters |
| MB / GB | megabyte / gigabyte | mégaoctet / gigaoctet | megabytes | mégaoctets | word (say in full) |
| RPM | revolutions per minute | tours par minute | R-P-M | tours par minute | letters |
| arcsec | arc-second | seconde d’arc | arc-seconds | secondes d’arc | word |
| BOL / EOL | beginning / end of life | début / fin de vie | B-O-L / E-O-L | B-O-L / E-O-L | letters |
| GaAs | gallium arsenide | arséniure de gallium | gallium arsenide | arséniure de gallium | word (say in full) |
| Li-ion | lithium-ion | lithium-ion | lithium-ion | lithium-ion | word |
| MLI | multi-layer insulation | isolation multicouche | M-L-I | M-L-I | letters |
| PVT | position, velocity, time | position, vitesse, temps | P-V-T | P-V-T | letters |
| expand: false (mode names, gloss once) | NOMINAL, FINE_POINT, INERTIAL, ECLIPSE, DESAT, SLEW, SAFE_BOOT, STANDBY, IMAGING, CALIBRATION, EMERGENCY, OFF | | | | |
| expand: false (MCS rail labels: "the overview page, OVR") | OVR, AOC, TTC, PLD, PRP, OBD, CMD, FDR, TRD, PUS (page), MAN | | | | |

Not found: the "65-video plan" the task refers to is not in the repo or the brief (it may be
in the project doc `research/Free H5P and animation tools.md`, which I could not read); the
ids above are provisional.
