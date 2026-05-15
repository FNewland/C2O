# Session 5.4: Final Review & Presentations


**Prerequisites:** All previous sessions (complete design through simulation)
**References:** ECSS-M-ST-10C Rev.1 section 6 (Reviews), NPR 7123.1D Appendix G, NASA SEH Rev 2 section 3.7, ECSS-E-ST-10C section 4 (Technical Dossier)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Prepare a complete design documentation package for review
2. Conduct a design review presentation with evidence-based arguments
3. Evaluate a peer team's design against gate criteria
4. Provide constructive technical feedback using a structured rubric
5. Identify lessons learned and articulate next steps for Phase B

---

## 1. Design Documentation Review
Before presenting, each team must verify that their design documentation is complete and internally consistent.

### Documentation Checklist

| Document | Source in SpaceCDF | Status Check |
|----------|-------------------|-------------|
| Mission Requirements Document (MRD) | Exports -> ECSS Documents | All requirements baselined? |
| Technical Specification (TS) | Exports -> ECSS Documents | All budgets captured? |
| Concept of Operations (ConOps) | Exports -> ECSS Documents | All phases defined? |
| Verification Plan (VP) | V&V Matrix tab | All requirements have methods? |
| Bill of Materials (BOM) | Exports -> Design Data | All equipment listed with TRL? |
| Risk Register | Worksheet 4.3 | All risks scored and mitigated? |
| Interface Matrix (N^2) | Worksheet 4.3 | Interfaces identified? Conflicts resolved? |
| Cost Estimate | Worksheet 4.4 | WBS complete? P80 computed? |
| Operations Concept | ConOps Editor | Modes, FDIR, procedures defined? |
| Sustainability Assessment | Sustainability Card | Debris compliance score? |

### Internal Consistency Checks

Before presenting, verify:

| Check | How to Verify | Common Error |
|-------|-------------|-------------|
| Mass budget closes | Dashboard mass KPI: margin > 0% | Equipment added without updating budget |
| Power budget closes | Dashboard power KPI: SA > loads in all modes | Eclipse mode power not checked |
| Link budget closes | Link Budget tool: margin >= 3 dB | Rain attenuation not included |
| Data budget closes | Data Budget: daily downlink >= daily generation | Assumed too many passes per day |
| Cost is within ceiling | Cost tab: total <= allocated budget | Forgot launch cost or operations |
| Requirements traceable | Every requirement maps to an objective | Orphan requirements (no parent objective) |
| V&V complete | Every requirement has a method assigned | "TBD" entries remaining |
| No unresolved conflicts | Dashboard: conflict count = 0 | Interface mismatches not addressed |

### SpaceCDF Document Generation

Navigate to **Exports** tab and generate all documents:
1. ECSS Documents: MRD, TS, VP, ConOps, SEMP, IRD
2. Design Data: BOM, Parametric Model Data
3. Regulatory Filings: ITU API, RSSSA, Export Assessment, COPUOS, EOL Report
4. Presentation: Summary slide data (auto-populated)

---

## 2. Presentation Structure
Each team presents a 12-minute design review followed by 5 minutes of Q&A from the peer review board.

*[Source: ECSS-M-ST-10C Rev.1 section 6; NPR 7123.1D Appendix G (Review Process)]*

### Presentation Outline
| Section | Duration | Content | Evidence |
|---------|----------|---------|----------|
| **1. Mission Need** | 2 min | Problem statement; stakeholders; objectives with MoPs | Mission Need step |
| **2. Why Space?** | 2 min | Trade study results; why space beats alternatives | Mission Trade results |
| **3. System Design** | 3 min | Architecture; orbit; key parameters; budget status | Dashboard, budgets |
| **4. Equipment & Verification** | 2 min | Key equipment; BOM summary; V&V approach; test plan | BOM, V&V Matrix |
| **5. Risk & Cost** | 2 min | Top 5 risks; cost estimate (P50/P80); schedule | Risk register, cost tab |
| **6. Operations & Lessons** | 1 min | ConOps summary; FDIR; what would you change | ConOps, simulation debrief |

