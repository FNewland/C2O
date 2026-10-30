# R1 — Design tools for C2O: landscape, gap analysis and a phased direction

**For:** Franz Newland (C2O / SpaceCDF)
**Date:** 30 October 2026
**Question:** Which concurrent/MBSE and detailed-design tools should C2O's design side (SpaceCDF, `design/`) learn from, integrate with or adopt, given its purpose: students in 2–3 week intensives and capstones, bilingual EN/FR, browser-based, low cost, open. The design side also has to fit the long-term design → develop → test → fly vision.

**Method.** Read-only survey of the C2O working tree at `/home/claude/c2o` (HEAD `558b202`). I read `design/README.md`, `design/docs/_review/CAPELLA_ASSESSMENT.md`, `SCDF-160-VERIFICATION.md`, `SCDF-170-VERIFICATION.md` and `designs/SCDF-160-arcadia-spine.md`, and walked the packages, routers, services, exporters, KB and frontend. Web research was done on 30 Oct 2026. Package versions and dates come from the live PyPI JSON API; everything else is cited in §8.

**Evidence caveat.** `ARCHITECTURE_REVIEW.md` and `SPINE_SPEC.md` (May 2026) are **not in the repository**. Both verification reports say the same thing ("SPINE_SPEC.md is not in the repository"). I used them only through the summaries in `CAPELLA_ASSESSMENT.md` and the project notes. Before acting on anything here that touches the spine, copy them from Drive into `design/docs/_review/`.

---

## 0. The answer in one page

1. **Nothing on the market replaces SpaceCDF for your use case.** No other tool is all four of: browser-based, open, bilingual, and teachable to a Phase-0 team in days. The tools ESA Academy and TU Delft actually teach with are COMET plus calculation sheets. COMET's web client is AGPL .NET/Blazor and needs a private DevExpress feed to build. Valispace has become Altium's "Requirements Portal" at US$999 per user per year. Virtual Satellite (no stable release since Nov 2024) and IDM-CIC (CNES, not open) are Java or Windows desktop tools. Capella is desktop Java. **Keep SpaceCDF as the front door, and treat every other tool as an exchange partner or as a deeper tool students graduate to.**

2. **The spine is in place, and it was the right choice.** The Arcadia-shaped model with 10-25 parameters, equations as model elements, Options, analysis closures, and the Capella / 10-25 / ReqIF / SysML v2 adapters (SCDF-160/170, 301 tests) puts SpaceCDF ahead of every open CDF tool on traceability, closures and teaching UX. What it lacks is **verified interoperability**: the COMET push returns 501, the SysML v2 output is not checked against the pilot implementation, ReqIF loses thresholds, and the SMO export is hand-written against an unversioned schema (DI-20, still open).

3. **The biggest gap for the lifecycle vision is the handoff, not the CDF.** The "detailed design" outputs today are LLM prompts (`spacecdf-ai/capabilities/wiring.py` → "KiCad schematic"; `cad.py` → CadQuery; `fsw.py`), a cFS-style header generator, and BOM/harness services. None of them produces a project that a real tool opens, checks and builds. **Build deterministic generators** that turn the spine into:
   - a KiCad 10 project, checked with `kicad-cli` ERC/DRC;
   - a CadQuery/build123d STEP envelope;
   - an F′ v4 FPP topology.

   Each one is checked in CI by the real tool.

4. **"Fly this design" should be a versioned contract, not an exporter.** Generate the SMO mission package from `smo_common` Pydantic schemas. Source it from the element model, so modelled hardware wins over agent estimates (fixes N6). Schedule every mode (fixes N2). Then bring ops results (SoC, data backlog, contacts) back as verification evidence. This is the C2O-specific advantage no other tool has. Make it work end to end first.

5. **What to adopt, integrate with and build:**

| | Choices |
|---|---|
| **Adopt** (as libraries) | Orekit (via `orekit-jpype`), CadQuery/build123d, `kicad-cli` + KiCad file generation, F′ tooling, StrictDoc, `reqif`, `capellambse` (already adopted) |
| **Integrate** (round-trip with) | COMET CE (ECSS-E-TM-10-25), Capella, SysON/SysML v2, KiCad, FreeCAD 1.1, GMAT (script export), OpenProject (optional) |
| **Build** | the Fly-this-design contract, per-subsystem "work packages", the document register / library, and a bilingual design-package viewer in the browser |
| **Learn from, but don't use** | Virtual Satellite (equations, discipline rights), IDM-CIC (CubeSat-first UX, 3D viewer), Valispace (live values in documents), ESA Academy's 5-day CE schedule |
| **Avoid** | KubOS (no push since 2023), poliastro/hapsira (archived / no release since Dec 2023), embedding any AGPL COMET component, building on Capella or Cameo |

---

## 1. What SpaceCDF actually is today (repo survey)

These facts come from the working tree, not the README.

