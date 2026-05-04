# Verification Record -- Session 1.1: Introduction to Space Mission Design

## Verification Date: 2026-05-04

## Claims Verified

### 1. The 17 Common Technical Processes (NPR 7123.1)
**Claim:** 17 processes grouped as System Design (1-4), Product Realization (5-9), Technical Management (10-17).

**Verification:** CONFIRMED. NPR 7123.1D Chapter 3 defines:
- Processes 1-4 (System Design): Stakeholder Expectations Definition, Technical Requirements Definition, Logical Decomposition, Design Solution Definition
- Processes 5-9 (Product Realization): Product Implementation, Product Integration, Product Verification, Product Validation, Product Transition
- Processes 10-17 (Technical Management): Technical Planning, Requirements Management, Interface Management, Technical Risk Management, Configuration Management, Technical Data Management, Technical Assessment, Decision Analysis

**Source:** NPR 7123.1D Chapter 3; NASA SEH §2.1
**Confidence:** HIGH

### 2. NASA Lifecycle Phases
**Claim:** 7 phases: Pre-A, A, B, C, D, E, F with KDPs between them.

**Verification:** CONFIRMED.
- Pre-A: Concept Studies
- A: Concept & Technology Development
- B: Preliminary Design & Technology Completion
- C: Final Design & Fabrication
- D: System Assembly, Integration & Test, Launch
- E: Operations & Sustainment
- F: Closeout

KDPs are lettered A-F, gating entry to each phase. Governed by NPR 7120.5 (currently Rev F).

**Source:** NPR 7120.5F Chapter 2; NASA SEH Chapter 3
**Confidence:** HIGH

### 3. Major Review Gates
**Claim:** MCR, SRR, SDR/MDR, PDR, CDR, TRR, ORR, FRR sequence.

**Verification:** CONFIRMED with clarification.
- MCR = Mission Concept Review (Pre-A)
- SRR = System Requirements Review (A)
- SDR = System Definition Review / MDR = Mission Definition Review (A)
- PDR = Preliminary Design Review (B exit)
- CDR = Critical Design Review (C entry)
- SIR = System Integration Review (C/D)
- TRR = Test Readiness Review (D)
- ORR = Operational Readiness Review (D)
- FRR = Flight Readiness Review (D, pre-launch)
- Additional: PLAR (Post-Launch Assessment Review), DR (Decommissioning Review)

**Source:** NPR 7123.1 Appendix G; NASA SEH §3.7
**Confidence:** HIGH

### 4. ECSS-NASA Phase Mapping
**Claim:** ECSS phases 0/A/B/C/D/E/F map approximately to NASA Pre-A/A/B/C/D/E/F.

**Verification:** CONFIRMED as approximate. Phase letters align but entry/exit criteria differ.
- ECSS Phase 0 ~ NASA Pre-A (exit: MDR ~ MCR)
- ECSS Phase A ~ NASA Phase A (exit: PRR ~ SRR)
- ECSS Phase B ~ NASA Phase B (exit: PDR in both)
- ECSS Phase C ~ NASA Phase C (exit: CDR in both)
- ECSS Phase D ~ NASA Phase D (exit: QR+AR ~ TRR/ORR)
- ECSS Phase E ~ NASA Phase E
- ECSS Phase F ~ NASA Phase F

**Caveat:** Not identical -- review content and baseline expectations differ. Course uses "approximately equivalent" language.

**Source:** ECSS-M-ST-10C Rev.1; NASA SEH Chapter 3
**Confidence:** MEDIUM-HIGH

### 5. ESA Concurrent Design Facility (CDF)
**Claim:** Established 1998, ~20-25 domain specialists, studies last 4-8 weeks.

**Verification:** 
- Established: November 1998 at ESTEC, Noordwijk. CONFIRMED.
- Team size: ~20-25 discipline specialists (sources report 25-35 in room). CORRECTED from earlier "~15".
- Study duration: 4-8 weeks typical. CONFIRMED.
- Format: 4-hour sessions, typically 2 per week.
- Tool: Originally Excel-based IDM, now OCDT (Open Concurrent Design Tool).
- Over 200 studies completed by 2018 (20th anniversary).

**Source:** ESA CDF official pages; "20 years of ESA's CDF" publication
**Confidence:** HIGH

### 6. System-V Model
**Claim:** Left side = decomposition (need -> requirements -> design -> implementation); right side = integration (verification -> validation -> operations).

**Verification:** CONFIRMED. The "Vee" model is described in NASA SEH §2.3 as the fundamental framework showing how system design (left side, top-down decomposition) maps to product realization (right side, bottom-up integration and verification). Each level on the left has a corresponding verification level on the right.

**Source:** NASA SEH §2.3, Figure 2.3-1
**Confidence:** HIGH

## Corrections Applied
1. CDF team size: changed from "~15 engineers" to "~20-25 domain specialists"
2. CDF study duration: changed from "3-6 weeks" to "4-8 weeks"
3. Phase mapping caveat: added note that ECSS and NASA phases are "approximately equivalent" not identical
