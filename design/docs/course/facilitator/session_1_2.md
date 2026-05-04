# Session 1.2: Mission Need & Stakeholder Analysis

**Duration:** 2 hours
**Prerequisites:** Session 1.1
**References:** NASA SEH §4.1, NPR 7123.1D §3.2.1, ECSS-E-ST-10C §5.1

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Write a clear problem statement that defines the need without prescribing a solution
2. Identify and categorise mission stakeholders
3. Define mission objectives with measurable success criteria
4. Distinguish between Measures of Effectiveness, Performance, and TPMs
5. Use SpaceCDF Step 1 to capture mission need

---

## 1. The Problem Statement (25 min)

### Teaching Notes

NASA SEH §4.1.1: *"Clearly define the problem before solving it."*

The most common mistake in mission design is jumping to a solution ("we need a 6U CubeSat at 500 km") before articulating the problem ("agricultural monitoring in sub-Saharan Africa requires 10m resolution multispectral imagery every 5 days").

### Structure of a Good Problem Statement

A problem statement should answer:

1. **What is the problem?** -- The capability gap
2. **Who is affected?** -- Stakeholders and end users
3. **What is the impact?** -- Consequence of not solving it
4. **What constraints exist?** -- Budget, schedule, political, regulatory

**Example -- GOOD:**
> "Agricultural monitoring agencies in sub-Saharan Africa lack timely, affordable access to multispectral imagery at sufficient resolution (<=10m) and revisit rate (<=5 days) to support crop yield prediction and food security planning. Current Sentinel-2 data has 10m resolution but only 5-day revisit at the equator, and cloud cover reduces usable observations to ~60%. The consequence is delayed or inaccurate crop assessments affecting food aid allocation for 300M people. Budget constraint: <?10M total mission cost."

**Example -- BAD:**
> "We need a 6U CubeSat with a multispectral imager at 500 km SSO."

The bad example is a solution statement, not a problem statement. It skips the "why" entirely.

### Key Principle: WHAT Not HOW

*[Source: NASA SEH Appendix C -- How to Write a Good Requirement]*

At the mission need level, everything should describe **WHAT** is needed, not **HOW** to achieve it:

| WHAT (good) | HOW (bad) |
|-------------|-----------|
| "10m resolution imagery" | "Use a 15cm aperture telescope" |
| "Daily revisit at equator" | "Deploy a Walker delta constellation" |
| "Data within 6 hours of acquisition" | "Use X-band downlink at 150 Mbps" |
| "Total cost under ?10M" | "Use COTS components exclusively" |

**Discussion prompt:** *Why is it harmful to specify HOW at this stage? What options does it close off?*

---

## 2. Stakeholder Identification (20 min)

### Teaching Notes

NASA SEH §4.1.2 defines stakeholders as all parties who have a legitimate interest in the system throughout its lifecycle. For space missions, typical stakeholders include:

### Stakeholder Categories

| Category | Examples | Typical Needs |
|----------|---------|---------------|
| **End Users** | Scientists, farmers, shipping companies, military | Data quality, latency, format, accessibility |
| **Operators** | Mission control, ground station staff | Operability, automation, staffing level |
| **Sponsors/Funders** | Space agency, university, commercial investor | Cost, schedule, return on investment |
| **Regulatory** | ITU, national spectrum authority, export control | Compliance, licensing, debris mitigation |
| **Launch Provider** | SpaceX, Rocket Lab, Arianespace | Mass, volume, interfaces, schedule |
| **Ground Segment** | KSAT, SSC, SatNOGS, own stations | Frequency bands, contact time, data volume |
| **Data Consumers** | Archives, APIs, partner agencies | Data format, metadata, distribution method |
| **General Public** | Taxpayers (for government missions) | Value for money, transparency, societal benefit |
| **Environment** | Earth's orbital environment | Debris mitigation, spectrum cleanliness |

### Stakeholder Analysis Matrix

For each stakeholder, capture:
- **Name/Role**: Who are they?
- **Needs**: What do they require from the mission?
- **Constraints**: What limitations do they impose?
- **Priority**: Primary (must satisfy) vs secondary (should satisfy)
- **Influence**: How much power do they have over the mission?

