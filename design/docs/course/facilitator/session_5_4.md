# Session 5.4: Design Optimisation & Final Presentations

**Duration:** 2 hours
**Prerequisites:** All previous sessions (complete design)
**References:** NASA SEH §6.8 (Decision Analysis); multi-objective optimisation theory

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Run multi-objective optimisation to explore the design space
2. Interpret a Pareto front and make informed trade-offs
3. Perform sensitivity analysis to identify dominant parameters
4. Present a complete mission design with evidence and rationale
5. Document lessons learned from the design process

---

## 1. Design Optimisation (30 min)

### Teaching Notes

### Why Optimise?

After the initial design converges, the team has a feasible design but not necessarily the **best** design. Optimisation explores the trade-off space systematically.

### Multi-Objective Optimisation

Real design has competing objectives:
- Minimise mass (lighter = cheaper launch, but less capability)
- Minimise cost (cheaper but may sacrifice TRL or performance)
- Maximise link margin (better comms but heavier/more power)
- Maximise reliability (more redundancy but more mass)

**No single design is best on all objectives.** Instead, there's a **Pareto front** of non-dominated designs — where improving one objective necessarily worsens another.

### SpaceCDF Optimizer

Navigate to the **Optimizer** tab (in the Analysis group):

**Single-objective mode:**
- Select one objective (e.g., "Minimise dry mass")
- Select variables to vary (e.g., orbit altitude, payload duty cycle)
- Set bounds per variable
- Run → returns the best design point for that objective

**Pareto mode (NSGA-II):**
- Select 2+ objectives (e.g., minimise mass AND minimise cost)
- Same variable selection
- Run → returns a set of Pareto-optimal designs
- Each point on the front represents a different trade-off between objectives

### Interpreting Results

The Pareto front shows the "efficient frontier" — all designs where you can't improve one objective without worsening another. The team must then **choose** which point on the front to use, based on mission priorities.

**Discussion prompt:** *Looking at the Pareto front between mass and cost — where would you choose? What non-quantitative factors influence this choice?*

---

## 2. Sensitivity Analysis (20 min)

### Teaching Notes

### Morris Screening

SpaceCDF provides Morris screening sensitivity analysis (POST /api/optimize/sensitivity):
- Perturbs each design variable independently
- Measures the **elementary effect** (change in objective per unit change in variable)
- Reports **μ**** (mean of absolute effects) — importance ranking
- Reports **σ** (standard deviation of effects) — linearity indicator

### Interpreting Sensitivity Results

| Variable | μ* | σ | Interpretation |
|----------|-----|---|---------------|
| High μ*, low σ | Important, linear | **Key driver** — small change has proportional effect |
| High μ*, high σ | Important, non-linear | **Critical** — effect depends on other variables (interactions) |
| Low μ*, low σ | Unimportant | **Freeze** — don't spend effort optimising this |
| Low μ*, high σ | Seems unimportant on average | **Investigate** — may be important in specific regions |

### What to Do With Results

1. **Focus trade studies** on high-μ* variables (they drive the design)
2. **Freeze** low-μ* variables at nominal values (save effort)
3. **Add constraints** if high-μ* variables hit physical limits
4. **Report** which parameters most influence the final design (for review boards)

---

## 3. Final Design Freeze (15 min)

### Teaching Notes

After optimisation and sensitivity analysis, the team selects a final design point. This involves:

1. **Review the Pareto front** — identify the region that best balances objectives
2. **Check all budgets** — mass, power, cost, link, pointing, data all have positive margin
3. **Check all constraints** — debris compliance, CDS compliance, V&V feasibility
4. **Resolve remaining conflicts** — any red items in Interface Matrix?
5. **Freeze the design** — create a snapshot (Snapshots tab) as the "baseline"

### Document Generation

Generate all ECSS documents from the frozen design:
1. **Exports** tab → ECSS Documents:
   - MRD (Mission Requirements Document)
   - TS (Technical Specification)
   - VP (Verification Plan)
   - ConOps
2. **Exports** tab → Regulatory:
   - All applicable filings (ITU, RSSSA, export, COPUOS, EOL)
3. **Exports** tab → Design Data:
   - BOM (Bill of Materials from equipment selections)
   - Parametric model data (for traceability)

---

## 4. Final Team Presentations (45 min)

### Instructions

Each team presents their complete mission design (10-12 minutes per team + 3 minutes Q&A):

### Presentation Structure

1. **Mission Need** (2 min)
   - Problem statement
   - Key stakeholders
   - Primary objective with measurable success criterion

2. **Why Space?** (2 min)
   - Trade study results
   - Why selected concept is preferred
   - Constellation vs single satellite rationale (if applicable)

3. **System Design** (3 min)
   - Architecture (space + ground + user segments)
   - Key parameters: orbit, mass, power, cost, lifetime
   - Budget status: all margins positive?
   - Key equipment selected (payload, AOCS, comms)

4. **Verification Approach** (2 min)
   - V&V matrix summary (how many A/T/R/I)
   - Environmental test plan
   - Key risks and mitigations

5. **Regulatory & Launch** (2 min)
   - Licensing approach (amateur/experimental/commercial)
   - Launch provider selected
   - Schedule overview with regulatory milestones

6. **Lessons Learned** (1 min)
   - What would you do differently?
   - What was the most challenging decision?
   - What does the design need next?

### Peer Review Criteria

| Criterion | Points | Description |
|-----------|--------|-------------|
| Problem clearly defined | /10 | Is the need justified? Is it WHAT not HOW? |
| Design feasibility | /20 | Do all budgets close? Margins positive? |
| Trade study rigour | /15 | Were alternatives properly evaluated? |
| Requirements quality | /15 | SMART? Traceable? Verifiable? |
| Completeness | /20 | All subsystems sized? Equipment selected? V&V planned? |
| Communication | /10 | Clear, concise, well-structured presentation |
| Risk awareness | /10 | Top risks identified with mitigations? |

---

## 5. Course Wrap-Up (10 min)

### Teaching Notes

### Key Takeaways from the Course

1. **Start with the problem**, not the solution
2. **Requirements drive design**, not the other way around
3. **Engineering budgets** are the language of systems engineering
4. **Concurrent design** resolves conflicts in real-time
5. **Trade studies** require rigour: criteria, weights, scores, rationale
6. **Verification** must be planned alongside design (not an afterthought)
7. **Regulatory** is on the critical path — start filings early
8. **Iteration** is normal and expected — the design will change

### Next Steps for Participants

- SpaceCDF access continues after the course (Facilitator's Book provided)
- Apply the methodology to your own missions
- Use the tool for CDF-style studies with your team
- Refer to the Verification Appendix for source material citations

### Feedback & Evaluation

Course evaluation form. Key questions:
- Which session was most valuable?
- Which was least clear?
- What would you add or remove?
- Would you recommend this to colleagues?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Optimisation | Pareto front shows efficient trade-offs; team chooses based on priorities |
| Sensitivity | Morris μ* ranks variable importance; focus effort on high-μ* parameters |
| Design freeze | All budgets positive, conflicts resolved, snapshot created |
| Documentation | Generate all ECSS + regulatory + BOM from SpaceCDF before review |
| Presentation | 6 sections: need, justification, design, V&V, regulatory, lessons |
| Course | Problem → Requirements → Design → Verify → Review (the V-model in action) |
