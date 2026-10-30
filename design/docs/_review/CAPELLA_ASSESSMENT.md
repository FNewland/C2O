# Eclipse Capella and SpaceCDF — assessment and recommendation

**Date:** 9 September 2026
**Question asked:** Is Eclipse Capella open source, what is its licensing model, and could it rapidly accelerate SpaceCDF?
**Evidence base:** two research dossiers (`research_capella_core.md`, `research_python_integration.md`, ~300 cited primary-source URLs), the SpaceCDF Drive folder, and the May 2026 architecture review (`ARCHITECTURE_REVIEW.md`, `SPINE_SPEC.md`, `BACKLOG.md`).

---

## 1. Short answer

**Yes, Capella is open source — Eclipse Public License 2.0 — and the licence is friendly to what you want to do.** You can read, write, embed, redistribute and sell around it; only files of Capella itself that you modify must be published. There is no copyleft reach into SpaceCDF's own code.

**No, you should not build SpaceCDF *on* Capella.** It is a Java/Eclipse desktop application with no web UI, no REST API, no equation engine, and a collaboration server (Team for Capella) that is Thales-owned and commercial. Three separate lines of evidence say the same thing: the Eclipse project has no web roadmap; the ESA CDF itself does not use Capella (it uses COMET / ECSS-E-TM-10-25); and DLR — who evaluated Capella for their concurrent-engineering facility — built their own tool (Virtual Satellite) instead.

**Yes, Capella can genuinely accelerate SpaceCDF — but as a *metamodel and exchange target*, not as a runtime.** The acceleration comes from three things:

1. **Adopting Arcadia's shape** (Operational → System → Logical → Physical, functions allocated to components, exchanges as first-class objects, modes/states, functional chains) as SpaceCDF's own internal architecture model. This is precisely the "System-V hierarchy" the May review found missing, and it arrives pre-designed and field-proven rather than bespoke.
2. **`capellambse`** — an Apache-2.0, pure-Python library (Deutsche Bahn, not DLR) that reads and writes real `.capella` files with no Java installed. Once SpaceCDF's internal model is Arcadia-shaped, Capella import/export is close to mechanical: ~5 weeks for the exporter.
3. **ECSS-E-TM-10-25** — the ESA CDF exchange standard. SpaceCDF already emits a "10-25-*like*" JSON; making it real 10-25 (Annex C) is 3–5 weeks and makes SpaceCDF a peer of the ESTEC CDF's tooling rather than an island.

The recommended architecture (Section 6) is the one your existing MBSE exporter was already reaching toward — its docstring says the output is meant to "round-trip into Cameo / Capella via a lightweight importer." That importer was never built; this report says how to build the whole bridge properly.

---

## 2. Licensing — the precise picture

| Question | Answer | Source |
|---|---|---|
| Licence of Capella core and all official add-ons | **EPL-2.0** (Requirements VP, Filtering, XHTML docgen, PVMT, Python4Capella, Simulink connector, SysML-v2 bridge all EPL-2.0) | projects.eclipse.org/projects/polarsys.capella; repo `NOTICE.md` |
| Copyleft scope | File-level, weak. Only *modified* EPL files must be released. Linking, subclassing, calling, reading/writing its file format create **no** obligation. | EPL-2.0 §1 ("Modified Works shall not include works that contain only declarations, interfaces… solely to link") |
| Commercial / educational use | Explicitly permitted; §4 "intended to facilitate the commercial use of the Program" | EPL-2.0 §2, §4 |
| GPL compatibility | **Not available** — Capella headers carry no "Secondary Licenses" Exhibit-A notice. Irrelevant unless SpaceCDF becomes GPL (it is MIT). | Repo file headers |
| Patent grant | Yes (§2b), terminates if you sue over the Program | EPL-2.0 §2b, §7 |
| Arcadia *method documentation* | **Not open.** "© 2023 THALES All rights reserved… may not be reproduced." The *metamodel as code* (Ecore) is EPL-2.0. Arcadia is AFNOR standard XP Z67-140. | mbse-capella.org/arcadia-reference.html |
| Team for Capella (multi-user server) | Proprietary; "the property of Thales Global Services"; sold by Obeo; floating licences; quote-only. **Free for students/professors/researchers via the Obeo Academic Program** (Carleton, ETH, NTNU HYPSO, Hawaii are members). | obeosoft.com/en/products/team-for-capella; obeosoft.com/en/academic-program |
| Trademark | "Capella®" is an Eclipse Foundation trademark. Permitted: "SpaceCDF Bridge for Eclipse Capella®". Not permitted: "CapellaCDF", "Capella Web", or `org.polarsys` namespaces. | eclipse.org/legal/logo-guidelines |
| Governance | Eclipse project, state Mature; 13 committers (Thales + Obeo); the "Capella Industry Consortium" working group **has been terminated**. Release cadence ~12–18 months. Latest 7.1.0, July 2026, Java 21, "minor" release. | projects.eclipse.org; eclipse.org/collaborations/working-groups/capellaic/charter |

