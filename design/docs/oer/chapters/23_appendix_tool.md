# Appendix A — About the SpaceCDF Tool

The numerical examples in this book were computed with SpaceCDF, an open-source concurrent-design tool for small spacecraft. This appendix describes it briefly and neutrally so that a reader can understand what produced the numbers, and reproduce or extend them. It is released under the MIT licence; the source code, the mission descriptors used for the examples in this book and the figure-generation scripts are available at `<repository URL>`. Nothing in Parts I–III depends on the tool: every method in the book can be applied with a spreadsheet, and the problems never require it.

## A.1 Positions and design agents

Two distinct concepts run through a concurrent-design study and are sometimes conflated. Disentangling them is essential before the first design loop.

A **position** is a *human role* assigned to a person at a console in a Concurrent Design Facility — the Power Engineer, the AOCS Engineer, the Mission Analyst and so on. The tool defines the sixteen positions of Chapter 1 Table 1.4, each with scoped editing rights over a subset of the design parameters; Part IV gives a briefing for each.

A **design agent** is a *computational solver* that runs in the background and converges a particular subsystem or analysis. The agents are grouped in two tiers:

| Tier | Purpose | Agents |
|---|---|---|
| Tier 1 — Parametric sizing | Compute the design point of one subsystem from inputs supplied by the others | orbit · link · data · power · thermal · AOCS · propulsion · mass · structure |
| Tier 2 — Cross-system analysis | Score, check or audit the converged design | cost · risk · reliability · debris · radiation · sustainability · volume · systems · conflicts · community · TRL |

The Tier 1 agents implement the sizing chains of Chapters 7–12 — the orbit agent the period, eclipse and pass geometry of Chapter 7, the power agent the array and battery chain of Chapter 9, the link agent the budget of Chapter 11, and so on — using the same equations and constants as the text. The Tier 2 agents implement the checks of Chapters 3, 8 and 13–16: the margin schedule of Table 8.3, the debris rules, the TRL roll-up, the cost estimate and the risk register.

Each agent publishes three things to the shared design state when it runs: its **parameters** (numbers with units, margin and confidence), its **rationale** (a short paragraph of reasoning in the terms of the relevant chapter) and a set of **assumptions** that downstream agents and reviewers can interrogate. Several agents also emit structured intermediates — the orbit agent a Δv breakdown, the link agent a full waterfall, the thermal agent hot- and cold-case node temperatures, the reliability agent a FMECA — and the exports surface these as tables and figures alongside the bare numbers.

## A.2 The design loop and the human–agent handover

A design loop runs every agent once, in dependency order, from the current design state. Because each agent reads the others' outputs, several loops are needed before the state stops changing; this is the computational analogue of the design iterations described in Chapter 1 §1.1.

When a human position changes a value, that parameter becomes *sticky* in the design state and the agents do not overwrite it in subsequent loops. This is the formal handover between the human operator and the computational solver, and it is the reason a concurrent-design study converges quickly: the agents do the iterative arithmetic while the positions do the engineering judgement. A sticky value is also a recorded decision, with an owner, which is what a reviewer will ask for.

## A.3 Reviews and exports

A review gate is not merely a meeting. It is a document set whose existence and contents are agreed in advance, whose generation is traceable to a converged design state, and whose acceptance moves the project from one lifecycle phase to the next (Chapter 1 Table 1.3; Chapter 16 §16.5–§16.6). The tool treats each gate as the anchor of an export bundle: at each gate it exports a design-review pack containing the budgets with their margins, the orbit and architecture figures, the compliance matrix, the equipment list, the TRL roll-up, the risk matrix, the cost S-curve and the work-breakdown structure, with the contents growing from concept review to critical design review as the chapters of Parts I–III would lead one to expect — trade-study records and the verification matrix from preliminary design review onward, the test plan and qualification status at critical design review.

In addition to the review packs the tool generates a family of data item descriptions in editable form: the mission requirements document, concept of operations, verification plan, systems engineering management plan, risk management plan, interface requirements document, test plan and bill of materials. Specialist reports cover the thermal analysis, the end-of-life deorbit plan, the remote-sensing licence application and the verification test programme. The figures in those exports are drawn by the same scripts, with the same conventions, as the figures in this book, so that a reader who has met a link waterfall in Chapter 11 will recognise the one in an exported review pack.

## A.4 Reproducing the examples in this book

Each running example (EOSat-3U and UniSat-1) is described by a mission descriptor file distributed with the tool. Running the design loop on a descriptor reproduces the budgets quoted in the corresponding chapters; the worked examples in the text then show the same numbers derived by hand from the equations of Parts I–III and Part V, which is the cross-method check that Part V §V.16 recommends for any design review. If an agent is updated and a worked-example number changes, the text can be checked against the tool's output and corrected in one place.