### Presentation Best Practices

**Slide design:**
- One key message per slide
- Data, not prose (budgets, trade tables, not paragraphs)
- Include backup slides with detailed analyses for Q&A

**Delivery:**
- Lead with conclusions: "Our mass budget closes with 22% margin"
- Show evidence for every claim: "Link budget analysis shows 4.2 dB margin at worst case"
- Acknowledge risks honestly: "Antenna deployment is our highest risk at 12 (L3 x C4)"
- For questions you cannot answer: "Good question -- we will take that as an action item"

**Common pitfalls to avoid:**
- Reading slides verbatim
- Hiding known problems (review boards always find them)
- Presenting analysis without stating assumptions
- Spending too long on the mission description and rushing through technical results

---

## 3. Peer Review Process
Each team acts as a review board for another team. This mirrors the real design review process where an independent board evaluates the project.

### Review Board Roles

| Role | Responsibility | Key Questions to Ask |
|------|---------------|---------------------|
| **Chair** | Manages review; ensures all criteria covered | "Let's systematically check each gate criterion" |
| **Systems reviewer** | Evaluates overall architecture and budgets | "Do all budgets close? What is the minimum margin?" |
| **Technical reviewer** | Evaluates subsystem design decisions | "Why did you choose this component over alternatives?" |
| **Risk reviewer** | Evaluates risk management and V&V | "What is your highest risk? Is the mitigation adequate?" |
| **Operations reviewer** | Evaluates ConOps, ground segment, regulatory | "What happens if you lose contact for 48 hours?" |

### Gate Criteria Evaluation

The review board evaluates the presenting team against PDR-level gate criteria:

| # | Criterion | Score (0-2) | Notes |
|---|-----------|------------|-------|
| 1 | Mission need clearly justified | 0 = missing, 1 = partial, 2 = strong | Is the problem real? Is space the right answer? |
| 2 | Requirements complete and traceable | 0/1/2 | All requirements linked to objectives? Verifiable? |
| 3 | All budgets close with adequate margin | 0/1/2 | Mass, power, link, data, pointing -- all positive? |
| 4 | Equipment selected with justified trades | 0/1/2 | BOM complete? TRL adequate? Trade studies documented? |
| 5 | Interfaces defined and conflicts resolved | 0/1/2 | N^2 matrix? No unresolved conflicts? |
| 6 | V&V approach defined for all requirements | 0/1/2 | Methods assigned? Test plan outlined? |
| 7 | Risks identified with mitigations | 0/1/2 | Risk register with scores? Top risks mitigated? |
| 8 | Cost estimate with WBS and P80 | 0/1/2 | Both parametric and bottom-up? Learning curve applied? |
| 9 | ConOps and ground segment designed | 0/1/2 | Modes defined? FDIR architecture? Ground stations? |
| 10 | Sustainability compliance | 0/1/2 | Debris compliance? 25-year rule? Passivation plan? |

### Review Board Questions Bank

Standard questions for the review board to ask:

- "Why is space the right answer? What alternatives were considered?"
- "What is your mass margin? What drives it? What if the payload is 20% heavier than estimated?"
- "Walk me through your link budget at worst case. What is the minimum margin?"
- "What are your top 3 risks? What is the residual risk after mitigation?"
- "Show me your data budget. Does it close with a single ground station?"
- "What happens during a safe mode entry in eclipse? Does the thermal budget survive?"
- "Which component has the lowest TRL? What is your qualification plan?"
- "Have you started spectrum licensing? What is on the critical path?"
- "What is your single-point failure list? Which ones have you accepted?"
- "If you had 6 more months and 20% more budget, what would you change?"

---

## 4. Team Presentations
### Instructions

**Presentation Schedule:** 12 minutes presentation + 5 minutes Q&A per team.

