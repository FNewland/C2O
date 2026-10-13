# Part III — Integration, Verification and Operations

# Chapter 13 — Equipment Selection and Bill of Materials

> **Recommended background.** SMAD4 Ch. 14 (Spacecraft subsystems and parts) and Ch. 20 (Cost modelling); NASA NPR 7123.1D Appendix E (Technology readiness levels); ECSS-E-HB-11A (TRL guidelines); ECSS-Q-ST-20C (Quality assurance); ECSS-E-ST-10-24C (Interface management); NASA SEH Rev 2 §6.8 (Decision analysis). This chapter assumes the subsystems have been sized (Chapters 9–12) and that candidate components have been identified for each; it turns those candidates into a procurable, traceable bill of materials. The trade-study method is that of Chapter 4 §4.5 and the interface codes are those of Chapter 8 Table 8.2.

## Learning objectives

By the end of this chapter, you will be able to:

1. Apply a structured make/buy/reuse decision framework to component selection
2. Evaluate COTS components against requirements using TRL and heritage criteria
3. Construct a bill of materials (BOM) with full traceability to requirements
4. Identify export-control constraints (ITAR, EAR, Canadian Controlled Goods) for selected equipment
5. Verify interface compatibility (RF, electrical, mechanical) during component selection
6. Track cumulative mass, power and cost budgets as selections are made

Vendor products named in this chapter are representative examples, not endorsements; prices are indicative (2026).

---

## 13.1 The make/buy/reuse decision

Before selecting any hardware, the project must decide the procurement strategy for each subsystem. This is a fundamental systems-engineering decision that affects cost, schedule, risk and performance.

*[Source: NASA SEH Rev 2 §6.8 "Decision Analysis"; ECSS-M-ST-10C Rev. 1 §5.4]*

### 13.1.1 Decision framework

```
For each subsystem or component:
  1. Does a COTS product exist that meets the requirements?
     → Yes: BUY (lowest risk, fastest schedule)
     → No: continue
  2. Does flight-proven hardware from a previous mission exist?
     → Yes: REUSE (low risk, may need delta-qualification)
     → No: continue
  3. Can the requirement be met by modifying existing hardware?
     → Yes: MODIFY (moderate risk, moderate schedule)
     → No: MAKE (highest risk, longest schedule, most expensive)
```

### 13.1.2 Make/buy/reuse trade matrix

| Factor | Buy (COTS) | Reuse (heritage) | Modify | Make (custom) |
|--------|-----------|-------------------|--------|---------------|
| **Cost (NRE)** | None | None–low | Moderate | High |
| **Cost (recurring)** | Vendor price | Reproduction cost | Vendor + delta | Full development |
| **Schedule** | 4–16 weeks lead | 8–24 weeks | 12–36 weeks | 12–48 months |
| **Risk** | Low (if TRL ≥ 7) | Low (flight-proven) | Medium | High |
| **Performance** | Fixed by vendor | Fixed by heritage | Tuneable | Fully customisable |
| **IP ownership** | Vendor retains | May be shared | Negotiated | Full ownership |
| **Qualification** | Vendor-provided data | Delta-qualification only | Partial re-qualification | Full qualification |

### 13.1.3 Non-recurring engineering cost

> **Key equation — non-recurring engineering (NRE) cost estimate:**
>
> $$C_{\text{NRE}} = N_{\text{hours}} \cdot r_{\text{hour}} + C_{\text{material}} + C_{\text{facility}} + C_{\text{test}}$$
>
> where $N_{\text{hours}}$ is the engineering labour, $r_{\text{hour}}$ the loaded hourly rate, and the remaining terms the material, facility and test costs of the development.
>
> For COTS: NRE is near zero (the vendor absorbs the development cost).
> For custom: NRE can be 3–10× the unit recurring cost. Chapter 16 develops the cost-estimating relationships that put this in context.

### 13.1.4 Worked example

