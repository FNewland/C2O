# R2: Operations support tools: what C2O should learn from, integrate with or adopt

*Research report for Franz Newland, 2026-10-30. Read-only study of `/home/claude/c2o/sim` plus a web survey. Facts about third-party tools carry a source; anything I could not verify is marked **unverified**. Version and date facts come from the package registries (npm, PyPI, Maven Central) where GitHub was not reachable from this session.*

---

## 0. Executive summary

1. **Keep the SMO MCS core. Do not replace it with Yamcs, COSMOS or SCOS-2000, and do not rebuild the displays on Open MCT.** What sets SMO apart for teaching is the part no product supplies:
   - console positions with authority (`positions.yaml`);
   - procedure cards with GO/NO-GO gates and handover;
   - sim-time-correct archive and logs;
   - failure scenarios with debriefs;
   - a modern UI that is fully EN/FR.

   None of the candidate products has documented French localisation, and the mature ones (Yamcs, COSMOS) would cost months to re-skin and still not hold the teaching layer.
2. **Make SMO interoperable with Yamcs. That is the cheapest, highest-value integration.** I tested it: stock **Yamcs 5.13.7** (released 2026-10-17) **rejects SMO's generated XTCE**. There are three generator defects in `tools/generate_xtce.py` (§5.2). With them patched in a scratch copy, Yamcs loads the whole EOSAT-1 database: 465 parameters, 10 HK containers and 219 commands. Fixing the generator makes the XTCE export truthful. It also opens three things:
   - a "same spacecraft, industry MCS" lab;
   - a route to Open MCT through the `openmct-yamcs` plugin;
   - a Yamcs front end for a real ground station later (SLE, COP-1, SDLS).
3. **Adopt standards and patterns, not products:**
   - map the canonical procedure schema to **ECSS-E-ST-70-32 PLUTO** (preconditions, main body, watchdog, confirmation), with import and export;
   - fix the XTCE export against **XTCE 1.3** (OMG, July 2025);
   - use **CCSDS ODM/CDM** files for flight-dynamics exercises, generated with **Orekit** (Apache-2.0);
   - borrow alarm "shelving" and "expected out-of-limit" handling, and anomaly-report workflows, from Yamcs, Open MCT and the 2025 DLR Columbus UX study.
4. **Voice:** use **LiveKit** (Apache-2.0, very active, bots through LiveKit Agents) as the platform. Keep **openvocs** (DLR, Apache-2.0, open-sourced July 2025) as a one-day spike and as the model for loop and keyset UX. Practice-mode bots that speak on the loops decide it for LiveKit.
5. **Practice mode should mirror real certification ladders:**
   - NASA's sequence is boot camp, knowledge capture, mini sims, integrated sims, then certification (about 18 months to a first certification);
   - ESA runs simulation campaigns in which simulation officers inject "monsters";
   - EUMETSAT runs certification and proficiency training tracked by KPIs.

   Bots play the missing roles and the game director plays the simulation officer. The published evidence for gamified ops training is thin and recent (DLR GSOC board games, SpaceOps 2023 and 2025). That makes C2O's practice mode a research contribution, so instrument it.
6. **Real ground station: SatNOGS first, receive-only, as a data source.** Replay SatNOGS DB frames of a real amateur CubeSat through the GSG before attempting an own station. SatNOGS has had no transmit support so far; TX is on its roadmap. Leaf Space and other GSaaS providers apply only once there is a licensed mission (CUBICS).

---

## 1. What SMO is today (from the code)

| Area | What exists (file evidence) | Notes |
|---|---|---|
| TM/TC MCS | `packages/smo-mcs/src/smo_mcs/server.py` (5,533 lines, 73 HTTP/WS routes), `tm_processor.py` (HK decom, S5 events, S12 monitoring, limit classification), `tc_manager.py`, `tc_lengths.py`, `pus_reports.py` | Single aiohttp process. Global state, so one stack per session (consistent with `web_2026-10/ARCHITECTURE.md` §3) |
| Displays | Modern UI `static/modern/mcs.js` (5,094 lines), `index.html`, `schematics.svg` (functional schematic as navigation); classic UI `static/index.html` (13,230 lines); server-side display models in `displays/` (contact schedule, power budget, FDIR alarms, system overview) | Chart.js for trends. The schematic as navigation (grey nominal, colour for deviation) is a deliberate high-performance HMI idiom |
| Positions | `configs/eosat1/mcs/positions.yaml`: **7** positions (FD, Power & Thermal, Flight Dynamics, TT&C, Payload, FDIR/Systems, Propulsion), each with `allowed_services`, `allowed_func_ids`, `visible_tabs`, `manual_sections` | Authority is **defined but not enforced against identity**: "Nothing is authenticated … the operator's position is whatever the browser claims" (`web_2026-10/ARCHITECTURE.md` §2). README says "six operator positions" (doc drift) |
| Procedures | `procedure_runner.py` (755 lines), step types `command, wait, tlm_check, go_nogo, note, label, branch`, fail-closed on unknown steps, sim-time stamped logs; canonical schema `docs/PROCEDURE_SCHEMA.md`; 64 Markdown ops procedures + `procedure_index.yaml`; on-board S18 OBCPs in `configs/eosat1/obcp/` | Equivalent to a reduced PLUTO, with no preconditions/watchdog/confirmation blocks and no structured "initiate and confirm" activity semantics |
| GO/NO-GO, handover, console log | Routes `/api/go-nogo/*`, `/api/handover`, `/api/console-log`, `/api/gonogo-matrix` | Rare in any open-source MCS. Open MCT's "operator status / poll question" is the nearest analogue |
| Verification | `/api/verification-log` (S1 acceptance/start/progress/completion) | |
| Archive | `tm_archive.py` (966 lines): SQLite, schema v2 in **sim time**, WAL verification, degraded mode; routes for parameters/events/alarms/commands/playback | Well engineered for one host; not a mission archive (no packet-level store, no replay as a TM source, no retrieval API standard) |
| Delayed TM | S15 dump emission in sim, `/api/tm-dump*`, `tools/delayed_tm_viewer.py` (8092) | |
| Planning | `smo-planner` (6,815 lines): contact planner, imaging, budgets, constraint checkers, activity scheduler, S11 upload | Python + sgp4 |
| Flight dynamics | sgp4 propagation in `smo-common`; `tools/orbit_tools.py` (TLE/state vector to TC); propulsion module and burn ops; planner ground track | No OD, no CCSDS ODM/CDM, no manoeuvre optimiser |
| Anomaly management | `fault_graph.py`, FDIR panel/alarm panel, 42 failure modes (`failure_catalog.py`), 25+ scenarios with `ScenarioDebrief.score_pct` (`scenario_engine.py`) | No anomaly-report lifecycle (AR/NCR), no alarm shelving, no "expected OOL" flag |
| RF / link | `smo-rfsim`: PACKET / FRAME / RF modes, CCSDS framing, RS, BPSK/QPSK, channel; ZMQ IQ on 5555; `smo-link` agent + GSG with SLE-style delivery modes | A strong teaching asset; most open-source MCSs stop at packets |
| Interchange | Generated XTCE (`configs/eosat1/xtce/eosat1.xml`, 448 kB) and SMDL; pinned in CI | XTCE **does not load in Yamcs** as generated (§5.2) |
| i18n | `static/shared/i18n.js`, `static/modern/i18n/fr.json` (708 keys), `i18n.yaml` + `tools/i18n` keeping manuals/procedures EN/FR in sync with a glossary and `STYLE_FR.md` | Bilingual is a first-class constraint: identifiers in English, labels and descriptions translated |
| Auth, voice, practice mode | None yet. Designed in `docs/web_2026-10/ARCHITECTURE.md` (IAP + MFA, LiveKit, game director + bots) | |