**Exercise:** *Participants fill in the stakeholder matrix for their sample mission in the Learner's Workbook (Worksheet 1.2, Part A).*

---

## 3. Mission Objectives (30 min)

### Teaching Notes

Objectives translate the problem statement into specific, testable goals. Each objective should have:

1. **Text**: Clear statement of what the mission will achieve
2. **Priority**: Primary (mission fails without it) or secondary (desirable but not essential)
3. **Measurable criterion**: How you know the objective is met -- with a number and a unit
4. **Type**: Observation, communication, navigation, science, technology demonstration

### MoE / MoP / TPM Hierarchy

*[Source: NASA SEH §4.1.4, §4.2.4, §6.7.3 -- verified, see Appendix N]*

| Measure | What It Measures | Example | Set By |
|---------|-----------------|---------|--------|
| **MoE** (Measure of Effectiveness) | How well the system satisfies operational need | "% of crop assessments delivered within 5 days" | Users/stakeholders |
| **MoP** (Measure of Performance) | Technical performance of the system | "GSD <= 10m at nadir" | Systems engineer |
| **TPM** (Technical Performance Measure) | Design parameter tracked over time | "Current mass estimate vs allocation" | Design team |

The hierarchy flows:
```
Stakeholder Need -> MoE -> Objective -> MoP -> Requirement -> TPM
```

### Writing Good Objectives

| Good Objective | Why It's Good |
|---------------|--------------|
| "Provide 10m GSD multispectral imagery with 4+ bands for the target region between 30°S-30°N, with <=5 day revisit and <=24h data latency" | Specific, measurable (10m, 4 bands, 5 days, 24h), relevant to agriculture, achievable with CubeSat |
| "Achieve 99.5% AIS ship detection rate in the North Atlantic within 30 minutes of ship transmission" | Specific (AIS, North Atlantic), measurable (99.5%, 30 min), relevant to maritime safety |

| Bad Objective | Why It's Bad |
|--------------|-------------|
| "Take pictures from space" | Not specific, not measurable |
| "Build a 3U CubeSat" | This is a solution, not an objective |
| "Demonstrate new technology" | What technology? What does "demonstrate" mean? |

**Exercise:** *Participants write 2-3 objectives for their sample mission with measurable criteria. Peer review in pairs using the checklist in Worksheet 1.2, Part B.*

---

## 4. From Need to Design: The Flow (15 min)

### Teaching Notes

Show how the mission need flows through to design decisions -- but the need itself does NOT prescribe design:

```
Problem: "Need 10m imagery, 5-day revisit, <?10M"
   ? (objectives)
Objective: "Provide 10m GSD multispectral imagery..."
   ? (mission trade -- is space the right answer?)
Decision: "Yes, dedicated CubeSat -- existing services don't meet revisit need"
   ? (requirements)
Requirement: "The system shall achieve GSD <= 10m"
   ? (orbit trade)
Design choice: "SSO 500 km gives 10m GSD with 15cm aperture"
   ? (subsystem design)
Equipment: "Selected: XYZ Telescope, 15cm aperture, 1.5 kg, 8W"
```

At each level, the tool helps with decision support -- but the team decides.

---

## 5. SpaceCDF Tool Exercise (30 min)

### Instructions

1. Open SpaceCDF
2. In **Step 1 (Mission Need)**, enter:
   - A problem statement (2-3 sentences)
   - At least 2 stakeholders with roles and needs
   - At least 2 objectives with measurable criteria, one primary and one secondary
3. Observe: Does the tool suggest a mission type from your objective text?
4. Navigate to **Step 2 (Concept)** -- we'll use this in the next session

**Checkpoint:** Each team should have a problem statement, 2+ stakeholders, and 2+ objectives entered before moving on.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Problem statement | Defines WHAT is needed, not HOW to solve it |
| Stakeholders | Identify all parties with legitimate interest; capture needs and constraints |
| Objectives | Must be specific, measurable, and traceable to stakeholder needs |
| MoE/MoP/TPM | Hierarchy from operational effectiveness to tracked design parameters |
| Flow | Need -> objectives -> trade -> requirements -> design -> equipment |
