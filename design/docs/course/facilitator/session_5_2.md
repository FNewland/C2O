# Session 5.2: Regulatory & Licensing

**Duration:** 2 hours
**Prerequisites:** Session 5.1 (gate review complete)
**References:** ITU Radio Regulations; IARU Satellite Coordination; FCC 47 CFR Parts 5/25/97; ISED CPC-2-6-02; RSSSA (S.C. 2005, c.45); ECSS-U-AS-10C

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Determine the appropriate licensing path (amateur/experimental/commercial)
2. Identify all regulatory filings required for a Canadian CubeSat mission
3. Assess export control implications for international missions
4. Generate regulatory filing templates using SpaceCDF
5. Plan the regulatory timeline (filings must start 12+ months before launch)

---

## 1. Regulatory Landscape Overview (20 min)

### Teaching Notes

A CubeSat mission requires approvals from multiple authorities:

| Authority | What They Approve | Timeline |
|-----------|------------------|----------|
| **ISED (Canada)** | Spectrum licence (CPC-2-6-02) | 126 days service standard |
| **ITU** | International frequency coordination | 12-24 months (API → coordination → notification) |
| **IARU** | Amateur frequency coordination | 2-6 months |
| **Global Affairs Canada** | RSSSA licence (if remote sensing) | 6+ months |
| **Global Affairs Canada** | Export permit (if controlled goods) | 3-6 months |
| **PSPC** | Controlled Goods registration | 3-6 months |
| **UN/COPUOS** | Space object registration | Post-launch ("as soon as practicable") |
| **FCC (if US launch)** | Orbital debris assessment (Part 25) | 6-9 months |

### Critical Path: Start Early!

The longest-lead regulatory item is typically **ITU coordination** (12-24 months). For Canadian missions, the filing goes through ISED to the ITU Radiocommunication Bureau.

**Rule:** Start spectrum licensing at least **12 months before planned launch date**. For complex filings (commercial, multiple bands), start **18-24 months** ahead.

---

## 2. Frequency Licensing Decision Tree (25 min)

### Teaching Notes

*[Source: SpaceCDF spectrum research — see ULTRAPLAN3 reference data]*

### Step 1: Determine License Type

```
Is the mission:
  Non-commercial + educational + data will be open?
    → AMATEUR (IARU + national amateur licence)
  R&D/technology demonstration + no revenue?
    → EXPERIMENTAL (FCC Part 5 / ISED developmental)
  Will generate revenue OR data is proprietary?
    → COMMERCIAL (FCC Part 25 / ISED CPC-2-6-02 + ITU filing)
```

### Step 2: Determine Required Bands

| Data Rate Needed | Recommended Band | Filing Type |
|-----------------|------------------|-------------|
| < 9.6 kbps | UHF amateur (435-438 MHz) | IARU only |
| < 19.2 kbps | UHF amateur (435-438 MHz) | IARU only |
| < 1 Mbps | S-band (2200-2290 MHz) | ISED + ITU |
| 1-10 Mbps | S-band (2200-2290 MHz) | ISED + ITU |
| 10-400 Mbps | X-band (8025-8400 MHz) | ISED + ITU |
| > 400 Mbps | Ka-band (25.5-27 GHz) | ISED + ITU (complex) |

### Step 3: File Appropriately

**Amateur route (simplest):**
1. IARU coordination request (submit through Radio Amateurs of Canada)
2. Obtain amateur callsign for ground station (Advanced licence)
3. No ITU cost recovery fees
4. Restrictions: no encryption (except TC), no commercial use, open data

**Commercial route (most common for professional missions):**
1. ISED spectrum licence application (CPC-2-6-02)
2. ITU Advance Publication Information (API) through ISED
3. ITU Coordination Request (CR/C) 4+ months after API
4. ITU Notification (after coordination complete)
5. Costs: ISED fees + ITU cost recovery (several thousand CHF)

---

## 3. Canadian-Specific Requirements (20 min)

### Teaching Notes