| Area | What exists | Where |
|---|---|---|
| Stack | FastAPI + SQLAlchemy (SQLite/Postgres) + React 19 / Zustand / Vite 8 / `@xyflow/react`; i18next. About 40k backend lines (per `sim/docs/web_2026-10/WEB_CURRENT_STATE.md`) | `design/packages/*`, `design/frontend` |
| Agents | Tier 1: orbit, power, mass, thermal, link, data, AOCS, propulsion, structure. Tier 2: systems, cost, risk, TRL, radiation, reliability, debris, sustainability, community, volume, conflicts. The `tier3` folder is empty. | `spacecdf-agents/src/spacecdf_agents/tier1, tier2` |
| Physics | In-house analytic models: orbit (SSO inclination, Hohmann, contact time), power, thermal, AOCS, link budget, radiation, structures, propulsion, beyond-LEO, constellation, heritage mass. Uses only `numpy`, `scipy` and `sgp4`. | `spacecdf-common/.../physics/` |
| Spine (SCDF-160) | 9 tables (functions, ports, allocations, functional exchanges, realisations, exchange items, requirement relations, parameter definitions, element parameters); `simpleeval` equation engine with `Ref:`/`Calc:`; Options | `spacecdf-server/.../services/equations.py`, `options.py` |
| Closures (SCDF-170) | Mission simulation (`conops_executor`), ground segment, physics (mass properties → inertia → torques → wheel sizing/pointing; thermal network), FMECA, V&V (verification items, RTM, VCD) with stale hashing and conflicts | `services/*_closure.py`, `routers/analyses_*.py` |
| Exchange adapters | Capella (`capellambse` 0.8, declarative export and import, vendored 7.0 template); ECSS-E-TM-10-25 C.3 zip + C.2 client; ReqIF (`reqif`); SysML v2 textual (Jinja). The legacy "10-25-like" MBSE JSON is still present. | `spacecdf-agents/.../exporters/{capella,ecss_10_25,reqif,sysmlv2,mbse}` |
| Optimiser | `scipy` differential evolution plus an in-house NSGA-II | `services/optimizer.py` |
| Documents | ECSS documents (MRD, TS, IRD, SEMP, ConOps, VP, VCD, test plan, tailoring). **Three overlapping docx builders remain** (DI-32), and `routers/exports.py` is about 2.5k lines (DI-18). Template search is language-aware, but "the Word/Excel artefacts ignore `lang` for now". | `exporters/docs/generator.py:392-408`, `services/docx_generator.py` |
| SMO export | About 20 YAML files (mission, orbit, eps/aocs/tcs/ttc/obdh/payload/fdir, telemetry, S12/S19, events, TC catalogue, planning). It is built from `DesignState` + `MissionRequirements`, **not** from the element/spine model, and has **no import of `smo_common` schemas** (DI-20 still open). | `exporters/smo/exporter.py`, `routers/exports.py:642` |
| "Detailed design" today | (a) `fsw/generator.py` writes cFS-style C headers, APIDs, mode and FDIR tables. (b) `harness_designer.py` covers bus specs, connectors and harness mass. (c) `bom_generator.py` produces JSON/CSV/docx. (d) **LLM-only** capabilities: `wiring.py` (prompt `kicad_schematic.txt`), `cad.py` (`cad_cadquery.txt`), `fsw.py`, `structural.py`, `thermal.py`. Nothing checks the LLM outputs. | as named |
| KB | 24 component YAML categories (space and ground) with 150+ COTS items | `spacecdf-kb/.../data/components/` |
| Bilingual | `tools.i18n status`: 1561 expected / 1685 translated FR keys, 0 missing; course books and OER in sync (2498 sections OK) | `design/frontend/src/i18n/locales/fr*.json` |
| Tests | 392 `def test` functions (301 suites green at SCDF-170); `tsc -b` has a ceiling of 105 pre-existing errors | `design/tests` |
| Deployment | Single process, single tenant; AI is off in Docker (WEB_CURRENT_STATE §5) | — |

Open defects from the reviews that matter for the handoffs:
- **N2:** user modes other than nominal/safe/downlink, such as Imaging, are never scheduled in the simulation.
- **N6:** the agent's link rate and data volume override the modelled radio and imager.
- **N7:** thermal joint conductances are too pessimistic.
- **N2 (SCDF-160):** ReqIF drops thresholds.
- **DI-20:** the SMO schema contract is unversioned.

---

## 2. Landscape survey

The verdict key used in every table: **Adopt** = use as a dependency. **Integrate** = exchange data with. **Learn** = copy ideas. **Avoid**.

### 2.1 Concurrent design (CDF) tools

#### ESA CDF practice: ECSS-E-TM-10-25, OCDT → COMET

- **What it is.** ESA's CDF data model is ECSS-E-TM-10-25A (2010). Annex A, the data model, is member-state restricted. Annex C covers REST (C.2) and a JSON zip exchange (C.3). ESA replaced OCDT with **COMET** (Starion Group, formerly RHEA) in 2022 (CAPELLA_ASSESSMENT §5.1).
- **Licence and cost.** The COMET Community Edition is open source with mixed licences:
  - COMET-WEB CE web application: **AGPL-3.0**;
  - `COMET.Web.Common` libraries: Apache-2.0;
  - SDKs: LGPL.

  Building the web app needs a private **DevExpress** NuGet feed (GitHub README).
- **Web or desktop.** COMET-IME is a Windows desktop client with an Excel add-in. COMET-WEB CE is a Blazor/.NET web app, and a public demo runs at comet-web.cdp4.org.
- **API and interop.** It implements 10-25 Annex C natively. ESA and Starion say COMET is moving toward SysML v2.
- **Maturity 2025–26.** Active: about 719 commits on the development branch. No GitHub releases are tagged for the web CE.
- **Education.** This is **the** reference tool:
  - The ESA Academy Concurrent Engineering Challenge runs a 5-day study in 3–4 university CEFs plus ESA's Training & Learning Facility, with teams of 2–3 per discipline, using "COMET along with related calculation sheets".
  - TU Delft's Collaborative Design Lab teaches COMET in its Collaborative Space System Design Project, Microsat Engineering, Design Synthesis Exercise and Space Minor.
- **UX strengths.** Rigorous model: parameter ownership per domain, options, iterations, the "published / unpublished" value discipline, Excel familiarity.
- **UX weaknesses.** A heavy enterprise UI, no physics, and the numbers live in calculation sheets.
- **Verdict: Integrate, do not embed.** Make SpaceCDF a real 10-25 peer: test the C.3 export and C.2 push against the COMET WebServices CE Docker image. Learn the published/unpublished value workflow. Never link AGPL code.

#### Valispace → Altium "Requirements Portal"

- **What changed.** Altium acquired Valispace, and the product page now reads "Valispace is now Requirements Portal". It is part of Altium Develop/Agile on Altium 365.
- **Cost and access.** US$999 per user per year, minimum 3 users. Only a 30-day evaluation is free, and no academic tier is listed. Cloud deployment, with on-prem for Enterprise.
- **UX strengths worth copying.** Live "valis" (values) embedded in requirements and documents that update as the model changes. A clean web UI. Formulas in the browser.
- **Verdict: Learn, avoid as a dependency.** It is commercial and has pivoted to requirements and Altium's ecosystem.

#### Virtual Satellite (DLR)

- **Licence and platform.** EPL-2.0, Eclipse RCP desktop, with a headless REST server and OpenAPI.
- **Activity.** Last stable release **4.18.0, 14 Nov 2024**. Development and integration snapshots continue (Feb and Jun 2026), but there have been no stable 2025–26 releases.
- **Why it matters to C2O.** It is the closest design analogue to SpaceCDF: product tree, QUDV units, discipline rights, and **equations as model elements** (`Ref:`/`Calc:`), which SpaceCDF already copied in SCDF-162.
- **Verdict: Learn** (discipline rights and equation editor UX). Don't integrate: there is no exchange format worth targeting beyond 10-25.

#### IDM-CIC (CNES)

- **What it is.** CNES's CubeSat-oriented CE tool (Windows), with IDM-View for 3D. ISAE's Nanostar suite lists it as the recommended tool for "Structure, Power and Mass Budget" and restricts IDM-View to Nanostar members.
- **Access.** Not open source. Access is through CNES or partner programmes. I could not confirm a public licence.
- **UX strengths worth copying.** It is CubeSat-first, and its 3D configuration view is integrated with mass properties. A spacecraft that students can *see* is a big motivator in short intensives.
- **Verdict: Learn.** Build a light 3D view: the placement data already exist (`position_json`, mass properties).

#### Other open, academic CE tools

