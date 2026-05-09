# Session 1.4: Mission Needs, Stakeholder Analysis & Trade Studies

**Duration:** 6 hours (Thursday + Friday)
**Prerequisites:** Sessions 1.1--1.3
**References:**
- [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016 -- Sections 4.1, 4.4, 6.8](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [NASA, NPR 7123.1D -- Sections 3.2.1 (Process 1), 3.2.4 (Process 4), 3.5.8 (Process 17)](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
- [ECSS, ECSS-E-ST-10C -- Section 5.1 (Requirements Engineering)](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
- [ECSS, ECSS-M-ST-10C Rev.1 -- Section 5.3 (Review Process)](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
- [Wertz, J.R. et al., Space Mission Engineering: The New SMAD (SMAD4), Microcosm Press, 2011 -- Chapters 1--3](https://www.microcosminc.com/)
- [NASA SEH Appendix C -- How to Write a Good Requirement](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [NASA SEH Appendix S -- ConOps Outline](https://www.nasa.gov/reference/systems-engineering-handbook/)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Write a clear problem statement that defines the mission need without prescribing a solution
2. Identify and categorise mission stakeholders using a structured analysis matrix
3. Define mission objectives with measurable success criteria and trace them through the MoE/MoP/TPM hierarchy
4. Structure and execute a trade study using weighted scoring methods (Decision Analysis -- Process 17)
5. Evaluate space vs non-space alternatives objectively and document the decision rationale
6. Design a Concept of Operations (ConOps) including mission phases, operational modes, and data flow
7. Use SpaceCDF Steps 1--2 and the Trade Studies tab to capture and evaluate mission concepts

---

## Part 1: Mission Need & Stakeholder Analysis (Thursday AM -- 2 hours)

---

### 1. The Problem Statement (30 min)

#### 1.1 Why Start with the Problem?

NASA SEH Section 4.1.1 states: *"Clearly define the problem before solving it."*

The single most common failure mode in mission design is not technical -- it is **solving the wrong problem**. Teams jump to solutions ("we need a 6U CubeSat at 500 km") before articulating the actual need ("agricultural monitoring in sub-Saharan Africa requires 10 m resolution multispectral imagery every 5 days"). This premature commitment to a solution:

- Closes off potentially superior alternatives (commercial data purchase, aerial surveys, ground sensors)
- Introduces unnecessary constraints that drive up cost and risk
- Makes it impossible to evaluate mission success (success against what?)
- Violates the fundamental SE principle of **WHAT before HOW**

[Source: NASA SEH Section 4.1; NASA SEH Appendix C -- "How to Write a Good Requirement"]

#### 1.2 Structure of a Good Problem Statement

A rigorous problem statement answers four questions:

| Question | Content | Example |
|----------|---------|---------|
| **What is the problem?** | The capability gap -- what is missing or inadequate | "Lack of timely, affordable multispectral imagery at sufficient resolution and revisit" |
| **Who is affected?** | Stakeholders and end users who suffer from the gap | "Agricultural monitoring agencies in sub-Saharan Africa" |
| **What is the impact?** | Consequence of not solving it -- quantified if possible | "Delayed or inaccurate crop assessments affecting food aid allocation for 300M people" |
| **What constraints exist?** | Budget, schedule, political, regulatory, or technical limitations | "Budget: <$10M total mission cost; timeline: 3 years to first data" |

#### 1.3 Good vs Bad Problem Statements

**Example -- GOOD:**
> "Agricultural monitoring agencies in sub-Saharan Africa lack timely, affordable access to multispectral imagery at sufficient resolution ($\leq 10$ m) and revisit rate ($\leq 5$ days) to support crop yield prediction and food security planning. Current Sentinel-2 data provides 10 m resolution but only 5-day revisit at the equator, and cloud cover reduces usable observations to approximately 60%. The consequence is delayed or inaccurate crop assessments affecting food aid allocation for 300 million people. Budget constraint: total mission cost $< \$10$M; first data delivery within 3 years."

**Example -- BAD:**
> "We need a 6U CubeSat with a multispectral imager at 500 km SSO."

The bad example prescribes a solution (6U CubeSat, SSO), specifies a design parameter (500 km), and says nothing about the actual problem. It is a **solution statement**, not a problem statement.

#### 1.4 The WHAT vs HOW Principle

At the mission need level, everything should describe **WHAT** is needed, not **HOW** to achieve it:

| WHAT (correct at this stage) | HOW (premature at this stage) |
|------------------------------|-------------------------------|
| "10 m resolution imagery" | "Use a 15 cm aperture telescope" |
| "Daily revisit at equator" | "Deploy a Walker delta constellation of 12 satellites" |
| "Data within 6 hours of acquisition" | "Use X-band downlink at 150 Mbps to 3 ground stations" |
| "Total cost under $10M" | "Use COTS components exclusively" |
| "5-year operational lifetime" | "Select radiation-hardened components" |

The HOW column is not wrong -- these are all reasonable design decisions. But they belong in later phases (Phase A/B), not in the problem statement. Fixing the HOW prematurely eliminates design freedom and may lead to suboptimal solutions.

**Discussion prompt:** *Why is it harmful to specify HOW at this stage? What design options does it close off?*

---

### 2. Stakeholder Identification & Analysis (30 min)

#### 2.1 Who is a Stakeholder?

NASA SEH Section 4.1.2 defines stakeholders as "all parties who have a legitimate interest in the system throughout its lifecycle." This is broader than just the end user -- it includes everyone who affects or is affected by the mission.

#### 2.2 Stakeholder Categories for Space Missions

| Category | Examples | Typical Needs | Typical Constraints |
|----------|---------|---------------|-------------------|
| **End Users** | Scientists, farmers, shipping companies, emergency responders | Data quality, resolution, latency, format, accessibility | Data rights, training, infrastructure |
| **Operators** | Mission control centre, ground station operators | Operability, automation level, staffing, training | Budget for operations, personnel availability |
| **Sponsors / Funders** | Space agency (CSA), university, commercial investor, DND | Return on investment, schedule adherence, risk profile | Budget cap, political timelines, reporting requirements |
| **Regulatory** | ISED, ITU, FCC, export control (GAC) | Compliance with spectrum, debris, RSSSA, export regulations | Licensing timelines, filing requirements |
| **Launch Provider** | SpaceX, Rocket Lab, ISRO, Arianespace | CDS compliance, mass/volume limits, schedule, payment | Interface requirements, launch window, manifesting |
| **Ground Segment** | KSAT, SSC, SatNOGS, own stations | Frequency compatibility, data volume, contact time | Station availability, geographic coverage |
| **Data Consumers** | Archives (e.g., EODMS), APIs, partner agencies | Data format (NetCDF, GeoTIFF), metadata standards, timeliness | Format standards, distribution agreements |
| **General Public** | Taxpayers (for government-funded missions) | Value for money, transparency, societal benefit | Political expectations, public engagement |
| **Orbital Environment** | Other satellite operators, debris community | Debris mitigation, spectrum cleanliness, collision avoidance | IADC guidelines, ISO 24113, FCC 5-year rule |

#### 2.3 Stakeholder Analysis Matrix

For each stakeholder, capture five attributes:

| Attribute | Description | Scale |
|-----------|-------------|-------|
| **Name / Role** | Who are they? | Text |
| **Needs** | What do they require from the mission? | Text (specific, measurable where possible) |
| **Constraints** | What limitations do they impose? | Text (mandatory vs desirable) |
| **Priority** | How critical is satisfying this stakeholder? | Primary (must satisfy) / Secondary (should satisfy) / Tertiary (nice to have) |
| **Influence** | How much power do they have over the mission? | High / Medium / Low |

> **Industry Practice:** For the RADARSAT Constellation Mission (RCM), the stakeholder analysis identified over 20 distinct stakeholder groups, including DND (maritime surveillance), Environment Canada (sea ice monitoring), Agriculture and Agri-Food Canada (crop monitoring), Natural Resources Canada (forestry), Public Safety Canada (disaster response), and international partners. Each stakeholder had different priority imaging modes, coverage requirements, and data latency needs. The systems engineering challenge was to design a 3-satellite constellation that satisfied all these needs within a single system architecture -- a classic example of multi-stakeholder optimisation.

**Exercise:** *Complete Part A of Worksheet 1.4 -- identify at least 4 stakeholders for your team's mission and fill in the analysis matrix.*

---

### 3. Mission Objectives and the MoE/MoP/TPM Hierarchy (30 min)

#### 3.1 From Need to Objectives

Objectives translate the problem statement into specific, testable goals. Each objective must have:

| Attribute | Description | Example |
|-----------|-------------|---------|
| **Text** | Clear statement of what the mission will achieve | "Provide 10 m GSD multispectral imagery over the target region" |
| **Priority** | Primary (mission fails without) or secondary (desirable) | Primary |
| **Measurable criterion** | How you know the objective is met -- a number with a unit | "GSD $\leq$ 10 m at nadir, 4+ spectral bands, revisit $\leq$ 5 days" |
| **Type** | Category of objective | Observation, communication, navigation, science, technology demonstration |

#### 3.2 Writing Good Objectives

| Good Objective | Why It Is Good |
|---------------|---------------|
| "Provide 10 m GSD multispectral imagery with 4+ bands for the target region (30S--30N), with $\leq$ 5-day revisit and $\leq$ 24 h data latency" | Specific (10 m, 4 bands, geographic scope), measurable (all criteria have numbers + units), relevant to agriculture, achievable with CubeSat technology |
| "Achieve 99.5% AIS ship detection probability in the North Atlantic within 30 minutes of ship transmission" | Specific (AIS, North Atlantic), measurable (99.5%, 30 min), relevant to maritime safety |

| Bad Objective | Why It Is Bad |
|--------------|-------------|
| "Take pictures from space" | Not specific, not measurable, no criterion for success |
| "Build a 3U CubeSat" | This is a solution, not an objective -- it says nothing about what the mission should accomplish |
| "Demonstrate new technology" | What technology? What does "demonstrate" mean? How do you know it succeeded? |

#### 3.3 The MoE / MoP / TPM Hierarchy

These three measures form a chain from operational need to tracked design parameter:

[Source: NASA SEH Section 4.1.4, Section 4.2.4, Section 6.7.3]

| Measure | What It Measures | Who Sets It | Example | When Evaluated |
|---------|-----------------|-------------|---------|---------------|
| **MoE** (Measure of Effectiveness) | How well the system satisfies the operational need | Users / stakeholders | "% of crop assessments delivered within 5 days of acquisition" | Phase E (operations) |
| **MoP** (Measure of Performance) | Technical performance of the system | Systems engineer | "GSD $\leq$ 10 m at nadir" | Phase C/D (verification) |
| **TPM** (Technical Performance Measure) | Design parameter tracked over time | Design team | "Current best estimate of imager mass vs allocation (1.5 kg target)" | All phases (continuous) |

The hierarchy flows downward:

```
Stakeholder Need
  -> MoE (operational effectiveness)
    -> Mission Objective
      -> MoP (technical performance)
        -> Technical Requirement ("shall" statement)
          -> TPM (tracked design parameter)
```

> **Key Equation:** Measures of Effectiveness often involve probability and time, connecting to system-level performance:
>
> $MoE = P_{detection} \times P_{data\_delivery} \times f(T_{latency})$
>
> For an Earth observation mission:
>
> $MoE_{coverage} = \frac{A_{imaged\_per\_revisit}}{A_{total\_target}} \times (1 - P_{cloud})$
>
> Where $A_{imaged\_per\_revisit}$ depends on swath width and orbit ground track spacing, $A_{total\_target}$ is the target area, and $P_{cloud}$ is the cloud cover probability.

**Exercise:** *For one of your objectives, trace the full hierarchy from stakeholder need through MoE, MoP, and TPM. Complete Part B of Worksheet 1.4.*

---

### 4. From Need to Design: The Flow (20 min)

Show how the mission need flows through to design decisions without the need itself prescribing the design:

<!-- SVG DIAGRAM: Need to Design Flow -->

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 520" style="max-width:700px; font-family: 'Segoe UI', Arial, sans-serif; background: #fafafa; border: 1px solid #ddd; border-radius: 8px;">
  <text x="350" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">From Mission Need to Design Decision</text>

  <!-- Level 1: Problem -->
  <rect x="50" y="45" width="600" height="45" rx="6" fill="#e8eaf6" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="63" font-size="10" font-weight="bold" fill="#1a237e">PROBLEM</text>
  <text x="70" y="78" font-size="9" fill="#333">"Need 10m imagery, 5-day revisit, &lt;$10M" -- describes WHAT is needed</text>

  <!-- Arrow -->
  <line x1="350" y1="90" x2="350" y2="110" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="105" font-size="8" fill="#888" font-style="italic">objectives derived</text>

  <!-- Level 2: Objective -->
  <rect x="50" y="115" width="600" height="45" rx="6" fill="#c5cae9" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="133" font-size="10" font-weight="bold" fill="#1a237e">OBJECTIVE</text>
  <text x="70" y="148" font-size="9" fill="#333">"Provide 10m GSD multispectral imagery with &lt;=5 day revisit" -- measurable goal</text>

  <!-- Arrow -->
  <line x1="350" y1="160" x2="350" y2="180" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="175" font-size="8" fill="#888" font-style="italic">mission trade (Process 17)</text>

  <!-- Level 3: Trade Decision -->
  <rect x="50" y="185" width="600" height="45" rx="6" fill="#fff9c4" stroke="#f9a825" stroke-width="2"/>
  <text x="70" y="203" font-size="10" font-weight="bold" fill="#e65100">TRADE DECISION</text>
  <text x="70" y="218" font-size="9" fill="#333">"Dedicated CubeSat -- existing services don't meet revisit+resolution together" -- justified choice</text>

  <!-- Arrow -->
  <line x1="350" y1="230" x2="350" y2="250" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="245" font-size="8" fill="#888" font-style="italic">requirements derived</text>

  <!-- Level 4: Requirement -->
  <rect x="50" y="255" width="600" height="45" rx="6" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
  <text x="70" y="273" font-size="10" font-weight="bold" fill="#1b5e20">REQUIREMENT</text>
  <text x="70" y="288" font-size="9" fill="#333">"The system shall achieve GSD &lt;= 10m at nadir" -- verifiable "shall" statement</text>

  <!-- Arrow -->
  <line x1="350" y1="300" x2="350" y2="320" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="315" font-size="8" fill="#888" font-style="italic">design analysis</text>

  <!-- Level 5: Design Choice -->
  <rect x="50" y="325" width="600" height="45" rx="6" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/>
  <text x="70" y="343" font-size="10" font-weight="bold" fill="#0d47a1">DESIGN CHOICE</text>
  <text x="70" y="358" font-size="9" fill="#333">"SSO 500 km gives 10m GSD with 15cm aperture" -- now we specify HOW</text>

  <!-- Arrow -->
  <line x1="350" y1="370" x2="350" y2="390" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="385" font-size="8" fill="#888" font-style="italic">equipment selection</text>

  <!-- Level 6: Equipment -->
  <rect x="50" y="395" width="600" height="45" rx="6" fill="#fce4ec" stroke="#c62828" stroke-width="2"/>
  <text x="70" y="413" font-size="10" font-weight="bold" fill="#b71c1c">EQUIPMENT</text>
  <text x="70" y="428" font-size="9" fill="#333">"Selected: XYZ Telescope, 15cm aperture, 1.5 kg, 8W" -- component-level HOW</text>

  <!-- Side annotation -->
  <rect x="50" y="460" width="200" height="40" rx="4" fill="#e0e0e0" stroke="#9e9e9e" stroke-width="1"/>
  <text x="150" y="477" text-anchor="middle" font-size="9" fill="#333" font-weight="bold">Each level: team decides.</text>
  <text x="150" y="490" text-anchor="middle" font-size="8" fill="#666">SpaceCDF supports, does not dictate.</text>

  <defs>
    <marker id="arrowDown" markerWidth="8" markerHeight="6" refX="4" refY="6" orient="auto">
      <path d="M0,0 L4,6 L8,0" fill="#555"/>
    </marker>
  </defs>
</svg>

At each level in this hierarchy, the design team makes decisions informed by analysis and trade studies. The tool supports this process with parametric calculations and automated constraint checking, but the team retains decision authority.

---

## Part 2: Trade Study Methodology (Thursday PM -- 2 hours)

---

### 5. Decision Analysis Framework (40 min)

#### 5.1 Process 17: Decision Analysis

NASA SEH Process 17 (Decision Analysis) provides the framework for structured alternative evaluation. Every major design decision should follow this process to ensure decisions are auditable, traceable, and defensible.

[Source: NASA SEH Section 6.8, Process 17: Decision Analysis]

#### 5.2 The Five Elements of a Rigorous Trade Study

| Element | Description | Pitfall to Avoid |
|---------|-------------|-----------------|
| **1. Decision statement** | What are we deciding? Framed as a question. | Too broad ("What should we build?") or too narrow ("Which reaction wheel?") for the current phase |
| **2. Alternatives** | What are the options? Minimum 3, including "do nothing" | Straw-man alternatives designed to lose; failure to include obvious options |
| **3. Criteria** | What matters? Performance, cost, schedule, risk, compliance | Missing a critical criterion; criteria that overlap (double-counting) |
| **4. Weightings** | How important is each criterion? Normalised to sum to 1.0 | All criteria weighted equally (means nothing matters more than anything else); weights set after seeing scores |
| **5. Scoring** | How well does each alternative perform? | Inconsistent scoring scale; anchoring bias; group conformity |

#### 5.3 Weighting Methods

| Method | Procedure | Best When | Limitations |
|--------|-----------|-----------|------------|
| **Pairwise comparison** | Compare criteria two at a time; count wins. Weight = wins / total comparisons | Small number of criteria ($< 8$) | Circular preferences possible; does not capture magnitude |
| **Swing weighting** | For each criterion, assess the value of moving from worst to best case. Normalise. | Criteria have different units and scales | Requires clear understanding of worst/best cases |
| **Direct assignment** | Team discusses and agrees on weights | Quick preliminary assessment | Subjective; dominated by vocal team members |
| **AHP (Analytic Hierarchy Process)** | Pairwise comparison on a 1--9 ratio scale; compute eigenvector | Complex decisions with many stakeholders | Mathematically complex; consistency check needed |

> **Key Equation (Pairwise Comparison):** For $n$ criteria, there are $\frac{n(n-1)}{2}$ pairwise comparisons. The raw weight of criterion $i$ is:
>
> $w_i^{raw} = \sum_{j \neq i} p_{ij}$
>
> Where $p_{ij} = 1$ if criterion $i$ is preferred over $j$, 0.5 for a tie, and 0 if $j$ is preferred. The normalised weight is:
>
> $w_i = \frac{w_i^{raw}}{\sum_{k=1}^{n} w_k^{raw}}$

#### 5.4 Scoring Methods

| Type | Description | Example | When to Use |
|------|-------------|---------|-------------|
| **Quantitative** | Numeric value normalised to 0--1 | Mass: 5 kg scores 0.8, 10 kg scores 0.4 | When hard numbers exist |
| **Qualitative** | Verbal rating mapped to number | "Excellent" = 1.0, "Good" = 0.75, "Fair" = 0.5, "Poor" = 0.25 | When only expert judgment is available |
| **Threshold (go/no-go)** | Pass/fail gate applied before scoring | "TRL $\geq 6$ required" -- below threshold is eliminated | Non-negotiable requirements |

#### 5.5 Weighted Score Calculation

For each alternative $a$ across $n$ criteria:

> **Key Equation:**
>
> $S(a) = \sum_{c=1}^{n} w_c \cdot s(a,c)$
>
> Where $w_c$ is the normalised weight of criterion $c$ and $s(a,c)$ is the normalised score (0--1) of alternative $a$ on criterion $c$.
>
> For "higher is better" criteria:
>
> $s(a,c) = \frac{v(a,c) - v_{min}(c)}{v_{max}(c) - v_{min}(c)}$
>
> For "lower is better" criteria:
>
> $s(a,c) = 1 - \frac{v(a,c) - v_{min}(c)}{v_{max}(c) - v_{min}(c)}$

#### 5.6 Sensitivity Analysis

A trade study result is only meaningful if it is **robust** -- i.e., the ranking does not change with small perturbations in weights or scores. Sensitivity analysis tests this:

| Method | Procedure | What It Reveals |
|--------|-----------|----------------|
| **Weight perturbation** | Vary each weight by $\pm 20\%$, re-normalise, re-score | Which criteria are "swing" criteria that could flip the outcome |
| **Score perturbation** | Vary each score by $\pm 1$ level, re-calculate | Which scores are the most uncertain and impactful |
| **Threshold analysis** | For each criterion, find the weight at which the 2nd-place alternative overtakes the 1st | How much the weights would need to change to reverse the decision |

> **Industry Practice:** For the Iridium NEXT constellation (66 operational + 6 on-orbit spares), the initial trade study for the constellation architecture compared Walker Delta, Walker Star, and hybrid configurations across 12 criteria including global coverage, revisit time, inter-satellite link geometry, launch cost, and orbital debris risk. Sensitivity analysis revealed that the ranking was robust for all weight perturbations up to $\pm 30\%$, giving high confidence in the selected Walker Star configuration at 780 km altitude.

**Exercise:** *Practice the pairwise comparison method by weighting 4 criteria for a lunch restaurant choice: taste, cost, healthiness, speed. Then score 3 options. This builds the skill on a low-stakes example before applying it to mission design.*

---

### 6. Space vs Non-Space Alternatives (30 min)

#### 6.1 The Most Important Trade Study

Before committing to building a satellite, teams must honestly evaluate whether existing solutions meet the need. This is the most important trade study in the mission lifecycle because it determines whether the entire project should proceed.

#### 6.2 Alternative Categories

| Category | Examples | Strengths | Weaknesses |
|----------|---------|-----------|-----------|
| **Existing free data** | Copernicus Sentinel-2, Landsat 8/9 | Zero acquisition cost, proven quality, long archive | Fixed resolution/revisit, no tasking control |
| **Commercial data purchase** | Planet (SuperDove), Maxar (WorldView), ICEYE (SAR) | High resolution, fast tasking, no development risk | Ongoing cost, data rights limitations, vendor dependency |
| **Aerial (drones/aircraft)** | Survey drones, P-3 Orion, Twin Otter | Very high resolution ($< 1$ m), flexible scheduling | Limited area coverage, weather dependent, regulatory constraints |
| **Ground sensors** | IoT networks, weather stations, tide gauges | Continuous monitoring, low per-unit cost | Point measurements only, no spatial coverage |
| **Dedicated satellite** | New CubeSat, SmallSat, or microsatellite | Full control, custom instrument, IP ownership | High cost ($2--50M), development risk, 2--5 year schedule |
| **Constellation** | Multiple dedicated satellites | Global coverage, short revisit ($< 1$ day) | Much higher cost, operational complexity |
| **Hosted payload** | Payload on another operator's bus | Lower cost, shared bus risk | Compromised orbit, limited control, schedule dependency |

#### 6.3 Decision Criteria: When is Space Justified?

**Space is likely NOT the right answer when:**
- Existing free data (Sentinel-2, Landsat) meets resolution and revisit needs
- Coverage requirement is local (drones or aircraft are cheaper and higher resolution)
- Data rate is very low (ground sensors with cellular/satellite IoT backhaul suffice)
- Budget does not support minimum viable satellite cost (~$2M for a basic 3U CubeSat)
- Technology readiness is too low for the available schedule

**Space is likely justified when:**
- Global or wide-area coverage is needed simultaneously
- Persistent monitoring is required (24/7 or very frequent revisit $< 5$ days)
- User needs data ownership and control over acquisition scheduling
- No existing service provides the required measurement type (e.g., specific wavelength, polarisation)
- Regulatory or sovereignty requirements demand national control over the sensor

#### 6.4 Constellation Sizing

For missions requiring short revisit, the number of satellites drives cost:

> **Key Equation:** For a Walker Delta constellation at altitude $h$ with half-swath angle $\eta$, the number of orbital planes $P$ and satellites per plane $S$ needed for revisit time $T_{rev}$ is approximately:
>
> $P \times S \geq \frac{2\pi R_E}{v_{ground} \times T_{rev} \times \tan(\eta)}$
>
> Where $v_{ground} \approx 7.1$ km/s (ground track velocity at 500 km) and $\eta$ is related to the instrument swath width $W$ by $\eta = W / (2 R_E)$ for small angles.
>
> More practically, constellation cost scales sub-linearly due to learning curves:
>
> $C_{total} = C_1 \times \sum_{i=1}^{N} i^{\log_2(L)}$
>
> Where $C_1$ is the first unit cost, $N$ is the number of satellites, and $L$ is the learning curve factor (typically 0.90--0.95 for small batches, 0.85 for large batches like Planet's SuperDove).

---

### 7. Documenting the Trade Decision (20 min)

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

> **Industry Practice:** The Canadian Hydrographic Service evaluated commercial SAR data (ICEYE, Capella) versus a dedicated satellite for Arctic maritime surveillance. The trade study documented 8 alternatives across 11 criteria, with weights set by a stakeholder panel including DND, Transport Canada, and CCG. The decision to use RCM data supplemented by commercial SAR tasking -- rather than building a new satellite -- saved an estimated $100M while meeting 90% of the maritime domain awareness requirements.

---

## Part 3: Concept of Operations (Friday -- 2 hours)

---

### 8. Mission Architecture (30 min)

#### 8.1 Three Segments of a Space Mission

Every space mission comprises three segments that must be designed together:

| Segment | Components | Key Design Drivers |
|---------|-----------|-------------------|
| **Space Segment** | Platform (bus): EPS, AOCS, OBC, thermal, structure, propulsion. Payload: instrument(s). Communications: TT&C + payload data link. | Mass, power, volume, orbit, lifetime |
| **Ground Segment** | Ground Operations: commanding, telemetry, orbit determination. Payload Data Centre: data reception, processing (L0-L1-L2-L3), archive. | Contact time, data volume, processing capacity |
| **User Segment** | Data products and services. APIs, portals, archives. Training and documentation. | Latency, format, accessibility, user capacity |

#### 8.2 Data Interfaces Between Segments

| Interface | Direction | Band/Protocol | Content |
|-----------|-----------|--------------|---------|
| TM/TC | Space <-> Ground Ops | S-band (typical) | Housekeeping telemetry, telecommands |
| Payload data | Space -> Data Centre | X-band or Ka-band | Science/imagery data (high volume) |
| Orbit/TLE | Ground Ops -> Data Centre | Network | Geolocation metadata for data products |
| Data products | Data Centre -> Users | Internet/API | Processed imagery (L2/L3), analytics |

#### 8.3 Interactive Architecture Diagram

SpaceCDF provides a **drag-and-drop architecture diagram editor** in the ConOps tab:

| Symbol | Type | Represents |
|--------|------|-----------|
| Satellite (blue) | `satellite` | Space segment (spacecraft + payload) |
| Ground Station (green) | `groundStation` | Ground receiving station with antenna |
| Processing (cyan) | `processing` | Data processing, MCC, archive |
| User (amber) | `user` | End user / data consumer |
| Sensor (orange) | `sensor` | Ground sensor, IoT device, in-situ instrument |
| GNSS/External (purple) | `gnss` | External system (GNSS, relay sat, other constellation) |

**Exercise:** *In the ConOps tab, build your mission architecture diagram. Add all segments, label all connections with data type and frequency band.*

---

### 9. Mission Phases and Operational Modes (30 min)

#### 9.1 Operational Mission Phases

| Phase | Duration (typical CubeSat) | Activities | Key Risks |
|-------|--------------------------|------------|-----------|
| **LEOP** | 1--3 days | Deployment, antenna deploy, first contact, initial health check | Deployment failure, tumbling, no contact |
| **Commissioning** | 2--4 weeks | Subsystem checkout, calibration, first light, orbit determination | Anomalies, calibration issues |
| **Nominal Ops** | Months to years | Routine acquisition, downlink, orbit maintenance | Component degradation, anomalies |
| **Extended Ops** | Beyond design life | Continued operations with degraded performance | Solar array degradation, propellant depletion |
| **Disposal** | Days to months | Passivation, deorbit manoeuvre or natural decay | Failure of deorbit system |

#### 9.2 Operational Modes and Power Budgets

Each mode defines which subsystems are active, the pointing configuration, power demand, and data flow:

| Mode | Subsystems Active | Pointing | Power (3U typical) | Data Flow |
|------|-------------------|----------|-------------------|-----------|
| **Safe** | EPS, OBC, TTC (beacon), AOCS (coarse) | Sun-pointing | ~1--2 W | Beacon only |
| **Idle** | EPS, OBC, AOCS (standby), TTC (beacon) | Inertial hold | ~2 W | Health TM periodic |
| **Science/Imaging** | + Payload, AOCS (fine pointing) | Nadir or target | ~6 W | Instrument -> OBC storage |
| **Downlink** | + TTC (full TX power) | Ground station track | ~8 W | OBC -> TX -> GS |
| **Eclipse** | EPS (battery), OBC, TCS (heaters), AOCS | Inertial hold | ~3 W (battery) | None |
| **Orbit Maintenance** | + Propulsion | Thrust direction | ~7 W | Manoeuvre TM |

#### 9.3 Duty Cycling and Power Analysis

CubeSats have limited power generation (7--25 W for a 3U with deployable panels). Not all modes can run simultaneously. The orbit timeline determines what can happen when:

**Typical 95-minute orbit at 500 km SSO:**
- 60 min sunlight, 35 min eclipse
- ~10 min imaging per orbit (~10% duty cycle)
- ~8 min downlink per pass (1--2 passes/day over a single ground station)
- ~42 min idle
- 35 min eclipse (battery-powered)

> **Key Equations -- Power Budget:**
>
> Orbit-average power:
>
> $P_{avg} = \sum_{i} P_{mode,i} \times DC_i$
>
> Where $DC_i$ is the duty cycle (fraction of orbit) for each mode.
>
> Solar array sizing:
>
> $P_{SA} = P_{sunlight} + \frac{P_{eclipse} \times t_{eclipse}}{t_{sunlight} \times \eta_{charge}}$
>
> Where $\eta_{charge} \approx 0.9$ (battery charge efficiency).
>
> Battery sizing:
>
> $E_{battery} = \frac{P_{eclipse} \times t_{eclipse}}{DoD \times \eta_{discharge}}$
>
> Where $DoD$ is the maximum depth of discharge (typically 0.2--0.3 for long life, up to 0.5 for short missions) and $\eta_{discharge} \approx 0.95$.

[Source: Wertz et al., SMAD4, Chapter 11; ECSS-E-ST-20C power budget methodology]

---

### 10. Data Flow Pipeline (20 min)

#### 10.1 End-to-End Data Flow

```
Instrument -> Onboard Storage -> Downlink -> Ground Reception
  -> Processing (L0 -> L1 -> L2) -> Archive -> User Delivery
```

| Stage | Key Parameter | Sized By |
|-------|--------------|---------|
| Data generation | GB/day | Payload data rate $\times$ imaging duty cycle |
| Onboard storage | GB | Must hold $\geq 1$ day of data ($2\times$ for margin) |
| Downlink per pass | GB/pass | Link data rate $\times$ contact time per pass |
| Processing | hours | Algorithm complexity, compute infrastructure |
| User delivery | hours | Archive API, network bandwidth |

#### 10.2 Data Budget Balance

> **Key Equation:** For the system to be sustainable, daily downlink capacity must equal or exceed daily data generation:
>
> $C_{downlink} = R_{data} \times N_{passes} \times t_{contact} \times \eta_{protocol} \geq G_{daily}$
>
> Where:
> - $R_{data}$ = data link rate (Mbps)
> - $N_{passes}$ = number of ground station passes per day
> - $t_{contact}$ = average contact time per pass (seconds)
> - $\eta_{protocol}$ = protocol overhead factor (~0.8 for CCSDS framing)
> - $G_{daily}$ = daily data generation (Mb)
>
> If $C_{downlink} < G_{daily}$, data accumulates on board and storage eventually fills. Solutions:
> - Increase $R_{data}$ (higher TX power, higher frequency band, better antenna)
> - Increase $N_{passes}$ (more ground stations, polar ground station for SSO)
> - Increase $t_{contact}$ (higher altitude increases contact time but worsens resolution)
> - Decrease $G_{daily}$ (lower duty cycle, on-board compression, selective downlink)

**SpaceCDF exercise:** *Check the Data Budget on the Dashboard. Does your design balance? If not, which parameter would you change first?*

---

### 11. ConOps Tool Exercise (20 min)

1. Navigate to the **ConOps** tab in SpaceCDF
2. Review and edit the **mission architecture diagram** -- add all segments and connections
3. Edit the **mission phases**: adjust durations for your mission type
4. Review the **operational modes**: are the right modes defined? Adjust power values.
5. Check the **data flow pipeline**: does downlink capacity balance data generation?

**Complete Worksheet 1.4, Parts E and F:** Document your ConOps outline and calculate the orbit-average power budget.

---

### 1U Worked Example: UniSat-1

**Trade Study: Why 1U instead of 2U or 3U for UniSat-1?**

The UniSat-1 team must justify the choice of a 1U form factor for their MEMS magnetometer technology demonstration. This is a classic Process 17 (Decision Analysis) exercise.

**Decision statement:** "What CubeSat form factor best supports a MEMS magnetometer technology demonstration within the university's budget and schedule constraints?"

**Alternatives:**

| Alternative | Mass Limit | Internal Volume | Typical Cost | Dev Time |
|-------------|-----------|-----------------|-------------|----------|
| 1U | 1.33 kg | ~1000 cm^3 | 50--200 kEUR | 6--12 months |
| 2U | 2.66 kg | ~2000 cm^3 | 100--400 kEUR | 12--18 months |
| 3U | 4.0 kg | ~3000 cm^3 | 200--800 kEUR | 18--24 months |

**Criteria and scoring:**

| Criterion | Weight | 1U | 2U | 3U | Rationale |
|-----------|--------|-----|-----|-----|-----------|
| Cost | 0.35 | 1.0 | 0.5 | 0.2 | University budget is 150 kEUR total |
| Schedule | 0.25 | 1.0 | 0.6 | 0.3 | Must launch within 12 months |
| Payload fits | 0.20 | 0.8 | 1.0 | 1.0 | MEMS sensor is 50 g, 0.2 W -- fits easily in 1U |
| Design simplicity | 0.10 | 1.0 | 0.7 | 0.5 | Smaller team, fewer subsystems |
| Data return | 0.10 | 0.5 | 0.7 | 1.0 | More volume allows better comms, but 9600 bps is sufficient for < 1 kbps payload |
| **Weighted Total** | | **0.90** | **0.63** | **0.41** | |

**Result:** 1U wins decisively. The MEMS magnetometer payload (50 g, 0.2 W, < 1 kbps) has no need for the extra volume, mass, or power that 2U/3U would provide. The additional cost and schedule of a larger bus are unjustified.

**Sensitivity check:** Even if cost weight drops from 0.35 to 0.15 (and schedule from 0.25 to 0.15, redistributing to data return), 1U still wins (0.82 vs 0.68 vs 0.51). The result is robust.

**Key lesson:** Do not over-design the bus for a simple payload. The 1U form factor imposes healthy constraints that force the team to focus on the mission objective rather than adding unnecessary capability.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Problem statement | Defines WHAT is needed, not HOW to solve it; answers what, who, impact, constraints |
| Stakeholder analysis | Identify all parties with legitimate interest; capture needs, constraints, priority, influence |
| Objectives | Must be specific, measurable, and traceable to stakeholder needs via MoE/MoP/TPM chain |
| Trade study structure | 5 elements: decision, alternatives, criteria, weights, scores; must include sensitivity analysis |
| Space vs non-space | Existing services may already meet the need -- evaluate honestly before committing to build |
| Decision documentation | Every trade decision must have auditable rationale per Process 17 |
| ConOps | Three segments (space, ground, user); operational modes drive power budget via duty cycling |
| Data pipeline | Daily downlink capacity must equal or exceed daily data generation |

---

## References

1. [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. [NASA, NPR 7123.1D -- Systems Engineering Processes and Requirements, 2020](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
3. [ECSS, ECSS-E-ST-10C -- System Engineering General Requirements, 2009](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
4. [Wertz, J.R. et al., Space Mission Engineering: The New SMAD (SMAD4), Microcosm Press, 2011](https://www.microcosminc.com/)
5. [NASA SEH Appendix C -- How to Write a Good Requirement](https://www.nasa.gov/reference/systems-engineering-handbook/)
6. [NASA SEH Appendix S -- ConOps Outline](https://www.nasa.gov/reference/systems-engineering-handbook/)
7. [Saaty, T.L., "The Analytic Hierarchy Process", McGraw-Hill, 1980](https://doi.org/10.1016/0377-2217(90)90057-I)