*Problem:* A 6U CubeSat mission needs a fine sun sensor with 0.1° accuracy. Three options:

| Option | Type | Accuracy | Mass | Cost (indicative, 2026) | TRL | Lead time |
|--------|------|----------|------|------|-----|-----------|
| Bradford SSOC-D60 (representative) | COTS | 0.1° | 35 g | 15 kEUR | 9 | 8 weeks |
| In-house photodiode array | Custom | 0.05° | 20 g | 8 kEUR + 400 h NRE | 4 | 12 months |
| Modified heritage sensor | Reuse | 0.08° | 40 g | 6 kEUR + 80 h delta-qualification | 7 | 16 weeks |

*Decision:* The COTS option meets the requirement, has TRL 9, the lowest schedule risk, and a total cost of 15 kEUR versus 8 kEUR + ~40 kEUR NRE (400 h at a loaded rate of ~100 EUR/h) for the custom option. **Buy.**

---

## 13.2 Technology readiness level (TRL) assessment

TRL is the standard metric for technology maturity. It was developed by NASA in the 1970s and is now used universally in space programmes. Figure 13.1 shows the nine-step ladder.

*[Source: NASA NPR 7123.1D Appendix E; ECSS-E-HB-11A "Technology Readiness Level (TRL) Guidelines"]*

![Technology readiness level ladder.](../assets/figures/fig_trl.png)

**Figure 13.1** — The nine technology readiness levels, from basic principles observed (TRL 1) to flight-proven (TRL 9), with the environment in which each level's evidence must be produced. The gap between TRL 6 and TRL 7 — from a relevant environment on the ground to the operational environment in space — is the one that costs the most to cross.

### 13.2.1 TRL scale with decision criteria

| TRL | Definition | Evidence required | CubeSat decision |
|-----|-----------|-------------------|-----------------|
| 1 | Basic principles observed | Published research | Do not select |
| 2 | Technology concept formulated | Analytical studies | Do not select |
| 3 | Experimental proof of concept | Laboratory measurements | Do not select |
| 4 | Component validated in laboratory | Breadboard tested | High risk — avoid unless no alternative |
| 5 | Component validated in relevant environment | Engineering model tested | Acceptable for technology-demonstrator missions |
| 6 | System/subsystem model demonstrated in relevant environment | Prototype in relevant environment | Acceptable with risk mitigation |
| 7 | System prototype demonstrated in operational environment | Prototype tested in space | Preferred minimum for CubeSats |
| 8 | Actual system completed and qualified | Flight-qualified hardware | Strong preference |
| 9 | Actual system flight-proven | Successful on-orbit operation | Lowest risk |

### 13.2.2 TRL and risk relationship

> **Risk reduction factor (empirical):**
>
> $$f_{\text{risk}} = 10^{-(\text{TRL} - 1)/3}$$
>
> | TRL | Risk factor | Interpretation |
> |-----|------------|----------------|
> | 3 | 0.22 | High probability of failure or redesign |
> | 5 | 0.046 | Moderate risk |
> | 7 | 0.010 | Low risk |
> | 9 | 0.002 | Very low risk |
>
> *This empirical relationship (after SMAD4 Table 20-12) illustrates why TRL ≥ 6 is the typical threshold for mission-critical components.*

### 13.2.3 Real mission example: MarCO (Mars Cube One)

NASA's MarCO A and B (launched May 2018) were the first interplanetary CubeSats. They used:
- Iris transponder (JPL, TRL 6 at selection — the first deep-space CubeSat radio)
- COTS reaction wheels (Blue Canyon Technologies, TRL 9)
- Custom deployable reflectarray antenna (JPL, TRL 5 at selection)

The custom antenna was the highest-risk item. It required extensive development testing and was the last component to reach TRL 6 for CDR. This delayed the schedule by 4 months but ultimately succeeded.

*Lesson: if you must fly a low-TRL component, it will dominate your schedule and risk register.*