### RSSSA (Remote Sensing Space Systems Act)

**Applies if:** The satellite has ANY remote sensing capability (camera, SAR, multispectral).

**Key requirements:**
- Data access control measures
- Shutter control capability (ability to restrict imaging of specific areas)
- Disposal plan with performance guarantee
- National security assessment
- Ongoing compliance reporting

**Filing:** Global Affairs Canada (RSSSA-LSTS@international.gc.ca)

**For educational CubeSats with cameras:** Still need RSSSA licence, even for low-resolution. There are no minimum GSD thresholds — any Earth-imaging capability triggers the requirement.

### Export Control (Canadian Controlled Goods Program)

**Applies if:** Any component is controlled under the Export Control List (item 5504 includes satellite systems).

**Key considerations:**
- US-origin components → ITAR/EAR apply even in Canada
- Launching from US soil → all satellite components need EAR classification
- Rad-hard components → often export controlled (ECCN 9A515.d/e)
- Star trackers → some models are controlled (military-grade accuracy)

**Process:**
1. Classify all components (request ECCN from vendors)
2. Register with Controlled Goods Directorate (if handling controlled items)
3. Apply for export permit (Global Affairs Canada) if shipping internationally

---

## 4. Filing Templates Exercise (25 min)

### Instructions

1. Navigate to **Exports** tab in SpaceCDF
2. Under **Regulatory Filings**, generate:
   - **ITU API Filing Template** — review all fields
   - **IARU Coordination Request** — review all fields
   - **RSSSA Filing** (if your mission has imaging)
   - **Export Control Assessment** — review classification
   - **COPUOS Registration** — review Article IV fields
   - **End-of-Life Analysis** — review debris compliance
3. For each generated document:
   - Identify which fields are auto-populated from the design
   - Identify which fields are "TBD" (require manual completion)
   - Note any fields you cannot fill yet (and when you'll be able to)

### Key Discussion Points

- How many of these documents would your team need for YOUR mission?
- What is the longest-lead filing? When should it be submitted?
- Are there any export control concerns with your component selections?

---

## 5. Regulatory Timeline Planning (30 min)

### Teaching Notes

### Example Timeline (working backward from launch date)

```
L-24 months: Start ITU API filing process through ISED
L-18 months: Submit ISED spectrum licence application
L-18 months: Start IARU coordination (if amateur)
L-12 months: ITU coordination complete; RSSSA application submitted
L-12 months: Export control assessment complete; permits applied
L-9 months:  ISED licence granted; export permits received
L-6 months:  RSSSA licence granted
L-3 months:  Final frequency notifications; ground station licences active
L-0:         Launch
L+1 month:   COPUOS registration filed
```

**For the course exercise:** Map your mission's regulatory timeline onto a Gantt chart showing which filings are on the critical path.

### Worksheet 5.2 Tasks

1. Determine which filings your mission requires (tick applicable):
   - [ ] ISED spectrum licence
   - [ ] ITU API/coordination/notification
   - [ ] IARU coordination
   - [ ] RSSSA operating licence
   - [ ] Export permit(s)
   - [ ] Controlled Goods registration
   - [ ] COPUOS registration
   - [ ] End-of-life / debris compliance report

2. For each required filing, note:
   - Filing authority
   - Estimated timeline to approval
   - Dependencies (what information is needed before filing)

3. Identify the critical path filing and compute launch date impact

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Licensing types | Amateur (free, open data) / Experimental (R&D) / Commercial (revenue OK) |
| Canadian authorities | ISED (spectrum), Global Affairs (RSSSA, export), PSPC (controlled goods) |
| ITU process | API → Coordination → Notification; 12-24 months total |
| RSSSA | Any Earth-imaging satellite needs this; no GSD minimum |
| Export control | US components → ITAR/EAR; US launch → EAR applies to all hardware |
| Timeline | Start filings 12-24 months before launch; ITU is usually critical path |
| SpaceCDF | Exports tab generates all filing templates from design data |