- **Nanospace** (CSUT / ISAE-SUPAERO, 2020). A web tool (Angular, Spring Boot, Neo4j) under **AGPL-3.0**, with link and power budgets, ADCS, Jsatorb and Stela hooks. It is the nearest open web CDF, but activity looks low and it is AGPL. **Learn.**
- **CEDESK** (Skoltech). Apache-2.0 desktop tool; last release 1.44 in Oct 2019. Dormant. **Learn** from its tradespace and DSM views only.

#### SMAD-style spreadsheets

- This is the de facto academic practice. ESA Academy's "calculation sheets" sit beside COMET, and the New SMAD supplies worked spreadsheets.
- **Strengths.** Every formula is visible, students can edit everything, there is zero install, and they work offline.
- **Weaknesses.** No concurrency, no traceability, and version chaos.
- **Lesson for SpaceCDF.** The equations-as-elements work and the editable parametric data (`GET /api/lifecycle/parametric-data`) answer most of this. Add **xlsx export with live formulas** of each agent's equations, so a student can audit a number in a spreadsheet. **Build** (small).

### 2.2 MBSE tools

#### Capella + capellambse

Details are in `CAPELLA_ASSESSMENT.md`; this survey confirms them.
- **Licence and platform.** EPL-2.0 Java desktop. Latest release 7.1.0 (Jul 2026, per the assessment). Team for Capella is free through the Obeo Academic Program.
- **capellambse.** Apache-2.0 / OFL-1.1, **0.8.1 released 20 Jan 2026** (PyPI). SpaceCDF already pins it at `>=0.8,<0.9`.
- **Bilingual.** The Capella UI is effectively English-only.
- **Verdict: Integrate** (done for the export and import paths). Add a CI job that reopens exports in Capella's Docker image. Keep Capella as the "go deeper" tool for capstones, not for intensives.

#### SysML v2

- **Standard.** OMG adopted SysML v2 in June 2025.
- **Pilot implementation.** The 2026-08 release (12 Sep 2026) contains **Beta 2 of KerML 1.1 / SysML 2.1 / Systems Modeling API 1.1**. Language and API implementations moved from LGPL to **EPL**.
- **Eclipse SysON** (Obeo). A web SysML v2 modeller built on Sirius Web (EPL-2.0), with monthly-ish releases; **2026.3** focused on stability, textual import/export (states, transitions, allocations) and validation rules. ESA's Ground Segment Engineering Framework uses a SysML v2 metamodel on SysON (CAPELLA_ASSESSMENT §5.3).
- **CATIA Magic / Cameo SysML v2 Community Edition** (Dassault). **Free**, capped at **500 major elements**, desktop (MSOSA plus a plugin), with two-way text/diagram sync. The full Cameo is commercial, with academic licences through Dassault's programmes.
- **Syside** (Sensmetry). SysML v2 tooling, 0.11.0 (Sep 2026), proprietary licence (`LicenseRef-Proprietary` on PyPI).
- **Verdict.**
  - SysON: **Integrate** as the browser-based MBSE view for capstones. It is web, EPL, and its French community is through Obeo.
  - SysML v2 textual: **Adopt** as SpaceCDF's long-term neutral export, and validate it against the pilot implementation in CI.
  - Cameo CE: mention it to students as a free desktop option; don't depend on it.

#### Ansys ModelCenter / STK