*[Source: Klesh, A. et al., "MarCO: Early Operations of the First CubeSats to Mars", 32nd Annual Small Satellite Conference, 2018; "Mars Cube One (MarCO) — Lessons Learned", 33rd Annual Small Satellite Conference, 2019]*

---

## 13.3 Bill of materials (BOM) construction

The BOM is the definitive list of all hardware, software and consumables required to build the satellite. It is the bridge between design and procurement.

### 13.3.1 BOM structure

A properly structured BOM follows the work-breakdown-structure hierarchy; Figure 13.2 shows the same five levels with the roll-up columns that each parent node carries:

```
BOM level 0: Spacecraft (S/C-001)
  BOM level 1: Subsystem (e.g. EPS-000)
    BOM level 2: Assembly (e.g. EPS-SA-000 Solar array assembly)
      BOM level 3: Component (e.g. EPS-SA-001 Solar cell string)
        BOM level 4: Part (e.g. EPS-SA-001-01 Azur 3G30C cell)
```

![BOM hierarchy tree with roll-up columns](../assets/figures/fig_bom_tree.png)

**Figure 13.2** — The BOM as an indented tree from spacecraft (level 0) to part (level 4), illustrated for the EPS branch of a 3U CubeSat with representative values. Each parent row rolls up its children: mass, power and cost are quantity-weighted sums, the TRL column carries the lowest TRL beneath it and the lead-time column the longest, so the spacecraft row shows at a glance which item (here the TRL 6 payload, 26 weeks) drives the risk and the schedule.

### 13.3.2 BOM fields

| Field | Description | Example |
|-------|------------|---------|
| **Item ID** | Unique hierarchical identifier | EPS-BAT-001 |
| **Description** | Component name and model | GomSpace NanoPower P31u |
| **Manufacturer** | Vendor name | GomSpace A/S |
| **Part number** | Manufacturer part number | P31U-9-30 |
| **Quantity** | Number required | 1 |
| **Unit mass (g)** | Per-item mass | 94 |
| **Unit power (W)** | Peak / average power draw | 0.5 / 0.2 |
| **Unit cost (EUR)** | Procurement cost | 8 500 (indicative) |
| **TRL** | Technology readiness level | 9 |
| **Heritage** | Previous mission(s) flown | GOMX-3, GOMX-4 |
| **Lead time** | Procurement lead time | 12 weeks |
| **ECCN/USML** | Export classification | EAR99 |
| **Status** | Selected / ordered / received / tested | Selected |

In a concurrent-design tool the BOM is generated automatically from the equipment selections — each selected component becomes a BOM entry with its quantity, and the export carries both the parametric estimate and the actual COTS data side by side for comparison. Built by hand, the same table is the single source from which the mass, power and cost budgets are re-totalled (Chapter 12 §12.5).

### 13.3.3 BOM mass total

> **Key equation — BOM mass total:**
>
> $$M_{\text{BOM}} = \sum_i m_i\, q_i + M_{\text{harness}} + M_{\text{fasteners}} + M_{\text{margin}}$$
>
> where:
> - $m_i$ = unit mass of component $i$
> - $q_i$ = quantity of component $i$
> - $M_{\text{harness}}$ = harness mass (typically 5–8 % of dry mass for CubeSats)
> - $M_{\text{fasteners}}$ = mechanical fasteners, standoffs, thermal hardware (~3–5 %)
> - $M_{\text{margin}}$ = equipment and system margins per the two-level schedule of Chapter 8 Table 8.3 (20 % system margin at Phase A)

### 13.3.4 Worked example — 6U CubeSat BOM summary

The subsystem-level roll-up below is for a 6U Earth-observation CubeSat (the allocation line is the 6U deployer limit of Chapter 12 §12.1.1). Compare it with the 3U equipment list of Chapter 12 §12.5.2.

