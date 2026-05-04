# SpaceCDF Mission Design Course — 40-Hour Programme

## Course Title
**Collaborative Space Mission Design: From Problem to Flight-Ready CubeSat**

## Audience
Engineers, scientists, and project managers participating in concurrent
design facility (CDF) studies. No prior spacecraft design experience required
but engineering background assumed.

## Structure
- **40 contact hours** over 5 days (8 hours/day) or 10 half-days
- **Facilitator's Book**: Complete reference with all content, solutions, diagrams
- **Learner's Workbook**: Condensed content with worksheets for tool exercises

## Reference Documents
- NASA/SP-2016-6105 Rev 2 (Systems Engineering Handbook)
- NPR 7123.1D (NASA SE Processes)
- ECSS-E-ST-10C Rev.1 (Space Engineering General Requirements)
- ECSS-M-ST-10C Rev.1 (Project Management)
- ECSS-E-ST-10-02C Rev.1 (Verification)
- Wertz et al., Space Mission Engineering: The New SMAD (2011)
- Larson & Wertz, Space Mission Analysis and Design (SMAD4)
- Cal Poly CubeSat Design Specification Rev 14.1
- ITU Radio Regulations
- ECSS-U-AS-10C Rev.2 (Space Debris Mitigation)

---

## Day 1: Mission Definition & Concept (8 hours)

### Session 1.1: Introduction to Space Mission Design (2 hrs)
- What is a Concurrent Design Facility?
- The System-V model (NASA SEH Ch. 2-3)
- The 17 SE processes (NPR 7123.1)
- NASA/ECSS lifecycle phases and review gates
- Role of each CDF position
- **Exercise**: Map the 17 processes to the SpaceCDF tool

### Session 1.2: Mission Need & Stakeholder Analysis (2 hrs)
- NASA SEH Process 1: Stakeholder Expectations Definition
- Problem statement writing (NASA SEH §4.1)
- Stakeholder identification and needs elicitation
- Objective definition with measurable success criteria
- MoE, MoP, TPM hierarchy
- **Exercise**: Define mission need for a sample problem (using SpaceCDF Step 1)
- **Worksheet**: Stakeholder matrix, objective hierarchy

### Session 1.3: Mission Trade Analysis (2 hrs)
- NASA SEH Process 17: Decision Analysis
- Space vs non-space alternatives
- Trade study methodology: criteria, weightings, scoring
- Existing data services (Copernicus, Planet, Spire)
- When NOT to build a satellite
- **Exercise**: Run mission trade in SpaceCDF (Step 2)
- **Worksheet**: Trade study matrix with scoring

### Session 1.4: Concept of Operations (2 hrs)
- NASA SEH Appendix S: ConOps structure
- Mission architecture: space, ground, user segments
- Mission phases (LEOP → commissioning → nominal → disposal)
- Operational modes and duty cycling
- Data flow pipeline design
- Ground segment architecture options
- **Exercise**: Build ConOps in SpaceCDF
- **Worksheet**: ConOps outline per Appendix S

---

## Day 2: Requirements & Functions (8 hours)

### Session 2.1: Requirements Engineering (2 hrs)
- NASA SEH Process 2: Technical Requirements Definition
- SMART requirements (Specific, Measurable, Achievable, Relevant, Traceable)
- WHAT not HOW: requirements vs design choices
- Requirement hierarchy: mission → system → subsystem
- NASA SEH Appendix C: How to Write a Good Requirement
- **Exercise**: Generate requirements from objectives in SpaceCDF
- **Worksheet**: Requirements quality checklist (Appendix C)

### Session 2.2: Functional Decomposition (2 hrs)
- NASA SEH Process 3: Logical Decomposition
- Function trees: objective → function → subfunction
- Allocation to subsystems (system boundary definition)
- Derived requirements from functions
- Performance criteria definition
- **Exercise**: Build function tree in SpaceCDF
- **Worksheet**: Function-to-requirement traceability matrix

### Session 2.3: Interface Management (2 hrs)
- NASA SEH Process 12: Interface Management
- ECSS-E-ST-10-24C: Interface requirements
- N² interface matrix methodology
- Interface types: mechanical, electrical, thermal, data, RF, optical
- Conflict identification and resolution
- **Exercise**: Review interface matrix in SpaceCDF
- **Worksheet**: Interface specification for 2 subsystem pairs

