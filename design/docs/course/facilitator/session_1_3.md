# Session 1.3: Mission Trade Analysis — Is Space the Right Answer?

**Duration:** 2 hours
**Prerequisites:** Session 1.2 (problem statement and objectives defined)
**References:** NASA SEH §4.4 (Process 17: Decision Analysis), ECSS-M-ST-10C §5.3

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Structure a trade study with criteria, weightings, and thresholds
2. Evaluate space vs non-space alternatives objectively
3. Identify when an existing service meets the need (no new satellite required)
4. Use SpaceCDF's mission trade analysis tool
5. Document the rationale for the selected concept

---

## 1. Decision Analysis Framework (25 min)

### Teaching Notes

NASA SEH Process 17 (Decision Analysis) provides the framework for structured alternative evaluation. Every major design decision should follow this process.

*[Source: NASA SEH §6.8, Process 17: Decision Analysis]*

### Trade Study Structure

A rigorous trade study has 5 elements:

1. **Decision statement**: What are we deciding? (e.g., "Should we build a new satellite or use existing data?")
2. **Alternatives**: What are the options? (minimum 3, including "do nothing")
3. **Criteria**: What matters? (performance, cost, schedule, risk, compliance)
4. **Weightings**: How important is each criterion relative to others? (normalised to sum to 1.0)
5. **Scoring**: How well does each alternative perform against each criterion?

### Weighting Methods

| Method | Description | When to Use |
|--------|-------------|-------------|
| **Pairwise comparison** | Compare criteria two at a time; count wins | Small number of criteria (<8) |
| **Swing weighting** | Assess the value of moving each criterion from worst to best | When criteria have different units |
| **Direct assignment** | Team agrees on weights through discussion | Quick, transparent, but subjective |

### Scoring Methods

| Type | Description | Example |
|------|-------------|---------|
| **Quantitative** | Numeric value normalised 0-1 | Mass: 5kg scores 0.8, 10kg scores 0.4 |
| **Qualitative** | Verbal rating mapped to numbers | "Excellent" = 1.0, "Good" = 0.75, "Fair" = 0.5, "Poor" = 0.25 |
| **Threshold** | Pass/fail gate | TRL ≥ 6 required → below threshold eliminated |

### Weighted Score Calculation

For each alternative *a* and criterion *c*:

```
Total_Score(a) = Σ [ Weight(c) × NormalisedScore(a,c) ] / Σ Weight(c)
```

Where normalised score maps the raw value to 0-1 range:
- For "higher is better": NormScore = (value - min) / (max - min)
- For "lower is better": NormScore = 1 - (value - min) / (max - min)

**Exercise:** *Practice scoring 3 lunch options using 4 criteria (taste, cost, healthiness, speed) — a non-space example to build the skill.*

---

## 2. Space vs Non-Space Alternatives (30 min)

### Teaching Notes

Before committing to building a satellite, teams must honestly evaluate whether existing solutions meet the need. This is the most important trade study in the mission lifecycle.

### Alternative Categories

| Category | Examples | Typical Strengths | Typical Weaknesses |
|----------|---------|-------------------|-------------------|
| **Existing free data** | Copernicus Sentinel-2, Landsat | Zero cost, proven, long archive | Fixed resolution/revisit, no control |
| **Commercial data purchase** | Planet, Maxar, ICEYE | High resolution, fast tasking | Ongoing cost, no ownership, data rights |
| **Aerial (drones/aircraft)** | Survey drones, P-3 Orion | Very high resolution, flexible | Limited coverage, weather dependent |
| **Ground sensors** | IoT networks, weather stations | Continuous, low cost | Point measurements only |
| **Dedicated satellite** | New CubeSat or SmallSat | Full control, custom, IP ownership | High cost, development risk, schedule |
| **Constellation** | Multiple satellites | Global coverage, short revisit | Much higher cost, operational complexity |
| **Hosted payload** | Payload on another mission | Lower cost, shared bus | Limited control, compromise orbit |

### When Space is NOT the Right Answer

