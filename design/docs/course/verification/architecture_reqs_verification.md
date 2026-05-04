# Verification Record -- Architecture-Derived Requirement Types

## Verification Date: 2026-05-04

### 1. Interface Requirements at System/Subsystem Level
**Claim:** Architecture selection derives interface requirements defining system boundaries (bus voltage, data protocols, RF connections, mechanical mounting).
**Verification:** CONFIRMED. ECSS-E-ST-10-24C SS5.2 requires that interface requirements be defined at each system boundary. NASA SEH SS6.3 (Process 12) states interface requirements are derived from architecture choices -- when you select a regulated bus architecture, you must specify the voltage, tolerance, and connector.
**Source:** ECSS-E-ST-10-24C SS5.2; NASA SEH SS6.3
**Confidence:** HIGH

### 2. Engineering Budget Requirements
**Claim:** Architecture selection derives mass, power, and cost budget allocations per subsystem.
**Verification:** CONFIRMED. ECSS-E-HB-10-02A SS5.2 requires that mass budgets be allocated to each subsystem as requirements. NASA SEH SS6.7 (Process 16: Technical Assessment) requires tracking TPMs against budgeted values. Budget allocations ARE requirements -- they constrain the subsystem design.
**Source:** ECSS-E-HB-10-02A SS5.2; NASA SEH SS6.7
**Confidence:** HIGH

### 3. Performance Requirements from Architecture
**Claim:** Architecture selection derives measurable performance requirements (pointing accuracy, data rate, thermal range).
**Verification:** CONFIRMED. NASA SEH SS4.2 (Process 2) defines performance requirements as "shall" statements with measurable thresholds. When an architecture is selected (e.g., "4-wheel AOCS with star tracker"), the performance capability of that architecture becomes a requirement on the subsystem.
**Source:** NASA SEH SS4.2; ECSS-E-ST-10-06C SS5.2
**Confidence:** HIGH

### 4. Functional Requirements from Architecture
**Claim:** Architecture selection derives functional requirements (operating modes, autonomy, FDIR).
**Verification:** CONFIRMED. NASA SEH SS4.3 (Process 3: Logical Decomposition) derives functional requirements from architecture -- when you define an FDIR architecture (e.g., "autonomous safe mode entry"), that becomes a functional requirement. ECSS-E-ST-10C SS5.3 requires functional requirements at each decomposition level.
**Source:** NASA SEH SS4.3; ECSS-E-ST-10C SS5.3
**Confidence:** HIGH

### 5. Requirement ID Prefixes
**Claim:** SR- = System Requirement, SSR- = Subsystem Requirement, IR- = Interface Requirement, BR- = Budget Requirement, FR- = Functional Requirement, PR- = Performance Requirement.
**Verification:** CONFIRMED as common practice. While neither NASA nor ECSS mandates specific prefixes, the convention of using ID prefixes to distinguish requirement types is standard in SE practice. NASA SEH Appendix C recommends unique identifiers. The specific prefixes used (SR/SSR/IR/BR/FR/PR) are widely adopted.
**Source:** NASA SEH Appendix C; common SE practice
**Confidence:** HIGH (convention, not standard mandate)
