# Chapter 4 — Mission Needs, Stakeholders, Trade Studies and Concept of Operations

> **Recommended background.** NASA Systems Engineering Handbook §4.1, §4.4 and §6.8, Appendix C (How to Write a Good Requirement) and Appendix S (ConOps outline); NPR 7123.1D §3.2.1 (Process 1), §3.2.4 (Process 4) and §3.5.8 (Process 17); ECSS-E-ST-10C §5.1; SMAD4 Ch. 1–3 and Ch. 14. This chapter builds on the V-model and the 17 processes of Chapter 1 and on the regulatory and standards context of Chapters 2 and 3.

## Learning objectives

By the end of this chapter, you will be able to:

1. Write a clear problem statement that defines the mission need without prescribing a solution
2. Identify and categorise mission stakeholders using a structured analysis matrix
3. Define mission objectives with measurable success criteria and trace them through the MoE/MoP/TPM hierarchy
4. Structure and execute a trade study using weighted scoring methods (Decision Analysis — Process 17)
5. Evaluate space versus non-space alternatives objectively and document the decision rationale
6. Design a Concept of Operations (ConOps) including mission phases, operational modes, and data flow
7. Capture a mission concept — need, objectives, alternatives and ConOps outline — in a form that a concurrent-design team can work from

---

## 4.1 The problem statement

### 4.1.1 Why start with the problem?

NASA SEH Section 4.1.1 states: *"Clearly define the problem before solving it."*

The single most common failure mode in mission design is not technical — it is **solving the wrong problem**. Teams jump to solutions ("we need a 6U CubeSat at 500 km") before articulating the actual need ("agricultural monitoring in sub-Saharan Africa requires 10 m resolution multispectral imagery every 5 days"). This premature commitment to a solution:

- Closes off potentially superior alternatives (commercial data purchase, aerial surveys, ground sensors)
- Introduces unnecessary constraints that drive up cost and risk
- Makes it impossible to evaluate mission success (success against what?)
- Violates the fundamental SE principle of **WHAT before HOW**

[Source: NASA SEH Section 4.1; NASA SEH Appendix C — "How to Write a Good Requirement"]

### 4.1.2 Structure of a good problem statement

A rigorous problem statement answers four questions:

| Question | Content | Example |
|----------|---------|---------|
| **What is the problem?** | The capability gap — what is missing or inadequate | "Lack of timely, affordable multispectral imagery at sufficient resolution and revisit" |
| **Who is affected?** | Stakeholders and end users who suffer from the gap | "Agricultural monitoring agencies in sub-Saharan Africa" |
| **What is the impact?** | Consequence of not solving it — quantified if possible | "Delayed or inaccurate crop assessments affecting food aid allocation for 300M people" |
| **What constraints exist?** | Budget, schedule, political, regulatory, or technical limitations | "Budget: < $10M total mission cost; timeline: 3 years to first data" |

### 4.1.3 Good versus bad problem statements

**Example — GOOD:**
> "Agricultural monitoring agencies in sub-Saharan Africa lack timely, affordable access to multispectral imagery at sufficient resolution ($\leq 10$ m) and revisit rate ($\leq 5$ days) to support crop yield prediction and food security planning. Current Sentinel-2 data provides 10 m resolution but only 5-day revisit at the equator, and cloud cover reduces usable observations to approximately 60 %. The consequence is delayed or inaccurate crop assessments affecting food aid allocation for 300 million people. Budget constraint: total mission cost $< \$10$M; first data delivery within 3 years."

**Example — BAD:**
> "We need a 6U CubeSat with a multispectral imager at 500 km SSO."

The bad example prescribes a solution (6U CubeSat, SSO), specifies a design parameter (500 km), and says nothing about the actual problem. It is a **solution statement**, not a problem statement.

### 4.1.4 The WHAT versus HOW principle

At the mission need level, everything should describe **WHAT** is needed, not **HOW** to achieve it:

| WHAT (correct at this stage) | HOW (premature at this stage) |
|------------------------------|-------------------------------|
| "10 m resolution imagery" | "Use a 15 cm aperture telescope" |
| "Daily revisit at equator" | "Deploy a Walker delta constellation of 12 satellites" |
| "Data within 6 hours of acquisition" | "Use X-band downlink at 150 Mbps to 3 ground stations" |
| "Total cost under $10M" | "Use COTS components exclusively" |
| "5-year operational lifetime" | "Select radiation-hardened components" |

The HOW column is not wrong — these are all reasonable design decisions. But they belong in later phases (Phase A/B), not in the problem statement. Fixing the HOW prematurely eliminates design freedom and may lead to suboptimal solutions.

**Think about it.** Take any one line of the HOW column and list the design options it silently closes off. A 15 cm aperture, for instance, rules out a synthetic-aperture radar, a hosted payload on a larger bus, and buying the imagery from a commercial provider — before anyone has asked whether those would serve the farmers better.

---

## 4.2 Stakeholder identification and analysis

### 4.2.1 Who is a stakeholder?

NASA SEH Section 4.1.2 defines stakeholders as "all parties who have a legitimate interest in the system throughout its lifecycle." This is broader than just the end user — it includes everyone who affects or is affected by the mission.

### 4.2.2 Stakeholder categories for space missions