| Subsystem | Components | Total mass (g) | Total power (W) | Total cost (kEUR, indicative) |
|-----------|-----------|----------------|-----------------|-------------------|
| Structure | Rails, panels, fasteners | 350 | 0 | 8.0 |
| EPS | Solar array + battery + board | 420 | 0.5 | 18.0 |
| OBC | Flight computer + storage | 80 | 1.2 | 10.0 |
| AOCS | Star tracker + magnetorquers + reaction wheels | 550 | 4.5 | 45.0 |
| TTC | S-band transceiver + patch antenna | 180 | 8.0 (TX) | 22.0 |
| Thermal | MLI + heaters | 60 | 2.0 (peak) | 3.0 |
| Payload | Multispectral imager | 800 | 12.0 | 65.0 |
| Harness | Cables, connectors | 180 | 0 | 2.5 |
| **Total** | | **2620** | **28.2 (peak)** | **173.5** |
| Allocation (6U) | | 12 000 | 40.0 (array EOL) | 250.0 |
| Margin | | 9380 (78 %) | 11.8 (30 %) | 76.5 (31 %) |

The 78 % mass margin is typical of an early 6U design with a 3U-class payload: the form factor was chosen for volume and power, not mass. The two margins that matter are power (30 % with every load at peak simultaneously, which the mode table of Chapter 18 will show never happens) and cost (31 %, before the margins of Chapter 16 are applied).

---

## 13.4 Export control and procurement

Export control is one of the most commonly overlooked aspects of CubeSat missions, especially for international teams. Violations carry severe penalties (criminal prosecution, programme cancellation). Chapter 2 §2.8 describes the Canadian regime; this section gives the engineer's view of what it means for component selection.

*[Source: ITAR — 22 CFR Parts 120–130; EAR — 15 CFR Parts 730–774; Canadian Controlled Goods Program — Defence Production Act]*

### 13.4.1 Export control regimes

| Regime | Governing law | Applies to | Key concern for CubeSats |
|--------|-------------|-----------|-------------------------|
| **ITAR** | US Arms Export Control Act | Defence articles (USML Categories IV, XI, XV) | Star trackers, rad-hard processors, some GPS receivers |
| **EAR** | US Export Administration Act | Dual-use items (CCL) | Most COTS space components (ECCN 9A515) |
| **Canadian CGP** | Defence Production Act | Controlled goods in Canada | Handling US-origin ITAR items in Canadian facilities |
| **Wassenaar** | Wassenaar Arrangement | Multilateral export controls | Encryption, high-accuracy GNSS, imaging sensors |

### 13.4.2 Component classification decision

```
Is the component on the US Munitions List (USML)?
  → Yes: ITAR-controlled. A DSP-5 licence is needed for export.
     Categories: IV (launch vehicles), XI (military electronics),
                 XV (spacecraft systems)
  → No: check the Commerce Control List (CCL)
     Is it classified under ECCN 9A515 (spacecraft)?
       → Yes: EAR-controlled. May need a BIS licence.
       → No: likely EAR99 (no licence required for most destinations)
```

### 13.4.3 Common ITAR-controlled CubeSat components

| Component type | Why controlled | Alternative |
|---------------|---------------|------------|
| Radiation-hardened processors | Military-grade radiation tolerance | COTS processors with software mitigation (Chapter 12 §12.3.2) |
| High-accuracy star trackers (< 1 arcsec) | Missile-guidance applicability | Lower-accuracy models (> 5 arcsec) |
| Certain GPS/GNSS receivers | Above COCOM limits (> 18 km altitude, > 515 m/s) | Space-rated receivers with COCOM compliance |
| Propulsion systems (some) | Missile technology | Cold-gas or water-based systems |
| Encryption modules | Signals intelligence | Open-source encryption (may still need EAR review) |

### 13.4.4 Procurement workflow

