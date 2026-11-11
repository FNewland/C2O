# Northern Fire and Ice in SpaceCDF: design script v2 (recording)

This is the position-by-position script for recording the Northern Fire and Ice design walkthrough
in SpaceCDF, from the Phase 0 need to a passed Preliminary Design Review (PDR). It replaces the v1
script. Version 2 keeps every v1 step and adds:

- the systems-engineering steps of the phase protocol (the Phase card, deliverables per phase,
  system-level trades, the allocation ledger, function links and the FFBD, the validation plan, the
  stage-transition inventory before each review, the V diagram);
- the four negotiation scenes, each ending with every involved seat signing: the fourth ground
  station (the ripple), N1 science volume and downlink, N3 payload peak power, N7 mass envelopes;
- the Licensing tab filled by the team on camera;
- the decision on ECP-02 (the launch request) at the System Requirements Review (SRR), through
  change control;
- the teaching scene on ECP-01 at the PDR: "when you disagree with the score, check the logic".

*A teaching mission concept for northern fire and ice monitoring. The numbers are a frozen teaching
baseline.* `design/tests/fixtures/nfi/NUMBERS.yaml` holds every number; if this script and
`NUMBERS.yaml` disagree, `NUMBERS.yaml` wins. No person or institution is named: every owner,
stakeholder and logbook author is a role.

**Companions.** Paths are relative to `design/`.

| File | Use |
|---|---|
| `tests/fixtures/nfi/*.yaml` | the frozen baseline: mission, requirements (302), risks (37), trades, equipment, modes, budgets, functions, stakeholders and MOEs, V&V plan, housekeeping SIDs, ground stations, logbook |
| `tests/fixtures/nfi/seed.py` | the staged seed S0 … S4 (`--recording` leaves the filmed scenes to the team) |
| `tests/fixtures/nfi/test_w3_integration.py` | the closing scenes of §6 as API calls, in the same order (`srr_actions`, `pdr_actions`, `ecp01_scene`, `negotiation_scenes`, `fill_recording_scenes`); the test passes on the full seed and on the recording seed |
| `docs/dev/DRY_RUN.md` | how to start the server, seed a stage and open the study; where each feature lives (§4); the dry-run record (§6) |
| `configs/examples/nfi/project.json` | the study as this script leaves it ("Load Example Mission" → Northern Fire and Ice) |

---

## 0. Read this first

### 0.1 How each scene is written

Every scene gives:

- **Seat**: the active seat (`[data-testid=active-seat]`) to take before the first action.
- **Panel**: the level, tab and card where the action happens.
- **Actions**: what the presenter does, in order.
- **On screen**: what the viewer must see when the action is done (frame the shot on it).
- **Caption EN / Caption FR**: one line for the lower third, in English and French.
- **Gate state after**: the review readiness after the scene (must-pass criteria met / total, and
  the must-pass criteria still open). Measured on the dry run (DRY_RUN.md §6).

Markers left in v2:

| Marker | Meaning |
|---|---|
| **[TOOL-CHECK]** | The tool computes its own number. Compare it with the value given; a difference beyond the tolerance is a tool finding for the logbook, not a design change. |
| **[UI-GAP kept]** | The UI cannot take the value; the reason it stays is given in Appendix A. Two remain, neither blocks a scene. |

The v1 markers PENDING-A (mission definition editor) and PENDING-C (project export and import) are
resolved, and so is every v1 UI-GAP except the two above (Appendix A).

### 0.2 Positions (seat ids from `configs/seats.yaml`)

Team: **9 seats, one each, plus the two optional seats** (Propulsion, Cost & risk). The Customer
seat joins for the requirements it writes and for the N1 negotiation; the Observer joins at the
reviews; the Instructor sets the protocol mode and signs off.

| Seat id | Label | Mission role | Scenes |
|---|---|---|---|
| `team_leader` | Team leader | Project lead, RSSSA licence lead, review chair, change board | 1.x, 2.10, 5.13, 6.x |
| `systems_engineer` | Systems | Budgets, functions, interfaces, ledger (N7), SEMP, ICD issues, FDIR spec | 2.4, 3.x, 5.1–5.4, 6.3, 6.6 |
| `mission_analyst` | Mission analysis & ops | Orbit, coverage, ground network (ripple), ConOps, debris assessment, flight rules | 2.2, 2.3, 2.5, 2.8, 4.9, 5.7, 6.4 |
| `payload_lead` | Payload | Cameras, optics, controller, products, compression (N1), T-A01 / ECP-01 | 4.1, 4.12, 6.9 |
| `power_engineer` | Power | EPS, arrays, battery, power by mode (N3) | 3.4, 4.2, 4.11, 4.13 |
| `aocs_engineer` | AOCS | ADCS, GNSS, pointing, AOCS modes | 4.3, 5.6 |
| `comms_engineer` | Comms & OBDH | UHF links, licensing technical data, OBC, TM/TC and housekeeping SIDs, data architecture (T-S01) | 3.4b, 4.4, 4.5, 5.5 |
| `thermal_engineer` | Thermal | Thermal control, thermal nodal model | 4.6, 6.8 |
| `structures_engineer` | Structures & config | Structure, stack, launch interface | 3.7, 4.7 |
| `propulsion_engineer` | Propulsion | **Disposal**: drag sail and independent timer (PI ruling: Propulsion owns disposal) | 4.8, 6.4 |
| `cost_engineer` | Cost & risk | Cost pricing, risk register, reliability and FMEA | 2.9, 2.10, 4.10, 6.7 |
| `customer` | Customer | Science lead and community liaison: mission requirements, N1 sign-off | 2.6, 4.12 |
| `observer` | Observer | External reviewer at the reviews (read-only) | 6.x |
| `instructor` | Instructor | Protocol mode (warn or block), class board, sign-off | 1.7, 6.x |

### 0.3 Recording set-up

1. Start a fresh server with a fresh build (DRY_RUN.md §1).
2. Seed the stage before the chapter you film (DRY_RUN.md §2, always with `--recording`):

   | Chapter | Seed | What the seed already holds |
   |---|---|---|
   | 1 Phase 0 | none (empty server) | nothing |
   | 2 Mission architecture | `--stage S0 --recording` | mission definition, mission need, stakeholders and MOEs |
   | 3 System level | `--stage S1 --recording` | + product tree, functions, requirement baseline |
   | 4 Subsystem level, 5 Integration | `--stage S2 --recording` | + equipment, modes, budgets, links |
   | 6 Reviews | `--stage S4 --recording` | the full study **without** the Licensing tab, the allocation ledger, the negotiations, the cost pricing, the debris assessment, the reliability and thermal models; ECP-01 and ECP-02 proposed |

3. One presenter claims every seat group (Seats drawer → each card → **Claim**) and switches the
   active seat at the start of each scene. Or use one browser profile per seat.
4. Leave the protocol mode at **Warn** (the default). Say once, in 1.7, that an instructor can set
   it to **Block**.
5. The register of the coaching cards is **learning** (the default) for the whole recording.

**Narration (opening).** "This recording follows one student team as it designs Northern Fire and
Ice, a 3U CubeSat that maps burn scars and river ice for northern communities. Each position works
in its own seat, and the tool keeps the shared design consistent as decisions are made."

---

## 1. Phase 0: the need (Home → Mission Wizard)

### Scene 1.1 — Join and create the mission

- **Seat:** none yet (name prompt).
- **Panel:** Home.
- **Actions:** 1. Name prompt: **Your name** = `NFI Team leader` (a role) → **Join**. 2. **Create New Mission**.
- **On screen:** the four-step wizard, step 1.
- **Caption EN:** We start from the problem, not from a spacecraft.
- **Caption FR:** On part du problème, pas d'un satellite.
- **Gate state after:** no study yet.

### Scene 1.2 — Problem (wizard step 1)

- **Seat:** Team leader.
- **Panel:** Wizard step 1 (`[data-decision='D-1.4-PROBLEM']`).
- **Actions:** Mission Name `Northern Fire and Ice`; Problem Statement and Operational Context from
  `mission.yaml → wizard.step1_problem` (paste); chip **Earth Observation**; open `D-1.4-PROBLEM`,
  paste LB-01, **Save decision record** → **Next**.
- **On screen:** the problem statement naming the two hazards, the communities and the central
  question (can a low-cost instrument reproduce the reference missions?).
- **Caption EN:** The problem names the hazards, the users and the question the mission must answer.
- **Caption FR:** Le problème nomme les aléas, les utilisateurs et la question à laquelle la mission doit répondre.
- **Gate state after:** no study yet (the study is created at step 4).