| Category | Examples | Typical needs | Typical constraints |
|----------|---------|---------------|-------------------|
| **End users** | Scientists, farmers, shipping companies, emergency responders | Data quality, resolution, latency, format, accessibility | Data rights, training, infrastructure |
| **Operators** | Mission control centre, ground station operators | Operability, automation level, staffing, training | Budget for operations, personnel availability |
| **Sponsors / funders** | Space agency (CSA), university, commercial investor, DND | Return on investment, schedule adherence, risk profile | Budget cap, political timelines, reporting requirements |
| **Regulatory** | ISED, ITU, FCC, export control (GAC) | Compliance with spectrum, debris, RSSSA, export regulations | Licensing timelines, filing requirements |
| **Launch provider** | SpaceX, Rocket Lab, ISRO, Arianespace | CDS compliance, mass/volume limits, schedule, payment | Interface requirements, launch window, manifesting |
| **Ground segment** | KSAT, SSC, SatNOGS, own stations | Frequency compatibility, data volume, contact time | Station availability, geographic coverage |
| **Data consumers** | Archives (e.g., EODMS), APIs, partner agencies | Data format (NetCDF, GeoTIFF), metadata standards, timeliness | Format standards, distribution agreements |
| **General public** | Taxpayers (for government-funded missions) | Value for money, transparency, societal benefit | Political expectations, public engagement |
| **Orbital environment** | Other satellite operators, debris community | Debris mitigation, spectrum cleanliness, collision avoidance | IADC guidelines, ISO 24113, FCC 5-year rule |

Company names here are representative examples, not endorsements.

### 4.2.3 Stakeholder analysis matrix

For each stakeholder, capture five attributes:

| Attribute | Description | Scale |
|-----------|-------------|-------|
| **Name / role** | Who are they? | Text |
| **Needs** | What do they require from the mission? | Text (specific, measurable where possible) |
| **Constraints** | What limitations do they impose? | Text (mandatory vs desirable) |
| **Priority** | How critical is satisfying this stakeholder? | Primary (must satisfy) / Secondary (should satisfy) / Tertiary (nice to have) |
| **Influence** | How much power do they have over the mission? | High / Medium / Low |

> **Industry practice.** For the RADARSAT Constellation Mission (RCM), the stakeholder analysis identified over 20 distinct stakeholder groups, including DND (maritime surveillance), Environment Canada (sea ice monitoring), Agriculture and Agri-Food Canada (crop monitoring), Natural Resources Canada (forestry), Public Safety Canada (disaster response), and international partners. Each stakeholder had different priority imaging modes, coverage requirements, and data latency needs. The systems engineering challenge was to design a 3-satellite constellation that satisfied all these needs within a single system architecture — a classic example of multi-stakeholder optimisation.

---

## 4.3 Mission objectives and the MoE/MoP/TPM hierarchy

### 4.3.1 From need to objectives

Objectives translate the problem statement into specific, testable goals. Each objective must have:

| Attribute | Description | Example |
|-----------|-------------|---------|
| **Text** | Clear statement of what the mission will achieve | "Provide 10 m GSD multispectral imagery over the target region" |
| **Priority** | Primary (mission fails without) or secondary (desirable) | Primary |
| **Measurable criterion** | How you know the objective is met — a number with a unit | "GSD $\leq$ 10 m at nadir, 4+ spectral bands, revisit $\leq$ 5 days" |
| **Type** | Category of objective | Observation, communication, navigation, science, technology demonstration |

### 4.3.2 Writing good objectives

| Good objective | Why it is good |
|---------------|---------------|
| "Provide 10 m GSD multispectral imagery with 4+ bands for the target region (30° S–30° N), with $\leq$ 5-day revisit and $\leq$ 24 h data latency" | Specific (10 m, 4 bands, geographic scope), measurable (all criteria have numbers and units), relevant to agriculture, achievable with CubeSat technology |
| "Achieve 99.5 % AIS ship detection probability in the North Atlantic within 30 minutes of ship transmission" | Specific (AIS, North Atlantic), measurable (99.5 %, 30 min), relevant to maritime safety |

| Bad objective | Why it is bad |
|--------------|-------------|
| "Take pictures from space" | Not specific, not measurable, no criterion for success |
| "Build a 3U CubeSat" | This is a solution, not an objective — it says nothing about what the mission should accomplish |
| "Demonstrate new technology" | What technology? What does "demonstrate" mean? How do you know it succeeded? |

### 4.3.3 The MoE / MoP / TPM hierarchy

These three measures form a chain from operational need to tracked design parameter:

[Source: NASA SEH Section 4.1.4, Section 4.2.4, Section 6.7.3]

| Measure | What it measures | Who sets it | Example | When evaluated |
|---------|-----------------|-------------|---------|---------------|
| **MoE** (Measure of Effectiveness) | How well the system satisfies the operational need | Users / stakeholders | "% of crop assessments delivered within 5 days of acquisition" | Phase E (operations) |
| **MoP** (Measure of Performance) | Technical performance of the system | Systems engineer | "GSD $\leq$ 10 m at nadir" | Phase C/D (verification) |
| **TPM** (Technical Performance Measure) | Design parameter tracked over time | Design team | "Current best estimate of imager mass vs allocation (1.5 kg target)" | All phases (continuous) |