- **Ownership.** Synopsys completed its acquisition of Ansys in July 2025.
- **STK.** The academic programme gives an STK Enterprise licence with 5, 25 or 50 concurrent "tasks", "priced for academic budgets". No free tier is documented on the current EAP page.
- **ModelCenter.** A commercial desktop integration framework (it is Capella's route for numerical analysis).
- **Strengths.** Industry-standard visualisation and coverage, and a large teaching ecosystem (STK labs in OER courses).
- **Verdict: Avoid as a dependency.** Optionally export a CZML or STK scenario for schools that already hold licences. For browser visualisation, use open CesiumJS with CZML.

#### Jupyter-based MDO (OpenMDAO)

- **OpenMDAO** (NASA Glenn). Apache-2.0, **3.45.2 released 27 Oct 2026**, very active. The CADRE CubeSat MDO problem (Hwang, Gray, Martins) is the canonical open spacecraft example.
- **Strengths.** Analytic derivatives, solvers and recorders; excellent for graduate teaching (SYS5186).
- **Verdict: Integrate later.** Expose SpaceCDF's agents as an OpenMDAO `Group` through a thin wrapper, so graduate students can run gradient-based MDO in Jupyter on the same model. Keep the in-house NSGA-II for the browser.

### 2.3 Mission analysis

| Tool | Licence / cost | Form | API / interop | 2025–26 activity | Education | Verdict |
|---|---|---|---|---|---|---|
| **GMAT** (NASA GSFC) | NASA open source (Apache-2.0), free | Desktop GUI + script; C++ API with Python access | GMAT script; R2025a "API interface... support for commands", JSON estimator output | **R2025a (May 2025)**: multi-body harmonic gravity, optimiser monitoring, K-band | Widely taught; recommended in ISAE's Nanostar suite | **Integrate**: export a `.script` per study for cross-check labs |
| **Orekit** (CS GROUP) | Apache-2.0 | Java library; Python via `orekit-jpype` (needs a JVM) | Rich (propagators, events, OD, CCSDS OEM/OPM/TDM) | Orekit 13.1 (Aug 2025); **orekit-jpype 13.1.9.0 (4 Oct 2026)** | Common in European MSc courses; listed by Nanostar | **Adopt** as the server-side "verification-grade" analysis worker |
| **Basilisk** (CU Boulder AVS) | ISC | C/C++ core, Python; Vizard visualiser | Python scripting; BSK-RL | **bsk 2.12.1 (25 Oct 2026)**, very active | Strong in GNC teaching | **Integrate on the sim side** (AOCS dynamics / HIL). Little value in the CDF loop |
| **poliastro → hapsira** | MIT | Python | — | poliastro archived Oct 2023; hapsira 0.18.0 (Dec 2023), no releases since | Was popular | **Avoid** |
| Tudat / tudatpy (TU Delft) | BSD | Python/C++ (conda) | — | Active | TU Delft teaching | Learn; optional |
| `sgp4`, `skyfield` | MIT | Python | TLE/SGP4 | `sgp4` 2.27, `skyfield` 1.55 | — | Already used (`sgp4`); keep |

**Why Orekit over Basilisk or GMAT for the design loop.** SpaceCDF needs fast, scriptable, server-side answers to orbit-design questions: contacts per station, eclipse fractions, lifetime/decay, ΔV. Orekit is a library, not an app. It is Apache-2.0, has CCSDS-standard I/O that the SMO side can also consume, and installs with `pip` plus a JRE in the container. Keep the in-house analytic orbit agent for interactivity (milliseconds). Run Orekit as an **analysis closure**, using the same `AnalysisContext` → `ResultsSink` pattern as SCDF-170, so results arrive with provenance and stale hashing.

### 2.4 Detailed design

#### Electronics: KiCad

- **Licence and cost.** GPL-3.0, free, with a French UI.
- **Releases.** **KiCad 10.0.0 was released on 20 Mar 2026**, with point releases through 10.0.7-rc (Sep 2026). It added Allegro, PADS and gEDA importers, 3D PDF export, and a graphical DRC rule editor.
- **APIs, version by version:**
  - The new **IPC API** arrived in KiCad 9.
  - In KiCad 9 and 10 the IPC API works **only in the PCB editor and only against a running GUI**.
  - **Headless use through `kicad-cli`, plotting and export, and schematic-editor coverage arrive in KiCad 11.**
  - `kicad-python` 0.8.0 (Aug 2026, MIT) wraps the IPC API.
- **Generating projects today** (Oct 2026):
  - write `.kicad_sch` / `.kicad_pcb` S-expressions directly, for example with `kicad-skip` 0.2.5;
  - or generate netlists with SKiDL, or use **atopile** (code-to-PCB, very active);
  - then run `kicad-cli` (KiCad ≥ 8) for ERC, DRC, BOM, Gerbers and STEP.
- **Education.** Ubiquitous, free, and the CubeSat community has open PC/104 templates.
- **Verdict: Adopt `kicad-cli` and the file format. Build a deterministic generator.** Replace the LLM `kicad_schematic.txt` capability. Plan to move to the IPC API when KiCad 11 makes it headless.

#### Mechanical CAD

- **FreeCAD 1.1** (LGPL-2.1+, released 25 Mar 2026). Desktop, French UI, Python scripting, FEM workbench (CalculiX), Assembly workbench.
- **CadQuery 2.8.0** (Jun 2026) and **build123d 0.13.0** (Sep 2026). Both Apache-2.0, pip-installable on OCCT, headless, and export STEP/STL/glTF. **Ideal for server-side generation** of a CubeSat envelope and component placement.
- **Onshape.** Browser CAD; Student and Educator plans are free, with 2,500 API calls per year. It is proprietary, and the free plans store documents publicly or under PTC terms. Good for teams that need collaboration, but not open.
- **Verdict.**
  - **Adopt CadQuery/build123d** for generating STEP from `position_json` and `dimensions_mm`.
  - **Integrate FreeCAD** as the open desktop tool students graduate to.
  - Show the STEP or glTF in the browser with three.js (no new licence burden).

#### OpenRocket

- GPL-3.0; a rocket flight simulator. It is **not relevant to CubeSat design** beyond REXUS/sounding-rocket projects such as µBioBridge-RX. **Ignore for SpaceCDF.**

#### Thermal

- **Industry tools.** ESATAN-TMS (commercial, the ESA standard) and Thermal Desktop (commercial, the US standard).
- **Open and academic options:**
  - **SATMO** (Chipps, Forgette and Cahoy at the Massachusetts Institute of Technology, arXiv Dec 2025). Open-source six-node CubeSat model in MATLAB, within 1.17 °C of Thermal Desktop. No licence is stated.
  - **TU Delft modular Python tool** (Meijering 2024 MSc). Open source, verified against ESATAN-TMS and validated with FUNcube-1 flight data.
  - **Radian.** Browser and cloud thermal software, benchmarked against ESATAN-TMS through ESA BIC; commercial.
- **Verdict.** Keep SpaceCDF's lumped network and fix N7 (joint conductances).
  - **Learn from or adopt** the TU Delft tool's material and contact database and its validation case.
  - Offer an ESATAN-friendly node/conductor export for capstone teams with licences.
  - Don't build a radiative ray-tracer.

#### Structural FEA

- **Open options.** CalculiX (GPL, used by FreeCAD FEM), Code_Aster (GPL, EDF, with **French-native documentation**, a bilingual asset), Elmer (GPL/LGPL).
- **Verdict.** In SpaceCDF, stay analytic: first natural frequency against the launcher requirement, quasi-static loads, and margins of safety. Hand off to FreeCAD FEM / CalculiX through the generated STEP. Note Code_Aster for French-language capstones.

### 2.5 Flight software

| | **F′ (F Prime)** — NASA JPL | **cFS** — NASA GSFC | **KubOS** |
|---|---|---|---|
| Licence | Apache-2.0 | Apache-2.0 (open-source edition) | Apache-2.0 |
| Status 2025–26 | **v4.0.0 (7 Aug 2025)**: CCSDS uplink/downlink, reusable subtopologies (C&DH), component interfaces, faster build, VS Code visualisation. `fprime-tools` **4.4.0 (30 Sep 2026)**, `fprime-gds` 4.4.1 | NASA announced (Apr 2025) a major update with a government-only edition first and open source "soon after". Public cadence is slow (Draco 2023 era) | Last push **25 Jul 2023**; dormant |
| Modelling | **FPP**, a textual architecture language (components, ports, topologies, commands, telemetry, events, parameters, state machines). It is easy to *generate*. | C apps plus table files; no modelling language | Rust/Python services |
| Ground | Browser-based GDS; JSON dictionaries | Needs COSMOS/OpenC3, OpenSatKit, etc. | — |
| Education | Strong: tutorials, LED blinker, many university CubeSats; runs on a Raspberry Pi or STM32 class | OpenSatKit (cFS + 42 sim) for training | — |
| Fit to C2O | Generate FPP from functions, ports, exchanges, modes and the SMO TC/TM catalogue; build in a CI container | The existing `fsw/generator.py` writes cFS-*style* headers | — |

**Verdict:**
- **Adopt F′ as the flight-software generation target.** Its FPP language maps almost one to one onto the Arcadia spine: function → component, port → port, exchange → connection, mode → state machine. v4 speaks CCSDS, and the GDS is browser-based.
- **Keep cFS as "learn about"** in the course: it is the other NASA standard.
- **Avoid KubOS.**

**Important tension.** The SMO MCS speaks **ECSS PUS-C**; F′ does not. The handoff needs either:
- an F′ "PUS-C adapter" component set (S1/S3/S5/S8/S17/S20 first), or
- MCS import of F′ JSON dictionaries.

Of the two, the PUS-C adapter keeps C2O's ECSS identity and is the better teaching story. It is a **Build** item for "Later". ESA's open TASTE toolchain (with N7 Space's Capella→TASTE bridge) is the European alternative to watch, but it is heavier for students.

### 2.6 Requirements and verification

| Tool | Licence / activity | Form | Interop | Verdict |
|---|---|---|---|---|
| **ReqIF** (OMG) + `reqif` (Python) | Standard; `reqif` 0.1.0 Apache-2.0 (Aug 2026) | — | DOORS, Polarion, Capella | **Adopt** (done). Fix the threshold round-trip (N2) with ReqIF attribute definitions |
| **StrictDoc** | Apache-2.0, **0.30.4 (22 Oct 2026)**, very active; presented at ESA's Software Product Assurance Conference (ESTEC, Sep 2025) with ECSS-E-ST-40C templates | Python, text `.sdoc`, built-in web UI | ReqIF, HTML/PDF, traceability to source | **Integrate**: export requirements, VCD and RTM to `.sdoc` so the lifecycle document library is plain text in Git. Good fit for the "develop/test" stages, where requirements meet code |
| **Doorstop** | LGPL-3.0, 3.2 (Jul 2026) | YAML-per-item in Git | — | Learn; StrictDoc is the stronger choice |
| **OpenProject** CE | GPL-3.0, free, self-hosted, **French UI**, HAL+JSON REST API | Web | Work packages, Gantt, BCF | **Integrate optionally** for capstone project management (risk, actions, schedule); not core |

### 2.7 How student CDFs actually run

- **ESA Academy CE Challenge / Workshop.** 5 days; teams of 2–3 per discipline (structures, configuration, power, thermal, AOCS, propulsion, trajectory, comms/data, payload, cost). Day 1 tool training, Day 2 requirements and architecture with the first iteration, Days 3–4 iterations with product tree and budgets, Day 5 consolidation and presentations. Tools: COMET plus calculation sheets.
- **TU Delft CDL.** COMET with Python scripting and Excel; Scrum training; used across 4+ courses.
- **Strathclyde CCDS** (Wilson & Vasile, SECESA 2022). Educational and industrial studies, plus the STRATHcube CubeSat. The paper reports "successes and failures" of running an academic CDF.
- **EPFL CDF.** An integrated design model for nano/microsats used in university projects (2016).
- **Uni.lu ISM.** Students design satellites and vehicles in the CDF.
- **CNES Nanolab Academy (ex-JANUS) / Nanostar.** IDM-CIC plus GMAT/Orekit/Stela, with access by membership.

**Lessons for C2O:**
1. Tool training eats Day 1 of a 5-day intensive. SpaceCDF's guided stepper and templates are a real advantage; protect them.
2. Every serious programme pairs the CDF with **visible calculation sheets**.
3. The output that matters is the **study report and product tree**, not the model.
4. Nobody else closes the loop to *operations*. C2O's design-then-fly story is unique.

---

## 3. SpaceCDF against the landscape

### Where SpaceCDF is ahead

1. **Browser-native, bilingual, open (MIT), zero install.** No CDF tool surveyed has all four. COMET-WEB comes closest but is AGPL, .NET, and needs a DevExpress build.
2. **Physics inside the model.** It has 20 agents, analysis closures (mission simulation, ground contacts and margins, mass properties → torques → wheel sizing, thermal network, FMECA, V&V auto-closure) with provenance and stale detection. COMET, Valispace and Virtual Satellite all leave physics to spreadsheets or external tools.
3. **Teaching scaffolding.** Templates, a phase stepper, gate reviews with "Go fix", conflict explanations with fix text (e.g. "raise battery capacity to 5.5 Wh"), and validation against real missions.
4. **One model, many standard views.** Arcadia shape plus 10-25 parameters plus Capella / ReqIF / SysML v2 / 10-25 adapters is a broader exchange surface than any open CDF.
5. **A real ops simulator downstream.** The SMO suite (PUS-C MCS, planner, RF, XTCE and SMDL configs) has no equivalent in any CDF ecosystem.

### Where SpaceCDF is behind

1. **Interoperability is claimed but not verified against the counterpart tools.**
   - The COMET push returns 501.
   - The 10-25 export has never been loaded into COMET.
   - SysML v2 output is not parsed by the pilot implementation or SysON.
   - Capella exports are not reopened in Capella in CI (the assessment's own recommendation).
   - ReqIF drops thresholds.
2. **Rigour of the parameter discipline.** COMET has per-domain ownership plus published/unpublished values. SpaceCDF has positions, but DI-31 means `can_edit` fails closed except for `systems_engineer`, and WebSocket `parameter_edit` doesn't trigger equation recompute (SCDF-160 verification §4).
3. **Mission-analysis fidelity.** The orbit work is analytic plus SGP4; there are no high-fidelity contacts, lifetime or eclipse calculations. GMAT and Orekit are standard.
4. **Visualisation.** There is no 3D configuration view (IDM-View, Capella diagrams, STK, Onshape all have one), and diagrams are xyflow only. Server-side ELK diagrams (SCDF-168) are not built.
5. **Engineering-quality debt.** 105 `tsc` errors; a 2.5k-line export router (DI-18); three docx builders (DI-32); single-tenant.

### What is missing for the design → develop → test → fly vision

| Lifecycle step | Needed | Today | Gap |
|---|---|---|---|
| Preliminary → detailed handoff | A per-subsystem **work package**: allocated requirements, ICD rows, budget allocations with margins, selected parts, environment specs, verification items | Data exist in the spine; no packaging | **Build** the work-package generator + document register |
| Electronics | KiCad project (schematic with real symbols, board outline, nets from ICD), ERC/DRC, BOM with MPNs | LLM prompt + harness service + BOM | **Build** a deterministic generator; add KiCad symbol/footprint/MPN refs to the KB |
| Mechanical | STEP envelope, component placement, mass-property cross-check | `position_json`, mass properties, LLM CadQuery prompt | **Build** a CadQuery/build123d generator |
| FSW | Buildable F′ deployment from the model; dictionaries shared with the MCS | cFS-style headers; LLM FSW prompt | **Build** an FPP generator plus a PUS-C bridge |
| Build | Release package (Gerbers, BOM, STEP, FSW tag), with hashes | none | **Build** later |
| Simulate | The sim represents *this* design and its equipment | SMO exporter from `DesignState`; schema unversioned; Imaging mode unscheduled; agent beats modelled hardware | **Fix** the contract first (Now) |
| HIL | FSW on a board ↔ sim models ↔ MCS | sim has `smo-link`, `smo-gateway` | Later, mostly sim-side |
| Test | Environmental test plans (ECSS-E-ST-10-03C), test results closing VIs | VP/VCD/test plan generation; V&V auto-closure by analysis only | Add **test evidence ingestion** + document library |
| Ops | Mission package → MCS / planner, results back as evidence | one-way export | Close the loop |

---

## 4. Recommended direction

### Principles (they hold across all phases)

1. **SpaceCDF owns the spine; other tools are adapters or exits.** Never put a desktop tool, or an AGPL or commercial service, in the critical path of an intensive.
2. **Every adapter is verified by the counterpart tool in CI.** Use Docker images: COMET WebServices CE, Capella, the SysML v2 pilot, `kicad-cli`, `fprime-tools`, and CadQuery/OCCT. An adapter that has not round-tripped is a claim, not a feature.
3. **Generate deterministically; use AI to explain and review.** Replace LLM-generated KiCad, CadQuery and FSW with template generators driven by the model. Keep the AI capabilities as tutors ("why is this net on I²C?") and reviewers, not authors.
4. **Bilingual by construction.** Generated artefacts carry EN/FR labels and descriptions with English identifiers, matching the SMO rule. Prefer target tools with French UIs (KiCad, FreeCAD, OpenProject, StrictDoc's HTML is language-neutral).
5. **Two tiers of depth.** The *intensive* tier stays inside SpaceCDF and the SMO. The *capstone* tier opens the generated KiCad, FreeCAD, F′, Capella or SysON projects in the real tools.

### Phase 1 — Now (Nov 2026 → Jan 2027, about 3 months)

**Goal:** make the existing seams honest, and ship "Fly this design" v1.

| # | Item | Type | Effort |
|---|---|---|---|
| N1 | **"Fly this design" contract v1** (see §5.1). Generate the SMO package by instantiating `smo_common.config.schemas` models, not hand-built dicts (closes DI-20). Source it from the element/spine model, with KB equipment performance outranking agent estimates (fixes N6). Schedule every user mode, Imaging included, and warn when a mode is unscheduled (fixes N2). Add a manifest with schema version, study, option and git hash. Add a CI test that boots the simulator on the exported package. | Build | 4–5 wk |
| N2 | **COMET round-trip test.** Run the COMET WebServices CE container in CI, push the C.3 zip through the C.2 client (replacing the 501), and read it back. Document "open your SpaceCDF study in COMET" for students who go on to the ESA Academy. | Integrate | 3 wk |
| N3 | **Adapter CI.** Reopen Capella exports in the Capella Docker image. Parse SysML v2 output with the pilot implementation (2026-08). Fix the ReqIF threshold round-trip. | Integrate | 2 wk |
| N4 | **Document register v0.** One `documents` table: DRD id, title EN/FR, lifecycle phase, version, status, source study/option, generated-by, hash. Collapse the three docx builders into one (DI-32), with `lang` actually honoured. This is the backbone of the lifecycle document library. | Build | 3 wk |
| N5 | **Formula transparency.** xlsx export of each agent's equations as live formulas (the SMAD-sheet lesson); the UI shows `Ref:`/`Calc:` next to every number, in EN/FR. | Build | 1–2 wk |
| N6 | **Hygiene that unblocks the above.** Bring `tsc` errors down from 105, split `routers/exports.py` (DI-18), fix DI-31 position authorisation (for COMET-style parameter ownership). | Build | ongoing |

### Phase 2 — Next (Feb → Oct 2027, 6–12 months)

**Goal:** per-subsystem detailed-design work packages that real tools open, plus verification-grade analysis.

| # | Item | Type | Notes |
|---|---|---|---|
| X1 | **Work-package generator.** Per subsystem: allocated requirements, ICD extract, budget allocations with margins, parts list, environment spec, VIs, and *generated starter projects* (below). It is a zip plus a register entry, bilingual cover sheet. | Build | The core of the "develop" stage |
| X2 | **KiCad generator.** From `ComponentExchange`/`ExchangeItem` and `harness_designer` bus specs, produce nets. Add `kicad_symbol`, `kicad_footprint` and MPN fields to the KB YAML. Generate `.kicad_sch` + `.kicad_pcb` (PC/104 outline, connector placement) by writing S-expressions (`kicad-skip`) or a SKiDL netlist. Run `kicad-cli` ERC/DRC/BOM in CI. Start with an EPS interface board and an OBC carrier. Move to the IPC API when KiCad 11 makes it headless. | Build + Adopt `kicad-cli` | Retire `kicad_schematic.txt` as an author |
| X3 | **Mechanical generator.** CadQuery/build123d produces the CubeSat structure envelope and component boxes from `dimensions_mm` and `position_json`, exported to STEP and glTF. Includes a footprint-aware packer (fixes N3). An in-browser three.js viewer gives students the IDM-View "see your spacecraft" moment. Check mass properties against `mass_properties.py`. | Build + Adopt | Opens in FreeCAD 1.1 or Onshape |
| X4 | **F′ generator.** Functions become components; ports become ports; functional exchanges become connections; mode elements become FPP state machines; the SMO TC/TM/event catalogue becomes commands, telemetry and events. The output is an F′ v4 project built in CI with `fprime-tools`. Replaces `fsw/generator.py`'s cFS-style headers (keep it as a reference). | Build + Adopt | Ties design to the sim's catalogue |
| X5 | **Orekit analysis closure.** Contacts, eclipse, lifetime/decay and ΔV through `orekit-jpype`, in a worker using the AnalysisContext → ResultsSink pattern. Outputs CCSDS OEM, which the SMO can ingest. Plus a **GMAT script export** for cross-check labs. | Adopt + Integrate | Keep analytic agents for interactivity |
| X6 | **SysON integration.** Import SpaceCDF's SysML v2 text into SysON (web) as the capstone MBSE canvas. Capella round-trip remains for teams on Team for Capella (free academic). | Integrate | |
| X7 | **StrictDoc export** of requirements, VCD and RTM, so the document library has a plain-text, Git-diffable trace to code and tests. | Integrate | |
| X8 | **Thermal and structural depth.** Per-class joint conductances (fixes N7), material and contact database (learn from the TU Delft tool), analytic first-mode and quasi-static checks; STEP to FreeCAD FEM/CalculiX as the exit. | Build | |

### Phase 3 — Later (2028+)

- **HIL and the digital thread.** A stable `c2o_id` on every element, exchange, requirement and document, carried through KiCad (field), STEP (metadata), F′ (component annotation), SMO config and test reports.
- **F′ PUS-C bridge.** S1/S3/S5/S8/S17/S20, so a generated F′ build on a dev board (Raspberry Pi or STM32 class) can be commanded by the SMO MCS through `smo-link`. The sim swaps modelled equipment for real hardware unit by unit.
- **COTS/designed equipment models.** Generate sim equipment models from KB entries plus work-package parameters, so the simulator "represents the real mission".
- **Environmental test library.** ECSS-E-ST-10-03C test plans per model philosophy, test procedure templates, and **test-result ingestion** that closes VIs with test evidence (today only analysis closes them).
- **Release ("build kit") package.** Gerbers, BOM with MPNs and suppliers, STEP, F′ tagged build, document set; all hashed and registered.
- **Optional:** a shared COMET server for multi-university CE challenges; an OpenMDAO wrapper of the agents for graduate MDO in Jupyter; CZML export for CesiumJS / STK.

### Adopt / integrate / build — summary

| Adopt (dependency) | Integrate (round-trip / exit) | Build (C2O-specific) |
|---|---|---|
| `capellambse` (have), `reqif` (have), `orekit-jpype`, CadQuery or build123d, `kicad-cli` (+ `kicad-skip`/SKiDL), `fprime-tools`, StrictDoc, SysML v2 pilot (CI validation only) | COMET CE (10-25), Capella + Team for Capella academic, SysON, KiCad 10/11, FreeCAD 1.1, GMAT, OpenProject (optional), Basilisk (sim side) | Fly-this-design contract, document register/library, work-package generator, KiCad/STEP/F′ generators, 3D viewer, PUS-C bridge, test-evidence ingestion, digital-thread IDs |

---

## 5. The two handoffs in detail

### 5.1 "Fly this design" (CDF → simulator)

**Today.** `POST /api/exports/smo/{study}` → `SMOExporter.export(DesignState, MissionRequirements)` → about 20 dicts. The schema is re-implemented by hand; the input is agent state, not the model; there is no version and no round-trip.

**Target contract (v1).**

1. **Schema source of truth.** SpaceCDF depends on a small, published `smo-common` schema package (or a vendored JSON Schema generated from it, with a version). The exporter builds Pydantic objects and calls `.model_dump()`, so validation failures are export failures.
2. **Inputs.**
   - The *element model*: equipment performance from KB-backed elements (battery Wh, panel W, radio rate and power, imager rate), modes from mode elements with `activate` rows, stations from ground elements, orbit from `AnalysisContext`.
   - The selected Option.
   - Agent values only as fallback, flagged in the manifest.
3. **Package.** A zip with `manifest.yaml` (contract version, study/option ids, git SHA, generated-at, language, list of fallbacks), `mission.yaml`, `orbit.yaml` (later plus a CCSDS OEM from Orekit), `subsystems/*.yaml`, telemetry and commands (identifiers in English, labels and descriptions EN/FR), and a scenario file that schedules every mode.
4. **Load.** The SMO accepts the package as a mission/scenario: an instructor upload, or the c2o.live portal's "Fly this design" button.
5. **Return path.** After a pass or a training run, the SMO posts a results bundle back to SpaceCDF: min SoC and DoD, data generated and returned, contacts, FDIR events, pointing. It lands through `ResultsSink` as `analysis:ops-run` evidence, which can pass or fail verification items. **This loop is C2O's unique teaching story:** "your requirement SR-PWR-1 failed in orbit 2 during Imaging".
6. **CI.** Export each template study and boot the simulator headless for N orbits; assert no validation errors and energy balance within tolerance of the SpaceCDF closure.

### 5.2 CDF → detailed design (KiCad / mechanical / F′)

```
Spine (elements, exchanges, exchange items, requirements, params, modes, VIs)
   │
   ├─ Work package per subsystem (docs: allocated reqs, ICD extract, budgets+margins,
   │     parts list, environment spec, VIs — EN/FR — registered in document library)
   │
   ├─ electronics/  KiCad 10 project
   │     nets  ← ComponentExchange + ExchangeItem(kind=data|power) + harness bus specs
   │     parts ← KB entries (+ kicad_symbol, kicad_footprint, MPN)
   │     board ← PC/104 outline template; connectors placed; unrouted ratsnest
   │     CI    ← kicad-cli sch erc / pcb drc / bom export
   │
   ├─ mechanical/   CadQuery/build123d → STEP + glTF
   │     envelope from form factor; boxes from dimensions_mm @ position_json
   │     check     ← mass/CoM/inertia vs mass_properties.py
   │
   └─ fsw/          F′ v4 project (FPP)
         components ← Functions allocated to OBC (one per subsystem app)
         ports/conns← Ports + FunctionalExchanges
         cmds/tlm/evr ← SMO TC/TM/event catalogue (same ids as the sim)
         modes      ← Mode elements → FPP state machine
         CI         ← fprime-util generate/build; dictionary diffed against SMO catalogue
```

Design rules:
- **Generated starters are deliberately incomplete.** No autorouting and no application logic. Students do the detailed design; the generator removes the blank-page problem and guarantees traceability.
- **Every generated file carries the `c2o_id` of its source elements.** A later import can then report drift: "board has a net not in the ICD".
- **The AI capabilities become reviewers.** For example: "check this schematic against the ICD and power budget". They are no longer the authors.

---

## 6. Risks and watch items

- **KiCad API churn.** IPC is GUI-bound until KiCad 11. File-format generation is stable within a major version; pin KiCad 10 in CI.
- **F′ and PUS-C mismatch.** Without the bridge, generated FSW can't talk to the SMO MCS. Scope the bridge early, even if it is built later.
- **COMET AGPL.** Test against the container only; never vendor or link.
- **cFS open-source cadence** is uncertain (the government edition comes first). One more reason for F′.
- **Orekit needs a JVM** in the backend container: +~200 MB. Acceptable for a server worker; keep it optional.
- **SysML v2 is still Beta 2 of 2.1.** Validate against a pinned pilot release.
- **Scope creep in intensives.** Keep generated projects behind the capstone tier; intensives stop at the work package plus "Fly this design".

---

## 7. Facts from the repository worth recording

- `ARCHITECTURE_REVIEW.md` and `SPINE_SPEC.md` are absent from `C2O/design/docs/_review/` (only CAPELLA_ASSESSMENT, SCDF-160/170 verification and `designs/SCDF-160-arcadia-spine.md` are present).
- DI-20 is still open: `exporters/smo/exporter.py` has no `smo_common` import and is fed by `DesignState`.
- The KiCad, CAD and FSW "generation" capabilities are LLM prompts (`spacecdf-ai/prompts/kicad_schematic.txt`, `cad_cadquery.txt`, `fsw_generator.txt`).
- SpaceCDF FR UI catalogue: 0 missing keys (`tools.i18n status`, 30 Oct 2026).

---

## 8. Sources

**Repository (local, HEAD 558b202):** `design/README.md`; `design/docs/_review/CAPELLA_ASSESSMENT.md`, `SCDF-160-VERIFICATION.md`, `SCDF-170-VERIFICATION.md`, `designs/SCDF-160-arcadia-spine.md`; `sim/docs/review_2026-07/REVIEW_2026-07.md` (DI-18, DI-20, DI-31, DI-32); `sim/docs/web_2026-10/WEB_CURRENT_STATE.md`; package sources as cited in §1.

**Package metadata (PyPI JSON API, queried 30 Oct 2026):** openmdao 3.45.2 (2026-10-27, Apache-2.0); orekit-jpype 13.1.9.0 (2026-10-04, Apache); bsk 2.12.1 (2026-10-25, ISC); capellambse 0.8.1 (2026-01-20, Apache-2.0/OFL-1.1); reqif 0.1.0 (2026-08-11, Apache-2.0); doorstop 3.2 (2026-07-10, LGPLv3); kicad-python 0.8.0 (2026-08-30, MIT); kicad-skip 0.2.5; fprime-tools 4.4.0 (2026-09-30, Apache); fprime-gds 4.4.1; syside 0.11.0 (2026-09-29, proprietary); cadquery 2.8.0 (2026-06-21); build123d 0.13.0 (2026-09-21, Apache-2.0); strictdoc 0.30.4 (2026-10-22, Apache-2.0); hapsira 0.18.0; sgp4 2.27; skyfield 1.55.

**Web:**
- COMET WEB Community Edition (licence, Blazor, DevExpress): https://github.com/STARIONGROUP/COMET-WEB-Community-Edition
- COMET WebServices CE wiki: https://github.com/STARIONGROUP/COMET-WebServices-Community-Edition/wiki
- ESA CDF, Open Concurrent Design: https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CDF/Open_Concurrent_Design_In_the_CDF
- ESA Academy Concurrent Engineering Challenge 2025 (format, COMET + calculation sheets): https://www.esa.int/Education/ESA_Academy/Concurrent_Engineering_Challenge_2025_Applications_Open_to_Universities
- ESA Academy, CubeSat preliminary design in four days: https://esa.int/Education/ESA_Academy/Students_prepare_preliminary_design_of_a_CubeSat_in_four_days_using_Concurrent_Engineering
- TU Delft Collaborative Design Lab (COMET in courses): https://tudelft.nl/lr/cdl
- Strathclyde CCDS, past, present and future (SECESA 2022): https://strathprints.strath.ac.uk/82824
- EPFL, Operation of a CDF for university projects: https://infoscience.epfl.ch/record/220263
- Uni.lu CDF: https://www.uni.lu/snt-en/facilities/cdf-lu/
- Valispace → Requirements Portal pricing: https://www.valispace.com/pricing/
- Valispace acquired by Altium: https://spaceinsider.tech/?p=22083
- Virtual Satellite releases: https://github.com/virtualsatellite/VirtualSatellite4-Core/releases
- DLR Virtual Satellite: https://www.dlr.de/de/sc/forschung-transfer/softwareloesungen/virtual-satellite
- Nanostar software list (IDM-CIC, IDM-View, GMAT, Orekit…): https://sourceforge.isae.fr/projects/nanostar-softwares/wiki/Wiki/12/annotate
- Nanospace (CSUT/ISAE, AGPL, OSCW 2020): https://events.libre.space/event/4/contributions/120/attachments/92/118/room2-sun-1435-Nanospace-an-open-source-tool-to-help-concurrent-engineering-teaming-in-cubesat-preliminary-design.pdf
- IDM-CIC and IDM-View for CubeSat design: https://fr.slideshare.net/PedroLopes101/rochalopespaper
- CNES Nanolab Academy (JANUS): https://janus.cnes.fr/en/janus
- CEDESK (Skoltech): https://cedesk.github.io
- SysML v2 release 2026-08 (Beta 2 KerML 1.1/SysML 2.1/API 1.1; EPL): https://github.com/Systems-Modeling/SysML-v2-Release/releases/tag/2026-08
- SysON 2026.3: https://blog.obeosoft.com/syson-2026-3
- CATIA Magic/Cameo SysML v2 Community Edition (free, 500 elements): https://docs.nomagic.com/SYSML2P/2026x/catia-magic-cameo-sysml-v2-community-edition-286557495.html and https://discover.3ds.com/free-catia-sysmlv2-community-edition
- Synopsys completes Ansys acquisition: https://www.goodwinlaw.com/en/news-and-events/news/2025/07/announcements-technology-ma-synopsys-completes-acquisition-of-ansys
- AGI/Ansys Educational Alliance (STK academic): https://www.agi.com/about/EAP
- OpenMDAO: https://openmdao.org/
- CADRE CubeSat MDO: https://github.com/JustinSGray/CADRE
- GMAT R2025a: https://gmat.atlassian.net/wiki/spaces/GW/blog/2025/05/16/2962227204/Announcing+GMAT+R2025a+Release
- GMAT NASA software catalogue: https://software.nasa.gov/software/GSC-19468-1
- Orekit 13.1: https://orekit.org/news/2025/08/01/orekit-13.1-released.html
- Basilisk: https://hanspeterschaub.info/basilisk/
- BSK-RL: https://avslab.github.io/bsk_rl
- hapsira (poliastro fork, history): https://hapsira.readthedocs.io/en/latest/history.html and https://pypi.org/project/hapsira
- KiCad 10.0.0 release: https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/
- KiCad 10 overview: https://www.cnx-software.com/2026/03/22/kicad-10-release-dark-mode-graphical-drc-rule-editor-new-file-importers-and-more/
- KiCad IPC API for add-on developers (PCB-only in 9/10; headless and schematic in 11): https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
- atopile: https://github.com/atopile/atopile
- FreeCAD 1.1 released: https://blog.freecad.org/2026/03/25/freecad-version-1-1-released/
- Onshape education plans: https://onshape.com/en/education/plans
- SATMO open-source CubeSat thermal tool: https://arxiv.org/abs/2512.07896v1
- TU Delft modular thermal analysis (Meijering 2024): https://repository.tudelft.nl/record/uuid:74339e69-0fdb-4ce9-96d1-a909e729fb96
- Radian cloud thermal benchmark (ESA thermal workshop 2024): https://indico.esa.int/event/520/contributions/9857/
- F′ v4.0.0 released: https://fprime.jpl.nasa.gov/news/2025/08/07/f-prime-v400-released
- F′ release tag: https://github.com/nasa/fprime/releases/tag/v4.0.0
- NASA cFS major update (Apr 2025): https://etd.gsfc.nasa.gov/capabilities/core-flight-system/news/nasa-to-roll-out-major-update-to-core-flight-software
- cFS repository: https://github.com/nasa/cFS
- KubOS activity (last push Jul 2023): https://awesome.ecosyste.ms/projects/github.com%2Fkubos%2Fkubos
- OpenSatKit: https://opensatkit.github.io/docs/OSK-Quick-Start-Guide.pdf
- StrictDoc at ESA Software Product Assurance Conference 2025: https://airdrive.eventsair.com/eventsairwesteuprod/production-atpi-public/deba9e40123b442e9370060a4da1d3a3
- StrictDoc docs: https://strictdoc.readthedocs.io/
- OpenProject Community Edition: https://openproject.org/community-edition
- Capella, capellambse, Team for Capella academic, COMET licences, Virtual Satellite equations, SysML v2 adoption: see the ~300 primary sources cited in `CAPELLA_ASSESSMENT.md` and its companion dossiers.