### Session 2.4: Design Budgets Introduction (2 hrs)
- Mass budget methodology (ECSS-E-HB-10-02A)
- Power budget methodology (ECSS-E-ST-20C)
- Margin philosophy by project phase
- Budget roll-up: component → subsystem → system
- Cost estimation approaches (parametric, analogy, bottom-up)
- **Exercise**: Review parametric budgets in SpaceCDF dashboard
- **Worksheet**: Mass budget template with margin policy

---

## Day 3: Subsystem Design (8 hours)

### Session 3.1: Orbit Design & Selection (2 hrs)
- Orbit mechanics fundamentals (Keplerian elements, perturbations)
- LEO/SSO/MEO/GEO/HEO trade-offs
- Coverage and revisit analysis
- Orbital lifetime and debris compliance (ECSS-U-AS-10C)
- Eclipse fraction and power implications
- **Exercise**: Run orbit trade in SpaceCDF
- **Worksheet**: Orbit selection trade matrix

### Session 3.2: Payload & Communications (2 hrs)
- Optical payload sizing (GSD → aperture → mass → power)
- RF payload sizing (link budget → antenna → power)
- SAR fundamentals (resolution → antenna area → power)
- Link budget methodology (ECSS-E-ST-50-05C)
- Frequency band selection and licensing
- Amateur vs experimental vs commercial licensing
- **Exercise**: Configure payload and review link budget
- **Worksheet**: Link budget calculation sheet

### Session 3.3: Power, AOCS, Thermal (2 hrs)
- EPS architecture (solar array, battery, regulation)
- Power budget by operational mode with duty cycling
- Attitude control: magnetorquers vs reaction wheels vs star trackers
- Pointing budget (RSS error tree)
- Thermal control: passive vs active, radiator sizing
- **Exercise**: Review power/AOCS/thermal outputs in SpaceCDF
- **Worksheet**: Power mode budget table

### Session 3.4: Structure, Propulsion, Data Handling (2 hrs)
- CubeSat Design Specification (CDS Rev 14.1)
- Structural design: launch loads, natural frequency, margin of safety
- Propulsion options: cold gas, electric, chemical
- Delta-V budget allocation
- OBC architecture, data storage, flight software
- PC/104 bus standard
- **Exercise**: Select equipment in SpaceCDF browser
- **Worksheet**: Component selection trade study

---

## Day 4: Integration & Verification (8 hours)

### Session 4.1: Equipment Selection & Integration (2 hrs)
- Component selection methodology (trade studies)
- RF chain compatibility (transponder + antenna band matching)
- Power bus compatibility (voltage, switched lines)
- Volume and mass fit verification
- Harness and cabling design
- **Exercise**: Complete equipment selection in SpaceCDF
- **Worksheet**: Equipment compatibility checklist

### Session 4.2: Verification & Validation Planning (2 hrs)
- NASA SEH Processes 7-8: Verification & Validation
- ECSS-E-ST-10-02C: Verification methods (ATRI)
- Verification matrix structure
- Test levels: unit → subsystem → system → acceptance → qual
- Environmental testing (vibration, thermal-vac, EMC)
- **Exercise**: Review compliance matrix in SpaceCDF
- **Worksheet**: V&V matrix for 10 key requirements

### Session 4.3: Risk Management (2 hrs)
- ECSS-M-ST-80C: Risk management process
- Risk identification, assessment (5×5 matrix), mitigation
- FMECA methodology (ECSS-Q-ST-30-02C)
- Single-point failure analysis
- Technical Performance Measures (TPMs)
- **Exercise**: Review risk scores and reliability in SpaceCDF
- **Worksheet**: Risk register for top 5 risks

### Session 4.4: Cost & Schedule (2 hrs)
- Cost estimation: parametric (SSCM, COMPACT), analogy, bottom-up
- WBS structure (NPR 7120.5)
- CubeSat cost drivers and fractions
- Schedule estimation and critical path
- Learning curve effects for constellations
- **Exercise**: Review cost breakdown and run optimizer
- **Worksheet**: Cost estimate by WBS element

---

## Day 5: Design Review & Regulatory (8 hours)

### Session 5.1: Gate Review Preparation (2 hrs)
- ECSS-M-ST-10C: Review gate structure
- MCR/SRR/PDR/CDR exit criteria
- Design review presentation structure
- Action item management
- **Exercise**: Run gate review in SpaceCDF, resolve action items
- **Worksheet**: MCR presentation outline