Space is likely **not** justified when:
- Existing free data (Sentinel-2, Landsat) meets resolution and revisit needs
- The coverage requirement is local (drones or aircraft are cheaper)
- The data rate is very low (ground sensors with cellular backhaul suffice)
- The budget doesn't support the minimum viable satellite cost
- The technology readiness is too low for the available schedule

Space is likely **justified** when:
- Global or wide-area coverage is needed simultaneously
- Persistent monitoring is required (24/7 or very frequent revisit)
- The user needs data ownership and control over acquisition
- No existing service provides the required measurement type
- Regulatory or sovereignty requirements demand national control

### Constellation Considerations

For missions requiring global coverage or short revisit:
- Single satellite at 500 km SSO: revisit ~3-15 days depending on swath
- 4-satellite constellation: revisit ~1-3 days
- 20+ satellite constellation: revisit <6 hours
- Cost scales with learning curve: 95% for ≤5 units, 90% for ≤50

**Discussion prompt:** *For your team's mission need, which alternatives should be considered? Is there an existing service that might already meet the need?*

---

## 3. SpaceCDF Mission Trade Tool (30 min)

### Instructions

1. Navigate to **Step 2 (Concept)**
2. The tool shows input fields for the trade analysis:
   - **GSD target** (for optical missions) or leave blank for non-optical
   - **Revisit target** (days)
   - **Coverage** (global / regional / local)
   - **Latency** (hours from acquisition to user)
   - **Annual budget** (kEUR)
   - **Data ownership** (required / not required)
   - **Scheduling control** (required / not required)
3. Click **"Run Analysis"**
4. Review the scored alternatives table

### Interpreting Results

The tool returns:
- **Scored alternatives**: each rated 0-100% against weighted criteria
- **Space justified flag**: "yes" if dedicated satellite scores highest
- **Recommendation**: text explaining the ranking
- **Pros/cons per alternative**: detailed comparison

### Critical Thinking Points

The tool's recommendation is a **starting point for discussion**, not a final answer. Teams should:
- Challenge the weightings — do they reflect YOUR mission's priorities?
- Consider alternatives the tool may not include (hybrid approaches, partnerships)
- Check whether the top-scoring existing service ACTUALLY provides the specific measurement needed (e.g., Sentinel-2 doesn't do SAR)

---

## 4. Tabular Trade Studies (20 min)

### Teaching Notes

Beyond the space-vs-non-space trade, the SpaceCDF **Trade Studies** tab provides a general-purpose tabular trade tool that can be used for ANY design decision:
- Orbit selection
- Component selection
- Ground segment selection
- Architecture selection

### SpaceCDF Trade Study Builder

1. Navigate to the **Trade Studies** tab
2. Select a template (e.g., "Orbit Selection Trade") or build a custom trade
3. Define criteria with names, weights (0-1), and direction (higher/lower is better)
4. Add options (minimum 3)
5. Score each option on each criterion (numeric or qualitative: low/medium/high)
6. Click **"Run Trade"** to see ranked results with sensitivity analysis

**Exercise:** *Using the tabular trade study builder, evaluate 3 orbit options for your mission using the "Orbit Selection Trade" template. Adjust weights to reflect your mission priorities.*

---

## 5. Documenting the Decision (15 min)

### Teaching Notes

Every trade study decision must be documented with:
1. **What was decided**: the selected alternative
2. **What was considered**: all alternatives evaluated
3. **Why this was chosen**: the criteria, weightings, and scores
4. **What was rejected and why**: brief rationale for non-selected options
5. **What risks remain**: any concerns with the selected approach
6. **Who decided**: responsible person/team and date

This documentation is required at every review gate. NASA SEH Process 17 requires "an auditable record of the decision rationale."

*[Source: NASA SEH §6.8.3]*

**Exercise:** *Write a 1-paragraph decision statement for your mission trade result. Include the top 2 alternatives and why one was selected over the other.*

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Trade study structure | Criteria + weights + scoring → ranked alternatives |
| Space vs non-space | Existing services may already meet the need — check first |
| Constellation | Cost scales sub-linearly; consider for global/frequent coverage |
| Documentation | Every decision must have auditable rationale |
| Tool usage | Mission trade in Step 2; tabular trades in Trade Studies tab |