For 4 teams: allocate 17 min x 4 = 68 min. Adjust timing based on actual number of teams. If fewer than 4 teams, allow 15 min presentation + 8 min Q&A.

**For the presenting team:**
1. Present the 6-section outline above
2. Use SpaceCDF live for demonstrations where helpful (show Dashboard, budgets)
3. Respond to board questions with evidence

**For the review board:**
1. Complete the gate criteria evaluation form on Worksheet 5.4
2. Ask at least 3 substantive questions
3. Provide a GO / NO GO / GO WITH ACTIONS recommendation
4. Document action items with responsible person and deadline

**After each presentation:**
- Chair announces the board's recommendation
- Action items are recorded
- Brief applause and transition to next team

---

## 5. Course Wrap-Up & Lessons Learned
### Individual Reflection
Each participant completes the self-assessment rubric on Worksheet 5.4, reflecting on their learning across all three weeks.

### Team Lessons Learned
Each team discusses and reports:

1. **Most challenging design decision:** What trade-off was hardest to resolve? Why?
2. **Biggest surprise:** What aspect of mission design was most different from expectations?
3. **Tool feedback:** What SpaceCDF feature was most valuable? What was missing?
4. **Process insight:** How did concurrent design change your approach to engineering?
5. **If starting over:** What would you do differently in Week 1?

### Key Takeaways from the Course
| Week | Theme | Core Lesson |
|------|-------|------------|
| **Week 1** | Requirements & Architecture | Start with the problem, not the solution. Requirements define WHAT, not HOW. |
| **Week 2** | Subsystem Design & Budgets | Engineering budgets are the language of systems engineering. Everything trades against everything. |
| **Week 3** | Integration, Verification & Operations | Building the right thing (V&V) is as important as designing it. Operations reveal what analysis cannot. |

### The Systems Engineering V-Model -- Completed

```
You started here:                          You finished here:
                                           
  Mission Need                               Mission Validated
     |                                              ^
     v                                              |
  Requirements                              Requirements Verified
     |                                              ^
     v                                              |
  System Design                             System Integrated (sim)
     |                                              ^
     v                                              |
  Subsystem Design                          Subsystem V&V Planned
     |                                              ^
     v                                              |
  Equipment Selected  ------>  Equipment Verified (BOM + compliance)
  
  Week 1-2 (left side)         Week 3 (right side)
```

*You have traversed the complete V-model: from mission need to verified, validated design.*

### Next Steps for Participants

- **SpaceCDF access** continues after the course
- **Apply the methodology** to your own missions or projects
- **Use the tool** for CDF-style studies with your team
- **Refer to the Facilitator's Book** for session plans and appendices
- **Share feedback** to improve the course for future cohorts

### Course Evaluation

Distribute the course evaluation form. Key questions:
- Which session was most valuable? Least valuable?
- What content should be added? Removed?
- How effective was the simulation day?
- Would you recommend this course to colleagues?
- What is one thing you will do differently in your engineering practice as a result?

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-M-ST-10C Rev.1 (Project Planning and Implementation) | https://ecss.nl/standard/ecss-m-st-10c-rev-1-project-planning-and-implementation/ |
| 2 | NPR 7123.1D Appendix G (Review Process) | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1D |
| 3 | NASA SEH Rev 2, section 3.7 (Technical Reviews) | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| 4 | ECSS-E-ST-10C (System Engineering) | https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Documentation | Complete package: MRD, TS, ConOps, VP, BOM, Risk Register, Cost, Regulatory |
| Consistency | All budgets must close; no unresolved conflicts; requirements fully traceable |
| Presentation | 6 sections: need, justification, design, V&V, risk+cost, operations+lessons |
| Peer review | Independent board evaluates against gate criteria; GO/NO GO/GO with actions |
| Best practices | Lead with conclusions, show evidence, acknowledge risks, answer directly |
| V-model | Course traverses full V: needs -> requirements -> design -> V&V -> validation |
| Lessons learned | Document what worked, what failed, and what to change -- this is the real output |