The hierarchy flows downward, as Figure 4.1 shows for the agricultural-monitoring example: the stakeholder need is measured by an MoE, stated as a mission objective, measured by an MoP, written as a technical requirement and tracked through the design as a TPM.

![Vertical chain from stakeholder need through MoE, objective, MoP and requirement to TPM, with an agricultural-monitoring example at each level.](../assets/figures/fig_moe_mop_tpm.png)

**Figure 4.1** — From stakeholder need to tracked design parameter. Each level of the chain is shown with its agricultural-monitoring example, the party that owns the measure and the lifecycle phase in which it is evaluated: MoEs belong to the users and are evaluated in operations, MoPs to the systems engineer and are verified in Phase C/D, and TPMs to the design team and are tracked in every phase.

> **Key equation.** Measures of Effectiveness often involve probability and time, connecting to system-level performance:
>
> $$MoE = P_{\text{detection}} \times P_{\text{data delivery}} \times f(T_{\text{latency}})$$
>
> For an Earth observation mission:
>
> $$MoE_{\text{coverage}} = \frac{A_{\text{imaged per revisit}}}{A_{\text{total target}}} \times (1 - P_{\text{cloud}})$$
>
> where $A_{\text{imaged per revisit}}$ depends on swath width and orbit ground track spacing, $A_{\text{total target}}$ is the target area, and $P_{\text{cloud}}$ is the cloud cover probability.

---

## 4.4 From need to design: the flow

Figure 4.2 shows how the mission need flows through to design decisions without the need itself prescribing the design.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 520" style="max-width:700px; font-family: sans-serif;">
  <text x="350" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">From mission need to design decision</text>

  <!-- Level 1: Problem -->
  <rect x="50" y="45" width="600" height="45" rx="6" fill="#e8eaf6" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="63" font-size="10" font-weight="bold" fill="#1a237e">PROBLEM</text>
  <text x="70" y="78" font-size="9" fill="#333">"Need 10 m imagery, 5-day revisit, &lt; $10M" — describes WHAT is needed</text>

  <!-- Arrow -->
  <line x1="350" y1="90" x2="350" y2="110" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="105" font-size="8" fill="#888" font-style="italic">objectives derived</text>

  <!-- Level 2: Objective -->
  <rect x="50" y="115" width="600" height="45" rx="6" fill="#c5cae9" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="133" font-size="10" font-weight="bold" fill="#1a237e">OBJECTIVE</text>
  <text x="70" y="148" font-size="9" fill="#333">"Provide 10 m GSD multispectral imagery with ≤ 5-day revisit" — measurable goal</text>

  <!-- Arrow -->
  <line x1="350" y1="160" x2="350" y2="180" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="175" font-size="8" fill="#888" font-style="italic">mission trade (Process 17)</text>

  <!-- Level 3: Trade Decision -->
  <rect x="50" y="185" width="600" height="45" rx="6" fill="#fff9c4" stroke="#f9a825" stroke-width="2"/>
  <text x="70" y="203" font-size="10" font-weight="bold" fill="#e65100">TRADE DECISION</text>
  <text x="70" y="218" font-size="9" fill="#333">"Dedicated CubeSat — existing services don't meet revisit and resolution together" — justified choice</text>

  <!-- Arrow -->
  <line x1="350" y1="230" x2="350" y2="250" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="245" font-size="8" fill="#888" font-style="italic">requirements derived</text>

  <!-- Level 4: Requirement -->
  <rect x="50" y="255" width="600" height="45" rx="6" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
  <text x="70" y="273" font-size="10" font-weight="bold" fill="#1b5e20">REQUIREMENT</text>
  <text x="70" y="288" font-size="9" fill="#333">"The system shall achieve GSD ≤ 10 m at nadir" — verifiable "shall" statement</text>

  <!-- Arrow -->
  <line x1="350" y1="300" x2="350" y2="320" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="315" font-size="8" fill="#888" font-style="italic">design analysis</text>

  <!-- Level 5: Design Choice -->
  <rect x="50" y="325" width="600" height="45" rx="6" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/>
  <text x="70" y="343" font-size="10" font-weight="bold" fill="#0d47a1">DESIGN CHOICE</text>
  <text x="70" y="358" font-size="9" fill="#333">"SSO 500 km gives 10 m GSD with 15 cm aperture" — now we specify HOW</text>

  <!-- Arrow -->
  <line x1="350" y1="370" x2="350" y2="390" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="385" font-size="8" fill="#888" font-style="italic">equipment selection</text>

  <!-- Level 6: Equipment -->
  <rect x="50" y="395" width="600" height="45" rx="6" fill="#fce4ec" stroke="#c62828" stroke-width="2"/>
  <text x="70" y="413" font-size="10" font-weight="bold" fill="#b71c1c">EQUIPMENT</text>
  <text x="70" y="428" font-size="9" fill="#333">"Selected: XYZ telescope, 15 cm aperture, 1.5 kg, 8 W" — component-level HOW</text>

  <!-- Side annotation -->
  <rect x="50" y="460" width="220" height="40" rx="4" fill="#e0e0e0" stroke="#9e9e9e" stroke-width="1"/>
  <text x="160" y="477" text-anchor="middle" font-size="9" fill="#333" font-weight="bold">At each level the team decides.</text>
  <text x="160" y="490" text-anchor="middle" font-size="8" fill="#666">The design tool supports; it does not dictate.</text>

  <defs>
    <marker id="arrowDown" markerWidth="8" markerHeight="6" refX="4" refY="6" orient="auto">
      <path d="M0,0 L4,6 L8,0" fill="#555"/>
    </marker>
  </defs>