### Session 5.2: Regulatory & Licensing (2 hrs)
- Frequency licensing (ITU, IARU, national)
- ITU filing process (API → coordination → notification)
- Canadian RSSSA for remote sensing
- Export control (ITAR/EAR/CGP)
- UN Registration Convention (COPUOS)
- Space debris regulations (25yr/5yr rules)
- **Exercise**: Generate regulatory filings in SpaceCDF
- **Worksheet**: Licensing decision tree

### Session 5.3: Launch Integration (2 hrs)
- Launch providers and pricing
- Deployer standards (ISIPOD, EXOpod, CSD)
- Launch ICD requirements (mechanical, electrical, environmental)
- Separation switches and inhibits
- Environmental test specification derivation
- **Exercise**: Select launch provider, review ICD requirements
- **Worksheet**: Launch ICD compliance checklist

### Session 5.4: Design Optimisation & Final Review (2 hrs)
- Multi-objective optimisation (Pareto concepts)
- Sensitivity analysis (Morris screening)
- Design iteration and convergence
- Final design review presentation
- Lessons learned
- **Exercise**: Run optimizer, review Pareto front, select final design
- **Final Exercise**: Each team presents their complete mission design

---

## Assessment
- Day 1-4: Worksheets completed in class (formative)
- Day 5: Team presentation of complete mission design (summative)
- Post-course: Access to SpaceCDF tool and Facilitator's Book

## Per-Position Deep Dives (Appendices)

### Appendix A: Systems Engineer
- Budget management, margin policy, trade study leadership
- Cross-domain conflict resolution
- Gate review preparation and exit criteria evaluation

### Appendix B: Mission Analyst
- Orbit mechanics, coverage analysis, constellation design
- Ground station selection, contact time analysis
- Lighting conditions, eclipse analysis

### Appendix C: Payload Engineer
- Optical/RF/SAR payload sizing
- Payload data rates and storage requirements
- Instrument calibration and performance verification

### Appendix D: Power Engineer
- Solar array sizing (body-mounted vs deployable)
- Battery sizing and cycle life
- EPS architecture and power distribution
- Power mode analysis with duty cycling

### Appendix E: AOCS Engineer
- Attitude determination: sun sensors, star trackers, gyros
- Attitude control: magnetorquers, reaction wheels
- Pointing budget (RSS error analysis)
- Momentum management and dumping

### Appendix F: Thermal Engineer
- Orbital thermal environment (hot case, cold case, eclipse)
- Passive thermal control (coatings, MLI, radiators)
- Active thermal control (heaters, heat pipes)
- Thermal margin policy (ECSS-E-ST-31C)

### Appendix G: Communications Engineer
- Link budget fundamentals
- Frequency band selection and licensing
- Antenna types and sizing
- Modulation and coding selection
- Ground station network design

### Appendix H: Propulsion Engineer
- Delta-V budget (orbit insertion, maintenance, deorbit, collision avoidance)
- Propulsion system types (cold gas, electric, chemical)
- Tank sizing and propellant management
- Thruster selection and performance

### Appendix I: Structures Engineer
- CubeSat Design Specification compliance
- Launch load analysis (quasi-static, vibration, shock)
- Structural margin of safety calculation
- Mechanism design (deployment, separation)

### Appendix J: Cost Engineer
- Parametric cost models (SSCM, COMPACT, NICM)
- WBS development and cost allocation
- Risk-adjusted cost (Monte Carlo)
- Learning curve for production runs

### Appendix K: Compliance / Regulatory Engineer
- ECSS standard applicability and tailoring
- Frequency licensing decision tree
- Export control classification
- Space debris compliance assessment
- End-of-life planning and filing

### Appendix L: Ground Segment Engineer
- Ground station architecture
- Mission control centre design
- Data processing pipeline
- Operations concept and staffing

### Appendix M: Software Engineer
- Flight software architecture
- FDIR (Fault Detection, Isolation, Recovery)
- Telecommand/telemetry definition
- Ground software and operations tools

---

## Document Production Plan

### Facilitator's Book (~400 pages)
- Full content for all 20 sessions
- Complete solutions to all exercises
- Diagrams and formulae throughout
- Reference citations per section
- Comprehensive index

### Learner's Workbook (~150 pages)
- Condensed content per session (key concepts + references)
- 20 worksheets (one per session)
- Tool exercise guides (step-by-step SpaceCDF instructions)
- Space for notes and discussion points
- Appendix with key formulae and reference tables