### Scene 1.3 — Stakeholders and objectives (wizard step 2)

- **Seat:** Team leader.
- **Panel:** Wizard step 2.
- **Actions:** six stakeholders and five objectives exactly as `mission.yaml → wizard.step2_*`
  (v1 §1.3 table: sponsor, communities, science team, operators, regulators, student team; O1, O3,
  O4 primary, O2 exploratory, C1 constraint). Record `D-1.4-STAKEHOLDERS` (LB-02) and
  `D-1.4-OBJECTIVES` (LB-03) → **Next**.
- **On screen:** each objective with its measure ("≥ 40 usable cloud-free scene pairs over ≥ 3
  burns in year 1 …").
- **Caption EN:** Each objective carries the measure that will tell us, after launch, whether it was met.
- **Caption FR:** Chaque objectif porte la mesure qui dira, après le lancement, s'il est atteint.
- **Gate state after:** no study yet.

### Scene 1.4 — Alternatives (wizard step 3)

- **Seat:** Systems.
- **Panel:** Wizard step 3 (`D-1.4-SPACE`).
- **Actions:** with the mission definition's real values (GSD 60 m, revisit 3 d, latency 24 h,
  regional coverage, data ownership and scheduling control required), check the nine alternative
  cards; select **New dedicated CubeSat**; **Why this approach?** = `mission.yaml →
  step3_alternatives.rationale`; record LB-04 → **Next**.
- **On screen:** Sentinel-2 and Landsat ranked high and kept as the calibration reference; the
  dedicated CubeSat selected.
- **Caption EN:** The free missions stay as the reference; only a dedicated satellite can be tasked by the communities.
- **Caption FR:** Les missions gratuites restent la référence ; seul un satellite dédié peut être programmé par les communautés.
- **Gate state after:** no study yet.

### Scene 1.5 — Architecture and seats (wizard step 4)

- **Seat:** Team leader.
- **Panel:** Wizard step 4.
- **Actions:** preset **Single Spacecraft (LEO)**; Design Lifetime 3; Target Mass 6; Team size **9**
  (`[data-testid=wizard-team-size]`); optional seats ☑ Propulsion ☑ Cost & risk → **Create Mission &
  Start Design**. Claim all seat groups (0.3).
- **On screen:** the starting product tree, five "The mission shall …" requirements, the Seats
  drawer with 11 seats plus Customer and Observer.
- **Caption EN:** Creating the mission builds the first product tree and divides ownership among the seats.
- **Caption FR:** La création de la mission construit le premier arbre produit et répartit les responsabilités entre les postes.
- **Gate state after:** the study exists; the MDR waits for the mission definition (scene 1.6), then as S0 below

### Scene 1.6 — Mission definition editor

- **Seat:** Team leader, then Mission analysis & ops.
- **Panel:** level 0 → **Traceability** → mission-need card → **Edit** (mission definition editor).
- **Actions:** enter every field of `mission.yaml → mission_patch.requirements` (SSO 590 km,
  i = 97.75°, LTAN 22:30, three payload entries, four ground stations, link, launch, disposal) and
  `mission_need.conops_summary`. Record LB-05 (node time: the daylight pass descends at 10:30, so
  `ltan` = 22:30).
- **On screen:** the mission-need card with SSO 590 km, 97.75°, LTAN 22:30, the four stations and
  the ConOps summary.
- **Caption EN:** The researched orbit and payload replace the wizard's placeholders.
- **Caption FR:** L'orbite et la charge utile étudiées remplacent les valeurs provisoires de l'assistant.
- **Gate state after:** seed S0: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 2/5 (open: PRR-EC-04, PRR-EC-05, PRR-EC-06) · SRR not ready, must 2/8 (open: SRR-EC-01, SRR-EC-02, SRR-EC-03, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 1/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-EC-08, PDR-RD-03)

### Scene 1.7 — Phase 0 entry: the Phase card (new)

- **Seat:** Team leader (Instructor for the mode).
- **Panel:** breadcrumb **V&V** → Review Gates → MDR → the **Phase card** at the top.
- **Actions:** 1. Read the three blocks aloud: **Before you start**, **Deliverables this phase**,
  **Analysis standard**. 2. Point to the coaching card (register **learning**). 3. Instructor: show the
  **Protocol checks** selector (Warn / Block / Off), leave **Warn**. 4. Team leader: Traceability →
  mission-need card → **Stakeholders**: complete each stakeholder's interest and authority from
  `stakeholders.yaml` (the S0 seed already holds them; show one, the communities). 5. **Diagrams** →
  **Stakeholder map**, then **Context diagram**.
- **On screen:** the deliverables of the MDR with ✅ / ⚠️ / ❌; the stakeholder map (interest ×
  authority); the context diagram with the regulator link.
- **Caption EN:** Each phase starts with the same three questions: what must be true, what we deliver, to what standard.
- **Caption FR:** Chaque phase commence par les trois mêmes questions : ce qui doit être vrai, ce que l'on livre, selon quelle norme.
- **Gate state after:** seed S0: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 2/5 (open: PRR-EC-04, PRR-EC-05, PRR-EC-06) · SRR not ready, must 2/8 (open: SRR-EC-01, SRR-EC-02, SRR-EC-03, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 1/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-EC-08, PDR-RD-03)

---

## 2. Mission architecture (level 0 Mission and level 1 Segment)

### Scene 2.1 — Blocks: complete the tree

- **Seat:** Systems.
- **Panel:** level 0 → **Blocks**.
- **Actions:** rename the spacecraft `Northern Fire and Ice spacecraft` (3U, Al 7075, deployables);
  add **Harness**; rename Propulsion to `Disposal (drag sail)` (domain propulsion, owned by
  Propulsion); four stations `GS Ottawa`, `GS Yellowknife`, `GS Iqaluit`, `GS Inuvik` with the
  coordinates of `ground_stations.yaml → sites`; **Science Segment**; **Mission control centre
  (Ottawa, VPN to the remote sites)**; **Rideshare launch and 3U deployer** with **In scope** off.
- **On screen:** the product tree with the disposal subsystem and the four stations.
- **Caption EN:** One spacecraft, a disposal subsystem instead of propulsion, four stations across Canada.
- **Caption FR:** Un satellite, un sous-système de retrait au lieu de la propulsion, quatre stations au Canada.
- **Gate state after:** seed S1: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)
- **Note:** the station element's **Antenna diameter (m)** field is a dish diameter; enter 1.8 m (the
  equivalent aperture of the 15 dBic Yagi at 401 MHz) and say so in the description. The link cases
  carry the real gain (scene 4.4). [UI-GAP kept, A.1]

### Scene 2.2 — Decide: orbit, launch and ground; record the system-level trades (new)

- **Seat:** Mission analysis & ops (Systems for T-M02).
- **Panel:** level 0 → **Decide** → Orbit Trade Study, Ground Segment Trade, Ground Contact Schedule;
  then the trade cards **T-M01** and **T-M02**.
- **Actions:** 1. **Evaluate Orbit Options**; [TOOL-CHECK] period 96.5–96.6 min, i 97.7–97.8°,
  eclipse 34–36 min. 2. **Evaluate Ground Architectures**; **Predict Contact Windows**: union
  125.7 min/day [TOOL-CHECK ±5 %]. 3. On each result, **Record as trade** (level *Mission*, gate
  *MDR*): T-M01 operational orbit (590 km, LTDN 10:30) and T-M02 launch approach (rideshare,
  3U deployer). 4. Open T-M01 in the matrix: criteria with their MOE sources, absolute scale,
  ±20 % sensitivity line.
- **On screen:** the trade-by-gate summary (`[data-testid=trade-gate-summary]`) showing MDR 2 of 2
  decided; the T-M01 matrix with its sources.
- **Caption EN:** Every phase needs at least one system-level trade; at the MDR they are the orbit and the launch.
- **Caption FR:** Chaque phase demande au moins un compromis de niveau système ; à la MDR, ce sont l'orbite et le lancement.
- **Gate state after:** seed S1: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 2.3 — The fourth station: the ripple (negotiation GS4, new)

- **Seat:** Mission analysis & ops proposes; Comms & OBDH, Power, Systems sign.
- **Panel:** level 0 → **Decide** → **Negotiations** → **New negotiation** → **GS4**.
- **Actions:** 1. The record opens with two computed options: three sites without Inuvik, and four
  sites with Inuvik, with the difference and **Affects** (Comms & OBDH capacity, Power downlink share
  and orbit average, Systems communications allocation, Mission analysis contact plan). 2. Choose
  **with**. 3. Each seat signs: **Sign as mission_analyst**, **comms_engineer**, **power_engineer**,
  **systems_engineer**. Record LB-06.