```
1. Requirements          → derive the component specification
2. Market survey         → identify candidate COTS products
3. Export classification → request the ECCN from the vendor
4. Trade study           → score and rank candidates
5. Request for quote     → obtain pricing and lead times
6. Purchase order        → commit to procurement
7. Incoming inspection   → verify against the purchase order and datasheet
8. Integration           → install and functionally test
```

### 13.4.5 Real mission example: export-control impact

The BRITE-Constellation (Austria/Canada/Poland) was a series of nanosatellites for stellar photometry. The Canadian BRITE satellites (UniBRITE and BRITE-Austria, built by UTIAS/SFL) required careful export-control management:
- US-origin ITAR components required Technical Assistance Agreements (TAAs)
- Controlled Goods registration was required for the Canadian team
- Export permits were needed for shipping between Canada, Austria and the US launch site
- Total regulatory compliance effort: ~6 person-months and 12+ months lead time

*Lesson: start export classification immediately when components are identified. A single ITAR component can add 6–12 months to the schedule.*

*[Source: Sarda, K. et al., "BRITE-Constellation Mission and Spacecraft", AIAA/USU Small Satellite Conference, 2014]*

---

## 13.5 Interface compatibility verification

As components are selected, every interface must be verified for compatibility. The three interface categories that most often bite at selection time are RF (R), electrical (E) and mechanical (M), in the letter codes of Chapter 8 Table 8.2.

### 13.5.1 RF chain compatibility

The RF chain (transponder, cable, antenna) must be frequency-matched. This is the most common equipment incompatibility for CubeSat newcomers.

| Rule | Correct example | Incorrect example |
|------|----------------|-------------------|
| **Band match** | S-band transponder + S-band patch antenna | S-band transponder + X-band horn |
| **Impedance match** | 50 Ω transponder + 50 Ω cable + 50 Ω antenna | Mixed impedances cause reflections |
| **Connector match** | SMA on transponder + SMA–SMA cable + SMA on antenna | SMA to N-type needs an adapter (loss) |
| **Polarisation** | RHCP antenna + RHCP ground station | RHCP to LHCP causes > 20 dB cross-polarisation loss (Chapter 11 §11.8.2) |

> **Key equations — impedance mismatch loss:**
>
> $$\Gamma = \frac{Z_{\text{load}} - Z_{\text{source}}}{Z_{\text{load}} + Z_{\text{source}}}$$
>
> $$\text{Return loss (dB)} = -20 \log_{10} |\Gamma|$$
>
> $$\text{Mismatch loss (dB)} = -10 \log_{10}\!\left(1 - |\Gamma|^2\right)$$
>
> For a 50 Ω source into a 75 Ω load:
> $\Gamma = (75 - 50)/(75 + 50) = 0.2$; return loss $= -20 \log_{10}(0.2) = 14$ dB; mismatch loss $= -10 \log_{10}(1 - 0.04) = 0.18$ dB.
>
> A mismatch loss of this size is absorbed by the line-loss term $L_{TX}$ of the link budget (Chapter 11 §11.2); the return loss matters more, because the reflected power can damage a transmitter's output stage.

A concurrent-design tool with band data on each component will flag a transponder and antenna in different bands as soon as the second one is selected; by hand, the check is one column in the BOM.

### 13.5.2 Electrical interface verification

| Parameter | Typical CubeSat | What to verify |
|-----------|----------------|----------------|
| Bus voltage | 3.3 V, 5 V, or unregulated (6–8.4 V Li-ion) | Component input-voltage range covers the bus voltage |
| Peak current | Per switched-line limit (typically 1–3 A) | Component inrush current does not exceed the limit |
| Data protocol | I²C, SPI, UART, CAN, RS-422 | All devices on the same bus use a compatible protocol (Chapter 8 §8.3.5 worked example) |
| Connector | PC/104, Hirose, Harwin | Physical connector type matches or an adapter is planned |

### 13.5.3 Mechanical interface verification

