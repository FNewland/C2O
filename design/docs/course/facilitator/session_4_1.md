# Session 4.1: Equipment Selection & Bill of Materials

**Duration:** 2 hours
**Prerequisites:** Day 3 complete (subsystems sized, components identified via parametric agents)
**References:** ECSS-Q-ST-20C (Quality Assurance), ECSS-E-ST-10-24C (Interfaces), ITAR/EAR (22 CFR 120-130 / 15 CFR 730-774), CDS Rev 14.1, NASA SEH Rev 2 section 6.8

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Apply a structured make/buy/reuse decision framework to component selection
2. Evaluate COTS components against requirements using TRL and heritage criteria
3. Construct a Bill of Materials (BOM) with full traceability to requirements
4. Identify export control constraints (ITAR, EAR, Canadian Controlled Goods) for selected equipment
5. Verify interface compatibility (RF, electrical, mechanical) during component selection
6. Track cumulative mass, power, and cost budgets as selections are made

---

## 1. The Make/Buy/Reuse Decision (20 min)

### Teaching Notes

Before selecting any hardware, the team must decide the procurement strategy for each subsystem. This is a fundamental systems engineering decision that affects cost, schedule, risk, and performance.

*[Source: NASA SEH Rev 2 section 6.8 "Decision Analysis"; ECSS-M-ST-10C Rev.1 section 5.4]*

### Decision Framework

```
For each subsystem or component:
  1. Does a COTS product exist that meets requirements?
     -> Yes: BUY (lowest risk, fastest schedule)
     -> No: Continue
  2. Does flight-proven hardware from a previous mission exist?
     -> Yes: REUSE (low risk, may need delta-qualification)
     -> No: Continue
  3. Can the requirement be met by modifying existing hardware?
     -> Yes: MODIFY (moderate risk, moderate schedule)
     -> No: MAKE (highest risk, longest schedule, most expensive)
```

### Make/Buy/Reuse Trade Matrix

| Factor | Buy (COTS) | Reuse (Heritage) | Modify | Make (Custom) |
|--------|-----------|-------------------|--------|---------------|
| **Cost (NRE)** | None | None-Low | Moderate | High |
| **Cost (Recurring)** | Vendor price | Reproduction cost | Vendor + delta | Full development |
| **Schedule** | 4-16 weeks lead | 8-24 weeks | 12-36 weeks | 12-48 months |
| **Risk** | Low (if TRL >= 7) | Low (flight-proven) | Medium | High |
| **Performance** | Fixed by vendor | Fixed by heritage | Tuneable | Fully customisable |
| **IP ownership** | Vendor retains | May be shared | Negotiated | Full ownership |
| **Qualification** | Vendor-provided data | Delta-qual only | Partial re-qual | Full qualification |

### Key Equations

> **Non-Recurring Engineering (NRE) Cost Estimate:**
>
> NRE = Labour_hours x Hourly_rate + Material_cost + Facility_cost + Testing_cost
>
> For COTS: NRE is near zero (vendor absorbs development cost).
> For custom: NRE can be 3-10x the unit recurring cost.

### Worked Example

*Problem:* A 6U CubeSat mission needs a fine sun sensor with 0.1 degree accuracy. Three options:

| Option | Type | Accuracy | Mass | Cost | TRL | Lead Time |
|--------|------|----------|------|------|-----|-----------|
| Bradford SSOC-D60 | COTS | 0.1 deg | 35 g | EUR 15K | 9 | 8 weeks |
| In-house photodiode array | Custom | 0.05 deg | 20 g | EUR 8K + 400 hr NRE | 4 | 12 months |
| Modified heritage sensor | Reuse | 0.08 deg | 40 g | EUR 6K + 80 hr delta-qual | 7 | 16 weeks |

*Decision:* The COTS option (Bradford SSOC-D60) meets the requirement, has TRL 9, lowest schedule risk, and total cost of EUR 15K vs EUR 8K + ~EUR 40K NRE for custom. **Buy.**