- **On screen:** union 93.4 → 125.7 min/day, capacity about +11.7 MB/day, data margin −12 % → +38.5 %,
  downlink share 5 → 9 %, orbit average +0.24 W; the record turns **agreed** with four signatures.
- **Caption EN:** One station decision moves numbers owned by four other seats; each one agrees before it stands.
- **Caption FR:** Une décision sur une station fait bouger des valeurs tenues par quatre autres postes ; chacun donne son accord avant qu'elle tienne.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 2.4 — Budget: spacecraft allocations

- **Seat:** Systems.
- **Panel:** level 0 → **Budget** (Mass, Power, Cost).
- **Actions:** spacecraft allocation 6.0 kg (CDS 3U limit), 12.2 W (EOL orbit-average generation with
  wings at β = 15°), cost target 0.8 MEUR for space and ground hardware and tests, launch provided
  (PI, 2026-11-10). Record `D-2.4-MASS` (LB-07). Show the study's margin hold: 20 % system margin held
  through the PDR, with the ECSS ladder (20 / 15 / 10 %) quoted beside it.
- **On screen:** the margin tower with 6.0 kg and the 20 % hold.
- **Caption EN:** We allocate the full six kilograms and hold a 20 % system margin until the PDR.
- **Caption FR:** On alloue les six kilogrammes et l'on garde une marge système de 20 % jusqu'à la PDR.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 2.5 — Modes (ConOps)

- **Seat:** Mission analysis & ops.
- **Panel:** level 0 → **Modes**.
- **Actions:** **Create the ConOps modes**, then edit to `modes.yaml → modes` (nine modes: nominal
  85 %, imaging 5 %, downlink 9 %, Night SWIR 1 %, Sail deploy / end of life); seven added
  transitions from `modes.yaml → transitions_added`. Phases and scenarios: **ConOps scenarios**
  (the S2 seed loads the v2 scenarios; show one).
- **On screen:** the mode state diagram (Diagrams → Mode state diagram).
- **Caption EN:** Most of the orbit is nadir standby, with a few minutes of imaging and about nine of downlink.
- **Caption FR:** L'essentiel de l'orbite se passe en attente au nadir, avec quelques minutes d'imagerie et environ neuf de transmission.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 2.6 — Requirements at mission level

- **Seat:** Team leader (codes), Customer (MIS-SCI), Mission analysis, Comms & OBDH, Payload, Propulsion.
- **Panel:** level 0 → **Requirements**.
- **Actions:** 1. Edit each wizard requirement and set its **Code** (`OBJ-O1` … `OBJ-C1`) in the row
  editor. 2. **+ Add Requirement** for five rows (MIS-SCI-01, MIS-SCI-02, MIS-DAT-01, MIS-COV-03,
  MIS-DIS-01): level, code, text, type, method, allocation, threshold, **Objectives** column, link ↑.
  3. **Import** the rest of `requirements.yaml` (302 rows, by level: mission 68, segment 40, system
  67, subsystem 115, interface 12) with the bulk import. 4. **SMART Check**.
- **On screen:** the requirements table filtered on level mission, objectives column filled.
- **Caption EN:** Each requirement has a threshold, a verification method and a parent objective.
- **Caption FR:** Chaque exigence a un seuil, une méthode de vérification et un objectif parent.
- **Gate state after:** seed S1: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 2.7 — Analyses at mission level

- **Seat:** Mission analysis & ops.
- **Panel:** level 0 → **Analyses**: `mission_simulation`, `ground_segment`, `physics`.
- **Actions:** **Run** each. [TOOL-CHECK] period 96.5–96.6 min, eclipse 34–36 min; four stations
  `ok`; lifetime with sail 3.0–3.4 y.
- **On screen:** the ground-segment card with the four UHF stations; the debris line with the sail.
- **Caption EN:** From 590 km the satellite would stay up for decades; the drag sail brings it down in about three years.
- **Caption FR:** Depuis 590 km, le satellite resterait en orbite des décennies ; la voile de traînée le fait rentrer en trois ans environ.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 2.8 — Risk register

- **Seat:** Team leader enters; Cost & risk maintains.
- **Panel:** **V&V** → Risk Register.
- **Actions:** the 37 risks of `risks.yaml` (the S3 seed loads them; show the entry form on one,
  RSK-035 "ECP-01 open"), the 5 × 5 matrix, **Export CSV**.
- **On screen:** the matrix with the highest risks and their owners.
- **Caption EN:** Each risk has an owner and a mitigation, and the matrix shows where to act first.
- **Caption FR:** Chaque risque a un responsable et une mesure de réduction ; la matrice montre où agir d'abord.
- **Gate state after:** seed S3: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 2.9 — Cost: price the project first (new)

- **Seat:** Cost & risk.
- **Panel:** **Budget** → **Cost** (project view) → **Price**.
- **Actions:** **Price** the project: labour, test campaigns and reserve from `configs/cost_pricing.yaml`,
  launch provided. Review the lines; keep the team's edits.
- **On screen:** the priced total against the 0.8 MEUR target (launch 0, labour, test campaigns, 20 % reserve).
  MDR-EC-08 and PRR-EC-11 now judge the priced total instead of the design loop's parametric
  estimate (both pass before and after on this study; say that the criterion is only meaningful now).
- **Caption EN:** The cost criterion can only be judged once the project is priced: labour, tests and reserve.
- **Caption FR:** Le critère de coût ne se juge qu'une fois le projet chiffré : main-d'œuvre, essais et réserve.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

---

## 3. System level (level 2: `Northern Fire and Ice spacecraft`)

### Scene 3.1 — Functions, links to requirements, FFBD (new steps)

- **Seat:** Systems.
- **Panel:** level 2 → **Functions**; then **Requirements** (function column); then **Diagrams**.
- **Actions:** 1. The function tree of `functions.yaml` (12 functions F1–F12, enabling processes,
  allocations, exchanges; the S1 seed imports it; show **+ child** and **Allocate** on one). 2. In
  Requirements, the **Function** column links each requirement to its function; show coverage
  12 / 12. 3. Diagrams → **Function tree**, **Function × product allocation**, **Functional flow
  block diagram**.
- **On screen:** the FFBD; coverage 12 / 12.
- **Caption EN:** Every function is allocated to a product and traced to the requirements that ask for it.
- **Caption FR:** Chaque fonction est allouée à un produit et reliée aux exigences qui la demandent.
- **Gate state after:** seed S1: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 3.2 — Budget at system level

- **Seat:** Systems.
- **Panel:** level 2 → **Budget** (Mass, Power).
- **Actions:** subsystem allocations from `budgets.yaml` (mass 0.76 kg payload … ; power by line).
  [TOOL-CHECK] the system margin line after equipment: nominal ≈ 3.87 kg, with maturity ≈ 4.15 kg,
  with 20 % ≈ 5.01 kg (v2).
- **On screen:** the budget rows with their allocations.
- **Caption EN:** Systems hands each subsystem a mass and power envelope.
- **Caption FR:** L'ingénierie système attribue à chaque sous-système une enveloppe de masse et de puissance.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 3.3 — The allocation ledger and the mass envelopes (negotiation N7, new)

- **Seat:** Systems proposes; each subsystem seat agrees its own line; all sign N7.
- **Panel:** level 2 → **Budget** → **Allocation ledger** (`#allocation-ledger`); then **Decide** →
  **Negotiations** → **New negotiation** → **N7**.
- **Actions:** 1. Systems: **Propose from the roll-up**: one line per subsystem and resource, with
  the system reserve held by Systems. 2. Film one agreement: Power seat → EPS line → **Agree**. The
  other seats agree theirs (or dispute with a reason, then agree after the edit). 3. Requirements
  now show the allocation rows (AR-…) under their SYS-BUD parents. 4. N7: two options computed
  (hold the 20 % margin through the PDR; use the 15 % of the ladder), choose **hold**; Systems and
  every subsystem seat sign.
- **On screen:** every ledger line **agreed**, the reserve line; N7 **agreed** with the reserve to the
  6.0 kg limit.
- **Caption EN:** An allocation counts only once the seat that must live with it has agreed.
- **Caption FR:** Une allocation ne compte qu'une fois acceptée par le poste qui devra la tenir.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04) (PDR-EC-07 reads the ledger)

### Scene 3.4 — Trades at subsystem level (T-04, T-05)