Licence: SMO is **GPL-3.0** (`sim/LICENSE`). That matters for combining with AGPL (Yamcs, SatNOGS), the COSMOS Builder's Licence, and the ESA Community Licence.

---

## 2. Survey by area

Legend for "University use": **known** means a published university user; **likely** means used in academic CubeSat programmes per secondary sources; **–** means none found.

### 2.1 TM/TC mission control systems

| Tool | Licence / cost | Architecture | PUS / CCSDS | Web UI | API | 2025–26 activity | Universities | UX strengths |
|---|---|---|---|---|---|---|---|---|
| **ESA SCOS-2000** (in MICONYS) | ESA Software Community Licence via CoDev; for ESA Member State academic and commercial entities ([ESOC software](https://esoc.esa.int/services-software); [Telespazio](https://www.telespazio.de/en/capabilities/mission-critical-infrastructure/scos2000)). Canada is an ESA Cooperating State; **eligibility for uOttawa unverified**. The Danish partner (DTU) is eligible as a Member State entity | C++/CORBA-era, MIB (SCOS-2000 database tables) drives everything, AND/GRD/scrolling displays, configured rather than coded | Native PUS (A/B/C via MIB), CCSDS packets/frames | Desktop (Qt/Java); web only via newer layers | Internal APIs | Maintained; **end of life no earlier than 2033** ([SpaceOps 2025 #477](https://publications.spaceops.org/2025/download_by_id.php?id=0477)) | Rare; heavy to install | The canonical ESA operator idiom: alphanumeric displays (ANDs), graphical displays (GRDs), out-of-limit (OOL) lists, command stack, manual stack |
| **ESA EGS-CC** (and ESOC's MCS-CC) | Not yet licensable externally; ESOC "will add [it] once … available for licensing" ([ESOC](https://esoc.esa.int/services-software)) | Common core for MCS and EGSE; common data model (TDM); automation built in; web access from any authorised device | Native | Yes (MCS-R web UI per DLR) ([Hartmann et al., SpaceOps 2025](https://elib.dlr.de/220842/1/SpaceOps2025-Paper-Investigating%20UX-UI%20design%20for%20Columbus%20Operations_FIN1.pdf)) | Yes | First operations 2026 (SWARM pilot), fully operational 2027, Ariel first SVTs 2027 ([SpaceOps 2025 #477](https://publications.spaceops.org/2025/download_by_id.php?id=0477)) | – | Its direction: web, automation-first, one data model from AIT to ops. SMO's mission-model thread already points this way |
| **Yamcs** (Space Applications Services) | **AGPL-3.0** server; API and clients **LGPL**; alternative licensing and customer-only plugins, e.g. SPELL ([yamcs.org/about](https://yamcs.org/about)). Training €2,000 to €12,000 ([yamcs.org/training](https://yamcs.org/training)) | Java server, embedded RocksDB archive, XTCE MDB, processors, links (TCP/UDP/frames), hot replication ([product sheet](https://www.spaceapplications.com/wp-content/uploads/2023/11/Product-Sheet_YAMCS.pdf)) | XTCE MDB; CCSDS SPP, TM/AOS/TC/USLP frames, COP-1, SLE, sync and coding; PUS packet preprocessor per ECSS-E-ST-70-41C (CUC time, CRC) ([PUS preprocessor](https://docs.yamcs.org/yamcs-server-manual/links/packet-preprocessor/pus/)); 5.13.6 added PUS S22, 5.13.7 added PUS embedded TCs in S11/S19 ([changelog](https://docs.yamcs.org/yamcs-relnotes/changelog/)) | Built-in Yamcs Web (Angular): parameters, packets, alarms, command stacks, scripts, timeline, activities, OPI displays | REST + WebSocket, Java and Python clients (`yamcs-client` 2.1.0, 2026-08-06, PyPI) | **Very active**: 5.11 to 5.13.7 in 2025–26 (timeline chaining 5.13.0 May 2026; SDLS AES-GCM 5.12.2; OpenID logout 5.13.7, 2026-10-17) ([changelog](https://docs.yamcs.org/yamcs-relnotes/changelog/)) | **Known**: Hasselt University, ISAE-SUPAERO, Carnegie Mellon ([about](https://yamcs.org/about); [SpaceApps 2025](https://www.spaceapplications.com/news/yamcs-mission-control-software-thats-open-tested-and-trusted)); NASA NOS3 option ([NOS3 docs](https://nos3.readthedocs.io/en/v1_07_02/Ground_Software.html)) | Clean web UI, archive browser, command history with verifiers, activities (command / stack / script) that can be planned on the timeline. Flown on VIPER, Peregrine, ERA, ISS payloads |
| **Yamcs Studio** | EPL-2.0 ([repo](https://github.com/yamcs/yamcs-studio)) | Eclipse RCP desktop display builder (OPI) | via Yamcs | Desktop; OPI files also render in Yamcs Web (`@yamcs/opi` on npm) | – | Release cadence not verified; Yamcs Web now renders OPI and gained more OPI widgets in 5.13.3 ([changelog](https://docs.yamcs.org/yamcs-relnotes/changelog/)) | as Yamcs | Synoptic display editor |
| **OpenC3 COSMOS** (formerly Ball COSMOS) | Core moved from AGPL to the **"COSMOS Builder's License"**, which **"explicitly prohibits offering COSMOS as a hosted or managed service"** ([v7.0.0-rc3 notes](https://newreleases.io/project/github/OpenC3/cosmos/release/v7.0.0-rc3)). Enterprise adds SSO, RBAC, audit, a scheduling engine and 24/7 support, priced by quote ([listing](https://theflyingengineer.com/listing/openc3/)) | Containers: Ruby/Python microservices, Valkey (Redis), QuestDB time series (v7), S3 (versitygw), Vue front end | Generic packet definitions (own text format); CCSDS via protocols; no native PUS service model | Yes: Command Sender, Packet Viewer, Telemetry Viewer screens, Script Runner, Limits Monitor, Calendar (Enterprise), Data Extractor | REST/JSON-RPC; Ruby and Python script APIs (`openc3` 7.5.1 on PyPI, **2026-10-30**) | **Very active** (v7 in 2026) | **Known**: Virginia Tech HERMES testbed ([SmallSat 2025](https://digitalcommons.usu.edu/smallsat/2025/all2025/65)); "programs for … universities" ([listing](https://theflyingengineer.com/listing/openc3/)); NOS3 option | Best-in-class **Script Runner** (step, breakpoint, audit) and plain-text screen DSL. **Licence blocks C2O from hosting it on c2o.live** |
| **NASA Open MCT** | Apache-2.0 (npm) | Vue/JS **framework**; you write telemetry/object providers; no server or TM/TC processing of its own | None. Needs an adapter (Yamcs plugin, AIT plugin, custom) | Yes (that is all it is): plots, time conductor, layouts, condition sets/styles, notebook, timelist, fault management, operator status, imagery | JS plugin API | 4.1/4.2 (2025-02-04), 4.3.0 (2026-08-25), **4.3.1 (2026-08-26)** (npm). The 4.3 line added discrete event timelines, correlation telemetry, derived telemetry prototype and fault-management swimlanes ([releases](https://www.github.com/nasa/openmct/releases)) | Many student projects; **no specific programme verified** | Time conductor (real-time vs fixed historical window) and composable layouts. "Poll question" and operator status are a ready-made GO/NO-GO metaphor. Open MCT is the de facto NASA web display layer |
| **openmct-yamcs** | Licence not stated on the page | Open MCT plugin to Yamcs (parameters, containers, historical, WS) | via Yamcs | Open MCT | – | 1,015 commits; tested against Yamcs QuickStart ([repo](https://github.com/akhenry/openmct-yamcs)) | NOS3 | Instant Open MCT on top of a Yamcs MDB |
| **NASA AIT / AMMOS** | MIT (`ait-core` 3.1.2, **2026-09-22**, PyPI) | Python server with streams/plugins/handlers; YAML cmd/tlm dictionaries; Open MCT plugin ([docs](https://ait-core.readthedocs.io/)) | CCSDS packets; not PUS | Via Open MCT / AIT-GUI | Python | Maintained; NOS3 calls its AIT integration "functional but not maintained" | JPL ISS/CubeSat | Simplest Python reference GDS. A useful code comparison for SMO |
| **Bright Ascension HELIX Ops / Groundkit** | Commercial | Component-based (same lineage as GenerationOne FSDK) | PUS/CCSDS (**details unverified**) | Yes (**unverified**) | – | Announcements Aug 2025 (satnews; page not retrievable) | – | Flight/ground model generated from one component model: the "digital thread" idea in C2O §10 |
| **KubOS Major Tom** | Commercial SaaS; Kubos assets acquired by **Xplore** in April 2022 ([Xplore PR](https://www.xplore.com/press/releases/2022/04.04.2022_Xplore_reaches_agreement_to_acquire_major_tom_cloud-based_mission_operation_software_and_kubos_flight_software.html)) | Cloud ops platform with GSaaS adapters | Agnostic | Yes | REST/GraphQL | Kept as Xplore's ops product ([Xplore](https://www.xplore.com/services/operations-as-a-service/major-tom.html)); KubOS flight SDK effectively frozen | Past free-access offers | Cloud-native multi-mission UX, GSaaS integration |
| **GMV hifly** (+ Autofly, Flyplan, focusSuite) | Commercial | Virtualised/dockerised; LEO to HEO; fleets | Yes | – | – | About 150 satellites; Eutelsat, SES, OneWeb, Arabsat and others; Telesat Lightspeed contract ([GMV](https://www.gmv.com/en/products/space/hifly)) | – | "Manual to lights-out" automation (Autofly) |
| **Leaf Space** | Commercial GSaaS | Leaf Line network + Leaf Key (dedicated) + Leaf Hosting (Nov 2025) ([Leaf Space](https://leaf.space/leaf-space-unveils-leaf-key-and-leaf-hosting-expanding-ground-segment-beyond-leaf-line)) | Delivers frames/data; S, X, Ka | Customer portal | REST API | Active | – | Pass booking through an API: the model for a "real provider" in the GSG |
| **SatNOGS** (Libre Space Foundation) | GPL-3 / AGPL / CERN-OHL ([Wikipedia](https://en.wikipedia.org/wiki/SatNOGS)); `satnogs-client` 2.1.4 AGPLv3, **2026-10-02** (PyPI) | Network (scheduler), DB (transmitters, frames, API), client on station, open hardware | Receives what amateur sats send; decoders (gr-satellites, satnogs-decoders) | Yes | DB API | ~290 online stations, ~5,550 observations/day, ~290 M frames from ~5,116 stations ([State of the Union](https://events.libre.space/event/9/contributions/231/attachments/175/262/SatNOGS_State_of_the_Union.pdf), year not stated) | Widely used by university CubeSat teams | Open data. TX/uplink is on the roadmap, not delivered |
| **"Parsec"** | – | – | – | – | – | – | – | **Could not identify an ops-support tool of this name.** NASA PARSEC is a concept-design suite ([SpaceNews](https://spacenews.com/?p=449159)); Lockheed Martin Parsec is a lunar relay network. If you meant a newer commercial ops console, the closest current products are **Epsilon3** (procedures; free online "Epsilon3 University" courses, [blog](https://www.epsilon3.io/behind-the-console/introducing-university)) and **Quindar**. Please confirm |
| **ESA OPS-SAT "Sim-Ops"** | GPL-3.0, Python + Vue ([ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fnunorc%2Fsim-ops)) | Minimal spacecraft sim + ground-station sim + MCS | Simplified | Yes | – | **Dormant**: last push 2024-07-02, 7 stars | ESA OPS-SAT Space Lab exercises: groups with no experience "operational within a day", voice protocols, time limits ([OPS-SAT training](https://opssat.esa.int/training)) | The closest peer to SMO, and evidence that ESA runs the same pedagogy. SMO is far deeper |

### 2.2 Procedures (preparation and execution)

| Item | Status | Relevance to SMO |
|---|---|---|
| **ECSS-E-ST-70-32C PLUTO** (31 July 2008) ([ECSS](https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/)) | The ECSS procedure language. Structure: **preconditions → main body (initiate-and-confirm activities, waits) → confirmation**, with a **watchdog** body for contingencies | SMO's canonical schema covers the main body only |
| **LibreCube PLUTO → Python** (GSoC 2019 prototype) ([slides](https://events.libre.space/event/3/contributions/49/attachments/45/66/librecube_pluto.pdf)) | Each procedure becomes a class with `preconditions()`, `main()`, `confirmation()`; `wait_until_expression`, `initiate_and_confirm_activity` | Direct template for an SMO PLUTO adapter |
| **pluto-ecss** (MIT, announced 2026-06-09) ([forum](https://community.libre.space/t/pluto-ecss-open-source-implementation-of-ecss-e-st-70-32c-pluto-transpiler/14867)) | Small transpiler; maturity unknown | Spike candidate |
| **EGS-CC Automation Procedures**, PLUTO-derived executable engines ([SESP 2015](https://indico.esa.int/event/93/contributions/3581/attachments/2795/3252/03.SESP-Process_towards_an_Executable_Engine_Compliant_with_the_Interoperable_Test_and_Operation_Procedure_Language_70-32.pdf)) | Industry extended PLUTO (records, arrays, criticality-tagged events, transactional bodies) | Shows PLUTO-as-written is not enough; a "PLUTO-shaped" schema is the realistic target |
| **MOIS** (RHEA; ESA procedure preparation/execution), **ESA MATIS** (automation) | Not on ESOC's public licensable list ([ESOC](https://esoc.esa.int/services-software)); **details unverified** | Learn the vocabulary (flight operations procedures, FOP, stored in a database, "MOIS procedure model") for teaching |
| **SPELL** (SES, Python-based, open source) ([SourceForge](https://sourceforge.net/p/spell-sat/)) | Integrated with Yamcs as a customer plugin ([yamcs.org/about](https://yamcs.org/about)) | Python procedures with a GUI executor: the same design space as SMO's runner |
| **Yamcs stacks, scripts, activities** | Activities = command / stack / script, plannable on the timeline; 5.13.1 renamed "Procedures" to "Automation" ([activities](https://docs.yamcs.org/yamcs-server-manual/activities/); [changelog](https://docs.yamcs.org/yamcs-relnotes/changelog/)) | Same split SMO has (procedure runner vs S11 timeline) |
| **COSMOS Script Runner** | Step / pause / breakpoints / audit log | UX model for the SMO runner |
| **Epsilon3** | Commercial procedure platform; free self-paced courses ([blog](https://www.epsilon3.io/behind-the-console/introducing-university)) | Modern UX for conditional steps, sign-offs and redlines |

### 2.3 Monitoring and control data definition

- **ECSS-E-ST-70-31C** (31 July 2008): monitoring and control data definition, the conceptual model behind SCOS-2000 MIB and EGS-CC's data model ([ECSS](https://ecss.nl/standard/ecss-e-st-70-31c-ground-systems-and-operations-monitoring-and-control-data-definition/); [EGS-CC CDM](https://indico.esa.int/event/93/contributions/3554/attachments/2826/3283/01.2015-03-24_EGS-CC_CDM_Utilization_v5.pdf)).
- **XTCE**: versions 1.0 (2005), 1.1 (2008), 1.2 (Oct 2018) and **1.3 (July 2025)** ([OMG](https://www.omg.org/spec/XTCE)). Yamcs is the reference open implementation. SMO emits XTCE 1.2 (`xmlns="http://www.omg.org/spec/XTCE/20180204"`).
- **ECSS-E-ST-70-41C (PUS-C)**: SMO implements it; Yamcs' preprocessor cites it explicitly.

### 2.4 Planning and scheduling

| Tool | Licence / cost | Architecture | Notes |
|---|---|---|---|
| **ESA EGOS-MPS** | Not yet licensable: "will be made available for licensing" to industry and academia ([ESOC](https://esoc.esa.int/content/powerful-generic-mission-planning-software-europe)) | Inputs (payload requests, manoeuvres, station windows), conflict checks, outputs timed command lists; config-driven | Rosetta, BepiColombo heritage; now multi-mission at ESOC |
| **NASA Aerie, now "PlanDev"** (and SeqDev) | MIT | Java mission-model library, discrete-event simulator, TypeScript DSLs for scheduling goals and constraints, GraphQL API, web UI. Services: merlin, scheduler, sequencing, workspace ([repo](https://www.github.com/NASA-AMMOS/aerie)) | **Renamed in 2026**: "the planning tool is now PlanDev, the sequencing tool is now SeqDev"; packages keep old names for now. About 9,400 commits; active. Heavy (Postgres + Hasura + several services) |
| **STK Scheduler** (Orbit Logic + Ansys/AGI) | Commercial; STK has university licensing via Ansys | Task/resource model, constraints from STK windows, desktop + online ([Orbit Logic](https://orbitlogic.com/stk-scheduler.html)) | Landsat 8/9 heritage |
| **Yamcs Timeline** | AGPL | Items, activities, chaining (5.13.0) | Lightweight; ties plan to execution |
| SMO `smo-planner` | GPL-3 | Python; contacts, imaging, power/data budgets, constraints, S11 upload | Already the right size for teaching |

### 2.5 Flight dynamics

| Tool | Licence | Status 2025–26 | Ops relevance |
|---|---|---|---|
| **Orekit** (CS GROUP) | Apache-2.0 | 13.0 released 2025-04-10 ([news](https://orekit.org/news/2025/04/10/orekit-13.0-released.html)); `orekit-jpype` **13.1.9.0, 2026-10-04** (PyPI) | Flight-grade OD (batch least squares, Kalman), propagators, events, manoeuvres, **CCSDS ODM (OPM/OEM/OMM), CDM, TDM**. The right engine for a Flight Dynamics desk |
| **GMAT** (NASA GSFC) | Apache-2.0 | **R2025a** (May 2025): new OD data types, API commands, cookbook ([announcement](https://gmat.atlassian.net/wiki/spaces/GW/blog/2025/05/16/2962227204/Announcing+GMAT+R2025a+Release)) | Mission design and OD; used operationally by NASA missions; heavy for embedding, good for coursework |
| **ESA GODOT**, NAPEOS | ESA Community Licence ([ESOC](https://esoc.esa.int/services-software)) | Maintained | ESOC's own FD; eligibility caveat as for SCOS |
| GMV focusSuite, Ansys STK/ODTK | Commercial | – | Industry FD stacks |

### 2.6 Anomaly management

There is no standalone open-source "anomaly management" product. The capability is spread across:

- MCS alarm models: Yamcs alarms with acknowledge and shelve, and an explicit pending status since 5.11 ([changelog](https://docs.yamcs.org/yamcs-relnotes/changelog/)); Open MCT fault management with swimlanes ([releases](https://www.github.com/nasa/openmct/releases)); COSMOS Limits Monitor.
- Procedure tools (contingency procedures, watchdog bodies).
- Ticketing (anomaly reports, ARs, and non-conformance reports, NCRs).

The best recent design evidence is the **DLR Columbus UX study**: 13 operator interviews ([Hartmann et al., SpaceOps 2025](https://elib.dlr.de/220842/1/SpaceOps2025-Paper-Investigating%20UX-UI%20design%20for%20Columbus%20Operations_FIN1.pdf)). Its findings:

- **expected** out-of-limits (OOLs) caused by timeline activities generate false alerts;
- audible alerts do not distinguish soft from hard limits;
- there is no clear stale-data indication;
- command success is not always clearly confirmed;
- conditional procedure steps are poorly highlighted;
- missed voice-loop playback is of limited use.

SMO already addresses several of these: staleness gating (`chartStale`), S1 verification, schematic deviation colouring and procedure cards. Expected-OOL handling and alarm shelving are the gaps.

### 2.7 Voice loops

| Option | Licence / cost | Architecture | Loops model | Activity | Fit |
|---|---|---|---|---|---|
| **openvocs** (DLR GSOC) | Apache-2.0, open-sourced July 2025 ([Interoperable Europe](https://interoperable-europe.ec.europa.eu/node/731260)) | Browser client; WebSocket signalling, WebRTC (Opus 48 kHz) + TURN; **server-side mixing per loop and per user**; SIP gateway; multi-site; dual-server failover ([Schiffner et al., SpaceOps 2023](https://publications.spaceops.org/2023/download_by_id.php?id=0204)) | **Native TALK / MONITOR / NONE**, role-based (RBAC), optional LDAP | FrOSCon talk Aug 2025 ([FrOSCon](https://programm.froscon.org/froscon2025/speaker/a9f0197c-1f3d-5262-b8bf-aa7cc8071087/)); repo `github.com/openvocs/openvocs`; current commit cadence and packaging **unverified** (GitHub blocked) | Most authentic; recorder status unclear; no bot SDK |
| **LiveKit** | Apache-2.0; self-host free | Go SFU (Pion), built-in TURN, Egress, **Agents** framework (STT → LLM → TTS, multilingual turn detection) ([Agents 1.0](https://aimresearch.co/?p=14980)) | Build it: one room per session, muted-until-PTT track, talk loop as attribute, selective subscription (design in `WEB_OPTIONS_RESEARCH.md` §A.3) | **Very active**: server v1.13.11 (2026-10-25), Python `livekit` 1.2.0 (2026-10-27, PyPI) | Best for practice-mode bots that speak and listen |
| **Commercial VCS** (Frequentis, used at NASA JSC; others) | Commercial; hardware keysets | NASA JSC is replacing its 2008 MOVE-era VCS with Frequentis VoIP while keeping keysets ([ATC Network, 2023](https://www.atc-network.com/atc-news/frequentis/frequentis-to-upgrade-mission-control-voice-conferencing-at-nasas-johnson-space-center-jsc)) | Full | Active | Out of budget; useful only as the UX reference (keyset panel) |

### 2.8 Simulators and training

| Item | Licence / facts | Lesson for SMO |
|---|---|---|
| **ESA SIMULUS / SIMSAT** | ESA Community Licence ([ESOC](https://esoc.esa.int/services-software)). SIMSAT is the real-time kernel; models follow ECSS-SMP; Terma builds operational simulators with flight-software emulators (TEMU: ERC32, LEON2–4, GR740, ARM) ([Terma](https://www.terma.com/space/ground-segment/satellite-simulators/)) | ESA ops simulators run the **real flight software in an emulator**. SMO's model-based OBC is the teaching-appropriate choice; the HIL "flatsat provider" in C2O §10 is the analogue. SMO already exports SMDL (SMP catalogue), a good bridge |
| **NASA flight-controller training** | Boot camp (ISS command certification), knowledge capture (segmented or spiral), **Mini Sims** (soft skills, four core positions), **Integrated Sims**, then certification at a backroom (MPSR) position before front room (FCR); **about 18 months** to first certification ([Forest & Apyan, NTRS 20160012370](https://ntrs.nasa.gov/api/citations/20160012370/downloads/20160012370.pdf)). "Train like you fly" ([NTRS 20110003658](https://ntrs.nasa.gov/api/citations/20110003658/downloads/20110003658.pdf)) | A progression ladder for practice mode: solo knowledge checks, then single-position sims with bots, then team sims, then an instructor "certification board" |
| **ESA ESOC simulation campaigns** | Sentinel-2C: >40 people, "weeks and weeks", simulation officers "set up a role-playing game … confront the team with monsters": data errors, station loss, sick staff, debris CAM ([phys.org 2024](https://phys.org/news/2024-09-sentinel-2c-rehearsals.pdf)). Sentinel-3A: about 6 months, >25 sims, real MCS with a software replica ([phys.org 2016](https://phys.org/news/2016-02-all-dressed-up-with-somewhere.pdf)). Steele (IAC-07): compare injected vs actual anomalies; include real ground-station ops ([IAF](https://iafastro.directory/iac/archive/browse/IAC-07/D1/5/6926/)) | The game director *is* the simulation officer. Add non-technical injects (station outage, staff sickness, manager pressure) and an injected-vs-real anomaly library |
| **EUMETSAT** | An Operations Training Officer owns certification training for new satellite controllers, proficiency training, a training-results database and training KPIs, and links training to recurring human errors ([EUMETSAT post](https://jobs.ch/de/stellenangebote/detail/60e3ed68-8d26-476a-acdb-bbd037079959)). Serco at ESOC: certification process per role, retraining and recertification ([Serco post](https://serco-1.betterteam.com/simulations-and-training-officer)) | Practice mode needs a **qualification record per person per position** (proficiency currency, recertification), not just badges |
| **Gamification evidence** | DLR GSOC: *Learning Satellite Operations by Play* (EDRS-C), SpaceOps 2023 ([#387](https://publications.spaceops.org/2023/0387)); *Operation Luna* cooperative board game (AOCS, OBDH, THM, EPS, PL, GND, FLD roles; anomaly cards, "Check TM", XP buys procedures), SpaceOps 2025 ([PDF](https://elib.dlr.de/220961/1/Spacecraft_Anomaly_Handlung_made_accessible_by_Jaus.pdf)). Reports high motivation but **no quantitative learning-gain data**; the authors call for a study | Evidence is thin. C2O can contribute the first instrumented, simulator-based study (time to detect, procedure choice, TC errors) |

### 2.9 Ground-station networks and data

- **SatNOGS**: open, receive-only today; TX is listed on the roadmap ([State of the Union](https://events.libre.space/event/9/contributions/231/attachments/175/262/SatNOGS_State_of_the_Union.pdf)). The DB API exposes demodulated frames, and about 43% of DB frames are decoded. This is the cheapest route to **real telemetry** in class.
- **Yamcs jsle**: SLE user and provider, with an SLE↔UDP bridge "intended as a front end for a simulator" (already in `LINK_RESEARCH.md`).
- **Leaf Space**: GSaaS with an API; dedicated or hosted stations (Nov 2025). The **AWS Ground Station / Azure Orbital** class of services is not surveyed here.
- **Own station**: an SDR with the SMO rfsim chain (`--rf`, ZMQ IQ on 5555) is already shaped for this.

### 2.10 Archiving and analysis

| Tool | Store | Analysis path |
|---|---|---|
| Yamcs | RocksDB (packets, parameters, events, commands), parameter archive, replay as a processor; Parameter Retrieval Service (5.11) | Web plots, Python client, Open MCT/Grafana |
| COSMOS 7 | **QuestDB** time series with SQL console (replaced reducers) ([v7 notes](https://newreleases.io/project/github/OpenC3/cosmos/release/v7.0.0-rc3)) | Data Extractor, SQL |
| Open MCT | None (front end only) | Historical providers; time conductor |
| SMO | SQLite in sim time, parameters/events/alarms/commands, playback route | Trends tab (Chart.js), report generator, delayed-TM viewer |

---

## 3. Evaluation of the SMO suite against the field

### 3.1 Strengths (where SMO already beats the open-source field for teaching)

1. **An operations *organisation* is in the data model.** Positions with service and function authority, GO/NO-GO polls and a matrix, handover logs and console log. Yamcs and COSMOS give you a tool; SMO gives you a control room.
2. **Procedures are the course.** There are 64 Markdown procedures, a canonical runnable schema with fail-closed execution, sim-time logs and EN/FR sync with a safety rule (`i18n.yaml`: forbidden French step-jump prose unless a BRANCH is declared). No product has this.
3. **The whole signal chain is real.** PUS-C over CCSDS over a modelled RF channel with framing, RS and BPSK. Most open-source MCS teaching stops at UDP packets.
4. **Time is handled properly.** Sim time is separate from onboard CUC, and the archive is stamped in sim time. Yamcs gets this right too; most student tools do not.
5. **Scenarios and debriefs.** 42 failure modes, 25+ scenarios and `ScenarioDebrief.score_pct`: the seed of practice-mode scoring.
6. **Bilingual by construction.** This is the decisive constraint: no surveyed MCS or display framework documents French localisation (Yamcs Web, COSMOS, Open MCT: none found in the docs reviewed; **not exhaustively verified**).
7. **Contract tests between artefacts** (`tests/test_content/`), the discipline that industry MCS projects formalise as database validation.

### 3.2 Gaps

| Gap | Industry reference | Severity for teaching |
|---|---|---|
| **XTCE export does not load in a real MCS** (§5.2) | Yamcs, XTCE 1.2/1.3 | High: a published interchange file that fails silently undermines the "what you learn transfers" claim |
| No authentication; position authority taken from the browser | Every MCS (Yamcs: parameter/command-level auth; COSMOS Enterprise RBAC) | Already planned (WP-3); a prerequisite for cloud |
| Procedures lack PLUTO's structure: preconditions, watchdog, confirmation, initiate-and-confirm semantics; no procedure version/approval state | ECSS-E-ST-70-32, MOIS, Epsilon3 | Medium-high: ECSS-literate graduates are the course's promise |
| Alarm model: no shelving, no "expected OOL" tied to procedure/timeline, no audible soft/hard distinction, no anomaly-report lifecycle | Yamcs alarms, Open MCT fault management, DLR Columbus study | Medium |
| Flight dynamics: SGP4 only; no OD, no CCSDS ODM/CDM, no manoeuvre planning tool for the FD desk | Orekit, GMAT, GODOT | Medium: the FD position is thin compared with real FDS |
| Archive is per-process SQLite; no packet-level store or replay-as-source; no standard retrieval API | Yamcs, COSMOS 7 | Low for class; matters for practice-mode replay and a real station |
| Command stack / manual stack idiom (SCOS-2000, Yamcs stacks) only partly present (procedure runner + quick commands) | SCOS-2000, Yamcs | Low-medium: worth teaching the stack concept |
| Monolithic `server.py` (5.5k lines) and `mcs.js` (5.1k lines) | – | Maintainability risk for one maintainer |
| Doc drift: README says six positions (config has seven); procedure counts 57 / 64 / 67 across docs | – | Low |

### 3.3 Should anything be replaced? Options compared

Costs are for one maintainer, in working days. Teaching value is judged against the course's aims: transferable ECSS/CCSDS practice, team operations and bilingual delivery.

| Option | What it means | Cost | Migration risk | Teaching value | Verdict |
|---|---|---|---|---|---|
| **A. Keep the SMO MCS, make it Yamcs-interoperable** | Fix the XTCE generator; add a CI gate that runs `yamcsadmin mdb verify`; document a "Yamcs lab" (stock Yamcs + SMO simulator on the same TM/TC sockets) | **2–4 days** (generator fixes + CI Docker job), +2–3 days for the lab guide (EN/FR) | Very low (additive) | **High**: students see the same spacecraft in an industry-grade MCS; the XTCE becomes truthful | **Do now** |
| **B. Yamcs replaces the MCS core; SMO keeps a teaching layer on top** | Yamcs does decom, limits, archive and command verification; SMO's UI, positions, procedures and GO/NO-GO call the Yamcs REST/WS API | **40–70 days**: re-plumb 73 routes, position authority via Yamcs privileges, procedure runner on Yamcs commanding, sim-time vs Yamcs mission time, rebuild archive views, re-test ~4,900 tests | **High**: the time architecture, S15 delayed-TM semantics, custom derived parameters (`derived_params.py`), the go/no-go and console log all need re-homing; AGPL server + Java ops burden on c2o.live | Medium-high (industry core), but **loses** some of what SMO teaches by exposing its internals (students can read the Python decom; they cannot easily read Yamcs) | **Not now.** Revisit only if a real mission (CUBICS) needs flight-grade archive/SLE; even then run Yamcs *beside* SMO (option D) |
| **C. Rebuild MCS displays on Open MCT** | Write an Open MCT telemetry provider over the SMO WebSocket; port panels to Open MCT layouts and condition sets | **25–40 days** for parity, plus FR localisation of a framework with no documented i18n | Medium-high: two UI stacks during transition; the procedure, GO/NO-GO and position UX do not map to Open MCT objects | Medium: the time conductor and layouts are excellent, but SMO's schematic-as-navigation and procedure cards are better for novices | **No rebuild.** Optionally (Next) an *analysis workbench*: a read-only Open MCT instance over Yamcs or the SMO archive for post-pass analysis, English-only, 3–5 days |
| **D. Yamcs alongside as the "real-world front end"** | For real-station or real-data work, Yamcs ingests frames (SLE/UDP), archives and forwards packets to the GSG/SMO MCS | 8–15 days when needed | Low (isolated provider) | High for the real-station phase | **Later**, tied to WP-9 |
| **E. OpenC3 COSMOS** | Replace or alongside | – | **Licence: hosting COSMOS as a service on c2o.live is prohibited**; not PUS-native | Its Script Runner UX is worth copying | **Do not adopt**; copy ideas |
| **F. SCOS-2000 / EGS-CC** | Replace or teach | SCOS: heavy install, licence eligibility unclear for Canada; EGS-CC not licensable | High | High authenticity for ESA careers | **Do not adopt.** Teach the vocabulary (MIB, AND/GRD, OOL, stacks) inside SMO; offer DTU partners a SCOS demo if they already hold a licence |

**Bottom line:** the value of SMO is the teaching layer *and* its tight coupling to a transparent Python spacecraft. Replacing the core buys industry provenance at the cost of transparency, bilingualism and months of one person's time. Interoperability (option A now, option D later) captures most of the provenance for a few days of work.

---

## 4. Recommended phased direction

### Now (next 3 months, alongside WP-0 to WP-3 of the web plan)

1. **XTCE truthfulness + Yamcs CI gate** (3–4 days). Fix the three generator defects (§5.2), move the namespace to XTCE 1.2-valid content (stay on the 1.2 schema until Yamcs advertises 1.3), and add a CI job that runs stock Yamcs `yamcsadmin mdb verify` in Docker.
2. **"Same spacecraft, industry MCS" lab** (2–3 days, EN/FR). Stock Yamcs connected to the simulator's TM/TC sockets. Spike the config: SMO frames TCP with a 2-byte length prefix, so use Yamcs' generic packet input stream with a 2-byte length field and strip it. The PUS-C TM time field is at octet 9 (3-octet secondary header before CUC), not Yamcs' default of 13, so set `pktTimeOffset` and the epoch. **Unverified end-to-end; budget one day to prove it.** Teaching use: students compare decom, limits and verification between SMO and Yamcs.
3. **Voice decision** (2 days, as already planned in WP-V0): a one-day openvocs spike, then **LiveKit as the platform** unless openvocs deploys in a day *and* offers a bot path (SIP gateway). Copy openvocs' TALK/MONITOR/NONE semantics and role-based loop rights into `voice_loops.yaml`, keyed to `positions.yaml`. Loop names stay English identifiers; labels are bilingual.
4. **Auth-backed position authority** (WP-3). This is the first gap every real MCS closes. Enforce `allowed_services`/`allowed_func_ids` server-side against the roster identity.
5. **Alarm hygiene from the Columbus study** (3–5 days):
   - an "expected" flag on alarms, raised by a procedure step or a timeline activity;
   - shelve/unshelve with a reason and expiry, logged to the console log;
   - distinct audible cues for warning and critical;
   - keep the stale-data gate.

### Next (6–12 months)

6. **PLUTO-shaped procedures** (8–12 days). Extend the canonical schema with `preconditions`, `watchdog` (contingency triggers that pre-empt the main body), `confirmation`, and initiate-and-confirm activity semantics. Add **PLUTO text import/export**, following the LibreCube mapping or the `pluto-ecss` transpiler if it proves sound. Add procedure version and approval state (draft → validated → approved), as MOIS/FOP practice does. Keep step-type identifiers in English and display text EN/FR (the existing glossary and safety rules apply).
7. **A Flight Dynamics desk on Orekit** (8–12 days). Use Python `orekit-jpype`, Apache-2.0, which is GPL-3-compatible. It covers:
   - OD from simulated GPS or ranging;
   - manoeuvre planning that hands a ΔV vector to the Propulsion position (already split in `positions.yaml`);
   - **CCSDS OPM/OEM/CDM** products;
   - a CDM-driven collision-avoidance drill built on the existing `debris_impact_hermes3` scenario. This mirrors ESA's Sentinel-2C debris rehearsal.
8. **Practice mode v1 with a certification ladder** (WP-5, 8–10 days, plus 3 for records):
   - levels per position: knowledge check → single-position sim with bots → team sim → instructor sign-off ("certification board");
   - a per-person qualification record with currency and recertification, as at EUMETSAT and ESOC;
   - the game director as simulation officer, including non-technical injects (station outage, staff sickness);
   - scoring from the console log: time to detect, procedure choice, rejected TCs, callout discipline.

   Instrument it for a SpaceOps or CEEA paper: the literature has no quantitative evidence.
9. **Anomaly reports** (4–6 days). An AR object with a lifecycle (open → investigating → workaround → closed), links to alarms, procedures and TC history, and an EN/FR template. This feeds the debrief.
10. **Archive export for analysis** (3–5 days). Per-session Parquet/CSV export of parameters, events and commands (sim-time stamped) to object storage, plus starter Jupyter notebooks. This fits the JupyterHub plan for SpaceCDF. Defer Grafana and Open MCT.
11. **Planner learning from PlanDev/Aerie** (no adoption). Add declarative constraint rules and activity resource effects to `smo-planner` in YAML, and keep the S11 upload. Do not deploy PlanDev: its Postgres, Hasura and Java services are too heavy for one maintainer, and it was renamed mid-2026.
12. **Optional Open MCT analysis workbench** (3–5 days, English-only, read-only), through `openmct-yamcs` once the Yamcs lab exists. Students meet the NASA display idiom without forking the MCS UI.

### Later (12 months +)

13. **Real data, receive-only:**
    - a **SatNOGS DB replay provider** for the GSG: pull frames of a chosen amateur CubeSat with a known decoder and replay them through the rfsim/GSG into a separate "real-sat" mission configuration;
    - then a **SatNOGS-compatible station** run by uOttawa, receive-only. Uplink stays locked by configuration, as already specified.
14. **Yamcs as the real-station front end** (option D). Frames arrive from the station (SDR, SLE via jsle, or a GSaaS such as Leaf Space) into Yamcs for archive and COP-1/SDLS, and packets are forwarded to the GSG so the SMO consoles are unchanged. Gate this on a licensed mission (CUBICS).
15. **Bots that talk** (WP-8, LiveKit Agents). Bilingual speech-to-text and text-to-speech with callout grammars per position. Keep the deterministic core authoritative.
16. **HIL/emulator provider.** Follow the ESA SIMULUS pattern of real flight software on an emulator, through the space-link agent, consistent with the C2O design → fly vision. SMO's SMDL export is the bridge to SMP-based tooling.

### Cross-cutting constraints

- **Cloud and licences:**
  - Hosting AGPL Yamcs or SatNOGS components on c2o.live is fine, because C2O publishes its source (GPL-3).
  - Hosting **COSMOS** is not allowed under the Builder's Licence.
  - ESA Community Licence products (SCOS-2000, SIMULUS, GODOT) must not be redistributed or hosted for non-eligible users. Keep them out of the public platform.
- **Bilingual:** every adopted component sits behind SMO's own UI, or is explicitly scoped as an English-only professional tool (Yamcs lab, Open MCT workbench). That is consistent with "only the modern UIs get French; identifiers stay English".
- **One maintainer:** prefer additive integrations with CI gates over replatforming.

---

## 5. Evidence notes

### 5.1 Version and activity facts (registries, retrieved 2026-10-30)

| Package | Version | Date | Licence |
|---|---|---|---|
| Yamcs server | 5.13.7 | 2026-10-17 ([changelog](https://docs.yamcs.org/yamcs-relnotes/changelog/)); tarball downloaded and run | AGPL-3.0 |
| `yamcs-client` (PyPI) | 2.1.0 | 2026-08-06 | LGPL |
| `openmct` (npm) | 4.3.1 | 2026-08-26 | Apache-2.0 |
| `openc3` (PyPI) | 7.5.1 | 2026-10-30 | OpenC3 Builder's Licence |
| `ait-core` (PyPI) | 3.1.2 | 2026-09-22 | MIT |
| `orekit-jpype` (PyPI) | 13.1.9.0 | 2026-10-04 | Apache-2.0 |
| `livekit` (PyPI) | 1.2.0 | 2026-10-27 | Apache-2.0 |
| `satnogs-client` (PyPI) | 2.1.4 | 2026-10-02 | AGPLv3 |

### 5.2 Yamcs compatibility test of SMO's XTCE (done in scratch; repository not modified)

Method: Yamcs 5.13.7 Linux tarball, instance `eosat1`, MDB `type: xtce` pointing at `configs/eosat1/xtce/eosat1.xml`, `bin/yamcsadmin mdb verify eosat1`. Working files are in `

| # | Yamcs error | Cause in `tools/generate_xtce.py` | Scale |
|---|---|---|---|
| 1 | `Invalid consequence level 'caution'; allowed values: [normal, user1, user2, vital, critical, forbidden]` | L373–374: `level = "critical" if crit == "critical" else "caution"`. `caution` is not an XTCE `ConsequenceLevelType` | 15 commands |
| 2 | `Cannot parse '0.1' to integer` | L253–261 choose `IntegerParameterType` from the *raw* pack format, then L264–267 add a `PolynomialCalibrator`. The engineering value is a float, so alarm and valid ranges are non-integer. XTCE wants `FloatParameterType` with an `IntegerDataEncoding` + calibrator. The same applies to argument types at L354 | 185 parameter types, 7 argument types |
| 3 | `Cannot resolve (circular?) references: … /EOSAT-1/OBDH/eps_spacecraft_phase …` | L317–319: HK container entries use `/EOSAT-1/{subsystem_name}/{xml_name}` with the *container's* subsystem rather than the parameter's owning `SpaceSystem` | 17 entries |

After patching all three in a scratch copy, Yamcs reports **14 subsystems, 465 parameters, 10 sequence containers, 219 commands** loaded. Packet decoding against live SMO TM was **not** tested (framing and time offset as in §4 item 2).

### 5.3 Items I could not verify

- openvocs repository activity, packaging and recorder (GitHub and openvocs.org unreachable).
- Bright Ascension HELIX feature details (article not retrievable).
- MOIS and MATIS current status and licensing.
- Whether Canadian universities qualify for the ESA Community Licence.
- Whether Yamcs Web, COSMOS or Open MCT have any French localisation (none found in the docs reviewed).
- What "Parsec" refers to.
- The SatNOGS "State of the Union" year.

---

## 6. Sources (primary first)

**MCS and displays**
- Yamcs: [release notes](https://docs.yamcs.org/yamcs-relnotes/changelog/) · [about/licence](https://yamcs.org/about) · [PUS preprocessor](https://docs.yamcs.org/yamcs-server-manual/links/packet-preprocessor/pus/) · [activities](https://docs.yamcs.org/yamcs-server-manual/activities/) · [product sheet](https://www.spaceapplications.com/wp-content/uploads/2023/11/Product-Sheet_YAMCS.pdf) · [training](https://yamcs.org/training) · [SpaceApps 2025](https://www.spaceapplications.com/news/yamcs-mission-control-software-thats-open-tested-and-trusted) · [Yamcs Studio](https://github.com/yamcs/yamcs-studio)
- OpenC3 COSMOS: [v7.0.0-rc3 notes](https://newreleases.io/project/github/OpenC3/cosmos/release/v7.0.0-rc3) · [listing](https://theflyingengineer.com/listing/openc3/) · [Virginia Tech HERMES, SmallSat 2025](https://digitalcommons.usu.edu/smallsat/2025/all2025/65)
- Open MCT: [releases](https://www.github.com/nasa/openmct/releases) · [openmct-yamcs](https://github.com/akhenry/openmct-yamcs) · [NASA software catalog](https://software.nasa.gov/software/ARC-15256-1D)
- NASA AIT: [docs](https://ait-core.readthedocs.io/) · NOS3 ground software: [docs](https://nos3.readthedocs.io/en/v1_07_02/Ground_Software.html)
- ESA: [ESOC licensable software](https://esoc.esa.int/services-software) · [EGS-CC at ESOC, SpaceOps 2025 #477](https://publications.spaceops.org/2025/download_by_id.php?id=0477) · [Telespazio SCOS-2000](https://www.telespazio.de/en/capabilities/mission-critical-infrastructure/scos2000) · [EGOS-MPS](https://esoc.esa.int/content/powerful-generic-mission-planning-software-europe)
- Commercial: [GMV hifly](https://www.gmv.com/en/products/space/hifly) · [Xplore acquires Major Tom](https://www.xplore.com/press/releases/2022/04.04.2022_Xplore_reaches_agreement_to_acquire_major_tom_cloud-based_mission_operation_software_and_kubos_flight_software.html) · [Xplore Major Tom](https://www.xplore.com/services/operations-as-a-service/major-tom.html) · [Leaf Space Nov 2025](https://leaf.space/leaf-space-unveils-leaf-key-and-leaf-hosting-expanding-ground-segment-beyond-leaf-line) · [Epsilon3 University](https://www.epsilon3.io/behind-the-console/introducing-university) · [NASA PARSEC (design tool)](https://spacenews.com/?p=449159)
- ESA OPS-SAT: [training](https://opssat.esa.int/training) · [Sim-Ops repo metadata](https://awesome.ecosyste.ms/projects/github.com%2Fnunorc%2Fsim-ops)

**Standards and procedures**
- [ECSS-E-ST-70-32C PLUTO](https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/) · [ECSS-E-ST-70-31C](https://ecss.nl/standard/ecss-e-st-70-31c-ground-systems-and-operations-monitoring-and-control-data-definition/) · [OMG XTCE](https://www.omg.org/spec/XTCE)
- [LibreCube PLUTO (LSF 2019)](https://events.libre.space/event/3/contributions/49/attachments/45/66/librecube_pluto.pdf) · [pluto-ecss (2026)](https://community.libre.space/t/pluto-ecss-open-source-implementation-of-ecss-e-st-70-32c-pluto-transpiler/14867) · [SESP 2015 PLUTO engine](https://indico.esa.int/event/93/contributions/3581/attachments/2795/3252/03.SESP-Process_towards_an_Executable_Engine_Compliant_with_the_Interoperable_Test_and_Operation_Procedure_Language_70-32.pdf) · [EGS-CC CDM](https://indico.esa.int/event/93/contributions/3554/attachments/2826/3283/01.2015-03-24_EGS-CC_CDM_Utilization_v5.pdf) · [SPELL](https://sourceforge.net/p/spell-sat/)

**Planning and flight dynamics**
- [NASA-AMMOS Aerie/PlanDev repo](https://www.github.com/NASA-AMMOS/aerie) · [STK Scheduler](https://orbitlogic.com/stk-scheduler.html) · [Orekit 13.0](https://orekit.org/news/2025/04/10/orekit-13.0-released.html) · [GMAT R2025a](https://gmat.atlassian.net/wiki/spaces/GW/blog/2025/05/16/2962227204/Announcing+GMAT+R2025a+Release)

**Voice**
- [openvocs, SpaceOps 2023](https://publications.spaceops.org/2023/download_by_id.php?id=0204) · [openvocs open-sourced, Interoperable Europe](https://interoperable-europe.ec.europa.eu/node/731260) · [FrOSCon 2025 talk](https://programm.froscon.org/froscon2025/speaker/a9f0197c-1f3d-5262-b8bf-aa7cc8071087/) · [LiveKit Agents 1.0](https://aimresearch.co/?p=14980) · [Frequentis at NASA JSC](https://www.atc-network.com/atc-news/frequentis/frequentis-to-upgrade-mission-control-voice-conferencing-at-nasas-johnson-space-center-jsc)

**Simulators, training, gamification, UX**
- [Terma operational simulators](https://www.terma.com/space/ground-segment/satellite-simulators/) · [NASA flight-ops training, NTRS 20160012370](https://ntrs.nasa.gov/api/citations/20160012370/downloads/20160012370.pdf) · [Shuttle flight-control training, NTRS 20110003658](https://ntrs.nasa.gov/api/citations/20110003658/downloads/20110003658.pdf) · [Sentinel-2C rehearsals](https://phys.org/news/2024-09-sentinel-2c-rehearsals.pdf) · [Sentinel-3A preparation](https://phys.org/news/2016-02-all-dressed-up-with-somewhere.pdf) · [Steele, IAC-07](https://iafastro.directory/iac/archive/browse/IAC-07/D1/5/6926/) · [EUMETSAT training officer](https://jobs.ch/de/stellenangebote/detail/60e3ed68-8d26-476a-acdb-bbd037079959) · [Serco ESOC sim & training officer](https://serco-1.betterteam.com/simulations-and-training-officer)
- [Jaus & Scharringhausen, SpaceOps 2023 #387](https://publications.spaceops.org/2023/0387) · [Jaus & Lautenschütz, SpaceOps 2025 #234 (PDF)](https://elib.dlr.de/220961/1/Spacecraft_Anomaly_Handlung_made_accessible_by_Jaus.pdf) · [Hartmann et al., Columbus UX, SpaceOps 2025](https://elib.dlr.de/220842/1/SpaceOps2025-Paper-Investigating%20UX-UI%20design%20for%20Columbus%20Operations_FIN1.pdf)

**Ground networks**
- [SatNOGS (Wikipedia)](https://en.wikipedia.org/wiki/SatNOGS) · [SatNOGS State of the Union](https://events.libre.space/event/9/contributions/231/attachments/175/262/SatNOGS_State_of_the_Union.pdf) · [SatNOGS TX question (2019)](https://community.libre.space/t/is-there-support-for-satnogs-to-transmit-and-command/3240)

**Package registries** (versions in §5.1): npm `openmct`; PyPI `yamcs-client`, `openc3`, `ait-core`, `orekit-jpype`, `livekit`, `satnogs-client`; Yamcs 5.13.7 tarball from the GitHub release.

**SMO internal**: `sim/README.md`, `sim/docs/architecture.md`, `sim/configs/eosat1/manual/software_architecture.md` (the "software_architecture" doc lives here, not in `docs/`), `sim/docs/web_2026-10/ARCHITECTURE.md`, `WEB_OPTIONS_RESEARCH.md`, `LINK_RESEARCH.md`, `sim/configs/eosat1/mcs/positions.yaml`, `sim/packages/smo-mcs/src/smo_mcs/*`, `sim/docs/PROCEDURE_SCHEMA.md`, `sim/tools/generate_xtce.py`, `sim/i18n.yaml`.
