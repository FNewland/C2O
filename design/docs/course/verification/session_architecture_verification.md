# Verification Record -- System Architecture Selection

## Verification Date: 2026-05-04

### 1. NASA SEH Process 4: Design Solution Definition
**Claim:** Architecture selection is Process 4 -- choosing among alternative designs.
**Verification:** CONFIRMED. NASA SEH SS4.4 describes Design Solution Definition as "selecting the preferred solution from alternative solutions." The process includes trade studies to evaluate alternatives against criteria.
**Source:** NASA SEH SS4.4; NPR 7123.1D SS3.2.4
**Confidence:** HIGH

### 2. Architecture Derives Requirements
**Claim:** Selecting an architecture derives system and subsystem level requirements.
**Verification:** CONFIRMED. NASA SEH SS4.3.3: "Derived requirements result from design decisions made during the design process." When an architecture is selected (e.g., "4-wheel AOCS with star tracker"), it creates requirements on the star tracker accuracy, wheel torque, etc. that did not exist at the mission level.
**Source:** NASA SEH SS4.3.3; ECSS-E-ST-10C SS5.4.3
**Confidence:** HIGH

### 3. AOCS Architecture Options
**Claim:** CubeSat AOCS ranges from passive magnetic (~10deg) to 4-wheel+ST (<0.1deg).
**Verification:** CONFIRMED from vendor data and mission heritage:
- Passive magnetic: SwissCube (1U), ~10-15deg pointing
- Magnetorquer-only: many 1U/2U CubeSats, 2-5deg typical
- 3-wheel + MTQ: common on 3U EO CubeSats, 0.5-1deg
- 4-wheel + ST + MTQ: Planet SuperDove, Spire LEMUR, <0.1deg
**Source:** Vendor datasheets (CubeSpace, BCT, NewSpace Systems); eoPortal mission data
**Confidence:** HIGH

### 4. EPS Architecture Options
**Claim:** Body-mounted gives 7-12W for 3U; deployable gives 15-30W.
**Verification:** CONFIRMED. See Session 3.3 verification SS8 (SA power reference table).
Body-mounted: GomSpace data confirms 7W for 3U.
Single deployable: 15W for 3U confirmed from MMA Design and GomSpace.
**Source:** GomSpace, ISIS, MMA Design vendor data
**Confidence:** HIGH

### 5. Star Tracker Accuracy
**Claim:** <=10 arcsec attitude knowledge (3-sigma).
**Verification:** CONFIRMED. Typical CubeSat star trackers:
- Hyperion ST200: 5-10 arcsec (cross-boresight)
- BCT NST: 6 arcsec (1-sigma)
- Berlin Space Technologies: 10 arcsec
The 10 arcsec figure is a reasonable subsystem requirement.
**Source:** Vendor datasheets; NASA Small Spacecraft SOA report
**Confidence:** HIGH