</svg>

**Figure 4.2** — From mission need to design decision. The problem and objective describe WHAT is needed; the trade decision justifies the chosen approach; only from the requirement level downward does the team specify HOW.

At each level in this hierarchy, the design team makes decisions informed by analysis and trade studies. A concurrent-design tool supports this process with parametric calculations and automated constraint checking, but the team retains decision authority.

---

## 4.5 Decision analysis framework

### 4.5.1 Process 17: Decision Analysis

NASA SEH Process 17 (Decision Analysis) provides the framework for structured alternative evaluation. Every major design decision should follow this process to ensure decisions are auditable, traceable, and defensible.

[Source: NASA SEH Section 6.8, Process 17: Decision Analysis]

### 4.5.2 The five elements of a rigorous trade study

| Element | Description | Pitfall to avoid |
|---------|-------------|-----------------|
| **1. Decision statement** | What are we deciding? Framed as a question. | Too broad ("What should we build?") or too narrow ("Which reaction wheel?") for the current phase |
| **2. Alternatives** | What are the options? Minimum 3, including "do nothing" | Straw-man alternatives designed to lose; failure to include obvious options |
| **3. Criteria** | What matters? Performance, cost, schedule, risk, compliance | Missing a critical criterion; criteria that overlap (double-counting) |
| **4. Weightings** | How important is each criterion? Normalised to sum to 1.0 | All criteria weighted equally (means nothing matters more than anything else); weights set after seeing scores |
| **5. Scoring** | How well does each alternative perform? | Inconsistent scoring scale; anchoring bias; group conformity |

### 4.5.3 Weighting methods

| Method | Procedure | Best when | Limitations |
|--------|-----------|-----------|------------|
| **Pairwise comparison** | Compare criteria two at a time; count wins. Weight = wins / total comparisons | Small number of criteria ($< 8$) | Circular preferences possible; does not capture magnitude |
| **Swing weighting** | For each criterion, assess the value of moving from worst to best case. Normalise. | Criteria have different units and scales | Requires clear understanding of worst/best cases |
| **Direct assignment** | Team discusses and agrees on weights | Quick preliminary assessment | Subjective; dominated by vocal team members |
| **AHP (Analytic Hierarchy Process)** | Pairwise comparison on a 1–9 ratio scale; compute eigenvector | Complex decisions with many stakeholders | Mathematically complex; consistency check needed |

> **Key equation (pairwise comparison).** For $n$ criteria, there are $\frac{n(n-1)}{2}$ pairwise comparisons. The raw weight of criterion $i$ is
>
> $$w_i^{\text{raw}} = \sum_{j \neq i} p_{ij}$$
>
> where $p_{ij} = 1$ if criterion $i$ is preferred over $j$, 0.5 for a tie, and 0 if $j$ is preferred. The normalised weight is
>
> $$w_i = \frac{w_i^{\text{raw}}}{\sum_{k=1}^{n} w_k^{\text{raw}}}$$

### 4.5.4 Scoring methods

| Type | Description | Example | When to use |
|------|-------------|---------|-------------|
| **Quantitative** | Numeric value normalised to 0–1 | Mass: 5 kg scores 0.8, 10 kg scores 0.4 | When hard numbers exist |
| **Qualitative** | Verbal rating mapped to number | "Excellent" = 1.0, "Good" = 0.75, "Fair" = 0.5, "Poor" = 0.25 | When only expert judgement is available |
| **Threshold (go/no-go)** | Pass/fail gate applied before scoring | "TRL $\geq 6$ required" — below threshold is eliminated | Non-negotiable requirements |

### 4.5.5 Weighted score calculation

For each alternative $a$ across $n$ criteria:

> **Key equation.**
>
> $$S(a) = \sum_{c=1}^{n} w_c \cdot s(a,c)$$
>
> where $w_c$ is the normalised weight of criterion $c$ and $s(a,c)$ is the normalised score (0–1) of alternative $a$ on criterion $c$.
>
> For "higher is better" criteria:
>
> $$s(a,c) = \frac{v(a,c) - v_{\min}(c)}{v_{\max}(c) - v_{\min}(c)}$$
>
> For "lower is better" criteria:
>
> $$s(a,c) = 1 - \frac{v(a,c) - v_{\min}(c)}{v_{\max}(c) - v_{\min}(c)}$$

### 4.5.6 Sensitivity analysis

A trade study result is only meaningful if it is **robust** — i.e., the ranking does not change with small perturbations in weights or scores. Sensitivity analysis tests this:

| Method | Procedure | What it reveals |
|--------|-----------|----------------|
| **Weight perturbation** | Vary each weight by $\pm 20\%$, re-normalise, re-score | Which criteria are "swing" criteria that could flip the outcome |
| **Score perturbation** | Vary each score by $\pm 1$ level, re-calculate | Which scores are the most uncertain and impactful |
| **Threshold analysis** | For each criterion, find the weight at which the 2nd-place alternative overtakes the 1st | How much the weights would need to change to reverse the decision |

> **Industry practice.** For the Iridium NEXT constellation (66 operational + 6 on-orbit spares), the initial trade study for the constellation architecture compared Walker Delta, Walker Star, and hybrid configurations across 12 criteria including global coverage, revisit time, inter-satellite link geometry, launch cost, and orbital debris risk. Sensitivity analysis revealed that the ranking was robust for all weight perturbations up to $\pm 30\%$, giving high confidence in the selected Walker Star configuration at 780 km altitude.

---

## 4.6 Space versus non-space alternatives

### 4.6.1 The most important trade study

Before committing to building a satellite, teams must honestly evaluate whether existing solutions meet the need. This is the most important trade study in the mission lifecycle because it determines whether the entire project should proceed.

### 4.6.2 Alternative categories

| Category | Examples | Strengths | Weaknesses |
|----------|---------|-----------|-----------|
| **Existing free data** | Copernicus Sentinel-2, Landsat 8/9 | Zero acquisition cost, proven quality, long archive | Fixed resolution/revisit, no tasking control |
| **Commercial data purchase** | Planet (SuperDove), Maxar (WorldView), ICEYE (SAR) | High resolution, fast tasking, no development risk | Ongoing cost, data rights limitations, vendor dependency |
| **Aerial (drones/aircraft)** | Survey drones, P-3 Orion, Twin Otter | Very high resolution ($< 1$ m), flexible scheduling | Limited area coverage, weather dependent, regulatory constraints |
| **Ground sensors** | IoT networks, weather stations, tide gauges | Continuous monitoring, low per-unit cost | Point measurements only, no spatial coverage |
| **Dedicated satellite** | New CubeSat, SmallSat, or microsatellite | Full control, custom instrument, IP ownership | High cost ($2–50M), development risk, 2–5 year schedule |
| **Constellation** | Multiple dedicated satellites | Global coverage, short revisit ($< 1$ day) | Much higher cost, operational complexity |
| **Hosted payload** | Payload on another operator's bus | Lower cost, shared bus risk | Compromised orbit, limited control, schedule dependency |

### 4.6.3 Decision criteria: when is space justified?

**Space is likely NOT the right answer when:**

- Existing free data (Sentinel-2, Landsat) meets resolution and revisit needs
- Coverage requirement is local (drones or aircraft are cheaper and higher resolution)
- Data rate is very low (ground sensors with cellular/satellite IoT backhaul suffice)
- Budget does not support minimum viable satellite cost (~$2M for a basic 3U CubeSat, indicative 2026)
- Technology readiness is too low for the available schedule

**Space is likely justified when:**

- Global or wide-area coverage is needed simultaneously
- Persistent monitoring is required (24/7 or very frequent revisit $< 5$ days)
- User needs data ownership and control over acquisition scheduling
- No existing service provides the required measurement type (e.g., specific wavelength, polarisation)
- Regulatory or sovereignty requirements demand national control over the sensor

### 4.6.4 Constellation sizing

For missions requiring short revisit, the number of satellites drives cost:

> **Key equation.** For a Walker Delta constellation at altitude $h$ with half-swath angle $\eta$, the number of orbital planes $P$ and satellites per plane $S$ needed for revisit time $T_{\text{rev}}$ is approximately
>
> $$P \times S \geq \frac{2\pi R_E}{v_{\text{ground}} \times T_{\text{rev}} \times \tan(\eta)}$$
>
> where $v_{\text{ground}} \approx 7.1$ km/s (ground track velocity at 500 km) and $\eta$ is related to the instrument swath width $W$ by $\eta = W / (2 R_E)$ for small angles.
>
> More practically, constellation cost scales sub-linearly due to learning curves:
>
> $$C_{\text{total}} = C_1 \times \sum_{i=1}^{N} i^{\log_2(L)}$$
>
> where $C_1$ is the first unit cost, $N$ is the number of satellites, and $L$ is the learning curve factor (typically 0.90–0.95 for small batches, 0.85 for large batches like Planet's SuperDove). Chapter 16 develops the learning curve further in the context of cost estimation.

---

## 4.7 Documenting the trade decision

Every trade study must produce an **auditable decision record**. NASA SEH Process 17 requires documentation of:

| Element | Content | Purpose |
|---------|---------|---------|
| **Decision statement** | What was decided | Clarity |
| **Alternatives considered** | All options evaluated, including rejected ones | Completeness |
| **Criteria and weights** | What mattered and how much | Transparency |
| **Scoring rationale** | Why each alternative received its score | Auditability |
| **Result and recommendation** | The selected alternative and its total score | Decision record |
| **Sensitivity analysis** | Robustness of the result | Confidence |
| **Risks of selected option** | What could go wrong with the chosen approach | Risk awareness |
| **Responsible person and date** | Who decided and when | Accountability |

> **Industry practice.** The Canadian Hydrographic Service evaluated commercial SAR data (ICEYE, Capella) versus a dedicated satellite for Arctic maritime surveillance. The trade study documented 8 alternatives across 11 criteria, with weights set by a stakeholder panel including DND, Transport Canada, and CCG. The decision to use RCM data supplemented by commercial SAR tasking — rather than building a new satellite — saved an estimated $100M while meeting 90 % of the maritime domain awareness requirements.

---

## 4.8 Concept of Operations

A **Concept of Operations (ConOps)** describes how the mission will be operated to deliver what the objectives demand: which elements exist, what phases the mission passes through, which modes the spacecraft occupies and how data flows from instrument to user. It is the bridge between the objectives of §4.3 and the requirements of Chapter 5, and it is the first document a concurrent-design team needs in order to size anything. NASA SEH Appendix S gives a complete outline; this section covers the four elements that drive early design.

### 4.8.1 Three segments of a space mission

Every space mission comprises three segments that must be designed together: the **space segment** (platform, payload and the communications that connect them to the ground), the **ground segment** (ground operations — commanding, telemetry, orbit determination — and the payload data centre that receives, processes and archives the data), and the **user segment** (the data products, services, portals and training through which the end users obtain value). The ConOps names each segment's elements and the interfaces between them — TM/TC on S-band, payload data on X- or Ka-band, orbit metadata and processed products over terrestrial networks. The detailed decomposition of the segments, their interfaces and the block diagram of the space segment are the subject of Chapter 8 §8.1; the ground segment itself is designed in Chapter 17. At the ConOps stage it is enough to draw an architecture diagram with the segments, the external systems they depend on (GNSS, relay satellites, in-situ sensors) and every connection labelled with its data type and frequency band.

### 4.8.2 Mission phases

The operational phases of the mission — distinct from the development phases of Chapter 1 §1.4 — are shown in Figure 4.3 and tabulated below. Each has its own activities, duration and dominant risks, and the ConOps must say what the spacecraft and ground segment do in each.

![Mission operations timeline from LEOP through commissioning, nominal and extended operations to disposal.](../assets/figures/fig_conops_timeline.png)

**Figure 4.3** — Mission operations timeline for a typical CubeSat mission: LEOP, commissioning, nominal and extended operations, and disposal, with indicative durations.

| Phase | Duration (typical CubeSat) | Activities | Key risks |
|-------|--------------------------|------------|-----------|
| **LEOP** | 1–3 days | Deployment, antenna deploy, first contact, initial health check | Deployment failure, tumbling, no contact |
| **Commissioning** | 2–4 weeks | Subsystem checkout, calibration, first light, orbit determination | Anomalies, calibration issues |
| **Nominal ops** | Months to years | Routine acquisition, downlink, orbit maintenance | Component degradation, anomalies |
| **Extended ops** | Beyond design life | Continued operations with degraded performance | Solar array degradation, propellant depletion |
| **Disposal** | Days to months | Passivation, deorbit manoeuvre or natural decay | Failure of deorbit system |

### 4.8.3 Operational modes

An **operational mode** is a defined configuration of the spacecraft: which subsystems are active, how it is pointed, how much power it draws and what data flows. Modes exist because a CubeSat cannot do everything at once — generation is limited to roughly 7–25 W for a 3U with deployable panels — and because the operators and the on-board FDIR logic need a small number of well-understood states to command and to fall back to. A safe mode with the minimum load and a Sun-pointing attitude is the anchor; the science, downlink and manoeuvre modes add load on top of it. Table 4.1 illustrates the concept with three of the modes of the 3U EO CubeSat running example; the complete mode table for the spacecraft, the transitions between modes and the FDIR rules that trigger them are given in Chapter 18.

**Table 4.1** — Illustrative operational modes for the 3U EO CubeSat running example (full table, with the nominal/standby mode at 4 W, in Chapter 18).

| Mode | Subsystems active | Pointing | Power | Data flow |
|------|-------------------|----------|-------|-----------|
| **Safe** | EPS, OBC, TTC (beacon), AOCS (coarse) | Sun-pointing | 2 W | Beacon only |
| **Imaging** | + Payload, AOCS (fine pointing) | Nadir or target | 8 W | Instrument → OBC storage |
| **Downlink** | + TTC (full TX power) | Ground station track | 10 W | OBC → TX → ground station |

### 4.8.4 Duty cycling

Not all modes can run simultaneously, and the orbit timeline determines what can happen when. For a typical 95-minute orbit at 500 km SSO:

- 60 min sunlight, 35 min eclipse
- ~10 min imaging per orbit (~10 % duty cycle)
- ~8 min downlink per pass (1–2 passes per day over a single ground station)
- ~42 min in the nominal/standby mode
- 35 min eclipse (battery-powered)

The orbit-average power demand is the duty-cycle-weighted sum of the mode powers, and it — together with the eclipse duration — is what sizes the solar array and the battery. The ConOps therefore has to state the duty cycle of every mode. The sizing equations themselves, and the worked UniSat-1 power budget, are given in Chapter 9 §9.2–§9.3.

[Source: Wertz et al., SMAD4, Chapter 11; ECSS-E-ST-20C power budget methodology]

### 4.8.5 Data flow

The ConOps must trace the data from instrument to user. Figure 4.4 shows the end-to-end pipeline and the parameter that sizes each stage:

![Horizontal data pipeline from instrument through on-board storage, downlink, ground reception, L0–L2 processing and archive to user delivery.](../assets/figures/fig_data_pipeline.png)

**Figure 4.4** — The end-to-end data pipeline, grouped by segment. The space segment generates, stores and downlinks the data; the ground segment receives, processes (L0 → L1 → L2) and archives it; the user segment receives the products. The key sizing parameter of each stage is written beneath it, and the pipeline is sustainable only if the daily downlink capacity equals or exceeds the daily data generated.

| Stage | Key parameter | Sized by |
|-------|--------------|---------|
| Data generation | GB/day | Payload data rate $\times$ imaging duty cycle |
| On-board storage | GB | Must hold $\geq 1$ day of data ($2\times$ for margin) |
| Downlink per pass | GB/pass | Link data rate $\times$ contact time per pass |
| Processing | hours | Algorithm complexity, compute infrastructure |
| User delivery | hours | Archive API, network bandwidth |

For the system to be sustainable, the daily downlink capacity must equal or exceed the daily data generation; if it does not, data accumulates on board and storage eventually fills. The levers are the link data rate, the number of passes, the contact time per pass and the data generated (duty cycle, on-board compression, selective downlink). The data budget that quantifies this balance is developed in Chapter 11 §11.9, and on-board storage sizing in Chapter 12.

---

## 4.9 Returning to UniSat-1: why 1U rather than 2U or 3U?

The UniSat-1 team must justify the choice of a 1U form factor for their MEMS magnetometer technology demonstration. This is a classic Process 17 (Decision Analysis) exercise.

**Decision statement:** "What CubeSat form factor best supports a MEMS magnetometer technology demonstration within the university's budget and schedule constraints?"

**Alternatives** (costs indicative, 2026):

| Alternative | Mass limit | Internal volume | Typical cost | Development time |
|-------------|-----------|-----------------|-------------|----------|
| 1U | 1.33 kg | ~1000 cm³ | 50–200 kEUR | 6–12 months |
| 2U | 2.66 kg | ~2000 cm³ | 100–400 kEUR | 12–18 months |
| 3U | 4.0 kg | ~3000 cm³ | 200–800 kEUR | 18–24 months |

**Criteria and scoring:**

| Criterion | Weight | 1U | 2U | 3U | Rationale |
|-----------|--------|-----|-----|-----|-----------|
| Cost | 0.35 | 1.0 | 0.5 | 0.2 | University budget is 150 kEUR total |
| Schedule | 0.25 | 1.0 | 0.6 | 0.3 | Must launch within 12 months |
| Payload fits | 0.20 | 0.8 | 1.0 | 1.0 | MEMS sensor is 50 g, 0.2 W — fits easily in 1U |
| Design simplicity | 0.10 | 1.0 | 0.7 | 0.5 | Smaller team, fewer subsystems |
| Data return | 0.10 | 0.5 | 0.7 | 1.0 | More volume allows better comms, but 9600 bps is sufficient for < 1 kbps payload |
| **Weighted total** | | **0.91** | **0.67** | **0.50** | |

**Result:** 1U wins decisively. The MEMS magnetometer payload (50 g, 0.2 W, < 1 kbps) has no need for the extra volume, mass, or power that 2U/3U would provide. The additional cost and schedule of a larger bus are unjustified.

**Sensitivity check:** Suppose the sponsor cares much less about cost and schedule than the team assumed, and the weights are changed to cost 0.15, schedule 0.15 and data return 0.40 (payload fit and simplicity unchanged). The totals become 0.76 (1U), 0.72 (2U) and 0.73 (3U): 1U still ranks first, but the margin shrinks from 0.24 to 0.03. Data return is therefore the *swing criterion* — the decision is robust to the weights the team actually holds, but a stakeholder who valued data volume above all else could reasonably reach a different answer, and the decision record should say so.

**Key lesson:** Do not over-design the bus for a simple payload. The 1U form factor imposes healthy constraints that force the team to focus on the mission objective rather than adding unnecessary capability.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Problem statement | Defines WHAT is needed, not HOW to solve it; answers what, who, impact, constraints |
| Stakeholder analysis | Identify all parties with legitimate interest; capture needs, constraints, priority, influence |
| Objectives | Must be specific, measurable, and traceable to stakeholder needs via the MoE/MoP/TPM chain |
| Trade study structure | 5 elements: decision, alternatives, criteria, weights, scores; must include sensitivity analysis |
| Space vs non-space | Existing services may already meet the need — evaluate honestly before committing to build |
| Decision documentation | Every trade decision must have auditable rationale per Process 17 |
| ConOps | Three segments (space, ground, user); phases from LEOP to disposal; operational modes and their duty cycles drive the power budget (Chapter 9) |
| Data pipeline | Daily downlink capacity must equal or exceed daily data generation (Chapter 11) |

---

## Problems

1. **Rewriting a solution statement.** A sponsor's brief reads: "We want a 6U CubeSat with a hyperspectral camera at 550 km sun-synchronous orbit to look at algal blooms in the Great Lakes." Rewrite this as a problem statement that answers the four questions of §4.1.2, inventing plausible figures for impact and constraints. Then list three alternatives to a dedicated satellite that your problem statement leaves open and the brief had closed off.

2. **Stakeholder analysis.** For a 3U Earth-observation CubeSat providing weekly NDVI imagery of the Canadian prairies to a provincial agriculture ministry, identify at least six stakeholders from at least five of the categories in §4.2.2 and complete the five-attribute matrix of §4.2.3 for each. Identify one pair of stakeholders whose needs conflict and propose how the conflict might be resolved at the objective level.

3. **MoE/MoP/TPM chain.** Trace the full hierarchy of §4.3.3 — stakeholder need, MoE, mission objective, MoP, technical requirement, TPM — for (a) the crop-monitoring objective in §4.3.2 and (b) the AIS ship-detection objective. For each TPM, state the current-best-estimate quantity, its allocation and who in Table 1.4 owns it.

4. **Pairwise weighting (warm-up).** Practise the pairwise comparison method of §4.5.3 by weighting four criteria for a lunch-restaurant choice — taste, cost, healthiness, speed — using your own preferences, then score three options on a 0–1 scale and compute the weighted total. Afterwards, repeat the exercise for the five criteria of §4.9 and compare the weights you obtain with those the UniSat-1 team assigned by direct assignment.

5. **Weighted scoring and sensitivity.** Three imaging payloads are being compared for the 3U EO CubeSat: A (mass 1.2 kg, power 6 W, GSD 8 m, TRL 8, cost 120 kEUR), B (0.9 kg, 4 W, 12 m, TRL 9, 60 kEUR) and C (1.5 kg, 9 W, 5 m, TRL 6, 200 kEUR). Using the criteria mass, power, GSD, TRL and cost with weights 0.15, 0.15, 0.30, 0.20, 0.20, normalise each criterion with the equations of §4.5.5 (identify which are "higher is better"), compute the weighted score of each alternative, and rank them. Then perform a weight-perturbation sensitivity analysis of ±20 % on each weight in turn and report whether the ranking ever changes. Finally, apply a threshold criterion "TRL ≥ 7" and state how the result changes.

6. **Space or not?** A conservation authority wants to monitor the water level of 40 reservoirs across Ontario once per day with 10 cm accuracy, with a 5-year budget of $3M. Using §4.6, evaluate at least four alternative categories against this need, state which you would recommend and why, and write the decision record of §4.7 for your recommendation (including at least two risks of the selected option).

7. **Constellation sizing.** Using §4.6.4, estimate the number of satellites needed for a 1-day revisit at the equator with a 50 km swath at 500 km altitude. Then estimate the total cost of that constellation if the first unit costs \$4M and the learning-curve factor is 0.90, and compare with a factor of 0.85. How much of the total is saved by the learning curve in each case compared with $N \times C_1$?

8. **ConOps for UniSat-1.** Write a one-page ConOps outline for UniSat-1 (Chapter 1 §1.7): the three segments and their connections, the five operational phases with durations appropriate to a 6-month 1U mission, and a mode table in the format of Table 4.1 with at least three modes, estimating the power of each mode from the subsystem values given in Chapter 1 §1.7. Which modes exist for UniSat-1 that the 3U EO CubeSat also has, and which 3U modes does UniSat-1 not need?

9. **Orbit-average power from duty cycles.** Using the 95-minute orbit timeline of §4.8.4 and the mode powers of Table 4.1 (take the nominal/standby mode as 4 W and the eclipse load as 3.5 W, as in Chapter 8 Table 8.4 and Chapter 18 Table 18.1), compute the orbit-average power demand of the 3U EO CubeSat as the duty-cycle-weighted sum of the mode powers. If the imaging duty cycle is doubled to 20 %, by how much does the orbit-average demand rise? What two design parameters would the Power Engineer in Table 1.4 then have to revisit (see Chapter 9)?

10. **Data balance.** The 3U EO CubeSat imager generates 150 Mbps while imaging for 10 minutes per orbit over 15 orbits per day, and the S-band downlink delivers 2 Mbps over two 8-minute passes per day with 80 % protocol efficiency. Compute the daily data generated and the daily downlink capacity, state whether the system balances, and — if not — rank the four levers listed in §4.8.5 by how much each would have to change to close the gap. Which lever would you pull first, and what other budgets (Chapter 8) would it affect?

---

## References

1. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016, Sections 4.1, 4.4, 6.8, Appendix C and Appendix S. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. NASA, *NPR 7123.1D — Systems Engineering Processes and Requirements*, 2020, Sections 3.2.1, 3.2.4 and 3.5.8. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
3. ECSS, *ECSS-E-ST-10C — System Engineering General Requirements*, 2009, Section 5.1. [https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
4. ECSS, *ECSS-M-ST-10C Rev.1 — Space Project Management*, 2009, Section 5.3. [https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
5. Wertz, J.R. et al., *Space Mission Engineering: The New SMAD* (SMAD4), Microcosm Press, 2011, Chapters 1–3 and 14. [https://www.microcosminc.com/](https://www.microcosminc.com/)
6. Saaty, T.L., *The Analytic Hierarchy Process*, McGraw-Hill, 1980. [https://doi.org/10.1016/0377-2217(90)90057-I](https://doi.org/10.1016/0377-2217(90)90057-I)
