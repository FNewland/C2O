# Script review C: V-OPS-08, V-OPS-09, V-PLN-01

Reviewer pass of 2026-11-06 against `BRIEF.md`. All three storyboards validate with no
`✗` problems and no `! acronym:` warnings, and they load as YAML.

## V-OPS-08: LEOP-006, set the on-board clock

Audience now: all. Recommendation: **whole team for the shape** (why the clock matters, what
NONE / GROUND mean, why every packet before this card is stamped in the year 2000), with the
commanding judgement on **`flight_director` + `fdir_systems`**. The index lists only
`flight_director` as required for LEOP-006. But `positions.yaml` gives `fdir_systems` the S9
service and says that desk "decides when to sync the OBC clock". `ttc` keeps S9 for the
passes and dumps side. The video is shot from the Flight Director seat, which matches the card.

| Step | Deeper explanation (what, and the source: file § heading) | Animation idea (what moves; route) | Scope |
|---|---|---|---|
| unset (card Step 2) | The three clocks (sim time, on-board time, ground time) and why a clock that was never set is not the same thing as a clock that drifted. The bootloader resets the clock to coarse time 0 (CUC 0) = J2000 on every reboot. Sources: `sim/docs/plan_2026-08c/TIME_ARCHITECTURE.md` § The three clocks, § Part B `obdh.time_ref` values, § Reboot and power; textbook `12_structures_propulsion_obdh.md` § 12.3.4 Flight software functions. | A timeline with two clocks. The on-board clock starts at J2000 at boot while the ground clock sits at the mission date. A label on the on-board clock steps NONE → GROUND → GPS → HOLDOVER as events fire. Route: Motion Canvas (timed block diagram). | Team (what NONE means, why early telemetry says year 2000) + `fdir_systems` (reference state) |
| delta (Step 3) | How the offset formula works: delta_t = T_obc − (T_ground − OWLT). OWLT is the slant range divided by c (3–22 ms for this orbit), and the card shows why it is two orders of magnitude below the 1 s threshold. The card's decision table (NONE / under 1 s / under 1 day / 1 day or more with GROUND). Sources: `sim/configs/eosat1/procedures/leop/time_sync.md` Step 3; `sim/docs/LINK_BUDGET_AND_RATES.md` (slant range); textbook `17_ground_segment.md` § 17.2.1 Contact geometry. | The spacecraft moves along a pass arc while a line from the station stretches and shrinks with the slant range. A packet travels down the line, and the OWLT readout follows the range. Route: ui-viz replay (`skyplot.js` + range series from the pass geometry), or Manim for the formula. | `flight_director` / `fdir_systems` (compute and approve); Team (light time as an idea) |
| set (Step 4) | The coarse+fine CUC time code against a Unix or GPS epoch (9.46e8 s and 6.3e8 s out), why the time is computed at the moment of sending, and the jump that event `OBC_TIME_SET` (0x030C) reports. Sources: `TIME_ARCHITECTURE.md` § Part A CUC wire format; card Step 4 notes; `sim/docs/PUS_SERVICE_REFERENCE.md` (S9). | A packet-layout diagram: the S9.1 packet with its CUC field broken into coarse and fine bytes, and the same instant encoded from three epochs, shown as three bars of very different lengths. Route: Manim. | `fdir_systems` / `flight_director` |
| verify (Step 5) | Residual against threshold. Why SET_TIME carries whole seconds only, so sub-second accuracy comes from GPS discipline. The tighter 0.1 s threshold is NOM-008's. Why the order of the two paths matters: a GPS jump of more than 5 s on a clock that was never set would force the AOCS into SAFE_BOOT (CTG-027). Sources: card Steps 5 and 6a; `TIME_ARCHITECTURE.md` § Transitions, § Drift. | An offset-against-time plot. The offset sits at years before the set, falls to below a second at the set, then drifts at about 12 ppm until GPS discipline holds it flat. A "what if GPS first" branch shows the 5 s jump line being crossed. Route: Manim, or a ui-viz-style replay of a time series from the LEOP fly-through test. | Team (the ordering idea) + `fdir_systems` / `aocs` (SAFE_BOOT side effect) |

