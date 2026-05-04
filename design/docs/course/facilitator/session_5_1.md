# Session 5.1: Gate Review Preparation

**Duration:** 2 hours
**Prerequisites:** Days 1-4 complete (full design cycle)
**References:** ECSS-M-ST-10C Rev.1 §6; NASA SEH §3.7; NPR 7123.1D Appendix G

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Identify the exit criteria for Mission Concept Review (MCR)
2. Prepare evidence for each criterion from the design data
3. Resolve failing criteria using the "Go fix" navigation
4. Conduct a peer review simulating a gate review board
5. Document action items and decisions from the review

---

## 1. Purpose of Gate Reviews (15 min)

### Teaching Notes

*[Source: ECSS-M-ST-10C §6; NASA SEH §3.7]*

Gate reviews serve three purposes:
1. **Technical readiness:** Is the design mature enough to proceed?
2. **Programmatic readiness:** Are budget, schedule, and resources in place?
3. **Risk assessment:** Are risks identified, assessed, and mitigated?

The review board evaluates evidence against predefined **exit criteria**. The outcome is:
- **GO:** Proceed to next phase
- **GO with actions:** Proceed but specific items must be resolved within a deadline
- **NO GO:** Cannot proceed; rework required

### Review Sequence for a CubeSat Mission

| Review | Phase Exit | Key Question |
|--------|-----------|-------------|
| **MCR** | Pre-A -> A | Is the mission need justified? Is space the right answer? |
| **SRR** | A -> B | Are requirements complete, consistent, and traceable? |
| **PDR** | B -> C | Does the preliminary design meet requirements with margin? |
| **CDR** | C -> D | Is the design complete and ready for build? |
| **TRR** | Pre-test | Is the system ready for formal testing? |
| **FRR** | Pre-launch | Is everything ready for launch? |

For a typical CubeSat project, MCR and SRR may be combined, and PDR is the most critical gate (it's where you commit to building hardware).

---

## 2. MCR Exit Criteria (30 min)

### Teaching Notes

SpaceCDF evaluates MCR criteria automatically where possible, with manual review for subjective criteria.

### MCR Criteria Table

| # | Criterion | Priority | How Evaluated | Evidence |
|---|-----------|----------|---------------|----------|
| EC-01 | Mission need clearly defined and justified | Must pass | Problem statement not empty | Mission Need step |
| EC-02 | Key stakeholders identified | Must pass | >= 1 stakeholder defined | Stakeholder list |
| EC-03 | Objectives defined with measurable criteria | Must pass | >= 1 primary objective with criterion | Objectives with MoPs |
| EC-04 | Alternatives considered including non-space | Must pass | >= 2 alternatives, including non-space | Mission trade results |
| EC-05 | Selected concept justified | Must pass | Alternative selected with rationale | Decision rationale |
| EC-06 | Preliminary ConOps documented | Should pass | ConOps summary not empty | ConOps tab |
| EC-07 | Feasible system concept identified | Must pass | Mass margin > -50% | Design run results |
| EC-08 | Mission sustainable (debris, casualty) | Should pass | Debris compliance > 50/100 | Sustainability card |
| EC-09 | Requirements traceable to objectives | Should pass | Manual review | Traceability matrix |
| EC-10 | Interface conflicts identified and managed | Should pass | Manual review | Interface matrix |

### SpaceCDF Gate Review Features

1. **Auto-evaluation:** Criteria EC-01 through EC-08 are automatically evaluated from the design state
2. **"Go fix" navigation:** Each failing criterion has a button that navigates to the relevant step/tab
3. **Pass/Fail/Manual indicators:** Green (pass), Red (fail), Blue (manual review needed)
4. **Readiness indicator:** Big checkmark/cross showing overall MCR readiness

### Resolving Failures

For each failing criterion:
1. Read the **evidence text** (what the tool found)
2. Click **"Go fix"** to navigate to the relevant tool
3. Address the issue (e.g., add stakeholders, complete alternatives analysis)
4. Return to Gate Review to verify the criterion now passes

---

## 3. Preparing the Review Package (25 min)

### Teaching Notes

A gate review presentation should cover:

### MCR Presentation Outline

1. **Mission overview** (5 min)
   - Problem statement and justification
   - Key stakeholders and their needs
   - Mission objectives with success criteria

2. **Alternatives analysis** (10 min)
   - Space vs non-space trade results
   - Why the selected concept is preferred
   - What was considered and rejected (with rationale)

3. **Concept description** (10 min)
   - Mission architecture (space, ground, user segments)
   - ConOps (phases, modes, data flow)
   - Preliminary orbit selection and rationale

4. **Feasibility assessment** (10 min)
   - Preliminary mass, power, cost budgets (with margins)
   - Key technology risks (TRL assessment)
   - Schedule overview and milestones

5. **Risk register** (5 min)
   - Top 5 risks with scores and mitigation plans

6. **Action items and recommendations** (5 min)

### Evidence Checklist

| Evidence | Source in SpaceCDF |
|----------|-------------------|
| Problem statement | Step 1: Mission Need |
| Stakeholder matrix | Step 1: Mission Need |
| Objectives with criteria | Step 1: Mission Need |
| Mission trade results | Step 2: Concept -> Mission Trade |
| ConOps architecture | ConOps tab |
| Mass/power/cost budgets | Dashboard |
| Pointing/data budgets | Dashboard budget cards |
| Risk register | Worksheet 4.3 |
| V&V matrix (preliminary) | V&V Matrix tab |
| Requirements list | Requirements tab |

---

## 4. Gate Review Simulation (35 min)

### Instructions

Each team conducts a simulated MCR:

1. **Preparation** (10 min): Review all gate criteria in the **Gate Review** tab. Fix any RED criteria.
2. **Presentation** (15 min): Present your mission design to another team (who acts as the review board). Cover the MCR outline above.
3. **Board deliberation** (5 min): The review board asks questions, identifies concerns, and provides a GO/NO GO/GO with actions recommendation.
4. **Action items** (5 min): Document any actions from the board.

### Review Board Guidance

As a review board member, ask:
- "Why is space the right answer? What alternatives were considered?"
- "How confident are you in the mass budget? What's the margin?"
- "What are the top risks? How will they be mitigated?"
- "Are all requirements traceable to an objective?"
- "What's your plan for debris compliance?"

---

## 5. Post-Review Actions (15 min)

### Teaching Notes

After the review:
1. **Record all action items** with responsible person, deadline, and acceptance criteria
2. **Update the risk register** if new risks were identified
3. **Document the decision** (GO/NO GO/GO with actions) and rationale
4. **Archive the review package** (SpaceCDF exports: MRD, VP, ConOps)

**Exercise:** Use SpaceCDF's **Changes** tab to review the audit trail of all design decisions made during the week.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Gate reviews | GO/NO GO decision based on exit criteria evidence |
| MCR criteria | Mission need, stakeholders, objectives, alternatives, feasibility |
| Auto-evaluation | SpaceCDF evaluates 8/10 criteria automatically |
| "Go fix" | Navigate directly from failing criterion to the fix location |
| Presentation | 6-section structure: need, alternatives, concept, feasibility, risk, actions |
| Documentation | Archive review package; record decisions and action items |
