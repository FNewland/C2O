# Decision Support Gap Analysis

## What the tool should do vs what it actually does

A mission designer walks in with "I need to monitor crop health in
sub-Saharan Africa." The tool should GUIDE them through every decision
with computed alternatives, trade-offs, and consequences. Instead, it
presents forms and runs a calculator.

This document catalogues every place the tool falls silent when it
should be speaking.

---

## 1. ORBIT SELECTION — Zero decision support

**What the designer needs:**
"Given my coverage, revisit, resolution, and cost constraints, which
orbit gives me the best trade?"

- SSO at 400 km: daily revisit at equator, 15m GSD with 15cm aperture,
  but high drag → short lifetime without propulsion
- SSO at 550 km: 3-day revisit, 20m GSD with same aperture,
  10-year natural lifetime, standard rideshare altitude
- SSO at 800 km: 5-day revisit, worse GSD but longer life,
  above ISS debris zone, but 25-year rule issue
- Equatorial LEO: excellent equatorial coverage but no polar data,
  limited launch options
- GEO: continuous coverage of one hemisphere but terrible resolution

**What the tool does:** Presents a dropdown: "Orbit type: LEO / SSO / MEO / GEO."
The designer picks one and types an altitude number. No guidance on WHY.

**What's missing:**
- Coverage calculator: given target latitude band, compute revisit time
  vs altitude vs inclination
- GSD calculator: given aperture budget (driven by mass/cost), compute
  achievable GSD vs altitude
- Orbital lifetime vs altitude chart with debris compliance overlay
- Launch vehicle access: which orbits can you reach from which launchers?
- Cost vs altitude: rideshare pricing varies by orbit
- The TRADE: present these as a multi-criteria decision matrix, not a form

---

## 2. MISSION CLASS — No guidance at all

**What the designer needs:**
"Given my budget, timeline, and performance needs, what class of
spacecraft should I build?"

- Nano (CubeSat 1-10 kg): <5 MEUR, 6-12 month build, limited performance,
  standardised, COTS. Good for: tech demo, IoT, low-res EO, education.
- Micro (10-100 kg): 5-30 MEUR, 12-24 month build, moderate performance.
  Good for: mid-res EO, targeted science, constellation members.
- Small (100-500 kg): 30-100 MEUR, 24-48 month build, high performance.
  Good for: high-res EO, dedicated science, operational service.

**What the tool does:** Dropdown: "Spacecraft class: nano / micro / small."
No rationale for why you'd pick one over another.

**What's missing:**
- Performance envelope per class: achievable GSD, data rate, pointing,
  lifetime, delta-V
- Cost envelope per class with confidence bounds
- Schedule envelope per class
- Risk profile per class (heritage, complexity, single-point failures)
- The question: "Given your objectives, which class can meet them?"
  This should be COMPUTED from the objectives, not hand-selected.

---

## 3. PAYLOAD SELECTION — No performance-to-need mapping

**What the designer needs:**
"I need 10m multispectral imagery. What instruments can do that from
what orbit? What do they weigh, cost, and need in terms of power/data?"

**What the tool does:** Form fields: "Payload mass: ___ kg, Power: ___ W."
The designer must already KNOW their payload.

**What's missing:**
- Instrument sizing from science requirements: "10m GSD at 550 km →
  needs 15cm aperture → ~8 kg for a Ritchey-Chrétien → 25W → 100 Mbps"
- Existing instrument database: "These 5 instruments from cubesatshop.com
  can achieve your GSD from this orbit — here are the trades"
- Payload performance trade: resolution vs swath vs data rate vs mass
- Spectral band selection guidance for specific applications (NDVI for
  crop health needs NIR + Red bands)

---

## 4. COST AND MASS TARGETS — Just input fields, no rationale

**What the designer needs:**
"What's a realistic cost and mass for a mission of this class that
meets these objectives?"

**What the tool does:** Form fields: "Target mass: ___ kg, Target cost: ___ MEUR."
If you type wrong numbers, the design just fails to close.