Acronyms changed:
- EN: PUS → "the packet utilisation standard, PUS"; S9 → "service nine, time management, S9 TIME on the console" (step 4 now says "S9, subtype one, set time"); LEOP → "the launch and early orbit phase, LEOP" (first said in the verify step).
- FR: "la norme d’utilisation des paquets, PUS"; "service neuf, gestion du temps"; "la phase de lancement et de début d’orbite, la LEOP".
- Jargon glossed: epoch ("the mission's zero: noon on the first of January two thousand" / « le zéro de la mission ») from the card's J2000; Unix timestamp ("which counts from nineteen seventy"); disciplined ("steered continuously" / « recalée en continu »).

Notes / risks:
- `sources:` points to `sim/docs/TIME_ARCHITECTURE.md`, which does not exist. The file is `sim/docs/plan_2026-08c/TIME_ARCHITECTURE.md`. I left the field as it is: it is not a narration field, so whoever owns the storyboard metadata should fix it.
- The video covers card Steps 2–5 only. Two things it leaves out matter: Step 6a (`HK_ENABLE(sid=12)` and the GPS sync), which is part of this card, and Step 7 (log). The verify narration says "Later, once the GPS receiver has a fix…", which can read as if GPS discipline happens on another card. LEOP-003 depends on SID 12 being enabled here. A learner who watches only the videos could arrive at LEOP-003 with SID 12 never enabled (V-OPS-09 only shows a one-shot request). Consider one sentence in a later revision, or a tie to WB-5.5-L006 Step 6a.
- The card says that before the sync T_obc reads "a few hours at most" (time since the last bootloader reset). The narration says the clock counts "from its epoch", which is consistent. The number on screen is small, while the offset is years. Worth making sure the highlight makes that distinction visible.

## V-OPS-09: LEOP-003, where are we? Then end LEOP