- **Seat:** Power.
- **Panel:** level 3 (EPS focus) → **Decide** → Pugh (weighted, pairwise weights).
- **Actions:** T-04 solar array: DMSA wings +0.65 over body-mounted; T-05 battery: BP4 +0.95. **Record
  decision** (LB-13, LB-14), then `D-2.4-POWER` (LB-15).
- **On screen:** the Pugh totals and the decision records.
- **Caption EN:** Body-mounted cells give four watts at end of life, less than we need; the wings give twelve.
- **Caption FR:** Les cellules sur la structure donnent quatre watts en fin de vie, moins que le besoin ; les ailes en donnent douze.
- **Gate state after:** seed S3: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 3.4b — System-level trade for the SRR: data architecture (T-S01, new)

- **Seat:** Comms & OBDH.
- **Panel:** level 2 → **Decide** → T-S01 **End-to-end data architecture** (level *System*, gate *SRR*).
- **Actions:** show the criteria and their MOE sources, the absolute scores, the ±20 % line; the
  decision is recorded with its rationale (seeded at S3: decided).
- **On screen:** trade-by-gate summary: SRR 1 of 1 decided (SRR-EC-04 reads this panel only).
- **Caption EN:** At the SRR the system-level trade is the data architecture, from the camera to the user.
- **Caption FR:** À la SRR, le compromis de niveau système porte sur l'architecture des données, de la caméra à l'utilisateur.
- **Gate state after:** seed S3: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 3.5 — Interfaces

- **Seat:** Systems.
- **Panel:** level 2 → **Interfaces**.
- **Actions:** **Propose links** → review → **Accept all**; **+ Add Interface** for the ten links of
  v1 §3.5 (PPS, CSP over CAN, CSI-2, the two sail release circuits, RF, VPN).
- **On screen:** the N² chart (Diagrams).
- **Caption EN:** The proposer finds the obvious links; the team adds the ones only it knows.
- **Caption FR:** Le proposeur trouve les liens évidents ; l'équipe ajoute ceux qu'elle seule connaît.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 3.6 — Options

- **Seat:** Systems.
- **Panel:** context bar → option switcher → **branch**; then Analyses → **Compare options**.
- **Actions:** branch `B: body-mounted + P31u + BP4`; overrides EPS mass −0.32 kg, power −0.4 W;
  compare. Keep A.
- **On screen:** B lighter but failing the power margin.
- **Caption EN:** Option B saves mass but does not close the power budget, so A stays the baseline.
- **Caption FR:** L'option B gagne de la masse mais ne boucle pas le bilan de puissance ; A reste la référence.
- **Gate state after:** unchanged.

### Scene 3.7 — Spacecraft: stack and faces

- **Seat:** Structures & config.
- **Panel:** level 2 → **Spacecraft**.
- **Actions:** **Auto-place** → 3D / Face map / Side elevation; [TOOL-CHECK] stack ≈ 295 of ≈ 328 mm;
  resolve the +Z contention (star tracker to a long face; +Z kept for the sail; LB-21) → **Approve
  layout**.
- **On screen:** the side elevation with about 10 % height margin.
- **Caption EN:** The stack fits with a tenth of its height to spare; the end face is kept for the sail.
- **Caption FR:** L'empilement tient avec un dixième de hauteur en réserve ; la face d'extrémité est gardée pour la voile.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 3.8 — First design loop

- **Seat:** Systems.
- **Panel:** context bar → **Run Analysis**.
- **Actions:** run after every custom element has its mass (chapter 4). [TOOL-CHECK] converged; mass
  ≤ 6.0 kg with margin (≈ 5.0 kg); power × 1.2 ≤ EOL generation; data; cost.
- **On screen:** the design-loop results.
- **Caption EN:** The loop checks that mass, power, data and cost close together.
- **Caption FR:** La boucle vérifie que masse, puissance, données et coût bouclent ensemble.
- **Gate state after:** seed S3: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03, PDR-RD-04)

---

## 4. Subsystem level (level 3), one seat per subsystem

Each scene follows the same pattern: drill into the subsystem and take its seat; **Blocks** →
**Equipment Catalog** (domain chip, search by name); quantity; mass and on-power where
`equipment.yaml` gives a correction; **Properties: <name>**; check the requirements allocated here;
**Record decision**. The selections, quantities and corrections are those of `equipment.yaml`
(v1 §4 tables).

### Scene 4.1 — Payload

- **Seat:** Payload.
- **Panel:** level 3 Payload.
- **Actions:** the two Alvium cameras, the CM4 controller (3.0 W average, 5 W peak in the matrix), the
  optics at 0 kg (traceability), and three custom items with **Equipment Catalog → Custom component**
  (SWIR filter 1610/90 nm TRL 4, optical bench and baffles 0.20 kg TRL 4, payload harness 0.05 kg
  TRL 5); **TRL (1-9)** in the Properties of each custom element. Properties (payload) as v1 §4.1.
  Trades T-01 (1610/90 +0.55), T-02, T-03 (LB-09 … LB-11).
- **On screen:** [TOOL-CHECK] GSD 58.2 m and swath 150.7 km at 590 km.
- **Caption EN:** The SWIR filter moves to 1610 nm to match Sentinel-2 band 11.
- **Caption FR:** Le filtre SWIR passe à 1610 nm pour correspondre à la bande 11 de Sentinel-2.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.2 — EPS

- **Seat:** Power.
- **Panel:** level 3 EPS.
- **Actions:** P60, BP4, two DMSA wings, four body panels, power harness; Properties (power) 14.4 V,
  dual-deploy, Li-ion. The S2 seed sets the arrays' orbit-average EOL generation (12.2 W total,
  3.98 W body only).
- **On screen:** [TOOL-CHECK] Spacecraft tab: eclipse ≈ 2.9 W; energy per orbit ≈ 19.6 Wh against
  ≈ 6.7 Wh.
- **Caption EN:** The wings give three times the orbit-average load at end of life.
- **Caption FR:** Les ailes donnent trois fois la charge moyenne orbitale en fin de vie.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.3 — AOCS

- **Seat:** AOCS.
- **Panel:** level 3 AOCS.
- **Actions:** CubeADCS Gen 2 with CubeStar, fine sun sensor, GNSS kit; Properties 1.0 / 0.1 / 1.0;
  T-08 (Gen 2 +0.20; LB-12).
- **On screen:** the AOCS rows with the star tracker.
- **Caption EN:** A tenth of a degree of knowledge needs a star tracker, the most expensive unit on board.
- **Caption FR:** Un dixième de degré de connaissance d'attitude demande un viseur d'étoiles, l'équipement le plus cher à bord.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.4 — Communications and the link cases

- **Seat:** Comms & OBDH.
- **Panel:** level 3 Communications; then **Analyses → Link budget**.
- **Actions:** Murgas transceiver (3.3 W TX DC), AntS, two RF cables; Properties (ttc) UHF, 1 W,
  38.4 kbps, AES-256. T-07 last (LB-17). The eight link cases of `NUMBERS.yaml → links` are named
  cases stored with the study (the S2 seed loads them; show DL-2 and **Apply as design case**).
  Record LB-18.
- **On screen:** DL-2 northern site +4.0 dB; DL-1 Ottawa urban +0.4 dB [TOOL-CHECK ±0.2 dB].
- **Caption EN:** The downlink closes with four decibels at a quiet northern site and almost nothing in a city.
- **Caption FR:** La liaison descendante boucle avec quatre décibels sur un site nordique calme et presque rien en ville.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.5 — On-board computer

- **Seat:** Comms & OBDH.
- **Panel:** level 3 On-Board Computer.
- **Actions:** NanoMind A3200; description as v1 §4.5 (SDLS in the OBC software, HK SIDs per
  `hk_sids.yaml`).
- **On screen:** the OBC row.
- **Caption EN:** Encryption sits in the computer's software, independent of the radio.
- **Caption FR:** Le chiffrement est dans le logiciel de l'ordinateur de bord, indépendant de la radio.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.6 — Thermal (equipment)

- **Seat:** Thermal.
- **Panel:** level 3 Thermal.
- **Actions:** straps, coating, 2 W Kapton heater, MLI; Properties 0 / 25 °C, white paint.
- **On screen:** the thermal rows.
- **Caption EN:** The SWIR camera must image between 0 and 25 °C; the thermal design keeps it there.
- **Caption FR:** La caméra SWIR doit imager entre 0 et 25 °C ; la conception thermique l'y maintient.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03) (the nodal model is built at the PDR, scene 6.8)

### Scene 4.7 — Structure