**What's missing:**
- Parametric estimation FROM the objectives: "A nano-class EO CubeSat
  at 550 km typically costs 3-8 MEUR and weighs 8-14 kg"
- Historical comparison: "Similar missions (EOSAT-1, Dove, NORSAT)
  achieved these specs at these costs"
- The warning: "Your target of 2 MEUR for 1m GSD multispectral is not
  achievable — the instrument alone costs 3 MEUR"

---

## 5. ConOps — Power-centric, not mission-centric

**What the designer needs:**
A ConOps is NOT a power mode table. Per NASA SEH Appendix S, a ConOps
describes:
- Mission scenarios / Design Reference Missions (DRMs)
- System operational modes with transitions and triggers
- User interactions (who requests data? how do they get it?)
- Ground operations concept (how many operators? what shifts? what tools?)
- Data flow from instrument to end user (latency, processing, distribution)
- Launch and deployment sequence
- Commissioning plan (what do you check first? in what order?)
- Contingency operations (what if the star tracker fails?)
- End-of-life disposal concept

**What the tool does:** Four power/pointing profiles (safe/nominal/downlink/eclipse)
auto-generated from payload specs. The ConOps "editor" is really a
power mode editor.

**What's missing:**
- The user story: "A farmer in Kenya checks their phone app for a crop
  health map. This map was generated from data acquired 2 orbits ago,
  downlinked to Svalbard, processed in AWS, and pushed to the app."
  THAT is a ConOps. The tool doesn't capture any of this.
- Mission timeline: "Day 1: deploy from ISS. Day 2: first beacon.
  Day 3-30: commissioning. Day 31: first science image."
- Operator workload: "2 operators, 8am-6pm, monitoring 4 passes/day"
- Contingency: "If attitude lost → enter safe mode → ground diagnoses
  within 2 passes → uplink recovery command"
- Data pipeline: instrument → onboard storage → downlink → ground
  processing → archive → user portal

---

## 6. SESSIONS — No explanation of when or why

**What the designer needs:**
"When should I start a collaborative session? Who should be in the room?
What should we decide in this session?"

**What the tool does:** A "Start Session" button with no context. You pick
positions and join. There's no guidance on what a session IS for.

**What's missing:**
- Session types: "Architecture exploration session (2 hours, all positions)"
  vs "Subsystem sizing session (1 hour, domain engineers)" vs
  "Trade study session (30 min, systems + 2 domains)"
- Session agenda: "This session will address decisions 0.5, 0.6, 0.7
  from the lifecycle framework. Pre-reads: orbital analysis memo."
- Session structure mapped to ESA CDF methodology: "Sessions 1-2:
  mission definition. Sessions 3-5: architecture exploration..."
- The prompt: "Your mission need and objectives are defined. You should
  now start an architecture exploration session to decide orbit, payload,
  and ground segment."

---

## 7. COMPONENT SELECTION — Catalogue, not decision support

**What the designer needs:**
"I need a reaction wheel that provides 0.01 Nms momentum storage,
fits in a 3U CubeSat, interfaces via I2C, costs < 10 kEUR, and has
flight heritage. What are my options?"

**What the tool does:** Shows a catalogue table you can sort by fit/mass/cost.
You click "Select" on one.

**What's missing:**
- Requirement-driven filtering: "Show me only components that MEET the
  derived requirement for this subsystem"
- Gap analysis prominent: "This wheel meets momentum but exceeds your
  mass allocation by 40g — here's what that does to total mass margin"
- Make-or-buy decision: "No COTS component meets your requirement.
  Options: (a) relax the requirement, (b) modify a COTS component,
  (c) custom development (adds 12 months + 50 kEUR)"
- Heritage relevance: "This component flew on Sentinel-2 (LEO SSO) —
  same environment as your mission" vs "This component flew on a GEO
  comsat — different radiation environment"
- Interface compatibility: "This component uses SPI but your OBC only
  supports I2C and CAN — incompatible without adapter board"

---

## 8. REQUIREMENT ROLL-UP — Missing the full chain

**What the designer needs:**
"My pointing budget is at 0% margin. Which mission requirement does
this threaten? Which objective? Which stakeholder need?"