| Parameter | CDS 3U requirement | Verification |
|-----------|--------------------|----|
| Dimensions | 100.0 ± 0.1 mm × 100.0 ± 0.1 mm × 340.5 ± 0.5 mm | Calliper measurement |
| Rail profile | 8.5 × 8.5 mm ± 0.1 mm | Profile gauge |
| Component stack height | ≤ 83 mm internal width per U | 3D model check |
| CG location | Within 2 cm of the geometric centre | Mass-properties measurement |

---

## 13.6 Returning to UniSat-1: bill of materials and cost

UniSat-1's BOM is remarkably short — only 5–7 line items plus harness. This simplicity is a major advantage for small teams with limited procurement experience. The equipment list itself was assembled in Chapter 12 §12.6; here it is restated in BOM form with the procurement fields added.

> **UniSat-1 BOM (Phase B — vendor quotes obtained; representative examples, costs indicative 2026):**
>
> | Item ID | Component | Manufacturer | Part number | Qty | Unit mass (g) | Unit cost (kEUR) | TRL | ECCN | Lead (weeks) |
> |---------|-----------|-------------|-------------|-----|---------------|-----------------|-----|------|-----------|
> | STR-001 | 1U CubeSat structure | ISIS | ISIS-1U-STR | 1 | 200 | 4.0 | 9 | EAR99 | 8 |
> | EPS-001 | NanoPower P31us (EPS + 10 Wh battery) | GomSpace | P31US-10 | 1 | 200 | 12.0 | 9 | EAR99 | 12 |
> | EPS-SA-001 | Body-mounted GaAs solar cells | AzurSpace | 3G30C | 5 | 10 | 1.5 | 9 | EAR99 | 10 |
> | OBC-001 | Custom flight computer (Cortex-M) | In-house | UNISAT-OBC-01 | 1 | 30 | 3.0 | 5 | EAR99 | — |
> | COM-001 | UHF transceiver | GomSpace | NanoCom AX100 | 1 | 55 | 8.0 | 8 | EAR99 | 12 |
> | COM-ANT-001 | UHF deployable antenna | Endurosat | UHF-ANT-S | 1 | 25 | 2.5 | 8 | EAR99 | 8 |
> | PL-001 | MEMS magnetometer board | In-house | UNISAT-MAG-01 | 1 | 50 | 5.0 | 4 | EAR99 | — |
> | AOCS-001 | Passive magnetic kit (magnet + rods) | NewSpace | PMAG-1U | 1 | 30 | 1.0 | 9 | EAR99 | 6 |
> | HAR-001 | Internal harness | Custom | — | 1 | 50 | 1.0 | N/A | EAR99 | — |
> | | **TOTALS** | | | | **690 g** | **~44 kEUR** | | | |

**Cost summary (total mission, hardware + services; indicative 2026):**

| WBS element | Cost (kEUR) | Notes |
|-------------|------------|-------|
| Hardware (BOM) | 44 | All COTS except OBC and payload |
| OBC software | 5 | Student labour (costed at stipend rate) |
| Payload calibration | 3 | University magnetometer laboratory |
| Integration and test | 8 | Assembly + vibration test (university facility) |
| Ground station | 5 | SatNOGS (free) + dedicated Yagi antenna purchase |
| Launch (ISS deployment) | 15 | NanoRacks 1U deployment fee |
| PM/SE/QA | 5 | Faculty supervision |
| **TOTAL** | **~85 kEUR** | |

**Comparison with the 3U EO mission:**

| Metric | UniSat-1 (1U) | EOSat-3U |
|--------|--------------|---------------|
| BOM line items | 9 | ~15–20 |
| Hardware cost | ~44 kEUR | ≈ 170 kEUR with a COTS imager (Chapter 16 §16.1.6); ≈ 313 kEUR with the custom telescope of Chapter 12 §12.5.2 |
| Total mission cost | ~85 kEUR | ~490 kEUR |
| Development time | 6–12 months | 18–24 months |
| Team size | 3–5 people | 8–15 people |