- **Seat:** Structures & config.
- **Panel:** level 3 Structure.
- **Actions:** ISISPACE 3U frame (LB-20), stand-offs, fastener kits, PC/104 stack harness.
- **On screen:** the structure rows.
- **Caption EN:** An off-the-shelf frame with flight heritage carries a 5 % maturity margin.
- **Caption FR:** Une structure du commerce avec un héritage de vol porte une marge de maturité de 5 %.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.8 — Disposal (drag sail)

- **Seat:** Propulsion.
- **Panel:** level 3 Disposal (drag sail).
- **Actions:** ARTICA configuration A (0.30 kg, 0 W average; 6 W only in the end-of-life mode); the
  custom independent timer and battery (0.08 kg, TRL 4); T-06 (LB-16).
- **On screen:** the two disposal rows.
- **Caption EN:** The team adds its own timer and battery so the sail deploys even if the computer has failed.
- **Caption FR:** L'équipe ajoute sa propre minuterie et sa batterie : la voile se déploie même si l'ordinateur est en panne.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.9 — Ground stations

- **Seat:** Mission analysis & ops (Comms & OBDH for the RF items).
- **Panel:** level 3 under each station → **RF chain**.
- **Actions:** the items of `ground_stations.yaml → rf_chains`; Yamcs under the mission control
  centre; record LB-19.
- **On screen:** the RF chain of Inuvik with the heated rotator.
- **Caption EN:** Three of the four stations are unattended in the North, at minus forty-five in winter.
- **Caption FR:** Trois des quatre stations sont automatiques, dans le Nord, à moins quarante-cinq en hiver.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.10 — Cost & risk (equipment)

- **Seat:** Cost & risk.
- **Panel:** V&V → **BOM**.
- **Actions:** compare the BOM with the researched list prices (LB-22); RSK-009 to **mitigating**.
- **On screen:** the BOM total.
- **Caption EN:** The bill of materials is one input to the cost; the priced project is the other.
- **Caption FR:** La nomenclature est une entrée du coût ; le projet chiffré en est une autre.
- **Gate state after:** seed S3: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 4.11 — Modes matrix

- **Seat:** Power, with every subsystem seat.
- **Panel:** level 0 → **Modes** → matrix.
- **Actions:** **Propose powers per mode**; type `modes.yaml → matrix_w` where it differs (ARTICA,
  ADCS in LEOP, controller, radio); **Accept**; **Run the rules**.
- **On screen:** [TOOL-CHECK] orbit average 4.17 W; imaging 15.68 W; downlink 9.17 W.
- **Caption EN:** With every unit's power per mode, the orbit average is just over four watts.
- **Caption FR:** Avec la puissance de chaque équipement par mode, la moyenne orbitale dépasse à peine quatre watts.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 4.12 — Science volume against the downlink (negotiation N1, new)

- **Seat:** Payload proposes; Comms & OBDH, Mission analysis & ops and Customer sign.
- **Panel:** **Decide** → **Negotiations** → **New negotiation** → **N1**; the **Sensitivity** strip
  below.
- **Actions:** 1. Three options computed from the study: keep 13 MB/day (robust to losing a site),
  raise to the largest that keeps 10 % margin, lower to what closes at the 19.2 kbit/s fallback; each
  with its margin and the compression it needs. 2. Show the sensitivity strip: margin against science
  target, compression ratio and rate tier. 3. Choose **keep**; the reopen trigger reads "if the
  compression measured on simulated scenes is below 1.3:1". 4. Payload, Comms & OBDH, Mission analysis
  and Customer sign. The PI decision D-PI-01 (raise the target?) stays open in the open-item register.
- **On screen:** C1 margin +38.5 %, worst site out +17.6 %, compression needed ≥ 1.28:1; N1 **agreed**.
- **Caption EN:** We keep thirteen megabytes a day because it still closes if a station is lost.
- **Caption FR:** On garde treize mégaoctets par jour, car le bilan boucle encore si une station est perdue.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 4.13 — Payload peak power and imaging duty (negotiation N3, new)

- **Seat:** Payload and Power; Mission analysis & ops, Thermal and Systems sign.
- **Panel:** **Decide** → **Negotiations** → **N3**.
- **Actions:** 1. Two options computed: imaging 5 % of the orbit with the flight rules (no transmission
  during an acquisition; imaging only above 40 % state of charge), or a larger imaging share. 2.
  Choose **keep**. 3. The five seats sign. The flight rules FR-01 and FR-02 are entered in scene 5.7.
- **On screen:** imaging mode 15.7 W, worst-eclipse depth of discharge 8.8 %; N3 **agreed**.
- **Caption EN:** The payload may draw its peak, under two flight rules that protect the battery and the link.
- **Caption FR:** La charge utile peut tirer sa crête, sous deux règles de vol qui protègent la batterie et la liaison.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

---

## 5. Integration and verification preparation

### Scene 5.1 — Electrical

- **Seat:** Power with Systems.
- **Panel:** level 2 → **Electrical**.
- **Actions:** **Propose from links**; set the nine lines of v1 §5.1 (rail, LCL trip, switchable, on at
  boot, on at separation); release B (independent timer) with **+ Add line**, "not on the EPS".
- **On screen:** [TOOL-CHECK] no finding on trip against load.
- **Caption EN:** Each load has its protected, switchable line; the second sail release stays off the EPS.
- **Caption FR:** Chaque charge a sa ligne protégée et commutable ; le second déclenchement de la voile reste hors de l'alimentation.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 5.2 — Data

- **Seat:** Comms & OBDH.
- **Panel:** level 2 → **Data**.
- **Actions:** **Propose from links**; CAN addresses, UART, CSI-2 rates, PPS lines, single string.
- **On screen:** the data-handling block diagram.
- **Caption EN:** One CAN bus carries the platform; the cameras talk to their controller directly.
- **Caption FR:** Un bus CAN porte la plateforme ; les caméras parlent directement à leur contrôleur.
- **Gate state after:** seed S2: MDR not ready, must 5/6 (open: MDR-EC-07) · PRR not ready, must 4/5 (open: PRR-EC-05) · SRR not ready, must 4/8 (open: SRR-EC-02, SRR-EC-06, SRR-EC-09, SRR-EC-10) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-03, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03)

### Scene 5.3 — ICD items

- **Seat:** Systems.
- **Panel:** level 2 → **ICD**.
- **Actions:** **+ item** for the nine exchange items of v1 §5.3 with their properties. The ICD
  inventory (`ICD-LAUNCH`, `ICD-RADIO-OBC`, `ICD-PAY-OBC`, `ICD-SAIL`, `ICD-SPACE-GROUND`) is seeded at S3;
  Issue A is raised at the PDR (scene 6.6).
- **On screen:** the ICD table with the five ICDs at draft.
- **Caption EN:** The interface control documents start as drafts and are issued at the PDR.
- **Caption FR:** Les documents de contrôle d'interface partent en brouillon et sont émis à la PDR.
- **Gate state after:** seed S3: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.4 — FDIR

- **Seat:** Systems.
- **Panel:** level 2 → **FDIR**.
- **Actions:** **Propose from design** → accept; load-shed stages and monitors of v1 §5.4.
- **On screen:** the three load-shed stages.
- **Caption EN:** The spacecraft sheds load in three stages before it reaches survival.
- **Caption FR:** Le satellite déleste en trois étapes avant d'atteindre la survie.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.5 — TM/TC and housekeeping

- **Seat:** Comms & OBDH.
- **Panel:** level 2 → **TM/TC**.
- **Actions:** **Propose from design** → accept; uplink settings, command-loss timer 72 h, rate ladder;
  the twelve SIDs of `hk_sids.yaml` with their real-time and stored intervals, the FULL and LEAN
  profiles, the pass classes (the S4 seed loads them; show SID 8 THERMAL at 60 s and SID 20 ADCS_DIAG
  off at boot).
- **On screen:** FULL 3.75 kbit/s designed, 4.8 kbit/s allocated; [TOOL-CHECK] CDR-EC-04.
- **Caption EN:** Housekeeping is organised the way operators use it: one packet per subsystem, each at its own rate.
- **Caption FR:** La télémesure de servitude suit l'usage des opérateurs : un paquet par sous-système, chacun à son rythme.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.6 — AOCS modes

- **Seat:** AOCS.
- **Panel:** level 2 → **AOCS modes**.
- **Actions:** B-dot gain proposed; minimum dwell 60 s; target pointing with roll ±30° and 60 s settle.
- **On screen:** the AOCS mode table.
- **Caption EN:** Imaging rolls up to thirty degrees and settles for a minute before each acquisition.
- **Caption FR:** L'imagerie s'incline jusqu'à trente degrés et se stabilise une minute avant chaque acquisition.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.7 — Operations (flight rules)