**What the tool does:** Shows "pointing margin: 0%" in the budget. No
upward link.

**What's missing:**
- Full chain: "Pointing margin 0% → threatens REQ-AOCS-001 (pointing
  ≤ 0.1°) → derived from function F-002 (point instrument at target) →
  serves objective OBJ-1 (10m multispectral imagery) → stakeholder need:
  farmers need field-scale crop health data"
- The consequence: "If pointing degrades to 0.15°, GSD degrades to 15m,
  which NO LONGER MEETS the stakeholder need"
- The options: "To recover pointing margin: (a) select higher-precision
  star tracker (+0.3 kg, +5 kEUR), (b) increase SA stiffness (+0.2 kg),
  (c) relax GSD requirement to 15m (needs stakeholder approval)"

---

## 9. WHAT THE TOOL SHOULD ACTUALLY DO AT EACH STEP

### Step 1: "Tell me about your problem"
- Free text: what need, for whom, where, when
- Tool SUGGESTS: similar past missions, typical mission classes,
  cost/schedule/performance envelope
- Tool ASKS: "Based on your description, is this an EO mission?
  Science? Communications?"

### Step 2: "Who cares about this?"
- Stakeholder entry with role and needs
- Tool ASKS: "Does the funding agency have a cost ceiling?"
- Tool ASKS: "What latency does the end user need? Daily? Hourly? NRT?"
- Tool COMPUTES: latency requirement → drives ground segment architecture

### Step 3: "What exactly do you need to achieve?"
- Objectives with measurable criteria
- Tool COMPUTES from objectives: "10m GSD + weekly revisit + Africa coverage
  → SSO at 500-600 km is optimal. Here's the trade:" [shows computed
  options with coverage maps]
- Tool COMPUTES: "10m GSD at 550 km needs 15cm aperture → ~8 kg payload →
  suggests micro or large-nano class → budget range 5-15 MEUR"

### Step 4: "Is space the right answer?"
- Tool PRESENTS computed alternatives:
  - Sentinel-2: 10m, 5-day revisit, FREE data — does this meet the need?
  - Planet Dove: 3m, daily, ~$5k/month — commercial option
  - Drone: 0.1m, on-demand, ~$500/flight — local coverage only
  - Own satellite: 10m, daily, 5-15 MEUR — full control
  - Tool ASKS: "Why can't you use Sentinel-2 data?"

### Step 5: "Here's what your mission looks like"
- Tool GENERATES from objectives + orbit + payload selection:
  - System architecture (block diagram)
  - ConOps with operational scenarios (not just power modes)
  - Data flow from sensor to end user
  - Ground segment options with cost
  - Preliminary budget estimates
  - "Start a collaborative session to refine this design"

### Step 6: Collaborative design session
- Tool GUIDES: "In this session, address these decisions: [list]"
- Each position answers their key questions
- Design converges
- Budgets close (or don't — tool shows WHY and WHAT TO CHANGE)
- Equipment selected with fit-gap analysis
- Tool GENERATES: BOM, FSW, test procedures, launch plan

---

## 10. SUMMARY: What's real vs what's needed

| Capability | Status | What's needed |
|-----------|--------|---------------|
| Design convergence loop | WORKING | Fine as-is |
| Multi-user collaboration | WORKING | Need session guidance |
| Equipment catalogue | WORKING | Need requirement-driven filtering + fit-gap + make-or-buy |
| Orbit selection | MISSING | Coverage/GSD/lifetime/cost trade calculator |
| Mission class selection | MISSING | Class advisor from objectives |
| Payload sizing from science reqs | MISSING | GSD → aperture → mass → power calculator (exists but not wired) |
| ConOps | POWER-ONLY | Need full operational scenarios, data flow, operator concept |
| Cost/mass estimation | DISCONNECTED | Should be computed from objectives, not input by user |
| Decision guidance | MISSING | Each step should present the question, the options, and the consequences |
| Requirement traceability | PARTIAL | Budget → requirement exists, but not full chain to objective/need |
| Session workflow | MISSING | Session types, agendas, decision lists |