**Export control:** All UniSat-1 components are classified EAR99 (no licence required). There are no ITAR-controlled items because the mission uses no star trackers, no radiation-hardened processors and no propulsion with ITAR-restricted technology. This is a significant advantage for international university collaborations.

**Make/buy/reuse decisions:**

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Structure | Buy (COTS) | ISIS 1U frame is flight-proven, TRL 9, low cost |
| EPS | Buy (COTS) | GomSpace P31us is the de facto standard, TRL 9 |
| OBC | Make (custom) | Minimal board using the university laboratory; lower cost than a COTS OBC for this simple application |
| Comms | Buy (COTS) | GomSpace AX100, TRL 8, well documented |
| Payload | Make (custom) | Novel MEMS sensor — this *is* the technology demonstration |
| Passive AOCS | Buy (COTS) | Standard magnetic-stabilisation kit |

> **Think about it.** The two "make" items on UniSat-1 are also the two lowest-TRL items (5 and 4). By the empirical relation of §13.2.2 they carry roughly 10 and 20 times the risk factor of the TRL 9 purchases. Where in the schedule should the project place the first end-to-end test of these two boards?

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| Make/buy/reuse | Buy COTS first; reuse heritage second; make custom only when necessary |
| NRE | $C_{\text{NRE}} = N_{\text{hours}} r_{\text{hour}} + C_{\text{material}} + C_{\text{facility}} + C_{\text{test}}$; custom NRE is 3–10× the unit cost |
| TRL | Minimum TRL 6 for mission-critical components; TRL 7+ preferred for CubeSats; $f_{\text{risk}} = 10^{-(\text{TRL}-1)/3}$ |
| BOM | Hierarchical list: subsystem → assembly → component → part, with full traceability |
| Export control | Classify every component (EAR99 / ECCN / ITAR); start early — delays the programme |
| RF compatibility | Band, impedance, connector and polarisation must all match across the RF chain |
| Electrical | Bus voltage, data protocol and connector type verified per component |
| Budget tracking | Running totals during selection; stop and resolve if an allocation is exceeded (Chapter 12 §12.5) |

---

## Problems

1. **Make/buy/reuse.** A 3U Earth-observation CubeSat needs a reaction wheel delivering 10 mN m s. Options: a COTS wheel (TRL 9, 8 kEUR, 10 weeks); a wheel flown on a previous mission by the same team that needs a new bearing qualification (TRL 7, 4 kEUR + 60 h delta-qualification, 16 weeks); and an in-house design (TRL 3, 2 kEUR + 600 h NRE, 14 months). At a loaded rate of 100 EUR/h, compute the total cost of each option, apply the decision framework of §13.1.1, and state the decision. Then state the one circumstance in which the in-house option could be the right answer.

2. **TRL and risk.** Using $f_{\text{risk}} = 10^{-(\text{TRL}-1)/3}$, compute the risk factor for every item of the UniSat-1 BOM (§13.6) and identify the two components that together account for most of the summed risk. Propose a development-test plan that raises each of them by one TRL before CDR, and estimate the calendar time.

3. **BOM roll-up.** Build the level-1 BOM roll-up for the EOSat-3U equipment list of Chapter 12 §12.5.2: group the components by subsystem, total mass, peak power and cost, add harness (6 %) and fasteners (4 %) to the mass, and apply the Phase A margins of Chapter 8 Table 8.3. Compare the resulting MEV with the 6 kg CDS limit and with the 5.17 kg of Chapter 12 §12.5.2, and explain the difference.

4. **Lead time as the critical path.** From the UniSat-1 BOM, identify the longest procurement lead time, then add 8 weeks of incoming inspection and integration and 6 weeks of environmental test. If the launch integration date is 40 weeks away, by which week must every purchase order be placed? Which two items, if late by four weeks, would miss the launch?