- **Seat:** Mission analysis & ops.
- **Panel:** level 2 → **Operations**.
- **Actions:** **Add rule** FR-01 … FR-11 (v1 §5.7); FR-01 and FR-02 cite N3.
- **On screen:** the eleven rules.
- **Caption EN:** Flight rule one pauses the transmitter for every acquisition; the budget allows for it.
- **Caption FR:** La règle de vol numéro un coupe l'émetteur pendant chaque acquisition ; le bilan en tient compte.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.8 — Diagrams, ending on the V (new ending)

- **Seat:** Systems.
- **Panel:** **Diagrams** (or from the Phase card, each deliverable's diagram).
- **Actions:** walk the phase set; **gaps** on each and fix any gap that points to a missing link; end on
  **V diagram**: products and reviews on the left, verification stages and validation on the right;
  then **Budget flow-down** and **Verification flow**. Download the diagrams document.
- **On screen:** the V diagram.
- **Caption EN:** The V shows what we define on the way down and how we prove it on the way up.
- **Caption FR:** Le V montre ce que l'on définit en descendant et comment on le prouve en remontant.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.9 — Analyses re-run

- **Seat:** Systems.
- **Panel:** context bar **Run Analysis**; **Analyses** cards; conflicts.
- **Actions:** design loop, `mission_simulation`, `ground_segment`, `physics`, `vv`, FMECA; resolve or
  accept each conflict (SRR-EC-05).
- **On screen:** no stale run.
- **Caption EN:** After every change, the analyses run again on the same design.
- **Caption FR:** Après chaque changement, les analyses repartent sur la même conception.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.10 — Licensing tab, filled by the team (new; replaces the v1 API-only forms)

- **Seat:** Team leader (applicant, data policy, security), Comms & OBDH (frequencies, stations),
  Mission analysis & ops and Propulsion (disposal), Payload (export control).
- **Panel:** tab strip → **Licensing**.
- **Actions:** fill each section from the baseline (the values of `seed.licensing_record`): applicant
  (placeholder name for the teaching example), 24/7 operations contact, participants, command and
  data protection plan (authentication, encryption, key management, VPN), data policy (open release
  within 6 months, CC BY 4.0, 10-year retention), deployer, disposal (two independent circuits,
  90-day timer, triggers). Watch the progress counter (**RSSSA §14–30: n of m**). Then the documents:
  **RSSSA Licence Application**, **ISED space station technical brief**, the earth-station briefs,
  **ITU API**, **Debris assessment**, **UN registration (Article IV)**, **Export-control summary**,
  **Licensing status and timeline**.
- **On screen:** the progress counter rising to complete; one document opened (the ISED brief with
  EIRP and PFD at 5°).
- **Caption EN:** The licences are written from the design: what the tool cannot derive, the team enters once.
- **Caption FR:** Les licences sont rédigées à partir de la conception : ce que l'outil ne peut pas déduire, l'équipe le saisit une fois.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.11 — Validation plan (new)

- **Seat:** Team leader with Customer.
- **Panel:** **V&V** → **Traceability** → the AIT panel → **Validation**.
- **Actions:** the seven validation activities V1–V7 of `vv_plan.yaml` (seeded at S3) and the twelve
  need-validation rows; show V1 with the performer "each stakeholder group" (users and operators,
  not engineers alone); the stages PRR … Phase E, ORR and CRR as validation stages.
- **On screen:** coverage of the objectives; the VP "Validation" chapter in the export.
- **Caption EN:** Verification asks whether we built it right; validation asks the users whether we built the right thing.
- **Caption FR:** La vérification demande si on l'a bien construit ; la validation demande aux utilisateurs si on a construit la bonne chose.
- **Gate state after:** seed S3: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 2/9 (open: PDR-EC-01, PDR-EC-02, PDR-EC-05, PDR-EC-06, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.12 — Assumptions and open items (new)

- **Seat:** Systems.
- **Panel:** Phase card → **Analysis standard**; **Decide** → **Open items**.
- **Actions:** show the assumption register (budget tags and requirement notes), the latency
  assumption due at the PDR; the open items with the gate each one blocks (D-PI-01, RIDs, conditional
  decisions, change proposals).
- **On screen:** the open-item list filtered on SRR, then PDR.
- **Caption EN:** Every assumption names the evidence that will replace it and the review where it is due.
- **Caption FR:** Chaque hypothèse nomme la preuve qui la remplacera et la revue à laquelle elle est attendue.
- **Gate state after:** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 5.13 — Documents and exports

- **Seat:** owners as listed in v1 §5.10.
- **Panel:** header **Export**.
- **Actions:** MRD, ConOps, SEMP, IRD, ICD, V&V matrix, BOM, margins, thermal report, launch ICD,
  simulator configuration, the review packs, Capella / ReqIF / SysML v2.
- **On screen:** the export drawer.
- **Caption EN:** Every document is generated from the one shared study.
- **Caption FR:** Chaque document est produit à partir de la même étude partagée.
- **Gate state after:** unchanged.

---

## 6. Reviews (V&V → Review Gates): MDR, PRR, SRR, PDR

Seed `--stage S4 --recording` for this chapter, then do scenes 2.3, 2.9, 3.3, 4.12, 4.13 and 5.10 if
they were not filmed on the same study (they are what the recording seed leaves empty).

Profile: **Full ECSS** (MDR → PRR → SRR → PDR → CDR → QR → AR → FRR), the default. The Team
leader chairs, the Observer reviews read-only, the Instructor signs off.

**At the start of chapter 6 (recording seed, nothing filmed yet):** recording seed S4: MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 5/8 (open: SRR-EC-09, SRR-EC-10, SRR-RD-03) · PDR not ready, must 4/9 (open: PDR-EC-02, PDR-EC-05, PDR-EC-07, PDR-RD-03, PDR-RD-04)

### Scene 6.1 — MDR: inventory, review, pass

- **Seat:** Team leader.
- **Panel:** V&V → Review Gates → MDR; Phase card; **Start review**.
- **Actions:** 1. Phase card: deliverables of the MDR ✅ (the system-level trades of scene 2.2,
  the stakeholder map, the ConOps), except **Objectives with measures of effectiveness** ⚠️: MOE-04
  and MOE-10 carry example thresholds and stay "to co-define" with the communities (PI ruling); say so. 2. **Start review**: the **stage-transition inventory** opens.
  Teaching beat: before the scene, delete the regulator link of the context diagram (or leave T-M02
  undecided); the inventory shows the warning; fix it; **Start review**. 3. Criteria: every must-pass
  criterion passes, MDR-EC-08 (cost) passes since scene 2.9. 4. **Pass**; **Record go / no-go** (LB-23:
  GO with actions taken from the open-item register).
- **On screen:** the inventory with the one warning, then clean; the MDR **passed**.
- **Caption EN:** Before a review starts, the tool lists what is missing; in Warn mode it is recorded, in Block mode it stops the review.
- **Caption FR:** Avant une revue, l'outil liste ce qui manque ; en mode Avertir c'est consigné, en mode Bloquer la revue ne démarre pas.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 6.2 — PRR: review, pass

- **Seat:** Team leader.
- **Panel:** V&V → Review Gates → PRR.
- **Actions:** inventory; **Start review**; criteria (orbit baselined, function tree, product tree,
  margins, requirements with methods, TRL, model philosophy, ground segment, risks, cost, debris);
  **Pass**.
- **On screen:** PRR **passed**.
- **Caption EN:** The preliminary requirements are baselined; the system requirements come next.
- **Caption FR:** Les exigences préliminaires sont figées ; les exigences système viennent ensuite.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 6.3 — SRR (1): issue the SEMP

- **Seat:** Systems (Team leader approves).
- **Panel:** V&V → Review Gates → SRR → Phase card → **Systems engineering management plan**.
- **Actions:** open the SEMP generated from the study (Export → SEMP: phases, reviews, seats, the
  change control, the margin policy); review it; **Record the SEMP issue** with the note "Reviewed for
  the SRR".
- **On screen:** SEMP **Issue A** with date and seat; SRR-EC-09 turns to pass.
- **Caption EN:** The management plan is written from the study and issued before the SRR.
- **Caption FR:** Le plan de management est rédigé à partir de l'étude et émis avant la SRR.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 6/8 (open: SRR-EC-10, SRR-RD-03) · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 6.4 — SRR (2): run and accept the debris assessment

- **Seat:** Mission analysis & ops with Propulsion.
- **Panel:** **Licensing** → Disposal → **Debris assessment** card.
- **Actions:** **Run**: lifetime with and without the sail over the solar-cycle cases, casualty risk
  (a 3U demises), collision probability; read the result; **Accept at SRR** with the note "Lifetime,
  casualty risk and collision probability reviewed".
- **On screen:** lifetime with sail ≈ 3.0 y nominal / 3.4 y weak cycle against the 5-year rule; the
  assessment **accepted (SRR)**; SRR-EC-10 turns to pass.
- **Caption EN:** The sail is what makes the mission licensable: the assessment shows re-entry well within five years.
- **Caption FR:** C'est la voile qui rend la mission autorisable : l'évaluation montre une rentrée bien en deçà de cinq ans.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR not ready, must 7/8 (open: SRR-RD-03) · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 6.5 — SRR (3): decide ECP-02, the launch request

- **Seat:** Mission analysis & ops presents; affected seats agree; Team leader decides (change board).
- **Panel:** **Decide** → **Change control** → `ECP-02` (`[data-testid=change-flow-ECP-02]`).
- **Actions:** 1. **Start change review (impact preview)**: the preview recomputes the study at
  550 km (the bottom of the requested range): contacts, data capacity and margin, disposal lifetime, energy. 2. Each affected seat
  reads its line and **Agree**s. 3. Team leader: note "Injection 550-600 km acceptable" →
  **Approve and update the baseline**. 4. Show **Requirements updated: SEG-LS-02, MIS-COV-03,
  PAY-OPT-04** and open SEG-LS-02 and PAY-OPT-04 in Requirements: the launch request now names the
  550-600 km range; the swath requirement is restated at 550 km, where it just meets 140 km.
- **On screen:** the impact lines with the seat that owns each (measured on the dry run): union of passes 125.7 → 118.0 min/day, capacity −1.7 MB/day, data margin 38.6 → 34.6 %, sail lifetime (worst cycle) 3.3 → 2.3 y, no-sail lifetime (worst cycle) 20.7 → 10.7 y. [TOOL-CHECK] the change record states 5.0 → 4.1 y for the no-sail lifetime in a strong cycle and ≥ 117.6 min/day; the preview quotes the worst cycle, so say which case is on screen. After approval: **New baseline: mission baseline, revision 1 (ECP-02)** (the last review passed is the PRR); SRR-RD-03 turns to pass; the SRR becomes ready.
- **Caption EN:** A change is approved only after every seat it touches has seen its impact and agreed; the baseline then moves.
- **Caption FR:** Un changement n'est approuvé qu'après l'accord de chaque poste touché, impact à l'appui ; le référentiel évolue alors.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR not ready, must 5/9 (open: PDR-EC-02, PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 6.6 — SRR pass; PDR (1): ICDs at Issue A

- **Seat:** Team leader (SRR); Systems with the provider and consumer seat of each ICD (PDR).
- **Panel:** V&V → Review Gates → SRR → **Start review** → **Pass**; then level 2 → **ICD** tab.
- **Actions:** 1. SRR: inventory clean; every must-pass criterion passes; **Pass**. 2. ICD tab: for each
  of `ICD-LAUNCH`, `ICD-RADIO-OBC`, `ICD-PAY-OBC`, `ICD-SAIL`, `ICD-SPACE-GROUND`: **Issue** (note
  "Issue A for the PDR"), then the provider seat and the consumer seat each **Sign**.
- **On screen:** SRR **passed**; the five ICDs at **Issue A**, two signatures each; PDR-EC-02 passes.
- **Caption EN:** An interface is fixed only when both sides have signed the same issue.
- **Caption FR:** Une interface n'est figée que lorsque les deux côtés ont signé la même édition.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR not ready, must 6/9 (open: PDR-EC-05, PDR-RD-03, PDR-RD-04)

### Scene 6.7 — PDR (2): reliability block diagram and FMEA

- **Seat:** Cost & risk (product assurance) with Systems.
- **Panel:** **V&V** → **Traceability** → the AIT panel → **Reliability**.
- **Actions:** **Run** the reliability block diagram over the mission-success horizon (12 months of
  science operations after commissioning, target 0.80, kept apart from the 3-year design life);
  **Propose** the FMEA (failure modes per unit, with the drag-sail deployment failure).
- **On screen:** mission reliability ≈ 0.88 ≥ 0.80 [TOOL-CHECK]; the FMEA rows; PDR-EC-05 passes.
- **Caption EN:** The reliability target is judged over the twelve months of science the mission promises, not the design life.
- **Caption FR:** L'objectif de fiabilité se juge sur les douze mois de science promis, pas sur la durée de vie de conception.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR not ready, must 7/9 (open: PDR-RD-03, PDR-RD-04)

### Scene 6.8 — PDR (3): thermal nodal model

- **Seat:** Thermal.
- **Panel:** **V&V** → **Traceability** → the AIT panel → **Thermal model**.
- **Actions:** **Propose** the nodal model (nodes, couplings, the hot and cold cases from the orbit
  season); **Solve**; read the units outside their range in the cold case; **Accept the sized
  heaters**; **Solve** again.
- **On screen:** hot and cold case temperatures per node; after the heaters, every unit inside its
  limits (SWIR camera, battery ≥ 0 °C while charging); the PDR thermal criterion passes.
- **Caption EN:** The cold case shows where heat is missing; the model sizes the heaters and checks again.
- **Caption FR:** Le cas froid montre où la chaleur manque ; le modèle dimensionne les réchauffeurs et vérifie à nouveau.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR not ready, must 8/9 (open: PDR-RD-04)

### Scene 6.9 — PDR (4): ECP-01, "when you disagree with the score, check the logic" (teaching scene)

ECP-01 proposes replacing the VNIR camera (IMX542) by a second IMX992 camera with a 35 mm f/1.4 lens
and an 875/50 filter. It comes from trade T-A01 (payload architecture), decided at the PDR. The
API twin of this scene is `ecp01_scene` in `test_w3_integration.py`.

- **Seat:** Payload leads; Systems, Cost & risk and Customer speak; Team leader decides the change.
- **Panel:** **Decide** → trade **T-A01** (absolute-scale matrix, ±20 % sensitivity, evidence per
  criterion, conditions of the trade); then **Change control** → `ECP-01`.
- **Actions, in four beats:**
  1. **What does the matrix say, and how robust is it?** Read the totals: **C 3.65, A 3.50**
     (D screened out on the must-criterion). Open the ±20 % line: the winner does not change for any
     weight. "The matrix says C, and the weights are not the problem."
  2. **Is the margin bigger than the uncertainty of the scores?** The margin is 0.15. One step on
     the 1-to-5 scale of a criterion weighted 0.2 or 0.25 moves a total by 0.2 to 0.25: one score
     moved by one step erases the lead. "Weight sensitivity tests the weights, not the scores."
  3. **Which scores are measured and which are assumed?** Read the **Evidence** line under each
     criterion: C's gains on NIR SNR and on technical risk are *Calculated* (the SNR is scaled from a
     datasheet; the snow exposure limit is scaled from the IMX542), and the cost of the custom NIR
     filter is *Assumed*. Nothing in C's favour has been measured.
  4. **Were the trade's own conditions met?** Read **Conditions of the trade** and the
     recommendation: a quote for the 875/50 filter, a breadboard measurement of the IMX992 over snow,
     a 0.82 kg payload allocation. None is met today.
  Then **decide**: Payload records the T-A01 decision **A** (the cameras in hand), with the rationale
  (the four beats in one paragraph), and opens **Conditional decision**: condition "Reopen ECP-01 if
  the 875/50 filter is quoted and the IMX992 breadboard measurement over snow is in before CDR", due
  2028-06-30, fallback "Keep A (IMX992 SWIR + IMX542 VNIR)", risk RSK-035, blocks **CDR**. Then
  **Change control** → ECP-01 → **Start change review** → the affected seats agree to the review →
  Team leader: note "Score overruled after checking the logic; see T-A01. Revisit before CDR if the
  filter quote and the breadboard measurement arrive." → **Reject**.
- **On screen:** the matrix with C highlighted; the ±20 % line "robust"; the evidence lines with
  *Calculated* and *Assumed*; the three unmet conditions; T-A01 **decided: A** with the condition and
  CDR; ECP-01 **Rejected**; the open-item list showing the conditional decision blocking the CDR.
- **Caption EN:** When you disagree with the score, check the logic: the margin, the evidence and the conditions, then decide and say what would change your mind.
- **Caption FR:** Quand on n'est pas d'accord avec la note, on vérifie le raisonnement : la marge, les preuves et les conditions, puis on décide et l'on dit ce qui ferait changer d'avis.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR ready, must 9/9

**Narration.** "The matrix ranks the two-IMX992 option first, and no change of weights moves it. But
its lead is smaller than one step on a single score, and the scores that give it the lead are
calculated, not measured. The trade itself said what evidence it needed, and none of it is in. So the
team keeps the cameras it has, records why, and names the two results that would reopen the change
before the CDR. Overruling a score is allowed; doing it without checking the logic is not."

### Scene 6.10 — PDR (5): allocations agreed, review, pass

- **Seat:** Team leader.
- **Panel:** V&V → Review Gates → PDR.
- **Actions:** Phase card: the PDR deliverables ✅ (ledger agreed, reliability, FMEA, thermal model,
  ECP-01 decided, the PDR trades decided); the ICD line shows ⚠️ "10 ICDs under issue control, 5 at
  issue A": the five due at the PDR are issued and signed, the other five are due at the CDR; **Start review**; criteria: every
  must-pass criterion passes; **Pass**; **Record go / no-go** (GO; actions: the conditional decision
  on T-A01, D-PI-01, the TBC launch ICD values). Instructor: sign-off.
- **On screen:** MDR, PRR, SRR and PDR **passed**; the allocated baseline.
- **Caption EN:** The design is allocated and its interfaces are fixed; the team can start the detailed design.
- **Caption FR:** La conception est allouée et ses interfaces sont figées ; l'équipe peut aborder la conception détaillée.
- **Gate state after:** MDR ready, must 6/6 · PRR ready, must 5/5 · SRR ready, must 8/8 · PDR ready, must 9/9

---

## 7. Logbook entries added in v2

The v1 entries LB-01 … LB-28 stay (`logbook.yaml`). Add, with **Save decision record** under the
context given (author = the active seat):

| Id | Seat | Saved under | Title | Entry text |
|---|---|---|---|---|
| LB-29 | mission_analyst | `decide:trade T-M01` | Orbit trade (MDR) | SSO 590 km, LTDN 10:30 kept: apogee ≤ 600 km with dispersion (ISED), 58.2 m GSD, sail lifetime 3.0-3.4 y; recorded as a mission-level trade for the MDR. |
| LB-30 | systems_engineer | `decide:trade T-M02` | Launch approach (MDR) | Rideshare with a 3U deployer; injection 550-600 km acceptable once ECP-02 is approved. |
| LB-31 | comms_engineer | `decide:trade T-S01` | Data architecture (SRR) | End-to-end data architecture decided for the SRR: ROI and quicklook products, lossless compression, four-site UHF network, per-pass virtual channels. |
| LB-32 | systems_engineer | `negotiation:N7` | Mass envelopes agreed | Allocations agreed by every subsystem seat; 20 % system margin held through PDR; reserve held by Systems. |
| LB-33 | mission_analyst | `negotiation:GS4` | Fourth station agreed | Inuvik kept; capacity, downlink share, communications power allocation and contact plan agreed by the four seats. |
| LB-34 | payload_lead | `negotiation:N1` | Science volume agreed | 13 MB/day kept, robust to a site loss; reopen if measured compression < 1.3:1; D-PI-01 open. |
| LB-35 | power_engineer | `negotiation:N3` | Imaging duty agreed | Imaging 5 % of the orbit under FR-01 and FR-02; reopen if the measured payload peak exceeds 12 W or the worst-eclipse DoD exceeds 15 %. |
| LB-36 | team_leader | `gate:SRR change ECP-02` | ECP-02 approved | Launch request 590 km nominal, 550-600 km acceptable; SEG-LS-02, MIS-COV-03 and PAY-OPT-04 updated; mission baseline revision 1. |
| LB-37 | payload_lead | `decide:trade T-A01` | T-A01 decided A, conditionally | Matrix C 3.65 vs A 3.50, robust to ±20 % weights, but the margin is below one score step, C's gains are calculated or assumed, and the trade's conditions are unmet. A kept; reopen before CDR on the filter quote and the breadboard measurement. |
| LB-38 | team_leader | `gate:PDR change ECP-01` | ECP-01 rejected | Rejected citing T-A01; revisit before CDR if the evidence arrives. |
| LB-39 | team_leader | `gate:D-GATE-*` | Stage-transition inventories | One record per review with the inventory result (warn mode), e.g. "MDR: 1 warning (context diagram regulator link), fixed before the review". |

---

## 8. Export, import and round trip

1. Systems: header **Export** → **Project file** (the complete study, format v2, with the licensing
   record and the exporting person's logbook).
2. **Close study** → Home → **Load from File** → the file: a new study, every row with a new id,
   nothing duplicated (the link proposer and the interface-requirement generator are not run).
3. The v1 checklist (`roundtrip_checklist.yaml`, frozen) plus the wave-3 objects are checked by
   `tests/fixtures/nfi/test_w3_close.py::test_round_trip_covers_the_v1_checklist_and_the_wave3_objects`:
   every table, every checklist row and every new object comes back identical after id mapping.
4. **Load Example Mission** → **Northern Fire and Ice (3U EO, full study to PDR)** opens the study as
   this script leaves it (`configs/examples/nfi/project.json`).

---

## Appendix A — Markers of v1 and where they stand

| v1 marker | Where in v1 | v2 status |
|---|---|---|
| PENDING-A mission definition editor | §1.4, §1.6, §2.2, §6.1 | **Resolved**: Traceability → mission-need card → Edit (scene 1.6); the wizard takes the real values. |
| PENDING-C full export/import | §8 | **Resolved**: project file v2 (chapter 8); round trip checked by a test. |
| UI-GAP station antenna diameter expects a dish | §2.1 | **A.1 kept.** The station element offers a dish diameter only. The link cases stored with the study (scene 4.4) carry the Yagi gain (13–15 dBic), and the licensing earth-station briefs take the gain from the link case, so no number is lost; the diameter field holds the equivalent aperture and the description says so. A gain field on ground elements is a small change, not needed for any scene. |
| UI-GAP objective requirement codes | §2.5 | **Resolved**: the row editor has a **Code** field (scene 2.6). |
| UI-GAP `objective_id` | §2.6 | **Resolved**: the **Objectives** column and the row editor (scene 2.6); the bulk import sets them. |
| UI-GAP options partial | §3.6 | **Resolved**: the option switcher's **branch** creates an option (scene 3.6). |
| UI-GAP custom SWIR filter not in the KB | §4.1 | **Resolved**: **Equipment Catalog → Custom component** with its TRL (scene 4.1). |
| UI-GAP custom TRL | §4.1 | **Resolved**: **TRL (1-9)** in the Properties of a custom element. |
| UI-GAP API-only regulatory forms | §5.10 | **Resolved**: the Licensing tab and its eight documents (scene 5.10). |
| (new) evidence per criterion and the trade's conditions not shown | scene 6.9 | **Resolved in v2**: the absolute-scale matrix shows each criterion's **Evidence** line and the **Conditions of the trade**. |
| (new) requirement edits of an approved change not shown | scene 6.5 | **Resolved in v2**: the change-control card lists **Requirements updated** after approval; ECP-02 carries its three edits. |
| **A.2 kept**: the logbook is per person | chapter 7 | The project file carries the exporting person's own logbook entries only. A team recording with several browsers exports one person's logbook; download each seat's Markdown if the others are needed. This is by design (the logbook is a personal record). |

## Appendix B — Tool findings of v1 (TF) and where they stand

| TF | v1 finding | v2 |
|---|---|---|
| TF-1 | contact windows at latitude 78° for every station | the trades and contact predictions take the study's station coordinates (78° is only the fallback with no station); the [TOOL-CHECK] in 2.2 stays |
| TF-2 | debris without the sail | the design state carries `deorbit.drag_area_m2` = 2.1 m²; the debris assessment (6.4) models it |
| TF-3 | PRR-EC-05 on the sum of on-powers | PRR-EC-05 reads the roll-up against the margin ladder; the orbit average is the Modes energy balance ([TOOL-CHECK] in 4.11) |
| TF-4 | constant 2000 bit/s HK and summed station minutes | the data budget uses the SIDs and the union of passes (N1, scene 4.12) |
| TF-5 | spectrum bands list | not needed by the script: the Licensing tab's frequency assignments (401 / 450 MHz) feed the ISED and ITU documents |