**Practical reading for SpaceCDF:** reading and writing `.capella` files, adopting the Arcadia concepts, and shipping a Capella bridge carry no licence obligation beyond attribution. Do not reproduce Thales' Arcadia PDFs, diagrams or tables in SpaceCDF documentation or UI — paraphrase the method. Do not put "Capella" in the product name.

---

## 3. What Capella is, and what it is not

**It is** a mature architecture-modelling tool built on Eclipse EMF/Sirius, implementing Arcadia's four perspectives — Operational Analysis, System Analysis, Logical Architecture, Physical Architecture — plus the End-Product Breakdown Structure. Its strengths are exactly SpaceCDF's weaknesses: function trees with allocation to components, functional chains, component exchanges and exchange items (the basis of ICDs), modes and states, sequence scenarios, requirements with ReqIF import and traceability, model validation rules, a "semantic browser", and computed links (leaf-function exchanges roll up automatically to parents). It is used in the space sector by Thales Alenia Space (Galileo G2G with Team for Capella; e.Deorbit), CNES (SVOM), ArianeGroup, INPE, Rivada, PoliMi (e.Inspector Phase A), N7 Space's ESA-funded Capella→TASTE bridge, and student CubeSat teams at Glasgow and Hawaii.

**It is not** a concurrent-design tool. Property values are plain typed scalars — no units, no equations, no propagation, no margins, no options/iterations. Thales calls the Mass/Cost/Performance viewpoints "basic demonstration viewpoints". Numeric analysis is routed to commercial connectors (Ansys ModelCenter). It has no web client (a 2018 Sprotty prototype only; Obeo's web energy has gone to SysON, a SysML v2 tool), no REST API, and no server mode beyond a batch CLI. Concurrent editing needs Team for Capella or a Git-with-discipline workflow; `.aird` layout files are effectively unmergeable.

**Where it sits in the ESA lifecycle** (ESA's own 2021 survey): Phase 0 CDF studies run on COMET/OCDT (ECSS-E-TM-10-25); Capella appears at industry primes and Phase A/B contractors — after the CDF's parametric sizing, when architecture is being formalised. In other words, Capella and SpaceCDF are complementary stages, not competitors.

---

## 4. The Python bridge — `capellambse`

This is the piece that makes Capella actionable from a FastAPI backend.

| Property | Verified value |
|---|---|
| Maintainer / licence | DB InfraGO AG (Deutsche Bahn "Digitale Schiene Deutschland"); **Apache-2.0**. Not DLR. GitHub org renamed `DSD-DBS` → `dbinfrago`. |
| Version / activity | 0.8.1 (Jan 2026); repo pushed Aug 2026; 2,100 commits; long-lived single maintainer; "Production/Stable"; Python ≥3.11 |
| Runtime | **Pure Python** (lxml; optional Rust speed-up). No Java, no Capella installation. |
| Reads | Full Arcadia model (OA/SA/LA/PA, functions, components, exchanges, exchange items, state machines, scenarios), Requirements Viewpoint, PVMT property values, library projects |
| Writes | `.create()` on containment lists; requirements + relations; `obj.pvmt["Domain.Group.Prop"] = value`; **declarative YAML** (`extend/set/sync/delete`, `!promise` wiring of exchanges); `model.save()` with a Git commit+push transaction; Capella-identical XML serialiser so Capella's own diff/merge stays happy |
| Diagrams | Renders existing Capella diagrams and auto-generates context/tree/interface/dataflow/functional-chain views to SVG/PNG (ELK layout, via `capellambse-context-diagrams`). **Cannot persist new diagrams into `.aird`** — "no plan to implement this." |
| Model sources | Local path, `git+https://…`, `git+ssh://`, `http(s)://`, zip, GitLab artifacts |
| ReqIF | Exports ReqIF 1.1/1.2 (for DOORS/Codebeamer). Import into Capella is done by the EPL Requirements VP add-on. |
| Ecosystem | `capella-model-explorer` (Jinja web views), `capella-diff-tools`, `capella-dockerimages`, `capella-polarion`, `capella-collab-manager` (Kubernetes + Guacamole to stream desktop Capella into a browser). `capella-rm-bridge` is **archived**. |
| Gotchas | Pre-1.0 API with breaking changes (pin `>=0.8,<0.9`); no "new model" API — copy the empty Capella 7.0 template project from its test data; some `create()` paths on aggregate lists misplace elements (issue #446) — always reopen exports in Capella in CI; context-diagram layout downloads an elkjs/deno binary at runtime. |

**What this means:** SpaceCDF can *generate a Capella model* from its own database — functions per subsystem, components per unit, exchanges per ICD row, requirements with traceability, PVMT budgets — commit it to a Git repo, and a Capella-using student, prime or reviewer opens it in Capella 7.1 and sees a proper Arcadia model. Reverse direction works too: SpaceCDF can read a Capella model a team built by hand and pull its architecture into the sizing loop.

---

## 5. Three other things the research surfaced that matter as much as Capella

**5.1 ECSS-E-TM-10-25 / COMET — the actual CDF standard.** ESA's CDF replaced OCDT with COMET (Starion Group, ex-RHEA) in 2022; COMET is "fully compliant with ECSS-E-TM-10-25". Annex C.2 is a REST API (GET + transactional POST of `_create/_update/_delete`); Annex C.3 is a zip of JSON arrays with public sample models. Licences are mixed — web services and apps are **AGPL-3.0** (do not embed), SDKs are LGPL, and a new Python SDK exists but needs .NET. The lightweight path is to speak Annex C JSON directly over `httpx`. SpaceCDF's existing `exporters/mbse/generator.py` already mimics the SiteDirectory / ReferenceDataLibrary / EngineeringModel shape; making it real is a 3–5 week job and would let a SpaceCDF session exchange data with an ESTEC-style CDF. Note: ESA and Starion both say COMET is heading toward SysML v2.

**5.2 DLR Virtual Satellite — the closest analogue to SpaceCDF.** EPL-2.0, Eclipse RCP, built for DLR's Concurrent Engineering Facility. Its data model is what SpaceCDF's should look like: product tree of Structural Elements; typed parameter bundles (Categories) with QUDV units; disciplines with rights; and — critically — **equations as first-class model elements** (`Ref: massWithMargin = mass * margin;`) that re-evaluate on every model change, with a distinction between stored (`Ref:`) and intermediate (`Calc:`) results. It has a headless REST server with OpenAPI. Last stable release Nov 2024 (snapshots continue). Not something to embed (Java), but the best available design reference for making SpaceCDF's agent physics *inspectable* rather than hidden in Python — a gap the May review's engineering-depth audit called out.

**5.3 SysML v2 — the medium-term interoperability layer.** Formally adopted by OMG on 30 June 2025 with a standard REST API; the pilot implementation is now EPL-2.0; Thales+Obeo have published an Arcadia→SysML v2 library; ESA's Ground Segment Engineering Framework already uses a SysML v2 metamodel on Eclipse SysON. A SpaceCDF SysML v2 textual exporter (Jinja + `opensysml` validation) is ~1–2 weeks once the internal model is Arcadia-shaped, and future-proofs the tool against ESA's direction.

---

## 6. Recommendation — Architecture C, staged through A

Three integration architectures were assessed. In brief:

| | A — SpaceCDF master, export `.capella` | B — Capella master, SpaceCDF as viewpoint | **C — Arcadia-shaped internal model; Capella/COMET/SysML v2/ReqIF as exchange formats** |
|---|---|---|---|
| What it fixes | Reviewers get a Capella model | Capella users get SpaceCDF numbers | SpaceCDF's own missing System-V hierarchy, functional decomposition, ICDs, traceability |
| What it doesn't | SpaceCDF's internal gaps stay | SpaceCDF loses authority; PVMT can't hold a parametric core; Git-mediated conflicts | Largest schema change |
| Effort | ~5 wk (+3–4 wk minimal function/interface layer it requires anyway) | ~6 wk | ~16–19 wk staged; first milestone (metamodel + Capella export) ≈ 8 wk |
| Verdict | Necessary first milestone | Not recommended | **Recommended** |

**Why C.** A alone exports what SpaceCDF doesn't have — you cannot emit functions and exchanges from a tool that has no function or exchange model. B hands the master model to a tool whose property bag cannot represent equations, units, options or iterations. C uses Capella's *vocabulary* to design the internal model SpaceCDF needs anyway, borrows 10-25 / Virtual Satellite for the parameter and equation layer, and then every exchange format becomes a thin adapter.

**The internal model C proposes** (SQLAlchemy + Pydantic; class names deliberately match `capellambse.metamodel` so the Capella mapping is near 1:1):

- **Architecture layer (from Arcadia):** `Layer ∈ {OA, SA, LA, PA}`; `Function` tree with `Port`s; `FunctionalExchange`; `Component` tree (PA distinguishes node vs behaviour); `ComponentExchange` + `ExchangeItem` (data / power / thermal / mechanical kinds → ICD tables); `Allocation(function → component)`; `Realization(SA → LA → PA)`; `StateMachine/Mode/State`; `FunctionalChain`. Keep OA optional; start at SA/LA.
- **Requirements & traceability (from Capella Requirements VP / ReqIF):** `RequirementModule / Requirement / RequirementType / Attribute` + `Relation(kind, source, target)`, preserving `SPEC-OBJECT` IDs so ReqIF round-trips with DOORS and Capella.
- **Parameters & budgets (from 10-25 and Virtual Satellite):** `ParameterType` + `MeasurementScale/Unit`; `Parameter` owned by a `Domain` (= a SpaceCDF agent/position); `ParameterValueSet` with `manual/computed/reference` and a switch; `Option`; `Iteration`; **equations as model elements** with `Ref:`/`Calc:` semantics so the agents' formulas are visible in the UI.
- **Exchange adapters:** Capella via capellambse declarative YAML; 10-25 Annex C.3 zip + C.2 client; SysML v2 textual notation; ReqIF via the Apache-2.0 `reqif` package. All imports are Apache-2.0 or standards-derived; nothing AGPL enters SpaceCDF.

---

## 7. How this changes the May backlog

The Horizon-2 tickets already planned for the "spine" are the right work — this research changes their *shape*, not their existence. Concretely:

| Backlog item | Change |
|---|---|
| **SCDF-110..116** (requirement hierarchy + ComplianceTracker) | Make the schema ReqIF/Capella-Requirements-VP-compatible (`RequirementModule`, `RequirementType`, attributes, `Relation`) instead of the bespoke `mission/system/subsystem` levels only. Levels become an attribute; traceability becomes typed relations. Cost: +1 week. Benefit: ReqIF round-trip and Capella export for free. |
| **SCDF-001 / SCDF-132** (FunctionTreeView, phase moves) | Don't fix the bespoke FunctionTreeView; replace it with a real `Function` tree + allocation model (Arcadia SA/LA). This is the new **SCDF-160 series** (see below). |
| **InterfaceMatrixView** (N² display only) | Becomes a view over `ComponentExchange` + `ExchangeItem`; gains an ICD editor for free. |
| **SCDF-133** (traceability tree) | Trivial once `Relation` and `Allocation`/`Realization` exist. |
| **SPINE_SPEC §8 KB-aware agents** | Keep; add the 10-25 `Parameter/ParameterValueSet/Domain` layer so agent outputs are owned, switchable (manual/computed/reference) and exportable. |
| **Engineering-depth "expose the equations"** | Adopt Virtual Satellite's pattern: equations as model elements with `Ref:`/`Calc:`; the UI shows the formula next to the number. |
| **Existing `exporters/mbse/generator.py`** | Retire the "10-25-*like*" JSON in favour of real Annex C.3; keep the file as the migration reference. |

**New tickets to add (Horizon 2b, ~16–19 weeks total, staged):**

- **SCDF-160** — Arcadia-shaped architecture metamodel (Function, Component, Exchange, ExchangeItem, Allocation, Realization, Layer). 3 wk. Design doc first.
- **SCDF-161** — Parameter/Unit/ValueSet/Option/Iteration layer per 10-25 Annex A shapes; agents write `ParameterValueSet.computed`. 2 wk.
- **SCDF-162** — Equations as model elements (`Ref:`/`Calc:`); expose in UI. 2 wk.
- **SCDF-163** — Capella exporter via capellambse decl YAML + empty-7.x template + Git transaction; CI reopens export in Capella 7.1 in Docker (`capella-dockerimages`). 3 wk. **First external milestone.**
- **SCDF-164** — Capella importer (architecture + requirements) via capellambse. 2 wk.
- **SCDF-165** — ReqIF import/export via `reqif`. 1 wk.
- **SCDF-166** — ECSS-E-TM-10-25 Annex C.3 exporter + C.2 client; integration test against the COMET web-services Docker image. 3–5 wk.
- **SCDF-167** — SysML v2 textual exporter, validated with `opensysml`. 1–2 wk.
- **SCDF-168** — Server-side SVG generation (ELK) for SAB/LAB/PAB-style views and context diagrams in the React UI. 2 wk.

---

## 8. Specific answer for the capstone context

SpaceCDF is the "Capstone Companion" for a student mission-design programme. Two things follow:

- **Team for Capella is free for you.** The Obeo Academic Program grants free floating licences to students, professors and researchers, renewed annually. Student teams could model architecture in Capella (as Glasgow and Hawaii CubeSat teams do), commit to Git, and SpaceCDF ingests it for concurrent sizing — the Capella-for-architecture, SpaceCDF-for-numbers split matches the ESA lifecycle exactly.
- **Don't force Capella on students for Phase 0.** ESA's own lesson from Galileo G2G and Euclid: "easy to overextend modelling", "intimidation from tool". Keep SpaceCDF's web UI as the front door; make Capella an *export they can open*, and later an *import for teams who want to go deeper*.

---

## 9. Risks and things to keep an eye on

- **capellambse is pre-1.0 and single-company.** Pin the minor version; wrap it behind one adapter module; keep a CI job that reopens every export in real Capella (Docker image available).
- **Capella namespace URIs are versioned** (`…/la/7.0.0`). Exports must match the Capella version your partners run. Keep the template project in the repo and update it deliberately.
- **Diagram layouts do not round-trip.** SpaceCDF can generate diagrams (ELK) but cannot save hand-laid Capella diagrams back; treat `.aird` as Capella-owned.
- **Governance thinning.** The Capella industry consortium is terminated; it is Thales + Obeo. The metamodel is stable and the file format is text; the risk is slow evolution, not disappearance. SysML v2 is the hedge.
- **10-25 Annex A is member-state restricted.** Implement from the public `CDP4Common` C# source, the public Annex-B reference data, and the CC-BY-4.0 sample models; avoid AGPL components.
- **Attribution hygiene.** capellambse/DB InfraGO, Virtual Satellite/DLR, COMET/Starion, Capella/Thales-Obeo-Eclipse. Several public summaries (including this project's earlier assumptions) get these wrong.

---

## 10. Suggested next step

Write the **SCDF-160 design doc** (Arcadia-shaped architecture metamodel + 10-25-shaped parameter model) — 2–3 days — and prototype **SCDF-163** (Capella export of one template mission via capellambse, opened in Capella 7.1) as a 1-week spike. That spike answers the only question the research cannot: how much of SpaceCDF's current state maps cleanly, and how the export looks to a Capella user. Everything else in Section 7 follows from that.

---

*Companion dossiers with full citations: `research_capella_core.md` (licensing, governance, adoption, alternatives) and `research_python_integration.md` (capellambse API, Virtual Satellite, COMET/10-25, SysML v2, ReqIF, worked YAML export, risk register).*