5. **Export classification.** Classify each of the following for a Canadian university mission with a Polish partner: (a) a 5-arcsec COTS star tracker made in the USA; (b) a European-built GNSS receiver without COCOM limits removed; (c) a rad-hard LEON3 processor; (d) an open-source AES encryption library; (e) a Canadian-built magnetometer. For each, state the likely regime (ITAR, EAR 9A515, EAR99, or non-US), the licensing action, and the schedule impact.

6. **RF chain check.** A 3U CubeSat selects an S-band transmitter (50 Ω, SMA, 2 W) and, by mistake, a 75 Ω cable assembly. Compute the reflection coefficient, return loss and mismatch loss at the cable input. Then, for the EOSat-3U link budget of Chapter 11 §11.8.1, state how much margin the mismatch costs and whether the error would have been caught by the link budget alone.

7. **Electrical interface.** The chosen OBC provides a single I²C bus at 3.3 V and switched 5 V lines limited to 1.5 A. The candidate star tracker needs 5 V at 2.0 A inrush and talks RS-422. List every incompatibility, propose a fix for each (component change, adapter, or wiring), and identify which fixes add mass to the harness line of the BOM.

8. **Interface audit from the N² matrix.** Using Chapter 8 Table 8.1 and the letter codes of Table 8.2, list every E, D and R interface of the TTC subsystem in the EOSat-3U equipment list of Chapter 12 §12.5.2 and, for each, write the single BOM field (voltage, protocol, connector, band or polarisation) that must agree on both sides.

9. **Cost comparison.** Using the UniSat-1 cost summary of §13.6 and the EOSat-3U hardware cost of Chapter 12 §12.5.2, estimate the EOSat-3U total mission cost by scaling each non-hardware line (software, calibration, integration and test, ground station, launch, management) with a justified factor, and compare the result with the ~490 kEUR quoted. Which non-hardware line is most sensitive to your assumptions?

10. **Design-for-procurement.** A rideshare opportunity moves the EOSat-3U launch forward by six months. Which selections in Chapter 12 §12.5.2 would you change to a shorter-lead or higher-TRL alternative, what performance would you give up, and how would the closure table of Chapter 12 §12.5.3 change?

---

## References

1. NASA, *Technology Readiness Levels*, NPR 7123.1D Appendix E. https://www.nasa.gov/directorates/somd/space-communications-navigation-program/technology-readiness-levels/
2. ECSS, *ECSS-E-HB-11A: Technology Readiness Level (TRL) Guidelines*, 2017. https://ecss.nl
3. ECSS, *ECSS-Q-ST-20C Rev. 2: Quality Assurance*, 2023. https://ecss.nl/standard/ecss-q-st-20c-rev-2-quality-assurance-1-march-2023/
4. ECSS, *ECSS-M-ST-10C Rev. 1: Project Planning and Implementation*, 2009. https://ecss.nl
5. NASA, *Systems Engineering Handbook*, NASA/SP-2016-6105 Rev 2, §6.8. https://www.nasa.gov/reference/systems-engineering-handbook/
6. US Department of State, Directorate of Defense Trade Controls (ITAR, 22 CFR 120–130). https://www.pmddtc.state.gov/
7. US Department of Commerce, Bureau of Industry and Security (EAR, 15 CFR 730–774). https://www.bis.doc.gov/
8. Public Services and Procurement Canada, *Controlled Goods Program*. https://www.tpsgc-pwgsc.gc.ca/pmc-cgp/
9. Cal Poly, *CubeSat Design Specification Rev 14.1*, 2022. https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf
10. Wertz, J. R., Everett, D. F. & Puschell, J. J. (eds.), *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, Ch. 14 and Ch. 20.
11. Klesh, A. et al., "Mars Cube One (MarCO) — Lessons Learned", SSC19-WKII-07, 33rd Annual Small Satellite Conference, 2019.
12. Sarda, K. et al., "BRITE-Constellation Mission and Spacecraft", AIAA/USU Small Satellite Conference, 2014.