---

## 2. Technology Readiness Level (TRL) Assessment (20 min)

### Teaching Notes

TRL is the standard metric for technology maturity. It was developed by NASA in the 1970s and is now used universally in space programmes.

*[Source: NASA NPR 7123.1D Appendix E; ECSS-E-HB-11A "Technology Readiness Level (TRL) Guidelines"]*
*[URL: https://www.nasa.gov/directorates/somd/space-communications-navigation-program/technology-readiness-levels/]*

### TRL Scale with Decision Criteria

| TRL | Definition | Evidence Required | CubeSat Decision |
|-----|-----------|-------------------|-----------------|
| 1 | Basic principles observed | Published research | Do not select |
| 2 | Technology concept formulated | Analytical studies | Do not select |
| 3 | Experimental proof of concept | Lab measurements | Do not select |
| 4 | Component validated in lab | Breadboard tested | High risk -- avoid unless no alternative |
| 5 | Component validated in relevant environment | Engineering model tested | Acceptable for technology demonstrator missions |
| 6 | System/subsystem model demonstrated in relevant environment | Prototype in relevant environment | Acceptable with risk mitigation |
| 7 | System prototype demonstrated in operational environment | Prototype tested in space | Preferred minimum for CubeSats |
| 8 | Actual system completed and qualified | Flight-qualified hardware | Strong preference |
| 9 | Actual system flight-proven | Successful on-orbit operation | Lowest risk |

### TRL and Risk Relationship

> **Risk Reduction Factor (empirical):**
>
> Risk_factor = 10^(-(TRL - 1) / 3)
>
> | TRL | Risk Factor | Interpretation |
> |-----|------------|----------------|
> | 3 | 0.22 | High probability of failure/redesign |
> | 5 | 0.046 | Moderate risk |
> | 7 | 0.010 | Low risk |
> | 9 | 0.002 | Very low risk |
>
> *This empirical relationship (from SMAD4 Table 20-12) illustrates why TRL >= 6 is the typical threshold for mission-critical components.*

### Real Mission Example: MarCO (Mars Cube One)

NASA's MarCO A and B (launched May 2018) were the first interplanetary CubeSats. They used:
- Iris transponder (JPL, TRL 6 at selection -- first deep-space CubeSat radio)
- COTS reaction wheels (Blue Canyon Technologies, TRL 9)
- Custom deployable reflectarray antenna (JPL, TRL 5 at selection)

The custom antenna was the highest-risk item. It required extensive development testing and was the last component to reach TRL 6 for CDR. This delayed the schedule by 4 months but ultimately succeeded.

*Lesson: If you must fly a low-TRL component, it will dominate your schedule and risk register.*

*[Source: "Mars Cube One (MarCO) -- Lessons Learned", A. Klesh et al., 33rd Annual Small Satellite Conference, 2019]*

---

## 3. Bill of Materials (BOM) Construction (20 min)

### Teaching Notes

The BOM is the definitive list of all hardware, software, and consumables required to build the satellite. It is the bridge between design and procurement.

### BOM Structure

A properly structured BOM follows the WBS hierarchy:

```
BOM Level 0: Spacecraft (S/C-001)
  BOM Level 1: Subsystem (e.g., EPS-000)
    BOM Level 2: Assembly (e.g., EPS-SA-000 Solar Array Assembly)
      BOM Level 3: Component (e.g., EPS-SA-001 Solar Cell String)
        BOM Level 4: Part (e.g., EPS-SA-001-01 Azur 3G30C cell)
```

### BOM Fields

| Field | Description | Example |
|-------|------------|---------|
| **Item ID** | Unique hierarchical identifier | EPS-BAT-001 |
| **Description** | Component name and model | GomSpace NanoPower P31u |
| **Manufacturer** | Vendor name | GomSpace A/S |
| **Part Number** | Manufacturer part number | P31U-9-30 |
| **Quantity** | Number required | 1 |
| **Unit Mass (g)** | Per-item mass | 94 |
| **Unit Power (W)** | Peak / average power draw | 0.5 / 0.2 |
| **Unit Cost (EUR)** | Procurement cost | 8,500 |
| **TRL** | Technology readiness level | 9 |
| **Heritage** | Previous mission(s) flown | GOMX-3, GOMX-4 |
| **Lead Time** | Procurement lead time | 12 weeks |
| **ECCN/USML** | Export classification | EAR99 |
| **Status** | Selected / Ordered / Received / Tested | Selected |

### SpaceCDF BOM Generation

In SpaceCDF, the BOM is built automatically from the Equipment Browser selections:
1. Each component selected in the Equipment Browser creates a BOM entry
2. Quantities are set using the quantity selector (e.g., x4 for reaction wheels)
3. The **Exports** tab generates a formatted BOM spreadsheet
4. The BOM includes both parametric estimates and actual COTS data for comparison

### Key Equations

> **BOM Mass Total:**
>
> M_BOM = Sum_i (m_i x q_i) + M_harness + M_fasteners + M_margin
>
> Where:
> - m_i = unit mass of component i
> - q_i = quantity of component i
> - M_harness = harness mass (typically 5-8% of dry mass for CubeSats)
> - M_fasteners = mechanical fasteners, standoffs, thermal hardware (~3-5%)
> - M_margin = system margin (typically 20% at Phase A)

### Worked Example

*3U CubeSat BOM Summary:*

| Subsystem | Components | Total Mass (g) | Total Power (W) | Total Cost (kEUR) |
|-----------|-----------|----------------|-----------------|-------------------|
| Structure | Rails, panels, fasteners | 350 | 0 | 8.0 |
| EPS | SA + battery + board | 420 | 0.5 | 18.0 |
| OBC | Flight computer + storage | 80 | 1.2 | 10.0 |
| AOCS | Star tracker + magnetorquers + RWs | 550 | 4.5 | 45.0 |
| TTC | S-band transceiver + patch antenna | 180 | 8.0 (TX) | 22.0 |
| Thermal | MLI + heaters | 60 | 2.0 (peak) | 3.0 |
| Payload | Multispectral imager | 800 | 12.0 | 65.0 |
| Harness | Cables, connectors | 180 | 0 | 2.5 |
| **Total** | | **2620** | **28.2 (peak)** | **173.5** |
| Allocation (6U) | | 12000 | 40.0 (SA EOL) | 250.0 |
| Margin | | 9380 (78%) | 11.8 (30%) | 76.5 (31%) |

---

### 1U Worked Example: UniSat-1

**Complete Bill of Materials**

UniSat-1's BOM is remarkably short -- only 5--7 line items plus harness. This simplicity is a major advantage for university teams with limited procurement experience.

> **UniSat-1 BOM (Phase B -- vendor quotes obtained):**
>
> | Item ID | Component | Manufacturer | Part Number | Qty | Unit Mass (g) | Unit Cost (kEUR) | TRL | ECCN | Lead (wks) |
> |---------|-----------|-------------|-------------|-----|---------------|-----------------|-----|------|-----------|
> | STR-001 | 1U CubeSat Structure | ISIS | ISIS-1U-STR | 1 | 200 | 4.0 | 9 | EAR99 | 8 |
> | EPS-001 | NanoPower P31us (EPS + 10Wh battery) | GomSpace | P31US-10 | 1 | 200 | 12.0 | 9 | EAR99 | 12 |
> | EPS-SA-001 | Body-mounted GaAs solar cells | AzurSpace | 3G30C | 5 | 10 | 1.5 | 9 | EAR99 | 10 |
> | OBC-001 | Custom flight computer (Cortex-M) | In-house | UNISAT-OBC-01 | 1 | 30 | 3.0 | 5 | EAR99 | -- |
> | COM-001 | UHF Transceiver | GomSpace | NanoCom AX100 | 1 | 55 | 8.0 | 8 | EAR99 | 12 |
> | COM-ANT-001 | UHF Deployable Antenna | Endurosat | UHF-ANT-S | 1 | 25 | 2.5 | 8 | EAR99 | 8 |
> | PL-001 | MEMS Magnetometer Board | In-house | UNISAT-MAG-01 | 1 | 50 | 5.0 | 4 | EAR99 | -- |
> | AOCS-001 | Passive magnetic kit (magnet + rods) | NewSpace | PMAG-1U | 1 | 30 | 1.0 | 9 | EAR99 | 6 |
> | HAR-001 | Internal harness | Custom | -- | 1 | 50 | 1.0 | N/A | EAR99 | -- |
> | | **TOTALS** | | | | **690 g** | **~44 kEUR** | | | |

**Cost summary (total mission, hardware + services):**

| WBS Element | Cost (kEUR) | Notes |
|-------------|------------|-------|
| Hardware (BOM) | 44 | All COTS except OBC and payload |
| OBC software | 5 | Student labour (costed at stipend rate) |
| Payload calibration | 3 | University magnetometer lab |
| I&T | 8 | Assembly + vibration test (university facility) |
| Ground station | 5 | SatNOGS (free) + dedicated Yagi antenna purchase |
| Launch (ISS deploy) | 15 | NanoRacks 1U deployment fee |
| PM/SE/QA | 5 | Faculty supervision |
| **TOTAL** | **~85 kEUR** | |

**Comparison to 3U EO mission:**

| Metric | UniSat-1 (1U) | 3U EO CubeSat |
|--------|--------------|---------------|
| BOM line items | 9 | ~15--20 |
| Hardware cost | ~44 kEUR | ~290 kEUR |
| Total mission cost | ~85 kEUR | ~490 kEUR |
| Development time | 6--12 months | 18--24 months |
| Team size | 3--5 people | 8--15 people |

**Export control:** All UniSat-1 components are classified EAR99 (no licence required). There are no ITAR-controlled items because the mission uses no star trackers, no radiation-hardened processors, and no propulsion with ITAR-restricted technology. This is a significant advantage for international university collaborations.

**Make/Buy/Reuse decisions:**

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Structure | Buy (COTS) | ISIS 1U frame is flight-proven, TRL 9, low cost |
| EPS | Buy (COTS) | GomSpace P31us is the de facto standard, TRL 9 |
| OBC | Make (custom) | Minimal board using university lab; lower cost than COTS OBC for this simple application |
| Comms | Buy (COTS) | GomSpace AX100, TRL 8, well-documented |
| Payload | Make (custom) | Novel MEMS sensor -- this IS the technology demonstration |
| Passive AOCS | Buy (COTS) | Standard magnetic stabilisation kit |

---

## 4. Export Control and Procurement (25 min)

### Teaching Notes

Export control is one of the most commonly overlooked aspects of CubeSat missions, especially for international teams. Violations carry severe penalties (criminal prosecution, programme cancellation).

*[Source: ITAR -- 22 CFR Parts 120-130; EAR -- 15 CFR Parts 730-774; Canadian Controlled Goods Program -- Defence Production Act]*
*[URL: https://www.pmddtc.state.gov/ddtc_public (US ITAR); https://www.bis.doc.gov (US EAR)]*

### Export Control Regimes

| Regime | Governing Law | Applies To | Key Concern for CubeSats |
|--------|-------------|-----------|-------------------------|
| **ITAR** | US Arms Export Control Act | Defence articles (USML Categories IV, XI, XV) | Star trackers, rad-hard processors, some GPS receivers |
| **EAR** | Export Administration Act | Dual-use items (CCL) | Most COTS space components (ECCN 9A515) |
| **Canadian CGP** | Defence Production Act | Controlled goods in Canada | Handling US-origin ITAR items in Canadian facilities |
| **Wassenaar** | Wassenaar Arrangement | Multilateral export controls | Encryption, high-accuracy GNSS, imaging sensors |

### Component Classification Decision

```
Is the component on the US Munitions List (USML)?
  -> Yes: ITAR-controlled. Need DSP-5 license for export.
     Categories: IV (launch vehicles), XI (military electronics),
                 XV (spacecraft systems)
  -> No: Check Commerce Control List (CCL)
     Is it classified under ECCN 9A515 (spacecraft)?
       -> Yes: EAR-controlled. May need BIS license.
       -> No: Likely EAR99 (no license required for most destinations)
```

### Common ITAR-Controlled CubeSat Components

| Component Type | Why Controlled | Alternative |
|---------------|---------------|------------|
| Radiation-hardened processors | Military-grade rad tolerance | COTS processors with software mitigation |
| High-accuracy star trackers (< 1 arcsec) | Missile guidance applicability | Lower-accuracy models (> 5 arcsec) |
| Certain GPS/GNSS receivers | Above COCOM limits (>60,000 ft, >1000 kt) | Space-rated receivers with COCOM compliance |
| Propulsion systems (some) | Missile technology | Cold-gas or water-based systems |
| Encryption modules | Signals intelligence | Open-source encryption (may still need EAR review) |

### Procurement Workflow

```
1. Requirements -> Derive component specification
2. Market survey -> Identify candidate COTS products
3. Export classification -> Request ECCN from vendor
4. Trade study -> Score and rank candidates
5. Request for Quote (RFQ) -> Obtain pricing and lead times
6. Purchase Order (PO) -> Commit to procurement
7. Incoming inspection -> Verify against PO and datasheet
8. Integration -> Install and functionally test
```

### Real Mission Example: Export Control Impact

The BRITE-Constellation (Austria/Canada/Poland) was a series of nanosatellites for stellar photometry. The Canadian BRITE satellites (UniBRITE and BRITE-Austria, built by UTIAS/SFL) required careful export control management:
- US-origin ITAR components required Technical Assistance Agreements (TAAs)
- Controlled Goods registration required for the Canadian team
- Export permits needed for shipping between Canada, Austria, and the US launch site
- Total regulatory compliance effort: ~6 person-months and 12+ months lead time

*Lesson: Start export classification immediately when components are identified. A single ITAR component can add 6-12 months to the schedule.*

*[Source: Sarda, K. et al., "BRITE-Constellation Mission and Spacecraft", AIAA/USU Small Satellite Conference, 2014]*

---

## 5. Interface Compatibility Verification (20 min)

### Teaching Notes

As components are selected, every interface must be verified for compatibility. The three interface categories are RF, electrical, and mechanical.

### RF Chain Compatibility

The RF chain (transponder, cable, antenna) must be frequency-matched. This is the most common equipment incompatibility for CubeSat newcomers.

| Rule | Correct Example | Incorrect Example |
|------|----------------|-------------------|
| **Band match** | S-band transponder + S-band patch antenna | S-band transponder + X-band horn |
| **Impedance match** | 50 ohm transponder + 50 ohm cable + 50 ohm antenna | Mixed impedances cause reflections |
| **Connector match** | SMA on transponder + SMA-SMA cable + SMA on antenna | SMA to N-type needs adapter (loss) |
| **Polarisation** | RHCP antenna + RHCP ground station | RHCP to LHCP causes > 20 dB cross-pol loss |

> **Impedance Mismatch Loss:**
>
> Return_Loss (dB) = -20 * log10(|Gamma|)
>
> Where Gamma = (Z_load - Z_source) / (Z_load + Z_source)
>
> For a 50 ohm source into a 75 ohm load:
> Gamma = (75 - 50) / (75 + 50) = 0.2
> Return_Loss = -20 * log10(0.2) = 14 dB
> Mismatch_Loss = -10 * log10(1 - |Gamma|^2) = -10 * log10(1 - 0.04) = 0.18 dB

SpaceCDF checks RF compatibility automatically: if you select a transponder in one band and an antenna in another, a warning dialog appears.

### Electrical Interface Verification

| Parameter | Typical CubeSat | What to Verify |
|-----------|----------------|----------------|
| Bus voltage | 3.3V, 5V, or unregulated (6-8.4V Li-ion) | Component input voltage range covers bus voltage |
| Peak current | Per switched line limit (typically 1-3A) | Component inrush current does not exceed limit |
| Data protocol | I2C, SPI, UART, CAN, RS-422 | All devices on same bus use compatible protocol |
| Connector | PC/104, Hirose, Harwin | Physical connector type matches or adapter planned |

### Mechanical Interface Verification

| Parameter | CDS 3U Requirement | Verification |
|-----------|--------------------|----|
| Dimensions | 100.0 +/- 0.1 mm x 100.0 +/- 0.1 mm x 340.5 +/- 0.5 mm | Caliper measurement |
| Rail profile | 8.5 x 8.5 mm +/- 0.1 mm | Profile gauge |
| Component stack height | <= 83 mm internal width per U | 3D model check |
| CG location | Within 2 cm of geometric centre | Mass properties measurement |

---

## 6. Equipment Selection Exercise (35 min)

### Instructions

**Part A: Equipment Selection (20 min)**

1. Open the **Equipment Browser** in SpaceCDF
2. For each **required** category (blue dot), select at least one component:
   - Start with EPS (batteries + solar panels + EPS board)
   - Then OBC, AOCS sensors/actuators, TTC, structure
   - Use quantity selectors (e.g., x4 for reaction wheels, x3 for magnetorquers)
3. Watch the **live budget bar** as you select -- keep mass under allocation
4. When selecting TTC: verify the spectrum band matches your earlier selection
5. After all selections, review the **Budget Breakdown** on the Dashboard

**Part B: BOM Review and Export Check (15 min)**

1. Navigate to the **Exports** tab
2. Generate the **BOM** -- review all entries
3. For each component, check: Is the ECCN listed? Is it EAR99, ECCN 9A515, or ITAR?
4. Flag any components that may require export licences
5. Compute: BOM total mass vs parametric estimate vs launcher allocation

### Worksheet 4.1 Tasks

1. Complete the full BOM table (component, manufacturer, part number, mass, power, cost, TRL, ECCN)
2. Document the make/buy/reuse decision for each subsystem with rationale
3. Compute total BOM mass vs parametric estimate vs allocation -- state margin
4. Identify any export-controlled components and note the required licensing action
5. Describe one interface incompatibility found during selection and how it was resolved

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | NASA Technology Readiness Levels | https://www.nasa.gov/directorates/somd/space-communications-navigation-program/technology-readiness-levels/ |
| 2 | ECSS-Q-ST-20C Quality Assurance | https://ecss.nl/standard/ecss-q-st-20c-rev-2-quality-assurance-1-march-2023/ |
| 3 | US DDTC (ITAR) | https://www.pmddtc.state.gov/ |
| 4 | US BIS (EAR) | https://www.bis.doc.gov/ |
| 5 | CubeSat Design Specification Rev 14.1 | https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf |
| 6 | SMAD4 Chapter 20 (Cost Modelling) | Wertz, Everett, Puschell (eds.), Space Mission Engineering, Microcosm 2011 |
| 7 | MarCO Lessons Learned (Klesh et al.) | SSC19-WKII-07, 33rd Small Sat Conference, 2019 |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Make/Buy/Reuse | Buy COTS first; Reuse heritage second; Make custom only when necessary |
| TRL | Minimum TRL 6 for mission-critical components; TRL 7+ preferred for CubeSats |
| BOM | Hierarchical list: Subsystem -> Assembly -> Component -> Part, with full traceability |
| Export control | Classify every component (EAR99 / ECCN / ITAR); start early -- delays programme |
| RF compatibility | Band, impedance, connector, polarisation must all match across RF chain |
| Electrical | Bus voltage, data protocol, connector type verified per component |
| Budget tracking | Live totals during selection; stop if allocation exceeded |