Audience now: all. Recommendation: **whole team** for Step 7 (the GO/NO-GO poll and the
end-of-LEOP declaration are a team event, and the reflect question asks about every
position). **`aocs`** for the GPS solution and the check band (card subsystem "AOCS /
Flight Dynamics"; index role "Process GPS PVT"). **`flight_director`** approves the orbit and
sends phase 5. **`ttc`** supplies range/Doppler (and the fall-back if GPS fails). The video
is held from rendering for an AOCS model issue; the narration has been reviewed and edited
anyway.

| Step | Deeper explanation (what, and the source: file § heading) | Animation idea (what moves; route) | Scope |
|---|---|---|---|
| fix (Step 1) | What a GPS fix type, the satellite count and dilution of precision (PDOP) mean, and why the PVT channels read zero below fix 2 (honest-invalid, so "wait", not "centre of the Earth"). Sources: card Step 1 note; textbook `10_aocs.md` § 10.1.1 "GPS receivers for orbit determination" and the worksheet's PDOP link. | A sky dome around the spacecraft showing GPS satellites in two geometries: clustered (high PDOP, a wide error ellipsoid) and spread out (low PDOP, a tight one). The fix type climbs 0 → 1 → 2 → 3 as satellites are acquired. Route: Manim, or `skyplot.js` replay. | `aocs` (judges the fix); Team (why a bad fix voids everything after it) |
| position (Step 2) | The check band (495–540 km) is the TLE-propagated altitude range (503–530 km, mean 513 km) plus margin. The wider anomaly band is 400–550 km. Why geodetic altitude varies over an orbit even for a near-circular orbit (Earth oblateness). Sources: card Step 2 notes; textbook `07_orbit_and_environment.md` § 7.1 Keplerian orbital elements, § 7.3.4 Perturbation effects. | An altitude-against-time trace over one orbit wobbles between 503 and 530 km inside the shaded check band, with the anomaly band in a lighter shade. A 552 km reading lands outside the check band but inside the anomaly band. Note that the 552 km scenario is graded question q2, so the video must not resolve it. Route: Manim or a ui-viz replay of the propagated TLE. | `aocs` (band check) + Team (NO-GO reporting) |
| compare (Steps 3–6) | State vector to orbital elements, and how the magnitudes are checked: \|r\| ≈ R_E + h, v = √(μ/a). The Sun-synchronous condition (97.39° here) and what LTAN controls (lighting, β-angle). Sources: textbook `07_orbit_and_environment.md` § 7.1.1 Key equations, § 7.3.1 Orbit types; `22_derivations.md` § Sun-synchronous condition; `17_ground_segment.md` § 17.1.4 Flight dynamics system (FDS); chapter 21 § Mission Analyst. | An ECEF position and velocity arrow on a globe turns into an orbit ellipse with labelled i, e and the ascending node. The node then precesses through a year so it keeps the same local time (SSO). Route: Manim (geometry), `groundtrack.js` / `attitude3d.js` replay for the track. | `aocs` + Flight Dynamics role (no console seat; `flight_director` approves) |
| end (Step 7) | What the mission phase gates: telecommand acceptance, the derived spacecraft mode, FDIR arming and the propulsion arm interlock. Why the command is `critical` and the argument is read back. Why `sat.mode` still derives SAFE until COM-013. Sources: card Step 7 and Exit state; textbook `17_ground_segment.md` § 17.4.1 Mission phases, § 17.4.3 LEOP timeline detail; `19_operations_rehearsal.md` § 19.4.1 LEOP. | A phase ladder (0 … 6) with the gates each phase opens shown as switches that flip at phase 5 (FDIR armed, and so on) while the mode stays SAFE. Route: Motion Canvas. | Team (poll, shape of LEOP) + `flight_director` (sends it) |

Acronyms changed:
- EN: LEOP → "the launch and early orbit phase, LEOP" (new opening sentence: "This is the last card of…"); SID → "structure identifier twelve, SID twelve"; LTAN added as a short form after "the local time of the ascending node", with a gloss ("the local solar time when the spacecraft crosses the equator heading north").
- FR: "la phase de lancement et de début d’orbite, la LEOP"; "identifiant de structure douze, SID douze"; "heure locale du nœud ascendant, LTAN, l’heure solaire locale quand le satellite franchit l’équateur vers le nord".
- Jargon glossed: insertion ("the orbit the launcher delivered" / « l’orbite livrée par le lanceur »).

Notes / risks:
- The narration calls it "the attitude page", and the rail label is "AOC" (`mcs.js` `["aocs","AOC"]`). I did not introduce AOC/AOCS here, to avoid an expansion that does not match the rail label. If you want it, "the attitude and orbit control page, AOC on the rail" needs AOC in the register.
- The card's Step 7 marks `SYS_SET_MISSION_PHASE` as `critical` with an argument read-back. The narration does not mention the read-back. That is fine for length, but it is a good teaching point.
- The step "Steps 3 to 6" only scrolls to s3 and s4. Steps 5 (second fix) and 6 (report distribution) are only spoken.
- The position step highlights only the altitude row (0x0212). Latitude and longitude are fetched but not pointed at.
- The question `why` text "Normal for LEO" uses LEO unexpanded. The option text just above it says "low Earth orbit" in full, so a reader meets the full form first. Left as it is.
- The video is held from rendering for the AOCS model issue. No number in the narration depends on AOCS state.

## V-PLN-01: Plan a pass in the mission planner

Audience now: all. Recommendation: **whole team.** Every position has to read passes,
eclipses and the predicted state of charge, and the Day 1 pass plan (WB-5.3-PP) is a team
deliverable that the other team challenges. Within it, the imaging step is
**`payload_ops`** (with **`eps_tcs`** for the cooler power and thermal load), and the final
constraint check and plan sign-off sit with **`flight_director`**. Passes and their duration
or elevation are also **`ttc`**'s daily input.

| Step | Deeper explanation (what, and the source: file § heading) | Animation idea (what moves; route) | Scope |
|---|---|---|---|
| horizon | The eclipse fraction for this orbit (about 34 of 95 min), and why the predicted state-of-charge curve is the yardstick for every activity (orbit-average energy balance). Sources: textbook `07_orbit_and_environment.md` § 7.1.2 Eclipse fraction and the β-angle; `09_power_and_thermal.md` § 9.3 Battery sizing; `sim/tools/power_budget.py`. | Over 24 h, eclipse bars sweep across while the state-of-charge curve dips in each eclipse. Dropping an imaging block onto the axis deepens the next dip. Route: `powerflow.js` / `overview.js` replay from a `power_budget.py` series. | Team + `eps_tcs` (state-of-charge judgement) |
| contact | Pass geometry: why passes vary in length and maximum elevation, the elevation mask, and the 7.4 min maximum pass at 500 km / 10° mask. Sources: textbook `07_orbit_and_environment.md` § 7.4.1 Ground-station contact geometry; `17_ground_segment.md` § 17.2.1 Contact geometry, § 17.2.3 Contact frequency; `sim/tools/pass_gap_analysis.py`. | A sky plot with a high overhead pass and a low grazing pass side by side, with AOS/LOS ticks and a duration bar growing with each. Route: `skyplot.js` replay. | Team (AOS/LOS, fitting a procedure in a pass) + `ttc` (link at low elevation) |
| track | β-angle: what it is, how it moves through the year for an SSO, and β* above which there is no eclipse. Ground-track drift between orbits. Sources: textbook `07_orbit_and_environment.md` § 7.1.2; `22_derivations.md` § V.5 Eclipse Fraction; chapter 21 § Mission Analyst. | A 3D Sun–Earth view: the orbit plane tilts as β changes and the eclipse arc shrinks to zero at β*. A synced `groundtrack.js` replay shades the eclipsed part of the track. Route: Manim (geometry) + ui-viz replay. | Team (reading β and eclipse length) |
| imaging | The off-nadir angle and the Sun elevation as imaging constraints (GSD growth with off-nadir; illumination). The activity sequence and its lead: mode lead-in, then focal plane array (FPA) cooler ON 480 s before the capture, because the cooler is off in STANDBY (ruling of 2026-11-03). Sources: `sim/configs/eosat1/planning/activity_types.yaml` (imaging_pass comments); `design/docs/oer/chapters/09_power_and_thermal.md`; chapter 21 § Payload Lead. | A timed block diagram of the imaging activity: lead-in, then cool-down (an FPA temperature trace falling into band), then capture, with telecommands as ticks. Route: Motion Canvas. | `payload_ops` (+ `eps_tcs` for cooler power and thermal) |
| check | What each constraint checker actually tests (power duty cycle, attitude mode, thermal limits, data volume against downlink) and how a conflict is reported. Sources: `activity_types.yaml` (`thermal_constraints`, `data_volume_mb`, `requires_attitude`; `PowerConstraintChecker`); textbook `17_ground_segment.md` § 17.2.2 Data volume per pass, § 17.4.2 Operations timeline. | A plan timeline where each constraint is a lane that lights green or red as a cursor replays the plan, then a conflict flag pops up on an overlap. Route: Motion Canvas (or a ui-viz replay of the planner's own check output). | Team (a plan is ready only when valid) + `flight_director` (sign-off) |

Acronyms changed:
- EN: AOS and LOS added as short forms after "acquisition of signal" and "loss of signal" (said in full already); question option "FPA cooler" → "focal plane array (FPA) cooler"; question intro "12:14 UTC (coordinated universal time)" (read, not spoken; a learner meets UTC here first).
- FR: « l’AOS », « la LOS »; « refroidisseur du plan focal (FPA) »; « 12:14 UTC (temps universel coordonné) ».
- Jargon glossed: maximum elevation ("how high it climbs above the horizon" / « la hauteur atteinte au-dessus de l’horizon »); off-nadir angle ("how far the camera tilts from straight down" / « l’inclinaison de la caméra par rapport à la verticale »).

Notes / risks:
- "access time" (EN) against « durée d’accès » (FR): the EN can be heard as a clock time. If the planner column is a duration, "access duration" would be clearer. I did not check the UI label, so I left it.
- No `cards:` tie and no procedure card. The numbers in the narration (34 / 95 min, eight minutes of cool-down) come from earlier authoring. The 480 s cool-down matches `activity_types.yaml`.
- The whole imaging sequence books about 625 s of dwell (lead-in plus cool-down), so the activity starts more than eight minutes before the capture. The narration's "about eight minutes to cool down first" is correct for the cooler alone.

## Explainer candidates

1. **Spacecraft time: epochs, CUC and the three clocks** (3–5 min). Textbook `12_structures_propulsion_obdh.md` § 12.3.4, plus `sim/docs/plan_2026-08c/TIME_ARCHITECTURE.md` (§ The three clocks, Part A, Part B). Outline: sim time against on-board time against ground time. The epoch as the clock's zero (J2000, against Unix and GPS). The coarse+fine CUC field. Why a reboot resets the clock to the year 2000 and why early telemetry carries those stamps. The NONE → GROUND → GPS → HOLDOVER reference states. Why ground-first then GPS (the 5 s SAFE_BOOT jump). Light-time correction as the general method. Route: Manim (packet layout, epoch bars) + Motion Canvas (reference state machine). Prepares WB-5.5-L006 q2–q5 and NOM-008 (routine sync), and gives context for CTG-027. Audience: whole team (concepts), with depth for `fdir_systems` / `flight_director`.
2. **β-angle, eclipses and the energy budget** (4–6 min). Textbook `07_orbit_and_environment.md` § 7.1.2 and `22_derivations.md` § V.5, with `09_power_and_thermal.md`. Outline: what β is. How eclipse length follows from β and altitude. β* and the fully sunlit season. How SSO and LTAN fix the β envelope over a year. How each orbit's energy margin, and so the predicted state-of-charge curve in the planner, follows from it. Route: Manim (3D geometry) + `powerflow.js` / `groundtrack.js` replay from `power_budget.py`. Prepares WB-5.3-PP (Day 1 pass plan) and the power-related LEOP and commissioning checks. Audience: whole team; `eps_tcs` in depth.
3. **From a GPS fix to an orbit: state vectors, elements and Sun-synchronous orbits** (4–6 min). Textbook `07_orbit_and_environment.md` § 7.1, § 7.3.1, § 7.3.4; `22_derivations.md` § Sun-synchronous condition; `17_ground_segment.md` § 17.1.4. Outline: fix quality (fix type, satellite count, PDOP). ECEF position and velocity. Sanity checks (\|r\|, v = √(μ/a)). Converting to i, e, RAAN and LTAN. Why 97.39° makes the node precess with the Sun. Check band against anomaly band and what each failure points to (bad fix or bad insertion). Route: Manim + `skyplot.js` / `groundtrack.js` replay. Prepares WB-5.5-L003 q1, q2 and q7 context (without resolving the 552 km question). Audience: `aocs` and the Flight Dynamics role; team for the shape.
4. (Lighter) **Pass geometry: AOS, LOS, elevation and what fits in a pass**. `07` § 7.4.1, `17` § 17.2.1–17.2.3. Route: `skyplot.js` replay. Prepares WB-5.3-PP q3 and the habit of checking pass length before choosing a card. Audience: whole team, `ttc` in depth.

## Register additions

- **FPA**: focal plane array / plan focal (matrice du plan focal); short "F-P-A"; kind letters; expand true. Used in the V-PLN-01 question (glossary: `focal plane array (FPA)`, `plan focal (FPA)`).
- **PDOP**: position dilution of precision / dilution de précision de position; short "P-DOP"; kind letters. Spoken here only as "dilution of precision", but it is on the worksheet and the AOC page.
- **PVT**: position, velocity and time / position, vitesse et temps; short "P-V-T". It is on the AOC page ("GPS navigation (PVT)") and in the card, though not spoken here.
- **ECEF**: Earth-centred, Earth-fixed / repère terrestre fixe (centré sur la Terre); short "E-C-E-F". Card Step 3, not spoken.
- **AOC** (MCS rail label for the AOCS page): needed only if a narrator says "AOC on the rail".
- **J2000** (expand false or gloss: the epoch noon UTC 1 January 2000): appears on the card and could appear in later time videos.
